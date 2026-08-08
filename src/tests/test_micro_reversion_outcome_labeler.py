from __future__ import annotations

import pytest

from src.engine.scalping.micro_reversion.contracts import (
    CoverageTier,
    PriceObservation,
    ShockEvent,
)
from src.engine.scalping.micro_reversion.outcome_labeler import (
    OutcomeLabeler,
    OutcomeLabelerConfig,
)

BASE_MS = 1_786_000_000_000


def _event() -> ShockEvent:
    return ShockEvent(
        event_id="SMR-LABEL",
        symbol="000001",
        venue="KRX",
        session_bucket="KRX_REGULAR",
        trade_date="2026-08-07",
        detected_at_ms=BASE_MS,
        reference_at_ms=BASE_MS - 5_000,
        reference_price=100.0,
        shock_price=99.5,
        shock_return_bps=-50.0,
        return_robust_z=-3.0,
        acceleration_robust_z=-2.5,
        micro_vwap=99.9,
        coverage_tier=CoverageTier.MICRO_CONTEXT,
        source_quality_status="micro_observed",
    )


def _observation(offset_sec: int, price: float) -> PriceObservation:
    return PriceObservation(
        symbol="000001",
        observed_at_ms=BASE_MS + offset_sec * 1_000,
        price=price,
        trade_date="2026-08-07",
        venue="KRX",
        session_bucket="KRX_REGULAR",
    )


def test_labeler_builds_15_second_to_10_minute_path_without_lookahead() -> None:
    milestone_prices = {
        0: 99.5,
        15: 99.8,
        30: 100.1,
        60: 100.2,
        120: 100.0,
        180: 99.9,
        300: 100.3,
        600: 100.4,
    }
    current_price = 99.5
    observations = []
    for offset_sec in range(0, 601, 5):
        current_price = milestone_prices.get(offset_sec, current_price)
        observations.append(_observation(offset_sec, current_price))
    observations.append(_observation(601, 80.0))
    label = OutcomeLabeler().label(_event(), observations)

    assert label.outcome_source_quality_status == "pass"
    assert label.mature_horizon_count == 7
    assert label.first_half_reclaim_ms == BASE_MS + 15_000
    assert label.first_full_reclaim_ms == BASE_MS + 30_000
    assert label.first_continuation_ms is None

    at_15 = label.outcomes[0]
    assert at_15.complete is True
    assert at_15.half_reclaim is True
    assert at_15.full_reclaim is False
    assert at_15.mfe_bps == pytest.approx(30.150754)
    assert at_15.cost_adjusted_terminal_return_bps == pytest.approx(7.150754)

    at_600 = label.outcomes[-1]
    assert at_600.mae_bps == 0.0
    assert at_600.mfe_bps == pytest.approx(90.452261)


def test_labeler_marks_missing_long_horizons_partial() -> None:
    labeler = OutcomeLabeler(
        OutcomeLabelerConfig(
            max_horizon_lag_ms=1_000,
            max_internal_gap_ms=20_000,
        )
    )
    label = labeler.label(
        _event(),
        [_observation(0, 99.5), _observation(15, 99.8)],
    )

    assert label.mature_horizon_count == 1
    assert label.outcome_source_quality_status == "partial_missing_horizon"
    assert label.outcomes[0].complete is True
    assert all(not outcome.complete for outcome in label.outcomes[1:])


def test_labeler_rejects_sparse_path_that_would_understate_mae() -> None:
    label = OutcomeLabeler().label(
        _event(),
        [_observation(0, 99.5), _observation(15, 100.0)],
    )

    assert label.mature_horizon_count == 0
    assert label.outcomes[0].path_continuity_status == "internal_gap_exceeded"
    assert label.outcomes[0].max_path_gap_ms == 15_000
