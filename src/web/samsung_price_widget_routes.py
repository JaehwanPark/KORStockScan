"""Read-only Samsung Electronics quote endpoint for the Windows desktop widget.

The endpoint consumes only the AWS server's existing shared Kiwoom token
cache.  It deliberately has no token-issue, token-refresh, order, account,
or bot-process control path.
"""

from __future__ import annotations

import hmac
import os
from datetime import datetime, time as datetime_time
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, jsonify, request

from src.engine.sniper_config import CONF
from src.utils import kiwoom_utils

samsung_price_widget_bp = Blueprint("samsung_price_widget", __name__)

_WIDGET_ACCESS_KEY_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY"
_WIDGET_ACCESS_KEY_FILE_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE"
_WIDGET_ACCESS_KEY_HEADER = "X-KORStockScan-Widget-Key"
_SAMSUNG_CODE = "005930"
_SAMSUNG_NAME = "삼성전자"
_REQUEST_TIMEOUT_SEC = 5
_MINUTE_TREND_BAR_COUNT = 3
_MINUTE_CHART_BAR_COUNT = 20
_NXT_PREMARKET_START = datetime_time(hour=8)
_NXT_PREMARKET_END = datetime_time(hour=8, minute=50)
_NXT_AFTERMARKET_START = datetime_time(hour=15, minute=40)
_NXT_AFTERMARKET_END = datetime_time(hour=20)


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


def _quote_route_for_observed_at(observed_at: datetime) -> tuple[str, str, str]:
    """Select the explicit Kiwoom market code for the current display session."""
    normalized = (
        observed_at.replace(tzinfo=ZoneInfo("Asia/Seoul"))
        if observed_at.tzinfo is None
        else observed_at.astimezone(ZoneInfo("Asia/Seoul"))
    )
    clock = normalized.time()
    if _NXT_PREMARKET_START <= clock < _NXT_PREMARKET_END:
        return (
            f"{_SAMSUNG_CODE}_NX",
            "PREMARKET_KRX_LIKE",
            "krx_like_premarket",
        )
    if _NXT_AFTERMARKET_START <= clock < _NXT_AFTERMARKET_END:
        return f"{_SAMSUNG_CODE}_NX", "NXT", "nxt_aftermarket"
    return _SAMSUNG_CODE, "KRX", "krx_or_closed"


def _completed_minute_closes(
    rows: object, *, observed_at: datetime, limit: int
) -> list[tuple[str, int]]:
    """Return current-session completed minute closes, excluding the forming bar."""
    if not isinstance(rows, list):
        return []

    current_minute = observed_at.strftime("%Y%m%d%H%M")
    today = observed_at.strftime("%Y%m%d")
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
            or source_time[:12] >= current_minute
            or close_price is None
        ):
            continue
        completed_by_time[source_time[:14]] = close_price

    return sorted(completed_by_time.items())[-max(1, int(limit)) :]


def _classify_minute_trend(completed: list[tuple[str, int]]) -> tuple[str, str | None]:
    """Classify the last three completed one-minute closes."""
    completed = completed[-_MINUTE_TREND_BAR_COUNT:]
    if len(completed) < _MINUTE_TREND_BAR_COUNT:
        return "unavailable", None

    closes = [price for _, price in completed]
    latest_time = completed[-1][0]
    if closes[0] < closes[1] < closes[2]:
        return "up", latest_time
    if closes[0] > closes[1] > closes[2]:
        return "down", latest_time
    return "flat", latest_time


def _kiwoom_post(token: str, *, path: str, api_id: str, payload: dict):
    try:
        response = requests.post(
            kiwoom_utils.get_api_url(path),
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {token}",
                "api-id": api_id,
            },
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


def _authorized_request() -> bool:
    expected = _widget_access_key()
    supplied = request.headers.get(_WIDGET_ACCESS_KEY_HEADER, "").strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


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


@samsung_price_widget_bp.get("/api/widget/samsung-price")
def get_samsung_price():
    """Return a single fresh ka10001 quote without issuing or refreshing a token."""
    if not _authorized_request():
        return _error_response("unauthorized", 401)

    token = kiwoom_utils.get_cached_kiwoom_token(CONF)
    if not token:
        return _error_response("shared_token_unavailable", 503)

    observed_at = _now_kst()
    request_code, market_venue, market_session = _quote_route_for_observed_at(
        observed_at
    )
    quote_payload = _kiwoom_post(
        token,
        path="/api/dostk/stkinfo",
        api_id="ka10001",
        payload={"stk_cd": request_code},
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
    chart_payload = _kiwoom_post(
        token,
        path="/api/dostk/chart",
        api_id="ka10080",
        payload={"stk_cd": request_code, "tic_scope": "1", "upd_stkpc_tp": "1"},
    )
    completed_minute_closes = _completed_minute_closes(
        (chart_payload or {}).get("stk_min_pole_chart_qry"),
        observed_at=observed_at,
        limit=_MINUTE_CHART_BAR_COUNT,
    )
    minute_trend, minute_trend_at = _classify_minute_trend(completed_minute_closes)

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
            "minute_trend_basis": "3_completed_1m_closes",
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
            "market_session": market_session,
            "quote_request_code": request_code,
            "source": f"kiwoom_ka10001_{market_venue.lower()}",
            "token_mode": "shared_cache_only",
        }
    )
    result.headers["Cache-Control"] = "no-store"
    return result
