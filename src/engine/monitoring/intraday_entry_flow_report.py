from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENTRY_PIPELINE = "ENTRY_PIPELINE"
KST = timezone(timedelta(hours=9))

BUY_SIGNAL_STAGES = {
    "entry_armed",
    "budget_pass",
    "score_buy_candidate",
    "entry_price_resolved",
    "scalp_entry_action_decision_snapshot",
    "latency_pass",
}
SUBMIT_STAGE_MARKERS = ("submitted", "order_send", "broker_submit", "buy_submit")
RISING_MISSED_FORCED_ENTRY_REASON = "rising_missed_one_share_entry"
RISING_MISSED_FORCED_ENTRY_STAGES = {
    "rising_missed_one_share_entry",
    "rising_missed_one_share_entry_order_plan_forced",
}
RISING_MISSED_FORCED_LINEAGE_WINDOW_SEC = 180
RISING_MISSED_FORCED_LINEAGE_STAGES = {
    "entry_cancel_wait_attribution",
    "order_leg_request",
    "order_leg_sent",
    "latency_pass",
    "order_bundle_submitted",
    "buy_signal_telegram_enqueued",
    "scalp_entry_action_decision_snapshot",
    "position_rebased_after_fill",
    "holding_started",
}
STALE_EVAL_QUOTE_AGE_MS = 3000.0
STALE_WEAK_BORDERLINE_QUOTE_AGE_MS = 5000.0
STALE_WEAK_MODERATE_QUOTE_AGE_MS = 10000.0
STALE_WEAK_SEVERE_QUOTE_AGE_MS = 20000.0
STALE_WEAK_RECHECK_DELTA_PCT = 3.0
LATENCY_DANGER_SPREAD_RATIO_CAP = 0.0100
LATENCY_DANGER_WS_AGE_MS_CAP = 450.0
STALE_WEAK_REASON = "stale_quote_with_weak_ai_or_strength"
LATENCY_DANGER_REASON = "latency_state_danger"
FRESH_REFRESH_REASONS = {
    "input_snapshot_fresh",
    "latest_ws_snapshot_fresh",
    "rest_orderbook_fresh",
    "observer_quote_fresh",
    "ws_snapshot_arrived_after_subscription_recheck",
    "rest_quote_applied",
}


def _parse_ts(value: Any, *, target_date: str | None = None) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is not None:
            return parsed.astimezone(KST).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass
    if target_date and len(text.split(":")) in {2, 3}:
        time_text = text if len(text.split(":")) == 3 else f"{text}:00"
        try:
            return datetime.fromisoformat(f"{target_date}T{time_text}")
        except ValueError:
            return None
    return None


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _field(fields: dict[str, Any], key: str, default: str = "") -> str:
    value = fields.get(key, default)
    return "" if value is None else str(value)


def _reason(fields: dict[str, Any]) -> str:
    for key in ("reason", "skip_reason", "blocked_reason", "eviction_reason", "terminal_reason", "entry_submit_revalidation_warning"):
        value = _field(fields, key)
        if value:
            return value
    return ""


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_rising_missed_forced_one_share_entry(stage: str, fields: dict[str, Any]) -> bool:
    reason = str(fields.get("forced_entry_reason") or "").strip()
    forced = _boolish(fields.get("rising_missed_one_share_entry_forced"))
    qty = _safe_float(fields.get("forced_entry_qty"))
    forced_scout_qty_or_missing = qty is None or qty > 0.0
    stage_forced = stage in RISING_MISSED_FORCED_ENTRY_STAGES
    return forced_scout_qty_or_missing and (stage_forced or reason == RISING_MISSED_FORCED_ENTRY_REASON or forced)


def _forced_lineage_qty_present(fields: dict[str, Any]) -> bool:
    for key in ("forced_entry_qty", "order_requested_qty", "order_quantity", "quantity", "qty", "fill_qty", "order_filled_qty"):
        value = _safe_float(fields.get(key))
        if value is not None and value > 0.0:
            return True
    return False


def _is_rising_missed_forced_lineage_row(
    row: dict[str, Any],
    latest_forced_scout_at_by_code: dict[str, datetime],
) -> bool:
    code = str(row.get("stock_code") or "").strip()
    forced_at = latest_forced_scout_at_by_code.get(code)
    event_at = _parse_ts(row.get("emitted_at"))
    if forced_at is None or event_at is None:
        return False
    elapsed_sec = (event_at - forced_at).total_seconds()
    if elapsed_sec < 0 or elapsed_sec > RISING_MISSED_FORCED_LINEAGE_WINDOW_SEC:
        return False
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    actual_submitted = str(fields.get("actual_order_submitted") or "").strip().lower() == "true"
    return stage in RISING_MISSED_FORCED_LINEAGE_STAGES or actual_submitted or _forced_lineage_qty_present(fields)


def _fresh_refresh_age_ms(fields: dict[str, Any]) -> float | None:
    if _boolish(fields.get("refresh_applied")):
        reason = str(fields.get("refresh_reason") or "").strip()
        if not reason or reason in FRESH_REFRESH_REASONS:
            age = _safe_float(fields.get("refresh_age_ms"))
            return 0.0 if age is None else age
    for applied_key, reason_key, age_key in (
        (
            "pre_ai_ws_snapshot_refresh_applied",
            "pre_ai_ws_snapshot_refresh_reason",
            "pre_ai_ws_snapshot_refresh_age_ms",
        ),
        (
            "pre_submit_ws_snapshot_refresh_applied",
            "pre_submit_ws_snapshot_refresh_reason",
            "pre_submit_ws_snapshot_refresh_age_ms",
        ),
        (
            "pre_submit_rest_orderbook_refresh_applied",
            "pre_submit_rest_orderbook_refresh_reason",
            "pre_submit_rest_orderbook_refresh_age_ms",
        ),
        (
            "pre_submit_quote_refresh_applied",
            "pre_submit_quote_refresh_reason",
            "pre_submit_quote_refresh_quote_age_ms",
        ),
    ):
        if not _boolish(fields.get(applied_key)):
            continue
        reason = str(fields.get(reason_key) or "").strip()
        if reason and reason not in FRESH_REFRESH_REASONS:
            continue
        age = _safe_float(fields.get(age_key))
        return 0.0 if age is None else age
    return None


def _stale_eval_category(stage: str, reason: str, fields: dict[str, Any], quote_age_ms: float | None) -> str:
    refresh_age_ms = _fresh_refresh_age_ms(fields)
    if refresh_age_ms is not None and refresh_age_ms <= STALE_EVAL_QUOTE_AGE_MS:
        return "fresh_refresh_recovered"
    text = f"{stage} {reason} {_field(fields, 'entry_submit_revalidation_warning')}".lower()
    if "stale_context_or_quote" in text:
        return "pre_submit_stale_context_or_quote"
    if "ws_snapshot_missing_or_zero" in text or "missing_or_zero_curr" in text:
        return "ws_snapshot_missing_or_zero"
    if "stale_ws_snapshot" in text:
        return "pre_ai_or_fast_precheck_stale_ws"
    if quote_age_ms is not None and quote_age_ms > STALE_EVAL_QUOTE_AGE_MS:
        return "diagnostic_quote_age_stale"
    return ""


def _latency_danger_cause(fields: dict[str, Any]) -> str:
    reason_text = str(fields.get("latency_danger_reasons") or fields.get("latency_reason") or "").lower()
    stale_values = (
        fields.get("pre_submit_effective_quote_stale"),
        fields.get("quote_stale_at_submit"),
        fields.get("quote_stale"),
    )
    if any(_boolish(value) for value in stale_values) or "quote_stale" in reason_text:
        return "quote_stale"
    if "spread_too_wide" in reason_text:
        return "spread_too_wide"
    spread_ratio = _safe_float(fields.get("spread_ratio") or fields.get("pre_submit_quote_refresh_spread_ratio"))
    if spread_ratio is not None and spread_ratio > LATENCY_DANGER_SPREAD_RATIO_CAP:
        return "spread_too_wide"
    spread_ticks = _safe_float(fields.get("orderbook_micro_spread_ticks"))
    bucket = str(fields.get("orderbook_micro_ofi_bucket_key") or fields.get("orderbook_micro_calibration_bucket") or "")
    if (spread_ticks is not None and spread_ticks >= 5.0) or "spread=wide" in bucket:
        return "spread_microstructure_wide"
    ws_age_ms = _safe_float(
        fields.get("ws_age_ms")
        or fields.get("pre_submit_effective_quote_age_ms")
        or fields.get("pre_submit_ws_snapshot_refresh_age_ms")
    )
    if (ws_age_ms is not None and ws_age_ms > LATENCY_DANGER_WS_AGE_MS_CAP) or "ws_age_too_high" in reason_text:
        return "ws_age_too_high"
    return "other_danger"


