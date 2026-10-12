"""Bounded latency diagnostics, emitted with the existing loop log writer.

Does not change policy, quotas or order guards. Measured response processing
reserves timeout budget only. All completed loops are sampled.
"""
import json
import math
import os
import time
from collections import deque, OrderedDict
from pathlib import Path
from threading import Lock

_LOCK = Lock()
_LIMIT = 4096
_NAMES = ('loop_work', 'loop_work_warm', 'loop_first', 'policy_prepare',
          'policy_load', 'policy_release_check', 'policy_consumer_check', 'ws_lock_wait', 'ws_lock_hold',
          'ws_snapshot', 'confirmed_to_claim', 'claim_to_machine',
          'provider_response', 'machine_to_provider_response', 'provider_response_to_pre_submit',
          'preparation_queue', 'preparation_service', 'source_prepare', 'capacity_prepare',
          'provider_key_wait', 'provider_transport', 'response_validate', 'main_commit', 'submit_guard',
          'capture_append', 'provider_reserve', 'order_acknowledgement', 'pipeline_source_replay',
          'observation_queue_wait')
_SAMPLES = {name: deque(maxlen=_LIMIT) for name in _NAMES}
_TOTAL = {name: 0 for name in _NAMES}
_BOUNDS = (.01, .05, .1, .25, .5, 1., 1.5, 2., 3., 5., 10., float('inf'))
_HIST = {name: [0]*len(_BOUNDS) for name in _NAMES}
_OVER5 = {name: 0 for name in _NAMES}
_UNDER5 = {name: 0 for name in _NAMES}
_AT_MOST2 = {name: 0 for name in _NAMES}
_READY = OrderedDict()
_SELECTED_READY = OrderedDict()
_SELECTED_EVICTED = {'claimed': 0, 'expired_before_claim': 0, 'unobservable': 0}
_LIFECYCLE_EVICTED = {}
_LIFECYCLE_PENDING = OrderedDict()
_LIFECYCLE_APPEND_DROPPED = 0
_LIFECYCLE_SINK = None
_NATIVE_READY_EVENT = None


def set_native_ready_event(event):
    """Existing Main wait event only; no callback, I/O, claim or new worker."""
    global _NATIVE_READY_EVENT
    with _LOCK:
        _NATIVE_READY_EVENT = event
_ACTIVE_SELECTED = {}  # stream -> bounded active keys, never all-day scans per tick
_LIFECYCLE_STATES = ('claimed', 'invalidated_before_claim', 'replaced_before_claim',
    'observed_valid_until_deadline_unclaimed', 'source_or_guard_blocked_before_claim',
    'not_yet_due', 'unobservable')
_COVERAGE = {kind: {'ready':0,'claimed':0} for kind in ('fixed_watch','other')}
_TIMELINES = deque(maxlen=128)
_GENERATION = None
_STARTED = time.time()
try:
    _PROCESS_START_TICKS = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
except (OSError, IndexError):
    _PROCESS_START_TICKS = None
_SIGNALS = OrderedDict()
_FAILURES = OrderedDict()
_CIRCUIT = {'state':'not_observed'}
_OBSERVATION_HEALTH = None


def set_observation_health(provider):
    global _OBSERVATION_HEALTH
    _OBSERVATION_HEALTH = provider


def set_lifecycle_sink(sink):
    global _LIFECYCLE_SINK
    _LIFECYCLE_SINK = sink


def _queue_lifecycle(key, row):
    global _LIFECYCLE_APPEND_DROPPED
    # Called with diagnostic lock only; no writer/provider or native callback.
    _LIFECYCLE_PENDING[key] = dict(row)
    if len(_LIFECYCLE_PENDING) > 128:
        _LIFECYCLE_PENDING.popitem(last=False)
        _LIFECYCLE_APPEND_DROPPED += 1


def _append_lifecycle(row):
    from src.utils.pipeline_event_logger import emit_pipeline_event
    scope = row['scope']
    return emit_pipeline_event('ENTRY_PIPELINE', scope[0], scope[0], 'native_signal_lifecycle',
        fields=dict(native_signal_lifecycle=json.dumps(row, sort_keys=True, separators=(',', ':')),
            source_date=scope[4], native_signal_id=row['signal_id'],
            runtime_effect=False, actual_order_submitted=False, broker_order_forbidden=True))


