from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests import test_machine_adaptive_exit_group_runtime as group_tests
from src.tests.test_machine_adaptive_exit_group_runtime import confirmed
from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    TARGET,
    current,
    detail,
)
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.group_execution import (
    GroupAction,
    GroupRunnerExecutor,
    RunnerBounds,
)
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.owner_custody_registry import OwnerRegistryConflict
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256


@pytest.fixture
def group_setup(tmp_path, monkeypatch):
    return group_tests.setup.__wrapped__(tmp_path, monkeypatch)


@pytest.fixture
def setup(group_setup):
    make_coordinator, adapter, transport, store, flags = group_setup
    flags["action_allowed"] = True

    def make(**changes):
        def factory(guard):
            child = RegisteredSellAdapter(
                post=transport,
                registry=adapter.registry,
                context=adapter.context,
                symbol=adapter.symbol,
                routes=adapter.routes,
                policy_hash=adapter.policy_hash,
                maximum_quantity=adapter.maximum_quantity,
                require_write_authority=lambda: None,
                write_guard=guard,
                now_ms=lambda: flags["now"],
            )
            return make_coordinator(adapter=child)

        return GroupRunnerExecutor(
            **{
                "coordinator_factory": factory,
                "bounds": RunnerBounds(1000, 500, 2000),
                "execution_approval_receipt_hash": "e" * 64,
                "authorize_action": lambda binding, record, now: flags[
                    "action_allowed"
                ],
                **changes,
            }
        )

    return make, adapter, transport, store, flags


def action(kind, now=NOW, price=None):
    return GroupAction(kind, "c" * 64, "d" * 64, now, price)


def release(executor, transport):
    result = executor.request_release(action("RELEASE_RUNNER"))
    assert result["status"] == "order_bound" and result["order_no"] == "0000003"
    confirmed(transport)


def sell(executor, transport):
    release(executor, transport)
    transport.write_body = {
        "return_code": 0,
        "ord_no": "0000005",
        "dmst_stex_tp": "SOR",
    }
    result = executor.sell_released(action("SELL_RUNNER", price=70400))
    assert result["order_no"] == "0000005"


