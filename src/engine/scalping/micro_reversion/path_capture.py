"""Worker-side pre-event buffering and parent-wave path coalescing.

Nothing in this module is imported by the market-data producer.  It operates
on immutable envelopes already accepted by the bounded observation queue.
"""

from __future__ import annotations

import hashlib
import fcntl
import gzip
import io
import json
import os
import stat
import threading
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .multi_horizon import MultiHorizonShockEvent
from .observation_adapter import RawMarketObservation
from .path_journal import (
    AggressorSide,
    MarketPathPoint,
    MarketStreamPoint,
    _assert_no_symlink_ancestors,
    _assert_open_descriptor_matches_path,
    _open_append_regular_nofollow,
    partition_maintenance_lock,
    readable_partition_path_files,
)

PATH_REFERENCE_SCHEMA = "scalp_micro_reversion_path_event_reference_v2"
PATH_CAPTURE_AUTHORITY = "forward_path_observation_only_no_policy_selection"
PATH_CAPTURE_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_path_coverage",
    "decision_authority": PATH_CAPTURE_AUTHORITY,
    "window_policy": "bounded_30s_pre_event_through_180s_post_event_parent_wave",
    "sample_floor": "five_trading_days_and_200_mature_events_collector_health_only",
    "primary_decision_metric": "pre_active_post_path_coverage_pct",
    "source_quality_gate": (
        "monotonic_source_sequence_and_one_segment_per_parent_wave"
    ),
    "forbidden_uses": (
        "child_event_double_counting",
        "sim_or_live_policy_selection",
        "broker_order_submission",
        "touch_as_real_fill",
        "threshold_or_provider_or_bot_mutation",
    ),
}


class PathPhase(StrEnum):
    PRE_EVENT = "PRE_EVENT"
    ACTIVE_EVENT = "ACTIVE_EVENT"
    POST_EVENT = "POST_EVENT"


class PathEnvelopeOrderStatus(StrEnum):
    ACCEPT = "accept"
    DUPLICATE_SOURCE_SEQUENCE = "duplicate_source_sequence"
    SOURCE_SEQUENCE_REGRESSION = "source_sequence_regression"
    LOCAL_RECEIVE_TIMESTAMP_REGRESSION = "local_receive_timestamp_regression"
    EXCHANGE_TIMESTAMP_REGRESSION_QUARANTINED = (
        "exchange_timestamp_regression_quarantined"
    )
    EXCHANGE_TIMESTAMP_REGRESSION_EXCEEDED = "exchange_timestamp_regression_exceeded"


@dataclass(frozen=True, slots=True)
class PathEnvelopeOrderAssessment:
    status: PathEnvelopeOrderStatus
    exchange_timestamp_regression_ms: int = 0


@dataclass(frozen=True, slots=True)
class PathEventReference:
    parent_wave_id: str
    path_segment_id: str
    shock_event_id: str
    shock_horizon_ms: int
    event_sequence_in_wave: int
    event_detected_at_ms: int
    symbol: str
    venue: str
    session_bucket: str
    sequence_epoch: int
    capture_started_at: str
    segment_event_detected_at_ms: int
    capture_ended_at: str
    schema: str = PATH_REFERENCE_SCHEMA

    def __post_init__(self) -> None:
        if (
            not self.parent_wave_id
            or not self.path_segment_id
            or not self.shock_event_id
        ):
            raise ValueError("parent wave, path segment, and shock event are required")
        if self.shock_horizon_ms <= 0 or self.event_sequence_in_wave <= 0:
            raise ValueError("horizon and event sequence must be positive")
        if not self.symbol or not self.venue or not self.session_bucket:
            raise ValueError("reference stream scope is required")
        if (
            self.sequence_epoch <= 0
            or self.event_detected_at_ms <= 0
            or self.segment_event_detected_at_ms <= 0
        ):
            raise ValueError(
                "reference sequence epoch and event/segment times are required"
            )
        started = _timestamp_ms(self.capture_started_at)
        ended = _timestamp_ms(self.capture_ended_at)
        if not started <= self.segment_event_detected_at_ms <= ended:
            raise ValueError("reference capture window is invalid")

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "trading_runtime_effect": False,
            **PATH_CAPTURE_METRIC_CONTRACT,
        }


