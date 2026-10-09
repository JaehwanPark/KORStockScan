"""Source observation and handoff adapters for the pinned reversal kernel.

Runtime source projection owns this module, independently of research kernel
and auxiliary input contracts. Policy/FSM definitions remain in pinned owners.
"""
from datetime import datetime
from copy import deepcopy
import math
import time
import os
import threading
from collections import OrderedDict
from pathlib import Path
from contextlib import ExitStack

try:
    _PROCESS_START_TICKS = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
except (OSError, IndexError):
    _PROCESS_START_TICKS = None

from src.engine.scalping import continuous_reversal as K

_CHANGE = threading.Condition()
_SEQUENCES = OrderedDict()


def observation_sequence(item):
    with _CHANGE:
        return _SEQUENCES.get(item, 0)


def notify_observation(item):
    """A wakeup only. Readers must inspect the producer under its own lock."""
    with _CHANGE:
        _SEQUENCES[item] = _SEQUENCES.get(item, 0) + 1
        _SEQUENCES.move_to_end(item)
        while len(_SEQUENCES) > 512:
            _SEQUENCES.popitem(last=False)
        _CHANGE.notify_all()


def wait_observation(item, sequence, timeout):
    with _CHANGE:
        _CHANGE.wait_for(lambda: _SEQUENCES.get(item, 0) != sequence, timeout=max(0, timeout))


def invalidate_observation_interval(item):
    """End a known last-owner collection interval without faking a trade tick."""
    from src.engine.scalping.reversal_current_backend import backend
    B = backend()
    owners = [B]
    if getattr(B, 'R', None) is not None:
        owners.append(B.R)
    for owner in owners:
        with owner._LOCK:
            for key in list(owner._STATES):
                if len(key) > 2 and key[2] == item:
                    owner._STATES.pop(key)
    notify_observation(item)


def observe_snapshot(symbol, venue, session, *, now, item, family_sha256,
                     live_clock=False):
    """Read the next eligible native snapshot without consuming any ready/claim.

    Uses the pinned producer's snapshot and FIRST filter on copies. Selector
    parity is tested against its real claim owner. No policy or FSM is changed.
    """
    from src.engine.scalping.reversal_current_backend import backend
    B = backend()
    with ExitStack() as locks:
        locks.enter_context(B._LOCK)
        carried = getattr(B, 'R', None)
        if carried is not None:
            locks.enter_context(carried._LOCK)
        stamp = time.time() if live_clock else now
        return _observe_snapshot_locked(B, symbol, venue, session, stamp, item, family_sha256)