def runner_market(transport, filled=0, remaining=None, ttl_child=False):
    confirmed(transport)
    remaining = 6 - filled if remaining is None else remaining
    transport.detailed.append(
        detail(
            ord_no="0000005",
            ord_qty="6",
            cntr_qty=str(filled),
            ord_remnq=str(remaining),
        )
    )
    if remaining:
        transport.current.append(
            current(
                ord_no="0000005",
                ord_qty="6",
                cntr_qty=str(filled),
                oso_qty=str(remaining),
            )
        )
    if ttl_child:
        transport.detailed.append(
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


def test_first_runner_sell_preserves_target_order_and_ack_is_not_terminal(setup):
    make, adapter, transport, store, _ = setup
    e = make()
    sell(e, transport)
    assert [r["api_id"] for r in transport.writes] == ["kt10003", "kt10001"]
    assert transport.writes[0]["payload"]["cncl_qty"] == "6"
    assert transport.writes[1]["payload"]["ord_qty"] == "6"
    assert transport.writes[1]["payload"]["ord_uv"] == "70400"
    target = adapter.registry.order_owner(
        order_date=DATE, broker_order_no=TARGET.order_no
    )
    assert target["state"] == "ORDER_BOUND" and target["canceled_qty"] == 6
    assert target["quantity"] - target["filled_qty"] - target["canceled_qty"] == 3
    assert e._read("SELL_RUNNER")["quantity"] == 6
    assert len(store.records) == 3  # group, cancel action, SELL action
    runner_market(transport)
    assert e.poll_runner()["status"] == "runner_working"
    assert (
        e.reconcile_release()["status"] == "runner_submitted_use_runner_reconciliation"
    )


def test_duplicate_or_restart_does_not_resubmit_or_reprice(setup):
    make, _, transport, _, flags = setup
    e = make()
    sell(e, transport)
    calls = len(transport.calls)
    flags["now"] += 1000  # stale decisions can recover known ACK, not create an order
    assert (
        make().sell_released(action("SELL_RUNNER", price=70400))["order_no"]
        == "0000005"
    )
    assert len(transport.calls) == calls
    assert make().request_release(action("RELEASE_RUNNER"))["order_no"] == "0000003"
    with pytest.raises(ValueError, match="immutable"):
        make().sell_released(action("SELL_RUNNER", price=70500))
    assert len(transport.writes) == 2


@pytest.mark.parametrize("fill", range(7))
def test_runner_terminal_never_becomes_group_flat_or_fabricated_pnl(setup, fill):
    make, _, transport, _, _ = setup
    e = make()
    sell(e, transport)
    runner_market(transport, fill, 0)
    result = e.poll_runner()
    assert result["status"] == (
        "runner_terminal" if fill == 6 else "runner_residual_requires_recovery"
    )
    assert result["runner_remaining_qty"] == 6 - fill
    assert result["runner_filled_qty"] == fill and result["group_terminal"] is False
    assert result["realized_pnl"] is None
    assert len(transport.writes) == 2


def test_ttl_cancels_only_fresh_runner_residual_then_terminal_reconciles(setup):
    make, _, transport, store, flags = setup
    e = make()
    sell(e, transport)
    runner_market(transport, 2)
    flags["now"] += 1000
    transport.write_body = {
        "return_code": 0,
        "ord_no": "0000006",
        "base_orig_ord_no": "0000005",
        "cncl_qty": "4",
    }
    result = e.poll_runner()
    assert result["status"] == "runner_cancel_pending"
    assert transport.writes[-1]["payload"]["orig_ord_no"] == "0000005"
    assert transport.writes[-1]["payload"]["cncl_qty"] == "4"
    assert len(store.records) == 4
    assert make().poll_runner()["status"] == "runner_cancel_pending"
    assert len(transport.writes) == 3
    flags["now"] += 2000
    assert e.poll_runner()["recovery_deadline_exceeded"] is True
    runner_market(transport, 2, 0, ttl_child=True)
    assert make().poll_runner()["status"] == "runner_residual_requires_recovery"
    assert len(transport.writes) == 3


@pytest.mark.parametrize("value", [False, None, 1])
def test_unapproved_action_has_no_write(setup, value):
    make, _, transport, store, flags = setup
    flags["action_allowed"] = value
    e = make()
    with pytest.raises(PermissionError):
        e.request_release(action("RELEASE_RUNNER"))
    assert not transport.writes
    assert e._read("RELEASE_RUNNER") is None


@pytest.mark.parametrize("kind", ["RELEASE_RUNNER", "SELL_RUNNER"])
@pytest.mark.parametrize("offset", [-501, 1])
def test_stale_or_future_decision_never_writes(setup, kind, offset):
    make, _, transport, _, _ = setup
    e = make()
    if kind == "SELL_RUNNER":
        release(e, transport)
    writes = len(transport.writes)
    method = e.request_release if kind == "RELEASE_RUNNER" else e.sell_released
    with pytest.raises((ValueError, PermissionError)):
        method(action(kind, NOW + offset, 70400 if kind == "SELL_RUNNER" else None))
    assert len(transport.writes) == writes


@pytest.mark.parametrize("kind", ["RELEASE_RUNNER", "SELL_RUNNER"])
@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_action_durable_save_failure_precedes_broker_write_and_is_recoverable(
    setup, kind, failure
):
    make, _, transport, store, _ = setup
    e = make()
    if kind == "SELL_RUNNER":
        release(e, transport)
        e.coordinator.reconcile()
        transport.write_body = {
            "return_code": 0,
            "ord_no": "0000005",
            "dmst_stex_tp": "SOR",
        }
    else:
        e.coordinator.freeze()
    writes = len(transport.writes)
    # Only fail the action slot; coordinator quantity receipts remain available.
    save = e.coordinator.save_record

    def fail_action(key, expected, payload):
        store.fail = (
            failure
            if payload.get("schema", "").endswith("execution_action_v1")
            else None
        )
        return save(key, expected, payload)

    e.coordinator.save_record = fail_action
    request = action(kind, price=70400 if kind == "SELL_RUNNER" else None)
    with pytest.raises((ValueError, OSError)):
        (e.request_release if kind == "RELEASE_RUNNER" else e.sell_released)(request)
    assert len(transport.writes) == writes
    store.fail = None
    other = make()
    (other.request_release if kind == "RELEASE_RUNNER" else other.sell_released)(
        request
    )
    assert len(transport.writes) == writes + 1


@pytest.mark.parametrize("kind", ["RELEASE_RUNNER", "SELL_RUNNER"])
def test_ambiguous_ack_is_not_retried(setup, kind):
    make, _, transport, _, _ = setup
    e = make()
    if kind == "SELL_RUNNER":
        release(e, transport)
    transport.crash = True
    request = action(kind, price=70400 if kind == "SELL_RUNNER" else None)
    method = e.request_release if kind == "RELEASE_RUNNER" else e.sell_released
    assert method(request)["status"] == "recovery_required"
    writes = len(transport.writes)
    other = make()
    assert (other.request_release if kind == "RELEASE_RUNNER" else other.sell_released)(
        request
    )["status"] == "recovery_required"
    assert len(transport.writes) == writes


def test_no_direct_adapter_write_outside_persisted_executor_action(setup):
    make, _, transport, _, _ = setup
    e = make()
    with pytest.raises(PermissionError):
        e.coordinator.adapter.cancel_owned_sell(
            TARGET, quantity=6, action_id=e.coordinator.cancel_client_id
        )
    assert not transport.writes


def test_partial_cancel_ack_or_pure_group_receipt_cannot_authorize_sell(setup):
    make, _, transport, _, _ = setup
    e = make()
    e.request_release(action("RELEASE_RUNNER"))
    with pytest.raises(ValueError):
        e.sell_released(action("SELL_RUNNER", price=70400))
    assert len(transport.writes) == 1


def test_guard_rechecked_after_slow_broker_read_before_sell_reserve(setup):
    make, _, transport, _, flags = setup
    e = make()
    release(e, transport)
    original = e.coordinator.adapter.reconcile_partial_cancel
    count = 0

    def revoke(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 2:  # inside actual submit, after durable intent exists
            flags["action_allowed"] = False
        return result

    e.coordinator.adapter.reconcile_partial_cancel = revoke
    with pytest.raises(PermissionError):
        e.sell_released(action("SELL_RUNNER", price=70400))
    assert len(transport.writes) == 1
    assert e._intent(e._read("SELL_RUNNER")) is None


def test_different_numeric_bounds_cannot_adopt_existing_action(setup):
    make, _, transport, _, _ = setup
    e = make()
    e.request_release(action("RELEASE_RUNNER"))
    changed = make(bounds=RunnerBounds(1001, 500, 2000))
    with pytest.raises(ValueError, match="saved_action"):
        changed.request_release(action("RELEASE_RUNNER"))
    assert len(transport.writes) == 1


@pytest.mark.parametrize("quantity", [1, 5, 7, True, 0])
def test_broker_partial_primitive_rejects_wrong_release_quantity(group_setup, quantity):
    make, adapter, transport, _, _ = group_setup
    c = make()
    c.freeze()
    adapter.cancel_owned_sell(TARGET, quantity=6, action_id=c.cancel_client_id)
    confirmed(transport)
    with pytest.raises(ValueError):
        adapter.submit_partial_cancel_residual(
            TARGET,
            OrderKey(DATE, "0000003"),
            quantity=quantity,
            limit_price=70400,
            action_id="runner",
            max_snapshot_age_ms=1000,
        )
    assert len(transport.writes) == 1


def test_single_lot_terminal_guard_is_unchanged(group_setup):
    make, adapter, transport, _, _ = group_setup
    c = make()
    c.freeze()
    adapter.cancel_owned_sell(TARGET, quantity=6, action_id=c.cancel_client_id)
    confirmed(transport)
    c.reconcile()
    with pytest.raises(ValueError, match="terminal_predecessor"):
        adapter.submit_owned_sell(
            TARGET, quantity=6, limit_price=70400, action_id="wrong-owner-path"
        )
    assert len(transport.writes) == 1


def test_release_deadline_survives_repeated_reconciliation_and_restart(setup):
    make, _, transport, _, flags = setup
    e = make()
    release(e, transport)
    result = e.poll_runner()
    assert result["status"] == "runner_released_awaiting_decision"
    assert result["runner_released_qty"] == 6 and result["target_reserved_qty"] == 3
    assert result["recovery_deadline_ms"] == NOW + 2000
    flags["now"] += 2100
    result = make().poll_runner()
    assert result["recovery_deadline_ms"] == NOW + 2000
    assert result["recovery_deadline_exceeded"] is True
    assert len(transport.writes) == 1  # expiry grants no forced SELL


def test_missing_cancel_confirmation_is_bounded_not_free_inventory(setup):
    make, _, transport, _, flags = setup
    e = make()
    e.request_release(action("RELEASE_RUNNER"))
    flags["now"] += 2100
    result = make().poll_runner()
    assert result["status"] == "release_source_gap_requires_recovery"
    assert result["recovery_deadline_exceeded"] is True
    assert "runner_released_qty" not in result and len(transport.writes) == 1


@pytest.mark.parametrize("kind", ["RELEASE_RUNNER", "SELL_RUNNER", "CANCEL_RUNNER_TTL"])
@pytest.mark.parametrize("revoked", ["action_allowed", "lock", "now"])
def test_reservation_wait_rechecks_guards_before_transport(setup, kind, revoked):
    make, adapter, transport, _, flags = setup
    e = make()
    if kind == "SELL_RUNNER":
        release(e, transport)
    if kind == "CANCEL_RUNNER_TTL":
        sell(e, transport)
        runner_market(transport, 2)
        flags["now"] += 1000
    before = len(transport.writes)
    reserve = adapter.registry.reserve

    def slow_reserve(**kwargs):
        result = reserve(**kwargs)
        flags[revoked] = flags["now"] + 501 if revoked == "now" else False
        return result

    adapter.registry.reserve = slow_reserve
    with pytest.raises((PermissionError, ValueError)):
        if kind == "CANCEL_RUNNER_TTL":
            e.poll_runner()
        elif kind == "SELL_RUNNER":
            e.sell_released(action(kind, price=70400))
        else:
            e.request_release(action(kind))
    assert len(transport.writes) == before
    flags.update(action_allowed=True, lock=True)
    saved = e._read(kind)
    assert e._intent(saved)["state"] == "INTENT_RESERVED"
    # A post-reservation local veto is an explicit recovery case, never resent.
    if kind == "CANCEL_RUNNER_TTL":
        assert make().poll_runner()["status"] == "recovery_required"
    elif kind == "SELL_RUNNER":
        assert (
            make().sell_released(action(kind, price=70400))["status"]
            == "recovery_required"
        )
    else:
        assert make().request_release(action(kind))["status"] == "recovery_required"
    assert len(transport.writes) == before


def test_partial_source_age_rechecked_after_reservation_even_with_fresh_decision(setup):
    make, adapter, transport, _, flags = setup
    e = make(bounds=RunnerBounds(1000, 5000, 2000))
    release(e, transport)
    reserve = adapter.registry.reserve

    def slow_reserve(**kwargs):
        result = reserve(**kwargs)
        flags["now"] += 1001  # approved action still fresh, release source is not
        return result

    adapter.registry.reserve = slow_reserve
    with pytest.raises(ValueError, match="release_expired_before_write"):
        e.sell_released(action("SELL_RUNNER", price=70400))
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", 5),
        ("quantity", True),
        ("binding_hash", "9" * 64),
        ("created_at_ms", NOW + 1),
        ("created_at_ms", NOW - 1),
    ],
)
def test_rehashed_saved_release_corruption_is_rejected(setup, field, value):
    make, _, transport, store, _ = setup
    e = make()
    e.request_release(action("RELEASE_RUNNER"))
    row = store.records[e._key("RELEASE_RUNNER")]
    row[field] = value
    row["canonical_sha256"] = canonical_sha256(row)
    with pytest.raises(ValueError):
        make().request_release(action("RELEASE_RUNNER"))
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("account_key", "other"),
        ("owner_id", "other"),
        ("position_id", "other"),
        ("order_date", "2026-09-08"),
        ("client_intent_id", "other"),
        ("source_contract", "other"),
        ("schema", "other"),
        ("receipt_sha256", ""),
    ],
)
def test_runner_terminal_proof_checks_exact_identity_and_contract(setup, field, value):
    make, adapter, transport, _, _ = setup
    e = make()
    sell(e, transport)
    runner_market(transport, 6, 0)
    e.coordinator.adapter.reconcile_owned_sell(OrderKey(DATE, "0000005"))
    read = adapter.registry.intent_for_client

    def corrupt(**kwargs):
        row = read(**kwargs)
        if row and row.get("broker_order_no") == "0000005":
            row = deepcopy(row)
            row["terminal_reconciliation"][field] = value
        return row

    adapter.registry.intent_for_client = corrupt
    with pytest.raises(ValueError, match="exact_terminal_proof"):
        e.poll_runner()
    assert len(transport.writes) == 2


