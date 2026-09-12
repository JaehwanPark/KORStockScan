"""Scale-in split order plan report and bounded runtime allocator."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    is_date_allowed,
)
from src.engine.trade_profit import calculate_net_realized_pnl
from src.trading.order.split_execution_math import (
    pct_price_offset as _pct_price_offset,
    scale_in_leg_ttl_seconds,
    split_qty as _split_qty,
    split_qty_by_weights as _split_qty_by_weights,
    tick_size as _tick_size,
)
from src.trading.order.tick_utils import clamp_price_to_tick
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl
from src.utils.market_day import count_krx_trading_days

SCHEMA_VERSION = "scale_in_split_order_plan_v3"
POLICY_SCHEMA_VERSION = "scale_in_split_order_policy_v3"
ECONOMIC_GATE_VERSION = "ttl_paired_fixed_control_v3"
REPORT_TYPE = "scale_in_split_order_plan"
RUNTIME_FAMILY = "scale_in_split_order_plan"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
POLICY_DIR = DATA_DIR / "threshold_cycle" / "scale_in_split_order_policy"
POLICY_MODE_BOUNDED_EQUAL_BASELINE = "bounded_equal_scale_in_split_baseline"
POLICY_MODE_COUNTERFACTUAL_TICK_BAND = "counterfactual_tick_band_selector"
POLICY_MODE_MARKET_QTY_SPLIT_ONLY = "market_qty_split_only"
POLICY_MODE_DIAGNOSTIC_THREE_LEG = "diagnostic_three_leg_tick_band"
BASELINE_SPLIT_VARIANT_ID = "scale_in_equal_50_50_offset_0pct_0_3pct"
COUNTERFACTUAL_70_30_VARIANT_ID = "scale_in_counterfactual_70_30_offset_0pct_0_3pct"
COUNTERFACTUAL_50_50_VARIANT_ID = "scale_in_counterfactual_50_50_offset_0pct_0_3pct"
COUNTERFACTUAL_60_40_VARIANT_ID = "scale_in_counterfactual_60_40_offset_0pct_0_8pct"
MARKET_QTY_SPLIT_VARIANT_ID = "scale_in_market_qty_split_50_50"
DIAGNOSTIC_THREE_LEG_VARIANT_ID = (
    "scale_in_diagnostic_50_25_25_offset_0pct_0_3pct_0_8pct"
)
COUNTERFACTUAL_WINDOW_SEC = 180
ANCHOR_RECONSTRUCT_WINDOW_SEC = 5
RUNTIME_REFRESH_REAL_OUTCOME_FLOOR = 3
RUNTIME_REFRESH_MFE_MAE_FLOOR = 3
RUNTIME_REFRESH_SOURCE_DATE_FLOOR = 2
RUNTIME_REFRESH_PRICE_JOIN_COVERAGE_FLOOR = 0.80
RUNTIME_REFRESH_MIN_COST_ADJUSTED_EV_PCT = 0.1
RUNTIME_REFRESH_FILL_PARTICIPATION_FLOOR = 0.70
RUNTIME_REFRESH_DOWNSIDE_P10_DELTA_FLOOR_PCT = -0.30
ROLLING_REPORT_DATE_LIMIT = 20
MAX_SCALE_IN_SPLIT_LEGS = 3
MAX_POLICY_AGE_KRX_TRADING_DAYS = 3
_INPUT_PROJECTION_KEYS = (
    "stage",
    "strategy",
    "raw_strategy",
    "add_type",
    "scale_in_type",
    "add_reason",
    "scale_in_trigger",
    "add_trigger",
    "reason",
    "stock_code",
    "code",
    "record_id",
    "recommendation_id",
    "id",
    "ord_no",
    "order_no",
    "odno",
    "broker_order_no",
    "broker_order_no_list",
    "broker_order_qty_list",
    "partial_submit_failure",
    "remaining_qty",
    "broker_route",
    "effective_venue",
    "quote_stale_at_submit",
    "quote_stale",
    "sim_record_id",
    "execution_no",
    "qty",
    "requested_qty",
    "effective_qty",
    "submitted_qty",
    "submitted_leg_count",
    "bundle_requested_qty",
    "bundle_filled_qty",
    "order_requested_qty",
    "order_filled_qty",
    "fill_qty",
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
    "order_type_code",
    "order_type",
    "price_source",
    "price_policy",
    "actual_order_submitted",
    "broker_order_forbidden",
    "receipt_economics_complete",
    "receipt_quantity_contract_complete",
    "receipt_unit_fill_consistent",
    "broker_execution_provenance_complete",
    "sell_price",
    "last_sell_fill_price",
    "position_weighted_sell_price",
    "sell_qty",
    "profit_rate",
    "sell_execution_receipt_economics_complete",
    "sell_execution_receipt_quantity_contract_complete",
    "sell_execution_receipt_unit_fill_consistent",
    "scale_in_split_order_policy_version",
    "scale_in_split_order_variant_id",
    "scale_in_split_order_policy_applied",
    "scale_in_split_order_original_qty",
    "rising_missed_scout",
    "emitted_at",
    "timestamp",
    "created_at",
    "event_time",
)

_AVG_DOWN_ATTEMPT_STAGE_TOKENS = (
    "scale_in_order_submitted",
    "stop_line_touch_mandatory_avg_down_submitted",
    "late_loss_avg_down_retry_submitted",
    "add_order_sent",
    "scale_in_executed",
)


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
    return (
        DATA_DIR
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError, OverflowError):
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
    ts = str(
        event.get("timestamp")
        or event.get("created_at")
        or event.get("emitted_at")
        or ""
    ).strip()
    return ts[:10] if len(ts) >= 10 else ""


def _source_quality_summary(target_date: str) -> dict[str, Any]:
    path = _source_quality_path(target_date)
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(
        payload.get("status") or ("missing" if not path.exists() else "loaded")
    )
    hard_gap_count = _safe_int(summary.get("hard_blocking_contract_gap_count"), 0)
    raw_row_exclusion_applied = bool(
        summary.get("raw_row_exclusion_applied") or payload.get("raw_row_exclusion")
    )
    tuning_input_allowed = summary.get("tuning_input_allowed")
    if tuning_input_allowed is None:
        tuning_input_allowed = status not in {"fail", "missing", "invalid"} and (
            hard_gap_count <= 0 or raw_row_exclusion_applied
        )
    if status in {"fail", "missing", "invalid"} or (
        hard_gap_count > 0 and not raw_row_exclusion_applied
    ):
        tuning_input_allowed = False
    return {
        "artifact": str(path) if path.exists() else None,
        "status": status,
        "tuning_input_allowed": bool(tuning_input_allowed),
        "hard_blocking_contract_gap_count": hard_gap_count,
        "hard_blocking_excluded_row_count": _safe_int(
            summary.get("hard_blocking_excluded_row_count"), 0
        ),
        "raw_row_exclusion_applied": raw_row_exclusion_applied,
    }


def _contains_rising_missed(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "rising_missed_scout" in value:
        return _safe_bool(value.get("rising_missed_scout"))
    return any(
        "rising_missed" in str(value.get(key) or "").lower()
        for key in ("entry_source", "source", "position_tag", "entry_trigger")
    )


def _project_relevant_input_event(
    event: dict[str, Any], *, source_name: str, event_date: str
) -> dict[str, Any] | None:
    fields = _event_fields(event)
    projected = {key: fields[key] for key in _INPUT_PROJECTION_KEYS if key in fields}
    stage = str(projected.get("stage") or "")
    add_type = str(
        projected.get("add_type") or projected.get("scale_in_type") or ""
    ).upper()
    scale_related = (
        add_type == "AVG_DOWN"
        or stage.startswith("scale_in_")
        or stage.endswith("_avg_down_submitted")
    )
    observation_related = bool(
        _stock_code(projected)
        and _event_time(projected) is not None
        and (
            _event_observed_price(projected) > 0 or _is_terminal_after_submit(projected)
        )
    )
    if not scale_related and not observation_related:
        return None
    if scale_related and _contains_rising_missed(fields):
        projected["rising_missed_scout"] = True
    projected["source_name"] = source_name
    projected["source_date"] = event_date
    return projected


def _source_has_avg_down_attempt(path: Path) -> bool:
    """Cheaply reject no-yield days before JSON decoding the full event stream."""

    source_path = existing_or_gzip_path(path)
    if not source_path.exists():
        return False
    opener = gzip.open if source_path.suffix == ".gz" else open
    stage_tokens = tuple(
        token.encode("ascii") for token in _AVG_DOWN_ATTEMPT_STAGE_TOKENS
    )
    try:
        with opener(source_path, "rb") as handle:
            for line in handle:
                if b"AVG_DOWN" not in line:
                    continue
                if any(token in line for token in stage_tokens):
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        return True
                    if not isinstance(payload, dict):
                        continue
                    fields = _event_fields(payload)
                    stage = str(fields.get("stage") or "")
                    add_type = (
                        str(fields.get("add_type") or fields.get("scale_in_type") or "")
                        .strip()
                        .upper()
                    )
                    if (
                        add_type == "AVG_DOWN"
                        and _safe_bool(fields.get("actual_order_submitted"))
                        and (
                            stage.endswith("_submitted")
                            or stage == "add_order_sent"
                            or stage == "scale_in_executed"
                        )
                    ):
                        return True
    except OSError:
        # The canonical JSONL reader owns malformed/compressed-source handling.
        # Falling through to it preserves fail-closed visibility.
        return True
    return False


def _iter_input_events(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    clean_policy = clean_baseline_policy()
    events: list[dict[str, Any]] = []
    excluded_pre_baseline = 0
    excluded_other_date = 0
    source_event_count = 0
    source_paths = {
        "pipeline_events": _pipeline_events_path(target_date),
        "threshold_events": _threshold_events_path(target_date),
    }
    attempt_source_present = any(
        _source_has_avg_down_attempt(path) for path in source_paths.values()
    )
    if not attempt_source_present:
        return [], {
            "source_paths": {
                name: (
                    str(existing_or_gzip_path(path))
                    if existing_or_gzip_path(path).exists()
                    else None
                )
                for name, path in source_paths.items()
            },
            "source_read_contract": {
                "read_mode": "avg_down_attempt_presence_precheck",
                "full_source_materialized": False,
                "json_parse_skipped": True,
                "source_event_count": None,
                "retained_event_count": 0,
                "retained_scope": "no_real_avg_down_attempt_anchor",
            },
            "excluded_pre_baseline_count": 0,
            "clean_tuning_baseline": clean_policy,
        }
    for source_name, path in source_paths.items():
        for event in iter_jsonl(path):
            source_event_count += 1
            fields = _event_fields(event)
            event_date = _event_date(fields) or target_date
            if not is_date_allowed(event_date, clean_policy):
                excluded_pre_baseline += 1
                continue
            if event_date != target_date:
                excluded_other_date += 1
                continue
            projected = _project_relevant_input_event(
                event, source_name=source_name, event_date=event_date
            )
            if projected is not None:
                events.append(projected)
    return events, {
        "source_paths": {
            name: (
                str(existing_or_gzip_path(path))
                if existing_or_gzip_path(path).exists()
                else None
            )
            for name, path in source_paths.items()
        },
        "source_read_contract": {
            "read_mode": "streaming_relevant_field_projection",
            "full_source_materialized": False,
            "source_event_count": source_event_count,
            "retained_event_count": len(events),
            "retained_scope": "avg_down_identity_anchor_price_and_terminal_events",
        },
        "excluded_pre_baseline_count": excluded_pre_baseline,
        "excluded_other_date_count": excluded_other_date,
        "clean_tuning_baseline": clean_policy,
    }


def _context_bucket(fields: dict[str, Any]) -> str:
    fields = _event_fields(fields)
    strategy = (
        str(fields.get("strategy") or fields.get("raw_strategy") or "").strip().upper()
    )
    strategy_bucket = (
        "scalping"
        if strategy in {"SCALPING", "SCALP"}
        else "swing" if strategy else "unknown_strategy"
    )
    stage = str(fields.get("stage") or "").strip()
    add_reason = str(
        fields.get("add_reason")
        or fields.get("scale_in_trigger")
        or fields.get("add_trigger")
        or fields.get("reason")
        or stage
        or ""
    ).strip()
    if add_reason in {"stop_line_touch_mandatory_avg_down", "deep_recovery_avg_down"}:
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
    lineage = "rising_missed" if _contains_rising_missed(fields) else "normal"
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
    return str(
        fields.get("record_id")
        or fields.get("recommendation_id")
        or fields.get("id")
        or ""
    ).strip()


def _order_no(fields: dict[str, Any]) -> str:
    return str(
        fields.get("ord_no") or fields.get("order_no") or fields.get("odno") or ""
    ).strip()


def _price_from_fields(fields: dict[str, Any], keys: tuple[str, ...]) -> int:
    for key in keys:
        price = _safe_int(fields.get(key), 0)
        if price > 0:
            return price
    return 0


def _is_market_like_order(fields: dict[str, Any], base_price: int) -> bool:
    order_type = str(
        fields.get("order_type_code") or fields.get("order_type") or ""
    ).strip()
    price_source = str(
        fields.get("price_source") or fields.get("price_policy") or ""
    ).strip()
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


def _anchor_base_price(
    anchor: dict[str, Any], events: list[dict[str, Any]]
) -> tuple[int, str]:
    price = _price_from_fields(
        anchor,
        (
            "final_price",
            "request_price",
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
        identity_match = bool(
            anchor_record_id and event_record_id and anchor_record_id == event_record_id
        ) or bool(
            anchor_order_no and event_order_no and anchor_order_no == event_order_no
        )
        if (anchor_record_id or anchor_order_no) and not identity_match:
            continue
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
            (
                "resolved_price",
                "order_price",
                "request_price",
                "final_price",
                "fill_price",
                "assumed_fill_price",
            ),
        )
        if candidate_price <= 0:
            continue
        if best_match is None or delta < best_match[0]:
            best_match = (
                delta,
                candidate_price,
                str(event.get("stage") or "nearby_event"),
            )
    if best_match is None:
        return 0, "reconstruct_gap"
    return best_match[1], f"reconstructed_from_{best_match[2]}"


def _enrich_avg_down_context(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reason_by_record: dict[tuple[str, str], str] = {}
    reason_by_order: dict[tuple[str, str], str] = {}
    strategy_by_record: dict[tuple[str, str], str] = {}
    strategy_by_order: dict[tuple[str, str], str] = {}
    for row in rows:
        stage = str(row.get("stage") or "")
        add_type = (
            str(row.get("add_type") or row.get("scale_in_type") or "").strip().upper()
        )
        if (
            add_type != "AVG_DOWN"
            and not stage.startswith("scale_in_")
            and not stage.endswith("_avg_down_submitted")
        ):
            continue
        reason = _explicit_add_reason(row)
        if not reason:
            continue
        code = _stock_code(row)
        record_id = _record_id(row)
        order_no = _order_no(row)
        if code and record_id:
            reason_by_record.setdefault((code, record_id), reason)
            if row.get("strategy") or row.get("raw_strategy"):
                strategy_by_record.setdefault(
                    (code, record_id),
                    str(row.get("strategy") or row.get("raw_strategy") or ""),
                )
        if code and order_no:
            reason_by_order.setdefault((code, order_no), reason)
            if row.get("strategy") or row.get("raw_strategy"):
                strategy_by_order.setdefault(
                    (code, order_no),
                    str(row.get("strategy") or row.get("raw_strategy") or ""),
                )

    enriched: list[dict[str, Any]] = []
    for row in rows:
        code = _stock_code(row)
        reason = _explicit_add_reason(row)
        strategy = str(row.get("strategy") or row.get("raw_strategy") or "")
        record_id = _record_id(row)
        order_no = _order_no(row)
        if code and record_id:
            reason = reason or reason_by_record.get((code, record_id), "")
            strategy = strategy or strategy_by_record.get((code, record_id), "")
        if not reason and code and order_no:
            reason = reason_by_order.get((code, order_no), "")
        if not strategy and code and order_no:
            strategy = strategy_by_order.get((code, order_no), "")
        updates: dict[str, Any] = {}
        if reason and not _explicit_add_reason(row):
            updates["add_reason"] = reason
        if strategy and not (row.get("strategy") or row.get("raw_strategy")):
            updates["strategy"] = strategy
        enriched.append({**row, **updates} if updates else row)
    return enriched


def _build_post_submit_observations(
    events: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_code: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        code = _stock_code(event)
        event_time = _event_time(event)
        if not code or event_time is None:
            continue
        by_code.setdefault(code, []).append(event)
    for rows in by_code.values():
        rows.sort(
            key=lambda item: _event_time(item)
            or datetime.min.replace(tzinfo=timezone.utc)
        )
    return by_code


def _order_numbers(fields: dict[str, Any]) -> set[str]:
    raw_values = (
        fields.get("ord_no"),
        fields.get("order_no"),
        fields.get("odno"),
        fields.get("broker_order_no"),
        fields.get("broker_order_no_list"),
    )
    return {
        part.strip()
        for raw in raw_values
        for part in str(raw or "").split(",")
        if part.strip() and part.strip() != "-"
    }


def _attempt_id(anchor: dict[str, Any]) -> str:
    source_date = str(anchor.get("source_date") or _event_date(anchor) or "unknown")
    code = _stock_code(anchor) or "unknown"
    order_numbers = sorted(_order_numbers(anchor))
    if order_numbers:
        return f"{source_date}:{code}:order:{','.join(order_numbers)}"
    record_id = _record_id(anchor)
    anchor_time = _event_time(anchor)
    if record_id:
        return (
            f"{source_date}:{code}:record:{record_id}:time:"
            f"{anchor_time.isoformat() if anchor_time else 'unknown'}"
        )
    return (
        f"{source_date}:{code}:time:"
        f"{anchor_time.isoformat() if anchor_time else 'unknown'}"
    )


def _event_matches_anchor(
    event: dict[str, Any], anchor: dict[str, Any], *, exact_only: bool
) -> bool:
    if _stock_code(event) != _stock_code(anchor):
        return False
    anchor_record_id = _record_id(anchor)
    event_record_id = _record_id(event)
    if anchor_record_id and event_record_id and anchor_record_id != event_record_id:
        return False
    stage = str(event.get("stage") or "")
    if _is_terminal_after_submit(event):
        # SELL has its own broker order. Its owner is the position lifecycle.
        return bool(anchor_record_id and anchor_record_id == event_record_id)
    anchor_orders = _order_numbers(anchor)
    event_orders = _order_numbers(event)
    if (
        anchor_orders
        and event_orders
        and (stage == "scale_in_executed" or stage.endswith("_submitted"))
    ):
        return bool(anchor_orders & event_orders)
    if anchor_record_id and event_record_id:
        return anchor_record_id == event_record_id
    return not exact_only and not anchor_record_id and not anchor_orders


def _attempt_requested_qty(anchor: dict[str, Any]) -> int:
    for key in (
        "scale_in_split_order_original_qty",
        "submitted_qty",
        "effective_qty",
        "requested_qty",
        "bundle_requested_qty",
        "order_requested_qty",
        "qty",
        "fill_qty",
    ):
        qty = _safe_int(anchor.get(key), 0)
        if qty > 0:
            return qty
    return 0


def _is_distinct_followup_attempt(
    event: dict[str, Any], anchor: dict[str, Any]
) -> bool:
    if _stock_code(event) != _stock_code(anchor):
        return False
    stage = str(event.get("stage") or "")
    if stage == "scale_in_order_leg_submitted" or not (
        stage.endswith("_submitted") or stage == "add_order_sent"
    ):
        return False
    anchor_orders = _order_numbers(anchor)
    event_orders = _order_numbers(event)
    if anchor_orders and event_orders:
        return not bool(anchor_orders & event_orders)
    anchor_record_id = _record_id(anchor)
    event_record_id = _record_id(event)
    if not anchor_record_id or anchor_record_id != event_record_id:
        return False
    anchor_time = _event_time(anchor)
    event_time = _event_time(event)
    return bool(
        anchor_time
        and event_time
        and (event_time - anchor_time).total_seconds() > ANCHOR_RECONSTRUCT_WINDOW_SEC
    )


def _receipt_flags_complete(fields: dict[str, Any], *, sell: bool) -> bool:
    keys = (
        (
            "sell_execution_receipt_economics_complete",
            "sell_execution_receipt_quantity_contract_complete",
            "sell_execution_receipt_unit_fill_consistent",
            "broker_execution_provenance_complete",
        )
        if sell
        else (
            "receipt_economics_complete",
            "receipt_quantity_contract_complete",
            "receipt_unit_fill_consistent",
            "broker_execution_provenance_complete",
        )
    )
    return all(_safe_bool(fields.get(key)) for key in keys)


def _unique_attempt_anchors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priorities = {
        "scale_in_order_submitted": 0,
        "add_order_sent": 2,
        "scale_in_executed": 3,
    }
    primary_rows: list[dict[str, Any]] = []
    fallback_execution_rows: list[dict[str, Any]] = []
    for row in rows:
        if not _safe_bool(row.get("actual_order_submitted")):
            continue
        stage = str(row.get("stage") or "")
        if stage == "scale_in_order_leg_submitted":
            continue
        if stage == "scale_in_executed":
            fallback_execution_rows.append(row)
            continue
        if not (stage.endswith("_submitted") or stage == "add_order_sent"):
            continue
        primary_rows.append(row)
    selected: list[tuple[int, dict[str, Any]]] = []
    for row in sorted(
        [*primary_rows, *fallback_execution_rows],
        key=lambda item: _event_time(item) or datetime.min.replace(tzinfo=timezone.utc),
    ):
        stage = str(row.get("stage") or "")
        priority = priorities.get(stage, 1 if stage.endswith("_submitted") else 9)
        row_orders = _order_numbers(row)
        row_record_id = _record_id(row)
        row_time = _event_time(row)
        matched_indexes: list[int] = []
        for index, (_, previous_row) in enumerate(selected):
            if _stock_code(previous_row) != _stock_code(row):
                continue
            previous_orders = _order_numbers(previous_row)
            if row_orders and previous_orders and row_orders & previous_orders:
                matched_indexes.append(index)
                continue
            previous_time = _event_time(previous_row)
            if (
                row_record_id
                and row_record_id == _record_id(previous_row)
                and (not row_orders or not previous_orders)
                and row_time
                and previous_time
                and abs((row_time - previous_time).total_seconds())
                <= ANCHOR_RECONSTRUCT_WINDOW_SEC
            ):
                matched_indexes.append(index)
        if not matched_indexes:
            selected.append((priority, row))
            continue
        best = min(
            [(priority, row), *(selected[index] for index in matched_indexes)],
            key=lambda item: item[0],
        )
        selected[matched_indexes[0]] = best
        for index in reversed(matched_indexes[1:]):
            del selected[index]
    return [
        item[1]
        for item in sorted(
            selected,
            key=lambda item: _event_time(item[1])
            or datetime.min.replace(tzinfo=timezone.utc),
        )
    ]


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
    record_id = _record_id(anchor)
    requested_qty = _attempt_requested_qty(anchor)
    exact_identity = bool(record_id and _order_numbers(anchor))
    result = {
        "attempt_id": _attempt_id(anchor),
        "source_date": str(anchor.get("source_date") or _event_date(anchor) or ""),
        "context_bucket": _context_bucket(anchor),
        "code": code,
        "record_id": record_id or None,
        "anchor_time": anchor_time.isoformat() if anchor_time else None,
        "anchor_stage": anchor.get("stage"),
        "requested_qty": requested_qty,
        "replay_contract_version": ECONOMIC_GATE_VERSION,
        "strategy": str(anchor.get("strategy") or "").upper(),
        "execution_price_samples": [],
        "terminal_elapsed_sec": None,
        "observation_end_elapsed_sec": None,
        "applied_policy_version": str(
            anchor.get("scale_in_split_order_policy_version") or ""
        ),
        "applied_variant_id": str(anchor.get("scale_in_split_order_variant_id") or ""),
        "policy_applicable_qty": requested_qty >= 2,
        "exact_attempt_identity": exact_identity,
        "base_price": base_price,
        "base_price_source": base_price_source,
        "fixed_control_price_complete": (
            (str(anchor.get("partial_submit_failure") or "").strip() in {"", "-"})
            and (
                _price_from_fields(
                    anchor,
                    ("request_price", "final_price", "resolved_price", "order_price"),
                )
                > 0
                or base_price_source == "reconstructed_from_scale_in_price_resolved"
            )
        ),
        "market_like_order": order_market_like,
        "observed": False,
        "min_observed_price": None,
        "max_observed_price": None,
        "down_ticks_reached": None,
        "down_pct_reached": None,
        "touch_0tick": False,
        "touch_1tick": False,
        "touch_2tick": False,
        "touch_0_3pct": False,
        "touch_0_5pct": False,
        "touch_0_8pct": False,
        "touch_1_0pct": False,
        "touch_1_5pct": False,
        "missed_upside_proxy": False,
        "additional_mfe_pct": None,
        "additional_mae_pct": None,
        "actual_fill_qty": 0,
        "actual_fill_price": None,
        "scale_in_receipt_quality_complete": False,
        "terminal_sell_price": None,
        "terminal_receipt_quality_complete": False,
        "real_outcome_joined": False,
        "additional_mfe_mae_joined": False,
        "actual_split_applied": _safe_bool(
            anchor.get("scale_in_split_order_policy_applied")
        )
        or _safe_int(anchor.get("submitted_leg_count"), 0) > 1,
    }
    if anchor_time is None or not code or base_price <= 0 or order_market_like:
        if order_market_like:
            result["not_applicable_reason"] = "market_split_promotion_removed"
        return result
    tick = _tick_size(base_price)
    min_price: int | None = None
    max_price: int | None = None
    end_time = anchor_time + timedelta(seconds=COUNTERFACTUAL_WINDOW_SEC)
    next_attempt_times = [
        event_time
        for event in observations_by_code.get(code, [])
        if (event_time := _event_time(event)) is not None
        and event_time > anchor_time
        and str(event.get("add_type") or event.get("scale_in_type") or "").upper()
        == "AVG_DOWN"
        and str(event.get("stage") or "") != "scale_in_order_leg_submitted"
        and (
            str(event.get("stage") or "").endswith("_submitted")
            or str(event.get("stage") or "") == "add_order_sent"
        )
        and _is_distinct_followup_attempt(event, anchor)
    ]
    if next_attempt_times:
        end_time = min(end_time, min(next_attempt_times))
    exact_events: list[dict[str, Any]] = []
    diagnostic_events: list[dict[str, Any]] = []
    for event in observations_by_code.get(code, []):
        event_time = _event_time(event)
        if event_time is None:
            continue
        if event_time >= anchor_time - timedelta(
            seconds=ANCHOR_RECONSTRUCT_WINDOW_SEC
        ) and _event_matches_anchor(event, anchor, exact_only=True):
            exact_events.append(event)
        if event_time < anchor_time:
            continue
        if event_time <= end_time and _event_matches_anchor(
            event, anchor, exact_only=False
        ):
            diagnostic_events.append(event)
    path_events = exact_events if exact_identity else diagnostic_events
    price_samples: dict[float, int] = {}
    price_conflict = False
    for event in path_events:
        event_time = _event_time(event)
        if event_time is None or event_time < anchor_time or event_time > end_time:
            continue
        if event is not anchor and _is_terminal_after_submit(event):
            end_time = min(end_time, event_time)
            break
        # Own fills do not prove a post-submit market observation. Sim quotes
        # and explicitly stale snapshots cannot establish executable touches.
        if (
            "sim" in str(event.get("stage") or "").lower()
            or event.get("sim_record_id")
            or _safe_bool(event.get("quote_stale"))
            or _safe_bool(event.get("quote_stale_at_submit"))
        ):
            continue
        price = _price_from_fields(event, ("curr_price", "canonical_mark_price"))
        if price > 0:
            elapsed = round((event_time - anchor_time).total_seconds(), 6)
            if elapsed in price_samples and price_samples[elapsed] != price:
                price_conflict = True
            price_samples[elapsed] = price
            min_price = price if min_price is None else min(min_price, price)
            max_price = price if max_price is None else max(max_price, price)

    fill_rows_by_key: dict[str, dict[str, Any]] = {}
    terminal_event: dict[str, Any] | None = None
    receipt_conflict = False
    terminal_conflict = False
    for event in exact_events:
        stage = str(event.get("stage") or "")
        if stage == "scale_in_executed":
            anchor_orders = _order_numbers(anchor)
            event_orders = _order_numbers(event)
            if anchor_orders and (
                not event_orders or not (anchor_orders & event_orders)
            ):
                continue
            fill_key = str(event.get("execution_no") or "").strip()
            if not fill_key or fill_key == "-":
                receipt_conflict = True
                continue
            fill_key = f"{','.join(sorted(event_orders))}:{fill_key}"
            previous = fill_rows_by_key.get(fill_key)
            if previous and any(
                previous.get(key) != event.get(key)
                for key in (
                    "fill_price",
                    "fill_qty",
                    "receipt_economics_complete",
                    "receipt_quantity_contract_complete",
                    "receipt_unit_fill_consistent",
                    "broker_execution_provenance_complete",
                )
            ):
                receipt_conflict = True
            fill_rows_by_key.setdefault(fill_key, event)
        if (
            stage == "sell_completed"
            and (_event_time(event) or anchor_time) >= anchor_time
        ):
            if terminal_event and any(
                terminal_event.get(key) != event.get(key)
                for key in (
                    "sell_price",
                    "position_weighted_sell_price",
                    "last_sell_fill_price",
                    "sell_execution_receipt_economics_complete",
                    "sell_execution_receipt_quantity_contract_complete",
                    "sell_execution_receipt_unit_fill_consistent",
                    "broker_execution_provenance_complete",
                )
            ):
                terminal_conflict = True
            terminal_event = terminal_event or event
    fill_rows = list(fill_rows_by_key.values())
    actual_fill_qty = sum(_safe_int(item.get("fill_qty"), 0) for item in fill_rows)
    fill_notional = sum(
        _safe_int(item.get("fill_qty"), 0)
        * _price_from_fields(item, ("fill_price", "assumed_fill_price"))
        for item in fill_rows
    )
    actual_fill_price = (
        round(fill_notional / actual_fill_qty, 4) if actual_fill_qty > 0 else None
    )
    scale_in_receipt_quality_complete = (
        bool(fill_rows)
        and all(
            _receipt_flags_complete(item, sell=False)
            and _safe_int(item.get("fill_qty"), 0) > 0
            and (_safe_float(item.get("fill_price"), 0.0) or 0.0) > 0
            for item in fill_rows
        )
        and not receipt_conflict
        and (
            terminal_event is None
            or all(
                _event_time(item) <= _event_time(terminal_event) for item in fill_rows
            )
        )
    )
    terminal_sell_price = (
        _price_from_fields(
            terminal_event or {},
            ("sell_price", "position_weighted_sell_price", "last_sell_fill_price"),
        )
        if terminal_event
        else 0
    )
    terminal_receipt_quality_complete = bool(
        terminal_event
        and _receipt_flags_complete(terminal_event, sell=True)
        and not terminal_conflict
    )
    full_fill_complete = requested_qty >= 2 and actual_fill_qty == requested_qty
    terminal_elapsed = (
        (_event_time(terminal_event) - anchor_time).total_seconds()
        if terminal_event and _event_time(terminal_event)
        else None
    )
    result.update(
        {
            "execution_price_samples": [
                {"elapsed_sec": elapsed, "price": price}
                for elapsed, price in sorted(price_samples.items())
            ],
            "price_sample_conflict": price_conflict,
            "terminal_elapsed_sec": terminal_elapsed,
            "observation_end_elapsed_sec": (end_time - anchor_time).total_seconds(),
            "actual_fill_class": (
                "full_fill" if full_fill_complete else "partial_or_unfilled"
            ),
            "actual_fill_qty": actual_fill_qty,
            "actual_fill_price": actual_fill_price,
            "scale_in_receipt_quality_complete": scale_in_receipt_quality_complete,
            "terminal_sell_price": terminal_sell_price or None,
            "terminal_receipt_quality_complete": terminal_receipt_quality_complete,
            "real_outcome_joined": bool(
                exact_identity
                and full_fill_complete
                and scale_in_receipt_quality_complete
                and terminal_sell_price > 0
                and terminal_receipt_quality_complete
            ),
        }
    )
    if min_price is None:
        return result
    down_ticks = max(0, int((base_price - min_price) // tick))
    down_pct = max(0.0, round(((base_price - min_price) / base_price) * 100.0, 4))
    result.update(
        {
            "observed": True,
            "min_observed_price": min_price,
            "max_observed_price": max_price,
            "down_ticks_reached": down_ticks,
            "down_pct_reached": down_pct,
            "touch_0tick": min_price <= base_price,
            "touch_1tick": min_price <= base_price - tick,
            "touch_2tick": min_price <= base_price - (2 * tick),
            "touch_0_3pct": down_pct >= 0.3,
            "touch_0_5pct": down_pct >= 0.5,
            "touch_0_8pct": down_pct >= 0.8,
            "touch_1_0pct": down_pct >= 1.0,
            "touch_1_5pct": down_pct >= 1.5,
            "missed_upside_proxy": min_price > base_price - tick
            and (max_price or 0) >= base_price + tick,
            "additional_mfe_pct": round(
                (((max_price or base_price) - base_price) / base_price) * 100.0,
                4,
            ),
            "additional_mae_pct": round(
                ((min_price - base_price) / base_price) * 100.0,
                4,
            ),
            "additional_mfe_mae_joined": bool(
                exact_identity
                and requested_qty >= 2
                and price_samples
                and max(price_samples) > 0
                and not price_conflict
            ),
        }
    )
    return result


def _counterfactual_summary(
    bucket_rows: list[dict[str, Any]],
    all_events: list[dict[str, Any]],
    *,
    historical_anchor_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    anchors = _unique_attempt_anchors(bucket_rows)
    observations_by_code = _build_post_submit_observations(all_events)
    daily_anchor_results = [
        _counterfactual_for_anchor(
            anchor, events=all_events, observations_by_code=observations_by_code
        )
        for anchor in anchors
    ]
    combined: dict[str, dict[str, Any]] = {}
    for item in historical_anchor_results or []:
        attempt_id = str(item.get("attempt_id") or "")
        if attempt_id:
            combined[attempt_id] = item
    for item in daily_anchor_results:
        combined[str(item.get("attempt_id") or _attempt_id(item))] = item
    anchor_results = list(combined.values())
    observed = [item for item in anchor_results if item.get("observed")]
    market_count = sum(1 for item in anchor_results if item.get("market_like_order"))
    reconstruct_gap_count = sum(
        1
        for item in anchor_results
        if item.get("base_price_source") == "reconstruct_gap"
    )
    join_gap_count = len(anchor_results) - len(observed) - market_count

    def rate(key: str) -> float | None:
        if not observed:
            return None
        return round(sum(1 for item in observed if item.get(key)) / len(observed), 4)

    min_observed_values = [
        _safe_int(item.get("min_observed_price"), 0) for item in observed
    ]
    down_ticks_values = [
        _safe_int(item.get("down_ticks_reached"), 0)
        for item in observed
        if item.get("down_ticks_reached") is not None
    ]
    down_pct_values = [
        _safe_float(item.get("down_pct_reached"), 0.0) or 0.0
        for item in observed
        if item.get("down_pct_reached") is not None
    ]
    return {
        "counterfactual_anchor_count": len(anchor_results),
        "daily_counterfactual_anchor_count": len(daily_anchor_results),
        "unique_attempt_count": len(anchor_results),
        "eligible_runtime_attempt_count": sum(
            1
            for item in anchor_results
            if item.get("policy_applicable_qty") and item.get("exact_attempt_identity")
        ),
        "real_outcome_joined_sample": sum(
            1 for item in anchor_results if item.get("real_outcome_joined")
        ),
        "additional_mfe_mae_joined_sample": sum(
            1 for item in anchor_results if item.get("additional_mfe_mae_joined")
        ),
        "actual_split_outcome_sample": sum(
            1
            for item in anchor_results
            if item.get("actual_split_applied") and item.get("real_outcome_joined")
        ),
        "post_submit_observed_sample": len(observed),
        "market_order_sample_count": market_count,
        "price_observation_join_gap_count": max(0, join_gap_count),
        "base_price_reconstruction_gap_count": reconstruct_gap_count,
        "min_observed_price": min(min_observed_values) if min_observed_values else None,
        "max_down_ticks_reached": max(down_ticks_values) if down_ticks_values else None,
        "avg_down_ticks_reached": (
            round(sum(down_ticks_values) / len(down_ticks_values), 4)
            if down_ticks_values
            else None
        ),
        "max_down_pct_reached": max(down_pct_values) if down_pct_values else None,
        "avg_down_pct_reached": (
            round(sum(down_pct_values) / len(down_pct_values), 4)
            if down_pct_values
            else None
        ),
        "touch_0tick_rate": rate("touch_0tick"),
        "touch_1tick_rate": rate("touch_1tick"),
        "touch_2tick_rate": rate("touch_2tick"),
        "touch_0_3pct_rate": rate("touch_0_3pct"),
        "touch_0_5pct_rate": rate("touch_0_5pct"),
        "touch_0_8pct_rate": rate("touch_0_8pct"),
        "touch_1_0pct_rate": rate("touch_1_0pct"),
        "touch_1_5pct_rate": rate("touch_1_5pct"),
        "missed_upside_proxy_rate": rate("missed_upside_proxy"),
        "anchor_samples": anchor_results[:20],
        "daily_anchor_results": daily_anchor_results,
        "rolling_anchor_results": anchor_results,
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = max(0.0, min(1.0, percentile)) * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


def _candidate_price_qty_plan(
    anchor: dict[str, Any], selected: dict[str, Any]
) -> list[tuple[int, int]]:
    qty = _safe_int(anchor.get("requested_qty"), 0)
    base_price = _safe_int(anchor.get("base_price"), 0)
    if qty < 2 or base_price <= 0:
        return []
    leg_count = min(
        max(1, _safe_int(selected.get("leg_count"), 2)),
        MAX_SCALE_IN_SPLIT_LEGS,
        qty,
    )
    raw_weights = selected.get("qty_weights")
    weights = (
        [_safe_float(item, 0.0) or 0.0 for item in raw_weights]
        if isinstance(raw_weights, list)
        else []
    )
    quantities = (
        _split_qty_by_weights(qty, leg_count, weights)
        if weights
        else _split_qty(
            qty,
            leg_count,
            _safe_float(selected.get("qty_weight_min"), 0.5) or 0.5,
        )
    )
    raw_pct_offsets = selected.get("price_offsets_pct")
    if raw_pct_offsets == "market" or selected.get("price_offsets_ticks") == "market":
        return [(leg_qty, base_price) for leg_qty in quantities]
    pct_offsets = (
        [max(0.0, _safe_float(item, 0.0) or 0.0) for item in raw_pct_offsets]
        if isinstance(raw_pct_offsets, list)
        else []
    )
    tick_offsets = selected.get("price_offsets_ticks")
    tick_offsets = (
        [_safe_int(item, 0) for item in tick_offsets]
        if isinstance(tick_offsets, list)
        else []
    )
    tick = _tick_size(base_price)
    plan: list[tuple[int, int]] = []
    for idx, leg_qty in enumerate(quantities):
        if pct_offsets:
            offset = pct_offsets[min(idx, len(pct_offsets) - 1)]
            price = _pct_price_offset(base_price, offset)
        else:
            offset = (
                tick_offsets[min(idx, len(tick_offsets) - 1)] if tick_offsets else idx
            )
            price = clamp_price_to_tick(max(1, base_price - (tick * offset)))
        plan.append((leg_qty, price))
    return plan


def _replay_execution(
    anchor: dict[str, Any], selected: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Sampled market-touch replay with the unchanged runtime TTLs."""
    qty = _safe_int(anchor.get("requested_qty"), 0)
    base = _safe_int(anchor.get("base_price"), 0)
    if qty < 2 or base <= 0 or anchor.get("market_like_order"):
        return None
    if anchor.get("replay_contract_version") != ECONOMIC_GATE_VERSION:
        return None
    if not anchor.get("fixed_control_price_complete"):
        return None
    if str(anchor.get("strategy") or "").upper() not in {"SCALPING", "SCALP"}:
        return None
    raw_samples = anchor.get("execution_price_samples")
    if not isinstance(raw_samples, list) or not raw_samples:
        return None
    samples: list[tuple[float, int]] = []
    for item in raw_samples:
        if not isinstance(item, dict):
            return None
        elapsed = _safe_float(item.get("elapsed_sec"), None)
        price = _safe_int(item.get("price"), 0)
        if elapsed is None or elapsed < 0 or price <= 0:
            return None
        samples.append((elapsed, price))
    if anchor.get("price_sample_conflict"):
        return None
    terminal_sec = _safe_float(anchor.get("terminal_elapsed_sec"), None)
    if terminal_sec is None or terminal_sec < 0:
        return None
    path_end = _safe_float(anchor.get("observation_end_elapsed_sec"), None)
    if path_end is None:
        return None
    samples = sorted((t, p) for t, p in samples if t < min(terminal_sec, path_end))
    if not samples:
        return None
    plan = _candidate_price_qty_plan(anchor, selected) if selected else [(qty, base)]
    ttls = scale_in_leg_ttl_seconds(len(plan), str(anchor.get("strategy") or ""))
    filled: list[tuple[int, int]] = []
    canceled_legs = 0
    for (leg_qty, price), ttl in zip(plan, ttls):
        deadline = min(float(ttl), terminal_sec, path_end)
        touched = any(t < deadline and observed <= price for t, observed in samples)
        if touched:
            filled.append((leg_qty, price))
        elif samples[-1][0] >= ttl or terminal_sec <= min(ttl, path_end):
            canceled_legs += 1
        else:
            # A short path is right-censored, not an unfilled zero-profit leg.
            return None
    filled_qty = sum(q for q, _ in filled)
    avg_price = sum(q * p for q, p in filled) / filled_qty if filled_qty else 0.0
    sell_price = _safe_float(anchor.get("terminal_sell_price"), None)
    if sell_price is None or sell_price <= 0:
        return None
    pnl = (
        calculate_net_realized_pnl(avg_price, sell_price, filled_qty)
        if filled_qty
        else 0
    )
    marks = [p for _, p in samples]
    return {
        "pnl_krw": pnl,
        "filled_qty": filled_qty,
        "fill_participation": filled_qty / qty,
        "cancel_rate": canceled_legs / len(plan),
        "mfe_pct": ((max(marks) / avg_price) - 1) * 100 if filled_qty else None,
        "mae_pct": ((min(marks) / avg_price) - 1) * 100 if filled_qty else None,
        "base_notional": base * qty,
    }


