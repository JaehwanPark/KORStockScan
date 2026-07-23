from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))
FAMILY = "scalping_pyramid_quality_gate"
STAGE = "scale_in"
REPORT_TYPE = "scalping_pyramid_quality_calibration"
INPUT_REPORT_DIR = DATA_DIR / "report" / "scalping_pyramid_intraday_feedback"
OUTPUT_REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
CLEAN_BASELINE_DATE = "2026-06-04"
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


def _closed_pyramid_rows(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        for row in report.get("pyramid_feedback_rows") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("pyramid_feedback_label") or "") not in CLOSED_LABELS:
                continue
            rows.append(row)
    return rows


def _closed_one_share_pyramid_rows(
    reports: list[dict[str, Any]],
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
            if row.get("probe_residual_observation_seen") and (
                row.get("residual_fill_attribution_valid") is not True
                or row.get("venue_source_quality_valid") is not True
            ):
                continue
            rows.append(row)
    return rows, section_present


def _normal_winner_expansion_observation(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
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
            int(row.get("normal_winner_expansion_candidate_notional_krw") or 0),
        )
        for row in rows
        if int(row.get("normal_winner_expansion_candidate_notional_krw") or 0) > 0
    ]
    winner_count = sum(
        1
        for row in rows
        if row.get("normal_winner_expansion_label") == "realized_incremental_winner"
    )
    sample_floor_met = len(rows) >= 20
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
                    int(row.get("normal_winner_expansion_candidate_notional_krw") or 0),
                )
                for row in bucket_rows
                if int(row.get("normal_winner_expansion_candidate_notional_krw") or 0)
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
        "sample_count": len(rows),
        "sample_floor": 20,
        "sample_floor_met": sample_floor_met,
        "provenance_rejected_count": provenance_rejected_count,
        "realized_incremental_winner_count": winner_count,
        "diagnostic_win_rate": (round(winner_count / len(rows), 4) if rows else 0.0),
        "notional_weighted_ev_pct": notional_weighted_ev_pct,
        "by_effective_venue": _dimension_rollup("effective_venue"),
        "by_market_session_bucket": _dimension_rollup("market_session_bucket"),
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
) -> dict[str, Any]:
    one_share_rows, one_share_source_present = _closed_one_share_pyramid_rows(reports)
    normal_winner_expansion = _normal_winner_expansion_observation(reports)
    rows = one_share_rows if one_share_source_present else _closed_pyramid_rows(reports)
    calibration_source_scope = (
        "one_share_event_opportunity"
        if one_share_source_present
        else "legacy_pyramid_feedback_rows"
    )
    rates = _row_rates(rows)
    source_quality_pass = bool(reports) and all(
        ((report.get("source_quality") or {}).get("status") == "pass")
        for report in reports
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
        allowed = state in {"adjust_up", "adjust_down"}

    return {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 39,
        "family_type": "bounded_tunable_scalping_pyramid_quality_gate",
        "calibration_state": state,
        "calibration_reason": reason,
        "threshold_version": f"{FAMILY}:{target_date}:v1",
        "sample_count": rates["sample_count"],
        "sample_floor": 20,
        "allowed_runtime_apply": allowed,
        "safety_revert_required": False,
        "source_quality_gate": (
            "pass" if source_contract_pass else "source_quality_blocked"
        ),
        "source_quality_status": "pass" if source_contract_pass else "blocked",
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
            "provenance_present": provenance_present,
            "recommended_action": state,
            "recommended_action_reason": reason,
            "normal_winner_expansion_observation": normal_winner_expansion,
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
    paths = (
        input_paths
        if input_paths is not None
        else _iter_feedback_report_paths(target_date)
    )
    reports = [_load_json(path) for path in paths if path.exists()]
    candidate = _calibration_candidate(
        target_date=target_date, reports=reports, source_paths=paths
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
            "source_quality_gate": "all_consumed_intraday_feedback_reports_source_quality_pass_and_provenance_present",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "normal_winner_expansion_observation": (
            candidate["source_metrics"]["normal_winner_expansion_observation"]
        ),
        "source_quality": {
            "status": (
                "pass"
                if candidate["source_metrics"]["source_quality_pass"]
                else "blocked"
            ),
            "input_report_count": len(reports),
            "input_paths": [str(path) for path in paths],
            "provenance_present": candidate["source_metrics"]["provenance_present"],
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
    lines = [
        f"# {report.get('target_date')} Scalping Pyramid Quality Calibration",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- family: {FAMILY}",
        f"- stage: {STAGE}",
        f"- calibration_state: {candidate.get('calibration_state')}",
        f"- calibration_reason: {candidate.get('calibration_reason')}",
        f"- allowed_runtime_apply: {str(candidate.get('allowed_runtime_apply')).lower()}",
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
        f"- provenance_present: {metrics.get('provenance_present')}",
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
