"""Build a preopen threshold apply manifest from the latest postclose report."""

from __future__ import annotations

import argparse
import json
import os
import shlex
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.approval_contracts import annotate_approval_request
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.runtime_apply_bridge import (
    ENTRY_BRIDGE_FAMILY,
    SCALE_IN_BRIDGE_FAMILY,
    ldm_entry_runtime_bridge_artifact_path,
    ldm_scale_in_runtime_bridge_artifact_path,
    runtime_apply_bridge_report_path,
)
from src.engine.lifecycle_bucket_discovery import (
    bucket_catalog_path,
    discovery_report_path,
    sim_auto_approval_path,
)
from src.engine.swing.sim_auto_approval_control_tower import (
    swing_sim_auto_approval_path,
    swing_sim_policy_catalog_path,
)
from src.utils.constants import DATA_DIR


APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"
RUNTIME_ENV_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
OPERATOR_RUNTIME_ENV_LOCK_DIR = DATA_DIR / "threshold_cycle" / "operator_runtime_env_locks"
AI_REVIEW_DIR = REPORT_DIR / "threshold_cycle_ai_review"
CALIBRATION_REPORT_DIR = REPORT_DIR / "threshold_cycle_calibration"
SWING_RUNTIME_APPROVAL_REPORT_DIR = DATA_DIR / "report" / "swing_runtime_approval"
SWING_RUNTIME_APPROVAL_ARTIFACT_DIR = DATA_DIR / "threshold_cycle" / "approvals"
LATENCY_CLASSIFIER_RECOMMENDATION_DIR = DATA_DIR / "report" / "latency_classifier_recommendation"

AUTO_APPLY_MODES = {"auto_bounded_live"}
AUTO_APPLY_ALLOWED_STATES = {"adjust_up", "adjust_down", "hold"}
AUTO_APPLY_BLOCK_STATES = {"freeze", "hold_sample", "hold_no_edge"}
AUTO_APPLY_ROUTE_EXCLUDE_ACTIONS = {"exclude_from_threshold_candidate_review"}
AUTO_APPLY_ALLOWED_ROUTES = {"threshold_candidate", "normal_drift", ""}
NON_LIVE_SELECTABLE_FAMILIES = {
    "panic_lifecycle_actuator",
    "panic_entry_freeze_guard",
    "panic_buy_runner_tp_canary",
}
LOCK_ALLOWED_CLOSE_KEYWORDS = {
    "safety_revert",
    "severe_loss",
    "order_provenance",
    "provenance_breach",
    "stale_quote",
    "stale_context_or_quote",
    "hard_stop",
    "protect_stop",
    "emergency_stop",
    "order_failure",
    "receipt_missing",
}