def _latency_danger_event(fields: dict[str, Any]) -> dict[str, Any]:
    cause = str(fields.get("latency_root_cause") or "").strip() or _latency_danger_cause(fields)
    return {
        "cause": cause,
        "spread_ratio": _safe_float(fields.get("spread_ratio") or fields.get("pre_submit_quote_refresh_spread_ratio")),
        "ws_age_ms": _safe_float(
            fields.get("ws_age_ms")
            or fields.get("pre_submit_effective_quote_age_ms")
            or fields.get("pre_submit_ws_snapshot_refresh_age_ms")
        ),
        "spread_ticks": _safe_float(fields.get("orderbook_micro_spread_ticks") or fields.get("spread_ticks")),
        "micro_state": str(fields.get("orderbook_micro_state") or fields.get("micro_state") or ""),
        "ofi_bucket": str(
            fields.get("orderbook_micro_ofi_bucket_key")
            or fields.get("orderbook_micro_calibration_bucket")
            or fields.get("ofi_bucket")
            or ""
        ),
    }


def _record_id(row: dict[str, Any], fields: dict[str, Any]) -> str:
    return str(row.get("record_id") or fields.get("record_id") or fields.get("runtime_record_id") or "").strip()


def _is_rising_missed_event_lineage(row: dict[str, Any], fields: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "")
    if _is_rising_missed_forced_one_share_entry(stage, fields):
        return True
    for key in (
        "forced_entry_reason",
        "rising_missed_class",
        "rising_missed_lineage",
        "rising_missed_filter_owner",
        "rising_missed_filter_layer",
        "source_signature",
        "scanner_promotion_reason",
    ):
        text = str(fields.get(key) or "").lower()
        if "rising_missed" in text or "low_rebound_rising" in text:
            return True
    return False


def _reason_matches(fields: dict[str, Any], reason: str) -> bool:
    for key in ("reason", "block_reason", "blocked_reason", "policy_reason", "effective_reason"):
        if str(fields.get(key) or "").strip() == reason:
            return True
    return False


def _bucket(value: float | None, bounds: tuple[float, ...], labels: tuple[str, ...]) -> str:
    if value is None:
        return "missing"
    for bound, label in zip(bounds, labels, strict=False):
        if value <= bound:
            return label
    return labels[-1] if labels else "present"


def _compact_counts(counter: Counter[str], *, limit: int = 12, key_name: str = "key") -> list[dict[str, Any]]:
    return [{key_name: key or "-", "count": count} for key, count in counter.most_common(limit)]


def _stale_weak_components(fields: dict[str, Any]) -> dict[str, bool]:
    quote_age = _safe_float(fields.get("rising_missed_scout_quality_guard_quote_age_ms"))
    max_quote_age = _safe_float(fields.get("rising_missed_scout_quality_guard_max_quote_age_ms"))
    return {
        "quote_stale": _boolish(fields.get("rising_missed_scout_quality_guard_quote_stale")),
        "quote_age_stale": quote_age is not None and max_quote_age is not None and quote_age > max_quote_age,
        "explicit_quote_stale": _boolish(fields.get("rising_missed_scout_quality_guard_explicit_quote_stale")),
        "text_quote_stale": _boolish(fields.get("rising_missed_scout_quality_guard_text_quote_stale")),
        "weak_ai": _boolish(fields.get("rising_missed_scout_quality_guard_weak_ai")),
        "ai_unusable": _boolish(fields.get("rising_missed_scout_quality_guard_ai_unusable")),
        "weak_strength": _boolish(fields.get("rising_missed_scout_quality_guard_weak_strength")),
        "recent_weak_ai_micro_block": _boolish(
            fields.get("rising_missed_scout_quality_guard_recent_weak_ai_micro_block")
        ),
    }


def _stale_weak_quote_age_bucket(quote_age_ms: float | None) -> str:
    if quote_age_ms is None:
        return "missing"
    if quote_age_ms <= STALE_EVAL_QUOTE_AGE_MS:
        return "fresh_or_under_threshold"
    if quote_age_ms <= STALE_WEAK_BORDERLINE_QUOTE_AGE_MS:
        return "borderline_3_5s"
    if quote_age_ms <= STALE_WEAK_MODERATE_QUOTE_AGE_MS:
        return "moderate_5_10s"
    if quote_age_ms <= STALE_WEAK_SEVERE_QUOTE_AGE_MS:
        return "stale_10_20s"
    return "severe_20s_plus"


def _stale_weak_ai_source_bucket(fields: dict[str, Any], components: dict[str, bool]) -> str:
    action = str(fields.get("rising_missed_scout_quality_guard_ai_action") or "-").strip().upper()
    ai_score = _safe_float(fields.get("rising_missed_scout_quality_guard_ai_score"))
    action_source = str(
        fields.get("rising_missed_entry_ai_action_source")
        or fields.get("entry_ai_action_source")
        or fields.get("rising_missed_scout_quality_guard_ai_action_source")
        or ""
    ).strip().lower()
    if action == "DROP":
        return "ai_drop"
    if components.get("ai_unusable"):
        return "ai_unusable"
    if action in {"", "-"} and ai_score is not None and ai_score <= 50.0 and action_source in {
        "",
        "-",
        "missing",
        "none",
        "null",
    }:
        return "ai_missing_default50"
    if components.get("weak_ai"):
        return "ai_weak_score"
    return "ai_other"


def _main_blocker_label(report_row: dict[str, Any] | None) -> str:
    if not report_row:
        return "-"
    stage = str(report_row.get("main_blocker_stage") or "-")
    reason = str(report_row.get("main_blocker_reason") or "-")
    return f"{stage}:{reason}"


def _summarize_stale_candidate_group(
    *,
    code: str,
    group: dict[str, Any],
    report_row: dict[str, Any] | None,
    next_action: str,
) -> dict[str, Any]:
    return {
        "stock_code": code,
        "stock_name": group.get("stock_name") or (report_row or {}).get("stock_name") or "",
        "event_count": int(group.get("event_count") or 0),
        "record_count": len(group.get("records") or set()),
        "max_delta_since_first_seen_pct": (report_row or {}).get("max_delta_since_first_seen_pct"),
        "rise_after_watch": (report_row or {}).get("rise_after_watch") or "unknown",
        "main_blocker": _main_blocker_label(report_row),
        "quote_age_ms": _metric_summary(group.get("quote_ages") or []),
        "quote_age_over_max_ms": _metric_summary(group.get("quote_age_over_max") or []),
        "quote_age_bucket_counts": _compact_counts(group.get("age_buckets") or Counter(), key_name="bucket"),
        "ai_source_bucket_counts": _compact_counts(group.get("ai_source_buckets") or Counter(), key_name="bucket"),
        "ai_action_counts": _compact_counts(group.get("ai_actions") or Counter(), key_name="action"),
        "next_action": next_action,
        "decision_authority": "source_only_recheck_candidate",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "runtime_threshold_apply",
            "intraday_runtime_apply",
            "broker_guard_bypass",
            "order_guard_relaxation",
            "provider_route_change",
            "bot_restart",
        ],
    }


