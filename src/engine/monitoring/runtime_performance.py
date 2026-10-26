"""Bounded latency diagnostics, emitted with the existing loop log writer.

Does not change policy, quotas or order guards. Measured response processing
reserves timeout budget only. All completed loops are sampled.
"""

import json
import math
import os
import time
from copy import deepcopy
from collections import deque, OrderedDict
from pathlib import Path
from threading import Lock, get_native_id
from contextlib import contextmanager
from contextvars import ContextVar

_LOCK = Lock()
_LIMIT = 4096
_NAMES = (
    "loop_work",
    "loop_work_warm",
    "loop_first",
    "policy_prepare",
    "policy_load",
    "policy_release_check",
    "policy_consumer_check",
    "ws_lock_wait",
    "ws_lock_hold",
    "ws_snapshot",
    "confirmed_to_claim",
    "claim_to_machine",
    "provider_response",
    "machine_to_provider_response",
    "provider_response_to_pre_submit",
    "preparation_queue",
    "preparation_service",
    "source_prepare",
    "capacity_prepare",
    "provider_key_wait",
    "provider_transport",
    "response_validate",
    "main_commit",
    "submit_guard",
    "capture_append",
    "provider_reserve",
    "order_acknowledgement",
    "pipeline_source_replay",
    "observation_queue_wait",
    "coordinator_ready_to_main_guard",
)
_NAMES += (
    "entry_refresh",
    "entry_evaluation",
    "entry_policy",
    "entry_machine_assess",
    "entry_machine_capture",
    "entry_economics",
    "entry_wire",
    "entry_native_check",
    "entry_native_load",
    "entry_native_claim",
    "entry_native_auxiliary",
    "entry_annotation",
    "entry_trace_prepare",
    "entry_trace_append",
    "entry_outcome_append",
    "entry_error_processing",
    "entry_submit_native_load",
    "entry_submit_auxiliary",
    "entry_submit_generation",
    "entry_submit_total",
    "entry_submit_pipeline_emit",
    "entry_submit_operating_context",
    "entry_submit_sizing_plan",
)
_ENTRY_TIMINGS = ContextVar("entry_local_stage_timings", default=None)
_NATIVE_VISIT_HINTS = OrderedDict()
_NATIVE_VISIT_TOKENS = {}
_NATIVE_HINT_SEQUENCE = 0
_MAIN_PHASE = {"name": "not_observed", "epoch": None, "perf": None, "code": None}
_MAIN_PHASE_HISTORY = deque(maxlen=256)
_HTTP_SETTLEMENTS = deque(maxlen=128)
_ENTRY_TIMING_GAPS = 0
_POLICY_CALL = ContextVar("policy_validation_call", default=None)
_POLICY_SEQUENCE = 0
_POLICY_VALIDATIONS = deque(maxlen=128)
_POLICY_SLOW_VALIDATIONS = deque(maxlen=32)


@contextmanager
def policy_validation(stage):
    """Bounded causal timings in the existing sink; never a validity cache."""
    global _POLICY_SEQUENCE
    started, cpu = time.perf_counter(), time.thread_time()
    with _LOCK:
        _POLICY_SEQUENCE += 1
        call_id = _POLICY_SEQUENCE
    facts = dict(
        call_id=call_id,
        parent_call_id=(_POLICY_CALL.get() or {}).get("call_id"),
        stage=stage,
        started_epoch=time.time(),
        native_thread_id=get_native_id(),
        status="pass",
    )
    token = _POLICY_CALL.set(facts)
    try:
        yield facts
    except BaseException as exc:
        facts.update(
            status="error", error_type=type(exc).__name__, reason=str(exc)[:256]
        )
        raise
    finally:
        _POLICY_CALL.reset(token)
        parent = _POLICY_CALL.get()
        if parent is not None:
            for key in ("source_digest_reads", "source_digest_bytes"):
                parent[key] = parent.get(key, 0) + facts.get(key, 0)
        elapsed = max(0.0, time.perf_counter() - started)
        cpu = max(0.0, time.thread_time() - cpu)
        facts.update(
            elapsed_seconds=elapsed,
            thread_cpu_seconds=cpu,
            non_cpu_wall_seconds=max(0.0, elapsed - cpu),
        )
        with _LOCK:
            _POLICY_VALIDATIONS.append(dict(facts))
            if elapsed >= 1 or facts["status"] == "error":
                _POLICY_SLOW_VALIDATIONS.append(dict(facts))


def record_policy_digest_read(byte_count):
    facts = _POLICY_CALL.get()
    if facts is not None:
        facts["source_digest_reads"] = facts.get("source_digest_reads", 0) + 1
        facts["source_digest_bytes"] = facts.get("source_digest_bytes", 0) + byte_count


def record_entry_gap():
    global _ENTRY_TIMING_GAPS
    with _LOCK:
        _ENTRY_TIMING_GAPS += 1


def record_http_settlement(
    request_id, symbol, clocks, *, cancelled, transport_facts=None, terminal=None
):
    """Late SDK facts reach the existing diagnostics, never a result inbox."""
    with _LOCK:
        _HTTP_SETTLEMENTS.append(
            dict(
                request_id=str(request_id)[:160],
                symbol=str(symbol)[:6],
                observed_epoch=time.time(),
                stage_monotonic=dict(clocks),
                future_cancelled=bool(cancelled),
                transport_facts=dict(transport_facts or {}),
                provider_terminal=dict(terminal or {}),
                decision_authority="none",
            )
        )


@contextmanager
def entry_timing_frame():
    """Call-local durations only; neither an admission gate nor a new ledger."""
    timings = {}
    token = _ENTRY_TIMINGS.set(timings)
    try:
        yield timings
    finally:
        _ENTRY_TIMINGS.reset(token)


@contextmanager
def entry_stage(name):
    started = time.perf_counter()
    try:
        yield
    finally:
        record_entry_duration(name, max(0.0, time.perf_counter() - started))


def entry_timings():
    return dict(_ENTRY_TIMINGS.get() or {})


def record_entry_duration(name, seconds):
    try:
        timings = _ENTRY_TIMINGS.get()
        if name in _NAMES and math.isfinite(seconds) and seconds >= 0:
            if timings is not None:
                timings[name] = timings.get(name, 0.0) + seconds * 1000
            observe(name, seconds)
    except Exception:
        record_entry_gap()


def timed_entry_call(name, function, *args, **kwargs):
    with entry_stage(name):
        return function(*args, **kwargs)


def record_main_phase(name, code=None):
    """A scalar Main boundary for the existing lifecycle sink, without I/O."""
    with _LOCK:
        _MAIN_PHASE.update(
            name=str(name)[:64],
            code=str(code)[:6] if code else None,
            epoch=time.time(),
            perf=time.perf_counter(),
        )
        _MAIN_PHASE_HISTORY.append(dict(_MAIN_PHASE))


