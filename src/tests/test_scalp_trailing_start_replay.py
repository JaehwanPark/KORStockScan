"""Report-only three-market trailing start contracts."""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit
from src.engine.scalping.trailing_start_replay import (
    replay_start_grid,
    summarize_start_grid,
)
from src.engine.scalping.trailing_threshold_policy import (
    GRID_VERSION,
    START_GRID_PCT,
    bootstrap_receipt,
    market_type_at,
    start_values_hash,
)
from src.trading.market import session_contract


def _at(clock: str) -> float:
    return datetime.fromisoformat(clock).replace(
        tzinfo=ZoneInfo("Asia/Seoul")
    ).timestamp()


def _event(clock: str, sequence: int, *, peak: int, bid: int,
           peak_profit: float, limit: float = 0.4) -> dict:
    at = _at(clock)
    states = []
    for start in START_GRID_PCT:
        decision = evaluate_trailing_take_profit(
            peak_price=peak, executable_bid=bid,
            peak_profit_pct=peak_profit, start_pct=start,
            strong=False, weak_limit_pct=limit, strong_limit_pct=limit,
        )
        states.append((str(start), decision.armed, decision.triggered))
    return {
        "observation_grid_version": GRID_VERSION,
        "tuning_start_grid_version": "start_0p3_to_1p2_step_0p1_v1",
        "event_sequence": sequence,
        "observation_coverage_exhausted": False,
        "observation_telemetry_gap": False,
        "tuning_grid_source_complete": True,
        "tuning_grid_evaluations_since_event": 1,
        "tuning_grid_max_evaluation_gap_sec": 0.0,
        "evaluation_at_epoch": at,
        "bid_source_received_at_epoch": at - 0.1,
        "tuning_market_type": market_type_at(at),
        "tuning_exit_allowed_by_clock": True,
        "tuning_session_contract_version": (
            session_contract.resolve_market_session(
                datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul"))
            ).contract_version
        ),
        "peak_price": peak,
        "peak_profit_pct": peak_profit,
        "executable_bid": bid,
        "executable_bid_qty": 20,
        "strong": False,
        "trailing_limit_pct": limit,
        "tuning_grid_state": json.dumps(states),
        "position_key": "record:1",
        "scalp_trailing_policy_value_sha256": "policy-hash",
        "ai_score_usable": True,
        "quote_consistency_state": "consistent",
        "executable_spread_bps": 12.0,
        "bid_source": "fresh_ws_executable_bid",
    }


def _trade() -> dict:
    return {
        "buy_filled_qty": 10,
        "buy_fill_amount": 100000.0,
        "effective_cost_rate": 0.0023,
        "realized_pnl_krw": 100.0,
        "buy_fill_legs": [{"at": "2026-09-25 09:29:00", "qty": 10,
                            "amount_krw": 100000.0}],
        "sell_fill_legs": [{"at": "2026-09-25 09:33:00", "qty": 10}],
    }


def test_market_type_is_fixed_to_three_research_sessions():
    assert market_type_at(_at("2026-09-25 08:30:00")) == "PREMARKET"
    assert market_type_at(_at("2026-09-25 10:00:00")) == "REGULAR"
    assert market_type_at(_at("2026-09-25 17:00:00")) == "INTEGRATED_AFTERMARKET"
    assert market_type_at(_at("2026-09-25 15:40:00")) is None


def test_structured_pipeline_string_fields_round_trip_into_replay():
    from src.engine.sniper_trade_review_report import _decode_threshold_json_fields

    row = _event("2026-09-25 09:30:00", 1, peak=10040,
                 bid=9990, peak_profit=0.4)
    row["scalp_trailing_start_by_market"] = json.dumps({
        "PREMARKET": 0.6, "REGULAR": 0.6,
        "INTEGRATED_AFTERMARKET": 0.6,
    })
    decoded = _decode_threshold_json_fields({
        key: str(value) for key, value in row.items()
    })
    assert decoded["scalp_trailing_start_by_market"]["REGULAR"] == 0.6
    replay = replay_start_grid(
        _trade(), [decoded], actual_exit_rule="scalp_hard_stop_pct",
        actual_exit_signal={"timestamp": "2026-09-25 09:30:10"},
        incumbent_start_pct=0.6,
    )
    assert replay["source_gap"] is None


