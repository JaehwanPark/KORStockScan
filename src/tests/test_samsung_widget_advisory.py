from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from src.engine.monitoring import samsung_widget_advisory as advisory
from src.engine.monitoring import samsung_widget_contract as contract

KST = ZoneInfo("Asia/Seoul")


def test_kiwoom_signed_price_is_normalized_to_absolute_price():
    assert advisory._positive_int("-262500") == 262_500
    assert advisory._positive_int("+262500") == 262_500


def _bars(start: datetime, closes: list[int]) -> list[advisory.MinuteBar]:
    result = []
    for index, close in enumerate(closes):
        source_time = (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S")
        open_price = close - 100 if index % 2 == 0 else close + 50
        result.append(
            advisory.MinuteBar(
                source_time=source_time,
                open=open_price,
                high=max(open_price, close) + 50,
                low=min(open_price, close) - 50,
                close=close,
                volume=1_500 if close > open_price else 1_000,
            )
        )
    return result


def _external(change_by_key=None, quality="BEST_EFFORT_DELAYED"):
    change_by_key = change_by_key or {}
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST).isoformat()
    return {
        key: advisory.ExternalPoint(
            key=key,
            ticker=ticker,
            value=100.0,
            change_15m_pct=change_by_key.get(key, 0.0),
            observed_at=now,
            received_at=now,
            age_sec=30,
            provider="yahoo_best_effort",
            quality=quality,
            market_state="OPEN",
        )
        for key, ticker in advisory.YahooExternalMarketProvider.TICKERS.items()
    }


def _ready_input(current_price=100_400, bbo_age=0.0):
    now = datetime(2026, 8, 3, 9, 10, 5, tzinfo=KST)
    bars = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [
            100_000,
            99_900,
            100_100,
            100_000,
            100_200,
            100_100,
            100_300,
            100_200,
            100_400,
            current_price,
        ],
    )
    return {
        "observed_at": now,
        "context": advisory.session_context(now),
        "current_price": current_price,
        "bars": bars,
        "bbo": {
            "best_bid": current_price - 100,
            "best_ask": current_price,
            "age_sec": bbo_age,
        },
        "previous_day": {
            "date": "20260731",
            "open": 99_000,
            "high": 102_000,
            "low": 98_000,
            "close": 100_000,
        },
        "relative": {
            "samsung_change_pct": 1.0,
            "sk_hynix_change_pct": 0.8,
            "kospi_change_pct": 0.5,
        },
        "external_points": _external(),
        "flow": {
            "status": "OBSERVED",
            "live_for_current_session": True,
            "foreign_nonworsening": True,
            "program_nonworsening": True,
        },
    }


def test_trend_band_treats_single_high_price_tick_as_flat():
    bars = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [262_000, 262_000, 262_000, 262_000, 262_500],
    )

    details = advisory.analyze_trends(bars, session_name="KRX_REGULAR")

    assert details["1m"]["tick_size"] == 500
    assert details["1m"]["flat_band_price"] >= 500
    assert details["1m"]["state"] == "flat"


def test_trend_analysis_requires_fit_and_consistency_for_up_state():
    monotonic = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [100_000, 100_100, 100_200, 100_300, 100_400, 100_500],
    )
    noisy = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [100_000, 100_700, 99_900, 100_800, 100_000, 100_900],
    )

    monotonic_details = advisory.analyze_trends(monotonic, session_name="KRX_REGULAR")
    noisy_details = advisory.analyze_trends(noisy, session_name="KRX_REGULAR")

    assert monotonic_details["5m"]["state"] == "up"
    assert monotonic_details["5m"]["regression_r2"] >= 0.4
    assert noisy_details["5m"]["state"] == "flat"


def test_nxt_trend_band_is_more_conservative_than_regular_session():
    bars = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [100_000, 100_100, 100_200, 100_300],
    )

    regular = advisory.analyze_trends(bars, session_name="KRX_REGULAR")
    premarket = advisory.analyze_trends(bars, session_name="NXT_PREMARKET")

    assert regular["3m"]["state"] == "up"
    assert premarket["3m"]["state"] == "flat"
    assert premarket["3m"]["flat_band_price"] > regular["3m"]["flat_band_price"]


def test_trend_assessment_keeps_setup_state_distinct_and_prioritizes_downside():
    stable = advisory._trend_assessment({"3m": "flat", "5m": "flat"})
    partial_down = advisory._trend_assessment({"3m": "down", "5m": "unavailable"})

    assert stable["state"] == "TREND_STABLE"
    assert stable["setup_ready_is_distinct"] is True
    assert stable["future_prediction"] is False
    assert partial_down["state"] == "TREND_DOWN"


def test_session_vwap_uses_hlc3_volume_weighting_and_hlc3_fallback():
    bars = [
        advisory.MinuteBar("20260803090000", 100, 130, 90, 110, 1),
        advisory.MinuteBar("20260803090100", 120, 160, 100, 130, 3),
    ]
    zero_volume = [
        advisory.MinuteBar(bar.source_time, bar.open, bar.high, bar.low, bar.close, 0)
        for bar in bars
    ]

    assert advisory._session_vwap(bars) == 125
    assert advisory._session_vwap(zero_volume) == 120


def test_structure_does_not_promote_single_unconfirmed_pivot_to_support():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    lows = [100_000, 99_000, 100_000, 101_000, 102_000, 103_000]
    highs = [105_000, 106_000, 107_000, 106_000, 106_500, 106_800]
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            low + 500,
            high,
            low,
            low + 1_000,
            1_000,
        )
        for index, (low, high) in enumerate(zip(lows, highs))
    ]

    structure = advisory._structure_features(bars)

    assert structure["candidate_support"] == 99_000
    assert structure["confirmed_support"] is None
    assert structure["support_confirmation"] == "unconfirmed"


def test_structure_does_not_confirm_failed_lower_retest():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    lows = [100_000, 99_000, 100_000, 97_000, 99_000, 100_000]
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            low + 500,
            105_000,
            low,
            low + 1_000,
            1_000,
        )
        for index, low in enumerate(lows)
    ]

    structure = advisory._structure_features(bars)

    assert structure["candidate_support"] == 97_000
    assert structure["retest_held"] is False
    assert structure["confirmed_support"] is None


