"""Future-path labels for source-only micro-reversion shock events."""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Iterable

from .contracts import (
    DEFAULT_HORIZONS_SEC,
    HorizonOutcome,
    OutcomeLabel,
    PriceObservation,
    ShockEvent,
)


@dataclass(frozen=True, slots=True)
class OutcomeLabelerConfig:
    horizons_sec: tuple[int, ...] = DEFAULT_HORIZONS_SEC
    max_horizon_lag_ms: int = 6_000
    max_internal_gap_ms: int = 10_000
    conservative_total_cost_bps: float = 23.0
    half_reclaim_fraction: float = 0.5
    continuation_fraction: float = 0.5

    def __post_init__(self) -> None:
        if not self.horizons_sec:
            raise ValueError("at least one horizon is required")
        if tuple(sorted(set(self.horizons_sec))) != self.horizons_sec:
            raise ValueError("horizons_sec must be sorted and unique")
        if self.horizons_sec[0] <= 0:
            raise ValueError("horizons_sec must be positive")
        if self.max_horizon_lag_ms < 0:
            raise ValueError("max_horizon_lag_ms must not be negative")
        if self.max_internal_gap_ms <= 0:
            raise ValueError("max_internal_gap_ms must be positive")
        if self.conservative_total_cost_bps < 0:
            raise ValueError("conservative_total_cost_bps must not be negative")
        if not 0 < self.half_reclaim_fraction <= 1:
            raise ValueError("half_reclaim_fraction must be in (0, 1]")
        if not 0 < self.continuation_fraction <= 1:
            raise ValueError("continuation_fraction must be in (0, 1]")


