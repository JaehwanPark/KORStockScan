from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests import test_machine_adaptive_exit_group_decision as pre_tests
from src.tests.test_machine_adaptive_exit_group_runtime import confirmed
from src.tests.test_machine_adaptive_exit_broker import NOW
from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.group_execution import GroupAction
from src.trading.order.adaptive_exit.group_trailing import evaluate_released_runners
from src.trading.order.adaptive_exit.models import Clock


@pytest.fixture
def setup(tmp_path, monkeypatch):
    return pre_tests.setup.__wrapped__(tmp_path, monkeypatch)


def release(make, transport, flags):
    e = make()
    e.decision_book.observe(**pre_tests.observations(e.coordinator))
    e.request_decided_release()
    confirmed(transport)
    flags["now"] += 1
    assert e.reconcile_release()["status"] == "runner_released_awaiting_decision"
    return e


def observation(e, flags, seq=2, bid=70400, **changes):
    obs = pre_tests.observations(e.coordinator, flags["now"], seq, bid)
    runners = e.coordinator.allocation.runner_lot_ids
    return {
        "snapshots": {
            k: replace(v, **changes)
            for k, v in obs["snapshots"].items()
            if k in runners
        },
        "clocks": {k: v for k, v in obs["clocks"].items() if k in runners},
    }


def sell_decision(e, flags):
    # The original trail arm disappeared after exact partial cancel. The existing
    # vanished-arm contract exits with valid current depth, never stale fallback.
    return e.released_book.observe(
        **observation(e, flags, bid=70100, supportive=False, improvement_bps=0)
    )


def ack(transport):
    transport.write_body = {
        "return_code": 0,
        "ord_no": "0000005",
        "dmst_stex_tp": "SOR",
    }


def test_confirmed_release_arm_monotonic_restart_stop_and_first_sell(setup):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    first = e.released_book.observe(**observation(e, flags))
    assert first["status"] == "TRAIL_ACTIVE"
    state = first["next_states"]["runner_lot"]
    assert state["trail_active"] is True
    assert (state["high_water"], state["stop_price"]) == (70400, 70300)
    assert first["authority"] == AUTHORITY and first["realized_pnl"] is None
    assert not first["group_terminal"]
    with pytest.raises(ValueError, match="does_not_allow_sell"):
        e.sell_decided_released()
    assert len(transport.writes) == 1
    flags["now"] += 1
    resumed = make()
    second = resumed.released_book.observe(
        **observation(resumed, flags, seq=3, bid=70500)
    )
    state2 = second["next_states"]["runner_lot"]
    assert (state2["high_water"], state2["stop_price"]) == (70500, 70400)
    assert state2["first_fill_at_ms"] == state["first_fill_at_ms"]
    flags["now"] += 1
    third = resumed.released_book.observe(
        **observation(resumed, flags, seq=4, bid=70400)
    )
    assert third["status"] == "SELL_RUNNER" and third["limit_price"] == 70400
    assert third["lot_decisions"]["runner_lot"]["action"] == "REQUEST_TRAIL_EXIT"
    ack(transport)
    result = resumed.sell_decided_released()
    assert result["status"] == "order_bound" and not result["group_terminal"]
    assert transport.writes[-1]["payload"]["ord_qty"] == "6"
    assert transport.writes[-1]["payload"]["ord_uv"] == "70400"
    assert transport.writes[-1]["payload"]["trde_tp"] == "0"
    assert len(transport.writes) == 2
    flags["now"] += 1000
    assert make().sell_decided_released()["status"] == "order_bound"
    assert len(transport.writes) == 2
    with pytest.raises(ValueError, match="already_committed"):
        make().released_book.observe(**observation(make(), flags, seq=5))


def test_vanished_arm_fresh_depth_first_sell_and_no_target_replacement(setup):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    r = sell_decision(e, flags)
    assert r["status"] == "SELL_RUNNER" and r["limit_price"] == 70100
    assert not r["next_states"]["runner_lot"]["trail_active"]
    ack(transport)
    e.sell_decided_released()
    target = e.coordinator._target()
    assert target["canceled_qty"] == 6 and target["state"] == "ORDER_BOUND"
    assert len(transport.writes) == 2


