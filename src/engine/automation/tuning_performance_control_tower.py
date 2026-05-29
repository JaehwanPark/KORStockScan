"""Build a one-page tuning performance control tower report."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


REPORT_TYPE = "tuning_performance_control_tower"
SCHEMA_VERSION = 1
REPORT_ROOT_DIR = DATA_DIR / "report"
REPORT_DIR = REPORT_ROOT_DIR / REPORT_TYPE
APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"
SCALP_SIM_AUTO_APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "sim_auto_approvals"
SCALP_SIM_POLICY_DIR = DATA_DIR / "threshold_cycle" / "scalp_sim_policies"

SOURCE_SPECS: dict[str, tuple[Path, str]] = {
    "threshold_cycle_ev": (REPORT_ROOT_DIR / "threshold_cycle_ev", "threshold_cycle_ev"),
    "runtime_approval_summary": (REPORT_ROOT_DIR / "runtime_approval_summary", "runtime_approval_summary"),
    "runtime_apply_bridge": (REPORT_ROOT_DIR / "runtime_apply_bridge", "runtime_apply_bridge"),
    "lifecycle_decision_matrix": (REPORT_ROOT_DIR / "lifecycle_decision_matrix", "lifecycle_decision_matrix"),
    "lifecycle_bucket_discovery": (REPORT_ROOT_DIR / "lifecycle_bucket_discovery", "lifecycle_bucket_discovery"),
    "swing_lifecycle_decision_matrix": (
        REPORT_ROOT_DIR / "swing_lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
    ),
    "swing_lifecycle_bucket_discovery": (
        REPORT_ROOT_DIR / "swing_lifecycle_bucket_discovery",
        "swing_lifecycle_bucket_discovery",
    ),
    "code_improvement_workorder": (
        REPORT_ROOT_DIR / "code_improvement_workorder",
        "code_improvement_workorder",
    ),
}

PROGRESS_KEYS: dict[str, tuple[str, ...]] = {
    "lifecycle_bucket_discovery": (
        "candidate_count",
        "surfaced_candidate_count",
        "sim_auto_approved_count",
        "live_auto_apply_ready_count",
        "new_bucket_candidate_count",
        "code_patch_required_count",
        "automation_handoff_gap_count",
        "parent_bucket_count",
        "selected_parent_level",
        "parent_granularity_status",
        "absorbed_sample_count",
        "child_conflict_warning_count",
    ),
    "lifecycle_decision_matrix": (
        "total_rows",
        "joined_rows",
        "policy_pass_count",
        "promote_ready_count",
        "lifecycle_flow_bucket_count",
        "lifecycle_flow_complete_count",
        "complete_flow_count",
        "incomplete_flow_count",
        "lifecycle_flow_runtime_candidate_count",
        "lifecycle_flow_workorder_count",
        "join_contract_blocked",
        "top_incomplete_reason",
        "holding_bucket_count",
        "holding_bucket_workorder_count",
        "exit_bucket_count",
        "exit_bucket_workorder_count",
        "identity_missing_count",
        "identity_join_rate",
        "complete_flow_rate",
        "entry_bucket_runtime_candidate_count",
        "scale_in_bucket_runtime_candidate_count",
        "overnight_bucket_runtime_candidate_count",
        "scale_in_bucket_workorder_count",
        "overnight_bucket_workorder_count",
    ),
    "swing_lifecycle_decision_matrix": (
        "total_rows",
        "probe_rows",
        "discovery_rows",
        "labeled_rows",
        "pending_future_quote_count",
        "sim_auto_candidate_count",
        "workorder_count",
    ),
    "swing_lifecycle_bucket_discovery": (
        "candidate_count",
        "surfaced_candidate_count",
        "sim_auto_approved_count",
        "source_only_keep_collecting_count",
        "code_patch_required_count",
        "automation_handoff_gap_count",
    ),
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _source_path(label: str, target_date: str) -> Path:
    directory, prefix = SOURCE_SPECS[label]
    return directory / f"{prefix}_{target_date}.json"


def _apply_plan_path(target_date: str) -> Path:
    return APPLY_PLAN_DIR / f"threshold_apply_{target_date}.json"


def _scalp_sim_auto_approval_path(target_date: str) -> Path:
    return SCALP_SIM_AUTO_APPROVAL_DIR / f"scalp_sim_auto_approval_{target_date}.json"


def _scalp_sim_policy_catalog_path(target_date: str) -> Path:
    return SCALP_SIM_POLICY_DIR / f"scalp_sim_policy_catalog_{target_date}.json"


def _postclose_verifier_path(target_date: str) -> Path:
    return REPORT_ROOT_DIR / "threshold_cycle_postclose_verification" / f"threshold_cycle_postclose_verification_{target_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary")
    return summary if isinstance(summary, dict) else {}


def _artifact_status(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "json_valid": bool(payload),
        "generated_at": payload.get("generated_at"),
        "report_type": payload.get("report_type"),
    }


def _previous_report(label: str, target_date: str) -> tuple[str | None, Path | None, dict[str, Any]]:
    directory, prefix = SOURCE_SPECS[label]
    candidates: list[tuple[str, Path]] = []
    for path in directory.glob(f"{prefix}_*.json"):
        match = re.fullmatch(rf"{re.escape(prefix)}_(\d{{4}}-\d{{2}}-\d{{2}})\.json", path.name)
        if not match:
            continue
        current_date = match.group(1)
        if current_date < target_date:
            candidates.append((current_date, path))
    if not candidates:
        return None, None, {}
    previous_date, previous_path = sorted(candidates)[-1]
    return previous_date, previous_path, _load_json(previous_path)


def _delta(current: dict[str, Any], previous: dict[str, Any], keys: tuple[str, ...]) -> dict[str, int | float | None]:
    out: dict[str, int | float | None] = {}
    for key in keys:
        current_value = current.get(key)
        previous_value = previous.get(key)
        if current_value is None or previous_value is None:
            out[key] = None
            continue
        if isinstance(current_value, float) or isinstance(previous_value, float):
            current_number = _safe_float(current_value)
            previous_number = _safe_float(previous_value)
            out[key] = None if current_number is None or previous_number is None else round(current_number - previous_number, 4)
        else:
            out[key] = _safe_int(current_value) - _safe_int(previous_value)
    return out


def _progress_section(
    *,
    label: str,
    target_date: str,
    payload: dict[str, Any],
    keys: tuple[str, ...],
) -> dict[str, Any]:
    current_summary = _summary(payload)
    previous_date, previous_path, previous_payload = _previous_report(label, target_date)
    previous_summary = _summary(previous_payload)
    return {
        "current_date": target_date,
        "previous_date": previous_date,
        "previous_path": str(previous_path) if previous_path else None,
        "status": current_summary.get("status"),
        "source_contract_status": current_summary.get("source_contract_status"),
        "current": {key: current_summary.get(key) for key in keys},
        "previous": {key: previous_summary.get(key) for key in keys} if previous_summary else {},
        "delta": _delta(current_summary, previous_summary, keys) if previous_summary else {},
        "state_counts": current_summary.get("state_counts") if isinstance(current_summary.get("state_counts"), dict) else {},
        "stage_counts": current_summary.get("stage_counts") if isinstance(current_summary.get("stage_counts"), dict) else {},
        "warnings": current_summary.get("warnings") if isinstance(current_summary.get("warnings"), list) else [],
    }


def _source_split_summary(daily_ev_summary: dict[str, Any]) -> dict[str, Any]:
    source_split = daily_ev_summary.get("source_split") if isinstance(daily_ev_summary.get("source_split"), dict) else {}
    out: dict[str, Any] = {}
    for label in ("real", "sim", "combined"):
        payload = source_split.get(label) if isinstance(source_split.get(label), dict) else {}
        out[label] = {
            "sample": _safe_int(payload.get("sample")),
            "avg_profit_rate": _safe_float(payload.get("avg_profit_rate")),
            "win_rate": _safe_float(payload.get("win_rate")),
            "downside_p10_profit_rate": _safe_float(payload.get("downside_p10_profit_rate")),
            "upside_p90_profit_rate": _safe_float(payload.get("upside_p90_profit_rate")),
        }
    out["real_family_candidate_authority"] = source_split.get("real_family_candidate_authority")
    out["sim_calibration_authority"] = source_split.get("sim_calibration_authority")
    out["combined_authority"] = source_split.get("combined_authority")
    return out


def _real_pnl_is_tuning_performance(apply_plan: dict[str, Any]) -> tuple[bool, str]:
    post_apply = apply_plan.get("post_apply_attribution") if isinstance(apply_plan.get("post_apply_attribution"), dict) else {}
    status = str(post_apply.get("status") or "").strip()
    if status in {"completed", "attributed", "pass"}:
        sample = max(
            _safe_int(post_apply.get("applied_sample_count")),
            _safe_int(post_apply.get("completed_trades")),
            _safe_int(post_apply.get("attributed_sample_count")),
        )
        if sample > 0:
            return True, "post_apply_attribution_completed"
    if not post_apply:
        return False, "post_apply_attribution_missing"
    return False, f"post_apply_attribution_not_ready:{status or 'unknown'}"


def _ev_authority(threshold_ev: dict[str, Any], apply_plan: dict[str, Any]) -> dict[str, Any]:
    daily = threshold_ev.get("daily_ev_summary") if isinstance(threshold_ev.get("daily_ev_summary"), dict) else {}
    real_is_tuning, reason = _real_pnl_is_tuning_performance(apply_plan)
    return {
        "completed_trades": _safe_int(daily.get("completed_trades")),
        "win_rate_pct": _safe_float(daily.get("win_rate_pct")),
        "avg_profit_rate_pct": _safe_float(daily.get("avg_profit_rate_pct")),
        "realized_pnl_krw": _safe_int(daily.get("realized_pnl_krw")),
        "source_split": _source_split_summary(daily),
        "warnings": threshold_ev.get("warnings") if isinstance(threshold_ev.get("warnings"), list) else [],
        "real_pnl_is_tuning_performance": real_is_tuning,
        "real_pnl_interpretation_reason": reason,
        "real_pnl_allowed_use": (
            "post_apply_attributed_live_candidate_result"
            if real_is_tuning
            else "diagnostic_only_until_post_apply_attribution_closes"
        ),
        "sim_allowed_use": "sim_policy_and_source_quality_progress_only",
        "combined_allowed_use": "diagnostic_only_not_live_conversion_evidence",
    }


def _selected_runtime(apply_plan: dict[str, Any], threshold_ev: dict[str, Any]) -> dict[str, Any]:
    runtime_apply = threshold_ev.get("runtime_apply") if isinstance(threshold_ev.get("runtime_apply"), dict) else {}
    selected = apply_plan.get("auto_apply_selected")
    if not isinstance(selected, list):
        selected = []
    return {
        "apply_plan_status": apply_plan.get("status"),
        "apply_mode": apply_plan.get("apply_mode"),
        "source_date": apply_plan.get("source_date"),
        "target_date": apply_plan.get("target_date"),
        "runtime_change": _safe_bool(apply_plan.get("runtime_change")),
        "threshold_ev_runtime_change": _safe_bool(runtime_apply.get("runtime_change")),
        "selected_family_count": len(selected),
        "selected_families": [str(item.get("family") or "") for item in selected if isinstance(item, dict)],
        "post_apply_attribution": apply_plan.get("post_apply_attribution")
        if isinstance(apply_plan.get("post_apply_attribution"), dict)
        else {},
    }


def _workorder_summary(code_workorder: dict[str, Any]) -> dict[str, Any]:
    summary = _summary(code_workorder)
    return {
        "selected_order_count": _safe_int(summary.get("selected_order_count")),
        "selected_decision_counts": summary.get("selected_decision_counts")
        if isinstance(summary.get("selected_decision_counts"), dict)
        else {},
        "selected_route_counts": summary.get("selected_route_counts")
        if isinstance(summary.get("selected_route_counts"), dict)
        else {},
        "selected_implement_now_route_count": _safe_int(summary.get("selected_implement_now_route_count")),
        "selected_unimplemented_runtime_effect_false_count": _safe_int(
            summary.get("selected_unimplemented_runtime_effect_false_count")
        ),
        "pattern_lab_ai_review_source_order_count": _safe_int(summary.get("pattern_lab_ai_review_source_order_count")),
        "pattern_lab_currentness_source_order_count": _safe_int(summary.get("pattern_lab_currentness_source_order_count")),
        "producer_gap_discovery_source_order_count": _safe_int(summary.get("producer_gap_discovery_source_order_count")),
        "stage_hook_workorder_discovery_source_order_count": _safe_int(
            summary.get("stage_hook_workorder_discovery_source_order_count")
        ),
        "interpretation": "workorder_intake_only_not_automatic_repo_change",
    }


def _runtime_summary(runtime_summary: dict[str, Any]) -> dict[str, Any]:
    summary = _summary(runtime_summary)
    return {
        "runtime_mutation_allowed": _safe_bool(runtime_summary.get("runtime_mutation_allowed")),
        "scalping_selected_auto_bounded_live": _safe_int(summary.get("scalping_selected_auto_bounded_live")),
        "lifecycle_bucket_discovery_live_auto_apply_ready_count": _safe_int(
            summary.get("lifecycle_bucket_discovery_live_auto_apply_ready_count")
        ),
        "lifecycle_bucket_discovery_surfaced_candidate_count": _safe_int(
            summary.get("lifecycle_bucket_discovery_surfaced_candidate_count")
        ),
        "swing_lifecycle_bucket_discovery_sim_auto_approved_count": _safe_int(
            summary.get("swing_lifecycle_bucket_discovery_sim_auto_approved_count")
        ),
        "pattern_lab_currentness_status": summary.get("pattern_lab_currentness_status"),
        "pattern_lab_ai_review_status": summary.get("pattern_lab_ai_review_status"),
        "producer_gap_discovery_status": summary.get("producer_gap_discovery_status"),
        "pattern_lab_propagation_status": summary.get("pattern_lab_propagation_status"),
        "warnings": runtime_summary.get("warnings") if isinstance(runtime_summary.get("warnings"), list) else [],
    }


def _window_discovery_path(target_date: str, suffix: str | None = None) -> Path:
    base_dir = REPORT_ROOT_DIR / "lifecycle_bucket_discovery"
    if suffix:
        return base_dir / f"lifecycle_bucket_discovery_{target_date}_{suffix}.json"
    return base_dir / f"lifecycle_bucket_discovery_{target_date}.json"


def _lifecycle_windows_payload(payload: dict[str, Any]) -> dict[str, Any]:
    windows = payload.get("lifecycle_bucket_windows") if isinstance(payload.get("lifecycle_bucket_windows"), dict) else {}
    return windows


def _window_item_from_payload(windows: dict[str, Any], suffix: str) -> dict[str, Any]:
    if suffix == "daily":
        item = windows.get("daily")
        return item if isinstance(item, dict) else {}
    window_items = windows.get("windows") if isinstance(windows.get("windows"), dict) else {}
    item = window_items.get(suffix)
    return item if isinstance(item, dict) else {}


def _window_role(suffix: str) -> str:
    if suffix == "daily":
        return "new_pattern_detection"
    if suffix == "mtd":
        return "promotion_confirmation"
    return "rolling_confirmation"


def _summary_window_item(
    *,
    suffix: str,
    source_item: dict[str, Any],
    fallback_payload: dict[str, Any],
    fallback_path: Path,
) -> dict[str, Any]:
    summary = _summary(fallback_payload)
    available = _safe_bool(source_item.get("available")) or bool(fallback_payload)
    artifact = source_item.get("artifact") or (str(fallback_path) if fallback_path.exists() else None)
    return {
        "artifact": artifact,
        "available": available,
        "window_role": source_item.get("window_role") or _window_role(suffix),
        "window_policy": source_item.get("window_policy") or fallback_payload.get("window_policy") or summary.get("source_window_policy") or ("daily_only" if suffix == "daily" else suffix),
        "status": source_item.get("status") or summary.get("status") or ("missing" if not available else "unknown"),
        "source_contract_status": source_item.get("source_contract_status") or summary.get("source_contract_status"),
        "ai_two_pass_review_status": source_item.get("ai_two_pass_review_status") or summary.get("ai_two_pass_review_status"),
        "parent_bucket_count": _safe_int(source_item.get("parent_bucket_count") or summary.get("parent_bucket_count")),
        "selected_parent_level": source_item.get("selected_parent_level") or summary.get("selected_parent_level"),
        "parent_granularity_status": source_item.get("parent_granularity_status") or summary.get("parent_granularity_status"),
        "absorbed_sample_count": _safe_int(source_item.get("absorbed_sample_count") or summary.get("absorbed_sample_count")),
        "child_conflict_warning_count": _safe_int(
            source_item.get("child_conflict_warning_count") or summary.get("child_conflict_warning_count")
        ),
        "live_auto_apply_ready_count": _safe_int(
            source_item.get("live_auto_apply_ready_count") or summary.get("live_auto_apply_ready_count")
        ),
    }


def _lifecycle_bucket_window_summary(
    target_date: str,
    *,
    threshold_ev: dict[str, Any],
    runtime_summary: dict[str, Any],
    daily_lifecycle_bucket: dict[str, Any],
) -> dict[str, Any]:
    ev_windows = _lifecycle_windows_payload(threshold_ev)
    runtime_windows = _lifecycle_windows_payload(runtime_summary)
    promotion_window = ev_windows.get("promotion_window") or runtime_windows.get("promotion_window") or "mtd"
    confirmation_windows = (
        ev_windows.get("confirmation_windows")
        if isinstance(ev_windows.get("confirmation_windows"), list)
        else runtime_windows.get("confirmation_windows")
        if isinstance(runtime_windows.get("confirmation_windows"), list)
        else ["rolling5d", "rolling10d"]
    )
    daily_path = _window_discovery_path(target_date)
    daily_item = _window_item_from_payload(ev_windows, "daily") or _window_item_from_payload(runtime_windows, "daily")
    windows: dict[str, Any] = {
        "daily": _summary_window_item(
            suffix="daily",
            source_item=daily_item,
            fallback_payload=daily_lifecycle_bucket,
            fallback_path=daily_path,
        ),
    }
    for suffix in ("rolling5d", "rolling10d", "mtd"):
        path = _window_discovery_path(target_date, suffix)
        source_item = _window_item_from_payload(ev_windows, suffix) or _window_item_from_payload(runtime_windows, suffix)
        windows[suffix] = _summary_window_item(
            suffix=suffix,
            source_item=source_item,
            fallback_payload=_load_json(path),
            fallback_path=path,
        )
    return {
        "promotion_window": promotion_window,
        "confirmation_windows": confirmation_windows,
        "daily": windows["daily"],
        "windows": {key: value for key, value in windows.items() if key != "daily"},
        "warnings": [
            str(item)
            for source in (ev_windows, runtime_windows)
            for item in (source.get("warnings") if isinstance(source.get("warnings"), list) else [])
            if str(item)
        ],
    }


def _bridge_summary(bridge_report: dict[str, Any]) -> dict[str, Any]:
    summary = _summary(bridge_report)
    promotion_contract_passed = summary.get("lifecycle_bucket_promotion_contract_passed")
    return {
        "status": bridge_report.get("status"),
        "candidate_count": _safe_int(summary.get("candidate_count")),
        "live_auto_apply_ready_count": _safe_int(summary.get("live_auto_apply_ready_count")),
        "greenfield_real_env_ready_count": _safe_int(summary.get("greenfield_real_env_ready_count")),
        "greenfield_policy_emit_state": summary.get("greenfield_policy_emit_state"),
        "lifecycle_bucket_promotion_window": summary.get("lifecycle_bucket_promotion_window"),
        "lifecycle_bucket_promotion_contract_passed": (
            promotion_contract_passed
            if isinstance(promotion_contract_passed, bool)
            else _safe_bool(promotion_contract_passed)
        ),
        "warnings": bridge_report.get("warnings") if isinstance(bridge_report.get("warnings"), list) else [],
    }


def _postclose_verifier_summary(
    verifier_report: dict[str, Any],
    artifact_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_status = artifact_status or {}
    if not verifier_report:
        if artifact_status.get("exists"):
            status = "parse_failed"
            window_status = "parse_failed"
            warnings = ["threshold_cycle_postclose_verification_parse_failed"]
        else:
            status = "pending_not_generated_yet"
            window_status = "pending_not_generated_yet"
            warnings = ["threshold_cycle_postclose_verification_pending"]
        return {
            "status": status,
            "lifecycle_bucket_windows": {
                "status": window_status,
                "checked": False,
                "missing": [],
                "warnings": warnings,
            },
        }
    windows = (
        verifier_report.get("lifecycle_bucket_windows")
        if isinstance(verifier_report.get("lifecycle_bucket_windows"), dict)
        else {}
    )
    return {
        "status": verifier_report.get("status"),
        "lifecycle_bucket_windows": {
            "status": windows.get("status"),
            "checked": bool(windows.get("checked")),
            "missing": windows.get("missing") if isinstance(windows.get("missing"), list) else [],
            "warnings": windows.get("warnings") if isinstance(windows.get("warnings"), list) else [],
        },
    }


def _scalp_sim_control_tower_summary(approval: dict[str, Any], catalog_path: Path) -> dict[str, Any]:
    source_status = approval.get("source_status") if isinstance(approval.get("source_status"), dict) else {}
    runtime_bridge = source_status.get("runtime_apply_bridge") if isinstance(source_status.get("runtime_apply_bridge"), dict) else {}
    return {
        "approved": _safe_bool(approval.get("approved")),
        "approved_policy_count": _safe_int(approval.get("approved_policy_count")),
        "approved_source_ids": approval.get("approved_source_ids") if isinstance(approval.get("approved_source_ids"), list) else [],
        "catalog": str(catalog_path),
        "catalog_exists": catalog_path.exists(),
        "runtime_bridge_live_auto_apply_ready_count": _safe_int(runtime_bridge.get("live_auto_apply_ready_count")),
        "blocked_reasons": approval.get("blocked_reasons") if isinstance(approval.get("blocked_reasons"), list) else [],
        "decision_authority": approval.get("decision_authority"),
        "runtime_effect": _safe_bool(approval.get("runtime_effect")),
        "allowed_runtime_apply": _safe_bool(approval.get("allowed_runtime_apply")),
    }


def _top_lifecycle_candidates(threshold_ev: dict[str, Any], lifecycle_bucket: dict[str, Any]) -> list[dict[str, Any]]:
    embedded = threshold_ev.get("lifecycle_bucket_discovery")
    top = embedded.get("top_surfaced") if isinstance(embedded, dict) and isinstance(embedded.get("top_surfaced"), list) else None
    raw = top if top is not None else lifecycle_bucket.get("surfaced_candidates")
    if not isinstance(raw, list):
        return []
    rendered = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        rendered.append(
            {
                "bucket_id": item.get("bucket_id") or item.get("candidate_id"),
                "stage": item.get("stage"),
                "classification_state": item.get("classification_state"),
                "recommended_action": item.get("recommended_action"),
                "joined_sample": _safe_int(item.get("joined_sample")),
                "source_quality_adjusted_ev_pct": _safe_float(item.get("source_quality_adjusted_ev_pct")),
                "live_auto_apply_family": item.get("live_auto_apply_family"),
            }
        )
    return rendered


def _primary_verdict(
    *,
    lifecycle_bucket_progress: dict[str, Any],
    swing_bucket_progress: dict[str, Any],
    ev_authority: dict[str, Any],
    warnings: list[str],
    lifecycle_bucket_windows: dict[str, Any],
    bridge_summary: dict[str, Any],
    verifier_summary: dict[str, Any],
) -> str:
    current_lifecycle = lifecycle_bucket_progress.get("current")
    current_swing = swing_bucket_progress.get("current")
    lifecycle_live = _safe_int(
        current_lifecycle.get("live_auto_apply_ready_count") if isinstance(current_lifecycle, dict) else 0
    )
    lifecycle_new_bucket = _safe_int(
        current_lifecycle.get("new_bucket_candidate_count") if isinstance(current_lifecycle, dict) else 0
    )
    lifecycle_sim = _safe_int(current_lifecycle.get("sim_auto_approved_count") if isinstance(current_lifecycle, dict) else 0)
    swing_sim = _safe_int(current_swing.get("sim_auto_approved_count") if isinstance(current_swing, dict) else 0)
    if warnings:
        return "source_gap_review_required"
    verifier_windows = (
        verifier_summary.get("lifecycle_bucket_windows")
        if isinstance(verifier_summary.get("lifecycle_bucket_windows"), dict)
        else {}
    )
    if verifier_summary.get("status") == "fail" or verifier_windows.get("status") == "fail":
        return "postclose_verifier_blocked"
    bridge_live = _safe_int(bridge_summary.get("live_auto_apply_ready_count"))
    if bridge_live > 0 and bridge_summary.get("lifecycle_bucket_promotion_contract_passed") is True:
        return "bridge_live_bucket_ready"
    promotion_window = str(lifecycle_bucket_windows.get("promotion_window") or "mtd")
    promotion = (lifecycle_bucket_windows.get("windows") or {}).get(promotion_window)
    if isinstance(promotion, dict):
        promotion_live = _safe_int(promotion.get("live_auto_apply_ready_count"))
        promotion_confirmed = (
            promotion.get("source_contract_status") == "pass"
            and promotion.get("parent_granularity_status") == "target_pass"
            and promotion_live > 0
        )
        if promotion_confirmed:
            return "promotion_confirmed_waiting_bridge"
    if lifecycle_live > 0 or lifecycle_new_bucket > 0:
        return "daily_detected_cumulative_missing"
    if lifecycle_sim + swing_sim > 0:
        return "sim_progress_no_live_bucket"
    if ev_authority.get("real_pnl_is_tuning_performance"):
        return "post_apply_performance_attributed"
    return "observe_only_no_new_tuning_progress"


def _markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    ldm_bucket = report["ldm_progression"]["lifecycle_bucket_discovery"]
    ldm_matrix = report["ldm_progression"]["lifecycle_decision_matrix"]
    swing_matrix = report["swing_progression"]["swing_lifecycle_decision_matrix"]
    swing_bucket = report["swing_progression"]["swing_lifecycle_bucket_discovery"]
    ev = report["ev_authority"]
    workorder = report["workorder"]
    runtime = report["runtime_approval"]
    scalp_sim_auto = report.get("scalp_sim_auto_approval") if isinstance(report.get("scalp_sim_auto_approval"), dict) else {}
    bucket_windows = (
        report.get("lifecycle_bucket_window_summary")
        if isinstance(report.get("lifecycle_bucket_window_summary"), dict)
        else {}
    )
    bridge = report.get("bridge_summary") if isinstance(report.get("bridge_summary"), dict) else {}
    verifier = report.get("postclose_verifier_summary") if isinstance(report.get("postclose_verifier_summary"), dict) else {}
    daily_window = bucket_windows.get("daily") if isinstance(bucket_windows.get("daily"), dict) else {}
    promotion_window = str(bucket_windows.get("promotion_window") or "mtd")
    promotion_summary = (
        (bucket_windows.get("windows") or {}).get(promotion_window)
        if isinstance(bucket_windows.get("windows"), dict)
        else {}
    )
    verifier_windows = (
        verifier.get("lifecycle_bucket_windows")
        if isinstance(verifier.get("lifecycle_bucket_windows"), dict)
        else {}
    )

    def current(section: dict[str, Any], key: str) -> Any:
        payload = section.get("current") if isinstance(section.get("current"), dict) else {}
        return payload.get(key)

    def delta(section: dict[str, Any], key: str) -> Any:
        payload = section.get("delta") if isinstance(section.get("delta"), dict) else {}
        value = payload.get(key)
        if value is None:
            return "n/a"
        return f"{value:+d}" if isinstance(value, int) else f"{value:+.4f}"

    def inline_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    lines = [
        f"# Tuning Performance Control Tower - {report['date']}",
        "",
        "## 판정",
        "",
        f"- 판정: `{summary['primary_verdict']}`",
        f"- bridge_policy_emit_state: `{summary.get('bridge_policy_emit_state') or '-'}`, "
        f"promotion_window: `{summary.get('promotion_window') or '-'}`, "
        f"verifier_status: `{summary.get('verifier_status') or '-'}`, "
        f"lifecycle_bucket_windows_status: `{summary.get('lifecycle_bucket_windows_status') or '-'}`.",
        f"- 근거: LDM `sim_auto_approved={summary['lifecycle_sim_auto_approved_count']}` "
        f"(`{delta(ldm_bucket, 'sim_auto_approved_count')}`), "
        f"`live_auto_apply_ready={summary['lifecycle_live_auto_apply_ready_count']}` "
        f"(`{delta(ldm_bucket, 'live_auto_apply_ready_count')}`), "
        f"swing sim-auto `{summary['swing_sim_auto_approved_count']}` "
        f"(`{delta(swing_bucket, 'sim_auto_approved_count')}`).",
        f"- 실현손익 해석: `real_pnl_is_tuning_performance={str(ev['real_pnl_is_tuning_performance']).lower()}` "
        f"({ev['real_pnl_interpretation_reason']}).",
        "- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, "
        "`pending_future_quote_count`, selected workorder backlog만 먼저 본다.",
        "",
        "## LDM 승격/후보",
        "",
        f"- Live-ready split: daily_discovery `{summary.get('daily_discovery_live_auto_apply_ready_count')}`, "
        f"promotion_window `{summary.get('promotion_window_live_auto_apply_ready_count')}`, "
        f"bridge_ready `{summary.get('bridge_live_auto_apply_ready_count')}`.",
        f"- Parent bucket: daily parent_granularity_status `{daily_window.get('parent_bucket_count')}`/"
        f"`{daily_window.get('parent_granularity_status')}`, "
        f"{promotion_window} `{promotion_summary.get('parent_bucket_count') if isinstance(promotion_summary, dict) else None}`/"
        f"`{promotion_summary.get('parent_granularity_status') if isinstance(promotion_summary, dict) else None}`, "
        f"absorbed_sample `{promotion_summary.get('absorbed_sample_count') if isinstance(promotion_summary, dict) else None}`, "
        f"conflict_children `{promotion_summary.get('child_conflict_warning_count') if isinstance(promotion_summary, dict) else None}`.",
        f"- Bridge/verifier: greenfield_policy_emit_state `{bridge.get('greenfield_policy_emit_state') or '-'}`, "
        f"promotion_contract_passed `{bridge.get('lifecycle_bucket_promotion_contract_passed')}`, "
        f"verifier_status `{verifier.get('status') or '-'}`, "
        f"verifier_missing `{inline_json(verifier_windows.get('missing') or [])}`.",
        f"- Lifecycle bucket: candidates `{current(ldm_bucket, 'candidate_count')}` "
        f"(`{delta(ldm_bucket, 'candidate_count')}`), surfaced `{current(ldm_bucket, 'surfaced_candidate_count')}` "
        f"(`{delta(ldm_bucket, 'surfaced_candidate_count')}`), sim-auto "
        f"`{current(ldm_bucket, 'sim_auto_approved_count')}` "
        f"(`{delta(ldm_bucket, 'sim_auto_approved_count')}`), live-ready "
        f"`{current(ldm_bucket, 'live_auto_apply_ready_count')}` "
        f"(`{delta(ldm_bucket, 'live_auto_apply_ready_count')}`).",
        f"- Lifecycle matrix: rows `{current(ldm_matrix, 'total_rows')}` "
        f"(`{delta(ldm_matrix, 'total_rows')}`), joined `{current(ldm_matrix, 'joined_rows')}` "
        f"(`{delta(ldm_matrix, 'joined_rows')}`), promote-ready "
        f"`{current(ldm_matrix, 'promote_ready_count')}` "
        f"(`{delta(ldm_matrix, 'promote_ready_count')}`).",
        f"- Lifecycle flow: buckets `{current(ldm_matrix, 'lifecycle_flow_bucket_count')}` "
        f"(`{delta(ldm_matrix, 'lifecycle_flow_bucket_count')}`), complete "
        f"`{current(ldm_matrix, 'lifecycle_flow_complete_count')}` "
        f"(`{delta(ldm_matrix, 'lifecycle_flow_complete_count')}`), runtime "
        f"`{current(ldm_matrix, 'lifecycle_flow_runtime_candidate_count')}` "
        f"(`{delta(ldm_matrix, 'lifecycle_flow_runtime_candidate_count')}`), workorders "
        f"`{current(ldm_matrix, 'lifecycle_flow_workorder_count')}` "
        f"(`{delta(ldm_matrix, 'lifecycle_flow_workorder_count')}`).",
        f"- Holding/exit buckets: holding `{current(ldm_matrix, 'holding_bucket_count')}` "
        f"(`{delta(ldm_matrix, 'holding_bucket_count')}`), exit `{current(ldm_matrix, 'exit_bucket_count')}` "
        f"(`{delta(ldm_matrix, 'exit_bucket_count')}`), workorders "
        f"`{current(ldm_matrix, 'holding_bucket_workorder_count')}`/`{current(ldm_matrix, 'exit_bucket_workorder_count')}`.",
        f"- Lifecycle identity: missing `{current(ldm_matrix, 'identity_missing_count')}` "
        f"(`{delta(ldm_matrix, 'identity_missing_count')}`), join_rate "
        f"`{current(ldm_matrix, 'identity_join_rate')}`, complete_flow_rate "
        f"`{current(ldm_matrix, 'complete_flow_rate')}`.",
        f"- Lifecycle join contract: blocked `{str(current(ldm_matrix, 'join_contract_blocked')).lower()}`, "
        f"incomplete `{current(ldm_matrix, 'incomplete_flow_count')}`, top reason "
        f"`{current(ldm_matrix, 'top_incomplete_reason')}`.",
        f"- Swing matrix: rows `{current(swing_matrix, 'total_rows')}` "
        f"(`{delta(swing_matrix, 'total_rows')}`), probe `{current(swing_matrix, 'probe_rows')}` "
        f"(`{delta(swing_matrix, 'probe_rows')}`), pending future quotes "
        f"`{current(swing_matrix, 'pending_future_quote_count')}` "
        f"(`{delta(swing_matrix, 'pending_future_quote_count')}`).",
        f"- Swing bucket: sim-auto `{current(swing_bucket, 'sim_auto_approved_count')}` "
        f"(`{delta(swing_bucket, 'sim_auto_approved_count')}`), code-patch "
        f"`{current(swing_bucket, 'code_patch_required_count')}` "
        f"(`{delta(swing_bucket, 'code_patch_required_count')}`).",
        f"- Scalp sim control tower: approved `{str(scalp_sim_auto.get('approved')).lower()}`, "
        f"policies `{scalp_sim_auto.get('approved_policy_count')}`, "
        f"sources `{inline_json(scalp_sim_auto.get('approved_source_ids') or [])}`, "
        f"bridge live-ready summary `{scalp_sim_auto.get('runtime_bridge_live_auto_apply_ready_count')}`.",
        "",
        "## EV 해석",
        "",
        f"- Daily completed trades `{ev['completed_trades']}`, win-rate `{ev['win_rate_pct']}`, "
        f"avg profit pct `{ev['avg_profit_rate_pct']}`, realized PnL KRW `{ev['realized_pnl_krw']}`.",
        f"- Real split sample `{ev['source_split']['real']['sample']}`, avg `{ev['source_split']['real']['avg_profit_rate']}`, "
        f"win-rate `{ev['source_split']['real']['win_rate']}`.",
        f"- Sim split sample `{ev['source_split']['sim']['sample']}`, avg `{ev['source_split']['sim']['avg_profit_rate']}`, "
        f"win-rate `{ev['source_split']['sim']['win_rate']}`.",
        f"- EV warnings: `{', '.join(ev['warnings']) if ev['warnings'] else '-'}`.",
        "",
        "## Workorder",
        "",
        f"- selected orders `{workorder['selected_order_count']}`, selected decisions "
        f"`{inline_json(workorder['selected_decision_counts'])}`, routes `{inline_json(workorder['selected_route_counts'])}`.",
        f"- pattern lab AI review source orders `{workorder['pattern_lab_ai_review_source_order_count']}`, "
        f"pattern lab currentness source orders `{workorder['pattern_lab_currentness_source_order_count']}`.",
        "- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. "
        "사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.",
        "",
        "## Runtime Summary",
        "",
        f"- runtime mutation allowed `{str(runtime['runtime_mutation_allowed']).lower()}`; "
        f"scalping selected auto-bounded-live `{runtime['scalping_selected_auto_bounded_live']}`.",
        f"- pattern lab currentness `{runtime['pattern_lab_currentness_status']}`, "
        f"AI review `{runtime['pattern_lab_ai_review_status']}`, propagation `{runtime['pattern_lab_propagation_status']}`, "
        f"producer gap `{runtime['producer_gap_discovery_status']}`.",
        "",
        "## Source",
        "",
    ]
    for label, status in report["sources"].items():
        lines.append(f"- {label}: `{status['path']}` exists={str(status['exists']).lower()} json_valid={str(status['json_valid']).lower()}")
    lines.append("")
    return "\n".join(lines)


def build_tuning_performance_control_tower(target_date: str) -> dict[str, Any]:
    payloads: dict[str, dict[str, Any]] = {}
    sources: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for label in SOURCE_SPECS:
        path = _source_path(label, target_date)
        payload = _load_json(path)
        payloads[label] = payload
        sources[label] = _artifact_status(path, payload)
        if not path.exists():
            warnings.append(f"{label}_missing")
        elif not payload:
            warnings.append(f"{label}_parse_failed")

    apply_path = _apply_plan_path(target_date)
    apply_plan = _load_json(apply_path)
    sources["threshold_apply"] = _artifact_status(apply_path, apply_plan)
    if not apply_path.exists():
        warnings.append("threshold_apply_missing")
    elif not apply_plan:
        warnings.append("threshold_apply_parse_failed")

    verifier_path = _postclose_verifier_path(target_date)
    verifier_payload = _load_json(verifier_path)
    payloads["threshold_cycle_postclose_verification"] = verifier_payload
    sources["threshold_cycle_postclose_verification"] = _artifact_status(verifier_path, verifier_payload)
    if verifier_path.exists() and not verifier_payload:
        warnings.append("threshold_cycle_postclose_verification_parse_failed")

    scalp_sim_auto_path = _scalp_sim_auto_approval_path(target_date)
    scalp_sim_auto = _load_json(scalp_sim_auto_path)
    sources["scalp_sim_auto_approval"] = _artifact_status(scalp_sim_auto_path, scalp_sim_auto)
    scalp_sim_catalog_path = _scalp_sim_policy_catalog_path(target_date)
    sources["scalp_sim_policy_catalog"] = _artifact_status(scalp_sim_catalog_path, _load_json(scalp_sim_catalog_path))

    threshold_ev = payloads["threshold_cycle_ev"]
    ldm_bucket = _progress_section(
        label="lifecycle_bucket_discovery",
        target_date=target_date,
        payload=payloads["lifecycle_bucket_discovery"],
        keys=PROGRESS_KEYS["lifecycle_bucket_discovery"],
    )
    ldm_matrix = _progress_section(
        label="lifecycle_decision_matrix",
        target_date=target_date,
        payload=payloads["lifecycle_decision_matrix"],
        keys=PROGRESS_KEYS["lifecycle_decision_matrix"],
    )
    swing_matrix = _progress_section(
        label="swing_lifecycle_decision_matrix",
        target_date=target_date,
        payload=payloads["swing_lifecycle_decision_matrix"],
        keys=PROGRESS_KEYS["swing_lifecycle_decision_matrix"],
    )
    swing_bucket = _progress_section(
        label="swing_lifecycle_bucket_discovery",
        target_date=target_date,
        payload=payloads["swing_lifecycle_bucket_discovery"],
        keys=PROGRESS_KEYS["swing_lifecycle_bucket_discovery"],
    )
    ev = _ev_authority(threshold_ev, apply_plan)
    runtime = _runtime_summary(payloads["runtime_approval_summary"])
    lifecycle_bucket_windows = _lifecycle_bucket_window_summary(
        target_date,
        threshold_ev=threshold_ev,
        runtime_summary=payloads["runtime_approval_summary"],
        daily_lifecycle_bucket=payloads["lifecycle_bucket_discovery"],
    )
    bridge = _bridge_summary(payloads["runtime_apply_bridge"])
    verifier = _postclose_verifier_summary(
        payloads["threshold_cycle_postclose_verification"],
        sources["threshold_cycle_postclose_verification"],
    )
    workorder = _workorder_summary(payloads["code_improvement_workorder"])
    current_ldm_bucket = ldm_bucket.get("current") if isinstance(ldm_bucket.get("current"), dict) else {}
    current_swing_bucket = swing_bucket.get("current") if isinstance(swing_bucket.get("current"), dict) else {}
    daily_bucket_summary = lifecycle_bucket_windows.get("daily") if isinstance(lifecycle_bucket_windows.get("daily"), dict) else {}
    promotion_window = str(lifecycle_bucket_windows.get("promotion_window") or "mtd")
    promotion_summary = (
        (lifecycle_bucket_windows.get("windows") or {}).get(promotion_window)
        if isinstance(lifecycle_bucket_windows.get("windows"), dict)
        else {}
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "operator_read_only_tuning_performance_summary",
        "metric_role": "diagnostic_summary",
        "primary_decision_metric": "live_auto_apply_ready_count_then_post_apply_attribution",
        "source_quality_gate": "all source artifacts json_valid and explicit source warnings separated",
        "forbidden_uses": [
            "real order enablement",
            "threshold mutation",
            "provider change",
            "bot restart",
            "position cap release",
            "live conversion from sim or combined EV alone",
        ],
        "summary": {
            "primary_verdict": _primary_verdict(
                lifecycle_bucket_progress=ldm_bucket,
                swing_bucket_progress=swing_bucket,
                ev_authority=ev,
                warnings=warnings,
                lifecycle_bucket_windows=lifecycle_bucket_windows,
                bridge_summary=bridge,
                verifier_summary=verifier,
            ),
            "legacy_daily_discovery_verdict": (
                "live_bucket_ready"
                if _safe_int(current_ldm_bucket.get("live_auto_apply_ready_count")) > 0
                else None
            ),
            "legacy_primary_verdict_alias": (
                "live_bucket_ready"
                if _safe_int(current_ldm_bucket.get("live_auto_apply_ready_count")) > 0
                else None
            ),
            "lifecycle_sim_auto_approved_count": _safe_int(current_ldm_bucket.get("sim_auto_approved_count")),
            "lifecycle_live_auto_apply_ready_count": _safe_int(current_ldm_bucket.get("live_auto_apply_ready_count")),
            "daily_discovery_live_auto_apply_ready_count": _safe_int(daily_bucket_summary.get("live_auto_apply_ready_count")),
            "promotion_window_live_auto_apply_ready_count": _safe_int(
                promotion_summary.get("live_auto_apply_ready_count") if isinstance(promotion_summary, dict) else 0
            ),
            "bridge_live_auto_apply_ready_count": _safe_int(bridge.get("live_auto_apply_ready_count")),
            "bridge_policy_emit_state": bridge.get("greenfield_policy_emit_state"),
            "promotion_window": promotion_window,
            "verifier_status": verifier.get("status"),
            "lifecycle_bucket_windows_status": (
                (verifier.get("lifecycle_bucket_windows") or {}).get("status")
                if isinstance(verifier.get("lifecycle_bucket_windows"), dict)
                else None
            ),
            "swing_sim_auto_approved_count": _safe_int(current_swing_bucket.get("sim_auto_approved_count")),
            "real_pnl_is_tuning_performance": ev["real_pnl_is_tuning_performance"],
            "source_artifact_warnings": warnings,
            "source_artifact_warning_count": len(warnings),
            "ev_warnings": ev["warnings"],
            "ev_warning_count": len(ev["warnings"]),
            "read_this_first": True,
        },
        "ldm_progression": {
            "lifecycle_decision_matrix": ldm_matrix,
            "lifecycle_bucket_discovery": ldm_bucket,
            "top_lifecycle_candidates": _top_lifecycle_candidates(threshold_ev, payloads["lifecycle_bucket_discovery"]),
        },
        "swing_progression": {
            "swing_lifecycle_decision_matrix": swing_matrix,
            "swing_lifecycle_bucket_discovery": swing_bucket,
        },
        "ev_authority": ev,
        "selected_runtime": _selected_runtime(apply_plan, threshold_ev),
        "runtime_approval": runtime,
        "lifecycle_bucket_window_summary": lifecycle_bucket_windows,
        "bridge_summary": bridge,
        "postclose_verifier_summary": verifier,
        "scalp_sim_auto_approval": _scalp_sim_control_tower_summary(scalp_sim_auto, scalp_sim_catalog_path),
        "workorder": workorder,
        "sources": sources,
        "warnings": warnings,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    args = parser.parse_args(argv)
    report = build_tuning_performance_control_tower(args.date)
    print(json.dumps({"date": args.date, "path": str(report_paths(args.date)[0]), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