def flush_lifecycle():
    global _LIFECYCLE_APPEND_DROPPED
    if _LIFECYCLE_SINK is None:
        return
    with _LOCK:
        now = time.time()
        for stream, keys in list(_ACTIVE_SELECTED.items()):
            for key in tuple(keys):
                row = _SELECTED_READY.get(key)
                if row and not row.get('terminal') and now >= row['original_deadline']:
                    row.update(terminal='unobservable', terminal_reason='deadline_continuity_unobserved')
                    _queue_lifecycle(key, row)
                if row is None or row.get('terminal'):
                    keys.discard(key)
            if not keys:
                _ACTIVE_SELECTED.pop(stream, None)
        pending = list(_LIFECYCLE_PENDING.values())
        _LIFECYCLE_PENDING.clear()
    for row in pending:
        try:
            result = _LIFECYCLE_SINK(_append_lifecycle, row)
            if not isinstance(result, dict) or result.get('status') != 'queued':
                raise ValueError('lifecycle_append_admission_unconfirmed')
        except Exception:
            with _LOCK:
                _LIFECYCLE_APPEND_DROPPED += 1
            failure('native_lifecycle', 'append_admission_failed', emit_log=False)


def observe_ai_circuit(*, failures, disabled):
    with _LOCK:
        _CIRCUIT.update(state='disabled' if disabled else 'enabled',
                        consecutive_failures=int(failures), observed_epoch=time.time())


def failure(stage, reason, *, emit_log=True):
    """Bounded failure evidence; never convert source-invalid into success."""
    key = (str(stage)[:48], str(reason)[:160])
    with _LOCK:
        count, last = _FAILURES.get(key, (0, 0.0))
        now = time.monotonic()
        emit = now - last >= 60
        if key not in _FAILURES and len(_FAILURES) >= 16:
            _FAILURES.popitem(last=False)
        _FAILURES[key] = (count + 1, now if emit else last)
    if emit and emit_log:
        from src.utils.logger import log_info
        log_info('[RUNTIME_PREPARATION_FAILURE] ' + json.dumps(dict(stage=key[0], reason=key[1], pid=os.getpid(), decision_authority='none')))


def machine_signal_id(fields):
    """Read an optional diagnostic identity without interpreting a decision.

    Source-invalid preflight uses a string in the same legacy result field.
    Missing/malformed telemetry cannot become an execution-path exception.
    """
    decision = fields.get('entry_mechanistic_policy_decision') if isinstance(fields, dict) else None
    if not isinstance(decision, dict):
        return None
    assessment = decision.get('continuous_reversal_assessment') or decision
    if not isinstance(assessment, dict):
        return None
    value = assessment.get('signal_id') or assessment.get('event_id')
    return value if isinstance(value, str) and value else None


def mark_signal(signal_id, stage, *, identity=None):
    """At most 128 in-process stage clocks; missing joins stay unobservable."""
    if not signal_id or stage not in {'claim', 'machine', 'provider', 'submit', 'pre_submit', 'guard_done', 'actual_submit'}:
        return
    now = time.perf_counter()
    sample = None
    with _LOCK:
        if stage == 'claim':
            if signal_id not in _SIGNALS:
                if len(_SIGNALS) >= 128:
                    _SIGNALS.popitem(last=False)
                _SIGNALS[signal_id] = {'claim': now}
                if signal_id in _READY:
                    _COVERAGE[_READY[signal_id]['kind']]['claimed'] += 1
                    _SIGNALS[signal_id]['identity'] = _READY[signal_id]
        elif signal_id in _SIGNALS:
            clocks = _SIGNALS[signal_id]
            if isinstance(identity,dict):
                clocks.setdefault('evidence',{}).update({k:str(v)[:160] for k,v in identity.items()
                    if k in {'evaluation_attempt_id','ai_request_id','source_registration_sha256','opportunity_key','request_identity','status'}})
            prior, metric = {'machine': ('claim', 'claim_to_machine'),
                             'provider': ('machine', 'machine_to_provider_response'),
                             'submit': ('provider', 'provider_response_to_pre_submit'),
                             'pre_submit': ('provider', 'provider_response_to_pre_submit'),
                             'guard_done': ('pre_submit', 'submit_guard'),
                             'actual_submit': ('guard_done', 'order_acknowledgement')}[stage]
            if prior in clocks and stage not in clocks:
                sample = (metric, now - clocks[prior])
                clocks[stage] = now
            if stage == 'actual_submit':
                _TIMELINES.append(dict(signal_id=signal_id, stages=dict(clocks), actual_submit=True))
                _SIGNALS.pop(signal_id, None)
    if sample is not None:
        observe(*sample)


