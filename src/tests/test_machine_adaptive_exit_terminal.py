"""Exact execution closure is independent from delayed net economics."""

from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.tests import test_machine_adaptive_exit_owner_loop as owner_fixtures
from src.tests.test_machine_adaptive_exit_broker import detail, current, DATE
from src.tests.test_machine_adaptive_exit_runtime import working_exit, cancel_detail
from src.trading.order.adaptive_exit.runtime import OwnerSession
from src.trading.order.adaptive_exit.terminal import TERMINAL_KEY, validate_terminal
from src.trading.widget_auto_trade import engine as widget

loop = owner_fixtures.loop


def close(loop, target_fill=0):
    if target_fill:
        loop.wire.detailed = [
            detail(cntr_qty=str(target_fill), ord_remnq=str(10 - target_fill))
        ]
        loop.wire.current = [
            current(cntr_qty=str(target_fill), oso_qty=str(10 - target_fill))
        ]
        loop.tick()
    loop.wire.write_body["cncl_qty"] = str(10 - target_fill)
    loop.tick()
    loop.wire.detailed = [
        detail(cntr_qty=str(target_fill), ord_remnq="0"),
        cancel_detail(requested=10 - target_fill),
    ]
    loop.wire.current = []
    loop.tick()
    loop.wire.write_body["ord_no"] = "0000004"
    loop.tick()
    working_exit(loop.wire, fill=10 - target_fill, remaining=0)
    loop.wire.detailed[-1]["ord_qty"] = str(10 - target_fill)
    loop.flags["quote"] = False
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "FLAT"


def receipt(loop):
    if loop.owner == "episode":
        return loop.machine._state["legs"][0][TERMINAL_KEY]
    return next(
        iter(
            loop.machine._state["symbols"]["005930"]["adaptive_exit_history"][-1][
                "terminals"
            ].values()
        )
    )


@pytest.mark.parametrize("target_fill", [0, 4])
def test_exact_quantity_terminal_does_not_invent_cost_or_profit(loop, target_fill):
    close(loop, target_fill)
    r = receipt(loop)
    validate_terminal(r, OwnerSession.from_payload(loop.record()))
    assert [row["filled_qty"] for row in r["orders"]] == [target_fill, 10 - target_fill]
    assert r["buy_filled_qty"] == r["sell_filled_qty"] == 10
    assert r["realized_net_profit_krw"] is None
    assert r["economic_acceptance"] is False and r["new_entry_authority"] is False
    assert all(
        row["commission_krw"] is None and row["fill_amount_krw"] is None
        for row in r["orders"]
    )
    if loop.owner == "widget":
        state = loop.machine._state["symbols"]["005930"]
        assert (
            state["completed_entry_count"] == 1 and state["entry_episode_open"] is False
        )
        assert not state.get("take_profit_completed_at")
        assert loop.machine._open_qty(state) == 0
        assert len(state["orders"]) == 3
        assert state["orders"][-1]["order_role"] == "ADAPTIVE_EXIT_SELL"
        assert state["orders"][-1]["fill_price"] is None
    else:
        assert loop.machine._state["attempt_consumed"] is True
        assert loop.machine._state["status"] == "ADAPTIVE_EXIT_FLAT"
    loop.machine._state = loop.machine._load_state()
    before = deepcopy(loop.machine._state)
    calls = len(loop.wire.calls)
    loop.tick()
    assert receipt(loop) == r
    assert len(loop.wire.calls) == calls
    if loop.owner == "widget":
        assert loop.machine._state == before


def test_next_entry_reaches_original_owner_only_after_terminal(loop, monkeypatch):
    close(loop)
    calls = len(loop.wire.calls)
    if loop.owner == "episode":
        prior = deepcopy(loop.machine._state)
        loop.clock[0] += 86400000
        loop.tick()
        assert loop.machine._state["trade_date"] != DATE
        assert loop.machine._state["status"] == "READY"
        assert loop.machine._state["adaptive_exit_history"] == [prior]
        assert loop.machine._state["attempt_consumed"] is False
        invoked = []
        monkeypatch.setattr(
            loop.machine,
            "_consider_entry",
            lambda now: invoked.append(now) or loop.machine.snapshot(),
        )
        loop.tick()
        assert len(invoked) == 1
        # Another ordinary rollover must not discard delayed-cost evidence.
        loop.clock[0] += 86400000
        loop.tick()
        assert loop.machine._state["adaptive_exit_history"] == [prior]
    else:

        class OriginalEntryPath(Exception):
            pass

        def original(*args):
            raise OriginalEntryPath

        monkeypatch.setattr(loop.machine, "_reconcile", original)
        with pytest.raises(OriginalEntryPath):
            loop.machine.process_payload(
                SimpleNamespace(code="005930"),
                {},
                datetime.fromtimestamp(loop.clock[0] / 1000, widget.KST),
            )
        assert loop.machine._state["symbols"]["005930"]["completed_entry_count"] == 1
    assert len(loop.wire.calls) == calls


