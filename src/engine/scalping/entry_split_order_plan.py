"""Entry split order plan report and bounded runtime allocator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy, is_date_allowed
from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import iter_jsonl


SCHEMA_VERSION = "entry_split_order_plan_v1"
POLICY_SCHEMA_VERSION = "entry_split_order_policy_v1"
REPORT_TYPE = "entry_split_order_plan"
RUNTIME_FAMILY = "entry_split_order_plan"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
POLICY_DIR = DATA_DIR / "threshold_cycle" / "entry_split_order_policy"
SAMPLE_FLOOR_REAL = 20
SAMPLE_FLOOR_SIM = 10
SPLIT_VARIANT_OUTCOME_FLOOR_REAL = 20
POST_SUBMIT_TICK_BAND_FLOOR_REAL = 20
POST_SUBMIT_LOW_WINDOW_MINUTES = 10
POLICY_MODE_REAL_PRIMARY_EV = "real_primary_ev_optimized"
POLICY_MODE_BOUNDED_EQUAL_BASELINE = "bounded_equal_split_baseline"
POLICY_MODE_POST_SUBMIT_TICK_BAND = "post_submit_tick_band_seed"
BASELINE_SPLIT_VARIANT_ID = "equal_50_50_offset_0pct_0_3pct"
PCT_BAND_3LEG_VARIANT_ID = "equal_3leg_offset_0pct_0_3pct_0_8pct"
RUNTIME_FALLBACK_POLICY_MODE = "runtime_default_passive_center_40_60_0_3pct"
RUNTIME_FALLBACK_VARIANT_ID = "runtime_default_passive_center_40_60_offset_0pct_0_3pct"
PASSIVE_CENTER_MAX_FIRST_WEIGHT = 0.40
PASSIVE_BIAS_WAIT_WARNING_FIRST_WEIGHT = 0.20
ALLOWED_PRICE_CANDIDATES = {
    "resolved_order_price",
    "best_bid",
    "bid-1tick",
    "bid-2tick",
    "reference_target",
    "AI_candidate",
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"entry_split_order_policy_{target_date}.json"


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _threshold_events_path(target_date: str) -> Path:
    return DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"


def _sim_post_sell_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"sim_post_sell_evaluations_{target_date}.jsonl"


def _real_post_sell_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl"


def _threshold_cycle_ev_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json"


def _source_quality_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    return {**event, **fields}


def _event_date(event: dict[str, Any]) -> str:
    for key in ("date", "target_date", "source_date", "trading_date"):
        value = str(event.get(key) or "").strip()
        if len(value) >= 10:
            return value[:10]
    ts = str(event.get("timestamp") or event.get("created_at") or event.get("ts") or "").strip()
    return ts[:10] if len(ts) >= 10 else ""


def _event_dt(event: dict[str, Any]) -> datetime | None:
    for key in ("emitted_at", "timestamp", "created_at", "ts"):
        value = str(event.get(key) or "").strip()
        if not value:
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone(timedelta(hours=9))).replace(tzinfo=None)
        return parsed
    return None


def _hard_blocking_stages(source_quality: dict[str, Any]) -> set[str]:
    summary = source_quality.get("summary") if isinstance(source_quality.get("summary"), dict) else {}
    raw = summary.get("hard_blocking_stages") or source_quality.get("hard_blocking_stages") or []
    if not isinstance(raw, list):
        raw = [raw]
    return {str(item).strip() for item in raw if str(item).strip()}


def _source_quality_summary(target_date: str) -> dict[str, Any]:
    path = _source_quality_path(target_date)
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or ("missing" if not path.exists() else "loaded"))
    hard_gap_count = _safe_int(summary.get("hard_blocking_contract_gap_count"), 0)
    tuning_input_allowed = summary.get("tuning_input_allowed")
    if tuning_input_allowed is None:
        tuning_input_allowed = status not in {"fail", "missing", "invalid"} and hard_gap_count <= 0
    if status == "fail" or hard_gap_count > 0:
        tuning_input_allowed = False
    return {
        "artifact": str(path) if path.exists() else None,
        "status": status,
        "tuning_input_allowed": bool(tuning_input_allowed),
        "hard_blocking_contract_gap_count": hard_gap_count,
        "hard_blocking_excluded_row_count": _safe_int(summary.get("hard_blocking_excluded_row_count"), 0),
        "raw_row_exclusion_applied": bool(summary.get("raw_row_exclusion_applied") or payload.get("raw_row_exclusion")),
        "hard_blocking_stages": sorted(_hard_blocking_stages(payload)),
    }


def _iter_input_events(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    clean_policy = clean_baseline_policy()
    events: list[dict[str, Any]] = []
    excluded_pre_baseline = 0
    source_paths = {
        "pipeline_events": _pipeline_events_path(target_date),
        "threshold_events": _threshold_events_path(target_date),
    }
    for source_name, path in source_paths.items():
        for event in iter_jsonl(path):
            fields = _event_fields(event)
            event_date = _event_date(fields) or target_date
            if not is_date_allowed(event_date, clean_policy):
                excluded_pre_baseline += 1
                continue
            fields["source_name"] = source_name
            fields["source_date"] = event_date
            events.append(fields)
    return events, {
        "source_paths": {name: str(path) if path.exists() else None for name, path in source_paths.items()},
        "excluded_pre_baseline_count": excluded_pre_baseline,
        "clean_tuning_baseline": clean_policy,
    }


def _load_sim_ev_values(target_date: str) -> dict[str, list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[str, list[float]] = defaultdict(list)
    path = _sim_post_sell_path(target_date)
    for event in iter_jsonl(path):
        fields = _event_fields(event)
        event_date = _event_date(fields) or str(fields.get("entry_date") or "")[:10]
        if event_date and event_date != target_date:
            continue
        profit = _safe_float(
            fields.get("profit_rate")
            if fields.get("profit_rate") is not None
            else fields.get("sim_profit_rate")
            if fields.get("sim_profit_rate") is not None
            else fields.get("post_sell_profit_rate"),
            None,
        )
        if profit is None:
            continue
        values[_context_bucket(fields)].append(float(profit))
    return values


def _load_real_ev_values(target_date: str) -> dict[str, list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[str, list[float]] = defaultdict(list)
    path = _real_post_sell_path(target_date)
    for event in iter_jsonl(path):
        fields = _event_fields(event)
        event_date = _event_date(fields) or str(fields.get("entry_date") or fields.get("sell_date") or "")[:10]
        if event_date and event_date != target_date:
            continue
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        profit = _safe_float(
            fields.get("profit_rate")
            if fields.get("profit_rate") is not None
            else fields.get("post_sell_profit_rate"),
            None,
        )
        if profit is None:
            continue
        values[_context_bucket(fields)].append(float(profit))
    return values


def _split_variant_id_from_fields(fields: dict[str, Any]) -> str:
    explicit = str(fields.get("entry_split_order_variant_id") or "").strip()
    if explicit:
        return explicit
    if not (
        _safe_bool(fields.get("entry_split_order_policy_applied"))
        or str(fields.get("entry_split_order_policy_mode") or "").strip()
    ):
        return ""
    mode = str(fields.get("entry_split_order_policy_mode") or "").strip() or "unknown_mode"
    leg_count = _safe_int(fields.get("entry_split_order_leg_count"), 0)
    offsets = str(fields.get("entry_split_order_price_offsets_ticks") or "").strip() or "unknown_offsets"
    weight = str(fields.get("entry_split_order_qty_weight_min") or "").strip() or "unknown_weight"
    return f"{mode}:legs{leg_count}:offsets{offsets}:w{weight}"


def _load_real_split_variant_ev_values(target_date: str) -> dict[tuple[str, str], list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    path = _real_post_sell_path(target_date)
    for event in iter_jsonl(path):
        fields = _event_fields(event)
        event_date = _event_date(fields) or str(fields.get("entry_date") or fields.get("sell_date") or "")[:10]
        if event_date and event_date != target_date:
            continue
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        variant_id = _split_variant_id_from_fields(fields)
        if not variant_id:
            continue
        profit = _safe_float(
            fields.get("profit_rate")
            if fields.get("profit_rate") is not None
            else fields.get("post_sell_profit_rate"),
            None,
        )
        if profit is None:
            continue
        values[(_context_bucket(fields), variant_id)].append(float(profit))
    return values


def _context_bucket(fields: dict[str, Any]) -> str:
    spread_bps = _safe_float(fields.get("spread_bps"), None)
    if spread_bps is None:
        spread_ratio = _safe_float(fields.get("spread_ratio"), None)
        spread_bps = float(spread_ratio or 0.0) * 10000.0 if spread_ratio is not None else 0.0
    buy_pressure = _safe_float(fields.get("buy_pressure_10t") or fields.get("tick_buy_pressure_10t"), 0.0) or 0.0
    micro_state = str(fields.get("orderbook_micro_state") or fields.get("micro_state") or "").lower()
    latency_state = str(fields.get("latency_state") or "").upper()
    quote_stale = _safe_bool(fields.get("quote_stale")) or _safe_bool(fields.get("stale_quote_submit_block"))
    if quote_stale or latency_state == "DANGER":
        return "guarded_or_stale"
    if spread_bps <= 12.0 and buy_pressure >= 60.0 and "weak" not in micro_state:
        return "urgent_tight_spread"
    if spread_bps >= 35.0 or buy_pressure <= 45.0 or "weak" in micro_state:
        return "passive_wide_or_weak"
    return "balanced_normal"


def _template_for_bucket(bucket: str) -> dict[str, Any]:
    templates = {
        "urgent_tight_spread": {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weight_min": 0.65,
            "qty_weight_max": 0.85,
            "urgency_score": 0.82,
            "passive_edge_score": 0.28,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick"],
        },
        "balanced_normal": {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weight_min": 0.55,
            "qty_weight_max": 0.70,
            "urgency_score": 0.55,
            "passive_edge_score": 0.52,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick", "reference_target", "AI_candidate"],
        },
        "passive_wide_or_weak": {
            "leg_count": 3,
            "price_offsets_ticks": [0, 1, 2],
            "price_offsets_pct": [0.0, 0.3, 0.8],
            "qty_weight_min": 0.30,
            "qty_weight_max": 0.50,
            "urgency_score": 0.30,
            "passive_edge_score": 0.78,
            "price_candidates": ["best_bid", "bid-1tick", "bid-2tick", "reference_target"],
        },
        "guarded_or_stale": {
            "leg_count": 1,
            "price_offsets_ticks": [0],
            "price_offsets_pct": [0.0],
            "qty_weight_min": 1.0,
            "qty_weight_max": 1.0,
            "urgency_score": 0.0,
            "passive_edge_score": 0.0,
            "price_candidates": ["resolved_order_price"],
        },
    }
    return dict(templates.get(bucket) or templates["balanced_normal"])


def _bounded_equal_split_template(bucket: str) -> dict[str, Any]:
    template = _template_for_bucket(bucket)
    template.update(
        {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick"],
            "split_variant_id": BASELINE_SPLIT_VARIANT_ID,
        }
    )
    return template


def _post_submit_tick_band_template(bucket: str, tick_band: dict[str, Any]) -> dict[str, Any]:
    template = _bounded_equal_split_template(bucket)
    sample = _safe_int(tick_band.get("sample_count"), 0)
    p75 = _safe_float(tick_band.get("p75_down_ticks"), 0.0) or 0.0
    touch2 = _safe_float(tick_band.get("touch_2tick_rate"), 0.0) or 0.0
    if sample >= POST_SUBMIT_TICK_BAND_FLOOR_REAL and p75 >= 2.0 and touch2 >= 50.0:
        template.update(
            {
                "leg_count": 3,
                "price_offsets_ticks": [0, 1, 2],
                "price_offsets_pct": [0.0, 0.3, 0.8],
                "qty_weight_min": 0.34,
                "qty_weight_max": 0.34,
                "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick", "bid-2tick"],
                "split_variant_id": PCT_BAND_3LEG_VARIANT_ID,
            }
        )
    return template


def _pct_price_offset(base_price: int, offset_pct: float) -> int:
    if base_price <= 0:
        return 0
    raw_price = int(round(float(base_price) * max(0.0, 1.0 - (float(offset_pct or 0.0) / 100.0))))
    return clamp_price_to_tick(max(1, raw_price))


def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(int(value) for value in values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * max(0.0, min(100.0, float(pct))) / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return float(ordered[lower])
    weight = rank - lower
    return (ordered[lower] * (1.0 - weight)) + (ordered[upper] * weight)


def _post_submit_observed_prices(fields: dict[str, Any]) -> list[int]:
    prices: list[int] = []
    for key in (
        "current_price_observed",
        "current_price",
        "latest_price",
        "holding_ws_recovered_curr",
        "curr_price",
        "mark_price_at_submit",
        "submitted_mark_price",
    ):
        value = _safe_int(fields.get(key), 0)
        if value > 0:
            prices.append(value)
    return prices


def _submit_order_price(fields: dict[str, Any]) -> int:
    return _safe_int(
        fields.get("order_price")
        or fields.get("submitted_order_price")
        or fields.get("resolved_order_price")
        or fields.get("price")
        or fields.get("submitted_price"),
        0,
    )


def _build_post_submit_low_tick_bands(
    events: list[dict[str, Any]],
    *,
    source_quality: dict[str, Any] | None = None,
    window_minutes: int = POST_SUBMIT_LOW_WINDOW_MINUTES,
) -> dict[str, dict[str, Any]]:
    blocked_stages = set((source_quality or {}).get("hard_blocking_stages") or [])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for fields in events:
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        if stage in blocked_stages:
            continue
        record_id = str(fields.get("record_id") or "").strip()
        code = str(fields.get("stock_code") or "").strip()
        if not record_id or not code:
            continue
        grouped[(record_id, code)].append(fields)

    down_ticks_by_bucket: dict[str, list[int]] = defaultdict(list)
    down_pct_by_bucket: dict[str, list[float]] = defaultdict(list)
    for group in grouped.values():
        dated = [(item, _event_dt(item)) for item in group]
        for submit, submit_dt in dated:
            stage = str(submit.get("stage") or submit.get("event") or "").strip()
            if stage != "order_bundle_submitted":
                continue
            if not _safe_bool(submit.get("actual_order_submitted")):
                continue
            if submit_dt is None:
                continue
            submit_price = _submit_order_price(submit)
            if submit_price <= 0:
                continue
            observed_prices: list[int] = []
            for item, item_dt in dated:
                if item_dt is None:
                    continue
                if item_dt < submit_dt:
                    continue
                if item_dt > submit_dt + timedelta(minutes=window_minutes):
                    continue
                observed_prices.extend(_post_submit_observed_prices(item))
            if not observed_prices:
                continue
            low_price = min(observed_prices)
            tick = max(1, int(get_tick_size(submit_price) or 1))
            down_ticks = max(0, int(math.ceil((submit_price - low_price) / tick)))
            down_pct = max(0.0, ((submit_price - low_price) / submit_price) * 100.0)
            bucket = _context_bucket(submit)
            down_ticks_by_bucket[bucket].append(down_ticks)
            down_pct_by_bucket[bucket].append(down_pct)

    result: dict[str, dict[str, Any]] = {}
    for bucket, values in down_ticks_by_bucket.items():
        sample = len(values)
        pct_values = down_pct_by_bucket.get(bucket) or []
        result[bucket] = {
            "sample_count": sample,
            "window_minutes": int(window_minutes),
            "source": "runtime_post_submit_observed_prices",
            "p50_down_ticks": round(_percentile(values, 50), 3),
            "p75_down_ticks": round(_percentile(values, 75), 3),
            "p90_down_ticks": round(_percentile(values, 90), 3),
            "max_down_ticks": max(values) if values else 0,
            "touch_1tick_rate": _pct(sum(1 for value in values if value >= 1), sample),
            "touch_2tick_rate": _pct(sum(1 for value in values if value >= 2), sample),
            "p50_down_pct": round(_percentile([int(value * 10000) for value in pct_values], 50) / 10000.0, 4)
            if pct_values
            else 0.0,
            "p75_down_pct": round(_percentile([int(value * 10000) for value in pct_values], 75) / 10000.0, 4)
            if pct_values
            else 0.0,
            "p90_down_pct": round(_percentile([int(value * 10000) for value in pct_values], 90) / 10000.0, 4)
            if pct_values
            else 0.0,
            "touch_0_3pct_rate": _pct(sum(1 for value in pct_values if value >= 0.3), sample),
            "touch_0_5pct_rate": _pct(sum(1 for value in pct_values if value >= 0.5), sample),
            "touch_0_8pct_rate": _pct(sum(1 for value in pct_values if value >= 0.8), sample),
            "touch_1_0pct_rate": _pct(sum(1 for value in pct_values if value >= 1.0), sample),
            "touch_1_5pct_rate": _pct(sum(1 for value in pct_values if value >= 1.5), sample),
            "no_pullback_rate": _pct(sum(1 for value in values if value <= 0), sample),
        }
    return result


def _is_real_submit_event(fields: dict[str, Any]) -> bool:
    return _safe_bool(fields.get("actual_order_submitted"))


def _is_sim_event(fields: dict[str, Any]) -> bool:
    stage = str(fields.get("stage") or fields.get("event") or "").strip()
    if str(stage).startswith("scalp_sim_"):
        return True
    decision_authority = str(fields.get("decision_authority") or "").strip()
    if decision_authority in {"sim_observation_only", "swing_sim_exploration_only"}:
        return True
    if _safe_bool(fields.get("broker_order_forbidden")) and ("sim" in stage or "probe" in stage):
        return True
    return False


def _quality_counts(events: list[dict[str, Any]], source_quality: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], int]:
    blocked_stages = set(source_quality.get("hard_blocking_stages") or [])
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))
    excluded_source_quality = 0
    for fields in events:
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        if stage in blocked_stages:
            excluded_source_quality += 1
            continue
        bucket = _context_bucket(fields)
        row = buckets[bucket]
        if _is_real_submit_event(fields):
            row["real_sample_count"] += 1
            if stage == "order_leg_sent" or _safe_bool(fields.get("broker_order_submitted")):
                row["real_submitted_count"] += 1
            if str(fields.get("fill_status") or "").upper() == "PARTIAL" or _safe_int(fields.get("filled_qty"), 0) > 0:
                row["partial_fill_count"] += 1
            if stage in {"order_leg_fail", "order_bundle_failed"}:
                row["cancel_or_fail_count"] += 1
            if _safe_bool(fields.get("late_fill")) or _safe_bool(fields.get("late_fill_detected")):
                row["late_fill_count"] += 1
        if _is_sim_event(fields):
            row["sim_sample_count"] += 1
            if stage in {"scalp_sim_buy_order_assumed_filled", "scalp_sim_sell_order_assumed_filled"}:
                row["sim_fill_count"] += 1
            if stage in {"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"}:
                row["cancel_or_fail_count"] += 1
    return {key: dict(value) for key, value in buckets.items()}, excluded_source_quality


def _pct(count: int, total: int) -> float:
    return round((count / total) * 100.0, 4) if total > 0 else 0.0


def _build_candidate_grid(
    buckets: dict[str, dict[str, Any]],
    sim_ev_values: dict[str, list[float]],
    real_ev_values: dict[str, list[float]],
    real_split_variant_ev_values: dict[tuple[str, str], list[float]] | None = None,
    post_submit_low_tick_bands: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    grid: list[dict[str, Any]] = []
    real_split_variant_ev_values = real_split_variant_ev_values or {}
    post_submit_low_tick_bands = post_submit_low_tick_bands or {}
    split_variant_buckets = {bucket for bucket, _variant_id in real_split_variant_ev_values}
    for bucket in sorted(
        set(buckets) | set(sim_ev_values) | set(real_ev_values) | split_variant_buckets | set(post_submit_low_tick_bands)
    ):
        counts = buckets.get(bucket) or {}
        template = _template_for_bucket(bucket)
        tick_band = post_submit_low_tick_bands.get(bucket) or {}
        real_count = _safe_int(counts.get("real_sample_count"), 0)
        sim_count = _safe_int(counts.get("sim_sample_count"), 0)
        total = max(1, real_count + sim_count)
        real_ev_list = real_ev_values.get(bucket) or []
        sim_ev_list = sim_ev_values.get(bucket) or []
        real_bucket_outcome_count = len(real_ev_list)
        real_bucket_ev = round(mean(real_ev_list), 4) if real_ev_list else None
        sim_ev = round(mean(sim_ev_list), 4) if sim_ev_list else None
        split_variant_id = ""
        if bucket != "guarded_or_stale":
            template = _post_submit_tick_band_template(bucket, tick_band)
            split_variant_id = BASELINE_SPLIT_VARIANT_ID
            if template.get("split_variant_id"):
                split_variant_id = str(template.get("split_variant_id") or BASELINE_SPLIT_VARIANT_ID)
        split_variant_ev_list = real_split_variant_ev_values.get((bucket, split_variant_id)) if split_variant_id else []
        split_variant_outcome_count = len(split_variant_ev_list or [])
        split_variant_ev = round(mean(split_variant_ev_list), 4) if split_variant_ev_list else None
        primary_ev = split_variant_ev if split_variant_ev is not None else None
        notional_ev = primary_ev
        partial_fill_rate = _pct(_safe_int(counts.get("partial_fill_count"), 0), max(real_count, 1))
        cancel_rate = _pct(_safe_int(counts.get("cancel_or_fail_count"), 0), total)
        late_fill_rate = _pct(_safe_int(counts.get("late_fill_count"), 0), max(real_count, 1))
        downside_source = split_variant_ev_list or []
        downside = sorted(downside_source)[max(0, int(len(downside_source) * 0.10) - 1)] if downside_source else 0.0
        split_variant_outcome_ready = split_variant_outcome_count >= SPLIT_VARIANT_OUTCOME_FLOOR_REAL
        ev_passed = (
            bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and split_variant_outcome_ready
            and split_variant_ev is not None
            and split_variant_ev > 0
            and downside > -2.0
        )
        execution_shape_seed_passed = (
            bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and not split_variant_outcome_ready
            and cancel_rate <= 20.0
            and late_fill_rate <= 20.0
        )
        policy_mode = ""
        policy_generation_reason = ""
        if ev_passed:
            floor_status = "pass_real_primary_ev"
            primary_sample_book = "real_split_variant"
            policy_mode = POLICY_MODE_REAL_PRIMARY_EV
            policy_generation_reason = "real split variant outcome EV passed sample/downside guards"
        elif execution_shape_seed_passed:
            tick_sample = _safe_int(tick_band.get("sample_count"), 0)
            if template.get("leg_count") == 3 and tick_sample >= POST_SUBMIT_TICK_BAND_FLOOR_REAL:
                floor_status = "pass_post_submit_tick_band_seed"
                primary_sample_book = "real_submit_post_submit_observed_low"
                policy_mode = POLICY_MODE_POST_SUBMIT_TICK_BAND
                policy_generation_reason = (
                    "real submit sample floor and post-submit observed low tick-band passed; "
                    "open a qty-preserving 3-leg 0/0.3/0.8pct seed"
                )
            else:
                floor_status = "pass_bounded_equal_split_baseline"
                primary_sample_book = "real_submit_execution_shape"
                policy_mode = POLICY_MODE_BOUNDED_EQUAL_BASELINE
                policy_generation_reason = (
                    "real submit sample floor passed, split-variant outcome is pending, and execution guards allow "
                    "a qty-preserving 2-leg 50/50 0.3pct baseline"
                )
        elif real_count < SAMPLE_FLOOR_REAL:
            floor_status = "hold_sample"
            primary_sample_book = "none"
        elif split_variant_outcome_ready:
            floor_status = "hold_no_split_variant_edge"
            primary_sample_book = "real_split_variant"
        elif sim_count >= SAMPLE_FLOOR_SIM and sim_ev is not None:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "sim_diagnostic"
        else:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "real_outcome_pending"
        passed = ev_passed or execution_shape_seed_passed
        grid.append(
            {
                "context_bucket": bucket,
                **template,
                "price_candidates": [item for item in template["price_candidates"] if item in ALLOWED_PRICE_CANDIDATES],
                "real_sample_count": real_count,
                "sim_sample_count": sim_count,
                "real_outcome_joined_sample": real_bucket_outcome_count,
                "real_bucket_outcome_ev_pct": real_bucket_ev,
                "real_split_variant_outcome_joined_sample": split_variant_outcome_count,
                "real_split_variant_ev_pct": split_variant_ev,
                "split_variant_id": split_variant_id,
                "optimization_basis": (
                    "split_variant_outcome"
                    if ev_passed
                    else "post_submit_observed_low_tick_band"
                    if policy_mode == POLICY_MODE_POST_SUBMIT_TICK_BAND
                    else "bounded_execution_shape_seed"
                ),
                "post_submit_low_tick_band": tick_band,
                "primary_sample_book": primary_sample_book,
                "fill_quality": round(
                    (_safe_int(counts.get("real_submitted_count"), 0) + _safe_int(counts.get("sim_fill_count"), 0))
                    / total,
                    4,
                ),
                "missed_upside": round(max(0.0, primary_ev or 0.0), 4),
                "source_quality_adjusted_ev_pct": primary_ev,
                "real_source_quality_adjusted_ev_pct": split_variant_ev,
                "diagnostic_sim_ev_pct": sim_ev,
                "notional_weighted_ev_pct": notional_ev,
                "partial_fill_rate": partial_fill_rate,
                "cancel_rate": cancel_rate,
                "late_fill_rate": late_fill_rate,
                "downside_p10_profit_rate": round(float(downside), 4),
                "sample_floor_status": floor_status,
                "policy_mode": policy_mode,
                "policy_generation_reason": policy_generation_reason,
                "candidate_passed": passed,
            }
        )
    return grid


def _policy_payload(target_date: str, report_json: Path, candidate_grid: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [item for item in candidate_grid if item.get("candidate_passed")]
    version_seed = json.dumps(passed, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha1(version_seed.encode("utf-8")).hexdigest()[:10]
    policy_version = f"{RUNTIME_FAMILY}:{target_date}:{digest}"
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_version": policy_version,
        "source_date": target_date,
        "source_report": str(report_json),
        "runtime_apply_allowed": False,
        "preopen_guard_required": True,
        "decision_authority": "next_preopen_bounded_entry_split_policy",
        "forbidden_uses": [
            "increase_requested_qty",
            "cap_release",
            "broker_guard_relief",
            "intraday_mutation",
            "provider_route_change",
        ],
        "buckets": {
            str(item["context_bucket"]): {
                "context_bucket": item["context_bucket"],
                "leg_count": item["leg_count"],
                "price_offsets_ticks": item["price_offsets_ticks"],
                "price_offsets_pct": item.get("price_offsets_pct"),
                "qty_weight_min": item["qty_weight_min"],
                "qty_weight_max": item["qty_weight_max"],
                "urgency_score": item["urgency_score"],
                "passive_edge_score": item["passive_edge_score"],
                "policy_mode": item.get("policy_mode") or POLICY_MODE_REAL_PRIMARY_EV,
                "policy_generation_reason": item.get("policy_generation_reason") or "",
                "primary_sample_book": item.get("primary_sample_book"),
                "real_sample_count": item.get("real_sample_count"),
                "real_outcome_joined_sample": item.get("real_outcome_joined_sample"),
                "real_split_variant_outcome_joined_sample": item.get("real_split_variant_outcome_joined_sample"),
                "split_variant_id": item.get("split_variant_id"),
                "optimization_basis": item.get("optimization_basis"),
                "post_submit_low_tick_band": item.get("post_submit_low_tick_band"),
                "source_quality_adjusted_ev_pct": item["source_quality_adjusted_ev_pct"],
                "notional_weighted_ev_pct": item["notional_weighted_ev_pct"],
                "downside_p10_profit_rate": item["downside_p10_profit_rate"],
            }
            for item in passed
        },
    }


def build_report(target_date: str, *, write: bool = True) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_quality = _source_quality_summary(target_date)
    events, load_summary = _iter_input_events(target_date)
    counts, excluded_source_quality = _quality_counts(events, source_quality)
    sim_ev_values = _load_sim_ev_values(target_date)
    real_ev_values = _load_real_ev_values(target_date)
    real_split_variant_ev_values = _load_real_split_variant_ev_values(target_date)
    post_submit_low_tick_bands = _build_post_submit_low_tick_bands(events, source_quality=source_quality)
    candidate_grid = _build_candidate_grid(
        counts,
        sim_ev_values,
        real_ev_values,
        real_split_variant_ev_values,
        post_submit_low_tick_bands,
    )
    json_path, md_path = report_paths(target_date)
    policy_json = policy_path(target_date)
    source_quality_allowed = source_quality.get("tuning_input_allowed") is True
    policy = _policy_payload(target_date, json_path, candidate_grid if source_quality_allowed else [])
    recommended_candidates = [
        {**item, "runtime_apply_allowed": False}
        for item in candidate_grid
        if source_quality_allowed and item.get("candidate_passed")
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "next_preopen_bounded_entry_split_policy",
            "window_policy": "rolling_10d_with_daily_diagnostic",
            "sample_floor": {"real": SAMPLE_FLOOR_REAL, "sim": SAMPLE_FLOOR_SIM},
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "observation_source_quality_audit_hard_block_rows_excluded",
            "policy_modes": {
                POLICY_MODE_REAL_PRIMARY_EV: "real split-variant outcome EV-positive optimized split",
                POLICY_MODE_BOUNDED_EQUAL_BASELINE: "real-submit-backed qty-preserving 2-leg 50/50 0.3pct baseline",
                POLICY_MODE_POST_SUBMIT_TICK_BAND: "post-submit observed-low tick-band qty-preserving seed",
            },
            "post_submit_low_tick_band_contract": {
                "metric_role": "execution_shape_seed",
                "decision_authority": "next_preopen_bounded_entry_split_policy",
                "window_policy": f"same_day_submit_plus_{POST_SUBMIT_LOW_WINDOW_MINUTES}m_runtime_observed_prices",
                "sample_floor": {"real_submit_observed_low": POST_SUBMIT_TICK_BAND_FLOOR_REAL},
                "primary_decision_metric": "p75_down_ticks",
                "source_quality_gate": "actual_order_submitted=true and post-submit runtime observed prices present",
                "forbidden_uses": [
                    "claim_split_variant_ev_without_variant_outcome",
                    "increase_requested_qty",
                    "broker_guard_relief",
                    "intraday_mutation",
                ],
            },
            "optimization_contract": (
                "Post-sell profit_rate is only split-policy primary EV when it is joined to an applied "
                "entry_split_order_variant_id. Bucket-only sell outcome is diagnostic."
            ),
            "forbidden_uses": [
                "requested_qty_increase",
                "real_execution_quality_approval_from_sim",
                "intraday_threshold_mutation",
                "broker_guard_relief",
            ],
        },
        "source_quality": source_quality,
        "input_summary": {
            **load_summary,
            "loaded_event_count": len(events),
            "excluded_source_quality_event_count": excluded_source_quality,
            "sim_post_sell_path": str(_sim_post_sell_path(target_date)) if _sim_post_sell_path(target_date).exists() else None,
            "real_post_sell_path": str(_real_post_sell_path(target_date)) if _real_post_sell_path(target_date).exists() else None,
            "threshold_cycle_ev_path": str(_threshold_cycle_ev_path(target_date)) if _threshold_cycle_ev_path(target_date).exists() else None,
            "post_submit_low_tick_band_bucket_count": len(post_submit_low_tick_bands),
        },
        "candidate_grid": candidate_grid,
        "recommended_policy": {
            "runtime_apply_allowed": False,
            "preopen_guard_required": True,
            "policy_file": str(policy_json),
            "policy_version": policy["policy_version"],
            "candidate_count": len(recommended_candidates),
            "candidates": recommended_candidates,
        },
    }
    if write:
        _write_json(json_path, report)
        _write_json(policy_json, policy)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    rec = report.get("recommended_policy") if isinstance(report.get("recommended_policy"), dict) else {}
    lines = [
        f"# Entry Split Order Plan - {report.get('date')}",
        "",
        "## Summary",
        f"- schema_version: `{report.get('schema_version')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- recommended_policy_candidates: `{rec.get('candidate_count')}`",
        f"- runtime_apply_allowed: `{rec.get('runtime_apply_allowed')}`",
        f"- policy_file: `{rec.get('policy_file') or '-'}`",
        "",
        "## Candidate Grid",
    ]
    for item in report.get("candidate_grid") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            "- "
            f"`{item.get('context_bucket')}` legs=`{item.get('leg_count')}` "
            f"mode=`{item.get('policy_mode') or '-'}` "
            f"real/sim=`{item.get('real_sample_count')}/{item.get('sim_sample_count')}` "
            f"ev=`{item.get('source_quality_adjusted_ev_pct')}` "
            f"bucket_ev=`{item.get('real_bucket_outcome_ev_pct')}` "
            f"p75_down_ticks=`{((item.get('post_submit_low_tick_band') or {}).get('p75_down_ticks'))}` "
            f"cancel=`{item.get('cancel_rate')}` "
            f"pass=`{item.get('candidate_passed')}`"
        )
    return "\n".join(lines) + "\n"


def _load_policy_from_env(
    policy_file: str | None = None,
    *,
    now: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    enabled = str(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "")).strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return {}, "policy_disabled"
    active_date = str(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE") or "").strip()
    if active_date:
        now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date().isoformat()
        if active_date != now_date:
            return {}, "policy_inactive_date"
    path_text = str(policy_file or os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE") or "").strip()
    if not path_text:
        return {}, "policy_file_missing"
    path = Path(path_text)
    if not path.exists():
        return {}, "policy_file_not_found"
    payload = _load_json(path)
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        return {}, "invalid_policy_schema"
    if not isinstance(payload.get("buckets"), dict):
        return {}, "invalid_policy_buckets"
    if "runtime_apply_allowed" in payload and not _safe_bool(payload.get("runtime_apply_allowed")):
        if not _entry_split_operator_fallback_active(now=now):
            return {}, "policy_runtime_apply_not_allowed"
        payload = {
            **payload,
            "entry_split_order_operator_fallback_authorized": True,
        }
    return payload, "loaded"


def _policy_is_stale(policy: dict[str, Any], *, now: datetime | None = None, max_age_days: int = 5) -> bool:
    source_date = str(policy.get("source_date") or "").strip()
    if not source_date:
        return True
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date()
    try:
        policy_date = date.fromisoformat(source_date)
    except ValueError:
        return True
    return now_date - policy_date > timedelta(days=max_age_days)


def _max_legs_for_qty(qty: int) -> int:
    if qty <= 1:
        return 1
    if qty == 2:
        return 2
    if 3 <= qty <= 5:
        return 2
    return 3


def _split_qty(total_qty: int, leg_count: int, first_weight: float) -> list[int]:
    leg_count = min(max(1, leg_count), total_qty)
    if leg_count <= 1:
        return [total_qty]
    first_qty = max(1, min(total_qty - (leg_count - 1), int(round(total_qty * first_weight))))
    remaining = total_qty - first_qty
    quantities = [first_qty]
    for idx in range(leg_count - 1):
        legs_left = leg_count - 1 - idx
        qty = max(1, remaining // legs_left)
        quantities.append(qty)
        remaining -= qty
    if sum(quantities) != total_qty:
        quantities[-1] += total_qty - sum(quantities)
    return quantities


def _tick_size(price: int) -> int:
    try:
        from src.utils import kiwoom_utils

        return max(1, int(kiwoom_utils.get_tick_size(price) or 1))
    except Exception:
        return 1


def _runtime_default_bucket_policy(bucket: str) -> dict[str, Any]:
    return {
        "context_bucket": bucket,
        "leg_count": 2,
        "price_offsets_ticks": [0, 1],
        "price_offsets_pct": [0.0, 0.3],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "policy_mode": RUNTIME_FALLBACK_POLICY_MODE,
        "split_variant_id": RUNTIME_FALLBACK_VARIANT_ID,
        "policy_generation_reason": "runtime fallback for policy bucket gap; qty-preserving passive-centered 0.3pct seed",
    }


def _has_present_value(fields: dict[str, Any], key: str) -> bool:
    value = fields.get(key)
    return value not in (None, "", "-", "unknown", "not_available")


def _split_allocator_stale_quote_blocked(fields: dict[str, Any]) -> bool:
    if _safe_bool(fields.get("stale_quote_submit_block")):
        return True
    for key in ("quote_stale_at_submit", "pre_submit_effective_quote_stale"):
        if _safe_bool(fields.get(key)):
            return True
    if any(_has_present_value(fields, key) for key in ("quote_stale_at_submit", "pre_submit_effective_quote_stale")):
        return False
    return _safe_bool(fields.get("quote_stale"))


def _spread_bps_from_fields(fields: dict[str, Any]) -> float:
    spread_bps = _safe_float(fields.get("spread_bps"), None)
    if spread_bps is not None:
        return float(spread_bps)
    spread_ratio = _safe_float(fields.get("spread_ratio"), None)
    return float(spread_ratio or 0.0) * 10000.0 if spread_ratio is not None else 0.0


def _entry_split_passive_bias_reason(fields: dict[str, Any]) -> str:
    action_tokens = {
        str(fields.get(key) or "").strip().upper()
        for key in (
            "ai_action",
            "action",
            "chosen_action",
            "entry_ai_action",
            "entry_ai_submit_authority_action",
            "last_watching_ai_action",
        )
    }
    if "WAIT" not in action_tokens:
        return ""
    reasons: list[str] = []
    if _safe_bool(fields.get("quote_stale")) or _safe_bool(fields.get("ai_input_quote_stale")):
        reasons.append("quote_stale_warning")
    if _spread_bps_from_fields(fields) >= 35.0:
        reasons.append("high_spread")
    text = " ".join(
        str(fields.get(key) or "").lower()
        for key in (
            "reason",
            "block_reason",
            "policy_reason",
            "latency_danger_reasons",
            "latency_danger_detail_reason",
            "entry_submit_revalidation_warning",
            "entry_price_gap_profile_reason",
            "ai_entry_price_canary_reason",
            "entry_ai_submit_authority_reason",
            "submit_quality_parent",
        )
    )
    text_markers = {
        "stale_quote": ("stale quote", "quote_stale", "stale_snapshot", "diagnostic_quote_age_stale"),
        "high_spread": ("high spread", "wide spread", "spread_too_wide", "spread=wide"),
    }
    for reason, markers in text_markers.items():
        if any(marker in text for marker in markers) and reason not in reasons:
            reasons.append(reason)
    if not reasons:
        return ""
    return "ai_wait_with_" + "+".join(reasons)


def _entry_split_passive_bias_first_weight(
    policy_first_weight: float,
    fields: dict[str, Any],
) -> tuple[float, str]:
    reason = _entry_split_passive_bias_reason(fields)
    if reason:
        return min(policy_first_weight, PASSIVE_BIAS_WAIT_WARNING_FIRST_WEIGHT), reason
    passive_center_weight = min(policy_first_weight, PASSIVE_CENTER_MAX_FIRST_WEIGHT)
    if passive_center_weight < policy_first_weight:
        return passive_center_weight, "passive_center_first_leg_cap"
    return policy_first_weight, ""


def _market_first_leg_active(*, now: datetime | None = None) -> bool:
    if not _safe_bool(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED")):
        return False
    active_date = str(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE") or "").strip()
    if not active_date:
        return False
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date().isoformat()
    return active_date == now_date


def _entry_split_operator_fallback_active(*, now: datetime | None = None) -> bool:
    if not _safe_bool(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED")):
        return False
    active_date = str(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE") or "").strip()
    if not active_date:
        return False
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date().isoformat()
    return active_date == now_date


def _market_first_leg_reference_price(fields: dict[str, Any], base_price: int) -> int:
    for key in (
        "best_ask_at_submit",
        "executable_buy_price",
        "best_ask",
        "latest_price",
        "canonical_mark_price",
    ):
        value = _safe_int(fields.get(key), 0)
        if value > 0:
            return value
    return max(0, int(base_price or 0))


def apply_entry_split_order_policy(
    planned_orders: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    stock: dict[str, Any] | None = None,
    latency_gate: dict[str, Any] | None = None,
    policy_file: str | None = None,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    orders = [dict(item) for item in (planned_orders or []) if isinstance(item, dict)]
    latency_gate = latency_gate if isinstance(latency_gate, dict) else {}
    stock = stock if isinstance(stock, dict) else {}
    total_qty = sum(_safe_int(item.get("qty"), 0) for item in orders)
    fields: dict[str, Any] = {
        "entry_split_order_policy_applied": False,
        "entry_split_order_original_order_count": len(orders),
        "entry_split_order_original_qty": total_qty,
    }
    if total_qty <= 1:
        fields["entry_split_order_skip_reason"] = "qty_lte_1"
        return orders, fields
    if len(orders) != 1:
        fields["entry_split_order_skip_reason"] = "multi_order_input_not_supported_v1"
        return orders, fields
    if _split_allocator_stale_quote_blocked(latency_gate):
        fields["entry_split_order_skip_reason"] = "stale_quote"
        return orders, fields
    if str(latency_gate.get("latency_state") or "").upper() == "DANGER" and not _safe_bool(
        latency_gate.get("latency_canary_applied")
    ):
        fields["entry_split_order_skip_reason"] = "danger_latency_without_approved_relief"
        return orders, fields
    policy, load_status = _load_policy_from_env(policy_file, now=now)
    if not policy:
        fields["entry_split_order_skip_reason"] = load_status
        return orders, fields
    if _policy_is_stale(policy, now=now):
        fields["entry_split_order_skip_reason"] = "stale_policy"
        return orders, fields
    context_fields = {**stock, **latency_gate}
    bucket = _context_bucket(context_fields)
    bucket_policy = (policy.get("buckets") or {}).get(bucket)
    fallback_policy_applied = False
    if not isinstance(bucket_policy, dict):
        bucket_policy = _runtime_default_bucket_policy(bucket)
        fallback_policy_applied = True
    policy_mode = str(bucket_policy.get("policy_mode") or "").strip()
    policy_split_variant_id = str(bucket_policy.get("split_variant_id") or "").strip() or _split_variant_id_from_fields(
        {
            "entry_split_order_policy_applied": True,
            "entry_split_order_policy_mode": policy_mode,
            "entry_split_order_leg_count": bucket_policy.get("leg_count"),
            "entry_split_order_price_offsets_ticks": ",".join(
                str(item) for item in (bucket_policy.get("price_offsets_ticks") or [])
            ),
            "entry_split_order_qty_weight_min": bucket_policy.get("qty_weight_min"),
        }
    )
    max_legs = _max_legs_for_qty(total_qty)
    desired_legs = min(_safe_int(bucket_policy.get("leg_count"), 1), max_legs, total_qty)
    if desired_legs <= 1:
        fields["entry_split_order_skip_reason"] = "single_leg_policy"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    base_order = orders[0]
    base_price = _safe_int(
        base_order.get("price")
        or latency_gate.get("order_price")
        or latency_gate.get("resolved_order_price")
        or latency_gate.get("best_bid")
        or stock.get("curr_price"),
        0,
    )
    if base_price <= 0:
        fields["entry_split_order_skip_reason"] = "invalid_base_price"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    tick = _tick_size(base_price)
    offsets = [
        _safe_int(item, 0)
        for item in (bucket_policy.get("price_offsets_ticks") or [0])
        if _safe_int(item, 0) in {0, 1, 2}
    ][:desired_legs]
    while len(offsets) < desired_legs:
        offsets.append(offsets[-1] + 1 if offsets else 0)
    policy_first_weight = (_safe_float(bucket_policy.get("qty_weight_min"), 0.5) or 0.5)
    market_first_leg_active = _market_first_leg_active(now=now)
    if market_first_leg_active:
        first_weight = policy_first_weight
        passive_bias_reason = ""
    else:
        first_weight, passive_bias_reason = _entry_split_passive_bias_first_weight(
            policy_first_weight,
            context_fields,
        )
    runtime_weight_adjusted = abs(float(first_weight) - float(policy_first_weight)) > 0.000001
    split_variant_id = policy_split_variant_id
    if runtime_weight_adjusted:
        split_variant_id = (
            f"{policy_split_variant_id}__runtime_first_weight_{int(round(first_weight * 100)):02d}"
        )
    quantities = _split_qty(total_qty, desired_legs, first_weight)
    applied_offsets = offsets[:desired_legs]
    raw_pct_offsets = bucket_policy.get("price_offsets_pct")
    pct_offsets = [
        max(0.0, _safe_float(item, 0.0) or 0.0)
        for item in raw_pct_offsets
    ][:desired_legs] if isinstance(raw_pct_offsets, list) else []
    while pct_offsets and len(pct_offsets) < desired_legs:
        pct_offsets.append(pct_offsets[-1])
    market_first_reference_price = _market_first_leg_reference_price(context_fields, base_price)
    split_orders: list[dict[str, Any]] = []
    for idx, qty in enumerate(quantities):
        price = (
            _pct_price_offset(base_price, pct_offsets[idx])
            if pct_offsets
            else clamp_price_to_tick(max(1, base_price - (tick * offsets[idx])))
        )
        split_orders.append(
            {
                **base_order,
                "tag": "entry_split_primary" if idx == 0 else f"entry_split_passive_{idx}",
                "qty": qty,
                "price": price,
                "order_type_code": "3" if market_first_leg_active and idx == 0 else base_order.get("order_type_code", "00"),
                "entry_split_order_execution_mode": (
                    "market_first" if market_first_leg_active and idx == 0 else "resolver_limit"
                ),
                "entry_split_order_market_first_leg_applied": bool(market_first_leg_active and idx == 0),
                "entry_split_order_market_reference_price": (
                    market_first_reference_price if market_first_leg_active and idx == 0 else 0
                ),
                "entry_split_order_leg_index": idx + 1,
                "entry_split_order_policy_version": policy.get("policy_version"),
                "entry_split_order_policy_mode": policy_mode,
                "entry_split_order_variant_id": split_variant_id,
                "entry_split_order_policy_variant_id": policy_split_variant_id,
                "entry_split_order_bucket": bucket,
                "entry_split_order_runtime_default_policy_applied": fallback_policy_applied,
                "entry_split_order_operator_fallback_authorized": bool(
                    policy.get("entry_split_order_operator_fallback_authorized")
                ),
                "entry_split_order_price_offsets_ticks": ",".join(str(item) for item in applied_offsets),
                "entry_split_order_price_offsets_pct": ",".join(str(item) for item in pct_offsets) if pct_offsets else "",
                "entry_split_order_price_offset_ticks": applied_offsets[idx],
                "entry_split_order_price_offset_pct": pct_offsets[idx] if pct_offsets else "",
                "split_price_offset_ticks": applied_offsets[idx],
                "split_price_offset_pct": pct_offsets[idx] if pct_offsets else "",
                "split_leg_role": "primary" if idx == 0 else "passive",
                "entry_split_order_qty_weight_min": first_weight,
                "entry_split_order_qty_weight_max": min(
                    _safe_float(bucket_policy.get("qty_weight_max"), first_weight) or first_weight,
                    first_weight,
                ),
                "entry_split_order_runtime_weight_adjustment_applied": runtime_weight_adjusted,
            }
        )
    if sum(_safe_int(item.get("qty"), 0) for item in split_orders) != total_qty:
        fields["entry_split_order_skip_reason"] = "quantity_conservation_failed"
        return orders, fields
    fields.update(
        {
            "entry_split_order_policy_applied": True,
            "entry_split_order_skip_reason": "",
            "entry_split_order_bucket": bucket,
            "entry_split_order_policy_version": policy.get("policy_version"),
            "entry_split_order_policy_mode": policy_mode,
            "entry_split_order_variant_id": split_variant_id,
            "entry_split_order_policy_variant_id": policy_split_variant_id,
            "entry_split_order_runtime_default_policy_applied": fallback_policy_applied,
            "entry_split_order_operator_fallback_authorized": bool(
                policy.get("entry_split_order_operator_fallback_authorized")
            ),
            "entry_split_order_market_first_leg_enabled": market_first_leg_active,
            "entry_split_order_market_first_leg_applied": market_first_leg_active,
            "entry_split_order_market_first_leg_active_date": str(
                os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE") or ""
            ),
            "entry_split_order_market_first_leg_qty": quantities[0] if market_first_leg_active else 0,
            "entry_split_order_market_reference_price": (
                market_first_reference_price if market_first_leg_active else 0
            ),
            "entry_split_order_policy_file": policy_file
            or os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"),
            "entry_split_order_leg_count": len(split_orders),
            "entry_split_order_split_qty": sum(_safe_int(item.get("qty"), 0) for item in split_orders),
            "entry_split_order_price_offsets_ticks": ",".join(str(item) for item in applied_offsets),
            "entry_split_order_price_offsets_pct": ",".join(str(item) for item in pct_offsets) if pct_offsets else "",
            "entry_split_order_qty_weight_min": first_weight,
            "entry_split_order_qty_weight_max": min(
                _safe_float(bucket_policy.get("qty_weight_max"), first_weight) or first_weight,
                first_weight,
            ),
            "entry_split_order_passive_bias_applied": bool(passive_bias_reason),
            "entry_split_order_passive_bias_reason": passive_bias_reason,
            "entry_split_order_policy_original_qty_weight_min": policy_first_weight,
            "entry_split_order_passive_center_max_first_weight": PASSIVE_CENTER_MAX_FIRST_WEIGHT,
            "entry_split_order_runtime_weight_adjustment_applied": runtime_weight_adjusted,
        }
    )
    return split_orders, fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", "--target-date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    build_report(args.target_date, write=not args.no_write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