def test_other_order_commitment_prevents_runner_oversell(setup):
    make, adapter, transport, _, _ = setup
    e = make()
    release(e, transport)
    e.coordinator.reconcile()
    adapter.registry.reserve(
        context=replace(adapter.context, client_intent_id="another-owned-sell"),
        symbol=adapter.symbol,
        side="SELL",
        quantity=1,
        route="SOR",
        order_date=DATE,
    )
    with pytest.raises(
        OwnerRegistryConflict, match="sell_quantity_exceeds_owner_available"
    ):
        e.sell_released(action("SELL_RUNNER", price=70400))
    assert len(transport.writes) == 1


def test_runner_ttl_fill_race_never_sends_old_larger_quantity(setup):
    make, _, transport, _, flags = setup
    e = make()
    sell(e, transport)
    runner_market(transport, 2)
    flags["now"] += 1000
    save = e.coordinator.save_record

    def fill_before_cancel_read(key, expected, record):
        save(key, expected, record)
        if key == e._key("CANCEL_RUNNER_TTL"):
            runner_market(transport, 3)

    e.coordinator.save_record = fill_before_cancel_read
    with pytest.raises(ValueError, match="fresh_owned_open_remainder"):
        e.poll_runner()
    assert len(transport.writes) == 2
    assert e._intent(e._read("CANCEL_RUNNER_TTL")) is None
    # Quantity reduction/repricing is a new recovery contract, not a blind retry.
    with pytest.raises(ValueError):
        make().poll_runner()
    assert len(transport.writes) == 2
