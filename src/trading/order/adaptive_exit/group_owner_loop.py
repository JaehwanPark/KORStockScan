"""Frozen group sessions in the ORIGINAL owner's lock and atomic state store.

No enrollment, default approval, source fabrication or launcher installation.
The caller must supply independently verified policy/account/source services.
Ordinary owner archival consumes a separately revalidated full-group terminal.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Callable

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.owner_custody_registry import OwnerOrderContext
from .group_decision import _plain, _policy
from .group_execution import GroupAction, GroupRunnerExecutor, RunnerBounds
from .group_runtime import GroupCoordinator, RunnerAllocation
from .group_terminal import validate_group_terminal
from .group_whole_exit import WholeExitServices, WholeGroupExit, whole_exit_key
from .broker import KST
from .models import Clock, ClockSourceGap, positive_int
from .reducer import OrderKey
from .source import OwnerScope
from .target_group import TargetGroup, _digest

SESSION_KEY = "adaptive_exit_group_session"
SCHEMA = "machine_adaptive_exit_group_owner_session_v1"


@dataclass(frozen=True)
class GroupLoopServices:
    # Each binding includes the immutable session definition, never just a hash.
    authorize_binding: Callable[[dict], bool]
    owner_guard: Callable[[dict], bool]
    authorize_action: Callable[[dict, dict, int], bool]
    observations_loader: Callable  # (session, phase, now_ms) -> book inputs
    authorize_retry: Callable | None = None
    retry_action_loader: Callable | None = None
    whole_exit: WholeExitServices | None = None
    # Independent of price observations, needed even while polling a live SELL.
    # Read already-collected history, no network: (session, now_ms) -> lot Clock.
    # Missing means receipt-only, never a default zero halt duration.
    clock_loader: Callable | None = None


@dataclass(frozen=True)
class GroupOwnerSession:
    payload: dict

    @classmethod
    def create(
        cls,
        *,
        group,
        allocation,
        context,
        bounds,
        max_snapshot_age_ms,
        execution_approval_receipt_hash,
        decision_policy,
    ):
        definition = {
            "group": group.to_payload(),
            "allocation": asdict(allocation),
            "context": asdict(context),
            "bounds": bounds.to_payload(),
            "max_snapshot_age_ms": max_snapshot_age_ms,
            "execution_approval_receipt_hash": execution_approval_receipt_hash,
            "decision_policy": decision_policy,
        }
        raw = _plain({"schema": SCHEMA, "definition": definition, "records": {}})
        return cls.from_payload(raw | {"canonical_sha256": canonical_sha256(raw)})

    @classmethod
    def from_payload(cls, payload):
        raw = _plain(payload)
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema", "definition", "records", "canonical_sha256"}
            or raw["schema"] != SCHEMA
            or raw["canonical_sha256"] != canonical_sha256(raw)
            or not isinstance(raw["records"], dict)
        ):
            raise ValueError("group_owner_session_schema_invalid")
        session = cls(raw)
        d = session.binding
        if not isinstance(d, dict) or set(d) != {
            "group",
            "allocation",
            "context",
            "bounds",
            "max_snapshot_age_ms",
            "execution_approval_receipt_hash",
            "decision_policy",
        }:
            raise ValueError("group_owner_definition_invalid")
        group, allocation, context = session.group, session.allocation, session.context
        if (
            _plain(group.to_payload()) != d["group"]
            or not positive_int(d["max_snapshot_age_ms"])
            or not _digest(d["execution_approval_receipt_hash"])
            or context.owner_type
            != ("widget_auto_trade" if group.scope.owner == "widget" else "episode")
            or group.episode_id != context.position_id
        ):
            raise ValueError("group_owner_definition_binding_invalid")
        _policy(group, allocation, d["decision_policy"])
        session.bounds  # Validate explicit execution bounds before any gateway.
        for key, value in raw["records"].items():
            if (
                not _digest(key)
                or not isinstance(value, dict)
                or value.get("canonical_sha256") != canonical_sha256(value)
            ):
                raise ValueError("group_owner_durable_record_invalid")
        return session

    @property
    def binding(self):
        return deepcopy(self.payload["definition"])

    @property
    def group(self):
        raw = self.binding["group"]
        group = TargetGroup(
            OwnerScope(**raw["scope"]),
            raw["episode_id"],
            OrderKey(**raw["target"]),
            raw["target_price"],
            tuple((r[0], OrderKey(**r[1]), *r[2:]) for r in raw["lots"]),
            raw["source_hash"],
        )
        group.validate()
        return group

    @property
    def allocation(self):
        raw = self.binding["allocation"]
        raw["runner_lot_ids"] = tuple(raw["runner_lot_ids"])
        raw["lot_order"] = tuple(raw["lot_order"])
        result = RunnerAllocation(**raw)
        result.validate(self.group)
        return result

    @property
    def context(self):
        return OwnerOrderContext(**self.binding["context"])

    @property
    def bounds(self):
        return RunnerBounds(**self.binding["bounds"])

    def to_payload(self):
        return deepcopy(self.payload)


class GroupOwnerPort:
    """Reconstruct all books/actions from the original owner's durable session.

    persist_session(expected_outer_hash, payload) performs an atomic/fsynced CAS
    in that owner's state. load_session reads back that same state. It must not
    return an unrelated side store; a restart uses the saved original owner file.
    """

    def __init__(
        self,
        *,
        services,
        lock_held,
        load_session,
        persist_session,
        adapter_factory,
        owner_binding_guard,
    ):
        if not isinstance(services, GroupLoopServices) or any(
            not callable(f)
            for f in (
                lock_held,
                load_session,
                persist_session,
                adapter_factory,
                owner_binding_guard,
                services.authorize_binding,
                services.owner_guard,
                services.authorize_action,
                services.observations_loader,
            )
        ):
            raise ValueError("group_owner_services_missing")
        self.services, self.lock_held = services, lock_held
        self.load_session, self.persist_session = load_session, persist_session
        self.owner_binding_guard = owner_binding_guard
        if lock_held() is not True:
            raise PermissionError("original_owner_lock_required")
        self.session = GroupOwnerSession.from_payload(load_session())
        self.binding = self.session.binding
        self.allowed_slots = None
        self._guard()

        def factory(write_guard):
            adapter = adapter_factory(self.session, write_guard)
            if adapter.context != self.session.context:
                raise ValueError("group_owner_adapter_context_mismatch")
            return GroupCoordinator(
                group=self.session.group,
                allocation=self.session.allocation,
                adapter=adapter,
                max_snapshot_age_ms=self.binding["max_snapshot_age_ms"],
                load_record=self._load_record,
                save_record=self._save_record,
                lock_held=lock_held,
                authorize_binding=lambda b: self._guard() is True,
                owner_guard=lambda b: self._guard(b) is True,
            )

        self.executor = GroupRunnerExecutor(
            coordinator_factory=factory,
            bounds=self.session.bounds,
            execution_approval_receipt_hash=self.binding[
                "execution_approval_receipt_hash"
            ],
            decision_policy=self.binding["decision_policy"],
            authorize_action=lambda b, r, n: self._write_clock_valid(n)
            and self._guard() is True
            and services.authorize_action(
                {"session": deepcopy(self.binding), "execution": b}, r, n
            )
            is True
            and self._write_clock_valid(self.executor.coordinator.adapter.now_ms()),
            authorize_retry=(
                (
                    lambda b, old, new, n: self._write_clock_valid(n)
                    and self._guard() is True
                    and services.authorize_retry(
                        {"session": deepcopy(self.binding), "execution": b}, old, new, n
                    )
                    is True
                    and self._write_clock_valid(
                        self.executor.coordinator.adapter.now_ms()
                    )
                )
                if callable(services.authorize_retry)
                else None
            ),
        )
        e = self.executor
        allowed = {
            e.coordinator.key,
            e.decision_book.key,
            e.released_book.key,
            e._key("RELEASE_RUNNER"),
            e._key("GROUP_TERMINAL"),
            whole_exit_key(e.coordinator),
        }
        allowed.update(
            e._key(kind, attempt)
            for attempt in range(1, e.bounds.maximum_sell_attempts + 1)
            for kind in ("SELL_RUNNER", "CANCEL_RUNNER_TTL")
        )
        if set(self.session.payload["records"]) - allowed:
            raise ValueError("group_owner_unrecognized_durable_slot")
        self.allowed_slots = allowed
        if services.whole_exit is not None and (
            not isinstance(services.whole_exit, WholeExitServices)
            or not callable(services.whole_exit.authorize_action)
        ):
            raise ValueError("whole_exit_independent_services_required")
        self.whole = (
            WholeGroupExit(
                runner=e,
                coordinator_factory=factory,
                services=replace(
                    services.whole_exit,
                    authorize_action=lambda b, r, a, n: self._write_clock_valid(n)
                    and services.whole_exit.authorize_action(b, r, a, n) is True
                    and self._write_clock_valid(
                        self.executor.coordinator.adapter.now_ms()
                    ),
                ),
                session_loader=self._current,
            )
            if services.whole_exit is not None
            else None
        )

    def _current(self):
        if self.lock_held() is not True:
            raise PermissionError("original_owner_lock_required")
        session = GroupOwnerSession.from_payload(self.load_session())
        if session.binding != self.binding:
            raise ValueError("group_owner_frozen_definition_changed")
        if (
            self.allowed_slots is not None
            and set(session.payload["records"]) - self.allowed_slots
        ):
            raise ValueError("group_owner_unrecognized_durable_slot")
        return session

    def _guard(self, coordinator=None):
        session = self._current()
        binding = session.binding
        if (
            self.services.authorize_binding(binding) is not True
            or self.owner_binding_guard(session) is not True
            or self.services.owner_guard(
                {"session": binding, "coordinator": coordinator}
            )
            is not True
        ):
            raise PermissionError("group_owner_policy_or_custody_authority_missing")
        # A guard may discover lock loss while reading external owner state.
        self._current()
        return True

    def _load_record(self, key):
        return deepcopy(self._current().payload["records"].get(key))

    def _save_record(self, key, expected_hash, payload):
        self._guard()
        current = self._current().to_payload()
        old = current["records"].get(key)
        if (old["canonical_sha256"] if old else None) != expected_hash:
            raise ValueError("group_owner_record_generation_changed")
        expected = current["canonical_sha256"]
        current["records"][key] = _plain(payload)
        current["canonical_sha256"] = canonical_sha256(current)
        GroupOwnerSession.from_payload(current)
        self.persist_session(expected, deepcopy(current))
        self._guard()
        if self._current().to_payload() != current:
            raise ValueError("group_owner_durable_save_missing")

    def _observe(self, phase, now_ms):
        self._guard()
        raw = self.services.observations_loader(self._current(), phase, now_ms)
        required = (
            {"positions", "snapshots", "clocks"}
            if phase == "pre_release"
            else {"snapshots", "clocks"}
        )
        if (
            not isinstance(raw, dict)
            or set(raw) != required
            or not isinstance(raw["clocks"], dict)
            or not raw["clocks"]
            or any(
                not isinstance(c, Clock) or c.now_ms != now_ms
                for c in raw["clocks"].values()
            )
        ):
            raise ValueError("group_owner_verified_source_clock_missing")
        verified = self._clocks(now_ms)
        if any(clock != verified.get(key) for key, clock in raw["clocks"].items()):
            raise ValueError("group_observation_clock_mismatch")
        self._guard()
        return raw

    def _clocks(self, now_ms):
        self._guard()
        loader = self.services.clock_loader
        if loader is None:
            raise ClockSourceGap("group_clock_provider_missing")
        if not callable(loader):
            raise ValueError("group_clock_provider_invalid")
        clocks = loader(self._current(), now_ms)
        lots = {lot[0]: lot[3] for lot in self.session.group.lots}
        if not isinstance(clocks, dict) or set(clocks) != set(lots):
            raise ValueError("group_clock_lot_coverage_invalid")
        for lot_id, first in lots.items():
            clock = clocks[lot_id]
            if (
                not isinstance(clock, Clock)
                or type(clock.now_ms) is not int
                or clock.now_ms != now_ms
                or now_ms < first
                or clock.verified_halt_ms is not None
                and (
                    type(clock.verified_halt_ms) is not int
                    or not 0 <= clock.verified_halt_ms <= now_ms - first
                )
            ):
                raise ValueError("group_clock_value_invalid")
        self._guard()
        return clocks

    def _write_clock_valid(self, now_ms):
        try:
            return all(
                c.verified_halt_ms is not None for c in self._clocks(now_ms).values()
            )
        except ClockSourceGap:
            return False

    def step(self, now_ms):
        self._guard()
        e, c = self.executor, self.executor.coordinator
        # now_ms is the original owner cycle start, not a market decision clock.
        # Earlier symbols may consume that cycle's time. Every observation and
        # write below uses fresh adapter time and its own approved age bounds.
        if not positive_int(now_ms) or now_ms > c.adapter.now_ms():
            raise ValueError("group_owner_clock_mismatch")
        if (
            datetime.fromtimestamp(now_ms / 1000, KST).date().isoformat()
            != c.group.target.trading_date
        ):
            raise ValueError("group_cross_date_requires_owner_recovery")
        receipt_only = not self._write_clock_valid(c.adapter.now_ms())
        gap = {
            "status": "group_clock_source_gap",
            "group_terminal": False,
            "manager_must_remain": True,
        }
        if self._load_record(whole_exit_key(c)) is not None:
            if self.whole is None:
                raise ValueError("whole_exit_independent_services_required")
            return self.whole.step(receipt_only=receipt_only)
        if self._load_record(e._key("GROUP_TERMINAL")) is not None:
            return e.reconcile_group_terminal()
        records = e.action_records()
        if "SELL_RUNNER" in records:
            result = e.poll_runner(receipt_only=receipt_only)
            if result["status"] == "runner_terminal":
                return e.reconcile_group_terminal()
            if (
                result["status"] == "runner_residual_requires_recovery"
                and result["attempts_exhausted"] is False
            ):
                if receipt_only:
                    return result | gap
                if not callable(self.services.retry_action_loader):
                    return result | {"status": "group_owner_fresh_retry_source_missing"}
                n = result["attempt_no"] + 1
                self._guard()
                action = self.services.retry_action_loader(
                    self._current(), n, c.adapter.now_ms()
                )
                if not isinstance(action, GroupAction):
                    raise ValueError("group_owner_retry_action_invalid")
                return e.retry_runner(action, attempt_no=n)
            return result
        if "RELEASE_RUNNER" in records:
            result = e.reconcile_release()
            if (
                result["status"] != "runner_released_awaiting_decision"
                or result["recovery_deadline_exceeded"]
            ):
                return result
            if receipt_only:
                return result | gap
            receipt = e.released_book.observe(
                **self._observe("released", c.adapter.now_ms())
            )
            if receipt["status"] == "SELL_RUNNER":
                return e.sell_decided_released()
            return {"status": receipt["status"], "group_terminal": False}
        was_frozen = self._load_record(c.key) is not None
        c.freeze()
        # A frozen target may fill before release. This never creates a runner.
        if was_frozen or receipt_only:
            result = e.reconcile_group_terminal()
            if result["status"] != "group_orders_working":
                return result
        if receipt_only:
            return gap
        receipt = e.decision_book.observe(
            **self._observe("pre_release", c.adapter.now_ms())
        )
        if receipt["status"] == "REQUEST_RUNNER_RELEASE":
            return e.request_decided_release()
        return {"status": receipt["status"], "group_terminal": False}

    def validate_terminal(self, receipt):
        self._guard()
        if self._load_record(whole_exit_key(self.executor.coordinator)) is not None:
            if self.whole is None:
                raise ValueError("whole_exit_independent_services_required")
            self.whole.validate_terminal(receipt)
        else:
            validate_group_terminal(receipt, self.executor)
        self._guard()

    def claim_whole_exit(self, request):
        self._guard()
        if self.whole is None:
            raise ValueError("whole_exit_independent_services_required")
        self.whole.claim(request)
