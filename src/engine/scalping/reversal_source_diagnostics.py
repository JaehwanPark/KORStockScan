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
from functools import lru_cache

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


def _required_definition(definition):
    """Resolve optional refinements to their unchanged native confirmation."""
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.scalping import reversal_cumulative_catalog as Q
    if definition.get('kind') in {'composed_confirmation_refinement', 'cumulative_refinement'}:
        return _required_definition(C.definition(definition['original_definition_ref']['branch_id']))
    if definition.get('kind') == 'cumulative_root':
        return dict(definition, root_contract=Q.root_contract(definition['root_confirmation']))
    return definition


def _filter_fields(filters):
    from src.engine.scalping import reversal_cumulative_catalog as Q
    fields = set()
    for name, value in filters.items():
        if name in {'when','require'} and isinstance(value,dict):
            fields.update(_filter_fields(value))
        for feature in ('ret','vwap','volume','buy10','dd','session','structure','low_rising',*Q.FIELDS):
            if name == feature or name.startswith(feature+'_'):
                fields.add(Q.FIELDS.get(feature,feature))
    return fields


def branch_required_seconds(definition):
    """Lower bound on native history, not a promise that a pattern will fire."""
    definition = _required_definition(definition)
    root = definition.get('root_contract') or {}
    filters = definition.get('filters') or {}
    fields = _filter_fields(filters)
    required = float(root.get('warmup_seconds') or 0)
    if (definition.get('return_60s_min_pct') is not None or definition.get('higher_low')
            or root.get('return_60s_min_pct') is not None):
        required = max(required, 60.)
    if fields & {'ret','vwap','structure','low_rising'}:
        required = max(required, 60.)
    if ('volume' in fields
            or definition.get('rule') in {'VOLUME_RATIO_GE_1_5', 'DROP_0_4_VOL_UP', 'DD5_0_8_VOL_UP'}):
        required = max(required, 120.)
    if 'bid_return30_pct' in fields:required = max(required,30.)
    return required + float(root.get('hold_seconds') or 0)


@lru_cache(maxsize=512)
def _branch_descriptor(registry_sha256, bid):
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.scalping.continuous_reversal_postclose import digest
    d = C.definition(bid)
    original=d
    optional_fields=[]
    if d.get('kind')=='composed_confirmation_refinement':
        optional_fields=[d['conditional_refinement']['feature']]
    elif d.get('kind')=='cumulative_refinement':
        optional_fields=sorted(_filter_fields(d['filters']))
    d=_required_definition(d)
    root, filters = d.get('root_contract') or {}, d.get('filters') or {}
    phase = C.branch(bid).get('decision_phase')
    hold = float(root.get('hold_seconds') or 0)
    seconds = branch_required_seconds(d)
    fields = _filter_fields(filters)
    if root.get('return_60s_min_pct') is not None:
        fields.add('ret')
    if d.get('rule') in {'VOLUME_RATIO_GE_1_5', 'DROP_0_4_VOL_UP', 'DD5_0_8_VOL_UP'}:
        fields.add('volume')
    if d.get('return_60s_min_pct') is not None:
        fields.add('ret')
    if d.get('higher_low'):
        fields.add('low_rising')
    return dict(branch_id=bid, definition_sha256=digest(original), registry_sha256=registry_sha256,
        backward_window_seconds=seconds-hold, minimum_seconds=seconds,
        hold_seconds=hold, decision_phase=phase,
        confirmation_window_seconds=d.get('confirmation_seconds') or root.get('maximum_wait_seconds'),
        predecessor_required='ret' in fields or bool(d.get('return_60s_min_pct')),
        minimum_trade_count=10 if fields & {'buy10','return10_pct','bid_return10_pct',
            'range_spread10','price_progress_spreads10'} else None,
        known_side_required='buy10' in fields,
        positive_quantity_required=bool(fields & {'buy10', 'vwap', 'volume'}),
        prefix_spread_denominator=('bid' if d.get('kind') in {'legacy_rule', 'registered_pattern'}
            else 'trade' if d.get('kind') in {'manual_path_pattern', 'cumulative_root'} else None),
        transition_required=phase in {'MOMENTUM_CROSS', 'MOMENTUM_HOLD', 'HIGH_BREAKOUT'},
        feature_fields=sorted(fields), optional_refinement_fields=optional_fields, root_contract=deepcopy(root))


