from src.engine.scalping.entry_cancel_wait_attribution import (
    DEFAULT_BASE_BREAKOUT,
    DEFAULT_BASE_PULLBACK,
    DEFAULT_BASE_RESERVE,
    DEFAULT_BASE_SCALPING,
    REAL_STANDARD_MIN_SEC,
    STALE_PASSIVE_RISK_MAX_SEC,
    WAIT_POLICY_VERSION,
    ADJUSTMENT_WEIGHTS,
    compute_entry_cancel_wait_attribution,
    EntryCancelWaitAttributionResult,
)


def test_default_scalping_no_override():
    r = compute_entry_cancel_wait_attribution()
    assert r.cancel_wait_sec == 90
    assert r.base_wait_sec == 90
    assert r.min_wait_sec >= REAL_STANDARD_MIN_SEC
    assert r.max_wait_sec >= r.base_wait_sec
    assert r.decision_authority == "bounded_tunable"
    assert r.forbidden_uses == "hard_safety_bypass"
    assert r.wait_policy_version == WAIT_POLICY_VERSION


def test_use_defensive_suggested_30_not_below_min():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=30,
        ai_action="USE_DEFENSIVE",
        is_report_only=False,
    )
    assert r.cancel_wait_sec >= REAL_STANDARD_MIN_SEC
    assert r.suggested_wait_sec == 30
    assert "ai_defensive_action" in r.adjustment_reasons


def test_passive_probe_shortens_wait():
    r = compute_entry_cancel_wait_attribution(
        entry_passive_probe_applied=True,
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.cancel_wait_sec >= 30
    assert r.cancel_wait_sec <= 90
    assert "passive_probe_lifecycle" in r.adjustment_reasons


def test_breakout_base_preserved():
    r = compute_entry_cancel_wait_attribution(position_tag="BREAKOUT")
    assert r.base_wait_sec == DEFAULT_BASE_BREAKOUT
    assert r.cancel_wait_sec == DEFAULT_BASE_BREAKOUT


def test_pullback_base_preserved():
    r = compute_entry_cancel_wait_attribution(entry_mode="PULLBACK")
    assert r.base_wait_sec == DEFAULT_BASE_PULLBACK
    assert r.cancel_wait_sec == DEFAULT_BASE_PULLBACK


def test_reserve_base_preserved():
    r = compute_entry_cancel_wait_attribution(position_tag="RESERVE")
    assert r.base_wait_sec == DEFAULT_BASE_RESERVE
    assert r.cancel_wait_sec == DEFAULT_BASE_RESERVE


def test_bounded_range_never_below_min():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=5,
        ai_action="USE_DEFENSIVE",
        quote_stale_at_submit=True,
        context_stale_at_submit=True,
        entry_passive_probe_applied=True,
        ai_confidence=10,
        spread_ratio=0.01,
        liquidity_verdict="LOW",
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.cancel_wait_sec >= r.min_wait_sec
    assert r.cancel_wait_sec >= 30


def test_bounded_range_never_above_max():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=9999,
        ai_confidence=95,
        ofi_direction_label="STABLE_BULLISH",
        active_priority_matched=True,
        is_report_only=False,
    )
    assert r.cancel_wait_sec <= r.max_wait_sec


def test_stale_quote_shortens():
    r = compute_entry_cancel_wait_attribution(
        quote_stale_at_submit=True,
        is_report_only=False,
    )
    assert r.cancel_wait_sec < 90
    assert "stale_quote_detect" in r.adjustment_reasons


def test_stale_context_shortens():
    r = compute_entry_cancel_wait_attribution(
        context_stale_at_submit=True,
        is_report_only=False,
    )
    assert r.cancel_wait_sec < 90
    assert "stale_context_high" in r.adjustment_reasons


def test_partial_fill_adjustment():
    r = compute_entry_cancel_wait_attribution(
        cancelled_or_partial_filled_qty=2,
        requested_qty=10,
        is_report_only=False,
    )
    assert "partial_fill_progress" in r.adjustment_reasons
    assert r.cancel_wait_sec <= 90


def test_full_fill_no_partial_adjustment():
    r = compute_entry_cancel_wait_attribution(
        cancelled_or_partial_filled_qty=10,
        requested_qty=10,
        is_report_only=False,
    )
    assert "partial_fill_progress" not in r.adjustment_reasons


