"""Build runtime-apply bridge candidates from LDM bucket attribution.

The bridge now consumes lifecycle bucket discovery policy: entry/scale-in bridge
families are auto-applied when source-quality and safety contracts are closed.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.auto_promotion_contracts import primary_ev_uplift_passes, tier2_validation_passed
from src.utils.constants import DATA_DIR
from src.engine.lifecycle_bucket_discovery import (
    ENTRY_LIVE_AUTO_FAMILY,
    ENTRY_LIVE_AUTO_BUCKET_KEY,
    EVIDENCE_GRADE_2_COUNTERFACTUAL,
    SCALE_IN_LIVE_AUTO_FAMILY,
    discovery_report_path,
)
from src.engine.lifecycle.greenfield_authority import validate_greenfield_policy_contract


REPORT_DIR = DATA_DIR / "report" / "runtime_apply_bridge"
LDM_REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"
GREENFIELD_POLICY_DIR = DATA_DIR / "threshold_cycle" / "greenfield_real_env_policies"

ENTRY_BRIDGE_FAMILY = ENTRY_LIVE_AUTO_FAMILY
SCALE_IN_BRIDGE_FAMILY = SCALE_IN_LIVE_AUTO_FAMILY
GREENFIELD_REAL_ENV_FAMILY = "greenfield_real_environment_authority"

ENTRY_TARGET_BUCKET_KEY = ENTRY_LIVE_AUTO_BUCKET_KEY
ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES: set[str] = set()


def runtime_apply_bridge_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_bridge_{target_date}.json"


def runtime_apply_bridge_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_bridge_{target_date}.md"


def ldm_entry_runtime_bridge_artifact_path(source_date: str) -> Path:
    return APPROVAL_DIR / f"ldm_entry_runtime_bridge_{source_date}.json"


def ldm_scale_in_runtime_bridge_artifact_path(source_date: str) -> Path:
    return APPROVAL_DIR / f"ldm_scale_in_runtime_bridge_{source_date}.json"


def greenfield_real_env_policy_path(source_date: str) -> Path:
    return GREENFIELD_POLICY_DIR / f"greenfield_real_env_policy_{source_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def validate_greenfield_policy_payload(policy: dict[str, Any], *, expected_version: str | None = None) -> str:
    if not policy:
        return "greenfield_policy_file_invalid"
    if str(policy.get("policy_id") or "") != GREENFIELD_REAL_ENV_FAMILY:
        return "greenfield_policy_id_mismatch"
    return validate_greenfield_policy_contract(policy, expected_version=expected_version)


def validate_greenfield_policy_file(policy_file: str, *, expected_version: str | None = None) -> str:
    policy_file = str(policy_file or "").strip()
    if not policy_file:
        return "greenfield_policy_file_missing"
    policy_path = Path(policy_file)
    if not policy_path.exists():
        return "greenfield_policy_file_missing"
    return validate_greenfield_policy_payload(_load_json(policy_path), expected_version=expected_version)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_slug(value: Any) -> str:
    return str(value or "").strip().replace("/", "_")


def _missing_source_fields(bucket: dict[str, Any]) -> list[str]:
    coverage = bucket.get("source_field_coverage") if isinstance(bucket.get("source_field_coverage"), dict) else {}
    missing: list[str] = []
    for field, meta in coverage.items():
        if not isinstance(meta, dict):
            continue
        sample_count = _safe_int(meta.get("sample_count"), 0)
        present_count = _safe_int(meta.get("present_count"), 0)
        if sample_count > 0 and present_count <= 0:
            missing.append(str(field))
    return sorted(missing)


def _ldm_report_path(target_date: str, *, suffix: str | None = None) -> Path:
    suffix_part = f"_{_safe_slug(suffix)}" if suffix else ""
    return LDM_REPORT_DIR / f"lifecycle_decision_matrix_{target_date}{suffix_part}.json"


def _discovery_report_path(target_date: str, *, suffix: str | None = None) -> Path:
    if not suffix:
        return discovery_report_path(target_date)
    base = discovery_report_path(target_date)
    return base.parent / f"lifecycle_bucket_discovery_{target_date}_{_safe_slug(suffix)}.json"


def _history_reports(target_date: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in sorted(LDM_REPORT_DIR.glob("lifecycle_decision_matrix_*.json")):
        report_date = path.stem.removeprefix("lifecycle_decision_matrix_")
        if "_" in report_date:
            continue
        if report_date >= target_date:
            continue
        payload = _load_json(path)
        if payload:
            reports.append(payload)
    return reports[-5:]


def _find_bucket(payload: dict[str, Any], section: str, bucket_type: str, bucket_key: str) -> dict[str, Any]:
    buckets = (
        payload.get(section, {}).get("buckets", [])
        if isinstance(payload.get(section), dict)
        else []
    )
    for item in buckets:
        if not isinstance(item, dict):
            continue
        if str(item.get("bucket_type") or "") == bucket_type and str(item.get("bucket_key") or "") == bucket_key:
            return item
    return {}


def _state_for_bucket(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    section: str,
    bucket_type: str,
    bucket_key: str,
    positive_edge: bool,
) -> tuple[str, dict[str, Any]]:
    if not current or str(current.get("source_quality_gate") or "") != "pass":
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    route = str(current.get("recommended_route") or "")
    expected_route = "candidate_recovery_or_relax" if positive_edge else "candidate_tighten_or_exclude"
    if route != expected_route:
        return "blocked_source_quality", {
            "confirmation_count": 0,
            "conflict_count": 0,
            "blocked_route": route or "missing",
            "expected_route": expected_route,
        }
    current_ev = _safe_float(current.get("source_quality_adjusted_ev_pct"), 0.0) or 0.0
    if positive_edge and current_ev <= 0:
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    if (not positive_edge) and current_ev >= 0:
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    if not primary_ev_uplift_passes(current_ev, positive_edge=positive_edge):
        return "hold_no_edge", {
            "confirmation_count": 0,
            "conflict_count": 0,
            "primary_ev_uplift_floor_passed": False,
            "primary_ev_uplift_threshold_pct": 1.0,
            "runtime_bridge_exclusion_reason": "primary_ev_uplift_below_live_floor",
        }

    confirmations = 0
    conflicts = 0
    for payload in history:
        bucket = _find_bucket(payload, section, bucket_type, bucket_key)
        if not bucket or str(bucket.get("source_quality_gate") or "") != "pass":
            continue
        ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"), None)
        if ev is None:
            continue
        if primary_ev_uplift_passes(ev, positive_edge=positive_edge):
            confirmations += 1
        else:
            conflicts += 1
    meta = {"confirmation_count": confirmations, "conflict_count": conflicts}
    if conflicts:
        return "blocked_rolling_conflict", meta
    meta["daily_only_auto_apply"] = confirmations <= 0
    return "live_auto_apply_ready", meta


def _discovery_live_families(discovery: dict[str, Any]) -> set[str]:
    return {
        str(item.get("live_auto_apply_family"))
        for item in (
            discovery.get("live_auto_apply_candidates")
            if isinstance(discovery.get("live_auto_apply_candidates"), list)
            else []
        )
        if _discovery_live_candidate_contract_passed(item)
    }


def _discovery_candidate_tier2_passed(item: dict[str, Any]) -> bool:
    contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
    status = (
        item.get("ai_review_status")
        or item.get("lifecycle_bucket_discovery_ai_review_status")
        or contract.get("tier2_status")
    )
    return tier2_validation_passed(status)


def _discovery_live_candidate_contract_passed(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    family = str(item.get("live_auto_apply_family") or "")
    if not family or family in ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES:
        return False
    if str(item.get("classification_state") or "") != "live_auto_apply_ready":
        return False
    if item.get("allowed_runtime_apply") is False:
        return False
    if item.get("broker_order_forbidden") is True:
        return False
    if str(item.get("source_quality_gate") or "pass") != "pass":
        return False
    return _discovery_candidate_tier2_passed(item)


def _greenfield_parent_policy_contract_passed(item: Any) -> bool:
    if not _discovery_live_candidate_contract_passed(item):
        return False
    if not isinstance(item, dict):
        return False
    if str(item.get("live_auto_apply_family") or "") != GREENFIELD_REAL_ENV_FAMILY:
        return False
    if str(item.get("stage") or "") != "lifecycle_flow":
        return False
    if str(item.get("bucket_type") or "") != "combo_lifecycle_flow":
        return False
    policy_bucket_id = str(item.get("policy_bucket_id") or item.get("canonical_parent_bucket") or "")
    if not policy_bucket_id:
        return False
    if item.get("parent_live_floor_passed") is not True:
        return False
    if _safe_int(item.get("parent_joined_sample")) < 10:
        return False
    if str(item.get("parent_granularity_status") or "") != "target_pass":
        return False
    return True


def _candidate_policy_bucket_id(item: dict[str, Any]) -> str:
    return str(item.get("policy_bucket_id") or item.get("canonical_parent_bucket") or item.get("parent_bucket_id") or item.get("bucket_id") or "")


def _greenfield_parent_confirmation(
    selected_flow: dict[str, Any],
    confirmation_discoveries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    policy_bucket_id = _candidate_policy_bucket_id(selected_flow)
    promotion_ev = _safe_float(
        selected_flow.get("parent_source_quality_adjusted_ev_pct")
        or selected_flow.get("parent_ev")
        or selected_flow.get("source_quality_adjusted_ev_pct"),
        None,
    )
    expected_positive = promotion_ev is None or promotion_ev >= 0
    windows: dict[str, dict[str, Any]] = {}
    passed = False
    for suffix, discovery in confirmation_discoveries.items():
        summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
        item_status = {
            "available": bool(discovery),
            "source_contract_status": summary.get("source_contract_status"),
            "parent_granularity_status": summary.get("parent_granularity_status"),
            "ai_two_pass_review_status": summary.get("ai_two_pass_review_status"),
            "same_parent_found": False,
            "same_direction": False,
            "matched_parent_ev": None,
        }
        if not discovery or not policy_bucket_id:
            windows[suffix] = item_status
            continue
        if (
            str(summary.get("source_contract_status") or "") != "pass"
            or str(summary.get("parent_granularity_status") or "") != "target_pass"
        ):
            windows[suffix] = item_status
            continue
        for candidate in discovery.get("live_auto_apply_candidates") or []:
            if not isinstance(candidate, dict) or not _greenfield_parent_policy_contract_passed(candidate):
                continue
            if _candidate_policy_bucket_id(candidate) == policy_bucket_id:
                item_status["same_parent_found"] = True
                item_status["same_direction"] = True
                passed = True
                break
        if not item_status["same_direction"]:
            for parent in discovery.get("parent_bucket_summaries") or []:
                if not isinstance(parent, dict):
                    continue
                if str(parent.get("parent_bucket_id") or "") != policy_bucket_id:
                    continue
                item_status["same_parent_found"] = True
                ev = _safe_float(
                    parent.get("parent_source_quality_adjusted_ev_pct") or parent.get("parent_ev"),
                    None,
                )
                item_status["matched_parent_ev"] = ev
                same_direction = ev is not None and ((ev >= 0) if expected_positive else (ev <= 0))
                item_status["same_direction"] = same_direction
                if same_direction:
                    passed = True
                break
        windows[suffix] = item_status
    return {
        "policy_bucket_id": policy_bucket_id,
        "promotion_ev": promotion_ev,
        "expected_direction": "positive" if expected_positive else "negative",
        "passed": passed,
        "windows": windows,
    }


def _discovery_live_candidate_by_family(discovery: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = (
        discovery.get("live_auto_apply_candidates")
        if isinstance(discovery.get("live_auto_apply_candidates"), list)
        else []
    )
    by_family: dict[str, dict[str, Any]] = {}
    for item in candidates:
        if not _discovery_live_candidate_contract_passed(item):
            continue
        family = str(item.get("live_auto_apply_family") or "")
        if family not in by_family:
            by_family[family] = item
    return by_family


def _discovery_window_context(target_date: str) -> dict[str, Any]:
    daily_path = _discovery_report_path(target_date)
    promotion_suffix = (
        os.getenv("THRESHOLD_CYCLE_LIFECYCLE_BUCKET_PROMOTION_WINDOW", "mtd").strip()
        or "mtd"
    )
    configured_windows = [
        item.strip()
        for item in os.getenv("THRESHOLD_CYCLE_LIFECYCLE_BUCKET_WINDOWS", "rolling5d,rolling10d,mtd").split(",")
        if item.strip()
    ]
    confirmation_suffixes = [item for item in configured_windows if item != promotion_suffix]
    if not confirmation_suffixes:
        confirmation_suffixes = ["rolling5d", "rolling10d"]
    promotion_path = _discovery_report_path(target_date, suffix=promotion_suffix)
    daily = _load_json(daily_path)
    promotion = _load_json(promotion_path)
    confirmation = {
        suffix: _load_json(_discovery_report_path(target_date, suffix=suffix))
        for suffix in confirmation_suffixes
    }
    return {
        "daily_path": daily_path,
        "daily": daily,
        "promotion_window": promotion_suffix,
        "promotion_path": promotion_path,
        "promotion": promotion,
        "confirmation_windows": confirmation_suffixes,
        "confirmation": confirmation,
        "paths": {
            "daily": daily_path,
            promotion_suffix: promotion_path,
            **{
                suffix: _discovery_report_path(target_date, suffix=suffix)
                for suffix in confirmation_suffixes
            },
        },
    }


def _summary_contract_passed(discovery: dict[str, Any]) -> bool:
    summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    return (
        str(summary.get("source_contract_status") or "") == "pass"
        and str(summary.get("parent_granularity_status") or "") == "target_pass"
        and str(summary.get("ai_two_pass_review_status") or "") == "parsed"
    )


def _discovery_summary_meta(discovery: dict[str, Any]) -> dict[str, Any]:
    summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    return {
        "lifecycle_bucket_discovery_source_contract_status": summary.get("source_contract_status"),
        "lifecycle_bucket_discovery_ai_review_status": summary.get("ai_two_pass_review_status"),
    }


def _discovery_candidate_meta(
    *,
    family: str,
    discovery: dict[str, Any],
    discovery_live_by_family: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    meta = _discovery_summary_meta(discovery)
    item = discovery_live_by_family.get(family) or {}
    if item:
        meta.update(
            {
                "lifecycle_bucket_discovery_bucket_id": item.get("bucket_id"),
                "lifecycle_bucket_discovery_classification_state": item.get("classification_state"),
                "lifecycle_bucket_discovery_bucket_relation": item.get("bucket_relation"),
                "lifecycle_bucket_discovery_ai_final_decision": item.get("ai_final_decision"),
                "lifecycle_bucket_discovery_ai_final_reason": item.get("ai_final_reason"),
                "lifecycle_bucket_discovery_ai_followup_required": item.get("ai_review_followup_required"),
                "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get("ai_review_block_ignored_reason"),
            }
        )
    return {key: value for key, value in meta.items() if value not in (None, "", [])}


def _action_for_greenfield_row(item: dict[str, Any]) -> str:
    stage = str(item.get("stage") or "").lower()
    action = str(item.get("recommended_action") or "").upper()
    if action in {"*", "ANY"}:
        return "*"
    if stage == "entry":
        if action == "BUY":
            return action
        return "BUY"
    if stage == "submit":
        if action == "ALLOW_SUBMIT":
            return action
        return "ALLOW_SUBMIT"
    if stage == "scale_in":
        if action in {"AVG_DOWN", "PYRAMID"}:
            return action
        return "*"
    if stage == "holding":
        if action == "HOLD":
            return action
        return "HOLD"
    if stage == "exit":
        if action in {"SELL", "EXIT"}:
            return "SELL"
        return "SELL"
    return "*"


def _build_greenfield_policy(target_date: str, discovery: dict[str, Any]) -> dict[str, Any]:
    live_candidates = (
        discovery.get("live_auto_apply_candidates")
        if isinstance(discovery.get("live_auto_apply_candidates"), list)
        else []
    )
    flow_candidates = [
        item
        for item in live_candidates
        if _greenfield_parent_policy_contract_passed(item)
    ]
    rows: list[dict[str, Any]] = []
    selected_flow = flow_candidates[0] if flow_candidates else {}
    if selected_flow:
        auto_contract = selected_flow.get("auto_promotion_contract")
        tier2_status = (
            selected_flow.get("ai_review_status")
            or selected_flow.get("lifecycle_bucket_discovery_ai_review_status")
            or (
                auto_contract.get("tier2_status")
                if isinstance(auto_contract, dict)
                else "parsed"
            )
            or "parsed"
        )
        child_ids = (
            selected_flow.get("child_bucket_ids")
            if isinstance(selected_flow.get("child_bucket_ids"), dict)
            else {}
        )
        absorbed_child_bucket_ids = (
            selected_flow.get("absorbed_child_bucket_ids")
            if isinstance(selected_flow.get("absorbed_child_bucket_ids"), list)
            else []
        )
        dimension_filters = (
            selected_flow.get("dimension_filters")
            if isinstance(selected_flow.get("dimension_filters"), dict)
            else {}
        )
        dominant_child_patterns = (
            selected_flow.get("dominant_child_patterns")
            if isinstance(selected_flow.get("dominant_child_patterns"), list)
            else []
        )
        conflicting_child_patterns = (
            selected_flow.get("conflicting_child_patterns")
            if isinstance(selected_flow.get("conflicting_child_patterns"), list)
            else []
        )
        policy_bucket_id = (
            selected_flow.get("policy_bucket_id")
            or selected_flow.get("canonical_parent_bucket")
            or selected_flow.get("bucket_id")
        )
        selected_parent_level = selected_flow.get("selected_parent_level")
        parent_granularity_status = selected_flow.get("parent_granularity_status")
        stage_actions = {
            "entry": "BUY",
            "submit": "ALLOW_SUBMIT",
            "holding": "HOLD",
            "exit": "SELL",
        }
        for stage, action in stage_actions.items():
            bucket_id = selected_flow.get(f"{stage}_bucket_id") or child_ids.get(stage)
            rows.append(
                {
                    "bucket_id": bucket_id,
                    "family": GREENFIELD_REAL_ENV_FAMILY,
                    "stage": stage,
                    "action": action,
                    "strategy_scope": "all",
                    "authority_source": "lifecycle_bucket_discovery_lifecycle_flow_live_auto_apply",
                    "source_quality_gate": selected_flow.get("source_quality_gate") or "pass",
                    "ai_tier2_status": tier2_status,
                    "runtime_apply_version": f"{GREENFIELD_REAL_ENV_FAMILY}:{target_date}",
                    "post_apply_attribution_key": selected_flow.get("attribution_key")
                    or selected_flow.get("bucket_id"),
                    "lifecycle_flow_bucket_id": selected_flow.get("lifecycle_flow_bucket_id")
                    or selected_flow.get("bucket_id"),
                    "greenfield_policy_bucket_id": selected_flow.get("bucket_id"),
                    "policy_bucket_id": policy_bucket_id,
                    "selected_parent_level": selected_parent_level,
                    "parent_granularity_status": parent_granularity_status,
                    "absorbed_child_bucket_ids": absorbed_child_bucket_ids,
                    "dimension_filters": dimension_filters,
                    "dominant_child_patterns": dominant_child_patterns,
                    "conflicting_child_patterns": conflicting_child_patterns,
                }
            )
        scale_bucket_id = selected_flow.get("scale_in_bucket_id")
        if scale_bucket_id:
            rows.append(
                {
                    "bucket_id": scale_bucket_id,
                    "family": GREENFIELD_REAL_ENV_FAMILY,
                    "stage": "scale_in",
                    "action": "*",
                    "strategy_scope": "all",
                    "authority_source": "lifecycle_bucket_discovery_lifecycle_flow_live_auto_apply",
                    "source_quality_gate": selected_flow.get("source_quality_gate") or "pass",
                    "ai_tier2_status": tier2_status,
                    "runtime_apply_version": f"{GREENFIELD_REAL_ENV_FAMILY}:{target_date}",
                    "post_apply_attribution_key": selected_flow.get("attribution_key")
                    or selected_flow.get("bucket_id"),
                    "lifecycle_flow_bucket_id": selected_flow.get("lifecycle_flow_bucket_id")
                    or selected_flow.get("bucket_id"),
                    "greenfield_policy_bucket_id": selected_flow.get("bucket_id"),
                    "policy_bucket_id": policy_bucket_id,
                    "selected_parent_level": selected_parent_level,
                    "parent_granularity_status": parent_granularity_status,
                    "absorbed_child_bucket_ids": absorbed_child_bucket_ids,
                    "dimension_filters": dimension_filters,
                    "dominant_child_patterns": dominant_child_patterns,
                    "conflicting_child_patterns": conflicting_child_patterns,
                }
            )
    stages: dict[str, list[dict[str, Any]]] = {
        stage: [] for stage in ("entry", "submit", "holding", "scale_in", "exit")
    }
    for row in rows:
        stages[str(row["stage"])].append(row)
    selected_policy_bucket_id = None
    if selected_flow:
        selected_policy_bucket_id = selected_flow.get("policy_bucket_id") or selected_flow.get("canonical_parent_bucket")
    stage_contract = {
        stage: {
            "stage": stage,
            "row_count": len(stages[stage]),
            "baseline_passthrough_allowed": False,
            "contract_state": "promoted_policy_present" if stages[stage] else "missing_policy",
        }
        for stage in ("entry", "submit", "holding", "scale_in", "exit")
    }
    return {
        "schema_version": "greenfield_lifecycle_bundle_policy_v1",
        "policy_id": GREENFIELD_REAL_ENV_FAMILY,
        "policy_version": f"{GREENFIELD_REAL_ENV_FAMILY}:{target_date}",
        "source_date": target_date,
        "scope": "full_lifecycle",
        "bundle_id": selected_flow.get("lifecycle_flow_bucket_id")
        or selected_flow.get("bucket_id")
        or f"greenfield_lifecycle_bundle_policy_v1:{target_date}",
        "source_lifecycle_flow_candidate": selected_flow.get("bucket_id") if selected_flow else None,
        "policy_bucket_id": selected_policy_bucket_id,
        "selected_parent_level": selected_flow.get("selected_parent_level") if selected_flow else None,
        "parent_granularity_status": selected_flow.get("parent_granularity_status") if selected_flow else None,
        "absorbed_child_bucket_ids": selected_flow.get("absorbed_child_bucket_ids") if selected_flow else [],
        "dimension_filters": selected_flow.get("dimension_filters") if selected_flow else {},
        "dominant_child_patterns": selected_flow.get("dominant_child_patterns") if selected_flow else [],
        "conflicting_child_patterns": selected_flow.get("conflicting_child_patterns") if selected_flow else [],
        "attribution_key": selected_flow.get("attribution_key") if selected_flow else None,
        "child_bucket_ids": selected_flow.get("child_bucket_ids") if selected_flow else {},
        "rollback_guard": selected_flow.get("rollback_guard") if selected_flow else None,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "stages": stages,
        "stage_contract": stage_contract,
        "allowlist": rows,
        "hard_safety_priority": [
            "broker_guard",
            "account_guard",
            "order_guard",
            "quantity_guard",
            "cooldown_guard",
            "stale_quote",
            "price_freshness",
            "hard_stop",
            "protect_stop",
            "emergency_stop",
        ],
    }


def _greenfield_candidate(
    target_date: str,
    discovery: dict[str, Any],
    *,
    confirmation_discoveries: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    policy = _build_greenfield_policy(target_date, discovery)
    if not policy.get("allowlist"):
        return None
    selected_policy_bucket_id = str(policy.get("policy_bucket_id") or "")
    selected_flow = {}
    for item in discovery.get("live_auto_apply_candidates") or []:
        if isinstance(item, dict) and _candidate_policy_bucket_id(item) == selected_policy_bucket_id:
            selected_flow = item
            break
    confirmation = _greenfield_parent_confirmation(selected_flow, confirmation_discoveries or {}) if selected_flow else {
        "passed": False,
        "policy_bucket_id": selected_policy_bucket_id,
        "windows": {},
    }
    if not confirmation.get("passed"):
        return {
            "candidate_id": f"{GREENFIELD_REAL_ENV_FAMILY}:{target_date}",
            "family": GREENFIELD_REAL_ENV_FAMILY,
            "stage": "greenfield_real_env",
            "priority": 7,
            "bridge_candidate_state": "blocked_cumulative_confirmation_missing",
            "approval_required": False,
            "human_approval_required": False,
            "live_auto_apply": False,
            "allowed_runtime_apply": False,
            "runtime_effect": False,
            "runtime_effect_after_approval": "none",
            "lifecycle_bucket_discovery_ai_review_status": "parsed",
            "ai_review_status": "parsed",
            "target_env_keys": [],
            "recommended_values": {
                "enabled": False,
                "scope": "inactive",
                "policy_file": "",
                "policy_version": policy.get("policy_version"),
                "telegram_enabled": False,
                "threshold_version": policy.get("policy_version"),
                "calibration_state": "runtime_apply_bridge:blocked_cumulative_confirmation_missing",
            },
            "current_values": {
                "enabled": False,
                "scope": "inactive",
                "policy_file": "",
                "policy_version": "runtime_default",
                "telegram_enabled": False,
            },
            "greenfield_policy_contract_state": "blocked_cumulative_confirmation_missing",
            "greenfield_parent_confirmation": confirmation,
            "source_bucket_keys": [str(row.get("bucket_id") or "") for row in policy.get("allowlist") or []],
            "primary_decision_metric": "lifecycle_bundle_ev",
            "decision_authority": "runtime_apply_bridge_cumulative_confirmation_gate",
            "forbidden_uses": [
                "daily_only_live_authority",
                "hard_safety_bypass",
                "intraday_threshold_mutation",
                "provider_route_change",
                "bot_restart_trigger",
            ],
        }
    bundle_issue = validate_greenfield_policy_payload(policy, expected_version=str(policy.get("policy_version") or ""))
    if bundle_issue:
        return {
            "candidate_id": f"{GREENFIELD_REAL_ENV_FAMILY}:{target_date}",
            "family": GREENFIELD_REAL_ENV_FAMILY,
            "stage": "greenfield_real_env",
            "priority": 7,
            "bridge_candidate_state": "runtime_blocked_contract_gap",
            "approval_required": False,
            "human_approval_required": False,
            "live_auto_apply": False,
            "allowed_runtime_apply": False,
            "runtime_effect": False,
            "runtime_effect_after_approval": "none",
            "lifecycle_bucket_discovery_ai_review_status": "parsed",
            "ai_review_status": "parsed",
            "target_env_keys": [],
            "recommended_values": {
                "enabled": False,
                "scope": "full_lifecycle",
                "policy_file": "",
                "policy_version": policy.get("policy_version"),
                "telegram_enabled": False,
                "threshold_version": policy.get("policy_version"),
                "calibration_state": f"runtime_apply_bridge:{bundle_issue}",
            },
            "current_values": {
                "enabled": False,
                "scope": "inactive",
                "policy_file": "",
                "policy_version": "runtime_default",
                "telegram_enabled": False,
            },
            "greenfield_policy_contract_state": bundle_issue,
            "greenfield_policy_stage_contract": policy.get("stage_contract"),
            "source_bucket_keys": [str(row.get("bucket_id") or "") for row in policy.get("allowlist") or []],
            "primary_decision_metric": "lifecycle_bundle_ev",
            "decision_authority": "runtime_apply_bridge_lifecycle_bundle_contract",
            "forbidden_uses": [
                "entry_only_full_lifecycle_promotion",
                "hard_safety_bypass",
                "intraday_threshold_mutation",
                "provider_route_change",
                "bot_restart_trigger",
            ],
        }
    policy_path = greenfield_real_env_policy_path(target_date)
    recommended = {
        "enabled": True,
        "scope": "full_lifecycle",
        "policy_file": str(policy_path),
        "policy_version": policy.get("policy_version"),
        "telegram_enabled": True,
        "threshold_version": policy.get("policy_version"),
        "calibration_state": "runtime_apply_bridge:live_auto_apply_ready",
    }
    return {
        "candidate_id": f"{GREENFIELD_REAL_ENV_FAMILY}:{target_date}",
        "family": GREENFIELD_REAL_ENV_FAMILY,
        "stage": "greenfield_real_env",
        "priority": 7,
        "bridge_candidate_state": "live_auto_apply_ready",
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": True,
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "runtime_effect_after_approval": "full_lifecycle_greenfield_real_env_authority",
        "lifecycle_bucket_discovery_ai_review_status": "parsed",
        "ai_review_status": "parsed",
        "target_env_keys": [
            "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
            "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE",
            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION",
            "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED",
        ],
        "recommended_values": recommended,
        "current_values": {
            "enabled": False,
            "scope": "inactive",
            "policy_file": "",
            "policy_version": "runtime_default",
            "telegram_enabled": False,
        },
            "greenfield_policy": policy,
            "greenfield_policy_file": str(policy_path),
            "greenfield_parent_confirmation": confirmation,
            "source_bucket_keys": [str(row.get("bucket_id") or "") for row in policy.get("allowlist") or []],
        "primary_decision_metric": "lifecycle_bundle_ev",
        "entry_bucket_ev_metric_role": "diagnostic_entry_bucket_ev",
        "decision_authority": "greenfield_lifecycle_bundle_policy_v1",
        "forbidden_uses": [
            "hard_safety_bypass",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
            "sizing_formula_runtime_apply_without_guard",
        ],
    }


def _greenfield_flow_discovery_counts(discovery: dict[str, Any]) -> dict[str, int]:
    candidates = discovery.get("candidates") if isinstance(discovery.get("candidates"), list) else []
    surfaced = discovery.get("surfaced_candidates") if isinstance(discovery.get("surfaced_candidates"), list) else []
    live_candidates = (
        discovery.get("live_auto_apply_candidates")
        if isinstance(discovery.get("live_auto_apply_candidates"), list)
        else []
    )

    def is_flow(item: Any) -> bool:
        return (
            isinstance(item, dict)
            and str(item.get("stage") or "") == "lifecycle_flow"
            and str(item.get("bucket_type") or "") == "combo_lifecycle_flow"
        )

    return {
        "candidate_count": sum(1 for item in candidates if is_flow(item)),
        "surfaced_candidate_count": sum(1 for item in surfaced if is_flow(item)),
        "live_auto_apply_candidate_count": sum(1 for item in live_candidates if is_flow(item)),
    }


def _align_with_discovery(
    state: str,
    rolling: dict[str, Any],
    *,
    family: str,
    discovery_live_families: set[str],
    discovery_available: bool,
) -> tuple[str, dict[str, Any]]:
    aligned = dict(rolling)
    if state != "live_auto_apply_ready":
        return state, aligned
    if family in discovery_live_families:
        aligned["lifecycle_bucket_discovery_gate"] = "pass"
        return state, aligned
    aligned["lifecycle_bucket_discovery_gate"] = "blocked"
    aligned["lifecycle_bucket_discovery_available"] = bool(discovery_available)
    return "runtime_blocked_contract_gap", aligned


def _entry_candidate(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    target_date: str,
    *,
    discovery_live_families: set[str],
    discovery_live_by_family: dict[str, dict[str, Any]],
    discovery: dict[str, Any],
    discovery_available: bool,
) -> dict[str, Any]:
    bucket = _find_bucket(payload, "entry_bucket_attribution", "combo_entry_spot", ENTRY_TARGET_BUCKET_KEY)
    state, rolling = _state_for_bucket(
        bucket,
        history,
        section="entry_bucket_attribution",
        bucket_type="combo_entry_spot",
        bucket_key=ENTRY_TARGET_BUCKET_KEY,
        positive_edge=True,
    )
    state, rolling = _align_with_discovery(
        state,
        rolling,
        family=ENTRY_BRIDGE_FAMILY,
        discovery_live_families=discovery_live_families,
        discovery_available=discovery_available,
    )
    discovery_meta = _discovery_candidate_meta(
        family=ENTRY_BRIDGE_FAMILY,
        discovery=discovery,
        discovery_live_by_family=discovery_live_by_family,
    )
    target_env_keys = []
    if state == "live_auto_apply_ready":
        target_env_keys = [
            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE",
            "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP",
            "AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION",
            "AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE",
        ]
    missing_fields = _missing_source_fields(bucket)
    explicit_exclusion = state != "live_auto_apply_ready" and (
        bool(missing_fields) or rolling.get("lifecycle_bucket_discovery_gate") == "blocked" or not bool(bucket)
    )
    exclusion_reason = (
        "counterfactual_source_field_gap"
        if missing_fields
        else "counterfactual_sim_lifecycle_handoff"
        if explicit_exclusion
        else ""
    )
    return {
        "candidate_id": f"{ENTRY_BRIDGE_FAMILY}:{target_date}",
        "family": ENTRY_BRIDGE_FAMILY,
        "stage": "entry",
        "priority": 9,
        "bridge_candidate_state": state,
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": state == "live_auto_apply_ready",
        "allowed_runtime_apply": state == "live_auto_apply_ready",
        "runtime_effect": False,
        "runtime_effect_after_approval": "bounded_entry_probe_recovery_live_auto"
        if state == "live_auto_apply_ready"
        else "none",
        "target_env_keys": target_env_keys,
        "recommended_values": {
            "enabled": state == "live_auto_apply_ready",
            "min_score": 66,
            "max_score": 69,
            "min_buy_pressure": 0.0,
            "min_tick_accel": 0.0,
            "min_micro_vwap_bp": -999.0,
            "max_budget_krw": 0,
            "max_qty": 0,
            "threshold_version": f"{ENTRY_BRIDGE_FAMILY}:{target_date}",
            "calibration_state": f"runtime_apply_bridge:{state}",
        },
        "current_values": {
            "enabled": False,
            "min_score": 65,
            "max_score": 74,
            "max_budget_krw": 0,
            "max_qty": 0,
            "threshold_version": "runtime_default",
            "calibration_state": "runtime_default",
        },
        "source_bucket_keys": [ENTRY_TARGET_BUCKET_KEY],
        "source_bucket": bucket,
        "rolling_confirmation": rolling,
        **discovery_meta,
        "evidence_grade": EVIDENCE_GRADE_2_COUNTERFACTUAL,
        "transition_target": "bounded_live_canary" if state == "live_auto_apply_ready" else "sim_lifecycle_handoff",
        "explicit_runtime_exclusion": explicit_exclusion,
        "bridge_exclusion_reason": exclusion_reason,
        "runtime_exclusion_reason": exclusion_reason,
        "missing_runtime_source_fields": missing_fields,
        "counterfactual_contract": {
            "evidence_grade": EVIDENCE_GRADE_2_COUNTERFACTUAL,
            "transition_target": "sim_lifecycle_handoff",
            "source_field_gap_fields": missing_fields,
        },
        "grade_reason": "wait6579_ev_cohort_is_counterfactual_source_not_completed_lifecycle_evidence",
        "full_real_conversion_allowed": False,
        "legacy_family_archived": False,
        "archived_live_exception_reason": None,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "decision_authority": "lifecycle_bucket_discovery_live_auto_apply"
        if state == "live_auto_apply_ready"
        else "runtime_apply_bridge_source_quality",
        "forbidden_uses": [
            "intraday_threshold_mutation",
            "broker_guard_bypass",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }


def _scale_source(bucket: dict[str, Any], *, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "bucket_type": bucket.get("bucket_type"),
        "bucket_key": bucket.get("bucket_key"),
        "joined_sample": bucket.get("joined_sample"),
        "source_quality_adjusted_ev_pct": bucket.get("source_quality_adjusted_ev_pct"),
        "recommended_route": bucket.get("recommended_route"),
        "source_quality_gate": bucket.get("source_quality_gate"),
    }


def _scale_candidate(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    target_date: str,
    *,
    discovery_live_families: set[str],
    discovery_live_by_family: dict[str, dict[str, Any]],
    discovery: dict[str, Any],
    discovery_available: bool,
) -> dict[str, Any]:
    pyramid = _find_bucket(payload, "scale_in_bucket_attribution", "arm", "PYRAMID")
    avg_down = _find_bucket(payload, "scale_in_bucket_attribution", "blocker_namespace", "AVG_DOWN_ONLY")
    pyramid_state, pyramid_roll = _state_for_bucket(
        pyramid,
        history,
        section="scale_in_bucket_attribution",
        bucket_type="arm",
        bucket_key="PYRAMID",
        positive_edge=False,
    )
    avg_state, avg_roll = _state_for_bucket(
        avg_down,
        history,
        section="scale_in_bucket_attribution",
        bucket_type="blocker_namespace",
        bucket_key="AVG_DOWN_ONLY",
        positive_edge=False,
    )
    ready = pyramid_state == "live_auto_apply_ready" or avg_state == "live_auto_apply_ready"
    blocked_conflict = pyramid_state == "blocked_rolling_conflict" or avg_state == "blocked_rolling_conflict"
    blocked_source = pyramid_state == "blocked_source_quality" and avg_state == "blocked_source_quality"
    if blocked_conflict:
        state = "blocked_rolling_conflict"
    elif ready:
        state = "live_auto_apply_ready"
    elif blocked_source:
        state = "blocked_source_quality"
    else:
        state = "bootstrap_pending"
    if state == "live_auto_apply_ready" and SCALE_IN_BRIDGE_FAMILY not in discovery_live_families:
        state = "runtime_blocked_contract_gap"
        pyramid_roll = {**pyramid_roll, "lifecycle_bucket_discovery_gate": "blocked"}
        avg_roll = {**avg_roll, "lifecycle_bucket_discovery_gate": "blocked"}
        pyramid_roll["lifecycle_bucket_discovery_available"] = bool(discovery_available)
        avg_roll["lifecycle_bucket_discovery_available"] = bool(discovery_available)
    discovery_meta = _discovery_candidate_meta(
        family=SCALE_IN_BRIDGE_FAMILY,
        discovery=discovery,
        discovery_live_by_family=discovery_live_by_family,
    )

    target_env_keys: list[str] = []
    recommended_values: dict[str, Any] = {
        "effective_qty_cap": 1,
        "threshold_version": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "calibration_state": f"runtime_apply_bridge:{state}",
    }
    current_values: dict[str, Any] = {
        "effective_qty_cap": 1,
        "scalping_enable_pyramid": True,
        "reversal_add_min_ai_score": 60,
        "reversal_add_min_buy_pressure": 55.0,
        "reversal_add_min_tick_accel": 0.95,
    }
    if pyramid_state == "live_auto_apply_ready":
        target_env_keys.append("SCALPING_ENABLE_PYRAMID")
        recommended_values["scalping_enable_pyramid"] = False
    if avg_state == "live_auto_apply_ready":
        target_env_keys.extend(
            [
                "REVERSAL_ADD_MIN_AI_SCORE",
                "REVERSAL_ADD_MIN_BUY_PRESSURE",
                "REVERSAL_ADD_MIN_TICK_ACCEL",
            ]
        )
        recommended_values.update(
            {
                "reversal_add_min_ai_score": 65,
                "reversal_add_min_buy_pressure": 60.0,
                "reversal_add_min_tick_accel": 1.05,
            }
        )

    source_buckets = []
    if pyramid:
        source_buckets.append(_scale_source(pyramid, role="pyramid_tighten_or_disable"))
    if avg_down:
        source_buckets.append(_scale_source(avg_down, role="avg_down_reversal_tighten"))
    positive_refs = []
    for item in payload.get("scale_in_bucket_attribution", {}).get("buckets", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("recommended_route") or "") == "candidate_recovery_or_relax":
            positive_refs.append(_scale_source(item, role="observe_only_reference"))

    return {
        "candidate_id": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "family": SCALE_IN_BRIDGE_FAMILY,
        "stage": "scale_in",
        "priority": 39,
        "bridge_candidate_state": state,
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": state == "live_auto_apply_ready",
        "allowed_runtime_apply": state == "live_auto_apply_ready",
        "runtime_effect": False,
        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
        "target_env_keys": list(dict.fromkeys(target_env_keys)),
        "recommended_values": recommended_values,
        "current_values": current_values,
        "source_bucket_keys": [str(item.get("bucket_key") or "") for item in source_buckets],
        "source_buckets": source_buckets,
        "observe_only_reference_buckets": positive_refs[:5],
        "rolling_confirmation": {
            "pyramid": pyramid_roll,
            "avg_down": avg_roll,
            "pyramid_state": pyramid_state,
            "avg_down_state": avg_state,
        },
        **discovery_meta,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "decision_authority": "lifecycle_bucket_discovery_live_auto_apply",
        "forbidden_uses": [
            "scale_in_safety_guard_bypass",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }


def build_runtime_apply_bridge_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_path = _ldm_report_path(target_date)
    payload = _load_json(source_path)
    discovery_context = _discovery_window_context(target_date)
    daily_discovery_path = discovery_context["daily_path"]
    daily_discovery = discovery_context["daily"]
    promotion_discovery_path = discovery_context["promotion_path"]
    promotion_discovery = discovery_context["promotion"]
    confirmation_discoveries = discovery_context["confirmation"]
    discovery_path = promotion_discovery_path if promotion_discovery else daily_discovery_path
    discovery = promotion_discovery if promotion_discovery else daily_discovery
    promotion_contract_passed = _summary_contract_passed(promotion_discovery) if promotion_discovery else False
    discovery_live_families = _discovery_live_families(promotion_discovery) if promotion_contract_passed else set()
    discovery_live_by_family = (
        _discovery_live_candidate_by_family(promotion_discovery) if promotion_contract_passed else {}
    )
    discovery_summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    daily_summary = daily_discovery.get("summary") if isinstance(daily_discovery.get("summary"), dict) else {}
    discovery_warnings = [str(item) for item in (discovery.get("warnings") or []) if str(item)]
    discovery_source_contract_status = str(discovery_summary.get("source_contract_status") or "")
    discovery_ai_review_status = str(discovery_summary.get("ai_two_pass_review_status") or "")
    greenfield_flow_counts = _greenfield_flow_discovery_counts(discovery) if discovery else {
        "candidate_count": 0,
        "surfaced_candidate_count": 0,
        "live_auto_apply_candidate_count": 0,
    }
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    if daily_discovery and _safe_int(daily_summary.get("live_auto_apply_ready_count"), 0) > 0 and not promotion_contract_passed:
        warnings.append("daily_only_live_candidate_blocked_cumulative_confirmation_missing")
    if promotion_discovery and not promotion_contract_passed:
        warnings.append("promotion_lifecycle_bucket_discovery_contract_not_passed")
    if not promotion_discovery:
        warnings.append("promotion_lifecycle_bucket_discovery_missing")
    if not payload:
        warnings.append("lifecycle_decision_matrix_missing")
    else:
        history = _history_reports(target_date)
        if not discovery:
            warnings.append("lifecycle_bucket_discovery_missing")
        candidates.append(
            _entry_candidate(
                payload,
                history,
                target_date,
                discovery_live_families=discovery_live_families,
                discovery_live_by_family=discovery_live_by_family,
                discovery=discovery,
                discovery_available=bool(discovery),
            )
        )
        candidates.append(
            _scale_candidate(
                payload,
                history,
                target_date,
                discovery_live_families=discovery_live_families,
                discovery_live_by_family=discovery_live_by_family,
                discovery=discovery,
                discovery_available=bool(discovery),
            )
        )
        greenfield = _greenfield_candidate(
            target_date,
            promotion_discovery if promotion_contract_passed else {},
            confirmation_discoveries=confirmation_discoveries,
        )
        if greenfield:
            if greenfield.get("greenfield_policy_contract_state"):
                warnings.append(str(greenfield.get("greenfield_policy_contract_state")))
            candidates.append(greenfield)
        elif discovery and greenfield_flow_counts["live_auto_apply_candidate_count"] <= 0:
            if greenfield_flow_counts["candidate_count"] > 0 or greenfield_flow_counts["surfaced_candidate_count"] > 0:
                warnings.append("greenfield_policy_not_emitted_no_live_auto_ready_lifecycle_flow")
            else:
                warnings.append("greenfield_policy_not_emitted_no_complete_lifecycle_flow")
    if discovery and discovery_source_contract_status and discovery_source_contract_status != "pass":
        warnings.append(f"lifecycle_bucket_discovery_source_contract_{discovery_source_contract_status}")
    if discovery and any(item.get("lifecycle_bucket_discovery_ai_followup_required") for item in candidates):
        warnings.append("lifecycle_bucket_discovery_live_auto_post_apply_followup_required")
    warnings.extend(
        item
        for item in discovery_warnings
        if item.startswith("ai_") or item.startswith("source_contract_")
    )
    warnings = list(dict.fromkeys(warnings))
    status = "pass" if candidates else "fail"
    live_ready_count = sum(1 for item in candidates if item.get("bridge_candidate_state") == "live_auto_apply_ready")
    greenfield_ready_count = sum(
        1
        for item in candidates
        if item.get("family") == GREENFIELD_REAL_ENV_FAMILY
        and item.get("bridge_candidate_state") == "live_auto_apply_ready"
    )
    greenfield_live_ready_flow_count = greenfield_flow_counts["live_auto_apply_candidate_count"]
    greenfield_contract_gap = next(
        (
            item
            for item in candidates
            if item.get("family") == GREENFIELD_REAL_ENV_FAMILY
            and item.get("bridge_candidate_state") == "runtime_blocked_contract_gap"
        ),
        None,
    )
    cumulative_confirmation_blocked = any(
        item.get("bridge_candidate_state") == "blocked_cumulative_confirmation_missing" for item in candidates
    )
    greenfield_flow_exists = (
        greenfield_flow_counts["candidate_count"] > 0
        or greenfield_flow_counts["surfaced_candidate_count"] > 0
    )
    greenfield_policy_emit_state = (
        "ready"
        if greenfield_ready_count > 0
        else "not_emitted_greenfield_policy_contract_gap"
        if greenfield_contract_gap
        else "not_emitted_cumulative_confirmation_missing"
        if cumulative_confirmation_blocked
        else "not_emitted_no_live_auto_ready_lifecycle_flow"
        if discovery and greenfield_flow_exists and greenfield_live_ready_flow_count <= 0
        else "not_emitted_no_complete_lifecycle_flow"
        if discovery
        else "not_emitted_discovery_missing"
    )
    greenfield_policy_emit_blocker = (
        None
        if greenfield_ready_count > 0
        else "greenfield_policy_contract_gap"
        if greenfield_contract_gap
        else "cumulative_confirmation_missing"
        if cumulative_confirmation_blocked
        else "no_live_auto_ready_lifecycle_flow"
        if discovery and greenfield_flow_exists
        else "no_complete_lifecycle_flow"
        if discovery
        else "discovery_missing"
    )
    greenfield_policy_emit_blocker_detail = (
        "greenfield policy ready"
        if greenfield_ready_count > 0
        else str(greenfield_contract_gap.get("greenfield_policy_contract_state") or "greenfield policy contract gap")
        if greenfield_contract_gap
        else "promotion window confirmation is missing for a live-auto lifecycle flow"
        if cumulative_confirmation_blocked
        else "lifecycle flow exists, but no lifecycle flow is live_auto_apply_ready for greenfield policy emission"
        if discovery and greenfield_flow_exists
        else "no lifecycle flow candidate is available for greenfield policy emission"
        if discovery
        else "lifecycle bucket discovery artifact is missing"
    )
    live_followup_count = sum(
        1
        for item in candidates
        if item.get("bridge_candidate_state") == "live_auto_apply_ready"
        and item.get("lifecycle_bucket_discovery_ai_followup_required")
    )
    report = {
        "schema_version": "runtime_apply_bridge_v1",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": {
            "lifecycle_decision_matrix": str(source_path) if source_path.exists() else None,
            "lifecycle_bucket_discovery": str(daily_discovery_path) if daily_discovery_path.exists() else None,
            "promotion_lifecycle_bucket_discovery": str(promotion_discovery_path) if promotion_discovery_path.exists() else None,
            "confirmation_lifecycle_bucket_discovery": {
                suffix: str(path) if path.exists() else None
                for suffix, path in discovery_context["paths"].items()
                if suffix not in {"daily", discovery_context["promotion_window"]}
            },
            "runtime_approval_summary": str(
                DATA_DIR / "report" / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json"
            ),
        },
        "status": status,
        "summary": {
            "candidate_count": len(candidates),
            "ready_for_approval_count": 0,
            "live_auto_apply_ready_count": live_ready_count,
            "greenfield_real_env_ready_count": greenfield_ready_count,
            "greenfield_lifecycle_flow_candidate_count": greenfield_flow_counts["candidate_count"],
            "greenfield_lifecycle_flow_surfaced_candidate_count": greenfield_flow_counts["surfaced_candidate_count"],
            "greenfield_lifecycle_flow_live_auto_apply_candidate_count": greenfield_flow_counts[
                "live_auto_apply_candidate_count"
            ],
            "greenfield_live_auto_ready_lifecycle_flow_count": greenfield_live_ready_flow_count,
            "greenfield_policy_emit_state": greenfield_policy_emit_state,
            "greenfield_policy_emit_blocker": greenfield_policy_emit_blocker,
            "greenfield_policy_emit_blocker_detail": greenfield_policy_emit_blocker_detail,
            "stage_local_live_auto_apply_ready_count": max(live_ready_count - greenfield_ready_count, 0),
            "lifecycle_bucket_discovery_status": "present" if discovery else "missing",
            "lifecycle_bucket_promotion_window": discovery_context["promotion_window"],
            "lifecycle_bucket_promotion_contract_passed": promotion_contract_passed,
            "lifecycle_bucket_discovery_source_contract_status": discovery_source_contract_status or None,
            "lifecycle_bucket_discovery_ai_review_status": discovery_ai_review_status or None,
            "lifecycle_bucket_discovery_live_followup_count": live_followup_count,
            "approval_required_count": sum(1 for item in candidates if item.get("approval_required")),
            "human_approval_required": False,
            "runtime_mutation_performed": False,
        },
        "candidates": candidates,
        "warnings": warnings,
    }
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    target_date = str(report.get("date") or "")
    lines = [
        f"# Runtime Apply Bridge {target_date}",
        "",
        "## 판정",
        "",
        f"- status: `{report.get('status')}`",
        f"- live_auto_apply_ready_count: `{report.get('summary', {}).get('live_auto_apply_ready_count')}`",
        f"- greenfield_policy_emit_state: `{report.get('summary', {}).get('greenfield_policy_emit_state')}`",
        f"- greenfield_policy_emit_blocker: `{report.get('summary', {}).get('greenfield_policy_emit_blocker') or '-'}`",
        f"- greenfield_policy_emit_blocker_detail: `{report.get('summary', {}).get('greenfield_policy_emit_blocker_detail') or '-'}`",
        f"- greenfield_lifecycle_flow live/surfaced/total: "
        f"`{report.get('summary', {}).get('greenfield_lifecycle_flow_live_auto_apply_candidate_count')}` / "
        f"`{report.get('summary', {}).get('greenfield_lifecycle_flow_surfaced_candidate_count')}` / "
        f"`{report.get('summary', {}).get('greenfield_lifecycle_flow_candidate_count')}`",
        f"- lifecycle_bucket_discovery_source_contract_status: `{report.get('summary', {}).get('lifecycle_bucket_discovery_source_contract_status') or '-'}`",
        f"- lifecycle_bucket_discovery_ai_review_status: `{report.get('summary', {}).get('lifecycle_bucket_discovery_ai_review_status') or '-'}`",
        f"- lifecycle_bucket_promotion_window: `{report.get('summary', {}).get('lifecycle_bucket_promotion_window') or '-'}`",
        f"- lifecycle_bucket_promotion_contract_passed: `{report.get('summary', {}).get('lifecycle_bucket_promotion_contract_passed')}`",
        f"- lifecycle_bucket_discovery_live_followup_count: `{report.get('summary', {}).get('lifecycle_bucket_discovery_live_followup_count')}`",
        "- note: `not_emitted_no_live_auto_ready_lifecycle_flow` means lifecycle flow exists but no "
        "greenfield live-auto-ready flow is available.",
        f"- human_approval_required: `{report.get('summary', {}).get('human_approval_required')}`",
        "- runtime mutation: `none`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## 근거",
        "",
    ]
    for item in report.get("candidates") or []:
        lines.extend(
            [
                f"- `{item.get('family')}`: state=`{item.get('bridge_candidate_state')}`, "
                f"allowed_runtime_apply=`{item.get('allowed_runtime_apply')}`, "
                f"approval_required=`{item.get('approval_required')}`, "
                f"live_auto_apply=`{item.get('live_auto_apply')}`, "
                f"ai_followup=`{item.get('lifecycle_bucket_discovery_ai_followup_required') or '-'}`",
            ]
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "",
            "- `live_auto_apply_ready` 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.",
            "- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.",
        ]
    )
    runtime_apply_bridge_markdown_path(target_date).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_runtime_apply_bridge_report(target_date: str) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_runtime_apply_bridge_report(target_date)
    for item in report.get("candidates") or []:
        if not isinstance(item, dict) or item.get("family") != GREENFIELD_REAL_ENV_FAMILY:
            continue
        policy = item.get("greenfield_policy") if isinstance(item.get("greenfield_policy"), dict) else {}
        policy_file = str(item.get("greenfield_policy_file") or "")
        if policy and policy_file:
            path = Path(policy_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")
    runtime_apply_bridge_report_path(target_date).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_markdown(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build LDM runtime apply bridge report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = write_runtime_apply_bridge_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get("status") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
