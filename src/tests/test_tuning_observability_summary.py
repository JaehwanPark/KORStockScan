import json

from analysis import tuning_observability_summary as mod


def test_observability_warns_when_all_snapshots_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SNAPSHOT_DIR", tmp_path)

    summary = mod.build_tuning_observability_summary(
        target_date="2026-05-26",
        analysis_start="2026-05-20",
        analysis_end="2026-05-26",
    )

    assert summary["schema_version"] == 3
    assert summary["source_quality"]["status"] == "fail"
    assert summary["source_contract_status"] == "fail"
    assert len(summary["source_quality"]["findings"]) == 4
    assert len(summary["source_contract_findings"]) == 4
    assert len(summary["code_improvement_orders"]) == 4
    assert summary["priority_findings"][0]["label"] == "Source quality warning"
    assert all(value is False for value in summary["source_presence"].values())
    assert all(order["runtime_effect"] is False for order in summary["code_improvement_orders"])
    assert all(order["allowed_runtime_apply"] is False for order in summary["code_improvement_orders"])


def test_observability_warns_for_non_dict_json_without_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SNAPSHOT_DIR", tmp_path)
    (tmp_path / "performance_tuning_2026-05-26.json").write_text(json.dumps([]), encoding="utf-8")

    summary = mod.build_tuning_observability_summary(
        target_date="2026-05-26",
        analysis_start="2026-05-20",
        analysis_end="2026-05-26",
    )

    assert "performance_tuning:invalid_json_type" in summary["source_quality"]["findings"]
    assert summary["source_contract_status"] == "fail"
    assert any(item["finding_type"] == "non_dict_json" for item in summary["source_contract_findings"])
    assert summary["source_presence"]["performance_tuning"] is False


def test_observability_safe_numeric_parsing(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SNAPSHOT_DIR", tmp_path)
    (tmp_path / "performance_tuning_2026-05-26.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "gatekeeper_decisions": "3.0",
                    "gatekeeper_eval_ms_p95": "-",
                    "budget_pass_events": None,
                    "order_bundle_submitted_events": "0",
                }
            }
        ),
        encoding="utf-8",
    )

    summary = mod.build_tuning_observability_summary(
        target_date="2026-05-26",
        analysis_start="2026-05-20",
        analysis_end="2026-05-26",
    )

    assert summary["entry_funnel"]["gatekeeper_decisions"] == 3
    assert summary["entry_funnel"]["gatekeeper_eval_ms_p95"] == 0.0
    assert summary["entry_funnel"]["budget_pass_events"] == 0


def test_observability_required_field_gap_generates_workorder(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SNAPSHOT_DIR", tmp_path)
    for source_id in ("performance_tuning", "trade_review", "post_sell_feedback"):
        (tmp_path / f"{source_id}_2026-05-26.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (tmp_path / "wait6579_ev_cohort_2026-05-26.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")

    summary = mod.build_tuning_observability_summary(
        target_date="2026-05-26",
        analysis_start="2026-05-20",
        analysis_end="2026-05-26",
    )

    assert summary["source_contract_status"] == "warning"
    assert any(
        item["source_id"] == "wait6579_ev_cohort"
        and item["finding_type"] == "required_field_missing"
        and item["field"] == "preflight"
        for item in summary["source_contract_findings"]
    )
    assert any(
        order["order_id"] == "order_tuning_observability_wait6579_ev_cohort_required_field_missing_contract_gap"
        for order in summary["code_improvement_orders"]
    )


def test_observability_contract_passes_with_required_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SNAPSHOT_DIR", tmp_path)
    (tmp_path / "performance_tuning_2026-05-26.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (tmp_path / "wait6579_ev_cohort_2026-05-26.json").write_text(
        json.dumps({"metrics": {}, "preflight": {}}),
        encoding="utf-8",
    )
    (tmp_path / "trade_review_2026-05-26.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (tmp_path / "post_sell_feedback_2026-05-26.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")

    summary = mod.build_tuning_observability_summary(
        target_date="2026-05-26",
        analysis_start="2026-05-20",
        analysis_end="2026-05-26",
    )

    assert summary["source_contract_status"] == "pass"
    assert summary["source_contract_findings"] == []
    assert summary["code_improvement_orders"] == []
