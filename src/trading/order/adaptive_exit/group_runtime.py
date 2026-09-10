"""Opt-in shared-target allocation and reconciliation, not a SELL executor.

One original-owner lock and one durable slot per account/dated target own this
coordinator. Allocation must be explicitly approved and frozen BEFORE cancel.
The owner supplies its existing atomic/fsynced store; a successful callback
alone is insufficient (read-back is checked). No launcher enrolls this class.
No broker write, implicit FIFO, synthetic lot-level realized PnL or new policy
approval is provided here. Runner SELL/TTL/terminal remains a separate consumer.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from datetime import datetime

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.owner_custody_registry import broker_account_key
from .broker import FAMILY, KST, RegisteredSellAdapter
from .models import positive_int
from .reducer import OrderKey
from .target_group import TargetGroup, _digest

RULE = "nonrunner_first_then_runner_in_declared_lot_order_v1"
SCHEMA = "machine_adaptive_exit_group_coordinator_v1"


@dataclass(frozen=True)
class RunnerAllocation:
    group_hash: str
    policy_hash: str
    approval_receipt_hash: str
    rule: str
    runner_lot_ids: tuple[str, ...]
    lot_order: tuple[str, ...]

    def validate(self, group):
        group.validate()
        ids = {r[0] for r in group.lots}
        if (
            self.group_hash != group.to_payload()["canonical_sha256"]
            or not all(
                _digest(v) for v in (self.policy_hash, self.approval_receipt_hash)
            )
            or self.rule != RULE
            or any(
                not isinstance(v, tuple)
                or any(not isinstance(x, str) or not x for x in v)
                or len(v) != len(set(v))
                for v in (self.runner_lot_ids, self.lot_order)
            )
            or not set(self.runner_lot_ids) < ids
            or not self.runner_lot_ids
            or set(self.lot_order) != ids
        ):
            raise ValueError("group_explicit_frozen_allocation_required")

    def balances(self, group, target_filled_qty):
        """Deterministic owner BOOK allocation, never broker BUY-lot labels."""
        self.validate(group)
        if (
            type(target_filled_qty) is not int
            or not 0 <= target_filled_qty <= group.quantity
        ):
            raise ValueError("group_target_fill_invalid")
        quantities = {r[0]: r[2] for r in group.lots}
        order = tuple(
            x for x in self.lot_order if x not in self.runner_lot_ids
        ) + tuple(x for x in self.lot_order if x in self.runner_lot_ids)
        left, rows = target_filled_qty, {}
        for lot in order:
            filled = min(left, quantities[lot])
            left -= filled
            rows[lot] = {
                "lot_id": lot,
                "admitted_qty": quantities[lot],
                "target_book_filled_qty": filled,
                "book_open_qty": quantities[lot] - filled,
                "runner": lot in self.runner_lot_ids,
            }
        return [rows[x] for x in self.lot_order]


class GroupCoordinator:
    """Freeze -> bind an existing cancel -> consume exact partial-cancel proof.

    load_record(key) and save_record(key, expected_hash, payload) MUST use the
    original owner's durable atomic store under the SAME lifecycle lock, shared
    by every group and single-lot manager. authorize_binding verifies the real
    approval/enrollment and excludes another manager for this target. owner_guard
    verifies no pending BUY/unknown inventory or manual/operator conflict.
    Callbacks are deliberately required; hashes and source-only reports are not
    authorization. Missing/rejected/ambiguous cancel is recovery, never resend.
    """

    def __init__(
        self,
        *,
        group: TargetGroup,
        allocation: RunnerAllocation,
        adapter: RegisteredSellAdapter,
        max_snapshot_age_ms: int,
        load_record,
        save_record,
        lock_held,
        authorize_binding,
        owner_guard,
    ):
        allocation.validate(group)
        if (
            not isinstance(adapter, RegisteredSellAdapter)
            or adapter.policy_hash != allocation.policy_hash
            or adapter.symbol != group.scope.symbol
            or group.scope.route not in adapter.routes
            or adapter.context.owner_type
            != ("widget_auto_trade" if group.scope.owner == "widget" else "episode")
            or not positive_int(max_snapshot_age_ms)
            or any(
                not callable(x)
                for x in (
                    load_record,
                    save_record,
                    lock_held,
                    authorize_binding,
                    owner_guard,
                )
            )
        ):
            raise ValueError("group_coordinator_binding_invalid")
        self.group, self.allocation, self.adapter = group, allocation, adapter
        self.max_age = max_snapshot_age_ms
        self.load_record, self.save_record = load_record, save_record
        self.lock_held, self.authorize_binding, self.owner_guard = (
            lock_held,
            authorize_binding,
            owner_guard,
        )
        self.binding = {
            "group_hash": allocation.group_hash,
            "allocation": asdict(allocation),
            "context": asdict(adapter.context),
            "account_hash": canonical_sha256({"account": adapter.account_key}),
            "max_snapshot_age_ms": max_snapshot_age_ms,
        }
        self.binding_hash = canonical_sha256(self.binding)
        # Not keyed by policy/lot: a changed policy cannot create a second slot.
        self.key = canonical_sha256(
            {"account": self.binding["account_hash"], "target": asdict(group.target)}
        )
        self.cancel_client_id = FAMILY + ":group-cancel:" + self.binding_hash

    def _authorize(self):
        self.allocation.validate(self.group)
        current_binding = {
            "group_hash": self.allocation.group_hash,
            "allocation": asdict(self.allocation),
            "context": asdict(self.adapter.context),
            "account_hash": canonical_sha256({"account": self.adapter.account_key}),
            "max_snapshot_age_ms": self.max_age,
        }
        if (
            canonical_sha256(current_binding) != self.binding_hash
            or canonical_sha256(self.binding) != self.binding_hash
            or self.adapter.policy_hash != self.allocation.policy_hash
            or self.adapter.symbol != self.group.scope.symbol
            or self.group.scope.route not in self.adapter.routes
        ):
            raise ValueError("group_frozen_adapter_binding_changed")
        if (
            self.lock_held() is not True
            or self.adapter.account_key != broker_account_key(require_explicit=True)
            or self.authorize_binding(deepcopy(self.binding)) is not True
            or self.owner_guard(deepcopy(self.binding)) is not True
        ):
            raise PermissionError("group_owner_lock_approval_and_custody_required")
        now = self.adapter.now_ms()
        if (
            not positive_int(now)
            or datetime.fromtimestamp(now / 1000, KST).date().isoformat()
            != self.group.target.trading_date
        ):
            raise ValueError("group_cross_date_requires_owner_recovery")

    def _row(self, order):
        return self.adapter.registry.assert_owner(
            context=self.adapter.context,
            order_date=order.trading_date,
            broker_order_no=order.order_no,
        )

    def _target(self):
        self._authorize()
        target = self._row(self.group.target)
        if any(
            target.get(k) != v
            for k, v in {
                "symbol": self.group.scope.symbol,
                "route": self.group.scope.route,
                "side": "SELL",
                "action": "NEW",
                "quantity": self.group.quantity,
            }.items()
        ):
            raise ValueError("group_target_registry_binding_conflict")
        for _, order, qty, _, _ in self.group.lots:
            buy = self._row(order)
            if any(
                buy.get(k) != v
                for k, v in {
                    "side": "BUY",
                    "action": "NEW",
                    "quantity": qty,
                    "filled_qty": qty,
                    "symbol": self.group.scope.symbol,
                    "route": self.group.scope.route,
                }.items()
            ):
                raise ValueError("group_full_buy_registry_binding_conflict")
        return target

    def _read(self):
        self._authorize()
        raw = self.load_record(self.key)
        if raw is None:
            return None
        return self._validate_state(deepcopy(raw))

    def _validate_state(self, raw):
        fields = {
            "schema",
            "binding_hash",
            "initial_filled_qty",
            "requested_qty",
            "target_intent_id",
            "freeze_source_hash",
            "frozen_at_ms",
            "phase",
            "cancel_order",
            "release",
            "canonical_sha256",
        }
        if (
            not isinstance(raw, dict)
            or set(raw) != fields
            or raw.get("schema") != SCHEMA
            or raw.get("binding_hash") != self.binding_hash
            or raw.get("canonical_sha256") != canonical_sha256(raw)
            or not _digest(raw.get("freeze_source_hash"))
            or not positive_int(raw.get("frozen_at_ms"))
            or not 0 < raw["frozen_at_ms"] <= self.adapter.now_ms()
            or datetime.fromtimestamp(raw["frozen_at_ms"] / 1000, KST)
            .date()
            .isoformat()
            != self.group.target.trading_date
            or not isinstance(raw.get("target_intent_id"), str)
            or not raw["target_intent_id"]
            or raw.get("phase")
            not in {"ALLOCATION_FROZEN", "CANCEL_BOUND", "RELEASE_RECONCILED"}
        ):
            raise ValueError("group_saved_binding_or_schema_conflict")
        rows = self.allocation.balances(self.group, raw["initial_filled_qty"])
        requested = sum(r["book_open_qty"] for r in rows if r["runner"])
        if (
            not positive_int(raw["requested_qty"])
            or raw["requested_qty"] != requested
            or not requested < self.group.quantity - raw["initial_filled_qty"]
        ):
            raise ValueError("group_partial_release_requires_live_nonrunner_remainder")
        if raw["phase"] == "ALLOCATION_FROZEN":
            if raw["cancel_order"] is not None or raw["release"] is not None:
                raise ValueError("group_frozen_state_conflict")
        else:
            order = raw["cancel_order"]
            if (
                not isinstance(order, dict)
                or set(order) != {"trading_date", "order_no"}
                or order["trading_date"] != self.group.target.trading_date
                or not isinstance(order["order_no"], str)
                or len(order["order_no"]) != 7
                or not order["order_no"].isascii()
                or not order["order_no"].isdigit()
                or int(order["order_no"]) == 0
                or order == asdict(self.group.target)
            ):
                raise ValueError("group_cancel_identity_invalid")
            if (raw["phase"] == "CANCEL_BOUND") != (raw["release"] is None):
                raise ValueError("group_release_phase_conflict")
            if raw["release"] is not None:
                self._validate_release(raw)
        return raw

    def _validate_release(self, raw):
        r = raw["release"]
        if not isinstance(r, dict) or set(r) != {
            "target_filled_qty",
            "target_reserved_qty",
            "runner_released_qty",
            "observed_at_ms",
            "snapshot_hash",
            "cancel_proof_hash",
            "target_event_hash",
            "cancel_event_hash",
            "book_lots",
            "actual_lot_fill_attribution",
            "sell_authority",
            "realized_pnl",
        }:
            raise ValueError("group_release_schema_invalid")
        if (
            any(
                type(r[k]) is not int or r[k] < 0
                for k in (
                    "target_filled_qty",
                    "target_reserved_qty",
                    "runner_released_qty",
                )
            )
            or r["target_filled_qty"] < raw["initial_filled_qty"]
            or r["target_reserved_qty"] < 0
            or r["runner_released_qty"] != raw["requested_qty"]
            or r["target_filled_qty"]
            + r["target_reserved_qty"]
            + r["runner_released_qty"]
            != self.group.quantity
            or not positive_int(r["observed_at_ms"])
            or r["observed_at_ms"] < raw["frozen_at_ms"]
            or r["observed_at_ms"] > self.adapter.now_ms()
            or any(
                not _digest(r[k])
                for k in (
                    "snapshot_hash",
                    "cancel_proof_hash",
                    "target_event_hash",
                    "cancel_event_hash",
                )
            )
            or canonical_sha256({"rows": r["book_lots"]})
            != canonical_sha256(
                {"rows": self.allocation.balances(self.group, r["target_filled_qty"])}
            )
            or r["actual_lot_fill_attribution"] is not None
            or r["realized_pnl"] is not None
            or r["sell_authority"] is not False
        ):
            raise ValueError("group_release_conservation_or_authority_conflict")

    def _save(self, previous, candidate):
        self._authorize()
        expected = previous["canonical_sha256"] if previous else None
        current = self._read()
        if (current["canonical_sha256"] if current else None) != expected:
            raise ValueError("group_coordinator_generation_changed")
        payload = deepcopy(candidate)
        payload["canonical_sha256"] = canonical_sha256(payload)
        self._validate_state(payload)
        self.save_record(self.key, expected, payload)
        saved = self._read()
        if saved is None or saved["canonical_sha256"] != payload["canonical_sha256"]:
            raise ValueError("group_durable_save_receipt_missing")
        return saved

    def _fresh(self, snapshot, start, *, allow_terminal=False):
        now = self.adapter.now_ms()
        if (
            snapshot.source_ok is not True
            or snapshot.order != self.group.target
            or (
                snapshot.terminal is not False
                and not (allow_terminal and snapshot.terminal is True)
            )
            or not 0 <= now - start <= self.max_age
            or not start <= snapshot.observed_at_ms <= now
            or datetime.fromtimestamp(now / 1000, KST).date().isoformat()
            != self.group.target.trading_date
        ):
            raise ValueError("group_source_stale_or_requires_owner_recovery")
        self._authorize()

    def _cancel(self):
        return self.adapter.registry.intent_for_client(
            context=replace(
                self.adapter.context, client_intent_id=self.cancel_client_id
            )
        )

    def freeze(self):
        """Persist approved allocation once; never retrofit an existing cancel."""
        existing = self._read()
        if existing is not None:
            return existing
        target = self._target()
        if target.get("canceled_qty", 0) != 0 or self._cancel() is not None:
            raise ValueError("group_cannot_freeze_after_cancel")
        start = self.adapter.now_ms()
        snapshot = self.adapter.reconcile_owned_sell(self.group.target)
        self._fresh(snapshot, start)
        target = self._target()
        requested = sum(
            r["book_open_qty"]
            for r in self.allocation.balances(self.group, snapshot.filled_qty)
            if r["runner"]
        )
        if (
            target.get("state") != "ORDER_BOUND"
            or target.get("canceled_qty", 0) != 0
            or target.get("filled_qty", 0) != snapshot.filled_qty
            or snapshot.filled_qty + snapshot.remaining_qty != self.group.quantity
            or not 0 < requested < snapshot.remaining_qty
            or self._cancel() is not None
        ):
            raise ValueError("group_partial_release_requires_live_nonrunner_remainder")
        return self._save(
            None,
            {
                "schema": SCHEMA,
                "binding_hash": self.binding_hash,
                "initial_filled_qty": snapshot.filled_qty,
                "requested_qty": requested,
                "target_intent_id": target["intent_id"],
                "freeze_source_hash": snapshot.receipt_hash,
                "frozen_at_ms": snapshot.observed_at_ms,
                "phase": "ALLOCATION_FROZEN",
                "cancel_order": None,
                "release": None,
            },
        )

    def bind_cancel(self):
        """Discover only the frozen deterministic cancel intent; never send it."""
        state = self._read()
        if state is None:
            raise ValueError("group_allocation_must_be_persisted_before_cancel")
        target, cancel = self._target(), self._cancel()
        if target.get("intent_id") != state["target_intent_id"] or cancel is None:
            raise ValueError("group_exact_cancel_intent_missing")
        if any(
            cancel.get(k) != v
            for k, v in {
                "action": "CANCEL",
                "side": "SELL",
                "quantity": state["requested_qty"],
                "symbol": self.group.scope.symbol,
                "route": self.group.scope.route,
                "original_order_no": self.group.target.order_no,
                "order_date": self.group.target.trading_date,
                "authority_policy_id": FAMILY,
                "authority_policy_hash": self.allocation.policy_hash,
            }.items()
        ) or cancel.get("state") not in {"ORDER_BOUND", "ORDER_TERMINAL"}:
            raise ValueError("group_cancel_ambiguous_rejected_or_binding_conflict")
        order = {
            "trading_date": cancel["order_date"],
            "order_no": cancel.get("broker_order_no"),
        }
        if state["phase"] != "ALLOCATION_FROZEN":
            if state["cancel_order"] != order:
                raise ValueError("group_cancel_changed")
            return state
        return self._save(
            state, state | {"phase": "CANCEL_BOUND", "cancel_order": order}
        )

    def reconcile(self):
        """Consume the existing adapter + atomic registry proof, not an ACK.

        RELEASE_RECONCILED is a historical capacity receipt, not current free
        inventory. A future SELL consumer must recheck registry reservations,
        price, TTL and all guards. This method has no order-writing method.
        """
        state = self.bind_cancel()
        order = OrderKey(**state["cancel_order"])
        start = self.adapter.now_ms()
        snapshot = self.adapter.reconcile_partial_cancel(
            self.group.target, order, max_snapshot_age_ms=self.max_age
        )
        self._fresh(snapshot, start, allow_terminal=True)
        target, cancel = self._target(), self._row(order)
        proof = cancel.get("cancel_reconciliation")
        if (
            not isinstance(proof, dict)
            or any(
                proof.get(k) != v
                for k, v in {
                    "schema": "order_owner_partial_cancel_reconciliation_v1",
                    "source_contract": "machine_adaptive_exit_full_cancel_request_dated_current_v1",
                    "target_intent_id": state["target_intent_id"],
                    "cancel_intent_id": cancel["intent_id"],
                    "target_order_no": self.group.target.order_no,
                    "cancel_order_no": order.order_no,
                    "order_date": order.trading_date,
                    "confirmed_qty": state["requested_qty"],
                }.items()
            )
            or target.get("partial_cancel_reconciliation") != proof
            or target.get("state")
            != ("ORDER_TERMINAL" if snapshot.terminal else "ORDER_BOUND")
            or cancel.get("state") != "ORDER_TERMINAL"
            or target.get("canceled_qty") != state["requested_qty"]
            or target.get("filled_qty") != snapshot.filled_qty
            or snapshot.filled_qty < state["initial_filled_qty"]
            or (
                state["release"] is not None
                and snapshot.filled_qty < state["release"]["target_filled_qty"]
            )
        ):
            raise ValueError("group_exact_partial_cancel_registry_proof_required")
        release = {
            "target_filled_qty": snapshot.filled_qty,
            "target_reserved_qty": snapshot.remaining_qty,
            "runner_released_qty": state["requested_qty"],
            "observed_at_ms": snapshot.observed_at_ms,
            "snapshot_hash": snapshot.receipt_hash,
            "cancel_proof_hash": canonical_sha256(proof),
            "target_event_hash": target["event_hash"],
            "cancel_event_hash": cancel["event_hash"],
            "book_lots": self.allocation.balances(self.group, snapshot.filled_qty),
            "actual_lot_fill_attribution": None,
            "sell_authority": False,
            "realized_pnl": None,
        }
        candidate = state | {"phase": "RELEASE_RECONCILED", "release": release}
        self._validate_release(candidate)
        if candidate == state:
            return state
        return self._save(state, candidate)
