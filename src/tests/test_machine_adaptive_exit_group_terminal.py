from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests import test_machine_adaptive_exit_group_execution as execution
from src.tests import test_machine_adaptive_exit_group_runtime as groups
from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    TARGET,
    detail,
    response,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.group_terminal import (
    _terminal_order,
    validate_group_terminal,
)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    group_setup = groups.setup.__wrapped__(tmp_path, monkeypatch)
    return execution.setup.__wrapped__(group_setup)


def flat_market(transport, runner_fill=6):
    execution.runner_market(transport, filled=runner_fill, remaining=0)
    transport.detailed[0].update(cntr_qty="4", ord_remnq="0")
    transport.current = []


def closed(setup):
    make, adapter, transport, store, flags = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    return e, e.reconcile_group_terminal()["receipt"]


def test_original_target_and_runner_close_exact_quantity_without_pnl_or_new_buy(setup):
    e, receipt = closed(setup)
    make, _, transport, store, flags = setup
    assert receipt["execution_status"] == "reconciled_flat"
    assert receipt["buy_filled_qty"] == receipt["sell_filled_qty"] == 10
    assert [r["filled_qty"] for r in receipt["orders"]] == [4, 6]
    assert len(receipt["cancel_proofs"]) == 1
    assert receipt["actual_lot_fill_attribution"] is None
    assert receipt["realized_net_profit_krw"] is None
    assert receipt["economic_acceptance"] is False
    assert receipt["new_entry_authority"] is False
    assert len(transport.writes) == 2
    calls, writes = len(transport.calls), store.writes
    flags["now"] += 10000
    assert make().reconcile_group_terminal()["receipt"] == receipt
    assert len(transport.calls) == calls and store.writes == writes
    with pytest.raises(ValueError, match="blocks_new_execution"):
        e._action_allowed(e._read("SELL_RUNNER"))


def test_baseline_target_full_fill_without_cancel_can_close_frozen_group(setup):
    make, _, transport, _, _ = setup
    e = make()
    e.coordinator.freeze()
    transport.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    transport.current = []
    result = e.reconcile_group_terminal()
    assert result["group_terminal"] is True
    assert len(result["receipt"]["orders"]) == 1
    assert result["receipt"]["cancel_proofs"] == []
    assert not transport.writes


def test_runner_full_fill_does_not_close_working_original_target(setup):
    make, _, transport, store, _ = setup
    e = make()
    execution.sell(e, transport)
    execution.runner_market(transport, filled=6, remaining=0)
    assert e.reconcile_group_terminal() == {
        "status": "group_orders_working",
        "group_terminal": False,
    }
    assert e._key("GROUP_TERMINAL") not in store.records


@pytest.mark.parametrize("filled", range(6))
def test_canceled_unfilled_runner_inventory_never_becomes_flat(setup, filled):
    make, _, transport, store, _ = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport, runner_fill=filled)
    with pytest.raises(ValueError, match="residual_requires_recovery"):
        e.reconcile_group_terminal()
    assert e._key("GROUP_TERMINAL") not in store.records
    assert len(transport.writes) == 2


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_atomic_save_failure_is_not_terminal_return_and_restart_recovers(
    setup, failure
):
    make, _, transport, store, _ = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    store.fail = failure
    with pytest.raises((ValueError, OSError)):
        e.reconcile_group_terminal()
    store.fail = None
    assert make().reconcile_group_terminal()["group_terminal"] is True
    assert len(transport.writes) == 2


@pytest.mark.parametrize("flag", ["lock", "approval", "custody"])
def test_missing_owner_services_prevents_reconciliation_and_save(setup, flag):
    make, _, transport, store, flags = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    flags[flag] = False
    calls, writes = len(transport.calls), store.writes
    with pytest.raises(PermissionError):
        e.reconcile_group_terminal()
    assert len(transport.calls) == calls and store.writes == writes


