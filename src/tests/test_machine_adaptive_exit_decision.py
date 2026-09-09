from dataclasses import replace

import pytest

from src.trading.order.adaptive_exit.decision import evaluate_exit
from src.trading.order.adaptive_exit.models import (
    Clock,
    DecisionState,
    ExitPolicy,
    Position,
    Snapshot,
    TrailPolicy,
)


def inputs(*, age=60_000, bid=10010.0, support=False, improvement=0.0):
    scope = "widget|005930|p1|KRX_REGULAR|KRX|entry_hash"
    policy = ExitPolicy(
        "a" * 64,
        scope,
        "time_progress_exit",
        60,
        30,
        0.4,
        1,
        None,
        2,
        1000,
        60_000,
        None,
    )
    position = Position(
        "widget",
        scope,
        "ep1",
        "lot1",
        "quantity_epoch1",
        100_000,
        10,
        10000,
        10100,
        0.23,
        "cost_hash",
        5,
    )
    snapshot = Snapshot(
        100_000 + age,
        100_000 + age,
        "ws1",
        1,
        "raw_hash",
        scope,
        position.position_epoch,
        bid + 5,
        ((bid, 10),),
        support,
        improvement,
    )
    clock = Clock(100_000 + age, 0)
    state = DecisionState(
        policy.policy_hash,
        position.position_epoch,
        position.first_fill_at_ms,
        position.open_qty,
    )
    return policy, position, snapshot, clock, state


def test_slow_weak_progress_requests_exit_not_an_order():
    d = evaluate_exit(*inputs())
    assert d.action == "REQUEST_EARLY_EXIT"
    assert d.reason == "slow_progress_without_recovery_support"
    assert d.net_return_pct < 0  # Individual loss is not an invalid decision.
    assert not hasattr(d, "broker_payload")


def test_before_soft_deadline_keeps_target():
    d = evaluate_exit(*inputs(age=59_999))
    assert d.action == "KEEP_TARGET"
    assert d.next_active_deadline_ms == 60_000


def test_restored_extension_cannot_inflate_deadline_or_reuse_future_grant():
    policy, pos, snap, clock, state = inputs()
    bad = replace(
        state,
        extensions=1,
        extension_granted_at_active_ms=60_000,
        extension_until_active_ms=999_999,
    )
    assert (
        evaluate_exit(policy, pos, snap, clock, bad).reason == "extension_state_invalid"
    )
    bad = replace(
        bad, extension_granted_at_active_ms=70_000, extension_until_active_ms=100_000
    )
    assert (
        evaluate_exit(policy, pos, snap, clock, bad).reason
        == "extension_grant_in_future"
    )


def test_corrupted_trail_state_is_not_bypassed_by_hard_deadline():
    policy, pos, snap, clock, state = trail_inputs(age=60_000)
    policy = replace(policy, hard_wall_sec=60)
    state = replace(state, trail_active=True, high_water=None, stop_price=None)
    assert evaluate_exit(policy, pos, snap, clock, state).action == "RECOVERY_REQUIRED"


def test_support_gives_only_one_extension_then_rechecks_weakness():
    args = inputs(support=True)
    d = evaluate_exit(*args)
    assert d.action == "GRANT_EXTENSION" and d.next_active_deadline_ms == 90_000
    policy, position, snap, clock, state = inputs(age=90_000)
    state = replace(
        state,
        extensions=1,
        extension_until_active_ms=90_000,
        extension_granted_at_active_ms=60_000,
    )
    assert (
        evaluate_exit(policy, position, snap, clock, state).action
        == "REQUEST_EARLY_EXIT"
    )
    snap = replace(snap, supportive=True)
    assert evaluate_exit(policy, position, snap, clock, state).action == "KEEP_TARGET"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("supportive", None, "support_or_improvement_missing"),
        ("supportive", 0, "support_or_improvement_missing"),
        ("improvement_bps", float("nan"), "support_or_improvement_missing"),
        ("improvement_bps", float("inf"), "support_or_improvement_missing"),
        ("quote_at_ms", 158999, "stale_quote"),
        ("quote_at_ms", 160001, "snapshot_time_not_past_fill"),
        ("source_hash", "", "snapshot_identity_missing_or_mismatched"),
        ("best_ask", 10000, "locked_or_crossed_bbo"),
        ("best_ask", None, "invalid_best_ask"),
        ("position_epoch", "other", "snapshot_identity_missing_or_mismatched"),
        ("scope_key", "NXT", "owner_route_session_scope_mismatch"),
        ("bid_levels", ((10010, 9),), "insufficient_executable_depth"),
        ("bid_levels", ((10010, True),), "invalid_bid_depth"),
        ("bid_levels", ((10010, 5), (10015, 5)), "invalid_bid_depth"),
        ("bid_levels", ((10010, 5, 3),), "invalid_bid_depth"),
        ("bid_levels", ((float("nan"), 10),), "invalid_bid_depth"),
    ],
)
def test_source_gaps_do_not_become_weak_support(field, value, reason):
    policy, position, snap, clock, state = inputs()
    d = evaluate_exit(policy, position, replace(snap, **{field: value}), clock, state)
    assert (d.action, d.reason) == ("SOURCE_GAP", reason)


