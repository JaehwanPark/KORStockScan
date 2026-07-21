import json
import time
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import src.engine.sniper_entry_latency as entry_latency_module
import src.engine.sniper_state_handlers as state_handlers
from src.engine.sniper_entry_latency import (
    _best_ask_bid_from_ws,
    _latency_danger_reasons,
    clear_signal_reference,
    evaluate_live_buy_entry,
    freeze_signal_reference,
)
from src.utils.constants import TRADING_RULES as CONFIG


def _assert_danger_hard_safety_block(result, *, danger_reasons=None):
    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "danger_hard_safety_block"
    assert result["allowed"] is False
    assert result["decision"] == "REJECT_DANGER"
    if danger_reasons is not None:
        if isinstance(danger_reasons, str):
            assert result["latency_danger_reasons"] == danger_reasons
        else:
            for reason in danger_reasons:
                assert reason in result["latency_danger_reasons"]


def test_scanner_promotion_correlation_fields_preserve_forced_rising_missed_lineage():
    fields = state_handlers._scanner_promotion_correlation_fields(
        {
            "scanner_promotion_id": "promo-1",
            "scanner_promotion_reason": "low_rebound_rising_missed_candidate",
            "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            "rising_missed_one_share_entry_forced": True,
            "forced_entry_reason": "rising_missed_one_share_entry",
            "forced_entry_qty": "1",
            "rising_missed_one_share_scout": True,
        }
    )

    assert fields["rising_missed_entry_lineage"] is True
    assert fields["rising_missed_one_share_entry_forced"] is True
    assert fields["forced_entry_reason"] == "rising_missed_one_share_entry"
    assert fields["forced_entry_qty"] == "1"
    assert fields["rising_missed_one_share_scout"] is True


def test_latency_entry_normal_mode_uses_defensive_limit_price():
    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_normal",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_normal",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=10_000,
    )

    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["order_price"] == 9_990
    assert result["entry_price_guard"] == "normal_defensive"
    assert result["entry_price_defensive_ticks"] == 1
    assert result["counterfactual_order_price_1tick"] == 9_990
    assert result["orderbook_stability"]["best_bid"] == 10_000
    assert result["orderbook_stability"]["best_ask"] == 10_010


def test_latency_entry_config_uses_runtime_classifier_overrides(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_NORMAL_DEFENSIVE_TICKS=3,
            SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION=1200,
            SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION=1500,
            SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION=0.01,
        ),
    )

    config = entry_latency_module._build_entry_config()

    assert config.normal_defensive_ticks == 3
    assert config.max_ws_age_ms_for_caution == 1200
    assert config.max_ws_jitter_ms_for_caution == 1500
    assert config.max_spread_ratio_for_caution == 0.01


def test_scanner_promotion_context_hydrates_missing_recheck_anchor(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_load_scanner_promotion_context_events",
        lambda target_date: {
            "123456": [
                {
                    "emitted_epoch": 1_781_830_800.0,
                    "fields": {
                        "scanner_promotion_reason": "price_jump_start_acceleration",
                        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                        "price_delta_since_first_seen_pct": "1.25",
                        "comparable_flu_delta_since_first_seen": "1.10",
                        "cntr_str_available": True,
                        "cntr_str": "123.4",
                        "current_price_observed": "23500",
                    },
                }
            ]
        },
    )
    stock = {
        "code": "123456",
        "date": "2026-06-19",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "1.25",
        "comparable_flu_delta_since_first_seen": "1.10",
        "cntr_str_available": True,
        "cntr_str": "123.4",
    }

    hydrated = state_handlers._hydrate_scanner_promotion_runtime_context(stock)

    assert hydrated["buy_price"] == 23_500
    assert hydrated["entry_armed_at_epoch"] == 1_781_830_800.0
    assert stock["buy_price"] == 23_500
    assert stock["entry_armed_at_epoch"] == 1_781_830_800.0


def test_early_accel_strong_bundle_pre_recheck_fields_are_contract_values(monkeypatch):
    monkeypatch.setattr(state_handlers, "_rule_bool", lambda key, default=False: False)
    decision = state_handlers._resolve_early_accel_strong_bundle_recheck(
        {
            "position_tag": "SCANNER",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        },
        {},
        strategy="SCALPING",
        ai_decision={"action": "WAIT"},
        ai_score=62,
    )

    assert decision["allowed"] is False
    assert decision["skip_reason"] == "disabled"
    assert decision["recheck_action"] == "not_evaluated"
    assert decision["recheck_score"] == "not_evaluated"


def test_early_accel_strong_bundle_recheck_failure_class_is_canonical():
    assert (
        state_handlers._early_accel_strong_bundle_recheck_failure_class("DROP")
        == "drop_action"
    )
    assert (
        state_handlers._early_accel_strong_bundle_recheck_failure_class("WAIT")
        == "wait_below_min_score"
    )
    assert (
        state_handlers._early_accel_strong_bundle_recheck_failure_class("BUY")
        == "buy_score_below_min"
    )
    assert (
        state_handlers._early_accel_strong_bundle_recheck_failure_class("UNKNOWN")
        == "non_buy_action"
    )


def test_ai_numeric_consistency_pre_recheck_fields_are_contract_values(monkeypatch):
    monkeypatch.setattr(state_handlers, "_rule_bool", lambda key, default=False: False)
    decision = state_handlers._resolve_ai_numeric_consistency_recheck(
        {"position_tag": "SCANNER"},
        {},
        now_ts=1_781_830_800.0,
        strategy="SCALPING",
        ai_decision={"action": "WAIT"},
        ai_score=62,
    )

    assert decision["allowed"] is False
    assert decision["skip_reason"] == "disabled"
    assert decision["inconsistency_field"] == "not_applicable"
    assert decision["inconsistency_reason"] == "not_applicable"
    assert decision["detected_value"] == "not_evaluated"
    assert decision["recheck_action"] == "not_evaluated"
    assert decision["recheck_score"] == "not_evaluated"
    assert decision["recheck_reason_excerpt"] == "not_evaluated"


