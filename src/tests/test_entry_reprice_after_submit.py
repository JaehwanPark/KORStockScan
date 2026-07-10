import time

from src.engine.scalping.entry_reprice_after_submit import evaluate_entry_reprice_after_submit


def _base_order(**overrides):
    order = {
        "ord_no": "0033470",
        "qty": 49,
        "filled_qty": 0,
        "price": 39750,
        "status": "OPEN",
        "order_type": "00",
        "entry_reprice_attempt_count": 0,
        "ai_score": 81.0,
        "entry_reprice_action": "BUY_DEFENSIVE",
        "entry_adm_recommended_action": "BUY_DEFENSIVE",
        "entry_adm_ev_pct": 0.12,
        "lifecycle_matrix_selected_action": "BUY_DEFENSIVE",
        "buy_pressure_10t": 91.0,
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 3,
        "latency_state": "SAFE",
        "mark_price_at_submit": 39885,
    }
    order.update(overrides)
    return order


def test_pending_reprice_config_reads_score_and_pressure_env(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_REPRICE_AFTER_SUBMIT_STRONG_SCORE_FLOOR", "60")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_REPRICE_AFTER_SUBMIT_STRONG_BUY_PRESSURE", "50")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_REPRICE_AFTER_SUBMIT_TIGHT_SPREAD_TICKS", "3")

    config = handlers._entry_reprice_config()

    assert config["strong_score_floor"] == 60.0
    assert config["strong_buy_pressure"] == 50.0
    assert config["tight_spread_ticks"] == 3


def test_helper_allows_tight_spread_continuation_without_negative_adm():
    decision = evaluate_entry_reprice_after_submit(
        order=_base_order(),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=120.0,
        orderbook_micro_state="neutral",
    )

    assert decision.allowed is True
    assert decision.target_price > 39750
    assert decision.target_price <= 39915
    assert decision.fields["reprice_price_mode"] == "tight_spread_best_ask_minus_1tick"


def test_helper_blocks_negative_adm_even_when_continuation_report_candidate():
    decision = evaluate_entry_reprice_after_submit(
        order=_base_order(entry_adm_recommended_action="NO_BUY_AI", entry_adm_ev_pct=-0.37),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=120.0,
        orderbook_micro_state="neutral",
    )

    assert decision.allowed is False
    assert decision.reason == "continuation_override_candidate_report_only"
    assert decision.fields["reprice_candidate"] == "continuation_override_candidate"


def test_helper_does_not_use_untrusted_pressure_for_continuation_candidate():
    decision = evaluate_entry_reprice_after_submit(
        order=_base_order(
            entry_adm_recommended_action="NO_BUY_AI",
            entry_adm_ev_pct=-0.37,
            tick_aggressor_pressure_usable=False,
            tick_aggressor_trusted_count=0,
        ),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=120.0,
        orderbook_micro_state="neutral",
    )

    assert decision.allowed is False
    assert decision.reason == "adm_negative_prior"
    assert decision.fields["tick_aggressor_pressure_usable"] is False
    assert decision.fields["tick_aggressor_trusted_count"] == 0


def test_helper_blocks_weak_462900_like_negative_adm():
    decision = evaluate_entry_reprice_after_submit(
        order=_base_order(
            price=16830,
            ai_score=78.0,
            entry_adm_recommended_action="NO_BUY_AI",
            entry_adm_ev_pct=-0.37,
            buy_pressure_10t=56.0,
            mark_price_at_submit=16875,
        ),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=16845,
        best_ask=16895,
        current_price=16880,
        quote_age_ms=100.0,
        max_spread_bps=40,
        orderbook_micro_state="neutral",
    )

    assert decision.allowed is False
    assert decision.reason == "adm_negative_prior"


def test_helper_blocks_safety_and_scope_cases():
    stale = evaluate_entry_reprice_after_submit(
        order=_base_order(),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=1000.0,
    )
    partial = evaluate_entry_reprice_after_submit(
        order=_base_order(filled_qty=1),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=100.0,
    )
    attempt_limit = evaluate_entry_reprice_after_submit(
        order=_base_order(entry_reprice_attempt_count=1),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=100.0,
    )
    non_scalping = evaluate_entry_reprice_after_submit(
        order=_base_order(),
        strategy="KOSPI_ML",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=100.0,
    )

    assert stale.reason == "quote_stale"
    assert partial.reason == "partial_fill"
    assert attempt_limit.reason == "attempt_limit"
    assert non_scalping.reason == "non_scalping"


