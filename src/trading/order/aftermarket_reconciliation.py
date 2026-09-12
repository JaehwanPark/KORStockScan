"""Pure order reconciliation for the 15:30 aftermarket boundary.

This module deliberately has no broker adapter or persistence dependency.  Its
inputs are durable intent bindings and already-normalized, read-only Kiwoom
order evidence.  In particular, SOR parent/child relationships are never
inferred from an order number or an upstream response field.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


SCHEMA = "aftermarket_close_reconciliation_v1"
_DATED_API = "kt00007"
_CURRENT_API = "ka10075"
_CHILD_ROUTES = frozenset({"KRX", "NXT"})
_PARENT_ROUTES = frozenset({"KRX", "NXT", "SOR"})
_EVIDENCE_STATES = frozenset({"OPEN", "TERMINAL", "ACK", "REJECTED", "UNKNOWN"})


class ReconciliationState(str, Enum):
    OPEN = "OPEN"
    TERMINAL = "TERMINAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ChildOrderBinding:
    """Explicit durable binding for one executable venue child.

    ``original_order_no`` preserves the route-local lineage used by cancel or
    modify operations.  ``cancel_order_no`` is required when a confirmed
    cancelled quantity is reported.
    """

    broker_order_no: str
    original_order_no: str
    route: str
    requested_qty: int
    cancel_order_no: str = ""


@dataclass(frozen=True)
class DurableParentIntent:
    intent_id: str
    account_key: str
    order_date: str
    symbol: str
    side: str
    requested_route: str
    requested_qty: int
    parent_order_no: str
    intent_sha256: str
    children: tuple[ChildOrderBinding, ...]


@dataclass(frozen=True)
class OrderEvidence:
    """Normalized exact-order evidence from a read-only Kiwoom query."""

    source_api: str
    account_key: str
    symbol: str
    side: str
    broker_order_no: str
    original_order_no: str
    route: str
    requested_qty: int
    filled_qty: int
    confirmed_cancel_qty: int
    remaining_qty: int
    state: str
    receipt_sha256: str
    order_date: str | None = None
    cancel_order_no: str = ""


@dataclass(frozen=True)
class ChildReconciliation:
    broker_order_no: str
    route: str
    state: ReconciliationState
    requested_qty: int
    filled_qty: int | None
    confirmed_cancel_qty: int | None
    broker_remaining_qty: int | None
    released_qty: int
    evidence_sha256s: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class BoundaryReconciliation:
    schema: str
    intent_id: str
    account_key: str
    order_date: str
    symbol: str
    side: str
    requested_route: str
    parent_order_no: str
    intent_sha256: str
    state: ReconciliationState
    terminal: bool
    requested_qty: int
    filled_qty: int | None
    confirmed_cancel_qty: int | None
    broker_remaining_qty: int | None
    releasable_qty: int
    successor_blocked: bool
    children: tuple[ChildReconciliation, ...]
    source_sha256s: tuple[str, ...]
    reasons: tuple[str, ...]


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _unknown_child(binding: ChildOrderBinding, *reasons: str) -> ChildReconciliation:
    return ChildReconciliation(
        broker_order_no=binding.broker_order_no,
        route=binding.route,
        state=ReconciliationState.UNKNOWN,
        requested_qty=binding.requested_qty,
        filled_qty=None,
        confirmed_cancel_qty=None,
        broker_remaining_qty=None,
        released_qty=0,
        evidence_sha256s=(),
        reasons=tuple(sorted(set(reasons))),
    )


def _identity_reasons(
    intent: DurableParentIntent,
    binding: ChildOrderBinding,
    evidence: OrderEvidence,
) -> list[str]:
    reasons: list[str] = []
    if evidence.account_key != intent.account_key:
        reasons.append("account_key_mismatch")
    if evidence.symbol != intent.symbol:
        reasons.append("symbol_mismatch")
    if evidence.side != intent.side:
        reasons.append("side_mismatch")
    if evidence.broker_order_no != binding.broker_order_no:
        reasons.append("broker_order_no_mismatch")
    if evidence.original_order_no != binding.original_order_no:
        reasons.append("original_order_no_mismatch")
    if evidence.route != binding.route:
        reasons.append("route_mismatch")
    if evidence.requested_qty != binding.requested_qty:
        reasons.append("requested_qty_mismatch")
    if evidence.order_date is not None and evidence.order_date != intent.order_date:
        reasons.append("order_date_mismatch")
    if evidence.cancel_order_no != binding.cancel_order_no:
        reasons.append("cancel_order_no_mismatch")
    if not _is_sha256(evidence.receipt_sha256):
        reasons.append("invalid_receipt_sha256")
    return reasons


def _quantity_reasons(evidence: OrderEvidence) -> list[str]:
    quantities = (
        evidence.requested_qty,
        evidence.filled_qty,
        evidence.confirmed_cancel_qty,
        evidence.remaining_qty,
    )
    reasons: list[str] = []
    if any(value < 0 for value in quantities):
        reasons.append("negative_quantity")
    if (
        evidence.requested_qty
        != evidence.filled_qty + evidence.confirmed_cancel_qty + evidence.remaining_qty
    ):
        reasons.append("quantity_conservation_failed")
    if evidence.confirmed_cancel_qty > 0 and not evidence.cancel_order_no:
        reasons.append("confirmed_cancel_without_order_no")
    return reasons


def _reconcile_child(
    intent: DurableParentIntent,
    binding: ChildOrderBinding,
    dated: tuple[OrderEvidence, ...],
    current: tuple[OrderEvidence, ...],
    *,
    current_snapshot_complete: bool,
) -> ChildReconciliation:
    if len(dated) != 1:
        return _unknown_child(
            binding,
            "missing_dated_receipt" if not dated else "duplicate_dated_receipt",
        )
    if len(current) > 1:
        return _unknown_child(binding, "duplicate_current_receipt")

    dated_row = dated[0]
    current_row = current[0] if current else None
    reasons = _identity_reasons(intent, binding, dated_row)
    reasons.extend(_quantity_reasons(dated_row))
    if dated_row.source_api != _DATED_API:
        reasons.append("invalid_dated_source_api")
    if dated_row.order_date != intent.order_date:
        reasons.append("dated_receipt_not_exact_date")
    if dated_row.state not in _EVIDENCE_STATES:
        reasons.append("invalid_dated_state")

    evidence_hashes = [dated_row.receipt_sha256]
    if current_row is not None:
        reasons.extend(_identity_reasons(intent, binding, current_row))
        reasons.extend(_quantity_reasons(current_row))
        if current_row.source_api != _CURRENT_API:
            reasons.append("invalid_current_source_api")
        if current_row.state != "OPEN" or current_row.remaining_qty <= 0:
            reasons.append("current_receipt_not_open")
        if (
            dated_row.filled_qty,
            dated_row.confirmed_cancel_qty,
            dated_row.remaining_qty,
        ) != (
            current_row.filled_qty,
            current_row.confirmed_cancel_qty,
            current_row.remaining_qty,
        ):
            reasons.append("dated_current_quantity_mismatch")
        evidence_hashes.append(current_row.receipt_sha256)

    if reasons:
        return ChildReconciliation(
            broker_order_no=binding.broker_order_no,
            route=binding.route,
            state=ReconciliationState.UNKNOWN,
            requested_qty=binding.requested_qty,
            filled_qty=None,
            confirmed_cancel_qty=None,
            broker_remaining_qty=None,
            released_qty=0,
            evidence_sha256s=tuple(sorted(set(evidence_hashes))),
            reasons=tuple(sorted(set(reasons))),
        )

    if current_row is not None:
        return ChildReconciliation(
            broker_order_no=binding.broker_order_no,
            route=binding.route,
            state=ReconciliationState.OPEN,
            requested_qty=binding.requested_qty,
            filled_qty=current_row.filled_qty,
            confirmed_cancel_qty=current_row.confirmed_cancel_qty,
            broker_remaining_qty=current_row.remaining_qty,
            released_qty=0,
            evidence_sha256s=tuple(sorted(set(evidence_hashes))),
            reasons=("nxt_child_open",) if binding.route == "NXT" else ("child_open",),
        )

    terminal_reasons: list[str] = []
    if not current_snapshot_complete:
        terminal_reasons.append("current_snapshot_incomplete")
    if dated_row.state != "TERMINAL":
        terminal_reasons.append("dated_receipt_not_terminal")
    if dated_row.remaining_qty != 0:
        terminal_reasons.append("terminal_with_remaining_quantity")
    if terminal_reasons:
        return ChildReconciliation(
            broker_order_no=binding.broker_order_no,
            route=binding.route,
            state=ReconciliationState.UNKNOWN,
            requested_qty=binding.requested_qty,
            filled_qty=None,
            confirmed_cancel_qty=None,
            broker_remaining_qty=None,
            released_qty=0,
            evidence_sha256s=tuple(sorted(set(evidence_hashes))),
            reasons=tuple(sorted(set(terminal_reasons))),
        )

    return ChildReconciliation(
        broker_order_no=binding.broker_order_no,
        route=binding.route,
        state=ReconciliationState.TERMINAL,
        requested_qty=binding.requested_qty,
        filled_qty=dated_row.filled_qty,
        confirmed_cancel_qty=dated_row.confirmed_cancel_qty,
        broker_remaining_qty=0,
        released_qty=dated_row.confirmed_cancel_qty,
        evidence_sha256s=tuple(sorted(set(evidence_hashes))),
        reasons=("child_terminal",),
    )


def reconcile_aftermarket_boundary(
    intent: DurableParentIntent,
    dated_evidence: Iterable[OrderEvidence],
    current_open_evidence: Iterable[OrderEvidence],
    *,
    current_snapshot_complete: bool,
    restart: bool = False,
    restart_intent_sha256: str | None = None,
) -> BoundaryReconciliation:
    """Reconcile one parent intent without side effects or broker calls.

    A terminal result requires exact dated evidence for every explicitly bound
    child and a complete current-open snapshot proving that no child remains
    open.  ACK, rejection, an empty incomplete page, or one terminal SOR child
    can therefore never close the parent.
    """

    parent_reasons: list[str] = []
    children = intent.children
    if intent.requested_route not in _PARENT_ROUTES:
        parent_reasons.append("invalid_parent_route")
    if intent.requested_qty <= 0:
        parent_reasons.append("invalid_parent_quantity")
    if not children:
        parent_reasons.append("missing_child_bindings")
    if not _is_sha256(intent.intent_sha256):
        parent_reasons.append("invalid_intent_sha256")
    if not intent.account_key:
        parent_reasons.append("missing_account_key")
    if not intent.symbol:
        parent_reasons.append("missing_symbol")
    if intent.side not in {"BUY", "SELL"}:
        parent_reasons.append("invalid_side")

    order_numbers = [child.broker_order_no for child in children]
    if len(order_numbers) != len(set(order_numbers)):
        parent_reasons.append("duplicate_child_order_no")
    if any(child.route not in _CHILD_ROUTES for child in children):
        parent_reasons.append("invalid_child_route")
    if any(child.requested_qty <= 0 for child in children):
        parent_reasons.append("invalid_child_quantity")
    if sum(child.requested_qty for child in children) != intent.requested_qty:
        parent_reasons.append("parent_child_quantity_mismatch")
    if intent.requested_route in _CHILD_ROUTES and any(
        child.route != intent.requested_route for child in children
    ):
        parent_reasons.append("direct_route_child_mismatch")

    if restart:
        if not current_snapshot_complete:
            parent_reasons.append("restart_current_snapshot_incomplete")
        if restart_intent_sha256 != intent.intent_sha256:
            parent_reasons.append("restart_durable_intent_mismatch")

    dated_rows = tuple(dated_evidence)
    current_rows = tuple(current_open_evidence)
    declared = set(order_numbers)
    if any(row.broker_order_no not in declared for row in dated_rows):
        parent_reasons.append("unbound_dated_receipt")
    if any(row.broker_order_no not in declared for row in current_rows):
        parent_reasons.append("unbound_current_receipt")
    if any(
        not _is_sha256(row.receipt_sha256) for row in dated_rows + current_rows
    ):
        parent_reasons.append("invalid_source_receipt_sha256")

    child_results = tuple(
        _reconcile_child(
            intent,
            child,
            tuple(row for row in dated_rows if row.broker_order_no == child.broker_order_no),
            tuple(row for row in current_rows if row.broker_order_no == child.broker_order_no),
            current_snapshot_complete=current_snapshot_complete,
        )
        for child in children
    )

    if parent_reasons or any(
        child.state is ReconciliationState.UNKNOWN for child in child_results
    ):
        state = ReconciliationState.UNKNOWN
    elif any(child.state is ReconciliationState.OPEN for child in child_results):
        state = ReconciliationState.OPEN
    else:
        state = ReconciliationState.TERMINAL

    if state is ReconciliationState.UNKNOWN:
        filled_qty = canceled_qty = remaining_qty = None
        releasable_qty = 0
    else:
        filled_qty = sum(child.filled_qty or 0 for child in child_results)
        canceled_qty = sum(child.confirmed_cancel_qty or 0 for child in child_results)
        remaining_qty = sum(child.broker_remaining_qty or 0 for child in child_results)
        if intent.requested_qty != filled_qty + canceled_qty + remaining_qty:
            state = ReconciliationState.UNKNOWN
            parent_reasons.append("aggregate_quantity_conservation_failed")
            filled_qty = canceled_qty = remaining_qty = None
            releasable_qty = 0
        else:
            # Never release a terminal venue remainder while another SOR child
            # is open or ambiguous; that would duplicate the live commitment.
            releasable_qty = canceled_qty if state is ReconciliationState.TERMINAL else 0

    child_reasons = [reason for child in child_results for reason in child.reasons]
    # Keep every supplied receipt digest, including an unbound receipt that
    # forced UNKNOWN, so the fail-closed result remains auditable.
    source_hashes = tuple(
        sorted({row.receipt_sha256 for row in dated_rows + current_rows})
    )
    return BoundaryReconciliation(
        schema=SCHEMA,
        intent_id=intent.intent_id,
        account_key=intent.account_key,
        order_date=intent.order_date,
        symbol=intent.symbol,
        side=intent.side,
        requested_route=intent.requested_route,
        parent_order_no=intent.parent_order_no,
        intent_sha256=intent.intent_sha256,
        state=state,
        terminal=state is ReconciliationState.TERMINAL,
        requested_qty=intent.requested_qty,
        filled_qty=filled_qty,
        confirmed_cancel_qty=canceled_qty,
        broker_remaining_qty=remaining_qty,
        releasable_qty=releasable_qty,
        successor_blocked=(
            state is not ReconciliationState.TERMINAL or releasable_qty <= 0
        ),
        children=child_results,
        source_sha256s=source_hashes,
        reasons=tuple(sorted(set(parent_reasons + child_reasons))),
    )


__all__ = [
    "BoundaryReconciliation",
    "ChildOrderBinding",
    "ChildReconciliation",
    "DurableParentIntent",
    "OrderEvidence",
    "ReconciliationState",
    "SCHEMA",
    "reconcile_aftermarket_boundary",
]