def observe(name, seconds, *, generation=None):
    global _GENERATION, _STARTED
    if name not in _SAMPLES or not math.isfinite(seconds) or seconds < 0:
        return
    with _LOCK:
        if generation is not None and generation != _GENERATION:
            _SIGNALS.clear()
            for values in _SAMPLES.values():
                values.clear()
            for key in _TOTAL:
                _TOTAL[key] = 0
                _HIST[key] = [0]*len(_BOUNDS)
                _OVER5[key] = 0
                _UNDER5[key] = 0
                _AT_MOST2[key] = 0
            _GENERATION = generation
            _STARTED = time.time()
        _SAMPLES[name].append(seconds)
        _TOTAL[name] += 1
        _OVER5[name] += seconds > 5
        _UNDER5[name] += seconds < 5
        _AT_MOST2[name] += seconds <= 2
        _HIST[name][next(i for i,b in enumerate(_BOUNDS) if seconds <= b)] += 1
        if name == 'loop_work':
            stage = 'loop_first' if _TOTAL[name] == 1 else 'loop_work_warm'
            _SAMPLES[stage].append(seconds)
            _TOTAL[stage] += 1
            _OVER5[stage] += seconds > 5
            _UNDER5[stage] += seconds < 5
            _AT_MOST2[stage] += seconds <= 2
            _HIST[stage][next(i for i,b in enumerate(_BOUNDS) if seconds <= b)] += 1


def snapshot():
    with _LOCK:
        samples = {k: list(v) for k, v in _SAMPLES.items()}
        totals = dict(_TOTAL)
        hist = {k:list(v) for k,v in _HIST.items()}
        over5 = dict(_OVER5)
        under5, at_most2 = dict(_UNDER5), dict(_AT_MOST2)
        coverage = {k:dict(v) for k,v in _COVERAGE.items()}
        timelines = list(_TIMELINES)
        inflight = {k:dict(v) for k,v in _SIGNALS.items()}
        generation, started = _GENERATION, _STARTED
        circuit = dict(_CIRCUIT)
        failures = [dict(stage=k[0], reason=k[1], count=v[0]) for k, v in _FAILURES.items()]
        selected = [dict(v) for v in _SELECTED_READY.values()]
        selected_counts = dict(_SELECTED_EVICTED, pending=0)
        lifecycle_counts = {k: _LIFECYCLE_EVICTED.get(k, 0) for k in _LIFECYCLE_STATES}
        lifecycle_append_dropped = _LIFECYCLE_APPEND_DROPPED
    selected_as_of = time.time()
    for row in selected:
        state = ('claimed' if row['claimed'] else 'expired_before_claim'
                 if selected_as_of >= row['epoch']+5 else 'pending')
        selected_counts[state] += 1
        terminal = row.get('terminal') or ('not_yet_due' if selected_as_of < row['epoch']+5 else 'unobservable')
        lifecycle_counts[terminal] += 1
    metrics = {}
    for name, values in samples.items():
        values.sort()
        n = len(values)
        metrics[name] = dict(n=n, total_observed=totals[name], retained_limit=_LIMIT,
            p95_seconds=values[math.ceil(n * .95)-1] if n else None,
            p99_seconds=values[math.ceil(n * .99)-1] if n else None,
            max_seconds=max(values) if n else None,
            over_five_seconds=sum(v > 5 for v in values),
            cumulative_over_five_seconds=over5[name],
            cumulative_under_five_seconds=under5[name],
            cumulative_at_most_two_seconds=at_most2[name],
            quantile_definition='nearest_rank_ceil_n_times_p',
            cumulative_histogram=dict(zip(('0.01','0.05','0.1','0.25','0.5','1','1.5','2','3','5','10','inf'),hist[name])),
            state='observed' if n else 'unobservable_or_not_invoked')
    return dict(schema='main_runtime_performance_v1', pid=os.getpid(),
        process_start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
        cwd=os.getcwd(), code_root=str(Path(__file__).resolve().parents[3]),
        bundle_sha256=generation, started_epoch=started, observed_epoch=time.time(),
        metric_reset_identity=f'{os.getpid()}:{started:.6f}:{generation}',
        metric_role='runtime_performance_diagnostic', decision_authority='none',
        window_policy='exact_pid_release_policy_scope_and_load_window',
        sample_floor='none_counts_and_unobservable_explicit',
        primary_decision_metric='latency_distribution_and_contract_parity',
        source_quality_gate='exact_identity_monotonic_duration_and_sample_coverage',
        forbidden_uses='policy_promotion_order_authority_or_economic_claim',
        signal_denominator='native_ready_seen_at_ingress_and_claimed_missing_joins_not_inferred',
        metrics=metrics, preparation_failures=failures,
        observation_queue=_OBSERVATION_HEALTH() if _OBSERVATION_HEALTH else {'status': 'not_installed'},
        ai_circuit=circuit,
        ready_coverage=coverage, ready_coverage_basis='native_ready_seen_at_ingress_not_all_market_opportunities',
        ready_coverage_window='process_lifetime',
        selected_native_coverage=dict(count=sum(selected_counts.values()), **selected_counts,
            age_only_not_delivery_failure=True, as_of=selected_as_of, retained=len(selected), scope='selected_backend_price_band_generation',
            coverage='process_ingress_only_not_all_market_opportunities'),
        native_signal_lifecycle=dict(schema='native_signal_lifecycle_v1', counts=lifecycle_counts,
            count=sum(lifecycle_counts.values()), recent=selected[-32:],
            append_admission_dropped=lifecycle_append_dropped,
            coverage='observed_snapshots_only_no_inferred_continuity', runtime_effect=False),
        recent_terminal_timelines=timelines, retained_signal_timelines=inflight)