TARGET_ENV_VALUE_KEYS = {
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "enabled",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC": "confirm_sec",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT": "buffer_pct",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT": "max_worsen_pct",
    "AI_SCORE65_74_RECOVERY_PROBE_ENABLED": "enabled",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE": "min_score",
    "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE": "max_score",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE": "min_buy_pressure",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL": "min_tick_accel",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP": "min_micro_vwap_bp",
    "AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION": "threshold_version",
    "AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE": "calibration_state",
    "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW": "max_budget_krw",
    "AI_WAIT6579_PROBE_CANARY_MAX_QTY": "max_qty",
    "SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP": "effective_qty_cap",
    "SCALPING_ENABLE_PYRAMID": "scalping_enable_pyramid",
    "REVERSAL_ADD_MIN_AI_SCORE": "reversal_add_min_ai_score",
    "REVERSAL_ADD_MIN_BUY_PRESSURE": "reversal_add_min_buy_pressure",
    "REVERSAL_ADD_MIN_TICK_ACCEL": "reversal_add_min_tick_accel",
    "SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED": "enabled",
    "SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC": "min_hold_sec",
    "SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT": "min_loss_pct",
    "SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT": "max_peak_profit_pct",
    "SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT": "ai_score_limit",
    "SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX": "recovery_prob_max",
    "OFI_AI_SMOOTHING_STALE_THRESHOLD_MS": "ofi_stale_threshold_ms",
    "OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED": "ofi_persistence_required",
    "HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT": "holding_bearish_confirm_worsen_pct",
    "HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC": "max_defer_sec",
    "HOLDING_FLOW_OVERRIDE_WORSEN_PCT": "worsen_floor_pct",
    "SWING_FLOOR_BULL": "floor_bull",
    "SWING_FLOOR_BEAR": "floor_bear",
    "SWING_SELECTION_TOP_K": "top_k",
    "ML_GATEKEEPER_REJECT_COOLDOWN": "reject_cooldown_sec",
    "SWING_MARKET_REGIME_SENSITIVITY": "regime_sensitivity",
    "SWING_SCALE_IN_REAL_CANARY_ENABLED": "enabled",
    "SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS": "allowed_arms",
    "SWING_SCALE_IN_REAL_CANARY_MAX_QTY": "max_order_qty",
    "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY": "max_orders_per_day",
    "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION": "max_orders_per_position",
    "SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW": "max_daily_notional_krw",
    "SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT": "require_approval_artifact",
    "SWING_ONE_SHARE_REAL_CANARY_ENABLED": "enabled",
    "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES": "allowed_codes",
    "SWING_ONE_SHARE_REAL_CANARY_MAX_QTY": "max_order_qty",
    "SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY": "max_new_entries_per_day",
    "SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS": "max_open_positions",
    "SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW": "max_total_notional_krw",
    "SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT": "require_approval_artifact",
    "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION": "max_ws_age_ms_for_caution",
    "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION": "max_ws_jitter_ms_for_caution",
    "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION": "max_spread_ratio_for_caution",
    "SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED": "recovery_enabled",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE": "recovery_min_signal_score",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS": "recovery_max_ws_age_ms",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS": "recovery_max_ws_jitter_ms",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO": "recovery_max_spread_ratio",
    "LIFECYCLE_DECISION_MATRIX_ENABLED": "enabled",
    "LIFECYCLE_DECISION_MATRIX_POLICY_FILE": "policy_file",
    "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION": "policy_version",
    "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED": "promote_enabled",
    "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY": "max_promotes_per_day",
    "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE": "min_stage_confidence",
    "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED": "runtime_effect_enabled",
    "LIFECYCLE_AI_CONTEXT_ENABLED": "lifecycle_ai_context_enabled",
    "LIFECYCLE_AI_CONTEXT_FILE": "lifecycle_ai_context_file",
    "LIFECYCLE_AI_CONTEXT_VERSION": "lifecycle_ai_context_version",
    "SCALP_ENTRY_ADM_ADVISORY_ENABLED": "entry_adm_advisory_enabled",
    "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED": "entry_adm_runtime_bias_enabled",
    "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED": "holding_exit_matrix_advisory_enabled",
    "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED": "holding_exit_matrix_runtime_bias_enabled",
    "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED": "holding_exit_matrix_scale_in_bias_enabled",
    "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED": "enabled",
    "SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS": "allowed_arms",
    "SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT": "min_profit_pct",
    "SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT": "max_profit_pct",
    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION": "max_orders_per_position",
    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY": "max_orders_per_day",
    "SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY": "max_daily",
    "SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT": "blocked_ai_score_max_share_pct",
    "SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT": "first_ai_wait_min_share_pct",
    "SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY": "time_bucket_policy",
    "LIFECYCLE_BUCKET_DISCOVERY_ENABLED": "enabled",
    "LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE": "policy_file",
    "LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION": "policy_version",
    "LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED": "live_auto_apply_enabled",
    "SWING_SIM_AUTO_POLICY_ENABLED": "enabled",
    "SWING_SIM_AUTO_POLICY_FILE": "policy_file",
    "SWING_SIM_AUTO_POLICY_VERSION": "policy_version",
    "SWING_SIM_AUTO_BOTTOM_REBOUND_SOURCE_ENABLED": "bottom_rebound_source_enabled",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _int_or_default(value: Any, default: int) -> int | None:
    if value is None or value == "":
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_phase0_real_canary_auto_approved(request: dict[str, Any]) -> bool:
    state = str(request.get("calibration_state") or "").strip()
    return state in {"auto_approved_real_canary", "auto_approved_real_canary_phase0"} and (
        bool(request.get("auto_approved_real_canary"))
        or bool(request.get("auto_approval_required"))
        or str(request.get("auto_approval_state") or "").strip() == "real_canary_phase0_auto_approved"
    )


def _latest_report_before(target_date: str) -> Path | None:
    candidates: list[tuple[str, Path]] = []
    for path in REPORT_DIR.glob("threshold_cycle_*.json"):
        report_date = path.stem.replace("threshold_cycle_", "")
        if report_date < target_date:
            candidates.append((report_date, path))
    for path in CALIBRATION_REPORT_DIR.glob("threshold_cycle_calibration_*_postclose.json"):
        report_date = path.stem.replace("threshold_cycle_calibration_", "").replace("_postclose", "")
        if report_date < target_date:
            candidates.append((report_date, path))
    if not candidates:
        return None
    return sorted(candidates)[-1][1]


def apply_manifest_path(target_date: str) -> Path:
    return APPLY_PLAN_DIR / f"threshold_apply_{target_date}.json"


def runtime_env_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.env"


def runtime_env_manifest_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.json"


def swing_runtime_approval_report_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_REPORT_DIR / f"swing_runtime_approval_{source_date}.json"


def swing_runtime_approval_artifact_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_runtime_approvals_{source_date}.json"


def swing_scale_in_real_canary_artifact_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_scale_in_real_canary_{source_date}.json"


def swing_one_share_real_canary_artifact_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_one_share_real_canary_{source_date}.json"


def scalp_sim_scale_in_window_artifact_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"scalp_sim_scale_in_window_expansion_{source_date}.json"


def _bridge_artifact_path_for_family(family: str, source_date: str) -> Path | None:
    if family == ENTRY_BRIDGE_FAMILY:
        return ldm_entry_runtime_bridge_artifact_path(source_date)
    if family == SCALE_IN_BRIDGE_FAMILY:
        return ldm_scale_in_runtime_bridge_artifact_path(source_date)
    return None


def _report_path_for_date(target_date: str, *, source_phase: str | None = None) -> Path:
    if source_phase == "intraday":
        return CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_intraday.json"
    if source_phase == "postclose":
        return CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"
    canonical = REPORT_DIR / f"threshold_cycle_{target_date}.json"
    if canonical.exists():
        return canonical
    postclose = CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"
    if postclose.exists():
        return postclose
    return canonical


def _ai_review_path_for_date(source_date: str, phase: str) -> Path:
    return AI_REVIEW_DIR / f"threshold_cycle_ai_review_{source_date}_{phase}.json"


def _load_ai_review(source_date: str | None, *, source_phase: str | None = None) -> dict[str, Any]:
    if not source_date:
        return {"status": "missing_source_date", "path": None, "items_by_family": {}}
    postclose_path = _ai_review_path_for_date(source_date, "postclose")
    intraday_path = _ai_review_path_for_date(source_date, "intraday")
    if source_phase == "intraday":
        preferred_paths = [intraday_path]
    else:
        preferred_paths = [postclose_path]
    for path in preferred_paths:
        if not path.exists():
            continue
        payload = _load_json(path)
        if str(payload.get("ai_status") or "").lower() != "parsed":
            if path == postclose_path:
                items = payload.get("items") if isinstance(payload.get("items"), list) else []
                return {
                    "status": str(payload.get("ai_status") or "unknown"),
                    "path": str(path),
                    "phase": "postclose",
                    "model": payload.get("ai_model"),
                    "provider_status": payload.get("ai_provider_status") or {},
                    "items_by_family": {
                        str(item.get("family") or ""): item
                        for item in items
                        if isinstance(item, dict) and item.get("family")
                    },
                }
            continue
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        return {
            "status": str(payload.get("ai_status") or "unknown"),
            "path": str(path),
            "phase": path.stem.rsplit("_", 1)[-1],
            "model": payload.get("ai_model"),
            "provider_status": payload.get("ai_provider_status") or {},
            "items_by_family": {
                str(item.get("family") or ""): item for item in items if isinstance(item, dict) and item.get("family")
            },
        }
    return {"status": "missing_ai_review", "path": None, "items_by_family": {}}


def _latency_classifier_recommendation_path(source_date: str) -> Path:
    return LATENCY_CLASSIFIER_RECOMMENDATION_DIR / f"latency_classifier_recommendation_{source_date}.json"


def _load_latency_classifier_candidates(source_date: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not source_date:
        return [], {"status": "missing_source_date", "path": None}
    path = _latency_classifier_recommendation_path(source_date)
    if not path.exists():
        return [], {"status": "missing_report", "path": str(path)}
    payload = _load_json(path)
    candidates = payload.get("calibration_candidates")
    if not isinstance(candidates, list):
        candidate = payload.get("calibration_candidate")
        candidates = [candidate] if isinstance(candidate, dict) else []
    normalized = [item for item in candidates if isinstance(item, dict)]
    selected_candidate = normalized[0] if normalized else {}
    selected_metrics = (
        selected_candidate.get("source_metrics")
        if isinstance(selected_candidate.get("source_metrics"), dict)
        else {}
    )
    return normalized, {
        "status": "loaded",
        "path": str(path),
        "latency_block_count": payload.get("latency_block_count"),
        "selected_profile_id": payload.get("selected_profile_id"),
        "profile_generation": payload.get("profile_generation"),
        "recommended_action": selected_metrics.get("recommended_action"),
        "recommended_action_reason": selected_metrics.get("recommended_action_reason"),
        "allowed_runtime_apply": selected_candidate.get("allowed_runtime_apply"),
        "calibration_state": selected_candidate.get("calibration_state"),
    }


def _runtime_env_name(target_env_key: str) -> str:
    if target_env_key.startswith("AI_SCORE65_74_RECOVERY_PROBE_"):
        return f"KORSTOCKSCAN_{target_env_key.removeprefix('AI_')}"
    if target_env_key.startswith("AI_WAIT6579_PROBE_CANARY_"):
        return f"KORSTOCKSCAN_{target_env_key.removeprefix('AI_')}"
    return f"KORSTOCKSCAN_{target_env_key}"


def _format_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _date_in_lock_window(lock: dict[str, Any], source_date: str | None, target_date: str) -> bool:
    basis_date = str(source_date or target_date or "").strip()
    if not basis_date:
        return False
    active_from = str(lock.get("active_from_date") or lock.get("created_date") or "").strip()
    active_until = str(
        lock.get("min_observation_until_date")
        or lock.get("expires_after_source_date")
        or lock.get("target_date")
        or ""
    ).strip()
    if active_from and basis_date < active_from:
        return False
    if active_until and basis_date > active_until:
        return False
    return True


def _load_operator_runtime_env_locks(source_date: str | None, target_date: str) -> list[dict[str, Any]]:
    locks: list[dict[str, Any]] = []
    if not OPERATOR_RUNTIME_ENV_LOCK_DIR.exists():
        return locks
    for path in sorted(OPERATOR_RUNTIME_ENV_LOCK_DIR.glob("*.json")):
        payload = _load_json(path)
        if not payload or not bool(payload.get("enabled", True)):
            continue
        family = str(payload.get("family") or "").strip()
        env_key = str(payload.get("env_key") or "").strip()
        env_overrides = payload.get("env_overrides") if isinstance(payload.get("env_overrides"), dict) else {}
        if not family or (not env_key and not env_overrides):
            continue
        if not _date_in_lock_window(payload, source_date, target_date):
            continue
        locks.append({**payload, "path": str(path)})
    return locks


def _lock_env_overrides(lock: dict[str, Any]) -> dict[str, str]:
    overrides = lock.get("env_overrides") if isinstance(lock.get("env_overrides"), dict) else {}
    if overrides:
        return {str(key): _format_env_value(value) for key, value in overrides.items()}
    env_key = str(lock.get("env_key") or "").strip()
    if not env_key:
        return {}
    value = lock.get("env_value", "true")
    return {env_key: _format_env_value(value)}


def _candidate_close_reasons(candidate: dict[str, Any], reject_reason: str) -> list[str]:
    reasons: list[str] = []
    if reject_reason:
        reasons.append(reject_reason)
    if bool(candidate.get("safety_revert_required")):
        reasons.append("safety_revert_required")
    for key in (
        "calibration_reason",
        "guard_reject_reason",
        "rollback_reason",
        "decision_reason",
        "source_quality_blocker",
        "source_quality_blockers",
        "block_reasons",
        "safety_reasons",
    ):
        value = candidate.get(key)
        if isinstance(value, list):
            reasons.extend(str(item) for item in value)
        elif value:
            reasons.append(str(value))
    metrics = candidate.get("source_metrics") if isinstance(candidate.get("source_metrics"), dict) else {}
    for key in ("block_reason", "submit_block_reason", "stale_reason", "order_provenance_status"):
        value = metrics.get(key)
        if value:
            reasons.append(str(value))
    return reasons


def _lock_allows_close(lock: dict[str, Any], close_reasons: list[str]) -> bool:
    allowed = {
        str(item).strip().lower()
        for item in (lock.get("allowed_close_reason_keywords") or [])
        if str(item).strip()
    }
    if not allowed:
        allowed = LOCK_ALLOWED_CLOSE_KEYWORDS
    lowered = " ".join(close_reasons).lower()
    return any(keyword in lowered for keyword in allowed)


def _locked_synthetic_candidate(lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": lock.get("family"),
        "stage": lock.get("stage") or "entry",
        "priority": int(lock.get("priority") or 10),
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "calibration_state": "operator_locked",
        "target_env_keys": [],
        "recommended_values": {"enabled": True},
        "threshold_version": lock.get("threshold_version") or f"{lock.get('family')}:operator_runtime_env_lock",
        "operator_runtime_env_lock_synthetic": True,
    }


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) == bool(right)
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return str(left) == str(right)


def _env_overrides_for_candidate(candidate: dict[str, Any]) -> dict[str, str]:
    recommended = candidate.get("recommended_values") if isinstance(candidate.get("recommended_values"), dict) else {}
    current = candidate.get("current_values") if isinstance(candidate.get("current_values"), dict) else {}
    calibration_state = str(candidate.get("calibration_state") or "")
    policy_or_family = str(candidate.get("policy_id") or candidate.get("family") or "")
    force_emit = policy_or_family in {
        "latency_classifier_runtime_profile",
        "swing_scale_in_real_canary_phase0",
        "swing_one_share_real_canary_phase0",
        "lifecycle_decision_matrix_runtime",
        ENTRY_BRIDGE_FAMILY,
        SCALE_IN_BRIDGE_FAMILY,
        "lifecycle_bucket_discovery_sim_auto_approval",
        "swing_sim_auto_approval",
    }
    overrides: dict[str, str] = {}
    for target_key in candidate.get("target_env_keys") or []:
        target_key = str(target_key)
        value_key = TARGET_ENV_VALUE_KEYS.get(target_key)
        if not value_key or value_key not in recommended:
            continue
        value = recommended[value_key]
        if value_key == "enabled" and calibration_state == "adjust_up" and not bool(current.get(value_key)):
            value = True
        if (not force_emit) and _values_equal(current.get(value_key), value):
            continue
        overrides[_runtime_env_name(target_key)] = _format_env_value(value)
    return overrides


def _score65_74_entry_unlock_candidate(candidate: dict[str, Any]) -> bool:
    if str(candidate.get("family") or "") != "score65_74_recovery_probe":
        return False
    metrics = candidate.get("source_metrics") if isinstance(candidate.get("source_metrics"), dict) else {}
    if bool(metrics.get("entry_unlock_probe_ready")):
        return True
    try:
        sample_count = int(candidate.get("sample_count") or 0)
        sample_floor = int(candidate.get("sample_floor") or 0)
    except Exception:
        return False
    if sample_floor <= 0 or sample_count < sample_floor:
        return False
    try:
        avg_ev = float(
            metrics.get("score60_74_avg_expected_ev_pct")
            if metrics.get("score60_74_avg_expected_ev_pct") is not None
            else metrics.get("score65_74_avg_expected_ev_pct")
            or 0.0
        )
        avg_close = float(
            metrics.get("score60_74_avg_close_10m_pct")
            if metrics.get("score60_74_avg_close_10m_pct") is not None
            else metrics.get("score65_74_avg_close_10m_pct")
            or 0.0
        )
    except Exception:
        return False
    risk_gate = str(metrics.get("risk_regime_gate_state") or "").lower()
    submitted = float(metrics.get("order_bundle_submitted") or 0.0)
    return (
        avg_ev >= 2.0
        and avg_close >= 1.0
        and submitted <= 0.0
        and risk_gate != "confirmed_panic"
    )


def _load_swing_runtime_approval_bundle(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {
            "request_report": None,
            "approval_artifact": None,
            "requests": [],
            "approved_requests": [],
            "blocked": ["missing_source_date"],
        }
    request_path = swing_runtime_approval_report_path(source_date)
    artifact_path = swing_runtime_approval_artifact_path(source_date)
    one_share_artifact_path = swing_one_share_real_canary_artifact_path(source_date)
    scale_artifact_path = swing_scale_in_real_canary_artifact_path(source_date)
    request_report = _load_json(request_path)
    artifact = _load_json(artifact_path)
    one_share_artifact = _load_json(one_share_artifact_path)
    scale_artifact = _load_json(scale_artifact_path)
    requests = request_report.get("approval_requests") if isinstance(request_report.get("approval_requests"), list) else []
    real_canary_policy = (
        request_report.get("real_canary_policy") if isinstance(request_report.get("real_canary_policy"), dict) else {}
    )
    scale_in_real_canary_policy = (
        request_report.get("scale_in_real_canary_policy")
        if isinstance(request_report.get("scale_in_real_canary_policy"), dict)
        else {}
    )
    approved_items = artifact.get("approved_requests") if isinstance(artifact.get("approved_requests"), list) else []
    approved_ids = {
        str(item.get("approval_id") or "")
        for item in approved_items
        if isinstance(item, dict) and bool(item.get("approved", True))
    }
    if bool(one_share_artifact.get("approved")) and str(one_share_artifact.get("policy_id") or "") == "swing_one_share_real_canary_phase0":
        for approval_id in one_share_artifact.get("approved_request_ids") or []:
            if approval_id:
                approved_ids.add(str(approval_id))
    if bool(scale_artifact.get("approved")) and str(scale_artifact.get("policy_id") or "") == "swing_scale_in_real_canary_phase0":
        for approval_id in scale_artifact.get("approved_request_ids") or []:
            if approval_id:
                approved_ids.add(str(approval_id))
    requests_by_id = {
        str(item.get("approval_id") or ""): item
        for item in requests
        if isinstance(item, dict) and item.get("approval_id")
    }
    scale_requests = [
        item
        for item in requests
        if isinstance(item, dict)
        and str(item.get("policy_id") or item.get("family") or "") == "swing_scale_in_real_canary_phase0"
    ]
    one_share_requests = [
        item
        for item in requests
        if isinstance(item, dict)
        and str(item.get("policy_id") or item.get("family") or "") == "swing_one_share_real_canary_phase0"
    ]
    non_scale_requests = [
        item
        for item in requests
        if isinstance(item, dict)
        and str(item.get("policy_id") or item.get("family") or "") != "swing_scale_in_real_canary_phase0"
        and str(item.get("policy_id") or item.get("family") or "") != "swing_one_share_real_canary_phase0"
    ]
    approved_requests = []
    blocked: list[str] = []
    if non_scale_requests and not artifact:
        blocked.append("approval_artifact_missing")
    # Phase0 real canaries are auto-approved from the source request report. Optional
    # artifacts may still narrow allowlists/caps, but missing artifacts no longer block.
    for item in one_share_requests:
        approval_id = str(item.get("approval_id") or "")
        if approval_id and _is_phase0_real_canary_auto_approved(item):
            approved_ids.add(approval_id)
        elif approval_id and approval_id not in approved_ids:
            blocked.append(f"one_share_real_canary_auto_approval_missing:{approval_id}")
    for item in scale_requests:
        approval_id = str(item.get("approval_id") or "")
        if approval_id and _is_phase0_real_canary_auto_approved(item):
            approved_ids.add(approval_id)
        elif approval_id and approval_id not in approved_ids:
            blocked.append(f"scale_in_real_canary_auto_approval_missing:{approval_id}")
    for approval_id in sorted(approved_ids):
        request = requests_by_id.get(approval_id)
        if not request:
            blocked.append(f"approval_request_not_found:{approval_id}")
            continue
        request_policy = str(request.get("policy_id") or request.get("family") or "")
        if request_policy == "swing_one_share_real_canary_phase0":
            request_codes = {
                str(value).zfill(6)
                for value in (
                    request.get("candidate_codes")
                    or [item.get("code") for item in (request.get("candidate_rows") or []) if isinstance(item, dict)]
                    or []
                )
                if str(value or "").strip()
            }
            artifact_codes = {
                str(value).zfill(6)
                for value in (one_share_artifact.get("allowed_codes") or [])
                if str(value or "").strip()
            }
            if not artifact_codes:
                artifact_codes = set(request_codes)
            if not artifact_codes:
                blocked.append(f"one_share_real_canary_allowed_codes_missing:{approval_id}")
                continue
            if request_codes and not artifact_codes.issubset(request_codes):
                blocked.append(f"one_share_real_canary_allowed_codes_mismatch:{approval_id}")
                continue
            request_values = request.get("recommended_values") if isinstance(request.get("recommended_values"), dict) else {}
            max_order_qty = _int_or_default(one_share_artifact.get("max_order_qty") or request_values.get("max_order_qty"), 1)
            max_new_entries = _int_or_default(
                one_share_artifact.get("max_new_entries_per_day")
                or request_values.get("max_new_entries_per_day"),
                1,
            )
            max_open_positions = _int_or_default(
                one_share_artifact.get("max_open_positions") or request_values.get("max_open_positions"),
                3,
            )
            max_total_notional = _int_or_default(
                one_share_artifact.get("max_total_notional_krw")
                or request_values.get("max_total_notional_krw"),
                300000,
            )
            if max_order_qty != 1:
                blocked.append(f"one_share_real_canary_qty_cap_mismatch:{approval_id}")
                continue
            if max_new_entries != 1:
                blocked.append(f"one_share_real_canary_daily_entry_cap_mismatch:{approval_id}")
                continue
            if not isinstance(max_open_positions, int) or max_open_positions < 1 or max_open_positions > 3:
                blocked.append(f"one_share_real_canary_open_position_cap_mismatch:{approval_id}")
                continue
            if not isinstance(max_total_notional, int) or max_total_notional < 1 or max_total_notional > 300000:
                blocked.append(f"one_share_real_canary_notional_cap_mismatch:{approval_id}")
                continue
            request = {
                **request,
                "recommended_values": {
                    **(request.get("recommended_values") or {}),
                    "allowed_codes": ",".join(sorted(artifact_codes)),
                    "max_order_qty": max_order_qty,
                    "max_new_entries_per_day": max_new_entries,
                    "max_open_positions": max_open_positions,
                    "max_total_notional_krw": max_total_notional,
                    "require_approval_artifact": False,
                },
                "auto_approval_state": "real_canary_phase0_auto_approved",
            }
        if request_policy == "swing_scale_in_real_canary_phase0":
            allowed = set(str(value).upper() for value in (request.get("allowed_actions") or []))
            artifact_allowed = set(str(value).upper() for value in (scale_artifact.get("allowed_actions") or []))
            if not artifact_allowed:
                artifact_allowed = set(allowed)
            if not artifact_allowed or not artifact_allowed.issubset(allowed):
                blocked.append(f"scale_in_real_canary_allowed_actions_mismatch:{approval_id}")
                continue
            request_values = request.get("recommended_values") if isinstance(request.get("recommended_values"), dict) else {}
            max_order_qty = _int_or_default(scale_artifact.get("max_order_qty") or request_values.get("max_order_qty"), 1)
            max_orders_per_day = _int_or_default(
                scale_artifact.get("max_orders_per_day") or request_values.get("max_orders_per_day"),
                1,
            )
            max_orders_per_position = _int_or_default(
                scale_artifact.get("max_orders_per_position") or request_values.get("max_orders_per_position"),
                1,
            )
            max_daily_notional = _int_or_default(
                scale_artifact.get("max_daily_notional_krw") or request_values.get("max_daily_notional_krw"),
                100000,
            )
            if max_order_qty != 1:
                blocked.append(f"scale_in_real_canary_qty_cap_mismatch:{approval_id}")
                continue
            if max_orders_per_day != 1:
                blocked.append(f"scale_in_real_canary_daily_order_cap_mismatch:{approval_id}")
                continue
            if max_orders_per_position != 1:
                blocked.append(f"scale_in_real_canary_position_order_cap_mismatch:{approval_id}")
                continue
            if not isinstance(max_daily_notional, int) or max_daily_notional < 1 or max_daily_notional > 100000:
                blocked.append(f"scale_in_real_canary_daily_notional_cap_mismatch:{approval_id}")
                continue
            request = {
                **request,
                "recommended_values": {
                    **(request.get("recommended_values") or {}),
                    "allowed_arms": ",".join(sorted(artifact_allowed)),
                    "max_order_qty": max_order_qty,
                    "max_orders_per_day": max_orders_per_day,
                    "max_orders_per_position": max_orders_per_position,
                    "max_daily_notional_krw": max_daily_notional,
                    "require_approval_artifact": False,
                },
                "auto_approval_state": "real_canary_phase0_auto_approved",
            }
        approval_state = (
            "auto_approved_real_canary_phase0"
            if request_policy in {"swing_one_share_real_canary_phase0", "swing_scale_in_real_canary_phase0"}
            else "approved_live"
        )
        approved_requests.append({**request, "approval_state": approval_state})
    return {
        "request_report": str(request_path) if request_path.exists() else None,
        "approval_artifact": str(artifact_path) if artifact_path.exists() else None,
        "one_share_real_canary_approval_artifact": (
            str(one_share_artifact_path) if one_share_artifact_path.exists() else None
        ),
        "scale_in_real_canary_approval_artifact": (
            str(scale_artifact_path) if scale_artifact_path.exists() else None
        ),
        "requests": requests,
        "approved_requests": approved_requests,
        "blocked": blocked,
        "artifact_payload": artifact,
        "one_share_real_canary_artifact_payload": one_share_artifact,
        "scale_in_real_canary_artifact_payload": scale_artifact,
        "real_canary_policy": real_canary_policy,
        "scale_in_real_canary_policy": scale_in_real_canary_policy,
    }


def _select_swing_approved_candidates(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    selected_by_stage: dict[str, str] = {}
    for item in bundle.get("approved_requests") or []:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        policy_id = str(item.get("policy_id") or "")
        is_scale_in_real_canary = policy_id == "swing_scale_in_real_canary_phase0" or family == "swing_scale_in_real_canary_phase0"
        is_one_share_real_canary = policy_id == "swing_one_share_real_canary_phase0" or family == "swing_one_share_real_canary_phase0"
        stage = str(item.get("stage") or "unknown")
        candidate = {
            **item,
            "calibration_state": "approved_live",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "one_share_real_canary": bool(is_one_share_real_canary),
            "scale_in_real_canary": bool(is_scale_in_real_canary),
        }
        overrides = _env_overrides_for_candidate(candidate)
        reject_reason = ""
        if bool(item.get("actual_order_submitted")):
            reject_reason = "actual_order_submission_not_allowed"
        elif (not is_scale_in_real_canary) and (not is_one_share_real_canary) and not bool(item.get("dry_run_required", True)):
            reject_reason = "dry_run_required_missing"
        elif stage in selected_by_stage:
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage]}"
        elif not overrides:
            reject_reason = "no_runtime_env_override"
        decision = {
            "approval_id": item.get("approval_id"),
            "family": family,
            "stage": stage,
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason
            or (
                "real_canary_phase0_auto_approval_accepted"
                if is_scale_in_real_canary or is_one_share_real_canary
                else "user_approval_artifact_accepted"
            ),
            "env_overrides": overrides if not reject_reason else {},
            "dry_run_required": not is_scale_in_real_canary,
            "one_share_real_canary": bool(is_one_share_real_canary),
            "scale_in_real_canary": bool(is_scale_in_real_canary),
        }
        decisions.append(decision)
        if reject_reason:
            continue
        selected_by_stage[stage] = family
        selected.append(candidate)
        env_overrides.update(overrides)
    if env_overrides:
        env_overrides["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] = "true"
    return selected, decisions, env_overrides


def _load_scalp_sim_scale_in_window_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "approved_request": None, "blocked": ["missing_source_date"]}
    path = scalp_sim_scale_in_window_artifact_path(source_date)
    payload = _load_json(path)
    blocked: list[str] = []
    if not payload:
        blocked.append("approval_artifact_missing")
    elif str(payload.get("policy_id") or payload.get("family") or "") != "scalp_sim_scale_in_window_expansion":
        blocked.append("approval_policy_mismatch")
    elif not bool(payload.get("approved")):
        blocked.append("sim_auto_approval_not_approved")
    elif payload.get("approval_state") != "sim_auto_approved":
        blocked.append("sim_auto_approval_state_invalid")
    elif bool(payload.get("human_approval_required")):
        blocked.append("human_approval_required_not_allowed_for_sim_auto")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    elif payload.get("runtime_effect") is not False:
        blocked.append("runtime_effect_not_allowed")
    elif payload.get("broker_order_forbidden") is not True:
        blocked.append("broker_order_forbidden_contract_missing")
    elif payload.get("source_quality_status") not in {None, "pass"}:
        blocked.append("source_quality_blocked")
    request = None
    if payload and not blocked:
        recommended = payload.get("recommended_values") if isinstance(payload.get("recommended_values"), dict) else {}
        request = {
            "family": "scalp_sim_scale_in_window_expansion",
            "policy_id": "scalp_sim_scale_in_window_expansion",
            "stage": "scale_in",
            "calibration_state": "sim_auto_approved",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "target_env_keys": payload.get("target_env_keys") or [],
            "recommended_values": recommended,
            "current_values": {
                "enabled": False,
                "allowed_arms": "",
                "min_profit_pct": None,
                "max_profit_pct": None,
                "max_orders_per_position": None,
                "max_orders_per_day": None,
            },
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "sim_auto_approval_only",
        }
    return {
        "artifact": str(path) if path.exists() else None,
        "approved_request": request,
        "blocked": blocked,
        "artifact_payload": payload,
    }


def _select_scalp_sim_scale_in_window_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    request = bundle.get("approved_request") if isinstance(bundle.get("approved_request"), dict) else None
    if not request:
        return [], [], {}
    overrides = _env_overrides_for_candidate(request)
    reject_reason = ""
    if not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "family": request.get("family"),
        "stage": request.get("stage"),
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "sim_auto_approval_artifact_accepted",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return ([request], [decision], overrides) if not reject_reason else ([], [decision], {})


def _artifact_matches_bridge_candidate(artifact: dict[str, Any], candidate: dict[str, Any]) -> bool:
    candidate_id = str(candidate.get("candidate_id") or "")
    explicit_candidate_id = str(artifact.get("candidate_id") or artifact.get("bridge_candidate_id") or "")
    if explicit_candidate_id and explicit_candidate_id != candidate_id:
        return False
    allowed_ids: set[str] = set()
    for key in ("approved_candidate_ids", "approved_bridge_candidate_ids", "approved_request_ids"):
        allowed_ids.update(str(value) for value in artifact.get(key) or [] if str(value or "").strip())
    if allowed_ids and candidate_id not in allowed_ids:
        return False
    return True


def _load_runtime_apply_bridge_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {
            "request_report": None,
            "artifacts": {},
            "candidates": [],
            "approved_requests": [],
            "blocked": ["missing_source_date"],
        }
    report_path = runtime_apply_bridge_report_path(source_date)
    report = _load_json(report_path)
    candidates = report.get("candidates") if isinstance(report.get("candidates"), list) else []
    artifacts: dict[str, str | None] = {}
    artifact_payloads: dict[str, dict[str, Any]] = {}
    approved_requests: list[dict[str, Any]] = []
    blocked: list[str] = []
    bridge_families = {ENTRY_BRIDGE_FAMILY, SCALE_IN_BRIDGE_FAMILY}
    if not report:
        blocked.append("runtime_apply_bridge_report_missing")

    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        if family not in bridge_families:
            continue
        artifact_path = _bridge_artifact_path_for_family(family, source_date)
        artifact = _load_json(artifact_path) if artifact_path else {}
        artifacts[family] = str(artifact_path) if artifact_path and artifact_path.exists() else None
        artifact_payloads[family] = artifact
        candidate_id = str(item.get("candidate_id") or "")
        contract = annotate_approval_request({"family": family}, source_date)
        item_blocked: list[str] = []
        auto_live = (
            str(item.get("bridge_candidate_state") or "") == "live_auto_apply_ready"
            and bool(item.get("allowed_runtime_apply"))
            and bool(item.get("live_auto_apply"))
            and not bool(item.get("approval_required"))
        )
        if not bool(contract.get("approval_live_ready")):
            item_blocked.append("approval_contract_not_live_ready")
        if str(item.get("bridge_candidate_state") or "") != "live_auto_apply_ready":
            item_blocked.append(f"runtime_apply_blocked_bridge_not_ready:{item.get('bridge_candidate_state')}")
        if not bool(item.get("allowed_runtime_apply")):
            item_blocked.append("runtime_apply_not_allowed")
        if not auto_live:
            item_blocked.append("runtime_apply_bridge_auto_live_contract_missing")
        if item_blocked:
            blocked.extend(f"{reason}:{family}" for reason in item_blocked)
            continue
        recommended = item.get("recommended_values") if isinstance(item.get("recommended_values"), dict) else {}
        approved_requests.append(
            {
                **item,
                "policy_id": family,
                "approval_id": f"{family}:live_auto_apply:{source_date}",
                "approval_state": "auto_live",
                "approval_artifact": None,
                "approval_runtime_scope": contract.get("approval_runtime_scope"),
                "calibration_state": "live_auto_apply",
                "threshold_version": recommended.get("threshold_version") or f"{family}:{source_date}",
                "allowed_runtime_apply": True,
                "safety_revert_required": False,
                "runtime_apply_bridge_family": family,
                "bridge_candidate_id": candidate_id,
                "source_bucket_key": ",".join(str(value) for value in item.get("source_bucket_keys") or []),
                "actual_runtime_effect": item.get("runtime_effect_after_approval"),
                "lifecycle_bucket_discovery_bucket_id": item.get("lifecycle_bucket_discovery_bucket_id"),
                "lifecycle_bucket_discovery_ai_review_status": item.get(
                    "lifecycle_bucket_discovery_ai_review_status"
                ),
                "lifecycle_bucket_discovery_ai_followup_required": item.get(
                    "lifecycle_bucket_discovery_ai_followup_required"
                ),
                "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get(
                    "lifecycle_bucket_discovery_ai_block_ignored_reason"
                ),
                "post_apply_verification_required": bool(
                    item.get("lifecycle_bucket_discovery_ai_followup_required")
                ),
                "actual_order_submitted": False,
                "decision_authority": (
                    "lifecycle_bucket_discovery_live_auto_apply"
                ),
            }
        )
    return {
        "request_report": str(report_path) if report_path.exists() else None,
        "artifacts": artifacts,
        "artifact_payloads": artifact_payloads,
        "candidates": candidates,
        "approved_requests": approved_requests,
        "blocked": blocked,
    }


