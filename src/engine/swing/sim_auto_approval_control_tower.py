"""Build the unified Swing sim-only auto-approval artifact.

This control-tower artifact can approve only source-only Swing simulation
policy inputs. It has no authority over broker orders, real canaries, runtime
thresholds, providers, bot state, or recommendation_history.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


REPORT_TYPE = "swing_sim_auto_approval"
SCHEMA_VERSION = "swing_sim_auto_approval_v1"
POLICY_ID = "swing_sim_auto_approval"
DECISION_AUTHORITY = "swing_sim_auto_approval_control_tower"

SIM_AUTO_APPROVAL_DIR = Path(DATA_DIR) / "threshold_cycle" / "sim_auto_approvals"
SWING_SIM_POLICY_DIR = Path(DATA_DIR) / "threshold_cycle" / "swing_sim_policies"
SWING_LIFECYCLE_BUCKET_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_bucket_discovery"
BOTTOM_REBOUND_POLICY_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_bottom_rebound_policy_auto_loop"

FORBIDDEN_USES = [
    "broker_order_submit",
    "real_order_enable",
    "one_share_real_canary",
    "scale_in_real_canary",
    "provider_route_change",
    "bot_restart",
    "runtime_threshold_mutation",
    "recommendation_history_replacement",
    "position_cap_release",
]


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def swing_sim_auto_approval_path(target_date: str) -> Path:
    return SIM_AUTO_APPROVAL_DIR / f"{REPORT_TYPE}_{target_date}.json"


def swing_sim_policy_catalog_path(target_date: str) -> Path:
    return SWING_SIM_POLICY_DIR / f"swing_sim_policy_catalog_{target_date}.json"


def swing_lifecycle_bucket_report_path(target_date: str) -> Path:
    return SWING_LIFECYCLE_BUCKET_REPORT_DIR / f"swing_lifecycle_bucket_discovery_{target_date}.json"


def bottom_rebound_policy_report_path(target_date: str) -> Path:
    return BOTTOM_REBOUND_POLICY_REPORT_DIR / f"swing_bottom_rebound_policy_auto_loop_{target_date}.json"


def _source_contract_ok(payload: dict[str, Any], expected_report_type: str) -> bool:
    return (
        payload.get("report_type") == expected_report_type
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
    )


def _swing_ldm_policy_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not _source_contract_ok(report, "swing_lifecycle_bucket_discovery"):
        return []
    items: list[dict[str, Any]] = []
    for candidate in report.get("sim_auto_approved_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        bucket_id = str(candidate.get("bucket_id") or "").strip()
        if not bucket_id:
            continue
        items.append(
            {
                "source_id": "swing_lifecycle_bucket_discovery",
                "policy_kind": "swing_ldm_bucket_sim_policy",
                "bucket_id": bucket_id,
                "lifecycle_stage": candidate.get("lifecycle_stage"),
                "bucket_type": candidate.get("bucket_type"),
                "bucket_key": candidate.get("bucket_key"),
                "source_quality_adjusted_ev_pct": candidate.get("source_quality_adjusted_ev_pct"),
                "classification_state": "sim_auto_approved",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return items


def _bottom_rebound_policy_item(report: dict[str, Any]) -> dict[str, Any] | None:
    if not _source_contract_ok(report, "swing_bottom_rebound_policy_auto_loop"):
        return None
    conclusion = report.get("final_conclusion") if isinstance(report.get("final_conclusion"), dict) else {}
    policy = report.get("sim_auto_approved_policy") if isinstance(report.get("sim_auto_approved_policy"), dict) else {}
    if conclusion.get("classification_state") != "sim_auto_approved" or conclusion.get("promote_policy") is not True:
        return None
    if not policy:
        return None
    return {
        "source_id": "bottom_rebound_policy_auto_loop",
        "policy_kind": "bottom_rebound_candidate_source_policy",
        "policy_version": policy.get("policy_version"),
        "max_candidates": policy.get("max_candidates"),
        "min_backtest_rank_score": policy.get("min_backtest_rank_score"),
        "min_primary_adjusted_ev_pct": policy.get("min_primary_adjusted_ev_pct"),
        "include_bottom_rebound_source": bool(policy.get("include_bottom_rebound_source", True)),
        "classification_state": "sim_auto_approved",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_swing_sim_auto_approval(
    target_date: str,
    *,
    swing_lifecycle_bucket_report: dict[str, Any] | None = None,
    bottom_rebound_policy_report: dict[str, Any] | None = None,
    source_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    paths = source_paths or {
        "swing_lifecycle_bucket_discovery": swing_lifecycle_bucket_report_path(date_key),
        "bottom_rebound_policy_auto_loop": bottom_rebound_policy_report_path(date_key),
    }
    swing_report = (
        swing_lifecycle_bucket_report
        if isinstance(swing_lifecycle_bucket_report, dict)
        else _load_json(paths["swing_lifecycle_bucket_discovery"])
    )
    bottom_report = (
        bottom_rebound_policy_report
        if isinstance(bottom_rebound_policy_report, dict)
        else _load_json(paths["bottom_rebound_policy_auto_loop"])
    )
    policy_items = _swing_ldm_policy_items(swing_report)
    bottom_policy = _bottom_rebound_policy_item(bottom_report)
    if bottom_policy:
        policy_items.append(bottom_policy)
    approved_source_ids = sorted({str(item.get("source_id")) for item in policy_items if item.get("source_id")})
    catalog_path = swing_sim_policy_catalog_path(date_key)
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "policy_id": POLICY_ID,
        "approved": bool(policy_items),
        "human_approval_required": False,
        "runtime_effect": False,
        "source_only": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "decision_authority": DECISION_AUTHORITY,
        "approval_scope": "next_preopen_swing_sim_policy_only",
        "policy_file": str(catalog_path),
        "approved_source_ids": approved_source_ids,
        "approved_policy_count": len(policy_items),
        "approved_policies": policy_items,
        "source_status": {
            "swing_lifecycle_bucket_discovery": {
                "path": str(paths["swing_lifecycle_bucket_discovery"]),
                "present": bool(swing_report),
                "contract_ok": _source_contract_ok(swing_report, "swing_lifecycle_bucket_discovery"),
                "sim_auto_approved_count": len(_swing_ldm_policy_items(swing_report)),
            },
            "bottom_rebound_policy_auto_loop": {
                "path": str(paths["bottom_rebound_policy_auto_loop"]),
                "present": bool(bottom_report),
                "contract_ok": _source_contract_ok(bottom_report, "swing_bottom_rebound_policy_auto_loop"),
                "sim_auto_approved": bottom_policy is not None,
            },
        },
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_policy_catalog(approval: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "swing_sim_policy_catalog_v1",
        "date": approval.get("date"),
        "generated_at": approval.get("generated_at"),
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "approved_source_ids": approval.get("approved_source_ids") or [],
        "policies": approval.get("approved_policies") or [],
        "forbidden_uses": FORBIDDEN_USES,
    }


def write_swing_sim_auto_approval(approval: dict[str, Any]) -> dict[str, Path]:
    date_key = _date_text(approval.get("date"))
    SIM_AUTO_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    SWING_SIM_POLICY_DIR.mkdir(parents=True, exist_ok=True)
    approval_path = swing_sim_auto_approval_path(date_key)
    catalog_path = swing_sim_policy_catalog_path(date_key)
    approval_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    catalog_path.write_text(
        json.dumps(build_policy_catalog(approval), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return {"approval": approval_path, "catalog": catalog_path}


def refresh_swing_sim_auto_approval(
    target_date: str,
    *,
    swing_lifecycle_bucket_report: dict[str, Any] | None = None,
    bottom_rebound_policy_report: dict[str, Any] | None = None,
) -> dict[str, Path]:
    approval = build_swing_sim_auto_approval(
        target_date,
        swing_lifecycle_bucket_report=swing_lifecycle_bucket_report,
        bottom_rebound_policy_report=bottom_rebound_policy_report,
    )
    return write_swing_sim_auto_approval(approval)


def bottom_rebound_is_approved_by_control_tower(approval: dict[str, Any]) -> bool:
    return (
        approval.get("report_type") == REPORT_TYPE
        and approval.get("approved") is True
        and approval.get("runtime_effect") is False
        and approval.get("allowed_runtime_apply") is False
        and approval.get("actual_order_submitted") is False
        and approval.get("broker_order_forbidden") is True
        and "bottom_rebound_policy_auto_loop" in set(approval.get("approved_source_ids") or [])
    )
