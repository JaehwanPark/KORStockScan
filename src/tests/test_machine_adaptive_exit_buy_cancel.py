from dataclasses import replace

import pytest

from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    Transport,
    current,
    detail,
    response,
)
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.buy_cancel import (
    BuyCancelWrite,
    RegisteredBuyCancelAdapter,
)
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
)

BUY = OrderKey(DATE, "0000001")
CHILD = OrderKey(DATE, "0000003")


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "buy-cancel-test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = OwnerOrderContext(
        "widget_auto_trade", "widget:test", "position:test", "buy"
    )
    intent = registry.reserve(
        context=context,
        symbol="005930",
        side="BUY",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no=BUY.order_no)
    flags = {"now": NOW, "guard": True, "authority": True}
    wire = Transport()
    market(wire, filled=2, remaining=8)
    wire.write_body.update(base_orig_ord_no=BUY.order_no, cncl_qty="8")

    def authorize():
        if not flags["authority"]:
            raise PermissionError("test missing original owner lock")

    def guard(request):
        assert type(request) is BuyCancelWrite
        return flags["guard"]

    def make():
        return RegisteredBuyCancelAdapter(
            post=wire,
            registry=registry,
            context=context,
            symbol="005930",
            routes=("SOR",),
            policy_hash="a" * 64,
            maximum_quantity=10,
            max_snapshot_age_ms=500,
            require_write_authority=authorize,
            write_guard=guard,
            now_ms=lambda: flags["now"],
        )

    return make, wire, registry, context, flags


def market(wire, *, filled, remaining, confirmed=None):
    wire.detailed = [
        detail(ord_no=BUY.order_no, cntr_qty=str(filled), ord_remnq=str(remaining))
    ]
    wire.current = (
        [current(ord_no=BUY.order_no, cntr_qty=str(filled), oso_qty=str(remaining))]
        if remaining
        else []
    )
    if confirmed is not None:
        wire.detailed.append(
            detail(
                ord_no=CHILD.order_no,
                ori_ord=BUY.order_no,
                ord_qty="8",
                cntr_qty="0",
                ord_remnq="0",
                cnfm_qty=str(confirmed),
                cnfm_tm="12:59:59",
            )
        )


def cancel(adapter):
    return adapter.cancel_owned_buy(
        BUY, quantity=8, action_id="frozen-whole-exit-action"
    )


@pytest.mark.parametrize("filled", [2, 4, 9])
def test_priced_cancel_preserves_late_fill_price_and_smaller_confirmation(
    setup, filled
):
    make, wire, registry, context, _ = setup
    cancel(make())
    market(wire, filled=filled, remaining=0, confirmed=10 - filled)
    wire.detailed[0]["cntr_uv"] = "10005"
    result = make().reconcile_priced_terminal_cancel(BUY, CHILD, guard=lambda: True)
    assert result.source_ok and result.terminal and result.fill_price == 10005
    assert result.filled_qty == filled and result.remaining_qty == 0
    root = registry.assert_owner(
        context=context, order_date=DATE, broker_order_no=BUY.order_no
    )
    assert root["canceled_qty"] == 10 - filled and root["filled_qty"] == filled
    assert len(wire.writes) == 1 and wire.writes[0]["api_id"] == "kt10003"


@pytest.mark.parametrize("price", [None, "", "0", "-10000", True, "10000.5"])
def test_priced_cancel_missing_price_does_not_publish_terminal(setup, price):
    make, wire, registry, _, _ = setup
    cancel(make())
    market(wire, filled=4, remaining=0, confirmed=6)
    wire.detailed[0]["cntr_uv"] = price
    before = registry.path.read_bytes()
    result = make().reconcile_priced_terminal_cancel(BUY, CHILD, guard=lambda: True)
    assert not result.source_ok and result.fill_price is None
    assert registry.path.read_bytes() == before and len(wire.writes) == 1


@pytest.mark.parametrize("when", ["before", "after_read", "after_registry"])
def test_priced_cancel_guard_loss_never_yields_projection_input(
    setup, when, monkeypatch
):
    make, wire, registry, _, flags = setup
    cancel(make())
    market(wire, filled=4, remaining=0, confirmed=6)
    wire.detailed[0]["cntr_uv"] = "10005"
    adapter = make()
    if when == "before":
        flags["guard"] = False
    elif when == "after_read":
        post = adapter._transport.post

        def call(**request):
            result = post(**request)
            if request["api_id"] == "ka10075":
                flags["guard"] = False
            return result

        adapter._transport.post = call
    else:
        reconcile = registry.record_buy_terminal_cancel_reconciliation

        def record(**kwargs):
            reconcile(**kwargs)
            flags["guard"] = False

        monkeypatch.setattr(
            registry, "record_buy_terminal_cancel_reconciliation", record
        )
    result = adapter.reconcile_priced_terminal_cancel(
        BUY, CHILD, guard=lambda: flags["guard"]
    )
    assert not result.source_ok and result.fill_price is None and len(wire.writes) == 1


