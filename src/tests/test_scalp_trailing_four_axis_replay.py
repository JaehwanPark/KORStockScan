"""Four-axis TP source, runtime vector and paired replay contracts."""

from __future__ import annotations

import json

from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit
from src.engine.scalping.trailing_four_axis_replay import (
    DEFAULT_VECTOR, _metric, prepare_position, replay_vector, summarize_four_axis,
)
from src.engine.scalping.trailing_threshold_policy import (
    START_GRID_PCT, START_MARKETS, THRESHOLD_KEYS, bootstrap_receipt,
    market_values_hash, selected_policy_env, value_hash,
)
from src.tests.test_scalp_trailing_start_replay import _at, _event, _trade


def _path(*, score=50, strong=False, peak=10100, bid=10050, limit=None):
    active_limit = limit if limit is not None else (0.8 if strong else 0.4)
    row = _event("2026-09-25 09:31:55", 1, peak=peak, bid=bid,
                 peak_profit=0.6, limit=active_limit)
    row.update({
        "strong": strong, "ai_score": score, "ai_score_age_sec": 1,
        "trailing_start_pct": 0.6, "strong_score_threshold": 75,
        "ai_score_effective_at_epoch": row["evaluation_at_epoch"] - 1,
        "ai_score_source": "holding_ai", "ai_score_data_quality": "fresh",
        "ai_score_ttl_sec": 10,
        "tuning_four_axis_bin_version": "start_0p1_width_0p1_score_5_v1",
    })
    row["tuning_grid_state"] = json.dumps([
        (str(start), decision.armed, decision.triggered)
        for start in START_GRID_PCT
        for decision in [evaluate_trailing_take_profit(
            peak_price=peak, executable_bid=bid, peak_profit_pct=0.6,
            start_pct=start, strong=strong, weak_limit_pct=active_limit,
            strong_limit_pct=active_limit,
        )]
    ])
    incumbent = {market: dict(DEFAULT_VECTOR) for market in START_MARKETS}
    row.update({
        "scalp_trailing_policy_values": dict(DEFAULT_VECTOR),
        "scalp_trailing_policy_value_sha256": value_hash(DEFAULT_VECTOR),
        "scalp_trailing_market_values": incumbent,
        "scalp_trailing_market_values_sha256": market_values_hash(incumbent),
    })
    trade = _trade()
    trade.update({
        "id": 1, "rec_date": "2026-09-25",
        "timeline": [
            {"stage": "holding_started", "timestamp": "2026-09-25 09:29:30",
             "fields": {"pipeline_lifecycle_population_scope": "real_record_bound"}},
            {"stage": "scalp_trailing_input_transition", "fields": row},
        ],
        "exit_signal": {"timestamp": "2026-09-25 09:32:00"},
        "trailing_event_source_status": "structured_partition_read",
        "trailing_event_source_sha256": "a" * 64,
    })
    return trade, incumbent


def test_bootstrap_contains_twelve_market_values_and_one_vector_hash():
    receipt = bootstrap_receipt({
        "KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_PREMARKET": "80",
        "KORSTOCKSCAN_SCALP_TRAILING_LIMIT_WEAK_REGULAR": "0.5",
        "KORSTOCKSCAN_SCALP_TRAILING_LIMIT_STRONG_INTEGRATED_AFTERMARKET": "0.9",
    }, {})
    assert receipt["schema"] == "scalp_trailing_threshold_receipt_v3"
    assert receipt["market_values"]["PREMARKET"][THRESHOLD_KEYS[1]] == 80
    assert receipt["market_values"]["REGULAR"][THRESHOLD_KEYS[2]] == 0.5
    assert receipt["market_values"]["INTEGRATED_AFTERMARKET"][THRESHOLD_KEYS[3]] == 0.9
    assert receipt["market_values_sha256"] == market_values_hash(receipt["market_values"])


