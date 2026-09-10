"""Confirmed runner release -> durable trailing/first SELL decision.

Reuses the same pure decision kernel and the original owner's atomic store.
The book cannot release a reservation, approve a policy, submit an order, or
complete an episode. The executor independently rechecks policy and all guards.
Unselected target lots are not implicitly sold or assigned broker lot profits.
"""

from copy import deepcopy
from dataclasses import asdict, replace

from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from .decision import _tick_ceiling, evaluate_exit
from .group_decision import (
    DEPTH_RULE,
    _consume,
    _plain,
    _policy,
    _raw_depth,
    validate_group_decision,
)
from .models import Clock, DecisionState, Position, Snapshot, positive_int
from .target_group import _digest

SCHEMA = "machine_adaptive_exit_released_runner_decision_v1"
BOOK_SCHEMA = "machine_adaptive_exit_released_runner_book_v1"


def evaluate_released_runners(*, group, allocation, policy_payload, inputs):
    """Past-only replayable decisions after a full requested partial cancel.

    The caller validates the registry release proof. This pure function binds its
    hash and exact BOOK quantities, not just a cancel ACK. A vanished arm exits only
    with fresh executable data, matching the existing single-lot driver contract.
    Mixed runner actions require a selective-lot executor, not pooled over-selling.
    """
    policy = _policy(group, allocation, policy_payload)
    inputs = _plain(inputs)
    if set(inputs) != {"pre_release", "release", "lots"}:
        raise ValueError("released_runner_inputs_invalid")
    pre, release = inputs["pre_release"], inputs["release"]
    validate_group_decision(
        pre, group=group, allocation=allocation, policy_payload=policy_payload
    )
    if pre["status"] != "REQUEST_RUNNER_RELEASE":
        raise ValueError("released_runner_original_intent_required")
    balances = allocation.balances(group, release["target_filled_qty"])
    active = {
        r["lot_id"]: r["book_open_qty"]
        for r in balances
        if r["runner"] and r["book_open_qty"]
    }
    if (
        not active
        or not isinstance(inputs["lots"], dict)
        or set(inputs["lots"]) != set(active)
        or not positive_int(release["observed_at_ms"])
        or release["observed_at_ms"] < pre["observed_at_ms"]
        or type(release["runner_released_qty"]) is not int
        or sum(active.values()) != release["runner_released_qty"]
        or release["runner_released_qty"] != pre["release_quantity"]
        or release["sell_authority"] is not False
        or release["actual_lot_fill_attribution"] is not None
        or release["realized_pnl"] is not None
    ):
        raise ValueError("released_runner_exact_quantity_or_intent_conflict")
    parsed, shared = {}, None
    for lot in allocation.lot_order:
        if lot not in active:
            continue
        row = inputs["lots"][lot]
        if set(row) != {"position", "snapshot", "clock", "previous_state"}:
            raise ValueError("released_runner_lot_schema_invalid")
        p, s, clock, old = (
            Position(**row["position"]),
            Snapshot(**row["snapshot"]),
            Clock(**row["clock"]),
            DecisionState(**row["previous_state"]),
        )
        if (
            row["position"] != pre["inputs"]["lots"][lot]["position"]
            or type(p.open_qty) is not int
            or p.open_qty != active[lot]
            or not positive_int(clock.now_ms)
            or clock.now_ms < release["observed_at_ms"]
            or not _digest(s.source_hash)
            or (
                s.quote_sequence is not None
                and (type(s.quote_sequence) is not int or s.quote_sequence < 0)
            )
            or (
                not old.trail_active
                and (old.high_water is not None or old.stop_price is not None)
            )
        ):
            raise ValueError("released_runner_frozen_position_or_state_changed")
        market = asdict(s)
        for name in ("position_epoch", "supportive", "improvement_bps"):
            market.pop(name)
        market["evaluation_now_ms"] = clock.now_ms
        if shared is not None and market != shared:
            raise ValueError("released_runner_shared_snapshot_required")
        shared = market
        parsed[lot] = p, s, clock, old
    depth, valid = _raw_depth(shared)
    results, states, commands = {}, {}, {}
    for lot, (p, s, clock, old) in parsed.items():
        local = _consume(depth, p.open_qty) if valid else s.bid_levels
        decision = evaluate_exit(policy, p, replace(s, bid_levels=local), clock, old)
        if not valid:
            decision = replace(
                decision, action="SOURCE_GAP", reason="invalid_shared_bid_depth"
            )
        state, command = old, "RECOVERY_REQUIRED"
        if decision.action not in {"SOURCE_GAP", "RECOVERY_REQUIRED"}:
            state = replace(
                old,
                last_observed_at_ms=s.observed_at_ms,
                source_epoch=s.source_epoch,
                sequence=s.sequence,
            )
            original = pre["lot_decisions"][lot]["action"]
            command = "SELL_RUNNER"
            if old.trail_active and decision.action == "KEEP_TRAIL":
                state = replace(
                    state,
                    high_water=decision.high_water,
                    stop_price=decision.stop_price,
                )
                command = "KEEP_TRAIL"
            elif (
                not old.trail_active
                and original == "REQUEST_TRAIL_ARM"
                and decision.action == "REQUEST_TRAIL_ARM"
            ):
                floor = p.entry_price * (1 + p.round_trip_cost_pct / 100)
                stop = _tick_ceiling(
                    max(
                        floor,
                        decision.executable_bid - policy.trail.gap_ticks * p.tick_size,
                    ),
                    p.tick_size,
                )
                if stop < decision.executable_bid:
                    state = replace(
                        state,
                        trail_active=True,
                        high_water=decision.executable_bid,
                        stop_price=stop,
                    )
                    command = "ARM_TRAIL"
        else:
            command = decision.action
        results[lot] = asdict(decision) | {"command": command, "depth_role": DEPTH_RULE}
        commands[lot], states[lot] = command, asdict(state)
    values = set(commands.values())
    if "RECOVERY_REQUIRED" in values:
        status = "RECOVERY_REQUIRED"
    elif "SOURCE_GAP" in values:
        status = "SOURCE_GAP"
    elif values == {"SELL_RUNNER"}:
        status = "SELL_RUNNER"
    elif values <= {"ARM_TRAIL", "KEEP_TRAIL"}:
        status = "TRAIL_ACTIVE"
    else:
        status = "SELECTIVE_RUNNER_EXIT_REQUIRES_RECOVERY"
    if status in {
        "SOURCE_GAP",
        "RECOVERY_REQUIRED",
        "SELECTIVE_RUNNER_EXIT_REQUIRES_RECOVERY",
    }:
        states = {lot: asdict(row[3]) for lot, row in parsed.items()}
    result = {
        "schema": SCHEMA,
        "inputs": inputs,
        "group_hash": allocation.group_hash,
        "policy_hash": policy.policy_hash,
        "depth_rule": DEPTH_RULE,
        "lot_decisions": results,
        "next_states": states,
        "status": status,
        "quantity": sum(active.values()),
        "limit_price": (
            min(row["worst_bid"] for row in results.values())
            if status == "SELL_RUNNER"
            else None
        ),
        "source_hash": shared["source_hash"],
        "observed_at_ms": shared["evaluation_now_ms"],
        "authority": dict(AUTHORITY),
        "actual_lot_fill_attribution": None,
        "realized_pnl": None,
        "group_terminal": False,
    }
    return _plain(result | {"canonical_sha256": canonical_sha256(result)})


