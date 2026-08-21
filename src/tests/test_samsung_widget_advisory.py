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


def _exit_source_quality():
    return {"status": "PASS", "issues": []}


def test_exit_advisory_requires_a_second_completed_bar_for_ready():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(
        start,
        [100_000, 100_300, 100_500, 100_400, 100_200, 100_000, 99_500],
    )
    context = advisory.session_context(start + timedelta(minutes=7, seconds=5))
    machine = advisory.ExitAdvisoryStateMachine()
    bbo = {"best_bid": 99_400, "best_ask": 99_500}

    caution = machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=5),
        context=context,
        bars=bars,
        bbo=bbo,
        source_quality=_exit_source_quality(),
    )
    duplicate = machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=15),
        context=context,
        bars=bars,
        bbo=bbo,
        source_quality=_exit_source_quality(),
    )
    ready_bars = [*bars, *_bars(start + timedelta(minutes=7), [99_000])]
    ready = machine.apply(
        observed_at=start + timedelta(minutes=8, seconds=5),
        context=context,
        bars=ready_bars,
        bbo={"best_bid": 98_900, "best_ask": 99_000},
        source_quality=_exit_source_quality(),
    )

    assert caution["state"] == "EXIT_CAUTION"
    assert caution["holding_independent"] is True
    assert caution["future_prediction"] is False
    assert duplicate["state"] == "EXIT_CAUTION"
    assert duplicate["continuity"]["pending_bars"] == 0
    assert ready["state"] == "EXIT_READY"
    assert ready["reference_exit_price"] == 98_900
    assert ready["broken_support"] == caution["broken_support"]
    assert "broken_support_reclaim_failed" in ready["reasons"]


def test_exit_ready_is_only_a_reversal_watch_after_a_completed_recovery_bar():
    start = datetime(2026, 8, 3, 11, 0, tzinfo=KST)
    ready_bar = "20260803110300"
    exit_advisory = {
        "state": "EXIT_READY",
        "source_quality": _exit_source_quality(),
        "continuity": {
            "ready_bar": ready_bar,
            "bars_without_new_low": 1,
            "reclaim_bars": 1,
        },
    }
    bars = _bars(start, [100_000, 99_800, 99_600, 99_500, 99_700])

    observation = advisory._exit_contrarian_reversal_observation(exit_advisory, bars)

    assert observation["state"] == "REVERSAL_WATCH"
    assert observation["direct_entry_authority"] is False
    assert observation["actual_order_submitted"] is False
    assert "completed_recovery_bar" in observation["reasons"]


def test_exit_ready_does_not_grant_reversal_watch_before_post_signal_bar():
    start = datetime(2026, 8, 3, 11, 0, tzinfo=KST)
    bars = _bars(start, [100_000, 99_800, 99_600, 99_500])
    exit_advisory = {
        "state": "EXIT_READY",
        "source_quality": _exit_source_quality(),
        "continuity": {
            "ready_bar": bars[-1].source_time,
            "bars_without_new_low": 0,
            "reclaim_bars": 0,
        },
    }

    observation = advisory._exit_contrarian_reversal_observation(exit_advisory, bars)

    assert observation["state"] == "WAIT_CONFIRMATION"
    assert observation["unmet_conditions"] == ["first_post_exit_ready_bar_pending"]


def test_exit_advisory_cancels_after_two_completed_support_reclaims():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(
        start,
        [100_000, 100_300, 100_500, 100_400, 100_200, 100_000, 99_500],
    )
    context = advisory.session_context(start + timedelta(minutes=7, seconds=5))
    machine = advisory.ExitAdvisoryStateMachine()
    quality = _exit_source_quality()
    machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 99_400, "best_ask": 99_500},
        source_quality=quality,
        entry_advisory={"state": "ENTRY_CAUTION"},
    )
    bars.append(_bars(start + timedelta(minutes=7), [99_000])[0])
    ready = machine.apply(
        observed_at=start + timedelta(minutes=8, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 98_900, "best_ask": 99_000},
        source_quality=quality,
    )
    support = ready["broken_support"]
    assert support is not None
    assert ready["continuity"]["entry_episode_id"] is not None
    bars.extend(
        [
            advisory.MinuteBar(
                "20260803090800", support, support + 100, support, support, 1_000
            ),
            advisory.MinuteBar(
                "20260803090900",
                support,
                support + 200,
                support,
                support + 100,
                1_000,
            ),
            advisory.MinuteBar(
                "20260803091000",
                support + 100,
                support + 200,
                support,
                support + 100,
                1_000,
            ),
        ]
    )
    support_hold = machine.apply(
        observed_at=start + timedelta(minutes=9, seconds=5),
        context=context,
        bars=bars[:-2],
        bbo={"best_bid": support, "best_ask": support + 100},
        source_quality=quality,
    )
    first_reclaim = machine.apply(
        observed_at=start + timedelta(minutes=10, seconds=5),
        context=context,
        bars=bars[:-1],
        bbo={"best_bid": support, "best_ask": support + 100},
        source_quality=quality,
    )
    cancelled = machine.apply(
        observed_at=start + timedelta(minutes=11, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": support, "best_ask": support + 100},
        source_quality=quality,
    )

    assert support_hold["state"] == "EXIT_READY"
    assert support_hold["continuity"]["reclaim_bars"] == 0
    assert first_reclaim["state"] == "EXIT_READY"
    assert first_reclaim["continuity"]["reclaim_bars"] == 1
    assert cancelled["state"] == "EXIT_CANCELLED"
    assert cancelled["reasons"] == ["broken_support_reclaimed_two_bars"]
    assert cancelled["reference_exit_price"] is None
    assert cancelled["continuity"]["entry_episode_id"] is None


def test_same_observation_exit_warning_blocks_new_entry_episode():
    entry = {
        "state": "ENTRY_CAUTION",
        "raw_state": "ENTRY_CAUTION",
        "entry_price_low": 99_900,
        "entry_price_high": 100_000,
        "unmet_conditions": ["vwap_or_resistance_reclaimed"],
        "derived": {},
    }
    exit_advisory = {
        "state": "EXIT_CAUTION",
        "entry_episode_reset": True,
    }

    blocked = advisory._apply_entry_exit_conflict_guard(entry, exit_advisory)

    assert blocked is True
    assert entry["state"] == "WATCH"
    assert entry["raw_state"] == "WATCH"
    assert entry["entry_price_low"] is None
    assert entry["entry_price_high"] is None
    assert entry["confirmation_streak"] == 1
    assert "same_observation_exit_warning_active" in entry["unmet_conditions"]
    assert entry["derived"]["entry_exit_conflict_guard"]["blocked"] is True


def test_exit_warning_does_not_erase_existing_entry_episode_provenance():
    entry = {
        "state": "ENTRY_CAUTION",
        "raw_state": "ENTRY_CAUTION",
        "entry_price_low": 99_900,
        "entry_price_high": 100_000,
        "unmet_conditions": [],
        "derived": {},
    }
    exit_advisory = {
        "state": "EXIT_CAUTION",
        "entry_episode_reset": False,
    }

    blocked = advisory._apply_entry_exit_conflict_guard(entry, exit_advisory)

    assert blocked is False
    assert entry["state"] == "ENTRY_CAUTION"
    assert entry["derived"]["entry_exit_conflict_guard"]["blocked"] is False


def test_exit_machine_can_remove_only_rejected_same_cycle_entry_link():
    machine = advisory.ExitAdvisoryStateMachine()
    machine._entry_was_actionable = True
    machine._entry_episode_id = "2026-08-10:KRX_REGULAR:20260810104000"

    assert machine.reject_current_entry_episode_reset() is True
    assert machine.snapshot()["entry_was_actionable"] is False
    assert machine.snapshot()["entry_episode_id"] is None
    assert machine.reject_current_entry_episode_reset() is False


def test_exit_advisory_no_new_low_cancel_requires_support_rearm():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(
        start,
        [100_000, 100_300, 100_500, 100_400, 100_200, 100_000, 99_500],
    )
    context = advisory.session_context(start + timedelta(minutes=7, seconds=5))
    machine = advisory.ExitAdvisoryStateMachine()
    quality = _exit_source_quality()
    machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 99_400, "best_ask": 99_500},
        source_quality=quality,
    )
    bars.append(_bars(start + timedelta(minutes=7), [99_000])[0])
    ready = machine.apply(
        observed_at=start + timedelta(minutes=8, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 98_900, "best_ask": 99_000},
        source_quality=quality,
    )
    support = ready["broken_support"]
    assert support is not None
    cancelled = None
    for offset in range(8, 13):
        bars.append(
            advisory.MinuteBar(
                (start + timedelta(minutes=offset)).strftime("%Y%m%d%H%M%S"),
                99_000,
                99_100,
                98_950,
                99_000,
                1_000,
            )
        )
        cancelled = machine.apply(
            observed_at=start + timedelta(minutes=offset + 1, seconds=5),
            context=context,
            bars=bars,
            bbo={"best_bid": 98_900, "best_ask": 99_000},
            source_quality=quality,
        )
    assert cancelled is not None
    assert cancelled["state"] == "EXIT_CANCELLED"
    assert cancelled["continuity"]["rearm_support"] == support

    bars.append(
        advisory.MinuteBar("20260803091300", 99_000, 99_000, 98_500, 98_500, 1_000)
    )
    locked = machine.apply(
        observed_at=start + timedelta(minutes=14, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 98_400, "best_ask": 98_500},
        source_quality=quality,
    )

    assert locked["state"] == "EXIT_WATCH"
    assert "exit_rearm_pending" in locked["unmet_conditions"]


