from src.engine.approval_contracts import (
    annotate_approval_request,
    approval_contract_for,
)


def test_approval_contract_registry_marks_ready_swing_contract():
    contract = approval_contract_for("swing_one_share_real_canary_phase0", "2026-05-15")

    assert contract["approval_contract_status"] == "contract_missing"
    assert contract["approval_live_ready"] is False
    assert "approval_contract_registry_entry" in contract["missing_components"]


def test_approval_contract_registry_marks_runtime_apply_bridge_contract_states():
    retired_entry = approval_contract_for(
        "entry_wait6579_score66_69_recovery_gate_v1", "2026-05-21"
    )
    scale = approval_contract_for("scale_in_bucket_runtime_policy_v1", "2026-05-21")
    greenfield = approval_contract_for(
        "greenfield_real_environment_authority", "2026-05-21"
    )

    assert retired_entry["approval_contract_status"] == "contract_missing"
    assert retired_entry["approval_live_ready"] is False
    assert "approval_contract_registry_entry" in retired_entry["missing_components"]
    assert retired_entry["approval_artifact_consumer"] is None
    assert scale["approval_contract_status"] == "ready"
    assert scale["approval_live_ready"] is True
    assert scale["approval_artifact_path"].endswith(
        "ldm_scale_in_runtime_bridge_2026-05-21.json"
    )
    assert scale["missing_components"] == []
    assert greenfield["approval_contract_status"] == "ready"
    assert greenfield["approval_live_ready"] is True
    assert greenfield["approval_artifact_path"].endswith(
        "greenfield_real_env_policy_2026-05-21.json"
    )
    assert greenfield["missing_components"] == []


def test_annotate_approval_request_does_not_restore_retired_entry_bridge():
    request = annotate_approval_request(
        {"family": "entry_wait6579_score66_69_recovery_gate_v1"},
        "2026-05-21",
    )

    assert request["approval_contract_status"] == "contract_missing"
    assert request["approval_mode"] == "artifact_required"
    assert request["approval_live_ready"] is False
    assert (
        "approval_contract_registry_entry"
        in request["approval_contract_missing_components"]
    )
    assert request["approval_artifact_consumer"] is None


def test_approval_contract_registry_marks_dynamic_formula_as_not_runtime_reflected():
    request = annotate_approval_request(
        {"family": "position_sizing_dynamic_formula"}, "2026-06-10"
    )

    assert request["approval_contract_status"] == "implemented_not_runtime_reflected"
    assert request["approval_mode"] == (
        "selected_formula_with_flat10_report_comparison"
    )
    assert request["approval_artifact_required"] is False
    assert request["approval_live_ready"] is False
    assert request["approval_artifact_path"].endswith(
        "position_sizing_dynamic_formula_2026-06-10.json"
    )
    assert request["approval_contract_missing_components"] == [
        "current_process_restart_not_authorized"
    ]
