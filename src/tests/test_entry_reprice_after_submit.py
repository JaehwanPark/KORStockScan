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


def test_pending_order_multi_leg_blocks_without_cancel(monkeypatch):
    import src.engine.sniper_state_handlers as handlers

    now = 1000.0
    stock = {
        "name": "테스트",
        "strategy": "SCALPING",
        "pending_entry_orders": [
            {**_base_order(sent_at=now - 16.0, ord_no="0033470"), "tif": "DAY"},
            {**_base_order(sent_at=now - 16.0, ord_no="0033471"), "tif": "DAY"},
        ],
    }
    events = []
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))
    monkeypatch.setattr(handlers.kiwoom_orders, "send_cancel_order", lambda **kwargs: (_ for _ in ()).throw(AssertionError))

    assert handlers._maybe_reprice_pending_entry_order(stock, "466920", "SCALPING", timeout_sec=60) == "blocked"
    assert stock["entry_reprice_multi_leg_block_logged"] is True
    assert events[0][1]["block_reason"] == "multi_leg_pending_not_supported"


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
