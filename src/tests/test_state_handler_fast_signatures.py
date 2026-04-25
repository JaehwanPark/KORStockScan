from dataclasses import replace

from src.engine.sniper_state_handlers import (
    _apply_initial_entry_qty_cap,
    _apply_wait6579_probe_canary,
    _build_ai_overlap_log_fields,
    _build_ai_ops_log_fields,
    _build_gatekeeper_fast_signature,
    _build_holding_ai_fast_signature,
    _should_run_main_buy_recovery_canary,
    _resolve_gatekeeper_fast_reuse_sec,
    _resolve_holding_ai_fast_reuse_sec,
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
    assert fields["ai_score_raw"] == "74.0"
    assert fields["ai_score_after_bonus"] == "79.0"
    assert fields["entry_score_threshold"] == "75.0"
    assert fields["big_bite_bonus_applied"] is True
    assert fields["ai_cooldown_blocked"] is False


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


def test_should_run_main_buy_recovery_canary_rejects_large_sell_or_danger(monkeypatch):
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

    assert _should_run_main_buy_recovery_canary({"action": "WAIT"}, 72, {}, [], [], _BadEngine()) is False
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
