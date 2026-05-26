import json
from pathlib import Path

from src.engine import pattern_lab_currentness_audit as mod


def _metric_contract() -> dict:
    return {
        "metric_role": "primary_ev",
        "decision_authority": "source_quality_only",
        "window_policy": "rolling_10d",
        "sample_floor": 5,
        "primary_decision_metric": "equal_weight_avg_profit_pct",
        "source_quality_gate": "completed_only",
        "forbidden_uses": ["threshold mutation"],
        "runtime_effect": False,
    }


def _observability_payload(*, source_contract_status: str = "pass", orders: list[dict] | None = None) -> dict:
    return {
        "schema_version": 3,
        "metric_contract": _metric_contract(),
        "source_quality": {"status": source_contract_status, "findings": []},
        "source_contract_status": source_contract_status,
        "source_contract_findings": [],
        "code_improvement_orders": orders or [],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_labs(project_root: Path, target_date: str) -> None:
    report_dir = project_root / "data" / "report"
    for report_name, stem in (
        ("threshold_cycle_ev", "threshold_cycle_ev"),
        ("lifecycle_decision_matrix", "lifecycle_decision_matrix"),
        ("lifecycle_bucket_discovery", "lifecycle_bucket_discovery"),
        ("runtime_approval_summary", "runtime_approval_summary"),
        ("swing_lifecycle_decision_matrix", "swing_lifecycle_decision_matrix"),
        ("swing_lifecycle_bucket_discovery", "swing_lifecycle_bucket_discovery"),
        ("swing_strategy_discovery_ev", "swing_strategy_discovery_ev"),
    ):
        _write_json(report_dir / report_name / f"{stem}_{target_date}.json", {"runtime_effect": False})
    for lab in ("gemini_scalping_pattern_lab", "claude_scalping_pattern_lab"):
        lab_dir = project_root / "analysis" / lab
        outputs = lab_dir / "outputs"
        outputs.mkdir(parents=True, exist_ok=True)
        _write_json(outputs / "ev_analysis_result.json", {"schema_version": 2, "metric_contract": _metric_contract()})
        _write_json(outputs / "tuning_observability_summary.json", _observability_payload())
        _write_json(outputs / "run_manifest.json", {"run_at": target_date, "history_coverage_end": target_date})
        (lab_dir / "README.md").write_text(
            "report_only_observation\nthreshold_cycle_ev\nlifecycle_decision_matrix\n"
            "lifecycle_bucket_discovery\nruntime_approval_summary\n",
            encoding="utf-8",
        )
        (lab_dir / "config.py").write_text('INCLUDE_REMOTE = os.getenv("PATTERN_LAB_INCLUDE_REMOTE", "false")\n', encoding="utf-8")
        (lab_dir / "prepare_dataset.py").write_text(
            "TRADE_FACT_COLUMNS = []\npd.DataFrame(columns=TRADE_FACT_COLUMNS).to_csv(path)\n",
            encoding="utf-8",
        )

    deep_dir = project_root / "analysis" / "deepseek_swing_pattern_lab"
    outputs = deep_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    _write_json(outputs / "swing_pattern_analysis_result.json", {"schema_version": 2, "metric_contract": _metric_contract()})
    _write_json(
        outputs / "data_quality_report.json",
        {"schema_version": 2, "sim_probe_provenance": {"trade_fact_actual_order_submitted_false": 1}},
    )
    _write_json(outputs / "run_manifest.json", {"analysis_window": {"start": target_date, "end": target_date}})
    (deep_dir / "README.md").write_text(
        "report_only_observation\nthreshold_cycle_ev\nswing_lifecycle_decision_matrix\n"
        "swing_lifecycle_bucket_discovery\nswing_strategy_discovery_ev\n",
        encoding="utf-8",
    )

    engine_dir = project_root / "src" / "engine"
    engine_dir.mkdir(parents=True, exist_ok=True)
    (engine_dir / "pattern_lab_ai_review.py").write_text(
        "FORBIDDEN_USES = []\n"
        "runtime_effect = False\n"
        "allowed_runtime_apply = False\n"
        "auditor_pass = True\n"
        "explicit_gap_type = None\n"
        "source_paths = []\n"
        "ai_two_pass_review = {'interpretation': {}, 'audit': {}, 'final_conclusions': []}\n",
        encoding="utf-8",
    )


def test_currentness_audit_passes_when_contracts_and_guards_exist(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    target_date = "2026-05-15"
    _seed_labs(project_root, target_date)

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    report = mod.build_pattern_lab_currentness_audit(target_date)

    assert report["status"] == "pass"
    assert report["runtime_effect"] is False
    assert report["summary"]["missing_feedback_source_count"] == 0
    assert report["feedback_sources"]["scalping"]["consumed_feedback_sources"]
    assert report["code_improvement_orders"] == []
    assert (report_dir / "pattern_lab_currentness_audit" / f"pattern_lab_currentness_audit_{target_date}.json").exists()


def test_currentness_audit_emits_runtime_false_orders_for_gaps(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    target_date = "2026-05-15"
    _seed_labs(project_root, target_date)

    (project_root / "analysis" / "claude_scalping_pattern_lab" / "README.md").write_text(
        "legacy shadow-only wording\n",
        encoding="utf-8",
    )
    _write_json(
        project_root / "analysis" / "gemini_scalping_pattern_lab" / "outputs" / "ev_analysis_result.json",
        {"schema_version": 1},
    )
    _write_json(
        project_root / "analysis" / "deepseek_swing_pattern_lab" / "outputs" / "data_quality_report.json",
        {"schema_version": 2},
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    report = mod.build_pattern_lab_currentness_audit(target_date)

    assert report["status"] == "warning"
    order_ids = {order["order_id"] for order in report["code_improvement_orders"]}
    assert "order_pattern_lab_currentness_audit_gemini_scalping_metric_contract" in order_ids
    assert "order_pattern_lab_currentness_audit_active_source_forbidden_terms" in order_ids
    assert "order_pattern_lab_currentness_audit_deepseek_sim_probe_provenance" in order_ids
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])
    assert all(order["allowed_runtime_apply"] is False for order in report["code_improvement_orders"])


def test_currentness_audit_surfaces_pattern_lab_feedback_and_ai_review_gaps(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    target_date = "2026-05-15"
    _seed_labs(project_root, target_date)

    (project_root / "analysis" / "gemini_scalping_pattern_lab" / "README.md").write_text(
        "report_only_observation\n",
        encoding="utf-8",
    )
    (project_root / "analysis" / "claude_scalping_pattern_lab" / "README.md").write_text(
        "report_only_observation\n",
        encoding="utf-8",
    )
    (project_root / "analysis" / "deepseek_swing_pattern_lab" / "README.md").write_text(
        "report_only_observation\n",
        encoding="utf-8",
    )
    (project_root / "src" / "engine" / "pattern_lab_ai_review.py").unlink()

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    report = mod.build_pattern_lab_currentness_audit(target_date)

    assert report["status"] == "warning"
    order_ids = {order["order_id"] for order in report["code_improvement_orders"]}
    assert "order_pattern_lab_currentness_audit_scalping_ldm_threshold_reentry_sources" in order_ids
    assert "order_pattern_lab_currentness_audit_swing_ldm_threshold_reentry_sources" in order_ids
    assert "order_pattern_lab_currentness_audit_pattern_lab_ai_review_contract" in order_ids
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])


def test_currentness_audit_surfaces_observability_source_contract_orders(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    target_date = "2026-05-15"
    _seed_labs(project_root, target_date)

    embedded_order = {
        "order_id": "order_tuning_observability_performance_tuning_missing_contract_gap",
        "title": "Tuning observability performance_tuning missing contract gap",
        "source_report_type": "producer_gap_discovery",
        "target_subsystem": "pattern_lab",
        "priority": 1,
        "route": "implement_now",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "strategy_effect": True,
        "data_quality_effect": False,
    }
    _write_json(
        project_root / "analysis" / "gemini_scalping_pattern_lab" / "outputs" / "tuning_observability_summary.json",
        _observability_payload(source_contract_status="fail", orders=[embedded_order]),
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    report = mod.build_pattern_lab_currentness_audit(target_date)

    order_ids = {order["order_id"] for order in report["code_improvement_orders"]}
    assert "order_pattern_lab_currentness_audit_gemini_scalping_observability_source_contract" in order_ids
    assert "order_tuning_observability_performance_tuning_missing_contract_gap" in order_ids
    embedded = next(
        order
        for order in report["code_improvement_orders"]
        if order["order_id"] == "order_tuning_observability_performance_tuning_missing_contract_gap"
    )
    assert embedded["source_report_type"] == "tuning_observability_summary"
    assert embedded["route"] == "source_contract_gap"
    assert embedded["runtime_effect"] is False
    assert embedded["allowed_runtime_apply"] is False
    assert embedded["strategy_effect"] is False
    assert embedded["data_quality_effect"] is True