def test_exit_advisory_new_entry_episode_releases_stale_rearm():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(
        start,
        [100_000, 100_300, 100_500, 100_400, 100_200, 100_000, 99_500],
    )
    context = advisory.session_context(start + timedelta(minutes=7, seconds=5))
    machine = advisory.ExitAdvisoryStateMachine()
    quality = _exit_source_quality()
    machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 99_400, "best_ask": 99_500},
        source_quality=quality,
    )
    bars.append(_bars(start + timedelta(minutes=7), [99_000])[0])
    machine.apply(
        observed_at=start + timedelta(minutes=8, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 98_900, "best_ask": 99_000},
        source_quality=quality,
    )
    for offset in range(8, 13):
        bars.append(
            advisory.MinuteBar(
                (start + timedelta(minutes=offset)).strftime("%Y%m%d%H%M%S"),
                99_000,
                99_100,
                98_950,
                99_000,
                1_000,
            )
        )
        machine.apply(
            observed_at=start + timedelta(minutes=offset + 1, seconds=5),
            context=context,
            bars=bars,
            bbo={"best_bid": 98_900, "best_ask": 99_000},
            source_quality=quality,
        )
    assert machine.snapshot()["rearm_support"] is not None

    bars.append(
        advisory.MinuteBar("20260803091300", 99_000, 99_100, 98_900, 99_000, 1_000)
    )
    reset = machine.apply(
        observed_at=start + timedelta(minutes=14, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 98_900, "best_ask": 99_000},
        source_quality=quality,
        entry_advisory={"state": "ENTRY_CAUTION"},
    )

    assert reset["state"] == "EXIT_WATCH"
    assert reset["entry_episode_reset"] is True
    assert reset["continuity"]["rearm_support"] is None
    assert "exit_rearm_pending" not in reset["unmet_conditions"]


def test_exit_advisory_local_peak_rollover_does_not_wait_for_session_vwap():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(
        start,
        [100_000, 100_500, 101_000, 101_500, 102_000, 102_500],
    )
    bars.append(
        advisory.MinuteBar("20260803090600", 102_000, 102_000, 101_000, 101_000, 2_000)
    )
    context = advisory.session_context(start + timedelta(minutes=7, seconds=5))
    machine = advisory.ExitAdvisoryStateMachine()

    caution = machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 100_900, "best_ask": 101_000},
        source_quality=_exit_source_quality(),
    )

    assert caution["state"] == "EXIT_CAUTION"
    assert caution["local_peak_rollover"] is True
    assert caution["continuity"]["caution_kind"] == "local_peak_rollover"
    assert caution["session_vwap"] is not None
    assert caution["reference_exit_price"] == 100_900
    assert "below_session_vwap" not in caution["reasons"]
    assert "local_support_break_confirmation_pending" in caution["reasons"]

    bars.extend(
        [
            advisory.MinuteBar(
                "20260803090700", 101_000, 101_000, 100_500, 100_500, 1_500
            ),
            advisory.MinuteBar(
                "20260803090800", 100_500, 100_500, 99_900, 100_000, 1_500
            ),
        ]
    )
    machine.apply(
        observed_at=start + timedelta(minutes=8, seconds=5),
        context=context,
        bars=bars[:-1],
        bbo={"best_bid": 100_400, "best_ask": 100_500},
        source_quality=_exit_source_quality(),
    )
    ready = machine.apply(
        observed_at=start + timedelta(minutes=9, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 99_900, "best_ask": 100_000},
        source_quality=_exit_source_quality(),
    )

    assert ready["state"] == "EXIT_READY"
    assert "local_peak_rollover_continued" in ready["reasons"]
    assert "three_minute_down_confirmed" in ready["reasons"]


def test_exit_advisory_restores_internal_state_from_failure_data_wait_snapshot():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(
        start,
        [100_000, 100_300, 100_500, 100_400, 100_200, 100_000, 99_500],
    )
    context = advisory.session_context(start + timedelta(minutes=7, seconds=5))
    machine = advisory.ExitAdvisoryStateMachine()
    quality = _exit_source_quality()
    machine.apply(
        observed_at=start + timedelta(minutes=7, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 99_400, "best_ask": 99_500},
        source_quality=quality,
    )
    bars.append(_bars(start + timedelta(minutes=7), [99_000])[0])
    machine.apply(
        observed_at=start + timedelta(minutes=8, seconds=5),
        context=context,
        bars=bars,
        bbo={"best_bid": 98_900, "best_ask": 99_000},
        source_quality=quality,
    )
    for offset in range(8, 13):
        bars.append(
            advisory.MinuteBar(
                (start + timedelta(minutes=offset)).strftime("%Y%m%d%H%M%S"),
                99_000,
                99_100,
                98_950,
                99_000,
                1_000,
            )
        )
        machine.apply(
            observed_at=start + timedelta(minutes=offset + 1, seconds=5),
            context=context,
            bars=bars,
            bbo={"best_bid": 98_900, "best_ask": 99_000},
            source_quality=quality,
        )

    continuity = machine.snapshot()
    persisted = {"state": "DATA_WAIT", "continuity": continuity}
    restored = advisory.ExitAdvisoryStateMachine()

    assert restored.restore(persisted) is True
    assert restored.snapshot()["state"] == "EXIT_CANCELLED"
    assert restored.snapshot()["rearm_support"] == continuity["rearm_support"]
    assert restored.snapshot()["rearm_support"] is not None


def test_exit_advisory_fails_closed_without_fresh_complete_source():
    now = datetime(2026, 8, 3, 9, 10, 5, tzinfo=KST)
    result = advisory.ExitAdvisoryStateMachine().apply(
        observed_at=now,
        context=advisory.session_context(now),
        bars=[],
        bbo={},
        source_quality={"status": "BLOCKED", "issues": ["quote_stale"]},
    )

    assert result["state"] == "DATA_WAIT"
    assert result["reference_exit_price"] is None
    assert "quote_stale" in result["unmet_conditions"]


