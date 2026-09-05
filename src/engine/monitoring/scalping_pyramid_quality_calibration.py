from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_hard_gate import (
    filter_source_dates_by_preflight,
    load_source_quality_preflight,
)
from src.engine.sniper_scale_in import _pyramid_quality_decision
from src.engine.trade_profit import calculate_net_profit_rate, get_trade_cost_rate
from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))
FAMILY = "scalping_pyramid_quality_gate"
STAGE = "scale_in"
REPORT_TYPE = "scalping_pyramid_quality_calibration"
INPUT_REPORT_DIR = DATA_DIR / "report" / "scalping_pyramid_intraday_feedback"
OUTPUT_REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
RUNTIME_ENV_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
CLEAN_BASELINE_DATE = "2026-06-05"
EVIDENCE_CONTRACT_VERSION = "pyramid_fixed_exit_replay_v1"
REPLAY_SOURCE_CONTRACT_VERSION = "pyramid_gate_replay_source_v1"
REPLAY_SOURCE_SCHEMA_VERSION = 5
REPLAY_EVENT_SCHEMA = "pyramid_gate_observation_v2"
REPLAY_PRICE_EVIDENCE = "fresh_quote_existing_resolver_limit_price"
CUMULATIVE_LEARNING_SAMPLE_FLOOR = 1
POST_PROBE_RUNTIME_PROMOTION_SAMPLE_FLOOR = 20
WINNER_RECOVERY_COUNTERFACTUAL_SAMPLE_FLOOR = 10
WINNER_RECOVERY_REAL_PROMOTION_SAMPLE_FLOOR = 20
WINNER_RECOVERY_EXACT_BLOCKER = (
    "rising_missed_scout_pyramid_bridge_blocked:profit_not_enough"
)
WINNER_RECOVERY_RUNTIME_ENV_KEYS = {
    "enabled": "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED",
    "active_date": "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ACTIVE_DATE",
    "KRX": "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_KRX_ENABLED",
    "NXT": "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_NXT_ENABLED",
    "PREMARKET_KRX_LIKE": (
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_PREMARKET_ENABLED"
    ),
}
CLOSED_LABELS = {
    "pyramid_would_have_helped",
    "pyramid_correctly_blocked",
    "pyramid_overheat_or_reversal_risk",
}
NORMAL_WINNER_EXPANSION_CLOSED_LABELS = {
    "realized_incremental_winner",
    "transient_extension_exit_timing_needed",
    "correctly_not_expanded_or_reversal",
}
POST_PROBE_REAL_OUTCOME_CLOSED_LABELS = {
    "profitable_zero_fill_confirmation_ready",
    "profitable_zero_fill_no_confirmation",
    "loss_or_flat_zero_fill_confirmation_ready",
    "loss_or_flat_zero_fill_no_confirmation",
}
FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "intraday_runtime_apply",
    "hard_safety_relaxation",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "quantity_guard_relaxation",
    "position_cap_release",
    "provider_route_change",
    "bot_restart",
    "real_execution_quality_approval",
]
TARGET_ENV_KEYS = [
    "SCALPING_PYRAMID_MIN_PROFIT_PCT",
]
TARGET_VALUE_FIELDS = {
    "SCALPING_PYRAMID_MIN_PROFIT_PCT": "min_profit_pct",
    "SCALPING_PYRAMID_MIN_AI_SCORE": "min_ai_score",
    "SCALPING_PYRAMID_MIN_BUY_PRESSURE": "min_buy_pressure",
    "SCALPING_PYRAMID_MIN_TICK_ACCEL": "min_tick_accel",
    "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS": "max_micro_vwap_bps",
    "SCALPING_PYRAMID_MAX_SPREAD_BPS": "max_spread_bps",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED": ("strong_continuation_enabled"),
    "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT": (
        "strong_continuation_min_profit_pct"
    ),
    "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT": (
        "strong_continuation_max_drawdown_pct"
    ),
}
BOOLEAN_VALUE_FIELDS = {"strong_continuation_enabled"}
PROFIT_GRID_MIN = 0.2
PROFIT_GRID_MAX = 2.5
PROFIT_GRID_STEP = 0.1
PROFIT_GRID_MIN_ELIGIBLE = 20
PROFIT_GRID_RUNTIME_STEP = 0.1
RUNTIME_UPDATE_MODE = "single_cumulative_quality_update"
ROW_ISOLATABLE_SOURCE_QUALITY_STATUSES = {
    "pass",
    "pass_with_row_exclusions",
    # Legacy schema-v4 reports emitted this status before the producer moved
    # the same complete per-row receipt rejection to pass_with_row_exclusions.
    "real_scale_in_receipt_source_quality_incomplete",
    "micro_vwap_provenance_missing",
    "micro_vwap_provenance_unusable",
    "pressure_provenance_missing",
    "pressure_provenance_unusable",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "-"):
        return default
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    return (
        OUTPUT_REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json",
        OUTPUT_REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md",
    )


def _feedback_report_path(target_date: str) -> Path:
    return INPUT_REPORT_DIR / f"scalping_pyramid_intraday_feedback_{target_date}.json"


def _date_from_feedback_path(path: Path) -> str | None:
    prefix = "scalping_pyramid_intraday_feedback_"
    if path.stem.startswith(prefix):
        return path.stem.removeprefix(prefix)
    return None


def _iter_feedback_report_paths(target_date: str) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(
        INPUT_REPORT_DIR.glob("scalping_pyramid_intraday_feedback_*.json")
    ):
        date_part = path.stem.removeprefix("scalping_pyramid_intraday_feedback_")
        if CLEAN_BASELINE_DATE <= date_part <= target_date:
            paths.append(path)
    explicit = _feedback_report_path(target_date)
    if explicit.exists() and explicit not in paths:
        paths.append(explicit)
    return paths


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _current_values() -> dict[str, Any]:
    return {
        "min_profit_pct": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_PROFIT_PCT", 1.5) or 1.5
        ),
        "min_ai_score": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_AI_SCORE", 70) or 70
        ),
        "min_buy_pressure": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_BUY_PRESSURE", 60.0) or 60.0
        ),
        "min_tick_accel": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_TICK_ACCEL", 0.5) or 0.5
        ),
        "max_micro_vwap_bps": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS", 60.0) or 60.0
        ),
        "max_spread_bps": float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_SPREAD_BPS", 80.0) or 80.0
        ),
        "strong_continuation_enabled": bool(
            getattr(
                TRADING_RULES, "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED", False
            )
        ),
        "strong_continuation_min_profit_pct": float(
            getattr(
                TRADING_RULES,
                "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT",
                0.9,
            )
            or 0.9
        ),
        "strong_continuation_max_drawdown_pct": float(
            getattr(
                TRADING_RULES,
                "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT",
                0.2,
            )
            or 0.2
        ),
    }


def _runtime_env_manifest_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.json"


def _runtime_env_verify_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_verify_{target_date}.json"


def _parse_runtime_value(field_name: str, value: Any) -> Any | None:
    if field_name in BOOLEAN_VALUE_FIELDS:
        if isinstance(value, bool):
            return value
        token = str(value or "").strip().lower()
        if token not in {"1", "0", "true", "false", "yes", "no", "on", "off"}:
            return None
        return token in {"1", "true", "yes", "on"}
    if value in (None, "", "-"):
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or (field_name == "min_profit_pct" and parsed <= 0):
        return None
    return parsed


def _verified_runtime_env_values(target_date: str) -> dict[str, Any]:
    manifest_path = _runtime_env_manifest_path(target_date)
    verify_path = _runtime_env_verify_path(target_date)
    manifest = _load_json(manifest_path)
    verify = _load_json(verify_path)
    reasons: list[str] = []
    if not manifest:
        reasons.append("runtime_env_manifest_missing_or_invalid")
    if not verify:
        reasons.append("runtime_env_verify_missing_or_invalid")
    if manifest and str(manifest.get("target_date") or "") != target_date:
        reasons.append("runtime_env_manifest_target_date_mismatch")
    if verify and str(verify.get("target_date") or "") != target_date:
        reasons.append("runtime_env_verify_target_date_mismatch")
    if verify and not (
        verify.get("passed") is True
        and verify.get("pid_passed") is True
        and str(verify.get("status") or "").lower() == "pass"
    ):
        reasons.append("runtime_env_pid_verification_not_pass")
    overrides = manifest.get("env_overrides") if isinstance(manifest, dict) else None
    if manifest and not isinstance(overrides, dict):
        reasons.append("runtime_env_overrides_missing_or_invalid")
    manifest_reference = str(verify.get("manifest_path") or "").strip()
    if manifest_reference:
        try:
            if Path(manifest_reference).resolve() != manifest_path.resolve():
                reasons.append("runtime_env_verify_manifest_path_mismatch")
        except OSError:
            reasons.append("runtime_env_verify_manifest_path_invalid")
    values: dict[str, Any] = {}
    invalid_keys: list[str] = []
    if not reasons and isinstance(overrides, dict):
        for env_key, field_name in TARGET_VALUE_FIELDS.items():
            runtime_key = f"KORSTOCKSCAN_{env_key}"
            if runtime_key not in overrides:
                continue
            parsed = _parse_runtime_value(field_name, overrides.get(runtime_key))
            if parsed is None:
                invalid_keys.append(runtime_key)
            else:
                values[field_name] = parsed
    if invalid_keys:
        reasons.append("runtime_env_target_value_invalid")
        values = {}
    return {
        "valid": not reasons,
        "values": values,
        "reasons": reasons,
        "invalid_keys": sorted(invalid_keys),
        "manifest_path": str(manifest_path),
        "verify_path": str(verify_path),
    }


def _observed_min_profit_values(
    target_date: str, reports: list[dict[str, Any]]
) -> dict[str, Any]:
    values: set[float] = set()
    reasons: list[str] = []
    report_count = 0
    selection_sources: set[str] = set()
    for report in reports:
        if str(report.get("target_date") or "") != target_date:
            continue
        report_count += 1
        provenance = report.get("pyramid_threshold_provenance")
        if not isinstance(provenance, dict):
            continue
        if provenance.get("ambiguous") is True:
            reasons.append("same_day_feedback_threshold_ambiguous")
        configured_contract_valid = (
            provenance.get("configured_threshold_contract_valid") is True
        )
        source = str(provenance.get("selection_source") or "").strip()
        if source:
            selection_sources.add(source)
        observed_values = provenance.get("configured_v2_min_profit_pct_values")
        if isinstance(observed_values, list):
            for value in observed_values:
                parsed = _parse_runtime_value("min_profit_pct", value)
                if parsed is not None:
                    values.add(round(float(parsed), 6))
                else:
                    reasons.append("same_day_feedback_observed_threshold_invalid")
        selected = _parse_runtime_value(
            "min_profit_pct", provenance.get("selected_min_profit_pct")
        )
        if (
            configured_contract_valid
            and selected is not None
            and source == "same_day_unique_runtime_pyramid_evaluation"
        ):
            values.add(round(float(selected), 6))
    if len(values) > 1:
        reasons.append("same_day_feedback_threshold_conflict")
    return {
        "valid": len(values) == 1 and not reasons,
        "value": next(iter(values)) if len(values) == 1 else None,
        "values": sorted(values),
        "reasons": sorted(set(reasons)),
        "report_count": report_count,
        "selection_sources": sorted(selection_sources),
    }


def _resolve_current_values(
    target_date: str, reports: list[dict[str, Any]]
) -> dict[str, Any]:
    current = _current_values()
    field_sources = {key: "code_default" for key in current}
    runtime_env = _verified_runtime_env_values(target_date)
    if runtime_env["valid"]:
        for field_name, value in runtime_env["values"].items():
            current[field_name] = value
            field_sources[field_name] = "verified_runtime_env_pid"

    observed = _observed_min_profit_values(target_date, reports)
    blockers = list(observed["reasons"])
    observed_value = observed.get("value")
    runtime_value = runtime_env["values"].get("min_profit_pct")
    if (
        observed["valid"]
        and runtime_value is not None
        and not math.isclose(float(observed_value), float(runtime_value), abs_tol=1e-9)
    ):
        blockers.append("feedback_runtime_env_min_profit_conflict")
    if observed["valid"] and not blockers:
        current["min_profit_pct"] = float(observed_value)
        field_sources["min_profit_pct"] = "same_day_runtime_feedback_observation"
    elif runtime_value is not None and not blockers:
        current["min_profit_pct"] = float(runtime_value)
        field_sources["min_profit_pct"] = "verified_runtime_env_pid"
    if observed_value is None and runtime_value is None:
        blockers.append("current_min_profit_runtime_provenance_missing")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": sorted(set(blockers)),
        "values": current,
        "field_sources": field_sources,
        "observed_feedback": observed,
        "verified_runtime_env": runtime_env,
        "selected_min_profit_pct": current["min_profit_pct"],
    }


