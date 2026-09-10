"""Concrete owner port and restartable single-lot session, not live activation.

The original owner supplies its atomic state save, lifecycle-lock proof and
account/manual/pending-BUY/all-venue custody guard. No private state file,
thread, broker account or research-to-live authority is created here. A trusted
envelope/receipt verifier must authorize the complete immutable binding; a
self-hashed record is integrity evidence, never authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
from typing import Callable

from src.trading.config.machine_adaptive_exit_policy import (
    canonical_sha256,
    parse_exit_policy,
)
from src.trading.order.owner_custody_registry import (
    OwnerOrderContext,
    OwnerRegistryError,
)
from .broker import RegisteredSellAdapter, SellSnapshot, SellWrite
from .driver import (
    BrokerProof,
    DriverState,
    ExecutionBounds,
    SubmitReceipt,
    advance_exit,
    rebind_remaining_quantity,
)
from .models import Clock, DecisionState, ExitPolicy, Position, Snapshot, finite
from .reducer import ExitEvent, ExitState, OrderKey, reduce_event
from .source import OwnerScope, normalize_position

SCHEMA = "machine_adaptive_exit_owner_session_v1"


def _exact(cls, raw):
    if not isinstance(raw, dict) or set(raw) != {f.name for f in fields(cls)}:
        raise ValueError("owner_session_schema_fields_invalid")
    return dict(raw)


def _digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


@dataclass(frozen=True)
class OwnerSession:
    policy: ExitPolicy
    # Immutable original filled lot; current remaining/epoch are in driver.
    position: Position
    bounds: ExecutionBounds
    context: OwnerOrderContext
    target_intent_id: str
    approval_receipt_hash: str
    driver: DriverState

    @property
    def binding(self) -> dict:
        return {
            "schema": SCHEMA,
            "policy": asdict(self.policy),
            "position": asdict(self.position),
            "bounds": asdict(self.bounds),
            "context": asdict(self.context),
            "target": asdict(self.driver.orders.target),
            "target_intent_id": self.target_intent_id,
            "approval_receipt_hash": self.approval_receipt_hash,
        }

    @property
    def binding_hash(self) -> str:
        return canonical_sha256(self.binding)

    @property
    def remaining_position(self) -> Position:
        s = self.driver.orders
        epoch = s.position_epoch
        if s.open_qty > 0 and self.driver.decision.open_qty != s.open_qty:
            epoch = canonical_sha256(
                {
                    "binding": self.binding_hash,
                    "target_fill": s.target_filled_qty,
                    "exit_fill": s.exit_filled_qty,
                }
            )
        return replace(
            self.position,
            open_qty=s.open_qty,
            position_epoch=epoch,
        )

    @property
    def manager_required(self) -> bool:
        # Recovery/attempt exhaustion/missing quotes do not mean completed.
        return self.driver.orders.phase != "FLAT"

    def validate(self) -> None:
        self.context.validate()
        scope = OwnerScope(*self.policy.scope_key.split("|"))
        normalize_position(asdict(self.position), scope=scope)
        parse_exit_policy(asdict(self.policy))
        ExecutionBounds(**asdict(self.bounds))
        if (
            self.context.owner_type
            != {"widget": "widget_auto_trade", "episode": "episode"}[scope.owner]
            or not isinstance(self.target_intent_id, str)
            or not self.target_intent_id
            or not _digest(self.approval_receipt_hash)
            or not _digest(self.position.cost_contract_hash)
        ):
            raise ValueError("owner_session_binding_invalid")
        s, d, p = self.driver.orders, self.driver.decision, self.position
        reduce_event(
            s,
            ExitEvent(
                "validate",
                "RECOVERY_REQUIRED",
                s.owner_id,
                s.episode_id,
                s.lot_id,
                s.policy_hash,
                s.position_epoch,
                s.intent_id or "validate",
                s.target,
            ),
        )
        if (
            (s.owner_id, s.episode_id, s.lot_id) != (p.owner_id, p.episode_id, p.lot_id)
            or s.policy_hash != self.policy.policy_hash
            or d.policy_hash != s.policy_hash
            or s.buy_filled_qty != p.open_qty
            or d.first_fill_at_ms != p.first_fill_at_ms
            or d.position_epoch != s.position_epoch
            or type(d.open_qty) is not int
            or not s.open_qty <= d.open_qty <= p.open_qty
            or type(d.trail_active) is not bool
            or type(d.extensions) is not int
            or d.extensions not in (0, 1)
            or (s.phase == "FLAT" and (s.open_qty or s.reserved_qty))
            or s.exit_attempts > self.bounds.maximum_sell_attempts
            or (
                s.phase in ("EXIT_WORKING", "EXIT_CANCEL_PENDING")
                and (s.exit_order is None or self.driver.submitted_at_ms is None)
            )
            or (s.phase == "EXIT_SUBMITTING" and not s.exit_reserved_qty)
            or (
                s.phase
                in (
                    "RESIDUAL_READY",
                    "TRAIL_ACTIVE",
                    "EXIT_SUBMITTING",
                    "EXIT_WORKING",
                    "EXIT_CANCEL_PENDING",
                )
                and not s.target_terminal
            )
            or (s.exit_order is not None and s.exit_order not in s.exit_order_history)
            or s.target in s.exit_order_history
        ):
            raise ValueError("owner_session_driver_binding_invalid")
        for value in (
            self.driver.submitted_at_ms,
            self.driver.unprotected_since_ms,
            d.last_observed_at_ms,
        ):
            if value is not None and (
                type(value) is not int or value < p.first_fill_at_ms
            ):
                raise ValueError("owner_session_timestamp_invalid")
        if any(
            v is not None and (type(v) is not int or v <= 0)
            for v in (d.extension_until_active_ms, d.extension_granted_at_active_ms)
        ):
            raise ValueError("owner_session_extension_time_invalid")
        if (
            d.extensions == 0
            and (
                d.extension_until_active_ms is not None
                or d.extension_granted_at_active_ms is not None
            )
            or d.extensions == 1
            and (
                d.extension_granted_at_active_ms is None
                or d.extension_granted_at_active_ms < self.policy.soft_sec * 1000
                or d.extension_until_active_ms
                != int(
                    d.extension_granted_at_active_ms + self.policy.extension_sec * 1000
                )
            )
            or d.last_observed_at_ms is None
            and (d.source_epoch is not None or d.sequence is not None)
            or d.last_observed_at_ms is not None
            and (
                not isinstance(d.source_epoch, str)
                or not d.source_epoch
                or type(d.sequence) is not int
                or d.sequence < 0
            )
            or self.driver.alert_reason is not None
            and not isinstance(self.driver.alert_reason, str)
        ):
            raise ValueError("owner_session_decision_state_invalid")
        if any(
            v is not None and (not finite(v) or v <= 0)
            for v in (d.high_water, d.stop_price, s.high_water, s.stop_price)
        ):
            raise ValueError("owner_session_trail_value_invalid")
        if s.phase == "TRAIL_ACTIVE" and (
            not d.trail_active
            or not finite(d.high_water)
            or not finite(d.stop_price)
            or (d.high_water, d.stop_price) != (s.high_water, s.stop_price)
        ):
            raise ValueError("owner_session_trail_binding_invalid")
        if (
            not isinstance(s.journal, tuple)
            or any(
                not isinstance(row, tuple)
                or len(row) != 2
                or not isinstance(row[0], str)
                or not row[0]
                or not _digest(row[1])
                for row in s.journal
            )
            or len(dict(s.journal)) != len(s.journal)
        ):
            raise ValueError("owner_session_journal_invalid")

    def to_payload(self) -> dict:
        self.validate()
        result = {"schema": SCHEMA, **asdict(self)}
        result["canonical_sha256"] = canonical_sha256(result)
        return result

    @classmethod
    def from_payload(cls, payload: dict) -> OwnerSession:
        if (
            not isinstance(payload, dict)
            or set(payload)
            != ({f.name for f in fields(cls)} | {"schema", "canonical_sha256"})
            or payload.get("schema") != SCHEMA
            or payload.get("canonical_sha256") != canonical_sha256(payload)
        ):
            raise ValueError("owner_session_schema_or_hash_invalid")
        try:
            driver = _exact(DriverState, payload["driver"])
            orders = _exact(ExitState, driver["orders"])
            orders["target"] = OrderKey(**_exact(OrderKey, orders["target"]))
            if orders["exit_order"] is not None:
                orders["exit_order"] = OrderKey(
                    **_exact(OrderKey, orders["exit_order"])
                )
            orders["exit_order_history"] = tuple(
                OrderKey(**_exact(OrderKey, row))
                for row in orders["exit_order_history"]
            )
            orders["journal"] = tuple(tuple(row) for row in orders["journal"])
            driver["orders"] = ExitState(**orders)
            driver["decision"] = DecisionState(
                **_exact(DecisionState, driver["decision"])
            )
            result = cls(
                parse_exit_policy(payload["policy"]),
                Position(**_exact(Position, payload["position"])),
                ExecutionBounds(**_exact(ExecutionBounds, payload["bounds"])),
                OwnerOrderContext(**_exact(OwnerOrderContext, payload["context"])),
                payload["target_intent_id"],
                payload["approval_receipt_hash"],
                DriverState(**driver),
            )
            result.validate()
            return result
        except (TypeError, AttributeError, KeyError) as exc:
            raise ValueError("owner_session_schema_invalid") from exc


class RegisteredOwnerExitPort:
    """One independently protected target/lot, driven under the original lock.

    Factories are the existing gateway.adaptive_exit_adapter methods. The
    original owner must persist the *whole* supplied payload atomically and
    exclude this claimed lot from its normal target/source-EXIT writers. This
    class is connected through optional owner-loop services, not an installed
    launcher bootstrap or a PREOPEN publisher.
    """

    def __init__(
        self,
        *,
        session: OwnerSession,
        adapter_factory: Callable,
        persist_record: Callable[[dict], None],
        lock_held: Callable[[], bool],
        owner_guard: Callable,
        authorize_binding: Callable[[dict], bool] | None = None,
    ):
        session.validate()
        self.session = session
        self._save_record, self._lock, self._owner_guard = (
            persist_record,
            lock_held,
            owner_guard,
        )
        self._authorize = authorize_binding
        self._write_quote = None
        self._quote_required = False
        self._source_gap = ""
        self._receipt_only = True  # No write until a step supplies a valid clock.
        self._adapter = adapter_factory(self._transport_guard)
        scope = OwnerScope(*session.policy.scope_key.split("|"))
        if (
            not isinstance(self._adapter, RegisteredSellAdapter)
            or self._adapter.context != session.context
            or self._adapter.symbol != scope.symbol
            or self._adapter.policy_hash != session.policy.policy_hash
            or self._adapter.write_guard != self._transport_guard
        ):
            raise ValueError("owner_port_adapter_binding_mismatch")
        target = self._adapter._owned(session.driver.orders.target)
        if (
            target["intent_id"] != session.target_intent_id
            or target["route"] != scope.route
            or target["quantity"] != session.position.open_qty
        ):
            raise ValueError("owner_port_independent_target_binding_required")
        predecessor = session.driver.orders.target
        for order in session.driver.orders.exit_order_history:
            row = self._adapter._owned(order)
            if (
                row.get("client_intent_id")
                != self._adapter._replacement_client_id(predecessor)
                or row.get("authority_policy_id") != "machine_adaptive_exit_v1"
                or row.get("authority_policy_hash") != session.policy.policy_hash
            ):
                raise ValueError("owner_port_replacement_chain_mismatch")
            predecessor = order
        if (
            session.driver.orders.exit_order is not None
            and predecessor != session.driver.orders.exit_order
        ):
            raise ValueError("owner_port_latest_replacement_mismatch")

    def _authorized(self):
        return (
            self._lock() is True
            and self._authorize is not None
            and self._authorize(self.session.binding) is True
        )

    def now_ms(self) -> int:
        return self._adapter.now_ms()

    def persist(self, state: DriverState) -> None:
        if self._lock() is not True:
            raise PermissionError("original_owner_lock_required")
        candidate = replace(self.session, driver=state)
        if candidate.binding_hash != self.session.binding_hash:
            raise ValueError("owner_port_immutable_binding_changed")
        payload = candidate.to_payload()
        self._save_record(
            payload
        )  # Failure propagates before memory/write advancement.
        self.session = candidate

    def guard(self, state, *, quantity, worst_bid, now_ms):
        if worst_bid is not None:
            self._quote_required = True
        quote = self._write_quote
        return (
            not self._receipt_only
            and state == self.session.driver.orders
            and self._authorized()
            and type(quantity) is int
            and 0 < quantity <= state.open_qty
            and (worst_bid is None or finite(worst_bid) and worst_bid > 0)
            and (
                not self._quote_required
                or (
                    isinstance(quote, Snapshot)
                    and quote.scope_key == self.session.policy.scope_key
                    and quote.position_epoch == state.position_epoch
                    and 0
                    <= now_ms - quote.quote_at_ms
                    <= self.session.policy.max_quote_age_ms
                )
            )
            and self._owner_guard(
                self.session.binding,
                state=state,
                quantity=quantity,
                worst_bid=worst_bid,
                now_ms=now_ms,
            )
            is True
        )

    def _transport_guard(self, request: SellWrite):
        s = self.session.driver.orders
        cancel = request.action == "CANCEL"
        expected = s.target if s.phase == "CANCEL_PENDING" else s.exit_order
        if not cancel:
            expected = s.exit_order or s.target
        return (
            request.action in ("NEW", "CANCEL")
            and request.policy_hash == s.policy_hash
            and request.predecessor == expected
            and (
                cancel
                and s.phase in ("CANCEL_PENDING", "EXIT_CANCEL_PENDING")
                or not cancel
                and s.phase == "EXIT_SUBMITTING"
            )
            and request.quantity
            == (s.open_qty if s.phase == "CANCEL_PENDING" else s.exit_reserved_qty)
            and self.guard(
                s,
                quantity=request.quantity,
                worst_bid=request.limit_price,
                now_ms=self._adapter.now_ms(),
            )
        )

    def _proof(self, snapshot):
        if not isinstance(snapshot, SellSnapshot) or not snapshot.source_ok:
            if isinstance(snapshot, SellSnapshot):
                self._source_gap = snapshot.error
            return None
        s = self.session.driver.orders
        return BrokerProof(
            snapshot.order,
            s.owner_id,
            s.episode_id,
            s.lot_id,
            snapshot.filled_qty,
            snapshot.terminal,
            snapshot.receipt_hash,
            snapshot.observed_at_ms,
            True,
        )

    def reconcile(self, order, *, state):
        if (
            self._lock() is not True
            or state != self.session.driver.orders
            or order not in (state.target, state.exit_order)
        ):
            raise ValueError("owner_port_reconcile_identity_mismatch")
        snapshot = self._adapter.reconcile_owned_sell(order)
        if snapshot.source_ok and snapshot.terminal:
            from .terminal import confirmed_cancel_proof

            context = replace(
                self.session.context, client_intent_id=self._cancel_client_id(order)
            )
            child = self._adapter.registry.intent_for_client(context=context)
            if child is not None:
                try:
                    confirmed_cancel_proof(
                        session=self.session, adapter=self._adapter, order=order
                    )
                except ValueError:
                    if child.get("state") not in {
                        "ORDER_BOUND",
                        "ORDER_TERMINAL",
                    } or not child.get("broker_order_no"):
                        self._source_gap = "cancel_child_intent_unresolved"
                        return None
                    snapshot = self._adapter.reconcile_terminal_cancel(
                        order,
                        OrderKey(child["order_date"], child["broker_order_no"]),
                        max_snapshot_age_ms=self.session.policy.max_quote_age_ms,
                    )
                    if snapshot.source_ok:
                        confirmed_cancel_proof(
                            session=self.session, adapter=self._adapter, order=order
                        )
        return self._proof(snapshot)

    def recover_submission(self, *, state):
        if (
            self._lock() is not True
            or state != self.session.driver.orders
            or state.phase != "EXIT_SUBMITTING"
        ):
            raise ValueError("owner_port_recovery_identity_mismatch")
        return self._proof(
            self._adapter.recover_replacement(
                state.exit_order or state.target,
                quantity=state.exit_reserved_qty,
            )
        )

    def cancel_owned_sell(self, order, *, quantity, state):
        if state != self.session.driver.orders or not self._authorized():
            raise PermissionError("durable_authorized_owner_state_required")
        self._adapter.cancel_owned_sell(
            order,
            quantity=quantity,
            action_id=self._cancel_client_id(order),
        )

    def _cancel_client_id(self, order):
        from .terminal import owner_cancel_client_id

        return owner_cancel_client_id(self.session.binding_hash, order)

    def resume_unreserved_cancel(self, order, *, state):
        """Only a missing durable broker reservation proves no dispatch here.

        ACK, reject, ambiguous or reserved rows never allow a retry. Original
        owner lock spans the read and possible reservation; restart uses the
        same deterministic client intent. Require a fresh quote for recovery.
        """
        if state != self.session.driver.orders or self._lock() is not True:
            raise PermissionError("durable_locked_owner_state_required")
        context = replace(
            self.session.context, client_intent_id=self._cancel_client_id(order)
        )
        if self._adapter.registry.intent_for_client(context=context) is not None:
            return
        self._quote_required = True
        quantity = (
            state.open_qty
            if state.phase == "CANCEL_PENDING"
            else state.exit_reserved_qty
        )
        if self.guard(state, quantity=quantity, worst_bid=None, now_ms=self.now_ms()):
            self.cancel_owned_sell(order, quantity=quantity, state=state)

    def submit_owned_sell(self, *, quantity, limit_price, state):
        if state != self.session.driver.orders or not self._authorized():
            raise PermissionError("durable_authorized_owner_state_required")
        if not finite(limit_price) or limit_price != int(limit_price):
            raise ValueError("integer_executable_limit_required_no_rounding")
        ack = self._adapter.submit_owned_sell(
            state.exit_order or state.target,
            quantity=quantity,
            limit_price=int(limit_price),
            action_id=f"{state.intent_id}:{state.exit_attempts}",
        )
        if not ack.accepted:
            return None
        return SubmitReceipt(
            ack.order,
            state.owner_id,
            state.episode_id,
            state.lot_id,
            quantity,
            ack.receipt_hash,
            True,
        )

    def step(
        self,
        *,
        snapshot: Snapshot | None,
        clock: Clock,
        final_exit_requested: bool = False,
    ) -> OwnerSession:
        """One bounded pass; callers never need an extra market/API polling loop."""
        if self._lock() is not True:
            raise PermissionError("original_owner_lock_required")
        self._write_quote, self._quote_required, self._source_gap = snapshot, False, ""
        self._receipt_only = True
        if type(final_exit_requested) is not bool:
            raise ValueError("final_exit_authority_invalid")
        if (
            not isinstance(clock, Clock)
            or type(clock.now_ms) is not int
            or clock.now_ms < self.session.position.first_fill_at_ms
            or (
                clock.verified_halt_ms is not None
                and (
                    type(clock.verified_halt_ms) is not int
                    or not 0
                    <= clock.verified_halt_ms
                    <= clock.now_ms - self.session.position.first_fill_at_ms
                )
            )
        ):
            raise ValueError("valid_owner_clock_required")
        self._receipt_only = clock.verified_halt_ms is None
        if not self._authorized():
            self.persist(
                replace(
                    self.session.driver, alert_reason="frozen_policy_authority_missing"
                )
            )
            return self.session
        s = self.session.driver.orders
        if s.phase == "FLAT":
            return self.session
        if self.session.driver.decision.open_qty != s.open_qty and s.open_qty > 0:
            # Derived only from exact cumulative fills, not quote/sample count.
            epoch = canonical_sha256(
                {
                    "binding": self.session.binding_hash,
                    "target_fill": s.target_filled_qty,
                    "exit_fill": s.exit_filled_qty,
                }
            )
            self.persist(
                rebind_remaining_quantity(
                    self.session.driver,
                    position=replace(
                        self.session.remaining_position, position_epoch=epoch
                    ),
                )
            )
        s = self.session.driver.orders
        if s.phase == "TARGET_WORKING":
            proof = self.reconcile(s.target, state=s)
            if (
                proof is None
                or not 0
                <= self.now_ms() - proof.observed_at_ms
                <= self.session.policy.max_quote_age_ms
            ):
                self.persist(
                    replace(
                        self.session.driver,
                        alert_reason=(
                            "broker_source_gap:" + self._source_gap
                            if self._source_gap
                            else "target_reconciliation_pending"
                        ),
                    )
                )
                return self.session
            if proof.cumulative_filled != s.target_filled_qty:
                updated = reduce_event(
                    s,
                    ExitEvent(
                        f"target:{proof.receipt_hash}",
                        "TARGET_FILL",
                        s.owner_id,
                        s.episode_id,
                        s.lot_id,
                        s.policy_hash,
                        s.position_epoch,
                        s.intent_id or "target-reconcile",
                        s.target,
                        cumulative_fill=proof.cumulative_filled,
                        receipt_hash=proof.receipt_hash,
                    ),
                )
                self.persist(replace(self.session.driver, orders=updated))
                return self.session  # Owner rebinds quantity before next quote.
            if proof.terminal:
                self.persist(
                    replace(
                        self.session.driver,
                        alert_reason="unexpected_target_terminal_owner_recovery_required",
                    )
                )
                return self.session
        try:
            current = advance_exit(
                self.session.driver,
                policy=self.session.policy,
                position=self.session.remaining_position,
                snapshot=snapshot,
                clock=clock,
                bounds=self.session.bounds,
                port=self,
                active_policy_authorized=True,
                final_exit_requested=final_exit_requested,
            )
        except (PermissionError, ValueError, OwnerRegistryError):
            # Preserve the last durable phase, not the pre-call local state.
            # Disk failures propagate; no error can synthesize a terminal fill.
            current = replace(
                self.session.driver,
                alert_reason="owner_exit_contract_requires_reconciliation",
            )
        if self._source_gap and current.alert_reason:
            current = replace(
                current, alert_reason="broker_source_gap:" + self._source_gap
            )
        if current != self.session.driver:
            self.persist(current)
        return self.session
