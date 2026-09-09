from dataclasses import replace
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
    OwnerRegistryError,
)
from src.trading.low_price_two_leg.profiles import profiles_for_target_date

DATE = "2026-09-09"
NOW = int(datetime.fromisoformat(DATE + "T13:00:00+09:00").timestamp() * 1000)
TARGET = OrderKey(DATE, "0000002")


def detail(**changes):
    return {
        "ord_no": TARGET.order_no,
        "ori_ord": "0000000",
        "stk_cd": "A005930",
        "ord_qty": "+0000000010",
        "cntr_qty": "0",
        "ord_remnq": "10",
        "dmst_stex_tp": "SOR",
        **changes,
    }


def current(**changes):
    return {
        "ord_no": TARGET.order_no,
        "orig_ord_no": "0000000",
        "stk_cd": "005930",
        "ord_qty": "10",
        "cntr_qty": "0",
        "oso_qty": "10",
        "stex_tp": "0",
        "sor_yn": "Y",
        **changes,
    }


def response(body, headers=None, status=200):
    return (
        SimpleNamespace(status_code=status, headers=headers or {"cont-yn": "N"}),
        body,
    )


class Transport:
    def __init__(self):
        self.detailed = [detail()]
        self.current = [current()]
        self.calls = []
        self.overrides = {}
        self.write_body = {
            "return_code": 0,
            "ord_no": "0000003",
            "base_orig_ord_no": TARGET.order_no,
            "cncl_qty": "6",
            "dmst_stex_tp": "SOR",
        }
        self.crash = False

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        api = kwargs["api_id"]
        if api in self.overrides:
            values = self.overrides[api]
            return values.pop(0) if isinstance(values, list) else values
        if api == "kt00007":
            return response({"return_code": 0, "acnt_ord_cntr_prps_dtl": self.detailed})
        if api == "ka10075":
            return response({"return_code": 0, "oso": self.current})
        if self.crash:
            raise TimeoutError("do not log raw credentials")
        return response(self.write_body)

    @property
    def writes(self):
        return [r for r in self.calls if r["api_id"] in {"kt10001", "kt10003"}]


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "adaptive-test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = OwnerOrderContext("episode", "episode:test", "position:test", "buy")
    buy = registry.reserve(
        context=context,
        symbol="005930",
        side="BUY",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(buy, state="ORDER_BOUND", broker_order_no="0000001")
    registry.record_fill(
        context=context,
        symbol="005930",
        side="BUY",
        order_quantity=10,
        order_date=DATE,
        broker_order_no="0000001",
        cumulative_filled_qty=10,
    )
    registry.transition(buy, state="ORDER_TERMINAL")
    target = registry.reserve(
        context=replace(context, client_intent_id="target"),
        symbol="005930",
        side="SELL",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(target, state="ORDER_BOUND", broker_order_no=TARGET.order_no)
    transport = Transport()
    adapter = RegisteredSellAdapter(
        post=transport,
        registry=registry,
        context=context,
        symbol="005930",
        routes=("SOR",),
        policy_hash="a" * 64,
        maximum_quantity=10,
        require_write_authority=lambda: None,
        now_ms=lambda: NOW,
        write_guard=lambda request: True,
    )
    return adapter, transport, registry


def test_disabled_without_guard_makes_no_call(setup):
    adapter, tr, _ = setup
    adapter.write_guard = None
    with pytest.raises(PermissionError):
        adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert tr.calls == []


def confirmed_partial(setup, *, quantity=6, filled=1):
    adapter, tr, registry = setup
    tr.write_body["cncl_qty"] = str(quantity)
    ack = adapter.cancel_owned_sell(TARGET, quantity=quantity, action_id="partial")
    assert ack.accepted
    remaining = 10 - quantity - filled
    tr.detailed = [
        detail(cntr_qty=str(filled), ord_remnq=str(remaining)),
        detail(
            ord_no=ack.order.order_no,
            ori_ord=TARGET.order_no,
            ord_qty=str(quantity),
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty=str(quantity),
            cnfm_tm="12:59:59",
        ),
    ]
    tr.current = [current(cntr_qty=str(filled), oso_qty=str(remaining))]
    return ack.order


def reserve_runner(setup, quantity, client="runner"):
    adapter, _, registry = setup
    return registry.reserve(
        context=replace(adapter.context, client_intent_id=client),
        symbol="005930",
        side="SELL",
        quantity=quantity,
        route="SOR",
        order_date=DATE,
    )


@pytest.mark.parametrize(
    "quantity,filled", [(q, f) for q in range(1, 10) for f in range(10 - q)]
)
def test_partial_confirmation_releases_only_exact_shares_and_keeps_target_open(
    setup, quantity, filled
):
    adapter, tr, registry = setup
    cancel = confirmed_partial(setup, quantity=quantity, filled=filled)
    before = len(tr.calls)
    result = adapter.reconcile_partial_cancel(TARGET, cancel, max_snapshot_age_ms=2000)
    assert result.source_ok and not result.terminal
    assert len(tr.calls) - before == 2  # Same bounded read pair, no write/retry.
    target = adapter._owned(TARGET)
    assert target["state"] == "ORDER_BOUND"
    assert target["canceled_qty"] == quantity
    assert target["filled_qty"] == filled
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=cancel.order_no)["state"]
        == "ORDER_TERMINAL"
    )
    with pytest.raises(OwnerRegistryError):
        reserve_runner(setup, quantity + 1)
    runner = reserve_runner(setup, quantity)
    registry.transition(runner, state="ORDER_BOUND", broker_order_no="0000004")
    with pytest.raises(OwnerRegistryError):
        reserve_runner(setup, 1, client="duplicate-runner")