def log_snapshot():
    from src.utils.logger import log_info
    try:
        flush_lifecycle()
        value = snapshot()
        from src.utils.kiwoom_transport_telemetry import snapshot as transport_snapshot
        value['kiwoom_transport'] = transport_snapshot()
    except (OSError, ValueError, IndexError) as exc:
        value = dict(schema='main_runtime_performance_v1', state='unobservable',
                     reason=type(exc).__name__, decision_authority='none')
    log_info('[RUNTIME_PERFORMANCE] ' + json.dumps(value, separators=(',', ':')))


def record_native_ready(B, symbol, venue, item, market, epoch):
    from contextlib import ExitStack
    # Match claim/observation adapter lock ordering. Publish the scalar receipt
    # before another thread can claim the event; no I/O under either lock.
    with ExitStack() as locks:
        locks.enter_context(B._LOCK)
        if getattr(B, 'R', None) is not None:
            locks.enter_context(B.R._LOCK)
        notify = _record_native_ready_locked(B, symbol, venue, item, market, epoch)
    event = _NATIVE_READY_EVENT
    if notify and event is not None:
        event.set()


def _record_native_ready_locked(B, symbol, venue, item, market, epoch):
    """Peek sealed native ready membership, before Main claim admission."""
    day = __import__('datetime').datetime.fromtimestamp(epoch, __import__('zoneinfo').ZoneInfo('Asia/Seoul')).date().isoformat()
    records = []
    selected = []
    states = {}
    notify = False
    for native in (B, getattr(B, 'R', None)):
        if native is None or not hasattr(native, '_STATES'):
            continue
        with native._LOCK:
            for scope,state in list(native._STATES.items()):
                if tuple(scope[:4]) != (symbol,venue,item,market) or str(scope[4]) != day:
                    continue
                legacy = getattr(state, 'legacy', None)
                last = getattr(legacy, 'last', None)
                states[tuple(scope)] = dict(turn=(getattr(legacy, 'turn', None) or {}).get('event_id'),
                    last=tuple(last) if last else None,
                    ready_event_ids=tuple(r['event'].get('event_id') for r in state.ready),
                    ready_ids=tuple(r['event'].get('signal_id') for r in state.ready))
                for ready in getattr(state,'ready', ()):
                    event=ready.get('event') if isinstance(ready,dict) else None
                    if event and 0 <= epoch-float(event['epoch']) <= 5:
                        records.append((event.get('signal_id') or event.get('event_id'),
                            dict(symbol=symbol, venue=venue, item=item, market=market, day=day,
                                 native_epoch=event.get('native_epoch'), epoch=event['epoch'],
                                 scope_execution_hash=getattr(state,'generation',None))))
                        family = getattr(B, '_FAMILY', None) or {}
                        if family.get('schema') in {'continuous_reversal_policy_v5', 'continuous_reversal_policy_v6'}:
                            from src.engine.scalping.reversal_extended_catalog import cell_key
                            band = cell_key(symbol, market, event['confirmation_price'])
                            cell = family['machine_cells'][band]['routes'][venue]
                            expected_backend = cell['backend']
                            selected_scope = ((native is B and scope[-1] == band
                                and expected_backend in {'union_v5','union_v6'}
                                and state.generation == cell['scope_execution_hash'])
                                or (native is not B and expected_backend == 'registered_v4'
                                    and state.generation == native._GENERATION))
                            if selected_scope:
                                branches = set(event.get('branch_signals', {})) & {
                                    b['branch_id'] for b in cell['payload']['branches']}
                                if branches:
                                    selected.append((dict(epoch=event['epoch'], signal_id=event.get('signal_id') or event['event_id'],
                                        native_event_id=event['event_id'], native_epoch=event.get('native_epoch'),
                                        native_sequence=event.get('native_sequence'),
                                        branch_membership={bid: signal.get('event_id', event['event_id'])
                                            if signal.get('decision_phase') == 'FIRST_UPTICK' else None
                                            for bid,signal in event.get('branch_signals', {}).items() if bid in branches},
                                        selector_claimed=bool(ready.get('claimed'))),
                                        family['family_sha256'], tuple(scope), getattr(state,'generation',None)))
    with _LOCK:
        for identity,record in records:
            if identity and identity not in _READY:
                kind='fixed_watch' if symbol in {'005930','034020','036930','196170','403870'} else 'other'
                record['kind']=kind
                _COVERAGE[kind]['ready'] += 1
                _READY[identity]=record
                if len(_READY)>4096:
                    _READY.popitem(last=False)
        stream = (symbol, venue, item, market, day)
        active = _ACTIVE_SELECTED.setdefault(stream, set())
        for event, family, scope, scope_hash in selected:
            identity = (day, os.getpid(), _GENERATION, family, scope_hash, *scope[:4],
                        event['native_epoch'], event['signal_id'])
            if identity not in _SELECTED_READY:
                _SELECTED_READY[identity] = dict(event, family_sha256=family,
                    process_pid=os.getpid(), process_start_ticks=_PROCESS_START_TICKS,
                    bundle_sha256=_GENERATION, scope=list(scope), scope_execution_hash=scope_hash,
                    claimed=False, first_native_seen=epoch, first_seen_perf=time.perf_counter(),
                    original_deadline=event['epoch']+5, terminal=None,
                    first_eligible_seen=None, last_eligible_seen=None, first_ineligible_seen=None,
                    main_first_visit=None, claim_attempt=None, claimed_epoch=None)
                _SELECTED_READY[identity].update(last_observed_sequence=None, continuous_ingress=True)
                active.add(identity)
                _queue_lifecycle(identity, _SELECTED_READY[identity])
            else:
                _SELECTED_READY[identity]['selector_claimed'] = event['selector_claimed']
            if len(_SELECTED_READY) > _LIMIT:
                old_key, old = _SELECTED_READY.popitem(last=False)
                old_state = 'claimed' if old['claimed'] else 'unobservable'
                _SELECTED_EVICTED[old_state] = _SELECTED_EVICTED.get(old_state, 0)+1
                terminal = old.get('terminal') or 'unobservable'
                _LIFECYCLE_EVICTED[terminal] = _LIFECYCLE_EVICTED.get(terminal, 0)+1
                old_stream = tuple(old['scope'][:5])
                _ACTIVE_SELECTED.get(old_stream, set()).discard(old_key)
        for key in tuple(active):
            row = _SELECTED_READY.get(key)
            if row is None:
                active.discard(key); continue
            if row.get('terminal'):
                active.discard(key); continue
            state = states.get(tuple(row['scope']))
            last = state['last'] if state else None
            from src.engine.scalping.continuous_reversal import good_quote
            if last:
                previous = row['last_observed_sequence']
                row['continuous_ingress'] = row['continuous_ingress'] and (
                    last[2] == row['native_sequence'] if previous is None else last[2] in (previous, previous+1))
                row['last_observed_sequence'] = last[2]
            survivors = ({bid: anchor is None or anchor == state['turn']
                          for bid,anchor in row['branch_membership'].items()} if state else {})
            # Never infer validity at the deadline from a static last tick.
            if epoch >= row['original_deadline']:
                proven = (epoch == row['original_deadline'] and last and last[0] == epoch
                    and good_quote(last) and last[1] == row['native_epoch'] and row['continuous_ingress']
                    and row['first_eligible_seen'] is not None and row['main_first_visit'] is not None
                    and row['signal_id'] in state['ready_ids'] and any(survivors.values()))
                row.update(terminal='observed_valid_until_deadline_unclaimed' if proven else 'unobservable',
                    terminal_reason='exact_boundary_observed' if proven else 'deadline_continuity_unobserved')
            elif not state or not last:
                row.update(terminal='unobservable', terminal_reason='native_state_unobserved')
            elif row['family_sha256'] != (getattr(B, '_FAMILY', None) or {}).get('family_sha256'):
                row.update(terminal='unobservable', terminal_reason='generation_changed')
            elif not good_quote(last) or last[1] != row['native_epoch']:
                row.update(terminal='source_or_guard_blocked_before_claim', terminal_reason='source_or_epoch_invalid')
            else:
                row['branch_survival'] = survivors
                if not any(survivors.values()):
                    replaced = state['turn'] and state['turn'] in state['ready_event_ids']
                    row.update(terminal='replaced_before_claim' if replaced else 'invalidated_before_claim',
                               terminal_reason='first_turn_invalidated')
                elif row['signal_id'] not in state['ready_ids']:
                    row.update(terminal='unobservable', terminal_reason='ready_removed_without_terminal_receipt')
                elif row['selector_claimed']:
                    row.update(terminal='unobservable', terminal_reason='selector_consumed_without_claim_receipt')
                else:
                    notify = notify or row['first_eligible_seen'] is None
                    row['first_eligible_seen'] = row['first_eligible_seen'] or epoch
                    row['last_eligible_seen'] = epoch
            if row.get('terminal'):
                row['first_ineligible_seen'] = epoch
                row['transition_interval'] = [row['last_eligible_seen'], epoch]
                _queue_lifecycle(key, row)
                active.discard(key)
            elif key in _LIFECYCLE_PENDING:
                _queue_lifecycle(key, row)
        if not active:
            _ACTIVE_SELECTED.pop(stream, None)
        # A date/market rollover cannot leave active indexes growing forever.
        for old_stream in tuple(_ACTIVE_SELECTED):
            if str(old_stream[4]) != day:
                for key in _ACTIVE_SELECTED.pop(old_stream):
                    row = _SELECTED_READY.get(key)
                    if row and not row.get('terminal'):
                        row.update(terminal='unobservable', terminal_reason='date_rollover')
                        _queue_lifecycle(key, row)
    return notify


