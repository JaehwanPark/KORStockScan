"""Bounded asynchronous dispatcher for live hot-path AI calls.

The dispatcher owns transport scheduling only.  It never receives broker, DB,
or mutable runtime-state handles.  Callers must validate every completed result
against current main-thread state before applying it.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
import threading
import time
from typing import AbstractSet, Any

from src.engine.infrastructure.snapshot_copy import (
    immutable_mapping as _immutable_mapping,
)

HOT_PATH_AI_DISPATCHER_VERSION = "hot_path_ai_dispatcher_v1"


@dataclass(frozen=True, slots=True)
class HotPathAIRequest:
    request_id: str
    generation_id: str
    cache_key: str
    endpoint: str
    venue: str
    submitted_epoch: float
    deadline_epoch: float
    execute: Callable[[], Mapping[str, Any]] = field(
        repr=False,
        compare=False,
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)
    on_complete: Callable[[Any], bool] | None = field(
        default=None, repr=False, compare=False
    )

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        generation_id: str,
        cache_key: str,
        endpoint: str,
        venue: str,
        submitted_epoch: float,
        deadline_epoch: float,
        execute: Callable[[], Mapping[str, Any]],
        metadata: Mapping[str, Any] | None = None,
        on_complete: Callable[[Any], bool] | None = None,
    ) -> "HotPathAIRequest":
        if not callable(execute):
            raise TypeError("hot-path AI request requires callable execute")
        if on_complete is not None and not callable(on_complete):
            raise TypeError("hot-path AI completion must be callable")
        normalized_request_id = str(request_id or "").strip()
        normalized_generation_id = str(generation_id or "").strip()
        normalized_cache_key = str(cache_key or "").strip()
        normalized_endpoint = str(endpoint or "unknown").strip().lower() or "unknown"
        if (
            not normalized_request_id
            or not normalized_generation_id
            or not normalized_cache_key
        ):
            raise ValueError(
                "hot-path AI request requires request, generation, and cache ids"
            )
        submitted = float(submitted_epoch)
        deadline = float(deadline_epoch)
        if submitted <= 0 or deadline <= submitted:
            raise ValueError("hot-path AI request requires a future deadline")
        return cls(
            request_id=normalized_request_id,
            generation_id=normalized_generation_id,
            cache_key=normalized_cache_key,
            endpoint=normalized_endpoint,
            venue=str(venue or "UNKNOWN").strip().upper(),
            submitted_epoch=submitted,
            deadline_epoch=deadline,
            execute=execute,
            metadata=_immutable_mapping(metadata),
            on_complete=on_complete,
        )

    @property
    def dedupe_key(self) -> tuple[str, str, str]:
        """Return the transport coalescing identity for one AI endpoint.

        A position/generation can legitimately have a holding-score, holding-flow,
        entry-price, and gatekeeper request in flight at the same time. Those
        calls share dispatcher capacity, but their results are not interchangeable.
        Coalescing only by generation and cache key could silently discard a
        different endpoint's request when both use the same snapshot key.
        """

        return self.endpoint, self.generation_id, self.cache_key


@dataclass(frozen=True, slots=True)
class HotPathAIResult:
    request_id: str
    generation_id: str
    cache_key: str
    endpoint: str
    venue: str
    status: str
    submitted_epoch: float
    started_epoch: float
    completed_epoch: float
    ai_dispatch_wait_sec: float
    ai_response_sec: float
    observation_only: bool
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    error_type: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class HotPathAISubmitDecision:
    accepted: bool
    reason: str
    request_id: str
    canonical_request_id: str
    pending_count: int


class HotPathAIDispatcher:
    """Deduplicate and execute live AI jobs outside the sniper main thread."""

    def __init__(self, *, loaded_key_count: int, max_workers: int = 2) -> None:
        self.loaded_key_count = max(0, int(loaded_key_count))
        if self.loaded_key_count <= 0:
            raise ValueError("hot-path AI dispatcher requires a loaded provider key")
        self.max_workers = min(
            max(1, int(max_workers)),
            self.loaded_key_count,
        )
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="hot_path_ai",
        )
        self._lock = threading.RLock()
        self._pending: dict[tuple[str, str, str], tuple[HotPathAIRequest, Future]] = {}
        self._completed: deque[HotPathAIResult] = deque()
        self._closed = False

    def submit(self, request: HotPathAIRequest) -> HotPathAISubmitDecision:
        if not isinstance(request, HotPathAIRequest):
            raise TypeError("dispatcher accepts HotPathAIRequest only")
        with self._lock:
            if self._closed:
                return HotPathAISubmitDecision(
                    accepted=False,
                    reason="dispatcher_closed",
                    request_id=request.request_id,
                    canonical_request_id=request.request_id,
                    pending_count=len(self._pending),
                )
            current = self._pending.get(request.dedupe_key)
            if current is not None:
                return HotPathAISubmitDecision(
                    accepted=False,
                    reason="duplicate_generation_cache_key_coalesced",
                    request_id=request.request_id,
                    canonical_request_id=current[0].request_id,
                    pending_count=len(self._pending),
                )
            future = self._executor.submit(self._execute, request)
            self._pending[request.dedupe_key] = (request, future)
            decision = HotPathAISubmitDecision(
                accepted=True,
                reason="ai_request_dispatched",
                request_id=request.request_id,
                canonical_request_id=request.request_id,
                pending_count=len(self._pending),
            )
        # An already settled Future invokes this synchronously. Publication
        # must never run under the dispatcher scheduling lock.
        future.add_done_callback(
            lambda completed, key=request.dedupe_key: self._on_done(key, completed)
        )
        return decision

    def _execute(self, request: HotPathAIRequest) -> HotPathAIResult:
        started = time.time()
        if started > request.deadline_epoch:
            return self._result(
                request,
                status="expired_before_start",
                started_epoch=started,
                completed_epoch=started,
                observation_only=True,
            )
        try:
            raw_payload = request.execute()
            payload = _immutable_mapping(raw_payload)
            completed = time.time()
            late = completed > request.deadline_epoch
            return self._result(
                request,
                status="expired_after_response" if late else "completed",
                started_epoch=started,
                completed_epoch=completed,
                observation_only=late,
                payload=payload,
            )
        except Exception as exc:
            completed = time.time()
            return self._result(
                request,
                status="error",
                started_epoch=started,
                completed_epoch=completed,
                observation_only=True,
                error_type=type(exc).__name__,
                error_message=str(exc)[:240],
            )

    @staticmethod
    def _result(
        request: HotPathAIRequest,
        *,
        status: str,
        started_epoch: float,
        completed_epoch: float,
        observation_only: bool,
        payload: Mapping[str, Any] | None = None,
        error_type: str = "",
        error_message: str = "",
    ) -> HotPathAIResult:
        return HotPathAIResult(
            request_id=request.request_id,
            generation_id=request.generation_id,
            cache_key=request.cache_key,
            endpoint=request.endpoint,
            venue=request.venue,
            status=status,
            submitted_epoch=request.submitted_epoch,
            started_epoch=started_epoch,
            completed_epoch=completed_epoch,
            ai_dispatch_wait_sec=max(0.0, started_epoch - request.submitted_epoch),
            ai_response_sec=max(0.0, completed_epoch - started_epoch),
            observation_only=observation_only,
            payload=_immutable_mapping(payload),
            metadata=_immutable_mapping(request.metadata),
            error_type=error_type,
            error_message=error_message,
        )

    def _on_done(
        self,
        dedupe_key: tuple[str, str, str],
        future: Future,
    ) -> None:
        with self._lock:
            request_and_future = self._pending.pop(dedupe_key, None)
        try:
            result = future.result()
        except Exception as exc:  # defensive: _execute already captures failures
            if request_and_future is None:
                return
            request = request_and_future[0]
            now = time.time()
            result = self._result(
                request,
                status="dispatcher_internal_error",
                started_epoch=now,
                completed_epoch=now,
                observation_only=True,
                error_type=type(exc).__name__,
                error_message=str(exc)[:240],
            )
        # Publication acknowledgement transfers only immutable result custody.
        # Rejection/failure leaves the original result for ordinary polling.
        callback = request_and_future[0].on_complete if request_and_future else None
        callback_error = None
        if callback is not None:
            try:
                if callback(result) is True:
                    return
            except Exception as exc:
                callback_error = type(exc).__name__
        self.restore_completed(result, front=False)
        if callback_error is not None:
            from src.engine.monitoring.runtime_performance import failure

            failure("async_completion_delivery", callback_error, emit_log=False)

    def restore_completed(self, result, *, front=True):
        """Retain the same settled result; never reevaluate or renew its deadline."""
        with self._lock:
            if not any(item is result for item in self._completed):
                if front:
                    self._completed.appendleft(result)
                else:
                    self._completed.append(result)
            notification = getattr(self, "completion_event", None)
            if notification is not None:
                notification.set()

    def drain_completed(
        self,
        *,
        limit: int | None = None,
        request_ids: AbstractSet[str] | None = None,
    ) -> list[HotPathAIResult]:
        """Drain only caller-owned results and preserve other endpoint results."""

        completed: list[HotPathAIResult] = []
        max_items = None if limit is None else max(0, int(limit))
        owned_ids = (
            None
            if request_ids is None
            else frozenset(str(request_id) for request_id in request_ids)
        )
        with self._lock:
            retained: deque[HotPathAIResult] = deque()
            while self._completed:
                result = self._completed.popleft()
                is_owned = owned_ids is None or result.request_id in owned_ids
                has_capacity = max_items is None or len(completed) < max_items
                if is_owned and has_capacity:
                    completed.append(result)
                else:
                    retained.append(result)
            self._completed = retained
        return completed

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def shutdown(self, *, wait: bool = False) -> None:
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=True)