def test_exit_advisory_contract_rejects_runtime_or_holding_authority():
    now = datetime(2026, 8, 3, 9, 10, 5, tzinfo=KST)
    context = advisory.session_context(now)
    payload = {
        "state": "EXIT_READY",
        "session": context.name,
        "peak_price": 101_000,
        "broken_support": 100_000,
        "reference_exit_price": 99_900,
        "observed_at": now.isoformat(),
        "valid_until": (now + timedelta(seconds=60)).isoformat(),
        "source_quality": {"status": "PASS"},
        "holding_independent": True,
        "future_prediction": False,
        "authority": contract.ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    assert contract.exit_advisory_contract_is_valid(
        payload,
        snapshot_observed_at=now,
        context=context,
        evaluated_at=now,
    )
    payload["holding_independent"] = False
    assert not contract.exit_advisory_contract_is_valid(
        payload,
        snapshot_observed_at=now,
        context=context,
        evaluated_at=now,
    )


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


def test_intraday_regime_detects_persistent_lower_high_and_lower_low():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(start, [240_000 - index * 250 for index in range(30)])

    regime = advisory.analyze_intraday_regime(bars)

    assert regime["state"] == "down"
    assert regime["lower_high"] is True
    assert regime["lower_low"] is True
    assert regime["future_prediction"] is False


def test_intraday_regime_requires_contiguous_completed_bars():
    start = datetime(2026, 8, 3, 9, 0, tzinfo=KST)
    bars = _bars(start, [100_000 + index * 100 for index in range(15)])
    bars[-1] = advisory.MinuteBar(
        "20260803091600", 101_300, 101_500, 101_200, 101_400, 1_000
    )

    regime = advisory.analyze_intraday_regime(bars)

    assert regime["state"] == "unavailable"
    assert regime["reason"] == "non_contiguous_completed_bars"


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
    assert structure["candidate_support_age_bars"] == 4
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


def test_recent_resistance_reclaim_is_an_alternative_to_vwap(monkeypatch):
    inputs = _ready_input(current_price=100_400)
    inputs["bbo"] = {"best_bid": 100_300, "best_ask": 100_400, "age_sec": 0}
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 101_000)
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_000,
            "recent_resistance": 100_300,
            "higher_high": True,
            "higher_low": True,
            "higher_high_and_low": True,
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["raw_state"] == "ENTRY_CAUTION"
    assert result["derived"]["vwap_reclaimed"] is False
    assert result["derived"]["recent_resistance_reclaimed"] is True
    assert result["derived"]["reclaim_mode"] == "recent_resistance"
    assert result["entry_price_low"] == 100_300
    assert result["entry_price_high"] == 100_400


def test_resistance_only_breakout_waits_for_pullback_above_one_tick(monkeypatch):
    inputs = _ready_input(current_price=100_500)
    inputs["bbo"] = {"best_bid": 100_400, "best_ask": 100_500, "age_sec": 0}
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 101_000)
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_000,
            "recent_resistance": 100_300,
            "higher_high": True,
            "higher_low": True,
            "higher_high_and_low": True,
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["raw_state"] == "WATCH"
    assert "resistance_reclaim_pullback_pending" in result["unmet_conditions"]
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None


def test_nxt_aftermarket_vwap_only_without_higher_structure_stays_watch(
    monkeypatch,
):
    inputs = _ready_input(current_price=100_400)
    inputs["observed_at"] = datetime(2026, 8, 3, 15, 50, 5, tzinfo=KST)
    inputs["context"] = advisory.session_context(inputs["observed_at"])
    inputs["bars"] = _bars(
        datetime(2026, 8, 3, 15, 40, tzinfo=KST),
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
            100_400,
        ],
    )
    inputs["bbo"] = {"best_bid": 100_300, "best_ask": 100_400, "age_sec": 0}
    inputs["external_points"] = _external(quality="STALE")
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_300,
            "candidate_support": 100_300,
            "recent_resistance": 100_500,
            "higher_high": False,
            "higher_low": False,
            "higher_high_and_low": False,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["external_risk"]["level"] == "DATA_LIMITED"
    assert result["derived"]["recent_resistance_reclaimed"] is False
    assert result["derived"]["higher_high_and_low"] is False
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert result["derived"]["vwap_only_structure_confirmed"] is False


def test_krx_vwap_only_without_higher_structure_stays_watch(monkeypatch):
    inputs = _ready_input(current_price=100_400)
    inputs["bbo"] = {"best_bid": 100_300, "best_ask": 100_400, "age_sec": 0}
    inputs["external_points"] = _external(quality="STALE")
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_300,
            "candidate_support": 100_300,
            "recent_resistance": 100_500,
            "higher_high": False,
            "higher_low": False,
            "higher_high_and_low": False,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert (
        "nxt_aftermarket_reclaim_structure_unconfirmed"
        not in result["unmet_conditions"]
    )
    assert result["derived"]["vwap_only_structure_confirmed"] is False


def _recovery_episode_advisory(
    observed_at: datetime,
    *,
    volume_confirmed: bool,
    current_price: int,
    structural_support: int = 244_000,
) -> dict:
    reasons = [
        "low_structure_confirmed",
        "three_five_minute_not_down",
        "relative_strength_not_weak",
        "spread_within_two_ticks",
    ]
    unmet = ["vwap_or_resistance_reclaimed", "regular_flow_unavailable"]
    if volume_confirmed:
        reasons.append("rebound_volume_confirmed")
    else:
        unmet.append("rebound_volume_confirmed")
    return {
        "state": "WATCH",
        "raw_state": "WATCH",
        "session": "KRX_REGULAR",
        "observed_at": observed_at.isoformat(),
        "valid_until": (observed_at + timedelta(seconds=60)).isoformat(),
        "entry_price_low": None,
        "entry_price_high": None,
        "reasons": reasons,
        "unmet_conditions": unmet,
        "source_quality": {"status": "PASS", "issues": []},
        "external_risk": {"level": "DATA_LIMITED"},
        "derived": {
            "structural_support": structural_support,
            "recent_resistance": 246_000,
        },
        "current_price": current_price,
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_recovery_episode_carries_volume_evidence_into_confirmed_pullback():
    start = datetime(2026, 8, 5, 10, 31, 6, tzinfo=KST)
    filter_ = advisory.AdvisoryRecoveryEpisodeFilter()
    armed = filter_.apply(
        _recovery_episode_advisory(
            start,
            volume_confirmed=True,
            current_price=245_500,
            structural_support=245_000,
        ),
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103000", 245_000, 246_000, 244_500, 245_750, 77_843
        ),
    )
    breakout = filter_.apply(
        _recovery_episode_advisory(
            start + timedelta(minutes=2),
            volume_confirmed=True,
            current_price=247_000,
            structural_support=245_000,
        ),
        current_price=247_000,
        bbo={"best_bid": 246_500, "best_ask": 247_000},
        latest_bar=advisory.MinuteBar(
            "20260805103200", 245_250, 247_000, 245_000, 246_500, 83_510
        ),
    )
    pullback_input = _recovery_episode_advisory(
        start + timedelta(minutes=3),
        volume_confirmed=False,
        current_price=246_000,
        structural_support=245_000,
    )
    pullback_input["unmet_conditions"].append("early_reversal_rebound_volume_required")
    pullback = filter_.apply(
        pullback_input,
        current_price=246_000,
        bbo={"best_bid": 246_000, "best_ask": 246_500},
        latest_bar=advisory.MinuteBar(
            "20260805103300", 246_500, 247_000, 246_000, 246_500, 47_458
        ),
    )

    assert armed["state"] == "WATCH"
    assert breakout["state"] == "WATCH"
    assert breakout["recovery_continuity"]["reclaimed_bar"] == "20260805103200"
    restored_filter = advisory.AdvisoryRecoveryEpisodeFilter()
    assert restored_filter.restore(breakout) is True
    restored_pullback_input = _recovery_episode_advisory(
        start + timedelta(minutes=3),
        volume_confirmed=False,
        current_price=246_000,
        structural_support=245_000,
    )
    restored_pullback_input["unmet_conditions"].append(
        "early_reversal_rebound_volume_required"
    )
    restored_pullback = restored_filter.apply(
        restored_pullback_input,
        current_price=246_000,
        bbo={"best_bid": 246_000, "best_ask": 246_500},
        latest_bar=advisory.MinuteBar(
            "20260805103300", 246_500, 247_000, 246_000, 246_500, 47_458
        ),
    )
    assert pullback == restored_pullback
    assert pullback["raw_state"] == "ENTRY_CAUTION"
    assert pullback["entry_price_low"] == 246_000
    assert pullback["entry_price_high"] == 246_500
    assert "recent_rebound_volume_grace" in pullback["reasons"]
    assert "regular_flow_unavailable" in pullback["unmet_conditions"]
    assert "early_reversal_rebound_volume_required" not in pullback["unmet_conditions"]
    assert pullback["derived"]["recovery_episode"]["reclaim_age_bars"] == 1
    assert pullback["runtime_effect"] is False
    assert pullback["actual_order_submitted"] is False
    evaluated_at = start + timedelta(minutes=3)
    assert contract.advisory_contract_is_valid(
        pullback,
        snapshot_observed_at=evaluated_at,
        context=contract.session_context(evaluated_at),
        evaluated_at=evaluated_at,
    )


