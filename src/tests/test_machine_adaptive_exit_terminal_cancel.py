import pytest

from src.tests import test_machine_adaptive_exit_broker as broker_tests
from src.tests import test_machine_adaptive_exit_group_execution as group_tests
from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    TARGET,
    NOW,
    detail,
    current,
    response,
)
from src.trading.order.adaptive_exit.reducer import OrderKey


@pytest.fixture
def setup(tmp_path, monkeypatch):
    adapter, transport, registry = broker_tests.setup.__wrapped__(tmp_path, monkeypatch)
    cancel = adapter.cancel_owned_sell(
        TARGET, quantity=6, action_id="terminal-cancel"
    ).order
    assert cancel == OrderKey(DATE, "0000003")
    return adapter, transport, registry, cancel


def terminal_market(transport, confirmed=6):
    transport.detailed = [
        detail(cntr_qty=str(10 - confirmed), ord_remnq="0"),
        detail(
            ord_no="0000003",
            ori_ord=TARGET.order_no,
            ord_qty="6",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty=str(confirmed),
            cnfm_tm="12:59:59",
        ),
    ]
    transport.current = []


def reconcile(adapter, cancel):
    return adapter.reconcile_terminal_cancel(TARGET, cancel, max_snapshot_age_ms=500)


@pytest.mark.parametrize("confirmed_qty", range(1, 7))
def test_terminal_cancel_smaller_than_request_after_late_fill_is_exact_not_flat(
    setup, confirmed_qty
):
    adapter, transport, registry, cancel = setup
    terminal_market(transport, confirmed_qty)
    before = len(registry._read_locked())
    result = reconcile(adapter, cancel)
    assert result.source_ok and result.terminal and result.remaining_qty == 0
    target = adapter._owned(TARGET)
    child = registry.order_owner(order_date=DATE, broker_order_no=cancel.order_no)
    assert target["state"] == child["state"] == "ORDER_TERMINAL"
    assert target["filled_qty"] == 10 - confirmed_qty
    assert target["canceled_qty"] == confirmed_qty
    proof = target["terminal_cancel_reconciliation"]
    assert child["terminal_cancel_reconciliation"] == proof
    assert proof["requested_qty"] == 6 and proof["confirmed_qty"] == confirmed_qty
    assert len(registry._read_locked()) == before + 1
    assert (
        registry.owner_position_qty(adapter.context.position_id, symbol=adapter.symbol)
        == confirmed_qty
    )
    assert len(transport.writes) == 1
    assert reconcile(adapter, cancel).source_ok
    assert len(registry._read_locked()) == before + 1


@pytest.mark.parametrize(
    "bad",
    [
        "ack_only",
        "zero",
        "over_request",
        "missing_time",
        "future_time",
        "root_nonterminal",
        "root_mismatch",
        "child_open",
        "child_filled",
        "duplicate_conflict",
        "route",
        "continuation",
        "rate_limit",
    ],
)
def test_ambiguous_or_incomplete_terminal_cancel_never_releases_journal(setup, bad):
    adapter, transport, registry, cancel = setup
    terminal_market(transport)
    if bad == "ack_only":
        transport.detailed.pop()
    elif bad == "zero":
        terminal_market(transport, 0)
    elif bad == "over_request":
        terminal_market(transport, 7)
    elif bad == "missing_time":
        transport.detailed[1].pop("cnfm_tm")
    elif bad == "future_time":
        transport.detailed[1]["cnfm_tm"] = "13:00:01"
    elif bad == "root_nonterminal":
        transport.detailed[0].update(cntr_qty="0", ord_remnq="4")
        transport.current = [current(cntr_qty="0", oso_qty="4")]
    elif bad == "root_mismatch":
        transport.detailed[0]["cntr_qty"] = "3"
    elif bad == "child_open":
        transport.current = [
            current(
                ord_no=cancel.order_no,
                orig_ord_no=TARGET.order_no,
                ord_qty="6",
                oso_qty="0",
            )
        ]
    elif bad == "child_filled":
        transport.detailed[1]["cntr_qty"] = "1"
    elif bad == "duplicate_conflict":
        transport.detailed.append(detail(cntr_qty="3", ord_remnq="0"))
    elif bad == "route":
        transport.detailed[0]["dmst_stex_tp"] = "UNKNOWN"
    elif bad == "continuation":
        transport.overrides["ka10075"] = response(
            {"return_code": 0, "oso": []}, {"cont-yn": "Y", "next-key": ""}
        )
    else:
        transport.overrides["kt00007"] = response({"return_code": 1700})
    before = registry.path.read_bytes()
    assert not reconcile(adapter, cancel).source_ok
    assert registry.path.read_bytes() == before and len(transport.writes) == 1


