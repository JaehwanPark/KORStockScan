"""Read-only Samsung Electronics intraday advisory collector.

This module is deliberately isolated from the trading runtime.  It consumes
only the existing shared Kiwoom token cache, never issues or refreshes a token,
and has no account, order, quantity, provider-route, or bot-control authority.
The generated state is for the Windows widget only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, time as datetime_time, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import holidays
import pandas as pd
import requests
import yfinance as yf

from src.engine.monitoring.samsung_widget_contract import (
    ADVISORY_AUTHORITY,
    DEFAULT_OBSERVATION_DIR,
    DEFAULT_SNAPSHOT_PATH,
    KRX_END,
    KRX_START,
    KST,
    INTRADAY_REGIME_METRIC_CONTRACT,
    METRIC_CONTRACT,
    NXT_AFTERMARKET_END,
    NXT_PREMARKET_END,
    NXT_PREMARKET_START,
    PREMARKET_AUXILIARY_END,
    SAMSUNG_CODE,
    SAMSUNG_NAME,
    SK_HYNIX_CODE,
    SNAPSHOT_SCHEMA_VERSION,
    SessionContext,
    advisory_contract_is_valid,
    as_kst as _as_kst,
    legacy_market_session,
    load_snapshot,
    previous_krx_trading_date,
    session_context,
    snapshot_observed_at,
    snapshot_is_fresh,
)
from src.engine.monitoring.widget_advisory_calibration_policy import (
    WidgetCalibrationPolicyLoader,
)
from src.engine.monitoring.samsung_widget_entry_notify import (
    SamsungWidgetEntryTelegramNotifier,
)
from src.engine.sniper_config import CONF
from src.trading.order.tick_utils import (
    clamp_price_to_tick,
    get_tick_size,
    move_price_by_ticks,
    move_price_up_by_bps,
)
from src.utils import kiwoom_utils

NEW_YORK = ZoneInfo("America/New_York")
NYSE_HOLIDAYS = holidays.NYSE()
EXTERNAL_STALE_SEC = 300
FLOW_STALE_SEC = 300
COLLECTOR_REQUESTS_PER_MINUTE = 36

TREND_R2_MIN = 0.40
TREND_DIRECTIONAL_CONSISTENCY_MIN = 0.60
TREND_VOLATILITY_LOOKBACK_BARS = 12
TREND_VOLATILITY_MULTIPLIER = 1.25
TREND_TICK_MULTIPLIERS = {
    "NXT_PREMARKET": {1: 2, 3: 3, 5: 4},
    "KRX_REGULAR": {1: 1, 3: 2, 5: 3},
    "NXT_AFTERMARKET": {1: 2, 3: 3, 5: 4},
}
RELATIVE_UNDERPERFORMANCE_LIMIT_PCT = 0.50
TACTICAL_CHASE_LIMIT_PCT = 0.30
STANDARD_VOLUME_REBOUND_RATIO_MIN = 1.00
OPENING_VOLUME_REBOUND_RATIO_MIN = 0.90
CANDIDATE_SUPPORT_CAUTION_MIN_HOLD_BARS = 3
CANDIDATE_SUPPORT_CAUTION_MAX_HOLD_BARS = 5
CANDIDATE_SUPPORT_CAUTION_MAX_RECOVERY_PCT = 1.50
RECENT_RUNUP_LOOKBACK_BARS = 20
RECENT_RUNUP_NO_CHASE_PCT = 0.80
RECENT_RUNUP_NO_CHASE_TICKS = 4
EARLY_REVERSAL_LOW_HOLD_MIN_BARS = 3
EARLY_REVERSAL_LOW_HOLD_MAX_BARS = 8
EARLY_REVERSAL_PULLBACK_MIN_PCT = 0.60
EARLY_REVERSAL_PULLBACK_TICKS = 3
EXIT_PEAK_LOOKBACK_BARS = 20
EXIT_SUPPORT_LOOKBACK_BARS = 5
EXIT_VOLATILITY_LOOKBACK_BARS = 10
EXIT_NO_NEW_LOW_CANCEL_BARS = 5
EXIT_PENDING_MAX_BARS = 3
EXIT_LOCAL_PEAK_PENDING_MAX_BARS = 8
EXIT_REARM_MAX_BARS = 20
INTRADAY_REGIME_MIN_BARS = 15
INTRADAY_REGIME_LOOKBACK_BARS = 30
INTRADAY_REGIME_MIN_DECLINE_TICKS = 3
ENTRY_TARGET_BPS = 100
ENTRY_MIN_REWARD_RISK_RATIO = 1.0

EXIT_REVERSAL_METRIC_CONTRACT = {
    "metric_role": "samsung_exit_contrarian_reversal_observation",
    "decision_authority": "widget_advisory_observation_only",
    "window_policy": "same_session_completed_1m_after_exit_ready",
    "sample_floor": "one_completed_bar_after_exit_ready",
    "primary_decision_metric": "reversal_observation_state",
    "source_quality_gate": "exit_advisory_pass_and_contiguous_completed_1m",
    "forbidden_uses": [
        "direct_buy_from_exit_ready",
        "automatic_order_submission",
        "same_day_threshold_mutation",
        "forced_position_exit_override",
    ],
}

EXTERNAL_THRESHOLDS = {
    "NQ": -0.40,
    "MU": -0.80,
    "USDKRW": 0.25,
}

READ_ONLY_KIWOOM_REQUESTS = frozenset(
    {
        ("/api/dostk/stkinfo", "ka10001"),
        ("/api/dostk/stkinfo", "ka10003"),
        ("/api/dostk/mrkcond", "ka10004"),
        ("/api/dostk/chart", "ka10064"),
        ("/api/dostk/chart", "ka10080"),
        ("/api/dostk/chart", "ka10081"),
        ("/api/dostk/chart", "ka20005"),
        ("/api/dostk/sect", "ka20001"),
        ("/api/dostk/mrkcond", "ka90008"),
    }
)


def _now_kst() -> datetime:
    return datetime.now(KST)


def _positive_int(value: object) -> int | None:
    text = str(value or "").replace(",", "").replace("+", "").strip()
    if not text:
        return None
    try:
        parsed = abs(int(float(text)))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _signed_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    if text.startswith("--"):
        text = "-" + text[2:]
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _signed_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    if text.startswith("--"):
        text = "-" + text[2:]
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class MinuteBar:
    source_time: str
    open: int
    high: int
    low: int
    close: int
    volume: int


def completed_session_bars(
    rows: object,
    *,
    observed_at: datetime,
    session_start: datetime_time,
    session_end: datetime_time | None = None,
    limit: int = 120,
) -> list[MinuteBar]:
    """Normalize current-session completed stock/index one-minute bars."""
    if not isinstance(rows, list):
        return []
    now = _as_kst(observed_at)
    current_minute = now.strftime("%Y%m%d%H%M")
    today = now.strftime("%Y%m%d")
    session_floor = f"{today}{session_start.strftime('%H%M')}"
    session_ceiling = (
        f"{today}{session_end.strftime('%H%M')}" if session_end is not None else None
    )
    by_time: dict[str, MinuteBar] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_time = str(row.get("cntr_tm") or "").strip()
        if (
            len(raw_time) < 14
            or not raw_time[:14].isdigit()
            or not raw_time.startswith(today)
            or raw_time[:12] < session_floor
            or (session_ceiling is not None and raw_time[:12] >= session_ceiling)
            or raw_time[:12] >= current_minute
        ):
            continue
        close = _positive_int(row.get("cur_prc"))
        open_price = _positive_int(row.get("open_pric")) or close
        high = _positive_int(row.get("high_pric")) or close
        low = _positive_int(row.get("low_pric")) or close
        volume = _positive_int(row.get("trde_qty")) or 0
        if not all((close, open_price, high, low)):
            continue
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        by_time[raw_time[:14]] = MinuteBar(
            raw_time[:14], open_price, high, low, close, volume
        )
    return sorted(by_time.values(), key=lambda bar: bar.source_time)[-max(1, limit) :]


def _contiguous_window(bars: list[MinuteBar], count: int) -> list[MinuteBar]:
    window = bars[-count:]
    if len(window) < count:
        return []
    try:
        timestamps = [
            datetime.strptime(bar.source_time, "%Y%m%d%H%M%S") for bar in window
        ]
    except ValueError:
        return []
    if any(
        int((current - previous).total_seconds()) != 60
        for previous, current in zip(timestamps, timestamps[1:])
    ):
        return []
    return window


def _trend_tick_multiplier(session_name: str, horizon: int) -> int:
    session_multipliers = TREND_TICK_MULTIPLIERS.get(
        session_name, TREND_TICK_MULTIPLIERS["KRX_REGULAR"]
    )
    return session_multipliers[horizon]


def _linear_trend_metrics(closes: list[int]) -> tuple[float, float]:
    """Return least-squares slope and R-squared for completed closes."""
    count = len(closes)
    if count < 2:
        return 0.0, 0.0
    x_mean = (count - 1) / 2
    y_mean = sum(closes) / count
    x_variance = sum((index - x_mean) ** 2 for index in range(count))
    if x_variance <= 0:
        return 0.0, 0.0
    slope = (
        sum((index - x_mean) * (price - y_mean) for index, price in enumerate(closes))
        / x_variance
    )
    total_variance = sum((price - y_mean) ** 2 for price in closes)
    if total_variance <= 0:
        return slope, 0.0
    residual = sum(
        (price - (y_mean + slope * (index - x_mean))) ** 2
        for index, price in enumerate(closes)
    )
    return slope, max(0.0, min(1.0, 1.0 - residual / total_variance))


def analyze_trends(
    bars: list[MinuteBar], *, session_name: str = "KRX_REGULAR"
) -> dict[str, dict[str, Any]]:
    """Describe confirmed-bar direction without claiming future prediction.

    The neutral band is at least one session/horizon-specific tick allowance and
    widens with recent realized one-minute volatility.  Net direction alone is
    insufficient: slope, fit, and directional consistency must agree.
    """
    recent_bars = bars[-TREND_VOLATILITY_LOOKBACK_BARS:]
    recent_changes = [
        abs(current.close - previous.close)
        for previous, current in zip(recent_bars, recent_bars[1:])
    ]
    recent_median_abs_change = float(median(recent_changes)) if recent_changes else 0.0
    result: dict[str, dict[str, Any]] = {}
    for horizon in (1, 3, 5):
        key = f"{horizon}m"
        window = _contiguous_window(bars, horizon + 1)
        if not window:
            result[key] = {
                "state": "unavailable",
                "horizon_minutes": horizon,
                "basis": "completed_contiguous_1m_closes",
            }
            continue
        closes = [bar.close for bar in window]
        net_change = closes[-1] - closes[0]
        tick_size = get_tick_size(closes[-1])
        tick_multiplier = _trend_tick_multiplier(session_name, horizon)
        raw_band = max(
            tick_size * tick_multiplier,
            recent_median_abs_change * TREND_VOLATILITY_MULTIPLIER,
        )
        flat_band = max(tick_size, int(math.ceil(raw_band / tick_size) * tick_size))
        slope, regression_r2 = _linear_trend_metrics(closes)
        deltas = [current - previous for previous, current in zip(closes, closes[1:])]
        direction = 1 if net_change > 0 else -1 if net_change < 0 else 0
        directional_consistency = (
            sum(1 for change in deltas if change * direction > 0) / len(deltas)
            if direction and deltas
            else 0.0
        )
        minimum_abs_slope = flat_band / max(1, horizon) * 0.5
        common_confirmation = bool(
            regression_r2 >= TREND_R2_MIN
            and directional_consistency >= TREND_DIRECTIONAL_CONSISTENCY_MIN
        )
        if net_change > flat_band and slope > minimum_abs_slope and common_confirmation:
            state = "up"
        elif (
            net_change < -flat_band
            and slope < -minimum_abs_slope
            and common_confirmation
        ):
            state = "down"
        else:
            state = "flat"
        result[key] = {
            "state": state,
            "horizon_minutes": horizon,
            "basis": "completed_contiguous_1m_closes",
            "session": session_name,
            "tick_size": tick_size,
            "tick_multiplier": tick_multiplier,
            "flat_band_price": flat_band,
            "recent_median_abs_change": round(recent_median_abs_change, 4),
            "net_change": net_change,
            "net_change_bps": round((net_change / closes[0]) * 10_000, 4),
            "slope_price_per_minute": round(slope, 4),
            "minimum_abs_slope": round(minimum_abs_slope, 4),
            "regression_r2": round(regression_r2, 4),
            "directional_consistency": round(directional_consistency, 4),
        }
    return result


def classify_trends(
    bars: list[MinuteBar], *, session_name: str = "KRX_REGULAR"
) -> dict[str, str]:
    return {
        key: str(detail.get("state") or "unavailable")
        for key, detail in analyze_trends(bars, session_name=session_name).items()
    }


def _trend_assessment(trends: dict[str, str]) -> dict[str, Any]:
    medium = trends.get("3m", "unavailable")
    slow = trends.get("5m", "unavailable")
    if "down" in {medium, slow}:
        state = "TREND_DOWN"
    elif "unavailable" in {medium, slow}:
        state = "TREND_DATA_WAIT"
    elif medium == slow == "up":
        state = "TREND_UP"
    elif medium == slow == "flat":
        state = "TREND_STABLE"
    else:
        state = "TREND_MIXED"
    return {
        "state": state,
        "basis": "confirmed_completed_3m_5m_direction",
        "future_prediction": False,
        "setup_ready_is_distinct": True,
    }


def analyze_intraday_regime(bars: list[MinuteBar]) -> dict[str, Any]:
    """Classify the completed-bar 15-30 minute structure.

    The short 3/5-minute trend intentionally remains responsive.  This
    companion view prevents a locally flat pause inside a persistent lower-
    high/lower-low move from being interpreted as a completed reversal.
    """
    if len(bars) < INTRADAY_REGIME_MIN_BARS:
        return {
            "state": "unavailable",
            "basis": "completed_contiguous_15_to_30m_structure",
            "completed_bar_count": len(bars),
            "minimum_bar_count": INTRADAY_REGIME_MIN_BARS,
            "future_prediction": False,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "metric_contract": INTRADAY_REGIME_METRIC_CONTRACT,
        }
    count = min(len(bars), INTRADAY_REGIME_LOOKBACK_BARS)
    window = _contiguous_window(bars, count)
    if not window:
        return {
            "state": "unavailable",
            "basis": "completed_contiguous_15_to_30m_structure",
            "completed_bar_count": count,
            "minimum_bar_count": INTRADAY_REGIME_MIN_BARS,
            "reason": "non_contiguous_completed_bars",
            "future_prediction": False,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "metric_contract": INTRADAY_REGIME_METRIC_CONTRACT,
        }
    segment_size = max(5, len(window) // 3)
    earlier = window[:segment_size]
    recent = window[-segment_size:]
    earlier_high = max(bar.high for bar in earlier)
    earlier_low = min(bar.low for bar in earlier)
    recent_high = max(bar.high for bar in recent)
    recent_low = min(bar.low for bar in recent)
    tick_size = get_tick_size(window[-1].close)
    lower_high = recent_high <= move_price_by_ticks(earlier_high, -1)
    lower_low = recent_low <= move_price_by_ticks(earlier_low, -1)
    closes = [bar.close for bar in window]
    slope, regression_r2 = _linear_trend_metrics(closes)
    net_change = closes[-1] - closes[0]
    decline_floor = tick_size * INTRADAY_REGIME_MIN_DECLINE_TICKS
    persistent_lower_structure = lower_high and lower_low
    broad_decline = bool(
        net_change <= -decline_floor and slope < 0 and (lower_high or lower_low)
    )
    down = bool((persistent_lower_structure and slope < 0) or broad_decline)
    return {
        "state": "down" if down else "not_down",
        "basis": "completed_contiguous_15_to_30m_structure",
        "completed_bar_count": len(window),
        "segment_bar_count": segment_size,
        "earlier_high": earlier_high,
        "earlier_low": earlier_low,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "lower_high": lower_high,
        "lower_low": lower_low,
        "persistent_lower_structure": persistent_lower_structure,
        "broad_decline": broad_decline,
        "net_change": net_change,
        "net_change_bps": round((net_change / closes[0]) * 10_000, 4),
        "slope_price_per_minute": round(slope, 4),
        "regression_r2": round(regression_r2, 4),
        "decline_floor_price": decline_floor,
        "tick_size": tick_size,
        "future_prediction": False,
        "authority": ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "metric_contract": INTRADAY_REGIME_METRIC_CONTRACT,
    }


def _session_vwap(bars: list[MinuteBar]) -> int | None:
    typical_prices = [(bar.high + bar.low + bar.close) / 3 for bar in bars]
    weighted_volume = sum(bar.volume for bar in bars if bar.volume > 0)
    if weighted_volume > 0:
        value = sum(
            typical_price * bar.volume
            for bar, typical_price in zip(bars, typical_prices)
            if bar.volume > 0
        )
        return int(round(value / weighted_volume))
    if typical_prices:
        return int(round(sum(typical_prices) / len(typical_prices)))
    return None


def _premarket_context(bars: list[MinuteBar], observed_at: datetime) -> dict[str, Any]:
    if not bars:
        return {}
    return {
        "status": "OBSERVED",
        "session": "NXT_PREMARKET",
        "market_venue": "NXT",
        "market_cohort": "PREMARKET_KRX_LIKE",
        "date": _as_kst(observed_at).date().isoformat(),
        "observed_at": _as_kst(observed_at).isoformat(),
        "vwap": _session_vwap(bars),
        "high": max(bar.high for bar in bars),
        "low": min(bar.low for bar in bars),
        "last_close": bars[-1].close,
        "completed_bar_count": len(bars),
        "minute_trends": classify_trends(bars, session_name="NXT_PREMARKET"),
    }


def _session_anchor(bars: list[MinuteBar], observed_at: datetime) -> dict[str, Any]:
    if not bars:
        return {}
    return {
        "status": "OBSERVED",
        "date": _as_kst(observed_at).date().isoformat(),
        "observed_at": _as_kst(observed_at).isoformat(),
        "open": bars[0].open,
        "high": max(bar.high for bar in bars),
        "low": min(bar.low for bar in bars),
        "close": bars[-1].close,
        "vwap": _session_vwap(bars),
        "completed_bar_count": len(bars),
    }


def _pivot_lows(bars: list[MinuteBar]) -> list[tuple[int, int]]:
    pivots: list[tuple[int, int]] = []
    for index in range(1, len(bars) - 1):
        current = bars[index].low
        if current <= bars[index - 1].low and current <= bars[index + 1].low:
            pivots.append((index, current))
    return pivots


def _structure_features(bars: list[MinuteBar]) -> dict[str, Any]:
    recent = bars[-12:]
    pivots = _pivot_lows(recent)
    higher_low = False
    higher_high = False
    higher_high_and_low = False
    retest_held = False
    retest_rebound_confirmed = False
    confirmed_support: int | None = None
    candidate_support: int | None = None
    support_confirmation = "unconfirmed"
    confirmed_support_age_bars: int | None = None
    candidate_support_age_bars: int | None = None
    latest_structure_low: int | None = None
    if len(recent) >= 6:
        prior_window = recent[-6:-3]
        latest_window = recent[-3:]
        prior_low = min(bar.low for bar in prior_window)
        latest_low = min(bar.low for bar in latest_window)
        latest_structure_low = latest_low
        prior_high = max(bar.high for bar in prior_window)
        latest_high = max(bar.high for bar in latest_window)
        higher_low = latest_low > prior_low
        higher_high = latest_high > prior_high
        higher_high_and_low = higher_low and higher_high
    if len(pivots) >= 2:
        first_index, first_low = pivots[-2]
        second_index, second_low = pivots[-1]
        candidate_support = second_low
        tolerance = max(get_tick_size(second_low), round(second_low * 0.001))
        between_tests = recent[first_index + 1 : second_index]
        retest_rebound_confirmed = bool(
            between_tests
            and max(bar.high for bar in between_tests)
            >= move_price_by_ticks(first_low, 1)
        )
        retest_held = (
            second_index >= first_index + 2
            and retest_rebound_confirmed
            and second_low >= first_low - tolerance
            and recent[-1].close > second_low
        )
        if retest_held:
            confirmed_support = second_low
            support_confirmation = "retest_held"
            confirmed_support_age_bars = len(recent) - 1 - second_index
    elif pivots:
        candidate_support = pivots[-1][1]

    if confirmed_support is None and higher_high_and_low and latest_structure_low:
        confirmed_support = latest_structure_low
        support_confirmation = "higher_high_and_low"
        latest_low_index = max(
            index for index, bar in enumerate(recent) if bar.low == latest_structure_low
        )
        confirmed_support_age_bars = len(recent) - 1 - latest_low_index
    if candidate_support is None:
        candidate_support = latest_structure_low
    if candidate_support is not None:
        candidate_support_index = max(
            index for index, bar in enumerate(recent) if bar.low == candidate_support
        )
        candidate_support_age_bars = len(recent) - 1 - candidate_support_index

    resistance_rows = recent[:-2] if len(recent) >= 5 else recent[:-1]
    recent_resistance = (
        max(bar.high for bar in resistance_rows) if resistance_rows else None
    )
    return {
        "higher_low": higher_low,
        "higher_high": higher_high,
        "higher_high_and_low": higher_high_and_low,
        "retest_held": retest_held,
        "retest_rebound_confirmed": retest_rebound_confirmed,
        "confirmed_support": confirmed_support,
        "candidate_support": candidate_support,
        "support_confirmation": support_confirmation,
        "confirmed_support_age_bars": confirmed_support_age_bars,
        "candidate_support_age_bars": candidate_support_age_bars,
        "recent_resistance": recent_resistance,
    }


def _volume_confirmation(
    bars: list[MinuteBar],
) -> tuple[bool, dict[str, Any]]:
    recent = bars[-8:]
    opening_bar_excluded = bool(recent and recent[0].source_time.endswith("090000"))
    comparison = recent[1:] if opening_bar_excluded else recent
    rising = [
        bar.volume for bar in comparison if bar.close > bar.open and bar.volume > 0
    ]
    falling = [
        bar.volume for bar in comparison if bar.close < bar.open and bar.volume > 0
    ]
    rising_avg = sum(rising) / len(rising) if rising else None
    falling_avg = sum(falling) / len(falling) if falling else None
    required_volume_ratio = (
        OPENING_VOLUME_REBOUND_RATIO_MIN
        if opening_bar_excluded
        else STANDARD_VOLUME_REBOUND_RATIO_MIN
    )
    zero_volume_count = sum(bar.volume <= 0 for bar in recent)
    zero_volume_ratio = zero_volume_count / len(recent) if recent else 1.0
    minimum_composition_met = (
        len(rising) >= 2 and len(falling) >= 1 and zero_volume_ratio <= 0.25
    )
    rebound_confirmed = bool(
        minimum_composition_met
        and rising_avg is not None
        and falling_avg is not None
        and rising_avg >= falling_avg * required_volume_ratio
    )
    pivots = _pivot_lows(recent)
    first_test_volume = None
    retest_volume = None
    retest_volume_contracted = None
    if len(pivots) >= 2:
        first_index, _first_low = pivots[-2]
        second_index, _second_low = pivots[-1]
        # Adjacent falling lows are one impulse, not two independent tests.
        # Keep volume retest semantics aligned with ``_structure_features``.
        between_tests = recent[first_index + 1 : second_index]
        if second_index >= first_index + 2 and between_tests:
            first_test_volume = recent[first_index].volume
            retest_volume = recent[second_index].volume
            if first_test_volume > 0 and retest_volume > 0:
                retest_volume_contracted = retest_volume <= first_test_volume
    passed = rebound_confirmed and retest_volume_contracted is not False
    return passed, {
        "rebound_avg_volume": round(rising_avg, 2) if rising_avg is not None else None,
        "decline_avg_volume": (
            round(falling_avg, 2) if falling_avg is not None else None
        ),
        "first_test_volume": first_test_volume,
        "retest_volume": retest_volume,
        "retest_volume_contracted": retest_volume_contracted,
        "rising_volume_sample_count": len(rising),
        "falling_volume_sample_count": len(falling),
        "zero_volume_count": zero_volume_count,
        "zero_volume_ratio": round(zero_volume_ratio, 4),
        "volume_minimum_composition_met": minimum_composition_met,
        "opening_bar_excluded": opening_bar_excluded,
        "opening_bar_source_time": (
            recent[0].source_time if opening_bar_excluded else None
        ),
        "opening_bar_volume": recent[0].volume if opening_bar_excluded else None,
        "rebound_to_decline_volume_ratio": (
            round(rising_avg / falling_avg, 4)
            if rising_avg is not None and falling_avg
            else None
        ),
        "required_rebound_to_decline_volume_ratio": required_volume_ratio,
    }


def _absorption_recovery_confirmation(
    *,
    volume_meta: dict[str, Any],
    structure: dict[str, Any],
    completed_close: int,
    vwap: int | None,
    recent_resistance: int | None,
    reclaim_ok: bool,
    trends_ok: bool,
) -> bool:
    """Recognize a high-volume retest that was absorbed and fully reclaimed."""
    return bool(
        structure.get("retest_held") is True
        and volume_meta.get("retest_volume_contracted") is False
        and int(volume_meta.get("rising_volume_sample_count") or 0) >= 3
        and int(volume_meta.get("falling_volume_sample_count") or 0) >= 1
        and float(volume_meta.get("zero_volume_ratio") or 0.0) <= 0.25
        and reclaim_ok
        and trends_ok
        and isinstance(vwap, int)
        and completed_close >= vwap
        and isinstance(recent_resistance, int)
        and completed_close >= recent_resistance
    )


@dataclass(frozen=True)
class ExternalPoint:
    key: str
    ticker: str
    value: float | None
    change_15m_pct: float | None
    observed_at: str | None
    received_at: str
    age_sec: float | None
    provider: str
    quality: str
    market_state: str
    reason: str | None = None


class ExternalMarketProvider(Protocol):
    def fetch(self, observed_at: datetime) -> dict[str, ExternalPoint]: ...


def _mu_extended_market_open(observed_at: datetime) -> bool:
    local = _as_kst(observed_at).astimezone(NEW_YORK)
    if local.weekday() >= 5 or local.date() in NYSE_HOLIDAYS:
        return False
    clock = local.time().replace(tzinfo=None)
    return datetime_time(4, 0) <= clock < datetime_time(20, 0)


class YahooExternalMarketProvider:
    """Best-effort Yahoo adapter; it never claims licensed real-time quality."""

    TICKERS = {"NQ": "NQ=F", "MU": "MU", "USDKRW": "KRW=X"}

    def __init__(
        self,
        downloader=None,
        *,
        tickers: dict[str, str] | None = None,
        thread_name_prefix: str = "samsung-widget-yahoo",
    ) -> None:
        self._downloader = downloader or yf.download
        self.tickers = dict(self.TICKERS if tickers is None else tickers)
        self.thread_name_prefix = str(thread_name_prefix).strip() or "widget-yahoo"

    def _fetch_one(self, key: str, ticker: str, now: datetime) -> ExternalPoint:
        received_at = _as_kst(now)
        market_state = (
            "OPEN" if key != "MU" or _mu_extended_market_open(now) else "MARKET_CLOSED"
        )
        try:
            frame = self._downloader(
                tickers=ticker,
                period="1d",
                interval="1m",
                auto_adjust=False,
                prepost=True,
                progress=False,
                threads=False,
                timeout=5,
            )
        except Exception as exc:
            return ExternalPoint(
                key,
                ticker,
                None,
                None,
                None,
                received_at.isoformat(),
                None,
                "yahoo_best_effort",
                "UNAVAILABLE",
                market_state,
                type(exc).__name__,
            )
        if frame is None or frame.empty:
            return ExternalPoint(
                key,
                ticker,
                None,
                None,
                None,
                received_at.isoformat(),
                None,
                "yahoo_best_effort",
                "UNAVAILABLE",
                market_state,
                "empty_response",
            )
        if isinstance(frame.columns, pd.MultiIndex):
            try:
                frame = frame.xs(ticker, axis=1, level=-1, drop_level=True)
            except (KeyError, ValueError):
                frame.columns = [
                    column[0] if isinstance(column, tuple) else column
                    for column in frame.columns
                ]
        close_column = next(
            (column for column in frame.columns if str(column).lower() == "close"),
            None,
        )
        if close_column is None:
            return ExternalPoint(
                key,
                ticker,
                None,
                None,
                None,
                received_at.isoformat(),
                None,
                "yahoo_best_effort",
                "UNAVAILABLE",
                market_state,
                "close_missing",
            )
        closes = pd.to_numeric(frame[close_column], errors="coerce").dropna()
        if closes.empty:
            return ExternalPoint(
                key,
                ticker,
                None,
                None,
                None,
                received_at.isoformat(),
                None,
                "yahoo_best_effort",
                "UNAVAILABLE",
                market_state,
                "close_empty",
            )
        observed_index = pd.Timestamp(closes.index[-1])
        if observed_index.tzinfo is None:
            return ExternalPoint(
                key,
                ticker,
                float(closes.iloc[-1]),
                None,
                None,
                received_at.isoformat(),
                None,
                "yahoo_best_effort",
                "UNAVAILABLE",
                market_state,
                "naive_source_timestamp",
            )
        observed_kst = observed_index.tz_convert(KST)
        age_sec = max(0.0, (received_at - observed_kst.to_pydatetime()).total_seconds())
        reference_cutoff = observed_index - pd.Timedelta(minutes=15)
        reference_rows = closes.loc[closes.index <= reference_cutoff]
        reference = float(reference_rows.iloc[-1]) if not reference_rows.empty else None
        change_pct = None
        if reference not in {None, 0.0}:
            change_pct = ((float(closes.iloc[-1]) - reference) / reference) * 100.0
        if market_state == "MARKET_CLOSED":
            quality = "MARKET_CLOSED"
            reason = None
        elif change_pct is None:
            quality = "UNAVAILABLE"
            reason = "insufficient_15m_history"
        elif age_sec <= EXTERNAL_STALE_SEC:
            quality = "BEST_EFFORT_DELAYED"
            reason = None
        else:
            quality = "STALE"
            reason = None
        return ExternalPoint(
            key,
            ticker,
            float(closes.iloc[-1]),
            round(change_pct, 4) if change_pct is not None else None,
            observed_kst.isoformat(),
            received_at.isoformat(),
            round(age_sec, 2),
            "yahoo_best_effort",
            quality,
            market_state,
            reason,
        )

    def fetch(self, observed_at: datetime) -> dict[str, ExternalPoint]:
        # Isolate configured best-effort sources so one five-second Yahoo delay
        # cannot serially consume the collector's ten-second refresh budget.
        with ThreadPoolExecutor(
            max_workers=max(1, len(self.tickers)),
            thread_name_prefix=self.thread_name_prefix,
        ) as executor:
            futures = {
                key: executor.submit(self._fetch_one, key, ticker, observed_at)
                for key, ticker in self.tickers.items()
            }
            points: dict[str, ExternalPoint] = {}
            for key, future in futures.items():
                try:
                    points[key] = future.result()
                except Exception as exc:
                    points[key] = ExternalPoint(
                        key=key,
                        ticker=self.tickers[key],
                        value=None,
                        change_15m_pct=None,
                        observed_at=None,
                        received_at=_as_kst(observed_at).isoformat(),
                        age_sec=None,
                        provider="yahoo_best_effort",
                        quality="UNAVAILABLE",
                        market_state=(
                            "OPEN"
                            if key != "MU" or _mu_extended_market_open(observed_at)
                            else "MARKET_CLOSED"
                        ),
                        reason=type(exc).__name__,
                    )
            return points


def _age_external_points(
    points: dict[str, ExternalPoint], observed_at: datetime
) -> dict[str, ExternalPoint]:
    now = _as_kst(observed_at)
    aged: dict[str, ExternalPoint] = {}
    for key, point in points.items():
        age_sec = point.age_sec
        if point.observed_at:
            try:
                source_time = datetime.fromisoformat(point.observed_at).astimezone(KST)
                age_sec = max(0.0, (now - source_time).total_seconds())
            except (TypeError, ValueError):
                pass
        quality = point.quality
        if (
            point.market_state != "MARKET_CLOSED"
            and age_sec is not None
            and age_sec > EXTERNAL_STALE_SEC
        ):
            quality = "STALE"
        aged[key] = ExternalPoint(
            **{
                **asdict(point),
                "age_sec": round(age_sec, 2) if age_sec is not None else None,
                "quality": quality,
            }
        )
    return aged


def evaluate_external_risk(
    points: dict[str, ExternalPoint],
    *,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    active_thresholds = EXTERNAL_THRESHOLDS if thresholds is None else thresholds
    adverse: list[str] = []
    severe: list[str] = []
    stale: list[str] = []
    unavailable: list[str] = []
    for key, threshold in active_thresholds.items():
        point = points.get(key)
        if point is None or point.quality == "UNAVAILABLE":
            unavailable.append(key)
            continue
        if point.quality == "STALE":
            stale.append(key)
            continue
        if point.market_state == "MARKET_CLOSED":
            continue
        change = point.change_15m_pct
        if change is None:
            unavailable.append(key)
            continue
        is_adverse = change <= threshold if key != "USDKRW" else change >= threshold
        is_severe = (
            change <= threshold * 2 if key != "USDKRW" else change >= threshold * 2
        )
        if is_adverse:
            adverse.append(key)
        if is_severe:
            severe.append(key)
    if severe or len(adverse) >= 2:
        level = "HOLD"
    elif adverse:
        level = "CAUTION"
    elif stale or unavailable:
        level = "DATA_LIMITED"
    else:
        level = "CLEAR"
    return {
        "level": level,
        "adverse": adverse,
        "severe": severe,
        "stale": stale,
        "unavailable": unavailable,
        "positive_promotion_forbidden": True,
    }


def _parse_previous_day(rows: object, observed_at: datetime) -> dict[str, Any]:
    if not isinstance(rows, list):
        return {}
    today = _as_kst(observed_at).strftime("%Y%m%d")
    expected_date = previous_krx_trading_date(_as_kst(observed_at).date())
    expected_source_date = expected_date.strftime("%Y%m%d")
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_date = str(row.get("dt") or "").strip()
        if (
            len(source_date) != 8
            or not source_date.isdigit()
            or source_date >= today
            or source_date != expected_source_date
        ):
            continue
        close = _positive_int(row.get("cur_prc"))
        high = _positive_int(row.get("high_pric"))
        low = _positive_int(row.get("low_pric"))
        open_price = _positive_int(row.get("open_pric"))
        if all((close, high, low, open_price)):
            return {
                "date": source_date,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
            }
    return {}


def _current_daily_anchor(
    rows: object, *, observed_at: datetime, cache_fetch_day: str
) -> dict[str, Any]:
    """Reject a retained daily response that was not refreshed this trade date."""
    day_key = _as_kst(observed_at).strftime("%Y%m%d")
    if cache_fetch_day != day_key:
        return {}
    return _parse_previous_day(rows, observed_at)


def _aligned_window_returns(
    primary_bars: list[MinuteBar], comparison_bars: list[MinuteBar]
) -> dict[str, dict[str, Any]]:
    """Return exact timestamp-aligned 3/5/15-minute close returns."""
    primary_by_time = {bar.source_time: bar.close for bar in primary_bars}
    comparison_by_time = {bar.source_time: bar.close for bar in comparison_bars}
    common_times = sorted(set(primary_by_time).intersection(comparison_by_time))
    result: dict[str, dict[str, Any]] = {}
    for horizon in (3, 5, 15):
        required_count = horizon + 1
        times = common_times[-required_count:]
        if len(times) < required_count:
            continue
        try:
            parsed_times = [datetime.strptime(value, "%Y%m%d%H%M%S") for value in times]
        except ValueError:
            continue
        if any(
            int((current - previous).total_seconds()) != 60
            for previous, current in zip(parsed_times, parsed_times[1:])
        ):
            continue
        primary_start = primary_by_time[times[0]]
        comparison_start = comparison_by_time[times[0]]
        if primary_start <= 0 or comparison_start <= 0:
            continue
        primary_return = (
            (primary_by_time[times[-1]] - primary_start) / primary_start
        ) * 100
        comparison_return = (
            (comparison_by_time[times[-1]] - comparison_start) / comparison_start
        ) * 100
        result[f"{horizon}m"] = {
            "samsung_return_pct": round(primary_return, 4),
            "comparison_return_pct": round(comparison_return, 4),
            "relative_return_pct_point": round(primary_return - comparison_return, 4),
            "window_start": times[0],
            "window_end": times[-1],
        }
    return result


def _same_window_relative_snapshot(
    samsung_bars: list[MinuteBar],
    peer_bars: list[MinuteBar],
    kospi_bars: list[MinuteBar],
) -> dict[str, Any]:
    return {
        "same_window": {
            "sk_hynix": _aligned_window_returns(samsung_bars, peer_bars),
            "kospi": _aligned_window_returns(samsung_bars, kospi_bars),
        },
        "same_window_basis": "timestamp_aligned_completed_1m_closes",
        "same_window_authority": ("negative_veto_and_session_weakness_recovery_only"),
        "same_window_sources": {
            "samsung": "kiwoom_ka10080_completed_1m",
            "sk_hynix": "kiwoom_ka10080_completed_1m",
            "kospi": "kiwoom_ka20005_completed_1m_index_x100",
        },
    }


def _relative_quality_assessment(
    relative: dict[str, Any], context: SessionContext
) -> tuple[bool, list[str], dict[str, Any]]:
    primary_change = _signed_float(relative.get("primary_change_pct"))
    if primary_change is None:
        primary_change = _signed_float(relative.get("samsung_change_pct"))
    peer_change = _signed_float(relative.get("peer_change_pct"))
    if peer_change is None:
        peer_change = _signed_float(relative.get("sk_hynix_change_pct"))
    market_change = _signed_float(relative.get("market_change_pct"))
    if market_change is None:
        market_change = _signed_float(relative.get("kospi_change_pct"))
    comparisons = (
        [peer_change, market_change] if context.name == "KRX_REGULAR" else [peer_change]
    )
    if primary_change is None or any(value is None for value in comparisons):
        return (
            False,
            ["relative_strength_unavailable"],
            {
                "session_underperformance": None,
                "same_window_negative_veto": False,
                "same_window_recovery_complete": False,
                "same_window_recovery_confirmed": False,
                "session_underperformance_cleared": False,
            },
        )
    weak_against = [
        value
        for value in comparisons
        if value is not None
        and primary_change < value - RELATIVE_UNDERPERFORMANCE_LIMIT_PCT
    ]
    generic_same_window = relative.get("same_window_generic")
    generic_contract = isinstance(generic_same_window, dict)
    same_window = (
        generic_same_window if generic_contract else relative.get("same_window")
    )
    same_window_weak = False
    recovery_complete = True
    recovery_nonweak = True
    if generic_contract:
        comparison_names = (
            ("peer", "market") if context.name == "KRX_REGULAR" else ("peer",)
        )
    else:
        comparison_names = (
            ("sk_hynix", "kospi") if context.name == "KRX_REGULAR" else ("sk_hynix",)
        )
    if isinstance(same_window, dict):
        for comparison_name in comparison_names:
            windows = same_window.get(comparison_name)
            if not isinstance(windows, dict):
                recovery_complete = False
                continue
            # Prefer the broadest available intraday window. Missing optional
            # minute data does not create a new positive or blocking authority.
            for horizon in ("15m", "5m", "3m"):
                row = windows.get(horizon)
                if not isinstance(row, dict):
                    continue
                relative_return = _signed_float(row.get("relative_return_pct_point"))
                if (
                    relative_return is not None
                    and relative_return < -RELATIVE_UNDERPERFORMANCE_LIMIT_PCT
                ):
                    same_window_weak = True
                break
            for horizon in ("15m", "5m"):
                row = windows.get(horizon)
                relative_return = (
                    _signed_float(row.get("relative_return_pct_point"))
                    if isinstance(row, dict)
                    else None
                )
                if relative_return is None:
                    recovery_complete = False
                elif relative_return < -RELATIVE_UNDERPERFORMANCE_LIMIT_PCT:
                    recovery_nonweak = False
    else:
        recovery_complete = False

    same_window_recovery = recovery_complete and recovery_nonweak
    session_underperformance = bool(weak_against)
    session_underperformance_cleared = bool(
        session_underperformance and same_window_recovery and not same_window_weak
    )
    passed = not same_window_weak and (
        not session_underperformance or session_underperformance_cleared
    )
    return (
        passed,
        ([] if passed else ["relative_strength_weak"]),
        {
            "session_underperformance": session_underperformance,
            "same_window_negative_veto": same_window_weak,
            "same_window_recovery_complete": recovery_complete,
            "same_window_recovery_confirmed": same_window_recovery,
            "session_underperformance_cleared": session_underperformance_cleared,
        },
    )


def _relative_quality(
    relative: dict[str, Any], context: SessionContext
) -> tuple[bool, list[str]]:
    passed, issues, _metadata = _relative_quality_assessment(relative, context)
    return passed, issues


def _live_reversal_veto(
    *,
    current_price: int,
    bars: list[MinuteBar],
    bbo: dict[str, Any],
    trend_details: dict[str, dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    """Use the forming-price impulse only as an immediate negative veto."""
    one_minute = trend_details.get("1m") or {}
    last_completed_close = bars[-1].close if bars else None
    reversal_band = _positive_int(one_minute.get("flat_band_price"))
    if reversal_band is None and last_completed_close:
        reversal_band = get_tick_size(last_completed_close)
    best_bid_qty = _positive_int(bbo.get("best_bid_qty"))
    best_ask_qty = _positive_int(bbo.get("best_ask_qty"))
    ask_to_bid_ratio = (
        best_ask_qty / best_bid_qty
        if best_bid_qty is not None and best_ask_qty is not None
        else None
    )
    negative_impulse = bool(
        last_completed_close is not None
        and reversal_band is not None
        and current_price <= last_completed_close - reversal_band
    )
    ask_pressure = bool(ask_to_bid_ratio is not None and ask_to_bid_ratio >= 1.5)
    veto = negative_impulse and ask_pressure
    return veto, {
        "veto": veto,
        "authority": "negative_veto_only",
        "positive_promotion_forbidden": True,
        "last_completed_close": last_completed_close,
        "current_price": current_price,
        "reversal_band": reversal_band,
        "negative_impulse": negative_impulse,
        "ask_pressure": ask_pressure,
        "ask_to_bid_qty_ratio": (
            round(ask_to_bid_ratio, 4) if ask_to_bid_ratio is not None else None
        ),
    }


def _source_quality(
    *,
    observed_at: datetime,
    context: SessionContext,
    bars: list[MinuteBar],
    bbo: dict[str, Any],
    previous_day: dict[str, Any] | None,
    quote_age_sec: float,
    current_price: int,
) -> dict[str, Any]:
    issues: list[str] = []
    if not context.active or context.start is None:
        issues.append("session_not_active")
    if len(bars) < context.minimum_bars:
        issues.append("minimum_bars_not_met")
    if bars:
        last_bar = datetime.strptime(bars[-1].source_time, "%Y%m%d%H%M%S").replace(
            tzinfo=KST
        )
        age = (_as_kst(observed_at) - last_bar).total_seconds()
        max_age = 120 if context.name == "KRX_REGULAR" else 180
        if age < -2:
            issues.append("completed_bar_time_conflict")
        elif age > max_age:
            issues.append("completed_bar_stale")
    else:
        issues.append("completed_bars_missing")
    if previous_day is not None and not previous_day:
        issues.append("previous_day_ohlc_missing")
    if quote_age_sec < 0 or quote_age_sec > 20:
        issues.append("quote_stale")
    best_bid = _positive_int(bbo.get("best_bid"))
    best_ask = _positive_int(bbo.get("best_ask"))
    bbo_age = _signed_float(bbo.get("age_sec"))
    if not best_bid or not best_ask or best_ask < best_bid:
        issues.append("bbo_missing_or_crossed")
    elif bbo_age is None or bbo_age < 0 or bbo_age > 20:
        issues.append("bbo_stale")
    elif current_price > 0:
        coherent_low = move_price_by_ticks(best_bid, -1)
        coherent_high = move_price_by_ticks(best_ask, 1)
        if not coherent_low <= current_price <= coherent_high:
            issues.append("quote_bbo_inconsistent")
    required_sources = ["quote", "bbo", "completed_1m"]
    if previous_day is not None:
        required_sources.append("previous_day_ohlc")
    return {
        "status": "PASS" if not issues else "BLOCKED",
        "issues": issues,
        "required_sources": required_sources,
    }


def _spread_tick_count(best_bid: int, best_ask: int, *, cap: int = 100) -> int:
    """Count valid exchange ticks, including price-band boundary changes."""
    if best_bid <= 0 or best_ask <= best_bid:
        return 0
    price = clamp_price_to_tick(best_bid)
    ticks = 0
    while price < best_ask and ticks < max(1, cap):
        next_price = move_price_by_ticks(price, 1)
        if next_price <= price:
            return max(1, cap)
        price = next_price
        ticks += 1
    return ticks


def _apply_nxt_aftermarket_caution_entry_scope(
    result: dict[str, Any],
    *,
    context: SessionContext,
    resistance_reclaimed: bool,
    higher_high_and_low: bool,
) -> None:
    """Narrow weak aftermarket caution entries to the support/bid price only."""
    if (
        context.name != "NXT_AFTERMARKET"
        or result.get("state") != "ENTRY_CAUTION"
        or resistance_reclaimed
        or higher_high_and_low
    ):
        return
    entry_low = _positive_int(result.get("entry_price_low"))
    entry_high = _positive_int(result.get("entry_price_high"))
    if entry_low is None or entry_high is None or entry_high < entry_low:
        return
    result["entry_price_high"] = entry_low
    result["unmet_conditions"] = list(
        dict.fromkeys(
            [
                *(result.get("unmet_conditions") or []),
                "nxt_aftermarket_reclaim_structure_unconfirmed",
            ]
        )
    )
    result.setdefault("derived", {})["entry_price_scope"] = {
        "policy": "nxt_aftermarket_caution_support_bid_only_v1",
        "applied": True,
        "reason": "resistance_not_reclaimed_and_higher_high_low_unconfirmed",
        "unconstrained_entry_price_low": entry_low,
        "unconstrained_entry_price_high": entry_high,
        "constrained_price": entry_low,
        "authority": ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "metric_contract": METRIC_CONTRACT,
    }


def evaluate_advisory(
    *,
    observed_at: datetime,
    context: SessionContext,
    current_price: int,
    bars: list[MinuteBar],
    bbo: dict[str, Any],
    previous_day: dict[str, Any],
    relative: dict[str, Any],
    external_points: dict[str, ExternalPoint],
    flow: dict[str, Any] | None = None,
    recent_trade_negative_veto: bool = False,
    premarket: dict[str, Any] | None = None,
    regular_session: dict[str, Any] | None = None,
    quote_age_sec: float = 0.0,
    quote_received_at: str | None = None,
    external_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build a deterministic widget-only advisory without score/AI authority."""
    flow = flow or {}
    premarket = premarket or {}
    regular_session = regular_session or {}
    source_quality = _source_quality(
        observed_at=observed_at,
        context=context,
        bars=bars,
        bbo=bbo,
        previous_day=previous_day,
        quote_age_sec=quote_age_sec,
        current_price=current_price,
    )
    external_points = _age_external_points(external_points, observed_at)
    external_risk = evaluate_external_risk(
        external_points, thresholds=external_thresholds
    )
    trend_details = analyze_trends(bars, session_name=context.name)
    trends = {
        key: str(detail.get("state") or "unavailable")
        for key, detail in trend_details.items()
    }
    trend_assessment = _trend_assessment(trends)
    intraday_regime = analyze_intraday_regime(bars)
    live_reversal_veto, live_reversal = _live_reversal_veto(
        current_price=current_price,
        bars=bars,
        bbo=bbo,
        trend_details=trend_details,
    )
    now = _as_kst(observed_at)
    premarket_same_day = premarket.get("date") == now.date().isoformat()
    premarket_aux_applied = bool(
        context.name == "KRX_REGULAR"
        and now.time().replace(tzinfo=None) < PREMARKET_AUXILIARY_END
        and premarket_same_day
    )
    if context.name == "KRX_REGULAR":
        if now.time().replace(tzinfo=None) >= PREMARKET_AUXILIARY_END:
            premarket_provenance = "EXPIRED_0930"
        elif premarket_aux_applied:
            premarket_provenance = "APPLIED_AUXILIARY"
        else:
            premarket_provenance = "UNAVAILABLE"
    else:
        premarket_provenance = "NOT_APPLICABLE"
    end_of_day = datetime.combine(now.date(), NXT_AFTERMARKET_END, tzinfo=KST)
    session_end = (
        datetime.combine(now.date(), context.end, tzinfo=KST)
        if context.end is not None
        else end_of_day
    )
    valid_until = min(now + timedelta(seconds=60), session_end, end_of_day).isoformat()
    base = {
        "state": "DATA_WAIT",
        "raw_state": "DATA_WAIT",
        "session": context.name,
        "entry_price_low": None,
        "entry_price_high": None,
        "trigger": None,
        "trigger_price": None,
        "invalidation": None,
        "invalidation_price": None,
        "reasons": [],
        "unmet_conditions": list(source_quality["issues"]),
        "valid_until": valid_until,
        "observed_at": _as_kst(observed_at).isoformat(),
        "source_quality": source_quality,
        "external_risk": external_risk,
        "external_points": {
            key: asdict(point) for key, point in external_points.items()
        },
        "trend_assessment": trend_assessment,
        "trend_details": trend_details,
        "intraday_regime": intraday_regime,
        "live_reversal": live_reversal,
        "relative_strength": relative,
        "provenance": {
            "market_venue": context.market_venue,
            "market_cohort": context.market_cohort,
            "quote_request_code": context.request_code,
            "external_provider": "yahoo_best_effort",
            "premarket_context": premarket_provenance,
            "quote_received_at": quote_received_at,
            "quote_age_sec": round(quote_age_sec, 3),
            "session_vwap_method": "hlc3_volume_weighted_with_hlc3_fallback",
        },
        "authority": ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": METRIC_CONTRACT,
    }
    if source_quality["status"] != "PASS":
        return base

    structure = _structure_features(bars)
    vwap = _session_vwap(bars)
    volume_ok, volume_meta = _volume_confirmation(bars)
    relative_ok, relative_issues, relative_assessment = _relative_quality_assessment(
        relative, context
    )
    base["relative_assessment"] = relative_assessment
    best_bid = int(bbo["best_bid"])
    best_ask = int(bbo["best_ask"])
    spread_ticks = _spread_tick_count(best_bid, best_ask)

    raw_structural_support = structure.get("confirmed_support")
    structural_support = (
        clamp_price_to_tick(raw_structural_support)
        if isinstance(raw_structural_support, int) and raw_structural_support > 0
        else None
    )
    raw_candidate_support = structure.get("candidate_support")
    candidate_support = (
        clamp_price_to_tick(raw_candidate_support)
        if isinstance(raw_candidate_support, int) and raw_candidate_support > 0
        else None
    )
    session_anchor = (
        regular_session if context.name == "NXT_AFTERMARKET" else previous_day
    )
    recent_resistance = structure.get("recent_resistance")
    structure_ok = bool(structure["higher_high_and_low"] or structure["retest_held"])
    vwap_reclaimed = bool(vwap and current_price >= vwap)
    resistance_reclaimed = bool(
        isinstance(recent_resistance, int)
        and recent_resistance > 0
        and current_price >= recent_resistance
        and structure_ok
    )
    resistance_reclaim_hold_confirmed = bool(
        resistance_reclaimed
        and isinstance(recent_resistance, int)
        and len(bars) >= 2
        and bars[-2].close > recent_resistance
        and bars[-1].close > recent_resistance
    )
    intraday_regime_down = intraday_regime.get("state") == "down"
    vwap_only_structure_confirmed = bool(
        vwap_reclaimed
        and not resistance_reclaimed
        and structure["higher_high_and_low"]
        and not intraday_regime_down
    )
    reclaim_ok = resistance_reclaimed or vwap_only_structure_confirmed
    tactical_candidates = [
        value
        for value in (
            structural_support,
            vwap if vwap_reclaimed else None,
            (
                recent_resistance
                if resistance_reclaimed and not vwap_reclaimed
                else None
            ),
        )
        if isinstance(value, int) and 0 < value <= current_price
    ]
    tactical_support = (
        clamp_price_to_tick(max(tactical_candidates)) if tactical_candidates else None
    )
    trends_ok = trends.get("3m") in {"up", "flat"} and trends.get("5m") in {
        "up",
        "flat",
    }
    absorption_recovery_ok = _absorption_recovery_confirmation(
        volume_meta=volume_meta,
        structure=structure,
        completed_close=bars[-1].close,
        vwap=vwap,
        recent_resistance=recent_resistance,
        reclaim_ok=reclaim_ok,
        trends_ok=trends_ok,
    )
    volume_ok = volume_ok or absorption_recovery_ok
    volume_meta["absorption_recovery_confirmed"] = absorption_recovery_ok
    volume_meta["volume_confirmation_mode"] = (
        "absorption_recovery"
        if absorption_recovery_ok
        else "standard_rebound" if volume_ok else "unconfirmed"
    )
    spread_ok = spread_ticks <= 2
    core_checks = {
        "low_structure_confirmed": structure_ok,
        "vwap_or_resistance_reclaimed": reclaim_ok,
        "rebound_volume_confirmed": volume_ok,
        "three_five_minute_not_down": trends_ok,
        "intraday_regime_recovery_confirmed": bool(
            not intraday_regime_down
            or (resistance_reclaimed and structure["higher_high_and_low"])
        ),
        "relative_strength_not_weak": relative_ok,
        "spread_within_two_ticks": spread_ok,
    }
    unmet = [
        name
        for name, passed in core_checks.items()
        if not passed and name != "relative_strength_not_weak"
    ]
    unmet.extend(relative_issues)
    reasons = [name for name, passed in core_checks.items() if passed]
    if relative_assessment["session_underperformance_cleared"]:
        reasons.append("same_window_relative_recovery")
    if flow.get("foreign_nonworsening"):
        reasons.append("foreign_flow_nonworsening")
    if flow.get("program_nonworsening"):
        reasons.append("program_flow_nonworsening")
    flow_negative = bool(
        context.name == "KRX_REGULAR"
        and flow.get("status") == "OBSERVED"
        and flow.get("live_for_current_session") is True
        and (
            not flow.get("foreign_nonworsening") or not flow.get("program_nonworsening")
        )
    )
    if flow_negative:
        unmet.append("foreign_or_program_flow_not_improving")
    flow_data_limited = bool(
        context.name == "KRX_REGULAR"
        and (
            flow.get("status") != "OBSERVED"
            or flow.get("live_for_current_session") is not True
        )
    )
    if flow_data_limited:
        unmet.append("regular_flow_unavailable")

    premarket_vwap = _positive_int(premarket.get("vwap"))
    premarket_aux_weak = bool(
        premarket_aux_applied
        and premarket_vwap is not None
        and current_price < premarket_vwap
    )
    if premarket_aux_applied and premarket_vwap is not None:
        if premarket_aux_weak:
            unmet.append("premarket_vwap_not_recovered")
        else:
            reasons.append("premarket_aux_supportive")

    if structural_support is None:
        candidate_support_age = structure.get("candidate_support_age_bars")
        candidate_hold_confirmed = bool(
            isinstance(candidate_support_age, int)
            and CANDIDATE_SUPPORT_CAUTION_MIN_HOLD_BARS
            <= candidate_support_age
            <= CANDIDATE_SUPPORT_CAUTION_MAX_HOLD_BARS
        )
        candidate_recovery_pct = (
            round(
                ((current_price - candidate_support) / candidate_support) * 100,
                4,
            )
            if candidate_support and current_price >= candidate_support
            else None
        )
        candidate_tactical_support = (
            clamp_price_to_tick(vwap) if vwap_reclaimed and vwap else None
        )
        candidate_two_tick_limit_pct = (
            (
                (
                    move_price_by_ticks(candidate_tactical_support, 2)
                    - candidate_tactical_support
                )
                / candidate_tactical_support
            )
            * 100
            if candidate_tactical_support
            else None
        )
        candidate_chase_limit_pct = (
            max(TACTICAL_CHASE_LIMIT_PCT, candidate_two_tick_limit_pct)
            if candidate_two_tick_limit_pct is not None
            else None
        )
        candidate_chase_pct = (
            ((current_price - candidate_tactical_support) / candidate_tactical_support)
            * 100
            if candidate_tactical_support
            else None
        )
        candidate_volume_composition = bool(
            volume_meta.get("volume_minimum_composition_met")
            and int(volume_meta.get("rising_volume_sample_count") or 0) >= 3
            and int(volume_meta.get("falling_volume_sample_count") or 0) >= 1
        )
        candidate_safety_blockers = []
        if recent_trade_negative_veto:
            candidate_safety_blockers.append("recent_rest_prints_descending")
        if live_reversal_veto:
            candidate_safety_blockers.append("live_price_reversal_with_ask_pressure")
        if external_risk["level"] == "HOLD":
            candidate_safety_blockers.append("external_risk_hold")
        candidate_caution_core = bool(
            context.name == "KRX_REGULAR"
            and candidate_support
            and candidate_hold_confirmed
            and candidate_recovery_pct is not None
            and candidate_recovery_pct <= CANDIDATE_SUPPORT_CAUTION_MAX_RECOVERY_PCT
            and candidate_tactical_support
            and vwap_reclaimed
            and trends_ok
            and relative_ok
            and spread_ok
            and candidate_volume_composition
            and not intraday_regime_down
            and not flow_negative
            and external_risk["level"] != "HOLD"
            and not candidate_safety_blockers
        )
        candidate_caution_within_chase = bool(
            candidate_caution_core
            and candidate_chase_pct is not None
            and candidate_chase_limit_pct is not None
            and candidate_chase_pct <= candidate_chase_limit_pct
        )
        candidate_caution_meta = {
            "eligible": candidate_caution_core,
            "candidate_support_age_bars": candidate_support_age,
            "minimum_hold_bars": CANDIDATE_SUPPORT_CAUTION_MIN_HOLD_BARS,
            "maximum_hold_bars": CANDIDATE_SUPPORT_CAUTION_MAX_HOLD_BARS,
            "recovery_pct": (
                candidate_recovery_pct if candidate_recovery_pct is not None else None
            ),
            "maximum_recovery_pct": CANDIDATE_SUPPORT_CAUTION_MAX_RECOVERY_PCT,
            "tactical_support": candidate_tactical_support,
            "tactical_chase_pct": (
                round(candidate_chase_pct, 4)
                if candidate_chase_pct is not None
                else None
            ),
            "dynamic_chase_limit_pct": (
                round(candidate_chase_limit_pct, 4)
                if candidate_chase_limit_pct is not None
                else None
            ),
            "volume_composition_met": candidate_volume_composition,
            "intraday_regime_state": intraday_regime.get("state"),
            "intraday_regime_not_down_required": True,
            "safety_blockers": candidate_safety_blockers,
            "ready_promotion_forbidden": True,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "metric_contract": METRIC_CONTRACT,
        }
        base.update(
            {
                "state": "WATCH",
                "raw_state": "WATCH",
                "reasons": reasons,
                "unmet_conditions": list(
                    dict.fromkeys(
                        [
                            "confirmed_support_missing",
                            *unmet,
                            *candidate_safety_blockers,
                        ]
                    )
                ),
                "derived": {
                    "session_vwap": vwap,
                    "confirmed_support": None,
                    "candidate_support": candidate_support,
                    "support_confirmation": structure["support_confirmation"],
                    "confirmed_support_age_bars": structure.get(
                        "confirmed_support_age_bars"
                    ),
                    "candidate_support_age_bars": candidate_support_age,
                    "session_anchor": session_anchor,
                    "recent_resistance": recent_resistance,
                    "minute_trends": trends,
                    "higher_low": structure["higher_low"],
                    "higher_high": structure["higher_high"],
                    "higher_high_and_low": structure["higher_high_and_low"],
                    "retest_held": structure["retest_held"],
                    "retest_rebound_confirmed": structure["retest_rebound_confirmed"],
                    "candidate_support_caution": candidate_caution_meta,
                    **volume_meta,
                },
                "flow": flow,
            }
        )
        if candidate_caution_within_chase:
            entry_low = max(candidate_tactical_support, best_bid)
            entry_high = min(
                best_ask, move_price_by_ticks(candidate_tactical_support, 2)
            )
            if entry_low <= entry_high:
                candidate_invalidation = move_price_by_ticks(candidate_support, -2)
                if not _apply_entry_reward_risk_guard(
                    base,
                    entry_price_high=entry_high,
                    invalidation_price=candidate_invalidation,
                ):
                    return base
                base.update(
                    {
                        "state": "ENTRY_CAUTION",
                        "raw_state": "ENTRY_CAUTION",
                        "entry_price_low": entry_low,
                        "entry_price_high": entry_high,
                        "trigger": "candidate_support_vwap_recovery_caution",
                        "trigger_price": candidate_tactical_support,
                        "invalidation": "candidate_support_break",
                        "invalidation_price": candidate_invalidation,
                        "reasons": list(
                            dict.fromkeys(
                                [
                                    *reasons,
                                    "candidate_support_hold_confirmed",
                                    "opening_recovery_caution",
                                ]
                            )
                        ),
                    }
                )
                return base
        if (
            candidate_caution_core
            and candidate_chase_pct is not None
            and candidate_chase_limit_pct is not None
            and candidate_chase_pct > candidate_chase_limit_pct
        ):
            base["state"] = base["raw_state"] = "NO_CHASE"
            base["reasons"] = ["price_above_dynamic_two_tick_chase_limit"]
            base["derived"]["latent_next_blockers"] = [
                "price_above_dynamic_two_tick_chase_limit"
            ]
        return base
    soft_invalidation = move_price_by_ticks(structural_support, -1)
    hard_invalidation = move_price_by_ticks(structural_support, -2)
    completed_close_break = bars[-1].close < structural_support
    live_break_depth_ticks = (
        _spread_tick_count(current_price, structural_support)
        if current_price < structural_support
        else 0
    )
    deep_live_break = bool(current_price <= hard_invalidation and live_reversal_veto)
    confirmed_support_break = completed_close_break or deep_live_break
    invalidation_confirmation = {
        "policy": "completed_1m_close_or_two_tick_live_break_with_ask_pressure",
        "soft_invalidation_price": soft_invalidation,
        "hard_invalidation_price": hard_invalidation,
        "completed_close_break": completed_close_break,
        "deep_live_break": deep_live_break,
        "live_break_depth_ticks": live_break_depth_ticks,
    }
    if confirmed_support_break:
        base.update(
            {
                "state": "AVOID",
                "raw_state": "AVOID",
                "invalidation": "confirmed_support_break",
                "invalidation_price": hard_invalidation,
                "reasons": ["confirmed_support_broken"],
                "unmet_conditions": list(dict.fromkeys(unmet)),
                "derived": {
                    "session_vwap": vwap,
                    "confirmed_support": structural_support,
                    "structural_support": structural_support,
                    "candidate_support": candidate_support,
                    "support_confirmation": structure["support_confirmation"],
                    "confirmed_support_age_bars": structure.get(
                        "confirmed_support_age_bars"
                    ),
                    "invalidation_confirmation": invalidation_confirmation,
                    "tactical_support": tactical_support,
                    "session_anchor": session_anchor,
                    "recent_resistance": recent_resistance,
                    "distance_from_structural_support_pct": round(
                        ((current_price - structural_support) / structural_support)
                        * 100,
                        4,
                    ),
                    "minute_trends": trends,
                    "higher_low": structure["higher_low"],
                    "higher_high": structure["higher_high"],
                    "higher_high_and_low": structure["higher_high_and_low"],
                    "retest_held": structure["retest_held"],
                    "retest_rebound_confirmed": structure["retest_rebound_confirmed"],
                },
                "flow": flow,
            }
        )
        return base
    if current_price < structural_support:
        base.update(
            {
                "state": "WATCH",
                "raw_state": "WATCH",
                "invalidation": "soft_support_break_pending_confirmation",
                "invalidation_price": hard_invalidation,
                "reasons": ["support_break_not_yet_confirmed"],
                "unmet_conditions": list(dict.fromkeys(["soft_support_break", *unmet])),
                "derived": {
                    "session_vwap": vwap,
                    "confirmed_support": structural_support,
                    "structural_support": structural_support,
                    "candidate_support": candidate_support,
                    "support_confirmation": structure["support_confirmation"],
                    "confirmed_support_age_bars": structure.get(
                        "confirmed_support_age_bars"
                    ),
                    "tactical_support": tactical_support,
                    "session_anchor": session_anchor,
                    "recent_resistance": recent_resistance,
                    "distance_from_structural_support_pct": round(
                        ((current_price - structural_support) / structural_support)
                        * 100,
                        4,
                    ),
                    "invalidation_confirmation": invalidation_confirmation,
                    "minute_trends": trends,
                    "higher_low": structure["higher_low"],
                    "higher_high": structure["higher_high"],
                    "higher_high_and_low": structure["higher_high_and_low"],
                    "retest_held": structure["retest_held"],
                    "retest_rebound_confirmed": structure["retest_rebound_confirmed"],
                },
                "flow": flow,
            }
        )
        return base
    if tactical_support is None:
        base["unmet_conditions"] = ["tactical_support_missing", *unmet]
        return base
    trigger_candidates = [
        value
        for value in (vwap, recent_resistance, session_anchor.get("close"))
        if isinstance(value, int) and value > 0 and value <= current_price
    ]
    trigger_price = clamp_price_to_tick(
        max(trigger_candidates, default=tactical_support)
    )
    structural_chase_pct = (
        (current_price - structural_support) / structural_support
    ) * 100
    tactical_chase_pct = ((current_price - tactical_support) / tactical_support) * 100

    base.update(
        {
            "trigger": "dynamic_support_and_vwap_reclaim",
            "trigger_price": trigger_price,
            "invalidation": "confirmed_support_break",
            "invalidation_price": hard_invalidation,
            "reasons": reasons,
            "unmet_conditions": list(dict.fromkeys(unmet)),
            "derived": {
                "session_vwap": vwap,
                "confirmed_support": structural_support,
                "structural_support": structural_support,
                "candidate_support": candidate_support,
                "support_confirmation": structure["support_confirmation"],
                "confirmed_support_age_bars": structure.get(
                    "confirmed_support_age_bars"
                ),
                "invalidation_confirmation": invalidation_confirmation,
                "tactical_support": tactical_support,
                "session_anchor": session_anchor,
                "recent_resistance": recent_resistance,
                "previous_day": previous_day,
                "opening_range_high": max(
                    bar.high for bar in bars[: context.minimum_bars]
                ),
                "opening_range_low": min(
                    bar.low for bar in bars[: context.minimum_bars]
                ),
                "spread_ticks": spread_ticks,
                "chase_pct": round(tactical_chase_pct, 4),
                "chase_basis": "tactical_support",
                "structural_chase_pct": round(structural_chase_pct, 4),
                "tactical_chase_pct": round(tactical_chase_pct, 4),
                "vwap_reclaimed": vwap_reclaimed,
                "recent_resistance_reclaimed": resistance_reclaimed,
                "resistance_reclaim_hold_confirmed": (
                    resistance_reclaim_hold_confirmed
                ),
                "resistance_reclaim_confirmation": {
                    "policy": "two_completed_closes_strictly_above_recent_resistance",
                    "recent_resistance": recent_resistance,
                    "previous_completed_close": (
                        bars[-2].close if len(bars) >= 2 else None
                    ),
                    "latest_completed_close": bars[-1].close if bars else None,
                    "hold_confirmed": resistance_reclaim_hold_confirmed,
                    "future_prediction": False,
                },
                "reclaim_mode": (
                    "vwap_and_resistance"
                    if vwap_reclaimed and resistance_reclaimed
                    else (
                        "vwap"
                        if vwap_reclaimed
                        else "recent_resistance" if resistance_reclaimed else "none"
                    )
                ),
                "vwap_only_structure_confirmed": vwap_only_structure_confirmed,
                "minute_trends": trends,
                "minute_trend_details": trend_details,
                "trend_assessment": trend_assessment,
                "live_reversal": live_reversal,
                "higher_low": structure["higher_low"],
                "higher_high": structure["higher_high"],
                "higher_high_and_low": structure["higher_high_and_low"],
                "retest_held": structure["retest_held"],
                "retest_rebound_confirmed": structure["retest_rebound_confirmed"],
                "premarket_auxiliary": (premarket if premarket_aux_applied else None),
                **volume_meta,
            },
            "flow": flow,
        }
    )
    relative_severe_veto = bool(
        relative_assessment.get("session_underperformance") is True
        and relative_assessment.get("same_window_negative_veto") is True
    )
    relative_caution_only = bool(
        not relative_ok
        and relative_assessment.get("session_underperformance") is not None
        and structure_ok
        and reclaim_ok
        and volume_ok
        and trends_ok
        and spread_ok
        and not relative_severe_veto
    )
    base["derived"]["relative_strength_policy"] = {
        "hard_veto": relative_severe_veto,
        "caution_only": relative_caution_only,
        "policy": "own_recovery_can_demote_transient_relative_weakness_to_caution",
        "authority": ADVISORY_AUTHORITY,
        "runtime_effect": False,
    }
    if relative_caution_only:
        base["reasons"] = list(
            dict.fromkeys([*base["reasons"], "relative_weakness_caution_only"])
        )
    if recent_trade_negative_veto or live_reversal_veto:
        base["state"] = base["raw_state"] = "WATCH"
        if recent_trade_negative_veto:
            base["unmet_conditions"].append("recent_rest_prints_descending")
        if live_reversal_veto:
            base["unmet_conditions"].append("live_price_reversal_with_ask_pressure")
        return base

    two_tick_chase_limit_pct = (
        (move_price_by_ticks(tactical_support, 2) - tactical_support) / tactical_support
    ) * 100
    dynamic_chase_limit_pct = max(TACTICAL_CHASE_LIMIT_PCT, two_tick_chase_limit_pct)
    base["derived"]["dynamic_chase_limit_pct"] = round(dynamic_chase_limit_pct, 4)

    early_reversal_allowed_unmet = {
        "vwap_or_resistance_reclaimed",
        "rebound_volume_confirmed",
        "regular_flow_unavailable",
    }
    early_reversal_pre_volume_eligible = bool(
        structure["retest_held"]
        and structure["retest_rebound_confirmed"]
        and trends_ok
        and relative_ok
        and spread_ok
        and not flow_negative
        and not premarket_aux_weak
        and external_risk["level"] != "HOLD"
        and not intraday_regime_down
        and not vwap_reclaimed
        and not reclaim_ok
        and "vwap_or_resistance_reclaimed" in base["unmet_conditions"]
        and set(base["unmet_conditions"]).issubset(early_reversal_allowed_unmet)
    )
    early_reversal_structure_eligible = bool(
        early_reversal_pre_volume_eligible and volume_ok
    )
    base["derived"]["early_reversal_confirmation_floor"] = {
        "pre_volume_structure_eligible": early_reversal_pre_volume_eligible,
        "rebound_volume_required": True,
        "rebound_volume_confirmed": volume_ok,
        "intraday_regime_not_down_required": True,
        "intraday_regime_state": intraday_regime.get("state"),
        "authority": "negative_veto_only",
        "runtime_effect": False,
        "metric_contract": METRIC_CONTRACT,
    }
    if early_reversal_pre_volume_eligible and not volume_ok:
        base["unmet_conditions"] = list(
            dict.fromkeys(
                [
                    *base["unmet_conditions"],
                    "early_reversal_rebound_volume_required",
                ]
            )
        )
    if intraday_regime_down and not resistance_reclaimed:
        base["unmet_conditions"] = list(
            dict.fromkeys(
                [
                    *base["unmet_conditions"],
                    "intraday_down_regime_resistance_reclaim_pending",
                ]
            )
        )
    recent_window = bars[-RECENT_RUNUP_LOOKBACK_BARS:]
    recent_runup_low = min(bar.low for bar in recent_window)
    recent_runup_high = max(bar.high for bar in recent_window)
    recent_runup_pct = (
        ((current_price - recent_runup_low) / recent_runup_low) * 100
        if current_price > recent_runup_low
        else 0.0
    )
    recent_runup_limit_pct = max(
        RECENT_RUNUP_NO_CHASE_PCT,
        (
            (
                move_price_by_ticks(recent_runup_low, RECENT_RUNUP_NO_CHASE_TICKS)
                - recent_runup_low
            )
            / recent_runup_low
        )
        * 100,
    )
    recent_pullback_pct = (
        ((recent_runup_high - recent_runup_low) / recent_runup_high) * 100
        if recent_runup_high > recent_runup_low
        else 0.0
    )
    recent_low_age_bars = (
        len(recent_window)
        - 1
        - max(
            index
            for index, bar in enumerate(recent_window)
            if bar.low == recent_runup_low
        )
    )
    early_reversal_pullback_limit_pct = max(
        EARLY_REVERSAL_PULLBACK_MIN_PCT,
        (
            (
                move_price_by_ticks(recent_runup_low, EARLY_REVERSAL_PULLBACK_TICKS)
                - recent_runup_low
            )
            / recent_runup_low
        )
        * 100,
    )
    early_reversal_setup_eligible = bool(
        early_reversal_structure_eligible
        and recent_pullback_pct >= early_reversal_pullback_limit_pct
        and EARLY_REVERSAL_LOW_HOLD_MIN_BARS
        <= recent_low_age_bars
        <= EARLY_REVERSAL_LOW_HOLD_MAX_BARS
    )
    near_recent_high = current_price >= move_price_by_ticks(recent_runup_high, -1)
    base["derived"]["recent_runup_chase_guard"] = {
        "lookback_bars": len(recent_window),
        "recent_low": recent_runup_low,
        "recent_high": recent_runup_high,
        "runup_pct": round(recent_runup_pct, 4),
        "pullback_range_pct": round(recent_pullback_pct, 4),
        "recent_low_age_bars": recent_low_age_bars,
        "limit_pct": round(recent_runup_limit_pct, 4),
        "early_reversal_pullback_limit_pct": round(
            early_reversal_pullback_limit_pct, 4
        ),
        "near_recent_high": near_recent_high,
        "authority": "negative_veto_only",
        "metric_contract": METRIC_CONTRACT,
    }
    if (
        (all(core_checks.values()) or early_reversal_setup_eligible)
        and near_recent_high
        and recent_runup_pct >= recent_runup_limit_pct
    ):
        base["state"] = base["raw_state"] = "NO_CHASE"
        base["entry_price_low"] = None
        base["entry_price_high"] = None
        base["reasons"] = ["recent_runup_near_rolling_high"]
        base["unmet_conditions"] = list(
            dict.fromkeys(
                [*base["unmet_conditions"], "pullback_from_recent_high_pending"]
            )
        )
        return base

    # A completed-bar retest plus rebound-volume confirmation is the earliest
    # defensible reversal observation.  It may precede VWAP/resistance reclaim,
    # but it must not inherit ENTRY_READY authority.
    early_reversal_caution = bool(
        early_reversal_setup_eligible and tactical_chase_pct <= dynamic_chase_limit_pct
    )
    if early_reversal_caution:
        entry_low = max(tactical_support, best_bid)
        entry_high = min(best_ask, move_price_by_ticks(tactical_support, 2))
        if entry_low <= entry_high:
            base["state"] = base["raw_state"] = "ENTRY_CAUTION"
            base["entry_price_low"] = entry_low
            base["entry_price_high"] = entry_high
            base["trigger"] = "confirmed_retest_early_reversal"
            base["trigger_price"] = tactical_support
            base["reasons"] = list(
                dict.fromkeys([*base["reasons"], "early_reversal_retest_confirmed"])
            )
            base["derived"]["early_reversal_caution"] = {
                "completed_bar_retest_required": True,
                "meaningful_recent_pullback_required": True,
                "recent_low_hold_bars": recent_low_age_bars,
                "ready_promotion_forbidden": True,
                "pending_confirmations": [
                    value
                    for value in (
                        "vwap_or_resistance_reclaimed",
                        "rebound_volume_confirmed",
                    )
                    if value in base["unmet_conditions"]
                ],
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "metric_contract": METRIC_CONTRACT,
            }
            _apply_nxt_aftermarket_caution_entry_scope(
                base,
                context=context,
                resistance_reclaimed=resistance_reclaimed,
                higher_high_and_low=bool(structure["higher_high_and_low"]),
            )
            narrowed_entry_high = _positive_int(base.get("entry_price_high"))
            if narrowed_entry_high is not None:
                _apply_entry_reward_risk_guard(
                    base,
                    entry_price_high=narrowed_entry_high,
                    invalidation_price=hard_invalidation,
                )
            return base

    non_relative_core_passed = all(
        passed
        for name, passed in core_checks.items()
        if name != "relative_strength_not_weak"
    )
    all_core_passed = bool(
        non_relative_core_passed and (relative_ok or relative_caution_only)
    )
    if not all_core_passed:
        latent_next_blockers: list[str] = []
        if near_recent_high and recent_runup_pct >= recent_runup_limit_pct:
            latent_next_blockers.append("recent_runup_near_rolling_high")
        if tactical_chase_pct > dynamic_chase_limit_pct:
            latent_next_blockers.append("price_above_dynamic_two_tick_chase_limit")
        base["derived"]["latent_next_blockers"] = latent_next_blockers
        base["state"] = base["raw_state"] = "WATCH"
        return base

    if (
        resistance_reclaimed
        and not vwap_reclaimed
        and isinstance(recent_resistance, int)
        and current_price > move_price_by_ticks(recent_resistance, 1)
    ):
        base["state"] = base["raw_state"] = "WATCH"
        base["unmet_conditions"].append("resistance_reclaim_pullback_pending")
        return base

    if tactical_chase_pct > dynamic_chase_limit_pct:
        base["state"] = base["raw_state"] = "NO_CHASE"
        base["reasons"] = ["price_above_dynamic_two_tick_chase_limit"]
        return base

    entry_low = max(tactical_support, best_bid)
    entry_high = min(best_ask, move_price_by_ticks(tactical_support, 2))
    if entry_high < entry_low:
        base["state"] = base["raw_state"] = "NO_CHASE"
        base["reasons"] = ["entry_range_not_available_without_chasing"]
        return base
    base["entry_price_low"] = entry_low
    base["entry_price_high"] = entry_high
    if external_risk["level"] == "HOLD":
        base["state"] = base["raw_state"] = "WATCH"
        base["entry_price_low"] = None
        base["entry_price_high"] = None
        base["unmet_conditions"].append("external_risk_hold")
    elif (
        external_risk["level"] in {"CAUTION", "DATA_LIMITED"}
        or relative_caution_only
        or flow_negative
        or flow_data_limited
        or premarket_aux_weak
        or (resistance_reclaimed and not vwap_reclaimed)
    ):
        base["state"] = base["raw_state"] = "ENTRY_CAUTION"
    else:
        base["state"] = base["raw_state"] = "ENTRY_READY"
    _apply_nxt_aftermarket_caution_entry_scope(
        base,
        context=context,
        resistance_reclaimed=resistance_reclaimed,
        higher_high_and_low=bool(structure["higher_high_and_low"]),
    )
    narrowed_entry_high = _positive_int(base.get("entry_price_high"))
    if (
        base.get("state") in {"ENTRY_CAUTION", "ENTRY_READY"}
        and narrowed_entry_high is not None
    ):
        _apply_entry_reward_risk_guard(
            base,
            entry_price_high=narrowed_entry_high,
            invalidation_price=hard_invalidation,
        )
    return base


