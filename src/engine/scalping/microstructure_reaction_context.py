from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from src.utils.constants import DATA_DIR


CONTEXT_VERSION = "microstructure_reaction_context_v1"
REPORT_DIR = DATA_DIR / "report" / "microstructure_reaction_context"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"

CONTEXT_KEYS = (
    "microstructure_reaction_context_version",
    "microstructure_reaction_context_status",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_context_hash",
)

FORBIDDEN_USES = [
    "standalone_buy",
    "broker_guard_bypass",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _safe_hhmmss_to_seconds(value: Any) -> int | None:
    try:
        text = str(value or "").replace(":", "").strip()
        if not text:
            return None
        if not text.isdigit():
            return None
        text = text.zfill(6)
        hour = int(text[0:2])
        minute = int(text[2:4])
        second = int(text[4:6])
        if hour > 23 or minute > 59 or second > 59:
            return None
        return (hour * 3600) + (minute * 60) + second
    except Exception:
        return None


def _age_ms_from_hhmmss(value: Any, *, now: datetime | None = None) -> int | None:
    tick_sec = _safe_hhmmss_to_seconds(value)
    if tick_sec is None:
        return None
    now_dt = now or datetime.now()
    now_sec = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    age_sec = now_sec - tick_sec
    if age_sec < -43200:
        age_sec += 86400
    elif age_sec > 43200:
        age_sec -= 86400
    return max(0, int(age_sec * 1000))


def _context_hash(payload: dict[str, Any]) -> str:
    compact = {
        key: payload.get(key)
        for key in CONTEXT_KEYS
        if key != "microstructure_reaction_context_hash"
    }
    raw = json.dumps(compact, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def neutral_microstructure_reaction_context(status: str, reason: str) -> dict[str, Any]:
    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": status,
        "microstructure_reaction_ask_sweep_score": 50,
        "microstructure_reaction_post_sweep_hold_score": 50,
        "microstructure_reaction_bid_replenishment_score": 50,
        "microstructure_reaction_wall_replenishment_risk_score": 50,
        "microstructure_reaction_vi_proximity_risk": 0,
        "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
        "microstructure_reaction_source_quality": reason,
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    return payload


def build_microstructure_reaction_context(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    recent_ticks = recent_ticks if isinstance(recent_ticks, list) else []
    recent_candles = recent_candles if isinstance(recent_candles, list) else []
    orderbook = ws_data.get("orderbook") if isinstance(ws_data.get("orderbook"), dict) else {}
    asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
    bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
    if not asks or not bids:
        return neutral_microstructure_reaction_context("source_quality_missing", "missing_orderbook")
    if len(recent_ticks) < 5:
        return neutral_microstructure_reaction_context("insufficient_window", "tick_sample_lt5")

    latest_time = recent_ticks[0].get("time") if isinstance(recent_ticks[0], dict) else None
    tick_age_ms = _age_ms_from_hhmmss(latest_time, now=now)
    quote_age_ms = _safe_float(ws_data.get("quote_age_ms"), -1.0)
    if quote_age_ms < 0:
        quote_age_ms = _safe_float(ws_data.get("ws_age_ms"), -1.0)
    if (tick_age_ms is not None and tick_age_ms > 5000) or (quote_age_ms >= 0 and quote_age_ms > 1200):
        return neutral_microstructure_reaction_context("stale", "stale_tick_or_quote")

    curr_price = _safe_float(ws_data.get("curr") or ws_data.get("curr_price"), 0.0)
    best_ask = _safe_float(asks[0].get("price") if asks else 0, curr_price)
    best_bid = _safe_float(bids[0].get("price") if bids else 0, curr_price)
    top3_ask_vol = sum(_safe_float(level.get("volume"), 0.0) for level in asks[:3] if isinstance(level, dict))
    top3_bid_vol = sum(_safe_float(level.get("volume"), 0.0) for level in bids[:3] if isinstance(level, dict))
    top3_depth_ratio = top3_ask_vol / top3_bid_vol if top3_bid_vol > 0 else 9.99

    ticks = [tick for tick in recent_ticks[:10] if isinstance(tick, dict)]
    buy_vol = sum(_safe_float(t.get("volume"), 0.0) for t in ticks if str(t.get("dir") or "").upper() == "BUY")
    sell_vol = sum(_safe_float(t.get("volume"), 0.0) for t in ticks if str(t.get("dir") or "").upper() == "SELL")
    total_vol = buy_vol + sell_vol
    buy_pressure = (buy_vol / total_vol * 100.0) if total_vol > 0 else 50.0
    prices: list[float] = []
    volumes: list[float] = []
    for tick in ticks:
        price_value = _safe_float(tick.get("price"), 0.0)
        if price_value > 0:
            prices.append(price_value)
        volume_value = _safe_float(tick.get("volume"), 0.0)
        if volume_value > 0:
            volumes.append(volume_value)
    latest_price = prices[0] if prices else curr_price
    oldest_price = prices[-1] if prices else curr_price
    price_change_pct = ((latest_price - oldest_price) / oldest_price * 100.0) if oldest_price > 0 else 0.0
    buy_at_or_above_ask = sum(
        _safe_float(t.get("volume"), 0.0)
        for t in ticks
        if str(t.get("dir") or "").upper() == "BUY" and _safe_float(t.get("price"), 0.0) >= best_ask
    )
    ask_sweep_share = buy_at_or_above_ask / total_vol if total_vol > 0 else 0.0
    avg_vol = mean(volumes) if volumes else 0.0
    large_buy = any(
        str(t.get("dir") or "").upper() == "BUY" and _safe_float(t.get("volume"), 0.0) >= avg_vol * 2.2
        for t in ticks[:5]
    ) if avg_vol > 0 else False
    large_sell = any(
        str(t.get("dir") or "").upper() == "SELL" and _safe_float(t.get("volume"), 0.0) >= avg_vol * 2.2
        for t in ticks[:5]
    ) if avg_vol > 0 else False

    ask_sweep_score = _clamp_score(35 + (buy_pressure - 50) * 0.7 + ask_sweep_share * 35 + (12 if price_change_pct > 0 else 0) + (8 if large_buy else 0))
    post_sweep_hold_score = _clamp_score(50 + min(25, max(-25, price_change_pct * 45)) + (12 if latest_price >= best_ask else 0) - (15 if latest_price < best_bid else 0))
    bid_ratio = top3_bid_vol / top3_ask_vol if top3_ask_vol > 0 else 2.0
    bid_replenishment_score = _clamp_score(45 + min(30, bid_ratio * 14) + (10 if sell_vol > 0 and price_change_pct >= -0.05 else 0) - (10 if latest_price < best_bid else 0))
    wall_replenishment_risk_score = _clamp_score(25 + max(0, top3_depth_ratio - 1.0) * 28 + (16 if large_sell else 0) + (10 if buy_pressure < 55 else 0))

    fluctuation = _safe_float(ws_data.get("fluctuation"), 0.0)
    candle_highs: list[float] = []
    candle_lows: list[float] = []
    for candle in recent_candles:
        if not isinstance(candle, dict):
            continue
        high_value = _safe_float(candle.get("고가"), 0.0)
        if high_value > 0:
            candle_highs.append(high_value)
        low_value = _safe_float(candle.get("저가"), 0.0)
        if low_value > 0:
            candle_lows.append(low_value)
    high = max(candle_highs or [curr_price])
    low = min(candle_lows or [curr_price])
    distance_from_high = ((curr_price - high) / high * 100.0) if high > 0 and curr_price > 0 else -99.0
    intraday_range = ((high - low) / low * 100.0) if high >= low and low > 0 else 0.0
    vi_proximity_risk = _clamp_score(max(0, fluctuation - 20) * 6 + (20 if distance_from_high >= -0.25 and intraday_range >= 12 else 0))

    if wall_replenishment_risk_score >= 70 or vi_proximity_risk >= 70:
        quality = "risk_context_only"
    elif ask_sweep_score >= 65 and post_sweep_hold_score >= 60 and bid_replenishment_score >= 55:
        quality = "favorable_reaction"
    elif ask_sweep_score <= 40 or post_sweep_hold_score <= 40:
        quality = "weak_reaction"
    else:
        quality = "mixed_reaction"

    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": "ok",
        "microstructure_reaction_ask_sweep_score": ask_sweep_score,
        "microstructure_reaction_post_sweep_hold_score": post_sweep_hold_score,
        "microstructure_reaction_bid_replenishment_score": bid_replenishment_score,
        "microstructure_reaction_wall_replenishment_risk_score": wall_replenishment_risk_score,
        "microstructure_reaction_vi_proximity_risk": vi_proximity_risk,
        "microstructure_reaction_entry_reaction_quality": quality,
        "microstructure_reaction_source_quality": "fresh_short_window",
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    return payload


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"microstructure_reaction_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    if path.exists():
        return path
    gz_path = Path(f"{path}.gz")
    return gz_path


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _has_context(fields: dict[str, Any]) -> bool:
    return any(key in fields for key in CONTEXT_KEYS)


def _row_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    if not _has_context(fields):
        return None
    row = {
        "stock_code": str(event.get("stock_code") or fields.get("stock_code") or "").lstrip("A"),
        "stock_name": event.get("stock_name"),
        "event_time": event.get("emitted_at") or fields.get("event_time") or fields.get("event_ts"),
        "event_ts": fields.get("event_ts") or event.get("emitted_at"),
        "record_id": event.get("record_id") or fields.get("record_id"),
        "sim_record_id": fields.get("sim_record_id"),
        "sim_parent_record_id": fields.get("sim_parent_record_id"),
        "source_event_stage": fields.get("source_event_stage") or event.get("stage"),
        "stage": event.get("stage"),
        "actual_order_submitted": _safe_bool(fields.get("actual_order_submitted"), False),
        "broker_order_forbidden": (
            _safe_bool(fields.get("broker_order_forbidden"), False)
            if "broker_order_forbidden" in fields
            else None
        ),
    }
    row.update({key: fields.get(key) for key in CONTEXT_KEYS})
    return row


def build_microstructure_reaction_context_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    path = _event_path(target_date)
    rows = [row for event in (_iter_jsonl(path) or []) if (row := _row_from_event(event))]
    status_counts = Counter(str(row.get("microstructure_reaction_context_status") or "missing") for row in rows)
    quality_counts = Counter(str(row.get("microstructure_reaction_entry_reaction_quality") or "-") for row in rows)
    source_quality_counts = Counter(str(row.get("microstructure_reaction_source_quality") or "-") for row in rows)
    stage_counts = Counter(str(row.get("stage") or "-") for row in rows)
    real_rows = [row for row in rows if row.get("actual_order_submitted") is True]
    summary = {
        "available": bool(rows),
        "row_count": len(rows),
        "ok_count": status_counts.get("ok", 0),
        "missing_or_unusable_count": len(rows) - status_counts.get("ok", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "entry_reaction_quality_counts": dict(sorted(quality_counts.items())),
        "source_quality_counts": dict(sorted(source_quality_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "real_submitted_count": len(real_rows),
        "avg_ask_sweep_score": _avg_score(rows, "microstructure_reaction_ask_sweep_score"),
        "avg_post_sweep_hold_score": _avg_score(rows, "microstructure_reaction_post_sweep_hold_score"),
        "avg_bid_replenishment_score": _avg_score(rows, "microstructure_reaction_bid_replenishment_score"),
        "max_vi_proximity_risk": max(
            [_safe_int(row.get("microstructure_reaction_vi_proximity_risk"), 0) for row in rows] or [0]
        ),
    }
    report = {
        "schema_version": 1,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "microstructure_reaction_context",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "entry_confidence_modifier_source_only",
        "metric_role": "feature_context",
        "window_policy": "same_day_short_window_runtime_events_plus_postclose_source_summary",
        "sample_floor": "none_for_v1_source_only",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "context_status ok and connection keys present",
        "forbidden_uses": FORBIDDEN_USES,
        "sources": {"pipeline_events": str(path) if path.exists() else None},
        "summary": summary,
        "rows": rows[:500],
        "warnings": [
            message
            for message in [
                "pipeline_events_missing" if not path.exists() else "",
                "microstructure_reaction_context_missing" if not rows else "",
            ]
            if message
        ],
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_microstructure_reaction_context_markdown(report), encoding="utf-8")
    return report


def _avg_score(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [_safe_float(row.get(key), -1.0) for row in rows]
    values = [value for value in values if value >= 0]
    return round(sum(values) / len(values), 3) if values else None


def render_microstructure_reaction_context_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Microstructure Reaction Context - {report.get('date')}",
        "",
        "- runtime_effect: `False`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- forbidden_uses: `{report.get('forbidden_uses') or []}`",
        "",
        "## Summary",
        f"- available: `{summary.get('available')}`",
        f"- row_count: `{summary.get('row_count')}`",
        f"- ok/missing_or_unusable: `{summary.get('ok_count')}` / `{summary.get('missing_or_unusable_count')}`",
        f"- real_submitted_count: `{summary.get('real_submitted_count')}`",
        f"- status_counts: `{summary.get('status_counts') or {}}`",
        f"- entry_reaction_quality_counts: `{summary.get('entry_reaction_quality_counts') or {}}`",
        f"- source_quality_counts: `{summary.get('source_quality_counts') or {}}`",
        f"- stage_counts: `{summary.get('stage_counts') or {}}`",
        f"- avg_ask_sweep_score: `{summary.get('avg_ask_sweep_score')}`",
        f"- avg_post_sweep_hold_score: `{summary.get('avg_post_sweep_hold_score')}`",
        f"- avg_bid_replenishment_score: `{summary.get('avg_bid_replenishment_score')}`",
        f"- max_vi_proximity_risk: `{summary.get('max_vi_proximity_risk')}`",
        f"- warnings: `{report.get('warnings') or []}`",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build source-only microstructure reaction context artifact.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args(argv)
    report = build_microstructure_reaction_context_report(args.date)
    print(json.dumps({"date": report.get("date"), "summary": report.get("summary"), "warnings": report.get("warnings")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