class OutcomeLabeler:
    def __init__(self, config: OutcomeLabelerConfig | None = None) -> None:
        self.config = config or OutcomeLabelerConfig()

    def label(
        self,
        event: ShockEvent,
        observations: Iterable[PriceObservation],
    ) -> OutcomeLabel:
        series = sorted(
            (
                observation
                for observation in observations
                if observation.series_key == event.series_key
                and observation.observed_at_ms >= event.detected_at_ms
            ),
            key=lambda observation: observation.observed_at_ms,
        )
        times = [observation.observed_at_ms for observation in series]
        outcomes = tuple(
            self._horizon_outcome(event, series, times, horizon_sec)
            for horizon_sec in self.config.horizons_sec
        )
        mature_count = sum(outcome.complete for outcome in outcomes)
        if mature_count == len(outcomes):
            quality_status = "pass"
            exclusion_reasons: tuple[str, ...] = ()
        elif mature_count:
            quality_status = "partial_missing_horizon"
            exclusion_reasons = ("one_or_more_horizons_missing",)
        else:
            quality_status = "blocked_missing_horizon"
            exclusion_reasons = ("all_horizons_missing",)

        complete_outcomes = [outcome for outcome in outcomes if outcome.complete]
        if complete_outcomes:
            last_complete = complete_outcomes[-1]
            path_limit_ms = (
                event.detected_at_ms
                + last_complete.horizon_sec * 1_000
                + int(last_complete.observation_lag_ms or 0)
            )
        else:
            path_limit_ms = event.detected_at_ms
        bounded_series = [
            observation
            for observation in series
            if observation.observed_at_ms <= path_limit_ms
        ]
        first_full_reclaim_ms = self._first_crossing_ms(
            bounded_series,
            event.reference_price,
            direction="up",
        )
        half_reclaim_price = event.shock_price + (
            event.shock_size * self.config.half_reclaim_fraction
        )
        first_half_reclaim_ms = self._first_crossing_ms(
            bounded_series,
            half_reclaim_price,
            direction="up",
        )
        continuation_price = event.shock_price - (
            event.shock_size * self.config.continuation_fraction
        )
        first_continuation_ms = self._first_crossing_ms(
            bounded_series,
            continuation_price,
            direction="down",
        )

        return OutcomeLabel(
            event_id=event.event_id,
            symbol=event.symbol,
            trade_date=event.trade_date,
            venue=event.venue,
            session_bucket=event.session_bucket,
            coverage_tier=event.coverage_tier,
            outcomes=outcomes,
            listing_market=event.listing_market,
            instrument_type=event.instrument_type,
            instrument_metadata_source=event.instrument_metadata_source,
            instrument_metadata_verified=event.instrument_metadata_verified,
            first_full_reclaim_ms=first_full_reclaim_ms,
            first_half_reclaim_ms=first_half_reclaim_ms,
            first_continuation_ms=first_continuation_ms,
            outcome_source_quality_status=quality_status,
            exclusion_reasons=exclusion_reasons,
        )

    def _horizon_outcome(
        self,
        event: ShockEvent,
        series: list[PriceObservation],
        times: list[int],
        horizon_sec: int,
    ) -> HorizonOutcome:
        target_ms = event.detected_at_ms + horizon_sec * 1_000
        endpoint_index = bisect.bisect_left(times, target_ms)
        if endpoint_index >= len(series):
            return HorizonOutcome(horizon_sec=horizon_sec, complete=False)
        endpoint = series[endpoint_index]
        lag_ms = endpoint.observed_at_ms - target_ms
        if lag_ms > self.config.max_horizon_lag_ms:
            return HorizonOutcome(
                horizon_sec=horizon_sec,
                complete=False,
                observation_lag_ms=lag_ms,
                path_continuity_status="endpoint_lag_exceeded",
            )

        path_observations = [
            observation
            for observation in series[: endpoint_index + 1]
            if observation.observed_at_ms >= event.detected_at_ms
        ]
        path_times = [event.detected_at_ms]
        path_times.extend(
            observation.observed_at_ms
            for observation in path_observations
            if observation.observed_at_ms > event.detected_at_ms
        )
        max_path_gap_ms = max(
            (right - left for left, right in zip(path_times, path_times[1:])),
            default=0,
        )
        if max_path_gap_ms > self.config.max_internal_gap_ms:
            return HorizonOutcome(
                horizon_sec=horizon_sec,
                complete=False,
                observation_lag_ms=lag_ms,
                path_observation_count=len(path_observations),
                max_path_gap_ms=max_path_gap_ms,
                path_continuity_status="internal_gap_exceeded",
            )

        path_prices = [event.shock_price]
        path_prices.extend(observation.price for observation in path_observations)
        terminal_return_bps = (endpoint.price / event.shock_price - 1.0) * 10_000.0
        mfe_bps = (max(path_prices) / event.shock_price - 1.0) * 10_000.0
        mae_bps = (min(path_prices) / event.shock_price - 1.0) * 10_000.0
        half_reclaim_price = event.shock_price + (
            event.shock_size * self.config.half_reclaim_fraction
        )
        continuation_price = event.shock_price - (
            event.shock_size * self.config.continuation_fraction
        )

        return HorizonOutcome(
            horizon_sec=horizon_sec,
            complete=True,
            observation_lag_ms=lag_ms,
            path_observation_count=len(path_observations),
            max_path_gap_ms=max_path_gap_ms,
            path_continuity_status="pass",
            terminal_return_bps=round(terminal_return_bps, 6),
            cost_adjusted_terminal_return_bps=round(
                terminal_return_bps - self.config.conservative_total_cost_bps,
                6,
            ),
            mfe_bps=round(mfe_bps, 6),
            mae_bps=round(mae_bps, 6),
            full_reclaim=max(path_prices) >= event.reference_price,
            half_reclaim=max(path_prices) >= half_reclaim_price,
            continuation_half_shock=min(path_prices) <= continuation_price,
            micro_vwap_reclaimed=(
                None
                if event.micro_vwap is None
                else max(path_prices) >= event.micro_vwap
            ),
        )

    @staticmethod
    def _first_crossing_ms(
        series: Iterable[PriceObservation],
        threshold: float,
        *,
        direction: str,
    ) -> int | None:
        for observation in series:
            crossed = (
                observation.price >= threshold
                if direction == "up"
                else observation.price <= threshold
            )
            if crossed:
                return observation.observed_at_ms
        return None