def test_bootstrap_receipt_seals_three_values_without_changing_scalar():
    receipt = bootstrap_receipt(
        {"KORSTOCKSCAN_SCALP_TRAILING_START_PCT": "0.6",
         "KORSTOCKSCAN_SCALP_TRAILING_START_PCT_PREMARKET": "0.7"},
        {"KORSTOCKSCAN_SCALP_TRAILING_START_PCT_PREMARKET": "test_owner"},
    )
    assert receipt["values"]["SCALP_TRAILING_START_PCT"] == 0.6
    assert receipt["start_by_market"] == {
        "PREMARKET": 0.7,
        "REGULAR": 0.6,
        "INTEGRATED_AFTERMARKET": 0.6,
    }
    assert receipt["start_by_market_sha256"] == start_values_hash(
        receipt["start_by_market"]
    )


def test_live_market_start_requires_matching_bootstrap_hash(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.trailing_mechanical_policy import (
        DEFAULTS as mechanical_defaults, START_MARKETS as mechanical_markets,
        market_values_hash as mechanical_hash,
    )

    values = {"PREMARKET": 0.7, "REGULAR": 0.6,
              "INTEGRATED_AFTERMARKET": 0.8}
    for market, value in values.items():
        monkeypatch.setenv(
            f"KORSTOCKSCAN_SCALP_TRAILING_START_PCT_{market}", str(value)
        )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_TRAILING_START_BY_MARKET_SHA256",
        start_values_hash(values),
    )
    # The retired start-only receipt cannot select live M1 TP values.
    assert handlers._scalp_trailing_start_for_evaluation(
        _at("2026-09-25 17:00:00")
    ) == (0.4, "INTEGRATED_AFTERMARKET")
    vector = {market: dict(mechanical_defaults) for market in mechanical_markets}
    for market, value in values.items():
        vector[market]["SCALP_TRAILING_START_PCT"] = value
        monkeypatch.setenv(f"KORSTOCKSCAN_SCALP_TRAILING_START_PCT_{market}", str(value))
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_TRAILING_MECHANICAL_VECTOR_SHA256",
                       mechanical_hash(vector))
    assert handlers._scalp_trailing_start_for_evaluation(
        _at("2026-09-25 17:00:00")
    ) == (0.8, "INTEGRATED_AFTERMARKET")
    # A running process keeps its verified bootstrap vector. Replacing one
    # environment value without a new policy hash cannot reselect the vector.
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_TRAILING_START_PCT_REGULAR", "0.9")
    assert handlers._scalp_trailing_start_for_evaluation(
        _at("2026-09-25 17:00:00")
    ) == (0.8, "INTEGRATED_AFTERMARKET")


def test_replay_models_only_earlier_sell_and_censors_later_sell():
    rows = [
        _event("2026-09-25 09:30:00", 1, peak=10040, bid=9990,
               peak_profit=0.4),
        _event("2026-09-25 09:32:00", 2, peak=10100, bid=10050,
               peak_profit=0.6),
    ]
    replay = replay_start_grid(
        _trade(), rows,
        actual_exit_rule="scalp_trailing_take_profit",
        actual_exit_signal={"timestamp": "2026-09-25 09:32:00"},
        incumbent_start_pct=0.6,
    )
    assert replay["source_gap"] is None
    regular = replay["markets"]["REGULAR"]
    assert regular["0.3"]["status"] == "modeled_earlier_full_sell"
    assert regular["0.3"]["paired_delta_pnl_krw"] < 0
    assert regular["0.6"]["status"] == "same_observed_exit"
    assert regular["0.6"]["paired_delta_pnl_krw"] == 0
    assert regular["0.7"]["status"] == "censored_after_actual_take_profit"
    assert regular["0.7"]["paired_delta_pnl_krw"] is None


