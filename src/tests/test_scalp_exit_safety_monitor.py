from datetime import datetime
import threading

import pytest

from src.engine import sniper_state_handlers as handlers
from src.engine import sniper_trade_utils
from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor


def _exact_cancel_ack_response(
    *,
    orig_order_no="0000001",
    qty="7",
    code="123456",
    route="SOR",
):
    return {
        "return_code": "0",
        "ord_no": "0000999",
        "base_orig_ord_no": orig_order_no,
        "cncl_qty": str(qty),
        "broker_route_attempted": True,
        "effective_dmst_stex_tp": route,
        "cancel_request_api_id": "kt10003",
        "cancel_request_code": code,
        "cancel_request_orig_ord_no": orig_order_no,
        "cancel_request_qty": "0",
        "cancel_request_route": route,
        "cancel_request_bound": True,
        "return_msg": "ok",
    }


@pytest.fixture(autouse=True)
def _disable_real_peak_ledger(monkeypatch):
    monkeypatch.setattr(
        handlers, "_persist_scalping_position_peak", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *args, **kwargs: False
    )


def test_monitor_polls_only_holding_targets():
    calls = []
    targets = [
        {"status": "WATCHING", "code": "111111"},
        {"status": "HOLDING", "code": "222222"},
    ]
    monitor = ScalpExitSafetyMonitor(
        targets_provider=lambda: targets,
        ws_snapshot_provider=lambda code: {"curr": 10_000, "code": code},
        evaluator=lambda stock, code, ws, now_ts: calls.append(
            (stock, code, ws, now_ts)
        ),
        state_lock=threading.RLock(),
    )

    assert monitor.run_once(now_ts=1_000.0) == 1
    assert [call[1] for call in calls] == ["222222"]


@pytest.mark.parametrize(
    ("regime", "expected_source"),
    [("BULL", "kospi_stop_loss_bull"), ("BEAR", "kospi_stop_loss_bear")],
)
def test_kospi_open_loss_stop_context_uses_regime_for_default_position(
    regime,
    expected_source,
):
    context = handlers._manual_control_open_loss_stop_context(
        {"position_tag": "SCANNER"},
        strategy="KOSPI_ML",
        market_regime=regime,
    )

    assert context["stop_line_source"] == expected_source
    assert context["exit_rule_candidate"] == "kospi_regime_stop_loss"


def test_exit_token_blocks_probe_continuation_during_reconciliation():
    assert handlers._entry_split_probe_exit_authority_active(
        {"status": "HOLDING", "exit_requested": False, "exit_token": "token-1"}
    )


def test_fast_exit_skips_manual_control_excluded_holding(monkeypatch):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("manual-control holdings must not reach quote or REST work")
        ),
    )

    assert (
        handlers.evaluate_and_dispatch_fast_scalp_exit(
            {
                "name": "수동관리",
                "code": "950160",
                "strategy": "SCALPING",
                "status": "HOLDING",
                "buy_price": 20_000,
                "buy_qty": 1,
            },
            "950160",
            {"curr": 19_000},
            now_ts=now_ts,
        )
        is False
    )


def test_fast_exit_claims_once_and_dispatches_without_holding_ai(monkeypatch):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {
                "quote_consistency_state": "consistent",
                "quote_consistency_reason": "ok",
                "executable_sell_price": 9_800,
            },
            9_800,
            0,
            9_800,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy_price, price: ((float(price) - float(buy_price)) / float(buy_price))
        * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers,
        "_scalping_micro_estimator_log_fields",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        lambda **_kwargs: False,
    )
    dispatches = []

    def fake_dispatch(**kwargs):
        dispatches.append(kwargs)
        kwargs["stock"]["status"] = "SELL_ORDERED"
        kwargs["stock"]["exit_order_sent_at"] = now_ts + 0.1

    monkeypatch.setattr(handlers, "_dispatch_scalp_preset_exit", fake_dispatch)
    handlers.HIGHEST_PRICES = {"123456": 10_077}
    stock = {
        "id": 1,
        "name": "금호건설",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 94,
    }

    triggered = handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock,
        "123456",
        {"curr": 9_800},
        now_ts=now_ts,
    )

    assert triggered is True
    assert len(dispatches) == 1
    assert dispatches[0]["fast_exit"] is True
    assert dispatches[0]["exit_rule"] == "scalp_trailing_take_profit"
    assert stock["exit_requested"] is True
    assert stock["exit_token"]
    assert stock["probe_expand_forbidden"] is True
    assert stock["exit_order_sent_at"] - stock["exit_decided_at"] <= 0.5

    assert (
        handlers.evaluate_and_dispatch_fast_scalp_exit(
            stock,
            "123456",
            {"curr": 9_790},
            now_ts=now_ts + 0.25,
        )
        is False
    )
    assert len(dispatches) == 1


def test_fast_exit_uses_cached_sell_quote_when_safety_contract_allows_it(
    monkeypatch,
):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers,
        "_fast_exit_execution_route_fields",
        lambda *args, **kwargs: {
            "fast_exit_broker_route": "SOR",
            "fast_exit_execution_cohort": "KRX",
            "fast_exit_route_source_quality_blocked": False,
            "fast_exit_broker_route_blocked": False,
        },
    )

    def quote_fields(*_args, safety_exit=False, **_kwargs):
        return (
            {
                "quote_consistency_state": "stale",
                "quote_consistency_reason": "quote_stale",
                "quote_consistency_safety_exit_allowed": safety_exit,
            },
            9_800,
            9_810,
            9_800,
        )

    monkeypatch.setattr(handlers, "_build_quote_consistency_fields", quote_fields)
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: ({}, "timeout", 400.0),
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy_price, price: ((float(price) - float(buy_price)) / float(buy_price))
        * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(
        handlers, "_scalping_micro_estimator_log_fields", lambda **_kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        lambda **_kwargs: False,
    )
    logs = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    handlers.HIGHEST_PRICES = {"475560": 10_077}
    stock = {
        "id": 475560,
        "name": "cached-safety-exit",
        "code": "475560",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "hard_stop_pct": -1.5,
    }

    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock,
        "475560",
        {"curr": 9_800},
        now_ts=now_ts,
    )
    assert len(dispatches) == 1
    assert dispatches[0]["curr_p"] == 9_800
    assert not any(stage == "scalp_fast_exit_quote_blocked" for stage, _ in logs)


