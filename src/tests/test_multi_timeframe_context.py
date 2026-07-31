from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine.scalping.multi_timeframe_context import (
    INPUT_CONTRACT,
    build_multi_timeframe_context,
    multi_timeframe_ai_input_enabled,
)

KST = ZoneInfo("Asia/Seoul")


def test_post_cutover_env_alone_cannot_bypass_promotion_artifact(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE", "2026-07-27"
    )

    assert not multi_timeframe_ai_input_enabled(
        datetime(2026, 7, 27, 8, 30, tzinfo=KST)
    )
    assert not multi_timeframe_ai_input_enabled(datetime(2026, 7, 28, 9, 0, tzinfo=KST))


def _rows(*, base: int, step: int, count: int = 20) -> list[dict]:
    start = datetime(2026, 7, 27, 9, 0, tzinfo=KST)
    output = []
    for index in range(count):
        moment = start + timedelta(minutes=index)
        close = base + step * index
        output.append(
            {
                "source_timestamp": moment.strftime("%Y%m%d%H%M%S"),
                "시가": close - 2,
                "고가": close + 4,
                "저가": close - 4,
                "현재가": close,
                "거래량": 100 + index,
                "effective_venue": "KRX",
            }
        )
    return output


def test_shared_bundle_contains_completed_multi_timeframe_and_macro_context():
    stock_rows = _rows(base=10_000, step=10)
    market_rows = _rows(base=300_000, step=20)
    sector_rows = _rows(base=120_000, step=5)
    captured_at = datetime(2026, 7, 27, 9, 20, 30, tzinfo=KST)

    bundle = build_multi_timeframe_context(
        stock_rows,
        token=None,
        symbol="005930",
        venue="KRX",
        session="krx_regular",
        ws_data={
            "previous_day_levels": {
                "date": "2026-07-24",
                "high": 10100,
                "low": 9900,
                "close": 10000,
                "source_quality": "pass",
            },
            "market_context": {
                "source": "fixture_ka20005",
                "minute_rows": market_rows,
            },
            "sector_context": {
                "source": "fixture_ka20005",
                "minute_rows": sector_rows,
            },
        },
        captured_at=captured_at,
    )

    assert bundle["schema"] == "scalping_multi_timeframe_context_v1"
    assert bundle["input_contract"] == INPUT_CONTRACT
    assert bundle["input_contract"]["runtime_effect"] is False
    assert bundle["source_quality"]["status"] == "pass"
    assert bundle["session_bar_vwap"]["status"] == "pass"
    assert bundle["opening_range_5m"]["status"] == "pass"
    assert bundle["opening_range_15m"]["status"] == "pass"
    assert len(bundle["multi_timeframe_bars"]["3m"]) == 6
    assert len(bundle["multi_timeframe_bars"]["5m"]) == 4
    assert len(bundle["multi_timeframe_bars"]["15m"]) == 1
    assert bundle["incomplete_multi_timeframe_bars"]["15m"][-1]["source_quality"] == (
        "source_quality_blocked"
    )
    assert bundle["previous_day_levels"]["close"] == 10000
    assert bundle["market_context"]["return_15m_pct"] is not None
    assert bundle["sector_context"]["sector_relative_return_15m_pct"] is not None
    assert len(bundle["payload_hash"]) == 64


def test_shared_bundle_treats_ka10080_sparse_minutes_as_no_trade_without_fill():
    rows = _rows(base=10_000, step=10)
    del rows[7]

    bundle = build_multi_timeframe_context(
        rows,
        token=None,
        symbol="005930",
        venue="KRX",
        session="krx_regular",
        ws_data={},
        captured_at=datetime(2026, 7, 27, 9, 20, 30, tzinfo=KST),
        minute_bar_source_api_id="ka10080",
    )

    assert bundle["source_quality"]["status"] == "pass"
    assert "missing_completed_minutes" not in bundle["source_quality"]["blockers"]
    assert bundle["source_quality"]["observed_no_trade_minutes"] == ["09:07"]
    assert bundle["source_quality"]["missing_source_minute_count"] == 0
    assert bundle["multi_timeframe_bars"]["3m"]
    assert bundle["multi_timeframe_bars"]["5m"]
    assert bundle["multi_timeframe_bars"]["15m"]
    assert bundle["session_bar_vwap"]["value"] is not None
    assert bundle["session_bar_vwap"]["zero_trade_minutes_synthetic_fill"] is False


def test_shared_bundle_keeps_unknown_sparse_source_fail_closed():
    rows = _rows(base=10_000, step=10)
    del rows[7]

    bundle = build_multi_timeframe_context(
        rows,
        token=None,
        symbol="005930",
        venue="KRX",
        session="krx_regular",
        ws_data={},
        captured_at=datetime(2026, 7, 27, 9, 20, 30, tzinfo=KST),
    )

    assert bundle["source_quality"]["status"] == "source_quality_blocked"
    assert "missing_completed_minutes" in bundle["source_quality"]["blockers"]


def test_shared_bundle_rejects_invalid_ohlc_instead_of_zero_filling():
    rows = _rows(base=10_000, step=10)
    rows[4]["고가"] = 0

    bundle = build_multi_timeframe_context(
        rows,
        token=None,
        symbol="005930",
        venue="KRX",
        session="krx_regular",
        ws_data={
            "previous_day_levels": {
                "high": float("nan"),
                "low": 9900,
                "close": 10000,
            }
        },
        captured_at=datetime(2026, 7, 27, 9, 20, 30, tzinfo=KST),
    )

    assert bundle["source_quality"]["status"] == "source_quality_blocked"
    assert "invalid_minute_rows" in bundle["source_quality"]["blockers"]
    assert bundle["previous_day_levels"]["high"] is None
