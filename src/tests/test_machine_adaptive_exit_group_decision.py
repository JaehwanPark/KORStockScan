from copy import deepcopy
from dataclasses import asdict, replace

import pytest

from src.tests import test_machine_adaptive_exit_group_runtime as group_tests
from src.tests.test_machine_adaptive_exit_broker import NOW, DATE
from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    canonical_sha256,
    make_policy_payload,
)
from src.trading.order.adaptive_exit.broker import RegisteredSellAdapter
from src.trading.order.adaptive_exit.group_decision import (
    GroupDecisionBook,
    evaluate_group_exit,
    validate_group_decision,
)
from src.trading.order.adaptive_exit.group_execution import (
    GroupAction,
    GroupRunnerExecutor,
    RunnerBounds,
)
from src.trading.order.adaptive_exit.models import (
    Clock,
    DecisionState,
    Position,
    Snapshot,
)
from src.trading.order.adaptive_exit.reducer import OrderKey


def policy_for(group, runners=("runner_lot",), **changes):
    return make_policy_payload(
        scope_key=group.scope.key,
        parameters={
            "mode": "fast_partial_trailing",
            "soft_sec": 60,
            "extension_sec": 30,
            "minimum_progress": 0.4,
            "minimum_improvement_bps": 2,
            "hard_wall_sec": None,
            "loss_budget_pct": 0.3,
            "max_quote_age_ms": 500,
            "max_observation_gap_ms": 2000,
            "trail": {
                "fast_sec": 20,
                "min_progress": 0.4,
                "gap_ticks": 1,
                "transition_buffer_ticks": 1,
                "minimum_net_cushion_pct": 0.02,
            },
            "runner_lot_ids": runners,
            **changes,
        },
    )


@pytest.fixture
def setup(tmp_path, monkeypatch):
    make_coordinator, original, transport, store, flags = group_tests.setup.__wrapped__(
        tmp_path, monkeypatch
    )
    group = make_coordinator().group
    policy = policy_for(group)
    allocation = replace(
        make_coordinator().allocation, policy_hash=policy["policy_hash"]
    )
    flags["action_allowed"] = True

    def make(**changes):
        def factory(guard):
            adapter = RegisteredSellAdapter(
                post=transport,
                registry=original.registry,
                context=original.context,
                symbol=original.symbol,
                routes=original.routes,
                policy_hash=policy["policy_hash"],
                maximum_quantity=original.maximum_quantity,
                require_write_authority=lambda: None,
                write_guard=guard,
                now_ms=lambda: flags["now"],
            )
            return make_coordinator(adapter=adapter, allocation=allocation)

        return GroupRunnerExecutor(
            **{
                "coordinator_factory": factory,
                "bounds": RunnerBounds(1000, 500, 2000),
                "execution_approval_receipt_hash": "e" * 64,
                "authorize_action": lambda binding, record, now: flags[
                    "action_allowed"
                ],
                "decision_policy": policy,
                **changes,
            }
        )

    return make, transport, store, flags


def observations(c, now=NOW, seq=1, bid=70400):
    frozen = c.freeze()
    positions, snapshots, clocks = {}, {}, {}
    balances = {
        r["lot_id"]: r["book_open_qty"]
        for r in c.allocation.balances(c.group, frozen["initial_filled_qty"])
    }
    for lot, _, _, first, entry in c.group.lots:
        if not balances[lot]:
            continue
        positions[lot] = Position(
            c.group.scope.owner,
            c.group.scope.key,
            c.group.episode_id,
            lot,
            "position-" + lot,
            first,
            balances[lot],
            entry,
            c.group.target_price,
            0.23,
            "c" * 64,
            100,
        )
        snapshots[lot] = Snapshot(
            now,
            now,
            "epoch",
            seq,
            "d" * 64,
            c.group.scope.key,
            "position-" + lot,
            70600,
            ((bid, 20),),
            True,
            5,
            seq,
        )
        clocks[lot] = Clock(now, 0)
    return {"positions": positions, "snapshots": snapshots, "clocks": clocks}


