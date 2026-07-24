from __future__ import annotations

import inspect
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine import sniper_state_handlers as state_handlers
from src.engine.ai_engine_openai import GPTSniperEngine
from src.engine.ai_prompt_contracts import (
    SCALPING_SYSTEM_PROMPT,
    SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
    SCALPING_WATCHING_SYSTEM_PROMPT,
)
from src.engine.scalping.entry_candle_context import (
    OBSERVATION_CONTRACT,
    apply_entry_candle_hybrid_guard,
    build_entry_candle_context,
    entry_candle_context_enabled,
    fetch_entry_candles_with_meta,
    resolve_entry_candle_request_code,
)

KST = ZoneInfo("Asia/Seoul")


def _enable(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ACTIVE_DATE", "2026-07-23")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_KRX_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_NXT_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_PREMARKET_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_CANDLE_HYBRID_GUARD_ENABLED", "true")


def _candles(
    count: int,
    *,
    day: str = "20260723",
    start_hour: int = 9,
    start_minute: int = 0,
    base: int = 10000,
    step: int = 10,
):
    rows = []
    total_start = start_hour * 60 + start_minute
    for index in range(count):
        minute_of_day = total_start + index
        hour, minute = divmod(minute_of_day, 60)
        close = base + index * step
        rows.append(
            {
                "source_timestamp": f"{day}{hour:02d}{minute:02d}00",
                "체결시간": f"{hour:02d}:{minute:02d}:00",
                "시가": close - 3,
                "고가": close + 5,
                "저가": close - 5,
                "현재가": close,
                "거래량": 100 + index,
            }
        )
    return rows


def _ws(price=10400):
    return {
        "curr": price,
        "quote_age_ms": 100,
        "quote_stale": False,
        "market_suffix": "",
        "market_route": "krx_regular",
        "orderbook": {
            "asks": [{"price": price + 10, "volume": 100}],
            "bids": [{"price": price, "volume": 200}],
        },
        "recent_trade_ticks": [],
    }


def test_builder_keeps_current_session_separate_and_compresses_latest_twenty(
    monkeypatch,
):
    _enable(monkeypatch)
    bars = _candles(5, day="20260722") + _candles(25)
    context = build_entry_candle_context(
        "token",
        "000660",
        _ws(),
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 9, 25, 30, tzinfo=KST),
        recent_candles=bars,
        source_meta={"api_id": "ka10080", "received_count": 30},
    )

    assert context["schema"] == "entry_candle_context_v1"
    assert context["enabled"] is True
    assert context["current_session_bar_count"] == 25
    assert context["previous_session_bar_count"] == 5
    assert len(context["bars"]) == 20
    assert context["bars"][0]["t"] == "09:05"
    assert context["bars"][-1]["t"] == "09:24"
    assert context["sample_mode"] == "full_structure"
    assert context["structure"]["returns_pct"]["20"] is not None
    assert context["structure"]["slopes_pct_per_bar"]["20"] is not None
    assert context["structure"]["ranges_pct"]["20"] is not None
    assert "latest_body_ratio" in context["structure"]
    assert "latest_lower_wick_ratio" in context["structure"]
    assert "volume_direction_alignment" in context["structure"]
    assert context["observation_contract"] == OBSERVATION_CONTRACT


def test_builder_uses_route_consistent_ws_tick_for_forming_bar(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 9, 20, 30, tzinfo=KST)
    ws = _ws(10200)
    ws["market_suffix"] = "_NX"
    ws["market_route"] = "nxt_only"
    ws["recent_trade_ticks"] = [
        {
            "time": "09:20:20",
            "price": 10210,
            "volume": 3,
            "market_suffix": "_NX",
            "market_route": "nxt_only",
        },
        {
            "time": "09:20:10",
            "price": 9900,
            "volume": 2,
            "market_suffix": "",
            "market_route": "krx_regular",
        },
    ]
    context = build_entry_candle_context(
        "token",
        "000660_NX",
        ws,
        venue="NXT",
        session="krx_regular",
        now_ts=now,
        recent_candles=_candles(20),
        source_meta={},
    )

    assert context["forming_bar_present"] is True
    assert context["bars"][-1]["c"] == 10210
    assert context["bars"][-1]["partial_volume"] is True
    assert context["source_quality"]["route_conflict_count"] == 1
    assert context["source_quality"]["status"] == "blocked"