def test_latency_entry_runtime_override_uses_more_conservative_defensive_ticks(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(
        entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config()
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_NORMAL_BUILDER",
        entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_ENTRY_POLICY",
        entry_latency_module.EntryPolicy(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_LATENCY_MONITOR",
        entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG),
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_defensive3",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_defensive3",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=10_000,
    )

    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["order_price"] == 9_970
    assert result["entry_price_guard"] == "normal_defensive"
    assert result["entry_price_defensive_ticks"] == 3
    assert result["counterfactual_order_price_1tick"] == 9_990


def test_latency_entry_conditional_real_1tick_override_for_strong_micro(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(
        entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config()
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_NORMAL_BUILDER",
        entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_ENTRY_POLICY",
        entry_latency_module.EntryPolicy(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_LATENCY_MONITOR",
        entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG),
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_conditional_1tick",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_conditional_1tick",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "buy_exec_volume": 70,
            "sell_exec_volume": 30,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 4,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=10_000,
    )

    assert result["allowed"] is True
    assert result["order_price"] == 9_990
    assert result["entry_price_defensive_ticks"] == 1
    assert result["entry_price_guard"] == "conditional_1tick_real_micro_override"
    assert result["conditional_1tick_real_override_applied"] is True
    assert result["conditional_1tick_real_override_context"]["spread_ticks"] == 1
    assert result["conditional_1tick_real_override_context"]["buy_pressure_ok"] is True
    assert result["normal_defensive_order_price"] == 9_970


def test_latency_entry_conditional_1tick_does_not_apply_to_non_scalping(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(
        entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config()
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_NORMAL_BUILDER",
        entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_ENTRY_POLICY",
        entry_latency_module.EntryPolicy(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_LATENCY_MONITOR",
        entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG),
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_non_scalping_conditional_1tick",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_non_scalping_conditional_1tick",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "buy_exec_volume": 70,
            "sell_exec_volume": 30,
            "net_buy_exec_volume": 40,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SWING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=10_000,
    )

    assert result["allowed"] is True
    assert result["order_price"] == 9_990
    assert result["entry_price_defensive_ticks"] == 1
    assert result["conditional_1tick_real_override_applied"] is False
    assert (
        result["conditional_1tick_real_override_reason"] == "disabled_or_non_scalping"
    )


def test_latency_entry_three_tick_override_is_limited_to_scalping(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(
        entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config()
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_NORMAL_BUILDER",
        entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_ENTRY_POLICY",
        entry_latency_module.EntryPolicy(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_LATENCY_MONITOR",
        entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG),
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_s15_fast_not_three_tick",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_s15_fast_not_three_tick",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="S15_FAST",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=0,
    )

    assert result["allowed"] is True
    assert result["order_price"] == 9_990
    assert result["entry_price_defensive_ticks"] == 1
    assert result["entry_price_guard"] == "normal_defensive"
    assert result["conditional_1tick_real_override_applied"] is False


def test_latency_entry_conditional_1tick_requires_complete_depth_context(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(
        entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config()
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_NORMAL_BUILDER",
        entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_ENTRY_POLICY",
        entry_latency_module.EntryPolicy(entry_latency_module._CONFIG),
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_LATENCY_MONITOR",
        entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG),
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_missing_ask_depth",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_missing_ask_depth",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "net_buy_exec_volume": 0,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 0}],
                "bids": [{"price": 10_000, "volume": 500}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=10_000,
    )

    assert result["allowed"] is True
    assert result["order_price"] == 9_970
    assert result["entry_price_defensive_ticks"] == 3
    assert result["conditional_1tick_real_override_applied"] is False
    assert result["conditional_1tick_real_override_context"]["depth_ok"] is False


def test_latency_entry_blocks_stale_quote_as_danger():
    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_stale",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": 0.0,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is False
    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_state"] == "DANGER"
    assert result["latency_danger_reasons"] == "quote_stale,ws_age_too_high"


def test_pre_submit_quote_refresh_uses_fresh_observer_quote_for_stale_ws(monkeypatch):
    runtime_rules = replace(
        CONFIG,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED=True,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS=700,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO=0.015,
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        runtime_rules,
    )
    monkeypatch.setattr(
        entry_latency_module.constants_module, "TRADING_RULES", runtime_rules
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_refresh",
        best_bid=10_020,
        best_ask=10_030,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_refresh",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": time.time() - 3.0,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["pre_submit_quote_refresh_enabled"] is True
    assert result["pre_submit_quote_refresh_applied"] is True
    assert result["pre_submit_quote_refresh_reason"] == "observer_quote_fresh"
    assert result["quote_stale"] is False
    assert result["latest_price"] == 10_020
    assert result["pre_submit_quote_refresh_latest_price"] == 10_020
    assert result["order_price"] == 10_010
    assert result["orderbook_stability"]["best_bid"] == 10_020
    assert result["orderbook_stability"]["best_ask"] == 10_030


def test_pre_submit_quote_refresh_uses_pid_env_when_runtime_rules_are_stale(
    monkeypatch,
):
    stale_rules = replace(
        CONFIG,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED=False,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS=100,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO=0.001,
    )
    monkeypatch.setattr(entry_latency_module, "TRADING_RULES", stale_rules)
    monkeypatch.setattr(
        entry_latency_module.constants_module, "TRADING_RULES", stale_rules
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO", "0.015"
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_refresh_env",
        best_bid=10_020,
        best_ask=10_030,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_refresh_env",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": time.time() - 3.0,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["pre_submit_quote_refresh_enabled"] is True
    assert result["pre_submit_quote_refresh_applied"] is True
    assert result["pre_submit_quote_refresh_reason"] == "observer_quote_fresh"


def test_pre_submit_quote_refresh_treats_kospi_ml_as_real_scalping_alias(monkeypatch):
    stale_rules = replace(
        CONFIG,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED=False,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS=100,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO=0.001,
    )
    monkeypatch.setattr(entry_latency_module, "TRADING_RULES", stale_rules)
    monkeypatch.setattr(
        entry_latency_module.constants_module, "TRADING_RULES", stale_rules
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO", "0.015"
    )

    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "123456_refresh_kospi_ml",
        best_bid=10_020,
        best_ask=10_030,
        ts=time.time(),
    )

    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_refresh_kospi_ml",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": time.time() - 3.0,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="KOSPI_ML",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["pre_submit_quote_refresh_strategy_id"] == "KOSPI_ML"
    assert result["pre_submit_quote_refresh_env_value"] == "true"
    assert result["pre_submit_quote_refresh_enabled"] is True
    assert result["pre_submit_quote_refresh_applied"] is True
    assert result["pre_submit_quote_refresh_reason"] == "observer_quote_fresh"
    assert result["quote_stale"] is False
    assert result["latest_price"] == 10_020
    assert result["pre_submit_quote_refresh_latest_price"] == 10_020


def test_latency_entry_accepts_flat_best_levels_from_ws_snapshot():
    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    ws_data = {
        "curr": 10_000,
        "last_ws_update_ts": time.time(),
        "best_ask": 10_010,
        "best_bid": 10_000,
    }
    assert _best_ask_bid_from_ws(ws_data) == (10_010, 10_000)
    result = evaluate_live_buy_entry(
        stock=stock,
        code="654321",
        ws_data=ws_data,
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["quote_stale"] is False
    assert result["spread_ratio"] > 0


def test_real_pre_submit_ws_snapshot_refresh_uses_fresh_ws_manager_snapshot(
    monkeypatch,
):
    class FakeWsManager:
        def get_latest_data(self, code):
            assert code == "123456"
            return {
                "curr": 10_020,
                "last_ws_update_ts": time.time(),
                "orderbook": {
                    "asks": [{"price": 10_030, "volume": 100}],
                    "bids": [{"price": 10_020, "volume": 100}],
                },
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    stale_input = {
        "curr": 10_000,
        "last_ws_update_ts": time.time() - 3.0,
        "orderbook": {
            "asks": [{"price": 10_010, "volume": 100}],
            "bids": [{"price": 10_000, "volume": 100}],
        },
    }

    refreshed, fields = state_handlers._pre_submit_refresh_real_ws_snapshot(
        "123456",
        stale_input,
        "SCALPING",
    )

    assert fields["pre_submit_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_submit_ws_snapshot_refresh_applied"] is True
    assert fields["pre_submit_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert refreshed["curr"] == 10_020
    assert refreshed["orderbook"]["bids"][0]["price"] == 10_020
    assert refreshed["pre_submit_ws_snapshot_refresh_latest_price"] == 10_020


def test_pre_submit_effective_quote_fields_mark_stale_ai_recovered_by_ws_refresh():
    fields = state_handlers._pre_submit_effective_quote_log_fields(
        latency_gate={
            "quote_stale": False,
            "pre_submit_ws_snapshot_refresh_applied": True,
            "pre_submit_ws_snapshot_refresh_age_ms": 79.165,
        },
        ai_quote_stale=True,
        ai_quote_age_ms=4955,
    )

    assert fields["pre_submit_effective_quote_stale"] is False
    assert fields["pre_submit_effective_quote_age_ms"] == 79.165
    assert (
        fields["pre_submit_effective_quote_age_source"]
        == "pre_submit_ws_snapshot_refresh"
    )
    assert fields["pre_submit_ai_input_quote_stale"] is True
    assert fields["pre_submit_ai_input_quote_age_ms"] == 4955
    assert fields["pre_submit_refresh_recovered_stale_ai_context"] is True


def test_pre_submit_effective_quote_fields_fall_back_to_latency_gate_age():
    fields = state_handlers._pre_submit_effective_quote_log_fields(
        latency_gate={
            "quote_stale": False,
            "ws_age_ms": 310,
        },
        ai_quote_stale=False,
        ai_quote_age_ms=120,
    )

    assert fields["pre_submit_effective_quote_stale"] is False
    assert fields["pre_submit_effective_quote_age_ms"] == 310
    assert fields["pre_submit_effective_quote_age_source"] == "latency_gate_ws_age"
    assert fields["pre_submit_refresh_recovered_stale_ai_context"] is False


def test_real_pre_submit_ws_snapshot_refresh_keeps_valid_input_when_timestamp_missing(
    monkeypatch,
):
    class FakeWsManager:
        def get_latest_data(self, code):
            raise AssertionError(
                "WS manager should not be consulted for a valid input snapshot"
            )

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    valid_input = {
        "curr": 10_000,
        "orderbook": {
            "asks": [{"price": 10_010, "volume": 100}],
            "bids": [{"price": 10_000, "volume": 100}],
        },
    }

    refreshed, fields = state_handlers._pre_submit_refresh_real_ws_snapshot(
        "123456",
        valid_input,
        "SCALPING",
    )

    assert refreshed == valid_input
    assert fields["pre_submit_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_submit_ws_snapshot_refresh_applied"] is False
    assert (
        fields["pre_submit_ws_snapshot_refresh_reason"]
        == "input_snapshot_timestamp_missing"
    )


def test_pre_ai_strength_ws_snapshot_refresh_uses_fresh_ws_manager_history(monkeypatch):
    now = time.time()

    class FakeWsManager:
        def get_latest_data(self, code):
            assert code == "123456"
            return {
                "curr": 10_020,
                "v_pw": 121.0,
                "last_ws_update_ts": time.time(),
                "strength_momentum_history": [
                    {"ts": now - 8.0, "v_pw": 100.0, "tick_value": 1000},
                    {"ts": now, "v_pw": 121.0, "tick_value": 2000},
                ],
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    refreshed, fields = state_handlers._pre_ai_refresh_strength_momentum_ws_snapshot(
        "123456",
        {
            "curr": 10_000,
            "v_pw": 99.0,
            "last_ws_update_ts": time.time() - 5.0,
            "strength_momentum_history": [],
        },
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_ai_ws_snapshot_refresh_applied"] is True
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert fields["pre_ai_ws_snapshot_refresh_history_count"] == 2
    assert refreshed["curr"] == 10_020
    assert refreshed["v_pw"] == 121.0


def test_pre_ai_strength_ws_snapshot_refresh_normalizes_latest_tick_timestamp(
    monkeypatch,
):
    now = time.time()

    class FakeWsManager:
        def get_latest_data(self, code):
            assert code == "123456"
            return {
                "curr": 10_020,
                "v_pw": 121.0,
                "last_ws_update_ts": now - 8.0,
                "last_realtime_type_ts": {"0B": now - 0.2},
                "strength_momentum_history": [
                    {"ts": now - 8.0, "v_pw": 100.0, "tick_value": 1000},
                    {"ts": now - 0.2, "v_pw": 121.0, "tick_value": 2000},
                ],
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )

    refreshed, fields = state_handlers._pre_ai_refresh_strength_momentum_ws_snapshot(
        "123456",
        {
            "curr": 10_000,
            "v_pw": 99.0,
            "last_ws_update_ts": now - 10.0,
            "strength_momentum_history": [],
        },
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_applied"] is True
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert (
        fields["pre_ai_ws_snapshot_refresh_latest_timestamp_normalized_from"]
        == "last_realtime_type_ts_0B"
    )
    assert fields["pre_ai_ws_snapshot_refresh_age_ms"] < 1000
    assert (
        refreshed["pre_ai_last_ws_update_ts_normalized_from"]
        == "last_realtime_type_ts_0B"
    )


def test_pre_ai_strength_ws_snapshot_refresh_keeps_fresh_input_history_count(
    monkeypatch,
):
    now = time.time()
    monkeypatch.setattr(state_handlers, "WS_MANAGER", None)
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    original = {
        "curr": 10_000,
        "v_pw": 119.0,
        "last_ws_update_ts": now - 0.2,
        "strength_momentum_history": [
            {"ts": now - 0.4, "v_pw": 117.0},
            {"ts": now - 0.2, "v_pw": 119.0},
        ],
    }

    refreshed, fields = state_handlers._pre_ai_refresh_strength_momentum_ws_snapshot(
        "123456",
        original,
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_ai_ws_snapshot_refresh_applied"] is False
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "input_snapshot_fresh"
    assert fields["pre_ai_ws_snapshot_refresh_history_count"] == 2
    assert refreshed == original


def test_pre_ai_strength_ws_snapshot_refresh_rechecks_near_stale_input(monkeypatch):
    class FakeWsManager:
        def get_latest_data(self, code):
            return {
                "curr": 10_030,
                "v_pw": 122.0,
                "last_ws_update_ts": time.time(),
                "strength_momentum_history": [{"ts": time.time(), "v_pw": 122.0}],
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    refreshed, fields = state_handlers._pre_ai_refresh_strength_momentum_ws_snapshot(
        "123456",
        {
            "curr": 10_000,
            "v_pw": 99.0,
            "last_ws_update_ts": time.time() - 2.8,
            "strength_momentum_history": [{"ts": time.time() - 2.8, "v_pw": 99.0}],
        },
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_applied"] is True
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert fields["pre_ai_ws_snapshot_refresh_input_age_ms"] >= 2500
    assert refreshed["curr"] == 10_030


def test_pre_ai_strength_ws_snapshot_refresh_keeps_stale_latest_blocked(monkeypatch):
    class FakeWsManager:
        def get_latest_data(self, code):
            return {
                "curr": 10_020,
                "v_pw": 121.0,
                "last_ws_update_ts": time.time() - 10.0,
                "strength_momentum_history": [
                    {"ts": time.time() - 10.0, "v_pw": 121.0}
                ],
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    original = {
        "curr": 10_000,
        "v_pw": 99.0,
        "last_ws_update_ts": time.time() - 15.0,
    }
    refreshed, fields = state_handlers._pre_ai_refresh_strength_momentum_ws_snapshot(
        "123456",
        original,
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_ai_ws_snapshot_refresh_applied"] is False
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "latest_snapshot_stale"
    assert refreshed["curr"] == original["curr"]


def test_pre_ai_quote_ws_snapshot_refresh_uses_fresh_quote_without_strength_history(
    monkeypatch,
):
    class FakeWsManager:
        def get_latest_data(self, code):
            assert code == "123456"
            return {
                "curr": 10_040,
                "v_pw": 118.0,
                "last_ws_update_ts": time.time(),
                "ask_tot": 500,
                "bid_tot": 600,
                "open": 9_900,
                "fluctuation": 2.4,
                "strength_momentum_history": [],
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )

    refreshed, fields = state_handlers._pre_ai_refresh_quote_ws_snapshot(
        "123456",
        {
            "curr": 10_000,
            "v_pw": 99.0,
            "last_ws_update_ts": time.time() - 8.0,
            "strength_momentum_history": [],
        },
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_ai_ws_snapshot_refresh_applied"] is True
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert fields["pre_ai_ws_snapshot_refresh_history_count"] == 0
    assert fields["pre_ai_ws_snapshot_refresh_age_ms"] < 3000
    assert refreshed["curr"] == 10_040
    assert refreshed["ask_tot"] == 500


def test_pre_ai_quote_ws_snapshot_refresh_keeps_stale_latest_blocked(monkeypatch):
    class FakeWsManager:
        def get_latest_data(self, code):
            return {
                "curr": 10_020,
                "last_ws_update_ts": time.time() - 10.0,
                "ask_tot": 500,
                "bid_tot": 600,
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    original = {
        "curr": 10_000,
        "last_ws_update_ts": time.time() - 15.0,
    }

    refreshed, fields = state_handlers._pre_ai_refresh_quote_ws_snapshot(
        "123456",
        original,
        "SCALPING",
    )

    assert fields["pre_ai_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_ai_ws_snapshot_refresh_applied"] is False
    assert fields["pre_ai_ws_snapshot_refresh_reason"] == "latest_snapshot_stale"
    assert refreshed["curr"] == original["curr"]


def test_strength_source_quality_uses_refreshed_snapshot_age(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    ws_data = {"last_ws_update_ts": time.time() - 6.0}
    result = {
        "reason": "below_strength_base",
        "window_buy_ratio": 0.80,
        "window_exec_buy_ratio": 0.80,
        "window_net_buy_qty": 10,
        "window_total_value": 1000,
        "pre_ai_ws_snapshot_refresh_applied": True,
        "pre_ai_ws_snapshot_refresh_age_ms": 120.0,
    }

    assert (
        state_handlers._strength_momentum_source_quality_block_reason(ws_data, result)
        == ""
    )


def test_strength_source_quality_keeps_stale_refresh_blocked(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALP_PRE_AI_MAX_WS_AGE_SEC=3.0),
    )
    result = {
        "reason": "below_strength_base",
        "window_buy_ratio": 0.80,
        "window_exec_buy_ratio": 0.80,
        "window_net_buy_qty": 10,
        "window_total_value": 1000,
        "pre_ai_ws_snapshot_refresh_applied": False,
        "pre_ai_ws_snapshot_refresh_reason": "latest_snapshot_stale",
        "pre_ai_ws_snapshot_refresh_age_ms": 5000.0,
    }

    assert (
        state_handlers._strength_momentum_source_quality_block_reason(
            {"last_ws_update_ts": time.time() - 5.0},
            result,
        )
        == "stale_ws_snapshot"
    )


def test_real_pre_submit_ws_snapshot_refresh_accepts_flat_best_levels(monkeypatch):
    class FakeWsManager:
        def get_latest_data(self, code):
            assert code == "123456"
            return {
                "curr": 10_020,
                "last_ws_update_ts": time.time(),
                "best_ask": 10_030,
                "best_bid": 10_020,
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    refreshed, fields = state_handlers._pre_submit_refresh_real_ws_snapshot(
        "123456",
        {
            "curr": 10_000,
            "last_ws_update_ts": time.time() - 3.0,
            "best_ask": 10_010,
            "best_bid": 10_000,
        },
        "SCALPING",
    )

    assert fields["pre_submit_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_submit_ws_snapshot_refresh_applied"] is True
    assert fields["pre_submit_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert fields["pre_submit_ws_snapshot_refresh_best_bid"] == 10_020
    assert fields["pre_submit_ws_snapshot_refresh_best_ask"] == 10_030
    assert refreshed["best_bid"] == 10_020


def test_real_pre_submit_ws_snapshot_refresh_honors_explicit_operator_off(monkeypatch):
    class FakeWsManager:
        def get_latest_data(self, code):
            raise AssertionError(
                "WS manager must not be called when refresh is explicitly disabled"
            )

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "false")
    refreshed, fields = state_handlers._pre_submit_refresh_real_ws_snapshot(
        "123456",
        {
            "curr": 10_000,
            "last_ws_update_ts": time.time() - 3.0,
            "best_ask": 10_010,
            "best_bid": 10_000,
        },
        "SCALPING",
    )

    assert fields["pre_submit_ws_snapshot_refresh_enabled"] is False
    assert fields["pre_submit_ws_snapshot_refresh_applied"] is False
    assert fields["pre_submit_ws_snapshot_refresh_reason"] == "disabled"
    assert refreshed["curr"] == 10_000


def test_latency_false_negative_report_marker_defaults_disabled(monkeypatch, tmp_path):
    target_date = "2026-07-10"
    report_dir = tmp_path / "report" / "rising_missed_intraday_feedback"
    report_dir.mkdir(parents=True)
    (report_dir / f"rising_missed_intraday_feedback_{target_date}.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-07-10T09:55:35+09:00",
                "latency_false_negative_canary_candidate_rows": [
                    {"stock_code": "123456", "canary_grade": "ready_for_recheck"}
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_ENABLED", raising=False
    )
    monkeypatch.setattr(state_handlers, "DATA_DIR", tmp_path)
    stock = {
        "latency_false_negative_remeasure_candidate": True,
        "latency_false_negative_remeasure_candidate_source": "intraday_feedback_report",
        "latency_false_negative_report_canary_grade": "ready_for_recheck",
    }

    fields = state_handlers._apply_latency_false_negative_remeasure_report_marker(
        stock,
        "123456",
        now_dt=datetime(2026, 7, 10),
        now_ts=1.0,
    )

    assert fields["latency_false_negative_remeasure_report_loaded"] is False
    assert fields["latency_false_negative_remeasure_report_reason"] == "disabled"
    assert "latency_false_negative_remeasure_candidate" not in stock
    assert "latency_false_negative_report_canary_grade" not in stock


def test_latency_false_negative_report_marker_loads_ready_and_clears_stale(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_ENABLED", "true")
    target_date = "2026-07-10"
    report_dir = tmp_path / "report" / "rising_missed_intraday_feedback"
    report_dir.mkdir(parents=True)
    report_path = report_dir / f"rising_missed_intraday_feedback_{target_date}.json"
    report_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-07-10T09:55:35+09:00",
                "latency_false_negative_canary_candidate_rows": [
                    {
                        "stock_code": "123456",
                        "canary_grade": "ready_for_recheck",
                        "canary_cohort": "true_ofi_near_zero_false_negative",
                        "review_score_pct": 4.2,
                        "mfe_after_block_pct": 5.0,
                        "mae_after_block_pct": -0.8,
                    },
                    {"stock_code": "654321", "canary_grade": "hold_sample"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "DATA_DIR", tmp_path)
    state_handlers._LATENCY_FALSE_NEGATIVE_READY_CACHE.update(
        {
            "target_date": "",
            "loaded_at": 0.0,
            "generated_at": "",
            "rows": {},
            "reason": "reset",
        }
    )
    stock = {}

    fields = state_handlers._apply_latency_false_negative_remeasure_report_marker(
        stock,
        "123456",
        now_dt=datetime(2026, 7, 10),
        now_ts=1.0,
    )

    assert (
        fields["latency_false_negative_remeasure_report_reason"]
        == "ready_for_recheck_marker_applied"
    )
    assert stock["latency_false_negative_remeasure_candidate"] is True
    assert (
        stock["latency_false_negative_remeasure_candidate_source"]
        == "intraday_feedback_report"
    )
    assert stock["latency_false_negative_report_canary_grade"] == "ready_for_recheck"

    report_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-07-10T10:00:00+09:00",
                "latency_false_negative_canary_candidate_rows": [],
            }
        ),
        encoding="utf-8",
    )
    state_handlers._LATENCY_FALSE_NEGATIVE_READY_CACHE.update(
        {
            "target_date": "",
            "loaded_at": 0.0,
            "generated_at": "",
            "rows": {},
            "reason": "reset",
        }
    )
    fields = state_handlers._apply_latency_false_negative_remeasure_report_marker(
        stock,
        "123456",
        now_dt=datetime(2026, 7, 10),
        now_ts=2.0,
    )

    assert (
        fields["latency_false_negative_remeasure_report_reason"] == "ready_rows_empty"
    )
    assert "latency_false_negative_remeasure_candidate" not in stock
    assert "latency_false_negative_report_canary_grade" not in stock


def test_pre_submit_secondary_recheck_defaults_disabled(monkeypatch):
    monkeypatch.delenv(
        "KORSTOCKSCAN_PRE_SUBMIT_SECONDARY_RECHECK_ENABLED", raising=False
    )

    assert state_handlers._pre_submit_secondary_recheck_enabled() is False


def test_pre_submit_secondary_recheck_env_no_longer_opens_gate(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_SECONDARY_RECHECK_ENABLED", "true")

    assert state_handlers._pre_submit_secondary_recheck_enabled() is False


def test_caution_stale_negative_micro_submit_block_matches_ceylab_pattern(monkeypatch):
    monkeypatch.delenv(
        "KORSTOCKSCAN_SCALPING_ENTRY_CAUTION_STALE_NEGATIVE_MICRO_BLOCK_ENABLED",
        raising=False,
    )

    result = state_handlers._evaluate_caution_stale_negative_micro_submit_block(
        strategy="SCALPING",
        latency_gate={"latency_state": "CAUTION"},
        orderbook_fields={
            "orderbook_micro_qi": 0.425414,
            "orderbook_micro_ofi_norm": -1.883032,
        },
        microstructure_fields={
            "tick_context_stale": True,
            "tick_latest_age_ms": 7000,
            "curr_vs_micro_vwap_bp": -22.68,
            "curr_vs_ma5_bp": -26.57,
        },
    )

    assert result["blocked"] is True
    assert result["block_reason"] == "caution_stale_negative_micro_context"
    assert result["broker_order_forbidden"] is True
    assert result["threshold_family"] == "pre_submit_price_guard"


def test_caution_stale_negative_micro_submit_block_does_not_hard_block_safe_profit_case():
    result = state_handlers._evaluate_caution_stale_negative_micro_submit_block(
        strategy="SCALPING",
        latency_gate={"latency_state": "SAFE"},
        orderbook_fields={
            "orderbook_micro_qi": 0.058228,
            "orderbook_micro_ofi_norm": -1.628069,
        },
        microstructure_fields={
            "tick_context_stale": False,
            "tick_latest_age_ms": 1000,
            "curr_vs_micro_vwap_bp": -12.89,
            "curr_vs_ma5_bp": -20.24,
        },
    )

    assert result["blocked"] is False
    assert result["broker_order_forbidden"] is False


def test_caution_stale_negative_micro_submit_block_requires_stale_tick_context():
    result = state_handlers._evaluate_caution_stale_negative_micro_submit_block(
        strategy="SCALPING",
        latency_gate={"latency_state": "CAUTION"},
        orderbook_fields={
            "orderbook_micro_qi": 0.065574,
            "orderbook_micro_ofi_norm": -1.120229,
        },
        microstructure_fields={
            "tick_context_stale": False,
            "tick_latest_age_ms": 3000,
            "curr_vs_micro_vwap_bp": -104.43,
            "curr_vs_ma5_bp": -76.12,
        },
    )

    assert result["blocked"] is False
    assert result["broker_order_forbidden"] is False


def test_intraday_entry_price_discovery_relaxes_reprice_config(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED", "true")

    config = state_handlers._entry_reprice_config()

    assert config["max_attempts"] == 2
    assert config["max_upward_bps"] == 60
    assert config["max_spread_bps"] == 65
    assert config["strong_score_floor"] == 55.0
    assert config["strong_buy_pressure"] == 60.0


def test_intraday_entry_price_discovery_reprice_chooses_fresher_rest(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED", "true")
    monkeypatch.setattr(
        state_handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda code, ws_data, strategy: (
            {
                **dict(ws_data),
                "curr": 10_000,
                "best_bid": 9_990,
                "best_ask": 10_000,
            },
            {
                "pre_submit_ws_snapshot_refresh_enabled": True,
                "pre_submit_ws_snapshot_refresh_applied": True,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                "pre_submit_ws_snapshot_refresh_age_ms": 500.0,
                "pre_submit_ws_snapshot_refresh_best_bid": 9_990,
                "pre_submit_ws_snapshot_refresh_best_ask": 10_000,
                "pre_submit_ws_snapshot_refresh_latest_price": 10_000,
            },
        ),
    )
    monkeypatch.setattr(
        state_handlers,
        "_pre_submit_refresh_rest_orderbook_snapshot",
        lambda code, ws_data, strategy: (
            {
                **dict(ws_data),
                "curr": 10_020,
                "best_bid": 10_010,
                "best_ask": 10_020,
                "orderbook": {
                    "asks": [{"price": 10_020}],
                    "bids": [{"price": 10_010}],
                },
            },
            {
                "pre_submit_rest_orderbook_refresh_enabled": True,
                "pre_submit_rest_orderbook_refresh_applied": True,
                "pre_submit_rest_orderbook_refresh_reason": "rest_orderbook_fresh",
                "pre_submit_rest_orderbook_refresh_age_ms": 1.0,
                "pre_submit_rest_orderbook_refresh_best_bid": 10_010,
                "pre_submit_rest_orderbook_refresh_best_ask": 10_020,
                "pre_submit_rest_orderbook_refresh_latest_price": 10_020,
            },
        ),
    )

    snapshot, fields = state_handlers._entry_reprice_refresh_snapshot(
        "123456",
        {
            "best_bid": 9_990,
            "best_ask": 10_000,
            "last_trade_price": 10_000,
            "observer_last_quote_age_ms": 500.0,
        },
        {},
        {},
        "SCALPING",
        time.time(),
    )

    assert fields["entry_reprice_quote_refresh_source"] == "ka10004_rest_orderbook"
    assert fields["entry_reprice_quote_refresh_age_ms"] == 1.0
    assert snapshot["best_bid"] == 10_010
    assert snapshot["best_ask"] == 10_020
    assert snapshot["last_trade_price"] == 10_020


def test_real_pre_submit_rest_orderbook_refresh_uses_ka10004_fresh_snapshot(
    monkeypatch,
):
    now_hhmmss = datetime.now().strftime("%H%M%S")
    received_ts = time.time()

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": now_hhmmss,
            "rest_received_ts": received_ts,
            "curr": 0,
            "rest_current_price": 0,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "best_ask_qty": 100,
            "best_bid_qty": 200,
            "ask_tot": 1000,
            "bid_tot": 1200,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000"
    )

    refreshed, fields = state_handlers._pre_submit_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000, "best_ask": 10_010, "best_bid": 10_000},
        "SCALPING",
    )

    assert fields["pre_submit_rest_orderbook_refresh_enabled"] is True
    assert fields["pre_submit_rest_orderbook_refresh_applied"] is True
    assert fields["pre_submit_rest_orderbook_refresh_reason"] == "rest_orderbook_fresh"
    assert refreshed["curr"] == 10_025
    assert refreshed["best_ask"] == 10_030
    assert refreshed["best_bid"] == 10_020
    assert refreshed["quote_refresh_source"] == "ka10004_rest_orderbook"


def test_pre_submit_rest_orderbook_refresh_force_ignores_disabled_env(monkeypatch):
    now_hhmmss = datetime.now().strftime("%H%M%S")
    received_ts = time.time()

    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "false")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_REFRESH_ENABLED", "false"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000"
    )
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": now_hhmmss,
            "rest_received_ts": received_ts,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "best_ask_qty": 100,
            "best_bid_qty": 200,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )

    refreshed, fields = state_handlers._pre_submit_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000, "best_ask": 10_010, "best_bid": 10_000},
        "SCALPING",
        force=True,
    )

    assert fields["pre_submit_rest_orderbook_refresh_enabled"] is True
    assert fields["pre_submit_rest_orderbook_refresh_forced"] is True
    assert fields["pre_submit_rest_orderbook_refresh_applied"] is True
    assert fields["pre_submit_rest_orderbook_refresh_reason"] == "rest_orderbook_fresh"
    assert refreshed["quote_refresh_source"] == "ka10004_rest_orderbook"


def test_real_pre_submit_rest_orderbook_refresh_blocks_stale_ka10004_snapshot(
    monkeypatch,
):
    stale_hhmmss = datetime.fromtimestamp(time.time() - 10).strftime("%H%M%S")
    stale_received_ts = time.time() - 10

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "bid_req_base_tm": stale_hhmmss,
            "rest_received_ts": stale_received_ts,
            "curr": 10_030,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "500")

    refreshed, fields = state_handlers._pre_submit_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000, "best_ask": 10_010, "best_bid": 10_000},
        "SCALPING",
    )

    assert fields["pre_submit_rest_orderbook_refresh_enabled"] is True
    assert fields["pre_submit_rest_orderbook_refresh_applied"] is False
    assert fields["pre_submit_rest_orderbook_refresh_reason"] == "rest_orderbook_stale"
    assert refreshed["curr"] == 10_000


def test_real_pre_submit_rest_orderbook_refresh_ignores_bid_req_base_tm_for_freshness(
    monkeypatch,
):
    stale_hhmmss = datetime.fromtimestamp(time.time() - 3600).strftime("%H%M%S")
    received_ts = time.time()

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": stale_hhmmss,
            "rest_received_ts": received_ts,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000"
    )

    refreshed, fields = state_handlers._pre_submit_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000, "best_ask": 10_010, "best_bid": 10_000},
        "SCALPING",
    )

    assert fields["pre_submit_rest_orderbook_refresh_applied"] is True
    assert fields["pre_submit_rest_orderbook_refresh_reason"] == "rest_orderbook_fresh"
    assert fields["pre_submit_rest_orderbook_refresh_bid_req_base_tm"] == stale_hhmmss
    assert refreshed["curr"] == 10_025


def test_real_pre_submit_rest_orderbook_refresh_rejects_ka10004_age_ms_without_received_time(
    monkeypatch,
):
    now_hhmmss = datetime.now().strftime("%H%M%S")

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": now_hhmmss,
            "bid_req_base_tm_authority": "raw_not_freshness_input",
            "age_ms": 0,
            "rest_age_ms": 0,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000"
    )

    refreshed, fields = state_handlers._pre_submit_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000, "best_ask": 10_010, "best_bid": 10_000},
        "SCALPING",
    )

    assert fields["pre_submit_rest_orderbook_refresh_applied"] is False
    assert (
        fields["pre_submit_rest_orderbook_refresh_reason"]
        == "rest_orderbook_time_missing"
    )
    assert fields["pre_submit_rest_orderbook_refresh_age_ms"] is None
    assert refreshed["curr"] == 10_000


def test_holding_ai_rest_orderbook_refresh_reuses_fresh_ka10004_snapshot(monkeypatch):
    now_hhmmss = datetime.now().strftime("%H%M%S")
    received_ts = time.time()

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": now_hhmmss,
            "rest_received_ts": received_ts,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "best_ask_qty": 100,
            "best_bid_qty": 200,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000"
    )

    refreshed, fields = state_handlers._holding_ai_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000},
        "SCALPING",
    )

    assert fields["holding_ai_rest_orderbook_refresh_enabled"] is True
    assert fields["holding_ai_rest_orderbook_refresh_applied"] is True
    assert fields["holding_ai_rest_orderbook_refresh_reason"] == "rest_orderbook_fresh"
    assert fields["holding_ai_rest_orderbook_refresh_best_bid"] == 10_020
    assert "pre_submit_rest_orderbook_refresh_applied" not in refreshed
    assert refreshed["curr"] == 10_025
    assert refreshed["orderbook"]["bids"][0]["price"] == 10_020


def test_holding_ai_rest_orderbook_refresh_keeps_stale_snapshot_blocked(monkeypatch):
    stale_hhmmss = datetime.fromtimestamp(time.time() - 10).strftime("%H%M%S")
    stale_received_ts = time.time() - 10

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "bid_req_base_tm": stale_hhmmss,
            "rest_received_ts": stale_received_ts,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "500")

    refreshed, fields = state_handlers._holding_ai_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000},
        "SCALPING",
    )

    assert fields["holding_ai_rest_orderbook_refresh_enabled"] is True
    assert fields["holding_ai_rest_orderbook_refresh_applied"] is False
    assert fields["holding_ai_rest_orderbook_refresh_reason"] == "rest_orderbook_stale"
    assert refreshed["curr"] == 10_000
    assert "orderbook" not in refreshed


