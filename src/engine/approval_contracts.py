"""Approval artifact readiness registry for runtime-changing requests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"


_CONTRACTS: dict[str, dict[str, Any]] = {
    "swing_model_floor": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_selection_top_k": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_gatekeeper_reject_cooldown": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_market_regime_sensitivity": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "swing_runtime_approvals_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_runtime_approvals",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "swing_dry_run_env_only",
    },
    "swing_one_share_real_canary_phase0": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "swing_one_share_real_canary_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_one_share_real_canary",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "approved_one_share_buy_and_closing_sell_only",
    },
    "swing_scale_in_real_canary_phase0": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "swing_scale_in_real_canary_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.swing_scale_in_real_canary",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "approved_real_holding_scale_in_only",
    },
    "entry_wait6579_score66_69_recovery_gate_v1": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "ldm_entry_runtime_bridge_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.runtime_apply_bridge_live_auto",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "live_auto_entry_wait6579_score66_69_recovery_gate_only",
    },
    "scale_in_bucket_runtime_policy_v1": {
        "approval_contract_status": "ready",
        "approval_artifact_template": "ldm_scale_in_runtime_bridge_{date}.json",
        "approval_artifact_consumer": "threshold_cycle_preopen_apply.runtime_apply_bridge_live_auto",
        "preopen_env_ready": True,
        "runtime_guard_ready": True,
        "runtime_scope": "live_auto_scalp_scale_in_policy_env_only",
    },
    "position_sizing_cap_release": {
        "approval_contract_status": "contract_missing",
        "approval_artifact_template": "position_sizing_cap_release_{date}.json",
        "approval_artifact_consumer": None,
        "preopen_env_ready": False,
        "runtime_guard_ready": False,
        "runtime_scope": "not_live_ready",
        "missing_components": [
            "approval_artifact_loader",
            "preopen_env_mapping",
            "runtime_qty_cap_release_guard",
            "rollback_tests",
        ],
    },
    "position_sizing_dynamic_formula": {
        "approval_contract_status": "contract_missing",
        "approval_artifact_template": "position_sizing_dynamic_formula_{date}.json",
        "approval_artifact_consumer": None,
        "preopen_env_ready": False,
        "runtime_guard_ready": False,
        "runtime_scope": "not_live_ready",
        "missing_components": [
            "approval_artifact_loader",
            "preopen_env_mapping",
            "runtime_formula_guard",
            "rollback_tests",
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
        "approval_live_ready": bool(contract.get("approval_live_ready")),
        "approval_artifact_path": contract.get("approval_artifact_path"),
        "approval_artifact_consumer": contract.get("approval_artifact_consumer"),
        "approval_contract_missing_components": contract.get("missing_components") or [],
        "approval_runtime_scope": contract.get("runtime_scope"),
    }
