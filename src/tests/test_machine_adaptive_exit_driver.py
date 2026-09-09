from dataclasses import replace

import pytest

from src.trading.order.adaptive_exit.driver import (
    DriverState,
    ExecutionBounds,
    BrokerProof,
    SubmitReceipt,
    advance_exit,
)
from src.trading.order.adaptive_exit.reducer import ExitState, OrderKey
from src.tests.test_machine_adaptive_exit_decision import inputs
from src.tests.test_machine_adaptive_exit_decision import trail_inputs
from src.trading.order.adaptive_exit.driver import rebind_remaining_quantity


class Port:
    def __init__(self):
        self.saved = []
        self.calls = []
        self.proof = None
        self.allowed = True
        self.crash = None

    def persist(self, state):
        if self.crash == "persist":
            raise OSError("disk")
        self.saved.append(state)

    def guard(self, *args, **kw):
        return self.allowed

    def reconcile(self, *args, **kw):
        return self.proof

    def recover_submission(self, *args, **kw):
        return self.proof

    def cancel_owned_sell(self, order, **kw):
        self.calls.append(("cancel", order, kw))
        assert self.saved[-1].orders.phase in ("CANCEL_PENDING", "EXIT_CANCEL_PENDING")
        if self.crash == "cancel":
            raise TimeoutError()

    def submit_owned_sell(self, **kw):
        self.calls.append(("sell", kw))
        assert self.saved[-1].orders.phase == "EXIT_SUBMITTING"
        if self.crash == "sell":
            raise TimeoutError()
        s = kw["state"]
        return SubmitReceipt(
            OrderKey("2026-09-09", "0000002"),
            s.owner_id,
            s.episode_id,
            s.lot_id,
            kw["quantity"],
            "raw-ack-hash",
            True,
        )


def setup():
    policy, p, s, c, state = inputs()
    orders = ExitState(
        p.owner_id,
        p.episode_id,
        p.lot_id,
        policy.policy_hash,
        p.position_epoch,
        OrderKey("2026-09-09", "0000001"),
        p.open_qty,
    )
    driver = DriverState(orders, state)
    bounds = ExecutionBounds(
        3000, 2, 5000, "exit_with_fresh_guard", "retain_manager_and_alert"
    )
    return driver, dict(
        policy=policy,
        position=p,
        snapshot=s,
        clock=c,
        bounds=bounds,
        active_policy_authorized=True,
    )


def proof(driver, clock, terminal=True, fill=0, order=None):
    s = driver.orders
    return BrokerProof(
        order or s.target,
        s.owner_id,
        s.episode_id,
        s.lot_id,
        fill,
        terminal,
        "receipt",
        clock.now_ms,
        True,
    )


def test_cancel_ack_is_not_terminal_and_no_duplicate_cancel():
    driver, args = setup()
    port = Port()
    current = advance_exit(driver, port=port, **args)
    assert current.orders.phase == "CANCEL_PENDING"
    assert len(port.calls) == 1
    current = advance_exit(current, port=port, **args)
    assert len(port.calls) == 1 and current.orders.phase == "CANCEL_PENDING"


def test_guard_and_durable_intent_precede_any_effect():
    driver, args = setup()
    port = Port()
    port.allowed = False
    assert advance_exit(driver, port=port, **args).alert_reason == "owner_guard_blocked"
    assert port.calls == []
    port.allowed = True
    port.crash = "persist"
    with pytest.raises(OSError):
        advance_exit(driver, port=port, **args)
    assert port.calls == []


def test_cancel_timeout_resumes_reconciliation_not_cancel():
    driver, args = setup()
    port = Port()
    port.crash = "cancel"
    with pytest.raises(TimeoutError):
        advance_exit(driver, port=port, **args)
    current = advance_exit(port.saved[-1], port=port, **args)
    assert current.orders.phase == "CANCEL_PENDING" and len(port.calls) == 1