def test_cancel_ack_and_default_snapshot_do_not_release_partial_reservation(setup):
    adapter, _, _ = setup
    cancel = confirmed_partial(setup)
    assert adapter.reconcile_owned_sell(TARGET).source_ok
    assert "canceled_qty" not in adapter._owned(TARGET)
    with pytest.raises(OwnerRegistryError):
        reserve_runner(setup, 1)
    # Existing single-lot replacement remains whole-target-terminal guarded.
    with pytest.raises(ValueError):
        adapter.submit_owned_sell(
            TARGET, quantity=6, limit_price=70000, action_id="runner"
        )
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok


@pytest.mark.parametrize(
    "changes",
    [
        {"cnfm_qty": None},
        {"cnfm_qty": "0"},
        {"cnfm_qty": "3"},
        {"cnfm_qty": True},
        {"cnfm_qty": "-6"},
        {"cnfm_qty": "7"},
        {"cnfm_tm": None},
        {"cnfm_tm": "25:00:00"},
        {"cnfm_tm": "13:00:01"},
        {"cntr_qty": "1"},
        {"ord_remnq": "1"},
        {"ord_qty": "7"},
        {"ori_ord": "0000004"},
        {"dmst_stex_tp": "unknown"},
    ],
)
def test_unproved_cancel_does_not_modify_registry(setup, changes):
    adapter, tr, registry = setup
    cancel = confirmed_partial(setup)
    tr.detailed[1].update(changes)
    before = registry.path.read_bytes()
    result = adapter.reconcile_partial_cancel(TARGET, cancel, max_snapshot_age_ms=2000)
    assert not result.source_ok
    assert registry.path.read_bytes() == before


@pytest.mark.parametrize(
    "mode",
    [
        "absent_history",
        "still_current",
        "root_race",
        "unexplained_delta",
        "missing_current",
        "duplicate_conflict",
    ],
)
def test_partial_cancel_requires_complete_paired_root_and_cancel_evidence(setup, mode):
    adapter, tr, registry = setup
    cancel = confirmed_partial(setup)
    if mode == "absent_history":
        tr.detailed.pop()
    elif mode == "still_current":
        tr.current.append(
            current(
                ord_no=cancel.order_no,
                orig_ord_no=TARGET.order_no,
                ord_qty="6",
                cntr_qty="0",
                oso_qty="0",
            )
        )
    elif mode == "root_race":
        tr.current[0]["oso_qty"] = "4"
    elif mode == "unexplained_delta":
        tr.current[0]["oso_qty"] = tr.detailed[0]["ord_remnq"] = "2"
    elif mode == "missing_current":
        tr.current.clear()
    else:
        tr.detailed.append(tr.detailed[1] | {"cnfm_qty": "3"})
    before = registry.path.read_bytes()
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert registry.path.read_bytes() == before


def test_partial_proof_is_restart_idempotent_and_late_fill_preserves_cancel(setup):
    adapter, tr, registry = setup
    cancel = confirmed_partial(setup)
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    first = registry.path.read_bytes()
    adapter.registry = OrderOwnerRegistry(registry.path)
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert registry.path.read_bytes() == first
    tr.detailed[0].update(cntr_qty="2", ord_remnq="2")
    tr.current[0].update(cntr_qty="2", oso_qty="2")
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert adapter._owned(TARGET)["canceled_qty"] == 6
    assert adapter._owned(TARGET)["filled_qty"] == 2
    with pytest.raises(OwnerRegistryError):
        registry.record_fill(
            context=adapter.context,
            symbol="005930",
            side="SELL",
            order_quantity=10,
            order_date=DATE,
            broker_order_no=TARGET.order_no,
            cumulative_filled_qty=5,
        )
    # Old current rows cannot revive the six released shares.
    tr.detailed[0].update(cntr_qty="2", ord_remnq="8")
    tr.current[0].update(cntr_qty="2", oso_qty="8")
    assert not adapter.snapshot(TARGET).source_ok


