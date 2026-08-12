"""Shared fail-closed contract for calibrated widget-symbol collectors."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.monitoring.samsung_widget_contract import (
    ADVISORY_AUTHORITY,
    KRX_END,
    KRX_START,
    SNAPSHOT_MAX_AGE_SEC,
    SessionContext,
    as_kst,
    snapshot_observed_at,
)
from src.engine.monitoring.widget_symbol_runtime_policy import (
    POLICY_AUTHORITY,
    SYMBOLS,
)
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

SNAPSHOT_SCHEMA_VERSION = 1
DEFAULT_SNAPSHOT_DIR = DATA_DIR / "runtime" / "widget_symbol_advisory"
DEFAULT_OBSERVATION_DIR = DATA_DIR / "report" / "widget_symbol_advisory_observation"

METRIC_CONTRACT = {
    "metric_role": "calibrated_widget_symbol_signal_observation",
    "decision_authority": ADVISORY_AUTHORITY,
    "window_policy": "exact_policy_date_krx_regular_completed_1m",
    "sample_floor": "policy_lookback_completed_contiguous_1m_bars",
    "primary_decision_metric": "none_operator_advisory",
    "source_quality_gate": (
        "exact_date_verified_policy;fresh_quote_and_bbo;completed_contiguous_1m;"
        "same_symbol_KRX_provenance;auxiliary_component_freshness_provenance"
    ),
    "forbidden_uses": [
        "cross_symbol_signal_transfer",
        "policy_parameter_mutation",
        "account_or_quantity_decision",
        "token_issue_or_refresh",
        "provider_or_bot_control",
        "automatic_policy_promotion",
        "delayed_foreign_estimate_positive_promotion",
        "uncalibrated_auxiliary_entry_veto",
    ],
}


def _aware(value: object) -> datetime | None:
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


@dataclass(frozen=True)
class WidgetSymbolRuntimeContract:
    code: str
    name: str

    @property
    def STRATEGY_PROFILE(self) -> str:  # noqa: N802 - contract compatibility
        return f"CALIBRATED_WIDGET_SYMBOL_{self.code}_V1"

    @property
    def DEFAULT_SNAPSHOT_PATH(self) -> Path:  # noqa: N802
        return DEFAULT_SNAPSHOT_DIR / f"{self.code}.json"

    def session_context(self, observed_at: datetime) -> SessionContext:
        now = as_kst(observed_at)
        if not is_krx_trading_day(now.date()):
            return SessionContext(
                "CLOSED", "KRX", "KRX", self.code, None, None, 0, False
            )
        clock = now.time().replace(tzinfo=None)
        if KRX_START <= clock < KRX_END:
            return SessionContext(
                "KRX_REGULAR",
                "KRX",
                "KRX",
                self.code,
                KRX_START,
                KRX_END,
                3,
                True,
            )
        return SessionContext("CLOSED", "KRX", "KRX", self.code, None, None, 0, False)

    def load_snapshot(self, path: Path | None = None) -> dict[str, Any]:
        try:
            payload = json.loads(
                (path or self.DEFAULT_SNAPSHOT_PATH).read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def snapshot_is_fresh(
        self,
        payload: dict[str, Any],
        *,
        now: datetime,
        max_age_sec: int = SNAPSHOT_MAX_AGE_SEC,
        require_ok: bool = True,
    ) -> bool:
        expected = {"ok"} if require_ok else {"ok", "closed"}
        observed_at = snapshot_observed_at(payload)
        if payload.get("status") not in expected or observed_at is None:
            return False
        age = (as_kst(now) - observed_at).total_seconds()
        return 0 <= age <= max(1, int(max_age_sec))

    def advisory_event_contract_is_valid(
        self,
        event: object,
        *,
        expected_type: str,
        evaluated_at: datetime,
    ) -> bool:
        if not isinstance(event, dict) or expected_type not in {"ENTRY", "EXIT"}:
            return False
        now = as_kst(evaluated_at)
        observed_at = _aware(event.get("observed_at"))
        valid_until = _aware(event.get("valid_until"))
        event_id = str(event.get("event_id") or "")
        if not (
            event.get("event_type") == expected_type
            and event_id.startswith(
                f"{self.code}:{now.date().isoformat()}:{expected_type}:"
            )
            and event.get("strategy_profile") == self.STRATEGY_PROFILE
            and event.get("policy_authority") == POLICY_AUTHORITY
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
                and low is not None
                and high is not None
                and low <= high
                and support is not None
                and support <= high
                and target is not None
                and target > high
            )
        return bool(
            _positive_int(event.get("reference_exit_price")) is not None
            and event.get("reason") in {"target_observed", "confirmed_support_break"}
        )


CONTRACTS = {
    symbol: WidgetSymbolRuntimeContract(symbol, name)
    for symbol, name in SYMBOLS.items()
}
