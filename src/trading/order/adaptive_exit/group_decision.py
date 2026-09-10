"""Pre-release group decisions; no policy approval, broker call or trail arming.

Runner depth is consumed once in the explicitly approved allocation lot order.
Nonrunner decisions are standalone target-retention diagnostics, NOT additive
execution/PnL estimates. A whole-target or mixed decision needs another executor.
The original owner's lock and atomic CAS store own the decision book. No live
launcher supplies this service. A source-only receipt never authorizes a write.
"""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime
import json

from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    canonical_sha256,
    parse_exit_policy,
)
from .broker import KST
from .decision import evaluate_exit
from .models import Clock, DecisionState, Position, Snapshot, finite, positive_int
from .target_group import _digest

SCHEMA = "machine_adaptive_exit_group_decision_v1"
BOOK_SCHEMA = "machine_adaptive_exit_group_decision_book_v1"
DEPTH_RULE = "runner_depth_once_in_declared_lot_order_v1"
REQUESTS = {"REQUEST_TRAIL_ARM", "REQUEST_EARLY_EXIT"}


def classify_group_request(actions, open_runners):
    """One shared runtime/replay routing rule, not an execution permission."""
    requested = {lot for lot, action in actions.items() if action in REQUESTS}
    if "RECOVERY_REQUIRED" in actions.values():
        return "RECOVERY_REQUIRED"
    if "SOURCE_GAP" in actions.values():
        return "SOURCE_GAP"
    if not requested:
        return "KEEP_TARGET"
    if (
        requested == set(open_runners)
        and requested < set(actions)
        and len({actions[lot] for lot in requested}) == 1
    ):
        return "REQUEST_RUNNER_RELEASE"
    return "UNSUPPORTED_GROUP_EXIT_REQUIRES_OWNER_RECOVERY"


def _plain(value):
    # Also rejects NaN/Infinity and normalizes tuple/list at the durable boundary.
    return json.loads(json.dumps(value, allow_nan=False))


def _policy(group, allocation, payload):
    allocation.validate(group)
    policy = parse_exit_policy(payload)
    if (
        policy.policy_hash != allocation.policy_hash
        or policy.scope_key != group.scope.key
        or (
            policy.mode != "time_progress_exit"
            and set(policy.runner_lot_ids) != set(allocation.runner_lot_ids)
        )
    ):
        raise ValueError("group_decision_policy_binding_invalid")
    return policy


def _consume(depth, quantity):
    result = []
    while quantity and depth:
        price, available = depth[0]
        take = min(quantity, available)
        result.append((price, take))
        quantity -= take
        if take == available:
            depth.pop(0)
        else:
            depth[0] = (price, available - take)
    return tuple(result)


def _raw_depth(shared):
    """Validate every level before allocating a shared book, even unused depth."""
    depth, last = [], None
    valid = finite(shared["best_ask"]) and shared["best_ask"] > 0
    levels = shared["bid_levels"]
    if not isinstance(levels, (list, tuple)):
        valid = False
        levels = []
    for level in levels:
        if not isinstance(level, (list, tuple)) or len(level) != 2:
            valid = False
            continue
        price, qty = level
        if not (
            finite(price)
            and price > 0
            and positive_int(qty)
            and (last is None or price < last)
            and finite(shared["best_ask"])
            and price < shared["best_ask"]
        ):
            valid = False
            continue
        depth.append((price, qty))
        last = price
    return depth, valid


