from dataclasses import replace

from src.engine import sniper_state_handlers as handlers
from src.engine.sniper_state_handlers import (
    SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY,
    _apply_initial_entry_qty_cap,
    _apply_wait6579_probe_canary,
    _build_soft_stop_whipsaw_confirmation_decision,
    _build_ai_overlap_log_fields,
    _build_ai_ops_log_fields,
    _build_observation_contract_fields,
    _score65_74_recovery_probe_block_contract_fields,
    _ensure_ai_source_quality_fields,
    _build_gatekeeper_fast_signature,
    _build_holding_ai_fast_signature,
    _extract_ai_overlap_snapshot,
    _is_score65_74_recovery_probe_entry_unlocked,
    _score65_74_recovery_probe_decision,
    _score65_74_recovery_probe_reuse_guard,
    _resolve_wait6579_probe_entry_unlock,
    _should_apply_ai_score_50_buy_hold_override,
    _should_publish_watching_buy_analysis_telegram,
    _should_run_score65_74_recovery_probe,
    _should_run_main_buy_recovery_canary,
    _resolve_early_accel_recheck,
    _resolve_gatekeeper_fast_reuse_sec,
    _resolve_holding_ai_fast_reuse_sec,
    _resolve_watching_state_change_refresh,
)
from src.utils.constants import TRADING_RULES


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
    ws_b.update({
        "volume": 1858999,
        "v_pw": 118.8,
        "buy_ratio": 63.1,
        "prog_net_qty": 18999,
        "ask_tot": 188999,
    })

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
    ws_data = {
        "curr": 12430,
        "tick_acceleration_ratio": 1.25,
        "curr_vs_micro_vwap_bp": 12.0,
        "quote_stale": False,
    }

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


def test_early_accel_recheck_blocks_stale_or_falling_context(monkeypatch):
    rules = replace(TRADING_RULES, EARLY_ACCEL_RECHECK_RUNTIME_ENABLED=True)
    monkeypatch.setattr(handlers, "TRADING_RULES", rules)
    stock = {"position_tag": "SCANNER", "buy_price": 12280, "entry_armed_at_epoch": 100.0}
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
        {"curr": 12350, "tick_acceleration_ratio": 1.5, "curr_vs_micro_vwap_bp": 10.0, "quote_stale": True},
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


def test_scalping_entry_blocker_role_registry_marks_score6574_micro_as_runtime_gate():
    assert SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["blocked_gap_from_scan"]["role"] == "baseline_prior_feature"
    assert SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["blocked_gap_from_scan"]["hard_block_allowed"] is False
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["score65_74_recovery_probe_micro_context"]["gate_action"]
        == "runtime_min_micro_gate"
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["score65_74_recovery_probe_micro_context"]["hard_block_allowed"]
        is True
    )
    assert (
        SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["main_buy_recovery_canary_micro_context"]["hard_block_allowed"]
        is False
    )
    assert SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["latency_danger"]["hard_block_allowed"] is True
    assert SCALPING_ENTRY_BLOCKER_ROLE_REGISTRY["stale_quote_or_context"]["hard_block_allowed"] is True


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
    ws_b.update({
        "curr": 12610,
        "volume": 1949999,
        "v_pw": 119.4,
        "buy_ratio": 67.9,
        "prog_net_qty": 20510,
        "prog_delta_qty": 4880,
        "ask_tot": 199999,
        "bid_tot": 241000,
    })
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
    ws_b.update({
        "curr": 766,
        "prog_net_qty": -10,
        "prog_delta_qty": -1,
    })
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
    ws_b.update({
        "prog_net_qty": 30000,
        "prog_delta_qty": 6000,
    })

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
    ws_b.update({
        "curr": 10120,
        "buy_ratio": 74.0,
        "ask_tot": 150000,
        "bid_tot": 80000,
    })
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
            "openai_request_id": "analyze_target:005930:1:abcd",
            "openai_endpoint_name": "analyze_target",
            "openai_schema_name": "entry_v1",
            "openai_ws_used": True,
            "openai_ws_http_fallback": False,
            "openai_ws_queue_wait_ms": 7,
            "openai_ws_roundtrip_ms": 234,
            "openai_input_tokens": 1234,
            "openai_output_tokens": 56,
            "openai_total_tokens": 1290,
            "openai_cached_input_tokens": 120,
            "openai_reasoning_tokens": 8,
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
    assert fields["openai_request_id"] == "analyze_target:005930:1:abcd"
    assert fields["openai_endpoint_name"] == "analyze_target"
    assert fields["openai_schema_name"] == "entry_v1"
    assert fields["openai_ws_used"] is True
    assert fields["openai_ws_http_fallback"] is False
    assert fields["openai_ws_queue_wait_ms"] == 7
    assert fields["openai_ws_roundtrip_ms"] == 234
    assert fields["openai_input_tokens"] == 1234
    assert fields["openai_output_tokens"] == 56
    assert fields["openai_total_tokens"] == 1290
    assert fields["openai_cached_input_tokens"] == 120
    assert fields["openai_reasoning_tokens"] == 8
    assert fields["ai_score_raw"] == "74.0"
    assert fields["ai_score_after_bonus"] == "79.0"
    assert fields["entry_score_threshold"] == "75.0"
    assert fields["big_bite_bonus_applied"] is True
    assert fields["ai_cooldown_blocked"] is False