def test_helper_blocks_latency_danger():
    decision = evaluate_entry_reprice_after_submit(
        order=_base_order(latency_state="DANGER"),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=39855,
        best_ask=39915,
        current_price=39900,
        quote_age_ms=100.0,
        orderbook_micro_state="neutral",
    )

    assert decision.allowed is False
    assert decision.reason == "latency_state_not_safe"


def test_helper_enforces_best_ask_and_upward_cap():
    decision = evaluate_entry_reprice_after_submit(
        order=_base_order(price=10000, mark_price_at_submit=10000),
        strategy="SCALPING",
        elapsed_sec=16.0,
        best_bid=10070,
        best_ask=10120,
        current_price=10100,
        quote_age_ms=100.0,
        max_upward_bps=40,
        max_spread_bps=60,
        orderbook_micro_state="neutral",
    )

    assert decision.allowed is True
    assert decision.target_price <= 10040
    assert decision.target_price <= 10120


def test_pending_order_reprices_once(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "id": 1,
        "name": "테스트",
        "strategy": "SCALPING",
        "order_time": now - 16.0,
        "pending_entry_orders": [
            {
                **_base_order(sent_at=now - 16.0),
                "tag": "normal",
                "tif": "DAY",
                "best_bid_at_submit": 39700,
                "best_ask_at_submit": 39915,
            }
        ],
    }
    events = []
    calls = {"cancel": 0, "buy": 0}
    cancel_calls = []

    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: (
            cancel_calls.append(kwargs)
            or calls.__setitem__("cancel", calls["cancel"] + 1)
            or {"return_code": "0", "ord_no": "0033622"}
        ),
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: calls.__setitem__("buy", calls["buy"] + 1) or {"return_code": "0", "ord_no": "0034000"},
    )

    result = handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60)

    assert result == "submitted"
    assert calls == {"cancel": 1, "buy": 1}
    assert cancel_calls[-1]["dmst_stex_tp"] == "SOR"
    assert stock["pending_entry_orders"][0]["ord_no"] == "0034000"
    assert stock["pending_entry_orders"][0]["dmst_stex_tp"] == "SOR"
    assert stock["pending_entry_orders"][0]["entry_reprice_parent_ord_no"] == "0033470"
    assert stock["entry_reprice_child_ord_no"] == "0034000"
    assert "entry_reprice_resubmit_submitted" in [stage for stage, _ in events]


def test_pending_order_before_eval_window_does_not_call_broker(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 14.0), "tif": "DAY"}],
    }
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "not_due"


def test_pending_order_cancel_failure_does_not_resubmit(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0), "tif": "DAY"}],
    }
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: {"return_code": "1", "return_msg": "fail"})
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "failed"
    assert stock["pending_entry_orders"][0]["entry_reprice_block_reason"] == "cancel_failed"


def test_pending_order_uses_current_observer_latency_not_submit_latency(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0, latency_state="SAFE"), "tif": "DAY"}],
    }
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": False,
            "observer_missing_reason": "stale_quote",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "blocked"
    assert stock["entry_reprice_block_reason"] == "latency_state_not_safe"
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    assert evaluated["latency_state"] == "DANGER"


