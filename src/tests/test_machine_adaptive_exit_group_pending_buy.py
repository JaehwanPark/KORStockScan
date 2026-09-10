"""Actual ordinary widget owner -> pending BUY close -> pooled EXIT -> archive."""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests import test_machine_adaptive_exit_group_owner_loop as owner
from src.tests import test_machine_adaptive_exit_group_whole_exit as whole
from src.tests.test_machine_adaptive_exit_broker import DATE, detail, current, response
from src.trading.order.adaptive_exit.group_owner_loop import SESSION_KEY
from src.trading.order.adaptive_exit.group_settlement import closed_census

BUY_NO = "0000009"
CANCEL_NO = "0000010"


def test_clock_gap_reconciles_pending_buy_without_cancel_or_residual_sell(setup):
    machine, new, wire, flags = setup
    whole.force(machine)
    flags["halt_ms"] = None
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "group_clock_source_gap"
    assert SESSION_KEY in state and not wire.writes
    assert state["completed_entry_count"] == 2


@pytest.fixture
def setup(tmp_path, monkeypatch):
    machine, old_new, wire, flags = whole.setup.__wrapped__(tmp_path, monkeypatch)
    state = machine._state["symbols"]["005930"]
    context = machine._owner_context_from_order(state["orders"][-1])
    context = replace(context, client_intent_id="pending-scale-in")
    registry = machine.owner_registry
    intent = registry.reserve(
        context=context,
        symbol="005930",
        side="BUY",
        quantity=4,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no=BUY_NO)
    registry.record_fill(
        context=context,
        symbol="005930",
        side="BUY",
        order_quantity=4,
        order_date=DATE,
        broker_order_no=BUY_NO,
        cumulative_filled_qty=1,
    )
    order = dict(
        side="BUY",
        order_role="SCALE_IN_BUY",
        order_date=DATE,
        order_no=BUY_NO,
        requested_qty=4,
        filled_qty=1,
        remaining_qty=3,
        status="SUBMITTED",
        fill_price=70000,
        owner_id=context.owner_id,
        owner_position_id=context.position_id,
        owner_client_intent_id=context.client_intent_id,
        owner_registry_intent_id=intent,
        route="SOR",
        broker_route="SOR",
        broker_accepted=True,
        parent_entry_signal_id="signal",
    )
    state["orders"].append(order)
    state["scale_in_requested"] = True
    state["pending_entry_confirmation"] = {
        "intent": "old-scale-in-source",
        "observed_at": "test-only",
    }
    flags["buy_filled"], flags["buy_remaining"], flags["confirmed"] = 1, 3, None
    flags["maximum_quantity"] = 20

    def post(**kwargs):
        api, payload = kwargs["api_id"], kwargs["payload"]
        if (
            api in {"kt00007", "ka10075"}
            and payload.get("sell_tp", payload.get("trde_tp")) == "2"
        ):
            wire.calls.append(kwargs)
            filled, remain = flags["buy_filled"], flags["buy_remaining"]
            if api == "kt00007":
                rows = [
                    detail(
                        ord_no=BUY_NO,
                        ord_qty="4",
                        cntr_qty=str(filled),
                        ord_remnq=str(remain),
                    )
                ]
                if flags["confirmed"] is not None:
                    rows.append(
                        detail(
                            ord_no=CANCEL_NO,
                            ori_ord=BUY_NO,
                            ord_qty="3",
                            cntr_qty="0",
                            ord_remnq="0",
                            cnfm_qty=str(flags["confirmed"]),
                            cnfm_tm="13:00:00",
                        )
                    )
                return response({"return_code": 0, "acnt_ord_cntr_prps_dtl": rows})
            rows = (
                [
                    current(
                        ord_no=BUY_NO,
                        ord_qty="4",
                        cntr_qty=str(filled),
                        oso_qty=str(remain),
                    )
                ]
                if remain
                else []
            )
            return response({"return_code": 0, "oso": rows})
        return wire(**kwargs)

    def adapt(m):
        factory = m.gateway.adaptive_exit_adapter

        def gateway(**kwargs):
            adapter = factory(**kwargs)
            adapter.post = post
            adapter.maximum_quantity = flags["maximum_quantity"]
            return adapter

        m.gateway.adaptive_exit_adapter = gateway
        return m

    adapt(machine)
    whole.force(machine)
    machine._save()
    return machine, lambda: adapt(old_new()), wire, flags


