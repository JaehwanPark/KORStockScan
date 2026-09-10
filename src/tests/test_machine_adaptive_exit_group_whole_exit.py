"""Whole-group original EXIT, actual widget loop and fake-only broker journal."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.tests import test_machine_adaptive_exit_group_owner_loop as owner
from src.tests.test_machine_adaptive_exit_broker import (
    DATE,
    NOW,
    TARGET,
    detail,
    current,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.group_owner_loop import SESSION_KEY
from src.trading.order.adaptive_exit.group_whole_exit import SCHEMA, WholeExitServices
from src.trading.order.adaptive_exit.group_settlement import closed_census


@pytest.fixture
def setup(tmp_path, monkeypatch):
    machine, new, wire, flags = owner.setup.__wrapped__(tmp_path, monkeypatch)
    flags.update(request=True, whole_action=True)

    def enable(m):
        m.adaptive_exit_services = replace(
            m.adaptive_exit_services,
            group=replace(
                m.adaptive_exit_services.group,
                authorize_retry=lambda *a: flags["whole_action"],
                whole_exit=WholeExitServices(
                    authorize_request=lambda *a: flags["request"],
                    authorize_action=lambda *a: flags["whole_action"],
                    action_loader=lambda s, r, k, q, n: {
                        "source_hash": "a" * 64,
                        "observed_at_ms": n,
                        "limit_price": 70300 if k == "NEW" else None,
                    },
                ),
            ),
        )
        return m

    enable(machine)
    return machine, lambda: enable(new()), wire, flags


def force(machine):
    machine._state["symbols"]["005930"]["entry_execution_policy"] = {
        "policy_id": "test-frozen-policy",
        "force_flat_at_session_end": True,
        "force_exit_time": "13:00",
        "source_final_exit_action": "sell_own_filled_quantity",
    }


def ack(wire, number, parent=None, quantity=None):
    wire.write_body = {"return_code": 0, "ord_no": number, "dmst_stex_tp": "SOR"}
    if parent:
        wire.write_body.update(base_orig_ord_no=parent, cncl_qty=str(quantity))


def root(wire, number, quantity, filled, remaining):
    wire.detailed = [r for r in wire.detailed if r["ord_no"] != number]
    wire.detailed.append(
        detail(
            ord_no=number,
            ord_qty=str(quantity),
            cntr_qty=str(filled),
            ord_remnq=str(remaining),
        )
    )
    wire.current = [r for r in wire.current if r["ord_no"] != number]
    if remaining:
        wire.current.append(
            current(
                ord_no=number,
                ord_qty=str(quantity),
                cntr_qty=str(filled),
                oso_qty=str(remaining),
            )
        )


def canceled(wire, number, parent, requested, confirmed_qty):
    wire.detailed.append(
        detail(
            ord_no=number,
            ori_ord=parent,
            ord_qty=str(requested),
            cntr_qty="0",
            ord_remnq="0",
            cnfm_qty=str(confirmed_qty),
            cnfm_tm="13:00:00",
        )
    )


def journal(state):
    return next(
        r for r in state[SESSION_KEY]["records"].values() if r["schema"] == SCHEMA
    )


def first_sell(setup):
    machine, new, wire, flags = setup
    force(machine)
    ack(wire, "0000003", TARGET.order_no, 10)
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["cncl_qty"] == "10"
    root(wire, TARGET.order_no, 10, 1, 0)
    canceled(wire, "0000003", TARGET.order_no, 10, 9)
    assert (
        owner.step(new(), flags, 1)["adaptive_exit_loop_status"]
        == "whole_exit_cancel_reconciliation"
    )
    ack(wire, "0000005")
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"] == {
        "dmst_stex_tp": "SOR",
        "stk_cd": "005930",
        "ord_qty": "9",
        "ord_uv": "70300",
        "trde_tp": "0",
    }
    return new()


def test_whole_target_original_policy_cancel_late_fill_sell_archives_once(setup):
    machine, new, wire, flags = setup
    machine = first_sell(setup)
    root(wire, "0000005", 9, 9, 0)
    assert (
        owner.step(machine, flags, 1)["adaptive_exit_loop_status"]
        == "whole_exit_root_reconciled"
    )
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "execution_terminal_handoff_completed"
    assert SESSION_KEY not in state and state["completed_entry_count"] == 3
    receipt = state["adaptive_exit_history"][-1]["group_terminal"]
    assert [r["filled_qty"] for r in receipt["orders"]] == [1, 9]
    assert (
        receipt["realized_net_profit_krw"] is None
        and receipt["new_entry_authority"] is False
    )
    assert len(wire.writes) == 2
    assert owner.step(new(), flags, 1)["completed_entry_count"] == 3
    assert len(wire.writes) == 2


def test_partial_runner_and_kept_target_each_cancel_before_one_pooled_residual(setup):
    machine, new, wire, flags = setup
    owner.sell(setup)
    force(machine)
    # Original target retained three shares after its original F1/partial C6.
    root(wire, "0000005", 6, 2, 4)
    ack(wire, "0000006", TARGET.order_no, 3)
    state = owner.step(machine, flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["cncl_qty"] == "3"
    root(wire, TARGET.order_no, 10, 2, 0)
    canceled(wire, "0000006", TARGET.order_no, 3, 2)
    owner.step(new(), flags, 1)
    ack(wire, "0000007", "0000005", 4)
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    root(wire, "0000005", 6, 3, 0)
    canceled(wire, "0000007", "0000005", 4, 3)
    owner.step(new(), flags, 1)
    ack(wire, "0000008")
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["ord_qty"] == "5"
    root(wire, "0000008", 5, 5, 0)
    owner.step(new(), flags, 1)
    state = owner.step(new(), flags, 1)
    assert SESSION_KEY not in state and state["completed_entry_count"] == 3
    receipt = state["adaptive_exit_history"][-1]["group_terminal"]
    assert [r["filled_qty"] for r in receipt["orders"]] == [2, 3, 5]
    assert len(receipt["cancel_proofs"]) == 3
    assert len(wire.writes) == 5


@pytest.mark.parametrize(
    "flag", ["request", "whole_action", "guard", "approval", "lock"]
)
def test_missing_explicit_whole_authority_never_writes(setup, flag):
    machine, _, wire, flags = setup
    force(machine)
    flags[flag] = False
    owner.step(machine, flags)
    assert not wire.writes


@pytest.mark.parametrize("mode", ["timeout", "rejected", "bad_ack", "unconfirmed"])
def test_cancel_uncertainty_is_sticky_no_duplicate_or_replacement(setup, mode):
    machine, new, wire, flags = setup
    force(machine)
    ack(wire, "0000003", TARGET.order_no, 10)
    if mode == "timeout":
        wire.crash = True
    elif mode == "rejected":
        wire.write_body = {"return_code": 1700}
    elif mode == "bad_ack":
        wire.write_body["cncl_qty"] = "9"
    owner.step(machine, flags)
    wire.crash = False
    for _ in range(3):
        state = owner.step(new(), flags, 1)
        assert state["entry_episode_open"] is True and SESSION_KEY in state
    assert len(wire.writes) == 1


def test_declared_ttl_cancels_once_but_exhausted_residual_is_not_flat(setup):
    machine, new, wire, flags = setup
    first_sell(setup)
    root(wire, "0000005", 9, 4, 5)
    assert (
        owner.step(new(), flags, 10)["adaptive_exit_loop_status"]
        == "whole_exit_sell_working"
    )
    ack(wire, "0000006", "0000005", 5)
    assert (
        owner.step(new(), flags, 1000)["adaptive_exit_loop_status"]
        == "whole_exit_order_bound"
    )
    root(wire, "0000005", 9, 5, 0)
    canceled(wire, "0000006", "0000005", 5, 4)
    owner.step(new(), flags, 1)
    state = owner.step(new(), flags, 1)
    assert (
        state["adaptive_exit_loop_status"] == "whole_exit_residual_attempts_exhausted"
    )
    assert state["entry_episode_open"] is True and len(wire.writes) == 3


def test_source_final_exit_survives_disappearing_source_and_cannot_promote_observe_only(
    setup, monkeypatch
):
    machine, new, wire, flags = setup
    state = machine._state["symbols"]["005930"]
    state["entry_execution_policy"] = {
        "policy_id": "test-policy",
        "source_final_exit_action": "sell_own_filled_quantity",
    }
    now = datetime.fromtimestamp(NOW / 1000, owner.widget.KST)
    monkeypatch.setattr(machine, "_exit_signal", lambda *a: "source-exit-id")
    monkeypatch.setattr(machine, "_snapshot_time", lambda *a: now)
    monkeypatch.setattr(machine, "_route", lambda *a: "KRX")
    spec = SimpleNamespace(
        code="005930",
        contract=SimpleNamespace(session_context=lambda n: SimpleNamespace(name="KRX")),
    )
    ack(wire, "0000003", TARGET.order_no, 10)
    machine.process_payload(spec, {"test_source": 1}, now)
    assert journal(state)["request"]["reason"] == "source_final_exit"
    state = owner.step(new(), flags, 1)
    assert (
        journal(state)["request"]["signal_id"] == "source-exit-id"
        and len(wire.writes) == 1
    )


def test_whole_journal_cannot_fall_back_to_runner_when_services_disappear(setup):
    machine, new, wire, flags = setup
    force(machine)
    ack(wire, "0000003", TARGET.order_no, 10)
    owner.step(machine, flags)
    machine = new()
    machine.adaptive_exit_services = replace(
        machine.adaptive_exit_services,
        group=replace(machine.adaptive_exit_services.group, whole_exit=None),
    )
    assert SESSION_KEY in owner.step(machine, flags, 1)
    assert len(wire.writes) == 1


@pytest.mark.parametrize(
    "failure", ["policy", "signal", "unknown_intent", "census_cancel_proof"]
)
def test_full_exit_never_accepts_rebound_policy_or_foreign_census(setup, failure):
    machine, new, wire, flags = setup
    machine = first_sell(setup)
    state = machine._state["symbols"]["005930"]
    if failure == "policy":
        state["entry_execution_policy"]["policy_id"] = "other"
    elif failure == "signal":
        state["entry_signal_id"] = "other"
    elif failure == "unknown_intent":
        context = machine._owner_context_from_order(state["orders"][-1])
        machine.owner_registry.reserve(
            context=replace(context, client_intent_id="unknown"),
            symbol="005930",
            side="BUY",
            quantity=1,
            route="SOR",
            order_date=DATE,
        )
    else:
        context = machine._owner_context_from_order(state["orders"][-1])
        rows = machine.owner_registry.position_intents(context=context, symbol="005930")
        rows = [r for r in rows if r["broker_order_no"] != "0000005"]
        damaged = deepcopy(rows)
        next(r for r in damaged if r["action"] == "CANCEL")[
            "terminal_cancel_reconciliation"
        ]["confirmed_qty"] = 0
        with pytest.raises(ValueError):
            closed_census(damaged)
        return
    count = len(wire.writes)
    assert SESSION_KEY in owner.step(machine, flags, 1)
    assert len(wire.writes) == count


def test_noop_owner_save_cannot_dispatch_whole_cancel(setup, monkeypatch):
    machine, _, wire, flags = setup
    force(machine)
    monkeypatch.setattr(machine, "_save", lambda: None)
    with pytest.raises(OSError, match="readback_missing"):
        owner.step(machine, flags)
    assert not wire.writes


def test_approved_whole_residual_generation_two_uses_its_own_terminal_predecessor(
    setup,
):
    machine, new, wire, flags = setup
    raw = machine._state["symbols"]["005930"][SESSION_KEY]
    raw["definition"]["bounds"]["maximum_sell_attempts"] = 2
    raw["canonical_sha256"] = canonical_sha256(raw)
    first_sell(setup)
    root(wire, "0000005", 9, 4, 5)
    ack(wire, "0000006", "0000005", 5)
    owner.step(new(), flags, 1000)
    root(wire, "0000005", 9, 5, 0)
    canceled(wire, "0000006", "0000005", 5, 4)
    owner.step(new(), flags, 1)
    ack(wire, "0000007")
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["ord_qty"] == "4"
    action = journal(state)["actions"][-1]
    assert action["generation"] == 2 and action["predecessor"]["order_no"] == "0000005"
    root(wire, "0000007", 4, 4, 0)
    owner.step(new(), flags, 1)
    state = owner.step(new(), flags, 1)
    assert SESSION_KEY not in state and state["completed_entry_count"] == 3
    assert [
        r["filled_qty"]
        for r in state["adaptive_exit_history"][-1]["group_terminal"]["orders"]
    ] == [1, 5, 4]
    assert len(wire.writes) == 4


def test_positive_partial_cancel_pending_at_whole_claim_is_reconciled_without_resend(
    setup,
):
    machine, new, wire, flags = setup
    owner.step(machine, flags)  # original runner's partial request, not terminal
    force(machine)
    from src.tests.test_machine_adaptive_exit_group_runtime import confirmed

    confirmed(wire)
    state = owner.step(machine, flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_cancel_reconciliation"
    assert len(wire.writes) == 1
    ack(wire, "0000005", TARGET.order_no, 3)
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert wire.writes[-1]["payload"]["cncl_qty"] == "3" and len(wire.writes) == 2


def test_closed_original_target_needs_no_extra_sell_or_runner_allocation(setup):
    machine, new, wire, flags = setup
    force(machine)
    root(wire, TARGET.order_no, 10, 10, 0)
    assert (
        owner.step(machine, flags)["adaptive_exit_loop_status"]
        == "whole_exit_root_reconciled"
    )
    state = owner.step(new(), flags, 1)
    assert SESSION_KEY not in state and len(wire.writes) == 0
    assert state["completed_entry_count"] == 3


def test_whole_clock_gap_blocks_cancel_but_original_target_can_finish(setup):
    machine, new, wire, flags = setup
    force(machine)
    flags["halt_ms"] = None
    state = owner.step(machine, flags)
    assert state["adaptive_exit_loop_status"] == "group_clock_source_gap"
    assert not wire.writes and SESSION_KEY in state
    root(wire, TARGET.order_no, 10, 10, 0)
    owner.step(new(), flags, 1)
    state = owner.step(new(), flags, 1)
    assert SESSION_KEY not in state and not wire.writes
    assert state["completed_entry_count"] == 3


def test_whole_clock_gap_blocks_new_sell_after_confirmed_cancel(setup):
    machine, new, wire, flags = setup
    force(machine)
    ack(wire, "0000003", TARGET.order_no, 10)
    owner.step(machine, flags)
    flags["halt_ms"] = None
    root(wire, TARGET.order_no, 10, 1, 0)
    canceled(wire, "0000003", TARGET.order_no, 10, 9)
    assert (
        owner.step(new(), flags, 1)["adaptive_exit_loop_status"]
        == "whole_exit_cancel_reconciliation"
    )
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "group_clock_source_gap"
    assert SESSION_KEY in state and len(wire.writes) == 1
    flags["halt_ms"] = 0
    ack(wire, "0000005")
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_order_bound"
    assert len(wire.writes) == 2


def test_cancel_deadline_does_not_issue_repeated_broker_reads(setup):
    machine, new, wire, flags = setup
    force(machine)
    ack(wire, "0000003", TARGET.order_no, 10)
    owner.step(machine, flags)
    before = len(wire.calls)
    for _ in range(2):
        state = owner.step(new(), flags, 2001)
        assert (
            state["adaptive_exit_loop_status"] == "whole_exit_cancel_deadline_exceeded"
        )
    assert len(wire.calls) == before


def test_post_reservation_authority_loss_leaves_reserved_intent_and_no_wire(setup):
    machine, new, wire, flags = setup
    force(machine)
    current_services = machine.adaptive_exit_services

    def guard(binding, request, action, now):
        context = machine._owner_context_from_order(
            machine._state["symbols"]["005930"]["orders"][-1]
        )
        rows = machine.owner_registry.position_intents(context=context, symbol="005930")
        return not any(r["state"] == "INTENT_RESERVED" for r in rows)

    machine.adaptive_exit_services = replace(
        current_services,
        group=replace(
            current_services.group,
            whole_exit=replace(
                current_services.group.whole_exit, authorize_action=guard
            ),
        ),
    )
    state = owner.step(machine, flags)
    assert (
        state["adaptive_exit_loop_status"]
        == "whole_exit_fresh_price_depth_and_safety_required"
    )
    assert not wire.writes
    state = owner.step(new(), flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_unresolved_intent_recovery"
    assert not wire.writes


def test_fresh_action_expiring_inside_validator_cannot_write(setup):
    machine, _, wire, flags = setup
    force(machine)
    services = machine.adaptive_exit_services

    def slow(*args):
        flags["now"] += 501
        return True

    machine.adaptive_exit_services = replace(
        services,
        group=replace(
            services.group,
            whole_exit=replace(services.group.whole_exit, authorize_action=slow),
        ),
    )
    state = owner.step(machine, flags)
    assert (
        state["adaptive_exit_loop_status"] == "whole_exit_action_stale_after_validation"
    )
    assert not wire.writes


def test_rehashed_generation_cannot_skip_the_first_pooled_sell(setup):
    machine, new, wire, flags = setup
    first_sell(setup)
    machine = new()
    state = machine._state["symbols"]["005930"]
    raw = journal(state)
    raw["actions"][-1]["generation"] = 2
    raw["actions"][-1]["canonical_sha256"] = canonical_sha256(raw["actions"][-1])
    raw["canonical_sha256"] = canonical_sha256(raw)
    state[SESSION_KEY]["canonical_sha256"] = canonical_sha256(state[SESSION_KEY])
    before = len(wire.calls)
    state = owner.step(machine, flags, 1)
    assert "whole_exit_action_invalid" in state["adaptive_exit_loop_status"]
    assert len(wire.calls) == before


def test_conflicting_old_terminal_cannot_be_hidden_by_whole_journal(setup):
    machine, new, wire, flags = setup
    first_sell(setup)
    machine = new()
    state = machine._state["symbols"]["005930"]
    raw = state[SESSION_KEY]
    # Exact coordinator slot is account + dated original target, not a new ID.
    from src.trading.order.adaptive_exit.group_owner_loop import GroupOwnerSession
    from dataclasses import asdict

    session = GroupOwnerSession.from_payload(raw)
    account = canonical_sha256({"account": "group-owner-test-account"})
    slot = canonical_sha256(
        {"account": account, "target": asdict(session.group.target)}
    )
    key = canonical_sha256({"group_slot": slot, "execution_kind": "GROUP_TERMINAL"})
    extra = {"schema": "competing"}
    extra["canonical_sha256"] = canonical_sha256(extra)
    raw["records"][key] = extra
    raw["canonical_sha256"] = canonical_sha256(raw)
    before = len(wire.calls)
    state = owner.step(machine, flags, 1)
    assert state["adaptive_exit_loop_status"] == "whole_exit_competing_terminal_journal"
    assert len(wire.calls) == before
