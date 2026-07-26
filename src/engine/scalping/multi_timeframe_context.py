"""Shared completed-bar context for scalping AI decision stages.

The bundle supplies inputs only.  It has no standalone action, order, provider,
threshold, or safety authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.scalping.market_context_observation import (
    derive_scalping_market_features,
)

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "scalping_multi_timeframe_context_v1"
SOURCE_BAR_LIMIT = 430
MODEL_MULTI_TIMEFRAME_BAR_LIMIT = 20

INPUT_CONTRACT = {
    "metric_role": "ai_input_feature_bundle",
    "decision_authority": "stage_context_input_only_no_standalone_action",
    "window_policy": "exact_timestamp_venue_session_completed_bar",
    "sample_floor": "field_specific_completed_bar_and_source_availability",
    "primary_decision_metric": "required_source_field_availability",
    "source_quality_gate": "fresh_same_basis_conflict_free",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "live_promotion_gate": (
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED_full_market_only"
    ),
    "forbidden_uses": [
        "standalone_buy_hold_exit_authority",
        "runtime_threshold_apply",
        "order_price_or_quantity_decision",
        "provider_route_change",
        "broker_or_safety_guard_bypass",
    ],
}
_PREVIOUS_DAY_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_PREVIOUS_DAY_CACHE_LOCK = threading.Lock()
_PREVIOUS_DAY_CACHE_TTL_SEC = 21_600.0


def multi_timeframe_ai_input_enabled(captured_at: datetime) -> bool:
    """Return the single global post-validation promotion state."""

    enabled = str(
        os.getenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED", "false")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return False
    active_date = str(
        os.getenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE", "")
    ).strip()
    if not active_date:
        return True
    try:
        first_active_date = datetime.strptime(active_date, "%Y-%m-%d").date()
    except ValueError:
        return False
    return captured_at.astimezone(KST).date() >= first_active_date


def _clean_code(code: str) -> str:
    raw = str(code or "").strip().upper()
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            raw = raw[:-3]
    if raw.startswith("A"):
        raw = raw[1:]
    digits = "".join(char for char in raw if char.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def _daily_request_code(code: str, venue: str) -> tuple[str, str]:
    base = _clean_code(code)
    venue_upper = str(venue or "").upper()
    if venue_upper in {"NXT", "PREMARKET_KRX_LIKE"}:
        return f"{base}_NX", "NXT"
    return base, "KRX"


def _explicit_index_code(ws_data: dict[str, Any], *, sector: bool) -> str:
    keys = (
        ("sector_index_code", "sector_inds_cd", "industry_index_code")
        if sector
        else ("market_index_code", "market_inds_cd")
    )
    for key in keys:
        value = str(ws_data.get(key) or "").strip()
        if value:
            return value
    if sector:
        return ""
    market = str(
        ws_data.get("market_type")
        or ws_data.get("mrkt_tp")
        or ws_data.get("market_code")
        or ws_data.get("market_segment")
        or ws_data.get("market")
        or ws_data.get("strategy")
        or ""
    ).upper()
    if market in {"101", "10", "1"}:
        return "101"
    if market in {"001", "0"}:
        return "001"
    if "KOSDAQ" in market:
        return "101"
    if "KOSPI" in market:
        return "001"
    return ""


def _previous_day_source(
    token: str | None,
    code: str,
    ws_data: dict[str, Any],
    target_date: str,
    venue: str,
) -> dict[str, Any]:
    supplied = ws_data.get("previous_day_levels")
    if isinstance(supplied, dict) and supplied:
        return {**supplied, "source": supplied.get("source") or "runtime_state"}
    request_code, venue_basis = _daily_request_code(code, venue)
    if not token:
        return {
            "source_quality": "missing",
            "reason": "token_missing",
            "request_code": request_code,
            "venue_basis": venue_basis,
        }
    cache_key = (request_code, target_date)
    with _PREVIOUS_DAY_CACHE_LOCK:
        cached = _PREVIOUS_DAY_CACHE.get(cache_key)
        if cached and time.monotonic() - cached[0] <= _PREVIOUS_DAY_CACHE_TTL_SEC:
            return dict(cached[1])
    try:
        from src.utils import kiwoom_utils

        frame = kiwoom_utils.get_daily_data_ka10005_df(token, request_code)
        if frame is None or frame.empty:
            return {
                "source": "kiwoom_ka10005",
                "source_quality": "missing",
                "reason": "daily_rows_missing",
                "request_code": request_code,
                "venue_basis": venue_basis,
            }
        cutoff = datetime.strptime(target_date, "%Y-%m-%d")
        eligible = frame[frame.index < cutoff]
        if eligible.empty:
            return {
                "source": "kiwoom_ka10005",
                "source_quality": "missing",
                "reason": "previous_trading_day_missing",
                "request_code": request_code,
                "venue_basis": venue_basis,
            }
        index = eligible.index[-1]
        row = eligible.iloc[-1]
        result = {
            "date": index.date().isoformat(),
            "high": row.get("High"),
            "low": row.get("Low"),
            "close": row.get("Close"),
            "source": "kiwoom_ka10005",
            "source_quality": "pass",
            "request_code": request_code,
            "venue_basis": venue_basis,
        }
        with _PREVIOUS_DAY_CACHE_LOCK:
            _PREVIOUS_DAY_CACHE[cache_key] = (time.monotonic(), dict(result))
        return result
    except Exception as exc:
        return {
            "source": "kiwoom_ka10005",
            "source_quality": "missing",
            "reason": f"{type(exc).__name__}:{str(exc)[:120]}",
            "request_code": request_code,
            "venue_basis": venue_basis,
        }


def _index_context_source(
    token: str | None,
    index_code: str,
    *,
    source_role: str,
) -> dict[str, Any]:
    if not index_code:
        return {
            "source": "kiwoom_ka20005",
            "source_quality": {"status": "source_unavailable"},
            "reason": f"{source_role}_index_code_missing",
        }
    if not token:
        return {
            "source": "kiwoom_ka20005",
            "index_code": index_code,
            "source_quality": {"status": "source_unavailable"},
            "reason": "token_missing",
        }
    try:
        from src.utils import kiwoom_utils

        rows, meta = kiwoom_utils.get_index_minute_candles_ka20005_with_meta(
            token, index_code, limit=SOURCE_BAR_LIMIT
        )
        return {
            "source": "kiwoom_ka20005",
            "index_code": index_code,
            "minute_rows": rows,
            "source_meta": meta,
        }
    except Exception as exc:
        return {
            "source": "kiwoom_ka20005",
            "index_code": index_code,
            "source_quality": {"status": "source_unavailable"},
            "reason": f"{type(exc).__name__}:{str(exc)[:120]}",
        }


def build_multi_timeframe_context(
    rows: list[dict[str, Any]],
    *,
    token: str | None,
    symbol: str,
    venue: str,
    session: str,
    ws_data: dict[str, Any] | None,
    captured_at: datetime,
    fetch_external_sources: bool = False,
) -> dict[str, Any]:
    """Build the shared feature bundle from exact completed source windows."""

    ws = dict(ws_data or {})
    target_date = captured_at.astimezone(KST).date().isoformat()
    previous_day = (
        _previous_day_source(token, symbol, ws, target_date, venue)
        if fetch_external_sources or isinstance(ws.get("previous_day_levels"), dict)
        else {"source_quality": "missing", "reason": "auxiliary_fetch_not_requested"}
    )
    market_code = _explicit_index_code(ws, sector=False)
    sector_code = _explicit_index_code(ws, sector=True)
    market_context = (
        dict(ws.get("market_context") or {})
        if isinstance(ws.get("market_context"), dict)
        else (
            _index_context_source(token, market_code, source_role="market")
            if fetch_external_sources
            else {
                "source_quality": {"status": "source_unavailable"},
                "reason": "auxiliary_fetch_not_requested",
            }
        )
    )
    sector_context = (
        dict(ws.get("sector_context") or {})
        if isinstance(ws.get("sector_context"), dict)
        else (
            _index_context_source(token, sector_code, source_role="sector")
            if fetch_external_sources
            else {
                "source_quality": {"status": "source_unavailable"},
                "reason": "auxiliary_fetch_not_requested",
            }
        )
    )
    derived = derive_scalping_market_features(
        rows,
        symbol=_clean_code(symbol),
        venue=venue,
        session=session,
        target_date=target_date,
        captured_at=captured_at.isoformat(),
        previous_day=previous_day,
        market_context=market_context,
        sector_context=sector_context,
    )
    bundle = {
        "schema": SCHEMA,
        "input_bundle_version": SCHEMA,
        "captured_at": derived.get("captured_at"),
        "multi_timeframe_bars": {
            key: list(rows_for_interval or [])[-MODEL_MULTI_TIMEFRAME_BAR_LIMIT:]
            for key, rows_for_interval in dict(
                derived.get("multi_timeframe_bars") or {}
            ).items()
        },
        "incomplete_multi_timeframe_bars": derived.get(
            "incomplete_multi_timeframe_bars"
        ),
        "session_bar_vwap": derived.get("session_bar_vwap"),
        "opening_range_5m": derived.get("opening_range_5m"),
        "opening_range_15m": derived.get("opening_range_15m"),
        "previous_day_levels": derived.get("previous_day_levels"),
        "market_context": derived.get("market_context"),
        "sector_context": derived.get("sector_context"),
        "source_quality": derived.get("source_quality"),
        "input_contract": INPUT_CONTRACT,
        "ai_input_enabled": multi_timeframe_ai_input_enabled(captured_at),
    }
    bundle["payload_hash"] = hashlib.sha256(
        json.dumps(
            bundle,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return bundle