def test_partial_reconciliation_journal_race_is_fail_closed(setup, monkeypatch):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    method = registry.record_partial_cancel_reconciliation

    def racing(**kwargs):
        registry.record_fill(
            context=adapter.context,
            symbol="005930",
            side="SELL",
            order_quantity=10,
            order_date=DATE,
            broker_order_no=TARGET.order_no,
            cumulative_filled_qty=2,
        )
        return method(**kwargs)

    monkeypatch.setattr(registry, "record_partial_cancel_reconciliation", racing)
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert "canceled_qty" not in adapter._owned(TARGET)
    with pytest.raises(OwnerRegistryError):
        reserve_runner(setup, 1)


def test_partial_reconciliation_disk_failure_does_not_split_target_cancel_state(
    setup, monkeypatch
):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    append = registry._append_locked

    def failing(events, row):
        if row.get("event") == "SELL_PARTIAL_CANCEL_RECONCILED":
            raise OSError("disk")
        return append(events, row)

    monkeypatch.setattr(registry, "_append_locked", failing)
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert "canceled_qty" not in adapter._owned(TARGET)
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=cancel.order_no)["state"]
        == "ORDER_BOUND"
    )
    monkeypatch.setattr(registry, "_append_locked", append)
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok


def test_partial_reconciliation_stale_read_does_not_release(setup):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    clock = iter([NOW, NOW + 3000, NOW + 3000])
    adapter.now_ms = lambda: next(clock)
    before = registry.path.read_bytes()
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert registry.path.read_bytes() == before


def test_sequential_partial_cancels_have_separate_proof_and_reservations(setup):
    adapter, tr, registry = setup
    first = confirmed_partial(setup)
    assert adapter.reconcile_partial_cancel(
        TARGET, first, max_snapshot_age_ms=2000
    ).source_ok
    tr.write_body.update(ord_no="0000004", cncl_qty="1")
    second = adapter.cancel_owned_sell(TARGET, quantity=1, action_id="partial2")
    assert second.accepted
    tr.detailed[0]["ord_remnq"] = tr.current[0]["oso_qty"] = "2"
    tr.detailed.append(
        tr.detailed[1] | {"ord_no": "0000004", "ord_qty": "1", "cnfm_qty": "1"}
    )
    assert adapter.reconcile_partial_cancel(
        TARGET, second.order, max_snapshot_age_ms=2000
    ).source_ok
    assert adapter._owned(TARGET)["canceled_qty"] == 7
    assert (
        registry.owner_position_qty(adapter.context.position_id, symbol="005930") == 9
    )
    reserve_runner(setup, 7)


@pytest.mark.parametrize(
    "changes",
    [
        {"confirmed_qty": True},
        {"filled_qty": 1.0},
        {"remaining_qty": -1},
        {"confirmed_qty": 5},
        {"remaining_qty": 4},
        {"remaining_qty": 0},
        {"receipt_sha256": "ACK"},
        {"target_event_hash": "b" * 64},
        {"cancel_event_hash": "b" * 64},
        {"cancel_order_no": "0000002"},
        {"order_date": "2026-09-08"},
    ],
)
def test_registry_partial_proof_strict_contract(setup, changes):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    snapshot, proof = adapter._snapshot(TARGET, cancel_order=cancel)
    assert snapshot.source_ok
    payload = dict(
        context=adapter.context,
        order_date=DATE,
        target_order_no=TARGET.order_no,
        cancel_order_no=cancel.order_no,
        filled_qty=1,
        remaining_qty=3,
        **{k: v for k, v in proof.items() if k != "started_at_ms"},
    )
    payload.update(changes)
    before = registry.path.read_bytes()
    with pytest.raises(OwnerRegistryError):
        registry.record_partial_cancel_reconciliation(**payload)
    assert registry.path.read_bytes() == before


@pytest.mark.parametrize("mode", ["owner", "policy", "date", "account"])
def test_partial_proof_rejects_scope_change_without_reads_or_release(
    setup, monkeypatch, mode
):
    adapter, tr, registry = setup
    cancel = confirmed_partial(setup)
    if mode == "owner":
        adapter.context = replace(adapter.context, owner_id="episode:other")
    elif mode == "policy":
        adapter.policy_hash = "b" * 64
    elif mode == "date":
        cancel = OrderKey("2026-09-08", cancel.order_no)
    else:
        monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "other-account")
    before, calls = registry.path.read_bytes(), len(tr.calls)
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert registry.path.read_bytes() == before and len(tr.calls) == calls


def test_target_terminal_race_cannot_be_reopened_by_partial_proof(setup, monkeypatch):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    method = registry.record_partial_cancel_reconciliation

    def racing(**kwargs):
        registry.transition(adapter._owned(TARGET)["intent_id"], state="ORDER_TERMINAL")
        return method(**kwargs)

    monkeypatch.setattr(registry, "record_partial_cancel_reconciliation", racing)
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert adapter._owned(TARGET)["state"] == "ORDER_TERMINAL"
    assert "canceled_qty" not in adapter._owned(TARGET)


