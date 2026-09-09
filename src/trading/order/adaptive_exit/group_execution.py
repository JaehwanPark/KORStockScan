"""Opt-in first runner order/TTL execution after a frozen group allocation.

No policy, price, trailing trigger or numeric approval is invented here. The
original owner supplies a decision receipt and an independent action validator
that rechecks fresh executable depth and ALL safety guards before each write.
Action slots are durable before transport. Registry client IDs own recovery;
an ACK is never terminal and a runner terminal is never a group/episode flat.
The actual launcher, group decision producer and residual retry are not wired.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.tick_utils import get_tick_size
from .broker import FAMILY, SellWrite
from .group_runtime import GroupCoordinator
from .models import positive_int
from .reducer import OrderKey
from .target_group import _digest

SCHEMA = "machine_adaptive_exit_group_execution_action_v1"
KINDS = ("RELEASE_RUNNER", "SELL_RUNNER", "CANCEL_RUNNER_TTL")


@dataclass(frozen=True)
class RunnerBounds:
    sell_ttl_ms: int
    max_decision_age_ms: int
    max_unprotected_ms: int

    def __post_init__(self):
        if not all(positive_int(v) for v in asdict(self).values()):
            raise ValueError("explicit_runner_execution_bounds_required")


@dataclass(frozen=True)
class GroupAction:
    kind: str
    decision_receipt_hash: str
    source_hash: str
    observed_at_ms: int
    limit_price: int | None

    def __post_init__(self):
        if (
            self.kind not in KINDS
            or not _digest(self.decision_receipt_hash)
            or not _digest(self.source_hash)
            or not positive_int(self.observed_at_ms)
            or (self.kind != "SELL_RUNNER" and self.limit_price is not None)
            or (
                self.kind == "SELL_RUNNER"
                and (
                    not positive_int(self.limit_price)
                    or self.limit_price % get_tick_size(self.limit_price)
                )
            )
        ):
            raise ValueError("group_action_identity_or_limit_invalid")


class GroupRunnerExecutor:
    """One cancel, one runner limit SELL, one TTL cancel; no blind retry.

    coordinator_factory(write_guard) must construct a fresh adapter using THAT
    guard, plus the original owner's shared lock/atomic CAS store. Never mutate
    another port's adapter guard. authorize_action(binding, record, now) verifies
    actual per-lot decisions, the approved numeric envelope, fresh BBO for SELL,
    loss/price/quantity limits and all broker/account/manual/operator guards.
    Validation runs both before and after the exact intent's atomic reservation;
    it must recognize that reservation, without treating unrelated commitments
    as available or granting a second order. It must not itself submit orders.
    It is NOT an unconditional policy-file-exists check. No default is supplied.
    """

    def __init__(
        self,
        *,
        coordinator_factory,
        bounds: RunnerBounds,
        execution_approval_receipt_hash: str,
        authorize_action,
    ):
        if (
            not isinstance(bounds, RunnerBounds)
            or not _digest(execution_approval_receipt_hash)
            or not callable(authorize_action)
            or not callable(coordinator_factory)
        ):
            raise ValueError("group_execution_approval_services_required")
        self.bounds, self.authorize_action = bounds, authorize_action
        self._inflight = None
        self._write_guard = self._transport_guard
        self.coordinator = coordinator_factory(self._write_guard)
        c = self.coordinator
        if (
            not isinstance(c, GroupCoordinator)
            or c.adapter.write_guard is not self._write_guard
        ):
            raise ValueError("group_execution_adapter_guard_not_bound")
        self.binding = {
            "group_binding_hash": c.binding_hash,
            "bounds": asdict(bounds),
            "execution_approval_receipt_hash": execution_approval_receipt_hash,
            "supported_sell_attempts": 1,
        }
        self.binding_hash = canonical_sha256(self.binding)

    def _authorize(self):
        c = self.coordinator
        c._authorize()
        if (
            c.adapter.write_guard is not self._write_guard
            or self.binding["group_binding_hash"] != c.binding_hash
            or self.binding["bounds"] != asdict(self.bounds)
            or canonical_sha256(self.binding) != self.binding_hash
        ):
            raise ValueError("group_execution_frozen_binding_changed")

    def _key(self, kind):
        return canonical_sha256(
            {"group_slot": self.coordinator.key, "execution_kind": kind}
        )

    def _validate(self, record, kind):
        if (
            not isinstance(record, dict)
            or set(record)
            != {
                "schema",
                "binding_hash",
                "action",
                "predecessor",
                "quantity",
                "created_at_ms",
                "canonical_sha256",
            }
            or record.get("schema") != SCHEMA
            or record.get("binding_hash") != self.binding_hash
            or record.get("canonical_sha256") != canonical_sha256(record)
            or not positive_int(record.get("quantity"))
            or not positive_int(record.get("created_at_ms"))
        ):
            raise ValueError("group_execution_saved_action_invalid")
        action = GroupAction(**record["action"])
        order = OrderKey(**record["predecessor"])
        if (
            action.kind != kind
            or order.trading_date != self.coordinator.group.target.trading_date
            or not order.order_no.isascii()
            or len(order.order_no) != 7
            or not order.order_no.isdigit()
            or int(order.order_no) == 0
            or record["created_at_ms"] > self.coordinator.adapter.now_ms()
            or action.observed_at_ms > record["created_at_ms"]
            or (kind != "CANCEL_RUNNER_TTL" and order != self.coordinator.group.target)
        ):
            raise ValueError("group_execution_saved_identity_conflict")
        if kind != "CANCEL_RUNNER_TTL":
            frozen = self.coordinator._read()
            if (
                frozen is None
                or record["quantity"] != frozen["requested_qty"]
                or record["created_at_ms"] < frozen["frozen_at_ms"]
            ):
                raise ValueError("group_execution_frozen_quantity_conflict")
        else:
            sell = self._read("SELL_RUNNER")
            row = self._intent(sell) if sell else None
            if (
                row is None
                or row["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"}
                or order != OrderKey(row["order_date"], row["broker_order_no"])
                or record["quantity"] > sell["quantity"]
                or record["created_at_ms"]
                < sell["created_at_ms"] + self.bounds.sell_ttl_ms
            ):
                raise ValueError("group_execution_ttl_predecessor_conflict")
        return record

    def _read(self, kind):
        self._authorize()
        value = self.coordinator.load_record(self._key(kind))
        return self._validate(deepcopy(value), kind) if value is not None else None

    def _record(self, action, predecessor, quantity):
        self._authorize()
        old = self._read(action.kind)
        if old is not None:
            if (
                old["action"] != asdict(action)
                or old["predecessor"] != asdict(predecessor)
                or old["quantity"] != quantity
            ):
                raise ValueError("group_execution_action_is_immutable")
            return old
        raw = {
            "schema": SCHEMA,
            "binding_hash": self.binding_hash,
            "action": asdict(action),
            "predecessor": asdict(predecessor),
            "quantity": quantity,
            "created_at_ms": self.coordinator.adapter.now_ms(),
        }
        raw["canonical_sha256"] = canonical_sha256(raw)
        self._validate(raw, action.kind)
        self._action_allowed(raw)
        self.coordinator.save_record(self._key(action.kind), None, deepcopy(raw))
        saved = self._read(action.kind)
        if saved != raw:
            raise ValueError("group_execution_durable_save_missing")
        return saved

    def _action_allowed(self, record):
        self._authorize()
        now = self.coordinator.adapter.now_ms()
        if (
            not 0
            <= now - record["action"]["observed_at_ms"]
            <= self.bounds.max_decision_age_ms
            or self.authorize_action(deepcopy(self.binding), deepcopy(record), now)
            is not True
        ):
            raise PermissionError(
                "group_fresh_approved_action_and_full_safety_required"
            )

    def _client(self, kind, predecessor):
        if kind == "RELEASE_RUNNER":
            return self.coordinator.cancel_client_id
        if kind == "SELL_RUNNER":
            return self.coordinator.adapter._replacement_client_id(predecessor)
        return (
            FAMILY
            + ":group-runner-ttl:"
            + canonical_sha256(
                {"group": self.coordinator.key, "order": asdict(predecessor)}
            )
        )

    def _intent(self, record):
        c = self.coordinator
        kind, order = record["action"]["kind"], OrderKey(**record["predecessor"])
        row = c.adapter.registry.intent_for_client(
            context=replace(
                c.adapter.context, client_intent_id=self._client(kind, order)
            )
        )
        if row is not None and any(
            row.get(k) != v
            for k, v in {
                "side": "SELL",
                "action": "NEW" if kind == "SELL_RUNNER" else "CANCEL",
                "quantity": record["quantity"],
                "symbol": c.group.scope.symbol,
                "route": c.group.scope.route,
                "order_date": order.trading_date,
                "authority_policy_id": FAMILY,
                "authority_policy_hash": c.allocation.policy_hash,
                "original_order_no": "" if kind == "SELL_RUNNER" else order.order_no,
            }.items()
        ):
            raise ValueError("group_execution_registry_intent_conflict")
        return row

    def _transport_guard(self, request: SellWrite):
        if self._inflight is None:
            return False
        kind, digest = self._inflight
        record = self._read(kind)
        if record is None or record["canonical_sha256"] != digest:
            return False
        self._action_allowed(record)
        c, order = self.coordinator, OrderKey(**record["predecessor"])
        return (
            request.predecessor == order
            and request.action == ("NEW" if kind == "SELL_RUNNER" else "CANCEL")
            and request.quantity == record["quantity"]
            and request.limit_price == record["action"]["limit_price"]
            and request.context
            == replace(c.adapter.context, client_intent_id=self._client(kind, order))
            and request.route == c.group.scope.route
            and request.symbol == c.group.scope.symbol
            and request.policy_hash == c.allocation.policy_hash
        )

    def _send(self, record, fn):
        # A durable reservation, rejection or ambiguous ACK is NEVER resent.
        prior = self._intent(record)
        if prior is not None:
            return self._status(prior)
        self._action_allowed(record)
        if self._inflight is not None:
            raise ValueError("group_execution_reentrant_write")
        self._inflight = (record["action"]["kind"], record["canonical_sha256"])
        try:
            fn()
        finally:
            self._inflight = None
        row = self._intent(record)
        if row is None:
            raise ValueError("group_execution_registry_receipt_missing")
        return self._status(row)

    @staticmethod
    def _status(row):
        return {
            "status": "order_bound"
            if row["state"] in {"ORDER_BOUND", "ORDER_TERMINAL"}
            else "recovery_required",
            "registry_state": row["state"],
            "intent_id": row["intent_id"],
            "order_no": row.get("broker_order_no"),
            "group_terminal": False,
        }

    def request_release(self, action: GroupAction):
        if action.kind != "RELEASE_RUNNER":
            raise ValueError("group_release_action_required")
        c = self.coordinator
        frozen = c.freeze()
        if (
            frozen["phase"] != "ALLOCATION_FROZEN"
            and self._read("RELEASE_RUNNER") is None
        ):
            raise ValueError("group_execution_cannot_adopt_external_cancel")
        record = self._record(action, c.group.target, frozen["requested_qty"])
        return self._send(
            record,
            lambda: c.adapter.cancel_owned_sell(
                c.group.target,
                quantity=record["quantity"],
                action_id=c.cancel_client_id,
            ),
        )

    def sell_released(self, action: GroupAction):
        if action.kind != "SELL_RUNNER":
            raise ValueError("group_runner_sell_action_required")
        c = self.coordinator
        cancel_record = self._read("RELEASE_RUNNER")
        if cancel_record is None or self._intent(cancel_record) is None:
            raise ValueError("group_original_cancel_action_required")
        existing = self._read("SELL_RUNNER")
        if existing is not None and self._intent(existing) is not None:
            # Lost ACK recovery does not re-cancel/reconcile an already sold target.
            if existing["action"] != asdict(action):
                raise ValueError("group_execution_action_is_immutable")
            return self._status(self._intent(existing))
        state = c.reconcile()
        record = self._record(action, c.group.target, state["requested_qty"])
        return self._send(
            record,
            lambda: c.adapter.submit_partial_cancel_residual(
                c.group.target,
                OrderKey(**state["cancel_order"]),
                quantity=record["quantity"],
                limit_price=action.limit_price,
                action_id=self._client("SELL_RUNNER", c.group.target),
                max_snapshot_age_ms=c.max_age,
            ),
        )

    def reconcile_release(self):
        """Observe release without inventing a trailing signal or deadline reset.

        The request's durable creation time is a conservative exposure bound,
        not a fabricated broker cancellation timestamp. Expiry requests recovery;
        it does not grant a forced SELL or permission to loosen a price guard.
        """
        c = self.coordinator
        sell = self._read("SELL_RUNNER")
        if sell is not None and self._intent(sell) is not None:
            return {
                "status": "runner_submitted_use_runner_reconciliation",
                "group_terminal": False,
            }
        record = self._read("RELEASE_RUNNER")
        if record is None:
            return {"status": "runner_not_submitted", "group_terminal": False}
        base = {
            "group_terminal": False,
            "deadline_basis": "durable_release_request_created_at_ms",
            "recovery_deadline_ms": record["created_at_ms"]
            + self.bounds.max_unprotected_ms,
        }
        row = self._intent(record)
        if row is None or row["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"}:
            result = {"status": "release_action_requires_recovery"}
        else:
            try:
                state = c.reconcile()
                result = {
                    "status": "runner_released_awaiting_decision",
                    "runner_released_qty": state["release"]["runner_released_qty"],
                    "target_reserved_qty": state["release"]["target_reserved_qty"],
                    "release_receipt_hash": canonical_sha256(state["release"]),
                }
            except ValueError:
                # ACK without confirmation, source gap or conflicting quantity
                # cannot become free inventory. No silent retry/forced order.
                result = {"status": "release_source_gap_requires_recovery"}
        return (
            base
            | result
            | {
                "recovery_deadline_exceeded": c.adapter.now_ms()
                >= base["recovery_deadline_ms"],
            }
        )

    def poll_runner(self):
        """Fresh fill/terminal reconciliation; TTL cancels only the runner.

        First runner terminal leaves the original target/group manager alive.
        A terminal partial fill retains the residual owner and requests recovery;
        it does not become a completed profitable episode or a new BUY gate.
        """
        c = self.coordinator
        record = self._read("SELL_RUNNER")
        if record is None:
            return self.reconcile_release()
        row = self._intent(record)
        deadline = {
            "recovery_deadline_ms": record["created_at_ms"]
            + self.bounds.sell_ttl_ms
            + self.bounds.max_unprotected_ms,
            "recovery_deadline_exceeded": c.adapter.now_ms() - record["created_at_ms"]
            >= self.bounds.sell_ttl_ms + self.bounds.max_unprotected_ms,
        }
        if row is None or row["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"}:
            return deadline | {"status": "recovery_required", "group_terminal": False}
        order = OrderKey(row["order_date"], row["broker_order_no"])
        start = c.adapter.now_ms()
        snapshot = c.adapter.reconcile_owned_sell(order)
        now = c.adapter.now_ms()
        deadline["recovery_deadline_exceeded"] = now >= deadline["recovery_deadline_ms"]
        self._authorize()
        if (
            snapshot.source_ok is not True
            or snapshot.order != order
            or not 0 <= now - start <= c.max_age
            or not start <= snapshot.observed_at_ms <= now
            or not _digest(snapshot.receipt_hash)
            or type(snapshot.filled_qty) is not int
            or not 0 <= snapshot.filled_qty <= record["quantity"]
            or type(snapshot.remaining_qty) is not int
            or not 0
            <= snapshot.remaining_qty
            <= record["quantity"] - snapshot.filled_qty
            or snapshot.terminal is not (snapshot.remaining_qty == 0)
        ):
            return deadline | {
                "status": "source_gap_requires_recovery",
                "group_terminal": False,
            }
        remaining = record["quantity"] - snapshot.filled_qty
        if snapshot.terminal:
            fresh = self._intent(record)
            proof = fresh.get("terminal_reconciliation")
            if (
                not isinstance(proof, dict)
                or fresh["state"] != "ORDER_TERMINAL"
                or proof.get("filled_qty") != snapshot.filled_qty
                or proof.get("quantity") != record["quantity"]
                or proof.get("broker_order_no") != order.order_no
                or not _digest(proof.get("receipt_sha256"))
                or proof.get("schema") != "order_owner_terminal_reconciliation_v1"
                or proof.get("source_contract")
                != "machine_adaptive_exit_dated_current_v1"
                or any(
                    proof.get(k) != fresh.get(k)
                    for k in (
                        "account_key",
                        "intent_id",
                        "order_date",
                        "broker_order_no",
                        "owner_type",
                        "owner_id",
                        "position_id",
                        "client_intent_id",
                        "symbol",
                        "side",
                        "action",
                        "route",
                        "quantity",
                        "filled_qty",
                    )
                )
            ):
                raise ValueError("runner_exact_terminal_proof_required")
            return {
                "status": "runner_terminal"
                if remaining == 0
                else "runner_residual_requires_recovery",
                "runner_filled_qty": snapshot.filled_qty,
                "runner_remaining_qty": remaining,
                "terminal_proof_hash": canonical_sha256(proof),
                "group_terminal": False,
                "realized_pnl": None,
                "realized_pnl_status": "exact_costs_not_reconciled",
            }
        if now - record["created_at_ms"] < self.bounds.sell_ttl_ms:
            return {"status": "runner_working", "group_terminal": False}
        old_cancel = self._read("CANCEL_RUNNER_TTL")
        if old_cancel is None:
            action = GroupAction(
                "CANCEL_RUNNER_TTL",
                canonical_sha256(
                    {
                        "sell_action": record["canonical_sha256"],
                        "bounds": asdict(self.bounds),
                        "snapshot": snapshot.receipt_hash,
                    }
                ),
                snapshot.receipt_hash,
                snapshot.observed_at_ms,
                None,
            )
            old_cancel = self._record(action, order, snapshot.remaining_qty)
        result = self._send(
            old_cancel,
            lambda: c.adapter.cancel_owned_sell(
                order,
                quantity=old_cancel["quantity"],
                action_id=self._client("CANCEL_RUNNER_TTL", order),
            ),
        )
        return (
            result
            | deadline
            | {
                "status": "runner_cancel_pending"
                if result["status"] == "order_bound"
                else "recovery_required",
            }
        )