def test_pending_order_intraday_discovery_relieves_reprice_latency_danger(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "이수페타시스",
        "strategy": "SCALPING",
        "current_price_observed": 104900,
        "pending_entry_orders": [
            {
                **_base_order(
                    sent_at=now - 26.0,
                    ord_no="0036283",
                    qty=1,
                    price=104500,
                    ai_score=70.0,
                    buy_pressure_10t=98.26,
                    tick_aggressor_trusted_count=10,
                    mark_price_at_submit=104600,
                ),
                "tag": "normal",
                "tif": "DAY",
            }
        ],
    }
    events = []
    cancel_calls = []
    buy_calls = []
    snapshot = {
        "best_bid": 104800,
        "best_ask": 105200,
        "last_trade_price": 104600,
        "observer_healthy": False,
        "observer_missing_reason": "stale_quote",
        "unstable_quote_observed": False,
        "observer_last_quote_age_ms": 462.5,
        "orderbook_micro": {"micro_state": "neutral"},
    }
    quote_fields = {
        "entry_reprice_quote_refresh_enabled": True,
        "entry_reprice_quote_refresh_applied": False,
        "entry_reprice_quote_refresh_source": "none",
        "entry_reprice_quote_refresh_reason": "rest_best_levels_invalid",
        "quote_consistency_family": "quote_consistency_normalization",
        "quote_consistency_state": "ok",
        "quote_consistency_runtime_action": "allow",
        "quote_consistency_age_ms": 0.114,
        "quote_consistency_ws_age_ms": 522.179,
        "quote_consistency_rest_age_ms": 0.114,
        "quote_consistency_entry_blocked": False,
    }

    monkeypatch.setenv("KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED", "true")
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(handlers.ORDERBOOK_STABILITY_OBSERVER, "snapshot", lambda code, now=None: dict(snapshot))
    monkeypatch.setattr(
        handlers,
        "_entry_reprice_refresh_snapshot",
        lambda code, snapshot_arg, stock_arg, order_arg, strategy_arg, now_ts: (dict(snapshot), dict(quote_fields)),
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs) or {"return_code": "0", "ord_no": "0036413"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: buy_calls.append((args, kwargs)) or {"return_code": "0", "ord_no": "0037000"},
    )

    assert handlers._maybe_reprice_pending_entry_order(stock, "007660", "SCALPING", timeout_sec=60) == "submitted"
    assert cancel_calls[-1]["orig_ord_no"] == "0036283"
    assert buy_calls[-1][0][2] == 104800
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    assert evaluated["entry_reprice_operator_latency_relief_applied"] is True
    assert evaluated["entry_reprice_latency_state_original"] == "DANGER"
    assert evaluated["entry_reprice_latency_state_effective"] == "CAUTION"
    assert evaluated["latency_state"] == "CAUTION"
    assert evaluated["reprice_order_price"] == 104800
    cancel_event = [fields for stage, fields in events if stage == "entry_reprice_cancel_requested"][0]
    assert cancel_event["entry_reprice_operator_latency_relief_applied"] is True
    assert cancel_event["entry_reprice_latency_state_original"] == "DANGER"
    assert cancel_event["entry_reprice_latency_state_effective"] == "CAUTION"
    submitted_event = [fields for stage, fields in events if stage == "entry_reprice_resubmit_submitted"][0]
    assert submitted_event["entry_reprice_operator_latency_relief_applied"] is True
    assert submitted_event["entry_reprice_latency_state_original"] == "DANGER"
    assert submitted_event["entry_reprice_latency_state_effective"] == "CAUTION"
    child_order = stock["pending_entry_orders"][0]
    assert child_order["entry_reprice_operator_latency_relief_applied"] is True
    assert child_order["entry_reprice_latency_state_original"] == "DANGER"
    assert child_order["entry_reprice_latency_state_effective"] == "CAUTION"


def test_pending_order_missing_trade_with_fresh_quote_is_caution(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0, latency_state="SAFE"), "tif": "DAY"}],
    }
    calls = {"cancel": 0, "buy": 0}
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": False,
            "observer_missing_reason": "missing_trade",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: calls.__setitem__("cancel", calls["cancel"] + 1) or {"return_code": "0", "ord_no": "0033622"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: calls.__setitem__("buy", calls["buy"] + 1) or {"return_code": "0", "ord_no": "0034000"},
    )

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "submitted"
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    assert evaluated["latency_state"] == "CAUTION"
    assert calls == {"cancel": 1, "buy": 1}


def test_pending_order_missing_quote_blocks_as_danger(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0, latency_state="SAFE"), "tif": "DAY"}],
    }
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 0,
            "best_ask": 0,
            "observer_healthy": False,
            "observer_missing_reason": "missing_quote",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": None,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "blocked"
    assert stock["entry_reprice_block_reason"] == "invalid_quote"
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    assert evaluated["latency_state"] == "DANGER"


def test_pending_order_quote_stale_remains_retryable(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0, latency_state="SAFE"), "tif": "DAY"}],
    }
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "observer_missing_reason": "ok",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 1000.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "blocked"
    assert "entry_reprice_evaluated" not in stock
    assert "entry_reprice_evaluated" not in stock["pending_entry_orders"][0]


def test_pending_order_refreshes_stale_observer_quote_from_ws(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "latest_price": 39900,
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0), "tif": "DAY"}],
    }
    events = []
    calls = {"cancel": 0, "buy": 0}

    class FakeWsManager:
        @staticmethod
        def get_latest_data(code):
            return {
                "curr": 39900,
                "best_bid": 39855,
                "best_ask": 39915,
                "last_ws_update_ts": now - 0.12,
                "orderbook": {
                    "asks": [{"price": 39915}],
                    "bids": [{"price": 39855}],
                },
            }

    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(handlers, "WS_MANAGER", FakeWsManager())
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "observer_missing_reason": "ok",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 4300.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: calls.__setitem__("cancel", calls["cancel"] + 1) or {"return_code": "0", "ord_no": "0033622"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: calls.__setitem__("buy", calls["buy"] + 1) or {"return_code": "0", "ord_no": "0034000"},
    )

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "submitted"
    assert calls == {"cancel": 1, "buy": 1}
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    assert evaluated["entry_reprice_quote_refresh_applied"] is True
    assert evaluated["entry_reprice_quote_refresh_source"] == "ws_manager_latest_data"
    assert float(evaluated["quote_age_ms"]) == 120.0