def test_dongyang_wide_spread_trailing_uses_confirmed_rest_bid(monkeypatch):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "_fast_exit_execution_route_fields",
        lambda *args, **kwargs: {
            "fast_exit_broker_route": "SOR",
            "fast_exit_execution_cohort": "KRX",
            "fast_exit_route_source_quality_blocked": False,
            "fast_exit_broker_route_blocked": False,
        },
    )

    def quote_fields(*_args, rest_snapshot=None, **_kwargs):
        if rest_snapshot:
            return (
                {
                    "quote_consistency_state": "consistent",
                    "quote_consistency_reason": "ok",
                    "quote_consistency_rest_age_ms": 10.0,
                },
                1134,
                1135,
                1133,
            )
        return (
            {
                "quote_consistency_state": "consistent",
                "quote_consistency_reason": "ok",
            },
            1133,
            1145,
            1121,
        )

    monkeypatch.setattr(handlers, "_build_quote_consistency_fields", quote_fields)
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (
            {
                "best_bid": 1133,
                "best_ask": 1135,
                "rest_received_ts": now_ts,
            },
            "ok",
            12.0,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_scalp_trailing_loss_conversion_recheck_config",
        lambda _now: {
            "max_spread_bps": 150.0,
            "rest_timeout_ms": 300,
            "max_rest_age_ms": 1500.0,
        },
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy, price: ((float(price) - float(buy)) / float(buy)) * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(
        handlers, "_scalping_micro_estimator_log_fields", lambda **_kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        lambda **_kwargs: False,
    )
    logs = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    handlers.HIGHEST_PRICES = {"001520": 1140}
    stock = {
        "id": 117,
        "name": "동양",
        "code": "001520",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 1123,
        "buy_qty": 1,
    }

    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock, "001520", {"curr": 1133}, now_ts=now_ts
    )
    assert dispatches[0]["curr_p"] == 1134
    assert dispatches[0]["ws_data"]["executable_sell_price"] == 1133
    assert any(
        stage == "scalp_trailing_wide_spread_recheck"
        and fields["recheck_state"] == "confirmed"
        for stage, fields in logs
    )


def test_wide_spread_trailing_rechecks_rest_when_mark_pnl_is_slightly_negative(
    monkeypatch,
):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_WARN_GAP_BPS", "80")
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "_fast_exit_execution_route_fields",
        lambda *args, **kwargs: {
            "fast_exit_broker_route": "SOR",
            "fast_exit_execution_cohort": "KRX",
            "fast_exit_route_source_quality_blocked": False,
            "fast_exit_broker_route_blocked": False,
        },
    )

    def quote_fields(*_args, rest_snapshot=None, **_kwargs):
        if rest_snapshot:
            return (
                {
                    "quote_consistency_state": "ok",
                    "quote_consistency_reason": "ws_rest_gap_ok",
                    "quote_consistency_rest_age_ms": 10.0,
                },
                3_000,
                3_005,
                2_995,
            )
        return (
            {
                "quote_consistency_state": "single_source",
                "quote_consistency_reason": "ws_only_fresh",
            },
            2_995,
            3_030,
            2_990,
        )

    monkeypatch.setattr(handlers, "_build_quote_consistency_fields", quote_fields)
    rest_fetches = []
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: rest_fetches.append((args, kwargs))
        or (
            {
                "best_bid": 2_995,
                "best_ask": 3_005,
                "rest_received_ts": now_ts,
            },
            "ok",
            12.0,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_scalp_trailing_loss_conversion_recheck_config",
        lambda _now: {
            "max_spread_bps": 150.0,
            "rest_timeout_ms": 300,
            "max_rest_age_ms": 1500.0,
        },
    )
    pnl_by_price = {
        2_990: -0.23,
        2_995: -0.06,
        3_000: 0.10,
        3_025: 0.94,
    }
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda _buy, price: pnl_by_price[int(price)],
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(
        handlers, "_scalping_micro_estimator_log_fields", lambda **_kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        lambda **_kwargs: False,
    )
    logs = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    handlers.HIGHEST_PRICES = {"475040": 3_025}
    stock = {
        "id": 25063,
        "name": "스트라드비젼",
        "code": "475040",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 2_990,
        "buy_qty": 1,
    }

    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock, "475040", {"curr": 2_995}, now_ts=now_ts
    )
    assert len(rest_fetches) == 1
    assert dispatches[0]["ws_data"]["executable_sell_price"] == 2_995
    recheck = next(
        fields
        for stage, fields in logs
        if stage == "scalp_trailing_wide_spread_recheck"
    )
    assert recheck["recheck_state"] == "confirmed"
    assert recheck["ws_mark_profit_rate"] == "-0.06"
    assert recheck["confirmation_spread_bps"] == "80.000"


def test_wide_spread_trailing_defers_when_rest_bbo_is_not_narrow(monkeypatch):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "_fast_exit_execution_route_fields",
        lambda *args, **kwargs: {
            "fast_exit_broker_route": "SOR",
            "fast_exit_execution_cohort": "KRX",
            "fast_exit_route_source_quality_blocked": False,
            "fast_exit_broker_route_blocked": False,
        },
    )
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *_args, **_kwargs: (
            {
                "quote_consistency_state": "consistent",
                "quote_consistency_reason": "ok",
                "quote_consistency_rest_age_ms": 10.0,
            },
            1133,
            1145,
            1121,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (
            {
                "best_bid": 1121,
                "best_ask": 1145,
                "rest_received_ts": now_ts,
            },
            "ok",
            12.0,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_scalp_trailing_loss_conversion_recheck_config",
        lambda _now: {
            "max_spread_bps": 150.0,
            "rest_timeout_ms": 300,
            "max_rest_age_ms": 1500.0,
        },
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy, price: ((float(price) - float(buy)) / float(buy)) * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    handlers.HIGHEST_PRICES = {"001520": 1140}
    stock = {
        "id": 117,
        "name": "동양",
        "code": "001520",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 1123,
        "buy_qty": 1,
    }

    assert (
        handlers.evaluate_and_dispatch_fast_scalp_exit(
            stock, "001520", {"curr": 1133}, now_ts=now_ts
        )
        is False
    )
    assert dispatches == []
    assert not stock.get("exit_token")


def test_fast_exit_dispatch_survives_claim_logging_failure(monkeypatch):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {
                "quote_consistency_state": "consistent",
                "quote_consistency_reason": "ok",
                "executable_sell_price": 9_800,
            },
            9_800,
            0,
            9_800,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy_price, price: ((float(price) - float(buy_price)) / float(buy_price))
        * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("instrumentation unavailable")
        ),
    )
    monkeypatch.setattr(handlers, "log_error", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        handlers, "_scalping_micro_estimator_log_fields", lambda **_kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        lambda **_kwargs: False,
    )
    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    handlers.HIGHEST_PRICES = {"123456": 10_077}
    stock = {
        "id": 1,
        "name": "동양",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
    }

    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock,
        "123456",
        {"curr": 9_800},
        now_ts=now_ts,
    )
    assert len(dispatches) == 1
    assert dispatches[0]["fast_exit"] is True
    assert stock["exit_requested"] is True


