"""WAIT 65~79 EV cohort report with paper-fill simulation."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error


WAIT6579_EV_COHORT_SCHEMA_VERSION = 1
_WAIT6579_STAGE = "wait65_79_ev_candidate"
_ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
_ATTEMPT_AUXILIARY_STAGES = {
    "dual_persona_shadow",
    "dual_persona_shadow_error",
}
_ORDER_FAIL_STAGES = {
    "order_bundle_failed",
    "order_leg_fail",
    "order_leg_no_response",
    "skip_order_leg_zero_qty",
}
_PREFLIGHT_STAGES = {
    _WAIT6579_STAGE,
    "watching_buy_recovery_canary",
    "wait6579_probe_canary_applied",
    "entry_armed",
    "entry_armed_resume",
    "budget_pass",
    "latency_pass",
    "latency_block",
    "order_bundle_submitted",
    "blocked_ai_score",
    "entry_armed_expired",
    "entry_armed_expired_after_wait",
    "entry_arm_expired",
    *_ORDER_FAIL_STAGES,
}
_PREFLIGHT_STAGE_MARKERS = tuple(f'"stage": "{stage}"' for stage in _PREFLIGHT_STAGES)


@dataclass
class EntryEvent:
    emitted_at: str
    signal_date: str
    name: str
    code: str
    stage: str
    record_id: str
    fields: dict[str, str]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, "", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return round((float(numerator) / float(denominator)) * 100.0, 1) if denominator > 0 else 0.0


def _parse_event_dt(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    candidate = str(value or "").strip()
    if not candidate:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return None


def _parse_minute_time(value: str, signal_date: str) -> datetime | None:
    try:
        return datetime.strptime(f"{signal_date} {value}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _classify_stage(stage: str) -> str:
    if stage == "order_bundle_submitted":
        return "submitted"
    if stage.startswith("blocked_") or stage.endswith("_block") or stage.endswith("_failed"):
        return "blocked"
    if stage in {"first_ai_wait", "entry_armed_expired", "entry_armed_expired_after_wait", "entry_arm_expired"}:
        return "waiting"
    return "progress"


def _is_attempt_terminal(stage: str) -> bool:
    return _classify_stage(stage) in {"blocked", "submitted"}


def _truthy(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _load_entry_events(target_date: str) -> list[EntryEvent]:
    rows = _load_jsonl(_pipeline_events_path(target_date))
    events: list[EntryEvent] = []
    for row in rows:
        if str(row.get("pipeline") or "").strip() != "ENTRY_PIPELINE":
            continue
        code = str(row.get("stock_code") or "").strip()[:6]
        if not code:
            continue
        events.append(
            EntryEvent(
                emitted_at=str(row.get("emitted_at") or ""),
                signal_date=str(row.get("emitted_date") or target_date),
                name=str(row.get("stock_name") or ""),
                code=code,
                stage=str(row.get("stage") or ""),
                record_id=str(row.get("record_id") or row.get("id") or ""),
                fields={str(key): str(value) for key, value in dict(row.get("fields") or {}).items()},
            )
        )
    events.sort(key=lambda item: (_parse_event_dt(item.emitted_at) or datetime.min, item.code, item.stage))
    return events


def _split_attempt_segments(item_events: list[EntryEvent]) -> list[list[EntryEvent]]:
    if not item_events:
        return []
    segments: list[list[EntryEvent]] = []
    current: list[EntryEvent] = []
    current_record_id = ""
    segment_terminated = False

    for event in item_events:
        record_changed = bool(current and event.record_id and current_record_id and event.record_id != current_record_id)
        should_rollover = record_changed or (
            segment_terminated and event.stage not in _ATTEMPT_AUXILIARY_STAGES
        )
        if should_rollover and current:
            segments.append(current)
            current = []
            current_record_id = ""
            segment_terminated = False

        current.append(event)
        if event.record_id and not current_record_id:
            current_record_id = event.record_id
        if _is_attempt_terminal(event.stage):
            segment_terminated = True

    if current:
        segments.append(current)
    return segments


def _build_wait6579_candidates(target_date: str) -> list[dict]:
    events = _load_entry_events(target_date)
    by_stock: dict[tuple[str, str], list[EntryEvent]] = defaultdict(list)
    for event in events:
        by_stock[(event.name, event.code)].append(event)

    candidates: list[dict] = []
    for _key, item_events in by_stock.items():
        for attempt_events in _split_attempt_segments(item_events):
            if not attempt_events:
                continue

            candidate_event = next((event for event in attempt_events if event.stage == _WAIT6579_STAGE), None)
            if candidate_event is None:
                continue

            anchor_dt = _parse_event_dt(candidate_event.emitted_at)
            if anchor_dt is None:
                continue

            terminal_event = next(
                (
                    event
                    for event in reversed(attempt_events)
                    if _classify_stage(event.stage) in {"blocked", "waiting", "submitted"}
                ),
                None,
            ) or attempt_events[-1]
            budget_event = next((event for event in reversed(attempt_events) if event.stage == "budget_pass"), None)
            entry_event = next(
                (event for event in reversed(attempt_events) if event.stage in _ENTRY_ARMED_STAGES),
                None,
            )

            signal_price = _safe_int(
                (entry_event.fields if entry_event else {}).get("target_buy_price")
                or candidate_event.fields.get("target_buy_price"),
                0,
            )
            has_submitted = any(event.stage == "order_bundle_submitted" for event in attempt_events)
            has_recovery_check = any(event.stage == "watching_buy_recovery_canary" for event in attempt_events)
            recovery_promoted = any(
                event.stage == "watching_buy_recovery_canary" and _truthy(event.fields.get("promoted"))
                for event in attempt_events
            )
            has_probe_applied = any(event.stage == "wait6579_probe_canary_applied" for event in attempt_events)
            has_budget_pass = any(event.stage == "budget_pass" for event in attempt_events)
            has_latency_pass = any(event.stage == "latency_pass" for event in attempt_events)
            has_latency_block = any(event.stage == "latency_block" for event in attempt_events)
            has_order_fail = any(event.stage in _ORDER_FAIL_STAGES for event in attempt_events)
            latency_block_event = next((event for event in reversed(attempt_events) if event.stage == "latency_block"), None)

            if has_submitted:
                submission_blocker = "submitted"
            elif has_latency_block:
                submission_blocker = "latency_block"
            elif has_order_fail:
                submission_blocker = "order_send_failure"
            elif not has_budget_pass:
                submission_blocker = "no_budget_pass"
            elif not has_recovery_check:
                submission_blocker = "no_recovery_check"
            elif not recovery_promoted:
                submission_blocker = "not_promoted"
            elif has_budget_pass and not has_latency_pass:
                submission_blocker = "post_budget_no_latency_pass"
            else:
                submission_blocker = "unknown"

            blocker_counts = Counter(
                event.stage for event in attempt_events if _classify_stage(event.stage) in {"blocked", "waiting"}
            )

            candidates.append(
                {
                    "candidate_id": f"{candidate_event.code}:{candidate_event.record_id or '-'}:{anchor_dt.strftime('%H%M%S')}",
                    "signal_date": target_date,
                    "signal_time": anchor_dt.strftime("%H:%M:%S"),
                    "stock_code": candidate_event.code,
                    "stock_name": candidate_event.name,
                    "record_id": candidate_event.record_id or None,
                    "attempt_status": "ENTERED" if has_submitted else "MISSED",
                    "ai_score": round(_safe_float(candidate_event.fields.get("ai_score"), 0.0), 1),
                    "action": str(candidate_event.fields.get("action") or "WAIT").upper(),
                    "buy_pressure": round(
                        _safe_float(
                            candidate_event.fields.get("buy_pressure"),
                            _safe_float(candidate_event.fields.get("buy_pressure_10t"), 0.0),
                        ),
                        3,
                    ),
                    "tick_accel": round(_safe_float(candidate_event.fields.get("tick_accel"), 0.0), 4),
                    "micro_vwap_bp": round(_safe_float(candidate_event.fields.get("micro_vwap_bp"), 0.0), 3),
                    "latency_state": str(candidate_event.fields.get("latency_state") or "-").upper(),
                    "parse_ok": str(candidate_event.fields.get("parse_ok") or "false").strip().lower() == "true",
                    "ai_response_ms": _safe_int(candidate_event.fields.get("ai_response_ms"), 0),
                    "target_qty": _safe_int((budget_event.fields if budget_event else {}).get("qty"), 0),
                    "safe_budget": _safe_int((budget_event.fields if budget_event else {}).get("safe_budget"), 0),
                    "signal_price": signal_price,
                    "terminal_blocker": terminal_event.stage,
                    "has_recovery_check": has_recovery_check,
                    "recovery_promoted": recovery_promoted,
                    "has_probe_applied": has_probe_applied,
                    "has_budget_pass": has_budget_pass,
                    "has_latency_pass": has_latency_pass,
                    "has_latency_block": has_latency_block,
                    "has_order_fail": has_order_fail,
                    "submission_blocker": submission_blocker,
                    "latency_block_reason": str((latency_block_event.fields if latency_block_event else {}).get("reason") or "-"),
                    "terminal_fields": dict(terminal_event.fields),
                    "stage_flow": [event.stage for event in attempt_events],
                    "blocker_counts": dict(blocker_counts),
                }
            )
    candidates.sort(
        key=lambda item: (
            str(item.get("signal_date") or ""),
            str(item.get("signal_time") or ""),
            str(item.get("stock_code") or ""),
        )
    )
    return candidates


def _resolve_anchor_price(signal_price: float, relevant: list[tuple[datetime, dict]]) -> float:
    if signal_price > 0:
        return signal_price
    if not relevant:
        return 0.0
    first_candle = relevant[0][1]
    for key in ("시가", "현재가", "고가", "저가"):
        price = _safe_float(first_candle.get(key), 0.0)
        if price > 0:
            return price
    return 0.0


def _compute_window_metrics(candidate: dict, candles: list[dict], window_minutes: int) -> dict:
    signal_dt = datetime.strptime(
        f"{candidate['signal_date']} {candidate['signal_time']}",
        "%Y-%m-%d %H:%M:%S",
    )
    start_dt = signal_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end_dt = start_dt + timedelta(minutes=window_minutes)

    relevant: list[tuple[datetime, dict]] = []
    for candle in candles:
        candle_dt = _parse_minute_time(str(candle.get("체결시간", "") or ""), candidate["signal_date"])
        if candle_dt is None:
            continue
        if candle_dt < start_dt or candle_dt >= end_dt:
            continue
        relevant.append((candle_dt, candle))
    relevant.sort(key=lambda item: item[0])

    anchor_price = _resolve_anchor_price(float(candidate.get("signal_price", 0) or 0), relevant)
    if anchor_price <= 0 or not relevant:
        return {
            "entry_price_used": int(round(anchor_price)),
            "close_ret_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "window_low_price": 0,
            "window_high_price": 0,
            "bars": len(relevant),
        }

    highs: list[float] = []
    lows: list[float] = []
    close_ret = 0.0
    low_prices: list[float] = []
    high_prices: list[float] = []

    for _candle_dt, candle in relevant:
        high_p = _safe_float(candle.get("고가"), 0.0)
        low_p = _safe_float(candle.get("저가"), 0.0)
        close_p = _safe_float(candle.get("현재가"), 0.0)
        if high_p > 0:
            high_ret = ((high_p / anchor_price) - 1.0) * 100.0
            highs.append(high_ret)
            high_prices.append(high_p)
        if low_p > 0:
            low_ret = ((low_p / anchor_price) - 1.0) * 100.0
            lows.append(low_ret)
            low_prices.append(low_p)
        if close_p > 0:
            close_ret = ((close_p / anchor_price) - 1.0) * 100.0

    mfe_pct = max(highs) if highs else 0.0
    mae_pct = min(lows) if lows else 0.0
    return {
        "entry_price_used": int(round(anchor_price)),
        "close_ret_pct": round(close_ret, 4),
        "mfe_pct": round(mfe_pct, 4),
        "mae_pct": round(mae_pct, 4),
        "window_low_price": int(round(min(low_prices))) if low_prices else 0,
        "window_high_price": int(round(max(high_prices))) if high_prices else 0,
        "bars": len(relevant),
    }


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _simulate_paper_fill(candidate: dict, metrics_10m: dict) -> dict:
    entry_price = _safe_float(metrics_10m.get("entry_price_used"), 0.0)
    low_price = _safe_float(metrics_10m.get("window_low_price"), 0.0)
    close_ret_pct = _safe_float(metrics_10m.get("close_ret_pct"), 0.0)
    qty = _safe_int(candidate.get("target_qty"), 0)

    partial_tolerance_bp = float(
        getattr(TRADING_RULES, "AI_WAIT6579_PAPER_FILL_PARTIAL_TOLERANCE_BP", 15.0) or 15.0
    )
    partial_weight = _clamp(
        float(getattr(TRADING_RULES, "AI_WAIT6579_PAPER_FILL_PARTIAL_WEIGHT", 0.40) or 0.40),
        0.0,
        1.0,
    )

    if entry_price <= 0 or low_price <= 0:
        return {
            "expected_fill_class": "NONE",
            "full_fill_prob": 0.0,
            "partial_fill_prob": 0.0,
            "expected_fill_prob": 0.0,
            "expected_fill_rate_pct": 0.0,
            "expected_ev_pct": 0.0,
            "expected_ev_krw": 0,
            "full_touch": False,
            "partial_touch": False,
            "partial_tolerance_bp": partial_tolerance_bp,
            "partial_weight": partial_weight,
        }

    partial_price_limit = entry_price * (1.0 + (partial_tolerance_bp / 10000.0))
    full_touch = low_price <= entry_price
    partial_touch = low_price <= partial_price_limit

    adj = 0.0
    if _safe_float(candidate.get("buy_pressure"), 0.0) >= 70.0:
        adj += 0.08
    if _safe_float(candidate.get("tick_accel"), 0.0) >= 1.25:
        adj += 0.06
    if _safe_float(candidate.get("micro_vwap_bp"), 0.0) > 0.0:
        adj += 0.04
    latency_state = str(candidate.get("latency_state") or "-").upper()
    if latency_state == "CAUTION":
        adj -= 0.10
    elif latency_state == "DANGER":
        adj -= 0.20
    if not bool(candidate.get("parse_ok")):
        adj -= 0.08
    if _safe_int(candidate.get("ai_response_ms"), 0) >= 2500:
        adj -= 0.05

    if full_touch:
        full_prob = 0.72 + adj
        partial_prob = 0.18 + (adj * 0.25)
    elif partial_touch:
        full_prob = 0.22 + (adj * 0.35)
        partial_prob = 0.54 + adj
    else:
        full_prob = 0.05 + (adj * 0.20)
        partial_prob = 0.08 + (adj * 0.30)

    full_prob = _clamp(full_prob, 0.0, 0.95)
    partial_prob = _clamp(partial_prob, 0.0, 0.95)
    if (full_prob + partial_prob) > 0.98:
        scale = 0.98 / (full_prob + partial_prob)
        full_prob *= scale
        partial_prob *= scale

    expected_fill_prob = full_prob + partial_prob
    effective_fill_prob = full_prob + (partial_prob * partial_weight)
    expected_ev_pct = close_ret_pct * effective_fill_prob
    expected_ev_krw = int(round(entry_price * qty * (expected_ev_pct / 100.0))) if qty > 0 else 0

    if full_touch and full_prob >= 0.50:
        expected_fill_class = "FULL"
    elif partial_touch and partial_prob >= 0.30:
        expected_fill_class = "PARTIAL"
    else:
        expected_fill_class = "NONE"

    return {
        "expected_fill_class": expected_fill_class,
        "full_fill_prob": round(full_prob, 4),
        "partial_fill_prob": round(partial_prob, 4),
        "expected_fill_prob": round(expected_fill_prob, 4),
        "expected_fill_rate_pct": round(expected_fill_prob * 100.0, 2),
        "expected_ev_pct": round(expected_ev_pct, 4),
        "expected_ev_krw": int(expected_ev_krw),
        "full_touch": bool(full_touch),
        "partial_touch": bool(partial_touch),
        "partial_tolerance_bp": round(partial_tolerance_bp, 2),
        "partial_weight": round(partial_weight, 3),
    }


def _fill_split_rows(rows: list[dict]) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        buckets[str(row.get("expected_fill_class") or "NONE")].append(row)

    out: list[dict] = []
    for key in ("FULL", "PARTIAL", "NONE"):
        items = buckets.get(key, [])
        if not items:
            continue
        out.append(
            {
                "fill_type": key,
                "samples": len(items),
                "avg_expected_fill_rate_pct": _avg(
                    [_safe_float(item.get("expected_fill_rate_pct"), 0.0) for item in items]
                ),
                "avg_expected_ev_pct": _avg([_safe_float(item.get("expected_ev_pct"), 0.0) for item in items]),
                "expected_ev_krw_sum": int(
                    sum(_safe_int(item.get("expected_ev_krw"), 0) for item in items)
                ),
                "avg_close_10m_pct": _avg([_safe_float(item.get("close_10m_pct"), 0.0) for item in items]),
            }
        )
    return out


def _terminal_breakdown(rows: list[dict]) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        buckets[str(row.get("terminal_blocker") or "-")].append(row)

    out: list[dict] = []
    for stage, items in sorted(buckets.items(), key=lambda pair: len(pair[1]), reverse=True):
        out.append(
            {
                "terminal_blocker": stage,
                "samples": len(items),
                "share_pct": _ratio(len(items), len(rows)),
                "avg_expected_fill_rate_pct": _avg(
                    [_safe_float(item.get("expected_fill_rate_pct"), 0.0) for item in items]
                ),
                "avg_expected_ev_pct": _avg([_safe_float(item.get("expected_ev_pct"), 0.0) for item in items]),
                "expected_ev_krw_sum": int(
                    sum(_safe_int(item.get("expected_ev_krw"), 0) for item in items)
                ),
            }
        )
    return out


def _preflight_summary(rows: list[dict]) -> dict:
    total = len(rows)
    submission_blockers = Counter(str(row.get("submission_blocker") or "-") for row in rows)
    latency_reasons = Counter(
        str(row.get("latency_block_reason") or "-")
        for row in rows
        if str(row.get("submission_blocker") or "") == "latency_block"
    )
    return {
        "total_candidates": total,
        "recovery_check_candidates": int(sum(1 for row in rows if bool(row.get("has_recovery_check")))),
        "recovery_promoted_candidates": int(sum(1 for row in rows if bool(row.get("recovery_promoted")))),
        "probe_applied_candidates": int(sum(1 for row in rows if bool(row.get("has_probe_applied")))),
        "budget_pass_candidates": int(sum(1 for row in rows if bool(row.get("has_budget_pass")))),
        "latency_pass_candidates": int(sum(1 for row in rows if bool(row.get("has_latency_pass")))),
        "latency_block_candidates": int(sum(1 for row in rows if bool(row.get("has_latency_block")))),
        "submitted_candidates": int(sum(1 for row in rows if str(row.get("attempt_status") or "") == "ENTERED")),
        "order_fail_candidates": int(sum(1 for row in rows if bool(row.get("has_order_fail")))),
        "recovery_check_rate_pct": _ratio(
            sum(1 for row in rows if bool(row.get("has_recovery_check"))),
            total,
        ),
        "promotion_rate_pct": _ratio(
            sum(1 for row in rows if bool(row.get("recovery_promoted"))),
            total,
        ),
        "submitted_rate_pct": _ratio(
            sum(1 for row in rows if str(row.get("attempt_status") or "") == "ENTERED"),
            total,
        ),
        "submission_blocker_breakdown": [
            {"label": label, "samples": count, "share_pct": _ratio(count, total)}
            for label, count in submission_blockers.most_common()
        ],
        "latency_block_reason_breakdown": [
            {"label": label, "samples": count, "share_pct": _ratio(count, sum(latency_reasons.values()))}
            for label, count in latency_reasons.most_common()
        ],
        "observability_passed": total == 0 or all("submission_blocker" in row for row in rows),
        "behavior_change": "none",
    }


def build_wait6579_preflight_report(target_date: str) -> dict:
    """Build a lightweight observability report without candle/API lookups."""
    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    path = _pipeline_events_path(safe_date)
    candidate_rows: list[EntryEvent] = []
    events_by_key: dict[tuple[str, str], list[EntryEvent]] = defaultdict(list)
    if path.exists():
        with open(path, "r", encoding="utf-8") as handle:
            for raw in handle:
                if not any(marker in raw for marker in _PREFLIGHT_STAGE_MARKERS):
                    continue
                try:
                    payload = json.loads(raw)
                except Exception:
                    continue
                if str(payload.get("pipeline") or "").strip() != "ENTRY_PIPELINE":
                    continue
                stage = str(payload.get("stage") or "")
                if stage not in _PREFLIGHT_STAGES:
                    continue
                code = str(payload.get("stock_code") or "").strip()[:6]
                record_id = str(payload.get("record_id") or payload.get("id") or "")
                if not code:
                    continue
                event = EntryEvent(
                    emitted_at=str(payload.get("emitted_at") or ""),
                    signal_date=str(payload.get("emitted_date") or safe_date),
                    name=str(payload.get("stock_name") or ""),
                    code=code,
                    stage=stage,
                    record_id=record_id,
                    fields={str(field_key): str(value) for field_key, value in dict(payload.get("fields") or {}).items()},
                )
                key = (code, record_id)
                events_by_key[key].append(event)
                if stage == _WAIT6579_STAGE:
                    candidate_rows.append(event)

    rows: list[dict] = []
    for candidate in candidate_rows:
        anchor_dt = _parse_event_dt(candidate.emitted_at)
        item_events = sorted(
            events_by_key.get((candidate.code, candidate.record_id), [candidate]),
            key=lambda item: _parse_event_dt(item.emitted_at) or datetime.min,
        )
        has_submitted = any(event.stage == "order_bundle_submitted" for event in item_events)
        has_recovery_check = any(event.stage == "watching_buy_recovery_canary" for event in item_events)
        recovery_promoted = any(
            event.stage == "watching_buy_recovery_canary" and _truthy(event.fields.get("promoted"))
            for event in item_events
        )
        has_probe_applied = any(event.stage == "wait6579_probe_canary_applied" for event in item_events)
        has_budget_pass = any(event.stage == "budget_pass" for event in item_events)
        has_latency_pass = any(event.stage == "latency_pass" for event in item_events)
        has_latency_block = any(event.stage == "latency_block" for event in item_events)
        has_order_fail = any(event.stage in _ORDER_FAIL_STAGES for event in item_events)
        latency_block_event = next((event for event in reversed(item_events) if event.stage == "latency_block"), None)
        terminal_event = next(
            (event for event in reversed(item_events) if _classify_stage(event.stage) in {"blocked", "waiting", "submitted"}),
            item_events[-1],
        )

        if has_submitted:
            submission_blocker = "submitted"
        elif has_latency_block:
            submission_blocker = "latency_block"
        elif has_order_fail:
            submission_blocker = "order_send_failure"
        elif not has_budget_pass:
            submission_blocker = "no_budget_pass"
        elif not has_recovery_check:
            submission_blocker = "no_recovery_check"
        elif not recovery_promoted:
            submission_blocker = "not_promoted"
        elif has_budget_pass and not has_latency_pass:
            submission_blocker = "post_budget_no_latency_pass"
        else:
            submission_blocker = "unknown"

        rows.append(
            {
                "candidate_id": f"{candidate.code}:{candidate.record_id or '-'}:{(anchor_dt or datetime.min).strftime('%H%M%S')}",
                "signal_date": candidate.signal_date,
                "signal_time": (anchor_dt or datetime.min).strftime("%H:%M:%S"),
                "stock_code": candidate.code,
                "stock_name": candidate.name,
                "record_id": candidate.record_id or None,
                "attempt_status": "ENTERED" if has_submitted else "MISSED",
                "ai_score": round(_safe_float(candidate.fields.get("ai_score"), 0.0), 1),
                "terminal_blocker": terminal_event.stage,
                "has_recovery_check": has_recovery_check,
                "recovery_promoted": recovery_promoted,
                "has_probe_applied": has_probe_applied,
                "has_budget_pass": has_budget_pass,
                "has_latency_pass": has_latency_pass,
                "has_latency_block": has_latency_block,
                "has_order_fail": has_order_fail,
                "submission_blocker": submission_blocker,
                "latency_block_reason": str((latency_block_event.fields if latency_block_event else {}).get("reason") or "-"),
                "stage_flow": [event.stage for event in item_events],
            }
        )
    rows.sort(
        key=lambda item: (
            str(item.get("signal_date") or ""),
            str(item.get("signal_time") or ""),
            str(item.get("stock_code") or ""),
        ),
        reverse=True,
    )
    return {
        "date": safe_date,
        "preflight": _preflight_summary(rows),
        "rows": rows,
        "meta": {
            "schema_version": WAIT6579_EV_COHORT_SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "pipeline_jsonl": str(_pipeline_events_path(safe_date)),
            "behavior_change": "none",
        },
    }


def build_wait6579_ev_cohort_report(
    target_date: str,
    *,
    token: str | None = None,
    top_n: int = 200,
) -> dict:
    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    candidates = _build_wait6579_candidates(safe_date)

    min_full_samples = max(
        1,
        int(getattr(TRADING_RULES, "AI_WAIT6579_EV_MIN_FULL_SAMPLES", 20) or 20),
    )
    min_partial_samples = max(
        1,
        int(getattr(TRADING_RULES, "AI_WAIT6579_EV_MIN_PARTIAL_SAMPLES", 20) or 20),
    )

    if not candidates:
        return {
            "date": safe_date,
            "metrics": {
                "total_candidates": 0,
                "entered_attempts": 0,
                "missed_attempts": 0,
                "expected_fill_rate_pct": 0.0,
                "avg_expected_ev_pct": 0.0,
                "expected_ev_krw_sum": 0,
            },
            "fill_split": [],
            "terminal_breakdown": [],
            "preflight": _preflight_summary([]),
            "approval_gate": {
                "min_full_samples_required": min_full_samples,
                "min_partial_samples_required": min_partial_samples,
                "full_samples": 0,
                "partial_samples": 0,
                "min_sample_gate_passed": False,
                "ev_directional_check_passed": False,
                "threshold_relaxation_approved": False,
            },
            "rows": [],
            "meta": {
                "schema_version": WAIT6579_EV_COHORT_SCHEMA_VERSION,
                "generated_at": datetime.now().isoformat(),
            },
        }

    try:
        from src.utils import kiwoom_utils
    except Exception as exc:
        log_error(f"[WAIT6579_EV] kiwoom_utils import failed: {exc}")
        kiwoom_utils = None

    if token is None and kiwoom_utils is not None:
        try:
            token = kiwoom_utils.get_kiwoom_token()
        except Exception as exc:
            log_error(f"[WAIT6579_EV] token fetch failed: {exc}")
            token = None

    candle_cache: dict[str, list[dict]] = {}
    rows: list[dict] = []
    for candidate in candidates:
        code = str(candidate.get("stock_code") or "").strip()[:6]
        if code and code not in candle_cache:
            if token is None or kiwoom_utils is None:
                candle_cache[code] = []
            else:
                try:
                    candle_cache[code] = kiwoom_utils.get_minute_candles_ka10080(token, code, limit=700) or []
                except Exception as exc:
                    log_error(f"[WAIT6579_EV] {code} minute candles fetch failed: {exc}")
                    candle_cache[code] = []

        candles = candle_cache.get(code, [])
        metrics_10m = _compute_window_metrics(candidate, candles, 10)
        paper_fill = _simulate_paper_fill(candidate, metrics_10m)
        rows.append(
            {
                "candidate_id": str(candidate.get("candidate_id") or ""),
                "signal_date": str(candidate.get("signal_date") or ""),
                "signal_time": str(candidate.get("signal_time") or ""),
                "stock_code": str(candidate.get("stock_code") or ""),
                "stock_name": str(candidate.get("stock_name") or ""),
                "record_id": candidate.get("record_id"),
                "attempt_status": str(candidate.get("attempt_status") or ""),
                "action": str(candidate.get("action") or "WAIT"),
                "ai_score": round(_safe_float(candidate.get("ai_score"), 0.0), 1),
                "buy_pressure": round(_safe_float(candidate.get("buy_pressure"), 0.0), 3),
                "tick_accel": round(_safe_float(candidate.get("tick_accel"), 0.0), 4),
                "micro_vwap_bp": round(_safe_float(candidate.get("micro_vwap_bp"), 0.0), 3),
                "latency_state": str(candidate.get("latency_state") or "-"),
                "parse_ok": bool(candidate.get("parse_ok")),
                "ai_response_ms": _safe_int(candidate.get("ai_response_ms"), 0),
                "terminal_blocker": str(candidate.get("terminal_blocker") or "-"),
                "has_recovery_check": bool(candidate.get("has_recovery_check")),
                "recovery_promoted": bool(candidate.get("recovery_promoted")),
                "has_probe_applied": bool(candidate.get("has_probe_applied")),
                "has_budget_pass": bool(candidate.get("has_budget_pass")),
                "has_latency_pass": bool(candidate.get("has_latency_pass")),
                "has_latency_block": bool(candidate.get("has_latency_block")),
                "has_order_fail": bool(candidate.get("has_order_fail")),
                "submission_blocker": str(candidate.get("submission_blocker") or "-"),
                "latency_block_reason": str(candidate.get("latency_block_reason") or "-"),
                "target_qty": _safe_int(candidate.get("target_qty"), 0),
                "safe_budget": _safe_int(candidate.get("safe_budget"), 0),
                "signal_price": _safe_int(candidate.get("signal_price"), 0),
                "entry_price_used": _safe_int(metrics_10m.get("entry_price_used"), 0),
                "close_10m_pct": round(_safe_float(metrics_10m.get("close_ret_pct"), 0.0), 4),
                "mfe_10m_pct": round(_safe_float(metrics_10m.get("mfe_pct"), 0.0), 4),
                "mae_10m_pct": round(_safe_float(metrics_10m.get("mae_pct"), 0.0), 4),
                "bars_10m": _safe_int(metrics_10m.get("bars"), 0),
                **paper_fill,
            }
        )

    rows.sort(
        key=lambda item: (
            str(item.get("signal_date") or ""),
            str(item.get("signal_time") or ""),
            str(item.get("stock_code") or ""),
        ),
        reverse=True,
    )
    capped_rows = rows[: max(1, int(top_n or 200))]

    total = len(rows)
    entered_attempts = sum(1 for row in rows if str(row.get("attempt_status") or "") == "ENTERED")
    missed_attempts = sum(1 for row in rows if str(row.get("attempt_status") or "") == "MISSED")
    fill_split = _fill_split_rows(rows)
    terminal_breakdown = _terminal_breakdown(rows)

    split_map = {str(item.get("fill_type") or ""): item for item in fill_split}
    full_samples = _safe_int((split_map.get("FULL") or {}).get("samples"), 0)
    partial_samples = _safe_int((split_map.get("PARTIAL") or {}).get("samples"), 0)
    full_ev = _safe_float((split_map.get("FULL") or {}).get("avg_expected_ev_pct"), 0.0)
    partial_ev = _safe_float((split_map.get("PARTIAL") or {}).get("avg_expected_ev_pct"), 0.0)
    min_sample_gate_passed = full_samples >= min_full_samples and partial_samples >= min_partial_samples
    ev_directional_check_passed = full_ev >= 0.0 and partial_ev >= 0.0

    return {
        "date": safe_date,
        "metrics": {
            "total_candidates": total,
            "entered_attempts": int(entered_attempts),
            "missed_attempts": int(missed_attempts),
            "entered_rate": _ratio(entered_attempts, total),
            "expected_fill_rate_pct": _avg(
                [_safe_float(row.get("expected_fill_rate_pct"), 0.0) for row in rows]
            ),
            "avg_expected_ev_pct": _avg([_safe_float(row.get("expected_ev_pct"), 0.0) for row in rows]),
            "expected_ev_krw_sum": int(sum(_safe_int(row.get("expected_ev_krw"), 0) for row in rows)),
            "avg_close_10m_pct": _avg([_safe_float(row.get("close_10m_pct"), 0.0) for row in rows]),
            "avg_ai_response_ms": _avg([float(_safe_int(row.get("ai_response_ms"), 0)) for row in rows]),
        },
        "fill_split": fill_split,
        "terminal_breakdown": terminal_breakdown,
        "preflight": _preflight_summary(rows),
        "approval_gate": {
            "min_full_samples_required": min_full_samples,
            "min_partial_samples_required": min_partial_samples,
            "full_samples": int(full_samples),
            "partial_samples": int(partial_samples),
            "min_sample_gate_passed": bool(min_sample_gate_passed),
            "ev_directional_check_passed": bool(ev_directional_check_passed),
            "threshold_relaxation_approved": bool(min_sample_gate_passed and ev_directional_check_passed),
            "full_avg_expected_ev_pct": float(full_ev),
            "partial_avg_expected_ev_pct": float(partial_ev),
        },
        "rows": capped_rows,
        "meta": {
            "schema_version": WAIT6579_EV_COHORT_SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "pipeline_jsonl": str(_pipeline_events_path(safe_date)),
        },
    }