def test_repeated_partial_proof_does_not_ignore_new_unbound_cancel(setup):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    registry.reserve(
        context=replace(adapter.context, client_intent_id="unbound-cancel"),
        symbol="005930",
        side="SELL",
        quantity=1,
        route="SOR",
        order_date=DATE,
        action="CANCEL",
        original_order_no=TARGET.order_no,
        authority_policy_id="machine_adaptive_exit_v1",
        authority_policy_hash="a" * 64,
    )
    before = registry.path.read_bytes()
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert registry.path.read_bytes() == before


def test_partial_commit_then_lost_result_recovers_without_second_release(
    setup, monkeypatch
):
    adapter, _, registry = setup
    cancel = confirmed_partial(setup)
    append = registry._append_locked

    def failing_after_commit(events, row):
        result = append(events, row)
        if row.get("event") == "SELL_PARTIAL_CANCEL_RECONCILED":
            raise OSError("lost result after durable write")
        return result

    monkeypatch.setattr(registry, "_append_locked", failing_after_commit)
    assert not adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    committed = registry.path.read_bytes()
    assert adapter._owned(TARGET)["canceled_qty"] == 6
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=cancel.order_no)["state"]
        == "ORDER_TERMINAL"
    )
    monkeypatch.setattr(registry, "_append_locked", append)
    assert adapter.reconcile_partial_cancel(
        TARGET, cancel, max_snapshot_age_ms=2000
    ).source_ok
    assert registry.path.read_bytes() == committed


def test_terminal_proof_is_idempotent_and_does_not_replace_terminal_origin(setup):
    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    tr.current = []
    first = adapter.reconcile_owned_sell(TARGET)
    assert first.source_ok and first.terminal
    row = adapter._owned(TARGET)
    before = registry.path.read_bytes()
    adapter.now_ms = lambda: NOW + 100
    second = adapter.reconcile_owned_sell(TARGET)
    assert second.receipt_hash != first.receipt_hash and second.source_ok
    assert registry.path.read_bytes() == before
    assert (
        adapter._owned(TARGET)["terminal_reconciliation"]
        == row["terminal_reconciliation"]
    )
    assert not tr.writes


def test_terminal_proof_disk_failure_can_reconcile_without_new_order(
    setup, monkeypatch
):
    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    tr.current = []
    append = registry._append_locked

    def fail(events, row):
        if row.get("event") == "TERMINAL_RECONCILIATION_RECORDED":
            raise OSError("disk")
        return append(events, row)

    monkeypatch.setattr(registry, "_append_locked", fail)
    failed = adapter.reconcile_owned_sell(TARGET)
    assert not failed.source_ok
    assert adapter._owned(TARGET)["state"] == "ORDER_TERMINAL"
    assert "terminal_reconciliation" not in adapter._owned(TARGET)
    monkeypatch.setattr(registry, "_append_locked", append)
    assert adapter.reconcile_owned_sell(TARGET).source_ok
    assert adapter._owned(TARGET)["terminal_reconciliation"]
    assert not tr.writes


def test_old_adapter_terminal_proof_is_projected_at_original_fill_not_late_fill(setup):
    adapter, tr, registry = setup
    row = adapter._owned(TARGET)
    registry.record_fill(
        context=adapter.context,
        symbol="005930",
        side="SELL",
        order_quantity=10,
        order_date=DATE,
        broker_order_no=TARGET.order_no,
        cumulative_filled_qty=4,
    )
    registry.transition(
        row["intent_id"],
        state="ORDER_TERMINAL",
        broker_order_no=TARGET.order_no,
        reason="adaptive_exact_terminal:" + "c" * 64,
    )
    before = registry.path.read_bytes()
    proof = adapter._owned(TARGET)["terminal_reconciliation"]
    assert proof["filled_qty"] == 4 and proof["receipt_sha256"] == "c" * 64
    assert registry.path.read_bytes() == before
    # A contradictory late quantity cannot inherit the old terminal's proof.
    registry.record_fill(
        context=adapter.context,
        symbol="005930",
        side="SELL",
        order_quantity=10,
        order_date=DATE,
        broker_order_no=TARGET.order_no,
        cumulative_filled_qty=5,
    )
    tr.detailed = [detail(cntr_qty="5", ord_remnq="0")]
    tr.current = []
    assert not adapter.reconcile_owned_sell(TARGET).source_ok
    assert adapter._owned(TARGET)["terminal_reconciliation"]["filled_qty"] == 4
    assert not tr.writes