def test_fast_exit_uses_trailing_continuation_owner_before_claim(monkeypatch):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {"quote_consistency_state": "consistent", "quote_consistency_reason": "ok"},
            9_800,
            0,
            9_800,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy_price, price: ((float(price) - float(buy_price)) / float(buy_price))
        * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(
        handlers, "_scalping_micro_estimator_log_fields", lambda **_kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )
    continuation_calls = []
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        lambda **kwargs: continuation_calls.append(kwargs) or True,
    )
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("deferred trailing must not dispatch")
        ),
    )
    handlers.HIGHEST_PRICES = {"123456": 10_077}
    stock = {
        "name": "지엔씨에너지",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
    }

    assert (
        handlers.evaluate_and_dispatch_fast_scalp_exit(
            stock, "123456", {"curr": 9_800}, now_ts=now_ts
        )
        is False
    )
    assert len(continuation_calls) == 1
    assert continuation_calls[0]["recheck_invoker"] == "fast_exit_monitor"
    envelope = continuation_calls[0]["decision_quote_envelope"]
    assert envelope["exit_quote_envelope_id"]
    assert envelope["exit_quote_envelope_base_best_bid"] == 9_800
    assert envelope["exit_quote_envelope_base_mark_price"] == 9_800
    assert stock.get("exit_token") in (None, "")
    assert stock.get("exit_requested") is not True

    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    hard_stop_stock = dict(stock, hard_stop_pct=-1.0)
    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        hard_stop_stock, "123456", {"curr": 9_800}, now_ts=now_ts
    )
    assert len(continuation_calls) == 1
    assert dispatches[0]["exit_rule"] == "scalp_hard_stop_pct"

    monkeypatch.setattr(
        handlers,
        "_pyramid_post_add_trailing_grace",
        lambda *_args, **_kwargs: (True, 1.0, 2.0),
    )
    monkeypatch.setattr(
        handlers, "_log_pyramid_post_add_trailing_grace", lambda *_args, **_kwargs: None
    )
    pyramid_stock = dict(stock)
    assert (
        handlers.evaluate_and_dispatch_fast_scalp_exit(
            pyramid_stock, "123456", {"curr": 9_800}, now_ts=now_ts
        )
        is False
    )
    assert len(continuation_calls) == 1
    assert len(dispatches) == 1


@pytest.mark.parametrize(
    ("reuse_allowed", "expected_triggered", "expected_decision_price"),
    (
        (True, True, 9_790),
        (False, False, None),
    ),
)
def test_fast_exit_reuses_or_blocks_continuation_recheck_quote_envelope(
    monkeypatch,
    reuse_allowed,
    expected_triggered,
    expected_decision_price,
):
    now_ts = 1_784_778_400.0
    active_date = datetime.fromtimestamp(now_ts, tz=handlers._KST).date().isoformat()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", active_date)
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {"quote_consistency_state": "consistent", "quote_consistency_reason": "ok"},
            9_800,
            9_801,
            9_800,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_fast_exit_execution_route_fields",
        lambda *args, **kwargs: {
            "fast_exit_broker_route": "SOR",
            "fast_exit_execution_cohort": "KRX",
            "fast_exit_route_source_quality_blocked": False,
            "fast_exit_broker_route_blocked": False,
        },
    )
    monkeypatch.setattr(
        handlers,
        "calculate_net_profit_rate",
        lambda buy_price, price: ((float(price) - float(buy_price)) / float(buy_price))
        * 100.0,
    )
    monkeypatch.setattr(
        handlers,
        "_rule_float",
        lambda name, default=0.0: {
            "SCALP_TRAILING_START_PCT": 0.6,
            "SCALP_TRAILING_LIMIT_WEAK": 0.4,
            "SCALP_TRAILING_LIMIT_STRONG": 0.8,
        }.get(name, default),
    )
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(
        handlers,
        "_holding_score_runtime_context",
        lambda *args, **kwargs: {"usable_for_negative_exit": False},
    )
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(
        handlers, "_scalping_micro_estimator_log_fields", lambda **_kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_loss_conversion_recheck",
        lambda **_kwargs: False,
    )

    def continuation_recheck(**kwargs):
        envelope = kwargs["decision_quote_envelope"]
        envelope.update(
            {
                "exit_quote_envelope_recheck_attempted": True,
                "exit_quote_envelope_recheck_rest_state": "ok",
                "exit_quote_envelope_recheck_rest_elapsed_ms": 12.0,
                "exit_quote_envelope_recheck_reuse_allowed": reuse_allowed,
                "exit_quote_envelope_recheck_block_reason": (
                    "-" if reuse_allowed else "recheck_quote_conflicted"
                ),
                "exit_quote_envelope_recheck_mark_price": 9_795,
                "exit_quote_envelope_recheck_best_ask": 9_800,
                "exit_quote_envelope_recheck_best_bid": 9_790,
                "exit_quote_envelope_recheck_rest_snapshot": {
                    "best_bid": 9_790,
                    "best_ask": 9_800,
                    "rest_received_ts": now_ts,
                },
                "exit_quote_envelope_recheck_quote_fields": {
                    "quote_consistency_state": (
                        "consistent" if reuse_allowed else "diverged"
                    ),
                    "quote_consistency_reason": (
                        "ok" if reuse_allowed else "quote_diverged"
                    ),
                },
            }
        )
        return False

    monkeypatch.setattr(
        handlers,
        "_evaluate_scalp_trailing_continuation_recheck",
        continuation_recheck,
    )
    logs = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    dispatches = []
    monkeypatch.setattr(
        handlers,
        "_dispatch_scalp_preset_exit",
        lambda **kwargs: dispatches.append(kwargs),
    )
    handlers.HIGHEST_PRICES = {"123456": 10_077}
    stock = {
        "name": "quote-envelope",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
    }

    triggered = handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock,
        "123456",
        {"curr": 9_800},
        now_ts=now_ts,
    )

    assert triggered is expected_triggered
    if reuse_allowed:
        assert len(dispatches) == 1
        assert (
            dispatches[0]["ws_data"]["executable_sell_price"] == expected_decision_price
        )
        claim = next(
            fields for stage, fields in logs if stage == "scalp_fast_exit_claimed"
        )
        assert claim["decision_price"] == expected_decision_price
        assert claim["exit_quote_envelope_recheck_reuse_allowed"] is True
    else:
        assert dispatches == []
        assert not stock.get("exit_token")
        blocked = next(
            fields
            for stage, fields in logs
            if stage == "scalp_fast_exit_quote_envelope_blocked"
        )
        assert blocked["block_reason"] == "recheck_quote_conflicted"
        assert blocked["exit_quote_envelope_recheck_reuse_allowed"] is False


def _nxt_quote_snapshot(code: str, now_ts: float) -> dict:
    return {
        "curr": 9_800,
        "best_bid": 9_800,
        "best_ask": 9_810,
        "last_realtime_type_ts": {"0D": now_ts},
        "last_realtime_type_item": {"0D": f"{code}_AL"},
        "last_realtime_type_market_suffix": {"0D": "_AL"},
        "last_realtime_type_market_route": {"0D": "krx_nxt_integrated"},
    }


def _exact_nxt_0d_snapshot(
    code: str,
    now_ts: float,
    *,
    observed_age_ms: float = 0.0,
    bid: int = 9_800,
    bid_qty: int = 20,
) -> dict:
    observed_epoch = now_ts - (observed_age_ms / 1000.0)
    orderbook = {
        "asks": [{"price": bid + 10, "volume": 15}],
        "bids": [{"price": bid, "volume": bid_qty}],
    }
    return {
        "curr": bid + 5,
        "orderbook": orderbook,
        "last_realtime_type_ts": {"0D": observed_epoch},
        "last_realtime_type_item": {"0D": f"{code}_NX"},
        "last_realtime_type_market_suffix": {"0D": "_NX"},
        "last_realtime_type_market_route": {"0D": "nxt_only"},
        "last_realtime_type_effective_venue": {"0D": "NXT"},
        "realtime_type_snapshots_by_route": {
            "_NX|nxt_only": {
                "0D": {
                    "realtime_type": "0D",
                    "observed_epoch": observed_epoch,
                    "item": f"{code}_NX",
                    "market_suffix": "_NX",
                    "market_route": "nxt_only",
                    "effective_venue": "NXT",
                    "orderbook": orderbook,
                }
            }
        },
    }