def _observe_snapshot_locked(B, symbol, venue, session, now, item, family_sha256):
    stream = symbol, venue, item, K.market_bucket(session), str(datetime.fromtimestamp(now, K.KST).date())
    receipt = dict(schema='native_observation_selection_v1', observed_epoch=now,
        evaluation_role='probe_observation', process_pid=os.getpid(),
        process_start_ticks=_PROCESS_START_TICKS, item=item, venue=venue,
        family_sha256=family_sha256, reason='state_absent', runtime_effect=False)
    if not family_sha256 or B._GENERATION != family_sha256:
        return None, dict(receipt, reason='scope_or_generation_mismatch')
    candidates = []
    raw_states = [state for key, state in B._STATES.items() if key[:5] == stream]
    receipt['raw_ready_count'] = sum(len(s.ready) for s in raw_states)
    receipt['selected_ready_count'] = 0
    operating = B.__name__.endswith(('reversal_extended_runtime', 'reversal_operating_runtime'))
    if operating:
        from src.engine.scalping import reversal_extended_catalog as C
        for key, state in B._STATES.items():
            if key[:5] != stream:
                continue
            last = getattr(state.legacy, 'last', None)
            if last and C.cell_key(symbol, session, last[3]) == key[-1]:
                cell = B._FAMILY['machine_cells'][key[-1]]['routes'][venue]
                ids = [b['branch_id'] for b in cell['payload']['branches']]
                truth = {bid: getattr(state, 'coverage_snapshot', {}).get(bid, 'UNKNOWN') for bid in ids}
                receipt.update(selected_scope=key[-1], scope_execution_hash=state.generation,
                    selected_branch_truth=truth, native_epoch=last[1], native_sequence=last[2],
                    observed_seconds=max(0, last[0]-state.legacy.segment_start),
                    reason='no_matching_pattern' if truth and all(v=='FALSE' for v in truth.values())
                           else 'required_window_incomplete')
            for ready in state.ready:
                e = ready['event']
                if C.cell_key(symbol, session, e['confirmation_price']) != key[-1]:
                    continue
                if ready['claimed']:
                    receipt['reason'] = 'already_claimed'; continue
                if not 0 <= now-e['epoch'] <= 5:
                    receipt['reason'] = 'signal_expired'; continue
                candidates.append((e['epoch'], e['native_sequence'], state, ready))
        receipt['selected_ready_count'] = len({(e[3]['event']['event_id'], e[3]['event']['signal_id']) for e in candidates})
        for _, _, state, ready in sorted(candidates, key=lambda x: x[:2]):
            event, source = B.snapshot(state, ready)
            confirmed = sorted(event['branch_signals'])
            B._filter_first(event, source, state)
            if not event['branch_signals']:
                receipt['reason'] = 'native_path_changed'; continue
            event['confirmed_set'] = confirmed
            event['opportunity_key'] = B.A.opportunity(event)
            return (event, source), dict(receipt, reason='ready',
                native_event_id=event['event_id'], signal_id=event['signal_id'],
                native_deadline_epoch=event['epoch']+5,
                scope_execution_hash=state.generation)
        parent = B._FAMILY['native_parent_bundle']['continuous_reversal']['family_sha256']
        snapshot, native_receipt = _observe_snapshot_locked(B.R, symbol, venue, session, now, item, parent)
        if snapshot:
            event = snapshot[0]
            cell = B._FAMILY['machine_cells'][C.cell_key(symbol, session, event['confirmation_price'])]['routes'][venue]
            if cell['backend'] != 'registered_v4':
                return None, receipt
            return snapshot, dict(native_receipt, family_sha256=family_sha256)
        return None, receipt
    state = B._STATES.get(stream)
    if state is None:
        return None, receipt
    receipt['reason'] = 'required_window_incomplete'
    for ready in state.ready:
        event = ready['event']
        if ready['claimed']:
            receipt['reason'] = 'already_claimed'; continue
        if not 0 <= now-event['epoch'] <= 5:
            receipt['reason'] = 'signal_expired'; continue
        snapshot = state.snapshot(ready)
        if not isinstance(snapshot, tuple):
            snapshot = tuple(snapshot)
        event, source = snapshot
        selected = None
        if getattr(B, '_FAMILY', None) and hasattr(B, 'C'):
            cell = B._FAMILY['machine_cells'][B.C.cell_key(symbol, session, event['confirmation_price'])]['routes'][venue]
            selected = {b['branch_id'] for b in cell['payload']['branches']}
        for bid, signal in list(event['branch_signals'].items()):
            if ((selected is not None and bid not in selected) or
                (signal['decision_phase'] == 'FIRST_UPTICK' and
                 (not state.legacy.turn or state.legacy.turn['event_id'] != event['event_id']))):
                event['branch_signals'].pop(bid); source['branch_inputs'].pop(bid)
        if event['branch_signals']:
            return snapshot, dict(receipt, reason='ready', native_event_id=event['event_id'],
                signal_id=event['signal_id'], native_deadline_epoch=event['epoch']+5)
        receipt['reason'] = 'native_path_changed'
    return None, receipt


def claim_expected_snapshot(expected, *, live_clock=True, now=None):
    """Compare the original event and claim under the same producer locks."""
    from src.engine.scalping.reversal_current_backend import backend
    B = backend()
    with ExitStack() as locks:
        locks.enter_context(B._LOCK)
        if getattr(B, 'R', None) is not None:
            locks.enter_context(B.R._LOCK)
        stamp = time.time() if live_clock else now
        event = expected['snapshot'][0]
        snapshot, _ = _observe_snapshot_locked(B, event['symbol'], event['venue'],
            event['market'], stamp, event['source_item'], expected['family_sha256'])
        if not snapshot or any(snapshot[0].get(k) != event.get(k) for k in
                ('event_id', 'signal_id', 'native_epoch', 'native_sequence', 'epoch')):
            return None
        current_signals = snapshot[0].get('branch_signals') or {}
        original_signals = event.get('branch_signals') or {}
        if not set(current_signals).issubset(original_signals) or any(
                signal != original_signals[bid] for bid, signal in current_signals.items()):
            return None
        claim = claim_snapshot_with_receipt(event['symbol'], event['venue'], event['market'],
            now=stamp, item=event['source_item'], family_sha256=expected['family_sha256'])
        if claim is not None:
            claim['observer_snapshot_sha256'] = expected.get('snapshot_sha256')
            claim['observer_branch_ids'] = sorted(original_signals)
            claim['live_branch_ids'] = sorted(current_signals)
            claim['observation_subset_changed'] = set(current_signals) != set(original_signals)
        return claim