def close_buy(setup):
    machine, new, wire, flags = setup
    whole.ack(wire, CANCEL_NO, BUY_NO, 3)
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["orig_ord_no"] == BUY_NO
    request = whole.journal(state)["request"]
    assert request["pending_buys"][0]["initial_filled_qty"] == 1
    assert len(state[SESSION_KEY]["definition"]["group"]["lots"]) == 2
    flags.update(buy_filled=2, buy_remaining=0, confirmed=2)
    machine = new()
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_cancel_reconciliation"
    return machine, state


def sell_residual(setup):
    machine, _ = close_buy(setup)
    _, _, wire, flags = setup
    whole.ack(wire, "0000003", "0000002", 10)
    assert (
        owner.step(machine, flags)["adaptive_exit_loop_status"]
        == "whole_exit_order_bound"
    )
    whole.root(wire, "0000002", 10, 1, 0)
    whole.canceled(wire, "0000003", "0000002", 10, 9)
    owner.step(machine, flags)
    whole.ack(wire, "0000005")
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["ord_qty"] == "11"
    return machine, state


def test_pending_buy_late_fill_enters_pooled_sell_and_actual_widget_archive(setup):
    machine, _ = sell_residual(setup)
    _, new, wire, flags = setup
    whole.root(wire, "0000005", 11, 11, 0)
    owner.step(machine, flags)
    state = owner.step(new(), flags)
    assert state["adaptive_exit_loop_status"] == "execution_terminal_handoff_completed"
    assert state["entry_episode_open"] is False
    assert (
        state["pending_entry_confirmation"] is None
        and state["scale_in_requested"] is False
    )
    receipt = state["adaptive_exit_history"][-1]["group_terminal"]
    assert receipt["buy_filled_qty"] == receipt["sell_filled_qty"] == 12
    assert len(receipt["cancel_proofs"]) == 2
    buy = next(o for o in state["orders"] if o["order_no"] == BUY_NO)
    assert (
        buy["filled_qty"] == 2
        and buy["status"] == "TERMINAL_UNFILLED"
        and buy["fill_price"] is None
    )
    assert buy["remaining_qty"] == 0 and buy["reconciliation_sha256"]
    assert (
        receipt["realized_net_profit_krw"] is None
        and receipt["economic_acceptance"] is False
    )
    assert len(wire.writes) == 3
    assert (
        state["adaptive_exit_history"][-1]["superseded_pending_entry_confirmation"][
            "intent"
        ]
        == "old-scale-in-source"
    )
    assert state["adaptive_exit_history"][-1]["superseded_scale_in_requested"] is True


@pytest.mark.parametrize(
    "bad",
    ["parent", "owner", "ordinary_qty", "unknown_status", "duplicate", "missing_guard"],
)
def test_invalid_pending_buy_cannot_be_adopted_from_symbol_or_quantity(setup, bad):
    machine, _, wire, flags = setup
    state = machine._state["symbols"]["005930"]
    order = state["orders"][-1]
    if bad == "parent":
        order["parent_entry_signal_id"] = "other-entry"
    elif bad == "owner":
        order["owner_id"] = "manual"
    elif bad == "ordinary_qty":
        order["requested_qty"] = 5
    elif bad == "unknown_status":
        order["status"] = "AMBIGUOUS"
    elif bad == "duplicate":
        state["orders"].append(deepcopy(order))
    else:
        flags["whole_action"] = False
    owner.step(machine, flags)
    assert not wire.writes and SESSION_KEY in state


@pytest.mark.parametrize("changed", ["ordinary", "confirmation", "scalein"])
def test_frozen_pending_ordinary_and_intent_provenance_cannot_change_mid_exit(
    setup, changed
):
    machine, state = close_buy(setup)
    _, _, wire, flags = setup
    if changed == "ordinary":
        state["orders"][-1]["filled_qty"] = 2
    elif changed == "confirmation":
        state["pending_entry_confirmation"]["intent"] = "different"
    else:
        state["scale_in_requested"] = False
    owner.step(machine, flags)
    assert "changed" in state["adaptive_exit_loop_status"]
    assert len(wire.writes) == 1 and state["entry_episode_open"] is True


def test_incomplete_buy_cancel_blocks_sell_and_cannot_be_retried(setup):
    machine, new, wire, flags = setup
    whole.ack(wire, CANCEL_NO, BUY_NO, 3)
    owner.step(machine, flags)
    flags.update(buy_filled=4, buy_remaining=0, confirmed=0)
    for _ in range(3):
        machine = new()
        state = owner.step(machine, flags)
        assert state["entry_episode_open"] is True
    assert len(wire.writes) == 1