class ReleasedRunnerBook:
    """Pending-veto -> evaluate -> atomic state -> first SELL consumer.

    No new observation may replace an already durable SELL intent. Restart retains
    the latest stop and the original first-fill/extension clocks. Registry/cancel
    proofs and policy authorization are re-read before every observation and write.
    """

    def __init__(self, executor):
        self.e, self.c = executor, executor.coordinator
        self.key = canonical_sha256({"group_slot": self.c.key, "role": BOOK_SCHEMA})
        self._healthy = True

    def _base(self):
        e, c = self.e, self.c
        e._authorize()
        frozen = c._read()
        pre = e.decision_book._read()
        action = e._read("RELEASE_RUNNER")
        cancel = e._intent(action) if action is not None else None
        if (
            frozen is None
            or frozen["phase"] != "RELEASE_RECONCILED"
            or pre is None
            or pre["veto"] is not None
            or pre["receipt"] is None
            or action is None
            or cancel is None
            or cancel["state"] != "ORDER_TERMINAL"
            or action["action"] != e.decision_book.release_action()
            or canonical_sha256(cancel.get("cancel_reconciliation", {}))
            != frozen["release"]["cancel_proof_hash"]
            or c._target().get("canceled_qty") != frozen["requested_qty"]
        ):
            raise ValueError("released_runner_confirmed_original_release_required")
        return pre["receipt"], frozen["release"]

    def _evaluate(self, inputs):
        return evaluate_released_runners(
            group=self.c.group,
            allocation=self.c.allocation,
            policy_payload=self.e.decision_book.policy_payload,
            inputs=inputs,
        )

    def _read(self):
        pre, release = self._base()
        raw = deepcopy(self.c.load_record(self.key))
        if raw is None:
            return None
        if (
            not isinstance(raw, dict)
            or set(raw)
            != {"schema", "binding_hash", "receipt", "veto", "canonical_sha256"}
            or raw.get("schema") != BOOK_SCHEMA
            or raw.get("binding_hash") != self.e.binding_hash
            or raw.get("canonical_sha256") != canonical_sha256(raw)
            or raw.get("veto") not in (None, "observation_pending_or_invalid")
        ):
            raise ValueError("released_runner_saved_book_invalid")
        receipt = raw["receipt"]
        if receipt is not None:
            if (
                receipt != self._evaluate(receipt["inputs"])
                or receipt["inputs"]["pre_release"] != pre
                # Reconciliation may refresh timestamps and target fills while
                # freed runner capacity stays fixed. Freeze the FIRST proof used.
                or receipt["inputs"]["release"]["cancel_proof_hash"]
                != release["cancel_proof_hash"]
                or receipt["inputs"]["release"]["runner_released_qty"]
                != release["runner_released_qty"]
                or receipt["observed_at_ms"] > self.c.adapter.now_ms()
            ):
                raise ValueError("released_runner_recomputed_receipt_conflict")
        return raw

    def _save(self, previous, receipt, veto):
        self._base()
        raw = {
            "schema": BOOK_SCHEMA,
            "binding_hash": self.e.binding_hash,
            "receipt": receipt,
            "veto": veto,
        }
        raw["canonical_sha256"] = canonical_sha256(raw)
        self.c.save_record(
            self.key, previous["canonical_sha256"] if previous else None, deepcopy(raw)
        )
        if self._read() != raw:
            raise ValueError("released_runner_durable_save_missing")
        return raw

    def observe(self, *, snapshots, clocks):
        pre, release = self._base()
        if (
            self.c.load_record(self.e._key("GROUP_TERMINAL")) is not None
            or self.e._read("SELL_RUNNER") is not None
        ):
            raise ValueError("released_runner_already_committed_use_execution_recovery")
        client = self.e._client("SELL_RUNNER", self.c.group.target)
        if (
            self.c.adapter.registry.intent_for_client(
                context=replace(self.c.adapter.context, client_intent_id=client)
            )
            is not None
        ):
            raise ValueError("released_runner_external_sell_requires_recovery")
        old = self._read()
        previous = old["receipt"] if old else None
        self._healthy = False
        pending = self._save(old, previous, "observation_pending_or_invalid")
        active = set(pre["requested_lot_ids"])
        if any(
            not isinstance(rows, dict) or set(rows) != active
            for rows in (snapshots, clocks)
        ):
            raise ValueError("released_runner_open_lot_census_mismatch")
        lots = {}
        for lot in active:
            clock = clocks[lot]
            if (
                not isinstance(clock, Clock)
                or not 0
                <= self.c.adapter.now_ms() - clock.now_ms
                <= self.e.bounds.max_decision_age_ms
            ):
                raise ValueError("released_runner_clock_not_current")
            lots[lot] = {
                "position": pre["inputs"]["lots"][lot]["position"],
                "snapshot": asdict(snapshots[lot]),
                "clock": asdict(clock),
                "previous_state": (
                    previous["next_states"][lot]
                    if previous
                    else pre["next_states"][lot]
                ),
            }
        receipt = self._evaluate(
            {
                "pre_release": pre,
                "release": previous["inputs"]["release"] if previous else release,
                "lots": lots,
            }
        )
        self._save(pending, receipt, None)
        self._healthy = True
        return receipt

    def sell_action(self):
        if not self._healthy:
            raise ValueError("released_runner_latest_observation_not_durable")
        raw = self._read()
        r = raw["receipt"] if raw else None
        if (
            not raw
            or raw["veto"] is not None
            or r is None
            or r["status"] != "SELL_RUNNER"
        ):
            raise ValueError("released_runner_latest_decision_does_not_allow_sell")
        price = r["limit_price"]
        if not isinstance(price, (int, float)) or int(price) != price:
            raise ValueError("released_runner_exact_limit_price_required")
        return {
            "kind": "SELL_RUNNER",
            "decision_receipt_hash": r["canonical_sha256"],
            "source_hash": r["source_hash"],
            "observed_at_ms": r["observed_at_ms"],
            "limit_price": int(price),
        }

    def validate_write(self, action):
        if action != self.sell_action():
            raise ValueError("released_runner_latest_recomputed_sell_required")
        raw = self._read()
        now = self.c.adapter.now_ms()
        if any(
            not 0
            <= now - row["snapshot"]["quote_at_ms"]
            <= self.e.decision_book.policy_payload["max_quote_age_ms"]
            for row in raw["receipt"]["inputs"]["lots"].values()
        ):
            raise ValueError("released_runner_quote_now_stale")