@pytest.mark.parametrize(
    "change",
    [
        {"cumulative_filled_qty": 9},
        {"cumulative_filled_qty": True},
        {"order_quantity": 11},
        {"symbol": "000660"},
        {"order_date": "2026-09-08"},
        {"broker_order_no": "0000001"},
        {"receipt_sha256": ""},
        {"receipt_sha256": "x" * 64},
    ],
)
def test_terminal_proof_rejects_conflicting_identity_or_quantity(setup, change):
    from src.trading.order.owner_custody_registry import OwnerRegistryError

    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    tr.current = []
    assert adapter.reconcile_owned_sell(TARGET).source_ok
    before = registry.path.read_bytes()
    values = dict(
        context=adapter.context,
        symbol="005930",
        order_quantity=10,
        order_date=DATE,
        broker_order_no=TARGET.order_no,
        cumulative_filled_qty=10,
        receipt_sha256="a" * 64,
    )
    with pytest.raises(OwnerRegistryError):
        registry.record_terminal_reconciliation(**(values | change))
    assert registry.path.read_bytes() == before


@pytest.mark.parametrize("mismatch", ["owner", "position", "account"])
def test_terminal_proof_cannot_cross_owner_or_account(setup, monkeypatch, mismatch):
    from src.trading.order.owner_custody_registry import OwnerRegistryError

    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="10", ord_remnq="0")]
    tr.current = []
    assert adapter.reconcile_owned_sell(TARGET).source_ok
    before = registry.path.read_bytes()
    context = adapter.context
    if mismatch == "owner":
        context = replace(context, owner_id="episode:other")
    elif mismatch == "position":
        context = replace(context, position_id="position:other")
    else:
        monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "different-account")
    with pytest.raises(OwnerRegistryError):
        registry.record_terminal_reconciliation(
            context=context,
            symbol="005930",
            order_quantity=10,
            order_date=DATE,
            broker_order_no=TARGET.order_no,
            cumulative_filled_qty=10,
            receipt_sha256="a" * 64,
        )
    assert registry.path.read_bytes() == before


def test_terminal_proof_rechecks_interleaved_fill_inside_registry_lock(
    setup, monkeypatch
):
    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="4", ord_remnq="0")]
    tr.current = []
    original = registry.record_terminal_reconciliation

    def interleave(**kwargs):
        registry.record_fill(
            context=adapter.context,
            symbol="005930",
            side="SELL",
            order_quantity=10,
            order_date=DATE,
            broker_order_no=TARGET.order_no,
            cumulative_filled_qty=5,
        )
        return original(**kwargs)

    monkeypatch.setattr(registry, "record_terminal_reconciliation", interleave)
    assert not adapter.reconcile_owned_sell(TARGET).source_ok
    assert "terminal_reconciliation" not in adapter._owned(TARGET)
    assert not tr.writes


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5, "1", 11])
def test_invalid_quantity_never_writes(setup, quantity):
    adapter, tr, _ = setup
    with pytest.raises(ValueError):
        adapter.cancel_owned_sell(TARGET, quantity=quantity, action_id="cancel")
    assert tr.calls == []


@pytest.mark.parametrize(
    "change",
    [
        {"cntr_qty": None},
        {"ord_remnq": "1.2"},
        {"cntr_qty": "-1"},
        {"cntr_qty": True},
        {"cntr_qty": "11"},
        {"ord_no": "2"},
        {"stk_cd": "A000660"},
        {"ord_qty": "20"},
        {"ori_ord": None},
    ],
)
def test_malformed_exact_source_not_zero_or_terminal(setup, change):
    adapter, tr, _ = setup
    tr.detailed = [detail(**change)]
    proof = adapter.snapshot(TARGET)
    assert not proof.source_ok and not proof.terminal and proof.filled_qty is None


def test_partial_fill_explicit_cancel_ack_retains_reservation(setup):
    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="4", ord_remnq="6")]
    tr.current = [current(cntr_qty="4", oso_qty="6")]
    ack = adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert ack.accepted and not ack.ambiguous
    assert tr.writes[0]["payload"]["cncl_qty"] == "6"
    original = registry.order_owner(order_date=DATE, broker_order_no=TARGET.order_no)
    assert original["state"] == "ORDER_BOUND" and original["filled_qty"] == 4
    assert (
        registry.owner_position_qty(adapter.context.position_id, symbol="005930") == 6
    )
    with pytest.raises(ValueError):
        adapter.submit_owned_sell(
            TARGET, quantity=6, limit_price=70000, action_id="sell"
        )
    with pytest.raises(OwnerRegistryError):
        adapter.cancel_owned_sell(TARGET, quantity=6, action_id="new-cancel-id")
    assert len(tr.writes) == 1


