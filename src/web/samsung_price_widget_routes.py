"""Samsung quote endpoint and separately authenticated operator order endpoint.

Both paths consume only the AWS server's existing shared Kiwoom token cache.
The quote path is read-only and may attach a display-only Samsung position
snapshot. The order path requires a distinct key and an explicit Windows-widget
action; neither path issues tokens, queries account cash, or controls a bot
process.
"""

from __future__ import annotations

import hmac
import json
import math
import os
import threading
import time
from datetime import datetime, time as datetime_time
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, jsonify, request

from src.engine.monitoring import samsung_widget_contract
from src.engine.sniper_config import CONF
from src.trading.order.tick_utils import get_tick_size
from src.trading.widget_auto_trade.manual_orders import ManualWidgetOrderExecutor
from src.utils import kiwoom_utils

samsung_price_widget_bp = Blueprint("samsung_price_widget", __name__)

_WIDGET_ACCESS_KEY_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY"
_WIDGET_ACCESS_KEY_FILE_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE"
_WIDGET_ACCESS_KEY_HEADER = "X-KORStockScan-Widget-Key"
_WIDGET_ORDER_KEY_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY"
_WIDGET_ORDER_KEY_FILE_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY_FILE"
_WIDGET_ORDER_KEY_HEADER = "X-KORStockScan-Widget-Order-Key"
_WIDGET_SNAPSHOT_PATH_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH"
_WIDGET_WS_SNAPSHOT_PATH_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_WS_SNAPSHOT_PATH"
_SAMSUNG_CODE = "005930"
_SAMSUNG_NAME = "삼성전자"
_REQUEST_TIMEOUT_SEC = 5
_MINUTE_CHART_BAR_COUNT = 20
_MINUTE_TREND_HORIZONS = (1, 3, 5)
_MINUTE_TREND_TICK_MULTIPLIERS = {1: 1, 3: 2, 5: 3}
_NXT_PREMARKET_START = datetime_time(hour=8)
_NXT_PREMARKET_END = datetime_time(hour=8, minute=50)
_KRX_SESSION_START = datetime_time(hour=9)
_NXT_AFTERMARKET_START = datetime_time(hour=15, minute=40)
_NXT_AFTERMARKET_END = datetime_time(hour=20)
_MANUAL_ORDER_SNAPSHOT_MAX_AGE_SEC = 15
_MANUAL_ORDER_EXECUTOR: ManualWidgetOrderExecutor | None = None
_POSITION_CACHE_TTL_SEC = 30
_POSITION_FAILURE_CACHE_TTL_SEC = 10
_POSITION_AUTHORITY = "widget_account_position_display_only"
_POSITION_CACHE_LOCK = threading.Lock()
_POSITION_CACHE: tuple[float, dict] | None = None
_DIRECT_QUOTE_CACHE_LOCK = threading.Lock()
_DIRECT_QUOTE_CACHE: tuple[float, str, dict] | None = None
_DIRECT_QUOTE_CACHE_TTL_SEC = 8.0
_WS_COMPARISON_MAX_AGE_SEC = 5.0
_WS_COMPARISON_AUTHORITY = "widget_ws_price_comparison_only"
_DEFAULT_WS_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "runtime"
    / "kiwoom_ws_snapshot"
    / "latest.json"
)

# Official Kiwoom reference gate evidence (retrieved 2026-08-12T13:55:33+09:00):
# upstream SHA 69642586f7d84ba9fd8a6faf1f1537c7fda6568b
# - kiwoom_docs/계좌.md: kt00018 request/response contract
# - kiwoom/_data/kiwoom_api_spec.json: kt00018 fields/examples
# - examples/국내주식/계좌/get_domestic_account_evaluation_balance.py
_KIWOOM_POSITION_REFERENCE_SHA = "69642586f7d84ba9fd8a6faf1f1537c7fda6568b"


def _parse_positive_price(value: object) -> int | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return abs(int(text))
    except (TypeError, ValueError):
        return None


def _now_kst() -> datetime:
    return datetime.now(ZoneInfo("Asia/Seoul"))


def _ws_snapshot_path() -> Path:
    configured = str(os.getenv(_WIDGET_WS_SNAPSHOT_PATH_ENV) or "").strip()
    return Path(configured) if configured else _DEFAULT_WS_SNAPSHOT_PATH


