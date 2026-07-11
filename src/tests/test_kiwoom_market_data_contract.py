from __future__ import annotations

import pandas as pd

from src.engine import sniper_strength_shadow_feedback
from src.utils import kiwoom_utils


def _clear_market_data_cache():
    with kiwoom_utils._MARKET_DATA_CACHE_LOCK:
        kiwoom_utils._MARKET_DATA_CACHE.clear()


def test_ka10080_continuous_pages_are_sorted_oldest_to_latest(monkeypatch):
    _clear_market_data_cache()
    monkeypatch.setattr(kiwoom_utils, "get_effective_kiwoom_code", lambda code: code)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        assert kwargs["api_id"] == "ka10080"
        assert kwargs["use_continuous"] is True
        assert kwargs["return_meta"] is True
        return (
            [
                {
                    "stk_min_pole_chart_qry": [
                        {"cntr_tm": "20260703090300", "open_pric": "103", "high_pric": "104", "low_pric": "102", "cur_prc": "103", "trde_qty": "30"},
                        {"cntr_tm": "20260703090100", "open_pric": "101", "high_pric": "102", "low_pric": "100", "cur_prc": "101", "trde_qty": "10"},
                    ]
                },
                {
                    "stk_min_pole_chart_qry": [
                        {"cntr_tm": "20260703090200", "open_pric": "102", "high_pric": "103", "low_pric": "101", "cur_prc": "102", "trde_qty": "20"},
                    ]
                },
            ],
            {
                "api_id": "ka10080",
                "cont_yn_seen": True,
                "next_key_seen": True,
                "page_count": 2,
                "continuous_page_limit_reached": False,
            },
        )

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    candles, meta = kiwoom_utils.get_minute_candles_ka10080_with_meta("token", "005930", limit=3)

    assert [row["체결시간"] for row in candles] == ["09:01:00", "09:02:00", "09:03:00"]
    assert [row["현재가"] for row in candles] == [101, 102, 103]
    assert [row["source_timestamp"] for row in candles] == [
        "20260703090100",
        "20260703090200",
        "20260703090300",
    ]
    assert {row["source_time_basis"] for row in candles} == {"ka10080_cntr_tm_bar_timestamp"}
    assert meta["requested_limit"] == 3
    assert meta["received_count"] == 3
    assert meta["sort_direction_detected"] == "mixed"
    assert meta["cont_yn_seen"] is True
    assert meta["next_key_seen"] is True
    assert meta["truncated_window"] is False
    assert meta["latest_source_timestamp"] == "20260703090300"
    assert meta["source_time_basis"] == "response_received_epoch_ms_and_chart_bar_timestamp"
    assert "rest_received_ts_ms" in meta
    assert calls[0]["max_pages"] >= 2


def test_ka10080_preserves_explicit_nxt_market_suffix(monkeypatch):
    _clear_market_data_cache()
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        return (
            [{"stk_min_pole_chart_qry": [{"cntr_tm": "20260703090100", "cur_prc": "101"}]}],
            {"api_id": "ka10080"},
        )

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    candles, meta = kiwoom_utils.get_minute_candles_ka10080_with_meta("token", "A005930_NX", limit=1)

    assert calls[0]["url"] == "https://example.test/api/dostk/chart"
    assert calls[0]["api_id"] == "ka10080"
    assert calls[0]["payload"]["stk_cd"] == "005930_NX"
    assert candles[0]["현재가"] == 101
    assert meta["api_id"] == "ka10080"