def test_priced_full_buy_has_exact_source_and_never_writes_order(setup):
    make, wire, registry, context, _ = setup
    market(wire, filled=10, remaining=0)
    wire.detailed[0]["cntr_uv"] = "+0000010000"
    result = make().reconcile_priced_full_buy(BUY, guard=lambda: True)
    assert result.source_ok and result.terminal and result.fill_price == 10000
    assert result.filled_qty == 10 and result.remaining_qty == 0
    row = registry.assert_owner(
        context=context, order_date=DATE, broker_order_no=BUY.order_no
    )
    assert row["state"] == "ORDER_TERMINAL"
    assert row["terminal_reconciliation"]["receipt_sha256"] == result.receipt_hash
    assert not wire.writes


@pytest.mark.parametrize("price", [None, "", "0", "-10000", True, "10000.5"])
def test_priced_full_buy_missing_price_cannot_publish_zero_or_entry_price(setup, price):
    make, wire, registry, _, _ = setup
    market(wire, filled=10, remaining=0)
    wire.detailed[0]["cntr_uv"] = price
    before = registry.path.read_bytes()
    result = make().reconcile_priced_full_buy(BUY, guard=lambda: True)
    assert not result.source_ok and result.fill_price is None
    assert registry.path.read_bytes() == before and not wire.writes


@pytest.mark.parametrize(
    "mode", ["partial", "cancelled", "conflicting_price", "descendant"]
)
def test_priced_full_buy_rejects_nonfull_or_ambiguous_price(setup, mode):
    make, wire, registry, _, _ = setup
    market(wire, filled=10, remaining=0)
    wire.detailed[0]["cntr_uv"] = "10000"
    if mode == "partial":
        wire.detailed[0].update(cntr_qty="4", ord_remnq="6")
        wire.current = [current(ord_no=BUY.order_no, cntr_qty="4", oso_qty="6")]
    elif mode == "cancelled":
        wire.detailed[0]["cntr_qty"] = "4"
    elif mode == "conflicting_price":
        wire.detailed.append({**wire.detailed[0], "cntr_uv": "10005"})
    else:
        wire.detailed.append(detail(ord_no=CHILD.order_no, ori_ord=BUY.order_no))
    before = registry.path.read_bytes()
    result = make().reconcile_priced_full_buy(BUY, guard=lambda: True)
    assert not result.source_ok and result.fill_price is None
    assert registry.path.read_bytes() == before and not wire.writes


@pytest.mark.parametrize("stage", ["before", "after_read", "after_registry"])
def test_priced_full_buy_requires_lock_and_authority_across_read(setup, stage):
    make, wire, registry, _, _ = setup
    market(wire, filled=10, remaining=0)
    wire.detailed[0]["cntr_uv"] = "10000"
    calls = []

    def guard():
        calls.append(1)
        return len(calls) < {"before": 1, "after_read": 2, "after_registry": 3}[stage]

    before = registry.path.read_bytes()
    result = make().reconcile_priced_full_buy(BUY, guard=guard)
    assert not result.source_ok and result.fill_price is None and not wire.writes
    if stage != "after_registry":
        assert registry.path.read_bytes() == before


@pytest.mark.parametrize("confirmed", range(1, 9))
def test_cancel_late_fills_atomically_close_buy_and_child_without_sell(
    setup, confirmed
):
    make, wire, registry, context, _ = setup
    adapter = make()
    ack = cancel(adapter)
    assert ack.accepted and ack.order == CHILD and not hasattr(ack, "terminal")
    assert wire.writes[0] == {
        "endpoint": "/api/dostk/ordr",
        "api_id": "kt10003",
        "payload": {
            "dmst_stex_tp": "SOR",
            "orig_ord_no": BUY.order_no,
            "stk_cd": "005930",
            "cncl_qty": "8",
        },
    }
    before = len(registry._read_locked())
    market(wire, filled=10 - confirmed, remaining=0, confirmed=confirmed)
    result = make().reconcile_terminal_cancel(BUY, CHILD)
    assert result.source_ok and result.terminal
    root = registry.order_owner(order_date=DATE, broker_order_no=BUY.order_no)
    child = registry.order_owner(order_date=DATE, broker_order_no=CHILD.order_no)
    assert root["state"] == child["state"] == "ORDER_TERMINAL"
    assert root["side"] == child["side"] == "BUY"
    assert root["filled_qty"] == 10 - confirmed and root["canceled_qty"] == confirmed
    assert (
        registry.owner_position_qty(context.position_id, symbol="005930")
        == 10 - confirmed
    )
    assert (
        root["terminal_cancel_reconciliation"]
        == child["terminal_cancel_reconciliation"]
    )
    assert (
        root["terminal_reconciliation"]["source_contract"]
        == "machine_adaptive_exit_buy_dated_current_v1"
    )
    assert len(registry._read_locked()) == before + 1
    assert make().reconcile_terminal_cancel(BUY, CHILD).source_ok
    assert len(registry._read_locked()) == before + 1 and len(wire.writes) == 1
    assert all(
        c["payload"]["sell_tp"] == "2" for c in wire.calls if c["api_id"] == "kt00007"
    )
    assert all(
        c["payload"]["trde_tp"] == "2" for c in wire.calls if c["api_id"] == "ka10075"
    )


