"""Samsung quote/advisory widget with explicit operator-confirmed orders.

The widget never stores a Kiwoom app key, secret key, or bearer token. Quote
and order access use separate AWS keys; every order requires a button click
and a confirmation dialog.
"""

from __future__ import annotations

import json
import math
import os
import threading
import tkinter as tk
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from tkinter import messagebox

APP_NAME = "SamsungPriceWidget"
POLL_INTERVAL_MS = 2_000
LOCAL_ADVISORY_MAX_AGE_SEC = 25
LOCAL_POSITION_MAX_AGE_SEC = 45
LOCAL_WS_COMPARISON_MAX_AGE_SEC = 7
WINDOW_SIZE = "190x220"
ACCESS_KEY_HEADER = "X-KORStockScan-Widget-Key"
ORDER_KEY_HEADER = "X-KORStockScan-Widget-Order-Key"
MAX_MANUAL_ORDER_QTY = 100

ADVISORY_STATES = {
    "DATA_WAIT",
    "WATCH",
    "ENTRY_CAUTION",
    "ENTRY_READY",
    "NO_CHASE",
    "AVOID",
}
TREND_ASSESSMENT_STATES = {
    "TREND_DATA_WAIT",
    "TREND_UP",
    "TREND_STABLE",
    "TREND_MIXED",
    "TREND_DOWN",
}
EXIT_ADVISORY_STATES = {
    "DATA_WAIT",
    "EXIT_WATCH",
    "EXIT_CAUTION",
    "EXIT_READY",
    "EXIT_CANCELLED",
}
ACTIVE_ORDER_SESSIONS = {"NXT_PREMARKET", "KRX_REGULAR", "NXT_AFTERMARKET"}


def default_config_path() -> Path:
    app_data = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or "."
    return Path(app_data) / "KORStockScan" / APP_NAME / "config.json"


@dataclass(frozen=True)
class WidgetSettings:
    endpoint_url: str
    access_key: str
    order_access_key: str = ""


def load_settings(config_path: Path | None = None) -> WidgetSettings:
    path = config_path or default_config_path()
    payload: dict = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        pass

    endpoint_url = str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_URL")
        or payload.get("endpoint_url")
        or ""
    ).strip()
    access_key = str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY")
        or payload.get("access_key")
        or ""
    ).strip()
    order_access_key = str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY")
        or payload.get("order_access_key")
        or ""
    ).strip()
    return WidgetSettings(
        endpoint_url=endpoint_url,
        access_key=access_key,
        order_access_key=order_access_key,
    )


def validate_settings(settings: WidgetSettings) -> str | None:
    if not settings.endpoint_url or not settings.access_key:
        return "설정 필요"
    if not settings.endpoint_url.lower().startswith("https://"):
        return "HTTPS URL 필요"
    return None


def order_endpoint_url(endpoint_url: str) -> str:
    parsed = urlsplit(str(endpoint_url or "").strip())
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError("invalid_order_endpoint")
    if not parsed.path.endswith("/api/widget/samsung-price"):
        raise ValueError("invalid_order_endpoint")
    path = parsed.path[: -len("samsung-price")] + "samsung-order"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


@dataclass(frozen=True)
class Quote:
    current_price: int
    websocket_price: int | None
    websocket_price_delta: int | None
    websocket_status: str
    websocket_age_ms: float | None
    websocket_route: str | None
    holding_quantity: int | None
    holding_average_price: int | None
    holding_status: str
    day_low_delta: int | None
    day_low_delta_pct: float | None
    minute_trend: str
    minute_trend_3m: str
    minute_trend_5m: str
    minute_chart: tuple[tuple[str, int], ...]
    market_venue: str
    market_cohort: str
    market_session: str
    order_session: str
    advisory_state: str
    trend_assessment_state: str
    entry_price_low: int | None
    entry_price_high: int | None
    advisory_reasons: tuple[str, ...]
    advisory_unmet_conditions: tuple[str, ...]
    external_risk_level: str
    external_quality: str
    observed_at: datetime | None
    advisory_observed_at: datetime | None
    advisory_valid_until: datetime | None
    exit_advisory_state: str
    reference_exit_price: int | None
    exit_peak_price: int | None
    exit_peak_drawdown_pct: float | None
    exit_broken_support: int | None
    exit_reasons: tuple[str, ...]
    exit_unmet_conditions: tuple[str, ...]


def _aware_datetime(value: object, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value or "").strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_{field}")
    return parsed


def _optional_positive_int(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"invalid_{field}")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed <= 0:
        raise ValueError(f"invalid_{field}")
    return parsed


def _optional_nonnegative_float(value: object, *, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"invalid_{field}")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"invalid_{field}")
    return parsed


def _string_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"invalid_{field}")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _parse_websocket_comparison(
    payload: object, *, reference_price: int, received_at: datetime | None
) -> tuple[int | None, int | None, str, float | None, str | None]:
    if not isinstance(payload, dict):
        return None, None, "UNAVAILABLE", None, None
    if (
        payload.get("authority") != "widget_ws_price_comparison_only"
        or payload.get("runtime_effect") is not False
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
        or payload.get("used_for_manual_order") is not False
    ):
        return None, None, "UNAVAILABLE", None, None
    if payload.get("status") != "OK":
        return None, None, "UNAVAILABLE", None, None
    route = str(payload.get("market_route") or "").strip().upper()
    if route not in {"KRX", "NXT", "SOR"}:
        return None, None, "UNAVAILABLE", None, None
    try:
        price = abs(int(payload.get("current_price")))
        declared_reference = abs(int(payload.get("reference_price")))
        declared_delta = int(payload.get("price_delta"))
        observed_at = _aware_datetime(
            payload.get("observed_at_kst"), field="websocket_observed_at_kst"
        )
    except (TypeError, ValueError):
        return None, None, "UNAVAILABLE", None, None
    local_received_at = received_at or datetime.now().astimezone()
    age_sec = (
        local_received_at.astimezone(observed_at.tzinfo) - observed_at
    ).total_seconds()
    if (
        price <= 0
        or declared_reference != reference_price
        or declared_delta != price - reference_price
        or age_sec < -2
        or age_sec > LOCAL_WS_COMPARISON_MAX_AGE_SEC
    ):
        return None, None, "UNAVAILABLE", None, None
    return price, declared_delta, "OK", max(0.0, age_sec) * 1000.0, route


