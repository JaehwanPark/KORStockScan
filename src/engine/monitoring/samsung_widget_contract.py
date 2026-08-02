"""Lightweight schema and session contract for the Samsung advisory widget."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time as datetime_time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import holidays

KST = ZoneInfo("Asia/Seoul")

SAMSUNG_CODE = "005930"
SAMSUNG_NAME = "삼성전자"
SK_HYNIX_CODE = "000660"

SNAPSHOT_SCHEMA_VERSION = 1
ADVISORY_AUTHORITY = "widget_advisory_only"
SNAPSHOT_MAX_AGE_SEC = 25
DEFAULT_SNAPSHOT_PATH = Path("data/runtime/samsung_widget_advisory_snapshot.json")
DEFAULT_OBSERVATION_DIR = Path("data/report/samsung_widget_advisory_observation")

NXT_PREMARKET_START = datetime_time(8, 0)
NXT_PREMARKET_END = datetime_time(8, 50)
KRX_START = datetime_time(9, 0)
KRX_END = datetime_time(15, 30)
NXT_AFTERMARKET_START = datetime_time(15, 40)
NXT_AFTERMARKET_END = datetime_time(20, 0)
PREMARKET_AUXILIARY_END = datetime_time(9, 30)

KR_HOLIDAYS = holidays.KR()

METRIC_CONTRACT = {
    "metric_role": "source_quality_gate",
    "decision_authority": ADVISORY_AUTHORITY,
    "window_policy": "intraday_current_session",
    "sample_floor": "session_minimum_completed_bars",
    "primary_decision_metric": "none_operator_advisory",
    "source_quality_gate": "fresh_quote_bbo_completed_1m_and_dynamic_daily_anchors",
    "forbidden_uses": [
        "real_order_submission",
        "account_or_quantity_decision",
        "trading_runtime_threshold",
        "provider_route_change",
        "bot_process_control",
        "automatic_live_promotion",
    ],
}


def as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=KST)
    return value.astimezone(KST)


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
    if now.weekday() >= 5 or now.date() in KR_HOLIDAYS:
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
    observed_text = str(payload.get("observed_at_kst") or "").strip()
    try:
        observed_at = datetime.fromisoformat(observed_text)
    except (TypeError, ValueError):
        return False
    if observed_at.tzinfo is None:
        return False
    observed_at = observed_at.astimezone(KST)
    age = (as_kst(now or datetime.now(KST)) - observed_at).total_seconds()
    return 0 <= age <= max_age_sec
