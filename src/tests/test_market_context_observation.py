from src.engine.scalping.market_context_observation import (
    build_market_context_observation,
    normalize_completed_bars,
)


def _bar(minute, o, h, l, c, v, **extra):
    return {
        "source_timestamp": f"20260727{minute.replace(':', '')}00",
        "시가": o,
        "고가": h,
        "저가": l,
        "현재가": c,
        "거래량": v,
        **extra,
    }


def test_observation_resamples_completed_bars_and_excludes_forming_bar():
    rows = [
        _bar(
            f"09:{minute:02d}",
            100 + minute,
            102 + minute,
            99 + minute,
            101 + minute,
            10,
        )
        for minute in range(15)
    ]
    rows.append(_bar("09:15", 200, 201, 199, 200, 999, forming=True))

    report = build_market_context_observation(
        rows,
        symbol="005930",
        venue="KRX",
        session="regular",
        target_date="2026-07-27",
    )

    assert report["runtime_effect"] is False
    assert report["source_quality"]["status"] == "pass"
    assert len(report["bars_1m_completed"]) == 15
    assert len(report["forming_bars"]) == 1
    assert len(report["multi_timeframe_bars"]["3m"]) == 5
    assert len(report["multi_timeframe_bars"]["5m"]) == 3
    assert report["multi_timeframe_bars"]["15m"][0] == {
        "interval_min": 15,
        "start": "2026-07-27T09:00:00+09:00",
        "end": "2026-07-27T09:15:00+09:00",
        "o": 100,
        "h": 116,
        "l": 99,
        "c": 115,
        "v": 150,
        "source_bar_count": 15,
        "expected_bar_count": 15,
        "source_quality": "pass",
        "missing_minutes": [],
        "observed_no_trade_minutes": [],
        "minute_gap_interpretation": "strict_expected_minute",
    }
    assert report["session_bar_vwap"]["completed_volume"] == 150
    assert report["opening_range_5m"]["high"] == 106
    assert report["opening_range_15m"]["low"] == 99


def test_missing_and_conflicting_duplicate_block_all_derived_values():
    rows = [
        _bar("09:00", 100, 101, 99, 100, 10),
        _bar("09:00", 100, 102, 99, 101, 11),
        _bar("09:02", 101, 102, 100, 101, 10),
    ]

    report = build_market_context_observation(
        rows,
        symbol="005930",
        venue="KRX",
        session="regular",
        target_date="2026-07-27",
    )

    assert report["source_quality"]["status"] == "source_quality_blocked"
    assert report["source_quality"]["blockers"] == [
        "duplicate_price_or_volume_conflict",
        "missing_completed_minutes",
    ]
    assert report["multi_timeframe_bars"] == {"3m": [], "5m": [], "15m": []}
    assert report["session_bar_vwap"]["value"] is None


def test_krx_closing_call_auction_gap_is_scheduled_not_missing():
    completed, _, quality = normalize_completed_bars(
        [
            _bar("15:18", 100, 101, 99, 100, 10),
            _bar("15:19", 100, 101, 99, 100, 10),
            _bar("15:30", 101, 102, 100, 101, 50),
        ],
        target_date="2026-07-27",
        venue="KRX",
        session="regular",
    )

    assert len(completed) == 3
    assert quality["status"] == "pass"
    assert quality["scheduled_call_auction_gap_count"] == 1
    assert quality["missing_minutes"] == []


def test_current_forming_bar_and_market_route_conflict_are_detected():
    report = build_market_context_observation(
        [
            _bar("09:18", 100, 101, 99, 100, 10),
            _bar("09:19", 100, 101, 99, 100, 10),
            _bar(
                "09:20",
                100,
                101,
                99,
                100,
                100,
                effective_venue="NXT",
            ),
        ],
        symbol="005930",
        venue="KRX",
        session="regular",
        target_date="2026-07-27",
        captured_at="2026-07-27T09:20:20+09:00",
    )

    assert len(report["forming_bars"]) == 1
    assert report["forming_bars"][0]["t"] == "09:20"
    assert report["source_quality"]["market_route_conflict_count"] == 1
    assert report["source_quality"]["status"] == "source_quality_blocked"
    assert report["session_bar_vwap"]["value"] is None


def test_market_and_sector_five_fifteen_minute_context_and_relative_return():
    rows = [
        _bar(
            f"09:{minute:02d}",
            100,
            101 + minute,
            99,
            100 + minute,
            10,
        )
        for minute in range(15)
    ]
    sector_rows = [
        _bar(
            f"09:{minute:02d}",
            100,
            101 + minute // 2,
            99,
            100 + minute // 2,
            10,
        )
        for minute in range(15)
    ]

    report = build_market_context_observation(
        rows,
        symbol="005930",
        venue="KRX",
        session="regular",
        target_date="2026-07-27",
        market_context={"index": "KOSPI", "minute_rows": rows},
        sector_context={"sector": "electrical", "minute_rows": sector_rows},
    )

    assert report["market_context"]["direction_5m"] == "up"
    assert report["market_context"]["direction_15m"] == "up"
    assert report["sector_context"]["stock_return_15m_pct"] == 14.0
    assert report["sector_context"]["sector_relative_return_15m_pct"] == 7.0


def test_other_dates_and_sessions_are_excluded_before_gap_validation():
    rows = [
        {
            **_bar("15:30", 100, 101, 99, 100, 10),
            "source_timestamp": "20260724153000",
        },
        _bar("08:59", 100, 101, 99, 100, 10),
        _bar("09:00", 100, 101, 99, 100, 10),
        _bar("09:01", 100, 101, 99, 100, 10),
    ]

    completed, _, quality = normalize_completed_bars(
        rows,
        target_date="2026-07-27",
        venue="KRX",
        session="regular",
    )

    assert [row["t"] for row in completed] == ["09:00", "09:01"]
    assert quality["excluded_other_date_count"] == 1
    assert quality["excluded_other_session_count"] == 1
    assert quality["status"] == "pass"
