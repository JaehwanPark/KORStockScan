"""Asynchronous scanner preparation/AI handoff with main-thread commit guards."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, field
from queue import Empty, SimpleQueue
import threading
import time
from types import MappingProxyType
from typing import Any

from src.engine.ai.hot_path_ai_dispatcher import (
    HotPathAIDispatcher,
    HotPathAIRequest,
)
from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration

SCANNER_ASYNC_EVAL_VERSION = "scanner_async_eval_commit_v1"
_MAX_READY_RESULTS = 128
_MAX_CANCELLED_GENERATIONS = 256


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(item) for item in value)
    return deepcopy(value)


def thaw_scanner_async_value(value: Any) -> Any:
    """Return a private mutable copy for a worker/provider call."""

    if isinstance(value, Mapping):
        return {str(key): thaw_scanner_async_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_scanner_async_value(item) for item in value]
    if isinstance(value, frozenset):
        return {thaw_scanner_async_value(item) for item in value}
    return deepcopy(value)


def _immutable_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return _deep_freeze(dict(value or {}))


@dataclass(frozen=True, slots=True)
class ScannerAsyncEvalContext:
    generation: ScannerGeneration
    cache_key: str
    submitted_epoch: float
    deadline_epoch: float
    stock_snapshot: Mapping[str, Any]
    ws_snapshot: Mapping[str, Any]
    state_version: str

    @classmethod
    def create(
        cls,
        *,
        generation: ScannerGeneration,
        cache_key: str,
        submitted_epoch: float,
        deadline_epoch: float,
        stock_snapshot: Mapping[str, Any],
        ws_snapshot: Mapping[str, Any],
        state_version: str,
    ) -> "ScannerAsyncEvalContext":
        if not isinstance(generation, ScannerGeneration):
            raise TypeError("scanner async context requires ScannerGeneration")
        submitted = float(submitted_epoch)
        deadline = float(deadline_epoch)
        if deadline <= submitted:
            raise ValueError("scanner async context requires future deadline")
        return cls(
            generation=generation,
            cache_key=str(cache_key or "").strip() or generation.generation_id,
            submitted_epoch=submitted,
            deadline_epoch=deadline,
            stock_snapshot=_immutable_mapping(stock_snapshot),
            ws_snapshot=_immutable_mapping(ws_snapshot),
            state_version=str(state_version or "-"),
        )

    @property
    def request_id(self) -> str:
        return f"{self.generation.generation_id}:{self.cache_key}"


@dataclass(frozen=True, slots=True)
class ScannerAsyncEvalRequest:
    context: ScannerAsyncEvalContext
    prepare: Callable[[ScannerAsyncEvalContext], Mapping[str, Any]] = field(
        repr=False,
        compare=False,
    )
    evaluate: Callable[
        [ScannerAsyncEvalContext, Mapping[str, Any]], Mapping[str, Any]
    ] = field(repr=False, compare=False)
    requires_ai_dispatch: bool = True


@dataclass(frozen=True, slots=True)
class ScannerAsyncEvalResult:
    request_id: str
    generation_id: str
    code: str
    venue: str
    cache_key: str
    state_version: str
    status: str
    submitted_epoch: float
    preparation_started_epoch: float
    preparation_completed_epoch: float
    ai_started_epoch: float
    completed_epoch: float
    preparation_wait_sec: float
    preparation_service_sec: float
    ai_dispatch_wait_sec: float
    ai_response_sec: float
    observation_only: bool
    prepared_context: Mapping[str, Any] = field(default_factory=dict)
    ai_payload: Mapping[str, Any] = field(default_factory=dict)
    error_type: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class ScannerAsyncSubmitDecision:
    accepted: bool
    reason: str
    request_id: str
    pending_count: int


@dataclass(frozen=True, slots=True)
class ScannerAsyncCommitDecision:
    allowed: bool
    reason: str
    fields: Mapping[str, Any]


class ScannerAsyncEvalCoordinator:
    """Run immutable market preparation then AI; never apply runtime state."""

    def __init__(
        self,
        *,
        ai_dispatcher: HotPathAIDispatcher,
        owns_ai_dispatcher: bool = True,
    ) -> None:
        if not isinstance(ai_dispatcher, HotPathAIDispatcher):
            raise TypeError("scanner async coordinator requires AI dispatcher")
        self.ai_dispatcher = ai_dispatcher
        self.owns_ai_dispatcher = bool(owns_ai_dispatcher)
        self._preparation_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="scanner_market_prepare",
        )
        self._lock = threading.RLock()
        self._requests: dict[str, ScannerAsyncEvalRequest] = {}
        self._preparation_futures: dict[str, Future] = {}
        self._prepared: dict[str, Mapping[str, Any]] = {}
        self._preparation_timings: dict[str, tuple[float, float]] = {}
        self._completed: SimpleQueue[ScannerAsyncEvalResult] = SimpleQueue()
        self._ready: dict[str, ScannerAsyncEvalResult] = {}
        self._undrained_request_ids: set[str] = set()
        self._cancelled_generations: set[str] = set()
        self._closed = False

    def submit(self, request: ScannerAsyncEvalRequest) -> ScannerAsyncSubmitDecision:
        if not isinstance(request, ScannerAsyncEvalRequest):
            raise TypeError("coordinator accepts ScannerAsyncEvalRequest only")
        if not callable(request.prepare) or not callable(request.evaluate):
            raise TypeError("scanner async request requires prepare and evaluate")
        request_id = request.context.request_id
        with self._lock:
            if self._closed:
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="coordinator_closed",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            if request_id in self._requests:
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="duplicate_generation_cache_key_coalesced",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            if request_id in self._ready:
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="completed_result_pending_commit",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            self._requests[request_id] = request
            future = self._preparation_executor.submit(self._prepare, request)
            self._preparation_futures[request_id] = future
            future.add_done_callback(
                lambda completed, rid=request_id: self._on_prepared(rid, completed)
            )
            return ScannerAsyncSubmitDecision(
                accepted=True,
                reason="market_preparation_dispatched",
                request_id=request_id,
                pending_count=len(self._requests),
            )

    @staticmethod
    def _prepare(
        request: ScannerAsyncEvalRequest,
    ) -> tuple[float, float, Mapping[str, Any]]:
        started = time.time()
        if started > request.context.deadline_epoch:
            return started, started, MappingProxyType({})
        prepared = request.prepare(request.context)
        completed = time.time()
        return started, completed, _immutable_mapping(prepared)

    def _on_prepared(self, request_id: str, future: Future) -> None:
        with self._lock:
            request = self._requests.get(request_id)
            self._preparation_futures.pop(request_id, None)
        if request is None:
            return
        try:
            started, completed, prepared = future.result()
        except Exception as exc:
            now = time.time()
            self._finish(
                request,
                status="preparation_error",
                preparation_started_epoch=now,
                preparation_completed_epoch=now,
                completed_epoch=now,
                observation_only=True,
                error_type=type(exc).__name__,
                error_message=str(exc)[:240],
            )
            return
        with self._lock:
            generation_cancelled = (
                request.context.generation.generation_id in self._cancelled_generations
            )
        if generation_cancelled:
            self._finish(
                request,
                status="superseded_before_ai",
                preparation_started_epoch=started,
                preparation_completed_epoch=completed,
                completed_epoch=completed,
                observation_only=True,
                prepared_context=prepared,
            )
            return
        if completed > request.context.deadline_epoch:
            self._finish(
                request,
                status="preparation_deadline_expired",
                preparation_started_epoch=started,
                preparation_completed_epoch=completed,
                completed_epoch=completed,
                observation_only=True,
                prepared_context=prepared,
            )
            return
        if not request.requires_ai_dispatch:
            self._finish(
                request,
                status="completed",
                preparation_started_epoch=started,
                preparation_completed_epoch=completed,
                completed_epoch=completed,
                observation_only=False,
                prepared_context=prepared,
            )
            return
        with self._lock:
            self._prepared[request_id] = prepared
            self._preparation_timings[request_id] = (started, completed)
        ai_request = HotPathAIRequest.create(
            request_id=request_id,
            generation_id=request.context.generation.generation_id,
            cache_key=request.context.cache_key,
            endpoint="scanner_entry",
            venue=request.context.generation.venue,
            submitted_epoch=completed,
            deadline_epoch=request.context.deadline_epoch,
            execute=lambda: request.evaluate(request.context, prepared),
            metadata={
                "scanner_async_request_id": request_id,
                "scanner_state_version": request.context.state_version,
            },
        )
        decision = self.ai_dispatcher.submit(ai_request)
        if not decision.accepted:
            self._finish(
                request,
                status="ai_dispatch_rejected",
                preparation_started_epoch=started,
                preparation_completed_epoch=completed,
                completed_epoch=time.time(),
                observation_only=True,
                prepared_context=prepared,
                error_type="HotPathAISubmitRejected",
                error_message=decision.reason,
            )

    def poll(self) -> int:
        finished = 0
        with self._lock:
            request_ids = frozenset(self._requests)
        for ai_result in self.ai_dispatcher.drain_completed(request_ids=request_ids):
            request_id = ai_result.request_id
            with self._lock:
                request = self._requests.get(request_id)
                prepared = self._prepared.pop(request_id, MappingProxyType({}))
                timings = self._preparation_timings.pop(
                    request_id,
                    (ai_result.submitted_epoch, ai_result.submitted_epoch),
                )
            if request is None:
                continue
            with self._lock:
                superseded = (
                    request.context.generation.generation_id
                    in self._cancelled_generations
                )
            self._finish(
                request,
                status="superseded_result" if superseded else ai_result.status,
                preparation_started_epoch=timings[0],
                preparation_completed_epoch=timings[1],
                ai_started_epoch=ai_result.started_epoch,
                completed_epoch=ai_result.completed_epoch,
                observation_only=bool(ai_result.observation_only or superseded),
                prepared_context=prepared,
                ai_payload=ai_result.payload,
                ai_dispatch_wait_sec=ai_result.ai_dispatch_wait_sec,
                ai_response_sec=ai_result.ai_response_sec,
                error_type=ai_result.error_type,
                error_message=ai_result.error_message,
            )
            finished += 1
        return finished

    def _finish(
        self,
        request: ScannerAsyncEvalRequest,
        *,
        status: str,
        preparation_started_epoch: float,
        preparation_completed_epoch: float,
        completed_epoch: float,
        observation_only: bool,
        ai_started_epoch: float = 0.0,
        prepared_context: Mapping[str, Any] | None = None,
        ai_payload: Mapping[str, Any] | None = None,
        ai_dispatch_wait_sec: float = 0.0,
        ai_response_sec: float = 0.0,
        error_type: str = "",
        error_message: str = "",
    ) -> None:
        context = request.context
        result = ScannerAsyncEvalResult(
            request_id=context.request_id,
            generation_id=context.generation.generation_id,
            code=context.generation.code,
            venue=context.generation.venue,
            cache_key=context.cache_key,
            state_version=context.state_version,
            status=status,
            submitted_epoch=context.submitted_epoch,
            preparation_started_epoch=preparation_started_epoch,
            preparation_completed_epoch=preparation_completed_epoch,
            ai_started_epoch=ai_started_epoch,
            completed_epoch=completed_epoch,
            preparation_wait_sec=max(
                0.0, preparation_started_epoch - context.submitted_epoch
            ),
            preparation_service_sec=max(
                0.0, preparation_completed_epoch - preparation_started_epoch
            ),
            ai_dispatch_wait_sec=max(0.0, ai_dispatch_wait_sec),
            ai_response_sec=max(0.0, ai_response_sec),
            observation_only=observation_only,
            prepared_context=_immutable_mapping(prepared_context),
            ai_payload=_immutable_mapping(ai_payload),
            error_type=error_type,
            error_message=error_message,
        )
        with self._lock:
            self._requests.pop(context.request_id, None)
            self._preparation_futures.pop(context.request_id, None)
            self._prepared.pop(context.request_id, None)
            self._preparation_timings.pop(context.request_id, None)
            self._ready[context.request_id] = result
            self._undrained_request_ids.add(context.request_id)
            while len(self._ready) > _MAX_READY_RESULTS:
                oldest_request_id = next(iter(self._ready))
                self._ready.pop(oldest_request_id, None)
        self._completed.put(result)

    def drain_completed(
        self, *, limit: int | None = None
    ) -> list[ScannerAsyncEvalResult]:
        self.poll()
        completed: list[ScannerAsyncEvalResult] = []
        max_items = None if limit is None else max(0, int(limit))
        while max_items is None or len(completed) < max_items:
            try:
                result = self._completed.get_nowait()
            except Empty:
                break
            with self._lock:
                self._undrained_request_ids.discard(result.request_id)
            completed.append(result)
        return completed

    def take_completed(
        self, *, generation_id: str, cache_key: str
    ) -> ScannerAsyncEvalResult | None:
        self.poll()
        request_id = (
            f"{str(generation_id or '').strip()}:{str(cache_key or '').strip()}"
        )
        with self._lock:
            return self._ready.pop(request_id, None)

    def discard_completed(
        self, *, generation_id: str, cache_key: str
    ) -> ScannerAsyncEvalResult | None:
        request_id = (
            f"{str(generation_id or '').strip()}:{str(cache_key or '').strip()}"
        )
        with self._lock:
            return self._ready.pop(request_id, None)

    def is_pending(self, *, generation_id: str, cache_key: str) -> bool:
        request_id = (
            f"{str(generation_id or '').strip()}:{str(cache_key or '').strip()}"
        )
        with self._lock:
            return request_id in self._requests

    def has_completed(self, *, generation_id: str, cache_key: str) -> bool:
        """Return whether a result is retained for this exact transport.

        The main thread is the only consumer of retained output.  Scanner
        scheduling uses this narrow read-only check to avoid re-dispatching a
        same-generation heavy evaluation in the small interval before the
        COMMIT lane claims the result.
        """

        request_id = (
            f"{str(generation_id or '').strip()}:{str(cache_key or '').strip()}"
        )
        with self._lock:
            return request_id in self._ready

    def has_completed_result(self) -> bool:
        """Report a result retained for main-thread COMMIT consumption.

        This remains true after the outer notification drain and must not be
        used as a cooperative-yield signal. The caller still needs
        ``take_completed`` or ``discard_completed`` to close the retained
        result.
        """

        self.poll()
        with self._lock:
            return bool(self._ready)

    def has_undrained_result(self) -> bool:
        """Report worker output that the outer main-thread drain has not seen.

        A result remains in ``_ready`` after the drain because the scheduler
        COMMIT lane still needs to consume it. Using that retained state as a
        cooperative-yield signal would make the main loop yield before it can
        execute the COMMIT.
        """

        self.poll()
        with self._lock:
            return bool(self._undrained_request_ids)

    def invalidate_generation(self, generation_id: str) -> None:
        normalized = str(generation_id or "").strip()
        if normalized:
            with self._lock:
                self._cancelled_generations.add(normalized)
                while len(self._cancelled_generations) > _MAX_CANCELLED_GENERATIONS:
                    self._cancelled_generations.pop()
                stale_ready_ids = [
                    request_id
                    for request_id, result in self._ready.items()
                    if result.generation_id == normalized
                ]
                for request_id in stale_ready_ids:
                    self._ready.pop(request_id, None)

    def reactivate_generation(self, generation_id: str) -> bool:
        """Release a fully quiesced generation for one scheduler-owned retry.

        The scheduler may deliberately reuse immutable generation provenance
        for a bounded fresh-market recheck.  Never release cancellation while
        an old preparation/AI request or retained result still exists.
        """

        normalized = str(generation_id or "").strip()
        if not normalized:
            return False
        with self._lock:
            if any(
                request.context.generation.generation_id == normalized
                for request in self._requests.values()
            ):
                return False
            if any(
                result.generation_id == normalized for result in self._ready.values()
            ):
                return False
            request_prefix = f"{normalized}:"
            if any(
                request_id.startswith(request_prefix)
                for request_id in self._undrained_request_ids
            ):
                return False
            if normalized not in self._cancelled_generations:
                return True
            self._cancelled_generations.discard(normalized)
            return True

    def pending_count(self) -> int:
        with self._lock:
            return len(self._requests)

    def shutdown(self, *, wait: bool = False) -> None:
        with self._lock:
            self._closed = True
        self._preparation_executor.shutdown(wait=wait, cancel_futures=True)
        if self.owns_ai_dispatcher:
            self.ai_dispatcher.shutdown(wait=wait)


def validate_scanner_async_commit(
    result: ScannerAsyncEvalResult,
    *,
    current_generation: ScannerGeneration | None,
    current_status: str,
    current_venue: str,
    current_source_signature: str,
    venue_resolution_valid: bool,
    current_state_version: str,
    quote_fresh: bool,
    position_or_pending_order_present: bool,
    cooldown_active: bool,
    now_epoch: float,
) -> ScannerAsyncCommitDecision:
    fields = {
        "metric_role": "runtime_scheduler_latency",
        "decision_authority": "scanner_main_thread_commit_guard",
        "window_policy": "per_scanner_generation_action_timestamps",
        "sample_floor": "one_completed_async_scanner_result",
        "primary_decision_metric": "result_to_commit_sec",
        "source_quality_gate": "generation_venue_state_and_fresh_quote_required",
        "forbidden_uses": (
            "standalone_buy,broker_submit,threshold_mutation,provider_route_change,"
            "order_price_change,quantity_or_cap_change,broker_guard_bypass,"
            "stale_quote_bypass,hard_safety_bypass"
        ),
        "scanner_async_version": SCANNER_ASYNC_EVAL_VERSION,
        "scanner_async_result_status": result.status,
        "scanner_generation_id": result.generation_id,
        "effective_venue": result.venue,
        "result_to_commit_sec": round(
            max(0.0, float(now_epoch) - result.completed_epoch), 6
        ),
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
    }
    reason = "commit_allowed"
    if result.status != "completed" or result.observation_only:
        reason = "result_not_commit_eligible"
    elif current_generation is None:
        reason = "current_generation_missing"
    elif current_generation.generation_id != result.generation_id:
        reason = "generation_superseded"
    elif str(current_status or "").upper() != "WATCHING":
        reason = "target_not_watching"
    elif str(current_venue or "").upper() != result.venue:
        reason = "venue_conflict"
    elif not venue_resolution_valid:
        reason = "venue_resolution_missing_or_conflicted"
    elif not str(current_source_signature or "").strip():
        reason = "source_signature_missing"
    elif (
        str(current_source_signature or "").strip()
        != str(current_generation.source_signature or "").strip()
    ):
        reason = "source_signature_conflict"
    elif str(current_state_version or "-") != result.state_version:
        reason = "state_version_changed"
    elif not quote_fresh:
        reason = "quote_stale_or_missing"
    elif position_or_pending_order_present:
        reason = "position_or_pending_order_present"
    elif cooldown_active:
        reason = "cooldown_active"
    allowed = reason == "commit_allowed"
    fields["scanner_async_commit_allowed"] = allowed
    fields["scanner_async_commit_reason"] = reason
    return ScannerAsyncCommitDecision(
        allowed=allowed,
        reason=reason,
        fields=_immutable_mapping(fields),
    )
