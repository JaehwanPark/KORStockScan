from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.engine import sniper_state_handlers as state_handlers
from src.engine.scalping import ai_market_snapshot as snapshot_module
from src.engine.scalping import holding_decision_context as holding_context_module
from src.engine.scalping.holding_decision_context import (
    OBSERVATION_CONTRACT,
    build_holding_decision_context,
    count_holding_context_changes,
    holding_decision_context_enabled,
    holding_decision_context_log_fields,
    holding_decision_context_model_payload,
)
from src.utils import kiwoom_utils

KST = ZoneInfo("Asia/Seoul")


def _enable(monkeypatch) -> None:
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE", "2026-07-23"
    )
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_KRX_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_NXT_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_PREMARKET_ENABLED", "true"
    )
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_SCORE_CONTEXT_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_FLOW_CONTEXT_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_OVERNIGHT_CONTEXT_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE", "2026-07-23"
    )


def test_overnight_context_is_permanently_retired(monkeypatch):
    _enable(monkeypatch)

    assert (
        holding_decision_context_enabled(
            venue="KRX",
            session="krx_regular",
            decision_kind="overnight",
            now_ts=datetime(2026, 7, 23, 15, 10, tzinfo=KST),
        )
        is False
    )


def test_holding_snapshot_collects_null_aware_investor_source(monkeypatch):
    _enable(monkeypatch)
    source_date = datetime(2026, 7, 23, tzinfo=KST)
    investor_frame = type(
        "InvestorFrame",
        (),
        {"empty": False, "index": [source_date]},
    )()
    monkeypatch.setattr(
        snapshot_module.kiwoom_utils,
        "get_investor_daily_ka10059_df",
        lambda *_args, **_kwargs: investor_frame,
    )
    monkeypatch.setattr(
        snapshot_module.kiwoom_utils,
        "get_investor_flow_summary_ka10059",
        lambda *_args, **_kwargs: {
            "foreign_net": 5000,
            "inst_net": 22000,
            "smart_money_net": 27000,
        },
    )
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)

    context = build_holding_decision_context(
        "token",
        "322000",
        _ws(now),
        _stock(),
        "KRX",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
        include_investor_source=True,
    )

    investor = context["ai_market_snapshot_v1"]["sources"]["investor"]
    assert investor["quality"] == "fresh"
    assert investor["source"] == "ka10059_process_cache_or_live"
    assert investor["value"]["smart_money_net"] == 27000
    assert investor["value"]["source_data_date"] == "2026-07-23"


