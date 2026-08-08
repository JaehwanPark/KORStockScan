"""Canary-only forward collector for existing Kiwoom 0B observations.

The market-data producer calls only :meth:`observe_kiwoom_0b`.  That method
normalizes already parsed fields, applies the manual-control veto through the
minimal observation adapter, and performs one bounded ``put_nowait``.  Pattern
detection, path coalescing, JSON encoding, file writes, and fsync all happen on
observer-owned worker threads.

This module never registers market data, calls a broker, creates a simulated
position, or changes an entry/exit decision.  It is loaded lazily only when the
observer feature flag is enabled.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, time as datetime_time, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .contracts import PriceObservation, normalize_symbol
from .multi_horizon import (
    MULTI_HORIZON_POLICY_VERSION,
    MultiHorizonShockDetector,
)
from .observation_adapter import (
    AdapterResult,
    AggressorSide,
    BoundedObservationQueue,
    ObservationAdapter,
    ObserverFeatureFlags,
    RawMarketObservation,
)
from .path_capture import (
    ParentWavePathCoalescer,
    PathEventReference,
    PreEventRingBuffer,
    append_path_event_references,
)
from .path_journal import (
    MarketPathPoint,
    NonBlockingPathJournalWriter,
    PathStoragePolicy,
    PathWriterMetrics,
)

KST = ZoneInfo("Asia/Seoul")
FORWARD_COLLECTOR_SCHEMA = "scalp_micro_reversion_forward_collector_v2"
FORWARD_COLLECTOR_AUTHORITY = "canary_observation_only_no_trading_authority"
FORWARD_COLLECTOR_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_forward_collector_health",
    "decision_authority": FORWARD_COLLECTOR_AUTHORITY,
    "window_policy": "process_and_trade_date_venue_session_partition",
    "sample_floor": "five_trading_days_and_200_mature_events_gate_b_only",
    "primary_decision_metric": "required_path_fields_coverage_pct",
    "source_quality_gate": (
        "official_0b_trade_time_and_explicit_item_venue_and_manual_control_veto_"
        "and_bounded_nonblocking_transport"
    ),
    "forbidden_uses": (
        "new_market_data_subscription",
        "broker_order_submission",
        "broker_order_cancel",
        "buy_wait_drop_or_entry_exit_decision",
        "simulated_or_real_position_creation",
        "threshold_provider_bot_quantity_or_cap_mutation",
        "p2_policy_selection_before_gate_b",
        "economic_headline_without_verified_tax_and_cost",
    ),
}


class ProducerCanaryResult(StrEnum):
    DISABLED = "disabled"
    UNSUPPORTED_REALTIME_TYPE = "unsupported_realtime_type"
    MISSING_0B_ITEM = "missing_0b_item"
    MISSING_OR_CONFLICTING_VENUE = "missing_or_conflicting_venue"
    INVALID_EXCHANGE_TIMESTAMP = "invalid_exchange_timestamp"
    INVALID_TRADE_SNAPSHOT = "invalid_trade_snapshot"
    ENQUEUED = AdapterResult.ENQUEUED.value
    MANUAL_CONTROL_EXCLUDED = AdapterResult.MANUAL_CONTROL_EXCLUDED.value
    INVALID_ENVELOPE = AdapterResult.INVALID_ENVELOPE.value
    QUEUE_FULL = AdapterResult.QUEUE_FULL.value
    ISOLATED_ERROR = AdapterResult.ISOLATED_ERROR.value


@dataclass(frozen=True, slots=True)
class ForwardCollectorConfig:
    output_root: Path = Path("data/observations/scalp_micro_reversion_forward")
    observation_queue_size: int = 10_000
    path_queue_size: int = 10_000
    path_batch_size: int = 256
    writer_flush_interval_sec: float = 0.25
    worker_poll_interval_sec: float = 0.1
    manual_exclusion_refresh_interval_sec: float = 1.0
    exchange_future_skew_tolerance_ms: int = 1_000
    maximum_exchange_to_receive_lag_ms: int = 10_000
    storage_policy: PathStoragePolicy = field(default_factory=PathStoragePolicy)

    def __post_init__(self) -> None:
        if self.observation_queue_size <= 0 or self.path_queue_size <= 0:
            raise ValueError("collector queue sizes must be positive")
        if self.path_batch_size <= 0:
            raise ValueError("path_batch_size must be positive")
        if self.writer_flush_interval_sec <= 0 or self.worker_poll_interval_sec <= 0:
            raise ValueError("collector intervals must be positive")
        if self.manual_exclusion_refresh_interval_sec <= 0:
            raise ValueError("manual exclusion refresh interval must be positive")
        if self.exchange_future_skew_tolerance_ms < 0:
            raise ValueError("future skew tolerance must not be negative")
        if self.maximum_exchange_to_receive_lag_ms <= 0:
            raise ValueError("maximum exchange lag must be positive")


class CollectorLifecycle(StrEnum):
    NEW = "new"
    RUNNING = "running"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ForwardCollectorSnapshot:
    schema: str
    observer_runtime_loaded: bool
    producer_observation_connected: bool
    observer_runtime_effect: bool
    observation_capture_active: bool
    producer_0b_callback_count: int
    enqueued_count: int
    producer_callback_latency_p50_ms: float
    producer_callback_latency_p95_ms: float
    producer_callback_latency_p99_ms: float
    enqueue_latency_p50_ms: float
    enqueue_latency_p95_ms: float
    enqueue_latency_p99_ms: float
    exchange_to_receive_latency_p95_ms: float
    quote_age_p95_ms: float
    observation_queue_high_water: int
    observation_queue_full_count: int
    observation_dropped_envelope_count: int
    manual_control_excluded_count: int
    adapter_invalid_envelope_count: int
    adapter_isolated_error_count: int
    unsupported_realtime_type_count: int
    missing_0b_item_count: int
    missing_or_conflicting_venue_count: int
    invalid_exchange_timestamp_count: int
    invalid_trade_snapshot_count: int
    future_exchange_timestamp_adjustment_count: int
    stale_exchange_timestamp_block_count: int
    invalid_snapshot_rate: float
    venue_block_rate: float
    timestamp_block_rate: float
    invalid_envelope_rate: float
    quote_age_missing_rate: float
    bbo_complete_rate: float
    raw_exchange_code_9081_observed_count: int
    worker_processed_count: int
    worker_error_count: int
    shock_event_count: int
    path_point_submitted_count: int
    path_point_dropped_count: int
    event_reference_persisted_count: int
    event_reference_error_count: int
    event_reference_write_latency_p95_ms: float
    event_reference_write_latency_p99_ms: float
    event_reference_coverage_pct: float
    orphan_reference_count: int
    unreferenced_segment_count: int
    reference_reconciliation_error_count: int
    reference_reconciliation_completed: bool
    path_accepted_envelope_count: int
    path_duplicate_sequence_count: int
    path_out_of_order_sequence_count: int
    path_sequence_gap_count: int
    series_with_gap_count: int
    queue_drop_explained_gap_count: int
    invalid_envelope_explained_gap_count: int
    other_explained_gap_count: int
    unexplained_sequence_gap_count: int
    path_evicted_envelope_count: int
    path_created_segment_count: int
    path_coalesced_event_reference_count: int
    path_pre_event_point_count: int
    path_active_event_point_count: int
    path_post_event_point_count: int
    writer_count: int
    writer_alive_count: int
    writer_queue_depth: int
    writer_queue_high_water: int
    writer_persisted_envelope_count: int
    writer_queue_full_count: int
    writer_dropped_envelope_count: int
    writer_error_count: int
    writer_restart_count: int
    writer_write_latency_max_ms: float
    writer_flush_latency_max_ms: float
    writer_fsync_latency_max_ms: float
    writer_bytes_written: int
    writer_bytes_per_persisted_envelope: float | None
    writer_bytes_by_trade_date: dict[str, int]
    writer_disk_free_bytes_min: int | None
    writer_capture_degraded_count: int
    writer_last_error_types: tuple[str, ...]
    writer_last_persisted_sequence: int | None
    writer_last_persisted_sequence_by_series: dict[str, dict[str, int]]
    writer_storage_self_disabled_count: int
    collector_lifecycle: str
    sequence_epoch: int
    manual_control_refresh_count: int
    manual_control_new_exclusion_count: int
    manual_control_state_purge_count: int
    manual_control_active_segment_purge_count: int
    manual_control_post_exclusion_envelope_count: int
    manual_control_post_exclusion_event_count: int
    manual_control_event_leak_count: int
    detector_clock_adjustment_count: int
    detector_clock_adjustment_max_ms: int
    p2_real_data_discovery_run: bool = False
    research_policy_selected: bool = False
    selection_authority: bool = False
    sim_position_effect: bool = False
    trading_runtime_effect: bool = False
    trading_decision_effect: bool = False
    threshold_effect: bool = False
    broker_effect: bool = False
    actual_order_submitted: bool = False
    broker_order_forbidden: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), **FORWARD_COLLECTOR_METRIC_CONTRACT}


class ForwardObservationCollector:
    """Fail-isolated 0B intake plus observer-owned detector/path workers."""

    def __init__(
        self,
        *,
        flags: ObserverFeatureFlags,
        config: ForwardCollectorConfig | None = None,
        detector: MultiHorizonShockDetector | None = None,
        manual_excluded_symbols: tuple[str, ...] | None = None,
    ) -> None:
        if not flags.observer_enabled:
            raise ValueError("observer flag must be enabled before collector creation")
        self.flags = flags
        self.config = config or ForwardCollectorConfig()
        self._sink = BoundedObservationQueue(maxsize=self.config.observation_queue_size)
        self._adapter = ObservationAdapter(
            self._sink,
            flags=flags,
            manual_excluded_symbols=manual_excluded_symbols,
            queue_depth=self._sink.qsize,
        )
        self._ring = PreEventRingBuffer()
        self._coalescer = ParentWavePathCoalescer(
            self._ring,
            max_open_segments=self.config.storage_policy.max_open_segments,
        )
        self._detector = detector or MultiHorizonShockDetector()
        self._writers: dict[tuple[str, str, str], NonBlockingPathJournalWriter] = {}
        self._reference_partitions: set[tuple[str, str, str]] = set()
        self._source_sequences: dict[tuple[str, str, str], int] = {}
        self._sequence_epoch = time.time_ns()
        self._series_epochs: dict[tuple[str, str, str], int] = {}
        self._sequence_losses: dict[tuple[int, str, str, str], dict[int, str]] = {}
        self._last_worker_sequence: dict[tuple[int, str, str, str], int] = {}
        self._series_with_gap: set[tuple[int, str, str, str]] = set()
        self._detector_clock_ms: dict[tuple[str, str, str], int] = {}
        self._state_lock = threading.Lock()
        self._manual_refresh_lock = threading.RLock()
        self._metrics_lock = threading.Lock()
        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None
        self._accepting = False
        self._writers_closing = False
        self._lifecycle = CollectorLifecycle.NEW
        self._automatic_manual_refresh = manual_excluded_symbols is None
        self._next_manual_refresh_at = 0.0
        self._producer_0b_callbacks = 0
        self._enqueued = 0
        self._unsupported_types = 0
        self._missing_0b_items = 0
        self._venue_blocks = 0
        self._timestamp_blocks = 0
        self._snapshot_blocks = 0
        self._future_timestamp_adjustments = 0
        self._stale_timestamp_blocks = 0
        self._quote_age_missing = 0
        self._bbo_complete = 0
        self._exchange_9081_observed = 0
        self._worker_processed = 0
        self._worker_errors = 0
        self._shock_events = 0
        self._path_submitted = 0
        self._path_dropped = 0
        self._reference_persisted = 0
        self._reference_errors = 0
        self._reference_write_latency_ms: deque[float] = deque(maxlen=4_096)
        self._reference_coverage_pct = 100.0
        self._orphan_references = 0
        self._unreferenced_segments = 0
        self._reference_reconciliation_errors = 0
        self._reference_reconciliation_completed = False
        self._queue_drop_explained_gaps = 0
        self._invalid_envelope_explained_gaps = 0
        self._other_explained_gaps = 0
        self._unexplained_sequence_gaps = 0
        self._manual_refreshes = 0
        self._manual_new_exclusions = 0
        self._manual_state_purges = 0
        self._manual_segment_purges = 0
        self._manual_post_exclusion_envelopes = 0
        self._manual_post_exclusion_events = 0
        self._manual_event_leaks = 0
        self._detector_clock_adjustments = 0
        self._detector_clock_adjustment_max_ms = 0
        self._producer_callback_latency_ms: deque[float] = deque(maxlen=4_096)

    def start(self) -> None:
        with self._state_lock:
            if self._lifecycle is CollectorLifecycle.RUNNING:
                return
            if self._lifecycle in {
                CollectorLifecycle.CLOSING,
                CollectorLifecycle.CLOSED,
            }:
                raise RuntimeError("forward collector is one-shot and already closed")
            self._stop_requested.clear()
            self._lifecycle = CollectorLifecycle.RUNNING
            self._accepting = True
            self._thread = threading.Thread(
                target=self._run,
                name="micro-reversion-forward-collector",
                daemon=True,
            )
            self._thread.start()

    def close(self, *, timeout_sec: float = 10.0) -> None:
        with self._state_lock:
            if self._lifecycle is CollectorLifecycle.CLOSED:
                return
            thread = self._thread
            self._accepting = False
            self._writers_closing = True
            self._lifecycle = CollectorLifecycle.CLOSING
            self._stop_requested.set()
        close_errors: list[Exception] = []
        if thread is not None:
            thread.join(timeout=max(0.01, timeout_sec))
            if thread.is_alive():
                close_errors.append(
                    TimeoutError("forward collector did not drain in time")
                )
        with self._state_lock:
            writers = tuple(self._writers.values())
        for writer in writers:
            try:
                writer.close(timeout_sec=timeout_sec)
            except Exception as exc:  # collector shutdown must inspect every writer
                close_errors.append(exc)
        try:
            self._reconcile_references_and_paths(shutdown_clean=not close_errors)
        except Exception as exc:
            self._increment("_reference_reconciliation_errors")
            close_errors.append(exc)
        with self._state_lock:
            self._lifecycle = CollectorLifecycle.CLOSED
        if close_errors:
            raise RuntimeError(
                f"forward collector shutdown had {len(close_errors)} error(s)"
            ) from close_errors[0]

    def refresh_manual_exclusions(
        self, symbols: tuple[str, ...] | None = None
    ) -> tuple[str, ...]:
        """Refresh and purge observer state; never called by producer callbacks."""

        with self._manual_refresh_lock:
            added, _removed, _version = self._adapter.refresh_manual_exclusions(symbols)
            self._increment("_manual_refreshes")
            self._apply_new_manual_exclusions(added)
            return tuple(sorted(added))

    def observe_kiwoom_0b(
        self,
        symbol: str,
        snapshot: dict[str, Any],
        *,
        realtime_type: str,
    ) -> ProducerCanaryResult:
        """Normalize one existing 0B snapshot and enqueue without waiting."""

        with self._state_lock:
            accepting = self._accepting
        if not accepting:
            return ProducerCanaryResult.DISABLED
        if str(realtime_type or "").strip() != "0B":
            self._increment("_unsupported_types")
            return ProducerCanaryResult.UNSUPPORTED_REALTIME_TYPE
        self._increment("_producer_0b_callbacks")
        callback_started_ns = time.perf_counter_ns()

        try:
            trade = snapshot.get("last_trade_tick")
            if not isinstance(trade, dict):
                self._increment("_snapshot_blocks")
                return ProducerCanaryResult.INVALID_TRADE_SNAPSHOT
            item = str(
                (snapshot.get("last_realtime_type_item") or {}).get("0B") or ""
            ).strip()
            if not item:
                self._increment("_missing_0b_items")
                return ProducerCanaryResult.MISSING_0B_ITEM
            declared_venue = (
                str(
                    (snapshot.get("last_realtime_type_effective_venue") or {}).get("0B")
                    or ""
                )
                .strip()
                .upper()
            )
            venue = _explicit_item_venue(item)
            if not venue or declared_venue not in {"", venue}:
                self._increment("_venue_blocks")
                return ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE
            exchange_code = str(trade.get("exchange_code_9081") or "").strip()
            if exchange_code:
                self._increment("_exchange_9081_observed")
            received_at_ms = _positive_int(trade.get("received_at_ms"))
            timestamp_result = _exchange_timestamp_from_0b(
                trade.get("exchange_time_raw"),
                received_at_ms=received_at_ms,
                future_skew_tolerance_ms=(
                    self.config.exchange_future_skew_tolerance_ms
                ),
                maximum_lag_ms=self.config.maximum_exchange_to_receive_lag_ms,
            )
            if timestamp_result is None:
                self._increment("_timestamp_blocks")
                return ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
            exchange_timestamp, future_adjusted, stale = timestamp_result
            if stale:
                self._increment("_timestamp_blocks")
                self._increment("_stale_timestamp_blocks")
                return ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
            if future_adjusted:
                self._increment("_future_timestamp_adjustments")
            received_at = datetime.fromtimestamp(received_at_ms / 1_000, tz=KST)
            session_bucket = _session_bucket(venue, exchange_timestamp.timetz())
            normalized_symbol = normalize_symbol(symbol)
            series_key = (normalized_symbol, venue, session_bucket)
            sequence_epoch, series_sequence = self._next_source_sequence(series_key)
            quote_age = _nonnegative_float_or_none(trade.get("quote_age_ms"))
            best_bid = _positive_float_or_none(trade.get("best_bid"))
            best_ask = _positive_float_or_none(trade.get("best_ask"))
            if quote_age is None:
                self._increment("_quote_age_missing")
            if best_bid is not None and best_ask is not None:
                self._increment("_bbo_complete")
            aggressor = str(trade.get("aggressor_side") or "UNKNOWN").upper()
            if aggressor not in {"BUY", "SELL"}:
                aggressor = "UNKNOWN"
            result = self._adapter.observe(
                symbol=symbol,
                venue=venue,
                session_bucket=session_bucket,
                exchange_timestamp=exchange_timestamp.isoformat(),
                local_receive_timestamp=received_at.isoformat(),
                source_sequence=series_sequence,
                sequence_epoch=sequence_epoch,
                series_sequence=series_sequence,
                realtime_type="0B",
                trade_price=_positive_float_or_none(trade.get("price")),
                trade_qty=_nonnegative_int_or_none(trade.get("volume")),
                best_bid=best_bid,
                best_ask=best_ask,
                bid_depth=None,
                ask_depth=None,
                quote_age_ms=quote_age,
                aggressor_side=AggressorSide(aggressor),
            )
            if result is AdapterResult.ENQUEUED:
                self._increment("_enqueued")
            elif result is AdapterResult.MANUAL_CONTROL_EXCLUDED:
                self._discard_manual_exclusion_sequence(series_key, sequence_epoch)
            else:
                self._record_sequence_loss(
                    sequence_epoch,
                    series_key,
                    series_sequence,
                    result,
                )
            return ProducerCanaryResult(result.value)
        except Exception:
            self._increment("_snapshot_blocks")
            return ProducerCanaryResult.ISOLATED_ERROR
        finally:
            self._record_producer_callback_latency(
                (time.perf_counter_ns() - callback_started_ns) / 1_000_000.0
            )

    def runtime_snapshot(self) -> ForwardCollectorSnapshot:
        adapter = self._adapter.runtime_snapshot()
        with self._state_lock:
            thread = self._thread
            writer_items = tuple(self._writers.items())
            connected = self._accepting
            lifecycle = self._lifecycle.value
        writers = tuple(writer for _, writer in writer_items)
        writer_metrics = tuple(writer.metrics() for writer in writers)
        aggregate = _aggregate_writer_metrics(writer_metrics)
        bytes_by_trade_date: dict[str, int] = {}
        for (trade_date, _venue, _session), metrics in zip(
            (key for key, _writer in writer_items), writer_metrics, strict=True
        ):
            bytes_by_trade_date[trade_date] = (
                bytes_by_trade_date.get(trade_date, 0) + metrics.bytes_written
            )
        path_quality = self._coalescer.quality_snapshot()
        with self._metrics_lock:
            callback_latency = tuple(self._producer_callback_latency_ms)
            reference_latency = tuple(self._reference_write_latency_ms)
            return ForwardCollectorSnapshot(
                schema=FORWARD_COLLECTOR_SCHEMA,
                observer_runtime_loaded=True,
                producer_observation_connected=connected,
                observer_runtime_effect=bool(thread is not None and thread.is_alive()),
                observation_capture_active=(
                    bool(thread is not None and thread.is_alive())
                    and self.flags.observation_capture_active
                ),
                producer_0b_callback_count=self._producer_0b_callbacks,
                enqueued_count=self._enqueued,
                producer_callback_latency_p50_ms=(_percentile(callback_latency, 50)),
                producer_callback_latency_p95_ms=(_percentile(callback_latency, 95)),
                producer_callback_latency_p99_ms=(_percentile(callback_latency, 99)),
                enqueue_latency_p50_ms=adapter.enqueue_latency_p50_ms,
                enqueue_latency_p95_ms=adapter.enqueue_latency_p95_ms,
                enqueue_latency_p99_ms=adapter.enqueue_latency_p99_ms,
                exchange_to_receive_latency_p95_ms=(
                    adapter.exchange_to_receive_latency_p95_ms
                ),
                quote_age_p95_ms=adapter.quote_age_p95_ms,
                observation_queue_high_water=adapter.queue_high_water,
                observation_queue_full_count=adapter.queue_full_count,
                observation_dropped_envelope_count=(adapter.dropped_envelope_count),
                manual_control_excluded_count=(adapter.manual_control_excluded_count),
                adapter_invalid_envelope_count=adapter.invalid_envelope_count,
                adapter_isolated_error_count=adapter.isolated_error_count,
                unsupported_realtime_type_count=self._unsupported_types,
                missing_0b_item_count=self._missing_0b_items,
                missing_or_conflicting_venue_count=self._venue_blocks,
                invalid_exchange_timestamp_count=self._timestamp_blocks,
                invalid_trade_snapshot_count=self._snapshot_blocks,
                future_exchange_timestamp_adjustment_count=(
                    self._future_timestamp_adjustments
                ),
                stale_exchange_timestamp_block_count=self._stale_timestamp_blocks,
                invalid_snapshot_rate=_rate(
                    self._snapshot_blocks, self._producer_0b_callbacks
                ),
                venue_block_rate=_rate(self._venue_blocks, self._producer_0b_callbacks),
                timestamp_block_rate=_rate(
                    self._timestamp_blocks, self._producer_0b_callbacks
                ),
                invalid_envelope_rate=_rate(
                    adapter.invalid_envelope_count, self._producer_0b_callbacks
                ),
                quote_age_missing_rate=_rate(
                    self._quote_age_missing, self._producer_0b_callbacks
                ),
                bbo_complete_rate=_rate(
                    self._bbo_complete, self._producer_0b_callbacks
                ),
                raw_exchange_code_9081_observed_count=(self._exchange_9081_observed),
                worker_processed_count=self._worker_processed,
                worker_error_count=self._worker_errors,
                shock_event_count=self._shock_events,
                path_point_submitted_count=self._path_submitted,
                path_point_dropped_count=self._path_dropped,
                event_reference_persisted_count=self._reference_persisted,
                event_reference_error_count=self._reference_errors,
                event_reference_write_latency_p95_ms=_percentile(reference_latency, 95),
                event_reference_write_latency_p99_ms=_percentile(reference_latency, 99),
                event_reference_coverage_pct=self._reference_coverage_pct,
                orphan_reference_count=self._orphan_references,
                unreferenced_segment_count=self._unreferenced_segments,
                reference_reconciliation_error_count=(
                    self._reference_reconciliation_errors
                ),
                reference_reconciliation_completed=(
                    self._reference_reconciliation_completed
                ),
                path_accepted_envelope_count=(path_quality.accepted_envelope_count),
                path_duplicate_sequence_count=(path_quality.duplicate_sequence_count),
                path_out_of_order_sequence_count=(
                    path_quality.out_of_order_sequence_count
                ),
                path_sequence_gap_count=path_quality.sequence_gap_count,
                series_with_gap_count=len(self._series_with_gap),
                queue_drop_explained_gap_count=self._queue_drop_explained_gaps,
                invalid_envelope_explained_gap_count=(
                    self._invalid_envelope_explained_gaps
                ),
                other_explained_gap_count=self._other_explained_gaps,
                unexplained_sequence_gap_count=self._unexplained_sequence_gaps,
                path_evicted_envelope_count=path_quality.evicted_envelope_count,
                path_created_segment_count=path_quality.created_segment_count,
                path_coalesced_event_reference_count=(
                    path_quality.coalesced_event_reference_count
                ),
                path_pre_event_point_count=path_quality.pre_event_point_count,
                path_active_event_point_count=(path_quality.active_event_point_count),
                path_post_event_point_count=path_quality.post_event_point_count,
                writer_count=len(writer_metrics),
                writer_alive_count=sum(
                    1 for metric in writer_metrics if metric.writer_alive
                ),
                writer_queue_depth=aggregate["queue_depth"],
                writer_queue_high_water=aggregate["queue_high_water"],
                writer_persisted_envelope_count=aggregate["persisted"],
                writer_queue_full_count=aggregate["queue_full"],
                writer_dropped_envelope_count=aggregate["dropped"],
                writer_error_count=aggregate["errors"],
                writer_restart_count=aggregate["restarts"],
                writer_write_latency_max_ms=aggregate["write_latency_max"],
                writer_flush_latency_max_ms=aggregate["flush_latency_max"],
                writer_fsync_latency_max_ms=aggregate["fsync_latency_max"],
                writer_bytes_written=aggregate["bytes_written"],
                writer_bytes_per_persisted_envelope=(
                    None
                    if aggregate["persisted"] == 0
                    else round(aggregate["bytes_written"] / aggregate["persisted"], 6)
                ),
                writer_bytes_by_trade_date=dict(sorted(bytes_by_trade_date.items())),
                writer_disk_free_bytes_min=aggregate["disk_free_min"],
                writer_capture_degraded_count=aggregate["capture_degraded"],
                writer_last_error_types=aggregate["last_error_types"],
                writer_last_persisted_sequence=aggregate["last_sequence"],
                writer_last_persisted_sequence_by_series=aggregate[
                    "last_sequence_by_series"
                ],
                writer_storage_self_disabled_count=aggregate["self_disabled"],
                collector_lifecycle=lifecycle,
                sequence_epoch=self._sequence_epoch,
                manual_control_refresh_count=self._manual_refreshes,
                manual_control_new_exclusion_count=self._manual_new_exclusions,
                manual_control_state_purge_count=self._manual_state_purges,
                manual_control_active_segment_purge_count=(self._manual_segment_purges),
                manual_control_post_exclusion_envelope_count=(
                    self._manual_post_exclusion_envelopes
                ),
                manual_control_post_exclusion_event_count=(
                    self._manual_post_exclusion_events
                ),
                manual_control_event_leak_count=self._manual_event_leaks,
                detector_clock_adjustment_count=(self._detector_clock_adjustments),
                detector_clock_adjustment_max_ms=(
                    self._detector_clock_adjustment_max_ms
                ),
            )

    def _next_source_sequence(
        self, series_key: tuple[str, str, str]
    ) -> tuple[int, int]:
        with self._state_lock:
            previous = self._source_sequences.get(series_key, 0)
            sequence = previous + 1
            self._source_sequences[series_key] = sequence
            epoch = self._series_epochs.setdefault(series_key, self._sequence_epoch)
            return epoch, sequence

    def _run(self) -> None:
        while not self._stop_requested.is_set() or self._sink.qsize() > 0:
            self._refresh_manual_exclusions_if_due()
            try:
                envelope = self._sink.get(timeout=self.config.worker_poll_interval_sec)
            except queue.Empty:
                continue
            try:
                self._process_envelope(envelope)
            except Exception:
                self._increment("_worker_errors")
            finally:
                self._sink.task_done()

    def _process_envelope(self, envelope: RawMarketObservation) -> None:
        with self._manual_refresh_lock:
            if self._adapter.is_manual_excluded(envelope.symbol):
                self._increment("_manual_post_exclusion_envelopes")
                return
            self._account_for_sequence_gap(envelope)
            self._process_allowed_envelope(envelope)

    def _process_allowed_envelope(self, envelope: RawMarketObservation) -> None:
        if not self.flags.path_capture_enabled:
            self._ring.add(envelope)
            self._increment("_worker_processed")
            return
        receive_ms = _iso_timestamp_ms(envelope.local_receive_timestamp)
        series_key = (envelope.symbol, envelope.venue, envelope.session_bucket)
        with self._state_lock:
            previous_clock = self._detector_clock_ms.get(series_key, 0)
            detector_clock_ms = max(receive_ms, previous_clock + 1)
            self._detector_clock_ms[series_key] = detector_clock_ms
        adjustment_ms = detector_clock_ms - receive_ms
        if adjustment_ms > 0:
            with self._metrics_lock:
                self._detector_clock_adjustments += 1
                self._detector_clock_adjustment_max_ms = max(
                    self._detector_clock_adjustment_max_ms,
                    adjustment_ms,
                )
        price_observation = _to_price_observation(
            envelope, observed_at_ms=detector_clock_ms
        )
        events = self._detector.process(price_observation)
        registrations = []
        for event in events:
            registration = self._coalescer.register_event(event)
            registrations.append(registration)
            pre_event_points = self._coalescer.points_from_registration(
                registration,
                detector_version=MULTI_HORIZON_POLICY_VERSION,
            )
            self._submit_points(envelope, pre_event_points)
            self._append_reference(envelope, registration.event_reference)
        self._ring.add(envelope)
        for parent_wave_id, state in self._coalescer.active_segments_for(envelope):
            point = self._coalescer.point_for_active_envelope(
                envelope,
                parent_wave_id=parent_wave_id,
                state=state,
                detector_version=MULTI_HORIZON_POLICY_VERSION,
            )
            self._submit_points(envelope, (point,))
        self._increment("_worker_processed")
        if registrations:
            self._add("_shock_events", len(registrations))

    def _refresh_manual_exclusions_if_due(self) -> None:
        if not self._automatic_manual_refresh:
            return
        now = time.monotonic()
        if now < self._next_manual_refresh_at:
            return
        self._next_manual_refresh_at = (
            now + self.config.manual_exclusion_refresh_interval_sec
        )
        try:
            self.refresh_manual_exclusions()
        except Exception:
            self._increment("_worker_errors")

    def _apply_new_manual_exclusions(self, symbols: frozenset[str]) -> None:
        for symbol in symbols:
            ring_rows = self._ring.drop_symbol(symbol)
            detector_states = self._detector.drop_symbol(symbol)
            segments = self._coalescer.drop_symbol(symbol)
            with self._state_lock:
                keys = [key for key in self._source_sequences if key[0] == symbol]
                for key in keys:
                    self._source_sequences.pop(key, None)
                    self._detector_clock_ms.pop(key, None)
                    self._series_epochs[key] = time.time_ns()
                sequence_keys = [
                    key for key in self._sequence_losses if key[1] == symbol
                ]
                for key in sequence_keys:
                    self._sequence_losses.pop(key, None)
                    self._last_worker_sequence.pop(key, None)
            with self._metrics_lock:
                for key in sequence_keys:
                    self._series_with_gap.discard(key)
            self._increment("_manual_new_exclusions")
            self._add(
                "_manual_state_purges",
                ring_rows + detector_states + len(keys),
            )
            self._add("_manual_segment_purges", segments)

    def _record_sequence_loss(
        self,
        epoch: int,
        series_key: tuple[str, str, str],
        sequence: int,
        result: AdapterResult,
    ) -> None:
        reason = {
            AdapterResult.QUEUE_FULL: "queue_full",
            AdapterResult.INVALID_ENVELOPE: "invalid_envelope",
        }.get(result, "other")
        key = (epoch, *series_key)
        with self._state_lock:
            losses = self._sequence_losses.setdefault(key, {})
            losses[sequence] = reason
            if len(losses) > self.config.observation_queue_size:
                del losses[min(losses)]

    def _discard_manual_exclusion_sequence(
        self,
        series_key: tuple[str, str, str],
        epoch: int,
    ) -> None:
        tracking_key = (epoch, *series_key)
        with self._state_lock:
            self._source_sequences.pop(series_key, None)
            self._detector_clock_ms.pop(series_key, None)
            self._series_epochs[series_key] = time.time_ns()
            self._sequence_losses.pop(tracking_key, None)
            self._last_worker_sequence.pop(tracking_key, None)
        with self._metrics_lock:
            self._series_with_gap.discard(tracking_key)

    def _account_for_sequence_gap(self, envelope: RawMarketObservation) -> None:
        key = (
            envelope.sequence_epoch,
            envelope.symbol,
            envelope.venue,
            envelope.session_bucket,
        )
        with self._state_lock:
            previous = self._last_worker_sequence.get(key, 0)
            current = envelope.series_sequence
            if current <= previous:
                return
            gap_count = current - previous - 1
            losses = self._sequence_losses.setdefault(key, {})
            reasons = [
                reason
                for sequence, reason in losses.items()
                if previous < sequence < current
            ]
            self._last_worker_sequence[key] = current
            stale_sequences = [sequence for sequence in losses if sequence <= current]
            for sequence in stale_sequences:
                losses.pop(sequence, None)
        if gap_count <= 0:
            return
        with self._metrics_lock:
            self._series_with_gap.add(key)
            self._queue_drop_explained_gaps += reasons.count("queue_full")
            self._invalid_envelope_explained_gaps += reasons.count("invalid_envelope")
            self._other_explained_gaps += reasons.count("other")
            self._unexplained_sequence_gaps += gap_count - len(reasons)

    def _reconcile_references_and_paths(self, *, shutdown_clean: bool) -> None:
        if not shutdown_clean:
            self._increment("_reference_reconciliation_errors")
            return
        with self._state_lock:
            partitions = tuple(set(self._writers) | self._reference_partitions)
        total_references = 0
        covered_references = 0
        orphan_references = 0
        unreferenced_segments = 0
        errors = 0
        for trade_date, venue, session_bucket in partitions:
            path = self.config.storage_policy.partition_path(
                self.config.output_root,
                trade_date=trade_date,
                venue=venue,
                session_bucket=session_bucket,
            )
            try:
                path_segments = _jsonl_values(path, "path_segment_id")
                references = _jsonl_value_rows(
                    path.with_name("event_references.jsonl"),
                    "path_segment_id",
                )
            except (OSError, ValueError, json.JSONDecodeError):
                errors += 1
                continue
            reference_segments = {value for value in references if value}
            total_references += len(references)
            covered = sum(1 for value in references if value in path_segments)
            covered_references += covered
            orphan_references += len(references) - covered
            unreferenced_segments += len(path_segments - reference_segments)
        with self._metrics_lock:
            self._reference_coverage_pct = (
                100.0
                if total_references == 0
                else round(100.0 * covered_references / total_references, 6)
            )
            self._orphan_references = orphan_references
            self._unreferenced_segments = unreferenced_segments
            self._reference_reconciliation_errors += errors
            self._reference_reconciliation_completed = errors == 0

    def _submit_points(
        self,
        envelope: RawMarketObservation,
        points: tuple[MarketPathPoint, ...],
    ) -> None:
        if not points:
            return
        writer = self._writer_for(envelope)
        for point in points:
            if writer.submit(point):
                self._increment("_path_submitted")
            else:
                self._increment("_path_dropped")

    def _writer_for(
        self, envelope: RawMarketObservation
    ) -> NonBlockingPathJournalWriter:
        trade_date = (
            datetime.fromisoformat(envelope.exchange_timestamp).date().isoformat()
        )
        key = (trade_date, envelope.venue, envelope.session_bucket)
        with self._state_lock:
            writer = self._writers.get(key)
            if writer is not None:
                return writer
            if self._writers_closing:
                raise RuntimeError("path writer creation blocked during shutdown")
            path = self.config.storage_policy.partition_path(
                self.config.output_root,
                trade_date=trade_date,
                venue=envelope.venue,
                session_bucket=envelope.session_bucket,
            )
            writer = NonBlockingPathJournalWriter(
                path,
                max_queue_size=self.config.path_queue_size,
                max_batch_size=self.config.path_batch_size,
                flush_interval_sec=self.config.writer_flush_interval_sec,
                storage_policy=self.config.storage_policy,
            )
            writer.start()
            self._writers[key] = writer
            return writer

    def _append_reference(
        self, envelope: RawMarketObservation, reference: PathEventReference
    ) -> None:
        started_ns = time.perf_counter_ns()
        trade_date = (
            datetime.fromisoformat(envelope.exchange_timestamp).date().isoformat()
        )
        path = self.config.storage_policy.partition_path(
            self.config.output_root,
            trade_date=trade_date,
            venue=envelope.venue,
            session_bucket=envelope.session_bucket,
        ).with_name("event_references.jsonl")
        with self._state_lock:
            self._reference_partitions.add(
                (trade_date, envelope.venue, envelope.session_bucket)
            )
        try:
            append_path_event_references(path, (reference,))
        except Exception:
            self._increment("_reference_errors")
        else:
            self._increment("_reference_persisted")
        finally:
            with self._metrics_lock:
                self._reference_write_latency_ms.append(
                    (time.perf_counter_ns() - started_ns) / 1_000_000.0
                )

    def _increment(self, attribute: str) -> None:
        self._add(attribute, 1)

    def _record_producer_callback_latency(self, value: float) -> None:
        with self._metrics_lock:
            self._producer_callback_latency_ms.append(max(0.0, float(value)))

    def _add(self, attribute: str, value: int) -> None:
        with self._metrics_lock:
            setattr(self, attribute, int(getattr(self, attribute)) + int(value))


def build_forward_collector_from_env(
    *,
    start: bool = True,
) -> ForwardObservationCollector | None:
    """Return no object and import no producer dependency when default OFF."""

    flags = ObserverFeatureFlags.from_env()
    if not flags.observer_enabled:
        return None
    output_root = Path(
        os.getenv(
            "SCALP_MICRO_REVERSION_PATH_ROOT",
            "data/observations/scalp_micro_reversion_forward",
        )
    )
    config = ForwardCollectorConfig(
        output_root=output_root,
        observation_queue_size=_bounded_env_int(
            "SCALP_MICRO_REVERSION_OBSERVATION_QUEUE_SIZE", 10_000, 1, 200_000
        ),
        path_queue_size=_bounded_env_int(
            "SCALP_MICRO_REVERSION_PATH_QUEUE_SIZE", 10_000, 1, 200_000
        ),
        path_batch_size=_bounded_env_int(
            "SCALP_MICRO_REVERSION_PATH_BATCH_SIZE", 256, 1, 10_000
        ),
    )
    collector = ForwardObservationCollector(flags=flags, config=config)
    if start:
        collector.start()
    return collector


def _explicit_item_venue(item: str) -> str:
    raw = str(item or "").strip().upper()
    if raw.endswith("_AL"):
        return ""
    if raw.endswith("_NX"):
        return "NXT"
    return "KRX" if raw else ""


def _exchange_timestamp_from_0b(
    value: object,
    *,
    received_at_ms: int,
    future_skew_tolerance_ms: int = 1_000,
    maximum_lag_ms: int = 10_000,
) -> tuple[datetime, bool, bool] | None:
    text = str(value or "").strip().replace(":", "")
    if received_at_ms <= 0 or len(text) not in {6, 9} or not text.isdigit():
        return None
    received = datetime.fromtimestamp(received_at_ms / 1_000, tz=KST)
    try:
        observed = received.replace(
            hour=int(text[0:2]),
            minute=int(text[2:4]),
            second=int(text[4:6]),
            microsecond=(int(text[6:9]) * 1_000 if len(text) == 9 else 0),
        )
    except ValueError:
        return None
    delta_sec = (observed - received).total_seconds()
    if delta_sec > 12 * 60 * 60:
        observed -= timedelta(days=1)
    elif delta_sec < -12 * 60 * 60:
        observed += timedelta(days=1)
    lag_ms = (received - observed).total_seconds() * 1_000.0
    if lag_ms < -future_skew_tolerance_ms:
        return None
    future_adjusted = lag_ms < 0
    if future_adjusted:
        observed = received
        lag_ms = 0
    return observed, future_adjusted, lag_ms > maximum_lag_ms


def _session_bucket(venue: str, clock: datetime_time) -> str:
    local_clock = clock.replace(tzinfo=None)
    if venue == "NXT":
        if local_clock < datetime_time(9, 0):
            return "NXT_PREMARKET"
        if local_clock < datetime_time(15, 30):
            return "NXT_REGULAR_OVERLAP"
        return "NXT_AFTERMARKET"
    if local_clock < datetime_time(9, 0):
        return "KRX_PREMARKET"
    if local_clock < datetime_time(15, 30):
        return "KRX_REGULAR"
    return "KRX_AFTERMARKET"


def _to_price_observation(
    envelope: RawMarketObservation, *, observed_at_ms: int
) -> PriceObservation:
    if envelope.trade_price is None:
        raise ValueError("0B forward detector requires trade price")
    return PriceObservation(
        symbol=envelope.symbol,
        observed_at_ms=observed_at_ms,
        price=envelope.trade_price,
        trade_date=datetime.fromisoformat(envelope.exchange_timestamp)
        .date()
        .isoformat(),
        venue=envelope.venue,
        session_bucket=envelope.session_bucket,
        source_event_id=(
            "kiwoom_0b_local_receive_sequence:"
            f"{envelope.sequence_epoch}:{envelope.series_sequence}"
        ),
        price_source_field="official_0b_fid10",
        best_bid=envelope.best_bid,
        best_ask=envelope.best_ask,
        quote_age_ms=envelope.quote_age_ms,
        source_quality_status="forward_0b_local_receive_ordered",
        instrument_metadata_source="missing_forward_symbol_master",
        instrument_metadata_verified=False,
        manual_control_exclusion_checked=True,
    )


def _aggregate_writer_metrics(
    rows: tuple[PathWriterMetrics, ...],
) -> dict[str, Any]:
    sequences = [
        row.last_persisted_sequence
        for row in rows
        if row.last_persisted_sequence is not None
    ]
    disk_free = [row.disk_free_bytes for row in rows if row.disk_free_bytes is not None]
    last_sequence_by_series: dict[str, dict[str, int]] = {}
    for row in rows:
        for key, value in row.last_persisted_sequence_by_series.items():
            current = last_sequence_by_series.get(key)
            if current is None or (
                value["sequence_epoch"],
                value["series_sequence"],
            ) > (
                current["sequence_epoch"],
                current["series_sequence"],
            ):
                last_sequence_by_series[key] = dict(value)
    return {
        "queue_depth": sum(row.journal_queue_depth for row in rows),
        "queue_high_water": sum(row.queue_high_water for row in rows),
        "persisted": sum(row.persisted_envelope_count for row in rows),
        "queue_full": sum(row.journal_queue_full_count for row in rows),
        "dropped": sum(row.journal_dropped_envelopes for row in rows),
        "errors": sum(row.journal_writer_error_count for row in rows),
        "restarts": sum(row.journal_writer_restart_count for row in rows),
        "write_latency_max": max(
            (row.journal_write_latency_ms for row in rows), default=0.0
        ),
        "flush_latency_max": max(
            (row.journal_flush_latency_ms for row in rows), default=0.0
        ),
        "fsync_latency_max": max(
            (row.journal_fsync_latency_ms for row in rows), default=0.0
        ),
        "bytes_written": sum(row.bytes_written for row in rows),
        "disk_free_min": min(disk_free) if disk_free else None,
        "capture_degraded": sum(1 for row in rows if row.capture_degraded),
        "last_error_types": tuple(
            sorted(
                {
                    row.last_writer_error_type
                    for row in rows
                    if row.last_writer_error_type
                }
            )
        ),
        "last_sequence": max(sequences) if sequences else None,
        "last_sequence_by_series": dict(sorted(last_sequence_by_series.items())),
        "self_disabled": sum(1 for row in rows if row.storage_self_disabled),
    }


def _bounded_env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def _positive_int(value: object) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _positive_float_or_none(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _nonnegative_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _nonnegative_float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _iso_timestamp_ms(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp() * 1_000)


def _percentile(values: tuple[float, ...], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile / 100)
    return round(ordered[index], 6)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(100.0 * numerator / denominator, 6)


def _jsonl_values(path: Path, field_name: str) -> set[str]:
    return set(_jsonl_value_rows(path, field_name))


def _jsonl_value_rows(path: Path, field_name: str) -> list[str]:
    if not path.exists():
        return []
    values: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            values.append(str(payload.get(field_name) or "").strip())
    return values