def test_structure_rejects_adjacent_flat_low_as_retest():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    lows = [101_000, 100_000, 100_000, 101_000, 101_000]
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            low + 500,
            102_000,
            low,
            low + 500,
            1_000,
        )
        for index, low in enumerate(lows)
    ]

    structure = advisory._structure_features(bars)

    assert structure["retest_rebound_confirmed"] is False
    assert structure["retest_held"] is False
    assert structure["confirmed_support"] is None


def test_session_context_separates_nxt_krx_and_transition_windows():
    assert (
        advisory.session_context(datetime(2026, 8, 3, 8, 10, tzinfo=KST)).name
        == "NXT_PREMARKET"
    )
    assert (
        advisory.session_context(datetime(2026, 8, 3, 8, 55, tzinfo=KST)).name
        == "SESSION_TRANSITION"
    )
    assert (
        advisory.session_context(datetime(2026, 8, 3, 9, 3, tzinfo=KST)).name
        == "KRX_REGULAR"
    )
    assert (
        advisory.session_context(datetime(2026, 8, 3, 15, 35, tzinfo=KST)).name
        == "SESSION_TRANSITION"
    )
    assert (
        advisory.session_context(datetime(2026, 8, 3, 15, 45, tzinfo=KST)).name
        == "NXT_AFTERMARKET"
    )
    assert (
        advisory.session_context(datetime(2026, 8, 2, 9, 10, tzinfo=KST)).name
        == "CLOSED"
    )
    assert (
        advisory.session_context(datetime(2026, 5, 1, 9, 10, tzinfo=KST)).name
        == "CLOSED"
    )


def test_completed_bars_exclude_forming_and_cross_session_rows():
    rows = [
        {
            "cntr_tm": "20260803085900",
            "open_pric": "99,000",
            "high_pric": "99,100",
            "low_pric": "98,900",
            "cur_prc": "99,050",
            "trde_qty": "100",
        },
        {
            "cntr_tm": "20260803090000",
            "open_pric": "100,000",
            "high_pric": "100,200",
            "low_pric": "99,900",
            "cur_prc": "100,100",
            "trde_qty": "200",
        },
        {
            "cntr_tm": "20260803090100",
            "open_pric": "100,100",
            "high_pric": "100,300",
            "low_pric": "100,000",
            "cur_prc": "100,200",
            "trde_qty": "300",
        },
    ]
    bars = advisory.completed_session_bars(
        rows,
        observed_at=datetime(2026, 8, 3, 9, 1, 30, tzinfo=KST),
        session_start=advisory.KRX_START,
    )
    assert [bar.source_time for bar in bars] == ["20260803090000"]


def test_completed_bars_respect_explicit_session_end():
    rows = [
        {
            "cntr_tm": source_time,
            "open_pric": "100000",
            "high_pric": "100100",
            "low_pric": "99900",
            "cur_prc": "100000",
            "trde_qty": "100",
        }
        for source_time in ("20260803084900", "20260803090000")
    ]

    bars = advisory.completed_session_bars(
        rows,
        observed_at=datetime(2026, 8, 3, 9, 10, tzinfo=KST),
        session_start=advisory.NXT_PREMARKET_START,
        session_end=advisory.NXT_PREMARKET_END,
    )

    assert [bar.source_time for bar in bars] == ["20260803084900"]


def test_daily_anchor_rejects_cache_not_refreshed_for_current_trade_date():
    now = datetime(2026, 8, 4, 9, 10, tzinfo=KST)
    rows = [
        {
            "dt": "20260803",
            "open_pric": "100000",
            "high_pric": "101000",
            "low_pric": "99000",
            "cur_prc": "100500",
        }
    ]

    assert (
        advisory._current_daily_anchor(
            rows, observed_at=now, cache_fetch_day="20260803"
        )
        == {}
    )
    assert (
        advisory._current_daily_anchor(
            rows, observed_at=now, cache_fetch_day="20260804"
        )["date"]
        == "20260803"
    )


def test_daily_anchor_rejects_stale_non_previous_trading_day_row():
    now = datetime(2026, 8, 4, 9, 10, tzinfo=KST)
    rows = [
        {
            "dt": "20260731",
            "open_pric": "100000",
            "high_pric": "101000",
            "low_pric": "99000",
            "cur_prc": "100500",
        }
    ]

    assert advisory._parse_previous_day(rows, now) == {}


def test_domestic_ready_requires_two_consecutive_observations():
    raw = advisory.evaluate_advisory(**_ready_input())
    assert raw["raw_state"] == "ENTRY_READY"
    assert raw["entry_price_low"] == 100_300
    assert raw["entry_price_high"] == 100_300
    assert (
        raw["derived"]["confirmed_support"]
        % advisory.get_tick_size(raw["derived"]["confirmed_support"])
        == 0
    )
    assert raw["trigger_price"] % advisory.get_tick_size(raw["trigger_price"]) == 0
    assert raw["authority"] == "widget_advisory_only"
    assert raw["runtime_effect"] is False
    assert raw["derived"]["higher_high_and_low"] is True

    filter_ = advisory.AdvisoryPromotionFilter()
    first = filter_.apply(raw)
    second = filter_.apply(raw)
    assert first["state"] == "WATCH"
    assert first["entry_price_low"] is None
    assert first["entry_price_high"] is None
    assert second["state"] == "ENTRY_READY"


def test_promotion_filter_requires_temporally_consecutive_observations():
    raw = advisory.evaluate_advisory(**_ready_input())
    filter_ = advisory.AdvisoryPromotionFilter()

    first = filter_.apply(raw)
    delayed = {
        **raw,
        "observed_at": (
            datetime.fromisoformat(raw["observed_at"]) + timedelta(seconds=30)
        ).isoformat(),
    }
    second = filter_.apply(delayed)

    assert first["state"] == "WATCH"
    assert second["state"] == "WATCH"
    assert second["confirmation_streak"] == 1