def test_lock_loss_during_reconciliation_cannot_publish_terminal(setup):
    make, _, transport, store, flags = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    original = e.coordinator.adapter.reconcile_owned_sell

    def lose_lock(order):
        value = original(order)
        flags["lock"] = False
        return value

    e.coordinator.adapter.reconcile_owned_sell = lose_lock
    with pytest.raises(PermissionError):
        e.reconcile_group_terminal()
    assert e._key("GROUP_TERMINAL") not in store.records


@pytest.mark.parametrize(
    "field,value",
    [
        ("sell_filled_qty", 11),
        ("economic_acceptance", True),
        ("realized_net_profit_krw", 0),
        ("new_entry_authority", True),
        ("owner_id", "another"),
        ("episode_id", "another"),
        ("observed_at_ms", NOW + 1),
        ("observed_at_ms", True),
    ],
)
def test_rehashed_terminal_forgery_fails_independent_registry_check(
    setup, field, value
):
    e, receipt = closed(setup)
    forged = deepcopy(receipt)
    forged[field] = value
    forged["canonical_sha256"] = canonical_sha256(forged)
    with pytest.raises(ValueError):
        validate_group_terminal(forged, e)


@pytest.mark.parametrize("field", ["receipt_sha256", "position_id", "source_contract"])
def test_ws_terminal_or_wrong_registry_proof_cannot_replace_dated_proof(setup, field):
    e, receipt = closed(setup)
    original = e.coordinator._target

    def corrupt():
        row = original()
        row["terminal_reconciliation"][field] = "invalid"
        return row

    e.coordinator._target = corrupt
    with pytest.raises(ValueError):
        validate_group_terminal(receipt, e)


@pytest.mark.parametrize(
    "state", ["INTENT_RESERVED", "INTENT_AMBIGUOUS", "INTENT_REJECTED"]
)
def test_unresolved_saved_action_is_not_silently_ignored(setup, state):
    make, _, transport, store, _ = setup
    e = make()
    e.coordinator.freeze()
    record = e._record(execution.action("RELEASE_RUNNER"), TARGET, 6)
    if state != "INTENT_RESERVED":
        # Test the action consumer independently; no false no-order proof.
        e._intent = lambda _: {"state": state}
    with pytest.raises(ValueError, match="unresolved_action"):
        e.reconcile_group_terminal()
    assert record is not None and not transport.writes
    assert e._key("GROUP_TERMINAL") not in store.records


@pytest.mark.parametrize(
    "route,date,state",
    [
        ("SOR", DATE, "INTENT_RESERVED"),
        ("KRX", DATE, "INTENT_RESERVED"),
        ("SOR", "2026-09-08", "INTENT_RESERVED"),
        ("SOR", DATE, "INTENT_REJECTED"),
    ],
)
def test_position_census_keeps_other_route_date_and_unbound_intents(
    setup, route, date, state
):
    e, receipt = closed(setup)
    _, adapter, _, _, _ = setup
    context = replace(adapter.context, client_intent_id="unregistered-successor")
    intent = adapter.registry.reserve(
        context=context,
        symbol="005930",
        side="BUY",
        quantity=1,
        route=route,
        order_date=date,
    )
    if state != "INTENT_RESERVED":
        adapter.registry.transition(intent, state=state)
    with pytest.raises(ValueError, match="census_conflict"):
        validate_group_terminal(receipt, e)


def test_other_position_is_not_mixed_into_group_closure(setup):
    e, receipt = closed(setup)
    _, adapter, _, _, _ = setup
    adapter.registry.reserve(
        context=replace(
            adapter.context, position_id="other-position", client_intent_id="other"
        ),
        symbol="005930",
        side="BUY",
        quantity=1,
        route="SOR",
        order_date=DATE,
    )
    validate_group_terminal(receipt, e)


def test_source_failure_cannot_reuse_registry_terminal_without_group_receipt(setup):
    make, _, transport, store, _ = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    transport.overrides["ka10075"] = response({"return_code": 1})
    assert e.reconcile_group_terminal()["group_terminal"] is False
    assert e._key("GROUP_TERMINAL") not in store.records


