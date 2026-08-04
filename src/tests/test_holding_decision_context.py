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


def test_nxt_aftermarket_real_holding_uses_current_session_execution_view(
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
        "route": "NXT",
        "source": "current_session_nxt_candle_route_equivalence",
        "authority": "current_session_execution_view_only_no_fill_claim",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
    }
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["broker_route"] == "NXT"
    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["broker_route_matches_venue"] is True
    assert "nxt_aftermarket_source_unproven" not in preflight["blockers"]
    assert preflight["allowed"] is True
    log_fields = holding_decision_context_log_fields(context)
    assert log_fields["holding_context_broker_route_provenance_state"] == (
        "observation_view_only"
    )
    assert log_fields["holding_context_broker_snapshot_freshness_state"] == "fresh"


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
        "overnight",
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
        "overnight",
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
        == "000660_NX"
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
