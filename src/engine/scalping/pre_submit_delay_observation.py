"""Bounded same-symbol PASS/price-ready observation using Main's existing WS.

The registry contains scalars, never stocks/WS objects. No subscriptions,
workers, REST calls or order authority are created here.
"""
from collections import Counter, OrderedDict
import heapq
import threading
import time

MAX_ACTIVE = 128
MAX_PER_SYMBOL = 16
MAX_DUE_PER_TURN = 8
LIFETIME_SEC = 183
_LOCK = threading.RLock()
_ACTIVE = {}
_HEAPS = {}
_COUNTERS = Counter()
_SINK = None
_EXPIRIES = []
_RECENT = OrderedDict()


def configure_sink(sink):
    global _SINK
    _SINK = sink


def append(code, name, stage, fields):
    from src.utils.pipeline_event_logger import emit_pipeline_event
    if _SINK is None:
        with _LOCK:
            _COUNTERS["writer_not_prepared"] += 1
        return False
    try:
        observed = (fields.get('quote_observed_at_epoch') or fields.get('decision_committed_at_epoch')
                    or fields.get('terminal_finished_at_epoch') or time.time())
        result = _SINK(emit_pipeline_event, "ENTRY_PIPELINE", str(name or code), code, stage,
                       fields=fields, observed_at_epoch=observed, observation_category="pre_submit_delay")
    except Exception:
        with _LOCK:
            _COUNTERS['writer_failed'] += 1
        return False
    accepted = isinstance(result, dict) and result.get("status") == "queued"
    with _LOCK:
        _COUNTERS["queued" if accepted else "queue_rejected"] += 1
    return accepted


def shutdown():
    with _LOCK:
        codes = {key[0] for key in _ACTIVE}
    for code in codes:
        terminate(code, reason='process_shutdown_observation_censored')
    configure_sink(None)


def register(code, state, *, name=None, commit=None):
    key = (str(code), str(state["id"]))
    with _LOCK:
        if key in _ACTIVE or key in _RECENT:
            return False
        if len(_ACTIVE) >= MAX_ACTIVE or sum(k[0] == str(code) for k in _ACTIVE) >= MAX_PER_SYMBOL:
            _COUNTERS["observation_capacity_exceeded"] += 1
            return False
        heap = _HEAPS.setdefault(str(code), [])
        value = dict(state)
        value["remaining_sec"] = list(state["remaining_sec"])
        value["name"] = str(name or code)
        _ACTIVE[key] = value
        _RECENT[key] = True
        while len(_RECENT) > 2 * MAX_ACTIVE:
            _RECENT.popitem(last=False)
        if len(_EXPIRIES) >= 2 * MAX_ACTIVE:
            _EXPIRIES[:] = [(v['committed_at_epoch'] + LIFETIME_SEC, k) for k, v in _ACTIVE.items()]
            heapq.heapify(_EXPIRIES)
        heapq.heappush(_EXPIRIES, (value['committed_at_epoch'] + LIFETIME_SEC, key))
        heapq.heappush(heap, (value["committed_at_epoch"] + value["remaining_sec"][0], key[1]))
        _COUNTERS["registered"] += 1
    if commit is not None:
        if not append(code, name, "pre_submit_delay_committed", commit):
            with _LOCK:
                _ACTIVE.pop(key, None)
                heap = _HEAPS.get(str(code), [])
                heap[:] = [item for item in heap if item[1] != key[1]]
                heapq.heapify(heap)
                if not heap:
                    _HEAPS.pop(str(code), None)
                _COUNTERS['commit_queue_rejected'] += 1
            return False
    return True


def has_due(code, now):
    with _LOCK:
        heap = _HEAPS.get(str(code))
        return bool(heap and heap[0][0] <= now)


def take_due(code, now):
    """O(D log A), where D is limited; no global sweep or tick sorting."""
    result = []
    with _LOCK:
        heap = _HEAPS.get(str(code), [])
        while heap and heap[0][0] <= now and len(result) < MAX_DUE_PER_TURN:
            _, identity = heapq.heappop(heap)
            state = _ACTIVE.get((str(code), identity))
            if state is not None:
                result.append(state)
        if not heap:
            _HEAPS.pop(str(code), None)
    return result


def advance(code, state):
    with _LOCK:
        key = (str(code), state["id"])
        if not state["remaining_sec"]:
            _ACTIVE.pop(key, None)
            _COUNTERS["completed"] += 1
        elif key in _ACTIVE:
            heapq.heappush(_HEAPS.setdefault(str(code), []),
                           (state["committed_at_epoch"] + state["remaining_sec"][0], state["id"]))