def _summarize_stale_weak_events(
    events: list[dict[str, Any]],
    report_rows_by_code: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    report_rows_by_code = report_rows_by_code or {}
    component_counts: Counter[str] = Counter()
    combo_counts: Counter[str] = Counter()
    ai_action_counts: Counter[str] = Counter()
    ai_source_bucket_counts: Counter[str] = Counter()
    ai_score_buckets: Counter[str] = Counter()
    quote_age_bucket_counts: Counter[str] = Counter()
    strength_state_counts: Counter[str] = Counter()
    prior_micro_state_counts: Counter[str] = Counter()
    quote_ages: list[float] = []
    quote_age_over_max: list[float] = []
    ai_scores: list[float] = []
    prior_ai_scores: list[float] = []
    weak_micro_ages: list[float] = []
    symbols: set[str] = set()
    records: set[str] = set()
    grouped_by_code: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "stock_name": "",
            "event_count": 0,
            "records": set(),
            "quote_ages": [],
            "quote_age_over_max": [],
            "age_buckets": Counter(),
            "ai_source_buckets": Counter(),
            "ai_actions": Counter(),
        }
    )
    for event in events:
        row = event["row"]
        fields = event["fields"]
        code = str(row.get("stock_code") or "").strip()
        if code:
            symbols.add(code)
            group = grouped_by_code[code]
            group["stock_name"] = str(row.get("stock_name") or fields.get("stock_name") or group["stock_name"])
            group["event_count"] += 1
        else:
            group = None
        record_id = _record_id(row, fields)
        if record_id:
            records.add(record_id)
            if group is not None:
                group["records"].add(record_id)
        components = _stale_weak_components(fields)
        for key, enabled in components.items():
            if enabled:
                component_counts[key] += 1
        combo = "+".join(key for key, enabled in components.items() if enabled) or "no_component_flag"
        combo_counts[combo] += 1
        ai_action = str(fields.get("rising_missed_scout_quality_guard_ai_action") or "-")
        ai_action_counts[ai_action] += 1
        ai_source_bucket = _stale_weak_ai_source_bucket(fields, components)
        ai_source_bucket_counts[ai_source_bucket] += 1
        strength_state_counts[str(fields.get("rising_missed_scout_quality_guard_strength_state") or "-")] += 1
        prior_micro_state_counts[str(fields.get("rising_missed_scout_quality_guard_prior_weak_micro_state") or "-")] += 1
        quote_age = _safe_float(fields.get("rising_missed_scout_quality_guard_quote_age_ms"))
        if quote_age is not None:
            quote_ages.append(quote_age)
        quote_age_bucket = _stale_weak_quote_age_bucket(quote_age)
        quote_age_bucket_counts[quote_age_bucket] += 1
        max_quote_age = _safe_float(fields.get("rising_missed_scout_quality_guard_max_quote_age_ms"))
        if quote_age is not None and max_quote_age is not None:
            quote_age_over_max.append(quote_age - max_quote_age)
        if group is not None:
            group["age_buckets"][quote_age_bucket] += 1
            group["ai_source_buckets"][ai_source_bucket] += 1
            group["ai_actions"][ai_action] += 1
            if quote_age is not None:
                group["quote_ages"].append(quote_age)
            if quote_age is not None and max_quote_age is not None:
                group["quote_age_over_max"].append(quote_age - max_quote_age)
        ai_score = _safe_float(fields.get("rising_missed_scout_quality_guard_ai_score"))
        if ai_score is not None:
            ai_scores.append(ai_score)
            ai_score_buckets[_bucket(ai_score, (50.0, 60.0, 65.0), ("<=50", "51-60", "61-65", ">65"))] += 1
        prior_ai_score = _safe_float(fields.get("rising_missed_scout_quality_guard_prior_weak_ai_score"))
        if prior_ai_score is not None:
            prior_ai_scores.append(prior_ai_score)
        weak_micro_age = _safe_float(fields.get("rising_missed_scout_quality_guard_recent_weak_ai_micro_block_age_sec"))
        if weak_micro_age is not None:
            weak_micro_ages.append(weak_micro_age)
    immediate_candidates: list[dict[str, Any]] = []
    borderline_candidates: list[dict[str, Any]] = []
    for code, group in grouped_by_code.items():
        report_row = report_rows_by_code.get(code)
        max_delta = _safe_float((report_row or {}).get("max_delta_since_first_seen_pct"))
        has_borderline_age = bool((group.get("age_buckets") or Counter()).get("borderline_3_5s", 0) > 0)
        if max_delta is not None and max_delta >= STALE_WEAK_RECHECK_DELTA_PCT:
            immediate_candidates.append(
                _summarize_stale_candidate_group(
                    code=code,
                    group=group,
                    report_row=report_row,
                    next_action="source_only_immediate_quote_refresh_and_ai_recheck_candidate",
                )
            )
        if has_borderline_age:
            borderline_candidates.append(
                _summarize_stale_candidate_group(
                    code=code,
                    group=group,
                    report_row=report_row,
                    next_action="source_only_borderline_stale_quote_recheck_candidate",
                )
            )

    def _candidate_sort_key(item: dict[str, Any]) -> tuple[float, int, float, str]:
        max_delta = _safe_float(item.get("max_delta_since_first_seen_pct"))
        quote_age_max = _safe_float((item.get("quote_age_ms") or {}).get("max"))
        return (
            -(max_delta if max_delta is not None else -999.0),
            -int(item.get("event_count") or 0),
            -(quote_age_max if quote_age_max is not None else -1.0),
            str(item.get("stock_code") or ""),
        )

    immediate_candidates.sort(key=_candidate_sort_key)
    borderline_candidates.sort(key=_candidate_sort_key)
    return {
        "event_count": len(events),
        "symbol_count": len(symbols),
        "record_count": len(records),
        "component_counts": _compact_counts(component_counts, key_name="component"),
        "component_combo_counts": _compact_counts(combo_counts, key_name="combo"),
        "ai_action_counts": _compact_counts(ai_action_counts, key_name="action"),
        "ai_source_bucket_counts": _compact_counts(ai_source_bucket_counts, key_name="bucket"),
        "ai_score_bucket_counts": _compact_counts(ai_score_buckets, key_name="bucket"),
        "quote_age_bucket_counts": _compact_counts(quote_age_bucket_counts, key_name="bucket"),
        "strength_state_counts": _compact_counts(strength_state_counts, key_name="state"),
        "prior_micro_state_counts": _compact_counts(prior_micro_state_counts, key_name="state"),
        "quote_age_ms": _metric_summary(quote_ages),
        "quote_age_over_max_ms": _metric_summary(quote_age_over_max),
        "ai_score": _metric_summary(ai_scores),
        "prior_weak_ai_score": _metric_summary(prior_ai_scores),
        "recent_weak_ai_micro_block_age_sec": _metric_summary(weak_micro_ages),
        "recheck_candidate_delta_threshold_pct": STALE_WEAK_RECHECK_DELTA_PCT,
        "immediate_quote_refresh_ai_recheck_candidate_count": len(immediate_candidates),
        "borderline_quote_recheck_candidate_count": len(borderline_candidates),
        "immediate_quote_refresh_ai_recheck_candidates": immediate_candidates,
        "borderline_quote_recheck_candidates": borderline_candidates,
        "candidate_decision_authority": "source_only_recheck_candidate_no_runtime_mutation",
        "candidate_runtime_effect": False,
        "candidate_allowed_runtime_apply": False,
    }


def _summarize_latency_danger_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    symbols: set[str] = set()
    records: set[str] = set()
    stage_counts: Counter[str] = Counter()
    cause_counts: Counter[str] = Counter()
    detail_reason_counts: Counter[str] = Counter()
    source_quality_counts: Counter[str] = Counter()
    spread_bucket_counts: Counter[str] = Counter()
    price_bucket_counts: Counter[str] = Counter()
    signal_bucket_counts: Counter[str] = Counter()
    relief_block_counts: Counter[str] = Counter()
    canary_reason_counts: Counter[str] = Counter()
    quote_stale_count = 0
    fresh_effective_quote_count = 0
    spread_ratios: list[float] = []
    ws_ages: list[float] = []
    spread_bps: list[float] = []
    spread_ticks: list[float] = []
    signal_scores: list[float] = []
    ai_scores: list[float] = []
    for event in events:
        row = event["row"]
        fields = event["fields"]
        code = str(row.get("stock_code") or "").strip()
        if code:
            symbols.add(code)
        record_id = _record_id(row, fields)
        if record_id:
            records.add(record_id)
        stage_counts[str(row.get("stage") or "-")] += 1
        latency_event = _latency_danger_event(fields)
        cause_counts[str(latency_event.get("cause") or "other_danger")] += 1
        detail_reason_counts[str(fields.get("latency_danger_detail_reason") or "-")] += 1
        source_quality_counts[str(fields.get("latency_danger_source_quality_state") or "-")] += 1
        spread_bucket_counts[str(fields.get("latency_spread_block_bucket") or "-")] += 1
        price_bucket_counts[str(fields.get("latency_spread_block_price_bucket") or "-")] += 1
        signal_bucket_counts[str(fields.get("latency_spread_block_signal_context_bucket") or "-")] += 1
        relief_block_counts[str(fields.get("latency_relief_block_reason") or fields.get("latency_spread_relief_block_reason") or "-")] += 1
        canary_reason_counts[str(fields.get("latency_canary_reason") or "-")] += 1
        if any(
            _boolish(fields.get(key))
            for key in ("quote_stale", "quote_stale_at_submit", "pre_submit_effective_quote_stale")
        ):
            quote_stale_count += 1
        elif _safe_float(fields.get("pre_submit_effective_quote_age_ms")) is not None:
            fresh_effective_quote_count += 1
        for values, key in (
            (spread_ratios, "spread_ratio"),
            (ws_ages, "ws_age_ms"),
            (spread_bps, "latency_spread_block_spread_bps"),
            (spread_ticks, "latency_spread_block_spread_ticks"),
            (signal_scores, "latency_spread_relief_signal_score"),
            (ai_scores, "ai_score"),
        ):
            value = _safe_float(fields.get(key))
            if value is not None:
                values.append(value)
    return {
        "event_count": len(events),
        "symbol_count": len(symbols),
        "record_count": len(records),
        "quote_stale_event_count": quote_stale_count,
        "fresh_effective_quote_event_count": fresh_effective_quote_count,
        "stage_counts": _compact_counts(stage_counts, key_name="stage"),
        "cause_counts": _compact_counts(cause_counts, key_name="cause"),
        "detail_reason_counts": _compact_counts(detail_reason_counts, key_name="detail_reason"),
        "source_quality_counts": _compact_counts(source_quality_counts, key_name="source_quality"),
        "spread_bucket_counts": _compact_counts(spread_bucket_counts, key_name="bucket"),
        "price_bucket_counts": _compact_counts(price_bucket_counts, key_name="bucket"),
        "signal_context_bucket_counts": _compact_counts(signal_bucket_counts, key_name="bucket"),
        "relief_block_reason_counts": _compact_counts(relief_block_counts, key_name="reason"),
        "canary_reason_counts": _compact_counts(canary_reason_counts, key_name="reason"),
        "spread_ratio": _metric_summary(spread_ratios),
        "ws_age_ms": _metric_summary(ws_ages),
        "spread_bps": _metric_summary(spread_bps),
        "spread_ticks": _metric_summary(spread_ticks),
        "relief_signal_score": _metric_summary(signal_scores),
        "ai_score": _metric_summary(ai_scores),
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _metric_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "min": round(min(values), 6) if values else None,
        "median": round(_median(values), 6) if values else None,
        "max": round(max(values), 6) if values else None,
    }


