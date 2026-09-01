from dataclasses import replace
from datetime import datetime
import inspect
from types import SimpleNamespace

from src.engine import sniper_state_handlers as handlers
from src.engine.sniper_state_handlers import (
    SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY,
    _apply_initial_entry_qty_cap,
    _apply_wait6579_probe_canary,
    _build_soft_stop_whipsaw_confirmation_decision,
    _build_ai_overlap_log_fields,
    _build_ai_ops_log_fields,
    _build_observation_contract_fields,
    _merge_entry_pipeline_field_groups,
    _score65_74_recovery_probe_block_contract_fields,
    _score65_74_recovery_probe_success_contract_fields,
    _ensure_ai_source_quality_fields,
    _build_gatekeeper_fast_signature,
    _build_holding_ai_fast_signature,
    _extract_ai_overlap_snapshot,
    _is_score65_74_recovery_probe_entry_unlocked,
    _score65_74_recovery_probe_decision,
    _score65_74_recovery_probe_reuse_guard,
    _scale_in_feature_contract_defaults,
    _without_entry_pipeline_fields,
    _resolve_wait6579_probe_entry_unlock,
    _should_apply_ai_score_50_buy_hold_override,
    _should_publish_watching_buy_analysis_telegram,
    _should_run_score65_74_recovery_probe,
    _should_first_ai_wait_for_big_bite,
    _resolve_early_accel_recheck,
    _resolve_early_accel_strong_bundle_recheck,
    _resolve_ai_numeric_consistency_recheck,
    _resolve_gatekeeper_fast_reuse_sec,
    _resolve_holding_ai_fast_reuse_sec,
    _resolve_scanner_rising_strength_momentum_override,
    _reversal_add_runtime_supply_context,
    _pre_ai_blocked_gate_quality_fields,
    _scanner_terminal_block_fresh_input_confirmed,
    _strength_momentum_source_quality_block_reason,
    _strength_momentum_stability_recheck_decision,
    _resolve_watching_state_change_refresh,
    _log_entry_pipeline,
    _log_ai_confirmed_terminal_no_budget,
)
from src.utils.constants import TRADING_RULES


def _trusted_pressure(fields):
    out = {
        **fields,
        "tick_aggressor_trusted_count": fields.get("tick_aggressor_trusted_count", 3),
        "tick_aggressor_pressure_usable": fields.get(
            "tick_aggressor_pressure_usable", True
        ),
        "tick_context_quality": fields.get("tick_context_quality", "fresh_computed"),
        "tick_context_stale": fields.get("tick_context_stale", False),
        "tick_accel_source": fields.get("tick_accel_source", "computed_10ticks"),
    }
    if "micro_vwap_bp" in fields or "curr_vs_micro_vwap_bp" in fields:
        out.setdefault("micro_vwap_available", True)
        out.setdefault("minute_candle_context_quality", "fresh_bar_window")
        out.setdefault("minute_candle_window_fresh", True)
        out.setdefault("minute_candle_latest_age_ms", 8000)
    return out


def test_holding_pipeline_stable_block_logging_is_bounded_and_preserves_changes(
    monkeypatch,
):
    emitted = []
    times = iter((100.0, 101.0, 102.0, 117.0))
    monkeypatch.setenv(
        "KORSTOCKSCAN_HOLDING_PIPELINE_STABLE_BLOCK_LOG_INTERVAL_SEC", "15"
    )
    monkeypatch.setattr(handlers.time, "time", lambda: next(times))
    monkeypatch.setattr(
        handlers,
        "_holding_pipeline_observation_scope_fields",
        lambda _stock: {},
    )
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    stock = {"id": 1, "name": "테스트"}
    base = {
        "fast_exit_broker_route": "KRX",
        "fast_exit_execution_cohort": "OUTSIDE_SUPPORTED_SESSION",
        "fast_exit_route_guard_reason": "krx_only_outside_krx_regular_session",
        "fast_exit_route_source_quality_blocked": False,
    }

    handlers._log_holding_pipeline(
        stock, "001740", "scalp_fast_exit_venue_blocked", **base
    )
    handlers._log_holding_pipeline(
        stock, "001740", "scalp_fast_exit_venue_blocked", **base
    )
    handlers._log_holding_pipeline(
        stock,
        "001740",
        "scalp_fast_exit_venue_blocked",
        **{**base, "fast_exit_execution_cohort": "NXT_AFTERMARKET"},
    )
    handlers._log_holding_pipeline(
        stock,
        "001740",
        "scalp_fast_exit_venue_blocked",
        **{**base, "fast_exit_execution_cohort": "NXT_AFTERMARKET"},
    )

    assert len(emitted) == 3
    first_fields = emitted[0][1]["fields"]
    changed_fields = emitted[1][1]["fields"]
    resumed_fields = emitted[2][1]["fields"]
    assert first_fields["holding_pipeline_stable_block_suppressed_count"] == 0
    assert changed_fields["holding_pipeline_stable_block_signature_changed"] is True
    assert changed_fields["holding_pipeline_stable_block_suppressed_count"] == 1
    assert resumed_fields["holding_pipeline_stable_block_suppressed_count"] == 0


def test_reversal_add_runtime_supply_context_rejects_untrusted_pressure():
    context = _reversal_add_runtime_supply_context(
        {
            "buy_pressure_10t": 95.0,
            "tick_acceleration_ratio": 1.2,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 10.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "tick_latest_age_ms": 100,
            "quote_stale": False,
            "quote_age_ms": 100,
            "tick_aggressor_trusted_count": 0,
            "tick_aggressor_pressure_usable": False,
        }
    )

    assert context["feature_usable"] is False
    assert context["supply_ok"] is False
    assert context["checks"] == [False, False, False, False]
    assert context["source_quality"]["reversal_feature_source_quality"] == "stale"
    assert (
        "tick_aggressor_pressure_unusable"
        in context["source_quality"]["reversal_feature_stale_reason"]
    )


def test_reversal_add_runtime_supply_context_accepts_trusted_pressure():
    context = _reversal_add_runtime_supply_context(
        {
            "buy_pressure_10t": 65.0,
            "tick_acceleration_ratio": 1.2,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 10.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "tick_latest_age_ms": 100,
            "quote_stale": False,
            "quote_age_ms": 100,
            "tick_aggressor_trusted_count": 3,
            "tick_aggressor_pressure_usable": True,
            "minute_candle_latest_age_ms": 7000,
            "tick_accel_source": "computed_10ticks",
        }
    )

    assert context["feature_usable"] is True
    assert context["supply_ok"] is True
    assert context["checks"] == [True, True, True, True]


def test_scale_in_feature_defaults_mark_missing_features_unusable():
    fields = _scale_in_feature_contract_defaults(None)

    assert fields["buy_pressure_10t"] == 50.0
    assert fields["tick_acceleration_ratio"] == 0.0
    assert fields["curr_vs_micro_vwap_bp"] == 0.0
    assert fields["micro_vwap_available"] is False
    assert fields["minute_candle_context_quality"] == "missing"
    assert fields["minute_candle_window_fresh"] is False
    assert fields["minute_candle_latest_age_ms"] == -1.0
    assert fields["tick_pressure_evaluation_state"] == "unavailable_fail_closed"
    assert fields["minute_candle_evaluation_state"] == "unavailable_fail_closed"
    assert fields["reversal_feature_source_quality"] == "stale"
    assert "features_missing" in fields["reversal_feature_stale_reason"]


def test_scale_in_feature_defaults_normalize_unavailable_candle_age():
    fields = _scale_in_feature_contract_defaults(
        {
            "micro_vwap_available": False,
            "minute_candle_window_fresh": False,
            "minute_candle_latest_age_ms": "-",
        }
    )

    assert fields["minute_candle_latest_age_ms"] == -1.0
    assert fields["minute_candle_evaluation_state"] == "unavailable_fail_closed"


def test_holding_quote_provenance_uses_fresh_consistency_age():
    fields = handlers._holding_quote_provenance_fields(
        {"quote_stale": False},
        {
            "quote_consistency_state": "single_source",
            "quote_consistency_age_ms": 125.5,
        },
        now_ts=100.0,
    )

    assert fields["quote_stale"] is False
    assert fields["quote_age_ms"] == 125.5
    assert fields["quote_age_source"] == "quote_consistency_age_ms"


def test_holding_quote_provenance_fails_closed_when_age_is_unavailable():
    fields = handlers._holding_quote_provenance_fields(
        {},
        {},
        now_ts=100.0,
    )

    assert fields["quote_stale"] is True
    assert fields["quote_age_ms"] == -1.0
    assert fields["quote_age_source"] == "unavailable_fail_closed"


def test_watching_strategy_initializes_ai_call_executed_before_optional_ai_call():
    source = inspect.getsource(handlers._handle_watching_strategy_branch)
    init_idx = source.index("ai_call_executed = False")
    optional_call_idx = source.index("ai_decision = ai_engine.analyze_target(")
    first_wait_idx = source.index("first_ai_big_bite_wait_bypassed = bool(")

    assert init_idx < optional_call_idx < first_wait_idx


def test_entry_ai_snapshots_use_post_fetch_clocks():
    source = inspect.getsource(handlers._handle_watching_strategy_branch)
    fetch_idx = source.index("recent_candles, candle_source_meta = (")
    clock_idx = source.index("entry_context_now_ts = time.time()")
    context_idx = source.index(
        "candle_context = build_entry_candle_context(",
        clock_idx,
    )
    analyze_idx = source.index("ai_decision = ai_engine.analyze_target(")
    context_block = source[context_idx:analyze_idx]

    assert fetch_idx < clock_idx < context_idx < analyze_idx
    assert "now_ts=entry_context_now_ts" in context_block

    retry_source = inspect.getsource(
        handlers._retry_entry_ai_submit_authority_before_block
    )
    assert "retry_context_now_ts = time.time()" in retry_source
    assert "now_ts=retry_context_now_ts" in retry_source

    assert not hasattr(handlers, "_run_watching_score_projection_refresh")

    gatekeeper_clock_idx = source.index("gatekeeper_context_now_ts = time.time()")
    gatekeeper_snapshot_idx = source.index(
        "gatekeeper_snapshot = build_ai_market_snapshot(",
        gatekeeper_clock_idx,
    )
    gatekeeper_block = source[gatekeeper_clock_idx : gatekeeper_snapshot_idx + 1800]
    assert "now_ts=gatekeeper_context_now_ts" in gatekeeper_block


def test_entry_context_prefetches_share_integrated_sor_execution_view_contract():
    watching_source = inspect.getsource(handlers._handle_watching_strategy_branch)
    async_source = inspect.getsource(handlers._resolve_scanner_async_entry_ai)
    retry_source = inspect.getsource(
        handlers._retry_entry_ai_submit_authority_before_block
    )
    canary_source = inspect.getsource(handlers._apply_entry_ai_price_canary)

    assert watching_source.count("allow_integrated_sor_execution_view=True") == 2
    assert "allow_integrated_sor_execution_view=True" in async_source
    assert "allow_integrated_sor_execution_view=True" in retry_source
    assert "allow_integrated_sor_execution_view=True" in canary_source


def test_caution_micro_block_log_deduplicates_explicit_block_reason():
    source = inspect.getsource(handlers._submit_watching_triggered_entry)
    start = source.index("block_log_fields = _without_entry_pipeline_fields(")
    end = source.index("_emit_scalp_entry_adm_snapshot(", start)
    block_source = source[start:end]

    assert '"block_reason",' in block_source
    assert "block_reason=block_reason" in block_source


def test_entry_opportunity_recheck_cap_block_deduplicates_authority_kwargs():
    source = inspect.getsource(handlers._handle_watching_strategy_branch)
    start = source.index('"entry_opportunity_recheck_exploration_cap_block"')
    end = source.index("elif entry_opportunity_recheck.allowed:", start)
    block_source = source[start:end]

    assert "**_without_entry_pipeline_fields(" in block_source
    assert '"actual_order_submitted",' in block_source
    assert '"broker_order_forbidden",' in block_source
    assert '"runtime_effect",' in block_source
    assert "actual_order_submitted=False" in block_source
    assert "broker_order_forbidden=True" in block_source
    assert "runtime_effect=True" in block_source


def _fresh_spread_latency_gate(**overrides):
    gate = {
        "allowed": False,
        "decision": "REJECT_DANGER",
        "reason": "latency_state_danger",
        "latency_state": "DANGER",
        "signal_price": 10_000,
        "latest_price": 10_000,
        "ws_age_ms": 120,
        "ws_jitter_ms": 0,
        "spread_ratio": 0.006,
        "quote_stale": False,
        "latency_danger_reasons": "spread_above_caution_below_guard_cap",
        "latency_danger_detail_reason": "spread_above_caution_below_guard_cap",
        "latency_danger_source_quality_state": "fresh",
        "latency_danger_guard_max_spread_ratio": 0.01,
    }
    gate.update(overrides)
    return gate


def test_fresh_spread_ai_recheck_eligibility_separates_liquidity_from_staleness(
    monkeypatch,
):
    monkeypatch.setenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ENABLED", "true")
    monkeypatch.delenv(
        "KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ACTIVE_DATE", raising=False
    )

    eligible = handlers._fresh_spread_ai_recheck_eligibility(
        strategy="SCALPING",
        stock={"strategy": "SCALPING"},
        latency_gate=_fresh_spread_latency_gate(),
        now_ts=1000.0,
    )
    stale = handlers._fresh_spread_ai_recheck_eligibility(
        strategy="SCALPING",
        stock={"strategy": "SCALPING"},
        latency_gate=_fresh_spread_latency_gate(
            quote_stale=True,
            latency_danger_source_quality_state="stale",
        ),
        now_ts=1000.0,
    )
    above_cap = handlers._fresh_spread_ai_recheck_eligibility(
        strategy="SCALPING",
        stock={"strategy": "SCALPING"},
        latency_gate=_fresh_spread_latency_gate(spread_ratio=0.011),
        now_ts=1000.0,
    )

    assert eligible["fresh_spread_ai_recheck_eligible"] is True
    assert eligible["decision_authority"] == "bounded_entry_confirmation"
    assert stale["fresh_spread_ai_recheck_eligible"] is False
    assert stale["fresh_spread_ai_recheck_reason"] == "quote_stale"
    assert above_cap["fresh_spread_ai_recheck_eligible"] is False
    assert above_cap["fresh_spread_ai_recheck_reason"] == (
        "absolute_spread_cap_exceeded"
    )


def test_fresh_spread_ai_recheck_is_default_off(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ENABLED", raising=False)
    monkeypatch.delenv(
        "KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ACTIVE_DATE", raising=False
    )

    fields = handlers._fresh_spread_ai_recheck_eligibility(
        strategy="SCALPING",
        stock={"strategy": "SCALPING"},
        latency_gate=_fresh_spread_latency_gate(),
        now_ts=1000.0,
    )

    assert fields["fresh_spread_ai_recheck_eligible"] is False
    assert fields["fresh_spread_ai_recheck_reason"] == "disabled"


def test_fresh_spread_ai_recheck_uses_ai_then_fresh_quote_without_reanchoring_price(
    monkeypatch,
):
    captured = {}
    stock = {
        "strategy": "SCALPING",
        "entry_signal_price": 10_000,
        "entry_signal_time": datetime(2026, 7, 24, 10, 0),
        "last_watching_ai_confirmed_at": 995.0,
        "last_watching_ai_source_quality_fields": {
            "entry_candle_context_enabled": True,
            "entry_candle_source_quality_status": "fresh_consistent",
            "entry_candle_hybrid_guard_result": "preserve_neutral_or_supportive",
        },
    }
    refreshed_ws = {
        "curr": 10_010,
        "last_ws_update_ts": 1000.0,
        "orderbook": {
            "asks": [{"price": 10_020, "volume": 100}],
            "bids": [{"price": 10_000, "volume": 100}],
        },
    }
    monkeypatch.setenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ENABLED", "true")
    monkeypatch.setattr(
        handlers,
        "_entry_ai_submit_authority_fields",
        lambda **kwargs: {
            "blocked": False,
            "entry_ai_submit_authority_action": "BUY",
            "entry_ai_submit_authority_score": "88.0",
            "entry_ai_submit_authority_result_source": "live",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda *args, **kwargs: (
            refreshed_ws,
            {
                "pre_submit_ws_snapshot_refresh_applied": True,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                "pre_submit_ws_snapshot_refresh_age_ms": 50,
                "pre_submit_ws_snapshot_refresh_best_bid": 10_000,
                "pre_submit_ws_snapshot_refresh_best_ask": 10_020,
            },
        ),
    )

    def fake_evaluate(**kwargs):
        captured.update(kwargs)
        return {
            "allowed": True,
            "decision": "ALLOW_NORMAL",
            "reason": "latency_spread_relief_normal_override",
            "latency_state": "DANGER",
            "ws_age_ms": 50,
            "spread_ratio": 0.002,
            "quote_stale": False,
            "orders": [{"qty": 1, "price": 10_000}],
        }

    monkeypatch.setattr(handlers, "evaluate_live_buy_entry", fake_evaluate)

    gate, snapshot, fields = handlers._maybe_recheck_fresh_spread_latency_with_ai(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000},
        ai_engine=object(),
        strategy="SCALPING",
        planned_qty=10,
        signal_price=10_000,
        target_buy_price=9_990,
        current_ai_score=70.0,
        latency_gate=_fresh_spread_latency_gate(),
        now_ts=1000.0,
    )

    assert snapshot is refreshed_ws
    assert captured["signal_price"] == 10_000
    assert captured["signal_strength"] == 0.88
    assert captured["ws_data"] is refreshed_ws
    assert captured["signal_time"].tzinfo is not None
    assert fields["fresh_spread_ai_recheck_latency_recovered"] is True
    assert fields["fresh_spread_ai_recheck_ai_tight_fresh"] is True
    assert fields["pre_submit_ws_snapshot_refresh_reason"] == (
        "latest_ws_snapshot_fresh"
    )
    assert gate["allowed"] is True


def test_fresh_spread_ai_recheck_keeps_final_absolute_spread_cap(monkeypatch):
    stock = {
        "strategy": "SCALPING",
        "last_watching_ai_confirmed_at": 995.0,
        "last_watching_ai_source_quality_fields": {
            "entry_candle_context_enabled": True,
            "entry_candle_source_quality_status": "fresh_consistent",
            "entry_candle_hybrid_guard_result": "preserve_neutral_or_supportive",
        },
    }
    monkeypatch.setenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ENABLED", "true")
    monkeypatch.setattr(
        handlers,
        "_entry_ai_submit_authority_fields",
        lambda **kwargs: {
            "blocked": False,
            "entry_ai_submit_authority_action": "BUY",
            "entry_ai_submit_authority_score": "88.0",
            "entry_ai_submit_authority_result_source": "live",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda *args, **kwargs: (
            {"curr": 10_010},
            {
                "pre_submit_ws_snapshot_refresh_applied": True,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                "pre_submit_ws_snapshot_refresh_age_ms": 50,
                "pre_submit_ws_snapshot_refresh_best_bid": 9_950,
                "pre_submit_ws_snapshot_refresh_best_ask": 10_070,
                "pre_submit_ws_snapshot_refresh_latest_price": 10_010,
            },
        ),
    )
    monkeypatch.setattr(
        handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": True,
            "decision": "ALLOW_NORMAL",
            "reason": "extended_spread_canary",
            "latency_state": "DANGER",
            "ws_age_ms": 50,
            "spread_ratio": 0.012,
            "quote_stale": False,
        },
    )

    gate, _snapshot, fields = handlers._maybe_recheck_fresh_spread_latency_with_ai(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000},
        ai_engine=object(),
        strategy="SCALPING",
        planned_qty=10,
        signal_price=10_000,
        target_buy_price=9_990,
        current_ai_score=70.0,
        latency_gate=_fresh_spread_latency_gate(),
        now_ts=1000.0,
    )

    assert gate["allowed"] is False
    assert gate["reason"] == "fresh_spread_ai_recheck_absolute_spread_cap_exceeded"
    assert fields["fresh_spread_ai_recheck_latency_recovered"] is False
    assert fields["fresh_spread_ai_recheck_post_ai_within_absolute_spread_cap"] is False


def test_fresh_spread_ai_recheck_retries_old_buy_and_fails_closed(monkeypatch):
    stock = {
        "strategy": "SCALPING",
        "last_watching_ai_confirmed_at": 900.0,
    }
    monkeypatch.setenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_MAX_AI_AGE_SEC", "15")
    monkeypatch.setattr(
        handlers,
        "_entry_ai_submit_authority_fields",
        lambda **kwargs: {
            "blocked": False,
            "entry_ai_submit_authority_action": "BUY",
            "entry_ai_submit_authority_score": "88.0",
            "entry_ai_submit_authority_result_source": "live",
        },
    )
    retry_calls = []
    monkeypatch.setattr(
        handlers,
        "_retry_entry_ai_submit_authority_before_block",
        lambda **kwargs: retry_calls.append(kwargs)
        or {
            "pre_submit_entry_ai_authority_retry_attempted": True,
            "pre_submit_entry_ai_authority_retry_action": "not_evaluated",
            "pre_submit_entry_ai_authority_retry_score": "0.0",
            "pre_submit_entry_ai_authority_retry_result_source": "not_available",
        },
    )
    monkeypatch.setattr(
        handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("stale BUY authority must fail closed")
        ),
    )

    gate, _snapshot, fields = handlers._maybe_recheck_fresh_spread_latency_with_ai(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000},
        ai_engine=object(),
        strategy="SCALPING",
        planned_qty=10,
        signal_price=10_000,
        target_buy_price=9_990,
        current_ai_score=70.0,
        latency_gate=_fresh_spread_latency_gate(),
        now_ts=1000.0,
    )

    assert len(retry_calls) == 1
    assert gate["allowed"] is False
    assert fields["fresh_spread_ai_recheck_ai_retry_attempted"] is True
    assert fields["fresh_spread_ai_recheck_reason"] == "ai_action_not_buy_or_wait"


def test_fresh_spread_ai_recheck_never_rechecks_fresh_drop(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_FRESH_SPREAD_AI_RECHECK_ENABLED", "true")
    monkeypatch.setattr(
        handlers,
        "_entry_ai_submit_authority_fields",
        lambda **kwargs: {
            "blocked": True,
            "entry_ai_submit_authority_fresh_drop_veto": True,
            "entry_ai_submit_authority_action": "DROP",
            "entry_ai_submit_authority_score": "91.0",
            "entry_ai_submit_authority_result_source": "live",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_retry_entry_ai_submit_authority_before_block",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("fresh DROP must not trigger another AI call")
        ),
    )
    monkeypatch.setattr(
        handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("fresh DROP must not re-evaluate latency")
        ),
    )

    gate, _snapshot, fields = handlers._maybe_recheck_fresh_spread_latency_with_ai(
        stock={"strategy": "SCALPING"},
        code="123456",
        ws_data={"curr": 10_000},
        ai_engine=object(),
        strategy="SCALPING",
        planned_qty=10,
        signal_price=10_000,
        target_buy_price=9_990,
        current_ai_score=70.0,
        latency_gate=_fresh_spread_latency_gate(),
        now_ts=1000.0,
    )

    assert gate["allowed"] is False
    assert fields["fresh_spread_ai_recheck_reason"] == "fresh_ai_drop_veto"
    assert fields["fresh_spread_ai_recheck_latency_recovered"] is False


def test_submit_clears_retired_direct_recheck_after_fresh_spread_refresh():
    source = inspect.getsource(handlers._submit_watching_triggered_entry)
    initial_latency_idx = source.index("latency_gate = evaluate_live_buy_entry(")
    recheck_idx = source.index("_maybe_recheck_fresh_spread_latency_with_ai(")
    retired_cleanup_idx = source.index(
        "_clear_retired_latency_true_ofi_direct_recheck_state(stock)"
    )

    assert initial_latency_idx < recheck_idx < retired_cleanup_idx
    assert "_apply_latency_true_ofi_direct_recheck(" not in source


