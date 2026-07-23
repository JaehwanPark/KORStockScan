import json

from src.engine.monitoring import scalping_pyramid_quality_calibration as mod


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
    assert "source_quality_not_pass" in candidate["calibration_reason"]
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["source_quality_status"] == "blocked"
    assert "source_quality_not_pass" in candidate["source_quality_blocked"]


def test_pyramid_quality_calibration_blocks_pressure_provenance_unusable_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
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
    assert "source_quality_not_pass" in candidate["calibration_reason"]


def test_pyramid_quality_calibration_blocks_micro_vwap_provenance_report(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "pyramid_would_have_helped") for i in range(20)]
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
    assert "source_quality_not_pass" in candidate["calibration_reason"]


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
    assert observation["notional_weighted_ev_pct"] == 0.4
    assert observation["provenance_rejected_count"] == 0
    assert observation["by_effective_venue"][0]["effective_venue"] == "KRX"
    assert observation["by_effective_venue"][0]["sample_floor_met"] is True
    assert observation["allowed_runtime_apply"] is False
    assert observation["runtime_effect"] is False
    assert (
        observation["decision_authority"]
        == "rolling_source_only_normal_winner_expansion_observation"
    )


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
