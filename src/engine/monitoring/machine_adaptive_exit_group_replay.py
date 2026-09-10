"""Coupled shared-target replay, consumed by the existing postclose study.

Liquidity is consumed once per quote by target and working runner together.
Lot economics use explicit frozen BOOK allocation, never broker lot labels.
No live group approval, broker call or additional strategy grid is supplied.
"""

from dataclasses import asdict, replace
from math import floor

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.decision import evaluate_exit, _tick_ceiling
from src.trading.order.adaptive_exit.group_runtime import RULE
from src.trading.order.adaptive_exit.group_decision import (
    _consume,
    classify_group_request,
)
from src.trading.order.adaptive_exit.models import DecisionState
from .machine_adaptive_exit_execution_replay import _advance, _empty_result, _path_error

GEOMETRY = "shared_target_single_depth_frozen_book_research_v1"


def replay_group_execution(paths, policy, model, *, lot_order, baseline=False):
    """One target/one runner order, with sequential whole-horizon cancellation.

    Policy requests use the existing runtime's exact strict-subset rule. Common
    horizon liquidation is evaluation-only for both arms. The whole order waits
    for both prior orders to cancel; it cannot spend the working runner's shares.
    Partial-cancel quantity changes and unsupported policy requests are censored.
    """
    if (
        len(paths) < 2
        or not isinstance(lot_order, tuple)
        or len(set(lot_order)) != len(lot_order)
        or len({p.position.lot_id for p in paths}) != len(paths)
        or set(lot_order) != {p.position.lot_id for p in paths}
    ):
        raise ValueError("complete_shared_target_lot_order_required")
    by_lot = {p.position.lot_id: p for p in paths}
    paths = [by_lot[k] for k in lot_order]
    first = paths[0]

    def identity(p):
        return (
            p.position.owner_id,
            p.position.scope_key,
            p.position.episode_id,
            p.position.original_target,
            p.position.cost_contract_hash,
            p.position.round_trip_cost_pct,
            p.entry_policy_hash,
            p.target_order_key,
            p.target_ack_at_ms,
            p.horizon_end_ms,
        )

    if (
        any(identity(p) != identity(first) for p in paths)
        or len({p.entry_order_key for p in paths}) != len(paths)
        or any(p.entry_order_key == p.target_order_key for p in paths)
    ):
        raise ValueError("shared_target_identity_or_cost_mismatch")
    runners = set(policy.runner_lot_ids).intersection(lot_order)
    if policy.trail is not None and not (runners and runners < set(lot_order)):
        raise ValueError("partial_trailing_requires_nonempty_strict_lot_subset")
    results = {
        k: _empty_result(by_lot[k], policy, model, baseline=baseline) for k in lot_order
    }
    target = {k: by_lot[k].position.open_qty for k in lot_order}
    released = dict.fromkeys(lot_order, 0)
    # The current SELL's reservation is NOT all released shares. Whole-target
    # cancellation may release more while an older runner still works.
    working = dict.fromkeys(lot_order, 0)
    proceeds, extra = dict.fromkeys(lot_order, 0.0), dict.fromkeys(lot_order, 0.0)
    trace = []
    binding = {
        "geometry": GEOMETRY,
        "target_order_key": first.target_order_key,
        "lot_order": list(lot_order),
        "runner_lot_ids": sorted(runners),
        "allocation_rule": RULE,
        "path_hashes": [p.source_hash for p in paths],
        "policy_hash": policy.policy_hash,
        "model_hash": results[lot_order[0]]["model_hash"],
        "cancel_barrier_model": "target_then_working_runner_sequential",
        "runner_state_model": "frozen_pre_release_until_cancel_terminal",
        "attempt_budget": "per_runner_or_whole_successor_chain",
        "runtime_geometry_approved": False,
    }

    def finish(error=None):
        for k, row in results.items():
            p = by_lot[k].position
            left = target[k] + released[k]
            row.update(
                remaining_quantity=left,
                transitions=list(trace),
                group_execution=dict(binding),
                group_execution_hash=canonical_sha256(binding),
                modeled_book_allocation=True,
                actual_lot_fill_attribution=None,
                resolution_reason=error or "right_censored_residual",
            )
            if not left and error is None:
                entry = row["entry_notional_krw"]
                pnl = proceeds[k] - entry - entry * p.round_trip_cost_pct / 100
                pnl -= extra[k] * model.extra_sell_cost_pct / 100
                row.update(
                    counterfactual_exit_resolved=True,
                    resolution_reason="modeled_complete_group_book_lot",
                    net_pnl_krw=pnl,
                    net_ev_pct=pnl / entry * 100,
                )
        return [results[k] for k in lot_order]

    for p in paths:
        error = _path_error(p, policy, model)
        if error:
            return finish("group_path_invalid:" + error)
    timelines = {
        k: {
            c.now_ms: (c, s)
            for c, s in by_lot[k].observations
            if c.now_ms >= first.target_ack_at_ms
        }
        for k in lot_order
    }
    times = tuple(timelines[lot_order[0]])
    if not times or any(tuple(t) != times for t in timelines.values()):
        return finish("shared_target_exact_timeline_missing")
    for now in times:
        markets = []
        for k in lot_order:
            raw = asdict(timelines[k][now][1])
            for field in ("position_epoch", "supportive", "improvement_bps"):
                raw.pop(field)
            markets.append(raw)
        if any(m != markets[0] for m in markets):
            return finish("shared_target_market_identity_mismatch")
    states = {
        k: DecisionState(
            policy.policy_hash,
            by_lot[k].position.position_epoch,
            by_lot[k].position.first_fill_at_ms,
            target[k],
        )
        for k in lot_order
    }
    book_order = tuple(k for k in lot_order if k not in runners) + tuple(
        k for k in lot_order if k in runners
    )
    queue_hits, prior_quote = 0, None
    phase, pending, target_due = "off", None, None
    requested_release = 0
    release_used, horizon_started = False, False
    attempts = {"runner": 0, "whole": 0}
    chain, limit, submit_due, expiry, sell_cancel_due = "runner", None, None, None, None

    def event(now, reason, **fields):
        trace.append({"at_ms": now, "phase": phase, "reason": reason, **fields})

    def fill(quantities, budget, minimum, now, *, target_fill):
        for level in budget:
            price = level[0]
            if price < minimum:
                break
            for k in book_order if target_fill else lot_order:
                qty = min(quantities[k], level[1])
                if not qty:
                    continue
                quantities[k] -= qty
                level[1] -= qty
                if not target_fill:
                    released[k] -= qty
                value = qty * (first.position.original_target if target_fill else price)
                proceeds[k] += value
                if not target_fill:
                    extra[k] += value
                if not target[k] and not released[k]:
                    results[k]["closed_at_ms"] = now
                event(
                    now,
                    "modeled_target_fill" if target_fill else "modeled_sell_fill",
                    lot_id=k,
                    quantity=qty,
                    price=value / qty,
                )

    for now in times:
        snapshot = timelines[lot_order[0]][now][1]
        quote = (
            snapshot.source_epoch,
            (
                snapshot.quote_sequence
                if snapshot.quote_sequence is not None
                else snapshot.sequence
            ),
        )
        new_quote = quote != prior_quote
        prior_quote = quote
        budget = (
            [[p, floor(q * model.depth_participation)] for p, q in snapshot.bid_levels]
            if new_quote
            else []
        )
        if (
            sum(target.values())
            and new_quote
            and snapshot.quote_at_ms >= first.target_ack_at_ms
        ):
            queue_hits = (
                queue_hits + 1
                if snapshot.bid_levels[0][0] >= first.position.original_target
                else 0
            )
            if queue_hits >= model.target_queue_confirmations:
                fill(
                    target,
                    budget,
                    first.position.original_target,
                    now,
                    target_fill=True,
                )
        # Target-first ordering also applies at the exact cancel boundary.
        if sum(working.values()) and now >= submit_due:
            if phase == "sell" and now >= expiry and pending is None:
                phase, sell_cancel_due = "sell_cancel", now + model.cancel_latency_ms
                event(now, "sell_ttl")
            else:
                fill(working, budget, limit, now, target_fill=False)
        if not sum(target.values()) + sum(released.values()):
            return finish()
        if sum(working.values()) == 0 and phase in {"sell", "sell_cancel"}:
            phase, sell_cancel_due = "off", None
        if pending and target_due is not None and now >= target_due:
            selected = set(lot_order) if pending == "whole" else runners
            if (
                pending != "whole"
                and sum(target[k] for k in selected) != requested_release
            ):
                return finish("partial_cancel_quantity_changed_requires_owner_recovery")
            for k in selected:
                released[k] += target[k]
                target[k] = 0
            target_due = None
            event(now, "modeled_target_cancel_terminal")
        if sell_cancel_due is not None and now >= sell_cancel_due:
            working = dict.fromkeys(lot_order, 0)
            sell_cancel_due = None
            phase = "ready"
            event(now, "modeled_sell_cancel_terminal")
        if pending and target_due is None and sell_cancel_due is None:
            if sum(working.values()):
                return finish("whole_cancel_working_reservation_unresolved")
            phase = "arm" if pending == "trail" else "ready"
            pending = None

        decisions = {}
        depth = list(snapshot.bid_levels)
        for k in lot_order:
            qty = target[k] + released[k]
            if not qty:
                continue
            if (
                k in runners
                and pending in {"trail", "runner"}
                and target_due is not None
            ):
                # Runtime's accepted pre-release book is immutable while its
                # cancel action is outstanding. Observed ticks cannot grant an
                # extension or bridge a decision gap on behalf of that book.
                continue
            clock, s = timelines[k][now]
            p = replace(by_lot[k].position, open_qty=qty)
            state = replace(states[k], open_qty=qty)
            # Match the runtime's pre-release runner allocation too, not only
            # the released phase; standalone nonrunner depth is not additive.
            if released[k] or k in runners and not release_used:
                s = replace(s, bid_levels=_consume(depth, qty))
            d = evaluate_exit(policy, p, s, clock, state)
            if d.action in {"SOURCE_GAP", "RECOVERY_REQUIRED"}:
                return finish("group_decision_invalid:" + d.reason)
            decisions[k] = d
            states[k] = (
                replace(
                    state,
                    last_observed_at_ms=s.observed_at_ms,
                    source_epoch=s.source_epoch,
                    sequence=s.sequence,
                )
                if released[k]
                else _advance(state, d, clock, s, p)
            )

        horizon = (
            model.horizon_close_lead_ms is not None
            and now >= first.horizon_end_ms - model.horizon_close_lead_ms
        )
        if horizon and not horizon_started and pending is None:
            horizon_started, chain, pending = True, "whole", "whole"
            target_due = now + model.cancel_latency_ms if sum(target.values()) else None
            if sum(working.values()):
                # Preserve a cancellation already in flight; no duplicate.
                if sell_cancel_due is None:
                    sell_cancel_due = (target_due or now) + model.cancel_latency_ms
                phase = "sell_cancel"
            event(now, "common_horizon_evaluation_close")
            continue
        if (
            pending is None
            and phase == "off"
            and not baseline
            and not release_used
            and not horizon_started
        ):
            actions = {k: d.action for k, d in decisions.items()}
            status = classify_group_request(actions, runners.intersection(actions))
            if status == "REQUEST_RUNNER_RELEASE":
                kinds = {actions[k] for k in runners}
                pending = "trail" if kinds == {"REQUEST_TRAIL_ARM"} else "runner"
                requested_release = sum(target[k] for k in runners)
                target_due, release_used = now + model.cancel_latency_ms, True
                event(now, "modeled_partial_cancel_requested")
            elif status != "KEEP_TARGET":
                return finish(status)
        if phase in {"arm", "trail"} and pending is None:
            commands = []
            for k in lot_order:
                if not released[k]:
                    continue
                d, p, state = decisions[k], by_lot[k].position, states[k]
                if phase == "arm":
                    stop = None
                    if d.action == "REQUEST_TRAIL_ARM":
                        stop = _tick_ceiling(
                            max(
                                p.entry_price * (1 + p.round_trip_cost_pct / 100),
                                d.executable_bid - policy.trail.gap_ticks * p.tick_size,
                            ),
                            p.tick_size,
                        )
                    if stop is not None and stop < d.executable_bid:
                        states[k] = replace(
                            state,
                            trail_active=True,
                            high_water=d.executable_bid,
                            stop_price=stop,
                        )
                        commands.append("trail")
                    else:
                        commands.append("sell")
                elif d.action == "KEEP_TRAIL":
                    states[k] = replace(
                        state, high_water=d.high_water, stop_price=d.stop_price
                    )
                    commands.append("trail")
                else:
                    commands.append("sell")
            if len(set(commands)) > 1:
                return finish("SELECTIVE_RUNNER_EXIT_REQUIRES_RECOVERY")
            phase = "trail" if commands and set(commands) == {"trail"} else "ready"
        if phase == "ready" and pending is None:
            if attempts[chain] >= model.maximum_sell_attempts:
                phase = "unresolved"
                event(now, "bounded_attempts_exhausted", chain=chain)
            elif sum(released.values()):
                attempts[chain] += 1
                limit = min(decisions[k].worst_bid for k in lot_order if released[k])
                working = dict(released)
                submit_due = now + model.submit_latency_ms
                expiry = submit_due + model.sell_ttl_ms
                phase = "sell"
                event(
                    now,
                    "pooled_marketable_limit_intent",
                    quantity=sum(working.values()),
                    chain=chain,
                    attempt=attempts[chain],
                    limit_price=limit,
                )
    return finish()


def replay_group_paired(paths, policies, models, *, lot_order):
    result = []
    for policy in policies:
        for model in models:
            base = replay_group_execution(
                paths, policy, model, lot_order=lot_order, baseline=True
            )
            candidate = replay_group_execution(
                paths, policy, model, lot_order=lot_order
            )
            result.extend(
                {
                    "policy_hash": policy.policy_hash,
                    "model_id": model.model_id,
                    "baseline": a,
                    "candidate": b,
                }
                for a, b in zip(base, candidate)
            )
    return result