def test_pending_order_multi_leg_compresses_to_single_child(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [
            {**_base_order(sent_at=now - 16.0, ord_no="0033470", qty=3, price=39750), "tag": "entry_split_primary", "tif": "DAY"},
            {**_base_order(sent_at=now - 16.0, ord_no="0033471", qty=11, price=39700), "tag": "entry_split_passive_1", "tif": "DAY"},
        ],
    }
    events = []
    cancel_calls = []
    buy_calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs) or {"return_code": "0", "ord_no": f"C{len(cancel_calls)}"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: buy_calls.append((args, kwargs)) or {"return_code": "0", "ord_no": "0034000"},
    )

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "submitted"
    assert [call["orig_ord_no"] for call in cancel_calls] == ["0033470", "0033471"]
    assert buy_calls[0][0][1] == 14
    assert len(stock["pending_entry_orders"]) == 1
    child = stock["pending_entry_orders"][0]
    assert child["ord_no"] == "0034000"
    assert child["qty"] == 14
    assert child["entry_reprice_parent_ord_no"] == "0033470,0033471"
    assert child["entry_reprice_bundle_compression"] is True
    assert child["entry_reprice_bundle_leg_count"] == 2
    stages = [stage for stage, _ in events]
    assert stages.count("entry_reprice_cancel_requested") == 2
    assert stages.count("entry_reprice_cancel_confirmed") == 2
    submitted = [fields for stage, fields in events if stage == "entry_reprice_resubmit_submitted"][-1]
    assert submitted["entry_reprice_bundle_compression"] is True
    assert submitted["entry_reprice_parent_order_nos"] == "0033470,0033471"


def test_entry_reprice_multi_leg_observed_mark_gap_unresolved_blocks_child(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "금호건설",
        "strategy": "SCALPING",
        "current_price_observed": 16780,
        "pending_entry_orders": [
            {
                **_base_order(
                    sent_at=now - 16.0,
                    ord_no="0051571",
                    qty=2,
                    price=16460,
                    mark_price_at_submit=16510,
                ),
                "tag": "entry_split_primary",
                "tif": "DAY",
            },
            {
                **_base_order(
                    sent_at=now - 16.0,
                    ord_no="0051572",
                    qty=10,
                    price=16410,
                    mark_price_at_submit=16510,
                ),
                "tag": "entry_split_passive_1",
                "tif": "DAY",
            },
        ],
    }
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 0,
            "best_ask": 0,
            "observer_healthy": False,
            "observer_missing_reason": "missing_quote",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": None,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(
        handlers,
        "_entry_reprice_refresh_snapshot",
        lambda code, snapshot, stock, order, strategy, now_ts: (snapshot, {}),
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "002990", "SCALPING", timeout_sec=60) == "blocked"
    assert stock["entry_reprice_block_reason"] == "observed_mark_gap_unresolved"
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    blocked = [fields for stage, fields in events if stage == "entry_reprice_after_submit_blocked"][0]
    assert evaluated["observed_mark_gap_action"] == "block_submit"
    assert evaluated["entry_reprice_bundle_compression"] is True
    assert blocked["broker_order_forbidden"] is True


def test_entry_reprice_observed_side_rebases_stale_parent_cap(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "금호건설",
        "strategy": "SCALPING",
        "current_price_observed": 16780,
        "pending_entry_orders": [
            {
                **_base_order(
                    sent_at=now - 16.0,
                    ord_no="0051571",
                    qty=2,
                    price=16460,
                    mark_price_at_submit=16510,
                ),
                "tag": "entry_split_primary",
                "tif": "DAY",
            },
            {
                **_base_order(
                    sent_at=now - 16.0,
                    ord_no="0051572",
                    qty=10,
                    price=16410,
                    mark_price_at_submit=16510,
                ),
                "tag": "entry_split_passive_1",
                "tif": "DAY",
            },
        ],
    }
    events = []
    cancel_calls = []
    buy_calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 16730,
            "best_ask": 16750,
            "last_trade_price": 16780,
            "observer_healthy": True,
            "observer_missing_reason": "ok",
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs) or {"return_code": "0", "ord_no": f"C{len(cancel_calls)}"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: buy_calls.append((args, kwargs)) or {"return_code": "0", "ord_no": "0052000"},
    )

    assert handlers._maybe_reprice_pending_entry_order(stock, "002990", "SCALPING", timeout_sec=60) == "submitted"
    assert [call["orig_ord_no"] for call in cancel_calls] == ["0051571", "0051572"]
    assert buy_calls[0][0][2] >= 16700
    evaluated = [fields for stage, fields in events if stage == "entry_reprice_after_submit_evaluated"][0]
    assert evaluated["observed_mark_gap_action"] == "recompute_from_observed_side"
    assert evaluated["observed_mark_gap_recompute_applied"] is True
    assert evaluated["mark_price_at_submit"] == 16780
    submitted = [fields for stage, fields in events if stage == "entry_reprice_resubmit_submitted"][-1]
    assert submitted["reprice_order_price"] >= 16700
    assert stock["pending_entry_orders"][0]["price"] >= 16700
    assert stock["pending_entry_orders"][0]["mark_price_at_submit"] == 16780


