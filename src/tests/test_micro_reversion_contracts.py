from __future__ import annotations

from src.engine.scalping.micro_reversion.contracts import (
    CoverageTier,
    PriceObservation,
    ShockEvent,
)


def _observation(**overrides) -> PriceObservation:
    payload = {
        "symbol": "A000001",
        "observed_at_ms": 1_786_000_000_000,
        "price": 10_000.0,
        "trade_date": "2026-08-07",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
    }
    payload.update(overrides)
    return PriceObservation(**payload)


def test_price_observation_has_no_manual_control_contract() -> None:
    payload = _observation().as_dict()
    assert payload["schema"] == "scalp_micro_reversion_price_observation_v4"
    assert not any(key.startswith("manual_control") for key in payload)


def test_coverage_tiers_never_impute_missing_microstructure() -> None:
    assert _observation().coverage_tier is CoverageTier.PRICE_PATH
    assert (
        _observation(best_bid=9_990, best_ask=10_000, quote_age_ms=100).coverage_tier
        is CoverageTier.BBO_CONTEXT
    )
    assert (
        _observation(
            best_bid=9_990,
            best_ask=10_000,
            quote_age_ms=100,
            aggressive_sell_ratio=0.8,
            ofi=-1.5,
        ).coverage_tier
        is CoverageTier.MICRO_CONTEXT
    )
    assert (
        _observation(
            best_bid=9_990,
            best_ask=10_000,
            quote_age_ms=3_000,
            aggressive_sell_ratio=0.8,
            ofi=-1.5,
        ).coverage_tier
        is CoverageTier.PRICE_PATH
    )


def test_shock_event_contract_is_source_only_and_broker_forbidden() -> None:
    event = ShockEvent(
        event_id="SMR-1",
        symbol="000001",
        venue="KRX",
        session_bucket="KRX_REGULAR",
        trade_date="2026-08-07",
        detected_at_ms=1_786_000_005_000,
        reference_at_ms=1_786_000_000_000,
        reference_price=10_000,
        shock_price=9_950,
        shock_return_bps=-50,
        return_robust_z=-3.5,
        acceleration_robust_z=-3.0,
        micro_vwap=None,
        coverage_tier=CoverageTier.PRICE_PATH,
        source_quality_status="price_path_only",
    )

    payload = event.as_dict()

    assert payload["schema"] == "scalp_micro_reversion_shock_event_v3"
    assert payload["actual_order_submitted"] is False
    assert payload["broker_order_forbidden"] is True
    assert payload["runtime_effect"] is False
    assert payload["decision_authority"] == (
        "diagnostic_replay_only_no_runtime_activation"
    )
    assert payload["primary_decision_metric"] == "coverage_adjusted_lower_bound_pct"