def residence_requirements(candidate, now, *, actual_price=None):
    """Use selected definitions only. Never stitch histories across leases."""
    from src.engine.scalping.reversal_current_backend import backend
    from src.engine.scalping import reversal_extended_catalog as C
    from src.trading.market import session_contract
    B = backend()
    route = {'nxt_only': 'NXT', 'krx_only': 'KRX', 'krx_nxt_integrated': 'SOR'}.get(candidate.route)
    market = K.market_bucket(session_contract.resolve_market_session(
        datetime.fromtimestamp(now, K.KST)).session_regime)
    with B._LOCK:
        family = getattr(B, '_FAMILY', None) or {}
        key = C.cell_key(candidate.code, market,
                         candidate.discovery_price if actual_price is None else actual_price)
        cell = family.get('machine_cells', {}).get(key, {}).get('routes', {}).get(route, {})
        branches = tuple(b['branch_id'] for b in cell.get('payload', {}).get('branches', ()))
        generation = family.get('family_sha256')
        scope_hash = cell.get('scope_execution_hash')
        registry_hash = family.get('registry_sha256') or C.registry_for(branches)
    if not branches:
        return dict(status='unobservable', reason='selected_branches_missing', minimum_seconds=None)
    try:
        descriptors = {bid: deepcopy(_branch_descriptor(registry_hash, bid)) for bid in branches}
        requirements = {bid: row['minimum_seconds'] for bid, row in descriptors.items()}
    except (KeyError, TypeError, ValueError):
        return dict(status='unobservable', reason='branch_requirement_unknown', minimum_seconds=None)
    return dict(schema='native_branch_residence_requirements_v2', status='observed',
        minimum_seconds=min(requirements.values()), any_branch_minimum_seconds=min(requirements.values()),
        full_input_requirement_seconds=max(requirements.values()), branch_descriptors=descriptors,
        policy_scope=key, price_basis='tentative_discovery' if actual_price is None else 'exact_native_trade',
        registry_sha256=registry_hash,
        branch_required_seconds=requirements, family_sha256=generation, scope_execution_hash=scope_hash,
        history_reuse='none_without_exact_lease_interval', runtime_effect=False)


def _cumulative_pending(state):
    """Map shared causal roots back to their selected branch dependencies."""
    from src.engine.scalping import reversal_cumulative_catalog as Q
    detector=getattr(state,'cumulative',None)
    if detector is None:return {}
    roots={p['root_confirmation']:p['epoch'] for p in detector.pending.values()}
    result={}
    for bid in state.operating_ids:
        definition=_required_definition(Q.DEFINITIONS[bid]) if bid in Q.DEFINITIONS else None
        if definition and definition.get('root_confirmation') in roots:
            result[bid]=roots[definition['root_confirmation']]
    return result