def test_high_confidence_ofi_priority_match_offsets():
    r = compute_entry_cancel_wait_attribution(
        ai_confidence=85,
        ofi_direction_label="STABLE_BULLISH",
        active_priority_matched=True,
        is_report_only=False,
    )
    assert "high_ai_confidence" in r.adjustment_reasons
    assert "favorable_ofi" in r.adjustment_reasons
    assert "active_priority_match" in r.adjustment_reasons


def test_log_fields_contain_required_keys():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=45,
        ai_action="USE_REFERENCE",
        is_report_only=True,
    )
    fields = r.as_log_fields()
    assert "cancel_wait_sec" in fields
    assert "base_wait_sec" in fields
    assert "min_wait_sec" in fields
    assert "max_wait_sec" in fields
    assert "suggested_wait_sec" in fields
    assert "wait_policy_version" in fields
    assert "wait_adjustment_reasons" in fields
    assert "wait_decision_authority" in fields
    assert "wait_forbidden_uses" in fields
    assert fields["wait_decision_authority"] == "bounded_tunable"
    assert fields["wait_forbidden_uses"] == "hard_safety_bypass"


def test_cancel_log_fields_include_overrun():
    r = compute_entry_cancel_wait_attribution()
    cancel_fields = r.as_cancel_log_fields(wait_elapsed_overrun_sec=12.5)
    assert "wait_elapsed_overrun_sec" in cancel_fields
    assert cancel_fields["wait_elapsed_overrun_sec"] == "12.5"


def test_report_only_default_behavior():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=30,
        ai_action="USE_DEFENSIVE",
    )
    assert r.cancel_wait_sec >= 30


def test_no_suggested_uses_base_wait():
    r = compute_entry_cancel_wait_attribution(
        position_tag="BREAKOUT",
        ai_confidence=90,
    )
    assert r.base_wait_sec == DEFAULT_BASE_BREAKOUT


def test_entry_mode_takes_priority():
    r = compute_entry_cancel_wait_attribution(entry_mode="PULLBACK")
    assert r.base_wait_sec == DEFAULT_BASE_PULLBACK


def test_position_tag_reserve():
    r = compute_entry_cancel_wait_attribution(position_tag="RESERVE")
    assert r.base_wait_sec == DEFAULT_BASE_RESERVE


