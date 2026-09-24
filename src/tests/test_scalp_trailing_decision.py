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