def test_holding_ai_rest_orderbook_refresh_skips_existing_usable_quote(monkeypatch):
    calls = []
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: calls.append((token, code)) or {},
    )

    refreshed, fields = state_handlers._holding_ai_refresh_rest_orderbook_snapshot(
        "123456",
        {
            "curr": 10_020,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
        "SCALPING",
    )

    assert calls == []
    assert fields["holding_ai_rest_orderbook_refresh_applied"] is False
    assert (
        fields["holding_ai_rest_orderbook_refresh_reason"] == "input_orderbook_usable"
    )
    assert refreshed["curr"] == 10_020


def test_holding_ai_rest_orderbook_refresh_rechecks_stale_usable_quote(monkeypatch):
    calls = []
    now_hhmmss = datetime.now().strftime("%H%M%S")
    received_ts = time.time()
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: calls.append((token, code))
        or {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": now_hhmmss,
            "rest_received_ts": received_ts,
            "rest_mid_price": 10_025,
            "best_ask": 10_030,
            "best_bid": 10_020,
            "best_ask_qty": 100,
            "best_bid_qty": 200,
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 200}],
            },
        },
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000"
    )

    refreshed, fields = state_handlers._holding_ai_refresh_rest_orderbook_snapshot(
        "123456",
        {
            "curr": 10_000,
            "best_bid": 9_990,
            "best_ask": 10_000,
            "quote_stale": True,
        },
        "SCALPING",
    )

    assert calls == [("TOKEN", "123456")]
    assert fields["holding_ai_rest_orderbook_refresh_applied"] is True
    assert fields["holding_ai_rest_orderbook_refresh_reason"] == "rest_orderbook_fresh"
    assert refreshed["curr"] == 10_025
    assert refreshed["best_bid"] == 10_020