def pure_inputs(c):
    obs = observations(c)
    frozen = c.freeze()
    return {
        "target_filled_qty": frozen["initial_filled_qty"],
        "freeze_source_hash": frozen["freeze_source_hash"],
        "frozen_at_ms": frozen["frozen_at_ms"],
        "lots": {
            lot: {
                "position": asdict(p),
                "snapshot": asdict(obs["snapshots"][lot]),
                "clock": asdict(obs["clocks"][lot]),
                "previous_state": asdict(
                    DecisionState(
                        c.allocation.policy_hash,
                        p.position_epoch,
                        p.first_fill_at_ms,
                        p.open_qty,
                    )
                ),
            }
            for lot, p in obs["positions"].items()
        },
    }


def evaluate(c, inputs, policy=None, allocation=None, group=None):
    return evaluate_group_exit(
        group=group or c.group,
        allocation=allocation or c.allocation,
        policy_payload=policy or policy_for(c.group),
        inputs=inputs,
    )


def test_receipt_to_first_partial_cancel_uses_existing_guard_and_no_trail_arm(setup):
    make, transport, store, _ = setup
    e = make()
    receipt = e.decision_book.observe(**observations(e.coordinator))
    assert receipt["status"] == "REQUEST_RUNNER_RELEASE"
    assert receipt["lot_decisions"]["runner_lot"]["action"] == "REQUEST_TRAIL_ARM"
    assert receipt["release_quantity"] == 6
    assert receipt["authority"] == AUTHORITY
    assert receipt["realized_pnl"] is None and not receipt["group_terminal"]
    assert not receipt["trail_armed"]
    assert not receipt["next_states"]["runner_lot"]["trail_active"]
    assert not transport.writes
    assert make().decision_book.release_action() == e.decision_book.release_action()
    assert e.request_decided_release()["status"] == "order_bound"
    assert [r["api_id"] for r in transport.writes] == ["kt10003"]
    assert transport.writes[0]["payload"]["cncl_qty"] == "6"
    assert (
        store.records[e._key("RELEASE_RUNNER")]["action"]["decision_receipt_hash"]
        == receipt["canonical_sha256"]
    )
    assert make().request_decided_release()["status"] == "order_bound"
    assert len(transport.writes) == 1
    with pytest.raises(ValueError, match="already_committed"):
        e.decision_book.observe(**observations(e.coordinator))


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_pending_save_failure_never_submits_and_poisoned_instance_cannot_release(
    setup, failure
):
    make, transport, store, _ = setup
    e = make()
    obs = observations(e.coordinator)
    e.decision_book.observe(**obs)
    store.fail = failure
    with pytest.raises((ValueError, OSError)):
        e.decision_book.observe(**obs)
    with pytest.raises(ValueError, match="durably_complete"):
        e.request_decided_release()
    assert not transport.writes


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
def test_result_save_failure_leaves_veto_or_exact_committed_result_no_order(
    setup, failure
):
    make, transport, store, _ = setup
    e = make()
    obs = observations(e.coordinator)
    save = e.coordinator.save_record
    calls = []

    def faulty(key, expected, raw):
        calls.append(raw)
        if key == e.decision_book.key and raw["veto"] is None:
            store.fail = failure
        return save(key, expected, raw)

    e.coordinator.save_record = faulty
    with pytest.raises((ValueError, OSError)):
        e.decision_book.observe(**obs)
    assert not transport.writes
    with pytest.raises(ValueError, match="durably_complete"):
        e.request_decided_release()
    if failure != "after":
        with pytest.raises(ValueError, match="latest_decision"):
            make().request_decided_release()


@pytest.mark.parametrize("bad", ["missing", "cost", "nan", "future", "epoch"])
def test_invalid_new_observation_veto_survives_restart(setup, bad):
    make, transport, _, flags = setup
    e = make()
    e.decision_book.observe(**observations(e.coordinator))
    flags["now"] += 1
    obs = observations(e.coordinator, flags["now"], 2)
    if bad == "missing":
        del obs["positions"]["target_lot"]
    elif bad == "cost":
        obs["positions"]["runner_lot"] = replace(
            obs["positions"]["runner_lot"], cost_contract_hash="e" * 64
        )
    elif bad == "nan":
        obs["snapshots"]["runner_lot"] = replace(
            obs["snapshots"]["runner_lot"], improvement_bps=float("nan")
        )
    elif bad == "future":
        obs["clocks"]["runner_lot"] = Clock(flags["now"] + 1, 0)
    else:
        obs["snapshots"]["runner_lot"] = replace(
            obs["snapshots"]["runner_lot"], source_epoch="another"
        )
    with pytest.raises(ValueError):
        e.decision_book.observe(**obs)
    with pytest.raises(ValueError, match="latest_decision"):
        make().request_decided_release()
    assert not transport.writes