def test_fast_exit_route_guard_resolves_nxt_and_premarket_as_nxt():
    code = "123456"
    nxt_ts = datetime(2026, 7, 23, 16, 20, tzinfo=handlers._KST).timestamp()
    nxt_fields = handlers._fast_exit_execution_route_fields(
        {
            "is_nxt": True,
            "entry_execution_broker_route": "NXT",
            "entry_execution_cohort": "NXT",
        },
        code,
        _nxt_quote_snapshot(code, nxt_ts),
        now_ts=nxt_ts,
    )
    assert nxt_fields["fast_exit_broker_route"] == "NXT"
    assert nxt_fields["fast_exit_execution_cohort"] == "NXT"
    assert nxt_fields["fast_exit_execution_cohort_resolution"] == (
        "session_and_broker_route_resolved"
    )
    assert nxt_fields["fast_exit_route_resolution_reason"] == (
        "nxt_session_nxt_enabled"
    )
    assert nxt_fields["fast_exit_ws_nxt_route_ready"] is True
    assert nxt_fields["fast_exit_route_source_quality_blocked"] is False

    premarket_ts = datetime(2026, 7, 23, 8, 30, tzinfo=handlers._KST).timestamp()
    premarket_fields = handlers._fast_exit_execution_route_fields(
        {
            "is_nxt": True,
            "entry_execution_broker_route": "NXT",
            "entry_execution_cohort": "PREMARKET_KRX_LIKE",
        },
        code,
        _nxt_quote_snapshot(code, premarket_ts),
        now_ts=premarket_ts,
    )
    assert premarket_fields["fast_exit_broker_route"] == "NXT"
    assert premarket_fields["fast_exit_execution_cohort"] == "PREMARKET_KRX_LIKE"
    assert premarket_fields["fast_exit_route_source_quality_blocked"] is False


def test_fast_exit_route_provenance_recognizes_nxt_aftermarket_at_1545():
    code = "123456"
    outside_ts = datetime(2026, 7, 23, 15, 45, tzinfo=handlers._KST).timestamp()

    fields = handlers._fast_exit_execution_route_fields(
        {"is_nxt": True},
        code,
        _exact_nxt_0d_snapshot(code, outside_ts),
        now_ts=outside_ts,
    )

    assert fields["fast_exit_broker_route"] == "NXT"
    assert fields["fast_exit_execution_cohort"] == "NXT"
    assert fields["fast_exit_execution_cohort_resolution"] == (
        "session_and_broker_route_resolved"
    )
    assert fields["fast_exit_route_resolution_reason"] == "nxt_session_nxt_enabled"
    assert fields["fast_exit_execution_session_blocked"] is False
    assert fields["fast_exit_broker_route_blocked"] is False
    assert fields["fast_exit_route_guard_reason"] == "nxt_ws_route_proven"


def test_nxt_aftermarket_early_sell_requires_fresh_exact_nx_executable_bid():
    code = "123456"
    now_ts = datetime(2026, 8, 21, 15, 45, tzinfo=handlers._KST).timestamp()
    stock = {
        "status": "HOLDING",
        "buy_qty": 3,
        "is_nxt": True,
        "entry_execution_broker_route": "NXT",
    }

    fields, exact_view = handlers._nxt_aftermarket_early_sell_quote_context(
        stock,
        code,
        _exact_nxt_0d_snapshot(code, now_ts, bid=10_020, bid_qty=7),
        now_ts=now_ts,
    )

    assert fields["nxt_aftermarket_early_sell_allowed"] is True
    assert fields["nxt_aftermarket_early_sell_reason"] == (
        "fresh_exact_nxt_executable_bid"
    )
    assert fields["nxt_aftermarket_early_sell_quote_item"] == f"{code}_NX"
    assert fields["nxt_aftermarket_early_sell_quote_route"] == "nxt_only"
    assert fields["nxt_aftermarket_early_sell_executable_bid"] == 10_020
    assert fields["nxt_aftermarket_early_sell_executable_bid_qty"] == 7
    assert exact_view["executable_sell_price"] == 10_020
    assert exact_view["orderbook"]["bids"][0]["price"] == 10_020
    assert exact_view["last_realtime_type_market_route"]["0D"] == "nxt_only"


@pytest.mark.parametrize(
    ("now_hhmm", "snapshot_factory", "expected_reason"),
    [
        (
            (15, 44, 59),
            lambda code, now_ts: _exact_nxt_0d_snapshot(code, now_ts),
            "outside_nxt_aftermarket_early_sell_window",
        ),
        (
            (15, 45, 0),
            lambda code, now_ts: _exact_nxt_0d_snapshot(
                code, now_ts, observed_age_ms=1001.0
            ),
            "exact_nxt_0d_stale",
        ),
        (
            (15, 45, 0),
            lambda code, now_ts: _nxt_quote_snapshot(code, now_ts),
            "exact_nxt_0d_missing",
        ),
        (
            (15, 45, 0),
            lambda code, now_ts: _exact_nxt_0d_snapshot(
                code, now_ts, bid=0, bid_qty=20
            ),
            "exact_nxt_executable_bid_missing",
        ),
        (
            (15, 45, 0),
            lambda code, now_ts: _exact_nxt_0d_snapshot(
                code, now_ts, bid=9_800, bid_qty=0
            ),
            "exact_nxt_executable_bid_depth_missing",
        ),
    ],
)
def test_nxt_aftermarket_early_sell_fails_closed_without_exact_fresh_bid(
    now_hhmm,
    snapshot_factory,
    expected_reason,
):
    code = "123456"
    now_ts = datetime(
        2026,
        8,
        21,
        now_hhmm[0],
        now_hhmm[1],
        now_hhmm[2],
        tzinfo=handlers._KST,
    ).timestamp()
    fields, _ = handlers._nxt_aftermarket_early_sell_quote_context(
        {"status": "HOLDING", "buy_qty": 3, "is_nxt": True},
        code,
        snapshot_factory(code, now_ts),
        now_ts=now_ts,
    )

    assert fields["nxt_aftermarket_early_sell_allowed"] is False
    assert fields["nxt_aftermarket_early_sell_reason"] == expected_reason


def test_nxt_aftermarket_early_sell_fails_closed_for_krx_only_holding():
    code = "123456"
    now_ts = datetime(2026, 8, 21, 15, 45, tzinfo=handlers._KST).timestamp()
    fields, _ = handlers._nxt_aftermarket_early_sell_quote_context(
        {"status": "HOLDING", "buy_qty": 3, "is_nxt": False},
        code,
        _exact_nxt_0d_snapshot(code, now_ts),
        now_ts=now_ts,
    )

    assert fields["nxt_aftermarket_early_sell_allowed"] is False
    assert fields["nxt_aftermarket_early_sell_reason"] == "nxt_sell_route_not_proven"