def test_update_ai_quote_freshness_fields_overwrites_stale_provenance(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    ws_data = {
        "curr": 10000,
        "orderbook": {"ask": []},
        "last_ws_update_ts": 999.95,
        "quote_age_ms": 6860,
        "quote_age_source": "old_quote_age_ms",
        "quote_stale": True,
    }

    result = handlers._update_ai_quote_freshness_fields(ws_data)

    assert result is ws_data
    assert ws_data["quote_age_ms"] == 50
    assert ws_data["quote_age_source"] == "last_ws_update_ts"
    assert ws_data["quote_stale"] is False


def test_score65_74_recovery_probe_micro_guard_blocks_unavailable_micro_vwap(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.20,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=False,
            ENTRY_STAGE_LIVE_TUNING_SELECTED=False,
        ),
    )

    decision = handlers._score65_74_recovery_probe_micro_guard(
        {
            "buy_pressure": 90.0,
            "tick_accel": 1.5,
            "micro_vwap_bp": 0.0,
            "micro_vwap_available": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 5,
        }
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "micro_vwap_unavailable"
    assert decision["micro_vwap_available"] is False


def test_score65_74_recovery_probe_micro_guard_rejects_numeric_micro_without_provenance(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.20,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=False,
            ENTRY_STAGE_LIVE_TUNING_SELECTED=False,
        ),
    )

    decision = handlers._score65_74_recovery_probe_micro_guard(
        {
            "buy_pressure": 90.0,
            "tick_accel": 1.5,
            "micro_vwap_bp": 35.0,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 5,
        }
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "micro_vwap_unavailable"
    assert decision["micro_vwap_available"] is False


def test_score65_74_recovery_probe_micro_guard_rejects_stale_minute_window(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.20,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=False,
            ENTRY_STAGE_LIVE_TUNING_SELECTED=False,
        ),
    )

    decision = handlers._score65_74_recovery_probe_micro_guard(
        {
            "buy_pressure": 90.0,
            "tick_accel": 1.5,
            "micro_vwap_bp": 35.0,
            "micro_vwap_available": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 5,
        }
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "micro_vwap_unavailable"
    assert decision["micro_vwap_available"] is False
    assert decision["minute_candle_window_fresh"] is False


def test_score65_74_recovery_probe_micro_guard_rejects_stale_minute_quality(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.20,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP=0.0,
            AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=False,
            ENTRY_STAGE_LIVE_TUNING_SELECTED=False,
        ),
    )

    decision = handlers._score65_74_recovery_probe_micro_guard(
        {
            "buy_pressure": 90.0,
            "tick_accel": 1.5,
            "micro_vwap_bp": 35.0,
            "micro_vwap_available": True,
            "minute_candle_context_quality": "stale_bar_window",
            "minute_candle_window_fresh": True,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 5,
        }
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "micro_vwap_unavailable"
    assert decision["micro_vwap_available"] is False


def test_update_ai_quote_freshness_fields_uses_pre_ai_window(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    ws_data = {
        "curr": 10000,
        "orderbook": {"ask": []},
        "last_ws_update_ts": 997.5,
    }

    result = handlers._update_ai_quote_freshness_fields(ws_data)

    assert result is ws_data
    assert ws_data["quote_age_ms"] == 2500
    assert ws_data["ai_quote_stale_max_ms"] == 3000
    assert ws_data["quote_stale"] is False


def test_update_ai_quote_freshness_fields_marks_stale_after_pre_ai_window(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    ws_data = {
        "curr": 10000,
        "orderbook": {"ask": []},
        "last_ws_update_ts": 996.5,
    }

    handlers._update_ai_quote_freshness_fields(ws_data)

    assert ws_data["quote_age_ms"] == 3500
    assert ws_data["quote_stale"] is True
    assert ws_data["quote_stale_source_class"] == "ws_snapshot_stale_at_consume"
    assert (
        ws_data["quote_stale_consumer_latency_gap_ms"]
        == "not_available_consumer_latency_gap_ms"
    )


def test_update_ai_quote_freshness_fields_marks_consumer_latency_stale_after_fresh_refresh(
    monkeypatch,
):
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    ws_data = {
        "curr": 10000,
        "orderbook": {"ask": []},
        "last_ws_update_ts": 996.5,
        "pre_ai_ws_snapshot_refresh_age_ms": 120.0,
    }

    handlers._update_ai_quote_freshness_fields(ws_data)

    assert ws_data["quote_age_ms"] == 3500
    assert ws_data["quote_stale"] is True
    assert (
        ws_data["quote_stale_source_class"]
        == "consumer_latency_stale_after_fresh_refresh"
    )
    assert ws_data["pre_ai_to_consume_quote_age_delta_ms"] == 3380.0
    assert ws_data["quote_stale_consumer_latency_gap_ms"] == 3380.0


def test_entry_adm_snapshot_uses_explicit_not_evaluated_ai_action(monkeypatch):
    captured = {}

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        captured.update(fields)

    monkeypatch.setattr(handlers, "_log_entry_pipeline", fake_log_entry_pipeline)

    handlers._emit_scalp_entry_adm_snapshot(
        {"strategy": "SCALPING", "name": "테스트"},
        "000000",
        "scalp_sim_entry_armed",
        ai_decision=None,
        ai_score=None,
    )

    assert captured["ai_action"] == "not_evaluated"
    assert captured["actual_order_submitted"] is False
    assert captured["broker_order_forbidden"] is True


def test_entry_adm_snapshot_prefers_latency_quote_freshness_over_ai_snapshot(
    monkeypatch,
):
    captured = {}

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        captured.update(fields)

    monkeypatch.setattr(handlers, "_log_entry_pipeline", fake_log_entry_pipeline)

    handlers._emit_scalp_entry_adm_snapshot(
        {
            "strategy": "SCALPING",
            "name": "테스트",
            "last_watching_ai_source_quality_fields": {
                "quote_stale": True,
                "quote_age_ms": 7_170,
            },
        },
        "003490",
        "latency_block",
        ai_decision={"action": "BUY", "score": 78, "quote_stale": True},
        ai_score=78,
        chosen_action="WAIT_REQUOTE",
        latency_gate={
            "reason": "latency_state_danger",
            "quote_stale": False,
            "latency_state": "DANGER",
            "latency_danger_reasons": "other_danger",
            "pre_submit_ws_snapshot_refresh_applied": True,
            "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
            "pre_submit_ws_snapshot_refresh_age_ms": 227.569,
        },
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )

    assert captured["quote_stale"] is False
    assert captured["latency_danger_reasons"] == "other_danger"
    assert captured["pre_submit_ws_snapshot_refresh_applied"] is True
    assert (
        captured["pre_submit_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    )


def test_entry_adm_snapshot_keeps_current_ai_preflight_over_persisted_fallback(
    monkeypatch,
):
    captured = {}

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        captured.update(fields)

    monkeypatch.setattr(handlers, "_log_entry_pipeline", fake_log_entry_pipeline)

    handlers._emit_scalp_entry_adm_snapshot(
        {
            "strategy": "SCALPING",
            "name": "테스트",
            "last_watching_ai_source_quality_fields": {
                "ai_market_snapshot_id": "snapshot-previous",
                "ai_input_preflight_status": "fresh_consistent",
                "ai_input_preflight_allowed": True,
                "ai_input_preflight_blockers": "",
                "tick_accel_source": "computed_10ticks",
            },
        },
        "003490",
        "ai_confirmed",
        ai_decision={
            "action": "DROP",
            "score": 0,
            "reason": "ai_input_preflight_blocked",
            "ai_result_source": "input_preflight_blocked",
            "ai_market_snapshot_id": "snapshot-current",
            "ai_input_preflight_status": "blocked",
            "ai_input_preflight_allowed": False,
            "ai_input_preflight_blockers": "bbo_stale,tape_stale",
        },
        ai_score=0,
        chosen_action="NO_BUY_AI",
    )

    assert captured["ai_market_snapshot_id"] == "snapshot-current"
    assert captured["ai_input_preflight_status"] == "blocked"
    assert captured["ai_input_preflight_allowed"] is False
    assert captured["ai_input_preflight_blockers"] == "bbo_stale,tape_stale"
    assert captured["tick_accel_source"] == "not_evaluated"


def test_entry_adm_snapshot_marks_transport_timeout_not_evaluated(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: captured.update(fields),
    )

    handlers._emit_scalp_entry_adm_snapshot(
        {"strategy": "SCALPING", "name": "test"},
        "000000",
        "ai_confirmed",
        ai_decision={
            "action": "DROP",
            "score": 0,
            "ai_result_source": "timeout",
            "provider_called": True,
            "openai_http_timeout_budget_exhausted": "True",
            "openai_transport_fail_closed_reason": "request timed out",
        },
        ai_score=0,
        chosen_action="NO_BUY_AI",
    )

    assert (
        captured["ai_decision_evaluation_status"]
        == "not_evaluated_transport_timeout"
    )
    assert captured["actual_order_submitted"] is False
    assert captured["broker_order_forbidden"] is True

    captured.clear()
    handlers._emit_scalp_entry_adm_snapshot(
        {"strategy": "SCALPING", "name": "test"},
        "000000",
        "ai_confirmed",
        ai_decision={
            "action": "DROP",
            "score": 0,
            "ai_result_source": "input_preflight_blocked",
            "openai_timeout_like": "False",
            "openai_http_timeout_budget_exhausted": "False",
        },
        ai_score=0,
        chosen_action="NO_BUY_AI",
    )
    assert (
        captured["ai_decision_evaluation_status"]
        == "not_evaluated_provider_or_preflight"
    )


def test_gatekeeper_fast_signature_absorbs_small_noise():
    stock = {"position_tag": "MIDDLE"}
    ws_a = {
        "curr": 12570,
        "fluctuation": 3.42,
        "volume": 1854321,
        "v_pw": 118.1,
        "buy_ratio": 62.4,
        "prog_net_qty": 18490,
        "prog_delta_qty": 2210,
        "ask_tot": 184200,
        "bid_tot": 218700,
        "net_bid_depth": 11880,
        "net_ask_depth": -3420,
        "orderbook": {
            "asks": [{"price": 12590}, {"price": 12580}],
            "bids": [{"price": 12570}, {"price": 12560}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update(
        {
            "volume": 1858999,
            "v_pw": 118.8,
            "buy_ratio": 63.1,
            "prog_net_qty": 18999,
            "ask_tot": 188999,
        }
    )

    sig_a = _build_gatekeeper_fast_signature(stock, ws_a, "KOSPI_ML", 81.0)
    sig_b = _build_gatekeeper_fast_signature(stock, ws_b, "KOSPI_ML", 81.4)

    assert sig_a == sig_b


def test_watching_state_change_refresh_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(handlers, "TRADING_RULES", TRADING_RULES)
    stock = {
        "last_watching_ai_state_signature": {
            "buy_pressure_10t": 55.0,
            "top3_depth_regime": "balanced",
            "quote_freshness": "fresh",
        }
    }
    result = _resolve_watching_state_change_refresh(
        stock,
        {"buy_ratio": 80.0},
        now_ts=120.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert result["allowed"] is False
    assert result["reason"] == "disabled"


def test_watching_state_change_refresh_allows_one_call_per_cooldown(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=True,
        AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "last_watching_ai_state_signature": {
            "micro_vwap_side": "positive",
            "ma5_side": "positive",
            "buy_pressure_10t": 55.0,
            "tick_acceleration_regime": "steady",
            "large_sell_print_detected": False,
            "top3_depth_regime": "balanced",
            "quote_freshness": "fresh",
        }
    }
    ws_data = {
        "buy_ratio": 70.2,
        "orderbook": {
            "asks": [{"volume": 300}, {"volume": 300}, {"volume": 300}],
            "bids": [{"volume": 300}, {"volume": 300}, {"volume": 300}],
        },
    }

    result = _resolve_watching_state_change_refresh(
        stock,
        ws_data,
        now_ts=120.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert result["allowed"] is True
    assert "buy_pressure_delta" in result["reason"]

    stock["watching_state_change_refresh_last_ai_time"] = "100.000"
    blocked = _resolve_watching_state_change_refresh(
        stock,
        ws_data,
        now_ts=121.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert blocked["allowed"] is False
    assert blocked["reason"] == "already_refreshed_this_cooldown"

    stock["watching_state_change_refresh_last_ai_time"] = "100.000"
    stock["watching_state_change_refresh_block_until"] = 210.0
    blocked_after_refresh_call = _resolve_watching_state_change_refresh(
        stock,
        ws_data,
        now_ts=130.0,
        last_ai_time=120.0,
        cooldown_sec=90,
    )
    assert blocked_after_refresh_call["allowed"] is False
    assert blocked_after_refresh_call["reason"] == "already_refreshed_this_cooldown"


def test_watching_refresh_signature_ignores_untrusted_feature_pressure():
    current = handlers._build_watching_refresh_signature(
        {},
        {
            "buy_pressure_10t": 90.0,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        },
    )
    assert current["buy_pressure_usable"] is False
    assert current["buy_pressure_source"] == "feature_packet_pressure_unusable"
    assert "buy_pressure_10t" not in current["available_axes"]


def test_watching_refresh_signature_uses_trusted_feature_pressure():
    current = handlers._build_watching_refresh_signature(
        {},
        {
            "buy_pressure_10t": 90.0,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
    )
    assert current["buy_pressure_usable"] is True
    assert current["buy_pressure_source"] == "feature_packet_trusted"
    assert "buy_pressure_10t" in current["available_axes"]


def test_watching_refresh_signature_prefers_provider_buy_ratio_when_packet_pressure_untrusted():
    current = handlers._build_watching_refresh_signature(
        {"buy_ratio": 72.5},
        {
            "buy_pressure_10t": 90.0,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        },
    )
    assert current["buy_pressure_usable"] is True
    assert current["buy_pressure_source"] == "provider_buy_ratio"
    assert current["buy_pressure_10t"] == 72.5
    assert "buy_pressure_10t" in current["available_axes"]


def test_watching_state_change_refresh_does_not_compare_missing_pressure_axis(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=True,
        AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "last_watching_ai_state_signature": {
            "buy_pressure_10t": 55.0,
            "top3_depth_regime": "unknown",
            "quote_freshness": "unknown",
            "available_axes": [
                "buy_pressure_10t",
                "top3_depth_regime",
                "quote_freshness",
            ],
            "signature_source": "runtime_context_v2",
        }
    }

    result = _resolve_watching_state_change_refresh(
        stock,
        {},
        now_ts=120.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert result["allowed"] is False
    assert result["reason"] == "state_unchanged"
    assert "buy_pressure_delta" not in result["reason"]


def test_early_accel_recheck_allows_scanner_cooldown_retry(monkeypatch):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True,
        EARLY_ACCEL_RECHECK_MAX_COUNT=2,
        EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC=20,
        EARLY_ACCEL_RECHECK_MAX_AGE_SEC=180,
        EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL=1.10,
        EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "probe_acceleration_confirmed",
        "buy_price": 12280,
        "entry_armed_at_epoch": 100.0,
        "early_accel_recheck_count": 0,
        "scalp_pre_ai_gate_context": {
            "strength_momentum": {"legacy_blocked_stage": "blocked_strength_momentum"},
            "liquidity": {"legacy_blocked_stage": "blocked_liquidity"},
        },
    }
    ws_data = _trusted_pressure(
        {
            "curr": 12430,
            "tick_acceleration_ratio": 1.25,
            "curr_vs_micro_vwap_bp": 12.0,
            "quote_stale": False,
        }
    )

    result = _resolve_early_accel_recheck(
        stock,
        ws_data,
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )

    assert result["allowed"] is True
    assert result["promotion_price"] == 12280
    assert result["current_price"] == 12430


def test_early_accel_recheck_blocks_numeric_microstructure_without_provenance(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True,
        EARLY_ACCEL_RECHECK_MAX_COUNT=2,
        EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC=20,
        EARLY_ACCEL_RECHECK_MAX_AGE_SEC=180,
        EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL=1.10,
        EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)

    result = _resolve_early_accel_recheck(
        {
            "position_tag": "SCANNER",
            "scanner_promotion_reason": "probe_acceleration_confirmed",
            "buy_price": 12280,
            "entry_armed_at_epoch": 100.0,
            "early_accel_recheck_count": 0,
        },
        {
            "curr": 12430,
            "tick_acceleration_ratio": 1.25,
            "curr_vs_micro_vwap_bp": 12.0,
            "quote_stale": False,
        },
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )

    assert result["allowed"] is False
    assert result["skip_reason"] == "micro_vwap_unusable"
    assert result["micro_vwap_usable"] is False
    assert result["tick_accel_usable"] is False


def test_early_accel_recheck_allows_scanner_price_jump_tier_a_reasons(monkeypatch):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True,
        EARLY_ACCEL_RECHECK_MAX_COUNT=2,
        EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC=20,
        EARLY_ACCEL_RECHECK_MAX_AGE_SEC=180,
        EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL=1.10,
        EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    ws_data = _trusted_pressure(
        {
            "curr": 12430,
            "tick_acceleration_ratio": 1.25,
            "curr_vs_micro_vwap_bp": 12.0,
            "quote_stale": False,
        }
    )

    for promotion_reason in (
        "price_jump_start_acceleration",
        "price_jump_multisource_confirmation",
    ):
        result = _resolve_early_accel_recheck(
            {
                "position_tag": "SCANNER",
                "scanner_promotion_reason": promotion_reason,
                "buy_price": 12280,
                "entry_armed_at_epoch": 100.0,
                "early_accel_recheck_count": 0,
            },
            ws_data,
            now_ts=130.0,
            last_ai_time=105.0,
            cooldown_sec=90,
            strategy="SCALPING",
            pos_tag="SCANNER",
            current_ai_score=64.0,
        )

        assert result["allowed"] is True
        assert result["scanner_promotion_reason"] == promotion_reason


def test_early_accel_recheck_blocks_stale_or_falling_context(monkeypatch):
    rules = replace(TRADING_RULES, EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True)
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "position_tag": "SCANNER",
        "buy_price": 12280,
        "entry_armed_at_epoch": 100.0,
    }
    stock["scanner_promotion_reason"] = "rank_jump_acceleration"

    falling = _resolve_early_accel_recheck(
        stock,
        {"curr": 12270, "tick_acceleration_ratio": 1.5, "curr_vs_micro_vwap_bp": 10.0},
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )
    assert falling["allowed"] is False
    assert falling["skip_reason"] == "price_below_promotion_anchor"

    stale = _resolve_early_accel_recheck(
        stock,
        {
            "curr": 12350,
            "tick_acceleration_ratio": 1.5,
            "curr_vs_micro_vwap_bp": 10.0,
            "quote_stale": True,
        },
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )
    assert stale["allowed"] is False
    assert stale["skip_reason"] == "stale_quote_or_context"

    missing_price = _resolve_early_accel_recheck(
        stock,
        {"tick_acceleration_ratio": 1.5, "curr_vs_micro_vwap_bp": 10.0},
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )
    assert missing_price["allowed"] is False
    assert missing_price["skip_reason"] == "missing_current_price"

    late_only = _resolve_early_accel_recheck(
        {**stock, "scanner_promotion_reason": "value_top_only_guard_disabled"},
        {"curr": 12350, "tick_acceleration_ratio": 1.5, "curr_vs_micro_vwap_bp": 10.0},
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )
    assert late_only["allowed"] is False
    assert late_only["skip_reason"] == "scanner_promotion_reason_not_early_accel"


def test_early_accel_recheck_hydrates_scanner_promotion_reason_from_pipeline_event(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True,
        EARLY_ACCEL_RECHECK_MAX_COUNT=2,
        EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC=20,
        EARLY_ACCEL_RECHECK_MAX_AGE_SEC=180,
        EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL=1.10,
        EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(
        handlers,
        "_load_scanner_promotion_context_events",
        lambda _target_date: {
            "111111": [
                {
                    "emitted_epoch": 100.0,
                    "fields": {
                        "scanner_promotion_reason": "probe_acceleration_confirmed",
                        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                        "price_delta_since_first_seen_pct": "0.55",
                        "comparable_flu_delta_since_first_seen": "0.62",
                        "cntr_str_available": "true",
                        "cntr_str": "118.0",
                    },
                }
            ]
        },
    )
    stock = {
        "code": "111111",
        "date": "2026-06-18",
        "position_tag": "SCANNER",
        "buy_price": 12280,
        "entry_armed_at_epoch": 100.0,
        "early_accel_recheck_count": 0,
    }

    result = _resolve_early_accel_recheck(
        stock,
        _trusted_pressure(
            {
                "curr": 12430,
                "tick_acceleration_ratio": 1.25,
                "curr_vs_micro_vwap_bp": 12.0,
                "quote_stale": False,
            }
        ),
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )

    assert result["allowed"] is True
    assert result["scanner_promotion_reason"] == "probe_acceleration_confirmed"
    assert stock["source_signature"] == "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"


def test_scanner_rising_strength_override_allows_exact_bid_imbalance_price_jump_case():
    stock = {
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": " bid_imbalance_surge , price_jump_start ",
        "price_delta_since_first_seen_pct": "1.53",
        "entry_armed_at_epoch": 100.0,
    }

    result = _resolve_scanner_rising_strength_momentum_override(
        stock,
        {"allowed": False, "reason": "below_strength_base"},
    )

    assert result["allowed"] is True
    assert (
        result["override_reason"] == "scanner_rising_bid_imbalance_strength_ai_recheck"
    )
    assert result["price_delta_since_first_seen_pct"] == "1.53"
    assert result["scanner_context_source"] == "stock_state"
    assert result["scanner_context_emitted_epoch"] == "100.000"


def test_scanner_rising_strength_override_allows_window_buy_value_recheck_case():
    stock = {
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "1.08",
        "entry_armed_at_epoch": 100.0,
    }

    result = _resolve_scanner_rising_strength_momentum_override(
        stock,
        {"allowed": False, "reason": "below_window_buy_value"},
    )

    assert result["allowed"] is True
    assert (
        result["override_reason"] == "scanner_rising_bid_imbalance_strength_ai_recheck"
    )
    assert result["original_reason"] == "below_window_buy_value"
    assert result["price_delta_since_first_seen_pct"] == "1.08"


def test_scanner_rising_strength_override_allows_window_buy_value_without_bid_imbalance():
    stock = {
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "1.08",
        "entry_armed_at_epoch": 100.0,
    }

    result = _resolve_scanner_rising_strength_momentum_override(
        stock,
        {"allowed": False, "reason": "below_window_buy_value"},
    )

    assert result["allowed"] is True
    assert result["original_reason"] == "below_window_buy_value"
    assert (
        result["source_signature"]
        == "PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE"
    )


def test_scanner_rising_strength_override_uses_latest_qualifying_event_when_stock_context_is_overwritten(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers,
        "_load_scanner_promotion_context_events",
        lambda _target_date: {
            "014950": [
                {
                    "emitted_epoch": 100.0,
                    "fields": {
                        "scanner_promotion_reason": "price_jump_start_acceleration",
                        "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START",
                        "price_delta_since_first_seen_pct": "1.53",
                    },
                },
                {
                    "emitted_epoch": 130.0,
                    "fields": {
                        "scanner_promotion_reason": "price_jump_start_acceleration",
                        "source_signature": "PRICE_JUMP_START",
                        "price_delta_since_first_seen_pct": "0.00",
                    },
                },
            ]
        },
    )
    stock = {
        "code": "014950",
        "date": "2026-06-19",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "0.00",
        "buy_price": 6700,
        "entry_armed_at_epoch": 130.0,
        "comparable_flu_delta_since_first_seen": "0.00",
        "cntr_str_available": False,
        "cntr_str": "0.0",
    }

    result = _resolve_scanner_rising_strength_momentum_override(
        stock,
        {"allowed": False, "reason": "below_strength_base"},
    )

    assert result["allowed"] is True
    assert result["scanner_context_source"] == "promotion_event_fallback"
    assert result["scanner_context_emitted_epoch"] == "100.000"
    assert result["price_delta_since_first_seen_pct"] == "1.53"


def test_scanner_rising_strength_override_requires_bid_imbalance_price_jump_and_delta():
    base_stock = {
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "1.53",
    }
    momentum_gate = {"allowed": False, "reason": "below_strength_base"}

    missing_bid_imbalance = _resolve_scanner_rising_strength_momentum_override(
        dict(base_stock),
        momentum_gate,
    )
    assert missing_bid_imbalance["allowed"] is False
    assert (
        missing_bid_imbalance["skip_reason"]
        == "source_signature_not_bid_imbalance_price_jump"
    )

    missing_volume_for_window_reason = (
        _resolve_scanner_rising_strength_momentum_override(
            dict(base_stock),
            {"allowed": False, "reason": "below_window_buy_value"},
        )
    )
    assert missing_volume_for_window_reason["allowed"] is False
    assert (
        missing_volume_for_window_reason["skip_reason"]
        == "source_signature_not_price_volume_multisource"
    )

    too_small_delta = _resolve_scanner_rising_strength_momentum_override(
        {
            **base_stock,
            "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "0.99",
        },
        momentum_gate,
    )
    assert too_small_delta["allowed"] is False
    assert too_small_delta["skip_reason"] == "price_delta_below_min"

    different_reason = _resolve_scanner_rising_strength_momentum_override(
        {**base_stock, "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START"},
        {"allowed": False, "reason": "insufficient_history"},
    )
    assert different_reason["allowed"] is False
    assert different_reason["skip_reason"] == "reason_not_scanner_rising_recheckable"


def test_scanner_rising_strength_override_respects_disable_flag(monkeypatch):
    rules = replace(
        TRADING_RULES, SCANNER_RISING_STRENGTH_PRE_AI_OVERRIDE_ENABLED=False
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    result = _resolve_scanner_rising_strength_momentum_override(
        {
            "position_tag": "SCANNER",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "1.53",
        },
        {"allowed": False, "reason": "below_strength_base"},
    )

    assert result["allowed"] is False
    assert result["skip_reason"] == "disabled"


def test_strength_momentum_stability_recheck_defers_unstable_scanner_window(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
        },
        {},
        {"reason": "below_window_buy_value"},
        {
            "stability_window_result": "single_snapshot_only",
            "tick_window_sample_count": 1,
            "tick_window_span_sec": 0.0,
        },
        now_ts=100.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "transient_strength_window_unstable"
    assert result["recheck_after_epoch"] == "102.000"
    assert result["recheck_attempt_count"] == 1


def test_strength_momentum_stability_recheck_extends_history_wait_for_rising_scanner(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STRENGTH_HISTORY_RECHECK_MAX_ATTEMPTS", "7"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STRENGTH_HISTORY_RECHECK_DELAY_SEC", "3"
    )

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "price_delta_since_first_seen_pct": "1.25",
        },
        {},
        {"reason": "insufficient_history"},
        {
            "stability_window_result": "not_available",
            "tick_window_sample_count": 0,
            "tick_window_span_sec": 0.0,
            "refresh_reason": "latest_snapshot_stale",
            "refresh_history_count": 120,
        },
        source_quality_block_reason="insufficient_history",
        now_ts=100.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "rising_strength_history_recheck_pending"
    assert result["recheck_max_attempts"] == 7
    assert result["recheck_after_epoch"] == "103.000"
    assert result["recheck_attempt_count"] == 1


def test_strength_momentum_stability_recheck_allows_strong_rising_min_history_ai_recheck(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=30,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_INSUFFICIENT_HISTORY_AI_RECHECK_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_INSUFFICIENT_HISTORY_AI_RECHECK_MIN_DELTA_PCT",
        "5.0",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_INSUFFICIENT_HISTORY_AI_RECHECK_MIN_SAMPLES", "2"
    )

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "source_signature": "BID_IMBALANCE_SURGE,OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE",
            "price_delta_since_first_seen_pct": "8.06",
        },
        {},
        {"reason": "insufficient_history"},
        {
            "quote_age_ms": 680.0,
            "refresh_reason": "latest_ws_snapshot_fresh",
            "refresh_age_ms": 680.0,
            "tick_sample_count": 2,
            "tick_window_sample_count": 2,
            "tick_window_span_sec": 0.001,
        },
        source_quality_block_reason="insufficient_history",
        now_ts=100.0,
    )

    assert result["pending"] is False
    assert result["reason"] == "rising_insufficient_history_ai_recheck_ready"
    assert result["recheck_ai_ready_sample_count"] == 2


def test_strength_momentum_stability_recheck_allows_rising_window_buy_value_ai_recheck(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
        SCANNER_RISING_STRENGTH_PRE_AI_OVERRIDE_ENABLED=True,
        SCANNER_RISING_STRENGTH_OVERRIDE_MIN_DELTA_PCT=1.0,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=30,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_INSUFFICIENT_HISTORY_AI_RECHECK_MIN_SAMPLES", "2"
    )

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "source_signature": "PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE",
            "price_delta_since_first_seen_pct": "1.35",
        },
        {},
        {"reason": "below_window_buy_value"},
        {
            "quote_age_ms": 250.0,
            "refresh_reason": "latest_ws_snapshot_fresh",
            "refresh_age_ms": 250.0,
            "tick_sample_count": 2,
            "tick_window_sample_count": 2,
            "tick_window_span_sec": 1.0,
        },
        now_ts=100.0,
    )

    assert result["pending"] is False
    assert result["reason"] == "rising_window_buy_value_ai_recheck_ready"
    assert result["recheck_ai_ready_reason"] == "strong_rising_window_value_ready"


def test_scanner_rising_strength_override_accepts_insufficient_history_only_when_enabled(
    monkeypatch,
):
    stock = {
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "OPEN_TOP,PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "8.06",
    }

    monkeypatch.delenv(
        "KORSTOCKSCAN_SCANNER_RISING_INSUFFICIENT_HISTORY_AI_RECHECK_ENABLED",
        raising=False,
    )
    disabled = _resolve_scanner_rising_strength_momentum_override(
        stock, {"allowed": False, "reason": "insufficient_history"}
    )
    assert disabled["allowed"] is False
    assert disabled["skip_reason"] == "reason_not_scanner_rising_recheckable"

    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_INSUFFICIENT_HISTORY_AI_RECHECK_ENABLED", "true"
    )
    enabled = _resolve_scanner_rising_strength_momentum_override(
        stock, {"allowed": False, "reason": "insufficient_history"}
    )
    assert enabled["allowed"] is True
    assert enabled["skip_reason"] == "allowed"


def test_strength_momentum_stability_recheck_keeps_non_rising_history_attempt_limit(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STRENGTH_HISTORY_RECHECK_MAX_ATTEMPTS", "7"
    )

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "price_delta_since_first_seen_pct": "0.00",
            "entry_strength_momentum_recheck_count": 1,
        },
        {},
        {"reason": "insufficient_history"},
        {"stability_window_result": "not_available"},
        source_quality_block_reason="insufficient_history",
        now_ts=100.0,
    )

    assert result["pending"] is False
    assert result["reason"] == "max_attempts_reached"
    assert result["recheck_max_attempts"] == 1


def test_pre_ai_blocked_gate_quality_reports_refresh_history_count():
    fields = _pre_ai_blocked_gate_quality_fields(
        gate_name="strength_momentum",
        ws_data={},
        gate_result={"window_sec": 5},
        refresh_fields={"pre_ai_ws_snapshot_refresh_history_count": 120},
    )

    assert fields["refresh_history_count"] == 120
    assert fields["stability_window_result"] == "not_available"


def test_strength_momentum_stability_recheck_keeps_stable_window_actionable(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MIN_WINDOW_SAMPLES=3,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MIN_WINDOW_SPAN_SEC=2.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
        },
        {},
        {"reason": "below_buy_ratio"},
        {
            "stability_window_result": "window_available",
            "tick_window_sample_count": 4,
            "tick_window_span_sec": 4.5,
        },
        now_ts=100.0,
    )

    assert result["pending"] is False
    assert result["reason"] == "window_already_stable"


def test_strength_momentum_stability_recheck_does_not_bypass_hard_source_quality():
    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
        },
        {},
        {"reason": "below_window_buy_value"},
        {"stability_window_result": "single_snapshot_only"},
        source_quality_block_reason="stale_ws_snapshot",
        now_ts=100.0,
    )

    assert result["pending"] is False
    assert result["reason"] == "source_quality_hard_block"


def test_strength_momentum_stability_recheck_defers_fresh_quote_stale_tick_window(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MIN_WINDOW_SAMPLES=3,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MIN_WINDOW_SPAN_SEC=2.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
        },
        {},
        {"reason": "below_window_buy_value"},
        {
            "quote_age_ms": 1020.043,
            "tick_latest_age_ms": 10184.841,
            "tick_window_sample_count": 2,
            "tick_window_span_sec": 4.245,
            "refresh_age_ms": 986.782,
            "refresh_reason": "latest_ws_snapshot_fresh",
            "stability_window_result": "window_available",
        },
        source_quality_block_reason="stale_ws_snapshot",
        now_ts=100.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "stale_strength_tick_window_recheck"
    assert result["recheck_after_epoch"] == "102.000"
    assert result["recheck_attempt_count"] == 1


def test_strength_momentum_stability_recheck_extends_stale_tick_wait_for_rising_scanner(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MIN_WINDOW_SAMPLES=3,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MIN_WINDOW_SPAN_SEC=2.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STRENGTH_HISTORY_RECHECK_MAX_ATTEMPTS", "5"
    )

    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "price_delta_since_first_seen_pct": "1.50",
            "entry_strength_momentum_recheck_count": 1,
        },
        {},
        {"reason": "below_window_buy_value"},
        {
            "quote_age_ms": 900.0,
            "tick_latest_age_ms": 4500.0,
            "tick_window_sample_count": 4,
            "tick_window_span_sec": 4.0,
            "refresh_age_ms": 900.0,
            "refresh_reason": "latest_ws_snapshot_fresh",
            "stability_window_result": "window_available",
        },
        source_quality_block_reason="stale_ws_snapshot",
        now_ts=100.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "stale_strength_tick_window_recheck"
    assert result["recheck_max_attempts"] == 5
    assert result["recheck_attempt_count"] == 2


def test_scanner_terminal_block_stale_source_quality_is_not_fresh_input():
    assert (
        _scanner_terminal_block_fresh_input_confirmed(
            {
                "reason": "below_window_buy_value",
                "source_quality_block_reason": "stale_ws_snapshot",
                "quote_age_ms": 900.0,
                "tick_latest_age_ms": 4500.0,
                "stability_window_result": "window_available",
            }
        )
        is False
    )


def test_strength_momentum_source_quality_blocks_stale_tick_window(monkeypatch):
    rules = SimpleNamespace(
        SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)

    reason = _strength_momentum_source_quality_block_reason(
        {
            "last_ws_update_ts": 99.8,
            "strength_momentum_history": [{"ts": 95.0}],
        },
        {
            "reason": "below_window_buy_value",
            "pre_ai_ws_snapshot_refresh_reason": "input_snapshot_fresh",
            "pre_ai_ws_snapshot_refresh_input_age_ms": 200.0,
        },
    )

    assert reason == "stale_ws_snapshot"


def test_strength_momentum_source_quality_splits_trade_tick_quiet_from_ws_stale(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
        SCANNER_TRADE_TICK_QUIET_NON_TRADE_WS_FRESH_SEC=10.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)

    reason = _strength_momentum_source_quality_block_reason(
        {
            "last_ws_update_ts": 99.8,
            "received_types": {"0B", "0D"},
            "last_realtime_type_ts": {"0B": 95.0, "0D": 99.7},
            "strength_momentum_history": [{"ts": 95.0}],
        },
        {
            "reason": "below_window_buy_value",
            "pre_ai_ws_snapshot_refresh_reason": "input_snapshot_fresh",
            "pre_ai_ws_snapshot_refresh_input_age_ms": 200.0,
        },
    )

    assert reason == "trade_tick_quiet"


def test_strength_momentum_source_quality_keeps_fresh_insufficient_history_recheckable(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)

    reason = _strength_momentum_source_quality_block_reason(
        {
            "last_ws_update_ts": 99.8,
            "strength_momentum_history": [],
        },
        {
            "reason": "insufficient_history",
            "pre_ai_ws_snapshot_refresh_reason": "input_snapshot_fresh",
            "pre_ai_ws_snapshot_refresh_input_age_ms": 200.0,
        },
    )

    assert reason == "insufficient_history"


def test_strength_momentum_stability_recheck_keeps_trade_tick_quiet_without_ws_recovery(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_REASONS="below_window_buy_value",
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)

    result = _strength_momentum_stability_recheck_decision(
        {
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "price_delta_since_first_seen_pct": 0.6,
        },
        {},
        {"reason": "below_window_buy_value"},
        {
            "quote_age_ms": 200.0,
            "tick_latest_age_ms": 5000.0,
            "refresh_reason": "input_snapshot_fresh",
        },
        source_quality_block_reason="trade_tick_quiet",
        now_ts=100.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "trade_tick_quiet_recheck_pending"


def test_strength_momentum_stability_recheck_keeps_rising_base_quiet_window(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_ENABLED=True,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_REASONS="below_window_buy_value",
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_MAX_ATTEMPTS=1,
        SCANNER_STRENGTH_MOMENTUM_STABILITY_RECHECK_DELAY_SEC=2,
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STRENGTH_HISTORY_RECHECK_MAX_ATTEMPTS", "5"
    )

    result = _strength_momentum_stability_recheck_decision(
        {
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "price_delta_since_first_seen_pct": 16.48,
        },
        {},
        {"reason": "below_strength_base"},
        {
            "quote_age_ms": 75.0,
            "tick_latest_age_ms": 3671.0,
            "refresh_age_ms": 70.0,
            "refresh_reason": "latest_ws_snapshot_fresh",
            "stability_window_result": "window_available",
            "tick_window_sample_count": 16,
            "tick_window_span_sec": 7.8,
        },
        source_quality_block_reason="trade_tick_quiet",
        now_ts=100.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "trade_tick_quiet_recheck_pending"
    assert result["recheck_max_attempts"] == 5


def test_strength_momentum_source_quality_does_not_block_fresh_base_on_refresh_failure(
    monkeypatch,
):
    rules = SimpleNamespace(
        SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
        SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(handlers.time, "time", lambda: 100.0)

    reason = _strength_momentum_source_quality_block_reason(
        {
            "last_ws_update_ts": 98.8,
            "strength_momentum_history": [{"ts": 99.0}, {"ts": 99.5}],
        },
        {
            "reason": "below_window_buy_value",
            "pre_ai_ws_snapshot_refresh_reason": "ws_manager_missing",
        },
    )

    assert reason == ""


def test_strength_momentum_stability_recheck_waits_until_recheck_epoch():
    result = _strength_momentum_stability_recheck_decision(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 90.0,
            "entry_strength_momentum_recheck_pending": True,
            "entry_strength_momentum_recheck_count": 1,
            "entry_strength_momentum_recheck_after_epoch": 102.0,
        },
        {},
        {"reason": "below_window_buy_value"},
        {"stability_window_result": "single_snapshot_only"},
        now_ts=101.0,
    )

    assert result["pending"] is True
    assert result["reason"] == "waiting_for_recheck_after_epoch"
    assert result["recheck_after_epoch"] == "102.000"
    assert result["recheck_attempt_count"] == 1


def test_strength_momentum_stability_recheck_requires_promoted_scanner_epoch():
    result = _strength_momentum_stability_recheck_decision(
        {"strategy": "SCALPING", "position_tag": "SCANNER"},
        {},
        {"reason": "insufficient_history"},
        {"stability_window_result": "not_available"},
        source_quality_block_reason="insufficient_history",
        now_ts=100.0,
    )

    assert result["pending"] is False
    assert result["reason"] == "missing_scanner_promotion_epoch"


def test_entry_adm_snapshot_records_feature_parity_and_numeric_consistency(monkeypatch):
    logs = []

    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 7,
        "name": "TEST",
        "strategy": "SCALPING",
        "scalp_pre_ai_gate_context": {},
        "last_watching_ai_source_quality_fields": {
            "tick_acceleration_ratio": "24.000",
            "tick_acceleration_ratio_raw": "0.000",
            "tick_accel_source": "same_second_burst_10ticks",
            "recent_5tick_seconds": "0.000",
            "prev_5tick_seconds": "24.000",
            "tick_accel_effective_recent_5tick_seconds": "1.000",
            "buy_pressure_10t": "71.200",
            "curr_vs_micro_vwap_bp": "11.400",
            "curr_vs_ma5_bp": "9.800",
        },
    }
    handlers._emit_scalp_entry_adm_snapshot(
        stock,
        "123456",
        "ai_confirmed",
        ai_decision={
            "action": "WAIT",
            "score": 62,
            "reason": "Speed advantage not strong enough: tick_acceleration_ratio = 24.0 fails < 1.10",
            "ai_reason_numeric_inconsistency": True,
            "ai_reason_numeric_inconsistency_field": "tick_acceleration_ratio",
            "ai_reason_numeric_inconsistency_reason": "tick_acceleration_pass_described_as_fail",
            "ai_reason_numeric_inconsistency_detected_value": 24.0,
            "ai_reason_numeric_inconsistency_excerpt": "tick_acceleration_ratio = 24.0 fails < 1.10",
        },
        chosen_action="NO_BUY_AI",
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )

    stage, fields = logs[0]
    assert stage == "scalp_entry_action_decision_snapshot"
    assert fields["tick_acceleration_ratio"] == "24.000"
    assert fields["tick_acceleration_ratio_raw"] == "0.000"
    assert fields["tick_accel_source"] == "same_second_burst_10ticks"
    assert fields["buy_pressure_10t"] == "71.200"
    assert fields["curr_vs_micro_vwap_bp"] == "11.400"
    assert fields["curr_vs_ma5_bp"] == "9.800"
    assert fields["micro_vwap_available"] is False
    assert fields["minute_candle_context_quality"] == "unavailable_fail_closed"
    assert fields["minute_candle_window_fresh"] is False
    assert fields["minute_candle_latest_age_ms"] == -1.0
    assert fields["minute_candle_evaluation_state"] == "unavailable_fail_closed"
    assert fields["ai_reason_numeric_inconsistency"] is True
    assert fields["source_quality_gate"] == "ai_numeric_consistency_review_required"
    assert fields["allowed_runtime_apply"] is False
    assert "runtime-apply" in fields["forbidden_uses"]


def test_entry_adm_snapshot_preserves_minute_candle_provenance(monkeypatch):
    logs = []

    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 8,
        "name": "TEST",
        "strategy": "SCALPING",
        "scalp_pre_ai_gate_context": {},
        "last_watching_ai_source_quality_fields": {
            "curr_vs_micro_vwap_bp": "11.400",
            "micro_vwap_available": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": True,
            "minute_candle_latest_age_ms": 12000,
        },
    }
    handlers._emit_scalp_entry_adm_snapshot(
        stock,
        "123456",
        "ai_confirmed",
        ai_decision={"action": "WAIT", "score": 62},
        chosen_action="NO_BUY_AI",
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )

    stage, fields = logs[0]
    assert stage == "scalp_entry_action_decision_snapshot"
    assert fields["curr_vs_micro_vwap_bp"] == "11.400"
    assert fields["micro_vwap_available"] is True
    assert fields["minute_candle_context_quality"] == "fresh_bar_window"
    assert fields["minute_candle_window_fresh"] is True
    assert fields["minute_candle_latest_age_ms"] == 12000


def test_ai_ops_log_fields_preserve_tick_acceleration_ratio_raw_precision():
    fields = handlers._build_ai_ops_log_fields(
        {
            "tick_acceleration_ratio_raw": "1.875",
            "tick_acceleration_ratio": "2.000",
            "recent_5tick_seconds": "1.250",
            "prev_5tick_seconds": "2.500",
            "tick_accel_effective_recent_5tick_seconds": "1.250",
        }
    )

    assert fields["tick_acceleration_ratio_raw"] == "1.875"
    assert fields["tick_acceleration_ratio"] == "2.000"


def test_reversal_feature_payload_preserves_minute_candle_age():
    payload = handlers._reversal_feature_payload(
        {
            "minute_candle_latest_age_ms": 12000,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": True,
        },
        100.0,
    )

    assert payload["minute_candle_latest_age_ms"] == 12000


def test_scalp_entry_snapshot_marks_final_submit_safety_block(monkeypatch):
    logs = []

    def fake_emit(event_type, stock_name, code, stage, *, record_id=None, fields=None):
        logs.append((event_type, stock_name, code, stage, record_id, fields or {}))

    monkeypatch.setattr(handlers, "emit_pipeline_event", fake_emit)

    stock = {
        "id": "R-WEAK-MICRO",
        "name": "가온전선",
        "strategy": "SCALPING",
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 50.0,
    }
    handlers._emit_scalp_entry_adm_snapshot(
        stock,
        "000500",
        "real_weak_ai_micro_entry_block",
        ai_score=50.0,
        chosen_action="NO_BUY_AI",
        latency_gate={
            "allowed": True,
            "decision": "ALLOW_NORMAL",
            "reason": "safe_normal_entry_allowed",
            "latency_state": "SAFE",
        },
        orderbook_fields={
            "orderbook_micro_state": "neutral",
            "orderbook_micro_ofi_norm": "0.0389",
            "orderbook_micro_qi": "0.2873",
        },
        actual_order_submitted=False,
        broker_order_forbidden=True,
        extra_fields={
            "blocked": True,
            "runtime_effect": True,
            "block_reason": "source_quality_unknown",
            "weak_ai_micro_entry_block_missing_fields": "buy_pressure_10t",
            "weak_ai_micro_entry_block_buy_pressure_10t": "-",
        },
    )

    assert logs
    event_type, _name, _code, stage, record_id, fields = logs[0]
    assert event_type == "ENTRY_PIPELINE"
    assert stage == "scalp_entry_action_decision_snapshot"
    assert record_id == "R-WEAK-MICRO"
    assert fields["source_stage"] == "real_weak_ai_micro_entry_block"
    assert fields["entry_action_latency_reason"] == "safe_normal_entry_allowed"
    assert fields["entry_action_final_decision"] == "BLOCKED"
    assert fields["entry_action_final_blocked"] is True
    assert fields["entry_action_final_block_reason"] == "source_quality_unknown"
    assert fields["buy_pressure_10t"] == "not_evaluated_runtime_block"
    assert fields["tick_acceleration_ratio"] == "not_evaluated"
    assert fields["tick_acceleration_ratio_raw"] == "not_evaluated"
    assert fields["recent_5tick_seconds"] == "not_evaluated"
    assert fields["prev_5tick_seconds"] == "not_evaluated"
    assert fields["tick_accel_effective_recent_5tick_seconds"] == "not_evaluated"
    assert fields["weak_ai_micro_entry_block_buy_pressure_10t"] == "-"


def test_scalp_entry_snapshot_marks_runtime_submit_when_ai_wait(monkeypatch):
    logs = []

    def fake_emit(event_type, stock_name, code, stage, *, record_id=None, fields=None):
        logs.append((event_type, stock_name, code, stage, record_id, fields or {}))

    monkeypatch.setattr(handlers, "emit_pipeline_event", fake_emit)

    stock = {
        "id": "R-PEPT",
        "name": "펩트론",
        "strategy": "SCALPING",
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 0.0,
    }
    handlers._emit_scalp_entry_adm_snapshot(
        stock,
        "087010",
        "order_bundle_submitted",
        ai_decision={
            "action": "WAIT",
            "score": 0.0,
            "reason": "no_directional_buy_authority",
        },
        ai_score=0.0,
        chosen_action="BUY_DEFENSIVE",
        latency_gate={
            "allowed": True,
            "decision": "ALLOW_NORMAL",
            "reason": "caution_normal_entry_allowed",
            "latency_state": "CAUTION",
            "ai_entry_price_canary_action": "USE_DEFENSIVE",
            "entry_price_guard": "defensive_price_selected",
        },
        actual_order_submitted=True,
        broker_order_forbidden=False,
        extra_fields={"reason": "order_submitted"},
    )

    assert logs
    fields = logs[0][5]
    assert fields["entry_action_final_decision"] == "SUBMITTED"
    assert fields["entry_action_submit_authority"] == "runtime_submit_policy"
    assert (
        fields["entry_action_submit_authority_reason"] == "caution_normal_entry_allowed"
    )
    assert fields["entry_action_ai_directional_authority"] == "observed_context_only"
    assert fields["entry_action_ai_directional_allowed"] is False
    assert fields["entry_action_ai_directional_mismatch"] is True
    assert fields["entry_action_price_ai_authority"] == "entry_price_ai_price_selection"
    assert fields["entry_action_price_ai_action"] == "USE_DEFENSIVE"
    assert fields["entry_action_final_reason_detail"] == (
        "submitted_by_runtime_policy_despite_directional_ai_not_buy"
    )


def test_ai_ops_log_fields_mark_numeric_inconsistency_as_no_runtime_authority():
    fields = handlers._build_ai_ops_log_fields(
        {
            "ai_reason_numeric_inconsistency": "true",
            "ai_reason_feature_inconsistency": "true",
            "ai_reason_numeric_inconsistency_field": "tick_acceleration_ratio",
            "ai_reason_numeric_inconsistency_reason": "tick_acceleration_pass_described_as_fail",
            "ai_reason_numeric_inconsistency_excerpt": "tick_acceleration_ratio = 24.0 fails < 1.10",
        }
    )

    assert fields["ai_reason_numeric_inconsistency"] is True
    assert fields["ai_reason_feature_inconsistency"] is True
    assert fields["source_quality_gate"] == "ai_numeric_consistency_review_required"
    assert fields["allowed_runtime_apply"] is False
    assert "runtime-apply" in fields["forbidden_uses"]
    assert "broker order submit" in fields["forbidden_uses"]


def test_early_accel_recheck_blocks_scope_and_limits(monkeypatch):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True,
        EARLY_ACCEL_RECHECK_MAX_COUNT=2,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "position_tag": "VWAP_RECLAIM",
        "scanner_promotion_reason": "probe_acceleration_confirmed",
        "buy_price": 12280,
        "entry_armed_at_epoch": 100.0,
        "early_accel_recheck_count": 2,
    }
    not_scanner = _resolve_early_accel_recheck(
        stock,
        {"curr": 12430, "tick_acceleration_ratio": 1.25, "curr_vs_micro_vwap_bp": 12.0},
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="VWAP_RECLAIM",
        current_ai_score=64.0,
    )
    assert not_scanner["allowed"] is False
    assert not_scanner["skip_reason"] == "scope_not_real_scalping_scanner"

    stock["position_tag"] = "SCANNER"
    max_count = _resolve_early_accel_recheck(
        stock,
        {"curr": 12430, "tick_acceleration_ratio": 1.25, "curr_vs_micro_vwap_bp": 12.0},
        now_ts=130.0,
        last_ai_time=105.0,
        cooldown_sec=90,
        strategy="SCALPING",
        pos_tag="SCANNER",
        current_ai_score=64.0,
    )
    assert max_count["allowed"] is False
    assert max_count["skip_reason"] == "max_recheck_count_reached"