def test_exact_cancel_terminal_allows_only_residual_limit_sell(setup):
    adapter, tr, registry = setup
    tr.detailed = [detail(cntr_qty="4", ord_remnq="0")]
    tr.current = []
    ack = adapter.submit_owned_sell(
        TARGET, quantity=6, limit_price=70000, action_id="sell"
    )
    assert ack.accepted
    assert tr.writes[0]["payload"] == {
        "dmst_stex_tp": "SOR",
        "stk_cd": "005930",
        "ord_qty": "6",
        "ord_uv": "70000",
        "trde_tp": "0",
        "cond_uv": "",
    }
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=TARGET.order_no)["state"]
        == "ORDER_TERMINAL"
    )
    with pytest.raises(OwnerRegistryError):
        adapter.submit_owned_sell(
            TARGET, quantity=6, limit_price=70000, action_id="another-id"
        )
    assert len(tr.writes) == 1


@pytest.mark.parametrize("fill", [0, 4, 10])
def test_absence_cannot_replace_dated_terminal(setup, fill):
    adapter, tr, _ = setup
    tr.detailed = [detail(cntr_qty=str(fill), ord_remnq=str(10 - fill))]
    tr.current = []
    proof = adapter.snapshot(TARGET)
    assert proof.source_ok is (fill == 10)
    assert proof.terminal is (fill == 10)


def test_fill_race_between_reads_retains_reservations(setup):
    adapter, tr, registry = setup
    tr.current = [current(cntr_qty="1", oso_qty="9")]
    assert adapter.snapshot(TARGET).error == "dated_current_quantity_race"
    assert (
        registry.order_owner(order_date=DATE, broker_order_no=TARGET.order_no)[
            "filled_qty"
        ]
        == 0
    )


@pytest.mark.parametrize(
    "headers", [{"cont-yn": "Y"}, {"cont-yn": "?"}, {"next-key": "abc"}]
)
def test_invalid_continuation_not_absence_proof(setup, headers):
    adapter, tr, _ = setup
    tr.overrides["ka10075"] = response({"return_code": 0, "oso": []}, headers)
    assert not adapter.snapshot(TARGET).source_ok


@pytest.mark.parametrize("keys", [("a", "a"), ("a", "b", "c")])
def test_repeated_or_exhausted_pagination_not_complete(setup, keys):
    adapter, tr, _ = setup
    tr.overrides["ka10075"] = [
        response({"return_code": 0, "oso": []}, {"cont-yn": "Y", "next-key": k})
        for k in keys
    ]
    assert not adapter.snapshot(TARGET).source_ok
    assert len([r for r in tr.calls if r["api_id"] == "ka10075"]) == len(keys)


def test_late_page_successor_is_not_ignored(setup):
    adapter, tr, _ = setup
    tr.detailed = [detail(ord_remnq="0")]
    tr.overrides["ka10075"] = [
        response({"return_code": 0, "oso": []}, {"cont-yn": "Y", "next-key": "next"}),
        response(
            {
                "return_code": 0,
                "oso": [current(ord_no="0000009", orig_ord_no=TARGET.order_no)],
            }
        ),
    ]
    assert adapter.snapshot(TARGET).error == "unknown_or_open_successor"
    assert tr.calls[-1]["cont_yn"] == "Y" and tr.calls[-1]["next_key"] == "next"


def test_known_cancel_history_is_not_unknown_modification(setup):
    adapter, tr, _ = setup
    adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    tr.detailed = [
        detail(ord_remnq="0"),
        detail(ord_no="0000003", ori_ord=TARGET.order_no, ord_qty="6", ord_remnq="0"),
    ]
    tr.current = []
    assert adapter.snapshot(TARGET).terminal


@pytest.mark.parametrize(
    "mode",
    [
        "timeout",
        "ack_without_number",
        "wrong_original",
        "wrong_qty",
        "http500",
        "bool_code",
    ],
)
def test_ambiguous_write_is_durable_and_not_retried(setup, mode):
    adapter, tr, registry = setup
    if mode == "timeout":
        tr.crash = True
    elif mode == "ack_without_number":
        tr.write_body.pop("ord_no")
    elif mode == "wrong_original":
        tr.write_body["base_orig_ord_no"] = "0000009"
    elif mode == "wrong_qty":
        tr.write_body["cncl_qty"] = "0"
    elif mode == "bool_code":
        tr.write_body["return_code"] = False
    else:
        tr.overrides["kt10003"] = response({"return_code": 3}, status=500)
    ack = adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert ack.ambiguous and not ack.accepted
    assert (
        registry.unresolved_intent_summary(symbol="005930", active_date=DATE)[
            "unresolved_intent_count"
        ]
        == 1
    )
    with pytest.raises(OwnerRegistryError):
        adapter.cancel_owned_sell(TARGET, quantity=6, action_id="new-id")
    assert len(tr.writes) == 1


def test_explicit_reject_separate_from_transport_ambiguity(setup):
    adapter, tr, registry = setup
    tr.write_body = {"return_code": 3}
    ack = adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert not ack.accepted and not ack.ambiguous
    assert (
        registry.unresolved_intent_summary(symbol="005930", active_date=DATE)[
            "unresolved_intent_count"
        ]
        == 0
    )