@dataclass(frozen=True, slots=True)
class PathSegmentRegistration:
    parent_wave_id: str
    path_segment_id: str
    primary_event_id: str
    event_reference: PathEventReference
    segment_created: bool
    pre_event_envelopes: tuple[RawMarketObservation, ...]
    capture_started_at: str


@dataclass(frozen=True, slots=True)
class PathCaptureQualitySnapshot:
    accepted_envelope_count: int
    duplicate_sequence_count: int
    out_of_order_sequence_count: int
    exchange_timestamp_regression_count: int
    exchange_timestamp_regression_quarantined_count: int
    exchange_timestamp_regression_exceeded_count: int
    exchange_timestamp_regression_max_ms: int
    local_receive_timestamp_regression_count: int
    local_receive_timestamp_regression_max_ms: int
    sequence_gap_count: int
    evicted_envelope_count: int
    created_segment_count: int
    coalesced_event_reference_count: int
    pre_event_point_count: int
    active_event_point_count: int
    post_event_point_count: int


class PreEventRingBuffer:
    """Bounded per-series raw envelope history; no persistence or I/O."""

    def __init__(
        self,
        *,
        max_age_ms: int = 30_000,
        max_points_per_series: int = 20_000,
        max_exchange_timestamp_regression_ms: int = 1_000,
    ) -> None:
        if max_age_ms < 20_000 or max_age_ms > 30_000:
            raise ValueError("pre-event max_age_ms must be between 20s and 30s")
        if max_points_per_series <= 0:
            raise ValueError("max_points_per_series must be positive")
        if not 0 <= max_exchange_timestamp_regression_ms <= 1_000:
            raise ValueError(
                "exchange timestamp regression tolerance must be between 0 and 1s"
            )
        self.max_age_ms = max_age_ms
        self.max_points_per_series = max_points_per_series
        self.max_exchange_timestamp_regression_ms = max_exchange_timestamp_regression_ms
        self._points: dict[
            tuple[str, str, str], deque[tuple[int, RawMarketObservation]]
        ] = defaultdict(deque)
        self._last_sequence: dict[tuple[str, str, str], int] = {}
        self._last_timestamp_ms: dict[tuple[str, str, str], int] = {}
        self._last_receive_timestamp_ms: dict[tuple[str, str, str], int] = {}
        self._lock = threading.Lock()
        self._accepted = 0
        self._duplicates = 0
        self._out_of_order = 0
        self._exchange_timestamp_regressions = 0
        self._exchange_timestamp_regressions_quarantined = 0
        self._exchange_timestamp_regressions_exceeded = 0
        self._exchange_timestamp_regression_max_ms = 0
        self._local_receive_timestamp_regressions = 0
        self._local_receive_timestamp_regression_max_ms = 0
        self._gaps = 0
        self._evicted = 0

    def order_status(self, envelope: RawMarketObservation) -> PathEnvelopeOrderStatus:
        """Classify path ordering without mutating buffer state or counters."""

        return self.order_assessment(envelope).status

    def order_assessment(
        self, envelope: RawMarketObservation
    ) -> PathEnvelopeOrderAssessment:
        """Classify ordering and return bounded regression provenance."""

        key = (envelope.symbol, envelope.venue, envelope.session_bucket)
        observed_ms = _timestamp_ms(envelope.exchange_timestamp)
        receive_ms = _timestamp_ms(envelope.local_receive_timestamp)
        with self._lock:
            return self._order_assessment_unlocked(
                key,
                source_sequence=envelope.source_sequence,
                observed_ms=observed_ms,
                receive_ms=receive_ms,
            )

    def add(self, envelope: RawMarketObservation) -> bool:
        key = (envelope.symbol, envelope.venue, envelope.session_bucket)
        observed_ms = _timestamp_ms(envelope.exchange_timestamp)
        receive_ms = _timestamp_ms(envelope.local_receive_timestamp)
        with self._lock:
            assessment = self._order_assessment_unlocked(
                key,
                source_sequence=envelope.source_sequence,
                observed_ms=observed_ms,
                receive_ms=receive_ms,
            )
            status = assessment.status
            if status is PathEnvelopeOrderStatus.DUPLICATE_SOURCE_SEQUENCE:
                self._duplicates += 1
                return False
            if status is PathEnvelopeOrderStatus.SOURCE_SEQUENCE_REGRESSION:
                self._out_of_order += 1
                return False
            if status is PathEnvelopeOrderStatus.LOCAL_RECEIVE_TIMESTAMP_REGRESSION:
                previous_receive_ms = self._last_receive_timestamp_ms[key]
                regression_ms = previous_receive_ms - receive_ms
                self._local_receive_timestamp_regressions += 1
                self._local_receive_timestamp_regression_max_ms = max(
                    self._local_receive_timestamp_regression_max_ms,
                    regression_ms,
                )
                return False
            if status in {
                PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_QUARANTINED,
                PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_EXCEEDED,
            }:
                regression_ms = assessment.exchange_timestamp_regression_ms
                self._exchange_timestamp_regressions += 1
                self._exchange_timestamp_regression_max_ms = max(
                    self._exchange_timestamp_regression_max_ms,
                    regression_ms,
                )
                if (
                    status
                    is PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_QUARANTINED
                ):
                    self._exchange_timestamp_regressions_quarantined += 1
                    # Preserve the source-sequence watermark while keeping the
                    # last trusted exchange timestamp. The raw stream row stays
                    # persisted, but detector/path consumers never see it.
                    self._last_sequence[key] = envelope.source_sequence
                    self._last_receive_timestamp_ms[key] = receive_ms
                else:
                    self._exchange_timestamp_regressions_exceeded += 1
                return False
            previous = self._last_sequence.get(key)
            if previous is not None and envelope.source_sequence > previous + 1:
                self._gaps += envelope.source_sequence - previous - 1
            self._last_sequence[key] = envelope.source_sequence
            self._last_timestamp_ms[key] = observed_ms
            self._last_receive_timestamp_ms[key] = receive_ms
            points = self._points[key]
            points.append((observed_ms, envelope))
            self._accepted += 1
            cutoff = observed_ms - self.max_age_ms
            while points and (
                points[0][0] < cutoff or len(points) > self.max_points_per_series
            ):
                points.popleft()
                self._evicted += 1
            return True

    def _order_assessment_unlocked(
        self,
        key: tuple[str, str, str],
        *,
        source_sequence: int,
        observed_ms: int,
        receive_ms: int,
    ) -> PathEnvelopeOrderAssessment:
        previous = self._last_sequence.get(key)
        if previous is not None:
            if source_sequence == previous:
                return PathEnvelopeOrderAssessment(
                    PathEnvelopeOrderStatus.DUPLICATE_SOURCE_SEQUENCE
                )
            if source_sequence < previous:
                return PathEnvelopeOrderAssessment(
                    PathEnvelopeOrderStatus.SOURCE_SEQUENCE_REGRESSION
                )
        previous_receive_ms = self._last_receive_timestamp_ms.get(key)
        if previous_receive_ms is not None and receive_ms < previous_receive_ms:
            return PathEnvelopeOrderAssessment(
                PathEnvelopeOrderStatus.LOCAL_RECEIVE_TIMESTAMP_REGRESSION
            )
        previous_timestamp_ms = self._last_timestamp_ms.get(key)
        if previous_timestamp_ms is not None and observed_ms < previous_timestamp_ms:
            regression_ms = previous_timestamp_ms - observed_ms
            if regression_ms <= self.max_exchange_timestamp_regression_ms:
                return PathEnvelopeOrderAssessment(
                    PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_QUARANTINED,
                    exchange_timestamp_regression_ms=regression_ms,
                )
            return PathEnvelopeOrderAssessment(
                PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_EXCEEDED,
                exchange_timestamp_regression_ms=regression_ms,
            )
        return PathEnvelopeOrderAssessment(PathEnvelopeOrderStatus.ACCEPT)

    def snapshot_before(
        self,
        *,
        symbol: str,
        venue: str,
        session_bucket: str,
        event_detected_at_ms: int,
    ) -> tuple[RawMarketObservation, ...]:
        key = (symbol, venue, session_bucket)
        cutoff = event_detected_at_ms - self.max_age_ms
        with self._lock:
            return tuple(
                envelope
                for observed_ms, envelope in self._points.get(key, ())
                if cutoff <= observed_ms < event_detected_at_ms
            )

    def counters(
        self,
    ) -> tuple[int, int, int, int, int, int, int, int, int, int, int]:
        with self._lock:
            return (
                self._accepted,
                self._duplicates,
                self._out_of_order,
                self._exchange_timestamp_regressions,
                self._exchange_timestamp_regressions_quarantined,
                self._exchange_timestamp_regressions_exceeded,
                self._exchange_timestamp_regression_max_ms,
                self._local_receive_timestamp_regressions,
                self._local_receive_timestamp_regression_max_ms,
                self._gaps,
                self._evicted,
            )

    def drop_symbol(self, symbol: str) -> int:
        """Discard buffered observations and ordering state for one symbol."""

        with self._lock:
            keys = [key for key in self._points if key[0] == symbol]
            removed = sum(len(self._points[key]) for key in keys)
            for key in keys:
                del self._points[key]
                self._last_sequence.pop(key, None)
                self._last_timestamp_ms.pop(key, None)
                self._last_receive_timestamp_ms.pop(key, None)
            return removed

    def reset_transport_epoch(self) -> int:
        """Discard all pre-reconnect history and ordering watermarks."""

        with self._lock:
            removed = sum(len(points) for points in self._points.values())
            self._points.clear()
            self._last_sequence.clear()
            self._last_timestamp_ms.clear()
            self._last_receive_timestamp_ms.clear()
            return removed