def test_promotion_filter_keeps_caution_until_ready_is_confirmed():
    caution = advisory.evaluate_advisory(
        **{
            **_ready_input(),
            "external_points": _external({"NQ": -0.5}),
        }
    )
    ready = advisory.evaluate_advisory(**_ready_input())
    filter_ = advisory.AdvisoryPromotionFilter()

    assert filter_.apply(caution)["state"] == "WATCH"
    assert filter_.apply(caution)["state"] == "ENTRY_CAUTION"
    assert filter_.apply(ready)["state"] == "ENTRY_CAUTION"
    assert filter_.apply(ready)["state"] == "ENTRY_READY"


def test_promotion_filter_applies_ready_to_caution_demotion_immediately():
    ready = advisory.evaluate_advisory(**_ready_input())
    caution = advisory.evaluate_advisory(
        **{
            **_ready_input(),
            "external_points": _external({"NQ": -0.5}),
        }
    )
    filter_ = advisory.AdvisoryPromotionFilter()
    filter_.apply(ready)
    filter_.apply(ready)

    assert filter_.apply(caution)["state"] == "ENTRY_CAUTION"


def test_promotion_confirmation_does_not_cross_session_or_trading_day():
    regular = advisory.evaluate_advisory(**_ready_input())
    filter_ = advisory.AdvisoryPromotionFilter()
    assert filter_.apply(regular)["state"] == "WATCH"
    assert filter_.apply(regular)["state"] == "ENTRY_READY"

    aftermarket_time = datetime(2026, 8, 3, 15, 45, 5, tzinfo=KST)
    aftermarket = {
        **regular,
        "session": "NXT_AFTERMARKET",
        "observed_at": aftermarket_time.isoformat(),
    }
    assert filter_.apply(aftermarket)["state"] == "WATCH"
    assert filter_.apply(aftermarket)["state"] == "ENTRY_READY"

    next_day = {
        **regular,
        "observed_at": datetime(2026, 8, 4, 9, 10, 5, tzinfo=KST).isoformat(),
    }
    assert filter_.apply(next_day)["state"] == "WATCH"


def test_promotion_filter_restores_widget_only_state_across_collector_restart():
    ready = advisory.evaluate_advisory(**_ready_input())
    first_filter = advisory.AdvisoryPromotionFilter()
    first_filter.apply(ready)
    confirmed = first_filter.apply(ready)

    restored_filter = advisory.AdvisoryPromotionFilter()
    assert restored_filter.restore(confirmed) is True
    assert restored_filter.apply(ready)["state"] == "ENTRY_READY"


def test_premarket_auxiliary_can_only_downgrade_before_0930():
    inputs = _ready_input(current_price=100_400)
    before_time = datetime(2026, 8, 3, 9, 29, 55, tzinfo=KST)
    inputs["observed_at"] = before_time
    inputs["context"] = advisory.session_context(before_time)
    inputs["bars"] = _bars(
        datetime(2026, 8, 3, 9, 20, tzinfo=KST),
        [bar.close for bar in inputs["bars"]],
    )
    inputs["external_points"] = {
        key: advisory.ExternalPoint(
            **{
                **point.__dict__,
                "observed_at": before_time.isoformat(),
                "received_at": before_time.isoformat(),
            }
        )
        for key, point in inputs["external_points"].items()
    }
    inputs["premarket"] = {
        "status": "OBSERVED",
        "date": "2026-08-03",
        "vwap": 100_500,
        "market_venue": "NXT",
    }

    before_expiry = advisory.evaluate_advisory(**inputs)
    after_time = datetime(2026, 8, 3, 9, 30, 5, tzinfo=KST)
    after_expiry = advisory.evaluate_advisory(
        **{
            **inputs,
            "observed_at": after_time,
            "context": advisory.session_context(after_time),
        }
    )

    assert before_expiry["state"] == "ENTRY_CAUTION"
    assert "premarket_vwap_not_recovered" in before_expiry["unmet_conditions"]
    assert before_expiry["provenance"]["premarket_context"] == "APPLIED_AUXILIARY"
    assert after_expiry["state"] == "ENTRY_READY"
    assert after_expiry["provenance"]["premarket_context"] == "EXPIRED_0930"
    assert after_expiry["derived"]["premarket_auxiliary"] is None