def test_recovery_episode_ignores_forming_price_only_resistance_touch():
    start = datetime(2026, 8, 5, 10, 31, 6, tzinfo=KST)
    filter_ = advisory.AdvisoryRecoveryEpisodeFilter()
    filter_.apply(
        _recovery_episode_advisory(start, volume_confirmed=True, current_price=245_500),
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103000", 245_000, 246_000, 244_500, 245_750, 77_843
        ),
    )

    forming_touch = filter_.apply(
        _recovery_episode_advisory(
            start + timedelta(minutes=1),
            volume_confirmed=True,
            current_price=246_500,
        ),
        current_price=246_500,
        bbo={"best_bid": 246_000, "best_ask": 246_500},
        latest_bar=advisory.MinuteBar(
            "20260805103100", 245_500, 246_000, 245_000, 245_500, 70_000
        ),
    )

    assert forming_touch["state"] == "WATCH"
    assert forming_touch["recovery_continuity"]["armed"] is True
    assert forming_touch["recovery_continuity"]["reclaimed_bar"] is None


def test_recovery_episode_does_not_bypass_source_quality():
    start = datetime(2026, 8, 5, 10, 31, 6, tzinfo=KST)
    filter_ = advisory.AdvisoryRecoveryEpisodeFilter()
    armed = _recovery_episode_advisory(
        start, volume_confirmed=True, current_price=245_500
    )
    armed["source_quality"] = {"status": "BLOCKED", "issues": ["quote_stale"]}

    blocked = filter_.apply(
        armed,
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103000", 245_000, 246_000, 244_500, 245_750, 77_843
        ),
    )

    assert blocked["state"] == "WATCH"
    assert blocked["recovery_continuity"]["armed"] is False


def test_recovery_episode_is_cancelled_by_completed_support_break():
    start = datetime(2026, 8, 5, 10, 31, 6, tzinfo=KST)
    filter_ = advisory.AdvisoryRecoveryEpisodeFilter()
    filter_.apply(
        _recovery_episode_advisory(start, volume_confirmed=True, current_price=245_500),
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103000", 245_000, 246_000, 244_500, 245_750, 77_843
        ),
    )

    cancelled = filter_.apply(
        _recovery_episode_advisory(
            start + timedelta(minutes=1),
            volume_confirmed=True,
            current_price=243_500,
        ),
        current_price=243_500,
        bbo={"best_bid": 243_500, "best_ask": 244_000},
        latest_bar=advisory.MinuteBar(
            "20260805103100", 244_500, 245_000, 243_500, 243_500, 90_000
        ),
    )

    assert cancelled["state"] == "WATCH"
    assert cancelled["recovery_continuity"]["armed"] is False


def test_recovery_episode_is_cancelled_when_continuation_trend_turns_down():
    start = datetime(2026, 8, 5, 10, 31, 6, tzinfo=KST)
    filter_ = advisory.AdvisoryRecoveryEpisodeFilter()
    filter_.apply(
        _recovery_episode_advisory(start, volume_confirmed=True, current_price=245_500),
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103000", 245_000, 246_000, 244_500, 245_750, 77_843
        ),
    )
    downtrend = _recovery_episode_advisory(
        start + timedelta(minutes=1),
        volume_confirmed=True,
        current_price=245_500,
    )
    downtrend["reasons"].remove("three_five_minute_not_down")
    downtrend["unmet_conditions"].append("three_five_minute_not_down")

    cancelled = filter_.apply(
        downtrend,
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103100", 245_500, 246_000, 245_000, 245_500, 40_000
        ),
    )

    assert cancelled["state"] == "WATCH"
    assert cancelled["recovery_continuity"]["armed"] is False


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


def test_promotion_filter_applies_bounded_three_observation_calibration():
    ready = advisory.evaluate_advisory(**_ready_input())
    filter_ = advisory.AdvisoryPromotionFilter()
    policy = {
        "policy_version": "widget_advisory_policy_2026-08-04_from_2026-08-03",
        "effective_date": "2026-08-04",
        "source_target_date": "2026-08-03",
        "load_status": "dated_policy_loaded",
        "decision": "tighten_confirmation",
        "reason": "cumulative_10m_adverse_first_exceeds_target_first",
        "authority": "widget_advisory_calibration_only",
        "widget_runtime_effect": True,
        "trading_runtime_effect": False,
        "runtime_effect": False,
    }

    first = filter_.apply(ready, required_confirmations=3, calibration_policy=policy)
    second = filter_.apply(ready, required_confirmations=3, calibration_policy=policy)
    third = filter_.apply(ready, required_confirmations=3, calibration_policy=policy)

    assert first["state"] == "WATCH"
    assert second["state"] == "WATCH"
    assert third["state"] == "ENTRY_READY"
    assert second["required_actionable_confirmations"] == 3
    assert second["calibration_policy"]["trading_runtime_effect"] is False
    assert "awaiting_calibrated_10s_confirmation" in second["unmet_conditions"]


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


def test_relative_strength_accepts_portable_primary_peer_market_schema():
    context = contract.session_context(datetime(2026, 8, 5, 10, 0, tzinfo=KST))
    portable = {
        "primary_change_pct": -1.0,
        "peer_change_pct": 0.0,
        "market_change_pct": 0.0,
        "same_window_generic": {},
    }

    ok, issues = advisory._relative_quality(portable, context)

    assert ok is False
    assert issues == ["relative_strength_weak"]

    portable["primary_change_pct"] = 0.0
    ok, issues = advisory._relative_quality(portable, context)

    assert ok is True
    assert issues == []


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
            "confirmed_support": 100_800,
            "candidate_support": 100_800,
            "support_confirmation": "retest_held",
            "recent_resistance": 101_000,
        },
    )
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 101_000)
    inputs = _ready_input(current_price=101_200)
    inputs["bars"] = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [
            100_700,
            100_800,
            100_700,
            100_900,
            100_800,
            101_000,
            100_900,
            101_100,
            101_000,
            101_200,
        ],
    )
    inputs["bbo"] = {"best_bid": 101_100, "best_ask": 101_200, "age_sec": 0}

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_READY"
    assert result["entry_price_low"] == 101_100
    assert result["entry_price_high"] == 101_200
    assert result["derived"]["structural_chase_pct"] > 0.3
    assert result["derived"]["tactical_chase_pct"] < 0.3
    assert result["derived"]["chase_pct"] == result["derived"]["tactical_chase_pct"]
    assert result["derived"]["chase_basis"] == "tactical_support"


