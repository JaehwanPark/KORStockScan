"""Local-only entry input timing regressions; no provider or broker calls."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from src.utils.constants import TRADING_RULES as CONFIG

from src.engine import sniper_state_handlers as handlers
from src.engine.scalping import ai_market_snapshot as snapshot_module
from src.engine.scalping.entry_candle_context import (
    build_entry_candle_context,
    revalidate_entry_candle_snapshot,
)

NOW = datetime(2026, 9, 10, 14, 0, 25, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()


def _ws(at, *, price=10000):
    return {
        "curr": price,
        "best_bid": price,
        "best_ask": price + 10,
        "last_ws_update_ts": at,
        "market_route": "krx_regular",
        "market_suffix": "",
        "received_types": ["0B", "0D"],
        "last_realtime_type_ts": {"0B": at, "0D": at},
        "last_realtime_type_item": {"0B": "123456", "0D": "123456"},
        "last_realtime_type_market_route": {"0B": "krx_regular", "0D": "krx_regular"},
        "last_realtime_type_market_suffix": {"0B": "", "0D": ""},
        "recent_trade_ticks": [{"price": price, "received_ts": at}],
        "orderbook": {
            "bids": [{"price": price, "volume": 100}],
            "asks": [{"price": price + 10, "volume": 100}],
        },
    }


@pytest.mark.parametrize("age", [0.753, 1.044, 1.065, 1.234])
def test_recheck_acquisition_uses_own_limit_but_submit_stays_stricter(monkeypatch, age):
    monkeypatch.setattr(handlers.time, "time", lambda: NOW)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_WS_AGE_MS", "1500")
    latest = _ws(NOW - age, price=10020)
    original = _ws(NOW - 5)
    monkeypatch.setattr(
        handlers, "WS_MANAGER", SimpleNamespace(get_latest_data=lambda _: latest)
    )
    ws, ticks, fields = handlers._refresh_entry_opportunity_recheck_inputs(
        "123456", "SCALPING", original, original["recent_trade_ticks"]
    )
    assert fields["entry_opportunity_recheck_quote_refresh_applied"] is True
    assert fields["entry_opportunity_recheck_quote_refresh_max_age_ms"] == 1500
    assert ws["last_ws_update_ts"] == latest["last_ws_update_ts"]
    assert ticks == latest["recent_trade_ticks"]
    assert original["curr"] == 10000
    _, final = handlers._pre_submit_refresh_real_ws_snapshot("123456", ws, "SCALPING")
    assert final["pre_submit_ws_snapshot_refresh_applied"] is False
    assert final["pre_submit_ws_snapshot_refresh_reason"] == "latest_snapshot_stale"
    assert final["pre_submit_ws_snapshot_refresh_max_age_ms"] == 700
    _, handoff = handlers._consume_entry_opportunity_recheck_ws_handoff(
        {"entry_opportunity_recheck_armed": True},
        _ws(NOW),
        {
            "strategy": "SCALPING",
            "_entry_opportunity_recheck_ws_handoff": {"snapshot": ws},
        },
    )
    assert handoff["entry_opportunity_recheck_ws_handoff_applied"] is False
    assert handoff["entry_opportunity_recheck_ws_handoff_reason"] == "snapshot_stale"


@pytest.mark.parametrize("age", [1.6, -0.1, float("nan"), float("inf")])
def test_recheck_does_not_accept_stale_future_or_nonfinite_receipts(monkeypatch, age):
    monkeypatch.setattr(handlers.time, "time", lambda: NOW)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_WS_AGE_MS", "1500")
    latest = _ws(NOW - age)
    monkeypatch.setattr(
        handlers, "WS_MANAGER", SimpleNamespace(get_latest_data=lambda _: latest)
    )
    _, _, fields = handlers._refresh_entry_opportunity_recheck_inputs(
        "123456", "SCALPING", _ws(NOW - 5), []
    )
    assert fields["entry_opportunity_recheck_quote_refresh_applied"] is False


def _context():
    ws = _ws(NOW - 0.1)
    ws.update(investor_context={"foreign_net": 20}, investor_observed_ts=NOW - 2)
    return build_entry_candle_context(
        None,
        "123456",
        ws,
        "KRX",
        "krx_regular",
        now_ts=NOW,
        recent_candles=[
            {
                "source_timestamp": "20260910135900",
                "시가": 10000,
                "고가": 10010,
                "저가": 9990,
                "현재가": 10000,
                "거래량": 100,
            },
        ],
        broker_route="KRX",
    )


def test_revalidation_keeps_bar_and_investor_clocks_without_io():
    context = _context()
    original = deepcopy(context)
    refreshed = revalidate_entry_candle_snapshot(
        context, _ws(NOW + 4.9), now_ts=NOW + 5
    )
    before = context["ai_market_snapshot_v1"]
    after = refreshed["ai_market_snapshot_v1"]
    assert after["snapshot_id"] != before["snapshot_id"]
    assert refreshed["bars"] == original["bars"]
    assert (
        after["sources"]["candle"]["observed_at"]
        == before["sources"]["candle"]["observed_at"]
    )
    assert after["sources"]["current_price"]["age_ms"] == pytest.approx(100, abs=1)
    assert (
        after["sources"]["investor"]["observed_at"]
        == before["sources"]["investor"]["observed_at"]
    )
    assert after["sources"]["investor"]["age_ms"] == pytest.approx(7000, abs=1)
    assert context == original


def test_revalidation_does_not_turn_fresh_quote_into_fresh_tape():
    ws = _ws(NOW + 4.9)
    ws["last_realtime_type_ts"]["0B"] = NOW - 5
    result = revalidate_entry_candle_snapshot(_context(), ws, now_ts=NOW + 5)
    preflight = result["ai_market_snapshot_v1"]["ai_input_preflight_v1"]
    assert preflight["allowed"] is False
    assert "tape_stale" in preflight["blockers"]


def test_revalidation_rejects_changed_route_and_reversed_clock():
    ws = _ws(NOW + 4.9)
    ws["last_realtime_type_market_route"] = {"0B": "nxt_regular", "0D": "nxt_regular"}
    ws["last_realtime_type_market_suffix"] = {"0B": "_NX", "0D": "_NX"}
    with pytest.raises(ValueError, match="route_changed"):
        revalidate_entry_candle_snapshot(_context(), ws, now_ts=NOW + 5)
    with pytest.raises(ValueError, match="clock_invalid"):
        revalidate_entry_candle_snapshot(_context(), _ws(NOW), now_ts=NOW - 1)


@pytest.mark.parametrize("age", [-1, float("nan"), float("inf")])
def test_revalidation_never_matures_an_invalid_prepared_candle_age(age):
    context = _context()
    context["latest_bar_age_sec"] = age
    with pytest.raises(ValueError, match="candle_age_invalid"):
        revalidate_entry_candle_snapshot(context, _ws(NOW + 4.9), now_ts=NOW + 5)


@pytest.mark.parametrize("expired_handoff", [False, True])
def test_retry_acquires_after_slow_context_build_and_uses_same_tape(
    monkeypatch, expired_handoff
):
    clock = {"now": NOW}
    calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: clock["now"])
    stock = {"id": 1, "name": "fixture", "strategy": "SCALPING"}
    if expired_handoff:
        monkeypatch.setenv(
            "KORSTOCKSCAN_ENTRY_PRICE_EXACT_CONTEXT_HANDOFF_TTL_SEC", "2"
        )
        context = _context()
        context["ai_market_snapshot_v1"]["captured_at"] = datetime.fromtimestamp(
            NOW - 5, ZoneInfo("Asia/Seoul")
        ).isoformat()
        stock.update(_record_handoff(context, response_at=NOW - 0.1))
        stock["_entry_price_exact_context_handoff"]["ws_data"] = _ws(NOW - 5.1)

    def refresh(*args, **kwargs):
        calls.append(clock["now"])
        return _ws(clock["now"] - 0.1), {"pre_submit_ws_snapshot_refresh_applied": True}

    monkeypatch.setattr(handlers, "_pre_submit_refresh_real_ws_snapshot", refresh)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *a, **k: [{"old": True}],
    )
    monkeypatch.setattr(
        handlers, "fetch_entry_candles_with_meta", lambda *a, **k: ([], {})
    )

    def slow_context(*args, **kwargs):
        context = _context()
        clock["now"] += 5
        return context

    monkeypatch.setattr(handlers, "build_entry_candle_context", slow_context)
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **k: None)
    monkeypatch.setattr(handlers, "_extract_ai_overlap_snapshot", lambda **k: {})

    def analyze(_name, ws, ticks, candles, **kwargs):
        assert calls == [NOW, NOW + 5]
        assert ticks == ws["recent_trade_ticks"]
        source = kwargs["candle_context"]["ai_market_snapshot_v1"]["sources"]
        assert source["tape"]["age_ms"] == pytest.approx(100, abs=1)
        assert kwargs["metadata_extra"]["ai_input_parent_snapshot_id"] is None
        return {
            "ai_result_source": "input_preflight_blocked",
            "action": "DROP",
            "score": 0,
        }

    result = handlers._retry_entry_ai_submit_authority_before_block(
        stock=stock,
        code="123456",
        ws_data=_ws(NOW - 5),
        ai_engine=SimpleNamespace(analyze_target=analyze),
        now_ts=NOW,
        current_ai_score=0,
    )
    assert result["pre_submit_entry_ai_authority_retry_final_refresh_applied"] is True
    assert result["pre_submit_entry_ai_authority_retry_success"] is False
    if expired_handoff:
        assert result[
            "pre_submit_entry_ai_exact_context_handoff_revalidation_error"
        ] == ("source_preflight_rejected")


def _record_handoff(context, *, response_at=NOW + 0.2):
    stock = {}
    handlers._record_entry_price_exact_context_handoff(
        stock,
        code="123456",
        captured_at=response_at,
        ws_data=_ws(NOW - 0.1),
        recent_ticks=_ws(NOW - 0.1)["recent_trade_ticks"],
        recent_candles=context["bars"],
        candle_context=context,
        preflight={"allowed": True},
        result={
            "ai_result_source": "live",
            "ai_parse_ok": True,
            "ai_input_snapshot_id": context["ai_market_snapshot_v1"]["snapshot_id"],
            "ai_decision_trace_id": "price-parent",
        },
    )
    return stock


def test_fast_handoff_recomputes_ages_preserves_parent_and_is_single_use(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_PRICE_EXACT_CONTEXT_HANDOFF_TTL_SEC", "2")
    context = _context()
    stock = _record_handoff(context)
    original = deepcopy(stock["_entry_price_exact_context_handoff"])
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + 0.5, current_ws_data=_ws(NOW - 0.1)
    )
    assert handoff is not None, fields
    snapshot = handoff["candle_context"]["ai_market_snapshot_v1"]
    assert snapshot["snapshot_id"] != original["snapshot_id"]
    assert handoff["snapshot_id"] == original["snapshot_id"]
    assert snapshot["sources"]["tape"]["age_ms"] == pytest.approx(600, abs=1)
    assert snapshot["sources"]["tape"]["observed_at"] == (
        context["ai_market_snapshot_v1"]["sources"]["tape"]["observed_at"]
    )
    assert fields["pre_submit_entry_ai_exact_context_handoff_revalidated"] is True
    assert handoff["recent_ticks"] == original["recent_ticks"]
    assert handoff["candle_context"]["bars"] == original["candle_context"]["bars"]
    second, _ = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + 0.6, current_ws_data=_ws(NOW)
    )
    assert second is None


@pytest.mark.parametrize("elapsed", [3.0, 5.0])
def test_provider_response_does_not_renew_source_freshness(monkeypatch, elapsed):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_PRICE_EXACT_CONTEXT_HANDOFF_TTL_SEC", "2")
    stock = _record_handoff(_context(), response_at=NOW + elapsed - 0.1)
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + elapsed, current_ws_data=_ws(NOW)
    )
    assert handoff is None
    assert fields["pre_submit_entry_ai_exact_context_handoff_revalidation_error"] == (
        "source_preflight_rejected"
    )
    assert "pre_submit_entry_ai_exact_context_handoff_parent_trace_id" not in fields
    assert "_entry_price_exact_context_handoff" not in stock


def test_handoff_ttl_does_not_add_a_stricter_source_freshness_limit(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_PRICE_EXACT_CONTEXT_HANDOFF_TTL_SEC", "2")
    stock = _record_handoff(_context(), response_at=NOW + 2.0)
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + 2.1, current_ws_data=_ws(NOW - 0.1)
    )
    assert handoff is not None, fields
    assert handoff["candle_context"]["ai_market_snapshot_v1"]["sources"]["tape"][
        "age_ms"
    ] == pytest.approx(2200, abs=1)


def test_handoff_rechecks_source_age_even_with_longer_existing_ttl(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_PRICE_EXACT_CONTEXT_HANDOFF_TTL_SEC", "15")
    stock = _record_handoff(_context(), response_at=NOW + 4.9)
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + 5, current_ws_data=_ws(NOW)
    )
    assert handoff is None
    assert (
        "tape_stale"
        in fields["pre_submit_entry_ai_exact_context_handoff_source_blockers"]
    )


@pytest.mark.parametrize("clock", [NOW + 1, float("nan"), float("inf")])
def test_handoff_rejects_future_or_nonfinite_response_clock(clock):
    stock = _record_handoff(_context(), response_at=clock)
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + 0.5, current_ws_data=_ws(NOW)
    )
    assert handoff is None
    assert fields["pre_submit_entry_ai_exact_context_handoff_used"] is False


@pytest.mark.parametrize(
    "field,value", [("stock_code", "654321"), ("snapshot_id", "other")]
)
def test_handoff_rejects_wrong_canonical_parent_identity(field, value):
    stock = _record_handoff(_context())
    stock["_entry_price_exact_context_handoff"]["candle_context"][
        "ai_market_snapshot_v1"
    ][field] = value
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock, code="123456", now_ts=NOW + 0.5, current_ws_data=_ws(NOW)
    )
    assert handoff is None
    assert fields["pre_submit_entry_ai_exact_context_handoff_revalidation_error"] == (
        "prepared_snapshot_identity_mismatch"
    )


@pytest.mark.parametrize(
    "suffix,route", [("_NX", "nxt_only"), ("_AL", "krx_nxt_integrated")]
)
def test_nxt_aftermarket_handoff_preserves_exact_route_and_source_clocks(
    monkeypatch, suffix, route
):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_PRICE_EXACT_CONTEXT_HANDOFF_TTL_SEC", "2")
    now = datetime(2026, 9, 10, 17, 0, 25, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    ws = _ws(now - 0.1)
    ws.update(market_suffix=suffix, market_route=route)
    for kind in ("0B", "0D"):
        ws["last_realtime_type_item"][kind] = "123456" + suffix
        ws["last_realtime_type_market_suffix"][kind] = suffix
        ws["last_realtime_type_market_route"][kind] = route
    context = build_entry_candle_context(
        None,
        "123456",
        ws,
        "NXT",
        "nxt_aftermarket",
        now_ts=now,
        recent_candles=[
            {
                "source_timestamp": "20260910165900",
                "시가": 10000,
                "고가": 10010,
                "저가": 9990,
                "현재가": 10000,
                "거래량": 100,
            }
        ],
        broker_route="NXT",
    )
    stock = {}
    handlers._record_entry_price_exact_context_handoff(
        stock,
        code="123456",
        captured_at=now + 2.0,
        ws_data=ws,
        recent_ticks=ws["recent_trade_ticks"],
        recent_candles=context["bars"],
        candle_context=context,
        preflight=context["ai_market_snapshot_v1"]["ai_input_preflight_v1"],
        result={
            "ai_result_source": "live",
            "ai_parse_ok": True,
            "ai_input_snapshot_id": context["ai_market_snapshot_v1"]["snapshot_id"],
            "ai_decision_trace_id": "nxt-price-parent",
        },
    )
    handoff, fields = handlers._consume_entry_price_exact_context_handoff(
        stock,
        code="123456",
        now_ts=now + 2.1,
        current_ws_data=ws,
    )
    assert handoff is not None, (context["source_quality"], fields)
    snapshot = handoff["candle_context"]["ai_market_snapshot_v1"]
    assert snapshot["effective_venue"] == "NXT"
    assert snapshot["market_data_route"] == route
    assert snapshot["sources"]["tape"]["age_ms"] == pytest.approx(2200, abs=1)
    assert snapshot["sources"]["tape"]["observed_at"] == (
        context["ai_market_snapshot_v1"]["sources"]["tape"]["observed_at"]
    )


@pytest.mark.parametrize("mode", ["fresh", "stale", "future", "route_changed"])
def test_entry_price_refreshes_after_auxiliary_reads_without_submit_relaxation(
    monkeypatch, mode
):
    clock = {"now": NOW}
    calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: clock["now"])
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", "700")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED", "true")
    monkeypatch.setattr(
        snapshot_module,
        "runtime_preflight_artifact_status",
        lambda **k: {"ready": True, "status": "ready_fixture"},
    )
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_PRICE_REFRESH_ENABLED=False,
        ),
    )
    monkeypatch.setattr(handlers, "entry_candle_context_enabled", lambda **k: True)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *a, **k: [{"old_rest": True}],
    )
    monkeypatch.setattr(
        handlers, "fetch_entry_candles_with_meta", lambda *a, **k: ([], {})
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **k: None)
    monkeypatch.setattr(
        handlers,
        "_entry_ai_price_input_audit_fields",
        lambda **k: {"ai_input_source_quality_status": "complete"},
    )

    def latest(_code):
        age = {"fresh": 0.9, "stale": 4, "future": -1, "route_changed": 0.1}[mode]
        ws = _ws(clock["now"] - age, price=10020)
        if mode == "route_changed":
            ws.update(market_route="nxt_only", market_suffix="_NX")
            ws["last_realtime_type_market_route"] = {"0B": "nxt_only", "0D": "nxt_only"}
            ws["last_realtime_type_market_suffix"] = {"0B": "_NX", "0D": "_NX"}
        return ws

    monkeypatch.setattr(handlers, "WS_MANAGER", SimpleNamespace(get_latest_data=latest))

    def slow_context(*a, **k):
        context = _context()
        clock["now"] += 5
        return context

    monkeypatch.setattr(handlers, "build_entry_candle_context", slow_context)

    def evaluate(_name, _code, ws, ticks, candles, price_ctx, **kwargs):
        calls.append(True)
        assert mode == "fresh"
        assert ws["curr"] == 10020 and price_ctx["current_price"] == 10020
        assert ticks == ws["recent_trade_ticks"] and "old_rest" not in str(ticks)
        assert kwargs["candle_context"]["ai_market_snapshot_v1"]["sources"]["tape"][
            "age_ms"
        ] == pytest.approx(900, abs=1)
        return {
            "action": "SKIP",
            "confidence": 99,
            "reason": "fixture_skip",
            "ai_parse_ok": True,
            "ai_result_source": "live",
        }

    gate = {
        "target_buy_price": 9980,
        "latency_guarded_order_price": 9990,
        "normal_defensive_order_price": 9990,
        "order_price": 9990,
        "price_resolution_reason": "defensive_order_price",
        "latency_state": "SAFE",
    }
    result, touched = handlers._apply_entry_ai_price_canary(
        stock={
            "name": "fixture",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "prob": 0.8,
        },
        code="123456",
        strategy="SCALPING",
        ws_data=_ws(NOW - 0.1),
        ai_engine=SimpleNamespace(evaluate_scalping_entry_price=evaluate),
        latency_gate=gate,
        planned_orders=[
            {
                "tag": "normal",
                "qty": 1,
                "price": 9990,
                "tif": "DAY",
                "order_type": "LIMIT",
            }
        ],
        curr_price=10000,
        best_bid=10000,
        best_ask=10010,
    )
    assert result == [] and touched is True
    assert len(calls) == (1 if mode == "fresh" else 0), {
        k: v for k, v in gate.items() if "reason" in k or "error" in k or "blocker" in k
    }
    assert gate["entry_ai_price_final_ws_snapshot_refresh_max_age_ms"] == 3000
    if mode == "fresh":
        _, final = handlers._pre_submit_refresh_real_ws_snapshot(
            "123456", latest("123456"), "SCALPING"
        )
        assert final["pre_submit_ws_snapshot_refresh_applied"] is False
        assert final["pre_submit_ws_snapshot_refresh_max_age_ms"] == 700
