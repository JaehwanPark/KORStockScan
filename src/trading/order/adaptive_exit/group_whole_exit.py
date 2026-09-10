"""Original-policy whole-target EXIT, superseding the pooled runner writer.

Original owner lock/CAS only; at most one root observation/action per step.
Bounded residual generations have fixed slots, positive cancel confirmations
and no resend of reserved/rejected/ambiguous intents. No launcher or authority
defaults: independent request, fresh market/depth and full safety services are
mandatory. Pending BUY closure requires a separately frozen exact owner census;
unknown/legacy/cross-date recovery is not silently adopted.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from datetime import datetime, time
from typing import Callable

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.tick_utils import get_tick_size
from .broker import FAMILY, KST, _hash
from .buy_cancel import BuyCancelWrite, RegisteredBuyCancelAdapter
from .group_pending_buy import validate_pending_buys
from .group_settlement import closed_census
from .models import positive_int
from .reducer import OrderKey
from .target_group import _digest

SCHEMA = "machine_adaptive_exit_whole_group_execution_v1"
REQUEST_SCHEMA = "machine_adaptive_exit_whole_group_original_exit_v1"


def whole_exit_key(coordinator):
    return canonical_sha256(
        {"group_slot": coordinator.key, "execution_kind": "WHOLE_EXIT"}
    )


@dataclass(frozen=True)
class WholeExitServices:
    authorize_request: Callable  # (session, immutable request) -> bool
    authorize_action: Callable  # (binding, request, action, now) -> bool
    action_loader: Callable  # (session, request, kind, quantity, now) -> fresh input


def make_whole_exit_request(
    session,
    *,
    execution_policy,
    entry_signal_id,
    reason,
    signal_id,
    source_hash,
    observed_at_ms,
    accepted_at_ms,
    route,
    source_session,
    pending_buys=None,
    pending_confirmation=None,
    scale_in_requested=False,
):
    raw = {
        "schema": REQUEST_SCHEMA,
        "session_binding_hash": canonical_sha256(session.binding),
        "execution_policy_hash": canonical_sha256(execution_policy),
        "entry_signal_id": entry_signal_id,
        "reason": reason,
        "signal_id": signal_id,
        "source_hash": source_hash,
        "observed_at_ms": observed_at_ms,
        "accepted_at_ms": accepted_at_ms,
        "route": route,
        "source_session": source_session,
    }
    if pending_buys or pending_confirmation or scale_in_requested:
        raw.update(
            schema="machine_adaptive_exit_whole_group_original_exit_v2",
            pending_buys=deepcopy(pending_buys or []),
            pending_confirmation_sha256=canonical_sha256(
                {"pending": pending_confirmation}
            ),
            scale_in_requested=scale_in_requested,
        )
    raw["canonical_sha256"] = canonical_sha256(raw)
    validate_whole_exit_request(
        raw,
        session,
        execution_policy=execution_policy,
        entry_signal_id=entry_signal_id,
        now_ms=accepted_at_ms,
    )
    return raw


def validate_whole_exit_request(
    raw, session, *, execution_policy, entry_signal_id, now_ms
):
    fields = {
        "schema",
        "session_binding_hash",
        "execution_policy_hash",
        "entry_signal_id",
        "reason",
        "signal_id",
        "source_hash",
        "observed_at_ms",
        "accepted_at_ms",
        "route",
        "source_session",
        "canonical_sha256",
    }
    group = session.group
    if (
        isinstance(raw, dict)
        and raw.get("schema") == "machine_adaptive_exit_whole_group_original_exit_v2"
    ):
        fields |= {"pending_buys", "pending_confirmation_sha256", "scale_in_requested"}
        validate_pending_buys(raw.get("pending_buys"), session)
        if (
            not _digest(raw.get("pending_confirmation_sha256"))
            or type(raw.get("scale_in_requested")) is not bool
            or (raw["scale_in_requested"] and not raw["pending_buys"])
        ):
            raise ValueError("whole_exit_pending_intent_binding_invalid")
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or raw["schema"]
        not in {REQUEST_SCHEMA, "machine_adaptive_exit_whole_group_original_exit_v2"}
        or raw["canonical_sha256"] != canonical_sha256(raw)
        or raw["session_binding_hash"] != canonical_sha256(session.binding)
        or not isinstance(execution_policy, dict)
        or not isinstance(execution_policy.get("policy_id"), str)
        or not execution_policy.get("policy_id")
        or raw["execution_policy_hash"] != canonical_sha256(execution_policy)
        or not isinstance(entry_signal_id, str)
        or not entry_signal_id
        or raw["entry_signal_id"] != entry_signal_id
        or not isinstance(raw["signal_id"], str)
        or not raw["signal_id"]
        or not _digest(raw["source_hash"])
        or not all(
            positive_int(v)
            for v in (raw["observed_at_ms"], raw["accepted_at_ms"], now_ms)
        )
        or not max(lot[3] for lot in group.lots)
        <= raw["observed_at_ms"]
        <= raw["accepted_at_ms"]
        <= now_ms
        or datetime.fromtimestamp(raw["accepted_at_ms"] / 1000, KST).date().isoformat()
        != group.target.trading_date
        or raw["source_session"] != group.scope.session
    ):
        raise ValueError("whole_exit_original_policy_binding_invalid")
    if raw["reason"] == "source_final_exit":
        if (
            execution_policy.get("source_final_exit_action")
            != "sell_own_filled_quantity"
            or raw["route"] not in {"KRX", "NXT"}
            or group.scope.route not in {"SOR", raw["route"]}
        ):
            raise ValueError("whole_exit_source_policy_or_route_invalid")
    elif raw["reason"] == "force_flat":
        try:
            cutoff = time.fromisoformat(execution_policy["force_exit_time"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("whole_exit_force_flat_policy_invalid") from None
        if (
            cutoff.tzinfo is not None
            or execution_policy.get("force_flat_at_session_end") is not True
            or raw["route"] != group.scope.route
            or raw["source_hash"] != canonical_sha256(execution_policy)
            or datetime.fromtimestamp(raw["observed_at_ms"] / 1000, KST).time() < cutoff
        ):
            raise ValueError("whole_exit_force_flat_policy_invalid")
    else:
        raise ValueError("whole_exit_unapproved_reason")


class WholeGroupExit:
    def __init__(self, *, runner, coordinator_factory, services, session_loader):
        if not isinstance(services, WholeExitServices) or any(
            not callable(f)
            for f in (
                services.authorize_request,
                services.authorize_action,
                services.action_loader,
                session_loader,
            )
        ):
            raise ValueError("whole_exit_independent_services_required")
        self.runner, self.services, self.session_loader = (
            runner,
            services,
            session_loader,
        )
        self.inflight = None
        self.write_guard = self._transport_guard
        self.c = coordinator_factory(self.write_guard)
        if (
            self.c.adapter.write_guard is not self.write_guard
            or self.c.binding != runner.coordinator.binding
        ):
            raise ValueError("whole_exit_original_owner_adapter_required")
        self.key = whole_exit_key(self.c)
        self.binding = {
            "runner_binding": deepcopy(runner.binding),
            "whole_bounds": runner.bounds.to_payload(),
        }
        self.binding_hash = canonical_sha256(self.binding)
        adapter = self.c.adapter
        self.buy_adapter = RegisteredBuyCancelAdapter(
            post=adapter.post,
            registry=adapter.registry,
            context=adapter.context,
            symbol=adapter.symbol,
            routes=adapter.routes,
            policy_hash=adapter.policy_hash,
            maximum_quantity=adapter.maximum_quantity,
            max_snapshot_age_ms=self.c.max_age,
            require_write_authority=self.c._authorize,
            write_guard=self.write_guard,
            now_ms=adapter.now_ms,
        )

    def _pending_ids(self, raw):
        return tuple(
            r["identity"]["intent_id"] for r in raw["request"].get("pending_buys", [])
        )

    def _closed(self, raw, rows):
        result = closed_census(rows, pending_buy_ids=self._pending_ids(raw))
        base = sum(
            r["filled_qty"]
            for r in result["buy_orders"]
            if r["intent_id"] not in self._pending_ids(raw)
        )
        if base != self.c.group.quantity:
            raise ValueError("whole_exit_group_quantity_conflict")
        return result

    def _read(self):
        self.c._authorize()
        if (
            self.c.adapter.write_guard is not self.write_guard
            or canonical_sha256(self.binding) != self.binding_hash
            or self.binding["runner_binding"] != self.runner.binding
            or self.binding["whole_bounds"] != self.runner.bounds.to_payload()
        ):
            raise ValueError("whole_exit_execution_binding_changed")
        raw = deepcopy(self.c.load_record(self.key))
        if raw is not None:
            if self.c.load_record(self.runner._key("GROUP_TERMINAL")) is not None:
                raise ValueError("whole_exit_competing_terminal_journal")
            if (
                not isinstance(raw, dict)
                or set(raw)
                != {
                    "schema",
                    "binding_hash",
                    "request",
                    "original_actions",
                    "actions",
                    "terminal",
                    "canonical_sha256",
                }
                or raw["schema"] != SCHEMA
                or raw["binding_hash"] != self.binding_hash
                or raw["canonical_sha256"] != canonical_sha256(raw)
                or not isinstance(raw["actions"], list)
                or raw["original_actions"]
                != {
                    k: v["canonical_sha256"]
                    for k, v in self.runner.action_records().items()
                }
            ):
                raise ValueError("whole_exit_frozen_journal_conflict")
            if (
                self.services.authorize_request(
                    self.session_loader(), deepcopy(raw["request"])
                )
                is not True
            ):
                raise PermissionError("whole_exit_request_authority_missing")
            self.c._authorize()
            for index, action in enumerate(raw["actions"]):
                self._validate_action(action, index, raw)
            self._validate_lineage(raw)
        return raw

    def _validate_lineage(self, raw):
        # Do not accept a rehashed journal that skips a generation, cancels a
        # different root, or invents additional execution slots after restart.
        roots = {self.c.group.target: 1}
        for record in self.runner.action_records().values():
            if record["action"]["kind"] == "SELL_RUNNER":
                row = self.runner._intent(record)
                if row and row.get("broker_order_no"):
                    roots[OrderKey(row["order_date"], row["broker_order_no"])] = 1
        cancels, sold, previous = set(), 0, self.c.group.target
        pending = validate_pending_buys(
            raw["request"].get("pending_buys", []), self.session_loader()
        )
        previous_time = raw["request"]["accepted_at_ms"]
        for action in raw["actions"]:
            key = OrderKey(**action["predecessor"])
            if action["created_at_ms"] < previous_time:
                raise ValueError("whole_exit_action_clock_regressed")
            previous_time = action["created_at_ms"]
            if action["kind"] == "CANCEL_BUY":
                if (
                    key not in pending
                    or key in cancels
                    or action["generation"] != 1
                    or sold
                ):
                    raise ValueError("whole_exit_buy_cancel_lineage_conflict")
                cancels.add(key)
            elif action["kind"] == "CANCEL":
                if (
                    key not in roots
                    or key in cancels
                    or action["generation"] != roots[key]
                ):
                    raise ValueError("whole_exit_cancel_lineage_conflict")
                cancels.add(key)
            else:
                sold += 1
                if action["generation"] != sold or key != previous:
                    raise ValueError("whole_exit_sell_lineage_conflict")
                row = self._intent(action)
                if row and row.get("broker_order_no"):
                    previous = OrderKey(row["order_date"], row["broker_order_no"])
                    roots[previous] = sold
                elif action is not raw["actions"][-1]:
                    raise ValueError("whole_exit_unbound_predecessor")

    def _save(self, raw, expected):
        self.c._authorize()
        raw = deepcopy(raw)
        raw["canonical_sha256"] = canonical_sha256(raw)
        self.c.save_record(self.key, expected, raw)
        if self._read() != raw:
            raise ValueError("whole_exit_durable_save_missing")
        return raw

    def claim(self, request):
        old = self._read()
        if old is not None:
            if old["request"] != request:
                raise ValueError("whole_exit_request_is_immutable")
            return
        self.c._authorize()
        if (
            self.services.authorize_request(self.session_loader(), deepcopy(request))
            is not True
        ):
            raise PermissionError("whole_exit_request_authority_missing")
        if self.c.load_record(self.runner._key("GROUP_TERMINAL")) is not None:
            raise ValueError("whole_exit_already_terminal")
        self._save(
            {
                "schema": SCHEMA,
                "binding_hash": self.binding_hash,
                "request": deepcopy(request),
                "original_actions": {
                    k: r["canonical_sha256"]
                    for k, r in self.runner.action_records().items()
                },
                "actions": [],
                "terminal": None,
            },
            None,
        )

    def _client(self, kind, predecessor, generation):
        if kind == "CANCEL_BUY":
            return self.buy_adapter.client_id(predecessor)
        if kind == "CANCEL":
            return (
                FAMILY
                + ":whole-cancel:"
                + canonical_sha256({"slot": self.c.key, "order": asdict(predecessor)})
            )
        if generation == 1:
            return self.c.adapter.whole_group_client_id(self.c.group.target)
        return self.c.adapter._replacement_client_id(predecessor)

    def _validate_action(self, action, index, raw):
        maximum = self.c.group.quantity + sum(
            r["identity"]["quantity"] for r in raw["request"].get("pending_buys", [])
        )
        if (
            not isinstance(action, dict)
            or set(action)
            != {
                "index",
                "kind",
                "generation",
                "predecessor",
                "quantity",
                "limit_price",
                "source_hash",
                "observed_at_ms",
                "created_at_ms",
                "canonical_sha256",
            }
            or type(action["index"]) is not int
            or action["index"] != index
            or action["canonical_sha256"] != canonical_sha256(action)
            or action["kind"] not in {"NEW", "CANCEL", "CANCEL_BUY"}
            or not positive_int(action["generation"])
            or action["generation"] > self.runner.bounds.maximum_sell_attempts
            or not positive_int(action["quantity"])
            or action["quantity"] > maximum
            or not positive_int(action["observed_at_ms"])
            or not positive_int(action["created_at_ms"])
            or not action["observed_at_ms"]
            <= action["created_at_ms"]
            <= self.c.adapter.now_ms()
            or not _digest(action["source_hash"])
            or (action["kind"] != "NEW" and action["limit_price"] is not None)
            or (
                action["kind"] == "NEW"
                and (
                    not positive_int(action["limit_price"])
                    or action["limit_price"] % get_tick_size(action["limit_price"])
                )
            )
        ):
            raise ValueError("whole_exit_action_invalid")
        key = OrderKey(**action["predecessor"])
        if (
            key.trading_date != self.c.group.target.trading_date
            or not key.order_no.isascii()
            or len(key.order_no) != 7
            or not key.order_no.isdigit()
            or int(key.order_no) == 0
        ):
            raise ValueError("whole_exit_action_order_invalid")

    def _intent(self, action):
        key = OrderKey(**action["predecessor"])
        context = replace(
            self.c.adapter.context,
            client_intent_id=self._client(action["kind"], key, action["generation"]),
        )
        row = self.c.adapter.registry.intent_for_client(context=context)
        if row is not None and any(
            row.get(k) != v
            for k, v in {
                "side": "BUY" if action["kind"] == "CANCEL_BUY" else "SELL",
                "action": (
                    "CANCEL" if action["kind"] == "CANCEL_BUY" else action["kind"]
                ),
                "quantity": action["quantity"],
                "symbol": self.c.group.scope.symbol,
                "route": self.c.group.scope.route,
                "order_date": key.trading_date,
                "authority_policy_id": FAMILY,
                "authority_policy_hash": self.c.allocation.policy_hash,
                "original_order_no": key.order_no if action["kind"] != "NEW" else "",
            }.items()
        ):
            raise ValueError("whole_exit_registry_intent_conflict")
        return row

    def _census(self, raw, *, allow_last_missing=False):
        target = self.c._target()
        rows = [self.c._row(order) for _, order, _, _, _ in self.c.group.lots] + [
            target
        ]
        pending = raw["request"].get("pending_buys", [])
        validate_pending_buys(
            pending, self.session_loader(), registry=self.c.adapter.registry
        )
        rows.extend(
            self.c._row(
                OrderKey(r["identity"]["order_date"], r["identity"]["broker_order_no"])
            )
            for r in pending
        )
        for record in self.runner.action_records().values():
            row = self.runner._intent(record)
            if row is None:
                raise ValueError("whole_exit_original_action_unbound")
            rows.append(row)
        for index, action in enumerate(raw["actions"]):
            row = self._intent(action)
            if row is None:
                if allow_last_missing and index == len(raw["actions"]) - 1:
                    continue
                raise ValueError("whole_exit_action_unbound")
            rows.append(row)
        census = self.c.adapter.registry.position_intents(
            context=self.c.adapter.context, symbol=self.c.group.scope.symbol
        )
        if len({r["intent_id"] for r in rows}) != len(rows) or {
            r["intent_id"]: r for r in census
        } != {r["intent_id"]: r for r in rows}:
            raise ValueError("whole_exit_position_census_conflict")
        return rows

    def _transport_guard(self, request):
        if self.inflight is None:
            return False
        raw = self._read()
        action = raw["actions"][-1]
        if raw["terminal"] is not None or action["canonical_sha256"] != self.inflight:
            return False
        now, bounds = self.c.adapter.now_ms(), self.runner.bounds
        self._census(raw, allow_last_missing=True)
        if action["kind"] == "NEW":
            prior_sell_index = max(
                (a["index"] for a in raw["actions"][:-1] if a["kind"] == "NEW"),
                default=-1,
            )
            releases = [
                a["created_at_ms"]
                for a in raw["actions"]
                if a["kind"] == "CANCEL" and a["index"] > prior_sell_index
            ]
            start = min(releases) if releases else raw["request"]["accepted_at_ms"]
            if not 0 <= now - start <= bounds.max_unprotected_ms:
                raise PermissionError("whole_exit_unprotected_deadline_exceeded")
        if (
            not 0 <= now - action["observed_at_ms"] <= bounds.max_decision_age_ms
            or self.services.authorize_action(
                deepcopy(self.binding), deepcopy(raw["request"]), deepcopy(action), now
            )
            is not True
        ):
            raise PermissionError("whole_exit_fresh_price_depth_and_safety_required")
        self.c._authorize()
        if self._read() != raw:
            raise ValueError("whole_exit_generation_changed_during_validation")
        self._census(raw, allow_last_missing=True)
        if (
            not 0
            <= self.c.adapter.now_ms() - action["observed_at_ms"]
            <= bounds.max_decision_age_ms
        ):
            raise PermissionError("whole_exit_action_stale_after_validation")
        key = OrderKey(**action["predecessor"])
        return (
            request.predecessor == key
            and request.action
            == ("CANCEL" if action["kind"] == "CANCEL_BUY" else action["kind"])
            and request.context
            == replace(
                self.c.adapter.context,
                client_intent_id=self._client(
                    action["kind"], key, action["generation"]
                ),
            )
            and request.quantity == action["quantity"]
            and (
                type(request) is BuyCancelWrite
                if action["kind"] == "CANCEL_BUY"
                else request.limit_price == action["limit_price"]
            )
            and request.symbol == self.c.group.scope.symbol
            and request.route == self.c.group.scope.route
            and request.policy_hash == self.c.allocation.policy_hash
        )

    def _send(self, raw, action):
        prior = self._intent(action)
        if prior is not None:
            return {
                "status": "whole_exit_" + prior["state"].lower(),
                "group_terminal": False,
            }
        rows = self._census(raw, allow_last_missing=True)
        self.inflight = action["canonical_sha256"]
        key, adapter = OrderKey(**action["predecessor"]), self.c.adapter
        try:
            if action["kind"] == "CANCEL_BUY":
                ack = self.buy_adapter.cancel_owned_buy(
                    key,
                    quantity=action["quantity"],
                    action_id=action["canonical_sha256"],
                )
            elif action["kind"] == "CANCEL":
                ack = adapter.cancel_owned_sell(
                    key,
                    quantity=action["quantity"],
                    action_id=self._client("CANCEL", key, action["generation"]),
                )
            elif action["generation"] == 1:
                ack = adapter.submit_closed_group_residual(
                    key,
                    quantity=action["quantity"],
                    limit_price=action["limit_price"],
                    action_id=self._client("NEW", key, 1),
                    census_sha256=_hash(sorted(rows, key=lambda r: r["intent_id"])),
                    pending_buy_ids=self._pending_ids(raw),
                )
            else:
                ack = adapter.submit_owned_sell(
                    key,
                    quantity=action["quantity"],
                    limit_price=action["limit_price"],
                    action_id=self._client("NEW", key, action["generation"]),
                )
            return {
                "status": (
                    "whole_exit_order_bound"
                    if ack.accepted
                    else "whole_exit_order_requires_recovery"
                ),
                "group_terminal": False,
            }
        finally:
            self.inflight = None

    def _act(self, raw, kind, predecessor, quantity, generation):
        now = self.c.adapter.now_ms()
        source = self.services.action_loader(
            self.session_loader(), deepcopy(raw["request"]), kind, quantity, now
        )
        if not isinstance(source, dict) or set(source) != {
            "source_hash",
            "observed_at_ms",
            "limit_price",
        }:
            raise ValueError("whole_exit_fresh_action_source_missing")
        action = {
            "index": len(raw["actions"]),
            "kind": kind,
            "generation": generation,
            "predecessor": asdict(predecessor),
            "quantity": quantity,
            "created_at_ms": self.c.adapter.now_ms(),
            **source,
        }
        action["canonical_sha256"] = canonical_sha256(action)
        self._validate_action(action, action["index"], raw)
        expected = raw["canonical_sha256"]
        raw["actions"].append(action)
        return self._send(self._save(raw, expected), action)

    def _terminal(self, raw, rows, observed_at_ms):
        result = self._closed(raw, rows)
        if result.pop("residual_qty") != 0:
            raise ValueError("whole_exit_owned_residual_remaining")
        if (
            self.c.adapter.registry.owner_position_qty(
                self.c.adapter.context.position_id, symbol=self.c.group.scope.symbol
            )
            != 0
        ):
            raise ValueError("whole_exit_registry_not_flat")
        if (
            not raw["request"]["accepted_at_ms"]
            <= observed_at_ms
            <= self.c.adapter.now_ms()
        ):
            raise ValueError("whole_exit_terminal_time_invalid")
        # Target first: ordinary owner updates its original order, then appends successors.
        result["orders"].sort(
            key=lambda r: r["order_no"] != self.c.group.target.order_no
        )
        result["orders"][0]["role"] = "original_target"
        payload = {
            "schema": "machine_adaptive_exit_whole_group_terminal_v1",
            "terminal_id": self.binding_hash,
            "request_hash": raw["request"]["canonical_sha256"],
            "action_hashes": [r["canonical_sha256"] for r in raw["actions"]],
            "original_action_hashes": raw["original_actions"],
            "group_binding_hash": self.c.binding_hash,
            "scope_key": self.c.group.scope.key,
            "position_id": self.c.adapter.context.position_id,
            "observed_at_ms": observed_at_ms,
            "execution_status": "reconciled_flat",
            **result,
            "actual_lot_fill_attribution": None,
            "realized_pnl_status": "unreconciled_exact_fill_cost_required",
            "realized_net_profit_krw": None,
            "economic_acceptance": False,
            "new_entry_authority": False,
        }
        return payload | {"canonical_sha256": canonical_sha256(payload)}

    def validate_terminal(self, receipt):
        raw = self._read()
        if (
            not isinstance(receipt, dict)
            or raw["terminal"] != receipt
            or self._terminal(raw, self._census(raw), receipt.get("observed_at_ms"))
            != receipt
        ):
            raise ValueError("whole_exit_terminal_binding_conflict")

    def step(self, *, receipt_only=False):
        if type(receipt_only) is not bool:
            raise ValueError("group_receipt_only_flag_invalid")
        gap = {
            "status": "group_clock_source_gap",
            "group_terminal": False,
            "manager_must_remain": True,
        }
        raw = self._read()
        if raw is None:
            raise ValueError("whole_exit_request_not_claimed")
        if raw["terminal"] is not None:
            self.validate_terminal(raw["terminal"])
            return {
                "status": "group_terminal",
                "group_terminal": True,
                "receipt": raw["terminal"],
            }
        if raw["actions"] and self._intent(raw["actions"][-1]) is None:
            if receipt_only:
                return gap
            return self._send(raw, raw["actions"][-1])
        rows = self._census(raw)
        if any(r["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"} for r in rows):
            return {
                "status": "whole_exit_unresolved_intent_recovery",
                "group_terminal": False,
            }
        # Complete existing partial release or cancel first; never send a second cancel.
        pending = [
            r
            for r in rows
            if r["action"] == "CANCEL" and r["state"] != "ORDER_TERMINAL"
        ]
        if pending:
            child = pending[0]
            action = next(
                (
                    a
                    for a in raw["actions"]
                    if self._intent(a)["intent_id"] == child["intent_id"]
                ),
                None,
            )
            if (
                action is not None
                and self.c.adapter.now_ms() - action["created_at_ms"]
                > self.runner.bounds.max_unprotected_ms
            ):
                return {
                    "status": "whole_exit_cancel_deadline_exceeded",
                    "group_terminal": False,
                }
            release = self.runner.action_records().get("RELEASE_RUNNER")
            if child["side"] == "BUY":
                self.buy_adapter.reconcile_terminal_cancel(
                    OrderKey(child["order_date"], child["original_order_no"]),
                    OrderKey(child["order_date"], child["broker_order_no"]),
                )
            elif (
                release
                and self.runner._intent(release)["intent_id"] == child["intent_id"]
            ):
                self.runner.reconcile_release()
            else:
                self.c.adapter.reconcile_terminal_cancel(
                    OrderKey(child["order_date"], child["original_order_no"]),
                    OrderKey(child["order_date"], child["broker_order_no"]),
                    max_snapshot_age_ms=self.c.max_age,
                )
            self.c._authorize()
            return {
                "status": "whole_exit_cancel_reconciliation",
                "group_terminal": False,
            }
        # The original BUY may fill while its cancellation travels. Close it
        # before canceling any target or creating any pooled residual SELL.
        for root in rows:
            if root["intent_id"] in self._pending_ids(raw) and (
                root["state"] != "ORDER_TERMINAL"
                or not isinstance(root.get("terminal_reconciliation"), dict)
            ):
                key = OrderKey(root["order_date"], root["broker_order_no"])
                snapshot = self.buy_adapter.reconcile_owned_buy(key)
                self.c._authorize()
                if not snapshot.source_ok:
                    return {
                        "status": "whole_exit_pending_buy_source_gap",
                        "group_terminal": False,
                    }
                if snapshot.terminal:
                    return {
                        "status": "whole_exit_pending_buy_reconciled",
                        "group_terminal": False,
                    }
                if receipt_only:
                    return gap
                return self._act(raw, "CANCEL_BUY", key, snapshot.remaining_qty, 1)
        working = [
            r
            for r in rows
            if r["side"] == "SELL"
            and r["action"] == "NEW"
            and (
                r["state"] != "ORDER_TERMINAL"
                or not isinstance(r.get("terminal_reconciliation"), dict)
            )
        ]
        if working:
            root = working[0]
            key = OrderKey(root["order_date"], root["broker_order_no"])
            start = self.c.adapter.now_ms()
            snapshot = self.c.adapter.reconcile_owned_sell(key)
            self.c._authorize()
            if (
                not snapshot.source_ok
                or not 0 <= self.c.adapter.now_ms() - start <= self.c.max_age
            ):
                return {"status": "whole_exit_source_gap", "group_terminal": False}
            if snapshot.terminal:
                return {"status": "whole_exit_root_reconciled", "group_terminal": False}
            mine = next(
                (
                    a
                    for a in raw["actions"]
                    if a["kind"] == "NEW"
                    and self._intent(a)["intent_id"] == root["intent_id"]
                ),
                None,
            )
            if (
                mine is not None
                and self.c.adapter.now_ms() - mine["created_at_ms"]
                < self.runner.bounds.sell_ttl_ms
            ):
                return {"status": "whole_exit_sell_working", "group_terminal": False}
            if receipt_only:
                return gap
            return self._act(
                raw,
                "CANCEL",
                key,
                snapshot.remaining_qty,
                mine["generation"] if mine else 1,
            )
        closed = self._closed(raw, rows)
        if closed["residual_qty"] == 0:
            expected = raw["canonical_sha256"]
            raw["terminal"] = self._terminal(raw, rows, self.c.adapter.now_ms())
            saved = self._save(raw, expected)
            return {
                "status": "group_terminal",
                "group_terminal": True,
                "receipt": saved["terminal"],
            }
        sells = [a for a in raw["actions"] if a["kind"] == "NEW"]
        if len(sells) >= self.runner.bounds.maximum_sell_attempts:
            return {
                "status": "whole_exit_residual_attempts_exhausted",
                "group_terminal": False,
            }
        if receipt_only:
            return gap
        predecessor = (
            self.c.group.target
            if not sells
            else OrderKey(
                self._intent(sells[-1])["order_date"],
                self._intent(sells[-1])["broker_order_no"],
            )
        )
        return self._act(
            raw, "NEW", predecessor, closed["residual_qty"], len(sells) + 1
        )