def test_entry_reward_risk_uses_one_percent_tick_target_and_worst_entry_price():
    rejected = advisory._entry_reward_risk_assessment(
        entry_price_high=231_000,
        invalidation_price=228_000,
    )
    accepted = advisory._entry_reward_risk_assessment(
        entry_price_high=231_500,
        invalidation_price=230_000,
    )

    assert rejected["target_price"] == 233_500
    assert rejected["reward_risk_ratio"] == 0.8333
    assert rejected["passed"] is False
    assert accepted["target_price"] == 234_000
    assert accepted["reward_risk_ratio"] == 1.6667
    assert accepted["passed"] is True


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
        "same_window": {
            "sk_hynix": {"5m": {"relative_return_pct_point": -1.0}},
            "kospi": {"5m": {"relative_return_pct_point": -1.0}},
        },
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert "relative_strength_weak" in result["unmet_conditions"]
    assert "price_more_than_30bp_above_support" not in result["reasons"]
    assert result["derived"]["latent_next_blockers"] == [
        "recent_runup_near_rolling_high",
        "price_above_dynamic_two_tick_chase_limit",
    ]


def test_transient_relative_weakness_demotes_complete_recovery_to_caution():
    inputs = _ready_input()
    inputs["relative"] = {
        "samsung_change_pct": 0.5,
        "sk_hynix_change_pct": 1.1,
        "kospi_change_pct": 0.6,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_CAUTION"
    assert result["derived"]["relative_strength_policy"]["caution_only"] is True
    assert result["derived"]["relative_strength_policy"]["hard_veto"] is False
    assert "relative_weakness_caution_only" in result["reasons"]
    assert "relative_strength_weak" in result["unmet_conditions"]


def test_session_and_same_window_relative_weakness_remains_hard_veto():
    inputs = _ready_input()
    inputs["relative"] = {
        "samsung_change_pct": -1.0,
        "sk_hynix_change_pct": 0.5,
        "kospi_change_pct": 0.5,
        "same_window": {
            "sk_hynix": {"5m": {"relative_return_pct_point": -1.0}},
            "kospi": {"5m": {"relative_return_pct_point": -1.0}},
        },
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["derived"]["relative_strength_policy"]["hard_veto"] is True
    assert result["derived"]["relative_strength_policy"]["caution_only"] is False


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


def test_live_support_break_without_pressure_is_soft_watch():
    inputs = _ready_input()
    inputs["current_price"] = 99_000
    inputs["bbo"] = {"best_bid": 98_900, "best_ask": 99_000, "age_sec": 0}

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["invalidation"] == "soft_support_break_pending_confirmation"
    assert "soft_support_break" in result["unmet_conditions"]
    assert result["derived"]["session_vwap"] is not None
    assert result["derived"]["support_confirmation"] != "unconfirmed"
    assert "distance_from_structural_support_pct" in result["derived"]


def test_deep_live_break_with_ask_pressure_is_immediate_avoid():
    baseline = advisory.evaluate_advisory(**_ready_input())
    invalidation = baseline["invalidation_price"]
    inputs = _ready_input()
    inputs["current_price"] = invalidation
    inputs["bbo"] = {
        "best_bid": advisory.move_price_by_ticks(invalidation, -1),
        "best_ask": invalidation,
        "best_bid_qty": 100,
        "best_ask_qty": 200,
        "age_sec": 0,
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "AVOID"
    assert result["entry_price_low"] is None
    assert result["derived"]["invalidation_confirmation"]["deep_live_break"] is True


def test_completed_close_below_support_confirms_break(monkeypatch):
    inputs = _ready_input(current_price=100_000)
    fixed_support = 100_100
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            "higher_low": True,
            "higher_high": True,
            "higher_high_and_low": True,
            "retest_held": False,
            "retest_rebound_confirmed": False,
            "confirmed_support": fixed_support,
            "candidate_support": fixed_support,
            "support_confirmation": "higher_high_and_low",
            "confirmed_support_age_bars": 1,
            "recent_resistance": 100_000,
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "AVOID"
    assert (
        result["derived"]["invalidation_confirmation"]["completed_close_break"] is True
    )


def test_confirmed_retest_without_rebound_volume_stays_watch(monkeypatch):
    inputs = _ready_input(current_price=100_200)
    first_bar = inputs["bars"][0]
    inputs["bars"][0] = advisory.MinuteBar(
        source_time=first_bar.source_time,
        open=first_bar.open,
        high=101_500,
        low=100_000,
        close=first_bar.close,
        volume=first_bar.volume,
    )
    pullback_bar = inputs["bars"][5]
    inputs["bars"][5] = advisory.MinuteBar(
        source_time=pullback_bar.source_time,
        open=pullback_bar.open,
        high=pullback_bar.high,
        low=99_500,
        close=pullback_bar.close,
        volume=pullback_bar.volume,
    )
    inputs["bbo"] = {"best_bid": 100_100, "best_ask": 100_200, "age_sec": 0}
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 101_000)
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_000,
            "candidate_support": 100_000,
            "recent_resistance": 101_000,
            "higher_high": True,
            "higher_low": True,
            "higher_high_and_low": True,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )
    monkeypatch.setattr(
        advisory,
        "_volume_confirmation",
        lambda _bars: (
            False,
            {
                "rebound_avg_volume": 1_000.0,
                "decline_avg_volume": 1_500.0,
                "first_test_volume": 1_500,
                "retest_volume": 1_000,
                "retest_volume_contracted": True,
                "rising_volume_sample_count": 2,
                "falling_volume_sample_count": 2,
                "zero_volume_count": 0,
                "zero_volume_ratio": 0.0,
                "volume_minimum_composition_met": True,
            },
        ),
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert (
        result["derived"]["early_reversal_confirmation_floor"][
            "pre_volume_structure_eligible"
        ]
        is True
    )
    assert "vwap_or_resistance_reclaimed" in result["unmet_conditions"]
    assert "rebound_volume_confirmed" in result["unmet_conditions"]
    assert "early_reversal_rebound_volume_required" in result["unmet_conditions"]


def test_confirmed_retest_with_rebound_volume_can_emit_early_reversal_caution(
    monkeypatch,
):
    inputs = _ready_input(current_price=100_200)
    first_bar = inputs["bars"][0]
    inputs["bars"][0] = advisory.MinuteBar(
        source_time=first_bar.source_time,
        open=first_bar.open,
        high=101_500,
        low=100_000,
        close=first_bar.close,
        volume=first_bar.volume,
    )
    pullback_bar = inputs["bars"][5]
    inputs["bars"][5] = advisory.MinuteBar(
        source_time=pullback_bar.source_time,
        open=pullback_bar.open,
        high=pullback_bar.high,
        low=99_500,
        close=pullback_bar.close,
        volume=pullback_bar.volume,
    )
    inputs["bbo"] = {"best_bid": 100_100, "best_ask": 100_200, "age_sec": 0}
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 101_000)
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_000,
            "candidate_support": 100_000,
            "recent_resistance": 101_000,
            "higher_high": True,
            "higher_low": True,
            "higher_high_and_low": True,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )
    monkeypatch.setattr(
        advisory,
        "_volume_confirmation",
        lambda _bars: (
            True,
            {
                "rebound_avg_volume": 1_600.0,
                "decline_avg_volume": 1_500.0,
                "first_test_volume": 1_500,
                "retest_volume": 1_000,
                "retest_volume_contracted": True,
                "rising_volume_sample_count": 2,
                "falling_volume_sample_count": 2,
                "zero_volume_count": 0,
                "zero_volume_ratio": 0.0,
                "volume_minimum_composition_met": True,
            },
        ),
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "ENTRY_CAUTION"
    assert result["trigger"] == "confirmed_retest_early_reversal"
    assert result["entry_price_low"] == 100_100
    assert result["entry_price_high"] == 100_200
    assert (
        result["derived"]["early_reversal_confirmation_floor"][
            "rebound_volume_confirmed"
        ]
        is True
    )
    assert (
        result["derived"]["early_reversal_caution"]["ready_promotion_forbidden"] is True
    )
    assert "vwap_or_resistance_reclaimed" in result["unmet_conditions"]


def test_confirmed_retest_in_intraday_down_regime_stays_watch(monkeypatch):
    inputs = _ready_input(current_price=101_100)
    inputs["bars"] = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [104_000 - index * 100 for index in range(30)],
    )
    inputs["observed_at"] = datetime(2026, 8, 3, 9, 30, 5, tzinfo=KST)
    inputs["context"] = advisory.session_context(inputs["observed_at"])
    inputs["current_price"] = inputs["bars"][-1].close
    inputs["bbo"] = {
        "best_bid": inputs["current_price"] - 100,
        "best_ask": inputs["current_price"],
        "age_sec": 0,
    }
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 105_000)
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": inputs["current_price"] - 100,
            "candidate_support": inputs["current_price"] - 100,
            "recent_resistance": inputs["current_price"] + 500,
            "higher_high": True,
            "higher_low": True,
            "higher_high_and_low": True,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )
    monkeypatch.setattr(
        advisory,
        "_volume_confirmation",
        lambda _bars: (
            True,
            {
                "rebound_avg_volume": 2_000.0,
                "decline_avg_volume": 1_000.0,
                "rebound_to_decline_volume_ratio": 2.0,
                "first_test_volume": 1_500,
                "retest_volume": 1_000,
                "retest_volume_contracted": True,
                "rising_volume_sample_count": 3,
                "falling_volume_sample_count": 2,
                "zero_volume_count": 0,
                "zero_volume_ratio": 0.0,
                "volume_minimum_composition_met": True,
            },
        ),
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["intraday_regime"]["state"] == "down"
    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None
    assert (
        "intraday_down_regime_resistance_reclaim_pending" in result["unmet_conditions"]
    )


def test_vwap_only_recovery_without_higher_high_stays_watch(monkeypatch):
    inputs = _ready_input(current_price=100_400)
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 100_200)
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 100_100,
            "candidate_support": 100_100,
            "recent_resistance": 100_800,
            "higher_high": False,
            "higher_low": True,
            "higher_high_and_low": False,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["derived"]["vwap_reclaimed"] is True
    assert result["derived"]["recent_resistance_reclaimed"] is False
    assert result["derived"]["vwap_only_structure_confirmed"] is False
    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None


