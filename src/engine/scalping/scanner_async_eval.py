"""Asynchronous scanner preparation/AI handoff with main-thread commit guards."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextvars import ContextVar
from collections import OrderedDict
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo
import math
import hashlib
import os
import threading
import time
from types import MappingProxyType
from typing import Any
from pathlib import Path

from src.engine.ai.hot_path_ai_dispatcher import (
    HotPathAIDispatcher,
    HotPathAIRequest,
)
from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration

SCANNER_ASYNC_EVAL_VERSION = "scanner_async_eval_commit_v1"
_MAX_READY_RESULTS = 128
_MAX_CANCELLED_GENERATIONS = 256

# Main's invocation owns a result from the instant take removes it, including
# exceptions before the resolver has constructed its return dictionary.
ASYNC_CONSUMPTION = ContextVar('main_async_consumption', default=None)


def async_request_binding(context):
    return dict(async_request_id=context.request_id, async_producer_pid=os.getpid(),
        async_producer_start_ticks=_PROCESS_START,
        async_origin_deadline_epoch=context.deadline_epoch,
        async_order_venue=context.generation.venue,
        scanner_generation_id=context.generation.generation_id)
try:
    _PROCESS_START = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
except (OSError, IndexError):
    _PROCESS_START = None


def _append_async_disposition(code, fields):
    from src.utils.pipeline_event_logger import emit_pipeline_event
    return emit_pipeline_event('ENTRY_PIPELINE', code, code,
                               'entry_async_disposition', fields=fields)


def record_async_disposition(result, disposition, reason, **facts):
    """Use the existing compact pipeline; never alter provider outbox state."""
    try:
        event = (result.native_claim.get('snapshot') or [{}])[0]
        payload = result.ai_payload
        identity = f'{os.getpid()}|{_PROCESS_START}|{result.request_id}|{disposition}'
        fields = dict(
                async_disposition_event_id=hashlib.sha256(identity.encode()).hexdigest(),
                async_disposition=disposition, async_disposition_reason=str(reason),
                async_request_id=result.request_id, scanner_generation_id=result.generation_id,
                evaluation_attempt_id=payload.get('evaluation_attempt_id'),
                ai_decision_trace_id=payload.get('ai_decision_trace_id'),
                async_origin_snapshot_id=payload.get('ai_decision_snapshot_id') or payload.get('ai_market_snapshot_id'),
                async_machine_action=payload.get('entry_mechanistic_action'),
                async_auxiliary_status=payload.get('entry_ai_screen_status'),
                async_auxiliary_verdict=payload.get('entry_ai_risk_verdict'),
                async_provider_called=payload.get('provider_called'),
                async_producer_start_ticks=_PROCESS_START,
                async_release=os.getenv('KORSTOCKSCAN_RUNTIME_GIT_COMMIT'),
                **{k:v for k,v in result.origin_fields.items() if k not in (
                    'effective_venue','entry_machine_bundle_sha256','entry_auxiliary_policy_sha256')},
                native_event_id=event.get('event_id'), native_signal_id=event.get('signal_id'),
                effective_venue=payload.get('effective_venue') or result.origin_fields.get('effective_venue') or result.venue,
                async_order_venue=result.venue,
                entry_machine_bundle_sha256=payload.get('machine_bundle_sha256') or result.origin_fields.get('entry_machine_bundle_sha256'),
                entry_auxiliary_policy_sha256=payload.get('entry_ai_component_sha256') or result.origin_fields.get('entry_auxiliary_policy_sha256'),
                async_origin_deadline_epoch=result.deadline_epoch,
                async_worker_completed_epoch=result.completed_epoch,
                async_disposition_epoch=time.time(), async_producer_pid=os.getpid(),
                async_request_source_date=datetime.fromtimestamp(
                    getattr(result, 'submitted_epoch', result.completed_epoch),
                    ZoneInfo('Asia/Seoul')).date().isoformat(),
                metric_role='source_quality_gate', decision_authority='report_only',
                window_policy='current_pid_exact_attempt_with_carry_in_out', sample_floor='none',
                primary_decision_metric='pass_to_main_disposition_coverage',
                forbidden_uses='policy_promotion,broker_order,economics',
                actual_order_submitted=False, broker_order_forbidden=True, runtime_effect=False,
                **facts)
        if getattr(result, 'observation_sink', None) is not None:
            return result.observation_sink(_append_async_disposition, result.code, fields)
        receipt = _append_async_disposition(result.code, fields)
        success = isinstance(receipt, dict) and receipt.get('structured_append_succeeded') is True
        if (not success or receipt.get('structured_append_status') != 'raw_appended'
                or receipt.get('structured_compact_append_succeeded') is False):
            from src.engine.monitoring.runtime_performance import failure
            failure('async_disposition', (receipt or {}).get('structured_append_status', 'writer_unobservable')
                    if isinstance(receipt, dict) else 'writer_unobservable')
        return success
    except Exception as exc:
        try:
            from src.engine.monitoring.runtime_performance import failure
            failure('async_disposition', type(exc).__name__, emit_log=False)
        except Exception:
            pass
        return False


@dataclass(frozen=True, slots=True)
class FixedWatchGeneration:
    """Native fixed-watch identity, never a scanner promotion."""
    code: str
    venue: str
    generation_id: str
    source_signature: str
    claim_epoch: float
    promotion_epoch: float = 0.0

    @classmethod
    def from_claim(cls, code, claim):
        from src.engine.scalping.entry_deadline import claim_deadline_epoch
        proof = claim.get('source_registration_receipt') or {}
        event = claim['snapshot'][0]
        if (not proof.get('sha256') or event['symbol'] != code
                or claim_deadline_epoch(claim) <= time.time()):
            raise ValueError('fixed_watch_native_identity_missing_or_expired')
        return cls(code, event['venue'], 'fixed-watch:' + claim['token'],
                   proof['sha256'], float(event['epoch']))

    def timing_fields(self, *, now_epoch):
        return dict(entry_async_identity_kind='fixed_watch_native_claim',
                    fixed_watch_request_identity=self.generation_id,
                    source_registration_sha256=self.source_signature,
                    signal_age_seconds=max(0.,now_epoch-self.claim_epoch))


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
    submitted_perf: float = field(default_factory=time.perf_counter, compare=False)
    deadline_perf: float = 0.0

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
        caller_deadline_perf: float | None = None,
    ) -> "ScannerAsyncEvalContext":
        if not isinstance(generation, (ScannerGeneration, FixedWatchGeneration)):
            raise TypeError("async context requires scanner or native fixed-watch identity")
        submitted = float(submitted_epoch)
        deadline = float(deadline_epoch)
        if (
            isinstance(submitted_epoch, bool)
            or isinstance(deadline_epoch, bool)
            or not math.isfinite(submitted)
            or not math.isfinite(deadline)
            or deadline <= submitted
        ):
            raise ValueError("scanner async context requires future deadline")
        perf = time.perf_counter()
        if caller_deadline_perf is not None and (
            isinstance(caller_deadline_perf, bool)
            or not math.isfinite(float(caller_deadline_perf))
            or float(caller_deadline_perf) <= 0
        ):
            raise ValueError('invalid original monotonic deadline')
        return cls(
            generation=generation,
            cache_key=str(cache_key or "").strip() or generation.generation_id,
            submitted_epoch=submitted,
            deadline_epoch=deadline,
            stock_snapshot=_immutable_mapping({k:v for k,v in stock_snapshot.items()
                if k != '_async_consumption_guard'}),
            ws_snapshot=_immutable_mapping(ws_snapshot),
            state_version=str(state_version or "-"),
            submitted_perf=perf,
            deadline_perf=min(perf+max(0.0, deadline-time.time()),
                              float(caller_deadline_perf) if caller_deadline_perf is not None else float('inf')),
        )

    def expired(self):
        return time.time() >= self.deadline_epoch or (self.deadline_perf > 0 and time.perf_counter() >= self.deadline_perf)

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
    refresh_before_evaluate: (
        Callable[[ScannerAsyncEvalContext, Mapping[str, Any]], Mapping[str, Any]] | None
    ) = field(default=None, repr=False, compare=False)


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
    deadline_perf: float = 0.0
    generation_kind: str = "scanner"
    native_claim: Mapping[str, Any] = field(default_factory=dict)
    deadline_epoch: float = 0.0
    original_generation: Any = None
    origin_fields: Mapping[str, Any] = field(default_factory=dict)
    observation_sink: Any = field(default=None, repr=False, compare=False)


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
        observation_sink=None,
    ) -> None:
        if not isinstance(ai_dispatcher, HotPathAIDispatcher):
            raise TypeError("scanner async coordinator requires AI dispatcher")
        self.ai_dispatcher = ai_dispatcher
        self.owns_ai_dispatcher = bool(owns_ai_dispatcher)
        self.observation_sink = observation_sink
        self._preparation_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="scanner_market_prepare",
        )
        self._lock = threading.RLock()
        self._requests: dict[str, ScannerAsyncEvalRequest] = {}
        self._preparation_futures: dict[str, Future] = {}
        self._prepared: dict[str, Mapping[str, Any]] = {}
        self._preparation_timings: dict[str, tuple[float, float]] = {}
        self._completed: OrderedDict[str, ScannerAsyncEvalResult] = OrderedDict()
        self._ready: dict[str, ScannerAsyncEvalResult] = {}
        self._undrained_request_ids: set[str] = set()
        self._consumed = OrderedDict()
        self._cancelled_generations: set[str] = set()
        self._closed = False
        self._preparation_queue = OrderedDict()
        self._preparation_pump = None
        self.completion_event = threading.Event()
        self.ai_dispatcher.completion_event = self.completion_event

    def submit(self, request: ScannerAsyncEvalRequest) -> ScannerAsyncSubmitDecision:
        if not isinstance(request, ScannerAsyncEvalRequest):
            raise TypeError("coordinator accepts ScannerAsyncEvalRequest only")
        if not callable(request.prepare) or not callable(request.evaluate):
            raise TypeError("scanner async request requires prepare and evaluate")
        if request.refresh_before_evaluate is not None and not callable(
            request.refresh_before_evaluate
        ):
            raise TypeError("scanner async refresh must be callable")
        request_id = request.context.request_id
        with self._lock:
            if self._closed:
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="coordinator_closed",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            if request_id in self._consumed:
                return ScannerAsyncSubmitDecision(False, 'result_already_consumed', request_id, len(self._requests))
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
            if request_id in self._undrained_request_ids:
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="completed_notification_pending_drain",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            retained = set(self._requests) | set(self._ready) | self._undrained_request_ids
            if len(retained) >= _MAX_READY_RESULTS:
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="market_preparation_capacity_deferred",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            self._requests[request_id] = request
            try:
                future = Future()
                self._preparation_queue[request_id] = request
                self._preparation_futures[request_id] = future
                future.add_done_callback(
                    lambda completed, rid=request_id: self._on_prepared(rid, completed)
                )
                if self._preparation_pump is None:
                    self._preparation_pump = self._preparation_executor.submit(self._drain_preparations)
            except Exception:
                self._requests.pop(request_id, None)
                self._preparation_queue.pop(request_id, None)
                self._preparation_futures.pop(request_id, None)
                return ScannerAsyncSubmitDecision(
                    accepted=False,
                    reason="market_preparation_enqueue_failed",
                    request_id=request_id,
                    pending_count=len(self._requests),
                )
            return ScannerAsyncSubmitDecision(
                accepted=True,
                reason="market_preparation_dispatched",
                request_id=request_id,
                pending_count=len(self._requests),
            )

    def _drain_preparations(self):
        # Non-preemptive, one existing worker. Aging bounds priority starvation.
        while True:
            with self._lock:
                if not self._preparation_queue:
                    self._preparation_pump = None
                    return
                now = time.perf_counter()
                def priority(pair):
                    request = pair[1]
                    claim = request.context.stock_snapshot.get('_continuous_reversal_pending_claim') or {}
                    snapshot = claim.get('snapshot') or ()
                    confirmed = bool(snapshot and snapshot[0].get('decision_phase') == 'CONFIRMED_UPTICK')
                    aged = now-request.context.submitted_perf >= 1.0
                    return (0 if aged else 1 if confirmed else 2, request.context.submitted_perf)
                rid,request = min(self._preparation_queue.items(), key=priority)
                self._preparation_queue.pop(rid)
                future = self._preparation_futures.get(rid)
            if future is None or not future.set_running_or_notify_cancel():
                continue
            try:
                future.set_result(self._prepare(request))
            except BaseException as exc:
                future.set_exception(exc)

    def _prepare(
        self, request: ScannerAsyncEvalRequest,
    ) -> tuple[float, float, Mapping[str, Any]]:
        started = time.time()
        started_perf = time.perf_counter()
        with self._lock:
            cancelled = self._closed or request.context.generation.generation_id in self._cancelled_generations
        if cancelled or request.context.expired():
            return started, started, MappingProxyType({})
        prepared = request.prepare(request.context)
        completed = time.time()
        from src.engine.monitoring.runtime_performance import observe
        observe('preparation_queue', max(0.,started_perf-request.context.submitted_perf))
        observe('preparation_service', max(0.,time.perf_counter()-started_perf))
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
                status="superseded_before_preparation" if isinstance(exc, CancelledError) else "preparation_error",
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
                self._closed or
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
        if request.context.expired():
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
            if self._requests.get(request_id) is not request:
                return
            self._prepared[request_id] = prepared
            self._preparation_timings[request_id] = (started, completed)
        try:
            ai_request = HotPathAIRequest.create(
                request_id=request_id,
                generation_id=request.context.generation.generation_id,
                cache_key=request.context.cache_key,
                endpoint="scanner_entry",
                venue=request.context.generation.venue,
                submitted_epoch=completed,
                deadline_epoch=request.context.deadline_epoch,
                execute=lambda: self._evaluate_prepared(request, prepared),
                metadata={
                    "scanner_async_request_id": request_id,
                    "scanner_state_version": request.context.state_version,
                },
            )
            decision = self.ai_dispatcher.submit(ai_request)
        except Exception as exc:
            self._finish(
                request,
                status="ai_dispatch_error",
                preparation_started_epoch=started,
                preparation_completed_epoch=completed,
                completed_epoch=time.time(),
                observation_only=True,
                prepared_context=prepared,
                error_type=type(exc).__name__,
                error_message="scanner_async_ai_enqueue_failed",
            )
            return
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

    def _evaluate_prepared(
        self, request: ScannerAsyncEvalRequest, prepared: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Pin the exact execution frame for both evaluation and final commit."""
        request_id = request.context.request_id
        if request.context.expired():
            raise RuntimeError("scanner_async_refresh_deadline_expired")
        with self._lock:
            if (
                self._closed
                or self._requests.get(request_id) is not request
                or request.context.generation.generation_id
                in self._cancelled_generations
            ):
                raise RuntimeError("scanner_async_superseded_before_evaluation")
        if request.refresh_before_evaluate is not None:
            refreshed = request.refresh_before_evaluate(request.context, prepared)
            if not isinstance(refreshed, Mapping):
                raise TypeError("scanner_async_refreshed_frame_must_be_mapping")
            prepared = _immutable_mapping(refreshed)
        # Refresh may outlive the deadline or cancellation. No provider call
        # or runtime commit may resurrect a superseded execution frame.
        with self._lock:
            if (
                self._closed
                or self._requests.get(request_id) is not request
                or request.context.generation.generation_id
                in self._cancelled_generations
            ):
                raise RuntimeError("scanner_async_superseded_during_refresh")
            if request.context.expired():
                raise RuntimeError("scanner_async_refresh_deadline_expired")
            self._prepared[request_id] = prepared
        return request.evaluate(request.context, prepared)

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
                    self._closed or
                    request.context.generation.generation_id
                    in self._cancelled_generations
                )
            self._finish(
                request,
                status="superseded_result" if superseded else "evaluation_deadline_expired" if request.context.expired() and ai_result.status == 'completed' else ai_result.status,
                preparation_started_epoch=timings[0],
                preparation_completed_epoch=timings[1],
                ai_started_epoch=ai_result.started_epoch,
                completed_epoch=ai_result.completed_epoch,
                observation_only=bool(ai_result.observation_only or superseded or request.context.expired()),
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
            deadline_perf=context.deadline_perf,
            generation_kind="fixed_watch" if isinstance(context.generation, FixedWatchGeneration) else "scanner",
            native_claim=_immutable_mapping(context.stock_snapshot.get('_continuous_reversal_pending_claim')),
            deadline_epoch=context.deadline_epoch,
            original_generation=context.generation,
            origin_fields=_immutable_mapping({key: context.stock_snapshot.get(key) for key in
                ('id', 'watch_origin', 'watch_admission_id', 'watch_generation_id', 'scanner_promotion_id',
                 'effective_venue', 'market_session_bucket',
                 'entry_machine_bundle_sha256', 'entry_auxiliary_policy_sha256')}),
            observation_sink=self.observation_sink,
        )
        terminal_reason = None
        evicted = []
        with self._lock:
            if self._requests.get(context.request_id) is not request:
                return
            self._requests.pop(context.request_id, None)
            self._preparation_futures.pop(context.request_id, None)
            self._prepared.pop(context.request_id, None)
            self._preparation_timings.pop(context.request_id, None)
            if self._closed:
                terminal_reason = 'coordinator_shutdown'
            else:
                if context.generation.generation_id in self._cancelled_generations:
                    terminal_reason = 'generation_invalidated'
                else:
                    self._ready[context.request_id] = result
                # Superseded output is still an observation notification,
                # never a retained executable result or a second terminal.
                self._undrained_request_ids.add(context.request_id)
                self._completed[context.request_id] = result
                self.completion_event.set()
                while len(self._ready) > _MAX_READY_RESULTS:
                    oldest_request_id = next(iter(self._ready))
                    evicted.append(self._ready.pop(oldest_request_id))
                    self._completed.pop(oldest_request_id, None)
                    self._undrained_request_ids.discard(oldest_request_id)
        record_async_disposition(result, 'worker_completed', status)
        try:
            from .pre_submit_delay_observation import register_pass_result
            register_pass_result(result)
        except (ValueError, TypeError, KeyError, AttributeError):
            from src.engine.monitoring.runtime_performance import failure
            failure('pre_submit_delay_pass_capture', 'source_unobservable', emit_log=False)
        if terminal_reason:
            record_async_disposition(result, 'terminal_nonexecution', terminal_reason)
        for old in evicted:
            record_async_disposition(old, 'terminal_nonexecution', 'result_retention_overflow')

    def drain_completed(
        self, *, limit: int | None = None
    ) -> list[ScannerAsyncEvalResult]:
        self.poll()
        completed: list[ScannerAsyncEvalResult] = []
        max_items = None if limit is None else max(0, int(limit))
        with self._lock:
            while self._completed and (max_items is None or len(completed) < max_items):
                _, result = self._completed.popitem(last=False)
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
            self._completed.pop(request_id, None)
            self._undrained_request_ids.discard(request_id)
            result = self._ready.pop(request_id, None)
            if result is not None:
                owner = ASYNC_CONSUMPTION.get()
                if owner is not None:
                    owner['original_result'] = result
                self._consumed[request_id] = None
                while len(self._consumed) > 256:
                    self._consumed.popitem(last=False)
            return result

    def peek_completed(self, *, generation_id: str, cache_key: str):
        self.poll()
        with self._lock:
            return self._ready.get(f"{generation_id}:{cache_key}")

    def discard_completed(
        self, *, generation_id: str, cache_key: str, reason='unused_result'
    ) -> ScannerAsyncEvalResult | None:
        request_id = (
            f"{str(generation_id or '').strip()}:{str(cache_key or '').strip()}"
        )
        with self._lock:
            self._completed.pop(request_id, None)
            self._undrained_request_ids.discard(request_id)
            result = self._ready.pop(request_id, None)
            if result is not None:
                self._consumed[request_id] = None
                while len(self._consumed) > 256:
                    self._consumed.popitem(last=False)
        if result is not None:
            record_async_disposition(result, 'terminal_nonexecution', reason)
        return result

    def wait_for_completion(self, timeout: float) -> bool:
        """A consumed wake always causes another loop before sleeping.

        The dispatcher and inbox also set this event. Clearing just before a
        blocking wait would lose their notifications because they do not own
        the coordinator lock.
        """
        if self.completion_event.is_set():
            self.completion_event.clear()
            self.poll()
            return True
        self.poll()
        with self._lock:
            if self._undrained_request_ids:
                return True
        return self.completion_event.wait(timeout)

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
            futures = []
            discarded = []
            with self._lock:
                self._cancelled_generations.add(normalized)
                while len(self._cancelled_generations) > _MAX_CANCELLED_GENERATIONS:
                    live = {r.context.generation.generation_id for r in self._requests.values()}
                    removable = next((g for g in self._cancelled_generations if g not in live), None)
                    if removable is None:
                        break
                    self._cancelled_generations.discard(removable)
                for request_id, future in list(self._preparation_futures.items()):
                    request = self._requests.get(request_id)
                    if request and request.context.generation.generation_id == normalized:
                        futures.append(future)
                stale_ready_ids = [
                    request_id
                    for request_id, result in self._ready.items()
                    if result.generation_id == normalized
                ]
                for request_id in stale_ready_ids:
                    result = self._ready.pop(request_id, None)
                    self._completed.pop(request_id, None)
                    self._undrained_request_ids.discard(request_id)
                    discarded.append(result)
            # Cancellation callbacks and evidence I/O must not hold the lock.
            for future in futures:
                future.cancel()
            for result in discarded:
                record_async_disposition(result, 'terminal_nonexecution', 'generation_invalidated')

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
        with self._lock:
            retained = list(self._ready.values())
            self._ready.clear()
            self._completed.clear()
            self._undrained_request_ids.clear()
        for result in retained:
            record_async_disposition(result, 'terminal_nonexecution', 'coordinator_shutdown')


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
    elif ((result.deadline_epoch > 0 and float(now_epoch) >= result.deadline_epoch)
          or (result.deadline_perf > 0 and time.perf_counter() >= result.deadline_perf)):
        reason = "result_deadline_expired"
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