def branch_readiness(candidate, *, now, deadline, original_requirements=None):
    """Project detector-owned scalar coverage, never replay or manufacture truth."""
    from src.engine.scalping.reversal_current_backend import backend
    from src.engine.scalping import reversal_extended_catalog as C
    from src.trading.market import session_contract as S
    B = backend()
    venue = {'nxt_only': 'NXT', 'krx_only': 'KRX', 'krx_nxt_integrated': 'SOR'}.get(candidate.route)
    market = K.market_bucket(S.resolve_market_session(datetime.fromtimestamp(now, K.KST)).session_regime)
    item = candidate.code + {'SOR': '_AL', 'NXT': '_NX', 'KRX': ''}.get(venue, '')
    stream = (candidate.code, venue, item, market, str(datetime.fromtimestamp(now, K.KST).date()))
    facts = None
    with ExitStack() as locks:
        locks.enter_context(B._LOCK)
        if getattr(B, 'R', None) is not None:
            locks.enter_context(B.R._LOCK)
        for owner in (B, getattr(B, 'R', None)):
            if owner is None:
                continue
            for key, state in owner._STATES.items():
                last = getattr(getattr(state, 'legacy', None), 'last', None)
                if key[:5] != stream or not last:
                    continue
                if type(last[3]) not in (int, float) or not math.isfinite(last[3]) or last[3] <= 0:
                    continue
                cell_key = C.cell_key(candidate.code, market, last[3])
                cell = (getattr(B, '_FAMILY', None) or {}).get('machine_cells', {}).get(cell_key, {}).get('routes', {}).get(venue, {})
                if ((owner is B and (key[-1] != cell_key or cell.get('backend') == 'registered_v4'))
                        or (owner is not B and cell.get('backend') != 'registered_v4')):
                    continue
                expected_generation = cell.get('scope_execution_hash') if owner is B else owner._GENERATION
                if state.generation != expected_generation:
                    continue
                facts = dict(last=tuple(last), start=state.legacy.segment_start,
                    coverage=dict(getattr(state, 'coverage_snapshot', {})),
                    root=dict(getattr(state, 'root_previous', {}), **getattr(state, 'extended_previous', {})),
                    features=dict(getattr(state, '_feature_values', None) or {}),
                    diagnostic_features=deepcopy(getattr(state, 'diagnostic_features', {})),
                    diagnostic_rolling=deepcopy(getattr(state, 'diagnostic_rolling', None)),
                    feature_identity=getattr(state, '_feature_key', None),
                    coverage_identity=getattr(state, 'coverage_identity', None),
                    family_sha256=getattr(B, '_GENERATION', None),
                    pending={p.get('bid'): p.get('epoch') for p in getattr(state, 'path_pending', {}).values()
                             if p.get('bid')})
                facts['pending'].update(_cumulative_pending(state))
                progress=getattr(getattr(state,'cumulative',None),'progress',None)
                if progress and progress.last is not None and tuple(progress.last[:3])==tuple(last[:3]):
                    rolling=facts['diagnostic_rolling']
                    if rolling and rolling.get('identity')==tuple(last[:3]):
                        rolling['values'].update(progress.values)
                break
            if facts:
                break
    if not facts:
        return dict(status='unobservable', reason='native_interval_unobserved',
                    remaining_seconds=max(0, deadline-now), decision_authority='none')
    last = facts['last']
    desc = residence_requirements(candidate, now, actual_price=last[3])
    if desc.get('status') != 'observed':
        return dict(desc, remaining_seconds=max(0, deadline-now), decision_authority='none')
    if desc.get('family_sha256') != facts['family_sha256']:
        return dict(status='unobservable', reason='policy_changed_during_projection', decision_authority='none')
    valid = bool(last[8] and 0 <= now-last[0] <= 3)
    quote_usable = bool(valid and K.good_quote(last))
    covered = max(0, last[0]-facts['start']) if valid and facts['start'] is not None else None
    desc.update(interval_start_epoch=facts['start'], interval_end_epoch=last[0],
        continuous_covered_seconds=covered, native_epoch=last[1], native_sequence=last[2],
        item=item, route=candidate.route, remaining_seconds=max(0, deadline-now),
        scope_changed=any((original_requirements or {}).get(k) != desc.get(k)
                          for k in ('policy_scope', 'scope_execution_hash', 'family_sha256')),
        decision_authority='none')
    feature_bound = facts['feature_identity'] == tuple(last[:3])
    coverage_bound = facts['coverage_identity'] == tuple(last[:3])
    for bid, row in desc.get('branch_descriptors', {}).items():
        actual = facts['diagnostic_features'].get(bid) or {}
        rolling = facts['diagnostic_rolling'] or {}
        projection = (actual if actual.get('identity') == tuple(last[:3]) else
                      rolling if rolling.get('identity') == tuple(last[:3]) else {})
        values = projection.get('values', facts['features'])
        # Rolling caches contain trade features; native spread is an event
        # quote fact. Project only a missing prefix key from this same current
        # row, using its owner's denominator. Explicit UNKNOWN confirmations
        # and producer values remain untouched; this never evaluates a gate.
        if (feature_bound and quote_usable and projection is rolling and projection
                and 'spread' in row['feature_fields'] and 'spread' not in values
                and all(type(v) in (int, float) and math.isfinite(v) for v in last[3:6])):
            basis = row['prefix_spread_denominator']
            if basis in {'bid', 'trade'}:
                spread = (100*(last[5]/last[4]-1) if basis == 'bid'
                          else 100*(last[5]-last[4])/last[3])
                if math.isfinite(spread):
                    values = dict(values, spread=spread)
        missing = [field for field in row['feature_fields']
                   if not feature_bound or values.get(field) is None]
        if not quote_usable:
            missing.append('executable_quote')
        if covered is None:
            missing.append('continuous_source_interval')
        elif covered < row['backward_window_seconds']:
            missing.append('backward_window')
        condition = facts['root'].get(bid)
        # Root predicate value is not the FALSE->TRUE event or its hold outcome.
        row.update(detector_truth=facts['coverage'].get(bid, 'UNKNOWN') if valid and coverage_bound else 'UNKNOWN',
            native_quote_usable=quote_usable,
            feature_basis='actual_branch_confirmation' if projection is actual and actual else 'prefix_context_no_confirmation',
            feature_identity=tuple(last[:3]) if feature_bound else None,
            feature_values={field: values.get(field) for field in row['feature_fields']},
            root_condition_truth=('TRUE' if condition is True else 'FALSE' if condition is False else 'UNKNOWN') if valid else 'UNKNOWN',
            feature_availability='complete' if not missing else 'incomplete', missing_inputs=missing,
            pending_confirmation_epoch=facts['pending'].get(bid),
            window_fits_remaining=covered is not None and
                max(0, row['backward_window_seconds']-covered)+row['hold_seconds'] < desc['remaining_seconds'])
    return desc


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
                     live_clock=False, original_root=None):
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
        snapshot, receipt = _observe_snapshot_locked(B, symbol, venue, session, stamp, item, family_sha256)
        if original_root is not None:
            from src.engine.monitoring.runtime_performance import native_ready_lifecycle
            receipt['original_signal_lifecycle'] = native_ready_lifecycle(original_root, family_sha256)
        return snapshot, receipt


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
                fresh = bool(last[8] and 0 <= now-last[0] <= 3)
                truth = {bid: getattr(state, 'coverage_snapshot', {}).get(bid, 'UNKNOWN') if fresh else 'UNKNOWN' for bid in ids}
                receipt.update(selected_scope=key[-1], scope_execution_hash=state.generation,
                    selected_branch_truth=truth, native_epoch=last[1], native_sequence=last[2],
                    native_last_received_epoch=last[0], native_source_current=fresh,
                    native_quote_current=bool(fresh and K.good_quote(last)),
                    observed_seconds=max(0, last[0]-state.legacy.segment_start),
                    reason='no_matching_pattern' if truth and all(v=='FALSE' for v in truth.values())
                           else 'required_window_incomplete')
                receipt['selected_pending_count']=sum(len(getattr(state,attr,{}))
                    for attr in ('pending','path_pending','extended_pending'))
                receipt['selected_pending_count']+=len(getattr(getattr(state,'cumulative',None),'pending',{}))
                receipt['selected_lifecycle_counts']={b:dict(getattr(state,'coverage_counts',{}).get(b,{})) for b in ids}
                receipt['source_censored_count']=getattr(state,'coverage_source_censored',0)
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
        try:
            from src.engine.monitoring.runtime_performance import record_native_visit
            symbol = args[0] if args else kwargs['symbol']
            venue = args[1] if len(args) > 1 else kwargs['venue']
            session = args[2] if len(args) > 2 else kwargs['session']
            record_native_visit(symbol, venue, kwargs['item'], K.market_bucket(session), kwargs['now'])
        except (KeyError, TypeError, ValueError, IndexError):
            pass
        claim = B.claim_snapshot(*args, **kwargs)
        if claim:
            try:
                from src.engine.monitoring.runtime_performance import record_selected_native_claim
                record_selected_native_claim(claim, family_sha256=kwargs.get('family_sha256'), now=kwargs['now'])
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
                                live_clock=False, receipt_out=None):
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
            result = B.validate_claim(claim, family_sha256, now=now)
            if receipt_out is not None:
                try:
                    receipt_out.update(compact_claim_state(B, claim, family_sha256, now, 'valid'))
                except Exception:
                    receipt_out.update(status='unobservable', validation_error='diagnostic_projection_failed')
            return result
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
            if receipt_out is not None:
                try:
                    receipt_out.update(compact_claim_state(B, claim, family_sha256, now, str(exc)))
                except Exception:
                    receipt_out.update(status='unobservable', validation_error=str(exc))
            raise