def test_stale_passive_risk_lowers_min_wait_sec():
    r = compute_entry_cancel_wait_attribution(
        quote_stale_at_submit=True,
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec <= 30
    assert r.min_wait_sec < 60


def test_no_stale_risk_keeps_real_min():
    r = compute_entry_cancel_wait_attribution(
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec >= 60


def test_passive_probe_lifecycle_lowers_min():
    r = compute_entry_cancel_wait_attribution(
        entry_order_lifecycle="PASSIVE_PROBE",
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec <= 30


def test_context_stale_lowers_min():
    r = compute_entry_cancel_wait_attribution(
        context_stale_at_submit=True,
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec <= 30


def test_old_context_age_lowers_min():
    r = compute_entry_cancel_wait_attribution(
        context_age_ms=6000,
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec <= 30


def test_old_quote_age_lowers_min():
    r = compute_entry_cancel_wait_attribution(
        quote_age_ms=3000,
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec <= 30


def test_attribution_context_has_stale_passive_field():
    r = compute_entry_cancel_wait_attribution(
        quote_stale_at_submit=True,
        entry_passive_probe_applied=True,
        is_report_only=False,
    )
    assert "has_stale_or_passive_risk" in r.attribution_context_summary
    assert r.attribution_context_summary["has_stale_or_passive_risk"] == "true"


def test_attribution_context_no_stale_passive():
    r = compute_entry_cancel_wait_attribution(
        is_report_only=False,
    )
    assert "has_stale_or_passive_risk" in r.attribution_context_summary
    assert r.attribution_context_summary["has_stale_or_passive_risk"] == "false"


def test_use_defensive_suggested_30_with_stale_goes_to_30():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=30,
        ai_action="USE_DEFENSIVE",
        quote_stale_at_submit=True,
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec <= 30
    assert r.cancel_wait_sec >= 30
    assert r.suggested_wait_sec == 30


def test_use_defensive_no_stale_stays_at_60():
    r = compute_entry_cancel_wait_attribution(
        suggested_wait_sec=30,
        ai_action="USE_DEFENSIVE",
        is_report_only=False,
        real_min_sec=60,
        stale_max_sec=30,
    )
    assert r.min_wait_sec >= 60
    assert r.cancel_wait_sec >= 60
    assert r.suggested_wait_sec == 30


def test_integration_compute_and_resolve_consistency(monkeypatch):
    from dataclasses import replace
    from src.engine import sniper_state_handlers
    from src.engine.scalping.entry_cancel_wait_attribution import compute_entry_cancel_wait_attribution
    from src.utils.constants import TRADING_RULES as CONFIG

    rules = replace(
        CONFIG,
        ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED=True,
        ENTRY_CANCEL_WAIT_ATTRIBUTION_REAL_MIN_SEC=60,
        ENTRY_CANCEL_WAIT_ATTRIBUTION_STALE_MAX_SEC=30,
        SCALPING_ENTRY_TIMEOUT_SEC=90,
        SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC=120,
        SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC=600,
        SCALPING_RESERVE_ENTRY_TIMEOUT_SEC=1200,
    )
    monkeypatch.setattr(sniper_state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(sniper_state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    stock: dict = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "entry_timeout_sec_override": 30,
        "entry_mode": "BREAKOUT",
        "position_tag": "BREAKOUT",
    }
    code = "123456"

    sniper_state_handlers._compute_and_emit_entry_cancel_wait_attribution(
        stock, code, latency_gate={"order_price": 10000}, curr_price=10000,
    )

    stored = stock.get("entry_cancel_wait_attribution_result")
    assert isinstance(stored, dict), "Attribution result must be stored on stock"
    assert stored.get("wait_policy_applied") is True
    assert stored.get("is_report_only") is False
    assert stored.get("cancel_wait_sec") >= 60

    actual_timeout = sniper_state_handlers._resolve_buy_order_timeout_sec(stock, "SCALPING")
    assert actual_timeout == stored.get("cancel_wait_sec"), (
        f"_resolve_buy_order_timeout_sec returned {actual_timeout}, "
        f"but stored cancel_wait_sec is {stored.get('cancel_wait_sec')}"
    )
    assert stored.get("actual_timeout_sec") == stored.get("cancel_wait_sec"), (
        f"stored actual_timeout_sec={stored.get('actual_timeout_sec')} != "
        f"cancel_wait_sec={stored.get('cancel_wait_sec')}"
    )


def test_integration_disabled_stores_provenance_only(monkeypatch):
    from dataclasses import replace
    from src.engine import sniper_state_handlers
    from src.utils.constants import TRADING_RULES as CONFIG

    rules = replace(
        CONFIG,
        ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED=False,
        ENTRY_CANCEL_WAIT_ATTRIBUTION_REAL_MIN_SEC=60,
        ENTRY_CANCEL_WAIT_ATTRIBUTION_STALE_MAX_SEC=30,
        SCALPING_ENTRY_TIMEOUT_SEC=90,
    )
    monkeypatch.setattr(sniper_state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(sniper_state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    stock: dict = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "entry_timeout_sec_override": 30,
        "entry_mode": "STANDARD",
    }
    code = "123456"

    sniper_state_handlers._compute_and_emit_entry_cancel_wait_attribution(
        stock, code, latency_gate={}, curr_price=10000,
    )

    stored = stock.get("entry_cancel_wait_attribution_result")
    assert isinstance(stored, dict), "Attribution result should be stored for provenance"
    assert stored.get("wait_policy_applied") is False
    assert stored.get("is_report_only") is True

    actual_timeout = sniper_state_handlers._resolve_buy_order_timeout_sec(stock, "SCALPING")
    assert actual_timeout == 30, (
        f"disabled: entry_timeout_sec_override=30 should give timeout=30, got {actual_timeout}"
    )
    assert stored.get("actual_timeout_sec") == 30, (
        f"disabled: stored actual_timeout_sec should be 30, got {stored.get('actual_timeout_sec')}"
    )
