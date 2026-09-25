"""Operational input comparison cannot turn a changed source into live EV."""

from __future__ import annotations

from src.engine.scalping.trailing_operational_replay import (
    AI_CRITICAL_TTL, GRID, NXT_0D, POLL, REST_TIMEOUT, WARN_GAP,
    GRID_VERSION, _digest, operational_shadow_state,
    summarize_operational_input_replay,
)
from src.tests.test_scalp_trailing_four_axis_replay import _path
from src.tests.test_scalp_trailing_start_replay import _at


def _case():
    trade, _ = _path()
    row = trade["timeline"][1]["fields"]
    values = {key: grid[1] for key, grid in GRID.items()}
    values["KORSTOCKSCAN_QUOTE_CONSISTENCY_OK_GAP_BPS"] = 30
    values[POLL] = 250
    values[NXT_0D] = 1500
    values[AI_CRITICAL_TTL] = 45
    values[WARN_GAP] = 80
    values[REST_TIMEOUT] = 400
    digest = _digest(values)
    row.update({
        "position_key": "record:1",
        "evaluator": "fast",
        "operational_threshold_value_sha256": digest,
        "holding_profit_rate_at_eval": 0.9,
        "holding_ai_elapsed_since_review_sec": 25,
        "holding_ai_price_change_since_review_pct": 0,
        "holding_ai_gate_prerequisites_met": True,
        "holding_ai_sim_budget_target": False,
        "holding_ai_fast_reuse_ws_age_sec": 1,
        "ai_score_age_sec": 35,
        "ai_score_effective_at_epoch": row["evaluation_at_epoch"] - 35,
        "quote_consistency_ws_age_ms": 650,
        "quote_consistency_rest_age_ms": 1100,
        "ws_rest_gap_bps": 90,
        "operational_executable_spread_bps": 90,
        "operational_mark_to_bid_gap_bps": 20,
        "operational_quote_warn_tick_floor_bps": 50,
        "holding_rest_request_elapsed_ms": 350,
        "holding_rest_since_last_request_sec": 12,
        "nxt_trailing_bid_guard_ws_0b_age_ms": 1600,
        "nxt_trailing_bid_guard_ws_0d_age_ms": 1400,
    })
    outcome = {"record_id": "1", "trailing_operational_values": values,
               "trailing_operational_value_sha256": digest}
    return trade, outcome


def test_market_axis_screen_keeps_crossing_and_economic_authority_separate():
    trade, outcome = _case()
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    regular = report["markets"]["REGULAR"]["axes"]
    assert len(report["axes"]) == 17
    assert report["research_candidate"] is None
    assert report["runtime_selected"] is None
    assert regular[WARN_GAP]["candidates"]["100"]["changed_input_ids"] == ["1"]
    assert regular[WARN_GAP]["candidates"]["100"]["paired_ev_pct"] is None
    assert regular[AI_CRITICAL_TTL]["candidates"]["30"]["status"] == (
        "action_effect_unidentified"
    )
    assert regular[POLL]["candidates"]["200"]["reason_counts"] == {
        "faster_than_observed_poll_unidentifiable": 1
    }
    assert regular[POLL]["candidates"]["250"]["status"] == "incumbent_observed"
    assert report["markets"]["INTEGRATED_AFTERMARKET"]["axes"][NXT_0D][
        "status"] == "not_exposed"


def test_missing_pre_gate_evidence_and_coverage_are_explicit_gaps():
    trade, outcome = _case()
    row = trade["timeline"][1]["fields"]
    row.pop("holding_rest_request_elapsed_ms")
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    timeout = report["markets"]["REGULAR"]["axes"][REST_TIMEOUT]
    assert timeout["candidates"]["300"]["source_gap_ids"] == ["1"]
    assert timeout["candidates"]["300"]["paired_ev_pct"] is None
    row["tuning_grid_evaluations_since_event"] = 2
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["source_gap_by_id"] == {
        "1": "source_gap_operational_shadow_or_clock_coverage"
    }


def test_population_and_policy_generation_fail_closed():
    trade, outcome = _case()
    assert summarize_operational_input_replay(
        [trade], [outcome], population_complete=False,
    )["status"] == "hold_population_census_or_empty"
    outcome["trailing_operational_value_sha256"] = "0" * 64
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["source_gap_by_id"] == {
        "1": "source_gap_operational_generation_mismatch"
    }