def _evaluate_candidate_economics(
    anchor_results: list[dict[str, Any]], selected: dict[str, Any]
) -> dict[str, Any]:
    eligible = [
        item
        for item in anchor_results
        if item.get("exact_attempt_identity")
        and item.get("policy_applicable_qty")
        and not item.get("market_like_order")
    ]
    price_joined = [item for item in eligible if item.get("additional_mfe_mae_joined")]
    outcome_joined = [item for item in eligible if item.get("real_outcome_joined")]
    deltas: list[float] = []
    participation: list[float] = []
    missed_upside: list[bool] = []
    sample_rows: list[dict[str, Any]] = []
    source_dates: set[str] = set()
    delta_pnl_total = 0
    base_notional_total = 0
    for item in eligible:
        if not (
            item.get("real_outcome_joined") and item.get("additional_mfe_mae_joined")
        ):
            continue
        source_date = str(item.get("source_date") or "")
        if not is_date_allowed(source_date, clean_baseline_policy()):
            continue
        control = _replay_execution(item, None)
        candidate = _replay_execution(item, selected)
        if control is None or candidate is None:
            continue
        delta_pnl = candidate["pnl_krw"] - control["pnl_krw"]
        base_notional = control["base_notional"]
        delta_pct = delta_pnl / base_notional * 100.0
        deltas.append(delta_pct)
        participation.append(candidate["fill_participation"])
        missed = candidate["pnl_krw"] < control["pnl_krw"] and control["pnl_krw"] > 0
        missed_upside.append(missed)
        delta_pnl_total += delta_pnl
        base_notional_total += base_notional
        source_dates.add(source_date)
        sample_rows.append(
            {
                "attempt_id": item.get("attempt_id"),
                "source_date": source_date,
                "delta_pnl_krw": delta_pnl,
                "delta_pct": round(delta_pct, 6),
                "control_pnl_krw": control["pnl_krw"],
                "candidate_pnl_krw": candidate["pnl_krw"],
                "modeled_fill_participation": candidate["fill_participation"],
                "fill_rate_delta": candidate["fill_participation"]
                - control["fill_participation"],
                "cancel_rate_delta": candidate["cancel_rate"] - control["cancel_rate"],
                "additional_mfe_pct_delta": (
                    candidate["mfe_pct"] - control["mfe_pct"]
                    if candidate["mfe_pct"] is not None
                    and control["mfe_pct"] is not None
                    else None
                ),
                "additional_mae_pct_delta": (
                    candidate["mae_pct"] - control["mae_pct"]
                    if candidate["mae_pct"] is not None
                    and control["mae_pct"] is not None
                    else None
                ),
                "missed_upside": missed,
                "actual_split_applied": bool(item.get("actual_split_applied")),
            }
        )
    weighted_ev = (
        delta_pnl_total / base_notional_total * 100.0 if base_notional_total else None
    )
    equal_ev = sum(deltas) / len(deltas) if deltas else None
    fill_rate = sum(participation) / len(participation) if participation else None
    downside_p10 = _percentile(deltas, 0.10)
    price_coverage = len(price_joined) / len(eligible) if eligible else 0.0
    blockers: list[str] = []
    if len(outcome_joined) < RUNTIME_REFRESH_REAL_OUTCOME_FLOOR:
        blockers.append("real_outcome_sample_floor")
    if len(price_joined) < RUNTIME_REFRESH_MFE_MAE_FLOOR:
        blockers.append("additional_mfe_mae_sample_floor")
    if len(deltas) < RUNTIME_REFRESH_REAL_OUTCOME_FLOOR:
        blockers.append("paired_economic_sample_floor")
    if len(source_dates) < RUNTIME_REFRESH_SOURCE_DATE_FLOOR:
        blockers.append("economic_source_date_floor")
    if price_coverage < RUNTIME_REFRESH_PRICE_JOIN_COVERAGE_FLOOR:
        blockers.append("price_join_coverage_floor")
    if (
        weighted_ev is not None
        and weighted_ev < RUNTIME_REFRESH_MIN_COST_ADJUSTED_EV_PCT
    ):
        blockers.append("cost_adjusted_ev_not_positive")
    if fill_rate is not None and fill_rate < RUNTIME_REFRESH_FILL_PARTICIPATION_FLOOR:
        blockers.append("modeled_fill_participation_floor")
    if (
        downside_p10 is not None
        and downside_p10 < RUNTIME_REFRESH_DOWNSIDE_P10_DELTA_FLOOR_PCT
    ):
        blockers.append("downside_p10_delta_floor")
    if selected.get("leg_count") != 2:
        blockers.append("three_leg_diagnostic_only")
    if selected.get("policy_mode") == POLICY_MODE_MARKET_QTY_SPLIT_ONLY:
        blockers.append("market_split_not_applicable")
    return {
        "eligible_runtime_attempt_count": len(eligible),
        "real_outcome_joined_sample": len(outcome_joined),
        "additional_mfe_mae_joined_sample": len(price_joined),
        "paired_economic_sample_count": len(deltas),
        "economic_source_dates": sorted(source_dates),
        "economic_source_date_count": len(source_dates),
        "control_definition": "unsplit_same_anchor_price_runtime_ttl_same_terminal",
        "replay_assumption": "sampled_market_touch_same_observed_terminal_not_real_fill_claim",
        "price_observation_joined_sample": len(price_joined),
        "price_observation_join_gap_count": max(0, len(eligible) - len(price_joined)),
        "price_join_coverage": round(price_coverage, 4),
        "equal_weight_avg_profit_pct": (
            round(equal_ev, 6) if equal_ev is not None else None
        ),
        "notional_weighted_ev_pct": (
            round(weighted_ev, 6) if weighted_ev is not None else None
        ),
        "source_quality_adjusted_ev_pct": (
            round(weighted_ev, 6) if weighted_ev is not None else None
        ),
        "modeled_fill_participation": (
            round(fill_rate, 4) if fill_rate is not None else None
        ),
        "missed_upside_rate": (
            sum(missed_upside) / len(missed_upside) if missed_upside else None
        ),
        "downside_p10_profit_rate": (
            round(downside_p10, 6) if downside_p10 is not None else None
        ),
        "economic_delta_pnl_krw": delta_pnl_total,
        "economic_base_notional_krw": base_notional_total,
        "economic_sample_rows": sample_rows,
        "runtime_apply_blockers": blockers,
        "runtime_apply_allowed": not blockers,
    }