def test_terminal_persistence_failure_keeps_claim_for_idempotent_recovery(
    loop, monkeypatch
):
    if loop.owner == "widget":
        original = loop.machine._finish_adaptive_episode
        monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", lambda *a: None)
        close(loop)
        before = deepcopy(loop.machine._state)
        monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", original)
    else:
        close(loop)
        del loop.machine._state["legs"][0][TERMINAL_KEY]
        loop.machine._save()
        before = deepcopy(loop.machine._state)
    original_save = loop.machine._save
    monkeypatch.setattr(
        loop.machine, "_save", lambda: (_ for _ in ()).throw(OSError("disk"))
    )
    with pytest.raises(OSError):
        loop.tick()
    assert loop.machine._state == before
    monkeypatch.setattr(loop.machine, "_save", original_save)
    loop.tick()
    assert receipt(loop)["execution_status"] == "reconciled_flat"
    assert len(loop.wire.writes) == 2


@pytest.mark.parametrize("missing", ["lock", "authority", "services"])
def test_terminal_cannot_release_without_owner_authority(loop, monkeypatch, missing):
    if loop.owner == "widget":
        original = loop.machine._finish_adaptive_episode
        monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", lambda *a: None)
        close(loop)
        monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", original)
    else:
        close(loop)
        loop.clock[0] += 86400000
    if missing == "services":
        loop.machine.adaptive_exit_services = None
    else:
        loop.flags[missing] = False
    loop.tick()
    assert "adaptive_exit_history" not in (
        loop.machine._state
        if loop.owner == "episode"
        else loop.machine._state["symbols"]["005930"]
    )
    assert len(loop.wire.writes) == 2


def test_rehashed_terminal_row_conflict_cannot_be_accepted(loop, monkeypatch):
    from src.trading.config.machine_adaptive_exit_policy import canonical_sha256

    if loop.owner == "widget":
        original = loop.machine._finish_adaptive_episode
        monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", lambda *a: None)
        close(loop)
        monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", original)
        r = next(iter(loop.machine._state["symbols"]["005930"][TERMINAL_KEY].values()))
    else:
        close(loop)
        r = receipt(loop)
    r["orders"][-1]["filled_qty"] = 9
    r["canonical_sha256"] = canonical_sha256(
        {k: v for k, v in r.items() if k != "canonical_sha256"}
    )
    loop.tick()
    assert "receipt_conflict" in loop.status()
    assert len(loop.wire.writes) == 2


def test_target_only_completion_has_no_replacement_or_profit_claim(loop):
    loop.wire.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    loop.wire.current = []
    loop.tick()
    r = receipt(loop)
    assert len(r["orders"]) == 1 and r["orders"][0]["filled_qty"] == 10
    assert r["realized_net_profit_krw"] is None and not loop.wire.writes


@pytest.mark.parametrize("missing", ["child", "confirmation", "zero_confirmation"])
def test_target_terminal_without_cancel_confirmation_keeps_owner(loop, missing):
    loop.tick()
    assert len(loop.wire.writes) == 1
    child = cancel_detail()
    if missing == "confirmation":
        child.pop("cnfm_qty")
    elif missing == "zero_confirmation":
        child["cnfm_qty"] = "0"
    loop.wire.detailed = [detail(ord_remnq="0")]
    if missing != "child":
        loop.wire.detailed.append(child)
    loop.wire.current = []
    for _ in range(2):
        loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "CANCEL_PENDING"
    assert len(loop.wire.writes) == 1
    state = (
        loop.machine._state
        if loop.owner == "episode"
        else loop.machine._state["symbols"]["005930"]
    )
    assert not state.get("adaptive_exit_history")
    assert not state.get("completed_entry_count")
    assert OwnerSession.from_payload(loop.record()).driver.orders.open_qty == 10
    # Exact positive proof later resumes the same owner without another cancel.
    if missing == "child":
        loop.wire.detailed.append(cancel_detail())
    else:
        loop.wire.detailed[-1] = cancel_detail()
    loop.tick()
    assert loop.record()["driver"]["orders"]["phase"] == "RESIDUAL_READY"
    assert len(loop.wire.writes) == 1


