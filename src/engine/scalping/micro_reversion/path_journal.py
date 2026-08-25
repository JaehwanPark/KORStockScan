"""Non-blocking, append-only market-path capture for detected events.

The producer-facing method performs a bounded ``put_nowait`` only.  A dedicated
writer thread batches durable appends so observation failures cannot block the
market-data or order hot path.
"""

from __future__ import annotations

import fcntl
import json
import os
import queue
import shutil
import stat
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .contracts import normalize_symbol, normalize_venue

MARKET_PATH_SCHEMA = "scalp_micro_reversion_market_path_point_v6"
MARKET_PATH_MANIFEST_SCHEMA = "scalp_micro_reversion_market_path_manifest_v1"
MARKET_PATH_AUTHORITY = "continuous_market_path_observation_only"
MARKET_STREAM_SCHEMA = "scalp_micro_reversion_market_stream_point_v3"
MARKET_STREAM_CONTRACT_ID = "scalp_micro_reversion_market_stream_contract_v3"
MARKET_STREAM_AUTHORITY = "canonical_market_stream_observation_only"
MARKET_DEPTH_SCHEMA = "scalp_micro_reversion_market_depth_point_v1"
MARKET_DEPTH_CONTRACT_ID = "scalp_micro_reversion_market_depth_contract_v1"
MARKET_DEPTH_AUTHORITY = "continuous_0d_depth_observation_only"
MARKET_STREAM_PATH_ORDER_STATUSES = frozenset(
    {
        "accept",
        "duplicate_source_sequence",
        "source_sequence_regression",
        "local_receive_timestamp_regression",
        "exchange_timestamp_regression_quarantined",
        "exchange_timestamp_regression_exceeded",
    }
)
MARKET_PATH_METRIC_CONTRACT = {
    "metric_role": "source_quality_gate",
    "decision_authority": MARKET_PATH_AUTHORITY,
    "window_policy": "event_baseline_through_180s_or_policy_terminal",
    "sample_floor": "collector_health_5d_200_events_not_economic_promotion",
    "primary_decision_metric": "pre_active_post_path_coverage_pct",
    "source_quality_gate": (
        "monotonic_source_sequence_and_timezone_aware_exchange_and_receive_timestamps"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "touch_as_real_fill",
        "missing_path_imputation",
        "sim_or_runtime_promotion_without_economic_gate",
    ),
}
MARKET_STREAM_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_canonical_market_stream",
    "decision_authority": MARKET_STREAM_AUTHORITY,
    "window_policy": "one_row_per_accepted_series_sequence_full_session",
    "sample_floor": "five_trading_days_and_200_mature_events_gate_b_only",
    "primary_decision_metric": "canonical_stream_sequence_coverage_pct",
    "source_quality_gate": (
        "monotonic_series_sequence_and_timezone_aware_exchange_and_receive_"
        "timestamps_with_explicit_path_consumer_eligibility"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "touch_as_real_fill",
        "missing_path_imputation",
        "sim_or_runtime_promotion_without_economic_gate",
    ),
}
MARKET_DEPTH_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_orderbook_depth_context",
    "decision_authority": MARKET_DEPTH_AUTHORITY,
    "window_policy": "one_row_per_accepted_0d_callback_full_session",
    "sample_floor": "five_trading_days_and_200_mature_events_gate_b_only",
    "primary_decision_metric": "past_only_depth_join_coverage_pct",
    "source_quality_gate": (
        "official_0d_fid21_and_explicit_item_venue_and_monotonic_local_"
        "receive_sequence_with_positive_non_crossed_best_quotes"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "touch_or_depth_as_real_fill",
        "future_or_cross_venue_depth_join",
        "missing_depth_imputation",
        "sim_or_runtime_promotion_without_economic_gate",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}


def validate_market_stream_path_provenance(
    *,
    path_order_status: object,
    path_consumer_eligible: object,
    exchange_timestamp_regression_ms: object,
) -> tuple[str, bool, int]:
    """Validate V3 ordering provenance before any path consumer uses a row."""

    if (
        not isinstance(path_order_status, str)
        or path_order_status not in MARKET_STREAM_PATH_ORDER_STATUSES
    ):
        raise ValueError("canonical stream path_order_status is invalid")
    status = path_order_status
    if not isinstance(path_consumer_eligible, bool):
        raise ValueError("canonical stream path_consumer_eligible must be boolean")
    if not isinstance(exchange_timestamp_regression_ms, int) or isinstance(
        exchange_timestamp_regression_ms, bool
    ):
        raise ValueError("exchange timestamp regression must be an integer")
    regression_ms = exchange_timestamp_regression_ms
    if regression_ms < 0:
        raise ValueError("exchange timestamp regression must not be negative")
    is_exchange_regression = status.startswith("exchange_timestamp_regression_")
    if is_exchange_regression != (regression_ms > 0):
        raise ValueError("exchange timestamp regression provenance is inconsistent")
    if path_consumer_eligible != (status == "accept"):
        raise ValueError("path eligibility conflicts with ordering status")
    return status, path_consumer_eligible, regression_ms


class AggressorSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MarketPathPoint:
    event_id: str
    path_segment_id: str
    symbol: str
    exchange_timestamp: str
    local_receive_timestamp: str
    source_sequence: int
    sequence_epoch: int
    series_sequence: int
    venue: str
    session_bucket: str
    detector_version: str
    capture_started_at: str
    event_detected_at: str
    parent_wave_id: str
    path_phase: str
    capture_ended_at: str | None = None
    trade_price: float | None = None
    trade_qty: int | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    bid_depth: int | None = None
    ask_depth: int | None = None
    quote_age_ms: float | None = None
    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    dropped_message_count: int = 0
    schema: str = MARKET_PATH_SCHEMA

    def __post_init__(self) -> None:
        if not str(self.event_id).strip() or not str(self.path_segment_id).strip():
            raise ValueError("event_id and path_segment_id are required")
        if not str(self.parent_wave_id).strip():
            raise ValueError("parent_wave_id is required")
        if self.path_phase not in {"PRE_EVENT", "ACTIVE_EVENT", "POST_EVENT"}:
            raise ValueError(
                "path_phase must be PRE_EVENT, ACTIVE_EVENT, or POST_EVENT"
            )
        symbol = normalize_symbol(self.symbol)
        if not symbol:
            raise ValueError("symbol is required")
        venue = normalize_venue(self.venue)
        if venue == "UNKNOWN":
            raise ValueError("market path venue must be explicit")
        if not str(self.session_bucket).strip():
            raise ValueError("market path session_bucket is required")
        if self.source_sequence < 0 or self.series_sequence < 0:
            raise ValueError("source and series sequences must not be negative")
        if self.source_sequence != self.series_sequence:
            raise ValueError("source_sequence must equal series_sequence")
        if self.sequence_epoch <= 0:
            raise ValueError("sequence_epoch must be positive")
        if self.dropped_message_count < 0:
            raise ValueError("dropped_message_count must not be negative")
        if not str(self.detector_version).strip():
            raise ValueError("detector_version is required")
        exchange_ts = _parse_aware_timestamp(
            self.exchange_timestamp, field_name="exchange_timestamp"
        )
        receive_ts = _parse_aware_timestamp(
            self.local_receive_timestamp, field_name="local_receive_timestamp"
        )
        started_ts = _parse_aware_timestamp(
            self.capture_started_at, field_name="capture_started_at"
        )
        event_ts = _parse_aware_timestamp(
            self.event_detected_at, field_name="event_detected_at"
        )
        ended_ts = (
            None
            if self.capture_ended_at is None
            else _parse_aware_timestamp(
                self.capture_ended_at, field_name="capture_ended_at"
            )
        )
        if receive_ts < exchange_ts:
            raise ValueError(
                "local_receive_timestamp must not precede exchange_timestamp"
            )
        if event_ts < started_ts:
            raise ValueError("event_detected_at must not precede capture_started_at")
        if exchange_ts < started_ts:
            raise ValueError("exchange_timestamp must not precede capture_started_at")
        if ended_ts is not None and ended_ts < exchange_ts:
            raise ValueError("capture_ended_at must not precede the point timestamp")
        _validate_positive_optional(self.trade_price, field_name="trade_price")
        _validate_positive_optional(self.best_bid, field_name="best_bid")
        _validate_positive_optional(self.best_ask, field_name="best_ask")
        if self.trade_qty is not None and self.trade_qty < 0:
            raise ValueError("trade_qty must not be negative")
        if self.bid_depth is not None and self.bid_depth < 0:
            raise ValueError("bid_depth must not be negative")
        if self.ask_depth is not None and self.ask_depth < 0:
            raise ValueError("ask_depth must not be negative")
        if self.quote_age_ms is not None and self.quote_age_ms < 0:
            raise ValueError("quote_age_ms must not be negative")
        if (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_ask < self.best_bid
        ):
            raise ValueError("best_ask must not be below best_bid")
        if all(
            value is None for value in (self.trade_price, self.best_bid, self.best_ask)
        ):
            raise ValueError("market path point requires trade or quote evidence")
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
                **MARKET_PATH_METRIC_CONTRACT,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class MarketStreamPoint:
    """One compact canonical row for one accepted market-data sequence."""

    symbol: str
    exchange_timestamp: str
    local_receive_timestamp: str
    source_sequence: int
    sequence_epoch: int
    series_sequence: int
    venue: str
    session_bucket: str
    realtime_type: str
    trade_price: float | None = None
    trade_qty: int | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    bid_depth: int | None = None
    ask_depth: int | None = None
    quote_age_ms: float | None = None
    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    path_order_status: str = "accept"
    path_consumer_eligible: bool = True
    exchange_timestamp_regression_ms: int = 0
    schema: str = MARKET_STREAM_SCHEMA

    def __post_init__(self) -> None:
        symbol = normalize_symbol(self.symbol)
        venue = normalize_venue(self.venue)
        if not symbol or venue == "UNKNOWN" or not self.session_bucket:
            raise ValueError("canonical stream requires symbol, venue, and session")
        if self.source_sequence < 0 or self.source_sequence != self.series_sequence:
            raise ValueError("canonical stream sequences must be nonnegative and equal")
        if self.sequence_epoch <= 0:
            raise ValueError("canonical stream sequence_epoch must be positive")
        if not self.realtime_type:
            raise ValueError("canonical stream realtime_type is required")
        exchange_ts = _parse_aware_timestamp(
            self.exchange_timestamp, field_name="exchange_timestamp"
        )
        receive_ts = _parse_aware_timestamp(
            self.local_receive_timestamp, field_name="local_receive_timestamp"
        )
        if receive_ts < exchange_ts:
            raise ValueError("receive timestamp must not precede exchange timestamp")
        _validate_positive_optional(self.trade_price, field_name="trade_price")
        _validate_positive_optional(self.best_bid, field_name="best_bid")
        _validate_positive_optional(self.best_ask, field_name="best_ask")
        for name in ("trade_qty", "bid_depth", "ask_depth"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.quote_age_ms is not None and self.quote_age_ms < 0:
            raise ValueError("quote_age_ms must not be negative")
        validate_market_stream_path_provenance(
            path_order_status=self.path_order_status,
            path_consumer_eligible=self.path_consumer_eligible,
            exchange_timestamp_regression_ms=(self.exchange_timestamp_regression_ms),
        )
        if (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_ask < self.best_bid
        ):
            raise ValueError("best_ask must not be below best_bid")
        if all(
            value is None for value in (self.trade_price, self.best_bid, self.best_ask)
        ):
            raise ValueError("canonical stream requires trade or quote evidence")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "aggressor_side", AggressorSide(self.aggressor_side))

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["aggressor_side"] = self.aggressor_side.value
        payload.update(
            {
                "metric_contract_id": MARKET_STREAM_CONTRACT_ID,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "trading_runtime_effect": False,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class MarketDepthPoint:
    """Compact 0D snapshot kept separate from the canonical 0B stream."""

    symbol: str
    exchange_timestamp: str
    local_receive_timestamp: str
    source_sequence: int
    sequence_epoch: int
    series_sequence: int
    venue: str
    session_bucket: str
    item: str
    orderbook_time_raw: str
    best_bid: float
    best_ask: float
    best_bid_qty: int
    best_ask_qty: int
    bid_depth: int
    ask_depth: int
    bid_levels: tuple[tuple[int, float, int], ...]
    ask_levels: tuple[tuple[int, float, int], ...]
    route_depth_totals: dict[str, dict[str, int | None]]
    realtime_type: str = "0D"
    schema: str = MARKET_DEPTH_SCHEMA

    def __post_init__(self) -> None:
        symbol = normalize_symbol(self.symbol)
        venue = normalize_venue(self.venue)
        if not symbol or venue == "UNKNOWN" or not self.session_bucket:
            raise ValueError("depth stream requires symbol, venue, and session")
        if not str(self.item).strip():
            raise ValueError("depth stream item is required")
        if self.realtime_type != "0D":
            raise ValueError("depth stream accepts only Kiwoom 0D")
        if self.source_sequence <= 0 or self.source_sequence != self.series_sequence:
            raise ValueError("depth stream sequences must be positive and equal")
        if self.sequence_epoch <= 0:
            raise ValueError("depth stream sequence_epoch must be positive")
        exchange_ts = _parse_aware_timestamp(
            self.exchange_timestamp, field_name="exchange_timestamp"
        )
        receive_ts = _parse_aware_timestamp(
            self.local_receive_timestamp, field_name="local_receive_timestamp"
        )
        if receive_ts < exchange_ts:
            raise ValueError("depth receive timestamp must not precede exchange time")
        _validate_positive_optional(self.best_bid, field_name="best_bid")
        _validate_positive_optional(self.best_ask, field_name="best_ask")
        if self.best_ask < self.best_bid:
            raise ValueError("depth best_ask must not be below best_bid")
        for name in ("best_bid_qty", "best_ask_qty", "bid_depth", "ask_depth"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        for side_name, levels in (
            ("bid_levels", self.bid_levels),
            ("ask_levels", self.ask_levels),
        ):
            if not levels:
                raise ValueError(f"{side_name} must not be empty")
            for level, price, quantity in levels:
                if level <= 0 or price <= 0 or quantity < 0:
                    raise ValueError(f"{side_name} contains an invalid level")
            if tuple(row[0] for row in levels) != tuple(range(1, len(levels) + 1)):
                raise ValueError(
                    f"{side_name} must start at level one and be contiguous"
                )
        if any(
            left[1] >= right[1]
            for left, right in zip(self.ask_levels, self.ask_levels[1:], strict=False)
        ):
            raise ValueError("ask prices must increase by level")
        if any(
            left[1] <= right[1]
            for left, right in zip(self.bid_levels, self.bid_levels[1:], strict=False)
        ):
            raise ValueError("bid prices must decrease by level")
        if self.ask_depth < sum(row[2] for row in self.ask_levels):
            raise ValueError("ask depth must cover retained ask levels")
        if self.bid_depth < sum(row[2] for row in self.bid_levels):
            raise ValueError("bid depth must cover retained bid levels")
        combined_totals = self.route_depth_totals.get("combined")
        if not isinstance(combined_totals, dict):
            raise ValueError("combined route depth totals are required")
        if (
            combined_totals.get("bid") != self.bid_depth
            or combined_totals.get("ask") != self.ask_depth
        ):
            raise ValueError("combined route totals conflict with depth fields")
        for totals in self.route_depth_totals.values():
            if not isinstance(totals, dict):
                raise ValueError("route depth totals must be objects")
            for quantity in totals.values():
                if quantity is not None and quantity < 0:
                    raise ValueError("route depth total must not be negative")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "venue", venue)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "metric_contract_id": MARKET_DEPTH_CONTRACT_ID,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "trading_runtime_effect": False,
            }
        )
        return payload


