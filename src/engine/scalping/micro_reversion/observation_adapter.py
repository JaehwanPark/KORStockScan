"""Fail-isolated, producer-facing observation adapter.

This module deliberately contains no detector, journal, filesystem, replay,
broker, order, or AI dependency.  A market-data producer may hand an immutable
envelope to :class:`ObservationAdapter`; the only downstream operation is a
bounded ``put_nowait`` call.

The adapter may be wired to an existing market-data producer only through the
default-off forward canary.  All three feature flags default to disabled, and
the adapter has no subscription, trading, simulation, or policy authority.
"""

from __future__ import annotations

import os
import queue
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Callable, Protocol, runtime_checkable

from .contracts import normalize_symbol, normalize_venue

OBSERVER_ENVELOPE_SCHEMA = "scalp_micro_reversion_observation_envelope_v4"
OBSERVER_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_observer_runtime_health",
    "decision_authority": "observation_transport_only_no_trading_authority",
    "window_policy": "bounded_process_lifetime_latency_reservoir_and_daily_storage_partition",
    "sample_floor": "collector_health_only_no_economic_promotion",
    "primary_decision_metric": "observation_capture_coverage_pct",
    "source_quality_gate": (
        "aware_timestamps_and_explicit_venue_and_nonnegative_source_sequence"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "sim_or_live_policy_selection",
        "threshold_or_provider_or_bot_mutation",
        "real_execution_quality_approval",
    ),
}


class AdapterResult(StrEnum):
    DISABLED = "disabled"
    ENQUEUED = "enqueued"
    INVALID_ENVELOPE = "invalid_envelope"
    QUEUE_FULL = "queue_full"
    ISOLATED_ERROR = "isolated_error"


class AggressorSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    UNKNOWN = "UNKNOWN"