def test_recent_runup_guard_blocks_shifted_support_entry_near_rolling_high(
    monkeypatch,
):
    inputs = _ready_input(current_price=101_500)
    inputs["bars"] = _bars(
        datetime(2026, 8, 3, 9, 0, tzinfo=KST),
        [
            100_000,
            100_100,
            100_200,
            100_300,
            100_500,
            100_700,
            100_900,
            101_100,
            101_300,
            101_500,
        ],
    )
    inputs["bbo"] = {"best_bid": 101_400, "best_ask": 101_500, "age_sec": 0}
    structure = advisory._structure_features(inputs["bars"])
    monkeypatch.setattr(
        advisory,
        "_structure_features",
        lambda _bars: {
            **structure,
            "confirmed_support": 101_300,
            "candidate_support": 101_300,
            "recent_resistance": 101_400,
            "higher_high": True,
            "higher_low": True,
            "higher_high_and_low": True,
            "retest_held": True,
            "retest_rebound_confirmed": True,
            "support_confirmation": "retest_held",
        },
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "NO_CHASE"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert result["reasons"] == ["recent_runup_near_rolling_high"]
    assert result["derived"]["recent_runup_chase_guard"]["near_recent_high"] is True


def test_break_rearm_requires_two_distinct_completed_bars():
    raw = advisory.evaluate_advisory(**_ready_input())
    support = raw["derived"]["structural_support"]
    break_advisory = {
        **raw,
        "state": "AVOID",
        "raw_state": "AVOID",
        "invalidation": "confirmed_support_break",
        "derived": {
            **raw["derived"],
            "invalidation_confirmation": {
                **raw["derived"]["invalidation_confirmation"],
                "completed_close_break": True,
            },
        },
    }
    filter_ = advisory.AdvisoryBreakRearmFilter()
    break_bar = advisory.MinuteBar(
        "20260803090900",
        support,
        support,
        advisory.move_price_by_ticks(support, -1),
        advisory.move_price_by_ticks(support, -1),
        1_000,
    )
    first_reclaim = advisory.MinuteBar(
        "20260803091000", support, support + 100, support, support, 1_000
    )
    second_reclaim = advisory.MinuteBar(
        "20260803091100", support, support + 100, support, support, 1_000
    )

    broken = filter_.apply(break_advisory, latest_bar=break_bar)
    first = filter_.apply(raw, latest_bar=first_reclaim)
    duplicate = filter_.apply(raw, latest_bar=first_reclaim)
    second = filter_.apply(raw, latest_bar=second_reclaim)

    assert broken["continuity"]["support_break_rearm_required"] is True
    assert first["state"] == "WATCH"
    assert first["continuity"]["reclaim_bar_count"] == 1
    assert duplicate["continuity"]["reclaim_bar_count"] == 1
    assert second["raw_state"] == "ENTRY_READY"
    assert second["continuity"]["support_break_rearm_required"] is False
    assert "post_break_rearm_satisfied" in second["reasons"]


def test_declarative_invalidation_does_not_create_break_rearm_lock():
    raw = advisory.evaluate_advisory(**_ready_input())
    support = raw["derived"]["structural_support"]
    result = advisory.AdvisoryBreakRearmFilter().apply(
        {
            **raw,
            "state": "WATCH",
            "raw_state": "WATCH",
            "invalidation": "confirmed_support_break",
        },
        latest_bar=advisory.MinuteBar(
            "20260803090900", support, support, support, support, 1_000
        ),
    )

    assert result["state"] == "WATCH"
    assert result["continuity"]["support_break_rearm_required"] is False
    assert "post_break_rearm_pending" not in result["unmet_conditions"]


def test_break_rearm_restore_rejects_legacy_lock_without_confirmed_evidence():
    raw = advisory.evaluate_advisory(**_ready_input())
    support = raw["derived"]["structural_support"]
    filter_ = advisory.AdvisoryBreakRearmFilter()

    restored = filter_.restore(
        {
            **raw,
            "continuity": {
                "support_break_rearm_required": True,
                "locked_support": support,
                "break_kind": "confirmed_support_break",
                "break_bar_source_time": "20260803090900",
                "reclaim_bar_source_times": [],
            },
        }
    )

    assert restored is False
    assert filter_.snapshot()["support_break_rearm_required"] is False


def test_collector_restores_break_lock_beyond_display_freshness(tmp_path):
    raw = advisory.evaluate_advisory(**_ready_input())
    support = raw["derived"]["structural_support"]
    filter_ = advisory.AdvisoryBreakRearmFilter()
    break_advisory = {
        **raw,
        "state": "AVOID",
        "raw_state": "AVOID",
        "invalidation": "confirmed_support_break",
        "derived": {
            **raw["derived"],
            "invalidation_confirmation": {
                **raw["derived"]["invalidation_confirmation"],
                "completed_close_break": True,
            },
        },
    }
    persisted = filter_.apply(
        break_advisory,
        latest_bar=advisory.MinuteBar(
            "20260803090900", support, support, support - 100, support, 1_000
        ),
    )
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "schema_version": contract.SNAPSHOT_SCHEMA_VERSION,
                "status": "ok",
                "symbol": contract.SAMSUNG_CODE,
                "observed_at_kst": raw["observed_at"],
                "market_venue": "KRX",
                "market_cohort": "KRX",
                "quote_request_code": contract.SAMSUNG_CODE,
                "token_mode": "shared_cache_only",
                "advisory": persisted,
            }
        ),
        encoding="utf-8",
    )
    collector = advisory.SamsungWidgetCollector(
        snapshot_path=snapshot_path,
        observation_dir=tmp_path / "observations",
    )
    restart_time = datetime.fromisoformat(raw["observed_at"]) + timedelta(seconds=60)
    context = advisory.session_context(restart_time)

    collector._restore_promotion_state(restart_time, context)
    first_reclaim = collector.break_rearm_filter.apply(
        {**raw, "observed_at": restart_time.isoformat()},
        latest_bar=advisory.MinuteBar(
            "20260803091000", support, support + 100, support, support, 1_000
        ),
    )

    assert first_reclaim["state"] == "WATCH"
    assert first_reclaim["continuity"]["reclaim_bar_count"] == 1


