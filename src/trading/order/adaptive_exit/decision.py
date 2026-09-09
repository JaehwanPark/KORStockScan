"""Pure, past-only decisions shared by replay and a future authorized adapter."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, ROUND_CEILING

from .models import (
    Clock,
    DecisionState,
    ExitDecision,
    ExitPolicy,
    Position,
    Snapshot,
    finite,
    positive_int,
)


def _tick_ceiling(price: float, tick: float) -> float:
    step = Decimal(str(tick))
    return float(
        (Decimal(str(price)) / step).to_integral_value(rounding=ROUND_CEILING) * step
    )


def evaluate_exit(
    policy: ExitPolicy,
    position: Position,
    snapshot: Snapshot,
    clock: Clock,
    previous_state: DecisionState,
) -> ExitDecision:
    """Return intent only. Never infer a fill, cancel, or broker-ready order.

    Time-progress extension is at most once; supportive positions may retain
    their target when hard_wall_sec is explicitly None. Missing support does
    not mean weak support. All prices are observed executable bid prices.
    """
    p, s, old = position, snapshot, previous_state
    base = ExitDecision(
        "SOURCE_GAP",
        "invalid_position",
        policy.policy_hash,
        s.source_hash,
        p.lot_id,
        p.open_qty,
    )

    def answer(action: str, reason: str, **fields: object) -> ExitDecision:
        return replace(base, action=action, reason=reason, **fields)

    if not all(
        isinstance(v, str) and v
        for v in (
            p.owner_id,
            p.scope_key,
            p.episode_id,
            p.lot_id,
            p.position_epoch,
            p.cost_contract_hash,
        )
    ) or not positive_int(p.open_qty):
        return base
    if (
        not all(
            finite(v) and v > 0 for v in (p.entry_price, p.original_target, p.tick_size)
        )
        or p.original_target <= p.entry_price
    ):
        return base
    if not finite(p.round_trip_cost_pct) or p.round_trip_cost_pct < 0:
        return answer("SOURCE_GAP", "cost_contract_invalid")
    if old.policy_hash != policy.policy_hash or old.position_epoch != p.position_epoch:
        return answer("RECOVERY_REQUIRED", "frozen_policy_or_position_epoch_mismatch")
    if old.first_fill_at_ms != p.first_fill_at_ms or old.open_qty != p.open_qty:
        return answer("RECOVERY_REQUIRED", "first_fill_clock_or_quantity_epoch_changed")
    if policy.scope_key != p.scope_key or s.scope_key != p.scope_key:
        return answer("SOURCE_GAP", "owner_route_session_scope_mismatch")
    if type(old.trail_active) is not bool:
        return answer("RECOVERY_REQUIRED", "trail_state_invalid")
    if old.trail_active and (
        policy.mode != "fast_partial_trailing"
        or not all(finite(v) and v > 0 for v in (old.high_water, old.stop_price))
        or old.stop_price >= old.high_water
    ):
        return answer("RECOVERY_REQUIRED", "trail_state_invalid")
    if (
        type(old.extensions) is not int
        or old.extensions not in (0, 1)
        or (
            old.extensions == 0
            and (
                old.extension_until_active_ms is not None
                or old.extension_granted_at_active_ms is not None
            )
        )
        or (
            old.extensions == 1
            and (
                not positive_int(old.extension_until_active_ms)
                or not positive_int(old.extension_granted_at_active_ms)
                or old.extension_granted_at_active_ms < policy.soft_sec * 1000
                or old.extension_until_active_ms
                != int(old.extension_granted_at_active_ms + policy.extension_sec * 1000)
            )
        )
    ):
        return answer("RECOVERY_REQUIRED", "extension_state_invalid")
    if not all(
        type(v) is int and v >= 0
        for v in (
            clock.now_ms,
            clock.verified_halt_ms,
            p.first_fill_at_ms,
            s.observed_at_ms,
            s.quote_at_ms,
            s.sequence,
        )
    ):
        return answer("SOURCE_GAP", "clock_or_sequence_invalid")
    wall_ms = clock.now_ms - p.first_fill_at_ms
    if wall_ms < 0 or not 0 <= clock.verified_halt_ms <= wall_ms:
        return answer("SOURCE_GAP", "clock_source_gap")
    active_ms = wall_ms - clock.verified_halt_ms
    if old.extensions and old.extension_granted_at_active_ms > active_ms:
        return answer("RECOVERY_REQUIRED", "extension_grant_in_future")
    if (
        not all(isinstance(v, str) and v for v in (s.source_hash, s.source_epoch))
        or s.position_epoch != p.position_epoch
    ):
        return answer("SOURCE_GAP", "snapshot_identity_missing_or_mismatched")
    if not p.first_fill_at_ms <= s.quote_at_ms <= s.observed_at_ms <= clock.now_ms:
        return answer("SOURCE_GAP", "snapshot_time_not_past_fill")
    if clock.now_ms - s.quote_at_ms > policy.max_quote_age_ms:
        return answer("SOURCE_GAP", "stale_quote")
    if old.last_observed_at_ms is not None:
        if (
            type(old.last_observed_at_ms) is not int
            or old.last_observed_at_ms < p.first_fill_at_ms
        ):
            return answer("RECOVERY_REQUIRED", "prior_observation_time_invalid")
        if old.source_epoch != s.source_epoch:
            return answer("RECOVERY_REQUIRED", "source_epoch_changed")
        if (
            type(old.sequence) is not int
            or old.sequence < 0
            or (
                s.sequence <= old.sequence or s.observed_at_ms < old.last_observed_at_ms
            )
        ):
            return answer("SOURCE_GAP", "source_sequence_regression_or_duplicate")
        if s.observed_at_ms - old.last_observed_at_ms > policy.max_observation_gap_ms:
            return answer("SOURCE_GAP", "observation_path_gap")

    elif old.source_epoch is not None or old.sequence is not None:
        return answer("RECOVERY_REQUIRED", "partial_prior_source_identity")
    remaining, notional, worst, last = p.open_qty, 0.0, None, None
    if not isinstance(s.bid_levels, (tuple, list)):
        return answer("SOURCE_GAP", "invalid_bid_depth")
    if not finite(s.best_ask) or s.best_ask <= 0:
        return answer("SOURCE_GAP", "invalid_best_ask")
    for level in s.bid_levels:
        if not isinstance(level, (tuple, list)) or len(level) != 2:
            return answer("SOURCE_GAP", "invalid_bid_depth")
        price, qty = level
        if (
            not finite(price)
            or price <= 0
            or not positive_int(qty)
            or (last is not None and price >= last)
        ):
            return answer("SOURCE_GAP", "invalid_bid_depth")
        if price >= s.best_ask:
            return answer("SOURCE_GAP", "locked_or_crossed_bbo")
        last = price
        take = min(remaining, qty)
        if take:
            notional += take * price
            remaining -= take
            worst = price
    if remaining or not finite(notional):
        return answer("SOURCE_GAP", "insufficient_executable_depth")
    bid = notional / p.open_qty
    progress = (bid - p.entry_price) / (p.original_target - p.entry_price)
    net = (bid / p.entry_price - 1) * 100 - p.round_trip_cost_pct
    base = replace(
        base, executable_bid=bid, worst_bid=worst, progress=progress, net_return_pct=net
    )
    # Risk limits request an exit only with a valid executable snapshot.
    if policy.hard_wall_sec is not None and wall_ms >= policy.hard_wall_sec * 1000:
        return answer("REQUEST_EARLY_EXIT", "hard_wall_deadline")
    if net <= -policy.loss_budget_pct:
        return answer(
            "REQUEST_EARLY_EXIT", "loss_budget_trigger_not_guaranteed_loss_cap"
        )

    if old.trail_active:
        if bid <= old.stop_price:
            return answer(
                "REQUEST_TRAIL_EXIT",
                "trailing_stop_crossed",
                high_water=old.high_water,
                stop_price=old.stop_price,
            )
        high = max(old.high_water, bid)
        floor = p.entry_price * (1 + p.round_trip_cost_pct / 100)
        stop = max(
            old.stop_price,
            _tick_ceiling(
                max(floor, high - policy.trail.gap_ticks * p.tick_size), p.tick_size
            ),
        )
        return answer("KEEP_TRAIL", "monotonic_trail", high_water=high, stop_price=stop)

    if type(s.supportive) is not bool or not finite(s.improvement_bps):
        return answer("SOURCE_GAP", "support_or_improvement_missing")
    if policy.mode == "fast_partial_trailing":
        t = policy.trail
        floor = p.entry_price * (1 + p.round_trip_cost_pct / 100)
        gap = t.gap_ticks * p.tick_size
        ceiling = p.original_target - t.transition_buffer_ticks * p.tick_size
        if floor + gap >= ceiling:
            return answer("KEEP_TARGET", "unsupported_trailing_geometry")
        if (
            active_ms <= t.fast_sec * 1000
            and t.min_progress <= progress < 1
            and (
                s.supportive
                and net >= t.minimum_net_cushion_pct
                and floor + gap < bid < ceiling
            )
        ):
            # No high-water is set until cancel terminal + fresh arm validation.
            return answer("REQUEST_TRAIL_ARM", "fast_supported_pretarget_approach")
        return answer("KEEP_TARGET", "trail_arm_predicate_not_met")

    deadline = old.extension_until_active_ms or int(policy.soft_sec * 1000)
    if active_ms < deadline:
        return answer(
            "KEEP_TARGET",
            "before_soft_or_extension_deadline",
            next_active_deadline_ms=deadline,
        )
    improving = s.improvement_bps > policy.minimum_improvement_bps
    if old.extensions == 0 and (s.supportive or improving):
        return answer(
            "GRANT_EXTENSION",
            "supported_or_improving_once",
            next_active_deadline_ms=int(active_ms + policy.extension_sec * 1000),
        )
    if progress < policy.minimum_progress and not improving and not s.supportive:
        return answer("REQUEST_EARLY_EXIT", "slow_progress_without_recovery_support")
    return answer("KEEP_TARGET", "time_progress_exit_predicate_not_met")