def test_runtime_mechanical_market_vector_is_atomic_and_score_does_not_select_tp(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.trailing_mechanical_policy import (
        TP_KEYS, market_values_hash as mechanical_values_hash,
    )

    scalar = handlers._scalp_trailing_values_for_evaluation(_at("2026-09-25 10:00:00"))[0]
    incumbent = {market: dict(scalar) for market in START_MARKETS}
    incumbent["REGULAR"]["SCALP_TRAILING_LIMIT_WEAK"] = 0.5
    for market, vector in incumbent.items():
        for key, value in vector.items():
            monkeypatch.setenv(f"KORSTOCKSCAN_{key}_{market}", str(value))
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_TRAILING_MECHANICAL_VECTOR_SHA256",
                       mechanical_values_hash(incumbent))
    effective, market = handlers._scalp_trailing_values_for_evaluation(
        _at("2026-09-25 10:00:00"))
    assert market == "REGULAR" and effective["SCALP_TRAILING_LIMIT_WEAK"] == 0.5
    assert set(effective) == set(TP_KEYS)
    assert not handlers._holding_strong_trailing_enabled(
        {"usable_for_negative_exit": False}, 99, threshold=80)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_TRAILING_LIMIT_WEAK_REGULAR", "0.7")
    effective, _ = handlers._scalp_trailing_values_for_evaluation(_at("2026-09-25 10:00:00"))
    assert effective["SCALP_TRAILING_LIMIT_WEAK"] == 0.5
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_TRAILING_MECHANICAL_VECTOR_SHA256", "0" * 64)
    effective, _ = handlers._scalp_trailing_values_for_evaluation(_at("2026-09-25 10:00:00"))
    assert effective == scalar


def test_score_and_strong_width_candidate_change_first_crossing():
    trade, incumbent = _path(score=80, strong=True, limit=0.8)
    prepared = prepare_position(trade)
    assert prepared["source_gap"] is None
    baseline = replay_vector(trade, prepared, incumbent,
                             actual_exit_rule="scalp_hard_stop_pct")
    assert baseline["paired_delta_pnl_krw"] == 0
    score_candidate = {market: dict(value) for market, value in incumbent.items()}
    score_candidate["REGULAR"][THRESHOLD_KEYS[1]] = 85
    score_result = replay_vector(trade, prepared, score_candidate,
                                 actual_exit_rule="scalp_hard_stop_pct")
    assert score_result["status"] == "modeled_earlier_full_sell"
    strong_candidate = {market: dict(value) for market, value in incumbent.items()}
    strong_candidate["REGULAR"][THRESHOLD_KEYS[3]] = 0.4
    strong_result = replay_vector(trade, prepared, strong_candidate,
                                  actual_exit_rule="scalp_hard_stop_pct")
    assert strong_result["status"] == "modeled_earlier_full_sell"
    assert score_result["paired_delta_pnl_krw"] == strong_result["paired_delta_pnl_krw"]
    sensitivity = score_result["paired_delta_pnl_by_slippage_bps"]
    assert sensitivity[0] == score_result["paired_delta_pnl_krw"]
    assert sensitivity[1] < sensitivity[0]
    assert sensitivity[2] < sensitivity[1]
    assert score_result["candidate_execution"]["full_quantity_depth_supported"] is True


def test_earlier_candidate_with_partial_bid_depth_is_censored_not_source_gap():
    trade, incumbent = _path(score=80, strong=True, limit=0.8)
    trade["timeline"][1]["fields"]["executable_bid_qty"] = 4
    candidate = {market: dict(value) for market, value in incumbent.items()}
    candidate["REGULAR"][THRESHOLD_KEYS[1]] = 85
    result = replay_vector(trade, prepare_position(trade), candidate,
                           actual_exit_rule="scalp_hard_stop_pct")

    assert result["status"] == "censored_insufficient_trigger_bid_depth"
    assert result["source_gap"] is None
    assert result["censor_reason"] == "observed_top_bid_depth_covers_only_part_of_position"
    assert result["candidate_execution"]["fillable_qty_at_trigger_bid"] == 4
    assert result["candidate_execution"]["residual_qty"] == 6
    assert result.get("paired_delta_pnl_krw") is None
    assert result["paired_delta_pnl_by_slippage_bps"] is None