def test_ai_numeric_consistency_recheck_allows_real_scalping_feature_bundle(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED=True,
        AI_NUMERIC_CONSISTENCY_RECHECK_MIN_SCORE=60,
        AI_NUMERIC_CONSISTENCY_RECHECK_BUY_MIN_SCORE=75,
        AI_NUMERIC_CONSISTENCY_RECHECK_MIN_FEATURE_PASS_COUNT=3,
        AI_NUMERIC_CONSISTENCY_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {"strategy": "SCALPING", "ai_numeric_consistency_recheck_count": 0}
    decision = {
        "action": "WAIT",
        "score": 72,
        "reason": "tick_acceleration_ratio >= 1.10 but described as failed",
        "ai_reason_numeric_inconsistency": True,
        "ai_reason_numeric_inconsistency_field": "tick_acceleration_ratio",
        "ai_reason_numeric_inconsistency_reason": "tick_acceleration_pass_described_as_fail",
        "tick_acceleration_ratio": 1.25,
        "buy_pressure_10t": 71.0,
        "net_aggressive_delta_10t": 1200.0,
        "tick_aggressor_trusted_count": 4,
        "tick_aggressor_pressure_usable": True,
        "curr_vs_micro_vwap_bp": 8.0,
        "curr_vs_ma5_bp": 4.0,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 9000,
    }

    result = _resolve_ai_numeric_consistency_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        now_ts=100.0,
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=72.0,
    )

    assert result["allowed"] is True
    assert result["feature_pass_count"] == 3
    assert result["skip_reason"] == "allowed"


def test_ai_numeric_consistency_recheck_records_two_feature_candidate_only(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED=True,
        AI_NUMERIC_CONSISTENCY_RECHECK_MIN_SCORE=60,
        AI_NUMERIC_CONSISTENCY_RECHECK_MIN_FEATURE_PASS_COUNT=3,
        AI_NUMERIC_CONSISTENCY_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    decision = {
        "action": "WAIT",
        "score": 68,
        "reason": "position and supply pass but stated as absent",
        "ai_reason_numeric_inconsistency": True,
        "ai_reason_numeric_inconsistency_field": "position_advantage",
        "ai_reason_numeric_inconsistency_reason": "position_pass_described_as_fail",
        "tick_acceleration_ratio": 0.95,
        "buy_pressure_10t": 75.0,
        "net_aggressive_delta_10t": 500.0,
        "tick_aggressor_trusted_count": 3,
        "tick_aggressor_pressure_usable": True,
        "curr_vs_micro_vwap_bp": 6.0,
        "curr_vs_ma5_bp": -1.0,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 9000,
    }

    result = _resolve_ai_numeric_consistency_recheck(
        {"strategy": "SCALPING"},
        {"quote_stale": False},
        now_ts=100.0,
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=68.0,
    )

    assert result["allowed"] is False
    assert result["feature_pass_count"] == 2
    assert result["skip_reason"] == "strong_micro_override_candidate_only"


def test_ai_numeric_consistency_recheck_allows_two_feature_bundle_when_runtime_floor_is_two(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED=True,
        AI_NUMERIC_CONSISTENCY_RECHECK_MIN_SCORE=65,
        AI_NUMERIC_CONSISTENCY_RECHECK_MIN_FEATURE_PASS_COUNT=2,
        AI_NUMERIC_CONSISTENCY_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    decision = {
        "action": "WAIT",
        "score": 68,
        "reason": "position and supply pass but text says weak",
        "ai_reason_numeric_inconsistency": True,
        "ai_reason_numeric_inconsistency_field": "position_advantage",
        "ai_reason_numeric_inconsistency_reason": "positive_numeric_fields_described_as_weak",
        "tick_acceleration_ratio": 0.95,
        "buy_pressure_10t": 75.0,
        "net_aggressive_delta_10t": 500.0,
        "tick_aggressor_trusted_count": 3,
        "tick_aggressor_pressure_usable": True,
        "curr_vs_micro_vwap_bp": 6.0,
        "curr_vs_ma5_bp": -1.0,
        "micro_vwap_available": True,
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": True,
        "minute_candle_latest_age_ms": 9000,
    }

    result = _resolve_ai_numeric_consistency_recheck(
        {"strategy": "SCALPING"},
        {"quote_stale": False},
        now_ts=100.0,
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=68.0,
    )

    assert result["allowed"] is True
    assert result["feature_pass_count"] == 2
    assert result["skip_reason"] == "allowed"


def test_ai_numeric_consistency_recheck_blocks_sim_and_stale_scope(monkeypatch):
    rules = replace(TRADING_RULES, AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED=True)
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    decision = {
        "action": "WAIT",
        "score": 72,
        "reason": "speed fail despite pass",
        "ai_reason_numeric_inconsistency": True,
        "tick_acceleration_ratio": 1.25,
        "buy_pressure_10t": 71.0,
        "net_aggressive_delta_10t": 1200.0,
        "curr_vs_micro_vwap_bp": 8.0,
        "curr_vs_ma5_bp": 4.0,
    }

    stale = _resolve_ai_numeric_consistency_recheck(
        {"strategy": "SCALPING"},
        {"quote_stale": True},
        now_ts=100.0,
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=72.0,
    )
    assert stale["allowed"] is False
    assert stale["skip_reason"] == "stale_quote_or_context"

    sim = _resolve_ai_numeric_consistency_recheck(
        {
            "strategy": "SCALPING",
            "scalp_live_simulator": True,
            "broker_order_forbidden": True,
        },
        {"quote_stale": False},
        now_ts=100.0,
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=72.0,
    )
    assert sim["allowed"] is False
    assert sim["skip_reason"] == "sim_or_probe_scope"


def test_early_accel_strong_bundle_recheck_allows_strong_scanner_bundle(monkeypatch):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE=66,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_BUY_MIN_SCORE=75,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=2,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "0.62",
        "comparable_flu_delta_since_first_seen": "0.71",
        "cntr_str_available": True,
        "cntr_str": 118.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 62,
            "tick_acceleration_ratio": 1.18,
            "curr_vs_micro_vwap_bp": 7.5,
            "buy_pressure_10t": 70.0,
        }
    )

    result = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=62.0,
    )

    assert result["allowed"] is True
    assert result["strong_bundle_pass_count"] >= 2
    assert result["skip_reason"] == "allowed"


def test_early_accel_strong_bundle_recheck_does_not_count_micro_vwap_without_provenance(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE=74,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=3,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "0.10",
        "comparable_flu_delta_since_first_seen": "0.10",
        "cntr_str_available": False,
        "cntr_str": 0.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    decision = {
        "action": "WAIT",
        "score": 68,
        "tick_acceleration_ratio": 0.90,
        "curr_vs_micro_vwap_bp": 12.0,
        "buy_pressure_10t": 71.0,
        "tick_aggressor_trusted_count": 3,
        "tick_aggressor_pressure_usable": True,
    }

    result = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=68.0,
    )

    assert result["strong_bundle_pass_count"] == 2
    assert result["micro_vwap_available"] is False
    assert result["minute_candle_window_fresh"] is False
    assert result["allowed"] is False
    assert result["skip_reason"] == "strong_bundle_below_min_pass_count"


def test_early_accel_strong_bundle_recheck_counts_micro_vwap_with_fresh_provenance(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE=74,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=3,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "0.10",
        "comparable_flu_delta_since_first_seen": "0.10",
        "cntr_str_available": False,
        "cntr_str": 0.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 68,
            "tick_acceleration_ratio": 0.90,
            "curr_vs_micro_vwap_bp": 12.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_latest_age_ms": 12000,
            "buy_pressure_10t": 71.0,
        }
    )

    result = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=68.0,
    )

    assert result["strong_bundle_pass_count"] == 3
    assert result["micro_vwap_available"] is True
    assert result["minute_candle_window_fresh"] is True
    assert result["allowed"] is True
    assert result["skip_reason"] == "allowed"


def test_early_accel_strong_bundle_recheck_default_includes_score_67_74(monkeypatch):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=2,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "late_confirmation_first_seen_probe",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "0.70",
        "comparable_flu_delta_since_first_seen": "0.82",
        "cntr_str_available": True,
        "cntr_str": 121.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 72,
            "tick_acceleration_ratio": 1.18,
            "curr_vs_micro_vwap_bp": 7.5,
            "buy_pressure_10t": 70.0,
        }
    )

    result = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=72.0,
    )

    assert result["allowed"] is True
    assert result["skip_reason"] == "allowed"


