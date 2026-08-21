import json

import pytest

from src.engine.monitoring import scalping_pyramid_quality_calibration as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
        },
    )


def _row(record_id, label, *, max_profit_seen=None, final_profit_rate=None):
    row = {
        "record_id": str(record_id),
        "pyramid_feedback_label": label,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "decision_authority": "source_only_pyramid_intraday_feedback_no_runtime_mutation",
        "forbidden_uses": ["intraday_threshold_mutation"],
    }
    if max_profit_seen is not None:
        row["max_profit_seen"] = max_profit_seen
    if final_profit_rate is not None:
        row["final_profit_rate"] = final_profit_rate
    return row


def _feedback(
    path,
    rows,
    *,
    source_quality="pass",
    one_share_rows=None,
    normal_winner_expansion_rows=None,
    real_scale_in_performance_rows=None,
    post_probe_real_outcome_contract=False,
):
    payload = {
        "report_type": "scalping_pyramid_intraday_feedback",
        "target_date": path.stem.rsplit("_", 1)[-1],
        "source_quality": {"status": source_quality},
        "pyramid_feedback_rows": rows,
    }
    if one_share_rows is not None:
        payload["one_share_pyramid_opportunity_rows"] = one_share_rows
    if normal_winner_expansion_rows is not None:
        payload["normal_winner_expansion_rows"] = normal_winner_expansion_rows
    if real_scale_in_performance_rows is not None:
        payload["real_scale_in_performance_rows"] = real_scale_in_performance_rows
        payload["real_scale_in_performance_metric_contract"] = {
            "metric_role": "real_scale_in_execution_outcome_attribution"
        }
    if post_probe_real_outcome_contract:
        payload["post_probe_real_outcome_metric_contract"] = {
            "metric_role": "multi_leg_post_probe_real_outcome_attribution"
        }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_pyramid_quality_calibration_holds_when_sample_floor_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [_row(i, "pyramid_overheat_or_reversal_risk") for i in range(3)],
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert "rolling_closed_pyramid_rows_lt_20" in candidate["calibration_reason"]


def test_pyramid_quality_calibration_excludes_blocked_source_date(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    allowed = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-02.json",
        [_row(1, "pyramid_correctly_blocked")],
    )
    blocked = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [_row(2, "pyramid_would_have_helped")],
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "pass" if source_date == "2026-07-02" else "fail",
            "tuning_input_allowed": source_date == "2026-07-02",
            "allowed_runtime_apply": source_date == "2026-07-02",
            "source_quality_gate": (
                "pass" if source_date == "2026-07-02" else "blocked_contract_gap"
            ),
            "blocked_reason": (
                None if source_date == "2026-07-02" else "blocked_contract_gap"
            ),
        },
    )

    report = mod.build_report(
        "2026-07-03", input_paths=[allowed, blocked], generated_at="fixed"
    )
    candidate = report["calibration_candidates"][0]

    assert candidate["sample_count"] == 1
    assert candidate["cumulative_quality_window"]["source_dates"] == ["2026-07-02"]
    assert (
        candidate["cumulative_quality_window"]["source_quality_excluded_date_count"]
        == 1
    )
    assert report["source_quality"]["input_paths"] == [str(allowed)]


def test_pyramid_quality_calibration_reversal_cluster_tightens_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_overheat_or_reversal_risk") for i in range(14)]
    rows.extend(_row(100 + i, "pyramid_correctly_blocked") for i in range(6))
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["allowed_runtime_apply"] is True
    assert (
        candidate["recommended_values"]["min_ai_score"]
        == candidate["current_values"]["min_ai_score"] + 5.0
    )
    assert candidate["recommended_values"]["max_micro_vwap_bps"] == (
        candidate["current_values"]["max_micro_vwap_bps"] - 10.0
    )
    assert "SCALPING_PYRAMID_MAX_ADD_QTY_RATIO" not in candidate["target_env_keys"]


def test_pyramid_quality_calibration_recovery_cluster_loosens_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(14)]
    rows.extend(_row(100 + i, "pyramid_correctly_blocked") for i in range(6))
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["allowed_runtime_apply"] is True
    assert (
        candidate["recommended_values"]["min_ai_score"]
        == candidate["current_values"]["min_ai_score"] - 5.0
    )
    assert (
        candidate["recommended_values"]["max_spread_bps"]
        == candidate["current_values"]["max_spread_bps"] + 10.0
    )
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True