def test_earlier_candidate_with_missing_bid_depth_is_source_gap():
    trade, incumbent = _path(score=80, strong=True, limit=0.8)
    trade["timeline"][1]["fields"]["executable_bid_qty"] = None
    candidate = {market: dict(value) for market, value in incumbent.items()}
    candidate["REGULAR"][THRESHOLD_KEYS[1]] = 85
    prepared = prepare_position(trade)
    assert prepared["source_gap"] == "source_gap_executable_bid_depth"
    result = replay_vector(trade, prepared, candidate,
                           actual_exit_rule="scalp_hard_stop_pct")

    assert result["status"] == "source_gap"
    assert result["source_gap"] == "source_gap_executable_bid_depth"
    assert result.get("paired_delta_pnl_krw") is None


def test_later_candidate_is_censored_after_actual_trailing_exit():
    trade, incumbent = _path(score=50, strong=False, peak=10100, bid=10050)
    signal_at = trade["timeline"][1]["fields"]["evaluation_at_epoch"]
    trade["exit_signal"] = {"timestamp": signal_at}
    trade["sell_fill_legs"] = [{"at": "2026-09-25 09:32:00", "qty": 10}]
    candidate = {market: dict(value) for market, value in incumbent.items()}
    candidate["REGULAR"][THRESHOLD_KEYS[2]] = 0.5
    result = replay_vector(trade, prepare_position(trade), candidate,
                           actual_exit_rule="scalp_trailing_take_profit")

    assert result["status"] == "censored_after_actual_take_profit"
    assert result["censor_reason"] == "candidate_trigger_after_observed_take_profit_or_not_observed"
    assert result["paired_delta_pnl_krw"] is None


def test_metric_reports_cost_sensitivity_sign_reversal_on_common_rows():
    metric = _metric([
        ({"buy_fill_amount": 100000.0}, {
            "paired_delta_pnl_krw": 100.0,
            "paired_delta_pnl_by_slippage_bps": (100.0, 0.0, -100.0),
            "modeled_or_observed_pnl_krw": 900.0,
        }),
    ])

    assert metric["execution_slippage_sensitivity"]["0"]["paired_ev_pct"] == 0.1
    assert metric["execution_slippage_sensitivity"]["30"]["delta_net_krw"] == 0
    assert metric["execution_slippage_sensitivity"]["100"]["paired_ev_pct"] == -0.1
    assert metric["slippage_sign_reversal"] is True


def test_sparse_legacy_path_and_partial_sell_are_not_silent_zero_effect():
    trade, incumbent = _path(score=80, strong=True, limit=0.8)
    row = trade["timeline"][1]["fields"]
    row.pop("tuning_four_axis_bin_version")
    row["tuning_grid_evaluations_since_event"] = 2
    assert prepare_position(trade)["source_gap"] == "source_gap_four_axis_crossing_coverage"
    row["tuning_four_axis_bin_version"] = "start_0p1_width_0p1_score_5_v1"
    trade["sell_fill_legs"] = [
        {"at": "2026-09-25 09:31:00", "qty": 1},
        {"at": "2026-09-25 09:33:00", "qty": 9},
    ]
    prepared = prepare_position(trade)
    candidate = {market: dict(value) for market, value in incumbent.items()}
    candidate["REGULAR"][THRESHOLD_KEYS[1]] = 85
    result = replay_vector(trade, prepared, candidate,
                           actual_exit_rule="scalp_hard_stop_pct")
    assert result["status"] == "source_gap"
    assert result["source_gap"] == "source_gap_sell_before_exit_signal"


def test_event_position_key_must_match_completed_trade_id():
    trade, _ = _path()
    trade["timeline"][1]["fields"]["position_key"] = "record:999"

    assert prepare_position(trade)["source_gap"] == "source_gap_position_trade_identity"