def _calibration_row_source_quality_reason(row: dict[str, Any]) -> str:
    if row.get("buy_pressure_10t") is not None and not (
        row.get("tick_aggressor_pressure_usable") is True
        or _safe_float(row.get("tick_aggressor_trusted_count"), 0.0) > 0.0
    ):
        return "pressure_provenance_invalid"
    if row.get("curr_vs_micro_vwap_bp") is not None and not (
        row.get("micro_vwap_available") is True
        and row.get("minute_candle_window_fresh") is True
    ):
        return "micro_vwap_provenance_invalid"
    if row.get("probe_residual_observation_seen") and (
        row.get("residual_fill_attribution_valid") is not True
        or row.get("venue_source_quality_valid") is not True
    ):
        return "probe_residual_or_venue_provenance_invalid"
    return ""


def _closed_pyramid_rows(
    reports: list[dict[str, Any]],
    exclusion_counts: Counter[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        for row in report.get("pyramid_feedback_rows") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("pyramid_feedback_label") or "") not in CLOSED_LABELS:
                continue
            exclusion_reason = _calibration_row_source_quality_reason(row)
            if exclusion_reason:
                if exclusion_counts is not None:
                    exclusion_counts[exclusion_reason] += 1
                continue
            rows.append(row)
    return rows


def _closed_one_share_pyramid_rows(
    reports: list[dict[str, Any]],
    exclusion_counts: Counter[str] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    section_present = False
    for report in reports:
        source_rows = report.get("one_share_pyramid_opportunity_rows")
        if not isinstance(source_rows, list):
            continue
        section_present = True
        for row in source_rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("pyramid_feedback_label") or "") not in CLOSED_LABELS:
                continue
            exclusion_reason = _calibration_row_source_quality_reason(row)
            if exclusion_reason:
                if exclusion_counts is not None:
                    exclusion_counts[exclusion_reason] += 1
                continue
            rows.append(row)
    return rows, section_present


def _count_real_scale_in_row_exclusions(
    reports: list[dict[str, Any]],
    exclusion_counts: Counter[str],
) -> None:
    """Account for isolated closed receipt defects without blocking the day."""

    for report in reports:
        source_rows = report.get("real_scale_in_performance_rows")
        if not isinstance(source_rows, list):
            continue
        for row in source_rows:
            if not isinstance(row, dict) or not _boolish(row.get("closed")):
                continue
            if _boolish(row.get("source_quality_valid")):
                continue
            exclusion_counts["real_scale_in_receipt_source_quality_incomplete"] += 1


def _normal_winner_expansion_observation(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    def _candidate_notional(row: dict[str, Any]) -> int:
        value = _safe_float(
            row.get("normal_winner_expansion_candidate_notional_krw"),
            0.0,
        )
        if not math.isfinite(value) or value <= 0.0:
            return 0
        return int(value)

    rows: list[dict[str, Any]] = []
    section_present = False
    provenance_rejected_count = 0
    for report in reports:
        source_rows = report.get("normal_winner_expansion_rows")
        if not isinstance(source_rows, list):
            continue
        section_present = True
        for row in source_rows:
            if not isinstance(row, dict):
                continue
            if (
                str(row.get("normal_winner_expansion_label") or "")
                not in NORMAL_WINNER_EXPANSION_CLOSED_LABELS
            ):
                continue
            if not _boolish(row.get("normal_winner_expansion_source_quality_valid")):
                continue
            provenance_valid = bool(
                row.get("runtime_effect") is False
                and row.get("allowed_runtime_apply") is False
                and row.get("actual_order_submitted") is False
                and row.get("broker_order_forbidden") is True
                and str(row.get("decision_authority") or "").startswith("source_only_")
                and isinstance(row.get("forbidden_uses"), list)
            )
            if not provenance_valid:
                provenance_rejected_count += 1
                continue
            rows.append(row)
    weighted = [
        (
            _safe_float(
                row.get("normal_winner_expansion_incremental_final_profit_pct"),
                0.0,
            ),
            _candidate_notional(row),
        )
        for row in rows
        if _candidate_notional(row) > 0
    ]
    winner_count = sum(
        1
        for row in rows
        if row.get("normal_winner_expansion_label") == "realized_incremental_winner"
    )
    ev_eligible_sample_count = len(weighted)
    sample_floor_met = ev_eligible_sample_count >= 20
    notional_weighted_ev_pct = (
        round(
            sum(value * notional for value, notional in weighted)
            / sum(notional for _, notional in weighted),
            4,
        )
        if weighted
        else 0.0
    )
    if not section_present:
        state = "not_available"
    elif not sample_floor_met:
        state = "hold_sample"
    elif notional_weighted_ev_pct > 0:
        state = "positive_ev_profile_candidate"
    else:
        state = "non_positive_ev_hold"

    def _dimension_rollup(dimension: str) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if dimension == "effective_venue" and not _boolish(
                row.get("venue_source_quality_valid")
            ):
                continue
            value = str(row.get(dimension) or "UNKNOWN").strip() or "UNKNOWN"
            grouped[value].append(row)
        result = []
        for value, bucket_rows in sorted(grouped.items()):
            bucket_weighted = [
                (
                    _safe_float(
                        row.get("normal_winner_expansion_incremental_final_profit_pct"),
                        0.0,
                    ),
                    _candidate_notional(row),
                )
                for row in bucket_rows
                if _candidate_notional(row) > 0
            ]
            result.append(
                {
                    dimension: value,
                    "sample_count": len(bucket_rows),
                    "ev_eligible_sample_count": len(bucket_weighted),
                    "sample_floor": 20,
                    "sample_floor_met": len(bucket_weighted) >= 20,
                    "notional_weighted_ev_pct": (
                        round(
                            sum(
                                outcome * notional
                                for outcome, notional in bucket_weighted
                            )
                            / sum(notional for _, notional in bucket_weighted),
                            4,
                        )
                        if bucket_weighted
                        else 0.0
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
        return result

    exact_blocker_rows = [
        row
        for row in rows
        if str(row.get("normal_winner_expansion_blocker_reason") or "")
        == WINNER_RECOVERY_EXACT_BLOCKER
        and _boolish(row.get("venue_source_quality_valid"))
        and str(row.get("effective_venue") or "")
        in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
    ]
    exact_by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in exact_blocker_rows:
        exact_by_venue[str(row.get("effective_venue"))].append(row)
    bounded_canary_by_venue = []
    for venue, venue_rows in sorted(exact_by_venue.items()):
        venue_weighted = [
            (
                _safe_float(
                    row.get("normal_winner_expansion_incremental_final_profit_pct"),
                    0.0,
                ),
                _candidate_notional(row),
            )
            for row in venue_rows
            if _candidate_notional(row) > 0
        ]
        venue_ev = (
            round(
                sum(outcome * notional for outcome, notional in venue_weighted)
                / sum(notional for _, notional in venue_weighted),
                4,
            )
            if venue_weighted
            else 0.0
        )
        venue_floor_met = (
            len(venue_weighted) >= WINNER_RECOVERY_COUNTERFACTUAL_SAMPLE_FLOOR
        )
        venue_state = (
            "hold_sample"
            if not venue_floor_met
            else (
                "bounded_one_share_canary_evidence_ready"
                if venue_ev > 0
                else "non_positive_ev_hold"
            )
        )
        bounded_canary_by_venue.append(
            {
                "effective_venue": venue,
                "state": venue_state,
                "sample_count": len(venue_rows),
                "ev_eligible_sample_count": len(venue_weighted),
                "sample_floor": WINNER_RECOVERY_COUNTERFACTUAL_SAMPLE_FLOOR,
                "sample_floor_met": venue_floor_met,
                "realized_incremental_winner_count": sum(
                    1
                    for row in venue_rows
                    if row.get("normal_winner_expansion_label")
                    == "realized_incremental_winner"
                ),
                "notional_weighted_ev_pct": venue_ev,
                "initial_real_qty_cap": 1,
                "runtime_env_key": WINNER_RECOVERY_RUNTIME_ENV_KEYS[venue],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    positive_ready = [
        item
        for item in bounded_canary_by_venue
        if item["state"] == "bounded_one_share_canary_evidence_ready"
    ]
    non_positive_ready = [
        item
        for item in bounded_canary_by_venue
        if item["state"] == "non_positive_ev_hold"
    ]
    bounded_canary_state = (
        "bounded_one_share_canary_evidence_ready"
        if positive_ready and not non_positive_ready
        else (
            "venue_conflict_requires_independent_decision"
            if positive_ready and non_positive_ready
            else "non_positive_ev_hold" if non_positive_ready else "hold_sample"
        )
    )
    bounded_canary = {
        "state": bounded_canary_state,
        "exact_blocker_reason": WINNER_RECOVERY_EXACT_BLOCKER,
        "sample_count": len(exact_blocker_rows),
        "sample_floor": WINNER_RECOVERY_COUNTERFACTUAL_SAMPLE_FLOOR,
        "ready_venue_count": len(positive_ready),
        "operator_action_required": False,
        "next_preopen_auto_apply_candidate": bool(positive_ready),
        "auto_apply_mode": "next_preopen_auto_bounded_live",
        "standalone_real_order_conversion_allowed": False,
        "remaining_real_authority_requirements": [
            "deterministic_preopen_source_quality_and_venue_gate",
            "dated_venue_cohort_runtime_selection_by_threshold_cycle",
            "post_apply_real_execution_attribution",
        ],
        "by_effective_venue": bounded_canary_by_venue,
        "runtime_env_contract": WINNER_RECOVERY_RUNTIME_ENV_KEYS,
        "initial_real_qty_cap": 1,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_role": "bounded_tunable_scale_in_counterfactual",
        "decision_authority": (
            "rolling_source_only_exact_blocker_one_share_canary_candidate"
        ),
        "window_policy": (
            "rolling_clean_baseline_closed_exact_blocker_rows_by_effective_venue"
        ),
        "sample_floor_policy": (
            "source_quality_valid_exact_blocker_rows_ge_10_per_venue"
        ),
        "primary_decision_metric": "notional_weighted_ev_pct",
        "source_quality_gate": (
            "source_only_provenance_exact_blocker_positive_cost_adjusted_ev_and_"
            "explicit_conflict_free_venue"
        ),
        "forbidden_uses": FORBIDDEN_USES
        + ["full_residual_submit", "cross_venue_promotion"],
    }

    return {
        "state": state,
        "section_present": section_present,
        "sample_count": len(rows),
        "ev_eligible_sample_count": ev_eligible_sample_count,
        "sample_floor": 20,
        "sample_floor_met": sample_floor_met,
        "provenance_rejected_count": provenance_rejected_count,
        "realized_incremental_winner_count": winner_count,
        "diagnostic_win_rate": (round(winner_count / len(rows), 4) if rows else 0.0),
        "notional_weighted_ev_pct": notional_weighted_ev_pct,
        "by_effective_venue": _dimension_rollup("effective_venue"),
        "by_market_session_bucket": _dimension_rollup("market_session_bucket"),
        "by_blocker_reason": _dimension_rollup(
            "normal_winner_expansion_blocker_reason"
        ),
        "winner_recovery_bounded_canary_observation": bounded_canary,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_role": "bounded_tunable_scale_in_counterfactual",
        "decision_authority": (
            "rolling_source_only_normal_winner_expansion_observation"
        ),
        "window_policy": "rolling_clean_baseline_closed_normal_winner_expansion_rows",
        "primary_decision_metric": "notional_weighted_ev_pct",
        "source_quality_gate": (
            "source_quality_valid_positive_pyramid_candidate_with_post_candidate_sell"
        ),
        "forbidden_uses": FORBIDDEN_USES,
    }


def _winner_recovery_real_execution_observation(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    section_present = False
    execution_count = 0
    closed_count = 0
    provenance_rejected_count = 0
    source_quality_rejected_count = 0
    rows: list[dict[str, Any]] = []
    for report in reports:
        if not isinstance(
            report.get("real_scale_in_performance_metric_contract"), dict
        ):
            continue
        source_rows = report.get("real_scale_in_performance_rows")
        if not isinstance(source_rows, list):
            continue
        section_present = True
        for row in source_rows:
            if not isinstance(row, dict) or row.get("scale_in_outcome_cohort") != (
                "winner_recovery"
            ):
                continue
            execution_count += 1
            if not _boolish(row.get("closed")):
                continue
            closed_count += 1
            provenance_valid = bool(
                _boolish(row.get("actual_order_submitted"))
                and not _boolish(row.get("broker_order_forbidden"))
                and row.get("runtime_effect") is False
                and row.get("allowed_runtime_apply") is False
                and row.get("decision_authority")
                == "real_scale_in_execution_outcome_observation_only"
                and isinstance(row.get("forbidden_uses"), list)
                and int(row.get("fill_qty") or 0) == 1
            )
            if not provenance_valid:
                provenance_rejected_count += 1
                continue
            if not _boolish(row.get("source_quality_valid")):
                source_quality_rejected_count += 1
                continue
            if (
                _safe_float(row.get("fill_notional_krw"), 0.0) <= 0
                or row.get("scale_in_leg_net_pnl_proxy_krw") is None
            ):
                source_quality_rejected_count += 1
                continue
            rows.append(row)

    valid_notional = sum(_safe_float(row.get("fill_notional_krw"), 0.0) for row in rows)
    valid_net_pnl = sum(
        _safe_float(row.get("scale_in_leg_net_pnl_proxy_krw"), 0.0) for row in rows
    )
    source_quality_adjusted_ev_pct = (
        round(valid_net_pnl / valid_notional * 100.0, 4) if valid_notional > 0 else None
    )
    sample_floor_met = len(rows) >= WINNER_RECOVERY_REAL_PROMOTION_SAMPLE_FLOOR
    positive_ev = bool(
        source_quality_adjusted_ev_pct is not None
        and source_quality_adjusted_ev_pct > 0
        and valid_net_pnl > 0
    )
    state = (
        "not_available"
        if not section_present
        else (
            "observe_one_share_canary"
            if not sample_floor_met
            else (
                "first_planned_residual_leg_candidate_ready"
                if positive_ev
                else "non_positive_ev_hold"
            )
        )
    )

    def _dimension_rollup(dimension: str) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(dimension) or "UNKNOWN")].append(row)
        result = []
        for value, bucket_rows in sorted(grouped.items()):
            bucket_notional = sum(
                _safe_float(row.get("fill_notional_krw"), 0.0) for row in bucket_rows
            )
            bucket_net_pnl = sum(
                _safe_float(row.get("scale_in_leg_net_pnl_proxy_krw"), 0.0)
                for row in bucket_rows
            )
            result.append(
                {
                    dimension: value,
                    "source_quality_valid_closed_count": len(bucket_rows),
                    "scale_in_leg_net_pnl_proxy_krw_sum": round(bucket_net_pnl, 4),
                    "source_quality_adjusted_ev_pct": (
                        round(bucket_net_pnl / bucket_notional * 100.0, 4)
                        if bucket_notional > 0
                        else None
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
        return result

    return {
        "state": state,
        "section_present": section_present,
        "execution_count": execution_count,
        "closed_count": closed_count,
        "source_quality_valid_closed_count": len(rows),
        "source_quality_rejected_count": source_quality_rejected_count,
        "provenance_rejected_count": provenance_rejected_count,
        "sample_floor": WINNER_RECOVERY_REAL_PROMOTION_SAMPLE_FLOOR,
        "sample_floor_met": sample_floor_met,
        "scale_in_leg_net_pnl_proxy_krw_sum": (
            round(valid_net_pnl, 4) if rows else None
        ),
        "source_quality_adjusted_ev_pct": source_quality_adjusted_ev_pct,
        "diagnostic_win_rate": (
            round(
                sum(
                    1
                    for row in rows
                    if _safe_float(row.get("scale_in_leg_net_pnl_proxy_krw"), 0.0) > 0
                )
                / len(rows),
                4,
            )
            if rows
            else None
        ),
        "recommended_next_qty_stage": (
            "first_planned_residual_leg_from_current_position_sizing_owner"
            if state == "first_planned_residual_leg_candidate_ready"
            else "retain_one_share_winner_recovery_canary"
        ),
        "operator_action_required": state
        == "first_planned_residual_leg_candidate_ready",
        "standalone_quantity_increase_allowed": False,
        "remaining_real_authority_requirements": [
            "explicit_operator_approval",
            "current_position_sizing_owner_leg_resolution",
            "dated_venue_cohort_runtime_selection",
            "post_apply_attribution_and_rollback",
        ],
        "by_entry_effective_venue": _dimension_rollup("entry_effective_venue"),
        "by_market_session_bucket": _dimension_rollup("market_session_bucket"),
        "runtime_env_contract": WINNER_RECOVERY_RUNTIME_ENV_KEYS,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_role": "real_scale_in_execution_outcome_attribution",
        "decision_authority": (
            "rolling_source_only_winner_recovery_real_execution_promotion_candidate"
        ),
        "window_policy": (
            "rolling_clean_baseline_winner_recovery_scale_in_to_terminal_sell"
        ),
        "sample_floor_policy": (
            "source_quality_valid_closed_one_share_winner_recovery_rows_ge_20"
        ),
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": (
            "complete_add_and_sell_receipt_economics_quantity_broker_provenance_"
            "with_explicit_entry_venue_session_and_one_share_cap"
        ),
        "forbidden_uses": FORBIDDEN_USES
        + ["automatic_quantity_increase", "full_residual_submit"],
    }


def _winner_recovery_runtime_funnel_observation(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    runtime_block_reasons: Counter[str] = Counter()
    downstream_block_reasons: Counter[str] = Counter()
    section_present = False
    accepted_report_count = 0
    provenance_rejected_report_count = 0
    for report in reports:
        contract = report.get("winner_recovery_runtime_funnel_metric_contract")
        summary = report.get("summary")
        if not isinstance(contract, dict) or not isinstance(summary, dict):
            continue
        funnel = summary.get("winner_recovery_runtime_funnel")
        if not isinstance(funnel, dict):
            continue
        section_present = True
        if not (
            contract.get("metric_role") == "winner_recovery_runtime_funnel_attribution"
            and funnel.get("runtime_effect") is False
            and funnel.get("allowed_runtime_apply") is False
            and funnel.get("decision_authority")
            == "source_only_winner_recovery_runtime_funnel_attribution"
            and funnel.get("source_quality_status") == "pass"
        ):
            provenance_rejected_report_count += 1
            continue
        accepted_report_count += 1
        for key in (
            "runtime_gate_evaluation_count",
            "runtime_gate_selected_count",
            "runtime_gate_blocked_count",
            "selected_downstream_guard_blocked_count",
            "selected_order_submitted_count",
            "selected_executed_count",
            "selected_open_or_unresolved_count",
            "selected_closed_without_submit_count",
            "invalid_timestamp_event_count",
        ):
            totals[key] += int(_safe_float(funnel.get(key), 0.0) or 0)
        for item in funnel.get("runtime_gate_block_reason_counts") or []:
            if isinstance(item, dict):
                runtime_block_reasons[str(item.get("reason") or "unknown")] += int(
                    _safe_float(item.get("count"), 0.0) or 0
                )
        for item in funnel.get("downstream_guard_block_reason_counts") or []:
            if isinstance(item, dict):
                downstream_block_reasons[str(item.get("reason") or "unknown")] += int(
                    _safe_float(item.get("count"), 0.0) or 0
                )

    selected_count = totals["runtime_gate_selected_count"]
    if not accepted_report_count and provenance_rejected_report_count:
        state = "source_quality_blocked"
    elif totals["selected_executed_count"]:
        state = "real_execution_observed"
    elif totals["selected_order_submitted_count"]:
        state = "selected_order_submitted_no_execution"
    elif totals["selected_downstream_guard_blocked_count"]:
        state = "selected_downstream_guard_blocked"
    elif totals["selected_closed_without_submit_count"]:
        state = "selected_closed_without_submit"
    elif selected_count:
        state = "selected_open_or_unresolved"
    elif totals["runtime_gate_blocked_count"]:
        state = "runtime_gate_only_no_selection"
    else:
        state = (
            "not_available" if not section_present else "no_runtime_gate_observation"
        )
    non_execution_layers = {
        "winner_recovery_runtime_gate": totals["runtime_gate_blocked_count"],
        "downstream_scale_in_guard": totals["selected_downstream_guard_blocked_count"],
        "execution_receipt_or_fill": max(
            0,
            totals["selected_order_submitted_count"]
            - totals["selected_executed_count"],
        ),
        "downstream_event_provenance": totals["selected_open_or_unresolved_count"],
        "position_closed_without_submit": totals[
            "selected_closed_without_submit_count"
        ],
        "rejected_report_provenance": provenance_rejected_report_count,
    }
    dominant_non_execution_layer = max(
        non_execution_layers,
        key=lambda key: (non_execution_layers[key], key),
    )
    if non_execution_layers[dominant_non_execution_layer] == 0:
        dominant_non_execution_layer = "none"
    count_fields = {
        key: totals[key]
        for key in (
            "runtime_gate_evaluation_count",
            "runtime_gate_selected_count",
            "runtime_gate_blocked_count",
            "selected_downstream_guard_blocked_count",
            "selected_order_submitted_count",
            "selected_executed_count",
            "selected_open_or_unresolved_count",
            "selected_closed_without_submit_count",
            "invalid_timestamp_event_count",
        )
    }
    return {
        "state": state,
        "section_present": section_present,
        "accepted_report_count": accepted_report_count,
        "provenance_rejected_report_count": provenance_rejected_report_count,
        **count_fields,
        "runtime_gate_block_reason_counts": [
            {"reason": reason, "count": count}
            for reason, count in runtime_block_reasons.most_common()
        ],
        "downstream_guard_block_reason_counts": [
            {"reason": reason, "count": count}
            for reason, count in downstream_block_reasons.most_common()
        ],
        "selection_to_submit_rate": (
            round(totals["selected_order_submitted_count"] / selected_count, 4)
            if selected_count
            else 0.0
        ),
        "selection_to_execution_rate": (
            round(totals["selected_executed_count"] / selected_count, 4)
            if selected_count
            else 0.0
        ),
        "dominant_non_execution_layer": dominant_non_execution_layer,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_role": "winner_recovery_runtime_funnel_attribution",
        "decision_authority": (
            "rolling_source_only_winner_recovery_runtime_funnel_attribution"
        ),
        "window_policy": "rolling_clean_baseline_runtime_gate_to_execution_funnel",
        "sample_floor": "1_winner_recovery_runtime_gate_evaluation",
        "primary_decision_metric": (
            "runtime_gate_selected_count_selected_downstream_guard_blocked_count_"
            "selected_closed_without_submit_count_selected_order_submitted_count_"
            "selected_executed_count"
        ),
        "source_quality_gate": (
            "feedback_metric_contract_and_source_only_summary_provenance"
        ),
        "forbidden_uses": FORBIDDEN_USES,
    }


def _post_probe_real_outcome_observation(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    section_present = False
    provenance_rejected_count = 0
    source_quality_rejected_count = 0
    for report in reports:
        if not isinstance(report.get("post_probe_real_outcome_metric_contract"), dict):
            continue
        source_rows = report.get("one_share_pyramid_opportunity_rows")
        if not isinstance(source_rows, list):
            continue
        section_present = True
        for row in source_rows:
            if not isinstance(row, dict):
                continue
            if (
                str(row.get("post_probe_real_outcome_label") or "")
                not in POST_PROBE_REAL_OUTCOME_CLOSED_LABELS
            ):
                continue
            if not _boolish(row.get("post_probe_real_outcome_source_quality_valid")):
                source_quality_rejected_count += 1
                continue
            provenance_valid = bool(
                row.get("runtime_effect") is False
                and row.get("allowed_runtime_apply") is False
                and str(row.get("decision_authority") or "").startswith("source_only_")
                and isinstance(row.get("forbidden_uses"), list)
                and _boolish(row.get("post_probe_probe_actual_order_submitted"))
            )
            if not provenance_valid:
                provenance_rejected_count += 1
                continue
            rows.append(row)

    confirmation_ready_rows = [
        row
        for row in rows
        if _boolish(row.get("post_probe_real_confirmation_ready"))
        and _boolish(row.get("post_probe_counterfactual_source_quality_valid"))
    ]
    confirmation_ready_source_blocked_count = sum(
        1
        for row in rows
        if _boolish(row.get("post_probe_real_confirmation_ready"))
        and not _boolish(row.get("post_probe_counterfactual_source_quality_valid"))
    )
    runtime_confirmation_source_quality_disputed_count = sum(
        1
        for row in rows
        if str(row.get("post_probe_confirmation_contract_alignment") or "")
        == "runtime_confirmed_source_quality_disputed"
    )
    weighted = [
        (
            _safe_float(row.get("post_probe_real_outcome_profit_pct"), 0.0),
            int(row.get("post_probe_counterfactual_first_leg_notional_krw") or 0),
        )
        for row in confirmation_ready_rows
        if int(row.get("post_probe_counterfactual_first_leg_notional_krw") or 0) > 0
    ]
    winner_count = sum(
        1
        for row in rows
        if str(row.get("post_probe_real_outcome_label") or "").startswith(
            "profitable_zero_fill"
        )
    )
    ready_winner_count = sum(
        1
        for row in confirmation_ready_rows
        if row.get("post_probe_real_outcome_label")
        == "profitable_zero_fill_confirmation_ready"
    )
    ready_loss_count = sum(
        1
        for row in confirmation_ready_rows
        if row.get("post_probe_real_outcome_label")
        == "loss_or_flat_zero_fill_confirmation_ready"
    )
    learning_sample_count = len(confirmation_ready_rows)
    learning_updated = learning_sample_count >= CUMULATIVE_LEARNING_SAMPLE_FLOOR
    sample_floor_met = (
        learning_sample_count >= POST_PROBE_RUNTIME_PROMOTION_SAMPLE_FLOOR
    )
    notional_weighted_ev_pct = (
        round(
            sum(value * notional for value, notional in weighted)
            / sum(notional for _, notional in weighted),
            4,
        )
        if weighted
        else 0.0
    )
    if not section_present:
        state = "not_available"
    elif not sample_floor_met:
        state = "hold_sample"
    elif notional_weighted_ev_pct > 0:
        state = "positive_ev_profile_candidate"
    else:
        state = "non_positive_ev_hold"

    def _dimension_rollup(dimension: str) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in confirmation_ready_rows:
            if dimension == "effective_venue" and not _boolish(
                row.get("venue_source_quality_valid")
            ):
                continue
            value = str(row.get(dimension) or "UNKNOWN").strip() or "UNKNOWN"
            grouped[value].append(row)
        result = []
        for value, bucket_rows in sorted(grouped.items()):
            bucket_weighted = [
                (
                    _safe_float(row.get("post_probe_real_outcome_profit_pct"), 0.0),
                    int(
                        row.get("post_probe_counterfactual_first_leg_notional_krw") or 0
                    ),
                )
                for row in bucket_rows
                if int(row.get("post_probe_counterfactual_first_leg_notional_krw") or 0)
                > 0
            ]
            result.append(
                {
                    dimension: value,
                    "sample_count": len(bucket_rows),
                    "sample_floor": 20,
                    "sample_floor_met": len(bucket_rows) >= 20,
                    "notional_weighted_ev_pct": (
                        round(
                            sum(
                                outcome * notional
                                for outcome, notional in bucket_weighted
                            )
                            / sum(notional for _, notional in bucket_weighted),
                            4,
                        )
                        if bucket_weighted
                        else 0.0
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
        return result

    return {
        "state": state,
        "section_present": section_present,
        "closed_real_outcome_count": len(rows),
        "confirmation_ready_count": len(confirmation_ready_rows),
        "cumulative_judgment_quality": {
            "learning_sample_floor": CUMULATIVE_LEARNING_SAMPLE_FLOOR,
            "learning_sample_count": learning_sample_count,
            "learning_updated": learning_updated,
            "learning_update_policy": (
                "one_mature_post_probe_outcome_updates_cumulative_judgment_quality"
            ),
            "notional_weighted_ev_pct": notional_weighted_ev_pct,
            "runtime_promotion_sample_floor": (
                POST_PROBE_RUNTIME_PROMOTION_SAMPLE_FLOOR
            ),
            "learning_floor_grants_runtime_promotion": False,
        },
        "confirmation_ready_counterfactual_source_blocked_count": (
            confirmation_ready_source_blocked_count
        ),
        "sample_floor": POST_PROBE_RUNTIME_PROMOTION_SAMPLE_FLOOR,
        "sample_floor_met": sample_floor_met,
        "provenance_rejected_count": provenance_rejected_count,
        "source_quality_rejected_count": source_quality_rejected_count,
        "runtime_confirmation_source_quality_disputed_count": (
            runtime_confirmation_source_quality_disputed_count
        ),
        "realized_winner_zero_fill_count": winner_count,
        "realized_loss_or_flat_zero_fill_count": len(rows) - winner_count,
        "confirmation_ready_winner_count": ready_winner_count,
        "confirmation_ready_loss_or_flat_count": ready_loss_count,
        "diagnostic_win_rate": (round(winner_count / len(rows), 4) if rows else 0.0),
        "notional_weighted_ev_pct": notional_weighted_ev_pct,
        "by_effective_venue": _dimension_rollup("effective_venue"),
        "by_market_session_bucket": _dimension_rollup("market_session_bucket"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_role": "multi_leg_post_probe_real_outcome_attribution",
        "decision_authority": (
            "rolling_source_only_post_probe_real_outcome_no_runtime_mutation"
        ),
        "window_policy": (
            "rolling_clean_baseline_closed_zero_fill_probe_to_terminal_sell"
        ),
        "sample_floor_policy": (
            "rolling_confirmation_ready_source_quality_valid_rows_ge_20"
        ),
        "primary_decision_metric": "notional_weighted_ev_pct",
        "source_quality_gate": (
            "exact_probe_terminal_fill_real_sell_profit_explicit_venue_and_"
            "version_proven_post_probe_evidence"
        ),
        "forbidden_uses": FORBIDDEN_USES,
    }


def _post_probe_reprice_observation(reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        source_rows = report.get("one_share_pyramid_opportunity_rows")
        if not isinstance(source_rows, list):
            continue
        for row in source_rows:
            if not isinstance(row, dict):
                continue
            if not _boolish(row.get("post_probe_reprice_observed")):
                continue
            if not _boolish(row.get("post_probe_reprice_outcome_source_quality_valid")):
                continue
            if row.get("post_probe_real_outcome_profit_pct") is None:
                continue
            rows.append(row)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        profiles = row.get("post_probe_reprice_profiles") or ["unknown"]
        profile = "+".join(str(value) for value in profiles) or "unknown"
        grouped[profile].append(row)
    profile_quality = []
    for profile, profile_rows in sorted(grouped.items()):
        profits = [
            _safe_float(row.get("post_probe_real_outcome_profit_pct"), 0.0)
            for row in profile_rows
        ]
        improvement = [
            _safe_float(row.get("post_probe_reprice_avg_passive_improvement_bps"), 0.0)
            for row in profile_rows
            if row.get("post_probe_reprice_avg_passive_improvement_bps") is not None
        ]
        profile_quality.append(
            {
                "reprice_profile": profile,
                "sample_count": len(profile_rows),
                "equal_weight_avg_profit_pct": round(sum(profits) / len(profits), 4),
                "avg_passive_improvement_bps": (
                    round(sum(improvement) / len(improvement), 4)
                    if improvement
                    else None
                ),
            }
        )
    learning_sample_count = len(rows)
    equal_weight_avg_profit_pct = (
        round(
            sum(
                _safe_float(row.get("post_probe_real_outcome_profit_pct"), 0.0)
                for row in rows
            )
            / learning_sample_count,
            4,
        )
        if learning_sample_count
        else None
    )
    return {
        "state": (
            "cumulative_judgment_updated"
            if learning_sample_count >= CUMULATIVE_LEARNING_SAMPLE_FLOOR
            else "hold_sample"
        ),
        "learning_sample_floor": CUMULATIVE_LEARNING_SAMPLE_FLOOR,
        "learning_sample_count": learning_sample_count,
        "learning_updated": (learning_sample_count >= CUMULATIVE_LEARNING_SAMPLE_FLOOR),
        "learning_update_policy": (
            "one_mature_leg_reprice_outcome_updates_cumulative_judgment_quality"
        ),
        "equal_weight_avg_profit_pct": equal_weight_avg_profit_pct,
        "profile_quality": profile_quality,
        "runtime_promotion_sample_floor": POST_PROBE_RUNTIME_PROMOTION_SAMPLE_FLOOR,
        "learning_floor_grants_runtime_promotion": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "metric_role": "execution_quality_real_only",
        "decision_authority": "postclose_reprice_quality_observation_only",
        "window_policy": (
            "clean_baseline_cumulative_closed_real_post_probe_reprice_outcomes"
        ),
        "sample_floor": {
            "cumulative_learning": CUMULATIVE_LEARNING_SAMPLE_FLOOR,
            "runtime_promotion_real": POST_PROBE_RUNTIME_PROMOTION_SAMPLE_FLOOR,
        },
        "primary_decision_metric": "equal_weight_avg_profit_pct",
        "source_quality_gate": (
            "complete_post_probe_resolver_profile_action_previous_resolved_price_"
            "and_valid_real_terminal_outcome"
        ),
        "forbidden_uses": FORBIDDEN_USES,
    }


def _provenance_present(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        "actual_order_submitted" in row
        and "broker_order_forbidden" in row
        and "runtime_effect" in row
        and "decision_authority" in row
        and "forbidden_uses" in row
        for row in rows
    )


def _row_rates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sample_count = len(rows)
    recovered = sum(
        1
        for row in rows
        if row.get("pyramid_feedback_label") == "pyramid_would_have_helped"
    )
    correct_block = sum(
        1
        for row in rows
        if row.get("pyramid_feedback_label") == "pyramid_correctly_blocked"
    )
    reversal = sum(
        1
        for row in rows
        if row.get("pyramid_feedback_label") == "pyramid_overheat_or_reversal_risk"
    )
    label_counts = Counter(
        str(row.get("pyramid_feedback_label") or "unknown") for row in rows
    )
    return {
        "sample_count": sample_count,
        "recovered_or_extended_count": recovered,
        "correctly_blocked_count": correct_block,
        "reversal_or_flat_count": reversal,
        "recovered_or_extended_rate": recovered / sample_count if sample_count else 0.0,
        "correctly_blocked_rate": correct_block / sample_count if sample_count else 0.0,
        "reversal_or_flat_rate": reversal / sample_count if sample_count else 0.0,
        "label_counts": [
            {"label": key, "count": value} for key, value in label_counts.most_common()
        ],
    }


def _profit_reached(row: dict[str, Any]) -> float | None:
    for key in (
        "max_profit_seen",
        "pyramid_opportunity_peak_profit",
        "peak_profit",
        "pyramid_opportunity_profit_rate",
        "profit_rate",
    ):
        if row.get(key) is not None:
            value = _safe_float(row.get(key), math.nan)
            return value if math.isfinite(value) and value >= -100.0 else None
    return None


def _final_profit(row: dict[str, Any]) -> float | None:
    if row.get("final_profit_rate") is not None:
        value = _safe_float(row.get("final_profit_rate"), math.nan)
        return value if math.isfinite(value) and value >= -100.0 else None
    return None


def _optional_bool(value: Any) -> bool | None:
    if value in (None, "", "-"):
        return None
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    if token in {"1", "true", "yes", "y", "on"}:
        return True
    if token in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _pyramid_gate_replay(row: dict[str, Any], threshold: float) -> dict[str, Any]:
    """Replay only the existing PYRAMID gate from one timestamped observation."""
    missing: list[str] = []

    def number(name: str) -> float | None:
        value = _safe_float(row.get(name), math.nan)
        if not math.isfinite(value):
            missing.append(name)
            return None
        return float(value)

    def boolean(name: str) -> bool | None:
        value = _optional_bool(row.get(name))
        if value is None:
            missing.append(name)
        return value

    profit = number("profit_rate")
    drawdown = number("drawdown_from_peak")
    is_new_high = boolean("is_new_high")
    strong_allowed = boolean("strong_continuation_allowed")
    strong_min = number("strong_continuation_min_profit_pct")
    ai_available = boolean("ai_score_available")
    ai_score = number("current_ai_score")
    min_ai = number("min_ai_score")
    pressure_usable = boolean("tick_aggressor_pressure_usable")
    trusted_pressure_count = number("tick_aggressor_trusted_count")
    buy_pressure = number("buy_pressure_10t")
    min_buy_pressure = number("min_buy_pressure")
    tick_accel = number("tick_acceleration_ratio")
    min_tick = number("min_tick_accel")
    stale = boolean("reversal_feature_stale")
    large_sell = boolean("large_sell_print_detected")
    micro_available = boolean("micro_vwap_available")
    micro_vwap = (
        number("curr_vs_micro_vwap_bp") if micro_available is not False else None
    )
    max_micro = number("max_micro_vwap_bps")
    if missing:
        return {
            "status": "source_quality_blocked",
            "selected": False,
            "reason": "missing_gate_context",
            "source_quality_reasons": sorted(set(missing)),
        }

    assert profit is not None
    assert drawdown is not None
    assert is_new_high is not None
    assert strong_allowed is not None
    assert strong_min is not None
    assert ai_available is not None
    assert ai_score is not None
    assert min_ai is not None
    assert pressure_usable is not None
    assert trusted_pressure_count is not None
    assert buy_pressure is not None
    assert min_buy_pressure is not None
    assert tick_accel is not None
    assert min_tick is not None
    assert stale is not None
    assert large_sell is not None
    assert micro_available is not None
    assert max_micro is not None

    effective_strong_min = min(float(threshold), strong_min)
    threshold_pass = bool(
        profit >= threshold
        or (profit < threshold and strong_allowed and profit >= effective_strong_min)
    )
    if not threshold_pass:
        return {
            "status": "evaluated",
            "selected": False,
            "reason": "profit_not_enough",
            "source_quality_reasons": [],
        }
    if not (is_new_high or drawdown <= 0.3):
        return {
            "status": "evaluated",
            "selected": False,
            "reason": "trend_not_strong",
            "source_quality_reasons": [],
        }

    quality_decision = _pyramid_quality_decision(
        {
            "current_ai_score": ai_score,
            "ai_score_available": ai_available,
            "min_ai_score": min_ai,
            "buy_pressure_10t": buy_pressure,
            "min_buy_pressure": min_buy_pressure,
            "tick_acceleration_ratio": tick_accel,
            "min_tick_accel": min_tick,
            "curr_vs_micro_vwap_bp": (
                micro_vwap if micro_available and micro_vwap is not None else "-"
            ),
            "max_micro_vwap_bps": max_micro,
            "reversal_feature_stale": stale,
            "tick_aggressor_pressure_usable": pressure_usable,
            "tick_aggressor_trusted_count": trusted_pressure_count,
            "large_sell_print_detected": large_sell,
        }
    )
    selected = bool(quality_decision.get("allowed"))
    return {
        "status": "evaluated",
        "selected": selected,
        "reason": "scalping_pyramid_ok" if selected else "quality_or_safety_blocked",
        "support_score": quality_decision.get("support_score"),
        "hard_blockers": sorted(set(quality_decision.get("hard_blockers") or [])),
        "source_quality_reasons": [],
    }


def _threshold_replay_rows(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        contract = report.get("pyramid_threshold_replay_metric_contract")
        if not isinstance(contract, dict) or contract.get("metric_role") != (
            "bounded_tunable_threshold_gate_counterfactual"
        ):
            continue
        contract_reasons: list[str] = []
        if int(_safe_float(report.get("schema_version"), -1.0)) != (
            REPLAY_SOURCE_SCHEMA_VERSION
        ):
            contract_reasons.append("threshold_replay_report_schema_invalid")
        if str(contract.get("contract_version") or "") != (
            REPLAY_SOURCE_CONTRACT_VERSION
        ):
            contract_reasons.append("threshold_replay_contract_version_invalid")
        if str(contract.get("decision_authority") or "") != (
            "source_only_fixed_observed_exit_pyramid_gate_replay"
        ):
            contract_reasons.append("threshold_replay_contract_authority_invalid")
        if str(contract.get("primary_decision_metric") or "") != (
            "source_quality_adjusted_ev_pct"
        ):
            contract_reasons.append("threshold_replay_primary_metric_invalid")
        source_date = str(report.get("target_date") or "")
        for raw in report.get("pyramid_threshold_replay_rows") or []:
            if not isinstance(raw, dict):
                continue
            row = dict(raw)
            source_reasons = list(row.get("source_quality_reasons") or []) + list(
                contract_reasons
            )
            if row.get("runtime_effect") is not False:
                source_reasons.append("threshold_replay_runtime_effect_not_false")
            if row.get("allowed_runtime_apply") is not False:
                source_reasons.append(
                    "threshold_replay_allowed_runtime_apply_not_false"
                )
            if str(row.get("decision_authority") or "") != (
                "source_only_fixed_observed_exit_pyramid_gate_replay"
            ):
                source_reasons.append("threshold_replay_decision_authority_invalid")
            if row.get("same_stage_competing_owner") is True:
                source_reasons.append("same_stage_competing_bridge_owner")
            if row.get("runtime_prior_action_applied") is True:
                source_reasons.append("runtime_prior_action_applied")
            if str(row.get("effective_venue") or "") not in {
                "KRX",
                "NXT",
                "PREMARKET_KRX_LIKE",
            } or str(row.get("effective_venue_source") or "") == (
                "terminal_cycle_fallback"
            ):
                source_reasons.append("threshold_replay_evaluation_venue_invalid")
            if not str(row.get("market_session_bucket") or "").strip():
                source_reasons.append("threshold_replay_evaluation_session_missing")
            if str(row.get("pyramid_evaluation_schema") or "") != REPLAY_EVENT_SCHEMA:
                source_reasons.append("threshold_replay_event_schema_invalid")
            if row.get("fixed_exit_economic_replay_ready") is not True:
                source_reasons.append("fixed_exit_economic_replay_not_ready")
            if str(row.get("price_evidence_level") or "") != REPLAY_PRICE_EVIDENCE:
                source_reasons.append("threshold_replay_price_evidence_invalid")
            if row.get("quote_stale") is not False:
                source_reasons.append("threshold_replay_quote_not_fresh")
            if row.get("pyramid_price_resolver_observed") is not True:
                source_reasons.append("threshold_replay_resolver_not_observed")
            if row.get("pyramid_price_resolver_allowed") is not True:
                source_reasons.append("threshold_replay_resolver_not_allowed")
            if str(row.get("pyramid_price_resolver_reason") or "") != (
                "scale_in_price_resolved"
            ) or str(row.get("pyramid_price_resolver_price_source") or "") not in {
                "best_bid",
                "defensive_ticks",
                "best_bid_defensive_clamp",
            }:
                source_reasons.append(
                    "threshold_replay_resolver_limit_contract_invalid"
                )
            best_ask = _safe_float(row.get("executable_best_ask"), math.nan)
            best_bid = _safe_float(row.get("executable_best_bid"), math.nan)
            resolver_best_ask = _safe_float(
                row.get("pyramid_price_resolver_best_ask"), math.nan
            )
            resolver_best_bid = _safe_float(
                row.get("pyramid_price_resolver_best_bid"), math.nan
            )
            if (
                not math.isfinite(best_ask)
                or not math.isfinite(best_bid)
                or best_ask <= 0
                or best_bid <= 0
                or best_ask < best_bid
            ):
                source_reasons.append("threshold_replay_executable_bbo_invalid")
            if (
                not math.isfinite(resolver_best_ask)
                or not math.isfinite(resolver_best_bid)
                or not math.isclose(best_ask, resolver_best_ask, abs_tol=1e-9)
                or not math.isclose(best_bid, resolver_best_bid, abs_tol=1e-9)
            ):
                source_reasons.append("threshold_replay_resolver_bbo_mismatch")
            replay_entry = _safe_float(row.get("replay_entry_price"), math.nan)
            resolver_price = _safe_float(
                row.get("pyramid_price_resolver_order_price"), math.nan
            )
            if (
                not math.isfinite(replay_entry)
                or not math.isfinite(resolver_price)
                or replay_entry <= 0
                or resolver_price <= 0
                or not math.isclose(replay_entry, resolver_price, abs_tol=1e-9)
            ):
                source_reasons.append("threshold_replay_resolver_price_mismatch")
            if source_reasons:
                row["gate_replay_source_quality_valid"] = False
                row["source_quality_reasons"] = sorted(set(source_reasons))
            row["source_target_date"] = source_date
            rows.append(row)
    return rows


def _threshold_replay_episode_result(
    events: list[dict[str, Any]], threshold: float
) -> dict[str, Any]:
    ordered = sorted(
        events,
        key=lambda row: (
            str(row.get("source_event_ts") or ""),
            str(row.get("pyramid_evaluation_id") or ""),
        ),
    )
    exclusion_reasons: list[str] = []
    for row in ordered:
        if not row.get("gate_replay_source_quality_valid"):
            exclusion_reasons.extend(row.get("source_quality_reasons") or [])
            continue
        configured_threshold = _safe_float(
            row.get("configured_min_profit_pct"), math.nan
        )
        if not math.isfinite(configured_threshold):
            exclusion_reasons.append("configured_min_profit_missing")
            continue
        observed_replay = _pyramid_gate_replay(row, configured_threshold)
        if observed_replay.get("status") != "evaluated":
            exclusion_reasons.extend(
                observed_replay.get("source_quality_reasons") or []
            )
            continue
        observed_selected = _optional_bool(row.get("observed_gate_selected"))
        if observed_selected is None:
            exclusion_reasons.append("observed_gate_selected_missing")
        elif bool(observed_replay.get("selected")) != observed_selected:
            exclusion_reasons.append("observed_gate_replay_mismatch")
    if exclusion_reasons:
        return {
            "status": "source_quality_blocked",
            "selected": False,
            "net_profit_pct": None,
            "selected_event_id": None,
            "source_quality_reasons": sorted(set(exclusion_reasons)),
        }

    for row in ordered:
        replay = _pyramid_gate_replay(row, threshold)
        if replay.get("status") != "evaluated":
            return {
                "status": "source_quality_blocked",
                "selected": False,
                "net_profit_pct": None,
                "selected_event_id": None,
                "source_quality_reasons": sorted(
                    set(replay.get("source_quality_reasons") or [])
                )
                or ["no_replayable_gate_event"],
            }
        if not replay.get("selected"):
            continue
        entry_price = _safe_float(row.get("replay_entry_price"), 0.0)
        sell_price = _safe_float(row.get("sell_price"), 0.0)
        if (
            not row.get("fixed_exit_economic_replay_ready")
            or entry_price <= 0
            or sell_price <= 0
        ):
            return {
                "status": "selected_price_or_outcome_unusable",
                "selected": True,
                "net_profit_pct": None,
                "selected_event_id": row.get("pyramid_evaluation_id"),
                "source_quality_reasons": sorted(
                    set(
                        (row.get("source_quality_reasons") or [])
                        + ["selected_event_fixed_exit_economics_unusable"]
                    )
                ),
            }
        return {
            "status": "evaluated",
            "selected": True,
            "net_profit_pct": calculate_net_profit_rate(
                entry_price,
                sell_price,
                precision=8,
            ),
            "selected_event_id": row.get("pyramid_evaluation_id"),
            "entry_price": entry_price,
            "sell_price": sell_price,
            "price_evidence_level": row.get("price_evidence_level"),
            "effective_venue": row.get("effective_venue"),
            "source_quality_reasons": [],
        }
    if ordered:
        episode_venues = {str(row.get("effective_venue") or "") for row in ordered}
        return {
            "status": "evaluated",
            "selected": False,
            "net_profit_pct": 0.0,
            "selected_event_id": None,
            "effective_venue": (
                next(iter(episode_venues)) if len(episode_venues) == 1 else "UNKNOWN"
            ),
            "source_quality_reasons": [],
        }
    return {
        "status": "source_quality_blocked",
        "selected": False,
        "net_profit_pct": None,
        "selected_event_id": None,
        "source_quality_reasons": sorted(set(exclusion_reasons))
        or ["no_replayable_gate_event"],
    }


def _pyramid_threshold_replay_grid(
    rows: list[dict[str, Any]], current_threshold: float
) -> list[dict[str, Any]]:
    if not rows:
        return []
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        position_key = str(row.get("position_key") or "").strip()
        source_date = str(row.get("source_target_date") or "").strip()
        if position_key and source_date:
            by_episode[f"{source_date}:{position_key}"].append(row)
    if not by_episode:
        return []
    thresholds = {
        round(PROFIT_GRID_MIN + (index * PROFIT_GRID_STEP), 1)
        for index in range(
            int(round((PROFIT_GRID_MAX - PROFIT_GRID_MIN) / PROFIT_GRID_STEP)) + 1
        )
    }
    thresholds.add(float(current_threshold))
    ordered_thresholds = sorted(thresholds)
    episode_results = {
        episode_key: {
            threshold: _threshold_replay_episode_result(events, threshold)
            for threshold in ordered_thresholds
        }
        for episode_key, events in by_episode.items()
    }
    aligned_episode_keys = {
        episode_key
        for episode_key, results_by_threshold in episode_results.items()
        if all(
            item.get("status") == "evaluated" for item in results_by_threshold.values()
        )
    }
    grid: list[dict[str, Any]] = []
    for threshold in ordered_thresholds:
        results = [
            results_by_threshold[threshold]
            for results_by_threshold in episode_results.values()
        ]
        aligned_results = [
            episode_results[episode_key][threshold]
            for episode_key in sorted(aligned_episode_keys)
        ]
        comparable = aligned_results
        selected = [item for item in comparable if item.get("selected")]
        net_values = [float(item.get("net_profit_pct") or 0.0) for item in comparable]
        selected_net_values = [
            float(item.get("net_profit_pct") or 0.0) for item in selected
        ]
        exclusion_counts = Counter(
            reason
            for item in results
            if item.get("status") != "evaluated"
            for reason in item.get("source_quality_reasons") or [item.get("status")]
        )
        positive_exit_count = sum(1 for value in selected_net_values if value > 0)
        venue_counts = Counter(
            str(item.get("effective_venue") or "UNKNOWN") for item in comparable
        )
        venue_rows = []
        for venue in sorted(venue_counts):
            venue_results = [
                item
                for item in comparable
                if str(item.get("effective_venue") or "UNKNOWN") == venue
            ]
            venue_values = [
                float(item.get("net_profit_pct") or 0.0) for item in venue_results
            ]
            venue_rows.append(
                {
                    "effective_venue": venue,
                    "comparable_episode_count": len(venue_results),
                    "eligible_count": sum(
                        1 for item in venue_results if item.get("selected")
                    ),
                    "source_quality_adjusted_ev_pct": (
                        sum(venue_values) / len(venue_values) if venue_values else 0.0
                    ),
                    "runtime_effect": False,
                }
            )
        grid.append(
            {
                "min_profit_pct": threshold,
                "source_episode_count": len(by_episode),
                "comparable_episode_count": len(comparable),
                "source_quality_excluded_episode_count": len(results) - len(comparable),
                "aligned_comparison_episode_count": len(comparable),
                "comparison_effective_venue_counts": dict(venue_counts),
                "source_quality_adjusted_ev_by_effective_venue": venue_rows,
                "eligible_count": len(selected),
                "eligible_rate": len(selected) / len(comparable) if comparable else 0.0,
                "positive_exit_count": positive_exit_count,
                "positive_exit_rate": (
                    positive_exit_count / len(selected) if selected else 0.0
                ),
                "loss_or_flat_count": len(selected) - positive_exit_count,
                "loss_or_flat_rate": (
                    (len(selected) - positive_exit_count) / len(selected)
                    if selected
                    else 0.0
                ),
                "trade_cost_rate": get_trade_cost_rate(),
                "trade_cost_pct": round(get_trade_cost_rate() * 100.0, 8),
                "cost_application": "calculate_net_profit_rate_once_on_sell_notional",
                "trade_cost_rate_source": "shared_trade_profit_runtime_config",
                "trade_cost_schedule_scope": (
                    "runtime_config_not_date_or_product_specific"
                ),
                "slippage_policy": "excluded_resolver_limit_price_counterfactual",
                "avg_incremental_exit_profit_pct": (
                    sum(selected_net_values) / len(selected_net_values)
                    if selected_net_values
                    else 0.0
                ),
                "equal_weight_avg_profit_pct": (
                    sum(selected_net_values) / len(selected_net_values)
                    if selected_net_values
                    else 0.0
                ),
                "notional_weighted_ev_pct": None,
                "notional_weighted_ev_status": (
                    "unavailable_without_compatible_quantity_provenance"
                ),
                "source_quality_adjusted_ev_pct": (
                    sum(net_values) / len(comparable) if comparable else 0.0
                ),
                "equal_weight_expected_net_profit_contribution_pct": (
                    sum(net_values) / len(comparable) if comparable else 0.0
                ),
                "source_quality_exclusion_reasons": [
                    {"reason": key, "count": value}
                    for key, value in exclusion_counts.most_common()
                ],
                "replay_method": (
                    "fixed_observed_exit_first_eligible_event_existing_resolver_price"
                ),
                "causal_runtime_effect_claimed": False,
                "comparison_alignment": "same_complete_episode_set_all_thresholds",
                "runtime_effect": False,
            }
        )
    return grid


def _profit_threshold_grid(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    usable_rows = [
        (float(reached), float(final), row)
        for row in rows
        if (reached := _profit_reached(row)) is not None
        and (final := _final_profit(row)) is not None
    ]
    if not usable_rows:
        return []
    assumed_trade_cost_pct = round(get_trade_cost_rate() * 100.0, 4)
    grid: list[dict[str, Any]] = []
    steps = int(round((PROFIT_GRID_MAX - PROFIT_GRID_MIN) / PROFIT_GRID_STEP)) + 1
    for index in range(steps):
        threshold = round(PROFIT_GRID_MIN + (index * PROFIT_GRID_STEP), 1)
        eligible = [
            (reached, final, row)
            for reached, final, row in usable_rows
            if reached >= threshold
        ]
        eligible_count = len(eligible)
        gross_incremental = [
            ((((1.0 + (final / 100.0)) / (1.0 + (threshold / 100.0))) - 1.0) * 100.0)
            for _, final, _ in eligible
        ]
        net_incremental = [
            value - assumed_trade_cost_pct for value in gross_incremental
        ]
        positive_exit_count = sum(1 for value in net_incremental if value > 0.0)
        loss_or_flat_count = eligible_count - positive_exit_count
        missed_upside = [max(0.0, reached - threshold) for reached, _, _ in eligible]
        label_counts = Counter(
            str(row.get("pyramid_feedback_label") or "unknown")
            for _, _, row in eligible
        )
        grid.append(
            {
                "min_profit_pct": threshold,
                "source_row_count": len(usable_rows),
                "eligible_count": eligible_count,
                "eligible_rate": (
                    eligible_count / len(usable_rows) if usable_rows else 0.0
                ),
                "positive_exit_count": positive_exit_count,
                "positive_exit_rate": (
                    positive_exit_count / eligible_count if eligible_count else 0.0
                ),
                "loss_or_flat_count": loss_or_flat_count,
                "loss_or_flat_rate": (
                    loss_or_flat_count / eligible_count if eligible_count else 0.0
                ),
                "assumed_trade_cost_pct": assumed_trade_cost_pct,
                "avg_gross_incremental_exit_profit_pct": (
                    sum(gross_incremental) / len(gross_incremental)
                    if gross_incremental
                    else 0.0
                ),
                "avg_incremental_exit_profit_pct": (
                    sum(net_incremental) / len(net_incremental)
                    if net_incremental
                    else 0.0
                ),
                "equal_weight_expected_net_profit_contribution_pct": (
                    sum(net_incremental) / len(usable_rows) if usable_rows else 0.0
                ),
                "avg_missed_upside_after_threshold_pct": (
                    sum(missed_upside) / len(missed_upside) if missed_upside else 0.0
                ),
                "label_counts": [
                    {"label": key, "count": value}
                    for key, value in label_counts.most_common()
                ],
            }
        )
    return grid


def _nearest_grid_row(
    grid: list[dict[str, Any]], threshold: float
) -> dict[str, Any] | None:
    if not grid:
        return None
    return min(
        grid, key=lambda row: abs(float(row.get("min_profit_pct") or 0.0) - threshold)
    )


def _profit_grid_decision(
    current: dict[str, Any], grid: list[dict[str, Any]]
) -> dict[str, Any]:
    current_threshold = float(current["min_profit_pct"])
    current_row = _nearest_grid_row(grid, current_threshold)
    current_row_exact = bool(
        current_row
        and math.isclose(
            float(current_row.get("min_profit_pct") or 0.0),
            current_threshold,
            abs_tol=1e-9,
        )
    )
    eligible_rows = [
        row
        for row in grid
        if int(row.get("eligible_count") or 0) >= PROFIT_GRID_MIN_ELIGIBLE
    ]
    if not grid:
        return {
            "status": "unavailable",
            "reason": "no_rows_with_max_and_final_profit",
            "objective": "maximize_fee_aware_expected_net_profit_contribution",
            "selected_min_profit_pct": current_threshold,
            "recommended_next_min_profit_pct": current_threshold,
            "exploratory_selected_min_profit_pct": None,
            "current_min_profit_pct": current_threshold,
            "current_row": current_row,
            "selected_row": None,
        }
    if not current_row_exact:
        return {
            "status": "hold",
            "reason": "current_threshold_outside_profit_grid",
            "objective": "maximize_fee_aware_expected_net_profit_contribution",
            "selected_min_profit_pct": current_threshold,
            "recommended_next_min_profit_pct": current_threshold,
            "candidate_next_min_profit_pct": None,
            "exploratory_selected_min_profit_pct": None,
            "current_min_profit_pct": current_threshold,
            "current_row": None,
            "selected_row": None,
            "candidate_next_row": None,
        }
    if not eligible_rows:
        return {
            "status": "hold",
            "reason": "grid_eligible_rows_lt_20",
            "objective": "maximize_fee_aware_expected_net_profit_contribution",
            "selected_min_profit_pct": current_threshold,
            "recommended_next_min_profit_pct": current_threshold,
            "exploratory_selected_min_profit_pct": None,
            "current_min_profit_pct": current_threshold,
            "current_row": current_row,
            "selected_row": None,
        }
    exploratory_selected = max(
        eligible_rows,
        key=lambda row: (
            float(row.get("equal_weight_expected_net_profit_contribution_pct") or 0.0),
            -float(row.get("loss_or_flat_rate") or 0.0),
            float(row.get("min_profit_pct") or 0.0),
        ),
    )
    current_contribution = (
        float(
            current_row.get("equal_weight_expected_net_profit_contribution_pct") or 0.0
        )
        if current_row
        else 0.0
    )
    exploratory_threshold = float(exploratory_selected["min_profit_pct"])
    if abs(exploratory_threshold - current_threshold) < 0.05:
        recommended_threshold = current_threshold
    else:
        direction = -1.0 if exploratory_threshold < current_threshold else 1.0
        recommended_threshold = round(
            current_threshold + (direction * PROFIT_GRID_RUNTIME_STEP), 1
        )
    candidate_next = _nearest_grid_row(grid, recommended_threshold)
    candidate_next_contribution = (
        float(
            candidate_next.get("equal_weight_expected_net_profit_contribution_pct")
            or 0.0
        )
        if candidate_next
        else current_contribution
    )
    contribution_delta = candidate_next_contribution - current_contribution
    if abs(exploratory_threshold - current_threshold) < 0.05:
        status = "hold"
        reason = "grid_selected_current_threshold"
    elif not candidate_next or int(candidate_next.get("eligible_count") or 0) < (
        PROFIT_GRID_MIN_ELIGIBLE
    ):
        status = "hold"
        reason = "grid_next_step_eligible_rows_lt_20"
    elif contribution_delta <= 0.0:
        status = "hold"
        reason = "grid_next_step_net_contribution_not_improved"
    elif candidate_next_contribution <= 0.0:
        status = "hold"
        reason = "grid_next_step_net_contribution_non_positive"
    elif recommended_threshold < current_threshold:
        status = "adjust_down"
        reason = "grid_loosen_profit_threshold_one_step"
    else:
        status = "adjust_up"
        reason = "grid_tighten_profit_threshold_one_step"
    return {
        "status": status,
        "reason": reason,
        "objective": "maximize_fee_aware_expected_net_profit_contribution",
        "selected_min_profit_pct": (
            recommended_threshold if status != "hold" else current_threshold
        ),
        "recommended_next_min_profit_pct": (
            recommended_threshold if status != "hold" else current_threshold
        ),
        "candidate_next_min_profit_pct": recommended_threshold,
        "exploratory_selected_min_profit_pct": exploratory_threshold,
        "current_min_profit_pct": current_threshold,
        "current_equal_weight_expected_net_profit_contribution_pct": (
            current_contribution
        ),
        "current_source_quality_adjusted_ev_pct": current_contribution,
        "selected_equal_weight_expected_net_profit_contribution_pct": (
            candidate_next_contribution if status != "hold" else current_contribution
        ),
        "candidate_next_equal_weight_expected_net_profit_contribution_pct": (
            candidate_next_contribution
        ),
        "candidate_next_source_quality_adjusted_ev_pct": candidate_next_contribution,
        "source_quality_adjusted_ev_delta_pct": contribution_delta,
        "equal_weight_expected_net_profit_contribution_delta_pct": (contribution_delta),
        "exploratory_selected_equal_weight_expected_net_profit_contribution_pct": (
            float(
                exploratory_selected.get(
                    "equal_weight_expected_net_profit_contribution_pct"
                )
                or 0.0
            )
        ),
        "current_avg_incremental_exit_profit_pct": (
            float(current_row.get("avg_incremental_exit_profit_pct") or 0.0)
            if current_row
            else 0.0
        ),
        "selected_avg_incremental_exit_profit_pct": (
            float(
                (candidate_next if status != "hold" else current_row).get(
                    "avg_incremental_exit_profit_pct"
                )
                or 0.0
            )
        ),
        "current_row": current_row,
        "selected_row": candidate_next if status != "hold" else current_row,
        "candidate_next_row": candidate_next,
        "exploratory_selected_row": exploratory_selected,
        "max_runtime_step_pct": PROFIT_GRID_RUNTIME_STEP,
    }


def _condition_feasibility(
    grid_decision: dict[str, Any],
    *,
    source_blockers: list[str],
    runtime_baseline_blockers: list[str],
    runtime_scope_blockers: list[str] | None = None,
) -> dict[str, Any]:
    """Distinguish missing evidence, economic rejection and a blocked step path."""
    runtime_scope_blockers = runtime_scope_blockers or []
    best = grid_decision.get("exploratory_selected_row") or {}
    best_net = best.get("equal_weight_expected_net_profit_contribution_pct")
    if source_blockers or runtime_baseline_blockers:
        state = "evidence_not_ready"
        action = "resolve_named_source_or_baseline_blockers"
    elif runtime_scope_blockers:
        state = "runtime_scope_not_supported"
        action = "collect_common_axis_krx_parent_evidence"
    elif not best:
        state = "grid_evidence_not_ready"
        action = "repair_profit_observations_or_collect_eligible_samples"
    elif best_net is None or best_net <= 0.0:
        state = "no_economic_candidate"
        action = "reject_current_threshold_only_hypothesis"
    elif grid_decision.get("status") in {"adjust_up", "adjust_down"}:
        state = "bounded_candidate_ready"
        action = "next_preopen_ai_and_owner_review"
    elif grid_decision.get("reason") == "grid_selected_current_threshold":
        state = "current_threshold_best"
        action = "retain_current_threshold"
    else:
        state = "positive_candidate_unreachable_in_one_step"
        action = "review_bounded_path_with_source_only_replay"
    return {
        "state": state,
        "next_action": action,
        "condition_currently_achievable": state == "bounded_candidate_ready",
        "profit_improvement_demonstrated": state == "bounded_candidate_ready",
        "positive_exploratory_candidate_present": bool(
            best_net is not None and best_net > 0
        ),
        "best_exploratory_min_profit_pct": best.get("min_profit_pct"),
        "best_exploratory_net_contribution_pct": best_net,
        "indefinite_wait_appropriate": state
        not in {"no_economic_candidate", "positive_candidate_unreachable_in_one_step"},
        "source_blockers": source_blockers,
        "runtime_baseline_blockers": runtime_baseline_blockers,
        "runtime_scope_blockers": runtime_scope_blockers,
        "reconsideration_trigger": "new_valid_closed_outcomes_or_revised_source_only_hypothesis",
        "future_success_probability": None,
        "probability_status": "not_estimated_from_observational_grid",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_threshold_feasibility_review",
    }


def _calibration_candidate(
    *,
    target_date: str,
    reports: list[dict[str, Any]],
    source_paths: list[Path],
    source_quality_excluded_dates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source_quality_excluded_dates = source_quality_excluded_dates or []
    row_exclusion_counts: Counter[str] = Counter()
    _count_real_scale_in_row_exclusions(reports, row_exclusion_counts)
    one_share_rows, one_share_source_present = _closed_one_share_pyramid_rows(
        reports, row_exclusion_counts
    )
    normal_winner_expansion = _normal_winner_expansion_observation(reports)
    winner_recovery_bounded_canary = normal_winner_expansion[
        "winner_recovery_bounded_canary_observation"
    ]
    winner_recovery_real_execution = _winner_recovery_real_execution_observation(
        reports
    )
    winner_recovery_runtime_funnel = _winner_recovery_runtime_funnel_observation(
        reports
    )
    post_probe_real_outcome = _post_probe_real_outcome_observation(reports)
    post_probe_reprice = _post_probe_reprice_observation(reports)
    threshold_replay_contract_present = any(
        isinstance(report.get("pyramid_threshold_replay_metric_contract"), dict)
        and (report.get("pyramid_threshold_replay_metric_contract") or {}).get(
            "metric_role"
        )
        == "bounded_tunable_threshold_gate_counterfactual"
        for report in reports
    )
    threshold_replay_rows = _threshold_replay_rows(reports)
    rows = (
        one_share_rows
        if one_share_source_present
        else _closed_pyramid_rows(reports, row_exclusion_counts)
    )
    calibration_source_scope = "timestamped_pyramid_gate_fixed_exit_replay"
    rates = _row_rates(rows)
    source_quality_status_counts = Counter(
        str((report.get("source_quality") or {}).get("status") or "missing")
        for report in reports
    )
    unisolatable_source_quality_statuses = sorted(
        status
        for status in source_quality_status_counts
        if status not in ROW_ISOLATABLE_SOURCE_QUALITY_STATUSES
    )
    source_quality_pass = bool(reports) and not unisolatable_source_quality_statuses
    if not source_quality_pass:
        for observation in (
            winner_recovery_bounded_canary,
            winner_recovery_real_execution,
        ):
            if observation.get("operator_action_required") or str(
                observation.get("state") or ""
            ) in {
                "bounded_one_share_canary_evidence_ready",
                "venue_conflict_requires_independent_decision",
                "first_planned_residual_leg_candidate_ready",
            }:
                observation["evidence_state_before_source_quality_gate"] = (
                    observation.get("state")
                )
                observation["state"] = "source_quality_blocked"
                observation["operator_action_required"] = False
                observation["source_quality_blocked_reason"] = (
                    "input_report_source_quality_not_row_isolatable"
                )
    legacy_provenance_present = _provenance_present(rows)
    provenance_present = _provenance_present(threshold_replay_rows)
    source_contract_pass = bool(
        source_quality_pass and (provenance_present or legacy_provenance_present)
    )
    current_resolution = _resolve_current_values(target_date, reports)
    current = dict(current_resolution["values"])
    legacy_proxy_profit_grid = _profit_threshold_grid(rows)
    threshold_replay_grid = _pyramid_threshold_replay_grid(
        threshold_replay_rows, float(current["min_profit_pct"])
    )
    grid_decision = _profit_grid_decision(current, threshold_replay_grid)
    replay_episode_count = max(
        (int(row.get("source_episode_count") or 0) for row in threshold_replay_grid),
        default=0,
    )
    replay_ready_episode_count = max(
        (
            int(row.get("comparable_episode_count") or 0)
            for row in threshold_replay_grid
        ),
        default=0,
    )
    replay_eligible_count = max(
        (int(row.get("eligible_count") or 0) for row in threshold_replay_grid),
        default=0,
    )
    decision_grid_row = (
        grid_decision.get("candidate_next_row")
        or grid_decision.get("current_row")
        or {}
    )
    decision_eligible_count = int(decision_grid_row.get("eligible_count") or 0)
    comparison_venue_counts = next(
        (
            dict(row.get("comparison_effective_venue_counts") or {})
            for row in threshold_replay_grid
            if int(row.get("comparable_episode_count") or 0) > 0
        ),
        {},
    )
    source_blockers: list[str] = []
    if not threshold_replay_contract_present:
        source_blockers.append("pyramid_threshold_replay_contract_missing")
    elif not threshold_replay_rows:
        source_blockers.append("pyramid_threshold_replay_rows_missing")
    elif replay_ready_episode_count <= 0:
        source_blockers.append("threshold_replay_no_comparable_episodes")
    elif replay_eligible_count < PROFIT_GRID_MIN_ELIGIBLE:
        source_blockers.append("rolling_replay_eligible_episodes_lt_20")
    if not source_quality_pass:
        source_blockers.append("source_quality_not_pass")
    if not provenance_present:
        source_blockers.append("threshold_replay_provenance_missing")
    decision_evidence_blockers = [
        blocker
        for blocker in source_blockers
        if blocker != "rolling_replay_eligible_episodes_lt_20"
    ]
    sample_blockers = [
        blocker
        for blocker in source_blockers
        if blocker == "rolling_replay_eligible_episodes_lt_20"
    ]
    runtime_scope_blockers: list[str] = []
    if (
        replay_ready_episode_count > 0
        and int(comparison_venue_counts.get("KRX") or 0) <= 0
    ):
        runtime_scope_blockers.append("common_runtime_axis_krx_evidence_missing")
    runtime_baseline_blockers = list(current_resolution.get("blockers") or [])

    opportunity_costs = [
        _safe_float(row.get("pyramid_opportunity_cost_pct"), 0.0)
        for row in rows
        if row.get("pyramid_opportunity_cost_pct") is not None
    ]
    source_dates = sorted(
        {
            _date_from_feedback_path(path)
            for path in source_paths
            if _date_from_feedback_path(path)
        }
    )
    cumulative_quality_window = {
        "window_policy": "clean_baseline_cumulative",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "start_date": CLEAN_BASELINE_DATE,
        "end_date": target_date,
        "source_dates": source_dates,
        "source_date_count": len(source_dates),
        "source_quality_excluded_date_count": len(source_quality_excluded_dates),
        "source_quality_excluded_dates": source_quality_excluded_dates,
    }
    normal_winner_loosen_veto_applied = False
    if runtime_baseline_blockers:
        state = "hold_runtime_baseline"
        recommended = dict(current)
        reason = ",".join(runtime_baseline_blockers)
        allowed = False
    elif decision_evidence_blockers:
        state = "source_quality_blocked"
        recommended = dict(current)
        reason = ",".join(decision_evidence_blockers)
        allowed = False
    elif sample_blockers:
        state = "hold_sample"
        recommended = dict(current)
        reason = ",".join(sample_blockers)
        allowed = False
    elif runtime_scope_blockers:
        state = "hold_runtime_scope"
        recommended = dict(current)
        reason = ",".join(runtime_scope_blockers)
        allowed = False
    else:
        recommended = dict(current)
        grid_status = str(grid_decision.get("status") or "")
        reason = str(grid_decision.get("reason") or "grid_evidence_missing")
        if grid_status in {"adjust_up", "adjust_down"}:
            state = grid_status
            recommended["min_profit_pct"] = float(
                grid_decision["selected_min_profit_pct"]
            )
        else:
            state = "hold"
        allowed = state in {"adjust_up", "adjust_down"}

    feasibility = _condition_feasibility(
        grid_decision,
        source_blockers=source_blockers,
        runtime_baseline_blockers=runtime_baseline_blockers,
        runtime_scope_blockers=runtime_scope_blockers,
    )

    evidence_digest = hashlib.sha256(
        json.dumps(
            {
                "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
                "target_date": target_date,
                "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
                "source_dates": source_dates,
                "current_min_profit_pct": current["min_profit_pct"],
                "recommended_min_profit_pct": recommended["min_profit_pct"],
                "threshold_replay_grid": threshold_replay_grid,
                "source_quality_excluded_dates": source_quality_excluded_dates,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    quality_update_id = (
        f"{FAMILY}:cumulative:{CLEAN_BASELINE_DATE}:{target_date}:"
        f"{recommended.get('min_profit_pct', current['min_profit_pct'])}:"
        f"{evidence_digest[:16]}"
    )

    return {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 39,
        "family_type": "bounded_tunable_scalping_pyramid_quality_gate",
        "calibration_state": state,
        "calibration_reason": reason,
        "threshold_version": f"{FAMILY}:{target_date}:v2",
        "quality_update_id": quality_update_id,
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "evidence_digest": evidence_digest,
        "runtime_update_mode": RUNTIME_UPDATE_MODE,
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": cumulative_quality_window,
        "post_apply_attribution_required": True,
        "sample_count": rates["sample_count"],
        "source_sample_count": replay_eligible_count,
        "decision_sample_count": decision_eligible_count,
        "decision_universe_count": replay_ready_episode_count,
        "sample_floor": 20,
        "allowed_runtime_apply": allowed,
        "safety_revert_required": False,
        "source_quality_gate": (
            ("pass_with_row_exclusions" if row_exclusion_counts else "pass")
            if source_contract_pass and not decision_evidence_blockers
            else "source_quality_blocked"
        ),
        "source_quality_status": (
            ("pass_with_row_exclusions" if row_exclusion_counts else "pass")
            if source_contract_pass and not decision_evidence_blockers
            else "blocked"
        ),
        "source_quality_blocked": (
            None
            if source_contract_pass and not decision_evidence_blockers
            else ",".join(decision_evidence_blockers)
            or "source_quality_or_provenance_not_pass"
        ),
        "input_source_quality_status": (
            (
                "pass_with_row_exclusions"
                if row_exclusion_counts and rates["sample_count"] > 0
                else "blocked" if row_exclusion_counts else "pass"
            )
            if source_quality_pass
            else "blocked"
        ),
        "decision_evidence_gate": ("blocked" if decision_evidence_blockers else "pass"),
        "decision_evidence_blockers": decision_evidence_blockers,
        "runtime_baseline_gate": current_resolution.get("status"),
        "runtime_baseline_blockers": runtime_baseline_blockers,
        "runtime_scope_gate": "blocked" if runtime_scope_blockers else "pass",
        "runtime_scope_blockers": runtime_scope_blockers,
        "current_value_provenance": current_resolution,
        "condition_feasibility": feasibility,
        "current_values": current,
        "recommended_values": recommended,
        "current_value": current["min_profit_pct"],
        "recommended_value": recommended["min_profit_pct"],
        "bounds": {"min": PROFIT_GRID_MIN, "max": PROFIT_GRID_MAX},
        "max_step_per_day": PROFIT_GRID_RUNTIME_STEP,
        "target_env_keys": TARGET_ENV_KEYS if allowed else [],
        "source_metrics": {
            "condition_feasibility": feasibility,
            **rates,
            "calibration_source_scope": calibration_source_scope,
            "threshold_replay_contract_present": threshold_replay_contract_present,
            "threshold_replay_row_count": len(threshold_replay_rows),
            "threshold_replay_episode_count": replay_episode_count,
            "threshold_replay_ready_episode_count": replay_ready_episode_count,
            "threshold_replay_eligible_episode_count": replay_eligible_count,
            "threshold_replay_decision_eligible_episode_count": (
                decision_eligible_count
            ),
            "threshold_replay_comparison_effective_venue_counts": (
                comparison_venue_counts
            ),
            "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
            "evidence_digest": evidence_digest,
            "one_share_event_source_present": one_share_source_present,
            "one_share_closed_pyramid_row_count": len(one_share_rows),
            "one_share_pyramid_avg_opportunity_cost_pct": (
                sum(opportunity_costs) / len(opportunity_costs)
                if opportunity_costs
                else 0.0
            ),
            "profit_threshold_grid": threshold_replay_grid,
            "profit_threshold_grid_decision": grid_decision,
            "legacy_peak_threshold_proxy_grid": legacy_proxy_profit_grid,
            "legacy_peak_threshold_proxy_role": (
                "diagnostic_only_no_runtime_candidate_authority"
            ),
            "source_quality_pass": source_quality_pass,
            "source_quality_status_counts": dict(source_quality_status_counts),
            "unisolatable_source_quality_statuses": (
                unisolatable_source_quality_statuses
            ),
            "source_quality_excluded_row_count": sum(row_exclusion_counts.values()),
            "source_quality_exclusion_reasons": dict(row_exclusion_counts),
            "provenance_present": provenance_present,
            "legacy_feedback_provenance_present": legacy_provenance_present,
            "recommended_action": state,
            "recommended_action_reason": reason,
            "normal_winner_expansion_observation": normal_winner_expansion,
            "normal_winner_expansion_loosen_veto_applied": (
                normal_winner_loosen_veto_applied
            ),
            "normal_winner_expansion_role": "diagnostic_different_entry_anchor_not_threshold_candidate_veto",
            "label_cluster_role": "diagnostic_only_no_quality_env_authority",
            "winner_recovery_bounded_canary_observation": (
                winner_recovery_bounded_canary
            ),
            "winner_recovery_real_execution_observation": (
                winner_recovery_real_execution
            ),
            "winner_recovery_runtime_funnel_observation": (
                winner_recovery_runtime_funnel
            ),
            "post_probe_real_outcome_observation": post_probe_real_outcome,
            "post_probe_reprice_observation": post_probe_reprice,
        },
        "source_reports": [str(path) for path in source_paths],
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_report(
    target_date: str,
    *,
    input_paths: list[Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    intended_paths = (
        input_paths
        if input_paths is not None
        else _iter_feedback_report_paths(target_date)
    )
    intended_dates = [
        date_part
        for path in intended_paths
        if (date_part := _date_from_feedback_path(path))
    ]
    allowed_dates, source_quality_excluded_dates = filter_source_dates_by_preflight(
        intended_dates,
        preflight_loader=load_source_quality_preflight,
    )
    allowed_date_set = set(allowed_dates)
    paths = [
        path
        for path in intended_paths
        if _date_from_feedback_path(path) in allowed_date_set
    ]
    reports = [_load_json(path) for path in paths if path.exists()]
    candidate = _calibration_candidate(
        target_date=target_date,
        reports=reports,
        source_paths=paths,
        source_quality_excluded_dates=source_quality_excluded_dates,
    )
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "family": FAMILY,
        "stage": STAGE,
        "runtime_effect": False,
        "allowed_runtime_apply": bool(candidate.get("allowed_runtime_apply")),
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "bounded_tunable_calibration_candidate",
            "decision_authority": "postclose_calibration_candidate_preopen_only",
            "window_policy": (
                "rolling_clean_baseline_timestamped_pyramid_gate_parent_episodes"
            ),
            "sample_floor": "rolling_replay_eligible_parent_episodes_ge_20",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": (
                "row_isolatable_provenance_gaps_excluded_then_timestamped_gate_"
                "context_conflict_free_owner_fresh_same_route_bbo_existing_price_"
                "resolver_observation_later_terminal_sell_and_same_day_current_"
                "min_profit_or_pid_verified_"
                "exact_date_runtime_provenance"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "condition_feasibility": candidate["condition_feasibility"],
        "condition_feasibility_metric_contract": {
            "metric_role": "threshold_candidate_feasibility_diagnostic",
            "decision_authority": "source_only_threshold_feasibility_review",
            "window_policy": (
                "rolling_clean_baseline_timestamped_fixed_exit_gate_replay"
            ),
            "sample_floor": PROFIT_GRID_MIN_ELIGIBLE,
            "primary_decision_metric": (
                "positive_source_quality_adjusted_ev_and_bounded_step_reachability"
            ),
            "source_quality_gate": "same_as_calibration_candidate",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "normal_winner_expansion_observation": (
            candidate["source_metrics"]["normal_winner_expansion_observation"]
        ),
        "winner_recovery_bounded_canary_observation": (
            candidate["source_metrics"]["winner_recovery_bounded_canary_observation"]
        ),
        "winner_recovery_real_execution_observation": (
            candidate["source_metrics"]["winner_recovery_real_execution_observation"]
        ),
        "winner_recovery_runtime_funnel_observation": (
            candidate["source_metrics"]["winner_recovery_runtime_funnel_observation"]
        ),
        "post_probe_real_outcome_observation": (
            candidate["source_metrics"]["post_probe_real_outcome_observation"]
        ),
        "post_probe_reprice_observation": (
            candidate["source_metrics"]["post_probe_reprice_observation"]
        ),
        "source_quality": {
            "status": candidate.get("input_source_quality_status"),
            "decision_evidence_status": candidate.get("source_quality_status"),
            "decision_evidence_gate": candidate.get("decision_evidence_gate"),
            "decision_evidence_blockers": candidate.get("decision_evidence_blockers"),
            "input_report_count": len(reports),
            "intended_input_report_count": len(intended_paths),
            "input_paths": [str(path) for path in paths],
            "source_quality_excluded_dates": source_quality_excluded_dates,
            "provenance_present": candidate["source_metrics"]["provenance_present"],
            "excluded_row_count": candidate["source_metrics"].get(
                "source_quality_excluded_row_count", 0
            ),
            "exclusion_reasons": candidate["source_metrics"].get(
                "source_quality_exclusion_reasons", {}
            ),
        },
        "runtime_update_contract": {
            "update_mode": RUNTIME_UPDATE_MODE,
            "owner_family": FAMILY,
            "owner_stage": STAGE,
            "max_runtime_apply_count": 1,
            "runtime_apply_candidate_count": 1,
            "allowed_runtime_apply_count": int(
                bool(candidate.get("allowed_runtime_apply"))
            ),
            "quality_update_id": candidate.get("quality_update_id"),
            "evidence_contract_version": candidate.get("evidence_contract_version"),
            "evidence_digest": candidate.get("evidence_digest"),
            "cumulative_quality_window": candidate.get("cumulative_quality_window"),
            "post_apply_attribution_required": True,
            "runtime_effect": False,
        },
        "calibration_candidates": [candidate],
    }


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    candidate = (report.get("calibration_candidates") or [{}])[0]
    metrics = (
        candidate.get("source_metrics")
        if isinstance(candidate.get("source_metrics"), dict)
        else {}
    )
    winner_recovery_runtime_funnel = (
        report.get("winner_recovery_runtime_funnel_observation")
        if isinstance(report.get("winner_recovery_runtime_funnel_observation"), dict)
        else {}
    )
    grid_decision = (
        metrics.get("profit_threshold_grid_decision")
        if isinstance(metrics.get("profit_threshold_grid_decision"), dict)
        else {}
    )
    selected_grid_row = (
        grid_decision.get("selected_row")
        if isinstance(grid_decision.get("selected_row"), dict)
        else {}
    )
    post_probe_observation = (
        report.get("post_probe_real_outcome_observation")
        if isinstance(report.get("post_probe_real_outcome_observation"), dict)
        else {}
    )
    winner_recovery_bounded_canary = (
        report.get("winner_recovery_bounded_canary_observation")
        if isinstance(report.get("winner_recovery_bounded_canary_observation"), dict)
        else {}
    )
    winner_recovery_real_execution = (
        report.get("winner_recovery_real_execution_observation")
        if isinstance(report.get("winner_recovery_real_execution_observation"), dict)
        else {}
    )
    normal_winner_expansion = (
        report.get("normal_winner_expansion_observation")
        if isinstance(report.get("normal_winner_expansion_observation"), dict)
        else {}
    )
    source_quality = (
        report.get("source_quality")
        if isinstance(report.get("source_quality"), dict)
        else {}
    )
    lines = [
        f"# {report.get('target_date')} Scalping Pyramid Quality Calibration",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- family: {FAMILY}",
        f"- stage: {STAGE}",
        f"- calibration_state: {candidate.get('calibration_state')}",
        f"- calibration_reason: {candidate.get('calibration_reason')}",
        "- condition_feasibility: "
        + json.dumps(
            candidate.get("condition_feasibility") or {},
            ensure_ascii=False,
            sort_keys=True,
        ),
        f"- allowed_runtime_apply: {str(candidate.get('allowed_runtime_apply')).lower()}",
        f"- runtime_baseline_gate: {candidate.get('runtime_baseline_gate')}",
        "- current_min_profit_pct: "
        f"{(candidate.get('current_values') or {}).get('min_profit_pct')}",
        "- current_min_profit_source: "
        f"{((candidate.get('current_value_provenance') or {}).get('field_sources') or {}).get('min_profit_pct')}",
        "- source_quality_excluded_dates: "
        + json.dumps(
            source_quality.get("source_quality_excluded_dates") or [],
            ensure_ascii=False,
            sort_keys=True,
        ),
        "- runtime_effect: false",
        "- decision_authority: postclose_calibration_candidate_preopen_only",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        "",
        "## Metrics",
        "",
        f"- calibration_source_scope: {metrics.get('calibration_source_scope')}",
        f"- one_share_event_source_present: {metrics.get('one_share_event_source_present')}",
        f"- one_share_closed_pyramid_row_count: {metrics.get('one_share_closed_pyramid_row_count')}",
        f"- sample_count: {metrics.get('sample_count')}",
        f"- recovered_or_extended_rate: {_safe_float(metrics.get('recovered_or_extended_rate')):.2f}",
        f"- reversal_or_flat_rate: {_safe_float(metrics.get('reversal_or_flat_rate')):.2f}",
        f"- correctly_blocked_rate: {_safe_float(metrics.get('correctly_blocked_rate')):.2f}",
        "- one_share_pyramid_avg_opportunity_cost_pct: "
        f"{_safe_float(metrics.get('one_share_pyramid_avg_opportunity_cost_pct')):.2f}",
        f"- profit_threshold_grid_status: {grid_decision.get('status')}",
        f"- profit_threshold_grid_reason: {grid_decision.get('reason')}",
        f"- profit_threshold_grid_objective: {grid_decision.get('objective')}",
        "- profit_threshold_grid_exploratory_selected_min_profit_pct: "
        f"{grid_decision.get('exploratory_selected_min_profit_pct')}",
        f"- profit_threshold_grid_selected_min_profit_pct: {grid_decision.get('selected_min_profit_pct')}",
        "- profit_threshold_grid_selected_avg_incremental_exit_profit_pct: "
        f"{_safe_float(selected_grid_row.get('avg_incremental_exit_profit_pct')):.2f}",
        "- profit_threshold_grid_selected_expected_net_profit_contribution_pct: "
        f"{_safe_float(selected_grid_row.get('equal_weight_expected_net_profit_contribution_pct')):.4f}",
        f"- source_quality_pass: {metrics.get('source_quality_pass')}",
        "- source_quality_excluded_row_count: "
        f"{metrics.get('source_quality_excluded_row_count')}",
        f"- provenance_present: {metrics.get('provenance_present')}",
        f"- normal_winner_expansion_state: {normal_winner_expansion.get('state')}",
        "- normal_winner_expansion_sample_count: "
        f"{normal_winner_expansion.get('sample_count')}",
        "- normal_winner_expansion_ev_eligible_sample_count: "
        f"{normal_winner_expansion.get('ev_eligible_sample_count')}",
        "- normal_winner_expansion_notional_weighted_ev_pct: "
        f"{_safe_float(normal_winner_expansion.get('notional_weighted_ev_pct')):.4f}",
        "- normal_winner_expansion_loosen_veto_applied: "
        f"{metrics.get('normal_winner_expansion_loosen_veto_applied')}",
        f"- post_probe_real_outcome_state: {post_probe_observation.get('state')}",
        "- post_probe_real_outcome_closed_count: "
        f"{post_probe_observation.get('closed_real_outcome_count')}",
        "- post_probe_confirmation_ready_count: "
        f"{post_probe_observation.get('confirmation_ready_count')}",
        "- post_probe_confirmation_ready_winner_count: "
        f"{post_probe_observation.get('confirmation_ready_winner_count')}",
        "- post_probe_confirmation_ready_loss_or_flat_count: "
        f"{post_probe_observation.get('confirmation_ready_loss_or_flat_count')}",
        "- post_probe_confirmation_ready_notional_weighted_ev_pct: "
        f"{_safe_float(post_probe_observation.get('notional_weighted_ev_pct')):.4f}",
        "- winner_recovery_bounded_canary_state: "
        f"{winner_recovery_bounded_canary.get('state')}",
        "- winner_recovery_bounded_canary_exact_blocker_sample_count: "
        f"{winner_recovery_bounded_canary.get('sample_count')}",
        "- winner_recovery_real_execution_state: "
        f"{winner_recovery_real_execution.get('state')}",
        "- winner_recovery_real_source_quality_valid_closed_count: "
        f"{winner_recovery_real_execution.get('source_quality_valid_closed_count')}",
        "- winner_recovery_real_source_quality_adjusted_ev_pct: "
        f"{_safe_float(winner_recovery_real_execution.get('source_quality_adjusted_ev_pct')):.4f}",
        "- winner_recovery_recommended_next_qty_stage: "
        f"{winner_recovery_real_execution.get('recommended_next_qty_stage')}",
        "- winner_recovery_runtime_funnel_state: "
        f"{winner_recovery_runtime_funnel.get('state')}",
        "- winner_recovery_runtime_selected_count: "
        f"{winner_recovery_runtime_funnel.get('runtime_gate_selected_count')}",
        "- winner_recovery_downstream_guard_blocked_count: "
        f"{winner_recovery_runtime_funnel.get('selected_downstream_guard_blocked_count')}",
        "- winner_recovery_order_submitted_count: "
        f"{winner_recovery_runtime_funnel.get('selected_order_submitted_count')}",
        "- winner_recovery_executed_count: "
        f"{winner_recovery_runtime_funnel.get('selected_executed_count')}",
        "- winner_recovery_dominant_non_execution_layer: "
        f"{winner_recovery_runtime_funnel.get('dominant_non_execution_layer')}",
    ]
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scalping PYRAMID quality calibration candidate."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    output_json, output_md = (
        (args.output_json, args.output_md)
        if args.output_json and args.output_md
        else _default_output_paths(args.target_date)
    )
    report = build_report(args.target_date)
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                report.get("calibration_candidates", [{}])[0],
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
