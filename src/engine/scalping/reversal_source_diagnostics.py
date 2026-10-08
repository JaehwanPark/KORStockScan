"""Read-only diagnostics for the pinned normalized reversal kernel.

Runtime source projection owns this module, independently of research kernel
and auxiliary input contracts. No price, feature, policy or decision mutation.
"""
from datetime import datetime
from copy import deepcopy
import math
import time

from src.engine.scalping import continuous_reversal as K


def claim_snapshot_with_receipt(*args, **kwargs):
    """Observe native registration before its bounded in-memory expiry.

    Extra source metadata does not change the native token, snapshot or guard.
    Registration and its copy share the ingestion lock; no disk or API I/O.
    """
    from src.engine.scalping.reversal_current_backend import backend
    B = backend()
    live_clock = kwargs.pop('live_clock', False)
    with B._LOCK:
        if live_clock:
            kwargs['now'] = time.time()
        claim = B.claim_snapshot(*args, **kwargs)
        if claim:
            if live_clock:
                from src.engine.monitoring.runtime_performance import observe, mark_signal
                observe('confirmed_to_claim', kwargs['now'] - claim['snapshot'][0]['epoch'])
                event = claim['snapshot'][0]
                mark_signal(event.get('signal_id') or event.get('event_id'), 'claim')
            try:
                receipt_backend = B.R if getattr(B,'R',None) and claim.get('backend')=='registered_v4' else B
                original = receipt_backend._CLAIMS.get(claim['token'])
                if original:
                    proof = dict(schema='continuous_reversal_claim_registration_v1',
                        claim_token=claim['token'], generation=original['generation'],
                        scope=list(original['scope']), snapshot=deepcopy(original['snapshot']),
                        claim_epoch=kwargs['now'], observed_epoch=time.time(), runtime_effect=False)
                    proof['sha256'] = B.digest(proof)
                    claim['source_registration_receipt'] = proof
            except (ValueError, TypeError, KeyError, OverflowError):
                # A source-copy failure must not alter native claim admission.
                claim['source_registration_receipt'] = dict(
                    schema='continuous_reversal_claim_registration_v1', status='unobservable', runtime_effect=False)
        return claim


def verified_registration(claim, proof):
    """Validate exact source metadata, without granting native claim validity."""
    from src.engine.scalping import continuous_reversal_branches as B
    try:
        event = proof['snapshot'][0]
        if (proof.get('schema') != 'continuous_reversal_claim_registration_v1'
                or proof.get('status') == 'unobservable'
                or proof.get('runtime_effect') is not False
                or proof['sha256'] != B.digest({k: v for k, v in proof.items() if k != 'sha256'})
                or proof['claim_token'] != claim['token']
                or proof['generation'] != claim['generation']
                or proof['snapshot'] != claim['snapshot']
                or proof['scope'] != ([event['symbol'], event['venue'], event['source_item'],
                                      event['market'], datetime.fromtimestamp(event['epoch'], K.KST).date().isoformat()]
                    + ([__import__('src.engine.scalping.reversal_path_catalog',fromlist=['cell_key']).cell_key(
                        event['symbol'],event['market'],event['confirmation_price'])] if claim.get('backend') in {'operating_v5','operating_v6'} else []))
                or proof['claim_token'] != B.digest([proof['generation'], event['signal_id'], proof['snapshot']])
                or not 0 <= proof['claim_epoch'] - event['epoch'] <= 5
                or not 0 <= proof['observed_epoch'] - proof['claim_epoch'] <= 5):
            return None
        return proof
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        return None


def validate_claim_with_receipt(claim, family_sha256, *, now,
                                evaluation_attempt_id=None, machine_bundle_sha256=None,
                                live_clock=False):
    """Run the unchanged guard and retain its exact source on rejection.

    Inspection and validation share the ingestion lock. Live callers acquire
    their clock after waiting; replay callers retain their explicit oracle.
    """
    from src.engine.scalping.reversal_current_backend import backend
    B = backend(claim)

    with B._LOCK:
        if live_clock:
            now = time.time()
        try:
            return B.validate_claim(claim, family_sha256, now=now)
        except ValueError as exc:
            try:
                receipt = _claim_failure_receipt(B, claim, family_sha256, now, str(exc))
            except (ValueError, TypeError, KeyError, OverflowError):
                # Telemetry must preserve the native rejection, even for a
                # malformed input that cannot be serialized safely.
                receipt = dict(schema='continuous_reversal_claim_source_receipt_v1',
                    status='unobservable', validation_error=str(exc), runtime_effect=False)
            receipt.update(evaluation_attempt_id=evaluation_attempt_id,
                           machine_bundle_sha256=machine_bundle_sha256)
            exc.reversal_source_receipt = receipt
            raise


