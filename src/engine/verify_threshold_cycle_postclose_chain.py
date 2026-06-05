"""Verify postclose artifact predecessor integrity and workorder lineage consistency."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import date, datetime, time as dtime
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    analytics_quarantine_reason,
    clean_baseline_policy,
    is_date_allowed,
    report_generated_before_clean_baseline,
    report_quarantine_reason,
)
from src.engine.automation.source_quality_hard_gate import (
    RUNTIME_APPLY_BOOL_FIELDS,
    RUNTIME_CANDIDATE_COUNT_FIELDS,
    RUNTIME_CANDIDATE_LIST_FIELDS,
    source_quality_preflight_blocked,
)
from src.engine.daily_threshold_cycle_report import REPORT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "logs" / "threshold_cycle_postclose_cron.log"
ANALYTICS_DIR = PROJECT_ROOT / "data" / "analytics"
VERIFY_DIR = REPORT_DIR / "threshold_cycle_postclose_verification"
ACTIVE_SIM_PRIORITY_OBSERVABLE_PREFIX_KEYS = {
    "entry_score_parent",
    "entry_source_parent",
    "submit_quality_parent",
}

_START_MARKER = "[START] threshold-cycle postclose"
_DONE_MARKER = "[DONE] threshold-cycle postclose"
_FAIL_MARKER = "[FAIL] threshold-cycle postclose"
_PAUSED_MARKER = "[PAUSED] threshold-cycle postclose"
_READY_RE = re.compile(
    r"artifact ready label=(?P<label>\S+) path=(?P<path>\S+) waited=(?P<waited>\d+)s(?: json_valid=(?P<json_valid>\w+))?"
)
_TIMEOUT_RE = re.compile(r"artifact wait timeout label=(?P<label>\S+) path=(?P<path>\S+) waited=(?P<waited>\d+)s")
_AI_RUNTIME_STATES = {
    "adjust_up",
    "adjust_down",
    "hold",
    "hold_no_edge",
}
_OPTIONAL_ARTIFACT_LABELS = {
    "buy_funnel_sentinel",
    "lifecycle_bucket_discovery",
    "lifecycle_decision_matrix_rolling5d",
    "lifecycle_bucket_discovery_rolling5d",
    "lifecycle_decision_matrix_rolling10d",
    "lifecycle_bucket_discovery_rolling10d",
    "lifecycle_decision_matrix_mtd",
    "lifecycle_bucket_discovery_mtd",
    "threshold_preopen_apply_next",
    "scalp_sim_policy_catalog",
    "swing_sim_policy_catalog",
    "observation_source_quality_audit",
    "ldm_hypothesis_parent_refinement",
    "key_lineage_ledger",
    "conversion_lane",
}
_AI_EXEMPT_RUNTIME_FAMILIES = {
    "latency_classifier_runtime_profile",
}
ENTRY_SUBMIT_DROUGHT_REQUIRED_ORDER_IDS = [
    "order_entry_submit_drought_auto_resolution",
    "order_entry_post_submit_contract_gap_review",
    "order_entry_broker_receipt_contract_gap_review",
    "order_entry_fill_quality_contract_gap_review",
    "order_entry_telegram_post_submit_contract_gap_review",
    "order_entry_source_taxonomy_contract_gap_review",
]


def verification_report_paths(target_date: str) -> tuple[Path, Path]:
    base = VERIFY_DIR / f"threshold_cycle_postclose_verification_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _has_runtime_applicable_candidate(value: Any) -> bool:
    if isinstance(value, list):
        return any(_has_runtime_applicable_candidate(item) for item in value)
    if not isinstance(value, dict):
        return False
    for key, item in value.items():
        if key in RUNTIME_CANDIDATE_LIST_FIELDS:
            return bool(item)
        if key in RUNTIME_CANDIDATE_COUNT_FIELDS:
            try:
                if int(float(item or 0)) > 0:
                    return True
            except Exception:
                pass
        if key in RUNTIME_APPLY_BOOL_FIELDS:
            if item is True:
                return True
        if _has_runtime_applicable_candidate(item):
            return True
    return False


def _source_quality_hard_block_status(
    preflight: dict[str, Any],
    *,
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    ldm_report: dict[str, Any],
    bridge_report: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    if not source_quality_preflight_blocked(preflight):
        return {
            "status": "pass",
            "tuning_input_allowed": True,
            "candidate_violation_sources": [],
            "workorder_handoff_present": True,
        }
    summary = preflight.get("summary") if isinstance(preflight.get("summary"), dict) else {}
    candidate_sources = [
        name
        for name, payload in (
            ("threshold_cycle_ev", ev_report),
            ("runtime_approval_summary", runtime_summary),
            ("lifecycle_decision_matrix", ldm_report),
            ("runtime_apply_bridge", bridge_report),
        )
        if _has_runtime_applicable_candidate(payload)
    ]
    orders = workorder.get("orders") if isinstance(workorder.get("orders"), list) else []
    non_selected = workorder.get("non_selected_orders") if isinstance(workorder.get("non_selected_orders"), list) else []
    workorder_handoff_present = any(
        isinstance(item, dict)
        and (
            item.get("order_id") == "order_observation_source_quality_hard_block_contract_gap"
            or item.get("improvement_type") == "source_quality_hard_block_contract_gap"
            or item.get("route") == "source_quality_gap"
        )
        for item in [*orders, *non_selected]
    )
    return {
        "status": "fail" if candidate_sources or not workorder_handoff_present else "pass",
        "tuning_input_allowed": False,
        "candidate_violation_sources": candidate_sources,
        "workorder_handoff_present": workorder_handoff_present,
        "hard_blocking_contract_gap_count": summary.get("hard_blocking_contract_gap_count")
        or preflight.get("hard_blocking_contract_gap_count"),
        "hard_blocking_stages": summary.get("hard_blocking_stages") or preflight.get("hard_blocking_stages") or [],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _raw_row_exclusion_handoff_status(
    preflight: dict[str, Any],
    *,
    workorder: dict[str, Any],
) -> dict[str, Any]:
    raw_exclusion = preflight.get("raw_row_exclusion") if isinstance(preflight.get("raw_row_exclusion"), dict) else {}
    excluded_row_count = int(raw_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count <= 0:
        return {
            "status": "pass",
            "excluded_row_count": 0,
            "workorder_handoff_present": True,
        }
    orders = workorder.get("orders") if isinstance(workorder.get("orders"), list) else []
    non_selected = workorder.get("non_selected_orders") if isinstance(workorder.get("non_selected_orders"), list) else []
    selected_matching_orders = [
        item
        for item in orders
        if isinstance(item, dict)
        and (
            item.get("order_id") == "order_observation_source_quality_raw_row_exclusion_producer_gap"
            or item.get("improvement_type") == "source_quality_raw_row_exclusion_producer_gap"
            or item.get("improvement_type") == "source_quality_raw_row_exclusion_limit_up_locked_context"
            or item.get("route") == "source_quality_raw_row_exclusion_producer_fix"
            or item.get("route") == "review_required_limit_up_locked_context"
        )
    ]
    review_only_matching_orders = [
        item
        for item in [*orders, *non_selected]
        if isinstance(item, dict)
        and (
            item.get("raw_row_exclusion_context_classification") == "limit_up_locked_context"
            or item.get("improvement_type") == "source_quality_raw_row_exclusion_limit_up_locked_context"
            or item.get("route") == "review_required_limit_up_locked_context"
        )
    ]
    matching_orders = [
        item
        for item in [*selected_matching_orders, *review_only_matching_orders]
    ]
    invalid_contract_reasons: list[str] = []
    for item in matching_orders:
        if (
            item.get("raw_row_exclusion_context_classification") == "limit_up_locked_context"
            or item.get("improvement_type") == "source_quality_raw_row_exclusion_limit_up_locked_context"
            or item.get("route") == "review_required_limit_up_locked_context"
        ):
            if str(item.get("decision") or "") not in {"attach_existing_family", "defer_evidence"}:
                invalid_contract_reasons.append("limit_up_context_decision_not_review_only")
                continue
            if item.get("runtime_effect") is not False:
                invalid_contract_reasons.append("runtime_effect_not_false")
                continue
            if item.get("allowed_runtime_apply") is not False:
                invalid_contract_reasons.append("allowed_runtime_apply_not_false")
                continue
            invalid_contract_reasons = []
            break
        if str(item.get("decision") or "") != "implement_now":
            invalid_contract_reasons.append("decision_not_implement_now")
            continue
        if item.get("runtime_effect") is not False:
            invalid_contract_reasons.append("runtime_effect_not_false")
            continue
        if item.get("allowed_runtime_apply") is not False:
            invalid_contract_reasons.append("allowed_runtime_apply_not_false")
            continue
        forbidden_uses = item.get("forbidden_uses")
        if not isinstance(forbidden_uses, list) or not any(str(value).strip() for value in forbidden_uses):
            invalid_contract_reasons.append("missing_forbidden_uses_contract")
            continue
        invalid_contract_reasons = []
        break
    workorder_handoff_present = bool(matching_orders) and not invalid_contract_reasons
    return {
        "status": "pass" if workorder_handoff_present else "fail",
        "excluded_row_count": excluded_row_count,
        "stage_counts": raw_exclusion.get("stage_counts") or {},
        "exclusion_reasons": raw_exclusion.get("exclusion_reasons") or {},
        "workorder_handoff_present": workorder_handoff_present,
        "matching_workorder_count": len(matching_orders),
        "invalid_contract_reasons": sorted(set(invalid_contract_reasons)),
        "review_only_context_count": sum(
            1
            for item in matching_orders
            if isinstance(item, dict)
            and (
                item.get("raw_row_exclusion_context_classification") == "limit_up_locked_context"
                or item.get("improvement_type") == "source_quality_raw_row_exclusion_limit_up_locked_context"
                or item.get("route") == "review_required_limit_up_locked_context"
            )
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _parse_generated_at(payload: dict[str, Any]) -> datetime | None:
    raw = str(payload.get("generated_at") or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _consumer_stale(consumer: dict[str, Any], source: dict[str, Any]) -> bool:
    consumer_dt = _parse_generated_at(consumer)
    source_dt = _parse_generated_at(source)
    return bool(consumer_dt and source_dt and consumer_dt < source_dt)


def _read_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for item in _log_bundle_paths(path):
        lines.extend(_read_single_log_lines(item))
    return lines


def _log_bundle_paths(path: Path) -> list[Path]:
    rotated: list[tuple[int, Path]] = []
    try:
        candidates = path.parent.glob(f"{path.name}.*")
    except OSError:
        candidates = []
    for candidate in candidates:
        suffix = candidate.name.removeprefix(f"{path.name}.")
        if suffix.isdigit():
            rotated.append((int(suffix), candidate))
    return [item for _, item in sorted(rotated, reverse=True)] + [path]


def _read_single_log_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _latest_run_lines(log_lines: list[str], target_date: str) -> tuple[list[str], str | None]:
    needle = f"{_START_MARKER} target_date={target_date}"
    start_indexes = [idx for idx, line in enumerate(log_lines) if needle in line]
    if not start_indexes:
        return [], None
    start_idx = start_indexes[-1]
    start_line = log_lines[start_idx]
    return log_lines[start_idx + 1 :], start_line


def _parse_bool_flags(line: str) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for key, value in re.findall(r"([A-Za-z0-9_]+)=(true|false|1|0)", line):
        flags[key] = value in {"true", "1"}
    return flags


def _parse_marker_values(line: str) -> dict[str, str]:
    return {
        key: value
        for key, value in re.findall(r"([A-Za-z0-9_]+)=(\S+)", line or "")
    }


def _swing_lifecycle_provider_mismatch_warning(done_line: str | None, discovery: dict[str, Any]) -> str | None:
    marker_values = _parse_marker_values(done_line or "")
    expected_provider = str(marker_values.get("swing_lifecycle_bucket_discovery_ai_provider") or "").strip().lower()
    if not expected_provider:
        return None
    ai_review = discovery.get("ai_two_pass_review") if isinstance(discovery.get("ai_two_pass_review"), dict) else {}
    actual_provider = str(ai_review.get("provider") or "").strip().lower()
    if not actual_provider or actual_provider == expected_provider:
        return None
    return (
        "swing_lifecycle_bucket_discovery:ai_provider_mismatch:"
        f"done_marker={expected_provider}:artifact={actual_provider}"
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _artifact_paths(target_date: str) -> dict[str, Path]:
    next_day = _next_krx_trading_day(target_date)
    return {
        "market_panic_breadth": REPORT_DIR
        / "market_panic_breadth"
        / f"market_panic_breadth_{target_date}.json",
        "panic_sell_defense": REPORT_DIR / "panic_sell_defense" / f"panic_sell_defense_{target_date}.json",
        "panic_buying": REPORT_DIR / "panic_buying" / f"panic_buying_{target_date}.json",
        "threshold_cycle_ev": REPORT_DIR / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json",
        "scalp_entry_action_decision_matrix": REPORT_DIR
        / "scalp_entry_action_decision_matrix"
        / f"scalp_entry_action_decision_matrix_{target_date}.json",
        "buy_funnel_sentinel": REPORT_DIR / "buy_funnel_sentinel" / f"buy_funnel_sentinel_{target_date}.json",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "ldm_hypothesis_parent_refinement": REPORT_DIR
        / "ldm_hypothesis_parent_refinement"
        / f"ldm_hypothesis_parent_refinement_{target_date}.json",
        "lifecycle_decision_matrix_rolling5d": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}_rolling5d.json",
        "lifecycle_bucket_discovery_rolling5d": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}_rolling5d.json",
        "lifecycle_decision_matrix_rolling10d": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}_rolling10d.json",
        "lifecycle_bucket_discovery_rolling10d": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}_rolling10d.json",
        "lifecycle_decision_matrix_mtd": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}_mtd.json",
        "lifecycle_bucket_discovery_mtd": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}_mtd.json",
        "code_improvement_workorder": REPORT_DIR / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json",
        "observation_source_quality_audit": REPORT_DIR
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json",
        "runtime_approval_summary": REPORT_DIR / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json",
        "runtime_apply_gap_audit": REPORT_DIR
        / "runtime_apply_gap_audit"
        / f"runtime_apply_gap_audit_{target_date}.json",
        "key_lineage_ledger": REPORT_DIR / "key_lineage_ledger" / f"key_lineage_ledger_{target_date}.json",
        "conversion_lane": REPORT_DIR / "conversion_lane" / f"conversion_lane_{target_date}.json",
        "runtime_apply_bridge": REPORT_DIR
        / "runtime_apply_bridge"
        / f"runtime_apply_bridge_{target_date}.json",
        "threshold_preopen_apply_next": PROJECT_ROOT
        / "data"
        / "threshold_cycle"
        / "apply_plans"
        / f"threshold_apply_{next_day}.json",
        "scalp_sim_policy_catalog": PROJECT_ROOT
        / "data"
        / "threshold_cycle"
        / "scalp_sim_policies"
        / f"scalp_sim_policy_catalog_{target_date}.json",
        "swing_sim_policy_catalog": PROJECT_ROOT
        / "data"
        / "threshold_cycle"
        / "swing_sim_policies"
        / f"swing_sim_policy_catalog_{target_date}.json",
        "pattern_lab_currentness_audit": REPORT_DIR
        / "pattern_lab_currentness_audit"
        / f"pattern_lab_currentness_audit_{target_date}.json",
        "pattern_lab_ai_review": REPORT_DIR / "pattern_lab_ai_review" / f"pattern_lab_ai_review_{target_date}.json",
        "producer_gap_discovery": REPORT_DIR
        / "producer_gap_discovery"
        / f"producer_gap_discovery_{target_date}.json",
        "stage_hook_workorder_discovery": REPORT_DIR
        / "stage_hook_workorder_discovery"
        / f"stage_hook_workorder_discovery_{target_date}.json",
        "stage_hook_runtime_scaffold": REPORT_DIR
        / "stage_hook_runtime_scaffold"
        / f"stage_hook_runtime_scaffold_{target_date}.json",
        "time_window_regime_counterfactual": REPORT_DIR
        / "time_window_regime_counterfactual"
        / f"time_window_regime_counterfactual_{target_date}.json",
        "pattern_lab_propagation_audit": REPORT_DIR
        / "pattern_lab_propagation_audit"
        / f"pattern_lab_propagation_audit_{target_date}.json",
        "swing_daily_simulation": REPORT_DIR / "swing_daily_simulation" / f"swing_daily_simulation_{target_date}.json",
        "swing_strategy_discovery_sim": REPORT_DIR
        / "swing_strategy_discovery_sim"
        / f"swing_strategy_discovery_sim_{target_date}.json",
        "swing_lifecycle_decision_matrix": REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_bucket_discovery": REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_audit": REPORT_DIR / "swing_lifecycle_audit" / f"swing_lifecycle_audit_{target_date}.json",
        "next_stage2_checklist": PROJECT_ROOT / "docs" / "checklists" / f"{next_day}-stage2-todo-checklist.md",
    }


def _clean_baseline_report_residue_status(report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    policy = clean_baseline_policy()
    residue: list[dict[str, Any]] = []
    for path in sorted(report_dir.rglob("*")):
        if not path.is_file():
            continue
        reason = report_quarantine_reason(path, policy, include_baseline_date=False)
        if not reason and report_generated_before_clean_baseline(path, policy):
            reason = "same_day_pre_clean_baseline_report_archive_only"
        if not reason:
            continue
        residue.append(
            {
                "path": str(path),
                "reason": reason,
                "decision_state": "archive_only_not_allowed_for_clean_tuning",
            }
        )
    return {
        "status": "fail" if residue else "pass",
        "policy": policy,
        "residue_count": len(residue),
        "residue": residue[:200],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _clean_baseline_analytics_residue_status(analytics_dir: Path = ANALYTICS_DIR) -> dict[str, Any]:
    policy = clean_baseline_policy()
    residue: list[dict[str, Any]] = []
    for path in sorted(analytics_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".duckdb", ".parquet"}:
            continue
        reason = analytics_quarantine_reason(path, policy)
        if not reason:
            continue
        residue.append(
            {
                "path": str(path),
                "reason": reason,
                "decision_state": "archive_only_not_allowed_for_clean_tuning",
            }
        )
    return {
        "status": "fail" if residue else "pass",
        "policy": policy,
        "residue_count": len(residue),
        "residue": residue[:200],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _next_krx_trading_day(target_date: str) -> str:
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day as _next

    return _next(target_date)


def _json_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return True


def _ai_review_path(target_date: str) -> Path:
    return REPORT_DIR / "threshold_cycle_ai_review" / f"threshold_cycle_ai_review_{target_date}_postclose.json"


def _scalp_sim_overnight_path(target_date: str) -> Path:
    return REPORT_DIR / "scalp_sim_overnight" / f"scalp_sim_overnight_{target_date}.json"


def _calibration_path(target_date: str) -> Path:
    return (
        REPORT_DIR
        / "threshold_cycle_calibration"
        / f"threshold_cycle_calibration_{target_date}_postclose.json"
    )


def _runtime_candidates_requiring_ai(calibration_report: dict[str, Any]) -> list[str]:
    candidates = calibration_report.get("calibration_candidates")
    if not isinstance(candidates, list):
        return []

    blocking: list[str] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or item.get("source_family") or "").strip()
        state = str(item.get("calibration_state") or "").strip()
        if not family or family in _AI_EXEMPT_RUNTIME_FAMILIES:
            continue
        if state not in _AI_RUNTIME_STATES:
            continue
        if item.get("allowed_runtime_apply") is not True:
            continue
        if item.get("human_approval_required") is True:
            continue
        blocking.append(family)
    return sorted(set(blocking))



def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def _slug_with_hash(value: str, *, limit: int = 80) -> str:
    raw = str(value or "unknown")
    base = _slug(raw)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    keep = max(1, int(limit) - len(digest) - 1)
    return f"{base[:keep].rstrip('_')}_{digest}"


def _entry_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_entry_bucket_{bucket_type}_{bucket_key}"


def _scale_in_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_scale_in_bucket_{bucket_type}_{bucket_key}"


def _submit_bucket_order_id(item: dict[str, Any]) -> str:
    workorder_id = str(item.get("workorder_id") or "").strip()
    if workorder_id.startswith("order_entry_"):
        return workorder_id
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_submit_bucket_{bucket_type}_{bucket_key}"


def _overnight_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_overnight_bucket_{bucket_type}_{bucket_key}"


def _stage_bucket_order_id(stage: str, item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug_with_hash(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_{stage}_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_flow_bucket_order_id(item: dict[str, Any]) -> str:
    workorder_id = _slug(str(item.get("workorder_id") or "unknown"))
    bucket_id = _slug_with_hash(str(item.get("lifecycle_flow_bucket_id") or item.get("bucket_key") or "unknown"))
    return f"order_lifecycle_flow_bucket_{workorder_id}_{bucket_id}"


def _swing_ldm_order_id(item: dict[str, Any]) -> str:
    stage = _slug(str(item.get("lifecycle_stage") or "swing"))
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_swing_ldm_{stage}_{bucket_type}_{bucket_key}"


def _collect_entry_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("entry_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_entry_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_entry_bucket_candidate_ids(item))
    return found


def _collect_scale_in_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("scale_in_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_scale_in_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_scale_in_bucket_candidate_ids(item))
    return found


def _collect_submit_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("submit_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_submit_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_submit_bucket_candidate_ids(item))
    return found


def _collect_overnight_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("overnight_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_overnight_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_overnight_bucket_candidate_ids(item))
    return found


def _collect_lifecycle_flow_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("lifecycle_flow_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_lifecycle_flow_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_lifecycle_flow_bucket_candidate_ids(item))
    return found


def _collect_lifecycle_bucket_discovery_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key in ("surfaced_candidate_ids", "approved_bucket_ids"):
            value = payload.get(key)
            if isinstance(value, list):
                found.update(str(item) for item in value if item)
        for key in ("surfaced_candidates", "live_auto_apply_candidates", "sim_auto_approved_candidates"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item.get("bucket_id"):
                        found.add(str(item.get("bucket_id")))
        for value in payload.values():
            found.update(_collect_lifecycle_bucket_discovery_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_lifecycle_bucket_discovery_ids(item))
    return found


def _collect_swing_lifecycle_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key in ("sim_auto_candidate_ids", "surfaced_candidate_ids"):
            value = payload.get(key)
            if isinstance(value, list):
                found.update(str(item) for item in value if item)
        for key in ("sim_auto_approval_candidates", "runtime_approval_candidates", "surfaced_candidates", "sim_auto_approved_candidates"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and (item.get("candidate_id") or item.get("bucket_id")):
                        found.add(str(item.get("candidate_id") or item.get("bucket_id")))
        for value in payload.values():
            found.update(_collect_swing_lifecycle_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_swing_lifecycle_ids(item))
    return found


def _collect_swing_lifecycle_required_matrix_ids(matrix: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    required_sections = (
        "swing_lifecycle_flow_bucket_attribution",
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    )
    for section_name in required_sections:
        section = matrix.get(section_name) if isinstance(matrix.get(section_name), dict) else {}
        for key in ("sim_auto_approval_candidates", "runtime_approval_candidates"):
            for item in section.get(key) or []:
                if isinstance(item, dict) and (item.get("candidate_id") or item.get("bucket_id")):
                    found.add(str(item.get("candidate_id") or item.get("bucket_id")))
    return found


def _lifecycle_bucket_discovery_handoff_status(
    discovery: dict[str, Any],
    bridge_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    discovery_summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    discovery_warnings = [str(item) for item in (discovery.get("warnings") or []) if str(item)]
    source_contract_status = str(discovery_summary.get("source_contract_status") or "")
    ai_review_status = str(discovery_summary.get("ai_two_pass_review_status") or "")
    candidates = discovery.get("surfaced_candidates") if isinstance(discovery.get("surfaced_candidates"), list) else []
    source_dimension_summary = (
        discovery.get("source_dimension_gap_summary")
        if isinstance(discovery.get("source_dimension_gap_summary"), dict)
        else {}
    )
    quiet_gap_summary = (
        discovery.get("quiet_gap_summary")
        if isinstance(discovery.get("quiet_gap_summary"), dict)
        else {}
    )
    bridge_summary = bridge_report.get("summary") if isinstance(bridge_report.get("summary"), dict) else {}
    greenfield_policy_emit_state = str(bridge_summary.get("greenfield_policy_emit_state") or "").strip()
    expected_ids = sorted(
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("bucket_id")
    )
    live_families_set: set[str] = set()
    explicit_bridge_exclusion_families: set[str] = set()
    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("live_auto_apply_family") or "")
        if item.get("classification_state") != "live_auto_apply_ready" or not family:
            continue
        if family == "greenfield_real_environment_authority" and greenfield_policy_emit_state.startswith("not_emitted_"):
            explicit_bridge_exclusion_families.add(family)
            continue
        live_families_set.add(family)
    live_families = sorted(live_families_set)
    bridge_families = {
        str(item.get("family"))
        for item in (bridge_report.get("candidates") if isinstance(bridge_report.get("candidates"), list) else [])
        if isinstance(item, dict) and item.get("family")
    }
    runtime_ids = _collect_lifecycle_bucket_discovery_ids(runtime_summary)
    order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    expected_workorder_prefix = "order_lifecycle_bucket_discovery_"

    def required_quiet_gap_order_ids(summary: dict[str, Any]) -> set[str]:
        type_counts = summary.get("quiet_gap_type_counts") if isinstance(summary.get("quiet_gap_type_counts"), dict) else {}
        required: set[str] = set()
        if _safe_int(type_counts.get("parent_conflict_child")) + _safe_int(type_counts.get("exclusion_dimension_candidate")) > 0:
            required.add("order_lifecycle_quiet_gap_parent_conflict_rollup")
        if (
            _safe_int(type_counts.get("positive_source_only_keep_collecting"))
            + _safe_int(type_counts.get("absorbed_into_parent_policy"))
            > 0
        ):
            required.add("order_lifecycle_quiet_gap_positive_source_only_rollup")
        if _safe_int(type_counts.get("ai_review_parsed_low_coverage")) > 0:
            required.add("order_lifecycle_quiet_gap_ai_review_coverage_rollup")
        if not required and _safe_int(summary.get("quiet_gap_count")) > 0:
            required.add("order_lifecycle_quiet_gap_rollup")
        return required

    def source_only_excluded(item: dict[str, Any]) -> bool:
        if item.get("explicit_runtime_exclusion") is True or item.get("source_only_explicit_exclusion") is True:
            return True
        stage = str(item.get("stage") or "").strip()
        state = str(item.get("classification_state") or "").strip()
        family = str(item.get("live_auto_apply_family") or "").strip()
        if stage != "lifecycle_flow" or state not in {"new_bucket_candidate", "runtime_blocked_contract_gap"}:
            return False
        source_kind = str(item.get("source_bucket_kind") or "").strip()
        if source_kind in {"taxonomy_provenance_gap", "source_only_observation"}:
            return True
        if family == "greenfield_real_environment_authority" and (
            item.get("allowed_runtime_apply") is False or item.get("broker_order_forbidden") is True
        ):
            return True
        return False

    workorder_needed = [
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict)
        and str(item.get("classification_state") or "") in {"new_bucket_candidate", "runtime_blocked_contract_gap", "code_patch_required", "code_review_failed"}
        and not source_only_excluded(item)
    ]
    actionable_source_dimension_gap_ids = [
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict)
        and str(item.get("source_dimension_gap") or "") == "unknown_source_dimensions"
        and str(item.get("recommended_resolution") or "") in {"emit_or_backfill_source_field", "resolve_unknown_source_dimensions"}
        and item.get("bucket_id")
    ]
    if not actionable_source_dimension_gap_ids and int(source_dimension_summary.get("actionable_unknown_gap_count") or 0) > 0:
        actionable_source_dimension_gap_ids = ["source_dimension_gap_summary"]
    blocking_source_dimension_gap_ids = [
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict)
        and str(item.get("bucket_id") or "") in actionable_source_dimension_gap_ids
        and str(item.get("classification_state") or "")
        in {"live_auto_apply_ready", "sim_auto_approved", "entry_only_sim_auto_approved", "lifecycle_flow_sim_probe_candidate"}
    ]
    ai_followup_ids = sorted(
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("bucket_id") and item.get("ai_review_followup_required")
    )
    missing_bridge_families = sorted(set(live_families) - bridge_families)
    missing_runtime_summary_ids = sorted(set(expected_ids) - runtime_ids) if runtime_ids else expected_ids
    has_discovery_workorder = any(order_id.startswith(expected_workorder_prefix) for order_id in order_ids)
    has_source_dimension_gap_workorder = any(
        str(item.get("order_id") or "").startswith("order_lifecycle_source_dimension_gap_")
        and str(item.get("order_id") or "") != "order_lifecycle_source_dimension_gap_rollup"
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict)
    )
    required_quiet_order_ids = required_quiet_gap_order_ids(quiet_gap_summary)
    missing_quiet_order_ids = sorted(
        order_id
        for order_id in required_quiet_order_ids
        if (
            order_id not in order_ids
            if order_id != "order_lifecycle_quiet_gap_rollup"
            else not any(existing.startswith("order_lifecycle_quiet_gap_") for existing in order_ids)
        )
    )
    has_quiet_gap_rollup_workorder = not missing_quiet_order_ids if required_quiet_order_ids else False
    quiet_gap_count = int(quiet_gap_summary.get("quiet_gap_count") or 0)
    sim_live_connected_quiet_gap_count = int(quiet_gap_summary.get("sim_live_connected_quiet_gap_count") or 0)
    missing: list[str] = []
    warnings: list[str] = []
    if missing_bridge_families:
        missing.append("lifecycle_bucket_discovery_live_auto_bridge_missing")
    if expected_ids and missing_runtime_summary_ids:
        missing.append("runtime_approval_summary_lifecycle_bucket_discovery_missing")
    if workorder_needed and not has_discovery_workorder:
        missing.append("code_improvement_workorder_lifecycle_bucket_discovery_orders_missing")
    if actionable_source_dimension_gap_ids and not has_source_dimension_gap_workorder:
        if blocking_source_dimension_gap_ids:
            missing.append("lifecycle_source_dimension_gap_handoff_missing")
        else:
            warnings.append("lifecycle_source_dimension_gap_handoff_missing")
    if quiet_gap_count > 0 and missing_quiet_order_ids:
        if sim_live_connected_quiet_gap_count > 0:
            missing.append("lifecycle_quiet_gap_handoff_missing")
        else:
            warnings.append("lifecycle_quiet_gap_handoff_missing")
    if source_contract_status == "fail":
        missing.append("lifecycle_bucket_discovery_source_contract_fail")
    elif source_contract_status and source_contract_status != "pass":
        warnings.append(f"lifecycle_bucket_discovery_source_contract_{source_contract_status}")
    if ai_followup_ids:
        warnings.append("lifecycle_bucket_discovery_ai_post_apply_followup_required")
    warnings.extend(
        item
        for item in discovery_warnings
        if item.startswith("ai_") or item.startswith("source_contract_")
    )
    warnings = list(dict.fromkeys(warnings))
    status_warning_reasons = {
        "lifecycle_source_dimension_gap_handoff_missing",
        "lifecycle_quiet_gap_handoff_missing",
    }
    handoff_warning = any(item in status_warning_reasons for item in warnings)
    return {
        "status": "fail" if missing else ("missing" if not discovery else "warning" if handoff_warning else "pass"),
        "source_contract_status": source_contract_status or None,
        "ai_two_pass_review_status": ai_review_status or None,
        "expected_candidate_ids": expected_ids,
        "live_auto_apply_families": live_families,
        "runtime_apply_bridge_families": sorted(bridge_families),
        "explicit_bridge_exclusion_families": sorted(explicit_bridge_exclusion_families),
        "runtime_approval_summary_candidate_ids": sorted(runtime_ids),
        "missing_bridge_families": missing_bridge_families,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_ids,
        "workorder_needed_bucket_ids": workorder_needed,
        "actionable_source_dimension_gap_bucket_ids": sorted(actionable_source_dimension_gap_ids),
        "actionable_source_dimension_gap_count": int(source_dimension_summary.get("actionable_unknown_gap_count") or len(actionable_source_dimension_gap_ids)),
        "blocking_source_dimension_gap_bucket_ids": sorted(blocking_source_dimension_gap_ids),
        "quiet_gap_count": quiet_gap_count,
        "sim_live_connected_quiet_gap_count": sim_live_connected_quiet_gap_count,
        "expected_quiet_gap_workorder_order_ids": sorted(required_quiet_order_ids),
        "missing_quiet_gap_workorder_order_ids": missing_quiet_order_ids,
        "has_quiet_gap_rollup_workorder": has_quiet_gap_rollup_workorder,
        "ai_post_apply_followup_bucket_ids": ai_followup_ids,
        "has_discovery_workorder": has_discovery_workorder,
        "has_source_dimension_gap_workorder": has_source_dimension_gap_workorder,
        "missing": missing,
        "warnings": warnings,
        "interpretation": (
            "lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder"
            if discovery and not missing
            else "lifecycle bucket discovery produced surfaced candidates that downstream consumers dropped"
            if discovery
            else "lifecycle bucket discovery report missing"
        ),
    }


def _lifecycle_bucket_windows_status(
    *,
    paths: dict[str, Path],
    done_line: str | None,
    bridge_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
) -> dict[str, Any]:
    marker_values = _parse_marker_values(done_line or "")
    marker_enabled = str(marker_values.get("lifecycle_bucket_windows") or "").lower() in {"true", "1"}
    ev_windows = ev_report.get("lifecycle_bucket_windows") if isinstance(ev_report.get("lifecycle_bucket_windows"), dict) else {}
    runtime_windows = (
        runtime_summary.get("lifecycle_bucket_windows")
        if isinstance(runtime_summary.get("lifecycle_bucket_windows"), dict)
        else {}
    )
    artifact_present = any(paths[f"lifecycle_bucket_discovery_{suffix}"].exists() for suffix in ("rolling5d", "rolling10d", "mtd"))
    should_check = marker_enabled or bool(ev_windows) or bool(runtime_windows) or artifact_present
    if not should_check:
        return {"status": "pass", "checked": False, "missing": [], "warnings": []}

    missing: list[str] = []
    warnings: list[str] = []
    windows: dict[str, dict[str, Any]] = {}
    for suffix in ("rolling5d", "rolling10d", "mtd"):
        ldm_path = paths[f"lifecycle_decision_matrix_{suffix}"]
        discovery_path = paths[f"lifecycle_bucket_discovery_{suffix}"]
        if not ldm_path.exists():
            missing.append(f"lifecycle_decision_matrix_{suffix}_missing")
        if not discovery_path.exists():
            missing.append(f"lifecycle_bucket_discovery_{suffix}_missing")
            windows[suffix] = {"available": False}
            continue
        payload = _load_json(discovery_path)
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        source_contract_status = str(summary.get("source_contract_status") or "")
        parent_granularity_status = str(summary.get("parent_granularity_status") or "")
        windows[suffix] = {
            "available": bool(payload),
            "source_contract_status": source_contract_status or None,
            "parent_granularity_status": parent_granularity_status or None,
            "parent_bucket_count": _safe_int(summary.get("parent_bucket_count")),
        }
        if source_contract_status != "pass":
            missing.append(f"lifecycle_bucket_discovery_{suffix}_source_contract_not_pass")
        if parent_granularity_status != "target_pass":
            missing.append(f"lifecycle_bucket_discovery_{suffix}_parent_granularity_not_target")

    bridge_summary = bridge_report.get("summary") if isinstance(bridge_report.get("summary"), dict) else {}
    live_ready_count = _safe_int(bridge_summary.get("live_auto_apply_ready_count"))
    promotion_passed = bridge_summary.get("lifecycle_bucket_promotion_contract_passed")
    if live_ready_count > 0 and promotion_passed is not True:
        missing.append("runtime_apply_bridge_daily_only_live_authority")

    for item in bridge_report.get("candidates") or []:
        if not isinstance(item, dict):
            continue
        if item.get("family") != "greenfield_real_environment_authority":
            continue
        if item.get("bridge_candidate_state") != "live_auto_apply_ready":
            continue
        policy = item.get("greenfield_policy") if isinstance(item.get("greenfield_policy"), dict) else {}
        policy_bucket_id = str(policy.get("policy_bucket_id") or item.get("policy_bucket_id") or "")
        parent_status = str(policy.get("parent_granularity_status") or item.get("parent_granularity_status") or "")
        absorbed = policy.get("absorbed_child_bucket_ids") if isinstance(policy.get("absorbed_child_bucket_ids"), list) else []
        if not policy_bucket_id or parent_status != "target_pass" or not absorbed:
            missing.append("runtime_apply_bridge_child_combo_policy_authority")

    if marker_enabled and not artifact_present:
        missing.append("lifecycle_bucket_windows_marker_true_but_artifacts_missing")
    return {
        "status": "fail" if missing else ("warning" if warnings else "pass"),
        "checked": True,
        "windows": windows,
        "missing": sorted(set(missing)),
        "warnings": sorted(set(warnings)),
    }


def _swing_lifecycle_handoff_status(
    matrix: dict[str, Any],
    discovery: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    matrix_candidate_ids = _collect_swing_lifecycle_ids(matrix)
    required_matrix_candidate_ids = _collect_swing_lifecycle_required_matrix_ids(matrix)
    discovery_candidate_ids = _collect_swing_lifecycle_ids(discovery)
    expected_candidate_ids = set(required_matrix_candidate_ids)
    ev_candidate_ids = _collect_swing_lifecycle_ids(
        {
            "swing_lifecycle_decision_matrix": ev_report.get("swing_lifecycle_decision_matrix"),
            "swing_lifecycle_bucket_discovery": ev_report.get("swing_lifecycle_bucket_discovery"),
        }
    )
    runtime_candidate_ids = _collect_swing_lifecycle_ids(
        {
            "swing_lifecycle_decision_matrix": runtime_summary.get("swing_lifecycle_decision_matrix"),
            "swing_lifecycle_bucket_discovery": runtime_summary.get("swing_lifecycle_bucket_discovery"),
        }
    )
    source_workorders: list[dict[str, Any]] = []
    for section_name in (
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        section = matrix.get(section_name) if isinstance(matrix.get(section_name), dict) else {}
        source_workorders.extend(
            item for item in (section.get("code_improvement_workorders") or []) if isinstance(item, dict)
        )
    expected_order_ids = {_swing_ldm_order_id(item) for item in source_workorders}
    bottleneck = matrix.get("swing_entry_bottleneck") if isinstance(matrix.get("swing_entry_bottleneck"), dict) else {}
    bottleneck_matches = bottleneck.get("matches") if isinstance(bottleneck.get("matches"), list) else []
    swing_entry_bottleneck_critical = (
        bottleneck.get("primary") == "SWING_ENTRY_DROUGHT_CRITICAL"
        or "SWING_ENTRY_DROUGHT_CRITICAL" in bottleneck_matches
    )
    if swing_entry_bottleneck_critical:
        expected_candidate_ids.add("swing_entry_bottleneck_swing_entry_drought_critical")
        expected_order_ids.add("order_swing_entry_bottleneck_auto_resolution")
    discovery_workorders = (
        discovery.get("code_improvement_workorders")
        if isinstance(discovery.get("code_improvement_workorders"), list)
        else []
    )
    for item in discovery_workorders:
        if isinstance(item, dict):
            bucket_id = str(item.get("bucket_id") or item.get("workorder_id") or "")
            if bucket_id:
                expected_order_ids.add(f"order_swing_lifecycle_bucket_discovery_{_slug(bucket_id)}")
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(expected_candidate_ids - ev_candidate_ids) if expected_candidate_ids else []
    missing_runtime_candidates = sorted(expected_candidate_ids - runtime_candidate_ids) if expected_candidate_ids else []
    missing_order_ids = sorted(expected_order_ids - actual_order_ids)
    missing: list[str] = []
    if matrix and not discovery:
        missing.append("swing_lifecycle_bucket_discovery_missing")
    missing_matrix_to_discovery_candidates = (
        sorted(required_matrix_candidate_ids - discovery_candidate_ids)
        if required_matrix_candidate_ids and discovery
        else []
    )
    if missing_matrix_to_discovery_candidates:
        missing.append("swing_lifecycle_matrix_to_discovery_candidate_handoff_missing")
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_swing_lifecycle_candidates_missing")
    if missing_runtime_candidates:
        missing.append("runtime_approval_summary_swing_lifecycle_candidates_missing")
    if missing_order_ids:
        missing.append("code_improvement_workorder_swing_lifecycle_orders_missing")
    if swing_entry_bottleneck_critical:
        ev_bottleneck = (
            (ev_report.get("swing_lifecycle_decision_matrix") or {}).get("swing_entry_bottleneck_primary")
            if isinstance(ev_report.get("swing_lifecycle_decision_matrix"), dict)
            else None
        )
        runtime_bottleneck = (
            (runtime_summary.get("swing_lifecycle_decision_matrix") or {}).get("swing_entry_bottleneck_primary")
            if isinstance(runtime_summary.get("swing_lifecycle_decision_matrix"), dict)
            else None
        )
        if ev_bottleneck != "SWING_ENTRY_DROUGHT_CRITICAL" or runtime_bottleneck != "SWING_ENTRY_DROUGHT_CRITICAL":
            missing.append("swing_entry_bottleneck_handoff_missing")
    contract = matrix.get("input_contract") if isinstance(matrix.get("input_contract"), dict) else {}
    if matrix and contract.get("swing_daily_simulation_consumed") is not False:
        missing.append("swing_lifecycle_forbidden_daily_simulation_consumed")
    discovery_summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    ai_review_status = str(discovery_summary.get("ai_two_pass_review_status") or "").strip()
    warnings = [
        item
        if item.startswith("swing_lifecycle_bucket_discovery:")
        else f"swing_lifecycle_bucket_discovery:{item}"
        for item in (str(raw_item) for raw_item in (discovery.get("warnings") or []) if str(raw_item))
    ]
    if ai_review_status and ai_review_status != "parsed":
        warnings.append(f"swing_lifecycle_bucket_discovery:ai_two_pass_review_{ai_review_status}_fail_closed")
    if bool(discovery_summary.get("ai_fail_closed")):
        warnings.append("swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked")
    surfaced_candidates = (
        discovery.get("surfaced_candidates")
        if isinstance(discovery.get("surfaced_candidates"), list)
        else []
    )
    stage_unknown_candidate_ids: list[str] = []
    for item in surfaced_candidates:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage") or item.get("lifecycle_stage") or "").strip().lower()
        if not stage or stage == "unknown":
            stage_unknown_candidate_ids.append(str(item.get("candidate_id") or item.get("bucket_id") or "unknown"))
    if stage_unknown_candidate_ids:
        warnings.append("swing_lifecycle_bucket_discovery:stage_unknown")
    matrix_summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    raw_swing_event_count = _safe_int(matrix_summary.get("raw_swing_event_count"), 0)
    ldm_consumed_event_count = _safe_int(matrix_summary.get("ldm_consumed_event_count"), 0)
    ldm_event_coverage_rate = _safe_float(matrix_summary.get("ldm_event_coverage_rate"), 0.0)
    unmapped_swing_stage_counts = (
        matrix_summary.get("unmapped_swing_stage_counts")
        if isinstance(matrix_summary.get("unmapped_swing_stage_counts"), dict)
        else {}
    )
    if raw_swing_event_count >= 1000 and ldm_event_coverage_rate < 0.01:
        warnings.append("swing_lifecycle_decision_matrix:low_event_coverage")
    warnings = list(dict.fromkeys(warnings))
    return {
        "status": "fail" if missing else ("missing" if not matrix else "warning" if warnings else "pass"),
        "matrix_candidate_ids": sorted(matrix_candidate_ids),
        "required_matrix_candidate_ids": sorted(required_matrix_candidate_ids),
        "discovery_candidate_ids": sorted(discovery_candidate_ids),
        "missing_matrix_to_discovery_candidate_ids": missing_matrix_to_discovery_candidates,
        "expected_candidate_ids": sorted(expected_candidate_ids),
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_candidates,
        "expected_workorder_order_ids": sorted(expected_order_ids),
        "swing_entry_bottleneck_critical": swing_entry_bottleneck_critical,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_order_ids,
        "daily_simulation_consumed": bool(contract.get("swing_daily_simulation_consumed")),
        "deterministic_proposal_count": discovery_summary.get("deterministic_proposal_count"),
        "ai_two_pass_review_status": ai_review_status or None,
        "ai_fail_closed": bool(discovery_summary.get("ai_fail_closed")),
        "ai_review_blocker_state": discovery_summary.get("ai_review_blocker_state"),
        "pre_review_sim_auto_candidate_count": _safe_int(
            discovery_summary.get("pre_review_sim_auto_candidate_count"),
            0,
        ),
        "sim_auto_reviewed_candidate_count": _safe_int(
            discovery_summary.get("sim_auto_reviewed_candidate_count"),
            0,
        ),
        "sim_auto_unreviewed_candidate_count": _safe_int(
            discovery_summary.get("sim_auto_unreviewed_candidate_count"),
            0,
        ),
        "sim_auto_downgraded_by_review_count": _safe_int(
            discovery_summary.get("sim_auto_downgraded_by_review_count"),
            0,
        ),
        "sim_auto_review_shard_count": _safe_int(discovery_summary.get("sim_auto_review_shard_count"), 0),
        "stage_unknown_candidate_ids": sorted(set(stage_unknown_candidate_ids)),
        "raw_swing_event_count": raw_swing_event_count,
        "ldm_consumed_event_count": ldm_consumed_event_count,
        "ldm_event_coverage_rate": ldm_event_coverage_rate,
        "unmapped_swing_stage_counts": unmapped_swing_stage_counts,
        "ai_tier2_proposal_count": discovery_summary.get("ai_tier2_proposal_count"),
        "comparative_review_count": discovery_summary.get("comparative_review_count"),
        "selected_decision_counts": discovery_summary.get("selected_decision_counts"),
        "selected_source_counts": discovery_summary.get("selected_source_counts"),
        "missing": missing,
        "warnings": warnings,
        "interpretation": (
            "Swing LDM candidates/workorders propagated through EV, runtime summary, workorder, and verifier."
            if matrix and not missing and not warnings
            else "Swing LDM AI two-pass review is fail-closed; sim-auto promotion is blocked and must be surfaced."
            if matrix and warnings and not missing
            else "Swing LDM generated output but one or more downstream consumers dropped it."
            if matrix
            else "Swing LDM report missing"
        ),
    }


def _entry_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("entry_bucket_attribution")
        if isinstance(ldm_report.get("entry_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _entry_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_entry_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_entry_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_entry_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_entry_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_entry_bucket_orders_missing")
    return {
        "status": "fail" if missing else "pass",
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM entry bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _submit_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("submit_bucket_attribution")
        if isinstance(ldm_report.get("submit_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _submit_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_submit_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_submit_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_submit_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_submit_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_submit_bucket_orders_missing")
    return {
        "status": "fail" if missing else ("missing" if not attribution else "pass"),
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM submit bucket attribution propagated to threshold EV, runtime summary, and code workorder."
            if attribution and not missing
            else "LDM submit bucket output was generated but one or more downstream consumers dropped it."
            if attribution
            else "LDM submit bucket attribution missing"
        ),
    }


def _buy_funnel_submit_drought_handoff_status(
    buy_funnel: dict[str, Any],
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    classification = (
        buy_funnel.get("classification")
        if isinstance(buy_funnel.get("classification"), dict)
        else {}
    )
    matches = classification.get("matches") if isinstance(classification.get("matches"), list) else []
    critical = (
        classification.get("primary") == "SUBMIT_DROUGHT_CRITICAL"
        or "SUBMIT_DROUGHT_CRITICAL" in matches
    )
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    ldm_submit = (
        ldm_report.get("submit_bucket_attribution")
        if isinstance(ldm_report.get("submit_bucket_attribution"), dict)
        else {}
    )
    ev_entry_funnel = ev_report.get("entry_funnel") if isinstance(ev_report.get("entry_funnel"), dict) else {}
    ev_buy = ev_report.get("buy_funnel_sentinel") if isinstance(ev_report.get("buy_funnel_sentinel"), dict) else {}
    runtime_buy = (
        runtime_summary.get("buy_funnel_sentinel")
        if isinstance(runtime_summary.get("buy_funnel_sentinel"), dict)
        else {}
    )
    runtime_summary_section = (
        runtime_summary.get("summary") if isinstance(runtime_summary.get("summary"), dict) else {}
    )
    missing: list[str] = []
    if critical:
        missing_order_ids = sorted(set(ENTRY_SUBMIT_DROUGHT_REQUIRED_ORDER_IDS) - actual_order_ids)
        if missing_order_ids:
            missing.append("code_improvement_workorder_entry_submit_drought_orders_missing")
        if not ldm_submit:
            missing.append("ldm_submit_bucket_attribution_missing")
        if ev_buy.get("primary") != "SUBMIT_DROUGHT_CRITICAL":
            missing.append("threshold_cycle_ev_buy_funnel_sentinel_missing")
        if not ev_entry_funnel.get("entry_submit_drought_handoff_selected"):
            missing.append("threshold_cycle_ev_entry_submit_drought_handoff_missing")
        if runtime_buy.get("primary") != "SUBMIT_DROUGHT_CRITICAL":
            missing.append("runtime_approval_summary_buy_funnel_sentinel_missing")
        if not runtime_summary_section.get("entry_submit_drought_handoff_selected"):
            missing.append("runtime_approval_summary_entry_submit_drought_handoff_missing")
    return {
        "status": "fail" if missing else ("pass" if critical else "not_applicable"),
        "critical": critical,
        "primary": classification.get("primary"),
        "matches": matches,
        "expected_workorder_order_ids": ENTRY_SUBMIT_DROUGHT_REQUIRED_ORDER_IDS if critical else [],
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": (
            sorted(set(ENTRY_SUBMIT_DROUGHT_REQUIRED_ORDER_IDS) - actual_order_ids) if critical else []
        ),
        "ldm_submit_bucket_attribution_present": bool(ldm_submit),
        "threshold_cycle_ev_primary": ev_buy.get("primary"),
        "runtime_approval_summary_primary": runtime_buy.get("primary"),
        "missing": missing,
        "interpretation": (
            "BUY Funnel Sentinel SUBMIT_DROUGHT_CRITICAL propagated through workorder, LDM submit attribution, EV, and runtime summary."
            if critical and not missing
            else "BUY Funnel Sentinel critical source was generated but one or more downstream consumers dropped it."
            if critical
            else "BUY Funnel Sentinel submit drought is not critical."
        ),
    }


def _producer_gap_discovery_handoff_status(
    producer_gap: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    if not producer_gap:
        return {
            "status": "missing",
            "expected_workorder_order_ids": [],
            "actual_workorder_order_ids": [],
            "missing_workorder_order_ids": [],
            "ai_two_pass_review_status": "missing",
            "interpretation": "producer_gap_discovery artifact missing",
        }
    summary = producer_gap.get("summary") if isinstance(producer_gap.get("summary"), dict) else {}
    ai_review = producer_gap.get("ai_two_pass_review") if isinstance(producer_gap.get("ai_two_pass_review"), dict) else {}
    provider_status = ai_review.get("provider_status") if isinstance(ai_review.get("provider_status"), dict) else {}
    ai_status = str(summary.get("ai_two_pass_review_status") or "").strip()
    audit_status = str(summary.get("audit_status") or "").strip()
    ai_review_followup_required = bool(summary.get("ai_review_followup_required"))
    ai_review_followup_reasons = (
        summary.get("ai_review_followup_reasons")
        if isinstance(summary.get("ai_review_followup_reasons"), list)
        else []
    )
    ai_provider = str(ai_review.get("provider") or summary.get("provider") or provider_status.get("provider") or "").strip()
    ai_provider_status = str(provider_status.get("status") or "").strip()
    ai_model = ai_review.get("model") or summary.get("model") or provider_status.get("model")
    source_orders = (
        producer_gap.get("code_improvement_orders")
        if isinstance(producer_gap.get("code_improvement_orders"), list)
        else []
    )
    expected_order_ids = {
        str(item.get("order_id"))
        for item in source_orders
        if isinstance(item, dict)
        and item.get("order_id")
        and str(item.get("producer_gap_priority") or "high") in {"critical", "high"}
    }
    followup_order_ids = {
        str(item.get("order_id"))
        for item in source_orders
        if isinstance(item, dict)
        and item.get("order_id")
        and str(item.get("improvement_type") or item.get("source_workorder_id") or "") == "ai_review_followup"
    }
    high_priority_candidate_ids = {
        f"order_producer_gap_discovery_{_slug(str(item.get('candidate_id') or 'unknown'))}"
        for item in (producer_gap.get("producer_gap_candidates") if isinstance(producer_gap.get("producer_gap_candidates"), list) else [])
        if isinstance(item, dict)
        and str(item.get("pattern_type") or "") == "sim_first_coverage_gap"
        and str(item.get("ai_priority") or item.get("priority") or "high") in {"critical", "high"}
    }
    expected_order_ids.update(high_priority_candidate_ids)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_order_ids = sorted(expected_order_ids - actual_order_ids)
    missing_followup_order_ids = sorted(followup_order_ids - actual_order_ids)
    parsed_followup_handoff_closed = (
        ai_status == "parsed"
        and ai_review_followup_required
        and bool(followup_order_ids)
        and not missing_followup_order_ids
    )
    missing: list[str] = []
    if producer_gap.get("status") == "fail":
        missing.append("producer_gap_discovery_ai_review_failed")
    if ai_status != "parsed":
        missing.append("producer_gap_discovery_ai_review_not_parsed")
    if audit_status != "pass" and not parsed_followup_handoff_closed:
        missing.append("producer_gap_discovery_ai_audit_not_pass")
    provider_review_present = (
        ai_provider == "openai"
        and ai_provider_status in {"success", "provided_response"}
        and bool(ai_model)
    )
    if not provider_review_present:
        missing.append("producer_gap_discovery_tier2_provider_review_missing")
    if missing_order_ids:
        missing.append("code_improvement_workorder_producer_gap_orders_missing")
    if high_priority_candidate_ids and missing_order_ids:
        missing.append("producer_gap_discovery_sim_first_coverage_handoff_missing")
    return {
        "status": "fail" if missing else "pass",
        "missing": missing,
        "expected_workorder_order_ids": sorted(expected_order_ids),
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_order_ids,
        "ai_review_followup_required": ai_review_followup_required,
        "ai_review_followup_reasons": ai_review_followup_reasons,
        "ai_review_followup_workorder_order_ids": sorted(followup_order_ids),
        "missing_ai_review_followup_workorder_order_ids": missing_followup_order_ids,
        "ai_two_pass_review_status": ai_status or "missing",
        "audit_status": audit_status or "missing",
        "provider": ai_provider or "missing",
        "provider_status": ai_provider_status or "missing",
        "model": ai_model,
        "candidate_count": summary.get("candidate_count"),
        "workorder_count": summary.get("workorder_count"),
        "deterministic_proposal_count": summary.get("deterministic_proposal_count"),
        "ai_tier2_proposal_count": summary.get("ai_tier2_proposal_count"),
        "comparative_review_count": summary.get("comparative_review_count"),
        "selected_decision_counts": summary.get("selected_decision_counts"),
        "selected_source_counts": summary.get("selected_source_counts"),
        "interpretation": (
            "producer gap high-priority orders propagated to code improvement workorder with parsed AI review"
            if not missing
            and not parsed_followup_handoff_closed
            else "producer gap parsed AI review requested follow-up and the follow-up workorder propagated"
            if not missing
            and parsed_followup_handoff_closed
            else "producer gap discovery failed closed or workorder handoff is missing"
        ),
    }


def _stage_hook_workorder_handoff_status(
    stage_hook: dict[str, Any],
    producer_gap: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    if not stage_hook:
        return {
            "status": "missing",
            "expected_workorder_order_ids": [],
            "actual_workorder_order_ids": [],
            "missing_workorder_order_ids": [],
            "ai_two_pass_review_status": "missing",
            "interpretation": "stage_hook_workorder_discovery artifact missing",
        }
    summary = stage_hook.get("summary") if isinstance(stage_hook.get("summary"), dict) else {}
    ai_review = stage_hook.get("ai_two_pass_review") if isinstance(stage_hook.get("ai_two_pass_review"), dict) else {}
    provider_status = ai_review.get("provider_status") if isinstance(ai_review.get("provider_status"), dict) else {}
    ai_status = str(summary.get("ai_two_pass_review_status") or "").strip()
    audit_status = str(summary.get("audit_status") or "").strip()
    ai_review_followup_required = bool(summary.get("ai_review_followup_required"))
    ai_review_followup_reasons = (
        summary.get("ai_review_followup_reasons")
        if isinstance(summary.get("ai_review_followup_reasons"), list)
        else []
    )
    ai_provider = str(ai_review.get("provider") or summary.get("provider") or provider_status.get("provider") or "").strip()
    ai_provider_status = str(provider_status.get("status") or "").strip()
    source_orders = (
        stage_hook.get("code_improvement_orders")
        if isinstance(stage_hook.get("code_improvement_orders"), list)
        else []
    )
    expected_order_ids = {
        str(item.get("order_id"))
        for item in source_orders
        if isinstance(item, dict)
        and item.get("order_id")
        and (
            str(item.get("stage_hook_priority") or "high") in {"critical", "high"}
            or (item.get("stage_hook_candidate_contract") or {}).get("readiness_tier")
            == "implementation_workorder_ready"
        )
    }
    followup_order_ids = {
        str(item.get("order_id"))
        for item in source_orders
        if isinstance(item, dict)
        and item.get("order_id")
        and str(item.get("improvement_type") or item.get("source_workorder_id") or "") == "ai_review_followup"
    }
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_order_ids = sorted(expected_order_ids - actual_order_ids)
    missing_followup_order_ids = sorted(followup_order_ids - actual_order_ids)
    parsed_followup_handoff_closed = (
        ai_status == "parsed"
        and ai_review_followup_required
        and bool(followup_order_ids)
        and not missing_followup_order_ids
    )
    consumed_ids = set((stage_hook.get("context") or {}).get("consumed_candidate_ids") or [])
    producer_hook_ids = {
        str(item.get("candidate_id") or "")
        for item in (producer_gap.get("producer_gap_candidates") if isinstance(producer_gap.get("producer_gap_candidates"), list) else [])
        if isinstance(item, dict)
        and (
            isinstance(item.get("runtime_hook_candidate_contract"), dict)
            or str(item.get("pattern_type") or "") in {
                "sim_entry_selection_gap_missing",
                "sim_submit_fill_quality_gap_missing",
                "sim_holding_runner_gap_missing",
                "sim_exit_plateau_breakdown_gap_missing",
                "sim_stop_recovery_gap_missing",
                "sim_scale_in_counterfactual_gap_missing",
                "sim_time_window_exception_gap_missing",
                "sim_source_quality_join_gap_missing",
            }
        )
    }
    unconsumed_hook_candidate_ids = sorted(item for item in producer_hook_ids - consumed_ids if item)
    missing: list[str] = []
    if stage_hook.get("status") == "fail":
        missing.append("stage_hook_workorder_discovery_ai_review_failed")
    if ai_status != "parsed":
        missing.append("stage_hook_workorder_discovery_ai_review_not_parsed")
    if audit_status != "pass" and not parsed_followup_handoff_closed:
        missing.append("stage_hook_workorder_discovery_ai_audit_not_pass")
    if ai_provider != "openai" or ai_provider_status != "success":
        missing.append("stage_hook_workorder_discovery_tier2_provider_review_missing")
    if missing_order_ids:
        missing.append("stage_hook_workorder_handoff_missing")
    if unconsumed_hook_candidate_ids:
        missing.append("stage_hook_candidate_contract_unconsumed")
    return {
        "status": "fail" if missing else "pass",
        "missing": missing,
        "expected_workorder_order_ids": sorted(expected_order_ids),
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_order_ids,
        "ai_review_followup_required": ai_review_followup_required,
        "ai_review_followup_reasons": ai_review_followup_reasons,
        "ai_review_followup_workorder_order_ids": sorted(followup_order_ids),
        "missing_ai_review_followup_workorder_order_ids": missing_followup_order_ids,
        "unconsumed_hook_candidate_ids": unconsumed_hook_candidate_ids,
        "ai_two_pass_review_status": ai_status or "missing",
        "audit_status": audit_status or "missing",
        "provider": ai_provider or "missing",
        "provider_status": ai_provider_status or "missing",
        "candidate_count": summary.get("candidate_count"),
        "workorder_count": summary.get("workorder_count"),
        "deterministic_proposal_count": summary.get("deterministic_proposal_count"),
        "ai_tier2_proposal_count": summary.get("ai_tier2_proposal_count"),
        "comparative_review_count": summary.get("comparative_review_count"),
        "selected_decision_counts": summary.get("selected_decision_counts"),
        "selected_source_counts": summary.get("selected_source_counts"),
        "interpretation": (
            "stage hook implementation-ready orders propagated to code improvement workorder"
            if not missing
            and not parsed_followup_handoff_closed
            else "stage hook parsed AI review requested follow-up and the follow-up workorder propagated"
            if not missing
            and parsed_followup_handoff_closed
            else "stage hook discovery failed closed or workorder handoff is missing"
        ),
    }


def _bottom_rebound_sim_handoff_status(sim_report: dict[str, Any]) -> dict[str, Any]:
    if not sim_report:
        return {
            "status": "missing",
            "included": False,
            "missing": ["swing_strategy_discovery_sim_missing"],
            "interpretation": "swing_strategy_discovery_sim artifact missing",
        }
    source_quality = (
        sim_report.get("source_quality") if isinstance(sim_report.get("source_quality"), dict) else {}
    )
    bottom_source = (
        source_quality.get("bottom_rebound_source")
        if isinstance(source_quality.get("bottom_rebound_source"), dict)
        else {}
    )
    summary = sim_report.get("summary") if isinstance(sim_report.get("summary"), dict) else {}
    persist_summary = (
        sim_report.get("persist_summary") if isinstance(sim_report.get("persist_summary"), dict) else {}
    )
    source_rows = _safe_int(source_quality.get("bottom_rebound_source_rows"))
    included = bottom_source.get("status") == "ok" and source_rows > 0
    selected_count = _safe_int(summary.get("bottom_rebound_selected_candidate_count"))
    arm_count = _safe_int(summary.get("bottom_rebound_arm_count"))
    persisted_candidates = _safe_int(summary.get("bottom_rebound_persisted_candidate_count"))
    persisted_arms = _safe_int(summary.get("bottom_rebound_persisted_arm_count"))
    total_persisted_candidates = _safe_int(persist_summary.get("candidate_rows"))
    total_persisted_arms = _safe_int(persist_summary.get("arm_rows"))
    missing: list[str] = []
    if included:
        if selected_count <= 0:
            missing.append("bottom_rebound_selected_candidates_missing")
        if arm_count <= 0:
            missing.append("bottom_rebound_arms_missing")
        if total_persisted_candidates <= 0 or persisted_candidates <= 0:
            missing.append("bottom_rebound_persisted_candidates_missing")
        if total_persisted_arms <= 0 or persisted_arms <= 0:
            missing.append("bottom_rebound_persisted_arms_missing")
    return {
        "status": "fail" if missing else ("pass" if included else "not_applicable"),
        "included": included,
        "bottom_rebound_source_status": bottom_source.get("status") or "missing",
        "bottom_rebound_source_rows": source_rows,
        "bottom_rebound_selected_candidate_count": selected_count,
        "bottom_rebound_arm_count": arm_count,
        "bottom_rebound_persisted_candidate_count": persisted_candidates,
        "bottom_rebound_persisted_arm_count": persisted_arms,
        "persist_summary": persist_summary,
        "missing": missing,
        "interpretation": (
            "bottom_rebound source candidates were selected, armed, and persisted for label/EV handoff"
            if included and not missing
            else "bottom_rebound source was included but sim DB handoff is incomplete"
            if included
            else "bottom_rebound source was absent or blocked; safe-pool-only swing sim path applies"
        ),
    }


def _iter_pipeline_event_fields(target_date: str):
    path = PROJECT_ROOT / "data" / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if not isinstance(item, dict):
                    continue
                fields = item.get("fields") if isinstance(item.get("fields"), dict) else item
                yield fields
    except Exception:
        return


def _load_json_string_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        payload = json.loads(value)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _active_sim_priority_handoff_status(
    *,
    target_date: str,
    discovery: dict[str, Any],
    scalp_catalog: dict[str, Any],
    swing_catalog: dict[str, Any],
    preopen_apply: dict[str, Any],
    swing_sim_report: dict[str, Any],
) -> dict[str, Any]:
    missing: list[str] = []
    warnings: list[str] = []
    producer_seeds = [
        item
        for item in (discovery.get("active_sim_priority_seeds") or [])
        if isinstance(item, dict) and str(item.get("active_seed_id") or "").strip()
    ]
    catalog_seeds = [
        item
        for item in (scalp_catalog.get("active_sim_priority_seeds") or [])
        if isinstance(item, dict) and str(item.get("active_seed_id") or "").strip()
    ]
    if scalp_catalog and scalp_catalog.get("schema_version") != "scalp_sim_policy_catalog_v1":
        missing.append("active_sim_priority_catalog_schema_invalid")
    producer_seed_ids = {str(item.get("active_seed_id")) for item in producer_seeds}
    catalog_seed_ids = {str(item.get("active_seed_id")) for item in catalog_seeds}
    active_seed_ids = {str(item.get("active_seed_id")) for item in catalog_seeds if str(item.get("status") or "") == "active"}
    inactive_seed_ids = catalog_seed_ids - active_seed_ids
    if producer_seed_ids and not catalog_seed_ids:
        missing.append("active_sim_priority_catalog_seed_missing")
    if producer_seed_ids and producer_seed_ids - catalog_seed_ids:
        missing.append("active_sim_priority_producer_catalog_key_mismatch")
    for seed in catalog_seeds:
        prefix = seed.get("observable_prefix") if isinstance(seed.get("observable_prefix"), dict) else {}
        if not str(seed.get("source_parent_bucket_id") or "").strip() or str(seed.get("status") or "") not in {"active", "cooldown", "retired"}:
            missing.append("active_sim_priority_seed_required_key_missing")
            break
        if str(seed.get("status") or "") == "active" and (
            not str(prefix.get("entry_score_parent") or "").strip()
            or not str(prefix.get("entry_source_parent") or "").strip()
        ):
            missing.append("active_sim_priority_seed_observable_prefix_missing")
            break
        if any(str(key) not in ACTIVE_SIM_PRIORITY_OBSERVABLE_PREFIX_KEYS for key in prefix):
            missing.append("active_sim_priority_seed_observable_prefix_forbidden_dimension")
            break
        if seed.get("actual_order_submitted") is True or seed.get("broker_order_forbidden") is not True or seed.get("runtime_effect") is not False:
            missing.append("active_sim_priority_forbidden_contract_violation")
            break

    swing_policies = [
        item
        for item in (swing_catalog.get("active_arm_priority_policies") or [])
        if isinstance(item, dict) and str(item.get("priority_policy_id") or "").strip()
    ]
    if swing_catalog and swing_catalog.get("schema_version") != "swing_sim_policy_catalog_v1":
        missing.append("swing_active_arm_priority_catalog_schema_invalid")
    swing_policy_ids = {str(item.get("priority_policy_id")) for item in swing_policies}
    active_swing_policy_ids = {str(item.get("priority_policy_id")) for item in swing_policies if str(item.get("status") or "") == "active"}
    inactive_swing_policy_ids = swing_policy_ids - active_swing_policy_ids
    for policy in swing_policies:
        if str(policy.get("status") or "") not in {"active", "cooldown", "retired"} or not str(policy.get("source_report_date") or "").strip():
            missing.append("swing_active_arm_priority_required_key_missing")
            break
        if str(policy.get("status") or "") == "active" and not str(policy.get("priority_arm_id") or policy.get("priority_bucket_id") or "").strip():
            missing.append("swing_active_arm_priority_match_key_missing")
            break
        if policy.get("actual_order_submitted") is True or policy.get("broker_order_forbidden") is not True or policy.get("runtime_effect") is not False:
            missing.append("swing_active_arm_priority_forbidden_contract_violation")
            break

    def collect_selected_families(payload: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(payload, dict):
            if payload.get("selected") is True and payload.get("family"):
                found.add(str(payload.get("family")))
            for key, value in payload.items():
                if key == "family" and payload.get("decision_reason") and payload.get("selected") is not False:
                    found.add(str(value))
                else:
                    found.update(collect_selected_families(value))
        elif isinstance(payload, list):
            for item in payload:
                found.update(collect_selected_families(item))
        return found

    selected_families = collect_selected_families(preopen_apply)
    def collect_values(payload: Any, key_name: str) -> set[str]:
        found: set[str] = set()
        if isinstance(payload, dict):
            value = payload.get(key_name)
            if isinstance(value, list):
                found.update(str(item).strip() for item in value if str(item).strip())
            elif value is not None and str(value).strip():
                found.add(str(value).strip())
            for child in payload.values():
                found.update(collect_values(child, key_name))
        elif isinstance(payload, list):
            for item in payload:
                found.update(collect_values(item, key_name))
        return found

    preopen_seed_ids = collect_values(preopen_apply, "active_sim_priority_seed_ids")
    preopen_swing_policy_ids = collect_values(preopen_apply, "active_arm_priority_policy_ids")
    if (active_seed_ids or active_swing_policy_ids) and preopen_apply:
        if active_seed_ids and "scalp_sim_auto_approval" not in selected_families:
            missing.append("active_sim_priority_preopen_handoff_missing")
        elif active_seed_ids and not active_seed_ids.issubset(preopen_seed_ids):
            missing.append("active_sim_priority_preopen_handoff_missing")
        if active_swing_policy_ids and "swing_sim_auto_approval" not in selected_families:
            missing.append("swing_active_arm_priority_preopen_handoff_missing")
        elif active_swing_policy_ids and not active_swing_policy_ids.issubset(preopen_swing_policy_ids):
            missing.append("swing_active_arm_priority_preopen_handoff_missing")
    elif active_seed_ids or active_swing_policy_ids:
        warnings.append("active_sim_priority_preopen_handoff_pending")

    def truthy(value: Any) -> bool:
        return value is True or str(value).strip().lower() in {"true", "1", "yes"}

    referenced_scalp_catalog_cache: dict[str, tuple[set[str], set[str]]] = {}

    def referenced_scalp_catalog_seed_sets(path_value: Any) -> tuple[set[str], set[str]]:
        path_text = str(path_value or "").strip()
        if not path_text:
            return set(), set()
        if path_text in referenced_scalp_catalog_cache:
            return referenced_scalp_catalog_cache[path_text]
        path = Path(path_text)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        payload = _load_json(path)
        seeds = [
            item
            for item in (payload.get("active_sim_priority_seeds") or [])
            if isinstance(item, dict) and str(item.get("active_seed_id") or "").strip()
        ]
        all_ids = {str(item.get("active_seed_id")) for item in seeds}
        active_ids = {str(item.get("active_seed_id")) for item in seeds if str(item.get("status") or "") == "active"}
        referenced_scalp_catalog_cache[path_text] = (all_ids, all_ids - active_ids)
        return referenced_scalp_catalog_cache[path_text]

    candidate_prefix_counts: dict[str, int] = {}
    observed_seed_ids: set[str] = set()
    referenced_runtime_seed_ids: set[str] = set()
    observed_swing_policy_ids: set[str] = set()
    inactive_consumed: set[str] = set()
    unknown_consumed: set[str] = set()
    for fields in _iter_pipeline_event_fields(target_date):
        prefix_raw = str(fields.get("active_seed_candidate_observable_prefix") or "").strip()
        if prefix_raw:
            prefix_mapping = _load_json_string_mapping(prefix_raw)
            prefix_key = (
                json.dumps(prefix_mapping, ensure_ascii=True, sort_keys=True)
                if prefix_mapping
                else prefix_raw
            )
            candidate_prefix_counts[prefix_key] = candidate_prefix_counts.get(prefix_key, 0) + 1
        seed_id = str(fields.get("active_seed_id") or "").strip()
        if seed_id:
            observed_seed_ids.add(seed_id)
            runtime_catalog_ids, runtime_inactive_ids = referenced_scalp_catalog_seed_sets(
                fields.get("scalp_sim_auto_policy_file")
            )
            if seed_id in runtime_catalog_ids:
                referenced_runtime_seed_ids.add(seed_id)
            if seed_id in inactive_seed_ids or seed_id in runtime_inactive_ids:
                inactive_consumed.add(seed_id)
            elif seed_id not in catalog_seed_ids and seed_id not in runtime_catalog_ids:
                unknown_consumed.add(seed_id)
            if truthy(fields.get("actual_order_submitted")) or not truthy(fields.get("broker_order_forbidden")):
                missing.append("active_sim_priority_runtime_forbidden_contract_violation")
        policy_id = str(fields.get("priority_policy_id") or "").strip()
        if policy_id:
            observed_swing_policy_ids.add(policy_id)
            if policy_id in inactive_swing_policy_ids:
                inactive_consumed.add(policy_id)
            elif policy_id not in swing_policy_ids:
                unknown_consumed.add(policy_id)
    swing_summary = swing_sim_report.get("summary") if isinstance(swing_sim_report.get("summary"), dict) else {}
    if _safe_int(swing_summary.get("active_arm_priority_arm_count")) > 0:
        observed_swing_policy_ids.update(active_swing_policy_ids)
    if unknown_consumed:
        missing.append("active_sim_priority_unknown_key_observed")
    if inactive_consumed:
        missing.append("active_sim_priority_inactive_key_consumed")
    active_seed_runtime_expected = bool(active_seed_ids and active_seed_ids.issubset(preopen_seed_ids))
    active_swing_runtime_expected = bool(
        active_swing_policy_ids and active_swing_policy_ids.issubset(preopen_swing_policy_ids)
    )
    if active_seed_runtime_expected and not (observed_seed_ids & active_seed_ids):
        warnings.append("active_sim_priority_runtime_observation_missing")
    if active_swing_runtime_expected and not (observed_swing_policy_ids & active_swing_policy_ids):
        warnings.append("swing_active_arm_priority_runtime_observation_missing")
    active_prefixes = {
        json.dumps(seed.get("observable_prefix"), ensure_ascii=True, sort_keys=True)
        for seed in catalog_seeds
        if str(seed.get("status") or "") == "active" and isinstance(seed.get("observable_prefix"), dict)
    }
    observed_prefixes = set(candidate_prefix_counts)
    prefix_field_names = {
        key
        for prefix in active_prefixes
        for key in (_load_json_string_mapping(prefix).keys() if isinstance(_load_json_string_mapping(prefix), dict) else [])
    }
    active_priority_match_absence_diagnosis = {
        "status": "not_applicable",
        "diagnosis": "not_applicable",
        "reason": "active_priority_observed_or_no_active_priority",
        "candidate_prefix_count": sum(candidate_prefix_counts.values()),
        "top_candidate_prefixes": sorted(candidate_prefix_counts.items(), key=lambda item: item[1], reverse=True)[:5],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if missing:
        active_priority_match_absence_diagnosis.update(
            {
                "status": "fail",
                "diagnosis": "posterior_dimension_leaked_into_priority"
                if any("observable_prefix_forbidden_dimension" in item for item in missing)
                else "catalog_or_preopen_handoff_gap"
                if any("handoff" in item or "catalog" in item for item in missing)
                else "inactive_or_unknown_key_consumed"
                if any("unknown_key" in item or "inactive_key" in item for item in missing)
                else "contract_or_handoff_gap",
                "reason": ",".join(sorted(set(missing))),
            }
        )
    elif active_seed_runtime_expected and not (observed_seed_ids & active_seed_ids):
        if not preopen_seed_ids or not active_seed_ids.issubset(preopen_seed_ids):
            diagnosis = "catalog_or_preopen_handoff_gap"
            reason = "active_seed_not_preserved_in_preopen_apply"
        elif not candidate_prefix_counts:
            diagnosis = "runtime_observable_prefix_not_emitted"
            reason = "runtime_events_missing_active_seed_candidate_observable_prefix"
        elif any(key not in ACTIVE_SIM_PRIORITY_OBSERVABLE_PREFIX_KEYS for key in prefix_field_names):
            diagnosis = "posterior_dimension_leaked_into_priority"
            reason = "active_prefix_contains_non_runtime_observable_dimension"
        elif active_prefixes and not (active_prefixes & observed_prefixes):
            diagnosis = "active_prefix_too_narrow"
            reason = "runtime_candidate_prefixes_never_equal_active_prefix"
        else:
            diagnosis = "catalog_handoff_ok_natural_absence"
            reason = "catalog_and_preopen_handoff_intact_but_no_natural_match"
        active_priority_match_absence_diagnosis.update(
            {"status": "warning", "diagnosis": diagnosis, "reason": reason}
        )
    return {
        "status": "fail" if missing else ("warning" if warnings else "pass" if (active_seed_ids or active_swing_policy_ids) else "not_applicable"),
        "producer_seed_ids": sorted(producer_seed_ids),
        "catalog_seed_ids": sorted(catalog_seed_ids),
        "active_seed_ids": sorted(active_seed_ids),
        "preopen_seed_ids": sorted(preopen_seed_ids),
        "observed_seed_ids": sorted(observed_seed_ids),
        "referenced_runtime_seed_ids": sorted(referenced_runtime_seed_ids),
        "swing_priority_policy_ids": sorted(swing_policy_ids),
        "active_swing_priority_policy_ids": sorted(active_swing_policy_ids),
        "preopen_swing_priority_policy_ids": sorted(preopen_swing_policy_ids),
        "observed_swing_priority_policy_ids": sorted(observed_swing_policy_ids),
        "missing": list(dict.fromkeys(missing)),
        "warnings": list(dict.fromkeys(warnings)),
        "active_priority_match_absence_diagnosis": active_priority_match_absence_diagnosis,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _ldm_refinement_consumption_status(
    refinement: dict[str, Any],
    discovery: dict[str, Any],
    *,
    disabled: bool = False,
) -> dict[str, Any]:
    inputs = [item for item in (refinement.get("refinement_inputs") or []) if isinstance(item, dict)]
    if disabled:
        return {
            "status": "disabled",
            "input_count": len(inputs),
            "consumed_count": 0,
            "closure_counts": {},
            "missing": [],
            "warnings": [],
            "unconsumed_refinement_input_ids": [],
            "repeated_unresolved_input_ids": [],
            "diagnosis_missing_warning_input_ids": [],
            "diagnosis_missing_fail_input_ids": [],
            "diagnosed_repeated_input_ids": [],
            "runtime_authority_violation_input_ids": [],
            "disabled_reason": "ldm_hypothesis_parent_refinement_stage_disabled",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    if not refinement and not inputs:
        return {
            "status": "not_applicable",
            "input_count": 0,
            "consumed_count": 0,
            "closure_counts": {},
            "missing": [],
            "warnings": [],
            "unconsumed_refinement_input_ids": [],
            "repeated_unresolved_input_ids": [],
            "diagnosis_missing_warning_input_ids": [],
            "diagnosis_missing_fail_input_ids": [],
            "diagnosed_repeated_input_ids": [],
            "runtime_authority_violation_input_ids": [],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    ledger = (
        discovery.get("ldm_refinement_pressure_consumption")
        if isinstance(discovery.get("ldm_refinement_pressure_consumption"), dict)
        else {}
    )
    entries = [item for item in (ledger.get("entries") or []) if isinstance(item, dict)]
    missing: list[str] = []
    warnings: list[str] = []
    if inputs and not ledger:
        missing.append("ldm_refinement_consumption_ledger_missing")
    if ledger and str(ledger.get("status") or "") == "fail":
        missing.append("ldm_refinement_consumption_ledger_failed")
    if inputs and _safe_int(ledger.get("input_count")) < len(inputs):
        missing.append("ldm_refinement_input_count_mismatch")
    consumed_ids = {str(item.get("refinement_input_id") or "") for item in entries if str(item.get("refinement_input_id") or "")}
    expected_ids = {
        str(item.get("refinement_input_id") or "")
        for item in inputs
        if str(item.get("refinement_input_id") or "")
    }
    unconsumed_ids = sorted(expected_ids - consumed_ids)
    if unconsumed_ids:
        missing.append("ldm_refinement_inputs_unconsumed")
    if entries and all(str(item.get("closure_status") or "") == "needs_more_contrastive_sample" for item in entries):
        if any(not str(item.get("closure_reason") or "").strip() for item in entries):
            warnings.append("ldm_refinement_all_needs_more_sample_without_reason")
        else:
            warnings.append("ldm_refinement_all_needs_more_contrastive_sample")
    entry_by_id = {str(item.get("refinement_input_id") or ""): item for item in entries}
    forced_closure_statuses = {
        "parent_refinement_candidate_created",
        "new_parent_candidate_created",
        "source_quality_gap_created",
        "rare_observation_only_budget_capped",
        "rejected_as_structurally_uncontrastable",
        "rejected_as_fragile",
        "contract_handoff_gap_created",
    }
    diagnosis_missing_warning = []
    diagnosis_missing_fail = []
    diagnosed_repeated = []
    runtime_authority_violation_ids = []
    for item in inputs:
        retry_count = _safe_int(item.get("retry_count"))
        diagnosis = item.get("repeated_status_diagnosis") if isinstance(item.get("repeated_status_diagnosis"), dict) else {}
        diagnosed_status = str(item.get("diagnosed_status") or diagnosis.get("diagnosed_status") or "").strip()
        diagnosis_reason = str(item.get("diagnosis_reason") or diagnosis.get("diagnosis_reason") or "").strip()
        closure_status = str(entry_by_id.get(str(item.get("refinement_input_id") or ""), {}).get("closure_status") or "")
        has_forced_closure = closure_status in forced_closure_statuses
        has_diagnosis = bool(diagnosed_status and diagnosed_status != "not_applicable")
        item_id = str(item.get("refinement_input_id") or item.get("soft_hypothesis_id") or "")
        if _safe_int(item.get("forbidden_contract_violation_count")) > 0 or (
            diagnosed_status == "contract_or_handoff_gap" and "authority" in diagnosis_reason
        ):
            runtime_authority_violation_ids.append(item_id)
        if retry_count >= 2 and (has_diagnosis or has_forced_closure):
            diagnosed_repeated.append(item_id)
        elif retry_count >= 3:
            diagnosis_missing_fail.append(item_id)
        elif retry_count >= 2:
            diagnosis_missing_warning.append(item_id)
    if diagnosis_missing_warning:
        warnings.append("ldm_refinement_repeated_status_diagnosis_missing_warning")
    if diagnosis_missing_fail:
        missing.append("ldm_refinement_repeated_status_diagnosis_missing_fail")
    if runtime_authority_violation_ids:
        missing.append("ldm_refinement_runtime_authority_violation_fail")
    repeated_unresolved = [
        str(item.get("refinement_input_id") or item.get("soft_hypothesis_id") or "")
        for item in inputs
        if str(item.get("classification") or "") == "taxonomy_gap_candidate"
        and _safe_int(item.get("repeated_gap_count")) >= 2
        and not any(
            str(entry.get("refinement_input_id") or "") == str(item.get("refinement_input_id") or "")
            and str(entry.get("closure_status") or "")
            in forced_closure_statuses
            for entry in entries
        )
    ]
    if repeated_unresolved:
        warnings.append("ldm_refinement_repeated_taxonomy_gap_unresolved")
    status = "fail" if missing else "warning" if warnings else "pass"
    return {
        "status": status,
        "input_count": len(inputs),
        "consumed_count": len(entries),
        "closure_counts": ledger.get("closure_counts") or {},
        "missing": list(dict.fromkeys(missing)),
        "warnings": list(dict.fromkeys(warnings)),
        "unconsumed_refinement_input_ids": unconsumed_ids,
        "repeated_unresolved_input_ids": [item for item in repeated_unresolved if item],
        "diagnosis_missing_warning_input_ids": [item for item in diagnosis_missing_warning if item],
        "diagnosis_missing_fail_input_ids": [item for item in diagnosis_missing_fail if item],
        "diagnosed_repeated_input_ids": [item for item in diagnosed_repeated if item],
        "runtime_authority_violation_input_ids": [item for item in runtime_authority_violation_ids if item],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _scale_in_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("scale_in_bucket_attribution")
        if isinstance(ldm_report.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _scale_in_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_scale_in_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_scale_in_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_scale_in_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_scale_in_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_scale_in_bucket_orders_missing")
    return {
        "status": "fail" if missing else "pass",
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM scale-in bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _overnight_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("overnight_bucket_attribution")
        if isinstance(ldm_report.get("overnight_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _overnight_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_overnight_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_overnight_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_overnight_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_overnight_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_overnight_bucket_orders_missing")
    return {
        "status": "fail" if missing else "pass",
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM overnight bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _lifecycle_flow_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("lifecycle_flow_bucket_attribution")
        if isinstance(ldm_report.get("lifecycle_flow_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _lifecycle_flow_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("lifecycle_flow_bucket_id")
    )
    summary = attribution.get("summary") if isinstance(attribution.get("summary"), dict) else {}
    flow_count = _safe_int(summary.get("flow_count"), 0)
    complete_flow_count = _safe_int(summary.get("complete_flow_count"), 0)
    direct_sim_record_complete_flow_count = _safe_int(summary.get("direct_sim_record_complete_flow_count"), 0)
    adm_bridge_complete_flow_count = _safe_int(summary.get("adm_bridge_complete_flow_count"), 0)
    fallback_complete_flow_count = _safe_int(summary.get("fallback_complete_flow_count"), 0)
    join_contract_blocked = bool(summary.get("join_contract_blocked"))
    ev_candidate_ids = _collect_lifecycle_flow_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_lifecycle_flow_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_lifecycle_flow_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_lifecycle_flow_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_lifecycle_flow_bucket_orders_missing")
    if flow_count > 0 and complete_flow_count <= 0:
        missing.append("lifecycle_complete_flow_absent")
    if join_contract_blocked:
        missing.append("lifecycle_join_contract_blocked")
    return {
        "status": "fail" if missing else "pass",
        "flow_count": flow_count,
        "complete_flow_count": complete_flow_count,
        "direct_sim_record_complete_flow_count": direct_sim_record_complete_flow_count,
        "adm_bridge_complete_flow_count": adm_bridge_complete_flow_count,
        "fallback_complete_flow_count": fallback_complete_flow_count,
        "complete_flow_rate": summary.get("complete_flow_rate"),
        "incomplete_flow_count": _safe_int(summary.get("incomplete_flow_count"), 0),
        "join_contract_blocked": join_contract_blocked,
        "bundle_ev_tuning_state": summary.get("bundle_ev_tuning_state"),
        "top_incomplete_reason": summary.get("top_incomplete_reason"),
        "incomplete_flow_reason_counts": summary.get("incomplete_flow_reason_counts") or {},
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM lifecycle-flow parent bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM lifecycle-flow parent bucket is fail-closed because complete entry-submit-holding-exit flow is absent."
            if "lifecycle_complete_flow_absent" in missing
            else "LDM lifecycle-flow parent bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _stage_only_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    attribution_key = f"{stage}_bucket_attribution"
    attribution = (
        ldm_report.get(attribution_key)
        if isinstance(ldm_report.get(attribution_key), dict)
        else {}
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    runtime_candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    attribution_summary = attribution.get("summary") if isinstance(attribution.get("summary"), dict) else {}
    expected_bucket_count = _safe_int(attribution_summary.get("bucket_count"), 0)
    expected_workorder_count = _safe_int(attribution_summary.get("workorder_count"), len(source_workorders))
    expected_order_ids = sorted(
        _stage_bucket_order_id(stage, item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    expected_workorder_ids = sorted(
        str(item.get("workorder_id"))
        for item in source_workorders
        if isinstance(item, dict) and item.get("workorder_id")
    )
    ev_matrix = ev_report.get("lifecycle_decision_matrix") if isinstance(ev_report.get("lifecycle_decision_matrix"), dict) else {}
    runtime_matrix = (
        runtime_summary.get("lifecycle_decision_matrix")
        if isinstance(runtime_summary.get("lifecycle_decision_matrix"), dict)
        else {}
    )
    ev_workorder_ids = {
        str(item.get("workorder_id"))
        for item in (
            ev_matrix.get(f"{stage}_bucket_code_improvement_workorders")
            if isinstance(ev_matrix.get(f"{stage}_bucket_code_improvement_workorders"), list)
            else []
        )
        if isinstance(item, dict) and item.get("workorder_id")
    }
    runtime_workorder_ids = {
        str(item.get("workorder_id"))
        for item in (
            runtime_matrix.get(f"{stage}_bucket_code_improvement_workorders")
            if isinstance(runtime_matrix.get(f"{stage}_bucket_code_improvement_workorders"), list)
            else []
        )
        if isinstance(item, dict) and item.get("workorder_id")
    }
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing_ev_workorder_ids = sorted(set(expected_workorder_ids) - ev_workorder_ids)
    missing_runtime_workorder_ids = sorted(set(expected_workorder_ids) - runtime_workorder_ids)
    ev_bucket_count = _safe_int(ev_matrix.get(f"{stage}_bucket_count"), -1)
    runtime_bucket_count = _safe_int(runtime_matrix.get(f"{stage}_bucket_count"), -1)
    ev_workorder_count = _safe_int(ev_matrix.get(f"{stage}_bucket_workorder_count"), -1)
    runtime_workorder_count = _safe_int(runtime_matrix.get(f"{stage}_bucket_workorder_count"), -1)
    missing: list[str] = []
    if runtime_candidates:
        missing.append(f"{stage}_stage_only_runtime_candidates_forbidden")
    if expected_bucket_count > 0 and ev_bucket_count < expected_bucket_count:
        missing.append(f"threshold_cycle_ev_{stage}_bucket_count_missing")
    if expected_bucket_count > 0 and runtime_bucket_count < expected_bucket_count:
        missing.append(f"runtime_approval_summary_{stage}_bucket_count_missing")
    if expected_workorder_count > 0 and ev_workorder_count < expected_workorder_count:
        missing.append(f"threshold_cycle_ev_{stage}_bucket_workorder_count_missing")
    if expected_workorder_count > 0 and runtime_workorder_count < expected_workorder_count:
        missing.append(f"runtime_approval_summary_{stage}_bucket_workorder_count_missing")
    if missing_ev_workorder_ids:
        missing.append(f"threshold_cycle_ev_{stage}_bucket_workorders_missing")
    if missing_runtime_workorder_ids:
        missing.append(f"runtime_approval_summary_{stage}_bucket_workorders_missing")
    if missing_order_ids:
        missing.append(f"code_improvement_workorder_{stage}_bucket_orders_missing")
    return {
        "status": "fail" if missing else ("missing" if not attribution else "pass"),
        "expected_workorder_order_ids": expected_order_ids,
        "expected_workorder_ids": expected_workorder_ids,
        "threshold_cycle_ev_workorder_ids": sorted(ev_workorder_ids),
        "runtime_approval_summary_workorder_ids": sorted(runtime_workorder_ids),
        "missing_ev_workorder_ids": missing_ev_workorder_ids,
        "missing_runtime_summary_workorder_ids": missing_runtime_workorder_ids,
        "expected_bucket_count": expected_bucket_count,
        "threshold_cycle_ev_bucket_count": ev_bucket_count,
        "runtime_approval_summary_bucket_count": runtime_bucket_count,
        "expected_workorder_count": expected_workorder_count,
        "threshold_cycle_ev_workorder_count": ev_workorder_count,
        "runtime_approval_summary_workorder_count": runtime_workorder_count,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_order_ids,
        "runtime_candidate_count": len(runtime_candidates),
        "missing": missing,
        "interpretation": (
            f"LDM {stage} bucket attribution propagated as source-only child evidence."
            if attribution and not missing
            else f"LDM {stage} bucket output was generated but one or more downstream consumers dropped it."
            if attribution
            else f"LDM {stage} bucket attribution missing"
        ),
    }


def _has_scale_in_source(ldm_report: dict[str, Any]) -> bool:
    sources = ldm_report.get("sources") if isinstance(ldm_report.get("sources"), dict) else {}
    summary = sources.get("scale_in_attribution") if isinstance(sources.get("scale_in_attribution"), dict) else {}
    if int(summary.get("rows") or 0) > 0:
        return True
    report_summary = ldm_report.get("summary") if isinstance(ldm_report.get("summary"), dict) else {}
    stage_counts = report_summary.get("stage_counts") if isinstance(report_summary.get("stage_counts"), dict) else {}
    return int(stage_counts.get("scale_in") or 0) > 0


def _has_lifecycle_stage_source(ldm_report: dict[str, Any], stage: str) -> bool:
    report_summary = ldm_report.get("summary") if isinstance(ldm_report.get("summary"), dict) else {}
    stage_counts = report_summary.get("stage_counts") if isinstance(report_summary.get("stage_counts"), dict) else {}
    return int(stage_counts.get(stage) or 0) > 0


def _has_overnight_source(ldm_report: dict[str, Any]) -> bool:
    sources = ldm_report.get("sources") if isinstance(ldm_report.get("sources"), dict) else {}
    summary = sources.get("scalp_sim_overnight") if isinstance(sources.get("scalp_sim_overnight"), dict) else {}
    return int(summary.get("rows") or 0) > 0


def _scalp_sim_overnight_source_quality(report: dict[str, Any], *, report_exists: bool) -> dict[str, Any]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    active_undecided_count = int(summary.get("active_undecided_count") or 0)
    decision_target = int(summary.get("decision_target") or 0)
    source_quality_status = str(summary.get("source_quality_status") or "missing").strip()
    warnings = summary.get("source_quality_warnings") if isinstance(summary.get("source_quality_warnings"), list) else []
    missing: list[str] = []
    if report_exists and not summary:
        missing.append("scalp_sim_overnight_report_missing_or_invalid")
    if active_undecided_count > 0 and decision_target == 0:
        missing.append("scalp_sim_overnight_active_undecided_without_decision")
    if source_quality_status == "source_quality_blocker":
        missing.append("scalp_sim_overnight_source_quality_blocker")
    return {
        "status": "fail" if missing else ("missing" if not report_exists else "pass"),
        "decision_target": decision_target,
        "active_undecided_count": active_undecided_count,
        "decision_coverage_rate": summary.get("decision_coverage_rate"),
        "source_quality_status": source_quality_status,
        "source_quality_warnings": warnings,
        "missing": missing,
        "interpretation": (
            "scalp sim overnight report was not present in this verification fixture/run"
            if not report_exists
            else "scalp sim overnight preclose decisions covered active sim positions"
            if not missing
            else "active scalp sim overnight positions were not covered by preclose decision events"
        ),
    }

def _ai_correction_status(target_date: str) -> dict[str, Any]:
    ai_path = _ai_review_path(target_date)
    calibration_path = _calibration_path(target_date)
    ai_review = _load_json(ai_path)
    calibration_report = _load_json(calibration_path)
    blocking_families = _runtime_candidates_requiring_ai(calibration_report)
    ai_status = str(ai_review.get("ai_status") or "missing").strip()
    provider_status = ai_review.get("provider_status") or ai_review.get("ai_provider_status")
    parse_warnings = ai_review.get("parse_warnings")
    if not isinstance(parse_warnings, list):
        parse_warnings = []

    if ai_status == "parsed":
        status = "pass"
    elif blocking_families:
        status = "fail"
    elif ai_path.exists() and ai_status not in {"", "missing"}:
        status = "warning"
    else:
        status = "missing"

    return {
        "status": status,
        "ai_status": ai_status,
        "ai_review_path": str(ai_path),
        "calibration_path": str(calibration_path),
        "provider_status": provider_status,
        "parse_warnings": parse_warnings,
        "blocking_runtime_candidate_families": blocking_families,
        "interpretation": (
            "AI correction parsed successfully"
            if status == "pass"
            else "AI correction unavailable blocks runtime-applicable threshold candidates"
            if status == "fail"
            else "AI correction unavailable but no runtime-applicable candidate was detected"
            if status == "warning"
            else "AI correction artifact missing or unreadable"
        ),
    }


def _postclose_not_yet_due(target_date: str) -> bool:
    try:
        parsed = date.fromisoformat(target_date)
    except ValueError:
        return False
    now = datetime.now()
    return parsed == now.date() and now.time() < dtime(16, 10)


def build_threshold_cycle_postclose_verification(
    target_date: str,
    *,
    require_done_marker: bool = True,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    log_lines = _read_lines(LOG_PATH)
    run_lines, start_line = _latest_run_lines(log_lines, target_date)

    predecessor_ready: list[dict[str, Any]] = []
    predecessor_waits: list[dict[str, Any]] = []
    predecessor_timeouts: list[dict[str, Any]] = []
    log_issues: list[str] = []
    handoff_warnings: list[str] = []
    done_line: str | None = None

    for line in run_lines:
        ready_match = _READY_RE.search(line)
        if ready_match:
            waited = int(ready_match.group("waited"))
            item = {
                "label": ready_match.group("label"),
                "path": ready_match.group("path"),
                "waited_sec": waited,
                "json_valid": ready_match.group("json_valid"),
            }
            predecessor_ready.append(item)
            if waited > 0:
                predecessor_waits.append(item)
        timeout_match = _TIMEOUT_RE.search(line)
        if timeout_match:
            predecessor_timeouts.append(
                {
                    "label": timeout_match.group("label"),
                    "path": timeout_match.group("path"),
                    "waited_sec": int(timeout_match.group("waited")),
                }
            )
        if _FAIL_MARKER in line and f"target_date={target_date}" in line:
            log_issues.append("postclose_fail_marker_present")
        if _PAUSED_MARKER in line and f"target_date={target_date}" in line:
            log_issues.append("postclose_paused_marker_present")
        if _DONE_MARKER in line and f"target_date={target_date}" in line:
            done_line = line

    artifact_status = []
    for label, path in _artifact_paths(target_date).items():
        item = {
            "label": label,
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        if path.suffix == ".json":
            item["json_valid"] = _json_valid(path)
        artifact_status.append(item)

    paths = _artifact_paths(target_date)
    ev_report = _load_json(paths["threshold_cycle_ev"])
    workorder = _load_json(paths["code_improvement_workorder"])
    observation_source_quality_audit = _load_json(paths["observation_source_quality_audit"])
    runtime_summary = _load_json(paths["runtime_approval_summary"])
    runtime_apply_gap_audit = _load_json(paths["runtime_apply_gap_audit"])
    key_lineage_ledger = _load_json(paths["key_lineage_ledger"])
    conversion_lane = _load_json(paths["conversion_lane"])
    bridge_report = _load_json(paths["runtime_apply_bridge"])
    preopen_apply_next = _load_json(paths["threshold_preopen_apply_next"])
    scalp_sim_policy_catalog = _load_json(paths["scalp_sim_policy_catalog"])
    swing_sim_policy_catalog = _load_json(paths["swing_sim_policy_catalog"])
    buy_funnel_report = _load_json(paths["buy_funnel_sentinel"])
    currentness_audit = _load_json(paths["pattern_lab_currentness_audit"])
    pattern_lab_ai_review = _load_json(paths["pattern_lab_ai_review"])
    producer_gap_discovery = _load_json(paths["producer_gap_discovery"])
    stage_hook_workorder_discovery = _load_json(paths["stage_hook_workorder_discovery"])
    propagation_audit = _load_json(paths["pattern_lab_propagation_audit"])
    swing_strategy_discovery_sim = _load_json(paths["swing_strategy_discovery_sim"])
    ldm_report = _load_json(paths["lifecycle_decision_matrix"])
    discovery_report = _load_json(paths["lifecycle_bucket_discovery"])
    ldm_refinement_report = _load_json(paths["ldm_hypothesis_parent_refinement"])
    swing_ldm_report = _load_json(paths["swing_lifecycle_decision_matrix"])
    swing_bucket_discovery_report = _load_json(paths["swing_lifecycle_bucket_discovery"])
    scalp_sim_overnight_path = _scalp_sim_overnight_path(target_date)
    scalp_sim_overnight = _load_json(scalp_sim_overnight_path)
    scalp_sim_overnight_quality = _scalp_sim_overnight_source_quality(
        scalp_sim_overnight,
        report_exists=scalp_sim_overnight_path.exists(),
    )
    if scalp_sim_overnight_quality.get("status") == "fail":
        log_issues.extend(scalp_sim_overnight_quality.get("missing") or [])
    ai_correction = _ai_correction_status(target_date)
    if ai_correction.get("status") == "fail":
        log_issues.append("ai_correction_unavailable_blocks_runtime_candidates")
    clean_policy = clean_baseline_policy()
    clean_baseline_report_residue = (
        _clean_baseline_report_residue_status(REPORT_DIR)
        if is_date_allowed(target_date, clean_policy)
        else {
            "status": "not_applicable_pre_clean_baseline_target",
            "policy": clean_policy,
            "residue_count": 0,
            "residue": [],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    )
    clean_baseline_analytics_residue = (
        _clean_baseline_analytics_residue_status(ANALYTICS_DIR)
        if is_date_allowed(target_date, clean_policy)
        else {
            "status": "not_applicable_pre_clean_baseline_target",
            "policy": clean_policy,
            "residue_count": 0,
            "residue": [],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    )
    if clean_baseline_report_residue.get("status") == "fail":
        log_issues.append("clean_baseline_report_residue_present")
    if clean_baseline_analytics_residue.get("status") == "fail":
        log_issues.append("clean_baseline_analytics_residue_present")
    if is_date_allowed(target_date, clean_policy) and not paths["observation_source_quality_audit"].exists():
        log_issues.append("source_quality_preflight_missing")
    source_quality_hard_block = _source_quality_hard_block_status(
        observation_source_quality_audit,
        ev_report=ev_report,
        runtime_summary=runtime_summary,
        ldm_report=ldm_report,
        bridge_report=bridge_report,
        workorder=workorder,
    )
    if source_quality_hard_block.get("candidate_violation_sources"):
        log_issues.append("source_quality_hard_block_candidate_generated")
    if source_quality_hard_block.get("workorder_handoff_present") is False:
        log_issues.append("source_quality_hard_block_handoff_missing")
    raw_row_exclusion_handoff = _raw_row_exclusion_handoff_status(
        observation_source_quality_audit,
        workorder=workorder,
    )
    if raw_row_exclusion_handoff.get("status") == "fail":
        log_issues.append("raw_row_exclusion_workorder_handoff_missing")
    entry_bucket_handoff = _entry_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if entry_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_entry_bucket_handoff_missing")
    submit_attribution = ldm_report.get("submit_bucket_attribution")
    submit_bucket_handoff = _submit_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if isinstance(submit_attribution, dict) and submit_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_submit_bucket_handoff_missing")
    holding_attribution = ldm_report.get("holding_bucket_attribution")
    holding_source_present = _has_lifecycle_stage_source(ldm_report, "holding")
    if holding_source_present and not isinstance(holding_attribution, dict):
        log_issues.append("ldm_holding_bucket_attribution_missing")
    if (
        holding_source_present
        and isinstance(holding_attribution, dict)
        and _safe_int(
            (
                holding_attribution.get("summary")
                if isinstance(holding_attribution.get("summary"), dict)
                else {}
            ).get("bucket_count"),
            0,
        )
        <= 0
    ):
        log_issues.append("ldm_holding_bucket_attribution_empty")
    holding_bucket_handoff = _stage_only_bucket_handoff_status(
        ldm_report,
        ev_report,
        runtime_summary,
        workorder,
        stage="holding",
    )
    if isinstance(holding_attribution, dict) and holding_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_holding_bucket_handoff_missing")
    exit_attribution = ldm_report.get("exit_bucket_attribution")
    exit_source_present = _has_lifecycle_stage_source(ldm_report, "exit")
    if exit_source_present and not isinstance(exit_attribution, dict):
        log_issues.append("ldm_exit_bucket_attribution_missing")
    if (
        exit_source_present
        and isinstance(exit_attribution, dict)
        and _safe_int(
            (
                exit_attribution.get("summary")
                if isinstance(exit_attribution.get("summary"), dict)
                else {}
            ).get("bucket_count"),
            0,
        )
        <= 0
    ):
        log_issues.append("ldm_exit_bucket_attribution_empty")
    exit_bucket_handoff = _stage_only_bucket_handoff_status(
        ldm_report,
        ev_report,
        runtime_summary,
        workorder,
        stage="exit",
    )
    if isinstance(exit_attribution, dict) and exit_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_exit_bucket_handoff_missing")
    buy_funnel_submit_drought_handoff = _buy_funnel_submit_drought_handoff_status(
        buy_funnel_report,
        ldm_report,
        ev_report,
        runtime_summary,
        workorder,
    )
    if buy_funnel_submit_drought_handoff.get("status") == "fail":
        log_issues.append("buy_funnel_submit_drought_handoff_missing")
    scale_in_attribution = ldm_report.get("scale_in_bucket_attribution")
    scale_in_source_present = _has_scale_in_source(ldm_report)
    if scale_in_source_present and not isinstance(scale_in_attribution, dict):
        log_issues.append("ldm_scale_in_bucket_attribution_missing")
    scale_in_bucket_handoff = _scale_in_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if isinstance(scale_in_attribution, dict) and scale_in_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_scale_in_bucket_handoff_missing")
    overnight_attribution = ldm_report.get("overnight_bucket_attribution")
    overnight_source_present = _has_overnight_source(ldm_report)
    if overnight_source_present and not isinstance(overnight_attribution, dict):
        log_issues.append("ldm_overnight_bucket_attribution_missing")
    overnight_bucket_handoff = _overnight_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if isinstance(overnight_attribution, dict) and overnight_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_overnight_bucket_handoff_missing")
    lifecycle_flow_attribution = ldm_report.get("lifecycle_flow_bucket_attribution")
    lifecycle_flow_bucket_handoff = _lifecycle_flow_bucket_handoff_status(
        ldm_report,
        ev_report,
        runtime_summary,
        workorder,
    )
    if isinstance(lifecycle_flow_attribution, dict) and lifecycle_flow_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_lifecycle_flow_bucket_handoff_missing")
    if "lifecycle_complete_flow_absent" in (lifecycle_flow_bucket_handoff.get("missing") or []):
        log_issues.append("lifecycle_complete_flow_absent")
    lifecycle_bucket_discovery_handoff = _lifecycle_bucket_discovery_handoff_status(
        discovery_report,
        bridge_report,
        runtime_summary,
        workorder,
    )
    if lifecycle_bucket_discovery_handoff.get("status") == "fail":
        log_issues.append("lifecycle_bucket_discovery_handoff_missing")
    elif lifecycle_bucket_discovery_handoff.get("status") == "warning":
        handoff_warnings.extend(
            str(item) for item in (lifecycle_bucket_discovery_handoff.get("warnings") or []) if str(item)
        )
    lifecycle_bucket_windows = _lifecycle_bucket_windows_status(
        paths=paths,
        done_line=done_line,
        bridge_report=bridge_report,
        ev_report=ev_report,
        runtime_summary=runtime_summary,
    )
    if lifecycle_bucket_windows.get("status") == "fail":
        log_issues.append("lifecycle_bucket_windows_fail")
    elif lifecycle_bucket_windows.get("status") == "warning":
        handoff_warnings.extend(str(item) for item in (lifecycle_bucket_windows.get("warnings") or []) if str(item))
    swing_lifecycle_handoff = _swing_lifecycle_handoff_status(
        swing_ldm_report,
        swing_bucket_discovery_report,
        ev_report,
        runtime_summary,
        workorder,
    )
    provider_mismatch_warning = _swing_lifecycle_provider_mismatch_warning(done_line, swing_bucket_discovery_report)
    if provider_mismatch_warning:
        warnings = list(swing_lifecycle_handoff.get("warnings") or [])
        warnings.append(provider_mismatch_warning)
        swing_lifecycle_handoff["warnings"] = list(dict.fromkeys(str(item) for item in warnings if str(item)))
        if swing_lifecycle_handoff.get("status") == "pass":
            swing_lifecycle_handoff["status"] = "warning"
    if swing_lifecycle_handoff.get("status") == "fail":
        log_issues.append("swing_lifecycle_handoff_missing")
    elif swing_lifecycle_handoff.get("status") == "warning":
        handoff_warnings.extend(str(item) for item in (swing_lifecycle_handoff.get("warnings") or []) if str(item))
    producer_gap_handoff = _producer_gap_discovery_handoff_status(producer_gap_discovery, workorder)
    if producer_gap_handoff.get("status") == "fail":
        log_issues.append("producer_gap_discovery_handoff_missing")
    stage_hook_handoff = _stage_hook_workorder_handoff_status(
        stage_hook_workorder_discovery,
        producer_gap_discovery,
        workorder,
    )
    preliminary_execution_flags = _parse_bool_flags(done_line or "")
    if (
        preliminary_execution_flags.get("stage_hook_workorder_discovery") is True
        and stage_hook_handoff.get("status") == "fail"
    ):
        log_issues.append("stage_hook_workorder_handoff_missing")
    bottom_rebound_sim_handoff = _bottom_rebound_sim_handoff_status(swing_strategy_discovery_sim)
    if bottom_rebound_sim_handoff.get("status") == "fail":
        log_issues.append("bottom_rebound_sim_handoff_missing")
    active_sim_priority_handoff = _active_sim_priority_handoff_status(
        target_date=target_date,
        discovery=discovery_report,
        scalp_catalog=scalp_sim_policy_catalog,
        swing_catalog=swing_sim_policy_catalog,
        preopen_apply=preopen_apply_next,
        swing_sim_report=swing_strategy_discovery_sim,
    )
    if active_sim_priority_handoff.get("status") == "fail":
        log_issues.append("active_sim_priority_handoff_missing")
    elif active_sim_priority_handoff.get("status") == "warning":
        handoff_warnings.extend(str(item) for item in (active_sim_priority_handoff.get("warnings") or []) if str(item))
    ldm_refinement_consumption = _ldm_refinement_consumption_status(
        ldm_refinement_report,
        discovery_report,
        disabled=preliminary_execution_flags.get("ldm_hypothesis_parent_refinement") is False,
    )
    if ldm_refinement_consumption.get("status") == "fail":
        log_issues.append("ldm_hypothesis_parent_refinement_unconsumed")
    elif ldm_refinement_consumption.get("status") == "warning":
        handoff_warnings.extend(
            str(item) for item in (ldm_refinement_consumption.get("warnings") or []) if str(item)
        )

    lineage = workorder.get("lineage") if isinstance(workorder.get("lineage"), dict) else {}
    workorder_snapshot = {
        "generation_id": workorder.get("generation_id"),
        "source_hash": workorder.get("source_hash"),
        "previous_generation_id": lineage.get("previous_generation_id"),
        "previous_source_hash": lineage.get("previous_source_hash"),
        "previous_exists": bool(lineage.get("previous_exists")),
        "new_order_ids": list(lineage.get("new_order_ids") or []),
        "removed_order_ids": list(lineage.get("removed_order_ids") or []),
        "decision_changed_order_ids": list(lineage.get("decision_changed_order_ids") or []),
        "new_selected_order_count": ((workorder.get("summary") or {}).get("new_selected_order_count")),
        "removed_selected_order_count": ((workorder.get("summary") or {}).get("removed_selected_order_count")),
        "decision_changed_order_count": ((workorder.get("summary") or {}).get("decision_changed_order_count")),
    }

    if workorder_snapshot["generation_id"] and workorder_snapshot["source_hash"]:
        if workorder_snapshot["source_hash"] == workorder_snapshot["previous_source_hash"]:
            workorder_snapshot_status = "same_snapshot_replay"
        elif workorder_snapshot["previous_exists"]:
            workorder_snapshot_status = "source_changed_with_lineage"
        else:
            workorder_snapshot_status = "first_generation"
    else:
        workorder_snapshot_status = "missing_snapshot_identity"

    downstream_links = {
        "threshold_cycle_ev_sources_workorder": (
            ((ev_report.get("sources") or {}).get("code_improvement_workorder")) or None
        ),
        "runtime_approval_summary_sources_ev": (
            ((runtime_summary.get("sources") or {}).get("threshold_cycle_ev")) or None
        ),
        "threshold_cycle_ev_sources_pattern_lab_currentness_audit": (
            ((ev_report.get("sources") or {}).get("pattern_lab_currentness_audit")) or None
        ),
        "threshold_cycle_ev_sources_pattern_lab_ai_review": (
            ((ev_report.get("sources") or {}).get("pattern_lab_ai_review")) or None
        ),
        "threshold_cycle_ev_sources_producer_gap_discovery": (
            ((ev_report.get("sources") or {}).get("producer_gap_discovery")) or None
        ),
        "threshold_cycle_ev_sources_stage_hook_workorder_discovery": (
            ((ev_report.get("sources") or {}).get("stage_hook_workorder_discovery")) or None
        ),
        "threshold_cycle_ev_sources_stage_hook_runtime_scaffold": (
            ((ev_report.get("sources") or {}).get("stage_hook_runtime_scaffold")) or None
        ),
        "threshold_cycle_ev_sources_pattern_lab_propagation_audit": (
            ((ev_report.get("sources") or {}).get("pattern_lab_propagation_audit")) or None
        ),
        "threshold_cycle_ev_sources_scalp_entry_action_decision_matrix": (
            ((ev_report.get("sources") or {}).get("scalp_entry_action_decision_matrix")) or None
        ),
        "threshold_cycle_ev_sources_lifecycle_decision_matrix": (
            ((ev_report.get("sources") or {}).get("lifecycle_decision_matrix")) or None
        ),
        "runtime_approval_summary_sources_scalp_entry_action_decision_matrix": (
            ((runtime_summary.get("sources") or {}).get("scalp_entry_action_decision_matrix")) or None
        ),
        "runtime_approval_summary_sources_lifecycle_decision_matrix": (
            ((runtime_summary.get("sources") or {}).get("lifecycle_decision_matrix")) or None
        ),
        "threshold_cycle_ev_sources_swing_lifecycle_decision_matrix": (
            ((ev_report.get("sources") or {}).get("swing_lifecycle_decision_matrix")) or None
        ),
        "threshold_cycle_ev_sources_swing_lifecycle_bucket_discovery": (
            ((ev_report.get("sources") or {}).get("swing_lifecycle_bucket_discovery")) or None
        ),
        "runtime_approval_summary_sources_swing_lifecycle_decision_matrix": (
            ((runtime_summary.get("sources") or {}).get("swing_lifecycle_decision_matrix")) or None
        ),
        "runtime_approval_summary_sources_swing_lifecycle_bucket_discovery": (
            ((runtime_summary.get("sources") or {}).get("swing_lifecycle_bucket_discovery")) or None
        ),
        "runtime_approval_summary_sources_pattern_lab_propagation_audit": (
            ((runtime_summary.get("sources") or {}).get("pattern_lab_propagation_audit")) or None
        ),
        "runtime_approval_summary_sources_pattern_lab_ai_review": (
            ((runtime_summary.get("sources") or {}).get("pattern_lab_ai_review")) or None
        ),
    }

    marker_values = _parse_marker_values(done_line or "")
    recovery_action = marker_values.get("recovery_action")
    recovery_done = recovery_action in {"marker_reconciliation", "tail_repair_done_reconciliation"}
    marker_reconciliation_done = recovery_action == "marker_reconciliation"
    execution_flags = _parse_bool_flags(done_line or "")
    required_execution_flags = (
        "swing_lifecycle",
        "pattern_labs",
        "deepseek_swing_lab",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "scalp_entry_adm",
        "lifecycle_decision_matrix",
        "code_improvement_workorder",
        "daily_ev",
        "runtime_approval_summary",
        "next_stage2_checklist",
    )
    missing_execution_flags = [
        key
        for key in required_execution_flags
        if done_line and not recovery_done and key not in execution_flags
    ]
    for key in ("swing_strategy_discovery", "swing_lifecycle_matrix", "swing_lifecycle_bucket_discovery"):
        if done_line and key in execution_flags and key not in missing_execution_flags:
            required_execution_flags = (*required_execution_flags, key)
    if done_line and "pattern_lab_ai_review" in execution_flags and "pattern_lab_ai_review" not in missing_execution_flags:
        required_execution_flags = (*required_execution_flags, "pattern_lab_ai_review")
    if done_line and "producer_gap_discovery" in execution_flags and "producer_gap_discovery" not in missing_execution_flags:
        required_execution_flags = (*required_execution_flags, "producer_gap_discovery")
    if (
        done_line
        and "stage_hook_workorder_discovery" in execution_flags
        and "stage_hook_workorder_discovery" not in missing_execution_flags
    ):
        required_execution_flags = (*required_execution_flags, "stage_hook_workorder_discovery")
    if (
        done_line
        and "stage_hook_runtime_scaffold" in execution_flags
        and "stage_hook_runtime_scaffold" not in missing_execution_flags
    ):
        required_execution_flags = (*required_execution_flags, "stage_hook_runtime_scaffold")
    if (
        done_line
        and "time_window_regime_counterfactual" in execution_flags
        and "time_window_regime_counterfactual" not in missing_execution_flags
    ):
        required_execution_flags = (*required_execution_flags, "time_window_regime_counterfactual")
    if done_line and "runtime_apply_gap_audit" in execution_flags and "runtime_apply_gap_audit" not in missing_execution_flags:
        required_execution_flags = (*required_execution_flags, "runtime_apply_gap_audit")
    if (
        done_line
        and "ldm_hypothesis_parent_refinement" in execution_flags
        and "ldm_hypothesis_parent_refinement" not in missing_execution_flags
    ):
        required_execution_flags = (*required_execution_flags, "ldm_hypothesis_parent_refinement")
    disabled_stage_flags = [
        key
        for key in (
            "swing_lifecycle",
            "swing_strategy_discovery",
            "swing_lifecycle_matrix",
            "swing_lifecycle_bucket_discovery",
            "pattern_labs",
            "deepseek_swing_lab",
            "pattern_lab_currentness_audit",
            "pattern_lab_ai_review",
            "time_window_regime_counterfactual",
            "producer_gap_discovery",
            "stage_hook_workorder_discovery",
            "stage_hook_runtime_scaffold",
            "pattern_lab_propagation_audit",
            "scalp_entry_adm",
            "lifecycle_decision_matrix",
            "code_improvement_workorder",
            "daily_ev",
            "runtime_approval_summary",
            "runtime_apply_gap_audit",
            "ldm_hypothesis_parent_refinement",
            "next_stage2_checklist",
        )
        if key in execution_flags and not execution_flags[key]
    ]
    disabled_artifact_labels = {
        "pattern_lab_currentness_audit" if "pattern_lab_currentness_audit" in disabled_stage_flags else "",
        "pattern_lab_ai_review" if "pattern_lab_ai_review" in disabled_stage_flags else "",
        "time_window_regime_counterfactual" if "time_window_regime_counterfactual" in disabled_stage_flags else "",
        "producer_gap_discovery" if "producer_gap_discovery" in disabled_stage_flags else "",
        "stage_hook_workorder_discovery" if "stage_hook_workorder_discovery" in disabled_stage_flags else "",
        "stage_hook_runtime_scaffold" if "stage_hook_runtime_scaffold" in disabled_stage_flags else "",
        "pattern_lab_propagation_audit" if "pattern_lab_propagation_audit" in disabled_stage_flags else "",
        "scalp_entry_action_decision_matrix" if "scalp_entry_adm" in disabled_stage_flags else "",
        "lifecycle_decision_matrix" if "lifecycle_decision_matrix" in disabled_stage_flags else "",
        "swing_strategy_discovery_sim" if "swing_strategy_discovery" in disabled_stage_flags else "",
        "swing_lifecycle_decision_matrix" if "swing_lifecycle_matrix" in disabled_stage_flags else "",
        "swing_lifecycle_bucket_discovery" if "swing_lifecycle_bucket_discovery" in disabled_stage_flags else "",
        "code_improvement_workorder" if "code_improvement_workorder" in disabled_stage_flags else "",
        "threshold_cycle_ev" if "daily_ev" in disabled_stage_flags else "",
        "runtime_approval_summary" if "runtime_approval_summary" in disabled_stage_flags else "",
        "runtime_apply_bridge" if "runtime_apply_bridge" in disabled_stage_flags else "",
        "runtime_apply_gap_audit" if "runtime_apply_gap_audit" in disabled_stage_flags else "",
        "ldm_hypothesis_parent_refinement" if "ldm_hypothesis_parent_refinement" in disabled_stage_flags else "",
        "next_stage2_checklist" if "next_stage2_checklist" in disabled_stage_flags else "",
    }
    if "runtime_apply_bridge" not in execution_flags:
        disabled_artifact_labels.add("runtime_apply_bridge")
    if "runtime_apply_gap_audit" not in execution_flags:
        disabled_artifact_labels.add("runtime_apply_gap_audit")
    if "ldm_hypothesis_parent_refinement" not in execution_flags:
        disabled_artifact_labels.add("ldm_hypothesis_parent_refinement")
    if "swing_strategy_discovery" not in execution_flags:
        disabled_artifact_labels.add("swing_strategy_discovery_sim")
    if "swing_lifecycle_matrix" not in execution_flags:
        disabled_artifact_labels.add("swing_lifecycle_decision_matrix")
    if "swing_lifecycle_bucket_discovery" not in execution_flags:
        disabled_artifact_labels.add("swing_lifecycle_bucket_discovery")
    if "pattern_lab_ai_review" not in execution_flags:
        disabled_artifact_labels.add("pattern_lab_ai_review")
    if "time_window_regime_counterfactual" not in execution_flags:
        disabled_artifact_labels.add("time_window_regime_counterfactual")
    if "producer_gap_discovery" not in execution_flags:
        disabled_artifact_labels.add("producer_gap_discovery")
    if "stage_hook_workorder_discovery" not in execution_flags:
        disabled_artifact_labels.add("stage_hook_workorder_discovery")
    if "stage_hook_runtime_scaffold" not in execution_flags:
        disabled_artifact_labels.add("stage_hook_runtime_scaffold")
    disabled_artifact_labels.discard("")
    missing_required_artifacts = [
        item["label"]
        for item in artifact_status
        if item["label"] not in disabled_artifact_labels
        and (
            item["label"] not in _OPTIONAL_ARTIFACT_LABELS
            or item.get("exists")
        )
        and (
            not item.get("exists")
            or (item.get("json_valid") is False)
        )
    ]
    if (
        execution_flags.get("ldm_hypothesis_parent_refinement") is True
        and "ldm_hypothesis_parent_refinement" not in disabled_stage_flags
        and not paths["ldm_hypothesis_parent_refinement"].exists()
    ):
        missing_required_artifacts.append("ldm_hypothesis_parent_refinement")
    missing_downstream_links = [
        key for key, value in downstream_links.items() if value in (None, "", "-")
    ]
    if "pattern_lab_currentness_audit" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "pattern_lab_currentness_audit" not in key
        ]
    if "pattern_lab_ai_review" not in execution_flags or "pattern_lab_ai_review" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "pattern_lab_ai_review" not in key
        ]
    if "producer_gap_discovery" not in execution_flags or "producer_gap_discovery" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "producer_gap_discovery" not in key
        ]
    if "stage_hook_workorder_discovery" not in execution_flags or "stage_hook_workorder_discovery" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "stage_hook_workorder_discovery" not in key
        ]
    if "stage_hook_runtime_scaffold" not in execution_flags or "stage_hook_runtime_scaffold" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "stage_hook_runtime_scaffold" not in key
        ]
    if "pattern_lab_propagation_audit" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "pattern_lab_propagation_audit" not in key
        ]
    if "code_improvement_workorder" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "code_improvement_workorder" not in key
        ]
    if "scalp_entry_adm" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "scalp_entry_action_decision_matrix" not in key
        ]
    if "lifecycle_decision_matrix" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "lifecycle_decision_matrix" not in key
        ]
    if "swing_lifecycle_matrix" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "swing_lifecycle_decision_matrix" not in key
        ]
    if "swing_lifecycle_matrix" not in execution_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "swing_lifecycle_decision_matrix" not in key
        ]
    if "swing_lifecycle_bucket_discovery" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "swing_lifecycle_bucket_discovery" not in key
        ]
    if "swing_lifecycle_bucket_discovery" not in execution_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "swing_lifecycle_bucket_discovery" not in key
        ]
    if "daily_ev" in disabled_stage_flags or "runtime_approval_summary" in disabled_stage_flags:
        missing_downstream_links = []
    runtime_apply_gap_audit_status = str(runtime_apply_gap_audit.get("status") or "missing").strip()
    runtime_apply_gap_audit_summary = (
        runtime_apply_gap_audit.get("summary") if isinstance(runtime_apply_gap_audit.get("summary"), dict) else {}
    )
    runtime_apply_gap_audit_issues: list[str] = []
    runtime_gap_check_enabled = (
        "runtime_apply_gap_audit" not in disabled_stage_flags
        and ("runtime_apply_gap_audit" in execution_flags or bool(runtime_apply_gap_audit))
    )
    if runtime_gap_check_enabled:
        if not runtime_apply_gap_audit:
            runtime_apply_gap_audit_issues.append("runtime_apply_gap_audit_missing")
        if runtime_apply_gap_audit_status == "fail":
            runtime_apply_gap_audit_issues.append("runtime_apply_gap_audit_failed")
        if runtime_apply_gap_audit_summary.get("ai_review_retry_pending") is True:
            runtime_apply_gap_audit_issues.append("runtime_apply_gap_ai_review_retry_pending")
        if (
            int(runtime_apply_gap_audit_summary.get("critical_failure_count") or 0) > 0
            and not runtime_apply_gap_audit.get("retry_queue")
        ):
            runtime_apply_gap_audit_issues.append("runtime_apply_gap_fail_without_retry_queue")
        if bridge_report and _consumer_stale(runtime_apply_gap_audit, bridge_report):
            runtime_apply_gap_audit_issues.append("runtime_apply_gap_audit_stale_before_runtime_apply_bridge")
        if preopen_apply_next and _consumer_stale(runtime_apply_gap_audit, preopen_apply_next):
            runtime_apply_gap_audit_issues.append("runtime_apply_gap_audit_stale_before_threshold_preopen_apply")
    key_lineage_summary = (
        key_lineage_ledger.get("summary") if isinstance(key_lineage_ledger.get("summary"), dict) else {}
    )
    conversion_lane_summary = (
        conversion_lane.get("summary") if isinstance(conversion_lane.get("summary"), dict) else {}
    )
    conversion_kpi_status = "pass"
    conversion_kpi_issues: list[str] = []
    conversion_kpi_warnings: list[str] = []
    conversion_check_enabled = (
        execution_flags.get("key_lineage_ledger") is True
        or execution_flags.get("conversion_lane") is True
        or bool(key_lineage_ledger)
        or bool(conversion_lane)
    )
    if conversion_check_enabled and not key_lineage_ledger:
        conversion_kpi_issues.append("key_lineage_ledger_missing")
    if conversion_check_enabled and not conversion_lane:
        conversion_kpi_issues.append("conversion_lane_missing")
    if conversion_check_enabled and _safe_int(key_lineage_summary.get("key_mismatch_count")) > 0:
        conversion_kpi_issues.append("active_or_hypothesis_key_mismatch")
    if conversion_check_enabled and _safe_int(key_lineage_summary.get("catalog_missing_count")) > 0:
        conversion_kpi_issues.append("active_or_hypothesis_catalog_missing")
    if conversion_check_enabled and _safe_int(key_lineage_summary.get("preopen_missing_count")) > 0:
        conversion_kpi_issues.append("active_or_hypothesis_preopen_missing")
    if conversion_check_enabled and _safe_int(key_lineage_summary.get("not_instrumented_count")) > 0:
        conversion_kpi_warnings.append("active_or_hypothesis_not_instrumented")
    if conversion_check_enabled and _safe_int(conversion_lane_summary.get("conversion_candidate_count")) == 0 and conversion_lane:
        conversion_kpi_warnings.append("conversion_lane_no_candidates")
    if conversion_kpi_issues:
        conversion_kpi_status = "fail"
    elif conversion_kpi_warnings:
        conversion_kpi_status = "warning"
    stale_downstream_links: list[str] = []
    if "daily_ev" not in disabled_stage_flags:
        if downstream_links.get("threshold_cycle_ev_sources_workorder") and _consumer_stale(ev_report, workorder):
            stale_downstream_links.append("threshold_cycle_ev_stale_before_code_improvement_workorder")
        if (
            "pattern_lab_currentness_audit" not in disabled_stage_flags
            and downstream_links.get("threshold_cycle_ev_sources_pattern_lab_currentness_audit")
            and _consumer_stale(ev_report, currentness_audit)
        ):
            stale_downstream_links.append("threshold_cycle_ev_stale_before_pattern_lab_currentness_audit")
        if (
            "pattern_lab_ai_review" in execution_flags
            and "pattern_lab_ai_review" not in disabled_stage_flags
            and downstream_links.get("threshold_cycle_ev_sources_pattern_lab_ai_review")
            and _consumer_stale(ev_report, pattern_lab_ai_review)
        ):
            stale_downstream_links.append("threshold_cycle_ev_stale_before_pattern_lab_ai_review")
        if (
            "producer_gap_discovery" in execution_flags
            and "producer_gap_discovery" not in disabled_stage_flags
            and downstream_links.get("threshold_cycle_ev_sources_producer_gap_discovery")
            and _consumer_stale(ev_report, producer_gap_discovery)
        ):
            stale_downstream_links.append("threshold_cycle_ev_stale_before_producer_gap_discovery")
        if (
            "pattern_lab_propagation_audit" not in disabled_stage_flags
            and downstream_links.get("threshold_cycle_ev_sources_pattern_lab_propagation_audit")
            and _consumer_stale(ev_report, propagation_audit)
        ):
            stale_downstream_links.append("threshold_cycle_ev_stale_before_pattern_lab_propagation_audit")
    if "runtime_approval_summary" not in disabled_stage_flags:
        if downstream_links.get("runtime_approval_summary_sources_ev") and _consumer_stale(runtime_summary, ev_report):
            stale_downstream_links.append("runtime_approval_summary_stale_before_threshold_cycle_ev")
        if (
            "pattern_lab_propagation_audit" not in disabled_stage_flags
            and downstream_links.get("runtime_approval_summary_sources_pattern_lab_propagation_audit")
            and _consumer_stale(runtime_summary, propagation_audit)
        ):
            stale_downstream_links.append("runtime_approval_summary_stale_before_pattern_lab_propagation_audit")
        if (
            "pattern_lab_ai_review" in execution_flags
            and "pattern_lab_ai_review" not in disabled_stage_flags
            and downstream_links.get("runtime_approval_summary_sources_pattern_lab_ai_review")
            and _consumer_stale(runtime_summary, pattern_lab_ai_review)
        ):
            stale_downstream_links.append("runtime_approval_summary_stale_before_pattern_lab_ai_review")
    source_generation_warnings: list[str] = []
    freshness_sources = {
        "lifecycle_decision_matrix": ldm_report,
        "lifecycle_bucket_discovery": discovery_report,
        "swing_lifecycle_decision_matrix": swing_ldm_report,
        "swing_lifecycle_bucket_discovery": swing_bucket_discovery_report,
    }
    if "daily_ev" not in disabled_stage_flags:
        for label, source_payload in freshness_sources.items():
            if source_payload and _consumer_stale(ev_report, source_payload):
                source_generation_warnings.append(f"threshold_cycle_ev_stale_before_{label}")
    if "runtime_approval_summary" not in disabled_stage_flags:
        for label, source_payload in freshness_sources.items():
            if source_payload and _consumer_stale(runtime_summary, source_payload):
                source_generation_warnings.append(f"runtime_approval_summary_stale_before_{label}")
    if "lifecycle_decision_matrix" in disabled_stage_flags or "lifecycle_decision_matrix" not in execution_flags:
        source_generation_warnings = [
            key for key in source_generation_warnings if "lifecycle_decision_matrix" not in key
        ]
    if "swing_lifecycle_matrix" in disabled_stage_flags or "swing_lifecycle_matrix" not in execution_flags:
        source_generation_warnings = [
            key for key in source_generation_warnings if "swing_lifecycle_decision_matrix" not in key
        ]
    if "swing_lifecycle_bucket_discovery" in disabled_stage_flags or "swing_lifecycle_bucket_discovery" not in execution_flags:
        source_generation_warnings = [
            key for key in source_generation_warnings if "swing_lifecycle_bucket_discovery" not in key
        ]
    if "daily_ev" in disabled_stage_flags or "runtime_approval_summary" in disabled_stage_flags:
        source_generation_warnings = []
    handoff_warnings.extend(source_generation_warnings)
    if "code_improvement_workorder" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "code_improvement_workorder" not in key]
    if "pattern_lab_currentness_audit" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "pattern_lab_currentness_audit" not in key]
    if "pattern_lab_ai_review" not in execution_flags or "pattern_lab_ai_review" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "pattern_lab_ai_review" not in key]
    if "producer_gap_discovery" not in execution_flags or "producer_gap_discovery" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "producer_gap_discovery" not in key]
    if "stage_hook_workorder_discovery" not in execution_flags or "stage_hook_workorder_discovery" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "stage_hook_workorder_discovery" not in key]
    if "stage_hook_runtime_scaffold" not in execution_flags or "stage_hook_runtime_scaffold" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "stage_hook_runtime_scaffold" not in key]
    if "pattern_lab_propagation_audit" in disabled_stage_flags:
        stale_downstream_links = [key for key in stale_downstream_links if "pattern_lab_propagation_audit" not in key]
    if "daily_ev" in disabled_stage_flags or "runtime_approval_summary" in disabled_stage_flags:
        stale_downstream_links = []
    if stale_downstream_links and not require_done_marker:
        handoff_warnings.append("pending_done_stale_downstream_links_present")
    pending_done_marker = bool(start_line and done_line is None and not require_done_marker)
    execution_profile_status = "full_profile"
    if disabled_stage_flags:
        execution_profile_status = "recovered_partial_profile"
    elif done_line is None and start_line:
        execution_profile_status = "done_marker_missing" if require_done_marker else "pending_done_marker"

    status = "pass"
    strict_log_issues = list(log_issues)
    if not require_done_marker:
        strict_log_issues = [
            item
            for item in strict_log_issues
            if item not in {"postclose_fail_marker_present", "postclose_done_marker_missing"}
        ]

    if not start_line:
        if _postclose_not_yet_due(target_date):
            status = "not_yet_due"
        else:
            status = "fail"
            log_issues.append("postclose_start_marker_missing")
            strict_log_issues.append("postclose_start_marker_missing")
    elif predecessor_timeouts or strict_log_issues:
        status = "fail"
    elif done_line is None and require_done_marker:
        status = "fail"
        log_issues.append("postclose_done_marker_missing")
        strict_log_issues.append("postclose_done_marker_missing")
    elif missing_execution_flags:
        status = "fail"
        log_issues.append("postclose_done_marker_missing_required_flags")
    elif missing_required_artifacts:
        status = "fail"
    elif missing_downstream_links:
        status = "fail"
    elif runtime_apply_gap_audit_issues:
        status = "fail"
    elif conversion_kpi_status == "fail":
        status = "fail"
    elif stale_downstream_links and require_done_marker:
        status = "fail"
    elif workorder_snapshot_status == "missing_snapshot_identity":
        status = "fail"
    elif handoff_warnings or conversion_kpi_warnings:
        status = "warning"
    elif predecessor_waits:
        status = "warning"
    elif disabled_stage_flags:
        status = "warning"
    elif pending_done_marker:
        status = "pass_with_pending_done_marker"

    return {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "threshold_cycle_postclose_verification",
        "status": status,
        "log_path": str(LOG_PATH),
        "latest_start_marker": start_line,
        "latest_done_marker": done_line,
        "execution_profile": {
            "status": execution_profile_status,
            "require_done_marker": require_done_marker,
            "pending_done_marker": pending_done_marker,
            "marker_reconciliation_done": marker_reconciliation_done,
            "recovery_done": recovery_done,
            "recovery_action": recovery_action,
            "required_flags_checked": bool(done_line and not recovery_done),
            "flags": execution_flags,
            "disabled_stage_flags": disabled_stage_flags,
            "missing_required_flags": missing_execution_flags,
            "interpretation": (
                "latest DONE marker was produced by a recovery run with selected heavy stages disabled; "
                "same-date artifacts are still validated separately"
                if disabled_stage_flags
                else f"latest DONE marker was produced by controller recovery action `{recovery_action}`; execution flags are not asserted by this marker"
                if recovery_done
                else "latest DONE marker used full/default stage profile"
                if done_line
                else "wrapper-internal verification passed required artifacts; final DONE marker is checked by a later health check"
                if pending_done_marker
                else "latest START marker has no matching DONE marker"
            ),
        },
        "predecessor_integrity": {
            "status": (
                "not_yet_due"
                if status == "not_yet_due"
                else "pass_pending_done_marker"
                if status == "pass_with_pending_done_marker"
                else "fail"
                if predecessor_timeouts or strict_log_issues
                else "warning"
                if predecessor_waits
                else "pass"
            ),
            "wait_count": len(predecessor_waits),
            "timeout_count": len(predecessor_timeouts),
            "waits": predecessor_waits,
            "timeouts": predecessor_timeouts,
            "log_issues": sorted(set(log_issues)),
        },
        "artifact_status": artifact_status,
        "missing_required_artifacts": missing_required_artifacts,
        "workorder_snapshot": {
            **workorder_snapshot,
            "status": workorder_snapshot_status,
            "priority_rule": "prefer_generation_id_source_hash_lineage_over_mtime",
        },
        "downstream_links": downstream_links,
        "missing_downstream_links": missing_downstream_links,
        "stale_downstream_links": stale_downstream_links,
        "source_generation_warnings": sorted(set(source_generation_warnings)),
        "runtime_apply_gap_audit": {
            "status": runtime_apply_gap_audit_status,
            "issues": runtime_apply_gap_audit_issues,
            "summary": runtime_apply_gap_audit_summary,
            "retry_queue_count": len(runtime_apply_gap_audit.get("retry_queue") or []),
            "codex_directive_count": len(runtime_apply_gap_audit.get("codex_workorder_directives") or []),
            "runtime_apply_bridge_generated_at": bridge_report.get("generated_at"),
            "threshold_preopen_apply_next_generated_at": preopen_apply_next.get("generated_at"),
        },
        "conversion_kpi": {
            "status": conversion_kpi_status,
            "issues": conversion_kpi_issues,
            "warnings": conversion_kpi_warnings,
            "key_lineage_summary": key_lineage_summary,
            "conversion_lane_summary": conversion_lane_summary,
        },
        "handoff_warnings": sorted(set(handoff_warnings)),
        "clean_baseline_report_residue": clean_baseline_report_residue,
        "clean_baseline_analytics_residue": clean_baseline_analytics_residue,
        "source_quality_hard_block": source_quality_hard_block,
        "raw_row_exclusion_handoff": raw_row_exclusion_handoff,
        "ai_correction": ai_correction,
        "scalp_sim_overnight_source_quality": scalp_sim_overnight_quality,
        "entry_bucket_handoff": entry_bucket_handoff,
        "submit_bucket_handoff": submit_bucket_handoff,
        "submit_bucket_attribution_present": isinstance(submit_attribution, dict),
        "holding_bucket_handoff": holding_bucket_handoff,
        "holding_bucket_attribution_present": isinstance(holding_attribution, dict),
        "holding_source_present": holding_source_present,
        "exit_bucket_handoff": exit_bucket_handoff,
        "exit_bucket_attribution_present": isinstance(exit_attribution, dict),
        "exit_source_present": exit_source_present,
        "buy_funnel_submit_drought_handoff": buy_funnel_submit_drought_handoff,
        "scale_in_bucket_handoff": scale_in_bucket_handoff,
        "scale_in_bucket_attribution_present": isinstance(scale_in_attribution, dict),
        "scale_in_source_present": scale_in_source_present,
        "overnight_bucket_handoff": overnight_bucket_handoff,
        "overnight_bucket_attribution_present": isinstance(overnight_attribution, dict),
        "overnight_source_present": overnight_source_present,
        "lifecycle_flow_bucket_handoff": lifecycle_flow_bucket_handoff,
        "lifecycle_flow_bucket_attribution_present": isinstance(lifecycle_flow_attribution, dict),
        "lifecycle_bucket_discovery_handoff": lifecycle_bucket_discovery_handoff,
        "ldm_hypothesis_parent_refinement_consumption": ldm_refinement_consumption,
        "lifecycle_bucket_windows": lifecycle_bucket_windows,
        "swing_lifecycle_handoff": swing_lifecycle_handoff,
        "producer_gap_discovery_handoff": producer_gap_handoff,
        "stage_hook_workorder_handoff": stage_hook_handoff,
        "bottom_rebound_sim_handoff": bottom_rebound_sim_handoff,
        "active_sim_priority_handoff": active_sim_priority_handoff,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    predecessor = report.get("predecessor_integrity") if isinstance(report.get("predecessor_integrity"), dict) else {}
    workorder = report.get("workorder_snapshot") if isinstance(report.get("workorder_snapshot"), dict) else {}
    ai_correction = report.get("ai_correction") if isinstance(report.get("ai_correction"), dict) else {}
    runtime_gap = report.get("runtime_apply_gap_audit") if isinstance(report.get("runtime_apply_gap_audit"), dict) else {}
    overnight_quality = (
        report.get("scalp_sim_overnight_source_quality")
        if isinstance(report.get("scalp_sim_overnight_source_quality"), dict)
        else {}
    )
    entry_bucket = report.get("entry_bucket_handoff") if isinstance(report.get("entry_bucket_handoff"), dict) else {}
    submit_bucket = report.get("submit_bucket_handoff") if isinstance(report.get("submit_bucket_handoff"), dict) else {}
    holding_bucket = report.get("holding_bucket_handoff") if isinstance(report.get("holding_bucket_handoff"), dict) else {}
    exit_bucket = report.get("exit_bucket_handoff") if isinstance(report.get("exit_bucket_handoff"), dict) else {}
    buy_funnel_handoff = (
        report.get("buy_funnel_submit_drought_handoff")
        if isinstance(report.get("buy_funnel_submit_drought_handoff"), dict)
        else {}
    )
    scale_in_bucket = report.get("scale_in_bucket_handoff") if isinstance(report.get("scale_in_bucket_handoff"), dict) else {}
    overnight_bucket = report.get("overnight_bucket_handoff") if isinstance(report.get("overnight_bucket_handoff"), dict) else {}
    lifecycle_flow_bucket = (
        report.get("lifecycle_flow_bucket_handoff")
        if isinstance(report.get("lifecycle_flow_bucket_handoff"), dict)
        else {}
    )
    lifecycle_bucket = (
        report.get("lifecycle_bucket_discovery_handoff")
        if isinstance(report.get("lifecycle_bucket_discovery_handoff"), dict)
        else {}
    )
    ldm_refinement = (
        report.get("ldm_hypothesis_parent_refinement_consumption")
        if isinstance(report.get("ldm_hypothesis_parent_refinement_consumption"), dict)
        else {}
    )
    lifecycle_bucket_windows = (
        report.get("lifecycle_bucket_windows")
        if isinstance(report.get("lifecycle_bucket_windows"), dict)
        else {}
    )
    swing_lifecycle = (
        report.get("swing_lifecycle_handoff")
        if isinstance(report.get("swing_lifecycle_handoff"), dict)
        else {}
    )
    producer_gap = (
        report.get("producer_gap_discovery_handoff")
        if isinstance(report.get("producer_gap_discovery_handoff"), dict)
        else {}
    )
    stage_hook = (
        report.get("stage_hook_workorder_handoff")
        if isinstance(report.get("stage_hook_workorder_handoff"), dict)
        else {}
    )
    bottom_rebound = (
        report.get("bottom_rebound_sim_handoff")
        if isinstance(report.get("bottom_rebound_sim_handoff"), dict)
        else {}
    )
    active_priority = (
        report.get("active_sim_priority_handoff")
        if isinstance(report.get("active_sim_priority_handoff"), dict)
        else {}
    )
    active_priority_diagnosis = (
        active_priority.get("active_priority_match_absence_diagnosis")
        if isinstance(active_priority.get("active_priority_match_absence_diagnosis"), dict)
        else {}
    )
    lines = [
        f"# Threshold Cycle Postclose Verification - {report.get('date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- latest_start_marker: `{report.get('latest_start_marker') or '-'}`",
        f"- latest_done_marker: `{report.get('latest_done_marker') or '-'}`",
        f"- predecessor_status: `{predecessor.get('status')}`",
        f"- predecessor_wait_count: `{predecessor.get('wait_count')}`",
        f"- predecessor_timeout_count: `{predecessor.get('timeout_count')}`",
        f"- log_issues: `{predecessor.get('log_issues') or []}`",
        "",
        "## Execution Profile",
        f"- profile_status: `{(report.get('execution_profile') or {}).get('status') or '-'}`",
        f"- disabled_stage_flags: `{(report.get('execution_profile') or {}).get('disabled_stage_flags') or []}`",
        f"- missing_required_flags: `{(report.get('execution_profile') or {}).get('missing_required_flags') or []}`",
        f"- interpretation: `{(report.get('execution_profile') or {}).get('interpretation') or '-'}`",
        f"- missing_required_artifacts: `{report.get('missing_required_artifacts') or []}`",
        f"- missing_downstream_links: `{report.get('missing_downstream_links') or []}`",
        f"- stale_downstream_links: `{report.get('stale_downstream_links') or []}`",
        f"- runtime_apply_gap_issues: `{runtime_gap.get('issues') or []}`",
        "",
        "## Runtime Apply Gap Audit",
        f"- status: `{runtime_gap.get('status') or '-'}`",
        f"- retry_queue_count: `{runtime_gap.get('retry_queue_count') or 0}`",
        f"- codex_directive_count: `{runtime_gap.get('codex_directive_count') or 0}`",
        f"- summary: `{runtime_gap.get('summary') or {}}`",
        "",
        "## BUY Funnel Submit Drought Handoff",
        f"- status: `{buy_funnel_handoff.get('status')}`",
        f"- critical: `{buy_funnel_handoff.get('critical')}`",
        f"- missing: `{buy_funnel_handoff.get('missing') or []}`",
        "",
        "## Submit Bucket Handoff",
        f"- status: `{submit_bucket.get('status')}`",
        f"- attribution_present: `{report.get('submit_bucket_attribution_present')}`",
        f"- missing: `{submit_bucket.get('missing') or []}`",
        "",
        "## Holding Bucket Handoff",
        f"- status: `{holding_bucket.get('status')}`",
        f"- attribution_present: `{report.get('holding_bucket_attribution_present')}`",
        f"- source_present: `{report.get('holding_source_present')}`",
        f"- runtime_candidate_count: `{holding_bucket.get('runtime_candidate_count')}`",
        f"- bucket_count ev/runtime/expected: `{holding_bucket.get('threshold_cycle_ev_bucket_count')}` / `{holding_bucket.get('runtime_approval_summary_bucket_count')}` / `{holding_bucket.get('expected_bucket_count')}`",
        f"- workorder_count ev/runtime/expected: `{holding_bucket.get('threshold_cycle_ev_workorder_count')}` / `{holding_bucket.get('runtime_approval_summary_workorder_count')}` / `{holding_bucket.get('expected_workorder_count')}`",
        f"- missing: `{holding_bucket.get('missing') or []}`",
        "",
        "## Exit Bucket Handoff",
        f"- status: `{exit_bucket.get('status')}`",
        f"- attribution_present: `{report.get('exit_bucket_attribution_present')}`",
        f"- source_present: `{report.get('exit_source_present')}`",
        f"- runtime_candidate_count: `{exit_bucket.get('runtime_candidate_count')}`",
        f"- bucket_count ev/runtime/expected: `{exit_bucket.get('threshold_cycle_ev_bucket_count')}` / `{exit_bucket.get('runtime_approval_summary_bucket_count')}` / `{exit_bucket.get('expected_bucket_count')}`",
        f"- workorder_count ev/runtime/expected: `{exit_bucket.get('threshold_cycle_ev_workorder_count')}` / `{exit_bucket.get('runtime_approval_summary_workorder_count')}` / `{exit_bucket.get('expected_workorder_count')}`",
        f"- missing: `{exit_bucket.get('missing') or []}`",
        "",
        "## Lifecycle Flow Bucket Handoff",
        f"- status: `{lifecycle_flow_bucket.get('status')}`",
        f"- attribution_present: `{report.get('lifecycle_flow_bucket_attribution_present')}`",
        f"- flow_count: `{lifecycle_flow_bucket.get('flow_count')}`",
        f"- complete_flow_count: `{lifecycle_flow_bucket.get('complete_flow_count')}`",
        f"- direct_sim_record_complete_flow_count: `{lifecycle_flow_bucket.get('direct_sim_record_complete_flow_count')}`",
        f"- adm_bridge_complete_flow_count: `{lifecycle_flow_bucket.get('adm_bridge_complete_flow_count')}`",
        f"- fallback_complete_flow_count: `{lifecycle_flow_bucket.get('fallback_complete_flow_count')}`",
        f"- incomplete_flow_count: `{lifecycle_flow_bucket.get('incomplete_flow_count')}`",
        f"- complete_flow_rate: `{lifecycle_flow_bucket.get('complete_flow_rate')}`",
        f"- join_contract_blocked: `{lifecycle_flow_bucket.get('join_contract_blocked')}`",
        f"- bundle_ev_tuning_state: `{lifecycle_flow_bucket.get('bundle_ev_tuning_state')}`",
        f"- top_incomplete_reason: `{lifecycle_flow_bucket.get('top_incomplete_reason')}`",
        f"- missing: `{lifecycle_flow_bucket.get('missing') or []}`",
        "",
        "## AI Correction",
        f"- status: `{ai_correction.get('status') or '-'}`",
        f"- ai_status: `{ai_correction.get('ai_status') or '-'}`",
        f"- provider_status: `{ai_correction.get('provider_status') or '-'}`",
        f"- blocking_runtime_candidate_families: `{ai_correction.get('blocking_runtime_candidate_families') or []}`",
        f"- parse_warnings: `{ai_correction.get('parse_warnings') or []}`",
        f"- interpretation: `{ai_correction.get('interpretation') or '-'}`",
        "",
        "## Scalp Sim Overnight",
        f"- status: `{overnight_quality.get('status') or '-'}`",
        f"- decision_target: `{overnight_quality.get('decision_target') or 0}`",
        f"- active_undecided_count: `{overnight_quality.get('active_undecided_count') or 0}`",
        f"- decision_coverage_rate: `{overnight_quality.get('decision_coverage_rate')}`",
        f"- source_quality_status: `{overnight_quality.get('source_quality_status') or '-'}`",
        f"- source_quality_warnings: `{overnight_quality.get('source_quality_warnings') or []}`",
        f"- interpretation: `{overnight_quality.get('interpretation') or '-'}`",
        "",
        "## Entry Bucket Handoff",
        f"- status: `{entry_bucket.get('status') or '-'}`",
        f"- expected_candidate_ids: `{entry_bucket.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{entry_bucket.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{entry_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{entry_bucket.get('missing_workorder_order_ids') or []}`",
        f"- interpretation: `{entry_bucket.get('interpretation') or '-'}`",
        "",
        "## Scale-In Bucket Handoff",
        f"- attribution_present: `{report.get('scale_in_bucket_attribution_present')}`",
        f"- source_present: `{report.get('scale_in_source_present')}`",
        f"- status: `{scale_in_bucket.get('status') or '-'}`",
        f"- expected_candidate_ids: `{scale_in_bucket.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{scale_in_bucket.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{scale_in_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{scale_in_bucket.get('missing_workorder_order_ids') or []}`",
        f"- interpretation: `{scale_in_bucket.get('interpretation') or '-'}`",
        "",
        "## Overnight Bucket Handoff",
        f"- attribution_present: `{report.get('overnight_bucket_attribution_present')}`",
        f"- source_present: `{report.get('overnight_source_present')}`",
        f"- status: `{overnight_bucket.get('status') or '-'}`",
        f"- expected_candidate_ids: `{overnight_bucket.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{overnight_bucket.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{overnight_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{overnight_bucket.get('missing_workorder_order_ids') or []}`",
        f"- interpretation: `{overnight_bucket.get('interpretation') or '-'}`",
        "",
        "## Lifecycle Bucket Discovery Handoff",
        f"- status: `{lifecycle_bucket.get('status') or '-'}`",
        f"- source_contract_status: `{lifecycle_bucket.get('source_contract_status') or '-'}`",
        f"- ai_two_pass_review_status: `{lifecycle_bucket.get('ai_two_pass_review_status') or '-'}`",
        f"- expected_candidate_ids: `{lifecycle_bucket.get('expected_candidate_ids') or []}`",
        f"- live_auto_apply_families: `{lifecycle_bucket.get('live_auto_apply_families') or []}`",
        f"- missing_bridge_families: `{lifecycle_bucket.get('missing_bridge_families') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{lifecycle_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- workorder_needed_bucket_ids: `{lifecycle_bucket.get('workorder_needed_bucket_ids') or []}`",
        f"- ai_post_apply_followup_bucket_ids: `{lifecycle_bucket.get('ai_post_apply_followup_bucket_ids') or []}`",
        f"- warnings: `{lifecycle_bucket.get('warnings') or []}`",
        f"- interpretation: `{lifecycle_bucket.get('interpretation') or '-'}`",
        "",
        "## LDM Hypothesis Parent Refinement",
        f"- status: `{ldm_refinement.get('status') or '-'}`",
        f"- input/consumed: `{ldm_refinement.get('input_count') or 0}` / `{ldm_refinement.get('consumed_count') or 0}`",
        f"- closure_counts: `{ldm_refinement.get('closure_counts') or {}}`",
        f"- missing: `{ldm_refinement.get('missing') or []}`",
        f"- warnings: `{ldm_refinement.get('warnings') or []}`",
        f"- diagnosis_missing_warning_input_ids: `{ldm_refinement.get('diagnosis_missing_warning_input_ids') or []}`",
        f"- diagnosis_missing_fail_input_ids: `{ldm_refinement.get('diagnosis_missing_fail_input_ids') or []}`",
        f"- diagnosed_repeated_input_ids: `{ldm_refinement.get('diagnosed_repeated_input_ids') or []}`",
        f"- runtime_authority_violation_input_ids: `{ldm_refinement.get('runtime_authority_violation_input_ids') or []}`",
        "",
        "## Active Sim Priority Handoff",
        f"- status: `{active_priority.get('status') or '-'}`",
        f"- active_seed_ids: `{active_priority.get('active_seed_ids') or []}`",
        f"- observed_seed_ids: `{active_priority.get('observed_seed_ids') or []}`",
        f"- missing: `{active_priority.get('missing') or []}`",
        f"- warnings: `{active_priority.get('warnings') or []}`",
        f"- match_absence_diagnosis: `{active_priority_diagnosis.get('diagnosis') or '-'}`",
        f"- match_absence_reason: `{active_priority_diagnosis.get('reason') or '-'}`",
        f"- candidate_prefix_count: `{active_priority_diagnosis.get('candidate_prefix_count') or 0}`",
        f"- top_candidate_prefixes: `{active_priority_diagnosis.get('top_candidate_prefixes') or []}`",
        "",
        "## Lifecycle Bucket Windows",
        f"- status: `{lifecycle_bucket_windows.get('status') or '-'}`",
        f"- checked: `{lifecycle_bucket_windows.get('checked')}`",
        f"- windows: `{lifecycle_bucket_windows.get('windows') or {}}`",
        f"- missing: `{lifecycle_bucket_windows.get('missing') or []}`",
        f"- warnings: `{lifecycle_bucket_windows.get('warnings') or []}`",
        "",
        "## Swing Lifecycle Handoff",
        f"- status: `{swing_lifecycle.get('status') or '-'}`",
        f"- expected_candidate_ids: `{swing_lifecycle.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{swing_lifecycle.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{swing_lifecycle.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{swing_lifecycle.get('missing_workorder_order_ids') or []}`",
        f"- daily_simulation_consumed: `{swing_lifecycle.get('daily_simulation_consumed')}`",
        f"- ai_two_pass_review_status: `{swing_lifecycle.get('ai_two_pass_review_status') or '-'}`",
        f"- warnings: `{swing_lifecycle.get('warnings') or []}`",
        f"- interpretation: `{swing_lifecycle.get('interpretation') or '-'}`",
        "",
        "## Producer Gap Discovery Handoff",
        f"- status: `{producer_gap.get('status') or '-'}`",
        f"- ai_two_pass_review_status: `{producer_gap.get('ai_two_pass_review_status') or '-'}`",
        f"- audit_status: `{producer_gap.get('audit_status') or '-'}`",
        f"- expected_workorder_order_ids: `{producer_gap.get('expected_workorder_order_ids') or []}`",
        f"- missing_workorder_order_ids: `{producer_gap.get('missing_workorder_order_ids') or []}`",
        f"- missing: `{producer_gap.get('missing') or []}`",
        f"- interpretation: `{producer_gap.get('interpretation') or '-'}`",
        "",
        "## Stage Hook Workorder Handoff",
        f"- status: `{stage_hook.get('status') or '-'}`",
        f"- ai_two_pass_review_status: `{stage_hook.get('ai_two_pass_review_status') or '-'}`",
        f"- audit_status: `{stage_hook.get('audit_status') or '-'}`",
        f"- expected_workorder_order_ids: `{stage_hook.get('expected_workorder_order_ids') or []}`",
        f"- missing_workorder_order_ids: `{stage_hook.get('missing_workorder_order_ids') or []}`",
        f"- unconsumed_hook_candidate_ids: `{stage_hook.get('unconsumed_hook_candidate_ids') or []}`",
        f"- missing: `{stage_hook.get('missing') or []}`",
        f"- interpretation: `{stage_hook.get('interpretation') or '-'}`",
        "",
        "## Bottom Rebound Sim Handoff",
        f"- status: `{bottom_rebound.get('status') or '-'}`",
        f"- included: `{bottom_rebound.get('included')}`",
        f"- source_rows: `{bottom_rebound.get('bottom_rebound_source_rows') or 0}`",
        f"- selected_candidate_count: `{bottom_rebound.get('bottom_rebound_selected_candidate_count') or 0}`",
        f"- arm_count: `{bottom_rebound.get('bottom_rebound_arm_count') or 0}`",
        f"- persisted_candidate_count: `{bottom_rebound.get('bottom_rebound_persisted_candidate_count') or 0}`",
        f"- persisted_arm_count: `{bottom_rebound.get('bottom_rebound_persisted_arm_count') or 0}`",
        f"- missing: `{bottom_rebound.get('missing') or []}`",
        f"- interpretation: `{bottom_rebound.get('interpretation') or '-'}`",
        "",
        "## Workorder Snapshot",
        f"- generation_id: `{workorder.get('generation_id') or '-'}`",
        f"- source_hash: `{workorder.get('source_hash') or '-'}`",
        f"- snapshot_status: `{workorder.get('status') or '-'}`",
        f"- previous_generation_id: `{workorder.get('previous_generation_id') or '-'}`",
        f"- previous_source_hash: `{workorder.get('previous_source_hash') or '-'}`",
        f"- new_order_ids: `{workorder.get('new_order_ids') or []}`",
        f"- removed_order_ids: `{workorder.get('removed_order_ids') or []}`",
        f"- decision_changed_order_ids: `{workorder.get('decision_changed_order_ids') or []}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify threshold-cycle postclose chain integrity.")
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--allow-pending-done-marker",
        action="store_true",
        help=(
            "Allow wrapper-internal verification to pass when required artifacts are present "
            "but the wrapper has not emitted its final DONE marker yet."
        ),
    )
    args = parser.parse_args()

    report = build_threshold_cycle_postclose_verification(
        args.date,
        require_done_marker=not args.allow_pending_done_marker,
    )
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = verification_report_paths(args.date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    if report.get("status") == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
