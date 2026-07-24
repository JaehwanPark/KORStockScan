from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine import sniper_state_handlers as state_handlers
from src.engine.scalping import ai_market_snapshot as snapshot_module
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
    assert context["candle"]["current_session_bar_count"] == 60
    assert len(context["candle"]["bars"]) == 20
    assert context["candle"]["structure"]["returns_pct"]["1"] is not None
    assert context["candle"]["structure"]["returns_pct"]["60"] is not None
    assert context["execution_pnl"]["mark_pnl_pct"] == 3.0
    assert context["execution_pnl"]["executable_pnl_pct"] == 2.99
    assert context["source_quality"]["hold_defer_allowed"] is True
    assert context["observation_contract"] == OBSERVATION_CONTRACT
    model_payload = holding_decision_context_model_payload(context)
    assert model_payload["schema"] == "holding_decision_context_v1"
    assert model_payload["candle"]["model_bar_count"] == 20
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
    assert (
        log_fields["holding_context_model_structure"]["returns_pct"]["60"] is not None
    )
    assert log_fields["holding_context_ai_market_snapshot"]["schema"] == (
        "ai_market_snapshot_v1"
    )


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
        == "000660_AL"
    )


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