@pytest.mark.parametrize("receipt_first", [True, False])
def test_shared_ws_terminal_and_dated_reconciliation_can_arrive_in_either_order(
    loop, receipt_first
):
    session = OwnerSession.from_payload(loop.record())
    registry = loop.machine.owner_registry

    def shared_receipt():
        registry.record_fill(
            context=session.context,
            symbol="005930",
            side="SELL",
            order_quantity=10,
            order_date=DATE,
            broker_order_no="0000002",
            cumulative_filled_qty=10,
            cumulative_fill_amount=101000,
            execution_no="1",
        )
        registry.transition(
            session.target_intent_id,
            state="ORDER_TERMINAL",
            broker_order_no="0000002",
            reason="shared_ws_execution_receipt_terminal",
        )

    if receipt_first:
        shared_receipt()
    loop.wire.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    loop.wire.current = []
    loop.tick()
    r = receipt(loop)
    if not receipt_first:
        shared_receipt()
    loop.machine._state = loop.machine._load_state()
    loop.tick()
    assert receipt(loop) == r
    assert r["execution_status"] == "reconciled_flat"
    assert r["realized_net_profit_krw"] is None
    assert not loop.wire.writes


def test_shared_ws_replacement_terminal_does_not_strand_closed_lot(loop, monkeypatch):
    registry = loop.machine.owner_registry
    original = registry.record_terminal_reconciliation

    def receive_first(**kwargs):
        if kwargs["broker_order_no"] == "0000004":
            # The shared receipt won the transition race in this same cycle.
            # Generic terminal idempotence must not suppress separate proof.
            row = registry.order_owner(order_date=DATE, broker_order_no="0000004")
            assert row["state"] == "ORDER_TERMINAL"
        original(**kwargs)

    monkeypatch.setattr(registry, "record_terminal_reconciliation", receive_first)
    original_transition = registry.transition

    def transition(intent, **kwargs):
        if (
            kwargs.get("broker_order_no") == "0000004"
            and kwargs.get("state") == "ORDER_TERMINAL"
        ):
            original_transition(
                intent, **(kwargs | {"reason": "shared_ws_execution_receipt_terminal"})
            )
        original_transition(intent, **kwargs)

    monkeypatch.setattr(registry, "transition", transition)
    close(loop, target_fill=4)
    r = receipt(loop)
    assert [row["filled_qty"] for row in r["orders"]] == [4, 6]
    row = registry.order_owner(order_date=DATE, broker_order_no="0000004")
    assert row["reason"] == "shared_ws_execution_receipt_terminal"
    assert (
        row["terminal_reconciliation"]["receipt_sha256"]
        == r["orders"][-1]["reconciliation_sha256"]
    )
    assert len(loop.wire.writes) == 2


def test_missing_terminal_receipt_retains_episode_manager(loop):
    if loop.owner != "episode":
        pytest.skip("episode manager only")
    close(loop)
    assert not loop.machine.adaptive_exit_manager_required()
    del loop.machine._state["legs"][0][TERMINAL_KEY]
    assert loop.machine.adaptive_exit_manager_required()


def test_widget_late_prior_day_completion_does_not_spend_today_cap(loop, monkeypatch):
    if loop.owner != "widget":
        pytest.skip("widget daily entry cap only")
    original = loop.machine._finish_adaptive_episode
    monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", lambda *a: None)
    close(loop)
    old = deepcopy(loop.machine._state["symbols"]["005930"])
    monkeypatch.setattr(loop.machine, "_finish_adaptive_episode", original)
    loop.clock[0] += 86400000
    loop.tick()
    state = loop.machine._state["symbols"]["005930"]
    assert state["orders"] == [] and state["entry_signal_id"] is None
    assert not state.get("completed_entry_count")
    archived = loop.machine._state["history"][-1]
    assert archived["trade_date"] == DATE
    assert archived["symbols"]["005930"]["completed_entry_count"] == 1
    assert (
        archived["symbols"]["005930"]["adaptive_exit_history"][-1]["sessions"]
        == old["adaptive_exit_sessions"]
    )
    assert len(loop.wire.writes) == 2