def test_nxt_aftermarket_early_sell_trusts_confirmed_nxt_position_route():
    code = "123456"
    now_ts = datetime(2026, 8, 21, 15, 45, tzinfo=handlers._KST).timestamp()
    fields, _ = handlers._nxt_aftermarket_early_sell_quote_context(
        {
            "status": "HOLDING",
            "buy_qty": 3,
            "is_nxt": False,
            "entry_execution_broker_route": "NXT",
        },
        code,
        _exact_nxt_0d_snapshot(code, now_ts),
        now_ts=now_ts,
    )

    assert fields["nxt_aftermarket_early_sell_allowed"] is True
    assert fields["nxt_aftermarket_early_sell_nxt_flag_source"] == (
        "confirmed_entry_execution_route"
    )
    assert fields["nxt_aftermarket_early_sell_confirmed_nxt_position"] is True


def test_sell_route_guard_blocks_inter_session_gap_even_for_nxt_holding():
    resolution = handlers._resolve_holding_sell_dmst_stex_tp(
        {"is_nxt": True},
        "123456",
        now_t=datetime(2026, 8, 14, 8, 55).time(),
    )

    assert resolution == {
        "blocked": True,
        "dmst_stex_tp": "NXT",
        "nxt_enabled": True,
        "nxt_flag_source": "stock.is_nxt",
        "reason": "outside_supported_sell_execution_session",
    }


def test_fast_exit_evaluator_never_reaches_quote_or_broker_in_inter_session_gap(
    monkeypatch,
):
    now_ts = datetime(2026, 8, 14, 8, 55, tzinfo=handlers._KST).timestamp()
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE", "2026-08-14")
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("blocked session must not reach quote or broker work")
        ),
    )
    stock = {
        "name": "장간격종목",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "is_nxt": True,
        "entry_execution_broker_route": "NXT",
        "entry_execution_cohort": "PREMARKET_KRX_LIKE",
    }

    triggered = handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock,
        "123456",
        _nxt_quote_snapshot("123456", now_ts),
        now_ts=now_ts,
    )

    assert triggered is False
    assert stock["status"] == "HOLDING"
    assert stock.get("exit_token") is None


def test_fast_exit_known_session_routes_do_not_wait_for_nxt_metadata(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "_resolve_holding_sell_dmst_stex_tp",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("known execution routes must not perform metadata lookup")
        ),
    )
    code = "123456"
    regular_ts = datetime(2026, 7, 23, 12, 0, tzinfo=handlers._KST).timestamp()
    regular = handlers._fast_exit_execution_route_fields(
        {}, code, {"curr": 9_800}, now_ts=regular_ts
    )
    assert regular["fast_exit_broker_route"] == "SOR"

    nxt_ts = datetime(2026, 7, 23, 16, 20, tzinfo=handlers._KST).timestamp()
    nxt = handlers._fast_exit_execution_route_fields(
        {
            "status": "HOLDING",
            "buy_qty": 7,
            "entry_execution_broker_route": "NXT",
            "entry_execution_cohort": "NXT",
        },
        code,
        _nxt_quote_snapshot(code, nxt_ts),
        now_ts=nxt_ts,
    )
    assert nxt["fast_exit_broker_route"] == "NXT"
    assert nxt["fast_exit_nxt_flag_source"] == "confirmed_entry_execution_route"


def test_fast_exit_route_guard_blocks_krx_only_and_unproven_nxt_quote():
    code = "123456"
    nxt_ts = datetime(2026, 7, 23, 16, 20, tzinfo=handlers._KST).timestamp()
    krx_only = handlers._fast_exit_execution_route_fields(
        {"is_nxt": False},
        code,
        _nxt_quote_snapshot(code, nxt_ts),
        now_ts=nxt_ts,
    )
    assert krx_only["fast_exit_broker_route_blocked"] is True
    assert krx_only["fast_exit_route_resolution_reason"] == (
        "krx_only_outside_krx_regular_session"
    )

    confirmed_nxt_position = handlers._fast_exit_execution_route_fields(
        {
            "status": "HOLDING",
            "buy_qty": 7,
            "is_nxt": False,
            "entry_execution_broker_route": "NXT",
            "entry_execution_cohort": "PREMARKET_KRX_LIKE",
        },
        code,
        _nxt_quote_snapshot(code, nxt_ts),
        now_ts=nxt_ts,
    )
    assert confirmed_nxt_position["fast_exit_broker_route_blocked"] is False
    assert confirmed_nxt_position["fast_exit_broker_route"] == "NXT"
    assert confirmed_nxt_position["fast_exit_confirmed_nxt_entry_position"] is True
    assert confirmed_nxt_position["fast_exit_route_resolution_reason"] == (
        "confirmed_nxt_entry_position_route"
    )

    unproven = handlers._fast_exit_execution_route_fields(
        {
            "is_nxt": True,
            "entry_execution_broker_route": "NXT",
            "entry_execution_cohort": "NXT",
        },
        code,
        {"curr": 9_800, "best_bid": 9_800, "best_ask": 9_810},
        now_ts=nxt_ts,
    )
    assert unproven["fast_exit_broker_route_blocked"] is False
    assert unproven["fast_exit_route_source_quality_blocked"] is True
    assert unproven["fast_exit_route_guard_reason"] == (
        "nxt_executable_quote_route_unproven"
    )
    assert unproven["fast_exit_ws_0d_route"] == "unknown"
    assert unproven["fast_exit_ws_0d_route_provenance_state"] == "not_available"

    rest_proven = handlers._fast_exit_execution_route_fields(
        {
            "is_nxt": True,
            "entry_execution_broker_route": "NXT",
            "entry_execution_cohort": "NXT",
        },
        code,
        {},
        rest_snapshot={
            "source": "ka10004_rest_orderbook",
            "stock_code": code,
            "request_code": f"{code}_AL",
        },
        now_ts=nxt_ts,
    )
    assert rest_proven["fast_exit_rest_nxt_route_ready"] is True
    assert rest_proven["fast_exit_route_source_quality_blocked"] is False