def test_real_pre_submit_ws_snapshot_refresh_blocks_stale_ws_manager_snapshot(
    monkeypatch,
):
    class FakeWsManager:
        def get_latest_data(self, code):
            return {
                "curr": 10_020,
                "last_ws_update_ts": time.time() - 3.0,
                "orderbook": {
                    "asks": [{"price": 10_030, "volume": 100}],
                    "bids": [{"price": 10_020, "volume": 100}],
                },
            }

    monkeypatch.setattr(state_handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    stale_input = {
        "curr": 10_000,
        "last_ws_update_ts": time.time() - 4.0,
        "orderbook": {
            "asks": [{"price": 10_010, "volume": 100}],
            "bids": [{"price": 10_000, "volume": 100}],
        },
    }

    refreshed, fields = state_handlers._pre_submit_refresh_real_ws_snapshot(
        "123456",
        stale_input,
        "SCALPING",
    )

    assert fields["pre_submit_ws_snapshot_refresh_enabled"] is True
    assert fields["pre_submit_ws_snapshot_refresh_applied"] is False
    assert fields["pre_submit_ws_snapshot_refresh_reason"] == "latest_snapshot_stale"
    assert refreshed["curr"] == 10_000


def test_latency_entry_caution_submits_normal_after_slippage_check():
    stock = {"name": "TEST", "position_tag": "MIDDLE"}
    signal_time = datetime.now(UTC)
    freeze_signal_reference(
        stock,
        signal_price=10_000,
        strategy_id="SCALPING",
        signal_time=signal_time,
    )

    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_caution",
        ws_data={
            "curr": 10_010,
            "last_ws_update_ts": time.time() - 0.35,
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 100}],
                "bids": [{"price": 10_010, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=3,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "caution_normal_entry_allowed"
    assert result["mode"] == "normal"
    clear_signal_reference(stock)


def test_latency_submit_recovery_canary_not_needed_for_caution_normal(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED=True,
            SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE=75.0,
            SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS=1200,
            SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS=1500,
            SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO=0.0100,
        ),
    )
    stock = {"name": "TEST", "position_tag": "SCANNER"}
    freeze_signal_reference(
        stock,
        signal_price=10_000,
        strategy_id="SCALPING",
        signal_time=datetime.now(UTC),
    )

    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_recovery",
        ws_data={
            "curr": 10_010,
            "last_ws_update_ts": time.time() - 0.35,
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 100}],
                "bids": [{"price": 10_010, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=82.0,
    )

    assert result["policy_decision"] == "ALLOW_NORMAL"
    assert result["policy_reason"] == "caution_normal_entry_allowed"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "caution_normal_entry_allowed"
    assert result["latency_canary_applied"] is False
    assert result["latency_state"] == "CAUTION"
    clear_signal_reference(stock)


def test_latency_entry_canary_overrides_reject_danger_for_scanner(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=True,
            SCALP_LATENCY_FALLBACK_ENABLED=True,
            SCALP_LATENCY_GUARD_CANARY_TAGS=("SCANNER",),
            SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=300,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=0.0100,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_canary_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(
        result, danger_reasons="spread_above_caution_below_guard_cap"
    )


def test_latency_entry_canary_normalizes_probability_signal_strength(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=True,
            SCALP_LATENCY_FALLBACK_ENABLED=True,
            SCALP_LATENCY_GUARD_CANARY_TAGS=("SCANNER",),
            SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=300,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=0.0100,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_canary_prob",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.90,
    )

    _assert_danger_hard_safety_block(
        result, danger_reasons="spread_above_caution_below_guard_cap"
    )


def test_latency_entry_canary_does_not_apply_when_signal_score_low(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=True,
            SCALP_LATENCY_FALLBACK_ENABLED=True,
            SCALP_LATENCY_GUARD_CANARY_TAGS=("SCANNER",),
            SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE=95.0,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=300,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=0.0100,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_canary_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(
        result, danger_reasons="spread_above_caution_below_guard_cap"
    )


def test_latency_spread_caution_records_explicit_reason_without_taxonomy_gap(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=0.0100,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_other_danger_spread_gap",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=70.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_danger_reasons"] == "spread_above_caution_below_guard_cap"
    assert (
        result["latency_danger_detail_reason"] == "spread_above_caution_below_guard_cap"
    )
    assert result["latency_danger_source_quality_state"] == "fresh"
    assert result["latency_danger_reason_taxonomy_gap"] is False
    assert result["latency_danger_max_spread_ratio_for_caution"] == 0.005
    assert result["latency_danger_guard_max_spread_ratio"] == 0.01
    assert result["latency_spread_relief_block_reason"] == "low_signal"
    assert result["latency_relief_attempted"] is True
    assert result["latency_relief_block_reason"] == "low_signal"
    assert (
        result["latency_spread_relief_signal_score_source"] == "input_signal_strength"
    )
    assert result["latency_spread_relief_signal_source_quality_state"] == "fresh"
    assert result["latency_spread_block_price_bucket"] == "spread_above_caution"
    assert result["latency_spread_block_signal_context_bucket"] == "signal_fresh"
    assert result["latency_spread_block_bucket"] == "spread_above_caution"


def test_latency_spread_relief_canary_overrides_reject_danger_to_normal(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0120,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_spread_relief_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_spread_relief_normal_override"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "spread_relief_canary_applied"
    assert result["latency_danger_reasons"] == "spread_too_wide"
    assert result["latency_strategy_id"] == "SCALPING"
    assert result["latency_position_tag"] == "SCANNER"


def test_latency_spread_relief_canary_accepts_scalp_strategy_alias(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0120,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_relief_scalp_alias",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALP",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["latency_canary_reason"] == "spread_relief_canary_applied"
    assert result["latency_strategy_id"] == "SCALP"


def test_latency_spread_relief_canary_uses_entry_momentum_tag_when_position_tag_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("KOSPI_BASE",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
        ),
    )

    stock = {"name": "TEST", "entry_momentum_tag": "KOSPI_BASE"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_spread_relief_momentum_tag_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_spread_relief_normal_override"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "spread_relief_canary_applied"


def test_latency_spread_relief_canary_enforces_effective_min_signal_floor(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_relief_low_score_blocked",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=78.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_danger_reasons"] == "spread_too_wide"
    assert result["latency_spread_relief_signal_score"] == 78.0
    assert result["latency_spread_relief_configured_min_signal_score"] == 60.0
    assert result["latency_spread_relief_effective_min_signal_score"] == 85.0
    assert result["latency_spread_relief_tag"] == "SCANNER"


def test_latency_spread_relief_records_prior_ai_signal_source_gap(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER", "ai_score": 62},
        code="123456_spread_signal_source_gap",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_spread_relief_block_reason"] == "low_signal"
    assert result["latency_spread_relief_signal_score"] == 0.0
    assert (
        result["latency_spread_relief_signal_score_source"]
        == "input_signal_strength_zero"
    )
    assert result["latency_spread_relief_signal_source_quality_state"] == "source_gap"
    assert result["latency_spread_relief_candidate_ai_score"] == 62.0
    assert result["latency_spread_relief_candidate_ai_score_source"] == "stock.ai_score"
    assert (
        result["latency_spread_relief_source_quality_gap"]
        == "prior_ai_available_but_signal_strength_zero"
    )
    assert result["latency_spread_block_price_bucket"] == "true_wide_spread"
    assert result["latency_spread_block_signal_context_bucket"] == "signal_source_gap"
    assert result["latency_spread_block_bucket"] == "true_wide_spread|signal_source_gap"


def test_latency_spread_relief_candidate_ai_prefers_positive_ws_over_stock_zero(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER", "ai_score": 0},
        code="123456_spread_signal_ws_source_gap",
        ws_data={
            "curr": 10_020,
            "ai_score": 63,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_spread_relief_block_reason"] == "low_signal"
    assert result["latency_spread_relief_signal_source_quality_state"] == "source_gap"
    assert result["latency_spread_relief_candidate_ai_score"] == 63.0
    assert result["latency_spread_relief_candidate_ai_score_source"] == "ws.ai_score"


def test_latency_spread_relief_uses_fresh_orderbook_micro_signal_when_input_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_micro_signal_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_ready": True,
            "orderbook_micro_reason": "ready",
            "orderbook_micro_observer_healthy": True,
            "orderbook_micro_snapshot_age_ms": 20,
            "orderbook_micro_sample_quote_count": 25,
            "orderbook_micro_micro_z_min_samples": 20,
            "orderbook_micro_ofi_z": 1.5,
            "orderbook_micro_ofi_bull_threshold": 1.2,
            "orderbook_micro_qi_ewma": 0.62,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_spread_relief_normal_override"
    assert result["latency_danger_reasons"] == "spread_above_caution_below_guard_cap"
    assert result["latency_spread_relief_signal_score"] >= 80.0
    assert (
        result["latency_spread_relief_signal_score_source"]
        == "ws.orderbook_micro_ofi_qi"
    )
    assert result["latency_spread_relief_signal_source_quality_state"] == "fresh"
    assert result["latency_spread_relief_block_reason"] == ""


def test_latency_spread_relief_does_not_use_insufficient_orderbook_micro_signal(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_micro_signal_insufficient",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_ready": False,
            "orderbook_micro_reason": "insufficient_samples",
            "orderbook_micro_observer_healthy": True,
            "orderbook_micro_snapshot_age_ms": 20,
            "orderbook_micro_sample_quote_count": 8,
            "orderbook_micro_micro_z_min_samples": 20,
            "orderbook_micro_ofi_z": 2.5,
            "orderbook_micro_qi_ewma": 0.70,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_spread_relief_block_reason"] == "low_signal"
    assert result["latency_spread_relief_signal_score"] == 0.0
    assert result["latency_spread_relief_signal_score_source"] == "missing"
    assert result["latency_spread_relief_signal_source_quality_state"] == "missing"


def test_latency_spread_relief_uses_fresh_true_ofi_estimator_when_observer_window_is_short(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.90,
                "true_ofi_ewma": 0.50,
                "pressure_ewma": 75.0,
                "top_depth_ratio": 1.25,
                "true_ofi_sample_count": 12,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_true_ofi_estimator_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook_micro_ready": False,
            "orderbook_micro_reason": "insufficient_samples",
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_spread_relief_normal_override"
    assert (
        result["latency_spread_relief_signal_score_source"]
        == "micro_estimator.true_ofi_ewma"
    )
    assert result["latency_spread_relief_micro_estimator_eligible"] is True
    assert result["latency_spread_relief_micro_estimator_true_ofi_sample_count"] == 12


def test_latency_spread_relief_true_ofi_estimator_keeps_block_below_sample_floor(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.90,
                "true_ofi_ewma": 0.50,
                "pressure_ewma": 75.0,
                "top_depth_ratio": 1.25,
                "true_ofi_sample_count": 7,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_true_ofi_estimator_sample_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_spread_relief_micro_estimator_eligible"] is False
    assert (
        result["latency_spread_relief_micro_estimator_reason"]
        == "true_ofi_samples_below_floor"
    )


def test_latency_false_negative_remeasure_enqueues_report_ready_true_ofi_without_allowing_submit(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": -0.05,
                "true_ofi_sample_count": 140,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "latency_false_negative_report_canary_grade": "ready_for_recheck",
            "latency_false_negative_report_canary_cohort": "true_ofi_near_zero_false_negative",
        },
        code="123456_false_negative_remeasure_ready",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["allowed"] is False
    assert result["latency_false_negative_remeasure_enqueued"] is True
    assert result["latency_false_negative_remeasure_grade"] == "ready_for_recheck"
    assert (
        result["latency_false_negative_remeasure_reason"]
        == "true_ofi_near_zero_or_positive_with_fresh_ws"
    )
    assert result["latency_false_negative_remeasure_runtime_effect"] is False
    assert result["latency_false_negative_remeasure_allowed_runtime_apply"] is False


def test_latency_false_negative_remeasure_requires_report_ready_marker(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.03,
                "true_ofi_sample_count": 140,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_false_negative_remeasure_no_marker",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_false_negative_remeasure_enqueued"] is False
    assert (
        result["latency_false_negative_remeasure_reason"]
        == "report_ready_for_recheck_missing"
    )


def _enable_latency_true_ofi_direct_canary(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )


def test_latency_true_ofi_direct_canary_dynamic_age_band_allows_strong_ws_tape(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    common = {
        "stock": {
            "rising_missed_entry_lineage": True,
            "price_delta_since_first_seen_pct": "4.2",
            "rising_missed_tp1_submit_context_fresh": True,
            "rising_missed_tp1_submit_context_at": time.time(),
            "rising_missed_tp1_submit_context_support_count": 2,
        },
        "ws_data": {
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 5,
            "buy_pressure_10t": 80.0,
            "buy_exec_volume": 500,
            "sell_exec_volume": 0,
            "net_buy_exec_volume": 500,
            "orderbook_micro_state": "bullish",
            "recent_trade_ticks": [
                {
                    "signed_trade_volume": value,
                    "aggressor_source": "kiwoom_0b_signed_trade_volume",
                }
                for value in ("+100", "+90", "+80", "+70", "+60")
            ],
        },
        "strategy_id": "SCALPING",
        "policy_decision": entry_latency_module.EntryDecision.REJECT_DANGER,
        "effective_decision": entry_latency_module.EntryDecision.REJECT_DANGER,
        "latency_status": SimpleNamespace(quote_stale=False),
        "danger_reasons": ["spread_too_wide"],
        "spread_bps": 51.0,
        "signal_score": 70.0,
        "micro_estimator_reason": "true_ofi_below_floor",
        "estimator_context": {
            "latency_false_negative_remeasure_true_ofi_ewma": 0.02,
            "latency_false_negative_remeasure_true_ofi_sample_count": 92,
            "latency_false_negative_remeasure_ws_age_ms": 443.7,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
        },
        "danger_relief_forbidden": False,
    }

    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(**common)

    assert fields["latency_true_ofi_direct_canary_applied"] is True
    assert fields["latency_true_ofi_direct_canary_dynamic_age_band_eligible"] is True
    assert fields["latency_true_ofi_direct_canary_dynamic_age_band_applied"] is True
    assert fields["latency_true_ofi_direct_canary_effective_max_ws_age_ms"] == 500.0

    mixed_tape = dict(common)
    mixed_tape["ws_data"] = {
        **common["ws_data"],
        "recent_trade_ticks": [
            {
                "signed_trade_volume": value,
                "aggressor_source": "kiwoom_0b_signed_trade_volume",
            }
            for value in ("+100", "+90", "+80", "-70", "-60")
        ],
    }
    blocked = entry_latency_module._latency_true_ofi_direct_canary_fields(**mixed_tape)

    assert blocked["latency_true_ofi_direct_canary_applied"] is False
    assert blocked["latency_true_ofi_direct_canary_dynamic_age_band_eligible"] is False
    assert blocked["latency_true_ofi_direct_canary_reason"] == (
        "ws_age_above_direct_canary_cap"
    )


def test_latency_true_ofi_dynamic_age_band_allows_bounded_low_sample_buy_burst(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    active_date = datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d")
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_ACTIVE_DATE",
        active_date,
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_MIN_SAMPLES",
        "25",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_MAX_WS_AGE_MS",
        "1200",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_MAX_SPREAD_BPS",
        "70",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_MIN_SIGNED_TAPE_BUY_RATIO",
        "100",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_DYNAMIC_AGE_BAND_MIN_SIGNED_TAPE_SAMPLES",
        "4",
    )
    common = {
        "stock": {
            "rising_missed_entry_lineage": True,
            "price_delta_since_first_seen_pct": "1.10",
            "source_signature": "BID_IMBALANCE_SURGE,VOLUME_SURGE_POSITIVE",
            "rising_missed_tp1_submit_context_fresh": True,
            "rising_missed_tp1_submit_context_at": time.time(),
            "rising_missed_tp1_submit_context_support_count": 2,
        },
        "ws_data": {
            "orderbook_micro_state": "neutral",
            "recent_trade_ticks": [
                {
                    "signed_trade_volume": value,
                    "aggressor_source": "kiwoom_0b_signed_trade_volume",
                }
                for value in ("+813", "+500", "+400", "+217")
            ],
        },
        "strategy_id": "SCALPING",
        "policy_decision": entry_latency_module.EntryDecision.REJECT_DANGER,
        "effective_decision": entry_latency_module.EntryDecision.REJECT_DANGER,
        "latency_status": SimpleNamespace(quote_stale=False),
        "danger_reasons": ["spread_above_caution_below_guard_cap"],
        "spread_bps": 67.935,
        "signal_score": 0.0,
        "micro_estimator_reason": "ws_state_stale_or_missing",
        "estimator_context": {
            "latency_false_negative_remeasure_true_ofi_ewma": 0.0008,
            "latency_false_negative_remeasure_true_ofi_sample_count": 29,
            "latency_false_negative_remeasure_ws_age_ms": 1113.572,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
        },
        "danger_relief_forbidden": False,
    }

    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(**common)

    assert fields["latency_true_ofi_direct_canary_applied"] is True
    assert fields["latency_true_ofi_direct_canary_dynamic_age_band_eligible"] is True
    assert fields["latency_true_ofi_direct_canary_dynamic_age_band_applied"] is True
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "direct_canary_dynamic_age_signed_tape_allow"
    )
    assert fields["latency_true_ofi_direct_canary_dynamic_age_band_min_samples"] == 25
    assert (
        fields[
            "latency_true_ofi_direct_canary_dynamic_age_band_min_signed_tape_samples"
        ]
        == 4
    )

    negative_ofi = {
        **common,
        "estimator_context": {
            **common["estimator_context"],
            "latency_false_negative_remeasure_true_ofi_ewma": -0.001,
        },
    }
    blocked = entry_latency_module._latency_true_ofi_direct_canary_fields(
        **negative_ofi
    )

    assert blocked["latency_true_ofi_direct_canary_applied"] is False
    assert blocked["latency_true_ofi_direct_canary_dynamic_age_band_eligible"] is False

    thin_tape = {
        **common,
        "ws_data": {
            **common["ws_data"],
            "recent_trade_ticks": common["ws_data"]["recent_trade_ticks"][:3],
        },
    }
    thin_tape_blocked = entry_latency_module._latency_true_ofi_direct_canary_fields(
        **thin_tape
    )

    assert thin_tape_blocked["latency_true_ofi_direct_canary_applied"] is False
    assert (
        thin_tape_blocked["latency_true_ofi_direct_canary_dynamic_age_band_eligible"]
        is False
    )

    stale_tp1 = {
        **common,
        "stock": {
            **common["stock"],
            "rising_missed_tp1_submit_context_at": time.time() - 61.0,
        },
    }
    stale_tp1_blocked = entry_latency_module._latency_true_ofi_direct_canary_fields(
        **stale_tp1
    )

    assert stale_tp1_blocked["latency_true_ofi_direct_canary_applied"] is False
    assert (
        stale_tp1_blocked["latency_true_ofi_direct_canary_dynamic_age_band_eligible"]
        is False
    )


def _enable_latency_true_ofi_nxt_probability_band(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_PROBABILITY_BAND_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_PROBABILITY_BAND_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )


def test_latency_true_ofi_nxt_probability_band_is_nxt_only_and_bounded(monkeypatch):
    _enable_latency_true_ofi_nxt_probability_band(monkeypatch)
    common_stock = {
        "rising_missed_entry_lineage": True,
        "rising_missed_effective_venue": "NXT",
        "rising_missed_market_session_bucket": "nxt_entry_window",
        "rising_missed_nxt_eligible": True,
        "rising_missed_ws_0b_route": "krx_nxt_integrated",
        "rising_missed_ws_0d_route": "krx_nxt_integrated",
        "rising_missed_tp1_evaluation_id": "nxt-probability-eval",
        "rising_missed_tp1_submit_context_fresh": True,
        "price_delta_since_first_seen_pct": "15.40",
    }
    estimator_context = {
        "latency_false_negative_remeasure_true_ofi_ewma": -0.0104,
        "latency_false_negative_remeasure_true_ofi_sample_count": 122,
        "latency_false_negative_remeasure_ws_age_ms": 60.0,
        "latency_false_negative_remeasure_source_state": ("fresh_ws_order_flow_delta"),
        "latency_false_negative_remeasure_estimator_confidence": 0.8494,
        "latency_false_negative_remeasure_pressure_ewma": 61.462,
        "latency_false_negative_remeasure_top_depth_ratio": 1.6032,
    }
    ws_data = {
        "recent_trade_ticks": [
            {
                "signed_trade_volume": "-1",
                "aggressor_source": "kiwoom_0b_signed_trade_volume",
            }
            for _ in range(5)
        ]
    }

    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=common_stock,
        ws_data=ws_data,
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=125.261,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context=estimator_context,
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is True
    assert fields["latency_true_ofi_nxt_probability_band_applied"] is True
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "direct_canary_nxt_probability_band_allow"
    )
    assert fields["latency_true_ofi_direct_canary_signed_tape_sell_dominated"] is True

    aged_fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=common_stock,
        ws_data=ws_data,
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["ws_age_too_high", "spread_too_wide"],
        spread_bps=103.734,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            **estimator_context,
            "latency_false_negative_remeasure_true_ofi_ewma": -0.0109,
            "latency_false_negative_remeasure_true_ofi_sample_count": 77,
            "latency_false_negative_remeasure_ws_age_ms": 587.0,
            "latency_false_negative_remeasure_pressure_ewma": 64.688,
            "latency_false_negative_remeasure_top_depth_ratio": 1.8239,
        },
        danger_relief_forbidden=False,
    )

    assert aged_fields["latency_true_ofi_nxt_probability_band_applied"] is True

    krx_fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={**common_stock, "rising_missed_effective_venue": "KRX"},
        ws_data=ws_data,
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=125.261,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context=estimator_context,
        danger_relief_forbidden=False,
    )

    assert krx_fields["latency_true_ofi_nxt_probability_band_context"] is False
    assert krx_fields["latency_true_ofi_nxt_probability_band_applied"] is False
    assert krx_fields["latency_true_ofi_direct_canary_applied"] is False

    missing_route_fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={**common_stock, "rising_missed_ws_0d_route": "unknown"},
        ws_data=ws_data,
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=125.261,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context=estimator_context,
        danger_relief_forbidden=False,
    )

    assert (
        missing_route_fields["latency_true_ofi_nxt_probability_band_context"] is False
    )
    assert (
        missing_route_fields["latency_true_ofi_nxt_probability_band_applied"] is False
    )


def test_latency_true_ofi_direct_canary_allows_high_opportunity_without_report_marker(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_REPASS_ENABLED", raising=False
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.012,
                "true_ofi_sample_count": 120,
                "last_ws_ts": now_ts - 0.08,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "5.88",
        },
        code="123456_true_ofi_direct_canary",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "buy_pressure_10t": 68.0,
            "buy_exec_volume": 680,
            "sell_exec_volume": 320,
            "net_buy_exec_volume": 360,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.70,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["allowed"] is True
    assert result["latency_canary_reason"] == "latency_true_ofi_direct_canary_applied"
    assert result["latency_true_ofi_direct_canary_applied"] is True
    assert (
        result["latency_true_ofi_direct_canary_reason"]
        == "direct_canary_true_ofi_false_negative_allow"
    )
    assert result["latency_true_ofi_direct_canary_max_spread_bps"] == 90.0
    assert result["latency_true_ofi_direct_canary_relief_runtime_enabled"] is True
    assert result["latency_true_ofi_direct_canary_tape_support_ok"] is True
    assert result["latency_false_negative_remeasure_enqueued"] is False
    assert (
        result["latency_false_negative_remeasure_reason"]
        == "report_ready_for_recheck_missing"
    )


def test_latency_true_ofi_direct_canary_allows_near_cap_spread(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MAX_SPREAD_BPS", raising=False
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": -0.02,
                "true_ofi_sample_count": 120,
                "last_ws_ts": now_ts - 0.08,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "6.16",
        },
        code="123456_true_ofi_direct_canary_near_cap",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": now_ts,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "buy_pressure_10t": 68.0,
            "buy_exec_volume": 680,
            "sell_exec_volume": 320,
            "net_buy_exec_volume": 360,
            "orderbook": {
                "asks": [{"price": 10_088, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.70,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["allowed"] is True
    assert result["latency_true_ofi_direct_canary_applied"] is True
    assert result["latency_true_ofi_direct_canary_spread_bps"] == 88.0
    assert result["latency_true_ofi_direct_canary_max_spread_bps"] == 90.0


def test_latency_true_ofi_direct_canary_allows_bounded_extended_spread_tier(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.0412,
                "true_ofi_sample_count": 222,
                "last_ws_ts": now_ts - 0.10,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "NEW_HIGH_CONFIRMATION,VOLUME_SURGE_POSITIVE",
            "price_delta_since_first_seen_pct": "3.79",
            "rising_missed_tp1_submit_context_support_count": 3,
        },
        code="123456_true_ofi_direct_canary_extended",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": now_ts,
            "recent_trade_ticks": [
                {
                    "signed_trade_volume": signed_volume,
                    "aggressor_source": "kiwoom_0b_signed_trade_volume",
                }
                for signed_volume in ("+100", "+80", "+60", "-30", "-20")
            ],
            "orderbook": {
                "asks": [{"price": 10_118, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["allowed"] is True
    assert result["latency_true_ofi_direct_canary_applied"] is True
    assert result["latency_true_ofi_direct_canary_extended_tier_applied"] is True
    assert result["latency_true_ofi_direct_canary_reason"] == (
        "direct_canary_extended_spread_true_ofi_allow"
    )
    assert result["latency_true_ofi_direct_canary_spread_bps"] == 118.0


def test_latency_true_ofi_direct_canary_extended_tier_keeps_weak_support_blocked(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={
            "rising_missed_entry_lineage": True,
            "price_delta_since_first_seen_pct": "3.79",
            "rising_missed_tp1_submit_context_support_count": 2,
        },
        ws_data={
            "recent_trade_ticks": [
                {"signed_trade_volume": "+100"},
                {"signed_trade_volume": "+80"},
                {"signed_trade_volume": "+60"},
                {"signed_trade_volume": "-30"},
                {"signed_trade_volume": "-20"},
            ]
        },
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=118.0,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.0412,
            "latency_false_negative_remeasure_true_ofi_sample_count": 222,
            "latency_false_negative_remeasure_ws_age_ms": 100.0,
            "latency_false_negative_remeasure_source_state": "fresh_ws_order_flow_delta",
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is False
    assert fields["latency_true_ofi_direct_canary_extended_tier_applied"] is False
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "extended_spread_support_count_below_floor"
    )


def test_latency_true_ofi_direct_canary_recovers_fresh_low_rebound_anchor_loss(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={
            "rising_missed_entry_lineage": True,
            "price_delta_since_first_seen_pct": "0.0",
            "rising_missed_tp1_submit_context_fresh": True,
            "rising_missed_tp1_submit_context_low_rebound_pct": 2.68,
            "rising_missed_tp1_submit_context_support_count": 2,
        },
        ws_data={
            "buy_ratio": 50.42,
            "recent_trade_ticks": [
                {
                    "signed_trade_volume": value,
                    "aggressor_source": "kiwoom_0b_signed_trade_volume",
                }
                for value in ("+3", "-20", "-15", "+2", "-17")
            ],
        },
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=108.46,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.0257,
            "latency_false_negative_remeasure_true_ofi_sample_count": 74,
            "latency_false_negative_remeasure_ws_age_ms": 113.0,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
            "latency_false_negative_remeasure_estimator_confidence": 0.8489,
            "latency_false_negative_remeasure_pressure_ewma": 52.531,
            "latency_false_negative_remeasure_top_depth_ratio": 1.1167,
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is True
    assert fields["latency_true_ofi_direct_canary_low_rebound_recovery_applied"] is True
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "direct_canary_low_rebound_recovery_allow"
    )


def test_latency_true_ofi_direct_canary_low_rebound_recovery_keeps_stale_blocked(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={
            "rising_missed_entry_lineage": True,
            "rising_missed_tp1_submit_context_low_rebound_pct": 2.68,
            "rising_missed_tp1_submit_context_support_count": 2,
        },
        ws_data={"buy_pressure_10t": 60.0},
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=True),
        danger_reasons=["spread_too_wide"],
        spread_bps=108.46,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.03,
            "latency_false_negative_remeasure_true_ofi_sample_count": 100,
            "latency_false_negative_remeasure_ws_age_ms": 100.0,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
            "latency_false_negative_remeasure_estimator_confidence": 0.9,
            "latency_false_negative_remeasure_pressure_ewma": 60.0,
            "latency_false_negative_remeasure_top_depth_ratio": 1.2,
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is False
    assert fields["latency_true_ofi_direct_canary_reason"] == "quote_stale"


def test_latency_true_ofi_low_rebound_sample_relief_does_not_change_base_band(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={
            "rising_missed_entry_lineage": True,
            "rising_missed_tp1_submit_context_low_rebound_pct": 3.0,
            "rising_missed_tp1_submit_context_support_count": 3,
        },
        ws_data={},
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=80.0,
        signal_score=80.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.02,
            "latency_false_negative_remeasure_true_ofi_sample_count": 60,
            "latency_false_negative_remeasure_ws_age_ms": 100.0,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is False
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "true_ofi_samples_below_floor"
    )


def test_latency_true_ofi_direct_canary_extended_tier_rejects_rest_positive_tape(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    now_ts = time.time()
    rest_ticks = [
        {
            "signed_trade_volume": signed_volume,
            "rest_signed_tape_source": "ka10084",
            "rest_signed_tape_received_at": now_ts,
            "source_timestamp": now_ts,
        }
        for signed_volume in ("+100", "+80", "+60")
    ]
    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={
            "rising_missed_entry_lineage": True,
            "price_delta_since_first_seen_pct": "3.79",
            "rising_missed_tp1_submit_context_support_count": 3,
        },
        ws_data={"rest_signed_trade_ticks": rest_ticks},
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=118.0,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.0412,
            "latency_false_negative_remeasure_true_ofi_sample_count": 222,
            "latency_false_negative_remeasure_ws_age_ms": 100.0,
            "latency_false_negative_remeasure_source_state": "fresh_ws_order_flow_delta",
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is False
    assert (
        fields["latency_true_ofi_direct_canary_extended_signed_tape_ws_only"] is False
    )
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "extended_spread_trusted_ws_signed_tape_required"
    )


def test_latency_true_ofi_direct_canary_extended_tier_rejects_unknown_tape_source(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_EXTENDED_SPREAD_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock={
            "rising_missed_entry_lineage": True,
            "price_delta_since_first_seen_pct": "3.79",
            "rising_missed_tp1_submit_context_support_count": 3,
        },
        ws_data={
            "recent_trade_ticks": [
                {"signed_trade_volume": "+100"},
                {"signed_trade_volume": "+80"},
                {"signed_trade_volume": "+60"},
            ]
        },
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_too_wide"],
        spread_bps=118.0,
        signal_score=0.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.0412,
            "latency_false_negative_remeasure_true_ofi_sample_count": 222,
            "latency_false_negative_remeasure_ws_age_ms": 100.0,
            "latency_false_negative_remeasure_source_state": "fresh_ws_order_flow_delta",
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is False
    assert (
        fields["latency_true_ofi_direct_canary_extended_signed_tape_ws_only"] is False
    )
    assert (
        fields["latency_true_ofi_direct_canary_signed_tape_unknown_source_count"] == 3
    )
    assert fields["latency_true_ofi_direct_canary_reason"] == (
        "extended_spread_trusted_ws_signed_tape_required"
    )


def test_latency_true_ofi_direct_canary_treats_missing_tape_as_neutral(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.018,
                "true_ofi_sample_count": 120,
                "last_ws_ts": now_ts - 0.06,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "5.42",
        },
        code="123456_true_ofi_direct_canary_missing_tape",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.70,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["allowed"] is True
    assert result["latency_true_ofi_direct_canary_applied"] is True
    assert (
        result["latency_true_ofi_direct_canary_reason"]
        == "direct_canary_true_ofi_false_negative_allow"
    )
    assert result["latency_true_ofi_direct_canary_tape_support_ok"] is True
    assert (
        result["latency_true_ofi_direct_canary_tape_block_reason"]
        == "tape_support_ok_missing_pressure"
    )


def test_latency_true_ofi_direct_canary_blocks_sell_dominated_tape(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_REPASS_ENABLED", raising=False
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": -0.001,
                "true_ofi_sample_count": 1900,
                "last_ws_ts": now_ts - 0.07,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,BID_IMBALANCE_SURGE",
            "price_delta_since_first_seen_pct": "5.31",
        },
        code="123456_true_ofi_direct_canary_sell_tape",
        ws_data={
            "curr": 7_320,
            "last_ws_update_ts": now_ts,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "buy_pressure_10t": 4.13,
            "buy_exec_volume": 9_121_202,
            "sell_exec_volume": 11_951_515,
            "net_buy_exec_volume": -2_830_313,
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 7_370, "volume": 5_575}],
                "bids": [{"price": 7_320, "volume": 32_238}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=27,
        signal_price=7_320,
        signal_strength=0.70,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["allowed"] is False
    assert result["latency_true_ofi_direct_canary_applied"] is False
    assert result["latency_true_ofi_direct_canary_reason"] == "sell_dominated_tape"
    assert result["latency_true_ofi_direct_canary_tape_support_ok"] is False
    assert result["latency_true_ofi_direct_canary_tape_net_buy_exec_volume"] < 0


def test_latency_true_ofi_direct_canary_blocks_recent_signed_sell_tape(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_REPASS_ENABLED", raising=False
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.001,
                "true_ofi_sample_count": 1900,
                "last_ws_ts": now_ts - 0.07,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,BID_IMBALANCE_SURGE",
            "price_delta_since_first_seen_pct": "5.31",
        },
        code="123456_true_ofi_direct_canary_signed_sell_tape",
        ws_data={
            "curr": 7_320,
            "last_ws_update_ts": now_ts,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "buy_pressure_10t": 68.0,
            "buy_exec_volume": 15_000,
            "sell_exec_volume": 8_000,
            "net_buy_exec_volume": 7_000,
            "recent_trade_ticks": [
                {"aggressor_aux_raw_15": "-200", "volume": 200},
                {"aggressor_aux_raw_15": "-150", "volume": 150},
                {"aggressor_aux_raw_15": "+50", "volume": 50},
            ],
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 7_370, "volume": 5_575}],
                "bids": [{"price": 7_320, "volume": 32_238}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=27,
        signal_price=7_320,
        signal_strength=0.70,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["allowed"] is False
    assert result["latency_true_ofi_direct_canary_applied"] is False
    assert (
        result["latency_true_ofi_direct_canary_reason"] == "signed_tape_sell_dominated"
    )
    assert result["latency_true_ofi_direct_canary_signed_tape_sell_dominated"] is True
    assert result["latency_true_ofi_direct_canary_signed_tape_sell_count"] == 2
    assert result["latency_true_ofi_direct_canary_signed_tape_net_buy_volume"] < 0


def test_latency_true_ofi_direct_canary_blocks_rest_signed_sell_tape(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_REPASS_ENABLED", raising=False
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.001,
                "true_ofi_sample_count": 1900,
                "last_ws_ts": now_ts - 0.07,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,BID_IMBALANCE_SURGE",
            "price_delta_since_first_seen_pct": "5.31",
        },
        code="123456_true_ofi_direct_canary_rest_signed_sell_tape",
        ws_data={
            "curr": 7_320,
            "last_ws_update_ts": now_ts,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "buy_pressure_10t": 68.0,
            "buy_exec_volume": 15_000,
            "sell_exec_volume": 8_000,
            "net_buy_exec_volume": 7_000,
            "rest_signed_trade_ticks": [
                {
                    "signed_trade_volume": "-200",
                    "volume": 200,
                    "rest_signed_tape_source": "ka10084",
                    "rest_signed_tape_received_at": now_ts,
                    "source_timestamp": now_ts,
                },
                {
                    "signed_trade_volume": "-150",
                    "volume": 150,
                    "rest_signed_tape_source": "ka10084",
                    "rest_signed_tape_received_at": now_ts,
                    "source_timestamp": now_ts - 0.1,
                },
                {
                    "signed_trade_volume": "+50",
                    "volume": 50,
                    "rest_signed_tape_source": "ka10084",
                    "rest_signed_tape_received_at": now_ts,
                    "source_timestamp": now_ts - 0.2,
                },
            ],
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 7_370, "volume": 5_575}],
                "bids": [{"price": 7_320, "volume": 32_238}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=27,
        signal_price=7_320,
        signal_strength=0.70,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["allowed"] is False
    assert result["latency_true_ofi_direct_canary_applied"] is False
    assert (
        result["latency_true_ofi_direct_canary_reason"] == "signed_tape_sell_dominated"
    )
    assert result["latency_true_ofi_direct_canary_signed_tape_sell_count"] == 2
    assert result["latency_true_ofi_direct_canary_signed_tape_net_buy_volume"] < 0


def test_rest_signed_tape_counts_unsigned_buy_rows_with_rest_side():
    now_ts = time.time()
    fields = entry_latency_module._latency_signed_tape_fields(
        {},
        {
            "rest_signed_trade_ticks": [
                {
                    "signed_trade_volume": "120",
                    "aggressor_side": "BUY",
                    "aggressor_source": "kiwoom_rest_ka10084_signed_trade_qty",
                    "rest_signed_tape_received_at": now_ts,
                    "source_timestamp": now_ts,
                },
                {
                    "signed_trade_volume": "-80",
                    "aggressor_side": "SELL",
                    "aggressor_source": "kiwoom_rest_ka10084_signed_trade_qty",
                    "rest_signed_tape_received_at": now_ts,
                    "source_timestamp": now_ts - 0.1,
                },
                {
                    "signed_trade_volume": "-20",
                    "aggressor_side": "SELL",
                    "aggressor_source": "kiwoom_rest_ka10084_signed_trade_qty",
                    "rest_signed_tape_received_at": now_ts,
                    "source_timestamp": now_ts - 0.2,
                },
            ]
        },
    )

    assert fields["latency_true_ofi_direct_canary_signed_tape_sample_count"] == 3
    assert fields["latency_true_ofi_direct_canary_signed_tape_buy_count"] == 1
    assert fields["latency_true_ofi_direct_canary_signed_tape_buy_volume"] == 120
    assert fields["latency_true_ofi_direct_canary_signed_tape_sell_dominated"] is False


def test_rest_signed_tape_stale_sell_rows_cannot_block_latency_canary():
    now_ts = time.time()
    fields = entry_latency_module._latency_signed_tape_fields(
        {},
        {
            "rest_signed_trade_ticks": [
                {
                    "signed_trade_volume": "-200",
                    "rest_signed_tape_source": "ka10084",
                    "rest_signed_tape_received_at": now_ts - 10.0,
                    "source_timestamp": now_ts - 10.0,
                },
                {
                    "signed_trade_volume": "-150",
                    "rest_signed_tape_source": "ka10084",
                    "rest_signed_tape_received_at": now_ts - 10.0,
                    "source_timestamp": now_ts - 9.9,
                },
                {
                    "signed_trade_volume": "-100",
                    "rest_signed_tape_source": "ka10084",
                    "rest_signed_tape_received_at": now_ts - 10.0,
                    "source_timestamp": now_ts - 9.8,
                },
            ]
        },
    )

    assert fields["latency_true_ofi_direct_canary_signed_tape_sample_count"] == 0
    assert fields["latency_true_ofi_direct_canary_signed_tape_sell_dominated"] is False
    assert (
        fields["latency_true_ofi_direct_canary_signed_tape_rest_stale_or_unknown_count"]
        == 3
    )


def test_latency_true_ofi_direct_canary_keeps_wide_spread_blocked(monkeypatch):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": -0.016,
                "true_ofi_sample_count": 120,
                "last_ws_ts": now_ts - 0.05,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "7.87",
        },
        code="123456_true_ofi_direct_canary_wide",
        ws_data={
            "curr": 8_920,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 9_020, "volume": 100}],
                "bids": [{"price": 8_920, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=8_900,
        signal_strength=0.70,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_false_negative_remeasure_enqueued"] is False
    assert (
        result["latency_false_negative_remeasure_reason"]
        == "spread_bps_above_remeasure_cap"
    )
    assert result["latency_true_ofi_direct_canary_applied"] is False
    assert (
        result["latency_true_ofi_direct_canary_reason"]
        == "spread_bps_above_direct_canary_cap"
    )


def test_latency_true_ofi_direct_canary_reports_stale_true_ofi_source_before_value(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("OTHER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.21,
                "true_ofi_sample_count": 120,
                "last_ws_ts": now_ts - 1.5,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_lineage": True,
            "source_signature": "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
            "price_delta_since_first_seen_pct": "7.63",
        },
        code="123456_true_ofi_direct_canary_stale_source",
        ws_data={
            "curr": 3_680,
            "last_ws_update_ts": now_ts,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "buy_pressure_10t": 83.0,
            "buy_exec_volume": 830,
            "sell_exec_volume": 170,
            "net_buy_exec_volume": 660,
            "orderbook": {
                "asks": [{"price": 3_700, "volume": 100}],
                "bids": [{"price": 3_680, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=3_680,
        signal_strength=0.70,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_true_ofi_direct_canary_applied"] is False
    assert (
        result["latency_true_ofi_direct_canary_derived_reason"]
        == "not_true_ofi_below_floor"
    )
    assert (
        result["latency_true_ofi_direct_canary_reason"]
        == "ws_age_above_direct_canary_cap"
    )
    assert (
        result["latency_true_ofi_direct_canary_ws_age_ms"]
        > result["latency_true_ofi_direct_canary_max_ws_age_ms"]
    )


def test_latency_true_ofi_direct_canary_is_off_without_dated_runtime(monkeypatch):
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ENABLED", raising=False
    )
    monkeypatch.delenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ACTIVE_DATE", raising=False
    )

    state = entry_latency_module._latency_true_ofi_direct_canary_runtime_state()

    assert state["configured_enabled"] is False
    assert state["active"] is False
    assert entry_latency_module._latency_true_ofi_direct_canary_enabled() is False


def test_latency_true_ofi_direct_canary_requires_tp1_micro_recheck_before_allow(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    now_ts = time.time()
    base_stock = {
        "rising_missed_entry_lineage": True,
        "price_delta_since_first_seen_pct": "4.20",
        "rising_missed_tp1_top_depth_ratio": 1.02,
        "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
        "rising_missed_tp1_counterfactual_risks": [
            "true_ofi_nonpositive",
            "depth_support_weak",
        ],
    }
    ws_data = {
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 10,
        "buy_pressure_10t": 68.0,
        "buy_exec_volume": 680,
        "sell_exec_volume": 320,
        "net_buy_exec_volume": 360,
        "orderbook": {
            "asks": [{"price": 10_060, "volume": 100}],
            "bids": [{"price": 10_000, "volume": 102}],
        },
    }
    kwargs = {
        "ws_data": ws_data,
        "strategy_id": "SCALPING",
        "policy_decision": entry_latency_module.EntryDecision.REJECT_DANGER,
        "effective_decision": entry_latency_module.EntryDecision.REJECT_DANGER,
        "latency_status": SimpleNamespace(quote_stale=False),
        "danger_reasons": ["spread_above_caution"],
        "spread_bps": 60.0,
        "signal_score": 75.0,
        "micro_estimator_reason": "true_ofi_below_floor",
        "estimator_context": {
            "latency_false_negative_remeasure_true_ofi_ewma": 0.041,
            "latency_false_negative_remeasure_true_ofi_sample_count": 120,
            "latency_false_negative_remeasure_ws_age_ms": 40.0,
            "latency_false_negative_remeasure_source_state": "fresh_ws_order_flow_delta",
        },
        "danger_relief_forbidden": False,
    }

    first = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=base_stock,
        **kwargs,
    )

    assert first["latency_true_ofi_direct_canary_applied"] is False
    assert first["latency_true_ofi_direct_canary_recheck_state"] == "arm_required"
    assert first["latency_true_ofi_direct_canary_reason"] == "tp1_recheck_arm_required"

    recovered_stock = {
        **base_stock,
        "latency_true_ofi_direct_canary_recheck_armed": True,
        "latency_true_ofi_direct_canary_recheck_started_at": now_ts - 2.5,
    }
    recovered = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=recovered_stock,
        **kwargs,
    )

    assert recovered["latency_true_ofi_direct_canary_applied"] is True
    assert recovered["latency_true_ofi_direct_canary_recheck_state"] == "recovered"
    assert recovered[
        "latency_true_ofi_direct_canary_recheck_top_depth_ratio_source"
    ] == ("ws.orderbook.top_bid_over_ask")
    assert recovered["latency_true_ofi_direct_canary_reason"] == (
        "direct_canary_tp1_recheck_recovered_allow"
    )

    rest_replaced = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=recovered_stock,
        **{
            **kwargs,
            "ws_data": {
                **ws_data,
                "quote_refresh_source": "ka10004_rest_orderbook",
                "pre_submit_rest_orderbook_refresh_applied": True,
            },
        },
    )

    assert rest_replaced["latency_true_ofi_direct_canary_applied"] is False
    assert rest_replaced[
        "latency_true_ofi_direct_canary_recheck_top_depth_ratio_source"
    ] == ("rest.orderbook.top_bid_over_ask")
    assert rest_replaced["latency_true_ofi_direct_canary_reason"] == (
        "tp1_recheck_positive_micro_not_recovered"
    )


def test_latency_true_ofi_direct_canary_rechecks_submit_time_deterioration(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        datetime.now(entry_latency_module._KST).strftime("%Y-%m-%d"),
    )
    stock = {
        "rising_missed_entry_lineage": True,
        "rising_missed_tp1_submit_context_fresh": True,
        "rising_missed_tp1_submit_context_true_ofi_ewma": 0.0278,
        "rising_missed_tp1_submit_context_spread_ratio": 0.00437,
        "price_delta_since_first_seen_pct": "2.77",
    }
    ws_data = {
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 10,
        "buy_pressure_10t": 68.0,
        "buy_exec_volume": 680,
        "sell_exec_volume": 320,
        "net_buy_exec_volume": 360,
        "orderbook": {
            "asks": [{"price": 13_790, "volume": 100}],
            "bids": [{"price": 13_710, "volume": 120}],
        },
    }

    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=stock,
        ws_data=ws_data,
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_above_caution_below_guard_cap"],
        spread_bps=58.2,
        signal_score=70.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": -0.0734,
            "latency_false_negative_remeasure_true_ofi_sample_count": 144,
            "latency_false_negative_remeasure_ws_age_ms": 23.0,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is False
    assert fields["latency_true_ofi_direct_canary_recheck_required"] is True
    assert fields["latency_true_ofi_direct_canary_recheck_state"] == "arm_required"
    assert fields["latency_true_ofi_direct_canary_reason"] == "tp1_recheck_arm_required"
    assert fields["latency_true_ofi_direct_canary_submit_deterioration_reasons"] == (
        "true_ofi_turned_negative,spread_worsened"
    )


def test_latency_true_ofi_direct_canary_keeps_pass_without_submit_deterioration(
    monkeypatch,
):
    _enable_latency_true_ofi_direct_canary(monkeypatch)
    stock = {
        "rising_missed_entry_lineage": True,
        "rising_missed_tp1_submit_context_fresh": True,
        "rising_missed_tp1_submit_context_true_ofi_ewma": 0.0278,
        "rising_missed_tp1_submit_context_spread_ratio": 0.00437,
        "price_delta_since_first_seen_pct": "3.20",
    }
    ws_data = {
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 10,
        "buy_pressure_10t": 68.0,
        "buy_exec_volume": 680,
        "sell_exec_volume": 320,
        "net_buy_exec_volume": 360,
    }

    fields = entry_latency_module._latency_true_ofi_direct_canary_fields(
        stock=stock,
        ws_data=ws_data,
        strategy_id="SCALPING",
        policy_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        effective_decision=entry_latency_module.EntryDecision.REJECT_DANGER,
        latency_status=SimpleNamespace(quote_stale=False),
        danger_reasons=["spread_above_caution_below_guard_cap"],
        spread_bps=47.0,
        signal_score=70.0,
        micro_estimator_reason="true_ofi_below_floor",
        estimator_context={
            "latency_false_negative_remeasure_true_ofi_ewma": 0.01,
            "latency_false_negative_remeasure_true_ofi_sample_count": 144,
            "latency_false_negative_remeasure_ws_age_ms": 23.0,
            "latency_false_negative_remeasure_source_state": (
                "fresh_ws_order_flow_delta"
            ),
        },
        danger_relief_forbidden=False,
    )

    assert fields["latency_true_ofi_direct_canary_applied"] is True
    assert fields["latency_true_ofi_direct_canary_recheck_required"] is False
    assert fields["latency_true_ofi_direct_canary_submit_deterioration_reasons"] == "-"


def test_latency_false_negative_remeasure_preserves_explicit_ai_wait(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.91,
                "true_ofi_ewma": 0.03,
                "true_ofi_sample_count": 140,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_ai_action": "WAIT",
            "latency_false_negative_report_canary_grade": "ready_for_recheck",
            "latency_false_negative_report_canary_cohort": "true_ofi_near_zero_false_negative",
        },
        code="123456_false_negative_remeasure_wait",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_false_negative_remeasure_enqueued"] is False
    assert result["latency_false_negative_remeasure_reason"] == "explicit_ai_wait_veto"


def test_latency_spread_relief_true_ofi_estimator_does_not_relax_hard_floors_from_env(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_CONFIDENCE", "0.1"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_TRUE_OFI_SAMPLES",
        "2",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_TRUE_OFI", "-0.5"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_PRESSURE", "50"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_TOP_DEPTH_RATIO",
        "1.0",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MAX_WS_AGE_MS",
        "99999",
    )
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.20,
                "true_ofi_ewma": 0.10,
                "pressure_ewma": 55.0,
                "top_depth_ratio": 1.00,
                "true_ofi_sample_count": 2,
                "last_ws_ts": now_ts - 1.0,
            }
        ),
    )

    result = entry_latency_module._latency_micro_estimator_relief_signal_candidate(
        "123456_true_ofi_hard_floor",
        position_tag="SCANNER",
    )

    assert result["latency_spread_relief_micro_estimator_eligible"] is False
    assert (
        result["latency_spread_relief_micro_estimator_reason"]
        == "ws_state_stale_or_missing"
    )
    assert result["latency_spread_relief_micro_estimator_min_confidence"] == 0.70
    assert result["latency_spread_relief_micro_estimator_min_true_ofi_samples"] == 8
    assert result["latency_spread_relief_micro_estimator_min_true_ofi"] == 0.20
    assert result["latency_spread_relief_micro_estimator_min_pressure"] == 65.0
    assert result["latency_spread_relief_micro_estimator_min_top_depth_ratio"] == 1.05
    assert result["latency_spread_relief_micro_estimator_max_ws_age_ms"] == 700.0


def test_latency_spread_relief_true_ofi_estimator_covers_all_scalping_tags(monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ALL_SCALPING_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_TAGS", "SCANNER"
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.90,
                "true_ofi_ewma": 0.50,
                "pressure_ewma": 75.0,
                "top_depth_ratio": 1.25,
                "true_ofi_sample_count": 12,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "MIDDLE"},
        code="123456_true_ofi_all_scalping_scope",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook_micro_ready": False,
            "orderbook_micro_reason": "insufficient_samples",
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert (
        result["latency_spread_relief_signal_score_source"]
        == "micro_estimator.true_ofi_ewma"
    )
    assert result["latency_spread_relief_micro_estimator_eligible"] is True
    assert result["latency_spread_relief_micro_estimator_all_scalping_enabled"] is True


def test_latency_spread_relief_true_ofi_estimator_keeps_non_allowlisted_tag_blocked_when_scope_off(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ALL_SCALPING_ENABLED",
        "false",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_TAGS", "SCANNER"
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.90,
                "true_ofi_ewma": 0.50,
                "pressure_ewma": 75.0,
                "top_depth_ratio": 1.25,
                "true_ofi_sample_count": 12,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "MIDDLE"},
        code="123456_true_ofi_tag_scope_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_spread_relief_micro_estimator_eligible"] is False
    assert result["latency_spread_relief_micro_estimator_reason"] == "tag_not_allowed"
    assert result["latency_spread_relief_signal_score_source"] == "missing"


def test_latency_spread_relief_true_ofi_estimator_fail_closes_invalid_snapshot(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ALL_SCALPING_ENABLED",
        "true",
    )
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(snapshot=lambda code, *, now_ts: None),
    )

    result = entry_latency_module._latency_micro_estimator_relief_signal_candidate(
        "123456_true_ofi_invalid_snapshot",
        position_tag="MIDDLE",
    )

    assert result["latency_spread_relief_micro_estimator_eligible"] is False
    assert (
        result["latency_spread_relief_micro_estimator_reason"] == "snapshot_unavailable"
    )


def test_latency_spread_relief_preserves_explicit_ai_wait_even_with_true_ofi_support(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED", "true"
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=80.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=False,
        ),
    )
    now_ts = time.time()
    monkeypatch.setattr(
        entry_latency_module,
        "MICRO_ESTIMATOR_STORE",
        SimpleNamespace(
            snapshot=lambda code, *, now_ts: {
                "source_state": "fresh_ws_order_flow_delta",
                "confidence": 0.90,
                "true_ofi_ewma": 0.50,
                "pressure_ewma": 75.0,
                "top_depth_ratio": 1.25,
                "true_ofi_sample_count": 12,
                "last_ws_ts": now_ts,
            }
        ),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "TEST",
            "position_tag": "SCANNER",
            "rising_missed_entry_ai_action": "WAIT",
        },
        code="123456_true_ofi_estimator_wait_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": now_ts,
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_spread_relief_signal_score"] == 0.0
    assert (
        result["latency_spread_relief_signal_source_quality_state"]
        == "explicit_negative_ai"
    )
    assert result["latency_spread_relief_explicit_negative_ai_action"] == "WAIT"


def test_latency_spread_relief_true_ofi_provenance_is_forwarded_to_pipeline_events():
    fields = state_handlers._latency_spread_relief_micro_estimator_log_fields(
        {
            "latency_spread_relief_micro_estimator_enabled": True,
            "latency_spread_relief_micro_estimator_eligible": True,
            "latency_spread_relief_micro_estimator_reason": "fresh_true_ofi_support",
            "latency_spread_relief_micro_estimator_true_ofi_ewma": 0.42,
            "latency_spread_relief_micro_estimator_true_ofi_sample_count": 12,
            "latency_spread_relief_micro_estimator_all_scalping_enabled": True,
            "latency_spread_relief_micro_estimator_metric_role": "source_quality_gate",
            "latency_spread_relief_micro_estimator_decision_authority": (
                "supplemental_signal_for_existing_latency_spread_relief_canary"
            ),
        }
    )

    assert fields["latency_spread_relief_micro_estimator_enabled"] is True
    assert fields["latency_spread_relief_micro_estimator_eligible"] is True
    assert (
        fields["latency_spread_relief_micro_estimator_reason"]
        == "fresh_true_ofi_support"
    )
    assert fields["latency_spread_relief_micro_estimator_true_ofi_ewma"] == 0.42
    assert fields["latency_spread_relief_micro_estimator_true_ofi_sample_count"] == 12
    assert fields["latency_spread_relief_micro_estimator_all_scalping_enabled"] is True
    assert (
        fields["latency_spread_relief_micro_estimator_metric_role"]
        == "source_quality_gate"
    )
    assert (
        fields["latency_spread_relief_micro_estimator_score"]
        == "not_evaluated_pre_contract"
    )

    remeasure_fields = state_handlers._latency_false_negative_remeasure_log_fields(
        {
            "latency_false_negative_remeasure_enqueued": True,
            "latency_false_negative_remeasure_candidate_source": "intraday_feedback_report",
            "latency_false_negative_remeasure_grade": "ready_for_recheck",
            "latency_false_negative_remeasure_reason": "true_ofi_near_zero_or_positive_with_fresh_ws",
            "latency_false_negative_remeasure_repass_attempted": True,
            "latency_false_negative_remeasure_repass_decision": "REJECT_DANGER",
            "latency_true_ofi_direct_canary_applied": True,
            "latency_true_ofi_direct_canary_reason": "direct_canary_true_ofi_false_negative_allow",
            "latency_true_ofi_direct_canary_relief_runtime_enabled": True,
            "latency_true_ofi_direct_canary_true_ofi_ewma": 0.012,
        }
    )
    assert remeasure_fields["latency_false_negative_remeasure_enqueued"] is True
    assert (
        remeasure_fields["latency_false_negative_remeasure_candidate_source"]
        == "intraday_feedback_report"
    )
    assert (
        remeasure_fields["latency_false_negative_remeasure_grade"]
        == "ready_for_recheck"
    )
    assert (
        remeasure_fields["latency_false_negative_remeasure_reason"]
        == "true_ofi_near_zero_or_positive_with_fresh_ws"
    )
    assert remeasure_fields["latency_false_negative_remeasure_repass_attempted"] is True
    assert (
        remeasure_fields["latency_false_negative_remeasure_repass_decision"]
        == "REJECT_DANGER"
    )
    assert remeasure_fields["latency_true_ofi_direct_canary_applied"] is True
    assert (
        remeasure_fields["latency_true_ofi_direct_canary_reason"]
        == "direct_canary_true_ofi_false_negative_allow"
    )
    assert (
        remeasure_fields["latency_true_ofi_direct_canary_relief_runtime_enabled"]
        is True
    )
    assert remeasure_fields["latency_true_ofi_direct_canary_true_ofi_ewma"] == 0.012


def test_latency_wide_spread_passive_requote_allows_scanner_target_price(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=85.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=True,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_TAGS=("SCANNER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_SIGNAL_SCORE=78.0,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_BUY_PRESSURE=78.0,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MAX_SPREAD_RATIO=0.0130,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_OFI_NORM=0.0,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
        ),
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "290690_passive_requote",
        best_bid=5_440,
        best_ask=5_500,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "SORUX", "position_tag": "SCANNER"},
        code="290690_passive_requote",
        ws_data={
            "curr": 5_460,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "buy_ratio": 83.0,
            "ofi_norm": 1.249,
            "orderbook": {
                "asks": [{"price": 5_500, "volume": 100}],
                "bids": [{"price": 5_440, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=5_460,
        signal_strength=78.0,
        target_buy_price=5_410,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_wide_spread_passive_requote_normal_override"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "wide_spread_passive_requote_applied"
    assert result["latency_wide_spread_passive_requote_applied"] is True
    assert (
        result["entry_price_guard"] == "latency_wide_spread_passive_requote_defensive"
    )
    assert result["price_resolution_reason"] == "reference_target_cap"
    assert result["order_price"] == 5_410
    assert result["latency_danger_reasons"] == "spread_too_wide"


def test_latency_wide_spread_passive_requote_blocks_low_buy_pressure(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED=True,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_TAGS=("SCANNER",),
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_SIGNAL_SCORE=78.0,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_BUY_PRESSURE=78.0,
            SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MAX_SPREAD_RATIO=0.0130,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_passive_requote_low_pressure",
        ws_data={
            "curr": 5_460,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "buy_ratio": 55.0,
            "orderbook": {
                "asks": [{"price": 5_500, "volume": 100}],
                "bids": [{"price": 5_440, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=5_460,
        signal_strength=78.0,
        target_buy_price=5_410,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_wide_spread_passive_requote_applied"] is False
    assert result["latency_wide_spread_passive_requote_reason"] == "low_buy_pressure"
    assert result["latency_danger_reasons"] == "spread_too_wide"


def test_latency_buy_pressure_prefers_trusted_ten_tick_pressure_over_provider_ratio():
    assert (
        entry_latency_module._latency_buy_pressure_value(
            {
                "buy_ratio": 83.0,
                "buy_pressure_10t": 21.0,
                "tick_aggressor_pressure_usable": True,
                "tick_aggressor_trusted_count": 3,
            },
            {"buy_pressure_10t": 20.0, "tick_aggressor_pressure_usable": False},
        )
        == 21.0
    )
    assert (
        entry_latency_module._latency_buy_pressure_value(
            {"buy_ratio": 83.0, "tick_aggressor_pressure_usable": False},
            {"buy_pressure_10t": 20.0, "tick_aggressor_pressure_usable": False},
        )
        == 83.0
    )


def test_latency_buy_pressure_blocks_untrusted_derived_fallback():
    assert (
        entry_latency_module._latency_buy_pressure_value(
            {},
            {
                "buy_pressure_10t": 90.0,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            },
        )
        == 0.0
    )
    assert (
        entry_latency_module._latency_buy_pressure_value(
            {},
            {
                "buy_pressure_10t": 90.0,
                "tick_aggressor_pressure_usable": True,
                "tick_aggressor_trusted_count": 1,
            },
        )
        == 90.0
    )


def test_latency_spread_relief_canary_uses_effective_min_signal_floor_override(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=60.0,
            SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR=75.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0150,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_relief_floor_override",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=78.0,
    )

    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_spread_relief_normal_override"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "spread_relief_canary_applied"
    assert result["latency_spread_relief_signal_score"] == 78.0
    assert result["latency_spread_relief_configured_min_signal_score"] == 60.0
    assert result["latency_spread_relief_effective_min_signal_score"] == 75.0


def test_latency_spread_relief_canary_requires_spread_only_danger(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0120,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_spread_relief_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": time.time() - 0.5,
            "orderbook": {
                "asks": [{"price": 10_130, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "spread_only_required"
    assert "ws_age_too_high" in result["latency_danger_reasons"]
    assert "spread_too_wide" in result["latency_danger_reasons"]


def test_latency_spread_relief_canary_blocks_unstable_quote(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0130,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=True,
            SCALP_LATENCY_SPREAD_RELIEF_MIN_PRINT_QUOTE_ALIGNMENT=0.90,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code: {
            "unstable_quote_observed": True,
            "unstable_reasons": "print_quote_alignment",
            "print_quote_alignment": 0.82716,
        },
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_relief_unstable_quote",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_140, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "unstable_quote_observed"
    assert result["latency_danger_reasons"] == "spread_too_wide"


def test_latency_spread_relief_canary_blocks_low_print_quote_alignment(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=0.0130,
            SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE=True,
            SCALP_LATENCY_SPREAD_RELIEF_MIN_PRINT_QUOTE_ALIGNMENT=0.90,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code: {
            "unstable_quote_observed": False,
            "print_quote_alignment": 0.82716,
        },
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_spread_relief_low_print_alignment",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_140, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "print_quote_alignment_too_low"
    assert result["latency_danger_reasons"] == "spread_too_wide"


def test_latency_ws_jitter_relief_canary_overrides_reject_danger_to_normal(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_WS_JITTER_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_JITTER_MS=360,
            SCALP_LATENCY_WS_JITTER_RELIEF_MAX_SPREAD_RATIO=0.0050,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=120,
            ws_jitter_ms=320,
            quote_stale=False,
            spread_ratio=0.001,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_ws_jitter_relief_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(result, danger_reasons="ws_jitter_too_high")


def test_latency_ws_jitter_relief_canary_requires_jitter_only_danger(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_WS_JITTER_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_JITTER_MS=360,
            SCALP_LATENCY_WS_JITTER_RELIEF_MAX_SPREAD_RATIO=0.0050,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=720,
            ws_jitter_ms=320,
            quote_stale=False,
            spread_ratio=0.001,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_ws_jitter_relief_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons=("ws_age_too_high", "ws_jitter_too_high"),
    )
    assert "ws_age_too_high" in result["latency_danger_reasons"]
    assert "ws_jitter_too_high" in result["latency_danger_reasons"]


def test_latency_other_danger_relief_canary_overrides_reject_danger_to_normal(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_AGE_MS=400,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_JITTER_MS=80,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_SPREAD_RATIO=0.0080,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_latency_danger_reasons",
        lambda latency: ["other_danger"],
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=220,
            ws_jitter_ms=0,
            quote_stale=False,
            spread_ratio=0.0072,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_other_danger_relief_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=85.0,
    )

    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_other_danger_relief_normal_override"
    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "other_danger_relief_canary_applied"
    assert result["latency_danger_reasons"] == "other_danger"


def test_latency_other_danger_relief_canary_enforces_stricter_residual_limits(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_AGE_MS=400,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_JITTER_MS=80,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_SPREAD_RATIO=0.0080,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_latency_danger_reasons",
        lambda latency: ["other_danger"],
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=220,
            ws_jitter_ms=120,
            quote_stale=False,
            spread_ratio=0.0072,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_other_danger_relief_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=92.0,
    )

    assert result["allowed"] is False
    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "ws_jitter_limit_exceeded"
    assert result["latency_danger_reasons"] == "other_danger"


def test_latency_other_danger_relief_canary_blocks_below_85_signal(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_AGE_MS=400,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_JITTER_MS=80,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_SPREAD_RATIO=0.0080,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_latency_danger_reasons",
        lambda latency: ["other_danger"],
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=220,
            ws_jitter_ms=0,
            quote_stale=False,
            spread_ratio=0.0072,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_other_danger_relief_low_signal",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=84.9,
    )

    assert result["allowed"] is False
    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "low_signal"
    assert result["latency_danger_reasons"] == "other_danger"


def test_latency_other_danger_relief_canary_blocks_unstable_quote(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE=74.0,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_AGE_MS=400,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_JITTER_MS=80,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_SPREAD_RATIO=0.0100,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_BLOCK_UNSTABLE_QUOTE=True,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module,
        "_latency_danger_reasons",
        lambda latency: ["other_danger"],
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=220,
            ws_jitter_ms=0,
            quote_stale=False,
            spread_ratio=0.0092,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code: {
            "unstable_quote_observed": True,
            "unstable_reasons": "quote_age_p90",
            "print_quote_alignment": 1.0,
        },
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_other_danger_unstable_quote",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=74.0,
    )

    assert result["allowed"] is False
    assert result["decision"] == "REJECT_DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "unstable_quote_observed"
    assert result["latency_danger_reasons"] == "other_danger"


def test_latency_quote_fresh_composite_canary_overrides_mixed_danger_to_normal(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_TAGS=("SCANNER",),
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MIN_SIGNAL_SCORE=88.0,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_AGE_MS=950,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_JITTER_MS=450,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_SPREAD_RATIO=0.0075,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=820,
            ws_jitter_ms=380,
            quote_stale=False,
            spread_ratio=0.0062,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_quote_fresh_composite_pass",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=88.0,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_age_too_high,ws_jitter_too_high",
    )


def test_latency_quote_fresh_composite_price_guard_respects_target_buy_price(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_TAGS=("SCANNER",),
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MIN_SIGNAL_SCORE=88.0,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_AGE_MS=950,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_JITTER_MS=450,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_SPREAD_RATIO=0.0075,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=820,
            ws_jitter_ms=380,
            quote_stale=False,
            spread_ratio=0.0062,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_quote_fresh_target_cap",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=88.0,
        target_buy_price=9_980,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_age_too_high,ws_jitter_too_high",
    )


def test_scalping_target_buy_price_can_override_defensive_order_price_for_daehan_cable():
    result = evaluate_live_buy_entry(
        stock={"name": "대한전선", "position_tag": "SCANNER"},
        code="001440_daehan_cable_target_cap",
        ws_data={
            "curr": 50_500,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 50_900, "volume": 100}],
                "bids": [{"price": 50_500, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=5,
        signal_price=50_500,
        signal_strength=90.0,
        target_buy_price=48_800,
    )

    assert result["allowed"] is False
    assert result["decision"] == "REJECT_DANGER"

    result = evaluate_live_buy_entry(
        stock={"name": "대한전선", "position_tag": "SCANNER"},
        code="001440_daehan_cable_target_cap_tight_spread",
        ws_data={
            "curr": 50_500,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 50_600, "volume": 100}],
                "bids": [{"price": 50_500, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=5,
        signal_price=50_500,
        signal_strength=90.0,
        target_buy_price=48_800,
    )

    assert result["allowed"] is True
    assert result["normal_defensive_order_price"] == 50_400
    assert result["latency_guarded_order_price"] == 50_400
    assert result["target_buy_price"] == 48_800
    assert result["counterfactual_order_price_1tick"] == 48_800
    assert result["order_price"] == 50_400
    assert result["price_resolution_reason"] == "scalping_reference_rejected_defensive"
    assert result["reference_target_applied"] is False
    assert result["reference_target_rejected_reason"] == "target_below_bid_bps_exceeded"
    assert result["reference_target_below_bid_bps"] == 337


def test_latency_quote_fresh_composite_price_guard_uses_valid_tick_at_price_boundary(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_TAGS=("SCANNER",),
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MIN_SIGNAL_SCORE=88.0,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_AGE_MS=950,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_JITTER_MS=450,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_SPREAD_RATIO=0.0075,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=820,
            ws_jitter_ms=380,
            quote_stale=False,
            spread_ratio=0.0062,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "TEST", "position_tag": "SCANNER"},
        code="123456_quote_fresh_boundary",
        ws_data={
            "curr": 200_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 200_500, "volume": 100}],
                "bids": [{"price": 200_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=200_000,
        signal_strength=88.0,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_age_too_high,ws_jitter_too_high",
    )


def test_latency_quote_fresh_composite_canary_blocks_below_88_signal(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_TAGS=("SCANNER",),
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MIN_SIGNAL_SCORE=88.0,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_AGE_MS=950,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_JITTER_MS=450,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_SPREAD_RATIO=0.0075,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=820,
            ws_jitter_ms=380,
            quote_stale=False,
            spread_ratio=0.0062,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_quote_fresh_composite_low_signal",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=87.9,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_age_too_high,ws_jitter_too_high",
    )


def test_latency_signal_quality_quote_composite_backup_canary_overrides_to_normal(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_TAGS=("SCANNER",),
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_SIGNAL_SCORE=90.0,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_STRENGTH=110.0,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_BUY_PRESSURE=65.0,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_WS_AGE_MS=1200,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_WS_JITTER_MS=500,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_SPREAD_RATIO=0.0085,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=1040,
            ws_jitter_ms=470,
            quote_stale=False,
            spread_ratio=0.0080,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_signal_quality_quote_pass",
        ws_data={
            "curr": 10_020,
            "v_pw": 112.0,
            "buy_ratio": 68.0,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_age_too_high,ws_jitter_too_high",
    )


def test_latency_signal_quality_quote_composite_backup_blocks_weak_buy_pressure(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_TAGS=("SCANNER",),
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_SIGNAL_SCORE=90.0,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_STRENGTH=110.0,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_BUY_PRESSURE=65.0,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=1040,
            ws_jitter_ms=470,
            quote_stale=False,
            spread_ratio=0.0080,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_signal_quality_quote_low_pressure",
        ws_data={
            "curr": 10_020,
            "v_pw": 112.0,
            "buy_ratio": 64.9,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_age_too_high,ws_jitter_too_high",
    )


def test_latency_mechanical_momentum_relief_overrides_low_ai_score_quote_family(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE=75.0,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH=110.0,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE=50.0,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS=1200,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS=500,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO=0.0085,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=204,
            ws_jitter_ms=383,
            quote_stale=False,
            spread_ratio=0.0080,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_mechanical_momentum_quote_pass",
        ws_data={
            "curr": 10_020,
            "v_pw": 119.0,
            "buy_ratio": 54.2,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.50,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_jitter_too_high",
    )


def test_latency_mechanical_momentum_relief_blocks_high_ai_score_to_avoid_axis_overlap(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=True,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS=("SCANNER",),
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE=75.0,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH=110.0,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE=50.0,
        ),
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE, "update", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        entry_latency_module._CACHE,
        "get_quote_health",
        lambda code: SimpleNamespace(
            ws_age_ms=204,
            ws_jitter_ms=383,
            quote_stale=False,
            spread_ratio=0.0080,
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_mechanical_momentum_high_ai_block",
        ws_data={
            "curr": 10_020,
            "v_pw": 119.0,
            "buy_ratio": 54.2,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_030, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=0.90,
    )

    _assert_danger_hard_safety_block(
        result,
        danger_reasons="ws_jitter_too_high",
    )


def test_latency_danger_reasons_are_allowlist_controllable(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_ENABLED=True,
            SCALP_LATENCY_FALLBACK_ENABLED=True,
            SCALP_LATENCY_GUARD_CANARY_TAGS=("SCANNER",),
            SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE=85.0,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=300,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=0.0040,
            SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS=("ws_jitter_too_high",),
        ),
    )

    stock = {"name": "TEST", "position_tag": "SCANNER"}
    result = evaluate_live_buy_entry(
        stock=stock,
        code="123456_canary_reason_block",
        ws_data={
            "curr": 10_020,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_080, "volume": 100}],
                "bids": [{"price": 10_020, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=2,
        signal_price=10_000,
        signal_strength=90.0,
    )

    _assert_danger_hard_safety_block(result, danger_reasons=("spread_too_wide",))
    assert "spread_too_wide" in result["latency_danger_reasons"]


def test_latency_danger_reason_helper_uses_thresholds(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS=450,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=300,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=0.0100,
            SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False,
        ),
    )

    status = type(
        "LatencyStatusStub",
        (),
        {
            "quote_stale": False,
            "ws_age_ms": 451,
            "ws_jitter_ms": 301,
            "spread_ratio": 0.011,
        },
    )()
    assert _latency_danger_reasons(status) == [
        "ws_age_too_high",
        "ws_jitter_too_high",
        "spread_too_wide",
    ]


def test_percent_bps_mode_normal_defensive_0025_pct(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps1",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_bps1",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["entry_price_defense_mode"] == "percent_bps"
    assert result["entry_price_defensive_bps"] == 25
    assert result["entry_price_gap_profile"] == "normal"
    assert result["entry_price_gap_profile_bps"] == 25
    assert result["order_price"] == 9970


def test_percent_bps_mode_strong_defensive_001_pct(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps2",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_bps2",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 5000}],
            },
            "volume_data_tick2": {"buy": 150, "sell": 50},
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["entry_price_defense_mode"] == "percent_bps"
    assert result["entry_price_defensive_bps"] == 10
    assert result["entry_price_gap_profile"] == "strong_1tick_pressure"
    assert result["entry_price_gap_profile_bps"] == 10
    assert result["conditional_1tick_real_override_applied"] is True
    assert (
        result["conditional_1tick_real_override_reason"]
        == "spread_1tick_strong_buy_pressure_percent_bps"
    )
    assert result["order_price"] == 9990


def test_percent_bps_mode_favorable_micro_0015_pct(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps_favorable",
        best_bid=10_000,
        best_ask=10_020,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_bps_favorable",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["entry_price_guard"] == "favorable_micro_percent_bps"
    assert result["entry_price_defensive_bps"] == 15
    assert result["entry_price_gap_profile"] == "favorable_micro"
    assert result["entry_price_gap_profile_bps"] == 15
    assert result["conditional_1tick_real_override_applied"] is False
    assert result["order_price"] == 9980


def test_percent_bps_mode_weak_liquidity_wide_spread_0040_pct(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps_weak",
        best_bid=10_000,
        best_ask=10_050,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_bps_weak",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_050, "volume": 5000}],
                "bids": [{"price": 10_000, "volume": 500}],
            },
            "buy_exec_volume": 20,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": -60,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["entry_price_guard"] == "weak_liquidity_wide_spread_percent_bps"
    assert result["entry_price_defensive_bps"] == 40
    assert result["entry_price_gap_profile"] == "weak_liquidity_wide_spread"
    assert result["entry_price_gap_profile_bps"] == 40
    assert result["conditional_1tick_real_override_applied"] is False
    assert result["order_price"] == 9960


def test_aggressive_entry_price_override_moves_neutral_defensive_to_bid_minus_tick(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1",
            SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS=15,
            SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS=1,
            SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS=0,
        ),
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_aggressive_neutral",
        best_bid=10_000,
        best_ask=10_050,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_aggressive_neutral",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 10_050, "volume": 5000}],
                "bids": [{"price": 10_000, "volume": 500}],
            },
            "buy_exec_volume": 20,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": -60,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["entry_price_guard"] == "defensive_missed_upside_aggressive_entry"
    assert result["order_price"] == 9990
    assert result["aggressive_entry_price_override_applied"] is True
    assert (
        result["aggressive_entry_price_override_type"] == "defensive_missed_upside_v1"
    )
    assert (
        result["aggressive_entry_price_original_profile"]
        == "weak_liquidity_wide_spread"
    )
    assert result["aggressive_entry_price_original_bps"] == 40
    assert result["aggressive_entry_price_target_mode"] == "best_bid_near"
    assert result["aggressive_entry_price_order_price"] == 9990


def test_aggressive_entry_price_override_moves_positive_micro_to_best_bid(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1",
            SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS=15,
            SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS=1,
            SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS=0,
        ),
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_aggressive_positive",
        best_bid=10_000,
        best_ask=10_020,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_aggressive_positive",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "bullish",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["entry_price_guard"] == "defensive_missed_upside_aggressive_entry"
    assert result["order_price"] == 10000
    assert result["aggressive_entry_price_original_profile"] == "favorable_micro"
    assert result["aggressive_entry_price_original_bps"] == 15


def test_aggressive_entry_price_override_does_not_trust_unproven_exec_volume(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1",
            SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS=15,
            SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS=1,
            SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS=0,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_aggressive_untrusted_pressure",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    context = result["entry_price_gap_profile_context"]
    assert context["tick_aggressor_pressure_usable"] is False
    assert context["buy_pressure_ok"] is False
    assert context["positive_signal_count"] == 0
    assert result["aggressive_entry_price_original_profile"] == "normal"


def test_reference_target_missed_upside_override_moves_positive_micro_to_best_bid(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS=20,
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS=1,
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS=0,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_reference_target_positive",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "bullish",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_900,
    )

    assert (
        result["entry_price_guard"]
        == "reference_target_cap_missed_upside_aggressive_entry"
    )
    assert result["order_price"] == 10000
    assert result["price_resolution_reason"] == "aggressive_entry_price_override"
    assert result["reference_target_applied"] is False
    assert (
        result["reference_target_rejected_reason"]
        == "aggressive_entry_price_override_applied"
    )
    assert result["aggressive_entry_price_override_applied"] is True
    assert (
        result["aggressive_entry_price_override_type"]
        == "reference_target_cap_missed_upside_v1"
    )
    assert (
        result["aggressive_entry_price_override_reason"]
        == "reference_target_cap_missed_upside_best_bid_near"
    )
    context = result["entry_price_gap_profile_context"]
    assert context["reference_target_price"] == 9900
    assert context["reference_target_below_bid_bps"] == 100
    assert context["reference_target_missed_upside_min_bps"] == 20


def test_reference_target_missed_upside_override_moves_neutral_to_bid_minus_tick(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="reference_target_cap_missed_upside_v1",
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS=20,
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS=1,
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS=0,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_reference_target_neutral",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 10_050, "volume": 5000}],
                "bids": [{"price": 10_000, "volume": 500}],
            },
            "buy_exec_volume": 20,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": -60,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_900,
    )

    assert (
        result["entry_price_guard"]
        == "reference_target_cap_missed_upside_aggressive_entry"
    )
    assert result["order_price"] == 9990
    assert (
        result["aggressive_entry_price_override_type"]
        == "reference_target_cap_missed_upside_v1"
    )
    assert result["aggressive_entry_price_target_mode"] == "best_bid_near"


def test_reference_target_missed_upside_override_skips_below_min_bps(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="reference_target_cap_missed_upside_v1",
            SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS=20,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_reference_target_below_min",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "bullish",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_990,
    )

    assert result["entry_price_guard"] == "favorable_micro_percent_bps"
    assert result["order_price"] == 9980
    assert result["aggressive_entry_price_override_applied"] is False
    assert (
        result["aggressive_entry_price_override_skip_reason"]
        == "reference_target_below_bid_bps_below_min"
    )


def test_aggressive_entry_price_override_skips_when_dynamic_resolver_live_selected(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
            DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED=True,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_aggressive_resolver_selected",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "bullish",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_900,
    )

    assert result["entry_price_guard"] == "favorable_micro_percent_bps"
    assert result["order_price"] == 9980
    assert result["aggressive_entry_price_override_applied"] is False
    assert (
        result["aggressive_entry_price_override_skip_reason"]
        == "dynamic_entry_price_resolver_live_selected"
    )


def test_intraday_entry_price_discovery_overrides_dynamic_owner_for_operator(
    monkeypatch,
):
    monkeypatch.setenv("KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED", "true")
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=False,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
            DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED=True,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_intraday_discovery",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "bullish",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_900,
    )

    assert result["allowed"] is True
    assert result["order_price"] == 10_000
    assert result["aggressive_entry_price_override_applied"] is True
    assert result["aggressive_entry_price_operator_intraday_discovery"] is True
    assert result["price_resolution_reason"] == "aggressive_entry_price_override"


def test_aggressive_entry_price_override_skips_when_entry_price_live_tuning_selected(
    monkeypatch,
):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True,
            SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES="defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
            ENTRY_PRICE_LIVE_TUNING_SELECTED=True,
        ),
    )

    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_aggressive_entry_live_owner",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "bullish",
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 1000}],
                "bids": [{"price": 10_000, "volume": 1000}],
            },
            "buy_exec_volume": 120,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": 40,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 2,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_900,
    )

    assert result["entry_price_guard"] == "favorable_micro_percent_bps"
    assert result["order_price"] == 9980
    assert result["aggressive_entry_price_override_applied"] is False
    assert (
        result["aggressive_entry_price_override_skip_reason"]
        == "dynamic_entry_price_resolver_live_selected"
    )


def test_aggressive_entry_price_override_skips_weak_pullback_like_context(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10
    )
    monkeypatch.setattr(
        entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15
    )
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(
        entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True
    )
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED=True),
    )

    result = evaluate_live_buy_entry(
        stock={
            "name": "삼성전자",
            "position_tag": "SCANNER",
            "scalp_pre_ai_gate_context": {
                "strength_momentum": {
                    "risk_state": "weak_momentum_context",
                    "reason": "below_buy_ratio",
                }
            },
        },
        code="005930_aggressive_weak_pullback",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook_micro_state": "neutral",
            "orderbook": {
                "asks": [{"price": 10_050, "volume": 5000}],
                "bids": [{"price": 10_000, "volume": 500}],
            },
            "buy_exec_volume": 20,
            "sell_exec_volume": 80,
            "net_buy_exec_volume": -60,
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["entry_price_guard"] == "weak_liquidity_wide_spread_percent_bps"
    assert result["order_price"] == 9960
    assert result["aggressive_entry_price_override_applied"] is False


def test_percent_bps_mode_non_scalping_stays_tick(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module, "_defense_mode_is_percent_bps", lambda: True
    )

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_swing1",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_swing1",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SWING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result.get("entry_price_defense_mode") == "tick"
    assert result["entry_price_defensive_ticks"] == 1


def test_tick_mode_default_unchanged():
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_tick",
        best_bid=10_000,
        best_ask=10_010,
        ts=time.time(),
    )
    result = evaluate_live_buy_entry(
        stock={"name": "삼성전자", "position_tag": "SCANNER"},
        code="005930_tick",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": datetime.now(UTC).timestamp(),
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
    )

    assert result["allowed"] is True
    assert result["entry_price_defense_mode"] == "tick"
    assert result["entry_price_defensive_ticks"] == 1
    assert result["order_price"] == 9990


def test_p1_initial_phase_preserves_legacy_price_contract():
    resolved = entry_latency_module.resolve_scalping_entry_price(
        strategy_id="SCALPING",
        defensive_order_price=10_000,
        target_buy_price=9_980,
        best_bid=10_000,
    )

    assert resolved["allowed"] is True
    assert resolved["entry_price_resolver_phase"] == "initial"
    assert resolved["resolved_order_price"] == 9_980
    assert resolved["price_resolution_reason"] == "reference_target_cap"


def test_p1_post_probe_profiles_own_residual_prices():
    narrow = entry_latency_module.resolve_scalping_entry_price(
        strategy_id="SCALPING",
        defensive_order_price=83_200,
        target_buy_price=0,
        best_bid=83_100,
        best_ask=83_600,
        phase="post_probe",
        probe_fill_price=83_200,
        fresh_mark_price=83_200,
        continuation_action="ALLOW_NARROW",
        residual_leg_index=1,
    )
    normal = entry_latency_module.resolve_scalping_entry_price(
        strategy_id="SCALPING",
        defensive_order_price=83_200,
        target_buy_price=0,
        best_bid=83_100,
        best_ask=83_600,
        phase="post_probe",
        probe_fill_price=83_200,
        fresh_mark_price=83_200,
        continuation_action="ALLOW_NORMAL",
        residual_leg_index=1,
    )
    recovered = entry_latency_module.resolve_scalping_entry_price(
        strategy_id="SCALPING",
        defensive_order_price=83_200,
        target_buy_price=0,
        best_bid=83_100,
        best_ask=83_600,
        phase="leg_reprice",
        probe_fill_price=83_200,
        fresh_mark_price=83_200,
        continuation_action="ALLOW_RECOVERED_WIDE",
        residual_leg_index=1,
    )

    assert narrow["offset_profile"] == "narrow"
    assert narrow["resolved_order_price"] == 83_100
    assert normal["offset_profile"] == "normal"
    assert normal["resolved_order_price"] == 82_900
    assert recovered["offset_profile"] == "recovered_wide"
    assert recovered["resolved_order_price"] == 82_500


def test_p1_post_probe_defer_has_no_executable_price():
    resolved = entry_latency_module.resolve_scalping_entry_price(
        strategy_id="SCALPING",
        defensive_order_price=10_000,
        target_buy_price=0,
        best_bid=9_990,
        best_ask=10_010,
        phase="post_probe",
        probe_fill_price=10_000,
        continuation_action="DEFER",
    )

    assert resolved["allowed"] is False
    assert resolved["resolved_order_price"] == 0
    assert resolved["reason"] == "continuation_defer"
