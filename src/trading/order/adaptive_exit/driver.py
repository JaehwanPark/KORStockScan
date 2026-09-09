"""Owner-locked exit execution driver with durable-before-effect transitions.

Ports must be implemented by the original widget/episode custody owner. This
module owns no account, thread, filesystem lock, policy activation or broker
API. Persist failures propagate BEFORE writes; ambiguous submissions are never
blindly retried. The port's guard must include account/manual/global vetoes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from .decision import evaluate_exit, _tick_ceiling
from .models import Clock, DecisionState, ExitPolicy, Position, Snapshot, positive_int
from .reducer import ExitState, ExitEvent, OrderKey, reduce_event


@dataclass(frozen=True)
class ExecutionBounds:
    sell_ttl_ms: int
    maximum_sell_attempts: int
    maximum_unprotected_ms: int
    vanished_arm: str
    final_residual: str

    def __post_init__(self):
        if (
            any(
                not positive_int(v)
                for v in (
                    self.sell_ttl_ms,
                    self.maximum_sell_attempts,
                    self.maximum_unprotected_ms,
                )
            )
            or self.maximum_sell_attempts > 3
            or self.vanished_arm != "exit_with_fresh_guard"
            or self.final_residual != "retain_manager_and_alert"
        ):
            raise ValueError("explicit_supported_execution_bounds_required")


@dataclass(frozen=True)
class BrokerProof:
    order: OrderKey
    owner_id: str
    episode_id: str
    lot_id: str
    cumulative_filled: int
    terminal: bool
    receipt_hash: str
    observed_at_ms: int
    # Complete dated execution/current-unfilled/successor reconciliation.
    reconciliation_complete: bool


@dataclass(frozen=True)
class SubmitReceipt:
    order: OrderKey
    owner_id: str
    episode_id: str
    lot_id: str
    quantity: int
    receipt_hash: str
    accepted: bool


@dataclass(frozen=True)
class DriverState:
    orders: ExitState
    decision: DecisionState
    submitted_at_ms: int | None = None
    unprotected_since_ms: int | None = None
    alert_reason: str | None = None


def rebind_remaining_quantity(
    driver: DriverState, *, position: Position
) -> DriverState:
    """Owner-only rebind after exact reducer fill reconciliation, before a quote.

    Quantity may only decrease. The owner issues a new epoch in its normalized
    position and persists this result. Keep the first-fill clock, extension and
    stop; discard only the old-quantity quote identity/high-water observation.
    """
    old = driver.decision
    s = driver.orders
    if (
        s.phase
        not in (
            "TARGET_WORKING",
            "INTENT_PERSISTED",
            "CANCEL_PENDING",
            "RESIDUAL_READY",
            "TRAIL_ACTIVE",
            "EXIT_WORKING",
            "EXIT_CANCEL_PENDING",
        )
        or (position.owner_id, position.episode_id, position.lot_id)
        != (s.owner_id, s.episode_id, s.lot_id)
        or position.first_fill_at_ms != old.first_fill_at_ms
        or not positive_int(position.open_qty)
        or position.open_qty != s.open_qty
        or position.open_qty >= old.open_qty
        or not position.position_epoch
        or position.position_epoch == s.position_epoch
    ):
        raise ValueError("exact_decreasing_quantity_epoch_rebind_required")
    return replace(
        driver,
        orders=replace(s, position_epoch=position.position_epoch),
        decision=replace(
            old,
            position_epoch=position.position_epoch,
            open_qty=position.open_qty,
            last_observed_at_ms=None,
            source_epoch=None,
            sequence=None,
        ),
    )


class OwnerExitPort(Protocol):
    def now_ms(self) -> int: ...
    def persist(self, state: DriverState) -> None: ...
    def guard(
        self, state: ExitState, *, quantity: int, worst_bid: float | None, now_ms: int
    ) -> bool: ...
    def reconcile(self, order: OrderKey, *, state: ExitState) -> BrokerProof | None: ...
    def recover_submission(self, *, state: ExitState) -> BrokerProof | None: ...
    def cancel_owned_sell(
        self, order: OrderKey, *, quantity: int, state: ExitState
    ) -> None: ...
    def submit_owned_sell(
        self, *, quantity: int, limit_price: float, state: ExitState
    ) -> SubmitReceipt | None: ...


def advance_exit(
    driver: DriverState,
    *,
    policy: ExitPolicy,
    position: Position,
    snapshot: Snapshot | None,
    clock: Clock,
    bounds: ExecutionBounds,
    port: OwnerExitPort,
    active_policy_authorized: bool,
    final_exit_requested: bool = False,
) -> DriverState:
    """Caller holds the existing owner lock across reconciliation and writes.

    Authorization is a previously frozen validated episode binding, NOT today's
    enable flag. Expiry stops new selection, not an already unprotected manager.
    """
    current = driver
    # Validate before a port can issue even a reconciliation request. Reducer
    # validation is pure; discard its recovery result rather than mutate state.
    try:
        s = driver.orders
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
        if s.phase in ("EXIT_WORKING", "EXIT_CANCEL_PENDING") and not isinstance(
            s.exit_order, OrderKey
        ):
            raise ValueError("exit_order_missing")
    except (TypeError, ValueError, AttributeError):
        return replace(driver, alert_reason="persisted_order_state_invalid")
    if active_policy_authorized is not True:
        return replace(driver, alert_reason="frozen_policy_authority_missing")
    if type(final_exit_requested) is not bool:
        return replace(driver, alert_reason="final_exit_authority_invalid")
    if (
        driver.orders.owner_id != position.owner_id
        or driver.orders.episode_id != position.episode_id
        or driver.orders.lot_id != position.lot_id
        or driver.orders.policy_hash != policy.policy_hash
        or driver.orders.position_epoch != position.position_epoch
        or driver.orders.open_qty != position.open_qty
        or driver.decision.policy_hash != policy.policy_hash
        or driver.decision.first_fill_at_ms != position.first_fill_at_ms
    ):
        return replace(driver, alert_reason="owner_position_binding_mismatch")
    if (
        type(clock.now_ms) is not int
        or clock.now_ms < position.first_fill_at_ms
        or type(clock.verified_halt_ms) is not int
        or clock.verified_halt_ms < 0
    ):
        return replace(driver, alert_reason="invalid_clock")

    def save(new):
        nonlocal current
        port.persist(new)
        current = new

    def observed_now():
        # A real broker read finishes AFTER the loop's input snapshot clock.
        # Compare the proof to the trusted owner clock after I/O, not that
        # earlier timestamp (which would reject every nonzero-latency read).
        reader = getattr(port, "now_ms", None)
        value = reader() if callable(reader) else clock.now_ms
        if type(value) is not int or value < clock.now_ms:
            raise ValueError("owner_clock_regressed_during_exit_step")
        return value

    def alert(reason):
        save(replace(current, alert_reason=reason))
        return current

    def event(kind, *, order=None, proof=None, decision_state=None, **extra):
        s = current.orders
        payload = dict(
            event_id=f"{s.intent_id or s.episode_id}:{kind}:{clock.now_ms}:{s.exit_attempts}",
            kind=kind,
            owner_id=s.owner_id,
            episode_id=s.episode_id,
            lot_id=s.lot_id,
            policy_hash=s.policy_hash,
            position_epoch=s.position_epoch,
            intent_id=s.intent_id or f"{s.episode_id}:{s.lot_id}:{s.policy_hash}",
            order=order or s.target,
        )
        if proof:
            payload.update(
                cumulative_fill=proof.cumulative_filled,
                exact_terminal_reconciled=proof.terminal,
                receipt_hash=proof.receipt_hash,
            )
        payload.update(extra)
        save(
            replace(
                current,
                orders=reduce_event(s, ExitEvent(**payload)),
                decision=decision_state or current.decision,
            )
        )

    def valid(proof, order):
        s = current.orders
        return (
            isinstance(proof, BrokerProof)
            and proof.order == order
            and proof.owner_id == s.owner_id
            and proof.episode_id == s.episode_id
            and proof.lot_id == s.lot_id
            and type(proof.cumulative_filled) is int
            and proof.cumulative_filled >= 0
            and type(proof.terminal) is bool
            and proof.reconciliation_complete is True
            and isinstance(proof.receipt_hash, str)
            and bool(proof.receipt_hash)
            and type(proof.observed_at_ms) is int
            and 0 <= observed_now() - proof.observed_at_ms <= policy.max_quote_age_ms
        )

    phase = current.orders.phase
    if phase in ("FLAT", "RECOVERY_REQUIRED"):
        return current
    if (
        current.unprotected_since_ms is not None
        and clock.now_ms - current.unprotected_since_ms >= bounds.maximum_unprotected_ms
    ):
        save(replace(current, alert_reason="unprotected_deadline_manager_must_remain"))
    if phase == "INTENT_PERSISTED":
        # CANCEL_PENDING is always persisted BEFORE the API. An earlier intent
        # alone is safe to continue only after a fresh exact target proof.
        proof = port.reconcile(current.orders.target, state=current.orders)
        if not valid(proof, current.orders.target):
            return alert("intent_target_requires_reconciliation")
        if proof.cumulative_filled:
            event("TARGET_FILL", proof=proof)
            if current.orders.phase == "FLAT":
                return current
        if proof.terminal:
            # Recovery may find that the target finished between durable intent
            # and cancel dispatch. Exact terminal proof, not an ACK, releases it.
            event("CANCEL_REQUESTED")
            event("CANCEL_CONFIRMED", proof=proof)
            save(replace(current, unprotected_since_ms=clock.now_ms))
            return current
        if (
            port.guard(
                current.orders,
                quantity=current.orders.open_qty,
                worst_bid=None,
                now_ms=clock.now_ms,
            )
            is not True
        ):
            return alert("cancel_owner_guard_blocked")
        event("CANCEL_REQUESTED")
        port.cancel_owned_sell(
            current.orders.target,
            quantity=current.orders.open_qty,
            state=current.orders,
        )
        return current
    if phase == "EXIT_SUBMITTING":
        proof = port.recover_submission(state=current.orders)
        if not isinstance(proof, BrokerProof) or not valid(proof, proof.order):
            return alert("ambiguous_submit_reservation_retained")
        if current.submitted_at_ms is None:
            return alert("recovered_submit_clock_missing_owner_recovery_required")
        event("EXIT_SUBMITTED", order=proof.order, receipt_hash=proof.receipt_hash)
        save(replace(current, unprotected_since_ms=None))
        # Observe the recovered order on the next cycle, never submit again.
        return current
    if phase in ("CANCEL_PENDING", "EXIT_WORKING", "EXIT_CANCEL_PENDING"):
        order = (
            current.orders.target
            if phase == "CANCEL_PENDING"
            else current.orders.exit_order
        )
        proof = port.reconcile(order, state=current.orders)
        if not valid(proof, order):
            return alert("exact_broker_reconciliation_pending")
        if proof.terminal:
            event(
                "CANCEL_CONFIRMED" if phase == "CANCEL_PENDING" else "EXIT_TERMINAL",
                order=order,
                proof=proof,
            )
            if current.orders.phase == "FLAT":
                return current
            save(replace(current, unprotected_since_ms=clock.now_ms))
            # Re-evaluate a partial-fill quantity with a new normalized position
            # supplied by its owner on the next cycle. Never synthesize an epoch.
            return current
        if proof.cumulative_filled:
            event(
                "TARGET_FILL" if phase == "CANCEL_PENDING" else "EXIT_FILL",
                order=order,
                proof=proof,
            )
        if current.orders.phase == "FLAT":
            return current
        if phase in ("CANCEL_PENDING", "EXIT_CANCEL_PENDING"):
            resume = getattr(port, "resume_unreserved_cancel", None)
            if callable(resume):
                resume(order, state=current.orders)
        if (
            phase == "EXIT_WORKING"
            and current.submitted_at_ms is not None
            and clock.now_ms - current.submitted_at_ms >= bounds.sell_ttl_ms
        ):
            if (
                port.guard(
                    current.orders,
                    quantity=current.orders.exit_reserved_qty,
                    worst_bid=None,
                    now_ms=clock.now_ms,
                )
                is not True
            ):
                return alert("cancel_owner_guard_blocked")
            event("EXIT_CANCEL_REQUESTED", order=order)
            port.cancel_owned_sell(
                order, quantity=current.orders.exit_reserved_qty, state=current.orders
            )
        return current

    if not isinstance(snapshot, Snapshot):
        return alert("fresh_executable_snapshot_required")
    clock = replace(clock, now_ms=observed_now())
    decision = evaluate_exit(
        policy,
        position,
        snapshot,
        clock,
        current.decision,
        final_exit_requested=final_exit_requested,
    )
    if decision.action in ("SOURCE_GAP", "RECOVERY_REQUIRED"):
        return alert(decision.reason)
    state = replace(
        current.decision,
        last_observed_at_ms=snapshot.observed_at_ms,
        sequence=snapshot.sequence,
        source_epoch=snapshot.source_epoch,
    )
    if decision.action == "GRANT_EXTENSION":
        state = replace(
            state,
            extensions=1,
            extension_until_active_ms=decision.next_active_deadline_ms,
            extension_granted_at_active_ms=clock.now_ms
            - position.first_fill_at_ms
            - clock.verified_halt_ms,
        )
    deadline_alert = (
        "unprotected_deadline_manager_must_remain"
        if current.unprotected_since_ms is not None
        and clock.now_ms - current.unprotected_since_ms >= bounds.maximum_unprotected_ms
        else None
    )
    save(replace(current, decision=state, alert_reason=deadline_alert))
    if phase == "TARGET_WORKING" and decision.action.startswith("REQUEST_"):
        if (
            port.guard(
                current.orders,
                quantity=current.orders.open_qty,
                worst_bid=decision.worst_bid,
                now_ms=clock.now_ms,
            )
            is not True
        ):
            return alert("owner_guard_blocked")
        event(
            "EXIT_INTENT",
            intent_kind=(
                "trail_arm" if decision.action == "REQUEST_TRAIL_ARM" else "early_exit"
            ),
        )
        event("CANCEL_REQUESTED")
        port.cancel_owned_sell(
            current.orders.target,
            quantity=current.orders.open_qty,
            state=current.orders,
        )
        return current
    if (
        phase == "RESIDUAL_READY"
        and current.orders.intent_kind == "trail_arm"
        and decision.action == "REQUEST_TRAIL_ARM"
    ):
        floor_price = position.entry_price * (1 + position.round_trip_cost_pct / 100)
        stop = _tick_ceiling(
            max(
                floor_price,
                decision.executable_bid - policy.trail.gap_ticks * position.tick_size,
            ),
            position.tick_size,
        )
        if stop < decision.executable_bid:
            event(
                "TRAIL_ARMED",
                high_water=decision.executable_bid,
                stop_price=stop,
                receipt_hash=snapshot.source_hash,
                decision_state=replace(
                    current.decision,
                    trail_active=True,
                    high_water=decision.executable_bid,
                    stop_price=stop,
                ),
            )
            return current
    if phase == "TRAIL_ACTIVE" and decision.action == "KEEP_TRAIL":
        event(
            "TRAIL_UPDATED",
            high_water=decision.high_water,
            stop_price=decision.stop_price,
            receipt_hash=snapshot.source_hash,
            decision_state=replace(
                current.decision,
                high_water=decision.high_water,
                stop_price=decision.stop_price,
            ),
        )
        return current
    if (
        phase == "RESIDUAL_READY"
        or phase == "TRAIL_ACTIVE"
        and decision.action in ("REQUEST_TRAIL_EXIT", "REQUEST_EARLY_EXIT")
    ):
        if current.orders.exit_attempts >= bounds.maximum_sell_attempts:
            return alert("attempts_exhausted_manager_must_remain")
        if (
            port.guard(
                current.orders,
                quantity=current.orders.open_qty,
                worst_bid=decision.worst_bid,
                now_ms=clock.now_ms,
            )
            is not True
        ):
            return alert("sell_owner_guard_blocked")
        event("EXIT_SUBMIT_INTENT", quantity=current.orders.open_qty)
        save(replace(current, submitted_at_ms=observed_now()))
        receipt = port.submit_owned_sell(
            quantity=current.orders.exit_reserved_qty,
            limit_price=decision.worst_bid,
            state=current.orders,
        )
        if (
            isinstance(receipt, SubmitReceipt)
            and isinstance(receipt.order, OrderKey)
            and receipt.accepted is True
            and (receipt.owner_id, receipt.episode_id, receipt.lot_id)
            == (
                current.orders.owner_id,
                current.orders.episode_id,
                current.orders.lot_id,
            )
            and type(receipt.quantity) is int
            and receipt.quantity == current.orders.exit_reserved_qty
            and isinstance(receipt.receipt_hash, str)
            and receipt.receipt_hash
        ):
            event(
                "EXIT_SUBMITTED",
                order=receipt.order,
                receipt_hash=receipt.receipt_hash,
            )
            save(replace(current, unprotected_since_ms=None))
        return current
    return current
