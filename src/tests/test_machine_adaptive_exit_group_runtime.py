from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    TARGET,
    Transport,
    current,
    detail,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.group_runtime import (
    GroupCoordinator,
    RULE,
    RunnerAllocation,
)
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.adaptive_exit.source import OwnerScope
from src.trading.order.adaptive_exit.target_group import TargetGroup
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
)


class Store:
    def __init__(self):
        self.records = {}
        self.writes = 0
        self.fail = None

    def load(self, key):
        return deepcopy(self.records.get(key))

    def save(self, key, expected, payload):
        existing = self.records.get(key)
        assert (existing["canonical_sha256"] if existing else None) == expected
        if self.fail == "before":
            raise OSError("store unavailable")
        if self.fail == "noop":
            return
        self.records[key] = json.loads(json.dumps(payload))
        self.writes += 1
        if self.fail == "after":
            raise OSError("response lost after durable commit")


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "group-test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = OwnerOrderContext("episode", "episode:test", "position:test", "group")
    lots = []
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
    target = registry.reserve(
        context=replace(context, client_intent_id="target"),
        symbol="005930",
        side="SELL",
        quantity=10,
        route="SOR",
        order_date=DATE,
    )
    registry.transition(target, state="ORDER_BOUND", broker_order_no=TARGET.order_no)
    group = TargetGroup(
        OwnerScope("episode", "test", "005930", "SOR", "KRX"),
        "episode1",
        TARGET,
        70700,
        tuple(lots),
        "f" * 64,
    )
    allocation = RunnerAllocation(
        group.to_payload()["canonical_sha256"],
        "a" * 64,
        "b" * 64,
        RULE,
        ("runner_lot",),
        ("runner_lot", "target_lot"),
    )
    transport, store = Transport(), Store()
    flags = {"lock": True, "approval": True, "custody": True, "now": NOW}
    adapter = RegisteredSellAdapter(
        post=transport,
        registry=registry,
        context=context,
        symbol="005930",
        routes=("SOR",),
        policy_hash=allocation.policy_hash,
        maximum_quantity=10,
        require_write_authority=lambda: None,
        write_guard=lambda _: True,
        now_ms=lambda: flags["now"],
    )

    def make(**changes):
        return GroupCoordinator(
            **{
                "group": group,
                "allocation": allocation,
                "adapter": adapter,
                "max_snapshot_age_ms": 1000,
                "load_record": store.load,
                "save_record": store.save,
                "lock_held": lambda: flags["lock"],
                "authorize_binding": lambda _: flags["approval"],
                "owner_guard": lambda _: flags["custody"],
                **changes,
            }
        )

    return make, adapter, transport, store, flags


def send_existing_cancel(coordinator, adapter):
    # Only a fake transport writes. The coordinator itself has NO write call.
    ack = adapter.cancel_owned_sell(
        TARGET, quantity=6, action_id=coordinator.cancel_client_id
    )
    assert ack.accepted
    return ack


def confirmed(transport, filled=1):
    transport.detailed = [
        detail(cntr_qty=str(filled), ord_remnq=str(4 - filled)),
        detail(
            ord_no="0000003",
            ori_ord=TARGET.order_no,
            ord_qty="6",
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty="6",
            cnfm_tm="12:59:59",
        ),
    ]
    transport.current = [current(cntr_qty=str(filled), oso_qty=str(4 - filled))]


def test_freeze_is_durable_before_cancel_and_restart_is_idempotent(setup):
    make, adapter, transport, store, _ = setup
    coordinator = make()
    frozen = coordinator.freeze()
    assert frozen["requested_qty"] == 6 and store.writes == 1
    calls = len(transport.calls)
    assert make().freeze() == frozen
    assert len(transport.calls) == calls and not transport.writes
    send_existing_cancel(coordinator, adapter)
    assert make().bind_cancel()["phase"] == "CANCEL_BOUND"
    assert make().bind_cancel()["release"] is None  # ACK releases nothing


