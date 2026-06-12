from src.engine.scalping.entry_cancel_wait_runtime import (
    COUNTERFACTUAL_AUTHORITY,
    candidate_thresholds,
    new_counterfactual_observation,
    observe_counterfactual,
)


def test_candidate_steps_follow_profile_contract():
    assert candidate_thresholds("standard", 60) == [30, 60, 90]
    assert candidate_thresholds("breakout", 120) == [90, 120, 150]
    assert candidate_thresholds("pullback", 600) == [540, 600, 660]


def test_counterfactual_completes_without_order_authority():
    observation = new_counterfactual_observation(
        order_no="1",
        submitted_at=1.0,
        cancelled_at=30.0,
        submitted_price=1000,
        qty=1,
        profile="standard",
        actual_timeout_sec=60,
        selected_timeout_sec=60,
    )
    observation, events = observe_counterfactual(observation, now_ts=91.0, current_price=990)
    assert any(item["stage"] == "entry_cancel_wait_counterfactual_threshold" for item in events)
    observation, events = observe_counterfactual(observation, now_ts=152.0, current_price=1010)
    completed = [item for item in events if item["stage"] == "entry_cancel_wait_counterfactual_completed"]
    assert completed
    assert completed[0]["counterfactual_ev_pct"] == 1.0
    assert COUNTERFACTUAL_AUTHORITY == "entry_cancel_wait_counterfactual_only"