class AdvisoryBreakRearmFilter:
    """Keep a broken support episode closed until two completed bars reclaim it."""

    ACTIONABLE = {"ENTRY_CAUTION", "ENTRY_READY"}
    REQUIRED_RECLAIM_BARS = 2

    def __init__(self) -> None:
        self.reset()

    @staticmethod
    def _scope_for(advisory: dict[str, Any]) -> str:
        observed_date = str(advisory.get("observed_at") or "")[:10]
        return f"{observed_date}:{advisory.get('session') or 'UNKNOWN'}"

    @staticmethod
    def _bar_values(latest_bar: MinuteBar | dict[str, Any] | None) -> tuple[str, int]:
        if isinstance(latest_bar, MinuteBar):
            return latest_bar.source_time, latest_bar.close
        if isinstance(latest_bar, dict):
            try:
                return str(latest_bar.get("source_time") or ""), int(
                    latest_bar.get("close") or 0
                )
            except (TypeError, ValueError):
                return "", 0
        return "", 0

    def reset(self) -> None:
        self._scope_key: str | None = None
        self._locked_support: int | None = None
        self._break_bar_source_time = ""
        self._break_kind = ""
        self._reclaim_bar_source_times: list[str] = []

    def restore(self, advisory: dict[str, Any]) -> bool:
        continuity = advisory.get("continuity")
        if not isinstance(continuity, dict):
            return False
        self._scope_key = self._scope_for(advisory)
        if continuity.get("support_break_rearm_required") is not True:
            return True
        # Snapshots written before confirmed-break provenance was introduced
        # may contain a lock created from the declarative invalidation label.
        # Do not restore those ambiguous locks.
        if continuity.get("confirmed_break_evidence") is not True:
            return False
        try:
            locked_support = int(continuity.get("locked_support") or 0)
        except (TypeError, ValueError):
            return False
        break_bar = str(continuity.get("break_bar_source_time") or "")
        reclaim_bars = continuity.get("reclaim_bar_source_times")
        if (
            locked_support <= 0
            or len(break_bar) != 14
            or not isinstance(reclaim_bars, list)
        ):
            return False
        normalized_reclaims = [
            str(value) for value in reclaim_bars if len(str(value)) == 14
        ][-self.REQUIRED_RECLAIM_BARS :]
        self._locked_support = locked_support
        self._break_bar_source_time = break_bar
        self._break_kind = str(continuity.get("break_kind") or "restored")
        self._reclaim_bar_source_times = normalized_reclaims
        return True

    def _bars_since_break(self, bar_source_time: str) -> int | None:
        if len(bar_source_time) != 14 or len(self._break_bar_source_time) != 14:
            return None
        try:
            current = datetime.strptime(bar_source_time, "%Y%m%d%H%M%S")
            broken = datetime.strptime(self._break_bar_source_time, "%Y%m%d%H%M%S")
        except ValueError:
            return None
        return max(0, int((current - broken).total_seconds() // 60))

    def snapshot(self) -> dict[str, Any]:
        """Return restart-safe widget-only continuity without market authority."""
        return {
            "support_break_rearm_required": self._locked_support is not None,
            "confirmed_break_evidence": self._locked_support is not None,
            "locked_support": self._locked_support,
            "break_kind": self._break_kind or None,
            "break_bar_source_time": self._break_bar_source_time or None,
            "bars_since_break": None,
            "reclaim_bar_count": len(self._reclaim_bar_source_times),
            "required_reclaim_bars": self.REQUIRED_RECLAIM_BARS,
            "reclaim_bar_source_times": list(self._reclaim_bar_source_times),
        }

    def apply(
        self,
        advisory: dict[str, Any],
        *,
        latest_bar: MinuteBar | dict[str, Any] | None,
    ) -> dict[str, Any]:
        result = json.loads(json.dumps(advisory, ensure_ascii=False))
        scope_key = self._scope_for(result)
        if scope_key != self._scope_key:
            self.reset()
            self._scope_key = scope_key

        bar_source_time, completed_close = self._bar_values(latest_bar)
        raw_state = str(result.get("raw_state") or result.get("state") or "")
        invalidation_kind = str(result.get("invalidation") or "")
        derived = result.get("derived")
        support = None
        if isinstance(derived, dict):
            try:
                support = int(derived.get("structural_support") or 0) or None
            except (TypeError, ValueError):
                support = None
        confirmation = (
            derived.get("invalidation_confirmation")
            if isinstance(derived, dict)
            else None
        )
        confirmed_break_evidence = bool(
            isinstance(confirmation, dict)
            and (
                confirmation.get("completed_close_break") is True
                or confirmation.get("deep_live_break") is True
            )
        )
        break_detected = bool(
            invalidation_kind == "confirmed_support_break"
            and raw_state == "AVOID"
            and confirmed_break_evidence
        )
        if break_detected and support:
            is_new_break_bar = (
                self._locked_support is None
                or support != self._locked_support
                or (bar_source_time and bar_source_time != self._break_bar_source_time)
            )
            if is_new_break_bar:
                self._locked_support = support
                self._break_bar_source_time = bar_source_time
                self._reclaim_bar_source_times = []
            self._break_kind = invalidation_kind
        elif self._locked_support and bar_source_time > self._break_bar_source_time:
            confirmed_support = bool(
                isinstance(derived, dict) and derived.get("confirmed_support")
            )
            if (
                completed_close >= self._locked_support
                and confirmed_support
                and bar_source_time not in self._reclaim_bar_source_times
            ):
                self._reclaim_bar_source_times.append(bar_source_time)
                self._reclaim_bar_source_times = self._reclaim_bar_source_times[
                    -self.REQUIRED_RECLAIM_BARS :
                ]

        rearm_satisfied = bool(
            self._locked_support
            and len(self._reclaim_bar_source_times) >= self.REQUIRED_RECLAIM_BARS
        )
        if rearm_satisfied:
            satisfied_support = self._locked_support
            self._locked_support = None
            self._break_bar_source_time = ""
            self._break_kind = ""
            self._reclaim_bar_source_times = []
            result.setdefault("reasons", []).append("post_break_rearm_satisfied")
            result["continuity"] = {
                "support_break_rearm_required": False,
                "rearm_satisfied_support": satisfied_support,
                "required_reclaim_bars": self.REQUIRED_RECLAIM_BARS,
            }
            return result

        if self._locked_support and raw_state in self.ACTIONABLE:
            result["state"] = "WATCH"
            result["raw_state"] = "WATCH"
            result["entry_price_low"] = None
            result["entry_price_high"] = None
            result.setdefault("unmet_conditions", []).append("post_break_rearm_pending")
        result["continuity"] = self.snapshot()
        result["continuity"]["bars_since_break"] = self._bars_since_break(
            bar_source_time
        )
        return result


class AdvisoryRecoveryEpisodeFilter:
    """Carry confirmed rebound evidence into the next resistance pullback."""

    MAX_VOLUME_GRACE_BARS = 3
    MAX_RECLAIM_WAIT_BARS = 3
    MAX_PULLBACK_WAIT_BARS = 3
    REQUIRED_ARM_REASONS = {
        "low_structure_confirmed",
        "rebound_volume_confirmed",
        "three_five_minute_not_down",
        "relative_strength_not_weak",
        "spread_within_two_ticks",
    }
    REQUIRED_CONTINUATION_REASONS = {
        "low_structure_confirmed",
        "three_five_minute_not_down",
        "relative_strength_not_weak",
        "spread_within_two_ticks",
    }
    NEGATIVE_VETOES = {
        "external_risk_hold",
        "recent_rest_prints_descending",
        "live_price_reversal_with_ask_pressure",
        "soft_support_break",
        "post_break_rearm_pending",
    }

    def __init__(self) -> None:
        self.reset()

    @staticmethod
    def _scope_for(advisory: dict[str, Any]) -> str:
        observed_date = str(advisory.get("observed_at") or "")[:10]
        return f"{observed_date}:{advisory.get('session') or 'UNKNOWN'}"

    @staticmethod
    def _bar_values(latest_bar: MinuteBar | dict[str, Any] | None) -> tuple[str, int]:
        return AdvisoryBreakRearmFilter._bar_values(latest_bar)

    @staticmethod
    def _bars_between(earlier: str, later: str) -> int | None:
        if len(earlier) != 14 or len(later) != 14:
            return None
        try:
            start = datetime.strptime(earlier, "%Y%m%d%H%M%S")
            end = datetime.strptime(later, "%Y%m%d%H%M%S")
        except ValueError:
            return None
        seconds = (end - start).total_seconds()
        if seconds < 0 or seconds % 60 != 0:
            return None
        return int(seconds // 60)

    def reset(self) -> None:
        self._scope_key: str | None = None
        self._support: int | None = None
        self._resistance: int | None = None
        self._volume_evidence_bar = ""
        self._reclaimed_bar = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "scope_key": self._scope_key,
            "armed": self._support is not None and self._resistance is not None,
            "support": self._support,
            "resistance": self._resistance,
            "volume_evidence_bar": self._volume_evidence_bar or None,
            "reclaimed_bar": self._reclaimed_bar or None,
            "max_volume_grace_bars": self.MAX_VOLUME_GRACE_BARS,
            "max_reclaim_wait_bars": self.MAX_RECLAIM_WAIT_BARS,
            "max_pullback_wait_bars": self.MAX_PULLBACK_WAIT_BARS,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
        }

    def restore(self, advisory: dict[str, Any]) -> bool:
        continuity = advisory.get("recovery_continuity")
        if not isinstance(continuity, dict):
            return False
        expected_scope = self._scope_for(advisory)
        if continuity.get("scope_key") != expected_scope:
            return False
        if continuity.get("armed") is not True:
            self.reset()
            self._scope_key = expected_scope
            return True
        try:
            support = int(continuity.get("support") or 0)
            resistance = int(continuity.get("resistance") or 0)
        except (TypeError, ValueError):
            return False
        volume_bar = str(continuity.get("volume_evidence_bar") or "")
        reclaimed_bar = str(continuity.get("reclaimed_bar") or "")
        if (
            support <= 0
            or resistance <= support
            or len(volume_bar) != 14
            or (reclaimed_bar and len(reclaimed_bar) != 14)
            or continuity.get("authority") != ADVISORY_AUTHORITY
            or continuity.get("runtime_effect") is not False
        ):
            return False
        reclaim_delay = (
            self._bars_between(volume_bar, reclaimed_bar) if reclaimed_bar else 0
        )
        if reclaim_delay is None or reclaim_delay > self.MAX_RECLAIM_WAIT_BARS:
            return False
        self._scope_key = expected_scope
        self._support = support
        self._resistance = resistance
        self._volume_evidence_bar = volume_bar
        self._reclaimed_bar = reclaimed_bar
        return True

    def _expire_if_needed(self, bar_source_time: str) -> None:
        if self._support is None:
            return
        volume_age = self._bars_between(self._volume_evidence_bar, bar_source_time)
        reclaim_age = self._bars_between(self._reclaimed_bar, bar_source_time)
        if volume_age is None or volume_age > self.MAX_VOLUME_GRACE_BARS:
            scope_key = self._scope_key
            self.reset()
            self._scope_key = scope_key
        elif self._reclaimed_bar and (
            reclaim_age is None or reclaim_age > self.MAX_PULLBACK_WAIT_BARS
        ):
            scope_key = self._scope_key
            self.reset()
            self._scope_key = scope_key

    def apply(
        self,
        advisory: dict[str, Any],
        *,
        current_price: int,
        bbo: dict[str, Any],
        latest_bar: MinuteBar | dict[str, Any] | None,
    ) -> dict[str, Any]:
        result = json.loads(json.dumps(advisory, ensure_ascii=False))
        scope_key = self._scope_for(result)
        if scope_key != self._scope_key:
            self.reset()
            self._scope_key = scope_key
        bar_source_time, completed_close = self._bar_values(latest_bar)
        if not bar_source_time:
            result["recovery_continuity"] = self.snapshot()
            return result

        self._expire_if_needed(bar_source_time)
        derived = result.get("derived")
        derived = derived if isinstance(derived, dict) else {}
        reasons = set(result.get("reasons") or [])
        unmet = set(result.get("unmet_conditions") or [])
        source_quality = result.get("source_quality")
        source_pass = bool(
            isinstance(source_quality, dict) and source_quality.get("status") == "PASS"
        )
        try:
            support = int(derived.get("structural_support") or 0)
            resistance = int(derived.get("recent_resistance") or 0)
            best_bid = int(bbo.get("best_bid") or 0)
            best_ask = int(bbo.get("best_ask") or 0)
        except (TypeError, ValueError):
            support = resistance = best_bid = best_ask = 0

        support_broken = bool(self._support and completed_close < self._support)
        if support_broken:
            self.reset()
            self._scope_key = scope_key
            result["recovery_continuity"] = self.snapshot()
            return result

        external_risk = result.get("external_risk")
        external_hold = bool(
            isinstance(external_risk, dict) and external_risk.get("level") == "HOLD"
        )
        if (
            not source_pass
            or external_hold
            or self.NEGATIVE_VETOES.intersection(unmet)
            or (
                self._support is not None
                and not self.REQUIRED_CONTINUATION_REASONS.issubset(reasons)
            )
        ):
            self.reset()
            self._scope_key = scope_key
            result["recovery_continuity"] = self.snapshot()
            return result
        can_arm = bool(
            source_pass
            and support > 0
            and resistance > support
            and self.REQUIRED_ARM_REASONS.issubset(reasons)
            and not external_hold
            and not self.NEGATIVE_VETOES.intersection(unmet)
        )
        if can_arm:
            if self._support is None:
                self._support = support
                self._resistance = resistance
            self._volume_evidence_bar = bar_source_time

        if self._support and self._resistance:
            arm_age = self._bars_between(self._volume_evidence_bar, bar_source_time)
            # Recovery continuity is completed-bar evidence. A forming quote may
            # touch resistance and reverse before the minute closes, so it must
            # not start the pullback window by itself.
            reclaim_seen = completed_close >= self._resistance
            if (
                not self._reclaimed_bar
                and reclaim_seen
                and arm_age is not None
                and arm_age <= self.MAX_RECLAIM_WAIT_BARS
            ):
                self._reclaimed_bar = bar_source_time

        reclaim_age = self._bars_between(self._reclaimed_bar, bar_source_time)
        volume_age = self._bars_between(self._volume_evidence_bar, bar_source_time)
        anchor = self._resistance or 0
        upper_bound = move_price_by_ticks(anchor, 2) if anchor > 0 else 0
        current_safety_pass = bool(
            source_pass
            and self.REQUIRED_CONTINUATION_REASONS.issubset(reasons)
            and not external_hold
            and not self.NEGATIVE_VETOES.intersection(unmet)
        )
        pullback_ready = bool(
            self._support
            and anchor > self._support
            and reclaim_age is not None
            and 1 <= reclaim_age <= self.MAX_PULLBACK_WAIT_BARS
            and volume_age is not None
            and volume_age <= self.MAX_VOLUME_GRACE_BARS
            and completed_close >= anchor
            and anchor <= current_price <= upper_bound
            and best_bid > 0
            and best_ask >= best_bid
            and current_safety_pass
        )
        if pullback_ready:
            entry_low = max(anchor, best_bid)
            entry_high = min(best_ask, upper_bound)
            if entry_low <= entry_high:
                invalidation_price = move_price_by_ticks(self._support, -2)
                if _apply_entry_reward_risk_guard(
                    result,
                    entry_price_high=entry_high,
                    invalidation_price=invalidation_price,
                ):
                    result["state"] = result["raw_state"] = "ENTRY_CAUTION"
                    result["entry_price_low"] = entry_low
                    result["entry_price_high"] = entry_high
                    result["trigger"] = "recovery_episode_resistance_reclaim_pullback"
                    result["trigger_price"] = anchor
                    result["invalidation"] = "confirmed_support_break"
                    result["invalidation_price"] = invalidation_price
                    result["reasons"] = list(
                        dict.fromkeys(
                            [
                                *(result.get("reasons") or []),
                                "recovery_episode_armed",
                                "recent_resistance_reclaimed",
                                "pullback_within_two_ticks",
                                "recent_rebound_volume_grace",
                            ]
                        )
                    )
                    result["unmet_conditions"] = [
                        value
                        for value in result.get("unmet_conditions") or []
                        if value
                        not in {
                            "vwap_or_resistance_reclaimed",
                            "rebound_volume_confirmed",
                            "early_reversal_rebound_volume_required",
                            "resistance_reclaim_pullback_pending",
                        }
                    ]
                    result.setdefault("derived", {})["recovery_episode"] = {
                        "support": self._support,
                        "reclaimed_resistance": anchor,
                        "volume_evidence_age_bars": volume_age,
                        "reclaim_age_bars": reclaim_age,
                        "entry_anchor": anchor,
                        "entry_upper_bound": upper_bound,
                        "authority": ADVISORY_AUTHORITY,
                        "runtime_effect": False,
                    }
        result["recovery_continuity"] = self.snapshot()
        return result


class AdvisoryPromotionFilter:
    """Require two identical actionable observations; demotions are immediate."""

    ACTIONABLE = {"ENTRY_CAUTION", "ENTRY_READY"}
    ACTIONABLE_RANK = {"ENTRY_CAUTION": 1, "ENTRY_READY": 2}
    MAX_CONFIRMATION_GAP_SEC = 25.0

    def __init__(self) -> None:
        self._scope_key: str | None = None
        self._last_raw_state: str | None = None
        self._streak = 0
        self._visible_state = "DATA_WAIT"
        self._last_observed_at: datetime | None = None

    @staticmethod
    def _scope_for(advisory: dict[str, Any]) -> str:
        observed_date = str(advisory.get("observed_at") or "")[:10]
        return f"{observed_date}:{advisory.get('session') or 'UNKNOWN'}"

    def restore(self, advisory: dict[str, Any]) -> bool:
        """Restore widget-only confirmation state from a validated snapshot."""
        raw_state = str(advisory.get("raw_state") or "")
        visible_state = str(advisory.get("state") or "")
        allowed_states = self.ACTIONABLE | {"DATA_WAIT", "WATCH", "NO_CHASE", "AVOID"}
        if raw_state not in allowed_states or visible_state not in allowed_states:
            return False
        try:
            streak = max(1, int(advisory.get("confirmation_streak") or 1))
        except (TypeError, ValueError):
            return False
        try:
            observed_at = datetime.fromisoformat(str(advisory.get("observed_at") or ""))
        except (TypeError, ValueError):
            return False
        if observed_at.tzinfo is None:
            return False
        self._scope_key = self._scope_for(advisory)
        self._last_raw_state = raw_state
        self._streak = streak
        self._visible_state = visible_state
        self._last_observed_at = _as_kst(observed_at)
        return True

    def reset(self) -> None:
        self._scope_key = None
        self._last_raw_state = None
        self._streak = 0
        self._visible_state = "DATA_WAIT"
        self._last_observed_at = None

    def apply(
        self,
        advisory: dict[str, Any],
        *,
        required_confirmations: int = 2,
        calibration_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = json.loads(json.dumps(advisory, ensure_ascii=False))
        try:
            required_confirmations = int(required_confirmations)
        except (TypeError, ValueError):
            required_confirmations = 2
        required_confirmations = max(2, min(3, required_confirmations))
        scope_key = self._scope_for(result)
        try:
            observed_at = datetime.fromisoformat(str(result.get("observed_at") or ""))
        except (TypeError, ValueError):
            observed_at = None
        if observed_at is not None and observed_at.tzinfo is not None:
            observed_at = _as_kst(observed_at)
        else:
            observed_at = None
        if scope_key != self._scope_key:
            self._scope_key = scope_key
            self._last_raw_state = None
            self._streak = 0
            self._visible_state = "DATA_WAIT"
            self._last_observed_at = None
        elif self._last_observed_at is not None and (
            observed_at is None
            or (observed_at - self._last_observed_at).total_seconds() < 0
            or (observed_at - self._last_observed_at).total_seconds()
            > self.MAX_CONFIRMATION_GAP_SEC
        ):
            self._last_raw_state = None
            self._streak = 0
            self._visible_state = "DATA_WAIT"
        raw_state = str(result.get("raw_state") or result.get("state") or "DATA_WAIT")
        if raw_state == self._last_raw_state:
            self._streak += 1
        else:
            self._last_raw_state = raw_state
            self._streak = 1
        raw_rank = self.ACTIONABLE_RANK.get(raw_state, 0)
        visible_rank = self.ACTIONABLE_RANK.get(self._visible_state, 0)
        is_unconfirmed_promotion = (
            raw_state in self.ACTIONABLE
            and raw_rank > visible_rank
            and self._streak < required_confirmations
        )
        if is_unconfirmed_promotion:
            result["state"] = (
                self._visible_state
                if self._visible_state in self.ACTIONABLE
                else "WATCH"
            )
            result.setdefault("unmet_conditions", []).append(
                "awaiting_second_10s_confirmation"
                if required_confirmations == 2
                else "awaiting_calibrated_10s_confirmation"
            )
            if result["state"] == "WATCH":
                result["entry_price_low"] = None
                result["entry_price_high"] = None
        else:
            self._visible_state = raw_state
            result["state"] = raw_state
        self._last_observed_at = observed_at
        result["confirmation_streak"] = self._streak
        result["required_actionable_confirmations"] = required_confirmations
        if isinstance(calibration_policy, dict):
            result["calibration_policy"] = {
                key: calibration_policy.get(key)
                for key in (
                    "policy_version",
                    "effective_date",
                    "source_target_date",
                    "load_status",
                    "decision",
                    "reason",
                    "authority",
                    "widget_runtime_effect",
                    "trading_runtime_effect",
                    "runtime_effect",
                )
            }
        return result


def _exit_downtrend_confirmed(bars: list[MinuteBar], horizon: int) -> bool:
    """Use completed closes only to confirm short-horizon downside direction."""
    window = _contiguous_window(bars, horizon + 1)
    if not window:
        return False
    closes = [bar.close for bar in window]
    deltas = [current - previous for previous, current in zip(closes, closes[1:])]
    return bool(
        closes[-1] < closes[0] - get_tick_size(closes[-1])
        and sum(delta < 0 for delta in deltas) >= max(2, (horizon + 1) // 2)
    )


def _entry_reward_risk_assessment(
    *, entry_price_high: int, invalidation_price: int
) -> dict[str, Any]:
    """Assess the worst recommended fill against the fixed +1% objective."""

    target_price = move_price_up_by_bps(entry_price_high, ENTRY_TARGET_BPS)
    reward_price = target_price - entry_price_high
    risk_price = entry_price_high - invalidation_price
    ratio = reward_price / risk_price if risk_price > 0 else 0.0
    return {
        "basis": "worst_recommended_entry_to_hard_invalidation",
        "entry_price": entry_price_high,
        "target_bps": ENTRY_TARGET_BPS,
        "target_price": target_price,
        "reward_price": reward_price,
        "invalidation_price": invalidation_price,
        "risk_price": risk_price,
        "reward_risk_ratio": round(ratio, 4),
        "minimum_reward_risk_ratio": ENTRY_MIN_REWARD_RISK_RATIO,
        "passed": bool(risk_price > 0 and ratio >= ENTRY_MIN_REWARD_RISK_RATIO),
        "authority": "negative_veto_only",
        "runtime_effect": False,
        "metric_contract": METRIC_CONTRACT,
    }


def _apply_entry_reward_risk_guard(
    advisory: dict[str, Any], *, entry_price_high: int, invalidation_price: int
) -> bool:
    """Keep a setup observable but non-actionable when gross reward is too small."""

    derived = advisory.setdefault("derived", {})
    assessment = _entry_reward_risk_assessment(
        entry_price_high=entry_price_high,
        invalidation_price=invalidation_price,
    )
    derived["entry_reward_risk_guard"] = assessment
    if assessment["passed"]:
        return True
    advisory["state"] = advisory["raw_state"] = "WATCH"
    advisory["entry_price_low"] = None
    advisory["entry_price_high"] = None
    advisory["unmet_conditions"] = list(
        dict.fromkeys(
            [
                *advisory.get("unmet_conditions", []),
                "entry_reward_risk_below_floor",
            ]
        )
    )
    return False


class ExitAdvisoryStateMachine:
    """Create holding-independent exit observations from completed minute bars."""

    ACTIONABLE = {"EXIT_CAUTION", "EXIT_READY"}

    def __init__(self) -> None:
        self.reset()

    @staticmethod
    def _scope_for(observed_at: datetime, context: SessionContext) -> str:
        return f"{_as_kst(observed_at).date().isoformat()}:{context.name}"

    def reset(self) -> None:
        self._scope_key: str | None = None
        self._state = "EXIT_WATCH"
        self._last_processed_bar = ""
        self._broken_support: int | None = None
        self._peak_price: int | None = None
        self._caution_bar = ""
        self._ready_bar = ""
        self._pending_bars = 0
        self._reclaim_bars = 0
        self._caution_kind: str | None = None
        self._lowest_since_ready: int | None = None
        self._bars_without_new_low = 0
        self._rearm_support: int | None = None
        self._rearm_closes = 0
        self._rearm_age_bars = 0
        self._cancel_reason: str | None = None
        self._entry_was_actionable = False
        self._entry_episode_id: str | None = None

    def restore(self, exit_advisory: object) -> bool:
        if not isinstance(exit_advisory, dict):
            return False
        continuity = exit_advisory.get("continuity")
        if not isinstance(continuity, dict):
            return False
        scope_key = str(continuity.get("scope_key") or "")
        reported_state = str(exit_advisory.get("state") or "")
        continuity_state = str(continuity.get("state") or "")
        restorable_states = {
            "EXIT_WATCH",
            "EXIT_CAUTION",
            "EXIT_READY",
            "EXIT_CANCELLED",
        }
        if reported_state == "DATA_WAIT":
            state = continuity_state
        elif reported_state in restorable_states and continuity_state in {
            "",
            reported_state,
        }:
            state = reported_state
        else:
            return False
        last_processed_bar = str(continuity.get("last_processed_bar") or "")
        if not scope_key or state not in restorable_states:
            return False
        if last_processed_bar and len(last_processed_bar) != 14:
            return False
        self._scope_key = scope_key
        self._state = state
        self._last_processed_bar = last_processed_bar
        for attribute, key in (
            ("_broken_support", "broken_support"),
            ("_peak_price", "peak_price"),
            ("_lowest_since_ready", "lowest_since_ready"),
            ("_rearm_support", "rearm_support"),
        ):
            try:
                value = int(continuity.get(key) or 0) or None
            except (TypeError, ValueError):
                self.reset()
                return False
            setattr(self, attribute, value)
        self._caution_bar = str(continuity.get("caution_bar") or "")
        self._ready_bar = str(continuity.get("ready_bar") or "")
        try:
            self._pending_bars = max(0, int(continuity.get("pending_bars") or 0))
            self._reclaim_bars = max(0, int(continuity.get("reclaim_bars") or 0))
            self._bars_without_new_low = max(
                0, int(continuity.get("bars_without_new_low") or 0)
            )
            self._rearm_closes = max(0, int(continuity.get("rearm_closes") or 0))
            self._rearm_age_bars = max(0, int(continuity.get("rearm_age_bars") or 0))
        except (TypeError, ValueError):
            self.reset()
            return False
        self._cancel_reason = str(continuity.get("cancel_reason") or "") or None
        self._caution_kind = str(continuity.get("caution_kind") or "") or None
        self._entry_was_actionable = bool(continuity.get("entry_was_actionable"))
        self._entry_episode_id = str(continuity.get("entry_episode_id") or "") or None
        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self._state,
            "scope_key": self._scope_key,
            "last_processed_bar": self._last_processed_bar or None,
            "broken_support": self._broken_support,
            "peak_price": self._peak_price,
            "caution_bar": self._caution_bar or None,
            "ready_bar": self._ready_bar or None,
            "pending_bars": self._pending_bars,
            "caution_kind": self._caution_kind,
            "reclaim_bars": self._reclaim_bars,
            "lowest_since_ready": self._lowest_since_ready,
            "bars_without_new_low": self._bars_without_new_low,
            "rearm_support": self._rearm_support,
            "rearm_closes": self._rearm_closes,
            "rearm_age_bars": self._rearm_age_bars,
            "rearm_max_bars": EXIT_REARM_MAX_BARS,
            "cancel_reason": self._cancel_reason,
            "entry_was_actionable": self._entry_was_actionable,
            "entry_episode_id": self._entry_episode_id,
        }

    def _clear_episode(self) -> None:
        self._broken_support = None
        self._peak_price = None
        self._caution_bar = ""
        self._ready_bar = ""
        self._pending_bars = 0
        self._reclaim_bars = 0
        self._caution_kind = None
        self._lowest_since_ready = None
        self._bars_without_new_low = 0

    def reject_current_entry_episode_reset(self) -> bool:
        """Remove only a same-cycle entry link rejected by final arbitration."""
        if not self._entry_was_actionable or self._entry_episode_id is None:
            return False
        self._entry_was_actionable = False
        self._entry_episode_id = None
        return True

    def _observe_entry_episode(
        self,
        entry_advisory: dict[str, Any] | None,
        latest: MinuteBar,
    ) -> bool:
        """Release stale exit continuity when a visible entry episode opens."""
        state = str((entry_advisory or {}).get("state") or "")
        actionable = state in {"ENTRY_CAUTION", "ENTRY_READY"}
        opened = actionable and not self._entry_was_actionable
        self._entry_was_actionable = actionable
        if not opened:
            return False
        self._entry_episode_id = f"{self._scope_key}:{latest.source_time}"
        self._state = "EXIT_WATCH"
        self._cancel_reason = None
        self._clear_episode()
        self._rearm_support = None
        self._rearm_closes = 0
        self._rearm_age_bars = 0
        return True

    @staticmethod
    def _valid_until(observed_at: datetime, context: SessionContext) -> str:
        now = _as_kst(observed_at)
        end_of_day = datetime.combine(now.date(), NXT_AFTERMARKET_END, tzinfo=KST)
        session_end = (
            datetime.combine(now.date(), context.end, tzinfo=KST)
            if context.end is not None
            else end_of_day
        )
        return min(now + timedelta(seconds=60), session_end, end_of_day).isoformat()

    def _base_payload(
        self,
        *,
        observed_at: datetime,
        context: SessionContext,
        source_quality: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "state": self._state,
            "raw_state": self._state,
            "session": context.name,
            "reference_exit_price": None,
            "peak_price": self._peak_price,
            "peak_drawdown_pct": None,
            "broken_support": self._broken_support,
            "session_vwap": None,
            "dynamic_drawdown_band": None,
            "reasons": [],
            "unmet_conditions": [],
            "observed_at": _as_kst(observed_at).isoformat(),
            "valid_until": self._valid_until(observed_at, context),
            "source_quality": source_quality,
            "holding_independent": True,
            "future_prediction": False,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "metric_contract": METRIC_CONTRACT,
            "continuity": self.snapshot(),
        }

    def apply(
        self,
        *,
        observed_at: datetime,
        context: SessionContext,
        bars: list[MinuteBar],
        bbo: dict[str, Any],
        source_quality: dict[str, Any],
        entry_advisory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        scope_key = self._scope_for(observed_at, context)
        if scope_key != self._scope_key:
            self.reset()
            self._scope_key = scope_key
        minimum_bars = max(6, context.minimum_bars)
        if source_quality.get("status") != "PASS" or len(bars) < minimum_bars:
            payload = self._base_payload(
                observed_at=observed_at,
                context=context,
                source_quality=source_quality,
            )
            payload["state"] = payload["raw_state"] = "DATA_WAIT"
            payload["unmet_conditions"] = list(
                dict.fromkeys(
                    [
                        *source_quality.get("issues", []),
                        *(
                            ["exit_minimum_bars_not_met"]
                            if len(bars) < minimum_bars
                            else []
                        ),
                    ]
                )
            )
            return payload
        contiguous = _contiguous_window(bars, minimum_bars)
        if not contiguous:
            payload = self._base_payload(
                observed_at=observed_at,
                context=context,
                source_quality=source_quality,
            )
            payload["state"] = payload["raw_state"] = "DATA_WAIT"
            payload["unmet_conditions"] = ["exit_completed_bars_not_contiguous"]
            return payload

        latest = bars[-1]
        entry_episode_reset = self._observe_entry_episode(entry_advisory, latest)
        change_window = bars[-(EXIT_VOLATILITY_LOOKBACK_BARS + 1) :]
        recent_changes = [
            abs(current.close - previous.close)
            for previous, current in zip(change_window, change_window[1:])
        ]
        median_change = float(median(recent_changes)) if recent_changes else 0.0
        tick_size = get_tick_size(latest.close)
        raw_band = max(tick_size * 2, median_change * 2)
        dynamic_band = max(tick_size, int(math.ceil(raw_band / tick_size) * tick_size))
        peak_price = max(bar.high for bar in bars[-EXIT_PEAK_LOOKBACK_BARS:])
        prior_support = min(
            bar.low for bar in bars[-(EXIT_SUPPORT_LOOKBACK_BARS + 1) : -1]
        )
        session_vwap = _session_vwap(bars)
        trend_3m_down = _exit_downtrend_confirmed(bars, 3)
        trend_5m_down = _exit_downtrend_confirmed(bars, 5)
        peak_departed = peak_price - latest.close >= dynamic_band
        support_broken = latest.close < prior_support
        below_vwap = bool(session_vwap and latest.close < session_vwap)
        previous = bars[-2]
        full_breakdown_setup = bool(
            peak_departed
            and support_broken
            and below_vwap
            and (trend_3m_down or trend_5m_down)
        )
        local_peak_rollover = bool(
            peak_departed
            and latest.high < peak_price
            and latest.close < previous.close
            and latest.close < latest.open
        )
        caution_setup = full_breakdown_setup or local_peak_rollover

        is_new_bar = latest.source_time != self._last_processed_bar
        continuity_gap_reset = False
        if is_new_bar and self._last_processed_bar:
            try:
                current_bar_time = datetime.strptime(latest.source_time, "%Y%m%d%H%M%S")
                previous_bar_time = datetime.strptime(
                    self._last_processed_bar, "%Y%m%d%H%M%S"
                )
                continuity_gap_reset = (
                    current_bar_time - previous_bar_time
                ).total_seconds() != 60
            except ValueError:
                continuity_gap_reset = True
            if continuity_gap_reset:
                self._state = "EXIT_WATCH"
                self._cancel_reason = None
                self._clear_episode()
                self._rearm_support = None
                self._rearm_closes = 0
                self._rearm_age_bars = 0
        if is_new_bar:
            if self._state == "EXIT_READY" and self._broken_support:
                if (
                    self._lowest_since_ready is None
                    or latest.low < self._lowest_since_ready
                ):
                    self._lowest_since_ready = latest.low
                    self._bars_without_new_low = 0
                else:
                    self._bars_without_new_low += 1
                self._reclaim_bars = (
                    self._reclaim_bars + 1 if latest.close > self._broken_support else 0
                )
                if self._reclaim_bars >= 2:
                    self._state = "EXIT_CANCELLED"
                    self._cancel_reason = "broken_support_reclaimed_two_bars"
                    self._clear_episode()
                    self._entry_episode_id = None
                    self._rearm_support = None
                    self._rearm_closes = 0
                    self._rearm_age_bars = 0
                elif self._bars_without_new_low >= EXIT_NO_NEW_LOW_CANCEL_BARS:
                    rearm_support = self._broken_support
                    self._state = "EXIT_CANCELLED"
                    self._cancel_reason = "no_new_low_for_five_completed_bars"
                    self._clear_episode()
                    self._entry_episode_id = None
                    self._rearm_support = rearm_support
                    self._rearm_closes = 0
                    self._rearm_age_bars = 0
            elif self._state == "EXIT_CAUTION" and self._broken_support:
                self._pending_bars += 1
                failed_reclaim = bool(
                    latest.high >= self._broken_support
                    and latest.close < self._broken_support
                )
                if self._caution_kind == "local_peak_rollover":
                    continuation = bool(
                        peak_departed
                        and latest.close < previous.close
                        and trend_3m_down
                        and latest.high < (self._peak_price or peak_price)
                    )
                    cancel_caution = bool(
                        (self._peak_price and latest.close >= self._peak_price)
                        or self._pending_bars >= EXIT_LOCAL_PEAK_PENDING_MAX_BARS
                    )
                else:
                    continuation = bool(
                        latest.close < self._broken_support
                        and trend_3m_down
                        and trend_5m_down
                        and (latest.close <= previous.close or failed_reclaim)
                    )
                    cancel_caution = bool(
                        latest.close >= self._broken_support
                        or self._pending_bars >= EXIT_PENDING_MAX_BARS
                    )
                if continuation:
                    self._state = "EXIT_READY"
                    self._ready_bar = latest.source_time
                    self._lowest_since_ready = latest.low
                    self._bars_without_new_low = 0
                    self._reclaim_bars = 0
                elif cancel_caution:
                    self._state = "EXIT_WATCH"
                    self._cancel_reason = None
                    self._clear_episode()
            else:
                if self._state == "EXIT_CANCELLED":
                    self._state = "EXIT_WATCH"
                    self._cancel_reason = None
                if self._rearm_support:
                    self._rearm_age_bars += 1
                    self._rearm_closes = (
                        self._rearm_closes + 1
                        if latest.close >= self._rearm_support
                        else 0
                    )
                    if (
                        self._rearm_closes >= 2
                        or self._rearm_age_bars >= EXIT_REARM_MAX_BARS
                    ):
                        self._rearm_support = None
                        self._rearm_closes = 0
                        self._rearm_age_bars = 0
                elif caution_setup:
                    self._state = "EXIT_CAUTION"
                    self._broken_support = prior_support
                    self._peak_price = peak_price
                    self._caution_bar = latest.source_time
                    self._pending_bars = 0
                    self._caution_kind = (
                        "full_session_breakdown"
                        if full_breakdown_setup
                        else "local_peak_rollover"
                    )
                    self._cancel_reason = None
            self._last_processed_bar = latest.source_time

        payload = self._base_payload(
            observed_at=observed_at,
            context=context,
            source_quality=source_quality,
        )
        payload["session_vwap"] = session_vwap
        payload["dynamic_drawdown_band"] = dynamic_band
        payload["trend_3m_down"] = trend_3m_down
        payload["trend_5m_down"] = trend_5m_down
        payload["continuity_gap_reset"] = continuity_gap_reset
        payload["entry_episode_reset"] = entry_episode_reset
        payload["local_peak_rollover"] = local_peak_rollover
        payload["full_session_breakdown"] = full_breakdown_setup
        payload["continuity"] = self.snapshot()
        if self._peak_price:
            payload["peak_drawdown_pct"] = round(
                ((self._peak_price - latest.close) / self._peak_price) * 100, 4
            )
        if self._state in self.ACTIONABLE:
            payload["reference_exit_price"] = _positive_int(bbo.get("best_bid"))
            if self._caution_kind == "local_peak_rollover":
                payload["reasons"] = [
                    "rolling_peak_drawdown",
                    "completed_bar_lower_high",
                    "completed_red_bar_after_peak",
                    "local_support_break_confirmation_pending",
                ]
            else:
                payload["reasons"] = [
                    "rolling_peak_drawdown",
                    "prior_five_bar_support_broken",
                    "below_session_vwap",
                    "three_or_five_minute_down",
                ]
            if self._state == "EXIT_READY":
                if self._caution_kind == "local_peak_rollover":
                    payload["reasons"] = [
                        "rolling_peak_drawdown",
                        "completed_bar_lower_high",
                        "completed_red_bar_after_peak",
                        "local_peak_rollover_continued",
                        "three_minute_down_confirmed",
                    ]
                else:
                    payload["reasons"].extend(
                        [
                            "broken_support_reclaim_failed",
                            "three_and_five_minute_down",
                        ]
                    )
        elif self._state == "EXIT_CANCELLED":
            payload["reasons"] = [self._cancel_reason or "exit_signal_cancelled"]
        else:
            checks = {
                "rolling_peak_drawdown_pending": peak_departed,
                "prior_five_bar_support_intact": support_broken,
                "session_vwap_not_broken": below_vwap,
                "downtrend_not_confirmed": trend_3m_down or trend_5m_down,
            }
            payload["unmet_conditions"] = [
                name for name, passed in checks.items() if not passed
            ]
            if self._rearm_support:
                payload["unmet_conditions"].insert(0, "exit_rearm_pending")
        return payload


def _exit_contrarian_reversal_observation(
    exit_advisory: dict[str, Any], bars: list[MinuteBar]
) -> dict[str, Any]:
    """Interpret an exit episode as a separate, non-actionable reversal watch."""

    result: dict[str, Any] = {
        "state": "NOT_APPLICABLE",
        "reasons": [],
        "unmet_conditions": [],
        "direct_entry_authority": False,
        "authority": "widget_advisory_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": EXIT_REVERSAL_METRIC_CONTRACT,
    }
    source_quality = exit_advisory.get("source_quality") or {}
    if source_quality.get("status") != "PASS" or len(bars) < 2:
        result["state"] = "DATA_WAIT"
        result["unmet_conditions"] = ["fresh_completed_reversal_evidence_missing"]
        return result
    state = str(exit_advisory.get("state") or "")
    continuity = exit_advisory.get("continuity") or {}
    cancel_reason = str(
        continuity.get("cancel_reason")
        or next(iter(exit_advisory.get("reasons") or []), "")
    )
    if state == "EXIT_CANCELLED" and cancel_reason == (
        "broken_support_reclaimed_two_bars"
    ):
        result["state"] = "REVERSAL_CONFIRMED"
        result["reasons"] = [cancel_reason]
        return result
    if state == "EXIT_CANCELLED" and cancel_reason == (
        "no_new_low_for_five_completed_bars"
    ):
        result["state"] = "REVERSAL_WATCH"
        result["reasons"] = [cancel_reason, "support_reclaim_still_required"]
        return result
    if state != "EXIT_READY":
        result["unmet_conditions"] = ["exit_ready_episode_not_active"]
        return result

    latest = bars[-1]
    previous = bars[-2]
    ready_bar = str(continuity.get("ready_bar") or "")
    try:
        bars_without_new_low = int(continuity.get("bars_without_new_low") or 0)
        reclaim_bars = int(continuity.get("reclaim_bars") or 0)
    except (TypeError, ValueError):
        result["state"] = "DATA_WAIT"
        result["unmet_conditions"] = ["exit_continuity_invalid"]
        return result
    result.update(
        {
            "ready_bar": ready_bar or None,
            "latest_bar": latest.source_time,
            "bars_without_new_low": bars_without_new_low,
            "reclaim_bars": reclaim_bars,
        }
    )
    if latest.source_time == ready_bar:
        result["state"] = "WAIT_CONFIRMATION"
        result["unmet_conditions"] = ["first_post_exit_ready_bar_pending"]
        return result
    recovery_bar = bool(
        bars_without_new_low >= 1
        and latest.close >= latest.open
        and latest.close > previous.close
    )
    if recovery_bar:
        result["state"] = "REVERSAL_WATCH"
        result["reasons"] = [
            "no_new_low_after_exit_ready",
            "completed_recovery_bar",
        ]
        if reclaim_bars:
            result["reasons"].append("broken_support_reclaim_started")
        return result
    if bars_without_new_low == 0:
        result["state"] = "CONTINUATION_RISK"
        result["reasons"] = ["new_low_after_exit_ready"]
        return result
    result["state"] = "WAIT_CONFIRMATION"
    result["unmet_conditions"] = ["completed_recovery_bar_not_confirmed"]
    return result


def _regular_flow_recoverable_for_aftermarket(
    flow: dict[str, Any], observed_at: datetime
) -> bool:
    """Accept a complete same-day KRX close snapshot as frozen provenance."""
    if not flow.get("foreign_available") or not flow.get("program_available"):
        return False
    now = _as_kst(observed_at)
    source_times: list[datetime] = []
    for field in ("foreign_source_observed_at", "program_source_observed_at"):
        try:
            source_time = datetime.fromisoformat(str(flow.get(field) or ""))
        except (TypeError, ValueError):
            return False
        if source_time.tzinfo is None:
            return False
        source_times.append(_as_kst(source_time))
    return all(
        source_time.date() == now.date()
        and source_time <= now
        and source_time.time().replace(tzinfo=None) <= KRX_END
        for source_time in source_times
    )


class KiwoomReadOnlyClient:
    """Small exact-contract REST client with no auth lifecycle mutation."""

    def __init__(
        self,
        token: str,
        *,
        session: requests.Session | None = None,
        budget: "ReadOnlyRequestBudget | None" = None,
    ) -> None:
        self.token = token
        self.session = session or requests.Session()
        self.budget = budget

    def post(
        self,
        path: str,
        api_id: str,
        payload: dict[str, str],
        *,
        optional: bool = False,
    ) -> dict[str, Any]:
        if (path, api_id) not in READ_ONLY_KIWOOM_REQUESTS:
            raise RuntimeError(f"forbidden_widget_kiwoom_request:{api_id}:{path}")
        if self.budget is not None:
            self.budget.acquire(optional=optional)
        active_token = kiwoom_utils.resolve_kiwoom_request_token(self.token)
        if active_token:
            self.token = active_token
        response = self.session.post(
            kiwoom_utils.get_api_url(path),
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {active_token}",
                "api-id": api_id,
            },
            json=payload,
            timeout=(5, 10),
        )
        if getattr(response, "status_code", None) == 429 and self.budget is not None:
            self.budget.note_rate_limited()
        response.raise_for_status()
        data = response.json()
        try:
            return_code = int(data["return_code"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"{api_id}_return_code_missing") from exc
        if return_code != 0:
            raise RuntimeError(f"{api_id}_rejected_{return_code}")
        return data


class ReadOnlyRequestBudget:
    """Collector-local budget; it never mutates the trading bot limiter."""

    def __init__(self, max_requests_per_minute: int = COLLECTOR_REQUESTS_PER_MINUTE):
        self.max_requests_per_minute = max(3, int(max_requests_per_minute))
        self._requests: deque[float] = deque()
        self._cooldown_until = 0.0
        self.total_request_count = 0
        self.rate_limit_count = 0

    def _prune(self, now: float) -> None:
        while self._requests and now - self._requests[0] >= 60.0:
            self._requests.popleft()

    def acquire(self, *, optional: bool) -> None:
        now = time.monotonic()
        self._prune(now)
        if now < self._cooldown_until:
            raise RuntimeError("widget_kiwoom_429_cooldown")
        reserve = 2 if optional else 0
        if len(self._requests) >= self.max_requests_per_minute - reserve:
            raise RuntimeError("widget_request_budget_exhausted")
        self._requests.append(now)
        self.total_request_count += 1

    def note_rate_limited(self) -> None:
        self.rate_limit_count += 1
        self._cooldown_until = max(self._cooldown_until, time.monotonic() + 30.0)

    def snapshot(self) -> dict[str, int]:
        now = time.monotonic()
        self._prune(now)
        return {
            "max_requests_per_minute": self.max_requests_per_minute,
            "requests_in_last_minute": len(self._requests),
            "remaining_requests": max(
                0, self.max_requests_per_minute - len(self._requests)
            ),
            "total_request_count": self.total_request_count,
            "rate_limit_count": self.rate_limit_count,
        }


def _parse_bbo(payload: dict[str, Any], observed_at: datetime) -> dict[str, Any]:
    return {
        "best_bid": _positive_int(payload.get("buy_fpr_bid")),
        "best_ask": _positive_int(payload.get("sel_fpr_bid")),
        "best_bid_qty": _positive_int(payload.get("buy_fpr_req")),
        "best_ask_qty": _positive_int(payload.get("sel_fpr_req")),
        "received_at": _as_kst(observed_at).isoformat(),
        "age_sec": 0.0,
        "source": "kiwoom_ka10004_response_received_time",
        "raw_bid_time": str(payload.get("bid_req_base_tm") or "").strip() or None,
        "raw_bid_time_authority": "provenance_only_not_freshness",
    }


def _recent_trade_negative_veto(payload: dict[str, Any]) -> bool:
    rows = payload.get("cntr_infr") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return False
    prices = [
        price
        for row in rows[:3]
        if isinstance(row, dict)
        and (price := _positive_int(row.get("cur_prc"))) is not None
    ]
    # Official ka10003 is newest first.  This is a negative veto only; an
    # ascending sequence never creates positive entry authority.
    return len(prices) == 3 and prices[0] < prices[1] < prices[2]


def _intraday_source_time(value: object, observed_at: datetime) -> datetime | None:
    raw = str(value or "").strip()
    if not raw.isdigit() or len(raw) not in {4, 6}:
        return None
    try:
        clock = datetime.strptime(raw.ljust(6, "0"), "%H%M%S").time()
    except ValueError:
        return None
    return datetime.combine(_as_kst(observed_at).date(), clock, tzinfo=KST)


def _parse_flow(
    investor_payload: dict[str, Any] | None,
    program_payload: dict[str, Any] | None,
    *,
    context: SessionContext,
    observed_at: datetime,
) -> dict[str, Any]:
    if context.name != "KRX_REGULAR":
        return {
            "status": "FROZEN_OR_NOT_APPLICABLE",
            "foreign_nonworsening": False,
            "program_nonworsening": False,
            "source_session": "KRX_REGULAR",
            "live_for_current_session": False,
        }
    investor_rows = (
        investor_payload.get("opmr_invsr_trde_chart", [])
        if isinstance(investor_payload, dict)
        else []
    )
    investor_rows = sorted(
        [row for row in investor_rows if isinstance(row, dict)],
        key=lambda row: str(row.get("tm") or ""),
    )
    foreign_values = [
        value
        for row in investor_rows[-2:]
        if (value := _signed_int(row.get("frgnr_invsr"))) is not None
    ]
    foreign_nonworsening = (
        len(foreign_values) >= 2 and foreign_values[-1] >= foreign_values[-2]
    )
    foreign_available = len(foreign_values) >= 2
    program_rows = (
        program_payload.get("stk_tm_prm_trde_trnsn", [])
        if isinstance(program_payload, dict)
        else []
    )
    program_rows = sorted(
        [row for row in program_rows if isinstance(row, dict)],
        key=lambda row: str(row.get("tm") or ""),
    )
    program_latest = program_rows[-1] if program_rows else {}
    program_net = _signed_int(program_latest.get("prm_netprps_amt"))
    program_delta = _signed_int(program_latest.get("prm_netprps_amt_irds"))
    program_nonworsening = bool(
        (program_net is not None and program_net >= 0)
        or (program_delta is not None and program_delta >= 0)
    )
    program_available = program_net is not None or program_delta is not None
    foreign_source_time = _intraday_source_time(
        investor_rows[-1].get("tm") if investor_rows else None, observed_at
    )
    program_source_time = _intraday_source_time(
        program_rows[-1].get("tm") if program_rows else None, observed_at
    )
    foreign_source_age_sec = (
        (_as_kst(observed_at) - foreign_source_time).total_seconds()
        if foreign_source_time is not None
        else None
    )
    program_source_age_sec = (
        (_as_kst(observed_at) - program_source_time).total_seconds()
        if program_source_time is not None
        else None
    )
    both_sources_fresh = bool(
        foreign_available
        and program_available
        and foreign_source_age_sec is not None
        and program_source_age_sec is not None
        and 0 <= foreign_source_age_sec <= FLOW_STALE_SEC
        and 0 <= program_source_age_sec <= FLOW_STALE_SEC
    )
    source_times = [
        value
        for value in (foreign_source_time, program_source_time)
        if value is not None
    ]
    source_observed_at = max(source_times).isoformat() if source_times else None
    source_age_sec = (
        max(foreign_source_age_sec, program_source_age_sec)
        if foreign_source_age_sec is not None and program_source_age_sec is not None
        else None
    )
    if foreign_available and program_available:
        status = "OBSERVED" if both_sources_fresh else "STALE"
    elif investor_rows or program_rows:
        status = "PARTIAL"
    else:
        status = "UNAVAILABLE"
    return {
        "status": status,
        "foreign_available": foreign_available,
        "foreign_nonworsening": foreign_nonworsening,
        "foreign_latest": foreign_values[-1] if foreign_values else None,
        "program_nonworsening": program_nonworsening,
        "program_available": program_available,
        "program_net_amount": program_net,
        "program_delta_amount": program_delta,
        "observed_at": _as_kst(observed_at).isoformat(),
        "source_observed_at": source_observed_at,
        "foreign_source_observed_at": (
            foreign_source_time.isoformat() if foreign_source_time else None
        ),
        "program_source_observed_at": (
            program_source_time.isoformat() if program_source_time else None
        ),
        "foreign_source_age_sec": (
            round(foreign_source_age_sec, 3)
            if foreign_source_age_sec is not None
            else None
        ),
        "program_source_age_sec": (
            round(program_source_age_sec, 3)
            if program_source_age_sec is not None
            else None
        ),
        "source_age_sec": (
            round(source_age_sec, 3) if source_age_sec is not None else None
        ),
        "source_session": "KRX_REGULAR",
        "live_for_current_session": True,
    }


def _freeze_regular_flow(
    regular_flow: dict[str, Any], observed_at: datetime
) -> dict[str, Any]:
    if not regular_flow:
        return {
            "status": "FROZEN_REGULAR_SESSION_UNAVAILABLE",
            "foreign_nonworsening": False,
            "program_nonworsening": False,
            "source_session": "KRX_REGULAR",
            "live_for_current_session": False,
            "frozen_at": _as_kst(observed_at).isoformat(),
            "last_live_observed_at": None,
        }
    return {
        **regular_flow,
        "status": "FROZEN_REGULAR_SESSION",
        "live_for_current_session": False,
        "frozen_at": _as_kst(observed_at).isoformat(),
        "last_live_observed_at": regular_flow.get("source_observed_at")
        or regular_flow.get("observed_at"),
    }


def _observation_is_same_day(payload: dict[str, Any], observed_at: datetime) -> bool:
    observed_date = str(payload.get("observed_at") or "")[:10]
    return observed_date == _as_kst(observed_at).date().isoformat()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    os.replace(temporary, path)


def _apply_entry_exit_conflict_guard(
    advisory: dict[str, Any], exit_advisory: dict[str, Any]
) -> bool:
    """Reject a newly opened entry when the same observation warns to exit."""
    entry_state = str(advisory.get("state") or "")
    exit_state = str(exit_advisory.get("state") or "")
    same_cycle_entry = exit_advisory.get("entry_episode_reset") is True
    blocked = bool(
        entry_state in {"ENTRY_CAUTION", "ENTRY_READY"}
        and exit_state in ExitAdvisoryStateMachine.ACTIONABLE
        and same_cycle_entry
    )
    derived = advisory.get("derived")
    if not isinstance(derived, dict):
        derived = {}
        advisory["derived"] = derived
    derived["entry_exit_conflict_guard"] = {
        "blocked": blocked,
        "entry_state": entry_state,
        "exit_state": exit_state,
        "same_cycle_entry_episode": same_cycle_entry,
        "policy": "new_entry_forbidden_during_same_observation_exit_warning",
        "authority": "negative_veto_only",
        "runtime_effect": False,
        "metric_contract": METRIC_CONTRACT,
    }
    if not blocked:
        return False
    advisory["state"] = advisory["raw_state"] = "WATCH"
    advisory["entry_price_low"] = None
    advisory["entry_price_high"] = None
    advisory["trigger"] = "entry_exit_conflict_wait"
    advisory["confirmation_streak"] = 1
    unmet_conditions = advisory.get("unmet_conditions")
    unmet_conditions = unmet_conditions if isinstance(unmet_conditions, list) else []
    advisory["unmet_conditions"] = list(
        dict.fromkeys(
            [
                *unmet_conditions,
                "same_observation_exit_warning_active",
            ]
        )
    )
    return True


class ObservationRecorder:
    def __init__(
        self,
        directory: Path,
        *,
        retention_days: int = 30,
        file_prefix: str = "samsung_widget_advisory",
    ) -> None:
        self.directory = directory
        self.retention_days = max(1, int(retention_days))
        normalized_prefix = str(file_prefix or "").strip()
        if not normalized_prefix or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789_"
            for character in normalized_prefix
        ):
            raise ValueError("invalid_observation_file_prefix")
        self.file_prefix = normalized_prefix
        self._last_state: str | None = None
        self._last_exit_state: str | None = None
        self._last_minute: str | None = None
        self._loaded_day: str | None = None

    def _restore_current_day(self, target: Path, day_key: str) -> None:
        self._last_state = None
        self._last_exit_state = None
        self._last_minute = None
        self._loaded_day = day_key
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except OSError:
            return
        for line in reversed(lines):
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            advisory = row.get("advisory") or {}
            exit_advisory = row.get("exit_advisory") or {}
            state = str(advisory.get("state") or "").strip()
            exit_state = str(exit_advisory.get("state") or "DATA_WAIT").strip()
            observed_at = str(row.get("observed_at_kst") or "")
            if not state or not observed_at.startswith(
                f"{day_key[:4]}-{day_key[4:6]}-{day_key[6:8]}"
            ):
                continue
            self._last_state = state
            self._last_exit_state = exit_state
            try:
                parsed = datetime.fromisoformat(observed_at)
            except ValueError:
                return
            self._last_minute = _as_kst(parsed).strftime("%Y%m%d%H%M")
            return

    def record(self, payload: dict[str, Any], observed_at: datetime) -> None:
        day_key = _as_kst(observed_at).strftime("%Y%m%d")
        target = self.directory / f"{self.file_prefix}_{day_key}.jsonl"
        if self._loaded_day != day_key:
            self._restore_current_day(target, day_key)
        advisory = payload.get("advisory") or {}
        exit_advisory = payload.get("exit_advisory") or {}
        state = str(advisory.get("state") or "DATA_WAIT")
        exit_state = str(exit_advisory.get("state") or "DATA_WAIT")
        minute = _as_kst(observed_at).strftime("%Y%m%d%H%M")
        previous_state = self._last_state
        previous_exit_state = self._last_exit_state
        state_changed = state != previous_state
        exit_state_changed = exit_state != previous_exit_state
        minute_changed = minute != self._last_minute
        if not state_changed and not exit_state_changed and not minute_changed:
            return
        self._last_state = state
        self._last_exit_state = exit_state
        self._last_minute = minute
        self.directory.mkdir(parents=True, exist_ok=True)
        row = {
            "observed_at_kst": _as_kst(observed_at).isoformat(),
            "current_price": payload.get("current_price"),
            "market_venue": payload.get("market_venue"),
            "market_session": advisory.get("session") or payload.get("market_session"),
            "legacy_market_session": payload.get("market_session"),
            "observation_kind": (
                "state_transition"
                if state_changed
                else "exit_state_transition" if exit_state_changed else "minute_summary"
            ),
            "previous_advisory_state": previous_state,
            "previous_exit_advisory_state": previous_exit_state,
            "latest_completed_bar": (payload.get("observation") or {}).get(
                "latest_completed_bar"
            ),
            "advisory": advisory,
            "exit_advisory": exit_advisory,
            "metric_contract": METRIC_CONTRACT,
        }
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        cutoff = _as_kst(observed_at).date() - timedelta(days=self.retention_days)
        for path in self.directory.glob(f"{self.file_prefix}_*.jsonl"):
            raw_date = path.stem.rsplit("_", 1)[-1]
            try:
                artifact_date = datetime.strptime(raw_date, "%Y%m%d").date()
            except ValueError:
                continue
            if artifact_date < cutoff:
                try:
                    path.unlink()
                except OSError:
                    pass


class SamsungWidgetCollector:
    def __init__(
        self,
        *,
        snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
        observation_dir: Path = DEFAULT_OBSERVATION_DIR,
        external_provider: ExternalMarketProvider | None = None,
        request_session: requests.Session | None = None,
        entry_notifier: SamsungWidgetEntryTelegramNotifier | None = None,
        calibration_policy_loader: WidgetCalibrationPolicyLoader | None = None,
    ) -> None:
        self.snapshot_path = snapshot_path
        self.external_provider = external_provider or YahooExternalMarketProvider()
        self.request_session = request_session
        self.entry_notifier = entry_notifier
        self.calibration_policy_loader = (
            calibration_policy_loader or WidgetCalibrationPolicyLoader()
        )
        self.request_budget = ReadOnlyRequestBudget()
        self.break_rearm_filter = AdvisoryBreakRearmFilter()
        self.recovery_episode_filter = AdvisoryRecoveryEpisodeFilter()
        self.promotion_filter = AdvisoryPromotionFilter()
        self.exit_state_machine = ExitAdvisoryStateMachine()
        self.recorder = ObservationRecorder(observation_dir)
        self._minute_cache: dict[str, Any] = {}
        self._relative_cache: dict[str, Any] = {}
        self._relative_window_cache: dict[str, Any] = {}
        self._flow_cache: dict[str, Any] = {}
        self._external_cache: dict[str, ExternalPoint] = {}
        self._daily_cache: dict[str, Any] = {}
        self._premarket_cache: dict[str, Any] = {}
        self._regular_flow_cache: dict[str, Any] = {}
        self._regular_session_cache: dict[str, Any] = {}
        self._active_scope_key: tuple[str, str, str, str] | None = None
        self._last_minute_fetch = ""
        self._last_relative_minute_fetch = ""
        self._last_relative_fetch = 0.0
        self._last_flow_fetch = 0.0
        self._last_external_fetch = 0.0
        self._last_daily_fetch = ""
        self._last_premarket_recovery_attempt = 0.0
        self._last_aftermarket_flow_recovery_attempt = 0.0
        self._last_aftermarket_anchor_recovery_attempt = 0.0
        self._optional_gaps: list[dict[str, str]] = []
        self._external_fetch_error: str | None = None
        self._promotion_state_restore_attempted = False

    def _observe_entry_notification(
        self, payload: dict[str, Any], observed_at: datetime
    ) -> str:
        if self.entry_notifier is None:
            return "not_configured"
        try:
            return self.entry_notifier.observe(payload, observed_at)
        except Exception as exc:
            # Telegram/state persistence is advisory-only and must never
            # replace a fresh market-data snapshot with collector failure.
            print(
                "[WARN] Samsung widget Telegram notification isolated: "
                f"{type(exc).__name__}"
            )
            return "notifier_error_isolated"

    @staticmethod
    def _scope_key(
        observed_at: datetime, context: SessionContext
    ) -> tuple[str, str, str, str]:
        return (
            _as_kst(observed_at).date().isoformat(),
            context.name,
            context.market_venue,
            context.request_code,
        )

    def _activate_scope(self, observed_at: datetime, context: SessionContext) -> None:
        scope_key = self._scope_key(observed_at, context)
        if scope_key == self._active_scope_key:
            return
        self._active_scope_key = scope_key
        self._minute_cache = {}
        self._relative_cache = {}
        self._relative_window_cache = {}
        self._flow_cache = {}
        self._last_minute_fetch = ""
        self._last_relative_minute_fetch = ""
        self._last_relative_fetch = 0.0
        self._last_flow_fetch = 0.0
        self._promotion_state_restore_attempted = False
        self.break_rearm_filter.reset()
        self.recovery_episode_filter.reset()
        self.promotion_filter.reset()
        self.exit_state_machine.reset()

    @staticmethod
    def _peer_request_code(context: SessionContext) -> str:
        return f"{SK_HYNIX_CODE}_NX" if context.market_venue == "NXT" else SK_HYNIX_CODE

    def _read_only_client(self) -> KiwoomReadOnlyClient:
        token = kiwoom_utils.get_cached_kiwoom_token(CONF)
        if not token:
            raise RuntimeError("shared_token_unavailable")
        return KiwoomReadOnlyClient(
            token, session=self.request_session, budget=self.request_budget
        )

    def _optional_post(
        self,
        client: KiwoomReadOnlyClient,
        path: str,
        api_id: str,
        payload: dict[str, str],
    ) -> dict[str, Any]:
        try:
            return client.post(path, api_id, payload, optional=True)
        except Exception as exc:
            self._optional_gaps.append({"api_id": api_id, "reason": type(exc).__name__})
            return {}

    def _restore_promotion_state(
        self, observed_at: datetime, context: SessionContext
    ) -> None:
        if self._promotion_state_restore_attempted:
            return
        self._promotion_state_restore_attempted = True
        payload = load_snapshot(self.snapshot_path)
        advisory = payload.get("advisory") or {}
        exit_advisory = payload.get("exit_advisory") or {}
        if not isinstance(advisory, dict):
            return
        persisted_observed_at = snapshot_observed_at(payload)
        if persisted_observed_at is None:
            return
        if (
            payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION
            or payload.get("symbol") != SAMSUNG_CODE
            or payload.get("market_venue") != context.market_venue
            or payload.get("market_cohort") != context.market_cohort
            or payload.get("quote_request_code") != context.request_code
            or payload.get("token_mode") != "shared_cache_only"
            or advisory.get("session") != context.name
            or advisory.get("authority") != ADVISORY_AUTHORITY
            or advisory.get("runtime_effect") is not False
            or persisted_observed_at.date() != _as_kst(observed_at).date()
        ):
            return
        # A broken-support lock spans completed bars and must survive a service
        # restart longer than the 25-second display freshness window. Promotion
        # streaks remain freshness-bound below.
        self.break_rearm_filter.restore(advisory)
        self.recovery_episode_filter.restore(advisory)
        self.exit_state_machine.restore(exit_advisory)
        if not snapshot_is_fresh(
            payload, now=observed_at
        ) or not advisory_contract_is_valid(
            advisory,
            snapshot_observed_at=persisted_observed_at,
            context=context,
            evaluated_at=observed_at,
        ):
            return
        self.promotion_filter.restore(advisory)

    def collect_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        cycle_started = time.monotonic()
        request_count_before = self.request_budget.total_request_count
        now = _as_kst(observed_at or _now_kst())
        context = session_context(now)
        self._activate_scope(now, context)
        self._optional_gaps = []
        self._external_fetch_error = None
        if not context.active:
            closed_advisory = evaluate_advisory(
                observed_at=now,
                context=context,
                current_price=0,
                bars=[],
                bbo={},
                previous_day={},
                relative={},
                external_points={},
            )
            payload = {
                "schema_version": SNAPSHOT_SCHEMA_VERSION,
                "status": "closed",
                "symbol": SAMSUNG_CODE,
                "name": SAMSUNG_NAME,
                "observed_at_kst": now.isoformat(),
                "market_venue": context.market_venue,
                "market_cohort": context.market_cohort,
                "market_session": legacy_market_session(context),
                "token_mode": "shared_cache_only",
                "advisory": closed_advisory,
                "exit_advisory": self.exit_state_machine.apply(
                    observed_at=now,
                    context=context,
                    bars=[],
                    bbo={},
                    source_quality=closed_advisory["source_quality"],
                ),
            }
            _atomic_write_json(self.snapshot_path, payload)
            return payload

        client = self._read_only_client()
        epoch = now.timestamp()
        if epoch - self._last_external_fetch >= 60 or not self._external_cache:
            try:
                external_points = self.external_provider.fetch(now)
            except Exception as exc:
                external_points = {}
                self._external_fetch_error = type(exc).__name__
            if external_points:
                self._external_cache = external_points
            self._last_external_fetch = epoch

        quote = client.post(
            "/api/dostk/stkinfo", "ka10001", {"stk_cd": context.request_code}
        )
        quote_received_at = now if observed_at is not None else _now_kst()
        current_price = _positive_int(quote.get("cur_prc"))
        if current_price is None:
            raise RuntimeError("kiwoom_price_missing")
        bbo_payload = client.post(
            "/api/dostk/mrkcond", "ka10004", {"stk_cd": context.request_code}
        )
        bbo_received_at = now if observed_at is not None else _now_kst()
        bbo = _parse_bbo(bbo_payload, bbo_received_at)
        trade_payload = self._optional_post(
            client,
            "/api/dostk/stkinfo",
            "ka10003",
            {"stk_cd": context.request_code},
        )

        minute_key = now.strftime("%Y%m%d%H%M")
        if minute_key != self._last_minute_fetch or not self._minute_cache:
            minute_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10080",
                {"stk_cd": context.request_code, "tic_scope": "1", "upd_stkpc_tp": "1"},
            )
            if minute_payload:
                self._minute_cache = minute_payload
                self._last_minute_fetch = minute_key
        bars = completed_session_bars(
            self._minute_cache.get("stk_min_pole_chart_qry"),
            observed_at=now,
            session_start=context.start,
            session_end=context.end,
        )
        if minute_key != self._last_relative_minute_fetch:
            peer_minute_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10080",
                {
                    "stk_cd": self._peer_request_code(context),
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
            )
            peer_bars = completed_session_bars(
                peer_minute_payload.get("stk_min_pole_chart_qry"),
                observed_at=now,
                session_start=context.start,
                session_end=context.end,
            )
            kospi_bars: list[MinuteBar] = []
            if context.name == "KRX_REGULAR":
                kospi_minute_payload = self._optional_post(
                    client,
                    "/api/dostk/chart",
                    "ka20005",
                    {"inds_cd": "001", "tic_scope": "1"},
                )
                kospi_bars = completed_session_bars(
                    kospi_minute_payload.get("inds_min_pole_qry"),
                    observed_at=now,
                    session_start=context.start,
                    session_end=context.end,
                )
            self._relative_window_cache = _same_window_relative_snapshot(
                bars, peer_bars, kospi_bars
            )
            self._last_relative_minute_fetch = minute_key
        if context.name == "NXT_PREMARKET" and bars:
            self._premarket_cache = _premarket_context(bars, now)
        elif context.name == "KRX_REGULAR" and bars:
            self._regular_session_cache = _session_anchor(bars, now)

        day_key = now.strftime("%Y%m%d")
        if self._regular_flow_cache and not _observation_is_same_day(
            self._regular_flow_cache, now
        ):
            self._regular_flow_cache = {}
        before_premarket_aux_expiry = (
            context.name == "KRX_REGULAR"
            and now.time().replace(tzinfo=None) < PREMARKET_AUXILIARY_END
        )
        if (
            before_premarket_aux_expiry
            and self._premarket_cache.get("date") != now.date().isoformat()
            and epoch - self._last_premarket_recovery_attempt >= 60
        ):
            premarket_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10080",
                {
                    "stk_cd": f"{SAMSUNG_CODE}_NX",
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
            )
            recovered_bars = completed_session_bars(
                premarket_payload.get("stk_min_pole_chart_qry"),
                observed_at=now,
                session_start=NXT_PREMARKET_START,
                session_end=NXT_PREMARKET_END,
            )
            if recovered_bars:
                self._premarket_cache = _premarket_context(recovered_bars, now)
            self._last_premarket_recovery_attempt = epoch

        if day_key != self._last_daily_fetch or not self._daily_cache:
            daily_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10081",
                {"stk_cd": SAMSUNG_CODE, "base_dt": day_key, "upd_stkpc_tp": "1"},
            )
            if daily_payload:
                self._daily_cache = daily_payload
                self._last_daily_fetch = day_key
        previous_day = _current_daily_anchor(
            self._daily_cache.get("stk_dt_pole_chart_qry"),
            observed_at=now,
            cache_fetch_day=self._last_daily_fetch,
        )
        if (
            context.name == "NXT_AFTERMARKET"
            and self._regular_session_cache.get("date") != now.date().isoformat()
            and epoch - self._last_aftermarket_anchor_recovery_attempt >= 60
        ):
            regular_minute_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10080",
                {"stk_cd": SAMSUNG_CODE, "tic_scope": "1", "upd_stkpc_tp": "1"},
            )
            regular_bars = completed_session_bars(
                regular_minute_payload.get("stk_min_pole_chart_qry"),
                observed_at=now,
                session_start=KRX_START,
                session_end=KRX_END,
                limit=400,
            )
            if regular_bars:
                self._regular_session_cache = _session_anchor(regular_bars, now)
            self._last_aftermarket_anchor_recovery_attempt = epoch

        if epoch - self._last_relative_fetch >= 30 or not self._relative_cache:
            peer = self._optional_post(
                client,
                "/api/dostk/stkinfo",
                "ka10001",
                {"stk_cd": self._peer_request_code(context)},
            )
            kospi_change = None
            if context.name == "KRX_REGULAR":
                kospi = self._optional_post(
                    client,
                    "/api/dostk/sect",
                    "ka20001",
                    {"mrkt_tp": "0", "inds_cd": "001"},
                )
                kospi_change = _signed_float(kospi.get("flu_rt"))
            self._relative_cache = {
                "samsung_change_pct": _signed_float(quote.get("flu_rt")),
                "sk_hynix_change_pct": _signed_float(peer.get("flu_rt")),
                "kospi_change_pct": kospi_change,
                **self._relative_window_cache,
                "observed_at": now.isoformat(),
                "market_venue": context.market_venue,
            }
            self._last_relative_fetch = epoch
        elif self._relative_window_cache:
            self._relative_cache.update(self._relative_window_cache)

        if epoch - self._last_flow_fetch >= 60 or not self._flow_cache:
            investor_payload = None
            program_payload = None
            if context.name == "KRX_REGULAR":
                investor_payload = self._optional_post(
                    client,
                    "/api/dostk/chart",
                    "ka10064",
                    {
                        "mrkt_tp": "000",
                        "amt_qty_tp": "1",
                        "trde_tp": "0",
                        "stk_cd": SAMSUNG_CODE,
                    },
                )
                program_payload = self._optional_post(
                    client,
                    "/api/dostk/mrkcond",
                    "ka90008",
                    {"amt_qty_tp": "1", "stk_cd": SAMSUNG_CODE, "date": day_key},
                )
                self._flow_cache = _parse_flow(
                    investor_payload,
                    program_payload,
                    context=context,
                    observed_at=now,
                )
                if self._flow_cache.get("status") == "OBSERVED":
                    self._regular_flow_cache = dict(self._flow_cache)
            elif context.name == "NXT_AFTERMARKET":
                if (
                    not self._regular_flow_cache
                    and epoch - self._last_aftermarket_flow_recovery_attempt >= 60
                ):
                    investor_payload = self._optional_post(
                        client,
                        "/api/dostk/chart",
                        "ka10064",
                        {
                            "mrkt_tp": "000",
                            "amt_qty_tp": "1",
                            "trde_tp": "0",
                            "stk_cd": SAMSUNG_CODE,
                        },
                    )
                    program_payload = self._optional_post(
                        client,
                        "/api/dostk/mrkcond",
                        "ka90008",
                        {
                            "amt_qty_tp": "1",
                            "stk_cd": SAMSUNG_CODE,
                            "date": day_key,
                        },
                    )
                    regular_context = session_context(
                        now.replace(hour=KRX_START.hour, minute=1, second=0)
                    )
                    recovered_flow = _parse_flow(
                        investor_payload,
                        program_payload,
                        context=regular_context,
                        observed_at=now,
                    )
                    if _regular_flow_recoverable_for_aftermarket(recovered_flow, now):
                        self._regular_flow_cache = recovered_flow
                    self._last_aftermarket_flow_recovery_attempt = epoch
                if self._regular_flow_cache:
                    self._flow_cache = _freeze_regular_flow(
                        self._regular_flow_cache, now
                    )
                else:
                    self._flow_cache = _freeze_regular_flow({}, now)
            else:
                self._flow_cache = _parse_flow(
                    None,
                    None,
                    context=context,
                    observed_at=now,
                )
            self._last_flow_fetch = epoch

        decision_now = now if observed_at is not None else _now_kst()
        quote_age_sec = max(
            0.0, (decision_now - _as_kst(quote_received_at)).total_seconds()
        )
        bbo["age_sec"] = max(
            0.0, (decision_now - _as_kst(bbo_received_at)).total_seconds()
        )

        advisory = evaluate_advisory(
            observed_at=decision_now,
            context=context,
            current_price=current_price,
            bars=bars,
            bbo=bbo,
            previous_day=previous_day,
            relative=self._relative_cache,
            external_points=self._external_cache,
            flow=self._flow_cache,
            recent_trade_negative_veto=_recent_trade_negative_veto(trade_payload),
            premarket=self._premarket_cache,
            regular_session=self._regular_session_cache,
            quote_age_sec=quote_age_sec,
            quote_received_at=_as_kst(quote_received_at).isoformat(),
        )
        self._restore_promotion_state(decision_now, context)
        advisory = self.break_rearm_filter.apply(
            advisory, latest_bar=bars[-1] if bars else None
        )
        advisory = self.recovery_episode_filter.apply(
            advisory,
            current_price=current_price,
            bbo=bbo,
            latest_bar=bars[-1] if bars else None,
        )
        calibration_policy = self.calibration_policy_loader.resolve(
            symbol=SAMSUNG_CODE,
            session=context.name,
            observed_date=decision_now.date(),
        )
        advisory = self.promotion_filter.apply(
            advisory,
            required_confirmations=int(
                calibration_policy["required_actionable_confirmations"]
            ),
            calibration_policy=calibration_policy,
        )
        advisory["source_quality"]["auxiliary_status"] = (
            "DATA_LIMITED"
            if self._optional_gaps or self._external_fetch_error
            else "PASS"
        )
        advisory["source_quality"]["auxiliary_gaps"] = list(self._optional_gaps)
        advisory["provenance"]["external_fetch_error"] = self._external_fetch_error
        advisory["provenance"]["cache_scope"] = list(self._active_scope_key or ())
        exit_source_quality = _source_quality(
            observed_at=decision_now,
            context=context,
            bars=bars,
            bbo=bbo,
            previous_day=None,
            quote_age_sec=quote_age_sec,
            current_price=current_price,
        )
        exit_advisory = self.exit_state_machine.apply(
            observed_at=decision_now,
            context=context,
            bars=bars,
            bbo=bbo,
            source_quality=exit_source_quality,
            entry_advisory=advisory,
        )
        if _apply_entry_exit_conflict_guard(advisory, exit_advisory):
            # The promotion filter has already observed this raw entry.  Reset
            # it so a cleared exit warning still needs the configured two/three
            # consecutive confirmations instead of reappearing immediately.
            self.promotion_filter.reset()
            if self.exit_state_machine.reject_current_entry_episode_reset():
                exit_advisory["entry_episode_reset"] = False
                exit_advisory["entry_conflict_rejected"] = True
                exit_advisory["continuity"] = self.exit_state_machine.snapshot()
        exit_advisory["contrarian_reversal"] = _exit_contrarian_reversal_observation(
            exit_advisory, bars
        )
        day_low = _positive_int(quote.get("low_pric"))
        day_low_delta = (
            current_price - day_low
            if day_low is not None and current_price >= day_low
            else None
        )
        day_low_delta_pct = (
            round((day_low_delta / day_low) * 100, 2)
            if day_low_delta is not None and day_low
            else None
        )
        trend_details = analyze_trends(bars, session_name=context.name)
        trends = {
            key: str(detail.get("state") or "unavailable")
            for key, detail in trend_details.items()
        }
        payload = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "status": "ok",
            "symbol": SAMSUNG_CODE,
            "name": SAMSUNG_NAME,
            "current_price": current_price,
            "day_low_price": day_low,
            "day_low_delta": day_low_delta,
            "day_low_delta_pct": day_low_delta_pct,
            "minute_trend": trends.get("1m", "unavailable"),
            "minute_trends": trends,
            "minute_trend_details": trend_details,
            "trend_assessment": _trend_assessment(trends),
            "minute_trend_basis": "tick_volatility_adjusted_completed_1m_closes",
            "minute_trends_basis": (
                "1m_3m_5m_completed_contiguous_closes_session_tick_volatility_band"
            ),
            "minute_chart_basis": "20_completed_1m_closes",
            "minute_chart": [
                {
                    "time_kst": f"{bar.source_time[8:10]}:{bar.source_time[10:12]}",
                    "close": bar.close,
                }
                for bar in bars[-20:]
            ],
            "minute_trend_at_kst": (
                datetime.strptime(bars[-1].source_time, "%Y%m%d%H%M%S")
                .replace(tzinfo=KST)
                .isoformat()
                if bars
                else None
            ),
            "observed_at_kst": decision_now.isoformat(),
            "market_venue": context.market_venue,
            "market_cohort": context.market_cohort,
            "market_session": legacy_market_session(context),
            "minute_session_start_kst": context.start.strftime("%H:%M"),
            "quote_request_code": context.request_code,
            "source": f"samsung_widget_collector_kiwoom_{context.market_venue.lower()}",
            "token_mode": "shared_cache_only",
            "observation": {
                "latest_completed_bar": asdict(bars[-1]) if bars else None,
                "raw_10s_persistence_forbidden": True,
            },
            "collector_metrics": {
                "cycle_elapsed_ms": round((time.monotonic() - cycle_started) * 1000, 3),
                "cycle_kiwoom_request_count": (
                    self.request_budget.total_request_count - request_count_before
                ),
                **self.request_budget.snapshot(),
                "scope": list(self._active_scope_key or ()),
                "authority": "widget_collector_local_only",
            },
            "advisory": advisory,
            "exit_advisory": exit_advisory,
        }
        _atomic_write_json(self.snapshot_path, payload)
        self.recorder.record(payload, decision_now)
        self._observe_entry_notification(payload, decision_now)
        return payload

    def write_failure(self, reason: str, observed_at: datetime | None = None) -> None:
        now = _as_kst(observed_at or _now_kst())
        context = session_context(now)
        self.promotion_filter.reset()
        payload = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "status": "unavailable",
            "symbol": SAMSUNG_CODE,
            "reason": reason,
            "observed_at_kst": now.isoformat(),
            "market_venue": context.market_venue,
            "market_cohort": context.market_cohort,
            "market_session": legacy_market_session(context),
            "quote_request_code": context.request_code,
            "token_mode": "shared_cache_only",
            "advisory": {
                "state": "DATA_WAIT",
                "raw_state": "DATA_WAIT",
                "session": context.name,
                "entry_price_low": None,
                "entry_price_high": None,
                "observed_at": now.isoformat(),
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality": {"status": "BLOCKED", "issues": [reason]},
                "continuity": self.break_rearm_filter.snapshot(),
                "recovery_continuity": self.recovery_episode_filter.snapshot(),
                "metric_contract": METRIC_CONTRACT,
            },
            "exit_advisory": {
                "state": "DATA_WAIT",
                "raw_state": "DATA_WAIT",
                "session": context.name,
                "reference_exit_price": None,
                "observed_at": now.isoformat(),
                "valid_until": now.isoformat(),
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "holding_independent": True,
                "future_prediction": False,
                "source_quality": {"status": "BLOCKED", "issues": [reason]},
                "continuity": self.exit_state_machine.snapshot(),
                "metric_contract": METRIC_CONTRACT,
            },
        }
        _atomic_write_json(self.snapshot_path, payload)

    def run_forever(self, *, interval_sec: float = 10.0) -> None:
        interval = max(1.0, float(interval_sec))
        while True:
            started = time.monotonic()
            try:
                self.collect_once()
            except Exception as exc:
                self.write_failure(str(exc)[:160])
            remaining = interval - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=10.0)
    parser.add_argument("--snapshot-path", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--observation-dir", type=Path, default=DEFAULT_OBSERVATION_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    collector = SamsungWidgetCollector(
        snapshot_path=args.snapshot_path,
        observation_dir=args.observation_dir,
        # Collector ENTRY states only arm the collector-linked EXIT episode.
        # Accepted BUY actions are notified by widget_auto_trade instead.
        entry_notifier=SamsungWidgetEntryTelegramNotifier(entry_messages_enabled=False),
    )
    if args.once:
        collector.collect_once()
        return 0
    collector.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