def advisory_range_text(quote: Quote) -> str:
    """Render a range only for actionable states and explain its absence."""
    if quote.entry_price_low is not None and quote.entry_price_high is not None:
        if quote.entry_price_low == quote.entry_price_high:
            return f" · {quote.entry_price_low:,}원"
        return f" · {quote.entry_price_low:,}~{quote.entry_price_high:,}원"
    return {
        "DATA_WAIT": " · 가격대기",
        "WATCH": " · 가격대기",
        "NO_CHASE": " · 범위이탈",
        "AVOID": " · 범위없음",
    }.get(quote.advisory_state, "")


def _expected_advisory_sessions(
    market_venue: str, market_cohort: str, market_session: str
) -> set[str] | None:
    return {
        ("NXT", "PREMARKET_KRX_LIKE", "krx_like_premarket"): {"NXT_PREMARKET"},
        ("KRX", "KRX", "krx_or_closed"): {
            "KRX_REGULAR",
            "SESSION_TRANSITION",
            "CLOSED",
        },
        ("NXT", "NXT", "nxt_aftermarket"): {"NXT_AFTERMARKET"},
    }.get((market_venue, market_cohort, market_session))


def parse_quote_payload(
    payload: object, *, received_at: datetime | None = None
) -> Quote:
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise ValueError("quote_unavailable")
    value = payload.get("current_price")
    try:
        price = abs(int(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_price") from exc
    if price <= 0:
        raise ValueError("invalid_price")
    (
        websocket_price,
        websocket_price_delta,
        websocket_status,
        websocket_age_ms,
        websocket_route,
    ) = _parse_websocket_comparison(
        payload.get("websocket_comparison"),
        reference_price=price,
        received_at=received_at,
    )
    holding_quantity = None
    holding_average_price = None
    holding_status = "UNAVAILABLE"
    position_payload = payload.get("position")
    if isinstance(position_payload, dict) and (
        position_payload.get("authority") == "widget_account_position_display_only"
        and position_payload.get("symbol") == "005930"
        and position_payload.get("token_mode") == "shared_cache_only"
        and position_payload.get("account_query_read_only") is True
        and position_payload.get("runtime_effect") is False
        and position_payload.get("actual_order_submitted") is False
        and position_payload.get("position_data_used_for_order_quantity") is False
    ):
        candidate_status = str(position_payload.get("status") or "UNAVAILABLE").strip()
        if candidate_status == "OK":
            try:
                position_observed_at = _aware_datetime(
                    position_payload.get("observed_at_kst"),
                    field="position_observed_at_kst",
                )
                position_received_at = received_at or datetime.now().astimezone()
                position_received_at = position_received_at.astimezone(
                    position_observed_at.tzinfo
                )
                position_age_sec = (
                    position_received_at - position_observed_at
                ).total_seconds()
                candidate_quantity = int(position_payload.get("quantity"))
                average_raw = position_payload.get("average_price")
                candidate_average = (
                    int(average_raw) if average_raw is not None else None
                )
            except (TypeError, ValueError):
                position_age_sec = LOCAL_POSITION_MAX_AGE_SEC + 1
                candidate_quantity = -1
                candidate_average = None
            if (
                -2 <= position_age_sec <= LOCAL_POSITION_MAX_AGE_SEC
                and candidate_quantity >= 0
                and (
                    (candidate_quantity == 0 and candidate_average is None)
                    or (
                        candidate_quantity > 0
                        and candidate_average is not None
                        and candidate_average > 0
                    )
                )
            ):
                holding_status = "OK"
                holding_quantity = candidate_quantity
                holding_average_price = candidate_average
    low_delta = payload.get("day_low_delta")
    try:
        low_delta = int(low_delta) if low_delta is not None else None
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_day_low_delta") from exc
    low_delta_pct = payload.get("day_low_delta_pct")
    try:
        low_delta_pct = float(low_delta_pct) if low_delta_pct is not None else None
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_day_low_delta_pct") from exc
    raw_trends = payload.get("minute_trends")
    if raw_trends is not None and not isinstance(raw_trends, dict):
        raise ValueError("invalid_minute_trends")
    raw_trends = raw_trends or {}
    trends = {
        "1m": str(raw_trends.get("1m") or payload.get("minute_trend") or "unavailable"),
        "3m": str(raw_trends.get("3m") or "unavailable"),
        "5m": str(raw_trends.get("5m") or "unavailable"),
    }
    if any(
        trend not in {"up", "down", "flat", "unavailable"} for trend in trends.values()
    ):
        raise ValueError("invalid_minute_trends")
    market_venue = str(payload.get("market_venue") or "KRX").strip().upper()
    if market_venue not in {"KRX", "NXT"}:
        raise ValueError("invalid_market_venue")
    market_cohort = str(payload.get("market_cohort") or market_venue).strip().upper()
    if market_cohort not in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}:
        raise ValueError("invalid_market_cohort")
    market_session = str(payload.get("market_session") or "unknown").strip()
    raw_chart = payload.get("minute_chart", [])
    if not isinstance(raw_chart, list):
        raise ValueError("invalid_minute_chart")
    minute_chart: list[tuple[str, int]] = []
    for row in raw_chart[-20:]:
        if not isinstance(row, dict):
            raise ValueError("invalid_minute_chart")
        time_kst = str(row.get("time_kst") or "").strip()
        try:
            close = abs(int(row.get("close")))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_minute_chart") from exc
        if len(time_kst) != 5 or time_kst[2] != ":" or close <= 0:
            raise ValueError("invalid_minute_chart")
        minute_chart.append((time_kst, close))

    advisory_payload = payload.get("advisory")
    advisory_state = "DATA_WAIT"
    trend_assessment_state = "TREND_DATA_WAIT"
    entry_price_low = None
    entry_price_high = None
    advisory_reasons: tuple[str, ...] = ()
    advisory_unmet_conditions: tuple[str, ...] = ()
    external_risk_level = "DATA_LIMITED"
    external_quality = "UNAVAILABLE"
    observed_at = None
    advisory_observed_at = None
    advisory_valid_until = None
    order_session = "UNKNOWN"
    if advisory_payload is not None:
        if not isinstance(advisory_payload, dict):
            raise ValueError("invalid_advisory")
        if (
            advisory_payload.get("authority") != "widget_advisory_only"
            or advisory_payload.get("runtime_effect") is not False
            or advisory_payload.get("actual_order_submitted") is not False
            or advisory_payload.get("broker_order_forbidden") is not True
        ):
            raise ValueError("invalid_advisory_authority")
        advisory_state = str(advisory_payload.get("state") or "DATA_WAIT").strip()
        order_session = str(advisory_payload.get("session") or "UNKNOWN").strip()
        if advisory_state not in ADVISORY_STATES:
            raise ValueError("invalid_advisory_state")
        trend_assessment = advisory_payload.get("trend_assessment") or {}
        if not isinstance(trend_assessment, dict):
            raise ValueError("invalid_trend_assessment")
        trend_assessment_state = str(
            trend_assessment.get("state") or "TREND_DATA_WAIT"
        ).strip()
        if trend_assessment_state not in TREND_ASSESSMENT_STATES:
            raise ValueError("invalid_trend_assessment")
        entry_price_low = _optional_positive_int(
            advisory_payload.get("entry_price_low"), field="entry_price_low"
        )
        entry_price_high = _optional_positive_int(
            advisory_payload.get("entry_price_high"), field="entry_price_high"
        )
        if (
            entry_price_low is not None
            and entry_price_high is not None
            and entry_price_high < entry_price_low
        ):
            raise ValueError("invalid_entry_price_range")
        is_actionable = advisory_state in {"ENTRY_CAUTION", "ENTRY_READY"}
        if is_actionable and (entry_price_low is None or entry_price_high is None):
            raise ValueError("invalid_actionable_entry_price_range")
        if not is_actionable and (
            entry_price_low is not None or entry_price_high is not None
        ):
            raise ValueError("invalid_non_actionable_entry_price_range")
        observed_at = _aware_datetime(
            payload.get("observed_at_kst"), field="observed_at_kst"
        )
        advisory_observed_at = _aware_datetime(
            advisory_payload.get("observed_at"), field="advisory_observed_at"
        )
        advisory_valid_until = _aware_datetime(
            advisory_payload.get("valid_until"), field="advisory_valid_until"
        )
        if abs((observed_at - advisory_observed_at).total_seconds()) > 1.0:
            raise ValueError("advisory_observed_at_mismatch")
        local_received_at = received_at or datetime.now().astimezone()
        local_received_at = local_received_at.astimezone(observed_at.tzinfo)
        age_sec = (local_received_at - observed_at).total_seconds()
        if age_sec < -2 or age_sec > LOCAL_ADVISORY_MAX_AGE_SEC:
            raise ValueError("stale_advisory_snapshot")
        if advisory_valid_until < local_received_at:
            raise ValueError("expired_advisory")
        expected_sessions = _expected_advisory_sessions(
            market_venue, market_cohort, market_session
        )
        if (
            expected_sessions is None
            or advisory_payload.get("session") not in expected_sessions
            or (
                is_actionable
                and advisory_payload.get("session")
                not in {"NXT_PREMARKET", "KRX_REGULAR", "NXT_AFTERMARKET"}
            )
            or (
                advisory_payload.get("session") in {"SESSION_TRANSITION", "CLOSED"}
                and advisory_state != "DATA_WAIT"
            )
        ):
            raise ValueError("advisory_session_mismatch")
        advisory_reasons = _string_tuple(
            advisory_payload.get("reasons"), field="advisory_reasons"
        )
        advisory_unmet_conditions = _string_tuple(
            advisory_payload.get("unmet_conditions"),
            field="advisory_unmet_conditions",
        )
        external_risk = advisory_payload.get("external_risk") or {}
        if not isinstance(external_risk, dict):
            raise ValueError("invalid_external_risk")
        external_risk_level = str(external_risk.get("level") or "DATA_LIMITED").strip()
        if external_risk_level not in {
            "CLEAR",
            "CAUTION",
            "HOLD",
            "DATA_LIMITED",
        }:
            raise ValueError("invalid_external_risk")
        external_points = advisory_payload.get("external_points") or {}
        if isinstance(external_points, dict) and external_points:
            qualities = {
                str(point.get("quality") or "UNAVAILABLE")
                for point in external_points.values()
                if isinstance(point, dict)
            }
            if "STALE" in qualities:
                external_quality = "STALE"
            elif "UNAVAILABLE" in qualities:
                external_quality = "PARTIAL"
            elif "BEST_EFFORT_DELAYED" in qualities:
                external_quality = "DELAYED"
            elif qualities == {"MARKET_CLOSED"}:
                external_quality = "MARKET_CLOSED"
    exit_advisory_state = "DATA_WAIT"
    reference_exit_price = None
    exit_peak_price = None
    exit_peak_drawdown_pct = None
    exit_broken_support = None
    exit_reasons: tuple[str, ...] = ()
    exit_unmet_conditions: tuple[str, ...] = ()
    exit_payload = payload.get("exit_advisory")
    if exit_payload is not None:
        if not isinstance(exit_payload, dict):
            raise ValueError("invalid_exit_advisory")
        if (
            exit_payload.get("authority") != "widget_advisory_only"
            or exit_payload.get("runtime_effect") is not False
            or exit_payload.get("actual_order_submitted") is not False
            or exit_payload.get("broker_order_forbidden") is not True
            or exit_payload.get("holding_independent") is not True
            or exit_payload.get("future_prediction") is not False
        ):
            raise ValueError("invalid_exit_advisory_authority")
        exit_advisory_state = str(exit_payload.get("state") or "DATA_WAIT").strip()
        if exit_advisory_state not in EXIT_ADVISORY_STATES:
            raise ValueError("invalid_exit_advisory_state")
        reference_exit_price = _optional_positive_int(
            exit_payload.get("reference_exit_price"), field="reference_exit_price"
        )
        exit_peak_price = _optional_positive_int(
            exit_payload.get("peak_price"), field="exit_peak_price"
        )
        exit_broken_support = _optional_positive_int(
            exit_payload.get("broken_support"), field="exit_broken_support"
        )
        exit_peak_drawdown_pct = _optional_nonnegative_float(
            exit_payload.get("peak_drawdown_pct"),
            field="exit_peak_drawdown_pct",
        )
        exit_actionable = exit_advisory_state in {"EXIT_CAUTION", "EXIT_READY"}
        exit_source_quality = exit_payload.get("source_quality")
        if exit_actionable and (
            reference_exit_price is None
            or exit_peak_price is None
            or exit_broken_support is None
            or not isinstance(exit_source_quality, dict)
            or exit_source_quality.get("status") != "PASS"
        ):
            raise ValueError("invalid_actionable_exit_advisory")
        exit_observed_at = _aware_datetime(
            exit_payload.get("observed_at"), field="exit_advisory_observed_at"
        )
        exit_valid_until = _aware_datetime(
            exit_payload.get("valid_until"), field="exit_advisory_valid_until"
        )
        outer_observed_at = observed_at or _aware_datetime(
            payload.get("observed_at_kst"), field="observed_at_kst"
        )
        if abs((outer_observed_at - exit_observed_at).total_seconds()) > 1.0:
            raise ValueError("exit_advisory_observed_at_mismatch")
        local_received_at = received_at or datetime.now().astimezone()
        local_received_at = local_received_at.astimezone(outer_observed_at.tzinfo)
        age_sec = (local_received_at - outer_observed_at).total_seconds()
        if age_sec < -2 or age_sec > LOCAL_ADVISORY_MAX_AGE_SEC:
            raise ValueError("stale_exit_advisory_snapshot")
        if exit_valid_until < local_received_at:
            raise ValueError("expired_exit_advisory")
        expected_exit_sessions = _expected_advisory_sessions(
            market_venue, market_cohort, market_session
        )
        if (
            expected_exit_sessions is None
            or exit_payload.get("session") not in expected_exit_sessions
            or (
                exit_actionable
                and exit_payload.get("session")
                not in {"NXT_PREMARKET", "KRX_REGULAR", "NXT_AFTERMARKET"}
            )
            or (
                exit_payload.get("session") in {"SESSION_TRANSITION", "CLOSED"}
                and exit_advisory_state != "DATA_WAIT"
            )
        ):
            raise ValueError("exit_advisory_session_mismatch")
        exit_reasons = _string_tuple(exit_payload.get("reasons"), field="exit_reasons")
        exit_unmet_conditions = _string_tuple(
            exit_payload.get("unmet_conditions"), field="exit_unmet_conditions"
        )
    return Quote(
        current_price=price,
        websocket_price=websocket_price,
        websocket_price_delta=websocket_price_delta,
        websocket_status=websocket_status,
        websocket_age_ms=websocket_age_ms,
        websocket_route=websocket_route,
        holding_quantity=holding_quantity,
        holding_average_price=holding_average_price,
        holding_status=holding_status,
        day_low_delta=low_delta,
        day_low_delta_pct=low_delta_pct,
        minute_trend=trends["1m"],
        minute_trend_3m=trends["3m"],
        minute_trend_5m=trends["5m"],
        minute_chart=tuple(minute_chart),
        market_venue=market_venue,
        market_cohort=market_cohort,
        market_session=market_session,
        order_session=order_session,
        advisory_state=advisory_state,
        trend_assessment_state=trend_assessment_state,
        entry_price_low=entry_price_low,
        entry_price_high=entry_price_high,
        advisory_reasons=advisory_reasons,
        advisory_unmet_conditions=advisory_unmet_conditions,
        external_risk_level=external_risk_level,
        external_quality=external_quality,
        observed_at=observed_at,
        advisory_observed_at=advisory_observed_at,
        advisory_valid_until=advisory_valid_until,
        exit_advisory_state=exit_advisory_state,
        reference_exit_price=reference_exit_price,
        exit_peak_price=exit_peak_price,
        exit_peak_drawdown_pct=exit_peak_drawdown_pct,
        exit_broken_support=exit_broken_support,
        exit_reasons=exit_reasons,
        exit_unmet_conditions=exit_unmet_conditions,
    )


def primary_advisory_reason(quote: Quote) -> str:
    prefer_unmet = quote.advisory_state in {"DATA_WAIT", "WATCH"}
    primary = (
        quote.advisory_unmet_conditions if prefer_unmet else quote.advisory_reasons
    )
    secondary = (
        quote.advisory_reasons if prefer_unmet else quote.advisory_unmet_conditions
    )
    if primary:
        return primary[0]
    if secondary:
        return secondary[0]
    return "data_wait"


def fetch_current_price(settings: WidgetSettings, *, timeout_sec: int = 10) -> Quote:
    request = Request(
        settings.endpoint_url,
        headers={ACCESS_KEY_HEADER: settings.access_key, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except (URLError, OSError, ValueError) as exc:
        raise RuntimeError("연결 실패") from exc
    return parse_quote_payload(payload, received_at=datetime.now().astimezone())


def submit_manual_order(
    settings: WidgetSettings,
    *,
    side: str,
    quantity: int,
    displayed_price: int,
    client_request_id: str,
    timeout_sec: int = 10,
) -> dict:
    if not settings.order_access_key:
        raise RuntimeError("주문 키 필요")
    payload = json.dumps(
        {
            "side": side,
            "quantity": quantity,
            "displayed_price": displayed_price,
            "client_request_id": client_request_id,
        }
    ).encode("utf-8")
    request = Request(
        order_endpoint_url(settings.endpoint_url),
        data=payload,
        headers={
            ORDER_KEY_HEADER: settings.order_access_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_sec) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            response_payload = json.loads(exc.read().decode("utf-8"))
        except (OSError, ValueError, AttributeError):
            raise RuntimeError(f"HTTP {exc.code}") from exc
        if not isinstance(response_payload, dict):
            raise RuntimeError(f"HTTP {exc.code}") from exc
        if response_payload.get("authority") != "operator_widget_manual_order_v1":
            reason = str(response_payload.get("reason") or f"HTTP {exc.code}")
            raise RuntimeError(reason) from exc
    except (URLError, OSError, ValueError) as exc:
        raise RuntimeError("주문 연결 실패") from exc
    if not isinstance(response_payload, dict):
        raise RuntimeError("주문 응답 오류")
    if (
        response_payload.get("authority") != "operator_widget_manual_order_v1"
        or response_payload.get("client_request_id") != client_request_id
        or response_payload.get("side") != side
        or response_payload.get("quantity") != quantity
        or response_payload.get("status")
        not in {"accepted", "partial", "rejected", "ambiguous"}
    ):
        raise RuntimeError("주문 응답 검증 실패")
    return response_payload


class SamsungPriceWidget:
    def __init__(self, root: tk.Tk, settings: WidgetSettings) -> None:
        self.root = root
        self.settings = settings
        self.previous_price: int | None = None
        self.inflight = False
        self.order_inflight = False
        self.latest_quote: Quote | None = None
        self.last_success_at: datetime | None = None

        root.title("삼성전자 2초 비교")
        root.geometry(WINDOW_SIZE)
        root.minsize(190, 220)
        root.maxsize(190, 220)
        root.attributes("-topmost", True)
        root.configure(bg="#1e2430")
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        frame = tk.Frame(root, bg="#1e2430", padx=8, pady=6)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="삼성 005930 · 수동 실주문",
            fg="#dfe7f3",
            bg="#1e2430",
            font=("Malgun Gothic", 8, "bold"),
            anchor="w",
        ).pack(fill="x")
        self.price_label = tk.Label(
            frame,
            text="—",
            fg="#ffffff",
            bg="#1e2430",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        )
        self.price_label.pack(fill="x", pady=(2, 0))
        self.websocket_label = tk.Label(
            frame,
            text="WS: 수신 대기",
            fg="#8fa2b7",
            bg="#1e2430",
            font=("Malgun Gothic", 7),
            anchor="w",
        )
        self.websocket_label.pack(fill="x")
        self.position_label = tk.Label(
            frame,
            text="보유: 확인 대기",
            fg="#dfe7f3",
            bg="#1e2430",
            font=("Malgun Gothic", 8, "bold"),
            anchor="w",
        )
        self.position_label.pack(fill="x")
        self.low_label = tk.Label(
            frame,
            text="오늘 저가 대비: —",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
            anchor="w",
        )
        self.low_label.pack(fill="x")
        self.trend_label = tk.Label(
            frame,
            text="1분 — · 3분 — · 5분 —",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
            anchor="w",
        )
        self.trend_label.pack(fill="x")
        self.advisory_label = tk.Label(
            frame,
            text="진입 조언: 데이터 대기",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8, "bold"),
            anchor="w",
        )
        self.advisory_label.pack(fill="x")
        self.advisory_detail_label = tk.Label(
            frame,
            text="근거 — · 외부 DATA",
            fg="#8fa2b7",
            bg="#1e2430",
            font=("Malgun Gothic", 7),
            anchor="w",
        )
        self.advisory_detail_label.pack(fill="x")
        self.delta_label = tk.Label(
            frame,
            text="직전: —",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
            anchor="w",
        )
        self.delta_label.pack(fill="x")
        order_frame = tk.Frame(frame, bg="#1e2430")
        order_frame.pack(fill="x", pady=(3, 0))
        tk.Label(
            order_frame,
            text="수량",
            fg="#dfe7f3",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
        ).pack(side="left")
        self.quantity_var = tk.StringVar(value="1")
        self.quantity_entry = tk.Entry(
            order_frame,
            textvariable=self.quantity_var,
            width=4,
            justify="right",
            font=("Segoe UI", 9),
        )
        self.quantity_entry.pack(side="left", padx=(3, 5))
        self.buy_button = tk.Button(
            order_frame,
            text="매수",
            width=5,
            command=lambda: self._submit_order("BUY"),
            bg="#b13b3b",
            fg="#ffffff",
            activebackground="#d34a4a",
            activeforeground="#ffffff",
            font=("Malgun Gothic", 8, "bold"),
        )
        self.buy_button.pack(side="left", padx=(0, 3))
        self.sell_button = tk.Button(
            order_frame,
            text="매도",
            width=5,
            command=lambda: self._submit_order("SELL"),
            bg="#3568a8",
            fg="#ffffff",
            activebackground="#477fc3",
            activeforeground="#ffffff",
            font=("Malgun Gothic", 8, "bold"),
        )
        self.sell_button.pack(side="left")
        self.order_status_label = tk.Label(
            frame,
            text="주문 키 확인 중",
            fg="#8fa2b7",
            bg="#1e2430",
            font=("Malgun Gothic", 7),
            anchor="w",
        )
        self.order_status_label.pack(fill="x")
        self.status_label = tk.Label(
            frame,
            text="초기화 중",
            fg="#8fa2b7",
            bg="#1e2430",
            font=("Malgun Gothic", 7),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(2, 0))

    def start(self) -> None:
        problem = validate_settings(self.settings)
        if problem:
            self.status_label.configure(text=problem, fg="#ffb86c")
            self._set_order_buttons_enabled(False)
            return
        if not self.settings.order_access_key:
            self.order_status_label.configure(text="주문 키 없음 · 조회만 가능")
            self._set_order_buttons_enabled(False)
        else:
            self.order_status_label.configure(text="실주문 전 확인창 표시")
            self._set_order_buttons_enabled(False)
        self._refresh()
        self.root.after(1_000, self._watchdog)

    def _refresh(self) -> None:
        if self.inflight:
            self.root.after(POLL_INTERVAL_MS, self._refresh)
            return
        self.inflight = True
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self) -> None:
        try:
            quote = fetch_current_price(self.settings)
        except Exception as exc:  # keep the last successful price visible
            message = str(exc)
            self.root.after(0, lambda message=message: self._apply_error(message))
        else:
            self.root.after(0, lambda: self._apply_quote(quote))

    def _apply_quote(self, quote: Quote) -> None:
        self.last_success_at = datetime.now().astimezone()
        self.latest_quote = quote
        current_price = quote.current_price
        previous = self.previous_price
        self.previous_price = current_price
        self.price_label.configure(text=f"{current_price:,}원")
        if (
            quote.websocket_status == "OK"
            and quote.websocket_price is not None
            and quote.websocket_price_delta is not None
            and quote.websocket_route is not None
        ):
            ws_delta = quote.websocket_price_delta
            ws_sign = "+" if ws_delta > 0 else ""
            ws_color = (
                "#ff6b6b" if ws_delta > 0 else "#5ca9ff" if ws_delta < 0 else "#7bd88f"
            )
            self.websocket_label.configure(
                text=(
                    f"WS/{quote.websocket_route} {quote.websocket_price:,}원 "
                    f"· {ws_sign}{ws_delta:,} · "
                    f"{(quote.websocket_age_ms or 0.0) / 1000.0:.1f}초"
                ),
                fg=ws_color,
            )
        else:
            self.websocket_label.configure(text="WS: 수신 대기", fg="#8fa2b7")
        if quote.holding_status != "OK" or quote.holding_quantity is None:
            self.position_label.configure(text="보유: 확인불가", fg="#ffb86c")
        elif quote.holding_quantity == 0:
            self.position_label.configure(text="보유: 0주 · 평단 —", fg="#aab7c8")
        else:
            self.position_label.configure(
                text=(
                    f"보유: {quote.holding_quantity:,}주 · "
                    f"평단 {quote.holding_average_price:,}원"
                ),
                fg="#dfe7f3",
            )
        if quote.day_low_delta is None or quote.day_low_delta_pct is None:
            self.low_label.configure(text="오늘 저가 대비: —", fg="#aab7c8")
        else:
            self.low_label.configure(
                text=(
                    f"오늘 저가 대비: +{quote.day_low_delta:,}원 "
                    f"(+{quote.day_low_delta_pct:.2f}%)"
                ),
                fg="#ff6b6b" if quote.day_low_delta > 0 else "#aab7c8",
            )
        trend_symbols = {
            "up": "▲",
            "down": "▼",
            "flat": "─",
            "unavailable": "—",
        }
        displayed_trends = (
            quote.minute_trend,
            quote.minute_trend_3m,
            quote.minute_trend_5m,
        )
        trend_text = (
            f"1분 {trend_symbols[displayed_trends[0]]} · "
            f"3분 {trend_symbols[displayed_trends[1]]} · "
            f"5분 {trend_symbols[displayed_trends[2]]}"
        )
        available_trends = [
            trend for trend in displayed_trends if trend != "unavailable"
        ]
        trend_color = (
            "#ff6b6b"
            if available_trends and all(trend == "up" for trend in available_trends)
            else (
                "#5ca9ff"
                if available_trends
                and all(trend == "down" for trend in available_trends)
                else "#aab7c8"
            )
        )
        self.trend_label.configure(text=trend_text, fg=trend_color)
        self._apply_advisory(quote)
        if previous is None:
            self.delta_label.configure(text="직전: —", fg="#aab7c8")
        else:
            delta = current_price - previous
            color = "#ff6b6b" if delta > 0 else "#5ca9ff" if delta < 0 else "#aab7c8"
            sign = "+" if delta > 0 else ""
            self.delta_label.configure(text=f"직전: {sign}{delta:,}원", fg=color)
        venue_label = {
            "KRX": "KRX",
            "NXT": "NXT",
            "PREMARKET_KRX_LIKE": "PRE",
        }[quote.market_cohort]
        self.status_label.configure(
            text=(
                f"갱신 {datetime.now().strftime('%H:%M:%S')} · "
                f"{venue_label} · AWS 공유 토큰"
            ),
            fg="#8fa2b7",
        )
        self._set_order_buttons_enabled(
            bool(self.settings.order_access_key)
            and quote.order_session in ACTIVE_ORDER_SESSIONS
        )
        self._finish_cycle()

    def _apply_advisory(self, quote: Quote) -> None:
        if quote.exit_advisory_state in {
            "EXIT_CAUTION",
            "EXIT_READY",
            "EXIT_CANCELLED",
        }:
            exit_labels = {
                "EXIT_CAUTION": "청산 주의",
                "EXIT_READY": "청산 신호",
                "EXIT_CANCELLED": "청산 해제",
            }
            exit_colors = {
                "EXIT_CAUTION": "#ffb86c",
                "EXIT_READY": "#5ca9ff",
                "EXIT_CANCELLED": "#7bd88f",
            }
            price_text = (
                f" · {quote.reference_exit_price:,}원"
                if quote.reference_exit_price is not None
                else ""
            )
            self.advisory_label.configure(
                text=f"{exit_labels[quote.exit_advisory_state]}{price_text}",
                fg=exit_colors[quote.exit_advisory_state],
            )
            details = []
            if quote.exit_peak_drawdown_pct is not None:
                details.append(f"고점-{quote.exit_peak_drawdown_pct:.2f}%")
            if quote.exit_broken_support is not None:
                details.append(f"{quote.exit_broken_support:,} 이탈")
            if quote.exit_advisory_state == "EXIT_READY":
                details.append("3·5분하락")
            elif quote.exit_advisory_state == "EXIT_CANCELLED":
                details.append("지지회복/신저가없음")
            self.advisory_detail_label.configure(
                text=" · ".join(details) or "청산 관측 해제",
                fg=exit_colors[quote.exit_advisory_state],
            )
            return
        state_labels = {
            "DATA_WAIT": "데이터 대기",
            "WATCH": "관찰",
            "ENTRY_CAUTION": "조건부분(관측)",
            "ENTRY_READY": "조건충족(관측)",
            "NO_CHASE": "추격 금지",
            "AVOID": "진입 회피",
        }
        state_colors = {
            "DATA_WAIT": "#8fa2b7",
            "WATCH": "#f5c26b",
            "ENTRY_CAUTION": "#ffb86c",
            "ENTRY_READY": "#ff6b6b",
            "NO_CHASE": "#f5c26b",
            "AVOID": "#5ca9ff",
        }
        range_text = advisory_range_text(quote)
        self.advisory_label.configure(
            text=f"{state_labels[quote.advisory_state]}{range_text}",
            fg=state_colors[quote.advisory_state],
        )
        reason_labels = {
            "low_structure_confirmed": "저점지지",
            "vwap_or_resistance_reclaimed": "VWAP/저항회복",
            "rebound_volume_confirmed": "반등거래량",
            "three_five_minute_not_down": "3·5분방어",
            "relative_strength_not_weak": "상대강도",
            "spread_within_two_ticks": "호가양호",
            "price_more_than_30bp_above_support": "과열추격",
            "price_above_dynamic_two_tick_chase_limit": "과열추격",
            "resistance_reclaim_pullback_pending": "돌파눌림대기",
            "nxt_aftermarket_reclaim_structure_unconfirmed": "NXT저항/상승구조대기",
            "recovery_episode_armed": "반등구조",
            "recent_resistance_reclaimed": "저항회복",
            "pullback_within_two_ticks": "2틱눌림",
            "recent_rebound_volume_grace": "거래량유지",
            "confirmed_support_broken": "지지이탈",
            "minimum_bars_not_met": "관측축적",
            "completed_bars_missing": "분봉대기",
            "completed_bar_stale": "분봉지연",
            "bbo_stale": "호가지연",
            "quote_stale": "현재가지연",
            "regular_flow_unavailable": "수급지연",
            "foreign_and_program_flow_not_improving": "수급약화",
            "premarket_vwap_not_recovered": "프리VWAP미회복",
            "external_risk_hold": "외부위험",
            "relative_strength_unavailable": "상대데이터대기",
            "relative_strength_weak": "상대약세",
            "confirmed_support_missing": "지지대기",
            "entry_range_not_available_without_chasing": "추천범위없음",
            "recent_rest_prints_descending": "체결하락",
            "live_price_reversal_with_ask_pressure": "실시간반전",
            "awaiting_second_10s_confirmation": "2회확인중",
            "collector_snapshot_missing_or_stale": "수집기대기",
            "previous_day_ohlc_missing": "전일데이터대기",
            "bbo_missing_or_crossed": "호가대기",
        }
        source_reason = primary_advisory_reason(quote)
        reason_text = reason_labels.get(source_reason, source_reason[:14])
        external_labels = {
            "CLEAR": "외부양호",
            "CAUTION": "외부주의",
            "HOLD": "외부보류",
            "DATA_LIMITED": "외부지연",
        }
        quality_labels = {
            "DELAYED": "/DLY",
            "STALE": "/STALE",
            "PARTIAL": "/PART",
            "MARKET_CLOSED": "/CLOSED",
            "UNAVAILABLE": "",
        }
        trend_labels = {
            "TREND_DATA_WAIT": "추세대기",
            "TREND_UP": "확정봉상승",
            "TREND_STABLE": "확정봉안정",
            "TREND_MIXED": "확정봉혼조",
            "TREND_DOWN": "확정봉하락",
        }
        self.advisory_detail_label.configure(
            text=(
                f"{trend_labels[quote.trend_assessment_state]} · {reason_text} · "
                f"{external_labels[quote.external_risk_level]}"
                f"{quality_labels[quote.external_quality]}"
            ),
            fg="#8fa2b7",
        )

    def _set_order_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled and not self.order_inflight else "disabled"
        self.buy_button.configure(state=state)
        self.sell_button.configure(state=state)

    def _order_ui_available(self) -> bool:
        return bool(
            self.settings.order_access_key
            and self.latest_quote is not None
            and self.latest_quote.order_session in ACTIVE_ORDER_SESSIONS
        )

    def _validated_quantity(self) -> int | None:
        try:
            quantity = int(self.quantity_var.get().strip())
        except ValueError:
            quantity = 0
        if quantity <= 0 or quantity > MAX_MANUAL_ORDER_QTY:
            messagebox.showerror(
                "수량 오류", f"수량은 1~{MAX_MANUAL_ORDER_QTY}주로 입력하세요."
            )
            return None
        return quantity

    def _submit_order(self, side: str) -> None:
        if self.order_inflight:
            return
        if not self.settings.order_access_key:
            messagebox.showerror("주문 불가", "전용 주문 키가 설정되지 않았습니다.")
            return
        quote = self.latest_quote
        if quote is None or self.last_success_at is None:
            messagebox.showerror("주문 불가", "최신 가격을 먼저 수신해야 합니다.")
            return
        if quote.order_session not in ACTIVE_ORDER_SESSIONS:
            messagebox.showerror(
                "주문 불가", "현재는 주문 가능한 KRX/NXT 세션이 아닙니다."
            )
            return
        age_sec = (datetime.now().astimezone() - self.last_success_at).total_seconds()
        if age_sec > LOCAL_ADVISORY_MAX_AGE_SEC:
            messagebox.showerror(
                "주문 불가", "가격이 오래되었습니다. 갱신 후 다시 누르세요."
            )
            return
        quantity = self._validated_quantity()
        if quantity is None:
            return

        route = "SOR" if quote.market_venue == "KRX" else "NXT"
        if side == "BUY":
            upper_qty = (quantity + 1) // 2
            lower_qty = quantity // 2
            detail = f"{quote.current_price:,}원 × {upper_qty}주"
            if lower_qty:
                detail += f"\n현재가 -0.5% × {lower_qty}주"
            title = "삼성전자 실매수 확인"
            prompt = f"{detail}\n경로: {route}\n\n실주문을 접수할까요?"
        else:
            order_type = "시장가" if route == "SOR" else "현재가 지정가"
            title = "삼성전자 실매도 확인"
            prompt = (
                f"{quantity}주 · {order_type}\n"
                f"표시 현재가: {quote.current_price:,}원\n경로: {route}\n\n"
                "보유수량 자동확인 없이 실주문을 접수할까요?"
            )
        if not messagebox.askyesno(title, prompt, icon="warning"):
            return

        request_id = str(uuid.uuid4())
        self.order_inflight = True
        self._set_order_buttons_enabled(False)
        self.order_status_label.configure(text="실주문 접수 중…", fg="#ffb86c")
        threading.Thread(
            target=self._order_worker,
            kwargs={
                "side": side,
                "quantity": quantity,
                "displayed_price": quote.current_price,
                "request_id": request_id,
            },
            daemon=True,
        ).start()

    def _order_worker(
        self,
        *,
        side: str,
        quantity: int,
        displayed_price: int,
        request_id: str,
    ) -> None:
        try:
            response = submit_manual_order(
                self.settings,
                side=side,
                quantity=quantity,
                displayed_price=displayed_price,
                client_request_id=request_id,
            )
        except Exception as exc:
            message = str(exc)
            self.root.after(0, lambda message=message: self._apply_order_error(message))
        else:
            self.root.after(0, lambda: self._apply_order_result(response))

    def _apply_order_result(self, response: dict) -> None:
        status = str(response.get("status") or "")
        orders = response.get("orders") or []
        accepted = int(response.get("accepted_order_count") or 0)
        expected = int(response.get("expected_order_count") or 0)
        order_numbers = [
            str(order.get("order_no"))
            for order in orders
            if isinstance(order, dict) and order.get("order_no")
        ]
        if status in {"partial", "ambiguous"}:
            prefix = "부분접수" if status == "partial" else "접수상태 불명"
            text = f"{prefix} {accepted}/{expected} · 재주문 금지"
            self.order_status_label.configure(text=text, fg="#ffb86c")
            messagebox.showwarning(
                "broker 확인 필요",
                f"{text}\n주문번호: {', '.join(order_numbers) or '확인 필요'}",
            )
        elif status == "rejected":
            messages = [
                str(order.get("return_msg") or order.get("return_code") or "거절")
                for order in orders
                if isinstance(order, dict)
            ]
            text = "주문 거절"
            self.order_status_label.configure(text=text, fg="#ffb86c")
            messagebox.showerror("주문 거절", " · ".join(messages) or text)
        else:
            text = f"접수완료 {accepted}/{expected}"
            self.order_status_label.configure(text=text, fg="#7bd88f")
            messagebox.showinfo(
                "주문 접수",
                f"{text}\n주문번호: {', '.join(order_numbers) or '확인 필요'}",
            )
        self.order_inflight = False
        self._set_order_buttons_enabled(self._order_ui_available())

    def _apply_order_error(self, message: str) -> None:
        self.order_status_label.configure(text=f"주문 실패 · {message}", fg="#ffb86c")
        self.order_inflight = False
        self._set_order_buttons_enabled(self._order_ui_available())
        messagebox.showerror(
            "주문 확인 필요",
            f"{message}\n재주문 전 broker 주문내역을 확인하세요.",
        )

    def _apply_error(self, message: str) -> None:
        self._clear_advisory_for_stale()
        self._set_order_buttons_enabled(False)
        age_text = self._last_success_age_text()
        self.status_label.configure(
            text=f"{message} · 마지막 성공 {age_text}", fg="#ffb86c"
        )
        self._finish_cycle()

    def _last_success_age_text(self) -> str:
        if self.last_success_at is None:
            return "없음"
        age_sec = max(
            0, int((datetime.now().astimezone() - self.last_success_at).total_seconds())
        )
        return f"{age_sec}초 전"

    def _clear_advisory_for_stale(self) -> None:
        self.advisory_label.configure(text="데이터 대기", fg="#8fa2b7")
        self.advisory_detail_label.configure(
            text="신호 만료 · 관측용/자동주문 아님", fg="#8fa2b7"
        )

    def _watchdog(self) -> None:
        if self.last_success_at is not None:
            age_sec = (
                datetime.now().astimezone() - self.last_success_at
            ).total_seconds()
            if age_sec > LOCAL_ADVISORY_MAX_AGE_SEC:
                self._clear_advisory_for_stale()
                self._set_order_buttons_enabled(False)
                self.status_label.configure(
                    text=f"응답 지연 · 마지막 성공 {int(age_sec)}초 전",
                    fg="#ffb86c",
                )
        self.root.after(1_000, self._watchdog)

    def _finish_cycle(self) -> None:
        self.inflight = False
        self.root.after(POLL_INTERVAL_MS, self._refresh)


def main() -> None:
    root = tk.Tk()
    widget = SamsungPriceWidget(root, load_settings())
    widget.start()
    root.mainloop()


if __name__ == "__main__":
    main()
