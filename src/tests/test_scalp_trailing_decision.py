import pytest

from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit


def test_fast_and_normal_share_peak_worsen_trigger():
    decision = evaluate_trailing_take_profit(
        peak_price=10100,
        executable_bid=10050,
        peak_profit_pct=1.0,
        start_pct=0.6,
        strong=False,
        weak_limit_pct=0.4,
        strong_limit_pct=0.8,
    )
    assert decision.armed is True
    assert decision.triggered is True
    assert decision.trigger_kind == "trailing_peak_worsen_floor"
    assert decision.threshold_key == "SCALP_TRAILING_LIMIT_WEAK"


def test_trailing_requires_arm_and_executable_bid():
    base = dict(
        peak_price=10100,
        executable_bid=10000,
        start_pct=0.6,
        strong=True,
        weak_limit_pct=0.4,
        strong_limit_pct=0.8,
    )
    assert not evaluate_trailing_take_profit(**base, peak_profit_pct=0.5).triggered
    missing_bid = evaluate_trailing_take_profit(
        **{**base, "executable_bid": 0}, peak_profit_pct=1.0
    )
    assert missing_bid.armed is True
    assert missing_bid.price_usable is False
    assert missing_bid.triggered is False


def test_strong_score_uses_wider_drawdown_than_weak_score():
    values = dict(
        peak_price=10100,
        executable_bid=10040,
        peak_profit_pct=1.0,
        start_pct=0.6,
        weak_limit_pct=0.4,
        strong_limit_pct=0.8,
    )
    weak = evaluate_trailing_take_profit(**values, strong=False)
    strong = evaluate_trailing_take_profit(**values, strong=True)

    assert weak.triggered is True
    assert strong.triggered is False
    assert strong.threshold_key == "SCALP_TRAILING_LIMIT_STRONG"


@pytest.mark.parametrize("changes,proceeds,reason", [
    ({"decision": "PASS"}, True, "decision_proceeds"),
    ({"decision": "INSUFFICIENT"}, True, "decision_proceeds"),
    ({}, False, "veto_deferred"),
    ({"now": 145}, True, "defer_timeout"),
    ({"profit": 0.59}, True, "profit_worsened"),
    ({"quote_fresh": False}, True, "quote_unavailable"),
    ({"safety": True}, True, "safety_priority"),
    ({"same_generation": False}, True, "generation_changed"),
    ({"same_market": False}, True, "market_changed"),
    ({"now": 99}, True, "clock_invalid"),
    ({"started_at": 101}, True, "clock_invalid"),
    ({"now": float("nan")}, True, "clock_invalid"),
])
def test_exit_deferral_permission_is_bounded_and_fail_safe(changes, proceeds, reason):
    from src.engine.scalping.trailing_exit_decision import evaluate_exit_deferral
    args = {"decision": "VETO", "now": 110, "signal_at": 100, "started_at": 100,
            "anchor_profit": 1, "profit": 1, "max_defer_sec": 45, "max_worsen_pct": 0.4}
    result = evaluate_exit_deferral(**{**args, **changes})
    assert result.proceeds is proceeds
    assert result.reason == reason
