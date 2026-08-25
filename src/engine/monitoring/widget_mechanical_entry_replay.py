"""Replay the portable Samsung-widget entry core on exact Entry-AI payloads.

The Samsung-only relative-strength, investor-flow, and external-market axes are
not fabricated for other symbols.  Missing symbol-generic equivalents cap a
portable-core pass at ``ENTRY_CAUTION``.  This module is offline/report-only and
has no runtime, account, order, quantity, provider, or bot authority.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import fmean
from typing import Any

# sniper_config emits a human boot banner while the widget module imports.
# Suppress only that import-time banner so this report CLI keeps stdout as JSON.
with contextlib.redirect_stdout(io.StringIO()):
    from src.engine.monitoring.samsung_widget_advisory import (
        MinuteBar,
        TACTICAL_CHASE_LIMIT_PCT,
        _absorption_recovery_confirmation,
        _live_reversal_veto,
        _session_vwap,
        _spread_tick_count,
        _structure_features,
        _volume_confirmation,
        analyze_trends,
    )
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.scalping.ai_decision_trace import replay_source_input
from src.trading.order.tick_utils import (
    clamp_price_to_tick,
    move_price_by_ticks,
)
from src.utils.jsonl_io import iter_jsonl_objects_strict, read_json_object_strict

DEFAULT_PAYLOAD_DIR = Path("data/ai_decision_payloads")
DEFAULT_LABEL_DIR = Path("data/report/ai_decision_outcome_labels")
DEFAULT_OUTPUT_DIR = Path("data/report/widget_mechanical_entry_replay")
ACTIONABLE_STATES = {"ENTRY_CAUTION", "ENTRY_READY"}
DECISIVE_HITS = {"target_first", "adverse_first"}
SESSION_MINIMUM_BARS = {
    "NXT_PREMARKET": 10,
    "KRX_REGULAR": 3,
    "NXT_AFTERMARKET": 5,
}

METRIC_CONTRACT = {
    "metric_role": "counterfactual_observation",
    "decision_authority": "offline_widget_mechanical_replay_only",
    "window_policy": "exact_entry_ai_payload_same_timestamp_venue_session_10m",
    "sample_floor": "60_coverage_qualified_trading_days_before_runtime_judgment",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_replay_payload_fresh_completed_1m_bbo_previous_day_and_mature_10m_label"
    ),
    "forbidden_uses": [
        "real_order_submission",
        "live_entry_ai_replacement",
        "automatic_threshold_or_runtime_apply",
        "provider_or_bot_change",
        "broker_account_order_quantity_or_cooldown_bypass",
        "hard_safety_bypass",
        "counterfactual_realized_pnl_merge",
    ],
}


def _positive_int(value: object) -> int | None:
    try:
        parsed = abs(int(float(str(value).replace(",", "").strip())))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _aware_kst(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        rows = list(iter_jsonl_objects_strict(path))
    except FileNotFoundError:
        return []
    for line_number, row in enumerate(rows, start=1):
        row["_line_number"] = line_number
    return rows


def _load_labels(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = read_json_object_strict(path)
    except FileNotFoundError:
        return {}
    labels = payload.get("labels") if isinstance(payload, dict) else None
    if not isinstance(labels, list):
        return {}
    return {
        str(row.get("decision_trace_id")): row
        for row in labels
        if isinstance(row, dict) and row.get("decision_trace_id")
    }


def _session_name(effective_venue: str, session_bucket: str) -> str | None:
    normalized_venue = effective_venue.upper()
    normalized_bucket = session_bucket.lower()
    if normalized_venue == "PREMARKET_KRX_LIKE" or "premarket" in normalized_bucket:
        return "NXT_PREMARKET"
    if normalized_venue == "KRX" or normalized_bucket in {
        "krx",
        "regular",
        "krx_regular",
    }:
        return "KRX_REGULAR"
    if normalized_venue in {"NXT", "NXT_AFTERMARKET"} and (
        "after" in normalized_bucket or "nxt" in normalized_bucket
    ):
        return "NXT_AFTERMARKET"
    return None


def _minute_bars(context: dict[str, Any], *, decision_ts: datetime) -> list[MinuteBar]:
    raw_bars = context.get("bars")
    if not isinstance(raw_bars, list):
        return []
    bars: list[MinuteBar] = []
    for row in raw_bars:
        if not isinstance(row, dict) or row.get("forming") is True:
            continue
        time_text = str(row.get("t") or "")
        try:
            hour, minute = (int(part) for part in time_text.split(":", 1))
            source_time = decision_ts.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            ).strftime("%Y%m%d%H%M%S")
            values = {key: _positive_int(row.get(key)) for key in ("o", "h", "l", "c")}
            volume = int(float(str(row.get("v") or 0)))
        except (TypeError, ValueError):
            continue
        if any(value is None for value in values.values()) or volume < 0:
            continue
        bars.append(
            MinuteBar(
                source_time=source_time,
                open=int(values["o"]),
                high=int(values["h"]),
                low=int(values["l"]),
                close=int(values["c"]),
                volume=volume,
            )
        )
    return sorted(bars, key=lambda bar: bar.source_time)


def _source_issue(
    payload_row: dict[str, Any],
    exact_payload: dict[str, Any],
    context: dict[str, Any],
    bars: list[MinuteBar],
    session_name: str | None,
) -> str | None:
    if payload_row.get("replay_exact") is not True:
        return "payload_not_exact_replay"
    if payload_row.get("replay_context_present") is True and (
        payload_row.get("replay_context_exact") is not True
    ):
        return "payload_not_exact_replay"
    if session_name is None:
        return "session_not_portable"
    if context.get("schema") != "entry_candle_context_v1":
        return "entry_context_schema_mismatch"
    source_quality = context.get("source_quality")
    if not isinstance(source_quality, dict) or source_quality.get("status") != (
        "fresh_consistent"
    ):
        return "entry_context_not_fresh_consistent"
    if len(bars) < SESSION_MINIMUM_BARS[session_name]:
        return "minimum_completed_bars_not_met"
    if len(bars) < 6:
        return "portable_structure_minimum_bars_not_met"
    quote = exact_payload.get("quote")
    if not isinstance(quote, dict) or quote.get("quote_stale") is not False:
        return "quote_missing_or_stale"
    if not _positive_int(quote.get("best_bid")) or not _positive_int(
        quote.get("best_ask")
    ):
        return "bbo_missing"
    multi = context.get("multi_timeframe_context")
    previous = multi.get("previous_day_levels") if isinstance(multi, dict) else None
    if not isinstance(previous, dict) or (
        (previous.get("source_quality") or "").lower() != "pass"
    ):
        return "previous_day_levels_missing"
    return None


def evaluate_portable_widget_core(payload_row: dict[str, Any]) -> dict[str, Any]:
    """Evaluate only widget axes available unchanged for arbitrary symbols."""
    user_input = replay_source_input(payload_row)
    exact_payload = (
        user_input.get("exact_payload") if isinstance(user_input, dict) else None
    )
    if not isinstance(exact_payload, dict):
        return {"state": "DATA_WAIT", "source_issue": "exact_payload_missing"}
    context = exact_payload.get("entry_candle_context")
    if not isinstance(context, dict):
        return {"state": "DATA_WAIT", "source_issue": "entry_context_missing"}
    multi_timeframe = context.get("multi_timeframe_context")
    decision_ts = _aware_kst(
        multi_timeframe.get("captured_at")
        if isinstance(multi_timeframe, dict)
        else None
    ) or _aware_kst(payload_row.get("captured_at"))
    if decision_ts is None:
        return {"state": "DATA_WAIT", "source_issue": "decision_time_missing"}
    session_name = _session_name(
        str(payload_row.get("effective_venue") or context.get("venue") or ""),
        str(payload_row.get("session_bucket") or context.get("session") or ""),
    )
    bars = _minute_bars(context, decision_ts=decision_ts)
    source_issue = _source_issue(
        payload_row, exact_payload, context, bars, session_name
    )
    if source_issue:
        return {
            "state": "DATA_WAIT",
            "source_issue": source_issue,
            "completed_bar_count": len(bars),
            "session": session_name,
        }

    current = exact_payload.get("current")
    quote = exact_payload.get("quote")
    top1 = exact_payload.get("orderbook_top1")
    current_price = _positive_int(
        current.get("price") if isinstance(current, dict) else 0
    )
    best_bid = _positive_int(quote.get("best_bid"))
    best_ask = _positive_int(quote.get("best_ask"))
    if current_price is None or best_bid is None or best_ask is None:
        return {"state": "DATA_WAIT", "source_issue": "price_or_bbo_missing"}

    bbo = {
        "best_bid": best_bid,
        "best_ask": best_ask,
        "best_bid_qty": _positive_int(
            ((top1.get("bid") or {}).get("volume")) if isinstance(top1, dict) else None
        ),
        "best_ask_qty": _positive_int(
            ((top1.get("ask") or {}).get("volume")) if isinstance(top1, dict) else None
        ),
    }
    structure = _structure_features(bars)
    vwap = _session_vwap(bars)
    trend_details = analyze_trends(bars, session_name=session_name or "KRX_REGULAR")
    trends = {
        key: str(value.get("state") or "unavailable")
        for key, value in trend_details.items()
    }
    live_reversal_veto, live_reversal = _live_reversal_veto(
        current_price=current_price,
        bars=bars,
        bbo=bbo,
        trend_details=trend_details,
    )
    raw_support = structure.get("confirmed_support")
    structural_support = (
        clamp_price_to_tick(int(raw_support))
        if isinstance(raw_support, int) and raw_support > 0
        else None
    )
    result: dict[str, Any] = {
        "state": "WATCH",
        "session": session_name,
        "source_issue": None,
        "current_price": current_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "completed_bar_count": len(bars),
        "structural_support": structural_support,
        "support_confirmation": structure.get("support_confirmation"),
        "session_vwap": vwap,
        "trend_3m": trends.get("3m"),
        "trend_5m": trends.get("5m"),
        "entry_price_low": None,
        "entry_price_high": None,
        "candidate_before_spread_gate": False,
        "portable_context_limitations": [
            "symbol_generic_relative_strength_unavailable",
            "symbol_generic_investor_flow_unavailable",
            "external_market_context_not_replayed",
        ],
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if structural_support is None:
        result["unmet_conditions"] = ["confirmed_support_missing"]
        return result

    hard_invalidation = move_price_by_ticks(structural_support, -2)
    completed_close_break = bars[-1].close < structural_support
    deep_live_break = bool(current_price <= hard_invalidation and live_reversal_veto)
    result["invalidation_price"] = hard_invalidation
    result["completed_close_break"] = completed_close_break
    result["deep_live_break"] = deep_live_break
    if completed_close_break or deep_live_break:
        result["state"] = "AVOID"
        result["unmet_conditions"] = ["confirmed_support_broken"]
        return result
    if current_price < structural_support:
        result["state"] = "WATCH"
        result["unmet_conditions"] = ["soft_support_break"]
        return result

    recent_resistance = structure.get("recent_resistance")
    structure_ok = bool(structure["higher_high_and_low"] or structure["retest_held"])
    vwap_reclaimed = bool(vwap and current_price >= vwap)
    resistance_reclaimed = bool(
        isinstance(recent_resistance, int)
        and recent_resistance > 0
        and current_price >= recent_resistance
        and structure_ok
    )
    reclaim_ok = vwap_reclaimed or resistance_reclaimed
    tactical_candidates = [
        value
        for value in (
            structural_support,
            vwap if vwap_reclaimed else None,
            (
                recent_resistance
                if resistance_reclaimed and not vwap_reclaimed
                else None
            ),
        )
        if isinstance(value, int) and 0 < value <= current_price
    ]
    tactical_support = (
        clamp_price_to_tick(max(tactical_candidates)) if tactical_candidates else None
    )
    if tactical_support is None:
        result["unmet_conditions"] = ["tactical_support_missing"]
        return result
    trends_ok = trends.get("3m") in {"up", "flat"} and trends.get("5m") in {
        "up",
        "flat",
    }
    volume_ok, volume_meta = _volume_confirmation(bars)
    absorption_ok = _absorption_recovery_confirmation(
        volume_meta=volume_meta,
        structure=structure,
        completed_close=bars[-1].close,
        vwap=vwap,
        recent_resistance=recent_resistance,
        reclaim_ok=reclaim_ok,
        trends_ok=trends_ok,
    )
    volume_ok = volume_ok or absorption_ok
    spread_ticks = _spread_tick_count(best_bid, best_ask)
    portable_core_checks = {
        "low_structure_confirmed": structure_ok,
        "vwap_or_resistance_reclaimed": reclaim_ok,
        "rebound_volume_confirmed": volume_ok,
        "three_five_minute_not_down": trends_ok,
        "live_reversal_clear": not live_reversal_veto,
    }
    checks = {
        **portable_core_checks,
        "spread_within_two_ticks": spread_ticks <= 2,
    }
    result.update(
        {
            "tactical_support": tactical_support,
            "recent_resistance": recent_resistance,
            "spread_ticks": spread_ticks,
            "live_reversal": live_reversal,
            "checks": checks,
            "unmet_conditions": [key for key, value in checks.items() if not value],
        }
    )
    if not all(portable_core_checks.values()):
        return result

    if (
        resistance_reclaimed
        and not vwap_reclaimed
        and isinstance(recent_resistance, int)
        and current_price > move_price_by_ticks(recent_resistance, 1)
    ):
        result["state"] = "WATCH"
        result["unmet_conditions"] = ["resistance_reclaim_pullback_pending"]
        return result

    chase_pct = ((current_price - tactical_support) / tactical_support) * 100
    result["tactical_chase_pct"] = round(chase_pct, 6)
    two_tick_chase_limit_pct = (
        (move_price_by_ticks(tactical_support, 2) - tactical_support) / tactical_support
    ) * 100
    dynamic_chase_limit_pct = max(TACTICAL_CHASE_LIMIT_PCT, two_tick_chase_limit_pct)
    result["dynamic_chase_limit_pct"] = round(dynamic_chase_limit_pct, 6)
    if chase_pct > dynamic_chase_limit_pct:
        result["state"] = "NO_CHASE"
        result["unmet_conditions"] = ["price_above_dynamic_two_tick_chase_limit"]
        return result
    entry_low = max(tactical_support, best_bid)
    entry_high = min(best_ask, move_price_by_ticks(tactical_support, 2))
    if entry_high < entry_low:
        result["state"] = "NO_CHASE"
        result["unmet_conditions"] = ["entry_range_not_available_without_chasing"]
        return result
    result["candidate_before_spread_gate"] = True
    result["entry_price_low"] = entry_low
    result["entry_price_high"] = entry_high
    if spread_ticks > 2:
        result["state"] = "WATCH"
        result["unmet_conditions"] = ["spread_within_two_ticks"]
        return result
    result["state"] = "ENTRY_CAUTION"
    result["unmet_conditions"] = list(result["portable_context_limitations"])
    return result


def _cohort_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hits = Counter(str(row.get("entry_path_first_hit") or "missing") for row in rows)
    decisive = sum(hits[hit] for hit in DECISIVE_HITS)
    target_first = hits["target_first"]
    end_returns = [
        float(row["end_return_pct"])
        for row in rows
        if isinstance(row.get("end_return_pct"), (int, float))
    ]
    return {
        "sample_count": len(rows),
        "unique_stock_count": len({str(row.get("stock_code")) for row in rows}),
        "hit_counts": dict(sorted(hits.items())),
        "decisive_sample_count": decisive,
        "diagnostic_target_first_rate_pct": (
            round((target_first / len(rows)) * 100, 6) if rows else None
        ),
        "diagnostic_target_share_among_decisive_pct": (
            round((target_first / decisive) * 100, 6) if decisive else None
        ),
        "equal_weight_avg_profit_pct": (
            round(fmean(end_returns), 6) if end_returns else None
        ),
        "source_quality_adjusted_ev_pct": (
            round(fmean(end_returns), 6) if end_returns else None
        ),
    }


def _dedupe_mechanical_episodes(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Collapse repeated same-symbol/range decisions within one minute."""
    accepted: list[dict[str, Any]] = []
    last_seen: dict[tuple[str, str, int, int], datetime] = {}
    duplicate_count = 0
    for row in sorted(rows, key=lambda value: str(value.get("decision_ts") or "")):
        observed_at = _aware_kst(row.get("decision_ts"))
        if observed_at is None:
            accepted.append(row)
            continue
        key = (
            str(row.get("stock_code") or ""),
            str(row.get("effective_venue") or ""),
            int(row.get("mechanical_entry_price_low") or 0),
            int(row.get("mechanical_entry_price_high") or 0),
        )
        previous = last_seen.get(key)
        last_seen[key] = observed_at
        if previous is not None and (observed_at - previous).total_seconds() <= 60:
            duplicate_count += 1
            continue
        accepted.append(row)
    return accepted, duplicate_count