def test_kept_target_fills_after_confirmed_release_before_runner_sell(setup):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    proof = e.coordinator._read()["release"]["cancel_proof_hash"]
    confirmed(transport, 4)
    transport.current = []
    state = e.reconcile_release()
    assert state["status"] == "runner_released_awaiting_decision"
    assert state["target_reserved_qty"] == 0
    assert e.coordinator._read()["release"]["cancel_proof_hash"] == proof
    assert e.coordinator._target()["state"] == "ORDER_TERMINAL"
    e = make()
    r = sell_decision(e, flags)
    assert r["quantity"] == 6
    ack(transport)
    assert e.sell_decided_released()["status"] == "order_bound"
    assert transport.writes[-1]["payload"]["ord_qty"] == "6"
    assert len(transport.writes) == 2


@pytest.mark.parametrize(
    "gap", ["missing_child", "confirmation", "root_fill", "current_child"]
)
def test_old_release_cannot_override_new_target_or_cancel_source_gap(setup, gap):
    from src.tests.test_machine_adaptive_exit_broker import current

    make, transport, _, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    confirmed(transport, 4)
    transport.current = []
    if gap == "missing_child":
        transport.detailed.pop()
    elif gap == "confirmation":
        transport.detailed[-1]["cnfm_qty"] = "5"
    elif gap == "root_fill":
        transport.detailed[0]["cntr_qty"] = "3"
    else:
        transport.current = [
            current(ord_no="0000003", orig_ord_no="0000002", ord_qty="6", oso_qty="0")
        ]
    ack(transport)
    with pytest.raises(ValueError):
        e.sell_decided_released()
    assert len(transport.writes) == 1


def test_cancel_ack_without_proof_cannot_arm(setup):
    make, transport, _, flags = setup
    e = make()
    e.decision_book.observe(**pre_tests.observations(e.coordinator))
    e.request_decided_release()
    with pytest.raises(ValueError, match="confirmed_original_release"):
        e.released_book.observe(**observation(e, flags))
    assert len(transport.writes) == 1


@pytest.mark.parametrize("failure", ["before", "after", "noop"])
@pytest.mark.parametrize("at_result", [False, True])
def test_save_failure_retains_veto_or_exact_receipt_never_sends(
    setup, failure, at_result
):
    make, transport, store, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    flags["now"] += 1
    save = e.coordinator.save_record

    def fail(key, expected, raw):
        if key == e.released_book.key and (raw["veto"] is None) == at_result:
            store.fail = failure
        return save(key, expected, raw)

    e.coordinator.save_record = fail
    with pytest.raises((ValueError, OSError)):
        e.released_book.observe(**observation(e, flags, seq=3))
    with pytest.raises(ValueError, match="not_durable"):
        e.sell_decided_released()
    assert len(transport.writes) == 1
    # Failure before/no-op of the pending write cannot durably record a veto.
    # The failed process stays poisoned; a restarted owner must revalidate live
    # source via the independent write guard, never infer a new observation.
    if (not at_result and failure == "after") or (at_result and failure != "after"):
        with pytest.raises(ValueError, match="does_not_allow_sell"):
            make().sell_decided_released()


@pytest.mark.parametrize("gate", ["action_allowed", "lock", "approval", "custody"])
def test_first_sell_still_requires_independent_full_guard(setup, gate):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    flags[gate] = False
    with pytest.raises(PermissionError):
        e.sell_decided_released()
    assert len(transport.writes) == 1


