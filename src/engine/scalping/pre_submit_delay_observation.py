"""Bounded same-symbol PASS/price-ready observation using Main's existing WS.

The registry contains scalars, never stocks/WS objects. A bounded source-only
sampler reads the existing local depth cache independently from Main visits.
It creates no subscription, REST/provider call or order authority.
"""

from collections import Counter, OrderedDict
from collections.abc import Mapping
import heapq
import math
import threading
import time
from .pre_submit_delay_tuning import (
    OBSERVATION_GRID_VERSION,
    OBSERVATION_HORIZONS,
    SHORT_RESEARCH_HORIZONS as SHORT_HORIZONS,
    SHORT_OBSERVATION_TOLERANCE_SEC as SHORT_TOLERANCE_SEC,
)

MAX_ACTIVE = 128
MAX_PER_SYMBOL = 16
MAX_DUE_PER_TURN = 8
MAX_HORIZONS_PER_TURN = 8
LIFETIME_SEC = 183
_LOCK = threading.RLock()
_ACTIVE = {}
_HEAPS = {}
_COUNTERS = Counter()
_SINK = None
_CLOSING = False
_CLOSED_AT = None
_EXPIRIES = []
_RECENT = OrderedDict()
_SAMPLER = None
_SAMPLER_STOP = threading.Event()
_SAMPLER_WAKE = threading.Event()
SAMPLE_INTERVAL_SEC = 0.05
MAX_SYMBOLS_PER_SAMPLE = 8


def observation_contract():
    """Research sampling only; runtime policy candidates remain unchanged."""
    return dict(
        observation_grid_version=OBSERVATION_GRID_VERSION,
        observation_horizons_sec=list(OBSERVATION_HORIZONS),
        observation_tolerance_sec=SHORT_TOLERANCE_SEC,
    )


def signal_reference_fields(result, *, machine_sha256=None, evaluation_attempt_id=None):
    """Read the already validated native confirmation; never use a live quote.

    Operating claims bind a scope execution generation, whereas the machine
    parent is the whole execution manifest. The frozen assessment binds both.
    No native revalidation, snapshot rehash or provider work happens here.
    """
    payload = getattr(result, "ai_payload", None)
    claim = getattr(result, "native_claim", None)
    if not isinstance(payload, Mapping) or not isinstance(claim, Mapping):
        return {}
    machine = payload.get("machine_observation_sha256")
    if (
        not isinstance(machine, str)
        or len(machine) != 64
        or any(c not in "0123456789abcdef" for c in machine)
        or machine_sha256 is not None
        and machine_sha256 != machine
        or evaluation_attempt_id is not None
        and evaluation_attempt_id != payload.get("evaluation_attempt_id")
    ):
        return {}
    assessment = payload.get("entry_mechanistic_policy_decision")
    snapshot = claim.get("snapshot")
    if (
        not isinstance(assessment, Mapping)
        or not isinstance(snapshot, (tuple, list))
        or not snapshot
        or not isinstance(snapshot[0], Mapping)
    ):
        return {}
    event = snapshot[0]
    proof = assessment.get("event")
    if not isinstance(proof, Mapping):
        return {}
    generation = assessment.get("scope_execution_hash") or assessment.get(
        "family_sha256"
    )
    token = claim.get("token")
    if (
        not isinstance(token, str)
        or len(token) != 64
        or any(c not in "0123456789abcdef" for c in token)
        or not isinstance(generation, str)
        or len(generation) != 64
        or any(c not in "0123456789abcdef" for c in generation)
        or claim.get("generation") != generation
        or assessment.get("machine_component_sha256")
        != payload.get("entry_mechanistic_policy_sha256")
        or not assessment.get("machine_component_sha256")
        or event.get("symbol") != getattr(result, "code", None)
        or not isinstance(event.get("source_item"), str)
        or not event["source_item"]
    ):
        return {}
    for key in (
        "symbol",
        "source_item",
        "market",
        "venue",
        "native_epoch",
        "native_sequence",
        "event_id",
        "signal_id",
        "epoch",
        "confirmation_price",
    ):
        if event.get(key) != proof.get(key):
            return {}
    for field, key in (
        ("continuous_reversal_event_id", "event_id"),
        ("continuous_reversal_signal_id", "signal_id"),
    ):
        if payload.get(field) != event.get(key) or assessment.get(key) != event.get(
            key
        ):
            return {}
    identity = event.get("signal_id") or event.get("event_id")
    price, epoch, completed = (
        event.get("confirmation_price"),
        event.get("epoch"),
        getattr(result, "completed_epoch", None),
    )
    if (
        not isinstance(identity, str)
        or not 0 < len(identity) <= 512
        or any(
            type(v) not in (int, float) or not math.isfinite(v) or v <= 0
            for v in (price, epoch, completed)
        )
        or epoch > completed
    ):
        return {}
    return dict(
        signal_reference_contract_version="native_confirmation_price_v1",
        original_signal_reference_price=price,
        original_signal_reference_epoch=epoch,
        original_signal_id=identity,
    )