def test_new_keep_target_and_duplicate_sequence_veto_old_action(setup):
    make, transport, _, flags = setup
    e = make()
    old = e.decision_book.observe(**observations(e.coordinator))
    flags["now"] += 1
    obs = observations(e.coordinator, flags["now"], 2, 70100)
    new = e.decision_book.observe(**obs)
    assert new["status"] == "KEEP_TARGET"
    with pytest.raises(ValueError, match="latest_decision"):
        e.request_release(
            GroupAction("RELEASE_RUNNER", old["canonical_sha256"], "d" * 64, NOW, None)
        )
    assert e.decision_book.observe(**obs)["status"] == "SOURCE_GAP"
    assert not transport.writes


@pytest.mark.parametrize("gate", ["action_allowed", "lock", "approval", "custody"])
def test_real_authority_callback_is_still_required(setup, gate):
    make, transport, _, flags = setup
    e = make()
    e.decision_book.observe(**observations(e.coordinator))
    flags[gate] = False
    with pytest.raises(PermissionError):
        e.request_decided_release()
    assert not transport.writes


def test_stale_action_and_hash_only_forgery_are_rejected(setup):
    make, transport, _, flags = setup
    e = make()
    e.decision_book.observe(**observations(e.coordinator))
    with pytest.raises(ValueError, match="latest_recomputed"):
        e.request_release(GroupAction("RELEASE_RUNNER", "e" * 64, "d" * 64, NOW, None))
    flags["now"] += 501
    with pytest.raises(ValueError, match="quote_now_stale"):
        e.request_decided_release()
    assert not transport.writes


def test_latest_receipt_checked_after_registry_reservation(setup, monkeypatch):
    make, transport, store, _ = setup
    e = make()
    e.decision_book.observe(**observations(e.coordinator))
    reserve = e.coordinator.adapter.registry.reserve

    def invalidate(**kwargs):
        result = reserve(**kwargs)
        raw = store.records[e.decision_book.key]
        raw["veto"] = "observation_pending_or_invalid"
        raw["canonical_sha256"] = canonical_sha256(raw)
        return result

    monkeypatch.setattr(e.coordinator.adapter.registry, "reserve", invalidate)
    with pytest.raises(ValueError, match="latest_decision"):
        e.request_decided_release()
    assert not transport.writes
    assert e._intent(e._read("RELEASE_RUNNER"))["state"] == "INTENT_RESERVED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("release_quantity", 5),
        ("trail_armed", True),
        ("realized_pnl", 0),
        ("group_terminal", True),
        ("status", "KEEP_TARGET"),
        ("source_hash", "f" * 64),
    ],
)
def test_receipt_recompute_rejects_self_rehashed_forgery(setup, field, value):
    make, _, _, _ = setup
    e = make()
    receipt = evaluate(e.coordinator, pure_inputs(e.coordinator))
    receipt[field] = value
    receipt["canonical_sha256"] = canonical_sha256(receipt)
    with pytest.raises(ValueError, match="recomputed"):
        validate_group_decision(
            receipt,
            group=e.coordinator.group,
            allocation=e.coordinator.allocation,
            policy_payload=e.decision_book.policy_payload,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("open_qty", 5),
        ("first_fill_at_ms", NOW - 1000),
        ("owner_id", "widget"),
        ("scope_key", "wrong"),
        ("episode_id", "wrong"),
        ("lot_id", "wrong"),
        ("entry_price", 69900),
        ("original_target", 70600),
        ("cost_contract_hash", "bad"),
    ],
)
def test_exact_lot_identity_and_cost_binding(setup, field, value):
    make, _, _, _ = setup
    c = make().coordinator
    inputs = pure_inputs(c)
    inputs["lots"]["runner_lot"]["position"][field] = value
    with pytest.raises(ValueError, match="lot_identity"):
        evaluate(c, inputs)


@pytest.mark.parametrize(
    "levels",
    [
        None,
        [],
        [[70400, 0]],
        [[70400, True]],
        [[70400, 20], [70500, 1]],
        [[70600, 20]],
        [[70400, 20], ["bad", 1]],
        [[70400, 20], [70300]],
    ],
)
def test_whole_raw_depth_validation_including_unused_tail(setup, levels):
    make, _, _, _ = setup
    c = make().coordinator
    inputs = pure_inputs(c)
    for row in inputs["lots"].values():
        row["snapshot"]["bid_levels"] = levels
    receipt = evaluate(c, inputs)
    assert receipt["status"] == "SOURCE_GAP"
    assert receipt["release_quantity"] is None


