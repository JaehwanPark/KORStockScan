"""Ordered, latency-aware counterfactual exits; never broker execution proof.

Target queue execution is a declared conservative model using marketable bid
depth, not a candle-high touch. Partial executions retain unresolved quantity;
costs are charged once on the complete paired lot, not once per retry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from math import floor
from typing import Sequence

from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.decision import evaluate_exit, _tick_ceiling
from src.trading.order.adaptive_exit.models import (
    Clock,
    DecisionState,
    ExitPolicy,
    Position,
    Snapshot,
    finite,
    positive_int,
)


@dataclass(frozen=True)
class ExecutionModel:
    model_id: str
    cancel_latency_ms: int
    submit_latency_ms: int
    sell_ttl_ms: int
    maximum_sell_attempts: int
    depth_participation: float
    extra_sell_cost_pct: float
    target_queue_confirmations: int
    terminal_residual: str
    # Optional for diagnostics; mandatory for economic policy comparison so
    # slow baseline holdings can be evaluated within the SAME finite horizon.
    horizon_close_lead_ms: int | None = None

    def __post_init__(self):
        if (
            not self.model_id
            or any(
                type(v) is not int or v < 0
                for v in (
                    self.cancel_latency_ms,
                    self.submit_latency_ms,
                )
            )
            or not positive_int(self.sell_ttl_ms)
            or not positive_int(self.maximum_sell_attempts)
            or not positive_int(self.target_queue_confirmations)
            or not finite(self.depth_participation)
            or not 0 < self.depth_participation <= 1
            or not finite(self.extra_sell_cost_pct)
            or self.extra_sell_cost_pct < 0
            or self.terminal_residual != "unresolved_not_zero"
            or self.horizon_close_lead_ms is not None
            and (
                not positive_int(self.horizon_close_lead_ms)
                or self.horizon_close_lead_ms
                <= self.cancel_latency_ms + self.submit_latency_ms
            )
        ):
            raise ValueError("execution_model_requires_explicit_bounded_contract")


@dataclass(frozen=True)
class ExitPath:
    position: Position
    entry_policy_hash: str
    entry_order_key: str
    target_order_key: str
    target_ack_at_ms: int
    horizon_end_ms: int
    source_hash: str
    observations: tuple[tuple[Clock, Snapshot], ...]


def _take_depth(
    snapshot: Snapshot, quantity: int, minimum: float, participation: float
):
    taken, notional = 0, 0.0
    for price, depth in snapshot.bid_levels:
        if price < minimum:
            break
        size = min(quantity - taken, floor(depth * participation))
        taken += size
        notional += size * price
        if taken == quantity:
            break
    return taken, notional


def _advance(state, decision, clock, snapshot, position):
    state = replace(
        state,
        last_observed_at_ms=snapshot.observed_at_ms,
        source_epoch=snapshot.source_epoch,
        sequence=snapshot.sequence,
    )
    if decision.action == "GRANT_EXTENSION":
        state = replace(
            state,
            extensions=1,
            extension_until_active_ms=decision.next_active_deadline_ms,
            extension_granted_at_active_ms=clock.now_ms
            - position.first_fill_at_ms
            - clock.verified_halt_ms,
        )
    return state


def replay_execution(
    path: ExitPath, policy: ExitPolicy, model: ExecutionModel, *, baseline: bool = False
) -> dict:
    p = path.position
    result = {
        "schema": "machine_adaptive_exit_execution_replay_v1",
        "owner_id": p.owner_id,
        "scope_key": p.scope_key,
        "episode_id": p.episode_id,
        "lot_id": p.lot_id,
        "position_epoch": p.position_epoch,
        "policy_hash": policy.policy_hash,
        "entry_policy_hash": path.entry_policy_hash,
        "cost_contract_hash": p.cost_contract_hash,
        "source_hash": path.source_hash,
        "first_fill_at_ms": p.first_fill_at_ms,
        "horizon_end_ms": path.horizon_end_ms,
        "model": asdict(model),
        "model_hash": canonical_sha256(asdict(model)),
        "baseline": baseline,
        "authority": dict(AUTHORITY),
        "actual_broker_terminal": False,
        "counterfactual_exit_resolved": False,
        "net_ev_pct": None,
        "net_pnl_krw": None,
        "entry_notional_krw": p.entry_price * p.open_qty,
        "remaining_quantity": p.open_qty,
        "transitions": [],
        "resolution_reason": "source_contract_missing",
        "closed_at_ms": None,
        "costs_are_modeled_not_exact_broker": True,
        "common_horizon_close_lead_ms": model.horizon_close_lead_ms,
        "horizon_close_is_evaluation_only_not_live_baseline": True,
    }
    if (
        not all(
            isinstance(v, str) and v
            for v in (
                path.entry_policy_hash,
                path.entry_order_key,
                path.target_order_key,
                path.source_hash,
            )
        )
        or not positive_int(path.target_ack_at_ms)
        or not positive_int(path.horizon_end_ms)
        or not p.first_fill_at_ms <= path.target_ack_at_ms < path.horizon_end_ms
        or not path.observations
        or model.horizon_close_lead_ms is not None
        and (model.horizon_close_lead_ms >= path.horizon_end_ms - p.first_fill_at_ms)
    ):
        return result
    initial = DecisionState(
        policy.policy_hash, p.position_epoch, p.first_fill_at_ms, p.open_qty
    )
    # Validate the WHOLE common horizon, even when the baseline exits early.
    # This prevents selecting only winners with short paths for one arm.
    source_state = initial
    last_now = None
    last_halt = 0
    prior_quote_sequence = None
    prior_quote_data = None
    for clock, snapshot in path.observations:
        if snapshot.quote_sequence is not None:
            quote_data = (snapshot.quote_at_ms, snapshot.bid_levels, snapshot.best_ask)
            if (
                type(snapshot.quote_sequence) is not int
                or snapshot.quote_sequence < 0
                or prior_quote_sequence is not None
                and (
                    snapshot.quote_sequence < prior_quote_sequence
                    or snapshot.quote_sequence == prior_quote_sequence
                    and quote_data != prior_quote_data
                )
            ):
                return result | {
                    "resolution_reason": "quote_sequence_conflict_or_regression"
                }
            prior_quote_sequence, prior_quote_data = snapshot.quote_sequence, quote_data
        d = evaluate_exit(policy, p, snapshot, clock, source_state)
        if (
            d.action in ("SOURCE_GAP", "RECOVERY_REQUIRED")
            or last_now is not None
            and clock.now_ms <= last_now
            or clock.verified_halt_ms < last_halt
            or clock.now_ms > path.horizon_end_ms
        ):
            return result | {"resolution_reason": "ordered_path_invalid:" + d.reason}
        source_state = _advance(source_state, d, clock, snapshot, p)
        last_now, last_halt = clock.now_ms, clock.verified_halt_ms
    if (
        path.observations[0][0].now_ms - p.first_fill_at_ms
        > policy.max_observation_gap_ms
        or last_now != path.horizon_end_ms
    ):
        return result | {"resolution_reason": "common_horizon_not_complete"}

    state = initial
    phase, cancel_due, submit_due, expiry, limit = "target", None, None, None, None
    left, proceeds, attempts, queue_hits = p.open_qty, 0.0, 0, 0
    extra_cost_notional = 0.0
    trace = result["transitions"]
    pending_kind = None
    last_quote_key = None

    def transition(now, next_phase, reason):
        trace.append({"at_ms": now, "phase": next_phase, "reason": reason})

    for clock, snapshot in path.observations:
        now = clock.now_ms
        quote_key = (
            snapshot.source_epoch,
            snapshot.quote_sequence
            if snapshot.quote_sequence is not None
            else snapshot.sequence,
        )
        new_quote = quote_key != last_quote_key
        last_quote_key = quote_key
        # A target remains live during cancel latency. At the cancel boundary
        # use conservative target-first ordering, including partial fills.
        if (
            phase in ("target", "cancel")
            and now >= path.target_ack_at_ms
            and new_quote
            and snapshot.quote_at_ms >= path.target_ack_at_ms
        ):
            if snapshot.bid_levels[0][0] >= p.original_target:
                queue_hits += 1
            else:
                queue_hits = 0
            if queue_hits >= model.target_queue_confirmations:
                qty, _ = _take_depth(
                    snapshot, left, p.original_target, model.depth_participation
                )
                left -= qty
                proceeds += qty * p.original_target  # no optimistic price improvement
                if qty:
                    transition(now, phase, "modeled_target_fill")
        if left == 0:
            result["closed_at_ms"] = now
            break
        local = replace(p, open_qty=left)
        state = replace(state, open_qty=left)
        d = evaluate_exit(policy, local, snapshot, clock, state)
        if d.action in ("SOURCE_GAP", "RECOVERY_REQUIRED"):
            return result | {"resolution_reason": d.reason, "remaining_quantity": left}

        if phase == "cancel" and now >= cancel_due:
            transition(now, "residual", "modeled_cancel_terminal")
            if pending_kind == "trail" and d.action == "REQUEST_TRAIL_ARM":
                floor_price = p.entry_price * (1 + p.round_trip_cost_pct / 100)
                stop = _tick_ceiling(
                    max(
                        floor_price,
                        d.executable_bid - policy.trail.gap_ticks * p.tick_size,
                    ),
                    p.tick_size,
                )
                if stop < d.executable_bid:
                    state = replace(
                        state,
                        trail_active=True,
                        high_water=d.executable_bid,
                        stop_price=stop,
                    )
                    phase = "trail"
                    transition(now, phase, "fresh_post_cancel_arm")
                else:
                    phase = "ready"
            else:
                phase = "ready"  # declared offline recipe: exit when arm vanishes
        elif (
            phase == "target"
            and now >= path.target_ack_at_ms
            and model.horizon_close_lead_ms is not None
            and now >= path.horizon_end_ms - model.horizon_close_lead_ms
        ):
            pending_kind = "exit"
            cancel_due = now + model.cancel_latency_ms
            phase = "cancel"
            transition(now, phase, "common_horizon_evaluation_close")
        elif (
            phase == "target"
            and now >= path.target_ack_at_ms
            and not baseline
            and d.action.startswith("REQUEST_")
        ):
            pending_kind = "trail" if d.action == "REQUEST_TRAIL_ARM" else "exit"
            cancel_due = now + model.cancel_latency_ms
            phase = "cancel"
            transition(now, phase, d.reason)
        elif phase == "trail":
            if (
                d.action in ("REQUEST_TRAIL_EXIT", "REQUEST_EARLY_EXIT")
                or model.horizon_close_lead_ms is not None
                and now >= path.horizon_end_ms - model.horizon_close_lead_ms
            ):
                phase = "ready"
                transition(now, phase, d.reason)
            elif d.action == "KEEP_TRAIL":
                state = replace(state, high_water=d.high_water, stop_price=d.stop_price)

        if phase == "ready":
            if attempts >= model.maximum_sell_attempts:
                phase = "unresolved"
                transition(now, phase, "bounded_attempts_exhausted")
            else:
                attempts += 1
                limit = d.worst_bid
                submit_due = now + model.submit_latency_ms
                expiry = submit_due + model.sell_ttl_ms
                phase = "sell"
                transition(now, phase, "marketable_limit_intent")
        elif phase == "sell" and now >= submit_due:
            if now >= expiry:
                # Old sell must be cancelled before another can reserve shares.
                phase = "sell_cancel"
                cancel_due = now + model.cancel_latency_ms
                transition(now, phase, "sell_ttl")
            elif new_quote:
                qty, value = _take_depth(
                    snapshot, left, limit, model.depth_participation
                )
                left -= qty
                proceeds += value
                extra_cost_notional += value
                if left == 0:
                    result["closed_at_ms"] = now
                    break
        elif phase == "sell_cancel":
            qty, value = (
                _take_depth(snapshot, left, limit, model.depth_participation)
                if new_quote
                else (0, 0.0)
            )
            left -= qty
            proceeds += value
            extra_cost_notional += value
            if not left:
                result["closed_at_ms"] = now
                break
            if now >= cancel_due:
                phase = "ready"
                transition(now, phase, "modeled_sell_cancel_terminal")
        state = _advance(state, d, clock, snapshot, local)

    result["remaining_quantity"] = left
    if left:
        # No synthetic horizon liquidation: model residual is censored.
        return result | {"resolution_reason": "right_censored_residual"}
    entry = result["entry_notional_krw"]
    pnl = (
        proceeds
        - entry
        - entry * p.round_trip_cost_pct / 100
        - extra_cost_notional * model.extra_sell_cost_pct / 100
    )
    result.update(
        counterfactual_exit_resolved=True,
        resolution_reason="modeled_complete_lot",
        net_ev_pct=pnl / entry * 100,
        net_pnl_krw=pnl,
    )
    return result


def replay_paired(
    path: ExitPath, policies: Sequence[ExitPolicy], models: Sequence[ExecutionModel]
) -> list[dict]:
    """One lot is never counted as several independent episodes by the caller."""
    return [
        {
            "policy_hash": policy.policy_hash,
            "model_id": model.model_id,
            "baseline": replay_execution(path, policy, model, baseline=True),
            "candidate": replay_execution(path, policy, model),
        }
        for policy in policies
        for model in models
    ]