def configure_sink(sink):
    global _SINK
    if sink is None:
        stop_sampler()
    with _LOCK:
        if _CLOSING and sink is not None:
            return False
        _SINK = sink
    return True


def sample_due(read_depth, observe, *, now=None):
    """Bounded local-cache reads; occurrence time is after the snapshot read."""
    now = time.time() if now is None else now
    with _LOCK:
        if _CLOSING:
            return 0
        due = sorted(
            (heap[0][0], code)
            for code, heap in _HEAPS.items()
            if heap and heap[0][0] <= now
        )[:MAX_SYMBOLS_PER_SAMPLE]
    for _, code in due:
        try:
            snapshot = read_depth(code)
            observed = time.time()
            observe({"code": code}, code, snapshot or {}, now_ts=observed)
        except Exception:
            with _LOCK:
                _COUNTERS["sampler_source_unobservable"] += 1
    return len(due)


def configure_sampler(read_depth, observe):
    """One sampling thread; no storage writes or Main/order callbacks."""
    global _SAMPLER
    if not stop_sampler():
        return False

    def run():
        while not _SAMPLER_STOP.is_set():
            count = sample_due(read_depth, observe)
            _SAMPLER_WAKE.wait(
                0.005 if count == MAX_SYMBOLS_PER_SAMPLE else SAMPLE_INTERVAL_SEC
            )
            _SAMPLER_WAKE.clear()

    with _LOCK:
        if _CLOSING:
            return False
        _SAMPLER_STOP.clear()
        _SAMPLER_WAKE.clear()
        _SAMPLER = threading.Thread(
            target=run, name="pre-submit-delay-sample", daemon=True
        )
        _SAMPLER.start()
    return True


def stop_sampler():
    global _SAMPLER
    worker = _SAMPLER
    if worker is not None:
        _SAMPLER_STOP.set()
        _SAMPLER_WAKE.set()
        if worker is not threading.current_thread():
            worker.join(timeout=1)
        if worker.is_alive():
            with _LOCK:
                _COUNTERS["sampler_shutdown_pending"] += 1
            return False
        _SAMPLER = None
    return True


def append(code, name, stage, fields):
    from src.utils.pipeline_event_logger import emit_pipeline_event

    with _LOCK:
        if _CLOSING and stage != "pre_submit_delay_intent_terminal":
            _COUNTERS["shutdown_admission_rejected"] += 1
            return False
        if _SINK is None:
            _COUNTERS["writer_not_prepared"] += 1
            return False
        try:
            observed = (
                fields.get("quote_observed_at_epoch")
                or fields.get("decision_committed_at_epoch")
                or fields.get("terminal_finished_at_epoch")
                or time.time()
            )
            result = _SINK(
                emit_pipeline_event,
                "ENTRY_PIPELINE",
                str(name or code),
                code,
                stage,
                fields=fields,
                observed_at_epoch=observed,
                observation_category="pre_submit_delay",
            )
        except Exception:
            _COUNTERS["writer_failed"] += 1
            return False
        accepted = isinstance(result, dict) and result.get("status") == "queued"
        _COUNTERS["queued" if accepted else "queue_rejected"] += 1
        return accepted


def shutdown():
    global _CLOSING, _CLOSED_AT, _SINK
    with _LOCK:
        _CLOSING = True
        if _CLOSED_AT is None:
            _CLOSED_AT = time.time()
    if not stop_sampler():
        return False
    with _LOCK:
        accepted = True
        codes = {key[0] for key in _ACTIVE}
        for code in codes:
            accepted = (
                terminate(
                    code,
                    reason="process_shutdown_observation_censored",
                    observed_at_epoch=_CLOSED_AT,
                )
                and accepted
            )
        _SINK = None
        if not accepted:
            _COUNTERS["shutdown_publication_failed"] += 1
        return not _COUNTERS["shutdown_publication_failed"]