def test_builder_excludes_untrusted_tick_volume_from_forming_bar(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 9, 20, 30, tzinfo=KST)
    ws = _ws(10200)
    ws["recent_trade_ticks"] = [
        {
            "time": "09:20:20",
            "price": 10210,
            "volume": 999_999_999,
            "volume_source": "1030_1031_sum",
            "market_suffix": "",
            "market_route": "krx_regular",
        },
        {
            "time": "09:20:10",
            "price": 10200,
            "volume": 7,
            "volume_source": "15_abs",
            "market_suffix": "",
            "market_route": "krx_regular",
        },
    ]
    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="KRX",
        session="krx_regular",
        now_ts=now,
        recent_candles=_candles(21),
        source_meta={},
    )

    assert context["bars"][-1]["v"] == 120
    assert context["structure"]["volume_ratio"] is None
    assert (
        context["structure"]["volume_direction_alignment"]
        == "forming_partial_not_comparable"
    )
    assert context["source_quality"]["trusted_tick_volume_count"] == 1
    assert context["source_quality"]["untrusted_tick_volume_count"] == 1
    assert context["source_quality"]["tick_volume_source_counts"] == {
        "1030_1031_sum": 1,
        "15_abs": 1,
    }


def test_builder_marks_two_or_more_missing_bars_as_source_quality_block(monkeypatch):
    _enable(monkeypatch)
    bars = _candles(5)
    bars.pop(2)
    bars.pop(2)
    context = build_entry_candle_context(
        "token",
        "000660",
        _ws(),
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 9, 5, 20, tzinfo=KST),
        recent_candles=bars,
        source_meta={},
    )

    assert context["source_quality"]["missing_bar_count"] >= 2
    assert context["source_quality"]["max_consecutive_missing_bar_count"] >= 2
    assert "consecutive_bar_gap" in context["risk_flags"]


def test_builder_does_not_treat_separate_single_gaps_as_consecutive(monkeypatch):
    _enable(monkeypatch)
    bars = _candles(7)
    bars = [bar for index, bar in enumerate(bars) if index not in {1, 5}]
    context = build_entry_candle_context(
        "token",
        "000660",
        _ws(),
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 9, 7, 20, tzinfo=KST),
        recent_candles=bars,
        source_meta={},
    )

    assert context["source_quality"]["missing_bar_count"] == 2
    assert context["source_quality"]["max_consecutive_missing_bar_count"] == 1
    assert "consecutive_bar_gap" not in context["risk_flags"]


def test_rest_current_minute_is_forming_without_ws_tick(monkeypatch):
    _enable(monkeypatch)
    context = build_entry_candle_context(
        "token",
        "000660",
        {**_ws(10040), "recent_trade_ticks": []},
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 9, 4, 20, tzinfo=KST),
        recent_candles=_candles(5),
        source_meta={},
    )

    assert context["forming_bar_present"] is True
    assert context["completed_bar_count"] == 4
    assert context["bars"][-1]["partial_volume"] is True


def test_opening_sample_does_not_infer_full_trend(monkeypatch):
    _enable(monkeypatch)
    context = build_entry_candle_context(
        "token",
        "000660",
        _ws(),
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 9, 2, 30, tzinfo=KST),
        recent_candles=_candles(2),
        source_meta={},
    )

    assert context["sample_mode"] == "opening_flow_only"
    assert context["regime"] == "opening_flow"