def _is_real_entry_candidate(row: dict[str, Any], promoted_codes: set[str]) -> bool:
    if row.get("pipeline") != ENTRY_PIPELINE:
        return False
    code = str(row.get("stock_code") or "").strip()
    if not code or code == "-":
        return False
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    if str(fields.get("simulated_order") or "").strip().lower() == "true":
        return False
    stage = str(row.get("stage") or "")
    if _is_rising_missed_forced_one_share_entry(stage, fields):
        return False
    if stage.startswith("scalp_sim_") or stage.startswith("swing_"):
        return False
    authority = str(fields.get("decision_authority") or "").lower()
    if "sim_" in authority or "swing_" in authority:
        return False
    return bool(
        fields.get("scanner_promotion_id")
        or fields.get("momentum_tag") == "SCANNER"
        or code in promoted_codes
    )


def _default_event_cache_path(target_date: str) -> Path:
    pipeline_path = PROJECT_ROOT / "data" / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if pipeline_path.exists():
        return pipeline_path
    return (
        PROJECT_ROOT
        / "data"
        / "runtime"
        / "sentinel_event_cache"
        / f"buy_funnel_sentinel_events_{target_date}.jsonl"
    )


def _default_diagnostic_path(target_date: str) -> Path:
    report_dir = PROJECT_ROOT / "data" / "report" / "intraday_entry_blocker_diagnostics"
    candidates = sorted(report_dir.glob(f"intraday_entry_blocker_diagnostics_{target_date}*.json"))
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else report_dir / f"intraday_entry_blocker_diagnostics_{target_date}.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _freshness_workorders_from_diagnostic(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    source_quality = diagnostic.get("source_quality_workorders")
    if not isinstance(source_quality, dict):
        return []
    workorders = source_quality.get("rising_missed_freshness_recovery")
    if not isinstance(workorders, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in workorders:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "stock_code": str(item.get("stock_code") or ""),
                "stock_name": str(item.get("stock_name") or ""),
                "event_count": int(item.get("event_count") or 0),
                "diagnostic_quote_age_stale": int(item.get("diagnostic_quote_age_stale") or 0),
                "pre_ai_stale_or_history_gap": int(item.get("pre_ai_stale_or_history_gap") or 0),
                "latest_stage": str(item.get("latest_stage") or ""),
                "latest_reason": str(item.get("latest_reason") or ""),
                "next_action": str(item.get("next_action") or ""),
                "decision_authority": str(item.get("decision_authority") or "source_quality_only"),
                "runtime_effect": _boolish(item.get("runtime_effect")),
                "allowed_runtime_apply": _boolish(item.get("allowed_runtime_apply")),
            }
        )
    normalized.sort(key=lambda row: int(row.get("event_count") or 0), reverse=True)
    return normalized


def _flow_summary(events: list[dict[str, Any]], *, limit: int = 8) -> str:
    if not events:
        return "-"
    parts: list[str] = []
    for item in events:
        label = str(item["stage"])
        if item.get("reason"):
            label += f":{item['reason']}"
        if item.get("delta") is not None:
            label += f"({item['delta']:+.2f}%)"
        parts.append(f"{item['ts'].strftime('%H:%M:%S')} {label}")
    if len(parts) <= limit:
        return " -> ".join(parts)
    return " -> ".join(parts[:4] + ["..."] + parts[-3:])


def _main_blocker(record: dict[str, Any], promoted: dict[str, dict[str, Any]]) -> tuple[str, str, int]:
    item = promoted.get(record["code"]) or {}
    actionable = item.get("dominant_actionable_blocker") if isinstance(item.get("dominant_actionable_blocker"), dict) else {}
    if actionable.get("stage"):
        return str(actionable.get("stage") or ""), str(actionable.get("reason") or ""), int(actionable.get("count") or 0)
    dominant = item.get("dominant_blocker") if isinstance(item.get("dominant_blocker"), dict) else {}
    if dominant.get("stage"):
        return str(dominant.get("stage") or ""), str(dominant.get("reason") or ""), int(dominant.get("count") or 0)
    stage_counts: Counter[str] = record["stage_counts"]
    if stage_counts:
        stage, count = max(stage_counts.items(), key=lambda kv: kv[1])
        reason_counts: Counter[str] = record["reason_counts"]
        reason = reason_counts.most_common(1)[0][0] if reason_counts else ""
        return stage, reason, count
    return str(record.get("latest_stage") or ""), str(record.get("latest_reason") or ""), 0


