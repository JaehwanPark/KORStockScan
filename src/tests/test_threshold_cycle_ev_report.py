import json

import pytest

from src.engine import threshold_cycle_ev_report as mod


@pytest.fixture(autouse=True)
def _isolate_pattern_lab_audit_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing_currentness_audit")
    monkeypatch.setattr(mod, "PATTERN_LAB_PROPAGATION_AUDIT_DIR", tmp_path / "missing_propagation_audit")


def test_build_threshold_cycle_ev_report_uses_existing_reports(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    automation_dir = report_dir / "scalping_pattern_lab_automation"
    workorder_report_dir = report_dir / "code_improvement_workorder"
    workorder_doc_dir = tmp_path / "docs" / "code-improvement-workorders"
    monitor_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    apply_dir.mkdir(parents=True)
    automation_dir.mkdir(parents=True)
    workorder_report_dir.mkdir(parents=True)
    workorder_doc_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.json",
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "code_improvement_workorder_paths",
        lambda target_date: (
            workorder_report_dir / f"code_improvement_workorder_{target_date}.json",
            workorder_doc_dir / f"code_improvement_workorder_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-08.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "completed_trades": 2,
                    "open_trades": 0,
                    "win_trades": 1,
                    "loss_trades": 1,
                    "avg_profit_rate": -0.39,
                    "realized_pnl_krw": -282,
                }
            }
        ),
        encoding="utf-8",
    )
    (monitor_dir / "performance_tuning_2026-05-08.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "budget_pass_events": 100,
                    "order_bundle_submitted_events": 5,
                    "latency_block_events": 95,
                    "latency_pass_events": 5,
                    "full_fill_events": 2,
                    "partial_fill_events": 0,
                    "full_fill_completed_avg_profit_rate": -0.395,
                    "holding_reviews": 17,
                    "exit_signals": 2,
                    "holding_review_ms_p95": 17022,
                }
            }
        ),
        encoding="utf-8",
    )
    (monitor_dir / "wait6579_ev_cohort_2026-05-08.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "total_candidates": 3,
                    "score65_74_probe_candidates": 2,
                    "avg_expected_ev_pct": 1.25,
                    "expected_ev_krw_sum": 12000,
                },
                "counterfactual_summary": {
                    "book": "scalp_score65_74_probe_counterfactual",
                    "role": "missed_buy_probe_counterfactual",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "counterfactual_report_only",
                    "calibration_authority": "missed_probe_ev_only_not_broker_execution",
                    "total_candidates": 3,
                    "score65_74_probe_candidates": 2,
                    "avg_expected_ev_pct": 1.25,
                    "score65_74_avg_expected_ev_pct": 2.5,
                    "expected_ev_krw_sum": 12000,
                    "real_execution_quality_source": "none",
                },
                "approval_gate": {
                    "min_sample_gate_passed": False,
                    "threshold_relaxation_approved": False,
                    "full_samples": 2,
                    "partial_samples": 0,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (calibration_dir / "threshold_cycle_calibration_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "run_phase": "postclose",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "calibration_state": "adjust_up",
                        "sample_count": 20,
                        "sample_floor": 20,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (apply_dir / "threshold_apply_2026-05-08.json").write_text(
        json.dumps(
            {
                "status": "auto_bounded_live_ready",
                "runtime_change": True,
                "auto_apply_selected": [{"family": "score65_74_recovery_probe"}],
                "operator_runtime_env_merge": {
                    "preserved_selected_families": [
                        "bad_entry_refined_canary",
                        "swing_one_share_real_canary_phase0",
                    ]
                },
                "swing_runtime_approval": {
                    "request_report": "data/report/swing_runtime_approval/swing_runtime_approval_2026-05-08.json",
                    "approval_artifact": None,
                    "requested": 1,
                    "approved": 0,
                    "real_canary_policy": {
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                        "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    },
                    "blocked": ["approval_artifact_missing"],
                    "requests": [
                        {
                            "approval_id": "swing_runtime_approval:2026-05-08:swing_model_floor",
                            "family": "swing_model_floor",
                            "stage": "selection",
                            "tradeoff_score": 0.72,
                            "target_env_keys": ["SWING_FLOOR_BULL"],
                            "recommended_values": {"floor_bull": 0.30},
                        }
                    ],
                    "selected": [],
                    "decisions": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "ev_report_summary": {
                    "gemini_fresh": True,
                    "claude_fresh": True,
                    "consensus_count": 1,
                    "auto_family_candidate_count": 0,
                    "code_improvement_order_count": 1,
                    "top_consensus_findings": [
                        {
                            "title": "AI threshold miss EV 회수 조건 점검",
                            "route": "existing_family",
                            "mapped_family": "score65_74_recovery_probe",
                        }
                    ],
                    "top_code_improvement_orders": [
                        {
                            "order_id": "order_ai_threshold",
                            "title": "AI threshold miss EV 회수 조건 점검",
                            "target_subsystem": "entry_funnel",
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workorder_report_dir / "code_improvement_workorder_2026-05-08.json").write_text(
        json.dumps(
            {
                "summary": {
                    "selected_order_count": 1,
                    "decision_counts": {"attach_existing_family": 1},
                },
                "orders": [
                    {
                        "order_id": "order_ai_threshold",
                        "decision": "attach_existing_family",
                        "target_subsystem": "entry_funnel",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workorder_doc_dir / "code_improvement_workorder_2026-05-08.md").write_text("# workorder\n", encoding="utf-8")

    report = mod.build_threshold_cycle_ev_report("2026-05-08")

    assert report["runtime_apply"]["selected_families"] == [
        "score65_74_recovery_probe",
        "bad_entry_refined_canary",
        "swing_one_share_real_canary_phase0",
    ]
    assert report["daily_ev_summary"]["completed_trades"] == 2
    assert report["daily_ev_summary"]["realized_pnl_krw"] == -282
    assert report["entry_funnel"]["budget_pass_to_submitted_rate_pct"] == 5.0
    assert report["missed_probe_counterfactual"]["book"] == "scalp_score65_74_probe_counterfactual"
    assert report["missed_probe_counterfactual"]["score65_74_probe_candidates"] == 2
    assert report["missed_probe_counterfactual"]["real_execution_quality_source"] == "none"
    assert report["pattern_lab_automation"]["consensus_count"] == 1
    assert report["swing_runtime_approval"]["requested"] == 1
    assert (
        report["swing_runtime_approval"]["real_canary_policy"]["policy_id"]
        == "swing_one_share_real_canary_phase0"
    )
    assert report["swing_runtime_approval"]["real_canary_policy"]["sim_only_actions"] == [
        "AVG_DOWN",
        "PYRAMID",
        "SCALE_IN",
    ]
    assert report["swing_runtime_approval"]["requests"][0]["tradeoff_score"] == 0.72
    assert report["pattern_lab_automation"]["top_consensus_findings"][0]["mapped_family"] == "score65_74_recovery_probe"
    assert report["code_improvement_workorder"]["selected_order_count"] == 1
    assert report["code_improvement_workorder"]["top_orders"][0]["order_id"] == "order_ai_threshold"
    assert (ev_dir / "threshold_cycle_ev_2026-05-08.json").exists()
    assert (ev_dir / "threshold_cycle_ev_2026-05-08.md").exists()
    markdown = (ev_dir / "threshold_cycle_ev_2026-05-08.md").read_text(encoding="utf-8")
    assert "Missed Probe Counterfactual" in markdown
    assert "Swing Runtime Approval" in markdown
    assert "swing_one_share_real_canary_phase0" in markdown
    assert "AVG_DOWN, PYRAMID, SCALE_IN" in markdown
    assert "swing_runtime_approval:2026-05-08:swing_model_floor" in markdown


def test_build_threshold_cycle_ev_report_warns_when_pattern_lab_artifact_missing(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    automation_dir = report_dir / "scalping_pattern_lab_automation"
    workorder_report_dir = report_dir / "code_improvement_workorder"
    workorder_doc_dir = tmp_path / "docs" / "code-improvement-workorders"
    monitor_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    apply_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.json",
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "code_improvement_workorder_paths",
        lambda target_date: (
            workorder_report_dir / f"code_improvement_workorder_{target_date}.json",
            workorder_doc_dir / f"code_improvement_workorder_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-08.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (monitor_dir / "performance_tuning_2026-05-08.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (calibration_dir / "threshold_cycle_calibration_2026-05-08_postclose.json").write_text(
        json.dumps({"run_phase": "postclose"}),
        encoding="utf-8",
    )
    (apply_dir / "threshold_apply_2026-05-08.json").write_text(json.dumps({"status": "manifest_ready"}), encoding="utf-8")

    report = mod.build_threshold_cycle_ev_report("2026-05-08")

    assert report["pattern_lab_automation"]["available"] is False
    assert "pattern_lab_automation_missing" in report["warnings"]
    assert "code_improvement_workorder_missing" in report["warnings"]
    assert "codebase_performance_workorder_missing" in report["warnings"]


def test_threshold_cycle_ev_report_exposes_codebase_performance_source_as_ops_summary(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    perf_dir = report_dir / "codebase_performance_workorder"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    workorder_report_dir = report_dir / "code_improvement_workorder"
    workorder_doc_dir = tmp_path / "docs" / "code-improvement-workorders"
    for path in (monitor_dir, calibration_dir, perf_dir, apply_dir, workorder_report_dir, workorder_doc_dir):
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            report_dir / "missing" / f"scalping_pattern_lab_automation_{target_date}.json",
            report_dir / "missing" / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "code_improvement_workorder_paths",
        lambda target_date: (
            workorder_report_dir / f"code_improvement_workorder_{target_date}.json",
            workorder_doc_dir / f"code_improvement_workorder_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-14.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (monitor_dir / "performance_tuning_2026-05-14.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (calibration_dir / "threshold_cycle_calibration_2026-05-14_postclose.json").write_text(
        json.dumps({"run_phase": "postclose"}),
        encoding="utf-8",
    )
    (apply_dir / "threshold_apply_2026-05-14.json").write_text(json.dumps({"status": "manifest_ready"}), encoding="utf-8")
    (workorder_report_dir / "code_improvement_workorder_2026-05-14.json").write_text(
        json.dumps({"summary": {}, "orders": []}),
        encoding="utf-8",
    )
    (workorder_doc_dir / "code_improvement_workorder_2026-05-14.md").write_text("# workorder\n", encoding="utf-8")
    (perf_dir / "codebase_performance_workorder_2026-05-14.json").write_text(
        json.dumps(
            {
                "source_doc_hash": "abc123",
                "summary": {"accepted_count": 7, "deferred_count": 3, "rejected_count": 2},
                "policy": {
                    "runtime_effect": False,
                    "strategy_effect": False,
                    "data_quality_effect": False,
                    "tuning_axis_effect": False,
                    "decision_authority": "ops_performance_workorder_source",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_ev_report("2026-05-14")

    summary = report["codebase_performance_workorder"]
    assert summary["available"] is True
    assert summary["accepted_count"] == 7
    assert summary["deferred_count"] == 3
    assert summary["rejected_count"] == 2
    assert summary["runtime_effect"] is False
    assert summary["strategy_effect"] is False
    assert summary["data_quality_effect"] is False
    assert summary["tuning_axis_effect"] is False
    assert report["sources"]["codebase_performance_workorder"] == str(
        perf_dir / "codebase_performance_workorder_2026-05-14.json"
    )
    markdown = (ev_dir / "threshold_cycle_ev_2026-05-14.md").read_text(encoding="utf-8")
    assert "Codebase Performance Workorder Source" in markdown
    assert "ops_performance_workorder_source" in markdown


def test_threshold_cycle_ev_report_prefers_candidate_sample_counts_from_calibration(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    workorder_report_dir = report_dir / "code_improvement_workorder"
    workorder_doc_dir = tmp_path / "docs" / "code-improvement-workorders"
    for path in (monitor_dir, calibration_dir, apply_dir, ev_dir, workorder_report_dir, workorder_doc_dir):
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            tmp_path / "missing" / f"scalping_pattern_lab_automation_{target_date}.json",
            tmp_path / "missing" / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "code_improvement_workorder_paths",
        lambda target_date: (
            workorder_report_dir / f"code_improvement_workorder_{target_date}.json",
            workorder_doc_dir / f"code_improvement_workorder_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-12.json").write_text(
        json.dumps({"metrics": {"completed_trades": 0, "open_trades": 0, "win_trades": 0, "loss_trades": 0}}),
        encoding="utf-8",
    )
    (monitor_dir / "performance_tuning_2026-05-12.json").write_text(
        json.dumps({"metrics": {"budget_pass_events": 0, "order_bundle_submitted_events": 0}}),
        encoding="utf-8",
    )
    (calibration_dir / "threshold_cycle_calibration_2026-05-12_postclose.json").write_text(
        json.dumps(
            {
                "run_phase": "postclose",
                "runtime_change": False,
                "calibration_candidates": [
                    {
                        "family": "holding_exit_decision_matrix_advisory",
                        "calibration_state": "hold_no_edge",
                        "sample_count": 14,
                        "source_sample_count": 14,
                        "sample_floor": 1,
                        "sample_floor_status": "minimum_edge_missing",
                        "source_metrics": {
                            "counterfactual_gap_count": 14,
                            "eligible_but_not_chosen_sample_snapshots": 0,
                        },
                    }
                ],
                "post_apply_attribution": {
                    "calibration_decisions": [
                        {
                            "family": "holding_exit_decision_matrix_advisory",
                            "calibration_state": "hold_no_edge",
                            "sample_count": 0,
                            "sample_floor": 1,
                        }
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (apply_dir / "threshold_apply_2026-05-12.json").write_text(
        json.dumps({"status": "auto_bounded_live_ready", "runtime_change": False}),
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_ev_report("2026-05-12")

    decision = next(
        item
        for item in report["calibration_outcome"]["decisions"]
        if item["family"] == "holding_exit_decision_matrix_advisory"
    )
    assert decision["sample_count"] == 14
    assert decision["source_sample_count"] == 14
    assert decision["sample_floor_status"] == "minimum_edge_missing"
    assert decision["source_metrics"]["counterfactual_gap_count"] == 14
    markdown = (ev_dir / "threshold_cycle_ev_2026-05-12.md").read_text(encoding="utf-8")
    assert "holding_exit_decision_matrix_advisory" in markdown
    assert "sample=`14/1`" in markdown


def test_build_threshold_cycle_ev_report_renders_swing_pattern_lab_section(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    automation_dir = report_dir / "scalping_pattern_lab_automation"
    swing_lab_automation_dir = report_dir / "swing_pattern_lab_automation"
    workorder_report_dir = report_dir / "code_improvement_workorder"
    workorder_doc_dir = tmp_path / "docs" / "code-improvement-workorders"
    for d in (monitor_dir, calibration_dir, apply_dir, automation_dir, swing_lab_automation_dir, workorder_report_dir, workorder_doc_dir):
        d.mkdir(parents=True)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.json",
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "swing_pattern_lab_automation_report_paths",
        lambda target_date: (
            swing_lab_automation_dir / f"swing_pattern_lab_automation_{target_date}.json",
            swing_lab_automation_dir / f"swing_pattern_lab_automation_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "code_improvement_workorder_paths",
        lambda target_date: (
            workorder_report_dir / f"code_improvement_workorder_{target_date}.json",
            workorder_doc_dir / f"code_improvement_workorder_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-08.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (monitor_dir / "performance_tuning_2026-05-08.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (calibration_dir / "threshold_cycle_calibration_2026-05-08_postclose.json").write_text(
        json.dumps({"run_phase": "postclose"}), encoding="utf-8"
    )
    (apply_dir / "threshold_apply_2026-05-08.json").write_text(json.dumps({"status": "manifest_ready"}), encoding="utf-8")
    (swing_lab_automation_dir / "swing_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "ev_report_summary": {
                    "deepseek_lab_available": True,
                    "findings_count": 2,
                    "code_improvement_order_count": 1,
                    "data_quality_warning_count": 0,
                    "carryover_warning_count": 1,
                    "population_split_available": True,
                    "source_quality_blocked_families": [
                        {
                            "family": "swing_scale_in_ofi_qi_confirmation",
                            "stage": "scale_in",
                            "source_quality_blockers": ["scale_in_ofi_qi_invalid_micro_context"],
                        }
                    ],
                },
                "consensus_findings": [
                    {"finding_id": "f1", "title": "selection gap", "route": "design_family_candidate"},
                    {"finding_id": "f2", "title": "entry block", "route": "attach_existing_family"},
                ],
                "code_improvement_orders": [
                    {"order_id": "order_f1", "title": "selection gap", "decision": "design_family_candidate"},
                ],
                "data_quality": {
                    "warnings": [],
                    "ofi_qi_quality": {"stale_missing_unique_record_count": 1},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workorder_report_dir / "code_improvement_workorder_2026-05-08.json").write_text(
        json.dumps({"summary": {}, "orders": []}), encoding="utf-8"
    )
    (workorder_doc_dir / "code_improvement_workorder_2026-05-08.md").write_text("# workorder\n", encoding="utf-8")

    report = mod.build_threshold_cycle_ev_report("2026-05-08")
    assert report["swing_pattern_lab_automation"]["available"] is True
    assert report["swing_pattern_lab_automation"]["findings_count"] == 2
    assert report["swing_pattern_lab_automation"]["carryover_warning_count"] == 1
    assert report["swing_pattern_lab_automation"]["source_quality_blocked_families"][0]["family"] == (
        "swing_scale_in_ofi_qi_confirmation"
    )

    markdown = (ev_dir / "threshold_cycle_ev_2026-05-08.md").read_text(encoding="utf-8")
    assert "Swing Pattern Lab Automation" in markdown
    assert "deepseek_lab_available" in markdown
    assert "source_quality_blocked_families" in markdown
    assert "carryover_warnings" in markdown
    assert "population_split_available" in markdown