def test_venue_request_code_contract_and_dated_activation(monkeypatch):
    _enable(monkeypatch)
    assert (
        resolve_entry_candle_request_code("000660", venue="KRX", session="krx_regular")
        == "000660"
    )
    assert (
        resolve_entry_candle_request_code(
            "000660_NX", venue="KRX", session="krx_regular"
        )
        == "000660"
    )
    assert (
        resolve_entry_candle_request_code(
            "000660", venue="NXT", session="nxt_aftermarket"
        )
        == "000660_NX"
    )
    assert (
        resolve_entry_candle_request_code(
            "000660", venue="PREMARKET_KRX_LIKE", session="premarket_krx_like"
        )
        == "000660_NX"
    )
    assert (
        resolve_entry_candle_request_code(
            "000660_AL",
            venue="PREMARKET_KRX_LIKE",
            session="premarket_krx_like",
        )
        == "000660_AL"
    )
    assert (
        resolve_entry_candle_request_code("000660", venue="SOR", session="krx_regular")
        == "000660_AL"
    )
    assert entry_candle_context_enabled(
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 10, 0, tzinfo=KST),
    )
    assert not entry_candle_context_enabled(
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 24, 10, 0, tzinfo=KST),
    )


def test_fetch_entry_candles_uses_effective_route_and_records_provenance(monkeypatch):
    _enable(monkeypatch)
    requested = []

    def _fetch(_token, code, limit, *, explicit_request_code=False):
        requested.append((code, limit, explicit_request_code))
        return _candles(3, start_hour=16), {"api_id": "ka10080"}

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_minute_candles_ka10080_with_meta",
        _fetch,
    )
    candles, metadata = fetch_entry_candles_with_meta(
        "token",
        "000660",
        {
            **_ws(),
            "market_suffix": "_NX",
            "market_route": "nxt_only",
        },
        venue="NXT",
        session="nxt_aftermarket",
        limit=40,
        now_ts=datetime(2026, 7, 23, 16, 3, tzinfo=KST),
    )

    assert requested == [("000660_NX", 40, True)]
    assert len(candles) == 3
    assert metadata["entry_candle_request_code"] == "000660_NX"
    assert metadata["entry_candle_request_venue"] == "NXT"
    assert metadata["entry_candle_request_session"] == "nxt_aftermarket"


def test_builder_blocks_prefetched_candles_from_wrong_rest_route(monkeypatch):
    _enable(monkeypatch)
    context = build_entry_candle_context(
        "token",
        "000660",
        {
            **_ws(),
            "market_suffix": "_NX",
            "market_route": "nxt_only",
        },
        venue="NXT",
        session="nxt_regular_overlap",
        now_ts=datetime(2026, 7, 23, 10, 0, tzinfo=KST),
        recent_candles=_candles(20, start_minute=40),
        source_meta={
            "api_id": "ka10080",
            "entry_candle_request_code": "000660",
            "entry_candle_request_venue": "KRX",
            "entry_candle_request_session": "krx_regular",
        },
    )

    assert context["request_code"] == "000660_NX"
    assert context["source_quality"]["status"] == "blocked"
    assert "rest_request_code_conflict" in context["risk_flags"]


def test_actual_ws_route_keys_select_nxt_and_premarket_al_requires_proof(monkeypatch):
    _enable(monkeypatch)
    nxt_ws = _ws(10000)
    nxt_ws.pop("market_suffix")
    nxt_ws.pop("market_route")
    nxt_ws["last_ws_market_suffix"] = "_NX"
    nxt_ws["last_ws_market_route"] = "nxt_only"
    nxt = build_entry_candle_context(
        "token",
        "000660",
        nxt_ws,
        venue=None,
        session=None,
        now_ts=datetime(2026, 7, 23, 10, 0, tzinfo=KST),
        recent_candles=_candles(20, start_minute=40),
        source_meta={},
    )
    premarket = build_entry_candle_context(
        "token",
        "000660_AL",
        {
            **_ws(10000),
            "market_suffix": "_AL",
            "market_route": "krx_nxt_integrated",
        },
        venue="PREMARKET_KRX_LIKE",
        session="premarket_krx_like",
        now_ts=datetime(2026, 7, 23, 8, 20, tzinfo=KST),
        recent_candles=_candles(20, start_hour=8),
        source_meta={},
    )
    assert nxt["venue"] == "NXT"
    assert nxt["session"] == "nxt_regular_overlap"
    assert nxt["request_code"] == "000660_NX"
    assert "premarket_al_proof_missing" in premarket["risk_flags"]