def _websocket_price_comparison(*, reference_price: int, observed_at: datetime) -> dict:
    """Build a fail-closed, display-only comparison from shared 0B state."""

    result = {
        "status": "UNAVAILABLE",
        "symbol": _SAMSUNG_CODE,
        "current_price": None,
        "reference_price": int(reference_price),
        "price_delta": None,
        "observed_at_kst": None,
        "age_ms": None,
        "ws_item": None,
        "market_route": None,
        "source": "shared_kiwoom_ws_dashboard_snapshot_0B",
        "authority": _WS_COMPARISON_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "used_for_manual_order": False,
        "reason": "snapshot_missing_or_invalid",
    }
    try:
        payload = json.loads(_ws_snapshot_path().read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return result
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != "kiwoom_ws_dashboard_snapshot_v1"
        or payload.get("decision_authority") != "source_quality_only"
        or payload.get("runtime_effect") is not False
    ):
        result["reason"] = "snapshot_contract_mismatch"
        return result
    stocks = payload.get("stocks")
    row = stocks.get(_SAMSUNG_CODE) if isinstance(stocks, dict) else None
    if not isinstance(row, dict):
        result["reason"] = "samsung_0b_not_subscribed"
        return result
    last_trade_tick = row.get("last_trade_tick")
    last_trade_tick = last_trade_tick if isinstance(last_trade_tick, dict) else {}
    price = _parse_positive_price(last_trade_tick.get("price"))
    try:
        tick_ts = float(last_trade_tick.get("ts"))
        type_tick_ts = float((row.get("last_realtime_type_ts") or {}).get("0B"))
    except (TypeError, ValueError, AttributeError):
        tick_ts = 0.0
        type_tick_ts = 0.0
    age_sec = observed_at.timestamp() - tick_ts if tick_ts > 0 else math.inf
    if (
        price is None
        or not math.isfinite(age_sec)
        or not math.isfinite(type_tick_ts)
        or abs(tick_ts - type_tick_ts) > 0.001
    ):
        result["reason"] = "samsung_0b_price_missing"
        return result
    if age_sec < -2.0 or age_sec > _WS_COMPARISON_MAX_AGE_SEC:
        result.update(
            {
                "age_ms": round(max(0.0, age_sec) * 1000.0, 1),
                "reason": "samsung_0b_stale",
            }
        )
        return result
    type_items = row.get("last_realtime_type_item")
    ws_item = (
        str(type_items.get("0B") or "").strip().upper()
        if isinstance(type_items, dict)
        else ""
    )
    if ws_item not in {_SAMSUNG_CODE, f"{_SAMSUNG_CODE}_NX", f"{_SAMSUNG_CODE}_AL"}:
        result["reason"] = "samsung_0b_item_mismatch"
        return result
    route = (
        "SOR"
        if ws_item.endswith("_AL")
        else "NXT" if ws_item.endswith("_NX") else "KRX"
    )
    tick_time = datetime.fromtimestamp(tick_ts, tz=ZoneInfo("Asia/Seoul"))
    result.update(
        {
            "status": "OK",
            "current_price": price,
            "price_delta": price - int(reference_price),
            "observed_at_kst": tick_time.isoformat(),
            "age_ms": round(max(0.0, age_sec) * 1000.0, 1),
            "ws_item": ws_item,
            "market_route": route,
            "reason": None,
        }
    )
    return result


def _quote_route_for_observed_at(observed_at: datetime) -> tuple[str, str, str]:
    """Select the explicit Kiwoom market code for the current display session."""
    normalized = (
        observed_at.replace(tzinfo=ZoneInfo("Asia/Seoul"))
        if observed_at.tzinfo is None
        else observed_at.astimezone(ZoneInfo("Asia/Seoul"))
    )
    clock = normalized.time()
    if _NXT_PREMARKET_START <= clock < _NXT_PREMARKET_END:
        return f"{_SAMSUNG_CODE}_NX", "NXT", "krx_like_premarket"
    if _NXT_AFTERMARKET_START <= clock < _NXT_AFTERMARKET_END:
        return f"{_SAMSUNG_CODE}_NX", "NXT", "nxt_aftermarket"
    return _SAMSUNG_CODE, "KRX", "krx_or_closed"


