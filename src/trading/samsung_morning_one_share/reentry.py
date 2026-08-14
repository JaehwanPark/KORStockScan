"""Second Samsung morning SOR episode gated by the completed opening episode."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.order.episode_quantity import SUPPORTED_OWNED_LEG_QUANTITIES
from src.trading.order.regular_two_leg_machine import (
    KST,
    SamsungRegularTwoLegMachine,
    _fresh_state,
)
from src.trading.samsung_morning_one_share.machine import (
    DEFAULT_STATE_PATH as DEFAULT_FIRST_EPISODE_STATE_PATH,
)
from src.trading.samsung_morning_one_share.policy import (
    DEFAULT_REENTRY_POLICY,
    MorningReentryPolicy,
)
from src.utils.constants import DATA_DIR

DEFAULT_REENTRY_STATE_PATH = (
    DATA_DIR / "runtime" / "samsung_morning_sor_reentry_state.json"
)
SAFE_PRECONDITION_BLOCK_REASONS = frozenset(
    {
        "first_episode_both_legs_not_complete",
        "first_episode_completion_provenance_missing",
    }
)


def _first_episode_payload_complete(payload: object, target_date: date) -> bool:
    if not isinstance(payload, dict):
        return False
    legs = payload.get("legs")
    try:
        position_qty = int(payload.get("position_qty", 0) or 0)
        legs_complete = (
            isinstance(legs, list)
            and len(legs) == 2
            and all(
                isinstance(leg, dict)
                and leg.get("status") == "COMPLETE"
                and int(leg.get("target_filled_qty", 0) or 0) > 0
                and int(leg.get("target_filled_qty", 0) or 0)
                == int(leg.get("buy_filled_qty", leg.get("target_filled_qty", 0)) or 0)
                for leg in legs
            )
        )
    except (TypeError, ValueError):
        return False
    return bool(
        payload.get("trade_date") == target_date.isoformat()
        and payload.get("status") == "COMPLETE"
        and position_qty == 0
        and legs_complete
    )


def prior_reentry_allows_new_first_episode(
    path: Path = DEFAULT_REENTRY_STATE_PATH, *, target_date: date
) -> tuple[bool, str]:
    """Fail closed when an older re-entry ledger can still own an order/position."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return True, "reentry_state_absent"
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"reentry_state_unreadable:{type(exc).__name__}"
    if not isinstance(payload, dict):
        return False, "reentry_state_invalid"
    trade_date = str(payload.get("trade_date") or "")
    if payload.get("schema") != "samsung_morning_sor_reentry_two_leg_state_v1":
        return False, "reentry_state_schema_invalid"
    try:
        parsed_trade_date = date.fromisoformat(trade_date)
    except ValueError:
        return False, "reentry_state_trade_date_invalid"
    if parsed_trade_date > target_date:
        return False, "reentry_state_future_date"
    if not isinstance(payload.get("attempt_consumed"), bool):
        return False, "reentry_state_attempt_contract_invalid"
    if trade_date == target_date.isoformat():
        return True, "same_date_reentry_state"
    try:
        position_qty = int(payload.get("position_qty", 0) or 0)
    except (TypeError, ValueError):
        return False, "prior_reentry_position_invalid"
    legs = payload.get("legs")
    owned_order_nos = payload.get("owned_order_nos", [])
    if not isinstance(owned_order_nos, list):
        return False, "prior_reentry_order_ledger_invalid"
    status = str(payload.get("status") or "")
    safe_status = status in {"READY", "COMPLETE", "NO_TRADE"}
    try:
        safe_legs = (
            isinstance(legs, list)
            and len(legs) == 2
            and all(
                isinstance(leg, dict)
                and leg.get("status") in {"COMPLETE", "NO_FILL"}
                and int(leg.get("quantity", 0) or 0) in SUPPORTED_OWNED_LEG_QUANTITIES
                for leg in legs
            )
        )
    except (TypeError, ValueError):
        return False, "prior_reentry_leg_contract_invalid"
    empty_terminal = (
        status in {"READY", "NO_TRADE"}
        and payload.get("attempt_consumed") is False
        and legs == []
        and owned_order_nos == []
    )
    safe_precondition_block = (
        status == "BLOCKED"
        and str(payload.get("blocked_reason") or "") in SAFE_PRECONDITION_BLOCK_REASONS
        and payload.get("attempt_consumed") is False
        and legs == []
        and owned_order_nos == []
    )
    completed_terminal = (
        status == "COMPLETE" and payload.get("attempt_consumed") is True and safe_legs
    )
    if position_qty == 0 and (
        (safe_status and (empty_terminal or completed_terminal))
        or safe_precondition_block
    ):
        return True, "prior_reentry_terminal_clear"
    return False, "prior_reentry_order_or_position_unresolved"


