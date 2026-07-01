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
RISING_MISSED_FORCED_LINEAGE_WINDOW_SEC = 180
RISING_MISSED_FORCED_LINEAGE_STAGES = {
    "latency_pass",
    "order_bundle_submitted",
    "holding_started",
}
STALE_EVAL_QUOTE_AGE_MS = 3000.0
LATENCY_DANGER_SPREAD_RATIO_CAP = 0.0100
LATENCY_DANGER_WS_AGE_MS_CAP = 450.0
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


def _is_rising_missed_forced_one_share_entry(fields: dict[str, Any]) -> bool:
    reason = str(fields.get("forced_entry_reason") or "").strip()
    forced = _boolish(fields.get("rising_missed_one_share_entry_forced"))
    qty = _safe_float(fields.get("forced_entry_qty"))
    one_share_or_missing = qty is None or qty == 1.0
    return one_share_or_missing and (reason == RISING_MISSED_FORCED_ENTRY_REASON or forced)


def _forced_lineage_qty_is_one(fields: dict[str, Any]) -> bool:
    for key in ("forced_entry_qty", "order_requested_qty", "order_quantity", "quantity", "qty", "fill_qty", "order_filled_qty"):
        value = _safe_float(fields.get(key))
        if value == 1.0:
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
    return stage in RISING_MISSED_FORCED_LINEAGE_STAGES or actual_submitted or _forced_lineage_qty_is_one(fields)


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
    if _is_rising_missed_forced_one_share_entry(fields):
        return False
    stage = str(row.get("stage") or "")
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
    rising_missed_codes = {
        str(item.get("stock_code"))
        for item in diagnostic.get("rising_missed_buy", [])
        if isinstance(item, dict) and item.get("stock_code")
    }
    promoted_codes = set(promoted)
    raw_promoted_codes = set(raw_promoted)
    forced_scout_event_count = 0
    forced_scout_symbols: set[str] = set()
    latest_forced_scout_at_by_code: dict[str, datetime] = {}

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
        if ts is None or (since_ts is not None and ts < since_ts) or (until_ts is not None and ts > until_ts):
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        code = str(row.get("stock_code") or "").strip()
        if code in raw_promoted_codes and _is_rising_missed_forced_one_share_entry(fields):
            forced_scout_event_count += 1
            forced_scout_symbols.add(code)
            if ts is not None:
                latest_forced_scout_at_by_code[code] = ts
            continue
        if _is_rising_missed_forced_lineage_row(row, latest_forced_scout_at_by_code):
            continue
        if not _is_real_entry_candidate(row, raw_promoted_codes):
            continue
        stage = str(row.get("stage") or "")
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
        "rising_missed_residual_excluding_forced_scout_symbol_count": len(rising_missed_codes - forced_scout_symbols),
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
            "rising_missed_residual_excluding_forced_scout_symbols": sorted(rising_missed_codes - forced_scout_symbols),
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
        "latency_danger_root_cause": latency_danger_root_cause,
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