def test_four_axis_report_keeps_source_gap_ids_separate():
    trade, _ = _path(score=80, strong=True, limit=0.8)
    bad = {**trade, "id": 2, "timeline": [], "trailing_event_source_sha256": None}
    outcomes = [{"record_id": "1", "rec_date": "2026-09-25",
                 "exit_rule": "scalp_hard_stop_pct"},
                {"record_id": "2", "rec_date": "2026-09-25",
                 "exit_rule": "scalp_hard_stop_pct"}]
    report = summarize_four_axis([trade, bad], outcomes, population_complete=True)
    assert report["strict_completed_position_ids"] == ["1", "2"]
    assert report["source_gap_by_id"]["2"] == "source_gap_structured_event_provenance"
    assert report["markets"]["REGULAR"]["excluded_ids"] == ["2"]
    assert report["runtime_selected"] is None
    mismatch = summarize_four_axis([trade], outcomes, population_complete=True)
    assert mismatch["status"] == "hold_position_identity_census"
    assert mismatch["strict_completed_position_ids"] == ["1"]
    invalid_date = summarize_four_axis(
        [trade], [{"record_id": "1", "rec_date": "bad-date",
                   "completion_observed_date": "bad-date",
                   "exit_rule": "scalp_hard_stop_pct"}],
        population_complete=True,
    )
    assert invalid_date["source_gap_by_id"]["1"] == "source_gap_completed_outcome_date"


def test_selected_policy_requires_exact_report_candidate_and_canary():
    vector = {market: dict(DEFAULT_VECTOR) for market in START_MARKETS}
    vector["REGULAR"][THRESHOLD_KEYS[3]] = 0.7
    digest = market_values_hash(vector)
    report = {
        "date": "2026-09-25", "completed_population_quality": {"complete": True},
        "trailing_four_axis_market_tuning": {
            "population_complete": True,
            "status": "research_candidate_holdout_positive_review_required",
            "research_candidate": {
                "values": vector, "market_values_sha256": digest,
                "decision_authority": "research_candidate_requires_policy_selection",
            },
            "joint_selection_evidence": {
                "winner_sha256": digest, "tail_review_required": False,
                "holdout_conservative_delta_krw": 200,
                "holdout_conservative_worst_slippage_delta_krw": 20,
                "holdout_worst_slippage_min_day_ev_pct": 0.01,
            },
        },
    }
    policy = {
        "schema": "scalp_trailing_four_axis_selected_policy_v1",
        "family": "scalp_trailing_four_axis_selector",
        "target_date": "2026-09-28", "source_date": "2026-09-25",
        "source_report_sha256": "b" * 64,
        "allowed_runtime_apply": True, "runtime_effect": True,
        "apply_scope": "one_stage_canary", "market_values": vector,
        "market_values_sha256": digest,
        "rollback_market_values_sha256": "a" * 64,
        "selection_review": {
            "status": "reviewed_one_stage_canary", "candidate_sha256": digest,
            "source_quality": "pass", "execution_model": "pass",
            "same_stage_owner": "scalp_trailing_take_profit",
            "rollback_sha256": "a" * 64,
        },
    }
    selected = selected_policy_env(policy, report, target_date="2026-09-28",
                                   report_sha256="b" * 64)
    assert len(selected) == 12
    from pytest import raises
    without_review = {**policy, "selection_review": {}}
    with raises(ValueError, match="selection_review_missing_or_invalid"):
        selected_policy_env(without_review, report, target_date="2026-09-28",
                            report_sha256="b" * 64)
    with raises(ValueError, match="source_report_binding_invalid"):
        selected_policy_env(policy, report, target_date="2026-09-28",
                            report_sha256="c" * 64)
    weak_stress = {
        **report,
        "trailing_four_axis_market_tuning": {
            **report["trailing_four_axis_market_tuning"],
            "joint_selection_evidence": {
                **report["trailing_four_axis_market_tuning"]["joint_selection_evidence"],
                "holdout_conservative_worst_slippage_delta_krw": -1,
            },
        },
    }
    with raises(ValueError, match="selection_safety_evidence_invalid"):
        selected_policy_env(policy, weak_stress, target_date="2026-09-28",
                            report_sha256="b" * 64)
    policy["apply_scope"] = "all_positions"
    with raises(ValueError, match="selection_authority_invalid"):
        selected_policy_env(policy, report, target_date="2026-09-28",
                            report_sha256="b" * 64)