@pytest.mark.parametrize("filled", range(4))
def test_cancel_release_preserves_nonrunner_reservation_and_no_sell_authority(
    setup, filled
):
    make, adapter, transport, store, _ = setup
    c = make()
    c.freeze()
    send_existing_cancel(c, adapter)
    confirmed(transport, filled)
    r = c.reconcile()["release"]
    assert r["target_reserved_qty"] == 4 - filled and r["runner_released_qty"] == 6
    assert (
        r["target_filled_qty"] + r["target_reserved_qty"] + r["runner_released_qty"]
        == 10
    )
    assert r["actual_lot_fill_attribution"] is r["realized_pnl"] is None
    assert r["sell_authority"] is False
    assert [r["book_open_qty"] for r in r["book_lots"]] == [6, 4 - filled]
    count = store.writes
    assert make().reconcile()["release"] == r
    assert store.writes == count and len(transport.writes) == 1
    target = adapter.registry.assert_owner(
        context=adapter.context, order_date=DATE, broker_order_no=TARGET.order_no
    )
    assert target["state"] == "ORDER_BOUND" and target["canceled_qty"] == 6


def test_late_target_fill_refresh_does_not_reassign_released_runner(setup):
    make, adapter, transport, _, _ = setup
    c = make()
    c.freeze()
    send_existing_cancel(c, adapter)
    confirmed(transport, 0)
    first = c.reconcile()["release"]
    confirmed(transport, 3)
    later = make().reconcile()["release"]
    assert first["cancel_proof_hash"] == later["cancel_proof_hash"]
    assert later["runner_released_qty"] == first["runner_released_qty"] == 6
    assert later["target_reserved_qty"] == 1


@pytest.mark.parametrize("flag", ["lock", "approval", "custody"])
@pytest.mark.parametrize("value", [False, None, 1])
def test_missing_guard_rejects_before_reads_or_persistence(setup, flag, value):
    make, _, transport, store, flags = setup
    flags[flag] = value
    with pytest.raises(PermissionError):
        make().freeze()
    assert not transport.calls and not store.records


@pytest.mark.parametrize("method", ["bind_cancel", "reconcile"])
def test_missing_frozen_allocation_cannot_be_reconstructed_from_cancel(setup, method):
    make, adapter, transport, store, _ = setup
    c = make()
    send_existing_cancel(c, adapter)
    calls = len(transport.calls)
    with pytest.raises(ValueError, match="persisted_before_cancel"):
        getattr(c, method)()
    with pytest.raises(ValueError, match="freeze_after_cancel"):
        c.freeze()
    assert len(transport.calls) == calls and not store.records


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_freeze_storage_failures_never_send_cancel(setup, failure):
    make, _, transport, store, _ = setup
    store.fail = failure
    with pytest.raises((OSError, ValueError)):
        make().freeze()
    assert not transport.writes
    if failure == "after":
        store.fail = None
        assert make().freeze()["phase"] == "ALLOCATION_FROZEN"
        assert store.writes == 1


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_registry_release_then_group_save_failure_is_restart_recoverable(
    setup, failure
):
    make, adapter, transport, store, _ = setup
    c = make()
    c.freeze()
    send_existing_cancel(c, adapter)
    c.bind_cancel()
    confirmed(transport)
    store.fail = failure
    with pytest.raises((OSError, ValueError)):
        c.reconcile()
    target = adapter.registry.order_owner(
        order_date=DATE, broker_order_no=TARGET.order_no
    )
    assert target["canceled_qty"] == 6
    store.fail = None
    assert make().reconcile()["release"]["runner_released_qty"] == 6
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "kind", ["ack", "partial", "missing_current", "unknown_cancel", "whole_terminal"]
)
def test_unsupported_evidence_is_recovery_not_resend_or_false_release(setup, kind):
    make, adapter, transport, store, _ = setup
    c = make()
    c.freeze()
    send_existing_cancel(c, adapter)
    if kind != "ack":
        confirmed(transport)
        if kind == "partial":
            transport.detailed[1]["cnfm_qty"] = "5"
        elif kind == "missing_current":
            transport.current = []
        elif kind == "unknown_cancel":
            transport.current.append(
                current(ord_no="0000008", orig_ord_no=TARGET.order_no)
            )
        else:
            transport.detailed[0].update(cntr_qty="4", ord_remnq="0")
            transport.current = []
    with pytest.raises(ValueError, match="requires_owner_recovery"):
        c.reconcile()
    assert store.load(c.key)["phase"] == "CANCEL_BOUND"
    assert store.load(c.key)["release"] is None and len(transport.writes) == 1


@pytest.mark.parametrize("filled", range(4, 11))
def test_whole_remaining_target_is_not_forced_through_partial_route(setup, filled):
    make, _, transport, store, _ = setup
    transport.detailed = [detail(cntr_qty=str(filled), ord_remnq=str(10 - filled))]
    transport.current = (
        [current(cntr_qty=str(filled), oso_qty=str(10 - filled))] if filled < 10 else []
    )
    with pytest.raises(ValueError):
        make().freeze()
    assert not store.records and not transport.writes