def _env_enabled(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class ObserverFeatureFlags:
    observer_enabled: bool = False
    path_capture_enabled: bool = False
    depth_capture_enabled: bool = False
    discovery_enabled: bool = False

    @classmethod
    def from_env(cls) -> "ObserverFeatureFlags":
        return cls(
            observer_enabled=_env_enabled("SCALP_MICRO_REVERSION_OBSERVER_ENABLED"),
            path_capture_enabled=_env_enabled(
                "SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED"
            ),
            depth_capture_enabled=_env_enabled(
                "SCALP_MICRO_REVERSION_DEPTH_CAPTURE_ENABLED"
            ),
            discovery_enabled=_env_enabled("SCALP_MICRO_REVERSION_DISCOVERY_ENABLED"),
        )

    @property
    def observation_capture_active(self) -> bool:
        return self.observer_enabled and self.path_capture_enabled

    @property
    def depth_capture_active(self) -> bool:
        return self.observer_enabled and self.depth_capture_enabled

    def authority_dict(
        self, *, observer_runtime_loaded: bool = False
    ) -> dict[str, Any]:
        return {
            "observer_runtime_loaded": observer_runtime_loaded,
            "observation_capture_active": (
                observer_runtime_loaded and self.observation_capture_active
            ),
            "depth_capture_active": (
                observer_runtime_loaded and self.depth_capture_active
            ),
            "discovery_active": (
                observer_runtime_loaded
                and self.observation_capture_active
                and self.discovery_enabled
            ),
            "observer_runtime_effect": observer_runtime_loaded,
            "trading_runtime_effect": False,
            "trading_decision_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "sim_effect": False,
            "sim_position_effect": False,
            "threshold_effect": False,
            "broker_effect": False,
            **OBSERVER_METRIC_CONTRACT,
        }


@dataclass(frozen=True, slots=True)
class RawMarketObservation:
    symbol: str
    venue: str
    session_bucket: str
    exchange_timestamp: str
    local_receive_timestamp: str
    source_sequence: int
    sequence_epoch: int
    series_sequence: int
    realtime_type: str
    trade_price: float | None = None
    trade_qty: int | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    bid_depth: int | None = None
    ask_depth: int | None = None
    quote_age_ms: float | None = None
    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    schema: str = OBSERVER_ENVELOPE_SCHEMA

    def __post_init__(self) -> None:
        symbol = normalize_symbol(self.symbol)
        venue = normalize_venue(self.venue)
        if not symbol:
            raise ValueError("symbol is required")
        if venue == "UNKNOWN":
            raise ValueError("venue must be explicit")
        if not str(self.session_bucket).strip():
            raise ValueError("session_bucket is required")
        if not str(self.realtime_type).strip():
            raise ValueError("realtime_type is required")
        if self.source_sequence < 0 or self.series_sequence < 0:
            raise ValueError("source and series sequences must not be negative")
        if self.source_sequence != self.series_sequence:
            raise ValueError("source_sequence must equal series_sequence")
        if self.sequence_epoch <= 0:
            raise ValueError("sequence_epoch must be positive")
        _validate_aware_timestamp(self.exchange_timestamp, "exchange_timestamp")
        _validate_aware_timestamp(
            self.local_receive_timestamp, "local_receive_timestamp"
        )
        if (
            _timestamp_delta_ms(self.exchange_timestamp, self.local_receive_timestamp)
            < 0
        ):
            raise ValueError(
                "local_receive_timestamp must not precede exchange_timestamp"
            )
        if self.trade_price is not None and self.trade_price <= 0:
            raise ValueError("trade_price must be positive")
        if self.best_bid is not None and self.best_bid <= 0:
            raise ValueError("best_bid must be positive")
        if self.best_ask is not None and self.best_ask <= 0:
            raise ValueError("best_ask must be positive")
        if (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_ask < self.best_bid
        ):
            raise ValueError("best_ask must not be below best_bid")
        for name in ("trade_qty", "bid_depth", "ask_depth"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.quote_age_ms is not None and self.quote_age_ms < 0:
            raise ValueError("quote_age_ms must not be negative")
        if all(
            value is None for value in (self.trade_price, self.best_bid, self.best_ask)
        ):
            raise ValueError("trade or quote evidence is required")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "aggressor_side", AggressorSide(self.aggressor_side))

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["aggressor_side"] = self.aggressor_side.value
        payload.update(
            {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "trading_runtime_effect": False,
                **OBSERVER_METRIC_CONTRACT,
            }
        )
        return payload


@runtime_checkable
class ObservationSink(Protocol):
    """Minimal dependency exposed to a producer."""

    def put_nowait(self, envelope: RawMarketObservation) -> bool:
        """Accept an envelope without waiting, returning false on capacity loss."""


class BoundedObservationQueue:
    """Bounded sink used between a producer adapter and an observer worker."""

    def __init__(self, *, maxsize: int = 10_000) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self._queue: queue.Queue[RawMarketObservation] = queue.Queue(maxsize=maxsize)

    def put_nowait(self, envelope: RawMarketObservation) -> bool:
        try:
            self._queue.put_nowait(envelope)
        except queue.Full:
            return False
        return True

    def get(self, *, timeout: float | None = None) -> RawMarketObservation:
        return self._queue.get(timeout=timeout)

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()


@dataclass(frozen=True, slots=True)
class ObserverRuntimeSnapshot:
    producer_callback_count: int
    producer_callback_latency_p50_ms: float
    producer_callback_latency_p95_ms: float
    producer_callback_latency_p99_ms: float
    enqueue_latency_p50_ms: float
    enqueue_latency_p95_ms: float
    enqueue_latency_p99_ms: float
    exchange_to_receive_latency_p95_ms: float
    quote_age_p95_ms: float
    queue_high_water: int
    queue_full_count: int
    dropped_envelope_count: int
    invalid_envelope_count: int
    isolated_error_count: int
    observer_runtime_loaded: bool
    observation_capture_active: bool
    trading_decision_effect: bool = False
    actual_order_submitted: bool = False
    broker_order_forbidden: bool = True
    sim_effect: bool = False
    threshold_effect: bool = False


class ObserverRuntimeMetrics:
    """Bounded in-memory observer metrics with no storage side effects."""

    def __init__(self, *, reservoir_size: int = 4_096) -> None:
        if reservoir_size <= 0:
            raise ValueError("reservoir_size must be positive")
        self._lock = threading.Lock()
        self._callback_latency_ms: deque[float] = deque(maxlen=reservoir_size)
        self._enqueue_latency_ms: deque[float] = deque(maxlen=reservoir_size)
        self._exchange_to_receive_latency_ms: deque[float] = deque(
            maxlen=reservoir_size
        )
        self._quote_age_ms: deque[float] = deque(maxlen=reservoir_size)
        self._callback_count = 0
        self._queue_high_water = 0
        self._queue_full = 0
        self._dropped = 0
        self._invalid = 0
        self._isolated_error = 0

    def record(
        self,
        result: AdapterResult,
        *,
        callback_latency_ms: float,
        enqueue_latency_ms: float | None = None,
        queue_depth: int | None = None,
        exchange_to_receive_latency_ms: float | None = None,
        quote_age_ms: float | None = None,
    ) -> None:
        with self._lock:
            self._callback_count += 1
            self._callback_latency_ms.append(max(0.0, callback_latency_ms))
            if enqueue_latency_ms is not None:
                self._enqueue_latency_ms.append(max(0.0, enqueue_latency_ms))
            if exchange_to_receive_latency_ms is not None:
                self._exchange_to_receive_latency_ms.append(
                    max(0.0, exchange_to_receive_latency_ms)
                )
            if quote_age_ms is not None:
                self._quote_age_ms.append(max(0.0, quote_age_ms))
            if queue_depth is not None:
                self._queue_high_water = max(self._queue_high_water, queue_depth)
            if result is AdapterResult.QUEUE_FULL:
                self._queue_full += 1
                self._dropped += 1
            elif result is AdapterResult.INVALID_ENVELOPE:
                self._invalid += 1
                self._dropped += 1
            elif result is AdapterResult.ISOLATED_ERROR:
                self._isolated_error += 1
                self._dropped += 1

    def snapshot(
        self,
        flags: ObserverFeatureFlags,
        *,
        observer_runtime_loaded: bool = False,
    ) -> ObserverRuntimeSnapshot:
        # Keep the producer-facing metrics lock limited to bounded copies.
        # Percentile sorting can take milliseconds once the rolling reservoirs
        # are full and must not stall Kiwoom's realtime callback while the
        # canary monitor builds its periodic health snapshot.
        with self._lock:
            callback = tuple(self._callback_latency_ms)
            enqueue = tuple(self._enqueue_latency_ms)
            exchange_to_receive = tuple(self._exchange_to_receive_latency_ms)
            quote_age = tuple(self._quote_age_ms)
            callback_count = self._callback_count
            queue_high_water = self._queue_high_water
            queue_full_count = self._queue_full
            dropped_envelope_count = self._dropped
            invalid_envelope_count = self._invalid
            isolated_error_count = self._isolated_error
        return ObserverRuntimeSnapshot(
            producer_callback_count=callback_count,
            producer_callback_latency_p50_ms=_percentile(callback, 50),
            producer_callback_latency_p95_ms=_percentile(callback, 95),
            producer_callback_latency_p99_ms=_percentile(callback, 99),
            enqueue_latency_p50_ms=_percentile(enqueue, 50),
            enqueue_latency_p95_ms=_percentile(enqueue, 95),
            enqueue_latency_p99_ms=_percentile(enqueue, 99),
            exchange_to_receive_latency_p95_ms=_percentile(exchange_to_receive, 95),
            quote_age_p95_ms=_percentile(quote_age, 95),
            queue_high_water=queue_high_water,
            queue_full_count=queue_full_count,
            dropped_envelope_count=dropped_envelope_count,
            invalid_envelope_count=invalid_envelope_count,
            isolated_error_count=isolated_error_count,
            observer_runtime_loaded=observer_runtime_loaded,
            observation_capture_active=(
                observer_runtime_loaded and flags.observation_capture_active
            ),
        )


class ObservationAdapter:
    """Minimal, exception-isolated producer adapter."""

    def __init__(
        self,
        sink: ObservationSink,
        *,
        flags: ObserverFeatureFlags | None = None,
        metrics: ObserverRuntimeMetrics | None = None,
        queue_depth: Callable[[], int] | None = None,
    ) -> None:
        self._sink = sink
        self.flags = flags or ObserverFeatureFlags.from_env()
        self.metrics = metrics or ObserverRuntimeMetrics()
        self._queue_depth = queue_depth

    def runtime_snapshot(self) -> ObserverRuntimeSnapshot:
        return self.metrics.snapshot(self.flags, observer_runtime_loaded=True)

    def observe(self, **envelope_fields: Any) -> AdapterResult:
        started_ns = time.perf_counter_ns()
        enqueue_latency_ms: float | None = None
        exchange_to_receive_latency_ms: float | None = None
        quote_age_ms: float | None = None
        result = AdapterResult.DISABLED
        try:
            if not self.flags.observer_enabled:
                return result
            try:
                envelope = RawMarketObservation(**envelope_fields)
            except (TypeError, ValueError):
                result = AdapterResult.INVALID_ENVELOPE
                return result
            exchange_to_receive_latency_ms = _timestamp_delta_ms(
                envelope.exchange_timestamp,
                envelope.local_receive_timestamp,
            )
            quote_age_ms = envelope.quote_age_ms
            enqueue_started_ns = time.perf_counter_ns()
            accepted = self._sink.put_nowait(envelope)
            enqueue_latency_ms = (
                time.perf_counter_ns() - enqueue_started_ns
            ) / 1_000_000.0
            result = AdapterResult.ENQUEUED if accepted else AdapterResult.QUEUE_FULL
            return result
        except Exception:
            result = AdapterResult.ISOLATED_ERROR
            return result
        finally:
            queue_depth = None
            if self._queue_depth is not None:
                try:
                    queue_depth = self._queue_depth()
                except Exception:
                    queue_depth = None
            self.metrics.record(
                result,
                callback_latency_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
                enqueue_latency_ms=enqueue_latency_ms,
                queue_depth=queue_depth,
                exchange_to_receive_latency_ms=exchange_to_receive_latency_ms,
                quote_age_ms=quote_age_ms,
            )


def _validate_aware_timestamp(value: str, field_name: str) -> None:
    from datetime import datetime

    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")


def _timestamp_delta_ms(start: str, end: str) -> float:
    from datetime import datetime

    start_text = start[:-1] + "+00:00" if start.endswith("Z") else start
    end_text = end[:-1] + "+00:00" if end.endswith("Z") else end
    return (
        datetime.fromisoformat(end_text) - datetime.fromisoformat(start_text)
    ).total_seconds() * 1_000.0


def _percentile(values: tuple[float, ...], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile / 100)
    return round(ordered[index], 6)
