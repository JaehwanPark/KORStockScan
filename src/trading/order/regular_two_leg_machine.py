"""Shared execution core for independent regular-session two-leg machines.

The caller owns the process, state path, policy, and broker gateway.  This module
only removes duplicated order-lifecycle code; it never shares state or orders
between the midday and afternoon strategies.
"""

from __future__ import annotations

import json
import os
import tempfile
import time as time_module
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Protocol
from zoneinfo import ZoneInfo

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.order.episode_quantity import (
    EPISODE_LEG_QUANTITY,
    EPISODE_TOTAL_QUANTITY,
    SUPPORTED_OWNED_LEG_QUANTITIES,
)
from src.trading.order.entry_liquidity_guard import (
    EntryLiquidityDecision,
    evaluate_entry_liquidity,
    unavailable_entry_liquidity_snapshot,
)
from src.trading.config.machine_entry_timing_policy import (
    ENTRY_CONFIRMATION_MAX_LATE_SEC,
    resolve_entry_confirmation_delay,
)

KST = ZoneInfo("Asia/Seoul")


class RegularGateway(Protocol):
    def completed_sor_minute_bars(self, *, trade_date, now: datetime): ...
    def entry_liquidity_snapshot(self, *, route: str = "SOR"): ...
    def submit_limit_buy(self, *, price: int, quantity: int): ...
    def submit_limit_sell(self, *, price: int, quantity: int): ...
    def cancel_buy(self, *, order_no: str): ...
    def execution_snapshot(
        self, *, order_no: str, order_date: str, expected_order_qty: int
    ): ...


def _iso(now: datetime) -> str:
    return now.astimezone(KST).isoformat()


def _new_leg(leg_id: str, price_role: str, entry_price: int) -> dict:
    return {
        "leg_id": leg_id,
        "price_role": price_role,
        "quantity": EPISODE_LEG_QUANTITY,
        "entry_price": int(entry_price),
        "status": "PLANNED",
        "buy_order_no": "",
        "buy_order_date": "",
        "buy_cancel_requested": False,
        "fill_price": 0,
        "buy_filled_at": "",
        "buy_filled_qty": 0,
        "position_qty": 0,
        "target_price": 0,
        "target_order_no": "",
        "target_order_date": "",
        "target_quantity": 0,
        "target_filled_qty": 0,
        "target_fill_price": 0,
        "target_filled_at": "",
    }


def _fresh_state(now: datetime, schema: str) -> dict:
    return {
        "schema": schema,
        "trade_date": now.date().isoformat(),
        "status": "READY",
        "attempt_consumed": False,
        "last_evaluated_bar": "",
        "signal_bar": "",
        "signal_close": 0,
        "signal_features": {},
        "pending_entry_confirmation": None,
        "legs": [],
        "position_qty": 0,
        "blocked_reason": "",
        "owned_order_nos": [],
        "last_action": "initialized",
        "audit": [],
    }


