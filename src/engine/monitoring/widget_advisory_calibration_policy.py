"""Load bounded, date-effective calibration for read-only widget advisories.

The policy affects only the widget promotion confirmation count.  It has no
account, order, quantity, provider, token, bot, or real-trading authority.
Malformed or future policies are ignored and the most recent valid policy is
carried forward automatically.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_POLICY_DIR = Path("data/runtime/widget_advisory_calibration")
POLICY_FILE_PREFIX = "widget_advisory_policy"
POLICY_SCHEMA = "widget_advisory_policy_v1"
POLICY_AUTHORITY = "widget_advisory_calibration_only"
DEFAULT_REQUIRED_CONFIRMATIONS = 2
MIN_REQUIRED_CONFIRMATIONS = 2
MAX_REQUIRED_CONFIRMATIONS = 3


def _bounded_confirmations(value: object) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if not MIN_REQUIRED_CONFIRMATIONS <= parsed <= MAX_REQUIRED_CONFIRMATIONS:
        return None
    return parsed


def default_selection(*, symbol: str, session: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "session": session,
        "required_actionable_confirmations": DEFAULT_REQUIRED_CONFIRMATIONS,
        "policy_version": "widget_advisory_default_v1",
        "effective_date": None,
        "source_target_date": None,
        "load_status": "default_no_valid_dated_policy",
        "authority": POLICY_AUTHORITY,
        "widget_runtime_effect": True,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _selection_from_payload(
    payload: object,
    *,
    symbol: str,
    session: str,
    observed_date: date,
) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    metric_contract = payload.get("metric_contract")
    if (
        payload.get("schema") != POLICY_SCHEMA
        or payload.get("status") != "verified"
        or not str(payload.get("policy_version") or "").strip()
        or payload.get("authority") != POLICY_AUTHORITY
        or payload.get("selected_axis") != "required_actionable_confirmations"
        or not isinstance(metric_contract, dict)
        or metric_contract.get("decision_authority") != POLICY_AUTHORITY
        or payload.get("widget_runtime_effect") is not True
        or payload.get("trading_runtime_effect") is not False
        or payload.get("runtime_effect") is not False
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
    ):
        return None
    try:
        effective_date = date.fromisoformat(str(payload.get("effective_date") or ""))
        source_target_date = date.fromisoformat(
            str(payload.get("source_target_date") or "")
        )
    except ValueError:
        return None
    if source_target_date >= effective_date or effective_date > observed_date:
        return None
    symbols = payload.get("symbols")
    symbol_policy = symbols.get(symbol) if isinstance(symbols, dict) else None
    sessions = (
        symbol_policy.get("sessions") if isinstance(symbol_policy, dict) else None
    )
    session_policy = sessions.get(session) if isinstance(sessions, dict) else None
    if not isinstance(session_policy, dict):
        return None
    confirmations = _bounded_confirmations(
        session_policy.get("required_actionable_confirmations")
    )
    if confirmations is None:
        return None
    return {
        "symbol": symbol,
        "session": session,
        "required_actionable_confirmations": confirmations,
        "policy_version": str(payload.get("policy_version") or ""),
        "effective_date": effective_date.isoformat(),
        "source_target_date": source_target_date.isoformat(),
        "load_status": "dated_policy_loaded",
        "decision": session_policy.get("decision"),
        "reason": session_policy.get("reason"),
        "authority": POLICY_AUTHORITY,
        "widget_runtime_effect": True,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


class WidgetCalibrationPolicyLoader:
    """Resolve the latest valid policy effective on an observation date."""

    def __init__(self, policy_dir: Path = DEFAULT_POLICY_DIR) -> None:
        self.policy_dir = policy_dir
        self._directory_mtime_ns: int | None = None
        self._cached_payloads: list[tuple[Path, object]] = []

    def _payloads(self) -> list[tuple[Path, object]]:
        try:
            directory_mtime_ns = self.policy_dir.stat().st_mtime_ns
        except OSError:
            directory_mtime_ns = -1
        if directory_mtime_ns == self._directory_mtime_ns:
            return self._cached_payloads
        payloads: list[tuple[Path, object]] = []
        for path in self.policy_dir.glob(f"{POLICY_FILE_PREFIX}_*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            payloads.append((path, payload))
        self._directory_mtime_ns = directory_mtime_ns
        self._cached_payloads = payloads
        return payloads

    def resolve(
        self,
        *,
        symbol: str,
        session: str,
        observed_date: date,
    ) -> dict[str, Any]:
        selections: list[dict[str, Any]] = []
        for path, payload in self._payloads():
            selection = _selection_from_payload(
                payload,
                symbol=symbol,
                session=session,
                observed_date=observed_date,
            )
            if selection is not None:
                selection["policy_path"] = str(path)
                selections.append(selection)
        if selections:
            return max(
                selections,
                key=lambda selection: (
                    str(selection["effective_date"]),
                    str(selection.get("source_target_date") or ""),
                    str(selection["policy_path"]),
                ),
            )
        return default_selection(symbol=symbol, session=session)