def _claim_failure_receipt(B, claim, family_sha256, now, reason):
    original = B._CLAIMS.get(claim.get('token')) if isinstance(claim, dict) else None
    snapshot = deepcopy(original['snapshot']) if original else None
    supplied = claim.get('snapshot') if isinstance(claim, dict) else None
    registration = deepcopy(claim.get('source_registration_receipt')) if isinstance(claim, dict) else None
    verified = verified_registration(claim, registration) if registration else None
    event = snapshot[0] if snapshot else verified['snapshot'][0] if verified else {}
    scope = original['scope'] if original else tuple(verified['scope']) if verified else None
    state = B._STATES.get(scope) if scope else None
    last = list(state.legacy.last) if state and state.legacy.last else None
    current_turn_id = (state.legacy.turn or {}).get('event_id') if state else None
    state_observed_epoch = time.time()
    receipt = dict(schema='continuous_reversal_claim_source_receipt_v3', status='observed',
        validation_epoch=now, requested_family_sha256=family_sha256,
        state_observed_epoch=state_observed_epoch,
        claim_token=claim.get('token') if isinstance(claim, dict) else None,
        claim_generation=claim.get('generation') if isinstance(claim, dict) else None,
        stored_generation=original.get('generation') if original else None,
        active_generation=B._GENERATION, registered_claim_present=original is not None,
        source_registration_receipt=registration, supplied_snapshot=deepcopy(supplied),
        scope=list(scope) if scope else None,
        snapshot=snapshot, snapshot_sha256=B.digest(snapshot) if snapshot else None,
        supplied_snapshot_sha256=B.digest(supplied) if supplied else None,
        signal_id=event.get('signal_id') or event.get('event_id'),
        decision_phase=event.get('decision_phase'),
        signal_age_seconds=now-event['epoch'] if event else None,
        latest_native_observation=last, current_turn_id=current_turn_id,
        price_path_segment_start=state.legacy.segment_start if state else None,
        validation_error=reason, failure_cause=reason,
        runtime_effect=False, actual_order_submitted=False)
    if (reason == 'reversal_signal_generation_changed' and not original and verified
            and B._GENERATION == family_sha256 == verified['generation']
            and receipt['signal_age_seconds'] > 5):
        receipt['failure_cause'] = 'reversal_signal_expired'
    if reason == 'reversal_signal_expired_or_changed':
        receipt['failure_cause'] = (
            'reversal_signal_snapshot_changed'
            if receipt['snapshot_sha256'] != receipt['supplied_snapshot_sha256']
            else 'reversal_signal_expired' if receipt['signal_age_seconds'] > 5
            else 'reversal_signal_clock_invalid')
    return receipt


def project(snapshot, *, symbol, venue, session, now, item, envelope=None):
    if snapshot is None:
        return {'status': 'not_observed', 'reason': 'no_current_reversal'}
    event, _ = snapshot
    market = K.market_bucket(session)
    key = (symbol, venue, item, market, datetime.fromtimestamp(now, K.KST).date())
    from src.engine.scalping.reversal_current_backend import backend
    registered=backend()
    native=registered if getattr(registered, "_FAMILY", None) is not None else K
    if native is registered:
        key=key[:4]+(key[4].isoformat(),)
    with native._LOCK:
        if (getattr(native,'_FAMILY',None) or {}).get('schema') in {'continuous_reversal_policy_v5','continuous_reversal_policy_v6'}:
            from src.engine.scalping.reversal_path_catalog import cell_key
            scope=cell_key(symbol,market,event['confirmation_price'])
            if native._FAMILY['machine_cells'][scope]['routes'][venue]['backend']=='registered_v4':
                native=native.R
            else:
                key=key+(scope,)
        state = native._STATES.get(key)
        if native is registered:
            state=state.legacy if state else None
            exact=state and any(r[1]==event.get('native_epoch') and r[2]==event.get('native_sequence') for r in state.rows)
        else:
            exact=state and state.turn and state.turn['event_id']==event['event_id']
        if not exact:
            return {'status': 'not_observed', 'reason': 'reversal_revision_changed'}
        start = state.segment_start
        # Native rows are append-only values; retain references briefly, then
        # compute diagnostics outside the ingestion lock.
        rows = [r for r in state.rows if r[0] <= event['epoch']]
    t = event['epoch']
    elapsed = max(0., t-start)
    reset = 'initial_observation_or_process_restart'
    for i, row in enumerate(rows):
        if row[0] == start and i and not K.connected(rows[i-1], row):
            previous = rows[i-1]
            reset = ('source_stale_or_invalid' if not row[8] or not previous[8]
                else 'transport_epoch_changed' if row[1] != previous[1]
                else 'sequence_or_clock_gap')
            break
    status = 'warmup_after_' + reset
    if elapsed >= 120:
        window = [r for r in rows if t-120 <= r[0] <= t]
        valid = all(type(r[6]) in (int,float) and math.isfinite(r[6]) and r[6] > 0 for r in window)
        status = ('quantity_missing_or_invalid' if not valid else
                  'ready' if event['volume_ratio_60s'] is not None else 'previous_window_empty')
    body = dict(schema='continuous_reversal_source_diagnostics_v1', status='observed',
        event_id=event['event_id'], volume_ratio_source_status=status,
        volume_ratio_observed_seconds=elapsed, runtime_effect=False)
    if (isinstance(envelope, dict) and envelope.get('observed_epoch') == t
            and envelope.get('item') == item
            and str(event['event_id']).endswith(
                ':' + str(envelope.get('transport_epoch')) + ':' + str(envelope.get('route_sequence')))
            and isinstance(envelope.get('market_source_latency'), dict)):
        body['source_latency'] = dict(envelope['market_source_latency'])
    return body