class SamsungRegularTwoLegMachine:
    """Persistent two-order episode with exact per-leg broker ownership.

    The compatibility class name is retained for the original Samsung callers.
    Symbol and session ownership come from the immutable caller policy.
    """

    LEG_IDS = ("signal_close", "signal_close_minus_1tick")

    def __init__(
        self,
        *,
        gateway: RegularGateway,
        state_path: Path,
        policy,
        strategy_name: str,
        schema: str,
        legacy_schema: str,
        live_enabled: bool = False,
        ownership_source: Callable[
            [object], str
        ] = manual_control_operator_exclusion_source,
        entry_timing_owner: str = "episode",
        entry_timing_scope_id: str | None = None,
        entry_timing_session: str = "KRX_REGULAR",
    ) -> None:
        self.gateway = gateway
        self.state_path = Path(state_path)
        self.policy = policy
        policy_leg_ids = tuple(getattr(policy, "entry_leg_ids", self.LEG_IDS))
        if len(policy_leg_ids) != 2 or len(set(policy_leg_ids)) != 2:
            raise ValueError("policy_leg_identity_contract_invalid")
        self.leg_ids = policy_leg_ids
        self.strategy_name = strategy_name
        self.schema = schema
        self.legacy_schema = legacy_schema
        self.live_enabled = bool(live_enabled)
        self.ownership_source = ownership_source
        self.entry_timing_owner = entry_timing_owner
        self.entry_timing_scope_id = entry_timing_scope_id or strategy_name
        self.entry_timing_session = entry_timing_session
        self._state = self._load_state()

    def _legacy_state(self, payload: dict) -> dict:
        status = str(payload.get("status") or "")
        try:
            position_qty = int(payload.get("position_qty", 0) or 0)
        except (TypeError, ValueError):
            return self._invalid_loaded_state("legacy_position_quantity_invalid")
        if status in {"READY", "COMPLETE", "NO_TRADE"} and position_qty == 0:
            try:
                legacy_now = datetime.fromisoformat(
                    f"{payload.get('trade_date')}T00:00:00+09:00"
                )
                signal_close = int(payload.get("signal_close", 0) or 0)
            except (TypeError, ValueError):
                return self._invalid_loaded_state("legacy_trade_date_invalid")
            migrated = _fresh_state(legacy_now, self.schema)
            migrated.update(
                {
                    "status": status,
                    "attempt_consumed": bool(payload.get("attempt_consumed")),
                    "last_evaluated_bar": str(payload.get("last_evaluated_bar") or ""),
                    "signal_bar": str(payload.get("signal_bar") or ""),
                    "signal_close": signal_close,
                    "last_action": "legacy_terminal_state_migrated",
                    "audit": list(payload.get("audit") or [])[-99:]
                    + [
                        {
                            "at_kst": datetime.now(tz=KST).isoformat(),
                            "action": "legacy_terminal_state_migrated",
                        }
                    ],
                }
            )
            return migrated
        return {
            "schema": self.schema,
            "trade_date": str(payload.get("trade_date") or ""),
            "status": "BLOCKED",
            "attempt_consumed": True,
            "signal_features": {},
            "legs": [],
            "position_qty": position_qty,
            "blocked_reason": "legacy_active_state_manual_reconciliation_required",
            "owned_order_nos": list(payload.get("owned_order_nos") or []),
            "last_action": "blocked_legacy_state_migration",
            "audit": list(payload.get("audit") or [])[-100:],
        }

    def _load_state(self) -> dict:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "schema": self.schema,
                "trade_date": "",
                "status": "BLOCKED",
                "attempt_consumed": True,
                "signal_features": {},
                "legs": [],
                "position_qty": 0,
                "blocked_reason": f"state_unreadable:{type(exc).__name__}",
                "owned_order_nos": [],
                "last_action": "blocked_state_load",
                "audit": [],
            }
        if not isinstance(payload, dict):
            return self._invalid_loaded_state("state_schema_invalid")
        if payload.get("schema") == self.legacy_schema:
            return self._legacy_state(payload)
        if payload.get("schema") != self.schema:
            return self._invalid_loaded_state("state_schema_invalid")
        # V2 states created before entry-feature instrumentation remain valid.
        # They are reported as a source-quality gap, rather than blocking an
        # already-owned order or position during an in-place deployment.
        payload.setdefault("signal_features", {})
        payload.setdefault("pending_entry_confirmation", None)
        for leg in payload.get("legs", []):
            if not isinstance(leg, dict):
                continue
            try:
                inferred_filled_qty = int(leg.get("position_qty", 0) or 0) + int(
                    leg.get("target_filled_qty", 0) or 0
                )
            except (TypeError, ValueError):
                return self._invalid_loaded_state("state_leg_numeric_field_invalid")
            leg.setdefault("buy_filled_qty", inferred_filled_qty)
            leg.setdefault("target_quantity", inferred_filled_qty)
            leg.setdefault("target_fill_price", 0)
            leg.setdefault("target_filled_at", "")
        return payload

    def _invalid_loaded_state(self, reason: str) -> dict:
        return {
            "schema": self.schema,
            "trade_date": "",
            "status": "BLOCKED",
            "attempt_consumed": True,
            "signal_features": {},
            "legs": [],
            "position_qty": 0,
            "blocked_reason": reason,
            "owned_order_nos": [],
            "last_action": "blocked_state_load",
            "audit": [],
        }

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.state_path.name}.", dir=self.state_path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    self._state, handle, ensure_ascii=False, indent=2, sort_keys=True
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self.state_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _record(self, now: datetime, action: str, **fields: object) -> None:
        # Persist a crash-consistent aggregate whenever a leg transition is
        # recorded.  BLOCKED is an explicit machine-level veto and must not be
        # replaced by the leg-derived status.
        if self._state.get("legs") and self._state.get("status") != "BLOCKED":
            self._sync_aggregate()
        self._state["last_action"] = action
        audit = self._state.setdefault("audit", [])
        audit.append({"at_kst": _iso(now), "action": action, **fields})
        self._state["audit"] = audit[-100:]
        self._save()

    def snapshot(self) -> dict:
        return json.loads(json.dumps(self._state, ensure_ascii=False))

    def _own_order(self, order_no: str) -> None:
        clean = str(order_no or "").strip()
        owned = {
            str(item).strip() for item in self._state.get("owned_order_nos", []) if item
        }
        if clean:
            owned.add(clean)
        self._state["owned_order_nos"] = sorted(owned)

    def _owns_order(self, order_no: str) -> bool:
        return str(order_no or "").strip() in {
            str(item).strip() for item in self._state.get("owned_order_nos", []) if item
        }

    def _block(self, now: datetime, reason: str) -> dict:
        self._state.update({"status": "BLOCKED", "blocked_reason": reason})
        self._record(now, "blocked", reason=reason)
        return self.snapshot()

    def _entry_liquidity_decision(
        self, *, route: str, requested_quantity: int
    ) -> EntryLiquidityDecision:
        try:
            snapshot = self.gateway.entry_liquidity_snapshot(route=route)
        except Exception as exc:
            snapshot = unavailable_entry_liquidity_snapshot(
                symbol=str(self.policy.symbol),
                route=route,
                error=type(exc).__name__,
            )
        return evaluate_entry_liquidity(snapshot, requested_quantity=requested_quantity)

    def _entry_liquidity_allows_planned_buys(
        self, *, now: datetime, route: str, requested_quantity: int
    ) -> bool:
        features = dict(self._state.get("signal_features") or {})
        normalized_route = str(route or "").strip().upper()
        decision = self._entry_liquidity_decision(
            route=normalized_route,
            requested_quantity=requested_quantity,
        )
        features["entry_liquidity"] = decision.event_fields()
        self._state["signal_features"] = features
        if not decision.allowed:
            for leg in self._state.get("legs", []):
                leg_route = str(leg.get("route") or normalized_route).upper()
                if leg.get("status") == "PLANNED" and leg_route == normalized_route:
                    leg["status"] = "NO_FILL"
            self._state["blocked_reason"] = decision.reason
            self._record(
                now,
                "entry_liquidity_blocked_before_buy",
                route=normalized_route,
                **decision.event_fields(),
            )
            return False
        self._state["blocked_reason"] = ""
        self._record(
            now,
            "entry_liquidity_guard_passed",
            route=normalized_route,
            **decision.event_fields(),
        )
        return True

    def _position_qty(self) -> int:
        return sum(
            int(leg.get("position_qty", 0) or 0) for leg in self._state.get("legs", [])
        )

    def _derive_status(self) -> str:
        legs = self._state.get("legs", [])
        if not legs:
            return str(self._state.get("status") or "READY")
        statuses = {str(leg.get("status") or "") for leg in legs}
        if "BLOCKED" in statuses:
            return "BLOCKED"
        if statuses & {"BUY_SUBMITTING", "BUY_CANCEL_SUBMITTING"}:
            return "BUY_SUBMITTING"
        if "BUY_OPEN" in statuses or "PLANNED" in statuses:
            return "BUY_OPEN"
        if "BUY_CANCEL_PENDING" in statuses:
            return "BUY_CANCEL_PENDING"
        if "TARGET_SUBMITTING" in statuses:
            return "TARGET_SUBMITTING"
        if statuses & {"POSITION_OPEN", "TARGET_OPEN"}:
            return "TARGET_OPEN"
        if self._position_qty() > 0:
            return "HELD"
        if statuses <= {"NO_FILL"}:
            return "NO_TRADE"
        if statuses <= {"NO_FILL", "COMPLETE"} and "COMPLETE" in statuses:
            return "COMPLETE"
        return "BLOCKED"

    def _sync_aggregate(self) -> None:
        self._state["position_qty"] = self._position_qty()
        self._state["status"] = self._derive_status()

    def _validate_state_contract(self, now: datetime) -> bool:
        if self._state.get("schema") != self.schema:
            self._block(now, "state_schema_invalid")
            return False
        try:
            date.fromisoformat(str(self._state.get("trade_date") or ""))
            position_qty = int(self._state.get("position_qty", 0) or 0)
        except (TypeError, ValueError):
            self._block(now, "state_date_or_quantity_invalid")
            return False
        allowed_statuses = {
            "READY",
            "BUY_SUBMITTING",
            "BUY_OPEN",
            "BUY_CANCEL_PENDING",
            "TARGET_SUBMITTING",
            "TARGET_OPEN",
            "COMPLETE",
            "NO_TRADE",
            "HELD",
            "BLOCKED",
        }
        if self._state.get("status") not in allowed_statuses:
            self._block(now, "state_status_invalid")
            return False
        if not 0 <= position_qty <= EPISODE_TOTAL_QUANTITY or not isinstance(
            self._state.get("attempt_consumed"), bool
        ):
            self._block(now, "state_quantity_or_attempt_invalid")
            return False
        if not isinstance(self._state.get("signal_features"), dict):
            self._block(now, "state_signal_features_invalid")
            return False
        pending_confirmation = self._state.get("pending_entry_confirmation")
        if pending_confirmation is not None:
            if not isinstance(pending_confirmation, dict):
                self._block(now, "state_pending_entry_confirmation_invalid")
                return False
            try:
                armed_at = datetime.fromisoformat(
                    str(pending_confirmation.get("armed_at") or "")
                )
                due_at = datetime.fromisoformat(
                    str(pending_confirmation.get("due_at") or "")
                )
                delay_sec = int(pending_confirmation.get("delay_sec"))
                signal_close = int(pending_confirmation.get("signal_close") or 0)
            except (TypeError, ValueError):
                self._block(now, "state_pending_entry_confirmation_invalid")
                return False
            provenance = pending_confirmation.get("policy_provenance")
            if (
                armed_at.tzinfo is None
                or due_at.tzinfo is None
                or isinstance(pending_confirmation.get("delay_sec"), bool)
                or abs((due_at - armed_at).total_seconds() - delay_sec) > 0.001
                or delay_sec not in {1, 3, 5}
                or not str(pending_confirmation.get("signal_bar") or "")
                or signal_close <= 0
                or not isinstance(provenance, dict)
                or provenance.get("status") != "applied"
                or len(str(provenance.get("policy_hash") or "")) != 64
                or provenance.get("target_date") != self._state.get("trade_date")
            ):
                self._block(now, "state_pending_entry_confirmation_invalid")
                return False
        owned = self._state.get("owned_order_nos")
        if not isinstance(owned, list) or any(
            not isinstance(x, str) or not x.strip() for x in owned
        ):
            self._block(now, "state_owned_order_ledger_invalid")
            return False
        legs = self._state.get("legs")
        if not isinstance(legs, list) or len(legs) not in {0, 2}:
            self._block(now, "state_leg_count_invalid")
            return False
        if not legs and position_qty != 0:
            self._block(now, "state_position_without_legs")
            return False
        if legs:
            if any(not isinstance(leg, dict) for leg in legs):
                self._block(now, "state_leg_payload_invalid")
                return False
            if {leg.get("leg_id") for leg in legs} != set(self.leg_ids):
                self._block(now, "state_leg_identity_invalid")
                return False
            leg_order_nos: list[str] = []
            allowed_leg_statuses = {
                "PLANNED",
                "BUY_SUBMITTING",
                "BUY_OPEN",
                "BUY_CANCEL_SUBMITTING",
                "BUY_CANCEL_PENDING",
                "POSITION_OPEN",
                "TARGET_SUBMITTING",
                "TARGET_OPEN",
                "NO_FILL",
                "COMPLETE",
                "HELD",
            }
            observed_leg_quantities: set[int] = set()
            for leg in legs:
                try:
                    leg_quantity = int(leg.get("quantity", 0) or 0)
                    leg_position = int(leg.get("position_qty", 0) or 0)
                    buy_filled_qty = int(leg.get("buy_filled_qty", 0) or 0)
                    target_quantity = int(leg.get("target_quantity", 0) or 0)
                    target_filled_qty = int(leg.get("target_filled_qty", 0) or 0)
                    target_fill_price = int(leg.get("target_fill_price", 0) or 0)
                    entry_price = int(leg.get("entry_price", 0) or 0)
                    fill_price = int(leg.get("fill_price", 0) or 0)
                except (TypeError, ValueError):
                    self._block(now, "state_leg_numeric_field_invalid")
                    return False
                if leg_quantity not in SUPPORTED_OWNED_LEG_QUANTITIES:
                    self._block(now, "state_leg_quantity_invalid")
                    return False
                observed_leg_quantities.add(leg_quantity)
                if not (
                    0 <= leg_position <= leg_quantity
                    and 0 <= buy_filled_qty <= leg_quantity
                    and 0 <= target_quantity <= leg_quantity
                    and 0 <= target_filled_qty <= target_quantity
                ):
                    self._block(now, "state_leg_position_invalid")
                    return False
                if entry_price < 0 or fill_price < 0 or target_fill_price < 0:
                    self._block(now, "state_leg_price_invalid")
                    return False
                if target_fill_price > 0 and target_filled_qty <= 0:
                    self._block(now, "state_target_fill_price_without_fill")
                    return False
                leg_status = str(leg.get("status") or "")
                if leg_status not in allowed_leg_statuses:
                    self._block(now, "state_leg_status_invalid")
                    return False
                positive_position_statuses = {
                    "POSITION_OPEN",
                    "TARGET_SUBMITTING",
                    "TARGET_OPEN",
                    "HELD",
                }
                if leg_status in positive_position_statuses and leg_position <= 0:
                    self._block(now, "state_leg_position_status_mismatch")
                    return False
                zero_position_statuses = {
                    "PLANNED",
                    "BUY_SUBMITTING",
                    "NO_FILL",
                    "COMPLETE",
                }
                if leg_status in zero_position_statuses and leg_position != 0:
                    self._block(now, "state_leg_position_status_mismatch")
                    return False
                if leg_position > 0 and fill_price <= 0:
                    self._block(now, "state_leg_fill_price_missing")
                    return False
                if leg_position != buy_filled_qty - target_filled_qty:
                    self._block(now, "state_leg_fill_position_mismatch")
                    return False
                if target_quantity and target_quantity != buy_filled_qty:
                    self._block(now, "state_leg_target_quantity_mismatch")
                    return False
                if (
                    leg_status in {"BUY_OPEN", "BUY_CANCEL_PENDING"}
                    and not str(leg.get("buy_order_no") or "").strip()
                ):
                    self._block(now, "state_leg_buy_order_missing")
                    return False
                if (
                    leg_status == "TARGET_OPEN"
                    and not str(leg.get("target_order_no") or "").strip()
                ):
                    self._block(now, "state_leg_target_order_missing")
                    return False
                for key in ("buy_order_no", "target_order_no"):
                    order_no = str(leg.get(key) or "").strip()
                    if order_no and not self._owns_order(order_no):
                        self._block(now, f"state_{key}_ownership_invalid")
                        return False
                    if order_no:
                        leg_order_nos.append(order_no)
            if len(observed_leg_quantities) != 1:
                self._block(now, "state_mixed_leg_quantities_invalid")
                return False
            if len(leg_order_nos) != len(set(leg_order_nos)):
                self._block(now, "state_leg_order_identity_collision")
                return False
            if position_qty != self._position_qty():
                self._block(now, "state_aggregate_position_mismatch")
                return False
            derived = self._derive_status()
            if self._state.get("status") != derived:
                self._block(now, "state_aggregate_status_mismatch")
                return False
        return True

    def _roll_date(self, now: datetime) -> bool:
        if not self._state:
            self._state = _fresh_state(now, self.schema)
            self._save()
            return True
        if self._state.get("trade_date") == now.date().isoformat():
            return True
        if int(self._state.get("position_qty", 0) or 0) > 0:
            return True
        if self._state.get("status") not in {"READY", "COMPLETE", "NO_TRADE"}:
            self._state.update(
                {
                    "status": "BLOCKED",
                    "blocked_reason": "previous_day_order_or_position_unresolved",
                }
            )
            self._record(now, "blocked_date_rollover")
            return False
        self._state = _fresh_state(now, self.schema)
        self._record(now, "daily_state_initialized")
        return True

    def _execution(self, leg: dict, order_key: str):
        order_no = str(leg.get(order_key) or "")
        if not self._owns_order(order_no):
            raise ValueError(f"{order_key}_not_owned")
        date_key = (
            "buy_order_date" if order_key == "buy_order_no" else "target_order_date"
        )
        return self.gateway.execution_snapshot(
            order_no=order_no,
            order_date=str(leg.get(date_key) or ""),
            expected_order_qty=(
                int(leg.get("quantity", 0) or 0)
                if order_key == "buy_order_no"
                else int(leg.get("target_quantity", 0) or 0)
            ),
        )

    def _submit_target(self, now: datetime, leg: dict) -> None:
        if (
            int(leg.get("position_qty", 0) or 0) <= 0
            or int(leg.get("fill_price", 0) or 0) <= 0
        ):
            self._block(now, f"target_requires_confirmed_leg_fill:{leg.get('leg_id')}")
            return
        leg["status"] = "TARGET_SUBMITTING"
        target_price = self.policy.target_price(int(leg["fill_price"]))
        self._record(
            now,
            "target_submit_intent",
            leg_id=leg["leg_id"],
            target_price=target_price,
            quantity=int(leg["position_qty"]),
        )
        target_quantity = int(leg["position_qty"])
        result = self.gateway.submit_limit_sell(
            price=target_price, quantity=target_quantity
        )
        if result.ambiguous:
            self._block(now, f"target_submit_ambiguous:{leg['leg_id']}")
            return
        if not result.accepted:
            leg["status"] = "POSITION_OPEN"
            self._record(
                now,
                "target_submit_rejected_retryable",
                leg_id=leg["leg_id"],
                return_code=result.return_code,
            )
            return
        leg.update(
            {
                "status": "TARGET_OPEN",
                "target_price": target_price,
                "target_order_no": result.order_no,
                "target_order_date": now.date().isoformat(),
                "target_quantity": target_quantity,
            }
        )
        self._own_order(result.order_no)
        self._record(
            now,
            "target_submitted",
            leg_id=leg["leg_id"],
            target_price=target_price,
            quantity=target_quantity,
        )

    def _reconcile_target(self, now: datetime, leg: dict) -> None:
        try:
            snapshot = self._execution(leg, "target_order_no")
        except ValueError:
            self._block(now, f"target_order_not_owned:{leg.get('leg_id')}")
            return
        if not snapshot.source_ok or not snapshot.found:
            self._record(
                now,
                "target_reconciliation_wait",
                leg_id=leg["leg_id"],
                error=snapshot.error,
            )
        else:
            target_quantity = int(leg.get("target_quantity", 0) or 0)
            target_filled_qty = int(snapshot.filled_qty)
            leg["target_filled_qty"] = target_filled_qty
            leg["position_qty"] = target_quantity - target_filled_qty
            if target_filled_qty > 0 and snapshot.fill_price:
                leg["target_fill_price"] = int(snapshot.fill_price)
                leg["target_filled_at"] = _iso(now)
        if (
            snapshot.source_ok
            and snapshot.found
            and snapshot.filled_qty == int(leg.get("target_quantity", 0) or 0)
        ):
            leg.update({"position_qty": 0, "status": "COMPLETE"})
            self._record(
                now,
                "target_fill_confirmed",
                leg_id=leg["leg_id"],
                filled_qty=snapshot.filled_qty,
                fill_price=int(snapshot.fill_price or 0),
                fill_price_source=(
                    "broker_kt00007_cntr_uv"
                    if snapshot.fill_price
                    else "unavailable_target_price_proxy_required"
                ),
            )
        elif snapshot.source_ok and snapshot.found and snapshot.remaining_qty == 0:
            leg["status"] = "HELD" if leg["position_qty"] > 0 else "COMPLETE"
            self._record(
                now,
                "target_closed_with_position_held",
                leg_id=leg["leg_id"],
                filled_qty=snapshot.filled_qty,
                position_qty=leg["position_qty"],
            )
        elif snapshot.source_ok and snapshot.found:
            self._record(now, "target_open_wait", leg_id=leg["leg_id"])

    def _source(self, now: datetime):
        return self.gateway.completed_sor_minute_bars(trade_date=now.date(), now=now)

    def _completed_bars_after_signal(self, now: datetime) -> int | None:
        source = self._source(now)
        if not source.source_ok:
            self._record(now, "buy_expiry_source_wait", error=source.error)
            return None
        try:
            signal_bar = datetime.fromisoformat(
                str(self._state.get("signal_bar") or "")
            )
            if signal_bar.tzinfo is None:
                raise ValueError("naive_signal_bar")
            signal_bar = signal_bar.astimezone(KST)
        except (TypeError, ValueError):
            self._block(now, "signal_bar_missing_for_buy_expiry")
            return None
        return sum(bar.timestamp > signal_bar for bar in source.bars)

    def _cancel_buy(self, now: datetime, leg: dict, elapsed: int) -> None:
        leg["status"] = "BUY_CANCEL_SUBMITTING"
        self._record(
            now,
            "buy_cancel_intent",
            leg_id=leg["leg_id"],
            completed_bars_after_signal=elapsed,
        )
        result = self.gateway.cancel_buy(order_no=str(leg["buy_order_no"]))
        if result.ambiguous:
            self._block(now, f"buy_cancel_ambiguous:{leg['leg_id']}")
            return
        if not result.accepted:
            leg["status"] = "BUY_OPEN"
            self._record(
                now,
                "buy_cancel_rejected_retryable",
                leg_id=leg["leg_id"],
                return_code=result.return_code,
            )
            return
        leg.update({"status": "BUY_CANCEL_PENDING", "buy_cancel_requested": True})
        self._own_order(result.order_no)
        self._record(now, "buy_cancel_submitted", leg_id=leg["leg_id"])

    def _reconcile_buy(self, now: datetime, leg: dict, elapsed: int | None) -> None:
        try:
            snapshot = self._execution(leg, "buy_order_no")
        except ValueError:
            self._block(now, f"buy_order_not_owned:{leg.get('leg_id')}")
            return
        if not snapshot.source_ok:
            self._record(
                now,
                "buy_reconciliation_wait",
                leg_id=leg["leg_id"],
                error=snapshot.error,
            )
            return
        if snapshot.found and snapshot.filled_qty > 0:
            if not snapshot.fill_price:
                self._block(now, f"buy_fill_price_missing:{leg['leg_id']}")
                return
            leg.update(
                {
                    "position_qty": snapshot.filled_qty,
                    "buy_filled_qty": snapshot.filled_qty,
                    "fill_price": snapshot.fill_price,
                    "buy_filled_at": _iso(now),
                    "status": (
                        "POSITION_OPEN"
                        if snapshot.remaining_qty == 0
                        else (
                            "BUY_CANCEL_PENDING"
                            if leg.get("buy_cancel_requested")
                            else "BUY_OPEN"
                        )
                    ),
                }
            )
            self._record(
                now,
                "buy_fill_confirmed",
                leg_id=leg["leg_id"],
                fill_price=snapshot.fill_price,
                filled_qty=snapshot.filled_qty,
                remaining_qty=snapshot.remaining_qty,
            )
            if snapshot.remaining_qty == 0:
                self._submit_target(now, leg)
            elif not leg.get("buy_cancel_requested"):
                self._cancel_buy(now, leg, elapsed or 0)
            return
        if snapshot.found and snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            leg.update({"status": "NO_FILL", "buy_cancel_requested": False})
            completed_sibling_leg_ids = [
                str(item.get("leg_id") or "")
                for item in self._state.get("legs", [])
                if item is not leg
                and item.get("status") == "COMPLETE"
                and int(item.get("buy_filled_qty", 0) or 0) > 0
            ]
            action = (
                "unfilled_buy_leg_resolved_after_sibling_completed"
                if completed_sibling_leg_ids
                else "buy_resolved_without_fill"
            )
            self._record(
                now,
                action,
                leg_id=leg["leg_id"],
                completed_sibling_leg_ids=completed_sibling_leg_ids,
            )
            return
        if leg.get("buy_cancel_requested"):
            self._record(now, "buy_cancel_reconciliation_wait", leg_id=leg["leg_id"])
            return
        if elapsed is None or elapsed < self.policy.entry_valid_completed_bars:
            self._record(
                now,
                "buy_open_wait",
                leg_id=leg["leg_id"],
                completed_bars_after_signal=elapsed,
            )
            return
        self._cancel_buy(now, leg, elapsed)

    def _submit_planned_buys(self, now: datetime) -> None:
        planned_quantity = sum(
            int(leg.get("quantity", 0) or 0)
            for leg in self._state.get("legs", [])
            if leg.get("status") == "PLANNED"
        )
        if planned_quantity > 0:
            route = str(getattr(self.policy, "route", "SOR") or "SOR").upper()
            if not self._entry_liquidity_allows_planned_buys(
                now=now,
                route=route,
                requested_quantity=planned_quantity,
            ):
                return
        for leg in self._state.get("legs", []):
            if leg.get("status") != "PLANNED" or self._state.get("status") == "BLOCKED":
                continue
            leg["status"] = "BUY_SUBMITTING"
            self._record(
                now,
                "buy_submit_intent",
                leg_id=leg["leg_id"],
                entry_price=leg["entry_price"],
                quantity=leg["quantity"],
            )
            result = self.gateway.submit_limit_buy(
                price=int(leg["entry_price"]), quantity=int(leg["quantity"])
            )
            if result.ambiguous:
                self._block(now, f"buy_submit_ambiguous:{leg['leg_id']}")
                return
            if not result.accepted:
                leg["status"] = "NO_FILL"
                self._record(
                    now,
                    "buy_submit_rejected",
                    leg_id=leg["leg_id"],
                    return_code=result.return_code,
                )
                continue
            leg.update(
                {
                    "status": "BUY_OPEN",
                    "buy_order_no": result.order_no,
                    "buy_order_date": now.date().isoformat(),
                }
            )
            self._own_order(result.order_no)
            self._record(
                now,
                "buy_submitted",
                leg_id=leg["leg_id"],
                entry_price=leg["entry_price"],
                quantity=leg["quantity"],
            )

    def _consider_entry(self, now: datetime) -> dict:
        source = self._source(now)
        if not source.source_ok or not source.bars:
            self._state.update(
                {
                    "last_action": "sor_minute_source_wait",
                    "blocked_reason": source.error,
                }
            )
            self._save()
            return self.snapshot()
        transient_source_wait = self._state.get("last_action") in {
            "sor_minute_source_wait",
            "stale_or_incomplete_sor_bar_wait",
        }
        latest = source.bars[-1]
        lag_minutes = int(
            (now.replace(second=0, microsecond=0) - latest.timestamp).total_seconds()
            // 60
        )
        if lag_minutes < 1 or lag_minutes > self.policy.max_source_lag_minutes:
            self._state.update(
                {
                    "last_action": "stale_or_incomplete_sor_bar_wait",
                    "blocked_reason": f"latest_completed_bar_lag:{lag_minutes}",
                }
            )
            self._save()
            return self.snapshot()
        if transient_source_wait:
            self._state["blocked_reason"] = ""
        latest_iso = latest.timestamp.isoformat()
        pending_confirmation = self._state.get("pending_entry_confirmation")
        confirmed_pending = False
        signal = None
        if isinstance(pending_confirmation, dict):
            signal = self.policy.evaluate(list(source.bars))
            same_signal = bool(
                signal is not None
                and latest_iso == pending_confirmation.get("signal_bar")
                and int(signal.signal_bar.close_price)
                == int(pending_confirmation.get("signal_close") or 0)
            )
            if not same_signal:
                self._state["pending_entry_confirmation"] = None
                self._record(
                    now,
                    "entry_confirmation_invalidated",
                    prior_signal_bar=pending_confirmation.get("signal_bar"),
                    current_completed_bar=latest_iso,
                    reason="signal_no_longer_same_and_actionable",
                )
                pending_confirmation = None
            else:
                due_at = datetime.fromisoformat(str(pending_confirmation["due_at"]))
                if now < due_at:
                    self._state.update(
                        {
                            "last_action": "entry_confirmation_wait",
                            "blocked_reason": "",
                        }
                    )
                    self._save()
                    return self.snapshot()
                if now > due_at + timedelta(seconds=ENTRY_CONFIRMATION_MAX_LATE_SEC):
                    self._state["pending_entry_confirmation"] = None
                    self._record(
                        now,
                        "entry_confirmation_invalidated",
                        prior_signal_bar=pending_confirmation.get("signal_bar"),
                        reason="confirmation_recheck_window_expired",
                    )
                    return self.snapshot()
                active_delay, active_provenance = resolve_entry_confirmation_delay(
                    target_date=now.date(),
                    owner=self.entry_timing_owner,
                    scope_id=self.entry_timing_scope_id,
                    symbol=str(self.policy.symbol),
                    session=self.entry_timing_session,
                    entry_state="UNSPECIFIED",
                )
                if (
                    active_delay != int(pending_confirmation["delay_sec"])
                    or active_provenance.get("status") != "applied"
                    or active_provenance.get("policy_hash")
                    != (pending_confirmation.get("policy_provenance") or {}).get(
                        "policy_hash"
                    )
                ):
                    self._state["pending_entry_confirmation"] = None
                    self._record(
                        now,
                        "entry_confirmation_invalidated",
                        prior_signal_bar=pending_confirmation.get("signal_bar"),
                        reason="entry_timing_policy_revalidation_failed",
                        active_policy_status=active_provenance.get("status"),
                    )
                    return self.snapshot()
                confirmed_pending = True
        if (
            not confirmed_pending
            and self._state.get("last_evaluated_bar") == latest_iso
        ):
            if transient_source_wait:
                self._record(now, "sor_minute_source_recovered", bar=latest_iso)
            return self.snapshot()
        if latest.timestamp.time() > self.policy.scan_last_bar:
            self._state["status"] = "NO_TRADE"
            self._record(now, f"{self.strategy_name}_scan_window_closed")
            return self.snapshot()
        if latest.timestamp.time() < self.policy.scan_start:
            self._state.update(
                {
                    "last_action": f"waiting_for_{self.strategy_name}_scan_window",
                    "blocked_reason": "",
                }
            )
            self._save()
            return self.snapshot()
        self._state["last_evaluated_bar"] = latest_iso
        if signal is None:
            signal = self.policy.evaluate(list(source.bars))
        if signal is None:
            self._record(now, "bar_evaluated_no_signal", bar=latest_iso)
            return self.snapshot()
        source_owner = str(self.ownership_source(self.policy.symbol) or "")
        plans = self.policy.entry_legs(signal.signal_bar.close_price)
        if not self.live_enabled:
            self._state.update(
                {
                    "last_action": "would_submit_sor_two_leg_buy",
                    "blocked_reason": "live_authority_disabled",
                    "preview": {
                        "signal_bar": latest_iso,
                        "total_quantity": EPISODE_TOTAL_QUANTITY,
                        "legs": plans,
                        "operator_exclusion_ready": bool(source_owner),
                        "strategy_relationship": "parallel_independent_strategy",
                    },
                }
            )
            self._save()
            return self.snapshot()
        if not source_owner:
            self._state.update(
                {
                    "last_action": "operator_exclusion_required",
                    "blocked_reason": (
                        f"{self.policy.symbol}_not_excluded_from_primary_bot"
                    ),
                }
            )
            self._save()
            return self.snapshot()
        if confirmed_pending:
            delay_sec = int(pending_confirmation["delay_sec"])
            signal_decision_at = str(pending_confirmation["armed_at"])
            timing_policy_provenance = dict(
                pending_confirmation.get("policy_provenance") or {}
            )
        else:
            delay_sec, timing_policy_provenance = resolve_entry_confirmation_delay(
                target_date=now.date(),
                owner=self.entry_timing_owner,
                scope_id=self.entry_timing_scope_id,
                symbol=str(self.policy.symbol),
                session=self.entry_timing_session,
                entry_state="UNSPECIFIED",
            )
            signal_decision_at = now.isoformat()
            if delay_sec > 0:
                due_at = now + timedelta(seconds=delay_sec)
                self._state["pending_entry_confirmation"] = {
                    "signal_bar": latest_iso,
                    "signal_close": int(latest.close_price),
                    "armed_at": signal_decision_at,
                    "due_at": due_at.isoformat(),
                    "delay_sec": delay_sec,
                    "policy_provenance": timing_policy_provenance,
                }
                self._record(
                    now,
                    "entry_confirmation_armed",
                    signal_bar=latest_iso,
                    delay_sec=delay_sec,
                    due_at=due_at.isoformat(),
                    timing_policy_hash=timing_policy_provenance.get("policy_hash"),
                )
                return self.snapshot()
        self._state.update(
            {
                "attempt_consumed": True,
                "pending_entry_confirmation": None,
                "signal_bar": latest_iso,
                "signal_close": latest.close_price,
                "signal_features": {
                    "schema": (
                        "samsung_regular_entry_signal_features_v1"
                        if self.policy.symbol == "005930"
                        else "regular_two_leg_entry_signal_features_v1"
                    ),
                    "strategy": self.strategy_name,
                    "symbol": str(self.policy.symbol),
                    "source": (f"kiwoom_ka10080_{self.policy.symbol}_AL_completed_1m"),
                    "signal_bar": latest_iso,
                    "signal_decision_at": signal_decision_at,
                    "signal_close": int(latest.close_price),
                    "entry_confirmation_delay_sec": delay_sec,
                    "entry_timing_policy_provenance": timing_policy_provenance,
                    "rolling_high": int(signal.rolling_high),
                    "rolling_low": int(signal.rolling_low),
                    "observed_drawdown_pct": float(signal.drawdown_pct),
                    "observed_near_low_pct": float(signal.near_low_pct),
                    "lookback_bars": int(self.policy.lookback_bars),
                    "required_drawdown_pct": float(
                        self.policy.rolling_high_drawdown_pct
                    ),
                    "max_near_low_pct": float(self.policy.rolling_low_proximity_pct),
                    "entry_valid_completed_bars": int(
                        self.policy.entry_valid_completed_bars
                    ),
                    "scan_start": self.policy.scan_start.isoformat(),
                    "scan_last_bar": self.policy.scan_last_bar.isoformat(),
                    "target_ticks": int(self.policy.target_ticks),
                    "runtime_policy_source": str(self.policy.runtime_policy_source),
                    "runtime_policy_hash": str(self.policy.runtime_policy_hash),
                    "entry_legs": [
                        {
                            "leg_id": str(plan["leg_id"]),
                            "price_role": str(plan["price_role"]),
                            "entry_price": int(plan["entry_price"]),
                            "quantity": EPISODE_LEG_QUANTITY,
                        }
                        for plan in plans
                    ],
                },
                "legs": [_new_leg(**plan) for plan in plans],
                "blocked_reason": "",
            }
        )
        self._sync_aggregate()
        self._record(
            now,
            "two_leg_entry_armed",
            signal_bar=latest_iso,
            signal_decision_at=signal_decision_at,
            entry_confirmation_delay_sec=delay_sec,
            drawdown_pct=signal.drawdown_pct,
            near_low_pct=signal.near_low_pct,
        )
        self._submit_planned_buys(now)
        self._sync_aggregate()
        self._save()
        return self.snapshot()

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        if self._state and self._state.get("status") == "BLOCKED":
            return self.snapshot()
        if self._state and not self._validate_state_contract(now):
            return self.snapshot()
        if not self._roll_date(now) or not self._validate_state_contract(now):
            return self.snapshot()
        if not self._state.get("legs"):
            if self._state.get("status") in {"COMPLETE", "NO_TRADE"} or self._state.get(
                "attempt_consumed"
            ):
                return self.snapshot()
            return self._consider_entry(now)
        for leg in self._state["legs"]:
            if leg.get("status") in {
                "BUY_SUBMITTING",
                "BUY_CANCEL_SUBMITTING",
                "TARGET_SUBMITTING",
            }:
                return self._block(
                    now,
                    f"broker_write_interrupted:{leg['leg_id']}:{str(leg['status']).lower()}",
                )
        elapsed = None
        if any(
            leg.get("status") in {"BUY_OPEN", "BUY_CANCEL_PENDING"}
            for leg in self._state["legs"]
        ):
            elapsed = self._completed_bars_after_signal(now)
            if self._state.get("status") == "BLOCKED":
                return self.snapshot()
        for leg in self._state["legs"]:
            status = leg.get("status")
            if status in {"BUY_OPEN", "BUY_CANCEL_PENDING"}:
                self._reconcile_buy(now, leg, elapsed)
            elif status == "POSITION_OPEN":
                self._submit_target(now, leg)
            elif status == "TARGET_OPEN":
                self._reconcile_target(now, leg)
            if self._state.get("status") == "BLOCKED":
                return self.snapshot()
        self._submit_planned_buys(now)
        self._sync_aggregate()
        if self._state["status"] == "BLOCKED":
            return self._block(now, "state_terminal_derivation_invalid")
        self._save()
        return self.snapshot()

    def run_forever(self, *, interval_sec: float = 2.0) -> None:
        while True:
            self.run_once()
            time_module.sleep(self._next_loop_delay_sec(interval_sec=interval_sec))

    def run_until_terminal(self, *, interval_sec: float = 2.0) -> dict:
        while True:
            state = self.run_once()
            if state.get("status") in {"COMPLETE", "NO_TRADE", "HELD", "BLOCKED"}:
                return state
            time_module.sleep(self._next_loop_delay_sec(interval_sec=interval_sec))

    def _next_loop_delay_sec(
        self, *, interval_sec: float, now: datetime | None = None
    ) -> float:
        """Wake at an armed confirmation deadline instead of the coarse poll.

        Lower-price launchers intentionally use a six-second steady-state poll.
        A selected one/three/five-second entry timing policy must nevertheless
        be consumed at its own deadline.  This changes only the next evaluation
        time; broker, signal, price, quantity, and exit behavior remain owned by
        the existing machine path.
        """

        base_delay = max(0.2, float(interval_sec))
        pending = self._state.get("pending_entry_confirmation")
        if not isinstance(pending, dict):
            return base_delay
        try:
            due_at = datetime.fromisoformat(str(pending.get("due_at") or ""))
        except ValueError:
            return base_delay
        if due_at.tzinfo is None:
            return base_delay
        current = (now or datetime.now(tz=KST)).astimezone(KST)
        remaining = (due_at.astimezone(KST) - current).total_seconds()
        if remaining <= 0:
            return min(base_delay, 0.2)
        return min(base_delay, max(0.02, remaining))