def test_changed_allocation_cannot_create_second_target_slot(setup):
    make, _, transport, store, _ = setup
    c = make()
    c.freeze()
    other = make(allocation=replace(c.allocation, approval_receipt_hash="c" * 64))
    assert other.key == c.key
    calls = len(transport.calls)
    with pytest.raises(ValueError, match="saved_binding"):
        other.freeze()
    assert len(store.records) == 1 and len(transport.calls) == calls


def test_source_only_observation_hash_does_not_grant_enrollment(setup):
    make, _, transport, store, _ = setup
    with pytest.raises(PermissionError):
        make(
            authorize_binding=lambda binding: (
                binding["allocation"]["approval_receipt_hash"] == "f" * 64
            )
        ).freeze()
    assert not store.records and not transport.calls


@pytest.mark.parametrize(
    "kind", ["phase", "requested", "authority", "book", "source", "date", "newfield"]
)
def test_corrupt_saved_payload_rejected_even_with_new_hash(setup, kind):
    make, adapter, transport, store, _ = setup
    c = make()
    c.freeze()
    send_existing_cancel(c, adapter)
    confirmed(transport)
    c.reconcile()
    raw = store.records[c.key]
    if kind == "phase":
        raw["phase"] = "FLAT"
    elif kind == "requested":
        raw["requested_qty"] = 7
    elif kind == "authority":
        raw["release"]["sell_authority"] = True
    elif kind == "book":
        raw["release"]["book_lots"][0]["book_open_qty"] = 7
    elif kind == "source":
        raw["release"]["snapshot_hash"] = ""
    elif kind == "date":
        raw["cancel_order"]["trading_date"] = "2026-09-08"
    else:
        raw["extra"] = True
    raw["canonical_sha256"] = canonical_sha256(raw)
    calls = len(transport.calls)
    with pytest.raises(ValueError):
        make().reconcile()
    assert len(transport.calls) == calls


@pytest.mark.parametrize("stage", ["freeze", "reconcile"])
def test_guard_loss_during_read_never_publishes_success(setup, stage):
    make, adapter, transport, store, flags = setup
    c = make()
    if stage == "reconcile":
        c.freeze()
        send_existing_cancel(c, adapter)
        c.bind_cancel()
        confirmed(transport)
    post = adapter.post

    def lose_lock(**kwargs):
        result = post(**kwargs)
        flags["lock"] = False
        return result

    adapter.post = lose_lock
    with pytest.raises(PermissionError):
        getattr(c, stage)()
    flags["lock"] = True
    raw = store.load(c.key)
    assert raw is None or raw["release"] is None


def test_stale_generation_between_read_and_save_cannot_overwrite_other_coordinator(
    setup,
):
    make, _, transport, store, _ = setup
    c = make()
    save = c.save_record

    def competing(key, expected, payload):
        store.records[key] = dict(payload, canonical_sha256="c" * 64)
        save(key, expected, payload)

    c.save_record = competing
    with pytest.raises(AssertionError):
        c.freeze()
    assert not transport.writes


def test_lost_cancel_ack_requires_recovery_without_inventing_order_id(setup):
    make, adapter, transport, store, _ = setup
    c = make()
    c.freeze()
    transport.crash = True
    ack = adapter.cancel_owned_sell(TARGET, quantity=6, action_id=c.cancel_client_id)
    assert ack.ambiguous
    with pytest.raises(ValueError, match="ambiguous"):
        c.reconcile()
    assert store.load(c.key)["phase"] == "ALLOCATION_FROZEN"
    assert len(transport.writes) == 1


