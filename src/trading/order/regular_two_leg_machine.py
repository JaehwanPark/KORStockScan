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
    independent_machine_ownership_source,
)
from src.engine.risk.market_weakness_entry_guard import (
    MarketWeaknessEntryDecision,
    evaluate_market_weakness_entry_guard,
    record_market_weakness_blocked_entry,
)
from src.trading.order.episode_quantity import (
    EPISODE_LEG_QUANTITY,
    EPISODE_TOTAL_QUANTITY,
    SUPPORTED_OWNED_LEG_QUANTITIES,
)
from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocityDecision,
    EntryLiquidityDecision,
    evaluate_entry_execution_velocity,
    evaluate_executable_micro_confirmation,
    evaluate_entry_liquidity,
    unavailable_entry_execution_velocity_snapshot,
    unavailable_entry_liquidity_snapshot,
)
from src.trading.config.symbol_owner_policy import (
    SymbolOwnerPolicyError,
    resolve_symbol_owner_policy,
)
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
    OwnerRegistryError,
    default_order_owner_registry,
)
from src.trading.order.tick_utils import move_price_by_ticks
from src.trading.config.machine_entry_timing_policy import (
    DYNAMIC_MODE,
    ENTRY_CONFIRMATION_MAX_LATE_SEC,
    resolve_entry_confirmation_policy,
)
from src.trading.market.micro_confirmation import advance_live_dynamic_confirmation

KST = ZoneInfo("Asia/Seoul")


class RegularGateway(Protocol):
    def completed_sor_minute_bars(self, *, trade_date, now: datetime): ...
    def entry_liquidity_snapshot(self, *, route: str = "SOR"): ...
    def entry_execution_velocity_snapshot(self, *, route: str = "SOR"): ...
    def submit_limit_buy(self, *, price: int, quantity: int): ...
    def submit_limit_sell(self, *, price: int, quantity: int): ...
    def cancel_buy(self, *, order_no: str): ...
    def execution_snapshot(
        self, *, order_no: str, order_date: str, expected_order_qty: int
    ): ...


def _iso(now: datetime) -> str:
    return now.astimezone(KST).isoformat()


def _default_episode_ownership_source(code: object) -> str:
    return independent_machine_ownership_source(code, owner="episode")


