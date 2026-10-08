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
_NAMES = ('loop_work', 'loop_work_warm', 'loop_first', 'policy_prepare', 'ws_lock_wait', 'ws_lock_hold',
          'ws_snapshot', 'confirmed_to_claim', 'claim_to_machine',
          'provider_response', 'machine_to_provider_response', 'provider_response_to_pre_submit',
          'preparation_queue', 'preparation_service', 'source_prepare', 'capacity_prepare',
          'provider_key_wait', 'provider_transport', 'response_validate', 'main_commit', 'submit_guard',
          'capture_append', 'provider_reserve', 'order_acknowledgement')
_SAMPLES = {name: deque(maxlen=_LIMIT) for name in _NAMES}
_TOTAL = {name: 0 for name in _NAMES}
_BOUNDS = (.01, .05, .1, .25, .5, 1., 1.5, 2., 3., 5., 10., float('inf'))
_HIST = {name: [0]*len(_BOUNDS) for name in _NAMES}
_OVER5 = {name: 0 for name in _NAMES}
_READY = OrderedDict()
_COVERAGE = {kind: {'ready':0,'claimed':0} for kind in ('fixed_watch','other')}
_TIMELINES = deque(maxlen=128)
_GENERATION = None
_STARTED = time.time()
_SIGNALS = OrderedDict()
_FAILURES = OrderedDict()


def failure(stage, reason):
    """Bounded failure evidence; never convert source-invalid into success."""
    key = (str(stage)[:48], str(reason)[:160])
    with _LOCK:
        count, last = _FAILURES.get(key, (0, 0.0))
        now = time.monotonic()
        emit = now - last >= 60
        if key not in _FAILURES and len(_FAILURES) >= 16:
            _FAILURES.popitem(last=False)
        _FAILURES[key] = (count + 1, now if emit else last)
    if emit:
        from src.utils.logger import log_info
        log_info('[RUNTIME_PREPARATION_FAILURE] ' + json.dumps(dict(stage=key[0], reason=key[1], pid=os.getpid(), decision_authority='none')))


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
            _GENERATION = generation
            _STARTED = time.time()
        _SAMPLES[name].append(seconds)
        _TOTAL[name] += 1
        _OVER5[name] += seconds > 5
        _HIST[name][next(i for i,b in enumerate(_BOUNDS) if seconds <= b)] += 1
        if name == 'loop_work':
            stage = 'loop_first' if _TOTAL[name] == 1 else 'loop_work_warm'
            _SAMPLES[stage].append(seconds)
            _TOTAL[stage] += 1
            _OVER5[stage] += seconds > 5
            _HIST[stage][next(i for i,b in enumerate(_BOUNDS) if seconds <= b)] += 1


def snapshot():
    with _LOCK:
        samples = {k: list(v) for k, v in _SAMPLES.items()}
        totals = dict(_TOTAL)
        hist = {k:list(v) for k,v in _HIST.items()}
        over5 = dict(_OVER5)
        coverage = {k:dict(v) for k,v in _COVERAGE.items()}
        timelines = list(_TIMELINES)
        inflight = {k:dict(v) for k,v in _SIGNALS.items()}
        generation, started = _GENERATION, _STARTED
        failures = [dict(stage=k[0], reason=k[1], count=v[0]) for k, v in _FAILURES.items()]
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
            cumulative_histogram=dict(zip(('0.01','0.05','0.1','0.25','0.5','1','1.5','2','3','5','10','inf'),hist[name])),
            state='observed' if n else 'unobservable_or_not_invoked')
    return dict(schema='main_runtime_performance_v1', pid=os.getpid(),
        process_start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
        cwd=os.getcwd(), code_root=str(Path(__file__).resolve().parents[3]),
        bundle_sha256=generation, started_epoch=started, observed_epoch=time.time(),
        metric_role='runtime_performance_diagnostic', decision_authority='none',
        window_policy='exact_pid_release_policy_scope_and_load_window',
        sample_floor='none_counts_and_unobservable_explicit',
        primary_decision_metric='latency_distribution_and_contract_parity',
        source_quality_gate='exact_identity_monotonic_duration_and_sample_coverage',
        forbidden_uses='policy_promotion_order_authority_or_economic_claim',
        signal_denominator='native_ready_seen_at_ingress_and_claimed_missing_joins_not_inferred',
        metrics=metrics, preparation_failures=failures,
        ready_coverage=coverage, ready_coverage_basis='native_ready_seen_at_ingress_not_all_market_opportunities',
        ready_coverage_window='process_lifetime_metrics_reset_on_policy_generation',
        recent_terminal_timelines=timelines, retained_signal_timelines=inflight)


def log_snapshot():
    from src.utils.logger import log_info
    try:
        value = snapshot()
        from src.utils.kiwoom_transport_telemetry import snapshot as transport_snapshot
        value['kiwoom_transport'] = transport_snapshot()
    except (OSError, ValueError, IndexError) as exc:
        value = dict(schema='main_runtime_performance_v1', state='unobservable',
                     reason=type(exc).__name__, decision_authority='none')
    log_info('[RUNTIME_PERFORMANCE] ' + json.dumps(value, separators=(',', ':')))


def record_native_ready(B, symbol, venue, item, market, epoch):
    """Peek sealed native ready membership, before Main claim admission."""
    day = __import__('datetime').datetime.fromtimestamp(epoch, __import__('zoneinfo').ZoneInfo('Asia/Seoul')).date().isoformat()
    records = []
    for native in (B, getattr(B, 'R', None)):
        if native is None or not hasattr(native, '_STATES'):
            continue
        with native._LOCK:
            for scope,state in list(native._STATES.items()):
                if tuple(scope[:4]) != (symbol,venue,item,market) or str(scope[4]) != day:
                    continue
                for ready in getattr(state,'ready', ()):
                    event=ready.get('event') if isinstance(ready,dict) else None
                    if event and 0 <= epoch-float(event['epoch']) <= 5:
                        records.append((event.get('signal_id') or event.get('event_id'),
                            dict(symbol=symbol, venue=venue, item=item, market=market, day=day,
                                 native_epoch=event.get('native_epoch'), epoch=event['epoch'],
                                 scope_execution_hash=getattr(state,'generation',None))))
    with _LOCK:
        for identity,record in records:
            if identity and identity not in _READY:
                kind='fixed_watch' if symbol in {'005930','034020','036930','196170','403870'} else 'other'
                record['kind']=kind
                _COVERAGE[kind]['ready'] += 1
                _READY[identity]=record
                if len(_READY)>4096:
                    _READY.popitem(last=False)


def response_reserve():
    """Measured mandatory local response processing, bounded to 250 ms.

    No observations means zero estimated reserve, never a guessed provider p95
    gate. Native freshness is still checked after every received response.
    """
    with _LOCK:
        values = list(_SAMPLES['response_validate'])[-64:]
    values.sort()
    return min(.25, values[math.ceil(len(values)*.95)-1]) if values else 0.
