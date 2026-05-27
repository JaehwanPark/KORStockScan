from src.engine.swing.entry_lifecycle_policy import evaluate_swing_entry_lifecycle_policy


def test_score_gap_gatekeeper_reject_are_features_not_hard_blocks():
    result = evaluate_swing_entry_lifecycle_policy(
        strategy="KOSPI_ML",
        score=42.0,
        buy_threshold=70.0,
        current_vpw=80.0,
        vpw_condition=False,
        v_pw_limit=120.0,
        gap_pct=4.8,
        gap_threshold=3.5,
        gatekeeper_action="WAIT",
        gatekeeper_action_key="pullback_wait",
        gatekeeper_allow_entry=False,
        market_regime_blocked=True,
        market_regime_reason="normal_prior",
        source_stage="blocked_gatekeeper_reject",
    )

    assert result.submit_allowed_by_policy is True
    assert result.hard_safety_block is False
    assert result.policy_action == "ALLOW_SUBMIT_EVALUATION"
    assert result.decision_authority == "swing_entry_lifecycle_policy_baseline_prior_features"
    assert result.baseline_prior_features["score_vpw"]["vpw_condition"] is False
    assert result.baseline_prior_features["gap"]["gap_pct"] == 4.8
    assert result.baseline_prior_features["gatekeeper"]["allow_entry"] is False


def test_hard_safety_block_remains_submit_veto():
    result = evaluate_swing_entry_lifecycle_policy(
        strategy="KOSPI_ML",
        hard_safety_block=True,
        hard_safety_reason="stale_quote_submit_block",
        source_stage="entry_submit_revalidation_block",
    )

    assert result.submit_allowed_by_policy is False
    assert result.hard_safety_block is True
    assert result.hard_safety_reason == "stale_quote_submit_block"
    assert result.policy_action == "BLOCK_HARD_SAFETY"


def test_market_regime_prior_observed_is_not_submit_veto():
    result = evaluate_swing_entry_lifecycle_policy(
        strategy="KOSPI_ML",
        market_regime_blocked=False,
        market_regime_prior_observed=True,
        confirmed_risk_block=False,
        market_regime_reason="market_regime_risk_off_prior",
        source_stage="market_regime_prior_observed",
    )

    assert result.submit_allowed_by_policy is True
    assert result.hard_safety_block is False
    assert result.baseline_prior_features["market_regime"]["prior_observed"] is True
    assert result.baseline_prior_features["market_regime"]["confirmed_risk_block"] is False