def test_vwap_and_worst_bid_are_distinct():
    policy, position, snap, clock, state = inputs()
    snap = replace(snap, bid_levels=((10010, 4), (10000, 6)))
    d = evaluate_exit(policy, position, snap, clock, state)
    assert d.executable_bid == 10004 and d.worst_bid == 10000


@pytest.mark.parametrize(
    "changed",
    [
        {"first_fill_at_ms": 100001},
        {"open_qty": 5},
        {"position_epoch": "other"},
    ],
)
def test_restart_or_partial_fill_cannot_reset_frozen_clock_or_quantity(changed):
    policy, p, snap, clock, state = inputs()
    assert (
        evaluate_exit(policy, replace(p, **changed), snap, clock, state).action
        == "RECOVERY_REQUIRED"
    )


def test_only_verified_halt_pauses_active_age_but_never_hard_wall_deadline():
    policy, p, snap, clock, state = inputs(age=70_000)
    halted = replace(clock, verified_halt_ms=20_000)
    assert evaluate_exit(policy, p, snap, halted, state).action == "KEEP_TARGET"
    policy = replace(policy, hard_wall_sec=65)
    assert evaluate_exit(policy, p, snap, halted, state).reason == "hard_wall_deadline"
    stale = replace(snap, quote_at_ms=160_000)
    assert evaluate_exit(policy, p, stale, halted, state).action == "SOURCE_GAP"


def test_sequence_gap_and_reconnect_do_not_synthesize_continuity():
    policy, p, snap, clock, state = inputs()
    state = replace(state, last_observed_at_ms=159_000, source_epoch="ws1", sequence=1)
    assert (
        evaluate_exit(policy, p, snap, clock, state).reason
        == "source_sequence_regression_or_duplicate"
    )
    state = replace(state, source_epoch="old_ws")
    assert evaluate_exit(policy, p, snap, clock, state).action == "RECOVERY_REQUIRED"


def trail_inputs(*, bid=10065, age=20_000):
    policy, p, snap, clock, state = inputs(age=age, bid=bid, support=True)
    policy = replace(
        policy,
        mode="fast_partial_trailing",
        trail=TrailPolicy(30, 0.5, 3, 2, 0.1),
        runner_lot_ids=(p.lot_id,),
    )
    return policy, p, snap, clock, state


def test_fast_pretarget_intent_does_not_initialize_high_water_before_cancel():
    d = evaluate_exit(*trail_inputs())
    assert d.action == "REQUEST_TRAIL_ARM"
    assert d.high_water is None and d.stop_price is None


def test_nonrunner_lot_keeps_original_target_in_trailing_only_mode():
    policy, p, snapshot, clock, state = trail_inputs()
    p = replace(p, lot_id="nonrunner")
    result = evaluate_exit(policy, p, snapshot, clock, state)
    assert result.action == "KEEP_TARGET"
    assert result.reason == "lot_not_selected_for_trailing"


def test_tight_target_geometry_is_not_fixed_by_weakening_costs():
    policy, p, snap, clock, state = trail_inputs()
    p = replace(p, original_target=10040)
    assert (
        evaluate_exit(policy, p, snap, clock, state).reason
        == "unsupported_trailing_geometry"
    )


def test_trail_only_moves_up_and_hard_deadline_dominates():
    policy, p, snap, clock, state = trail_inputs(bid=10080)
    state = replace(state, trail_active=True, high_water=10070, stop_price=10055)
    d = evaluate_exit(policy, p, snap, clock, state)
    assert (d.action, d.high_water, d.stop_price) == ("KEEP_TRAIL", 10080, 10065)
    snap = replace(snap, bid_levels=((10050, 10),))
    assert evaluate_exit(policy, p, snap, clock, state).action == "REQUEST_TRAIL_EXIT"
    policy = replace(policy, hard_wall_sec=60)
    clock = replace(clock, now_ms=160_000)
    snap = replace(snap, observed_at_ms=160_000, quote_at_ms=160_000)
    assert evaluate_exit(policy, p, snap, clock, state).reason == "hard_wall_deadline"


@pytest.mark.parametrize(
    "patch",
    [
        {"extension_sec": 0},
        {"soft_sec": True},
        {"loss_budget_pct": float("nan")},
        {"max_quote_age_ms": 0},
        {"hard_wall_sec": 10},
        {"minimum_progress": 2},
        {"mode": "combined"},
        {"scope_key": ""},
        {"trail": TrailPolicy(30, 0.5, 3, 1, 0.1)},
    ],
)
def test_invalid_policies_have_no_implicit_permissive_defaults(patch):
    with pytest.raises(ValueError):
        replace(inputs()[0], **patch)


def test_first_checkpoint_accepts_available_fresh_quote_just_before_fill():
    policy, p, s, clock, old = inputs()
    s = replace(
        s, quote_at_ms=p.first_fill_at_ms - 1, observed_at_ms=p.first_fill_at_ms
    )
    clock = replace(clock, now_ms=p.first_fill_at_ms)
    result = evaluate_exit(policy, p, s, clock, old)
    assert result.action not in ("SOURCE_GAP", "RECOVERY_REQUIRED")
