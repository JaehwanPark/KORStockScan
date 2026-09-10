"""Original episode's bounded pending-BUY closure, never a new order owner.

The launcher must supply an independent guard and explicit confirmation bound.
No default enablement, BUY, pooled SELL, cancel-all, or write retry is provided.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from typing import Callable

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from .broker import FAMILY, RegisteredSellAdapter
from .buy_cancel import BuyCancelWrite, RegisteredBuyCancelAdapter
from .reducer import OrderKey
from .source import record_first_fill_observation
from .episode_buy_recovery import (
    KEY as RECOVERY_KEY,
    TerminalRecoveryServices,
    recover,
    require_durable_recovery_state,
    validate_record,
)

KEY = "adaptive_pending_buy_resolution"
SCHEMA = "episode_adaptive_pending_buy_v1"


@dataclass(frozen=True)
class EpisodePendingBuyServices:
    # Operational confirmation deadline, not a holding/exit risk threshold.
    confirmation_timeout_ms: int
    authorize: Callable[[dict], bool]
    terminal_recovery: TerminalRecoveryServices | None = None

    def __post_init__(self):
        if (
            type(self.confirmation_timeout_ms) is not int
            or self.confirmation_timeout_ms <= 0
            or not callable(self.authorize)
            or (
                self.terminal_recovery is not None
                and not isinstance(self.terminal_recovery, TerminalRecoveryServices)
            )
        ):
            raise ValueError("explicit_pending_buy_confirmation_contract_required")


def _ordinary(leg):
    return canonical_sha256({k: v for k, v in leg.items() if k != KEY})


def validate_projection(machine, leg):
    """Recheck durable BUY proof at both the manager and original SELL consumer."""
    from .runtime import OwnerSession

    journal = leg.get(KEY)
    receipt = leg.get("adaptive_sibling_full_buy_receipt")
    if journal is None and not (
        isinstance(receipt, dict)
        and receipt.get("schema") == "episode_adaptive_sibling_cancelled_buy_v1"
    ):
        return
    if (
        not isinstance(journal, dict)
        or journal.get("schema") != SCHEMA
        or journal.get("phase") != "PROJECTED"
        or journal.get("canonical_sha256") != canonical_sha256(journal)
        or not isinstance(journal.get("binding"), dict)
        or not isinstance(receipt, dict)
        or journal.get("terminal_receipt") != receipt
        or receipt.get("canonical_sha256") != canonical_sha256(receipt)
    ):
        raise ValueError("pending_buy_projection_journal_invalid")
    binding = journal.get("binding", {})
    validate_record(journal)
    sessions = [
        OwnerSession.from_payload(row["adaptive_exit_session"])
        for row in machine._state["legs"]
        if "adaptive_exit_session" in row
    ]
    if not any(
        session.binding_hash == binding.get("session_binding_sha256")
        and session.policy.policy_hash == binding.get("policy_hash")
        for session in sessions
    ):
        raise ValueError("pending_buy_projection_session_binding_invalid")
    route = str(leg.get("route") or getattr(machine.policy, "route", "SOR"))
    context = machine._episode_owner_context(
        leg=leg,
        action="NEW",
        ordinal=f"BUY:{route}:{leg.get('buy_submit_attempt_count')}",
    )
    order = OrderKey(leg.get("buy_order_date"), leg.get("buy_order_no"))
    root = machine.owner_registry.assert_owner(
        context=context, order_date=order.trading_date, broker_order_no=order.order_no
    )
    terminal = root.get("terminal_reconciliation")
    if (
        binding.get("context") != asdict(context)
        or binding.get("order") != asdict(order)
        or binding.get("intent_id") != root["intent_id"]
        or binding.get("quantity") != leg.get("quantity")
        or binding.get("route") != route
        or binding.get("symbol") != machine.policy.symbol
        or receipt.get("order") != asdict(order)
        or receipt.get("intent_id") != root["intent_id"]
        or root["intent_id"] != leg.get("buy_owner_registry_intent_id")
        or root.get("client_intent_id") != context.client_intent_id
        or root.get("quantity") != leg.get("quantity")
        or root.get("route") != route
        or root.get("symbol") != machine.policy.symbol
        or root.get("action") != "NEW"
        or root.get("side") != "BUY"
        or root.get("state") != "ORDER_TERMINAL"
        or root.get("filled_qty") != receipt.get("filled_qty")
        or receipt.get("filled_qty") != leg.get("buy_filled_qty")
        or (receipt.get("fill_price") or 0) != leg.get("fill_price")
        or not isinstance(terminal, dict)
        or terminal.get("source_contract")
        != "machine_adaptive_exit_buy_dated_current_v1"
        or receipt.get("registry_terminal_sha256") != canonical_sha256(terminal)
    ):
        raise ValueError("pending_buy_projection_root_proof_invalid")
    child_key = receipt.get("cancel_order")
    children = [
        row
        for row in machine.owner_registry.position_intents(
            context=context, symbol=machine.policy.symbol
        )
        if row.get("order_date") == order.trading_date
        and row.get("original_order_no") == order.order_no
    ]
    if child_key is None:
        if (
            children
            or receipt.get("schema") != "episode_adaptive_sibling_full_buy_v1"
            or root.get("filled_qty") != root["quantity"]
            or root.get("canceled_qty", 0)
        ):
            raise ValueError("pending_buy_projection_full_proof_invalid")
        return
    proof = root.get("terminal_cancel_reconciliation")
    if (
        len(children) != 1
        or not isinstance(proof, dict)
        or child_key
        != {
            "trading_date": order.trading_date,
            "order_no": children[0].get("broker_order_no"),
        }
        or receipt.get("schema") != "episode_adaptive_sibling_cancelled_buy_v1"
        or children[0].get("state") != "ORDER_TERMINAL"
        or children[0].get("side") != "BUY"
        or children[0].get("action") != "CANCEL"
        or children[0].get("authority_policy_id") != FAMILY
        or children[0].get("authority_policy_hash") != binding.get("policy_hash")
        or children[0].get("quantity") != journal.get("cancel_quantity")
        or children[0].get("terminal_cancel_reconciliation") != proof
        or proof.get("source_contract")
        != "machine_adaptive_exit_buy_terminal_cancel_dated_current_v1"
        or proof.get("filled_qty") != root["filled_qty"]
        or proof.get("confirmed_qty") != root.get("canceled_qty")
        or root["quantity"] != root["filled_qty"] + root.get("canceled_qty", 0)
        or receipt.get("registry_cancel_sha256") != canonical_sha256(proof)
    ):
        raise ValueError("pending_buy_projection_cancel_proof_invalid")


def step_pending_buy(machine, now, session):
    """None means no owned pending work; a string retains this manager."""
    legs = [leg for leg in machine._state["legs"] if "adaptive_exit_session" not in leg]
    work = []
    for leg in legs:
        if KEY in leg:
            require_durable_recovery_state(machine, leg, KEY)
        if KEY in leg and not isinstance(leg[KEY], dict):
            raise ValueError("pending_buy_journal_binding_invalid")
        if leg.get(KEY, {}).get("phase") == "PROJECTED":
            validate_projection(machine, leg)
        elif leg.get("status") == "BUY_OPEN" or KEY in leg:
            work.append(leg)
        elif isinstance(leg.get("adaptive_sibling_full_buy_receipt"), dict):
            validate_projection(machine, leg)
    if not work:
        return None
    services = getattr(machine.adaptive_exit_services, "pending_buy", None)
    if not isinstance(services, EpisodePendingBuyServices):
        if any(KEY in leg for leg in work):
            return "pending_buy_services_missing"
        return None  # Existing natural full-fill path is still read-only.
    if len(work) != 1:
        raise ValueError("pending_buy_independent_sibling_required")
    return _PendingBuy(machine, work[0], session, services, now).step()


class _PendingBuy:
    def __init__(self, machine, leg, session, services, now):
        self.terminal_recovery = None
        self.m, self.leg, self.session, self.services, self.now = (
            machine,
            leg,
            session,
            services,
            now,
        )
        self.now_ms = int(now.timestamp() * 1000)
        self.initial_ordinary_sha256 = _ordinary(leg)
        route = str(leg.get("route") or getattr(machine.policy, "route", "SOR"))
        attempt = leg.get("buy_submit_attempt_count")
        self.context = machine._episode_owner_context(
            leg=leg, action="NEW", ordinal=f"BUY:{route}:{attempt}"
        )
        self.order = OrderKey(leg.get("buy_order_date"), leg.get("buy_order_no"))
        self.row = machine.owner_registry.assert_owner(
            context=self.context,
            order_date=self.order.trading_date,
            broker_order_no=self.order.order_no,
        )
        if (
            self.order.trading_date != now.date().isoformat()
            or self.order.trading_date != machine._state["trade_date"]
            or type(attempt) is not int
            or attempt <= 0
            or self.row.get("client_intent_id") != self.context.client_intent_id
            or self.row.get("intent_id") != leg.get("buy_owner_registry_intent_id")
            or self.row.get("action") != "NEW"
            or self.row.get("side") != "BUY"
            or self.row.get("quantity") != leg.get("quantity")
            or self.row.get("route") != route
            or self.row.get("symbol") != machine.policy.symbol
            or self.row.get("state") not in {"ORDER_BOUND", "ORDER_TERMINAL"}
            or leg.get("target_order_no")
            or any(
                leg.get(k)
                for k in (
                    "buy_cancel_requested",
                    "buy_cancel_attempt_count",
                    "buy_cancel_order_no",
                    "buy_cancel_owner_registry_intent_id",
                    "buy_cancel_ambiguous",
                    "buy_cancel_terminal_failure",
                )
            )
        ):
            raise ValueError("pending_buy_original_leg_binding_required")
        self.binding = {
            "context": asdict(self.context),
            "order": asdict(self.order),
            "intent_id": self.row["intent_id"],
            "symbol": machine.policy.symbol,
            "route": route,
            "quantity": leg["quantity"],
            "session_binding_sha256": session.binding_hash,
            "policy_hash": session.policy.policy_hash,
            "confirmation_timeout_ms": services.confirmation_timeout_ms,
        }
        self.journal = deepcopy(leg.get(KEY))
        if self.journal is not None:
            if (
                not isinstance(self.journal, dict)
                or self.journal.get("schema") != SCHEMA
                or self.journal.get("canonical_sha256")
                != canonical_sha256(self.journal)
                or self.journal.get("binding") != self.binding
                or self.journal.get("ordinary_sha256") != _ordinary(leg)
                or self.journal.get("phase")
                not in {"INTENT_SAVED", "ACK_SAVED", "SPENT_UNRESOLVED"}
                or type(self.journal.get("created_at_ms")) is not int
                or self.journal.get("deadline_ms")
                != self.journal["created_at_ms"] + services.confirmation_timeout_ms
                or not 0 < self.journal["created_at_ms"] <= self.now_ms
                or not isinstance(self.journal.get("reason"), dict)
                or self.journal["reason"].get("reason")
                not in {"partial_fill_remainder", "entry_validity_expired"}
                or type(self.journal.get("cancel_quantity")) is not int
                or not 0 < self.journal["cancel_quantity"] <= leg["quantity"]
                or type(self.journal.get("observed_filled_qty")) is not int
                or self.journal["observed_filled_qty"] < 0
                or self.journal["observed_filled_qty"] + self.journal["cancel_quantity"]
                != leg["quantity"]
                or self.journal.get("action_id") != canonical_sha256(self.binding)
            ):
                raise ValueError("pending_buy_journal_binding_invalid")
        self.reader = None
        if self.journal is not None:
            validate_record(self.journal)

    def request(self):
        return {
            "schema": SCHEMA,
            "binding": deepcopy(self.binding),
            "action": (
                "INSPECT_TERMINAL_RECOVERY"
                if self.terminal_recovery
                else "CANCEL_BUY" if self.journal else "INSPECT_BUY"
            ),
            "journal": deepcopy(self.journal),
        }

    def authorized(self):
        ordinary = (
            self.journal["ordinary_sha256"]
            if self.journal
            else self.initial_ordinary_sha256
        )

        def timely():
            if self.terminal_recovery is not None:
                return self.terminal_recovery.allowed()
            return (
                not self.journal
                or (self.reader._transport.now_ms() if self.reader else self.now_ms)
                < self.journal["deadline_ms"]
            )

        def current_leg():
            return any(row is self.leg for row in self.m._state.get("legs", []))

        return (
            timely()
            and current_leg()
            and self.m._adaptive_authority_current()
            and getattr(self.m.adaptive_exit_services, "pending_buy", None)
            is self.services
            and ordinary == _ordinary(self.leg)
            and self.services.authorize(self.request()) is True
            and self.m._adaptive_authority_current()
            and ordinary == _ordinary(self.leg)
            and timely()
            and current_leg()
        )

    def save(self, journal):
        if not self.authorized():
            raise PermissionError("pending_buy_original_owner_guard_required")
        prior = deepcopy(self.m._state)
        journal = deepcopy(journal)
        journal["canonical_sha256"] = canonical_sha256(journal)
        self.leg[KEY] = journal
        try:
            self.m._save()
        except BaseException:
            self.m._state = prior
            raise
        self.journal = journal

    def write_guard(self, request):
        return (
            self.terminal_recovery is None
            and type(request) is BuyCancelWrite
            and request.action == "CANCEL"
            and request.predecessor == self.order
            and request.policy_hash == self.binding["policy_hash"]
            and request.quantity == self.journal["cancel_quantity"]
            and request.action_id == self.journal["action_id"]
            and self.reader._transport.now_ms() < self.journal["deadline_ms"]
            and self.authorized()
            and self.leg[KEY] == self.journal
            and next(
                leg
                for leg in self.m._load_state()["legs"]
                if leg["leg_id"] == self.leg["leg_id"]
            )
            == self.leg
        )

    def build_reader(self):
        if not self.authorized():
            raise PermissionError("pending_buy_original_owner_guard_required")
        transport = self.m.gateway.adaptive_exit_adapter(
            registry=self.m.owner_registry,
            context=self.context,
            policy_hash=self.session.policy.policy_hash,
            write_guard=lambda _: False,
        )
        if (
            not isinstance(transport, RegisteredSellAdapter)
            or transport.context != self.context
            or transport.registry is not self.m.owner_registry
            or transport.symbol != self.binding["symbol"]
            or self.binding["route"] not in transport.routes
            or transport.policy_hash != self.binding["policy_hash"]
        ):
            raise ValueError("pending_buy_adapter_binding_invalid")
        self.reader = RegisteredBuyCancelAdapter(
            post=transport.post,
            registry=transport.registry,
            context=self.context,
            symbol=transport.symbol,
            routes=transport.routes,
            policy_hash=transport.policy_hash,
            maximum_quantity=transport.maximum_quantity,
            require_write_authority=transport.require_write_authority,
            max_snapshot_age_ms=self.session.policy.max_quote_age_ms,
            write_guard=self.write_guard,
            now_ms=transport.now_ms,
        )

    def step(self):
        if self.journal and (
            self.now_ms >= self.journal["deadline_ms"] or RECOVERY_KEY in self.journal
        ):
            return recover(self)
        self.build_reader()
        return self._step_with_reader()

    def _step_with_reader(self, *, terminal_only=False):
        registry = self.m.owner_registry
        child = registry.intent_for_client(
            context=replace(
                self.context, client_intent_id=self.reader.client_id(self.order)
            )
        )
        siblings = [
            r
            for r in registry.position_intents(
                context=self.context, symbol=self.binding["symbol"]
            )
            if r.get("original_order_no") == self.order.order_no
            and r.get("order_date") == self.order.trading_date
        ]
        if any(child is None or r["intent_id"] != child["intent_id"] for r in siblings):
            return "pending_buy_legacy_cancel_requires_owner_recovery"
        if child:
            if not self.journal or (
                child.get("action") != "CANCEL"
                or child.get("side") != "BUY"
                or child.get("quantity") != self.journal["cancel_quantity"]
                or child.get("authority_policy_id") != FAMILY
                or child.get("authority_policy_hash") != self.binding["policy_hash"]
            ):
                return "pending_buy_spent_intent_binding_requires_recovery"
            if child.get("state") not in {
                "ORDER_BOUND",
                "ORDER_TERMINAL",
            } or not child.get("broker_order_no"):
                return "pending_buy_spent_intent_requires_recovery"
            key = OrderKey(self.order.trading_date, child["broker_order_no"])
            result = self.reader.reconcile_priced_terminal_cancel(
                self.order, key, guard=self.authorized
            )
            if not result.source_ok:
                return "pending_buy_terminal_source_wait:" + result.error
            return self.project(result, key)
        if self.journal and self.journal["phase"] != "INTENT_SAVED":
            return "pending_buy_spent_intent_missing_requires_recovery"
        if terminal_only:
            result = self.reader.reconcile_priced_full_buy(
                self.order, guard=self.authorized
            )
            if not result.source_ok:
                return "terminal_recovery_full_source_wait:" + result.error
            return self.project(result, None)
        snapshot = self.reader.snapshot(self.order)
        if not snapshot.source_ok:
            return "pending_buy_source_wait:" + snapshot.error
        if snapshot.terminal:
            if snapshot.filled_qty == self.binding["quantity"]:
                if not self.authorized():
                    raise PermissionError("pending_buy_original_owner_guard_required")
                if not self.journal:
                    self.m._recover_adaptive_full_buy_siblings(self.now, self.session)
                    return "sibling_full_buy_reconciled_original_target_pending"
                result = self.reader.reconcile_priced_full_buy(
                    self.order, guard=self.authorized
                )
                if not result.source_ok:
                    return "pending_buy_full_source_wait:" + result.error
                return self.project(result, None)
            return "pending_buy_unconfirmed_terminal_requires_recovery"
        reason = self.m._adaptive_pending_buy_cancel_reason(
            self.now, self.leg, snapshot
        )
        if reason is None:
            if not self.authorized():
                raise PermissionError("pending_buy_original_owner_guard_required")
            return "pending_buy_original_validity_wait"
        if not self.authorized():
            raise PermissionError("pending_buy_original_owner_guard_required")
        old = self.journal
        journal = {
            "schema": SCHEMA,
            "binding": self.binding,
            "ordinary_sha256": _ordinary(self.leg),
            "phase": "INTENT_SAVED",
            "created_at_ms": old["created_at_ms"] if old else self.now_ms,
            "deadline_ms": (
                old["deadline_ms"]
                if old
                else self.now_ms + self.services.confirmation_timeout_ms
            ),
            "action_id": old["action_id"] if old else canonical_sha256(self.binding),
            "cancel_quantity": snapshot.remaining_qty,
            "observed_filled_qty": snapshot.filled_qty,
            "source_sha256": snapshot.receipt_hash,
            "reason": reason,
        }
        if old and snapshot.filled_qty < old["observed_filled_qty"]:
            return "pending_buy_source_fill_regression"
        self.save(journal)
        if not self.authorized():
            raise PermissionError("pending_buy_original_owner_guard_required")
        ack = self.reader.cancel_owned_buy(
            self.order,
            quantity=journal["cancel_quantity"],
            action_id=journal["action_id"],
        )
        self.save(
            {
                **self.journal,
                "phase": "ACK_SAVED" if ack.accepted else "SPENT_UNRESOLVED",
                "cancel_order": asdict(ack.order) if ack.order else None,
                "ack_receipt_sha256": ack.receipt_hash,
            }
        )
        return "pending_buy_cancel_confirmation_wait"

    def project(self, result, cancel_order):
        if not self.authorized():
            raise PermissionError("pending_buy_original_owner_guard_required")
        nxt_zero = result.filled_qty == 0 and self.binding["route"] == "NXT"
        if nxt_zero and not callable(
            getattr(getattr(self, "m", None), "_adaptive_zero_buy_handoff", None)
        ):
            return "pending_buy_zero_fill_original_nxt_fallback_handoff_required"
        receipt = {
            "schema": (
                "episode_adaptive_sibling_cancelled_buy_v1"
                if cancel_order
                else "episode_adaptive_sibling_full_buy_v1"
            ),
            "order": asdict(self.order),
            "intent_id": self.binding["intent_id"],
            "source_sha256": result.receipt_hash,
            "observed_at_ms": result.observed_at_ms,
            "filled_qty": result.filled_qty,
            "fill_price": result.fill_price,
            "original_target_price": (
                self.m.policy.target_price(result.fill_price)
                if result.filled_qty
                else None
            ),
            "cancel_order": asdict(cancel_order) if cancel_order else None,
            "realized_pnl_status": "unreconciled_exact_fill_cost_required",
        }
        root = self.m.owner_registry.assert_owner(
            context=self.context,
            order_date=self.order.trading_date,
            broker_order_no=self.order.order_no,
        )
        receipt["registry_terminal_sha256"] = canonical_sha256(
            root.get("terminal_reconciliation")
        )
        receipt["registry_cancel_sha256"] = (
            canonical_sha256(root.get("terminal_cancel_reconciliation"))
            if cancel_order
            else None
        )
        receipt["canonical_sha256"] = canonical_sha256(receipt)
        prior = deepcopy(self.m._state)
        record_first_fill_observation(
            self.leg,
            previous_filled_qty=self.leg["buy_filled_qty"],
            filled_qty=result.filled_qty,
            observed_at=self.now.isoformat(),
        )
        self.leg.update(
            status="POSITION_OPEN" if result.filled_qty else "NO_FILL",
            position_qty=result.filled_qty,
            buy_filled_qty=result.filled_qty,
            fill_price=result.fill_price or 0,
            last_buy_reconciled_at=self.now.isoformat(),
            last_buy_remaining_qty=0,
            last_buy_reconcile_source_ok=True,
            adaptive_sibling_full_buy_receipt=receipt,
        )
        journal = {**self.journal, "phase": "PROJECTED", "terminal_receipt": receipt}
        journal["canonical_sha256"] = canonical_sha256(journal)
        self.leg[KEY] = journal
        try:
            validate_projection(self.m, self.leg)
            if nxt_zero:
                self.m._adaptive_zero_buy_handoff(self.now, self.leg)
            self.m._sync_aggregate()
            self.m._save()
        except BaseException:
            self.m._state = prior
            raise
        if nxt_zero:
            return "pending_buy_terminal_sor_fallback_prepared"
        return (
            "pending_buy_terminal_original_target_pending"
            if result.filled_qty
            else "pending_buy_terminal_no_fill"
        )
