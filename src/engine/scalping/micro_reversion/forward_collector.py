"""Canary-only forward collector for existing Kiwoom 0B/0D observations.

The market-data producer calls :meth:`observe_kiwoom_0b` for the canonical trade
stream and :meth:`observe_kiwoom_0d` for a separate depth stream. Both callbacks
perform one bounded ``put_nowait``. Pattern detection, JSON encoding, file writes,
and fsync all happen on observer-owned worker threads.

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
from bisect import bisect_left, bisect_right
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, time as datetime_time, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .contracts import PriceObservation, normalize_symbol, registration_item_identity
from .multi_horizon import MultiHorizonShockDetector
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
    PathEnvelopeOrderStatus,
    PathEventReference,
    PreEventRingBuffer,
    append_path_event_references,
    to_market_stream_point,
)
from .path_journal import (
    MarketPathPoint,
    MarketDepthPoint,
    MarketStreamPoint,
    NonBlockingPathJournalWriter,
    PathStoragePolicy,
    PathWriterMetrics,
    partition_path_files,
    validate_market_stream_path_provenance,
)

KST = ZoneInfo("Asia/Seoul")
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_ROOT = (
    REPOSITORY_ROOT / "data/observations/scalp_micro_reversion_forward"
)
FORWARD_COLLECTOR_SCHEMA = "scalp_micro_reversion_forward_collector_v9"
FORWARD_COLLECTOR_AUTHORITY = "canary_observation_only_no_trading_authority"
PRODUCER_CALLBACK_LATENCY_SCOPE = "kiwoom_0b_trade_callback_only"
FORWARD_COLLECTOR_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_forward_collector_health",
    "decision_authority": FORWARD_COLLECTOR_AUTHORITY,
    "window_policy": "process_and_trade_date_venue_session_partition",
    "sample_floor": "five_trading_days_and_200_mature_events_gate_b_only",
    "primary_decision_metric": "required_path_fields_coverage_pct",
    "source_quality_gate": (
        "official_0b_trade_time_and_explicit_item_venue_and_monotonic_"
        "source_sequence_and_local_receive_time_with_bounded_raw_only_"
        "exchange_timestamp_regression_quarantine"
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
CROSSED_BBO_SANITIZATION_METRIC_CONTRACT = {
    "metric_role": "source_quality_diagnostic",
    "decision_authority": "observation_input_sanitization_only",
    "window_policy": "current_process_cumulative",
    "sample_floor": "not_applicable_per_observation_contract",
    "primary_decision_metric": "crossed_bbo_sanitized_rate",
    "source_quality_gate": (
        "positive_trade_evidence_retained_with_crossed_optional_bbo_removed"
    ),
    "forbidden_uses": (
        "entry_or_exit_decision",
        "touch_or_fill_inference",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
        "gate_b_quote_coverage_imputation",
    ),
}
EXCHANGE_TIMESTAMP_REGRESSION_METRIC_CONTRACT = {
    "metric_role": "source_quality_quarantine",
    "decision_authority": "observer_path_row_quarantine_only",
    "window_policy": "current_process_cumulative_per_symbol_venue_session",
    "sample_floor": "not_applicable_per_observation_contract",
    "primary_decision_metric": "path_exchange_timestamp_regression_exceeded_count",
    "source_quality_gate": (
        "monotonic_source_sequence_and_local_receive_time_with_at_most_"
        "one_second_exchange_timestamp_regression_quarantined"
    ),
    "forbidden_uses": (
        "exchange_timestamp_imputation_or_reordering",
        "detector_or_path_consumption_of_quarantined_row",
        "gate_b_coverage_imputation",
        "sim_or_live_policy_selection",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}
EXCHANGE_TIMESTAMP_REGRESSION_CANARY_METRIC_CONTRACT = {
    "metric_role": "source_quality_incident_and_raw_row_exclusion",
    "decision_authority": "observer_row_quarantine_only",
    "window_policy": "current_process_cumulative_per_symbol_venue_session",
    "sample_floor": "not_applicable_each_affected_row_is_excluded",
    "primary_decision_metric": "path_exchange_timestamp_regression_exceeded_count",
    "source_quality_gate": (
        "affected_rows_remain_path_consumer_ineligible_and_are_skipped_by_"
        "p2_reconstruction_without_imputation"
    ),
    "forbidden_uses": (
        "detector_or_path_consumption_of_quarantined_row",
        "p2_policy_ranking_before_gate_b",
        "sim_or_live_policy_selection",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}
DEPTH_CALLBACK_LATENCY_METRIC_CONTRACT = {
    "metric_role": "source_quality_diagnostic",
    "decision_authority": "observer_performance_diagnostic_only",
    "window_policy": "current_process_rolling_last_4096_kiwoom_0d_callbacks",
    "sample_floor": "diagnostic_only_no_frozen_stop_limit",
    "primary_decision_metric": "producer_0d_callback_latency_p99_ms",
    "source_quality_gate": (
        "separate_from_frozen_0b_callback_canary_and_interpreted_with_depth_"
        "queue_drop_worker_and_writer_health"
    ),
    "forbidden_uses": (
        "satisfy_or_bypass_0b_callback_latency_canary",
        "sim_or_live_policy_selection",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}
LOW_DISK_CAPACITY_WARNING_METRIC_CONTRACT = {
    "metric_role": "operational_capacity_warning",
    "decision_authority": "storage_maintenance_attention_only",
    "window_policy": "current_process_cumulative_successful_writer_batches",
    "sample_floor": "one_successful_write_below_low_disk_watermark",
    "primary_decision_metric": (
        "writer_and_depth_writer_low_disk_watermark_breach_count"
    ),
    "source_quality_gate": (
        "warning_does_not_imply_row_loss_and_actual_drop_error_self_disable_"
        "manifest_or_projection_failure_remains_capture_degraded"
    ),
    "forbidden_uses": (
        "whole_date_source_quality_stop_without_capture_loss",
        "sim_or_live_policy_selection",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}


class ProducerCanaryResult(StrEnum):
    DISABLED = "disabled"
    UNSUPPORTED_REALTIME_TYPE = "unsupported_realtime_type"
    MISSING_0B_ITEM = "missing_0b_item"
    MISSING_0D_ITEM = "missing_0d_item"
    MISSING_OR_CONFLICTING_VENUE = "missing_or_conflicting_venue"
    INVALID_EXCHANGE_TIMESTAMP = "invalid_exchange_timestamp"
    INVALID_TRADE_SNAPSHOT = "invalid_trade_snapshot"
    INVALID_DEPTH_SNAPSHOT = "invalid_depth_snapshot"
    ENQUEUED = AdapterResult.ENQUEUED.value
    INVALID_ENVELOPE = AdapterResult.INVALID_ENVELOPE.value
    QUEUE_FULL = AdapterResult.QUEUE_FULL.value
    ISOLATED_ERROR = AdapterResult.ISOLATED_ERROR.value


@dataclass(frozen=True, slots=True)
class ForwardCollectorConfig:
    output_root: Path = DEFAULT_OUTPUT_ROOT
    observation_queue_size: int = 50_000
    path_queue_size: int = 10_000
    depth_queue_size: int = 50_000
    path_batch_size: int = 256
    writer_flush_interval_sec: float = 0.25
    worker_poll_interval_sec: float = 0.1
    exchange_future_skew_tolerance_ms: int = 1_000
    maximum_exchange_to_receive_lag_ms: int = 10_000
    exchange_timestamp_regression_tolerance_ms: int = 1_000
    storage_policy: PathStoragePolicy = field(default_factory=PathStoragePolicy)

    def __post_init__(self) -> None:
        if (
            self.observation_queue_size <= 0
            or self.path_queue_size <= 0
            or self.depth_queue_size <= 0
        ):
            raise ValueError("collector queue sizes must be positive")
        if self.path_batch_size <= 0:
            raise ValueError("path_batch_size must be positive")
        if self.writer_flush_interval_sec <= 0 or self.worker_poll_interval_sec <= 0:
            raise ValueError("collector intervals must be positive")
        if self.exchange_future_skew_tolerance_ms < 0:
            raise ValueError("future skew tolerance must not be negative")
        if self.maximum_exchange_to_receive_lag_ms <= 0:
            raise ValueError("maximum exchange lag must be positive")
        if not 0 <= self.exchange_timestamp_regression_tolerance_ms <= 1_000:
            raise ValueError(
                "exchange timestamp regression tolerance must be between 0 and 1s"
            )


class CollectorLifecycle(StrEnum):
    NEW = "new"
    RUNNING = "running"
    CLOSING = "closing"
    CLOSE_FAILED = "close_failed"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ForwardCollectorSnapshot:
    schema: str
    observer_runtime_loaded: bool
    producer_observation_connected: bool
    observer_runtime_effect: bool
    observation_capture_active: bool
    depth_capture_requested: bool
    depth_capture_active: bool
    producer_0b_callback_count: int
    producer_0d_callback_count: int
    enqueued_count: int
    depth_enqueued_count: int
    producer_callback_latency_scope: str
    producer_callback_latency_p50_ms: float
    producer_callback_latency_p95_ms: float
    producer_callback_latency_p99_ms: float
    producer_0d_callback_latency_p50_ms: float
    producer_0d_callback_latency_p95_ms: float
    producer_0d_callback_latency_p99_ms: float
    enqueue_latency_p50_ms: float
    enqueue_latency_p95_ms: float
    enqueue_latency_p99_ms: float
    exchange_to_receive_latency_p95_ms: float
    quote_age_p95_ms: float
    observation_queue_high_water: int
    observation_queue_full_count: int
    observation_dropped_envelope_count: int
    adapter_invalid_envelope_count: int
    adapter_isolated_error_count: int
    unsupported_realtime_type_count: int
    missing_0b_item_count: int
    missing_0d_item_count: int
    missing_or_conflicting_venue_count: int
    invalid_exchange_timestamp_count: int
    invalid_trade_snapshot_count: int
    invalid_depth_snapshot_count: int
    invalid_depth_timestamp_count: int
    crossed_bbo_sanitized_count: int
    crossed_bbo_sanitized_rate: float
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
    depth_queue_depth: int
    depth_queue_high_water: int
    depth_queue_full_count: int
    depth_dropped_envelope_count: int
    depth_worker_processed_count: int
    depth_worker_error_count: int
    event_symbol_mismatch_count: int
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
    reference_reconciliation_duration_ms: float
    reference_reconciliation_path_rows_scanned: int
    reference_reconciliation_reference_rows_scanned: int
    reference_reconciliation_peak_tracked_key_count: int
    duplicate_event_reference_count: int
    duplicate_event_id_count: int
    duplicate_path_reference_pair_count: int
    path_accepted_envelope_count: int
    path_duplicate_sequence_count: int
    path_out_of_order_sequence_count: int
    path_exchange_timestamp_regression_count: int
    path_exchange_timestamp_regression_quarantined_count: int
    path_exchange_timestamp_regression_exceeded_count: int
    path_exchange_timestamp_regression_max_ms: int
    path_exchange_timestamp_regression_tolerance_ms: int
    path_local_receive_timestamp_regression_count: int
    path_local_receive_timestamp_regression_max_ms: int
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
    writer_low_disk_watermark_bytes: int
    writer_critical_disk_watermark_bytes: int
    writer_low_disk_watermark_breach_count: int
    writer_capture_degraded_count: int
    writer_last_error_types: tuple[str, ...]
    writer_last_persisted_sequence: int | None
    writer_last_persisted_sequence_by_series: dict[str, dict[str, int]]
    writer_storage_self_disabled_count: int
    writer_rotation_count: int
    writer_shard_count: int
    writer_manifest_error_count: int
    writer_partition_bytes: int
    writer_projected_partition_bytes_max: int | None
    writer_projection_breach_count: int
    depth_writer_count: int
    depth_writer_alive_count: int
    depth_writer_queue_depth: int
    depth_writer_queue_high_water: int
    depth_writer_persisted_envelope_count: int
    depth_writer_queue_full_count: int
    depth_writer_dropped_envelope_count: int
    depth_writer_error_count: int
    depth_writer_storage_self_disabled_count: int
    depth_writer_manifest_error_count: int
    depth_writer_projection_breach_count: int
    depth_writer_low_disk_watermark_breach_count: int
    depth_writer_bytes_written: int
    canonical_stream_point_count: int
    canonical_stream_duplicate_count: int
    canonical_stream_pre_window_point_count: int
    canonical_stream_active_window_point_count: int
    canonical_stream_post_window_point_count: int
    canonical_stream_complete_segment_count: int
    canonical_stream_incomplete_segment_count: int
    collector_lifecycle: str
    collector_active_callback_count: int
    collector_close_attempt_count: int
    collector_close_failure_count: int
    collector_worker_alive_after_close_count: int
    writer_alive_after_close_count: int
    collector_last_close_error_types: tuple[str, ...]
    sequence_epoch: int
    stale_sequence_epoch_envelope_count: int
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
        return {
            **asdict(self),
            **FORWARD_COLLECTOR_METRIC_CONTRACT,
            "metric_contracts": {
                "crossed_bbo_sanitization": (CROSSED_BBO_SANITIZATION_METRIC_CONTRACT),
                "exchange_timestamp_regression": (
                    EXCHANGE_TIMESTAMP_REGRESSION_METRIC_CONTRACT
                ),
                "exchange_timestamp_regression_canary": (
                    EXCHANGE_TIMESTAMP_REGRESSION_CANARY_METRIC_CONTRACT
                ),
                "depth_callback_latency": DEPTH_CALLBACK_LATENCY_METRIC_CONTRACT,
                "low_disk_capacity_warning": (
                    LOW_DISK_CAPACITY_WARNING_METRIC_CONTRACT
                ),
            },
        }


class ForwardObservationCollector:
    """Fail-isolated 0B intake plus observer-owned detector/path workers."""

    def __init__(
        self,
        *,
        flags: ObserverFeatureFlags,
        config: ForwardCollectorConfig | None = None,
        detector: MultiHorizonShockDetector | None = None,
    ) -> None:
        if not flags.observer_enabled:
            raise ValueError("observer flag must be enabled before collector creation")
        self.flags = flags
        self.config = config or ForwardCollectorConfig()
        self._sink = BoundedObservationQueue(maxsize=self.config.observation_queue_size)
        self._depth_sink: queue.Queue[MarketDepthPoint] = queue.Queue(
            maxsize=self.config.depth_queue_size
        )
        self._adapter = ObservationAdapter(
            self._sink,
            flags=flags,
            queue_depth=self._sink.qsize,
        )
        self._ring = PreEventRingBuffer(
            max_exchange_timestamp_regression_ms=(
                self.config.exchange_timestamp_regression_tolerance_ms
            )
        )
        self._coalescer = ParentWavePathCoalescer(
            self._ring,
            max_open_segments=self.config.storage_policy.max_open_segments,
        )
        self._detector = detector or MultiHorizonShockDetector()
        self._writers: dict[tuple[str, str, str], NonBlockingPathJournalWriter] = {}
        self._depth_writers: dict[
            tuple[str, str, str], NonBlockingPathJournalWriter
        ] = {}
        self._reference_partitions: set[tuple[str, str, str]] = set()
        self._source_sequences: dict[tuple[str, str, str], int] = {}
        self._depth_source_sequences: dict[tuple[str, str, str], int] = {}
        self._sequence_epoch = time.time_ns()
        self._series_epochs: dict[tuple[str, str, str], int] = {}
        self._sequence_losses: dict[tuple[int, str, str, str], dict[int, str]] = {}
        self._last_worker_sequence: dict[tuple[int, str, str, str], int] = {}
        self._series_with_gap: set[tuple[int, str, str, str]] = set()
        self._detector_clock_ms: dict[tuple[str, str, str], int] = {}
        self._transport_epoch_lock = threading.RLock()
        self._state_lock = threading.Lock()
        self._callback_condition = threading.Condition(self._state_lock)
        self._metrics_lock = threading.Lock()
        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None
        self._depth_thread: threading.Thread | None = None
        self._accepting = False
        self._active_callbacks = 0
        self._writers_closing = False
        self._lifecycle = CollectorLifecycle.NEW
        self._producer_0b_callbacks = 0
        self._producer_0d_callbacks = 0
        self._enqueued = 0
        self._depth_enqueued = 0
        self._unsupported_types = 0
        self._missing_0b_items = 0
        self._missing_0d_items = 0
        self._venue_blocks = 0
        self._timestamp_blocks = 0
        self._snapshot_blocks = 0
        self._depth_snapshot_blocks = 0
        self._depth_timestamp_blocks = 0
        self._crossed_bbo_sanitized = 0
        self._future_timestamp_adjustments = 0
        self._stale_timestamp_blocks = 0
        self._quote_age_missing = 0
        self._bbo_complete = 0
        self._exchange_9081_observed = 0
        self._worker_processed = 0
        self._worker_errors = 0
        self._depth_queue_high_water = 0
        self._depth_queue_full = 0
        self._depth_dropped = 0
        self._depth_worker_processed = 0
        self._depth_worker_errors = 0
        self._event_symbol_mismatches = 0
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
        self._reference_reconciliation_duration_ms = 0.0
        self._reference_reconciliation_path_rows_scanned = 0
        self._reference_reconciliation_reference_rows_scanned = 0
        self._reference_reconciliation_peak_tracked_key_count = 0
        self._duplicate_event_references = 0
        self._duplicate_event_ids = 0
        self._duplicate_path_reference_pairs = 0
        self._canonical_stream_points = 0
        self._canonical_stream_duplicates = 0
        self._canonical_stream_pre_points = 0
        self._canonical_stream_active_points = 0
        self._canonical_stream_post_points = 0
        self._canonical_stream_complete_segments = 0
        self._canonical_stream_incomplete_segments = 0
        self._queue_drop_explained_gaps = 0
        self._invalid_envelope_explained_gaps = 0
        self._other_explained_gaps = 0
        self._unexplained_sequence_gaps = 0
        self._stale_sequence_epoch_envelopes = 0
        self._close_attempts = 0
        self._close_failures = 0
        self._worker_alive_after_close = 0
        self._writer_alive_after_close = 0
        self._last_close_error_types: tuple[str, ...] = ()
        self._detector_clock_adjustments = 0
        self._detector_clock_adjustment_max_ms = 0
        self._producer_0b_callback_latency_ms: deque[float] = deque(maxlen=4_096)
        self._producer_0d_callback_latency_ms: deque[float] = deque(maxlen=4_096)

    def start(self) -> None:
        with self._state_lock:
            if self._lifecycle is CollectorLifecycle.RUNNING:
                return
            if self._lifecycle in {
                CollectorLifecycle.CLOSING,
                CollectorLifecycle.CLOSE_FAILED,
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
            if self.flags.depth_capture_active:
                self._depth_thread = threading.Thread(
                    target=self._run_depth,
                    name="micro-reversion-depth-collector",
                    daemon=True,
                )
                self._depth_thread.start()

    def begin_transport_epoch(self) -> int:
        """Atomically detach queued/path state from a completed WS transport.

        Producer callbacks remain non-blocking.  A callback that already took
        an old epoch may enqueue after this boundary, but both workers reject
        that immutable old-epoch row before persistence or detector use.
        """

        with self._transport_epoch_lock:
            with self._state_lock:
                if (
                    self._lifecycle is not CollectorLifecycle.RUNNING
                    or not self._accepting
                ):
                    raise RuntimeError(
                        "transport epoch requires a running forward collector"
                    )
                previous_epoch = self._sequence_epoch
                self._sequence_epoch = max(time.time_ns(), previous_epoch + 1)
                self._source_sequences.clear()
                self._depth_source_sequences.clear()
                self._series_epochs.clear()
                self._sequence_losses.clear()
                self._last_worker_sequence.clear()
                self._detector_clock_ms.clear()
                sequence_epoch = self._sequence_epoch
            self._detector.reset()
            self._ring.reset_transport_epoch()
            self._coalescer.reset_transport_epoch()
            return sequence_epoch

    def close(self, *, timeout_sec: float = 10.0) -> None:
        deadline = time.monotonic() + max(0.01, timeout_sec)
        self._increment("_close_attempts")
        callback_timeout_error: TimeoutError | None = None
        with self._callback_condition:
            if self._lifecycle is CollectorLifecycle.CLOSED:
                return
            thread = self._thread
            depth_thread = self._depth_thread
            self._accepting = False
            self._lifecycle = CollectorLifecycle.CLOSING
            while self._active_callbacks:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    callback_timeout_error = TimeoutError(
                        "producer callbacks did not quiesce in time"
                    )
                    break
                self._callback_condition.wait(timeout=remaining)
            if callback_timeout_error is not None:
                self._lifecycle = CollectorLifecycle.CLOSE_FAILED
            else:
                self._stop_requested.set()
        if callback_timeout_error is not None:
            with self._state_lock:
                callback_timeout_writers = tuple(self._writers.values()) + tuple(
                    self._depth_writers.values()
                )
            callback_timeout_writer_alive = 0
            for writer in callback_timeout_writers:
                try:
                    callback_timeout_writer_alive += int(writer.metrics().writer_alive)
                except Exception:
                    callback_timeout_writer_alive += 1
            with self._metrics_lock:
                self._close_failures += 1
                self._worker_alive_after_close += int(
                    bool(thread is not None and thread.is_alive())
                )
                self._worker_alive_after_close += int(
                    bool(depth_thread is not None and depth_thread.is_alive())
                )
                self._writer_alive_after_close += callback_timeout_writer_alive
                self._last_close_error_types = ("TimeoutError",)
            raise RuntimeError(
                "forward collector shutdown had 1 error(s)"
            ) from callback_timeout_error
        worker_errors: list[Exception] = []
        if thread is not None:
            thread.join(timeout=max(0.01, deadline - time.monotonic()))
            if thread.is_alive():
                worker_errors.append(
                    TimeoutError("forward collector did not drain in time")
                )
        if depth_thread is not None:
            depth_thread.join(timeout=max(0.01, deadline - time.monotonic()))
            if depth_thread.is_alive():
                worker_errors.append(
                    TimeoutError("depth collector did not drain in time")
                )
        # Writers are downstream of both collector workers.  Closing them while
        # a worker is still draining makes accepted rows fail at _writer_for()
        # and also consumes the writer deadline before a retry can succeed.
        # Leave writers running and retry only after both workers quiesce.
        if worker_errors:
            with self._metrics_lock:
                self._worker_alive_after_close += int(
                    bool(thread is not None and thread.is_alive())
                )
                self._worker_alive_after_close += int(
                    bool(depth_thread is not None and depth_thread.is_alive())
                )
            self._record_close_failure(tuple(worker_errors))
            raise RuntimeError(
                f"forward collector shutdown had {len(worker_errors)} error(s)"
            ) from worker_errors[0]

        close_errors: list[Exception] = []
        with self._state_lock:
            self._writers_closing = True
            writers = tuple(self._writers.values()) + tuple(
                self._depth_writers.values()
            )
        # Signal every writer before waiting.  Their accepted queues then drain
        # concurrently instead of the first writer consuming the entire phase.
        for writer in writers:
            try:
                writer.request_close()
            except Exception as exc:  # collector shutdown must inspect every writer
                close_errors.append(exc)
        writer_deadline = time.monotonic() + max(0.01, timeout_sec)
        for writer in writers:
            try:
                writer.wait_closed(
                    timeout_sec=max(0.01, writer_deadline - time.monotonic())
                )
            except Exception as exc:  # collector shutdown must inspect every writer
                close_errors.append(exc)
        writer_alive_count = 0
        for writer in writers:
            try:
                writer_alive_count += int(writer.metrics().writer_alive)
            except Exception as exc:
                close_errors.append(exc)
        if writer_alive_count:
            close_errors.append(
                RuntimeError(f"{writer_alive_count} path writer(s) remain alive")
            )
        try:
            self._reconcile_references_and_paths(shutdown_clean=not close_errors)
        except Exception as exc:
            self._increment("_reference_reconciliation_errors")
            close_errors.append(exc)
        with self._metrics_lock:
            reconciliation_completed = self._reference_reconciliation_completed
        if not close_errors and not reconciliation_completed:
            close_errors.append(
                RuntimeError("reference reconciliation did not complete")
            )
        if close_errors:
            with self._metrics_lock:
                self._worker_alive_after_close += int(
                    bool(thread is not None and thread.is_alive())
                )
                self._worker_alive_after_close += int(
                    bool(depth_thread is not None and depth_thread.is_alive())
                )
                self._writer_alive_after_close += writer_alive_count
            self._record_close_failure(tuple(close_errors))
            raise RuntimeError(
                f"forward collector shutdown had {len(close_errors)} error(s)"
            ) from close_errors[0]
        with self._state_lock:
            self._lifecycle = CollectorLifecycle.CLOSED

    def _record_close_failure(self, errors: tuple[Exception, ...]) -> None:
        with self._metrics_lock:
            self._close_failures += 1
            self._last_close_error_types = tuple(
                type(error).__name__ for error in errors
            )
        with self._state_lock:
            self._lifecycle = CollectorLifecycle.CLOSE_FAILED

    def observe_kiwoom_0b(
        self,
        symbol: str,
        snapshot: dict[str, Any],
        *,
        realtime_type: str,
    ) -> ProducerCanaryResult:
        """Normalize one existing 0B snapshot and enqueue without waiting."""

        callback_started_ns = time.perf_counter_ns()
        with self._callback_condition:
            if not self._accepting:
                return ProducerCanaryResult.DISABLED
            self._active_callbacks += 1

        try:
            if str(realtime_type or "").strip() != "0B":
                self._increment("_unsupported_types")
                return ProducerCanaryResult.UNSUPPORTED_REALTIME_TYPE
            self._increment("_producer_0b_callbacks")
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
            item_symbol, item_venue = registration_item_identity(item)
            if (
                not venue
                or item_venue != venue
                or item_symbol != normalize_symbol(symbol)
                or declared_venue not in {"", venue}
            ):
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
            if best_bid is not None and best_ask is not None and best_ask < best_bid:
                # 0B may carry an internally crossed optional touch while a
                # valid trade is still present. Retain the trade-only row and
                # forbid touch/fill use instead of losing the source sequence.
                best_bid = None
                best_ask = None
                quote_age = None
                self._increment("_crossed_bbo_sanitized")
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
                "0B", (time.perf_counter_ns() - callback_started_ns) / 1_000_000.0
            )
            with self._callback_condition:
                self._active_callbacks -= 1
                if self._active_callbacks == 0:
                    self._callback_condition.notify_all()

    def observe_kiwoom_0d(
        self,
        symbol: str,
        snapshot: dict[str, Any],
        *,
        realtime_type: str,
    ) -> ProducerCanaryResult:
        """Normalize one existing 0D snapshot into the separate bounded queue."""

        callback_started_ns = time.perf_counter_ns()
        with self._callback_condition:
            if not self._accepting or not self.flags.depth_capture_active:
                return ProducerCanaryResult.DISABLED
            self._active_callbacks += 1
        try:
            if str(realtime_type or "").strip() != "0D":
                self._increment("_unsupported_types")
                return ProducerCanaryResult.UNSUPPORTED_REALTIME_TYPE
            self._increment("_producer_0d_callbacks")
            depth = snapshot.get("last_depth_tick")
            if not isinstance(depth, dict):
                self._increment("_depth_snapshot_blocks")
                return ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
            item = str(depth.get("item") or "").strip()
            type_item = str(
                (snapshot.get("last_realtime_type_item") or {}).get("0D") or ""
            ).strip()
            if not item or item != type_item:
                self._increment("_missing_0d_items")
                return ProducerCanaryResult.MISSING_0D_ITEM
            declared_venue = (
                str(
                    (snapshot.get("last_realtime_type_effective_venue") or {}).get("0D")
                    or ""
                )
                .strip()
                .upper()
            )
            venue = _explicit_item_venue(item)
            item_symbol, item_venue = registration_item_identity(item)
            if (
                not venue
                or item_venue != venue
                or item_symbol != normalize_symbol(symbol)
                or declared_venue not in {"", venue}
            ):
                self._increment("_venue_blocks")
                return ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE
            received_at_ms = _positive_int(depth.get("received_at_ms"))
            timestamp_result = _exchange_timestamp_from_0b(
                depth.get("orderbook_time_raw"),
                received_at_ms=received_at_ms,
                future_skew_tolerance_ms=(
                    self.config.exchange_future_skew_tolerance_ms
                ),
                maximum_lag_ms=self.config.maximum_exchange_to_receive_lag_ms,
            )
            if timestamp_result is None:
                self._increment("_depth_timestamp_blocks")
                return ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
            exchange_timestamp, _future_adjusted, stale = timestamp_result
            if stale:
                self._increment("_depth_timestamp_blocks")
                return ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
            try:
                asks = _normalize_depth_levels(depth.get("ask_levels"), side="ask")
                bids = _normalize_depth_levels(depth.get("bid_levels"), side="bid")
                bid_depth = _nonnegative_int(depth.get("bid_depth"))
                ask_depth = _nonnegative_int(depth.get("ask_depth"))
                route_depth_totals = _normalize_route_depth_totals(
                    depth.get("route_depth_totals")
                )
                if ask_depth < sum(row[2] for row in asks) or bid_depth < sum(
                    row[2] for row in bids
                ):
                    raise ValueError("depth totals do not cover retained levels")
                if route_depth_totals["combined"] != {
                    "ask": ask_depth,
                    "bid": bid_depth,
                }:
                    raise ValueError("combined route totals conflict with depth")
            except ValueError:
                self._increment("_depth_snapshot_blocks")
                return ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
            if not asks or not bids:
                self._increment("_depth_snapshot_blocks")
                return ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
            best_ask = asks[0][1]
            best_bid = bids[0][1]
            if best_ask < best_bid:
                self._increment("_depth_snapshot_blocks")
                return ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
            received_at = datetime.fromtimestamp(received_at_ms / 1_000, tz=KST)
            session_bucket = _session_bucket(venue, exchange_timestamp.timetz())
            series_key = (normalize_symbol(symbol), venue, session_bucket)
            sequence_epoch, series_sequence = self._next_depth_source_sequence(
                series_key
            )
            point = MarketDepthPoint(
                symbol=symbol,
                exchange_timestamp=exchange_timestamp.isoformat(),
                local_receive_timestamp=received_at.isoformat(),
                source_sequence=series_sequence,
                sequence_epoch=sequence_epoch,
                series_sequence=series_sequence,
                venue=venue,
                session_bucket=session_bucket,
                item=item,
                orderbook_time_raw=str(depth.get("orderbook_time_raw") or "").strip(),
                best_bid=best_bid,
                best_ask=best_ask,
                best_bid_qty=bids[0][2],
                best_ask_qty=asks[0][2],
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                bid_levels=bids,
                ask_levels=asks,
                route_depth_totals=route_depth_totals,
            )
            try:
                self._depth_sink.put_nowait(point)
            except queue.Full:
                self._increment("_depth_queue_full")
                self._increment("_depth_dropped")
                return ProducerCanaryResult.QUEUE_FULL
            with self._metrics_lock:
                self._depth_enqueued += 1
                self._depth_queue_high_water = max(
                    self._depth_queue_high_water, self._depth_sink.qsize()
                )
            return ProducerCanaryResult.ENQUEUED
        except Exception:
            self._increment("_depth_snapshot_blocks")
            return ProducerCanaryResult.ISOLATED_ERROR
        finally:
            self._record_producer_callback_latency(
                "0D", (time.perf_counter_ns() - callback_started_ns) / 1_000_000.0
            )
            with self._callback_condition:
                self._active_callbacks -= 1
                if self._active_callbacks == 0:
                    self._callback_condition.notify_all()

    def runtime_snapshot(self) -> ForwardCollectorSnapshot:
        adapter = self._adapter.runtime_snapshot()
        with self._state_lock:
            thread = self._thread
            writer_items = tuple(self._writers.items())
            depth_thread = self._depth_thread
            depth_writer_items = tuple(self._depth_writers.items())
            connected = self._accepting
            lifecycle = self._lifecycle.value
            active_callbacks = self._active_callbacks
        writers = tuple(writer for _, writer in writer_items)
        writer_metrics = tuple(writer.metrics() for writer in writers)
        aggregate = _aggregate_writer_metrics(writer_metrics)
        depth_writers = tuple(writer for _, writer in depth_writer_items)
        depth_writer_metrics = tuple(writer.metrics() for writer in depth_writers)
        depth_aggregate = _aggregate_writer_metrics(depth_writer_metrics)
        bytes_by_trade_date: dict[str, int] = {}
        for (trade_date, _venue, _session), metrics in zip(
            (key for key, _writer in writer_items), writer_metrics, strict=True
        ):
            bytes_by_trade_date[trade_date] = (
                bytes_by_trade_date.get(trade_date, 0) + metrics.bytes_written
            )
        path_quality = self._coalescer.quality_snapshot()
        # The 0B callback records several counters through this lock.  Copy the
        # rolling samples first, then perform percentile sorting outside the
        # critical section so the 10-second canary snapshot cannot manufacture
        # a callback-latency p99 breach through lock contention of its own.
        with self._metrics_lock:
            callback_latency = tuple(self._producer_0b_callback_latency_ms)
            depth_callback_latency = tuple(self._producer_0d_callback_latency_ms)
            reference_latency = tuple(self._reference_write_latency_ms)
            producer_0b_callback_count = self._producer_0b_callbacks
        callback_latency_p50_ms = _percentile(callback_latency, 50)
        callback_latency_p95_ms = _percentile(callback_latency, 95)
        callback_latency_p99_ms = _percentile(callback_latency, 99)
        depth_callback_latency_p50_ms = _percentile(depth_callback_latency, 50)
        depth_callback_latency_p95_ms = _percentile(depth_callback_latency, 95)
        depth_callback_latency_p99_ms = _percentile(depth_callback_latency, 99)
        reference_write_latency_p95_ms = _percentile(reference_latency, 95)
        reference_write_latency_p99_ms = _percentile(reference_latency, 99)
        with self._metrics_lock:
            return ForwardCollectorSnapshot(
                schema=FORWARD_COLLECTOR_SCHEMA,
                observer_runtime_loaded=True,
                producer_observation_connected=connected,
                observer_runtime_effect=bool(thread is not None and thread.is_alive()),
                observation_capture_active=(
                    bool(thread is not None and thread.is_alive())
                    and self.flags.observation_capture_active
                ),
                depth_capture_active=(
                    bool(depth_thread is not None and depth_thread.is_alive())
                    and self.flags.depth_capture_active
                ),
                depth_capture_requested=self.flags.depth_capture_active,
                producer_0b_callback_count=producer_0b_callback_count,
                producer_0d_callback_count=self._producer_0d_callbacks,
                enqueued_count=self._enqueued,
                depth_enqueued_count=self._depth_enqueued,
                producer_callback_latency_scope=PRODUCER_CALLBACK_LATENCY_SCOPE,
                producer_callback_latency_p50_ms=callback_latency_p50_ms,
                producer_callback_latency_p95_ms=callback_latency_p95_ms,
                producer_callback_latency_p99_ms=callback_latency_p99_ms,
                producer_0d_callback_latency_p50_ms=(depth_callback_latency_p50_ms),
                producer_0d_callback_latency_p95_ms=(depth_callback_latency_p95_ms),
                producer_0d_callback_latency_p99_ms=(depth_callback_latency_p99_ms),
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
                adapter_invalid_envelope_count=adapter.invalid_envelope_count,
                adapter_isolated_error_count=adapter.isolated_error_count,
                unsupported_realtime_type_count=self._unsupported_types,
                missing_0b_item_count=self._missing_0b_items,
                missing_0d_item_count=self._missing_0d_items,
                missing_or_conflicting_venue_count=self._venue_blocks,
                invalid_exchange_timestamp_count=self._timestamp_blocks,
                invalid_trade_snapshot_count=self._snapshot_blocks,
                invalid_depth_snapshot_count=self._depth_snapshot_blocks,
                invalid_depth_timestamp_count=self._depth_timestamp_blocks,
                crossed_bbo_sanitized_count=self._crossed_bbo_sanitized,
                crossed_bbo_sanitized_rate=_rate(
                    self._crossed_bbo_sanitized, self._producer_0b_callbacks
                ),
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
                depth_queue_depth=self._depth_sink.qsize(),
                depth_queue_high_water=self._depth_queue_high_water,
                depth_queue_full_count=self._depth_queue_full,
                depth_dropped_envelope_count=self._depth_dropped,
                depth_worker_processed_count=self._depth_worker_processed,
                depth_worker_error_count=self._depth_worker_errors,
                event_symbol_mismatch_count=self._event_symbol_mismatches,
                shock_event_count=self._shock_events,
                path_point_submitted_count=self._path_submitted,
                path_point_dropped_count=self._path_dropped,
                event_reference_persisted_count=self._reference_persisted,
                event_reference_error_count=self._reference_errors,
                event_reference_write_latency_p95_ms=(reference_write_latency_p95_ms),
                event_reference_write_latency_p99_ms=(reference_write_latency_p99_ms),
                event_reference_coverage_pct=self._reference_coverage_pct,
                orphan_reference_count=self._orphan_references,
                unreferenced_segment_count=self._unreferenced_segments,
                reference_reconciliation_error_count=(
                    self._reference_reconciliation_errors
                ),
                reference_reconciliation_completed=(
                    self._reference_reconciliation_completed
                ),
                reference_reconciliation_duration_ms=(
                    self._reference_reconciliation_duration_ms
                ),
                reference_reconciliation_path_rows_scanned=(
                    self._reference_reconciliation_path_rows_scanned
                ),
                reference_reconciliation_reference_rows_scanned=(
                    self._reference_reconciliation_reference_rows_scanned
                ),
                reference_reconciliation_peak_tracked_key_count=(
                    self._reference_reconciliation_peak_tracked_key_count
                ),
                duplicate_event_reference_count=self._duplicate_event_references,
                duplicate_event_id_count=self._duplicate_event_ids,
                duplicate_path_reference_pair_count=(
                    self._duplicate_path_reference_pairs
                ),
                path_accepted_envelope_count=(path_quality.accepted_envelope_count),
                path_duplicate_sequence_count=(path_quality.duplicate_sequence_count),
                path_out_of_order_sequence_count=(
                    path_quality.out_of_order_sequence_count
                ),
                path_exchange_timestamp_regression_count=(
                    path_quality.exchange_timestamp_regression_count
                ),
                path_exchange_timestamp_regression_quarantined_count=(
                    path_quality.exchange_timestamp_regression_quarantined_count
                ),
                path_exchange_timestamp_regression_exceeded_count=(
                    path_quality.exchange_timestamp_regression_exceeded_count
                ),
                path_exchange_timestamp_regression_max_ms=(
                    path_quality.exchange_timestamp_regression_max_ms
                ),
                path_exchange_timestamp_regression_tolerance_ms=(
                    self.config.exchange_timestamp_regression_tolerance_ms
                ),
                path_local_receive_timestamp_regression_count=(
                    path_quality.local_receive_timestamp_regression_count
                ),
                path_local_receive_timestamp_regression_max_ms=(
                    path_quality.local_receive_timestamp_regression_max_ms
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
                writer_low_disk_watermark_bytes=(
                    self.config.storage_policy.low_disk_watermark_bytes
                ),
                writer_critical_disk_watermark_bytes=(
                    self.config.storage_policy.critical_disk_watermark_bytes
                ),
                writer_low_disk_watermark_breach_count=aggregate[
                    "low_disk_watermark_breaches"
                ],
                writer_capture_degraded_count=aggregate["capture_degraded"],
                writer_last_error_types=aggregate["last_error_types"],
                writer_last_persisted_sequence=aggregate["last_sequence"],
                writer_last_persisted_sequence_by_series=aggregate[
                    "last_sequence_by_series"
                ],
                writer_storage_self_disabled_count=aggregate["self_disabled"],
                writer_rotation_count=aggregate["rotations"],
                writer_shard_count=aggregate["shard_count"],
                writer_manifest_error_count=aggregate["manifest_errors"],
                writer_partition_bytes=aggregate["partition_bytes"],
                writer_projected_partition_bytes_max=aggregate[
                    "projected_partition_bytes_max"
                ],
                writer_projection_breach_count=aggregate["projection_breaches"],
                depth_writer_count=len(depth_writer_metrics),
                depth_writer_alive_count=sum(
                    1 for metric in depth_writer_metrics if metric.writer_alive
                ),
                depth_writer_queue_depth=depth_aggregate["queue_depth"],
                depth_writer_queue_high_water=depth_aggregate["queue_high_water"],
                depth_writer_persisted_envelope_count=depth_aggregate["persisted"],
                depth_writer_queue_full_count=depth_aggregate["queue_full"],
                depth_writer_dropped_envelope_count=depth_aggregate["dropped"],
                depth_writer_error_count=depth_aggregate["errors"],
                depth_writer_storage_self_disabled_count=depth_aggregate[
                    "self_disabled"
                ],
                depth_writer_manifest_error_count=depth_aggregate["manifest_errors"],
                depth_writer_projection_breach_count=depth_aggregate[
                    "projection_breaches"
                ],
                depth_writer_low_disk_watermark_breach_count=depth_aggregate[
                    "low_disk_watermark_breaches"
                ],
                depth_writer_bytes_written=depth_aggregate["bytes_written"],
                canonical_stream_point_count=self._canonical_stream_points,
                canonical_stream_duplicate_count=self._canonical_stream_duplicates,
                canonical_stream_pre_window_point_count=(
                    self._canonical_stream_pre_points
                ),
                canonical_stream_active_window_point_count=(
                    self._canonical_stream_active_points
                ),
                canonical_stream_post_window_point_count=(
                    self._canonical_stream_post_points
                ),
                canonical_stream_complete_segment_count=(
                    self._canonical_stream_complete_segments
                ),
                canonical_stream_incomplete_segment_count=(
                    self._canonical_stream_incomplete_segments
                ),
                collector_lifecycle=lifecycle,
                collector_active_callback_count=active_callbacks,
                collector_close_attempt_count=self._close_attempts,
                collector_close_failure_count=self._close_failures,
                collector_worker_alive_after_close_count=(
                    self._worker_alive_after_close
                ),
                writer_alive_after_close_count=self._writer_alive_after_close,
                collector_last_close_error_types=self._last_close_error_types,
                sequence_epoch=self._sequence_epoch,
                stale_sequence_epoch_envelope_count=(
                    self._stale_sequence_epoch_envelopes
                ),
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

    def _next_depth_source_sequence(
        self, series_key: tuple[str, str, str]
    ) -> tuple[int, int]:
        with self._state_lock:
            previous = self._depth_source_sequences.get(series_key, 0)
            sequence = previous + 1
            self._depth_source_sequences[series_key] = sequence
            return self._sequence_epoch, sequence

    def _run(self) -> None:
        while not self._stop_requested.is_set() or self._sink.qsize() > 0:
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

    def _run_depth(self) -> None:
        while not self._stop_requested.is_set() or self._depth_sink.qsize() > 0:
            try:
                point = self._depth_sink.get(
                    timeout=self.config.worker_poll_interval_sec
                )
            except queue.Empty:
                continue
            try:
                with self._transport_epoch_lock:
                    if self._is_stale_depth_sequence_epoch(point):
                        self._increment("_depth_dropped")
                        continue
                    writer = self._depth_writer_for(point)
                    if not writer.submit(point):
                        self._increment("_depth_dropped")
                    else:
                        self._increment("_depth_worker_processed")
            except Exception:
                self._increment("_depth_worker_errors")
            finally:
                self._depth_sink.task_done()

    def _process_envelope(self, envelope: RawMarketObservation) -> None:
        with self._transport_epoch_lock:
            if self._is_stale_sequence_epoch(envelope):
                self._increment("_stale_sequence_epoch_envelopes")
                return
            self._account_for_sequence_gap(envelope)
            self._process_allowed_envelope(envelope)

    def _is_stale_sequence_epoch(self, envelope: RawMarketObservation) -> bool:
        series_key = (envelope.symbol, envelope.venue, envelope.session_bucket)
        with self._state_lock:
            current_epoch = self._series_epochs.get(series_key)
        return current_epoch != envelope.sequence_epoch

    def _is_stale_depth_sequence_epoch(self, point: MarketDepthPoint) -> bool:
        with self._state_lock:
            current_epoch = self._sequence_epoch
        return current_epoch != point.sequence_epoch

    def _event_registration_allowed(
        self, envelope: RawMarketObservation, event: Any
    ) -> bool:
        event_symbol = normalize_symbol(
            getattr(getattr(event, "event", None), "symbol", "")
        )
        if event_symbol != envelope.symbol:
            self._increment("_event_symbol_mismatches")
            return False
        return not self._is_stale_sequence_epoch(envelope)

    def _process_allowed_envelope(self, envelope: RawMarketObservation) -> None:
        if not self.flags.path_capture_enabled:
            self._ring.add(envelope)
            self._increment("_worker_processed")
            return
        order_assessment = self._ring.order_assessment(envelope)
        order_status = order_assessment.status
        self._submit_points(
            envelope,
            (
                to_market_stream_point(
                    envelope,
                    path_order_status=order_status,
                    exchange_timestamp_regression_ms=(
                        order_assessment.exchange_timestamp_regression_ms
                    ),
                ),
            ),
        )
        if order_status is not PathEnvelopeOrderStatus.ACCEPT:
            # Persist the immutable raw stream row, then quarantine it from
            # detector/path consumers. The ring records whether the bounded
            # one-second tolerance or the hard-stop boundary was crossed.
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
            if not self._event_registration_allowed(envelope, event):
                continue
            registration = self._coalescer.register_event(
                event,
                sequence_epoch=envelope.sequence_epoch,
                event_exchange_timestamp=envelope.exchange_timestamp,
            )
            registrations.append(registration)
            self._append_reference(envelope, registration.event_reference)
        self._ring.add(envelope)
        self._coalescer.active_segments_for(envelope)
        self._increment("_worker_processed")
        if registrations:
            self._add("_shock_events", len(registrations))

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
        started_ns = time.perf_counter_ns()
        if not shutdown_clean:
            with self._metrics_lock:
                self._reference_reconciliation_errors += 1
                self._reference_reconciliation_completed = False
                self._reference_reconciliation_duration_ms = (
                    time.perf_counter_ns() - started_ns
                ) / 1_000_000.0
            return
        with self._state_lock:
            partitions = tuple(set(self._writers) | self._reference_partitions)
        total_references = 0
        covered_references = 0
        orphan_references = 0
        unreferenced_segments = 0
        path_rows_scanned = 0
        reference_rows_scanned = 0
        peak_tracked_keys = 0
        duplicate_references = 0
        duplicate_event_ids = 0
        duplicate_pairs = 0
        canonical_stream_points = 0
        canonical_stream_duplicates = 0
        canonical_stream_pre_points = 0
        canonical_stream_active_points = 0
        canonical_stream_post_points = 0
        canonical_stream_complete_segments = 0
        canonical_stream_incomplete_segments = 0
        errors = 0
        for trade_date, venue, session_bucket in partitions:
            path = self.config.storage_policy.partition_path(
                self.config.output_root,
                trade_date=trade_date,
                venue=venue,
                session_bucket=session_bucket,
            )
            stream_path = self.config.storage_policy.stream_partition_path(
                self.config.output_root,
                trade_date=trade_date,
                venue=venue,
                session_bucket=session_bucket,
            )
            try:
                stream_files = partition_path_files(stream_path)
                stream_reference_path = stream_path.with_name(
                    "market_stream_event_references.jsonl"
                )
                if stream_files or stream_reference_path.exists():
                    reference_rows = _jsonl_rows(stream_reference_path)
                    (
                        path_segments,
                        partition_path_rows_scanned,
                        stream_duplicate_count,
                        stream_phase_counts,
                    ) = _reconcile_canonical_stream(stream_files, reference_rows)
                    canonical_stream_points += partition_path_rows_scanned
                    canonical_stream_duplicates += stream_duplicate_count
                    canonical_stream_pre_points += stream_phase_counts["pre"]
                    canonical_stream_active_points += stream_phase_counts["active"]
                    canonical_stream_post_points += stream_phase_counts["post"]
                    canonical_stream_complete_segments += stream_phase_counts[
                        "complete_segments"
                    ]
                    canonical_stream_incomplete_segments += stream_phase_counts[
                        "incomplete_segments"
                    ]
                else:
                    reference_rows = _jsonl_rows(
                        path.with_name("event_references.jsonl")
                    )
                    path_segments = set()
                    partition_path_rows_scanned = 0
                    for shard in partition_path_files(path):
                        for row in _iter_jsonl_rows(shard):
                            partition_path_rows_scanned += 1
                            segment_id = str(row.get("path_segment_id") or "").strip()
                            if segment_id:
                                path_segments.add(segment_id)
            except (OSError, ValueError, json.JSONDecodeError):
                errors += 1
                continue
            path_rows_scanned += partition_path_rows_scanned
            reference_rows_scanned += len(reference_rows)
            references = [
                str(row.get("path_segment_id") or "").strip() for row in reference_rows
            ]
            reference_segments = {value for value in references if value}
            canonical_references = [
                json.dumps(row, sort_keys=True, separators=(",", ":"))
                for row in reference_rows
            ]
            event_ids = [
                str(row.get("shock_event_id") or "").strip()
                for row in reference_rows
                if str(row.get("shock_event_id") or "").strip()
            ]
            reference_pairs = [
                (
                    str(row.get("shock_event_id") or "").strip(),
                    str(row.get("path_segment_id") or "").strip(),
                )
                for row in reference_rows
                if str(row.get("shock_event_id") or "").strip()
                and str(row.get("path_segment_id") or "").strip()
            ]
            duplicate_references += len(canonical_references) - len(
                set(canonical_references)
            )
            duplicate_event_ids += len(event_ids) - len(set(event_ids))
            duplicate_pairs += len(reference_pairs) - len(set(reference_pairs))
            peak_tracked_keys = max(
                peak_tracked_keys,
                len(path_segments)
                + len(reference_segments)
                + len(set(canonical_references))
                + len(set(event_ids))
                + len(set(reference_pairs)),
            )
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
            self._reference_reconciliation_duration_ms = (
                time.perf_counter_ns() - started_ns
            ) / 1_000_000.0
            self._reference_reconciliation_path_rows_scanned = path_rows_scanned
            self._reference_reconciliation_reference_rows_scanned = (
                reference_rows_scanned
            )
            self._reference_reconciliation_peak_tracked_key_count = peak_tracked_keys
            self._duplicate_event_references = duplicate_references
            self._duplicate_event_ids = duplicate_event_ids
            self._duplicate_path_reference_pairs = duplicate_pairs
            self._canonical_stream_points = canonical_stream_points
            self._canonical_stream_duplicates = canonical_stream_duplicates
            self._canonical_stream_pre_points = canonical_stream_pre_points
            self._canonical_stream_active_points = canonical_stream_active_points
            self._canonical_stream_post_points = canonical_stream_post_points
            self._canonical_stream_complete_segments = (
                canonical_stream_complete_segments
            )
            self._canonical_stream_incomplete_segments = (
                canonical_stream_incomplete_segments
            )

    def _submit_points(
        self,
        envelope: RawMarketObservation,
        points: tuple[MarketPathPoint | MarketStreamPoint, ...],
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
            if self._writers_closing:
                raise RuntimeError("path writer access blocked during shutdown")
            writer = self._writers.get(key)
            if writer is not None:
                return writer
            path = self.config.storage_policy.stream_partition_path(
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

    def _depth_writer_for(
        self, point: MarketDepthPoint
    ) -> NonBlockingPathJournalWriter:
        trade_date = datetime.fromisoformat(point.exchange_timestamp).date().isoformat()
        key = (trade_date, point.venue, point.session_bucket)
        with self._state_lock:
            if self._writers_closing:
                raise RuntimeError("depth writer access blocked during shutdown")
            writer = self._depth_writers.get(key)
            if writer is not None:
                return writer
            path = self.config.storage_policy.depth_partition_path(
                self.config.output_root,
                trade_date=trade_date,
                venue=point.venue,
                session_bucket=point.session_bucket,
            )
            writer = NonBlockingPathJournalWriter(
                path,
                max_queue_size=self.config.path_queue_size,
                max_batch_size=self.config.path_batch_size,
                flush_interval_sec=self.config.writer_flush_interval_sec,
                storage_policy=self.config.storage_policy,
            )
            writer.start()
            self._depth_writers[key] = writer
            return writer

    def _append_reference(
        self, envelope: RawMarketObservation, reference: PathEventReference
    ) -> None:
        started_ns = time.perf_counter_ns()
        trade_date = (
            datetime.fromisoformat(envelope.exchange_timestamp).date().isoformat()
        )
        path = self.config.storage_policy.stream_partition_path(
            self.config.output_root,
            trade_date=trade_date,
            venue=envelope.venue,
            session_bucket=envelope.session_bucket,
        ).with_name("market_stream_event_references.jsonl")
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

    def _record_producer_callback_latency(
        self, realtime_type: str, value: float
    ) -> None:
        with self._metrics_lock:
            latency = max(0.0, float(value))
            if realtime_type == "0B":
                self._producer_0b_callback_latency_ms.append(latency)
            elif realtime_type == "0D":
                self._producer_0d_callback_latency_ms.append(latency)
            else:
                raise ValueError("unsupported_callback_latency_realtime_type")

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
    configured_output_root = Path(
        os.getenv("SCALP_MICRO_REVERSION_PATH_ROOT", str(DEFAULT_OUTPUT_ROOT))
    )
    output_root = (
        configured_output_root
        if configured_output_root.is_absolute()
        else REPOSITORY_ROOT / configured_output_root
    )
    config = ForwardCollectorConfig(
        output_root=output_root,
        observation_queue_size=_bounded_env_int(
            "SCALP_MICRO_REVERSION_OBSERVATION_QUEUE_SIZE", 50_000, 1, 200_000
        ),
        path_queue_size=_bounded_env_int(
            "SCALP_MICRO_REVERSION_PATH_QUEUE_SIZE", 10_000, 1, 200_000
        ),
        depth_queue_size=_bounded_env_int(
            "SCALP_MICRO_REVERSION_DEPTH_QUEUE_SIZE", 50_000, 1, 200_000
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
        # Kiwoom documents _AL as the explicit SOR subscription route.  It
        # does not identify the underlying KRX/NXT execution venue, so keep it
        # in a separate SOR cohort instead of guessing either exchange.
        return "SOR"
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
    if venue == "SOR":
        if local_clock < datetime_time(9, 0):
            return "SOR_PREMARKET"
        if local_clock < datetime_time(15, 30):
            return "SOR_REGULAR"
        return "SOR_AFTERMARKET"
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
        "low_disk_watermark_breaches": sum(
            1 for row in rows if row.low_disk_watermark_breached
        ),
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
        "rotations": sum(row.journal_rotation_count for row in rows),
        "shard_count": sum(row.journal_shard_count for row in rows),
        "manifest_errors": sum(row.journal_manifest_error_count for row in rows),
        "partition_bytes": sum(row.journal_partition_bytes for row in rows),
        "projected_partition_bytes_max": max(
            (
                row.journal_projected_partition_bytes
                for row in rows
                if row.journal_projected_partition_bytes is not None
            ),
            default=None,
        ),
        "projection_breaches": sum(row.journal_projection_breach_count for row in rows),
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


def _nonnegative_int(value: object) -> int:
    parsed = _nonnegative_int_or_none(value)
    if parsed is None:
        raise ValueError("depth quantity must be a nonnegative integer")
    return parsed


def _normalize_depth_levels(
    value: object,
    *,
    side: str,
) -> tuple[tuple[int, float, int], ...]:
    if side not in {"ask", "bid"}:
        raise ValueError("depth side must be ask or bid")
    if not isinstance(value, (list, tuple)):
        raise ValueError("depth levels must be a list")
    normalized: list[tuple[int, float, int]] = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError("depth level must be an object")
        level = _positive_int(row.get("level"))
        price = _positive_float_or_none(row.get("price"))
        quantity = _nonnegative_int_or_none(row.get("quantity"))
        if level <= 0 or price is None or quantity is None:
            raise ValueError("depth level fields are invalid")
        normalized.append((level, price, quantity))
    normalized.sort(key=lambda row: row[0])
    if len({row[0] for row in normalized}) != len(normalized):
        raise ValueError("depth levels must not contain duplicates")
    retained = tuple(normalized[:5])
    if tuple(row[0] for row in retained) != tuple(range(1, len(retained) + 1)):
        raise ValueError("depth levels must start at one and be contiguous")
    prices = tuple(row[1] for row in retained)
    if side == "ask" and any(
        left >= right for left, right in zip(prices, prices[1:], strict=False)
    ):
        raise ValueError("ask prices must increase by level")
    if side == "bid" and any(
        left <= right for left, right in zip(prices, prices[1:], strict=False)
    ):
        raise ValueError("bid prices must decrease by level")
    return retained


def _normalize_route_depth_totals(
    value: object,
) -> dict[str, dict[str, int | None]]:
    if not isinstance(value, dict):
        raise ValueError("route depth totals must be an object")
    normalized: dict[str, dict[str, int | None]] = {}
    for route in ("combined", "KRX", "NXT"):
        raw = value.get(route)
        if not isinstance(raw, dict):
            continue
        normalized[route] = {
            side: (None if raw.get(side) is None else _nonnegative_int(raw.get(side)))
            for side in ("ask", "bid")
        }
    if "combined" not in normalized:
        raise ValueError("combined depth totals are required")
    if any(normalized["combined"].get(side) is None for side in ("ask", "bid")):
        raise ValueError("combined depth totals must be observed")
    return normalized


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


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    return list(_iter_jsonl_rows(path))


def _iter_jsonl_rows(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("JSONL row must be an object")
            yield payload


def _reconcile_canonical_stream(
    stream_files: tuple[Path, ...], reference_rows: list[dict[str, Any]]
) -> tuple[set[str], int, int, dict[str, int]]:
    series_times: dict[tuple[str, str, str, int], list[int]] = {}
    seen_sequences: set[tuple[str, str, str, int, int]] = set()
    duplicate_count = 0
    row_count = 0
    for stream_file in stream_files:
        for row in _iter_jsonl_rows(stream_file):
            stream_contract = (
                row.get("schema"),
                row.get("metric_contract_id"),
            )
            if stream_contract not in {
                (
                    "scalp_micro_reversion_market_stream_point_v1",
                    "scalp_micro_reversion_market_stream_contract_v1",
                ),
                (
                    "scalp_micro_reversion_market_stream_point_v2",
                    "scalp_micro_reversion_market_stream_contract_v2",
                ),
                (
                    "scalp_micro_reversion_market_stream_point_v3",
                    "scalp_micro_reversion_market_stream_contract_v3",
                ),
            }:
                raise ValueError("unexpected canonical stream schema or contract")
            if (
                row.get("actual_order_submitted") is not False
                or row.get("broker_order_forbidden") is not True
                or row.get("trading_runtime_effect") is not False
            ):
                raise ValueError("canonical stream authority contract is invalid")
            if stream_contract[0].endswith("_v3"):
                _, eligible, _ = validate_market_stream_path_provenance(
                    path_order_status=row.get("path_order_status"),
                    path_consumer_eligible=row.get("path_consumer_eligible"),
                    exchange_timestamp_regression_ms=row.get(
                        "exchange_timestamp_regression_ms"
                    ),
                )
            key = (
                str(row.get("symbol") or "").strip(),
                str(row.get("venue") or "").strip(),
                str(row.get("session_bucket") or "").strip(),
                int(row.get("sequence_epoch") or 0),
            )
            sequence = int(row.get("series_sequence") or 0)
            source_sequence = int(row.get("source_sequence") or 0)
            if (
                not all(key[:3])
                or key[3] <= 0
                or sequence <= 0
                or source_sequence != sequence
            ):
                raise ValueError("canonical stream scope or sequence is invalid")
            sequence_key = (*key, sequence)
            if sequence_key in seen_sequences:
                duplicate_count += 1
            else:
                seen_sequences.add(sequence_key)
            if stream_contract[0].endswith("_v3") and not eligible:
                row_count += 1
                continue
            series_times.setdefault(key, []).append(
                _iso_timestamp_ms(str(row.get("exchange_timestamp") or ""))
            )
            row_count += 1
    for values in series_times.values():
        values.sort()
    covered_segments: set[str] = set()
    phase_counts = {
        "pre": 0,
        "active": 0,
        "post": 0,
        "complete_segments": 0,
        "incomplete_segments": 0,
    }
    measured_segments: set[str] = set()
    for reference in reference_rows:
        if reference.get("schema") != "scalp_micro_reversion_path_event_reference_v2":
            raise ValueError("canonical stream requires v2 event references")
        if (
            reference.get("actual_order_submitted") is not False
            or reference.get("broker_order_forbidden") is not True
            or reference.get("trading_runtime_effect") is not False
        ):
            raise ValueError("canonical stream reference authority is invalid")
        segment_id = str(reference.get("path_segment_id") or "").strip()
        key = (
            str(reference.get("symbol") or "").strip(),
            str(reference.get("venue") or "").strip(),
            str(reference.get("session_bucket") or "").strip(),
            int(reference.get("sequence_epoch") or 0),
        )
        start_ms = _iso_timestamp_ms(str(reference.get("capture_started_at") or ""))
        end_ms = _iso_timestamp_ms(str(reference.get("capture_ended_at") or ""))
        values = series_times.get(key, ())
        index = bisect_left(values, start_ms)
        if segment_id and index < len(values) and values[index] <= end_ms:
            covered_segments.add(segment_id)
        if not segment_id or segment_id in measured_segments:
            continue
        measured_segments.add(segment_id)
        event_ms = int(reference.get("segment_event_detected_at_ms") or 0)
        if event_ms <= 0:
            raise ValueError("canonical stream reference event time is invalid")
        active_end_ms = min(event_ms + 20_000, end_ms)
        pre_count = bisect_left(values, event_ms) - bisect_left(values, start_ms)
        active_count = bisect_right(values, active_end_ms) - bisect_left(
            values, event_ms
        )
        post_count = bisect_right(values, end_ms) - bisect_right(values, active_end_ms)
        phase_counts["pre"] += pre_count
        phase_counts["active"] += active_count
        phase_counts["post"] += post_count
        if pre_count > 0 and active_count > 0 and post_count > 0:
            phase_counts["complete_segments"] += 1
        else:
            phase_counts["incomplete_segments"] += 1
    return covered_segments, row_count, duplicate_count, phase_counts