def test_arm_latch_crosses_closed_regular_to_aftermarket_gap():
    from src.engine.scalping.trailing_threshold_policy import closed_exit_gap

    before = _at("2026-09-25 15:29:59")
    after = _at("2026-09-25 16:00:00")
    assert closed_exit_gap(before, after)
    assert not closed_exit_gap(_at("2026-09-25 09:30:00"),
                               _at("2026-09-25 09:31:00"))
    trade, incumbent = _path(score=50, strong=False, peak=10100, bid=10090)
    first = trade["timeline"][1]["fields"]
    first.update(evaluation_at_epoch=before, bid_source_received_at_epoch=before-.1,
                 ai_score_effective_at_epoch=before-1)
    second = _event("2026-09-25 16:00:00", 2, peak=10100,
                    bid=10040, peak_profit=0.6)
    second.update({key: value for key, value in first.items()
                   if key.startswith("scalp_trailing_") or key.startswith("ai_score_")
                   or key in {"ai_score", "trailing_start_pct", "strong_score_threshold"}})
    second.update(event_sequence=2, evaluation_at_epoch=after,
                  bid_source_received_at_epoch=after-.1,
                  ai_score_effective_at_epoch=after-1,
                  tuning_market_type="INTEGRATED_AFTERMARKET",
                  tuning_four_axis_bin_version="start_0p1_width_0p1_score_5_v1")
    trade["timeline"][0]["timestamp"] = "2026-09-25 15:29:58"
    trade["timeline"].append({"stage": "scalp_trailing_input_transition",
                              "fields": second})
    trade["exit_signal"] = {"timestamp": "2026-09-25 16:00:00"}
    trade["sell_fill_legs"] = [{"at": "2026-09-25 16:00:01", "qty": 10}]
    prepared = prepare_position(trade)
    assert prepared["source_gap"] is None
    result = replay_vector(trade, prepared, incumbent,
                           actual_exit_rule="scalp_trailing_take_profit")
    assert result["status"] == "same_observed_exit"
    assert result["first_arm_at_epoch"] == before
    assert result["first_trigger_market"] == "INTEGRATED_AFTERMARKET"


def test_four_axis_start_only_matches_existing_start_replay_and_cache():
    from src.engine.scalping.trailing_start_replay import replay_start_grid

    trade, incumbent = _path(score=50, strong=False, peak=10100, bid=10050)
    first = _event("2026-09-25 09:31:58", 1, peak=10040,
                   bid=9990, peak_profit=0.4)
    second = _event("2026-09-25 09:32:00", 2, peak=10100,
                    bid=10050, peak_profit=0.6)
    source = trade["timeline"][1]["fields"]
    for row in (first, second):
        row.update({key: value for key, value in source.items()
                    if key.startswith("scalp_trailing_") or key.startswith("ai_score_")
                    or key in {"ai_score", "trailing_start_pct", "strong_score_threshold"}})
        row["ai_score_effective_at_epoch"] = row["evaluation_at_epoch"] - 1
        row["tuning_four_axis_bin_version"] = "start_0p1_width_0p1_score_5_v1"
    trade["timeline"] = [trade["timeline"][0],
                         {"stage": "scalp_trailing_input_transition", "fields": first},
                         {"stage": "scalp_trailing_input_transition", "fields": second}]
    prepared = prepare_position(trade)
    assert prepared["source_gap"] is None
    candidate = {market: dict(vector) for market, vector in incumbent.items()}
    candidate["REGULAR"][THRESHOLD_KEYS[0]] = 0.3
    four = replay_vector(trade, prepared, candidate,
                         actual_exit_rule="scalp_trailing_take_profit")
    fresh = replay_vector(trade, prepare_position(trade), candidate,
                          actual_exit_rule="scalp_trailing_take_profit")
    start = replay_start_grid(trade, [first, second],
                              actual_exit_rule="scalp_trailing_take_profit",
                              actual_exit_signal=trade["exit_signal"],
                              incumbent_start_pct=0.6)
    assert four == fresh
    assert four["status"] == start["markets"]["REGULAR"]["0.3"]["status"]
    assert four["paired_delta_pnl_krw"] == start["markets"]["REGULAR"]["0.3"][
        "paired_delta_pnl_krw"
    ]