def three_lots(c):
    group = replace(
        c.group,
        lots=(
            c.group.lots[0],
            ("runner_lot", OrderKey(DATE, "0000004"), 3, NOW - 5000, 70000.0),
            ("runner2", OrderKey(DATE, "0000007"), 3, NOW - 5000, 70000.0),
        ),
    )
    policy = policy_for(group, ("runner_lot", "runner2"))
    allocation = replace(
        c.allocation,
        group_hash=group.to_payload()["canonical_sha256"],
        policy_hash=policy["policy_hash"],
        runner_lot_ids=("runner_lot", "runner2"),
        lot_order=("runner_lot", "runner2", "target_lot"),
    )
    inputs = pure_inputs(c)
    r = inputs["lots"]["runner_lot"]
    r["position"]["open_qty"] = r["previous_state"]["open_qty"] = 3
    inputs["lots"]["runner2"] = deepcopy(r)
    r2 = inputs["lots"]["runner2"]
    r2["position"]["lot_id"] = "runner2"
    for row in inputs["lots"].values():
        row["previous_state"]["policy_hash"] = policy["policy_hash"]
    return group, allocation, policy, inputs


def test_shared_depth_not_reused_for_each_runner_and_no_vwap_limit(setup):
    make, _, _, _ = setup
    c = make().coordinator
    group, allocation, policy, inputs = three_lots(c)
    for row in inputs["lots"].values():
        row["snapshot"]["bid_levels"] = [[70400, 3], [70300, 3]]
    receipt = evaluate(c, inputs, policy, allocation, group)
    assert receipt["lot_decisions"]["runner_lot"]["executable_bid"] == 70400
    assert receipt["lot_decisions"]["runner2"]["executable_bid"] == 70300
    assert receipt["status"] == "REQUEST_RUNNER_RELEASE"
    assert "limit_price" not in receipt
    for row in inputs["lots"].values():
        row["snapshot"]["bid_levels"] = [[70400, 3], [70300, 2]]
    short = evaluate(c, inputs, policy, allocation, group)
    assert short["status"] == "SOURCE_GAP" and short["release_quantity"] is None


def test_mixed_subset_and_whole_target_requests_not_silently_kept_or_released(setup):
    make, _, _, _ = setup
    c = make().coordinator
    group, allocation, policy, inputs = three_lots(c)
    inputs["lots"]["runner2"]["snapshot"]["supportive"] = False
    assert (
        evaluate(c, inputs, policy, allocation, group)["status"]
        == "UNSUPPORTED_GROUP_EXIT_REQUIRES_OWNER_RECOVERY"
    )
    policy = policy_for(
        c.group,
        mode="time_progress_and_trailing",
        soft_sec=1,
        trail={
            "fast_sec": 1,
            "min_progress": 0.4,
            "gap_ticks": 1,
            "transition_buffer_ticks": 1,
            "minimum_net_cushion_pct": 0.02,
        },
    )
    inputs = pure_inputs(c)
    allocation = replace(c.allocation, policy_hash=policy["policy_hash"])
    for row in inputs["lots"].values():
        row["previous_state"]["policy_hash"] = policy["policy_hash"]
        row["snapshot"].update(
            supportive=False, improvement_bps=0, bid_levels=[[70100, 20]]
        )
    result = evaluate(c, inputs, policy, allocation)
    assert result["status"] == "UNSUPPORTED_GROUP_EXIT_REQUIRES_OWNER_RECOVERY"
    assert set(result["requested_lot_ids"]) == {"runner_lot", "target_lot"}


