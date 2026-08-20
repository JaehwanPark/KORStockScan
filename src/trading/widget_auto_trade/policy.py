"""Verified dated execution policies for the widget auto-trade owner.

Only a fully verified policy whose source date precedes its effective date can
be loaded.  Policy files never submit orders by themselves; the existing
widget auto-trader remains the sole execution owner and retains every broker,
freshness, ownership, quantity, and global BUY-pause guard.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from src.utils.constants import PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day
from src.trading.order.episode_quantity import EPISODE_LEG_QUANTITY

POLICY_SCHEMA = "widget_auto_trade_policy_v1"
POLICY_AUTHORITY = "postclose_widget_auto_trade_calibration_v1"
POLICY_FILE_PREFIX = "widget_auto_trade_policy"
DEFAULT_POLICY_DIR = PROJECT_ROOT / "data/runtime/widget_auto_trade_policy"
WIDGET_AUTO_TRADE_LEG_QUANTITY = EPISODE_LEG_QUANTITY
CUMULATIVE_RESEARCH_GATE_SYMBOLS = frozenset({"034020", "042660"})
STATIC_WIDGET_AUTO_TRADE_SYMBOLS = frozenset(
    {"005930", *CUMULATIVE_RESEARCH_GATE_SYMBOLS}
)
SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL = {
    "005930": "observe_only_no_forced_sell",
    "034020": "sell_own_filled_quantity",
    "042660": "sell_own_filled_quantity",
}
CUMULATIVE_RESEARCH_START_DATE = date(2026, 8, 12)
CUMULATIVE_RESEARCH_MIN_QUALIFIED_DATES = 40
CUMULATIVE_RESEARCH_QUALIFICATION_CONTRACT = (
    "KRX_trading_date;KRX_REGULAR/KRX;source_quality_PASS_rows>=300;"
    "first_PASS_observation<=09:30;last_PASS_observation>=15:20"
)
SUPPORTED_SESSIONS = frozenset({"NXT_PREMARKET", "KRX_REGULAR", "NXT_AFTERMARKET"})
SUPPORTED_VENUES = frozenset({"KRX", "NXT"})
SUPPORTED_ENTRY_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
SESSION_VENUES = {
    "NXT_PREMARKET": "NXT",
    "KRX_REGULAR": "KRX",
    "NXT_AFTERMARKET": "NXT",
}


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _bounded_int(value: object, *, minimum: int, maximum: int) -> int | None:
    parsed = _positive_int(value)
    return parsed if parsed is not None and minimum <= parsed <= maximum else None


def _valid_clock(value: object) -> str | None:
    text = str(value or "").strip()
    parts = text.split(":")
    if len(parts) != 3:
        return None
    try:
        hour, minute, second = (int(part) for part in parts)
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return None
    return f"{hour:02d}:{minute:02d}:{second:02d}"


def _validated_session_policy(
    payload: object,
    *,
    symbol: str,
    session: str,
    policy_id: str,
    effective_date: date,
    source_target_date: date,
    policy_path: Path,
    evidence_report_path: str,
    research_gate: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or payload.get("enabled") is not True:
        return None
    venue = str(payload.get("market_venue") or "")
    entry_states_raw = payload.get("allowed_entry_states")
    entry_states = (
        tuple(str(value) for value in entry_states_raw)
        if isinstance(entry_states_raw, list)
        else ()
    )
    add_triggers_raw = payload.get("add_trigger_bps_from_initial_fill")
    if not isinstance(add_triggers_raw, list):
        return None
    try:
        add_triggers = tuple(int(value) for value in add_triggers_raw)
    except (TypeError, ValueError):
        return None
    target_bps = _bounded_int(
        payload.get("take_profit_bps_from_equal_share_average"),
        minimum=20,
        maximum=300,
    )
    max_entries = _bounded_int(
        payload.get("max_completed_entries_per_day"), minimum=1, maximum=5
    )
    cooldown = _bounded_int(
        payload.get("reentry_cooldown_minutes"), minimum=1, maximum=120
    )
    leg_qty = _bounded_int(
        payload.get("leg_quantity_each"),
        minimum=WIDGET_AUTO_TRADE_LEG_QUANTITY,
        maximum=WIDGET_AUTO_TRADE_LEG_QUANTITY,
    )
    entry_cutoff = _valid_clock(payload.get("new_entry_cutoff_time"))
    force_flat = payload.get("force_flat_at_session_end") is True
    force_exit_time = _valid_clock(payload.get("force_exit_time"))
    expected_source_exit_action = SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL.get(symbol)
    if (
        session not in SUPPORTED_SESSIONS
        or venue not in SUPPORTED_VENUES
        or SESSION_VENUES.get(session) != venue
        or not entry_states
        or any(value not in SUPPORTED_ENTRY_STATES for value in entry_states)
        or len(set(entry_states)) != len(entry_states)
        or len(add_triggers) > 2
        or any(value >= 0 for value in add_triggers)
        or any(
            later >= earlier for earlier, later in zip(add_triggers, add_triggers[1:])
        )
        or target_bps is None
        or max_entries is None
        or cooldown is None
        or leg_qty is None
        or entry_cutoff is None
        or (force_flat and force_exit_time is None)
        or (not force_flat and force_exit_time is not None)
        or (payload.get("overnight_forbidden") is True and not force_flat)
        or (
            force_flat
            and force_exit_time is not None
            and entry_cutoff >= force_exit_time
        )
        or expected_source_exit_action is None
        or payload.get("source_final_exit_action") != expected_source_exit_action
        or str(payload.get("evidence_artifact") or "") != evidence_report_path
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_guard_bypass") is not False
    ):
        return None
    research_fields_match = True
    if symbol in CUMULATIVE_RESEARCH_GATE_SYMBOLS:
        research_fields_match = all(
            (
                str(payload.get("research_accumulation_start_date") or "")
                == str(research_gate.get("start_date") or ""),
                _positive_int(payload.get("research_qualified_observation_date_count"))
                == research_gate.get("qualified_observation_date_count"),
                _positive_int(
                    payload.get("research_minimum_qualified_observation_dates")
                )
                == research_gate.get("minimum_qualified_observation_dates"),
                str(payload.get("research_accumulation_gate_status") or "")
                == str(research_gate.get("status") or ""),
            )
        )
    new_entry_runtime_eligible = symbol not in CUMULATIVE_RESEARCH_GATE_SYMBOLS or (
        research_fields_match and research_gate.get("runtime_eligible") is True
    )
    return {
        "policy_id": policy_id,
        "symbol": symbol,
        "session": session,
        "market_venue": venue,
        "allowed_entry_sessions": (session,),
        "allowed_entry_venues": (venue,),
        "allowed_entry_states": entry_states,
        "leg_quantity_each": leg_qty,
        "add_trigger_bps_from_initial_fill": add_triggers,
        "take_profit_bps_from_equal_share_average": target_bps,
        "max_completed_entries_per_day": max_entries,
        "reentry_cooldown_minutes": cooldown,
        "new_entry_cutoff_time": entry_cutoff,
        "force_flat_at_session_end": force_flat,
        "force_exit_time": force_exit_time,
        "overnight_forbidden": payload.get("overnight_forbidden") is True,
        "source_final_exit_action": expected_source_exit_action,
        "additional_leg_window": "original_entry_session_only",
        "research_arm": payload.get("research_arm"),
        "evidence_window": payload.get("evidence_window"),
        "evidence_artifact": evidence_report_path,
        "policy_tier": payload.get("policy_tier"),
        "rollback_condition": payload.get("rollback_condition"),
        "effective_date": effective_date.isoformat(),
        "source_target_date": source_target_date.isoformat(),
        "policy_path": str(policy_path),
        "authority": POLICY_AUTHORITY,
        "new_entry_runtime_eligible": new_entry_runtime_eligible,
        "new_entry_runtime_block_reason": (
            None
            if new_entry_runtime_eligible
            else "cumulative_research_40_qualified_dates_incomplete"
        ),
        "research_accumulation_start_date": research_gate.get("start_date"),
        "research_qualified_observation_date_count": research_gate.get(
            "qualified_observation_date_count"
        ),
        "research_minimum_qualified_observation_dates": research_gate.get(
            "minimum_qualified_observation_dates"
        ),
        "research_accumulation_gate_status": research_gate.get("status"),
    }


def _research_gate_from_evidence(
    evidence: dict[str, Any],
    *,
    symbol: str,
    session: str,
    source_target_date: date,
) -> dict[str, Any]:
    if symbol not in CUMULATIVE_RESEARCH_GATE_SYMBOLS:
        return {"status": "not_required", "runtime_eligible": True}
    try:
        accumulation = evidence["symbols"][symbol]["sessions"][session][
            "research_accumulation"
        ]
    except (KeyError, TypeError):
        accumulation = None
    if not isinstance(accumulation, dict):
        return {
            "status": "missing",
            "start_date": CUMULATIVE_RESEARCH_START_DATE.isoformat(),
            "qualified_observation_date_count": 0,
            "minimum_qualified_observation_dates": (
                CUMULATIVE_RESEARCH_MIN_QUALIFIED_DATES
            ),
            "runtime_eligible": False,
        }
    qualified_dates = accumulation.get("qualified_observation_dates")
    qualified_dates = qualified_dates if isinstance(qualified_dates, list) else []
    try:
        parsed_dates = [date.fromisoformat(str(value)) for value in qualified_dates]
        count = int(accumulation.get("qualified_observation_date_count"))
        minimum = int(accumulation.get("minimum_qualified_observation_dates"))
    except (TypeError, ValueError):
        parsed_dates = []
        count = 0
        minimum = 0
    start_date = str(accumulation.get("start_date") or "")
    status = str(accumulation.get("status") or "")
    qualification_contract = str(accumulation.get("qualification_contract") or "")
    runtime_eligible = bool(
        start_date == CUMULATIVE_RESEARCH_START_DATE.isoformat()
        and minimum == CUMULATIVE_RESEARCH_MIN_QUALIFIED_DATES
        and count == len(set(parsed_dates))
        and count >= minimum
        and all(value >= CUMULATIVE_RESEARCH_START_DATE for value in parsed_dates)
        and all(value <= source_target_date for value in parsed_dates)
        and all(is_krx_trading_day(value) for value in parsed_dates)
        and status == "ready"
        and accumulation.get("runtime_eligible") is True
        and qualification_contract == CUMULATIVE_RESEARCH_QUALIFICATION_CONTRACT
    )
    return {
        "status": status or "invalid",
        "start_date": start_date or CUMULATIVE_RESEARCH_START_DATE.isoformat(),
        "qualified_observation_date_count": count,
        "minimum_qualified_observation_dates": minimum,
        "runtime_eligible": runtime_eligible,
    }


def _validated_payload(
    payload: object,
    *,
    observed_date: date,
    policy_path: Path,
) -> dict[str, dict[str, dict[str, Any]]] | None:
    if not isinstance(payload, dict):
        return None
    metric_contract = payload.get("metric_contract")
    symbols = payload.get("symbols")
    blocked_sessions = payload.get("blocked_sessions")
    has_runtime_policy = isinstance(symbols, dict) and bool(symbols)
    has_supported_block = bool(
        isinstance(blocked_sessions, dict)
        and any(
            symbol in STATIC_WIDGET_AUTO_TRADE_SYMBOLS
            and isinstance(sessions, dict)
            and sessions
            for symbol, sessions in blocked_sessions.items()
        )
    )
    source_quality_status = payload.get("source_quality_status")
    if (
        payload.get("schema") != POLICY_SCHEMA
        or payload.get("status") != "verified"
        or payload.get("authority") != POLICY_AUTHORITY
        or payload.get("runtime_effect") is not True
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not False
        or not isinstance(metric_contract, dict)
        or metric_contract.get("decision_authority") != POLICY_AUTHORITY
        or metric_contract.get("metric_role")
        != "bounded_widget_auto_trade_policy_calibration"
        or metric_contract.get("primary_decision_metric")
        != "source_quality_adjusted_ev_pct"
        or not metric_contract.get("window_policy")
        or not metric_contract.get("sample_floor")
        or not metric_contract.get("source_quality_gate")
        or not isinstance(metric_contract.get("forbidden_uses"), list)
        or source_quality_status not in {"PASS", "BLOCKED"}
        or (has_runtime_policy and source_quality_status != "PASS")
        or (source_quality_status == "BLOCKED" and not has_supported_block)
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
    evidence_path_text = str(payload.get("evidence_report_path") or "").strip()
    evidence_path = Path(evidence_path_text)
    if not evidence_path.is_absolute():
        evidence_path = PROJECT_ROOT / evidence_path
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(evidence, dict):
        return None
    verification = evidence.get("policy_verification")
    if (
        evidence.get("status") != "complete"
        or evidence.get("source_quality_status") != source_quality_status
        or evidence.get("target_date") != source_target_date.isoformat()
        or evidence.get("effective_date") != effective_date.isoformat()
        or not isinstance(verification, dict)
        or verification.get("status") != "pass"
        or Path(str(verification.get("policy_path") or "")) != policy_path
    ):
        return None
    policy_id = str(payload.get("policy_version") or "").strip()
    if not policy_id or not isinstance(symbols, dict):
        return None
    validated: dict[str, dict[str, dict[str, Any]]] = {}
    for symbol, symbol_payload in symbols.items():
        sessions = (
            symbol_payload.get("sessions") if isinstance(symbol_payload, dict) else None
        )
        if not isinstance(sessions, dict):
            continue
        for session, session_payload in sessions.items():
            research_gate = _research_gate_from_evidence(
                evidence,
                symbol=str(symbol),
                session=str(session),
                source_target_date=source_target_date,
            )
            session_policy = _validated_session_policy(
                session_payload,
                symbol=str(symbol),
                session=str(session),
                policy_id=policy_id,
                effective_date=effective_date,
                source_target_date=source_target_date,
                policy_path=policy_path,
                evidence_report_path=evidence_path_text,
                research_gate=research_gate,
            )
            if session_policy is not None:
                validated.setdefault(str(symbol), {})[str(session)] = session_policy
    blocked_sessions = payload.get("blocked_sessions")
    if isinstance(blocked_sessions, dict):
        for symbol, sessions in blocked_sessions.items():
            symbol_text = str(symbol)
            if symbol_text not in STATIC_WIDGET_AUTO_TRADE_SYMBOLS or not isinstance(
                sessions, dict
            ):
                continue
            for session, reason in sessions.items():
                session_name = str(session)
                venue = SESSION_VENUES.get(session_name)
                reason_text = str(reason or "").strip()
                if (
                    venue is None
                    or not reason_text
                    or session_name in validated.get(symbol_text, {})
                ):
                    continue
                research_gate = _research_gate_from_evidence(
                    evidence,
                    symbol=symbol_text,
                    session=session_name,
                    source_target_date=source_target_date,
                )
                validated.setdefault(symbol_text, {})[session_name] = {
                    "policy_id": policy_id,
                    "symbol": symbol_text,
                    "session": session_name,
                    "market_venue": venue,
                    "allowed_entry_sessions": (session_name,),
                    "allowed_entry_venues": (venue,),
                    "allowed_entry_states": tuple(SUPPORTED_ENTRY_STATES),
                    "leg_quantity_each": WIDGET_AUTO_TRADE_LEG_QUANTITY,
                    "new_entry_runtime_eligible": False,
                    "new_entry_runtime_block_reason": reason_text,
                    "source_final_exit_action": "observe_only_no_forced_sell",
                    "actual_order_submitted": False,
                    "broker_guard_bypass": False,
                    "research_arm": "blocked_no_runtime_apply",
                    "evidence_window": (
                        f"{source_target_date.isoformat()}_{source_target_date.isoformat()}"
                    ),
                    "evidence_artifact": evidence_path_text,
                    "policy_tier": "safety_or_evidence_block",
                    "effective_date": effective_date.isoformat(),
                    "source_target_date": source_target_date.isoformat(),
                    "policy_path": str(policy_path),
                    "authority": POLICY_AUTHORITY,
                    "research_accumulation_start_date": research_gate.get("start_date"),
                    "research_qualified_observation_date_count": research_gate.get(
                        "qualified_observation_date_count"
                    ),
                    "research_minimum_qualified_observation_dates": research_gate.get(
                        "minimum_qualified_observation_dates"
                    ),
                    "research_accumulation_gate_status": research_gate.get("status"),
                }
    return validated or None


class WidgetAutoTradePolicyLoader:
    """Resolve the newest verified policy effective for a trading date."""

    def __init__(
        self,
        policy_dir: Path = DEFAULT_POLICY_DIR,
        *,
        include_symbol_expansion: bool = True,
    ) -> None:
        self.policy_dir = policy_dir
        self.include_symbol_expansion = bool(include_symbol_expansion)
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

    def resolve_all(self, *, observed_date: date) -> dict[str, dict[str, Any]]:
        candidates: list[tuple[str, str, dict[str, dict[str, dict[str, Any]]]]] = []
        for path, payload in self._payloads():
            validated = _validated_payload(
                payload, observed_date=observed_date, policy_path=path
            )
            if validated is None:
                continue
            any_policy = next(
                session_policy
                for sessions in validated.values()
                for session_policy in sessions.values()
            )
            candidates.append(
                (
                    str(any_policy["effective_date"]),
                    str(any_policy["source_target_date"]),
                    validated,
                )
            )
        selected: dict[str, dict[str, Any]] = {}
        if candidates:
            _, _, selected = max(candidates, key=lambda item: (item[0], item[1]))
            selected = {symbol: dict(sessions) for symbol, sessions in selected.items()}
        if not self.include_symbol_expansion:
            return selected

        # This exact-date bridge is a distinct widget owner and cannot replace
        # an existing standard-policy symbol/session.  A conflict fails closed
        # for the expansion row rather than changing the incumbent owner.
        from src.engine.monitoring.widget_symbol_runtime_policy import (
            WidgetSymbolRuntimePolicyLoader,
        )

        expansion = WidgetSymbolRuntimePolicyLoader().resolve_all(
            observed_date=observed_date
        )
        for symbol, payload in expansion.items():
            execution = payload["execution_policy"]
            session = str(execution["session"])
            if session in selected.get(symbol, {}):
                continue
            selected.setdefault(symbol, {})[session] = {
                **execution,
                "policy_id": payload["policy_id"],
                "symbol": symbol,
                "research_arm": (
                    "symbol_specific_"
                    f"{payload['signal_policy']['segment']}_"
                    f"tp{payload['signal_policy']['target_bps']}"
                ),
                "evidence_window": payload["evidence_window"],
                "evidence_artifact": payload["evidence_artifact"],
                "policy_tier": "holdout_verified_symbol_specific",
                "rollback_condition": (
                    "exact_date_policy_missing; source-quality failure; "
                    "postclose holdout/EV gate failure; unresolved forced-flat"
                ),
                "effective_date": payload["effective_date"],
                "source_target_date": payload["source_target_date"],
                "policy_path": payload["policy_path"],
                "authority": payload["authority"],
                "new_entry_runtime_eligible": True,
                "new_entry_runtime_block_reason": None,
                "research_accumulation_gate_status": "holdout_verified",
            }
        return selected
