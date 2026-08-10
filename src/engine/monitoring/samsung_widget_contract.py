"""Lightweight schema and session contract for the Samsung advisory widget."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")

SAMSUNG_CODE = "005930"
SAMSUNG_NAME = "삼성전자"
SK_HYNIX_CODE = "000660"

SNAPSHOT_SCHEMA_VERSION = 1
ADVISORY_AUTHORITY = "widget_advisory_only"
SNAPSHOT_MAX_AGE_SEC = 25
ADVISORY_STATES = frozenset(
    {"DATA_WAIT", "WATCH", "ENTRY_CAUTION", "ENTRY_READY", "NO_CHASE", "AVOID"}
)
ACTIONABLE_ADVISORY_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
EXIT_ADVISORY_STATES = frozenset(
    {"DATA_WAIT", "EXIT_WATCH", "EXIT_CAUTION", "EXIT_READY", "EXIT_CANCELLED"}
)
ACTIONABLE_EXIT_ADVISORY_STATES = frozenset({"EXIT_CAUTION", "EXIT_READY"})
TREND_ASSESSMENT_STATES = frozenset(
    {
        "TREND_DATA_WAIT",
        "TREND_UP",
        "TREND_STABLE",
        "TREND_MIXED",
        "TREND_DOWN",
    }
)
INTRADAY_REGIME_STATES = frozenset({"unavailable", "not_down", "down"})
DEFAULT_SNAPSHOT_PATH = Path("data/runtime/samsung_widget_advisory_snapshot.json")
DEFAULT_OBSERVATION_DIR = Path("data/report/samsung_widget_advisory_observation")

NXT_PREMARKET_START = datetime_time(8, 0)
NXT_PREMARKET_END = datetime_time(8, 50)
KRX_START = datetime_time(9, 0)
KRX_END = datetime_time(15, 30)
NXT_AFTERMARKET_START = datetime_time(15, 40)
NXT_AFTERMARKET_END = datetime_time(20, 0)
PREMARKET_AUXILIARY_END = datetime_time(9, 30)

METRIC_CONTRACT = {
    "metric_role": "source_quality_gate",
    "decision_authority": ADVISORY_AUTHORITY,
    "window_policy": "intraday_current_session",
    "sample_floor": "session_minimum_completed_bars",
    "primary_decision_metric": "none_operator_advisory",
    "source_quality_gate": (
        "fresh_coherent_quote_bbo_completed_1m_and_dynamic_daily_anchors"
    ),
    "forbidden_uses": [
        "real_order_submission",
        "account_or_quantity_decision",
        "trading_runtime_threshold",
        "provider_route_change",
        "bot_process_control",
        "automatic_live_promotion",
    ],
}

INTRADAY_REGIME_METRIC_CONTRACT = {
    "metric_role": "diagnostic_signal_observation",
    "decision_authority": ADVISORY_AUTHORITY,
    "window_policy": "current_session_completed_contiguous_15_to_30m",
    "sample_floor": "15_completed_contiguous_1m_bars",
    "primary_decision_metric": "none_operator_advisory",
    "source_quality_gate": "completed_contiguous_current_session_1m_ohlcv",
    "forbidden_uses": [
        "standalone_positive_order_authority",
        "account_or_quantity_decision",
        "provider_route_change",
        "bot_process_control",
        "automatic_live_promotion",
    ],
}


def as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=KST)
    return value.astimezone(KST)


def previous_krx_trading_date(value: date) -> date:
    candidate = value - timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate -= timedelta(days=1)
    return candidate


@dataclass(frozen=True)
class SessionContext:
    name: str
    market_venue: str
    market_cohort: str
    request_code: str
    start: datetime_time | None
    end: datetime_time | None
    minimum_bars: int
    active: bool


def session_context(observed_at: datetime) -> SessionContext:
    now = as_kst(observed_at)
    if not is_krx_trading_day(now.date()):
        return SessionContext(
            "CLOSED", "KRX", "KRX", SAMSUNG_CODE, None, None, 0, False
        )
    clock = now.time().replace(tzinfo=None)
    if NXT_PREMARKET_START <= clock < NXT_PREMARKET_END:
        return SessionContext(
            "NXT_PREMARKET",
            "NXT",
            "PREMARKET_KRX_LIKE",
            f"{SAMSUNG_CODE}_NX",
            NXT_PREMARKET_START,
            NXT_PREMARKET_END,
            10,
            True,
        )
    if NXT_PREMARKET_END <= clock < KRX_START:
        return SessionContext(
            "SESSION_TRANSITION", "KRX", "KRX", SAMSUNG_CODE, None, KRX_START, 0, False
        )
    if KRX_START <= clock < KRX_END:
        return SessionContext(
            "KRX_REGULAR",
            "KRX",
            "KRX",
            SAMSUNG_CODE,
            KRX_START,
            KRX_END,
            3,
            True,
        )
    if KRX_END <= clock < NXT_AFTERMARKET_START:
        return SessionContext(
            "SESSION_TRANSITION",
            "NXT",
            "NXT",
            f"{SAMSUNG_CODE}_NX",
            None,
            NXT_AFTERMARKET_START,
            0,
            False,
        )
    if NXT_AFTERMARKET_START <= clock < NXT_AFTERMARKET_END:
        return SessionContext(
            "NXT_AFTERMARKET",
            "NXT",
            "NXT",
            f"{SAMSUNG_CODE}_NX",
            NXT_AFTERMARKET_START,
            NXT_AFTERMARKET_END,
            5,
            True,
        )
    return SessionContext("CLOSED", "KRX", "KRX", SAMSUNG_CODE, None, None, 0, False)


def legacy_market_session(context: SessionContext) -> str:
    if context.name == "NXT_PREMARKET":
        return "krx_like_premarket"
    if context.name == "NXT_AFTERMARKET":
        return "nxt_aftermarket"
    return "krx_or_closed"


def load_snapshot(path: Path = DEFAULT_SNAPSHOT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def snapshot_is_fresh(
    payload: dict[str, Any],
    *,
    now: datetime | None = None,
    max_age_sec: int = SNAPSHOT_MAX_AGE_SEC,
) -> bool:
    if payload.get("status") != "ok":
        return False
    observed_at = snapshot_observed_at(payload)
    if observed_at is None:
        return False
    age = (as_kst(now or datetime.now(KST)) - observed_at).total_seconds()
    return 0 <= age <= max_age_sec


def _aware_datetime(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").strip())
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def snapshot_observed_at(payload: dict[str, Any]) -> datetime | None:
    return _aware_datetime(payload.get("observed_at_kst"))


def advisory_contract_is_valid(
    advisory: object,
    *,
    snapshot_observed_at: datetime,
    context: SessionContext,
    evaluated_at: datetime | None = None,
    max_clock_skew_sec: float = 1.0,
) -> bool:
    """Validate the actionable payload at the API trust boundary.

    Snapshot freshness alone is insufficient: a producer defect must not be
    able to pair a fresh outer timestamp with an expired or stale actionable
    advisory.
    """
    if not isinstance(advisory, dict):
        return False
    state = str(advisory.get("state") or "")
    raw_state = str(advisory.get("raw_state") or state)
    if state not in ADVISORY_STATES or raw_state not in ADVISORY_STATES:
        return False
    if (
        advisory.get("authority") != ADVISORY_AUTHORITY
        or advisory.get("session") != context.name
        or advisory.get("runtime_effect") is not False
        or advisory.get("actual_order_submitted") is not False
        or advisory.get("broker_order_forbidden") is not True
    ):
        return False
    trend_assessment = advisory.get("trend_assessment")
    if trend_assessment is not None and (
        not isinstance(trend_assessment, dict)
        or trend_assessment.get("state") not in TREND_ASSESSMENT_STATES
        or trend_assessment.get("future_prediction") is not False
    ):
        return False
    intraday_regime = advisory.get("intraday_regime")
    if intraday_regime is not None and (
        not isinstance(intraday_regime, dict)
        or intraday_regime.get("state") not in INTRADAY_REGIME_STATES
        or intraday_regime.get("future_prediction") is not False
    ):
        return False
    outer_observed_at = as_kst(snapshot_observed_at)
    advisory_observed_at = _aware_datetime(advisory.get("observed_at"))
    valid_until = _aware_datetime(advisory.get("valid_until"))
    if advisory_observed_at is None or valid_until is None:
        return False
    if abs((outer_observed_at - advisory_observed_at).total_seconds()) > max(
        0.0, float(max_clock_skew_sec)
    ):
        return False
    if valid_until < as_kst(evaluated_at or outer_observed_at):
        return False

    entry_low = advisory.get("entry_price_low")
    entry_high = advisory.get("entry_price_high")
    entry_values_are_ints = (
        isinstance(entry_low, int)
        and not isinstance(entry_low, bool)
        and isinstance(entry_high, int)
        and not isinstance(entry_high, bool)
    )
    if state in ACTIONABLE_ADVISORY_STATES:
        source_quality = advisory.get("source_quality")
        return bool(
            entry_values_are_ints
            and entry_low > 0
            and entry_high >= entry_low
            and isinstance(source_quality, dict)
            and source_quality.get("status") == "PASS"
        )
    return entry_low is None and entry_high is None


def exit_advisory_contract_is_valid(
    exit_advisory: object,
    *,
    snapshot_observed_at: datetime,
    context: SessionContext,
    evaluated_at: datetime | None = None,
    max_clock_skew_sec: float = 1.0,
) -> bool:
    """Validate the holding-independent exit observation at the API boundary."""
    if not isinstance(exit_advisory, dict):
        return False
    state = str(exit_advisory.get("state") or "")
    if state not in EXIT_ADVISORY_STATES:
        return False
    if (
        exit_advisory.get("authority") != ADVISORY_AUTHORITY
        or exit_advisory.get("session") != context.name
        or exit_advisory.get("runtime_effect") is not False
        or exit_advisory.get("actual_order_submitted") is not False
        or exit_advisory.get("broker_order_forbidden") is not True
        or exit_advisory.get("holding_independent") is not True
        or exit_advisory.get("future_prediction") is not False
    ):
        return False
    outer_observed_at = as_kst(snapshot_observed_at)
    advisory_observed_at = _aware_datetime(exit_advisory.get("observed_at"))
    valid_until = _aware_datetime(exit_advisory.get("valid_until"))
    if advisory_observed_at is None or valid_until is None:
        return False
    if abs((outer_observed_at - advisory_observed_at).total_seconds()) > max(
        0.0, float(max_clock_skew_sec)
    ):
        return False
    if valid_until < as_kst(evaluated_at or outer_observed_at):
        return False
    source_quality = exit_advisory.get("source_quality")
    if state in ACTIONABLE_EXIT_ADVISORY_STATES:
        price_fields = (
            exit_advisory.get("peak_price"),
            exit_advisory.get("broken_support"),
            exit_advisory.get("reference_exit_price"),
        )
        return bool(
            isinstance(source_quality, dict)
            and source_quality.get("status") == "PASS"
            and all(
                isinstance(value, int) and not isinstance(value, bool) and value > 0
                for value in price_fields
            )
        )
    return isinstance(source_quality, dict)