def test_fast_exit_dispatch_passes_explicit_nxt_route(monkeypatch):
    now_ts = datetime(2026, 7, 23, 16, 20, tzinfo=handlers._KST).timestamp()
    monkeypatch.setattr(handlers, "_remember_exit_context", lambda **kwargs: None)
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers, "_sell_side_open_time_block_fields", lambda **kwargs: {}
    )
    monkeypatch.setattr(handlers, "DB", _CancelDB())
    monkeypatch.setattr(
        handlers,
        "_confirm_cancel_or_reload_remaining",
        lambda *args, **kwargs: 7,
    )
    sells = []
    monkeypatch.setattr(
        handlers,
        "_send_exit_best_ioc",
        lambda code, qty, token, **kwargs: sells.append((code, qty, kwargs))
        or {"return_code": "0", "ord_no": "0000101"},
    )
    stock = {
        "id": 1,
        "name": "NXT종목",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 7,
        "fast_exit_broker_route": "NXT",
        "fast_exit_execution_cohort": "PREMARKET_KRX_LIKE",
        "exit_token": "token-nxt",
        "exit_decided_at": now_ts,
    }

    handlers._dispatch_scalp_preset_exit(
        stock=stock,
        code="123456",
        now_ts=now_ts,
        curr_p=9_800,
        buy_p=10_000,
        profit_rate=-2.0,
        peak_profit=0.8,
        strategy="SCALPING",
        sell_reason_type="LOSS",
        reason="test",
        exit_rule="scalp_trailing_take_profit",
        fast_exit=True,
    )

    assert sells == [
        (
            "123456",
            7,
            {
                "dmst_stex_tp": "NXT",
                "reason_type": "LOSS",
                "strategy": "SCALPING",
            },
        )
    ]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["sell_odno"] == "0000101"
    assert stock["sell_ord_no"] == "0000101"


def test_fast_exit_dispatch_1545_uses_exact_nxt_bid_time_passthrough(monkeypatch):
    now_ts = datetime(2026, 8, 21, 15, 45, tzinfo=handlers._KST).timestamp()
    monkeypatch.setattr(handlers.time, "time", lambda: now_ts)
    monkeypatch.setattr(handlers, "WS_MANAGER", None)
    monkeypatch.setattr(handlers, "DB", _CancelDB())
    monkeypatch.setattr(handlers, "_remember_exit_context", lambda **kwargs: None)
    pipeline_logs = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: pipeline_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        handlers,
        "_sell_side_open_time_block_fields",
        lambda **kwargs: {
            "runtime_family": "sell_side_open_time_block_runtime",
            "policy_version": "sell_side_open_time_block_v1",
            "sell_time_block_checked": True,
            "sell_time_block_applied": True,
            "sell_time_block_passthrough_reason": "-",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_confirm_cancel_or_reload_remaining",
        lambda *args, **kwargs: 3,
    )
    sells = []
    monkeypatch.setattr(
        handlers,
        "_send_exit_best_ioc",
        lambda code, qty, token, **kwargs: sells.append((code, qty, kwargs))
        or {"return_code": "0", "ord_no": "0001545"},
    )
    stock = {
        "id": 1,
        "name": "NXT종목",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 3,
        "is_nxt": True,
        "entry_execution_broker_route": "NXT",
        "fast_exit_broker_route": "NXT",
        "fast_exit_execution_cohort": "NXT",
        "exit_token": "token-nxt-1545",
        "exit_decided_at": now_ts,
    }

    handlers._dispatch_scalp_preset_exit(
        stock=stock,
        code="123456",
        now_ts=now_ts,
        curr_p=10_100,
        buy_p=10_000,
        profit_rate=1.0,
        peak_profit=2.0,
        strategy="SCALPING",
        sell_reason_type="TRAILING",
        reason="test NXT 15:45 trailing",
        exit_rule="scalp_trailing_take_profit",
        ws_data=_exact_nxt_0d_snapshot("123456", now_ts, bid=10_090, bid_qty=10),
        fast_exit=True,
    )

    assert sells == [
        (
            "123456",
            3,
            {
                "dmst_stex_tp": "NXT",
                "reason_type": "TRAILING",
                "strategy": "SCALPING",
                "bypass_open_time_block": True,
            },
        )
    ]
    assert not [
        fields
        for stage, fields in pipeline_logs
        if stage == "sell_order_blocked_open_time"
    ]
    passthrough = [
        fields
        for stage, fields in pipeline_logs
        if stage == "nxt_aftermarket_early_sell_passthrough"
    ]
    assert passthrough
    assert passthrough[-1]["nxt_aftermarket_early_sell_executable_bid"] == 10_090
    sent = [fields for stage, fields in pipeline_logs if stage == "sell_order_sent"]
    assert sent[-1]["sell_time_block_passthrough_reason"] == (
        "nxt_aftermarket_fresh_executable_bid"
    )


def test_fast_exit_dispatch_1545_blocks_when_final_nxt_bid_turns_stale(monkeypatch):
    now_ts = datetime(2026, 8, 21, 15, 45, tzinfo=handlers._KST).timestamp()
    monkeypatch.setattr(handlers.time, "time", lambda: now_ts)

    class StaleFinalQuoteManager:
        @staticmethod
        def get_latest_data(code):
            return _exact_nxt_0d_snapshot(
                code,
                now_ts,
                observed_age_ms=1001.0,
                bid=10_080,
                bid_qty=10,
            )

    monkeypatch.setattr(handlers, "WS_MANAGER", StaleFinalQuoteManager())
    monkeypatch.setattr(handlers, "_remember_exit_context", lambda **kwargs: None)
    pipeline_logs = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: pipeline_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        handlers,
        "_sell_side_open_time_block_fields",
        lambda **kwargs: {
            "sell_time_block_applied": True,
            "sell_time_block_passthrough_reason": "-",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_confirm_cancel_or_reload_remaining",
        lambda *args, **kwargs: 3,
    )
    sells = []
    monkeypatch.setattr(
        handlers,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: sells.append((args, kwargs)),
    )
    stock = {
        "name": "NXT종목",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 3,
        "is_nxt": True,
        "entry_execution_broker_route": "NXT",
        "fast_exit_broker_route": "NXT",
        "fast_exit_execution_cohort": "NXT",
        "exit_token": "token-nxt-stale",
        "exit_decided_at": now_ts,
    }

    handlers._dispatch_scalp_preset_exit(
        stock=stock,
        code="123456",
        now_ts=now_ts,
        curr_p=10_100,
        buy_p=10_000,
        profit_rate=1.0,
        peak_profit=2.0,
        strategy="SCALPING",
        sell_reason_type="TRAILING",
        reason="test stale final NXT bid",
        exit_rule="scalp_trailing_take_profit",
        ws_data=_exact_nxt_0d_snapshot("123456", now_ts, bid=10_090, bid_qty=10),
        fast_exit=True,
    )

    assert sells == []
    assert stock["status"] == "HOLDING"
    blocked = [
        fields
        for stage, fields in pipeline_logs
        if stage == "nxt_aftermarket_early_sell_pre_submit_blocked"
    ]
    assert blocked[-1]["nxt_aftermarket_early_sell_reason"] == ("exact_nxt_0d_stale")