def test_one_extension_survives_restart_without_becoming_trail_state(setup):
    make, _, _, flags = setup
    e = make()
    c = e.coordinator
    policy = policy_for(
        c.group, runners=(), mode="time_progress_exit", trail=None, soft_sec=1
    )
    c.allocation = replace(c.allocation, policy_hash=policy["policy_hash"])
    # Construct a NEW coordinator before freezing, never mutate its frozen binding.
    factory = group_tests.GroupCoordinator
    c.adapter.policy_hash = policy["policy_hash"]
    c = factory(
        group=c.group,
        allocation=c.allocation,
        adapter=c.adapter,
        max_snapshot_age_ms=c.max_age,
        load_record=c.load_record,
        save_record=c.save_record,
        lock_held=c.lock_held,
        authorize_binding=c.authorize_binding,
        owner_guard=c.owner_guard,
    )
    book = GroupDecisionBook(coordinator=c, policy_payload=policy)
    first = book.observe(**observations(c))
    assert first["next_states"]["runner_lot"]["extensions"] == 1
    deadline = first["next_states"]["runner_lot"]["extension_until_active_ms"]
    flags["now"] += 1000
    resumed = GroupDecisionBook(coordinator=c, policy_payload=policy)
    second = resumed.observe(**observations(c, flags["now"], 2))
    state = second["next_states"]["runner_lot"]
    assert state["extensions"] == 1 and state["extension_until_active_ms"] == deadline
    assert not state["trail_active"] and state["high_water"] is None


def test_policy_content_hash_and_runner_set_must_match(setup):
    make, _, _, _ = setup
    c = make().coordinator
    policy = policy_for(c.group)
    policy["loss_budget_pct"] = 99
    with pytest.raises(ValueError, match="content_hash"):
        GroupDecisionBook(coordinator=c, policy_payload=policy)
    policy = policy_for(c.group, ("target_lot",))
    with pytest.raises(ValueError, match="policy_binding"):
        evaluate(c, pure_inputs(c), policy)


def test_quote_ages_during_registry_wait_even_when_decision_is_young(
    setup, monkeypatch
):
    make, transport, _, flags = setup
    e = make()
    obs = observations(e.coordinator)
    for lot, snapshot in obs["snapshots"].items():
        obs["snapshots"][lot] = replace(snapshot, quote_at_ms=NOW - 450)
    e.decision_book.observe(**obs)
    reserve = e.coordinator.adapter.registry.reserve

    def wait_at_save(**kwargs):
        result = reserve(**kwargs)
        flags["now"] += 100
        return result

    monkeypatch.setattr(e.coordinator.adapter.registry, "reserve", wait_at_save)
    with pytest.raises(ValueError, match="quote_now_stale"):
        e.request_decided_release()
    assert not transport.writes


@pytest.mark.parametrize(
    "bad",
    ["missing_book", "policy_drift", "book_swap", "future_state", "corrupt_state"],
)
def test_execution_binding_and_durable_book_rejections(setup, bad):
    make, transport, store, _ = setup
    e = make()
    e.decision_book.observe(**observations(e.coordinator))
    if bad == "missing_book":
        e.decision_book = None
    elif bad == "policy_drift":
        e.decision_book.policy_payload["loss_budget_pct"] = 9
    elif bad == "book_swap":
        e.decision_book = make().decision_book
    elif bad == "future_state":
        raw = store.records[e.decision_book.key]
        raw["receipt"]["observed_at_ms"] = NOW + 100
        raw["receipt"]["canonical_sha256"] = canonical_sha256(raw["receipt"])
        raw["canonical_sha256"] = canonical_sha256(raw)
    else:
        raw = store.records[e.decision_book.key]
        raw["receipt"]["next_states"]["runner_lot"]["extensions"] = 99
        raw["receipt"]["canonical_sha256"] = canonical_sha256(raw["receipt"])
        raw["canonical_sha256"] = canonical_sha256(raw)
    with pytest.raises(ValueError):
        e.request_decided_release()
    assert not transport.writes


def test_valid_source_recovers_veto_without_resetting_accepted_state(setup):
    make, _, _, flags = setup
    e = make()
    first = e.decision_book.observe(**observations(e.coordinator))
    flags["now"] += 100
    bad = observations(e.coordinator, flags["now"], 2)
    for lot, snapshot in bad["snapshots"].items():
        bad["snapshots"][lot] = replace(snapshot, supportive=None)
    gap = e.decision_book.observe(**bad)
    assert gap["status"] == "SOURCE_GAP"
    assert gap["next_states"] == first["next_states"]
    flags["now"] += 100
    good = make().decision_book.observe(**observations(e.coordinator, flags["now"], 3))
    assert good["status"] == "REQUEST_RUNNER_RELEASE"
    assert good["next_states"]["runner_lot"]["sequence"] == 3


