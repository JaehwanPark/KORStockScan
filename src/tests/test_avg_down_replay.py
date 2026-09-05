"""Offline AVG_DOWN inventory/exit replay: never a broker or provider adapter."""

from copy import deepcopy

import pytest

from src.engine.lifecycle import avg_down_replay as mod
from src.engine.trade_profit import calculate_net_realized_pnl


def replay_fixture():
    observation = {
        "source_event_id": "observation-1",
        "position_episode_id": "episode-1",
        "stock_code": "005930",
        "venue": "KRX",
        "scale_in_decision_id": "decision-1",
        "emitted_at": "2026-09-04T10:00:00+09:00",
        "exit_policy_version": "frozen-full-policy-1",
        "cost_rate": 0.0023,
        "pre_add_buy_qty": 10,
        "pre_add_buy_price": 10000,
        "replay_peak_price": 10000,
        "replay_start_sequence": 0,
        "initial_policy_state": {
            "ai_cache": {"source_id": "prior-ai-1"},
            "used_count": 0,
        },
        "effective_min_buy_pressure": 85,
        "route_replay": {
            "85": {"should_add": False, "route_evaluation_complete": True},
            "80": {
                "should_add": True,
                "route_evaluation_complete": True,
                "price_allowed": True,
                "proposed_add_qty": 5,
                "proposed_add_price": 9900,
                "add_order_expires_at": "2026-09-04T10:01:00+09:00",
            },
        },
    }
    frames = [
        {
            "source_event_id": f"frame-{index}",
            "replay_frame_schema": mod.FRAME_SCHEMA,
            "position_episode_id": "episode-1",
            "stock_code": "005930",
            "venue": "KRX",
            "exit_policy_version": observation["exit_policy_version"],
            "sequence": index,
            "emitted_at": f"2026-09-04T10:00:{index:02d}+09:00",
            "market": {
                "best_bid": bid,
                "best_ask": bid + 10,
                "best_bid_qty": 100,
                "best_ask_qty": 100,
                "source_quality": "fresh_conflict_free",
            },
        }
        for index, bid in enumerate((9890, 10100, 10200, 10300), 1)
    ]
    return observation, frames


