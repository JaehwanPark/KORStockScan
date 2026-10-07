"""Read-only diagnostics for the pinned normalized reversal kernel.

Runtime source projection owns this module, independently of research kernel
and auxiliary input contracts. No price, feature, policy or decision mutation.
"""
from datetime import datetime
from copy import deepcopy
import math
import time

from src.engine.scalping import continuous_reversal as K


def validate_claim_with_receipt(claim, family_sha256, *, now,
                                evaluation_attempt_id=None, machine_bundle_sha256=None):
    """Run the unchanged guard and retain its exact source on rejection.

    Inspection and validation share the ingestion lock. Keep the caller's
    decision clock for the unchanged guard and separately timestamp the state
    read: ingestion can advance while the caller waits to acquire this lock.
    """
    from src.engine.scalping import continuous_reversal_branches as B

    with B._LOCK:
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
    event = snapshot[0] if snapshot else {}
    state = B._STATES.get(original['scope']) if original else None
    last = list(state.legacy.last) if state and state.legacy.last else None
    current_turn_id = (state.legacy.turn or {}).get('event_id') if state else None
    state_observed_epoch = time.time()
    receipt = dict(schema='continuous_reversal_claim_source_receipt_v2', status='observed',
        validation_epoch=now, requested_family_sha256=family_sha256,
        state_observed_epoch=state_observed_epoch,
        claim_token=claim.get('token') if isinstance(claim, dict) else None,
        claim_generation=claim.get('generation') if isinstance(claim, dict) else None,
        stored_generation=original.get('generation') if original else None,
        scope=list(original['scope']) if original else None,
        snapshot=snapshot, snapshot_sha256=B.digest(snapshot) if snapshot else None,
        supplied_snapshot_sha256=B.digest(supplied) if supplied else None,
        signal_id=event.get('signal_id') or event.get('event_id'),
        decision_phase=event.get('decision_phase'),
        signal_age_seconds=now-event['epoch'] if event else None,
        latest_native_observation=last, current_turn_id=current_turn_id,
        price_path_segment_start=state.legacy.segment_start if state else None,
        validation_error=reason, failure_cause=reason,
        runtime_effect=False, actual_order_submitted=False)
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
    with K._LOCK:
        state = K._STATES.get(key)
        if (state is None or state.turn is None
                or state.turn['event_id'] != event['event_id']):
            return {'status': 'not_observed', 'reason': 'reversal_revision_changed'}
        start = state.segment_start
        # Native rows are append-only values; retain references briefly, then
        # compute diagnostics outside the ingestion lock.
        rows = list(state.rows)
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
