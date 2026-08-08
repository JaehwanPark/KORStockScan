"""Deterministic robust shock detector for offline micro-reversion replay."""

from __future__ import annotations

import hashlib
import statistics
from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

from .contracts import POLICY_VERSION, PriceObservation, ShockEvent


@dataclass(frozen=True, slots=True)
class DetectorConfig:
    return_window_ms: int = 5_000
    reference_max_lag_ms: int = 2_000
    history_size: int = 120
    min_robust_history: int = 20
    absolute_shock_bps: float = -30.0
    return_z_trigger: float = -3.0
    acceleration_z_trigger: float = -2.5
    release_return_bps: float = -10.0
    release_return_z: float = -1.0
    cooldown_ms: int = 60_000
    mad_floor_bps: float = 0.5
    allow_absolute_trigger_during_warmup: bool = True

    def __post_init__(self) -> None:
        if self.return_window_ms <= 0:
            raise ValueError("return_window_ms must be positive")
        if self.reference_max_lag_ms < 0:
            raise ValueError("reference_max_lag_ms must not be negative")
        if self.history_size < 3:
            raise ValueError("history_size must be at least 3")
        if self.min_robust_history < 3:
            raise ValueError("min_robust_history must be at least 3")
        if self.cooldown_ms < 0:
            raise ValueError("cooldown_ms must not be negative")


@dataclass(slots=True)
class _SeriesState:
    observations: deque[PriceObservation] = field(default_factory=deque)
    return_history_bps: deque[float] = field(default_factory=deque)
    acceleration_history_bps: deque[float] = field(default_factory=deque)
    previous_return_bps: float | None = None
    active: bool = False
    cooldown_until_ms: int = 0
    last_observed_at_ms: int = 0


def robust_zscore(
    value: float,
    history: Iterable[float],
    *,
    mad_floor: float = 0.5,
) -> float | None:
    samples = tuple(float(sample) for sample in history)
    if len(samples) < 3:
        return None
    median = statistics.median(samples)
    mad = statistics.median(abs(sample - median) for sample in samples)
    scale = max(float(mad_floor), 1.4826 * mad)
    return (float(value) - median) / scale


