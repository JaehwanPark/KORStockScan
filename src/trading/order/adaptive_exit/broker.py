"""Registry-bound SELL transport, not an exit policy loader or runtime loop.

The original owner holds its lifecycle lock and persists the driver intent
before calling this adapter. A supplied write guard must validate its frozen
approved policy, fresh executable price, account/manual vetoes and all-venue
custody. Without that guard writes are disabled. Research artifacts cannot
activate this class. No BUY, market order, zero-quantity cancel or write retry.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import re
import time
from typing import Callable
from zoneinfo import ZoneInfo

from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
    broker_account_key,
)
from src.trading.order.tick_utils import get_tick_size
from .reducer import OrderKey

KST = ZoneInfo("Asia/Seoul")
FAMILY = "machine_adaptive_exit_v1"
OFFICIAL_REFERENCE_SHA = "234560d213acd8871ae344b5481aecd2f30287fa"


class SellContractError(ValueError):
    """Local constant-only diagnostics, never raw transport error text."""


def _count(value: object) -> int:
    # No float coercion, abs(), missing->0 or normalization of negative counts.
    if isinstance(value, bool) or not re.fullmatch(r"\+?[0-9]+", str(value)):
        raise SellContractError("invalid_share_count")
    return int(value)


def _number(value: object) -> str:
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[0-9]{7}", value)
        or int(value) == 0
    ):
        raise SellContractError("invalid_broker_order_number")
    return value


def _hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class SellSnapshot:
    order: OrderKey
    source_ok: bool = False
    filled_qty: int | None = None
    remaining_qty: int | None = None
    terminal: bool = False
    observed_at_ms: int = 0
    receipt_hash: str = ""
    error: str = ""


@dataclass(frozen=True)
class SellWrite:
    action: str
    predecessor: OrderKey
    context: OwnerOrderContext
    symbol: str
    route: str
    quantity: int
    limit_price: int | None
    policy_hash: str


@dataclass(frozen=True)
class SellAck:
    intent_id: str
    order: OrderKey | None
    accepted: bool
    ambiguous: bool
    receipt_hash: str
    reason: str
    # Intentionally no terminal flag: even a valid cancel ACK releases nothing.


class RegisteredSellAdapter:
    """Fresh dated/current read reconciliation and durable owned write binding.

    The single-lot method requires a terminal independent target. A separate
    opt-in group method consumes one exact confirmed partial-cancel release;
    neither method invents per-lot fill attribution on a shared target.
    Caller assigns a durable unique action_id for each reducer attempt. The
    registry forbids reusing it even after an ambiguous submit or process crash.
    """

    def __init__(
        self,
        *,
        post: Callable,
        registry: OrderOwnerRegistry,
        context: OwnerOrderContext,
        symbol: str,
        routes: tuple[str, ...],
        policy_hash: str,
        maximum_quantity: int | None,
        require_write_authority: Callable[[], None],
        write_guard: Callable[[SellWrite], bool] | None = None,
        now_ms: Callable[[], int] | None = None,
        new_route: Callable[[str], str] | None = None,
    ):
        context.validate()
        if (
            context.owner_type not in {"widget_auto_trade", "episode"}
            or not re.fullmatch(r"[0-9]{6}", symbol)
            or not routes
            or any(r not in {"KRX", "SOR", "NXT"} for r in routes)
            or not re.fullmatch(r"[0-9a-f]{64}", policy_hash)
            or (
                maximum_quantity is not None
                and (type(maximum_quantity) is not int or maximum_quantity <= 0)
            )
        ):
            raise ValueError("invalid_owned_sell_adapter_binding")
        self.post, self.registry, self.context = post, registry, context
        self.symbol, self.routes, self.policy_hash = symbol, routes, policy_hash
        self.maximum_quantity = maximum_quantity
        self.require_write_authority, self.write_guard = (
            require_write_authority,
            write_guard,
        )
        self.now_ms = now_ms or (lambda: time.time_ns() // 1_000_000)
        self.new_route = new_route or (lambda route: route)
        self.account_key = broker_account_key(require_explicit=True)

    def _owned(self, order):
        if not isinstance(order, OrderKey):
            raise SellContractError("exact_dated_order_required")
        _number(order.order_no)
        if self.account_key != broker_account_key(require_explicit=True):
            raise SellContractError("adapter_account_changed")
        row = self.registry.assert_owner(
            context=self.context,
            order_date=order.trading_date,
            broker_order_no=order.order_no,
        )
        quantity = _count(row.get("quantity"))
        if (
            row.get("symbol") != self.symbol
            or row.get("side") != "SELL"
            or row.get("action") != "NEW"
            or row.get("route") not in self.routes
            or quantity <= 0
            or (self.maximum_quantity is not None and quantity > self.maximum_quantity)
        ):
            raise SellContractError("owned_sell_scope_mismatch")
        return row

    def _pages(self, api_id, payload, field):
        result, hashes, seen_keys = [], [], set()
        cont, key = "N", ""
        for _ in range(3):
            response, body = self.post(
                endpoint="/api/dostk/acnt",
                api_id=api_id,
                payload=payload,
                cont_yn=cont,
                next_key=key,
            )
            if (
                response.status_code != 200
                or not isinstance(body, dict)
                or _count(body.get("return_code")) != 0
                or not isinstance(body.get(field), list)
            ):
                raise SellContractError("broker_read_rejected_or_missing_list")
            if any(not isinstance(row, dict) for row in body[field]):
                raise SellContractError("broker_row_not_mapping")
            result.extend(body[field])
            # Hash raw page, never persist its account fields, messages or token.
            hashes.append(_hash(body))
            headers = {str(k).lower(): v for k, v in response.headers.items()}
            if headers.get("api-id", api_id) != api_id:
                raise SellContractError("broker_response_api_mismatch")
            cont, key = headers.get("cont-yn"), headers.get("next-key", "")
            # Official response headers are optional when there is no next
            # page. Requiring a literal N would reject valid complete replies.
            # A dangling cursor without Y is a conflict, not a terminal page.
            if cont in (None, "", "N") and key in (None, ""):
                return result, hashes
            if (
                cont != "Y"
                or not isinstance(key, str)
                or not key.strip()
                or key in seen_keys
            ):
                raise SellContractError("invalid_broker_continuation")
            seen_keys.add(key)
        raise SellContractError("broker_continuation_bound_exhausted")

    def snapshot(self, order: OrderKey) -> SellSnapshot:
        """Read-only; no stale transport cache and no absence-only terminal proof."""
        return self._snapshot(order)[0]

    def _snapshot(self, order: OrderKey, *, cancel_order: OrderKey | None = None):
        try:
            owned = self._owned(order)
            cancel = None
            if cancel_order is not None:
                if (
                    not isinstance(cancel_order, OrderKey)
                    or cancel_order.trading_date != order.trading_date
                    or cancel_order == order
                ):
                    raise SellContractError("partial_cancel_exact_identity_required")
                cancel = self.registry.assert_owner(
                    context=self.context,
                    order_date=cancel_order.trading_date,
                    broker_order_no=_number(cancel_order.order_no),
                )
                if (
                    cancel.get("action") != "CANCEL"
                    or cancel.get("side") != "SELL"
                    or cancel.get("original_order_no") != order.order_no
                    or cancel.get("symbol") != self.symbol
                    or cancel.get("route") != owned["route"]
                    or cancel.get("authority_policy_id") != FAMILY
                    or cancel.get("authority_policy_hash") != self.policy_hash
                    or cancel.get("state") not in {"ORDER_BOUND", "ORDER_TERMINAL"}
                    or type(cancel.get("quantity")) is not int
                    or cancel["quantity"] <= 0
                ):
                    raise SellContractError("partial_cancel_owner_binding_mismatch")
            start = self.now_ms()
            today = datetime.fromtimestamp(start / 1000, KST).date().isoformat()
            # Current-unfilled has no date. Do not guess reused order identity.
            if order.trading_date != today:
                raise SellContractError(
                    "cross_date_current_ledger_requires_owner_recovery"
                )
            detailed, dh = self._pages(
                "kt00007",
                {
                    "ord_dt": today.replace("-", ""),
                    "qry_tp": "1",
                    "stk_bond_tp": "1",
                    "sell_tp": "1",
                    "stk_cd": self.symbol,
                    "fr_ord_no": "",
                    "dmst_stex_tp": "%",
                },
                "acnt_ord_cntr_prps_dtl",
            )
            current, ch = self._pages(
                "ka10075",
                {
                    "all_stk_tp": "1",
                    "trde_tp": "1",
                    "stk_cd": self.symbol,
                    "stex_tp": "0",
                },
                "oso",
            )
            root, open_root, cancel_confirmations = set(), set(), set()
            descendants = {order.order_no}
            links = [(r.get("ord_no"), r.get("ori_ord")) for r in detailed]
            links += [(r.get("ord_no"), r.get("orig_ord_no")) for r in current]
            for _ in range(len(links)):
                before = len(descendants)
                descendants.update(
                    n
                    for n, parent in links
                    if isinstance(n, str)
                    and isinstance(parent, str)
                    and parent in descendants
                )
                if len(descendants) == before:
                    break
            for rows, is_current in ((detailed, False), (current, True)):
                for row in rows:
                    number = _number(row.get("ord_no"))
                    original = row.get("orig_ord_no" if is_current else "ori_ord")
                    if original not in ("", "0000000"):
                        _number(original)
                    symbol = row.get("stk_cd")
                    if not isinstance(symbol, str) or not re.fullmatch(
                        r"[AJQ]?[0-9]{6}", symbol
                    ):
                        raise SellContractError("broker_symbol_invalid")
                    if symbol[-6:] != self.symbol:
                        raise SellContractError("broker_symbol_scope_conflict")
                    qty, filled = (
                        _count(row.get("ord_qty")),
                        _count(row.get("cntr_qty")),
                    )
                    remaining = _count(
                        row.get("oso_qty" if is_current else "ord_remnq")
                    )
                    if (
                        qty <= 0
                        or filled > qty
                        or remaining > qty
                        or filled + remaining > qty
                    ):
                        raise SellContractError("broker_quantity_conflict")
                    if number in descendants:
                        if is_current:
                            venue, sor = row.get("stex_tp"), row.get("sor_yn")
                            if (
                                venue not in {"0", "1", "2"}
                                or sor not in {"Y", "N"}
                                or (owned["route"] == "SOR" and sor != "Y")
                                or (
                                    owned["route"] != "SOR"
                                    and (
                                        sor != "N"
                                        or venue
                                        != {"KRX": "1", "NXT": "2"}[owned["route"]]
                                    )
                                )
                            ):
                                raise SellContractError("current_broker_route_conflict")
                        else:
                            venue = row.get("dmst_stex_tp")
                            if venue not in {"KRX", "NXT", "SOR"} or (
                                owned["route"] != "SOR" and venue != owned["route"]
                            ):
                                raise SellContractError("dated_broker_route_unresolved")
                    if number == order.order_no:
                        if original not in ("", "0000000") or qty != owned["quantity"]:
                            raise SellContractError("broker_original_identity_conflict")
                        (open_root if is_current else root).add((filled, remaining))
                    elif original in descendants:
                        successor = self.registry.order_owner(
                            order_date=today, broker_order_no=number
                        )
                        # Known CANCEL request may appear in history, but an
                        # open successor or unknown modification cannot vanish.
                        if (
                            not successor
                            or successor.get("action") != "CANCEL"
                            or successor.get("original_order_no") != order.order_no
                            or any(
                                successor.get(k) != owned.get(k)
                                for k in (
                                    "owner_type",
                                    "owner_id",
                                    "position_id",
                                    "symbol",
                                )
                            )
                            or (is_current and remaining > 0)
                        ):
                            raise SellContractError("unknown_or_open_successor")
                        if cancel is not None and number == cancel_order.order_no:
                            if is_current:
                                raise SellContractError("partial_cancel_still_current")
                            # No undocumented status enum is promoted. Accept
                            # only the entire requested quantity confirmed in
                            # dated history AND the same reduction in both root
                            # ledgers; ACK, partial confirmation and absence
                            # alone never release shares.
                            confirmed = _count(row.get("cnfm_qty"))
                            stamp = row.get("cnfm_tm")
                            if not isinstance(stamp, str) or not re.fullmatch(
                                r"[0-9]{2}:[0-9]{2}:[0-9]{2}", stamp
                            ):
                                raise SellContractError(
                                    "partial_cancel_confirmation_time_missing"
                                )
                            confirmed_at = int(
                                datetime.fromisoformat(today + "T" + stamp)
                                .replace(tzinfo=KST)
                                .timestamp()
                                * 1000
                            )
                            if (
                                qty != cancel["quantity"]
                                or confirmed != qty
                                or filled != 0
                                or remaining != 0
                                or confirmed_at > start
                            ):
                                raise SellContractError(
                                    "partial_cancel_confirmation_incomplete"
                                )
                            cancel_confirmations.add((qty, confirmed_at))
            if len(root) != 1 or len(open_root) > 1:
                raise SellContractError("missing_or_conflicting_dated_order")
            filled, remaining = next(iter(root))
            if filled < owned.get("filled_qty", 0):
                raise SellContractError("broker_fill_regression")
            if filled + remaining + owned.get("canceled_qty", 0) > owned["quantity"]:
                raise SellContractError("broker_canceled_quantity_regression")
            if open_root and open_root != root:
                raise SellContractError("dated_current_quantity_race")
            if remaining and not open_root:
                raise SellContractError("absence_without_dated_terminal")
            if cancel is not None:
                prior = owned.get("canceled_qty", 0)
                if cancel.get("cancel_reconciliation") is None:
                    prior += cancel["quantity"]
                if (
                    len(cancel_confirmations) != 1
                    or remaining <= 0
                    or owned.get("state") != "ORDER_BOUND"
                    or owned["quantity"] != filled + remaining + prior
                ):
                    raise SellContractError("partial_cancel_root_conservation_unproved")
            end = self.now_ms()
            if (
                end < start
                or datetime.fromtimestamp(end / 1000, KST).date().isoformat() != today
            ):
                raise SellContractError("reconciliation_clock_or_date_changed")
            snapshot = SellSnapshot(
                order,
                True,
                filled,
                remaining,
                remaining == 0,
                end,
                _hash(
                    {
                        "dated": dh,
                        "current": ch,
                        "order": order.__dict__,
                        "account_scope": _hash(self.account_key),
                        "start": start,
                        "end": end,
                    }
                ),
            )
            return snapshot, (
                {
                    "target_event_hash": owned["event_hash"],
                    "cancel_event_hash": cancel["event_hash"],
                    "confirmed_qty": cancel["quantity"],
                    "receipt_sha256": _hash(
                        {
                            "root_receipt": snapshot.receipt_hash,
                            "cancel": cancel_order.__dict__,
                            "confirmation": sorted(cancel_confirmations),
                        }
                    ),
                    "started_at_ms": start,
                }
                if cancel is not None
                else None
            )
        except Exception as exc:
            # Never leak response text, token or account numbers into an alert.
            reason = str(exc) if type(exc) is SellContractError else type(exc).__name__
            return SellSnapshot(order, error=reason), None

    def reconcile_partial_cancel(
        self,
        order: OrderKey,
        cancel_order: OrderKey,
        *,
        max_snapshot_age_ms: int,
    ) -> SellSnapshot:
        """Reconcile a fully confirmed partial request without a broker write.

        This opt-in quantity primitive is not group enrollment or runner SELL.
        The future coordinator supplies its approved freshness bound. Existing
        single-lot consumers do not call it or bypass whole-target terminal.
        """
        if type(max_snapshot_age_ms) is not int or max_snapshot_age_ms <= 0:
            raise ValueError("partial_cancel_freshness_bound_required")
        snapshot, proof = self._snapshot(order, cancel_order=cancel_order)
        if snapshot.source_ok:
            try:
                now = self.now_ms()
                if (
                    proof is None
                    or not 0 <= now - proof["started_at_ms"] <= max_snapshot_age_ms
                    or datetime.fromtimestamp(now / 1000, KST).date().isoformat()
                    != order.trading_date
                    or self.account_key != broker_account_key(require_explicit=True)
                ):
                    raise SellContractError(
                        "partial_cancel_snapshot_stale_or_account_changed"
                    )
                self.registry.record_partial_cancel_reconciliation(
                    context=self.context,
                    order_date=order.trading_date,
                    target_order_no=order.order_no,
                    cancel_order_no=cancel_order.order_no,
                    filled_qty=snapshot.filled_qty,
                    remaining_qty=snapshot.remaining_qty,
                    **{k: v for k, v in proof.items() if k != "started_at_ms"},
                )
            except SellContractError as exc:
                return SellSnapshot(order, error=str(exc))
            except Exception:
                return SellSnapshot(
                    order, error="partial_cancel_registry_reconciliation_failed"
                )
        return snapshot

    def reconcile_owned_sell(self, order: OrderKey) -> SellSnapshot:
        """Persist exact cumulative fills in the same owner registry, not PnL."""
        snapshot = self.snapshot(order)
        if snapshot.source_ok:
            try:
                self._bind_fill(self._owned(order), snapshot)
            except Exception:
                return SellSnapshot(order, error="owner_registry_reconciliation_failed")
        return snapshot

    def recover_replacement(
        self, predecessor: OrderKey, *, quantity: int
    ) -> SellSnapshot | None:
        """Recover only a durably bound ACK; ambiguous/unbound intents stay held.

        A symbol/time/quantity match cannot invent the missing broker identity.
        No write, retry, date rebasing or cancellation-ACK terminal inference.
        """
        self._owned(predecessor)
        context = replace(
            self.context, client_intent_id=self._replacement_client_id(predecessor)
        )
        row = self.registry.intent_for_client(context=context)
        if row is None or row.get("state") not in {"ORDER_BOUND", "ORDER_TERMINAL"}:
            return None
        if (
            type(quantity) is not int
            or quantity <= 0
            or row.get("quantity") != quantity
            or row.get("order_date") != predecessor.trading_date
            or row.get("symbol") != self.symbol
            or row.get("side") != "SELL"
            or row.get("action") != "NEW"
            or row.get("authority_policy_id") != FAMILY
            or row.get("authority_policy_hash") != self.policy_hash
        ):
            raise SellContractError("replacement_recovery_binding_mismatch")
        order = OrderKey(row["order_date"], _number(row.get("broker_order_no")))
        if order == predecessor:
            raise SellContractError("replacement_recovery_reuses_predecessor")
        return self.reconcile_owned_sell(order)

    def _replacement_client_id(self, order):
        return (
            FAMILY
            + ":replacement:"
            + _hash([self.account_key, order.trading_date, order.order_no])
        )

    def _guard(self, request):
        if self.write_guard is None or self.write_guard(request) is not True:
            raise PermissionError("approved_frozen_owner_write_guard_required")
        if self.account_key != broker_account_key(require_explicit=True):
            raise PermissionError("adapter_account_changed")
        if (
            datetime.fromtimestamp(self.now_ms() / 1000, KST).date().isoformat()
            != request.predecessor.trading_date
        ):
            raise PermissionError("write_date_changed")
        self.require_write_authority()

    def _request(self, action, order, quantity, action_id, price=None):
        owned = self._owned(order)
        if (
            type(quantity) is not int
            or quantity <= 0
            or (self.maximum_quantity is not None and quantity > self.maximum_quantity)
            or not isinstance(action_id, str)
            or not action_id.strip()
        ):
            raise ValueError("positive_exact_quantity_and_durable_action_required")
        if action == "NEW" and (
            type(price) is not int or price <= 0 or price % get_tick_size(price)
        ):
            raise ValueError("valid_integer_limit_price_required")
        # One successor per dated predecessor even if a caller invents a new
        # action id after a crash. Further bounded attempts must use the last
        # terminal replacement, never re-spend the original lot's reservation.
        client_id = (
            action_id if action == "CANCEL" else self._replacement_client_id(order)
        )
        context = replace(self.context, client_intent_id=client_id)
        context.validate()
        route = owned["route"] if action == "CANCEL" else self.new_route(owned["route"])
        if route not in self.routes:
            raise ValueError("replacement_route_not_supported")
        return owned, SellWrite(
            action,
            order,
            context,
            self.symbol,
            route,
            quantity,
            price,
            self.policy_hash,
        )

    def _bind_fill(self, owned, snapshot):
        self.registry.record_fill(
            context=self.context,
            symbol=self.symbol,
            side="SELL",
            order_quantity=owned["quantity"],
            order_date=snapshot.order.trading_date,
            broker_order_no=snapshot.order.order_no,
            cumulative_filled_qty=snapshot.filled_qty,
        )
        if snapshot.terminal:
            self.registry.transition(
                owned["intent_id"],
                state="ORDER_TERMINAL",
                broker_order_no=snapshot.order.order_no,
                reason="adaptive_dated_current_reconciled",
            )
            self.registry.record_terminal_reconciliation(
                context=self.context,
                symbol=self.symbol,
                order_quantity=owned["quantity"],
                order_date=snapshot.order.trading_date,
                broker_order_no=snapshot.order.order_no,
                cumulative_filled_qty=snapshot.filled_qty,
                receipt_sha256=snapshot.receipt_hash,
            )

    def cancel_owned_sell(
        self, order: OrderKey, *, quantity: int, action_id: str
    ) -> SellAck:
        owned, request = self._request("CANCEL", order, quantity, action_id)
        self._guard(request)
        snapshot = self.snapshot(order)
        if (
            not snapshot.source_ok
            or snapshot.terminal
            or quantity > snapshot.remaining_qty
        ):
            raise ValueError("fresh_owned_open_remainder_required")
        self._bind_fill(owned, snapshot)
        return self._write(
            request,
            "kt10003",
            {
                "dmst_stex_tp": request.route,
                "orig_ord_no": order.order_no,
                "stk_cd": self.symbol,
                "cncl_qty": str(quantity),
            },
        )

    def submit_owned_sell(
        self, predecessor: OrderKey, *, quantity: int, limit_price: int, action_id: str
    ) -> SellAck:
        owned, request = self._request(
            "NEW", predecessor, quantity, action_id, limit_price
        )
        self._guard(request)
        snapshot = self.snapshot(predecessor)
        if (
            not snapshot.source_ok
            or not snapshot.terminal
            or quantity > owned["quantity"] - snapshot.filled_qty
        ):
            raise ValueError("exact_terminal_predecessor_and_residual_required")
        self._bind_fill(owned, snapshot)
        return self._write(
            request,
            "kt10001",
            {
                "dmst_stex_tp": request.route,
                "stk_cd": self.symbol,
                "ord_qty": str(quantity),
                "ord_uv": str(limit_price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )

    def submit_partial_cancel_residual(
        self,
        predecessor: OrderKey,
        cancel_order: OrderKey,
        *,
        quantity: int,
        limit_price: int,
        action_id: str,
        max_snapshot_age_ms: int,
    ) -> SellAck:
        """One group successor from an exact fully confirmed partial cancel.

        This does not relax the single-lot whole-terminal method above. The
        group owner must durably bind its approved action before calling and
        provide the normal write guard. The registry atomically preserves the
        live target's remaining commitment. The deterministic NEW client ID
        prevents spending this predecessor twice, including after a lost ACK.
        """
        _, request = self._request("NEW", predecessor, quantity, action_id, limit_price)
        self._guard(request)
        started = self.now_ms()
        snapshot = self.reconcile_partial_cancel(
            predecessor, cancel_order, max_snapshot_age_ms=max_snapshot_age_ms
        )
        if not snapshot.source_ok or snapshot.terminal:
            raise ValueError("exact_partial_cancel_residual_required")
        target = self._owned(predecessor)
        cancel = self.registry.assert_owner(
            context=self.context,
            order_date=cancel_order.trading_date,
            broker_order_no=cancel_order.order_no,
        )
        proof = cancel.get("cancel_reconciliation")
        if (
            not isinstance(proof, dict)
            or cancel.get("state") != "ORDER_TERMINAL"
            or target.get("state") != "ORDER_BOUND"
            or target.get("partial_cancel_reconciliation") != proof
            or proof.get("confirmed_qty") != quantity
            or target.get("canceled_qty") != quantity
            or target.get("filled_qty") != snapshot.filled_qty
            or target["quantity"]
            != snapshot.filled_qty + snapshot.remaining_qty + quantity
        ):
            raise ValueError("partial_cancel_single_release_quantity_conflict")

        def require_fresh_release():
            now = self.now_ms()
            if not (
                0 <= now - started <= max_snapshot_age_ms
                and started <= snapshot.observed_at_ms <= now
            ):
                raise ValueError("partial_cancel_release_expired_before_write")

        return self._write(
            request,
            "kt10001",
            {
                "dmst_stex_tp": request.route,
                "stk_cd": self.symbol,
                "ord_qty": str(quantity),
                "ord_uv": str(limit_price),
                "trde_tp": "0",
                "cond_uv": "",
            },
            source_guard=require_fresh_release,
        )

    def _write(self, request, api_id, payload, *, source_guard=None):
        # Recheck price/account/veto after all possibly slow reads, before reserve.
        self._guard(request)
        if source_guard is not None:
            source_guard()
        intent = self.registry.reserve(
            context=request.context,
            symbol=self.symbol,
            side="SELL",
            quantity=request.quantity,
            route=request.route,
            order_date=request.predecessor.trading_date,
            action=request.action,
            original_order_no=(
                request.predecessor.order_no if request.action == "CANCEL" else ""
            ),
            authority_policy_id=FAMILY,
            authority_policy_hash=self.policy_hash,
        )
        # An atomic registry/fsync wait can outlive price/date/owner approval.
        # If this fails, retain the durable reservation for explicit recovery;
        # never post and never blindly retry it after restart.
        self._guard(request)
        if source_guard is not None:
            source_guard()
        order, accepted, ambiguous, reason, receipt = (
            None,
            False,
            True,
            "write_ambiguous",
            "",
        )
        try:
            response, body = self.post(
                endpoint="/api/dostk/ordr", api_id=api_id, payload=payload
            )
            receipt = _hash(body)
            code = _count(body.get("return_code"))
            if response.status_code == 200 and code == 0:
                number = _number(body.get("ord_no"))
                if request.action == "CANCEL":
                    if (
                        body.get("base_orig_ord_no") != request.predecessor.order_no
                        or _count(body.get("cncl_qty")) != request.quantity
                        or number == request.predecessor.order_no
                    ):
                        raise ValueError("cancel_ack_identity_mismatch")
                elif body.get("dmst_stex_tp") != request.route:
                    raise ValueError("sell_ack_route_mismatch")
                order = OrderKey(request.predecessor.trading_date, number)
                accepted, ambiguous, reason = True, False, "ack_only"
            # Even HTTP 429/5xx with a business code is not proof of no order.
            elif response.status_code == 200 and code != 0 and not body.get("ord_no"):
                ambiguous, reason = False, "explicit_broker_rejection"
        except Exception:
            pass  # Durable reservation survives transport/parser ambiguity.
        self.registry.transition(
            intent,
            state=(
                "ORDER_BOUND"
                if accepted
                else "INTENT_AMBIGUOUS" if ambiguous else "INTENT_REJECTED"
            ),
            broker_order_no=order.order_no if order else "",
            reason=reason,
        )
        return SellAck(intent, order, accepted, ambiguous, receipt, reason)