def build_report(
    *,
    target_date: str,
    event_cache_path: Path | None = None,
    diagnostic_path: Path | None = None,
    since: str | None = None,
    until: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    event_cache_path = event_cache_path or _default_event_cache_path(target_date)
    diagnostic_path = diagnostic_path or _default_diagnostic_path(target_date)
    diagnostic = _read_json(diagnostic_path)
    raw_promoted = {
        str(item.get("stock_code")): item
        for item in diagnostic.get("promoted_symbols", [])
        if isinstance(item, dict) and item.get("stock_code")
    }
    since_ts = _parse_ts(since, target_date=target_date) if since else None
    until_ts = _parse_ts(until, target_date=target_date) if until else None
    promoted: dict[str, dict[str, Any]] = {}
    for code, item in raw_promoted.items():
        first_promoted_at = _parse_ts(item.get("first_promoted_at"))
        last_event_at = _parse_ts(item.get("last_event_at"))
        active_from = first_promoted_at
        active_until = last_event_at or first_promoted_at
        if since_ts is not None and active_until is not None and active_until < since_ts:
            continue
        if until_ts is not None and active_from is not None and active_from > until_ts:
            continue
        promoted[code] = item
    rising_missed_codes: set[str] = set()
    rising_missed_residual_codes: set[str] = set()
    non_residual_classes = {
        "intended_guard_preserved",
        "source_quality_excluded",
        "runtime_backpressure_observation",
        "strategy_reject_missed",
        "submitted_resolved",
        "not_rising_missed",
    }
    for item in diagnostic.get("rising_missed_buy", []):
        if not isinstance(item, dict) or not item.get("stock_code"):
            continue
        code = str(item.get("stock_code"))
        rising_missed_codes.add(code)
        klass = str(item.get("rising_missed_class") or "")
        explicit_eligible = item.get("rising_missed_one_share_eligible")
        if explicit_eligible is False or klass in non_residual_classes:
            continue
        rising_missed_residual_codes.add(code)
    promoted_codes = set(promoted)
    raw_promoted_codes = set(raw_promoted)
    forced_scout_event_count = 0
    forced_scout_symbols: set[str] = set()
    latest_forced_scout_at_by_code: dict[str, datetime] = {}
    stale_weak_events: list[dict[str, Any]] = []
    latency_danger_events: list[dict[str, Any]] = []

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "events": [],
            "stage_counts": Counter(),
            "reason_counts": Counter(),
            "first_ts": None,
            "last_ts": None,
            "name": "",
            "code": "",
            "latest_delta": None,
            "max_delta": None,
            "min_delta": None,
            "latest_stage": "",
            "latest_reason": "",
            "latest_ai_score": None,
            "latest_ai_action": "",
            "actual_submit_count": 0,
            "buy_signal_seen": False,
            "first_buy_signal_ts": None,
            "stale_eval_count": 0,
            "stale_refresh_recovered_count": 0,
            "max_quote_age_ms": None,
            "stale_eval_stage_counts": Counter(),
            "stale_eval_category_counts": Counter(),
            "latency_danger_events": [],
        }
    )

    for row in _read_jsonl(event_cache_path):
        ts = _parse_ts(row.get("emitted_at"))
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        code = str(row.get("stock_code") or "").strip()
        in_window = ts is not None and not (
            (since_ts is not None and ts < since_ts) or (until_ts is not None and ts > until_ts)
        )
        stage = str(row.get("stage") or "")
        if in_window and row.get("pipeline") == ENTRY_PIPELINE and _is_rising_missed_event_lineage(row, fields):
            if _reason_matches(fields, STALE_WEAK_REASON):
                stale_weak_events.append({"row": row, "fields": fields})
            if _reason_matches(fields, LATENCY_DANGER_REASON):
                latency_danger_events.append({"row": row, "fields": fields})
        if row.get("pipeline") == ENTRY_PIPELINE and code and _is_rising_missed_forced_one_share_entry(stage, fields):
            if ts is not None and (until_ts is None or ts <= until_ts):
                forced_scout_symbols.add(code)
                latest_forced_scout_at_by_code[code] = ts
            if in_window:
                forced_scout_event_count += 1
            continue
        if ts is None or (since_ts is not None and ts < since_ts) or (until_ts is not None and ts > until_ts):
            continue
        if _is_rising_missed_forced_lineage_row(row, latest_forced_scout_at_by_code):
            continue
        if not _is_real_entry_candidate(row, raw_promoted_codes):
            continue
        reason = _reason(fields)
        record = grouped[code]
        record["code"] = code
        record["name"] = str(row.get("stock_name") or fields.get("stock_name") or record["name"])
        record["first_ts"] = min([value for value in (record["first_ts"], ts) if value], default=ts)
        record["last_ts"] = max([value for value in (record["last_ts"], ts) if value], default=ts)
        delta = _safe_float(fields.get("price_delta_since_first_seen_pct"))
        if delta is not None:
            record["latest_delta"] = delta
            record["max_delta"] = delta if record["max_delta"] is None else max(record["max_delta"], delta)
            record["min_delta"] = delta if record["min_delta"] is None else min(record["min_delta"], delta)
        ai_score = _safe_float(fields.get("ai_score") or fields.get("ai_score_raw") or fields.get("ai_score_projected"))
        if ai_score is not None:
            record["latest_ai_score"] = ai_score
        action = _field(fields, "action") or _field(fields, "ai_action")
        if action:
            record["latest_ai_action"] = action
        quote_age_ms = _safe_float(fields.get("quote_age_ms") or fields.get("quote_age_at_submit_ms"))
        if quote_age_ms is not None:
            record["max_quote_age_ms"] = (
                quote_age_ms
                if record["max_quote_age_ms"] is None
                else max(record["max_quote_age_ms"], quote_age_ms)
            )
        stale_eval_category = _stale_eval_category(stage, reason, fields, quote_age_ms)
        if stale_eval_category == "fresh_refresh_recovered":
            record["stale_refresh_recovered_count"] += 1
        elif stale_eval_category:
            record["stale_eval_count"] += 1
            record["stale_eval_stage_counts"][stage] += 1
            record["stale_eval_category_counts"][stale_eval_category] += 1
        record["stage_counts"][stage] += 1
        if stage == "latency_block" and reason == "latency_state_danger":
            record["latency_danger_events"].append(_latency_danger_event(fields))
        if reason:
            record["reason_counts"][reason] += 1
        record["latest_stage"] = stage
        record["latest_reason"] = reason
        if str(fields.get("actual_order_submitted") or "").strip().lower() == "true" or any(
            marker in stage for marker in SUBMIT_STAGE_MARKERS
        ):
            record["actual_submit_count"] += 1
        if stage in BUY_SIGNAL_STAGES:
            record["buy_signal_seen"] = True
            if record["first_buy_signal_ts"] is None:
                record["first_buy_signal_ts"] = ts
        event_key = (stage, reason)
        events = record["events"]
        if not events or events[-1]["key"] != event_key or stage in BUY_SIGNAL_STAGES:
            events.append({"ts": ts, "stage": stage, "reason": reason, "delta": delta, "ai_score": ai_score, "key": event_key})

    for code, item in promoted.items():
        record = grouped[code]
        record["code"] = code
        record["name"] = item.get("stock_name") or record["name"]
        first_promoted_at = _parse_ts(item.get("first_promoted_at"))
        last_event_at = _parse_ts(item.get("last_event_at"))
        if first_promoted_at is not None and (since_ts is None or first_promoted_at >= since_ts):
            record["first_ts"] = first_promoted_at if record["first_ts"] is None else min(record["first_ts"], first_promoted_at)
        elif record["first_ts"] is None and since_ts is not None:
            record["first_ts"] = since_ts
        if last_event_at is not None:
            bounded_last_event_at = min(last_event_at, until_ts) if until_ts is not None else last_event_at
            record["last_ts"] = (
                bounded_last_event_at
                if record["last_ts"] is None
                else max(record["last_ts"], bounded_last_event_at)
            )
        latest_delta = _safe_float(item.get("latest_price_delta_since_first_seen_pct"))
        if latest_delta is not None:
            record["latest_delta"] = latest_delta
        max_delta = _safe_float(item.get("max_price_delta_since_first_seen_pct"))
        if max_delta is not None:
            record["max_delta"] = max_delta if record["max_delta"] is None else max(record["max_delta"], max_delta)
        if item.get("latest_ai_score") is not None:
            record["latest_ai_score"] = item.get("latest_ai_score")
        record["latest_ai_action"] = item.get("latest_ai_action") or record["latest_ai_action"]
        latest_blocker = item.get("latest_blocker") if isinstance(item.get("latest_blocker"), dict) else {}
        if latest_blocker:
            record["latest_stage"] = latest_blocker.get("stage") or record["latest_stage"]
            record["latest_reason"] = latest_blocker.get("reason") or record["latest_reason"]
        if code not in forced_scout_symbols:
            record["actual_submit_count"] = max(record["actual_submit_count"], int(item.get("real_submit_count") or 0))

    rows: list[dict[str, Any]] = []
    for code, record in grouped.items():
        if record["first_ts"] is None:
            continue
        diagnostic_item = promoted.get(code) or {}
        stage, reason, count = _main_blocker(record, promoted)
        max_delta = record["max_delta"]
        if max_delta is None:
            rise = "unknown"
        elif max_delta > 0:
            rise = "rising"
        else:
            rise = "flat_or_falling"
        rows.append(
            {
                "stock_code": code,
                "stock_name": record["name"],
                "first_observed_at": record["first_ts"].strftime("%H:%M:%S"),
                "last_observed_at": record["last_ts"].strftime("%H:%M:%S") if record["last_ts"] else "",
                "rise_after_watch": rise,
                "max_delta_since_first_seen_pct": max_delta,
                "latest_delta_since_first_seen_pct": record["latest_delta"],
                "buy_signal_seen": bool(record["buy_signal_seen"]),
                "first_buy_signal_at": record["first_buy_signal_ts"].strftime("%H:%M:%S") if record["first_buy_signal_ts"] else "",
                "actual_submit_count": int(record["actual_submit_count"] or 0),
                "main_blocker_stage": stage,
                "main_blocker_reason": reason,
                "main_blocker_count": count,
                "main_blocker_class": (
                    (diagnostic_item.get("dominant_actionable_blocker") or {}).get("class")
                    if isinstance(diagnostic_item.get("dominant_actionable_blocker"), dict)
                    else ""
                ),
                "latest_stage": record["latest_stage"],
                "latest_reason": record["latest_reason"],
                "latest_ai_score": record["latest_ai_score"],
                "latest_ai_action": record["latest_ai_action"],
                "stale_eval_count": int(record["stale_eval_count"] or 0),
                "stale_refresh_recovered_count": int(record["stale_refresh_recovered_count"] or 0),
                "max_quote_age_ms": record["max_quote_age_ms"],
                "dominant_stale_eval_stage": (
                    record["stale_eval_stage_counts"].most_common(1)[0][0]
                    if record["stale_eval_stage_counts"]
                    else ""
                ),
                "dominant_stale_eval_category": (
                    record["stale_eval_category_counts"].most_common(1)[0][0]
                    if record["stale_eval_category_counts"]
                    else ""
                ),
                "rising_missed_in_diagnostic": code in rising_missed_codes,
                "flow": _flow_summary(record["events"]),
            }
        )
    rows.sort(
        key=lambda item: (
            item["max_delta_since_first_seen_pct"] is None,
            -(item["max_delta_since_first_seen_pct"] if item["max_delta_since_first_seen_pct"] is not None else -999.0),
            item["first_observed_at"],
        )
    )
    blocker_rollup = [
        {"stage": stage or "-", "reason": reason or "-", "count": count}
        for (stage, reason), count in Counter((row["main_blocker_stage"], row["main_blocker_reason"]) for row in rows).most_common()
    ]
    rising_blocker_rollup = [
        {"stage": stage or "-", "reason": reason or "-", "count": count}
        for (stage, reason), count in Counter(
            (row["main_blocker_stage"], row["main_blocker_reason"]) for row in rows if row["rise_after_watch"] == "rising"
        ).most_common()
    ]
    rising_fresh_only_blocker_rollup = [
        {"stage": stage or "-", "reason": reason or "-", "count": count}
        for (stage, reason), count in Counter(
            (row["main_blocker_stage"], row["main_blocker_reason"])
            for row in rows
            if row["rise_after_watch"] == "rising" and row["stale_eval_count"] <= 0
        ).most_common()
    ]
    rising_stale_mixed_blocker_rollup = [
        {"stage": stage or "-", "reason": reason or "-", "count": count}
        for (stage, reason), count in Counter(
            (row["main_blocker_stage"], row["main_blocker_reason"])
            for row in rows
            if row["rise_after_watch"] == "rising" and row["stale_eval_count"] > 0
        ).most_common()
    ]
    summary = {
        "symbol_count": len(rows),
        "rising_symbol_count_by_max_delta": sum(1 for row in rows if row["rise_after_watch"] == "rising"),
        "rising_missed_buy_count_in_latest_diagnostic": len(rising_missed_codes),
        "rising_missed_symbol_count_in_report": sum(1 for row in rows if row["rising_missed_in_diagnostic"]),
        "rising_missed_residual_excluding_forced_scout_symbol_count": len(
            rising_missed_residual_codes - forced_scout_symbols
        ),
        "rising_missed_forced_scout_event_count": forced_scout_event_count,
        "rising_missed_forced_scout_symbol_count": len(forced_scout_symbols),
        "rising_missed_forced_scout_residual_symbol_count": len(rising_missed_codes & forced_scout_symbols),
        "real_submit_symbol_count_in_latest_diagnostic": diagnostic.get("summary", {}).get("real_submit_symbol_count"),
        "buy_signal_or_pre_submit_pass_seen_symbols": sum(1 for row in rows if row["buy_signal_seen"]),
        "stale_eval_symbol_count": sum(1 for row in rows if row["stale_eval_count"] > 0),
        "rising_stale_eval_symbol_count": sum(
            1 for row in rows if row["rise_after_watch"] == "rising" and row["stale_eval_count"] > 0
        ),
        "rising_fresh_only_symbol_count": sum(
            1 for row in rows if row["rise_after_watch"] == "rising" and row["stale_eval_count"] <= 0
        ),
        "stale_refresh_recovered_symbol_count": sum(1 for row in rows if row["stale_refresh_recovered_count"] > 0),
        "rising_missed_stale_quote_weak_event_count": len(stale_weak_events),
        "rising_missed_stale_quote_weak_symbol_count": len(
            {str(event["row"].get("stock_code") or "").strip() for event in stale_weak_events if event["row"].get("stock_code")}
        ),
        "rising_missed_latency_danger_event_count": len(latency_danger_events),
        "rising_missed_latency_danger_symbol_count": len(
            {
                str(event["row"].get("stock_code") or "").strip()
                for event in latency_danger_events
                if event["row"].get("stock_code")
            }
        ),
    }
    stale_eval_rollup = [
        {"stage": stage or "-", "count": count}
        for stage, count in Counter(
            row["dominant_stale_eval_stage"] for row in rows if row["dominant_stale_eval_stage"]
        ).most_common()
    ]
    stale_eval_category_rollup = [
        {"category": category or "-", "count": count}
        for category, count in Counter(
            row["dominant_stale_eval_category"] for row in rows if row["dominant_stale_eval_category"]
        ).most_common()
    ]
    latency_danger_root_cause = []
    latency_root_codes: set[str] = set()
    for code, record in grouped.items():
        events = list(record.get("latency_danger_events") or [])
        if not events:
            continue
        latency_root_codes.add(code)
        cause_counts = Counter(str(item.get("cause") or "other_danger") for item in events)
        micro_state_counts = Counter(str(item.get("micro_state") or "-") for item in events)
        bucket_counts = Counter(str(item.get("ofi_bucket") or "-") for item in events)
        latency_danger_root_cause.append(
            {
                "stock_code": code,
                "stock_name": record["name"],
                "event_count": len(events),
                "top_cause": cause_counts.most_common(1)[0][0],
                "cause_counts": [
                    {"cause": cause, "count": count}
                    for cause, count in cause_counts.most_common()
                ],
                "spread_ratio": _metric_summary(
                    [value for item in events if (value := item.get("spread_ratio")) is not None]
                ),
                "ws_age_ms": _metric_summary(
                    [value for item in events if (value := item.get("ws_age_ms")) is not None]
                ),
                "spread_ticks": _metric_summary(
                    [value for item in events if (value := item.get("spread_ticks")) is not None]
                ),
                "top_micro_state": micro_state_counts.most_common(1)[0][0],
                "top_ofi_bucket": bucket_counts.most_common(1)[0][0],
            }
        )
    diagnostic_latency_items = {
        **{
            str(item.get("stock_code")): item
            for item in diagnostic.get("rising_missed_buy", [])
            if isinstance(item, dict) and item.get("stock_code")
        },
        **raw_promoted,
    }
    for code, item in diagnostic_latency_items.items():
        if code in latency_root_codes:
            continue
        actionable = item.get("dominant_actionable_blocker") if isinstance(item.get("dominant_actionable_blocker"), dict) else {}
        dominant = item.get("dominant_blocker") if isinstance(item.get("dominant_blocker"), dict) else {}
        blocker = actionable if actionable.get("stage") == "latency_block" else dominant
        if blocker.get("stage") != "latency_block":
            continue
        count = int(blocker.get("count") or 0)
        if count <= 0:
            continue
        diagnostic_root = item.get("latency_danger_root_cause")
        if isinstance(diagnostic_root, dict) and int(diagnostic_root.get("event_count") or 0) > 0:
            latency_danger_root_cause.append(
                {
                    "stock_code": code,
                    "stock_name": item.get("stock_name") or "",
                    "event_count": int(diagnostic_root.get("event_count") or count),
                    "top_cause": diagnostic_root.get("top_cause") or "other_danger",
                    "cause_counts": diagnostic_root.get("cause_counts") or [],
                    "spread_ratio": diagnostic_root.get("spread_ratio") or _metric_summary([]),
                    "ws_age_ms": diagnostic_root.get("ws_age_ms") or _metric_summary([]),
                    "spread_ticks": diagnostic_root.get("spread_ticks") or _metric_summary([]),
                    "top_micro_state": diagnostic_root.get("top_micro_state") or "-",
                    "top_ofi_bucket": diagnostic_root.get("top_ofi_bucket") or "diagnostic_latency_root_cause",
                }
            )
            continue
        diagnostic_events = []
        for recent in item.get("recent_blockers") or []:
            if not isinstance(recent, dict):
                continue
            if recent.get("stage") != "latency_block" or recent.get("reason") != "latency_state_danger":
                continue
            if not any(
                recent.get(key) not in (None, "")
                for key in (
                    "latency_root_cause",
                    "spread_ratio",
                    "ws_age_ms",
                    "spread_ticks",
                    "orderbook_micro_spread_ticks",
                    "ofi_bucket",
                    "orderbook_micro_ofi_bucket_key",
                    "pre_submit_effective_quote_stale",
                    "quote_stale",
                )
            ):
                continue
            diagnostic_events.append(_latency_danger_event(recent))
        if diagnostic_events:
            cause_counts = Counter(str(event.get("cause") or "other_danger") for event in diagnostic_events)
            micro_state_counts = Counter(str(event.get("micro_state") or "-") for event in diagnostic_events)
            bucket_counts = Counter(str(event.get("ofi_bucket") or "-") for event in diagnostic_events)
            latency_danger_root_cause.append(
                {
                    "stock_code": code,
                    "stock_name": item.get("stock_name") or "",
                    "event_count": len(diagnostic_events),
                    "top_cause": cause_counts.most_common(1)[0][0],
                    "cause_counts": [
                        {"cause": cause, "count": event_count}
                        for cause, event_count in cause_counts.most_common()
                    ],
                    "spread_ratio": _metric_summary(
                        [value for event in diagnostic_events if (value := event.get("spread_ratio")) is not None]
                    ),
                    "ws_age_ms": _metric_summary(
                        [value for event in diagnostic_events if (value := event.get("ws_age_ms")) is not None]
                    ),
                    "spread_ticks": _metric_summary(
                        [value for event in diagnostic_events if (value := event.get("spread_ticks")) is not None]
                    ),
                    "top_micro_state": micro_state_counts.most_common(1)[0][0],
                    "top_ofi_bucket": bucket_counts.most_common(1)[0][0],
                }
            )
            continue
        latency_danger_root_cause.append(
            {
                "stock_code": code,
                "stock_name": item.get("stock_name") or "",
                "event_count": count,
                "top_cause": "latency_provenance_gap",
                "cause_counts": [{"cause": "latency_provenance_gap", "count": count}],
                "spread_ratio": _metric_summary([]),
                "ws_age_ms": _metric_summary([]),
                "spread_ticks": _metric_summary([]),
                "top_micro_state": "-",
                "top_ofi_bucket": "diagnostic_latency_without_source_event_fields",
            }
        )
    latency_danger_root_cause.sort(key=lambda item: int(item["event_count"]), reverse=True)
    report_rows_by_code = {str(row.get("stock_code") or ""): row for row in rows if row.get("stock_code")}
    return {
        "report_type": "intraday_entry_flow_report",
        "schema_version": 1,
        "target_date": target_date,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "event_window": {"since": since, "until": until},
        "source_events": str(event_cache_path),
        "source_diagnostic": str(diagnostic_path),
        "decision_authority": "source_quality_and_blocker_observation_only",
        "runtime_effect": False,
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "broker_guard_bypass",
        ],
        "summary": summary,
        "forced_scout_observation": {
            "event_count": forced_scout_event_count,
            "symbol_count": len(forced_scout_symbols),
            "symbols": sorted(forced_scout_symbols),
            "rising_missed_residual_symbols": sorted(rising_missed_codes & forced_scout_symbols),
            "rising_missed_residual_excluding_forced_scout_symbols": sorted(
                rising_missed_residual_codes - forced_scout_symbols
            ),
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
        },
        "blocker_taxonomy": diagnostic.get("blocker_taxonomy") if isinstance(diagnostic.get("blocker_taxonomy"), dict) else {},
        "blocker_rollup": blocker_rollup,
        "rising_symbol_blocker_rollup": rising_blocker_rollup,
        "rising_fresh_only_blocker_rollup": rising_fresh_only_blocker_rollup,
        "rising_stale_mixed_blocker_rollup": rising_stale_mixed_blocker_rollup,
        "stale_eval_rollup": stale_eval_rollup,
        "stale_eval_category_rollup": stale_eval_category_rollup,
        "freshness_recheck_workorders": _freshness_workorders_from_diagnostic(diagnostic),
        "latency_danger_root_cause": latency_danger_root_cause,
        "rising_missed_submit_safety_decomposition": {
            STALE_WEAK_REASON: _summarize_stale_weak_events(stale_weak_events, report_rows_by_code),
            LATENCY_DANGER_REASON: _summarize_latency_danger_events(latency_danger_events),
            "decision_authority": "source_only_submit_safety_decomposition_no_runtime_mutation",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "forbidden_uses": [
                "runtime_threshold_apply",
                "intraday_runtime_apply",
                "broker_guard_bypass",
                "order_guard_relaxation",
                "provider_route_change",
                "bot_restart",
            ],
        },
        "rows": rows,
    }


