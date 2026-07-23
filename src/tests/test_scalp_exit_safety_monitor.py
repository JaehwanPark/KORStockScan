from datetime import datetime
import threading

from src.engine import sniper_state_handlers as handlers
from src.engine import sniper_trade_utils
from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor


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
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
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


def test_fast_exit_retries_cancel_with_same_token_before_single_sell(monkeypatch):
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
    monkeypatch.setattr(handlers, "_holding_score_role_log_fields", lambda context: {})
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "_remember_exit_context", lambda **kwargs: None)
    monkeypatch.setattr(
        handlers, "_early_volatility_tp_order_unresolved", lambda stock: True
    )
    cancel_results = iter([False, True])
    monkeypatch.setattr(
        handlers,
        "_cancel_early_volatility_tp",
        lambda *args, **kwargs: next(cancel_results),
    )
    monkeypatch.setattr(
        handlers, "_sell_side_open_time_block_fields", lambda **kwargs: {}
    )
    monkeypatch.setattr(
        handlers,
        "_confirm_cancel_or_reload_remaining",
        lambda *args, **kwargs: 94,
    )
    sells = []
    monkeypatch.setattr(
        handlers,
        "_send_exit_best_ioc",
        lambda code, qty, token, **kwargs: sells.append((code, qty, kwargs))
        or {"return_code": "0", "ord_no": "S1"},
    )
    handlers.HIGHEST_PRICES = {"123456": 10_077}
    stock = {
        "name": "금호건설",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 94,
        "early_volatility_tp_state": "OPEN",
    }

    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock, "123456", {"curr": 9_800}, now_ts=now_ts
    )
    claimed_token = stock["exit_token"]
    assert sells == []
    assert stock["status"] == "HOLDING"
    assert stock.get("fast_exit_retry_pending") is True, stock

    assert (
        handlers.evaluate_and_dispatch_fast_scalp_exit(
            stock, "123456", {"curr": 9_800}, now_ts=now_ts + 0.1
        )
        is False
    )
    assert sells == []

    # A claimed exit remains authoritative after reconciliation even when the
    # current tick no longer crosses the original trailing threshold.
    handlers.HIGHEST_PRICES = {"123456": 9_800}
    assert handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock, "123456", {"curr": 9_800}, now_ts=now_ts + 0.3
    )
    assert stock["exit_token"] == claimed_token
    assert sells == [
        (
            "123456",
            94,
            {
                "dmst_stex_tp": "SOR",
                "reason_type": "LOSS",
                "strategy": "SCALPING",
            },
        )
    ]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["fast_exit_retry_pending"] is False


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


def test_fast_exit_route_guard_resolves_nxt_and_premarket_as_nxt():
    code = "123456"
    nxt_ts = datetime(
        2026, 7, 23, 16, 20, tzinfo=handlers._KST
    ).timestamp()
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
    assert nxt_fields["fast_exit_ws_nxt_route_ready"] is True
    assert nxt_fields["fast_exit_route_source_quality_blocked"] is False

    premarket_ts = datetime(
        2026, 7, 23, 8, 30, tzinfo=handlers._KST
    ).timestamp()
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
    assert (
        premarket_fields["fast_exit_execution_cohort"]
        == "PREMARKET_KRX_LIKE"
    )
    assert premarket_fields["fast_exit_route_source_quality_blocked"] is False


def test_fast_exit_known_session_routes_do_not_wait_for_nxt_metadata(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "_resolve_holding_sell_dmst_stex_tp",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("known execution routes must not perform metadata lookup")
        ),
    )
    code = "123456"
    regular_ts = datetime(
        2026, 7, 23, 12, 0, tzinfo=handlers._KST
    ).timestamp()
    regular = handlers._fast_exit_execution_route_fields(
        {}, code, {"curr": 9_800}, now_ts=regular_ts
    )
    assert regular["fast_exit_broker_route"] == "SOR"

    nxt_ts = datetime(
        2026, 7, 23, 16, 20, tzinfo=handlers._KST
    ).timestamp()
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
    nxt_ts = datetime(
        2026, 7, 23, 16, 20, tzinfo=handlers._KST
    ).timestamp()
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
    now_ts = datetime(
        2026, 7, 23, 16, 20, tzinfo=handlers._KST
    ).timestamp()
    monkeypatch.setattr(handlers, "_remember_exit_context", lambda **kwargs: None)
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers, "_early_volatility_tp_order_unresolved", lambda stock: False
    )
    monkeypatch.setattr(
        handlers, "_sell_side_open_time_block_fields", lambda **kwargs: {}
    )
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
        or {"return_code": "0", "ord_no": "NXT-S1"},
    )
    stock = {
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
