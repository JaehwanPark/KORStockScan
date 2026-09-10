"""Original widget run_once, durable session and fake-only broker integration."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
import json
from types import SimpleNamespace

import pytest

from src.tests.test_machine_adaptive_exit_broker import DATE, NOW, TARGET, Transport
from src.tests.test_machine_adaptive_exit_group_runtime import confirmed
from src.tests.test_machine_adaptive_exit_group_decision import observations, policy_for
from src.tests.test_machine_adaptive_exit_group_trailing import ack
from src.tests.test_machine_adaptive_exit_group_terminal import flat_market
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.group_execution import RunnerBounds
from src.trading.order.adaptive_exit.group_owner_loop import (
    SESSION_KEY,
    GroupLoopServices,
    GroupOwnerSession,
)
from src.trading.order.adaptive_exit.group_runtime import RULE, RunnerAllocation
from src.trading.order.adaptive_exit.owner_loop import OwnerLoopServices
from src.trading.order.adaptive_exit.models import Clock, ClockSourceGap
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.adaptive_exit.source import OwnerScope
from src.trading.order.adaptive_exit.target_group import TargetGroup
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
)
from src.trading.widget_auto_trade import engine as widget


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "group-owner-test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = OwnerOrderContext(
        "widget_auto_trade", "widget:test", "widget:test:episode", "target"
    )
    lots, orders = [], []
    for lot, number, qty in (
        ("target_lot", "0000001", 4),
        ("runner_lot", "0000004", 6),
    ):
        child = replace(context, client_intent_id=lot)
        intent = registry.reserve(
            context=child,
            symbol="005930",
            side="BUY",
            quantity=qty,
            route="SOR",
            order_date=DATE,
        )
        registry.transition(intent, state="ORDER_BOUND", broker_order_no=number)
        registry.record_fill(
            context=child,
            symbol="005930",
            side="BUY",
            order_quantity=qty,
            order_date=DATE,
            broker_order_no=number,
            cumulative_filled_qty=qty,
        )
        registry.transition(intent, state="ORDER_TERMINAL")
        lots.append((lot, OrderKey(DATE, number), qty, NOW - 5000, 70000.0))
        orders.append(
            dict(
                side="BUY",
                order_no=number,
                order_date=DATE,
                requested_qty=qty,
                filled_qty=qty,
                fill_price=70000.0,
                status="FILLED",
                broker_accepted=True,
                owner_id=context.owner_id,
                owner_position_id=context.position_id,
                owner_registry_intent_id=intent,
                owner_client_intent_id=lot,
                route="SOR",
            )
        )
    target = registry.reserve(
        context=context,
        symbol="005930",
        side="SELL",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(target, state="ORDER_BOUND", broker_order_no=TARGET.order_no)
    orders.append(
        dict(
            side="SELL",
            order_no=TARGET.order_no,
            order_date=DATE,
            requested_qty=10,
            filled_qty=0,
            limit_price=70700,
            status="ACCEPTED",
            broker_accepted=True,
            owner_id=context.owner_id,
            owner_position_id=context.position_id,
            owner_registry_intent_id=target,
            owner_client_intent_id="target",
            route="SOR",
            order_role=widget.ORDER_ROLE_TAKE_PROFIT,
            parent_entry_signal_id="signal",
        )
    )
    group = TargetGroup(
        OwnerScope("widget", "test", "005930", "SOR", "KRX"),
        context.position_id,
        TARGET,
        70700,
        tuple(lots),
        "f" * 64,
    )
    policy = policy_for(group)
    allocation = RunnerAllocation(
        group.to_payload()["canonical_sha256"],
        policy["policy_hash"],
        "b" * 64,
        RULE,
        ("runner_lot",),
        ("runner_lot", "target_lot"),
    )
    session = GroupOwnerSession.create(
        group=group,
        allocation=allocation,
        context=context,
        bounds=RunnerBounds(1000, 500, 2000),
        max_snapshot_age_ms=1000,
        execution_approval_receipt_hash="e" * 64,
        decision_policy=policy,
    )
    wire, flags = Transport(), dict(
        now=NOW,
        lock=True,
        approval=True,
        guard=True,
        action=True,
        bid=70400,
        source=True,
    )

    def source(s, phase, now):
        if not flags["source"]:
            return None
        frozen = next(
            r
            for r in s.payload["records"].values()
            if r["schema"] == "machine_adaptive_exit_group_coordinator_v1"
        )
        c = SimpleNamespace(
            group=s.group, allocation=s.allocation, freeze=lambda: frozen
        )
        result = observations(c, now, now - NOW + 1, flags["bid"])
        if phase == "released":
            return {
                name: {k: v for k, v in result[name].items() if k == "runner_lot"}
                for name in ("snapshots", "clocks")
            }
        return result

    services = OwnerLoopServices(
        lock_held=lambda: flags["lock"],
        authorize_binding=lambda b: flags["approval"],
        owner_guard=lambda *a, **k: flags["guard"],
        snapshot_loader=lambda *a: None,
        clock_loader=lambda *a: None,
        group=GroupLoopServices(
            authorize_binding=lambda b: flags["approval"],
            owner_guard=lambda b: flags["guard"],
            authorize_action=lambda b, r, n: flags["action"],
            observations_loader=source,
            clock_loader=lambda session, now: {
                lot[0]: Clock(now, flags.get("halt_ms", 0))
                for lot in session.group.lots
            },
        ),
    )

    class Gateway:
        def adaptive_exit_adapter(
            self, *, registry, context, code, policy_hash, write_guard
        ):
            return RegisteredSellAdapter(
                post=wire,
                registry=registry,
                context=context,
                symbol=code,
                routes=("SOR",),
                policy_hash=policy_hash,
                maximum_quantity=10,
                require_write_authority=lambda: None,
                write_guard=write_guard,
                now_ms=lambda: flags["now"],
            )

    def new():
        return widget.WidgetSignalAutoTrader(
            gateway=Gateway(),
            specs=(),
            dynamic_spec_catalog=(),
            state_path=tmp_path / "widget.json",
            enabled=True,
            policy_loader=SimpleNamespace(resolve_all=lambda **k: {}),
            owner_registry=registry,
            adaptive_exit_services=services,
        )

    machine = new()
    machine._state = dict(
        active_date=DATE,
        symbols={
            "005930": dict(
                code="005930",
                orders=orders,
                entry_episode_open=True,
                entry_signal_id="signal",
                completed_entry_count=2,
                **{SESSION_KEY: session.to_payload()},
            )
        },
    )
    machine._save()
    return machine, new, wire, flags


def step(machine, flags, advance=0):
    flags["now"] += advance
    machine.run_once(datetime.fromtimestamp(flags["now"] / 1000, widget.KST))
    return machine._state["symbols"]["005930"]


def sell(setup):
    machine, new, wire, flags = setup
    assert step(machine, flags)["adaptive_exit_loop_status"] == "order_bound"
    assert len(wire.writes) == 1
    confirmed(wire)
    assert step(machine, flags, 1)["adaptive_exit_loop_status"] == "TRAIL_ACTIVE"
    flags["bid"] = 70300
    ack(wire)
    assert step(machine, flags, 1)["adaptive_exit_loop_status"] == "order_bound"
    return machine


def test_actual_widget_group_loop_archives_exact_orders_once_without_profit_or_new_buy(
    setup,
):
    machine, new, wire, flags = setup
    sell(setup)
    flat_market(wire)
    state = step(new(), flags, 1)
    assert SESSION_KEY not in state
    assert state["entry_episode_open"] is False and state["completed_entry_count"] == 3
    assert [o["filled_qty"] for o in state["orders"] if o["side"] == "SELL"] == [4, 6]
    assert state["adaptive_exit_loop_status"] == "execution_terminal_handoff_completed"
    history = state["adaptive_exit_history"][-1]
    assert history["group_terminal"]["realized_net_profit_krw"] is None
    assert history["group_terminal"]["new_entry_authority"] is False
    assert history["group_terminal"]["economic_acceptance"] is False
    assert len(wire.writes) == 2
    resumed = new()
    assert step(resumed, flags, 1)["completed_entry_count"] == 3
    assert len(wire.writes) == 2


@pytest.mark.parametrize("kind", ["missing", "unknown", "exception"])
def test_group_clock_gap_never_requests_release_or_market_source(setup, kind):
    machine, _, wire, flags = setup
    group = machine.adaptive_exit_services.group

    def unavailable(*args):
        raise ClockSourceGap("fixture_gap")

    def unexpected_source(*args):
        pytest.fail("price source must not run with an unknown clock")

    flags["halt_ms"] = None
    group = replace(
        group,
        observations_loader=unexpected_source,
        clock_loader=(
            None
            if kind == "missing"
            else unavailable if kind == "exception" else group.clock_loader
        ),
    )
    machine.adaptive_exit_services = replace(
        machine.adaptive_exit_services, group=group
    )
    state = step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "group_clock_source_gap"
    assert SESSION_KEY in state and not wire.writes


def test_runner_ttl_clock_gap_retains_receipt_reconciliation_and_resumes(setup):
    machine, new, wire, flags = setup
    sell(setup)
    from src.tests.test_machine_adaptive_exit_group_execution import runner_market

    runner_market(wire, filled=0, remaining=6)
    flags["halt_ms"] = None
    state = step(new(), flags, 1001)
    assert state["adaptive_exit_loop_status"] == "group_clock_source_gap"
    assert SESSION_KEY in state and len(wire.writes) == 2
    flat_market(wire)
    state = step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "execution_terminal_handoff_completed"
    assert SESSION_KEY not in state and len(wire.writes) == 2


@pytest.mark.parametrize("halt", [True, -1, "0", NOW])
def test_malformed_group_clock_blocks_before_broker_read(setup, halt):
    machine, _, wire, flags = setup
    flags["halt_ms"] = halt
    state = step(machine, flags)
    assert "group_clock_value_invalid" in state["adaptive_exit_loop_status"]
    assert not wire.calls and not wire.writes


def test_clock_rechecked_after_authority_validator_before_write(setup):
    machine, _, wire, flags = setup
    services = machine.adaptive_exit_services

    def lose_clock(*args):
        flags["halt_ms"] = None
        return True

    machine.adaptive_exit_services = replace(
        services, group=replace(services.group, authorize_action=lose_clock)
    )
    state = step(machine, flags)
    assert SESSION_KEY in state and not wire.writes


@pytest.mark.parametrize("fault", ["missing_lot", "foreign_lot", "stale", "bool_now"])
def test_group_clock_identity_coverage_is_not_inferred(setup, fault):
    machine, _, wire, flags = setup
    services = machine.adaptive_exit_services
    old = services.group.clock_loader

    def clocks(session, now):
        value = old(session, now)
        if fault == "missing_lot":
            value.pop("target_lot")
        elif fault == "foreign_lot":
            value["foreign"] = Clock(now, 0)
        else:
            value["target_lot"] = Clock(now - 1 if fault == "stale" else True, 0)
        return value

    machine.adaptive_exit_services = replace(
        services, group=replace(services.group, clock_loader=clocks)
    )
    state = step(machine, flags)
    assert "group_clock_" in state["adaptive_exit_loop_status"]
    assert not wire.calls and not wire.writes


def test_group_price_observations_cannot_replace_independent_clock(setup):
    machine, _, wire, flags = setup
    flags["halt_ms"] = 1  # The price fixture still claims zero.
    state = step(machine, flags)
    assert "group_observation_clock_mismatch" in state["adaptive_exit_loop_status"]
    assert SESSION_KEY in state and not wire.writes


def test_existing_runner_cancel_closes_without_clock_or_new_cancel(setup):
    from src.tests.test_machine_adaptive_exit_group_execution import runner_market

    machine, new, wire, flags = setup
    sell(setup)
    runner_market(wire, filled=2, remaining=4)
    wire.write_body = {
        "return_code": 0,
        "ord_no": "0000006",
        "dmst_stex_tp": "SOR",
        "base_orig_ord_no": "0000005",
        "cncl_qty": "4",
    }
    assert (
        step(machine, flags, 1001)["adaptive_exit_loop_status"]
        == "runner_cancel_pending"
    )
    flags["halt_ms"] = None
    runner_market(wire, filled=2, remaining=0, ttl_child=True)
    state = step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "runner_residual_requires_recovery"
    assert SESSION_KEY in state and len(wire.writes) == 3
    assert state["completed_entry_count"] == 2


@pytest.mark.parametrize("flag", ["lock", "approval", "guard"])
def test_missing_approval_or_original_lock_cannot_even_load_broker_source(setup, flag):
    machine, _, wire, flags = setup
    flags[flag] = False
    state = step(machine, flags)
    assert SESSION_KEY in state and not wire.calls and not wire.writes


@pytest.mark.parametrize(
    "failure",
    [
        "double_owner",
        "pending_buy",
        "manual_exit",
        "foreign_qty",
        "buy_partial",
        "buy_price",
        "target_identity",
        "buy_owner",
    ],
)
def test_competing_or_mismatched_owner_is_not_adopted(setup, failure):
    machine, _, wire, flags = setup
    state = machine._state["symbols"]["005930"]
    if failure == "double_owner":
        state["adaptive_exit_sessions"] = {}
    elif failure == "pending_buy":
        state["pending_entry_confirmation"] = {"signal": "pending"}
    elif failure == "manual_exit":
        state["exit_requested"] = True
    elif failure == "foreign_qty":
        state["prior_day_unmanaged_qty"] = 1
    elif failure == "buy_partial":
        state["orders"][0]["filled_qty"] = 3
    elif failure == "buy_price":
        state["orders"][0]["fill_price"] = None
    elif failure == "buy_owner":
        state["orders"][0]["owner_id"] = "manual"
    else:
        state["orders"][-1]["parent_entry_signal_id"] = "other"
    result = step(machine, flags)
    assert SESSION_KEY in result and result["entry_episode_open"] is True
    assert result["completed_entry_count"] == 2
    assert not wire.calls and not wire.writes


def test_no_group_service_does_not_fall_through_to_normal_buy_or_exit(setup):
    machine, _, wire, flags = setup
    machine.adaptive_exit_services = replace(machine.adaptive_exit_services, group=None)
    assert (
        step(machine, flags)["adaptive_exit_loop_status"]
        == "group_owner_services_missing"
    )
    assert not wire.calls and not wire.writes


def test_missing_source_after_release_retains_manager_and_original_target(setup):
    machine, _, wire, flags = setup
    step(machine, flags)
    confirmed(wire)
    flags["source"] = False
    result = step(machine, flags, 1)
    assert "source_clock_missing" in result["adaptive_exit_loop_status"]
    assert SESSION_KEY in result and result["entry_episode_open"]
    assert len(wire.writes) == 1


def test_original_target_still_working_does_not_release_episode(setup):
    machine, _, wire, flags = setup
    sell(setup)
    from src.tests.test_machine_adaptive_exit_group_execution import runner_market

    runner_market(wire, filled=6, remaining=0)
    result = step(machine, flags, 1)
    assert result["adaptive_exit_loop_status"] == "group_orders_working"
    assert result["entry_episode_open"] and result["completed_entry_count"] == 2


def test_previously_confirmed_cancel_remains_proof_not_a_second_order(setup):
    machine, _, wire, flags = setup
    sell(setup)
    flat_market(wire)
    wire.detailed = [r for r in wire.detailed if r["ord_no"] != "0000003"]
    state = step(machine, flags, 1)
    # Already durable positive partial-cancel proof remains valid; latest target
    # must still be reconcilable. This test does not erase historical receipts.
    assert state["completed_entry_count"] == 3
    assert state["adaptive_exit_history"][-1]["group_terminal"]["cancel_proofs"]
    assert len(wire.writes) == 2


def test_unknown_record_slot_blocks_instead_of_silently_dropping_state(setup):
    machine, _, wire, flags = setup
    raw = machine._state["symbols"]["005930"][SESSION_KEY]
    record = {"x": 1}
    record["canonical_sha256"] = canonical_sha256(record)
    raw["records"]["a" * 64] = record
    raw["canonical_sha256"] = canonical_sha256(raw)
    state = step(machine, flags)
    assert "unrecognized_durable_slot" in state["adaptive_exit_loop_status"]
    assert not wire.calls and not wire.writes


def test_cross_date_keeps_group_and_orders_without_new_entries(setup):
    machine, new, wire, flags = setup
    step(machine, flags)
    state = step(new(), flags, 86400000)
    assert SESSION_KEY in state and "cross_date" in state["adaptive_exit_loop_status"]
    assert all(o["order_date"] == DATE for o in state["orders"])
    assert len(wire.writes) == 1


def test_session_round_trip_does_not_reassign_tuple_or_policy_hash(setup):
    machine, _, _, _ = setup
    raw = machine._state["symbols"]["005930"][SESSION_KEY]
    assert (
        GroupOwnerSession.from_payload(json.loads(json.dumps(raw))).to_payload() == raw
    )
    changed = deepcopy(raw)
    changed["definition"]["bounds"]["maximum_sell_attempts"] = True
    changed["canonical_sha256"] = canonical_sha256(changed)
    with pytest.raises(ValueError):
        GroupOwnerSession.from_payload(changed)


def test_frozen_target_natural_full_fill_closes_without_any_cancel(setup):
    from src.tests.test_machine_adaptive_exit_broker import detail

    machine, new, wire, flags = setup
    flags["bid"] = 70100
    state = step(machine, flags)
    assert not wire.writes and SESSION_KEY in state
    wire.detailed, wire.current = [detail(cntr_qty="10", ord_remnq="0")], []
    state = step(new(), flags, 1)
    assert SESSION_KEY not in state and state["completed_entry_count"] == 3
    assert not wire.writes


@pytest.mark.parametrize("lag_ms", [1, 1500])
def test_cycle_start_is_not_reused_as_the_current_source_decision_clock(setup, lag_ms):
    machine, _, wire, flags = setup
    machine.run_once(datetime.fromtimestamp((flags["now"] - lag_ms) / 1000, widget.KST))
    assert len(wire.writes) == 1


@pytest.mark.parametrize("failure", ["raise", "noop"])
def test_original_owner_store_failure_cannot_be_successful_release(
    setup, monkeypatch, failure
):
    machine, new, wire, flags = setup
    old = machine.state_path.read_bytes()

    def bad_save():
        if failure == "raise":
            raise OSError("disk unavailable")

    monkeypatch.setattr(machine, "_save", bad_save)
    with pytest.raises(OSError):
        step(machine, flags)
    assert not wire.writes and machine.state_path.read_bytes() == old
    state = step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "order_bound" and len(wire.writes) == 1


def test_terminal_archival_save_failure_recovers_without_second_sell_or_count(
    setup, monkeypatch
):
    machine, new, wire, flags = setup
    sell(setup)
    flat_market(wire)
    save = machine._save

    def lose_archive():
        if SESSION_KEY not in machine._state["symbols"]["005930"]:
            return
        save()

    monkeypatch.setattr(machine, "_save", lose_archive)
    with pytest.raises(OSError, match="terminal_file_readback"):
        step(machine, flags, 1)
    assert len(wire.writes) == 2
    state = step(new(), flags, 1)
    assert SESSION_KEY not in state and state["completed_entry_count"] == 3
    receipt_ms = state["adaptive_exit_history"][-1]["group_terminal"]["observed_at_ms"]
    assert (
        int(
            datetime.fromisoformat(state["last_episode_completed_at"]).timestamp()
            * 1000
        )
        == receipt_ms
    )
    assert len(wire.writes) == 2


def test_invalid_durable_file_is_preserved_for_recovery_not_overwritten(
    setup, monkeypatch
):
    machine, new, wire, flags = setup
    monkeypatch.setattr(machine, "_save", lambda: machine.state_path.write_text("{"))
    with pytest.raises(OSError, match="durable_file_invalid"):
        step(machine, flags)
    assert machine.state_path.read_text() == "{" and not wire.writes
    with pytest.raises(ValueError, match="owner_state_unreadable"):
        new()


def test_action_validator_loss_after_source_cannot_send_release(setup):
    machine, _, wire, flags = setup
    services = machine.adaptive_exit_services.group

    def loss(*args):
        value = services.observations_loader(*args)
        flags["action"] = False
        return value

    machine.adaptive_exit_services = replace(
        machine.adaptive_exit_services,
        group=replace(services, observations_loader=loss),
    )
    state = step(machine, flags)
    assert SESSION_KEY in state and not wire.writes


def test_guard_detecting_lock_loss_cannot_query_or_persist(setup):
    machine, _, wire, flags = setup
    old = machine.state_path.read_bytes()
    services = machine.adaptive_exit_services.group

    def loss(binding):
        flags["lock"] = False
        return True

    machine.adaptive_exit_services = replace(
        machine.adaptive_exit_services, group=replace(services, owner_guard=loss)
    )
    step(machine, flags)
    assert not wire.calls and machine.state_path.read_bytes() == old


@pytest.mark.parametrize(
    "index,field",
    [
        (0, "owner_registry_intent_id"),
        (0, "owner_client_intent_id"),
        (2, "owner_registry_intent_id"),
    ],
)
def test_ordinary_order_registry_identity_must_match_before_io(setup, index, field):
    machine, _, wire, flags = setup
    machine._state["symbols"]["005930"]["orders"][index][field] = "other"
    state = step(machine, flags)
    assert SESSION_KEY in state and not wire.calls


@pytest.mark.parametrize(
    "action,blocked",
    [("observe_only_no_forced_sell", False), ("sell_own_filled_quantity", True)],
)
def test_original_source_exit_is_not_promoted_to_runner_or_forced_sell(
    setup, monkeypatch, action, blocked
):
    machine, _, wire, flags = setup
    state = machine._state["symbols"]["005930"]
    state["entry_execution_policy"] = {"source_final_exit_action": action}
    monkeypatch.setattr(machine, "_exit_signal", lambda *a: "exact-source-exit")
    machine.process_payload(
        SimpleNamespace(code="005930"),
        {},
        datetime.fromtimestamp(flags["now"] / 1000, widget.KST),
    )
    assert bool(state.get("adaptive_exit_group_recovery_reason")) is blocked
    assert len(wire.writes) == (0 if blocked else 1)
    assert SESSION_KEY in state and state["entry_episode_open"]


def test_force_flat_boundary_is_explicit_not_silently_ignored(setup):
    machine, _, wire, flags = setup
    state = machine._state["symbols"]["005930"]
    state["entry_execution_policy"] = {
        "force_flat_at_session_end": True,
        "force_exit_time": "09:00",
    }
    result = step(machine, flags)
    assert (
        result["adaptive_exit_group_recovery_reason"]
        == "force_flat_requires_group_arbitration"
    )
    assert not wire.calls


def test_bounded_residual_retry_reaches_actual_widget_terminal_handoff(setup):
    from src.tests import test_machine_adaptive_exit_group_retry as retry
    from src.tests.test_machine_adaptive_exit_group_execution import action
    from src.tests.test_machine_adaptive_exit_broker import detail

    machine, _, wire, flags = setup
    raw = machine._state["symbols"]["005930"][SESSION_KEY]
    raw["definition"]["bounds"]["maximum_sell_attempts"] = 2
    raw["canonical_sha256"] = canonical_sha256(raw)
    services = machine.adaptive_exit_services
    machine.adaptive_exit_services = replace(
        services,
        group=replace(
            services.group,
            authorize_retry=lambda *a: True,
            retry_action_loader=lambda s, n, now: action(
                "SELL_RUNNER", now=now, price=70300
            ),
        ),
    )
    sell(setup)
    retry.runner(wire, "0000005", 6, 2, 4)
    retry.ack(wire, "0000006", "0000005", 4)
    assert (
        step(machine, flags, 1000)["adaptive_exit_loop_status"]
        == "runner_cancel_pending"
    )
    retry.runner(wire, "0000005", 6, 2, 0)
    wire.detailed.append(
        detail(
            ord_no="0000006",
            ori_ord="0000005",
            ord_qty="4",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty="4",
            cnfm_tm="12:59:59",
        )
    )
    retry.ack(wire, "0000007")
    assert step(machine, flags, 1)["adaptive_exit_loop_status"] == "order_bound"
    assert wire.writes[-1]["payload"]["ord_qty"] == "4"
    retry.runner(wire, "0000007", 4, 4, 0)
    retry.runner(wire, TARGET.order_no, 10, 4, 0)
    state = step(machine, flags, 1)
    assert state["completed_entry_count"] == 3 and SESSION_KEY not in state
    assert [
        r["filled_qty"]
        for r in state["adaptive_exit_history"][-1]["group_terminal"]["orders"]
    ] == [4, 2, 4]
    assert len(wire.writes) == 4
