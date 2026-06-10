from src.engine.approval_contracts import annotate_approval_request, approval_contract_for


def test_approval_contract_registry_marks_ready_swing_contract():
    contract = approval_contract_for("swing_one_share_real_canary_phase0", "2026-05-15")

    assert contract["approval_contract_status"] == "contract_missing"
    assert contract["approval_live_ready"] is False
    assert "approval_contract_registry_entry" in contract["missing_components"]


def test_approval_contract_registry_marks_runtime_apply_bridge_contract_states():
    entry = approval_contract_for("entry_wait6579_score66_69_recovery_gate_v1", "2026-05-21")
    scale = approval_contract_for("scale_in_bucket_runtime_policy_v1", "2026-05-21")
    greenfield = approval_contract_for("greenfield_real_environment_authority", "2026-05-21")

    assert entry["approval_contract_status"] == "ready"
    assert entry["approval_mode"] == "live_auto_apply_ready"
    assert entry["approval_live_ready"] is True
    assert entry["approval_artifact_path"].endswith("ldm_entry_runtime_bridge_2026-05-21.json")
    assert entry["missing_components"] == []
    assert scale["approval_contract_status"] == "ready"
    assert scale["approval_live_ready"] is True
    assert scale["approval_artifact_path"].endswith("ldm_scale_in_runtime_bridge_2026-05-21.json")
    assert scale["missing_components"] == []
    assert greenfield["approval_contract_status"] == "ready"
    assert greenfield["approval_live_ready"] is True
    assert greenfield["approval_artifact_path"].endswith("greenfield_real_env_policy_2026-05-21.json")
    assert greenfield["missing_components"] == []


def test_approval_contract_registry_marks_dynamic_formula_as_candidate_grid():
    request = annotate_approval_request({"family": "position_sizing_dynamic_formula"}, "2026-06-10")

    assert request["approval_contract_status"] == "candidate_grid_active_runtime_apply_blocked"
    assert request["approval_mode"] == "candidate_grid_comparison"
    assert request["approval_artifact_required"] is False
    assert request["approval_live_ready"] is False
    assert request["approval_artifact_path"].endswith("position_sizing_dynamic_formula_2026-06-10.json")
