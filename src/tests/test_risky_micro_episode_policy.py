from src.engine.scalping.risky_micro_episode import evaluate_risky_micro_episode


def _evaluate(**overrides):
    values = {
        "rising_missed_lineage": True,
        "source_stage": "latency_block",
        "source_block_reason": "wide_spread",
        "best_bid": 16_220,
        "best_ask": 16_310,
        "quote_age_ms": 120.0,
        "tick_acceleration_ratio": 0.795,
        "tick_window_span_sec": 5.0,
        "positive_micro_support": True,
        "adverse_micro_detected": False,
        "large_sell_detected": False,
    }
    values.update(overrides)
    return evaluate_risky_micro_episode(**values)


def test_theborn_like_wide_spread_case_is_recheck_not_live_candidate():
    result = _evaluate()

    assert result["risky_micro_episode_status"] == "recheck_required"
    assert (
        result["risky_micro_episode_reason"] == "tick_acceleration_confirmation_pending"
    )
    assert result["risky_micro_episode_marketability"] == "passive_only"
    assert result["risky_micro_episode_hypothetical_entry_price"] < 16_310
    assert result["risky_micro_episode_runtime_effect"] is False
    assert result["risky_micro_episode_broker_order_forbidden"] is True
    assert (
        result["risky_micro_episode_metric_role"] == "source_candidate_classification"
    )
    assert result["risky_micro_episode_outcome_join_required"] is True


def test_wemade_like_tick_deceleration_is_excluded():
    result = _evaluate(tick_acceleration_ratio=0.64)

    assert result["risky_micro_episode_status"] == "excluded_excessive_risk"
    assert (
        result["risky_micro_episode_reason"] == "tick_acceleration_below_recheck_floor"
    )


def test_confirmed_fresh_case_builds_cost_aware_passive_source_plan():
    result = _evaluate(tick_acceleration_ratio=1.12)

    assert result["risky_micro_episode_status"] == "source_only_candidate"
    assert result["risky_micro_episode_gross_target_bps"] == 33
    assert result["risky_micro_episode_adverse_limit_bps"] == 33
    assert (
        result["risky_micro_episode_hypothetical_target_price"]
        > result["risky_micro_episode_hypothetical_entry_price"]
    )
    assert (
        result["risky_micro_episode_hypothetical_adverse_price"]
        < result["risky_micro_episode_hypothetical_entry_price"]
    )
    assert "risky_micro_episode_hypothetical_quantity" not in result
    assert (
        result["risky_micro_episode_quantity_owner"]
        == "position_sizing_dynamic_formula_then_existing_probe_first"
    )
    assert result["risky_micro_episode_quantity_is_tuning_axis"] is False
    assert result["risky_micro_episode_independent_episode_or_widget_owner"] is False
    assert result["risky_micro_episode_scale_in_allowed"] is False
    assert result["risky_micro_episode_residual_multi_leg_allowed"] is False
    assert (
        result["risky_micro_episode_primary_decision_metric"]
        == "candidate_status_counts"
    )


def test_adverse_micro_and_stale_bbo_fail_closed():
    adverse = _evaluate(tick_acceleration_ratio=1.2, large_sell_detected=True)
    stale = _evaluate(tick_acceleration_ratio=1.2, quote_age_ms=None)

    assert adverse["risky_micro_episode_status"] == "excluded_excessive_risk"
    assert stale["risky_micro_episode_status"] == "source_quality_blocked"


def test_long_tick_window_is_not_a_micro_episode():
    result = _evaluate(tick_acceleration_ratio=1.2, tick_window_span_sec=60.0)

    assert result["risky_micro_episode_status"] == "excluded_excessive_risk"
    assert result["risky_micro_episode_reason"] == "tick_window_span_not_micro"


def test_unrelated_entry_is_not_classified():
    result = _evaluate(rising_missed_lineage=False, tick_acceleration_ratio=1.2)

    assert result["risky_micro_episode_status"] == "not_applicable"
    assert result["risky_micro_episode_actual_order_submitted"] is False