def discard(code, identity, *, reason):
    """Remove only the failed intent, preserving other same-symbol PASSes."""
    with _LOCK:
        key = (str(code), str(identity))
        state = _ACTIVE.pop(key, None)
        heap = _HEAPS.get(key[0], [])
        heap[:] = [item for item in heap if item[1] != key[1]]
        heapq.heapify(heap)
        if not heap:
            _HEAPS.pop(key[0], None)
        if state is not None:
            _COUNTERS[reason] += 1
            append(code, state['name'], 'pre_submit_delay_intent_terminal', {
                'delay_intent_id':key[1], 'terminal_reason':reason,
                'decision_source_sha256':state['decision_source_sha256'],
                'observation_only':True, 'actual_order_submitted':False, 'broker_order_forbidden':True})


def terminate(code, *, reason):
    with _LOCK:
        _HEAPS.pop(str(code), None)
        for key in [key for key in _ACTIVE if key[0] == str(code)]:
            identity = key[1]
            state = _ACTIVE.pop(key, None)
            if state is not None:
                _COUNTERS[reason] += len(state["remaining_sec"])
                append(code, state["name"], "pre_submit_delay_intent_terminal", {
                    "delay_intent_id": identity, "terminal_reason": reason,
                    "observation_only": True, "decision_source_sha256": state["decision_source_sha256"],
                    "actual_order_submitted": False, "broker_order_forbidden": True})


def prune(now=None):
    """Bounded maintenance by the existing Main loop, including silent symbols."""
    now = time.time() if now is None else now
    with _LOCK:
        for _ in range(MAX_DUE_PER_TURN):
            if not _EXPIRIES or _EXPIRIES[0][0] > now:
                break
            _, key = heapq.heappop(_EXPIRIES)
            state = _ACTIVE.pop(key, None)
            if state is not None:
                heap = _HEAPS.get(key[0], [])
                heap[:] = [item for item in heap if item[1] != key[1]]
                heapq.heapify(heap)
                if not heap:
                    _HEAPS.pop(key[0], None)
                _COUNTERS['expired_without_quote'] += len(state['remaining_sec'])
                append(key[0], state['name'], 'pre_submit_delay_intent_terminal', {
                    'delay_intent_id': key[1], 'terminal_reason': 'observation_expired_without_quote',
                    'decision_source_sha256': state['decision_source_sha256'],
                    'observation_only': True, 'actual_order_submitted': False, 'broker_order_forbidden': True})


def health():
    with _LOCK:
        return {**_COUNTERS, "active": len(_ACTIVE), "heap_items": sum(map(len, _HEAPS.values())),
                "capacity": MAX_ACTIVE, "max_due_per_turn": MAX_DUE_PER_TURN}


def register_pass_result(result):
    """Freeze valid effective verdict at original completion, before Main intake."""
    payload = result.ai_payload
    assessment = payload.get("entry_ai_effective_assessment") or {}
    from collections.abc import Mapping
    verdict = assessment.get('effective_verdict') if isinstance(assessment, Mapping) else assessment
    if (verdict != "PASS"
        or payload.get("entry_mechanistic_action") != "ENTER_NOW"
        or result.completed_epoch > result.deadline_epoch or result.error_type):
        return False
    from .pre_submit_delay_tuning import decision_source_sha256, expected_route_for_session
    from .pre_submit_delay_initial_policy import digest
    origin = result.origin_fields
    market = origin.get("market_session_bucket")
    route = expected_route_for_session(market)
    machine = str(payload.get("machine_observation_sha256") or "")
    if not route or len(machine) != 64:
        return False
    identity = digest([result.code, result.request_id, machine, "signal_ready"])
    epoch = (result.prepared_context.get("ws_data") or {}).get("market_data_transport_epoch")
    commit = dict(delay_intent_id=identity, decision_committed_at_epoch=result.completed_epoch,
                  anchor_contract_version=2,
                  signal_ready_at_epoch=result.completed_epoch, anchor_kind="signal_ready",
                  route=route, quote_transport_epoch=epoch, delay_policy_sha256=None,
                  original_machine_observation_sha256=machine, planned_qty=None,
                  owner="main_scalping", market_session_bucket=market,
                  evaluation_attempt_id=payload.get("evaluation_attempt_id"),
                  ai_decision_trace_id=payload.get("ai_decision_trace_id"), request_id=result.request_id,
                  entry_action="ENTER_NOW", auxiliary_effective_action="PASS",
                  entry_mechanistic_policy_sha256=payload.get("entry_mechanistic_policy_sha256"),
                  entry_ai_soft_policy_sha256=payload.get("entry_ai_soft_policy_sha256"),
                  primary_branch_id=payload.get("primary_branch_id"),
                  actual_order_submitted=False, runtime_effect=False, broker_order_forbidden=True)
    commit["decision_source_sha256"] = decision_source_sha256(commit)
    return register(result.code, {"id": identity, "committed_at_epoch": result.completed_epoch,
                    "remaining_sec": [0, 30, 60, 120, 180], "route": route,
                    "quote_transport_epoch": epoch, "decision_source_sha256": commit["decision_source_sha256"]},
                    commit=commit)