def register(code, state, *, name=None, commit=None):
    key = (str(code), str(state["id"]))
    with _LOCK:
        if _CLOSING:
            _COUNTERS["shutdown_admission_rejected"] += 1
            return False
        if key in _ACTIVE or key in _RECENT:
            return False
        if (
            len(_ACTIVE) >= MAX_ACTIVE
            or sum(k[0] == str(code) for k in _ACTIVE) >= MAX_PER_SYMBOL
        ):
            _COUNTERS["observation_capacity_exceeded"] += 1
            return False
        heap = _HEAPS.setdefault(str(code), [])
        value = dict(state)
        value["remaining_sec"] = list(state["remaining_sec"])
        value["name"] = str(name or code)
        value["_commit_admitted"] = commit is None
        _ACTIVE[key] = value
        _RECENT[key] = True
        while len(_RECENT) > 2 * MAX_ACTIVE:
            _RECENT.popitem(last=False)
        if len(_EXPIRIES) >= 2 * MAX_ACTIVE:
            _EXPIRIES[:] = [
                (v["committed_at_epoch"] + LIFETIME_SEC, k) for k, v in _ACTIVE.items()
            ]
            heapq.heapify(_EXPIRIES)
        heapq.heappush(_EXPIRIES, (value["committed_at_epoch"] + LIFETIME_SEC, key))
        heapq.heappush(
            heap, (value["committed_at_epoch"] + value["remaining_sec"][0], key[1])
        )
        _COUNTERS["registered"] += 1
        if commit is not None:
            if not append(code, name, "pre_submit_delay_committed", commit):
                _ACTIVE.pop(key, None)
                heap = _HEAPS.get(str(code), [])
                heap[:] = [item for item in heap if item[1] != key[1]]
                heapq.heapify(heap)
                if not heap:
                    _HEAPS.pop(str(code), None)
                _COUNTERS["commit_queue_rejected"] += 1
                return False
        if key in _ACTIVE:
            _ACTIVE[key]["_commit_admitted"] = True
    _SAMPLER_WAKE.set()
    return True


def has_due(code, now):
    with _LOCK:
        heap = _HEAPS.get(str(code))
        return bool(heap and heap[0][0] <= now)


def should_retain_ws_subscription(code, *, now_ts=None):
    """Keep existing sources through the last pending horizon, never create REG.

    The active registry also covers a due intent temporarily removed from its
    heap by the sampler. Order/watch terminals do not end this research lease.
    The original admission clock bounds retention even if maintenance stalls.
    """
    now = time.time() if now_ts is None else now_ts
    code = str(code)
    with _LOCK:
        return not _CLOSING and any(
            key[0] == code
            and value.get("_commit_admitted", True)
            and value["remaining_sec"]
            and value["committed_at_epoch"]
            <= now
            < value["committed_at_epoch"] + LIFETIME_SEC
            for key, value in _ACTIVE.items()
        )