def decision(state, frame, policy, input_digest, *, action=None):
    # Synthetic full-policy fixture, not a replacement live exit strategy.
    if action is None:
        action = (
            "EXIT"
            if frame["sequence"] >= (3 if state["filled_add_qty"] else 2)
            else "HOLD"
        )
    return {
        "source_event_id": f"policy-eval-{input_digest}",
        "input_digest": input_digest,
        "policy_version": policy,
        "full_policy_evaluation": True,
        "input_cutoff": frame["emitted_at"],
        "policy_state_after": deepcopy(state["policy_state"]),
        "action": action,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_independent_average_inventory_exit_and_cost_once():
    observation, frames = replay_fixture()
    before = deepcopy((observation, frames))
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["state"] == "paired_exit_complete_source_only"
    assert result["outcomes"]["80"]["exit_qty"] == 15
    assert result["outcomes"]["80"]["exit_price"] == 10200
    assert result["outcomes"]["85"]["exit_price"] == 10100
    assert result["outcomes"]["80"]["net_pnl_krw"] == sum(
        calculate_net_realized_pnl(price, 10200, qty, cost_rate=0.0023)
        for price, qty in [(10000, 10), (9900, 5)]
    )
    assert result["economics"]["85"]["incremental_net_pnl_krw"] == 0
    assert result["economics"]["80"]["candidate_minus_current_pnl_krw"] > 0
    assert (
        len(
            {value["terminal_source_event_id"] for value in result["outcomes"].values()}
        )
        == 3
    )
    assert result["runtime_authority_ready"] is False
    assert result["allowed_runtime_apply"] is False
    assert (observation, frames) == before


def test_later_gap_does_not_invalidate_completed_prefix():
    observation, frames = replay_fixture()
    frames[-1]["capture_gap"] = "observer_stopped"
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["state"] == "paired_exit_complete_source_only"
    assert result["unconsumed_tail_gap"] == "replay_capture_continuity_gap"


def test_cancel_then_exit_does_not_invent_an_extra_frame_delay():
    observation, frames = replay_fixture()
    observation["route_replay"]["80"]["proposed_add_price"] = 9000

    def cancel_and_exit(state, frame, policy, digest):
        record = decision(state, frame, policy, digest, action="EXIT")
        record["pending_add_cancelled"] = state["pending_add"] is not None
        return record

    result = mod.replay_exit_paths(
        observation, frames, full_exit_evaluator=cancel_and_exit
    )
    assert result["state"] == "paired_exit_complete_source_only"
    assert result["outcomes"]["80"]["exit_time"] == frames[0]["emitted_at"]
    assert result["outcomes"]["80"]["filled_add_qty"] == 0


def test_gap_blocks_only_arms_that_still_need_future_frames():
    observation, frames = replay_fixture()
    frames[2]["capture_gap"] = "observer_stopped"
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert set(result["outcomes"]) == {"85", "NO_ADD"}
    assert result["blockers"] == {"80": "replay_capture_continuity_gap"}


def test_conflicting_duplicate_after_exit_is_still_global_source_conflict():
    observation, frames = replay_fixture()
    conflict = deepcopy(frames[0])
    conflict["market"]["best_bid"] += 1
    frames.append(conflict)
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["outcomes"] == {}


def test_missing_ai_becomes_exact_state_request_not_assumed_hold():
    observation, frames = replay_fixture()
    result = mod.replay_exit_paths(observation, frames)
    assert set(result["blockers"].values()) == {
        "requires_state_bound_holding_ai_replay"
    }
    assert len({request["input_digest"] for request in result["replay_requests"]}) == 3
    assert result["outcomes"] == {}
    assert next(
        request for request in result["replay_requests"] if request["arm"] == "80"
    )["state"]["buy_price"] == pytest.approx(9966.6666667)


def test_recorded_policy_evaluations_are_reusable_only_for_exact_state():
    observation, frames = replay_fixture()

    def recording_evaluator(state, frame, policy, input_digest):
        record = decision(state, frame, policy, input_digest)
        frames[frame["sequence"] - 1].setdefault("full_policy_decisions", {})[
            input_digest
        ] = record
        return record

    first = mod.replay_exit_paths(
        observation, frames, full_exit_evaluator=recording_evaluator
    )
    second = mod.replay_exit_paths(observation, frames)
    assert first == second
    observation["pre_add_buy_price"] = 10001
    changed = mod.replay_exit_paths(observation, frames)
    assert changed["outcomes"] == {}


@pytest.mark.parametrize(
    "key,value,reason",
    [
        ("venue", "NXT", "replay_frame_identity_policy_or_sequence_gap"),
        (
            "position_episode_id",
            "other",
            "replay_frame_identity_policy_or_sequence_gap",
        ),
        ("sequence", 3, "replay_frame_identity_policy_or_sequence_gap"),
        (
            "exit_policy_version",
            "other",
            "replay_frame_identity_policy_or_sequence_gap",
        ),
        ("source_event_id", "", "replay_frame_identity_policy_or_sequence_gap"),
    ],
)
def test_frame_lineage_and_continuity_fail_closed(key, value, reason):
    observation, frames = replay_fixture()
    frames[0][key] = value
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["blockers"] == {"source": reason}
    assert result["outcomes"] == {}


@pytest.mark.parametrize(
    "key,value",
    [("source_quality", "stale"), ("best_bid", 999999), ("best_ask", float("nan"))],
)
def test_invalid_market_is_not_an_exit(key, value):
    observation, frames = replay_fixture()
    frames[0]["market"][key] = value
    assert (
        mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)[
            "outcomes"
        ]
        == {}
    )


def test_partial_add_and_partial_exit_not_mislabeled_full_fill():
    observation, frames = replay_fixture()
    frames[0]["market"]["best_ask_qty"] = 1
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["blockers"]["80"] == "partial_add_fill_replay_not_supported"
    assert result["state"] == "paired_exit_replay_blocked"
    frames[1]["market"]["best_bid_qty"] = 1
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["blockers"]["85"] == "partial_exit_fill_replay_not_supported"


def test_expired_add_does_not_fill_in_later_quote():
    observation, frames = replay_fixture()
    observation["route_replay"]["80"]["add_order_expires_at"] = frames[0]["emitted_at"]
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert (
        result["blockers"]["80"] == "expired_add_requires_state_bound_cancel_evaluation"
    )

    def cancel(state, frame, policy, input_digest):
        return decision(
            state,
            frame,
            policy,
            input_digest,
            action="CANCEL_ADD" if state.get("pending_add_expired") else "EXIT",
        )

    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=cancel)
    assert result["outcomes"]["80"]["filled_add_qty"] == 0