def test_fast_exit_broker_reject_uses_shared_sell_backoff(monkeypatch):
    now_ts = datetime(2026, 8, 14, 16, 20, tzinfo=handlers._KST).timestamp()
    monkeypatch.setattr(handlers, "_remember_exit_context", lambda **kwargs: None)
    monkeypatch.setattr(handlers, "DB", _CancelDB())
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers, "_sell_side_open_time_block_fields", lambda **kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_confirm_cancel_or_reload_remaining",
        lambda *args, **kwargs: 7,
    )
    monkeypatch.setattr(
        handlers,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: {
            "return_code": "2000",
            "return_msg": "[2000](505217:휴장시간으로 취소주문만 가능합니다.)",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_rule_bool",
        lambda name, default=False: (
            True if name == "SELL_ORDER_FAILURE_RETRY_BACKOFF_ENABLED" else default
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_rule_int",
        lambda name, default=0: (
            30 if name == "SELL_ORDER_FAILURE_RETRY_BACKOFF_SEC" else default
        ),
    )
    stock = {
        "id": 1,
        "name": "NXT종목",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 7,
        "fast_exit_broker_route": "NXT",
        "exit_token": "token-reject",
        "exit_decided_at": now_ts,
    }

    handlers._dispatch_scalp_preset_exit(
        stock=stock,
        code="123456",
        now_ts=now_ts,
        curr_p=9_800,
        buy_p=10_000,
        profit_rate=-2.0,
        peak_profit=0.8,
        strategy="SCALPING",
        sell_reason_type="LOSS",
        reason="test",
        exit_rule="scalp_hard_stop_pct",
        fast_exit=True,
    )

    assert stock["status"] == "HOLDING"
    assert stock["fast_exit_retry_pending"] is True
    assert stock["fast_exit_retry_at"] == pytest.approx(now_ts + 30.0)
    assert stock["sell_order_retry_backoff_until_ts"] == pytest.approx(now_ts + 30.0)
    assert stock["sell_order_failure_count"] == 1


def test_shared_exit_wrapper_preserves_explicit_route_and_guard_context(monkeypatch):
    calls = []
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "send_sell_order_market",
        lambda **kwargs: calls.append(kwargs) or {"return_code": "0"},
    )

    sniper_trade_utils.send_exit_best_ioc(
        "123456",
        7,
        "token",
        dmst_stex_tp="NXT",
        reason_type="LOSS",
        strategy="SCALPING",
    )

    assert calls == [
        {
            "code": "123456",
            "qty": 7,
            "token": "token",
            "order_type": "16",
            "dmst_stex_tp": "NXT",
            "reason_type": "LOSS",
            "strategy": "SCALPING",
        }
    ]


def test_shared_exit_wrapper_forwards_proven_time_block_bypass(monkeypatch):
    calls = []
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "send_sell_order_market",
        lambda **kwargs: calls.append(kwargs) or {"return_code": "0"},
    )

    sniper_trade_utils.send_exit_best_ioc(
        "123456",
        3,
        "token",
        dmst_stex_tp="NXT",
        reason_type="TRAILING",
        strategy="SCALPING",
        bypass_open_time_block=True,
    )

    assert calls[-1]["dmst_stex_tp"] == "NXT"
    assert calls[-1]["bypass_open_time_block"] is True


def test_handler_exit_wrapper_preserves_legacy_three_argument_dependency(monkeypatch):
    calls = []
    monkeypatch.setattr(
        handlers,
        "SEND_EXIT_BEST_IOC",
        lambda code, qty, token: calls.append((code, qty, token))
        or {"return_code": "0"},
    )

    handlers._send_exit_best_ioc("123456", 3, "token")

    assert calls == [("123456", 3, "token")]


class _CancelQuery:
    def __init__(self, updates):
        self.updates = updates

    def filter_by(self, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def update(self, values):
        self.updates.append(dict(values))
        return 1

    def first(self):
        return object()


class _CancelSession:
    def __init__(self, updates):
        self.updates = updates

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, model):
        return _CancelQuery(self.updates)


class _CancelDB:
    def __init__(self):
        self.updates = []

    def get_session(self):
        return _CancelSession(self.updates)


def test_sell_timeout_without_order_number_keeps_claim_until_reconciled(monkeypatch):
    monkeypatch.setattr(handlers.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(
        handlers,
        "_rule_int",
        lambda name, default=0: {
            "SELL_TIMEOUT_SEC": 40,
            "SELL_ORDER_FAILURE_RETRY_BACKOFF_SEC": 30,
        }.get(name, default),
    )
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "log_error", lambda *args, **kwargs: None)
    db = _CancelDB()
    monkeypatch.setattr(handlers, "DB", db)
    stock = {
        "id": 1,
        "name": "주문번호미확인",
        "status": "SELL_ORDERED",
        "buy_qty": 3,
        "sell_order_time": 900.0,
        "exit_token": "exit-unknown-order",
        "exit_requested": True,
    }

    handlers.handle_sell_ordered_state(stock, "123456")

    assert stock["status"] == "SELL_ORDERED"
    assert stock["exit_token"] == "exit-unknown-order"
    assert stock["exit_requested"] is True
    assert stock["sell_cancel_reconciliation_required"] is True
    assert stock["sell_cancel_reconciliation_retry_at"] == 1_030.0
    assert db.updates == [{"status": "SELL_ORDERED"}]


@pytest.mark.parametrize("recovery_succeeds", [False, True])
def test_sell_timeout_never_cancels_while_tp1_lifecycle_release_is_pending(
    monkeypatch,
    recovery_succeeds,
):
    from src.engine import sniper_execution_receipts as receipts

    monkeypatch.setattr(handlers.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(
        handlers,
        "_rule_int",
        lambda name, default=0: {
            "SELL_TIMEOUT_SEC": 40,
            "SELL_ORDER_FAILURE_RETRY_BACKOFF_SEC": 30,
        }.get(name, default),
    )
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *a, **k: False
    )
    cancel_calls = []
    monkeypatch.setattr(
        handlers,
        "process_sell_cancellation",
        lambda *args, **kwargs: cancel_calls.append((args, kwargs)),
    )
    stock = {
        "id": 1,
        "name": "TP1",
        "status": "SELL_ORDERED",
        "sell_odno": "0000001",
        "sell_order_time": 900.0,
        "_sell_execution_receipt_state": {
            "nxt_tp1_completion_runtime_release_pending": True,
            "pending_partial_lifecycle_legs": {"leg": {}},
        },
    }

    def _recover(target):
        if not recovery_succeeds:
            return False
        target["_sell_execution_receipt_state"] = {
            "partial_order_kind": "nxt_rising_missed_tp1"
        }
        target["status"] = "HOLDING"
        return True

    monkeypatch.setattr(receipts, "recover_pending_sell_lifecycle_outbox", _recover)

    handlers.handle_sell_ordered_state(stock, "123456")

    assert cancel_calls == []
    if recovery_succeeds:
        assert stock["status"] == "HOLDING"
    else:
        assert stock["status"] == "SELL_ORDERED"
        assert stock["sell_cancel_reconciliation_required"] is True
        assert stock["sell_cancel_reconciliation_retry_at"] == 1_030.0


def _ambiguous_cancel_response():
    return {
        "return_code": "2000",
        "return_msg": "[2000](506550:취소가능수량이 없습니다.)",
    }


