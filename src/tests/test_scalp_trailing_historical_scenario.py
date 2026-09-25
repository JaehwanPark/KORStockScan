"""Legacy neutral scenarios remain diagnostic and expose their assumptions."""

from src.engine.scalping.trailing_historical_scenario import (
    summarize_legacy_neutral_scenarios,
)


def _trade(*, trade_id=1, rule="scalp_trailing_take_profit", mfe=None):
    fields = {"mfe_pct": str(mfe)} if mfe is not None else {}
    return {
        "id": trade_id, "rec_date": "2026-09-25", "status": "COMPLETED",
        "strategy": "SCALPING", "buy_price": 10000, "buy_qty": 10,
        "sell_price": 10100, "sell_time": "2026-09-25 10:00:00",
        "profit_rate": 0.77,
        "exit_signal": {"exit_rule": rule, "inferred": True, "fields": fields},
    }


def test_inferred_trailing_peak_produces_only_a_labeled_scenario():
    report = summarize_legacy_neutral_scenarios(
        [_trade()], clean_start="2026-06-05", source_gap_dates=[],
    )
    regular = report["markets"]["REGULAR"]
    assert regular["source_grade_counts"] == {
        "inferred_trailing_rule_assumed_peak_to_sell_path": 1
    }
    assert report["research_candidate"] is None
    assert report["runtime_selected"] is None
    assert "threshold_apply" in report["forbidden_uses"]
    weak = regular["single_axis"]["SCALP_TRAILING_LIMIT_WEAK"]
    assert weak["0.3"]["weak"]["0"]["neutral_scenario_delta_pct"] > 0
    assert weak["0.4"]["weak"]["0"]["neutral_scenario_delta_pct"] == 0
    score = regular["single_axis"]["SCALP_TRAILING_STRONG_AI_SCORE"]
    assert score["65"] == score["85"]


def test_unidentified_peak_stays_neutral_and_invalid_rows_are_separate():
    missing_peak = _trade(rule="scalp_hard_stop_pct")
    missing_peak["id"] = 2
    bad = _trade(trade_id=3)
    bad["sell_price"] = None
    report = summarize_legacy_neutral_scenarios(
        [missing_peak, bad], clean_start="2026-06-05", source_gap_dates=[],
    )
    assert report["excluded_by_id"] == {"3": "missing_price_quantity_or_valid_profit"}
    regular = report["markets"]["REGULAR"]
    assert regular["source_grade_counts"] == {"neutral_unknown_peak": 1}
    candidate = regular["single_axis"]["SCALP_TRAILING_LIMIT_WEAK"]["0.3"]
    assert candidate["weak"]["0"]["neutral_unknown_effect_ids"] == ["2"]
    assert candidate["weak"]["0"]["neutral_scenario_delta_pct"] == 0


def test_reported_mfe_is_distinct_from_inferred_rule_and_slippage_is_sensitivity():
    report = summarize_legacy_neutral_scenarios(
        [_trade(mfe=2.0)], clean_start="2026-06-05", source_gap_dates=[],
    )
    regular = report["markets"]["REGULAR"]
    assert regular["source_grade_counts"] == {
        "reported_mfe_assumed_peak_to_sell_path": 1
    }
    candidate = regular["single_axis"]["SCALP_TRAILING_LIMIT_WEAK"]["0.3"]["weak"]
    assert candidate["0"]["neutral_scenario_delta_pct"] > candidate["100"][
        "neutral_scenario_delta_pct"
    ]
    incumbent = regular["single_axis"]["SCALP_TRAILING_LIMIT_WEAK"]["0.4"]["weak"]
    assert all(row["neutral_scenario_delta_pct"] == 0 for row in incumbent.values())


def test_mfe_below_recorded_sell_return_is_neutral_source_conflict():
    report = summarize_legacy_neutral_scenarios(
        [_trade(mfe=0.1)], clean_start="2026-06-05", source_gap_dates=[],
    )
    regular = report["markets"]["REGULAR"]
    assert regular["source_grade_counts"] == {"neutral_inconsistent_mfe": 1}
    row = regular["single_axis"]["SCALP_TRAILING_LIMIT_WEAK"]["0.3"]["weak"]["0"]
    assert row["neutral_unknown_effect_ids"] == ["1"]
    assert row["neutral_scenario_delta_pct"] == 0


def test_scenario_holdout_tracks_completion_day():
    trades = []
    for trade_id, day in enumerate(("2026-09-23", "2026-09-24", "2026-09-25"), 1):
        trade = _trade(trade_id=trade_id)
        trade["rec_date"] = "2026-09-20"
        trade["sell_time"] = f"{day} 10:00:00"
        trades.append(trade)
    report = summarize_legacy_neutral_scenarios(
        trades, clean_start="2026-06-05", source_gap_dates=[],
    )
    regular = report["markets"]["REGULAR"]
    assert regular["holdout_days"] == ["2026-09-24", "2026-09-25"]
    assert (regular["train_n"], regular["holdout_n"]) == (1, 2)
    candidate = regular["single_axis"]["SCALP_TRAILING_LIMIT_WEAK"]["0.3"]
    assert candidate["train"]["weak"]["0"]["modeled_ids"] == ["1"]
    assert candidate["holdout"]["weak"]["0"]["modeled_ids"] == ["2", "3"]


def test_future_buy_clock_is_excluded_and_recorded_cost_is_labeled():
    valid = _trade()
    valid.update({
        "realized_pnl_krw_source": "broker_fill_prices_fee_aware",
        "realized_pnl_krw": 77,
        "main_lifecycle_fees_taxes_krw": 23,
        "exact_sell_fill_time": "2026-09-25 10:00:00",
    })
    future_buy = _trade(trade_id=2)
    future_buy["buy_time"] = "2026-09-25 10:01:00"
    report = summarize_legacy_neutral_scenarios(
        [valid, future_buy], clean_start="2026-06-05", source_gap_dates=[],
    )
    assert report["cost_evidence_counts"] == {"recorded_fill_cost": 1}
    assert report["excluded_by_id"]["2"] == "sell_before_buy_clock"


def test_duplicate_completed_id_cannot_be_counted_twice():
    report = summarize_legacy_neutral_scenarios(
        [_trade(), _trade()], clean_start="2026-06-05", source_gap_dates=[],
    )
    assert report["duplicate_completed_ids"] == ["1"]
    assert report["excluded_by_id"] == {"1": "duplicate_completed_position_id"}
    assert report["markets"]["REGULAR"]["n"] == 0