PathJournalPoint = MarketPathPoint | MarketStreamPoint | MarketDepthPoint


@dataclass(frozen=True, slots=True)
class PathWriterMetrics:
    journal_queue_depth: int
    journal_write_latency_ms: float
    journal_dropped_envelopes: int
    journal_writer_restart_count: int
    journal_writer_error_count: int
    capture_degraded: bool
    last_persisted_sequence: int | None
    last_persisted_sequence_by_series: dict[str, dict[str, int]]
    persisted_envelope_count: int
    queue_high_water: int
    journal_queue_full_count: int
    journal_flush_latency_ms: float
    journal_fsync_latency_ms: float
    bytes_written: int
    disk_free_bytes: int | None
    low_disk_watermark_breached: bool
    storage_self_disabled: bool
    writer_alive: bool
    last_writer_error_type: str | None
    journal_rotation_count: int
    journal_shard_count: int
    journal_active_shard_index: int
    journal_manifest_error_count: int
    journal_partition_bytes: int
    journal_projected_partition_bytes: int | None
    journal_projection_breach_count: int


@dataclass(frozen=True, slots=True)
class PathStoragePolicy:
    """Writer-thread-only disk guard for one daily venue/session partition.

    ``max_partition_bytes`` is retained as the public configuration name for
    compatibility, but it is enforced per JSONL shard.  The partition remains
    bounded by ``max_partition_shards`` and the existing disk watermarks.
    """

    max_partition_bytes: int = 512 * 1024 * 1024
    low_disk_watermark_bytes: int = 5 * 1024 * 1024 * 1024
    critical_disk_watermark_bytes: int = 1 * 1024 * 1024 * 1024
    retention_days: int = 14
    compression_after_days: int = 1
    max_open_segments: int = 2_000
    max_partition_shards: int = 8
    max_partition_total_bytes: int = 4 * 1024 * 1024 * 1024
    max_projected_partition_bytes: int = 2 * 1024 * 1024 * 1024
    projection_horizon_sec: int = 6 * 60 * 60 + 30 * 60
    projection_min_elapsed_sec: int = 5 * 60

    def __post_init__(self) -> None:
        if self.max_partition_bytes <= 0:
            raise ValueError("max_partition_bytes must be positive")
        if self.critical_disk_watermark_bytes < 0:
            raise ValueError("critical_disk_watermark_bytes must not be negative")
        if self.low_disk_watermark_bytes < self.critical_disk_watermark_bytes:
            raise ValueError("low disk watermark must not be below critical watermark")
        if self.retention_days <= 0 or self.compression_after_days < 0:
            raise ValueError("retention/compression days are invalid")
        if self.max_open_segments <= 0:
            raise ValueError("max_open_segments must be positive")
        if self.max_partition_shards <= 0:
            raise ValueError("max_partition_shards must be positive")
        if self.max_partition_total_bytes < self.max_partition_bytes:
            raise ValueError("partition total bytes must cover at least one shard")
        if self.max_projected_partition_bytes <= 0:
            raise ValueError("projected partition byte limit must be positive")
        if self.projection_horizon_sec <= 0 or self.projection_min_elapsed_sec <= 0:
            raise ValueError("projection timing must be positive")

    def partition_path(
        self,
        root: Path,
        *,
        trade_date: str,
        venue: str,
        session_bucket: str,
    ) -> Path:
        safe_session = "".join(
            character
            for character in str(session_bucket).upper()
            if character.isalnum() or character in {"_", "-"}
        )
        normalized_venue = normalize_venue(venue)
        if normalized_venue == "UNKNOWN" or not safe_session:
            raise ValueError("explicit venue and session_bucket are required")
        date.fromisoformat(trade_date)
        return (
            Path(root)
            / f"trade_date={trade_date}"
            / f"venue={normalized_venue}"
            / f"session={safe_session}"
            / "market_path.jsonl"
        )

    def shard_path(self, partition_path: Path, shard_index: int) -> Path:
        if shard_index < 0 or shard_index >= self.max_partition_shards:
            raise ValueError("shard_index is outside the configured partition bound")
        path = Path(partition_path)
        if shard_index == 0:
            return path
        return path.with_name(f"{path.stem}.part-{shard_index:06d}{path.suffix}")

    def manifest_path(self, partition_path: Path) -> Path:
        path = Path(partition_path)
        return path.with_name(f"{path.stem}.manifest.json")

    def stream_partition_path(
        self,
        root: Path,
        *,
        trade_date: str,
        venue: str,
        session_bucket: str,
    ) -> Path:
        return self.partition_path(
            root,
            trade_date=trade_date,
            venue=venue,
            session_bucket=session_bucket,
        ).with_name("market_stream.jsonl")

    def depth_partition_path(
        self,
        root: Path,
        *,
        trade_date: str,
        venue: str,
        session_bucket: str,
    ) -> Path:
        return self.partition_path(
            root,
            trade_date=trade_date,
            venue=venue,
            session_bucket=session_bucket,
        ).with_name("market_depth_stream.jsonl")


