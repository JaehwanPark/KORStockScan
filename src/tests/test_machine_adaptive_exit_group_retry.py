"""Offline multi-generation execution; never construct a live API client."""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests import test_machine_adaptive_exit_group_execution as first
from src.tests import test_machine_adaptive_exit_group_runtime as groups
from src.tests.test_machine_adaptive_exit_broker import DATE, current, detail
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.group_execution import RunnerBounds


@pytest.fixture
def setup(tmp_path, monkeypatch):
    return first.setup.__wrapped__(groups.setup.__wrapped__(tmp_path, monkeypatch))


def enabled(make, **changes):
    return make(
        **{
            "bounds": RunnerBounds(1000, 500, 2000, 3),
            "authorize_retry": lambda binding, original, record, now: True,
            **changes,
        }
    )


def ack(t, number, parent=None, qty=None):
    t.write_body = {"return_code": 0, "ord_no": number, "dmst_stex_tp": "SOR"}
    if parent:
        t.write_body.update(base_orig_ord_no=parent, cncl_qty=str(qty))


def runner(t, number, quantity, filled, remaining):
    t.detailed = [r for r in t.detailed if r["ord_no"] != number]
    t.current = [r for r in t.current if r["ord_no"] != number]
    t.detailed.append(
        detail(
            ord_no=number,
            ord_qty=str(quantity),
            cntr_qty=str(filled),
            ord_remnq=str(remaining),
        )
    )
    if remaining:
        t.current.append(
            current(
                ord_no=number,
                ord_qty=str(quantity),
                cntr_qty=str(filled),
                oso_qty=str(remaining),
            )
        )


def canceled(e, t, flags, attempt=1, filled=2, late_filled=None):
    record = e._read("SELL_RUNNER", attempt)
    row = e._intent(record)
    number, quantity = row["broker_order_no"], record["quantity"]
    runner(t, number, quantity, filled, quantity - filled)
    flags["now"] += 1000
    child_no = f"{int(number) + 1:07d}"
    ack(t, child_no, number, quantity - filled)
    assert e.poll_runner()["status"] == "runner_cancel_pending"
    final_fill = filled if late_filled is None else late_filled
    runner(t, number, quantity, final_fill, 0)
    t.detailed.append(
        detail(
            ord_no=child_no,
            ori_ord=number,
            ord_qty=str(quantity - filled),
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty=str(quantity - final_fill),
            cnfm_tm="12:59:59",
        )
    )
    assert (
        e.reconcile_runner_cancel(attempt_no=attempt)["status"]
        == "runner_cancel_terminal"
    )


def prepared(setup, **changes):
    make, adapter, t, store, flags = setup
    e = enabled(make, **changes)
    first.sell(e, t)
    canceled(e, t, flags)
    return e


def retry(e, t, flags, attempt=2):
    number = f"{attempt * 2 + 3:07d}"
    ack(t, number)
    action = first.action("SELL_RUNNER", now=flags["now"], price=70300)
    return action, e.retry_runner(action, attempt_no=attempt)


def test_three_generations_sum_actual_fills_and_restart_does_not_resubmit(setup):
    make, adapter, t, store, flags = setup
    e = prepared(setup)
    action2, result = retry(e, t, flags)
    assert result["order_no"] == "0000007"
    assert t.writes[-1]["payload"]["ord_qty"] == "4"
    writes = len(t.writes)
    assert enabled(make).retry_runner(action2, attempt_no=2) == result
    assert len(t.writes) == writes
    canceled(e, t, flags, attempt=2, filled=1)
    _, result = retry(enabled(make), t, flags, attempt=3)
    assert result["order_no"] == "0000009"
    assert t.writes[-1]["payload"]["ord_qty"] == "3"
    runner(t, "0000009", 3, 3, 0)
    runner(t, "0000002", 10, 4, 0)
    assert e.poll_runner()["status"] == "runner_terminal"
    queries = len(t.calls)
    final = e.reconcile_group_terminal()
    assert len(t.calls) - queries == 4  # target + latest runner, dated/current
    assert final["group_terminal"] is True
    r = final["receipt"]
    assert [o["filled_qty"] for o in r["orders"]] == [4, 2, 1, 3]
    assert r["buy_filled_qty"] == r["sell_filled_qty"] == 10
    assert len(r["cancel_proofs"]) == 3
    assert r["realized_net_profit_krw"] is None and not r["new_entry_authority"]
    assert len(r["action_hashes"]) == 6
    calls = len(t.calls)
    assert enabled(make).reconcile_group_terminal() == final
    assert len(t.calls) == calls


