"""Read-only Samsung Electronics quote endpoint for the Windows desktop widget.

The endpoint consumes only the AWS server's existing shared Kiwoom token
cache.  It deliberately has no token-issue, token-refresh, order, account,
or bot-process control path.
"""

from __future__ import annotations

import hmac
import math
import os
from datetime import datetime, time as datetime_time
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, jsonify, request

from src.engine.monitoring import samsung_widget_contract
from src.engine.sniper_config import CONF
from src.trading.order.tick_utils import get_tick_size
from src.utils import kiwoom_utils

samsung_price_widget_bp = Blueprint("samsung_price_widget", __name__)

_WIDGET_ACCESS_KEY_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY"
_WIDGET_ACCESS_KEY_FILE_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE"
_WIDGET_ACCESS_KEY_HEADER = "X-KORStockScan-Widget-Key"
_WIDGET_SNAPSHOT_PATH_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH"
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
    if (path, api_id) != ("/api/dostk/stkinfo", "ka10001"):
        return None
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


def _snapshot_path() -> Path:
    configured = os.getenv(_WIDGET_SNAPSHOT_PATH_ENV, "").strip()
    return (
        Path(configured)
        if configured
        else samsung_widget_contract.DEFAULT_SNAPSHOT_PATH
    )


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


@samsung_price_widget_bp.get("/api/widget/samsung-price")
def get_samsung_price():
    """Return the fresh collector snapshot or a quote-only safe fallback."""
    if not _authorized_request():
        return _error_response("unauthorized", 401)

    observed_at = _now_kst()
    collector_snapshot = _fresh_collector_snapshot(observed_at)
    if collector_snapshot is not None:
        result = jsonify(collector_snapshot)
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
            "advisory": _fallback_advisory(
                observed_at,
                samsung_widget_contract.session_context(observed_at).name,
            ),
        }
    )
    result.headers["Cache-Control"] = "no-store"
    return result