def test_early_accel_strong_bundle_recheck_allows_value_volume_rank_without_price_jump(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=2,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "late_confirmation_first_seen_probe",
        "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "0.12",
        "comparable_flu_delta_since_first_seen": "0.20",
        "cntr_str_available": False,
        "cntr_str": 0.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 62,
            "tick_acceleration_ratio": 1.0,
            "curr_vs_micro_vwap_bp": 1.2,
            "buy_pressure_10t": 70.0,
        }
    )

    result = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=62.0,
    )

    assert result["allowed"] is True
    assert result["skip_reason"] == "allowed"


def test_early_accel_strong_bundle_recheck_skips_weak_or_out_of_band_candidates(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE=66,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=2,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    weak_stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "new_price_jump_start_source",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "0.10",
        "comparable_flu_delta_since_first_seen": "0.10",
        "cntr_str_available": False,
        "cntr_str": 0.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    weak_decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 62,
            "tick_acceleration_ratio": 0.95,
            "curr_vs_micro_vwap_bp": -1.0,
            "buy_pressure_10t": 50.0,
        }
    )
    weak = _resolve_early_accel_strong_bundle_recheck(
        weak_stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=weak_decision,
        ai_score=62.0,
    )
    assert weak["allowed"] is False
    assert weak["skip_reason"] == "strong_bundle_below_min_pass_count"

    low_score = _resolve_early_accel_strong_bundle_recheck(
        weak_stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision={**weak_decision, "score": 58},
        ai_score=58.0,
    )
    assert low_score["allowed"] is False
    assert low_score["skip_reason"] == "strong_bundle_below_min_pass_count"
    assert low_score["score_gate_converted_to_prior"] is True
    assert low_score["score_prior_band"] == "low"
    assert low_score["hard_gate_veto"] is False

    high_score = _resolve_early_accel_strong_bundle_recheck(
        weak_stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision={**weak_decision, "score": 67},
        ai_score=67.0,
    )
    assert high_score["allowed"] is False
    assert high_score["skip_reason"] == "strong_bundle_below_min_pass_count"
    assert high_score["score_gate_converted_to_prior"] is True
    assert high_score["score_prior_band"] == "high"
    assert high_score["hard_gate_veto"] is False


def test_early_accel_strong_bundle_recheck_skips_scope_and_safety_blocks(monkeypatch):
    rules = replace(TRADING_RULES, EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True)
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 62,
            "tick_acceleration_ratio": 1.20,
            "curr_vs_micro_vwap_bp": 4.0,
            "buy_pressure_10t": 70.0,
        }
    )
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_reason": "probe_acceleration_confirmed",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "0.60",
        "comparable_flu_delta_since_first_seen": "0.60",
        "cntr_str_available": True,
        "cntr_str": 120.0,
        "scalp_pre_ai_gate_context": {
            "source_quality": {"gate_action": "source_quality_block"}
        },
    }

    stale = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": True},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=62.0,
    )
    assert stale["allowed"] is False
    assert stale["skip_reason"] == "stale_quote_or_context"

    source_quality = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=62.0,
    )
    assert source_quality["allowed"] is False
    assert source_quality["skip_reason"] == "source_quality_hard_block"

    sim = _resolve_early_accel_strong_bundle_recheck(
        {**stock, "scalp_live_simulator": True, "broker_order_forbidden": True},
        {"quote_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=62.0,
    )
    assert sim["allowed"] is False
    assert sim["skip_reason"] == "sim_or_probe_scope"


def test_early_accel_strong_bundle_recheck_hydrates_scanner_bundle_from_pipeline_event(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED=True,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE=60,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE=66,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_BUY_MIN_SCORE=75,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT=2,
        EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL=1,
    )
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(
        handlers,
        "_load_scanner_promotion_context_events",
        lambda _target_date: {
            "222222": [
                {
                    "emitted_epoch": 100.0,
                    "fields": {
                        "scanner_promotion_reason": "price_jump_start_acceleration",
                        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                        "price_delta_since_first_seen_pct": "0.62",
                        "comparable_flu_delta_since_first_seen": "0.71",
                        "cntr_str_available": "true",
                        "cntr_str": "118.0",
                    },
                }
            ]
        },
    )
    stock = {
        "code": "222222",
        "date": "2026-06-18",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 100.0,
        "early_accel_strong_bundle_recheck_count": 0,
    }
    decision = _trusted_pressure(
        {
            "action": "WAIT",
            "score": 62,
            "tick_acceleration_ratio": 1.18,
            "curr_vs_micro_vwap_bp": 7.5,
            "buy_pressure_10t": 70.0,
        }
    )

    result = _resolve_early_accel_strong_bundle_recheck(
        stock,
        {"quote_stale": False, "context_stale": False},
        strategy="SCALPING",
        ai_decision=decision,
        ai_score=62.0,
    )

    assert result["allowed"] is True
    assert result["scanner_promotion_reason"] == "price_jump_start_acceleration"
    assert result["strong_bundle_pass_count"] >= 2
    assert stock["price_delta_since_first_seen_pct"] == "0.62"


def test_scalping_entry_blocker_role_registry_marks_score6574_micro_as_runtime_gate():
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["blocked_gap_from_scan"]["role"]
        == "baseline_prior_feature"
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["blocked_gap_from_scan"][
            "hard_block_allowed"
        ]
        is False
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["score65_74_recovery_probe_micro_context"][
            "gate_action"
        ]
        == "runtime_min_micro_gate"
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["score65_74_recovery_probe_micro_context"][
            "hard_block_allowed"
        ]
        is True
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["main_buy_recovery_canary_micro_context"][
            "hard_block_allowed"
        ]
        is False
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["latency_danger"]["hard_block_allowed"]
        is True
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["stale_quote_or_context"][
            "hard_block_allowed"
        ]
        is True
    )


def test_gatekeeper_fast_signature_absorbs_small_price_and_orderbook_noise():
    stock = {"position_tag": "SCANNER"}
    ws_a = {
        "curr": 12570,
        "fluctuation": 3.42,
        "volume": 1854321,
        "v_pw": 118.1,
        "buy_ratio": 62.4,
        "prog_net_qty": 18490,
        "prog_delta_qty": 2210,
        "ask_tot": 184200,
        "bid_tot": 218700,
        "net_bid_depth": 11880,
        "net_ask_depth": -3420,
        "orderbook": {
            "asks": [{"price": 12590}, {"price": 12600}],
            "bids": [{"price": 12570}, {"price": 12560}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update(
        {
            "curr": 12610,
            "volume": 1949999,
            "v_pw": 119.4,
            "buy_ratio": 67.9,
            "prog_net_qty": 20510,
            "prog_delta_qty": 4880,
            "ask_tot": 199999,
            "bid_tot": 241000,
        }
    )
    ws_b["orderbook"] = {
        "asks": [{"price": 12620}, {"price": 12630}],
        "bids": [{"price": 12600}, {"price": 12590}],
    }

    sig_a = _build_gatekeeper_fast_signature(stock, ws_a, "KOSPI_ML", 86.0)
    sig_b = _build_gatekeeper_fast_signature(stock, ws_b, "KOSPI_ML", 87.9)

    assert sig_a == sig_b


def test_gatekeeper_fast_signature_absorbs_buy_ratio_band_noise():
    stock = {"position_tag": "SCANNER"}
    ws_a = {
        "curr": 12570,
        "fluctuation": 3.42,
        "volume": 1854321,
        "v_pw": 118.1,
        "buy_ratio": 71.9,
        "prog_net_qty": 18490,
        "prog_delta_qty": 2210,
        "ask_tot": 184200,
        "bid_tot": 218700,
        "net_bid_depth": 11880,
        "net_ask_depth": -3420,
        "orderbook": {
            "asks": [{"price": 12590}, {"price": 12580}],
            "bids": [{"price": 12570}, {"price": 12560}],
        },
    }
    ws_b = dict(ws_a)
    ws_b["buy_ratio"] = 79.9

    sig_a = _build_gatekeeper_fast_signature(stock, ws_a, "KOSPI_ML", 82.0)
    sig_b = _build_gatekeeper_fast_signature(stock, ws_b, "KOSPI_ML", 82.0)

    assert sig_a == sig_b


def test_gatekeeper_fast_signature_ignores_small_signed_program_flow_noise():
    stock = {"position_tag": "SCANNER"}
    ws_a = {
        "curr": 767,
        "fluctuation": 1.0,
        "volume": 100000,
        "v_pw": 100.0,
        "buy_ratio": 56.0,
        "prog_net_qty": 1000,
        "prog_delta_qty": 0,
        "ask_tot": 1000,
        "bid_tot": 1000,
        "net_bid_depth": 0,
        "net_ask_depth": 0,
        "orderbook": {
            "asks": [{"price": 768}],
            "bids": [{"price": 767}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update(
        {
            "curr": 766,
            "prog_net_qty": -10,
            "prog_delta_qty": -1,
        }
    )
    ws_b["orderbook"] = {
        "asks": [{"price": 767}],
        "bids": [{"price": 766}],
    }

    sig_a = _build_gatekeeper_fast_signature(stock, ws_a, "KOSPI_ML", 65.0)
    sig_b = _build_gatekeeper_fast_signature(stock, ws_b, "KOSPI_ML", 65.0)

    assert sig_a == sig_b


def test_gatekeeper_fast_signature_keeps_large_program_flow_shift_sensitive():
    stock = {"position_tag": "SCANNER"}
    ws_a = {
        "curr": 767,
        "fluctuation": 1.0,
        "volume": 100000,
        "v_pw": 100.0,
        "buy_ratio": 56.0,
        "prog_net_qty": 1000,
        "prog_delta_qty": 0,
        "ask_tot": 1000,
        "bid_tot": 1000,
        "net_bid_depth": 0,
        "net_ask_depth": 0,
        "orderbook": {
            "asks": [{"price": 768}],
            "bids": [{"price": 767}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update(
        {
            "prog_net_qty": 30000,
            "prog_delta_qty": 6000,
        }
    )

    sig_a = _build_gatekeeper_fast_signature(stock, ws_a, "KOSPI_ML", 65.0)
    sig_b = _build_gatekeeper_fast_signature(stock, ws_b, "KOSPI_ML", 65.0)

    assert sig_a != sig_b


def test_holding_ai_fast_signature_changes_on_meaningful_orderbook_shift():
    ws_a = {
        "curr": 10000,
        "fluctuation": 1.5,
        "v_pw": 122.0,
        "buy_ratio": 61.0,
        "ask_tot": 90000,
        "bid_tot": 120000,
        "net_bid_depth": 7000,
        "net_ask_depth": -2000,
        "buy_exec_volume": 4000,
        "sell_exec_volume": 2000,
        "tick_trade_value": 26000,
        "orderbook": {
            "asks": [{"price": 10020}, {"price": 10010}],
            "bids": [{"price": 10000}, {"price": 9990}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update(
        {
            "curr": 10120,
            "buy_ratio": 74.0,
            "ask_tot": 150000,
            "bid_tot": 80000,
        }
    )
    ws_b["orderbook"] = {
        "asks": [{"price": 10140}, {"price": 10130}],
        "bids": [{"price": 10120}, {"price": 10110}],
    }

    sig_a = _build_holding_ai_fast_signature(ws_a)
    sig_b = _build_holding_ai_fast_signature(ws_b)

    assert sig_a != sig_b


def test_holding_ai_fast_reuse_sec_tracks_review_window():
    assert _resolve_holding_ai_fast_reuse_sec(True, 10) == 12.0
    assert _resolve_holding_ai_fast_reuse_sec(False, 50) == 52.0


def test_gatekeeper_fast_reuse_sec_has_minimum_window():
    assert _resolve_gatekeeper_fast_reuse_sec() >= 20.0


def test_build_ai_ops_log_fields_preserves_operational_meta():
    fields = _build_ai_ops_log_fields(
        {
            "ai_parse_ok": True,
            "ai_parse_fail": False,
            "ai_fallback_score_50": False,
            "ai_response_ms": 321,
            "ai_prompt_type": "scalping_shared",
            "ai_prompt_version": "split_v1",
            "ai_result_source": "live",
            "openai_transport_mode": "responses_ws",
            "openai_transport_requested_mode": "http",
            "openai_model": "gpt-5.4-nano",
            "openai_timeout_budget_ms": 5000,
            "openai_primary_provider": "openai",
            "openai_primary_error_type": "OpenAIResponsesHTTPError",
            "openai_primary_timeout_budget_ms": 7000,
            "openai_total_route_timeout_budget_ms": 15000,
            "bedrock_fallback_family": "lite_v2",
            "bedrock_model_family": "lite_v2",
            "bedrock_fallback_used": True,
            "bedrock_primary_used": False,
            "bedrock_failback_used": False,
            "openai_request_id": "analyze_target:005930:1:abcd",
            "openai_endpoint_name": "analyze_target",
            "openai_schema_name": "entry_v1",
            "openai_ws_used": True,
            "openai_ws_http_fallback": False,
            "openai_ws_queue_wait_ms": 7,
            "openai_ws_roundtrip_ms": 234,
            "openai_ws_attempt_timeout_ms": 2500,
            "openai_ws_total_timeout_ms": 4000,
            "openai_ws_http_fallback_reserve_ms": 1500,
            "openai_ws_elapsed_before_fallback_ms": 2510,
            "openai_http_fallback_budget_ms": 1490,
            "openai_original_timeout_ms": 4000,
            "openai_http_lock_wait_ms": 12,
            "openai_http_provider_ms": 640,
            "openai_http_provider_total_ms": 1440,
            "openai_http_attempt_count": 2,
            "openai_http_deadline_overshoot_ms": 0,
            "openai_http_timeout_budget_exhausted": True,
            "openai_http_wall_deadline_enforced": True,
            "openai_http_wall_deadline_exceeded": True,
            "openai_http_provider_future_cancelled": False,
            "openai_ws_http_fallback_fail_closed": True,
            "openai_ws_http_fallback_error_type": "RuntimeError",
            "openai_http_error_type": "OpenAIResponsesHTTPError",
            "openai_input_tokens": 1234,
            "openai_output_tokens": 56,
            "openai_total_tokens": 1290,
            "openai_cached_input_tokens": 120,
            "openai_reasoning_tokens": 8,
            "ai_request_envelope_sha256": "e" * 64,
            "ai_request_temperature": 0.2,
            "ai_request_max_output_tokens": 700,
            "ai_request_reasoning_effort": "low",
            "holding_score_source_quality_reason": "feature_packet_fresh",
            "holding_score_score50_origin": "post_call_source_quality_neutralized",
            "holding_score_preflight_blocked": True,
            "holding_score_preflight_block_reason": "stale_tick_context",
            "holding_score_preflight_source_quality": "stale",
            "holding_score_preflight_source_quality_reason": "tick_context_stale,tick_context_quality:stale_tick",
            "holding_score_raw_score_non50_neutralized": True,
            "holding_score_model_action": "EXIT",
            "holding_score_model_score": 23,
            "holding_score_model_confidence": 81,
            "holding_score_model_reason": "support failed",
            "holding_score_model_data_quality": "fresh",
            "holding_score_effective_action": "HOLD",
            "holding_score_source_quality_override_applied": True,
            "holding_score_source_quality_override_reason": "holding_context_blocked",
            "holding_score_source_quality_override_blockers": [
                "microstructure_missing_or_stale"
            ],
            "holding_score_timeout_like": True,
            "holding_score_transport_fail_closed": True,
            "holding_score_transport_fail_closed_reason": "OpenAI Responses HTTP timeout budget exhausted",
        },
        ai_score_raw=74,
        ai_score_after_bonus=79,
        entry_score_threshold=75,
        big_bite_bonus_applied=True,
        ai_cooldown_blocked=False,
    )

    assert fields["ai_parse_ok"] is True
    assert fields["ai_parse_fail"] is False
    assert fields["ai_fallback_score_50"] is False
    assert fields["ai_response_ms"] == 321
    assert fields["ai_prompt_type"] == "scalping_shared"
    assert fields["ai_prompt_version"] == "split_v1"
    assert fields["ai_result_source"] == "live"
    assert fields["openai_transport_mode"] == "responses_ws"
    assert fields["openai_transport_requested_mode"] == "http"
    assert fields["openai_model"] == "gpt-5.4-nano"
    assert fields["openai_timeout_budget_ms"] == 5000
    assert fields["openai_primary_provider"] == "openai"
    assert fields["openai_primary_error_type"] == "OpenAIResponsesHTTPError"
    assert fields["openai_primary_timeout_budget_ms"] == 7000
    assert fields["openai_total_route_timeout_budget_ms"] == 15000
    assert fields["bedrock_fallback_family"] == "lite_v2"
    assert fields["bedrock_model_family"] == "lite_v2"
    assert fields["ai_provider_actual"] == "bedrock"
    assert fields["ai_model_actual"] == "lite_v2"
    assert fields["bedrock_fallback_used"] is True
    assert fields["bedrock_primary_used"] is False
    assert fields["bedrock_failback_used"] is False
    assert fields["openai_request_id"] == "analyze_target:005930:1:abcd"
    assert fields["openai_endpoint_name"] == "analyze_target"
    assert fields["openai_schema_name"] == "entry_v1"
    assert fields["openai_ws_used"] is True
    assert fields["openai_ws_http_fallback"] is False
    assert fields["openai_ws_queue_wait_ms"] == 7
    assert fields["openai_ws_roundtrip_ms"] == 234
    assert fields["openai_ws_attempt_timeout_ms"] == 2500
    assert fields["openai_ws_total_timeout_ms"] == 4000
    assert fields["openai_ws_http_fallback_reserve_ms"] == 1500
    assert fields["openai_ws_elapsed_before_fallback_ms"] == 2510
    assert fields["openai_http_fallback_budget_ms"] == 1490
    assert fields["openai_original_timeout_ms"] == 4000
    assert fields["openai_http_lock_wait_ms"] == 12
    assert fields["openai_http_provider_ms"] == 640
    assert fields["openai_http_provider_total_ms"] == 1440
    assert fields["openai_http_attempt_count"] == 2
    assert fields["openai_http_deadline_overshoot_ms"] == 0
    assert fields["openai_http_timeout_budget_exhausted"] is True
    assert fields["openai_http_wall_deadline_enforced"] is True
    assert fields["openai_http_wall_deadline_exceeded"] is True
    assert fields["openai_http_provider_future_cancelled"] is False
    assert fields["openai_ws_http_fallback_fail_closed"] is True
    assert fields["openai_ws_http_fallback_error_type"] == "RuntimeError"
    assert fields["openai_http_error_type"] == "OpenAIResponsesHTTPError"
    assert fields["openai_input_tokens"] == 1234
    assert fields["openai_output_tokens"] == 56
    assert fields["openai_total_tokens"] == 1290
    assert fields["openai_cached_input_tokens"] == 120
    assert fields["openai_reasoning_tokens"] == 8
    assert fields["ai_request_envelope_sha256"] == "e" * 64
    assert fields["ai_request_temperature"] == 0.2
    assert fields["ai_request_max_output_tokens"] == 700
    assert fields["ai_request_reasoning_effort"] == "low"
    assert fields["holding_score_source_quality_reason"] == "feature_packet_fresh"
    assert (
        fields["holding_score_score50_origin"] == "post_call_source_quality_neutralized"
    )
    assert fields["holding_score_preflight_blocked"] is True
    assert fields["holding_score_preflight_block_reason"] == "stale_tick_context"
    assert fields["holding_score_preflight_source_quality"] == "stale"
    assert (
        fields["holding_score_preflight_source_quality_reason"]
        == "tick_context_stale,tick_context_quality:stale_tick"
    )
    assert fields["holding_score_raw_score_non50_neutralized"] is True
    assert fields["holding_score_model_action"] == "EXIT"
    assert fields["holding_score_model_score"] == 23
    assert fields["holding_score_model_confidence"] == 81
    assert fields["holding_score_model_reason"] == "support failed"
    assert fields["holding_score_model_data_quality"] == "fresh"
    assert fields["holding_score_effective_action"] == "HOLD"
    assert fields["holding_score_source_quality_override_applied"] is True
    assert fields["holding_score_source_quality_override_reason"] == (
        "holding_context_blocked"
    )
    assert fields["holding_score_source_quality_override_blockers"] == [
        "microstructure_missing_or_stale"
    ]
    assert fields["holding_score_timeout_like"] is True
    assert fields["holding_score_transport_fail_closed"] is True
    assert (
        fields["holding_score_transport_fail_closed_reason"]
        == "OpenAI Responses HTTP timeout budget exhausted"
    )
    assert fields["ai_score_raw"] == "74.0"
    assert fields["ai_score_after_bonus"] == "79.0"
    assert fields["entry_score_threshold"] == "75.0"
    assert fields["big_bite_bonus_applied"] is True
    assert fields["ai_cooldown_blocked"] is False


def test_build_ai_ops_log_fields_preserves_missing_request_config_as_null():
    fields = _build_ai_ops_log_fields(
        {
            "ai_request_temperature": None,
            "ai_request_max_output_tokens": None,
        }
    )

    assert fields["ai_request_temperature"] is None
    assert fields["ai_request_max_output_tokens"] is None


def test_build_ai_ops_log_fields_reports_bedrock_entry_price_actual_model():
    fields = _build_ai_ops_log_fields(
        {
            "ai_result_source": "live",
            "ai_model": "gpt-5.4-mini",
            "openai_model": "gpt-5.4-mini",
            "openai_transport_mode": "bedrock_primary",
            "bedrock_primary_used": True,
            "bedrock_model_family": "qwen3_32b",
            "bedrock_primary_family": "qwen3_32b",
        }
    )

    assert fields["ai_provider_actual"] == "bedrock"
    assert fields["ai_model_actual"] == "qwen3_32b"
    assert fields["bedrock_model_family"] == "qwen3_32b"
    assert fields["bedrock_primary_family"] == "qwen3_32b"


def test_build_ai_ops_log_fields_reports_bedrock_entry_price_failback_model():
    fields = _build_ai_ops_log_fields(
        {
            "ai_result_source": "live",
            "ai_model": "gpt-5.4-mini",
            "openai_transport_mode": "bedrock_primary",
            "bedrock_primary_used": False,
            "bedrock_failback_used": True,
            "bedrock_model_family": "lite_v2",
            "bedrock_primary_family": "qwen3_32b",
            "bedrock_failback_family": "lite_v2",
        }
    )

    assert fields["ai_provider_actual"] == "bedrock"
    assert fields["ai_model_actual"] == "lite_v2"
    assert fields["bedrock_failback_family"] == "lite_v2"


def test_build_ai_ops_log_fields_reports_openai_after_holding_bedrock_failure():
    fields = _build_ai_ops_log_fields(
        {
            "ai_result_source": "live",
            "ai_model": "gpt-5.4-mini",
            "openai_transport_mode": "http",
            "bedrock_primary_used": False,
            "bedrock_failback_used": True,
        }
    )

    assert fields["ai_provider_actual"] == "openai"
    assert fields["ai_model_actual"] == "gpt-5.4-mini"


def test_build_ai_ops_log_fields_does_not_claim_provider_before_live_call():
    fields = _build_ai_ops_log_fields(
        {
            "ai_result_source": "input_preflight_blocked",
            "openai_transport_mode": "responses_ws",
            "openai_model": "gpt-5.4-nano",
        }
    )

    assert fields["ai_provider_actual"] == "-"
    assert fields["ai_model_actual"] == "-"


def test_build_ai_ops_log_fields_preserves_v214_candidate_lifecycle_binding():
    fields = _build_ai_ops_log_fields(
        {
            "ai_decision_trace_id": "analyze_target:005930:1:abcd",
            "ai_input_payload_sha256": "a" * 64,
            "decision_quality_live_adapter": ("entry_setup_v2_14_krx_bounded_probe_v1"),
            "entry_setup_live_policy_status": "active_bounded_krx_canary",
            "entry_setup_live_policy_mode": "one_share_exploration",
            "entry_setup_live_policy_effective_venue": "KRX",
            "entry_setup_live_policy_session_bucket": "krx_regular",
            "entry_setup_live_policy_runtime_effect": True,
            "entry_probe_intent": True,
            "entry_probe_first_required": True,
            "entry_ai_full_entry_forbidden": True,
        }
    )

    assert fields["ai_decision_trace_id"] == "analyze_target:005930:1:abcd"
    assert fields["ai_input_payload_sha256"] == "a" * 64
    assert fields["entry_setup_live_policy_status"] == "active_bounded_krx_canary"
    assert fields["entry_setup_live_policy_effective_venue"] == "KRX"
    assert fields["entry_setup_live_policy_session_bucket"] == "krx_regular"
    assert fields["entry_setup_live_policy_runtime_effect"] is True
    assert fields["entry_probe_intent"] is True


def test_holding_score_preflight_blocks_stale_tick_context():
    preflight = handlers._holding_score_source_quality_from_feature_packet(
        {
            "tick_context_stale": True,
            "tick_context_quality": "stale_tick",
            "tick_latest_age_ms": 412000,
            "buy_pressure_10t": 50.0,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
            "curr_vs_micro_vwap_bp": 0.0,
            "micro_vwap_available": False,
            "quote_stale": False,
        },
        {},
    )

    assert preflight["data_quality"] == "stale"
    assert "tick_context_stale" in preflight["source_quality_reason"]
    assert "tick_context_quality:stale_tick" in preflight["source_quality_reason"]


def test_holding_score_preflight_accepts_runtime_epoch_timestamp():
    now_dt = datetime(2026, 7, 15, 11, 40, 10)
    now_ts = now_dt.timestamp()
    preflight = handlers._holding_score_preflight_source_quality(
        {
            "curr": 100,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 101, "volume": 1000}],
                "bids": [{"price": 100, "volume": 1200}],
            },
        },
        [
            {
                "time": f"1140{second:02d}",
                "price": 100,
                "volume": 10,
                "dir": "NEUTRAL",
                "aggressor_source": "price_change_heuristic",
            }
            for second in range(9, -1, -1)
        ],
        [
            {
                "체결시간": "20260715114000",
                "source_timestamp": "20260715114000",
                "현재가": 100,
                "고가": 101,
                "저가": 99,
                "거래량": 1000,
            }
        ],
        now_ts=now_ts,
    )

    assert preflight["source_quality_reason"] != "preflight_error:AttributeError"
    assert preflight["data_quality"] == "partial"
    assert preflight["tick_context_quality"] == "fresh_computed"


def test_ai_source_quality_fields_marks_not_evaluated_without_snapshot():
    fields = _ensure_ai_source_quality_fields(
        {}, {}, not_evaluated_reason="watching_ai_cooldown_active"
    )

    assert fields["ai_input_source_quality_status"] == "not_evaluated"
    assert fields["ai_input_source_quality_reason"] == "watching_ai_cooldown_active"
    assert fields["tick_source_quality_fields_sent"] is False
    assert fields["tick_accel_source"] == "not_evaluated"
    assert fields["tick_context_quality"] == "not_evaluated"
    assert fields["quote_age_source"] == "not_evaluated"
    assert "buy_pressure_10t" not in fields


def test_not_evaluated_ai_source_fields_do_not_override_overlap_fields():
    stock = {
        "last_ai_overlap_snapshot": {
            "latest_strength": 123.0,
            "buy_pressure_10t": 71.2,
            "distance_from_day_high_pct": -0.5,
            "intraday_range_pct": 2.1,
            "overlap_context_source_quality": "fresh_range_context",
        }
    }

    fields = _merge_entry_pipeline_field_groups(
        _build_ai_overlap_log_fields(
            stock=stock,
            ai_score=62,
            blocked_stage="blocked_ai_score",
        ),
        _ensure_ai_source_quality_fields(
            {},
            stock,
            not_evaluated_reason="blocked_ai_score_no_tick_audit",
        ),
    )

    assert fields["buy_pressure_10t"] == "71.20"
    assert fields["latest_strength"] == "123.0"
    assert fields["tick_source_quality_fields_sent"] is False


def test_without_entry_pipeline_fields_drops_explicit_authority_keys():
    merged = _merge_entry_pipeline_field_groups(
        {"actual_order_submitted": False, "broker_order_forbidden": True},
        {"threshold_family": "weak_context_late_entry_guard_runtime"},
    )

    fields = _without_entry_pipeline_fields(
        merged,
        "actual_order_submitted",
        "broker_order_forbidden",
    )

    assert fields == {"threshold_family": "weak_context_late_entry_guard_runtime"}


def test_ai_confirmed_log_fields_do_not_duplicate_large_sell_kwarg():
    captured = {}

    def fake_log(*, large_sell_print_detected, **fields):
        captured.update(fields)
        captured["large_sell_print_detected"] = large_sell_print_detected

    pre_ai_fields = _without_entry_pipeline_fields(
        {
            "pre_ai_gate_context_keys": "strength_momentum",
            "large_sell_print_detected": False,
        },
        "large_sell_print_detected",
    )
    ai_confirm_fields = _without_entry_pipeline_fields(
        _merge_entry_pipeline_field_groups(
            {"ai_score": "72.0"},
            {"large_sell_print_detected": False},
        ),
        "large_sell_print_detected",
    )

    fake_log(
        large_sell_print_detected=True,
        **pre_ai_fields,
        **ai_confirm_fields,
    )

    assert captured["large_sell_print_detected"] is True
    assert captured["pre_ai_gate_context_keys"] == "strength_momentum"
    assert captured["ai_score"] == "72.0"


def test_pre_submit_guard_log_fields_do_not_duplicate_authority_kwargs():
    captured = {}

    def fake_log(*, actual_order_submitted, broker_order_forbidden, **fields):
        captured.update(fields)
        captured["actual_order_submitted"] = actual_order_submitted
        captured["broker_order_forbidden"] = broker_order_forbidden

    fake_log(
        actual_order_submitted=False,
        broker_order_forbidden=True,
        **_without_entry_pipeline_fields(
            _merge_entry_pipeline_field_groups(
                handlers._build_pre_submit_gate_contract_fields(
                    "weak_context_late_entry_guard_runtime",
                    gate_action="pre_submit_quality_guard_block",
                ),
                {
                    "decision_authority": "real_scalping_submit_quality_guard",
                    "source_quality_gate": "weak_context_late_entry_guard_contract",
                },
            ),
            "actual_order_submitted",
            "broker_order_forbidden",
        ),
    )

    assert captured["actual_order_submitted"] is False
    assert captured["broker_order_forbidden"] is True
    assert captured["threshold_family"] == "weak_context_late_entry_guard_runtime"
    assert captured["decision_authority"] == "real_scalping_submit_quality_guard"


def test_stale_not_evaluated_ai_source_fields_do_not_override_overlap_fields():
    stock = {
        "last_ai_overlap_snapshot": {
            "latest_strength": 123.0,
            "buy_pressure_10t": 71.2,
            "distance_from_day_high_pct": -0.5,
            "intraday_range_pct": 2.1,
            "overlap_context_source_quality": "fresh_range_context",
        },
        "last_watching_ai_source_quality_fields": {
            "tick_source_quality_fields_sent": True,
            "tick_accel_source": "not_evaluated",
            "tick_context_quality": "not_evaluated",
            "quote_age_source": "not_evaluated",
            "buy_pressure_10t": "-",
        },
    }

    fields = _merge_entry_pipeline_field_groups(
        _build_ai_overlap_log_fields(
            stock=stock,
            ai_score=62,
            blocked_stage="blocked_ai_score",
        ),
        _ensure_ai_source_quality_fields(
            {},
            stock,
            not_evaluated_reason="blocked_ai_score_no_tick_audit",
        ),
    )

    assert fields["buy_pressure_10t"] == "71.20"
    assert fields["tick_source_quality_fields_sent"] is True


def test_ai_source_quality_fields_inherits_previous_snapshot():
    stock = {
        "last_watching_ai_source_quality_fields": {
            "tick_source_quality_fields_sent": True,
            "tick_accel_source": "computed_10ticks",
            "tick_context_quality": "fresh_computed",
            "quote_age_source": "missing",
        }
    }

    fields = _ensure_ai_source_quality_fields(
        {}, stock, not_evaluated_reason="wait65_79_ev_candidate_no_tick_audit"
    )

    assert fields["tick_source_quality_fields_sent"] is True
    assert fields["tick_accel_source"] == "computed_10ticks"
    assert fields["ai_input_source_quality_status"] == "evaluated"
    assert fields["ai_input_source_quality_reason"] == "fresh_computed"


def test_observation_contract_fields_are_source_quality_only():
    fields = _build_observation_contract_fields("funnel_count")

    assert fields["metric_role"] == "funnel_count"
    assert fields["decision_authority"] == "source_quality_only"
    assert fields["runtime_effect"] is False
    assert "runtime_threshold_apply" in fields["forbidden_uses"]


def test_log_entry_pipeline_carries_scanner_promotion_correlation(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "record_id": record_id,
                "fields": fields or {},
            }
        ),
    )
    stock = {
        "id": 42,
        "name": "PROMOTED",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-000033-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "scanner_promotion_reason": "rank_jump_acceleration",
        "source_signature": "REALTIME_RANK_START",
        "price_delta_since_first_seen_pct": "1.25",
    }

    _log_entry_pipeline(
        stock,
        "000033",
        "blocked_strength_momentum",
        original_reason="below_strength_base",
    )

    fields = emitted[-1]["fields"]
    assert emitted[-1]["record_id"] == 42
    assert fields["scanner_promotion_id"] == "SCANPROM-000033-1000000"
    assert fields["scanner_promotion_reason"] == "rank_jump_acceleration"
    assert fields["source_signature"] == "REALTIME_RANK_START"
    assert fields["original_reason"] == "below_strength_base"


def test_log_entry_pipeline_carries_explicit_condition_venue(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 77,
        "name": "CONDITION",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "effective_venue": "KRX",
        "venue": "KRX",
        "venue_resolution": "condition_session_clock:krx_regular",
        "market_session_bucket": "krx_regular",
        "scanner_promotion_id": "CONDPROM-001450-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "scanner_promotion_reason": "condition_search_match:scalp_underpress_01",
        "source_signature": "CONDITION_MATCHED,SCALP_UNDERPRESS_01",
    }

    _log_entry_pipeline(stock, "001450", "strength_momentum_observed")

    fields = emitted[-1]["fields"]
    assert fields["venue"] == "KRX"
    assert fields["effective_venue"] == "KRX"
    assert fields["venue_resolution"] == "condition_session_clock:krx_regular"
    assert fields["market_session_bucket"] == "krx_regular"


def test_log_entry_pipeline_hydrates_missing_scanner_promotion_id(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_load_scanner_promotion_context_events",
        lambda _target_date: {
            "000034": [
                {
                    "emitted_epoch": 1000.0,
                    "fields": {
                        "scanner_promotion_id": "SCANPROM-000034-1000000",
                        "scanner_promotion_emitted_epoch": "1000.000",
                        "scanner_promotion_reason": "price_jump_start_acceleration",
                        "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START",
                        "price_delta_since_first_seen_pct": "1.25",
                        "comparable_flu_delta_since_first_seen": "1.30",
                        "cntr_str_available": True,
                        "cntr_str": "121.0",
                    },
                }
            ]
        },
    )
    stock = {
        "id": 43,
        "name": "PROMOTED",
        "code": "000034",
        "date": "2026-06-19",
        "position_tag": "SCANNER",
        "buy_price": 12000,
        "entry_armed_at_epoch": 1000.0,
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "BID_IMBALANCE_SURGE,PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "1.25",
        "comparable_flu_delta_since_first_seen": "1.30",
        "cntr_str_available": True,
        "cntr_str": "121.0",
    }

    _log_entry_pipeline(stock, "000034", "blocked_strength_momentum")

    fields = emitted[-1]["fields"]
    assert fields["scanner_promotion_id"] == "SCANPROM-000034-1000000"
    assert fields["scanner_promotion_emitted_epoch"] == "1000.000"


def test_log_entry_pipeline_refreshes_stale_scanner_promotion_id(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_load_scanner_promotion_context_events",
        lambda _target_date: {
            "000036": [
                {
                    "emitted_epoch": 900.0,
                    "fields": {
                        "scanner_promotion_id": "SCANPROM-000036-900000",
                        "scanner_promotion_emitted_epoch": "900.000",
                        "scanner_promotion_reason": "old_price_jump",
                        "source_signature": "PRICE_JUMP_START",
                        "price_delta_since_first_seen_pct": "0.25",
                        "comparable_flu_delta_since_first_seen": "0.25",
                        "cntr_str_available": True,
                        "cntr_str": "110.0",
                    },
                },
                {
                    "emitted_epoch": 1000.0,
                    "fields": {
                        "scanner_promotion_id": "SCANPROM-000036-1000000",
                        "scanner_promotion_emitted_epoch": "1000.000",
                        "scanner_promotion_reason": "price_jump_start_acceleration",
                        "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                        "price_delta_since_first_seen_pct": "1.45",
                        "comparable_flu_delta_since_first_seen": "1.50",
                        "cntr_str_available": True,
                        "cntr_str": "122.0",
                    },
                },
            ]
        },
    )
    stock = {
        "id": 45,
        "name": "REPROMOTED",
        "code": "000036",
        "date": "2026-06-19",
        "position_tag": "SCANNER",
        "buy_price": 12500,
        "entry_armed_at_epoch": 1000.0,
        "scanner_promotion_id": "SCANPROM-000036-900000",
        "scanner_promotion_emitted_epoch": "900.000",
        "scanner_promotion_reason": "old_price_jump",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "0.25",
        "comparable_flu_delta_since_first_seen": "0.25",
        "cntr_str_available": True,
        "cntr_str": "110.0",
    }

    _log_entry_pipeline(stock, "000036", "blocked_strength_momentum")

    fields = emitted[-1]["fields"]
    assert fields["scanner_promotion_id"] == "SCANPROM-000036-1000000"
    assert fields["scanner_promotion_emitted_epoch"] == "1000.000"
    assert fields["source_signature"] == "OPEN_TOP,PRICE_JUMP_START"
    assert fields["price_delta_since_first_seen_pct"] == "1.45"


def test_log_entry_pipeline_marks_scanner_terminal_block_freshness(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda *args, **kwargs: None,
    )
    fresh_stock = {
        "id": 80,
        "name": "PROMOTED",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
    }
    stale_stock = dict(fresh_stock, id=81)

    _log_entry_pipeline(
        fresh_stock,
        "000080",
        "blocked_vpw",
        quote_age_ms=120.0,
        tick_latest_age_ms=300.0,
        snapshot_source="ws_snapshot_input",
    )
    _log_entry_pipeline(
        stale_stock,
        "000081",
        "blocked_vpw",
        quote_age_ms=120.0,
        tick_latest_age_ms=300.0,
        quote_stale=True,
        snapshot_source="ws_snapshot_input",
    )

    assert (
        fresh_stock["_scanner_watch_last_terminal_block"]["fresh_input_confirmed"]
        is True
    )
    assert (
        stale_stock["_scanner_watch_last_terminal_block"]["fresh_input_confirmed"]
        is False
    )


def test_emit_scanner_watching_runtime_skip_fills_contract_fields(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "rising_missed_selection_prior_fields",
        lambda stock: {
            "rising_missed_selection_prior_key": "prior_positive",
            "rising_missed_selection_recommendation": "positive_prior",
            "rising_missed_selection_confidence": "high",
            "rising_missed_selection_score_delta": 20.0,
            "rising_missed_selection_rank_reason": "positive_prior_test",
            "rising_missed_selection_match_type": "observable_prefix_exact",
            "rising_missed_selection_runtime_effect": False,
            "rising_missed_selection_allowed_runtime_apply": False,
        },
    )
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "record_id": record_id, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 77,
        "name": "PROMOTED",
        "code": "000037",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "added_time": 900.0,
        "entry_armed_at_epoch": 1000.0,
        "scanner_promotion_id": "SCANPROM-000037-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START",
        "price_delta_since_first_seen_pct": "1.20",
        "_scanner_fast_precheck_fields": {
            "effective_venue": "KRX",
            "venue": "KRX",
            "venue_resolution": "scanner_session_clock:krx_regular",
            "market_session_bucket": "krx_regular",
        },
    }

    emitted_result = handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000037",
        skip_reason="ws_snapshot_missing_or_zero",
        now_ts=1100.0,
        ws_data={},
        ws_manager_available=True,
    )

    assert emitted_result is True
    scanner_event = next(
        event
        for event in emitted
        if event["stage"] == "scalping_scanner_watching_runtime_skip"
    )
    fields = scanner_event["fields"]
    assert fields["metric_role"] == "funnel_count"
    assert (
        fields["decision_authority"]
        == "real_scalping_scanner_runtime_watchlist_observation_only"
    )
    assert fields["source_quality_route"] == "runtime_watchlist_skip_observation_only"
    assert fields["runtime_effect"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert fields["effective_venue"] == "KRX"
    assert fields["venue"] == "KRX"
    assert fields["venue_source_quality_status"] == "pass"
    assert fields["venue_unknown_reviewed_reason"] == "not_applicable"
    assert fields["venue_resolution"] == (
        "scanner_runtime_event:scanner_fast_precheck:"
        "scanner_session_clock:krx_regular"
    )
    assert fields["skip_reason"] == "ws_snapshot_missing_or_zero"
    assert fields["scanner_promotion_id"] == "SCANPROM-000037-1000000"
    assert fields["target_status"] == "WATCHING"
    assert fields["target_strategy"] == "SCALPING"
    assert fields["target_position_tag"] == "SCANNER"
    assert fields["runtime_record_id"] == 77
    assert fields["entry_armed_at_epoch"] == 1000.0
    assert fields["ws_curr"] == "not_applicable_ws_curr"
    assert fields["ws_manager_available"] is True
    assert fields["rising_entry_relief_eligible"] is True
    assert fields["scanner_positive_delta_pct"] == 1.2
    assert (
        fields["scanner_full_eval_budget_source"]
        == "not_applicable_full_eval_budget_source"
    )
    assert fields["rising_missed_selection_prior_key"] == "prior_positive"
    assert fields["rising_missed_selection_recommendation"] == "positive_prior"
    assert fields["rising_missed_selection_score_delta"] == 20.0
    assert fields["rising_missed_selection_runtime_effect"] is False
    assert fields["zero_context_domain"] == "ws_quote"
    assert fields["zero_context_blocker"] == "ws_snapshot_missing_or_zero"
    assert fields["zero_context_ws_curr_state"] == "missing_defaulted_zero"
    assert (
        fields["zero_context_ws_received_type_count_state"] == "missing_defaulted_zero"
    )
    assert fields["zero_context_defaulted_zero_field_count"] >= 2
    assert "threshold_mutation" in fields["zero_context_forbidden_uses"]
    assert all(
        event["stage"] != "opening_rotation_1pct_upstream_blocked" for event in emitted
    )


def test_emit_scanner_watching_runtime_skip_reports_ws_type_freshness(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            fields or {}
        ),
    )
    stock = {
        "id": 78,
        "name": "PROMOTED",
        "code": "000078",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
    }

    assert handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000078",
        skip_reason="scanner_fast_precheck_stability_pending",
        now_ts=1100.0,
        ws_data={
            "curr": 1200,
            "received_types": {"0B", "0D"},
            "last_realtime_type_ts": {"0B": 1099.0, "0D": 1090.0},
            "strength_momentum_history": [{"ts": 1099.5}],
        },
        throttle_sec=0,
    )

    fields = emitted[-1]
    assert fields["ws_received_types"] == "0B,0D"
    assert fields["ws_received_type_count"] == 2
    assert fields["ws_last_0b_age_ms"] == 1000.0
    assert fields["ws_last_0d_age_ms"] == 10000.0
    assert fields["ws_last_0b_epoch"] == "1099.000000"
    assert fields["ws_last_0d_epoch"] == "1090.000000"
    assert fields["ws_last_strength_history_age_ms"] == 500.0
    assert fields["ws_strength_history_count"] == 1


def test_zero_context_strength_momentum_fields_split_insufficient_history():
    fields = handlers._strength_momentum_zero_context_fields(
        {
            "reason": "insufficient_history",
            "window_buy_value": 0,
            "window_net_buy_qty": 0,
            "window_buy_ratio": None,
            "tick_window_sample_count": None,
        },
        "insufficient_history",
    )

    assert fields["zero_context_domain"] == "strength_momentum"
    assert fields["zero_context_blocker"] == "insufficient_history"
    assert fields["zero_context_window_buy_value_state"] == "actual_zero"
    assert fields["zero_context_window_buy_ratio_state"] == "not_applicable_zero"
    assert fields["zero_context_sample_count_state"] == "not_applicable_zero"
    assert "stale_quote_bypass" in fields["zero_context_forbidden_uses"]


def test_emit_scanner_watching_runtime_skip_carries_fast_precheck_observed_fields(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            fields or {}
        ),
    )
    stock = {
        "id": 80,
        "name": "PROMOTED",
        "code": "000080",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
    }

    assert handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000080",
        skip_reason="scanner_fast_precheck_stability_pending",
        now_ts=1100.0,
        ws_data={},
        throttle_sec=0,
        fast_precheck_fields={
            "ws_strength_history_count": 13,
            "ws_last_strength_history_age_ms": 1234.0,
            "quote_age_ms": 7377.143,
            "quote_age_source": "last_ws_update_ts",
            "snapshot_source": "ws_snapshot_input",
            "fast_precheck_result": "stability_pending",
            "fast_precheck_reason": "stale_ws_snapshot",
        },
    )

    fields = emitted[-1]
    assert fields["ws_strength_history_count"] == 0
    assert fields["fast_precheck_observed_ws_strength_history_count"] == 13
    assert fields["fast_precheck_observed_ws_last_strength_history_age_ms"] == 1234.0
    assert fields["fast_precheck_observed_quote_age_ms"] == 7377.143
    assert fields["fast_precheck_observed_quote_age_source"] == "last_ws_update_ts"
    assert fields["fast_precheck_observed_snapshot_source"] == "ws_snapshot_input"
    assert fields["fast_precheck_observed_result"] == "stability_pending"
    assert fields["fast_precheck_observed_reason"] == "stale_ws_snapshot"
    assert (
        fields["fast_precheck_observed_payload_source"]
        == "scanner_fast_precheck_fields"
    )
    assert fields["runtime_effect"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True


def test_emit_scanner_watching_runtime_skip_ignores_expired_cutoff_relief_state(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            fields or {}
        ),
    )
    stock = {
        "id": 79,
        "name": "PROMOTED",
        "code": "000079",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
        "_scanner_rising_cutoff_recheck_after_epoch": 1050.0,
        "_scanner_rising_entry_relief_reason": "next_buy_window_recheck_pending",
        "_scanner_full_eval_budget_source": "not_applicable_cutoff",
    }

    assert handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000079",
        skip_reason="ws_snapshot_missing_or_zero",
        now_ts=1100.0,
        ws_data={},
        throttle_sec=0,
    )

    fields = emitted[-1]
    assert fields["rising_entry_relief_eligible"] is True
    assert fields["rising_entry_relief_reason"] == "not_applicable_rising_entry_relief"
    assert (
        fields["scanner_full_eval_budget_source"]
        == "not_applicable_full_eval_budget_source"
    )


def test_emit_scanner_watching_runtime_skip_keeps_active_cutoff_relief_state(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            fields or {}
        ),
    )
    stock = {
        "id": 80,
        "name": "PROMOTED",
        "code": "000080",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
        "_scanner_rising_cutoff_recheck_after_epoch": 1150.0,
        "_scanner_rising_entry_relief_reason": "next_buy_window_recheck_pending",
        "_scanner_full_eval_budget_source": "not_applicable_cutoff",
    }

    assert handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000080",
        skip_reason="outside_scalping_buy_window",
        now_ts=1100.0,
        ws_data={},
        throttle_sec=0,
    )

    fields = emitted[-1]
    assert fields["rising_entry_relief_reason"] == "next_buy_window_recheck_pending"
    assert fields["scanner_full_eval_budget_source"] == "not_applicable_cutoff"


