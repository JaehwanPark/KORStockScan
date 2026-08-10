"""Contract and KRX session boundary for the Doosan advisory widget."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.monitoring.samsung_widget_contract import (
    ADVISORY_AUTHORITY,
    KRX_END,
    KRX_START,
    SNAPSHOT_MAX_AGE_SEC,
    SessionContext,
    advisory_contract_is_valid as _base_advisory_contract_is_valid,
    as_kst,
    exit_advisory_contract_is_valid as _base_exit_advisory_contract_is_valid,
    snapshot_observed_at,
)
from src.utils.market_day import is_krx_trading_day

DOOSAN_CODE = "034020"
DOOSAN_NAME = "두산에너빌리티"
SNAPSHOT_SCHEMA_VERSION = 1
DEFAULT_SNAPSHOT_PATH = Path("data/runtime/doosan_widget_advisory_snapshot.json")
DEFAULT_OBSERVATION_DIR = Path("data/report/doosan_widget_advisory_observation")

STRATEGY_PROFILE = "DOOSAN_FIRST_PULLBACK_V1"
EPISODE_POLICY = "multiple_non_overlapping_after_exit_and_new_bar_rearm"
MIN_SESSION_DRAWDOWN_PCT = -0.50
HIGH_CONFIDENCE_DRAWDOWN_PCT = -1.00
ENTRY_TARGET_PCT = 1.00
EXTENDED_RUNUP_TRIGGER_PCT = 0.70
EXTENDED_RUNUP_MIN_PULLBACK_TICKS = 3
LOSS_REENTRY_CONFIRMATION_WINDOW_SEC = 15 * 60
EXIT_EVENT_REASONS = frozenset(
    {
        "doosan_target_1pct_reached",
        "doosan_completed_close_below_entry_support",
    }
)

METRIC_CONTRACT = {
    "metric_role": "diagnostic_signal_observation",
    "decision_authority": ADVISORY_AUTHORITY,
    "window_policy": "krx_regular_multiple_rearmed_episodes_per_trade_date",
    "sample_floor": "three_completed_1m_bars_and_two_10s_confirmations",
    "primary_decision_metric": "none_operator_advisory",
    "source_quality_gate": (
        "fresh_coherent_quote_bbo_completed_1m_and_previous_day_ohlc;"
        "high_requires_observed_peer_kospi_flow_and_usdkrw_context"
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

KIWOOM_OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-07T10:44:54+09:00",
    "inspected_paths": [
        "kiwoom_docs/종목정보.md",
        "kiwoom_docs/시세.md",
        "kiwoom_docs/차트.md",
        "kiwoom_docs/업종.md",
        "kiwoom/specs.py",
        "kiwoom/core",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": [
        "ka10001",
        "ka10004",
        "ka10064",
        "ka10080",
        "ka10081",
        "ka20005",
        "ka90008",
    ],
}


def session_context(observed_at: datetime) -> SessionContext:
    """Expose only the KRX regular session as a decision-bearing session."""
    now = as_kst(observed_at)
    if not is_krx_trading_day(now.date()):
        return SessionContext("CLOSED", "KRX", "KRX", DOOSAN_CODE, None, None, 0, False)
    clock = now.time().replace(tzinfo=None)
    if KRX_START <= clock < KRX_END:
        return SessionContext(
            "KRX_REGULAR",
            "KRX",
            "KRX",
            DOOSAN_CODE,
            KRX_START,
            KRX_END,
            3,
            True,
        )
    return SessionContext("CLOSED", "KRX", "KRX", DOOSAN_CODE, None, None, 0, False)


def load_snapshot(path: Path = DEFAULT_SNAPSHOT_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def snapshot_is_fresh(
    payload: dict[str, Any],
    *,
    now: datetime,
    max_age_sec: int = SNAPSHOT_MAX_AGE_SEC,
    require_ok: bool = True,
) -> bool:
    if require_ok and payload.get("status") != "ok":
        return False
    if not require_ok and payload.get("status") not in {"ok", "closed"}:
        return False
    observed_at = snapshot_observed_at(payload)
    if observed_at is None:
        return False
    age_sec = (as_kst(now) - observed_at).total_seconds()
    return 0 <= age_sec <= max(1, int(max_age_sec))


def advisory_contract_is_valid(
    advisory: object,
    *,
    snapshot_time: datetime,
    context: SessionContext,
    evaluated_at: datetime,
) -> bool:
    if not isinstance(advisory, dict):
        return False
    return bool(
        advisory.get("strategy_profile") == STRATEGY_PROFILE
        and advisory.get("metric_contract") == METRIC_CONTRACT
        and _base_advisory_contract_is_valid(
            advisory,
            snapshot_observed_at=snapshot_time,
            context=context,
            evaluated_at=evaluated_at,
        )
    )


def exit_advisory_contract_is_valid(
    exit_advisory: object,
    *,
    snapshot_time: datetime,
    context: SessionContext,
    evaluated_at: datetime,
) -> bool:
    if not isinstance(exit_advisory, dict):
        return False
    return bool(
        exit_advisory.get("strategy_profile") == STRATEGY_PROFILE
        and exit_advisory.get("metric_contract") == METRIC_CONTRACT
        and _base_exit_advisory_contract_is_valid(
            exit_advisory,
            snapshot_observed_at=snapshot_time,
            context=context,
            evaluated_at=evaluated_at,
        )
    )


def _aware_timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    return as_kst(parsed) if parsed.tzinfo is not None else None


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def advisory_event_contract_is_valid(
    event: object,
    *,
    expected_type: str,
    evaluated_at: datetime,
) -> bool:
    """Validate a currently notify-able public entry or exit event."""
    if not isinstance(event, dict) or expected_type not in {"ENTRY", "EXIT"}:
        return False
    observed_at = _aware_timestamp(event.get("observed_at"))
    valid_until = _aware_timestamp(event.get("valid_until"))
    now = as_kst(evaluated_at)
    event_id = str(event.get("event_id") or "")
    expected_prefix = f"{DOOSAN_CODE}:{now.date().isoformat()}:{expected_type}:"
    if not (
        event.get("event_type") == expected_type
        and event_id.startswith(expected_prefix)
        and event.get("strategy_profile") == STRATEGY_PROFILE
        and event.get("authority") == ADVISORY_AUTHORITY
        and event.get("runtime_effect") is False
        and event.get("actual_order_submitted") is False
        and event.get("broker_order_forbidden") is True
        and event.get("source_quality_status") == "PASS"
        and observed_at is not None
        and observed_at.date() == now.date()
        and observed_at <= now
        and valid_until is not None
        and valid_until > now
    ):
        return False
    if expected_type == "ENTRY":
        low = _positive_int(event.get("entry_price_low"))
        high = _positive_int(event.get("entry_price_high"))
        support = _positive_int(event.get("structural_support"))
        target = _positive_int(event.get("target_price"))
        return bool(
            event.get("status") == "ACTIVE"
            and event.get("state") in {"ENTRY_CAUTION", "ENTRY_READY"}
            and event.get("signal_tier") in {"STANDARD", "HIGH"}
            and low is not None
            and high is not None
            and low <= high
            and support is not None
            and support <= high
            and target is not None
            and target > high
        )
    reference_exit = _positive_int(event.get("reference_exit_price"))
    entry_reference = _positive_int(event.get("entry_reference_price"))
    support = _positive_int(event.get("structural_support"))
    target = _positive_int(event.get("target_price"))
    return bool(
        reference_exit is not None
        and entry_reference is not None
        and support is not None
        and support <= entry_reference
        and target is not None
        and target > entry_reference
        and event.get("reason") in EXIT_EVENT_REASONS
    )