def _select_runtime_apply_bridge_approval(
    bundle: dict[str, Any],
    *,
    include_families: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    selected_by_stage: dict[str, str] = {}
    for item in sorted(bundle.get("approved_requests") or [], key=lambda row: int(row.get("priority") or 999)):
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        stage = str(item.get("stage") or "unknown")
        overrides = _env_overrides_for_candidate(item)
        reject_reason = ""
        if include_families is not None and family not in include_families:
            reject_reason = "operator_family_filter_excluded"
        elif bool(item.get("actual_order_submitted")):
            reject_reason = "actual_order_submission_not_allowed"
        elif not bool(item.get("allowed_runtime_apply")):
            reject_reason = "runtime_apply_not_allowed"
        elif stage in selected_by_stage:
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage]}"
        elif not overrides:
            reject_reason = "no_runtime_env_override"
        decision = {
            "approval_id": item.get("approval_id"),
            "family": family,
            "stage": stage,
            "bridge_candidate_id": item.get("bridge_candidate_id"),
            "runtime_apply_bridge_family": item.get("runtime_apply_bridge_family"),
            "source_bucket_keys": item.get("source_bucket_keys") or [],
            "actual_runtime_effect": item.get("actual_runtime_effect"),
            "lifecycle_bucket_discovery_bucket_id": item.get("lifecycle_bucket_discovery_bucket_id"),
            "lifecycle_bucket_discovery_ai_review_status": item.get(
                "lifecycle_bucket_discovery_ai_review_status"
            ),
            "lifecycle_bucket_discovery_ai_followup_required": item.get(
                "lifecycle_bucket_discovery_ai_followup_required"
            ),
            "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get(
                "lifecycle_bucket_discovery_ai_block_ignored_reason"
            ),
            "post_apply_verification_required": bool(
                item.get("lifecycle_bucket_discovery_ai_followup_required")
            ),
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason
            or (
                "lifecycle_bucket_discovery_live_auto_apply"
                if str(item.get("approval_state") or "") == "auto_live"
                else "user_approval_artifact_accepted_bridge_ready"
            ),
            "env_overrides": overrides if not reject_reason else {},
            "actual_order_submitted": False,
        }
        decisions.append(decision)
        if reject_reason:
            continue
        selected_by_stage[stage] = family
        selected.append(item)
        env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _load_lifecycle_bucket_sim_auto_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "approved_request": None, "blocked": ["missing_source_date"]}
    artifact_path = sim_auto_approval_path(source_date)
    discovery_path = discovery_report_path(source_date)
    catalog_path = bucket_catalog_path(source_date)
    payload = _load_json(artifact_path)
    blocked: list[str] = []
    if not payload:
        blocked.append("sim_auto_approval_missing")
    elif not bool(payload.get("approved")):
        blocked.append("sim_auto_approval_not_approved")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    if not catalog_path.exists():
        blocked.append("bucket_catalog_missing")
    approved_request = None
    if not blocked:
        approved_request = {
            "family": "lifecycle_bucket_discovery_sim_auto_approval",
            "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
            "stage": "sim_lifecycle",
            "priority": 89,
            "approval_id": f"lifecycle_bucket_discovery_sim_auto_approval:{source_date}",
            "approval_state": "auto_sim",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "calibration_state": "sim_auto_approved",
            "target_env_keys": [
                "LIFECYCLE_BUCKET_DISCOVERY_ENABLED",
                "LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE",
                "LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION",
                "LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED",
            ],
            "recommended_values": {
                "enabled": True,
                "policy_file": str(catalog_path),
                "policy_version": f"lifecycle_bucket_discovery:{source_date}",
                "live_auto_apply_enabled": True,
            },
            "current_values": {
                "enabled": False,
                "policy_file": "",
                "policy_version": "",
                "live_auto_apply_enabled": False,
            },
            "actual_order_submitted": False,
            "decision_authority": "postclose_lifecycle_bucket_discovery_sim_auto",
        }
    return {
        "artifact": str(artifact_path) if artifact_path.exists() else None,
        "discovery_report": str(discovery_path) if discovery_path.exists() else None,
        "catalog": str(catalog_path) if catalog_path.exists() else None,
        "approved_request": approved_request,
        "blocked": blocked,
    }