def test_emit_scanner_watching_runtime_skip_uses_active_epoch_reason_over_stale_state(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            fields or {}
        ),
    )
    stock = {
        "id": 81,
        "name": "PROMOTED",
        "code": "000081",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
        "_scanner_rising_cooldown_recheck_after_epoch": 1150.0,
        "_scanner_rising_cutoff_recheck_after_epoch": 1050.0,
        "_scanner_rising_entry_relief_reason": "next_buy_window_recheck_pending",
        "_scanner_full_eval_budget_source": "not_applicable_cutoff",
    }

    assert handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000081",
        skip_reason="entry_cooldown_active",
        now_ts=1100.0,
        ws_data={},
        throttle_sec=0,
    )

    fields = emitted[-1]
    assert fields["rising_entry_relief_reason"] == "cooldown_recheck_pending"
    assert fields["scanner_full_eval_budget_source"] == "not_applicable_cooldown"


def test_emit_scanner_watching_runtime_skip_keeps_terminal_hardgate_recheck_state(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            fields or {}
        ),
    )
    stock = {
        "id": 82,
        "name": "PROMOTED",
        "code": "000082",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
        "_scanner_rising_terminal_hardgate_recheck_after_epoch": 1150.0,
    }

    assert handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000082",
        skip_reason="blocked_strength_momentum",
        now_ts=1100.0,
        ws_data={},
        throttle_sec=0,
    )

    fields = emitted[-1]
    assert fields["rising_entry_relief_reason"] == "terminal_hardgate_recheck_pending"
    assert (
        fields["scanner_full_eval_budget_source"] == "not_applicable_terminal_hardgate"
    )


def test_emit_scanner_watching_runtime_skip_resets_terminal_eviction_memory(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda *args, **kwargs: None,
    )
    stock = {
        "id": 79,
        "name": "PROMOTED",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "_scanner_watch_last_terminal_block": {"stage": "blocked_vpw"},
        "_scanner_watch_eviction_terminal_stage": "blocked_vpw",
        "_scanner_watch_eviction_terminal_reason": "below_vpw",
        "_scanner_watch_eviction_terminal_count": 1,
        "_scanner_watch_eviction_last_terminal_observed_epoch": 1000.0,
    }

    emitted = handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000039",
        skip_reason="entry_cooldown_active",
        now_ts=1100.0,
        ws_data={"curr": 12000},
        throttle_sec=0,
    )

    assert emitted is True
    assert "_scanner_watch_last_terminal_block" not in stock
    assert "_scanner_watch_eviction_terminal_stage" not in stock
    assert "_scanner_watch_eviction_terminal_reason" not in stock
    assert "_scanner_watch_eviction_terminal_count" not in stock
    assert "_scanner_watch_eviction_last_terminal_observed_epoch" not in stock
    assert stock["_scanner_watch_last_pool_block"]["reason"] == "entry_cooldown_active"
    assert stock["_scanner_watch_last_pool_block"]["observed_epoch"] == 1100.0


def test_emit_scanner_watching_runtime_skip_throttles_same_reason(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 78,
        "name": "PROMOTED",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
    }

    first = handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000038",
        skip_reason="entry_cooldown_active",
        now_ts=1100.0,
        ws_data={"curr": 12000},
    )
    second = handlers.emit_scanner_watching_runtime_skip(
        stock,
        "000038",
        skip_reason="entry_cooldown_active",
        now_ts=1110.0,
        ws_data={"curr": 12000},
    )

    assert first is True
    assert second is False
    assert len(emitted) == 1