def test_other_exit_remains_in_replay_and_bad_path_fails_closed():
    rows = [
        _event("2026-09-25 09:30:00", 1, peak=10040, bid=9990,
               peak_profit=0.4),
        _event("2026-09-25 09:31:55", 2, peak=10040, bid=9990,
               peak_profit=0.4),
    ]
    replay = replay_start_grid(
        _trade(), rows,
        actual_exit_rule="scalp_hard_stop_pct",
        actual_exit_signal={"timestamp": "2026-09-25 09:32:00"},
        incumbent_start_pct=0.6,
    )
    assert replay["source_gap"] is None
    assert replay["markets"]["REGULAR"]["0.3"]["status"] == (
        "modeled_earlier_full_sell"
    )
    assert replay["markets"]["REGULAR"]["0.6"]["status"] == (
        "same_observed_exit"
    )
    outcomes = [{"record_id": "1", "rec_date": "2026-09-25",
                 "buy_fill_amount": 100000.0,
                 "trailing_start_market_replay": replay}]
    summary = summarize_start_grid(outcomes)
    assert summary["markets"]["REGULAR"]["exposed_ids"] == ["1"]
    assert summary["markets"]["REGULAR"]["research_candidate_value_pct"] is None
    rows[0]["tuning_grid_source_complete"] = False
    bad = replay_start_grid(
        _trade(), rows, actual_exit_rule="scalp_hard_stop_pct",
        actual_exit_signal={"timestamp": "2026-09-25 09:32:00"},
        incumbent_start_pct=0.6,
    )
    assert bad["source_gap"] == "source_gap_tuning_input_quality"


def test_market_denominator_keeps_unexposed_completed_position():
    rows = [_event("2026-09-25 09:30:00", 1, peak=10040,
                   bid=9990, peak_profit=0.4)]
    replay = replay_start_grid(
        _trade(), rows, actual_exit_rule="scalp_hard_stop_pct",
        actual_exit_signal={"timestamp": "2026-09-25 09:30:10"},
        incumbent_start_pct=0.6,
    )
    assert replay["source_gap"] is None
    outcome = {"record_id": "1", "rec_date": "2026-09-25",
               "buy_fill_amount": 100000.0,
               "trailing_start_market_replay": replay}
    premarket = summarize_start_grid([outcome])["markets"]["PREMARKET"]
    assert premarket["exposed_ids"] == []
    assert premarket["common_grid_ids"] == ["1"]
    assert premarket["candidate_metrics"]["0.3"]["train_ev_pct"] == 0.0
    assert premarket["candidate_metrics"]["0.3"]["pairable_ids"] == ["1"]


def test_replay_rejects_sparse_exit_clock_and_unreproduced_incumbent():
    rows = [_event("2026-09-25 09:30:00", 1, peak=10040,
                   bid=9990, peak_profit=0.4)]
    sparse = replay_start_grid(
        _trade(), rows, actual_exit_rule="scalp_hard_stop_pct",
        actual_exit_signal={"timestamp": "2026-09-25 09:32:00"},
    )
    assert sparse["source_gap"] == "source_gap_exit_signal_coverage"
    rows[0]["tuning_grid_max_evaluation_gap_sec"] = 3.0
    bad_interval = replay_start_grid(
        _trade(), rows, actual_exit_rule="scalp_hard_stop_pct",
        actual_exit_signal={"timestamp": "2026-09-25 09:30:10"},
    )
    assert bad_interval["source_gap"] == "source_gap_evaluation_coverage"
    rows[0]["tuning_grid_max_evaluation_gap_sec"] = 0.0
    wrong_incumbent = replay_start_grid(
        _trade(), rows, actual_exit_rule="scalp_trailing_take_profit",
        actual_exit_signal={"timestamp": "2026-09-25 09:30:10"},
    )
    assert wrong_incumbent["source_gap"] == (
        "source_gap_incumbent_trigger_not_reproduced"
    )


def test_market_change_keeps_prior_arm_for_later_market_signal():
    trade = _trade()
    trade["buy_fill_legs"][0]["at"] = "2026-09-25 08:58:00"
    trade["sell_fill_legs"][0]["at"] = "2026-09-25 09:00:06"
    rows = [
        _event("2026-09-25 08:59:59", 1, peak=10100,
               bid=10090, peak_profit=0.7),
        _event("2026-09-25 09:00:00", 2, peak=10100,
               bid=10050, peak_profit=0.7),
    ]
    rows[1]["tuning_grid_max_evaluation_gap_sec"] = 1.0
    replay = replay_start_grid(
        trade, rows, actual_exit_rule="scalp_trailing_take_profit",
        actual_exit_signal={"timestamp": "2026-09-25 09:00:00"},
    )
    assert replay["source_gap"] == "source_gap_market_exit_clock_blocked"
