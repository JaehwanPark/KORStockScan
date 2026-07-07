"""Scale-in split order plan report and bounded runtime allocator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy, is_date_allowed
from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


SCHEMA_VERSION = "scale_in_split_order_plan_v1"
POLICY_SCHEMA_VERSION = "scale_in_split_order_policy_v1"
REPORT_TYPE = "scale_in_split_order_plan"
RUNTIME_FAMILY = "scale_in_split_order_plan"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
POLICY_DIR = DATA_DIR / "threshold_cycle" / "scale_in_split_order_policy"
POLICY_MODE_BOUNDED_EQUAL_BASELINE = "bounded_equal_scale_in_split_baseline"
POLICY_MODE_COUNTERFACTUAL_TICK_BAND = "counterfactual_tick_band_selector"
POLICY_MODE_MARKET_QTY_SPLIT_ONLY = "market_qty_split_only"
POLICY_MODE_DIAGNOSTIC_THREE_LEG = "diagnostic_three_leg_tick_band"
BASELINE_SPLIT_VARIANT_ID = "scale_in_equal_50_50_offset_0_1tick"
COUNTERFACTUAL_70_30_VARIANT_ID = "scale_in_counterfactual_70_30_offset_0_1tick"
COUNTERFACTUAL_50_50_VARIANT_ID = "scale_in_counterfactual_50_50_offset_0_1tick"
COUNTERFACTUAL_60_40_VARIANT_ID = "scale_in_counterfactual_60_40_offset_0_2tick"
MARKET_QTY_SPLIT_VARIANT_ID = "scale_in_market_qty_split_50_50"
DIAGNOSTIC_THREE_LEG_VARIANT_ID = "scale_in_diagnostic_50_25_25_offset_0_1_2tick"
RUNTIME_FALLBACK_POLICY_MODE = "runtime_default_scale_in_equal_50_50_1tick"
RUNTIME_FALLBACK_VARIANT_ID = "runtime_default_scale_in_equal_50_50_offset_0_1tick"
COUNTERFACTUAL_WINDOW_SEC = 180
ANCHOR_RECONSTRUCT_WINDOW_SEC = 5


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"scale_in_split_order_policy_{target_date}.json"


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _threshold_events_path(target_date: str) -> Path:
    return DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"


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


def _parse_event_time(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=9)))
    return parsed


def _event_time(event: dict[str, Any]) -> datetime | None:
    for key in ("emitted_at", "timestamp", "created_at", "event_time"):
        parsed = _parse_event_time(event.get(key))
        if parsed is not None:
            return parsed
    return None


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    return {**event, **fields}


def _event_date(event: dict[str, Any]) -> str:
    for key in ("date", "target_date", "source_date", "trading_date", "emitted_date"):
        value = str(event.get(key) or "").strip()
        if len(value) >= 10:
            return value[:10]
    ts = str(event.get("timestamp") or event.get("created_at") or event.get("emitted_at") or "").strip()
    return ts[:10] if len(ts) >= 10 else ""


def _source_quality_summary(target_date: str) -> dict[str, Any]:
    path = _source_quality_path(target_date)
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or ("missing" if not path.exists() else "loaded"))
    hard_gap_count = _safe_int(summary.get("hard_blocking_contract_gap_count"), 0)
    raw_row_exclusion_applied = bool(summary.get("raw_row_exclusion_applied") or payload.get("raw_row_exclusion"))
    tuning_input_allowed = summary.get("tuning_input_allowed")
    if tuning_input_allowed is None:
        tuning_input_allowed = (
            status not in {"fail", "missing", "invalid"}
            and (hard_gap_count <= 0 or raw_row_exclusion_applied)
        )
    if status in {"fail", "missing", "invalid"} or (hard_gap_count > 0 and not raw_row_exclusion_applied):
        tuning_input_allowed = False
    return {
        "artifact": str(path) if path.exists() else None,
        "status": status,
        "tuning_input_allowed": bool(tuning_input_allowed),
        "hard_blocking_contract_gap_count": hard_gap_count,
        "hard_blocking_excluded_row_count": _safe_int(summary.get("hard_blocking_excluded_row_count"), 0),
        "raw_row_exclusion_applied": raw_row_exclusion_applied,
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
        "source_paths": {
            name: str(existing_or_gzip_path(path)) if existing_or_gzip_path(path).exists() else None
            for name, path in source_paths.items()
        },
        "excluded_pre_baseline_count": excluded_pre_baseline,
        "clean_tuning_baseline": clean_policy,
    }


def _context_bucket(fields: dict[str, Any]) -> str:
    strategy = str(fields.get("strategy") or fields.get("raw_strategy") or "").strip().upper()
    strategy_bucket = "scalping" if strategy in {"SCALPING", "SCALP"} else "swing" if strategy else "unknown_strategy"
    stage = str(fields.get("stage") or "").strip()
    add_reason = str(
        fields.get("add_reason")
        or fields.get("scale_in_trigger")
        or fields.get("reason")
        or stage
        or ""
    ).strip()
    if add_reason == "stop_line_touch_mandatory_avg_down":
        reason_bucket = "stop_line_touch"
    elif add_reason == "late_loss_avg_down_retry":
        reason_bucket = "late_loss_retry"
    elif add_reason == "swing_avg_down_ok":
        reason_bucket = "swing_avg_down"
    elif "first_touch" in add_reason:
        reason_bucket = "first_touch"
    elif add_reason:
        reason_bucket = add_reason[:48]
    else:
        reason_bucket = "generic_avg_down"
    lineage = "rising_missed" if _safe_bool(fields.get("rising_missed_scout")) or "rising_missed" in str(fields).lower() else "normal"
    return f"{strategy_bucket}:{reason_bucket}:{lineage}"


def _stock_code(fields: dict[str, Any]) -> str:
    return str(fields.get("stock_code") or fields.get("code") or "").strip()[:6]


def _add_reason(fields: dict[str, Any]) -> str:
    return str(
        fields.get("add_reason")
        or fields.get("scale_in_trigger")
        or fields.get("add_trigger")
        or fields.get("reason")
        or fields.get("stage")
        or ""
    ).strip()


def _explicit_add_reason(fields: dict[str, Any]) -> str:
    return str(
        fields.get("add_reason")
        or fields.get("scale_in_trigger")
        or fields.get("add_trigger")
        or fields.get("reason")
        or ""
    ).strip()


def _record_id(fields: dict[str, Any]) -> str:
    return str(fields.get("record_id") or fields.get("recommendation_id") or fields.get("id") or "").strip()


def _order_no(fields: dict[str, Any]) -> str:
    return str(fields.get("ord_no") or fields.get("order_no") or fields.get("odno") or "").strip()


def _price_from_fields(fields: dict[str, Any], keys: tuple[str, ...]) -> int:
    for key in keys:
        price = _safe_int(fields.get(key), 0)
        if price > 0:
            return price
    return 0


def _is_market_like_order(fields: dict[str, Any], base_price: int) -> bool:
    order_type = str(fields.get("order_type_code") or fields.get("order_type") or "").strip()
    price_source = str(fields.get("price_source") or fields.get("price_policy") or "").strip()
    return order_type in {"3", "03", "6", "06", "16"} or price_source in {
        "market",
        "non_scalping_market",
        "stop_line_touch_market",
    }


def _is_terminal_after_submit(fields: dict[str, Any]) -> bool:
    stage = str(fields.get("stage") or "")
    return stage.startswith("sell_") or stage in {
        "exit_signal",
        "sell_order_sent",
        "sell_executed",
        "position_completed",
        "post_sell_evaluated",
    }


def _event_observed_price(fields: dict[str, Any]) -> int:
    return _price_from_fields(
        fields,
        (
            "curr_price",
            "canonical_mark_price",
            "passive_buy_price",
            "best_bid",
            "fill_price",
            "assumed_fill_price",
        ),
    )


def _anchor_base_price(anchor: dict[str, Any], events: list[dict[str, Any]]) -> tuple[int, str]:
    price = _price_from_fields(
        anchor,
        (
            "request_price",
            "final_price",
            "resolved_price",
            "order_price",
            "fill_price",
            "assumed_fill_price",
            "curr_price",
            "canonical_mark_price",
            "passive_buy_price",
            "best_bid",
        ),
    )
    if price > 0:
        return price, "anchor_field"
    anchor_time = _event_time(anchor)
    code = _stock_code(anchor)
    reason = _explicit_add_reason(anchor)
    anchor_record_id = _record_id(anchor)
    anchor_order_no = _order_no(anchor)
    if anchor_time is None or not code:
        return 0, "missing_anchor_time_or_code"
    stages = {"scale_in_price_resolved", "scale_in_executed"}
    best_match: tuple[float, int, str] | None = None
    for event in events:
        if _stock_code(event) != code:
            continue
        if str(event.get("stage") or "") not in stages:
            continue
        event_reason = _explicit_add_reason(event)
        event_record_id = _record_id(event)
        event_order_no = _order_no(event)
        identity_match = (
            bool(anchor_record_id and event_record_id and anchor_record_id == event_record_id)
            or bool(anchor_order_no and event_order_no and anchor_order_no == event_order_no)
        )
        if not identity_match and reason and event_reason and event_reason != reason:
            continue
        event_time = _event_time(event)
        if event_time is None:
            continue
        delta = abs((event_time - anchor_time).total_seconds())
        if delta > ANCHOR_RECONSTRUCT_WINDOW_SEC:
            continue
        candidate_price = _price_from_fields(
            event,
            ("resolved_price", "order_price", "request_price", "final_price", "fill_price", "assumed_fill_price"),
        )
        if candidate_price <= 0:
            continue
        if best_match is None or delta < best_match[0]:
            best_match = (delta, candidate_price, str(event.get("stage") or "nearby_event"))
    if best_match is None:
        return 0, "reconstruct_gap"
    return best_match[1], f"reconstructed_from_{best_match[2]}"


def _enrich_avg_down_context(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reason_by_record: dict[tuple[str, str], str] = {}
    reason_by_order: dict[tuple[str, str], str] = {}
    for row in rows:
        stage = str(row.get("stage") or "")
        add_type = str(row.get("add_type") or row.get("scale_in_type") or "").strip().upper()
        if add_type != "AVG_DOWN" and not stage.startswith("scale_in_") and not stage.endswith("_avg_down_submitted"):
            continue
        reason = _explicit_add_reason(row)
        if not reason:
            continue
        code = _stock_code(row)
        record_id = _record_id(row)
        order_no = _order_no(row)
        if code and record_id:
            reason_by_record.setdefault((code, record_id), reason)
        if code and order_no:
            reason_by_order.setdefault((code, order_no), reason)

    enriched: list[dict[str, Any]] = []
    for row in rows:
        if _explicit_add_reason(row):
            enriched.append(row)
            continue
        code = _stock_code(row)
        reason = ""
        record_id = _record_id(row)
        order_no = _order_no(row)
        if code and record_id:
            reason = reason_by_record.get((code, record_id), "")
        if not reason and code and order_no:
            reason = reason_by_order.get((code, order_no), "")
        if reason:
            enriched.append({**row, "add_reason": reason})
        else:
            enriched.append(row)
    return enriched


def _build_post_submit_observations(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_code: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        code = _stock_code(event)
        event_time = _event_time(event)
        if not code or event_time is None:
            continue
        by_code.setdefault(code, []).append(event)
    for rows in by_code.values():
        rows.sort(key=lambda item: _event_time(item) or datetime.min.replace(tzinfo=timezone.utc))
    return by_code


def _counterfactual_for_anchor(
    anchor: dict[str, Any],
    *,
    events: list[dict[str, Any]],
    observations_by_code: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    anchor_time = _event_time(anchor)
    code = _stock_code(anchor)
    base_price, base_price_source = _anchor_base_price(anchor, events)
    order_market_like = _is_market_like_order(anchor, base_price)
    result = {
        "code": code,
        "anchor_time": anchor_time.isoformat() if anchor_time else None,
        "anchor_stage": anchor.get("stage"),
        "base_price": base_price,
        "base_price_source": base_price_source,
        "market_like_order": order_market_like,
        "observed": False,
        "min_observed_price": None,
        "max_observed_price": None,
        "down_ticks_reached": None,
        "touch_0tick": False,
        "touch_1tick": False,
        "touch_2tick": False,
        "missed_upside_proxy": False,
    }
    if anchor_time is None or not code or base_price <= 0 or order_market_like:
        return result
    tick = _tick_size(base_price)
    min_price: int | None = None
    max_price: int | None = None
    end_time = anchor_time + timedelta(seconds=COUNTERFACTUAL_WINDOW_SEC)
    for event in observations_by_code.get(code, []):
        event_time = _event_time(event)
        if event_time is None or event_time < anchor_time:
            continue
        if event_time > end_time:
            break
        if event is not anchor and _is_terminal_after_submit(event):
            price = _event_observed_price(event)
            if price > 0:
                min_price = price if min_price is None else min(min_price, price)
                max_price = price if max_price is None else max(max_price, price)
            break
        price = _event_observed_price(event)
        if price <= 0:
            continue
        min_price = price if min_price is None else min(min_price, price)
        max_price = price if max_price is None else max(max_price, price)
    if min_price is None:
        return result
    down_ticks = max(0, int((base_price - min_price) // tick))
    result.update(
        {
            "observed": True,
            "min_observed_price": min_price,
            "max_observed_price": max_price,
            "down_ticks_reached": down_ticks,
            "touch_0tick": min_price <= base_price,
            "touch_1tick": min_price <= base_price - tick,
            "touch_2tick": min_price <= base_price - (2 * tick),
            "missed_upside_proxy": min_price > base_price - tick and (max_price or 0) >= base_price + tick,
        }
    )
    return result


def _counterfactual_summary(bucket_rows: list[dict[str, Any]], all_events: list[dict[str, Any]]) -> dict[str, Any]:
    raw_anchors = [
        row
        for row in bucket_rows
        if _safe_bool(row.get("actual_order_submitted"))
        and (
            str(row.get("stage") or "").endswith("_submitted")
            or str(row.get("stage") or "") in {"add_order_sent", "scale_in_executed"}
        )
    ]
    submitted_keys = {
        (_stock_code(row), _record_id(row) or _order_no(row))
        for row in raw_anchors
        if str(row.get("stage") or "").endswith("_submitted") or str(row.get("stage") or "") == "add_order_sent"
    }
    submitted_keys.discard(("", ""))
    anchors = [
        row
        for row in raw_anchors
        if str(row.get("stage") or "") != "scale_in_executed"
        or (_stock_code(row), _record_id(row) or _order_no(row)) not in submitted_keys
    ]
    observations_by_code = _build_post_submit_observations(all_events)
    anchor_results = [
        _counterfactual_for_anchor(anchor, events=all_events, observations_by_code=observations_by_code)
        for anchor in anchors
    ]
    observed = [item for item in anchor_results if item.get("observed")]
    market_count = sum(1 for item in anchor_results if item.get("market_like_order"))
    reconstruct_gap_count = sum(1 for item in anchor_results if item.get("base_price_source") == "reconstruct_gap")
    join_gap_count = len(anchor_results) - len(observed) - market_count
    def rate(key: str) -> float | None:
        if not observed:
            return None
        return round(sum(1 for item in observed if item.get(key)) / len(observed), 4)
    min_observed_values = [_safe_int(item.get("min_observed_price"), 0) for item in observed]
    down_ticks_values = [
        _safe_int(item.get("down_ticks_reached"), 0)
        for item in observed
        if item.get("down_ticks_reached") is not None
    ]
    return {
        "counterfactual_anchor_count": len(anchor_results),
        "post_submit_observed_sample": len(observed),
        "market_order_sample_count": market_count,
        "price_observation_join_gap_count": max(0, join_gap_count),
        "base_price_reconstruction_gap_count": reconstruct_gap_count,
        "min_observed_price": min(min_observed_values) if min_observed_values else None,
        "max_down_ticks_reached": max(down_ticks_values) if down_ticks_values else None,
        "avg_down_ticks_reached": round(sum(down_ticks_values) / len(down_ticks_values), 4) if down_ticks_values else None,
        "touch_0tick_rate": rate("touch_0tick"),
        "touch_1tick_rate": rate("touch_1tick"),
        "touch_2tick_rate": rate("touch_2tick"),
        "missed_upside_proxy_rate": rate("missed_upside_proxy"),
        "anchor_samples": anchor_results[:20],
    }


def _selected_policy_from_counterfactual(summary: dict[str, Any]) -> dict[str, Any]:
    observed_sample = _safe_int(summary.get("post_submit_observed_sample"), 0)
    market_sample = _safe_int(summary.get("market_order_sample_count"), 0)
    anchor_count = _safe_int(summary.get("counterfactual_anchor_count"), 0)
    if anchor_count > 0 and market_sample > 0 and observed_sample <= 0:
        return {
            "leg_count": 2,
            "price_offsets_ticks": "market",
            "qty_weights": [0.5, 0.5],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "policy_mode": POLICY_MODE_MARKET_QTY_SPLIT_ONLY,
            "split_variant_id": MARKET_QTY_SPLIT_VARIANT_ID,
            "selection_reason": "market_or_best_limit_order_price_split_not_applicable",
            "runtime_apply_allowed": True,
        }
    if observed_sample <= 0:
        return {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "qty_weights": [0.5, 0.5],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "policy_mode": POLICY_MODE_BOUNDED_EQUAL_BASELINE,
            "split_variant_id": BASELINE_SPLIT_VARIANT_ID,
            "selection_reason": "counterfactual_sample_or_price_observation_missing",
            "runtime_apply_allowed": True,
        }
    touch1 = _safe_float(summary.get("touch_1tick_rate"), 0.0) or 0.0
    touch2 = _safe_float(summary.get("touch_2tick_rate"), 0.0) or 0.0
    missed = _safe_float(summary.get("missed_upside_proxy_rate"), 0.0) or 0.0
    if touch1 >= 0.70 and touch2 >= 0.40 and missed < 0.40:
        return {
            "leg_count": 2,
            "price_offsets_ticks": [0, 2],
            "qty_weights": [0.6, 0.4],
            "qty_weight_min": 0.6,
            "qty_weight_max": 0.4,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_60_40_VARIANT_ID,
            "selection_reason": "touch_1tick_and_2tick_high_with_low_missed_upside",
            "runtime_apply_allowed": True,
        }
    if touch1 < 0.30 or missed >= 0.40:
        return {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "qty_weights": [0.7, 0.3],
            "qty_weight_min": 0.7,
            "qty_weight_max": 0.3,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_70_30_VARIANT_ID,
            "selection_reason": "touch_1tick_low_or_missed_upside_high",
            "runtime_apply_allowed": True,
        }
    return {
        "leg_count": 2,
        "price_offsets_ticks": [0, 1],
        "qty_weights": [0.5, 0.5],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
        "split_variant_id": COUNTERFACTUAL_50_50_VARIANT_ID,
        "selection_reason": "touch_1tick_mid_range",
        "runtime_apply_allowed": True,
    }


def _diagnostic_three_leg_candidate(bucket: str, summary: dict[str, Any]) -> dict[str, Any] | None:
    observed_sample = _safe_int(summary.get("post_submit_observed_sample"), 0)
    touch1 = _safe_float(summary.get("touch_1tick_rate"), 0.0) or 0.0
    touch2 = _safe_float(summary.get("touch_2tick_rate"), 0.0) or 0.0
    if observed_sample <= 0 or touch1 < 0.70 or touch2 < 0.40:
        return None
    return {
        **{key: value for key, value in summary.items() if key != "anchor_samples"},
        "context_bucket": bucket,
        "leg_count": 3,
        "price_offsets_ticks": [0, 1, 2],
        "qty_weights": [0.5, 0.25, 0.25],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.25,
        "policy_mode": POLICY_MODE_DIAGNOSTIC_THREE_LEG,
        "split_variant_id": DIAGNOSTIC_THREE_LEG_VARIANT_ID,
        "selection_reason": "diagnostic_only_touch_1tick_and_2tick_high",
        "runtime_apply_allowed": False,
        "diagnostic_only": True,
    }


def _candidate_for_bucket(bucket: str, rows: list[dict[str, Any]], all_events: list[dict[str, Any]]) -> dict[str, Any]:
    real_rows = [row for row in rows if _safe_bool(row.get("actual_order_submitted"))]
    sim_rows = [row for row in rows if not _safe_bool(row.get("actual_order_submitted"))]
    counterfactual = _counterfactual_summary(rows, all_events)
    selected = _selected_policy_from_counterfactual(counterfactual)
    return {
        "context_bucket": bucket,
        "leg_count": selected["leg_count"],
        "price_offsets_ticks": selected["price_offsets_ticks"],
        "qty_weights": selected.get("qty_weights"),
        "qty_weight_min": selected["qty_weight_min"],
        "qty_weight_max": selected["qty_weight_max"],
        "fill_quality": None,
        "missed_upside": None,
        "source_quality_adjusted_ev_pct": None,
        "notional_weighted_ev_pct": None,
        "diagnostic_sim_ev_pct": None,
        "partial_fill_rate": None,
        "cancel_rate": None,
        "late_fill_rate": None,
        "downside_p10_profit_rate": None,
        "real_sample_count": len(real_rows),
        "sim_sample_count": len(sim_rows),
        "real_outcome_joined_sample": 0,
        "primary_sample_book": "post_submit_tick_band_counterfactual",
        "policy_mode": selected["policy_mode"],
        "split_variant_id": selected["split_variant_id"],
        "runtime_apply_allowed": bool(selected["runtime_apply_allowed"]),
        "policy_generation_reason": "post_submit_tick_band_counterfactual_selector",
        "selection_reason": selected["selection_reason"],
        "counterfactual_sample_count": counterfactual.get("post_submit_observed_sample"),
        "post_submit_touch_rates": {
            "touch_0tick_rate": counterfactual.get("touch_0tick_rate"),
            "touch_1tick_rate": counterfactual.get("touch_1tick_rate"),
            "touch_2tick_rate": counterfactual.get("touch_2tick_rate"),
            "missed_upside_proxy_rate": counterfactual.get("missed_upside_proxy_rate"),
        },
        **counterfactual,
    }


def _build_policy(target_date: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    policy_version = f"{RUNTIME_FAMILY}:{target_date}:{_policy_hash(candidates)}"
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_version": policy_version,
        "source_report": str(report_paths(target_date)[0]),
        "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "runtime_apply_allowed": True,
        "scope": {
            "stage": "scale_in",
            "add_type": "AVG_DOWN",
            "excluded_add_types": ["PYRAMID"],
            "quantity_authority": "describe_dynamic_scale_in_qty",
            "forbidden_uses": "quantity_expansion|cap_release|broker_guard_bypass|stale_quote_bypass|provider_route_change|bot_restart",
        },
        "default_bucket": {
            "context_bucket": "default",
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "qty_weights": [0.5, 0.5],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "policy_mode": POLICY_MODE_BOUNDED_EQUAL_BASELINE,
            "split_variant_id": BASELINE_SPLIT_VARIANT_ID,
            "selection_reason": "default_qty_preserving_baseline",
            "runtime_apply_allowed": True,
        },
        "buckets": {str(item["context_bucket"]): item for item in candidates},
    }


def _policy_hash(candidates: list[dict[str, Any]]) -> str:
    raw = json.dumps(candidates, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def build_report(target_date: str) -> dict[str, Any]:
    source_quality = _source_quality_summary(target_date)
    events, input_summary = _iter_input_events(target_date)
    avg_down_rows: list[dict[str, Any]] = []
    skipped = Counter()
    enriched_events = _enrich_avg_down_context(events)
    for event in enriched_events:
        stage = str(event.get("stage") or "")
        add_type = str(event.get("add_type") or event.get("scale_in_type") or "").strip().upper()
        if add_type != "AVG_DOWN":
            continue
        if stage not in {
            "scale_in_price_resolved",
            "add_order_sent",
            "scale_in_executed",
            "scalp_sim_scale_in_order_assumed_filled",
            "scalp_sim_scale_in_order_unfilled",
            "swing_sim_scale_in_order_assumed_filled",
            "swing_probe_scale_in_order_assumed_filled",
        } and not stage.endswith("_submitted"):
            skipped[stage or "unknown_stage"] += 1
            continue
        avg_down_rows.append(event)
    by_bucket: dict[str, list[dict[str, Any]]] = {}
    for row in avg_down_rows:
        by_bucket.setdefault(_context_bucket(row), []).append(row)
    candidate_grid: list[dict[str, Any]] = []
    diagnostic_candidates: list[dict[str, Any]] = []
    for bucket, rows in sorted(by_bucket.items()):
        candidate = _candidate_for_bucket(bucket, rows, events)
        candidate_grid.append(candidate)
        diagnostic = _diagnostic_three_leg_candidate(
            bucket,
            {key: value for key, value in candidate.items() if key != "anchor_samples"},
        )
        if diagnostic:
            diagnostic_candidates.append(diagnostic)
            candidate_grid.append(diagnostic)
    if not candidate_grid:
        candidate_grid = [_candidate_for_bucket("default", [], events)]
    candidates = [
        item
        for item in candidate_grid
        if source_quality.get("tuning_input_allowed") is not False
        and _safe_bool(item.get("runtime_apply_allowed"))
    ]
    policy = _build_policy(target_date, candidates)
    policy_file = policy_path(target_date)
    counterfactual_selected_count = sum(
        1
        for item in candidates
        if isinstance(item, dict) and item.get("policy_mode") == POLICY_MODE_COUNTERFACTUAL_TICK_BAND
    )
    baseline_fallback_count = sum(
        1
        for item in candidates
        if isinstance(item, dict) and item.get("policy_mode") == POLICY_MODE_BOUNDED_EQUAL_BASELINE
    )
    market_qty_split_only_count = sum(
        1
        for item in candidates
        if isinstance(item, dict) and item.get("policy_mode") == POLICY_MODE_MARKET_QTY_SPLIT_ONLY
    )
    price_observation_join_gap_count = sum(
        _safe_int(item.get("price_observation_join_gap_count"), 0)
        for item in candidate_grid
        if isinstance(item, dict) and not _safe_bool(item.get("diagnostic_only"))
    )
    base_price_reconstruction_gap_count = sum(
        _safe_int(item.get("base_price_reconstruction_gap_count"), 0)
        for item in candidate_grid
        if isinstance(item, dict) and not _safe_bool(item.get("diagnostic_only"))
    )
    input_summary.update(
        {
            "avg_down_observation_count": len(avg_down_rows),
            "bucket_count": len(by_bucket),
            "skipped_stage_counts": dict(skipped),
            "excluded_source_quality_event_count": 0,
            "counterfactual_selected_count": counterfactual_selected_count,
            "baseline_fallback_count": baseline_fallback_count,
            "price_observation_join_gap_count": price_observation_join_gap_count,
            "base_price_reconstruction_gap_count": base_price_reconstruction_gap_count,
            "market_qty_split_only_count": market_qty_split_only_count,
            "diagnostic_three_leg_candidate_count": len(diagnostic_candidates),
            "counterfactual_window_sec": COUNTERFACTUAL_WINDOW_SEC,
            "anchor_reconstruct_window_sec": ANCHOR_RECONSTRUCT_WINDOW_SEC,
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "metric_contract": {
            "metric_role": "execution_shape_seed",
            "decision_authority": "next_preopen_bounded_scale_in_split_policy",
            "window_policy": "operator_requested_seed_with_daily_diagnostic",
            "sample_floor": {"real": 0, "sim": 0},
            "primary_decision_metric": "post_submit_tick_band_counterfactual_selector",
            "source_quality_gate": "observation_source_quality_audit_tuning_input_allowed",
            "forbidden_uses": [
                "quantity_expansion",
                "cap_release",
                "broker_guard_bypass",
                "stale_quote_bypass",
                "provider_route_change",
                "bot_restart",
                "pyramid_scale_in",
            ],
        },
        "source_quality": source_quality,
        "input_summary": input_summary,
        "candidate_grid": candidate_grid,
        "recommended_policy": {
            "runtime_apply_allowed": bool(candidates),
            "policy_file": str(policy_file),
            "policy_version": policy.get("policy_version"),
            "candidates": candidates,
            "diagnostic_candidates": diagnostic_candidates,
        },
        "policy_artifact": policy,
    }


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    recommended = report.get("recommended_policy") if isinstance(report.get("recommended_policy"), dict) else {}
    lines = [
        f"# Scale-In Split Order Plan {report.get('target_date')}",
        "",
        f"- schema_version: `{report.get('schema_version')}`",
        f"- source_quality: `{(report.get('source_quality') or {}).get('status')}`",
        f"- runtime_apply_allowed: `{recommended.get('runtime_apply_allowed')}`",
        f"- policy_version: `{recommended.get('policy_version')}`",
        f"- policy_file: `{recommended.get('policy_file')}`",
        f"- candidate_count: `{len(recommended.get('candidates') or [])}`",
        f"- counterfactual_selected_count: `{(report.get('input_summary') or {}).get('counterfactual_selected_count')}`",
        f"- baseline_fallback_count: `{(report.get('input_summary') or {}).get('baseline_fallback_count')}`",
        f"- price_observation_join_gap_count: `{(report.get('input_summary') or {}).get('price_observation_join_gap_count')}`",
        f"- market_qty_split_only_count: `{(report.get('input_summary') or {}).get('market_qty_split_only_count')}`",
        "",
        "## Candidate Grid",
    ]
    for item in report.get("candidate_grid") or []:
        lines.append(
            "- bucket=`{}` mode=`{}` real=`{}` sim=`{}` offsets=`{}`".format(
                item.get("context_bucket"),
                item.get("policy_mode"),
                item.get("real_sample_count"),
                item.get("sim_sample_count"),
                item.get("price_offsets_ticks"),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(target_date: str, report: dict[str, Any]) -> tuple[Path, Path, Path]:
    json_path, md_path = report_paths(target_date)
    policy_file = policy_path(target_date)
    policy = report.get("policy_artifact") if isinstance(report.get("policy_artifact"), dict) else {}
    report_to_write = {key: value for key, value in report.items() if key != "policy_artifact"}
    _write_json(json_path, report_to_write)
    _write_json(policy_file, policy)
    _write_markdown(md_path, report_to_write)
    return json_path, md_path, policy_file


def _load_policy_from_env(policy_file: str | None = None) -> tuple[dict[str, Any] | None, str]:
    enabled = os.environ.get("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED")
    if not _safe_bool(enabled):
        return None, "policy_disabled"
    path_value = policy_file or os.environ.get("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE")
    if not path_value:
        return None, "policy_file_missing"
    path = Path(path_value)
    if not path.exists():
        return None, "policy_file_not_found"
    payload = _load_json(path)
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        return None, "policy_schema_mismatch"
    if not _safe_bool(payload.get("runtime_apply_allowed")):
        return None, "runtime_apply_not_allowed"
    return payload, "loaded"


def _policy_is_stale(policy: dict[str, Any], *, now: datetime | None = None) -> bool:
    raw = str(policy.get("generated_at") or "")
    if not raw:
        return True
    try:
        generated_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return True
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone(timedelta(hours=9)))
    now = now or datetime.now(timezone(timedelta(hours=9)))
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone(timedelta(hours=9)))
    return now - generated_at.astimezone(now.tzinfo) > timedelta(days=3)


def _runtime_default_bucket_policy(bucket: str) -> dict[str, Any]:
    return {
        "context_bucket": bucket,
        "leg_count": 2,
        "price_offsets_ticks": [0, 1],
        "qty_weights": [0.5, 0.5],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "policy_mode": RUNTIME_FALLBACK_POLICY_MODE,
        "split_variant_id": RUNTIME_FALLBACK_VARIANT_ID,
    }


def _split_qty(total_qty: int, leg_count: int, first_weight: float) -> list[int]:
    if leg_count <= 1 or total_qty <= 1:
        return [total_qty]
    first_qty = max(1, min(total_qty - (leg_count - 1), int(round(total_qty * first_weight))))
    quantities = [first_qty]
    remaining = total_qty - first_qty
    for remaining_legs in range(leg_count - 1, 0, -1):
        qty = max(1, remaining // remaining_legs)
        quantities.append(qty)
        remaining -= qty
    if remaining:
        quantities[-1] += remaining
    return quantities


def _split_qty_by_weights(total_qty: int, leg_count: int, weights: list[float]) -> list[int]:
    if leg_count <= 1 or total_qty <= 1:
        return [total_qty]
    if total_qty < leg_count:
        return _split_qty(total_qty, leg_count, weights[0] if weights else 0.5)
    normalized = [max(0.0, float(weight or 0.0)) for weight in weights[:leg_count]]
    while len(normalized) < leg_count:
        normalized.append(0.0)
    weight_sum = sum(normalized)
    if weight_sum <= 0:
        return _split_qty(total_qty, leg_count, 0.5)
    normalized = [weight / weight_sum for weight in normalized]
    if leg_count == 2:
        first_qty = max(1, min(total_qty - 1, int(round(total_qty * normalized[0]))))
        return [first_qty, total_qty - first_qty]
    quantities = [1] * leg_count
    remaining = total_qty - leg_count
    raw_allocations = [remaining * weight for weight in normalized]
    floors = [int(value) for value in raw_allocations]
    for idx, value in enumerate(floors):
        quantities[idx] += value
    leftover = remaining - sum(floors)
    remainders = sorted(
        ((raw_allocations[idx] - floors[idx], idx) for idx in range(leg_count)),
        key=lambda item: (-item[0], item[1]),
    )
    for _remainder, idx in remainders[:leftover]:
        quantities[idx] += 1
    return quantities


def _tick_size(price: int) -> int:
    try:
        return max(1, int(get_tick_size(price) or 1))
    except Exception:
        return 1


def apply_scale_in_split_order_policy(
    order: dict[str, Any] | None,
    *,
    stock: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    price_resolution: dict[str, Any] | None = None,
    quote_fields: dict[str, Any] | None = None,
    policy_file: str | None = None,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_order = dict(order or {})
    stock = stock if isinstance(stock, dict) else {}
    action = action if isinstance(action, dict) else {}
    price_resolution = price_resolution if isinstance(price_resolution, dict) else {}
    quote_fields = quote_fields if isinstance(quote_fields, dict) else {}
    qty = _safe_int(base_order.get("qty"), 0)
    add_type = str(action.get("add_type") or base_order.get("add_type") or "").strip().upper()
    fields: dict[str, Any] = {
        "scale_in_split_order_policy_applied": False,
        "scale_in_split_order_original_qty": qty,
        "scale_in_split_order_original_order_count": 1 if base_order else 0,
    }
    if add_type != "AVG_DOWN":
        fields["scale_in_split_order_skip_reason"] = "not_avg_down"
        return [base_order] if base_order else [], fields
    if qty <= 1:
        fields["scale_in_split_order_skip_reason"] = "qty_lte_1"
        return [base_order], fields
    if _safe_bool(quote_fields.get("stale_quote_submit_block")) or _safe_bool(quote_fields.get("quote_stale_at_submit")):
        fields["scale_in_split_order_skip_reason"] = "stale_quote"
        return [base_order], fields
    policy, load_status = _load_policy_from_env(policy_file)
    if not policy:
        fields["scale_in_split_order_skip_reason"] = load_status
        return [base_order], fields
    if _policy_is_stale(policy, now=now):
        fields["scale_in_split_order_skip_reason"] = "stale_policy"
        return [base_order], fields
    base_price = _safe_int(
        base_order.get("price")
        or price_resolution.get("order_price")
        or price_resolution.get("best_bid")
        or quote_fields.get("passive_buy_price")
        or stock.get("curr_price"),
        0,
    )
    base_order_price = _safe_int(base_order.get("price"), 0)
    order_type_code = str(base_order.get("order_type_code") or "")
    market_order = base_order_price <= 0 and order_type_code in {"3", "03", "6", "06", "16"}
    if base_price <= 0 and not market_order:
        fields["scale_in_split_order_skip_reason"] = "invalid_base_price"
        return [base_order], fields
    bucket = _context_bucket({**stock, **action, **price_resolution})
    bucket_policy = (policy.get("buckets") or {}).get(bucket)
    fallback_policy_applied = False
    if not isinstance(bucket_policy, dict):
        bucket_policy = policy.get("default_bucket") if isinstance(policy.get("default_bucket"), dict) else None
    if not isinstance(bucket_policy, dict):
        bucket_policy = _runtime_default_bucket_policy(bucket)
        fallback_policy_applied = True
    desired_legs = min(max(1, _safe_int(bucket_policy.get("leg_count"), 2)), 2, qty)
    if desired_legs <= 1:
        fields["scale_in_split_order_skip_reason"] = "single_leg_policy"
        fields["scale_in_split_order_bucket"] = bucket
        return [base_order], fields
    raw_offsets = bucket_policy.get("price_offsets_ticks")
    if isinstance(raw_offsets, list):
        offsets = [_safe_int(item, 0) for item in raw_offsets][:desired_legs]
    else:
        offsets = [0, 1][:desired_legs]
    while len(offsets) < desired_legs:
        offsets.append(len(offsets))
    raw_weights = bucket_policy.get("qty_weights")
    qty_weights = [
        _safe_float(item, 0.0) or 0.0
        for item in raw_weights
    ] if isinstance(raw_weights, list) else []
    first_weight = _safe_float(bucket_policy.get("qty_weight_min"), 0.5) or 0.5
    quantities = (
        _split_qty_by_weights(qty, desired_legs, qty_weights)
        if qty_weights
        else _split_qty(qty, desired_legs, first_weight)
    )
    tick = _tick_size(base_price) if base_price > 0 else 1
    split_orders = []
    for idx, leg_qty in enumerate(quantities):
        price = 0 if market_order else clamp_price_to_tick(max(1, base_price - (tick * offsets[idx])))
        split_orders.append(
            {
                **base_order,
                "qty": leg_qty,
                "price": price,
                "scale_in_split_order_leg_index": idx + 1,
                "scale_in_split_order_policy_version": policy.get("policy_version"),
                "scale_in_split_order_policy_mode": bucket_policy.get("policy_mode"),
                "scale_in_split_order_variant_id": bucket_policy.get("split_variant_id"),
                "scale_in_split_order_bucket": bucket,
                "scale_in_split_order_runtime_default_policy_applied": fallback_policy_applied,
                "scale_in_split_order_market_order_applied": market_order,
                "scale_in_split_order_price_offsets_ticks": (
                    "market" if market_order else ",".join(str(item) for item in offsets)
                ),
                "scale_in_split_order_qty_weight_min": first_weight,
                "scale_in_split_order_qty_weight_max": _safe_float(bucket_policy.get("qty_weight_max"), first_weight),
                "scale_in_split_order_qty_weights": ",".join(str(item) for item in qty_weights) if qty_weights else "",
            }
        )
    if sum(_safe_int(item.get("qty"), 0) for item in split_orders) != qty:
        fields["scale_in_split_order_skip_reason"] = "quantity_conservation_failed"
        return [base_order], fields
    fields.update(
        {
            "scale_in_split_order_policy_applied": True,
            "scale_in_split_order_skip_reason": "",
            "scale_in_split_order_bucket": bucket,
            "scale_in_split_order_policy_version": policy.get("policy_version"),
            "scale_in_split_order_policy_mode": bucket_policy.get("policy_mode"),
            "scale_in_split_order_variant_id": bucket_policy.get("split_variant_id"),
            "scale_in_split_order_runtime_default_policy_applied": fallback_policy_applied,
            "scale_in_split_order_policy_file": policy_file
            or os.environ.get("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE"),
            "scale_in_split_order_leg_count": len(split_orders),
            "scale_in_split_order_split_qty": qty,
            "scale_in_split_order_market_order_applied": market_order,
            "scale_in_split_order_price_offsets_ticks": (
                "market" if market_order else ",".join(str(item) for item in offsets)
            ),
            "scale_in_split_order_qty_weight_min": first_weight,
            "scale_in_split_order_qty_weight_max": _safe_float(bucket_policy.get("qty_weight_max"), first_weight),
            "scale_in_split_order_qty_weights": ",".join(str(item) for item in qty_weights) if qty_weights else "",
        }
    )
    return split_orders, fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", "--target-date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date)
    if not args.no_write:
        write_outputs(args.target_date, report)
    else:
        print(json.dumps({key: value for key, value in report.items() if key != "policy_artifact"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