def test_live_regular_flow_joint_weakness_only_downgrades_ready():
    inputs = _ready_input()
    inputs["flow"] = {
        "status": "OBSERVED",
        "live_for_current_session": True,
        "foreign_nonworsening": False,
        "program_nonworsening": False,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_CAUTION"
    assert "foreign_or_program_flow_not_improving" in result["unmet_conditions"]


def test_either_live_regular_flow_weakness_downgrades_ready():
    inputs = _ready_input()
    inputs["flow"] = {
        "status": "OBSERVED",
        "live_for_current_session": True,
        "foreign_nonworsening": True,
        "program_nonworsening": False,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_CAUTION"
    assert "foreign_or_program_flow_not_improving" in result["unmet_conditions"]


def test_regular_flow_gap_caps_otherwise_ready_signal_at_caution():
    inputs = _ready_input()
    inputs["flow"] = {
        "status": "UNAVAILABLE",
        "live_for_current_session": False,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_CAUTION"
    assert "regular_flow_unavailable" in result["unmet_conditions"]


def test_regular_flow_partial_source_is_not_labeled_fully_observed():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    flow = advisory._parse_flow(
        {
            "opmr_invsr_trde_chart": [
                {"tm": "090000", "frgnr_invsr": "-100"},
                {"tm": "091000", "frgnr_invsr": "-50"},
            ]
        },
        {},
        context=advisory.session_context(now),
        observed_at=now,
    )

    assert flow["status"] == "PARTIAL"
    assert flow["foreign_available"] is True
    assert flow["program_available"] is False


def test_regular_flow_old_source_clock_is_labeled_stale():
    now = datetime(2026, 8, 3, 9, 20, tzinfo=KST)
    flow = advisory._parse_flow(
        {
            "opmr_invsr_trde_chart": [
                {"tm": "090000", "frgnr_invsr": "-100"},
                {"tm": "091000", "frgnr_invsr": "-50"},
            ]
        },
        {
            "stk_tm_prm_trde_trnsn": [
                {
                    "tm": "091000",
                    "prm_netprps_amt": "100",
                    "prm_netprps_amt_irds": "10",
                }
            ]
        },
        context=advisory.session_context(now),
        observed_at=now,
    )

    assert flow["status"] == "STALE"
    assert flow["source_age_sec"] == 600.0


def test_regular_flow_requires_each_source_clock_to_be_fresh():
    now = datetime(2026, 8, 3, 9, 20, tzinfo=KST)
    flow = advisory._parse_flow(
        {
            "opmr_invsr_trde_chart": [
                {"tm": "090000", "frgnr_invsr": "-100"},
                {"tm": "091900", "frgnr_invsr": "-50"},
            ]
        },
        {
            "stk_tm_prm_trde_trnsn": [
                {
                    "tm": "091000",
                    "prm_netprps_amt": "100",
                    "prm_netprps_amt_irds": "10",
                }
            ]
        },
        context=advisory.session_context(now),
        observed_at=now,
    )

    assert flow["status"] == "STALE"
    assert flow["foreign_source_age_sec"] == 60.0
    assert flow["program_source_age_sec"] == 600.0


def test_regular_relative_strength_requires_both_peer_and_kospi_inputs():
    inputs = _ready_input()
    inputs["relative"] = {
        "samsung_change_pct": 1.0,
        "sk_hynix_change_pct": None,
        "kospi_change_pct": 0.5,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert "relative_strength_unavailable" in result["unmet_conditions"]


def test_nxt_relative_strength_does_not_require_closed_krx_index():
    context = advisory.session_context(datetime(2026, 8, 3, 15, 45, tzinfo=KST))

    ok, issues = advisory._relative_quality(
        {
            "samsung_change_pct": 1.0,
            "sk_hynix_change_pct": 0.8,
            "kospi_change_pct": None,
        },
        context,
    )

    assert ok is True
    assert issues == []


def test_same_window_relative_weakness_is_negative_veto_only():
    context = advisory.session_context(datetime(2026, 8, 3, 9, 20, tzinfo=KST))
    relative = {
        "samsung_change_pct": 1.0,
        "sk_hynix_change_pct": 0.8,
        "kospi_change_pct": 0.5,
        "same_window": {
            "sk_hynix": {
                "5m": {"relative_return_pct_point": -0.7},
            },
            "kospi": {
                "5m": {"relative_return_pct_point": 0.1},
            },
        },
    }

    ok, issues = advisory._relative_quality(relative, context)

    assert ok is False
    assert issues == ["relative_strength_weak"]


def test_same_window_recovery_clears_persistent_session_underperformance():
    context = advisory.session_context(datetime(2026, 8, 3, 10, 35, tzinfo=KST))
    relative = {
        "samsung_change_pct": -1.67,
        "sk_hynix_change_pct": -2.30,
        "kospi_change_pct": -0.37,
        "same_window": {
            "sk_hynix": {
                "15m": {"relative_return_pct_point": -0.0337},
                "5m": {"relative_return_pct_point": -0.3332},
            },
            "kospi": {
                "15m": {"relative_return_pct_point": 0.7438},
                "5m": {"relative_return_pct_point": 0.2841},
            },
        },
    }

    ok, issues, metadata = advisory._relative_quality_assessment(relative, context)

    assert ok is True
    assert issues == []
    assert metadata["session_underperformance"] is True
    assert metadata["same_window_recovery_confirmed"] is True
    assert metadata["session_underperformance_cleared"] is True


def test_same_window_recovery_requires_both_15m_and_5m_for_every_comparison():
    context = advisory.session_context(datetime(2026, 8, 3, 10, 35, tzinfo=KST))
    relative = {
        "samsung_change_pct": -1.67,
        "sk_hynix_change_pct": -2.30,
        "kospi_change_pct": -0.37,
        "same_window": {
            "sk_hynix": {
                "15m": {"relative_return_pct_point": 0.1},
            },
            "kospi": {
                "15m": {"relative_return_pct_point": 0.2},
                "5m": {"relative_return_pct_point": 0.1},
            },
        },
    }

    ok, issues, metadata = advisory._relative_quality_assessment(relative, context)

    assert ok is False
    assert issues == ["relative_strength_weak"]
    assert metadata["same_window_recovery_complete"] is False
    assert metadata["same_window_recovery_confirmed"] is False
    assert metadata["session_underperformance_cleared"] is False


def test_missing_same_window_relative_data_does_not_add_a_new_block():
    context = advisory.session_context(datetime(2026, 8, 3, 9, 3, tzinfo=KST))

    ok, issues = advisory._relative_quality(
        {
            "samsung_change_pct": 1.0,
            "sk_hynix_change_pct": 0.8,
            "kospi_change_pct": 0.5,
            "same_window": {},
        },
        context,
    )

    assert ok is True
    assert issues == []


def test_advisory_validity_is_short_and_capped_by_session_end():
    inputs = _ready_input()
    result = advisory.evaluate_advisory(**inputs)
    assert result["valid_until"] == "2026-08-03T09:11:05+09:00"

    inputs["observed_at"] = datetime(2026, 8, 3, 15, 29, 30, tzinfo=KST)
    inputs["context"] = advisory.session_context(inputs["observed_at"])
    result = advisory.evaluate_advisory(**inputs)
    assert result["valid_until"] == "2026-08-03T15:30:00+09:00"


def test_frozen_aftermarket_flow_is_provenance_not_live_downgrade():
    now = datetime(2026, 8, 3, 15, 45, tzinfo=KST)
    result = advisory._freeze_regular_flow(
        {
            "status": "OBSERVED",
            "foreign_nonworsening": False,
            "program_nonworsening": False,
            "observed_at": "2026-08-03T15:29:00+09:00",
            "source_session": "KRX_REGULAR",
            "live_for_current_session": True,
        },
        now,
    )

    assert result["status"] == "FROZEN_REGULAR_SESSION"
    assert result["live_for_current_session"] is False
    assert result["source_session"] == "KRX_REGULAR"
    assert result["last_live_observed_at"] == "2026-08-03T15:29:00+09:00"


def test_same_day_stale_regular_flow_can_be_recovered_as_aftermarket_frozen():
    now = datetime(2026, 8, 3, 15, 45, tzinfo=KST)
    recovered = advisory._parse_flow(
        {
            "opmr_invsr_trde_chart": [
                {"tm": "152800", "frgnr_invsr": "-100"},
                {"tm": "153000", "frgnr_invsr": "-50"},
            ]
        },
        {
            "stk_tm_prm_trde_trnsn": [
                {
                    "tm": "153000",
                    "prm_netprps_amt": "100",
                    "prm_netprps_amt_irds": "10",
                }
            ]
        },
        context=advisory.session_context(datetime(2026, 8, 3, 9, 1, tzinfo=KST)),
        observed_at=now,
    )

    assert recovered["status"] == "STALE"
    assert advisory._regular_flow_recoverable_for_aftermarket(recovered, now)


def test_previous_day_regular_flow_is_not_recovered_for_aftermarket():
    now = datetime(2026, 8, 4, 15, 45, tzinfo=KST)
    flow = {
        "foreign_available": True,
        "program_available": True,
        "source_observed_at": "2026-08-03T15:30:00+09:00",
    }

    assert not advisory._regular_flow_recoverable_for_aftermarket(flow, now)


def test_regular_flow_cache_must_match_current_trade_date():
    cached = {"observed_at": "2026-08-03T15:29:00+09:00"}

    assert advisory._observation_is_same_day(
        cached, datetime(2026, 8, 3, 15, 45, tzinfo=KST)
    )
    assert not advisory._observation_is_same_day(
        cached, datetime(2026, 8, 4, 15, 45, tzinfo=KST)
    )


def test_chasing_more_than_30bp_is_rejected():
    inputs = _ready_input(current_price=102_000)
    inputs["bbo"] = {"best_bid": 101_800, "best_ask": 101_900, "age_sec": 0}
    result = advisory.evaluate_advisory(**inputs)
    assert result["state"] == "NO_CHASE"
    assert result["entry_price_low"] is None


def test_tactical_support_owns_chase_while_structural_support_owns_invalidation(
    monkeypatch,
):
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            "higher_low": True,
            "higher_high": True,
            "higher_high_and_low": True,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "confirmed_support": 100_000,
            "candidate_support": 100_000,
            "support_confirmation": "retest_held",
            "recent_resistance": 101_000,
        },
    )
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 101_000)
    inputs = _ready_input(current_price=101_200)
    inputs["bbo"] = {"best_bid": 101_100, "best_ask": 101_200, "age_sec": 0}

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_READY"
    assert result["entry_price_low"] == 101_100
    assert result["entry_price_high"] == 101_200
    assert result["derived"]["structural_chase_pct"] > 0.3
    assert result["derived"]["tactical_chase_pct"] < 0.3
    assert result["derived"]["chase_pct"] == result["derived"]["tactical_chase_pct"]
    assert result["derived"]["chase_basis"] == "tactical_support"


def test_absorption_recovery_can_confirm_expanded_retest_volume(monkeypatch):
    monkeypatch.setattr(
        advisory,
        "_volume_confirmation",
        lambda _bars: (
            False,
            {
                "rebound_avg_volume": 61_667.8,
                "decline_avg_volume": 159_850.0,
                "first_test_volume": 63_810,
                "retest_volume": 159_850,
                "retest_volume_contracted": False,
                "rising_volume_sample_count": 5,
                "falling_volume_sample_count": 1,
                "zero_volume_count": 0,
                "zero_volume_ratio": 0.0,
                "volume_minimum_composition_met": True,
            },
        ),
    )

    result = advisory.evaluate_advisory(**_ready_input())

    assert result["state"] == "ENTRY_READY"
    assert result["derived"]["absorption_recovery_confirmed"] is True
    assert result["derived"]["volume_confirmation_mode"] == "absorption_recovery"


def test_absorption_recovery_does_not_use_forming_price_as_positive_authority():
    confirmed = advisory._absorption_recovery_confirmation(
        volume_meta={
            "retest_volume_contracted": False,
            "rising_volume_sample_count": 5,
            "falling_volume_sample_count": 1,
            "zero_volume_ratio": 0.0,
        },
        structure={"retest_held": True},
        completed_close=100_900,
        vwap=100_800,
        recent_resistance=101_000,
        reclaim_ok=True,
        trends_ok=True,
    )

    assert confirmed is False


def test_core_blocker_is_reported_before_no_chase():
    inputs = _ready_input(current_price=102_000)
    inputs["bbo"] = {"best_bid": 101_800, "best_ask": 101_900, "age_sec": 0}
    inputs["relative"] = {
        "samsung_change_pct": -2.0,
        "sk_hynix_change_pct": 0.5,
        "kospi_change_pct": 0.5,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert "relative_strength_not_weak" in result["unmet_conditions"]
    assert "price_more_than_30bp_above_support" not in result["reasons"]


def test_missing_confirmed_support_is_watch_with_candidate_provenance(monkeypatch):
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            "higher_low": False,
            "higher_high": False,
            "higher_high_and_low": False,
            "retest_held": False,
            "retest_rebound_confirmed": False,
            "confirmed_support": None,
            "candidate_support": 100_100,
            "support_confirmation": "unconfirmed",
            "recent_resistance": 100_300,
        },
    )

    result = advisory.evaluate_advisory(**_ready_input())

    assert result["state"] == "WATCH"
    assert "confirmed_support_missing" in result["unmet_conditions"]
    assert result["derived"]["candidate_support"] == 100_100
    assert result["derived"]["confirmed_support"] is None


