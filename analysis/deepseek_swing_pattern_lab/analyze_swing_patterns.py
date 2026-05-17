"""Analyze swing patterns from fact tables and produce structured findings."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from analysis.deepseek_swing_pattern_lab.config import MIN_VALID_SAMPLES, OUTPUT_DIR

SCHEMA_VERSION = 2
FINDING_ID_PREFIX = "swing_pattern_lab_deepseek"
METRIC_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "probe_observe_only|sim_equal_weight",
    "window_policy": "sim_first_lifecycle_window_with_daily_source_quality_guard",
    "sample_floor": MIN_VALID_SAMPLES,
    "primary_decision_metric": "equal_weight_avg_profit_pct",
    "source_quality_gate": "sim/probe/dry-run provenance required; COMPLETED + valid_profit_rate only for realized PnL diagnostics",
    "forbidden_uses": [
        "threshold_mutation",
        "order_guard_mutation",
        "provider_change",
        "bot_restart",
        "broker_order_submit",
    ],
    "runtime_effect": False,
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_csv(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    if path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _load_json(name: str) -> dict[str, Any]:
    path = OUTPUT_DIR / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _nan_none(value: Any) -> Any:
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def analyze_selection_bottleneck(
    funnel_fact: pd.DataFrame, trade_fact: pd.DataFrame
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    total_dates = len(funnel_fact)
    zero_selected = int((funnel_fact["selected_count"] <= 0).sum()) if not funnel_fact.empty else 0
    low_selected = int(((funnel_fact["selected_count"] > 0) & (funnel_fact["selected_count"] < 3)).sum()) if not funnel_fact.empty else 0

    if total_dates == 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_selection_no_data",
                "title": "Swing selection data missing",
                "lifecycle_stage": "selection",
                "route": "defer_evidence",
                "mapped_family": "swing_model_floor",
                "confidence": "solo",
                "evidence": {"error": "No funnel fact data available"},
                "runtime_effect": False,
                "expected_ev_effect": "Evidence insufficient; wait for data accumulation.",
            }
        )
        return findings

    if zero_selected > 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_selection_zero_candidates",
                "title": "Model floor too high causing zero candidates",
                "lifecycle_stage": "selection",
                "route": "design_family_candidate",
                "mapped_family": "swing_model_floor",
                "confidence": "solo" if zero_selected < MIN_VALID_SAMPLES else "consensus",
                "evidence": {
                    "zero_selected_dates": _safe_int(zero_selected),
                    "total_dates": total_dates,
                    "current_floor_bull": _nan_none(funnel_fact["floor_bull"].iloc[-1]) if not funnel_fact.empty else None,
                    "current_floor_bear": _nan_none(funnel_fact["floor_bear"].iloc[-1]) if not funnel_fact.empty else None,
                },
                "runtime_effect": False,
                "expected_ev_effect": "Lower floor could increase candidate count but risks quality degradation.",
            }
        )

    if low_selected > 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_selection_low_candidate_count",
                "title": "Low swing candidate count per day",
                "lifecycle_stage": "selection",
                "route": "attach_existing_family",
                "mapped_family": "swing_selection_top_k",
                "confidence": "solo" if low_selected < MIN_VALID_SAMPLES else "consensus",
                "evidence": {
                    "low_selected_dates": _safe_int(low_selected),
                    "total_dates": total_dates,
                },
                "runtime_effect": False,
                "expected_ev_effect": "Increase top_k or adjust floor slightly to expand candidate pool.",
            }
        )

    fallback_dates = funnel_fact.get("fallback_written", pd.Series(dtype=bool))
    fallback_count = int(fallback_dates.sum()) if not fallback_dates.empty else 0
    if fallback_count > 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_selection_fallback_contamination",
                "title": "Fallback diagnostic rows detected in recommendations",
                "lifecycle_stage": "selection",
                "route": "design_family_candidate",
                "mapped_family": "swing_model_floor",
                "confidence": "solo" if fallback_count < MIN_VALID_SAMPLES else "consensus",
                "evidence": {
                    "fallback_dates": _safe_int(fallback_count),
                    "total_dates": total_dates,
                },
                "runtime_effect": False,
                "expected_ev_effect": "Fallback contamination indicates floor may be mis-calibrated for current regime.",
            }
        )

    return findings


def analyze_entry_bottleneck(funnel_fact: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if funnel_fact.empty:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_entry_no_data",
                "title": "Swing entry data missing",
                "lifecycle_stage": "entry",
                "route": "defer_evidence",
                "mapped_family": None,
                "confidence": "solo",
                "evidence": {"error": "No funnel fact data available"},
                "runtime_effect": False,
            }
        )
        return findings

    total_blocked_gatekeeper = _safe_int(funnel_fact["blocked_gatekeeper_reject_selection_unique"].sum())
    total_blocked_gatekeeper_carryover = _safe_int(funnel_fact["blocked_gatekeeper_reject_carryover_unique"].sum())
    total_blocked_gap = _safe_int(funnel_fact["blocked_swing_gap_selection_unique"].sum())
    total_blocked_gap_carryover = _safe_int(funnel_fact["blocked_swing_gap_carryover_unique"].sum())
    total_market_block = _safe_int(funnel_fact["market_regime_block_selection_unique"].sum())
    total_market_block_carryover = _safe_int(funnel_fact["market_regime_block_carryover_unique"].sum())
    total_submitted = _safe_int(funnel_fact["submitted_unique_records"].sum())
    total_selected = _safe_int(funnel_fact["selected_count"].sum())

    selection_blocked = total_blocked_gatekeeper > 0

    if total_blocked_gatekeeper > 0 or total_blocked_gatekeeper_carryover > 0:
        route = "attach_existing_family" if selection_blocked else "defer_evidence"
        confidence_val = "solo" if total_blocked_gatekeeper < MIN_VALID_SAMPLES else "consensus"
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_entry_gatekeeper_reject",
                "title": "Gatekeeper rejects swing entry candidates",
                "lifecycle_stage": "entry",
                "route": route,
                "mapped_family": "swing_gatekeeper_accept_reject" if selection_blocked else None,
                "confidence": confidence_val,
                "evidence": {
                    "blocked_selection_unique": total_blocked_gatekeeper,
                    "blocked_carryover_unique": total_blocked_gatekeeper_carryover,
                    "selected_count": total_selected,
                },
                "runtime_effect": False,
                "expected_ev_effect": "Review gatekeeper criteria for swing-specific calibration."
                if selection_blocked
                else "Carryover-only blocker; observe before attaching to threshold family.",
            }
        )

    gap_selection_blocked = total_blocked_gap > 0

    if total_blocked_gap > 0 or total_blocked_gap_carryover > 0:
        route = "design_family_candidate" if gap_selection_blocked else "defer_evidence"
        confidence_val = "solo" if total_blocked_gap < MIN_VALID_SAMPLES else "consensus"
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_entry_gap_block",
                "title": "Swing gap/protection blocking entry",
                "lifecycle_stage": "entry",
                "route": route,
                "mapped_family": None,
                "confidence": confidence_val,
                "evidence": {
                    "blocked_selection_unique": total_blocked_gap,
                    "blocked_carryover_unique": total_blocked_gap_carryover,
                    "selected_count": total_selected,
                },
                "runtime_effect": False,
                "expected_ev_effect": "No existing swing gap family exists; design new gap/protection threshold family candidate."
                if gap_selection_blocked
                else "Carryover-only blocker; observe before designing new family.",
            }
        )

    if total_market_block > 0 or total_market_block_carryover > 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_entry_market_regime_block",
                "title": "Market regime hard block prevents entry",
                "lifecycle_stage": "entry",
                "route": "defer_evidence",
                "mapped_family": "swing_market_regime_sensitivity",
                "confidence": "solo" if total_market_block < MIN_VALID_SAMPLES else "consensus",
                "evidence": {
                    "blocked_selection_unique": total_market_block,
                    "blocked_carryover_unique": total_market_block_carryover,
                    "selected_count": total_selected,
                },
                "runtime_effect": False,
                "expected_ev_effect": "Market regime sensitivity should be assessed over longer sample.",
            }
        )

    if total_selected > 0 and total_submitted == 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_entry_no_submissions",
                "title": "All selected candidates failed to reach order submission",
                "lifecycle_stage": "entry",
                "route": "design_family_candidate",
                "mapped_family": None,
                "confidence": "solo" if total_selected < MIN_VALID_SAMPLES else "consensus",
                "evidence": {
                    "selected_count": total_selected,
                    "submitted_count": total_submitted,
                    "blocked_gatekeeper_selection": total_blocked_gatekeeper,
                    "blocked_gatekeeper_carryover": total_blocked_gatekeeper_carryover,
                    "blocked_gap_selection": total_blocked_gap,
                    "blocked_gap_carryover": total_blocked_gap_carryover,
                    "blocked_market_selection": total_market_block,
                    "blocked_market_carryover": total_market_block_carryover,
                },
                "runtime_effect": False,
                "expected_ev_effect": "Investigate the entry funnel for swing-specific bottlenecks.",
            }
        )

    return findings


def analyze_holding_exit_bottleneck(
    funnel_fact: pd.DataFrame,
    sequence_fact: pd.DataFrame,
    trade_fact: pd.DataFrame,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    total_entered = _safe_int(funnel_fact["entered_rows"].sum()) if not funnel_fact.empty else 0
    total_completed = _safe_int(funnel_fact["completed_rows"].sum()) if not funnel_fact.empty else 0
    total_valid = _safe_int(funnel_fact["valid_profit_rows"].sum()) if not funnel_fact.empty else 0

    if not trade_fact.empty:
        completed = trade_fact[trade_fact["completed"] == True]
        if not completed.empty:
            valid = completed[completed["valid_profit_rate"].notna()]
            win_count = int((valid["profit_rate"] > 0).sum()) if not valid.empty else 0
            loss_count = int((valid["profit_rate"] < 0).sum()) if not valid.empty else 0
            win_count_all = int((valid["profit"] > 0).sum()) if not valid.empty else 0
            loss_count_all = int((valid["profit"] < 0).sum()) if not valid.empty else 0
            avg_win = round(float(valid[valid["profit_rate"] > 0]["profit_rate"].mean()), 4) if not valid.empty and win_count > 0 else None
            avg_loss = round(abs(float(valid[valid["profit_rate"] < 0]["profit_rate"].mean())), 4) if not valid.empty and loss_count > 0 else None
            total_pnl = _safe_float(valid["profit"].sum()) if not valid.empty else 0.0

            if win_count_all + loss_count_all >= MIN_VALID_SAMPLES:
                findings.append(
                    {
                        "finding_id": f"{FINDING_ID_PREFIX}_holding_exit_pnl_review",
                        "title": "Swing trade P&L review from completed trades",
                        "lifecycle_stage": "holding_exit",
                        "route": "attach_existing_family",
                        "mapped_family": "swing_trailing_stop_time_stop",
                        "confidence": "consensus" if win_count_all + loss_count_all >= 5 else "solo",
                        "evidence": {
                            "completed_trades": len(completed),
                            "valid_profit_trades": len(valid),
                            "win_trades": win_count,
                            "loss_trades": loss_count,
                            "avg_win_rate": avg_win,
                            "avg_loss_rate": avg_loss,
                            "total_pnl_krw": total_pnl,
                        },
                        "runtime_effect": False,
                        "expected_ev_effect": "Calibrate trailing stop and exit timing based on observed MFE/MAE patterns.",
                    }
                )

    exit_sources = (
        sequence_fact["exit_source"].value_counts().to_dict()
        if not sequence_fact.empty and "exit_source" in sequence_fact
        else {}
    )
    if exit_sources:
        sources_str = ", ".join(f"{k}: {v}" for k, v in sorted(exit_sources.items(), key=lambda x: -x[1])[:5])
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_holding_exit_source_distribution",
                "title": "Exit source distribution review",
                "lifecycle_stage": "holding_exit",
                "route": "defer_evidence",
                "mapped_family": "swing_trailing_stop_time_stop",
                "confidence": "solo",
                "evidence": {"exit_sources": exit_sources},
                "runtime_effect": False,
                "expected_ev_effect": "Monitor exit source distribution for mis-calibration signals.",
            }
        )

    if total_entered == 0 and total_completed == 0 and total_valid == 0:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_holding_exit_no_trades",
                "title": "No completed swing trades in analysis window",
                "lifecycle_stage": "holding_exit",
                "route": "defer_evidence",
                "mapped_family": None,
                "confidence": "low_sample",
                "evidence": {"entered_rows": total_entered, "completed_rows": total_completed},
                "runtime_effect": False,
                "expected_ev_effect": "Insufficient evidence; defer until more trades complete.",
            }
        )

    return findings


def analyze_scale_in_bottleneck(
    sequence_fact: pd.DataFrame, trade_fact: pd.DataFrame
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    if not sequence_fact.empty:
        scale_in_events = sequence_fact[sequence_fact["scale_in_observed"] == True]
        if len(scale_in_events) > 0:
            findings.append(
                {
                    "finding_id": f"{FINDING_ID_PREFIX}_scale_in_events_observed",
                    "title": "Scale-in events observed for swing positions",
                    "lifecycle_stage": "scale_in",
                    "route": "attach_existing_family",
                    "mapped_family": "swing_scale_in_ofi_qi_confirmation",
                    "confidence": "solo" if len(scale_in_events) < MIN_VALID_SAMPLES else "consensus",
                    "evidence": {"scale_in_events": len(scale_in_events)},
                    "runtime_effect": False,
                    "expected_ev_effect": "Evaluate PYRAMID/AVG_DOWN outcome quality with OFI/QI confirmation.",
                }
            )

    if not trade_fact.empty:
        pyramid_count = _safe_int(trade_fact["pyramid_count"].sum())
        avg_down_count = _safe_int(trade_fact["avg_down_count"].sum())
        if pyramid_count > 0:
            findings.append(
                {
                    "finding_id": f"{FINDING_ID_PREFIX}_scale_in_pyramid_usage",
                    "title": "PYRAMID scale-in observed",
                    "lifecycle_stage": "scale_in",
                    "route": "attach_existing_family",
                    "mapped_family": "swing_pyramid_trigger",
                    "confidence": "solo" if pyramid_count < MIN_VALID_SAMPLES else "consensus",
                    "evidence": {"pyramid_count": pyramid_count},
                    "runtime_effect": False,
                    "expected_ev_effect": "Assess PYRAMID trigger threshold and post-add MFE.",
                }
            )
        if avg_down_count > 0:
            findings.append(
                {
                    "finding_id": f"{FINDING_ID_PREFIX}_scale_in_avg_down_usage",
                    "title": "AVG_DOWN scale-in observed",
                    "lifecycle_stage": "scale_in",
                    "route": "attach_existing_family",
                    "mapped_family": "swing_avg_down_eligibility",
                    "confidence": "solo" if avg_down_count < MIN_VALID_SAMPLES else "consensus",
                    "evidence": {"avg_down_count": avg_down_count},
                    "runtime_effect": False,
                    "expected_ev_effect": "Assess AVG_DOWN eligibility criteria and risk of loss extension.",
                }
            )

    return findings


def analyze_ofi_qi_quality(ofi_qi_fact: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if ofi_qi_fact.empty:
        return findings

    total_rows = len(ofi_qi_fact)
    stale_missing = int(ofi_qi_fact["stale_missing_flag"].sum())
    stale_ratio = round(stale_missing / max(total_rows, 1), 4)
    reason_counts = {
        column.replace("_flag", ""): int(ofi_qi_fact[column].sum())
        for column in (
            "micro_missing_flag",
            "micro_stale_flag",
            "observer_unhealthy_flag",
            "micro_not_ready_flag",
            "state_insufficient_flag",
        )
        if column in ofi_qi_fact
    }
    reason_ratios = {
        reason: round(count / max(total_rows, 1), 4)
        for reason, count in reason_counts.items()
    }
    stale_rows = ofi_qi_fact[ofi_qi_fact["stale_missing_flag"] == True].copy()
    reason_combination_counts = (
        stale_rows["stale_missing_reasons"].fillna("unknown").replace("", "unknown").str.replace(",", "+").value_counts().to_dict()
        if "stale_missing_reasons" in stale_rows and not stale_rows.empty
        else {}
    )
    reason_combination_unique_record_counts: dict[str, int] = {}
    if not stale_rows.empty and "stale_missing_reasons" in stale_rows and "record_id" in stale_rows:
        tmp = stale_rows.copy()
        tmp["_reason_combination"] = tmp["stale_missing_reasons"].fillna("unknown").replace("", "unknown").str.replace(",", "+")
        reason_combination_unique_record_counts = {
            str(key): int(value)
            for key, value in tmp.groupby("_reason_combination")["record_id"].nunique().to_dict().items()
        }
    stale_missing_group_counts = (
        stale_rows["group"].fillna("unknown").replace("", "unknown").value_counts().to_dict()
        if "group" in stale_rows and not stale_rows.empty
        else {}
    )
    stale_missing_group_unique_record_counts = (
        {
            str(key): int(value)
            for key, value in stale_rows.groupby("group")["record_id"].nunique().to_dict().items()
        }
        if "group" in stale_rows and "record_id" in stale_rows and not stale_rows.empty
        else {}
    )
    observer_unhealthy_overlap = {
        "observer_unhealthy_total": int(stale_rows["observer_unhealthy_flag"].sum())
        if "observer_unhealthy_flag" in stale_rows and not stale_rows.empty else 0,
        "observer_unhealthy_with_other_reason": 0,
        "observer_unhealthy_only": 0,
    }
    if not stale_rows.empty and "observer_unhealthy_flag" in stale_rows:
        other_columns = [
            column for column in (
                "micro_missing_flag",
                "micro_stale_flag",
                "micro_not_ready_flag",
                "state_insufficient_flag",
            )
            if column in stale_rows
        ]
        observer_rows = stale_rows[stale_rows["observer_unhealthy_flag"] == True]
        observer_unhealthy_overlap["observer_unhealthy_with_other_reason"] = int(
            observer_rows[other_columns].any(axis=1).sum()
        ) if other_columns else 0
        observer_unhealthy_overlap["observer_unhealthy_only"] = (
            observer_unhealthy_overlap["observer_unhealthy_total"]
            - observer_unhealthy_overlap["observer_unhealthy_with_other_reason"]
        )

    advice_counts = ofi_qi_fact["swing_micro_advice"].value_counts().to_dict() if "swing_micro_advice" in ofi_qi_fact else {}
    state_counts = ofi_qi_fact["orderbook_micro_state"].value_counts().to_dict() if "orderbook_micro_state" in ofi_qi_fact else {}
    group_counts = ofi_qi_fact["group"].value_counts().to_dict() if "group" in ofi_qi_fact else {}

    runtime_effect_true = int(
        (ofi_qi_fact["swing_micro_runtime_effect"] == True).sum()
    ) if "swing_micro_runtime_effect" in ofi_qi_fact else 0

    findings.append(
        {
            "finding_id": f"{FINDING_ID_PREFIX}_ofi_qi_stale_missing",
            "title": "OFI/QI stale/missing quality review",
            "lifecycle_stage": "ofi_qi",
            "route": "implement_now" if stale_ratio > 0.3 else "defer_evidence",
            "mapped_family": "swing_entry_ofi_qi_execution_quality",
            "confidence": "consensus" if total_rows >= 10 else "solo",
            "evidence": {
                "total_samples": total_rows,
                "stale_missing_count": stale_missing,
                "stale_missing_ratio": stale_ratio,
                "stale_missing_reason_counts": reason_counts,
                "stale_missing_reason_ratios": reason_ratios,
                "stale_missing_reason_combination_counts": reason_combination_counts,
                "stale_missing_reason_combination_unique_record_counts": reason_combination_unique_record_counts,
                "stale_missing_group_counts": stale_missing_group_counts,
                "stale_missing_group_unique_record_counts": stale_missing_group_unique_record_counts,
                "stale_missing_unique_record_count": int(stale_rows["record_id"].nunique()) if "record_id" in stale_rows else 0,
                "observer_unhealthy_overlap": observer_unhealthy_overlap,
                "advice_distribution": advice_counts,
                "state_distribution": state_counts,
                "group_distribution": group_counts,
                "runtime_effect_true_count": runtime_effect_true,
            },
            "runtime_effect": False,
            "expected_ev_effect": "If stale ratio > 0.3, consider instrumentation/observer enhancement.",
        }
    )

    smoothing_actions = ofi_qi_fact["smoothing_action"].value_counts().to_dict() if "smoothing_action" in ofi_qi_fact else {}
    if smoothing_actions:
        findings.append(
            {
                "finding_id": f"{FINDING_ID_PREFIX}_ofi_qi_smoothing_review",
                "title": "OFI/QI exit smoothing action distribution",
                "lifecycle_stage": "ofi_qi",
                "route": "attach_existing_family",
                "mapped_family": "swing_exit_ofi_qi_smoothing",
                "confidence": "solo",
                "evidence": {"smoothing_actions": smoothing_actions},
                "runtime_effect": False,
                "expected_ev_effect": "Monitor DEBOUNCE_EXIT/CONFIRM_EXIT rate for holding flow quality.",
            }
        )

    return findings


def analyze_recommendation_csv_detail(trade_fact: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if trade_fact.empty:
        return findings

    return findings


def classify_finding_route(finding: dict[str, Any]) -> dict[str, Any]:
    route = finding.get("route", "defer_evidence")
    if route == "implement_now":
        finding["decision_classification"] = "implement_now"
    elif route == "attach_existing_family" and finding.get("mapped_family"):
        finding["decision_classification"] = "attach_existing_family"
    elif route == "design_family_candidate":
        finding["decision_classification"] = "design_family_candidate"
    elif route == "defer_evidence":
        finding["decision_classification"] = "defer_evidence"
    else:
        finding["decision_classification"] = "defer_evidence"
    return finding


def build_code_improvement_orders(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for idx, finding in enumerate(findings):
        route = finding.get("route", "defer_evidence")
        if route in ("defer_evidence", "reject"):
            continue
        classification = finding.get("decision_classification", route)
        orders.append(
            {
                "order_id": f"order_{finding.get('finding_id', f'unknown_{idx}')}",
                "title": finding.get("title", ""),
                "lifecycle_stage": finding.get("lifecycle_stage", ""),
                "target_subsystem": {
                    "selection": "swing_model_selection",
                    "entry": "swing_entry_funnel",
                    "holding_exit": "swing_holding_exit",
                    "scale_in": "swing_scale_in",
                    "ofi_qi": "swing_micro_context",
                }.get(finding.get("lifecycle_stage", ""), "swing_logic"),
                "priority": idx + 1,
                "route": classification,
                "mapped_family": finding.get("mapped_family"),
                "threshold_family": finding.get("mapped_family"),
                "intent": f"Improve swing {finding.get('lifecycle_stage', '')} quality based on pattern lab evidence.",
                "expected_ev_effect": finding.get("expected_ev_effect", ""),
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_audit.py",
                    "src/engine/swing_selection_funnel_report.py",
                    "src/model/common_v2.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py",
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py",
                ],
                "evidence": [finding.get("evidence", {})],
                "improvement_type": "pattern_lab_observation",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "next_postclose_metric": f"swing_{finding.get('lifecycle_stage', '')}_quality_score",
            }
        )
    return orders


def load_fact_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trade_fact = _load_csv("swing_trade_fact.csv")
    funnel_fact = _load_csv("swing_lifecycle_funnel_fact.csv")
    sequence_fact = _load_csv("swing_sequence_fact.csv")
    ofi_qi_fact = _load_csv("swing_ofi_qi_fact.csv")
    return trade_fact, funnel_fact, sequence_fact, ofi_qi_fact


def build_swing_pattern_analysis_result() -> dict[str, Any]:
    trade_fact, funnel_fact, sequence_fact, ofi_qi_fact = load_fact_tables()

    all_findings: list[dict[str, Any]] = []
    all_findings.extend(analyze_selection_bottleneck(funnel_fact, trade_fact))
    all_findings.extend(analyze_entry_bottleneck(funnel_fact))
    all_findings.extend(analyze_holding_exit_bottleneck(funnel_fact, sequence_fact, trade_fact))
    all_findings.extend(analyze_scale_in_bottleneck(sequence_fact, trade_fact))
    all_findings.extend(analyze_ofi_qi_quality(ofi_qi_fact))

    all_findings = [classify_finding_route(f) for f in all_findings]

    code_improvement_orders = build_code_improvement_orders(all_findings)

    quality_report = _load_json("data_quality_report.json")
    quality_warnings = quality_report.get("warnings", []) if isinstance(quality_report.get("warnings"), list) else []

    result = {
        "schema_version": SCHEMA_VERSION,
        "metric_contract": METRIC_CONTRACT,
        "report_type": "deepseek_swing_pattern_lab",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "analysis_start": str(funnel_fact["date"].iloc[0]) if not funnel_fact.empty else "",
        "analysis_end": str(funnel_fact["date"].iloc[-1]) if not funnel_fact.empty else "",
        "runtime_change": False,
        "data_quality": {
            "trade_rows": len(trade_fact),
            "lifecycle_event_rows": len(sequence_fact),
            "completed_valid_profit_rows": int(trade_fact["valid_profit_rate"].notna().sum()) if not trade_fact.empty else 0,
            "ofi_qi_rows": len(ofi_qi_fact),
            "sim_probe_provenance": quality_report.get("sim_probe_provenance", {}),
            "warnings": quality_warnings,
        },
        "stage_findings": all_findings,
        "code_improvement_orders": code_improvement_orders,
    }

    output_path = OUTPUT_DIR / "swing_pattern_analysis_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    result = build_swing_pattern_analysis_result()
    print(f"Analysis complete: {len(result['stage_findings'])} findings, {len(result['code_improvement_orders'])} code improvement orders")
    print(f"Output written to {OUTPUT_DIR / 'swing_pattern_analysis_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