def evaluate_group_exit(*, group, allocation, policy_payload, inputs):
    """Recomputable intent with exact frozen BOOK quantities and past-only data.

    Inputs contain target_filled_qty, freeze_source_hash, frozen_at_ms, and a row
    per open BOOK lot (position/snapshot/clock/previous_state). They must come from
    the original owner's frozen group, cost provenance and ordered market source.
    No broker BUY-lot SELL attribution or true fill timestamp is inferred here.
    Malformed contracts raise; valid-but-unusable market data returns SOURCE_GAP.
    """
    policy = _policy(group, allocation, policy_payload)
    inputs = _plain(inputs)
    if (
        set(inputs)
        != {"target_filled_qty", "freeze_source_hash", "frozen_at_ms", "lots"}
        or not _digest(inputs["freeze_source_hash"])
        or not positive_int(inputs["frozen_at_ms"])
    ):
        raise ValueError("group_decision_frozen_input_invalid")
    balances = allocation.balances(group, inputs["target_filled_qty"])
    active = {r["lot_id"]: r for r in balances if r["book_open_qty"]}
    if (
        not active
        or not isinstance(inputs["lots"], dict)
        or set(inputs["lots"]) != set(active)
    ):
        raise ValueError("group_decision_open_lot_census_mismatch")
    lots = {r[0]: r for r in group.lots}
    parsed, shared = {}, None
    for lot in allocation.lot_order:
        if lot not in active:
            continue
        row = inputs["lots"][lot]
        if set(row) != {"position", "snapshot", "clock", "previous_state"}:
            raise ValueError("group_decision_lot_schema_invalid")
        p, s, clock, old = (
            Position(**row["position"]),
            Snapshot(**row["snapshot"]),
            Clock(**row["clock"]),
            DecisionState(**row["previous_state"]),
        )
        admitted = lots[lot]
        if (
            p.owner_id != group.scope.owner
            or p.scope_key != group.scope.key
            or p.episode_id != group.episode_id
            or p.lot_id != lot
            or p.open_qty != active[lot]["book_open_qty"]
            or not positive_int(p.open_qty)
            or p.first_fill_at_ms != admitted[3]
            or type(p.first_fill_at_ms) is not int
            or p.entry_price != admitted[4]
            or p.original_target != group.target_price
            or not _digest(p.cost_contract_hash)
            or not _digest(s.source_hash)
            or (
                s.quote_sequence is not None
                and (type(s.quote_sequence) is not int or s.quote_sequence < 0)
            )
            or old.trail_active is not False
            or old.high_water is not None
            or old.stop_price is not None
            or not positive_int(clock.now_ms)
            or clock.now_ms < inputs["frozen_at_ms"]
            or datetime.fromtimestamp(clock.now_ms / 1000, KST).date().isoformat()
            != group.target.trading_date
            or datetime.fromtimestamp(inputs["frozen_at_ms"] / 1000, KST)
            .date()
            .isoformat()
            != group.target.trading_date
        ):
            raise ValueError("group_decision_lot_identity_or_pre_release_state_invalid")
        market = asdict(s)
        for name in ("position_epoch", "supportive", "improvement_bps"):
            market.pop(name)
        market["evaluation_now_ms"] = clock.now_ms
        if shared is not None and market != shared:
            raise ValueError("group_decision_requires_one_exact_market_snapshot")
        shared = market
        parsed[lot] = p, s, clock, old
    # Validate the WHOLE raw book before allocating, including unused levels.
    depth, raw_valid = _raw_depth(shared)
    results, next_states = {}, {}
    for lot, (p, s, clock, old) in parsed.items():
        runner = active[lot]["runner"]
        local = _consume(depth, p.open_qty) if runner and raw_valid else s.bid_levels
        decision = evaluate_exit(policy, p, replace(s, bid_levels=local), clock, old)
        if not raw_valid:
            decision = replace(
                decision,
                action="SOURCE_GAP",
                reason="invalid_shared_bid_depth",
                executable_bid=None,
                worst_bid=None,
                progress=None,
                net_return_pct=None,
            )
        results[lot] = asdict(decision) | {
            "depth_role": DEPTH_RULE if runner else "standalone_nonrunner_diagnostic",
        }
        state = old
        if decision.action not in {"SOURCE_GAP", "RECOVERY_REQUIRED"}:
            state = replace(
                old,
                last_observed_at_ms=s.observed_at_ms,
                source_epoch=s.source_epoch,
                sequence=s.sequence,
            )
            if decision.action == "GRANT_EXTENSION":
                state = replace(
                    state,
                    extensions=1,
                    extension_until_active_ms=decision.next_active_deadline_ms,
                    extension_granted_at_active_ms=clock.now_ms
                    - p.first_fill_at_ms
                    - clock.verified_halt_ms,
                )
        next_states[lot] = asdict(state)
    actions = {lot: row["action"] for lot, row in results.items()}
    requested = [lot for lot, action in actions.items() if action in REQUESTS]
    open_runners = {lot for lot in active if active[lot]["runner"]}
    status = classify_group_request(actions, open_runners)
    if status in {"SOURCE_GAP", "RECOVERY_REQUIRED"}:
        # Atomic observation: partial success cannot consume an extension/epoch.
        next_states = {lot: asdict(row[3]) for lot, row in parsed.items()}
    result = {
        "schema": SCHEMA,
        "group_hash": allocation.group_hash,
        "allocation_hash": canonical_sha256(asdict(allocation)),
        "policy_payload": _plain(policy_payload),
        "depth_rule": DEPTH_RULE,
        "inputs": inputs,
        "book_lots": balances,
        "lot_decisions": results,
        "next_states": next_states,
        "status": status,
        "requested_lot_ids": requested,
        "release_quantity": (
            sum(active[x]["book_open_qty"] for x in open_runners)
            if status == "REQUEST_RUNNER_RELEASE"
            else None
        ),
        "observed_at_ms": shared["evaluation_now_ms"],
        "source_hash": shared["source_hash"],
        "authority": dict(AUTHORITY),
        "actual_lot_fill_attribution": None,
        "realized_pnl": None,
        "group_terminal": False,
        "trail_armed": False,
    }
    result["canonical_sha256"] = canonical_sha256(result)
    return _plain(result)


