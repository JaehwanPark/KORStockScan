"""Report-only BUY funnel hurdle backtest from existing June artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.market_day import is_krx_trading_day


REPORT_TYPE = "entry_hurdle_backtest"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
BUY_FUNNEL_DIR = DATA_DIR / "report" / "buy_funnel_sentinel"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
MISSED_ENTRY_DIRS = [
    DATA_DIR / "report" / "monitor_snapshots",
    DATA_DIR / "report" / "missed_entry_counterfactual",
]

FORBIDDEN_USES = [
    "entry price reprice",
    "risk expansion",
    "quantity cap release",
    "broker guard bypass",
    "stale quote guard bypass",
    "intraday threshold mutation",
    "provider change",
    "bot restart",
]
OVERBOUGHT_BLOCKER_KEYS = {
    "blocked_overbought",
    "pre_submit_overbought_pullback_guard_block",
    "scalp_sim_pre_submit_overbought_guard_would_block",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "null", "none"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "null", "none"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _tick_aggressor_pressure_usable(fields: dict[str, Any]) -> bool:
    return bool(
        _safe_bool(fields.get("tick_aggressor_pressure_usable"))
        or _safe_float(fields.get("tick_aggressor_trusted_count"), 0.0) > 0
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        actual_path = existing_or_gzip_path(path)
        if actual_path.exists():
            with open_text_auto(actual_path) as handle:
                return json.loads(handle.read())
    except Exception:
        return {}
    return {}


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    dates: list[str] = []
    current = start
    while current <= end:
        if is_krx_trading_day(current):
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _buy_funnel_path(target_date: str) -> Path:
    return existing_or_gzip_path(BUY_FUNNEL_DIR / f"buy_funnel_sentinel_{target_date}.json")


def _missed_entry_path(target_date: str) -> Path:
    for base in MISSED_ENTRY_DIRS:
        path = base / f"missed_entry_counterfactual_{target_date}.json"
        actual_path = existing_or_gzip_path(path)
        if actual_path.exists():
            return actual_path
    return existing_or_gzip_path(MISSED_ENTRY_DIRS[0] / f"missed_entry_counterfactual_{target_date}.json")


def _pipeline_events_path(target_date: str) -> Path:
    return existing_or_gzip_path(PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl")


def _iter_jsonl(path: Path, *, required_substrings: tuple[str, ...] = ()):
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    try:
        with open_text_auto(actual_path) as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                if required_substrings and not any(marker in line for marker in required_substrings):
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except Exception:
        return


def _session_summary(report: dict[str, Any]) -> dict[str, Any]:
    session = report.get("session_summary")
    if isinstance(session, dict):
        return session
    current = report.get("current")
    if isinstance(current, dict) and isinstance(current.get("session"), dict):
        return current["session"]
    if isinstance(current, dict):
        return current
    return {}


def _stage_unique(report: dict[str, Any]) -> dict[str, int]:
    session = _session_summary(report)
    values = session.get("stage_unique")
    if not isinstance(values, dict):
        return {}
    return {str(key): _safe_int(value, 0) for key, value in values.items()}


def _ratios(report: dict[str, Any]) -> dict[str, float]:
    session = _session_summary(report)
    values = session.get("ratios")
    if not isinstance(values, dict):
        return {}
    return {str(key): _safe_float(value, 0.0) for key, value in values.items()}


def _classification(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("classification")
    return value if isinstance(value, dict) else {}


def _quote_freshness_attribution(report: dict[str, Any]) -> dict[str, Any]:
    classification = _classification(report)
    root_cause = classification.get("submit_drought_root_cause")
    if not isinstance(root_cause, dict):
        return {}
    value = root_cause.get("quote_freshness_attribution")
    return value if isinstance(value, dict) else {}


def _blocker_metrics(missed_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = ((missed_report.get("metrics") or {}).get("blocker_outcome_metrics") or {})
    return metrics if isinstance(metrics, dict) else {}


def _cohort_metrics(missed_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = ((missed_report.get("metrics") or {}).get("cohort_outcome_metrics") or {})
    return metrics if isinstance(metrics, dict) else {}


def _hurdle_decision(row: dict[str, Any]) -> str:
    missed_rate = _safe_float(row.get("missed_winner_rate"), 0.0)
    avoided_rate = _safe_float(row.get("avoided_loser_rate"), 0.0)
    evaluated = _safe_int(row.get("evaluated_candidates"), 0)
    if evaluated < 3:
        return "hold_sample"
    if missed_rate >= avoided_rate + 20.0 and missed_rate >= 35.0:
        return "overblocking_candidate"
    if avoided_rate >= missed_rate + 20.0 and avoided_rate >= 35.0:
        return "protective_hurdle_candidate"
    return "balanced_or_unclear"


def _counter_to_plain(counter: Counter[str]) -> dict[str, int]:
    return {str(key): _safe_int(value, 0) for key, value in sorted(counter.items()) if _safe_int(value, 0) > 0}


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _source_signature_tokens(source_signature: Any) -> set[str]:
    return {
        token.strip().upper()
        for token in str(source_signature or "").replace("|", ",").split(",")
        if token.strip()
    }


def _signature_strong_bundle(source_signature: Any) -> bool:
    tokens = _source_signature_tokens(source_signature)
    if {"PRICE_JUMP_START", "VOLUME_SURGE_POSITIVE"}.issubset(tokens):
        return True
    return (
        {"VALUE_TOP", "VOLUME_SURGE_POSITIVE"}.issubset(tokens)
        and bool({"REALTIME_RANK_START", "OPEN_TOP"} & tokens)
    )


def _signature_micro_pressure_path(fields: dict[str, Any]) -> bool:
    return (
        _signature_strong_bundle(fields.get("source_signature"))
        and _safe_float(fields.get("curr_vs_micro_vwap_bp"), 0.0) >= 25.0
        and _tick_aggressor_pressure_usable(fields)
        and _safe_float(fields.get("buy_pressure_10t"), 0.0) >= 80.0
    )


def _event_key(event: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(event.get("emitted_date") or ""),
        str(event.get("stock_code") or ""),
        str(event.get("record_id") or ""),
        str(event.get("stage") or ""),
    )


def _top_overblocking(summary: dict[str, dict[str, Any]], keys: set[str]) -> dict[str, Any] | None:
    rows = []
    for key in keys:
        row = summary.get(key)
        if not isinstance(row, dict):
            continue
        if row.get("hurdle_decision") != "overblocking_candidate":
            continue
        rows.append((key, row))
    if not rows:
        return None
    rows.sort(
        key=lambda item: (
            _safe_float(item[1].get("missed_winner_rate"), 0.0),
            _safe_int(item[1].get("missed_winner_count"), 0),
            _safe_int(item[1].get("evaluated_candidates"), 0),
        ),
        reverse=True,
    )
    key, row = rows[0]
    return {"blocker": key, **row}


def _build_implemented_policy_backtest(
    *,
    source_dates: list[str],
    stage_totals: Counter[str],
    blocker_summary: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    liquidity_attempts: set[tuple[str, str, str, str]] = set()
    liquidity_symbols: set[str] = set()
    liquidity_skip_reasons: Counter[str] = Counter()
    liquidity_excluded: Counter[str] = Counter()
    ai_recheck_attempts: set[tuple[str, str, str, str]] = set()
    ai_recheck_symbols: set[str] = set()
    ai_recheck_excluded: Counter[str] = Counter()
    latest_liquidity_relief_by_record: dict[tuple[str, str], dict[str, Any]] = {}

    for source_date in source_dates:
        for event in _iter_jsonl(
            _pipeline_events_path(source_date),
            required_substrings=(
                '"stage":"pre_submit_liquidity_guard_block"',
                '"stage": "pre_submit_liquidity_guard_block"',
                '"stage":"pre_submit_liquidity_relief_skipped"',
                '"stage": "pre_submit_liquidity_relief_skipped"',
                '"stage":"blocked_ai_score"',
                '"stage": "blocked_ai_score"',
                '"stage":"first_ai_wait"',
                '"stage": "first_ai_wait"',
            ),
        ) or ():
            if not isinstance(event, dict):
                continue
            stage = str(event.get("stage") or "")
            fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
            code = str(event.get("stock_code") or "")
            record_key = (code, str(event.get("record_id") or ""))
            if stage == "pre_submit_liquidity_relief_skipped":
                latest_liquidity_relief_by_record[record_key] = fields
                continue
            if stage == "pre_submit_liquidity_guard_block":
                relief_fields = latest_liquidity_relief_by_record.get(record_key, {})
                merged_fields = {**relief_fields, **fields}
                if _truthy(merged_fields.get("quote_stale_at_submit")) or _truthy(
                    merged_fields.get("price_context_stale_at_submit")
                ):
                    liquidity_excluded["stale_quote_or_context"] += 1
                    continue
                if str(merged_fields.get("pre_submit_overbought_guard_action") or "").upper() not in {"", "PASS"}:
                    liquidity_excluded["overbought_guard_not_pass"] += 1
                    continue
                if str(merged_fields.get("entry_submit_revalidation_warning") or "").strip():
                    liquidity_excluded["submit_revalidation_warning"] += 1
                    continue
                if str(merged_fields.get("latency_state") or "").upper() == "DANGER":
                    liquidity_excluded["latency_danger"] += 1
                    continue
                if (
                    merged_fields.get("ai_score") not in {None, "", "null", "none", "-"}
                    and _safe_float(merged_fields.get("ai_score"), 0.0) < 75.0
                ):
                    liquidity_excluded["ai_score_below_submit_min"] += 1
                    continue
                if not _signature_micro_pressure_path(merged_fields):
                    liquidity_excluded["signature_micro_pressure_not_met"] += 1
                    continue
                candidate_key = _event_key(event)
                if candidate_key not in liquidity_attempts:
                    liquidity_attempts.add(candidate_key)
                    if code:
                        liquidity_symbols.add(code)
                    liquidity_skip_reasons[str(merged_fields.get("liquidity_relief_skip_reason") or "-")] += 1
                continue

            if stage in {"blocked_ai_score", "first_ai_wait"}:
                score = _safe_float(fields.get("ai_score"), 0.0)
                if score < 60.0 or score > 74.0:
                    ai_recheck_excluded["score_outside_60_74"] += 1
                    continue
                if _truthy(fields.get("quote_stale")) or _truthy(fields.get("tick_context_stale")):
                    ai_recheck_excluded["stale_quote_or_tick_context"] += 1
                    continue
                if not _signature_strong_bundle(fields.get("source_signature")):
                    ai_recheck_excluded["source_signature_not_strong_bundle"] += 1
                    continue
                if _safe_float(fields.get("curr_vs_micro_vwap_bp"), 0.0) < 0.0:
                    ai_recheck_excluded["micro_vwap_negative"] += 1
                    continue
                ai_recheck_attempts.add(_event_key(event))
                if code:
                    ai_recheck_symbols.add(code)

    submitted_unique = _safe_int(stage_totals.get("order_bundle_submitted"), 0)
    budget_unique = _safe_int(stage_totals.get("budget_pass"), 0)
    conservative_submit_rate = submitted_unique / budget_unique if budget_unique else 0.0
    blocked_ai = blocker_summary.get("blocked_ai_score") if isinstance(blocker_summary.get("blocked_ai_score"), dict) else {}
    ai_missed_rate = _safe_float(blocked_ai.get("missed_winner_rate"), 0.0) / 100.0
    liquidity_count = len(liquidity_attempts)
    ai_recheck_count = len(ai_recheck_attempts)
    liquidity_conservative = round(liquidity_count * conservative_submit_rate)
    ai_recheck_conservative = round(ai_recheck_count * conservative_submit_rate * max(ai_missed_rate, 0.0))
    return {
        "metric_role": "funnel_count",
        "decision_authority": "implemented_entry_logic_counterfactual_report_only",
        "window_policy": "clean_baseline_existing_pipeline_events",
        "sample_floor": "event_level_reconstruction_available_rows_only",
        "primary_decision_metric": "estimated_order_bundle_submitted_count",
        "source_quality_gate": "clean_baseline_allowed_existing_pipeline_events",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted_provenance_preserved": True,
        "forbidden_uses": FORBIDDEN_USES,
        "implemented_policy_version": "entry_submit_recovery_v2_no_reprice_no_risk_expansion",
        "policy_changes_backtested": [
            "pre_submit_liquidity_signature_micro_pressure_relief",
            "early_accel_strong_bundle_recheck_score_60_74",
        ],
        "liquidity_signature_micro_pressure_relief": {
            "eligible_attempts": liquidity_count,
            "unique_symbols": len(liquidity_symbols),
            "conservative_estimated_order_submit_success": liquidity_conservative,
            "upper_bound_order_submit_path_reentry": liquidity_count,
            "eligible_prior_skip_reasons": _counter_to_plain(liquidity_skip_reasons),
            "excluded_reasons": _counter_to_plain(liquidity_excluded),
        },
        "ai_score_60_74_strong_bundle_recheck": {
            "eligible_recheck_attempts": ai_recheck_count,
            "unique_symbols": len(ai_recheck_symbols),
            "blocked_ai_score_missed_winner_rate_used": round(ai_missed_rate * 100.0, 2),
            "conservative_estimated_order_submit_success": ai_recheck_conservative,
            "upper_bound_recheck_attempts": ai_recheck_count,
            "excluded_reasons": _counter_to_plain(ai_recheck_excluded),
        },
        "total": {
            "eligible_attempts": liquidity_count + ai_recheck_count,
            "unique_symbols_upper_bound": len(liquidity_symbols | ai_recheck_symbols),
            "conservative_estimated_order_submit_success": liquidity_conservative + ai_recheck_conservative,
            "upper_bound_order_submit_path_reentry": liquidity_count + ai_recheck_count,
            "baseline_order_bundle_submitted": submitted_unique,
            "baseline_budget_pass": budget_unique,
            "baseline_submitted_to_budget_rate_pct": round(conservative_submit_rate * 100.0, 2),
        },
        "estimation_limits": [
            "second_ai_recheck_response_is_not_replayed",
            "broker_acceptance_is_not_replayed",
            "downstream_hard_guards_remain_excluded_or_unmodified",
        ],
    }


def _next_action_diagnostics(
    *,
    stage_totals: Counter[str],
    blocker_summary: dict[str, dict[str, Any]],
    cohort_summary: dict[str, dict[str, Any]],
    quote_totals: dict[str, Counter[str] | int],
    window_policy: str,
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    refresh_attempted = _safe_int(quote_totals.get("refresh_attempted_count"), 0)
    refresh_applied = _safe_int(quote_totals.get("refresh_applied_count"), 0)
    recovered = _safe_int(quote_totals.get("latency_pass_recovered_count"), 0)
    submitted_after_refresh = _safe_int(quote_totals.get("order_bundle_submitted_after_refresh_count"), 0)
    still_blocked = _safe_int(quote_totals.get("still_latency_blocked_after_refresh_count"), 0)
    recovered_downstream = (
        quote_totals.get("latency_pass_recovered_downstream_stage_counts")
        if isinstance(quote_totals.get("latency_pass_recovered_downstream_stage_counts"), Counter)
        else Counter()
    )

    if recovered > submitted_after_refresh:
        actions.append(
            {
                "action_id": "trace_latency_refresh_recovered_downstream_blocker",
                "priority": 1,
                "decision": "instrumentation_or_guard_overlap_candidate",
                "reason": "quote refresh recovered latency pass but did not always reach broker submit",
                "evidence": {
                    "refresh_attempted_count": refresh_attempted,
                    "refresh_applied_count": refresh_applied,
                    "latency_pass_recovered_count": recovered,
                    "order_bundle_submitted_after_refresh_count": submitted_after_refresh,
                    "still_latency_blocked_after_refresh_count": still_blocked,
                    "downstream_stage_counts": _counter_to_plain(recovered_downstream),
                },
                "allowed_next_step": "trace post-refresh downstream blocker provenance before changing guards",
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    liquidity = _top_overblocking(blocker_summary, {"pre_submit_liquidity_guard_block", "blocked_liquidity"})
    if liquidity:
        actions.append(
            {
                "action_id": "review_pre_submit_liquidity_relief_scope",
                "priority": 2,
                "decision": "bounded_report_only_policy_candidate",
                "reason": "liquidity blocker has missed-winner skew in existing counterfactual data",
                "evidence": liquidity,
                "allowed_next_step": (
                    "inspect pre_submit_liquidity_relief_skipped reasons and source-quality fields; "
                    "promote only through postclose/PREOPEN bounded policy if validated"
                ),
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    overbought = _top_overblocking(blocker_summary, OVERBOUGHT_BLOCKER_KEYS)
    if overbought:
        actions.append(
            {
                "action_id": "review_overbought_gate_miss_ev_recovery_scope",
                "priority": 3,
                "decision": "source_only_counterfactual_candidate",
                "reason": "overbought blocker has missed-winner skew in existing counterfactual data",
                "evidence": overbought,
                "allowed_next_step": (
                    "preserve overbought guard authority; use missed-winner/avoided-loser evidence only "
                    "for source-only recovery design until LDM/bridge contracts close"
                ),
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    ai_wait = _top_overblocking(blocker_summary, {"blocked_ai_score", "first_ai_wait"})
    ai_wait = ai_wait or _top_overblocking(
        cohort_summary,
        {"entry_source_blocked_ai_score", "entry_source_wait6579", "entry_wait6579_score66_69"},
    )
    if ai_wait:
        actions.append(
            {
                "action_id": "review_ai_wait_score_recheck_scope",
                "priority": 4,
                "decision": "recheck_scope_candidate_not_threshold_relaxation",
                "reason": "AI wait/score blocker has missed-winner skew but broad BUY threshold relaxation is forbidden",
                "evidence": ai_wait,
                "allowed_next_step": "evaluate bounded recheck/cohort routing using clean-baseline missed-winner evidence",
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    drift = _top_overblocking(blocker_summary, {"pre_submit_late_entry_price_drift_guard_block"})
    if drift:
        actions.append(
            {
                "action_id": "audit_late_entry_price_drift_guard_context",
                "priority": 5,
                "decision": "price_context_audit_candidate",
                "reason": "late price drift guard blocks possible winners; changing entry price is forbidden",
                "evidence": drift,
                "allowed_next_step": "audit reference-price and micro-reconfirmation provenance before any policy candidate",
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    actions.sort(key=lambda item: (_safe_int(item.get("priority"), 99), str(item.get("action_id") or "")))
    return {
        "metric_role": "next_action_diagnostic",
        "decision_authority": "entry_hurdle_backtest_report_only",
        "window_policy": window_policy,
        "sample_floor": "report_only_blocker_sample_floor_3",
        "primary_decision_metric": "missed_winner_vs_avoided_loser_tradeoff",
        "source_quality_gate": "clean_baseline_allowed_existing_buy_funnel_and_missed_entry_artifacts",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted_provenance_preserved": True,
        "forbidden_uses": FORBIDDEN_USES,
        "stage_pressure": {
            "ai_confirmed": _safe_int(stage_totals.get("ai_confirmed"), 0),
            "budget_pass": _safe_int(stage_totals.get("budget_pass"), 0),
            "latency_pass": _safe_int(stage_totals.get("latency_pass"), 0),
            "order_bundle_submitted": _safe_int(stage_totals.get("order_bundle_submitted"), 0),
            "blocked_ai_score": _safe_int(stage_totals.get("blocked_ai_score"), 0),
            "first_ai_wait": _safe_int(stage_totals.get("first_ai_wait"), 0),
            "latency_block": _safe_int(stage_totals.get("latency_block"), 0),
            "blocked_liquidity": _safe_int(stage_totals.get("blocked_liquidity"), 0),
            "pre_submit_liquidity_guard_block": _safe_int(
                stage_totals.get("pre_submit_liquidity_guard_block"), 0
            ),
            "blocked_overbought": _safe_int(stage_totals.get("blocked_overbought"), 0),
            "pre_submit_overbought_pullback_guard_block": _safe_int(
                stage_totals.get("pre_submit_overbought_pullback_guard_block"), 0
            ),
            "pre_submit_late_entry_price_drift_guard_block": _safe_int(
                stage_totals.get("pre_submit_late_entry_price_drift_guard_block"), 0
            ),
        },
        "quote_freshness_totals": {
            "refresh_attempted_count": refresh_attempted,
            "refresh_applied_count": refresh_applied,
            "still_latency_blocked_after_refresh_count": still_blocked,
            "latency_pass_recovered_count": recovered,
            "order_bundle_submitted_after_refresh_count": submitted_after_refresh,
            "refresh_subreason_counts": _counter_to_plain(
                quote_totals.get("refresh_subreason_counts")
                if isinstance(quote_totals.get("refresh_subreason_counts"), Counter)
                else Counter()
            ),
            "latency_pass_recovered_downstream_stage_counts": _counter_to_plain(recovered_downstream),
        },
        "recommended_next_actions": actions,
    }


def _overbought_gate_counterfactual(
    *,
    blocker_summary: dict[str, dict[str, Any]],
    window_policy: str,
) -> dict[str, Any]:
    top = _top_overblocking(blocker_summary, OVERBOUGHT_BLOCKER_KEYS)
    blocker_rows = {
        key: row
        for key, row in sorted(blocker_summary.items())
        if key in OVERBOUGHT_BLOCKER_KEYS and isinstance(row, dict)
    }
    evaluated = sum(_safe_int(row.get("evaluated_candidates"), 0) for row in blocker_rows.values())
    missed = sum(_safe_int(row.get("missed_winner_count"), 0) for row in blocker_rows.values())
    avoided = sum(_safe_int(row.get("avoided_loser_count"), 0) for row in blocker_rows.values())
    neutral = sum(_safe_int(row.get("neutral_count"), 0) for row in blocker_rows.values())
    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "entry_hurdle_backtest_report_only",
        "window_policy": window_policy,
        "sample_floor": "report_only_overbought_blocker_sample_floor_3",
        "primary_decision_metric": "missed_winner_vs_avoided_loser_tradeoff",
        "source_quality_gate": "clean_baseline_allowed_existing_missed_entry_counterfactual",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted_provenance_preserved": True,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "blocker_keys": sorted(OVERBOUGHT_BLOCKER_KEYS),
        "evaluated_candidates": evaluated,
        "missed_winner_count": missed,
        "avoided_loser_count": avoided,
        "neutral_count": neutral,
        "missed_winner_rate": round(missed * 100.0 / evaluated, 2) if evaluated else 0.0,
        "avoided_loser_rate": round(avoided * 100.0 / evaluated, 2) if evaluated else 0.0,
        "top_overblocking": top,
        "blocker_tradeoff": blocker_rows,
        "decision": "source_only_recovery_design_candidate" if top else "hold_sample_or_balanced",
        "allowed_next_step": (
            "Use this evidence to design a bounded source-only overbought recovery candidate; "
            "do not relax live overbought guards without a separate runtime apply contract."
        ),
    }


def _code_improvement_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    overbought = (
        summary.get("overbought_gate_counterfactual")
        if isinstance(summary.get("overbought_gate_counterfactual"), dict)
        else {}
    )
    if not overbought or overbought.get("top_overblocking") is None:
        return []
    evidence = [
        f"evaluated_candidates={overbought.get('evaluated_candidates')}",
        f"missed_winner_count={overbought.get('missed_winner_count')}",
        f"avoided_loser_count={overbought.get('avoided_loser_count')}",
        f"missed_winner_rate={overbought.get('missed_winner_rate')}",
        f"avoided_loser_rate={overbought.get('avoided_loser_rate')}",
        "runtime_effect=false",
        "allowed_runtime_apply=false",
        "actual_order_submitted=false",
        "broker_order_forbidden=true",
    ]
    return [
        {
            "order_id": "order_overbought_gate_miss_ev_recovery",
            "title": "overbought gate miss EV recovery",
            "source_report_type": REPORT_TYPE,
            "lifecycle_stage": "entry_submit",
            "target_subsystem": "entry_funnel",
            "route": "existing_family",
            "mapped_family": "overbought_gate_miss_ev_recovery",
            "threshold_family": "overbought_gate_miss_ev_recovery",
            "improvement_type": "source_only_counterfactual_provenance",
            "confidence": "clean_baseline_counterfactual",
            "priority": 2,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "implementation_status": "implemented_source_quality_contract_available",
            "original_implementation_status": "implemented_source_quality_contract_available",
            "implementation_provenance": {
                "implementation_type": "overbought_gate_counterfactual_report_provenance",
                "metric_role": overbought.get("metric_role"),
                "decision_authority": overbought.get("decision_authority"),
                "primary_decision_metric": overbought.get("primary_decision_metric"),
                "source_quality_gate": overbought.get("source_quality_gate"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "requires_separate_runtime_apply_candidate": True,
                "root_cause_closure_status_hint": "implementation_done",
            },
            "expected_ev_effect": (
                "Expose overbought gate missed-winner vs avoided-loser evidence as source-only provenance "
                "before any bounded policy design."
            ),
            "evidence": evidence,
            "source_paths": [str(path) for path in report.get("source_paths") or []],
            "next_postclose_metric": (
                "entry_hurdle_backtest overbought_gate_counterfactual should keep runtime_effect=false and "
                "show missed_winner_vs_avoided_loser_tradeoff."
            ),
            "files_likely_touched": [
                "src/engine/scalping/entry_hurdle_backtest.py",
                "src/engine/build_code_improvement_workorder.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_entry_hurdle_backtest.py src/tests/test_build_code_improvement_workorder.py",
                "runtime_effect remains false; overbought/stale/broker/order/provider/bot guards remain unchanged",
            ],
            "forbidden_uses": FORBIDDEN_USES,
        }
    ]


def build_report(
    target_date: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    candidate_dates = _date_range(start, end)
    source_dates, excluded_dates = filter_allowed_dates(candidate_dates, policy)
    stage_totals: Counter[str] = Counter()
    blocker_totals: dict[str, Counter] = defaultdict(Counter)
    cohort_totals: dict[str, Counter] = defaultdict(Counter)
    quote_totals: dict[str, Counter[str] | int] = {
        "refresh_subreason_counts": Counter(),
        "refresh_block_subreason_counts": Counter(),
        "latency_pass_recovered_downstream_counts": Counter(),
        "latency_pass_recovered_downstream_stage_counts": Counter(),
        "refresh_attempted_count": 0,
        "refresh_applied_count": 0,
        "still_latency_blocked_after_refresh_count": 0,
        "latency_pass_recovered_count": 0,
        "order_bundle_submitted_after_refresh_count": 0,
    }
    date_rows: list[dict[str, Any]] = []
    missing_artifacts: list[dict[str, str]] = []

    for source_date in source_dates:
        buy_path = _buy_funnel_path(source_date)
        missed_path = _missed_entry_path(source_date)
        buy_report = _load_json(buy_path)
        missed_report = _load_json(missed_path)
        if not buy_report:
            missing_artifacts.append({"date": source_date, "artifact": "buy_funnel_sentinel", "path": str(buy_path)})
        if not missed_report:
            missing_artifacts.append({"date": source_date, "artifact": "missed_entry_counterfactual", "path": str(missed_path)})

        stage_unique = _stage_unique(buy_report)
        ratios = _ratios(buy_report)
        for stage, count in stage_unique.items():
            stage_totals[stage] += count

        blocker_rows = _blocker_metrics(missed_report)
        for key, row in blocker_rows.items():
            bucket = blocker_totals[str(key)]
            bucket["evaluated_candidates"] += _safe_int(row.get("evaluated_candidates"), 0)
            bucket["missed_winner_count"] += _safe_int(row.get("missed_winner_count"), 0)
            bucket["avoided_loser_count"] += _safe_int(row.get("avoided_loser_count"), 0)
            bucket["neutral_count"] += _safe_int(row.get("neutral_count"), 0)

        cohort_rows = _cohort_metrics(missed_report)
        for key, row in cohort_rows.items():
            bucket = cohort_totals[str(key)]
            evaluated = _safe_int(row.get("evaluated_candidates"), 0)
            missed = round(_safe_float(row.get("missed_winner_rate"), 0.0) * evaluated / 100.0)
            avoided = round(_safe_float(row.get("avoided_loser_rate"), 0.0) * evaluated / 100.0)
            bucket["evaluated_candidates"] += evaluated
            bucket["missed_winner_count"] += missed
            bucket["avoided_loser_count"] += avoided

        classification = _classification(buy_report)
        quote_freshness = _quote_freshness_attribution(buy_report)
        for key in (
            "refresh_attempted_count",
            "refresh_applied_count",
            "still_latency_blocked_after_refresh_count",
            "latency_pass_recovered_count",
            "order_bundle_submitted_after_refresh_count",
        ):
            quote_totals[key] = _safe_int(quote_totals.get(key), 0) + _safe_int(quote_freshness.get(key), 0)
        for key in (
            "refresh_subreason_counts",
            "refresh_block_subreason_counts",
            "latency_pass_recovered_downstream_counts",
            "latency_pass_recovered_downstream_stage_counts",
        ):
            target_counter = quote_totals.get(key)
            source_counts = quote_freshness.get(key)
            if isinstance(target_counter, Counter) and isinstance(source_counts, dict):
                for label, count in source_counts.items():
                    target_counter[str(label)] += _safe_int(count, 0)

        date_rows.append(
            {
                "date": source_date,
                "buy_funnel_path": str(buy_path),
                "missed_entry_path": str(missed_path),
                "buy_funnel_loaded": bool(buy_report),
                "missed_entry_loaded": bool(missed_report),
                "stage_unique": stage_unique,
                "ratios": ratios,
                "classification_primary": classification.get("primary", "-"),
                "submit_drought_handoff_state": classification.get("submit_drought_handoff_state", "-"),
                "quote_freshness_attribution": quote_freshness,
            }
        )

    blocker_summary = {}
    for key, counter in blocker_totals.items():
        evaluated = _safe_int(counter.get("evaluated_candidates"), 0)
        missed = _safe_int(counter.get("missed_winner_count"), 0)
        avoided = _safe_int(counter.get("avoided_loser_count"), 0)
        row = {
            "evaluated_candidates": evaluated,
            "missed_winner_count": missed,
            "avoided_loser_count": avoided,
            "neutral_count": _safe_int(counter.get("neutral_count"), 0),
            "missed_winner_rate": round(missed * 100.0 / evaluated, 2) if evaluated else 0.0,
            "avoided_loser_rate": round(avoided * 100.0 / evaluated, 2) if evaluated else 0.0,
        }
        row["hurdle_decision"] = _hurdle_decision(row)
        blocker_summary[key] = row

    cohort_summary = {}
    for key, counter in cohort_totals.items():
        evaluated = _safe_int(counter.get("evaluated_candidates"), 0)
        missed = _safe_int(counter.get("missed_winner_count"), 0)
        avoided = _safe_int(counter.get("avoided_loser_count"), 0)
        row = {
            "evaluated_candidates": evaluated,
            "missed_winner_count": missed,
            "avoided_loser_count": avoided,
            "missed_winner_rate": round(missed * 100.0 / evaluated, 2) if evaluated else 0.0,
            "avoided_loser_rate": round(avoided * 100.0 / evaluated, 2) if evaluated else 0.0,
        }
        row["hurdle_decision"] = _hurdle_decision(row)
        cohort_summary[key] = row

    ai_unique = stage_totals.get("ai_confirmed", 0)
    budget_unique = stage_totals.get("budget_pass", 0)
    submitted_unique = stage_totals.get("order_bundle_submitted", 0)
    next_action_diagnostics = _next_action_diagnostics(
        stage_totals=stage_totals,
        blocker_summary=blocker_summary,
        cohort_summary=cohort_summary,
        quote_totals=quote_totals,
        window_policy=f"{start}_to_{end}",
    )
    implemented_policy_backtest = _build_implemented_policy_backtest(
        source_dates=source_dates,
        stage_totals=stage_totals,
        blocker_summary=blocker_summary,
    )
    overbought_gate_counterfactual = _overbought_gate_counterfactual(
        blocker_summary=blocker_summary,
        window_policy=f"{start}_to_{end}",
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "metric_role": "funnel_count",
        "decision_authority": "entry_hurdle_backtest_report_only",
        "window_policy": f"{start}_to_{end}",
        "sample_floor": "report_only_blocker_sample_floor_3",
        "primary_decision_metric": "missed_winner_vs_avoided_loser_tradeoff",
        "source_quality_gate": "clean_baseline_allowed_existing_buy_funnel_and_missed_entry_artifacts",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "excluded_dates": excluded_dates,
        "missing_artifacts": missing_artifacts,
        "summary": {
            "stage_unique_totals": dict(sorted(stage_totals.items())),
            "submitted_to_ai_unique_pct": round(submitted_unique * 100.0 / ai_unique, 2) if ai_unique else 0.0,
            "submitted_to_budget_unique_pct": round(submitted_unique * 100.0 / budget_unique, 2) if budget_unique else 0.0,
            "blocker_tradeoff": blocker_summary,
            "cohort_tradeoff": cohort_summary,
            "next_action_diagnostics": next_action_diagnostics,
            "implemented_policy_backtest": implemented_policy_backtest,
            "overbought_gate_counterfactual": overbought_gate_counterfactual,
        },
        "date_rows": date_rows,
    }
    report["source_paths"] = [
        *(str(row.get("buy_funnel_path")) for row in date_rows if row.get("buy_funnel_loaded")),
        *(str(row.get("missed_entry_path")) for row in date_rows if row.get("missed_entry_loaded")),
    ]
    report["code_improvement_orders"] = _code_improvement_orders(report)
    report["summary"]["code_improvement_order_count"] = len(report["code_improvement_orders"])
    return report


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def build_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Entry Hurdle Backtest {report['date']}",
        "",
        f"- runtime_effect: `{report['runtime_effect']}`",
        f"- source_dates: `{', '.join(report.get('source_dates') or []) or '-'}`",
        f"- submitted/ai unique: `{summary.get('submitted_to_ai_unique_pct', 0.0)}%`",
        f"- submitted/budget unique: `{summary.get('submitted_to_budget_unique_pct', 0.0)}%`",
        f"- missing_artifacts: `{len(report.get('missing_artifacts') or [])}`",
        "",
        "## Implemented Policy Backtest",
    ]
    policy_backtest = (
        summary.get("implemented_policy_backtest")
        if isinstance(summary.get("implemented_policy_backtest"), dict)
        else {}
    )
    total = policy_backtest.get("total") if isinstance(policy_backtest.get("total"), dict) else {}
    liquidity_backtest = (
        policy_backtest.get("liquidity_signature_micro_pressure_relief")
        if isinstance(policy_backtest.get("liquidity_signature_micro_pressure_relief"), dict)
        else {}
    )
    ai_recheck_backtest = (
        policy_backtest.get("ai_score_60_74_strong_bundle_recheck")
        if isinstance(policy_backtest.get("ai_score_60_74_strong_bundle_recheck"), dict)
        else {}
    )
    lines.extend(
        [
            f"- eligible attempts: `{total.get('eligible_attempts', 0)}`",
            f"- unique symbols upper bound: `{total.get('unique_symbols_upper_bound', 0)}`",
            f"- conservative estimated submit success: `{total.get('conservative_estimated_order_submit_success', 0)}`",
            f"- upper bound submit-path reentry: `{total.get('upper_bound_order_submit_path_reentry', 0)}`",
            f"- liquidity relief eligible/success: "
            f"`{liquidity_backtest.get('eligible_attempts', 0)}`/"
            f"`{liquidity_backtest.get('conservative_estimated_order_submit_success', 0)}`",
            f"- AI 60-74 recheck eligible/success: "
            f"`{ai_recheck_backtest.get('eligible_recheck_attempts', 0)}`/"
            f"`{ai_recheck_backtest.get('conservative_estimated_order_submit_success', 0)}`",
            "",
        ]
    )
    lines.extend(
        [
            "## Recommended Next Actions",
        ]
    )
    diagnostics = summary.get("next_action_diagnostics") if isinstance(summary.get("next_action_diagnostics"), dict) else {}
    for item in diagnostics.get("recommended_next_actions") or []:
        lines.append(
            f"- `{item.get('action_id', '-')}`: priority={item.get('priority', '-')}, "
            f"decision={item.get('decision', '-')}, reason={item.get('reason', '-')}"
        )
    if not diagnostics.get("recommended_next_actions"):
        lines.append("- `none`: no overblocking action met the report-only trigger")
    overbought = (
        summary.get("overbought_gate_counterfactual")
        if isinstance(summary.get("overbought_gate_counterfactual"), dict)
        else {}
    )
    lines.extend(
        [
            "",
            "## Overbought Gate Counterfactual",
            f"- decision: `{overbought.get('decision', '-')}`",
            f"- evaluated/missed/avoided: `{overbought.get('evaluated_candidates', 0)}`/"
            f"`{overbought.get('missed_winner_count', 0)}`/"
            f"`{overbought.get('avoided_loser_count', 0)}`",
            f"- missed/avoided rate: `{overbought.get('missed_winner_rate', 0.0)}%`/"
            f"`{overbought.get('avoided_loser_rate', 0.0)}%`",
            f"- runtime_effect: `{overbought.get('runtime_effect')}`",
            f"- code_improvement_orders: `{summary.get('code_improvement_order_count', 0)}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Blocker Tradeoff",
        ]
    )
    for blocker, row in (summary.get("blocker_tradeoff") or {}).items():
        lines.append(
            f"- `{blocker}`: evaluated={row.get('evaluated_candidates', 0)}, "
            f"missed={row.get('missed_winner_rate', 0.0)}%, "
            f"avoided={row.get('avoided_loser_rate', 0.0)}%, "
            f"decision={row.get('hurdle_decision', '-')}"
        )
    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(str(report.get("date") or date.today().isoformat()))
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build report-only entry hurdle backtest.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print", dest="print_stdout", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, start_date=args.start_date, end_date=args.end_date)
    if args.write:
        json_path, md_path = write_outputs(report)
        print(f"Wrote {json_path}")
        print(f"Wrote {md_path}")
    if args.print_stdout or not args.write:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
