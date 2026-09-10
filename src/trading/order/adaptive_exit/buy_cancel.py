"""Opt-in closure of an exact existing owner BUY before whole-position EXIT.

No NEW order method, strategy, automatic enrollment or launcher. The caller
holds its original lifecycle lock, persists the action and supplies independent
cancel authority. BUY fills are quantities only; no price/time/cost is invented.
Shared private dated/current parsing retains SELL's existing public contract.
"""

from dataclasses import dataclass, fields, replace
from datetime import datetime

from src.trading.order.owner_custody_registry import (
    OwnerOrderContext,
    broker_account_key,
)
from .broker import FAMILY, KST, RegisteredSellAdapter, SellContractError, _hash
from .reducer import OrderKey


@dataclass(frozen=True)
class BuySnapshot:
    order: OrderKey
    source_ok: bool = False
    filled_qty: int | None = None
    remaining_qty: int | None = None
    terminal: bool = False
    observed_at_ms: int = 0
    receipt_hash: str = ""
    error: str = ""


@dataclass(frozen=True)
class PricedFullBuySnapshot(BuySnapshot):
    # The dated broker execution unit price, not settlement amount or net EV.
    fill_price: int | None = None


@dataclass(frozen=True)
class PricedCancelledBuySnapshot(BuySnapshot):
    fill_price: int | None = None


@dataclass(frozen=True)
class BuyCancelWrite:
    action: str
    predecessor: OrderKey
    context: OwnerOrderContext
    symbol: str
    route: str
    quantity: int
    policy_hash: str
    action_id: str
    # There is deliberately no price or NEW/SELL method on this adapter.


@dataclass(frozen=True)
class BuyCancelAck:
    intent_id: str
    order: OrderKey | None
    accepted: bool
    ambiguous: bool
    receipt_hash: str
    reason: str


