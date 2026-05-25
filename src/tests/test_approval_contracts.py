from src.engine.approval_contracts import annotate_approval_request, approval_contract_for


def test_approval_contract_registry_marks_ready_swing_contract():
    contract = approval_contract_for("swing_one_share_real_canary_phase0", "2026-05-15")

    assert contract["approval_contract_status"] == "ready"
    assert contract["approval_mode"] == "auto_approved_real_canary_phase0"
    assert contract["approval_artifact_required"] is False
    assert contract["approval_live_ready"] is True
    assert contract["approval_artifact_path"].endswith("swing_one_share_real_canary_2026-05-15.json")
    assert contract["missing_components"] == []


def test_approval_contract_registry_marks_ready_runtime_apply_bridge_contracts():
    entry = approval_contract_for("entry_wait6579_score66_69_recovery_gate_v1", "2026-05-21")
    scale = approval_contract_for("scale_in_bucket_runtime_policy_v1", "2026-05-21")

    assert entry["approval_contract_status"] == "ready"
    assert entry["approval_live_ready"] is True
    assert entry["approval_artifact_path"].endswith("ldm_entry_runtime_bridge_2026-05-21.json")
    assert entry["missing_components"] == []
    assert scale["approval_contract_status"] == "ready"
    assert scale["approval_live_ready"] is True
    assert scale["approval_artifact_path"].endswith("ldm_scale_in_runtime_bridge_2026-05-21.json")
    assert scale["missing_components"] == []


def test_approval_contract_registry_marks_missing_scalping_manual_contract():
    request = annotate_approval_request({"family": "position_sizing_cap_release"}, "2026-05-15")

    assert request["approval_contract_status"] == "final_user_approval_required"
    assert request["approval_mode"] == "final_user_approval_required"
    assert request["approval_artifact_required"] is True
    assert request["approval_live_ready"] is False
    assert request["approval_artifact_path"].endswith("position_sizing_cap_release_2026-05-15.json")