def partition_maintenance_lock_path(partition_path: Path) -> Path:
    """Return the external lock shared by writers and closed-date maintenance."""

    path = Path(partition_path).absolute()
    trade_dir = next(
        (
            candidate
            for candidate in (path, *path.parents)
            if candidate.name.startswith("trade_date=")
        ),
        None,
    )
    if trade_dir is None:
        return path.parent / ".partition_maintenance_locks" / f"{path.name}.lock"
    date.fromisoformat(trade_dir.name.removeprefix("trade_date="))
    return (
        trade_dir.parent / ".partition_maintenance_locks" / (f"{trade_dir.name}.lock")
    )


@contextmanager
def partition_maintenance_lock(
    partition_path: Path,
    *,
    blocking: bool = True,
    exclusive: bool = False,
) -> Iterable[None]:
    """Hold the date-partition lock before opening any journal shard."""

    lock_path = partition_maintenance_lock_path(partition_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o640)
    operation = (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | (
        0 if blocking else fcntl.LOCK_NB
    )
    try:
        fcntl.flock(descriptor, operation)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


class NonBlockingPathJournalWriter:
    """Bounded queue and dedicated durable writer.

    ``submit`` never waits. A full queue records a drop and returns ``False``.
    Shutdown may wait while the already accepted queue is drained.
    """

    def __init__(
        self,
        path: Path,
        *,
        max_queue_size: int = 10_000,
        max_batch_size: int = 256,
        flush_interval_sec: float = 0.25,
        storage_policy: PathStoragePolicy | None = None,
    ) -> None:
        if max_queue_size <= 0 or max_batch_size <= 0:
            raise ValueError("queue and batch sizes must be positive")
        if flush_interval_sec <= 0:
            raise ValueError("flush_interval_sec must be positive")
        self._path = Path(path)
        self._queue: queue.Queue[PathJournalPoint] = queue.Queue(maxsize=max_queue_size)
        self._max_batch_size = max_batch_size
        self._flush_interval_sec = flush_interval_sec
        self._storage_policy = storage_policy or PathStoragePolicy()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_requested = threading.Event()
        self._accepting = False
        self._last_latency_ms = 0.0
        self._dropped = 0
        self._writer_restarts = 0
        self._writer_errors = 0
        self._capture_degraded = False
        self._last_sequence: int | None = None
        self._last_sequence_by_series: dict[str, dict[str, int]] = {}
        self._persisted = 0
        self._queue_high_water = 0
        self._queue_full = 0
        self._last_flush_latency_ms = 0.0
        self._last_fsync_latency_ms = 0.0
        self._bytes_written = 0
        self._disk_free_bytes: int | None = None
        self._low_disk_watermark_breached = False
        self._storage_self_disabled = False
        self._last_order_by_segment: dict[str, tuple[datetime, int]] = {}
        self._last_writer_error_type: str | None = None
        self._active_shard_index = 0
        self._shard_count = 0
        self._rotations = 0
        self._manifest_errors = 0
        self._partition_bytes = 0
        self._projected_partition_bytes: int | None = None
        self._projection_breaches = 0
        self._first_write_monotonic: float | None = None

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            if self._thread is not None:
                self._writer_restarts += 1
            with partition_maintenance_lock(self._path):
                shard_paths = readable_partition_path_files(self._path)
            if shard_paths:
                last_logical = (
                    shard_paths[-1].with_suffix("")
                    if shard_paths[-1].suffix == ".gz"
                    else shard_paths[-1]
                )
                self._active_shard_index = _shard_index(self._path, last_logical)
                self._shard_count = len(shard_paths)
                self._partition_bytes = sum(path.stat().st_size for path in shard_paths)
            else:
                self._active_shard_index = 0
                self._shard_count = 0
            self._stop_requested.clear()
            self._accepting = True
            self._thread = threading.Thread(
                target=self._run,
                name="micro-reversion-path-writer",
                daemon=True,
            )
            self._thread.start()

    def submit(self, point: PathJournalPoint) -> bool:
        with self._lock:
            if not self._accepting:
                raise RuntimeError("path journal writer is not running")
            if self._storage_self_disabled:
                self._dropped += 1
                self._capture_degraded = True
                return False
            try:
                self._queue.put_nowait(point)
            except queue.Full:
                self._dropped += 1
                self._queue_full += 1
                self._capture_degraded = True
                return False
            self._queue_high_water = max(self._queue_high_water, self._queue.qsize())
        return True

    def close(self, *, timeout_sec: float = 10.0) -> None:
        self.request_close()
        self.wait_closed(timeout_sec=timeout_sec)

    def request_close(self) -> None:
        """Stop accepting rows and ask the writer to drain its accepted queue."""

        with self._lock:
            self._accepting = False
            self._stop_requested.set()

    def wait_closed(self, *, timeout_sec: float = 10.0) -> None:
        """Wait for a previously requested drain without changing acceptance."""

        with self._lock:
            thread = self._thread
        if thread is None:
            return
        thread.join(timeout=max(0.01, timeout_sec))
        if thread.is_alive():
            raise TimeoutError("path journal writer did not stop in time")

    def metrics(self) -> PathWriterMetrics:
        with self._lock:
            return PathWriterMetrics(
                journal_queue_depth=self._queue.qsize(),
                journal_write_latency_ms=round(self._last_latency_ms, 6),
                journal_dropped_envelopes=self._dropped,
                journal_writer_restart_count=self._writer_restarts,
                journal_writer_error_count=self._writer_errors,
                capture_degraded=self._capture_degraded,
                last_persisted_sequence=self._last_sequence,
                last_persisted_sequence_by_series={
                    key: dict(value)
                    for key, value in self._last_sequence_by_series.items()
                },
                persisted_envelope_count=self._persisted,
                queue_high_water=self._queue_high_water,
                journal_queue_full_count=self._queue_full,
                journal_flush_latency_ms=round(self._last_flush_latency_ms, 6),
                journal_fsync_latency_ms=round(self._last_fsync_latency_ms, 6),
                bytes_written=self._bytes_written,
                disk_free_bytes=self._disk_free_bytes,
                low_disk_watermark_breached=(self._low_disk_watermark_breached),
                storage_self_disabled=self._storage_self_disabled,
                writer_alive=(self._thread is not None and self._thread.is_alive()),
                last_writer_error_type=self._last_writer_error_type,
                journal_rotation_count=self._rotations,
                journal_shard_count=self._shard_count,
                journal_active_shard_index=self._active_shard_index,
                journal_manifest_error_count=self._manifest_errors,
                journal_partition_bytes=self._partition_bytes,
                journal_projected_partition_bytes=self._projected_partition_bytes,
                journal_projection_breach_count=self._projection_breaches,
            )

    def _run(self) -> None:
        batch: list[PathJournalPoint] = []
        stopping = False
        manifest_needs_refresh = not self._storage_policy.manifest_path(
            self._path
        ).exists()
        while not stopping:
            try:
                item = self._queue.get(timeout=self._flush_interval_sec)
            except queue.Empty:
                item = None
                if self._stop_requested.is_set():
                    stopping = True
            if isinstance(item, (MarketPathPoint, MarketStreamPoint, MarketDepthPoint)):
                batch.append(item)
                self._queue.task_done()
                if self._stop_requested.is_set() and self._queue.empty():
                    stopping = True
            if batch and (
                stopping or item is None or len(batch) >= self._max_batch_size
            ):
                started = time.monotonic()
                try:
                    next_order = _validate_batch_order(
                        tuple(batch), previous_by_segment=self._last_order_by_segment
                    )
                    disk_free = self._disk_free_space()
                    with self._lock:
                        self._disk_free_bytes = disk_free
                    if disk_free < self._storage_policy.critical_disk_watermark_bytes:
                        with self._lock:
                            self._storage_self_disabled = True
                        raise OSError("critical disk watermark reached")
                    projected_bytes = _encoded_size(batch)
                    if projected_bytes > self._storage_policy.max_partition_bytes:
                        raise OSError("batch exceeds path shard size limit")
                    if (
                        self._partition_bytes + projected_bytes
                        > self._storage_policy.max_partition_total_bytes
                    ):
                        with self._lock:
                            self._storage_self_disabled = True
                        raise OSError("path partition total byte limit reached")
                    with partition_maintenance_lock(self._path):
                        active_path = self._storage_policy.shard_path(
                            self._path, self._active_shard_index
                        )
                        # Maintenance may have compressed the last closed
                        # shard while this long-lived writer was idle. Never
                        # recreate that logical index beside its gzip. Advance
                        # to a new shard and refresh a mixed gzip/plain manifest
                        # while still holding the shared partition lock.
                        if (
                            not active_path.exists()
                            and active_path.with_suffix(
                                f"{active_path.suffix}.gz"
                            ).exists()
                        ):
                            active_path = self._advance_shard_locked()
                            manifest_needs_refresh = True
                        existing_bytes = (
                            active_path.stat().st_size if active_path.exists() else 0
                        )
                        if (
                            existing_bytes + projected_bytes
                            > self._storage_policy.max_partition_bytes
                        ):
                            active_path = self._advance_shard_locked()
                            manifest_needs_refresh = True
                        write_metrics = _append_market_path_points_locked(
                            active_path,
                            batch,
                        )
                        if manifest_needs_refresh:
                            manifest_needs_refresh = not self._refresh_manifest(
                                partition_lock_held=True
                            )
                    if write_metrics is None:
                        write_metrics = PathAppendMetrics(0, 0.0, 0.0)
                except Exception as exc:
                    with self._lock:
                        self._writer_errors += 1
                        self._last_writer_error_type = exc.__class__.__name__
                        self._capture_degraded = True
                        self._dropped += len(batch)
                else:
                    with self._lock:
                        self._last_sequence = batch[-1].source_sequence
                        for point in batch:
                            series_key = "|".join(
                                (
                                    point.symbol,
                                    point.venue,
                                    point.session_bucket,
                                )
                            )
                            self._last_sequence_by_series[series_key] = {
                                "sequence_epoch": point.sequence_epoch,
                                "series_sequence": point.series_sequence,
                            }
                        self._persisted += len(batch)
                        self._last_flush_latency_ms = write_metrics.flush_latency_ms
                        self._last_fsync_latency_ms = write_metrics.fsync_latency_ms
                        self._bytes_written += write_metrics.bytes_written
                        self._partition_bytes += write_metrics.bytes_written
                        if self._first_write_monotonic is None:
                            self._first_write_monotonic = started
                        self._shard_count = max(
                            self._shard_count, self._active_shard_index + 1
                        )
                        self._last_order_by_segment = next_order
                        if disk_free < self._storage_policy.low_disk_watermark_bytes:
                            # A successful durable write below the preventive
                            # watermark is a capacity warning, not evidence of
                            # lost capture.  Critical capacity, write errors,
                            # queue loss, and projection shutdown remain
                            # capture-degrading paths above/below this branch.
                            self._low_disk_watermark_breached = True
                        elapsed = time.monotonic() - self._first_write_monotonic
                        if elapsed >= self._storage_policy.projection_min_elapsed_sec:
                            projected_total = round(
                                self._bytes_written
                                / elapsed
                                * self._storage_policy.projection_horizon_sec
                            )
                            self._projected_partition_bytes = projected_total
                            if (
                                projected_total
                                > self._storage_policy.max_projected_partition_bytes
                                and not self._storage_self_disabled
                            ):
                                self._projection_breaches += 1
                                self._storage_self_disabled = True
                                self._capture_degraded = True
                finally:
                    latency_ms = (time.monotonic() - started) * 1_000.0
                    with self._lock:
                        self._last_latency_ms = latency_ms
                    batch.clear()
        if self._shard_count > 0:
            self._refresh_manifest()

    def _advance_shard_locked(self) -> Path:
        next_index = self._active_shard_index + 1
        if next_index >= self._storage_policy.max_partition_shards:
            with self._lock:
                self._storage_self_disabled = True
            raise OSError("path partition shard limit reached")
        next_path = self._storage_policy.shard_path(self._path, next_index)
        next_gzip = next_path.with_suffix(f"{next_path.suffix}.gz")
        if next_path.exists() or next_gzip.exists():
            raise OSError("next path shard already exists")
        with self._lock:
            self._active_shard_index = next_index
            self._rotations += 1
        return next_path

    def _refresh_manifest(self, *, partition_lock_held: bool = False) -> bool:
        try:
            write_market_path_manifest(
                self._path,
                storage_policy=self._storage_policy,
                active_shard_index=self._active_shard_index,
                _partition_lock_held=partition_lock_held,
            )
        except Exception as exc:
            with self._lock:
                self._manifest_errors += 1
                self._capture_degraded = True
                self._last_writer_error_type = exc.__class__.__name__
            return False
        return True

    def _disk_free_space(self) -> int:
        target = self._path.parent
        while not target.exists() and target != target.parent:
            target = target.parent
        return shutil.disk_usage(target).free


@dataclass(frozen=True, slots=True)
class PathAppendMetrics:
    bytes_written: int
    flush_latency_ms: float
    fsync_latency_ms: float


def append_market_path_points(
    path: Path, points: Iterable[PathJournalPoint]
) -> PathAppendMetrics:
    materialized = tuple(points)
    if not materialized:
        return PathAppendMetrics(0, 0.0, 0.0)
    with partition_maintenance_lock(path):
        return _append_market_path_points_locked(Path(path), materialized)


def _append_market_path_points_locked(
    path: Path,
    points: Iterable[PathJournalPoint],
) -> PathAppendMetrics:
    materialized = tuple(points)
    _validate_batch_order(materialized)
    encoded = b"".join(
        (json.dumps(point.as_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        for point in materialized
    )
    target = Path(path)
    _assert_no_symlink_ancestors(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_ancestors(target)
    descriptor = _open_append_regular_nofollow(target, allow_create=True)
    write_started = time.monotonic()
    fsync_latency_ms = 0.0
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        remaining = memoryview(encoded)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("market path append made no progress")
            remaining = remaining[written:]
        fsync_started = time.monotonic()
        os.fsync(descriptor)
        _assert_open_descriptor_matches_path(descriptor, target)
        fsync_latency_ms = (time.monotonic() - fsync_started) * 1_000.0
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
    return PathAppendMetrics(
        bytes_written=len(encoded),
        flush_latency_ms=(time.monotonic() - write_started) * 1_000.0,
        fsync_latency_ms=fsync_latency_ms,
    )


def _open_append_regular_nofollow(path: Path, *, allow_create: bool) -> int:
    _assert_no_symlink_ancestors(path)
    if path.is_symlink():
        raise OSError(f"journal target symlink is forbidden: {path}")
    if path.exists() and not path.is_file():
        raise OSError(f"journal target must be a regular file: {path}")
    flags = (
        os.O_APPEND
        | os.O_WRONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    if allow_create:
        flags |= os.O_CREAT
    descriptor = os.open(path, flags, 0o640)
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        raise OSError(f"journal target must be a regular file: {path}")
    return descriptor


def _assert_open_descriptor_matches_path(descriptor: int, path: Path) -> None:
    _assert_no_symlink_ancestors(path)
    opened = os.fstat(descriptor)
    current = path.lstat()
    if (
        not stat.S_ISREG(current.st_mode)
        or opened.st_dev != current.st_dev
        or opened.st_ino != current.st_ino
    ):
        raise OSError(f"journal target changed during append: {path}")


def _assert_no_symlink_ancestors(path: Path) -> None:
    absolute = Path(path).absolute()
    for ancestor in reversed(absolute.parents):
        if ancestor.is_symlink():
            raise OSError(f"path ancestor symlink is forbidden: {ancestor}")
        if ancestor.exists() and not ancestor.is_dir():
            raise OSError(f"path ancestor must be a directory: {ancestor}")


def partition_path_files(partition_path: Path) -> tuple[Path, ...]:
    """Return the legacy base file followed by validated rotated shards."""

    base = Path(partition_path)
    _assert_no_symlink_ancestors(base)
    indexed: list[tuple[int, Path]] = []
    if base.exists() or base.is_symlink():
        _assert_regular_partition_file(base)
        indexed.append((0, base))
    pattern = f"{base.stem}.part-*{base.suffix}"
    for candidate in base.parent.glob(pattern):
        _assert_regular_partition_file(candidate)
        index = _shard_index(base, candidate)
        if index > 0:
            indexed.append((index, candidate))
    indexed.sort(key=lambda item: item[0])
    for expected, (actual, _path) in enumerate(indexed):
        if actual != expected:
            raise ValueError("market path shard sequence is not contiguous")
    return tuple(path for _index, path in indexed)


def readable_partition_path_files(partition_path: Path) -> tuple[Path, ...]:
    """Discover one contiguous partition from plain or post-session gzip shards."""

    base = Path(partition_path)
    _assert_no_symlink_ancestors(base)
    indexed: dict[int, Path] = {}
    candidates: list[Path] = []
    if base.exists() or base.is_symlink():
        candidates.append(base)
    compressed_base = base.with_suffix(f"{base.suffix}.gz")
    if compressed_base.exists() or compressed_base.is_symlink():
        candidates.append(compressed_base)
    candidates.extend(base.parent.glob(f"{base.stem}.part-*{base.suffix}"))
    candidates.extend(base.parent.glob(f"{base.stem}.part-*{base.suffix}.gz"))
    for candidate in candidates:
        _assert_regular_partition_file(candidate)
        logical = candidate.with_suffix("") if candidate.suffix == ".gz" else candidate
        index = _shard_index(base, logical)
        if index in indexed:
            raise ValueError("plain and compressed copies overlap for one path shard")
        indexed[index] = candidate
    ordered = sorted(indexed.items())
    for expected, (actual, _path) in enumerate(ordered):
        if actual != expected:
            raise ValueError("readable market stream shard sequence is not contiguous")
    return tuple(path for _index, path in ordered)


def _assert_regular_partition_file(path: Path) -> None:
    if path.is_symlink():
        raise OSError(f"path partition shard symlink is forbidden: {path}")
    if not path.is_file():
        raise OSError(f"path partition shard must be a regular file: {path}")


def write_market_path_manifest(
    partition_path: Path,
    *,
    storage_policy: PathStoragePolicy,
    active_shard_index: int,
    _partition_lock_held: bool = False,
) -> Path:
    """Atomically publish a discoverable manifest for all JSONL shards."""

    if not _partition_lock_held:
        with partition_maintenance_lock(partition_path):
            return write_market_path_manifest(
                partition_path,
                storage_policy=storage_policy,
                active_shard_index=active_shard_index,
                _partition_lock_held=True,
            )

    base = Path(partition_path)
    shards = readable_partition_path_files(base)
    if not shards:
        raise ValueError("cannot write a manifest without path shards")
    last_logical = (
        shards[-1].with_suffix("") if shards[-1].suffix == ".gz" else shards[-1]
    )
    if _shard_index(base, last_logical) != active_shard_index:
        raise ValueError("active shard does not match discovered shard sequence")
    payload = {
        "schema": MARKET_PATH_MANIFEST_SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "logical_path": base.name,
        "active_shard_index": active_shard_index,
        "max_shard_bytes": storage_policy.max_partition_bytes,
        "max_partition_shards": storage_policy.max_partition_shards,
        "max_partition_total_bytes": storage_policy.max_partition_total_bytes,
        "max_projected_partition_bytes": (storage_policy.max_projected_partition_bytes),
        "projection_horizon_sec": storage_policy.projection_horizon_sec,
        "shards": [
            {
                "index": _shard_index(
                    base,
                    shard.with_suffix("") if shard.suffix == ".gz" else shard,
                ),
                "file": shard.name,
                "bytes": shard.stat().st_size,
                "compressed": shard.suffix == ".gz",
            }
            for shard in shards
        ],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "row_schema": (
            MARKET_DEPTH_SCHEMA
            if base.name.startswith("market_depth_stream")
            else (
                MARKET_STREAM_SCHEMA
                if base.name.startswith("market_stream")
                else MARKET_PATH_SCHEMA
            )
        ),
        "metric_contract_id": (
            MARKET_DEPTH_CONTRACT_ID
            if base.name.startswith("market_depth_stream")
            else (
                MARKET_STREAM_CONTRACT_ID
                if base.name.startswith("market_stream")
                else "scalp_micro_reversion_market_path_contract_v6"
            )
        ),
        **(
            MARKET_DEPTH_METRIC_CONTRACT
            if base.name.startswith("market_depth_stream")
            else (
                MARKET_STREAM_METRIC_CONTRACT
                if base.name.startswith("market_stream")
                else MARKET_PATH_METRIC_CONTRACT
            )
        ),
    }
    target = storage_policy.manifest_path(base)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, target)
        directory_descriptor = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def _shard_index(base: Path, candidate: Path) -> int:
    if candidate == base:
        return 0
    prefix = f"{base.stem}.part-"
    name = candidate.name
    if not name.startswith(prefix) or not name.endswith(base.suffix):
        raise ValueError("path is not a shard of the requested partition")
    raw_index = name[len(prefix) : -len(base.suffix)]
    if len(raw_index) != 6 or not raw_index.isdigit():
        raise ValueError("path shard index must use six decimal digits")
    return int(raw_index)


def _validate_batch_order(
    points: tuple[PathJournalPoint, ...],
    *,
    previous_by_segment: dict[str, tuple[datetime, int]] | None = None,
) -> dict[str, tuple[datetime, int]]:
    last_by_segment = dict(previous_by_segment or {})
    for point in points:
        key = (
            point.path_segment_id
            if isinstance(point, MarketPathPoint)
            else "|".join(
                (
                    point.symbol,
                    point.venue,
                    point.session_bucket,
                    str(point.sequence_epoch),
                )
            )
        )
        order_timestamp = (
            point.local_receive_timestamp
            if isinstance(point, MarketDepthPoint)
            else point.exchange_timestamp
        )
        current = (
            _parse_aware_timestamp(order_timestamp, field_name="ordering_timestamp"),
            point.source_sequence,
        )
        previous = last_by_segment.get(key)
        if previous is not None:
            sequence_regressed = current[1] <= previous[1]
            timestamp_regressed = (
                isinstance(point, (MarketPathPoint, MarketDepthPoint))
                and current[0] < previous[0]
            )
            if sequence_regressed or timestamp_regressed:
                raise ValueError(
                    "market path points must increase by timestamp and source_sequence"
                )
        last_by_segment[key] = current
    return last_by_segment


def _parse_aware_timestamp(value: str, *, field_name: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed


def _validate_positive_optional(value: float | None, *, field_name: str) -> None:
    if value is not None and value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _encoded_size(points: Iterable[PathJournalPoint]) -> int:
    return sum(
        len(
            (
                json.dumps(point.as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            ).encode("utf-8")
        )
        for point in points
    )