def _select_lifecycle_bucket_sim_auto_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    item = bundle.get("approved_request")
    decisions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    if not isinstance(item, dict):
        decisions.append(
            {
                "family": "lifecycle_bucket_discovery_sim_auto_approval",
                "selected": False,
                "decision_reason": ",".join(str(reason) for reason in bundle.get("blocked") or []) or "sim_auto_approval_missing",
                "env_overrides": {},
                "actual_order_submitted": False,
            }
        )
        return selected, decisions, env_overrides
    overrides = _env_overrides_for_candidate(item)
    reject_reason = ""
    if not bool(item.get("allowed_runtime_apply")):
        reject_reason = "runtime_apply_not_allowed"
    elif bool(item.get("actual_order_submitted")):
        reject_reason = "actual_order_submitted_not_allowed"
    elif not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "approval_id": item.get("approval_id"),
        "family": item.get("family"),
        "stage": item.get("stage"),
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "lifecycle_bucket_discovery_sim_auto_apply",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
    }
    decisions.append(decision)
    if reject_reason:
        return selected, decisions, env_overrides
    selected.append(item)
    env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _load_swing_sim_auto_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "catalog": None, "approved_request": None, "blocked": ["missing_source_date"]}
    artifact_path = swing_sim_auto_approval_path(source_date)
    catalog_path = swing_sim_policy_catalog_path(source_date)
    payload = _load_json(artifact_path)
    blocked: list[str] = []
    if not payload:
        blocked.append("swing_sim_auto_approval_missing")
    elif payload.get("report_type") != "swing_sim_auto_approval":
        blocked.append("swing_sim_auto_approval_report_type_invalid")
    elif not bool(payload.get("approved")):
        blocked.append("swing_sim_auto_approval_not_approved")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    elif payload.get("runtime_effect") is not False:
        blocked.append("runtime_effect_not_allowed")
    elif payload.get("allowed_runtime_apply") is not False:
        blocked.append("artifact_allowed_runtime_apply_must_be_false")
    elif payload.get("broker_order_forbidden") is not True:
        blocked.append("broker_order_forbidden_contract_missing")
    if not catalog_path.exists():
        blocked.append("swing_sim_policy_catalog_missing")
    approved_request = None
    if not blocked:
        approved_source_ids = [str(item) for item in (payload.get("approved_source_ids") or [])]
        approved_request = {
            "family": "swing_sim_auto_approval",
            "policy_id": "swing_sim_auto_approval",
            "stage": "swing_sim_lifecycle",
            "priority": 88,
            "approval_id": f"swing_sim_auto_approval:{source_date}",
            "approval_state": "auto_sim",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "calibration_state": "sim_auto_approved",
            "target_env_keys": [
                "SWING_SIM_AUTO_POLICY_ENABLED",
                "SWING_SIM_AUTO_POLICY_FILE",
                "SWING_SIM_AUTO_POLICY_VERSION",
                "SWING_SIM_AUTO_BOTTOM_REBOUND_SOURCE_ENABLED",
            ],
            "recommended_values": {
                "enabled": True,
                "policy_file": str(catalog_path),
                "policy_version": f"swing_sim_auto_approval:{source_date}",
                "bottom_rebound_source_enabled": "bottom_rebound_policy_auto_loop" in set(approved_source_ids),
            },
            "current_values": {
                "enabled": False,
                "policy_file": "",
                "policy_version": "",
                "bottom_rebound_source_enabled": False,
            },
            "approved_source_ids": approved_source_ids,
            "approved_policy_count": int(payload.get("approved_policy_count") or 0),
            "actual_order_submitted": False,
            "decision_authority": "swing_sim_auto_approval_control_tower",
        }
    return {
        "artifact": str(artifact_path) if artifact_path.exists() else None,
        "catalog": str(catalog_path) if catalog_path.exists() else None,
        "approved_request": approved_request,
        "blocked": blocked,
        "approved_source_ids": payload.get("approved_source_ids") or [],
        "approved_policy_count": payload.get("approved_policy_count"),
    }