def test_pending_order_multi_leg_partial_fill_blocks_without_cancel(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [
            {**_base_order(sent_at=now - 16.0, ord_no="0033470", qty=3, filled_qty=1, status="PARTIAL"), "tif": "DAY"},
            {**_base_order(sent_at=now - 16.0, ord_no="0033471", qty=11), "tif": "DAY"},
        ],
    }
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "blocked"
    assert stock["entry_reprice_block_reason"] == "bundle_partial_fill_not_supported"
    assert events[0][1]["block_reason"] == "bundle_partial_fill_not_supported"


def test_pending_order_multi_leg_cancel_failure_does_not_resubmit(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [
            {**_base_order(sent_at=now - 16.0, ord_no="0033470", qty=3), "tif": "DAY"},
            {**_base_order(sent_at=now - 16.0, ord_no="0033471", qty=11), "tif": "DAY"},
        ],
    }
    events = []
    cancel_calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))

    def fake_cancel(**kwargs):
        cancel_calls.append(kwargs)
        if len(cancel_calls) == 1:
            return {"return_code": "0", "ord_no": "C1"}
        return {"return_code": "1", "return_msg": "cancel failed"}

    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", fake_cancel)
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "failed"
    assert [call["orig_ord_no"] for call in cancel_calls] == ["0033470", "0033471"]
    assert stock["entry_reprice_block_reason"] == "bundle_cancel_partial_failure"
    failed = [fields for stage, fields in events if stage == "entry_reprice_after_submit_failed"][-1]
    assert failed["failure_reason"] == "bundle_cancel_partial_failure"


def test_pending_order_multi_leg_post_cancel_fill_blocks_child(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [
            {**_base_order(sent_at=now - 16.0, ord_no="0033470", qty=3), "tif": "DAY"},
            {**_base_order(sent_at=now - 16.0, ord_no="0033471", qty=11), "tif": "DAY"},
        ],
    }
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))

    def fake_cancel(**kwargs):
        if kwargs["orig_ord_no"] == "0033471":
            stock["entry_filled_qty"] = 1
        return {"return_code": "0", "ord_no": f"C{kwargs['orig_ord_no']}"}

    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", fake_cancel)
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "failed"
    assert stock["entry_reprice_block_reason"] == "bundle_fill_after_cancel_detected"
    failed = [fields for stage, fields in events if stage == "entry_reprice_after_submit_failed"][-1]
    assert failed["failure_stage"] == "post_cancel_fill_check"
    assert failed["entry_reprice_filled_qty"] == 1


def test_pending_order_resubmit_missing_order_no_clears_pending(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [{**_base_order(sent_at=now - 16.0), "tif": "DAY"}],
    }
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(
        handlers.ORDERBOOK_STABILITY_OBSERVER,
        "snapshot",
        lambda code, now=None: {
            "best_bid": 39855,
            "best_ask": 39915,
            "observer_healthy": True,
            "unstable_quote_observed": False,
            "observer_last_quote_age_ms": 120.0,
            "orderbook_micro": {"micro_state": "neutral"},
        },
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "_clear_entry_arm", lambda stock: None)
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", {"466920"})
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: {"return_code": "0", "ord_no": "0033622"})
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: {"return_code": "0", "ord_no": ""})

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "failed"
    assert "pending_entry_orders" not in stock
    assert stock["status"] == "WATCHING"
    assert "466920" not in handlers.ALERTED_STOCKS


def test_child_order_does_not_reprice_again(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = time.time()
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [
            {
                **_base_order(sent_at=now - 20.0, ord_no="0034000", entry_reprice_attempt_count=1),
                "entry_order_lifecycle": "repriced_after_submit",
            }
        ],
    }
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))
    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "blocked"
    assert stock["pending_entry_orders"][0]["entry_reprice_block_reason"] == "attempt_limit"
