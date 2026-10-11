"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import time


from datetime import datetime, timedelta


from pathlib import Path


from typing import Any


from src.utils.jsonl_io import iter_jsonl


PIPELINE_EVENTS_DIR = Path(__file__).resolve().parents[4] / "data" / "pipeline_events"


STATUS_VALUES = {
    "OK",
    "MISSING",
    "STALE",
    "PARSE_ERROR",
    "PARTIAL",
    "RATE_LIMITED",
    "TOKEN_ERROR",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(str(value).replace(",", "").replace("+", "")))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_code(code: Any) -> str:
    return str(code or "").strip().lstrip("A")


def _load_pipeline_event_codes(target_date: str, limit: int = 120) -> list[str]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    codes: list[str] = []
    seen: set[str] = set()
    for item in iter_jsonl(path, errors="ignore"):
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        code = _normalize_code(item.get("stock_code") or fields.get("stock_code"))
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
        if len(codes) >= limit:
            break
    return codes


def _ws_age_sec(
    ws_data: dict[str, Any] | None, now_ts: float | None = None
) -> float | None:
    if not isinstance(ws_data, dict):
        return None
    now_ts = float(now_ts or time.time())
    candidates = [
        _safe_float(ws_data.get("last_foreign_broker_update_ts"), 0.0),
        _safe_float(ws_data.get("last_prog_update_ts"), 0.0),
        _safe_float(ws_data.get("last_ws_update_ts"), 0.0),
    ]
    latest = max(candidates)
    if latest <= 0:
        return None
    return round(max(0.0, now_ts - latest), 3)


def normalize_institutional_flow_context(
    code: str,
    *,
    daily_summary: dict[str, Any] | None = None,
    period_summary: dict[str, Any] | None = None,
    intraday_chart_qty: dict[str, Any] | None = None,
    intraday_chart_amt: dict[str, Any] | None = None,
    ws_data: dict[str, Any] | None = None,
    status_hint: str | None = None,
) -> dict[str, Any]:
    """Normalize REST/WS helper outputs for explicit offline inspection."""
    code = _normalize_code(code)
    daily_summary = daily_summary if isinstance(daily_summary, dict) else {}
    period_summary = period_summary if isinstance(period_summary, dict) else {}
    intraday_chart_qty = (
        intraday_chart_qty if isinstance(intraday_chart_qty, dict) else {}
    )
    intraday_chart_amt = (
        intraday_chart_amt if isinstance(intraday_chart_amt, dict) else {}
    )
    ws_data = ws_data if isinstance(ws_data, dict) else {}

    foreign_intraday_qty = _safe_int(intraday_chart_qty.get("foreign_net"))
    inst_intraday_qty = _safe_int(intraday_chart_qty.get("inst_net"))
    foreign_intraday_amt = _safe_int(intraday_chart_amt.get("foreign_net"))
    inst_intraday_amt = _safe_int(intraday_chart_amt.get("inst_net"))
    foreign_roll5 = _safe_int(period_summary.get("foreign_net"))
    inst_roll5 = _safe_int(period_summary.get("inst_net"))
    smart_money_net = _safe_int(
        daily_summary.get("smart_money_net"), foreign_roll5 + inst_roll5
    )
    broker_net = _safe_int(ws_data.get("foreign_broker_net_est_qty"))
    broker_delta = _safe_int(ws_data.get("foreign_broker_net_est_delta_qty"))
    program_net_qty = _safe_int(ws_data.get("prog_net_qty"))
    program_delta_qty = _safe_int(ws_data.get("prog_delta_qty"))
    program_net_amt = _safe_int(ws_data.get("prog_net_amt"))

    dual_net_buy = foreign_roll5 > 0 and inst_roll5 > 0
    score = 0
    score += 25 if dual_net_buy else 0
    score += 20 if smart_money_net > 0 else 0
    score += 15 if broker_delta > 0 else 0
    score += 15 if program_delta_qty > 0 else 0
    score += 25 if (foreign_intraday_qty + inst_intraday_qty) > 0 else 0
    score = min(100, score)

    if dual_net_buy and score >= 45:
        regime = "DUAL_ACCUMULATION"
    elif foreign_roll5 > 0 or broker_delta > 0:
        regime = "FOREIGN_ACCUMULATION"
    elif inst_roll5 > 0 or inst_intraday_qty > 0:
        regime = "INSTITUTION_ACCUMULATION"
    elif program_delta_qty > 0:
        regime = "PROGRAM_SUPPORT"
    elif smart_money_net < 0 and broker_delta < 0:
        regime = "DISTRIBUTION"
    elif any(
        value for value in (foreign_roll5, inst_roll5, broker_delta, program_delta_qty)
    ):
        regime = "MIXED"
    else:
        regime = "UNKNOWN"

    sources = []
    if daily_summary:
        sources.append("ka10059")
    if period_summary:
        sources.append("ka10061")
    if intraday_chart_qty or intraday_chart_amt:
        sources.append("ka10064")
    if ws_data:
        if "0F" in (ws_data.get("received_types") or set()) or ws_data.get(
            "foreign_broker_net_est_qty"
        ):
            sources.append("WS_0F")
        if "0w" in (ws_data.get("received_types") or set()) or ws_data.get(
            "prog_net_qty"
        ):
            sources.append("WS_0w")

    status = status_hint if status_hint in STATUS_VALUES else None
    if not status:
        status = (
            "OK"
            if {"ka10059", "ka10061"} <= set(sources)
            else "PARTIAL"
            if sources
            else "MISSING"
        )

    return {
        "stock_code": code,
        "foreign_net_intraday_qty": foreign_intraday_qty,
        "foreign_net_intraday_amt": foreign_intraday_amt,
        "institution_net_intraday_qty": inst_intraday_qty,
        "institution_net_intraday_amt": inst_intraday_amt,
        "foreign_broker_est_net_qty": broker_net,
        "foreign_broker_est_delta_qty": broker_delta,
        "program_net_qty": program_net_qty,
        "program_delta_qty": program_delta_qty,
        "program_net_amt": program_net_amt,
        "foreign_net_roll5": foreign_roll5,
        "inst_net_roll5": inst_roll5,
        "dual_net_buy": dual_net_buy,
        "smart_money_net": smart_money_net,
        "institutional_accumulation_score": score,
        "institutional_flow_regime": regime,
        "institutional_flow_source": (
            "+".join(dict.fromkeys(sources)) if sources else "none"
        ),
        "institutional_flow_status": status,
        "institutional_flow_age_sec": _ws_age_sec(ws_data),
        "runtime_effect": False,
        "decision_authority": "archive_offline_source_only",
    }


def resolve_institutional_flow_context(
    code: str,
    *,
    token: str | None,
    target_date: str,
    ws_data: dict[str, Any] | None = None,
    live_intraday: bool = False,
) -> dict[str, Any]:
    result = normalize_institutional_flow_context(code, ws_data=ws_data)
    result["institutional_flow_status"] = "RETIRED_NO_COLLECTION"
    return result


RUNTIME_FEATURE_KEYS = [
    "foreign_net_intraday_qty",
    "foreign_net_intraday_amt",
    "institution_net_intraday_qty",
    "institution_net_intraday_amt",
    "foreign_broker_est_net_qty",
    "foreign_broker_est_delta_qty",
    "program_net_qty",
    "program_delta_qty",
    "program_net_amt",
    "foreign_net_roll5",
    "inst_net_roll5",
    "dual_net_buy",
    "smart_money_net",
    "institutional_accumulation_score",
    "institutional_flow_regime",
    "institutional_flow_source",
    "institutional_flow_status",
    "institutional_flow_age_sec",
]
