import json

from src.engine import swing_lifecycle_bucket_discovery as mod


def test_bucket_discovery_auto_approves_sim_only_candidates(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    discovery_dir = tmp_path / "discovery"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", discovery_dir)

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": "safe_pool|probe",
                            "lifecycle_stage": "entry",
                            "recommended_route": "sim_auto_approved",
                            "source_quality_gate": "pass",
                            "joined_sample": 3,
                            "sample_count": 3,
                            "source_quality_adjusted_ev_pct": 1.2,
                        }
                    ],
                    "code_improvement_workorders": [],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    assert report["summary"]["sim_auto_approved_count"] == 1
    candidate = report["sim_auto_approved_candidates"][0]
    assert candidate["classification_state"] == "sim_auto_approved"
    assert candidate["next_route"] == "next_preopen_swing_sim_policy_input"
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True
    assert candidate["allowed_runtime_apply"] is False
    assert "real_order_submit" in candidate["forbidden_uses"]
    assert report["human_intervention_required"] is False


def test_bucket_discovery_flags_daily_simulation_contract_gap(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps({"input_contract": {"swing_daily_simulation_consumed": True}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    assert report["summary"]["source_contract_status"] == "fail"
    assert report["summary"]["runtime_blocked_contract_gap_count"] == 1
    assert report["surfaced_candidates"][0]["classification_state"] == "runtime_blocked_contract_gap"
    assert report["surfaced_candidates"][0]["allowed_runtime_apply"] is False
    assert "runtime_threshold_mutation" in report["surfaced_candidates"][0]["forbidden_uses"]


def test_bucket_discovery_normalizes_explicit_workorder_contract(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {
                    "buckets": [],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "source_gap",
                            "runtime_effect": True,
                            "allowed_runtime_apply": True,
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)
    workorder = report["code_improvement_workorders"][0]

    assert workorder["runtime_effect"] is False
    assert workorder["allowed_runtime_apply"] is False
    assert workorder["actual_order_submitted"] is False
    assert workorder["broker_order_forbidden"] is True
    assert "real_order_submit" in workorder["forbidden_uses"]


def test_bucket_discovery_surfaces_ai_review_augmentation_workorders(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "holding_exit_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "holding_exit_bucket_attribution",
                            "bucket_key": "mfe_low|mae_low|time_stop",
                            "lifecycle_stage": "holding_exit",
                            "recommended_route": "source_only_keep_collecting",
                            "source_quality_gate": "hold_sample",
                            "joined_sample": 1,
                            "sample_count": 1,
                        }
                    ],
                    "code_improvement_workorders": [],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    assert report["ai_review_policy"]["status"] == "not_configured"
    assert report["summary"]["ai_review_augmentation_point_count"] >= 3
    assert report["summary"]["ai_audit_point_count"] >= 3
    assert report["ai_audit"]["sim_auto_policy_preserved"] is True
    assert all(item["runtime_effect"] is False for item in report["ai_audit"]["audit_points"])
    assert all(item["allowed_runtime_apply"] is False for item in report["ai_audit"]["audit_points"])
    assert "swing_ldm_ai_review_not_configured" in report["warnings"]
    ai_workorders = [
        item
        for item in report["code_improvement_workorders"]
        if item["target_subsystem"] == "swing_lifecycle_bucket_discovery_ai_review"
    ]
    assert ai_workorders
    assert all(item["runtime_effect"] is False for item in ai_workorders)
    assert all(item["allowed_runtime_apply"] is False for item in ai_workorders)
    assert all(item["required_flow"] == ["interpretation", "audit", "final_conclusions"] for item in ai_workorders)


def test_bucket_discovery_surfaces_swing_entry_bottleneck_handoff(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "swing_entry_bottleneck": {
                    "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
                    "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
                    "counts": {"entry_unique": 15, "submitted_unique_records": 0},
                    "ratios": {"probe_to_blocked_unique_pct": 0.0},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    candidate = next(
        item
        for item in report["surfaced_candidates"]
        if item["bucket_id"] == "swing_entry_bottleneck_swing_entry_drought_critical"
    )
    assert candidate["classification_state"] == "code_patch_required"
    assert candidate["next_route"] == "code_improvement_workorder"
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False
    assert report["summary"]["swing_entry_bottleneck_primary"] == "SWING_ENTRY_DROUGHT_CRITICAL"
    assert report["summary"]["swing_entry_bottleneck_candidate_present"] is True