def runtime_ledgers_allow_service_start(
    *,
    first_episode_path: Path = DEFAULT_FIRST_EPISODE_STATE_PATH,
    reentry_path: Path = DEFAULT_REENTRY_STATE_PATH,
    target_date: date,
) -> tuple[bool, str]:
    clear, reason = prior_reentry_allows_new_first_episode(
        reentry_path, target_date=target_date
    )
    if not clear or reason != "same_date_reentry_state":
        return clear, reason
    try:
        reentry = json.loads(Path(reentry_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"reentry_state_unreadable:{type(exc).__name__}"
    if not isinstance(reentry, dict):
        return False, "reentry_state_invalid"
    if not reentry.get("attempt_consumed") and not reentry.get("legs"):
        return True, "same_date_reentry_not_armed"
    try:
        first = json.loads(Path(first_episode_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"first_episode_state_unreadable:{type(exc).__name__}"
    if not _first_episode_payload_complete(first, target_date):
        return False, "same_date_reentry_without_completed_first_episode"
    return True, "same_date_ledgers_consistent"


class SamsungMorningSORReentryMachine(SamsungRegularTwoLegMachine):
    """One bounded two-leg SOR episode after both opening legs complete."""

    LEG_IDS = (
        "confirmation_close_minus_1tick",
        "confirmation_close_minus_2ticks",
    )

    def __init__(
        self,
        *,
        gateway,
        state_path: Path = DEFAULT_REENTRY_STATE_PATH,
        first_episode_state_path: Path = DEFAULT_FIRST_EPISODE_STATE_PATH,
        policy: MorningReentryPolicy = DEFAULT_REENTRY_POLICY,
        live_enabled: bool = False,
        ownership_source: Callable[
            [object], str
        ] = manual_control_operator_exclusion_source,
    ) -> None:
        self.first_episode_state_path = Path(first_episode_state_path)
        self._eligible_after: datetime | None = None
        super().__init__(
            gateway=gateway,
            state_path=state_path,
            policy=policy,
            strategy_name="morning_sor_reentry",
            schema="samsung_morning_sor_reentry_two_leg_state_v1",
            legacy_schema="samsung_morning_sor_reentry_state_v0",
            live_enabled=live_enabled,
            ownership_source=ownership_source,
        )

    def _first_episode_completion(self, now: datetime) -> tuple[datetime | None, str]:
        try:
            payload = json.loads(
                self.first_episode_state_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            return None, f"first_episode_state_unreadable:{type(exc).__name__}"
        if not isinstance(payload, dict):
            return None, "first_episode_state_invalid"
        if not _first_episode_payload_complete(payload, now.date()):
            return None, "first_episode_both_legs_not_complete"
        expected_ids = {"base_plus_1tick", "base"}
        completion_by_leg: dict[str, datetime] = {}
        for leg in payload.get("legs") or []:
            if not isinstance(leg, dict):
                continue
            leg_id = str(leg.get("leg_id") or "")
            if leg_id not in expected_ids:
                continue
            try:
                completed_at = datetime.fromisoformat(
                    str(leg.get("target_filled_at") or "")
                )
            except ValueError:
                continue
            if completed_at.tzinfo is not None:
                completion_by_leg[leg_id] = completed_at.astimezone(KST)
        for event in payload.get("audit") or []:
            if (
                not isinstance(event, dict)
                or event.get("action") != "target_fill_confirmed"
            ):
                continue
            leg_id = str(event.get("leg_id") or "")
            if leg_id not in expected_ids or leg_id in completion_by_leg:
                continue
            try:
                completed_at = datetime.fromisoformat(str(event.get("at_kst") or ""))
            except ValueError:
                continue
            if completed_at.tzinfo is not None:
                completion_by_leg[leg_id] = completed_at.astimezone(KST)
        if set(completion_by_leg) != expected_ids:
            return None, "first_episode_completion_provenance_missing"
        if any(value.date() != now.date() for value in completion_by_leg.values()):
            return None, "first_episode_completion_date_mismatch"
        completed_at = max(completion_by_leg.values())
        return completed_at, "ready"

    def _source(self, now: datetime):
        source = self.gateway.completed_sor_minute_bars(trade_date=now.date(), now=now)
        if not source.source_ok:
            return source
        eligible_after = self._eligible_after
        if eligible_after is None:
            prerequisite = self._state.get("prerequisite") or {}
            try:
                eligible_after = datetime.fromisoformat(
                    str(prerequisite.get("first_episode_completed_at") or "")
                ).astimezone(KST)
            except (TypeError, ValueError):
                return replace(
                    source, source_ok=False, bars=(), error="prerequisite_time_missing"
                )
        return replace(
            source,
            bars=tuple(bar for bar in source.bars if bar.timestamp > eligible_after),
        )

    def _record(self, now: datetime, action: str, **fields: object) -> None:
        if action == "two_leg_entry_armed":
            features = dict(self._state.get("signal_features") or {})
            features.update(
                {
                    "schema": "samsung_morning_sor_reentry_signal_features_v1",
                    "family": "low_hold_reclaim_passive_split",
                    "confirmation_bars": int(self.policy.confirmation_bars),
                    "reclaim_ticks": int(self.policy.reclaim_ticks),
                    "entry_offset_ticks": int(self.policy.entry_offset_ticks),
                    "prerequisite": dict(self._state.get("prerequisite") or {}),
                }
            )
            self._state["signal_features"] = features
        super()._record(now, action, **fields)

    def _validate_state_contract(self, now: datetime) -> bool:
        if not super()._validate_state_contract(now):
            return False
        if self._state.get("legs") or self._state.get("attempt_consumed"):
            prerequisite = self._state.get("prerequisite")
            if not isinstance(prerequisite, dict) or not str(
                prerequisite.get("first_episode_completed_at") or ""
            ):
                self._block(now, "reentry_prerequisite_contract_invalid")
                return False
        return True

    def _roll_safe_precondition_block(self, now: datetime) -> None:
        """Roll only a prior-day, zero-exposure prerequisite miss.

        The base machine intentionally keeps every BLOCKED state terminal.  A
        re-entry episode is different only for the narrow case where the first
        episode never completed and therefore no re-entry order could exist.
        """

        if (
            not self._state
            or self._state.get("trade_date") == now.date().isoformat()
            or self._state.get("status") != "BLOCKED"
        ):
            return
        clear, reason = prior_reentry_allows_new_first_episode(
            self.state_path, target_date=now.date()
        )
        if not clear or reason != "prior_reentry_terminal_clear":
            return
        prior_date = str(self._state.get("trade_date") or "")
        prior_reason = str(self._state.get("blocked_reason") or "")
        self._state = _fresh_state(now, self.schema)
        self._record(
            now,
            "daily_state_initialized_from_safe_precondition_block",
            prior_trade_date=prior_date,
            prior_blocked_reason=prior_reason,
        )

    def _retry_safe_same_day_completion_provenance_block(self, now: datetime) -> None:
        """Retry only an unarmed same-day block repaired by durable provenance."""

        if (
            not self._state
            or self._state.get("schema") != self.schema
            or self._state.get("trade_date") != now.date().isoformat()
            or self._state.get("status") != "BLOCKED"
            or self._state.get("blocked_reason")
            != "first_episode_completion_provenance_missing"
            or self._state.get("attempt_consumed") is not False
            or self._state.get("legs") != []
            or self._state.get("owned_order_nos") != []
        ):
            return
        try:
            position_qty = int(self._state.get("position_qty", 0) or 0)
        except (TypeError, ValueError):
            return
        if position_qty != 0:
            return
        completed_at, reason = self._first_episode_completion(now)
        if completed_at is None or reason != "ready":
            return
        self._state = _fresh_state(now, self.schema)
        self._record(
            now,
            "same_day_completion_provenance_block_recovered",
            first_episode_completed_at=completed_at.isoformat(),
        )

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        self._roll_safe_precondition_block(now)
        self._retry_safe_same_day_completion_provenance_block(now)
        return super().run_once(now)

    def _consider_entry(self, now: datetime) -> dict:
        completed_at, reason = self._first_episode_completion(now)
        if completed_at is None:
            return self._block(now, reason)
        self._eligible_after = completed_at
        self._state["prerequisite"] = {
            "first_episode_state": str(self.first_episode_state_path),
            "first_episode_status": "COMPLETE",
            "first_episode_completed_at": completed_at.isoformat(),
            "required_completed_leg_count": 2,
        }
        self._save()
        if now.time() < self.policy.scan_start:
            self._state.update(
                {
                    "last_action": "waiting_for_morning_sor_reentry_window",
                    "blocked_reason": "",
                }
            )
            self._save()
            return self.snapshot()
        return super()._consider_entry(now)