def test_krx_sor_order_route_stays_krx_cohort_with_integrated_market_data(
    monkeypatch,
):
    _enable(monkeypatch)
    ws = _ws(10000)
    ws["market_suffix"] = "_AL"
    ws["market_route"] = "krx_nxt_integrated"

    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="SOR",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 10, 0, tzinfo=KST),
        recent_candles=_candles(20, start_minute=40),
        source_meta={},
        broker_route="SOR",
    )

    assert context["venue"] == "KRX"
    assert context["request_code"] == "000660_AL"
    assert context["rest_route"] == "_AL"
    assert context["ws_route"] == "krx_nxt_integrated"
    assert context["source_quality"]["status"] == "fresh_consistent"
    snapshot = context["ai_market_snapshot_v1"]
    assert snapshot["effective_venue"] == "KRX"
    assert snapshot["broker_route"] == "SOR"
    assert snapshot["market_data_route"] == "krx_nxt_integrated"
    assert snapshot["underlying_event_venue"] is None


def test_nxt_aftermarket_accepts_integrated_ws_only_with_closed_session_proof(
    monkeypatch,
):
    _enable(monkeypatch)
    ws = _ws(10200)
    ws.pop("market_suffix")
    ws.pop("market_route")
    ws["last_ws_market_suffix"] = "_AL"
    ws["last_ws_market_route"] = "krx_nxt_integrated"
    ws["recent_trade_ticks"] = [
        {
            "time": "16:20:20",
            "price": 10210,
            "volume": 3,
            "market_suffix": "_AL",
            "market_route": "krx_nxt_integrated",
        }
    ]
    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="NXT",
        session="nxt_aftermarket",
        now_ts=datetime(2026, 7, 23, 16, 20, 30, tzinfo=KST),
        recent_candles=_candles(20, start_hour=16),
        source_meta={},
    )

    assert context["request_code"] == "000660_NX"
    assert context["route_equivalence_proven"] is True
    assert context["route_equivalence"] == "nxt_aftermarket_integrated_ws_to_nx_rest"
    assert context["source_quality"]["route_equivalence_proof"]["proven"] is True
    assert context["source_quality"]["status"] == "fresh_consistent"
    assert context["source_quality"]["route_conflict_count"] == 0
    assert context["bars"][-1]["c"] == 10210


def test_premarket_accepts_integrated_ws_with_closed_krx_session_proof(monkeypatch):
    _enable(monkeypatch)
    ws = _ws(128300)
    ws["market_suffix"] = "_AL"
    ws["market_route"] = "krx_nxt_integrated"
    ws["recent_trade_ticks"] = [
        {
            "time": "08:08:20",
            "price": 128300,
            "volume": 3,
            "market_suffix": "_AL",
            "market_route": "krx_nxt_integrated",
        }
    ]

    context = build_entry_candle_context(
        "token",
        "096770",
        ws,
        venue="PREMARKET_KRX_LIKE",
        session="premarket_krx_like",
        now_ts=datetime(2026, 7, 24, 8, 8, 30, tzinfo=KST),
        recent_candles=_candles(9, start_hour=8),
        source_meta={},
    )

    assert context["request_code"] == "096770_NX"
    assert context["route_equivalence_proven"] is True
    assert context["route_equivalence"] == "nxt_premarket_integrated_ws_to_nx_rest"
    proof = context["source_quality"]["route_equivalence_proof"]
    assert proof["proof_session"] == "premarket_krx_like"
    assert proof["krx_regular_closed_by_clock"] is True
    assert context["source_quality"]["status"] == "fresh_consistent"