def take_due(code, now):
    """O(D log A), where D is limited; no global sweep or tick sorting."""
    result = []
    with _LOCK:
        if _CLOSING:
            return result
        heap = _HEAPS.get(str(code), [])
        while heap and heap[0][0] <= now and len(result) < MAX_DUE_PER_TURN:
            _, identity = heap[0]
            state = _ACTIVE.get((str(code), identity))
            if state is not None and not state.get("_commit_admitted", True):
                break
            heapq.heappop(heap)
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
            heapq.heappush(
                _HEAPS.setdefault(str(code), []),
                (state["committed_at_epoch"] + state["remaining_sec"][0], state["id"]),
            )


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
            append(
                code,
                state["name"],
                "pre_submit_delay_intent_terminal",
                {
                    "delay_intent_id": key[1],
                    "terminal_reason": reason,
                    "decision_source_sha256": state["decision_source_sha256"],
                    "observation_only": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )


def terminate(code, *, reason, observed_at_epoch=None):
    with _LOCK:
        accepted = True
        _HEAPS.pop(str(code), None)
        for key in [key for key in _ACTIVE if key[0] == str(code)]:
            identity = key[1]
            state = _ACTIVE.pop(key, None)
            if state is not None:
                _COUNTERS[reason] += len(state["remaining_sec"])
                accepted = (
                    append(
                        code,
                        state["name"],
                        "pre_submit_delay_intent_terminal",
                        {
                            "delay_intent_id": identity,
                            "terminal_reason": reason,
                            "observation_only": True,
                            "decision_source_sha256": state["decision_source_sha256"],
                            "terminal_finished_at_epoch": (
                                time.time()
                                if observed_at_epoch is None
                                else observed_at_epoch
                            ),
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                    )
                    and accepted
                )
        return accepted


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
                _COUNTERS["expired_without_quote"] += len(state["remaining_sec"])
                append(
                    key[0],
                    state["name"],
                    "pre_submit_delay_intent_terminal",
                    {
                        "delay_intent_id": key[1],
                        "terminal_reason": "observation_expired_without_quote",
                        "decision_source_sha256": state["decision_source_sha256"],
                        "observation_only": True,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    },
                )


def health():
    with _LOCK:
        return {
            **_COUNTERS,
            "active": len(_ACTIVE),
            "heap_items": sum(map(len, _HEAPS.values())),
            "capacity": MAX_ACTIVE,
            "max_due_per_turn": MAX_DUE_PER_TURN,
            "max_horizons_per_turn": MAX_HORIZONS_PER_TURN,
        }


def register_pass_result(result):
    """Freeze valid effective verdict at original completion, before Main intake."""
    payload = result.ai_payload
    assessment = payload.get("entry_ai_effective_assessment") or {}
    from collections.abc import Mapping

    verdict = (
        assessment.get("effective_verdict")
        if isinstance(assessment, Mapping)
        else assessment
    )
    if (
        verdict != "PASS"
        or payload.get("entry_mechanistic_action") != "ENTER_NOW"
        or result.completed_epoch > result.deadline_epoch
        or result.error_type
    ):
        return False
    from .pre_submit_delay_tuning import (
        decision_source_sha256,
        expected_route_for_session,
    )
    from .pre_submit_delay_initial_policy import digest, situation_fields
    from .reversal_auxiliary_registry import identity_json

    origin = result.origin_fields
    market = origin.get("market_session_bucket")
    route = expected_route_for_session(market)
    machine = str(payload.get("machine_observation_sha256") or "")
    if not route or len(machine) != 64:
        return False
    identity = digest([result.code, result.request_id, machine, "signal_ready"])
    epoch = (result.prepared_context.get("ws_data") or {}).get(
        "market_data_transport_epoch"
    )
    commit = dict(
        delay_intent_id=identity,
        decision_committed_at_epoch=result.completed_epoch,
        anchor_contract_version=4,
        **observation_contract(),
        **signal_reference_fields(result, machine_sha256=machine),
        signal_ready_at_epoch=result.completed_epoch,
        anchor_kind="signal_ready",
        route=route,
        quote_transport_epoch=epoch,
        delay_policy_sha256=None,
        original_machine_observation_sha256=machine,
        planned_qty=None,
        owner="main_scalping",
        market_session_bucket=market,
        evaluation_attempt_id=payload.get("evaluation_attempt_id"),
        ai_decision_trace_id=payload.get("ai_decision_trace_id"),
        request_id=result.request_id,
        entry_action="ENTER_NOW",
        auxiliary_effective_action="PASS",
        entry_mechanistic_policy_sha256=payload.get("entry_mechanistic_policy_sha256"),
        entry_ai_soft_policy_sha256=payload.get("entry_ai_soft_policy_sha256"),
        entry_auxiliary_policy_identity=(
            identity_json(payload.get("entry_auxiliary_policy_identity"))
            if payload.get("entry_auxiliary_policy_identity")
            else None
        ),
        entry_auxiliary_policy_identity_version=payload.get(
            "entry_auxiliary_policy_identity_version"
        ),
        **situation_fields(payload),
        actual_order_submitted=False,
        runtime_effect=False,
        broker_order_forbidden=True,
    )
    commit["decision_source_sha256"] = decision_source_sha256(commit)
    return register(
        result.code,
        {
            "id": identity,
            "committed_at_epoch": result.completed_epoch,
            "remaining_sec": list(OBSERVATION_HORIZONS),
            "route": route,
            **observation_contract(),
            "quote_transport_epoch": epoch,
            "decision_source_sha256": commit["decision_source_sha256"],
        },
        commit=commit,
    )