class ShockDetector:
    """Detect one shock per hysteresis/cooldown episode.

    The detector consumes observations that are already sorted within each
    symbol/venue/session series. It never creates orders or runtime policy.
    """

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()
        self._states: dict[tuple[str, str, str, str], _SeriesState] = {}

    def reset(self) -> None:
        self._states.clear()

    def drop_symbol(self, symbol: str) -> int:
        """Discard all detector history for one newly manual-managed symbol."""

        keys = [key for key in self._states if key[1] == symbol]
        for key in keys:
            del self._states[key]
        return len(keys)

    def process(self, observation: PriceObservation) -> ShockEvent | None:
        state = self._states.setdefault(observation.series_key, _SeriesState())
        if observation.observed_at_ms <= state.last_observed_at_ms:
            raise ValueError("observations must be strictly increasing within a series")
        state.last_observed_at_ms = observation.observed_at_ms
        self._trim_observations(state, observation.observed_at_ms)
        reference = self._reference_observation(state, observation.observed_at_ms)
        state.observations.append(observation)
        if reference is None:
            return None

        return_bps = (observation.price / reference.price - 1.0) * 10_000.0
        return_z = robust_zscore(
            return_bps,
            state.return_history_bps,
            mad_floor=self.config.mad_floor_bps,
        )
        acceleration_bps = (
            None
            if state.previous_return_bps is None
            else return_bps - state.previous_return_bps
        )
        acceleration_z = (
            None
            if acceleration_bps is None
            else robust_zscore(
                acceleration_bps,
                state.acceleration_history_bps,
                mad_floor=self.config.mad_floor_bps,
            )
        )

        event = self._transition(
            state,
            observation=observation,
            reference=reference,
            return_bps=return_bps,
            return_z=return_z,
            acceleration_z=acceleration_z,
        )
        if acceleration_bps is not None:
            state.acceleration_history_bps.append(acceleration_bps)
            self._trim_history(state.acceleration_history_bps)
        state.return_history_bps.append(return_bps)
        self._trim_history(state.return_history_bps)
        state.previous_return_bps = return_bps
        return event

    def process_many(
        self, observations: Iterable[PriceObservation]
    ) -> tuple[ShockEvent, ...]:
        events: list[ShockEvent] = []
        for observation in observations:
            event = self.process(observation)
            if event is not None:
                events.append(event)
        return tuple(events)

    def _transition(
        self,
        state: _SeriesState,
        *,
        observation: PriceObservation,
        reference: PriceObservation,
        return_bps: float,
        return_z: float | None,
        acceleration_z: float | None,
    ) -> ShockEvent | None:
        released = return_bps >= self.config.release_return_bps or (
            return_bps > self.config.absolute_shock_bps
            and return_z is not None
            and return_z >= self.config.release_return_z
        )
        if state.active:
            if released:
                state.active = False
                state.cooldown_until_ms = (
                    observation.observed_at_ms + self.config.cooldown_ms
                )
            return None
        if observation.observed_at_ms < state.cooldown_until_ms:
            return None

        robust_history_ready = (
            len(state.return_history_bps) >= self.config.min_robust_history
        )
        robust_trigger = (
            return_z is not None and return_z <= self.config.return_z_trigger
        ) or (
            acceleration_z is not None
            and acceleration_z <= self.config.acceleration_z_trigger
        )
        warmup_trigger = (
            self.config.allow_absolute_trigger_during_warmup
            and not robust_history_ready
        )
        if return_bps > self.config.absolute_shock_bps or not (
            robust_trigger or warmup_trigger
        ):
            return None

        state.active = True
        event_id = self._event_id(
            observation,
            reference=reference,
            return_bps=return_bps,
        )
        return ShockEvent(
            event_id=event_id,
            symbol=observation.symbol,
            venue=observation.venue,
            session_bucket=observation.session_bucket,
            trade_date=observation.trade_date,
            detected_at_ms=observation.observed_at_ms,
            reference_at_ms=reference.observed_at_ms,
            reference_price=reference.price,
            shock_price=observation.price,
            shock_return_bps=round(return_bps, 6),
            return_robust_z=None if return_z is None else round(return_z, 6),
            acceleration_robust_z=(
                None if acceleration_z is None else round(acceleration_z, 6)
            ),
            micro_vwap=observation.micro_vwap,
            coverage_tier=observation.coverage_tier,
            source_quality_status=observation.source_quality_status,
            listing_market=observation.listing_market,
            instrument_type=observation.instrument_type,
            instrument_metadata_source=observation.instrument_metadata_source,
            instrument_metadata_verified=observation.instrument_metadata_verified,
        )

    def _trim_observations(self, state: _SeriesState, now_ms: int) -> None:
        keep_after_ms = (
            now_ms
            - self.config.return_window_ms
            - self.config.reference_max_lag_ms
            - 1_000
        )
        while state.observations and (
            state.observations[0].observed_at_ms < keep_after_ms
        ):
            state.observations.popleft()

    def _reference_observation(
        self, state: _SeriesState, now_ms: int
    ) -> PriceObservation | None:
        target_ms = now_ms - self.config.return_window_ms
        for observation in reversed(state.observations):
            if observation.observed_at_ms > target_ms:
                continue
            if target_ms - observation.observed_at_ms > (
                self.config.reference_max_lag_ms
            ):
                return None
            return observation
        return None

    def _trim_history(self, history: deque[float]) -> None:
        while len(history) > self.config.history_size:
            history.popleft()

    @staticmethod
    def _event_id(
        observation: PriceObservation,
        *,
        reference: PriceObservation,
        return_bps: float,
    ) -> str:
        raw = "|".join(
            (
                POLICY_VERSION,
                observation.trade_date,
                observation.symbol,
                observation.venue,
                observation.session_bucket,
                str(observation.observed_at_ms),
                str(reference.observed_at_ms),
                f"{return_bps:.6f}",
            )
        )
        digest = hashlib.sha256(raw.encode("ascii")).hexdigest()[:20]
        return f"SMR-{observation.trade_date.replace('-', '')}-{digest}"