def test_emit_scanner_runtime_queue_lag_fills_contract_fields(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "record_id": record_id, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 79,
        "name": "PROMOTED",
        "code": "000039",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "added_time": 990.0,
        "entry_armed_at_epoch": 1000.0,
        "scanner_attach_epoch": 1000.1,
        "scanner_first_entry_realtime_epoch": 1002.0,
        "scanner_first_entry_realtime_type": "0B",
        "scanner_evaluation_anchor_source": "first_post_attach_entry_realtime",
        "scanner_promotion_id": "SCANPROM-000039-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PREV_CLOSE_GAINER,PRICE_JUMP_START",
        "_scanner_fast_precheck_fields": {
            "effective_venue": "KRX",
            "venue": "KRX",
            "venue_resolution": "scanner_session_clock:krx_regular",
            "market_session_bucket": "krx_regular",
        },
    }

    emitted_result = handlers.emit_scanner_runtime_queue_lag(
        stock,
        "000039",
        now_ts=1012.345,
        queue_rank=2,
        scanner_queue_rank=1,
        watching_count=72,
        scanner_watching_count=52,
        real_holding_count=3,
        non_real_holding_count=28,
        pre_scanner_runtime_count=5,
        loop_started_epoch=1010.000,
    )

    assert emitted_result is True
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_queue_lag"
    fields = emitted[-1]["fields"]
    assert fields["metric_role"] == "funnel_count"
    assert (
        fields["decision_authority"]
        == "real_scalping_scanner_runtime_watchlist_observation_only"
    )
    assert (
        fields["source_quality_gate"] == "scalping_scanner_runtime_queue_lag_contract"
    )
    assert (
        fields["source_quality_route"] == "runtime_watchlist_queue_lag_observation_only"
    )
    assert fields["runtime_effect"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert fields["effective_venue"] == "KRX"
    assert fields["venue_source_quality_status"] == "pass"
    assert fields["queue_rank"] == 2
    assert fields["scanner_queue_rank"] == 1
    assert fields["watching_count"] == 72
    assert fields["scanner_watching_count"] == 52
    assert fields["real_holding_count"] == 3
    assert fields["non_real_holding_count"] == 28
    assert fields["pre_scanner_runtime_count"] == 5
    assert fields["queue_lag_sec"] == 12.345
    assert fields["controllable_queue_lag_sec"] == 10.345
    assert fields["queue_lag_causal_class"] == "internal_post_usable_ws_queue"
    assert fields["external_first_ws_delay_excluded"] is True
    assert fields["external_first_ws_delay_sec"] == 1.9
    assert fields["scanner_attach_epoch"] == "1000.100"
    assert fields["scanner_first_entry_realtime_epoch"] == "1002.000"
    assert fields["scanner_first_entry_realtime_type"] == "0B"
    assert fields["scanner_evaluation_anchor_source"] == (
        "first_post_attach_entry_realtime"
    )
    assert fields["anchor_to_loop_sec"] == 10.0
    assert fields["loop_to_emit_sec"] == 2.345
    assert fields["pre_emit_delay_sec"] == 2.345
    assert fields["loop_started_epoch"] == "1010.000"
    assert fields["queue_emit_epoch"] == "1012.345"
    assert fields["runtime_record_id"] == 79
    assert fields["entry_armed_at_epoch"] == 1000.0
    assert fields["market_gainer_first_ai_priority_active"] is True
    assert fields["market_gainer_first_eval_retention_reason"] == (
        "awaiting_first_ai_evaluated"
    )
    assert fields["market_gainer_first_eval_retention_age_sec"] == 12.345
    assert fields["market_gainer_first_ai_evaluated_observed"] is False


def test_emit_scanner_runtime_queue_lag_throttles(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 80,
        "name": "PROMOTED",
        "code": "000040",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
    }

    assert (
        handlers.emit_scanner_runtime_queue_lag(stock, "000040", now_ts=1010.0) is True
    )
    assert (
        handlers.emit_scanner_runtime_queue_lag(stock, "000040", now_ts=1015.0) is False
    )
    assert len(emitted) == 1


def test_emit_scanner_fast_precheck_and_heavy_eval_lag_are_order_forbidden(monkeypatch):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 81,
        "name": "FAST",
        "code": "000081",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "added_time": 990.0,
        "entry_armed_at_epoch": 1000.0,
        "scanner_first_entry_realtime_epoch": 1001.5,
        "scanner_first_entry_realtime_type": "0B",
        "scanner_promotion_id": "SCANPROM-000081-1000000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "source_signature": "PRICE_JUMP_START",
        "venue": "KRX",
        "effective_venue": "KRX",
        "venue_resolution": "scanner_session_clock:krx_regular",
        "market_session_bucket": "krx_regular",
    }
    ws_data = {"curr": 1200, "last_ws_update_ts": 1011.9}

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000081",
        now_ts=1012.0,
        ws_data=ws_data,
        queue_rank=2,
        scanner_queue_rank=1,
        watching_count=10,
        scanner_watching_count=3,
        throttle_sec=0,
    )
    assert handlers.emit_scanner_heavy_eval_lag(
        stock,
        "000081",
        now_ts=1012.2,
        queue_enter_epoch=1012.0,
        throttle_sec=0,
    )

    fast = emitted[-2]["fields"]
    heavy = emitted[-1]["fields"]
    assert emitted[-2]["stage"] == "scalping_scanner_fast_precheck"
    assert fast["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert fast["runtime_effect"] is False
    assert fast["actual_order_submitted"] is False
    assert fast["broker_order_forbidden"] is True
    assert fast["effective_venue"] == "KRX"
    assert fast["venue_resolution"] == "scanner_session_clock:krx_regular"
    assert fast["market_session_bucket"] == "krx_regular"
    assert fast["heavy_queue_enter_epoch"] == "1012.000"
    assert fast["rising_entry_relief_eligible"] is False
    assert emitted[-1]["stage"] == "scalping_scanner_heavy_eval_lag"
    assert heavy["heavy_queue_wait_sec"] == 0.2
    assert heavy["queue_lag_causal_class"] == ("internal_post_usable_ws_heavy_queue")
    assert heavy["external_first_ws_delay_excluded"] is True
    assert heavy["scanner_first_entry_realtime_epoch"] == "1001.500"
    assert heavy["scanner_first_entry_realtime_type"] == "0B"
    assert heavy["runtime_effect"] is False
    assert heavy["actual_order_submitted"] is False
    assert heavy["broker_order_forbidden"] is True
    assert heavy["effective_venue"] == "KRX"
    assert heavy["venue_resolution"] == "scanner_session_clock:krx_regular"
    assert heavy["market_session_bucket"] == "krx_regular"
    assert (
        heavy["scanner_full_eval_budget_source"]
        == "not_applicable_full_eval_budget_source"
    )

    completion = handlers._scanner_heavy_eval_completion_fields(
        stock,
        started_epoch=1012.2,
        completed_epoch=1012.55,
        queue_enter_epoch=1012.0,
        outcome="WATCHING",
    )
    assert completion["heavy_queue_wait_sec"] == 0.2
    assert completion["heavy_handler_duration_sec"] == 0.35
    assert completion["heavy_end_to_end_sec"] == 0.55
    assert completion["heavy_eval_outcome"] == "WATCHING"
    assert completion["runtime_effect"] is False
    assert completion["actual_order_submitted"] is False
    assert completion["broker_order_forbidden"] is True


def test_scanner_runtime_event_venue_fields_fail_closed_without_inference():
    conflict = handlers._scanner_runtime_event_venue_fields(
        {
            "effective_venue": "KRX",
            "venue": "NXT",
            "venue_resolution": "stale_resolution_must_not_override_conflict",
            "market_session_bucket": "krx_regular",
        }
    )
    missing = handlers._scanner_runtime_event_venue_fields(
        {"broker_route": "SOR", "ws_item": "005930_AL"}
    )
    fast_precheck = handlers._scanner_runtime_event_venue_fields(
        {
            "_scanner_fast_precheck_fields": {
                "effective_venue": "PREMARKET_KRX_LIKE",
                "venue": "PREMARKET_KRX_LIKE",
                "venue_resolution": "scanner_session_clock:krx_like_premarket",
                "market_session_bucket": "krx_like_premarket",
            }
        }
    )
    session_mismatch = handlers._scanner_runtime_event_venue_fields(
        {
            "effective_venue": "KRX",
            "venue": "KRX",
            "venue_resolution": "consistent_explicit:effective_venue,venue",
            "market_session_bucket": "nxt",
        }
    )

    assert conflict["effective_venue"] == "UNKNOWN"
    assert conflict["venue"] == "UNKNOWN"
    assert conflict["venue_resolution"].startswith(
        "scanner_runtime_event:conflicting_explicit_target_venue:"
    )
    assert missing == {
        "venue": "UNKNOWN",
        "effective_venue": "UNKNOWN",
        "venue_resolution": "scanner_runtime_event:explicit_target_venue_missing",
        "venue_source_quality_status": "reviewed_fail_closed",
        "venue_unknown_reviewed_reason": (
            "scanner_runtime_event:explicit_target_venue_missing"
        ),
        "market_session_bucket": (
            "scanner_runtime_event:market_session_bucket_missing"
        ),
    }
    assert fast_precheck == {
        "venue": "PREMARKET_KRX_LIKE",
        "effective_venue": "PREMARKET_KRX_LIKE",
        "venue_resolution": (
            "scanner_runtime_event:scanner_fast_precheck:"
            "scanner_session_clock:krx_like_premarket"
        ),
        "venue_source_quality_status": "pass",
        "venue_unknown_reviewed_reason": "not_applicable",
        "market_session_bucket": "krx_like_premarket",
    }
    assert session_mismatch == {
        "venue": "UNKNOWN",
        "effective_venue": "UNKNOWN",
        "venue_resolution": (
            "scanner_runtime_event:market_session_bucket_venue_mismatch:"
            "effective_venue=KRX,market_session_bucket=nxt"
        ),
        "venue_source_quality_status": "reviewed_fail_closed",
        "venue_unknown_reviewed_reason": (
            "scanner_runtime_event:market_session_bucket_venue_mismatch:"
            "effective_venue=KRX,market_session_bucket=nxt"
        ),
        "market_session_bucket": "nxt",
    }


def test_scanner_terminal_block_insufficient_history_is_not_fresh_for_eviction():
    assert (
        handlers._scanner_terminal_block_fresh_input_confirmed(
            {
                "reason": "insufficient_history",
                "quote_age_ms": 100,
                "tick_latest_age_ms": 100,
                "snapshot_source": "ws_snapshot",
            }
        )
        is False
    )
    assert (
        handlers._scanner_terminal_block_fresh_input_confirmed(
            {
                "source_quality_block_reason": "single_snapshot_only",
                "quote_age_ms": 100,
                "tick_latest_age_ms": 100,
                "snapshot_source": "ws_snapshot",
            }
        )
        is False
    )


def test_pre_ai_blocked_gate_quality_fields_include_freshness_and_stability(
    monkeypatch,
):
    monkeypatch.setattr(handlers.time, "time", lambda: 1010.0)
    ws_data = {
        "curr": 1200,
        "last_ws_update_ts": 1009.5,
        "strength_momentum_history": [
            {"ts": 1004.0, "v_pw": 100.0},
            {"ts": 1008.0, "v_pw": 104.0},
            {"ts": 1009.0, "v_pw": 105.0},
        ],
    }
    fields = handlers._pre_ai_blocked_gate_quality_fields(
        gate_name="vpw",
        ws_data=ws_data,
        gate_result={"window_sec": 5},
        refresh_fields={
            "pre_ai_ws_snapshot_refresh_applied": True,
            "pre_ai_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
            "pre_ai_ws_snapshot_refresh_source": "ws_manager_latest_data",
            "pre_ai_ws_snapshot_refresh_age_ms": 300.0,
        },
    )

    assert fields["quote_age_ms"] == 500.0
    assert fields["tick_latest_age_ms"] == 1000.0
    assert fields["tick_sample_count"] == 3
    assert fields["tick_window_sample_count"] == 3
    assert fields["tick_window_span_sec"] == 5.0
    assert fields["snapshot_source"] == "ws_manager_latest_data"
    assert fields["refresh_applied"] is True
    assert fields["refresh_reason"] == "latest_ws_snapshot_fresh"
    assert fields["refresh_age_ms"] == 300.0
    assert fields["stability_window_result"] == "window_available"
    assert fields["stability_sample_count"] == 3


def test_pre_ai_liquidity_quality_marks_missing_orderbook(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 1010.0)
    fields = handlers._pre_ai_blocked_gate_quality_fields(
        gate_name="liquidity",
        ws_data={"curr": 1200, "last_ws_update_ts": 1009.0},
        liquidity_totals_present=False,
    )

    assert fields["quote_age_ms"] == 1000.0
    assert fields["tick_latest_age_ms"] == "not_available_tick_latest_age_ms"
    assert fields["refresh_applied"] is False
    assert fields["refresh_reason"] == "not_attempted_no_refresh_fields"
    assert fields["stability_window_result"] == "missing_orderbook_snapshot"
    assert fields["stability_window_reason"] == "ask_bid_totals_missing"


def test_pre_ai_strength_momentum_quality_uses_explicit_reason_labels(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 1010.0)
    fields = handlers._pre_ai_blocked_gate_quality_fields(
        gate_name="strength_momentum",
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1009.0,
            "strength_momentum_history": [],
        },
        gate_result={"window_sec": 5},
        refresh_fields={},
    )

    assert fields["quote_age_ms"] == 1000.0
    assert fields["tick_latest_age_ms"] == "not_available_tick_latest_age_ms"
    assert fields["tick_window_sample_count"] == 0
    assert fields["snapshot_source"] == "ws_snapshot_input"
    assert fields["refresh_applied"] is False
    assert fields["refresh_reason"] == "not_attempted_no_refresh_fields"
    assert fields["stability_window_result"] == "not_available"
    assert fields["stability_window_reason"] == "strength_momentum_history_missing"


def test_pre_ai_gate_contract_forbids_broker_order():
    fields = handlers._build_pre_ai_gate_contract_fields(
        "strength_momentum_soft_gate_p1",
        gate_action="source_quality_block",
    )

    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert fields["allowed_runtime_apply"] is False


def test_scanner_fast_precheck_marks_stale_snapshot_not_queued(monkeypatch):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 82,
        "name": "STALE",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "scanner_promotion_id": "SCANPROM-000082-1000000",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000082",
        now_ts=1012.0,
        ws_data={"curr": 1200, "last_ws_update_ts": 1000.0},
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "stability_pending"
    assert fields["fast_precheck_reason"] == "stale_ws_snapshot"
    assert fields["heavy_queue_enter_epoch"] == "not_queued"
    assert fields["ws_received_types"] == "-"
    assert fields["ws_last_0b_age_ms"] == "not_available_realtime_type_age_ms"
    assert fields["fast_precheck_positive_delta_pct"] == 0.0
    assert (
        fields["fast_precheck_rest_supplement_status"] == "rest_supplement_not_present"
    )
    assert (
        fields["fast_precheck_rest_supplement_block_reason"]
        == "rest_supplement_not_present"
    )
    assert (
        fields["fast_precheck_stale_ws_relief_block_reason"]
        == "rising_stale_ws_relief_disabled"
    )
    assert stock["_scanner_fast_precheck_result"] == "stability_pending"
    assert "_scanner_heavy_queue_enter_epoch" not in stock


def test_scanner_fast_precheck_reports_low_delta_stale_ws_relief_block(monkeypatch):
    emitted = []
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_MIN_DELTA_PCT", "0.1")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STALE_WS_FULL_EVAL_RELIEF_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STALE_WS_FULL_EVAL_MIN_DELTA_PCT", "1.0"
    )
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 820,
        "name": "STALE_LOW_DELTA",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "0.20",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000820",
        now_ts=1012.0,
        ws_data={"curr": 1200, "last_ws_update_ts": 1000.0},
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "stability_pending"
    assert fields["fast_precheck_reason"] == "stale_ws_snapshot"
    assert fields["fast_precheck_positive_delta_pct"] == 0.2
    assert fields["fast_precheck_stale_ws_relief_applied"] is False
    assert (
        fields["fast_precheck_stale_ws_relief_block_reason"]
        == "positive_delta_below_stale_ws_relief_min"
    )
    assert (
        fields["fast_precheck_rest_supplement_status"] == "rest_supplement_not_present"
    )


def test_scanner_fast_precheck_holds_rest_quote_only_recovery_until_realtime_strength(
    monkeypatch,
):
    emitted = []
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_REST_QUOTE_FULL_EVAL_RELIEF_ENABLED", "false"
    )
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 821,
        "name": "RESTONLY",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "8.20",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000821",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1000.0,
            "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback",
            "ws_snapshot_recovery_epoch": 1012.0,
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "stability_pending"
    assert fields["fast_precheck_reason"] == "rest_quote_without_realtime_strength"
    assert (
        fields["fast_precheck_rest_supplement_status"] == "rest_quote_fallback_detected"
    )
    assert (
        fields["fast_precheck_rest_supplement_block_reason"]
        == "rising_rest_quote_relief_disabled"
    )
    assert (
        fields["fast_precheck_stale_ws_relief_block_reason"]
        == "rest_supplement_present"
    )
    assert fields["heavy_queue_enter_epoch"] == "not_queued"
    assert stock["_scanner_fast_precheck_result"] == "stability_pending"
    assert "_scanner_heavy_queue_enter_epoch" not in stock


def test_scanner_fast_precheck_reports_ws_type_freshness(monkeypatch):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 83,
        "name": "FRESH_TYPES",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000083",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1011.5,
            "received_types": {"0B", "0D", "0w"},
            "last_realtime_type_ts": {"0B": 1011.4, "0D": 1000.0, "0w": 1011.0},
            "strength_momentum_history": [{"ts": 1011.8}],
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert fields["ws_received_types"] == "0B,0D,0w"
    assert fields["ws_last_0b_age_ms"] == 600.0
    assert fields["ws_last_0d_age_ms"] == 12000.0
    assert fields["ws_last_0w_age_ms"] == 1000.0
    assert fields["ws_last_strength_history_age_ms"] == 200.0
    assert fields["ws_strength_history_count"] == 1


def test_scanner_fast_precheck_allows_rising_candidate_with_fresh_realtime_type(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 84,
        "name": "RISING",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000084",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1000.0,
            "received_types": {"0B"},
            "last_realtime_type_ts": {"0B": 1011.4},
            "strength_momentum_history": [{"ts": 1011.8}],
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert (
        fields["fast_precheck_reason"]
        == "rising_realtime_type_fresh_quote_timestamp_stale"
    )
    assert fields["fast_precheck_realtime_relief_applied"] is True
    assert fields["fast_precheck_realtime_relief_scope"] == "rising_entry_relief_only"
    assert fields["heavy_queue_enter_epoch"] == "1012.000"
    assert stock["_scanner_fast_precheck_result"] == "eligible_for_heavy_entry_eval"


def test_scanner_fast_precheck_holds_subscription_recheck_until_realtime_strength(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 85,
        "name": "RISING_RECHECK",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000085",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1007.0,
            "scanner_subscription_recheck_entry_relief": True,
            "scanner_subscription_recheck_age_sec": 5.0,
            "scanner_subscription_recheck_fresh_sec": 10.0,
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "stability_pending"
    assert (
        fields["fast_precheck_reason"]
        == "subscription_recheck_without_realtime_strength"
    )
    assert fields["fast_precheck_subscription_recheck_relief_applied"] is True
    assert fields["fast_precheck_realtime_relief_scope"] == "rising_entry_relief_only"
    assert fields["heavy_queue_enter_epoch"] == "not_queued"


def test_scanner_fast_precheck_allows_high_delta_rest_quote_recovery(monkeypatch):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 850,
        "name": "RISING_REST_QUOTE",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "5.20",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000850",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1011.0,
            "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback",
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert (
        fields["fast_precheck_reason"]
        == "rising_rest_quote_recovery_without_realtime_strength"
    )
    assert fields["fast_precheck_rest_quote_relief_applied"] is True
    assert (
        fields["fast_precheck_rest_supplement_status"]
        == "applied_rising_rest_quote_relief"
    )
    assert (
        fields["fast_precheck_rest_supplement_block_reason"]
        == "applied_rising_rest_quote_relief"
    )
    assert fields["fast_precheck_stale_ws_relief_block_reason"] == "quote_not_stale"
    assert fields["fast_precheck_realtime_relief_scope"] == "rising_entry_relief_only"
    assert fields["heavy_queue_enter_epoch"] == "1012.000"
    assert stock["_scanner_fast_precheck_result"] == "eligible_for_heavy_entry_eval"


def test_scanner_fast_precheck_blocks_rest_quote_below_promotion_anchor(monkeypatch):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 851,
        "name": "RISING_BAD_REST_QUOTE",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "first_seen_price": "43400",
        "current_price_observed": "45400",
        "price_delta_since_first_seen_pct": "6.22",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "376900",
        now_ts=1012.0,
        ws_data={
            "curr": 40000,
            "last_ws_update_ts": 1011.0,
            "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback",
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "stability_pending"
    assert (
        fields["fast_precheck_reason"] == "rest_quote_conflicts_with_scanner_promotion"
    )
    assert fields["fast_precheck_rest_quote_relief_applied"] is False
    assert fields["fast_precheck_rest_quote_anchor_price"] == 45400
    assert fields["fast_precheck_rest_quote_anchor_gap_pct"] > 1.0
    assert (
        fields["fast_precheck_rest_quote_consistency_status"]
        == "conflicts_with_scanner_promotion"
    )
    assert (
        fields["fast_precheck_rest_supplement_status"] == "rest_quote_fallback_detected"
    )
    assert (
        fields["fast_precheck_rest_supplement_block_reason"]
        == "rest_quote_conflicts_with_scanner_promotion"
    )
    assert fields["heavy_queue_enter_epoch"] == "not_queued"
    assert stock["_scanner_fast_precheck_result"] == "stability_pending"
    assert "_scanner_heavy_queue_enter_epoch" not in stock


def test_scanner_fast_precheck_blocks_fresh_ws_promotion_price_conflict():
    stock = {
        "id": 852,
        "name": "PROMOTION_PRICE_CONFLICT",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "scanner_generation_id": "GEN-475040-1",
        "scanner_generation_observed_price": "2965",
        "current_price_observed": "2655",
        "price_delta_since_first_seen_pct": "3.10",
    }

    fields = handlers._scanner_fast_precheck_fields(
        stock,
        now_ts=1001.0,
        ws_data={
            "curr": 2655,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95},
        },
    )

    assert fields["fast_precheck_result"] == "source_quality_blocked"
    assert (
        fields["fast_precheck_reason"]
        == "scanner_promotion_price_conflicts_with_fresh_ws"
    )
    assert fields["scanner_promotion_price_consistency_state"] == "conflicted"
    assert fields["scanner_promotion_price"] == 2965
    assert (
        fields["scanner_promotion_price_source"] == "scanner_generation_observed_price"
    )
    assert fields["scanner_promotion_price_ws_curr"] == 2655
    assert fields["scanner_promotion_price_gap_pct"] > 10.0
    assert fields["scanner_promotion_price_broker_order_forbidden"] is True
    assert fields["heavy_queue_enter_epoch"] == "not_queued"


def test_scanner_promotion_price_validation_does_not_block_later_normal_move():
    stock = {
        "id": 853,
        "name": "PROMOTION_PRICE_VALIDATED",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "scanner_generation_id": "GEN-000853-1",
        "scanner_generation_observed_price": "10000",
        "current_price_observed": "10000",
        "price_delta_since_first_seen_pct": "0.10",
    }

    initial = handlers._scanner_fast_precheck_fields(
        stock,
        now_ts=1001.0,
        ws_data={
            "curr": 10010,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95},
        },
    )
    moved = handlers._scanner_promotion_price_consistency_fields(
        stock,
        {
            "curr": 10200,
            "last_ws_update_ts": 1099.95,
            "last_realtime_type_ts": {"0B": 1099.95},
        },
        now_ts=1100.0,
    )

    assert initial["scanner_promotion_price_consistency_state"] == "consistent"
    assert initial["fast_precheck_attach_anchor_price"] == 10000
    assert (
        initial["fast_precheck_attach_anchor_source"]
        == "scanner_generation_observed_price"
    )
    assert initial["fast_precheck_current_ws_price"] == 10010
    assert initial["fast_precheck_current_price_source"] == "ws_data.curr"
    assert initial["fast_precheck_current_vs_attach_delta_pct"] == 0.1
    assert initial["fast_precheck_attach_current_runtime_effect"] is False
    assert initial["fast_precheck_attach_current_allowed_runtime_apply"] is False
    assert initial["fast_precheck_attach_current_broker_order_forbidden"] is True
    assert stock["_scanner_promotion_price_validated_generation_id"] == ("GEN-000853-1")
    assert moved["scanner_promotion_price_gap_pct"] == 2.0
    assert moved["scanner_promotion_price_conflict"] is False
    assert (
        moved["scanner_promotion_price_consistency_reason"]
        == "scanner_promotion_price_initial_validation_reused"
    )


def test_scanner_promotion_price_consistency_ignores_boot_restore_price_move():
    fields = handlers._scanner_promotion_price_consistency_fields(
        {
            "scanner_generation_id": "GEN-BOOT-1",
            "scanner_generation_observed_price": 1874,
            "scanner_generation_boot_restore": True,
            "current_price_observed": 1874,
        },
        {
            "curr": 1734,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95},
        },
        now_ts=1001.0,
    )

    assert fields["scanner_promotion_price_gap_pct"] > 7.0
    assert fields["scanner_promotion_price_conflict"] is False
    assert fields["scanner_promotion_price_consistency_state"] == "not_evaluated"
    assert (
        fields["scanner_promotion_price_consistency_reason"]
        == "boot_restore_generation_price_not_initial_attach_evidence"
    )
    assert fields["scanner_promotion_price_boot_restore"] is True


def test_scanner_promotion_price_conflict_reanchors_to_fresh_executable_ws_ask():
    stock = {
        "scanner_generation_id": "GEN-REANCHOR-WS-1",
        "scanner_generation_observed_price": 10000,
        "current_price_observed": 10000,
        "effective_venue": "KRX",
        "venue": "KRX",
        "venue_resolution": "scanner_attach:explicit_krx",
        "market_session_bucket": "krx_regular",
    }
    fields = handlers._scanner_promotion_price_consistency_fields(
        stock,
        {
            "curr": 11000,
            "best_bid": 10990,
            "best_ask": 11000,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95, "0D": 1000.95},
        },
        now_ts=1001.0,
    )

    assert fields["scanner_promotion_price_original_conflict"] is True
    assert fields["scanner_promotion_price_conflict"] is False
    assert fields["scanner_promotion_price_consistency_state"] == "reanchored"
    assert fields["scanner_promotion_reanchor_allowed"] is True
    assert fields["scanner_promotion_reanchor_price"] == 11000
    assert fields["scanner_promotion_reanchor_price_type"] == "executable_ask"
    assert fields["scanner_promotion_reanchor_source"] == "ws_executable_bbo"
    assert fields["scanner_promotion_reanchor_contract_status"] == "pass"
    assert fields["scanner_promotion_reanchor_effective_venue"] == "KRX"
    assert fields["scanner_promotion_reanchor_broker_order_forbidden"] is True


def test_scanner_promotion_price_conflict_reanchors_to_fresh_rest_bbo_contract():
    fields = handlers._scanner_promotion_price_consistency_fields(
        {
            "scanner_generation_id": "GEN-REANCHOR-REST-1",
            "scanner_generation_observed_price": 10000,
            "current_price_observed": 10000,
            "effective_venue": "KRX",
            "venue": "KRX",
            "venue_resolution": "scanner_attach:explicit_krx",
            "market_session_bucket": "krx_regular",
        },
        {
            "curr": 11000,
            "best_bid": 10990,
            "best_ask": 11000,
            "last_ws_update_ts": 990.0,
            "last_realtime_type_ts": {"0B": 990.0},
            "ws_snapshot_recovery_source": "ka10004_rest_orderbook_enrichment",
            "market_data_effective_price_source": "ka10004_rest_orderbook",
            "market_data_freshness_state": "rest_enriched",
            "market_data_orderbook_state": "rest_enriched",
            "market_data_effective_quote_age_ms": 100.0,
            "market_data_effective_age_basis": "bounded_call_completion_receive_ts",
        },
        now_ts=1001.0,
    )

    assert fields["scanner_promotion_price_conflict"] is False
    assert fields["scanner_promotion_reanchor_allowed"] is True
    assert fields["scanner_promotion_reanchor_source"] == ("ka10004_rest_orderbook")
    assert fields["scanner_promotion_reanchor_contract_status"] == "pass"
    assert fields["scanner_promotion_price_ws_fresh"] is False
    assert fields["scanner_promotion_price_comparison_source_fresh"] is True
    assert fields["scanner_promotion_price_effective_curr"] == 11000
    assert fields["scanner_promotion_price_effective_source"] == (
        "ka10004_rest_orderbook"
    )


def test_scanner_promotion_price_conflict_blocks_rest_reanchor_for_nxt_venue():
    fields = handlers._scanner_promotion_price_consistency_fields(
        {
            "scanner_generation_id": "GEN-REANCHOR-NXT-REST-1",
            "scanner_generation_observed_price": 10000,
            "current_price_observed": 10000,
            "effective_venue": "NXT",
            "venue": "NXT",
            "venue_resolution": "scanner_attach:explicit_nxt",
            "market_session_bucket": "nxt",
        },
        {
            "curr": 11000,
            "best_bid": 10990,
            "best_ask": 11000,
            "last_ws_update_ts": 990.0,
            "last_realtime_type_ts": {"0B": 990.0},
            "ws_snapshot_recovery_source": "ka10004_rest_orderbook_enrichment",
            "market_data_effective_price_source": "ka10004_rest_orderbook",
            "market_data_freshness_state": "rest_enriched",
            "market_data_orderbook_state": "rest_enriched",
            "market_data_effective_quote_age_ms": 100.0,
            "market_data_effective_age_basis": "bounded_call_completion_receive_ts",
        },
        now_ts=1001.0,
    )

    assert fields["scanner_promotion_price_conflict"] is True
    assert fields["scanner_promotion_reanchor_allowed"] is False
    assert fields["scanner_promotion_reanchor_rest_venue_eligible"] is False
    assert fields["scanner_promotion_reanchor_contract_status"] == (
        "blocked_unproven_rest_venue"
    )


def test_scanner_promotion_price_conflict_keeps_block_for_non_executable_bbo():
    fields = handlers._scanner_promotion_price_consistency_fields(
        {
            "scanner_generation_id": "GEN-REANCHOR-BLOCK-1",
            "scanner_generation_observed_price": 10000,
            "current_price_observed": 10000,
            "effective_venue": "KRX",
            "venue": "KRX",
            "venue_resolution": "scanner_attach:explicit_krx",
            "market_session_bucket": "krx_regular",
        },
        {
            "curr": 11000,
            "best_bid": 10800,
            "best_ask": 11100,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95, "0D": 1000.95},
        },
        now_ts=1001.0,
    )

    assert fields["scanner_promotion_price_original_conflict"] is True
    assert fields["scanner_promotion_price_conflict"] is True
    assert fields["scanner_promotion_reanchor_allowed"] is False
    assert fields["scanner_promotion_reanchor_contract_status"] == (
        "blocked_non_executable_bbo"
    )


