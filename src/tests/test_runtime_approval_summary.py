import json

import pytest

from src.engine import runtime_approval_summary as mod


@pytest.fixture(autouse=True)
def _isolate_pattern_lab_audit_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing_currentness_audit"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_PROPAGATION_AUDIT_DIR", tmp_path / "missing_propagation_audit"
    )


def test_runtime_approval_summary_combines_scalping_and_swing(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    env_dir = tmp_path / "runtime_env"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    env_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    env_path = env_dir / "threshold_runtime_env_2026-05-11.env"
    env_path.write_text(
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true\n",
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-11.json").write_text(
        json.dumps(
            {
                "runtime_apply": {
                    "selected_families": ["score65_74_recovery_probe"],
                    "runtime_env_file": str(env_path),
                },
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "score65_74_recovery_probe",
                            "calibration_state": "adjust_up",
                            "confidence": 1.0,
                            "sample_count": 712,
                            "sample_floor": 20,
                        },
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-11.json").write_text(
        json.dumps(
            {
                "summary": {"requested": 0, "approved": 0},
                "candidates": [
                    {
                        "family": "swing_model_floor",
                        "sample_count": 3,
                        "sample_floor": 3,
                    }
                ],
                "blocked_requests": [
                    {
                        "family": "swing_model_floor",
                        "calibration_state": "freeze",
                        "tradeoff_score": 0.8657,
                        "block_reasons": [
                            "critical_instrumentation_gap",
                            "db_load_gap",
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-11")

    assert report["runtime_mutation_allowed"] is False
    assert report["summary"]["scalping_items"] == 1
    assert report["summary"]["scalping_selected_auto_bounded_live"] == 1
    assert (
        report["summary"]["scalping_legacy_hard_gate_risk_counts"][
            "no_unreviewed_hard_gate"
        ]
        == 1
    )
    assert report["summary"]["swing_blocked"] == 1
    assert (
        report["summary"]["swing_legacy_hard_gate_risk_counts"][
            "no_unreviewed_hard_gate"
        ]
        == 1
    )
    assert report["summary"]["microstructure_reaction_available"] is False
    assert (
        report["microstructure_reaction_context"]["runtime_mutation_allowed"] is False
    )
    assert report["application_timing"]["runtime_env_file"] == str(env_path)
    assert "WAIT 구간" in report["scalping"][0]["description"]
    assert (
        report["scalping"][0]["current_application"]
        == "PREOPEN env 적용: 당일 runtime 변경 대상"
    )
    assert report["scalping"][0]["gate_review_class"] == "entry_unlock_probe"
    assert report["scalping"][0]["legacy_hard_gate_risk"] == "no_unreviewed_hard_gate"
    assert "PREOPEN env" in report["scalping"][0]["state_interpretation"]
    assert report["swing"][0]["reason_label"] == "계측 gap, DB gap"
    assert (
        report["swing"][0]["current_application"]
        == "스윙 dry-run/probe 관찰: 실주문 변경 없음"
    )
    assert report["swing"][0]["gate_review_class"] == "approval_route_available"
    markdown = (out_dir / "runtime_approval_summary_2026-05-11.md").read_text(
        encoding="utf-8"
    )
    assert "## Scalping" in markdown
    assert "score65_74_recovery_probe" in markdown
    assert "설명" in markdown
    assert "현재 적용" in markdown
    assert "Gate 분류" in markdown
    assert "판정 해석" in markdown
    assert "## Swing" in markdown
    assert "swing_model_floor" in markdown


def test_runtime_approval_summary_surfaces_microstructure_source_only_context(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    (ev_dir / "threshold_cycle_ev_2026-05-31.json").write_text(
        json.dumps(
            {
                "sources": {
                    "microstructure_reaction_context": "data/report/microstructure_reaction_context/x.json"
                },
                "microstructure_reaction_context": {
                    "available": True,
                    "row_count": 3,
                    "ok_count": 2,
                    "missing_or_unusable_count": 1,
                    "real_submitted_count": 1,
                    "status_counts": {"ok": 2, "stale": 1},
                    "entry_reaction_quality_counts": {
                        "favorable_reaction": 1,
                        "neutral_unusable": 1,
                    },
                    "avg_ask_sweep_score": 61.5,
                    "avg_post_sweep_hold_score": 58.5,
                    "avg_bid_replenishment_score": 63.0,
                    "max_vi_proximity_risk": 70,
                    "runtime_effect": False,
                    "decision_authority": "entry_confidence_modifier_source_only",
                    "forbidden_uses": ["standalone_buy", "broker_guard_bypass"],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-31.json").write_text(
        json.dumps(
            {"summary": {"requested": 0, "approved": 0}, "blocked_requests": []}
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-31")

    summary = report["microstructure_reaction_context"]
    assert summary["available"] is True
    assert summary["runtime_mutation_allowed"] is False
    assert summary["decision_authority"] == "entry_confidence_modifier_source_only"
    assert summary["row_count"] == 3
    assert summary["ok_count"] == 2
    assert "standalone_buy" in summary["forbidden_uses"]
    markdown = (out_dir / "runtime_approval_summary_2026-05-31.md").read_text(
        encoding="utf-8"
    )
    assert "Microstructure Reaction Context" in markdown


def test_runtime_approval_summary_labels_hold_sample_contract_gaps(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    (ev_dir / "threshold_cycle_ev_2026-06-05.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "pre_submit_price_guard",
                            "calibration_state": "hold_sample",
                            "sample_count": 24790,
                            "source_sample_count": 24790,
                            "sample_floor": 20,
                            "source_metrics": {
                                "coverage_gap_type": "counterfactual_join_gap",
                                "attribution_gap": True,
                                "recommended_action_reason": "recovery_count=0 below floor=2479",
                            },
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-06-05.json").write_text(
        json.dumps(
            {"summary": {"requested": 0, "approved": 0}, "blocked_requests": []}
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-06-05")

    row = next(
        item
        for item in report["scalping"]
        if item["family"] == "pre_submit_price_guard"
    )
    assert row["reasons"] == ["counterfactual_join_gap", "recovery_floor_not_met"]
    assert row["reason_label"] == "counterfactual join gap, recovery floor 미달"
    assert "표본/소스 계약" in row["state_interpretation"]


def test_runtime_approval_summary_microstructure_summary_tolerates_malformed_types():
    payload = {
        "microstructure_reaction_context": {
            "available": True,
            "row_count": "bad",
            "ok_count": "2.9",
            "missing_or_unusable_count": None,
            "real_submitted_count": "x",
            "status_counts": ["not-a-dict"],
            "entry_reaction_quality_counts": "not-a-dict",
            "source_quality_counts": 1,
            "max_vi_proximity_risk": "not-numeric",
            "forbidden_uses": "standalone_buy",
            "runtime_effect": "true",
        }
    }

    summary = mod._microstructure_reaction_context_summary(payload)

    assert summary["row_count"] == 0
    assert summary["ok_count"] == 2
    assert summary["missing_or_unusable_count"] == 0
    assert summary["real_submitted_count"] == 0
    assert summary["status_counts"] == {}
    assert summary["entry_reaction_quality_counts"] == {}
    assert summary["source_quality_counts"] == {}
    assert summary["max_vi_proximity_risk"] == 0
    assert summary["forbidden_uses"] == []
    assert "microstructure_reaction_runtime_effect_unexpected" in summary["warnings"]


def test_runtime_approval_summary_surfaces_swing_bucket_ai_fail_closed():
    ev_report = {
        "swing_lifecycle_bucket_discovery": {
            "available": True,
            "source_contract_status": "pass",
            "ai_two_pass_review_status": "missing",
            "ai_fail_closed": True,
            "warnings": ["ai_two_pass_review_missing_fail_closed"],
        }
    }

    summary = mod._swing_lifecycle_bucket_discovery_summary(ev_report)

    assert summary["ai_two_pass_review_status"] == "missing"
    assert summary["ai_fail_closed"] is True
    assert "ai_two_pass_review_missing_fail_closed" in summary["warnings"]
    assert "ai_two_pass_review_fail_closed_sim_auto_blocked" in summary["warnings"]


def test_runtime_approval_summary_preserves_swing_flow_metrics():
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "available": True,
            "total_rows": 9,
            "swing_lifecycle_flow_bucket_count": 1,
            "complete_flow_count": 3,
            "incomplete_flow_count": 0,
            "identity_join_rate": 1.0,
            "complete_flow_rate": 1.0,
            "join_contract_blocked": False,
            "sim_auto_candidate_count": 1,
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
            "raw_swing_event_count": 1200,
            "ldm_consumed_event_count": 48,
            "ldm_event_coverage_rate": 0.04,
            "unmapped_swing_stage_counts": {"swing_other": 5},
        },
        "swing_lifecycle_bucket_discovery": {
            "available": True,
            "source_contract_status": "pass",
            "candidate_count": 2,
            "surfaced_candidate_count": 2,
            "sim_auto_approved_count": 1,
            "sim_auto_reviewed_candidate_count": 21,
            "sim_auto_unreviewed_candidate_count": 0,
            "sim_auto_downgraded_by_review_count": 0,
            "sim_auto_review_shard_count": 2,
            "swing_lifecycle_flow_bucket_count": 1,
            "complete_flow_count": 3,
            "incomplete_flow_count": 0,
            "identity_join_rate": 1.0,
            "complete_flow_rate": 1.0,
            "join_contract_blocked": False,
            "flow_sim_auto_approved_count": 1,
            "stage_only_source_only_count": 1,
        },
    }

    matrix_summary = mod._swing_lifecycle_matrix_summary(ev_report)
    discovery_summary = mod._swing_lifecycle_bucket_discovery_summary(ev_report)

    assert matrix_summary["swing_lifecycle_flow_bucket_count"] == 1
    assert matrix_summary["sim_auto_candidate_ids"] == [
        "swing_ldm_lifecycle_flow_combo_parent"
    ]
    assert matrix_summary["raw_swing_event_count"] == 1200
    assert matrix_summary["ldm_consumed_event_count"] == 48
    assert matrix_summary["ldm_event_coverage_rate"] == 0.04
    assert matrix_summary["unmapped_swing_stage_counts"] == {"swing_other": 5}
    assert discovery_summary["swing_lifecycle_flow_bucket_count"] == 1
    assert discovery_summary["flow_sim_auto_approved_count"] == 1
    assert discovery_summary["stage_only_source_only_count"] == 1
    assert discovery_summary["sim_auto_reviewed_candidate_count"] == 21
    assert discovery_summary["sim_auto_review_shard_count"] == 2


def test_runtime_approval_summary_tolerates_malformed_swing_coverage_numbers():
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "available": True,
            "total_rows": "bad-total",
            "raw_swing_event_count": "bad-raw-count",
            "ldm_consumed_event_count": "bad-consumed-count",
            "ldm_event_coverage_rate": "bad-rate",
        },
    }

    summary = mod._swing_lifecycle_matrix_summary(ev_report)

    assert summary["total_rows"] == 0
    assert summary["raw_swing_event_count"] == 0
    assert summary["ldm_consumed_event_count"] == 0
    assert summary["ldm_event_coverage_rate"] == 0.0
    assert (
        "swing_lifecycle_decision_matrix_low_event_coverage" not in summary["warnings"]
    )


def test_runtime_approval_summary_tolerates_non_finite_swing_coverage_numbers():
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "available": True,
            "raw_swing_event_count": 1200,
            "ldm_consumed_event_count": 48,
            "ldm_event_coverage_rate": "nan",
        },
    }

    summary = mod._swing_lifecycle_matrix_summary(ev_report)

    assert summary["raw_swing_event_count"] == 1200
    assert summary["ldm_consumed_event_count"] == 48
    assert summary["ldm_event_coverage_rate"] == 0.0
    assert "swing_lifecycle_decision_matrix_low_event_coverage" in summary["warnings"]

    ev_report["swing_lifecycle_decision_matrix"]["ldm_event_coverage_rate"] = "inf"
    summary = mod._swing_lifecycle_matrix_summary(ev_report)

    assert summary["ldm_event_coverage_rate"] == 0.0
    assert "swing_lifecycle_decision_matrix_low_event_coverage" in summary["warnings"]


def test_runtime_approval_summary_surfaces_swing_bucket_ai_followup_separately():
    ev_report = {
        "swing_lifecycle_bucket_discovery": {
            "available": True,
            "source_contract_status": "pass",
            "ai_two_pass_review_status": "parsed",
            "ai_fail_closed": False,
            "ai_review_followup_required": True,
            "ai_review_followup_reasons": ["audit_status=correction_required"],
            "sim_auto_blocked_by_ai_review_followup": True,
            "code_improvement_workorder_ids": [
                "swing_lifecycle_bucket_discovery_ai_review_followup"
            ],
            "implemented_code_improvement_workorder_ids": [
                "swing_lifecycle_bucket_discovery_ai_review_followup"
            ],
            "pending_code_improvement_workorder_ids": [],
            "ai_review_followup_workorder_ids": [
                "swing_lifecycle_bucket_discovery_ai_review_followup"
            ],
            "warnings": [
                "swing_lifecycle_bucket_discovery:ai_review_followup_required"
            ],
        }
    }

    summary = mod._swing_lifecycle_bucket_discovery_summary(ev_report)

    assert summary["ai_two_pass_review_status"] == "parsed"
    assert summary["ai_fail_closed"] is False
    assert summary["ai_review_followup_required"] is True
    assert summary["sim_auto_blocked_by_ai_review_followup"] is True
    assert summary["code_improvement_workorder_ids"] == [
        "swing_lifecycle_bucket_discovery_ai_review_followup"
    ]
    assert summary["ai_review_followup_workorder_ids"] == [
        "swing_lifecycle_bucket_discovery_ai_review_followup"
    ]
    assert "ai_review_followup_required" in summary["warnings"]
    assert "ai_review_followup_sim_auto_blocked" in summary["warnings"]
    assert not any("fail_closed" in warning for warning in summary["warnings"])


def test_runtime_approval_summary_tolerates_malformed_swing_discovery_counts():
    ev_report = {
        "swing_lifecycle_bucket_discovery": {
            "available": True,
            "candidate_count": "bad-candidate",
            "surfaced_candidate_count": "bad-surfaced",
            "sim_auto_approved_count": "bad-approved",
            "sim_auto_reviewed_candidate_count": "bad-reviewed",
            "sim_auto_unreviewed_candidate_count": "bad-unreviewed",
            "sim_auto_downgraded_by_review_count": "bad-downgraded",
            "sim_auto_review_shard_count": "bad-shard",
            "flow_sim_auto_approved_count": "bad-flow",
            "stage_only_source_only_count": "bad-stage-only",
            "code_patch_required_count": "bad-code-patch",
            "runtime_blocked_contract_gap_count": "bad-contract",
            "automation_handoff_gap_count": "bad-handoff",
        }
    }

    summary = mod._swing_lifecycle_bucket_discovery_summary(ev_report)

    assert summary["candidate_count"] == 0
    assert summary["surfaced_candidate_count"] == 0
    assert summary["sim_auto_approved_count"] == 0
    assert summary["sim_auto_reviewed_candidate_count"] == 0
    assert summary["sim_auto_unreviewed_candidate_count"] == 0
    assert summary["sim_auto_downgraded_by_review_count"] == 0
    assert summary["sim_auto_review_shard_count"] == 0
    assert summary["flow_sim_auto_approved_count"] == 0
    assert summary["stage_only_source_only_count"] == 0
    assert summary["code_patch_required_count"] == 0
    assert summary["runtime_blocked_contract_gap_count"] == 0
    assert summary["automation_handoff_gap_count"] == 0


def test_runtime_approval_summary_surfaces_entry_adm_runtime_bias_summary(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    adm_dir = tmp_path / "scalp_entry_action_decision_matrix"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    for directory in (ev_dir, adm_dir, swing_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    adm_path = adm_dir / "scalp_entry_action_decision_matrix_2026-05-18.json"
    adm_path.write_text(json.dumps({"status": "warning"}), encoding="utf-8")
    (ev_dir / "threshold_cycle_ev_2026-05-18.json").write_text(
        json.dumps(
            {
                "sources": {"scalp_entry_action_decision_matrix": str(adm_path)},
                "scalp_entry_action_decision_matrix": {
                    "available": True,
                    "status": "warning",
                    "joined_sample": 2,
                    "sample_floor": 20,
                    "prompt_applied_count": 0,
                    "missing_actions": ["WAIT_REQUOTE", "BUY_DEFENSIVE"],
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_adjusted_ev_pct": -2.22,
                    "unknown_bucket_summary": {
                        "affected_rows": 3,
                        "source_quality_gate": "source_quality_blocker",
                    },
                    "top_actions": [
                        {
                            "action": "BUY_NOW",
                            "joined_sample": 2,
                            "source_quality_adjusted_ev_pct": -2.22,
                        }
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-18.json").write_text(
        json.dumps(
            {"summary": {"requested": 0, "approved": 0}, "blocked_requests": []}
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-18")

    adm_summary = report["scalp_entry_action_decision_matrix"]
    assert (
        adm_summary["runtime_bias_scope"] == "force_wait_force_drop_buy_defensive_bias"
    )
    assert adm_summary["joined_action_ev_pct"] == -2.22
    assert adm_summary["ready_for_daily_policy_tuning"] is False
    assert "joined_sample_below_sample_floor" in adm_summary["warnings"]
    assert "missing_action_bucket" in adm_summary["warnings"]
    assert "prompt_context_not_loaded" in adm_summary["warnings"]
    assert "unknown_bucket_source_quality_gap" in adm_summary["warnings"]
    assert adm_summary["unknown_bucket_summary"]["affected_rows"] == 3
    assert report["summary"]["scalp_entry_adm_ready_for_daily_policy_tuning"] is False
    adm_row = next(
        row
        for row in report["scalping"]
        if row["family"] == "scalp_entry_action_decision_matrix_advisory"
    )
    assert adm_row["gate_review_class"] == "entry_adm_runtime_bias_operator_override"
    assert adm_row["runtime_bias_scope"] == "force_wait_force_drop_buy_defensive_bias"
    markdown = (out_dir / "runtime_approval_summary_2026-05-18.md").read_text(
        encoding="utf-8"
    )
    assert "## Scalp Entry ADM" in markdown
    assert "BUY_DEFENSIVE" in markdown


def test_runtime_approval_summary_dedupes_lifecycle_matrix_decision_row(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    (ev_dir / "threshold_cycle_ev_2026-05-20.json").write_text(
        json.dumps(
            {
                "runtime_apply": {
                    "selected_families": ["lifecycle_decision_matrix_runtime"]
                },
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "lifecycle_decision_matrix_runtime",
                            "calibration_state": "adjust_up",
                            "tradeoff_score": 1.0,
                            "sample_count": 2000,
                            "sample_floor": 20,
                        }
                    ]
                },
                "lifecycle_decision_matrix": {
                    "available": True,
                    "sample_floor": 20,
                    "metrics": {
                        "total_rows": 7155,
                        "joined_rows": 6109,
                        "policy_pass_count": 5,
                        "promote_ready_count": 0,
                    },
                    "policy_entries": [
                        {"stage": "entry", "stage_ev_composite_pct": -0.0239},
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-20.json").write_text(
        json.dumps(
            {"summary": {"requested": 0, "approved": 0}, "blocked_requests": []}
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-20")

    lifecycle_rows = [
        row
        for row in report["scalping"]
        if row["family"] == "lifecycle_decision_matrix_runtime"
    ]
    assert len(lifecycle_rows) == 1
    assert lifecycle_rows[0]["sample"]["count"] == 7155
    assert report["summary"]["scalping_selected_auto_bounded_live"] == 1


def test_runtime_approval_summary_falls_back_to_lifecycle_bucket_source(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    matrix_dir = tmp_path / "lifecycle_decision_matrix"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    matrix_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    matrix_path = matrix_dir / "lifecycle_decision_matrix_2026-05-21.json"
    matrix_path.write_text(
        json.dumps(
            {
                "matrix_version": "ldm-test",
                "entry_bucket_attribution": {
                    "summary": {"runtime_candidate_count": 1, "workorder_count": 1},
                    "runtime_approval_candidates": [{"candidate_id": "entry_bucket_1"}],
                    "code_improvement_workorders": [{"workorder_id": "entry_order"}],
                },
                "submit_bucket_attribution": {
                    "summary": {
                        "runtime_candidate_count": 0,
                        "workorder_count": 1,
                        "contract_gap_count": 1,
                    },
                    "runtime_approval_candidates": [],
                    "code_improvement_workorders": [{"workorder_id": "submit_order"}],
                    "post_submit_contract_gaps": [
                        {"gap_type": "broker_receipt_contract_gap"}
                    ],
                },
                "scale_in_bucket_attribution": {
                    "summary": {"runtime_candidate_count": 1, "workorder_count": 1},
                    "runtime_approval_candidates": [
                        {"candidate_id": "scale_in_bucket_1"}
                    ],
                    "code_improvement_workorders": [{"workorder_id": "scale_order"}],
                },
                "overnight_bucket_attribution": {
                    "summary": {"runtime_candidate_count": 1, "workorder_count": 1},
                    "runtime_approval_candidates": [
                        {"candidate_id": "overnight_bucket_1"}
                    ],
                    "code_improvement_workorders": [
                        {"workorder_id": "overnight_order"}
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-21.json").write_text(
        json.dumps(
            {
                "sources": {"lifecycle_decision_matrix": str(matrix_path)},
                "runtime_apply": {
                    "selected_families": ["lifecycle_decision_matrix_runtime"]
                },
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "lifecycle_decision_matrix_runtime",
                            "calibration_state": "adjust_up",
                            "sample_count": 2000,
                            "sample_floor": 20,
                        }
                    ]
                },
                "lifecycle_decision_matrix": {
                    "available": True,
                    "status": "ready",
                    "total_rows": 2000,
                    "joined_rows": 1900,
                    "policy_pass_count": 3,
                    "promote_ready_count": 0,
                    "complete_flow_count": 0,
                    "incomplete_flow_count": 4,
                    "complete_flow_rate": 0.0,
                    "join_contract_blocked": True,
                    "bundle_ev_tuning_state": "blocked_join_gap",
                    "top_incomplete_reason": "identity_namespace_mismatch",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-21.json").write_text(
        json.dumps(
            {"summary": {"requested": 0, "approved": 0}, "blocked_requests": []}
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-21")
    matrix = report["lifecycle_decision_matrix"]

    assert matrix["matrix_version"] == "ldm-test"
    assert matrix["entry_bucket_runtime_candidate_count"] == 1
    assert matrix["entry_bucket_runtime_approval_candidates"] == [
        {"candidate_id": "entry_bucket_1"}
    ]
    assert matrix["submit_bucket_attribution_summary"]["contract_gap_count"] == 1
    assert matrix["submit_bucket_code_improvement_workorders"] == [
        {"workorder_id": "submit_order"}
    ]
    assert matrix["post_submit_contract_gaps"] == [
        {"gap_type": "broker_receipt_contract_gap"}
    ]
    assert matrix["scale_in_bucket_runtime_candidate_count"] == 1
    assert matrix["scale_in_bucket_runtime_approval_candidates"] == [
        {"candidate_id": "scale_in_bucket_1"}
    ]
    assert matrix["overnight_bucket_runtime_candidate_count"] == 1
    assert matrix["overnight_bucket_runtime_approval_candidates"] == [
        {"candidate_id": "overnight_bucket_1"}
    ]
    assert matrix["complete_flow_count"] == 0
    assert matrix["incomplete_flow_count"] == 4
    assert matrix["join_contract_blocked"] is True
    assert matrix["bundle_ev_tuning_state"] == "blocked_join_gap"
    assert matrix["top_incomplete_reason"] == "identity_namespace_mismatch"


def test_runtime_approval_summary_holds_latency_when_recommendation_not_allowed(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    (ev_dir / "threshold_cycle_ev_2026-05-20.json").write_text(
        json.dumps(
            {
                "runtime_apply": {
                    "selected_families": ["latency_classifier_runtime_profile"]
                },
                "entry_funnel": {
                    "latency_submit_routing": "latency_submit_recovery_hold",
                    "latency_block_events": 621,
                    "latency_pass_events": 0,
                    "order_bundle_submitted_events": 0,
                    "recommended_action": "hold",
                    "recommended_action_reason": "counterfactual_joined_sample=1 below floor=3",
                    "allowed_runtime_apply": False,
                    "would_safe_pass_events": 0,
                    "would_caution_normal_events": 220,
                    "would_recovery_canary_events": 220,
                    "counterfactual_joined_sample": 1,
                    "counterfactual_ev_pct": -3.704,
                    "missed_winner_recovered": 0,
                    "avoided_loser_lost": 1,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-20.json").write_text(
        json.dumps(
            {"summary": {"requested": 0, "approved": 0}, "blocked_requests": []}
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-20")

    latency = next(
        row
        for row in report["scalping"]
        if row["family"] == "latency_classifier_runtime_profile"
    )
    assert latency["state"] == "hold_sample"
    assert latency["selected_auto_bounded_live"] is False
    assert latency["previous_selected_auto_bounded_live"] is True
    assert latency["allowed_runtime_apply"] is False
    assert (
        latency["current_application"]
        == "보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음"
    )
    assert report["summary"]["scalping_selected_auto_bounded_live"] == 0


def test_runtime_approval_summary_warns_when_sources_missing(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-11")

    assert "threshold_cycle_ev_missing" in report["warnings"]
    assert "swing_runtime_approval_missing" in report["warnings"]


def test_runtime_approval_summary_surfaces_source_parse_errors(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)
    (ev_dir / "threshold_cycle_ev_2026-05-11.json").write_text(
        "{bad json", encoding="utf-8"
    )
    (swing_dir / "swing_runtime_approval_2026-05-11.json").write_text(
        json.dumps({"summary": {"requested": 0}, "candidates": []}),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-11")

    assert report["source_load_diagnostics"][0]["status"] == "parse_error"
    assert (
        "source_load_parse_error:threshold_cycle_ev_2026-05-11.json"
        in report["warnings"]
    )
    markdown = (out_dir / "runtime_approval_summary_2026-05-11.md").read_text(
        encoding="utf-8"
    )
    assert "Source Load Diagnostics" in markdown


def test_runtime_approval_summary_classifies_legacy_gate_and_contract_gaps(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    (ev_dir / "threshold_cycle_ev_2026-05-15.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "liquidity_gate_refined_candidate",
                            "calibration_state": "hold",
                        },
                        {
                            "family": "pre_submit_price_guard",
                            "calibration_state": "freeze",
                        },
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "summary": {"requested": 0, "approved": 0},
                "candidates": [
                    {
                        "family": "swing_gatekeeper_accept_reject",
                        "sample_count": 27,
                        "sample_floor": 5,
                    }
                ],
                "blocked_requests": [
                    {
                        "family": "swing_gatekeeper_accept_reject",
                        "calibration_state": "freeze",
                        "tradeoff_score": 0.8361,
                        "block_reasons": ["runtime_family_guard_missing"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-15")

    scalping = {row["family"]: row for row in report["scalping"]}
    assert (
        scalping["liquidity_gate_refined_candidate"]["gate_review_class"]
        == "superseded_legacy_pre_ai_gate"
    )
    assert (
        scalping["liquidity_gate_refined_candidate"]["legacy_hard_gate_risk"]
        == "legacy_summary_superseded"
    )
    assert (
        scalping["pre_submit_price_guard"]["legacy_hard_gate_risk"]
        == "intentional_safety_guard"
    )
    swing = report["swing"][0]
    assert swing["gate_review_class"] == "legacy_hard_gate_contract_gap"
    assert swing["legacy_hard_gate_risk"] == "contract_gap"
    assert "blocked_gatekeeper_reject" in swing["analysis_coverage"]
    assert (
        report["summary"]["scalping_legacy_hard_gate_risk_counts"][
            "legacy_summary_superseded"
        ]
        == 1
    )
    assert report["summary"]["swing_legacy_hard_gate_risk_counts"]["contract_gap"] == 1


def test_runtime_approval_summary_decomposes_hold_defer_when_sample_ready(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    (ev_dir / "threshold_cycle_ev_2026-06-11.json").write_text(
        json.dumps({"calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-06-11.json").write_text(
        json.dumps(
            {
                "date": "2026-06-11",
                "summary": {"requested": 0, "approved": 0},
                "candidates": [
                    {
                        "family": "swing_holding_flow_defer",
                        "sample_count": 137,
                        "sample_floor": 5,
                        "source_metrics": {
                            "sample_count": 137,
                            "field_coverage": {
                                "flow_action": 0,
                                "defer_sec": 0,
                                "worsen_after_candidate": 0,
                            },
                        },
                    }
                ],
                "blocked_requests": [
                    {
                        "family": "swing_holding_flow_defer",
                        "calibration_state": "freeze",
                        "tradeoff_score": 0.32,
                        "block_reasons": [
                            "severe_downside_guard",
                            "runtime_family_guard_missing",
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-06-11")

    row = report["swing"][0]
    assert row["family"] == "swing_holding_flow_defer"
    assert row["sample"]["status"] == "ready"
    assert (
        row["gate_review_class"]
        == "source_quality_and_runtime_contract_gap_holding_axis"
    )
    assert row["legacy_hard_gate_risk"] == "source_quality_or_contract_gap"
    assert row["hold_defer_breakdown"] == {
        "sample_floor_status": "ready",
        "sample_count": 137,
        "sample_floor": 5,
        "field_coverage": {
            "flow_action": 0,
            "defer_sec": 0,
            "worsen_after_candidate": 0,
        },
        "missing_component_fields": [
            "flow_action",
            "defer_sec",
            "worsen_after_candidate",
        ],
        "runtime_guard_status": "missing",
        "downside_guard_status": "blocked",
    }
    assert "표본 floor는 충족" in row["hard_gate_review"]
    assert (
        report["summary"]["swing_legacy_hard_gate_risk_counts"][
            "source_quality_or_contract_gap"
        ]
        == 1
    )


def test_runtime_approval_summary_does_not_mark_sample_ready_swing_quality_axis_as_sample_gap(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    (ev_dir / "threshold_cycle_ev_2026-06-11.json").write_text(
        json.dumps({"calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-06-11.json").write_text(
        json.dumps(
            {
                "date": "2026-06-11",
                "summary": {"requested": 0, "approved": 0},
                "candidates": [
                    {
                        "family": "swing_entry_ofi_qi_execution_quality",
                        "sample_count": 17701,
                        "sample_floor": 5,
                    }
                ],
                "blocked_requests": [
                    {
                        "family": "swing_entry_ofi_qi_execution_quality",
                        "calibration_state": "freeze",
                        "tradeoff_score": 0.32,
                        "block_reasons": [
                            "entry_ofi_qi_invalid_micro_context",
                            "runtime_family_guard_missing",
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-06-11")

    row = report["swing"][0]
    assert row["sample"]["status"] == "ready"
    assert (
        row["gate_review_class"] == "source_quality_or_contract_gap_entry_quality_axis"
    )
    assert row["legacy_hard_gate_risk"] == "source_quality_or_contract_gap"
    assert "표본 floor는 충족" in row["hard_gate_review"]
    assert (
        "sample_or_contract_gap"
        not in report["summary"]["swing_legacy_hard_gate_risk_counts"]
    )


def test_runtime_approval_summary_surfaces_swing_one_share_legacy_archive_request(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    approval_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    (ev_dir / "threshold_cycle_ev_2026-05-15.json").write_text(
        json.dumps({"calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "summary": {"requested": 1, "approved": 0},
                "approval_requests": [
                    {
                        "family": "swing_one_share_real_canary_phase0",
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "approval_id": "swing_one_share_real_canary:2026-05-15:phase0",
                        "calibration_state": "approval_required",
                    }
                ],
                "blocked_requests": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-15")

    assert report["summary"]["swing_requested"] == 1
    assert report["summary"]["swing_blocked"] == 0
    assert report["summary"]["swing_legacy_archive"] == 1
    assert report["summary"]["swing_legacy_phase0_ignored"] == 1
    assert report["summary"]["swing_legacy_hard_gate_risk_counts"] == {}
    assert len(report["swing"]) == 1
    row = report["swing"][0]
    assert row["family"] == "swing_one_share_real_canary_phase0"
    assert row["state"] == "legacy_archive"
    assert row["reasons"] == ["legacy_phase0_real_canary_ignored"]
    assert row["selected_auto_bounded_live"] is False
    assert row["approval_live_ready"] is False
    assert row["actual_order_submitted"] is False
    assert row["broker_order_forbidden"] is True


def test_runtime_approval_summary_surfaces_panic_approval_requests(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-13.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_state": "PANIC_SELL",
                            "panic_regime_mode": "PANIC_DETECTED",
                            "panic_regime_decision_authority": "source_quality_only",
                            "panic_regime_runtime_effect": "report_only_no_mutation",
                            "stop_loss_exit_count": 2,
                            "confirmation_eligible_exit_count": 1,
                            "microstructure_max_panic_score": 0.91,
                            "candidate_status": {
                                "panic_stop_confirmation": "report_only_candidate"
                            },
                        },
                        "panic_buying": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_state": "PANIC_BUY",
                            "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                            "panic_buy_regime_decision_authority": "source_quality_only",
                            "panic_buy_regime_runtime_effect": "report_only_no_mutation",
                            "risk_regime_gate_state": "confirmed_panic_buy",
                            "risk_regime_gate_authority": "source_quality_only",
                            "risk_regime_threshold_mode": "dynamic_quantile",
                            "confirmed_evidence_count": 4,
                            "panic_buy_active_count": 1,
                            "tp_counterfactual_count": 3,
                            "trailing_winner_count": 1,
                            "max_panic_buy_score": 0.88,
                            "market_wide_panic_buy_confirmed": True,
                            "market_breadth_risk_on_advisory": True,
                            "candidate_status": {
                                "panic_buy_runner_tp_canary": "report_only_candidate"
                            },
                        },
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-13.json").write_text(
        json.dumps(
            {
                "sources": {"calibration": str(calibration_path)},
                "calibration_outcome": {"decisions": []},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-13")

    assert report["summary"]["panic_approval_requested"] == 0
    assert {row["family"] for row in report["panic"]} == {
        "panic_entry_freeze_guard",
        "panic_buy_runner_tp_canary",
    }
    assert all(row["state"] == "approval_contract_missing" for row in report["panic"])
    assert all(
        row["approval_contract_status"] == "contract_missing" for row in report["panic"]
    )
    assert all(row["selected_auto_bounded_live"] is False for row in report["panic"])
    panic_sell = next(
        row for row in report["panic"] if row["family"] == "panic_entry_freeze_guard"
    )
    assert panic_sell["panic_regime_mode"] == "PANIC_DETECTED"
    assert panic_sell["panic_regime_decision_authority"] == "source_quality_only"
    assert (
        "entry_pre_submit_runtime_guard"
        in panic_sell["approval_contract_missing_components"]
    )
    panic_buy = next(
        row for row in report["panic"] if row["family"] == "panic_buy_runner_tp_canary"
    )
    assert panic_buy["panic_buy_regime_mode"] == "PANIC_BUY_CONTINUATION"
    assert panic_buy["panic_buy_regime_decision_authority"] == "source_quality_only"
    assert panic_buy["risk_regime_gate_state"] == "confirmed_panic_buy"
    assert panic_buy["risk_regime_threshold_mode"] == "dynamic_quantile"
    assert panic_buy["confirmed_evidence_count"] == 4
    assert panic_buy["market_wide_panic_buy_confirmed"] is True
    assert panic_buy["market_breadth_risk_on_advisory"] is True
    markdown = (out_dir / "runtime_approval_summary_2026-05-13.md").read_text(
        encoding="utf-8"
    )
    assert "## Panic" in markdown
    assert "panic_buy_runner_tp_canary" in markdown


def test_runtime_approval_summary_freezes_panic_request_on_source_quality_blocker(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-14.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_state": "NORMAL",
                            "active_sim_probe_positions": 3,
                            "microstructure_max_panic_score": 0.84,
                            "candidate_status": {
                                "panic_entry_freeze_guard": "report_only_candidate"
                            },
                            "source_quality_blockers": ["market_regime_not_risk_off"],
                            "market_breadth_followup_candidate": True,
                        },
                        "panic_buying": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_state": "PANIC_BUY",
                            "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                            "panic_buy_regime_decision_authority": "source_quality_only",
                            "panic_buy_regime_runtime_effect": "report_only_no_mutation",
                            "risk_regime_gate_state": "watch",
                            "risk_regime_gate_authority": "source_quality_only",
                            "risk_regime_threshold_mode": "dynamic_quantile",
                            "confirmed_evidence_count": 2,
                            "panic_buy_active_count": 1,
                            "tp_counterfactual_count": 3,
                            "max_panic_buy_score": 0.88,
                            "market_wide_panic_buy_confirmed": False,
                            "market_breadth_risk_on_advisory": False,
                            "source_quality_blockers": [
                                "panic_buy_local_unconfirmed_by_market_breadth"
                            ],
                            "candidate_status": {
                                "panic_buy_runner_tp_canary": "report_only_candidate"
                            },
                        },
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text(
        json.dumps(
            {
                "sources": {"calibration": str(calibration_path)},
                "calibration_outcome": {"decisions": []},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-14")

    rows = {row["family"]: row for row in report["panic"]}
    row = rows["panic_entry_freeze_guard"]
    assert row["state"] == "freeze"
    assert "source_quality_blocker" in row["reasons"]
    assert row["source_quality_blockers"] == ["market_regime_not_risk_off"]
    assert row["market_breadth_followup_candidate"] is True
    panic_buy = rows["panic_buy_runner_tp_canary"]
    assert panic_buy["state"] == "freeze"
    assert "source_quality_blocker" in panic_buy["reasons"]
    assert panic_buy["source_quality_blockers"] == [
        "panic_buy_local_unconfirmed_by_market_breadth"
    ]


def test_runtime_approval_summary_does_not_request_for_inactive_panic_candidate_status(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-14.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_state": "NORMAL",
                            "active_sim_probe_positions": 10,
                            "candidate_status": {
                                "panic_entry_freeze_guard": "inactive_no_panic",
                                "panic_attribution_pack": "active_report_only",
                            },
                            "market_breadth_followup_candidate": True,
                        }
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text(
        json.dumps(
            {
                "sources": {"calibration": str(calibration_path)},
                "calibration_outcome": {"decisions": []},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-14")

    assert report["summary"]["panic_approval_requested"] == 0
    row = report["panic"][0]
    assert row["state"] == "hold"
    assert row["reasons"] == ["hold"]
