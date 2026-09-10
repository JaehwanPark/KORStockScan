"""Unknown active time permits exact receipts, never a new broker effect."""

from dataclasses import replace

import pytest

from src.tests.test_machine_adaptive_exit_activation import OPEN
from src.tests.test_machine_adaptive_exit_driver import Port, setup, proof
from src.tests.test_machine_adaptive_exit_runtime import (
    cancelled,
    working_exit,
    detail,
    current,
    cancel_detail,
)
from src.trading.order.adaptive_exit.driver import advance_exit
from src.trading.order.adaptive_exit.models import Clock, ClockSourceGap
from src.trading.order.adaptive_exit.runtime import OwnerSession

pytest_plugins = [
    "src.tests.test_machine_adaptive_exit_enrollment",
    "src.tests.test_machine_adaptive_exit_runtime",
]


def unknown_clock(*args):
    raise ClockSourceGap("session_or_halt_history_unverified")


@pytest.mark.parametrize("full_fill", [False, True])
@pytest.mark.parametrize("mode", ["exception", "explicit_none"])
def test_unknown_clock_original_owner_receipts_without_market_or_orders(
    enrolled_owner, full_fill, mode
):
    x = enrolled_owner
    assert x.propose()
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services,
        clock_loader=(
            unknown_clock if mode == "exception" else lambda s, ms: Clock(ms, None)
        ),
        snapshot_loader=lambda *a: pytest.fail("unknown clock used for price decision"),
    )
    if full_fill:
        x.wire.detailed[0].update(cntr_qty="10", ord_remnq="0")
        x.wire.current = []
    x.machine.run_once(OPEN)
    if full_fill and x.owner == "widget":
        history = x.machine._state["symbols"]["005930"]["adaptive_exit_history"][-1]
        session = OwnerSession.from_payload(history["sessions"]["entry"])
        assert history["enrollments"]["entry"]
        assert history["terminals"]["entry"]["realized_pnl_status"] != "reconciled"
    else:
        session = OwnerSession.from_payload(x.raw())
    assert session.driver.orders.open_qty == (0 if full_fill else 10)
    assert session.manager_required is not full_fill
    assert x.wire.calls and not x.wire.writes
    if not full_fill:
        assert "clock_source_gap" in str(x.machine._state)
        assert session.driver.decision.extensions == 0


@pytest.mark.parametrize("flag", ["lock", "authority"])
def test_clock_gap_does_not_bypass_original_authority(enrolled_owner, flag):
    x = enrolled_owner
    assert x.propose()
    x.flags[flag] = False
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services, clock_loader=unknown_clock
    )
    x.machine.run_once(OPEN)
    assert not x.wire.calls


def gap_tick(port, now):
    now[0] += 1
    return port.step(snapshot=None, clock=Clock(now[0], None))


def test_clock_gap_tracks_partial_target_then_full_fill_after_restart(runtime):
    initial, build, _, wire, _, saved, now, _ = runtime
    port = build(initial()[0])
    anchor = port.session.position.first_fill_at_ms
    wire.detailed = [detail(cntr_qty="3", ord_remnq="7")]
    wire.current = [current(cntr_qty="3", oso_qty="7")]
    gap_tick(port, now)
    assert port.session.driver.orders.open_qty == 7
    port = build(OwnerSession.from_payload(saved[-1]))
    gap_tick(port, now)
    assert port.session.driver.decision.open_qty == 7
    assert port.session.position.first_fill_at_ms == anchor
    wire.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    wire.current = []
    gap_tick(port, now)
    assert port.session.driver.orders.phase == "FLAT"
    assert not wire.writes


def test_clock_gap_accepts_confirmed_cancel_but_never_sells_residual(runtime):
    initial, build, tick, wire, _, saved, now, _ = runtime
    port = build(initial()[0])
    tick(port)
    assert port.session.driver.orders.phase == "CANCEL_PENDING"
    wire.detailed, wire.current = [detail(ord_remnq="0"), cancel_detail()], []
    writes = len(wire.writes)
    gap_tick(port, now)
    assert port.session.driver.orders.phase == "RESIDUAL_READY"
    port = build(OwnerSession.from_payload(saved[-1]))
    gap_tick(port, now)
    assert port.session.driver.orders.phase == "RESIDUAL_READY"
    assert len(wire.writes) == writes
    assert "clock_source_gap" in port.session.driver.alert_reason
    # Restore a genuinely verified clock and fresh market through the old path.
    wire.write_body["ord_no"] = "0000004"
    tick(port)
    assert port.session.driver.orders.phase == "EXIT_WORKING"
    assert len(wire.writes) == writes + 1


def test_clock_gap_recovers_accepted_submission_without_resubmitting(runtime):
    _, build, tick, wire, _, saved, now, _ = runtime
    port = cancelled(runtime)
    port = build(port.session, fail_phase="EXIT_WORKING")
    wire.write_body["ord_no"] = "0000004"
    with pytest.raises(OSError):
        tick(port)
    assert saved[-1]["driver"]["orders"]["phase"] == "EXIT_SUBMITTING"
    working_exit(wire)
    writes = len(wire.writes)
    port = build(OwnerSession.from_payload(saved[-1]))
    gap_tick(port, now)
    assert port.session.driver.orders.phase == "EXIT_WORKING"
    assert port.session.driver.orders.exit_order.order_no == "0000004"
    assert len(wire.writes) == writes
    working_exit(wire, fill=10, remaining=0)
    gap_tick(port, now)
    assert not port.session.manager_required
    assert len(wire.writes) == writes