def _new_leg(leg_id: str, price_role: str, entry_price: int) -> dict:
    return {
        "leg_id": leg_id,
        "price_role": price_role,
        "quantity": EPISODE_LEG_QUANTITY,
        "entry_price": int(entry_price),
        "status": "PLANNED",
        "buy_order_no": "",
        "buy_order_date": "",
        "buy_submit_attempt_count": 0,
        "buy_owner_registry_intent_id": "",
        "buy_cancel_requested": False,
        "buy_cancel_ambiguous": False,
        "buy_cancel_attempt_count": 0,
        "buy_cancel_attempted_at": "",
        "buy_cancel_terminal_failure": False,
        "buy_cancel_reason": "",
        "buy_cancel_provenance": {},
        "buy_cancel_order_no": "",
        "buy_cancel_order_date": "",
        "buy_cancel_owner_registry_reconciliation_required": False,
        "last_buy_reconciled_at": "",
        "last_buy_remaining_qty": 0,
        "last_buy_reconcile_source_ok": False,
        "fill_price": 0,
        "buy_filled_at": "",
        "buy_filled_qty": 0,
        "position_qty": 0,
        "target_price": 0,
        "target_order_no": "",
        "target_order_date": "",
        "target_submit_attempt_count": 0,
        "target_owner_registry_intent_id": "",
        "buy_owner_registry_reconciliation_required": False,
        "target_owner_registry_reconciliation_required": False,
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
        "owner_registry_reconciliation_required": False,
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
    BUY_CANCEL_MAX_ATTEMPTS = 3
    BUY_CANCEL_RETRY_SEC = 5

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
        ownership_source: Callable[[object], str] = _default_episode_ownership_source,
        entry_timing_owner: str = "episode",
        entry_timing_scope_id: str | None = None,
        entry_timing_session: str = "KRX_REGULAR",
        owner_registry: OrderOwnerRegistry | None = None,
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
        self.owner_registry = owner_registry or default_order_owner_registry()
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
        payload.setdefault("owner_registry_reconciliation_required", False)
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
            leg.setdefault("buy_cancel_ambiguous", False)
            leg.setdefault("buy_cancel_attempt_count", 0)
            leg.setdefault("buy_cancel_attempted_at", "")
            leg.setdefault("buy_cancel_terminal_failure", False)
            leg.setdefault("buy_cancel_reason", "")
            leg.setdefault("buy_cancel_provenance", {})
            leg.setdefault("buy_cancel_order_no", "")
            leg.setdefault("buy_cancel_order_date", "")
            leg.setdefault("buy_cancel_owner_registry_reconciliation_required", False)
            leg.setdefault("buy_owner_registry_reconciliation_required", False)
            leg.setdefault("target_owner_registry_reconciliation_required", False)
            leg.setdefault("last_buy_reconciled_at", "")
            leg.setdefault("last_buy_remaining_qty", 0)
            leg.setdefault("last_buy_reconcile_source_ok", False)
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

    def _episode_owner_context(
        self, *, leg: dict, action: str, ordinal: object
    ) -> OwnerOrderContext:
        trade_date = str(self._state.get("trade_date") or "").strip()
        leg_id = str(leg.get("leg_id") or "").strip()
        if not trade_date or not leg_id:
            raise OwnerRegistryError("episode_owner_identity_missing")
        position_id = f"episode:{self.strategy_name}:{self.policy.symbol}:{trade_date}"
        return OwnerOrderContext(
            owner_type="episode",
            owner_id=position_id,
            position_id=position_id,
            client_intent_id=f"{position_id}:{leg_id}:{action}:{ordinal}",
        )

    def _reserve_episode_intent(
        self,
        *,
        leg: dict,
        side: str,
        quantity: int,
        route: str,
        action: str,
        ordinal: object,
        original_order_no: str = "",
    ) -> tuple[str, OwnerOrderContext]:
        trade_date = str(self._state.get("trade_date") or "")
        try:
            policy = resolve_symbol_owner_policy(
                self.policy.symbol, target_date=trade_date
            )
        except (SymbolOwnerPolicyError, OSError, ValueError) as exc:
            raise OwnerRegistryError(
                f"episode_symbol_owner_policy_fail_closed:{type(exc).__name__}"
            ) from exc
        context = self._episode_owner_context(leg=leg, action=action, ordinal=ordinal)
        if not policy.coexistence_enabled:
            if policy.symbol_selected and not policy.owner_allowed(
                "episode", new_entry=side == "BUY" and action == "NEW"
            ):
                raise OwnerRegistryError("episode_owner_policy_action_forbidden")
            if self.owner_registry.symbol_registered(self.policy.symbol):
                raise OwnerRegistryError(
                    "registered_coexistence_symbol_requires_exact_date_policy"
                )
            return "", context
        if not self.owner_registry.decision_activation_matches(policy):
            raise OwnerRegistryError(
                "coexistence_policy_activation_missing_or_mismatched"
            )
        if not policy.owner_allowed(
            "episode", new_entry=side == "BUY" and action == "NEW"
        ):
            raise OwnerRegistryError("episode_owner_policy_action_forbidden")
        intent_id = self.owner_registry.reserve(
            context=context,
            symbol=self.policy.symbol,
            side=side,
            quantity=quantity,
            route=route,
            order_date=trade_date,
            action=action,
            original_order_no=original_order_no,
            authority_policy_id=policy.policy_id,
            authority_policy_hash=policy.policy_hash,
        )
        return intent_id, context

    def _bind_episode_submit(
        self,
        *,
        intent_id: str,
        result,
        reason: str = "",
    ) -> bool:
        if not intent_id:
            return True
        try:
            self.owner_registry.transition(
                intent_id,
                state=(
                    "ORDER_BOUND"
                    if result is not None and result.accepted
                    else (
                        "INTENT_AMBIGUOUS"
                        if result is None or result.ambiguous
                        else "INTENT_REJECTED"
                    )
                ),
                broker_order_no=(
                    result.order_no if result is not None and result.accepted else ""
                ),
                reason=(reason or (result.return_msg if result is not None else "")),
            )
            return bool(
                result is not None and (result.accepted or not result.ambiguous)
            )
        except OwnerRegistryError:
            try:
                self.owner_registry.transition(
                    intent_id,
                    state="INTENT_AMBIGUOUS",
                    reason="episode_registry_bind_failed",
                )
            except OwnerRegistryError:
                pass
            return False

    def _preserve_ambiguous_broker_submit(
        self,
        *,
        now: datetime,
        leg: dict,
        result,
        role: str,
        quantity: int,
        price: int = 0,
        reason: str,
    ) -> None:
        """Persist every broker-visible identifier before fail-closed blocking.

        A successful broker response followed by a registry journal failure must
        never leave the accepted order discoverable only in process memory.  An
        ambiguous response without an order number is also retained as an exact
        intent-level reconciliation requirement.
        """

        order_no = str(getattr(result, "order_no", "") or "").strip()
        accepted = bool(getattr(result, "accepted", False))
        ambiguous = bool(getattr(result, "ambiguous", False))
        if role == "buy":
            if order_no:
                leg.update(
                    {
                        "status": "BUY_OPEN",
                        "buy_order_no": order_no,
                        "buy_order_date": now.date().isoformat(),
                    }
                )
                self._own_order(order_no)
            leg["buy_owner_registry_reconciliation_required"] = True
        elif role == "target":
            if order_no:
                leg.update(
                    {
                        "status": "TARGET_OPEN",
                        "target_price": int(price),
                        "target_order_no": order_no,
                        "target_order_date": now.date().isoformat(),
                        "target_quantity": int(quantity),
                    }
                )
                self._own_order(order_no)
            leg["target_owner_registry_reconciliation_required"] = True
        elif role == "buy_cancel":
            if order_no:
                leg.update(
                    {
                        "buy_cancel_order_no": order_no,
                        "buy_cancel_order_date": now.date().isoformat(),
                    }
                )
                self._own_order(order_no)
            leg["buy_cancel_owner_registry_reconciliation_required"] = True
        else:  # pragma: no cover - internal programming error
            raise ValueError(f"unsupported_registry_reconciliation_role:{role}")

        self._state["owner_registry_reconciliation_required"] = True
        self._record(
            now,
            f"{role}_owner_registry_reconciliation_required",
            leg_id=leg.get("leg_id"),
            broker_order_no=order_no,
            broker_accepted=accepted,
            broker_ambiguous=ambiguous,
            owner_registry_intent_id=leg.get(
                {
                    "buy": "buy_owner_registry_intent_id",
                    "target": "target_owner_registry_intent_id",
                    "buy_cancel": "buy_cancel_owner_registry_intent_id",
                }[role]
            ),
            quantity=int(quantity),
            price=int(price),
            reason=reason,
        )

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

    def _entry_execution_velocity_decision(
        self, *, route: str, requested_quantity: int
    ) -> EntryExecutionVelocityDecision:
        try:
            snapshot = self.gateway.entry_execution_velocity_snapshot(route=route)
        except Exception as exc:
            snapshot = unavailable_entry_execution_velocity_snapshot(
                symbol=str(self.policy.symbol),
                route=route,
                error=type(exc).__name__,
            )
        return evaluate_entry_execution_velocity(
            snapshot, requested_quantity=requested_quantity
        )

    def _market_weakness_entry_decision(
        self, now: datetime
    ) -> MarketWeaknessEntryDecision:
        return evaluate_market_weakness_entry_guard(
            symbol=self.policy.symbol,
            owner="episode",
            now=now,
        )

    def _market_weakness_allows_new_buys(
        self,
        *,
        now: datetime,
        signal_bar: str = "",
        preserve_signal_for_recheck: bool = False,
        reference_price: int | None = None,
        target_price: int | None = None,
        required_quantity: int | None = None,
        expected_venues: tuple[str, ...] | list[str] | None = None,
        counterfactual_session: str | None = None,
    ) -> bool:
        decision = self._market_weakness_entry_decision(now)
        if not decision.blocked:
            return True
        fingerprint = ":".join(
            [
                decision.reason,
                decision.listing_market or "UNKNOWN",
                decision.observation_id or decision.phase,
                signal_bar,
            ]
        )
        self._state["pending_entry_confirmation"] = None
        if preserve_signal_for_recheck:
            self._state["last_evaluated_bar"] = ""
        self._state["blocked_reason"] = decision.reason
        features = dict(self._state.get("signal_features") or {})
        features["market_weakness_entry_guard"] = decision.event_fields()
        resolved_reference = int(
            reference_price or self._state.get("signal_close") or 0
        )
        resolved_quantity = int(required_quantity or EPISODE_TOTAL_QUANTITY)
        resolved_target = int(target_price or 0)
        if resolved_target <= 0 and resolved_reference > 0:
            resolved_target = move_price_by_ticks(
                resolved_reference, int(self.policy.target_ticks)
            )
        resolved_venues = list(
            expected_venues
            or [str(getattr(self.policy, "route", "SOR") or "SOR").upper()]
        )
        counterfactual_receipt = record_market_weakness_blocked_entry(
            decision,
            now=now,
            scope_id=self.entry_timing_scope_id,
            session=str(counterfactual_session or self.entry_timing_session),
            source_signal_id=(
                f"{self.policy.symbol}:{signal_bar}"
                if signal_bar
                else f"{self.policy.symbol}:{now.date().isoformat()}:planned_entry"
            ),
            signal_bar=signal_bar,
            reference_price=resolved_reference or None,
            target_price=resolved_target or None,
            required_quantity=resolved_quantity,
            expected_venues=resolved_venues,
        )
        features["market_weakness_counterfactual_observation"] = counterfactual_receipt
        self._state["signal_features"] = features
        if self._state.get("last_market_weakness_block_fingerprint") != fingerprint:
            self._state["last_market_weakness_block_fingerprint"] = fingerprint
            self._record(
                now,
                decision.reason,
                signal_bar=signal_bar,
                actual_order_submitted=False,
                market_weakness_counterfactual_observation=(counterfactual_receipt),
                **decision.event_fields(),
            )
        else:
            self._save()
        return False

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
        confirmation_delay_sec = int(features.get("entry_confirmation_delay_sec") or 0)
        confirmation_mode = str(
            (features.get("entry_timing_policy_provenance") or {}).get(
                "entry_confirmation_mode"
            )
            or "fixed_delay"
        )
        # Dynamic 0/1/3/5 confirmation already consumed exact-route 0B/0D and
        # cost-aware BBO at its selected checkpoint.  Re-running the legacy
        # fixed-delay comparison here would use a non-existent anchor snapshot
        # and turn every delayed dynamic ENTER into a false submit drought.
        if confirmation_delay_sec > 0 and confirmation_mode != DYNAMIC_MODE:
            planned_entry_prices = [
                int(leg.get("entry_price") or 0)
                for leg in self._state.get("legs", [])
                if leg.get("status") == "PLANNED"
                and str(leg.get("route") or normalized_route).upper()
                == normalized_route
                and int(leg.get("entry_price") or 0) > 0
            ]
            maximum_entry_price = max(planned_entry_prices, default=0)
            current_ask = int(decision.snapshot.best_ask)
            target_price = (
                self.policy.target_price(current_ask) if current_ask > 0 else 0
            )
            micro_decision = evaluate_executable_micro_confirmation(
                anchor_snapshot=features.get("entry_confirmation_anchor_snapshot"),
                current_snapshot=decision.snapshot,
                requested_quantity=requested_quantity,
                reference_price=int(
                    features.get("signal_close")
                    or features.get("opening_price")
                    or self._state.get("signal_close")
                    or 0
                ),
                maximum_entry_price=maximum_entry_price,
                target_price=target_price,
                policy=(features.get("entry_timing_policy_provenance") or {}).get(
                    "executable_confirmation"
                ),
            )
            features["entry_executable_micro_confirmation"] = (
                micro_decision.event_fields()
            )
            self._state["signal_features"] = features
            if not micro_decision.allowed:
                for leg in self._state.get("legs", []):
                    leg_route = str(leg.get("route") or normalized_route).upper()
                    if leg.get("status") == "PLANNED" and leg_route == normalized_route:
                        leg["status"] = "NO_FILL"
                self._state["blocked_reason"] = micro_decision.reason
                self._record(
                    now,
                    "entry_executable_micro_confirmation_blocked_before_buy",
                    route=normalized_route,
                    **micro_decision.event_fields(),
                )
                return False
            self._record(
                now,
                "entry_executable_micro_confirmation_passed",
                route=normalized_route,
                **micro_decision.event_fields(),
            )
        velocity_decision = self._entry_execution_velocity_decision(
            route=normalized_route,
            requested_quantity=requested_quantity,
        )
        features = dict(self._state.get("signal_features") or {})
        features["entry_execution_velocity"] = velocity_decision.event_fields()
        self._state["signal_features"] = features
        if not velocity_decision.allowed:
            for leg in self._state.get("legs", []):
                leg_route = str(leg.get("route") or normalized_route).upper()
                if leg.get("status") == "PLANNED" and leg_route == normalized_route:
                    leg["status"] = "NO_FILL"
            self._state["blocked_reason"] = velocity_decision.reason
            self._record(
                now,
                "entry_execution_velocity_blocked_before_buy",
                route=normalized_route,
                **velocity_decision.event_fields(),
            )
            return False
        self._record(
            now,
            "entry_execution_velocity_guard_passed",
            route=normalized_route,
            **velocity_decision.event_fields(),
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
            confirmation_mode = str(
                pending_confirmation.get("confirmation_mode") or "fixed_delay"
            )
            checkpoint_sec = pending_confirmation.get("checkpoint_sec")
            dynamic_state_valid = bool(
                confirmation_mode == DYNAMIC_MODE
                and delay_sec == 0
                and checkpoint_sec in {1, 3, 5}
                and abs((due_at - armed_at).total_seconds() - checkpoint_sec) <= 0.001
                and isinstance(pending_confirmation.get("dynamic_checkpoints"), dict)
                and isinstance(pending_confirmation.get("dynamic_anchor"), dict)
            )
            fixed_state_valid = bool(
                confirmation_mode == "fixed_delay"
                and delay_sec in {1, 3, 5}
                and abs((due_at - armed_at).total_seconds() - delay_sec) <= 0.001
            )
            if (
                armed_at.tzinfo is None
                or due_at.tzinfo is None
                or isinstance(pending_confirmation.get("delay_sec"), bool)
                or not (dynamic_state_valid or fixed_state_valid)
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

    def _execution(self, now: datetime, leg: dict, order_key: str):
        order_no = str(leg.get(order_key) or "")
        if not self._owns_order(order_no):
            raise ValueError(f"{order_key}_not_owned")
        date_key = (
            "buy_order_date" if order_key == "buy_order_no" else "target_order_date"
        )
        snapshot = self.gateway.execution_snapshot(
            order_no=order_no,
            order_date=str(leg.get(date_key) or ""),
            expected_order_qty=(
                int(leg.get("quantity", 0) or 0)
                if order_key == "buy_order_no"
                else int(leg.get("target_quantity", 0) or 0)
            ),
        )
        try:
            self._record_owner_execution(leg, order_key, snapshot)
        except OwnerRegistryError as exc:
            self._state["owner_registry_reconciliation_required"] = True
            reconciliation_key = (
                "buy_owner_registry_reconciliation_required"
                if order_key == "buy_order_no"
                else "target_owner_registry_reconciliation_required"
            )
            leg[reconciliation_key] = True
            self._block(
                now,
                "owner_registry_execution_reconciliation_required:"
                f"{leg.get('leg_id')}:{type(exc).__name__}",
            )
            raise
        return snapshot

    def _record_owner_execution(self, leg: dict, order_key: str, snapshot) -> None:
        order_no = str(leg.get(order_key) or "")
        date_key = (
            "buy_order_date" if order_key == "buy_order_no" else "target_order_date"
        )
        registry_intent_key = (
            "buy_owner_registry_intent_id"
            if order_key == "buy_order_no"
            else "target_owner_registry_intent_id"
        )
        intent_id = str(leg.get(registry_intent_key) or "")
        if intent_id and snapshot.source_ok and snapshot.found:
            context = self._episode_owner_context(
                leg=leg,
                action=("BUY" if order_key == "buy_order_no" else "TARGET"),
                ordinal=leg.get("leg_id"),
            )
            order_date = str(leg.get(date_key) or "")
            owner = self.owner_registry.order_owner(
                order_date=order_date, broker_order_no=order_no
            )
            if owner is None:
                # The exact broker snapshot heals an accepted submit whose
                # synchronous registry bind failed after transport.
                self.owner_registry.transition(
                    intent_id,
                    state="ORDER_BOUND",
                    broker_order_no=order_no,
                    reason="episode_exact_broker_snapshot_rebind",
                )
            else:
                self.owner_registry.assert_owner(
                    context=context,
                    order_date=order_date,
                    broker_order_no=order_no,
                )
            # Client intent identity is irrelevant for ownership checks; the
            # immutable owner and position identifiers are the authority.
            self.owner_registry.record_fill(
                context=context,
                symbol=self.policy.symbol,
                side=("BUY" if order_key == "buy_order_no" else "SELL"),
                order_quantity=(
                    int(leg.get("quantity", 0) or 0)
                    if order_key == "buy_order_no"
                    else int(leg.get("target_quantity", 0) or 0)
                ),
                order_date=order_date,
                broker_order_no=order_no,
                cumulative_filled_qty=int(snapshot.filled_qty or 0),
                cumulative_fill_amount=None,
            )
            if int(snapshot.remaining_qty or 0) == 0:
                self.owner_registry.transition(
                    intent_id,
                    state="ORDER_TERMINAL",
                    broker_order_no=order_no,
                    reason="episode_execution_snapshot_terminal",
                )
            reconciliation_key = (
                "buy_owner_registry_reconciliation_required"
                if order_key == "buy_order_no"
                else "target_owner_registry_reconciliation_required"
            )
            leg[reconciliation_key] = False
            self._state["owner_registry_reconciliation_required"] = any(
                bool(item.get(key))
                for item in self._state.get("legs", [])
                for key in (
                    "buy_owner_registry_reconciliation_required",
                    "target_owner_registry_reconciliation_required",
                    "buy_cancel_owner_registry_reconciliation_required",
                )
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
        route = str(getattr(self.policy, "route", "SOR") or "SOR").upper()
        target_attempt = int(leg.get("target_submit_attempt_count") or 0) + 1
        leg["target_submit_attempt_count"] = target_attempt
        intent_id = ""
        try:
            intent_id, _ = self._reserve_episode_intent(
                leg=leg,
                side="SELL",
                quantity=target_quantity,
                route=route,
                action="NEW",
                ordinal=f"TARGET:{target_attempt}",
            )
            leg["target_owner_registry_intent_id"] = intent_id
            self._save()
        except OwnerRegistryError as exc:
            self._block(
                now,
                f"target_submit_owner_registry_or_gateway_error:{leg['leg_id']}:{type(exc).__name__}",
            )
            return
        try:
            result = self.gateway.submit_limit_sell(
                price=target_price, quantity=target_quantity
            )
        except Exception as exc:
            self._bind_episode_submit(
                intent_id=intent_id, result=None, reason=type(exc).__name__
            )
            self._preserve_ambiguous_broker_submit(
                now=now,
                leg=leg,
                result=None,
                role="target",
                quantity=target_quantity,
                price=target_price,
                reason=f"target_broker_transport_exception:{type(exc).__name__}",
            )
            raise
        if not self._bind_episode_submit(intent_id=intent_id, result=result):
            self._preserve_ambiguous_broker_submit(
                now=now,
                leg=leg,
                result=result,
                role="target",
                quantity=target_quantity,
                price=target_price,
                reason="target_registry_bind_failed",
            )
            if not (
                intent_id
                and str(getattr(result, "order_no", "") or "").isdigit()
                and len(str(getattr(result, "order_no", "") or "")) == 7
            ):
                self._block(
                    now,
                    f"target_submit_owner_registry_ambiguous:{leg['leg_id']}",
                )
            return
        if result.ambiguous:
            self._preserve_ambiguous_broker_submit(
                now=now,
                leg=leg,
                result=result,
                role="target",
                quantity=target_quantity,
                price=target_price,
                reason="target_broker_submit_ambiguous",
            )
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
            snapshot = self._execution(now, leg, "target_order_no")
        except ValueError:
            self._block(now, f"target_order_not_owned:{leg.get('leg_id')}")
            return
        except OwnerRegistryError:
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
            current_open_reader = getattr(
                self.gateway, "current_open_sell_snapshot", None
            )
            if not callable(current_open_reader):
                self._record(now, "target_open_wait", leg_id=leg["leg_id"])
                return
            try:
                current_open = current_open_reader(
                    order_no=str(leg.get("target_order_no") or ""),
                    order_date=str(leg.get("target_order_date") or ""),
                    observed_date=now.date().isoformat(),
                )
            except Exception as exc:
                self._record(
                    now,
                    "target_current_open_reconciliation_wait",
                    leg_id=leg["leg_id"],
                    error=type(exc).__name__,
                )
                return
            if not bool(getattr(current_open, "source_ok", False)):
                self._record(
                    now,
                    "target_current_open_reconciliation_wait",
                    leg_id=leg["leg_id"],
                    error=str(
                        getattr(current_open, "error", "") or "source_unavailable"
                    ),
                )
                return
            successor_order_no = str(
                getattr(current_open, "successor_order_no", "") or ""
            ).strip()
            if successor_order_no:
                self._block(
                    now,
                    f"target_successor_order_not_owned:{leg.get('leg_id')}",
                )
                return
            if bool(getattr(current_open, "found", False)):
                self._record(
                    now,
                    "target_open_wait",
                    leg_id=leg["leg_id"],
                    current_open_source="ka10075_exact_order",
                )
                return
            leg["status"] = "HELD" if leg["position_qty"] > 0 else "COMPLETE"
            self._record(
                now,
                "target_terminal_absence_position_held",
                leg_id=leg["leg_id"],
                filled_qty=target_filled_qty,
                position_qty=leg["position_qty"],
                dated_execution_source="kt00007",
                current_open_source="ka10075_terminal_absence_confirmed",
            )

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

    def _submit_buy_cancel(self, leg: dict, now: datetime):
        original_intent_id = str(leg.get("buy_owner_registry_intent_id") or "")
        if not original_intent_id:
            return self.gateway.cancel_buy(order_no=str(leg["buy_order_no"]))
        original_context = self._episode_owner_context(
            leg=leg, action="BUY", ordinal=leg.get("leg_id")
        )
        self.owner_registry.assert_owner(
            context=original_context,
            order_date=str(leg.get("buy_order_date") or ""),
            broker_order_no=str(leg.get("buy_order_no") or ""),
        )
        route = str(getattr(self.policy, "route", "SOR") or "SOR").upper()
        intent_id, _ = self._reserve_episode_intent(
            leg=leg,
            side="BUY",
            quantity=max(
                0, int(leg.get("last_buy_remaining_qty") or leg.get("quantity") or 0)
            ),
            route=route,
            action="CANCEL",
            ordinal=int(leg.get("buy_cancel_attempt_count") or 0),
            original_order_no=str(leg.get("buy_order_no") or ""),
        )
        leg["buy_cancel_owner_registry_intent_id"] = intent_id
        self._save()
        try:
            result = self.gateway.cancel_buy(order_no=str(leg["buy_order_no"]))
        except Exception as exc:
            self._bind_episode_submit(
                intent_id=intent_id,
                result=None,
                reason=type(exc).__name__,
            )
            self._preserve_ambiguous_broker_submit(
                now=now,
                leg=leg,
                result=None,
                role="buy_cancel",
                quantity=max(
                    0,
                    int(leg.get("last_buy_remaining_qty") or leg.get("quantity") or 0),
                ),
                reason=f"buy_cancel_transport_exception:{type(exc).__name__}",
            )
            raise
        registry_bound = self._bind_episode_submit(intent_id=intent_id, result=result)
        if not registry_bound or result.ambiguous:
            self._preserve_ambiguous_broker_submit(
                now=now,
                leg=leg,
                result=result,
                role="buy_cancel",
                quantity=max(
                    0,
                    int(leg.get("last_buy_remaining_qty") or leg.get("quantity") or 0),
                ),
                reason=(
                    "buy_cancel_registry_bind_failed"
                    if not registry_bound
                    else "buy_cancel_broker_submit_ambiguous"
                ),
            )
        if not registry_bound:
            raise OwnerRegistryError("buy_cancel_registry_bind_failed")
        return result

    def _buy_cancel_route_fields(self, leg: dict) -> dict[str, object]:
        return {}

    def _cancel_buy(
        self,
        now: datetime,
        leg: dict,
        elapsed: int,
        *,
        cancel_reason: str = "entry_validity_expired",
        provenance: dict[str, object] | None = None,
    ) -> None:
        provenance = dict(
            provenance
            or (
                leg.get("buy_cancel_provenance")
                if isinstance(leg.get("buy_cancel_provenance"), dict)
                else {}
            )
        )
        cancel_reason = str(
            cancel_reason or leg.get("buy_cancel_reason") or "entry_validity_expired"
        )
        order_no = str(leg.get("buy_order_no") or "").strip()
        if (
            not order_no
            or not self._owns_order(order_no)
            or str(leg.get("buy_order_date") or "") != now.date().isoformat()
        ):
            fingerprint = f"{leg.get('leg_id')}:{order_no}:{cancel_reason}"
            if (
                self._state.get("last_buy_cancel_owner_block_fingerprint")
                != fingerprint
            ):
                self._state["last_buy_cancel_owner_block_fingerprint"] = fingerprint
                self._record(
                    now,
                    "buy_cancel_blocked_owner_or_date_mismatch",
                    leg_id=leg.get("leg_id"),
                    buy_order_no=order_no,
                    buy_order_date=leg.get("buy_order_date"),
                    cancel_reason=cancel_reason,
                    **self._buy_cancel_route_fields(leg),
                    **provenance,
                )
            return
        if leg.get("buy_cancel_terminal_failure"):
            return
        attempts = int(leg.get("buy_cancel_attempt_count", 0) or 0)
        if attempts >= self.BUY_CANCEL_MAX_ATTEMPTS:
            leg.update(
                {
                    "status": "BUY_OPEN",
                    "buy_cancel_requested": False,
                    "buy_cancel_ambiguous": False,
                    "buy_cancel_terminal_failure": True,
                }
            )
            self._record(
                now,
                "buy_cancel_terminal_failure",
                leg_id=leg["leg_id"],
                buy_order_no=order_no,
                cancel_attempt_count=attempts,
                cancel_reason=cancel_reason,
                **self._buy_cancel_route_fields(leg),
                **provenance,
            )
            return
        last_attempt_text = str(leg.get("buy_cancel_attempted_at") or "")
        if last_attempt_text:
            try:
                last_attempt = datetime.fromisoformat(last_attempt_text).astimezone(KST)
            except ValueError:
                last_attempt = None
            if (
                last_attempt is not None
                and (now - last_attempt).total_seconds() < self.BUY_CANCEL_RETRY_SEC
            ):
                return
        leg["status"] = "BUY_CANCEL_SUBMITTING"
        leg["buy_cancel_attempt_count"] = attempts + 1
        leg["buy_cancel_attempted_at"] = _iso(now)
        leg["buy_cancel_reason"] = cancel_reason
        leg["buy_cancel_provenance"] = provenance
        self._record(
            now,
            "buy_cancel_intent",
            leg_id=leg["leg_id"],
            completed_bars_after_signal=elapsed,
            buy_order_no=order_no,
            cancel_attempt_count=attempts + 1,
            cancel_reason=cancel_reason,
            **self._buy_cancel_route_fields(leg),
            **provenance,
        )
        try:
            result = self._submit_buy_cancel(leg, now)
        except Exception as exc:
            leg.update(
                {
                    "status": "BUY_CANCEL_PENDING",
                    "buy_cancel_requested": True,
                    "buy_cancel_ambiguous": True,
                }
            )
            self._record(
                now,
                "buy_cancel_ambiguous",
                leg_id=leg["leg_id"],
                buy_order_no=order_no,
                error=type(exc).__name__,
                cancel_attempt_count=attempts + 1,
                cancel_reason=cancel_reason,
                **self._buy_cancel_route_fields(leg),
                **provenance,
            )
            return
        if result.ambiguous:
            leg.update(
                {
                    "status": "BUY_CANCEL_PENDING",
                    "buy_cancel_requested": True,
                    "buy_cancel_ambiguous": True,
                }
            )
            self._record(
                now,
                "buy_cancel_ambiguous",
                leg_id=leg["leg_id"],
                buy_order_no=order_no,
                return_code=result.return_code,
                cancel_attempt_count=attempts + 1,
                cancel_reason=cancel_reason,
                **self._buy_cancel_route_fields(leg),
                **provenance,
            )
            return
        if not result.accepted:
            leg.update(
                {
                    "status": "BUY_OPEN",
                    "buy_cancel_requested": False,
                    "buy_cancel_ambiguous": False,
                }
            )
            self._record(
                now,
                "buy_cancel_rejected_retryable",
                leg_id=leg["leg_id"],
                buy_order_no=order_no,
                return_code=result.return_code,
                cancel_attempt_count=attempts + 1,
                cancel_reason=cancel_reason,
                **self._buy_cancel_route_fields(leg),
                **provenance,
            )
            return
        leg.update(
            {
                "status": "BUY_CANCEL_PENDING",
                "buy_cancel_requested": True,
                "buy_cancel_ambiguous": False,
            }
        )
        self._own_order(result.order_no)
        self._record(
            now,
            "buy_cancel_submitted",
            leg_id=leg["leg_id"],
            buy_order_no=order_no,
            cancel_order_no=result.order_no,
            cancel_attempt_count=attempts + 1,
            cancel_reason=cancel_reason,
            **self._buy_cancel_route_fields(leg),
            **provenance,
        )

    def _reconcile_buy(self, now: datetime, leg: dict, elapsed: int | None) -> None:
        try:
            snapshot = self._execution(now, leg, "buy_order_no")
        except ValueError:
            self._block(now, f"buy_order_not_owned:{leg.get('leg_id')}")
            return
        except OwnerRegistryError:
            return
        if not snapshot.source_ok:
            self._record(
                now,
                "buy_reconciliation_wait",
                leg_id=leg["leg_id"],
                error=snapshot.error,
            )
            return
        if snapshot.found:
            leg["last_buy_reconciled_at"] = _iso(now)
            leg["last_buy_remaining_qty"] = int(snapshot.remaining_qty)
            leg["last_buy_reconcile_source_ok"] = True
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
                leg["buy_cancel_ambiguous"] = False
                self._submit_target(now, leg)
            elif not leg.get("buy_cancel_requested"):
                self._cancel_buy(
                    now,
                    leg,
                    elapsed or 0,
                    cancel_reason="partial_fill_remainder",
                )
            elif leg.get("buy_cancel_ambiguous"):
                self._cancel_buy(
                    now,
                    leg,
                    elapsed or 0,
                    cancel_reason=str(
                        leg.get("buy_cancel_reason") or "entry_validity_expired"
                    ),
                )
            return
        if snapshot.found and snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            leg.update(
                {
                    "status": "NO_FILL",
                    "buy_cancel_requested": False,
                    "buy_cancel_ambiguous": False,
                }
            )
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
            if leg.get("buy_cancel_ambiguous"):
                self._cancel_buy(
                    now,
                    leg,
                    elapsed or 0,
                    cancel_reason=str(
                        leg.get("buy_cancel_reason") or "entry_validity_expired"
                    ),
                )
                return
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

    def _cancel_market_weakness_open_buys(
        self,
        *,
        now: datetime,
        elapsed: int | None,
    ) -> None:
        open_legs = [
            leg
            for leg in self._state.get("legs", [])
            if leg.get("status") == "BUY_OPEN"
            and not leg.get("buy_cancel_terminal_failure")
        ]
        if not open_legs:
            return
        decision = self._market_weakness_entry_decision(now)
        if not decision.exact_market_open_buy_cancel_allowed:
            return
        features = dict(self._state.get("signal_features") or {})
        features["market_weakness_entry_guard"] = decision.event_fields()
        self._state["signal_features"] = features
        for leg in open_legs:
            order_no = str(leg.get("buy_order_no") or "").strip()
            exact_owner = bool(
                order_no
                and self._owns_order(order_no)
                and str(leg.get("buy_order_date") or "") == now.date().isoformat()
            )
            fresh_reconciliation = bool(
                leg.get("last_buy_reconciled_at") == _iso(now)
                and leg.get("last_buy_reconcile_source_ok") is True
                and int(leg.get("last_buy_remaining_qty", 0) or 0) > 0
            )
            if not exact_owner or not fresh_reconciliation:
                fingerprint = ":".join(
                    [
                        str(leg.get("leg_id") or ""),
                        order_no,
                        decision.observation_id or decision.phase,
                        "owner" if not exact_owner else "reconciliation",
                    ]
                )
                if (
                    self._state.get("last_market_weakness_cancel_block_fingerprint")
                    != fingerprint
                ):
                    self._state["last_market_weakness_cancel_block_fingerprint"] = (
                        fingerprint
                    )
                    self._record(
                        now,
                        "market_weakness_buy_cancel_blocked_exact_order_check",
                        leg_id=leg.get("leg_id"),
                        buy_order_no=order_no,
                        exact_owner=exact_owner,
                        fresh_reconciliation=fresh_reconciliation,
                        last_buy_reconciled_at=leg.get("last_buy_reconciled_at"),
                        **self._buy_cancel_route_fields(leg),
                        **decision.event_fields(),
                    )
                continue
            self._cancel_buy(
                now,
                leg,
                elapsed or 0,
                cancel_reason="market_weakness_active_exact_market",
                provenance=decision.event_fields(),
            )

    def _submit_planned_buys(self, now: datetime) -> None:
        if any(
            leg.get("status") == "PLANNED" for leg in self._state.get("legs", [])
        ) and not self._market_weakness_allows_new_buys(
            now=now,
            signal_bar=str(self._state.get("signal_bar") or ""),
        ):
            return
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
            route = str(getattr(self.policy, "route", "SOR") or "SOR").upper()
            buy_attempt = int(leg.get("buy_submit_attempt_count") or 0) + 1
            leg["buy_submit_attempt_count"] = buy_attempt
            intent_id = ""
            try:
                intent_id, _ = self._reserve_episode_intent(
                    leg=leg,
                    side="BUY",
                    quantity=int(leg["quantity"]),
                    route=route,
                    action="NEW",
                    ordinal=f"BUY:{route}:{buy_attempt}",
                )
                leg["buy_owner_registry_intent_id"] = intent_id
                self._save()
            except OwnerRegistryError as exc:
                self._block(
                    now,
                    f"buy_submit_owner_registry_or_gateway_error:{leg['leg_id']}:{type(exc).__name__}",
                )
                return
            try:
                result = self.gateway.submit_limit_buy(
                    price=int(leg["entry_price"]), quantity=int(leg["quantity"])
                )
            except Exception as exc:
                self._bind_episode_submit(
                    intent_id=intent_id,
                    result=None,
                    reason=type(exc).__name__,
                )
                self._preserve_ambiguous_broker_submit(
                    now=now,
                    leg=leg,
                    result=None,
                    role="buy",
                    quantity=int(leg["quantity"]),
                    price=int(leg["entry_price"]),
                    reason=f"buy_broker_transport_exception:{type(exc).__name__}",
                )
                raise
            if not self._bind_episode_submit(intent_id=intent_id, result=result):
                self._preserve_ambiguous_broker_submit(
                    now=now,
                    leg=leg,
                    result=result,
                    role="buy",
                    quantity=int(leg["quantity"]),
                    price=int(leg["entry_price"]),
                    reason="buy_registry_bind_failed",
                )
                if not (
                    intent_id
                    and str(getattr(result, "order_no", "") or "").isdigit()
                    and len(str(getattr(result, "order_no", "") or "")) == 7
                ):
                    self._block(
                        now,
                        f"buy_submit_owner_registry_ambiguous:{leg['leg_id']}",
                    )
                return
            if result.ambiguous:
                self._preserve_ambiguous_broker_submit(
                    now=now,
                    leg=leg,
                    result=result,
                    role="buy",
                    quantity=int(leg["quantity"]),
                    price=int(leg["entry_price"]),
                    reason="buy_broker_submit_ambiguous",
                )
                self._block(now, f"buy_submit_ambiguous:{leg['leg_id']}")
                return
            if not result.accepted:
                if result.return_code == "AUTHORITY_BLOCKED":
                    leg["status"] = "PLANNED"
                    self._record(
                        now,
                        "new_buy_authority_wait",
                        leg_id=leg["leg_id"],
                        reason=result.return_msg,
                    )
                    return
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
                active_policy = resolve_entry_confirmation_policy(
                    target_date=now.date(),
                    owner=self.entry_timing_owner,
                    scope_id=self.entry_timing_scope_id,
                    symbol=str(self.policy.symbol),
                    session=self.entry_timing_session,
                    entry_state="UNSPECIFIED",
                )
                active_delay = int(active_policy["delay_sec"])
                active_provenance = dict(active_policy["provenance"])
                pending_mode = str(
                    pending_confirmation.get("confirmation_mode") or "fixed_delay"
                )
                if (
                    active_delay != int(pending_confirmation["delay_sec"])
                    or active_policy["mode"] != pending_mode
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
        if not self._market_weakness_allows_new_buys(
            now=now,
            signal_bar=latest_iso,
            preserve_signal_for_recheck=True,
            reference_price=int(signal.signal_bar.close_price),
            target_price=move_price_by_ticks(
                int(signal.signal_bar.close_price), int(self.policy.target_ticks)
            ),
            required_quantity=EPISODE_TOTAL_QUANTITY,
            expected_venues=[
                str(getattr(self.policy, "route", "SOR") or "SOR").upper()
            ],
        ):
            return self.snapshot()
        if confirmed_pending:
            delay_sec = int(pending_confirmation["delay_sec"])
            signal_decision_at = str(pending_confirmation["armed_at"])
            timing_policy_provenance = dict(
                pending_confirmation.get("policy_provenance") or {}
            )
            if (
                str(pending_confirmation.get("confirmation_mode") or "fixed_delay")
                == DYNAMIC_MODE
            ):
                armed_at = datetime.fromisoformat(signal_decision_at)
                checkpoint_sec = int(pending_confirmation["checkpoint_sec"])
                runtime_cost = (
                    timing_policy_provenance.get("executable_confirmation") or {}
                ).get("round_trip_cost_pct")
                dynamic_step = advance_live_dynamic_confirmation(
                    now=now,
                    signal_decision_at=armed_at,
                    checkpoint_sec=checkpoint_sec,
                    prior_checkpoints=pending_confirmation.get("dynamic_checkpoints"),
                    prior_anchor=pending_confirmation.get("dynamic_anchor"),
                    symbol=str(self.policy.symbol),
                    route=str(getattr(self.policy, "route", "SOR") or "SOR").upper(),
                    owner="episode",
                    baseline_fill_price=int(signal.signal_bar.close_price),
                    owner_entry_limit_price=max(
                        int(plan["entry_price"]) for plan in plans
                    ),
                    owner_target_price=move_price_by_ticks(
                        int(signal.signal_bar.close_price),
                        int(self.policy.target_ticks),
                    ),
                    round_trip_cost_pct=runtime_cost,
                    widget_take_profit=False,
                )
                if dynamic_step["action"] == "WAIT":
                    next_checkpoint = int(dynamic_step["next_checkpoint_sec"])
                    pending_confirmation.update(
                        {
                            "due_at": (
                                armed_at + timedelta(seconds=next_checkpoint)
                            ).isoformat(),
                            "checkpoint_sec": next_checkpoint,
                            "dynamic_checkpoints": dynamic_step["checkpoints"],
                            "dynamic_anchor": dynamic_step["anchor"],
                        }
                    )
                    self._state["pending_entry_confirmation"] = pending_confirmation
                    self._record(
                        now,
                        "entry_dynamic_confirmation_wait",
                        signal_bar=latest_iso,
                        checkpoint_sec=next_checkpoint,
                        dynamic_confirmation=dynamic_step,
                    )
                    return self.snapshot()
                self._state["pending_entry_confirmation"] = None
                if dynamic_step["action"] == "REJECT":
                    self._record(
                        now,
                        "entry_dynamic_confirmation_rejected",
                        signal_bar=latest_iso,
                        dynamic_confirmation=dynamic_step,
                    )
                    return self.snapshot()
                delay_sec = int(
                    dynamic_step.get("selected_delay_sec") or checkpoint_sec
                )
                timing_policy_provenance["dynamic_runtime_decision"] = dynamic_step
        else:
            timing_policy = resolve_entry_confirmation_policy(
                target_date=now.date(),
                owner=self.entry_timing_owner,
                scope_id=self.entry_timing_scope_id,
                symbol=str(self.policy.symbol),
                session=self.entry_timing_session,
                entry_state="UNSPECIFIED",
            )
            delay_sec = int(timing_policy["delay_sec"])
            timing_policy_provenance = dict(timing_policy["provenance"])
            signal_decision_at = now.isoformat()
            if timing_policy["mode"] == DYNAMIC_MODE:
                runtime_cost = (
                    timing_policy_provenance.get("executable_confirmation") or {}
                ).get("round_trip_cost_pct")
                dynamic_step = advance_live_dynamic_confirmation(
                    now=now,
                    signal_decision_at=now,
                    checkpoint_sec=0,
                    prior_checkpoints={},
                    prior_anchor={},
                    symbol=str(self.policy.symbol),
                    route=str(getattr(self.policy, "route", "SOR") or "SOR").upper(),
                    owner="episode",
                    baseline_fill_price=int(signal.signal_bar.close_price),
                    owner_entry_limit_price=max(
                        int(plan["entry_price"]) for plan in plans
                    ),
                    owner_target_price=move_price_by_ticks(
                        int(signal.signal_bar.close_price),
                        int(self.policy.target_ticks),
                    ),
                    round_trip_cost_pct=runtime_cost,
                    widget_take_profit=False,
                )
                if dynamic_step["action"] == "WAIT":
                    next_checkpoint = int(dynamic_step["next_checkpoint_sec"])
                    due_at = now + timedelta(seconds=next_checkpoint)
                    self._state["pending_entry_confirmation"] = {
                        "signal_bar": latest_iso,
                        "signal_close": int(latest.close_price),
                        "armed_at": signal_decision_at,
                        "due_at": due_at.isoformat(),
                        "delay_sec": 0,
                        "checkpoint_sec": next_checkpoint,
                        "confirmation_mode": DYNAMIC_MODE,
                        "policy_provenance": timing_policy_provenance,
                        "dynamic_checkpoints": dynamic_step["checkpoints"],
                        "dynamic_anchor": dynamic_step["anchor"],
                    }
                    self._record(
                        now,
                        "entry_dynamic_confirmation_armed",
                        signal_bar=latest_iso,
                        checkpoint_sec=next_checkpoint,
                        due_at=due_at.isoformat(),
                        timing_policy_hash=timing_policy_provenance.get("policy_hash"),
                        dynamic_confirmation=dynamic_step,
                    )
                    return self.snapshot()
                if dynamic_step["action"] == "REJECT":
                    self._record(
                        now,
                        "entry_dynamic_confirmation_rejected",
                        signal_bar=latest_iso,
                        dynamic_confirmation=dynamic_step,
                    )
                    return self.snapshot()
                delay_sec = int(dynamic_step.get("selected_delay_sec") or 0)
                timing_policy_provenance["dynamic_runtime_decision"] = dynamic_step
            elif delay_sec > 0:
                due_at = now + timedelta(seconds=delay_sec)
                anchor_liquidity = self._entry_liquidity_decision(
                    route=str(getattr(self.policy, "route", "SOR") or "SOR").upper(),
                    requested_quantity=EPISODE_TOTAL_QUANTITY,
                )
                anchor_snapshot = anchor_liquidity.event_fields()[
                    "entry_liquidity_snapshot"
                ]
                self._state["pending_entry_confirmation"] = {
                    "signal_bar": latest_iso,
                    "signal_close": int(latest.close_price),
                    "armed_at": signal_decision_at,
                    "due_at": due_at.isoformat(),
                    "delay_sec": delay_sec,
                    "policy_provenance": timing_policy_provenance,
                    "anchor_liquidity_snapshot": anchor_snapshot,
                }
                self._record(
                    now,
                    "entry_confirmation_armed",
                    signal_bar=latest_iso,
                    delay_sec=delay_sec,
                    due_at=due_at.isoformat(),
                    timing_policy_hash=timing_policy_provenance.get("policy_hash"),
                    anchor_liquidity_snapshot=anchor_snapshot,
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
                    "entry_confirmation_anchor_snapshot": (
                        pending_confirmation.get("anchor_liquidity_snapshot")
                        if isinstance(pending_confirmation, dict)
                        else None
                    ),
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
        if self._state.get("status") != "BLOCKED":
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
        self._cancel_market_weakness_open_buys(now=now, elapsed=elapsed)
        if self._state.get("status") == "BLOCKED":
            return self.snapshot()
        self._submit_planned_buys(now)
        if self._state.get("status") == "BLOCKED":
            return self.snapshot()
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