def _completed_minute_closes(
    rows: object,
    *,
    observed_at: datetime,
    limit: int,
    session_start: datetime_time | None = None,
) -> list[tuple[str, int]]:
    """Return current-session completed minute closes, excluding the forming bar."""
    if not isinstance(rows, list):
        return []

    current_minute = observed_at.strftime("%Y%m%d%H%M")
    today = observed_at.strftime("%Y%m%d")
    session_start_minute = (
        f"{today}{session_start.strftime('%H%M')}" if session_start is not None else ""
    )
    completed_by_time: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_time = str(row.get("cntr_tm") or "").strip()
        close_price = _parse_positive_price(row.get("cur_prc"))
        if (
            len(source_time) < 14
            or not source_time[:14].isdigit()
            or not source_time.startswith(today)
            or (bool(session_start_minute) and source_time[:12] < session_start_minute)
            or source_time[:12] >= current_minute
            or close_price is None
        ):
            continue
        completed_by_time[source_time[:14]] = close_price

    return sorted(completed_by_time.items())[-max(1, int(limit)) :]


def _classify_horizon_trend(
    completed: list[tuple[str, int]], *, horizon_minutes: int
) -> tuple[str, str | None]:
    """Classify one completed-close horizon without crossing a missing minute."""
    required_count = max(1, int(horizon_minutes)) + 1
    window = completed[-required_count:]
    if len(window) < required_count:
        return "unavailable", None

    try:
        timestamps = [
            datetime.strptime(source_time[:14], "%Y%m%d%H%M%S")
            for source_time, _ in window
        ]
    except (TypeError, ValueError):
        return "unavailable", None
    if any(
        int((current - previous).total_seconds()) != 60
        for previous, current in zip(timestamps, timestamps[1:])
    ):
        return "unavailable", None

    closes = [price for _, price in window]
    latest_time = window[-1][0]
    net_change = closes[-1] - closes[0]
    tick_size = get_tick_size(closes[-1])
    recent_prices = [price for _, price in completed[-12:]]
    recent_changes = [
        abs(current - previous)
        for previous, current in zip(recent_prices, recent_prices[1:])
    ]
    median_change = float(median(recent_changes)) if recent_changes else 0.0
    raw_band = max(
        tick_size * _MINUTE_TREND_TICK_MULTIPLIERS[horizon_minutes],
        median_change * 1.25,
    )
    flat_band = max(tick_size, int(math.ceil(raw_band / tick_size) * tick_size))
    center = (len(closes) - 1) / 2
    x_variance = sum((index - center) ** 2 for index in range(len(closes)))
    y_mean = sum(closes) / len(closes)
    slope = sum(
        (index - center) * (price - y_mean) for index, price in enumerate(closes)
    ) / max(x_variance, 1)
    total_variance = sum((price - y_mean) ** 2 for price in closes)
    residual = sum(
        (price - (y_mean + slope * (index - center))) ** 2
        for index, price in enumerate(closes)
    )
    regression_r2 = (
        max(0.0, min(1.0, 1.0 - residual / total_variance))
        if total_variance > 0
        else 0.0
    )
    direction = 1 if net_change > 0 else -1 if net_change < 0 else 0
    deltas = [current - previous for previous, current in zip(closes, closes[1:])]
    consistency = (
        sum(1 for change in deltas if change * direction > 0) / len(deltas)
        if direction and deltas
        else 0.0
    )
    minimum_slope = flat_band / max(1, horizon_minutes) * 0.5
    if abs(net_change) <= flat_band:
        return "flat", latest_time
    if (
        net_change > flat_band
        and slope > minimum_slope
        and regression_r2 >= 0.40
        and consistency >= 0.60
    ):
        return "up", latest_time
    if (
        net_change < -flat_band
        and slope < -minimum_slope
        and regression_r2 >= 0.40
        and consistency >= 0.60
    ):
        return "down", latest_time
    return "flat", latest_time


def _classify_minute_trends(
    completed: list[tuple[str, int]],
) -> tuple[dict[str, str], str | None]:
    trends: dict[str, str] = {}
    latest_time: str | None = None
    for horizon in _MINUTE_TREND_HORIZONS:
        trend, trend_at = _classify_horizon_trend(
            completed,
            horizon_minutes=horizon,
        )
        trends[f"{horizon}m"] = trend
        if trend_at is not None:
            latest_time = trend_at
    return trends, latest_time