def test_cancel_late_fill_reduces_successor_not_whole_initial_quantity(setup):
    make, _, t, _, flags = setup
    e = enabled(make)
    first.sell(e, t)
    canceled(e, t, flags, filled=2, late_filled=4)
    retry(e, t, flags)
    assert e._read("SELL_RUNNER", 2)["quantity"] == 2
    assert t.writes[-1]["payload"]["ord_qty"] == "2"


@pytest.mark.parametrize("cap", [0, -1, True, 1.0, 4])
def test_invalid_attempt_bounds(cap):
    with pytest.raises(ValueError):
        RunnerBounds(1000, 500, 2000, cap)


def test_more_attempts_require_independent_retry_validator(setup):
    make, _, t, _, _ = setup
    with pytest.raises(ValueError, match="approval_services"):
        make(bounds=RunnerBounds(1000, 500, 2000, 2))
    assert not t.calls
    assert RunnerBounds(1000, 500, 2000).to_payload() == {
        "sell_ttl_ms": 1000,
        "max_decision_age_ms": 500,
        "max_unprotected_ms": 2000,
    }


@pytest.mark.parametrize("attempt", [0, True, 1, 3, 4])
def test_cannot_skip_or_exceed_generation(setup, attempt):
    _, _, t, _, flags = setup
    e = prepared(setup)
    writes = len(t.writes)
    with pytest.raises(ValueError):
        retry(e, t, flags, attempt=attempt)
    assert len(t.writes) == writes


@pytest.mark.parametrize("approved", [False, None, 1])
def test_retry_validator_blocks_without_reservation(setup, approved):
    _, _, t, store, flags = setup
    e = prepared(setup, authorize_retry=lambda *args: approved)
    writes, saved = len(t.writes), store.writes
    with pytest.raises(PermissionError, match="fresh_retry_price"):
        retry(e, t, flags)
    assert len(t.writes) == writes and store.writes == saved


def test_changed_original_intent_or_quantity_fails_even_rehashed(setup):
    _, _, t, store, flags = setup
    e = prepared(setup)
    retry(e, t, flags)
    raw = store.records[e._key("SELL_RUNNER", 2)]
    raw["quantity"] += 1
    raw["canonical_sha256"] = canonical_sha256(raw)
    with pytest.raises(ValueError, match="predecessor_quantity"):
        e.poll_runner()


@pytest.mark.parametrize(
    "proof_field",
    ["confirmed_qty", "cancel_order_no", "source_contract", "receipt_sha256"],
)
def test_missing_or_forged_cancel_child_does_not_allow_retry(
    setup, monkeypatch, proof_field
):
    _, _, t, _, flags = setup
    e = prepared(setup)
    original = e._intent

    def broken(record):
        row = original(record)
        if row and row.get("terminal_cancel_reconciliation"):
            row = deepcopy(row)
            row["terminal_cancel_reconciliation"].pop(proof_field)
        return row

    monkeypatch.setattr(e, "_intent", broken)
    writes = len(t.writes)
    with pytest.raises(ValueError):
        retry(e, t, flags)
    assert len(t.writes) == writes


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_durable_action_save_failure_never_sends(setup, failure):
    _, _, t, store, flags = setup
    e = prepared(setup)
    writes = len(t.writes)
    store.fail = failure
    with pytest.raises((ValueError, OSError)):
        retry(e, t, flags)
    assert len(t.writes) == writes


def test_ambiguous_retry_ack_cannot_be_resent_or_skipped(setup):
    make, _, t, _, flags = setup
    e = prepared(setup)
    t.crash = True
    action, result = retry(e, t, flags)
    assert result["status"] == "recovery_required"
    writes = len(t.writes)
    t.crash = False
    assert enabled(make).retry_runner(action, attempt_no=2) == result
    with pytest.raises(ValueError):
        retry(e, t, flags, attempt=3)
    assert len(t.writes) == writes


def test_unknown_position_intent_cannot_be_adopted_as_runner(setup):
    _, adapter, t, _, flags = setup
    e = prepared(setup)
    predecessor, qty = e._retry_predecessor(2)
    adapter.registry.reserve(
        context=replace(
            adapter.context, client_intent_id=e._client("SELL_RUNNER", predecessor)
        ),
        symbol=adapter.symbol,
        side="SELL",
        quantity=qty,
        route="SOR",
        order_date=DATE,
        authority_policy_id="machine_adaptive_exit_v1",
        authority_policy_hash=adapter.policy_hash,
    )
    writes = len(t.writes)
    with pytest.raises(ValueError, match="census_conflict"):
        retry(e, t, flags)
    assert len(t.writes) == writes