@pytest.mark.parametrize("kind", ["epoch", "time", "sequence", "support", "depth"])
def test_partial_source_gap_does_not_advance_any_group_state(setup, kind):
    make, _, _, flags = setup
    e = make()
    first = e.decision_book.observe(**observations(e.coordinator))
    flags["now"] += 1
    obs = observations(e.coordinator, flags["now"], 2)
    for lot, snapshot in obs["snapshots"].items():
        changes = {
            "epoch": {"source_epoch": "changed"},
            "time": {"quote_at_ms": NOW - 1000},
            "sequence": {"sequence": 1},
            "support": {"supportive": None},
            "depth": {"bid_levels": ((70400, 4),)},
        }[kind]
        obs["snapshots"][lot] = replace(snapshot, **changes)
    result = e.decision_book.observe(**obs)
    assert result["status"] in {"SOURCE_GAP", "RECOVERY_REQUIRED"}
    assert result["next_states"] == first["next_states"]


@pytest.mark.parametrize("fill", range(10))
def test_frozen_book_fill_conservation_never_becomes_lot_broker_pnl(setup, fill):
    make, _, _, _ = setup
    c = make().coordinator
    inputs = pure_inputs(c)
    inputs["target_filled_qty"] = fill
    for row in c.allocation.balances(c.group, fill):
        lot, qty = row["lot_id"], row["book_open_qty"]
        if not qty:
            del inputs["lots"][lot]
        else:
            inputs["lots"][lot]["position"]["open_qty"] = qty
            inputs["lots"][lot]["previous_state"]["open_qty"] = qty
    result = evaluate(c, inputs)
    assert (
        sum(
            r["book_open_qty"] + r["target_book_filled_qty"]
            for r in result["book_lots"]
        )
        == 10
    )
    assert sum(r["target_book_filled_qty"] for r in result["book_lots"]) == fill
    expected = (
        "REQUEST_RUNNER_RELEASE"
        if fill < 4
        else "UNSUPPORTED_GROUP_EXIT_REQUIRES_OWNER_RECOVERY"
    )
    assert result["status"] == expected
    assert (
        result["actual_lot_fill_attribution"] is None and result["realized_pnl"] is None
    )


@pytest.mark.parametrize("owner", ["widget", "episode"])
def test_scope_generic_producer_keeps_owner_separate(setup, owner):
    make, _, _, _ = setup
    c = make().coordinator
    group = replace(c.group, scope=replace(c.group.scope, owner=owner))
    policy = policy_for(group)
    allocation = replace(
        c.allocation,
        group_hash=group.to_payload()["canonical_sha256"],
        policy_hash=policy["policy_hash"],
    )
    inputs = pure_inputs(c)
    for row in inputs["lots"].values():
        row["position"].update(owner_id=owner, scope_key=group.scope.key)
        row["snapshot"]["scope_key"] = group.scope.key
        row["previous_state"]["policy_hash"] = policy["policy_hash"]
    assert (
        evaluate(c, inputs, policy, allocation, group)["status"]
        == "REQUEST_RUNNER_RELEASE"
    )


def test_ack_recovery_after_quote_expiry_does_not_send_again(setup):
    make, transport, _, flags = setup
    e = make()
    e.decision_book.observe(**observations(e.coordinator))
    e.request_decided_release()
    flags["now"] += 1000
    assert make().request_decided_release()["status"] == "order_bound"
    assert len(transport.writes) == 1


def test_initial_unaccepted_cost_gap_can_recover_but_accepted_cost_cannot_change(setup):
    make, transport, _, flags = setup
    e = make()
    bad = observations(e.coordinator)
    bad["positions"]["runner_lot"] = replace(
        bad["positions"]["runner_lot"], round_trip_cost_pct=-1
    )
    first = e.decision_book.observe(**bad)
    assert first["status"] == "SOURCE_GAP"
    assert all(s["last_observed_at_ms"] is None for s in first["next_states"].values())
    flags["now"] += 1
    resumed = make()
    good = resumed.decision_book.observe(
        **observations(resumed.coordinator, flags["now"], 2)
    )
    assert good["status"] == "REQUEST_RUNNER_RELEASE"
    flags["now"] += 1
    changed = observations(resumed.coordinator, flags["now"], 3)
    changed["positions"]["runner_lot"] = replace(
        changed["positions"]["runner_lot"], round_trip_cost_pct=0.22
    )
    with pytest.raises(ValueError, match="position_or_cost_epoch_changed"):
        resumed.decision_book.observe(**changed)
    with pytest.raises(ValueError, match="latest_decision"):
        make().request_decided_release()
    assert not transport.writes