def _phase_window_locked(start, end):
    if start is None:
        return {"coverage": "eligible_clock_unobserved", "intervals": []}
    phases = list(_MAIN_PHASE_HISTORY)
    intervals = []
    for i, phase in enumerate(phases):
        left = max(start, phase["perf"])
        right = min(end, phases[i + 1]["perf"] if i + 1 < len(phases) else end)
        if right > left:
            intervals.append(
                dict(
                    name=phase["name"],
                    code=phase["code"],
                    started_perf=left,
                    ended_perf=right,
                )
            )
    return dict(
        coverage=(
            "complete" if phases and phases[0]["perf"] <= start else "prefix_unobserved"
        ),
        interval_count=len(intervals),
        intervals=intervals[-32:],
        truncated=len(intervals) > 32,
        clock_basis="same_pid_monotonic",
    )


def acknowledge_native_watch_visit(target, token, *, now):
    """Acknowledge only the hint used to select this actual Main visit."""
    code = str(target.get("code") or "")[:6]
    perf = time.perf_counter()
    with _LOCK:
        if token is not None and token == (
            _NATIVE_VISIT_HINTS.get(code),
            _NATIVE_VISIT_TOKENS.get(code),
        ):
            _NATIVE_VISIT_HINTS.pop(code, None)
            _NATIVE_VISIT_TOKENS.pop(code, None)
        for stream, keys in _ACTIVE_SELECTED.items():
            if stream[0] != code:
                continue
            for key in keys:
                row = _SELECTED_READY.get(key)
                if (
                    row
                    and not row.get("terminal")
                    and row.get("main_queue_first_visit") is None
                ):
                    row.update(
                        main_queue_first_visit=now,
                        main_queue_first_visit_perf=perf,
                        main_phase_at_queue_visit=dict(_MAIN_PHASE),
                        main_queue_visit_scope_basis="symbol_only_not_native_claim",
                    )
                    _queue_lifecycle(key, row)


def rearm_native_watch_after_completion(claim):
    """Revisit an already observed successor after the old request releases Main.

    This is only a bounded scheduling hint. The native selector and handler
    still validate and claim the signal, with its original five-second budget.
    """
    global _NATIVE_HINT_SEQUENCE
    snapshot = (claim or {}).get("snapshot")
    if not snapshot or not isinstance(snapshot[0], dict):
        return False
    original = snapshot[0]
    required = (
        "symbol",
        "venue",
        "source_item",
        "market",
        "native_epoch",
        "epoch",
        "signal_id",
    )
    if any(original.get(key) is None for key in required) or not claim.get(
        "generation"
    ):
        return False
    day = (
        __import__("datetime")
        .datetime.fromtimestamp(
            original["epoch"], __import__("zoneinfo").ZoneInfo("Asia/Seoul")
        )
        .date()
        .isoformat()
    )
    stream = (
        original["symbol"],
        original["venue"],
        original["source_item"],
        original["market"],
        day,
    )
    now, perf = time.time(), time.perf_counter()
    with _LOCK:
        eligible = []
        for key in _ACTIVE_SELECTED.get(stream, ()):
            row = _SELECTED_READY.get(key)
            if (
                row
                and not row.get("terminal")
                and not row.get("claimed")
                and not row.get("selector_claimed")
                and row.get("first_eligible_seen") is not None
                and row["signal_id"] != original["signal_id"]
                and row["native_epoch"] == original["native_epoch"]
                and row["scope_execution_hash"] == claim["generation"]
                and 0 <= now - row["epoch"] < 5
                and now < row["original_deadline"]
                and perf
                < row["first_seen_perf"]
                + row["original_deadline"]
                - row["first_native_seen"]
            ):
                eligible.append(row["epoch"])
        if not eligible or _NATIVE_READY_EVENT is None:
            return False
        code = str(original["symbol"])[:6]
        # Never replace a newer ingress token or restart the signal clock.
        if not 0 <= now - _NATIVE_VISIT_HINTS.get(code, float("-inf")) < 5:
            _NATIVE_HINT_SEQUENCE += 1
            _NATIVE_VISIT_TOKENS[code] = _NATIVE_HINT_SEQUENCE
            _NATIVE_VISIT_HINTS[code] = min(eligible)
            _NATIVE_VISIT_HINTS.move_to_end(code)
            while len(_NATIVE_VISIT_HINTS) > 128:
                old_code, _ = _NATIVE_VISIT_HINTS.popitem(last=False)
                _NATIVE_VISIT_TOKENS.pop(old_code, None)
        event = _NATIVE_READY_EVENT
    event.set()
    return True


def prioritize_native_watches(
    queue,
    *,
    now,
    completed_requests=None,
    all_targets=None,
    processed_target_ids=None,
    revisited_target_ids=None,
    visit_tokens=None,
):
    """Retain bounded wake hints until the selected target is actually visited.

    A hint only changes the next visit. The handler still owns native claim,
    current source validation and every execution guard. No target is dropped.
    """
    with _LOCK:
        for code, stamp in tuple(_NATIVE_VISIT_HINTS.items()):
            if not 0 <= now - stamp < 5:
                _NATIVE_VISIT_HINTS.pop(code, None)
                _NATIVE_VISIT_TOKENS.pop(code, None)
        hints = dict(_NATIVE_VISIT_HINTS)
        tokens = {
            code: (stamp, _NATIVE_VISIT_TOKENS.get(code))
            for code, stamp in hints.items()
        }
    # A signal can arrive after this target's ordinary visit. Re-admit at
    # most once per target/pass; the unchanged native selector owns its claim.
    # Append before sorting so every existing protected slot keeps its index.
    queued = {id(target) for target in queue}
    additions = []
    if all_targets is not None and revisited_target_ids is not None:
        for target in all_targets:
            identity = id(target)
            if (
                identity in (processed_target_ids or ())
                and identity not in queued
                and identity not in revisited_target_ids
                and target.get("status") == "WATCHING"
                and str(target.get("_scanner_scheduler_lane") or "") != "COMMIT"
                and str(target.get("code") or "")[:6] in hints
            ):
                additions.append(target)
                queued.add(identity)
                revisited_target_ids.add(identity)
    if additions:
        queue = [*queue, *additions]
    if visit_tokens is not None:
        visit_tokens.update(
            {
                id(target): tokens[str(target.get("code") or "")[:6]]
                for target in queue
                if str(target.get("code") or "")[:6] in tokens
            }
        )
    if not hints and not completed_requests:
        return queue
    with _LOCK:
        indexes = [
            i
            for i, target in enumerate(queue)
            if target.get("status") == "WATCHING"
            and str(target.get("_scanner_scheduler_lane") or "") != "COMMIT"
        ]
        hinted = {
            str(queue[i].get("code") or "")[:6]: hints.get(
                str(queue[i].get("code") or "")[:6]
            )
            for i in indexes
        }
        hinted = {code: stamp for code, stamp in hinted.items() if stamp is not None}
    completed_requests = completed_requests or {}
    completed = {}
    for i in indexes:
        target = queue[i]
        identity = (
            target.get("_scanner_async_generation_id"),
            target.get("_scanner_async_cache_key"),
        )
        stamp = completed_requests.get(identity)
        if (
            type(stamp) in (int, float)
            and math.isfinite(stamp)
            and stamp >= 0
            and identity[0]
            and identity[1]
        ):
            completed[id(target)] = stamp
    if not hinted and not completed:
        return queue

    def visit_order(target):
        if id(target) in completed:
            return (0, completed[id(target)])
        return (1, hinted.get(str(target.get("code") or "")[:6], float("inf")))

    ordered = sorted((queue[i] for i in indexes), key=visit_order)
    result = list(queue)
    for i, target in zip(indexes, ordered):
        result[i] = target
    return result