def observation_binding_valid(expected, *, now=None):
    """Validate the local immutable observation's original clocks and producer."""
    try:
        stamp = time.time() if now is None else now
        event = expected['snapshot'][0]
        epoch, deadline, perf = event['epoch'], expected['deadline_epoch'], expected['deadline_perf']
        return (all(type(v) in (int, float) and math.isfinite(v) and v > 0
                    for v in (epoch, deadline, perf, stamp))
                and epoch <= stamp < deadline <= epoch+5
                and time.perf_counter() < perf
                and expected['observer_pid'] == os.getpid()
                and expected.get('observer_start_ticks') == _PROCESS_START_TICKS)
    except (KeyError, TypeError, IndexError):
        return False


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
            try:
                from src.engine.monitoring.runtime_performance import record_selected_native_claim
                record_selected_native_claim(claim)
            except (KeyError, TypeError, ValueError):
                pass  # Diagnostic joins cannot revoke the native claim.
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
                        event['symbol'],event['market'],event['confirmation_price'])] if claim.get('backend') in {'registered_v4','operating_v5','operating_v6'} else []))
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
    if isinstance(claim,dict) and claim.get('backend') == 'registered_v4' and getattr(B,'R',None):
        # v6 delegates carried scopes to the original native owner. The outer
        # lock does not make that owner's registry/state observable atomically.
        with B.R._LOCK:
            receipt = _claim_failure_receipt(B.R,claim,B.R._GENERATION,now,reason)
        receipt['requested_envelope_family_sha256'] = family_sha256
        return receipt
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
        claim_backend=claim.get('backend') if isinstance(claim, dict) else None,
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
    if isinstance(claim, dict) and claim.get('backend') in {'operating_v5', 'operating_v6'}:
        # Operating claims bind to a cell execution hash, not the envelope hash.
        # Retain both identities under the same validation/ingestion lock.
        family = getattr(B, '_FAMILY', None) or {}
        cell = (family.get('machine_cells', {}).get(scope[-1], {}).get('routes', {})
                .get(scope[1], {})) if scope else {}
        receipt.update(schema='continuous_reversal_claim_source_receipt_v4',
            claim_backend=claim['backend'],
            stored_envelope_family_sha256=original.get('envelope_sha256') if original else None,
            state_generation=state.generation if state else None,
            active_scope_execution_hash=cell.get('scope_execution_hash'),
            registered_signal_ready=(any(r['event']['signal_id'] == event.get('signal_id')
                                         for r in state.ready) if state else None))
    if reason == 'reversal_signal_path_changed':
        predicates = {
            'native_state_present': state is not None,
            'legacy_last_present': bool(last),
            'latest_source_valid': bool(last[8]) if last else None,
            'native_epoch_matches': last[1] == event.get('native_epoch') if last else None,
            'first_signal_turn_matches': current_turn_id == event.get('event_id') if state and event.get('decision_phase') == 'FIRST_UPTICK' else None,
            'scope_generation_matches': getattr(state,'generation',None) == (original or {}).get('generation') if state else None,
            'ready_membership_present': any(r['event'].get('signal_id') == event.get('signal_id') for r in state.ready) if state else None,
        }
        receipt['native_predicates'] = predicates
        receipt['failed_native_predicates'] = [key for key,value in predicates.items() if value is False]
        # Keep the consumer's native lifecycle label; predicates supplement it.
        receipt['process_pid'] = os.getpid()
        receipt['process_start_ticks'] = _PROCESS_START_TICKS
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
    if native is registered and native is not K:
        key=key[:4]+(key[4].isoformat(),)
    with ExitStack() as locks:
        locks.enter_context(native._LOCK)
        if (getattr(native,'_FAMILY',None) or {}).get('schema') in {'continuous_reversal_policy_v4','continuous_reversal_policy_v5','continuous_reversal_policy_v6'}:
            from src.engine.scalping.reversal_path_catalog import cell_key
            scope=cell_key(symbol,market,event['confirmation_price'])
            key=key+(scope,)
            if (native._FAMILY['schema'] in {'continuous_reversal_policy_v5','continuous_reversal_policy_v6'}
                    and native._FAMILY['machine_cells'][scope]['routes'][venue]['backend']=='registered_v4'):
                native=native.R
                locks.enter_context(native._LOCK)
        state = native._STATES.get(key)
        if state is not None and hasattr(state, 'legacy'):
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