def test_holding_context_recovers_shared_positive_broker_reconciliation(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = _stock()
    stock.pop("broker_holding_qty")
    stock.pop("broker_snapshot_age_sec")
    stock["entry_execution_broker_route"] = "SOR"
    snapshot_module.publish_broker_account_snapshot(
        inventory=[{"code": "322000", "qty": 20}],
        successful_exchanges={"KRX"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now.timestamp() - 1,
    )
    try:
        context = build_holding_decision_context(
            None,
            "322000",
            _ws(now),
            stock,
            "KRX",
            "krx_regular",
            "holding_flow",
            now_ts=now,
            recent_candles=_candles(
                60,
                start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
            ),
        )
    finally:
        snapshot_module._clear_broker_account_snapshot_for_tests()

    assert context["position_lifecycle"]["broker_qty"] == 20
    assert context["order_reconciliation"]["open_buy_qty"] == 0
    assert context["order_reconciliation"]["open_sell_qty"] == 0
    assert context["source_quality"]["position_reconciled"] is True
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["sources"]["broker_position"]["verification"] == "present"
    assert snapshot["sources"]["open_orders"]["verification"] == "verified_zero"
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is True


def test_holding_flow_uses_explicit_simulation_book_reconciliation(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = _stock()
    stock.pop("broker_holding_qty")
    stock.pop("broker_snapshot_age_sec")
    stock.update(
        {
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_price": 10_000,
            "simulation_book": "scalp_ai_buy_all",
            "simulation_owner": "ScalpAiBuyAllLiveSimulator0511",
            "scalp_live_simulator": True,
            "sim_record_id": "sim-322000-1",
            "decision_authority": "sim_observation_only",
            "simulated_order": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    )
    ws_data = _ws(now, route="krx_only")
    ws_data.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {"0B": "322000", "0D": "322000"},
            "last_realtime_type_market_suffix": {"0B": "", "0D": ""},
            "last_realtime_type_market_route": {
                "0B": "krx_only",
                "0D": "krx_only",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "322000",
        ws_data,
        stock,
        "KRX",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
    )

    source_quality = context["source_quality"]
    assert source_quality["position_reconciled"] is False
    assert source_quality["position_authority_reconciled"] is True
    assert source_quality["position_reconciliation_mode"] == "simulation_book"
    assert source_quality["simulation_position_reconciled"] is True
    assert context["ai_market_snapshot_v1"]["ai_input_preflight_v1"]["allowed"] is True
    assert source_quality["scale_in_support_allowed"] is False


def test_scalp_sim_holding_defaults_pin_observation_only_authority():
    stock = {"sim_record_id": "sim-005930-1"}

    state_handlers._initialize_scalp_sim_holding_defaults(stock, 10_000)

    assert stock["simulation_book"] == state_handlers.SCALP_SIMULATION_BOOK
    assert stock["decision_authority"] == "sim_observation_only"
    assert stock["simulated_order"] is True
    assert stock["actual_order_submitted"] is False
    assert stock["broker_order_forbidden"] is True


def _candles(
    count: int,
    *,
    start: datetime,
    base: int = 10_000,
    step: int = 5,
) -> list[dict]:
    rows = []
    for index in range(count):
        moment = start + timedelta(minutes=index)
        close = base + step * index
        rows.append(
            {
                "source_timestamp": moment.strftime("%Y%m%d%H%M%S"),
                "체결시간": moment.strftime("%H:%M:%S"),
                "시가": close - 2,
                "고가": close + 4,
                "저가": close - 4,
                "현재가": close,
                "거래량": 100 + index,
            }
        )
    return rows


def _ws(
    now: datetime, *, price: int = 10_300, suffix: str = "", route: str = "krx_regular"
):
    ticks = []
    for index, side in enumerate(("BUY", "SELL", "BUY")):
        ticks.append(
            {
                "price": price - index,
                "volume": 5 + index,
                "aggressor_side": side,
                "aggressor_source": "ws_executable_quote",
                "received_at_ms": int(now.timestamp() * 1000) - index * 100,
                "market_suffix": suffix,
                "market_route": route,
            }
        )
    return {
        "curr": price,
        "best_bid": price - 1,
        "best_ask": price + 1,
        "best_bid_qty": 200,
        "best_ask_qty": 100,
        "ask_tot": 1_000,
        "bid_tot": 1_400,
        "last_ws_update_ts": now.timestamp(),
        "market_suffix": suffix,
        "market_route": route,
        "recent_trade_ticks": ticks,
    }


@pytest.mark.parametrize(
    "totals,expected",
    [
        ({"ask": 1000, "bid": 1400}, True),
        ({"ask": -1, "bid": 1400}, False),
        ({"ask": True, "bid": 1400}, False),
        ({"ask": None, "bid": 1400}, False),
    ],
)
def test_selected_route_depth_totals_reach_holding_microstructure(
    monkeypatch, totals, expected
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    ws = _ws(now)
    ws["recent_trade_ticks"] = []
    rows = {}
    for kind in ("0B", "0D"):
        rows[kind] = {
            "observed_epoch": now.timestamp(),
            "item": "000660",
            "market_suffix": "",
            "market_route": "krx_regular",
        }
    rows["0B"]["current_price"] = 10300
    rows["0D"].update(
        {
            "orderbook": {
                "asks": [{"price": 10301, "volume": 100}],
                "bids": [{"price": 10299, "volume": 200}],
            },
            "route_depth_totals": {
                "combined": totals,
                "KRX": {"ask": 0, "bid": 0},
                "NXT": {"ask": 0, "bid": 0},
            },
        }
    )
    ws["realtime_type_snapshots_by_route"] = {"KRX|krx_regular": rows}
    stock = _stock()
    stock.pop("holding_flow_ofi_regime")
    stock.pop("holding_flow_ofi_snapshot_age_ms")
    context = build_holding_decision_context(
        None,
        "000660",
        ws,
        stock,
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )
    assert (
        "microstructure_missing_or_stale" not in context["source_quality"]["blockers"]
    ) is expected
    assert context["source_quality"]["hold_defer_allowed"] is expected


@pytest.mark.parametrize("quote_age", [4.0, -2.0])
def test_new_trade_does_not_refresh_stale_or_future_quote(monkeypatch, quote_age):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    ws = _ws(now)
    ws["last_realtime_type_ts"] = {
        "0B": now.timestamp(),
        "0D": now.timestamp() - quote_age,
    }
    context = build_holding_decision_context(
        None,
        "000660",
        ws,
        _stock(),
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )
    assert "executable_bbo" in context["source_quality"]["blockers"]
    assert context["source_quality"]["hold_defer_allowed"] is False


def test_holding_refresh_replaces_volatile_input_without_restamping(monkeypatch):
    from types import SimpleNamespace

    now = 1789014600.0
    base = {
        "curr": 100,
        "last_ws_update_ts": now - 4,
        "orderbook": {"old": True},
        "recent_trade_ticks": [{"old": True}],
        "market_type": "KOSDAQ",
        "last_realtime_type_ts": {"0B": now - 4},
    }
    latest = {"curr": 101, "last_ws_update_ts": now - 0.1}
    calls = []

    def read(code):
        calls.append(code)
        return latest

    monkeypatch.setattr(
        state_handlers, "WS_MANAGER", SimpleNamespace(get_latest_data=read)
    )
    monkeypatch.setattr(state_handlers.time, "time", lambda: now)
    refreshed, fields = state_handlers._refresh_holding_ai_ws_snapshot("232140", base)
    assert calls == ["232140"]
    assert fields["holding_ai_ws_refresh_applied"] is True
    assert refreshed["last_ws_update_ts"] == latest["last_ws_update_ts"]
    assert refreshed["market_type"] == "KOSDAQ"
    assert not any(
        k in refreshed
        for k in ["orderbook", "recent_trade_ticks", "last_realtime_type_ts"]
    )
    assert base["curr"] == 100 and latest == {
        "curr": 101,
        "last_ws_update_ts": now - 0.1,
    }


@pytest.mark.parametrize(
    "timestamp", [0, float("nan"), float("inf"), 1789014700.0, 1789014590.0]
)
def test_holding_refresh_rejects_invalid_future_or_regressed_cache(
    monkeypatch, timestamp
):
    from types import SimpleNamespace

    base = {"curr": 100, "last_ws_update_ts": 1789014599.0}
    monkeypatch.setattr(
        state_handlers,
        "WS_MANAGER",
        SimpleNamespace(
            get_latest_data=lambda code: {"curr": 101, "last_ws_update_ts": timestamp}
        ),
    )
    monkeypatch.setattr(state_handlers.time, "time", lambda: 1789014600.0)
    refreshed, fields = state_handlers._refresh_holding_ai_ws_snapshot("232140", base)
    assert refreshed == base
    assert fields["holding_ai_ws_refresh_applied"] is False


def test_holding_refresh_repairs_pre_fetch_age_without_relaxing_gate(monkeypatch):
    from types import SimpleNamespace

    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    base = _ws(now - timedelta(seconds=4))
    latest = _ws(now)
    monkeypatch.setattr(
        state_handlers,
        "WS_MANAGER",
        SimpleNamespace(get_latest_data=lambda code: latest),
    )
    monkeypatch.setattr(state_handlers.time, "time", lambda: now.timestamp())
    fresh, fields = state_handlers._refresh_holding_ai_ws_snapshot("000660", base)
    for source, allowed in [(base, False), (fresh, True)]:
        ctx = build_holding_decision_context(
            None,
            "000660",
            source,
            _stock(),
            "KRX",
            "krx_regular",
            "holding_score",
            now_ts=now,
            recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
        )
        assert ctx["source_quality"]["hold_defer_allowed"] is allowed
    assert fields["holding_ai_ws_refresh_applied"] is True


@pytest.mark.parametrize(
    "fee,slippage,known",
    [
        (None, None, False),
        (0.23, None, False),
        (float("nan"), 0, False),
        (-0.1, 0, False),
        (0, 0, True),
        (0.23, 2, True),
    ],
)
def test_missing_holding_costs_are_not_zero_net_profit(
    monkeypatch, fee, slippage, known
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "estimated_fee_tax_pct": fee,
        "estimated_slippage_bps": slippage,
    }
    ctx = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        stock,
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )
    pnl = ctx["execution_pnl"]
    assert (pnl["estimated_net_executable_pnl_pct"] is not None) is known
    if known:
        assert pnl["estimated_net_executable_pnl_pct"] == pytest.approx(
            pnl["executable_pnl_pct"] - fee - slippage / 100.0
        )


def _stock() -> dict:
    return {
        "avg_price": 10_000,
        "buy_qty": 20,
        "broker_holding_qty": 20,
        "broker_snapshot_age_sec": 0.3,
        "peak_basis_qty": 20,
        "peak_basis_avg_price": 10_000,
        "peak_profit": 3.2,
        "mfe_pct": 3.2,
        "mae_pct": -0.4,
        "partial_tp_realized_qty": 5,
        "partial_tp_remaining_qty": 20,
        "holding_flow_ofi_regime": "stable_bullish",
        "holding_flow_ofi_snapshot_age_ms": 100,
    }


def test_holding_excursion_context_tracks_mfe_mae_and_rebaselines():
    stock = {"buy_qty": 10}

    state_handlers._update_holding_excursion_context(
        stock,
        average_entry_price=10_000,
        current_profit_pct=1.2,
        peak_profit_pct=1.8,
        now_ts=100.0,
    )
    state_handlers._update_holding_excursion_context(
        stock,
        average_entry_price=10_000,
        current_profit_pct=-0.7,
        peak_profit_pct=1.8,
        now_ts=110.0,
    )

    assert stock["mfe_pct"] == 1.8
    assert stock["mae_pct"] == -0.7
    assert stock["excursion_tracking_started_at"] == 100.0
    assert stock["excursion_context_authority"] == "instrumentation_only"

    stock["buy_qty"] = 15
    state_handlers._update_holding_excursion_context(
        stock,
        average_entry_price=9_900,
        current_profit_pct=0.2,
        peak_profit_pct=0.4,
        now_ts=120.0,
    )
    assert stock["mfe_pct"] == 0.4
    assert stock["mae_pct"] == 0.2
    assert stock["excursion_tracking_started_at"] == 120.0


def test_holding_snapshot_recovers_program_context_from_position_state(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = _stock()
    stock.update(
        {
            "program_context": {"net_qty": 1234, "delta_qty": 50},
            "program_source": "position_runtime_state",
            "program_observed_ts": now.timestamp(),
        }
    )

    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        stock,
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )

    program = context["ai_market_snapshot_v1"]["sources"]["program"]
    assert program["quality"] == "fresh"
    assert program["source"] == "position_runtime_state"
    assert program["value"]["net_qty"] == 1234


def test_holding_model_omits_multi_timeframe_before_global_promotion(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED", "false")
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        _stock(),
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )

    assert "multi_timeframe_context" in context["candle"]
    payload = holding_decision_context_model_payload(context)
    assert payload["candle"]["multi_timeframe_ai_input_enabled"] is False
    assert "multi_timeframe_context" not in payload["candle"]
    assert "input_bundle_version" not in payload["candle"]


def test_fresh_krx_context_contains_sixty_minute_structure_and_executable_pnl(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        _stock(),
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    assert context["schema"] == "holding_decision_context_v1"
    assert context["enabled"] is True
    assert context["candle"]["current_session_bar_count"] == 61
    assert len(context["candle"]["bars"]) == 20
    assert context["candle"]["structure"]["returns_pct"]["1"] is not None
    assert context["candle"]["structure"]["returns_pct"]["60"] is None
    assert (
        context["candle"]["structure"]["window_source_bar_counts"]["60"][
            "return_complete"
        ]
        is False
    )
    assert context["execution_pnl"]["mark_pnl_pct"] == 3.0
    assert context["execution_pnl"]["executable_pnl_pct"] == 2.99
    assert context["source_quality"]["hold_defer_allowed"] is True
    assert context["observation_contract"] == OBSERVATION_CONTRACT
    model_payload = holding_decision_context_model_payload(context)
    assert model_payload["schema"] == "holding_decision_context_v1"
    assert model_payload["candle"]["model_bar_count"] == 20
    assert (
        model_payload["candle"]["input_bundle_version"]
        == "scalping_multi_timeframe_context_v1"
    )
    assert model_payload["candle"]["bar_schema"] == {
        "sequence": "oldest_to_latest",
        "timezone": "Asia/Seoul",
        "interval": "1m",
        "price_unit": "KRW",
        "volume_unit": "shares",
    }
    assert model_payload["candle"]["bars"][0] == {
        "minute": "09:41",
        "open": 10203,
        "high": 10209,
        "low": 10201,
        "close": 10205,
        "volume": 141,
        "is_forming": False,
        "volume_is_partial": False,
    }
    log_fields = holding_decision_context_log_fields(context)
    assert len(log_fields["holding_context_model_bars"]) == 20
    assert log_fields["holding_context_model_structure"]["returns_pct"]["60"] is None
    assert log_fields["holding_context_ai_market_snapshot"]["schema"] == (
        "ai_market_snapshot_v1"
    )


def test_entry_time_context_is_logged_exactly_but_not_duplicated_in_model_payload(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    entry_time_context = {
        "entry_context_quality": "complete",
        "entry_liquidity_score": 73.5,
        "fillability_score": 68.0,
        "source": "last_watching_ai_source_quality_fields",
    }
    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        {**_stock(), "entry_time_context": entry_time_context},
        "KRX",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    log_fields = holding_decision_context_log_fields(context)
    model_payload = holding_decision_context_model_payload(context)
    assert log_fields["holding_context_entry_time_context_status"] == ("exact_captured")
    assert log_fields["holding_context_entry_time_context"] == entry_time_context
    assert len(log_fields["holding_context_entry_time_context_sha256"]) == 64
    assert "entry_time_context_provenance" not in model_payload
    assert "entry_time_context" not in model_payload


def test_nxt_route_and_conflicting_ws_route_are_kept_separate(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    bars = _candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST))
    nxt = build_holding_decision_context(
        None,
        "000660",
        _ws(now, suffix="_NX", route="nxt_only"),
        _stock(),
        "NXT",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=bars,
    )
    conflict = build_holding_decision_context(
        None,
        "000660",
        _ws(now, suffix="", route="krx_regular"),
        _stock(),
        "NXT",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=bars,
    )

    assert nxt["request_code"] == "000660_NX"
    assert nxt["rest_route"] == "_NX"
    assert nxt["session"] == "nxt_regular_overlap"
    assert nxt["source_quality"]["hold_defer_allowed"] is True
    assert conflict["source_quality"]["hold_defer_allowed"] is False
    assert "candle_source_quality" in conflict["source_quality"]["blockers"]
    assert "venue_conflict" in conflict["candle"]["risk_flags"]


@pytest.mark.parametrize("decision_kind", ["holding_score", "holding_flow"])
def test_krx_sim_holding_uses_session_execution_view_without_fake_fill_route(
    monkeypatch,
    decision_kind,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    bars = _candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST))
    stock = {
        **_stock(),
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now, suffix="_AL", route="krx_nxt_integrated"),
        stock,
        "KRX",
        "krx_regular",
        decision_kind,
        now_ts=now,
        recent_candles=bars,
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    assert context["request_code"] == "000660_AL"
    assert context["rest_route"] == "_AL"
    assert context["ws_route"] == "krx_nxt_integrated"
    assert context["source_quality"]["hold_defer_allowed"] is True
    assert "venue_conflict" not in context["candle"]["risk_flags"]
    assert context["broker_route_provenance"] == {
        "route": "SOR",
        "source": "current_session_default_for_simulation",
        "authority": "simulated_execution_view_only",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    assert context["ai_market_snapshot_v1"]["broker_route"] == "SOR"
    preflight = context["ai_market_snapshot_v1"]["ai_input_preflight_v1"]
    assert preflight["broker_route_matches_venue"] is True
    assert "candle_source_quality" not in preflight["blockers"]
    assert "krx_integrated_event_venue_unproven" not in preflight["blockers"]
    log_fields = holding_decision_context_log_fields(context)
    assert log_fields["holding_context_broker_route"] == "SOR"
    assert (
        log_fields["holding_context_broker_route_authority"]
        == "simulated_execution_view_only"
    )


def test_krx_real_holding_does_not_infer_missing_broker_route(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)

    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now, suffix="_AL", route="krx_nxt_integrated"),
        _stock(),
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    assert context["request_code"] == "000660"
    assert "venue_conflict" in context["candle"]["risk_flags"]
    assert context["source_quality"]["hold_defer_allowed"] is False
    assert context["broker_route_provenance"]["route"] is None
    assert (
        context["broker_route_provenance"]["authority"]
        == "broker_execution_provenance_required"
    )
    assert context["ai_market_snapshot_v1"]["broker_route"] is None
    assert context["ai_market_snapshot_v1"]["broker_route_match_state"] == "missing"
    log_fields = holding_decision_context_log_fields(context)
    assert log_fields["holding_context_broker_route_provenance_state"] == "missing"
    assert log_fields["holding_context_broker_snapshot_freshness_state"] == "fresh"
    assert log_fields["holding_context_broker_snapshot_freshness_limit_sec"] == 60.0


def test_future_broker_snapshot_is_reported_as_provenance_conflict(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = _stock()
    stock["broker_snapshot_at"] = now.timestamp() + 5.0

    context = build_holding_decision_context(
        None,
        "322000",
        _ws(now),
        stock,
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
    )

    reconciliation = context["order_reconciliation"]
    assert reconciliation["broker_snapshot_age_sec"] == -5.0
    assert reconciliation["broker_snapshot_freshness_state"] == "future_conflict"


def test_nxt_aftermarket_real_holding_does_not_infer_integrated_execution_view(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 31, 16, 10, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "broker_snapshot_at": now.timestamp() - 0.2,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    ws.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {
                "0B": "066570_AL",
                "0D": "066570_AL",
            },
            "last_realtime_type_market_suffix": {"0B": "_AL", "0D": "_AL"},
            "last_realtime_type_market_route": {
                "0B": "krx_nxt_integrated",
                "0D": "krx_nxt_integrated",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "066570",
        ws,
        stock,
        "NXT",
        "nxt_aftermarket",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 31, 15, 30, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    assert context["request_code"] == "066570_NX"
    assert context["broker_route_provenance"] == {
        "route": None,
        "source": "missing",
        "authority": "broker_execution_provenance_required",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
    }
    snapshot = context["ai_market_snapshot_v1"]
    assert context["actual_execution_venue"] == "UNKNOWN"
    assert snapshot["actual_execution_venue"] == "UNKNOWN"
    assert snapshot["broker_route"] is None
    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["broker_route_matches_venue"] is False
    assert "nxt_aftermarket_source_unproven" in preflight["blockers"]
    assert preflight["allowed"] is False
    log_fields = holding_decision_context_log_fields(context)
    assert log_fields["holding_context_broker_route_provenance_state"] == "missing"
    assert log_fields["holding_context_broker_snapshot_freshness_state"] == "fresh"


def test_integrated_aftermarket_holding_preserves_scope_and_unknown_execution_venue(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 31, 16, 10, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "entry_execution_broker_route": "SOR",
        "broker_snapshot_at": now.timestamp() - 0.2,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    ws.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {
                "0B": "066570_AL",
                "0D": "066570_AL",
            },
            "last_realtime_type_market_suffix": {"0B": "_AL", "0D": "_AL"},
            "last_realtime_type_market_route": {
                "0B": "krx_nxt_integrated",
                "0D": "krx_nxt_integrated",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "066570",
        ws,
        stock,
        "KRX_NXT_INTEGRATED",
        "krx_nxt_aftermarket",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 31, 15, 30, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    assert context["request_code"] == "066570_AL"
    assert context["market_data_route"] == "krx_nxt_integrated"
    assert context["actual_execution_venue"] == "UNKNOWN"
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["effective_venue"] == "KRX_NXT_INTEGRATED"
    assert snapshot["market_data_route"] == "krx_nxt_integrated"
    assert snapshot["actual_execution_venue"] == "UNKNOWN"
    assert snapshot["broker_route"] == "SOR"
    assert snapshot["ai_input_preflight_v1"]["allowed"] is True


def test_holding_submit_authority_requires_fresh_broker_reconciliation(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 31, 16, 10, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "broker_snapshot_at": now.timestamp() - 61.0,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_NX", route="nxt_only")
    ws.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {
                "0B": "066570_NX",
                "0D": "066570_NX",
            },
            "last_realtime_type_market_suffix": {"0B": "_NX", "0D": "_NX"},
            "last_realtime_type_market_route": {
                "0B": "nxt_only",
                "0D": "nxt_only",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "066570",
        ws,
        stock,
        "NXT",
        "nxt_aftermarket",
        "holding_score_submit_authority",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 31, 15, 30, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    preflight = context["ai_market_snapshot_v1"]["ai_input_preflight_v1"]
    assert preflight["position_reconciled"] is False
    assert "broker_position_or_open_orders_unreconciled" in preflight["blockers"]
    assert preflight["allowed"] is False
    assert context["source_quality"]["hold_defer_allowed"] is False


def test_holding_score_preserves_stale_broker_snapshot_as_partial_warning(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 31, 16, 10, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "broker_snapshot_at": now.timestamp() - 61.0,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_NX", route="nxt_only")
    ws.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {
                "0B": "066570_NX",
                "0D": "066570_NX",
            },
            "last_realtime_type_market_suffix": {"0B": "_NX", "0D": "_NX"},
            "last_realtime_type_market_route": {
                "0B": "nxt_only",
                "0D": "nxt_only",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "066570",
        ws,
        stock,
        "NXT",
        "nxt_aftermarket",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 31, 15, 30, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    preflight = context["ai_market_snapshot_v1"]["ai_input_preflight_v1"]
    assert preflight["allowed"] is True
    assert preflight["status"] == "partial"
    assert context["source_quality"]["status"] == "partial"
    assert context["source_quality"]["hold_defer_allowed"] is True
    assert context["source_quality"]["warnings"] == [
        "broker_position_or_open_orders_stale_advisory"
    ]
    payload = holding_decision_context_model_payload(context)
    assert payload["source_quality"]["warnings"] == [
        "broker_position_or_open_orders_stale_advisory"
    ]


def test_nxt_current_session_view_honors_authoritative_zero_broker_quantity(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 31, 16, 10, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "remaining_qty": 0,
        "buy_qty": 20,
        "broker_holding_qty": 0,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "broker_snapshot_at": now.timestamp() - 0.2,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    ws.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {
                "0B": "066570_AL",
                "0D": "066570_AL",
            },
            "last_realtime_type_market_suffix": {"0B": "_AL", "0D": "_AL"},
            "last_realtime_type_market_route": {
                "0B": "krx_nxt_integrated",
                "0D": "krx_nxt_integrated",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "066570",
        ws,
        stock,
        "NXT",
        "nxt_aftermarket",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 31, 15, 30, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 60},
    )

    assert context["broker_route_provenance"] == {
        "route": None,
        "source": "missing",
        "authority": "broker_execution_provenance_required",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
    }
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["broker_route"] is None
    assert (
        "nxt_aftermarket_source_unproven"
        in snapshot["ai_input_preflight_v1"]["blockers"]
    )
    assert snapshot["ai_input_preflight_v1"]["allowed"] is False


@pytest.mark.parametrize("decision_kind", ["holding_score", "holding_flow"])
def test_krx_real_sor_holding_uses_integrated_execution_view(
    monkeypatch,
    decision_kind,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "entry_execution_broker_route": "SOR",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "broker_snapshot_at": now.timestamp() - 0.2,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    ws.update(
        {
            "last_realtime_type_ts": {
                "0B": now.timestamp() - 0.1,
                "0D": now.timestamp() - 0.2,
            },
            "last_realtime_type_item": {
                "0B": "000660_AL",
                "0D": "000660_AL",
            },
            "last_realtime_type_market_suffix": {"0B": "_AL", "0D": "_AL"},
            "last_realtime_type_market_route": {
                "0B": "krx_nxt_integrated",
                "0D": "krx_nxt_integrated",
            },
        }
    )

    context = build_holding_decision_context(
        None,
        "000660",
        ws,
        stock,
        "KRX",
        "krx_regular",
        decision_kind,
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
        candle_meta={
            "api_id": "ka10080",
            "received_count": 60,
            "entry_candle_request_code": "000660_AL",
        },
    )

    assert context["request_code"] == "000660_AL"
    assert context["rest_route"] == "_AL"
    assert context["source_quality"]["hold_defer_allowed"] is True
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["integrated_sor_route_proven"] is True
    assert snapshot["integrated_sor_execution_view_only"] is True
    assert snapshot["ai_input_preflight_v1"]["allowed"] is True
    assert "candle_source_quality" not in snapshot["ai_input_preflight_v1"]["blockers"]
    assert (
        "krx_integrated_event_venue_unproven"
        not in snapshot["ai_input_preflight_v1"]["blockers"]
    )


def test_krx_real_sor_holding_falls_back_to_fresh_exact_krx_when_al_is_stale(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 8, 4, 9, 15, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "entry_execution_broker_route": "SOR",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "broker_snapshot_at": now.timestamp() - 0.2,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    krx_ticks = [
        {
            "price": 10_300 - index,
            "volume": 5 + index,
            "aggressor_side": side,
            "aggressor_source": "ws_executable_quote",
            "volume_source": "15_abs",
            "received_at_ms": int(now.timestamp() * 1000) - index * 100,
            "market_suffix": "",
            "market_route": "krx_regular",
        }
        for index, side in enumerate(("BUY", "SELL", "BUY"))
    ]
    ws["recent_trade_ticks_by_route"] = {
        "KRX|krx_regular": krx_ticks,
        "_AL|krx_nxt_integrated": list(ws["recent_trade_ticks"]),
    }
    ws["realtime_type_snapshots_by_route"] = {
        "KRX|krx_regular": {
            "0B": {
                "observed_epoch": now.timestamp() - 0.1,
                "item": "000660",
                "market_suffix": "",
                "market_route": "krx_regular",
                "effective_venue": "KRX",
                "current_price": 10_300,
            },
            "0D": {
                "observed_epoch": now.timestamp() - 0.2,
                "item": "000660",
                "market_suffix": "",
                "market_route": "krx_regular",
                "effective_venue": "KRX",
                "orderbook": {
                    "asks": [{"price": 10_301, "volume": 100}],
                    "bids": [{"price": 10_299, "volume": 200}],
                },
            },
        },
        "_AL|krx_nxt_integrated": {
            "0B": {
                "observed_epoch": now.timestamp() - 10.0,
                "item": "000660_AL",
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
                "current_price": 10_280,
            },
            "0D": {
                "observed_epoch": now.timestamp() - 10.0,
                "item": "000660_AL",
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
                "orderbook": {
                    "asks": [{"price": 10_281, "volume": 100}],
                    "bids": [{"price": 10_279, "volume": 200}],
                },
            },
        },
    }

    context = build_holding_decision_context(
        None,
        "000660",
        ws,
        stock,
        "KRX",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=_candles(
            16,
            start=datetime(2026, 8, 4, 9, 0, tzinfo=KST),
        ),
        candle_meta={"api_id": "ka10080", "received_count": 16},
    )

    assert context["request_code"] == "000660"
    selection = context["market_data_route_selection"]
    assert selection["integrated_sor_view_selected"] is False
    assert selection["fallback_to_exact_krx"] is True
    assert selection["integrated_sor_view_status"]["status"] == "unusable"
    assert selection["selected_route_partition"]["selected_key"] == ("KRX|krx_regular")
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["market_data_route"] == "krx_only"
    assert snapshot["sources"]["bbo"]["value"] == {
        "best_bid": 10_299,
        "best_ask": 10_301,
    }
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True
    assert snapshot["ai_input_preflight_v1"]["source_blockers"] == []
    log_fields = holding_decision_context_log_fields(context)
    assert log_fields["holding_context_market_data_fallback_to_exact_krx"] is True


def test_premarket_uses_nxt_route_and_al_requires_equivalence_proof(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 8, 20, 30, tzinfo=KST)
    bars = _candles(20, start=datetime(2026, 7, 23, 8, 0, tzinfo=KST))
    nxt = build_holding_decision_context(
        None,
        "000660",
        _ws(now, suffix="_NX", route="nxt_only"),
        _stock(),
        "PREMARKET_KRX_LIKE",
        "premarket_krx_like",
        "holding_flow",
        now_ts=now,
        recent_candles=bars,
    )
    unproven_al = build_holding_decision_context(
        None,
        "000660_AL",
        _ws(now, suffix="_AL", route="krx_nxt_integrated"),
        _stock(),
        "PREMARKET_KRX_LIKE",
        "premarket_krx_like",
        "holding_flow",
        now_ts=now,
        recent_candles=bars,
    )

    assert nxt["request_code"] == "000660_NX"
    assert nxt["source_quality"]["hold_defer_allowed"] is True
    assert unproven_al["source_quality"]["hold_defer_allowed"] is False
    assert "premarket_al_proof_missing" in unproven_al["candle"]["risk_flags"]


def test_premarket_nx_candles_accept_integrated_ws_only_during_closed_krx_session(
    monkeypatch,
):
    _enable(monkeypatch)
    premarket_now = datetime(2026, 7, 23, 8, 20, 30, tzinfo=KST)
    bars = _candles(20, start=datetime(2026, 7, 23, 8, 0, tzinfo=KST))
    integrated_ws = _ws(
        premarket_now,
        suffix="_AL",
        route="krx_nxt_integrated",
    )

    premarket = build_holding_decision_context(
        None,
        "000660",
        integrated_ws,
        _stock(),
        "PREMARKET_KRX_LIKE",
        "premarket_krx_like",
        "holding_score",
        now_ts=premarket_now,
        recent_candles=bars,
    )

    assert premarket["request_code"] == "000660_NX"
    assert premarket["candle"]["route_equivalence_proven"] is True
    assert (
        premarket["candle"]["route_equivalence"]
        == "nxt_premarket_integrated_ws_to_nx_rest"
    )
    assert premarket["source_quality"]["hold_defer_allowed"] is True

    regular_now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    regular = build_holding_decision_context(
        None,
        "000660",
        _ws(regular_now, suffix="_AL", route="krx_nxt_integrated"),
        _stock(),
        "NXT",
        "nxt_regular_overlap",
        "holding_score",
        now_ts=regular_now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
    )

    assert regular["candle"]["route_equivalence_proven"] is False
    assert regular["source_quality"]["hold_defer_allowed"] is False
    assert "venue_conflict" in regular["candle"]["risk_flags"]


def test_untrusted_ka10003_is_ignored_and_ka10084_fallback_is_bounded(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    ws = _ws(now)
    ws["recent_trade_ticks"] = [
        {
            "aggressor_side": "BUY",
            "aggressor_source": "price_change_heuristic",
            "volume": 100,
            "received_at_ms": int(now.timestamp() * 1000),
        }
    ]
    calls = []

    def _signed_tape(_token, code, limit):
        calls.append((code, limit))
        return [
            {
                "aggressor_side": side,
                "aggressor_aux_raw_15": "+5" if side == "BUY" else "-5",
                "rest_signed_tape_received_at": now.timestamp(),
                "source_timestamp": now.timestamp(),
            }
            for side in ("BUY", "SELL", "BUY")
        ]

    monkeypatch.setattr(kiwoom_utils, "get_recent_signed_trades_ka10084", _signed_tape)
    context = build_holding_decision_context(
        "token",
        "000660",
        ws,
        _stock(),
        "KRX",
        "krx_regular",
        "holding_flow",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )

    assert calls == [("000660", 10)]
    assert context["signed_tape"]["fallback_fetched"] is True
    assert context["signed_tape"]["source"] == "ka10084_signed_tape"
    assert context["signed_tape"]["sample_count"] == 3
    assert context["source_quality"]["signed_tape_fresh"] is False
    assert context["source_quality"]["rest_signed_tape_advisory_fresh"] is True

    cached = build_holding_decision_context(
        "token",
        "000660",
        ws,
        _stock(),
        "KRX",
        "krx_regular",
        "holding_flow",
        now_ts=now + timedelta(seconds=1),
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )
    assert calls == [("000660", 10)]
    assert cached["signed_tape"]["fallback_fetched"] is False
    assert cached["signed_tape"]["fallback_cache_hit"] is True


def test_holding_tape_rejects_declared_cumulative_split_volume(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    ws = _ws(now)
    for tick in ws["recent_trade_ticks"]:
        tick["volume"] = 100_000_000
        tick["volume_source"] = "1030_1031_sum"
    context = build_holding_decision_context(
        None,
        "000660",
        ws,
        _stock(),
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(
            60,
            start=datetime(2026, 7, 23, 9, 0, tzinfo=KST),
        ),
    )

    assert context["signed_tape"]["sample_count"] == 0
    assert context["signed_tape"]["buy_volume"] == 0
    assert context["signed_tape"]["sell_volume"] == 0
    assert context["source_quality"]["signed_tape_fresh"] is False


def test_exit_token_and_order_conflict_prevent_hold_deferral(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "exit_token": "exit-1",
        "broker_order_conflict": True,
    }
    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        stock,
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )

    assert context["source_quality"]["hold_defer_allowed"] is False
    assert "active_exit_token" in context["source_quality"]["blockers"]
    assert "order_or_quantity_conflict" in context["source_quality"]["blockers"]


def test_zero_remaining_qty_and_cached_broker_mismatch_are_not_hidden(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = {
        **_stock(),
        "remaining_qty": 0,
        "buy_qty": 20,
        "broker_holding_qty": 5,
    }
    context = build_holding_decision_context(
        None,
        "000660",
        _ws(now),
        stock,
        "KRX",
        "krx_regular",
        "holding_score",
        now_ts=now,
        recent_candles=_candles(60, start=datetime(2026, 7, 23, 9, 0, tzinfo=KST)),
    )

    assert context["position_lifecycle"]["memory_qty"] == 0
    assert context["position_lifecycle"]["broker_qty"] == 5
    assert context["order_reconciliation"]["quantity_mismatch"] is True
    assert context["source_quality"]["hold_defer_allowed"] is False
    assert "position_invalid" in context["source_quality"]["blockers"]
    assert "order_or_quantity_conflict" in context["source_quality"]["blockers"]


def test_runtime_axes_default_off_and_stage_disjoint(monkeypatch):
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST)
    for name in (
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_KRX_ENABLED",
        "KORSTOCKSCAN_HOLDING_SCORE_CONTEXT_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    assert not holding_decision_context_enabled(
        venue="KRX",
        session="krx_regular",
        decision_kind="holding_score",
        now_ts=now,
    )
    _enable(monkeypatch)
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_FLOW_CONTEXT_ENABLED", "false")
    assert holding_decision_context_enabled(
        venue="KRX",
        session="krx_regular",
        decision_kind="holding_score",
        now_ts=now,
    )
    assert not holding_decision_context_enabled(
        venue="KRX",
        session="krx_regular",
        decision_kind="holding_flow",
        now_ts=now,
    )


def test_runtime_keeps_bounded_nxt_operator_lock_after_activation_date(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setenv("KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_KRX_ENABLED", "false")
    monkeypatch.setenv(
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_PREMARKET_ENABLED", "false"
    )
    monkeypatch.setattr(
        holding_context_module,
        "promotion_activation_state",
        lambda _now: {
            "active": False,
            "activation_source": "promotion_artifact_required_missing_or_invalid",
            "promotion_artifact_required": True,
        },
    )
    now = datetime(2026, 7, 28, 17, 0, tzinfo=KST)

    assert holding_decision_context_enabled(
        venue="NXT",
        session="nxt_aftermarket",
        decision_kind="holding_score",
        now_ts=now,
    )
    assert not holding_decision_context_enabled(
        venue="KRX",
        session="krx_regular",
        decision_kind="holding_score",
        now_ts=now,
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE", "2026-07-29"
    )
    assert not holding_decision_context_enabled(
        venue="NXT",
        session="nxt_aftermarket",
        decision_kind="holding_score",
        now_ts=now,
    )


def test_runtime_limits_invalid_full_market_promotion_to_bounded_nxt(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(
        holding_context_module,
        "promotion_activation_state",
        lambda _now: {
            "active": False,
            "activation_source": "promotion_artifact_required_missing_or_invalid",
            "promotion_artifact_required": True,
        },
    )

    now = datetime(2026, 7, 28, 17, 0, tzinfo=KST)
    assert holding_decision_context_enabled(
        venue="NXT",
        session="nxt_aftermarket",
        decision_kind="holding_flow",
        now_ts=now,
    )
    assert not holding_decision_context_enabled(
        venue="KRX",
        session="krx_regular",
        decision_kind="holding_flow",
        now_ts=now,
    )
    assert not holding_decision_context_enabled(
        venue="PREMARKET_KRX_LIKE",
        session="premarket_krx_like",
        decision_kind="holding_flow",
        now_ts=now,
    )


def test_runtime_fetch_request_code_matches_actual_holding_venue(monkeypatch):
    _enable(monkeypatch)
    regular = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    premarket = datetime(2026, 7, 23, 8, 30, tzinfo=KST).timestamp()
    aftermarket = datetime(2026, 7, 23, 16, 30, tzinfo=KST).timestamp()

    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={"market_suffix": "", "market_route": "krx_regular"},
            decision_kind="holding_score",
            now_ts=regular,
        )
        == "000660"
    )
    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={"market_suffix": "_NX", "market_route": "nxt_only"},
            decision_kind="holding_flow",
            now_ts=regular,
        )
        == "000660_NX"
    )
    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={"market_suffix": "_NX", "market_route": "nxt_only"},
            decision_kind="overnight",
            now_ts=premarket,
        )
        == "000660"
    )
    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
            },
            decision_kind="holding_score",
            now_ts=regular,
        )
        == "000660"
    )
    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
            },
            position_ctx={"entry_execution_broker_route": "SOR"},
            decision_kind="holding_score",
            now_ts=regular,
        )
        == "000660_AL"
    )
    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
            },
            decision_kind="holding_score",
            now_ts=aftermarket,
        )
        == "000660_AL"
    )
    assert (
        state_handlers._resolve_holding_context_request_code(
            "000660",
            ws_data={
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
            },
            position_ctx={
                "simulation_book": "scalp_ai_buy_all",
                "simulated_order": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            decision_kind="holding_flow",
            now_ts=regular,
        )
        == "000660_AL"
    )


@pytest.mark.parametrize('case', ['current', 'missing', 'stale', 'rejected', 'hash', 'source_date'])
def test_dated_vote_policy_activates_only_its_mandatory_context(monkeypatch, case):
    now = datetime(2026, 10, 19, 10, tzinfo=KST)
    receipt = dict(status='verified_incumbent_loaded', source_date='2026-10-16',
                   target_date='2026-10-19', bundle_sha256='a'*64)
    if case == 'missing': receipt = {}
    if case == 'stale': receipt['target_date'] = '2026-10-16'
    if case == 'rejected': receipt['status'] = 'baseline_policy_load_rejected'
    if case == 'hash': receipt['bundle_sha256'] = 'bad'
    if case == 'source_date': receipt['source_date'] = '2026-10-19'
    monkeypatch.setattr(holding_context_module, 'promotion_activation_state',
                        lambda _: dict(activation_source='none', promotion_artifact_required=True))
    monkeypatch.setenv('KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED', 'false')
    for kind in ('holding_path_vote', 'holding_score', 'holding_flow', 'overnight'):
        for venue, session in (('KRX','krx_regular'), ('NXT','nxt_aftermarket'),
                               ('PREMARKET_KRX_LIKE','krx_like_premarket')):
            assert holding_decision_context_enabled(venue=venue,session=session,
                decision_kind=kind,now_ts=now,vote_policy_receipt=receipt) is (
                    case == 'current' and kind == 'holding_path_vote')


@pytest.mark.parametrize('session,hour,suffix,route,broker,market', [
    ('krx_like_premarket',8,'_NX','nxt_only','NXT','PREMARKET'),
    ('krx_regular',10,'_AL','krx_nxt_integrated','SOR','REGULAR'),
    ('krx_nxt_aftermarket',17,'_AL','krx_nxt_integrated','SOR','INTEGRATED_AFTERMARKET'),
])
def test_vote_context_builds_fresh_input_with_overlay_off(monkeypatch, tmp_path, session, hour, suffix, route, broker, market):
    from src.engine.ai.holding_exit_vote import (
        build_path_vote_input, path_vote_input_gaps, normalize_path_vote_bundle, PATH_REASON_PREFIX,
    )
    from src.engine.ai.hot_path_ai_symbol_budget import HotPathAISymbolBudget
    now = datetime(2026,10,19,hour,30,30,tzinfo=KST)
    for name in ('HOLDING_DECISION_CONTEXT_ENABLED','HOLDING_FLOW_CONTEXT_ENABLED',
                 'HOLDING_SCORE_CONTEXT_ENABLED','MULTI_TIMEFRAME_AI_CONTEXT_ENABLED'):
        monkeypatch.setenv('KORSTOCKSCAN_'+name,'false')
    monkeypatch.setattr(holding_context_module, 'promotion_activation_state',
                        lambda _: dict(activation_source='none', promotion_artifact_required=True))
    receipt=dict(status='verified_incumbent_loaded',source_date='2026-10-16',
                 target_date='2026-10-19',bundle_sha256='a'*64)
    monkeypatch.setattr(state_handlers,'_HOLDING_PATH_POLICY_RECEIPT',receipt)
    ws=_ws(now,price=9990,suffix=suffix,route=route)
    ws.update(orderbook=dict(bids=[dict(price=9989,volume=200)],asks=[dict(price=9991,volume=100)]),
        last_realtime_type_ts={'0B':now.timestamp()-.1,'0D':now.timestamp()-.2},
        last_realtime_type_item={'0B':'000660'+suffix,'0D':'000660'+suffix},
        last_realtime_type_market_suffix={'0B':suffix,'0D':suffix},
        last_realtime_type_market_route={'0B':route,'0D':route})
    stock=dict(_stock(),id=7,name='TEST',strategy='SCALPING',status='HOLDING',
        buy_price=10000,code='000660',entry_execution_broker_route=broker,
        _entry_receipt_filled_by_order_no={'BUY-1':20},
        _entry_receipt_executions_by_order_no={'BUY-1':{'FILL-1':dict(cumulative_qty=20)}},
        broker_snapshot_at=now.timestamp(),open_buy_qty=0,open_sell_qty=0,
        estimated_fee_tax_pct=.2,estimated_slippage_bps=1)
    position=dict(buy_price=10000,curr_price=9990,profit_rate=-.3,peak_profit=0,
                  drawdown_from_peak_pct=.3,held_sec=60)
    candles=_candles(30,start=now.replace(minute=0,second=0))
    assert state_handlers._resolve_holding_context_request_code('000660',ws_data=ws,
        position_ctx=stock,decision_kind='holding_path_vote',now_ts=now.timestamp())=='000660'+suffix
    requests=[]
    def fetch(token,code,**kw):
        requests.append((code,kw))
        return candles,dict(api_id='ka10080',entry_candle_request_code=code)
    monkeypatch.setattr(kiwoom_utils,'get_minute_candles_ka10080_with_meta',fetch)
    fetched,meta=state_handlers._get_holding_minute_candles_with_meta('000660',limit=60,
        ws_data=ws,position_ctx=stock,decision_kind='holding_path_vote',now_ts=now.timestamp())
    assert fetched==candles and requests[0][0]=='000660'+suffix
    assert requests[0][1]['explicit_request_code'] is True
    assert requests[0][1]['limit'] == 60
    assert meta['multi_timeframe_auxiliary_fetch'] is False
    def build(at):
        return state_handlers._build_holding_ai_decision_context(stock=stock,code='000660',
            ws_data=ws,decision_kind='holding_path_vote',now_ts=at,recent_candles=candles,
            candle_meta=dict(api_id='ka10080',received_count=30,entry_candle_request_code='000660'+suffix,
                             multi_timeframe_auxiliary_fetch=False),
            recent_ticks=ws['recent_trade_ticks'],position_ctx=position,include_disabled_forensics=True)
    context=build(now.timestamp())
    active,forensic=state_handlers._holding_context_call_views(context)
    assert active is context and forensic is None
    assert context['vote_input_policy']==receipt
    assert context['source_quality']['hold_defer_allowed'] is False
    preflight=snapshot_module.ai_input_preflight(context)
    assert preflight['allowed'] is True, preflight
    common=dict(stock_code='000660',ws_data=ws,recent_ticks=ws['recent_trade_ticks'],recent_candles=candles,
        position_ctx=position,requested_paths=('ADD_REBOUND',),market=market,session_key='2026-10-19',
        position_key='record:7',buy_fill_identity='b'*64,route=route,transport_epoch='1',
        source_generation='native:1',quote_observed_at=now.timestamp()-.2)
    payload=build_path_vote_input(**common,holding_context=context)
    assert path_vote_input_gaps(payload)=={'ADD_REBOUND':()}, payload['source_quality']
    assert 'multi_timeframe_context' not in payload['flow']['candle']
    assert payload['flow']['execution_pnl']['estimated_net_executable_pnl_pct'] is not None
    # The old disabled forensic object cannot become a voter input.
    for bad in (dict(context,enabled=False,forensic_context_only=True),
                dict(context,enabled=True,forensic_context_only=True)):
        rejected=build_path_vote_input(**common,holding_context=bad)
        assert rejected['flow']=={} and rejected['source_quality']['allowed'] is False
    blocked=build_path_vote_input(**common,holding_context=dict(context,
        source_quality=dict(status='blocked',blockers=['active_exit_token'])))
    assert 'source_preflight_blocked' in path_vote_input_gaps(blocked)['ADD_REBOUND']
    assert 'holding_context_source_quality_blocked' in blocked['source_quality']['blockers']
    malformed=build_path_vote_input(**common,holding_context=dict(context,source_quality='invalid'))
    assert malformed['source_quality']['allowed'] is False
    # Existing collector, cadence owner, durable ledger and signal consumer.
    clock=[now.timestamp()]
    monkeypatch.setattr(state_handlers.time,'time',lambda:clock[0])
    monkeypatch.setattr(state_handlers,'DATA_DIR',tmp_path)
    monkeypatch.setattr(state_handlers,'_log_holding_pipeline',lambda *a,**k:None)
    monkeypatch.setattr(state_handlers,'DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET',HotPathAISymbolBudget())
    monkeypatch.setattr(state_handlers,'ws_quote_source_receipt',lambda *a,**k:dict(
        item='000660'+suffix,observed_epoch=clock[0]-.2,market_route=route,
        transport_epoch='1',route_sequence=int(clock[0])))
    calls=[]
    class AI:
        def evaluate_scalping_holding_path_votes(self,*args,**kw):
            calls.append(kw)
            requested=clock[0];clock[0]+=.2
            sid='snapshot-'+str(len(calls))
            rows=normalize_path_vote_bundle(dict(input_snapshot_id=sid,votes=[dict(
                path_id=path,verdict='PASS',conviction='FIRM',
                reason_codes=[PATH_REASON_PREFIX[path]+'fixture']) for path in kw['requested_paths']]),
                requested_paths=kw['requested_paths'],expected_snapshot_id=sid,
                position_key=kw['position_key'],market=kw['market'],session_key=kw['session_key'],
                model='gpt-5.4-nano',route=kw['route'],transport_epoch=kw['transport_epoch'],
                source_generation=kw['source_generation'],requested_at=requested,received_at=clock[0],
                quote_observed_at=kw['quote_observed_at'],buy_fill_identity=kw['buy_fill_identity'],
                buy_fill_legs=kw['buy_fill_legs'])
            return [dict(row,provider_called=True,
                         path_decision_input_sha256=kw['expected_path_hashes'][row['path_id']]) for row in rows]
    for cycle in range(2):
        if cycle:
            clock[0]=now.timestamp()+10
            ws['v_pw']=81
            ws['last_ws_update_ts']=clock[0]
            ws['last_realtime_type_ts']={'0B':clock[0]-.1,'0D':clock[0]-.2}
            for tick in ws['recent_trade_ticks']:tick['received_at_ms']+=10000
            context=build(clock[0])
        assert state_handlers._collect_holding_path_votes(stock=stock,code='000660',ai_engine=AI(),
            ws_data=ws,recent_ticks=ws['recent_trade_ticks'],recent_candles=candles,position_ctx=position,
            holding_context=context,now_ts=clock[0],min_interval_sec=1)=='appended'
        snapshot=state_handlers._holding_path_signal_decision(stock,'000660',path_id='ADD_REBOUND',
            signal_id=f'rebound-{cycle}',signal_at=clock[0]+.1)
        assert snapshot['vote_count']==cycle+1
        assert snapshot['decision']==('PASS' if cycle else 'INSUFFICIENT')
    assert len(calls)==2


def test_disabled_holding_context_builds_only_explicit_forensic_source(monkeypatch):
    calls = []

    monkeypatch.setattr(
        state_handlers,
        "holding_decision_context_enabled",
        lambda **_kwargs: False,
    )

    def _build(*_args, **kwargs):
        calls.append(kwargs)
        return {
            "schema": "holding_decision_context_v1",
            "enabled": True,
            "venue": "KRX",
            "session": "krx_regular",
            "source_quality": {
                "status": "fresh_consistent",
                "hold_defer_allowed": True,
                "blockers": [],
            },
        }

    monkeypatch.setattr(state_handlers, "build_holding_decision_context", _build)
    common = {
        "stock": {"buy_price": 70000, "buy_qty": 1},
        "code": "005930",
        "ws_data": {"curr": 70100},
        "decision_kind": "holding_score",
        "now_ts": datetime(2026, 7, 27, 14, 59, tzinfo=KST).timestamp(),
        "recent_candles": [{"현재가": 70100}],
        "recent_ticks": [{"price": 70100, "volume": 1}],
        "position_ctx": {"buy_price": 70000, "buy_qty": 1},
    }

    assert state_handlers._build_holding_ai_decision_context(**common) is None
    assert calls == []

    source = state_handlers._build_holding_ai_decision_context(
        **common,
        include_disabled_forensics=True,
    )
    active, forensic = state_handlers._holding_context_call_views(source)

    assert source["enabled"] is False
    assert source["forensic_context_only"] is True
    assert source["source_quality"]["status"] == "disabled"
    assert source["source_quality"]["hold_defer_allowed"] is False
    assert active is None
    assert forensic is source
    assert calls[0]["include_investor_source"] is False


def test_hard_and_protect_exit_candidates_prohibit_holding_context_work(
    monkeypatch,
):
    monkeypatch.setattr(
        state_handlers,
        "_rule_float",
        lambda name, default: {
            "SCALP_STOP": -1.5,
            "SCALP_HARD_STOP": -2.5,
        }.get(name, default),
    )

    assert state_handlers._holding_context_prohibited_exit_candidate(
        strategy="SCALPING",
        opening_rotation_active=False,
        is_sell_signal=False,
        exit_requested=False,
        profit_rate=-2.5,
        trailing_stop_price=0,
        current_price=9700,
    )
    assert state_handlers._holding_context_prohibited_exit_candidate(
        strategy="SCALPING",
        opening_rotation_active=False,
        is_sell_signal=False,
        exit_requested=False,
        profit_rate=-1.5,
        trailing_stop_price=0,
        current_price=9850,
    )
    assert state_handlers._holding_context_prohibited_exit_candidate(
        strategy="SCALPING",
        opening_rotation_active=False,
        is_sell_signal=False,
        exit_requested=False,
        profit_rate=0.2,
        trailing_stop_price=10_000,
        current_price=9_990,
    )
    assert not state_handlers._holding_context_prohibited_exit_candidate(
        strategy="SCALPING",
        opening_rotation_active=False,
        is_sell_signal=False,
        exit_requested=False,
        profit_rate=-1.0,
        trailing_stop_price=10_000,
        current_price=10_010,
    )


def test_flow_action_reversal_requires_two_independent_context_changes():
    previous = {
        "executable_pnl_pct": 1.0,
        "candle_regime": "range",
        "candle_slope_3m": 0.01,
        "signed_tape_state": "mixed",
        "ofi_regime": "neutral",
        "source_quality_status": "fresh_consistent",
    }
    one_change = {**previous, "signed_tape_state": "sell_dominated"}
    two_changes = {
        **one_change,
        "ofi_regime": "stable_bearish",
    }

    assert count_holding_context_changes(previous, one_change)[0] == 1
    count, groups = count_holding_context_changes(previous, two_changes)
    assert count == 2
    assert groups == ["signed_tape", "orderbook_ofi"]


def test_log_fields_can_namespace_contract_for_cross_stage_composition():
    context = {
        "schema": "holding_decision_context_v1",
        "enabled": True,
        "decision_kind": "holding_score_submit_authority",
    }

    direct = holding_decision_context_log_fields(context)
    nested = holding_decision_context_log_fields(
        context,
        observation_contract_prefix="holding_context_",
    )

    assert direct["decision_authority"] == "bounded_holding_confirmation"
    assert set(OBSERVATION_CONTRACT).isdisjoint(nested)
    assert all(
        nested[f"holding_context_{key}"] == value
        for key, value in OBSERVATION_CONTRACT.items()
    )
    assert (
        nested["holding_context_decision_authority"] == "bounded_holding_confirmation"
    )
    assert nested["holding_context_metric_role"] == "holding_context_feature_bundle"


@pytest.mark.parametrize("age_seconds", [6.0, -0.001])
def test_holding_quote_uses_0d_clock_instead_of_fresh_transport_or_carried_age(age_seconds):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=KST).timestamp()
    age, _ = holding_context_module._quote_age_ms({
        "last_realtime_type_ts": {"0D": now - age_seconds},
        "last_ws_update_ts": now, "quote_age_ms": 0,
    }, now)
    assert age == pytest.approx(age_seconds * 1000, abs=0.001)
    age, _ = holding_context_module._quote_age_ms({
        "last_realtime_type_ts": None, "last_ws_update_ts": now, "quote_age_ms": 0,
    }, now)
    assert age is None


@pytest.mark.parametrize('fault', [None, 'within_best', 'insufficient', 'stale', 'future', 'crossed',
    'conflict', 'out_of_order', 'bad_cost', 'future_cost', 'unknown_fee', 'explicit_invalid'])
def test_frozen_fee_and_full_visible_depth_feed_exit_vote_without_actual_cost_claim(monkeypatch, fault):
    from src.engine.ai.holding_exit_vote import build_path_vote_input, path_vote_input_gaps
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST)
    stock = dict(_stock(), buy_qty=220, broker_holding_qty=220,
        _trailing_entry_cost_model=dict(buy_cost_krw=0, sell_cost_rate=.0023,
            source_sha256='a'*64, known_at=now.timestamp()-60, actual_broker_cost=False,
            allocation='frozen_configured_round_trip_rate_on_sell_model_only'))
    ws = _ws(now)
    ws['orderbook'] = dict(bids=[dict(price=10299, volume=200),dict(price=10298,volume=100)])
    if fault == 'within_best': stock.update(buy_qty=20, broker_holding_qty=20)
    if fault == 'insufficient': ws['orderbook']['bids'][1]['volume'] = 1
    if fault in ('stale','future'):
        ws.setdefault('last_realtime_type_ts', {})['0D'] = now.timestamp() + (1 if fault == 'future' else -4)
        ws['quote_age_ms'] = -1000 if fault == 'future' else 4000
    if fault == 'crossed': ws['best_ask'] = 10298
    if fault == 'conflict': ws['orderbook']['bids'][0]['volume'] = 201
    if fault == 'out_of_order': ws['orderbook']['bids'][1]['price'] = 10300
    if fault == 'bad_cost': stock['_trailing_entry_cost_model']['actual_broker_cost'] = True
    if fault == 'future_cost': stock['_trailing_entry_cost_model']['known_at'] = now.timestamp()+1
    if fault == 'unknown_fee': stock.pop('_trailing_entry_cost_model')
    if fault == 'explicit_invalid': stock['estimated_slippage_bps'] = float('nan')
    ctx = build_holding_decision_context(None, '000660', ws, stock, 'KRX', 'krx_regular',
        'holding_score', now_ts=now,
        recent_candles=_candles(60,start=datetime(2026,7,23,9,0,tzinfo=KST)))
    pnl = ctx['execution_pnl']
    payload = build_path_vote_input(stock_code='000660', ws_data=ws,
        recent_ticks=ws['recent_trade_ticks'], recent_candles=[],
        position_ctx=dict(drawdown_from_peak_pct=.4),requested_paths=('EXIT_TRAILING_TP',),
        holding_context=ctx, market='REGULAR',session_key='2026-07-23',position_key='record:1',
        buy_fill_identity='b'*64,route='KRX',transport_epoch='1',source_generation='native:1',
        quote_observed_at=now.timestamp())
    if fault in (None,'within_best'):
        vwap = (200*10299+20*10298)/220 if fault is None else 10299
        expected = (vwap*(1-.0023)/10000-1)*100
        assert pnl['estimated_net_executable_pnl_pct'] == pytest.approx(round(expected,4))
        assert (pnl['estimated_slippage_bps'] > 0) is (fault is None)
        assert pnl['cost_estimate_source']['depth_levels'] == (2 if fault is None else 1)
        assert payload['flow']['execution_pnl']['cost_estimate_source'] == pnl['cost_estimate_source']
        assert pnl['cost_estimate_source']['actual_broker_cost'] is False
        assert pnl['cost_estimate_source']['actual_fill'] is False
        assert 'executable_exit_pnl_missing' not in path_vote_input_gaps(payload)['EXIT_TRAILING_TP']
    else:
        assert pnl['estimated_net_executable_pnl_pct'] is None
        assert 'executable_exit_pnl_missing' in path_vote_input_gaps(payload)['EXIT_TRAILING_TP']