def test_ai_source_quality_fields_marks_not_evaluated_without_snapshot():
    fields = _ensure_ai_source_quality_fields({}, {}, not_evaluated_reason="watching_ai_cooldown_active")

    assert fields["ai_input_source_quality_status"] == "not_evaluated"
    assert fields["ai_input_source_quality_reason"] == "watching_ai_cooldown_active"
    assert fields["tick_source_quality_fields_sent"] is False
    assert fields["tick_accel_source"] == "not_evaluated"
    assert fields["tick_context_quality"] == "not_evaluated"
    assert fields["quote_age_source"] == "not_evaluated"


def test_ai_source_quality_fields_inherits_previous_snapshot():
    stock = {
        "last_watching_ai_source_quality_fields": {
            "tick_source_quality_fields_sent": True,
            "tick_accel_source": "computed_10ticks",
            "tick_context_quality": "fresh_computed",
            "quote_age_source": "missing",
        }
    }

    fields = _ensure_ai_source_quality_fields({}, stock, not_evaluated_reason="wait65_79_ev_candidate_no_tick_audit")

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


def test_should_run_main_buy_recovery_canary_with_feature_allowlist(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=True,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE=65,
        AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE=79,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE=65.0,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL=1.2,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    class _Engine:
        @staticmethod
        def _extract_scalping_features(ws_data, recent_ticks, recent_candles):
            return {
                "buy_pressure_10t": 70.0,
                "tick_acceleration_ratio": 1.35,
                "curr_vs_micro_vwap_bp": 3.0,
                "large_sell_print_detected": False,
            }

    assert _should_run_main_buy_recovery_canary({"action": "WAIT"}, 72, {}, [], [], _Engine()) is True


def test_should_run_main_buy_recovery_canary_keeps_micro_context_feature_only(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=True,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE=65,
        AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE=79,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE=65.0,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL=1.2,
        AI_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP=0.0,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    class _BadEngine:
        @staticmethod
        def _extract_scalping_features(ws_data, recent_ticks, recent_candles):
            return {
                "buy_pressure_10t": 70.0,
                "tick_acceleration_ratio": 1.35,
                "curr_vs_micro_vwap_bp": 3.0,
                "large_sell_print_detected": True,
            }

    assert _should_run_main_buy_recovery_canary({"action": "WAIT"}, 72, {}, [], [], _BadEngine()) is True
    assert (
        _should_run_main_buy_recovery_canary(
            {"action": "WAIT"},
            72,
            {"latency_state": "DANGER"},
            [],
            [],
            _BadEngine(),
        )
        is False
    )


def test_should_run_score65_74_recovery_probe_uses_dedicated_default_off_flag(monkeypatch):
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

    feature_probe = {
        "buy_pressure": 70.0,
        "tick_accel": 1.35,
        "micro_vwap_bp": 12.0,
        "large_sell_print": False,
    }

    assert _should_run_score65_74_recovery_probe(
        {"action": "WAIT"},
        72,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
    ) is True
    assert _should_run_score65_74_recovery_probe(
        {"action": "WAIT"},
        75,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=feature_probe,
    ) is False


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
    weak_micro_feature_probe = {
        "buy_pressure": 10.0,
        "tick_accel": 0.1,
        "micro_vwap_bp": -25.0,
        "large_sell_print": True,
    }

    assert _should_run_score65_74_recovery_probe(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe=weak_micro_feature_probe,
    ) is False
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
    assert _should_run_score65_74_recovery_probe(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe={**weak_micro_feature_probe, "quote_stale": True},
    ) is False
    assert _should_run_score65_74_recovery_probe(
        {"action": "WAIT"},
        72,
        {"latency_state": "DANGER"},
        [],
        [],
        None,
        feature_probe=weak_micro_feature_probe,
    ) is False


def test_score65_74_recovery_probe_strong_micro_override_relaxes_tick_only_veto(monkeypatch):
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
        feature_probe={
            "buy_pressure": 91.0,
            "tick_accel": 0.0,
            "micro_vwap_bp": 45.0,
            "tick_accel_source": "computed_10ticks",
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "quote_stale": False,
        },
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
        feature_probe={
            "buy_pressure": 87.0,
            "tick_accel": 1.25,
            "micro_vwap_bp": 4.11,
        },
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "micro_vwap_below_min"
    assert decision["score65_74_recovery_probe_min_micro_vwap_bp"] == 10.0
    assert decision["score65_74_recovery_probe_configured_min_micro_vwap_bp"] == 0.0


def test_score65_74_recovery_probe_blocks_negative_wait_reason_even_when_micro_passes(monkeypatch):
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
        feature_probe={
            "buy_pressure": 91.0,
            "tick_accel": 1.6,
            "micro_vwap_bp": 45.0,
        },
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == (
        "ai_wait_negative_reason_veto:mixed_signal"
    )


def test_score65_74_recovery_probe_does_not_veto_positive_reason_with_negative_absent(monkeypatch):
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
        feature_probe={
            "buy_pressure": 91.0,
            "tick_accel": 1.6,
            "micro_vwap_bp": 45.0,
        },
    )

    assert decision["allowed"] is True
    assert decision["score65_74_recovery_probe_skip_reason"] == ""


def test_score65_74_recovery_probe_strong_micro_override_does_not_relax_weak_micro(monkeypatch):
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
        feature_probe={
            "buy_pressure": 91.0,
            "tick_accel": 0.0,
            "micro_vwap_bp": 12.0,
            "tick_accel_source": "computed_10ticks",
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "quote_stale": False,
        },
    )

    assert decision["allowed"] is False
    assert decision["score65_74_recovery_probe_strong_micro_override_applied"] is False
    assert decision["score65_74_recovery_probe_skip_reason"] == "tick_accel_below_min"


