"""Sim-only scalp overnight decision runner and source artifact builder."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.sniper_config import CONF
from src.engine.trade_profit import calculate_net_profit_rate, calculate_net_realized_pnl
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import read_jsonl
from src.utils.pipeline_event_logger import emit_pipeline_event


STATE_PATH = DATA_DIR / "runtime" / "scalp_live_simulator_state.json"
REPORT_DIR = DATA_DIR / "report" / "scalp_sim_overnight"
SIM_BOOK = "scalp_ai_buy_all"
SCHEMA_VERSION = 1
OVERNIGHT_SCHEMA = "overnight_v1"
DECISION_AUTHORITY = "sim_observation_only"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        numeric = float(str(value).replace("%", "").replace("+", "").strip())
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _boolish_true(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _boolish_false(value: Any) -> bool:
    return str(value).strip().lower() in {"", "0", "false", "no", "none", "null"}


def _load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "simulation_book": SIM_BOOK, "active_positions": []}
    except Exception:
        return {"schema_version": 1, "simulation_book": SIM_BOOK, "active_positions": []}
    return payload if isinstance(payload, dict) else {"schema_version": 1, "simulation_book": SIM_BOOK, "active_positions": []}


def _write_state(payload: dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = _now_iso()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _is_active_sim_position(row: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    if str(row.get("status") or "").upper() != "HOLDING":
        return False
    if str(row.get("strategy") or "").upper() != "SCALPING":
        return False
    if str(row.get("simulation_book") or "") != SIM_BOOK:
        return False
    if not _boolish_true(row.get("scalp_live_simulator")):
        return False
    if not _boolish_false(row.get("actual_order_submitted")):
        return False
    return bool(str(row.get("sim_record_id") or "").strip())


def _holding_sample_price(row: dict[str, Any]) -> int | None:
    samples = row.get("holding_price_samples")
    if isinstance(samples, list):
        for sample in reversed(samples):
            if not isinstance(sample, dict):
                continue
            price = _safe_int(sample.get("price"), 0)
            if price > 0:
                return price
    return None


def _price_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    sample_price = _holding_sample_price(row)
    buy_price = _safe_int(row.get("buy_price"), 0)
    current_price = sample_price or _safe_int(row.get("curr_price"), 0) or buy_price
    source = "holding_price_samples_last" if sample_price else ("curr_price" if row.get("curr_price") else "buy_price_fallback")
    return {
        "best_bid": None,
        "best_ask": None,
        "current_price": current_price,
        "price_source": source,
        "price_fallback_used": source == "buy_price_fallback",
    }


def _held_sec(row: dict[str, Any]) -> int:
    for key in ("held_sec", "last_ai_held_sec"):
        value = _safe_int(row.get(key), 0)
        if value > 0:
            return value
    buy_time = _safe_float(row.get("buy_time"), None)
    if buy_time and buy_time > 0:
        return max(0, int(time.time() - buy_time))
    return 0


def _profit_pct(row: dict[str, Any], current_price: int) -> float:
    explicit = _safe_float(row.get("last_ai_profit_rate"), None)
    if explicit is not None:
        return round(explicit, 4)
    return calculate_net_profit_rate(row.get("buy_price"), current_price, precision=4)


def _peak_profit_pct(row: dict[str, Any], profit_pct: float) -> float:
    explicit = _safe_float(row.get("last_ai_peak_profit"), None)
    if explicit is not None:
        return round(explicit, 4)
    return round(max(profit_pct, _safe_float(row.get("peak_profit"), profit_pct) or profit_pct), 4)


def _base_event_fields(row: dict[str, Any], target_date: str, price: dict[str, Any]) -> dict[str, Any]:
    return {
        "sim_record_id": row.get("sim_record_id"),
        "sim_parent_record_id": row.get("sim_parent_record_id"),
        "simulation_book": SIM_BOOK,
        "scalp_live_simulator": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": DECISION_AUTHORITY,
        "overnight_schema": OVERNIGHT_SCHEMA,
        "target_date": target_date,
        "current_price": price.get("current_price"),
        "best_bid": price.get("best_bid"),
        "best_ask": price.get("best_ask"),
        "current_price_source": price.get("price_source"),
        "price_fallback_used": price.get("price_fallback_used"),
    }


def _emit(row: dict[str, Any], stage: str, fields: dict[str, Any]) -> None:
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        str(row.get("name") or row.get("stock_name") or row.get("code") or "-"),
        str(row.get("code") or row.get("stock_code") or "")[:6],
        stage,
        fields=fields,
    )


def _build_ai_context(row: dict[str, Any], price: dict[str, Any]) -> dict[str, Any]:
    current_price = _safe_int(price.get("current_price"), 0)
    profit = _profit_pct(row, current_price)
    peak = _peak_profit_pct(row, profit)
    held = _held_sec(row)
    return {
        "position_status": "SIM_HOLDING",
        "strategy": "SCALPING",
        "simulation_book": SIM_BOOK,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": DECISION_AUTHORITY,
        "avg_price": _safe_int(row.get("buy_price"), 0),
        "buy_price": _safe_int(row.get("buy_price"), 0),
        "buy_qty": _safe_int(row.get("buy_qty"), 0),
        "curr_price": current_price,
        "best_bid": price.get("best_bid"),
        "best_ask": price.get("best_ask"),
        "pnl_pct": profit,
        "peak_profit_pct": peak,
        "drawdown_from_peak_pct": round(peak - profit, 4),
        "held_minutes": round(held / 60, 2) if held else 0,
        "held_sec": held,
        "last_holding_ai_action": row.get("last_ai_action"),
        "last_holding_ai_score": row.get("last_ai_score"),
        "last_holding_ai_reason": row.get("last_ai_reason"),
        "entry_ai_action": row.get("original_ai_action") or row.get("ai_action"),
        "entry_ai_score": row.get("original_ai_score") or row.get("ai_score"),
        "source_quality": row.get("last_ai_source_quality") or row.get("source_quality") or "state_snapshot",
        "price_source": price.get("price_source"),
        "order_status_note": "sim-only overnight decision; no broker order is allowed",
    }


def _normalize_decision(decision: dict[str, Any] | None, *, fallback_reason: str = "decision_missing") -> dict[str, Any]:
    if not isinstance(decision, dict):
        fallback_class = _classify_ai_fallback(fallback_reason)
        return {
            "action": "SELL_TODAY",
            "confidence": 0,
            "reason": f"SELL_TODAY fallback: {fallback_reason}",
            "risk_note": fallback_reason,
            "ai_parse_ok": False,
            "ai_result_source": "fallback",
            "ai_fallback": True,
            "ai_fallback_reason": fallback_reason,
            "ai_fallback_class": fallback_class,
        }
    action = str(decision.get("action") or "SELL_TODAY").upper()
    if action not in {"SELL_TODAY", "HOLD_OVERNIGHT"}:
        action = "SELL_TODAY"
    try:
        confidence = int(float(decision.get("confidence") or 0))
    except (TypeError, ValueError):
        confidence = 0
    fallback = (
        decision.get("ai_parse_ok") is False
        or str(decision.get("ai_result_source") or "") in {"fallback", "exception", "engine_disabled", "lock_contention"}
    )
    fallback_reason = str(decision.get("ai_exception_message") or decision.get("reason") or decision.get("risk_note") or "")
    return {
        **decision,
        "action": action,
        "confidence": max(0, min(100, confidence)),
        "reason": str(decision.get("reason") or ""),
        "risk_note": str(decision.get("risk_note") or ""),
        "ai_fallback": bool(fallback),
        "ai_fallback_reason": fallback_reason if fallback else "",
        "ai_fallback_class": _classify_ai_fallback(
            fallback_reason,
            result_source=str(decision.get("ai_result_source") or ""),
        ),
    }


def _classify_ai_fallback(reason: str, *, result_source: str = "") -> str:
    text = f"{reason} {result_source}".lower()
    if "engine_disabled" in text or "비활성화" in text:
        return "engine_disabled"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "lock_contention" in text or "경합" in text:
        return "lock_contention"
    if "parse" in text or "json" in text:
        return "parse_fail"
    if "missing" in text:
        return "missing"
    if text.strip():
        return "exception"
    return "none"


def _call_overnight_ai(ai_engine: Any, row: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    if ai_engine is None:
        return _normalize_decision(None, fallback_reason="ai_engine_missing")
    try:
        decision = ai_engine.evaluate_scalping_overnight_decision(
            str(row.get("name") or row.get("stock_name") or row.get("code") or "-"),
            str(row.get("code") or row.get("stock_code") or "")[:6],
            ctx,
        )
        return _normalize_decision(decision)
    except Exception as exc:
        return _normalize_decision(None, fallback_reason=f"ai_exception:{exc}")


def _mark_hold_overnight(row: dict[str, Any], target_date: str, decision: dict[str, Any]) -> None:
    row["scalp_sim_overnight_status"] = "HOLD_OVERNIGHT"
    row["scalp_sim_overnight_decision_date"] = target_date
    row["scalp_sim_overnight_decision_at"] = _now_iso()
    row["scalp_sim_overnight_ai_confidence"] = decision.get("confidence")
    row["scalp_sim_overnight_reason"] = decision.get("reason")
    row["scalp_sim_overnight_schema"] = OVERNIGHT_SCHEMA


def _complete_sell_today(row: dict[str, Any], price: dict[str, Any], target_date: str, decision: dict[str, Any]) -> dict[str, Any]:
    current_price = _safe_int(price.get("best_bid"), 0) or _safe_int(price.get("current_price"), 0) or _safe_int(row.get("buy_price"), 0)
    qty = _safe_int(row.get("buy_qty"), 0)
    profit = calculate_net_profit_rate(row.get("buy_price"), current_price)
    pnl_krw = calculate_net_realized_pnl(row.get("buy_price"), current_price, qty)
    now_ts = time.time()
    row["status"] = "COMPLETED"
    row["sell_price"] = current_price
    row["sell_qty"] = qty
    row["sell_time"] = now_ts
    row["profit_rate"] = profit
    row["realized_pnl_krw"] = pnl_krw
    row["simulated_sell_order"] = True
    row["actual_order_submitted"] = False
    row["scalp_sim_overnight_status"] = "SELL_TODAY"
    row["scalp_sim_overnight_decision_date"] = target_date
    row["scalp_sim_overnight_decision_at"] = _now_iso()
    row["scalp_sim_overnight_ai_confidence"] = decision.get("confidence")
    row["scalp_sim_overnight_reason"] = decision.get("reason")
    return {
        "assumed_fill_price": current_price,
        "qty": qty,
        "profit_rate": profit,
        "realized_pnl_krw": pnl_krw,
        "sell_time": now_ts,
    }


def run_sim_overnight(
    *,
    target_date: str,
    ai_engine: Any | None = None,
    state_path: Path = STATE_PATH,
    mutate_state: bool = True,
    emit_events: bool = True,
) -> dict[str, Any]:
    payload = _load_state(state_path)
    active = payload.get("active_positions") if isinstance(payload.get("active_positions"), list) else []
    remaining: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    summary_counts: Counter[str] = Counter()

    for row in active:
        if not isinstance(row, dict):
            continue
        if not _is_active_sim_position(row):
            remaining.append(row)
            continue
        sim_record_id = str(row.get("sim_record_id") or "")
        if str(row.get("scalp_sim_overnight_decision_date") or "") == target_date:
            summary_counts["idempotent_skipped"] += 1
            remaining.append(row)
            rows.append(
                {
                    "sim_record_id": sim_record_id,
                    "stock_name": row.get("name") or row.get("stock_name"),
                    "stock_code": row.get("code") or row.get("stock_code"),
                    "decision": "SKIPPED_ALREADY_DECIDED",
                    "status_after": row.get("status"),
                }
            )
            continue

        price = _price_snapshot(row)
        ctx = _build_ai_context(row, price)
        decision = _call_overnight_ai(ai_engine, row, ctx)
        action = str(decision.get("action") or "SELL_TODAY").upper()
        summary_counts["decision_target"] += 1
        if decision.get("ai_fallback"):
            summary_counts["ai_failure_fallback"] += 1
            fallback_class = str(decision.get("ai_fallback_class") or "exception")
            if fallback_class == "timeout":
                summary_counts["ai_timeout_fallback"] += 1
            elif fallback_class == "engine_disabled":
                summary_counts["ai_engine_disabled_fallback"] += 1
            elif fallback_class == "lock_contention":
                summary_counts["ai_lock_contention_fallback"] += 1
            elif fallback_class == "parse_fail":
                summary_counts["ai_parse_fail_fallback"] += 1
            else:
                summary_counts[f"ai_{fallback_class}_fallback"] += 1
            action = "SELL_TODAY"
            decision["action"] = "SELL_TODAY"
        else:
            summary_counts["ai_success"] += 1

        base_fields = _base_event_fields(row, target_date, price)
        decision_fields = {
            **base_fields,
            "ai_action": action,
            "ai_confidence": decision.get("confidence"),
            "ai_reason": decision.get("reason"),
            "ai_risk_note": decision.get("risk_note"),
            "ai_parse_ok": decision.get("ai_parse_ok"),
            "ai_fallback": decision.get("ai_fallback"),
            "ai_fallback_class": decision.get("ai_fallback_class"),
            "ai_fallback_reason": decision.get("ai_fallback_reason"),
            "ai_result_source": decision.get("ai_result_source"),
            "openai_endpoint_name": decision.get("openai_endpoint_name"),
            "openai_schema_name": decision.get("openai_schema_name") or OVERNIGHT_SCHEMA,
            "openai_ws_used": decision.get("openai_ws_used"),
            "profit_rate_live": ctx.get("pnl_pct"),
            "peak_profit": ctx.get("peak_profit_pct"),
            "held_sec": ctx.get("held_sec"),
            "last_holding_ai_action": ctx.get("last_holding_ai_action"),
            "last_holding_ai_score": ctx.get("last_holding_ai_score"),
        }
        if emit_events:
            _emit(row, "scalp_sim_overnight_decision", decision_fields)

        if action == "HOLD_OVERNIGHT":
            _mark_hold_overnight(row, target_date, decision)
            remaining.append(row)
            summary_counts["hold_overnight"] += 1
            if emit_events:
                _emit(
                    row,
                    "scalp_sim_overnight_hold",
                    {
                        **decision_fields,
                        "runtime_effect": "sim_observation_only_active_carry",
                    },
                )
            rows.append(
                {
                    "sim_record_id": sim_record_id,
                    "sim_parent_record_id": row.get("sim_parent_record_id"),
                    "stock_name": row.get("name") or row.get("stock_name"),
                    "stock_code": row.get("code") or row.get("stock_code"),
                    "decision": action,
                    "status_after": "HOLDING",
                    "runtime_features": ctx,
                    "overnight_ai_action": action,
                    "overnight_ai_confidence": decision.get("confidence"),
                    "overnight_ai_reason": decision.get("reason"),
                    "overnight_ai_fallback": decision.get("ai_fallback"),
                    "overnight_ai_fallback_class": decision.get("ai_fallback_class"),
                    "overnight_ai_fallback_reason": decision.get("ai_fallback_reason"),
                    "sell_today_realized_profit_pct": None,
                    "sell_today_realized_pnl_krw": None,
                }
            )
            continue

        fill = _complete_sell_today(row, price, target_date, decision)
        summary_counts["sell_today"] += 1
        if price.get("price_fallback_used"):
            summary_counts["price_fallback"] += 1
        if emit_events:
            _emit(
                row,
                "scalp_sim_overnight_sell_today",
                {
                    **decision_fields,
                    "exit_rule": "scalp_sim_overnight_sell_today",
                    "sell_reason_type": "OVERNIGHT",
                    "assumed_fill_price": fill["assumed_fill_price"],
                    "qty": fill["qty"],
                    "profit_rate": f"{fill['profit_rate']:+.2f}",
                    "realized_pnl_krw": fill["realized_pnl_krw"],
                    "runtime_effect": "simulated_completed_only",
                },
            )
            _emit(
                row,
                "scalp_sim_sell_order_assumed_filled",
                {
                    **base_fields,
                    "threshold_family": "scalp_sim_overnight_ai_carry",
                    "exit_rule": "scalp_sim_overnight_sell_today",
                    "sell_reason_type": "OVERNIGHT",
                    "exit_decision_source": "overnight_v1",
                    "qty": fill["qty"],
                    "assumed_fill_price": fill["assumed_fill_price"],
                    "best_bid": price.get("best_bid"),
                    "best_ask": price.get("best_ask"),
                    "buy_price": row.get("buy_price"),
                    "profit_rate": f"{fill['profit_rate']:+.2f}",
                    "realized_pnl_krw": fill["realized_pnl_krw"],
                    "would_submit_stage": "sell_order_sent",
                    "runtime_effect": "simulated_completed_only",
                },
            )
        rows.append(
            {
                "sim_record_id": sim_record_id,
                "sim_parent_record_id": row.get("sim_parent_record_id"),
                "stock_name": row.get("name") or row.get("stock_name"),
                "stock_code": row.get("code") or row.get("stock_code"),
                "decision": "SELL_TODAY",
                "status_after": "COMPLETED",
                "runtime_features": ctx,
                "overnight_ai_action": action,
                "overnight_ai_confidence": decision.get("confidence"),
                "overnight_ai_reason": decision.get("reason"),
                "overnight_ai_fallback": decision.get("ai_fallback"),
                "overnight_ai_fallback_class": decision.get("ai_fallback_class"),
                "overnight_ai_fallback_reason": decision.get("ai_fallback_reason"),
                "sell_today_realized_profit_pct": fill["profit_rate"],
                "sell_today_realized_pnl_krw": fill["realized_pnl_krw"],
                "assumed_fill_price": fill["assumed_fill_price"],
            }
        )

    if mutate_state:
        payload["active_positions"] = remaining
        _write_state(payload, state_path)

    return {
        "target_date": target_date,
        "generated_at": _now_iso(),
        "schema_version": SCHEMA_VERSION,
        "artifact_role": "postclose_source_packet_for_scalp_sim_overnight_ai_carry",
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "state_path": str(state_path),
        "summary": {
            "decision_target": int(summary_counts.get("decision_target", 0)),
            "sell_today": int(summary_counts.get("sell_today", 0)),
            "hold_overnight": int(summary_counts.get("hold_overnight", 0)),
            "ai_success": int(summary_counts.get("ai_success", 0)),
            "ai_failure_fallback": int(summary_counts.get("ai_failure_fallback", 0)),
            "ai_timeout_fallback": int(summary_counts.get("ai_timeout_fallback", 0)),
            "ai_engine_disabled_fallback": int(summary_counts.get("ai_engine_disabled_fallback", 0)),
            "ai_lock_contention_fallback": int(summary_counts.get("ai_lock_contention_fallback", 0)),
            "ai_parse_fail_fallback": int(summary_counts.get("ai_parse_fail_fallback", 0)),
            "price_fallback": int(summary_counts.get("price_fallback", 0)),
            "idempotent_skipped": int(summary_counts.get("idempotent_skipped", 0)),
            **dict(summary_counts),
            "active_before": len(active),
            "active_after": len(remaining),
            "carry_open_count": sum(1 for row in remaining if str(row.get("scalp_sim_overnight_status") or "") == "HOLD_OVERNIGHT"),
            "forbidden_uses": [
                "broker_submit",
                "real_execution_quality_claim",
                "runtime_threshold_apply",
                "provider_route_change",
                "live_order_enable",
            ],
        },
        "rows": rows,
    }


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields")
    return fields if isinstance(fields, dict) else {}


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def _event_fallback_class(fields: dict[str, Any]) -> str:
    explicit = str(fields.get("ai_fallback_class") or "").strip()
    if explicit:
        return explicit
    if _truthy(fields.get("ai_fallback")) or str(fields.get("ai_parse_ok") or "").strip().lower() in {"false", "0"}:
        return _classify_ai_fallback(
            str(fields.get("ai_fallback_reason") or fields.get("ai_reason") or fields.get("ai_risk_note") or ""),
            result_source=str(fields.get("ai_result_source") or ""),
        )
    return "none"


def build_report(target_date: str, state_path: Path = STATE_PATH) -> dict[str, Any]:
    events_path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    events = read_jsonl(events_path, errors="ignore")
    overnight_events = [
        event for event in events
        if str(event.get("stage") or "").startswith("scalp_sim_overnight_")
        or (
            str(event.get("stage") or "") == "scalp_sim_sell_order_assumed_filled"
            and _event_fields(event).get("exit_rule") == "scalp_sim_overnight_sell_today"
        )
    ]
    stage_counts = Counter(str(event.get("stage") or "-") for event in overnight_events)
    action_counts = Counter(
        str(action)
        for event in overnight_events
        for action in [_event_fields(event).get("ai_action") or _event_fields(event).get("overnight_ai_action")]
        if action
    )
    fallback_counts = Counter(
        _event_fallback_class(_event_fields(event))
        for event in overnight_events
        if str(event.get("stage") or "") == "scalp_sim_overnight_decision"
        and _event_fallback_class(_event_fields(event)) != "none"
    )
    state = _load_state(state_path)
    active = state.get("active_positions") if isinstance(state.get("active_positions"), list) else []
    carry_open = [
        row for row in active
        if isinstance(row, dict)
        and str(row.get("scalp_sim_overnight_status") or "") == "HOLD_OVERNIGHT"
        and str(row.get("scalp_sim_overnight_decision_date") or "") == target_date
    ]
    rows: list[dict[str, Any]] = []
    for event in overnight_events:
        fields = _event_fields(event)
        rows.append(
            {
                "emitted_at": event.get("emitted_at"),
                "stage": event.get("stage"),
                "stock_name": event.get("stock_name"),
                "stock_code": event.get("stock_code"),
                "sim_record_id": fields.get("sim_record_id"),
                "sim_parent_record_id": fields.get("sim_parent_record_id"),
                "actual_order_submitted": fields.get("actual_order_submitted"),
                "broker_order_forbidden": fields.get("broker_order_forbidden"),
                "decision_authority": fields.get("decision_authority"),
                "runtime_effect": fields.get("runtime_effect"),
                "overnight_schema": fields.get("overnight_schema"),
                "ai_action": fields.get("ai_action"),
                "ai_confidence": fields.get("ai_confidence"),
                "ai_reason": fields.get("ai_reason"),
                "ai_risk_note": fields.get("ai_risk_note"),
                "ai_parse_ok": fields.get("ai_parse_ok"),
                "ai_fallback": fields.get("ai_fallback") if fields.get("ai_fallback") is not None else (_event_fallback_class(fields) != "none"),
                "ai_fallback_class": _event_fallback_class(fields),
                "ai_fallback_reason": fields.get("ai_fallback_reason"),
                "ai_result_source": fields.get("ai_result_source"),
                "current_price": fields.get("current_price"),
                "current_price_source": fields.get("current_price_source"),
                "profit_rate_live": fields.get("profit_rate_live"),
                "peak_profit": fields.get("peak_profit"),
                "held_sec": fields.get("held_sec"),
                "sell_today_realized_profit_pct": fields.get("profit_rate"),
                "sell_today_realized_pnl_krw": fields.get("realized_pnl_krw"),
                "next_day_open_gap_pct": None,
                "next_day_mfe_pct": None,
                "next_day_mae_pct": None,
                "next_day_close_pct": None,
                "final_realized_exit_pct": None,
            }
        )
    return {
        "target_date": target_date,
        "generated_at": _now_iso(),
        "schema_version": SCHEMA_VERSION,
        "artifact_role": "postclose_source_packet_for_scalp_sim_overnight_ai_carry",
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "source_path": str(events_path),
        "state_path": str(state_path),
        "summary": {
            "decision_target": int(stage_counts.get("scalp_sim_overnight_decision", 0)),
            "sell_today": int(stage_counts.get("scalp_sim_overnight_sell_today", 0)),
            "hold_overnight": int(stage_counts.get("scalp_sim_overnight_hold", 0)),
            "sell_assumed_filled": int(stage_counts.get("scalp_sim_sell_order_assumed_filled", 0)),
            "carry_restored": int(stage_counts.get("scalp_sim_overnight_carry_restored", 0)),
            "carry_open_count": len(carry_open),
            "ai_failure_fallback": sum(fallback_counts.values()),
            "ai_timeout_fallback": int(fallback_counts.get("timeout", 0)),
            "ai_engine_disabled_fallback": int(fallback_counts.get("engine_disabled", 0)),
            "ai_lock_contention_fallback": int(fallback_counts.get("lock_contention", 0)),
            "ai_parse_fail_fallback": int(fallback_counts.get("parse_fail", 0)),
            "ai_fallback_counts": dict(sorted(fallback_counts.items())),
            "stage_counts": dict(sorted(stage_counts.items())),
            "action_counts": dict(sorted(action_counts.items())),
            "forbidden_uses": [
                "broker_submit",
                "real_execution_quality_claim",
                "runtime_threshold_apply",
                "provider_route_change",
                "live_order_enable",
            ],
        },
        "rows": rows,
    }


def write_outputs(report: dict[str, Any], output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = str(report.get("target_date") or datetime.now().date().isoformat())
    json_path = output_dir / f"scalp_sim_overnight_{target_date}.json"
    md_path = output_dir / f"scalp_sim_overnight_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        f"# Scalp Sim Overnight {target_date}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- artifact_role: `{report.get('artifact_role')}`",
        f"- runtime_effect: `{str(report.get('runtime_effect')).lower()}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- decision_target: `{summary.get('decision_target', 0)}`",
        f"- sell_today: `{summary.get('sell_today', 0)}`",
        f"- hold_overnight: `{summary.get('hold_overnight', 0)}`",
        f"- carry_open_count: `{summary.get('carry_open_count', 0)}`",
        f"- ai_failure_fallback: `{summary.get('ai_failure_fallback', 0)}`",
        f"- ai_timeout_fallback: `{summary.get('ai_timeout_fallback', 0)}`",
        f"- ai_engine_disabled_fallback: `{summary.get('ai_engine_disabled_fallback', 0)}`",
        "",
        "## Stage Counts",
        "",
    ]
    for stage, count in (summary.get("stage_counts") or {}).items():
        lines.append(f"- `{stage}`: `{count}`")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| time | stage | stock | action | confidence | profit/live | sell_profit | held_sec |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report.get("rows") or []:
        lines.append(
            f"| {row.get('emitted_at') or '-'} | `{row.get('stage') or '-'}` | "
            f"{row.get('stock_name')}({row.get('stock_code')}) | `{row.get('ai_action') or '-'}` | "
            f"{row.get('ai_confidence') or '-'} | {row.get('profit_rate_live') or '-'} | "
            f"{row.get('sell_today_realized_profit_pct') or '-'} | {row.get('held_sec') or '-'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _openai_keys() -> list[str]:
    raw = os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY") or ""
    keys = [part.strip() for part in raw.split(",") if part.strip()]
    keys.extend(v for k, v in sorted(CONF.items()) if str(k).startswith("OPENAI_API_KEY") and v)
    seen: set[str] = set()
    unique: list[str] = []
    for key in keys:
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def _build_openai_engine():
    from src.engine import ai_engine_openai as openai_module
    from src.engine.ai_engine_openai import GPTSniperEngine

    keys = _openai_keys()
    if not keys:
        raise RuntimeError("OPENAI_API_KEY or OPENAI_API_KEYS is required for --live-openai")
    engine = GPTSniperEngine(keys, announce_startup=False)
    fast_model = str(getattr(TRADING_RULES, "GPT_FAST_MODEL", "gpt-5-nano") or "gpt-5-nano")
    deep_model = str(getattr(TRADING_RULES, "GPT_DEEP_MODEL", fast_model) or fast_model)
    report_model = str(getattr(TRADING_RULES, "GPT_REPORT_MODEL", fast_model) or fast_model)
    engine.set_model_names(fast_model=fast_model, deep_model=deep_model, report_model=report_model, announce=False)
    return engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=datetime.now().date().isoformat())
    parser.add_argument("--state-path", type=Path, default=STATE_PATH)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--live-openai", action="store_true", help="Run overnight_v1 through the live OpenAI engine.")
    parser.add_argument("--report-only", action="store_true", help="Only rebuild the source artifact from events/state.")
    parser.add_argument("--dry-run", action="store_true", help="Run decisions without mutating state or emitting events.")
    args = parser.parse_args(argv)

    if args.report_only:
        report = build_report(args.target_date, args.state_path)
    else:
        engine = _build_openai_engine() if args.live_openai else None
        try:
            report = run_sim_overnight(
                target_date=args.target_date,
                ai_engine=engine,
                state_path=args.state_path,
                mutate_state=not args.dry_run,
                emit_events=not args.dry_run,
            )
        finally:
            pool = getattr(locals().get("engine", None), "_responses_ws_pool", None)
            if pool is not None:
                pool.close()
    json_path, md_path = write_outputs(report, args.output_dir)
    print(f"[OK] wrote {json_path}")
    print(f"[OK] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