@pytest.mark.parametrize(
    "bad",
    [
        "ack",
        "zero",
        "over",
        "missing_time",
        "future",
        "race",
        "remaining",
        "child_open",
        "route",
        "quantity",
        "regression",
        "continuation",
        "limit",
        "unknown",
    ],
)
def test_unproved_cancel_or_source_never_changes_custody(setup, bad):
    make, wire, registry, _, _ = setup
    cancel(make())
    market(wire, filled=4, remaining=0, confirmed=6)
    if bad == "ack":
        wire.detailed.pop()
    elif bad == "zero":
        market(wire, filled=10, remaining=0, confirmed=0)
    elif bad == "over":
        market(wire, filled=1, remaining=0, confirmed=9)
    elif bad == "missing_time":
        wire.detailed[1].pop("cnfm_tm")
    elif bad == "future":
        wire.detailed[1]["cnfm_tm"] = "13:00:01"
    elif bad == "race":
        wire.current = [current(ord_no=BUY.order_no, cntr_qty="3", oso_qty="0")]
    elif bad == "remaining":
        market(wire, filled=3, remaining=1, confirmed=6)
    elif bad == "child_open":
        wire.current = [
            current(
                ord_no=CHILD.order_no,
                orig_ord_no=BUY.order_no,
                ord_qty="8",
                oso_qty="0",
            )
        ]
    elif bad == "route":
        wire.detailed[0]["dmst_stex_tp"] = "UNKNOWN"
    elif bad == "quantity":
        wire.detailed[0]["ord_qty"] = "11"
    elif bad == "regression":
        market(wire, filled=1, remaining=0, confirmed=8)
    elif bad == "continuation":
        wire.overrides["ka10075"] = response(
            {"return_code": 0, "oso": []}, {"cont-yn": "Y", "next-key": ""}
        )
    elif bad == "limit":
        wire.overrides["kt00007"] = response({"return_code": 1700})
    else:
        wire.detailed.append(
            detail(ord_no="0000009", ori_ord=BUY.order_no, ord_qty="1", ord_remnq="0")
        )
    before = registry.path.read_bytes()
    assert not make().reconcile_terminal_cancel(BUY, CHILD).source_ok
    assert before == registry.path.read_bytes() and len(wire.writes) == 1


def test_natural_full_buy_terminal_has_proof_not_an_exit_receipt(setup):
    make, wire, registry, context, _ = setup
    market(wire, filled=10, remaining=0)
    result = make().reconcile_owned_buy(BUY)
    assert result.source_ok and result.terminal and result.filled_qty == 10
    assert registry.owner_position_qty(context.position_id, symbol="005930") == 10
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=BUY.order_no)[
            "terminal_reconciliation"
        ]["side"]
        == "BUY"
    )
    assert not wire.writes


def test_absence_without_confirmed_cancel_is_not_buy_terminal(setup):
    make, wire, registry, _, _ = setup
    market(wire, filled=4, remaining=0)
    before = registry.path.read_bytes()
    assert not make().reconcile_owned_buy(BUY).source_ok
    assert registry.path.read_bytes() == before


def test_zero_fill_full_cancel_closes_buy_without_inventing_inventory(setup):
    make, wire, registry, context, _ = setup
    market(wire, filled=0, remaining=10)
    wire.write_body["cncl_qty"] = "10"
    ack = make().cancel_owned_buy(BUY, quantity=10, action_id="zero-fill-close")
    assert ack.accepted
    market(wire, filled=0, remaining=0, confirmed=10)
    wire.detailed[1]["ord_qty"] = "10"
    result = make().reconcile_terminal_cancel(BUY, CHILD)
    assert result.source_ok and result.terminal and result.filled_qty == 0
    assert registry.owner_position_qty(context.position_id, symbol="005930") == 0
    root = registry.order_owner(order_date=DATE, broker_order_no=BUY.order_no)
    assert root["canceled_qty"] == 10 and root["filled_qty"] == 0
    assert root["terminal_reconciliation"]["side"] == "BUY"
    assert len(wire.writes) == 1