def observe_async_main_guard(result, *, now_perf):
    """Same-process coordinator clock only, including normally rejected work."""
    ready = getattr(result, "coordinator_ready_perf", 0.0)
    if (
        type(ready) not in (int, float)
        or not math.isfinite(ready)
        or ready <= 0
        or not math.isfinite(now_perf)
        or now_perf < ready
    ):
        return {}
    seconds = now_perf - ready
    observe("coordinator_ready_to_main_guard", seconds)
    fields = dict(
        async_main_guard_perf=now_perf,
        async_coordinator_ready_to_main_guard_ms=round(seconds * 1000, 3),
        async_guard_clock_basis="same_pid_monotonic",
    )
    finished = (
        getattr(result, "ai_payload", {}).get("entry_local_stage_clocks") or {}
    ).get("async_evaluation_completed_perf")
    if (
        type(finished) in (int, float)
        and math.isfinite(finished)
        and 0 < finished <= ready
    ):
        fields.update(
            async_evaluation_completed_perf=finished,
            async_evaluation_to_coordinator_ready_ms=round(
                (ready - finished) * 1000, 3
            ),
            async_evaluation_to_main_guard_ms=round((now_perf - finished) * 1000, 3),
        )
    return fields


_SAMPLES = {name: deque(maxlen=_LIMIT) for name in _NAMES}
_TOTAL = {name: 0 for name in _NAMES}
_BOUNDS = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, float("inf"))
_HIST = {name: [0] * len(_BOUNDS) for name in _NAMES}
_OVER5 = {name: 0 for name in _NAMES}
_UNDER5 = {name: 0 for name in _NAMES}
_AT_MOST2 = {name: 0 for name in _NAMES}
_READY = OrderedDict()
_SELECTED_READY = OrderedDict()
_SELECTED_EVICTED = {"claimed": 0, "expired_before_claim": 0, "unobservable": 0}
_LIFECYCLE_EVICTED = {}
_LIFECYCLE_PENDING = OrderedDict()
_LIFECYCLE_APPEND_DROPPED = 0
_LIFECYCLE_SINK = None
_NATIVE_READY_EVENT = None


def set_native_ready_event(event):
    """Existing Main wait event only; no callback, I/O, claim or new worker."""
    global _NATIVE_READY_EVENT
    with _LOCK:
        if _NATIVE_READY_EVENT is not event:
            _NATIVE_VISIT_HINTS.clear()
            _NATIVE_VISIT_TOKENS.clear()
        _NATIVE_READY_EVENT = event
        if event is None:
            _NATIVE_VISIT_HINTS.clear()
            _NATIVE_VISIT_TOKENS.clear()


_ACTIVE_SELECTED = {}  # stream -> bounded active keys, never all-day scans per tick
_LIFECYCLE_STATES = (
    "claimed",
    "invalidated_before_claim",
    "replaced_before_claim",
    "observed_valid_until_deadline_unclaimed",
    "source_or_guard_blocked_before_claim",
    "not_yet_due",
    "unobservable",
)
_COVERAGE = {kind: {"ready": 0, "claimed": 0} for kind in ("fixed_watch", "other")}
_TIMELINES = deque(maxlen=128)
_GENERATION = None
_STARTED = time.time()
try:
    _PROCESS_START_TICKS = (
        Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19]
    )
except (OSError, IndexError):
    _PROCESS_START_TICKS = None
