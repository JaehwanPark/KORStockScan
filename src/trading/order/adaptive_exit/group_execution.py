"""Opt-in bounded runner order/TTL generations after a frozen allocation.

No policy, price, trailing trigger or numeric approval is invented here. The
original owner supplies a decision receipt and an independent action validator
that rechecks fresh executable depth and ALL safety guards before each write.
Action slots are durable before transport. Registry client IDs own recovery;
an ACK is never terminal and a runner terminal is never a group/episode flat.
The optional pre/post-release decision books are not approval validators. The
actual launcher is not wired. Residual retries require a separately supplied
fresh-price/intent validator; enabling more attempts never supplies that approval.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.tick_utils import get_tick_size
from .broker import FAMILY, SellWrite
from .group_runtime import GroupCoordinator
from .group_decision import GroupDecisionBook
from .models import positive_int
from .reducer import OrderKey
from .target_group import _digest

SCHEMA = "machine_adaptive_exit_group_execution_action_v1"
GENERATION_SCHEMA = "machine_adaptive_exit_group_execution_action_v2"
KINDS = ("RELEASE_RUNNER", "SELL_RUNNER", "CANCEL_RUNNER_TTL")


@dataclass(frozen=True)
class RunnerBounds:
    sell_ttl_ms: int
    max_decision_age_ms: int
    max_unprotected_ms: int
    maximum_sell_attempts: int = 1

    def __post_init__(self):
        if not all(positive_int(v) for v in asdict(self).values()):
            raise ValueError("explicit_runner_execution_bounds_required")
        if self.maximum_sell_attempts > 3:
            raise ValueError("runner_sell_attempts_exceed_supported_bound")

    def to_payload(self):
        result = asdict(self)
        # Preserve the already frozen one-attempt binding, not a silent migration.
        if self.maximum_sell_attempts == 1:
            result.pop("maximum_sell_attempts")
        return result


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
    """One release and explicitly bounded runner SELL/TTL generations.

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
        decision_policy=None,
        authorize_retry=None,
    ):
        if (
            not isinstance(bounds, RunnerBounds)
            or not _digest(execution_approval_receipt_hash)
            or not callable(authorize_action)
            or not callable(coordinator_factory)
            or (bounds.maximum_sell_attempts > 1 and not callable(authorize_retry))
        ):
            raise ValueError("group_execution_approval_services_required")
        self.bounds, self.authorize_action = bounds, authorize_action
        # Must independently bind the original exit intent, latest source receipt,
        # executable price/depth and approved loss/price bounds. No default exists.
        self.authorize_retry = authorize_retry
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
            "bounds": bounds.to_payload(),
            "execution_approval_receipt_hash": execution_approval_receipt_hash,
            "supported_sell_attempts": bounds.maximum_sell_attempts,
        }
        self.decision_book = (
            GroupDecisionBook(coordinator=c, policy_payload=decision_policy)
            if decision_policy is not None
            else None
        )
        if self.decision_book is not None:
            self.binding["decision_book_binding_hash"] = self.decision_book.binding_hash
        self.binding_hash = canonical_sha256(self.binding)
        from .group_trailing import ReleasedRunnerBook

        self.released_book = ReleasedRunnerBook(self) if self.decision_book else None

    def _authorize(self):
        c = self.coordinator
        c._authorize()
        if (
            c.adapter.write_guard is not self._write_guard
            or self.binding["group_binding_hash"] != c.binding_hash
            or self.binding["bounds"] != self.bounds.to_payload()
            or self.binding["supported_sell_attempts"]
            != self.bounds.maximum_sell_attempts
            or (
                self.bounds.maximum_sell_attempts > 1
                and not callable(self.authorize_retry)
            )
            or canonical_sha256(self.binding) != self.binding_hash
            or self.binding.get("decision_book_binding_hash")
            != (
                self.decision_book.binding_hash
                if self.decision_book is not None
                else None
            )
            or (self.decision_book is not None and self.decision_book.c is not c)
            or (self.released_book is None) != (self.decision_book is None)
            or (
                self.released_book is not None
                and (self.released_book.e is not self or self.released_book.c is not c)
            )
        ):
            raise ValueError("group_execution_frozen_binding_changed")

    def _attempt(self, attempt_no):
        if (
            not positive_int(attempt_no)
            or attempt_no > self.bounds.maximum_sell_attempts
        ):
            raise ValueError("runner_attempt_outside_approved_bound")
        return attempt_no

    def _key(self, kind, attempt_no=1):
        self._attempt(attempt_no)
        if attempt_no != 1 and kind not in {"SELL_RUNNER", "CANCEL_RUNNER_TTL"}:
            raise ValueError("runner_generation_role_invalid")
        raw = {"group_slot": self.coordinator.key, "execution_kind": kind}
        if attempt_no != 1:
            raw["attempt_no"] = attempt_no
        return canonical_sha256(raw)

    def _validate(self, record, kind, attempt_no=1):
        self._attempt(attempt_no)
        if (
            not isinstance(record, dict)
            or set(record)
            != (
                {
                    "schema",
                    "binding_hash",
                    "action",
                    "predecessor",
                    "quantity",
                    "created_at_ms",
                    "canonical_sha256",
                }
                | (
                    {"attempt_no", "original_sell_action_hash"}
                    if attempt_no > 1
                    else set()
                )
            )
            or record.get("schema")
            != (SCHEMA if attempt_no == 1 else GENERATION_SCHEMA)
            or record.get("binding_hash") != self.binding_hash
            or record.get("canonical_sha256") != canonical_sha256(record)
            or not positive_int(record.get("quantity"))
            or not positive_int(record.get("created_at_ms"))
            or (
                attempt_no > 1
                and (
                    type(record.get("attempt_no")) is not int
                    or record["attempt_no"] != attempt_no
                )
            )
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
            or (
                attempt_no == 1
                and kind != "CANCEL_RUNNER_TTL"
                and order != self.coordinator.group.target
            )
        ):
            raise ValueError("group_execution_saved_identity_conflict")
        if attempt_no > 1:
            first = self._read("SELL_RUNNER")
            if (
                first is None
                or record["original_sell_action_hash"] != first["canonical_sha256"]
            ):
                raise ValueError("runner_original_exit_intent_missing")
        if kind == "SELL_RUNNER" and attempt_no > 1:
            previous, qty = self._retry_predecessor(attempt_no)
            prior = self._read("SELL_RUNNER", attempt_no - 1)
            if (
                order != previous
                or record["quantity"] != qty
                or record["created_at_ms"] < prior["created_at_ms"]
            ):
                raise ValueError("runner_retry_predecessor_quantity_conflict")
        elif kind != "CANCEL_RUNNER_TTL":
            frozen = self.coordinator._read()
            if (
                frozen is None
                or record["quantity"] != frozen["requested_qty"]
                or record["created_at_ms"] < frozen["frozen_at_ms"]
            ):
                raise ValueError("group_execution_frozen_quantity_conflict")
        else:
            sell = self._read("SELL_RUNNER", attempt_no)
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

    def _read(self, kind, attempt_no=1):
        self._authorize()
        value = self.coordinator.load_record(self._key(kind, attempt_no))
        return (
            self._validate(deepcopy(value), kind, attempt_no)
            if value is not None
            else None
        )

    def _record(self, action, predecessor, quantity, attempt_no=1):
        self._authorize()
        old = self._read(action.kind, attempt_no)
        if old is not None:
            if (
                old["action"] != asdict(action)
                or old["predecessor"] != asdict(predecessor)
                or old["quantity"] != quantity
            ):
                raise ValueError("group_execution_action_is_immutable")
            return old
        raw = {
            "schema": SCHEMA if attempt_no == 1 else GENERATION_SCHEMA,
            "binding_hash": self.binding_hash,
            "action": asdict(action),
            "predecessor": asdict(predecessor),
            "quantity": quantity,
            "created_at_ms": self.coordinator.adapter.now_ms(),
        }
        if attempt_no > 1:
            raw.update(
                attempt_no=attempt_no,
                original_sell_action_hash=self._read("SELL_RUNNER")["canonical_sha256"],
            )
        raw["canonical_sha256"] = canonical_sha256(raw)
        self._validate(raw, action.kind, attempt_no)
        self._action_allowed(raw)
        self.coordinator.save_record(
            self._key(action.kind, attempt_no), None, deepcopy(raw)
        )
        saved = self._read(action.kind, attempt_no)
        if saved != raw:
            raise ValueError("group_execution_durable_save_missing")
        return saved

    def _action_allowed(self, record):
        self._authorize()
        from .group_whole_exit import whole_exit_key

        if self.coordinator.load_record(whole_exit_key(self.coordinator)) is not None:
            raise ValueError("whole_exit_supersedes_runner_writer")
        if self.coordinator.load_record(self._key("GROUP_TERMINAL")) is not None:
            raise ValueError("group_terminal_blocks_new_execution")
        if (
            self.decision_book is not None
            and record["action"]["kind"] == "RELEASE_RUNNER"
        ):
            self.decision_book.validate_write(record["action"])
        if record["action"]["kind"] == "SELL_RUNNER":
            if record.get("attempt_no", 1) == 1:
                if self.released_book is not None:
                    self.released_book.validate_write(record["action"])
            else:
                original = self._read("SELL_RUNNER")
                self._retry_census()
                if (
                    self.released_book is not None
                    and original["action"] != self.released_book.sell_action()
                ):
                    raise ValueError("runner_original_decided_exit_changed")
                if (
                    self.authorize_retry(
                        deepcopy(self.binding),
                        deepcopy(original),
                        deepcopy(record),
                        self.coordinator.adapter.now_ms(),
                    )
                    is not True
                ):
                    raise PermissionError(
                        "runner_fresh_retry_price_and_intent_required"
                    )
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
        kind, attempt_no, digest = self._inflight
        record = self._read(kind, attempt_no)
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
        self._inflight = (
            record["action"]["kind"],
            record.get("attempt_no", 1),
            record["canonical_sha256"],
        )
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
            "status": (
                "order_bound"
                if row["state"] in {"ORDER_BOUND", "ORDER_TERMINAL"}
                else "recovery_required"
            ),
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

    def request_decided_release(self):
        """Consume the persisted pre-release receipt, retaining independent guards.

        The book is re-read before AND after registry reservation by _action_allowed.
        No implicit enrollment, numeric approval or trail activation is provided.
        """
        if self.decision_book is None:
            raise ValueError("group_execution_decision_book_required")
        return self.request_release(GroupAction(**self.decision_book.release_action()))

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

    def sell_decided_released(self):
        """Consume the confirmed-release trailing/SELL book, never a raw signal."""
        if self.released_book is None:
            raise ValueError("released_runner_decision_book_required")
        return self.sell_released(GroupAction(**self.released_book.sell_action()))

    def action_records(self):
        """Contiguous, bounded generations, including unresolved reservations."""
        result = {}
        release = self._read("RELEASE_RUNNER")
        if release is not None:
            result["RELEASE_RUNNER"] = release
        missing = False
        for number in range(1, self.bounds.maximum_sell_attempts + 1):
            sell = self._read("SELL_RUNNER", number)
            cancel = self._read("CANCEL_RUNNER_TTL", number)
            if sell is None:
                missing = True
                if cancel is not None:
                    raise ValueError("runner_cancel_without_sell_generation")
                continue
            if missing or release is None:
                raise ValueError("runner_generation_lineage_gap")
            suffix = "" if number == 1 else f":{number}"
            result["SELL_RUNNER" + suffix] = sell
            if cancel is not None:
                result["CANCEL_RUNNER_TTL" + suffix] = cancel
        return result

    def _latest_attempt(self):
        rows = self.action_records()
        return max(
            (
                r.get("attempt_no", 1)
                for r in rows.values()
                if r["action"]["kind"] == "SELL_RUNNER"
            ),
            default=1,
        )

    def _retry_predecessor(self, attempt_no):
        """Read both terminal proofs; a broker ACK/zero remainder is insufficient."""
        self._attempt(attempt_no)
        if attempt_no < 2:
            raise ValueError("runner_retry_requires_successor_generation")
        from .group_terminal import _terminal_order, _runner_cancel_proof

        sell = self._read("SELL_RUNNER", attempt_no - 1)
        cancel = self._read("CANCEL_RUNNER_TTL", attempt_no - 1)
        root, child = self._intent(sell) if sell else None, (
            self._intent(cancel) if cancel else None
        )
        if root is None or child is None:
            raise ValueError("runner_retry_confirmed_predecessor_required")
        _terminal_order(root, "adaptive_runner")
        _runner_cancel_proof(root, child)
        quantity = root["quantity"] - root["filled_qty"]
        if not positive_int(quantity):
            raise ValueError("runner_retry_no_owned_residual")
        return OrderKey(root["order_date"], root["broker_order_no"]), quantity

    def _retry_census(self):
        c = self.coordinator
        expected = [c._target()] + [c._row(order) for _, order, _, _, _ in c.group.lots]
        for record in self.action_records().values():
            row = self._intent(record)
            if row is not None:
                expected.append(row)
        actual = c.adapter.registry.position_intents(
            context=c.adapter.context, symbol=c.group.scope.symbol
        )
        if len({r["intent_id"] for r in expected}) != len(expected) or {
            r["intent_id"]: r for r in actual
        } != {r["intent_id"]: r for r in expected}:
            raise ValueError("runner_retry_position_census_conflict")

    def retry_runner(self, action: GroupAction, *, attempt_no):
        """Explicit fresh action for a confirmed residual; never a network retry.

        Original SELL intent remains sticky. authorize_retry must validate the
        newly supplied price/source within the approved execution envelope; it
        cannot require a second alpha trigger or silently expand the attempt cap.
        An existing ambiguous/rejected/reserved intent is returned, never resent.
        """
        self._attempt(attempt_no)
        if action.kind != "SELL_RUNNER" or attempt_no < 2:
            raise ValueError("runner_retry_successor_sell_required")
        self.action_records()
        old = self._read("SELL_RUNNER", attempt_no)
        if old is not None and self._intent(old) is not None:
            if old["action"] != asdict(action):
                raise ValueError("group_execution_action_is_immutable")
            return self._status(self._intent(old))
        # Fresh broker reconciliation before a new generation, followed by
        # independent price/source/safety validation before AND after reservation.
        self._retry_census()
        result = self.reconcile_runner_cancel(attempt_no=attempt_no - 1)
        if result["status"] != "runner_cancel_terminal":
            raise ValueError("runner_retry_confirmed_predecessor_required")
        predecessor, quantity = self._retry_predecessor(attempt_no)
        record = self._record(action, predecessor, quantity, attempt_no)
        return self._send(
            record,
            lambda: self.coordinator.adapter.submit_owned_sell(
                predecessor,
                quantity=quantity,
                limit_price=action.limit_price,
                action_id=self._client("SELL_RUNNER", predecessor),
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

    def poll_runner(self, *, receipt_only=False):
        """Fresh fill/terminal reconciliation; TTL cancels only the runner.

        First runner terminal leaves the original target/group manager alive.
        A terminal partial fill retains the residual owner and requests recovery;
        it does not become a completed profitable episode or a new BUY gate.
        """
        if type(receipt_only) is not bool:
            raise ValueError("group_receipt_only_flag_invalid")
        c = self.coordinator
        attempt_no = self._latest_attempt()
        record = self._read("SELL_RUNNER", attempt_no)
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
            if self._read("CANCEL_RUNNER_TTL", attempt_no) is not None:
                cancel_result = self.reconcile_runner_cancel(attempt_no=attempt_no)
                if cancel_result["status"] != "runner_cancel_terminal":
                    return cancel_result | deadline
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
                "status": (
                    "runner_terminal"
                    if remaining == 0
                    else "runner_residual_requires_recovery"
                ),
                "runner_filled_qty": snapshot.filled_qty,
                "runner_remaining_qty": remaining,
                "attempt_no": attempt_no,
                "maximum_sell_attempts": self.bounds.maximum_sell_attempts,
                "attempts_exhausted": remaining > 0
                and attempt_no == self.bounds.maximum_sell_attempts,
                "manager_must_remain": True,
                "terminal_proof_hash": canonical_sha256(proof),
                "group_terminal": False,
                "realized_pnl": None,
                "realized_pnl_status": "exact_costs_not_reconciled",
            }
        if now - record["created_at_ms"] < self.bounds.sell_ttl_ms:
            return {"status": "runner_working", "group_terminal": False}
        if receipt_only:
            old_cancel = self._read("CANCEL_RUNNER_TTL", attempt_no)
            if old_cancel is not None:
                return self.reconcile_runner_cancel(attempt_no=attempt_no) | deadline
            return deadline | {
                "status": "group_clock_source_gap",
                "group_terminal": False,
                "manager_must_remain": True,
            }
        old_cancel = self._read("CANCEL_RUNNER_TTL", attempt_no)
        if old_cancel is None:
            action = GroupAction(
                "CANCEL_RUNNER_TTL",
                canonical_sha256(
                    {
                        "sell_action": record["canonical_sha256"],
                        "bounds": self.bounds.to_payload(),
                        "snapshot": snapshot.receipt_hash,
                    }
                ),
                snapshot.receipt_hash,
                snapshot.observed_at_ms,
                None,
            )
            old_cancel = self._record(action, order, snapshot.remaining_qty, attempt_no)
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
                "status": (
                    "runner_cancel_pending"
                    if result["status"] == "order_bound"
                    else "recovery_required"
                ),
            }
        )

    def reconcile_runner_cancel(self, *, attempt_no=None):
        """Close the TTL child independently; canceled shares remain inventory."""
        self._authorize()
        attempt_no = (
            self._latest_attempt() if attempt_no is None else self._attempt(attempt_no)
        )
        record, sell = self._read("CANCEL_RUNNER_TTL", attempt_no), self._read(
            "SELL_RUNNER", attempt_no
        )
        cancel = self._intent(record) if record else None
        root = self._intent(sell) if sell else None
        if any(
            row is None or row["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"}
            for row in (cancel, root)
        ):
            return {
                "status": "runner_cancel_intent_requires_recovery",
                "group_terminal": False,
            }
        snapshot = self.coordinator.adapter.reconcile_terminal_cancel(
            OrderKey(root["order_date"], root["broker_order_no"]),
            OrderKey(cancel["order_date"], cancel["broker_order_no"]),
            max_snapshot_age_ms=self.coordinator.max_age,
        )
        self._authorize()
        if snapshot.source_ok is not True or snapshot.terminal is not True:
            return {
                "status": "runner_cancel_terminal_source_gap",
                "group_terminal": False,
            }
        return {
            "status": "runner_cancel_terminal",
            "runner_filled_qty": snapshot.filled_qty,
            "runner_remaining_qty": sell["quantity"] - snapshot.filled_qty,
            "group_terminal": False,
            "realized_pnl": None,
        }

    def reconcile_group_terminal(self):
        """Close exact group quantities without submitting another order."""
        from .group_terminal import reconcile_group_terminal

        return reconcile_group_terminal(self)