def test_clock_gap_reconciles_exit_cancel_terminal_but_blocks_next_attempt(runtime):
    _, build, tick, wire, _, saved, now, _ = runtime
    port = cancelled(runtime)
    wire.write_body["ord_no"] = "0000004"
    tick(port)
    working_exit(wire, fill=3, remaining=7)
    now[0] += 3000
    wire.write_body.update(ord_no="0000005", base_orig_ord_no="0000004", cncl_qty="7")
    tick(port, quote=False)
    assert port.session.driver.orders.phase == "EXIT_CANCEL_PENDING"
    working_exit(wire, fill=3, remaining=0)
    wire.detailed.append(cancel_detail(order="0000005", parent="0000004", requested=7))
    port = build(OwnerSession.from_payload(saved[-1]))
    writes = len(wire.writes)
    gap_tick(port, now)
    assert port.session.driver.orders.phase == "RESIDUAL_READY"
    gap_tick(port, now)
    assert port.session.driver.orders.open_qty == 7
    assert port.session.manager_required
    assert len(wire.writes) == writes


@pytest.mark.parametrize("full_fill", [False, True])
def test_clock_gap_reconciles_exit_but_cannot_submit_ttl_cancel(runtime, full_fill):
    _, build, tick, wire, registry, saved, now, _ = runtime
    port = cancelled(runtime)
    wire.write_body["ord_no"] = "0000004"
    tick(port)
    working_exit(wire, fill=10 if full_fill else 3, remaining=0 if full_fill else 7)
    now[0] += port.session.bounds.sell_ttl_ms + 1
    writes = len(wire.writes)
    port = build(OwnerSession.from_payload(saved[-1]))
    gap_tick(port, now)
    assert port.session.driver.orders.open_qty == (0 if full_fill else 7)
    assert len(wire.writes) == writes
    if full_fill:
        assert not port.session.manager_required
        assert registry.owner_position_qty("position:test", symbol="005930") == 0
    else:
        assert port.session.driver.orders.phase == "EXIT_WORKING"
        gap_tick(port, now)
        assert port.session.driver.orders.phase == "EXIT_WORKING"
        assert len(wire.writes) == writes
        assert not port.guard(
            port.session.driver.orders, quantity=7, worst_bid=None, now_ms=now[0]
        )


@pytest.mark.parametrize(
    "phase", ["TARGET_WORKING", "INTENT_PERSISTED", "CANCEL_PENDING"]
)
def test_pure_driver_clock_gap_blocks_intent_and_cancel_resume(phase):
    driver, args = setup()
    port = Port()
    if phase != "TARGET_WORKING":
        advance_exit(driver, port=port, **args)
        driver = next(s for s in port.saved if s.orders.phase == phase)
    port.calls.clear()
    port.resume_unreserved_cancel = lambda *a, **k: pytest.fail(
        "new cancel on clock gap"
    )
    port.proof = proof(driver, args["clock"], terminal=False, fill=0)
    args["clock"] = replace(args["clock"], verified_halt_ms=None)
    result = advance_exit(driver, port=port, **args)
    assert result.orders.phase == phase
    assert result.alert_reason == "clock_source_gap_receipt_reconciliation_only"
    assert not port.calls


@pytest.mark.parametrize("bad", [-1, True, "0", 999999999999999])
def test_malformed_clock_is_not_normalized_to_receipt_mode(runtime, bad):
    initial, build, _, wire, _, _, now, _ = runtime
    port = build(initial()[0])
    with pytest.raises(ValueError, match="valid_owner_clock_required"):
        port.step(snapshot=None, clock=Clock(now[0], bad))
    assert not wire.calls


def test_unknown_clock_is_not_an_economic_replay_or_decision_input():
    from src.tests.test_machine_adaptive_exit_decision import inputs
    from src.tests.test_machine_adaptive_exit_execution_replay import fixture
    from src.engine.monitoring.machine_adaptive_exit_replay import replay_decisions
    from src.engine.monitoring.machine_adaptive_exit_execution_replay import (
        replay_execution,
    )
    from src.trading.order.adaptive_exit.decision import evaluate_exit

    policy, position, snapshot, clock, state = inputs()
    clock = replace(clock, verified_halt_ms=None)
    assert (
        evaluate_exit(policy, position, snapshot, clock, state).action == "SOURCE_GAP"
    )
    result = replay_decisions(policy, position, [(clock, snapshot)])
    assert result["status"] == "source_gap" and result["net_ev_pct"] is None
    path, policy, model = fixture()
    path = replace(
        path,
        observations=tuple(
            (replace(clock, verified_halt_ms=None), snap)
            for clock, snap in path.observations
        ),
    )
    result = replay_execution(path, policy, model)
    assert not result["counterfactual_exit_resolved"]
    assert result["net_ev_pct"] is None


def test_unknown_clock_keeps_group_decisions_source_gapped(tmp_path, monkeypatch):
    from src.tests import test_machine_adaptive_exit_group_decision as group

    make, transport, _, _ = group.setup.__wrapped__(tmp_path, monkeypatch)
    coordinator = make().coordinator
    inputs = group.pure_inputs(coordinator)
    for row in inputs["lots"].values():
        row["clock"]["verified_halt_ms"] = None
    result = group.evaluate(coordinator, inputs)
    assert result["status"] == "SOURCE_GAP"
    assert all(
        row["action"] == "SOURCE_GAP" for row in result["lot_decisions"].values()
    )
    assert not transport.writes
