from src.engine.scalping.entry_opportunity_recheck import (
    EntryOpportunityRecheckConfig,
    EntryOpportunityRecheckState,
    config_from_env,
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
        "require_explicit_buy_action": False,
        "allow_wait_probe_intent": True,
        "require_probe_first_contract": True,
        "probe_first_enabled": True,
        "probe_first_active_date": "2026-07-02",
        "probe_qty": 1,
        "post_probe_resolver_enabled": True,
    }
    values.update(overrides)
    return EntryOpportunityRecheckConfig(**values)


def _decision(config=None, state=None, **overrides):
    values = {
        "code": "005930",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "ai_score": 72.0,
        "ai_action": "WAIT",
        "ws_age_ms": 500,
        "latency_state": "SAFE",
        "ai_contract_status": "pass",
        "ai_edge_state": "EDGE",
        "ai_probe_intent": True,
        "ai_probe_intent_status": "eligible_wait_probe",
        "ai_recovery_trigger": "recovery_required",
        "microstructure_confirmed": True,
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


def test_config_from_env_parses_numeric_runtime_overrides(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE", "69.25")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE", "74.75")

    config = config_from_env()

    assert config.min_ai_score == 69.25
    assert config.max_ai_score == 74.75
    assert config.probe_qty == 0


def test_edge_wait_recovery_intent_can_arm_one_share_probe_path():
    decision = _decision()

    assert decision.allowed
    assert decision.action == "allow_one_share_probe_entry"
    assert decision.stage == "entry_opportunity_recheck_probe_armed"
    assert decision.fields["runtime_effect"] is True
    assert decision.fields["allowed_runtime_apply"] is True
    assert decision.fields["actual_order_submitted"] is False
    assert decision.fields["broker_order_forbidden"] is False
    assert "broker_guard_bypass" in decision.fields["forbidden_uses"]
    assert "order_quantity_or_position_cap_change" in decision.fields["forbidden_uses"]
    assert "quantity_or_cap_change" not in decision.fields["forbidden_uses"]


def test_exploration_can_bind_recovery_cap_to_verified_probe_submissions():
    state = EntryOpportunityRecheckState(
        trade_date="2026-07-02",
        daily_buy_recovery_count=3,
        daily_exploration_probe_submit_count=2,
    )

    decision = _decision(
        state=state,
        buy_recovery_cap_observed_count=state.daily_exploration_probe_submit_count,
    )

    assert decision.allowed is True
    assert (
        decision.fields["entry_opportunity_recheck_buy_recovery_cap_basis"]
        == "caller_verified_submissions"
    )
    state.record_exploration_probe_submit()
    capped = _decision(
        state=state,
        buy_recovery_cap_observed_count=state.daily_exploration_probe_submit_count,
    )
    assert capped.reason == "daily_buy_recovery_cap_exhausted"


def test_exploration_probe_submit_count_resets_on_new_trade_date():
    state = EntryOpportunityRecheckState(
        trade_date="2026-07-01",
        daily_exploration_probe_submit_count=3,
    )

    state.reset_if_new_day("2026-07-02")

    assert state.daily_exploration_probe_submit_count == 0


def test_durable_exploration_cap_survives_state_trade_date_reset():
    state = EntryOpportunityRecheckState(trade_date="2026-07-01")
    state.sync_exploration_probe_submit_count(3)
    durable_count = state.daily_exploration_probe_submit_count

    decision = _decision(
        state=state,
        today="2026-07-02",
        buy_recovery_cap_observed_count=durable_count,
    )

    assert decision.allowed is False
    assert decision.reason == "daily_buy_recovery_cap_exhausted"
    assert (
        decision.fields["entry_opportunity_recheck_buy_recovery_cap_observed_count"]
        == 3
    )


def test_score_bounds_are_prior_not_fail_closed_but_canonical_wait_still_required():
    low = _decision(ai_score=69.9)
    high = _decision(ai_score=75.0)
    assert low.allowed
    assert low.fields["entry_opportunity_recheck_score_gate_converted_to_prior"] is True
    assert low.fields["entry_opportunity_recheck_hard_gate_veto"] is False
    assert low.fields["entry_opportunity_recheck_score_prior_band"] == "low"
    assert _decision(ai_score=74.9).allowed
    assert high.allowed
    assert high.fields["entry_opportunity_recheck_score_in_prior_band"] is False
    assert _decision(ai_action="DROP").reason == "ai_action_not_supported_wait"
    assert _decision(ai_action="BUY").reason == "normal_buy_does_not_require_recheck"


def test_wait_recheck_requires_canonical_probe_micro_and_probe_first_contract():
    assert (
        _decision(ai_probe_intent=False).reason
        == "canonical_wait_probe_contract_not_confirmed"
    )
    assert (
        _decision(microstructure_confirmed=False).reason
        == "strong_micro_confirmation_missing"
    )
    assert _decision(microstructure_confirmed=False).action == "wait_for_recovery_micro"
    assert (
        _decision(config=_enabled_config(post_probe_resolver_enabled=False)).reason
        == "probe_first_post_probe_contract_not_active"
    )
    assert (
        _decision(config=_enabled_config(require_explicit_buy_action=True)).reason
        == "legacy_explicit_buy_contract_incompatible"
    )
    assert (
        _decision(config=_enabled_config(require_probe_first_contract=False)).reason
        == "probe_first_contract_requirement_disabled"
    )
    assert (
        _decision(ai_probe_intent="false").reason
        == "canonical_wait_probe_contract_not_confirmed"
    )
    assert (
        _decision(microstructure_confirmed="false").reason
        == "strong_micro_confirmation_missing"
    )


def test_danger_and_stale_quote_are_not_relaxed():
    assert (
        _decision(latency_state="DANGER", microstructure_confirmed=False).reason
        == "latency_state_danger"
    )
    assert (
        _decision(ws_age_ms=2000, microstructure_confirmed=False).reason
        == "quote_freshness_not_confirmed"
    )


def test_hard_safety_source_reason_blocks_even_when_score_matches():
    decision = _decision(source_reason="entry_cooldown_active")

    assert not decision.allowed
    assert decision.reason == "hard_safety_source_block"
    assert decision.fields["runtime_effect"] is False
    assert decision.fields["allowed_runtime_apply"] is False


def test_daily_and_symbol_caps_block():
    state = EntryOpportunityRecheckState(trade_date="2026-07-02")
    state.record_recheck("005930")
    symbol_capped = _decision(
        state=state, config=_enabled_config(max_recheck_per_symbol=1)
    )
    assert symbol_capped.reason == "symbol_recheck_cap_exhausted"

    state = EntryOpportunityRecheckState(
        trade_date="2026-07-02", daily_recheck_count=10
    )
    daily_capped = _decision(state=state, config=_enabled_config(max_daily_recheck=10))
    assert daily_capped.reason == "daily_recheck_cap_exhausted"

    state = EntryOpportunityRecheckState(
        trade_date="2026-07-02", daily_buy_recovery_count=3
    )
    recovery_capped = _decision(
        state=state, config=_enabled_config(max_daily_buy_recovery=3)
    )
    assert recovery_capped.reason == "daily_buy_recovery_cap_exhausted"


def test_intraday_escalation_disabled_keeps_base_daily_caps():
    state = EntryOpportunityRecheckState(
        trade_date="2026-07-02", daily_recheck_count=10
    )
    state.record_recovery_mark(
        "000001", profit_rate=0.4, peak_profit=0.7, now_ts=1_000.0
    )
    state.record_recovery_mark(
        "000002", profit_rate=0.2, peak_profit=0.4, now_ts=1_001.0
    )

    decision = _decision(
        state=state,
        config=_enabled_config(
            intraday_escalation_enabled=False,
            max_daily_recheck=10,
            escalation_max_daily_recheck=30,
        ),
    )

    assert not decision.allowed
    assert decision.reason == "daily_recheck_cap_exhausted"
    assert (
        decision.fields["entry_opportunity_recheck_escalation_attempt_reason"]
        == "disabled"
    )
    assert (
        decision.fields["entry_opportunity_recheck_effective_max_daily_recheck"] == 10
    )


def test_intraday_escalation_does_not_revive_zero_base_caps():
    state = EntryOpportunityRecheckState(trade_date="2026-07-02")
    state.record_recovery_mark(
        "000001", profit_rate=0.4, peak_profit=0.7, now_ts=1_000.0
    )
    state.record_recovery_mark(
        "000002", profit_rate=0.2, peak_profit=0.4, now_ts=1_001.0
    )

    decision = _decision(
        state=state,
        config=_enabled_config(
            intraday_escalation_enabled=True,
            max_daily_recheck=0,
            max_daily_buy_recovery=3,
            escalation_max_daily_recheck=30,
        ),
    )

    assert not decision.allowed
    assert decision.reason == "daily_recheck_cap_exhausted"
    assert (
        decision.fields["entry_opportunity_recheck_escalation_attempt_reason"]
        == "base_cap_disabled"
    )
    assert decision.fields["entry_opportunity_recheck_effective_max_daily_recheck"] == 0


def test_intraday_escalation_raises_caps_when_exhausted_recoveries_are_profitable():
    state = EntryOpportunityRecheckState(
        trade_date="2026-07-02",
        daily_recheck_count=10,
        daily_buy_recovery_count=3,
    )
    state.record_recovery_mark(
        "000001", profit_rate=0.4, peak_profit=0.7, now_ts=1_000.0
    )
    state.record_recovery_mark(
        "000002", profit_rate=0.2, peak_profit=0.4, now_ts=1_001.0
    )

    decision = _decision(
        state=state,
        config=_enabled_config(
            intraday_escalation_enabled=True,
            max_daily_recheck=10,
            max_daily_buy_recovery=3,
            escalation_step_recheck=10,
            escalation_step_buy_recovery=2,
            escalation_max_daily_recheck=30,
            escalation_max_daily_buy_recovery=7,
            escalation_min_successful_recoveries=2,
            escalation_min_avg_profit_pct=0.0,
            escalation_min_peak_profit_pct=0.3,
            escalation_max_worst_profit_pct=-0.6,
        ),
    )

    assert decision.allowed
    assert (
        decision.fields["entry_opportunity_recheck_escalation_attempt_reason"]
        == "escalated"
    )
    assert decision.fields["entry_opportunity_recheck_escalation_level"] == 1
    assert (
        decision.fields["entry_opportunity_recheck_effective_max_daily_recheck"] == 20
    )
    assert (
        decision.fields["entry_opportunity_recheck_effective_max_daily_buy_recovery"]
        == 5
    )
    assert decision.fields["entry_opportunity_recheck_successful_recovery_count"] == 2


def test_intraday_escalation_blocks_when_worst_profit_guard_fails():
    state = EntryOpportunityRecheckState(
        trade_date="2026-07-02", daily_recheck_count=10
    )
    state.record_recovery_mark(
        "000001", profit_rate=0.4, peak_profit=0.7, now_ts=1_000.0
    )
    state.record_recovery_mark(
        "000002", profit_rate=-0.8, peak_profit=0.5, now_ts=1_001.0
    )

    decision = _decision(
        state=state,
        config=_enabled_config(
            intraday_escalation_enabled=True,
            max_daily_recheck=10,
            escalation_min_successful_recoveries=1,
            escalation_max_worst_profit_pct=-0.6,
        ),
    )

    assert not decision.allowed
    assert decision.reason == "daily_recheck_cap_exhausted"
    assert (
        decision.fields["entry_opportunity_recheck_escalation_attempt_reason"]
        == "worst_profit_guard_block"
    )
    assert (
        decision.fields["entry_opportunity_recheck_effective_max_daily_recheck"] == 10
    )


def test_registry_maps_recheck_stages_to_family():
    assert (
        threshold_family_for_stage("entry_opportunity_recheck_normal_buy_reentered")
        == "entry_opportunity_recheck_runtime"
    )
    assert (
        threshold_family_for_stage("entry_opportunity_recheck_blocked")
        == "entry_opportunity_recheck_runtime"
    )
    assert (
        threshold_family_for_stage("entry_opportunity_recheck_probe_armed")
        == "entry_opportunity_recheck_runtime"
    )
    assert (
        threshold_family_for_stage("entry_opportunity_recheck_evaluated")
        == "entry_opportunity_recheck_runtime"
    )