def _select_swing_sim_auto_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    item = bundle.get("approved_request")
    decisions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    if not isinstance(item, dict):
        decisions.append(
            {
                "family": "swing_sim_auto_approval",
                "selected": False,
                "decision_reason": ",".join(str(reason) for reason in bundle.get("blocked") or []) or "swing_sim_auto_approval_missing",
                "env_overrides": {},
                "actual_order_submitted": False,
            }
        )
        return selected, decisions, env_overrides
    overrides = _env_overrides_for_candidate(item)
    reject_reason = ""
    if not bool(item.get("allowed_runtime_apply")):
        reject_reason = "runtime_apply_not_allowed"
    elif bool(item.get("actual_order_submitted")):
        reject_reason = "actual_order_submitted_not_allowed"
    elif not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "approval_id": item.get("approval_id"),
        "family": item.get("family"),
        "stage": item.get("stage"),
        "approved_source_ids": item.get("approved_source_ids") or [],
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "swing_sim_auto_approval_apply",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
    }
    decisions.append(decision)
    if reject_reason:
        return selected, decisions, env_overrides
    selected.append(item)
    env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _ai_guard_allows_candidate(candidate: dict[str, Any], ai_review: dict[str, Any], *, require_ai: bool) -> tuple[bool, str]:
    if str(candidate.get("family") or "") == "latency_classifier_runtime_profile":
        return (True, "deterministic_latency_classifier_recommendation")
    items_by_family = ai_review.get("items_by_family") if isinstance(ai_review.get("items_by_family"), dict) else {}
    item = items_by_family.get(str(candidate.get("family") or ""))
    if not item:
        return (not require_ai, "ai_review_missing" if require_ai else "ai_review_missing_deterministic_allowed")
    guard_decision = item.get("guard_decision") if isinstance(item.get("guard_decision"), dict) else {}
    route_action = str(item.get("route_action") or guard_decision.get("route_action") or "")
    if (
        _score65_74_entry_unlock_candidate(candidate)
        and route_action == "exclude_from_threshold_candidate_review"
        and str(guard_decision.get("anomaly_route") or item.get("ai_anomaly_route") or "") == "instrumentation_gap"
    ):
        return (True, "entry_unlock_probe_ready_overrides_no_applied_probe_gap")
    if str(item.get("guard_decision") or "").lower() != "accept" and not bool(item.get("guard_accepted")):
        return (False, str(item.get("guard_reject_reason") or "ai_guard_rejected"))
    if route_action in AUTO_APPLY_ROUTE_EXCLUDE_ACTIONS:
        return (False, "ai_route_excluded_from_threshold_candidate")
    route = str(item.get("ai_anomaly_route") or "")
    if route not in AUTO_APPLY_ALLOWED_ROUTES:
        return (False, f"ai_route_not_runtime_apply:{route}")
    return (True, "ai_guard_accepted")