def test_collector_failure_snapshot_preserves_break_rearm_lock(tmp_path):
    raw = advisory.evaluate_advisory(**_ready_input())
    support = raw["derived"]["structural_support"]
    snapshot_path = tmp_path / "snapshot.json"
    collector = advisory.SamsungWidgetCollector(
        snapshot_path=snapshot_path,
        observation_dir=tmp_path / "observations",
    )
    collector.break_rearm_filter.apply(
        {
            **raw,
            "state": "AVOID",
            "raw_state": "AVOID",
            "invalidation": "confirmed_support_break",
            "derived": {
                **raw["derived"],
                "invalidation_confirmation": {
                    **raw["derived"]["invalidation_confirmation"],
                    "completed_close_break": True,
                },
            },
        },
        latest_bar=advisory.MinuteBar(
            "20260803090900", support, support, support - 100, support, 1_000
        ),
    )
    failure_time = datetime.fromisoformat(raw["observed_at"]) + timedelta(seconds=10)
    collector.write_failure("temporary_transport_error", failure_time)

    restarted = advisory.SamsungWidgetCollector(
        snapshot_path=snapshot_path,
        observation_dir=tmp_path / "restarted-observations",
    )
    restart_time = failure_time + timedelta(seconds=60)
    restarted._restore_promotion_state(
        restart_time, advisory.session_context(restart_time)
    )
    first_reclaim = restarted.break_rearm_filter.apply(
        {**raw, "observed_at": restart_time.isoformat()},
        latest_bar=advisory.MinuteBar(
            "20260803091000", support, support + 100, support, support, 1_000
        ),
    )

    assert first_reclaim["state"] == "WATCH"
    assert first_reclaim["continuity"]["reclaim_bar_count"] == 1


def test_collector_failure_snapshot_preserves_recovery_episode(tmp_path):
    observed_at = datetime(2026, 8, 5, 10, 31, 6, tzinfo=KST)
    snapshot_path = tmp_path / "snapshot.json"
    collector = advisory.SamsungWidgetCollector(
        snapshot_path=snapshot_path,
        observation_dir=tmp_path / "observations",
    )
    collector.recovery_episode_filter.apply(
        _recovery_episode_advisory(
            observed_at, volume_confirmed=True, current_price=245_500
        ),
        current_price=245_500,
        bbo={"best_bid": 245_500, "best_ask": 246_000},
        latest_bar=advisory.MinuteBar(
            "20260805103000", 245_000, 246_000, 244_500, 245_750, 77_843
        ),
    )
    collector.write_failure("temporary_transport_error", observed_at)

    restarted = advisory.SamsungWidgetCollector(
        snapshot_path=snapshot_path,
        observation_dir=tmp_path / "restarted-observations",
    )
    restarted._restore_promotion_state(
        observed_at + timedelta(seconds=30),
        advisory.session_context(observed_at),
    )

    continuity = restarted.recovery_episode_filter.snapshot()
    assert continuity["armed"] is True
    assert continuity["support"] == 244_000
    assert continuity["resistance"] == 246_000


def test_quote_bbo_incoherence_blocks_advisory():
    inputs = _ready_input()
    inputs["bbo"] = {"best_bid": 99_000, "best_ask": 99_100, "age_sec": 0}

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "DATA_WAIT"
    assert "quote_bbo_inconsistent" in result["source_quality"]["issues"]


def test_exit_source_quality_does_not_require_entry_only_previous_day_ohlc():
    inputs = _ready_input()
    exit_quality = advisory._source_quality(
        observed_at=inputs["observed_at"],
        context=inputs["context"],
        bars=inputs["bars"],
        bbo=inputs["bbo"],
        previous_day=None,
        quote_age_sec=0.0,
        current_price=inputs["current_price"],
    )
    entry_quality = advisory._source_quality(
        observed_at=inputs["observed_at"],
        context=inputs["context"],
        bars=inputs["bars"],
        bbo=inputs["bbo"],
        previous_day={},
        quote_age_sec=0.0,
        current_price=inputs["current_price"],
    )

    assert exit_quality["status"] == "PASS"
    assert exit_quality["required_sources"] == ["quote", "bbo", "completed_1m"]
    assert entry_quality["status"] == "BLOCKED"
    assert "previous_day_ohlc_missing" in entry_quality["issues"]


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
    assert metadata["rising_volume_sample_count"] == 7
    assert metadata["falling_volume_sample_count"] == 0
    assert metadata["volume_minimum_composition_met"] is False
    assert metadata["opening_bar_excluded"] is True


def test_opening_auction_volume_is_normalized_for_early_recovery():
    start = datetime(2026, 8, 10, 9, 0, tzinfo=KST)
    rows = [
        (236_000, 233_000, 626_341),
        (233_500, 231_500, 142_224),
        (231_500, 232_000, 145_583),
        (232_000, 233_000, 101_596),
        (233_000, 232_250, 56_205),
        (232_500, 234_000, 54_712),
        (234_000, 235_500, 78_172),
    ]
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            open_price,
            max(open_price, close),
            min(open_price, close),
            close,
            volume,
        )
        for index, (open_price, close, volume) in enumerate(rows)
    ]

    passed, metadata = advisory._volume_confirmation(bars)

    assert passed is True
    assert metadata["opening_bar_excluded"] is True
    assert metadata["opening_bar_source_time"] == "20260810090000"
    assert metadata["opening_bar_volume"] == 626_341
    assert metadata["rebound_to_decline_volume_ratio"] >= 0.9
    assert metadata["required_rebound_to_decline_volume_ratio"] == 0.9


def test_non_opening_volume_keeps_full_rebound_ratio_requirement():
    start = datetime(2026, 8, 10, 9, 1, tzinfo=KST)
    rows = [
        (100_000, 100_100, 90),
        (100_100, 100_000, 100),
        (100_000, 100_100, 100),
        (100_100, 100_000, 100),
        (100_000, 100_100, 95),
    ]
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            open_price,
            max(open_price, close),
            min(open_price, close),
            close,
            volume,
        )
        for index, (open_price, close, volume) in enumerate(rows)
    ]

    passed, metadata = advisory._volume_confirmation(bars)

    assert passed is False
    assert metadata["opening_bar_excluded"] is False
    assert metadata["rebound_to_decline_volume_ratio"] == 0.95
    assert metadata["required_rebound_to_decline_volume_ratio"] == 1.0