class RegisteredBuyCancelAdapter:
    """Read/reconcile and at most one cancel intent per original dated BUY.

    This is composition, not inheritance: SELL and NEW methods are not public
    BUY capabilities. The mandatory snapshot bound is checked before AND after
    reservation. A changed action ID never resets an ambiguous/rejected intent.
    """

    def __init__(
        self,
        *,
        post,
        registry,
        context,
        symbol,
        routes,
        policy_hash,
        maximum_quantity,
        require_write_authority,
        max_snapshot_age_ms,
        write_guard=None,
        now_ms=None,
    ):
        if type(max_snapshot_age_ms) is not int or max_snapshot_age_ms <= 0:
            raise ValueError("buy_cancel_snapshot_bound_required")
        self.max_snapshot_age_ms = max_snapshot_age_ms
        self.write_guard = write_guard
        self._transport = RegisteredSellAdapter(
            post=post,
            registry=registry,
            context=context,
            symbol=symbol,
            routes=routes,
            policy_hash=policy_hash,
            maximum_quantity=maximum_quantity,
            require_write_authority=require_write_authority,
            write_guard=self._guard,
            now_ms=now_ms,
        )

    def _guard(self, request):
        if (
            type(request) is not BuyCancelWrite
            or request.action != "CANCEL"
            or self.write_guard is None
            or self.write_guard(request) is not True
        ):
            raise PermissionError("approved_original_owner_buy_cancel_guard_required")
        self._transport._owned_for_side(request.predecessor, "BUY")
        return True

    def client_id(self, order):
        self._transport._owned_for_side(order, "BUY")
        return (
            FAMILY
            + ":buy-cancel:"
            + _hash([self._transport.account_key, order.trading_date, order.order_no])
        )

    def _fresh(self, order, started, observed):
        t = self._transport
        now = t.now_ms()
        if (
            not started <= observed <= now
            or not 0 <= now - started <= self.max_snapshot_age_ms
            or datetime.fromtimestamp(now / 1000, KST).date().isoformat()
            != order.trading_date
            or t.account_key != broker_account_key(require_explicit=True)
        ):
            raise SellContractError("buy_cancel_snapshot_stale_or_scope_changed")

    def snapshot(self, order):
        t = self._transport
        start = t.now_ms()
        raw, _ = t._snapshot(order, _side="BUY")
        result = BuySnapshot(
            **{field.name: getattr(raw, field.name) for field in fields(BuySnapshot)}
        )
        if result.source_ok:
            try:
                self._fresh(order, start, result.observed_at_ms)
            except SellContractError as exc:
                return BuySnapshot(order, error=str(exc))
        return result

    def _bind_fill(self, row, snapshot):
        t = self._transport
        if snapshot.terminal and (
            row["quantity"] != snapshot.filled_qty + row.get("canceled_qty", 0)
            or (
                row.get("canceled_qty", 0)
                and not row.get("terminal_cancel_reconciliation")
            )
        ):
            raise SellContractError("buy_terminal_cancel_confirmation_required")
        t.registry.record_fill(
            context=t.context,
            symbol=t.symbol,
            side="BUY",
            order_quantity=row["quantity"],
            order_date=snapshot.order.trading_date,
            broker_order_no=snapshot.order.order_no,
            cumulative_filled_qty=snapshot.filled_qty,
        )
        if snapshot.terminal:
            t.registry.transition(
                row["intent_id"],
                state="ORDER_TERMINAL",
                broker_order_no=snapshot.order.order_no,
                reason="adaptive_buy_dated_current_reconciled",
            )
            t.registry.record_buy_terminal_reconciliation(
                context=t.context,
                symbol=t.symbol,
                order_quantity=row["quantity"],
                order_date=snapshot.order.trading_date,
                broker_order_no=snapshot.order.order_no,
                cumulative_filled_qty=snapshot.filled_qty,
                receipt_sha256=snapshot.receipt_hash,
            )

    def reconcile_owned_buy(self, order):
        result = self.snapshot(order)
        if result.source_ok:
            try:
                self._bind_fill(self._transport._owned_for_side(order, "BUY"), result)
            except SellContractError as exc:
                return BuySnapshot(order, error=str(exc))
            except Exception:
                return BuySnapshot(order, error="buy_registry_reconciliation_failed")
        return result

    def reconcile_priced_full_buy(self, order, *, guard):
        """Read-only broker recovery; no partial/cancelled BUY normalization.

        Requires the original owner lock/authority again after the bounded
        read. The caller separately journals its leg projection before an
        existing target owner can resume. No BUY or cancel is submitted here.
        """
        t = self._transport
        if not callable(guard) or guard() is not True:
            return PricedFullBuySnapshot(order, error="full_buy_owner_guard_missing")
        raw, proof = t._snapshot(order, _side="BUY", _full_buy_price=True)
        if not raw.source_ok:
            return PricedFullBuySnapshot(
                **{
                    field.name: getattr(raw, field.name)
                    for field in fields(BuySnapshot)
                }
            )
        try:
            self._fresh(order, proof["started_at_ms"], raw.observed_at_ms)
            if guard() is not True:
                raise SellContractError("full_buy_owner_guard_lost")
            self._bind_fill(t._owned_for_side(order, "BUY"), raw)
            if guard() is not True:
                raise SellContractError("full_buy_owner_guard_lost")
            return PricedFullBuySnapshot(
                **{
                    field.name: getattr(raw, field.name)
                    for field in fields(BuySnapshot)
                },
                fill_price=proof["fill_price"],
            )
        except SellContractError as exc:
            return PricedFullBuySnapshot(order, error=str(exc))
        except Exception:
            return PricedFullBuySnapshot(
                order, error="full_buy_registry_reconciliation_failed"
            )

    def reconcile_terminal_cancel(self, order, cancel_order):
        return self._terminal_cancel(order, cancel_order)

    def reconcile_priced_terminal_cancel(self, order, cancel_order, *, guard):
        return self._terminal_cancel(order, cancel_order, priced=True, guard=guard)

    def _terminal_cancel(self, order, cancel_order, *, priced=False, guard=None):
        t = self._transport
        result_type = PricedCancelledBuySnapshot if priced else BuySnapshot
        if priced and (not callable(guard) or guard() is not True):
            return result_type(order, error="cancelled_buy_owner_guard_missing")
        raw, proof = t._snapshot(
            order,
            cancel_order=cancel_order,
            terminal_cancel=True,
            _side="BUY",
            _cancelled_buy_price=priced,
        )
        result = result_type(
            **{field.name: getattr(raw, field.name) for field in fields(BuySnapshot)}
        )
        if result.source_ok:
            try:
                if proof is None:
                    raise SellContractError("buy_cancel_exact_proof_required")
                self._fresh(order, proof["started_at_ms"], result.observed_at_ms)
                if priced and guard() is not True:
                    raise SellContractError("cancelled_buy_owner_guard_lost")
                t.registry.record_buy_terminal_cancel_reconciliation(
                    context=t.context,
                    order_date=order.trading_date,
                    target_order_no=order.order_no,
                    cancel_order_no=cancel_order.order_no,
                    filled_qty=result.filled_qty,
                    terminal_receipt_sha256=result.receipt_hash,
                    **{
                        k: v
                        for k, v in proof.items()
                        if k not in {"started_at_ms", "fill_price"}
                    },
                )
                if priced:
                    if guard() is not True:
                        raise SellContractError("cancelled_buy_owner_guard_lost")
                    result = result_type(
                        **{
                            field.name: getattr(raw, field.name)
                            for field in fields(BuySnapshot)
                        },
                        fill_price=proof["fill_price"],
                    )
            except SellContractError as exc:
                return result_type(order, error=str(exc))
            except Exception:
                return result_type(
                    order, error="buy_cancel_registry_reconciliation_failed"
                )
        return result

    def cancel_owned_buy(self, order, *, quantity, action_id):
        t = self._transport
        row = t._owned_for_side(order, "BUY")
        if (
            type(quantity) is not int
            or not 0 < quantity <= row["quantity"]
            or not isinstance(action_id, str)
            or not action_id.strip()
        ):
            raise ValueError("buy_cancel_positive_quantity_and_durable_action_required")
        request = BuyCancelWrite(
            "CANCEL",
            order,
            replace(t.context, client_intent_id=self.client_id(order)),
            t.symbol,
            row["route"],
            quantity,
            t.policy_hash,
            action_id,
        )
        t._guard(request)
        # A bounded re-read is unnecessary when this slot is already spent.
        if t.registry.intent_for_client(context=request.context) is not None:
            raise ValueError("buy_cancel_intent_already_spent_requires_recovery")
        start = t.now_ms()
        snapshot = self.snapshot(order)
        if (
            not snapshot.source_ok
            or snapshot.terminal
            or snapshot.remaining_qty != quantity
        ):
            raise ValueError("buy_cancel_exact_fresh_remaining_required")
        self._bind_fill(row, snapshot)

        def source_guard():
            self._fresh(order, start, snapshot.observed_at_ms)
            current = t._owned_for_side(order, "BUY")
            if (
                current.get("state") != "ORDER_BOUND"
                or current["filled_qty"] != snapshot.filled_qty
                or current["quantity"]
                - current["filled_qty"]
                - current.get("canceled_qty", 0)
                != quantity
            ):
                raise ValueError("buy_cancel_owner_quantity_changed")

        ack = t._write(
            request,
            "kt10003",
            {
                "dmst_stex_tp": request.route,
                "orig_ord_no": order.order_no,
                "stk_cd": t.symbol,
                "cncl_qty": str(quantity),
            },
            source_guard=source_guard,
            _side="BUY",
        )
        return BuyCancelAck(**ack.__dict__)