def test_market_grid_always_includes_the_observed_incumbent():
    trade, vector = _path(score=80, strong=True, limit=0.8)
    vector["REGULAR"][THRESHOLD_KEYS[0]] = 1.3
    row = trade["timeline"][1]["fields"]
    row["scalp_trailing_market_values"] = vector
    row["scalp_trailing_market_values_sha256"] = market_values_hash(vector)
    row["trailing_start_pct"] = 1.3
    report = summarize_four_axis(
        [trade], [{"record_id": "1", "rec_date": "2026-09-25",
                   "exit_rule": "scalp_hard_stop_pct"}], population_complete=True,
    )
    assert report["source_gap_by_id"] == {}
    assert 1.3 in report["markets"]["REGULAR"]["grid"][THRESHOLD_KEYS[0]]


def test_market_candidate_metrics_use_one_common_position_support():
    good, _ = _path(score=80, strong=True, limit=0.8)
    shallow, _ = _path(score=80, strong=True, limit=0.8)
    shallow["id"] = 2
    shallow["timeline"][1]["fields"]["position_key"] = "record:2"
    shallow["timeline"][1]["fields"]["executable_bid_qty"] = 1
    outcomes = [
        {"record_id": str(trade["id"]), "rec_date": "2026-09-25",
         "exit_rule": "scalp_hard_stop_pct"}
        for trade in (good, shallow)
    ]
    report = summarize_four_axis([good, shallow], outcomes,
                                 population_complete=True)
    regular = report["markets"]["REGULAR"]
    assert regular["common_support_ids"] == ["1"]
    assert regular["grid_censored_or_gap_ids"] == ["2"]
    score = regular["axes"][THRESHOLD_KEYS[1]]
    assert score["75"]["pairable_ids"] == ["1", "2"]
    assert score["75"]["comparison_support_ids"] == ["1"]
    assert score["75"]["train"]["n"] == 1
    assert regular["axes"][THRESHOLD_KEYS[3]]["0.4"]["train"]["n"] == 1


def test_invalid_historical_width_combinations_do_not_empty_valid_support():
    first, _ = _path(score=80, strong=True, limit=0.8)
    second, vector = _path(score=80, strong=True, limit=0.6)
    second["id"] = 2
    row = second["timeline"][1]["fields"]
    row["position_key"] = "record:2"
    vector["REGULAR"][THRESHOLD_KEYS[2]] = 0.6
    vector["REGULAR"][THRESHOLD_KEYS[3]] = 0.6
    row["scalp_trailing_market_values"] = vector
    row["scalp_trailing_market_values_sha256"] = market_values_hash(vector)
    report = summarize_four_axis(
        [first, second],
        [{"record_id": str(trade["id"]), "rec_date": "2026-09-25",
          "exit_rule": "scalp_hard_stop_pct"} for trade in (first, second)],
        population_complete=True,
    )
    regular = report["markets"]["REGULAR"]
    assert regular["common_support_ids"] == ["1", "2"]
    assert "0.8" not in regular["axes"][THRESHOLD_KEYS[2]]
    assert f"{THRESHOLD_KEYS[2]}=0.8" in regular["invalid_vector_candidates"]


def test_holdout_uses_completed_outcome_day_not_entry_day():
    trades = []
    outcomes = []
    for trade_id, entry_day in enumerate(("2026-09-10", "2026-09-11", "2026-09-12"), 1):
        trade, _ = _path(score=80, strong=True, limit=0.8)
        trade["id"] = trade_id
        trade["rec_date"] = entry_day
        trade["timeline"][1]["fields"]["position_key"] = f"record:{trade_id}"
        trades.append(trade)
        outcomes.append({
            "record_id": str(trade_id), "rec_date": entry_day,
            "completion_observed_date": "2026-09-25",
            "exit_rule": "scalp_hard_stop_pct",
        })
    report = summarize_four_axis(trades, outcomes, population_complete=True)
    assert report["holdout_days"] == []
    assert report["entry_date_fallback_ids"] == []


def test_completion_day_must_match_final_sell_fill_clock():
    trade, _ = _path(score=80, strong=True, limit=0.8)
    report = summarize_four_axis(
        [trade], [{"record_id": "1", "rec_date": "2026-09-20",
                   "completion_observed_date": "2026-09-24",
                   "exit_rule": "scalp_hard_stop_pct"}],
        population_complete=True,
    )
    assert report["completion_clock_mismatch_ids"] == ["1"]
    assert report["source_gap_by_id"]["1"] == "source_gap_completion_fill_day_mismatch"
