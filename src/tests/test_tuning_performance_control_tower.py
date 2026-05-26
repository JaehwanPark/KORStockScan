import json
from pathlib import Path

from src.engine.automation import tuning_performance_control_tower as mod


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _patch_dirs(monkeypatch, tmp_path):
    report_root = tmp_path / "data" / "report"
    apply_dir = tmp_path / "data" / "threshold_cycle" / "apply_plans"
    output_dir = report_root / "tuning_performance_control_tower"
    specs = {
        label: (report_root / label, prefix)
        for label, (_, prefix) in mod.SOURCE_SPECS.items()
    }
    monkeypatch.setattr(mod, "REPORT_ROOT_DIR", report_root)
    monkeypatch.setattr(mod, "REPORT_DIR", output_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "SOURCE_SPECS", specs)
    return report_root, apply_dir, output_dir


def test_tuning_performance_control_tower_separates_sim_progress_from_real_pnl(monkeypatch, tmp_path):
    report_root, apply_dir, output_dir = _patch_dirs(monkeypatch, tmp_path)
    target = "2026-05-26"
    previous = "2026-05-22"
    _write_json(
        report_root / "threshold_cycle_ev" / f"threshold_cycle_ev_{target}.json",
        {
            "daily_ev_summary": {
                "completed_trades": 7,
                "win_rate_pct": 57.14,
                "avg_profit_rate_pct": -0.46,
                "realized_pnl_krw": -2184,
                "source_split": {
                    "real": {"sample": 10, "avg_profit_rate": 0.088, "win_rate": 0.6},
                    "sim": {"sample": 730, "avg_profit_rate": -0.4989, "win_rate": 0.3493},
                    "combined": {"sample": 740, "avg_profit_rate": -0.491, "win_rate": 0.3527},
                    "combined_authority": "diagnostic_only_not_family_candidate_input",
                },
            },
            "warnings": [
                "swing_strategy_discovery:pending_future_quotes",
                "swing_lifecycle_decision_matrix:pending_future_quotes",
            ],
        },
    )
    _write_json(
        report_root / "runtime_approval_summary" / f"runtime_approval_summary_{target}.json",
        {
            "runtime_mutation_allowed": False,
            "summary": {
                "scalping_selected_auto_bounded_live": 3,
                "lifecycle_bucket_discovery_live_auto_apply_ready_count": 0,
                "lifecycle_bucket_discovery_surfaced_candidate_count": 184,
                "swing_lifecycle_bucket_discovery_sim_auto_approved_count": 6,
                "pattern_lab_currentness_status": "pass",
                "pattern_lab_ai_review_status": "pass",
                "producer_gap_discovery_status": "warning",
                "pattern_lab_propagation_status": "pass",
            },
            "warnings": [],
        },
    )
    _write_json(
        report_root / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{previous}.json",
        {"summary": {"candidate_count": 379, "surfaced_candidate_count": 120, "sim_auto_approved_count": 119, "live_auto_apply_ready_count": 1}},
    )
    _write_json(
        report_root / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {
                "status": "pass",
                "source_contract_status": "pass",
                "candidate_count": 414,
                "surfaced_candidate_count": 184,
                "sim_auto_approved_count": 184,
                "live_auto_apply_ready_count": 0,
                "state_counts": {"sim_auto_approved": 184, "source_only_keep_collecting": 230},
            },
            "surfaced_candidates": [
                {
                    "bucket_id": "entry:source_stage:wait6579_ev_cohort",
                    "stage": "entry",
                    "classification_state": "sim_auto_approved",
                    "recommended_action": "relax_or_recover",
                    "joined_sample": 163,
                    "source_quality_adjusted_ev_pct": 3.3661,
                }
            ],
        },
    )
    _write_json(
        report_root / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{previous}.json",
        {"summary": {"total_rows": 35228, "joined_rows": 33631, "promote_ready_count": 1, "entry_bucket_runtime_candidate_count": 6}},
    )
    _write_json(
        report_root / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{target}.json",
        {
            "summary": {
                "status": "pass",
                "total_rows": 48781,
                "joined_rows": 47168,
                "policy_pass_count": 5,
                "promote_ready_count": 1,
                "entry_bucket_runtime_candidate_count": 6,
                "scale_in_bucket_runtime_candidate_count": 10,
                "overnight_bucket_runtime_candidate_count": 2,
            }
        },
    )
    _write_json(
        report_root / "swing_lifecycle_decision_matrix" / f"swing_lifecycle_decision_matrix_{previous}.json",
        {"summary": {"total_rows": 1200, "probe_rows": 0, "pending_future_quote_count": 1118, "sim_auto_candidate_count": 4}},
    )
    _write_json(
        report_root / "swing_lifecycle_decision_matrix" / f"swing_lifecycle_decision_matrix_{target}.json",
        {
            "summary": {
                "status": "pass",
                "total_rows": 1721,
                "probe_rows": 121,
                "discovery_rows": 1600,
                "labeled_rows": 113,
                "pending_future_quote_count": 1434,
                "sim_auto_candidate_count": 6,
                "workorder_count": 9,
            }
        },
    )
    _write_json(
        report_root / "swing_lifecycle_bucket_discovery" / f"swing_lifecycle_bucket_discovery_{previous}.json",
        {"summary": {"candidate_count": 390, "surfaced_candidate_count": 390, "sim_auto_approved_count": 4, "code_patch_required_count": 4}},
    )
    _write_json(
        report_root / "swing_lifecycle_bucket_discovery" / f"swing_lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {
                "status": "pass",
                "candidate_count": 442,
                "surfaced_candidate_count": 442,
                "sim_auto_approved_count": 6,
                "source_only_keep_collecting_count": 426,
                "code_patch_required_count": 19,
            }
        },
    )
    _write_json(
        report_root / "code_improvement_workorder" / f"code_improvement_workorder_{target}.json",
        {
            "summary": {
                "selected_order_count": 64,
                "selected_decision_counts": {"implement_now": 38, "attach_existing_family": 26},
                "selected_route_counts": {"instrumentation_order": 30, "implement_now": 7, "existing_family": 26},
                "pattern_lab_ai_review_source_order_count": 0,
                "pattern_lab_currentness_source_order_count": 0,
            }
        },
    )
    _write_json(
        apply_dir / f"threshold_apply_{target}.json",
        {
            "status": "auto_bounded_live_ready",
            "apply_mode": "auto_bounded_live",
            "runtime_change": True,
            "auto_apply_selected": [{"family": "lifecycle_decision_matrix_runtime"}],
            "post_apply_attribution": {"status": "pending_applied_cohort", "runtime_change": False},
        },
    )

    report = mod.build_tuning_performance_control_tower(target)

    assert report["summary"]["primary_verdict"] == "sim_progress_no_live_bucket"
    assert report["summary"]["real_pnl_is_tuning_performance"] is False
    assert report["ldm_progression"]["lifecycle_bucket_discovery"]["delta"]["sim_auto_approved_count"] == 65
    assert report["ldm_progression"]["lifecycle_bucket_discovery"]["delta"]["live_auto_apply_ready_count"] == -1
    assert report["swing_progression"]["swing_lifecycle_decision_matrix"]["delta"]["probe_rows"] == 121
    assert report["ev_authority"]["real_pnl_allowed_use"] == "diagnostic_only_until_post_apply_attribution_closes"
    assert report["workorder"]["pattern_lab_ai_review_source_order_count"] == 0
    markdown = (output_dir / f"tuning_performance_control_tower_{target}.md").read_text(encoding="utf-8")
    assert "live_auto_apply_ready" in markdown
    assert "real_pnl_is_tuning_performance=false" in markdown
