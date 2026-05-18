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
            SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION=1200,
            SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION=1500,
            SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION=0.01,
        ),
    )

    config = entry_latency_module._build_entry_config()

    assert config.max_ws_age_ms_for_caution == 1200
    assert config.max_ws_jitter_ms_for_caution == 1500
    assert config.max_spread_ratio_for_caution == 0.01


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


def test_latency_entry_caution_rejects_deprecated_fallback():
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

    assert result["allowed"] is False
    assert result["decision"] == "REJECT_MARKET_CONDITION"
    assert result["reason"] == "latency_fallback_deprecated"
    assert result["mode"] == "reject"
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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["allowed"] is False
    assert result["decision"] == "REJECT_MARKET_CONDITION"
    assert result["reason"] == "latency_fallback_deprecated"
    assert result["mode"] == "reject"
    assert result["latency_danger_reasons"] == "other_danger"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["allowed"] is False
    assert result["decision"] == "REJECT_MARKET_CONDITION"
    assert result["reason"] == "latency_fallback_deprecated"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["decision"] == "REJECT_DANGER"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "spread_relief_canary_applied"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_spread_relief_normal_override"
    assert result["mode"] == "normal"
    assert result["latency_danger_reasons"] == "spread_too_wide"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "spread_only_required"
    assert result["decision"] == "REJECT_DANGER"
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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "ws_jitter_relief_canary_applied"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_ws_jitter_relief_normal_override"
    assert result["mode"] == "normal"
    assert result["latency_danger_reasons"] == "ws_jitter_too_high"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "ws_jitter_only_required"
    assert result["decision"] == "REJECT_DANGER"
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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "other_danger_relief_canary_applied"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_other_danger_relief_normal_override"
    assert result["mode"] == "normal"
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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "ws_jitter_limit_exceeded"
    assert result["decision"] == "REJECT_DANGER"
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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "low_signal"
    assert result["decision"] == "REJECT_DANGER"
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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "quote_fresh_composite_canary_applied"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_quote_fresh_composite_normal_override"
    assert result["mode"] == "normal"
    assert result["latency_danger_reasons"] == "ws_age_too_high,ws_jitter_too_high"
    assert result["entry_price_guard"] == "latency_danger_override_defensive"
    assert result["entry_price_defensive_ticks"] == 3
    assert result["normal_defensive_order_price"] == 10_010
    assert result["counterfactual_order_price_1tick"] == 10_010
    assert result["latency_guarded_order_price"] == 9_990
    assert result["order_price"] == 9_990


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

    assert result["allowed"] is True
    assert result["latency_guarded_order_price"] == 9_990
    assert result["counterfactual_order_price_1tick"] == 9_980
    assert result["order_price"] == 9_980
    assert result["price_resolution_reason"] == "reference_target_cap"
    assert result["reference_target_applied"] is True


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

    assert result["allowed"] is True
    assert result["normal_defensive_order_price"] == 199_900
    assert result["latency_guarded_order_price"] == 199_700
    assert result["order_price"] == 199_700


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "low_signal"
    assert result["decision"] == "REJECT_DANGER"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "signal_quality_quote_composite_canary_applied"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_signal_quality_quote_composite_normal_override"


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

    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "low_buy_pressure"
    assert result["decision"] == "REJECT_DANGER"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is True
    assert result["latency_canary_reason"] == "mechanical_momentum_relief_canary_applied"
    assert result["allowed"] is True
    assert result["decision"] == "ALLOW_NORMAL"
    assert result["reason"] == "latency_mechanical_momentum_relief_normal_override"


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

    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "signal_not_mechanical"
    assert result["decision"] == "REJECT_DANGER"


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

    assert result["latency_state"] == "DANGER"
    assert result["latency_canary_applied"] is False
    assert result["latency_canary_reason"] == "danger_reason_not_allowed"
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