@dataclass(slots=True)
class _SegmentState:
    path_segment_id: str
    primary_event_id: str
    event_ids: set[str]
    symbol: str
    venue: str
    session_bucket: str
    event_detected_at_ms: int
    capture_started_at: str
    active_until_ms: int


class ParentWavePathCoalescer:
    """Create exactly one path segment and many event references per wave."""

    def __init__(
        self,
        ring_buffer: PreEventRingBuffer,
        *,
        post_event_ms: int = 180_000,
        active_event_ms: int = 20_000,
        max_open_segments: int = 2_000,
    ) -> None:
        if (
            post_event_ms <= 0
            or active_event_ms <= 0
            or active_event_ms >= post_event_ms
            or max_open_segments <= 0
        ):
            raise ValueError("capture windows and max_open_segments are invalid")
        self._ring = ring_buffer
        self._post_event_ms = post_event_ms
        self._active_event_ms = active_event_ms
        self._max_open_segments = max_open_segments
        self._segments: dict[str, _SegmentState] = {}
        self._references: list[PathEventReference] = []
        self._lock = threading.Lock()
        self._created = 0
        self._coalesced = 0
        self._phase_counts = {phase: 0 for phase in PathPhase}

    def register_event(
        self,
        event: MultiHorizonShockEvent,
        *,
        sequence_epoch: int,
        event_exchange_timestamp: str,
    ) -> PathSegmentRegistration:
        if sequence_epoch <= 0:
            raise ValueError("event reference sequence_epoch must be positive")
        event_exchange_ms = _timestamp_ms(event_exchange_timestamp)
        shock = event.event
        with self._lock:
            state = self._segments.get(event.parent_wave_id)
            created = state is None
            if state is None:
                self._expire_before(event_exchange_ms)
                if len(self._segments) >= self._max_open_segments:
                    raise RuntimeError("max open parent-wave segments reached")
                digest = hashlib.sha256(
                    f"{event.parent_wave_id}|path-v1".encode("ascii")
                ).hexdigest()[:20]
                pre_event = self._ring.snapshot_before(
                    symbol=shock.symbol,
                    venue=shock.venue,
                    session_bucket=shock.session_bucket,
                    event_detected_at_ms=event_exchange_ms,
                )
                capture_started_at = (
                    pre_event[0].exchange_timestamp
                    if pre_event
                    else event_exchange_timestamp
                )
                state = _SegmentState(
                    path_segment_id=f"SMRPS-{digest}",
                    primary_event_id=event.shock_event_id,
                    event_ids=set(),
                    symbol=shock.symbol,
                    venue=shock.venue,
                    session_bucket=shock.session_bucket,
                    event_detected_at_ms=event_exchange_ms,
                    capture_started_at=capture_started_at,
                    active_until_ms=event_exchange_ms + self._post_event_ms,
                )
                self._segments[event.parent_wave_id] = state
                self._created += 1
            if event.shock_event_id in state.event_ids:
                raise ValueError("duplicate shock event reference")
            state.event_ids.add(event.shock_event_id)
            reference = PathEventReference(
                parent_wave_id=event.parent_wave_id,
                path_segment_id=state.path_segment_id,
                shock_event_id=event.shock_event_id,
                shock_horizon_ms=event.shock_horizon_ms,
                event_sequence_in_wave=event.event_sequence_in_wave,
                event_detected_at_ms=shock.detected_at_ms,
                symbol=state.symbol,
                venue=state.venue,
                session_bucket=state.session_bucket,
                sequence_epoch=(
                    pre_event[0].sequence_epoch
                    if created and pre_event
                    else sequence_epoch
                ),
                capture_started_at=state.capture_started_at,
                segment_event_detected_at_ms=state.event_detected_at_ms,
                capture_ended_at=_timestamp_iso(state.active_until_ms),
            )
            self._references.append(reference)
            if not created:
                self._coalesced += 1
        pre_event = pre_event if created else ()
        return PathSegmentRegistration(
            parent_wave_id=event.parent_wave_id,
            path_segment_id=state.path_segment_id,
            primary_event_id=state.primary_event_id,
            event_reference=reference,
            segment_created=created,
            pre_event_envelopes=pre_event,
            capture_started_at=state.capture_started_at,
        )

    def active_segments_for(
        self, envelope: RawMarketObservation
    ) -> tuple[tuple[str, _SegmentState], ...]:
        observed_ms = _timestamp_ms(envelope.exchange_timestamp)
        with self._lock:
            self._expire_before(observed_ms)
            return tuple(
                (parent_wave_id, state)
                for parent_wave_id, state in self._segments.items()
                if observed_ms <= state.active_until_ms
                and envelope.symbol == state.symbol
                and envelope.venue == state.venue
                and envelope.session_bucket == state.session_bucket
            )

    def points_from_registration(
        self, registration: PathSegmentRegistration, *, detector_version: str
    ) -> tuple[MarketPathPoint, ...]:
        if not registration.segment_created:
            return ()
        detected_at = _timestamp_iso(registration.event_reference.event_detected_at_ms)
        points = tuple(
            _to_market_path_point(
                envelope,
                registration=registration,
                detector_version=detector_version,
                event_detected_at=detected_at,
                phase=PathPhase.PRE_EVENT,
            )
            for envelope in registration.pre_event_envelopes
        )
        with self._lock:
            self._phase_counts[PathPhase.PRE_EVENT] += len(points)
        return points

    def point_for_active_envelope(
        self,
        envelope: RawMarketObservation,
        *,
        parent_wave_id: str,
        state: _SegmentState,
        detector_version: str,
    ) -> MarketPathPoint:
        observed_ms = _timestamp_ms(envelope.exchange_timestamp)
        phase = (
            PathPhase.ACTIVE_EVENT
            if observed_ms <= state.event_detected_at_ms + self._active_event_ms
            else PathPhase.POST_EVENT
        )
        point = _to_market_path_point(
            envelope,
            registration=PathSegmentRegistration(
                parent_wave_id=parent_wave_id,
                path_segment_id=state.path_segment_id,
                primary_event_id=state.primary_event_id,
                event_reference=PathEventReference(
                    parent_wave_id=parent_wave_id,
                    path_segment_id=state.path_segment_id,
                    shock_event_id=state.primary_event_id,
                    shock_horizon_ms=1,
                    event_sequence_in_wave=1,
                    event_detected_at_ms=state.event_detected_at_ms,
                    symbol=state.symbol,
                    venue=state.venue,
                    session_bucket=state.session_bucket,
                    sequence_epoch=envelope.sequence_epoch,
                    capture_started_at=state.capture_started_at,
                    segment_event_detected_at_ms=state.event_detected_at_ms,
                    capture_ended_at=_timestamp_iso(state.active_until_ms),
                ),
                segment_created=False,
                pre_event_envelopes=(),
                capture_started_at=state.capture_started_at,
            ),
            detector_version=detector_version,
            event_detected_at=_timestamp_iso(state.event_detected_at_ms),
            phase=phase,
        )
        with self._lock:
            self._phase_counts[phase] += 1
        return point

    def references(self) -> tuple[PathEventReference, ...]:
        with self._lock:
            return tuple(self._references)

    def quality_snapshot(self) -> PathCaptureQualitySnapshot:
        (
            accepted,
            duplicates,
            out_of_order,
            timestamp_regressions,
            timestamp_regressions_quarantined,
            timestamp_regressions_exceeded,
            timestamp_regression_max_ms,
            local_receive_timestamp_regressions,
            local_receive_timestamp_regression_max_ms,
            gaps,
            evicted,
        ) = self._ring.counters()
        with self._lock:
            return PathCaptureQualitySnapshot(
                accepted_envelope_count=accepted,
                duplicate_sequence_count=duplicates,
                out_of_order_sequence_count=out_of_order,
                exchange_timestamp_regression_count=timestamp_regressions,
                exchange_timestamp_regression_quarantined_count=(
                    timestamp_regressions_quarantined
                ),
                exchange_timestamp_regression_exceeded_count=(
                    timestamp_regressions_exceeded
                ),
                exchange_timestamp_regression_max_ms=(timestamp_regression_max_ms),
                local_receive_timestamp_regression_count=(
                    local_receive_timestamp_regressions
                ),
                local_receive_timestamp_regression_max_ms=(
                    local_receive_timestamp_regression_max_ms
                ),
                sequence_gap_count=gaps,
                evicted_envelope_count=evicted,
                created_segment_count=self._created,
                coalesced_event_reference_count=self._coalesced,
                pre_event_point_count=self._phase_counts[PathPhase.PRE_EVENT],
                active_event_point_count=self._phase_counts[PathPhase.ACTIVE_EVENT],
                post_event_point_count=self._phase_counts[PathPhase.POST_EVENT],
            )

    def drop_symbol(self, symbol: str) -> int:
        """Abort open capture segments for a newly manual-managed symbol."""

        with self._lock:
            wave_ids = [
                wave_id
                for wave_id, state in self._segments.items()
                if state.symbol == symbol
            ]
            for wave_id in wave_ids:
                del self._segments[wave_id]
            return len(wave_ids)

    def reset_transport_epoch(self) -> int:
        """Abort open paths so no parent wave spans a WS reconnect."""

        with self._lock:
            removed = len(self._segments)
            self._segments.clear()
            return removed

    def _expire_before(self, observed_at_ms: int) -> None:
        expired = [
            parent_wave_id
            for parent_wave_id, state in self._segments.items()
            if state.active_until_ms < observed_at_ms
        ]
        for parent_wave_id in expired:
            del self._segments[parent_wave_id]