def _select_auto_apply_candidates(
    calibration_candidates: list[dict[str, Any]],
    *,
    ai_review: dict[str, Any],
    require_ai: bool,
    include_families: set[str] | None = None,
    operator_locks: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected_by_stage: dict[str, dict[str, Any]] = {}
    decisions: list[dict[str, Any]] = []
    locks_by_family = {
        str(lock.get("family") or ""): lock
        for lock in (operator_locks or [])
        if isinstance(lock, dict) and lock.get("family")
    }
    candidates = list(calibration_candidates)
    present_families = {str(item.get("family") or "") for item in candidates if isinstance(item, dict)}
    for family, lock in locks_by_family.items():
        if family not in present_families:
            candidates.append(_locked_synthetic_candidate(lock))
    for candidate in sorted(candidates, key=lambda item: int(item.get("priority") or 999)):
        family = str(candidate.get("family") or "")
        stage = str(candidate.get("stage") or "unknown")
        state = str(candidate.get("calibration_state") or "")
        lock = locks_by_family.get(family)
        allowed, reason = _ai_guard_allows_candidate(candidate, ai_review, require_ai=require_ai)
        reject_reason = ""
        if include_families is not None and family not in include_families:
            reject_reason = "operator_family_filter_excluded"
        elif family in NON_LIVE_SELECTABLE_FAMILIES or str(candidate.get("family_type") or "") == "sim_lifecycle_source":
            reject_reason = "non_live_selectable_sim_lifecycle_source"
        elif not bool(candidate.get("allowed_runtime_apply")):
            reject_reason = "runtime_apply_not_allowed"
        elif bool(candidate.get("safety_revert_required")):
            reject_reason = "safety_revert_required"
        elif state in AUTO_APPLY_BLOCK_STATES or state not in AUTO_APPLY_ALLOWED_STATES:
            reject_reason = f"calibration_state_blocked:{state}"
        elif not allowed:
            reject_reason = reason
        elif not _env_overrides_for_candidate(candidate):
            reject_reason = "no_runtime_env_override"
        elif stage in selected_by_stage:
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage].get('family')}"

        lock_applied = False
        lock_close_reasons = _candidate_close_reasons(candidate, reject_reason)
        if lock and (include_families is None or family in include_families):
            lock_overrides = _lock_env_overrides(lock)
            lock_can_preserve = bool(lock_overrides) and not _lock_allows_close(lock, lock_close_reasons)
            if lock_can_preserve:
                reject_reason = ""
                reason = f"operator_runtime_env_lock_preserved:{lock.get('lock_id') or family}"
                lock_applied = True
            elif bool(lock_overrides):
                reason = f"operator_runtime_env_lock_allowed_close:{lock.get('lock_id') or family}"

        decision = {
            "family": family,
            "stage": stage,
            "priority": int(candidate.get("priority") or 999),
            "calibration_state": state,
            "threshold_version": candidate.get("threshold_version"),
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason or reason,
            "env_overrides": (
                _lock_env_overrides(lock)
                if lock_applied and lock
                else _env_overrides_for_candidate(candidate)
                if not reject_reason
                else {}
            ),
        }
        if lock:
            decision["operator_runtime_env_lock"] = {
                "lock_id": lock.get("lock_id"),
                "path": lock.get("path"),
                "applied": bool(lock_applied),
                "close_reasons": lock_close_reasons,
                "allowed_close": _lock_allows_close(lock, lock_close_reasons),
            }
        if reject_reason:
            decisions.append(decision)
            continue
        selected_by_stage[stage] = candidate
        decisions.append(decision)

    selected_decisions = [decision for decision in decisions if bool(decision.get("selected"))]
    env_overrides: dict[str, str] = {}
    for decision in selected_decisions:
        env_overrides.update(decision.get("env_overrides") or {})
    return selected_decisions, decisions, env_overrides