def _format_pct(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.2f}%"


def _window_label(report: dict[str, Any]) -> str:
    since_ts = _parse_ts(report.get("event_window", {}).get("since"), target_date=report.get("target_date"))
    if since_ts is None:
        return "전체"
    return since_ts.strftime("%H:%M")


def _md_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


def _md_stat_pair(stats: dict[str, Any]) -> str:
    median = stats.get("median")
    max_value = stats.get("max")
    return f"{'-' if median is None else median}/{'-' if max_value is None else max_value}"


def _md_counts(items: list[dict[str, Any]], label_key: str, *, limit: int = 8) -> str:
    return ", ".join(f"{item.get(label_key)}={item.get('count')}" for item in items[:limit]) or "-"


def _write_stale_recheck_candidate_table(
    handle: Any,
    candidates: list[dict[str, Any]],
    *,
    title: str,
    limit: int = 12,
) -> None:
    if not candidates:
        return
    handle.write(f"\n#### {title}\n\n")
    handle.write(
        "|종목|events|records|maxΔ|rise|quote age med/max|over max med/max|age buckets|AI source|main blocker|next action|runtime|\n"
    )
    handle.write("|---|---:|---:|---:|---|---:|---:|---|---|---|---|---|\n")
    for item in candidates[:limit]:
        runtime_state = (
            f"effect={bool(item.get('runtime_effect'))},"
            f"apply={bool(item.get('allowed_runtime_apply'))}"
        )
        handle.write(
            "|"
            f"{_md_cell(item.get('stock_name') or '')}({_md_cell(item.get('stock_code') or '')})|"
            f"{int(item.get('event_count') or 0)}|"
            f"{int(item.get('record_count') or 0)}|"
            f"{_format_pct(item.get('max_delta_since_first_seen_pct'))}|"
            f"{_md_cell(item.get('rise_after_watch') or 'unknown')}|"
            f"{_md_stat_pair(item.get('quote_age_ms') or {})}|"
            f"{_md_stat_pair(item.get('quote_age_over_max_ms') or {})}|"
            f"{_md_cell(_md_counts(item.get('quote_age_bucket_counts') or [], 'bucket', limit=4))}|"
            f"{_md_cell(_md_counts(item.get('ai_source_bucket_counts') or [], 'bucket', limit=4))}|"
            f"{_md_cell(item.get('main_blocker') or '-')}|"
            f"{_md_cell(item.get('next_action') or '-')}|"
            f"{runtime_state}|\n"
        )