def _to_market_path_point(
    envelope: RawMarketObservation,
    *,
    registration: PathSegmentRegistration,
    detector_version: str,
    event_detected_at: str,
    phase: PathPhase,
) -> MarketPathPoint:
    return MarketPathPoint(
        event_id=registration.primary_event_id,
        path_segment_id=registration.path_segment_id,
        parent_wave_id=registration.parent_wave_id,
        path_phase=phase.value,
        symbol=envelope.symbol,
        exchange_timestamp=envelope.exchange_timestamp,
        local_receive_timestamp=envelope.local_receive_timestamp,
        source_sequence=envelope.source_sequence,
        sequence_epoch=envelope.sequence_epoch,
        series_sequence=envelope.series_sequence,
        venue=envelope.venue,
        session_bucket=envelope.session_bucket,
        detector_version=detector_version,
        capture_started_at=registration.capture_started_at,
        event_detected_at=event_detected_at,
        trade_price=envelope.trade_price,
        trade_qty=envelope.trade_qty,
        best_bid=envelope.best_bid,
        best_ask=envelope.best_ask,
        bid_depth=envelope.bid_depth,
        ask_depth=envelope.ask_depth,
        quote_age_ms=envelope.quote_age_ms,
        aggressor_side=AggressorSide(envelope.aggressor_side.value),
    )