def _lifecycle_ai_context_overlay_env(
    calibration_candidates: list[dict[str, Any]],
    *,
    include_families: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    if include_families is not None and "lifecycle_decision_matrix_runtime" not in include_families:
        return (
            {
                "selected": False,
                "decision_reason": "operator_family_filter_excluded",
                "env_overrides": {},
            },
            {},
        )
    candidate = next(
        (
            item
            for item in calibration_candidates
            if isinstance(item, dict) and str(item.get("family") or "") == "lifecycle_decision_matrix_runtime"
        ),
        None,
    )
    if not candidate:
        return (
            {
                "selected": False,
                "decision_reason": "lifecycle_decision_matrix_runtime_candidate_missing",
                "env_overrides": {},
            },
            {},
        )
    recommended = candidate.get("recommended_values") if isinstance(candidate.get("recommended_values"), dict) else {}
    context_file = str(recommended.get("lifecycle_ai_context_file") or "")
    if not bool(recommended.get("lifecycle_ai_context_enabled")) or not context_file:
        return (
            {
                "selected": False,
                "decision_reason": "lifecycle_ai_context_artifact_missing_or_disabled",
                "env_overrides": {},
            },
            {},
        )

    overlay_values = {
        "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED": False,
        "LIFECYCLE_AI_CONTEXT_ENABLED": True,
        "LIFECYCLE_AI_CONTEXT_FILE": context_file,
        "LIFECYCLE_AI_CONTEXT_VERSION": str(recommended.get("lifecycle_ai_context_version") or ""),
        "SCALP_ENTRY_ADM_ADVISORY_ENABLED": bool(recommended.get("entry_adm_advisory_enabled", True)),
        "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED": False,
        "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED": bool(
            recommended.get("holding_exit_matrix_advisory_enabled", True)
        ),
        "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED": False,
        "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED": False,
    }
    env_overrides = {
        _runtime_env_name(key): _format_env_value(value)
        for key, value in overlay_values.items()
        if key in TARGET_ENV_VALUE_KEYS
    }
    decision = {
        "family": "lifecycle_ai_context",
        "source_family": "lifecycle_decision_matrix_runtime",
        "family_type": "context_only_env_overlay",
        "selected": True,
        "decision_reason": "context_only_advisory_prompt_overlay_bias_off",
        "runtime_effect": False,
        "decision_authority": "ai_advisory_prompt_context_only",
        "live_selectable": False,
        "standalone_threshold_family": False,
        "env_overrides": env_overrides,
    }
    return decision, env_overrides


def _write_runtime_env(target_date: str, manifest: dict[str, Any], env_overrides: dict[str, str]) -> None:
    RUNTIME_ENV_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated by threshold_cycle_preopen_apply.py",
        f"# target_date={target_date}",
        f"# source_date={manifest.get('source_date')}",
        f"# generated_at={manifest.get('generated_at')}",
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true",
        f"export KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE={shlex.quote(target_date)}",
    ]
    for key in sorted(env_overrides):
        lines.append(f"export {key}={shlex.quote(str(env_overrides[key]))}")
    runtime_env_path(target_date).write_text("\n".join(lines) + "\n", encoding="utf-8")
    runtime_env_manifest_path(target_date).write_text(
        json.dumps(
            {
                "target_date": target_date,
                "source_date": manifest.get("source_date"),
                "source_report": manifest.get("source_report"),
                "generated_at": manifest.get("generated_at"),
                "env_file": str(runtime_env_path(target_date)),
                "env_overrides": env_overrides,
                "selected_families": [
                    item.get("family")
                    for item in [
                        *(manifest.get("auto_apply_selected") or []),
                        *((manifest.get("swing_runtime_approval") or {}).get("selected") or []),
                        *((manifest.get("scalp_sim_scale_in_window_approval") or {}).get("selected") or []),
                        *((manifest.get("runtime_apply_bridge") or {}).get("selected") or []),
                        *((manifest.get("lifecycle_bucket_discovery") or {}).get("selected") or []),
                    ]
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def build_preopen_apply_manifest(
    target_date: str,
    *,
    source_date: str | None = None,
    apply_mode: str = "manifest_only",
    auto_apply: bool = False,
    require_ai: bool = True,
    source_phase: str | None = None,
    include_families: set[str] | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_path = _report_path_for_date(source_date, source_phase=source_phase) if source_date else _latest_report_before(target_date)
    if source_path is None or not source_path.exists():
        manifest = {
            "target_date": target_date,
            "status": "missing_source_report",
            "apply_mode": apply_mode,
            "runtime_change": False,
            "source_report": None,
            "candidates": [],
            "calibration_candidates": [],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
    else:
        report = _load_json(source_path)
        candidates = report.get("apply_candidate_list") if isinstance(report.get("apply_candidate_list"), list) else []
        calibration_candidates = (
            report.get("calibration_candidates") if isinstance(report.get("calibration_candidates"), list) else []
        )
        report_source_date = str(report.get("date") or source_date or "")
        latency_candidates, latency_recommendation = _load_latency_classifier_candidates(report_source_date)
        if latency_candidates:
            calibration_candidates = [*calibration_candidates, *latency_candidates]
        approval_requests = []
        for item in calibration_candidates:
            if (
                isinstance(item, dict)
                and bool(item.get("human_approval_required"))
                and str(item.get("calibration_state") or "") == "approval_required"
            ):
                approval_requests.append(
                    annotate_approval_request(
                        {
                            "family": item.get("family"),
                            "stage": item.get("stage"),
                            "threshold_version": item.get("threshold_version"),
                            "calibration_state": item.get("calibration_state"),
                            "calibration_reason": item.get("calibration_reason"),
                            "current_values": item.get("current_values"),
                            "recommended_values": item.get("recommended_values"),
                            "sample_count": item.get("sample_count"),
                            "sample_floor": item.get("sample_floor"),
                            "source_reports": item.get("source_reports"),
                        },
                        str(report.get("date") or source_date or ""),
                    )
                )
        approval_contract_gaps = [
            item
            for item in approval_requests
            if isinstance(item, dict) and not bool(item.get("approval_live_ready"))
        ]
        auto_apply_requested = bool(auto_apply) or apply_mode in AUTO_APPLY_MODES
        ai_review = _load_ai_review(report_source_date, source_phase=source_phase)
        intraday_source_auto_apply_blocked = bool(auto_apply_requested and source_phase == "intraday")
        operator_runtime_env_locks = _load_operator_runtime_env_locks(
            report_source_date,
            target_date,
        )
        selected, decisions, env_overrides = ([], [], {})
        lifecycle_context_overlay, lifecycle_context_env_overrides = ({}, {})
        swing_bundle = _load_swing_runtime_approval_bundle(report_source_date)
        swing_selected, swing_decisions, swing_env_overrides = ([], [], {})
        scalp_scale_bundle = _load_scalp_sim_scale_in_window_approval(report_source_date)
        scalp_scale_selected, scalp_scale_decisions, scalp_scale_env_overrides = ([], [], {})
        runtime_bridge_bundle = _load_runtime_apply_bridge_approval(report_source_date)
        runtime_bridge_selected, runtime_bridge_decisions, runtime_bridge_env_overrides = ([], [], {})
        lifecycle_bucket_bundle = _load_lifecycle_bucket_sim_auto_approval(report_source_date)
        lifecycle_bucket_selected, lifecycle_bucket_decisions, lifecycle_bucket_env_overrides = ([], [], {})
        swing_sim_auto_bundle = _load_swing_sim_auto_approval(report_source_date)
        swing_sim_auto_selected, swing_sim_auto_decisions, swing_sim_auto_env_overrides = ([], [], {})
        if auto_apply_requested and not intraday_source_auto_apply_blocked:
            selected, decisions, env_overrides = _select_auto_apply_candidates(
                calibration_candidates,
                ai_review=ai_review,
                require_ai=require_ai,
                include_families=include_families,
                operator_locks=operator_runtime_env_locks,
            )
            swing_selected, swing_decisions, swing_env_overrides = _select_swing_approved_candidates(swing_bundle)
            scalp_scale_selected, scalp_scale_decisions, scalp_scale_env_overrides = (
                _select_scalp_sim_scale_in_window_approval(scalp_scale_bundle)
            )
            runtime_bridge_selected, runtime_bridge_decisions, runtime_bridge_env_overrides = (
                _select_runtime_apply_bridge_approval(
                    runtime_bridge_bundle,
                    include_families=include_families,
                )
            )
            lifecycle_bucket_selected, lifecycle_bucket_decisions, lifecycle_bucket_env_overrides = (
                _select_lifecycle_bucket_sim_auto_approval(lifecycle_bucket_bundle)
            )
            swing_sim_auto_selected, swing_sim_auto_decisions, swing_sim_auto_env_overrides = (
                _select_swing_sim_auto_approval(swing_sim_auto_bundle)
            )
            lifecycle_context_overlay, lifecycle_context_env_overrides = _lifecycle_ai_context_overlay_env(
                calibration_candidates,
                include_families=include_families,
            )
            env_overrides = {
                **env_overrides,
                **lifecycle_context_env_overrides,
                **swing_env_overrides,
                **scalp_scale_env_overrides,
                **runtime_bridge_env_overrides,
                **lifecycle_bucket_env_overrides,
                **swing_sim_auto_env_overrides,
            }
        runtime_change = bool(auto_apply_requested and env_overrides)
        status = (
            "auto_bounded_live_ready"
            if runtime_change
            else "auto_bounded_live_blocked"
            if auto_apply_requested
            else "efficient_tradeoff_manifest_ready"
            if apply_mode == "efficient_tradeoff_canary_candidate"
            else "calibrated_manifest_ready"
            if apply_mode == "calibrated_apply_candidate"
            else "manifest_ready"
        )
        manifest = {
            "target_date": target_date,
            "source_date": report.get("date"),
            "source_report": str(source_path),
            "status": status,
            "apply_mode": apply_mode,
            "runtime_change": runtime_change,
            "runtime_change_reason": (
                "intraday source phase는 manual forensic/legacy manifest-only이며 runtime env apply 금지"
                if intraday_source_auto_apply_blocked
                else
                "장전 자동 bounded env apply; 장중 threshold mutation은 계속 금지"
                if runtime_change
                else "장전 자동 bounded env apply 후보 없음; 장중 threshold mutation은 계속 금지"
                if auto_apply_requested
                else "장중 자동 mutation 금지; calibrated/efficient trade-off 후보도 승인된 family의 다음 장전 bounded apply 후보만 생성"
            ),
            "candidates": candidates,
            "calibration_candidates": calibration_candidates,
            "source_phase": source_phase or "canonical",
            "source_phase_auto_apply_blocked": intraday_source_auto_apply_blocked,
            "ai_correction_review": {
                "required": bool(require_ai),
                "status": ai_review.get("status"),
                "path": ai_review.get("path"),
                "phase": ai_review.get("phase"),
                "model": ai_review.get("model"),
                "provider_status": ai_review.get("provider_status") or {},
            },
            "latency_classifier_recommendation": latency_recommendation,
            "auto_apply_selected": selected,
            "auto_apply_decisions": decisions,
            "lifecycle_ai_context_overlay": lifecycle_context_overlay,
            "operator_runtime_env_locks": operator_runtime_env_locks,
            "approval_requests": approval_requests,
            "approval_contract_gaps": approval_contract_gaps,
            "swing_runtime_approval": {
                "request_report": swing_bundle.get("request_report"),
                "approval_artifact": swing_bundle.get("approval_artifact"),
                "one_share_real_canary_approval_artifact": swing_bundle.get("one_share_real_canary_approval_artifact"),
                "scale_in_real_canary_approval_artifact": swing_bundle.get("scale_in_real_canary_approval_artifact"),
                "requested": len(swing_bundle.get("requests") or []),
                "approved": len(swing_bundle.get("approved_requests") or []),
                "blocked": swing_bundle.get("blocked") or [],
                "requests": swing_bundle.get("requests") or [],
                "approved_requests": swing_bundle.get("approved_requests") or [],
                "real_canary_policy": swing_bundle.get("real_canary_policy") or {},
                "scale_in_real_canary_policy": swing_bundle.get("scale_in_real_canary_policy") or {},
                "selected": swing_selected,
                "decisions": swing_decisions,
                "dry_run_forced": bool(swing_env_overrides),
            },
            "scalp_sim_scale_in_window_approval": {
                "artifact": scalp_scale_bundle.get("artifact"),
                "approved": 1 if scalp_scale_bundle.get("approved_request") else 0,
                "blocked": scalp_scale_bundle.get("blocked") or [],
                "approved_request": scalp_scale_bundle.get("approved_request"),
                "selected": scalp_scale_selected,
                "decisions": scalp_scale_decisions,
            },
            "runtime_apply_bridge": {
                "request_report": runtime_bridge_bundle.get("request_report"),
                "artifacts": runtime_bridge_bundle.get("artifacts") or {},
                "candidate_count": len(runtime_bridge_bundle.get("candidates") or []),
                "approved": len(runtime_bridge_bundle.get("approved_requests") or []),
                "blocked": runtime_bridge_bundle.get("blocked") or [],
                "approved_requests": runtime_bridge_bundle.get("approved_requests") or [],
                "selected": runtime_bridge_selected,
                "decisions": runtime_bridge_decisions,
            },
            "lifecycle_bucket_discovery": {
                "artifact": lifecycle_bucket_bundle.get("artifact"),
                "discovery_report": lifecycle_bucket_bundle.get("discovery_report"),
                "catalog": lifecycle_bucket_bundle.get("catalog"),
                "approved": 1 if lifecycle_bucket_bundle.get("approved_request") else 0,
                "blocked": lifecycle_bucket_bundle.get("blocked") or [],
                "approved_request": lifecycle_bucket_bundle.get("approved_request"),
                "selected": lifecycle_bucket_selected,
                "decisions": lifecycle_bucket_decisions,
            },
            "swing_sim_auto_approval": {
                "artifact": swing_sim_auto_bundle.get("artifact"),
                "catalog": swing_sim_auto_bundle.get("catalog"),
                "approved": 1 if swing_sim_auto_bundle.get("approved_request") else 0,
                "approved_policy_count": swing_sim_auto_bundle.get("approved_policy_count"),
                "approved_source_ids": swing_sim_auto_bundle.get("approved_source_ids") or [],
                "blocked": swing_sim_auto_bundle.get("blocked") or [],
                "approved_request": swing_sim_auto_bundle.get("approved_request"),
                "selected": swing_sim_auto_selected,
                "decisions": swing_sim_auto_decisions,
            },
            "runtime_env_file": (
                str(runtime_env_path(target_date))
                if auto_apply_requested and not intraday_source_auto_apply_blocked
                else None
            ),
            "runtime_env_overrides": env_overrides,
            "threshold_snapshot": report.get("threshold_snapshot") or {},
            "post_apply_attribution": report.get("post_apply_attribution") or {},
            "safety_guard_pack": report.get("safety_guard_pack") or [],
            "calibration_trigger_pack": report.get("calibration_trigger_pack") or [],
            "rollback_guard_pack": report.get("rollback_guard_pack") or [],
            "calibration_policy": {
                "condition_miss_action": "calibration_trigger",
                "sample_shortfall_action": "cap_reduce_or_hold_sample_or_max_step_shrink",
                "rollback_policy": "safety_breach_only",
                "intraday_runtime_mutation": False,
                "apply_frequency": "next_preopen_once",
                "human_approval_required": bool(approval_requests),
                "ai_correction_required": bool(require_ai),
                "same_stage_owner_rule": "one_selected_family_per_stage_by_priority",
                "daily_ev_report_only": True,
                "operator_family_filter": sorted(include_families) if include_families is not None else None,
                "intraday_source_auto_apply": False,
            },
            "warnings": ["intraday_source_phase_auto_apply_blocked"] if intraday_source_auto_apply_blocked else [],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        if auto_apply_requested and not intraday_source_auto_apply_blocked:
            _write_runtime_env(target_date, manifest, env_overrides)
    APPLY_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    apply_manifest_path(target_date).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build preopen threshold apply manifest.")
    parser.add_argument(
        "--date",
        "--target-date",
        dest="target_date",
        default=date.today().isoformat(),
        help="Target preopen date",
    )
    parser.add_argument("--source-date", dest="source_date", default=None, help="Postclose report date to apply")
    parser.add_argument(
        "--source-phase",
        choices=["canonical", "intraday", "postclose"],
        default="canonical",
        help="When --source-date is given, choose canonical threshold report or a phase calibration artifact.",
    )
    parser.add_argument(
        "--include-family",
        action="append",
        default=[],
        help="Limit auto-apply selection to the given family. May be repeated for stage-disjoint explicit applies.",
    )
    parser.add_argument(
        "--apply-mode",
        default=os.getenv("THRESHOLD_CYCLE_APPLY_MODE", "manifest_only"),
        choices=[
            "manifest_only",
            "calibrated_apply_candidate",
            "efficient_tradeoff_canary_candidate",
            "auto_bounded_live",
        ],
        help="Apply mode. auto_bounded_live writes next-preopen runtime env under deterministic/AI guards.",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        default=str(os.getenv("THRESHOLD_CYCLE_AUTO_APPLY", "")).lower() in {"1", "true", "yes", "on"},
        help="Write guarded runtime env overrides for selected candidates.",
    )
    parser.add_argument(
        "--allow-deterministic-without-ai",
        action="store_true",
        default=str(os.getenv("THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI", "true")).lower() in {"0", "false", "no", "off"},
        help="Allow deterministic guards to apply when AI correction review is missing/unavailable.",
    )
    args = parser.parse_args(argv)
    manifest = build_preopen_apply_manifest(
        args.target_date,
        source_date=args.source_date,
        apply_mode=args.apply_mode,
        auto_apply=args.auto_apply,
        require_ai=not args.allow_deterministic_without_ai,
        source_phase=None if args.source_phase == "canonical" else args.source_phase,
        include_families=set(args.include_family) if args.include_family else None,
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return (
        0
        if manifest.get("status")
        in {
            "manifest_ready",
            "calibrated_manifest_ready",
            "efficient_tradeoff_manifest_ready",
            "auto_bounded_live_ready",
            "auto_bounded_live_blocked",
        }
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
