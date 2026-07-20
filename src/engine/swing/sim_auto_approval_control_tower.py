"""Build the unified Swing sim-only auto-approval artifact.

This control-tower artifact can approve only source-only Swing simulation
policy inputs. It has no authority over broker orders, real canaries, runtime
thresholds, providers, bot state, or recommendation_history.
"""

from __future__ import annotations

import argparse
import json
import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.auto_promotion_contracts import tier2_validation_passed
from src.utils.constants import DATA_DIR

REPORT_TYPE = "swing_sim_auto_approval"
SCHEMA_VERSION = "swing_sim_auto_approval_v1"
POLICY_ID = "swing_sim_auto_approval"
DECISION_AUTHORITY = "swing_sim_auto_approval_control_tower"

SIM_AUTO_APPROVAL_DIR = Path(DATA_DIR) / "threshold_cycle" / "sim_auto_approvals"
SWING_SIM_POLICY_DIR = Path(DATA_DIR) / "threshold_cycle" / "swing_sim_policies"
LDM_HYPOTHESIS_PLAN_DIR = (
    Path(DATA_DIR) / "threshold_cycle" / "ldm_hypothesis_observation_plans"
)
SWING_LIFECYCLE_BUCKET_REPORT_DIR = (
    Path(DATA_DIR) / "report" / "swing_lifecycle_bucket_discovery"
)
BOTTOM_REBOUND_POLICY_REPORT_DIR = (
    Path(DATA_DIR) / "report" / "swing_bottom_rebound_policy_auto_loop"
)
SWING_RUNTIME_APPROVAL_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_runtime_approval"
SWING_STRATEGY_DISCOVERY_EV_REPORT_DIR = (
    Path(DATA_DIR) / "report" / "swing_strategy_discovery_ev"
)
ACTIVE_ARM_PRIORITY_POLICY_VERSION = "active_swing_arm_priority_v1"