def write_outputs(report: dict[str, Any], *, output_md: Path, output_csv: Path, max_rows: int = 100) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = list(report.get("rows", []))
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
    with output_md.open("w", encoding="utf-8") as handle:
        handle.write(f"# {report['target_date']} {_window_label(report)} 이후 감시대상 BUY 전 흐름\n\n")
        handle.write(f"- generated_at: {report['generated_at']}\n")
        handle.write(f"- source_events: {report['source_events']}\n")
        handle.write(f"- source_diagnostic: {report['source_diagnostic']}\n")
        handle.write(f"- event_window_since: {report.get('event_window', {}).get('since')}\n")
        handle.write(f"- event_window_until: {report.get('event_window', {}).get('until')}\n")
        for key, value in report["summary"].items():
            handle.write(f"- {key}: {value}\n")
        forced = report.get("forced_scout_observation") if isinstance(report.get("forced_scout_observation"), dict) else {}
        if forced:
            handle.write("\n## forced scout observation\n\n")
            handle.write(f"- event_count: {forced.get('event_count', 0)}\n")
            handle.write(f"- symbol_count: {forced.get('symbol_count', 0)}\n")
            handle.write(f"- symbols: {', '.join(forced.get('symbols') or []) or '-'}\n")
            handle.write(
                "- rising_missed_residual_symbols: "
                f"{', '.join(forced.get('rising_missed_residual_symbols') or []) or '-'}\n"
            )
            handle.write(
                "- rising_missed_residual_excluding_forced_scout_symbols: "
                f"{', '.join(forced.get('rising_missed_residual_excluding_forced_scout_symbols') or []) or '-'}\n"
            )
            handle.write(f"- decision_authority: {forced.get('decision_authority', 'source_quality_only')}\n")
            handle.write(f"- runtime_effect: {forced.get('runtime_effect', False)}\n")
        handle.write("\n## blocker rollup\n\n")
        for item in report["blocker_rollup"][:12]:
            handle.write(f"- {item['count']}: `{item['stage']}` / `{item['reason']}`\n")
        taxonomy = report.get("blocker_taxonomy") if isinstance(report.get("blocker_taxonomy"), dict) else {}
        if taxonomy:
            handle.write("\n## blocker taxonomy\n\n")
            for item in taxonomy.get("class_counts", [])[:12]:
                handle.write(f"- {item['count']}: `{item['class']}`\n")
            suppressed = taxonomy.get("suppressed_non_major_counts") or taxonomy.get("suppressed_non_actionable_counts", [])
            if suppressed:
                handle.write("\n## suppressed non-major blocker counts\n\n")
                for item in suppressed[:12]:
                    handle.write(
                        f"- {item['count']}: `{item['class']}` / `{item['stage']}` / `{item['reason']}`\n"
                    )
        handle.write("\n## rising-symbol blocker rollup\n\n")
        for item in report["rising_symbol_blocker_rollup"][:12]:
            handle.write(f"- {item['count']}: `{item['stage']}` / `{item['reason']}`\n")
        handle.write("\n## rising fresh-only blocker rollup\n\n")
        for item in report.get("rising_fresh_only_blocker_rollup", [])[:12]:
            handle.write(f"- {item['count']}: `{item['stage']}` / `{item['reason']}`\n")
        handle.write("\n## rising stale-mixed blocker rollup\n\n")
        for item in report.get("rising_stale_mixed_blocker_rollup", [])[:12]:
            handle.write(f"- {item['count']}: `{item['stage']}` / `{item['reason']}`\n")
        handle.write("\n## stale-eval rollup\n\n")
        for item in report["stale_eval_rollup"][:12]:
            handle.write(f"- {item['count']}: `{item['stage']}`\n")
        handle.write("\n## stale-eval category rollup\n\n")
        for item in report.get("stale_eval_category_rollup", [])[:12]:
            handle.write(f"- {item['count']}: `{item['category']}`\n")
        decomposition = (
            report.get("rising_missed_submit_safety_decomposition")
            if isinstance(report.get("rising_missed_submit_safety_decomposition"), dict)
            else {}
        )
        stale_weak = decomposition.get(STALE_WEAK_REASON) if isinstance(decomposition.get(STALE_WEAK_REASON), dict) else {}
        latency_danger = (
            decomposition.get(LATENCY_DANGER_REASON)
            if isinstance(decomposition.get(LATENCY_DANGER_REASON), dict)
            else {}
        )
        has_stale_weak = bool(stale_weak and int(stale_weak.get("event_count") or 0) > 0)
        has_latency_danger = bool(latency_danger and int(latency_danger.get("event_count") or 0) > 0)
        if has_stale_weak or has_latency_danger:
            handle.write("\n## rising missed submit-safety decomposition\n\n")
            handle.write(
                f"- decision_authority: {decomposition.get('decision_authority', 'source_only_submit_safety_decomposition_no_runtime_mutation')}\n"
            )
            handle.write(f"- runtime_effect: {decomposition.get('runtime_effect', False)}\n")
            handle.write(f"- allowed_runtime_apply: {decomposition.get('allowed_runtime_apply', False)}\n")
        if has_stale_weak:
            handle.write("\n### stale quote with weak AI or strength\n\n")
            handle.write(
                f"- events/symbols/records: {stale_weak.get('event_count', 0)}/"
                f"{stale_weak.get('symbol_count', 0)}/{stale_weak.get('record_count', 0)}\n"
            )
            handle.write(f"- quote_age_ms med/max: {_md_stat_pair(stale_weak.get('quote_age_ms') or {})}\n")
            handle.write(f"- quote_age_over_max_ms med/max: {_md_stat_pair(stale_weak.get('quote_age_over_max_ms') or {})}\n")
            handle.write(f"- ai_score med/max: {_md_stat_pair(stale_weak.get('ai_score') or {})}\n")
            handle.write(f"- quote age buckets: {_md_counts(stale_weak.get('quote_age_bucket_counts', []), 'bucket')}\n")
            handle.write(f"- AI source buckets: {_md_counts(stale_weak.get('ai_source_bucket_counts', []), 'bucket')}\n")
            handle.write(f"- components: {_md_counts(stale_weak.get('component_counts', []), 'component')}\n")
            handle.write(f"- top combos: {_md_counts(stale_weak.get('component_combo_counts', []), 'combo', limit=5)}\n")
            handle.write(f"- ai actions: {_md_counts(stale_weak.get('ai_action_counts', []), 'action', limit=6)}\n")
            handle.write(
                "- recheck candidates: "
                f"immediate_quote_refresh_ai_recheck="
                f"{stale_weak.get('immediate_quote_refresh_ai_recheck_candidate_count', 0)}, "
                f"borderline_quote_recheck={stale_weak.get('borderline_quote_recheck_candidate_count', 0)}, "
                f"delta_threshold_pct={stale_weak.get('recheck_candidate_delta_threshold_pct', STALE_WEAK_RECHECK_DELTA_PCT)}, "
                f"authority={stale_weak.get('candidate_decision_authority', 'source_only_recheck_candidate_no_runtime_mutation')}, "
                f"runtime_effect={stale_weak.get('candidate_runtime_effect', False)}, "
                f"allowed_runtime_apply={stale_weak.get('candidate_allowed_runtime_apply', False)}\n"
            )
            _write_stale_recheck_candidate_table(
                handle,
                stale_weak.get("immediate_quote_refresh_ai_recheck_candidates") or [],
                title="immediate quote refresh + AI recheck candidates",
            )
            _write_stale_recheck_candidate_table(
                handle,
                stale_weak.get("borderline_quote_recheck_candidates") or [],
                title="borderline stale quote recheck candidates",
            )
        if has_latency_danger:
            handle.write("\n### latency state danger\n\n")
            handle.write(
                f"- events/symbols/records: {latency_danger.get('event_count', 0)}/"
                f"{latency_danger.get('symbol_count', 0)}/{latency_danger.get('record_count', 0)}\n"
            )
            handle.write(
                f"- quote_stale/fresh_effective_quote: {latency_danger.get('quote_stale_event_count', 0)}/"
                f"{latency_danger.get('fresh_effective_quote_event_count', 0)}\n"
            )
            handle.write(f"- spread_bps med/max: {_md_stat_pair(latency_danger.get('spread_bps') or {})}\n")
            handle.write(f"- ws_age_ms med/max: {_md_stat_pair(latency_danger.get('ws_age_ms') or {})}\n")
            handle.write(f"- causes: {_md_counts(latency_danger.get('cause_counts', []), 'cause', limit=6)}\n")
            handle.write(f"- spread buckets: {_md_counts(latency_danger.get('spread_bucket_counts', []), 'bucket', limit=5)}\n")
        freshness_workorders = report.get("freshness_recheck_workorders") or []
        if freshness_workorders:
            handle.write("\n## bounded freshness recheck workorders\n\n")
            handle.write(
                "|종목|건수|diagnostic stale|history gap|latest|next action|authority|runtime|\n"
            )
            handle.write("|---|---:|---:|---:|---|---|---|---|\n")
            for item in freshness_workorders[:12]:
                latest = f"{item.get('latest_stage') or '-'}:{item.get('latest_reason') or '-'}"
                runtime_state = (
                    f"effect={bool(item.get('runtime_effect'))},"
                    f"apply={bool(item.get('allowed_runtime_apply'))}"
                )
                handle.write(
                    "|"
                    f"{_md_cell(item.get('stock_name') or '')}({_md_cell(item.get('stock_code') or '')})|"
                    f"{int(item.get('event_count') or 0)}|"
                    f"{int(item.get('diagnostic_quote_age_stale') or 0)}|"
                    f"{int(item.get('pre_ai_stale_or_history_gap') or 0)}|"
                    f"{_md_cell(latest)}|"
                    f"{_md_cell(item.get('next_action') or '-')}|"
                    f"{_md_cell(item.get('decision_authority') or 'source_quality_only')}|"
                    f"{runtime_state}|\n"
                )
        latency_causes = report.get("latency_danger_root_cause") or []
        if latency_causes:
            handle.write("\n## latency danger root cause\n\n")
            handle.write(
                "|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|\n"
            )
            handle.write("|---|---:|---|---:|---:|---:|---|---|\n")
            for item in latency_causes[:12]:
                spread = item.get("spread_ratio") or {}
                ws_age = item.get("ws_age_ms") or {}
                ticks = item.get("spread_ticks") or {}
                handle.write(
                    "|"
                    f"{item.get('stock_name')}({item.get('stock_code')})|"
                    f"{item.get('event_count')}|"
                    f"{item.get('top_cause')}|"
                    f"{_md_stat_pair(spread)}|"
                    f"{_md_stat_pair(ws_age)}|"
                    f"{_md_stat_pair(ticks)}|"
                    f"{_md_cell(item.get('top_micro_state') or '-')}|"
                    f"{_md_cell(item.get('top_ofi_bucket') or '-')}|\n"
                )
        handle.write("\n## top rows by max delta\n\n")
        handle.write("|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|\n")
        handle.write("|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|\n")
        for row in rows[:max_rows]:
            ai = ""
            if row["latest_ai_score"] is not None:
                ai = f"{float(row['latest_ai_score']):.0f}/{row['latest_ai_action']}"
            blocker = f"`{row['main_blocker_stage'] or '-'}`/{row['main_blocker_reason'] or '-'}"
            handle.write(
                "|"
                f"{row['stock_name']}({row['stock_code']})|"
                f"{row['first_observed_at']}|"
                f"{row['last_observed_at']}|"
                f"{row['rise_after_watch']}|"
                f"{_format_pct(row['max_delta_since_first_seen_pct'])}|"
                f"{_format_pct(row['latest_delta_since_first_seen_pct'])}|"
                f"{blocker}|"
                f"{row.get('main_blocker_class') or '-'}|"
                f"{row['stale_eval_count']}|"
                f"{row['stale_refresh_recovered_count']}|"
                f"{row['dominant_stale_eval_category'] or '-'}|"
                f"{'' if row['max_quote_age_ms'] is None else round(float(row['max_quote_age_ms']), 0)}|"
                f"{row['first_buy_signal_at'] or '-'}|"
                f"{ai}|"
                f"{row['actual_submit_count']}|"
                f"{row['flow']}|\n"
            )


