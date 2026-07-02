from src.engine.scalping.entry_opportunity_recheck import (
    EntryOpportunityRecheckConfig,
    EntryOpportunityRecheckState,
    evaluate_blocked_ai_score_recheck,
)
from src.utils.threshold_cycle_registry import threshold_family_for_stage


def _enabled_config(**overrides):
    values = {
        "enabled": True,
        "min_ai_score": 70.0,
        "max_ai_score": 74.999,
        "max_recheck_per_symbol": 1,
        "max_daily_recheck": 10,
        "max_daily_buy_recovery": 3,
        "max_ws_age_ms": 1500,
        "forbid_danger": True,
        "require_fresh_quote": True,
        "require_explicit_buy_action": True,
    }
    values.update(overrides)
    return EntryOpportunityRecheckConfig(**values)


def _decision(config=None, state=None, **overrides):
    values = {
        "code": "005930",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "ai_score": 72.0,
        "ai_action": "BUY",
        "ws_age_ms": 500,
        "latency_state": "SAFE",
        "state": state or EntryOpportunityRecheckState(),
        "config": config or _enabled_config(),
        "today": "2026-07-02",
    }
    values.update(overrides)
    return evaluate_blocked_ai_score_recheck(**values)


def test_default_off_blocks_without_order_authority():
    decision = _decision(config=EntryOpportunityRecheckConfig())

    assert not decision.allowed
    assert decision.reason == "disabled"
    assert decision.fields["runtime_effect"] is False
    assert decision.fields["allowed_runtime_apply"] is False
    assert decision.fields["actual_order_submitted"] is False
    assert decision.fields["broker_order_forbidden"] is True


def test_score_70_74_explicit_buy_fresh_quote_can_reenter_normal_path():
    decision = _decision()

    assert decision.allowed
    assert decision.action == "allow_normal_buy_reentry"
    assert decision.stage == "entry_opportunity_recheck_normal_buy_reentered"
    assert decision.fields["runtime_effect"] is True
    assert decision.fields["allowed_runtime_apply"] is True
    assert decision.fields["actual_order_submitted"] is False
    assert decision.fields["broker_order_forbidden"] is False
    assert "broker_guard_bypass" in decision.fields["forbidden_uses"]


def test_score_and_action_bounds_are_fail_closed():
    assert _decision(ai_score=69.9).reason == "score_out_of_range"
    assert _decision(ai_score=74.9).allowed
    assert _decision(ai_score=75.0).reason == "score_out_of_range"
    assert _decision(ai_action="WAIT").reason == "ai_action_not_buy"


def test_danger_and_stale_quote_are_not_relaxed():
    assert _decision(latency_state="DANGER").reason == "latency_state_danger"
    assert _decision(ws_age_ms=2000).reason == "quote_freshness_not_confirmed"


def test_hard_safety_source_reason_blocks_even_when_score_matches():
    decision = _decision(source_reason="entry_cooldown_active")

    assert not decision.allowed
    assert decision.reason == "hard_safety_source_block"
    assert decision.fields["runtime_effect"] is False
    assert decision.fields["allowed_runtime_apply"] is False


def test_daily_and_symbol_caps_block():
    state = EntryOpportunityRecheckState(trade_date="2026-07-02")
    state.record_recheck("005930")
    symbol_capped = _decision(state=state, config=_enabled_config(max_recheck_per_symbol=1))
    assert symbol_capped.reason == "symbol_recheck_cap_exhausted"

    state = EntryOpportunityRecheckState(trade_date="2026-07-02", daily_recheck_count=10)
    daily_capped = _decision(state=state, config=_enabled_config(max_daily_recheck=10))
    assert daily_capped.reason == "daily_recheck_cap_exhausted"

    state = EntryOpportunityRecheckState(trade_date="2026-07-02", daily_buy_recovery_count=3)
    recovery_capped = _decision(state=state, config=_enabled_config(max_daily_buy_recovery=3))
    assert recovery_capped.reason == "daily_buy_recovery_cap_exhausted"


def test_registry_maps_recheck_stages_to_family():
    assert (
        threshold_family_for_stage("entry_opportunity_recheck_normal_buy_reentered")
        == "entry_opportunity_recheck_runtime"
    )
    assert (
        threshold_family_for_stage("entry_opportunity_recheck_blocked")
        == "entry_opportunity_recheck_runtime"
    )