def record_native_visit(symbol, venue, item, market, now):
    """Main adapter calls this before claim; never consumes the native state."""
    with _LOCK:
        for stream, keys in _ACTIVE_SELECTED.items():
            if stream[:4] != (symbol, venue, item, market):
                continue
            for key in keys:
                row = _SELECTED_READY.get(key)
                if row and not row.get('terminal'):
                    row['main_first_visit'] = row['main_first_visit'] or now
                    row['claim_attempt'] = now
                    _queue_lifecycle(key, row)


def record_selected_native_claim(claim, *, family_sha256=None, now=None):
    event = claim['snapshot'][0]
    with _LOCK:
        # Exact route/native generation matching; a reused signal ID elsewhere
        # cannot inherit this claim. Active set is bounded by native lifetimes.
        for stream, keys in _ACTIVE_SELECTED.items():
            if stream[:4] != (event['symbol'], event['venue'], event['source_item'], event['market']):
                continue
            for key in keys:
                row = _SELECTED_READY.get(key)
                if (row and row['signal_id'] == (event.get('signal_id') or event['event_id'])
                        and row['native_epoch'] == event.get('native_epoch')
                        and row['scope_execution_hash'] == claim.get('generation')
                        and (family_sha256 is None or row['family_sha256'] == family_sha256)):
                    row.update(claimed=True, terminal='claimed', claimed_epoch=now or time.time())
                    _queue_lifecycle(key, row)


def response_reserve():
    """Measured mandatory local response processing, bounded to 250 ms.

    No observations means zero estimated reserve, never a guessed provider p95
    gate. Native freshness is still checked after every received response.
    """
    with _LOCK:
        values = list(_SAMPLES['response_validate'])[-64:]
    values.sort()
    return min(.25, values[math.ceil(len(values)*.95)-1]) if values else 0.