def _classify_minute_trend(completed: list[tuple[str, int]]) -> tuple[str, str | None]:
    """Backward-compatible one-minute trend classifier."""
    return _classify_horizon_trend(completed, horizon_minutes=1)


def _kiwoom_post(token: str, *, path: str, api_id: str, payload: dict):
    if (path, api_id) not in {
        ("/api/dostk/stkinfo", "ka10001"),
        ("/api/dostk/acnt", "kt00018"),
    }:
        return None
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "api-id": api_id,
    }
    if api_id == "kt00018":
        headers.update({"cont-yn": "N", "next-key": ""})
    try:
        response = requests.post(
            kiwoom_utils.get_api_url(path),
            headers=headers,
            json=payload,
            timeout=_REQUEST_TIMEOUT_SEC,
        )
        response_payload = response.json() if response.content else {}
    except (requests.RequestException, ValueError):
        return None
    if response.status_code != 200:
        return None
    try:
        if int(response_payload["return_code"]) != 0:
            return None
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    return response_payload


def _cached_direct_quote(
    token: str, *, request_code: str, observed_at: datetime
) -> dict | None:
    """Bound quote-only fallback load while the 10-second collector is stale."""

    global _DIRECT_QUOTE_CACHE
    now_epoch = observed_at.timestamp()
    with _DIRECT_QUOTE_CACHE_LOCK:
        cached = _DIRECT_QUOTE_CACHE
        if (
            cached is not None
            and cached[1] == request_code
            and -2.0 <= now_epoch - cached[0] <= _DIRECT_QUOTE_CACHE_TTL_SEC
        ):
            return dict(cached[2])
    payload = _kiwoom_post(
        token,
        path="/api/dostk/stkinfo",
        api_id="ka10001",
        payload={"stk_cd": request_code},
    )
    if not isinstance(payload, dict):
        return None
    with _DIRECT_QUOTE_CACHE_LOCK:
        _DIRECT_QUOTE_CACHE = (now_epoch, request_code, dict(payload))
    return payload


def _position_contract_payload(
    *,
    status: str,
    observed_at: datetime,
    quantity: int | None = None,
    average_price: int | None = None,
    source_exchanges: list[str] | None = None,
    reason: str | None = None,
) -> dict:
    payload = {
        "status": status,
        "symbol": _SAMSUNG_CODE,
        "quantity": quantity,
        "average_price": average_price,
        "observed_at_kst": observed_at.isoformat(),
        "source": "kiwoom_kt00018_shared_cache",
        "source_exchanges": source_exchanges or [],
        "cache_ttl_sec": _POSITION_CACHE_TTL_SEC,
        "token_mode": "shared_cache_only",
        "account_query_read_only": True,
        "authority": _POSITION_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "position_data_used_for_order_quantity": False,
        "official_reference_sha": _KIWOOM_POSITION_REFERENCE_SHA,
    }
    if reason:
        payload["reason"] = reason
    return payload