def _persist_exact_sell_cancel_generation(
    stock,
    *,
    code="123456",
    order_no="0000001",
):
    from src.engine import sniper_execution_receipts as receipts

    stock.update(
        {
            "code": code,
            "status": "SELL_ORDERED",
            "sell_odno": order_no,
        }
    )
    stock.update(
        handlers._new_sell_submit_context_fields(
            stock,
            code,
            requested_qty=int(stock["buy_qty"]),
            started_at=handlers.time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(stock)


def test_sell_cancel_exact_success_releases_generation_after_db_commit(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts

    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: _exact_cancel_ack_response(),
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([{"code": "123456", "qty": 7}], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        handlers,
        "_sell_order_terminal_absence_confirmed",
        lambda code, order_no: (True, "exact_order_absent"),
    )
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *a, **k: None)
    db = _CancelDB()
    stock = {
        "id": 1,
        "code": "123456",
        "name": "정상취소",
        "status": "SELL_ORDERED",
        "buy_qty": 7,
        "sell_odno": "0000001",
    }
    stock.update(
        handlers._new_sell_submit_context_fields(
            stock,
            stock["code"],
            requested_qty=7,
            started_at=handlers.time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    generation = stock["sell_submit_generation"]
    assert receipts.persist_pending_sell_submit_custody(stock)

    assert handlers.process_sell_cancellation(stock, stock["code"], "0000001", db)
    assert stock["status"] == "HOLDING"
    assert "sell_odno" not in stock
    assert "sell_submit_generation" not in stock
    assert not receipts._sell_pending_submit_path(stock["id"]).exists()
    assert db.updates[0]["status"] == "HOLDING"
    assert generation


def test_sell_cancel_ack_is_durable_and_reused_until_terminal_absence(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts

    cancel_calls = []
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or _exact_cancel_ack_response(orig_order_no=kwargs["orig_ord_no"]),
    )
    terminal_results = iter(
        (
            (False, "sell_order_still_open"),
            (True, "ka10075_terminal_absence_confirmed"),
        )
    )
    monkeypatch.setattr(
        handlers,
        "_sell_order_terminal_absence_confirmed",
        lambda code, order_no: next(terminal_results),
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([{"code": "123456", "qty": 7}], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *a, **k: None)
    db = _CancelDB()
    stock = {
        "id": 2,
        "code": "123456",
        "name": "지연취소",
        "status": "SELL_ORDERED",
        "buy_qty": 7,
        "sell_odno": "0000002",
    }
    stock.update(
        handlers._new_sell_submit_context_fields(
            stock,
            "123456",
            requested_qty=7,
            started_at=handlers.time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    generation = stock["sell_submit_generation"]
    assert receipts.persist_pending_sell_submit_custody(stock)

    assert not handlers.process_sell_cancellation(
        stock,
        "123456",
        "0000002",
        db,
    )
    assert stock["status"] == "SELL_ORDERED"
    assert stock["sell_cancel_ack_generation"] == generation
    assert receipts.pending_sell_cancel_ack_exact(
        stock,
        code="123456",
        order_no="0000002",
    )

    assert handlers.process_sell_cancellation(
        stock,
        "123456",
        "0000002",
        db,
    )
    assert len(cancel_calls) == 1
    assert stock["status"] == "HOLDING"
    assert "sell_submit_generation" not in stock
    assert not receipts._sell_pending_submit_path(stock["id"]).exists()


@pytest.mark.parametrize("cancel_response", [None, True, "ok", {"return_code": False}])
def test_sell_cancel_non_dict_or_bool_response_never_releases_order(
    monkeypatch,
    cancel_response,
):
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_response,
    )
    terminal_calls = []
    monkeypatch.setattr(
        handlers,
        "_sell_order_terminal_absence_confirmed",
        lambda *args: terminal_calls.append(args) or (True, "absent"),
    )
    stock = {
        "id": 1,
        "name": "취소불명",
        "status": "SELL_ORDERED",
        "buy_qty": 7,
        "sell_odno": "0000001",
    }
    db = _CancelDB()

    assert not handlers.process_sell_cancellation(stock, "123456", "0000001", db)
    assert stock["status"] == "SELL_ORDERED"
    assert stock["sell_odno"] == "0000001"
    assert terminal_calls == []
    assert db.updates == []


def test_sell_cancel_error_releases_only_after_exact_intent_and_terminal_proof(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: _ambiguous_cancel_response(),
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([{"code": "123456", "qty": 7}], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        handlers,
        "_sell_order_terminal_absence_confirmed",
        lambda code, order_no: (True, "ka10075_terminal_absence_confirmed"),
    )
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "log_error", lambda *args, **kwargs: None)
    db = _CancelDB()
    stock = {
        "id": 1,
        "name": "잔고종목",
        "status": "SELL_ORDERED",
        "buy_qty": 7,
        "sell_odno": "0000001",
        "sell_order_time": 100.0,
        "exit_token": "exit-positive",
        "exit_requested": True,
    }
    _persist_exact_sell_cancel_generation(stock)

    handlers.process_sell_cancellation(stock, "123456", "0000001", db)

    assert stock["status"] == "HOLDING"
    assert stock["buy_qty"] == 7
    assert "sell_odno" not in stock
    assert "exit_token" not in stock
    assert stock["exit_requested"] is False
    assert "sell_cancel_reconciliation_required" not in stock
    assert db.updates[0]["status"] == "HOLDING"


def test_sell_cancel_error_all_venue_zero_still_requires_exact_receipt(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: _ambiguous_cancel_response(),
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        handlers,
        "_sell_order_terminal_absence_confirmed",
        lambda code, order_no: (True, "ka10075_terminal_absence_confirmed"),
    )
    monkeypatch.setattr(handlers, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "HIGHEST_PRICES", {"123456": 10_100})
    db = _CancelDB()
    stock = {
        "id": 1,
        "name": "체결종목",
        "status": "SELL_ORDERED",
        "buy_qty": 7,
        "sell_odno": "0000001",
        "sell_order_time": 100.0,
    }
    _persist_exact_sell_cancel_generation(stock)

    handlers.process_sell_cancellation(stock, "123456", "0000001", db)

    assert stock["status"] == "SELL_ORDERED"
    assert stock["sell_odno"] == "0000001"
    assert stock["sell_cancel_reconciliation_required"] is True
    assert (
        stock["sell_cancel_reconciliation_source"]
        == "zero_inventory_exact_receipt_required"
    )
    assert "123456" in handlers.HIGHEST_PRICES
    assert db.updates == []


def test_sell_cancel_error_with_partial_inventory_evidence_stays_sell_ordered(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: _ambiguous_cancel_response(),
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([], {"KRX"}),
    )
    monkeypatch.setattr(
        handlers,
        "_sell_order_terminal_absence_confirmed",
        lambda code, order_no: (True, "ka10075_terminal_absence_confirmed"),
    )
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(
        handlers,
        "_rule_int",
        lambda name, default=0: (
            30 if name == "SELL_ORDER_FAILURE_RETRY_BACKOFF_SEC" else default
        ),
    )
    db = _CancelDB()
    stock = {
        "id": 1,
        "name": "미확인종목",
        "status": "SELL_ORDERED",
        "buy_qty": 7,
        "sell_odno": "0000001",
        "sell_order_time": 100.0,
    }
    _persist_exact_sell_cancel_generation(stock)

    handlers.process_sell_cancellation(stock, "123456", "0000001", db)

    assert stock["status"] == "SELL_ORDERED"
    assert stock["sell_cancel_reconciliation_required"] is True
    assert stock["sell_cancel_reconciliation_retry_at"] == 1_030.0
    assert stock["sell_odno"] == "0000001"
    assert db.updates == []