def test_premarket_integrated_equivalence_closes_at_krx_regular_open(monkeypatch):
    _enable(monkeypatch)
    ws = _ws(128300)
    ws["market_suffix"] = "_AL"
    ws["market_route"] = "krx_nxt_integrated"

    context = build_entry_candle_context(
        "token",
        "096770",
        ws,
        venue="PREMARKET_KRX_LIKE",
        session="premarket_krx_like",
        now_ts=datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST),
        recent_candles=_candles(20, start_minute=40),
        source_meta={},
    )

    assert context["request_code"] == "096770_NX"
    assert context["route_equivalence_proven"] is False
    assert context["source_quality"]["status"] == "blocked"
    assert "venue_conflict" in context["risk_flags"]


def test_nxt_integrated_ws_is_not_equivalent_during_regular_overlap(monkeypatch):
    _enable(monkeypatch)
    ws = _ws(10200)
    ws["market_suffix"] = "_AL"
    ws["market_route"] = "krx_nxt_integrated"
    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="NXT",
        session="nxt_regular_overlap",
        now_ts=datetime(2026, 7, 23, 10, 0, 30, tzinfo=KST),
        recent_candles=_candles(20, start_minute=40),
        source_meta={},
    )

    assert context["route_equivalence_proven"] is False
    assert context["source_quality"]["status"] == "blocked"
    assert "venue_conflict" in context["risk_flags"]


def test_nxt_aftermarket_rejects_tick_from_non_equivalent_route(monkeypatch):
    _enable(monkeypatch)
    ws = _ws(10200)
    ws["market_suffix"] = "_AL"
    ws["market_route"] = "krx_nxt_integrated"
    ws["recent_trade_ticks"] = [
        {
            "time": "16:20:20",
            "price": 10210,
            "volume": 3,
            "market_suffix": "_NX",
            "market_route": "nxt_only",
        }
    ]
    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="NXT",
        session="nxt_aftermarket",
        now_ts=datetime(2026, 7, 23, 16, 20, 30, tzinfo=KST),
        recent_candles=_candles(20, start_hour=16),
        source_meta={},
    )

    assert context["route_equivalence_proven"] is True
    assert context["source_quality"]["route_conflict_count"] == 1
    assert context["source_quality"]["status"] == "blocked"


def test_nxt_aftermarket_uses_route_partition_without_cross_route_poisoning(
    monkeypatch,
):
    _enable(monkeypatch)
    ws = _ws(10200)
    # A KRX tick may be the latest aggregate observation even while the
    # position-owned NXT route has a valid partition.
    ws["market_suffix"] = ""
    ws["market_route"] = "krx_regular"
    nxt_tick = {
        "time": "16:20:20",
        "price": 10210,
        "volume": 3,
        "market_suffix": "_NX",
        "market_route": "nxt_only",
    }
    krx_tick = {
        "time": "16:20:21",
        "price": 9990,
        "volume": 9,
        "market_suffix": "",
        "market_route": "krx_regular",
    }
    ws["recent_trade_ticks"] = [krx_tick, nxt_tick]
    ws["recent_trade_ticks_by_route"] = {
        "_NX|nxt_only": [nxt_tick],
        "KRX|krx_regular": [krx_tick],
    }

    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="NXT",
        session="nxt_aftermarket",
        now_ts=datetime(2026, 7, 23, 16, 20, 30, tzinfo=KST),
        recent_candles=_candles(20, start_hour=16),
        source_meta={},
    )

    quality = context["source_quality"]
    assert quality["status"] == "fresh_consistent"
    assert quality["route_conflict_count"] == 0
    assert quality["route_partition_used"] is True
    assert quality["route_partition_expected_key"] == "_NX|nxt_only"
    assert quality["route_partition_selected_route"] == "nxt_only"
    assert quality["route_partition_ignored_tick_count"] == 1
    assert context["bars"][-1]["c"] == 10210