def test_score65_74_recovery_probe_strong_micro_override_skips_when_entry_tuning_live(monkeypatch):
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
        feature_probe={
            "buy_pressure": 91.0,
            "tick_accel": 0.0,
            "micro_vwap_bp": 45.0,
            "tick_accel_source": "computed_10ticks",
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "quote_stale": False,
        },
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
        feature_probe={
            "buy_pressure": 50.0,
            "tick_accel": 1.0,
            "micro_vwap_bp": -8.34,
            "large_sell_print": False,
        },
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
        feature_probe={
            "buy_pressure": 80.0,
            "tick_accel": 1.5,
            "micro_vwap_bp": 3.0,
            "large_sell_print": False,
        },
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
    assert fields["decision_authority"] == "score65_74_recovery_probe_block_observation_only"
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True


def test_score65_74_recovery_probe_reuse_guard_blocks_stale_armed_cancel_cooldown(monkeypatch):
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

    assert _should_run_score65_74_recovery_probe(
        {"action": "WAIT"},
        62,
        {"latency_state": "OK"},
        [],
        [],
        None,
        feature_probe={
            "buy_pressure": 72.0,
            "tick_accel": 1.35,
            "micro_vwap_bp": 12.0,
            "large_sell_print": False,
        },
    ) is True


def test_score65_74_recovery_probe_entry_unlock_requires_armed_source(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert _is_score65_74_recovery_probe_entry_unlocked(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "score65_74_recovery_probe",
        }
    ) is True
    assert _is_score65_74_recovery_probe_entry_unlocked(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "buy_recovery_canary_promoted",
        }
    ) is False
    assert _is_score65_74_recovery_probe_entry_unlocked({}) is False


def test_wait6579_probe_entry_unlock_allows_only_enabled_sources(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=True,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    score65 = _resolve_wait6579_probe_entry_unlock(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "score65_74_recovery_probe",
        }
    )
    assert score65["unlocked"] is True
    assert score65["event_stage"] == "score65_74_recovery_probe_entry_unlocked"

    promoted = _resolve_wait6579_probe_entry_unlock(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "buy_recovery_canary_promoted",
        }
    )
    assert promoted["unlocked"] is True
    assert promoted["event_stage"] == "buy_recovery_canary_entry_unlocked"

    assert _resolve_wait6579_probe_entry_unlock(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "unknown_probe",
        }
    )["unlocked"] is False


def test_wait6579_probe_entry_unlock_blocks_disabled_future_canary(monkeypatch):
    rules = replace(
        TRADING_RULES,
        AI_SCORE65_74_RECOVERY_PROBE_ENABLED=True,
        AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=False,
    )
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    promoted = _resolve_wait6579_probe_entry_unlock(
        {
            "wait6579_probe_canary_armed": True,
            "wait6579_probe_canary_source": "buy_recovery_canary_promoted",
        }
    )

    assert promoted["unlocked"] is False
    assert promoted["event_stage"] == "buy_recovery_canary_entry_unlocked"


def test_ai_score_50_buy_hold_override_blocks_neutral_and_fallback(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert _should_apply_ai_score_50_buy_hold_override(50, {"ai_fallback_score_50": False}) is True
    assert _should_apply_ai_score_50_buy_hold_override(72, {"ai_fallback_score_50": True}) is True
    assert _should_apply_ai_score_50_buy_hold_override(72, {"ai_fallback_score_50": False}) is False


def test_ai_score_50_buy_hold_override_can_be_disabled(monkeypatch):
    rules = replace(TRADING_RULES, AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=False)
    monkeypatch.setattr("src.engine.sniper_state_handlers.TRADING_RULES", rules)

    assert _should_apply_ai_score_50_buy_hold_override(50, {"ai_fallback_score_50": True}) is False


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


def test_soft_stop_whipsaw_confirmation_respects_emergency_and_one_time_cap(monkeypatch):
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