def test_attempt_exhaustion_keeps_residual_manager_and_quantity(setup):
    _, _, t, _, flags = setup
    e = prepared(setup, bounds=RunnerBounds(1000, 500, 2000, 2))
    retry(e, t, flags)
    canceled(e, t, flags, attempt=2, filled=1)
    r = e.poll_runner()
    assert r["runner_remaining_qty"] == 3
    assert r["attempts_exhausted"] and r["manager_must_remain"]
    assert not r["group_terminal"] and r["realized_pnl"] is None
    writes = len(t.writes)
    with pytest.raises(ValueError, match="outside_approved"):
        retry(e, t, flags, attempt=3)
    assert len(t.writes) == writes


@pytest.mark.parametrize("flag", ["lock", "approval", "custody", "action_allowed"])
def test_retry_rechecks_all_owner_guards(setup, flag):
    _, _, t, _, flags = setup
    e = prepared(setup)
    flags[flag] = False
    writes = len(t.writes)
    with pytest.raises(PermissionError):
        retry(e, t, flags)
    assert len(t.writes) == writes


def test_fresh_retry_guard_rechecks_after_registry_reservation(setup, monkeypatch):
    make, adapter, t, _, flags = setup
    flags["retry_allowed"] = True

    def validate(*args):
        return flags["retry_allowed"]

    e = prepared(setup, authorize_retry=validate)
    reserve = adapter.registry.reserve

    def delayed(**kwargs):
        result = reserve(**kwargs)
        flags["retry_allowed"] = False
        return result

    monkeypatch.setattr(adapter.registry, "reserve", delayed)
    writes = len(t.writes)
    with pytest.raises(PermissionError, match="fresh_retry_price"):
        retry(e, t, flags)
    record = e._read("SELL_RUNNER", 2)
    assert e._intent(record)["state"] == "INTENT_RESERVED"
    flags["retry_allowed"] = True
    assert (
        enabled(make, authorize_retry=validate).retry_runner(
            first.GroupAction(**record["action"]), attempt_no=2
        )["status"]
        == "recovery_required"
    )
    assert len(t.writes) == writes


def test_stale_action_cannot_use_a_fresh_terminal_proof_as_price(setup):
    _, _, t, _, flags = setup
    e = prepared(setup)
    writes = len(t.writes)
    action = first.action("SELL_RUNNER", now=flags["now"] - 501, price=70300)
    with pytest.raises(PermissionError, match="fresh_approved_action"):
        e.retry_runner(action, attempt_no=2)
    assert len(t.writes) == writes


def test_cap_cannot_change_after_first_frozen_action(setup):
    make, _, t, _, _ = setup
    prepared(setup)
    with pytest.raises(ValueError, match="saved_action_invalid"):
        enabled(make, bounds=RunnerBounds(1000, 500, 2000, 2)).poll_runner()


def test_book_enabled_retry_preserves_original_exit_and_requires_fresh_validator(
    tmp_path, monkeypatch
):
    from src.tests import test_machine_adaptive_exit_group_decision as pre
    from src.tests import test_machine_adaptive_exit_group_trailing as trailing

    make, t, store, flags = pre.setup.__wrapped__(tmp_path, monkeypatch)
    observed = []

    def validate(binding, original, record, now):
        observed.append((original, record))
        return (
            record["action"]["source_hash"] == "d" * 64
            and record["action"]["limit_price"] == 70300
        )

    def make_enabled():
        return enabled(make, authorize_retry=validate)

    e = trailing.release(make_enabled, t, flags)
    trailing.sell_decision(e, flags)
    trailing.ack(t)
    e.sell_decided_released()
    first_record = e._read("SELL_RUNNER")
    book_before = deepcopy(store.records[e.released_book.key])
    canceled(e, t, flags)
    action2, _ = retry(make_enabled(), t, flags)
    assert all(original == first_record for original, _ in observed)
    assert store.records[e.released_book.key] == book_before
    assert (
        e._read("SELL_RUNNER", 2)["original_sell_action_hash"]
        == first_record["canonical_sha256"]
    )
    # A new raw price cannot rewrite the immutable second-generation action.
    with pytest.raises(ValueError, match="immutable"):
        e.retry_runner(replace(action2, limit_price=70200), attempt_no=2)