def test_krx_context_blocks_nxt_ws_suffix_even_without_route_label(monkeypatch):
    _enable(monkeypatch)
    ws = _ws(10000)
    ws["market_suffix"] = "_NX"
    ws["market_route"] = ""
    context = build_entry_candle_context(
        "token",
        "000660",
        ws,
        venue="KRX",
        session="krx_regular",
        now_ts=datetime(2026, 7, 23, 9, 20, 30, tzinfo=KST),
        recent_candles=_candles(20),
        source_meta={},
    )

    assert context["source_quality"]["status"] == "blocked"
    assert "venue_conflict" in context["risk_flags"]


def _guard_context(*, regime: str, quality: str = "fresh_consistent"):
    return {
        "enabled": True,
        "regime": regime,
        "source_quality": {"status": quality, "blockers": []},
        "structure": {"returns_pct": {"3": 0.2}},
        "bars": [{"c": 10000}],
    }


def test_hybrid_guard_preserves_neutral_buy_and_never_upgrades_wait(monkeypatch):
    _enable(monkeypatch)
    buy = apply_entry_candle_hybrid_guard(
        {"action": "BUY", "score": 80, "reason": "valid"},
        _guard_context(regime="range"),
        _ws(10000),
        [],
    )
    wait = apply_entry_candle_hybrid_guard(
        {"action": "WAIT", "score": 70, "reason": "mixed"},
        _guard_context(regime="breakout"),
        _ws(10000),
        [],
    )
    assert buy["action"] == "BUY"
    assert buy["entry_candle_hybrid_guard"]["result"].startswith("preserve")
    assert wait["action"] == "WAIT"


def test_hybrid_guard_demotes_quality_conflict_and_unconfirmed_adverse(monkeypatch):
    _enable(monkeypatch)
    stale = apply_entry_candle_hybrid_guard(
        {"action": "BUY", "score": 90, "reason": "valid"},
        _guard_context(regime="range", quality="blocked"),
        _ws(10000),
        [],
    )
    adverse_ws = _ws(9990)
    adverse_ws["orderbook"] = {
        "asks": [{"price": 10000, "volume": 300}],
        "bids": [{"price": 9990, "volume": 100}],
    }
    adverse = apply_entry_candle_hybrid_guard(
        {"action": "BUY", "score": 86, "reason": "valid"},
        _guard_context(regime="downtrend_bounce"),
        adverse_ws,
        [{"aggressor_side": "SELL", "volume": 50}],
    )
    assert stale["action"] == "WAIT"
    assert stale["score"] == 74
    assert adverse["action"] == "WAIT"
    assert (
        adverse["entry_candle_hybrid_guard"]["result"] == "demote_adverse_unconfirmed"
    )


def test_hybrid_guard_keeps_adverse_buy_only_with_two_clean_groups(monkeypatch):
    _enable(monkeypatch)
    result = apply_entry_candle_hybrid_guard(
        {"action": "BUY", "score": 82, "reason": "valid"},
        _guard_context(regime="failed_breakout"),
        _ws(10010),
        [
            {"aggressor_side": "BUY", "volume": 30},
            {"aggressor_side": "BUY", "volume": 20},
            {"aggressor_side": "SELL", "volume": 5},
        ],
    )
    assert result["action"] == "BUY"
    assert (
        result["entry_candle_hybrid_guard"]["result"]
        == "preserve_independent_confirmation"
    )
    assert len(result["entry_candle_hybrid_guard"]["positive_groups"]) >= 2