def test_already_reconciled_root_terminal_still_requires_child_proof(setup):
    adapter, transport, registry, cancel = setup
    terminal_market(transport)
    assert adapter.reconcile_owned_sell(TARGET).source_ok
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=cancel.order_no)["state"]
        == "ORDER_BOUND"
    )
    assert reconcile(adapter, cancel).source_ok
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=cancel.order_no)["state"]
        == "ORDER_TERMINAL"
    )


@pytest.mark.parametrize("phase", ["before", "after"])
def test_atomic_append_failure_and_restart_no_cancel_resend(setup, monkeypatch, phase):
    adapter, transport, registry, cancel = setup
    terminal_market(transport)
    original = registry._append_locked

    def fail(events, event):
        if event["event"] == "SELL_TERMINAL_CANCEL_RECONCILED":
            if phase == "after":
                original(events, event)
            raise OSError("test fsync failure")
        return original(events, event)

    monkeypatch.setattr(registry, "_append_locked", fail)
    assert not reconcile(adapter, cancel).source_ok
    rows = [
        registry.order_owner(order_date=DATE, broker_order_no=n)
        for n in (TARGET.order_no, cancel.order_no)
    ]
    assert [r["state"] for r in rows] == [
        "ORDER_TERMINAL" if phase == "after" else "ORDER_BOUND"
    ] * 2
    monkeypatch.setattr(registry, "_append_locked", original)
    assert reconcile(adapter, cancel).source_ok
    assert len(transport.writes) == 1


def test_generation_change_between_read_and_append_is_rejected(setup, monkeypatch):
    adapter, transport, registry, cancel = setup
    terminal_market(transport)
    original = registry.record_terminal_cancel_reconciliation

    def changed(**kwargs):
        kwargs["target_event_hash"] = "f" * 64
        return original(**kwargs)

    monkeypatch.setattr(registry, "record_terminal_cancel_reconciliation", changed)
    assert not reconcile(adapter, cancel).source_ok
    assert adapter._owned(TARGET)["state"] == "ORDER_BOUND"


def test_terminal_cancel_freshness_and_cross_date_are_not_waived(setup):
    adapter, transport, _, cancel = setup
    terminal_market(transport)
    times = iter([NOW, NOW, NOW + 501, NOW + 501])
    adapter.now_ms = lambda: next(times)
    assert not reconcile(adapter, cancel).source_ok
    adapter.now_ms = lambda: NOW + 86400000
    assert not reconcile(adapter, cancel).source_ok


def test_group_ttl_uses_new_proof_and_retains_residual_manager(tmp_path, monkeypatch):
    core = group_tests.group_setup.__wrapped__(tmp_path, monkeypatch)
    make, adapter, transport, _, flags = group_tests.setup.__wrapped__(core)
    e = make()
    group_tests.sell(e, transport)
    flags["now"] += 1000
    group_tests.runner_market(transport, 2)
    transport.write_body = {
        "return_code": 0,
        "ord_no": "0000006",
        "base_orig_ord_no": "0000005",
        "cncl_qty": "4",
    }
    assert e.poll_runner()["status"] == "runner_cancel_pending"
    group_tests.runner_market(transport, 4, 0, ttl_child=True)
    transport.detailed[-1]["cnfm_qty"] = "2"
    result = make().poll_runner()
    assert result["status"] == "runner_residual_requires_recovery"
    assert result["runner_remaining_qty"] == 2 and result["group_terminal"] is False
    child = adapter.registry.order_owner(order_date=DATE, broker_order_no="0000006")
    assert child["state"] == "ORDER_TERMINAL"
    assert child["terminal_cancel_reconciliation"]["confirmed_qty"] == 2
    assert len(transport.writes) == 3