def test_guard_rechecked_after_reads_before_reservation(setup):
    adapter, tr, registry = setup
    answers = iter([True, False])
    adapter.write_guard = lambda request: next(answers)
    with pytest.raises(PermissionError):
        adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert not tr.writes
    assert (
        registry.unresolved_intent_summary(symbol="005930", active_date=DATE)[
            "unresolved_intent_count"
        ]
        == 0
    )


def test_reservation_failure_prevents_transport(setup, monkeypatch):
    adapter, tr, _ = setup

    def fail(**kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(adapter.registry, "reserve", fail)
    with pytest.raises(OSError):
        adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert not tr.writes


def test_cross_owner_or_account_never_reaches_broker(setup, monkeypatch):
    adapter, tr, _ = setup
    adapter.context = replace(adapter.context, owner_id="different-owner")
    assert not adapter.snapshot(TARGET).source_ok
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "other-account")
    assert not adapter.snapshot(TARGET).source_ok
    assert not tr.calls


def test_midnight_does_not_reuse_undated_order_number(setup):
    adapter, tr, _ = setup
    adapter.now_ms = lambda: NOW + 86400000
    assert (
        adapter.snapshot(TARGET).error
        == "cross_date_current_ledger_requires_owner_recovery"
    )
    assert not tr.calls


def test_date_change_during_read_or_guard_prevents_write(setup):
    adapter, tr, _ = setup
    times = iter([NOW, NOW, NOW + 86400000])
    adapter.now_ms = lambda: next(times)
    with pytest.raises(ValueError):
        adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    assert not tr.writes


@pytest.mark.parametrize(
    "field,value", [("stex_tp", "9"), ("sor_yn", "N"), ("sor_yn", None)]
)
def test_current_route_conflict_not_complete(setup, field, value):
    adapter, tr, _ = setup
    tr.current = [current(**{field: value})]
    assert adapter.snapshot(TARGET).error == "current_broker_route_conflict"


def test_undefined_history_route_not_guessed(setup):
    adapter, tr, _ = setup
    tr.detailed = [detail(dmst_stex_tp="unknown")]
    assert adapter.snapshot(TARGET).error == "dated_broker_route_unresolved"


def test_transitive_successor_not_absence(setup):
    adapter, tr, _ = setup
    adapter.cancel_owned_sell(TARGET, quantity=6, action_id="cancel")
    tr.detailed = [
        detail(ord_remnq="0"),
        detail(ord_no="0000003", ori_ord=TARGET.order_no, ord_qty="6", ord_remnq="0"),
    ]
    tr.current = [current(ord_no="0000004", orig_ord_no="0000003")]
    assert adapter.snapshot(TARGET).error == "unknown_or_open_successor"


@pytest.mark.parametrize("price", [None, 0, True, 70101, 70000.0, "70000"])
def test_no_price_coercion_or_market_fallback(setup, price):
    adapter, tr, _ = setup
    with pytest.raises(ValueError):
        adapter.submit_owned_sell(
            TARGET, quantity=6, limit_price=price, action_id="sell"
        )
    assert not tr.calls


def test_transport_valueerror_does_not_expose_credentials(setup):
    adapter, _, _ = setup

    def fail(**kwargs):
        raise ValueError("private-token-and-account")

    adapter.post = fail
    assert adapter.snapshot(TARGET).error == "ValueError"


@pytest.mark.parametrize(
    "module_name,class_name",
    [
        ("low_price_two_leg", "KiwoomLowPriceTwoLegGateway"),
        ("samsung_morning_one_share", "KiwoomOneShareGateway"),
        ("samsung_midday_one_share", "KiwoomMiddayOneShareGateway"),
        ("samsung_afternoon_one_share", "KiwoomAfternoonOneShareGateway"),
        ("widget_auto_trade", "KiwoomSharedTokenOrderGateway"),
    ],
)
def test_every_real_gateway_builds_correctly_scoped_disabled_adapter(
    setup, module_name, class_name
):
    from importlib import import_module

    adapter, tr, registry = setup
    cls = getattr(import_module("src.trading." + module_name + ".gateway"), class_name)
    # Constructors would load production defaults; this test exercises the real
    # factory with an explicitly injected inert transport and registry.
    gateway = cls.__new__(cls)
    gateway.symbol = "005930"
    gateway._post = tr
    gateway._require_write_authority = lambda: None
    kw = dict(registry=registry, context=adapter.context, policy_hash="a" * 64)
    if module_name == "widget_auto_trade":
        kw.update(
            context=replace(adapter.context, owner_type="widget_auto_trade"),
            code="005930",
        )
    bound = gateway.adaptive_exit_adapter(**kw)
    assert bound.write_guard is None
    assert bound.symbol == "005930"
    assert bound.maximum_quantity == (
        None if module_name == "widget_auto_trade" else 10
    )
    if module_name != "widget_auto_trade":
        bound.now_ms = lambda: NOW
        assert bound.snapshot(TARGET).source_ok
        assert all(r["fresh"] is True for r in tr.calls)
    else:
        assert bound.new_route("KRX") == "SOR"