def test_candidate_support_vwap_recovery_requires_favorable_reward_risk():
    start = datetime(2026, 8, 10, 9, 0, tzinfo=KST)
    rows = [
        (236_000, 236_500, 233_000, 233_000, 626_341),
        (233_500, 233_500, 231_500, 231_500, 142_224),
        (231_500, 232_500, 231_000, 232_000, 145_583),
        (232_000, 233_000, 231_500, 233_000, 101_596),
        (233_000, 233_000, 232_000, 232_250, 56_205),
        (232_500, 234_000, 232_000, 234_000, 54_712),
    ]
    bars = [
        advisory.MinuteBar(
            (start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
            open_price,
            high,
            low,
            close,
            volume,
        )
        for index, (open_price, high, low, close, volume) in enumerate(rows)
    ]
    observed_at = datetime(2026, 8, 10, 9, 6, 4, tzinfo=KST)
    inputs = {
        "observed_at": observed_at,
        "context": advisory.session_context(observed_at),
        "current_price": 234_000,
        "bars": bars,
        "bbo": {"best_bid": 233_500, "best_ask": 234_000, "age_sec": 0},
        "previous_day": {
            "date": "20260807",
            "open": 235_000,
            "high": 239_500,
            "low": 229_000,
            "close": 231_000,
        },
        "relative": {
            "samsung_change_pct": 1.0,
            "sk_hynix_change_pct": 0.8,
            "kospi_change_pct": 0.5,
        },
        "external_points": _external(),
        "flow": {
            "status": "PARTIAL",
            "live_for_current_session": True,
            "foreign_nonworsening": False,
            "program_nonworsening": True,
        },
        "premarket": {
            "date": "2026-08-10",
            "vwap": 235_500,
        },
    }

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert result["trigger"] is None
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert result["derived"]["candidate_support"] == 231_000
    assert result["derived"]["candidate_support_age_bars"] == 3
    assert (
        result["derived"]["candidate_support_caution"]["ready_promotion_forbidden"]
        is True
    )
    reward_risk = result["derived"]["entry_reward_risk_guard"]
    assert reward_risk["entry_price"] == 234_000
    assert reward_risk["target_price"] == 236_500
    assert reward_risk["invalidation_price"] == 230_000
    assert reward_risk["reward_risk_ratio"] == 0.625
    assert reward_risk["passed"] is False
    assert "entry_reward_risk_below_floor" in result["unmet_conditions"]
    assert "premarket_vwap_not_recovered" in result["unmet_conditions"]
    assert contract.advisory_contract_is_valid(
        result,
        snapshot_observed_at=observed_at,
        context=inputs["context"],
        evaluated_at=observed_at,
    )

    promotion = advisory.AdvisoryPromotionFilter()
    assert promotion.apply(result)["state"] == "WATCH"
    assert promotion.apply(result)["state"] == "WATCH"


def test_candidate_support_recovery_keeps_two_tick_no_chase_guard(monkeypatch):
    inputs = _ready_input(current_price=101_500)
    inputs["bbo"] = {"best_bid": 101_400, "best_ask": 101_500, "age_sec": 0}
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 100_000)
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
            "candidate_support": 100_000,
            "support_confirmation": "unconfirmed",
            "confirmed_support_age_bars": None,
            "candidate_support_age_bars": 3,
            "recent_resistance": 102_000,
        },
    )
    monkeypatch.setattr(
        advisory,
        "_volume_confirmation",
        lambda _bars: (
            False,
            {
                "rising_volume_sample_count": 3,
                "falling_volume_sample_count": 1,
                "zero_volume_ratio": 0.0,
                "volume_minimum_composition_met": True,
                "retest_volume_contracted": None,
            },
        ),
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "NO_CHASE"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert result["derived"]["candidate_support_caution"]["eligible"] is True
    assert result["derived"]["latent_next_blockers"] == [
        "price_above_dynamic_two_tick_chase_limit"
    ]


def test_candidate_support_recovery_preserves_recent_trade_reversal_veto(monkeypatch):
    inputs = _ready_input(current_price=100_400)
    inputs["recent_trade_negative_veto"] = True
    monkeypatch.setattr(advisory, "_session_vwap", lambda _bars: 100_000)
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
            "candidate_support": 100_000,
            "support_confirmation": "unconfirmed",
            "confirmed_support_age_bars": None,
            "candidate_support_age_bars": 3,
            "recent_resistance": 102_000,
        },
    )
    monkeypatch.setattr(
        advisory,
        "_volume_confirmation",
        lambda _bars: (
            False,
            {
                "rising_volume_sample_count": 3,
                "falling_volume_sample_count": 1,
                "zero_volume_ratio": 0.0,
                "volume_minimum_composition_met": True,
                "retest_volume_contracted": None,
            },
        ),
    )

    result = advisory.evaluate_advisory(**inputs)

    assert result["state"] == "WATCH"
    assert "recent_rest_prints_descending" in result["unmet_conditions"]
    assert result["derived"]["candidate_support_caution"]["safety_blockers"] == [
        "recent_rest_prints_descending"
    ]


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


def test_collector_isolates_entry_notification_failure(tmp_path, capsys):
    class BrokenNotifier:
        def observe(self, payload, observed_at):
            raise OSError("telegram state unavailable")

    collector = advisory.SamsungWidgetCollector(
        snapshot_path=tmp_path / "snapshot.json",
        observation_dir=tmp_path / "observations",
        entry_notifier=BrokenNotifier(),
    )

    status = collector._observe_entry_notification(
        {"advisory": {"state": "ENTRY_CAUTION"}},
        datetime(2026, 8, 4, 14, 33, tzinfo=KST),
    )

    assert status == "notifier_error_isolated"
    assert "OSError" in capsys.readouterr().out


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


def test_snapshot_contract_rejects_invalid_intraday_regime_label():
    now = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    context = contract.session_context(now)
    raw = advisory.evaluate_advisory(**_ready_input())
    raw["intraday_regime"]["state"] = "FUTURE_UP"

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


def test_exit_state_transition_does_not_create_a_new_entry_signal_row(tmp_path):
    recorder = advisory.ObservationRecorder(tmp_path)
    start = datetime(2026, 8, 3, 9, 10, 1, tzinfo=KST)

    def payload(exit_state):
        return {
            "current_price": 100_000,
            "market_venue": "KRX",
            "market_session": "KRX_REGULAR",
            "advisory": {"state": "ENTRY_CAUTION", "session": "KRX_REGULAR"},
            "exit_advisory": {"state": exit_state},
            "observation": {"latest_completed_bar": None},
        }

    recorder.record(payload("EXIT_WATCH"), start)
    recorder.record(payload("EXIT_CAUTION"), start + timedelta(seconds=10))
    rows = [
        json.loads(line)
        for line in (tmp_path / "samsung_widget_advisory_20260803.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert rows[0]["observation_kind"] == "state_transition"
    assert rows[1]["observation_kind"] == "exit_state_transition"
    assert rows[1]["previous_advisory_state"] == "ENTRY_CAUTION"
    assert rows[1]["previous_exit_advisory_state"] == "EXIT_WATCH"


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


def test_read_only_client_uses_registered_token_handoff(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json")
    )

    class Response:
        status_code = 200

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"return_code": 0, "cur_prc": "10000"}

    class Session:
        def __init__(self):
            self.headers = []

        def post(self, *args, **kwargs):
            self.headers.append(dict(kwargs.get("headers") or {}))
            return Response()

    advisory.kiwoom_utils.register_kiwoom_token_replacement(
        "STARTUP_TOKEN", "FRESH_TOKEN", source="test"
    )
    session = Session()
    client = advisory.KiwoomReadOnlyClient("STARTUP_TOKEN", session=session)

    result = client.post("/api/dostk/stkinfo", "ka10001", {"stk_cd": "005930"})

    assert result["cur_prc"] == "10000"
    assert client.token == "FRESH_TOKEN"
    assert session.headers[0]["authorization"] == "Bearer FRESH_TOKEN"


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
