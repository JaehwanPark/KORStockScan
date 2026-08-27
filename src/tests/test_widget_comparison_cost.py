from datetime import date, datetime, timezone

import pytest

from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    cost_aware_return_pct,
    modeled_execution_economics,
    round_trip_cost_pct,
)


def test_cost_policy_changes_on_effective_date_and_is_hash_bound() -> None:
    legacy = comparison_cost_contract(date(2026, 8, 17))
    current = comparison_cost_contract(date(2026, 8, 18))

    assert legacy["round_trip_cost_pct"] == 0.2
    assert current["round_trip_cost_pct"] == 0.23
    assert current["buy_fee_bps"] == 1.5
    assert current["sell_fee_bps"] == 1.5
    assert current["statutory_sell_tax_bps"] == 20.0
    assert len(current["contract_sha256"]) == 64
    assert current["runtime_effect"] is False


def test_pre_clean_baseline_cost_is_rejected() -> None:
    with pytest.raises(ValueError, match="pre_clean_baseline"):
        round_trip_cost_pct(date(2026, 6, 4))


def test_modeled_execution_cost_uses_buy_and_sell_notionals() -> None:
    economics = modeled_execution_economics(
        buy_notional_krw=773_000,
        sell_notional_krw=762_000,
        trade_date=date(2026, 8, 27),
    )

    assert economics["gross_profit_krw"] == -11_000
    assert economics["modeled_total_cost_krw"] == pytest.approx(1754.25)
    assert economics["modeled_net_profit_krw"] == pytest.approx(-12754.25)
    assert economics["broker_receipt_exact"] is False


def test_aware_datetime_is_resolved_to_kst_trade_date() -> None:
    contract = comparison_cost_contract(
        datetime(2026, 8, 17, 16, 0, tzinfo=timezone.utc)
    )

    assert contract["trade_date"] == "2026-08-18"
    assert contract["round_trip_cost_pct"] == 0.23


@pytest.mark.parametrize(
    ("buy_notional", "sell_notional"),
    ((0, 1), (-1, 1), (1, -1), (float("nan"), 1), (1, float("inf"))),
)
def test_modeled_execution_rejects_invalid_notionals(
    buy_notional: float, sell_notional: float
) -> None:
    with pytest.raises(ValueError, match="execution_notional_invalid"):
        modeled_execution_economics(
            buy_notional_krw=buy_notional,
            sell_notional_krw=sell_notional,
            trade_date=date(2026, 8, 27),
        )


def test_cost_aware_return_rejects_nonfinite_value() -> None:
    with pytest.raises(ValueError, match="gross_return_invalid"):
        cost_aware_return_pct(float("nan"), trade_date=date(2026, 8, 27))