def to_market_stream_point(
    envelope: RawMarketObservation,
    *,
    path_order_status: PathEnvelopeOrderStatus = PathEnvelopeOrderStatus.ACCEPT,
    exchange_timestamp_regression_ms: int = 0,
) -> MarketStreamPoint:
    return MarketStreamPoint(
        symbol=envelope.symbol,
        exchange_timestamp=envelope.exchange_timestamp,
        local_receive_timestamp=envelope.local_receive_timestamp,
        source_sequence=envelope.source_sequence,
        sequence_epoch=envelope.sequence_epoch,
        series_sequence=envelope.series_sequence,
        venue=envelope.venue,
        session_bucket=envelope.session_bucket,
        realtime_type=envelope.realtime_type,
        trade_price=envelope.trade_price,
        trade_qty=envelope.trade_qty,
        best_bid=envelope.best_bid,
        best_ask=envelope.best_ask,
        bid_depth=envelope.bid_depth,
        ask_depth=envelope.ask_depth,
        quote_age_ms=envelope.quote_age_ms,
        aggressor_side=AggressorSide(envelope.aggressor_side.value),
        path_order_status=path_order_status.value,
        path_consumer_eligible=(path_order_status is PathEnvelopeOrderStatus.ACCEPT),
        exchange_timestamp_regression_ms=exchange_timestamp_regression_ms,
    )