def test_hot_and_entry_price_payloads_include_common_context(monkeypatch):
    _enable(monkeypatch)
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    context = {
        **_guard_context(regime="range"),
        "schema": "entry_candle_context_v1",
        "enabled": True,
        "venue": "KRX",
        "session": "krx_regular",
        "ai_market_snapshot_v1": {
            "schema": "ai_market_snapshot_v1",
            "snapshot_id": "aims-payload-contract",
            "effective_venue": "KRX",
            "broker_route": "SOR",
            "market_data_route": "krx_nxt_integrated",
            "underlying_event_venue": None,
            "underlying_event_venue_source": "not_provided",
        },
        "current_session_bar_count": 10,
        "completed_bar_count": 10,
        "forming_bar_present": False,
        "latest_bar_age_sec": 10,
        "sample_mode": "full_structure",
        "alignment": "neutral",
        "risk_flags": [],
    }
    hot = engine._build_entry_screen_hot_payload(
        _ws(10000),
        [],
        _candles(10),
        feature_packet={},
        candle_context=context,
    )
    price = engine._build_scalping_entry_price_user_input(
        stock_name="test",
        stock_code="000660",
        ws_data=_ws(10000),
        recent_ticks=[],
        recent_candles=_candles(10),
        price_ctx={},
        candle_context=context,
    )
    price_payload = json.loads(price)
    assert hot["entry_candle_context"]["schema"] == "entry_candle_context_v1"
    assert hot["entry_candle_context"]["bar_schema"]["order"] == "oldest_to_latest"
    assert hot["ai_market_snapshot_v1"]["snapshot_id"] == "aims-payload-contract"
    assert hot["ai_input_semantics"]["canonical_candle_owner"] == (
        "entry_candle_context"
    )
    assert price_payload["entry_candle_context"]["schema"] == (
        "entry_candle_context_v1"
    )
    assert "recent_candles" not in price_payload
    assert "candle_summary" not in price_payload
    assert price_payload["ai_input_semantics"]["duplicate_candle_views_omitted"] is True


def test_gatekeeper_packet_and_entry_prompts_keep_compact_context_contract(monkeypatch):
    _enable(monkeypatch)
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    context = {
        **_guard_context(regime="range"),
        "schema": "entry_candle_context_v1",
        "venue": "KRX",
        "session": "krx_regular",
        "current_session_bar_count": 10,
        "completed_bar_count": 10,
        "forming_bar_present": False,
        "latest_bar_age_sec": 10,
        "sample_mode": "full_structure",
        "alignment": "neutral",
        "risk_flags": [],
    }
    packet = engine._build_realtime_quant_packet(
        "test",
        "000660",
        {"entry_candle_context": context},
        "SWING",
    )
    assert "[ENTRY_CANDLE_CONTEXT]" in packet
    assert "entry_candle_context_v1" in packet
    for prompt in (
        SCALPING_SYSTEM_PROMPT,
        SCALPING_WATCHING_SYSTEM_PROMPT,
        SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
    ):
        assert "20 or fewer words" in prompt
        assert '"action"' in prompt
        assert '"score"' in prompt
        assert '"reason"' in prompt


def test_runtime_call_sites_use_context_and_s15_no_longer_sends_empty_candles():
    root = Path(__file__).resolve().parents[1]
    state_source = (root / "engine" / "sniper_state_handlers.py").read_text()
    s15_source = (root / "engine" / "sniper_s15_fast_track.py").read_text()
    analysis_source = (root / "engine" / "sniper_analysis.py").read_text()
    ipo_source = (root / "engine" / "ipo_listing_day_runner.py").read_text()

    assert "candle_context=candle_context" in state_source
    assert "candle_context=gatekeeper_candle_context" not in state_source
    assert "recent_candles=[]" not in s15_source
    assert "candle_context=candle_context" in s15_source
    assert "candle_context=candle_context" in analysis_source
    assert "entry_candle_context" in ipo_source
    for source in (state_source, s15_source, analysis_source, ipo_source):
        assert "fetch_entry_candles_with_meta" in source
    assert "get_minute_candles_ka10080_with_meta" not in s15_source
    assert "get_minute_candles_ka10080_with_meta" not in analysis_source
    assert "get_minute_candles_ka10080_with_meta" not in ipo_source
    assert (
        "candle_context" in inspect.signature(GPTSniperEngine.analyze_target).parameters
    )
    assert (
        "candle_context"
        in inspect.signature(GPTSniperEngine.evaluate_scalping_entry_price).parameters
    )