def _position_row(payload: dict) -> tuple[int, int] | None:
    rows = payload.get("acnt_evlt_remn_indv_tot")
    if not isinstance(rows, list):
        raise ValueError("invalid_position_rows")
    matched: list[tuple[int, int]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_position_row")
        raw_code = str(row.get("stk_cd") or "").strip().upper()
        code = raw_code[1:] if raw_code.startswith("A") else raw_code
        if code != _SAMSUNG_CODE:
            continue
        try:
            quantity = int(str(row.get("rmnd_qty") or "0").strip())
            average_price = int(str(row.get("pur_pric") or "0").strip())
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_position_row") from exc
        if quantity < 0 or (quantity > 0 and average_price <= 0):
            raise ValueError("invalid_position_row")
        matched.append((quantity, average_price if quantity > 0 else 0))
    if len(matched) > 1:
        raise ValueError("duplicate_position_rows")
    return matched[0] if matched else None


def _load_samsung_position(token: str, observed_at: datetime) -> dict:
    successful_exchanges: list[str] = []
    invalid_exchanges: list[str] = []
    found: dict[str, tuple[int, int]] = {}
    for exchange in ("KRX", "NXT"):
        response_payload = _kiwoom_post(
            token,
            path="/api/dostk/acnt",
            api_id="kt00018",
            payload={"qry_tp": "1", "dmst_stex_tp": exchange},
        )
        if response_payload is None:
            continue
        try:
            row = _position_row(response_payload)
        except ValueError:
            invalid_exchanges.append(exchange)
            continue
        successful_exchanges.append(exchange)
        if row is not None:
            found[exchange] = row

    if found:
        distinct = set(found.values())
        if len(distinct) > 1:
            return _position_contract_payload(
                status="UNAVAILABLE",
                observed_at=observed_at,
                source_exchanges=successful_exchanges,
                reason="venue_position_conflict",
            )
        quantity, average_price = found.get("KRX") or found["NXT"]
        return _position_contract_payload(
            status="OK",
            observed_at=observed_at,
            quantity=quantity,
            average_price=average_price if quantity > 0 else None,
            source_exchanges=successful_exchanges,
        )
    if len(successful_exchanges) == 2:
        return _position_contract_payload(
            status="OK",
            observed_at=observed_at,
            quantity=0,
            average_price=None,
            source_exchanges=successful_exchanges,
        )
    return _position_contract_payload(
        status="UNAVAILABLE",
        observed_at=observed_at,
        source_exchanges=successful_exchanges,
        reason=(
            "position_contract_invalid"
            if invalid_exchanges
            else (
                "position_query_failed"
                if not successful_exchanges
                else "position_query_partial_without_holding"
            )
        ),
    )


def _cached_samsung_position(token: str | None, observed_at: datetime) -> dict:
    global _POSITION_CACHE
    if not token:
        return _position_contract_payload(
            status="UNAVAILABLE",
            observed_at=observed_at,
            reason="shared_token_unavailable",
        )
    with _POSITION_CACHE_LOCK:
        now_monotonic = time.monotonic()
        if _POSITION_CACHE is not None:
            cached_at, cached_payload = _POSITION_CACHE
            cache_ttl = (
                _POSITION_CACHE_TTL_SEC
                if cached_payload.get("status") == "OK"
                else _POSITION_FAILURE_CACHE_TTL_SEC
            )
            if now_monotonic - cached_at < cache_ttl:
                return dict(cached_payload)
        payload = _load_samsung_position(token, observed_at)
        _POSITION_CACHE = (now_monotonic, payload)
        return dict(payload)


def _reset_position_cache_for_test() -> None:
    global _DIRECT_QUOTE_CACHE, _POSITION_CACHE
    with _POSITION_CACHE_LOCK:
        _POSITION_CACHE = None
    with _DIRECT_QUOTE_CACHE_LOCK:
        _DIRECT_QUOTE_CACHE = None


def _authorized_request() -> bool:
    expected = _widget_access_key()
    supplied = request.headers.get(_WIDGET_ACCESS_KEY_HEADER, "").strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def _authorized_order_request() -> bool:
    expected = _widget_order_key()
    supplied = request.headers.get(_WIDGET_ORDER_KEY_HEADER, "").strip()
    read_key = _widget_access_key()
    return bool(
        expected
        and supplied
        and (not read_key or not hmac.compare_digest(expected, read_key))
        and hmac.compare_digest(expected, supplied)
    )


def _widget_access_key() -> str:
    direct_value = os.getenv(_WIDGET_ACCESS_KEY_ENV, "").strip()
    if direct_value:
        return direct_value
    key_path = os.getenv(_WIDGET_ACCESS_KEY_FILE_ENV, "").strip()
    if not key_path:
        return ""
    try:
        return Path(key_path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _widget_order_key() -> str:
    direct_value = os.getenv(_WIDGET_ORDER_KEY_ENV, "").strip()
    if direct_value:
        return direct_value
    key_path = os.getenv(_WIDGET_ORDER_KEY_FILE_ENV, "").strip()
    if not key_path:
        return ""
    try:
        return Path(key_path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _error_response(reason: str, status_code: int):
    response = jsonify(
        {
            "status": "unavailable",
            "reason": reason,
            "token_mode": "shared_cache_only",
        }
    )
    response.status_code = status_code
    response.headers["Cache-Control"] = "no-store"
    return response


def _manual_order_response(result_payload: dict):
    status = str(result_payload.get("status") or "")
    status_code = {
        "accepted": 200,
        "partial": 207,
        "rejected": 422,
        "ambiguous": 502,
    }.get(status, 500)
    response = jsonify(result_payload)
    response.status_code = status_code
    response.headers["Cache-Control"] = "no-store"
    return response


def _snapshot_path() -> Path:
    configured = os.getenv(_WIDGET_SNAPSHOT_PATH_ENV, "").strip()
    return (
        Path(configured)
        if configured
        else samsung_widget_contract.DEFAULT_SNAPSHOT_PATH
    )


def _manual_order_executor() -> ManualWidgetOrderExecutor:
    global _MANUAL_ORDER_EXECUTOR
    if _MANUAL_ORDER_EXECUTOR is None:
        _MANUAL_ORDER_EXECUTOR = ManualWidgetOrderExecutor()
    return _MANUAL_ORDER_EXECUTOR


def _fresh_manual_order_snapshot(observed_at: datetime) -> dict | None:
    """Return only a coherent active-session quote suitable for manual orders."""
    payload = samsung_widget_contract.load_snapshot(_snapshot_path())
    if not samsung_widget_contract.snapshot_is_fresh(
        payload,
        now=observed_at,
        max_age_sec=_MANUAL_ORDER_SNAPSHOT_MAX_AGE_SEC,
    ):
        return None
    context = samsung_widget_contract.session_context(observed_at)
    persisted_observed_at = samsung_widget_contract.snapshot_observed_at(payload)
    if not context.active or persisted_observed_at is None:
        return None
    if (
        payload.get("schema_version") != samsung_widget_contract.SNAPSHOT_SCHEMA_VERSION
        or payload.get("status") != "ok"
        or payload.get("symbol") != _SAMSUNG_CODE
        or payload.get("token_mode") != "shared_cache_only"
        or payload.get("market_venue") != context.market_venue
        or payload.get("market_cohort") != context.market_cohort
        or payload.get("quote_request_code") != context.request_code
        or _parse_positive_price(payload.get("current_price")) is None
    ):
        return None
    return payload


def _fresh_collector_snapshot(observed_at: datetime) -> dict | None:
    payload = samsung_widget_contract.load_snapshot(_snapshot_path())
    if not samsung_widget_contract.snapshot_is_fresh(payload, now=observed_at):
        return None
    current_context = samsung_widget_contract.session_context(observed_at)
    if not current_context.active:
        return None
    persisted_observed_at = samsung_widget_contract.snapshot_observed_at(payload)
    if persisted_observed_at is None:
        return None
    if (
        payload.get("schema_version") != samsung_widget_contract.SNAPSHOT_SCHEMA_VERSION
        or payload.get("symbol") != _SAMSUNG_CODE
        or _parse_positive_price(payload.get("current_price")) is None
        or payload.get("token_mode") != "shared_cache_only"
        or payload.get("market_venue") != current_context.market_venue
        or payload.get("market_cohort") != current_context.market_cohort
        or payload.get("quote_request_code") != current_context.request_code
    ):
        return None
    advisory = payload.get("advisory")
    if not samsung_widget_contract.advisory_contract_is_valid(
        advisory,
        snapshot_observed_at=persisted_observed_at,
        context=current_context,
        evaluated_at=observed_at,
    ):
        return None
    exit_advisory = payload.get("exit_advisory")
    if (
        exit_advisory is not None
        and not samsung_widget_contract.exit_advisory_contract_is_valid(
            exit_advisory,
            snapshot_observed_at=persisted_observed_at,
            context=current_context,
            evaluated_at=observed_at,
        )
    ):
        return None
    return payload


def _fallback_advisory(observed_at: datetime, market_session: str) -> dict:
    return {
        "state": "DATA_WAIT",
        "raw_state": "DATA_WAIT",
        "session": market_session,
        "entry_price_low": None,
        "entry_price_high": None,
        "trigger": None,
        "trigger_price": None,
        "invalidation": None,
        "invalidation_price": None,
        "reasons": [],
        "unmet_conditions": ["collector_snapshot_missing_or_stale"],
        "valid_until": observed_at.replace(
            hour=20, minute=0, second=0, microsecond=0
        ).isoformat(),
        "observed_at": observed_at.isoformat(),
        "source_quality": {
            "status": "BLOCKED",
            "issues": ["collector_snapshot_missing_or_stale"],
        },
        "external_risk": {
            "level": "DATA_LIMITED",
            "adverse": [],
            "severe": [],
            "stale": [],
            "unavailable": ["NQ", "MU", "USDKRW"],
            "positive_promotion_forbidden": True,
        },
        "provenance": {"source": "direct_quote_fallback_only"},
        "authority": samsung_widget_contract.ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": samsung_widget_contract.METRIC_CONTRACT,
    }


def _fallback_exit_advisory(observed_at: datetime, market_session: str) -> dict:
    return {
        "state": "DATA_WAIT",
        "raw_state": "DATA_WAIT",
        "session": market_session,
        "reference_exit_price": None,
        "peak_price": None,
        "peak_drawdown_pct": None,
        "broken_support": None,
        "reasons": [],
        "unmet_conditions": ["collector_snapshot_missing_or_stale"],
        "valid_until": observed_at.replace(
            hour=20, minute=0, second=0, microsecond=0
        ).isoformat(),
        "observed_at": observed_at.isoformat(),
        "source_quality": {
            "status": "BLOCKED",
            "issues": ["collector_snapshot_missing_or_stale"],
        },
        "holding_independent": True,
        "future_prediction": False,
        "authority": samsung_widget_contract.ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": samsung_widget_contract.METRIC_CONTRACT,
    }


@samsung_price_widget_bp.get("/api/widget/samsung-price")
def get_samsung_price():
    """Return quote/advisory data plus a best-effort display-only position."""
    if not _authorized_request():
        return _error_response("unauthorized", 401)

    observed_at = _now_kst()
    collector_snapshot = _fresh_collector_snapshot(observed_at)
    if collector_snapshot is not None:
        token = kiwoom_utils.get_cached_kiwoom_token(CONF)
        response_payload = dict(collector_snapshot)
        response_payload["position"] = _cached_samsung_position(token, observed_at)
        response_payload["websocket_comparison"] = _websocket_price_comparison(
            reference_price=_parse_positive_price(
                response_payload.get("current_price")
            ),
            observed_at=observed_at,
        )
        result = jsonify(response_payload)
        result.headers["Cache-Control"] = "no-store"
        return result

    token = kiwoom_utils.get_cached_kiwoom_token(CONF)
    if not token:
        return _error_response("shared_token_unavailable", 503)

    request_code, market_venue, market_session = _quote_route_for_observed_at(
        observed_at
    )
    session_start = {
        "krx_like_premarket": _NXT_PREMARKET_START,
        "nxt_aftermarket": _NXT_AFTERMARKET_START,
        "krx_or_closed": _KRX_SESSION_START,
    }[market_session]
    quote_payload = _cached_direct_quote(
        token,
        request_code=request_code,
        observed_at=observed_at,
    )
    if quote_payload is None:
        return _error_response("kiwoom_quote_rejected", 503)

    current_price = _parse_positive_price(quote_payload.get("cur_prc"))
    if not current_price:
        return _error_response("kiwoom_price_missing", 503)

    day_low_price = _parse_positive_price(quote_payload.get("low_pric"))
    day_low_delta = (
        current_price - day_low_price
        if day_low_price is not None and current_price >= day_low_price
        else None
    )
    day_low_delta_pct = (
        round((day_low_delta / day_low_price) * 100, 2)
        if day_low_delta is not None and day_low_price > 0
        else None
    )
    completed_minute_closes: list[tuple[str, int]] = []
    minute_trends = {"1m": "unavailable", "3m": "unavailable", "5m": "unavailable"}
    minute_trend_at = None
    minute_trend = "unavailable"

    result = jsonify(
        {
            "status": "ok",
            "symbol": _SAMSUNG_CODE,
            "name": _SAMSUNG_NAME,
            "current_price": current_price,
            "day_low_price": day_low_price,
            "day_low_delta": day_low_delta,
            "day_low_delta_pct": day_low_delta_pct,
            "minute_trend": minute_trend,
            "minute_trends": minute_trends,
            "minute_trend_basis": "collector_unavailable_quote_only",
            "minute_trends_basis": (
                "collector_unavailable_no_advisory_trend_synthesized"
            ),
            "minute_chart_basis": "20_completed_1m_closes",
            "minute_chart": [
                {
                    "time_kst": f"{source_time[8:10]}:{source_time[10:12]}",
                    "close": close,
                }
                for source_time, close in completed_minute_closes
            ],
            "minute_trend_at_kst": (
                f"{minute_trend_at[:8]}T{minute_trend_at[8:10]}:{minute_trend_at[10:12]}"
                f":{minute_trend_at[12:14]}+09:00"
                if minute_trend_at
                else None
            ),
            "observed_at_kst": observed_at.isoformat(),
            "market_venue": market_venue,
            "market_cohort": (
                "PREMARKET_KRX_LIKE"
                if market_session == "krx_like_premarket"
                else market_venue
            ),
            "market_session": market_session,
            "minute_session_start_kst": session_start.strftime("%H:%M"),
            "quote_request_code": request_code,
            "source": f"kiwoom_ka10001_{market_venue.lower()}_quote_only_fallback",
            "token_mode": "shared_cache_only",
            "position": _cached_samsung_position(token, observed_at),
            "advisory": _fallback_advisory(
                observed_at,
                samsung_widget_contract.session_context(observed_at).name,
            ),
            "exit_advisory": _fallback_exit_advisory(
                observed_at,
                samsung_widget_contract.session_context(observed_at).name,
            ),
            "websocket_comparison": _websocket_price_comparison(
                reference_price=current_price,
                observed_at=observed_at,
            ),
        }
    )
    result.headers["Cache-Control"] = "no-store"
    return result


@samsung_price_widget_bp.post("/api/widget/samsung-order")
def submit_samsung_manual_order():
    """Submit an explicit operator-confirmed Samsung order.

    The collector snapshot, not the Windows payload, owns price, venue and
    session.  A separate order key prevents read-only widget credentials from
    becoming broker authority.
    """
    if not _authorized_order_request():
        return _error_response("order_unauthorized", 401)
    if not request.is_json:
        return _error_response("json_body_required", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error_response("invalid_json_body", 400)

    observed_at = _now_kst()
    executor = _manual_order_executor()
    try:
        duplicate = executor.existing_response(
            client_request_id=body.get("client_request_id"), now=observed_at
        )
    except ValueError as exc:
        return _error_response(str(exc), 400)
    except RuntimeError as exc:
        return _error_response(str(exc), 503)
    if duplicate is not None:
        return _manual_order_response(duplicate)

    snapshot = _fresh_manual_order_snapshot(observed_at)
    if snapshot is None:
        return _error_response("fresh_active_session_snapshot_required", 409)
    context = samsung_widget_contract.session_context(observed_at)
    reference_price = _parse_positive_price(snapshot.get("current_price"))
    snapshot_observed_at = samsung_widget_contract.snapshot_observed_at(snapshot)
    if reference_price is None or snapshot_observed_at is None:
        return _error_response("fresh_active_session_snapshot_required", 409)

    displayed_raw = body.get("displayed_price")
    if isinstance(displayed_raw, bool):
        return _error_response("displayed_price_required", 400)
    try:
        displayed_price = int(displayed_raw)
    except (TypeError, ValueError):
        return _error_response("displayed_price_required", 400)
    if displayed_price <= 0:
        return _error_response("displayed_price_required", 400)
    maximum_drift = 2 * max(
        get_tick_size(displayed_price), get_tick_size(reference_price)
    )
    if abs(displayed_price - reference_price) > maximum_drift:
        return _error_response("displayed_price_moved_refresh_required", 409)

    try:
        result_payload = executor.execute(
            side=body.get("side"),
            quantity=body.get("quantity"),
            client_request_id=body.get("client_request_id"),
            reference_price=reference_price,
            market_venue=context.market_venue,
            session=context.name,
            snapshot_observed_at=snapshot_observed_at.isoformat(),
            now=observed_at,
        )
    except ValueError as exc:
        return _error_response(str(exc), 400)
    except RuntimeError as exc:
        return _error_response(str(exc), 503)

    return _manual_order_response(result_payload)