def build_report(
    payload_rows: list[dict[str, Any]],
    labels_by_trace: dict[str, dict[str, Any]],
    *,
    target_date: date,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    join_excluded = Counter()
    source_issues = Counter()
    for payload_row in payload_rows:
        if payload_row.get("endpoint") != "analyze_target":
            continue
        request_id = str(payload_row.get("request_id") or "")
        label = labels_by_trace.get(request_id)
        if not label:
            join_excluded["outcome_label_missing"] += 1
            continue
        horizon = (label.get("horizon_metrics") or {}).get("10m")
        if (
            label.get("decision_stage") != "entry_screen"
            or label.get("label_status") != "mature"
            or label.get("primary_cohort_eligible") is not True
            or not isinstance(horizon, dict)
            or horizon.get("entry_path_first_hit")
            not in {
                "target_first",
                "adverse_first",
                "same_bar_ambiguous",
                "neither_hit",
            }
        ):
            join_excluded["mature_primary_10m_outcome_unavailable"] += 1
            continue
        mechanical = evaluate_portable_widget_core(payload_row)
        if mechanical.get("source_issue"):
            source_issues[str(mechanical["source_issue"])] += 1
        reference_price = _positive_int(label.get("reference_price"))
        entry_low = _positive_int(mechanical.get("entry_price_low"))
        entry_high = _positive_int(mechanical.get("entry_price_high"))
        mechanical_signal = mechanical.get("state") in ACTIONABLE_STATES
        candidate_before_spread = mechanical.get("candidate_before_spread_gate") is True
        price_comparable = bool(
            candidate_before_spread
            and reference_price
            and entry_low
            and entry_high
            and entry_low <= reference_price <= entry_high
        )
        row = {
            "decision_trace_id": request_id,
            "decision_ts": label.get("decision_ts"),
            "stock_code": label.get("stock_code"),
            "effective_venue": label.get("effective_venue"),
            "session_bucket": label.get("session_bucket"),
            "payload_sha256": payload_row.get("payload_sha256"),
            "ai_action": label.get("action"),
            "ai_score": label.get("score"),
            "ai_confidence": label.get("confidence"),
            "mechanical_state": mechanical.get("state"),
            "mechanical_signal": mechanical_signal,
            "mechanical_candidate_before_spread_gate": candidate_before_spread,
            "mechanical_price_comparable": price_comparable,
            "mechanical_entry_price_low": entry_low,
            "mechanical_entry_price_high": entry_high,
            "reference_price": reference_price,
            "mechanical_spread_ticks": mechanical.get("spread_ticks"),
            "mechanical_unmet_conditions": mechanical.get("unmet_conditions", []),
            "mechanical_source_issue": mechanical.get("source_issue"),
            "entry_path_first_hit": horizon.get("entry_path_first_hit"),
            "mfe_pct": horizon.get("mfe_pct"),
            "mae_pct": horizon.get("mae_pct"),
            "end_return_pct": horizon.get("end_return_pct"),
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        rows.append(row)

    ai_buy = [row for row in rows if row["ai_action"] == "BUY"]
    ai_block = [row for row in rows if row["ai_action"] in {"WAIT", "DROP"}]
    mechanical_signals_raw = [
        row
        for row in rows
        if row["mechanical_signal"] and row["mechanical_price_comparable"]
    ]
    mechanical_signals, mechanical_episode_duplicate_count = (
        _dedupe_mechanical_episodes(mechanical_signals_raw)
    )
    pre_spread_candidates_raw = [
        row for row in rows if row["mechanical_candidate_before_spread_gate"]
    ]
    pre_spread_candidates, pre_spread_episode_duplicate_count = (
        _dedupe_mechanical_episodes(pre_spread_candidates_raw)
    )
    pre_spread_price_comparable = [
        row
        for row in pre_spread_candidates
        if row["mechanical_candidate_before_spread_gate"]
        and row["mechanical_price_comparable"]
    ]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        mechanical_action = "SIGNAL" if row["mechanical_signal"] else "BLOCK"
        groups[f"AI_{row['ai_action']}__MECHANICAL_{mechanical_action}"].append(row)
    spread_sensitivity = {}
    for max_ticks in (2, 3, 5, 10, 20):
        cohort = [
            row
            for row in pre_spread_candidates
            if isinstance(row.get("mechanical_spread_ticks"), int)
            and row["mechanical_spread_ticks"] <= max_ticks
        ]
        spread_sensitivity[f"max_{max_ticks}_ticks"] = _cohort_summary(cohort)
    symbol_cohorts: dict[str, dict[str, Any]] = {}
    for stock_code in sorted({str(row.get("stock_code") or "") for row in rows}):
        if not stock_code:
            continue
        stock_rows = [row for row in rows if str(row.get("stock_code")) == stock_code]
        stock_signals = [row for row in stock_rows if row["mechanical_signal"]]
        stock_candidates = [
            row for row in stock_rows if row["mechanical_candidate_before_spread_gate"]
        ]
        symbol_cohorts[stock_code] = {
            "all_joined_rows": _cohort_summary(stock_rows),
            "mechanical_signals": _cohort_summary(stock_signals),
            "candidates_before_spread": _cohort_summary(stock_candidates),
            "mechanical_state_counts": dict(
                sorted(
                    Counter(str(row["mechanical_state"]) for row in stock_rows).items()
                )
            ),
            "blocker_counts": dict(
                sorted(
                    Counter(
                        str(reason)
                        for row in stock_rows
                        for reason in row.get("mechanical_unmet_conditions", [])
                    ).items()
                )
            ),
        }

    return {
        "schema": "widget_mechanical_entry_replay_v1",
        "status": "observed" if rows else "no_comparable_rows",
        "target_date": target_date.isoformat(),
        "generated_at": datetime.now(KST).isoformat(),
        "portable_core_policy": {
            "reused_unchanged": [
                "completed_1m_structure",
                "session_vwap",
                "rebound_volume_or_absorption",
                "three_five_minute_trend",
                "fresh_bbo_spread_within_two_ticks",
                "live_negative_reversal_veto",
                "dynamic_thirty_bp_or_two_tick_chase_limit",
                "dynamic_two_tick_entry_range",
                "support_break_confirmation",
                "vwap_or_confirmed_resistance_reclaim",
            ],
            "not_fabricated": [
                "samsung_vs_sk_hynix_and_kospi_relative_strength",
                "samsung_foreign_and_program_flow",
                "yahoo_nq_mu_usdkrw_external_risk",
            ],
            "limitation_policy": "portable_core_pass_capped_at_ENTRY_CAUTION",
            "promotion_filter_replayed": False,
            "promotion_filter_reason": (
                "AI calls are event-spaced snapshots, not consecutive 10-second widget cycles"
            ),
            "recovery_episode_filter_replayed": False,
            "recovery_episode_filter_reason": (
                "AI calls do not provide a contiguous per-symbol completed-minute sequence "
                "for arm, reclaim, and pullback state continuity"
            ),
        },
        "source": {
            "payload_row_count": len(payload_rows),
            "joined_mature_primary_10m_count": len(rows),
            "join_excluded_counts": dict(sorted(join_excluded.items())),
            "joined_row_source_issue_counts": dict(sorted(source_issues.items())),
        },
        "summary": {
            "ai_buy": _cohort_summary(ai_buy),
            "ai_wait_drop": _cohort_summary(ai_block),
            "mechanical_signal_executable_comparable": _cohort_summary(
                mechanical_signals
            ),
            "mechanical_candidate_before_spread_executable_comparable": (
                _cohort_summary(pre_spread_price_comparable)
            ),
            "mechanical_candidate_before_spread_ai_ask_proxy": _cohort_summary(
                pre_spread_candidates
            ),
            "spread_tick_sensitivity_ai_ask_proxy": spread_sensitivity,
            "stock_code_cohorts": symbol_cohorts,
            "mechanical_signal_raw_count": sum(
                row["mechanical_signal"] for row in rows
            ),
            "mechanical_signal_episode_duplicate_count": (
                mechanical_episode_duplicate_count
            ),
            "mechanical_signal_price_noncomparable_count": sum(
                row["mechanical_signal"] and not row["mechanical_price_comparable"]
                for row in rows
            ),
            "mechanical_candidate_before_spread_raw_count": sum(
                row["mechanical_candidate_before_spread_gate"] for row in rows
            ),
            "mechanical_candidate_before_spread_episode_duplicate_count": (
                pre_spread_episode_duplicate_count
            ),
            "mechanical_candidate_before_spread_price_noncomparable_count": sum(
                row["mechanical_candidate_before_spread_gate"]
                and not row["mechanical_price_comparable"]
                for row in rows
            ),
            "agreement_groups": {
                key: _cohort_summary(value) for key, value in sorted(groups.items())
            },
        },
        "rows": rows,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# Widget mechanical Entry-AI replay — {report['target_date']}",
        "",
        "- authority: `offline_widget_mechanical_replay_only`",
        "- runtime_effect: `false`",
        "- actual_order_submitted: `false`",
        "- outcome: 10m tight entry path (`+0.3% / -0.7%`)",
        "",
        "| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, key in (
        ("AI BUY", "ai_buy"),
        ("AI WAIT/DROP", "ai_wait_drop"),
        (
            "Mechanical signal (price-comparable)",
            "mechanical_signal_executable_comparable",
        ),
        (
            "Mechanical candidate before spread gate (price-comparable)",
            "mechanical_candidate_before_spread_executable_comparable",
        ),
        (
            "Mechanical candidate before spread gate (AI-ask proxy)",
            "mechanical_candidate_before_spread_ai_ask_proxy",
        ),
    ):
        row = summary[key]
        hits = row["hit_counts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    str(row["sample_count"]),
                    str(row["unique_stock_count"]),
                    str(hits.get("target_first", 0)),
                    str(hits.get("adverse_first", 0)),
                    str(row["diagnostic_target_first_rate_pct"]),
                    str(row["diagnostic_target_share_among_decisive_pct"]),
                    str(row["equal_weight_avg_profit_pct"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Stock-code cohorts",
            "",
            "Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.",
            "",
            "| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for stock_code, cohort in summary.get("stock_code_cohorts", {}).items():
        if (
            cohort["mechanical_signals"]["sample_count"] == 0
            and cohort["candidates_before_spread"]["sample_count"] == 0
        ):
            continue
        joined = cohort["all_joined_rows"]
        hits = joined["hit_counts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    stock_code,
                    str(joined["sample_count"]),
                    str(cohort["mechanical_signals"]["sample_count"]),
                    str(cohort["candidates_before_spread"]["sample_count"]),
                    str(hits.get("target_first", 0)),
                    str(hits.get("adverse_first", 0)),
                    str(joined["equal_weight_avg_profit_pct"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Scope limits",
            "",
            "Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.",
            "",
            "The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.",
            "",
            "This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--payload-dir", type=Path, default=DEFAULT_PAYLOAD_DIR)
    parser.add_argument("--label-dir", type=Path, default=DEFAULT_LABEL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def build_report_for_date(
    target_date: date,
    *,
    payload_dir: Path = DEFAULT_PAYLOAD_DIR,
    label_dir: Path = DEFAULT_LABEL_DIR,
) -> dict[str, Any]:
    return build_report(
        _load_jsonl(payload_dir / f"ai_decision_payloads_{target_date}.jsonl"),
        _load_labels(label_dir / f"ai_decision_outcome_labels_{target_date}.json"),
        target_date=target_date,
    )


def write_report(
    report: dict[str, Any],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    target_date = date.fromisoformat(str(report.get("target_date") or ""))
    stem = f"widget_mechanical_entry_replay_{target_date}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_date = date.fromisoformat(args.target_date)
    report = build_report_for_date(
        target_date,
        payload_dir=args.payload_dir,
        label_dir=args.label_dir,
    )
    if args.write:
        write_report(report, output_dir=args.output_dir)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