def _default_output_paths(target_date: str, since: str | None, generated_at: str) -> tuple[Path, Path]:
    suffix = "all"
    since_ts = _parse_ts(since, target_date=target_date)
    if since_ts is not None:
        suffix = since_ts.strftime("%H%M")
    generated_ts = _parse_ts(generated_at, target_date=target_date) or datetime.now()
    output_md = (
        PROJECT_ROOT
        / "data"
        / "report"
        / "intraday_entry_flow"
        / f"intraday_entry_flow_{target_date}_current.md"
    )
    output_csv = Path("/tmp") / f"intraday_entry_flow_{target_date}_{suffix}_to_{generated_ts.strftime('%H%M')}.csv"
    return output_md, output_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build intraday watched-symbol entry flow report.")
    parser.add_argument("--target-date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--event-cache-path", type=Path)
    parser.add_argument("--diagnostic-path", type=Path)
    parser.add_argument("--since")
    parser.add_argument("--generated-at")
    parser.add_argument("--until")
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--max-rows", type=int, default=100)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)

    generated_at = args.generated_at or datetime.now().isoformat(timespec="seconds")
    report = build_report(
        target_date=args.target_date,
        event_cache_path=args.event_cache_path,
        diagnostic_path=args.diagnostic_path,
        since=args.since,
        until=args.until,
        generated_at=generated_at,
    )
    default_md, default_csv = _default_output_paths(args.target_date, args.since, generated_at)
    output_md = args.output_md or default_md
    output_csv = args.output_csv or default_csv
    write_outputs(report, output_md=output_md, output_csv=output_csv, max_rows=args.max_rows)
    if args.print_summary:
        print(json.dumps({"output_md": str(output_md), "output_csv": str(output_csv), **report["summary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