def test_subsequent_leg_and_policy_state_are_independent():
    observation, frames = replay_fixture()
    frames[1]["market"].update(best_bid=9890, best_ask=9900)

    def evaluator(state, frame, policy, input_digest):
        record = decision(state, frame, policy, input_digest)
        if frame["sequence"] == 1 and state["min_buy_pressure"] == 80:
            record.update(
                action="ADD",
                add_order={
                    "qty": 2,
                    "price": 9900,
                    "expires_at": "2026-09-04T10:01:00+09:00",
                    "existing_sizing_price_and_safety_evaluated": True,
                },
            )
            record["policy_state_after"]["used_count"] = 2
        return record

    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=evaluator)
    assert result["outcomes"]["80"]["exit_qty"] == 17
    assert len(result["outcomes"]["80"]["legs"]) == 3
    assert result["outcomes"]["80"]["final_policy_state"]["used_count"] == 2
    assert result["outcomes"]["85"]["final_policy_state"]["used_count"] == 0


@pytest.mark.parametrize(
    "key,value",
    [
        ("full_policy_evaluation", False),
        ("input_digest", "other"),
        ("policy_version", "other"),
        ("actual_order_submitted", True),
        ("broker_order_forbidden", False),
        ("input_cutoff", "future"),
        ("policy_state_after", None),
    ],
)
def test_invalid_evaluation_cannot_terminate_arm(key, value):
    observation, frames = replay_fixture()

    def invalid(*args):
        return {**decision(*args), key: value}

    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=invalid)
    assert set(result["blockers"].values()) == {
        "full_exit_policy_evaluation_contract_gap"
    }


def test_first_episode_decision_is_not_replaced_by_later_complete_input():
    observation, frames = replay_fixture()
    later = {
        **observation,
        "emitted_at": "2026-09-04T10:00:01+09:00",
        "independent_exit_replay_frames": frames,
    }
    result = mod.build_replay_evidence([later, observation])
    assert result["unique_episode_count"] == 1
    assert result["complete_episode_count"] == 0
    assert result["blocker_counts"] == {"replay_market_path_missing": 1}


def test_evaluator_failure_is_explicit_and_cannot_escape_into_runtime():
    observation, frames = replay_fixture()

    def failed(*args):
        raise RuntimeError("offline evaluator unavailable")

    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=failed)
    assert set(result["blockers"].values()) == {"offline_full_policy_evaluator_failed"}


def test_clean_baseline_is_enforced_by_engine_itself():
    observation, frames = replay_fixture()
    observation["emitted_at"] = "2026-06-04T23:59:59+09:00"
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["blockers"] == {"source": "pre_clean_baseline_replay_forbidden"}


def test_cost_snapshot_not_current_process_rate_controls_replay():
    observation, frames = replay_fixture()
    observation["cost_rate"] = 0.01
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["outcomes"]["85"]["net_pnl_krw"] == -10


def test_zero_available_ask_quantity_is_known_unfilled_not_missing_data():
    observation, frames = replay_fixture()
    frames[0]["market"]["best_ask_qty"] = 0
    result = mod.replay_exit_paths(observation, frames)
    candidate = next(
        request for request in result["replay_requests"] if request["arm"] == "80"
    )
    assert candidate["state"]["filled_add_qty"] == 0
    assert candidate["state"]["pending_add"] is not None
    assert result["blockers"]["80"] == "requires_state_bound_holding_ai_replay"


@pytest.mark.parametrize("malformed", ["not-an-arm", None, []])
def test_malformed_arm_is_reported_without_crashing_other_arms(malformed):
    observation, frames = replay_fixture()
    observation["route_replay"]["80"] = malformed
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["blockers"]["80"] == "route_arm_schema_invalid"
    assert "85" in result["outcomes"]


@pytest.mark.parametrize("sequence", [True, 1.5])
def test_frame_sequence_is_not_lossily_normalized(sequence):
    observation, frames = replay_fixture()
    frames[0]["sequence"] = sequence
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["outcomes"] == {}
    assert "source" in result["blockers"]


def test_missing_peak_is_not_replaced_by_average_entry():
    observation, frames = replay_fixture()
    observation.pop("replay_peak_price")
    result = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    assert result["outcomes"] == {}
    assert result["state"] == "paired_exit_replay_blocked"


def test_identical_duplicate_frame_is_idempotent_but_conflict_blocks():
    observation, frames = replay_fixture()
    original = mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
    frames.append(deepcopy(frames[0]))
    assert (
        mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)
        == original
    )
    frames[-1]["market"]["best_bid"] -= 1
    assert mod.replay_exit_paths(observation, frames, full_exit_evaluator=decision)[
        "blockers"
    ] == {"source": "conflicting_replay_frame"}
