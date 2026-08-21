from __future__ import annotations

import argparse
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
from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))
FAMILY = "scalping_pyramid_quality_gate"
STAGE = "scale_in"
REPORT_TYPE = "scalping_pyramid_quality_calibration"
INPUT_REPORT_DIR = DATA_DIR / "report" / "scalping_pyramid_intraday_feedback"
OUTPUT_REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
CLEAN_BASELINE_DATE = "2026-06-05"
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
    "SCALPING_PYRAMID_MIN_AI_SCORE",
    "SCALPING_PYRAMID_MIN_BUY_PRESSURE",
    "SCALPING_PYRAMID_MIN_TICK_ACCEL",
    "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS",
    "SCALPING_PYRAMID_MAX_SPREAD_BPS",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT",
]
PROFIT_GRID_MIN = 0.8
PROFIT_GRID_MAX = 2.5
PROFIT_GRID_STEP = 0.1
PROFIT_GRID_MIN_ELIGIBLE = 20
PROFIT_GRID_MIN_EV_DELTA = 0.2
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
            else "non_positive_ev_hold"
            if non_positive_ready
            else "hold_sample"
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
        if not isinstance(report.get("real_scale_in_performance_metric_contract"), dict):
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

    valid_notional = sum(
        _safe_float(row.get("fill_notional_krw"), 0.0) for row in rows
    )
    valid_net_pnl = sum(
        _safe_float(row.get("scale_in_leg_net_pnl_proxy_krw"), 0.0) for row in rows
    )
    source_quality_adjusted_ev_pct = (
        round(valid_net_pnl / valid_notional * 100.0, 4)
        if valid_notional > 0
        else None
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
        else "observe_one_share_canary"
        if not sample_floor_met
        else "first_planned_residual_leg_candidate_ready"
        if positive_ev
        else "non_positive_ev_hold"
    )

    def _dimension_rollup(dimension: str) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(dimension) or "UNKNOWN")].append(row)
        result = []
        for value, bucket_rows in sorted(grouped.items()):
            bucket_notional = sum(
                _safe_float(row.get("fill_notional_krw"), 0.0)
                for row in bucket_rows
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
                    if _safe_float(
                        row.get("scale_in_leg_net_pnl_proxy_krw"), 0.0
                    )
                    > 0
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
            return _safe_float(row.get(key), 0.0)
    return None


def _final_profit(row: dict[str, Any]) -> float | None:
    if row.get("final_profit_rate") is not None:
        return _safe_float(row.get("final_profit_rate"), 0.0)
    return None


def _profit_threshold_grid(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    usable_rows = [
        (float(reached), float(final), row)
        for row in rows
        if (reached := _profit_reached(row)) is not None
        and (final := _final_profit(row)) is not None
    ]
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
        positive_exit_count = sum(1 for _, final, _ in eligible if final > threshold)
        loss_or_flat_count = eligible_count - positive_exit_count
        incremental = [final - threshold for _, final, _ in eligible]
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
                "avg_incremental_exit_profit_pct": (
                    sum(incremental) / len(incremental) if incremental else 0.0
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
    eligible_rows = [
        row
        for row in grid
        if int(row.get("eligible_count") or 0) >= PROFIT_GRID_MIN_ELIGIBLE
    ]
    if not grid:
        return {
            "status": "unavailable",
            "reason": "no_rows_with_max_and_final_profit",
            "selected_min_profit_pct": current_threshold,
            "current_row": current_row,
            "selected_row": None,
        }
    if not eligible_rows:
        return {
            "status": "hold",
            "reason": "grid_eligible_rows_lt_20",
            "selected_min_profit_pct": current_threshold,
            "current_row": current_row,
            "selected_row": None,
        }
    selected = max(
        eligible_rows,
        key=lambda row: (
            float(row.get("avg_incremental_exit_profit_pct") or 0.0),
            -float(row.get("loss_or_flat_rate") or 0.0),
            float(row.get("min_profit_pct") or 0.0),
        ),
    )
    current_ev = (
        float(current_row.get("avg_incremental_exit_profit_pct") or 0.0)
        if current_row
        else 0.0
    )
    selected_ev = float(selected.get("avg_incremental_exit_profit_pct") or 0.0)
    selected_threshold = float(selected["min_profit_pct"])
    ev_delta = selected_ev - current_ev
    if abs(selected_threshold - current_threshold) < 0.05:
        status = "hold"
        reason = "grid_selected_current_threshold"
    elif ev_delta < PROFIT_GRID_MIN_EV_DELTA:
        status = "hold"
        reason = "grid_ev_delta_lt_0_20"
    elif selected_threshold < current_threshold:
        status = "adjust_down"
        reason = "grid_loosen_profit_threshold_direct"
    else:
        status = "adjust_up"
        reason = "grid_tighten_profit_threshold_direct"
    return {
        "status": status,
        "reason": reason,
        "selected_min_profit_pct": selected_threshold,
        "current_min_profit_pct": current_threshold,
        "current_avg_incremental_exit_profit_pct": current_ev,
        "selected_avg_incremental_exit_profit_pct": selected_ev,
        "avg_incremental_exit_profit_delta_pct": ev_delta,
        "current_row": current_row,
        "selected_row": selected,
    }


def _one_step_candidate_values(
    current: dict[str, Any], rates: dict[str, Any]
) -> tuple[str, dict[str, Any], str]:
    recommended = dict(current)
    recovery_rate = _safe_float(rates.get("recovered_or_extended_rate"))
    reversal_rate = _safe_float(rates.get("reversal_or_flat_rate"))
    if reversal_rate >= 0.60:
        recommended["min_profit_pct"] = min(float(current["min_profit_pct"]) + 0.2, 3.0)
        recommended["min_ai_score"] = min(float(current["min_ai_score"]) + 5.0, 85.0)
        recommended["min_buy_pressure"] = min(
            float(current["min_buy_pressure"]) + 5.0, 80.0
        )
        recommended["min_tick_accel"] = min(float(current["min_tick_accel"]) + 0.1, 1.5)
        recommended["max_micro_vwap_bps"] = max(
            float(current["max_micro_vwap_bps"]) - 10.0, 30.0
        )
        recommended["max_spread_bps"] = max(
            float(current["max_spread_bps"]) - 10.0, 40.0
        )
        if _boolish(current.get("strong_continuation_enabled")):
            recommended["strong_continuation_enabled"] = False
        return "adjust_up", recommended, "reversal_cluster_tighten_one_step"
    if recovery_rate >= 0.60:
        recommended["min_profit_pct"] = max(float(current["min_profit_pct"]) - 0.2, 0.8)
        recommended["min_ai_score"] = max(float(current["min_ai_score"]) - 5.0, 60.0)
        recommended["min_buy_pressure"] = max(
            float(current["min_buy_pressure"]) - 5.0, 45.0
        )
        recommended["min_tick_accel"] = max(float(current["min_tick_accel"]) - 0.1, 0.2)
        recommended["max_micro_vwap_bps"] = min(
            float(current["max_micro_vwap_bps"]) + 10.0, 100.0
        )
        recommended["max_spread_bps"] = min(
            float(current["max_spread_bps"]) + 10.0, 120.0
        )
        if not _boolish(current.get("strong_continuation_enabled")):
            recommended["strong_continuation_enabled"] = True
        return "adjust_down", recommended, "recovery_cluster_loosen_one_step"
    return "hold", recommended, "mixed_cluster_hold"


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
    winner_recovery_real_execution = (
        _winner_recovery_real_execution_observation(reports)
    )
    post_probe_real_outcome = _post_probe_real_outcome_observation(reports)
    post_probe_reprice = _post_probe_reprice_observation(reports)
    rows = (
        one_share_rows
        if one_share_source_present
        else _closed_pyramid_rows(reports, row_exclusion_counts)
    )
    calibration_source_scope = (
        "one_share_event_opportunity"
        if one_share_source_present
        else "legacy_pyramid_feedback_rows"
    )
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
    provenance_present = _provenance_present(rows)
    source_contract_pass = bool(source_quality_pass and provenance_present)
    sample_floor_met = int(rates["sample_count"]) >= 20
    sample_floor_reason = (
        "rolling_closed_one_share_pyramid_rows_lt_20"
        if one_share_source_present
        else "rolling_closed_pyramid_rows_lt_20"
    )
    current = _current_values()
    profit_grid = _profit_threshold_grid(rows)
    grid_decision = _profit_grid_decision(current, profit_grid)
    blockers: list[str] = []
    if not sample_floor_met:
        blockers.append(sample_floor_reason)
    if not source_quality_pass:
        blockers.append("source_quality_not_pass")
    if not provenance_present:
        blockers.append("order_provenance_missing")

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
    if blockers:
        state = "hold_sample"
        recommended = dict(current)
        reason = ",".join(blockers)
        allowed = False
    else:
        state, recommended, reason = _one_step_candidate_values(current, rates)
        grid_status = str(grid_decision.get("status") or "")
        if grid_status in {"adjust_up", "adjust_down"}:
            if state in {"adjust_up", "adjust_down"} and state != grid_status:
                state = "hold"
                recommended = dict(current)
                reason = (
                    f"cluster_grid_conflict_hold:{reason},{grid_decision.get('reason')}"
                )
            else:
                state = grid_status
                recommended = dict(
                    recommended if reason != "mixed_cluster_hold" else current
                )
                recommended["min_profit_pct"] = float(
                    grid_decision["selected_min_profit_pct"]
                )
                reason = str(grid_decision.get("reason") or reason)
        normal_winner_loosen_veto_applied = bool(
            state == "adjust_down"
            and normal_winner_expansion.get("sample_floor_met")
            and _safe_float(
                normal_winner_expansion.get("notional_weighted_ev_pct"), 0.0
            )
            <= 0.0
        )
        if normal_winner_loosen_veto_applied:
            prior_reason = reason
            state = "hold"
            recommended = dict(current)
            reason = (
                "normal_winner_expansion_non_positive_ev_hold:"
                f"{prior_reason}"
            )
        allowed = state in {"adjust_up", "adjust_down"}

    if blockers:
        normal_winner_loosen_veto_applied = False

    quality_update_id = (
        f"{FAMILY}:cumulative:{CLEAN_BASELINE_DATE}:{target_date}:"
        f"{recommended.get('min_profit_pct', current['min_profit_pct'])}"
    )

    return {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 39,
        "family_type": "bounded_tunable_scalping_pyramid_quality_gate",
        "calibration_state": state,
        "calibration_reason": reason,
        "threshold_version": f"{FAMILY}:{target_date}:v1",
        "quality_update_id": quality_update_id,
        "runtime_update_mode": RUNTIME_UPDATE_MODE,
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": cumulative_quality_window,
        "post_apply_attribution_required": True,
        "sample_count": rates["sample_count"],
        "sample_floor": 20,
        "allowed_runtime_apply": allowed,
        "safety_revert_required": False,
        "source_quality_gate": (
            ("pass_with_row_exclusions" if row_exclusion_counts else "pass")
            if source_contract_pass
            else "source_quality_blocked"
        ),
        "source_quality_status": (
            ("pass_with_row_exclusions" if row_exclusion_counts else "pass")
            if source_contract_pass
            else "blocked"
        ),
        "source_quality_blocked": (
            None
            if source_contract_pass
            else ",".join(blockers) or "source_quality_or_provenance_not_pass"
        ),
        "current_values": current,
        "recommended_values": recommended,
        "target_env_keys": TARGET_ENV_KEYS if allowed else [],
        "source_metrics": {
            **rates,
            "calibration_source_scope": calibration_source_scope,
            "one_share_event_source_present": one_share_source_present,
            "one_share_closed_pyramid_row_count": len(one_share_rows),
            "one_share_pyramid_avg_opportunity_cost_pct": (
                sum(opportunity_costs) / len(opportunity_costs)
                if opportunity_costs
                else 0.0
            ),
            "profit_threshold_grid": profit_grid,
            "profit_threshold_grid_decision": grid_decision,
            "source_quality_pass": source_quality_pass,
            "source_quality_status_counts": dict(source_quality_status_counts),
            "unisolatable_source_quality_statuses": (
                unisolatable_source_quality_statuses
            ),
            "source_quality_excluded_row_count": sum(row_exclusion_counts.values()),
            "source_quality_exclusion_reasons": dict(row_exclusion_counts),
            "provenance_present": provenance_present,
            "recommended_action": state,
            "recommended_action_reason": reason,
            "normal_winner_expansion_observation": normal_winner_expansion,
            "normal_winner_expansion_loosen_veto_applied": (
                normal_winner_loosen_veto_applied
            ),
            "winner_recovery_bounded_canary_observation": (
                winner_recovery_bounded_canary
            ),
            "winner_recovery_real_execution_observation": (
                winner_recovery_real_execution
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
            "window_policy": "rolling_clean_baseline_one_share_pyramid_opportunity_rows_when_present",
            "sample_floor": "rolling_closed_one_share_pyramid_rows_ge_20",
            "primary_decision_metric": (
                "one_share_pyramid_recovered_or_extended_rate_reversal_or_flat_rate_and_opportunity_cost"
            ),
            "source_quality_gate": (
                "row_isolatable_provenance_gaps_excluded_then_remaining_rows_"
                "must_have_complete_order_provenance"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "normal_winner_expansion_observation": (
            candidate["source_metrics"]["normal_winner_expansion_observation"]
        ),
        "winner_recovery_bounded_canary_observation": (
            candidate["source_metrics"][
                "winner_recovery_bounded_canary_observation"
            ]
        ),
        "winner_recovery_real_execution_observation": (
            candidate["source_metrics"][
                "winner_recovery_real_execution_observation"
            ]
        ),
        "post_probe_real_outcome_observation": (
            candidate["source_metrics"]["post_probe_real_outcome_observation"]
        ),
        "post_probe_reprice_observation": (
            candidate["source_metrics"]["post_probe_reprice_observation"]
        ),
        "source_quality": {
            "status": candidate.get("source_quality_status"),
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
        f"- allowed_runtime_apply: {str(candidate.get('allowed_runtime_apply')).lower()}",
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
        f"- profit_threshold_grid_selected_min_profit_pct: {grid_decision.get('selected_min_profit_pct')}",
        "- profit_threshold_grid_selected_avg_incremental_exit_profit_pct: "
        f"{_safe_float(selected_grid_row.get('avg_incremental_exit_profit_pct')):.2f}",
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