def test_scanner_promotion_price_conflict_keeps_block_for_stale_ws_bbo():
    fields = handlers._scanner_promotion_price_consistency_fields(
        {
            "scanner_generation_id": "GEN-REANCHOR-STALE-1",
            "scanner_generation_observed_price": 10000,
            "current_price_observed": 10000,
            "effective_venue": "KRX",
            "venue": "KRX",
            "venue_resolution": "scanner_attach:explicit_krx",
            "market_session_bucket": "krx_regular",
        },
        {
            "curr": 11000,
            "best_bid": 10990,
            "best_ask": 11000,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95, "0D": 995.0},
        },
        now_ts=1001.0,
    )

    assert fields["scanner_promotion_price_conflict"] is True
    assert fields["scanner_promotion_reanchor_allowed"] is False
    assert fields["scanner_promotion_reanchor_contract_status"] == (
        "blocked_stale_or_conflicted_source"
    )
    assert fields["scanner_promotion_reanchor_ws_last_0d_age_ms"] == 6000.0


def test_scanner_fast_precheck_persists_safe_reanchor_before_heavy_eval(
    monkeypatch,
):
    monkeypatch.setattr(handlers.time, "time", lambda: 1001.0)
    stock = {
        "id": 854,
        "name": "SAFE_REANCHOR",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-000854-1000000",
        "scanner_promotion_reason": "opening_rotation",
        "scanner_generation_id": "GEN-REANCHOR-FAST-1",
        "scanner_generation_observed_price": 10000,
        "current_price_observed": 10000,
        "entry_armed_at_epoch": 1000.0,
        "effective_venue": "KRX",
        "venue": "KRX",
        "venue_resolution": "scanner_attach:explicit_krx",
        "market_session_bucket": "krx_regular",
    }
    fields = handlers._scanner_fast_precheck_fields(
        stock,
        code="000854",
        now_ts=1001.0,
        ws_data={
            "curr": 11000,
            "best_bid": 10990,
            "best_ask": 11000,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95, "0D": 1000.95},
            "strength_momentum_history": [{"ts": 1000.95}],
        },
    )

    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert fields["scanner_promotion_price_consistency_state"] == "reanchored"
    assert stock["_scanner_promotion_price_validated_generation_id"] == (
        "GEN-REANCHOR-FAST-1"
    )
    assert stock["_scanner_promotion_reanchor_price"] == 11000
    assert stock["_scanner_promotion_reanchor_source"] == "ws_executable_bbo"


def test_scanner_fast_precheck_reuses_reanchor_as_effective_delta_baseline(
    monkeypatch,
):
    monkeypatch.setattr(handlers.time, "time", lambda: 1002.0)
    stock = {
        "id": 855,
        "name": "SAFE_REANCHOR_REUSE",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-000855-1000000",
        "scanner_promotion_reason": "opening_rotation",
        "scanner_generation_id": "GEN-REANCHOR-FAST-2",
        "scanner_generation_observed_price": 10000,
        "current_price_observed": 10000,
        "entry_armed_at_epoch": 1000.0,
        "effective_venue": "KRX",
        "venue": "KRX",
        "venue_resolution": "scanner_attach:explicit_krx",
        "market_session_bucket": "krx_regular",
    }
    first = handlers._scanner_fast_precheck_fields(
        stock,
        code="000855",
        now_ts=1001.0,
        ws_data={
            "curr": 11000,
            "best_bid": 10990,
            "best_ask": 11000,
            "last_ws_update_ts": 1000.95,
            "last_realtime_type_ts": {"0B": 1000.95, "0D": 1000.95},
            "strength_momentum_history": [{"ts": 1000.95}],
        },
    )
    second = handlers._scanner_fast_precheck_fields(
        stock,
        code="000855",
        now_ts=1002.0,
        ws_data={
            "curr": 11100,
            "best_bid": 11090,
            "best_ask": 11100,
            "last_ws_update_ts": 1001.95,
            "last_realtime_type_ts": {"0B": 1001.95, "0D": 1001.95},
            "strength_momentum_history": [{"ts": 1001.95}],
        },
    )

    assert first["scanner_promotion_effective_anchor_price"] == 11000
    assert first["fast_precheck_current_vs_attach_delta_pct"] == 0.0
    assert second["scanner_promotion_reanchor_persisted_reused"] is True
    assert second["scanner_promotion_effective_anchor_price"] == 11000
    assert second["scanner_promotion_effective_anchor_source"] == ("ws_executable_bbo")
    assert second["fast_precheck_current_vs_attach_delta_pct"] == 0.909091


def test_scanner_fast_precheck_allows_configured_high_delta_stale_ws_relief(
    monkeypatch,
):
    emitted = []
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STALE_WS_FULL_EVAL_RELIEF_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_RISING_STALE_WS_FULL_EVAL_MIN_DELTA_PCT", "1.0"
    )
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 851,
        "name": "RISING_STALE_WS",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "3.40",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000851",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1000.0,
            "ws_snapshot_recovery_source": "ws_manager_latest_data",
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert fields["fast_precheck_reason"] == "rising_stale_ws_snapshot_full_eval_relief"
    assert fields["fast_precheck_stale_ws_relief_applied"] is True
    assert fields["fast_precheck_positive_delta_pct"] == 3.4
    assert (
        fields["fast_precheck_stale_ws_relief_block_reason"]
        == "applied_rising_stale_ws_relief"
    )
    assert (
        fields["fast_precheck_rest_supplement_status"] == "rest_supplement_not_present"
    )
    assert fields["fast_precheck_realtime_relief_scope"] == "rising_entry_relief_only"
    assert fields["heavy_queue_enter_epoch"] == "1012.000"
    assert stock["_scanner_fast_precheck_result"] == "eligible_for_heavy_entry_eval"


def test_scanner_fast_precheck_allows_subscription_recheck_with_fresh_realtime_strength(
    monkeypatch,
):
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: 1012.0)
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 86,
        "name": "RISING_RECHECK_PASS",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "price_delta_since_first_seen_pct": "1.20",
    }

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000086",
        now_ts=1012.0,
        ws_data={
            "curr": 1200,
            "last_ws_update_ts": 1007.0,
            "received_types": {"0B", "0D"},
            "last_realtime_type_ts": {"0B": 1003.0, "0D": 1002.0},
            "strength_momentum_history": [{"ts": 1003.5}],
            "scanner_subscription_recheck_entry_relief": True,
            "scanner_subscription_recheck_age_sec": 5.0,
            "scanner_subscription_recheck_fresh_sec": 10.0,
        },
        throttle_sec=0,
    )

    fields = emitted[-1]["fields"]
    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert (
        fields["fast_precheck_reason"]
        == "rising_subscription_recheck_fresh_realtime_evidence"
    )
    assert fields["fast_precheck_realtime_relief_applied"] is False
    assert fields["fast_precheck_subscription_recheck_relief_applied"] is True
    assert fields["fast_precheck_realtime_relief_scope"] == "rising_entry_relief_only"
    assert fields["heavy_queue_enter_epoch"] == "1012.000"
    assert stock["_scanner_fast_precheck_result"] == "eligible_for_heavy_entry_eval"


def test_log_ai_confirmed_terminal_no_budget_emits_contract_fields(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    stock = {
        "id": 44,
        "name": "AIWAIT",
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_source_quality_fields": {
            "tick_source_quality_fields_sent": True,
            "tick_context_quality": "fresh_computed",
            "quote_age_source": "last_ws_update_ts",
        },
    }

    _log_ai_confirmed_terminal_no_budget(
        stock,
        "000035",
        terminal_reason="first_ai_wait_big_bite_not_confirmed",
        source_stage="first_ai_wait",
        ai_decision={"action": "BUY", "score": 78},
        ai_score=78,
    )

    assert emitted[-1]["stage"] == "ai_confirmed_terminal_no_budget"
    fields = emitted[-1]["fields"]
    assert fields["decision_authority"] == "ai_confirmed_terminal_attribution_only"
    assert fields["primary_decision_metric"] == "funnel_count"
    assert fields["source_quality_gate"] == "terminal_reason_contract_fields_present"
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert fields["allowed_runtime_apply"] is False
    assert fields["terminal_reason"] == "first_ai_wait_big_bite_not_confirmed"
    assert fields["source_stage"] == "first_ai_wait"
    assert fields["ai_score"] == "78.0"
    assert fields["ai_action"] == "BUY"
    assert fields["tick_source_quality_fields_sent"] is True
    assert fields["tick_context_quality"] == "fresh_computed"
    assert fields["quote_age_source"] == "last_ws_update_ts"


def test_first_ai_big_bite_wait_does_not_block_strong_buy():
    assert (
        _should_first_ai_wait_for_big_bite(
            {"action": "BUY", "score": 82},
            82,
            big_bite_confirmed=False,
            entry_score_threshold=75,
        )
        is False
    )
    assert (
        _should_first_ai_wait_for_big_bite(
            {"action": "WAIT", "score": 74},
            74,
            big_bite_confirmed=False,
            entry_score_threshold=75,
        )
        is True
    )
    assert (
        _should_first_ai_wait_for_big_bite(
            {"action": "BUY", "score": 74},
            74,
            big_bite_confirmed=False,
            entry_score_threshold=75,
        )
        is True
    )
    assert (
        _should_first_ai_wait_for_big_bite(
            {"action": "WAIT", "score": 62},
            62,
            big_bite_confirmed=True,
            entry_score_threshold=75,
        )
        is False
    )


def test_canonical_wait_probe_handoff_precedes_legacy_first_ai_wait(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION", "false"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT", "true"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv(
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "true"
    )
    decision = {
        "action": "WAIT",
        "decision_quality_contract_status": "pass",
        "edge_state": "EDGE",
        "entry_probe_intent": True,
        "entry_probe_intent_status": "eligible_wait_probe",
        "evidence": {"trigger": "recovery_required"},
    }

    assert handlers._canonical_wait_probe_handoff_active(decision)
    assert handlers._canonical_wait_probe_handoff_active(
        {
            **decision,
            "edge_state": None,
            "decision_quality_model_edge_state": "EDGE",
        }
    )
    assert not handlers._canonical_wait_probe_handoff_active(
        {**decision, "entry_probe_intent": False}
    )
    assert not handlers._canonical_wait_probe_handoff_active(
        {**decision, "decision_quality_contract_status": "semantic_rejected"}
    )
    assert not handlers._canonical_wait_probe_handoff_active(
        {**decision, "edge_state": "NO_EDGE"}
    )
    assert not handlers._canonical_wait_probe_handoff_active(
        {**decision, "action": "DROP"}
    )
    assert not handlers._canonical_wait_probe_handoff_active(
        {**decision, "evidence": {"trigger": "hold"}}
    )
    assert not handlers._canonical_wait_probe_handoff_active(
        {
            **decision,
            "evidence": {
                "trigger": "recovery_required",
                "adverse_risk": "blocking",
            },
        }
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED", "false")
    assert not handlers._canonical_wait_probe_handoff_active(decision)


def test_canonical_wait_probe_micro_pending_has_no_submit_authority(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
        "false",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
        "true",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv(
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "true"
    )
    decision = {
        "action": "WAIT",
        "decision_quality_contract_status": "pass",
        "edge_state": "EDGE",
        "entry_probe_intent": True,
        "entry_probe_intent_status": "eligible_wait_probe",
        "evidence": {
            "trigger": "recovery_required",
            "adverse_risk": "non_blocking",
        },
    }
    recheck = type(
        "Recheck",
        (),
        {
            "allowed": False,
            "reason": "strong_micro_confirmation_missing",
        },
    )()

    assert handlers._canonical_wait_probe_recheck_pending(
        recheck,
        decision,
        ai_action="WAIT",
        now_ts=1_785_737_300.0,
    )
    recheck.allowed = True
    assert not handlers._canonical_wait_probe_recheck_pending(
        recheck,
        decision,
        ai_action="WAIT",
        now_ts=1_785_737_300.0,
    )


def test_entry_opportunity_recheck_pending_window_is_bounded(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_PENDING_TTL_SEC", "15")

    active = handlers._entry_opportunity_recheck_pending_window(
        {
            "entry_opportunity_recheck_pending": True,
            "entry_opportunity_recheck_pending_since": 100.0,
        },
        now_ts=114.9,
    )
    expired = handlers._entry_opportunity_recheck_pending_window(
        {
            "entry_opportunity_recheck_pending": True,
            "entry_opportunity_recheck_pending_since": 100.0,
        },
        now_ts=115.0,
    )

    assert active["pending_active"] is True
    assert expired["pending_active"] is False
    assert expired["pending_ttl_sec"] == 15.0

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_PENDING_TTL_SEC", "999")
    clamped = handlers._entry_opportunity_recheck_pending_window({}, now_ts=200.0)
    assert clamped["pending_ttl_sec"] == 30.0


def test_watching_handler_consumes_pending_with_bounded_fresh_ai_recheck():
    source = inspect.getsource(handlers._handle_watching_strategy_branch)
    pending_slice = source[
        source.index("pending_recheck_requested") : source.index(
            "ai_wait_rebound_recheck_pending"
        )
    ]

    assert 'stock.get("entry_opportunity_recheck_pending")' in pending_slice
    assert '"entry_opportunity_recheck_pending_fresh_ai"' in pending_slice
    assert '"entry_opportunity_recheck_pending_fresh_ai_requested"' in pending_slice
    assert '"entry_opportunity_recheck_pending_parent_snapshot_id"' in pending_slice
    assert '"entry_opportunity_recheck_pending_recheck_after_epoch"' in pending_slice
    assert '"entry_opportunity_recheck_pending_expired"' in pending_slice
    assert "cooldowns[code] = now_ts + cooldown_time" in pending_slice
    assert "actual_order_submitted=False" in pending_slice
    assert "broker_order_forbidden=True" in pending_slice

    reset = handlers._entry_opportunity_recheck_pending_window(
        {
            "entry_opportunity_recheck_pending": False,
            "entry_opportunity_recheck_pending_since": 100.0,
        },
        now_ts=200.0,
    )
    assert reset["pending_since"] == 200.0
    assert reset["pending_active"] is True


def test_first_ai_big_bite_wait_arms_rebound_anchor_for_score_band(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_MIN_SCORE", "65")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_MAX_SCORE", "74")
    cooldowns = {}
    stock = {"strategy": "SCALPING", "position_tag": "SCANNER"}

    result = handlers._arm_ai_wait_rebound_recheck_anchor(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        ai_decision={
            "action": "WAIT",
            "score": 70,
            "reason": "big bite not confirmed",
            "buy_pressure_10t": 82.0,
            "curr_vs_micro_vwap_bp": 4.0,
            "tick_acceleration_ratio": 1.2,
            "tick_aggressor_trusted_count": 3,
            "tick_aggressor_pressure_usable": True,
            "micro_vwap_available": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": True,
            "minute_candle_latest_age_ms": 7000,
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "tick_accel_source": "computed_10ticks",
        },
        ai_score=70,
        config={"AI_WAIT_DROP_COOLDOWN": 180},
        cooldowns=cooldowns,
        now_ts=100.0,
        source_stage="first_ai_wait_big_bite_not_confirmed",
    )

    assert result["ai_wait_rebound_anchor_armed"] is True
    assert cooldowns["123456"] == 280.0
    assert stock["ai_wait_cooldown_anchor_action"] == "WAIT"
    assert stock["ai_wait_cooldown_anchor_score"] == 70.0
    assert stock["last_watching_ai_feature_probe"]["buy_pressure"] == 82.0
    assert (
        stock["last_watching_ai_feature_probe"]["tick_aggressor_pressure_usable"]
        is True
    )
    assert stock["last_watching_ai_feature_probe"]["micro_vwap_available"] is True
    assert stock["last_watching_ai_feature_probe"]["minute_candle_window_fresh"] is True


def test_first_ai_big_bite_wait_anchor_does_not_infer_micro_vwap_from_numeric_only(
    monkeypatch,
):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_ENABLED", "true")
    cooldowns = {}
    stock = {"strategy": "SCALPING", "position_tag": "SCANNER"}

    result = handlers._arm_ai_wait_rebound_recheck_anchor(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        ai_decision={
            "action": "WAIT",
            "score": 70,
            "reason": "numeric micro only",
            "buy_pressure_10t": 82.0,
            "curr_vs_micro_vwap_bp": 4.0,
            "tick_acceleration_ratio": 1.2,
            "tick_aggressor_trusted_count": 3,
            "tick_aggressor_pressure_usable": True,
        },
        ai_score=70,
        config={"AI_WAIT_DROP_COOLDOWN": 180},
        cooldowns=cooldowns,
        now_ts=100.0,
        source_stage="first_ai_wait_big_bite_not_confirmed",
    )

    assert result["ai_wait_rebound_anchor_armed"] is True
    probe = stock["last_watching_ai_feature_probe"]
    assert probe["curr_vs_micro_vwap_bp"] == 4.0
    assert probe["micro_vwap_available"] is False
    assert probe["minute_candle_window_fresh"] is False


def test_first_ai_big_bite_wait_anchor_treats_score_band_as_prior(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_MIN_SCORE", "65")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_AI_WAIT_REBOUND_RECHECK_MAX_SCORE", "74")
    cooldowns = {}
    stock = {"strategy": "SCALPING", "position_tag": "SCANNER"}

    result = handlers._arm_ai_wait_rebound_recheck_anchor(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        ai_decision={
            "action": "WAIT",
            "score": 55,
            "reason": "low score but strong micro",
            "buy_pressure_10t": 88.0,
            "curr_vs_micro_vwap_bp": 4.0,
            "tick_acceleration_ratio": 1.2,
            "tick_aggressor_trusted_count": 3,
            "tick_aggressor_pressure_usable": True,
            "micro_vwap_available": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": True,
        },
        ai_score=55,
        config={"AI_WAIT_DROP_COOLDOWN": 180},
        cooldowns=cooldowns,
        now_ts=100.0,
        source_stage="first_ai_wait_big_bite_not_confirmed",
    )

    assert result["ai_wait_rebound_anchor_armed"] is True
    assert result["ai_wait_rebound_anchor_score_prior_band"] == "outside_candidate_band"
    assert result["ai_wait_rebound_anchor_score_gate_converted_to_prior"] is True
    assert result["ai_wait_rebound_anchor_hard_gate_veto"] is False


def test_build_ai_overlap_log_fields_includes_momentum_and_profile():
    stock = {"entry_momentum_tag": "SURGE", "entry_threshold_profile": "RELAX"}

    fields = _build_ai_overlap_log_fields(
        stock=stock,
        ai_score=78,
        momentum_tag="MIDDLE",
        threshold_profile="STRICT",
        overbought_blocked=False,
        blocked_stage="blocked_strength_momentum",
        overlap_snapshot={},
    )

    assert fields["momentum_tag"] == "MIDDLE"
    assert fields["threshold_profile"] == "STRICT"
    assert fields["blocked_stage"] == "blocked_strength_momentum"
    assert fields["ai_score"] == "78.0"


def test_extract_ai_overlap_snapshot_uses_ws_day_high_low_without_candles():
    snapshot = _extract_ai_overlap_snapshot(
        ws_data={
            "curr": 9800,
            "high": 10000,
            "low": 9500,
            "v_pw": 123.4,
            "buy_ratio": 61.2,
        }
    )

    assert round(snapshot["distance_from_day_high_pct"], 3) == -2.0
    assert round(snapshot["intraday_range_pct"], 3) == 5.263
    assert snapshot["latest_strength"] == 123.4
    assert snapshot["buy_pressure_10t"] == 61.2


def test_extract_ai_overlap_snapshot_marks_feature_packet_conflict_as_derived():
    class FeatureEngine:
        @staticmethod
        def _extract_scalping_features(ws_data, ticks, candles):
            return {
                "distance_from_day_high_pct": 0.0,
                "intraday_range_pct": 0.0,
            }

    snapshot = _extract_ai_overlap_snapshot(
        ws_data={"curr": 9800, "high": 10000, "low": 9500},
        ai_engine=FeatureEngine(),
    )

    assert snapshot["distance_from_day_high_pct"] == 0.0
    assert (
        snapshot["distance_from_day_high_pct_observation_state"]
        == "derived_feature_packet_without_consistent_raw_range"
    )
    assert (
        snapshot["intraday_range_pct_observation_state"]
        == "derived_feature_packet_without_consistent_raw_range"
    )


def test_extract_ai_overlap_snapshot_keeps_consistent_observed_zero_provenance():
    class FeatureEngine:
        @staticmethod
        def _extract_scalping_features(ws_data, ticks, candles):
            return {
                "distance_from_day_high_pct": 0.0,
                "intraday_range_pct": 0.0,
            }

    snapshot = _extract_ai_overlap_snapshot(
        ws_data={"curr": 10000, "high": 10000, "low": 10000},
        ai_engine=FeatureEngine(),
    )

    assert snapshot["distance_from_day_high_pct_observation_state"].startswith(
        "observed_"
    )
    assert snapshot["intraday_range_pct_observation_state"].startswith("observed_")


def test_extract_ai_overlap_snapshot_accepts_feature_packet_range_provenance():
    class FeatureEngine:
        @staticmethod
        def _extract_scalping_features(ws_data, ticks, candles):
            return {
                "distance_from_day_high_pct": 0.0,
                "intraday_range_pct": 16.0,
                "distance_from_day_high_pct_observation_state": (
                    "observed_feature_packet_recent_candles"
                ),
                "intraday_range_pct_observation_state": (
                    "observed_feature_packet_recent_candles"
                ),
            }

    snapshot = _extract_ai_overlap_snapshot(
        ws_data={"curr_price": 3008},
        recent_candles=[{"고가": 3008, "저가": 2593}],
        ai_engine=FeatureEngine(),
    )

    assert snapshot["distance_from_day_high_pct"] == 0.0
    assert snapshot["distance_from_day_high_pct_observation_state"].startswith(
        "observed_"
    )
    assert snapshot["intraday_range_pct_observation_state"].startswith("observed_")


def test_extract_ai_overlap_snapshot_ignores_price_change_heuristic_tick_direction():
    snapshot = _extract_ai_overlap_snapshot(
        ws_data={
            "curr": 9800,
            "high": 10000,
            "low": 9500,
            "v_pw": 123.4,
            "buy_ratio": 61.2,
        },
        recent_ticks=[
            {
                "time": "09:00:10",
                "price": 9810,
                "volume": 120,
                "dir": "BUY",
                "aggressor_side": "BUY",
                "aggressor_source": "price_change_heuristic",
                "strength": 130.0,
            },
            {
                "time": "09:00:09",
                "price": 9800,
                "volume": 80,
                "dir": "SELL",
                "aggressor_side": "SELL",
                "aggressor_source": "price_change_heuristic",
                "strength": 120.0,
            },
        ],
    )

    assert snapshot["latest_strength"] == 130.0
    assert snapshot["buy_pressure_10t"] == 61.2


def test_should_run_score65_74_recovery_probe_uses_score_band_as_prior(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=65,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 70.0,
            "tick_accel": 1.35,
            "micro_vwap_bp": 12.0,
            "large_sell_print": False,
        }
    )

    assert (
        _should_run_score65_74_recovery_probe(
            {"action": "WAIT"},
            72,
            {"latency_state": "OK"},
            [],
            [],
            None,
            feature_probe=feature_probe,
        )
        is True
    )
    assert (
        _should_run_score65_74_recovery_probe(
            {"action": "WAIT"},
            75,
            {"latency_state": "OK"},
            [],
            [],
            None,
            feature_probe=feature_probe,
        )
        is True
    )


def test_score65_74_recovery_probe_cannot_reopen_semantic_rejection(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 91.0,
            "tick_accel": 1.6,
            "micro_vwap_bp": 45.0,
            "large_sell_print": False,
        }
    )
    decision = _score65_74_recovery_probe_decision(
        {
            "action": "DROP",
            "reason": "decision_quality_v2_7_semantic_rejected",
            "decision_quality_contract_status": "semantic_rejected",
            "decision_quality_score_semantics": "fail_closed_not_model_quality_score",
        },
        0,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
    )

    assert decision == {
        "allowed": False,
        "evaluated": False,
        "score65_74_recovery_probe_skip_reason": "ai_semantic_contract_rejected",
    }


def test_score65_74_probe_delegates_canonical_wait_probe_to_recheck_owner(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
        "false",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
        "true",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv(
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "true"
    )

    decision = _score65_74_recovery_probe_decision(
        {
            "action": "WAIT",
            "decision_quality_contract_status": "pass",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "evidence": {
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        68,
        {"latency_state": "SAFE"},
        [],
        [],
        None,
    )

    assert decision == {
        "allowed": False,
        "evaluated": False,
        "score65_74_recovery_probe_skip_reason": (
            "delegated_to_entry_opportunity_recheck_runtime"
        ),
    }


def test_score65_74_recovery_probe_enforces_micro_context_hard_gate(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    weak_micro_feature_probe = _trusted_pressure(
        {
            "buy_pressure": 10.0,
            "tick_accel": 0.1,
            "micro_vwap_bp": -25.0,
            "large_sell_print": True,
        }
    )

    assert (
        _should_run_score65_74_recovery_probe(
            {"action": "WAIT"},
            62,
            {"latency_state": "OK"},
            [],
            [],
            None,
            feature_probe=weak_micro_feature_probe,
        )
        is False
    )
    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=weak_micro_feature_probe,
    )
    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == (
        "buy_pressure_below_min|tick_accel_below_min|micro_vwap_below_min"
    )
    assert (
        _should_run_score65_74_recovery_probe(
            {"action": "WAIT"},
            62,
            {"latency_state": "OK"},
            [],
            [],
            None,
            feature_probe={**weak_micro_feature_probe, "quote_stale": True},
        )
        is False
    )
    assert (
        _should_run_score65_74_recovery_probe(
            {"action": "WAIT"},
            72,
            {"latency_state": "DANGER"},
            [],
            [],
            None,
            feature_probe=weak_micro_feature_probe,
        )
        is False
    )


def test_score65_74_recovery_probe_blocks_missing_pressure_provenance(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        72,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe={
            "buy_pressure": 91.0,
            "tick_accel": 1.6,
            "micro_vwap_bp": 45.0,
        },
    )

    assert decision["allowed"] is False
    assert (
        decision["score65_74_recovery_probe_skip_reason"] == "source_quality_hard_block"
    )


def test_score65_74_recovery_probe_allows_scanner_quote_stale_only_with_refresh_guard(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_ALLOW_QUOTE_STALE_WITH_PRE_SUBMIT_REFRESH=True,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_QUOTE_STALE_AGE_MS=7000,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 83.0,
            "tick_accel": 1.55,
            "micro_vwap_bp": 12.0,
            "tick_context_stale": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "quote_stale": True,
            "quote_age_ms": 2500,
        }
    )

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "position and speed advantage"},
        74,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
        stock={
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "status": "WATCHING",
            "scanner_promotion_reason": "price_jump_multisource_confirmation",
            "source_signature": "PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE",
        },
    )

    assert decision["allowed"] is True
    assert decision["score65_74_recovery_probe_quote_stale_relief_applied"] is True
    assert decision["score65_74_recovery_probe_quote_stale_relief_reason"] == (
        "quote_stale_only_pre_submit_refresh_required"
    )


def test_score65_74_recovery_probe_quote_stale_relief_stays_scanner_real_only(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_ALLOW_QUOTE_STALE_WITH_PRE_SUBMIT_REFRESH=True,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 83.0,
            "tick_accel": 1.55,
            "micro_vwap_bp": 12.0,
            "tick_context_stale": False,
            "quote_stale": True,
            "quote_age_ms": 2500,
        }
    )

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "position and speed advantage"},
        74,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
        stock={
            "strategy": "SCALPING",
            "position_tag": "VWAP_RECLAIM",
            "status": "WATCHING",
        },
    )

    assert decision["allowed"] is False
    assert (
        decision["score65_74_recovery_probe_skip_reason"] == "source_quality_hard_block"
    )
    assert decision["score65_74_recovery_probe_quote_stale_relief_reason"] == (
        "scope_not_real_scanner_rising_watching"
    )