def test_ka10081_dataframe_keeps_source_meta_and_sorts_index(monkeypatch):
    _clear_market_data_cache()
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    def fake_fetch(**kwargs):
        assert kwargs["api_id"] == "ka10081"
        assert kwargs["use_continuous"] is True
        assert kwargs["return_meta"] is True
        return (
            [
                {
                    "stk_dt_pole_chart_qry": [
                        {"dt": "20260703", "open_pric": "103", "high_pric": "104", "low_pric": "102", "cur_prc": "103", "trde_qty": "30"},
                        {"dt": "20260701", "open_pric": "101", "high_pric": "102", "low_pric": "100", "cur_prc": "101", "trde_qty": "10"},
                    ]
                },
                {
                    "stk_dt_pole_chart_qry": [
                        {"dt": "20260702", "open_pric": "102", "high_pric": "103", "low_pric": "101", "cur_prc": "102", "trde_qty": "20"},
                    ]
                },
            ],
            {
                "api_id": "ka10081",
                "cont_yn_seen": True,
                "next_key_seen": True,
                "page_count": 2,
                "continuous_page_limit_reached": False,
            },
        )

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    df = kiwoom_utils.get_daily_ohlcv_ka10081_df("token", "005930", end_date="20260703")

    assert [idx.strftime("%Y%m%d") for idx in df.index] == ["20260701", "20260702", "20260703"]
    assert df["Close"].tolist() == [101, 102, 103]
    meta = df.attrs["kiwoom_source_meta"]
    assert meta["received_count"] == 3
    assert meta["sort_direction_detected"] == "mixed"
    assert meta["cont_yn_seen"] is True
    assert meta["latest_source_timestamp"] == "20260703"
    assert meta["source_time_basis"] == "response_received_epoch_ms_and_chart_bar_timestamp"
    assert "rest_received_ts_ms" in meta


def test_signed_rate_parsers_and_rank_change_sign_contract(monkeypatch):
    _clear_market_data_cache()
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    assert kiwoom_utils._scanner_to_signed_float("-0.07") == -0.07
    assert kiwoom_utils._scanner_to_signed_float("+38.04") == 38.04
    assert kiwoom_utils._scanner_to_int("-12,300") == 12300
    assert kiwoom_utils._pred_pre_signal_direction("2") == "positive"
    assert kiwoom_utils._pred_pre_signal_direction("3") == "neutral"
    assert kiwoom_utils._pred_pre_signal_direction("5") == "negative"

    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "realtime_item_rank": [
                    {
                        "stk_cd": "005930",
                        "stk_nm": "삼성전자",
                        "past_curr_prc": "+12300",
                        "base_comp_chgr": "-0.07",
                        "prev_base_chgr": "+0.03",
                        "bigd_rank": "1",
                        "rank_chg": "2",
                        "rank_chg_sign": "X",
                    },
                    {
                        "stk_cd": "000660",
                        "stk_nm": "SK하이닉스",
                        "past_curr_prc": "+123000",
                        "base_comp_chgr": "+1.25",
                        "prev_base_chgr": "-0.10",
                        "bigd_rank": "2",
                        "rank_chg": "3",
                        "rank_chg_sign": "+",
                    },
                    {
                        "stk_cd": "006340",
                        "stk_nm": "대원전선",
                        "past_curr_prc": "+3500",
                        "base_comp_chgr": "+0.00",
                        "prev_base_chgr": "+0.00",
                        "bigd_rank": "3",
                        "rank_chg": "-2",
                        "rank_chg_sign": "-",
                    },
                    {
                        "stk_cd": "035420",
                        "stk_nm": "NAVER",
                        "past_curr_prc": "+210000",
                        "base_comp_chgr": "+0.00",
                        "prev_base_chgr": "+0.00",
                        "bigd_rank": "4",
                        "rank_chg": "0",
                        "rank_chg_sign": "",
                    },
                    {
                        "stk_cd": "035720",
                        "stk_nm": "카카오",
                        "past_curr_prc": "+58000",
                        "base_comp_chgr": "+0.00",
                        "prev_base_chgr": "+0.00",
                        "bigd_rank": "5",
                        "rank_chg": "0",
                        "rank_chg_sign": "N",
                    }
                ]
            }
        ],
    )

    rows = kiwoom_utils.get_realtime_item_rank_ka00198("token", limit=5)

    assert rows[0]["FluRate"] == -0.07
    assert rows[0]["RealtimePrevBaseChange"] == 0.03
    assert rows[0]["RankChangeSign"] == "X"
    assert rows[0]["RankChangeSignAuthority"] == "raw_unverified_not_decision_input"
    assert rows[0]["RankChangeSignState"] == "unknown"
    assert rows[0]["RankChangeSignConsistency"] == "unknown"
    assert rows[1]["RankChangeSignState"] == "positive"
    assert rows[1]["RankChangeSignConsistency"] == "consistent"
    assert rows[2]["RankChangeSignState"] == "negative"
    assert rows[2]["RankChangeSignConsistency"] == "consistent"
    assert rows[3]["RankChangeSignState"] == "neutral_empty"
    assert rows[3]["RankChangeSignConsistency"] == "neutral_zero"
    assert rows[4]["RankChangeSignState"] == "neutral_N"
    assert rows[4]["RankChangeSignConsistency"] == "neutral_zero"