def test_confirmed_support_break_is_immediate_avoid():
    inputs = _ready_input()
    inputs["current_price"] = 99_000
    inputs["bbo"] = {"best_bid": 98_900, "best_ask": 99_000, "age_sec": 0}

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "AVOID"
    assert result["derived"]["session_vwap"] is not None
    assert result["derived"]["support_confirmation"] != "unconfirmed"
    assert "distance_from_structural_support_pct" in result["derived"]


def test_exact_invalidation_boundary_is_immediate_avoid():
    baseline = advisory.evaluate_advisory(**_ready_input())
    invalidation = baseline["invalidation_price"]
    inputs = _ready_input()
    inputs["current_price"] = invalidation
    inputs["bbo"] = {
        "best_bid": advisory.move_price_by_ticks(invalidation, -1),
        "best_ask": invalidation,
        "age_sec": 0,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "AVOID"
    assert result["entry_price_low"] is None


def test_quote_bbo_incoherence_blocks_advisory():
    inputs = _ready_input()
    inputs["bbo"] = {"best_bid": 99_000, "best_ask": 99_100, "age_sec": 0}

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "DATA_WAIT"
    assert "quote_bbo_inconsistent" in result["source_quality"]["issues"]


def test_volume_confirmation_requires_both_bar_directions():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            100_000,
            100_200,
            99_900,
            100_100,
            1_000,
        )
        for index in range(8)
    ]

    passed, metadata = advisory._volume_confirmation(bars)

    assert passed is False
    assert metadata["rising_volume_sample_count"] == 8
    assert metadata["falling_volume_sample_count"] == 0
    assert metadata["volume_minimum_composition_met"] is False