def test_terminal_reads_have_a_shared_freshness_bound(setup):
    make, _, transport, store, flags = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    original = e.coordinator.adapter.reconcile_owned_sell

    def slow(order):
        result = original(order)
        flags["now"] += 600
        return result

    e.coordinator.adapter.reconcile_owned_sell = slow
    assert e.reconcile_group_terminal() == {
        "status": "group_terminal_source_gap",
        "group_terminal": False,
    }
    assert e._key("GROUP_TERMINAL") not in store.records


def test_cross_date_remains_explicit_recovery_not_rebased_orders(setup):
    e, _ = closed(setup)
    setup[-1]["now"] += 86400000
    with pytest.raises(ValueError, match="cross_date"):
        e.reconcile_group_terminal()


def test_ttl_cancel_ack_is_separate_from_runner_full_fill_terminal(setup):
    make, _, transport, store, flags = setup
    e = make()
    execution.sell(e, transport)
    execution.runner_market(transport, filled=2)
    flags["now"] += 1000
    transport.write_body = {
        "return_code": 0,
        "ord_no": "0000006",
        "base_orig_ord_no": "0000005",
        "cncl_qty": "4",
    }
    assert e.poll_runner()["status"] == "runner_cancel_pending"
    flat_market(transport)
    with pytest.raises(ValueError, match="ttl_cancel_recovery_required"):
        e.reconcile_group_terminal()
    assert e._key("GROUP_TERMINAL") not in store.records
    assert len(transport.writes) == 3


def test_stored_terminal_cannot_hide_missing_cancel_proof(setup):
    e, receipt = closed(setup)
    original = e._intent

    def corrupt(record):
        row = original(record)
        if record["action"]["kind"] == "RELEASE_RUNNER":
            row.pop("cancel_reconciliation", None)
        return row

    e._intent = corrupt
    with pytest.raises(ValueError):
        validate_group_terminal(receipt, e)


def test_unrecorded_pending_action_in_registry_is_not_adopted(setup):
    make, _, transport, store, _ = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    del store.records[e._key("SELL_RUNNER")]
    with pytest.raises(ValueError, match="census_conflict"):
        e.reconcile_group_terminal()


def test_save_committed_then_lock_lost_does_not_return_success(setup):
    make, _, transport, store, flags = setup
    e = make()
    execution.sell(e, transport)
    flat_market(transport)
    original = e.coordinator.save_record

    def lose_lock(key, expected, payload):
        original(key, expected, payload)
        flags["lock"] = False

    e.coordinator.save_record = lose_lock
    with pytest.raises(PermissionError):
        e.reconcile_group_terminal()
    flags["lock"] = True
    assert make().reconcile_group_terminal()["group_terminal"] is True


def test_position_census_is_read_only_and_returns_detached_values(setup):
    _, adapter, _, _, _ = setup
    before = adapter.registry.path.read_bytes()
    rows = adapter.registry.position_intents(context=adapter.context, symbol="005930")
    rows[0]["quantity"] = -100
    fresh = adapter.registry.position_intents(context=adapter.context, symbol="005930")
    assert all(r["quantity"] > 0 for r in fresh)
    assert adapter.registry.path.read_bytes() == before


@pytest.mark.parametrize("field", ["quantity", "filled_qty"])
def test_bool_in_a_one_share_terminal_proof_is_not_an_integer(field):
    row = {
        "state": "ORDER_TERMINAL",
        "side": "SELL",
        "action": "NEW",
        "quantity": 1,
        "filled_qty": 1,
    }
    row["terminal_reconciliation"] = {
        "schema": "order_owner_terminal_reconciliation_v1",
        "source_contract": "machine_adaptive_exit_dated_current_v1",
        "side": "SELL",
        "action": "NEW",
        "quantity": 1,
        "filled_qty": 1,
        "receipt_sha256": "a" * 64,
    }
    row["terminal_reconciliation"][field] = True
    with pytest.raises(ValueError, match="exact_sell_proof_required"):
        _terminal_order(row, "original_target")
