"""Approval artifact readiness registry for runtime-changing requests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"


_CONTRACTS: dict[str, dict[str, Any]] = {
    "swing_model_floor": {
        "approval_contract_status": "ready",
        "approval_mode": "ai_tier2_pre_final_auto",
        "approval_artifact_required": False,
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_selection_top_k": {
        "approval_contract_status": "ready",
        "approval_mode": "ai_tier2_pre_final_auto",
        "approval_artifact_required": False,
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_gatekeeper_reject_cooldown": {
        "approval_contract_status": "ready",
        "approval_mode": "ai_tier2_pre_final_auto",
        "approval_artifact_required": False,
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_market_regime_sensitivity": {
        "approval_contract_status": "ready",
        "approval_mode": "ai_tier2_pre_final_auto",
        "approval_artifact_required": False,
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "entry_wait6579_score66_69_recovery_gate_v1": {
        "approval_contract_status": "legacy_entry_bridge_metadata",
        "approval_mode": "entry_only_bridge_metadata",
        "approval_artifact_required": False,
        "approval_artifact_template": "ldm_entry_runtime_bridge_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.runtime_apply_bridge_metadata",
        "preopen_env_ready": False,
        "runtime_guard_ready": False,
        "runtime_scope": "entry_dimension_provenance_only",
        "missing_components": [
            "not_complete_lifecycle_bucket",
            "not_live_apply_candidate",
        ],
    },
    "scale_in_bucket_runtime_policy_v1": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "ldm_scale_in_runtime_bridge_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.runtime_apply_bridge_live_auto",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "live_auto_scalp_scale_in_policy_env_only",
    },
    "greenfield_real_environment_authority": {
        "approval_contract_status": "ready",
        "approval_mode": "live_auto_apply_ready",
        "approval_artifact_required": False,
        "approval_artifact_template": "greenfield_real_env_policy_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.runtime_apply_bridge_live_auto",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "full_lifecycle_promoted_bucket_real_environment_only",
        "missing_components": [],
    },
    "position_sizing_dynamic_formula": {
        "approval_contract_status": "candidate_grid_active_runtime_apply_blocked",
        "approval_mode": "candidate_grid_comparison",
        "approval_artifact_required": False,
        "approval_artifact_template": "position_sizing_dynamic_formula_{date}.json",
        "approval_artifact_consumer": None,
        "preopen_env_ready": False,
        "runtime_guard_ready": False,
        "runtime_scope": "candidate_grid_comparison_only_runtime_apply_blocked",
        "missing_components": [
            "preopen_env_mapping",
            "runtime_formula_guard",
            "approval_preopen_guard_tests",
        ],
    },
    "panic_entry_freeze_guard": {
        "approval_contract_status": "contract_missing",
        "approval_artifact_template": "panic_entry_freeze_guard_{date}.json",
        "approval_artifact_consumer": None,
        "preopen_env_ready": False,
        "runtime_guard_ready": False,
        "runtime_scope": "not_live_ready",
        "missing_components": [
            "approval_artifact_loader",
            "preopen_env_mapping",
            "entry_pre_submit_runtime_guard",
            "rollback_tests",
        ],
    },
    "panic_buy_runner_tp_canary": {
        "approval_contract_status": "contract_missing",
        "approval_artifact_template": "panic_buy_runner_tp_canary_{date}.json",
        "approval_artifact_consumer": None,
        "preopen_env_ready": False,
        "runtime_guard_ready": False,
        "runtime_scope": "not_live_ready",
        "missing_components": [
            "approval_artifact_loader",
            "preopen_env_mapping",
            "tp_runner_runtime_guard",
            "rollback_tests",
        ],
    },
}


def approval_contract_for(family: str, source_date: str | None = None) -> dict[str, Any]:
    family_key = str(family or "").strip()
    source_date = str(source_date or "YYYY-MM-DD").strip() or "YYYY-MM-DD"
    contract = dict(_CONTRACTS.get(family_key) or {})
    if not contract:
        contract = {
            "approval_contract_status": "contract_missing",
            "approval_artifact_template": f"{family_key or 'unknown'}_{{date}}.json",
            "approval_artifact_consumer": None,
            "preopen_env_ready": False,
            "runtime_guard_ready": False,
            "runtime_scope": "not_live_ready",
            "missing_components": [
                "approval_contract_registry_entry",
                "approval_artifact_loader",
                "preopen_env_mapping",
                "runtime_guard",
                "rollback_tests",
            ],
        }
    template = str(contract.get("approval_artifact_template") or f"{family_key}_{{date}}.json")
    contract["family"] = family_key
    contract["approval_artifact_path"] = str(APPROVAL_DIR / template.format(date=source_date))
    contract["approval_artifact_exists"] = Path(contract["approval_artifact_path"]).exists()
    contract["approval_live_ready"] = (
        contract.get("approval_contract_status") == "ready"
        and bool(contract.get("preopen_env_ready"))
        and bool(contract.get("runtime_guard_ready"))
    )
    contract.setdefault("missing_components", [])
    return contract


def annotate_approval_request(request: dict[str, Any], source_date: str | None = None) -> dict[str, Any]:
    family = str(request.get("family") or request.get("policy_id") or "").strip()
    contract = approval_contract_for(family, source_date)
    return {
        **request,
        "approval_contract_status": contract.get("approval_contract_status"),
        "approval_mode": contract.get("approval_mode") or "artifact_required",
        "approval_artifact_required": bool(contract.get("approval_artifact_required", True)),
        "approval_live_ready": bool(contract.get("approval_live_ready")),
        "approval_artifact_path": contract.get("approval_artifact_path"),
        "approval_artifact_consumer": contract.get("approval_artifact_consumer"),
        "approval_contract_missing_components": contract.get("missing_components") or [],
        "approval_runtime_scope": contract.get("runtime_scope"),
    }
