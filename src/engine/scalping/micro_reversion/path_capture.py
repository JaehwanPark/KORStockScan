"""Worker-side pre-event buffering and parent-wave path coalescing.

Nothing in this module is imported by the market-data producer.  It operates
on immutable envelopes already accepted by the bounded observation queue.
"""

from __future__ import annotations

import hashlib
import fcntl
import json
import os
import threading
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .multi_horizon import MultiHorizonShockEvent
from .observation_adapter import RawMarketObservation
from .path_journal import AggressorSide, MarketPathPoint

PATH_REFERENCE_SCHEMA = "scalp_micro_reversion_path_event_reference_v1"
PATH_CAPTURE_AUTHORITY = "forward_path_observation_only_no_policy_selection"
PATH_CAPTURE_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_path_coverage",
    "decision_authority": PATH_CAPTURE_AUTHORITY,
    "window_policy": "bounded_30s_pre_event_through_180s_post_event_parent_wave",
    "sample_floor": "five_trading_days_and_200_mature_events_collector_health_only",
    "primary_decision_metric": "pre_active_post_path_coverage_pct",
    "source_quality_gate": (
        "monotonic_source_sequence_and_no_manual_control_rows_and_"
        "one_segment_per_parent_wave"
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


@dataclass(frozen=True, slots=True)
class PathEventReference:
    parent_wave_id: str
    path_segment_id: str
    shock_event_id: str
    shock_horizon_ms: int
    event_sequence_in_wave: int
    event_detected_at_ms: int
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
    ) -> None:
        if max_age_ms < 20_000 or max_age_ms > 30_000:
            raise ValueError("pre-event max_age_ms must be between 20s and 30s")
        if max_points_per_series <= 0:
            raise ValueError("max_points_per_series must be positive")
        self.max_age_ms = max_age_ms
        self.max_points_per_series = max_points_per_series
        self._points: dict[
            tuple[str, str, str], deque[tuple[int, RawMarketObservation]]
        ] = defaultdict(deque)
        self._last_sequence: dict[tuple[str, str, str], int] = {}
        self._last_timestamp_ms: dict[tuple[str, str, str], int] = {}
        self._lock = threading.Lock()
        self._accepted = 0
        self._duplicates = 0
        self._out_of_order = 0
        self._gaps = 0
        self._evicted = 0

    def add(self, envelope: RawMarketObservation) -> bool:
        key = (envelope.symbol, envelope.venue, envelope.session_bucket)
        observed_ms = _timestamp_ms(envelope.exchange_timestamp)
        with self._lock:
            previous = self._last_sequence.get(key)
            previous_timestamp_ms = self._last_timestamp_ms.get(key)
            if previous is not None:
                if envelope.source_sequence == previous:
                    self._duplicates += 1
                    return False
                if envelope.source_sequence < previous:
                    self._out_of_order += 1
                    return False
            if (
                previous_timestamp_ms is not None
                and observed_ms < previous_timestamp_ms
            ):
                self._out_of_order += 1
                return False
            if previous is not None and envelope.source_sequence > previous + 1:
                self._gaps += envelope.source_sequence - previous - 1
            self._last_sequence[key] = envelope.source_sequence
            self._last_timestamp_ms[key] = observed_ms
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

    def counters(self) -> tuple[int, int, int, int, int]:
        with self._lock:
            return (
                self._accepted,
                self._duplicates,
                self._out_of_order,
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

    def register_event(self, event: MultiHorizonShockEvent) -> PathSegmentRegistration:
        shock = event.event
        with self._lock:
            state = self._segments.get(event.parent_wave_id)
            created = state is None
            if state is None:
                self._expire_before(shock.detected_at_ms)
                if len(self._segments) >= self._max_open_segments:
                    raise RuntimeError("max open parent-wave segments reached")
                digest = hashlib.sha256(
                    f"{event.parent_wave_id}|path-v1".encode("ascii")
                ).hexdigest()[:20]
                pre_event = self._ring.snapshot_before(
                    symbol=shock.symbol,
                    venue=shock.venue,
                    session_bucket=shock.session_bucket,
                    event_detected_at_ms=shock.detected_at_ms,
                )
                capture_started_at = (
                    pre_event[0].exchange_timestamp
                    if pre_event
                    else _timestamp_iso(shock.detected_at_ms)
                )
                state = _SegmentState(
                    path_segment_id=f"SMRPS-{digest}",
                    primary_event_id=event.shock_event_id,
                    event_ids=set(),
                    symbol=shock.symbol,
                    venue=shock.venue,
                    session_bucket=shock.session_bucket,
                    event_detected_at_ms=shock.detected_at_ms,
                    capture_started_at=capture_started_at,
                    active_until_ms=shock.detected_at_ms + self._post_event_ms,
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
        accepted, duplicates, out_of_order, gaps, evicted = self._ring.counters()
        with self._lock:
            return PathCaptureQualitySnapshot(
                accepted_envelope_count=accepted,
                duplicate_sequence_count=duplicates,
                out_of_order_sequence_count=out_of_order,
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
        manual_control_exclusion_checked=(envelope.manual_control_exclusion_checked),
        manual_control_excluded=envelope.manual_control_excluded,
        manual_control_exclusion_version=(envelope.manual_control_exclusion_version),
        manual_control_exclusion_checked_at=(
            envelope.manual_control_exclusion_checked_at
        ),
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
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = b"".join(
        (json.dumps(reference.as_dict(), sort_keys=True) + "\n").encode("utf-8")
        for reference in materialized
    )
    descriptor = os.open(target, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o640)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        remaining = memoryview(encoded)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("path reference append made no progress")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