@pytest.mark.parametrize("mutation", ["state", "filled", "proof", "chain"])
def test_terminal_requires_exact_registry_chain_not_only_self_hash(
    loop, monkeypatch, mutation
):
    from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
    from src.trading.order.adaptive_exit.terminal import terminal_receipt

    close(loop)
    session = OwnerSession.from_payload(loop.record())
    adapter = loop.machine.gateway.adaptive_exit_adapter(
        registry=loop.machine.owner_registry,
        context=session.context,
        policy_hash=session.policy.policy_hash,
        write_guard=lambda request: False,
    )
    original = RegisteredSellAdapter._owned

    def broken(self, key):
        row = dict(original(self, key))
        if key.order_no == "0000004":
            row.update(
                {
                    "state": {"state": "ORDER_BOUND"},
                    "filled": {"filled_qty": 9},
                    "proof": {"terminal_reconciliation": None},
                    "chain": {"client_intent_id": "unrelated"},
                }[mutation]
            )
        return row

    monkeypatch.setattr(RegisteredSellAdapter, "_owned", broken)
    with pytest.raises(ValueError):
        terminal_receipt(session=session, adapter=adapter, observed_at_ms=loop.clock[0])


def test_two_independent_lots_close_one_owner_episode(loop):
    from dataclasses import replace
    from src.trading.order.adaptive_exit.reducer import OrderKey

    initial = OwnerSession.from_payload(loop.record())
    registry = loop.machine.owner_registry
    context = replace(initial.context, client_intent_id="second-target")
    registry.register_migrated_position(
        context=replace(context, client_intent_id="second-entry"),
        symbol="005930",
        quantity=10,
        average_price=10000,
        route="SOR",
        order_date=DATE,
        broker_order_no="0000006",
        evidence_sha256="d" * 64,
    )
    target_id = registry.reserve(
        context=context,
        symbol="005930",
        side="SELL",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(target_id, state="ORDER_BOUND", broker_order_no="0000005")
    lot_id = "signal_close_minus_1tick" if loop.owner == "episode" else target_id
    second = replace(
        initial,
        context=context,
        target_intent_id=target_id,
        position=replace(initial.position, lot_id=lot_id),
        driver=replace(
            initial.driver,
            orders=replace(
                initial.driver.orders, lot_id=lot_id, target=OrderKey(DATE, "0000005")
            ),
        ),
    )
    if loop.owner == "episode":
        from src.trading.order.adaptive_exit.owner_loop import SESSION_KEY

        leg = deepcopy(loop.machine._state["legs"][0])
        leg.update(
            leg_id=lot_id,
            order_type=lot_id,
            buy_order_no="0000006",
            target_order_no="0000005",
            target_owner_registry_intent_id=target_id,
        )
        leg[SESSION_KEY] = second.to_payload()
        loop.machine._state["legs"][1] = leg
        loop.machine._state["owned_order_nos"].extend(["0000005", "0000006"])
        loop.machine._sync_aggregate()
    else:
        state = loop.machine._state["symbols"]["005930"]
        entry, target = deepcopy(state["orders"])
        entry["order_no"] = "0000006"
        target.update(
            order_no="0000005",
            owner_registry_intent_id=target_id,
            owner_client_intent_id="second-target",
        )
        state["orders"].extend([entry, target])
        state["adaptive_exit_sessions"][lot_id] = second.to_payload()
    loop.wire.detailed = [
        detail(cntr_qty="10", ord_remnq="0"),
        detail(ord_no="0000005", cntr_qty="10", ord_remnq="0"),
    ]
    loop.wire.current = []
    loop.tick()
    assert not loop.wire.writes
    if loop.owner == "episode":
        assert loop.machine._state["position_qty"] == 0
        assert all(leg.get(TERMINAL_KEY) for leg in loop.machine._state["legs"])
    else:
        state = loop.machine._state["symbols"]["005930"]
        assert loop.machine._open_qty(state) == 0
        assert state["completed_entry_count"] == 1
        assert len(state["adaptive_exit_history"][-1]["terminals"]) == 2