@pytest.mark.parametrize("filled", range(31))
def test_three_lot_allocation_conservation_monotonicity_and_explicit_priority(
    setup, filled
):
    make, _, _, _, _ = setup
    c = make()
    group = replace(
        c.group,
        lots=(
            ("a", OrderKey(DATE, "0000011"), 10, NOW - 5000, 70000.0),
            ("b", OrderKey(DATE, "0000012"), 10, NOW - 4000, 70100.0),
            ("c", OrderKey(DATE, "0000013"), 10, NOW - 3000, 70200.0),
        ),
    )
    allocation = replace(
        c.allocation,
        group_hash=group.to_payload()["canonical_sha256"],
        lot_order=("c", "b", "a"),
        runner_lot_ids=("b", "c"),
    )
    rows = allocation.balances(group, filled)
    assert sum(r["target_book_filled_qty"] for r in rows) == filled
    assert sum(r["book_open_qty"] for r in rows) == 30 - filled
    assert rows[2]["target_book_filled_qty"] == min(10, filled)  # nonrunner a FIRST
    assert rows[0]["target_book_filled_qty"] == min(
        10, max(0, filled - 10)
    )  # then declared c
    if filled:
        before = allocation.balances(group, filled - 1)
        assert all(
            a["book_open_qty"] >= b["book_open_qty"] for a, b in zip(before, rows)
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"rule": "fifo"},
        {"rule": ""},
        {"lot_order": ("target_lot",)},
        {"lot_order": ("target_lot", "target_lot")},
        {"runner_lot_ids": ()},
        {"runner_lot_ids": ("target_lot", "runner_lot")},
        {"runner_lot_ids": ("foreign",)},
        {"runner_lot_ids": ["runner_lot"]},
        {"approval_receipt_hash": "research"},
        {"group_hash": "a" * 64},
        {"lot_order": (None, "target_lot")},
    ],
)
def test_no_default_or_malformed_allocation(setup, changes):
    make, _, transport, store, _ = setup
    c = make()
    with pytest.raises(ValueError):
        make(allocation=replace(c.allocation, **changes))
    assert not transport.calls and not store.records


@pytest.mark.parametrize("delta", [-86400000, 86400000])
@pytest.mark.parametrize("stage", ["freeze", "bind_cancel", "reconcile"])
def test_date_rollover_does_not_rebind_current_order_numbers(setup, delta, stage):
    make, adapter, transport, store, flags = setup
    c = make()
    if stage != "freeze":
        c.freeze()
        send_existing_cancel(c, adapter)
    flags["now"] += delta
    calls, writes = len(transport.calls), store.writes
    with pytest.raises(ValueError, match="cross_date"):
        getattr(c, stage)()
    assert len(transport.calls) == calls and store.writes == writes


@pytest.mark.parametrize("delta", [-86400000, 1])
def test_bad_freeze_time_is_rejected_before_persistence(setup, delta):
    make, _, transport, store, _ = setup
    c = make()
    save = c._save

    def corrupt(previous, candidate):
        return save(previous, candidate | {"frozen_at_ms": NOW + delta})

    c._save = corrupt
    with pytest.raises(ValueError, match="schema_conflict"):
        c.freeze()
    assert not store.records and not transport.writes


def test_adapter_account_change_fails_before_read(setup, monkeypatch):
    make, _, transport, store, _ = setup
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "different-account")
    with pytest.raises(PermissionError):
        make().freeze()
    assert not transport.calls and not store.records


@pytest.mark.parametrize("delta", [1001, -1])
def test_read_staleness_or_clock_regression_cannot_freeze(setup, delta):
    make, adapter, transport, store, flags = setup
    original = adapter.reconcile_owned_sell

    def delayed(order):
        result = original(order)
        flags["now"] += delta
        return result

    adapter.reconcile_owned_sell = delayed
    with pytest.raises(ValueError, match="source_stale"):
        make().freeze()
    assert not store.records and not transport.writes


@pytest.mark.parametrize("which", ["target", "buy"])
def test_exact_registry_owner_conflict_blocks_before_broker_read(setup, which):
    make, adapter, transport, store, _ = setup
    c = make()
    original = adapter.registry.assert_owner

    def wrong(**kwargs):
        result = original(**kwargs)
        if (result["side"] == "SELL") == (which == "target"):
            return result | {"route": "NXT"}
        return result

    adapter.registry.assert_owner = wrong
    with pytest.raises(ValueError, match="binding_conflict"):
        c.freeze()
    assert not transport.calls and not store.records


@pytest.mark.parametrize(
    "kind", ["policy", "context", "symbol", "route", "bound", "binding", "allocation"]
)
def test_mutation_after_construction_cannot_reuse_approval(setup, kind):
    make, adapter, transport, store, _ = setup
    c = make()
    if kind == "policy":
        adapter.policy_hash = "c" * 64
    elif kind == "context":
        adapter.context = replace(adapter.context, client_intent_id="foreign")
    elif kind == "symbol":
        adapter.symbol = "005935"
    elif kind == "route":
        adapter.routes = ("NXT",)
    elif kind == "bound":
        c.max_age += 1
    elif kind == "binding":
        c.binding["allocation"]["approval_receipt_hash"] = "c" * 64
    else:
        c.allocation = replace(c.allocation, approval_receipt_hash="c" * 64)
    with pytest.raises(ValueError, match="binding_changed"):
        c.freeze()
    assert not transport.calls and not store.records
