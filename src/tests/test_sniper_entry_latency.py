import time
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import src.engine.sniper_entry_latency as entry_latency_module
from src.engine.sniper_entry_latency import (
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

    _assert_danger_hard_safety_block(
        result,
        danger_reasons=("ws_age_too_high", "spread_too_wide"),
    )
    assert "ws_age_too_high" in result["latency_danger_reasons"]
    assert "spread_too_wide" in result["latency_danger_reasons"]


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

    _assert_danger_hard_safety_block(result, danger_reasons="other_danger")


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

    _assert_danger_hard_safety_block(result, danger_reasons="other_danger")


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

    _assert_danger_hard_safety_block(result, danger_reasons="other_danger")


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