def test_cancel_fill_flattens_without_rebuy_or_resell():
    driver, args = setup()
    port = Port()
    current = advance_exit(driver, port=port, **args)
    port.proof = proof(current, args["clock"], fill=10)
    current = advance_exit(current, port=port, **args)
    assert current.orders.phase == "FLAT" and len(port.calls) == 1


@pytest.mark.parametrize("fill", [4, 10])
def test_recovery_terminal_between_intent_and_cancel_never_cancels_again(fill):
    driver, args = setup()
    port = Port()
    advance_exit(driver, port=port, **args)
    intent = next(x for x in port.saved if x.orders.phase == "INTENT_PERSISTED")
    port.calls.clear()
    port.proof = proof(intent, args["clock"], fill=fill)
    recovered = advance_exit(intent, port=port, **args)
    assert recovered.orders.phase == ("FLAT" if fill == 10 else "RESIDUAL_READY")
    assert recovered.orders.open_qty == 10 - fill
    assert port.calls == []


def test_exact_cancel_then_fresh_sell_and_ambiguous_submit_never_repeats():
    driver, args = setup()
    port = Port()
    current = advance_exit(driver, port=port, **args)
    port.proof = proof(current, args["clock"])
    current = advance_exit(current, port=port, **args)
    assert current.orders.phase == "RESIDUAL_READY"
    args["snapshot"] = replace(
        args["snapshot"],
        sequence=2,
        observed_at_ms=args["clock"].now_ms + 1,
        quote_at_ms=args["clock"].now_ms + 1,
    )
    args["clock"] = replace(args["clock"], now_ms=args["clock"].now_ms + 1)
    port.crash = "sell"
    with pytest.raises(TimeoutError):
        advance_exit(current, port=port, **args)
    assert port.saved[-1].orders.phase == "EXIT_SUBMITTING"
    port.proof = None
    current = advance_exit(port.saved[-1], port=port, **args)
    assert current.orders.exit_reserved_qty == 10 and len(port.calls) == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("owner_id", "other"),
        ("receipt_hash", ""),
        ("reconciliation_complete", False),
        ("terminal", 1),
        ("cumulative_filled", True),
    ],
)
def test_untrusted_or_wrong_owner_proof_does_not_release_quantity(field, value):
    driver, args = setup()
    port = Port()
    current = advance_exit(driver, port=port, **args)
    port.proof = replace(proof(current, args["clock"]), **{field: value})
    current = advance_exit(current, port=port, **args)
    assert current.orders.phase == "CANCEL_PENDING" and len(port.calls) == 1


def test_trailing_arms_after_cancel_only_then_monotonic_stop_and_sell():
    _, args = setup()
    policy, p, s, c, state = trail_inputs()
    args.update(policy=policy, position=p, snapshot=s, clock=c)
    orders = ExitState(
        p.owner_id,
        p.episode_id,
        p.lot_id,
        policy.policy_hash,
        p.position_epoch,
        OrderKey("2026-09-09", "0000001"),
        p.open_qty,
    )
    port = Port()
    current = advance_exit(DriverState(orders, state), port=port, **args)
    assert (
        current.orders.phase == "CANCEL_PENDING" and not current.decision.trail_active
    )
    port.proof = proof(current, c)
    current = advance_exit(current, port=port, **args)
    args["clock"] = replace(c, now_ms=c.now_ms + 1)
    args["snapshot"] = replace(
        s,
        sequence=s.sequence + 1,
        quote_at_ms=c.now_ms + 1,
        observed_at_ms=c.now_ms + 1,
    )
    current = advance_exit(current, port=port, **args)
    assert current.orders.phase == "TRAIL_ACTIVE"
    assert current.decision.trail_active and len(port.calls) == 1
    stop = current.decision.stop_price
    args["clock"] = replace(c, now_ms=c.now_ms + 2)
    args["snapshot"] = replace(
        s,
        sequence=s.sequence + 2,
        quote_at_ms=c.now_ms + 2,
        observed_at_ms=c.now_ms + 2,
        bid_levels=((stop - 1, 100),),
        best_ask=stop + 10,
    )
    current = advance_exit(current, port=port, **args)
    assert current.orders.phase == "EXIT_WORKING" and len(port.calls) == 2
    assert current.unprotected_since_ms is None