@pytest.mark.parametrize("mutation", ["veto", "quote_age", "lock", "approval"])
def test_write_revalidation_after_reservation(setup, monkeypatch, mutation):
    make, transport, store, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    reserve = e.coordinator.adapter.registry.reserve

    def changed(**kwargs):
        row = reserve(**kwargs)
        if mutation == "veto":
            raw = store.records[e.released_book.key]
            raw["veto"] = "observation_pending_or_invalid"
            raw["canonical_sha256"] = canonical_sha256(raw)
        elif mutation == "quote_age":
            flags["now"] += 501
        else:
            flags[mutation] = False
        return row

    monkeypatch.setattr(e.coordinator.adapter.registry, "reserve", changed)
    with pytest.raises((ValueError, PermissionError)):
        e.sell_decided_released()
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "bad",
    ["missing", "future", "epoch", "sequence", "stale", "depth", "support", "nan"],
)
def test_bad_new_observation_veto_and_preserves_accepted_stop(setup, bad):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    # First save a SELL so an invalid replacement must revoke it.
    original = sell_decision(e, flags)
    flags["now"] += 1
    obs = observation(e, flags, seq=3)
    if bad == "missing":
        obs["snapshots"] = {}
    elif bad == "future":
        obs["clocks"]["runner_lot"] = Clock(flags["now"] + 1, 0)
    else:
        changes = {
            "epoch": {"source_epoch": "changed"},
            "sequence": {"sequence": 2},
            "stale": {"quote_at_ms": NOW - 1000},
            "depth": {"bid_levels": ((70400, 5),)},
            "support": {"supportive": None},
            "nan": {"improvement_bps": float("nan")},
        }[bad]
        obs["snapshots"]["runner_lot"] = replace(
            obs["snapshots"]["runner_lot"], **changes
        )
    try:
        result = e.released_book.observe(**obs)
    except ValueError:
        pass
    else:
        assert result["status"] in {"SOURCE_GAP", "RECOVERY_REQUIRED"}
        assert result["next_states"] == original["next_states"]
    with pytest.raises(ValueError):
        make().sell_decided_released()
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("limit_price", 70200),
        ("quantity", 7),
        ("group_terminal", True),
        ("realized_pnl", 0),
        ("status", "TRAIL_ACTIVE"),
    ],
)
def test_rehashed_receipt_not_a_decision_authority(setup, field, value):
    make, transport, store, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    raw = store.records[e.released_book.key]
    raw["receipt"][field] = value
    raw["receipt"]["canonical_sha256"] = canonical_sha256(raw["receipt"])
    raw["canonical_sha256"] = canonical_sha256(raw)
    with pytest.raises(ValueError, match="recomputed"):
        make().sell_decided_released()
    assert len(transport.writes) == 1


@pytest.mark.parametrize("which", ["absent", "swapped"])
def test_removing_or_swapping_post_book_cannot_bypass_decision(setup, which):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    e.released_book = None if which == "absent" else make().released_book
    with pytest.raises(ValueError):
        e.sell_released(
            GroupAction("SELL_RUNNER", "a" * 64, "b" * 64, flags["now"], 70100)
        )
    assert len(transport.writes) == 1


def test_pre_release_action_hash_cannot_be_reused_as_sell_decision(setup):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    sell_decision(e, flags)
    old = e.decision_book.release_action()
    with pytest.raises(ValueError, match="latest_recomputed"):
        e.sell_released(
            GroupAction(
                "SELL_RUNNER",
                old["decision_receipt_hash"],
                old["source_hash"],
                flags["now"],
                70100,
            )
        )
    assert len(transport.writes) == 1


def test_shared_runner_depth_and_mixed_actions_never_sell_other_runner(setup):
    make, _, _, _ = setup
    c = make().coordinator
    group, allocation, policy, pre_inputs = pre_tests.three_lots(c)
    pre = pre_tests.evaluate(c, pre_inputs, policy, allocation, group)
    release = {
        "target_filled_qty": 1,
        "runner_released_qty": 6,
        "observed_at_ms": NOW + 1,
        "sell_authority": False,
        "actual_lot_fill_attribution": None,
        "realized_pnl": None,
    }
    lots = deepcopy(pre_inputs["lots"])
    del lots["target_lot"]
    for lot, row in lots.items():
        row["previous_state"] = pre["next_states"][lot]
        row["clock"]["now_ms"] = NOW + 1
        row["snapshot"].update(
            observed_at_ms=NOW + 1,
            quote_at_ms=NOW + 1,
            sequence=2,
            bid_levels=[[70400, 3], [70300, 3]],
        )

    def evaluate():
        return evaluate_released_runners(
            group=group,
            allocation=allocation,
            policy_payload=policy,
            inputs={"pre_release": pre, "release": release, "lots": lots},
        )

    result = evaluate()
    assert result["status"] == "TRAIL_ACTIVE"
    assert result["lot_decisions"]["runner2"]["executable_bid"] == 70300
    lots["runner2"]["snapshot"]["supportive"] = False
    result = evaluate()
    assert result["status"] == "SELECTIVE_RUNNER_EXIT_REQUIRES_RECOVERY"
    assert result["limit_price"] is None
    assert all(not row["trail_active"] for row in result["next_states"].values())
    for row in lots.values():
        row["snapshot"]["bid_levels"] = [[70400, 3], [70300, 2]]
    assert evaluate()["status"] == "SOURCE_GAP"


def test_live_book_does_not_accept_caller_supplied_positions_or_cost(setup):
    make, transport, _, flags = setup
    e = release(make, transport, flags)
    with pytest.raises(TypeError):
        e.released_book.observe(**observation(e, flags), positions={})
    assert len(transport.writes) == 1