@pytest.mark.parametrize("outcome", ["accepted", "timeout", "reject", "bad_ack"])
def test_restart_or_changed_action_cannot_retry_any_spent_cancel(setup, outcome):
    make, wire, _, _, _ = setup
    wire.crash = outcome == "timeout"
    if outcome == "reject":
        wire.write_body = {"return_code": 10}
    elif outcome == "bad_ack":
        wire.write_body["base_orig_ord_no"] = "0000009"
    cancel(make())
    with pytest.raises(ValueError, match="already_spent"):
        make().cancel_owned_buy(BUY, quantity=8, action_id="another-action")
    assert len(wire.writes) == 1


@pytest.mark.parametrize("phase", ["before", "after"])
def test_atomic_cancel_fsync_failure_restart_has_no_half_projection(
    setup, monkeypatch, phase
):
    make, wire, registry, _, _ = setup
    cancel(make())
    market(wire, filled=4, remaining=0, confirmed=6)
    original = registry._append_locked

    def fail(events, event):
        if event["event"] == "BUY_TERMINAL_CANCEL_RECONCILED":
            if phase == "after":
                original(events, event)
            raise OSError("test fsync")
        return original(events, event)

    monkeypatch.setattr(registry, "_append_locked", fail)
    assert not make().reconcile_terminal_cancel(BUY, CHILD).source_ok
    rows = [
        registry.order_owner(order_date=DATE, broker_order_no=n)
        for n in (BUY.order_no, CHILD.order_no)
    ]
    assert {r["state"] for r in rows} == {
        "ORDER_TERMINAL" if phase == "after" else "ORDER_BOUND"
    }
    monkeypatch.setattr(registry, "_append_locked", original)
    assert make().reconcile_terminal_cancel(BUY, CHILD).source_ok
    assert len(wire.writes) == 1


@pytest.mark.parametrize(
    "stage", ["guard", "authority", "after_reserve", "fill_race", "stale", "date"]
)
def test_all_original_guards_and_freshness_survive_reservation(
    setup, monkeypatch, stage
):
    make, wire, registry, _, flags = setup
    if stage in {"guard", "authority"}:
        flags[stage] = False
    if stage == "date":
        flags["now"] += 86400000
    original = registry.reserve

    def reserve(**kwargs):
        result = original(**kwargs)
        if stage == "after_reserve":
            flags["guard"] = False
        elif stage == "stale":
            flags["now"] += 501
        elif stage == "fill_race":
            registry.record_fill(
                context=kwargs["context"],
                symbol="005930",
                side="BUY",
                order_quantity=10,
                order_date=DATE,
                broker_order_no=BUY.order_no,
                cumulative_filled_qty=3,
            )
        return result

    monkeypatch.setattr(registry, "reserve", reserve)
    with pytest.raises((ValueError, PermissionError)):
        cancel(make())
    assert not wire.writes


def test_buy_cancel_api_cannot_submit_sell_or_buy_new(setup):
    make, _, _, _, _ = setup
    adapter = make()
    assert not hasattr(adapter, "submit_owned_sell")
    assert not hasattr(adapter, "submit_owned_buy")
    assert not hasattr(adapter, "cancel_owned_sell")
    with pytest.raises(ValueError, match="owned_sell_scope_mismatch"):
        adapter._transport.cancel_owned_sell(BUY, quantity=8, action_id="wrong")


@pytest.mark.parametrize("quantity", [0, True, -1, 7, 9, 11])
def test_only_explicit_full_fresh_pending_remainder_can_be_canceled(setup, quantity):
    make, wire, _, _, _ = setup
    with pytest.raises(ValueError):
        make().cancel_owned_buy(BUY, quantity=quantity, action_id="cancel")
    assert not wire.writes


def test_public_sell_adapter_still_rejects_buy_roots(setup):
    make, wire, registry, context, flags = setup
    adapter = RegisteredSellAdapter(
        post=wire,
        registry=registry,
        context=replace(context, client_intent_id="sell"),
        symbol="005930",
        routes=("SOR",),
        policy_hash="a" * 64,
        maximum_quantity=10,
        require_write_authority=lambda: None,
        write_guard=lambda _: True,
        now_ms=lambda: flags["now"],
    )
    assert not adapter.snapshot(BUY).source_ok
    assert not wire.calls
    assert make().snapshot(BUY).source_ok