def test_quantity_rebind_is_explicit_decreasing_and_preserves_clock():
    driver, args = setup()
    port = Port()
    current = advance_exit(driver, port=port, **args)
    port.proof = proof(current, args["clock"], fill=4)
    current = advance_exit(current, port=port, **args)
    assert current.orders.open_qty == 6
    pos = replace(args["position"], open_qty=6, position_epoch="remaining:6")
    rebound = rebind_remaining_quantity(current, position=pos)
    assert rebound.decision.open_qty == 6
    assert rebound.decision.first_fill_at_ms == driver.decision.first_fill_at_ms
    assert rebound.orders.position_epoch == "remaining:6"
    with pytest.raises(ValueError):
        rebind_remaining_quantity(rebound, position=replace(pos, open_qty=10))


def test_unprotected_deadline_alert_survives_normal_trail_update():
    driver, args = setup()
    policy, p, snap, clock, state = trail_inputs(bid=10080)
    state = replace(state, trail_active=True, high_water=10070, stop_price=10055)
    driver = DriverState(
        replace(
            driver.orders,
            phase="TRAIL_ACTIVE",
            target_terminal=True,
            intent_id="intent",
            intent_kind="trail_arm",
            high_water=10070,
            stop_price=10055,
        ),
        state,
        unprotected_since_ms=clock.now_ms - 6000,
    )
    args.update(policy=policy, position=p, snapshot=snap, clock=clock)
    port = Port()
    current = advance_exit(driver, port=port, **args)
    assert current.orders.phase == "TRAIL_ACTIVE"
    assert current.alert_reason == "unprotected_deadline_manager_must_remain"
    assert port.saved[-1].alert_reason == current.alert_reason
    assert not port.calls


def test_corrupt_persisted_state_never_reaches_broker_port():
    driver, args = setup()
    port = Port()
    bad = replace(
        driver, orders=replace(driver.orders, phase="EXIT_WORKING", exit_order=None)
    )
    result = advance_exit(bad, port=port, **args)
    assert result.alert_reason == "persisted_order_state_invalid" and not port.calls


def test_driver_has_no_symbol_or_profile_allowlist():
    from datetime import date
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    from src.trading.widget_auto_trade.engine import ALL_WIDGET_SPECS
    from src.trading.order.adaptive_exit.source import OwnerScope

    scopes = [
        OwnerScope("episode", key, profile.symbol, "SOR", profile.session)
        for key, profile in profiles_for_target_date(date(2026, 9, 9)).items()
    ]
    scopes += [
        OwnerScope("widget", spec.code, spec.code, "KRX", "KRX_REGULAR")
        for spec in ALL_WIDGET_SPECS
    ]
    assert len(scopes) > 56
    for scope in scopes:
        driver, args = setup()
        policy = replace(args["policy"], scope_key=scope.key)
        p = replace(
            args["position"],
            owner_id=scope.owner,
            scope_key=scope.key,
            episode_id=scope.key + ":episode",
        )
        args.update(
            policy=policy,
            position=p,
            snapshot=replace(args["snapshot"], scope_key=scope.key),
        )
        driver = replace(
            driver,
            orders=replace(driver.orders, owner_id=p.owner_id, episode_id=p.episode_id),
        )
        port = Port()
        current = advance_exit(driver, port=port, **args)
        assert current.orders.phase == "CANCEL_PENDING", scope
        assert len(port.calls) == 1
        assert port.calls[0][2]["state"].episode_id == p.episode_id
