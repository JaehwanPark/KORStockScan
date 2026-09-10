"""Local-only entry input timing regressions; no provider or broker calls."""

from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from src.engine import sniper_state_handlers as handlers
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


def test_retry_acquires_after_slow_context_build_and_uses_same_tape(monkeypatch):
    clock = {"now": NOW}
    calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: clock["now"])
    monkeypatch.setattr(
        handlers,
        "_consume_entry_price_exact_context_handoff",
        lambda *a, **k: (None, {}),
    )

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
        return {
            "ai_result_source": "input_preflight_blocked",
            "action": "DROP",
            "score": 0,
        }

    result = handlers._retry_entry_ai_submit_authority_before_block(
        stock={"id": 1, "name": "fixture", "strategy": "SCALPING"},
        code="123456",
        ws_data=_ws(NOW - 5),
        ai_engine=SimpleNamespace(analyze_target=analyze),
        now_ts=NOW,
        current_ai_score=0,
    )
    assert result["pre_submit_entry_ai_authority_retry_final_refresh_applied"] is True
    assert result["pre_submit_entry_ai_authority_retry_success"] is False