def _post_apply_attribution(anchors: list[dict[str, Any]]) -> dict[str, Any]:
    """R6: actual full-fill receipts against the fixed unsplit control.

    Partial/unfilled attempts are counted separately, never pooled into full-fill EV.
    Cancel/late-fill outcomes without authoritative receipts remain unmeasured.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    unattributed = 0
    for item in anchors:
        if not item.get("actual_split_applied"):
            continue
        version = str(item.get("applied_policy_version") or "")
        variant = str(item.get("applied_variant_id") or "")
        if not version or not variant:
            unattributed += 1
            continue
        groups.setdefault((version, variant), []).append(item)
    rows: list[dict[str, Any]] = []
    for (version, variant), items in sorted(groups.items()):
        paired: list[dict[str, Any]] = []
        for item in items:
            if not item.get("real_outcome_joined") or not item.get(
                "additional_mfe_mae_joined"
            ):
                continue
            control = _replay_execution(item, None)
            if control is None:
                continue
            actual_price = _safe_float(item.get("actual_fill_price"), None)
            if actual_price is None or actual_price <= 0:
                continue
            actual_pnl = calculate_net_realized_pnl(
                actual_price, item["terminal_sell_price"], item["actual_fill_qty"]
            )
            marks = [row["price"] for row in item["execution_price_samples"]]
            paired.append(
                {
                    "attempt_id": item["attempt_id"],
                    "source_date": item["source_date"],
                    "delta_pnl_krw": actual_pnl - control["pnl_krw"],
                    "base_notional": control["base_notional"],
                    "fill_rate_delta": 1.0 - control["fill_participation"],
                    "additional_mfe_pct_delta": (
                        ((max(marks) / actual_price) - 1) * 100 - control["mfe_pct"]
                        if control["mfe_pct"] is not None
                        else None
                    ),
                    "additional_mae_pct_delta": (
                        ((min(marks) / actual_price) - 1) * 100 - control["mae_pct"]
                        if control["mae_pct"] is not None
                        else None
                    ),
                    "missed_upside": actual_pnl < control["pnl_krw"]
                    and control["pnl_krw"] > 0,
                }
            )
        dates = sorted({str(item["source_date"]) for item in paired})
        notional = sum(item["base_notional"] for item in paired)
        ev = (
            sum(item["delta_pnl_krw"] for item in paired) / notional * 100
            if notional
            else None
        )

        def mean(key: str) -> float | None:
            values = [item[key] for item in paired if item[key] is not None]
            return sum(values) / len(values) if values else None

        rows.append(
            {
                "policy_version": version,
                "split_variant_id": variant,
                "attempt_count": len(items),
                "actual_full_fill_attempt_count": sum(
                    item.get("actual_fill_class") == "full_fill" for item in items
                ),
                "partial_or_unfilled_attempt_count": sum(
                    item.get("actual_fill_class") != "full_fill" for item in items
                ),
                "paired_full_fill_sample_count": len(paired),
                "economic_source_dates": dates,
                "source_quality_adjusted_ev_pct": (
                    round(ev, 6) if ev is not None else None
                ),
                "fill_rate_delta": mean("fill_rate_delta"),
                "additional_mfe_pct_delta": mean("additional_mfe_pct_delta"),
                "additional_mae_pct_delta": mean("additional_mae_pct_delta"),
                "missed_upside_rate": mean("missed_upside"),
                "cancel_rate_delta": None,
                "cancel_rate_status": "not_measured_no_exact_cancel_receipt_join",
                "negative_economic_evidence": bool(
                    len(paired) >= RUNTIME_REFRESH_REAL_OUTCOME_FLOOR
                    and len(dates) >= RUNTIME_REFRESH_SOURCE_DATE_FLOOR
                    and ev is not None
                    and ev < 0
                ),
                "sample_rows": paired,
            }
        )
    return {
        "status": "observed" if rows else "not_observed",
        "comparison": "actual_full_fill_vs_fixed_unsplit_ttl_control_same_terminal",
        "unattributed_split_attempt_count": unattributed,
        "policy_versions": rows,
    }


def _load_rolling_anchor_results(
    target_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    clean_policy = clean_baseline_policy()
    dated_paths: list[tuple[str, Path]] = []
    for path in REPORT_DIR.glob(f"{REPORT_TYPE}_*.json"):
        source_date = path.stem.removeprefix(f"{REPORT_TYPE}_")
        if len(source_date) != 10 or source_date >= target_date:
            continue
        if not is_date_allowed(source_date, clean_policy):
            continue
        dated_paths.append((source_date, path))
    selected_paths = sorted(dated_paths)[-(ROLLING_REPORT_DATE_LIMIT - 1) :]
    by_attempt: dict[str, dict[str, Any]] = {}
    accepted_dates: list[str] = []
    excluded_dates: list[dict[str, str]] = []
    for source_date, path in selected_paths:
        payload = _load_json(path)
        if (
            payload.get("schema_version") != SCHEMA_VERSION
            or str(payload.get("target_date") or "") != source_date
        ):
            excluded_dates.append(
                {"source_date": source_date, "reason": "report_contract_mismatch"}
            )
            continue
        source_quality = (
            payload.get("source_quality")
            if isinstance(payload.get("source_quality"), dict)
            else {}
        )
        if source_quality.get("tuning_input_allowed") is not True:
            excluded_dates.append(
                {"source_date": source_date, "reason": "source_quality_not_allowed"}
            )
            continue
        rows = payload.get("daily_attempt_outcomes")
        if not isinstance(rows, list):
            excluded_dates.append(
                {"source_date": source_date, "reason": "daily_attempt_outcomes_missing"}
            )
            continue
        accepted_dates.append(source_date)
        for item in rows:
            if not isinstance(item, dict):
                continue
            attempt_id = str(item.get("attempt_id") or "")
            if (
                attempt_id
                and item.get("source_date") == source_date
                and item.get("replay_contract_version") == ECONOMIC_GATE_VERSION
            ):
                by_attempt[attempt_id] = item
    return list(by_attempt.values()), {
        "window_policy": "latest_20_report_dates_including_target",
        "historical_source_dates": accepted_dates,
        "historical_source_date_count": len(accepted_dates),
        "excluded_dates": excluded_dates,
        "historical_unique_attempt_count": len(by_attempt),
    }


def _selected_policy_from_counterfactual(summary: dict[str, Any]) -> dict[str, Any]:
    observed_sample = _safe_int(summary.get("post_submit_observed_sample"), 0)
    market_sample = _safe_int(summary.get("market_order_sample_count"), 0)
    anchor_count = _safe_int(summary.get("counterfactual_anchor_count"), 0)
    if anchor_count > 0 and market_sample > 0 and observed_sample <= 0:
        return {
            "leg_count": 2,
            "price_offsets_ticks": "market",
            "price_offsets_pct": "market",
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
            "price_offsets_pct": [0.0, 0.3],
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
    touch03pct = _safe_float(summary.get("touch_0_3pct_rate"), 0.0) or 0.0
    touch05pct = _safe_float(summary.get("touch_0_5pct_rate"), 0.0) or 0.0
    touch08pct = _safe_float(summary.get("touch_0_8pct_rate"), 0.0) or 0.0
    touch1pct = _safe_float(summary.get("touch_1_0pct_rate"), 0.0) or 0.0
    touch15pct = _safe_float(summary.get("touch_1_5pct_rate"), 0.0) or 0.0
    missed = _safe_float(summary.get("missed_upside_proxy_rate"), 0.0) or 0.0
    if (touch08pct >= 0.40 or touch15pct >= 0.25) and missed < 0.40:
        return {
            "leg_count": 2,
            "price_offsets_ticks": [0, 2],
            "price_offsets_pct": [0.0, 0.8],
            "qty_weights": [0.6, 0.4],
            "qty_weight_min": 0.6,
            "qty_weight_max": 0.4,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_60_40_VARIANT_ID,
            "selection_reason": "touch_0_8pct_high_with_low_missed_upside",
            "runtime_apply_allowed": True,
        }
    if touch03pct < 0.30 or touch05pct < 0.30 or touch1 < 0.30 or missed >= 0.40:
        return {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weights": [0.7, 0.3],
            "qty_weight_min": 0.7,
            "qty_weight_max": 0.3,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_70_30_VARIANT_ID,
            "selection_reason": "touch_0_3pct_low_or_missed_upside_high",
            "runtime_apply_allowed": True,
        }
    if touch08pct >= 0.40 or touch1pct >= 0.40 or (touch1 >= 0.70 and touch2 >= 0.40):
        return {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weights": [0.5, 0.5],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_50_50_VARIANT_ID,
            "selection_reason": "touch_0_8pct_ready_or_tick_band_high",
            "runtime_apply_allowed": True,
        }
    return {
        "leg_count": 2,
        "price_offsets_ticks": [0, 1],
        "price_offsets_pct": [0.0, 0.3],
        "qty_weights": [0.5, 0.5],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
        "split_variant_id": COUNTERFACTUAL_50_50_VARIANT_ID,
        "selection_reason": "touch_0_3pct_mid_range_pct_baseline",
        "runtime_apply_allowed": True,
    }


def _two_leg_variant_grid(selected: dict[str, Any]) -> list[dict[str, Any]]:
    if selected.get("policy_mode") == POLICY_MODE_MARKET_QTY_SPLIT_ONLY:
        return [dict(selected)]
    variants = [
        dict(selected),
        {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weights": [0.7, 0.3],
            "qty_weight_min": 0.7,
            "qty_weight_max": 0.3,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_70_30_VARIANT_ID,
            "selection_reason": "existing_variant_grid_70_30",
            "runtime_apply_allowed": False,
        },
        {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weights": [0.5, 0.5],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_50_50_VARIANT_ID,
            "selection_reason": "existing_variant_grid_50_50",
            "runtime_apply_allowed": False,
        },
        {
            "leg_count": 2,
            "price_offsets_ticks": [0, 2],
            "price_offsets_pct": [0.0, 0.8],
            "qty_weights": [0.6, 0.4],
            "qty_weight_min": 0.6,
            "qty_weight_max": 0.4,
            "policy_mode": POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": COUNTERFACTUAL_60_40_VARIANT_ID,
            "selection_reason": "existing_variant_grid_60_40",
            "runtime_apply_allowed": False,
        },
    ]
    by_variant: dict[str, dict[str, Any]] = {}
    for item in variants:
        variant_id = str(item.get("split_variant_id") or "")
        if variant_id:
            by_variant.setdefault(variant_id, item)
    return list(by_variant.values())


def _economic_rank(candidate: dict[str, Any]) -> tuple[float, float, float]:
    def value_or_floor(key: str, floor: float) -> float:
        value = _safe_float(candidate.get(key), None)
        return value if value is not None else floor

    return (
        value_or_floor("source_quality_adjusted_ev_pct", -999.0),
        value_or_floor("modeled_fill_participation", -1.0),
        value_or_floor("downside_p10_profit_rate", -999.0),
    )


def _three_leg_candidate(bucket: str, summary: dict[str, Any]) -> dict[str, Any] | None:
    observed_sample = _safe_int(summary.get("post_submit_observed_sample"), 0)
    touch1 = _safe_float(summary.get("touch_1tick_rate"), 0.0) or 0.0
    touch2 = _safe_float(summary.get("touch_2tick_rate"), 0.0) or 0.0
    if observed_sample <= 0 or touch1 < 0.70 or touch2 < 0.40:
        return None
    candidate = {
        **{key: value for key, value in summary.items() if key != "anchor_samples"},
        "context_bucket": bucket,
        "leg_count": 3,
        "price_offsets_ticks": [0, 1, 2],
        "price_offsets_pct": [0.0, 0.3, 0.8],
        "qty_weights": [0.5, 0.25, 0.25],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.25,
        "policy_mode": POLICY_MODE_DIAGNOSTIC_THREE_LEG,
        "split_variant_id": DIAGNOSTIC_THREE_LEG_VARIANT_ID,
        "selection_reason": "three_leg_diagnostic_only",
        "runtime_apply_allowed": False,
        "diagnostic_only": True,
    }
    economics = _evaluate_candidate_economics(
        list(summary.get("rolling_anchor_results") or []), candidate
    )
    candidate.update(economics)
    candidate["diagnostic_only"] = not bool(candidate["runtime_apply_allowed"])
    return candidate


def _candidate_for_bucket(
    bucket: str,
    rows: list[dict[str, Any]],
    all_events: list[dict[str, Any]],
    *,
    historical_anchor_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    real_rows = [row for row in rows if _safe_bool(row.get("actual_order_submitted"))]
    sim_rows = [
        row for row in rows if not _safe_bool(row.get("actual_order_submitted"))
    ]
    counterfactual = _counterfactual_summary(
        rows,
        all_events,
        historical_anchor_results=historical_anchor_results,
    )
    heuristic_selected = _selected_policy_from_counterfactual(counterfactual)
    evaluated_variants: list[dict[str, Any]] = []
    attribution = _post_apply_attribution(
        list(counterfactual.get("rolling_anchor_results") or [])
    )
    for variant in _two_leg_variant_grid(heuristic_selected):
        evaluated_variants.append(
            {
                **variant,
                **_evaluate_candidate_economics(
                    list(counterfactual.get("rolling_anchor_results") or []), variant
                ),
            }
        )
        if any(
            row["split_variant_id"] == variant["split_variant_id"]
            and row["negative_economic_evidence"]
            for row in attribution["policy_versions"]
        ):
            evaluated_variants[-1]["runtime_apply_blockers"].append(
                "post_apply_negative_economic_evidence"
            )
            evaluated_variants[-1]["runtime_apply_allowed"] = False
    runtime_variants = [
        item
        for item in evaluated_variants
        if _safe_bool(item.get("runtime_apply_allowed"))
    ]
    selected = (
        max(runtime_variants, key=_economic_rank)
        if runtime_variants
        else evaluated_variants[0]
    )
    candidate = {
        **counterfactual,
        "context_bucket": bucket,
        "leg_count": selected["leg_count"],
        "price_offsets_ticks": selected["price_offsets_ticks"],
        "price_offsets_pct": selected.get("price_offsets_pct"),
        "qty_weights": selected.get("qty_weights"),
        "qty_weight_min": selected["qty_weight_min"],
        "qty_weight_max": selected["qty_weight_max"],
        "fill_quality": None,
        "missed_upside": None,
        "diagnostic_sim_ev_pct": None,
        "partial_fill_rate": None,
        "cancel_rate": None,
        "late_fill_rate": None,
        "real_sample_count": _safe_int(
            counterfactual.get("unique_attempt_count"), len(real_rows)
        ),
        "sim_sample_count": len(sim_rows),
        "primary_sample_book": "post_submit_tick_band_counterfactual",
        "policy_mode": selected["policy_mode"],
        "split_variant_id": selected["split_variant_id"],
        "runtime_apply_allowed": False,
        "policy_generation_reason": "post_submit_tick_band_counterfactual_selector",
        "selection_reason": (
            f"economic_grid_best:{selected['split_variant_id']}"
            if runtime_variants
            else selected["selection_reason"]
        ),
        "heuristic_selection_reason": heuristic_selected.get("selection_reason"),
        "evaluated_variant_economics": [
            {
                key: item.get(key)
                for key in (
                    "split_variant_id",
                    "policy_mode",
                    "real_outcome_joined_sample",
                    "additional_mfe_mae_joined_sample",
                    "source_quality_adjusted_ev_pct",
                    "modeled_fill_participation",
                    "downside_p10_profit_rate",
                    "runtime_apply_allowed",
                    "runtime_apply_blockers",
                )
            }
            for item in evaluated_variants
        ],
        "counterfactual_sample_count": counterfactual.get(
            "post_submit_observed_sample"
        ),
        "post_submit_touch_rates": {
            "touch_0tick_rate": counterfactual.get("touch_0tick_rate"),
            "touch_1tick_rate": counterfactual.get("touch_1tick_rate"),
            "touch_2tick_rate": counterfactual.get("touch_2tick_rate"),
            "touch_0_3pct_rate": counterfactual.get("touch_0_3pct_rate"),
            "touch_0_5pct_rate": counterfactual.get("touch_0_5pct_rate"),
            "touch_0_8pct_rate": counterfactual.get("touch_0_8pct_rate"),
            "touch_1_0pct_rate": counterfactual.get("touch_1_0pct_rate"),
            "touch_1_5pct_rate": counterfactual.get("touch_1_5pct_rate"),
            "missed_upside_proxy_rate": counterfactual.get("missed_upside_proxy_rate"),
        },
    }
    candidate.update(
        _evaluate_candidate_economics(
            list(counterfactual.get("rolling_anchor_results") or []), selected
        )
    )
    candidate["runtime_apply_blockers"] = selected["runtime_apply_blockers"]
    candidate["runtime_apply_allowed"] = selected["runtime_apply_allowed"]
    candidate["post_apply_attribution"] = attribution
    candidate["fill_quality"] = candidate.get("modeled_fill_participation")
    candidate["missed_upside"] = candidate.get("missed_upside_rate")
    fill_participation = _safe_float(candidate.get("modeled_fill_participation"), None)
    candidate["modeled_unfilled_quantity_fraction"] = (
        round(1.0 - fill_participation, 4) if fill_participation is not None else None
    )
    return candidate


def _runtime_refresh_evidence(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_candidates = [
        item
        for item in candidates
        if isinstance(item, dict) and _safe_bool(item.get("runtime_apply_allowed"))
    ]
    evidence_candidates = runtime_candidates or [
        item for item in candidates if isinstance(item, dict)
    ]
    real_outcome_joined_sample = sum(
        _safe_int(item.get("real_outcome_joined_sample"), 0)
        for item in evidence_candidates
    )
    additional_mfe_mae_joined_sample = sum(
        _safe_int(item.get("additional_mfe_mae_joined_sample"), 0)
        for item in evidence_candidates
    )
    paired_count = sum(
        _safe_int(item.get("paired_economic_sample_count"), 0)
        for item in evidence_candidates
    )
    source_dates = sorted(
        {
            str(day)
            for item in evidence_candidates
            for day in item.get("economic_source_dates") or []
        }
    )
    observed_price_sample = sum(
        _safe_int(item.get("price_observation_joined_sample"), 0)
        for item in evidence_candidates
    )
    price_join_gap_count = sum(
        _safe_int(item.get("price_observation_join_gap_count"), 0)
        for item in evidence_candidates
    )
    price_join_denominator = observed_price_sample + price_join_gap_count
    price_join_coverage = (
        observed_price_sample / price_join_denominator
        if price_join_denominator > 0
        else 0.0
    )
    delta_pnl = sum(
        _safe_int(item.get("economic_delta_pnl_krw"), 0) for item in evidence_candidates
    )
    base_notional = sum(
        _safe_int(item.get("economic_base_notional_krw"), 0)
        for item in evidence_candidates
    )
    weighted_ev = (delta_pnl / base_notional) * 100.0 if base_notional > 0 else None
    fill_weight = sum(
        (_safe_float(item.get("modeled_fill_participation"), 0.0) or 0.0)
        * _safe_int(item.get("paired_economic_sample_count"), 0)
        for item in evidence_candidates
    )
    fill_participation = fill_weight / paired_count if paired_count > 0 else None
    downside_values = [
        _safe_float(item.get("downside_p10_profit_rate"), None)
        for item in evidence_candidates
    ]
    downside_values = [item for item in downside_values if item is not None]
    downside_p10 = min(downside_values) if downside_values else None
    blockers: list[str] = []
    if runtime_candidates:
        blockers = []
    else:
        for item in evidence_candidates:
            for blocker in item.get("runtime_apply_blockers") or []:
                if blocker not in blockers:
                    blockers.append(str(blocker))
        if not candidates:
            blockers = [
                "real_outcome_sample_floor",
                "additional_mfe_mae_sample_floor",
                "price_join_coverage_floor",
                "paired_economic_sample_floor",
                "economic_source_date_floor",
            ]
    return {
        "economic_gate_version": ECONOMIC_GATE_VERSION,
        "paired_economic_sample_count": paired_count,
        "economic_source_dates": source_dates,
        "economic_source_date_count": len(source_dates),
        "runtime_policy_refresh_allowed": bool(runtime_candidates) and not blockers,
        "eligible_runtime_bucket_count": len(runtime_candidates),
        "real_outcome_joined_sample": real_outcome_joined_sample,
        "real_outcome_sample_floor": RUNTIME_REFRESH_REAL_OUTCOME_FLOOR,
        "additional_mfe_mae_joined_sample": additional_mfe_mae_joined_sample,
        "additional_mfe_mae_sample_floor": RUNTIME_REFRESH_MFE_MAE_FLOOR,
        "price_observation_joined_sample": observed_price_sample,
        "price_observation_join_gap_count": price_join_gap_count,
        "price_join_coverage": round(price_join_coverage, 4),
        "price_join_coverage_floor": RUNTIME_REFRESH_PRICE_JOIN_COVERAGE_FLOOR,
        "source_quality_adjusted_ev_pct": (
            round(weighted_ev, 6) if weighted_ev is not None else None
        ),
        "minimum_cost_adjusted_ev_pct": RUNTIME_REFRESH_MIN_COST_ADJUSTED_EV_PCT,
        "modeled_fill_participation": (
            round(fill_participation, 4) if fill_participation is not None else None
        ),
        "modeled_fill_participation_floor": (RUNTIME_REFRESH_FILL_PARTICIPATION_FLOOR),
        "downside_p10_profit_rate": (
            round(downside_p10, 4) if downside_p10 is not None else None
        ),
        "downside_p10_delta_floor_pct": (RUNTIME_REFRESH_DOWNSIDE_P10_DELTA_FLOOR_PCT),
        "blockers": blockers,
        "insufficient_evidence_action": (
            "block_refresh_until_validated_prior_policy_available"
        ),
    }


def runtime_refresh_contract_error(evidence: Any) -> str:
    if not isinstance(evidence, dict):
        return "runtime_refresh_evidence_missing"
    if evidence.get("economic_gate_version") != ECONOMIC_GATE_VERSION:
        return "runtime_refresh_economic_gate_version_mismatch"
    if evidence.get("runtime_policy_refresh_allowed") is not True:
        return "runtime_refresh_evidence_not_allowed"
    if evidence.get("blockers"):
        return "runtime_refresh_evidence_blocked"
    if _safe_int(evidence.get("eligible_runtime_bucket_count"), 0) < 1:
        return "runtime_refresh_bucket_missing"
    paired_count = _safe_int(evidence.get("paired_economic_sample_count"), 0)
    if paired_count < RUNTIME_REFRESH_REAL_OUTCOME_FLOOR:
        return "runtime_refresh_paired_economic_floor"
    dates = evidence.get("economic_source_dates")
    if (
        not isinstance(dates, list)
        or len(set(map(str, dates))) < RUNTIME_REFRESH_SOURCE_DATE_FLOOR
        or _safe_int(evidence.get("economic_source_date_count"), 0)
        != len(set(map(str, dates)))
        or any(not is_date_allowed(str(day), clean_baseline_policy()) for day in dates)
    ):
        return "runtime_refresh_source_date_floor"
    if (
        _safe_int(evidence.get("real_outcome_joined_sample"), 0)
        < RUNTIME_REFRESH_REAL_OUTCOME_FLOOR
    ):
        return "runtime_refresh_real_outcome_floor"
    if (
        _safe_int(evidence.get("additional_mfe_mae_joined_sample"), 0)
        < RUNTIME_REFRESH_MFE_MAE_FLOOR
    ):
        return "runtime_refresh_mfe_mae_floor"
    if (
        _safe_float(evidence.get("price_join_coverage"), 0.0) or 0.0
    ) < RUNTIME_REFRESH_PRICE_JOIN_COVERAGE_FLOOR:
        return "runtime_refresh_price_coverage_floor"
    if (
        _safe_float(evidence.get("source_quality_adjusted_ev_pct"), None) is None
        or (_safe_float(evidence.get("source_quality_adjusted_ev_pct"), 0.0) or 0.0)
        < RUNTIME_REFRESH_MIN_COST_ADJUSTED_EV_PCT
    ):
        return "runtime_refresh_cost_adjusted_ev_floor"
    if (
        _safe_float(evidence.get("modeled_fill_participation"), 0.0) or 0.0
    ) < RUNTIME_REFRESH_FILL_PARTICIPATION_FLOOR:
        return "runtime_refresh_fill_participation_floor"
    downside = _safe_float(evidence.get("downside_p10_profit_rate"), None)
    if downside is None or downside < RUNTIME_REFRESH_DOWNSIDE_P10_DELTA_FLOOR_PCT:
        return "runtime_refresh_downside_p10_floor"
    return ""


def _build_policy(
    target_date: str,
    candidates: list[dict[str, Any]],
    *,
    refresh_evidence: dict[str, Any],
) -> dict[str, Any]:
    runtime_candidates = [
        item for item in candidates if _safe_bool(item.get("runtime_apply_allowed"))
    ]
    runtime_allowed = bool(runtime_candidates) and not runtime_refresh_contract_error(
        refresh_evidence
    )
    default_bucket = {
        "context_bucket": "default",
        "leg_count": 2,
        "price_offsets_ticks": [0, 1],
        "price_offsets_pct": [0.0, 0.3],
        "qty_weights": [0.5, 0.5],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "policy_mode": POLICY_MODE_BOUNDED_EQUAL_BASELINE,
        "split_variant_id": BASELINE_SPLIT_VARIANT_ID,
        "selection_reason": "unseen_context_fail_closed_to_unsplit_base_order",
        "runtime_apply_allowed": False,
        "runtime_refresh_evidence": refresh_evidence,
    }
    policy_version = f"{RUNTIME_FAMILY}:{target_date}:{_policy_hash(runtime_candidates, default_bucket=default_bucket)}"
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_version": policy_version,
        "source_report": str(report_paths(target_date)[0]),
        "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "runtime_apply_allowed": runtime_allowed,
        "economic_gate_version": ECONOMIC_GATE_VERSION,
        "runtime_refresh_evidence": refresh_evidence,
        "scope": {
            "stage": "scale_in",
            "add_type": "AVG_DOWN",
            "excluded_add_types": ["PYRAMID"],
            "quantity_authority": "describe_dynamic_scale_in_qty",
            "forbidden_uses": "quantity_expansion|cap_release|broker_guard_bypass|stale_quote_bypass|provider_route_change|bot_restart",
        },
        "default_bucket": default_bucket,
        "buckets": {str(item["context_bucket"]): item for item in runtime_candidates},
    }


def _policy_hash(
    candidates: list[dict[str, Any]], *, default_bucket: dict[str, Any] | None = None
) -> str:
    raw = json.dumps(
        {"candidates": candidates, "default_bucket": default_bucket or {}},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def build_report(target_date: str) -> dict[str, Any]:
    source_quality = _source_quality_summary(target_date)
    events, input_summary = _iter_input_events(target_date)
    historical_anchor_results, rolling_summary = _load_rolling_anchor_results(
        target_date
    )
    avg_down_rows: list[dict[str, Any]] = []
    skipped = Counter()
    enriched_events = _enrich_avg_down_context(events)
    for event in enriched_events:
        stage = str(event.get("stage") or "")
        add_type = (
            str(event.get("add_type") or event.get("scale_in_type") or "")
            .strip()
            .upper()
        )
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
    # Choose the canonical submitted attempt before assigning a context bucket;
    # leg/receipt mirrors may carry different diagnostic reasons.
    canonical_rows = _unique_attempt_anchors(avg_down_rows)
    canonical_rows.extend(
        row
        for row in avg_down_rows
        if not _safe_bool(row.get("actual_order_submitted"))
    )
    for row in canonical_rows:
        by_bucket.setdefault(_context_bucket(row), []).append(row)
    historical_by_bucket: dict[str, list[dict[str, Any]]] = {}
    for row in historical_anchor_results:
        historical_by_bucket.setdefault(
            str(
                row.get("context_bucket") or "unknown_strategy:generic_avg_down:normal"
            ),
            [],
        ).append(row)
    candidate_grid: list[dict[str, Any]] = []
    diagnostic_candidates: list[dict[str, Any]] = []
    selected_candidates: list[dict[str, Any]] = []
    daily_attempt_outcomes_by_id: dict[str, dict[str, Any]] = {}
    buckets = sorted(set(by_bucket) | set(historical_by_bucket))
    for bucket in buckets:
        rows = by_bucket.get(bucket, [])
        candidate = _candidate_for_bucket(
            bucket,
            rows,
            events,
            historical_anchor_results=historical_by_bucket.get(bucket, []),
        )
        for item in candidate.get("daily_anchor_results") or []:
            attempt_id = str(item.get("attempt_id") or "")
            if attempt_id:
                daily_attempt_outcomes_by_id[attempt_id] = item
        candidate_grid.append(candidate)
        three_leg_candidate = _three_leg_candidate(
            bucket,
            {key: value for key, value in candidate.items() if key != "anchor_samples"},
        )
        selected = candidate
        if three_leg_candidate:
            candidate_grid.append(three_leg_candidate)
            if _safe_bool(three_leg_candidate.get("diagnostic_only")):
                diagnostic_candidates.append(three_leg_candidate)
        selected_candidates.append(selected)
    if not candidate_grid:
        empty_candidate = _candidate_for_bucket("default", [], events)
        candidate_grid = [empty_candidate]
        selected_candidates = [empty_candidate]
    candidates: list[dict[str, Any]] = []
    for item in selected_candidates:
        candidate = dict(item)
        candidate.pop("daily_anchor_results", None)
        candidate.pop("rolling_anchor_results", None)
        if source_quality.get("tuning_input_allowed") is False:
            candidate["runtime_apply_allowed"] = False
            blockers = list(candidate.get("runtime_apply_blockers") or [])
            if "source_quality_blocked" not in blockers:
                blockers.insert(0, "source_quality_blocked")
            candidate["runtime_apply_blockers"] = blockers
        candidates.append(candidate)
    for item in candidate_grid:
        item.pop("daily_anchor_results", None)
        item.pop("rolling_anchor_results", None)
    refresh_evidence = _runtime_refresh_evidence(candidates)
    policy = _build_policy(
        target_date,
        candidates,
        refresh_evidence=refresh_evidence,
    )
    runtime_policy_refresh_allowed = bool(policy.get("runtime_apply_allowed"))
    policy_file = policy_path(target_date)
    counterfactual_selected_count = sum(
        1
        for item in candidates
        if isinstance(item, dict)
        and item.get("policy_mode") == POLICY_MODE_COUNTERFACTUAL_TICK_BAND
    )
    baseline_fallback_count = sum(
        1
        for item in candidates
        if isinstance(item, dict)
        and item.get("policy_mode") == POLICY_MODE_BOUNDED_EQUAL_BASELINE
    )
    market_qty_split_only_count = sum(
        1
        for item in candidates
        if isinstance(item, dict)
        and item.get("policy_mode") == POLICY_MODE_MARKET_QTY_SPLIT_ONLY
    )
    price_observation_join_gap_count = sum(
        _safe_int(item.get("price_observation_join_gap_count"), 0)
        for item in candidates
        if isinstance(item, dict)
    )
    base_price_reconstruction_gap_count = sum(
        _safe_int(item.get("base_price_reconstruction_gap_count"), 0)
        for item in candidates
        if isinstance(item, dict)
    )
    daily_attempt_outcomes = list(daily_attempt_outcomes_by_id.values())
    rolling_unique_attempt_count = sum(
        _safe_int(item.get("unique_attempt_count"), 0) for item in candidates
    )
    rolling_eligible_attempt_count = sum(
        _safe_int(item.get("eligible_runtime_attempt_count"), 0) for item in candidates
    )
    rolling_summary.update(
        {
            "target_date": target_date,
            "current_source_date_included": bool(daily_attempt_outcomes),
            "current_unique_attempt_count": len(daily_attempt_outcomes),
            "rolling_unique_attempt_count": rolling_unique_attempt_count,
            "rolling_eligible_runtime_attempt_count": rolling_eligible_attempt_count,
            "rolling_real_outcome_joined_sample": _safe_int(
                refresh_evidence.get("real_outcome_joined_sample"), 0
            ),
            "rolling_additional_mfe_mae_joined_sample": _safe_int(
                refresh_evidence.get("additional_mfe_mae_joined_sample"), 0
            ),
        }
    )
    input_summary.update(
        {
            "avg_down_observation_count": len(avg_down_rows),
            "unattributed_split_attempt_count": sum(
                _safe_int(
                    item["post_apply_attribution"].get(
                        "unattributed_split_attempt_count"
                    ),
                    0,
                )
                for item in candidates
            ),
            "daily_unique_attempt_count": len(daily_attempt_outcomes),
            "rolling_unique_attempt_count": rolling_unique_attempt_count,
            "rolling_eligible_runtime_attempt_count": rolling_eligible_attempt_count,
            "bucket_count": len(by_bucket),
            "skipped_stage_counts": dict(skipped),
            "excluded_source_quality_event_count": 0,
            "counterfactual_selected_count": counterfactual_selected_count,
            "baseline_fallback_count": baseline_fallback_count,
            "price_observation_join_gap_count": price_observation_join_gap_count,
            "base_price_reconstruction_gap_count": base_price_reconstruction_gap_count,
            "market_qty_split_only_count": market_qty_split_only_count,
            "diagnostic_three_leg_candidate_count": len(diagnostic_candidates),
            "runtime_three_leg_candidate_count": sum(
                1
                for item in candidates
                if _safe_int(item.get("leg_count"), 0) == 3
                and _safe_bool(item.get("runtime_apply_allowed"))
            ),
            "counterfactual_window_sec": COUNTERFACTUAL_WINDOW_SEC,
            "anchor_reconstruct_window_sec": ANCHOR_RECONSTRUCT_WINDOW_SEC,
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "split_domain_ownership": {
            "stage": "scale_in",
            "add_type": "AVG_DOWN",
            "evidence_owner": "scale_in_split_order_plan",
            "policy_owner": "scale_in_split_order_plan",
            "shared_execution_math": "src.trading.order.split_execution_math",
            "shared_execution_math_authority": "pure_qty_tick_and_existing_ttl_math_only",
            "initial_entry_evidence_or_policy_accepted": False,
            "pyramid_evidence_or_policy_accepted": False,
            "independent_machine_evidence_or_policy_accepted": False,
        },
        "metric_contract": {
            "metric_role": "cost_adjusted_execution_shape_calibration",
            "decision_authority": "next_preopen_bounded_scale_in_split_policy",
            "window_policy": "rolling_20_report_dates_unique_attempt_with_daily_increment",
            "sample_floor": {
                "real_exact_outcome": RUNTIME_REFRESH_REAL_OUTCOME_FLOOR,
                "additional_mfe_mae": RUNTIME_REFRESH_MFE_MAE_FLOOR,
                "paired_economic": RUNTIME_REFRESH_REAL_OUTCOME_FLOOR,
                "economic_source_dates": RUNTIME_REFRESH_SOURCE_DATE_FLOOR,
                "runtime_refresh_real_outcome": RUNTIME_REFRESH_REAL_OUTCOME_FLOOR,
                "runtime_refresh_additional_mfe_mae": RUNTIME_REFRESH_MFE_MAE_FLOOR,
            },
            "runtime_refresh_price_join_coverage_floor": (
                RUNTIME_REFRESH_PRICE_JOIN_COVERAGE_FLOOR
            ),
            "runtime_refresh_minimum_cost_adjusted_ev_pct": (
                RUNTIME_REFRESH_MIN_COST_ADJUSTED_EV_PCT
            ),
            "runtime_refresh_fill_participation_floor": (
                RUNTIME_REFRESH_FILL_PARTICIPATION_FLOOR
            ),
            "runtime_refresh_downside_p10_delta_floor_pct": (
                RUNTIME_REFRESH_DOWNSIDE_P10_DELTA_FLOOR_PCT
            ),
            "three_leg_decision_authority": "diagnostic_only",
            "market_split_decision_authority": "not_applicable",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "observation_source_quality_audit_tuning_input_allowed",
            "entry_probe_exclusion_contract": (
                "One-share entry probes and residual entry legs are not scale-in samples. Only AVG_DOWN "
                "additional-buy observations owned by scale_in_split_order_plan may update this plan."
            ),
            "forbidden_uses": [
                "quantity_expansion",
                "cap_release",
                "broker_guard_bypass",
                "stale_quote_bypass",
                "provider_route_change",
                "bot_restart",
                "pyramid_scale_in",
                "runtime_policy_refresh_without_real_outcome_and_mfe_mae",
                "daily_event_row_count_as_attempt_count",
                "non_positive_cost_adjusted_ev_runtime_apply",
            ],
        },
        "source_quality": source_quality,
        "input_summary": input_summary,
        "rolling_summary": rolling_summary,
        "daily_attempt_outcomes": daily_attempt_outcomes,
        "candidate_grid": candidate_grid,
        "recommended_policy": {
            "runtime_apply_allowed": runtime_policy_refresh_allowed,
            "runtime_apply_scope": "qty_preserving_execution_shape_refresh",
            "runtime_refresh_evidence": refresh_evidence,
            "post_apply_attribution": {
                "required": True,
                "buckets": [
                    {
                        "context_bucket": item["context_bucket"],
                        **item["post_apply_attribution"],
                    }
                    for item in candidates
                ],
                "metrics": [
                    "source_quality_adjusted_ev_pct",
                    "fill_rate_delta",
                    "cancel_rate_delta",
                    "additional_mfe_pct_delta",
                    "additional_mae_pct_delta",
                    "missed_upside_rate",
                ],
            },
            "rollback_guard": {
                "action": "disable_candidate_require_validated_prior_policy",
                "triggers": [
                    "source_quality_adjusted_ev_pct_non_positive",
                    "modeled_fill_participation_below_floor",
                    "downside_p10_delta_below_floor",
                    "post_apply_negative_economic_evidence",
                ],
                "diagnostic_only_not_automatic_rollback": [
                    "cancel_rate_delta",
                    "additional_mfe_pct_delta",
                    "additional_mae_pct_delta",
                ],
            },
            "policy_file": str(policy_file),
            "policy_version": policy.get("policy_version"),
            "candidates": candidates,
            "runtime_candidate_count": sum(
                1
                for item in candidates
                if _safe_bool(item.get("runtime_apply_allowed"))
            ),
            "diagnostic_candidates": diagnostic_candidates,
        },
        "policy_artifact": policy,
    }


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    recommended = (
        report.get("recommended_policy")
        if isinstance(report.get("recommended_policy"), dict)
        else {}
    )
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
    policy = (
        report.get("policy_artifact")
        if isinstance(report.get("policy_artifact"), dict)
        else {}
    )
    report_to_write = {
        key: value for key, value in report.items() if key != "policy_artifact"
    }
    _write_json(json_path, report_to_write)
    _write_json(policy_file, policy)
    _write_markdown(md_path, report_to_write)
    return json_path, md_path, policy_file


def _load_policy_from_env(
    policy_file: str | None = None,
) -> tuple[dict[str, Any] | None, str]:
    enabled = os.environ.get("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED")
    if not _safe_bool(enabled):
        return None, "policy_disabled"
    path_value = policy_file or os.environ.get(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE"
    )
    if not path_value:
        return None, "policy_file_missing"
    path = Path(path_value)
    if not path.exists():
        return None, "policy_file_not_found"
    payload = _load_json(path)
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        return None, "policy_schema_mismatch"
    expected_version = str(
        os.environ.get("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION") or ""
    ).strip()
    if (
        expected_version
        and str(payload.get("policy_version") or "") != expected_version
    ):
        return None, "policy_version_mismatch"
    if not _safe_bool(payload.get("runtime_apply_allowed")):
        return None, "runtime_apply_not_allowed"
    refresh_evidence = payload.get("runtime_refresh_evidence")
    refresh_error = runtime_refresh_contract_error(refresh_evidence)
    if refresh_error:
        return None, refresh_error
    policy_error = policy_runtime_contract_error(payload)
    if policy_error:
        return None, policy_error
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
    generated_at = generated_at.astimezone(now.tzinfo)
    if generated_at > now:
        return True
    return (
        count_krx_trading_days(generated_at.date(), now.date())
        > MAX_POLICY_AGE_KRX_TRADING_DAYS
    )


def _bucket_runtime_contract_error(bucket_policy: Any) -> str:
    if not isinstance(bucket_policy, dict):
        return "context_bucket_not_runtime_approved"
    if not _safe_bool(bucket_policy.get("runtime_apply_allowed")):
        return "context_bucket_runtime_not_allowed"
    mode = str(bucket_policy.get("policy_mode") or "")
    variant = str(bucket_policy.get("split_variant_id") or "")
    allowed_variant_modes = {
        BASELINE_SPLIT_VARIANT_ID: POLICY_MODE_BOUNDED_EQUAL_BASELINE,
        COUNTERFACTUAL_70_30_VARIANT_ID: POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
        COUNTERFACTUAL_50_50_VARIANT_ID: POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
        COUNTERFACTUAL_60_40_VARIANT_ID: POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
    }
    if allowed_variant_modes.get(variant) != mode:
        return "context_bucket_policy_mode_invalid"
    leg_count = _safe_int(bucket_policy.get("leg_count"), 0)
    if leg_count != 2:
        return "context_bucket_leg_count_invalid"
    raw_weights = bucket_policy.get("qty_weights")
    if not isinstance(raw_weights, list) or len(raw_weights) != leg_count:
        return "context_bucket_qty_weights_invalid"
    weights = [_safe_float(item, None) for item in raw_weights]
    if any(item is None or item <= 0.0 or item >= 1.0 for item in weights):
        return "context_bucket_qty_weights_invalid"
    if abs(sum(item for item in weights if item is not None) - 1.0) > 1e-6:
        return "context_bucket_qty_weights_invalid"
    raw_pct_offsets = bucket_policy.get("price_offsets_pct")
    raw_tick_offsets = bucket_policy.get("price_offsets_ticks")
    expected_shapes: dict[str, tuple[int, Any, Any, list[float]]] = {
        BASELINE_SPLIT_VARIANT_ID: (2, [0, 1], [0.0, 0.3], [0.5, 0.5]),
        COUNTERFACTUAL_70_30_VARIANT_ID: (2, [0, 1], [0.0, 0.3], [0.7, 0.3]),
        COUNTERFACTUAL_50_50_VARIANT_ID: (2, [0, 1], [0.0, 0.3], [0.5, 0.5]),
        COUNTERFACTUAL_60_40_VARIANT_ID: (2, [0, 2], [0.0, 0.8], [0.6, 0.4]),
    }
    expected_leg_count, expected_ticks, expected_pct, expected_weights = (
        expected_shapes[variant]
    )
    if leg_count != expected_leg_count or any(
        abs((item or 0.0) - expected) > 1e-6
        for item, expected in zip(weights, expected_weights)
    ):
        return "context_bucket_variant_shape_mismatch"
    if not isinstance(raw_pct_offsets, list) or len(raw_pct_offsets) != leg_count:
        return "context_bucket_price_offsets_invalid"
    pct_offsets = [_safe_float(item, None) for item in raw_pct_offsets]
    if any(item is None or item < 0.0 or item > 1.5 for item in pct_offsets):
        return "context_bucket_price_offsets_invalid"
    finite_offsets = [item for item in pct_offsets if item is not None]
    if (
        not finite_offsets
        or finite_offsets[0] != 0.0
        or finite_offsets != sorted(finite_offsets)
    ):
        return "context_bucket_price_offsets_invalid"
    if not isinstance(raw_tick_offsets, list) or len(raw_tick_offsets) != leg_count:
        return "context_bucket_tick_offsets_invalid"
    tick_offsets = [_safe_int(item, -1) for item in raw_tick_offsets]
    if any(item < 0 or item > 2 for item in tick_offsets):
        return "context_bucket_tick_offsets_invalid"
    if tick_offsets != expected_ticks or any(
        abs((item or 0.0) - expected) > 1e-6
        for item, expected in zip(pct_offsets, expected_pct)
    ):
        return "context_bucket_variant_shape_mismatch"
    return ""


def policy_runtime_contract_error(policy: Any) -> str:
    if not isinstance(policy, dict):
        return "scale_in_split_policy_missing"
    refresh_error = runtime_refresh_contract_error(
        policy.get("runtime_refresh_evidence")
    )
    if refresh_error:
        return refresh_error
    default_bucket = policy.get("default_bucket")
    if isinstance(default_bucket, dict) and _safe_bool(
        default_bucket.get("runtime_apply_allowed")
    ):
        return "default_context_runtime_apply_forbidden"
    buckets = policy.get("buckets")
    if not isinstance(buckets, dict) or not buckets:
        return "runtime_context_bucket_missing"
    for context_bucket, bucket_policy in buckets.items():
        error = _bucket_runtime_contract_error(bucket_policy)
        if error:
            return error
        if str((bucket_policy or {}).get("context_bucket") or "") != str(
            context_bucket
        ):
            return "context_bucket_identity_mismatch"
    policy_version = str(policy.get("policy_version") or "")
    if policy_version.startswith(f"{RUNTIME_FAMILY}:"):
        version_parts = policy_version.rsplit(":", 1)
        expected_hash = _policy_hash(
            list(buckets.values()),
            default_bucket=(default_bucket if isinstance(default_bucket, dict) else {}),
        )
        if len(version_parts) != 2 or version_parts[-1] != expected_hash:
            return "policy_content_hash_mismatch"
    return ""


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
    add_type = (
        str(action.get("add_type") or base_order.get("add_type") or "").strip().upper()
    )
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
    if _safe_bool(quote_fields.get("stale_quote_submit_block")) or _safe_bool(
        quote_fields.get("quote_stale_at_submit")
    ):
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
    market_order = base_order_price <= 0 and order_type_code in {
        "3",
        "03",
        "6",
        "06",
        "16",
    }
    if market_order:
        fields["scale_in_split_order_skip_reason"] = "market_split_not_applicable"
        return [base_order], fields
    if base_price <= 0:
        fields["scale_in_split_order_skip_reason"] = "invalid_base_price"
        return [base_order], fields
    bucket = _context_bucket({**stock, **action, **price_resolution})
    bucket_policy = (policy.get("buckets") or {}).get(bucket)
    bucket_contract_error = _bucket_runtime_contract_error(bucket_policy)
    if bucket_contract_error:
        fields["scale_in_split_order_skip_reason"] = bucket_contract_error
        fields["scale_in_split_order_bucket"] = bucket
        return [base_order], fields
    assert isinstance(bucket_policy, dict)
    requested_legs = max(1, _safe_int(bucket_policy.get("leg_count"), 2))
    desired_legs = min(requested_legs, MAX_SCALE_IN_SPLIT_LEGS, qty)
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
    raw_pct_offsets = bucket_policy.get("price_offsets_pct")
    pct_offsets = (
        [max(0.0, _safe_float(item, 0.0) or 0.0) for item in raw_pct_offsets][
            :desired_legs
        ]
        if isinstance(raw_pct_offsets, list)
        else []
    )
    while pct_offsets and len(pct_offsets) < desired_legs:
        pct_offsets.append(pct_offsets[-1])
    raw_weights = bucket_policy.get("qty_weights")
    qty_weights = (
        [_safe_float(item, 0.0) or 0.0 for item in raw_weights]
        if isinstance(raw_weights, list)
        else []
    )
    first_weight = _safe_float(bucket_policy.get("qty_weight_min"), 0.5) or 0.5
    quantities = (
        _split_qty_by_weights(qty, desired_legs, qty_weights)
        if qty_weights
        else _split_qty(qty, desired_legs, first_weight)
    )
    tick = _tick_size(base_price) if base_price > 0 else 1
    policy_variant_id = str(bucket_policy.get("split_variant_id") or "").strip()
    leg_count_clipped = desired_legs != requested_legs
    execution_variant_id = policy_variant_id
    if leg_count_clipped:
        execution_variant_id = f"{execution_variant_id}__qty_clipped_legs{desired_legs}"
    split_orders = []
    for idx, leg_qty in enumerate(quantities):
        price = (
            0
            if market_order
            else (
                _pct_price_offset(base_price, pct_offsets[idx])
                if pct_offsets
                else clamp_price_to_tick(max(1, base_price - (tick * offsets[idx])))
            )
        )
        split_orders.append(
            {
                **base_order,
                "qty": leg_qty,
                "price": price,
                "scale_in_split_order_leg_index": idx + 1,
                "scale_in_split_order_policy_version": policy.get("policy_version"),
                "scale_in_split_order_policy_mode": bucket_policy.get("policy_mode"),
                "scale_in_split_order_variant_id": execution_variant_id,
                "scale_in_split_order_policy_variant_id": policy_variant_id,
                "scale_in_split_order_policy_requested_leg_count": requested_legs,
                "scale_in_split_order_max_leg_count": MAX_SCALE_IN_SPLIT_LEGS,
                "scale_in_split_order_leg_count_clipped": leg_count_clipped,
                "scale_in_split_order_bucket": bucket,
                "scale_in_split_order_runtime_default_policy_applied": False,
                "scale_in_split_order_market_order_applied": market_order,
                "scale_in_split_order_price_offsets_ticks": (
                    "market"
                    if market_order
                    else ",".join(str(item) for item in offsets)
                ),
                "scale_in_split_order_price_offsets_pct": (
                    "market"
                    if market_order
                    else (
                        ",".join(str(item) for item in pct_offsets)
                        if pct_offsets
                        else ""
                    )
                ),
                "scale_in_split_order_price_offset_ticks": (
                    "market" if market_order else offsets[idx]
                ),
                "scale_in_split_order_price_offset_pct": (
                    "market"
                    if market_order
                    else pct_offsets[idx] if pct_offsets else ""
                ),
                "split_price_offset_ticks": "market" if market_order else offsets[idx],
                "split_price_offset_pct": (
                    "market"
                    if market_order
                    else pct_offsets[idx] if pct_offsets else ""
                ),
                "split_leg_role": "primary" if idx == 0 else "passive",
                "scale_in_split_order_qty_weight_min": first_weight,
                "scale_in_split_order_qty_weight_max": _safe_float(
                    bucket_policy.get("qty_weight_max"), first_weight
                ),
                "scale_in_split_order_qty_weights": (
                    ",".join(str(item) for item in qty_weights) if qty_weights else ""
                ),
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
            "scale_in_split_order_variant_id": execution_variant_id,
            "scale_in_split_order_policy_variant_id": policy_variant_id,
            "scale_in_split_order_policy_requested_leg_count": requested_legs,
            "scale_in_split_order_max_leg_count": MAX_SCALE_IN_SPLIT_LEGS,
            "scale_in_split_order_leg_count_clipped": leg_count_clipped,
            "scale_in_split_order_runtime_default_policy_applied": False,
            "scale_in_split_order_policy_file": policy_file
            or os.environ.get("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE"),
            "scale_in_split_order_leg_count": len(split_orders),
            "scale_in_split_order_split_qty": qty,
            "scale_in_split_order_market_order_applied": market_order,
            "scale_in_split_order_price_offsets_ticks": (
                "market" if market_order else ",".join(str(item) for item in offsets)
            ),
            "scale_in_split_order_price_offsets_pct": (
                "market"
                if market_order
                else ",".join(str(item) for item in pct_offsets) if pct_offsets else ""
            ),
            "scale_in_split_order_qty_weight_min": first_weight,
            "scale_in_split_order_qty_weight_max": _safe_float(
                bucket_policy.get("qty_weight_max"), first_weight
            ),
            "scale_in_split_order_qty_weights": (
                ",".join(str(item) for item in qty_weights) if qty_weights else ""
            ),
        }
    )
    return split_orders, fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        "--target-date",
        dest="target_date",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date)
    if not args.no_write:
        write_outputs(args.target_date, report)
    else:
        print(
            json.dumps(
                {
                    key: value
                    for key, value in report.items()
                    if key != "policy_artifact"
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