def test_pyramid_quality_calibration_blocks_pressure_provenance_missing_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in rows:
        row.update(
            {
                "buy_pressure_10t": 55.0,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="pressure_provenance_missing",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert "rolling_closed_pyramid_rows_lt_20" in candidate["calibration_reason"]
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["source_quality_status"] == "blocked"
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "pressure_provenance_invalid": 20
    }


def test_pyramid_quality_calibration_blocks_pressure_provenance_unusable_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in rows:
        row.update(
            {
                "buy_pressure_10t": 55.0,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="pressure_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "pressure_provenance_invalid": 20
    }


def test_pyramid_quality_calibration_blocks_micro_vwap_provenance_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in rows:
        row.update(
            {
                "curr_vs_micro_vwap_bp": 12.0,
                "micro_vwap_available": False,
                "minute_candle_window_fresh": False,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="micro_vwap_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "micro_vwap_provenance_invalid": 20
    }


def test_pyramid_quality_calibration_keeps_valid_rows_from_mixed_quality_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    invalid_rows = [_row(100 + i, "pyramid_would_have_helped") for i in range(2)]
    for row in invalid_rows:
        row.update(
            {
                "curr_vs_micro_vwap_bp": 15.0,
                "micro_vwap_available": False,
                "minute_candle_window_fresh": False,
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        rows + invalid_rows,
        source_quality="micro_vwap_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "pass_with_row_exclusions"
    assert candidate["sample_count"] == 20
    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["source_metrics"]["source_quality_excluded_row_count"] == 2
    assert report["runtime_update_contract"]["max_runtime_apply_count"] == 1
    assert (
        report["runtime_update_contract"]["quality_update_id"]
        == candidate["quality_update_id"]
    )


def test_negative_normal_winner_ev_vetoes_loosening_and_isolates_bad_receipt(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    normal_rows = [
        {
            "record_id": f"normal-{index}",
            "normal_winner_expansion_label": "correctly_not_expanded_or_reversal",
            "normal_winner_expansion_source_quality_valid": True,
            "normal_winner_expansion_incremental_final_profit_pct": -0.3,
            "normal_winner_expansion_candidate_notional_krw": 100_000,
            "effective_venue": "KRX",
            "venue_source_quality_valid": True,
            "market_session_bucket": "krx_regular",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
            ),
            "forbidden_uses": ["intraday_runtime_apply"],
        }
        for index in range(20)
    ]
    invalid_receipt_row = {
        "record_id": "invalid-receipt",
        "scale_in_outcome_cohort": "normal_pyramid",
        "closed": True,
        "source_quality_valid": False,
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        source_quality="real_scale_in_receipt_source_quality_incomplete",
        one_share_rows=one_share_rows,
        normal_winner_expansion_rows=normal_rows,
        real_scale_in_performance_rows=[invalid_receipt_row],
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "pass_with_row_exclusions"
    assert candidate["calibration_state"] == "hold"
    assert candidate["calibration_reason"].startswith(
        "normal_winner_expansion_non_positive_ev_hold:"
    )
    assert candidate["recommended_values"] == candidate["current_values"]
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert candidate["source_metrics"][
        "normal_winner_expansion_loosen_veto_applied"
    ] is True
    assert candidate["source_metrics"]["source_quality_excluded_row_count"] == 1
    assert candidate["source_metrics"]["source_quality_exclusion_reasons"] == {
        "real_scale_in_receipt_source_quality_incomplete": 1
    }


def test_pyramid_quality_calibration_uses_all_one_share_rows_for_thresholds(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    legacy_rows = [_row(i, "pyramid_overheat_or_reversal_risk") for i in range(20)]
    one_share_rows = [_row(1000 + i, "pyramid_would_have_helped") for i in range(14)]
    one_share_rows.extend(_row(2000 + i, "pyramid_correctly_blocked") for i in range(6))
    for index, row in enumerate(one_share_rows):
        row["stock_code"] = f"{index:06d}"
        row["one_share_event"] = True
        row["pyramid_opportunity_cost_pct"] = 0.5 + index / 10
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        legacy_rows,
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["sample_count"] == 20
    assert (
        candidate["source_metrics"]["calibration_source_scope"]
        == "one_share_event_opportunity"
    )
    assert candidate["source_metrics"]["one_share_event_source_present"] is True
    assert candidate["source_metrics"]["one_share_closed_pyramid_row_count"] == 20
    assert (
        candidate["recommended_values"]["min_ai_score"]
        == candidate["current_values"]["min_ai_score"] - 5.0
    )


def test_pyramid_quality_calibration_excludes_invalid_probe_attribution_rows(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    for row in one_share_rows:
        row.update(
            {
                "probe_residual_observation_seen": True,
                "residual_fill_attribution_valid": True,
                "venue_source_quality_valid": True,
            }
        )
    one_share_rows[0]["residual_fill_attribution_valid"] = False
    one_share_rows[1]["venue_source_quality_valid"] = False
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["sample_count"] == 18
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["source_metrics"]["one_share_closed_pyramid_row_count"] == 18


def test_pyramid_quality_calibration_consumes_normal_winner_expansion_as_source_only(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    normal_rows = [
        {
            "record_id": str(index),
            "normal_winner_expansion_label": "realized_incremental_winner",
            "normal_winner_expansion_source_quality_valid": True,
            "normal_winner_expansion_incremental_final_profit_pct": 0.4,
            "normal_winner_expansion_candidate_notional_krw": 100_000,
            "effective_venue": "KRX",
            "venue_source_quality_valid": True,
            "market_session_bucket": "krx_regular",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
            ),
            "forbidden_uses": ["intraday_runtime_apply"],
        }
        for index in range(20)
    ]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        normal_winner_expansion_rows=normal_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    observation = report["normal_winner_expansion_observation"]

    assert observation["state"] == "positive_ev_profile_candidate"
    assert observation["sample_count"] == 20
    assert observation["ev_eligible_sample_count"] == 20
    assert observation["notional_weighted_ev_pct"] == 0.4
    assert observation["provenance_rejected_count"] == 0
    assert observation["by_effective_venue"][0]["effective_venue"] == "KRX"
    assert observation["by_effective_venue"][0]["ev_eligible_sample_count"] == 20
    assert observation["by_effective_venue"][0]["sample_floor_met"] is True
    assert observation["allowed_runtime_apply"] is False
    assert observation["runtime_effect"] is False
    assert (
        observation["decision_authority"]
        == "rolling_source_only_normal_winner_expansion_observation"
    )


def test_normal_winner_ev_floor_requires_positive_parseable_notional(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    normal_rows = [
        {
            "record_id": str(index),
            "normal_winner_expansion_label": "realized_incremental_winner",
            "normal_winner_expansion_source_quality_valid": True,
            "normal_winner_expansion_incremental_final_profit_pct": 0.4,
            "normal_winner_expansion_candidate_notional_krw": (
                "nan" if index == 0 else "malformed" if index == 1 else 100_000
            ),
            "effective_venue": "KRX",
            "venue_source_quality_valid": True,
            "market_session_bucket": "krx_regular",
            "normal_winner_expansion_blocker_reason": (
                mod.WINNER_RECOVERY_EXACT_BLOCKER if index < 10 else "other_blocker"
            ),
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
            ),
            "forbidden_uses": ["intraday_runtime_apply"],
        }
        for index in range(21)
    ]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        normal_winner_expansion_rows=normal_rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["normal_winner_expansion_observation"]
    exact = report["winner_recovery_bounded_canary_observation"]

    assert observation["sample_count"] == 21
    assert observation["ev_eligible_sample_count"] == 19
    assert observation["sample_floor_met"] is False
    assert observation["state"] == "hold_sample"
    assert exact["by_effective_venue"][0]["sample_count"] == 10
    assert exact["by_effective_venue"][0]["ev_eligible_sample_count"] == 8
    assert exact["by_effective_venue"][0]["sample_floor_met"] is False


def test_pyramid_quality_calibration_rejects_normal_winner_authority_leak(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    leaked_row = {
        "record_id": "leaked",
        "normal_winner_expansion_label": "realized_incremental_winner",
        "normal_winner_expansion_source_quality_valid": True,
        "normal_winner_expansion_incremental_final_profit_pct": 1.0,
        "normal_winner_expansion_candidate_notional_krw": 100_000,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "decision_authority": "live_runtime",
        "forbidden_uses": [],
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        normal_winner_expansion_rows=[leaked_row],
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    observation = report["normal_winner_expansion_observation"]

    assert observation["state"] == "hold_sample"
    assert observation["sample_count"] == 0
    assert observation["provenance_rejected_count"] == 1
    assert observation["allowed_runtime_apply"] is False


def test_winner_recovery_counterfactual_isolates_exact_blocker_by_venue(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    normal_rows = []
    for index in range(10):
        normal_rows.append(
            {
                "record_id": str(index),
                "normal_winner_expansion_label": "realized_incremental_winner",
                "normal_winner_expansion_source_quality_valid": True,
                "normal_winner_expansion_incremental_final_profit_pct": 0.5,
                "normal_winner_expansion_candidate_notional_krw": 100_000,
                "normal_winner_expansion_blocker_reason": (
                    mod.WINNER_RECOVERY_EXACT_BLOCKER
                ),
                "effective_venue": "KRX",
                "venue_source_quality_valid": True,
                "market_session_bucket": "krx_regular",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": (
                    "source_only_one_share_pyramid_opportunity_backtest_"
                    "no_runtime_mutation"
                ),
                "forbidden_uses": ["intraday_runtime_apply"],
            }
        )
    normal_rows.append(
        {
            **normal_rows[0],
            "record_id": "mixed-negative",
            "normal_winner_expansion_blocker_reason": (
                "rising_missed_scout_pyramid_bridge_blocked:"
                "buy_pressure_severe_below_min"
            ),
            "normal_winner_expansion_label": (
                "correctly_not_expanded_or_reversal"
            ),
            "normal_winner_expansion_incremental_final_profit_pct": -5.0,
        }
    )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        normal_winner_expansion_rows=normal_rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_bounded_canary_observation"]

    assert observation["state"] == "bounded_one_share_canary_evidence_ready"
    assert observation["sample_count"] == 10
    assert observation["ready_venue_count"] == 1
    assert observation["operator_action_required"] is False
    assert observation["next_preopen_auto_apply_candidate"] is True
    assert observation["auto_apply_mode"] == "next_preopen_auto_bounded_live"
    assert observation["allowed_runtime_apply"] is False
    assert observation["initial_real_qty_cap"] == 1
    assert observation["by_effective_venue"] == [
        {
            "effective_venue": "KRX",
            "state": "bounded_one_share_canary_evidence_ready",
            "sample_count": 10,
            "ev_eligible_sample_count": 10,
            "sample_floor": 10,
            "sample_floor_met": True,
            "realized_incremental_winner_count": 10,
            "notional_weighted_ev_pct": 0.5,
            "initial_real_qty_cap": 1,
            "runtime_env_key": (
                "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_KRX_ENABLED"
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    ]
    assert len(report["normal_winner_expansion_observation"]["by_blocker_reason"]) == 2


def test_winner_recovery_candidate_is_blocked_by_unisolatable_report_quality(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    row = {
        "normal_winner_expansion_label": "realized_incremental_winner",
        "normal_winner_expansion_source_quality_valid": True,
        "normal_winner_expansion_incremental_final_profit_pct": 0.5,
        "normal_winner_expansion_candidate_notional_krw": 100_000,
        "normal_winner_expansion_blocker_reason": mod.WINNER_RECOVERY_EXACT_BLOCKER,
        "effective_venue": "KRX",
        "venue_source_quality_valid": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_valid",
        "forbidden_uses": ["runtime_apply"],
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        source_quality="unisolatable_contract_failure",
        normal_winner_expansion_rows=[{**row, "record_id": str(i)} for i in range(10)],
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_bounded_canary_observation"]

    assert observation["state"] == "source_quality_blocked"
    assert observation["evidence_state_before_source_quality_gate"] == (
        "bounded_one_share_canary_evidence_ready"
    )
    assert observation["operator_action_required"] is False
    assert observation["allowed_runtime_apply"] is False


def test_winner_recovery_real_execution_requires_positive_fee_aware_ev_and_floor(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [
        {
            "record_id": str(index),
            "scale_in_outcome_cohort": "winner_recovery",
            "closed": True,
            "fill_qty": 1,
            "fill_notional_krw": 100_000,
            "scale_in_leg_net_pnl_proxy_krw": 400,
            "source_quality_valid": True,
            "entry_effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": (
                "real_scale_in_execution_outcome_observation_only"
            ),
            "forbidden_uses": ["runtime_threshold_apply"],
        }
        for index in range(20)
    ]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        real_scale_in_performance_rows=rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_real_execution_observation"]

    assert observation["state"] == "first_planned_residual_leg_candidate_ready"
    assert observation["source_quality_valid_closed_count"] == 20
    assert observation["source_quality_adjusted_ev_pct"] == 0.4
    assert observation["scale_in_leg_net_pnl_proxy_krw_sum"] == 8000
    assert observation["diagnostic_win_rate"] == 1.0
    assert observation["recommended_next_qty_stage"] == (
        "first_planned_residual_leg_from_current_position_sizing_owner"
    )
    assert observation["operator_action_required"] is True
    assert observation["allowed_runtime_apply"] is False


def test_winner_recovery_real_execution_holds_below_floor_and_rejects_bad_source(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    valid = {
        "scale_in_outcome_cohort": "winner_recovery",
        "closed": True,
        "fill_qty": 1,
        "fill_notional_krw": 100_000,
        "scale_in_leg_net_pnl_proxy_krw": 300,
        "source_quality_valid": True,
        "entry_effective_venue": "NXT",
        "market_session_bucket": "nxt_regular",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "real_scale_in_execution_outcome_observation_only",
        "forbidden_uses": ["runtime_threshold_apply"],
    }
    rows = [{**valid, "record_id": str(index)} for index in range(19)]
    rows.append({**valid, "record_id": "bad-source", "source_quality_valid": False})
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-08-20.json",
        [],
        real_scale_in_performance_rows=rows,
    )

    report = mod.build_report("2026-08-20", input_paths=[path], generated_at="fixed")
    observation = report["winner_recovery_real_execution_observation"]

    assert observation["state"] == "observe_one_share_canary"
    assert observation["execution_count"] == 20
    assert observation["closed_count"] == 20
    assert observation["source_quality_valid_closed_count"] == 19
    assert observation["source_quality_rejected_count"] == 1
    assert observation["operator_action_required"] is False
    assert observation["allowed_runtime_apply"] is False


def test_pyramid_quality_calibration_consumes_post_probe_real_outcomes_source_only(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    post_probe_rows = []
    for index in range(20):
        winner = index < 12
        profit_pct = 0.4 if winner else -0.2
        post_probe_rows.append(
            {
                **_row(
                    index,
                    "pyramid_correctly_blocked",
                    final_profit_rate=profit_pct,
                ),
                "post_probe_real_outcome_label": (
                    "profitable_zero_fill_confirmation_ready"
                    if winner
                    else "loss_or_flat_zero_fill_confirmation_ready"
                ),
                "post_probe_real_outcome_source_quality_valid": True,
                "post_probe_real_outcome_profit_pct": profit_pct,
                "post_probe_real_confirmation_ready": True,
                "post_probe_counterfactual_source_quality_valid": True,
                "post_probe_probe_actual_order_submitted": True,
                "post_probe_residual_actual_order_submitted": False,
                "post_probe_counterfactual_first_leg_notional_krw": 100_000,
                "post_probe_reprice_observed": True,
                "post_probe_reprice_outcome_source_quality_valid": True,
                "post_probe_reprice_profiles": ["normal"],
                "post_probe_reprice_avg_passive_improvement_bps": 30.0,
                "effective_venue": "NXT",
                "venue_source_quality_valid": True,
                "market_session_bucket": "nxt",
                "allowed_runtime_apply": False,
                "decision_authority": (
                    "source_only_one_share_pyramid_opportunity_backtest_"
                    "no_runtime_mutation"
                ),
            }
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-29.json",
        [],
        one_share_rows=post_probe_rows,
        post_probe_real_outcome_contract=True,
    )

    report = mod.build_report("2026-07-29", input_paths=[path], generated_at="fixed")
    observation = report["post_probe_real_outcome_observation"]

    assert observation["state"] == "positive_ev_profile_candidate"
    assert observation["closed_real_outcome_count"] == 20
    assert observation["confirmation_ready_count"] == 20
    assert observation["confirmation_ready_winner_count"] == 12
    assert observation["confirmation_ready_loss_or_flat_count"] == 8
    assert observation["diagnostic_win_rate"] == 0.6
    assert observation["notional_weighted_ev_pct"] == 0.16
    assert observation["sample_floor_met"] is True
    assert observation["cumulative_judgment_quality"] == {
        "learning_sample_floor": 1,
        "learning_sample_count": 20,
        "learning_updated": True,
        "learning_update_policy": (
            "one_mature_post_probe_outcome_updates_cumulative_judgment_quality"
        ),
        "notional_weighted_ev_pct": 0.16,
        "runtime_promotion_sample_floor": 20,
        "learning_floor_grants_runtime_promotion": False,
    }
    assert observation["by_effective_venue"][0]["effective_venue"] == "NXT"
    reprice = report["post_probe_reprice_observation"]
    assert reprice["learning_updated"] is True
    assert reprice["learning_sample_count"] == 20
    assert reprice["equal_weight_avg_profit_pct"] == 0.16
    assert reprice["profile_quality"][0] == {
        "reprice_profile": "normal",
        "sample_count": 20,
        "equal_weight_avg_profit_pct": 0.16,
        "avg_passive_improvement_bps": 30.0,
    }
    assert reprice["metric_role"] == "execution_quality_real_only"
    assert reprice["window_policy"] == (
        "clean_baseline_cumulative_closed_real_post_probe_reprice_outcomes"
    )
    assert reprice["sample_floor"] == {
        "cumulative_learning": 1,
        "runtime_promotion_real": 20,
    }
    assert reprice["primary_decision_metric"] == "equal_weight_avg_profit_pct"
    assert "complete_post_probe_resolver" in reprice["source_quality_gate"]
    assert observation["runtime_effect"] is False
    assert observation["allowed_runtime_apply"] is False
    assert (
        observation["decision_authority"]
        == "rolling_source_only_post_probe_real_outcome_no_runtime_mutation"
    )
    output_json = tmp_path / "post_probe_calibration.json"
    output_md = tmp_path / "post_probe_calibration.md"
    mod.write_outputs(report, output_json=output_json, output_md=output_md)
    markdown = output_md.read_text(encoding="utf-8")
    assert "- post_probe_confirmation_ready_winner_count: 12" in markdown
    assert (
        "- post_probe_confirmation_ready_notional_weighted_ev_pct: 0.1600" in markdown
    )


def test_runtime_confirmation_quality_dispute_is_observed_but_excluded_from_ev(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    disputed = {
        **_row(1, "pyramid_correctly_blocked", final_profit_rate=0.38),
        "post_probe_real_outcome_label": "profitable_zero_fill_no_confirmation",
        "post_probe_real_outcome_source_quality_valid": True,
        "post_probe_real_outcome_profit_pct": 0.38,
        "post_probe_real_confirmation_ready": False,
        "post_probe_runtime_confirmation_ready": True,
        "post_probe_confirmation_contract_alignment": (
            "runtime_confirmed_source_quality_disputed"
        ),
        "post_probe_counterfactual_source_quality_valid": True,
        "post_probe_probe_actual_order_submitted": True,
        "post_probe_residual_actual_order_submitted": False,
        "post_probe_counterfactual_first_leg_notional_krw": 146_600,
        "effective_venue": "KRX",
        "venue_source_quality_valid": True,
        "market_session_bucket": "krx_regular",
        "allowed_runtime_apply": False,
        "decision_authority": (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        ),
    }
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-31.json",
        [],
        one_share_rows=[disputed],
        post_probe_real_outcome_contract=True,
    )

    report = mod.build_report("2026-07-31", input_paths=[path], generated_at="fixed")
    observation = report["post_probe_real_outcome_observation"]

    assert observation["closed_real_outcome_count"] == 1
    assert observation["confirmation_ready_count"] == 0
    assert observation["runtime_confirmation_source_quality_disputed_count"] == 1
    assert observation["cumulative_judgment_quality"]["learning_sample_count"] == 0
    assert observation["notional_weighted_ev_pct"] == 0.0


def test_pyramid_quality_calibration_profit_grid_sets_one_step_min_profit(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    one_share_rows = [
        _row(i, "pyramid_would_have_helped", max_profit_seen=1.4, final_profit_rate=2.0)
        for i in range(24)
    ]
    one_share_rows.extend(
        _row(
            100 + i,
            "pyramid_overheat_or_reversal_risk",
            max_profit_seen=2.0,
            final_profit_rate=0.2,
        )
        for i in range(6)
    )
    for row in one_share_rows:
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        [],
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]
    grid_decision = candidate["source_metrics"]["profit_threshold_grid_decision"]

    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["calibration_reason"] == "grid_loosen_profit_threshold_direct"
    assert (
        candidate["recommended_values"]["min_profit_pct"]
        == grid_decision["selected_min_profit_pct"]
    )
    assert (
        grid_decision["selected_min_profit_pct"]
        < candidate["current_values"]["min_profit_pct"]
    )
    assert grid_decision["selected_row"]["eligible_count"] >= 20


def test_pyramid_quality_calibration_does_not_fallback_when_one_share_floor_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    legacy_rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
    one_share_rows = [_row(3000 + i, "pyramid_would_have_helped") for i in range(5)]
    for row in one_share_rows:
        row["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
    path = _feedback(
        mod.INPUT_REPORT_DIR / "scalping_pyramid_intraday_feedback_2026-07-03.json",
        legacy_rows,
        one_share_rows=one_share_rows,
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["sample_count"] == 5
    assert (
        "rolling_closed_one_share_pyramid_rows_lt_20" in candidate["calibration_reason"]
    )