def test_collector_scope_change_clears_session_local_caches(tmp_path):
    collector = advisory.SamsungWidgetCollector(
        snapshot_path=tmp_path / "snapshot.json",
        observation_dir=tmp_path / "observations",
    )
    premarket_now = datetime(2026, 8, 3, 8, 10, tzinfo=KST)
    collector._activate_scope(premarket_now, advisory.session_context(premarket_now))
    collector._minute_cache = {"scope": "premarket"}
    collector._relative_cache = {"scope": "premarket"}

    regular_now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    collector._activate_scope(regular_now, advisory.session_context(regular_now))

    assert collector._minute_cache == {}
    assert collector._relative_cache == {}
    assert collector._active_scope_key == (
        "2026-08-03",
        "KRX_REGULAR",
        "KRX",
        "005930",
    )


def test_stale_bbo_fails_closed_before_advisory():
    result = advisory.evaluate_advisory(**_ready_input(bbo_age=21.0))
    assert result["state"] == "DATA_WAIT"
    assert "bbo_stale" in result["source_quality"]["issues"]


def test_live_price_reversal_with_ask_pressure_is_immediate_negative_veto():
    inputs = _ready_input()
    inputs["current_price"] = 100_200
    inputs["bbo"] = {
        "best_bid": 100_100,
        "best_ask": 100_200,
        "best_bid_qty": 1_000,
        "best_ask_qty": 2_000,
        "age_sec": 0,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["live_reversal"]["veto"] is True
    assert "live_price_reversal_with_ask_pressure" in result["unmet_conditions"]


def test_future_completed_bar_time_conflict_fails_closed():
    inputs = _ready_input()
    future_bar = inputs["bars"][-1]
    inputs["bars"][-1] = advisory.MinuteBar(
        "20260803091100",
        future_bar.open,
        future_bar.high,
        future_bar.low,
        future_bar.close,
        future_bar.volume,
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "DATA_WAIT"
    assert "completed_bar_time_conflict" in result["source_quality"]["issues"]


def test_negative_bbo_age_is_rejected_as_invalid_freshness():
    result = advisory.evaluate_advisory(**_ready_input(bbo_age=-1.0))
    assert result["state"] == "DATA_WAIT"
    assert "bbo_stale" in result["source_quality"]["issues"]


def test_stale_rest_quote_fails_closed_before_advisory():
    inputs = _ready_input()
    inputs["quote_age_sec"] = 21.0
    result = advisory.evaluate_advisory(**inputs)
    assert result["state"] == "DATA_WAIT"
    assert "quote_stale" in result["source_quality"]["issues"]


def test_external_risk_can_downgrade_or_hold_but_not_promote():
    caution = advisory.evaluate_external_risk(_external({"NQ": -0.5}))
    hold = advisory.evaluate_external_risk(_external({"NQ": -0.5, "MU": -0.9}))
    severe = advisory.evaluate_external_risk(_external({"USDKRW": 0.6}))
    assert caution["level"] == "CAUTION"
    assert hold["level"] == "HOLD"
    assert severe["level"] == "HOLD"
    assert caution["positive_promotion_forbidden"] is True


def test_market_closed_micron_is_not_misclassified_as_stale_or_adverse():
    points = _external({"MU": -5.0})
    mu = points["MU"]
    points["MU"] = advisory.ExternalPoint(
        **{
            **mu.__dict__,
            "quality": "MARKET_CLOSED",
            "market_state": "MARKET_CLOSED",
            "age_sec": 10_000,
        }
    )
    result = advisory.evaluate_external_risk(points)
    assert result["level"] == "CLEAR"
    assert "MU" not in result["adverse"]
    assert "MU" not in result["stale"]


def test_micron_market_state_respects_nyse_holiday_calendar():
    assert not advisory._mu_extended_market_open(
        datetime(2026, 7, 3, 23, 0, tzinfo=KST)
    )
    assert advisory._mu_extended_market_open(datetime(2026, 7, 2, 23, 0, tzinfo=KST))


def test_external_stale_caps_domestic_ready_at_caution():
    inputs = _ready_input()
    inputs["external_points"] = _external(quality="STALE")
    result = advisory.evaluate_advisory(**inputs)
    assert result["state"] == "ENTRY_CAUTION"
    assert result["external_risk"]["level"] == "DATA_LIMITED"


def test_external_total_gap_caps_domestic_ready_at_caution():
    inputs = _ready_input()
    inputs["external_points"] = {}
    result = advisory.evaluate_advisory(**inputs)
    assert result["state"] == "ENTRY_CAUTION"
    assert result["external_risk"]["unavailable"] == ["NQ", "MU", "USDKRW"]


def test_cached_external_observation_becomes_stale_as_wall_clock_advances():
    inputs = _ready_input()
    old_time = (inputs["observed_at"] - timedelta(minutes=6)).isoformat()
    inputs["external_points"] = {
        key: advisory.ExternalPoint(
            **{
                **point.__dict__,
                "observed_at": old_time,
                "quality": "BEST_EFFORT_DELAYED",
                "age_sec": 10,
            }
        )
        for key, point in _external().items()
    }
    result = advisory.evaluate_advisory(**inputs)
    assert result["state"] == "ENTRY_CAUTION"
    assert result["external_risk"]["level"] == "DATA_LIMITED"
    assert result["external_points"]["NQ"]["quality"] == "STALE"


def test_external_hold_removes_entry_price_range():
    inputs = _ready_input()
    inputs["external_points"] = _external({"NQ": -0.9})
    result = advisory.evaluate_advisory(**inputs)
    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert "external_risk_hold" in result["unmet_conditions"]


def test_yahoo_provider_labels_data_best_effort_not_realtime():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    index = pd.date_range(
        now.astimezone(ZoneInfo("UTC")) - timedelta(minutes=19),
        periods=20,
        freq="1min",
    )
    frame = pd.DataFrame({"Close": range(100, 120)}, index=index)

    provider = advisory.YahooExternalMarketProvider(downloader=lambda **_: frame)
    point = provider._fetch_one("NQ", "NQ=F", now)

    assert point.provider == "yahoo_best_effort"
    assert point.quality == "BEST_EFFORT_DELAYED"
    assert point.change_15m_pct is not None


def test_yahoo_provider_requires_actual_15_minute_history():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    index = pd.date_range(
        now.astimezone(ZoneInfo("UTC")) - timedelta(minutes=9),
        periods=10,
        freq="1min",
    )
    frame = pd.DataFrame({"Close": range(100, 110)}, index=index)

    point = advisory.YahooExternalMarketProvider(
        downloader=lambda **_: frame
    )._fetch_one("NQ", "NQ=F", now)

    assert point.quality == "UNAVAILABLE"
    assert point.change_15m_pct is None
    assert point.reason == "insufficient_15m_history"


def test_yahoo_provider_fetches_independent_sources_concurrently():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    index = pd.date_range(
        now.astimezone(ZoneInfo("UTC")) - timedelta(minutes=19),
        periods=20,
        freq="1min",
    )
    frame = pd.DataFrame({"Close": range(100, 120)}, index=index)
    barrier = threading.Barrier(3)
    thread_ids: set[int] = set()

    def downloader(**_):
        thread_ids.add(threading.get_ident())
        barrier.wait(timeout=1)
        return frame

    points = advisory.YahooExternalMarketProvider(downloader=downloader).fetch(now)

    assert set(points) == {"NQ", "MU", "USDKRW"}
    assert len(thread_ids) == 3


def test_yahoo_provider_isolates_unexpected_single_source_failure(monkeypatch):
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    provider = advisory.YahooExternalMarketProvider(downloader=lambda **_: None)

    def fetch_one(key, ticker, observed_at):
        if key == "MU":
            raise ValueError("malformed_source")
        return _external()[key]

    monkeypatch.setattr(provider, "_fetch_one", fetch_one)
    points = provider.fetch(now)

    assert points["NQ"].quality == "BEST_EFFORT_DELAYED"
    assert points["MU"].quality == "UNAVAILABLE"
    assert points["MU"].reason == "ValueError"
    assert points["USDKRW"].quality == "BEST_EFFORT_DELAYED"


def test_spread_tick_count_handles_exchange_price_band_boundary():
    assert advisory._spread_tick_count(199_900, 200_000) == 1
    assert advisory._spread_tick_count(199_800, 200_500) == 3


def test_snapshot_freshness_uses_collector_observed_time():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    assert contract.snapshot_is_fresh(
        {"status": "ok", "observed_at_kst": (now - timedelta(seconds=20)).isoformat()},
        now=now,
    )
    assert not contract.snapshot_is_fresh(
        {"status": "ok", "observed_at_kst": (now - timedelta(seconds=26)).isoformat()},
        now=now,
    )
    assert not contract.snapshot_is_fresh(
        {"status": "ok", "observed_at_kst": "2026-08-03T09:10:00"},
        now=now,
    )


def test_actionable_snapshot_contract_rejects_expired_inner_advisory():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    context = contract.session_context(now)
    raw = advisory.evaluate_advisory(**_ready_input())
    raw["valid_until"] = (now - timedelta(seconds=1)).isoformat()

    assert not contract.advisory_contract_is_valid(
        raw,
        snapshot_observed_at=now,
        context=context,
    )


def test_snapshot_contract_rejects_invalid_trend_prediction_authority():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    context = contract.session_context(now)
    raw = advisory.evaluate_advisory(**_ready_input())
    raw["trend_assessment"]["future_prediction"] = True

    assert not contract.advisory_contract_is_valid(
        raw,
        snapshot_observed_at=now,
        context=context,
    )


def test_observation_recorder_writes_only_state_transition_and_minute_summary(
    tmp_path,
):
    recorder = advisory.ObservationRecorder(tmp_path)
    start = datetime(2026, 8, 3, 9, 10, 1, tzinfo=KST)

    def payload(state):
        return {
            "observed_at_kst": start.isoformat(),
            "current_price": 100_000,
            "market_venue": "KRX",
            "market_session": "KRX_REGULAR",
            "advisory": {"state": state},
            "observation": {"latest_completed_bar": None},
        }

    recorder.record(payload("WATCH"), start)
    recorder.record(payload("WATCH"), start + timedelta(seconds=10))
    recorder.record(payload("ENTRY_CAUTION"), start + timedelta(seconds=20))
    recorder.record(payload("ENTRY_CAUTION"), start + timedelta(minutes=1))
    rows = [
        json.loads(line)
        for line in (tmp_path / "samsung_widget_advisory_20260803.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert [row["observation_kind"] for row in rows] == [
        "state_transition",
        "state_transition",
        "minute_summary",
    ]
    assert rows[1]["previous_advisory_state"] == "WATCH"

    restarted = advisory.ObservationRecorder(tmp_path)
    restarted.record(payload("ENTRY_CAUTION"), start + timedelta(minutes=1, seconds=10))
    rows_after_same_state = (
        (tmp_path / "samsung_widget_advisory_20260803.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert len(rows_after_same_state) == 3

    restarted.record(payload("ENTRY_READY"), start + timedelta(minutes=1, seconds=20))
    rows_after_change = [
        json.loads(line)
        for line in (tmp_path / "samsung_widget_advisory_20260803.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rows_after_change) == 4
    assert rows_after_change[-1]["previous_advisory_state"] == "ENTRY_CAUTION"


def test_collector_uses_only_read_only_market_data_and_cached_token(
    monkeypatch, tmp_path
):
    now = datetime(2026, 8, 3, 9, 10, 5, tzinfo=KST)
    monkeypatch.setattr(
        advisory.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )

    def fail_if_issued(*args, **kwargs):
        raise AssertionError("collector must never issue or refresh a token")

    monkeypatch.setattr(advisory.kiwoom_utils, "get_kiwoom_token", fail_if_issued)
    monkeypatch.setattr(
        advisory.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://api.example.test{path}",
    )

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return {"return_code": 0, **self.payload}

    class FakeSession:
        def __init__(self):
            self.calls = []

        def post(self, url, *, headers, json, timeout):
            self.calls.append((headers["api-id"], url, json, timeout))
            api_id = headers["api-id"]
            if api_id == "ka10001":
                return Response(
                    {
                        "cur_prc": "100400",
                        "low_pric": "99800",
                        "flu_rt": "1.00" if json["stk_cd"] == "005930" else "0.80",
                    }
                )
            if api_id == "ka10004":
                return Response(
                    {
                        "buy_fpr_bid": "100300",
                        "sel_fpr_bid": "100400",
                        "buy_fpr_req": "1000",
                        "sel_fpr_req": "1200",
                        "bid_req_base_tm": "091005",
                    }
                )
            if api_id == "ka10003":
                return Response(
                    {
                        "cntr_infr": [
                            {"cur_prc": "100400"},
                            {"cur_prc": "100300"},
                            {"cur_prc": "100300"},
                        ]
                    }
                )
            if api_id == "ka10080":
                closes = [
                    100000,
                    99900,
                    100100,
                    100000,
                    100200,
                    100100,
                    100300,
                    100200,
                    100400,
                    100400,
                ]
                return Response(
                    {
                        "stk_min_pole_chart_qry": [
                            {
                                "cntr_tm": (
                                    datetime(2026, 8, 3, 9, 0, tzinfo=KST)
                                    + timedelta(minutes=index)
                                ).strftime("%Y%m%d%H%M%S"),
                                "open_pric": str(close - 100),
                                "high_pric": str(close + 50),
                                "low_pric": str(close - 150),
                                "cur_prc": str(close),
                                "trde_qty": "1000",
                            }
                            for index, close in enumerate(closes)
                        ]
                    }
                )
            if api_id == "ka10081":
                return Response(
                    {
                        "stk_dt_pole_chart_qry": [
                            {
                                "dt": "20260731",
                                "open_pric": "99000",
                                "high_pric": "102000",
                                "low_pric": "98000",
                                "cur_prc": "100000",
                            }
                        ]
                    }
                )
            if api_id == "ka20001":
                return Response({"flu_rt": "0.50"})
            if api_id == "ka20005":
                return Response(
                    {
                        "inds_min_pole_qry": [
                            {
                                "cntr_tm": (
                                    datetime(2026, 8, 3, 9, 0, tzinfo=KST)
                                    + timedelta(minutes=index)
                                ).strftime("%Y%m%d%H%M%S"),
                                "open_pric": str(300_000 + index * 100),
                                "high_pric": str(300_100 + index * 100),
                                "low_pric": str(299_900 + index * 100),
                                "cur_prc": str(300_000 + index * 100),
                                "trde_qty": "1000",
                            }
                            for index in range(10)
                        ]
                    }
                )
            if api_id == "ka10064":
                return Response(
                    {
                        "opmr_invsr_trde_chart": [
                            {"tm": "090000", "frgnr_invsr": "-100"},
                            {"tm": "091000", "frgnr_invsr": "-50"},
                        ]
                    }
                )
            if api_id == "ka90008":
                return Response(
                    {
                        "stk_tm_prm_trde_trnsn": [
                            {
                                "tm": "091000",
                                "prm_netprps_amt": "100",
                                "prm_netprps_amt_irds": "10",
                            }
                        ]
                    }
                )
            raise AssertionError(f"unexpected api-id: {api_id}")

    class ExternalProvider:
        def fetch(self, observed_at):
            return _external()

    request_session = FakeSession()
    snapshot_path = tmp_path / "snapshot.json"
    collector = advisory.SamsungWidgetCollector(
        snapshot_path=snapshot_path,
        observation_dir=tmp_path / "observations",
        external_provider=ExternalProvider(),
        request_session=request_session,
    )
    payload = collector.collect_once(now)

    assert payload["status"] == "ok"
    assert payload["market_session"] == "krx_or_closed"
    assert payload["advisory"]["session"] == "KRX_REGULAR"
    assert payload["advisory"]["authority"] == "widget_advisory_only"
    assert payload["advisory"]["broker_order_forbidden"] is True
    assert snapshot_path.exists()
    assert {call[0] for call in request_session.calls} == {
        "ka10001",
        "ka10003",
        "ka10004",
        "ka10064",
        "ka10080",
        "ka10081",
        "ka20001",
        "ka20005",
        "ka90008",
    }
    assert all(
        "order" not in call[1] and "acnt" not in call[1]
        for call in request_session.calls
    )


def test_read_only_client_blocks_non_market_data_before_network_call():
    class FailSession:
        def post(self, *args, **kwargs):
            raise AssertionError("forbidden request must not reach the network")

    client = advisory.KiwoomReadOnlyClient("TOKEN", session=FailSession())

    try:
        client.post("/api/dostk/acnt", "kt00001", {})
    except RuntimeError as exc:
        assert str(exc).startswith("forbidden_widget_kiwoom_request")
    else:
        raise AssertionError("account request was not blocked")


def test_collector_local_request_budget_reserves_mandatory_quote_and_bbo_calls():
    budget = advisory.ReadOnlyRequestBudget(max_requests_per_minute=4)

    budget.acquire(optional=True)
    budget.acquire(optional=True)
    try:
        budget.acquire(optional=True)
    except RuntimeError as exc:
        assert str(exc) == "widget_request_budget_exhausted"
    else:
        raise AssertionError("optional request consumed the mandatory reserve")

    budget.acquire(optional=False)
    budget.acquire(optional=False)
    assert budget.snapshot()["remaining_requests"] == 0