def test_terminal_partial_buy_cannot_enter_unextended_sell_census(setup):
    machine, state = sell_residual(setup)
    _, _, wire, flags = setup
    whole.root(wire, "0000005", 11, 11, 0)
    owner.step(machine, flags)
    context = machine._owner_context_from_order(state["orders"][2])
    rows = machine.owner_registry.position_intents(context=context, symbol="005930")
    with pytest.raises(ValueError, match="full_buy"):
        closed_census(rows)
    pending_id = next(
        r["intent_id"] for r in rows if r.get("broker_order_no") == BUY_NO
    )
    assert closed_census(rows, pending_buy_ids=(pending_id,))["residual_qty"] == 0


def test_pending_buy_does_not_increase_existing_execution_quantity_cap(setup):
    machine, _ = close_buy(setup)
    _, new, wire, flags = setup
    whole.ack(wire, "0000003", "0000002", 10)
    owner.step(machine, flags)
    whole.root(wire, "0000002", 10, 1, 0)
    whole.canceled(wire, "0000003", "0000002", 10, 9)
    owner.step(machine, flags)
    flags["maximum_quantity"] = 10
    state = owner.step(new(), flags)
    assert state["entry_episode_open"] is True
    assert len(wire.writes) == 2
    assert (
        state["adaptive_exit_loop_status"]
        == "positive_exact_quantity_and_durable_action_required"
    )


def test_full_fill_before_cancel_is_reconciled_without_sending_cancel(setup):
    machine, new, wire, flags = setup
    flags.update(buy_filled=4, buy_remaining=0)
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_pending_buy_reconciled"
    assert not wire.writes and state["entry_episode_open"] is True
    whole.ack(wire, "0000003", "0000002", 10)
    owner.step(new(), flags)
    assert (
        len(wire.writes) == 1 and wire.writes[0]["payload"]["orig_ord_no"] == "0000002"
    )


@pytest.mark.parametrize("ws_terminal", [False, True])
def test_registry_full_fill_before_claim_does_not_block_pending_owner_reconciliation(
    setup, ws_terminal
):
    machine, _, wire, flags = setup
    state = machine._state["symbols"]["005930"]
    order = state["orders"][-1]
    context = machine._owner_context_from_order(order)
    machine.owner_registry.record_fill(
        context=context,
        symbol="005930",
        side="BUY",
        order_quantity=4,
        order_date=DATE,
        broker_order_no=BUY_NO,
        cumulative_filled_qty=4,
    )
    if ws_terminal:
        machine.owner_registry.transition(
            order["owner_registry_intent_id"], state="ORDER_TERMINAL"
        )
    flags.update(buy_filled=4, buy_remaining=0)
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_pending_buy_reconciled"
    request = whole.journal(state)["request"]
    assert request["pending_buys"][0]["initial_filled_qty"] == 4
    assert request["pending_buys"][0]["initial_ordinary_filled_qty"] == 1
    assert not wire.writes and state["entry_episode_open"] is True


def test_pending_cancel_deadline_retains_all_owner_state_without_further_query(setup):
    machine, new, wire, flags = setup
    whole.ack(wire, CANCEL_NO, BUY_NO, 3)
    owner.step(machine, flags)
    flags["now"] += 2001
    before = len(wire.calls)
    state = owner.step(new(), flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_cancel_deadline_exceeded"
    assert len(wire.calls) == before and state["entry_episode_open"] is True
    assert state["pending_entry_confirmation"] and state["scale_in_requested"] is True


def test_pending_buys_do_not_change_target_lot_decision_definition(setup):
    machine, _, _, _ = setup
    original = deepcopy(machine._state["symbols"]["005930"][SESSION_KEY]["definition"])
    machine, state = sell_residual(setup)
    assert state[SESSION_KEY]["definition"] == original
    assert len(whole.journal(state)["request"]["pending_buys"]) == 1


def test_partial_buy_census_requires_buy_not_sell_terminal_proof(setup):
    machine, state = sell_residual(setup)
    _, _, wire, flags = setup
    whole.root(wire, "0000005", 11, 11, 0)
    owner.step(machine, flags)
    context = machine._owner_context_from_order(state["orders"][2])
    rows = machine.owner_registry.position_intents(context=context, symbol="005930")
    pending = next(r for r in rows if r.get("broker_order_no") == BUY_NO)
    pending["terminal_reconciliation"][
        "source_contract"
    ] = "machine_adaptive_exit_dated_current_v1"
    with pytest.raises(ValueError, match="pending_buy_proof"):
        closed_census(rows, pending_buy_ids=(pending["intent_id"],))