@pytest.mark.parametrize(
    "module_name,class_name",
    [
        ("low_price_two_leg", "KiwoomLowPriceTwoLegGateway"),
        ("samsung_morning_one_share", "KiwoomOneShareGateway"),
        ("samsung_midday_one_share", "KiwoomMiddayOneShareGateway"),
        ("samsung_afternoon_one_share", "KiwoomAfternoonOneShareGateway"),
    ],
)
def test_fresh_episode_read_bypasses_cache_but_retains_existing_pacing(
    setup, monkeypatch, module_name, class_name
):
    from importlib import import_module

    module = import_module("src.trading." + module_name + ".gateway")
    gateway = getattr(module, class_name).__new__(getattr(module, class_name))
    gateway._token = lambda: "test-only"
    gateway.base_url = "https://api.kiwoom.com"
    gateway.read_retry_sleep = None
    gateway.read_pacing_enabled = True
    gateway.read_pacer = object()
    gateway._account_read_cache = object()
    gateway._current_open_read_cache = object()
    calls = []

    def paced(**kw):
        calls.append(kw)
        return response({"return_code": 0})

    monkeypatch.setattr(module, "post_kiwoom_episode_read", paced)
    for fresh in (False, True):
        gateway._post(
            endpoint="/api/dostk/acnt", api_id="kt00007", payload={}, fresh=fresh
        )
    assert calls[0]["cache"] is gateway._account_read_cache
    assert "cache" not in calls[1]
    assert (
        calls[1]["pacing_enabled"] is True and calls[1]["pacer"] is gateway.read_pacer
    )


@pytest.mark.parametrize(
    "profile_id", sorted(profiles_for_target_date(date.fromisoformat(DATE)))
)
def test_all_registered_low_price_profiles_have_inert_adapter(setup, profile_id):
    from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway

    adapter, tr, registry = setup
    profile = profiles_for_target_date(date.fromisoformat(DATE))[profile_id]
    gateway = KiwoomLowPriceTwoLegGateway(
        symbol=profile.policy.symbol,
        request_session=SimpleNamespace(),
        token_loader=lambda: None,
    )
    bound = gateway.adaptive_exit_adapter(
        registry=registry,
        context=replace(adapter.context, owner_id=profile_id),
        policy_hash="a" * 64,
    )
    assert bound.symbol == profile.policy.symbol and bound.routes == ("SOR",)
    assert bound.write_guard is None
    with pytest.raises(PermissionError):
        bound.require_write_authority()
    assert tr.calls == []


def test_widget_current_unfilled_uses_shared_execution_read_budget(setup, monkeypatch):
    from src.trading.widget_auto_trade.gateway import KiwoomSharedTokenOrderGateway
    from src.utils import kiwoom_utils

    calls = []

    def acquire(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(admitted=False, reason="test-budget-full")

    monkeypatch.setattr(
        kiwoom_utils, "resolve_kiwoom_request_token", lambda value: value
    )
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda path: "https://api.kiwoom.com" + path
    )
    monkeypatch.setattr(kiwoom_utils, "acquire_kiwoom_read_capacity", acquire)
    gateway = KiwoomSharedTokenOrderGateway(
        request_session=SimpleNamespace(),
        token_loader=lambda: "test-only",
        shared_read_control_enabled=True,
    )
    with pytest.raises(RuntimeError, match="rate_deferred"):
        gateway._post(
            endpoint="/api/dostk/acnt", api_id="ka10075", payload={"stk_cd": "005930"}
        )
    assert (
        calls[0]["api_id"] == "ka10075"
        and calls[0]["request_class"] == "execution_critical"
    )


@pytest.mark.parametrize("headers", [{}, {"cont-yn": ""}, {"cont-yn": "N"}])
def test_optional_no_more_pages_header_is_not_an_extra_gate(setup, headers):
    adapter, tr, _ = setup
    tr.overrides["ka10075"] = (
        SimpleNamespace(status_code=200, headers=headers),
        {"return_code": 0, "oso": [current()]},
    )
    assert adapter.snapshot(TARGET).source_ok


def test_conflicting_response_api_id_is_not_valid_source(setup):
    adapter, tr, _ = setup
    tr.overrides["ka10075"] = response(
        {"return_code": 0, "oso": [current()]}, {"cont-yn": "N", "api-id": "wrong-api"}
    )
    assert adapter.snapshot(TARGET).error == "broker_response_api_mismatch"
