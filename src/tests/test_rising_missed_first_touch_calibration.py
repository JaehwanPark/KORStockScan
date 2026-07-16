import json

from src.engine.monitoring import rising_missed_first_touch_calibration as mod


def _row(record_id, label, *, submitted=False, forbidden=True):
    return {
        "record_id": str(record_id),
        "first_touch_regression_label": label,
        "first_touch_avg_down_submitted": submitted,
        "actual_order_submitted": False,
        "broker_order_forbidden": forbidden,
        "runtime_effect": False,
        "decision_authority": "source_only_first_touch_regression_table",
        "forbidden_uses": ["intraday_threshold_mutation"],
    }


def _feedback(path, rows, *, source_quality="pass"):
    payload = {
        "report_type": "rising_missed_intraday_feedback",
        "target_date": path.stem.rsplit("_", 1)[-1],
        "source_quality": {"status": source_quality},
        "first_touch_regression_rows": rows,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_first_touch_calibration_holds_when_sample_floor_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    path = _feedback(
        mod.INPUT_REPORT_DIR / "rising_missed_intraday_feedback_2026-07-03.json",
        [_row(i, "first_touch_loss_or_flat") for i in range(3)],
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidate"]

    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
    assert "rolling_closed_first_touch_rows_lt_10" in candidate["calibration_reason"]


def test_first_touch_calibration_loss_cluster_creates_tighten_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "first_touch_loss_or_flat") for i in range(7)]
    rows += [_row(100 + i, "first_touch_recovered_profit") for i in range(3)]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "rising_missed_intraday_feedback_2026-07-03.json", rows
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidate"]

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["recommended_values"]["min_ai_moderate"] == (
        candidate["current_values"]["min_ai_moderate"] + 5.0
    )
    assert candidate["recommended_values"]["max_spread_bps"] == (
        candidate["current_values"]["max_spread_bps"] - 10.0
    )
    assert "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE" in candidate["target_env_keys"]


def test_first_touch_calibration_recovery_cluster_creates_loosen_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "first_touch_recovered_profit") for i in range(7)]
    rows += [_row(100 + i, "first_touch_loss_or_flat") for i in range(3)]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "rising_missed_intraday_feedback_2026-07-03.json", rows
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidate"]

    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["recommended_values"]["min_ai_moderate"] == (
        candidate["current_values"]["min_ai_moderate"] - 5.0
    )
    assert candidate["recommended_values"]["max_repeated_blockers_without_support"] == (
        candidate["current_values"]["max_repeated_blockers_without_support"] + 1
    )


def test_first_touch_calibration_forbidden_uses_and_provenance_contract(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "first_touch_loss_or_flat") for i in range(10)]
    del rows[0]["runtime_effect"]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "rising_missed_intraday_feedback_2026-07-03.json", rows
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidate"]

    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert "order_provenance_missing" in candidate["calibration_reason"]
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["source_quality_status"] == "blocked"
    assert "order_provenance_missing" in candidate["source_quality_blocked"]
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True
    assert "intraday_threshold_mutation" in candidate["forbidden_uses"]


def test_first_touch_calibration_blocks_feedback_source_quality_gap(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "INPUT_REPORT_DIR", tmp_path / "input")
    mod.INPUT_REPORT_DIR.mkdir(parents=True)
    rows = [_row(i, "first_touch_recovered_profit") for i in range(10)]
    path = _feedback(
        mod.INPUT_REPORT_DIR / "rising_missed_intraday_feedback_2026-07-03.json",
        rows,
        source_quality="first_touch_micro_provenance_unusable",
    )

    report = mod.build_report("2026-07-03", input_paths=[path], generated_at="fixed")
    candidate = report["calibration_candidate"]

    assert report["source_quality"]["status"] == "blocked"
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert "source_quality_not_pass" in candidate["calibration_reason"]
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["source_quality_status"] == "blocked"
    assert "source_quality_not_pass" in candidate["source_quality_blocked"]