def test_legacy_realtime_hot_stocks_preserves_signed_rank_delta(monkeypatch):
    _clear_market_data_cache()
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "item_inq_rank": [
                    {
                        "stk_cd": "006340",
                        "stk_nm": "대원전선",
                        "bigd_rank": "5",
                        "rank_chg": "-3",
                        "rank_chg_sign": "-",
                        "past_curr_prc": "+3500",
                        "base_comp_chgr": "-1.25",
                        "prev_base_chgr": "+0.10",
                    }
                ]
            }
        ],
    )

    rows = kiwoom_utils.get_realtime_hot_stocks_ka00198("token")

    assert rows[0]["rank_chg"] == -3
    assert rows[0]["rank_chg_authority"] == "signed_numeric_rank_delta_from_api"
    assert rows[0]["rank_sign"] == "-"
    assert rows[0]["rank_sign_authority"] == "raw_unverified_not_decision_input"
    assert rows[0]["flu_rate"] == -1.25
    assert rows[0]["prev_flu"] == 0.10


def test_ka10046_strength_trend_is_rest_source_only_with_received_timestamp(monkeypatch):
    _clear_market_data_cache()
    monkeypatch.setattr(kiwoom_utils, "get_effective_kiwoom_code", lambda code: code)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")
    monkeypatch.setattr(kiwoom_utils.time, "sleep", lambda *_args, **_kwargs: None)

    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return [
            {
                "cntr_str_tm": [
                    {
                        "cntr_str": "121.5",
                        "cntr_str_5min": "118.2",
                        "cntr_str_20min": "112.4",
                        "cntr_str_60min": "104.0",
                        "acc_trde_prica": "12,345,000",
                        "trde_qty": "1234",
                        "flu_rt": "+1.25",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    row = kiwoom_utils.check_execution_strength_ka10046("token", "005930")

    assert captured["url"] == "https://example.test/api/dostk/mrkcond"
    assert captured["api_id"] == "ka10046"
    assert captured["payload"] == {"stk_cd": "005930"}
    assert captured["use_continuous"] is False
    assert row["strength"] == 121.5
    assert row["acc_amt"] == 12345000
    assert row["source"] == "ka10046_rest_strength_trend"
    assert row["decision_authority"] == "strength_trend_rest_fallback_source_only"
    assert row["runtime_effect"] is False
    assert row["allowed_runtime_apply"] is False
    assert row["source_time_basis"] == "response_received_epoch_ms"
    assert row["rest_received_ts_ms"] > 0
    assert "standalone_buy_support" in row["forbidden_uses"]


def test_realtime_analysis_context_uses_first_ask_level_as_best_ask(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "check_execution_strength_ka10046",
        lambda *_args, **_kwargs: {"strength": 120, "s5": 118, "s20": 116, "s60": 114, "acc_amt": 0, "trde_qty": 0, "flu_rt": 0},
    )
    monkeypatch.setattr(kiwoom_utils, "get_program_flow_realtime", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(kiwoom_utils, "get_investor_flow_summary_ka10059", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        kiwoom_utils,
        "summarize_ticks_for_realtime_ka10003",
        lambda *_args, **_kwargs: {"buy_ratio_now": 50.0, "buy_ratio_1m": 50.0, "buy_ratio_3m": 50.0, "tape_bias": "중립"},
    )
    monkeypatch.setattr(kiwoom_utils, "get_minute_candles_ka10080", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_daily_ohlcv_ka10081_df", lambda *_args, **_kwargs: pd.DataFrame())

    ctx = kiwoom_utils.build_realtime_analysis_context(
        "token",
        "005930",
        {
            "curr": 10000,
            "orderbook": {
                "asks": [{"price": 10010, "volume": 100}, {"price": 10050, "volume": 300}],
                "bids": [{"price": 9990, "volume": 200}],
            },
        },
    )

    assert ctx["best_ask"] == 10010
    assert ctx["best_bid"] == 9990


def test_realtime_analysis_context_marks_ka10046_fallback_without_price_leak(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "check_execution_strength_ka10046",
        lambda *_args, **_kwargs: {
            "source": "ka10046_rest_strength_trend",
            "strength": 120,
            "s5": 118,
            "s20": 116,
            "s60": 114,
            "acc_amt": 987654321,
            "trde_qty": 3000,
            "flu_rt": 1.2,
            "runtime_effect": False,
            "decision_authority": "strength_trend_rest_fallback_source_only",
            "rest_received_ts_ms": 1780000000000,
        },
    )
    monkeypatch.setattr(kiwoom_utils, "get_program_flow_realtime", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(kiwoom_utils, "get_investor_flow_summary_ka10059", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        kiwoom_utils,
        "summarize_ticks_for_realtime_ka10003",
        lambda *_args, **_kwargs: {"buy_ratio_now": 50.0, "buy_ratio_1m": 50.0, "buy_ratio_3m": 50.0, "tape_bias": "중립"},
    )
    monkeypatch.setattr(kiwoom_utils, "get_minute_candles_ka10080", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_daily_ohlcv_ka10081_df", lambda *_args, **_kwargs: pd.DataFrame())

    ctx = kiwoom_utils.build_realtime_analysis_context("token", "005930", {"volume": 0})

    assert ctx["curr_price"] == 0
    assert ctx["today_turnover"] == 987654321
    assert ctx["today_vol"] == 3000
    assert ctx["v_pw_now"] == 120
    assert ctx["v_pw_source"] == "ka10046_rest_fallback"
    assert ctx["v_pw_runtime_support_usable"] is False
    assert ctx["v_pw_ws_value"] == 0.0
    assert ctx["v_pw_rest_value"] == 120
    assert ctx["timing_score"] == 50.0
    assert ctx["ka10046_strength_source"] == "ka10046_rest_strength_trend"
    assert ctx["ka10046_strength_decision_authority"] == "strength_trend_rest_fallback_source_only"
    assert ctx["ka10046_strength_runtime_effect"] is False
    assert ctx["ka10046_strength_rest_received_ts_ms"] == 1780000000000


def test_realtime_analysis_context_prefers_ws_strength_source(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "check_execution_strength_ka10046",
        lambda *_args, **_kwargs: {"strength": 120, "s5": 118, "s20": 116, "s60": 114, "acc_amt": 0, "trde_qty": 0, "flu_rt": 0},
    )
    monkeypatch.setattr(kiwoom_utils, "get_program_flow_realtime", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(kiwoom_utils, "get_investor_flow_summary_ka10059", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        kiwoom_utils,
        "summarize_ticks_for_realtime_ka10003",
        lambda *_args, **_kwargs: {"buy_ratio_now": 50.0, "buy_ratio_1m": 50.0, "buy_ratio_3m": 50.0, "tape_bias": "중립"},
    )
    monkeypatch.setattr(kiwoom_utils, "get_minute_candles_ka10080", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_daily_ohlcv_ka10081_df", lambda *_args, **_kwargs: pd.DataFrame())

    ctx = kiwoom_utils.build_realtime_analysis_context("token", "005930", {"curr": 10000, "v_pw": 131.0})

    assert ctx["v_pw_now"] == 131.0
    assert ctx["v_pw_source"] == "ws_0b"
    assert ctx["v_pw_runtime_support_usable"] is True
    assert ctx["v_pw_ws_value"] == 131.0
    assert ctx["v_pw_rest_value"] == 120
    assert ctx["timing_score"] == 81.0


def test_strength_shadow_feedback_uses_first_ask_level_as_best_ask(monkeypatch):
    sniper_strength_shadow_feedback._RECORDED_KEYS.clear()
    recorded = []
    monkeypatch.setattr(sniper_strength_shadow_feedback, "_append_jsonl", lambda _path, payload: recorded.append(payload))

    payload = sniper_strength_shadow_feedback.record_shadow_candidate(
        {"name": "삼성전자", "strategy": "SCALPING"},
        "005930",
        {
            "curr": 10000,
            "orderbook": {
                "asks": [{"price": 10010, "volume": 100}, {"price": 10050, "volume": 300}],
                "bids": [{"price": 9990, "volume": 200}],
            },
        },
        {"allowed": True, "reason": "test"},
    )

    assert payload is not None
    assert payload["best_ask"] == 10010
    assert payload["best_bid"] == 9990
    assert recorded and recorded[0]["best_ask"] == 10010
