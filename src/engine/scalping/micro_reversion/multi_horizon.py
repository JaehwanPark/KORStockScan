"""Multi-horizon shock detection grouped into independent parent waves."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable

from .contracts import PriceObservation, ShockEvent
from .detector import DetectorConfig, ShockDetector

MULTI_HORIZON_SCHEMA = "scalp_micro_reversion_multi_horizon_event_v1"
MULTI_HORIZON_POLICY_VERSION = "scalp_micro_reversion_multi_horizon_parent_wave_v1"
MULTI_HORIZON_METRIC_CONTRACT = {
    "metric_role": "pattern_discovery_feature",
    "window_policy": "predeclared_1s_3s_5s_10s_20s_parent_wave_grouping",
    "sample_floor": "independent_parent_wave_floor_owned_by_research_gate",
    "primary_decision_metric": "shock_event_count_by_horizon",
    "source_quality_gate": "strictly_increasing_observation_series_and_parent_wave_provenance",
    "forbidden_uses": (
        "child_horizon_events_as_independent_samples",
        "fixed_cooldown_as_economic_filter",
        "sim_or_runtime_promotion",
        "broker_order_submission",
    ),
}


@dataclass(frozen=True, slots=True)
class MultiHorizonConfig:
    horizons_ms: tuple[int, ...] = (1_000, 3_000, 5_000, 10_000, 20_000)
    recovery_from_low_bps: float = 12.0
    new_impulse_from_peak_bps: float = -18.0
    max_parent_wave_ms: int = 180_000
    detector_base: DetectorConfig = field(
        default_factory=lambda: DetectorConfig(cooldown_ms=0)
    )

    def __post_init__(self) -> None:
        if not self.horizons_ms or any(horizon <= 0 for horizon in self.horizons_ms):
            raise ValueError("horizons_ms must contain positive values")
        if tuple(sorted(set(self.horizons_ms))) != self.horizons_ms:
            raise ValueError("horizons_ms must be sorted and unique")
        if self.recovery_from_low_bps <= 0:
            raise ValueError("recovery_from_low_bps must be positive")
        if self.new_impulse_from_peak_bps >= 0:
            raise ValueError("new_impulse_from_peak_bps must be negative")
        if self.max_parent_wave_ms <= 0:
            raise ValueError("max_parent_wave_ms must be positive")


@dataclass(frozen=True, slots=True)
class MultiHorizonShockEvent:
    parent_wave_id: str
    shock_event_id: str
    shock_horizon_ms: int
    event_sequence_in_wave: int
    rearm_reason: str
    event: ShockEvent
    schema: str = MULTI_HORIZON_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "parent_wave_id": self.parent_wave_id,
            "shock_event_id": self.shock_event_id,
            "shock_horizon_ms": self.shock_horizon_ms,
            "event_sequence_in_wave": self.event_sequence_in_wave,
            "rearm_reason": self.rearm_reason,
            "detector_version": MULTI_HORIZON_POLICY_VERSION,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "trading_runtime_effect": False,
            "decision_authority": "multi_horizon_pattern_observation_only",
            **MULTI_HORIZON_METRIC_CONTRACT,
            "event": self.event.as_dict(),
        }


@dataclass(slots=True)
class _WaveState:
    parent_wave_id: str
    started_at_ms: int
    low_price: float
    recovery_peak_price: float
    released: bool = False
    sequence: int = 0


class MultiHorizonShockDetector:
    """Run robust detectors and group their output into parent waves."""

    def __init__(self, config: MultiHorizonConfig | None = None) -> None:
        self.config = config or MultiHorizonConfig()
        self._detectors = {
            horizon: ShockDetector(
                replace(
                    self.config.detector_base,
                    return_window_ms=horizon,
                    cooldown_ms=0,
                )
            )
            for horizon in self.config.horizons_ms
        }
        self._waves: dict[tuple[str, str, str, str], _WaveState] = {}

    def reset(self) -> None:
        for detector in self._detectors.values():
            detector.reset()
        self._waves.clear()

    def drop_symbol(self, symbol: str) -> int:
        """Discard detector and parent-wave state for a manual exclusion."""

        removed = sum(
            detector.drop_symbol(symbol) for detector in self._detectors.values()
        )
        wave_keys = [key for key in self._waves if key[1] == symbol]
        for key in wave_keys:
            del self._waves[key]
        return removed + len(wave_keys)

    def process(
        self, observation: PriceObservation
    ) -> tuple[MultiHorizonShockEvent, ...]:
        key = observation.series_key
        wave = self._waves.get(key)
        if wave is not None:
            wave.low_price = min(wave.low_price, observation.price)
            recovery_bps = (observation.price / wave.low_price - 1.0) * 10_000.0
            if recovery_bps >= self.config.recovery_from_low_bps:
                wave.released = True
            if wave.released:
                wave.recovery_peak_price = max(
                    wave.recovery_peak_price, observation.price
                )

        emitted: list[tuple[int, ShockEvent]] = []
        for horizon, detector in self._detectors.items():
            event = detector.process(observation)
            if event is not None:
                emitted.append((horizon, event))
        if not emitted:
            return ()

        rearm_reason = "same_parent_wave"
        if wave is None:
            wave = self._new_wave(observation, reason="initial_shock")
            rearm_reason = "initial_shock"
        elif observation.observed_at_ms - wave.started_at_ms > (
            self.config.max_parent_wave_ms
        ):
            wave = self._new_wave(observation, reason="parent_wave_ttl_elapsed")
            rearm_reason = "parent_wave_ttl_elapsed"
        elif wave.released:
            impulse_bps = (
                observation.price / wave.recovery_peak_price - 1.0
            ) * 10_000.0
            if impulse_bps <= self.config.new_impulse_from_peak_bps:
                wave = self._new_wave(observation, reason="recovery_then_new_impulse")
                rearm_reason = "recovery_then_new_impulse"

        results: list[MultiHorizonShockEvent] = []
        for horizon, event in emitted:
            wave.sequence += 1
            results.append(
                MultiHorizonShockEvent(
                    parent_wave_id=wave.parent_wave_id,
                    shock_event_id=f"{event.event_id}-H{horizon}",
                    shock_horizon_ms=horizon,
                    event_sequence_in_wave=wave.sequence,
                    rearm_reason=(
                        rearm_reason if wave.sequence == 1 else "same_parent_wave"
                    ),
                    event=event,
                )
            )
        return tuple(results)

    def process_many(
        self, observations: Iterable[PriceObservation]
    ) -> tuple[MultiHorizonShockEvent, ...]:
        results: list[MultiHorizonShockEvent] = []
        for observation in observations:
            results.extend(self.process(observation))
        return tuple(results)

    def config_dict(self) -> dict[str, Any]:
        payload = asdict(self.config)
        return payload

    def _new_wave(self, observation: PriceObservation, *, reason: str) -> _WaveState:
        raw = "|".join(
            (
                MULTI_HORIZON_POLICY_VERSION,
                *observation.series_key,
                str(observation.observed_at_ms),
                reason,
            )
        )
        digest = hashlib.sha256(raw.encode("ascii")).hexdigest()[:20]
        wave = _WaveState(
            parent_wave_id=(f"SMRW-{observation.trade_date.replace('-', '')}-{digest}"),
            started_at_ms=observation.observed_at_ms,
            low_price=observation.price,
            recovery_peak_price=observation.price,
        )
        self._waves[observation.series_key] = wave
        return wave