def test_entry_price_skips_provider_and_blocks_submit_for_blocked_context(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 16, 20, 30, tzinfo=KST)
    monkeypatch.setattr(state_handlers.time, "time", lambda: now.timestamp())
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_minute_candles_ka10080_with_meta",
        lambda *args, **kwargs: (
            _candles(20, start_hour=16),
            {"api_id": "ka10080", "received_count": 20},
        ),
    )
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    class DummyAI:
        def __init__(self):
            self.calls = 0

        def evaluate_scalping_entry_price(self, *args, **kwargs):
            self.calls += 1
            raise AssertionError("blocked candle context must skip provider")

    ai = DummyAI()
    latency_gate = {
        "target_buy_price": 10000,
        "latency_guarded_order_price": 10000,
        "normal_defensive_order_price": 10000,
        "order_price": 10000,
        "latency_state": "SAFE",
        "quote_stale": False,
    }
    planned_orders = [{"tag": "normal", "qty": 1, "price": 10000}]
    ws = _ws(10010)
    ws["market_suffix"] = ""
    ws["market_route"] = "krx_regular"

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock={"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER"},
        code="000660",
        strategy="SCALPING",
        ws_data=ws,
        ai_engine=ai,
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        curr_price=10010,
        best_bid=10000,
        best_ask=10020,
        requested_qty=1,
        real_order_subject=True,
    )

    assert ai.calls == 0
    assert adjusted == []
    assert touched is True
    assert latency_gate["ai_entry_price_canary_submit_blocked"] is True
    assert (
        latency_gate["ai_entry_price_canary_submit_block_reason"]
        == "entry_candle_source_quality_blocked"
    )
    assert latency_gate["ai_entry_price_provider_skipped"] is True
    assert latency_gate["ai_entry_price_provider_call_count"] == 0
    assert latency_gate["ai_entry_price_canary_eval_ms"] == 0
    assert latency_gate["entry_candle_source_quality_blockers"] == ["venue_conflict"]
    assert logs[-1][0] == "entry_ai_price_candle_source_block"
    assert logs[-1][1]["actual_order_submitted"] is False
    assert logs[-1][1]["broker_order_forbidden"] is True


def test_entry_price_calls_provider_for_proven_nxt_aftermarket_equivalence(
    monkeypatch,
):
    _enable(monkeypatch)
    now = datetime(2026, 7, 23, 16, 20, 30, tzinfo=KST)
    monkeypatch.setattr(state_handlers.time, "time", lambda: now.timestamp())
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_minute_candles_ka10080_with_meta",
        lambda *args, **kwargs: (
            _candles(20, start_hour=16),
            {"api_id": "ka10080", "received_count": 20},
        ),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: None,
    )

    class DummyAI:
        def __init__(self):
            self.calls = 0

        def evaluate_scalping_entry_price(self, *args, **kwargs):
            self.calls += 1
            return {
                "action": "USE_DEFENSIVE",
                "confidence": 90,
                "reason": "Fresh equivalent route",
                "ai_parse_ok": True,
                "ai_parse_fail": False,
            }

    ai = DummyAI()
    latency_gate = {
        "target_buy_price": 10000,
        "latency_guarded_order_price": 10000,
        "normal_defensive_order_price": 10000,
        "order_price": 10000,
        "latency_state": "SAFE",
        "quote_stale": False,
    }
    ws = _ws(10010)
    ws.pop("market_suffix")
    ws.pop("market_route")
    ws["last_ws_market_suffix"] = "_AL"
    ws["last_ws_market_route"] = "krx_nxt_integrated"

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock={"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER"},
        code="000660",
        strategy="SCALPING",
        ws_data=ws,
        ai_engine=ai,
        latency_gate=latency_gate,
        planned_orders=[{"tag": "normal", "qty": 1, "price": 10000}],
        curr_price=10010,
        best_bid=10000,
        best_ask=10020,
        requested_qty=1,
        real_order_subject=True,
    )

    assert ai.calls == 1
    assert adjusted
    assert touched is True
    assert latency_gate.get("ai_entry_price_canary_submit_blocked") is not True