def test_score65_74_recovery_probe_quote_stale_relief_allows_rank_rising_scanner(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_ALLOW_QUOTE_STALE_WITH_PRE_SUBMIT_REFRESH=True,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_QUOTE_STALE_AGE_MS=7000,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 86.0,
            "tick_accel": 1.55,
            "micro_vwap_bp": 18.0,
            "tick_context_stale": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "quote_stale": True,
            "quote_age_ms": 4500,
        }
    )

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "rank and value expansion"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
        stock={
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "status": "WATCHING",
            "scanner_promotion_reason": "rank_jump_acceleration",
            "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            "price_delta_since_first_seen_pct": "1.77",
        },
    )

    assert decision["allowed"] is True
    assert decision["score65_74_recovery_probe_quote_stale_relief_applied"] is True
    assert decision["score65_74_recovery_probe_quote_stale_relief_reason"] == (
        "quote_stale_only_pre_submit_refresh_required"
    )


def test_score65_74_recovery_probe_quote_stale_relief_blocks_thin_rank_rising_scanner(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_ALLOW_QUOTE_STALE_WITH_PRE_SUBMIT_REFRESH=True,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 86.0,
            "tick_accel": 1.55,
            "micro_vwap_bp": 18.0,
            "tick_context_stale": False,
            "quote_stale": True,
            "quote_age_ms": 4500,
        }
    )

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "rank and value expansion"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
        stock={
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "status": "WATCHING",
            "scanner_promotion_reason": "rank_jump_acceleration",
            "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            "price_delta_since_first_seen_pct": "0.25",
        },
    )

    assert decision["allowed"] is False
    assert (
        decision["score65_74_recovery_probe_skip_reason"] == "source_quality_hard_block"
    )
    assert decision["score65_74_recovery_probe_quote_stale_relief_reason"] == (
        "scope_not_real_scanner_rising_watching"
    )


def test_score65_74_recovery_probe_scanner_rising_micro_vwap_relief_is_narrow(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_SCANNER_RISING_MICRO_VWAP_RELIEF_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_SCANNER_RISING_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 83.0,
            "tick_accel": 1.55,
            "micro_vwap_bp": 2.0,
            "tick_context_stale": False,
            "quote_stale": False,
        }
    )

    scanner_decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "position and speed advantage"},
        74,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
        stock={
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "status": "WATCHING",
            "scanner_promotion_reason": "price_jump_multisource_confirmation",
            "source_signature": "PRICE_JUMP_START,REALTIME_RANK_START,VOLUME_SURGE_POSITIVE",
        },
    )
    non_scanner_decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "position and speed advantage"},
        74,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
        stock={
            "strategy": "SCALPING",
            "position_tag": "VWAP_RECLAIM",
            "status": "WATCHING",
        },
    )

    assert scanner_decision["allowed"] is True
    assert (
        scanner_decision[
            "score65_74_recovery_probe_scanner_rising_micro_relief_applied"
        ]
        is True
    )
    assert non_scanner_decision["allowed"] is False
    assert (
        non_scanner_decision["score65_74_recovery_probe_skip_reason"]
        == "micro_vwap_below_min"
    )


def test_score65_74_recovery_probe_strong_micro_override_relaxes_tick_only_veto(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_BUY_PRESSURE=85.0,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_MICRO_VWAP_BP=30.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 91.0,
                "tick_accel": 0.0,
                "micro_vwap_bp": 45.0,
                "tick_accel_source": "computed_10ticks",
                "tick_context_quality": "fresh_computed",
                "tick_context_stale": False,
                "quote_stale": False,
            }
        ),
    )

    assert decision["allowed"] is True
    assert decision["score65_74_recovery_probe_strong_micro_override_applied"] is True
    assert decision["score65_74_recovery_probe_skip_reason"] == ""


def test_score65_74_recovery_probe_requires_meaningful_micro_vwap_floor(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "reason": "Position advantage but still checking recovery"},
        74,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 87.0,
                "tick_accel": 1.25,
                "micro_vwap_bp": 4.11,
            }
        ),
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "micro_vwap_below_min"
    assert decision["score65_74_recovery_probe_min_micro_vwap_bp"] == 10.0
    assert decision["score65_74_recovery_probe_configured_min_micro_vwap_bp"] == 0.0


def test_score65_74_recovery_probe_blocks_negative_wait_reason_even_when_micro_passes(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {
            "action": "WAIT",
            "reason": (
                "mixed signals: tick_acceleration_ratio below BUY threshold "
                "and absorption not confirmed"
            ),
        },
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 91.0,
                "tick_accel": 1.6,
                "micro_vwap_bp": 45.0,
            }
        ),
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == (
        "ai_wait_negative_reason_veto:mixed_signal"
    )


def test_score65_74_recovery_probe_does_not_veto_positive_reason_with_negative_absent(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {
            "action": "WAIT",
            "reason": "negative sell pressure absent; recovery microstructure is improving",
        },
        72,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 91.0,
                "tick_accel": 1.6,
                "micro_vwap_bp": 45.0,
            }
        ),
    )

    assert decision["allowed"] is True
    assert decision["score65_74_recovery_probe_skip_reason"] == ""


def test_score65_74_recovery_probe_strong_micro_override_does_not_relax_weak_micro(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_BUY_PRESSURE=85.0,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_MICRO_VWAP_BP=30.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 91.0,
                "tick_accel": 0.0,
                "micro_vwap_bp": 12.0,
                "tick_accel_source": "computed_10ticks",
                "tick_context_quality": "fresh_computed",
                "tick_context_stale": False,
                "quote_stale": False,
            }
        ),
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_strong_micro_override_applied"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "tick_accel_below_min"


def test_score65_74_recovery_probe_strong_micro_override_skips_when_entry_tuning_live(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_BUY_PRESSURE=85.0,
        AI_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_MICRO_VWAP_BP=30.0,
        ENTRY_STAGE_LIVE_TUNING_SELECTED=True,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 91.0,
                "tick_accel": 0.0,
                "micro_vwap_bp": 45.0,
                "tick_accel_source": "computed_10ticks",
                "tick_context_quality": "fresh_computed",
                "tick_context_stale": False,
                "quote_stale": False,
            }
        ),
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_strong_micro_override_enabled"] is False
    assert decision["score65_74_recovery_probe_strong_micro_override_applied"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "tick_accel_below_min"


def test_score65_74_recovery_probe_blocks_lg_innotek_style_falling_wait(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK", "curr": 1050000},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 50.0,
                "tick_accel": 1.0,
                "micro_vwap_bp": -8.34,
                "large_sell_print": False,
            }
        ),
    )

    assert decision["allowed"] is False
    assert "micro_vwap_below_min" in decision["score65_74_recovery_probe_skip_reason"]
    assert "tick_accel_below_min" in decision["score65_74_recovery_probe_skip_reason"]


def test_score65_74_recovery_probe_blocks_same_symbol_cooldown(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=60,
        AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=74,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_decision(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK", "curr": 1050000},
        [],
        [],
        None,
        feature_probe=_trusted_pressure(
            {
                "buy_pressure": 80.0,
                "tick_accel": 1.5,
                "micro_vwap_bp": 3.0,
                "large_sell_print": False,
            }
        ),
        stock={"score65_74_recovery_probe_cancel_cooldown_until": 2_000.0},
        code="011070",
        now_ts=1_000.0,
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == (
        "same_symbol_cooldown_active:entry_cancel_confirmed"
    )


def test_score65_74_recovery_probe_block_contract_fields_are_single_source_of_authority():
    fields = dict(
        **_score65_74_recovery_probe_block_contract_fields(),
        applied=False,
        threshold_family="score65_74_recovery_probe",
        score65_74_recovery_probe_skip_reason="tick_accel_below_min",
        ai_score="62.0",
        buy_pressure="70.00",
        tick_accel="0.900",
        micro_vwap_bp="2.00",
        score65_74_recovery_probe_min_buy_pressure="65.00",
        score65_74_recovery_probe_min_tick_accel="1.200",
        score65_74_recovery_probe_min_micro_vwap_bp="0.00",
    )

    assert fields["runtime_effect"] is False
    assert (
        fields["decision_authority"]
        == "score65_74_recovery_probe_block_observation_only"
    )
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True


def test_score65_74_recovery_probe_log_fields_preserve_micro_vwap_provenance():
    fields = handlers._build_tick_source_quality_log_fields(
        {
            "tick_aggressor_trusted_count": 4,
            "tick_aggressor_pressure_usable": True,
            "micro_vwap_available": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "minute_candle_window_fresh": True,
            "minute_candle_latest_age_ms": 12000,
            "entry_candle_context_enabled": True,
            "entry_candle_venue": "KRX",
            "entry_candle_route_equivalence_proven": True,
            "entry_candle_source_quality_status": "fresh_consistent",
            "entry_candle_decision_window_quality_status": "fresh_consistent",
            "entry_candle_decision_window_missing_bar_count": 0,
            "entry_candle_session_integrity_status": "blocked",
            "entry_candle_session_integrity_missing_bar_count": 30,
            "entry_candle_hybrid_guard_result": "preserve_neutral_or_supportive",
        }
    )

    assert fields["tick_aggressor_trusted_count"] == 4
    assert fields["tick_aggressor_pressure_usable"] is True
    assert fields["micro_vwap_available"] is True
    assert fields["minute_candle_context_quality"] == "fresh_bar_window"
    assert fields["minute_candle_window_fresh"] is True
    assert fields["minute_candle_latest_age_ms"] == 12000
    assert fields["entry_candle_context_enabled"] is True
    assert fields["entry_candle_venue"] == "KRX"
    assert fields["entry_candle_route_equivalence_proven"] is True
    assert fields["entry_candle_source_quality_status"] == "fresh_consistent"
    assert fields["entry_candle_decision_window_quality_status"] == "fresh_consistent"
    assert fields["entry_candle_decision_window_missing_bar_count"] == "0"
    assert fields["entry_candle_session_integrity_status"] == "blocked"
    assert fields["entry_candle_session_integrity_missing_bar_count"] == "30"
    assert (
        fields["entry_candle_hybrid_guard_result"] == "preserve_neutral_or_supportive"
    )
    assert fields["tick_source_quality_fields_sent"] is True


def test_score65_74_recovery_probe_feature_extraction_preserves_minute_provenance():
    class FakeEngine:
        def _extract_scalping_features(self, ws_data, recent_ticks, recent_candles):
            return {
                "buy_pressure_10t": 82.0,
                "tick_acceleration_ratio": 1.45,
                "curr_vs_micro_vwap_bp": 22.5,
                "micro_vwap_available": True,
                "minute_candle_context_quality": "fresh_bar_window",
                "minute_candle_window_fresh": True,
                "minute_candle_latest_age_ms": 9000,
                "tick_aggressor_trusted_count": 5,
                "tick_aggressor_pressure_usable": True,
            }

    probe = handlers._extract_buy_recovery_probe_features(FakeEngine(), {}, [], [])

    assert probe["micro_vwap_bp"] == 22.5
    assert probe["micro_vwap_available"] is True
    assert probe["minute_candle_context_quality"] == "fresh_bar_window"
    assert probe["minute_candle_window_fresh"] is True
    assert probe["minute_candle_latest_age_ms"] == 9000
    assert probe["tick_aggressor_trusted_count"] == 5
    assert probe["tick_aggressor_pressure_usable"] is True


def test_score65_74_recovery_probe_reuse_guard_preserves_source_provenance(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_reuse_guard(
        {
            "score65_74_recovery_probe_last_buy_pressure": 84.0,
            "score65_74_recovery_probe_last_tick_accel": 1.5,
            "score65_74_recovery_probe_last_micro_vwap_bp": 24.0,
            "score65_74_recovery_probe_last_micro_vwap_available": True,
            "score65_74_recovery_probe_last_minute_candle_context_quality": "fresh_bar_window",
            "score65_74_recovery_probe_last_minute_candle_window_fresh": True,
            "score65_74_recovery_probe_last_minute_candle_latest_age_ms": 8000,
            "score65_74_recovery_probe_last_tick_aggressor_trusted_count": 6,
            "score65_74_recovery_probe_last_tick_aggressor_pressure_usable": True,
        },
        "011070",
        {"curr": 10500},
        now_ts=1_000.0,
    )

    assert decision["allowed"] is True
    assert decision["micro_vwap_available"] is True
    assert decision["minute_candle_context_quality"] == "fresh_bar_window"
    assert decision["minute_candle_window_fresh"] is True
    assert decision["minute_candle_latest_age_ms"] == 8000
    assert decision["tick_aggressor_trusted_count"] == 6
    assert decision["tick_aggressor_pressure_usable"] is True


def test_score65_74_recovery_probe_reuse_guard_blocks_missing_tick_provenance(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_reuse_guard(
        {
            "score65_74_recovery_probe_last_buy_pressure": 84.0,
            "score65_74_recovery_probe_last_tick_accel": 1.5,
            "score65_74_recovery_probe_last_micro_vwap_bp": 24.0,
            "score65_74_recovery_probe_last_micro_vwap_available": True,
            "score65_74_recovery_probe_last_minute_candle_context_quality": "fresh_bar_window",
            "score65_74_recovery_probe_last_minute_candle_window_fresh": True,
            "score65_74_recovery_probe_last_minute_candle_latest_age_ms": 8000,
            "score65_74_recovery_probe_last_tick_aggressor_trusted_count": 0,
            "score65_74_recovery_probe_last_tick_aggressor_pressure_usable": False,
        },
        "011070",
        {"curr": 10500},
        now_ts=1_000.0,
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == (
        "source_quality_hard_block"
    )


def test_score65_74_recovery_probe_success_contract_fields_close_forbidden_authority():
    fields = _score65_74_recovery_probe_success_contract_fields()

    assert fields["metric_role"] == "bounded_tunable"
    assert fields["decision_authority"] == "score65_74_recovery_probe_entry_unlock_only"
    assert fields["runtime_effect"] is True
    assert fields["allowed_runtime_apply"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert "runtime_threshold_apply" in fields["forbidden_uses"]
    assert "broker_guard_bypass" in fields["forbidden_uses"]
    assert "stale_submit_bypass" in fields["forbidden_uses"]


def test_score65_74_recovery_probe_reuse_guard_blocks_stale_armed_cancel_cooldown(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _score65_74_recovery_probe_reuse_guard(
        {
            "score65_74_recovery_probe_cancel_cooldown_until": 2_000.0,
            "score65_74_recovery_probe_last_buy_pressure": 80.0,
            "score65_74_recovery_probe_last_tick_accel": 1.5,
            "score65_74_recovery_probe_last_micro_vwap_bp": 2.0,
            "score65_74_recovery_probe_last_micro_vwap_available": True,
            "score65_74_recovery_probe_last_minute_candle_context_quality": "fresh_bar_window",
            "score65_74_recovery_probe_last_minute_candle_window_fresh": True,
            "score65_74_recovery_probe_last_minute_candle_latest_age_ms": 8000,
            "score65_74_recovery_probe_last_tick_aggressor_trusted_count": 6,
            "score65_74_recovery_probe_last_tick_aggressor_pressure_usable": True,
        },
        "011070",
        {"curr": 1050000},
        now_ts=1_000.0,
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == (
        "same_symbol_cooldown_active:entry_cancel_confirmed"
    )


def test_score65_74_recovery_probe_default_floor_includes_low_60s(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65.0,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=1.2,
        AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert (
        _should_run_score65_74_recovery_probe(
            {"action": "WAIT"},
            62,
            {"latency_state": "OK"},
            [],
            [],
            None,
            feature_probe=_trusted_pressure(
                {
                    "buy_pressure": 72.0,
                    "tick_accel": 1.35,
                    "micro_vwap_bp": 12.0,
                    "large_sell_print": False,
                }
            ),
        )
        is True
    )


def test_score65_74_recovery_probe_entry_unlock_requires_armed_source(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert (
        _is_score65_74_recovery_probe_entry_unlocked(
            {
                "wait6579_probe_canary_armed": True,
                "wait6579_probe_canary_source": "score65_74_recovery_probe",
                "wait6579_probe_canary_score": "68.0",
            }
        )
        is True
    )
    assert _is_score65_74_recovery_probe_entry_unlocked({}) is False


def test_wait6579_probe_entry_unlock_allows_only_enabled_sources(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    score65 = _resolve_wait6579_probe_entry_unlock(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "score65_74_recovery_probe",
            "wait6579_probe_canary_score": "68.0",
        }
    )
    assert score65["unlocked"] is True
    assert score65["event_stage"] == "score65_74_recovery_probe_entry_unlocked"

    assert (
        _resolve_wait6579_probe_entry_unlock(
            {
                "wait6579_probe_canary_armed": True,
                "wait6579_probe_canary_source": "unknown_probe",
            }
        )["unlocked"]
        is False
    )


def test_score65_74_recovery_probe_blocks_preflight_and_neutral_results(
    monkeypatch,
):
    rules = replace(TRADING_RULES, AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    feature_probe = _trusted_pressure(
        {
            "buy_pressure": 90.0,
            "tick_accel": 2.0,
            "micro_vwap_bp": 20.0,
            "large_sell_print": False,
        }
    )

    preflight = _score65_74_recovery_probe_decision(
        {
            "action": "DROP",
            "score": 0,
            "reason": "ai_input_preflight_blocked",
            "decision_evaluation_status": "not_evaluated_provider_or_preflight",
            "ai_result_source": "input_preflight_blocked",
        },
        0,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
    )
    assert preflight["allowed"] is False
    assert preflight["evaluated"] is False
    assert (
        preflight["score65_74_recovery_probe_skip_reason"]
        == "ai_decision_not_evaluated"
    )

    neutral = _score65_74_recovery_probe_decision(
        {"action": "WAIT", "score": 50},
        50,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
    )
    assert neutral["allowed"] is False
    assert neutral["evaluated"] is False
    assert (
        neutral["score65_74_recovery_probe_skip_reason"]
        == "neutral_or_fail_closed_score"
    )


def test_score65_74_recovery_probe_unlock_rejects_missing_or_neutral_score(
    monkeypatch,
):
    rules = replace(TRADING_RULES, AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    base = {
        "wait6579_probe_canary_armed": True,
        "wait6579_probe_canary_source": "score65_74_recovery_probe",
    }

    assert _resolve_wait6579_probe_entry_unlock(base)["unlocked"] is False
    assert (
        _resolve_wait6579_probe_entry_unlock(
            {**base, "wait6579_probe_canary_score": "50.0"}
        )["unlocked"]
        is False
    )
    assert (
        _resolve_wait6579_probe_entry_unlock(
            {**base, "wait6579_probe_canary_score": "68.0"}
        )["unlocked"]
        is True
    )


def test_ai_score_50_buy_hold_override_blocks_neutral_and_fallback(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert (
        _should_apply_ai_score_50_buy_hold_override(50, {"ai_fallback_score_50": False})
        is True
    )
    assert (
        _should_apply_ai_score_50_buy_hold_override(72, {"ai_fallback_score_50": True})
        is True
    )
    assert (
        _should_apply_ai_score_50_buy_hold_override(72, {"ai_fallback_score_50": False})
        is False
    )


def test_ai_score_50_buy_hold_override_can_be_disabled(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=False)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert (
        _should_apply_ai_score_50_buy_hold_override(50, {"ai_fallback_score_50": True})
        is False
    )


def test_ai_score_50_buy_hold_override_merges_duplicate_contract_fields(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)
    captured = {}

    def fake_log(stock, code, stage, **fields):
        captured.update(fields)
        captured["code"] = code
        captured["stage"] = stage

    monkeypatch.setattr(handlers, "_log_entry_pipeline", fake_log)
    cooldowns = {}

    blocked = handlers._block_ai_score_50_buy_hold_override_if_needed(
        stock={"id": 1, "name": "test"},
        code="005930",
        current_ai_score=50,
        ai_decision={
            "ai_result_source": "live",
            "metric_role": "untrusted_ai_payload_role",
            "decision_authority": "untrusted_ai_payload_authority",
            "source_quality_gate": "untrusted_ai_payload_gate",
        },
        config={"AI_WAIT_DROP_COOLDOWN": 30, "BUY_SCORE_THRESHOLD": 75},
        cooldowns=cooldowns,
        now_ts=123.0,
    )

    assert blocked is True
    assert cooldowns["005930"] == 153.0
    assert captured["stage"] == "blocked_ai_score"
    assert captured["metric_role"] == "entry_score_prior_provenance"
    assert captured["decision_authority"] == (
        "entry_score_prior_block_observation_only"
    )
    assert captured["source_quality_gate"] == (
        "blocked_ai_score_entry_score_prior_contract"
    )
    assert captured["actual_order_submitted"] is False
    assert captured["broker_order_forbidden"] is True


def test_watching_buy_analysis_telegram_suppresses_sim_and_probe_context():
    assert _should_publish_watching_buy_analysis_telegram(
        {"scalp_live_simulator": True},
        "SCALPING",
        90,
        buy_score_threshold=75,
    ) == (False, "simulation_context")

    assert _should_publish_watching_buy_analysis_telegram(
        {"scalp_sim_candidate_window_expansion": True},
        "SCALPING",
        90,
        buy_score_threshold=75,
    ) == (False, "scalp_sim_candidate_window_expansion")

    assert _should_publish_watching_buy_analysis_telegram(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "score65_74_recovery_probe",
        },
        "SCALPING",
        66,
        buy_score_threshold=75,
    ) == (False, "score65_74_recovery_probe")


def test_watching_buy_analysis_telegram_requires_scalp_score_cutoff():
    assert _should_publish_watching_buy_analysis_telegram(
        {},
        "SCALPING",
        74,
        buy_score_threshold=75,
    ) == (False, "pre_submit_buy_telegram_disabled_until_order_submitted")
    assert _should_publish_watching_buy_analysis_telegram(
        {},
        "SCALPING",
        75,
        buy_score_threshold=75,
    ) == (False, "pre_submit_buy_telegram_disabled_until_order_submitted")


def test_apply_wait6579_probe_canary_caps_qty_and_budget():
    orders = [
        {"tag": "normal", "qty": 12, "price": 10100, "order_type": "00", "tif": "IOC"},
    ]

    adjusted, original, scaled, applied = _apply_wait6579_probe_canary(
        orders,
        curr_price=10100,
        max_budget_krw=50_000,
        min_qty=1,
        max_qty=1,
    )

    assert original == 12
    assert scaled == 1
    assert applied is True
    assert adjusted[0]["qty"] == 1


def test_apply_wait6579_probe_canary_allows_unlimited_qty_cap():
    orders = [
        {"tag": "normal", "qty": 12, "price": 10100, "order_type": "00", "tif": "IOC"},
    ]

    adjusted, original, scaled, applied = _apply_wait6579_probe_canary(
        orders,
        curr_price=10100,
        max_budget_krw=50_000,
        min_qty=1,
        max_qty=0,
    )

    assert original == 12
    assert scaled == 4
    assert applied is True
    assert adjusted[0]["qty"] == 4


def test_soft_stop_whipsaw_confirmation_respects_emergency_and_one_time_cap(
    monkeypatch,
):
    rules = replace(
        TRADING_RULES,
        SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=True,
        SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=60,
        SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT=0.20,
        SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT=0.30,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    decision = _build_soft_stop_whipsaw_confirmation_decision(
        {},
        now_ts=1000.0,
        profit_rate=-1.55,
        dynamic_stop_pct=-1.50,
        emergency_pct=-2.0,
        grace_elapsed_sec=20,
        grace_sec=20,
        curr_price=9850,
        buy_price=10000,
    )
    assert decision["should_confirm"] is True
    assert decision["rebound_above_sell"] is True
    assert decision["rebound_above_buy"] is False
    assert decision["threshold_family"] == "soft_stop_whipsaw_confirmation"
    assert "confirm_sec=60" in decision["threshold_applied_value"]

    emergency = _build_soft_stop_whipsaw_confirmation_decision(
        {},
        now_ts=1000.0,
        profit_rate=-2.10,
        dynamic_stop_pct=-1.50,
        emergency_pct=-2.0,
        grace_elapsed_sec=20,
        grace_sec=20,
        curr_price=9790,
        buy_price=10000,
    )
    assert emergency["should_confirm"] is False

    used = _build_soft_stop_whipsaw_confirmation_decision(
        {"soft_stop_whipsaw_confirmation_used": True},
        now_ts=1000.0,
        profit_rate=-1.55,
        dynamic_stop_pct=-1.50,
        emergency_pct=-2.0,
        grace_elapsed_sec=20,
        grace_sec=20,
        curr_price=9850,
        buy_price=10000,
    )
    assert used["should_confirm"] is False


def test_apply_initial_entry_qty_cap_limits_total_qty_without_reordering():
    orders = [
        {"tag": "normal", "qty": 2, "price": 10100, "order_type": "00", "tif": "DAY"},
        {"tag": "normal", "qty": 3, "price": 10110, "order_type": "00", "tif": "DAY"},
    ]

    adjusted, original, scaled, applied = _apply_initial_entry_qty_cap(
        orders,
        max_total_qty=1,
    )

    assert original == 5
    assert scaled == 1
    assert applied is True
    assert adjusted[0]["qty"] == 1
    assert adjusted[1]["qty"] == 0


def test_entry_ai_price_input_audit_fields_flattens_provider_compare_contract(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: {
            "entry_liquidity_score": 72,
            "fillability_score": 68,
            "order_flow_pressure_score": 61,
            "entry_context_quality": "partial",
            "entry_context_missing_features": "signed_tape",
            "quote_age_ms": 120,
            "quote_stale": False,
        },
    )
    monkeypatch.setattr(
        handlers,
        "build_scalping_feature_audit_fields",
        lambda packet: {"quote_age_ms": packet["quote_age_ms"]},
    )

    fields = handlers._entry_ai_price_input_audit_fields(
        result={"ai_input_schema": "entry_price_compact_v1"},
        price_ctx={
            "current_price": 10020,
            "resolved_order_price": 10000,
            "best_bid": 10010,
            "best_ask": 10030,
            "quote_stale": False,
        },
        ws_data={"curr": 10020},
        recent_ticks=[],
        recent_candles=[],
    )

    assert fields["entry_price_input_schema"] == "entry_price_compact_v1"
    assert fields["entry_price_input_resolved_order_price"] == 10000
    assert fields["entry_price_input_best_bid"] == 10010
    assert fields["entry_price_input_best_ask"] == 10030
    assert fields["entry_liquidity_score"] == 72
    assert fields["quote_age_ms"] == 120
    assert fields["quote_stale"] is False
    assert fields["ai_input_source_quality_status"] == "partial"
    assert fields["entry_price_input_decision_authority"] == (
        "provider_call_fail_closed_only"
    )


def test_entry_ai_price_input_audit_uses_frozen_feature_packet(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("frozen packet must not be rebuilt after provider latency")
        ),
    )

    fields = handlers._entry_ai_price_input_audit_fields(
        result={"ai_input_schema": "entry_price_compact_v1"},
        price_ctx={
            "current_price": 10020,
            "resolved_order_price": 10000,
            "best_bid": 10010,
            "best_ask": 10030,
        },
        ws_data={"curr": 10020},
        recent_ticks=[],
        recent_candles=[],
        feature_packet={
            "entry_context_quality": "complete",
            "entry_context_missing_features": "",
            "quote_age_ms": 2800,
            "quote_stale": False,
        },
    )

    assert fields["ai_input_source_quality_status"] == "complete"
    assert fields["quote_age_ms"] == 2800
    assert fields["quote_stale"] is False
