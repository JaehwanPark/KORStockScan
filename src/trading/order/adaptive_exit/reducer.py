"""Durable-intent state reducer, not a broker adapter.

The owner must persist returned state under its existing custody lock BEFORE
performing any side effect. A crash in a pre-submit state is ambiguous; replaying
that state does not grant permission to resubmit. ACKs never prove terminality.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from datetime import date

from .models import finite, positive_int


@dataclass(frozen=True)
class OrderKey:
    trading_date: str
    order_no: str

    def __post_init__(self) -> None:
        if date.fromisoformat(self.trading_date).isoformat() != self.trading_date:
            raise ValueError("invalid_order_date")
        if not isinstance(self.order_no, str) or not self.order_no.strip():
            raise ValueError("invalid_order_number")


@dataclass(frozen=True)
class ExitState:
    owner_id: str
    episode_id: str
    lot_id: str
    policy_hash: str
    position_epoch: str
    target: OrderKey
    buy_filled_qty: int
    phase: str = "TARGET_WORKING"
    target_filled_qty: int = 0
    exit_filled_qty: int = 0
    exit_reserved_qty: int = 0
    target_terminal: bool = False
    intent_id: str | None = None
    intent_kind: str | None = None
    exit_order: OrderKey | None = None
    high_water: float | None = None
    stop_price: float | None = None
    recovery_reason: str | None = None
    journal: tuple[tuple[str, str], ...] = ()

    @property
    def open_qty(self) -> int:
        return self.buy_filled_qty - self.target_filled_qty - self.exit_filled_qty

    @property
    def reserved_qty(self) -> int:
        target = (
            0 if self.target_terminal else self.buy_filled_qty - self.target_filled_qty
        )
        return target + self.exit_reserved_qty


@dataclass(frozen=True)
class ExitEvent:
    event_id: str
    kind: str
    owner_id: str
    episode_id: str
    lot_id: str
    policy_hash: str
    position_epoch: str
    intent_id: str
    order: OrderKey
    quantity: int = 0
    cumulative_fill: int = 0
    # This is supplied only by an exact owner/order current-unfilled + fill
    # reconciliation adapter. It must NEVER be set from an API cancel ACK.
    exact_terminal_reconciled: bool = False
    receipt_hash: str = ""
    pending_buy: bool = False
    other_reserved_sell_qty: int = 0
    intent_kind: str = "early_exit"
    high_water: float | None = None
    stop_price: float | None = None


def reduce_event(state: ExitState, event: ExitEvent) -> ExitState:
    """Fail closed on malformed transitions; exact duplicate events are no-ops."""
    s, e = state, event
    phases = {
        "TARGET_WORKING",
        "INTENT_PERSISTED",
        "CANCEL_PENDING",
        "RESIDUAL_READY",
        "TRAIL_ACTIVE",
        "EXIT_SUBMITTING",
        "EXIT_WORKING",
        "FLAT",
        "RECOVERY_REQUIRED",
    }
    if (
        s.phase not in phases
        or type(s.target_terminal) is not bool
        or (
            not isinstance(s.target, OrderKey)
            or not isinstance(e.order, OrderKey)
            or s.exit_order is not None
            and not isinstance(s.exit_order, OrderKey)
        )
    ):
        raise ValueError("invalid_persisted_state_contract")
    if s.phase not in ("TARGET_WORKING", "FLAT", "RECOVERY_REQUIRED") and (
        not isinstance(s.intent_id, str)
        or not s.intent_id
        or s.intent_kind not in ("early_exit", "trail_arm")
    ):
        raise ValueError("active_state_missing_durable_intent")
    if not all(
        isinstance(v, str) and v
        for v in (
            e.event_id,
            e.intent_id,
            s.owner_id,
            s.episode_id,
            s.lot_id,
            s.policy_hash,
            s.position_epoch,
        )
    ):
        raise ValueError("missing_event_or_state_identity")
    if (
        not positive_int(s.buy_filled_qty)
        or not all(
            type(v) is int and v >= 0
            for v in (
                s.target_filled_qty,
                s.exit_filled_qty,
                s.exit_reserved_qty,
                e.quantity,
                e.cumulative_fill,
                e.other_reserved_sell_qty,
            )
        )
        or s.open_qty < 0
        or s.reserved_qty > s.open_qty
    ):
        raise ValueError("invalid_owned_quantity_or_reservation")
    if type(e.pending_buy) is not bool or type(e.exact_terminal_reconciled) is not bool:
        raise ValueError("invalid_receipt_boolean")
    if not isinstance(e.receipt_hash, str):
        raise ValueError("invalid_receipt_hash")
    if any(
        getattr(s, key) != getattr(e, key)
        for key in ("owner_id", "episode_id", "lot_id", "policy_hash", "position_epoch")
    ):
        raise ValueError("owner_or_policy_identity_mismatch")
    fingerprint = hashlib.sha256(
        json.dumps(
            asdict(e), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()
    seen = dict(s.journal)
    if e.event_id in seen:
        if seen[e.event_id] != fingerprint:
            raise ValueError("event_id_payload_conflict")
        return s
    if s.intent_id is not None and s.intent_id != e.intent_id:
        raise ValueError("active_intent_conflict")

    def require(*phases: str) -> None:
        if s.phase not in phases:
            raise ValueError("invalid_transition:" + s.phase + ":" + e.kind)

    def target_order() -> None:
        if e.order != s.target:
            raise ValueError("dated_target_order_mismatch")

    def terminal_evidence() -> None:
        if not e.exact_terminal_reconciled or not e.receipt_hash:
            raise ValueError("exact_terminal_evidence_required_not_ack")

    new = s
    if e.kind == "EXIT_INTENT":
        require("TARGET_WORKING")
        target_order()
        if e.intent_kind not in ("early_exit", "trail_arm") or e.pending_buy:
            raise ValueError("unsupported_intent_or_pending_buy")
        if e.other_reserved_sell_qty or s.open_qty <= 0:
            raise ValueError("owner_reservation_conflict")
        new = replace(
            s,
            phase="INTENT_PERSISTED",
            intent_id=e.intent_id,
            intent_kind=e.intent_kind,
        )
    elif e.kind == "CANCEL_REQUESTED":
        require("INTENT_PERSISTED")
        target_order()
        new = replace(s, phase="CANCEL_PENDING")
    elif e.kind == "CANCEL_CONFIRMED":
        require("CANCEL_PENDING")
        target_order()
        terminal_evidence()
        if (
            e.cumulative_fill < s.target_filled_qty
            or e.cumulative_fill > s.buy_filled_qty
        ):
            raise ValueError("target_fill_regression_or_overfill")
        new = replace(s, target_filled_qty=e.cumulative_fill, target_terminal=True)
        new = replace(new, phase="FLAT" if new.open_qty == 0 else "RESIDUAL_READY")
    elif e.kind == "TARGET_FILL":
        target_order()
        if (
            not e.receipt_hash
            or not s.target_filled_qty <= e.cumulative_fill <= s.buy_filled_qty
        ):
            raise ValueError("target_fill_receipt_invalid")
        new = replace(s, target_filled_qty=e.cumulative_fill)
        if new.open_qty < 0 or new.reserved_qty > new.open_qty:
            raise ValueError("late_fill_requires_owner_reconciliation")
        if new.open_qty == 0:
            new = replace(new, phase="FLAT", target_terminal=True)
    elif e.kind == "TRAIL_ARMED":
        require("RESIDUAL_READY")
        target_order()
        if s.intent_kind != "trail_arm" or not s.target_terminal:
            raise ValueError("trail_requires_confirmed_target_cancel")
        if (
            not e.receipt_hash
            or not all(finite(v) and v > 0 for v in (e.high_water, e.stop_price))
            or e.stop_price >= e.high_water
        ):
            raise ValueError("fresh_trail_arm_evidence_required")
        new = replace(
            s, phase="TRAIL_ACTIVE", high_water=e.high_water, stop_price=e.stop_price
        )
    elif e.kind == "TRAIL_UPDATED":
        require("TRAIL_ACTIVE")
        target_order()
        if (
            not e.receipt_hash
            or not all(finite(v) for v in (e.high_water, e.stop_price))
            or (
                e.high_water < s.high_water
                or e.stop_price < s.stop_price
                or e.stop_price >= e.high_water
            )
        ):
            raise ValueError("trail_must_be_monotonic")
        new = replace(s, high_water=e.high_water, stop_price=e.stop_price)
    elif e.kind == "EXIT_SUBMIT_INTENT":
        require("RESIDUAL_READY", "TRAIL_ACTIVE")
        target_order()
        if (
            not s.target_terminal
            or e.pending_buy
            or e.other_reserved_sell_qty
            or (
                not positive_int(e.quantity) or e.quantity > s.open_qty - s.reserved_qty
            )
        ):
            raise ValueError("sell_reservation_conflict")
        new = replace(s, phase="EXIT_SUBMITTING", exit_reserved_qty=e.quantity)
    elif e.kind == "EXIT_SUBMITTED":
        require("EXIT_SUBMITTING")
        if e.order == s.target or not e.receipt_hash:
            raise ValueError("new_sell_receipt_required")
        new = replace(s, phase="EXIT_WORKING", exit_order=e.order)
    elif e.kind == "EXIT_FILL":
        require("EXIT_WORKING")
        if (
            e.order != s.exit_order
            or not e.receipt_hash
            or (
                not s.exit_filled_qty
                <= e.cumulative_fill
                <= s.exit_filled_qty + s.exit_reserved_qty
            )
        ):
            raise ValueError("exact_exit_fill_receipt_required")
        delta = e.cumulative_fill - s.exit_filled_qty
        new = replace(
            s,
            exit_filled_qty=e.cumulative_fill,
            exit_reserved_qty=s.exit_reserved_qty - delta,
        )
        if new.open_qty == 0:
            new = replace(new, phase="FLAT")
        elif new.exit_reserved_qty == 0:
            # No generic automatic second sell. A bounded adapter must reconcile.
            new = replace(
                new, phase="RECOVERY_REQUIRED", recovery_reason="residual_after_exit"
            )
    elif e.kind == "RECOVERY_REQUIRED":
        new = replace(
            s, phase="RECOVERY_REQUIRED", recovery_reason="ambiguous_broker_state"
        )
    else:
        raise ValueError("unsupported_event")
    return replace(new, journal=s.journal + ((e.event_id, fingerprint),))