def _timestamp_ms(value: str) -> int:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return int(parsed.timestamp() * 1_000)


def _timestamp_iso(value_ms: int) -> str:
    return datetime.fromtimestamp(value_ms / 1_000).astimezone().isoformat()


def append_path_event_references(
    path: Path, references: Iterable[PathEventReference]
) -> None:
    """Durable worker-side append; producer code must never call it."""

    materialized = tuple(references)
    if not materialized:
        return
    target = Path(path)
    encoded = b"".join(
        (json.dumps(reference.as_dict(), sort_keys=True) + "\n").encode("utf-8")
        for reference in materialized
    )
    with partition_maintenance_lock(target):
        _assert_no_symlink_ancestors(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        _assert_no_symlink_ancestors(target)
        shards = readable_partition_path_files(target)
        # Reference reconciliation has one canonical filename and no manifest
        # handoff for late logical shards. Once maintenance publishes any gzip
        # (or a legacy shard is present), fail closed instead of mutating the
        # gzip in place or accepting a row that production cannot discover.
        if any(shard.suffix == ".gz" for shard in shards) or len(shards) > 1:
            raise OSError("compressed or sharded reference partition is closed")
        append_target = target
        descriptor = _open_append_regular_nofollow(
            append_target,
            allow_create=True,
        )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            original_size = os.fstat(descriptor).st_size
            try:
                remaining = memoryview(encoded)
                while remaining:
                    written = os.write(descriptor, remaining)
                    if written <= 0:
                        raise OSError("path reference append made no progress")
                    remaining = remaining[written:]
                os.fsync(descriptor)
                _assert_open_descriptor_matches_path(descriptor, append_target)
            except BaseException:
                # JSONL append is restored to the exact previous byte boundary
                # before releasing the per-file lock.  This keeps both the
                # old gzip history and an existing/new plain tail readable
                # after ENOSPC or an interrupted short write.
                os.ftruncate(descriptor, original_size)
                os.fsync(descriptor)
                raise
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def load_path_event_references(path: Path) -> tuple[dict[str, Any], ...]:
    """Load current plain or post-session compressed event-window references."""

    plain = Path(path)
    with partition_maintenance_lock(plain):
        _assert_no_symlink_ancestors(plain)
        return _load_reference_shards(readable_partition_path_files(plain))


def _load_reference_shards(shards: tuple[Path, ...]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for selected in shards:
        rows.extend(_load_reference_shard(selected))
    return tuple(rows)


def _load_reference_shard(selected: Path) -> list[dict[str, Any]]:
    descriptor = os.open(
        selected,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_SH)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("path reference source must be a regular file")
        rows: list[dict[str, Any]] = []
        raw = os.fdopen(descriptor, "rb", closefd=False)
        binary = (
            gzip.GzipFile(fileobj=raw, mode="rb") if selected.suffix == ".gz" else raw
        )
        with io.TextIOWrapper(binary, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("path event reference row must be an object")
                rows.append(row)
        current = selected.lstat()
        if (
            not stat.S_ISREG(current.st_mode)
            or opened.st_dev != current.st_dev
            or opened.st_ino != current.st_ino
        ):
            raise OSError("path reference source changed during read")
        return rows
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