_SIGNALS = OrderedDict()
_FAILURES = OrderedDict()
_CIRCUIT = {"state": "not_observed"}
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

    scope = row["scope"]
    return emit_pipeline_event(
        "ENTRY_PIPELINE",
        scope[0],
        scope[0],
        "native_signal_lifecycle",
        fields=dict(
            native_signal_lifecycle=json.dumps(
                row, sort_keys=True, separators=(",", ":")
            ),
            source_date=scope[4],
            native_signal_id=row["signal_id"],
            runtime_effect=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
    )


def flush_lifecycle():
    global _LIFECYCLE_APPEND_DROPPED
    if _LIFECYCLE_SINK is None:
        return
    with _LOCK:
        now = time.time()
        for stream, keys in list(_ACTIVE_SELECTED.items()):
            for key in tuple(keys):
                row = _SELECTED_READY.get(key)
                if row and not row.get("terminal") and now >= row["original_deadline"]:
                    row.update(
                        terminal="unobservable",
                        terminal_reason="deadline_continuity_unobserved",
                    )
                    _queue_lifecycle(key, row)
                if row is None or row.get("terminal"):
                    keys.discard(key)
            if not keys:
                _ACTIVE_SELECTED.pop(stream, None)
        pending = list(_LIFECYCLE_PENDING.values())
        _LIFECYCLE_PENDING.clear()
    for row in pending:
        try:
            result = _LIFECYCLE_SINK(_append_lifecycle, row)
            if not isinstance(result, dict) or result.get("status") != "queued":
                raise ValueError("lifecycle_append_admission_unconfirmed")
        except Exception:
            with _LOCK:
                _LIFECYCLE_APPEND_DROPPED += 1
            failure("native_lifecycle", "append_admission_failed", emit_log=False)


def observe_ai_circuit(
    *, failures, disabled, entry=None, common=None, common_failure=None
):
    with _LOCK:
        _CIRCUIT.update(
            state="disabled" if disabled else "enabled",
            consecutive_failures=int(failures),
            observed_epoch=time.time(),
        )
        if entry is not None:
            _CIRCUIT["entry_transport"] = dict(entry)
        if common is not None:
            _CIRCUIT["provider_common"] = dict(common)
        if common_failure is not None:
            _CIRCUIT["common_failure"] = dict(common_failure)


def circuit_snapshot():
    with _LOCK:
        return dict(
            pid=os.getpid(),
            process_start_ticks=_PROCESS_START_TICKS,
            snapshot_epoch=time.time(),
            **dict(_CIRCUIT),
        )


def process_identity_fields():
    return dict(pid=os.getpid(), process_start_ticks=_PROCESS_START_TICKS)


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

        log_info(
            "[RUNTIME_PREPARATION_FAILURE] "
            + json.dumps(
                dict(
                    stage=key[0],
                    reason=key[1],
                    pid=os.getpid(),
                    decision_authority="none",
                )
            )
        )


def machine_signal_id(fields):
    """Read an optional diagnostic identity without interpreting a decision.

    Source-invalid preflight uses a string in the same legacy result field.
    Missing/malformed telemetry cannot become an execution-path exception.
    """
    decision = (
        fields.get("entry_mechanistic_policy_decision")
        if isinstance(fields, dict)
        else None
    )
    if not isinstance(decision, dict):
        return None
    assessment = decision.get("continuous_reversal_assessment") or decision
    if not isinstance(assessment, dict):
        return None
    value = assessment.get("signal_id") or assessment.get("event_id")
    return value if isinstance(value, str) and value else None


def mark_signal(signal_id, stage, *, identity=None):
    """At most 128 in-process stage clocks; missing joins stay unobservable."""
    if not signal_id or stage not in {
        "claim",
        "machine",
        "provider",
        "submit",
        "pre_submit",
        "guard_done",
        "actual_submit",
    }:
        return
    now = time.perf_counter()
    sample = None
    with _LOCK:
        if stage == "claim":
            if signal_id not in _SIGNALS:
                if len(_SIGNALS) >= 128:
                    _SIGNALS.popitem(last=False)
                _SIGNALS[signal_id] = {"claim": now}
                if signal_id in _READY:
                    _COVERAGE[_READY[signal_id]["kind"]]["claimed"] += 1
                    _SIGNALS[signal_id]["identity"] = _READY[signal_id]
        elif signal_id in _SIGNALS:
            clocks = _SIGNALS[signal_id]
            if isinstance(identity, dict):
                clocks.setdefault("evidence", {}).update(
                    {
                        k: str(v)[:160]
                        for k, v in identity.items()
                        if k
                        in {
                            "evaluation_attempt_id",
                            "ai_request_id",
                            "source_registration_sha256",
                            "opportunity_key",
                            "request_identity",
                            "status",
                        }
                    }
                )
            prior, metric = {
                "machine": ("claim", "claim_to_machine"),
                "provider": ("machine", "machine_to_provider_response"),
                "submit": ("provider", "provider_response_to_pre_submit"),
                "pre_submit": ("provider", "provider_response_to_pre_submit"),
                "guard_done": ("pre_submit", "submit_guard"),
                "actual_submit": ("guard_done", "order_acknowledgement"),
            }[stage]
            if prior in clocks and stage not in clocks:
                sample = (metric, now - clocks[prior])
                clocks[stage] = now
            if stage == "actual_submit":
                _TIMELINES.append(
                    dict(signal_id=signal_id, stages=dict(clocks), actual_submit=True)
                )
                _SIGNALS.pop(signal_id, None)
    if sample is not None:
        observe(*sample)


def observe(name, seconds, *, generation=None):
    global _GENERATION, _STARTED
    if name not in _SAMPLES or not math.isfinite(seconds) or seconds < 0:
        return
    with _LOCK:
        if generation is not None and generation != _GENERATION:
            _NATIVE_VISIT_HINTS.clear()
            _NATIVE_VISIT_TOKENS.clear()
            _SIGNALS.clear()
            for values in _SAMPLES.values():
                values.clear()
            for key in _TOTAL:
                _TOTAL[key] = 0
                _HIST[key] = [0] * len(_BOUNDS)
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
        _HIST[name][next(i for i, b in enumerate(_BOUNDS) if seconds <= b)] += 1
        if name == "loop_work":
            stage = "loop_first" if _TOTAL[name] == 1 else "loop_work_warm"
            _SAMPLES[stage].append(seconds)
            _TOTAL[stage] += 1
            _OVER5[stage] += seconds > 5
            _UNDER5[stage] += seconds < 5
            _AT_MOST2[stage] += seconds <= 2
            _HIST[stage][next(i for i, b in enumerate(_BOUNDS) if seconds <= b)] += 1


def snapshot():
    with _LOCK:
        samples = {k: list(v) for k, v in _SAMPLES.items()}
        totals = dict(_TOTAL)
        hist = {k: list(v) for k, v in _HIST.items()}
        over5 = dict(_OVER5)
        under5, at_most2 = dict(_UNDER5), dict(_AT_MOST2)
        coverage = {k: dict(v) for k, v in _COVERAGE.items()}
        timelines = list(_TIMELINES)
        inflight = {k: dict(v) for k, v in _SIGNALS.items()}
        generation, started = _GENERATION, _STARTED
        circuit = dict(_CIRCUIT)
        settlements = list(_HTTP_SETTLEMENTS)
        timing_gaps = _ENTRY_TIMING_GAPS
        failures = [
            dict(stage=k[0], reason=k[1], count=v[0]) for k, v in _FAILURES.items()
        ]
        policy_validations = list(_POLICY_VALIDATIONS)
        policy_slow = list(_POLICY_SLOW_VALIDATIONS)
        selected = [dict(v) for v in _SELECTED_READY.values()]
        raw_ready_count = len(_READY)
        raw_ready_recent = deepcopy(list(_READY.values())[-32:])
        selected_counts = dict(_SELECTED_EVICTED, pending=0)
        lifecycle_counts = {k: _LIFECYCLE_EVICTED.get(k, 0) for k in _LIFECYCLE_STATES}
        lifecycle_append_dropped = _LIFECYCLE_APPEND_DROPPED
    selected_as_of = time.time()
    for row in selected:
        state = (
            "claimed"
            if row["claimed"]
            else (
                "expired_before_claim"
                if selected_as_of >= row["epoch"] + 5
                else "pending"
            )
        )
        selected_counts[state] += 1
        terminal = row.get("terminal") or (
            "not_yet_due" if selected_as_of < row["epoch"] + 5 else "unobservable"
        )
        lifecycle_counts[terminal] += 1
    metrics = {}
    for name, values in samples.items():
        values.sort()
        n = len(values)
        metrics[name] = dict(
            n=n,
            total_observed=totals[name],
            retained_limit=_LIMIT,
            p95_seconds=values[math.ceil(n * 0.95) - 1] if n else None,
            p99_seconds=values[math.ceil(n * 0.99) - 1] if n else None,
            max_seconds=max(values) if n else None,
            over_five_seconds=sum(v > 5 for v in values),
            cumulative_over_five_seconds=over5[name],
            cumulative_under_five_seconds=under5[name],
            cumulative_at_most_two_seconds=at_most2[name],
            quantile_definition="nearest_rank_ceil_n_times_p",
            cumulative_histogram=dict(
                zip(
                    (
                        "0.01",
                        "0.05",
                        "0.1",
                        "0.25",
                        "0.5",
                        "1",
                        "1.5",
                        "2",
                        "3",
                        "5",
                        "10",
                        "inf",
                    ),
                    hist[name],
                )
            ),
            state="observed" if n else "unobservable_or_not_invoked",
        )
    return dict(
        schema="main_runtime_performance_v1",
        pid=os.getpid(),
        process_start_ticks=Path("/proc/self/stat")
        .read_text()
        .rsplit(")", 1)[1]
        .split()[19],
        cwd=os.getcwd(),
        code_root=str(Path(__file__).resolve().parents[3]),
        bundle_sha256=generation,
        started_epoch=started,
        observed_epoch=time.time(),
        metric_reset_identity=f"{os.getpid()}:{started:.6f}:{generation}",
        metric_role="runtime_performance_diagnostic",
        decision_authority="none",
        window_policy="exact_pid_release_policy_scope_and_load_window",
        sample_floor="none_counts_and_unobservable_explicit",
        primary_decision_metric="latency_distribution_and_contract_parity",
        source_quality_gate="exact_identity_monotonic_duration_and_sample_coverage",
        forbidden_uses="policy_promotion_order_authority_or_economic_claim",
        signal_denominator="native_ready_seen_at_ingress_and_claimed_missing_joins_not_inferred",
        metrics=metrics,
        preparation_failures=failures,
        policy_validation=dict(
            recent=policy_validations,
            slow_or_failed=policy_slow,
            retained_limits=dict(recent=128, slow_or_failed=32),
            non_cpu_wall_semantics="includes_io_lock_and_scheduling_not_io_attribution",
        ),
        observation_queue=(
            _OBSERVATION_HEALTH()
            if _OBSERVATION_HEALTH
            else {"status": "not_installed"}
        ),
        ai_circuit=circuit,
        provider_attempt_settlements=settlements,
        entry_timing_gap_count=timing_gaps,
        ready_coverage=coverage,
        ready_coverage_basis="native_ready_seen_at_ingress_not_all_market_opportunities",
        ready_coverage_window="process_lifetime",
        native_ready_selection=dict(
            schema="native_ready_selection_v1",
            retained_ready_count=raw_ready_count,
            recent=raw_ready_recent,
            recent_limit=32,
            recent_truncated=raw_ready_count > 32,
            coverage="bounded_raw_membership_not_all_market_opportunities",
            runtime_effect=False,
        ),
        selected_native_coverage=dict(
            count=sum(selected_counts.values()),
            **selected_counts,
            age_only_not_delivery_failure=True,
            as_of=selected_as_of,
            retained=len(selected),
            scope="selected_backend_price_band_generation",
            coverage="process_ingress_only_not_all_market_opportunities",
        ),
        native_signal_lifecycle=dict(
            schema="native_signal_lifecycle_v1",
            counts=lifecycle_counts,
            count=sum(lifecycle_counts.values()),
            recent=selected[-32:],
            append_admission_dropped=lifecycle_append_dropped,
            coverage="observed_snapshots_only_no_inferred_continuity",
            runtime_effect=False,
        ),
        recent_terminal_timelines=timelines,
        retained_signal_timelines=inflight,
    )


def log_snapshot():
    from src.utils.logger import log_info

    try:
        flush_lifecycle()
        value = snapshot()
        from src.utils.kiwoom_transport_telemetry import snapshot as transport_snapshot

        value["kiwoom_transport"] = transport_snapshot()
    except (OSError, ValueError, IndexError) as exc:
        value = dict(
            schema="main_runtime_performance_v1",
            state="unobservable",
            reason=type(exc).__name__,
            decision_authority="none",
        )
    log_info("[RUNTIME_PERFORMANCE] " + json.dumps(value, separators=(",", ":")))


def notify_source_recovery_target(symbol, *, original_epoch, now):
    """Prioritize one existing quote-recovery target without a native sample.

    The recovery owner has already checked its exact source and original
    deadline. This changes scheduling only; native-ready/claim counts remain
    untouched and the Main consumer repeats all guards before calculation.
    """
    global _NATIVE_HINT_SEQUENCE
    if (
        type(original_epoch) not in (int, float)
        or type(now) not in (int, float)
        or not math.isfinite(original_epoch)
        or not math.isfinite(now)
        or not 0 <= now - original_epoch < 5
    ):
        return False
    code = str(symbol)[:6]
    if len(code) != 6 or not code.isdigit():
        return False
    with _LOCK:
        event = _NATIVE_READY_EVENT
        if event is None:
            return False
        _NATIVE_HINT_SEQUENCE += 1
        _NATIVE_VISIT_TOKENS[code] = _NATIVE_HINT_SEQUENCE
        _NATIVE_VISIT_HINTS[code] = original_epoch
        _NATIVE_VISIT_HINTS.move_to_end(code)
        while len(_NATIVE_VISIT_HINTS) > 128:
            old_code, _ = _NATIVE_VISIT_HINTS.popitem(last=False)
            _NATIVE_VISIT_TOKENS.pop(old_code, None)
    event.set()
    return True


def record_native_ready(B, symbol, venue, item, market, epoch):
    global _NATIVE_HINT_SEQUENCE
    from contextlib import ExitStack

    # Match claim/observation adapter lock ordering. Publish the scalar receipt
    # before another thread can claim the event; no I/O under either lock.
    with ExitStack() as locks:
        locks.enter_context(B._LOCK)
        if getattr(B, "R", None) is not None:
            locks.enter_context(B.R._LOCK)
        notify = _record_native_ready_locked(B, symbol, venue, item, market, epoch)
    with _LOCK:
        event = _NATIVE_READY_EVENT
        if notify and event is not None:
            _NATIVE_HINT_SEQUENCE += 1
            _NATIVE_VISIT_TOKENS[str(symbol)[:6]] = _NATIVE_HINT_SEQUENCE
            _NATIVE_VISIT_HINTS[str(symbol)[:6]] = epoch
            _NATIVE_VISIT_HINTS.move_to_end(str(symbol)[:6])
            while len(_NATIVE_VISIT_HINTS) > 128:
                old_code, _ = _NATIVE_VISIT_HINTS.popitem(last=False)
                _NATIVE_VISIT_TOKENS.pop(old_code, None)
    if notify and event is not None:
        event.set()


def _record_native_ready_locked(B, symbol, venue, item, market, epoch):
    """Peek sealed native ready membership, before Main claim admission."""
    day = (
        __import__("datetime")
        .datetime.fromtimestamp(epoch, __import__("zoneinfo").ZoneInfo("Asia/Seoul"))
        .date()
        .isoformat()
    )
    records = []
    selected = []
    states = {}
    notify = False
    for native in (B, getattr(B, "R", None)):
        if native is None or not hasattr(native, "_STATES"):
            continue
        with native._LOCK:
            for scope, state in list(native._STATES.items()):
                if (
                    tuple(scope[:4]) != (symbol, venue, item, market)
                    or str(scope[4]) != day
                ):
                    continue
                legacy = getattr(state, "legacy", None)
                last = getattr(legacy, "last", None)
                states[tuple(scope)] = dict(
                    turn=(getattr(legacy, "turn", None) or {}).get("event_id"),
                    last=tuple(last) if last else None,
                    generation=getattr(state, "generation", None),
                    ready_event_ids=tuple(
                        r["event"].get("event_id") for r in state.ready
                    ),
                    ready_ids=tuple(r["event"].get("signal_id") for r in state.ready),
                )
                for ready in getattr(state, "ready", ()):
                    event = ready.get("event") if isinstance(ready, dict) else None
                    if event and 0 <= epoch - float(event["epoch"]) <= 5:
                        selection = _native_selection(
                            B, native, scope, state, event, epoch
                        )
                        records.append(
                            (
                                event.get("signal_id") or event.get("event_id"),
                                dict(
                                    symbol=symbol,
                                    venue=venue,
                                    item=item,
                                    market=market,
                                    day=day,
                                    signal_id=event.get("signal_id")
                                    or event.get("event_id"),
                                    native_event_id=event.get("event_id"),
                                    native_sequence=event.get("native_sequence"),
                                    native_epoch=event.get("native_epoch"),
                                    epoch=event["epoch"],
                                    confirmation_price=event.get("confirmation_price"),
                                    scope_execution_hash=getattr(
                                        state, "generation", None
                                    ),
                                ),
                                selection,
                            )
                        )
                        family = getattr(B, "_FAMILY", None) or {}
                        if selection["reason"] == "selected":
                            from src.engine.scalping.reversal_extended_catalog import (
                                CUMULATIVE_DEFINITIONS,
                            )

                            branches = set(selection["matched_branches"])
                            selected.append(
                                (
                                    dict(
                                        epoch=event["epoch"],
                                        signal_id=event.get("signal_id")
                                        or event["event_id"],
                                        native_event_id=event["event_id"],
                                        native_epoch=event.get("native_epoch"),
                                        native_sequence=event.get("native_sequence"),
                                        branch_membership={
                                            bid: (
                                                signal.get(
                                                    "event_id", event["event_id"]
                                                )
                                                if signal.get("decision_phase")
                                                == "FIRST_UPTICK"
                                                else None
                                            )
                                            for bid, signal in event.get(
                                                "branch_signals", {}
                                            ).items()
                                            if bid in branches
                                        },
                                        branch_hold_floors={
                                            bid: (signal.get("signal_proof") or {}).get(
                                                "price"
                                            )
                                            for bid, signal in event.get(
                                                "branch_signals", {}
                                            ).items()
                                            if bid in branches
                                            and bid not in CUMULATIVE_DEFINITIONS
                                            and signal.get("decision_phase")
                                            == "FIRST_PRICE_HOLD"
                                        },
                                        selector_claimed=bool(ready.get("claimed")),
                                    ),
                                    family["family_sha256"],
                                    tuple(scope),
                                    getattr(state, "generation", None),
                                )
                            )
    with _LOCK:
        for identity, record, selection in records:
            if identity and identity not in _READY:
                kind = (
                    "fixed_watch"
                    if symbol in {"005930", "034020", "036930", "196170", "403870"}
                    else "other"
                )
                record["kind"] = kind
                record["selections"] = []
                _COVERAGE[kind]["ready"] += 1
                _READY[identity] = record
                if len(_READY) > 4096:
                    _READY.popitem(last=False)
            if identity in _READY:
                receipts = _READY[identity]["selections"]
                source_key = (
                    "observed_scope",
                    "native_backend",
                    "family_sha256",
                    "scope_execution_hash",
                    "reason",
                    "expected_scope_execution_hash",
                    "selected_branches",
                    "observed_branches",
                )
                if not any(
                    all(r[k] == selection[k] for k in source_key) for r in receipts
                ):
                    receipts.append(selection)
                    if len(receipts) > 32:
                        receipts.pop(0)
                        _READY[identity]["selection_receipts_truncated"] = True
        stream = (symbol, venue, item, market, day)
        active = _ACTIVE_SELECTED.setdefault(stream, set())
        for event, family, scope, scope_hash in selected:
            identity = (
                day,
                os.getpid(),
                _GENERATION,
                family,
                scope_hash,
                *scope[:4],
                event["native_epoch"],
                event["signal_id"],
            )
            if identity not in _SELECTED_READY:
                _SELECTED_READY[identity] = dict(
                    event,
                    family_sha256=family,
                    process_pid=os.getpid(),
                    process_start_ticks=_PROCESS_START_TICKS,
                    bundle_sha256=_GENERATION,
                    scope=list(scope),
                    scope_execution_hash=scope_hash,
                    claimed=False,
                    first_native_seen=epoch,
                    first_seen_perf=time.perf_counter(),
                    original_deadline=event["epoch"] + 5,
                    terminal=None,
                    first_eligible_seen=None,
                    last_eligible_seen=None,
                    first_ineligible_seen=None,
                    main_first_visit=None,
                    claim_attempt=None,
                    claimed_epoch=None,
                )
                _SELECTED_READY[identity].update(
                    last_observed_sequence=None, continuous_ingress=True
                )
                active.add(identity)
                _queue_lifecycle(identity, _SELECTED_READY[identity])
            else:
                _SELECTED_READY[identity]["selector_claimed"] = event[
                    "selector_claimed"
                ]
            if len(_SELECTED_READY) > _LIMIT:
                old_key, old = _SELECTED_READY.popitem(last=False)
                old_state = "claimed" if old["claimed"] else "unobservable"
                _SELECTED_EVICTED[old_state] = _SELECTED_EVICTED.get(old_state, 0) + 1
                terminal = old.get("terminal") or "unobservable"
                _LIFECYCLE_EVICTED[terminal] = _LIFECYCLE_EVICTED.get(terminal, 0) + 1
                old_stream = tuple(old["scope"][:5])
                _ACTIVE_SELECTED.get(old_stream, set()).discard(old_key)
        for key in tuple(active):
            row = _SELECTED_READY.get(key)
            if row is None:
                active.discard(key)
                continue
            if row.get("terminal"):
                active.discard(key)
                continue
            state = states.get(tuple(row["scope"]))
            last = state["last"] if state else None
            from src.engine.scalping.continuous_reversal import good_quote

            if last:
                previous = row["last_observed_sequence"]
                row["continuous_ingress"] = row["continuous_ingress"] and (
                    last[2] == row["native_sequence"]
                    if previous is None
                    else last[2] in (previous, previous + 1)
                )
                row["last_observed_sequence"] = last[2]
            survivors = (
                {
                    bid: anchor is None or anchor == state["turn"]
                    for bid, anchor in row["branch_membership"].items()
                }
                if state
                else {}
            )
            floors = row["branch_hold_floors"]
            hold_proven = bool(
                floors
                and last
                and row["continuous_ingress"]
                and last[0] == epoch
                and last[2] > row["native_sequence"]
                and all(
                    type(f) in (int, float) and math.isfinite(f) and f > 0
                    for f in floors.values()
                )
            )
            if hold_proven:
                survivors.update(
                    {bid: last[3] >= floor for bid, floor in floors.items()}
                )
            row["latest_native_observation"] = list(last) if last else None
            row["ready_membership_present"] = bool(
                state and row["signal_id"] in state["ready_ids"]
            )
            # Never infer validity at the deadline from a static last tick.
            if epoch >= row["original_deadline"]:
                proven = (
                    epoch == row["original_deadline"]
                    and last
                    and last[0] == epoch
                    and good_quote(last)
                    and last[1] == row["native_epoch"]
                    and row["continuous_ingress"]
                    and row["first_eligible_seen"] is not None
                    and row["main_first_visit"] is not None
                    and row["signal_id"] in state["ready_ids"]
                    and any(survivors.values())
                )
                row.update(
                    terminal=(
                        "observed_valid_until_deadline_unclaimed"
                        if proven
                        else "unobservable"
                    ),
                    terminal_reason=(
                        "exact_boundary_observed"
                        if proven
                        else "deadline_continuity_unobserved"
                    ),
                )
            elif not state or not last:
                row.update(
                    terminal="unobservable", terminal_reason="native_state_unobserved"
                )
            elif (
                row["family_sha256"]
                != (getattr(B, "_FAMILY", None) or {}).get("family_sha256")
                or state["generation"] != row["scope_execution_hash"]
            ):
                row.update(
                    terminal="unobservable", terminal_reason="generation_changed"
                )
            elif not good_quote(last) or last[1] != row["native_epoch"]:
                row.update(
                    terminal="source_or_guard_blocked_before_claim",
                    terminal_reason="source_or_epoch_invalid",
                )
            else:
                row["branch_survival"] = survivors
                if not any(survivors.values()):
                    replaced = (
                        state["turn"] and state["turn"] in state["ready_event_ids"]
                    )
                    row.update(
                        terminal=(
                            "replaced_before_claim"
                            if replaced
                            else "invalidated_before_claim"
                        ),
                        terminal_reason=(
                            "first_price_hold_breached"
                            if hold_proven
                            and set(floors) == set(survivors)
                            and not row["ready_membership_present"]
                            else "first_turn_invalidated"
                        ),
                    )
                elif row["signal_id"] not in state["ready_ids"]:
                    row.update(
                        terminal="unobservable",
                        terminal_reason="ready_removed_without_terminal_receipt",
                    )
                elif row["selector_claimed"]:
                    row.update(
                        terminal="unobservable",
                        terminal_reason="selector_consumed_without_claim_receipt",
                    )
                else:
                    notify = notify or row["first_eligible_seen"] is None
                    if row["first_eligible_seen"] is None:
                        row.update(
                            first_eligible_perf=time.perf_counter(),
                            main_phase_at_first_eligible=dict(_MAIN_PHASE),
                            native_wake_event_installed=_NATIVE_READY_EVENT is not None,
                        )
                    row["first_eligible_seen"] = row["first_eligible_seen"] or epoch
                    row["last_eligible_seen"] = epoch
            if row.get("terminal"):
                row["first_ineligible_seen"] = epoch
                row["transition_interval"] = [row["last_eligible_seen"], epoch]
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
                    if row and not row.get("terminal"):
                        row.update(
                            terminal="unobservable", terminal_reason="date_rollover"
                        )
                        _queue_lifecycle(key, row)
    return notify


def _native_selection(B, native, scope, state, event, observed):
    """Explain the existing selector predicates without claiming any event."""
    family = getattr(B, "_FAMILY", None) or {}
    result = dict(
        observed_scope=list(scope),
        native_backend="operating" if native is B else "native_parent",
        family_sha256=family.get("family_sha256"),
        scope_execution_hash=getattr(state, "generation", None),
        expected_scope=None,
        expected_backend=None,
        expected_scope_execution_hash=None,
        observed_branches=sorted(event.get("branch_signals") or {}),
        selected_branches=[],
        matched_branches=[],
        observed_epoch=observed,
        reason="selection_contract_unobservable",
    )
    try:
        if family.get("schema") not in {
            "continuous_reversal_policy_v5",
            "continuous_reversal_policy_v6",
        }:
            return result
        from src.engine.scalping.reversal_extended_catalog import cell_key

        band = cell_key(scope[0], scope[3], event["confirmation_price"])
        result["expected_scope"] = band
        cell = family["machine_cells"][band]["routes"][scope[1]]
        expected = cell["backend"]
        branches = sorted(b["branch_id"] for b in cell["payload"]["branches"])
        matched = sorted(set(result["observed_branches"]) & set(branches))
        result.update(
            expected_backend=expected,
            expected_scope_execution_hash=cell.get("scope_execution_hash"),
            selected_branches=branches,
            matched_branches=matched,
        )
        if native is B and scope[-1] != band:
            reason = "price_band_not_selected"
        elif not (
            native is B
            and expected in {"union_v5", "union_v6"}
            or native is not B
            and expected == "registered_v4"
        ):
            reason = "carried_backend_not_selected"
        elif state.generation != (
            cell["scope_execution_hash"] if native is B else native._GENERATION
        ):
            reason = "scope_generation_mismatch"
        else:
            reason = "selected" if matched else "selected_branch_missing"
        result["reason"] = reason
    except (KeyError, TypeError, ValueError, AttributeError):
        pass  # Missing selection proof stays diagnostic, never eligible.
    return result


def record_native_preclaim_guard(*, stock, code, ws_data, reason, now):
    """Bind an actual Main return to a live selected signal, without claiming it.

    Native invalidation remains a separate terminal. A later fresh Main visit
    may still claim the signal; this receipt carries no retry/order authority.
    """
    if (
        not isinstance(stock, dict)
        or stock.get("watch_origin") != "MAIN_FIXED_WATCH"
        or not isinstance(ws_data, dict)
        or type(now) not in (float, int)
        or not math.isfinite(now)
        or not isinstance(reason, str)
        or reason
        not in {
            "extreme_sell_dominant",
            "stale_ws_snapshot",
            "trade_tick_quiet",
            "insufficient_history",
        }
    ):
        return 0
    from src.engine.scalping.continuous_reversal import market_bucket

    try:
        market = market_bucket(stock.get("market_session_bucket"))
    except ValueError:
        return 0
    item_map = ws_data.get("last_realtime_type_item")
    routes = ws_data.get("realtime_type_snapshots_by_route")
    if not isinstance(item_map, dict) or not isinstance(routes, dict):
        return 0
    item = item_map.get("0B")
    if not isinstance(item, str) or item.split("_", 1)[0] != code:
        return 0
    tapes = [
        records.get("0B")
        for records in routes.values()
        if isinstance(records, dict)
        and isinstance(records.get("0B"), dict)
        and records["0B"].get("item") == item
    ]
    if len(tapes) != 1:
        return 0
    tape = tapes[0]
    venue = {"krx_nxt_integrated": "SOR", "nxt_only": "NXT", "krx_only": "KRX"}.get(
        tape.get("market_route")
    )
    from src.trading.market.session_contract import market_source_partition_venue

    if venue is None or market_source_partition_venue(item) != venue:
        return 0
    stamp, epoch, sequence = (
        tape.get(k) for k in ("observed_epoch", "transport_epoch", "route_sequence")
    )
    if (
        type(stamp) not in (int, float)
        or not math.isfinite(stamp)
        or stamp > now
        or type(epoch) is not int
        or epoch <= 0
        or type(sequence) is not int
        or sequence < 0
    ):
        return 0
    recorded = 0
    with _LOCK:
        phase_visit = (
            _MAIN_PHASE.get("name") == "target_visit"
            and _MAIN_PHASE.get("code") == code
            and type(_MAIN_PHASE.get("epoch")) in (int, float)
            and 0 <= now - _MAIN_PHASE["epoch"] < 5
        )
        for stream, keys in _ACTIVE_SELECTED.items():
            if stream[:4] != (code, venue, item, market):
                continue
            for key in keys:
                row = _SELECTED_READY.get(key)
                if (
                    not row
                    or row.get("terminal")
                    or row.get("claimed")
                    or row.get("selector_claimed")
                    or row.get("bundle_sha256") != _GENERATION
                    or (row.get("main_queue_first_visit") is None and not phase_visit)
                    or not (row.get("main_queue_first_visit") or row["epoch"])
                    <= now
                    < row["original_deadline"]
                    or not row["epoch"] <= stamp <= now
                    or row["native_epoch"] != epoch
                    or sequence < row["native_sequence"]
                    or "main_preclaim_guard" in row
                ):
                    continue
                row["main_preclaim_guard"] = dict(
                    stage="blocked_strength_momentum",
                    reason=reason,
                    gate_action="source_quality_block",
                    observed_epoch=now,
                    source_observed_epoch=stamp,
                    source_item=item,
                    source_transport_epoch=epoch,
                    source_sequence=sequence,
                    main_visit_basis=(
                        "queue_visit"
                        if row.get("main_queue_first_visit") is not None
                        else "current_target_phase"
                    ),
                    record_id=stock.get("id"),
                    watch_admission_id=stock.get("watch_admission_id"),
                    watch_generation_id=stock.get("watch_generation_id"),
                    runtime_effect=False,
                )
                _queue_lifecycle(key, row)
                recorded += 1
    return recorded


def native_ready_lifecycle(event, family_sha256):
    """Read one exact bounded lifecycle while the caller holds native locks."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    identity = (
        datetime.fromtimestamp(event["epoch"], ZoneInfo("Asia/Seoul"))
        .date()
        .isoformat(),
        os.getpid(),
        _GENERATION,
        family_sha256,
        event.get("registry_generation"),
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        event["native_epoch"],
        event["signal_id"],
    )
    with _LOCK:
        return deepcopy(_SELECTED_READY.get(identity))


def record_native_visit(symbol, venue, item, market, now):
    """Main adapter calls this before claim; never consumes the native state."""
    with _LOCK:
        for stream, keys in _ACTIVE_SELECTED.items():
            if stream[:4] != (symbol, venue, item, market):
                continue
            for key in keys:
                row = _SELECTED_READY.get(key)
                if row and not row.get("terminal"):
                    row["main_first_visit"] = row["main_first_visit"] or now
                    row["claim_attempt"] = now
                    row.setdefault("main_first_visit_perf", time.perf_counter())
                    row["claim_attempt_perf"] = time.perf_counter()
                    row["main_phase_at_claim_attempt"] = dict(_MAIN_PHASE)
                    row["main_delivery_phase_window"] = _phase_window_locked(
                        row.get("first_eligible_perf"), row["claim_attempt_perf"]
                    )
                    _queue_lifecycle(key, row)


def record_selected_native_claim(claim, *, family_sha256=None, now=None):
    event = claim["snapshot"][0]
    with _LOCK:
        # Exact route/native generation matching; a reused signal ID elsewhere
        # cannot inherit this claim. Active set is bounded by native lifetimes.
        for stream, keys in _ACTIVE_SELECTED.items():
            if stream[:4] != (
                event["symbol"],
                event["venue"],
                event["source_item"],
                event["market"],
            ):
                continue
            for key in keys:
                row = _SELECTED_READY.get(key)
                if (
                    row
                    and row["signal_id"]
                    == (event.get("signal_id") or event["event_id"])
                    and row["native_epoch"] == event.get("native_epoch")
                    and row["scope_execution_hash"] == claim.get("generation")
                    and (family_sha256 is None or row["family_sha256"] == family_sha256)
                ):
                    row.update(
                        claimed=True,
                        terminal="claimed",
                        claimed_epoch=now or time.time(),
                    )
                    _queue_lifecycle(key, row)


def response_reserve():
    """Measured mandatory local response processing, bounded to 250 ms.

    No observations means zero estimated reserve, never a guessed provider p95
    gate. Native freshness is still checked after every received response.
    """
    with _LOCK:
        values = list(_SAMPLES["response_validate"])[-64:]
    values.sort()
    return min(0.25, values[math.ceil(len(values) * 0.95) - 1]) if values else 0.0
