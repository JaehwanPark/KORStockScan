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
    assert state_handlers._early_accel_strong_bundle_recheck_failure_class("DROP") == "drop_action"
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


def test_latency_entry_runtime_override_uses_more_conservative_defensive_ticks(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config())
    monkeypatch.setattr(entry_latency_module, "_NORMAL_BUILDER", entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_ENTRY_POLICY", entry_latency_module.EntryPolicy(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_LATENCY_MONITOR", entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG))

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
    monkeypatch.setattr(entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config())
    monkeypatch.setattr(entry_latency_module, "_NORMAL_BUILDER", entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_ENTRY_POLICY", entry_latency_module.EntryPolicy(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_LATENCY_MONITOR", entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG))

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
    monkeypatch.setattr(entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config())
    monkeypatch.setattr(entry_latency_module, "_NORMAL_BUILDER", entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_ENTRY_POLICY", entry_latency_module.EntryPolicy(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_LATENCY_MONITOR", entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG))

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
    assert result["conditional_1tick_real_override_reason"] == "disabled_or_non_scalping"


def test_latency_entry_three_tick_override_is_limited_to_scalping(monkeypatch):
    monkeypatch.setattr(
        entry_latency_module,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_NORMAL_DEFENSIVE_TICKS=3),
    )
    monkeypatch.setattr(entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config())
    monkeypatch.setattr(entry_latency_module, "_NORMAL_BUILDER", entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_ENTRY_POLICY", entry_latency_module.EntryPolicy(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_LATENCY_MONITOR", entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG))

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
    monkeypatch.setattr(entry_latency_module, "_CONFIG", entry_latency_module._build_entry_config())
    monkeypatch.setattr(entry_latency_module, "_NORMAL_BUILDER", entry_latency_module.NormalEntryBuilder(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_ENTRY_POLICY", entry_latency_module.EntryPolicy(entry_latency_module._CONFIG))
    monkeypatch.setattr(entry_latency_module, "_LATENCY_MONITOR", entry_latency_module.LatencyMonitor(entry_latency_module._CONFIG))

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
    monkeypatch.setattr(entry_latency_module.constants_module, "TRADING_RULES", runtime_rules)

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


def test_pre_submit_quote_refresh_uses_pid_env_when_runtime_rules_are_stale(monkeypatch):
    stale_rules = replace(
        CONFIG,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED=False,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS=100,
        SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO=0.001,
    )
    monkeypatch.setattr(entry_latency_module, "TRADING_RULES", stale_rules)
    monkeypatch.setattr(entry_latency_module.constants_module, "TRADING_RULES", stale_rules)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO", "0.015")

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
    monkeypatch.setattr(entry_latency_module.constants_module, "TRADING_RULES", stale_rules)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO", "0.015")

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


def test_real_pre_submit_ws_snapshot_refresh_uses_fresh_ws_manager_snapshot(monkeypatch):
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


def test_real_pre_submit_ws_snapshot_refresh_keeps_valid_input_when_timestamp_missing(monkeypatch):
    class FakeWsManager:
        def get_latest_data(self, code):
            raise AssertionError("WS manager should not be consulted for a valid input snapshot")

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
    assert fields["pre_submit_ws_snapshot_refresh_reason"] == "input_snapshot_timestamp_missing"


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


def test_pre_ai_strength_ws_snapshot_refresh_keeps_fresh_input_history_count(monkeypatch):
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
                "strength_momentum_history": [{"ts": time.time() - 10.0, "v_pw": 121.0}],
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

    assert state_handlers._strength_momentum_source_quality_block_reason(ws_data, result) == ""


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
            raise AssertionError("WS manager must not be called when refresh is explicitly disabled")

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


def test_latency_gate_observer_unhealthy_detection():
    assert state_handlers._latency_gate_observer_unhealthy(
        {"orderbook_stability": {"observer_healthy": False, "observer_missing_reason": "missing_trade"}}
    ) is True
    assert state_handlers._latency_gate_observer_unhealthy(
        {"orderbook_stability": {"observer_healthy": True, "observer_missing_reason": "ok"}}
    ) is False
    assert state_handlers._latency_gate_observer_unhealthy({}) is False


def test_real_pre_submit_rest_orderbook_refresh_uses_ka10004_fresh_snapshot(monkeypatch):
    now_hhmmss = datetime.now().strftime("%H%M%S")

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "source": "ka10004_rest_orderbook",
            "bid_req_base_tm": now_hhmmss,
            "curr": 10_030,
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
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_REST_ORDERBOOK_MAX_AGE_MS", "3000")

    refreshed, fields = state_handlers._pre_submit_refresh_rest_orderbook_snapshot(
        "123456",
        {"curr": 10_000, "best_ask": 10_010, "best_bid": 10_000},
        "SCALPING",
    )

    assert fields["pre_submit_rest_orderbook_refresh_enabled"] is True
    assert fields["pre_submit_rest_orderbook_refresh_applied"] is True
    assert fields["pre_submit_rest_orderbook_refresh_reason"] == "rest_orderbook_fresh"
    assert refreshed["curr"] == 10_030
    assert refreshed["best_ask"] == 10_030
    assert refreshed["best_bid"] == 10_020
    assert refreshed["quote_refresh_source"] == "ka10004_rest_orderbook"


def test_real_pre_submit_rest_orderbook_refresh_blocks_stale_ka10004_snapshot(monkeypatch):
    stale_hhmmss = datetime.fromtimestamp(time.time() - 10).strftime("%H%M%S")

    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        lambda token, code: {
            "bid_req_base_tm": stale_hhmmss,
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


def test_real_pre_submit_ws_snapshot_refresh_blocks_stale_ws_manager_snapshot(monkeypatch):
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

    _assert_danger_hard_safety_block(result, danger_reasons="other_danger")


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

    _assert_danger_hard_safety_block(result, danger_reasons="other_danger")


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

    _assert_danger_hard_safety_block(result, danger_reasons="other_danger")


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


def test_latency_spread_relief_canary_uses_entry_momentum_tag_when_position_tag_missing(monkeypatch):
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


def test_latency_spread_relief_canary_uses_effective_min_signal_floor_override(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_other_danger_relief_canary_overrides_reject_danger_to_normal(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_other_danger_relief_canary_enforces_stricter_residual_limits(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_quote_fresh_composite_canary_overrides_mixed_danger_to_normal(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_quote_fresh_composite_price_guard_respects_target_buy_price(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_quote_fresh_composite_price_guard_uses_valid_tick_at_price_boundary(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_signal_quality_quote_composite_backup_canary_overrides_to_normal(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_signal_quality_quote_composite_backup_blocks_weak_buy_pressure(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_mechanical_momentum_relief_overrides_low_ai_score_quote_family(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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


def test_latency_mechanical_momentum_relief_blocks_high_ai_score_to_avoid_axis_overlap(monkeypatch):
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
    monkeypatch.setattr(entry_latency_module._CACHE, "update", lambda *args, **kwargs: None)
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
        {"quote_stale": False, "ws_age_ms": 451, "ws_jitter_ms": 301, "spread_ratio": 0.011},
    )()
    assert _latency_danger_reasons(status) == [
        "ws_age_too_high",
        "ws_jitter_too_high",
        "spread_too_wide",
    ]


def test_percent_bps_mode_normal_defensive_0025_pct(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps1", best_bid=10_000, best_ask=10_010, ts=time.time(),
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
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps2", best_bid=10_000, best_ask=10_010, ts=time.time(),
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
    assert result["conditional_1tick_real_override_reason"] == "spread_1tick_strong_buy_pressure_percent_bps"
    assert result["order_price"] == 9990


def test_percent_bps_mode_favorable_micro_0015_pct(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps_favorable", best_bid=10_000, best_ask=10_020, ts=time.time(),
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
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_bps_weak", best_bid=10_000, best_ask=10_050, ts=time.time(),
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


def test_aggressive_entry_price_override_moves_neutral_defensive_to_bid_minus_tick(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
        "005930_aggressive_neutral", best_bid=10_000, best_ask=10_050, ts=time.time(),
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
    assert result["aggressive_entry_price_override_type"] == "defensive_missed_upside_v1"
    assert result["aggressive_entry_price_original_profile"] == "weak_liquidity_wide_spread"
    assert result["aggressive_entry_price_original_bps"] == 40
    assert result["aggressive_entry_price_target_mode"] == "best_bid_near"
    assert result["aggressive_entry_price_order_price"] == 9990


def test_aggressive_entry_price_override_moves_positive_micro_to_best_bid(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
        "005930_aggressive_positive", best_bid=10_000, best_ask=10_020, ts=time.time(),
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


def test_reference_target_missed_upside_override_moves_positive_micro_to_best_bid(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
        },
        strategy_id="SCALPING",
        planned_qty=1,
        signal_price=10_000,
        signal_strength=0.9,
        target_buy_price=9_900,
    )

    assert result["entry_price_guard"] == "reference_target_cap_missed_upside_aggressive_entry"
    assert result["order_price"] == 10000
    assert result["price_resolution_reason"] == "aggressive_entry_price_override"
    assert result["reference_target_applied"] is False
    assert result["reference_target_rejected_reason"] == "aggressive_entry_price_override_applied"
    assert result["aggressive_entry_price_override_applied"] is True
    assert result["aggressive_entry_price_override_type"] == "reference_target_cap_missed_upside_v1"
    assert result["aggressive_entry_price_override_reason"] == "reference_target_cap_missed_upside_best_bid_near"
    context = result["entry_price_gap_profile_context"]
    assert context["reference_target_price"] == 9900
    assert context["reference_target_below_bid_bps"] == 100
    assert context["reference_target_missed_upside_min_bps"] == 20


def test_reference_target_missed_upside_override_moves_neutral_to_bid_minus_tick(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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

    assert result["entry_price_guard"] == "reference_target_cap_missed_upside_aggressive_entry"
    assert result["order_price"] == 9990
    assert result["aggressive_entry_price_override_type"] == "reference_target_cap_missed_upside_v1"
    assert result["aggressive_entry_price_target_mode"] == "best_bid_near"


def test_reference_target_missed_upside_override_skips_below_min_bps(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
    assert result["aggressive_entry_price_override_skip_reason"] == "reference_target_below_bid_bps_below_min"


def test_aggressive_entry_price_override_skips_when_dynamic_resolver_live_selected(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
    assert result["aggressive_entry_price_override_skip_reason"] == "dynamic_entry_price_resolver_live_selected"


def test_aggressive_entry_price_override_skips_when_entry_price_live_tuning_selected(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
    assert result["aggressive_entry_price_override_skip_reason"] == "dynamic_entry_price_resolver_live_selected"


def test_aggressive_entry_price_override_skips_weak_pullback_like_context(monkeypatch):
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)
    monkeypatch.setattr(entry_latency_module, "_normal_defensive_bps", lambda: 25)
    monkeypatch.setattr(entry_latency_module, "_conditional_strong_defensive_bps", lambda: 10)
    monkeypatch.setattr(entry_latency_module, "_normal_favorable_defensive_bps", lambda: 15)
    monkeypatch.setattr(entry_latency_module, "_normal_weak_defensive_bps", lambda: 40)
    monkeypatch.setattr(entry_latency_module, "_conditional_real_1tick_enabled", lambda s: True)
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
    monkeypatch.setattr(entry_latency_module, "_defense_mode_is_percent_bps", lambda: True)

    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.reset()
    entry_latency_module.ORDERBOOK_STABILITY_OBSERVER.record_quote(
        "005930_swing1", best_bid=10_000, best_ask=10_010, ts=time.time(),
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
        "005930_tick", best_bid=10_000, best_ask=10_010, ts=time.time(),
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
