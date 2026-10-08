"""Bounded latency diagnostics, emitted with the existing loop log writer.

Never consulted by policy, quota, admission, or order guards. All completed
loops are sampled; the log interval is not a sampling interval.
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
          'provider_response', 'machine_to_provider_response', 'provider_response_to_pre_submit')
_SAMPLES = {name: deque(maxlen=_LIMIT) for name in _NAMES}
_TOTAL = {name: 0 for name in _NAMES}
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


def mark_signal(signal_id, stage):
    """At most 128 in-process stage clocks; missing joins stay unobservable."""
    if not signal_id or stage not in {'claim', 'machine', 'provider', 'submit'}:
        return
    now = time.perf_counter()
    sample = None
    with _LOCK:
        if stage == 'claim':
            if signal_id not in _SIGNALS:
                if len(_SIGNALS) >= 128:
                    _SIGNALS.popitem(last=False)
                _SIGNALS[signal_id] = {'claim': now}
        elif signal_id in _SIGNALS:
            clocks = _SIGNALS[signal_id]
            prior, metric = {'machine': ('claim', 'claim_to_machine'),
                             'provider': ('machine', 'machine_to_provider_response'),
                             'submit': ('provider', 'provider_response_to_pre_submit')}[stage]
            if prior in clocks and stage not in clocks:
                sample = (metric, now - clocks[prior])
                clocks[stage] = now
            if stage == 'submit':
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
            _GENERATION = generation
            _STARTED = time.time()
        _SAMPLES[name].append(seconds)
        _TOTAL[name] += 1
        if name == 'loop_work':
            stage = 'loop_first' if _TOTAL[name] == 1 else 'loop_work_warm'
            _SAMPLES[stage].append(seconds)
            _TOTAL[stage] += 1


def snapshot():
    with _LOCK:
        samples = {k: list(v) for k, v in _SAMPLES.items()}
        totals = dict(_TOTAL)
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
        signal_denominator='actually_claimed_only_expired_and_unobserved_not_inferred',
        metrics=metrics, preparation_failures=failures)


def log_snapshot():
    from src.utils.logger import log_info
    try:
        value = snapshot()
    except (OSError, ValueError, IndexError) as exc:
        value = dict(schema='main_runtime_performance_v1', state='unobservable',
                     reason=type(exc).__name__, decision_authority='none')
    log_info('[RUNTIME_PERFORMANCE] ' + json.dumps(value, separators=(',', ':')))
