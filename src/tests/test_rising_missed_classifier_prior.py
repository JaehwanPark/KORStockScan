import json
from pathlib import Path

from src.engine.monitoring import rising_missed_classifier_prior as mod


def _feedback(path: Path, day: str, outcomes: list[tuple[str, float | None]]) -> Path:
    submit = []
    labels = []
    for index, (label, terminal) in enumerate(outcomes):
        evaluation_id = f"{day}-{index}"
        submit.append(
            {
                "evaluation_id": evaluation_id,
                "positive_support_count": 1,
                "positive_support_families": "depth",
            }
        )
        horizon = {
            "horizon_min": 20,
            "outcome_label": label,
            "source_quality_state": "pass",
            "terminal_executable_move_pct": terminal,
        }
        labels.append(
            {
                "evaluation_id": evaluation_id,
                "candidate_ts": f"{day}T10:00:00+09:00",
                "stock_code": f"{index:06d}",
                "entry_executable_bbo_state": "pass",
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
                "gross_first_hit_label": label,
                "gross_target_pct": 1.3,
                "adverse_stop_pct": -0.7,
                "post_block_horizon_measurements": [horizon],
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            }
        )
    payload = {
        "schema_version": 1,
        "report_type": "rising_missed_intraday_feedback",
        "target_date": day,
        "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "rising_missed_tp1_counterfactual_submit_safety_rows": submit,
        "rising_missed_tp1_counterfactual_first_hit_label_rows": labels,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _cost(_stamp):
    return {"round_trip_cost_pct": 0.2, "policy_id": "test-cost"}


def test_direct_paired_evaluator_measures_negative_support_relaxation(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "comparison_cost_contract", _cost)
    paths = []
    for day in ("2026-09-10", "2026-09-11", "2026-09-14", "2026-09-15", "2026-09-16"):
        paths.append(_feedback(tmp_path / f"rising_missed_intraday_feedback_{day}.json", day, [("adverse_stop_first", None)] * 12))

    report = mod.build_report("2026-09-16", source_paths=paths, generated_at="2026-09-16T21:00:00+09:00")

    support = report["economic_evaluation"]["candidates"][0]
    assert report["status"] == "measured_no_edge"
    assert support["decision_change_count"] == 60
    assert support["calibration_sample_floor_met"] is True
    assert support["holdout_sample_floor_met"] is True
    assert support["calibration"]["paired_delta_ev_pct"] == -0.9
    assert support["holdout"]["paired_delta_daily_net_profit_krw"] < 0
    assert support["disposition"] == "measured_no_edge"
    assert all(row["disposition"] == "identical_policy" for row in report["economic_evaluation"]["candidates"][1:])
    assert report["code_improvement_orders"] == []


def test_no_hit_requires_terminal_executable_exit(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "comparison_cost_contract", _cost)
    path = _feedback(
        tmp_path / "rising_missed_intraday_feedback_2026-09-16.json",
        "2026-09-16",
        [("no_hit_within_20m", 0.5), ("no_hit_within_20m", None)],
    )

    report = mod.build_report("2026-09-16", source_paths=[path], generated_at="fixed")

    states = [row["outcome_state"] for row in report["paired_rows"]]
    assert states == ["paired_cost_adjusted", "censored_no_hit_terminal_exit_missing"]
    assert report["paired_rows"][0]["net_return_pct"] == 0.3
    assert report["paired_rows"][1]["net_return_pct"] is None


def test_source_loader_fails_closed_on_malformed_input(tmp_path):
    path = tmp_path / "rising_missed_intraday_feedback_2026-09-16.json"
    path.write_text("{", encoding="utf-8")

    report = mod.build_report("2026-09-16", source_paths=[path], generated_at="fixed")

    assert report["status"] == "structurally_blocked"
    assert report["source_quality"]["tuning_input_allowed"] is False
    assert report["source_receipts"][0]["state"] == "malformed_json"


def test_validated_edge_publishes_bounded_dated_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "comparison_cost_contract", _cost)
    paths = []
    for day in ("2026-09-10", "2026-09-11", "2026-09-14", "2026-09-15", "2026-09-16"):
        paths.append(_feedback(tmp_path / f"rising_missed_intraday_feedback_{day}.json", day, [("gross_target_first", None)] * 12))
    report = mod.build_report("2026-09-16", source_paths=paths, generated_at="2026-09-16T21:00:00+09:00")
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "out")

    result = mod.write_outputs(
        report,
        output_json=tmp_path / "report.json",
        output_md=tmp_path / "report.md",
        effective_date="2026-09-17",
    )

    policy = result["policy"]
    assert report["status"] == "validated_edge"
    assert policy["status"] == "validated_edge"
    assert policy["runtime_env_overrides"]["KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN"] == "1"
    assert policy["runtime_env_overrides"]["KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE"] == "2026-09-17"
    assert len(policy["policy_sha256"]) == 64


def test_no_edge_policy_receipt_preserves_incumbent_without_env_mutation(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "comparison_cost_contract", _cost)
    path = _feedback(tmp_path / "rising_missed_intraday_feedback_2026-09-16.json", "2026-09-16", [("adverse_stop_first", None)] * 2)
    report = mod.build_report("2026-09-16", source_paths=[path], generated_at="2026-09-16T21:00:00+09:00")
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "out")

    result = mod.write_outputs(report, output_json=tmp_path / "report.json", output_md=tmp_path / "report.md", effective_date="2026-09-17")

    assert result["policy"]["status"] == "incumbent_preserved"
    assert result["policy"]["runtime_env_overrides"] == {}
    assert result["policy"]["runtime_effect"] is False
    assert result["policy"]["economic_disposition"] == "insufficient_mature_sample"
    assert result["policy"]["evaluated_axis"] == "positive_support_min"
    assert result["policy"]["calibration"]["paired_sample_count"] == 0
    assert Path(result["effective_policy"]).exists()
