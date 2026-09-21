import json
from pathlib import Path

import pytest

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
    assert support["holdout"]["paired_delta_daily_net_profit_krw"] is None
    assert support["holdout"]["paired_delta_daily_return_sum_pct"] < 0
    assert support["holdout"]["daily_net_profit_authority"] == (
        "unavailable_quantity_and_capital_constraints_missing"
    )
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
    assert report["decision"] == "hold_structural_gap"
    assert report["economic_evaluation"]["first_blocker"] == "source:malformed_json"
    assert report["source_quality"]["tuning_input_allowed"] is False
    assert report["source_receipts"][0]["state"] == "malformed_json"


def test_positive_ev_without_quantity_or_capital_does_not_publish_policy(
    monkeypatch, tmp_path
):
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
    assert report["status"] == "structurally_blocked"
    assert report["decision"] == "hold_structural_gap"
    assert report["economic_evaluation"]["first_blocker"] == (
        "counterfactual_quantity_or_capital_constraints_missing"
    )
    assert report["economic_evaluation"]["candidates"][0]["blocker"] == (
        "counterfactual_quantity_or_capital_constraints_missing"
    )
    assert policy["status"] == "incumbent_preserved"
    assert policy["runtime_env_overrides"] == {}
    assert len(policy["policy_sha256"]) == 64


def test_source_loader_rejects_schema_mismatch_and_future_explicit_source(tmp_path):
    schema_path = _feedback(
        tmp_path / "rising_missed_intraday_feedback_2026-09-16.json",
        "2026-09-16",
        [("adverse_stop_first", None)],
    )
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    payload["schema_version"] = 2
    schema_path.write_text(json.dumps(payload), encoding="utf-8")
    future_path = _feedback(
        tmp_path / "rising_missed_intraday_feedback_2026-09-17.json",
        "2026-09-17",
        [("adverse_stop_first", None)],
    )

    schema_report = mod.build_report(
        "2026-09-16", source_paths=[schema_path], generated_at="fixed"
    )
    future_report = mod.build_report(
        "2026-09-16", source_paths=[schema_path, future_path], generated_at="fixed"
    )

    assert schema_report["status"] == "structurally_blocked"
    assert schema_report["source_receipts"][0]["state"] == "schema_version_mismatch"
    assert future_report["status"] == "structurally_blocked"
    assert future_report["source_receipts"][1]["state"] == "blocked_future_source"


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


@pytest.mark.parametrize(
    ("publication", "effective"),
    [("2026-09-17", "2026-09-18"), ("2026-09-20", "2026-09-21")],
)
def test_publication_date_selects_consumer_policy(monkeypatch, tmp_path, publication, effective):
    from src.engine.automation import runtime_policy_bootstrap as bootstrap

    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(mod, "FEEDBACK_DIR", tmp_path / "feedback")
    monkeypatch.setattr(bootstrap, "RISING_MISSED_REPORT_DIR", tmp_path)
    report = mod.build_report(
        "2026-09-17", generated_at=f"{publication}T14:00:00+09:00"
    )
    report_path = tmp_path / "rising_missed_classifier_prior_2026-09-17.json"
    # A prior publication for the next apply date must be replaced together
    # with the refreshed source, rather than left bound to the old hash.
    _, policy_path = mod.policy_paths("2026-09-17", effective)
    policy_path.write_text('{"source_report_sha256": "old-generation"}')

    result = mod.write_outputs(
        report, output_json=report_path, output_md=tmp_path / "report.md"
    )

    accepted, rejected = bootstrap._load_direct_receipts(effective, [policy_path])
    assert rejected == []
    assert len(accepted) == 1
    assert accepted[0]["status"] == "incumbent_preserved"
    assert accepted[0]["runtime_env_overrides"] == {}
    assert result["policy"]["effective_date"] == effective
    assert result["policy"]["source_report_sha256"] == report["artifact_sha256"]
    assert json.loads(Path(result["source_policy"]).read_text()) == result["policy"]


def test_publication_rejects_changed_source_before_any_write(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(mod, "FEEDBACK_DIR", tmp_path / "feedback")
    report = mod.build_report(
        "2026-09-17", generated_at="2026-09-20T14:00:00+09:00"
    )
    report["decision"] = "changed_after_hash"
    report_path = tmp_path / "report.json"
    report_path.write_text("previous-generation")

    with pytest.raises(ValueError, match="source_report_sha256_mismatch"):
        mod.write_outputs(report, output_json=report_path, output_md=tmp_path / "report.md")

    assert report_path.read_text() == "previous-generation"
    assert not (tmp_path / "rising_missed_tp1_policy_2026-09-21.json").exists()


def test_overnight_recovery_preserves_requested_publication_date(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(mod, "FEEDBACK_DIR", tmp_path / "feedback")
    monkeypatch.setenv("POSTCLOSE_POLICY_PUBLICATION_DATE", "2026-09-21")
    report = mod.build_report("2026-09-21", generated_at="2026-09-22T00:30:00+09:00")
    result = mod.write_outputs(report, output_json=tmp_path / "report.json", output_md=tmp_path / "report.md")
    assert result["policy"]["publication_date"] == "2026-09-21"
    assert result["policy"]["effective_date"] == "2026-09-22"
    monkeypatch.setenv("POSTCLOSE_POLICY_PUBLICATION_DATE", "2026-09-23")
    with pytest.raises(ValueError, match="publication_date_invalid"):
        mod.write_outputs(report, output_json=tmp_path / "report.json", output_md=tmp_path / "report.md")