def compact_claim_state(B, claim, family_sha256, now, reason):
    """Called under the native lock. Scalars only; no raw input duplication."""
    if claim.get('backend') == 'registered_v4' and getattr(B, 'R', None):
        with B.R._LOCK:
            result = compact_claim_state(B.R, claim, B.R._GENERATION, now, reason)
        result['envelope_family_sha256'] = family_sha256
        from src.engine.scalping.reversal_extended_catalog import cell_key
        event = claim['snapshot'][0]
        cell = (B._FAMILY.get('machine_cells', {}).get(cell_key(event['symbol'], event['market'],
            event['confirmation_price']), {}).get('routes', {}).get(event['venue'], {}))
        result['envelope_scope_execution_hash'] = cell.get('scope_execution_hash')
        return result
    original = B._CLAIMS.get(claim.get('token')) or {}
    event = (claim.get('snapshot') or [{}])[0]
    scope = original.get('scope')
    state = B._STATES.get(scope) if scope else None
    legacy = getattr(state, 'legacy', None)
    last = getattr(legacy, 'last', None)
    turn = (getattr(legacy, 'turn', None) or {}).get('event_id')
    branches = event.get('branch_signals') or {}
    survivors = {bid: (signal.get('decision_phase') != 'FIRST_UPTICK'
                       or turn == signal.get('event_id', event.get('event_id')))
                 for bid, signal in branches.items()}
    for bid,signal in branches.items():
        if signal.get('decision_phase')=='FIRST_PRICE_HOLD':
            survivors[bid]=bool(state and any(
                r['event'].get('signal_id')==event.get('signal_id')
                and bid in r['event'].get('branch_signals',{}) for r in state.ready))
    from src.engine.scalping.reversal_extended_catalog import cell_key
    band = cell_key(event['symbol'], event['market'], event['confirmation_price']) if event.get('confirmation_price') else None
    cell = ((getattr(B, '_FAMILY', None) or {}).get('machine_cells', {})
            .get(band, {}).get('routes', {}).get(event.get('venue'), {}))
    predicates = dict(registered_claim_present=bool(original), native_state_present=state is not None,
        latest_source_valid=bool(last[8]) if last else None,
        latest_quote_valid=K.good_quote(last) if last else None,
        native_epoch_matches=last[1] == event.get('native_epoch') if last else None,
        scope_generation_matches=getattr(state, 'generation', None) == claim.get('generation') if state else None,
        ready_membership_present=any(r['event'].get('signal_id') == event.get('signal_id')
                                     for r in state.ready) if state else None,
        any_branch_survives=any(survivors.values()) if branches else None,
        original_deadline_valid=0 <= now-event['epoch'] <= 5 if event.get('epoch') else None)
    return dict(schema='native_commit_revalidation_v1', stage='commit_revalidation', status='observed',
        validation_epoch=now, validation_perf=time.perf_counter(), validation_error=reason,
        process_pid=os.getpid(), process_start_ticks=_PROCESS_START_TICKS,
        claim_backend=claim.get('backend'), envelope_family_sha256=family_sha256,
        claim_generation=claim.get('generation'), active_generation=B._GENERATION,
        scope_execution_hash=cell.get('scope_execution_hash'),
        registration_sha256=(claim.get('source_registration_receipt') or {}).get('sha256'),
        signal_id=event.get('signal_id'), native_event_id=event.get('event_id'),
        source_item=event.get('source_item'), venue=event.get('venue'), market=event.get('market'),
        native_epoch=event.get('native_epoch'), native_sequence=event.get('native_sequence'),
        signal_epoch=event.get('epoch'), original_deadline=event.get('epoch', now)+5,
        remaining_seconds=event.get('epoch', now)+5-now,
        branch_survival=survivors, current_turn_id=turn,
        latest_native_epoch=last[1] if last else None, latest_native_sequence=last[2] if last else None,
        latest_price=last[3] if last else None, latest_received_epoch=last[0] if last else None,
        predicates=predicates, failed_predicates=[k for k,v in predicates.items() if v is False],
        runtime_effect=False)


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