def validate_group_decision(receipt, *, group, allocation, policy_payload):
    expected = evaluate_group_exit(
        group=group,
        allocation=allocation,
        policy_payload=policy_payload,
        inputs=receipt["inputs"],
    )
    if (
        _plain(receipt) != expected
        or canonical_sha256(receipt) != expected["canonical_sha256"]
    ):
        raise ValueError("group_decision_recomputed_receipt_mismatch")
    return expected


class GroupDecisionBook:
    """Durable pre-release state + latest veto, under the coordinator owner lock.

    Malformed observations persist a veto before evaluation and cannot leave an old
    release usable. Saving failure is fail-closed. After an execution action slot is
    created, observations are frozen; recovery uses that exact action, never a new
    decision ID. Actual fresh market/approval validation still belongs to the
    executor's mandatory independent authorize_action callback.
    """

    def __init__(self, *, coordinator, policy_payload):
        _policy(coordinator.group, coordinator.allocation, policy_payload)
        self.c = coordinator
        self.policy_payload = _plain(policy_payload)
        self.binding = {
            "group_binding_hash": coordinator.binding_hash,
            "policy_hash": coordinator.allocation.policy_hash,
            "depth_rule": DEPTH_RULE,
        }
        self.binding_hash = canonical_sha256(self.binding)
        self.key = canonical_sha256(
            {"group_slot": coordinator.key, "role": BOOK_SCHEMA}
        )
        self._observation_healthy = True

    def _authorize(self):
        self.c._authorize()
        policy = _policy(self.c.group, self.c.allocation, self.policy_payload)
        if (
            self.binding
            != {
                "group_binding_hash": self.c.binding_hash,
                "policy_hash": policy.policy_hash,
                "depth_rule": DEPTH_RULE,
            }
            or canonical_sha256(self.binding) != self.binding_hash
        ):
            raise ValueError("group_decision_book_binding_changed")

    def _read(self):
        self._authorize()
        raw = deepcopy(self.c.load_record(self.key))
        if raw is None:
            return None
        if (
            not isinstance(raw, dict)
            or set(raw)
            != {"schema", "binding_hash", "receipt", "veto", "canonical_sha256"}
            or raw.get("schema") != BOOK_SCHEMA
            or raw.get("binding_hash") != self.binding_hash
            or raw.get("canonical_sha256") != canonical_sha256(raw)
            or raw.get("veto") not in (None, "observation_pending_or_invalid")
        ):
            raise ValueError("group_decision_book_saved_contract_invalid")
        if raw["receipt"] is not None:
            validate_group_decision(
                raw["receipt"],
                group=self.c.group,
                allocation=self.c.allocation,
                policy_payload=self.policy_payload,
            )
            frozen = self.c._read()
            if raw["receipt"]["observed_at_ms"] > self.c.adapter.now_ms():
                raise ValueError("group_decision_saved_clock_in_future")
            if frozen is None or any(
                raw["receipt"]["inputs"][k] != frozen[v]
                for k, v in (
                    ("target_filled_qty", "initial_filled_qty"),
                    ("freeze_source_hash", "freeze_source_hash"),
                    ("frozen_at_ms", "frozen_at_ms"),
                )
            ):
                raise ValueError("group_decision_book_frozen_source_changed")
        return raw

    def _save(self, previous, receipt, veto):
        self._authorize()
        raw = {
            "schema": BOOK_SCHEMA,
            "binding_hash": self.binding_hash,
            "receipt": receipt,
            "veto": veto,
        }
        raw["canonical_sha256"] = canonical_sha256(raw)
        self.c.save_record(
            self.key, previous["canonical_sha256"] if previous else None, deepcopy(raw)
        )
        if self._read() != raw:
            raise ValueError("group_decision_book_durable_save_missing")
        return raw

    def observe(self, *, positions, snapshots, clocks):
        self._authorize()
        frozen = self.c.freeze()
        action_key = canonical_sha256(
            {"group_slot": self.c.key, "execution_kind": "RELEASE_RUNNER"}
        )
        if (
            frozen["phase"] != "ALLOCATION_FROZEN"
            or self.c.load_record(action_key) is not None
        ):
            raise ValueError("group_decision_already_committed_use_execution_recovery")
        # Also forbid adopting an externally reserved/ambiguous cancel.
        context = replace(
            self.c.adapter.context, client_intent_id=self.c.cancel_client_id
        )
        if self.c.adapter.registry.intent_for_client(context=context) is not None:
            raise ValueError("group_decision_external_cancel_requires_recovery")
        old = self._read()
        previous_receipt = old["receipt"] if old else None
        position_bound = previous_receipt is not None and any(
            state["last_observed_at_ms"] is not None
            for state in previous_receipt["next_states"].values()
        )
        self._observation_healthy = False
        pending = self._save(old, previous_receipt, "observation_pending_or_invalid")
        active = {
            r["lot_id"]
            for r in self.c.allocation.balances(
                self.c.group, frozen["initial_filled_qty"]
            )
            if r["book_open_qty"]
        }
        if any(
            not isinstance(x, dict) or set(x) != active
            for x in (positions, snapshots, clocks)
        ):
            raise ValueError("group_decision_open_lot_census_mismatch")
        rows = {}
        for lot in self.c.allocation.lot_order:
            if lot not in active:
                continue
            p = positions[lot]
            now = self.c.adapter.now_ms()
            if (
                not positive_int(clocks[lot].now_ms)
                or not 0
                <= now - clocks[lot].now_ms
                <= self.policy_payload["max_quote_age_ms"]
            ):
                raise ValueError("group_decision_clock_not_current")
            if position_bound:
                if asdict(p) != previous_receipt["inputs"]["lots"][lot]["position"]:
                    raise ValueError("group_decision_position_or_cost_epoch_changed")
                state = previous_receipt["next_states"][lot]
            else:
                state = asdict(
                    DecisionState(
                        self.c.allocation.policy_hash,
                        p.position_epoch,
                        p.first_fill_at_ms,
                        p.open_qty,
                    )
                )
            rows[lot] = {
                "position": asdict(p),
                "snapshot": asdict(snapshots[lot]),
                "clock": asdict(clocks[lot]),
                "previous_state": state,
            }
        receipt = evaluate_group_exit(
            group=self.c.group,
            allocation=self.c.allocation,
            policy_payload=self.policy_payload,
            inputs={
                "target_filled_qty": frozen["initial_filled_qty"],
                "freeze_source_hash": frozen["freeze_source_hash"],
                "frozen_at_ms": frozen["frozen_at_ms"],
                "lots": rows,
            },
        )
        self._save(pending, receipt, None)
        self._observation_healthy = True
        return receipt

    def release_action(self):
        if not self._observation_healthy:
            raise ValueError("group_latest_observation_not_durably_complete")
        raw = self._read()
        receipt = raw["receipt"] if raw else None
        if (
            not raw
            or raw["veto"] is not None
            or receipt is None
            or receipt["status"] != "REQUEST_RUNNER_RELEASE"
        ):
            raise ValueError("group_latest_decision_does_not_allow_runner_release")
        frozen = self.c._read()
        if receipt["release_quantity"] != frozen["requested_qty"]:
            raise ValueError("group_decision_release_quantity_conflict")
        return {
            "kind": "RELEASE_RUNNER",
            "decision_receipt_hash": receipt["canonical_sha256"],
            "source_hash": receipt["source_hash"],
            "observed_at_ms": receipt["observed_at_ms"],
            "limit_price": None,
        }

    def validate_write(self, action):
        """Fresh quote check at transport time, not merely at decision time.

        Read-only ACK recovery may reuse the immutable receipt. A new write may not.
        The independent validator must still check actual current source and safety;
        hashes/age alone cannot prove a source has not been superseded outside this book.
        """
        if action != self.release_action():
            raise ValueError("group_execution_requires_latest_recomputed_decision")
        raw = self._read()
        now = self.c.adapter.now_ms()
        if any(
            not 0
            <= now - row["snapshot"]["quote_at_ms"]
            <= self.policy_payload["max_quote_age_ms"]
            for row in raw["receipt"]["inputs"]["lots"].values()
        ):
            raise ValueError("group_decision_executable_quote_now_stale")