def test_runtime_shadow_proves_skipped_equal_gate_evaluations_but_not_tampering():
    trade, outcome = _case()
    row = trade["timeline"][1]["fields"]
    row["tuning_grid_evaluations_since_event"] = 2
    row["tuning_operational_shadow_version"] = GRID_VERSION
    row["tuning_operational_shadow_sha256"] = _digest(
        operational_shadow_state(row, outcome["trailing_operational_values"])
    )
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["source_gap_by_id"] == {}
    assert report["markets"]["REGULAR"]["axes"][WARN_GAP]["candidates"]["100"][
        "changed_input_ids"] == ["1"]
    row["operational_executable_spread_bps"] = 50
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["source_gap_by_id"] == {
        "1": "source_gap_operational_shadow_or_clock_coverage"
    }


def test_nxt_requires_exact_route_and_premarket_clock_is_not_exit_exposure():
    trade, outcome = _case()
    row = trade["timeline"][1]["fields"]
    row["evaluation_at_epoch"] = _at("2026-09-25 16:30:00")
    row["tuning_market_type"] = "INTEGRATED_AFTERMARKET"
    row["evaluator"] = "normal"
    row["nxt_trailing_bid_guard_ws_0d_item"] = "005930_NX"
    row["nxt_trailing_bid_guard_ws_0d_route"] = "nxt_only"
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    nxt = report["markets"]["INTEGRATED_AFTERMARKET"]["axes"][NXT_0D]
    assert nxt["candidates"]["1000"]["changed_input_ids"] == ["1"]
    row["nxt_trailing_bid_guard_ws_0d_route"] = "krx_only"
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    nxt = report["markets"]["INTEGRATED_AFTERMARKET"]["axes"][NXT_0D]
    assert nxt["candidates"]["1000"]["source_gap_ids"] == ["1"]
    row["evaluation_at_epoch"] = _at("2026-09-25 08:30:00")
    row["tuning_market_type"] = "PREMARKET"
    row["tuning_exit_allowed_by_clock"] = False
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    premarket = report["markets"]["PREMARKET"]
    assert premarket["exposed_ids"] == []
    assert premarket["exit_clock_blocked_ids"] == ["1"]


def test_nxt_missing_trade_clock_is_stale_for_every_candidate():
    from src.engine.scalping.trailing_operational_replay import NXT_0B

    trade, outcome = _case()
    row = trade["timeline"][1]["fields"]
    row["evaluation_at_epoch"] = _at("2026-09-25 16:30:00")
    row["tuning_market_type"] = "INTEGRATED_AFTERMARKET"
    row["evaluator"] = "normal"
    row["nxt_trailing_bid_guard_ws_0d_item"] = "005930_AL"
    row["nxt_trailing_bid_guard_ws_0d_route"] = "krx_nxt_integrated"
    row["nxt_trailing_bid_guard_ws_0b_age_ms"] = "-"
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    candidate = report["markets"]["INTEGRATED_AFTERMARKET"]["axes"][NXT_0B][
        "candidates"
    ]["1000"]
    assert candidate["source_gap_ids"] == []
    assert candidate["changed_input_ids"] == []


def test_normal_ai_gate_reports_cadence_flip_without_assuming_provider_score():
    trade, outcome = _case()
    trade["timeline"][1]["fields"]["evaluator"] = "normal"
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    key = "SCALP_SAFE_PROFIT"
    axis = report["markets"]["REGULAR"]["axes"][key]
    assert axis["candidates"]["1.2"]["changed_input_ids"] == ["1"]
    assert axis["candidates"]["1.2"]["paired_ev_pct"] is None
    assert axis["owner_review"]["required_consumer_scope"] == (
        "real_holding|sim_holding|provider_cost|score_ttl"
    )
    assert report["markets"]["REGULAR"]["axes"][POLL]["status"] == "not_exposed"


def test_sim_cadence_isolated_and_all_source_gaps_block_report_status():
    trade, outcome = _case()
    row = trade["timeline"][1]["fields"]
    row["evaluator"] = "normal"
    row["holding_ai_sim_budget_target"] = True
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    axis = report["markets"]["REGULAR"]["axes"]["SCALP_SAFE_PROFIT"]
    assert axis["candidates"]["1.2"]["source_gap_ids"] == ["1"]
    row["tuning_grid_evaluations_since_event"] = 2
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["status"] == "source_gap_input_path"


def test_shared_quote_warn_gap_respects_tick_floor():
    trade, outcome = _case()
    row = trade["timeline"][1]["fields"]
    row["evaluator"] = "normal"
    row["operational_quote_warn_tick_floor_bps"] = 120
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["markets"]["REGULAR"]["axes"][WARN_GAP]["candidates"][
        "100"
    ]["changed_input_ids"] == []
    row.pop("operational_quote_warn_tick_floor_bps")
    report = summarize_operational_input_replay(
        [trade], [outcome], population_complete=True,
    )
    assert report["markets"]["REGULAR"]["axes"][WARN_GAP]["candidates"][
        "100"
    ]["source_gap_ids"] == ["1"]