FORBIDDEN_USES = [
    "broker_order_submit",
    "real_order_enable",
    "one_share_real_canary",
    "scale_in_real_canary",
    "provider_route_change",
    "bot_restart",
    "runtime_threshold_mutation",
    "recommendation_history_replacement",
    "sizing_formula_runtime_apply_without_guard",
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


def _latest_hypothesis_observation_plan(target_date: str) -> dict[str, Any]:
    exact = (
        LDM_HYPOTHESIS_PLAN_DIR / f"ldm_hypothesis_observation_plan_{target_date}.json"
    )
    if exact.exists():
        return _load_json(exact)
    candidates: list[tuple[str, Path]] = []
    if LDM_HYPOTHESIS_PLAN_DIR.exists():
        for path in LDM_HYPOTHESIS_PLAN_DIR.glob(
            "ldm_hypothesis_observation_plan_*.json"
        ):
            plan_date = path.stem.removeprefix("ldm_hypothesis_observation_plan_")
            if plan_date <= target_date:
                candidates.append((plan_date, path))
    if not candidates:
        return {}
    return _load_json(sorted(candidates)[-1][1])


def swing_lifecycle_bucket_report_path(target_date: str) -> Path:
    return (
        SWING_LIFECYCLE_BUCKET_REPORT_DIR
        / f"swing_lifecycle_bucket_discovery_{target_date}.json"
    )


def bottom_rebound_policy_report_path(target_date: str) -> Path:
    return (
        BOTTOM_REBOUND_POLICY_REPORT_DIR
        / f"swing_bottom_rebound_policy_auto_loop_{target_date}.json"
    )


def swing_runtime_approval_report_path(target_date: str) -> Path:
    return (
        SWING_RUNTIME_APPROVAL_REPORT_DIR / f"swing_runtime_approval_{target_date}.json"
    )


def swing_strategy_discovery_ev_report_path(target_date: str) -> Path:
    return (
        SWING_STRATEGY_DISCOVERY_EV_REPORT_DIR
        / f"swing_strategy_discovery_ev_{target_date}.json"
    )


def _source_contract_ok(payload: dict[str, Any], expected_report_type: str) -> bool:
    return (
        payload.get("report_type") == expected_report_type
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
    )


def _previous_active_arm_policies(target_date: str) -> dict[str, dict[str, Any]]:
    previous: dict[str, dict[str, Any]] = {}
    for path in sorted(
        SWING_SIM_POLICY_DIR.glob("swing_sim_policy_catalog_*.json"), reverse=True
    ):
        if target_date and target_date in path.name:
            continue
        payload = _load_json(path)
        policies = (
            payload.get("active_arm_priority_policies")
            if isinstance(payload, dict)
            else []
        )
        if not isinstance(policies, list):
            continue
        for item in policies:
            if not isinstance(item, dict):
                continue
            key = str(
                item.get("priority_arm_id") or item.get("priority_bucket_id") or ""
            ).strip()
            if key and key not in previous:
                previous[key] = item
        if previous:
            break
    return previous


def _priority_policy_id(priority_key: str, source_report_date: str) -> str:
    raw = json.dumps(
        {
            "priority_key": priority_key,
            "source_report_date": source_report_date,
            "policy_version": ACTIVE_ARM_PRIORITY_POLICY_VERSION,
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return "active_arm_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _active_arm_priority_policies(
    report: dict[str, Any],
    target_date: str,
    *,
    swing_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    previous = _previous_active_arm_policies(target_date)
    seen: set[str] = set()
    policies: list[dict[str, Any]] = []
    ev_source_date = str(report.get("date") or target_date)
    if report.get("report_type") == "swing_strategy_discovery_ev":
        for arm in report.get("surviving_arms") or []:
            if not isinstance(arm, dict):
                continue
            arm_id = str(arm.get("arm_id") or "").strip()
            if not arm_id:
                continue
            seen.add(arm_id)
            ev = arm.get("source_quality_adjusted_ev_pct")
            sample = arm.get("sample_count")
            policies.append(
                {
                    "priority_policy_id": _priority_policy_id(arm_id, ev_source_date),
                    "priority_arm_id": arm_id,
                    "policy_version": ACTIVE_ARM_PRIORITY_POLICY_VERSION,
                    "source_id": "swing_strategy_discovery_ev",
                    "source_report_date": ev_source_date,
                    "priority_source": "surviving_arms",
                    "status": "active",
                    "source_quality_adjusted_ev_pct": ev,
                    "sample_count": sample,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": FORBIDDEN_USES,
                }
            )
    swing_source_date = str((swing_report or {}).get("date") or target_date)
    if _source_contract_ok(swing_report or {}, "swing_lifecycle_bucket_discovery"):
        for candidate in (swing_report or {}).get("sim_auto_approved_candidates") or []:
            if not isinstance(candidate, dict):
                continue
            bucket_id = str(candidate.get("bucket_id") or "").strip()
            if not bucket_id:
                continue
            priority_key = f"bucket:{bucket_id}"
            seen.add(priority_key)
            policies.append(
                {
                    "priority_policy_id": _priority_policy_id(
                        priority_key, swing_source_date
                    ),
                    "priority_bucket_id": bucket_id,
                    "policy_version": ACTIVE_ARM_PRIORITY_POLICY_VERSION,
                    "source_id": "swing_lifecycle_bucket_discovery",
                    "source_report_date": swing_source_date,
                    "priority_source": "sim_auto_approved_candidates",
                    "status": "active",
                    "lifecycle_stage": candidate.get("lifecycle_stage"),
                    "bucket_type": candidate.get("bucket_type"),
                    "bucket_key": candidate.get("bucket_key"),
                    "source_quality_adjusted_ev_pct": candidate.get(
                        "source_quality_adjusted_ev_pct"
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": FORBIDDEN_USES,
                }
            )
    for priority_key, old in previous.items():
        old_key = str(
            old.get("priority_arm_id") or old.get("priority_bucket_id") or priority_key
        ).strip()
        if old_key in seen or f"bucket:{old_key}" in seen:
            continue
        missing = int(old.get("consecutive_missing_count") or 0) + 1
        old_status = str(old.get("status") or "").strip()
        status = (
            "retired"
            if old_status == "retired" or missing >= 5
            else "cooldown" if old_status == "cooldown" or missing >= 2 else "active"
        )
        policies.append(
            {
                **old,
                "status": status,
                "consecutive_missing_count": missing,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "retired_reason": (
                    "consecutive_missing"
                    if status == "retired"
                    else str(old.get("retired_reason") or "")
                ),
            }
        )
    return sorted(
        policies,
        key=lambda item: (
            {"active": 0, "cooldown": 1, "retired": 2}.get(
                str(item.get("status") or ""), 9
            ),
            str(item.get("priority_arm_id") or item.get("priority_bucket_id") or ""),
        ),
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
                "source_quality_adjusted_ev_pct": candidate.get(
                    "source_quality_adjusted_ev_pct"
                ),
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
    conclusion = (
        report.get("final_conclusion")
        if isinstance(report.get("final_conclusion"), dict)
        else {}
    )
    policy = (
        report.get("sim_auto_approved_policy")
        if isinstance(report.get("sim_auto_approved_policy"), dict)
        else {}
    )
    if (
        conclusion.get("classification_state") != "sim_auto_approved"
        or conclusion.get("promote_policy") is not True
    ):
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
        "include_bottom_rebound_source": bool(
            policy.get("include_bottom_rebound_source", True)
        ),
        "classification_state": "sim_auto_approved",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _request_tier2_passed(request: dict[str, Any]) -> bool:
    contract = request.get("auto_promotion_contract")
    if not isinstance(contract, dict):
        return False
    return tier2_validation_passed(contract.get("tier2_status"))


def _swing_runtime_pre_final_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("report_type") != "swing_runtime_approval":
        return []
    items: list[dict[str, Any]] = []
    for request in report.get("approval_requests") or []:
        if not isinstance(request, dict):
            continue
        if not _request_tier2_passed(request):
            continue
        state = str(request.get("calibration_state") or "")
        auto_state = str(request.get("auto_approval_state") or "")
        family = str(request.get("family") or request.get("policy_id") or "")
        if (
            state == "dry_run_auto_apply_ready"
            and auto_state == "ai_tier2_auto_approved"
        ):
            policy_kind = "swing_runtime_dry_run_pre_final_policy"
        else:
            continue
        items.append(
            {
                "source_id": "swing_runtime_approval",
                "policy_kind": policy_kind,
                "approval_id": request.get("approval_id"),
                "family": family,
                "stage": request.get("stage"),
                "classification_state": state,
                "auto_approval_state": request.get("auto_approval_state"),
                "tradeoff_score": request.get("tradeoff_score"),
                "sample_count": request.get("sample_count"),
                "sample_floor": request.get("sample_floor"),
                "auto_promotion_contract": request.get("auto_promotion_contract") or {},
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return items


def build_swing_sim_auto_approval(
    target_date: str,
    *,
    swing_lifecycle_bucket_report: dict[str, Any] | None = None,
    bottom_rebound_policy_report: dict[str, Any] | None = None,
    swing_runtime_approval_report: dict[str, Any] | None = None,
    swing_strategy_discovery_ev_report: dict[str, Any] | None = None,
    source_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    default_paths = {
        "swing_lifecycle_bucket_discovery": swing_lifecycle_bucket_report_path(
            date_key
        ),
        "bottom_rebound_policy_auto_loop": bottom_rebound_policy_report_path(date_key),
        "swing_runtime_approval": swing_runtime_approval_report_path(date_key),
        "swing_strategy_discovery_ev": swing_strategy_discovery_ev_report_path(
            date_key
        ),
    }
    paths = {**default_paths, **(source_paths or {})}
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
    runtime_report = (
        swing_runtime_approval_report
        if isinstance(swing_runtime_approval_report, dict)
        else _load_json(paths["swing_runtime_approval"])
    )
    discovery_ev_report = (
        swing_strategy_discovery_ev_report
        if isinstance(swing_strategy_discovery_ev_report, dict)
        else _load_json(paths["swing_strategy_discovery_ev"])
    )
    policy_items = _swing_ldm_policy_items(swing_report)
    bottom_policy = _bottom_rebound_policy_item(bottom_report)
    if bottom_policy:
        policy_items.append(bottom_policy)
    policy_items.extend(_swing_runtime_pre_final_items(runtime_report))
    active_arm_policies = _active_arm_priority_policies(
        discovery_ev_report,
        date_key,
        swing_report=swing_report,
    )
    approved_source_ids = sorted(
        {
            str(item.get("source_id"))
            for item in [*policy_items, *active_arm_policies]
            if item.get("source_id")
        }
    )
    catalog_path = swing_sim_policy_catalog_path(date_key)
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "policy_id": POLICY_ID,
        "approved": bool(policy_items or active_arm_policies),
        "human_approval_required": False,
        "runtime_effect": False,
        "source_only": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "decision_authority": DECISION_AUTHORITY,
        "approval_scope": "next_preopen_swing_pre_final_auto_policy",
        "final_user_approval_boundary": "full_live_only",
        "tier2_policy": "fail_closed",
        "policy_file": str(catalog_path),
        "approved_source_ids": approved_source_ids,
        "approved_policy_count": len(policy_items),
        "approved_policies": policy_items,
        "active_arm_priority_policies": active_arm_policies,
        "active_arm_priority_policy_count": len(active_arm_policies),
        "source_status": {
            "swing_lifecycle_bucket_discovery": {
                "path": str(paths["swing_lifecycle_bucket_discovery"]),
                "present": bool(swing_report),
                "contract_ok": _source_contract_ok(
                    swing_report, "swing_lifecycle_bucket_discovery"
                ),
                "sim_auto_approved_count": len(_swing_ldm_policy_items(swing_report)),
            },
            "bottom_rebound_policy_auto_loop": {
                "path": str(paths["bottom_rebound_policy_auto_loop"]),
                "present": bool(bottom_report),
                "contract_ok": _source_contract_ok(
                    bottom_report, "swing_bottom_rebound_policy_auto_loop"
                ),
                "sim_auto_approved": bottom_policy is not None,
            },
            "swing_runtime_approval": {
                "path": str(paths["swing_runtime_approval"]),
                "present": bool(runtime_report),
                "pre_final_auto_policy_count": len(
                    _swing_runtime_pre_final_items(runtime_report)
                ),
            },
            "swing_strategy_discovery_ev": {
                "path": str(paths["swing_strategy_discovery_ev"]),
                "present": bool(discovery_ev_report),
                "active_arm_priority_policy_count": len(active_arm_policies),
            },
        },
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_policy_catalog(approval: dict[str, Any]) -> dict[str, Any]:
    target_date = _date_text(approval.get("date"))
    hypothesis_plan = _latest_hypothesis_observation_plan(target_date)
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
        "active_arm_priority_policies": approval.get("active_arm_priority_policies")
        or [],
        "active_priority_lineage": {
            "source": "swing_sim_auto_approval",
            "active_arm_priority_policy_count": len(
                approval.get("active_arm_priority_policies") or []
            ),
            "lineage_artifact": f"data/report/key_lineage_ledger/key_lineage_ledger_{target_date}.json",
        },
        "hypothesis_observation_plan": hypothesis_plan or {},
        "forbidden_uses": FORBIDDEN_USES,
    }


def write_swing_sim_auto_approval(approval: dict[str, Any]) -> dict[str, Path]:
    date_key = _date_text(approval.get("date"))
    SIM_AUTO_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    SWING_SIM_POLICY_DIR.mkdir(parents=True, exist_ok=True)
    approval_path = swing_sim_auto_approval_path(date_key)
    catalog_path = swing_sim_policy_catalog_path(date_key)
    approval_path.write_text(
        json.dumps(approval, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    catalog_path.write_text(
        json.dumps(
            build_policy_catalog(approval), ensure_ascii=False, indent=2, default=str
        ),
        encoding="utf-8",
    )
    return {"approval": approval_path, "catalog": catalog_path}


def refresh_swing_sim_auto_approval(
    target_date: str,
    *,
    swing_lifecycle_bucket_report: dict[str, Any] | None = None,
    bottom_rebound_policy_report: dict[str, Any] | None = None,
    swing_runtime_approval_report: dict[str, Any] | None = None,
    swing_strategy_discovery_ev_report: dict[str, Any] | None = None,
) -> dict[str, Path]:
    approval = build_swing_sim_auto_approval(
        target_date,
        swing_lifecycle_bucket_report=swing_lifecycle_bucket_report,
        bottom_rebound_policy_report=bottom_rebound_policy_report,
        swing_runtime_approval_report=swing_runtime_approval_report,
        swing_strategy_discovery_ev_report=swing_strategy_discovery_ev_report,
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
        and "bottom_rebound_policy_auto_loop"
        in set(approval.get("approved_source_ids") or [])
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Swing sim-only auto-approval artifact"
    )
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    paths = refresh_swing_sim_auto_approval(args.date)
    print(
        json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
