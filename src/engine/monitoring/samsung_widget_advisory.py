"""Read-only Samsung Electronics intraday advisory collector.

This module is deliberately isolated from the trading runtime.  It consumes
only the existing shared Kiwoom token cache, never issues or refreshes a token,
and has no account, order, quantity, provider-route, or bot-control authority.
The generated state is for the Windows widget only.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, time as datetime_time, timedelta
from pathlib import Path
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
    KRX_START,
    KST,
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
    as_kst as _as_kst,
    legacy_market_session,
    load_snapshot,
    session_context,
    snapshot_is_fresh,
)
from src.engine.sniper_config import CONF
from src.trading.order.tick_utils import (
    clamp_price_to_tick,
    get_tick_size,
    move_price_by_ticks,
)
from src.utils import kiwoom_utils

NEW_YORK = ZoneInfo("America/New_York")
NYSE_HOLIDAYS = holidays.NYSE()
EXTERNAL_STALE_SEC = 300
FLOW_STALE_SEC = 300

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
    """Normalize current-session completed ka10080 one-minute bars."""
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


def classify_trends(bars: list[MinuteBar]) -> dict[str, str]:
    result: dict[str, str] = {}
    for horizon in (1, 3, 5):
        window = _contiguous_window(bars, horizon + 1)
        if not window:
            result[f"{horizon}m"] = "unavailable"
            continue
        closes = [bar.close for bar in window]
        change = closes[-1] - closes[0]
        flat_band = max(1, round(closes[-1] * 0.0005))
        center = (len(closes) - 1) / 2
        slope = sum((index - center) * price for index, price in enumerate(closes))
        if abs(change) <= flat_band:
            trend = "flat"
        elif change > flat_band and slope > 0:
            trend = "up"
        elif change < -flat_band and slope < 0:
            trend = "down"
        else:
            trend = "flat"
        result[f"{horizon}m"] = trend
    return result


def _session_vwap(bars: list[MinuteBar]) -> int | None:
    weighted_volume = sum(bar.volume for bar in bars if bar.volume > 0)
    if weighted_volume > 0:
        value = sum(bar.close * bar.volume for bar in bars if bar.volume > 0)
        return int(round(value / weighted_volume))
    if bars:
        return int(round(sum(bar.close for bar in bars) / len(bars)))
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
        "minute_trends": classify_trends(bars),
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
    confirmed_support: int | None = None
    if len(recent) >= 6:
        prior_window = recent[-6:-3]
        latest_window = recent[-3:]
        prior_low = min(bar.low for bar in prior_window)
        latest_low = min(bar.low for bar in latest_window)
        prior_high = max(bar.high for bar in prior_window)
        latest_high = max(bar.high for bar in latest_window)
        higher_low = latest_low >= prior_low
        higher_high = latest_high > prior_high
        higher_high_and_low = higher_low and higher_high
    if len(pivots) >= 2:
        first_index, first_low = pivots[-2]
        second_index, second_low = pivots[-1]
        tolerance = max(get_tick_size(second_low), round(second_low * 0.001))
        retest_held = (
            second_index > first_index
            and second_low >= first_low - tolerance
            and recent[-1].close > second_low
        )
        confirmed_support = second_low
    elif pivots:
        confirmed_support = pivots[-1][1]
    elif recent:
        confirmed_support = min(bar.low for bar in recent[-3:])

    resistance_rows = recent[:-2] if len(recent) >= 5 else recent[:-1]
    recent_resistance = (
        max(bar.high for bar in resistance_rows) if resistance_rows else None
    )
    return {
        "higher_low": higher_low,
        "higher_high": higher_high,
        "higher_high_and_low": higher_high_and_low,
        "retest_held": retest_held,
        "confirmed_support": confirmed_support,
        "recent_resistance": recent_resistance,
    }


def _volume_confirmation(
    bars: list[MinuteBar],
) -> tuple[bool, dict[str, float | int | bool | None]]:
    recent = bars[-8:]
    rising = [bar.volume for bar in recent if bar.close > bar.open and bar.volume > 0]
    falling = [bar.volume for bar in recent if bar.close < bar.open and bar.volume > 0]
    rising_avg = sum(rising) / len(rising) if rising else None
    falling_avg = sum(falling) / len(falling) if falling else None
    if rising_avg is None:
        rebound_confirmed = False
    elif falling_avg is None:
        rebound_confirmed = True
    else:
        rebound_confirmed = rising_avg >= falling_avg
    pivots = _pivot_lows(recent)
    first_test_volume = None
    retest_volume = None
    retest_volume_contracted = None
    if len(pivots) >= 2:
        first_test_volume = recent[pivots[-2][0]].volume
        retest_volume = recent[pivots[-1][0]].volume
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
    }


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

    def __init__(self, downloader=None) -> None:
        self._downloader = downloader or yf.download

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
        # Isolate the three best-effort sources so one five-second Yahoo delay
        # cannot serially consume the collector's ten-second refresh budget.
        with ThreadPoolExecutor(
            max_workers=len(self.TICKERS),
            thread_name_prefix="samsung-widget-yahoo",
        ) as executor:
            futures = {
                key: executor.submit(self._fetch_one, key, ticker, observed_at)
                for key, ticker in self.TICKERS.items()
            }
            points: dict[str, ExternalPoint] = {}
            for key, future in futures.items():
                try:
                    points[key] = future.result()
                except Exception as exc:
                    points[key] = ExternalPoint(
                        key=key,
                        ticker=self.TICKERS[key],
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


def evaluate_external_risk(points: dict[str, ExternalPoint]) -> dict[str, Any]:
    adverse: list[str] = []
    severe: list[str] = []
    stale: list[str] = []
    unavailable: list[str] = []
    for key, threshold in EXTERNAL_THRESHOLDS.items():
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
    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_date = str(row.get("dt") or "").strip()
        if len(source_date) != 8 or not source_date.isdigit() or source_date >= today:
            continue
        close = _positive_int(row.get("cur_prc"))
        high = _positive_int(row.get("high_pric"))
        low = _positive_int(row.get("low_pric"))
        open_price = _positive_int(row.get("open_pric"))
        if all((close, high, low, open_price)):
            candidates.append(
                {
                    "date": source_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                }
            )
    return max(candidates, key=lambda row: row["date"], default={})


def _current_daily_anchor(
    rows: object, *, observed_at: datetime, cache_fetch_day: str
) -> dict[str, Any]:
    """Reject a retained daily response that was not refreshed this trade date."""
    day_key = _as_kst(observed_at).strftime("%Y%m%d")
    if cache_fetch_day != day_key:
        return {}
    return _parse_previous_day(rows, observed_at)


def _relative_quality(
    relative: dict[str, Any], context: SessionContext
) -> tuple[bool, list[str]]:
    samsung_change = _signed_float(relative.get("samsung_change_pct"))
    sk_hynix_change = _signed_float(relative.get("sk_hynix_change_pct"))
    kospi_change = _signed_float(relative.get("kospi_change_pct"))
    comparisons = (
        [sk_hynix_change, kospi_change]
        if context.name == "KRX_REGULAR"
        else [sk_hynix_change]
    )
    if samsung_change is None or any(value is None for value in comparisons):
        return False, ["relative_strength_unavailable"]
    weak_against = [
        value
        for value in comparisons
        if value is not None and samsung_change < value - 0.5
    ]
    return not weak_against, ([] if not weak_against else ["relative_strength_weak"])


def _source_quality(
    *,
    observed_at: datetime,
    context: SessionContext,
    bars: list[MinuteBar],
    bbo: dict[str, Any],
    previous_day: dict[str, Any],
    quote_age_sec: float,
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
        if age > max_age:
            issues.append("completed_bar_stale")
    else:
        issues.append("completed_bars_missing")
    if not previous_day:
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
    return {
        "status": "PASS" if not issues else "BLOCKED",
        "issues": issues,
        "required_sources": ["quote", "bbo", "completed_1m", "previous_day_ohlc"],
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
    quote_age_sec: float = 0.0,
    quote_received_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic widget-only advisory without score/AI authority."""
    flow = flow or {}
    premarket = premarket or {}
    source_quality = _source_quality(
        observed_at=observed_at,
        context=context,
        bars=bars,
        bbo=bbo,
        previous_day=previous_day,
        quote_age_sec=quote_age_sec,
    )
    external_points = _age_external_points(external_points, observed_at)
    external_risk = evaluate_external_risk(external_points)
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
        "provenance": {
            "market_venue": context.market_venue,
            "market_cohort": context.market_cohort,
            "quote_request_code": context.request_code,
            "external_provider": "yahoo_best_effort",
            "premarket_context": premarket_provenance,
            "quote_received_at": quote_received_at,
            "quote_age_sec": round(quote_age_sec, 3),
        },
        "authority": ADVISORY_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": METRIC_CONTRACT,
    }
    if source_quality["status"] != "PASS":
        return base

    trends = classify_trends(bars)
    structure = _structure_features(bars)
    vwap = _session_vwap(bars)
    volume_ok, volume_meta = _volume_confirmation(bars)
    relative_ok, relative_issues = _relative_quality(relative, context)
    best_bid = int(bbo["best_bid"])
    best_ask = int(bbo["best_ask"])
    spread_ticks = _spread_tick_count(best_bid, best_ask)

    support_candidates = [
        value
        for value in (
            structure.get("confirmed_support"),
            vwap if vwap is not None and vwap <= current_price else None,
            (
                previous_day.get("low")
                if previous_day.get("low") and previous_day["low"] <= current_price
                else None
            ),
        )
        if isinstance(value, int) and value > 0
    ]
    raw_support = max(support_candidates, default=None)
    support = clamp_price_to_tick(raw_support) if raw_support is not None else None
    recent_resistance = structure.get("recent_resistance")
    structure_ok = bool(structure["higher_high_and_low"] or structure["retest_held"])
    reclaim_ok = bool(
        vwap
        and current_price >= vwap
        and (
            recent_resistance is None
            or current_price >= recent_resistance
            or structure_ok
        )
    )
    trends_ok = trends.get("3m") in {"up", "flat"} and trends.get("5m") in {
        "up",
        "flat",
    }
    spread_ok = spread_ticks <= 2
    core_checks = {
        "low_structure_confirmed": structure_ok,
        "vwap_or_resistance_reclaimed": reclaim_ok,
        "rebound_volume_confirmed": volume_ok,
        "three_five_minute_not_down": trends_ok,
        "relative_strength_not_weak": relative_ok,
        "spread_within_two_ticks": spread_ok,
    }
    unmet = [name for name, passed in core_checks.items() if not passed]
    unmet.extend(relative_issues)
    reasons = [name for name, passed in core_checks.items() if passed]
    if flow.get("foreign_nonworsening"):
        reasons.append("foreign_flow_nonworsening")
    if flow.get("program_nonworsening"):
        reasons.append("program_flow_nonworsening")
    flow_negative = bool(
        context.name == "KRX_REGULAR"
        and flow.get("status") == "OBSERVED"
        and flow.get("live_for_current_session") is True
        and not flow.get("foreign_nonworsening")
        and not flow.get("program_nonworsening")
    )
    if flow_negative:
        unmet.append("foreign_and_program_flow_not_improving")
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

    if support is None:
        base["unmet_conditions"] = ["confirmed_support_missing", *unmet]
        return base
    invalidation = move_price_by_ticks(support, -1)
    trigger_candidates = [
        value
        for value in (vwap, recent_resistance, previous_day.get("close"))
        if isinstance(value, int) and value > 0 and value <= current_price
    ]
    trigger_price = clamp_price_to_tick(max(trigger_candidates, default=support))
    chase_pct = ((current_price - support) / support) * 100 if support else 0.0

    base.update(
        {
            "trigger": "dynamic_support_and_vwap_reclaim",
            "trigger_price": trigger_price,
            "invalidation": "confirmed_support_break",
            "invalidation_price": invalidation,
            "reasons": reasons,
            "unmet_conditions": list(dict.fromkeys(unmet)),
            "derived": {
                "session_vwap": vwap,
                "confirmed_support": support,
                "recent_resistance": recent_resistance,
                "previous_day": previous_day,
                "opening_range_high": max(
                    bar.high for bar in bars[: context.minimum_bars]
                ),
                "opening_range_low": min(
                    bar.low for bar in bars[: context.minimum_bars]
                ),
                "spread_ticks": spread_ticks,
                "chase_pct": round(chase_pct, 4),
                "minute_trends": trends,
                "higher_low": structure["higher_low"],
                "higher_high": structure["higher_high"],
                "higher_high_and_low": structure["higher_high_and_low"],
                "retest_held": structure["retest_held"],
                "premarket_auxiliary": (premarket if premarket_aux_applied else None),
                **volume_meta,
            },
            "flow": flow,
        }
    )
    if current_price < invalidation:
        base["state"] = base["raw_state"] = "AVOID"
        base["reasons"] = ["confirmed_support_broken"]
        return base
    if chase_pct > 0.3:
        base["state"] = base["raw_state"] = "NO_CHASE"
        base["reasons"] = ["price_more_than_30bp_above_support"]
        return base
    if not spread_ok or recent_trade_negative_veto:
        base["state"] = base["raw_state"] = "WATCH"
        if recent_trade_negative_veto:
            base["unmet_conditions"].append("recent_rest_prints_descending")
        return base

    all_core_passed = all(core_checks.values())
    if all_core_passed:
        entry_low = max(support, best_bid)
        entry_high = min(best_ask, move_price_by_ticks(support, 2))
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
            or flow_negative
            or flow_data_limited
            or premarket_aux_weak
        ):
            base["state"] = base["raw_state"] = "ENTRY_CAUTION"
        else:
            base["state"] = base["raw_state"] = "ENTRY_READY"
        return base

    base["state"] = base["raw_state"] = "WATCH"
    return base


class AdvisoryPromotionFilter:
    """Require two identical actionable observations; demotions are immediate."""

    ACTIONABLE = {"ENTRY_CAUTION", "ENTRY_READY"}
    ACTIONABLE_RANK = {"ENTRY_CAUTION": 1, "ENTRY_READY": 2}

    def __init__(self) -> None:
        self._scope_key: str | None = None
        self._last_raw_state: str | None = None
        self._streak = 0
        self._visible_state = "DATA_WAIT"

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
        self._scope_key = self._scope_for(advisory)
        self._last_raw_state = raw_state
        self._streak = streak
        self._visible_state = visible_state
        return True

    def apply(self, advisory: dict[str, Any]) -> dict[str, Any]:
        result = json.loads(json.dumps(advisory, ensure_ascii=False))
        scope_key = self._scope_for(result)
        if scope_key != self._scope_key:
            self._scope_key = scope_key
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
            and self._streak < 2
        )
        if is_unconfirmed_promotion:
            result["state"] = (
                self._visible_state
                if self._visible_state in self.ACTIONABLE
                else "WATCH"
            )
            result.setdefault("unmet_conditions", []).append(
                "awaiting_second_10s_confirmation"
            )
        else:
            self._visible_state = raw_state
            result["state"] = raw_state
        result["confirmation_streak"] = self._streak
        return result


class KiwoomReadOnlyClient:
    """Small exact-contract REST client with no auth lifecycle mutation."""

    def __init__(self, token: str, *, session: requests.Session | None = None) -> None:
        self.token = token
        self.session = session or requests.Session()

    def post(self, path: str, api_id: str, payload: dict[str, str]) -> dict[str, Any]:
        if (path, api_id) not in READ_ONLY_KIWOOM_REQUESTS:
            raise RuntimeError(f"forbidden_widget_kiwoom_request:{api_id}:{path}")
        response = self.session.post(
            kiwoom_utils.get_api_url(path),
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {self.token}",
                "api-id": api_id,
            },
            json=payload,
            timeout=(5, 10),
        )
        response.raise_for_status()
        data = response.json()
        try:
            return_code = int(data["return_code"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"{api_id}_return_code_missing") from exc
        if return_code != 0:
            raise RuntimeError(f"{api_id}_rejected_{return_code}")
        return data


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
    latest_source_clock = max(
        (
            str(row.get("tm") or "").strip()
            for row in [*investor_rows, *program_rows]
            if str(row.get("tm") or "").strip()
        ),
        default="",
    )
    source_observed_at = None
    if latest_source_clock.isdigit() and len(latest_source_clock) in {4, 6}:
        normalized_clock = latest_source_clock.ljust(6, "0")
        try:
            source_observed_at = datetime.combine(
                _as_kst(observed_at).date(),
                datetime.strptime(normalized_clock, "%H%M%S").time(),
                tzinfo=KST,
            ).isoformat()
        except ValueError:
            source_observed_at = None
    if foreign_available and program_available and source_observed_at is not None:
        source_time = datetime.fromisoformat(source_observed_at)
        source_age_sec = (_as_kst(observed_at) - source_time).total_seconds()
        status = "OBSERVED" if 0 <= source_age_sec <= FLOW_STALE_SEC else "STALE"
    elif investor_rows or program_rows:
        source_age_sec = None
        status = "PARTIAL"
    else:
        source_age_sec = None
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


class ObservationRecorder:
    def __init__(self, directory: Path, *, retention_days: int = 30) -> None:
        self.directory = directory
        self.retention_days = max(1, int(retention_days))
        self._last_state: str | None = None
        self._last_minute: str | None = None
        self._loaded_day: str | None = None

    def _restore_current_day(self, target: Path, day_key: str) -> None:
        self._last_state = None
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
            state = str(advisory.get("state") or "").strip()
            observed_at = str(row.get("observed_at_kst") or "")
            if not state or not observed_at.startswith(
                f"{day_key[:4]}-{day_key[4:6]}-{day_key[6:8]}"
            ):
                continue
            self._last_state = state
            try:
                parsed = datetime.fromisoformat(observed_at)
            except ValueError:
                return
            self._last_minute = _as_kst(parsed).strftime("%Y%m%d%H%M")
            return

    def record(self, payload: dict[str, Any], observed_at: datetime) -> None:
        day_key = _as_kst(observed_at).strftime("%Y%m%d")
        target = self.directory / f"samsung_widget_advisory_{day_key}.jsonl"
        if self._loaded_day != day_key:
            self._restore_current_day(target, day_key)
        advisory = payload.get("advisory") or {}
        state = str(advisory.get("state") or "DATA_WAIT")
        minute = _as_kst(observed_at).strftime("%Y%m%d%H%M")
        previous_state = self._last_state
        state_changed = state != previous_state
        minute_changed = minute != self._last_minute
        if not state_changed and not minute_changed:
            return
        self._last_state = state
        self._last_minute = minute
        self.directory.mkdir(parents=True, exist_ok=True)
        row = {
            "observed_at_kst": _as_kst(observed_at).isoformat(),
            "current_price": payload.get("current_price"),
            "market_venue": payload.get("market_venue"),
            "market_session": advisory.get("session") or payload.get("market_session"),
            "legacy_market_session": payload.get("market_session"),
            "observation_kind": (
                "state_transition" if state_changed else "minute_summary"
            ),
            "previous_advisory_state": previous_state,
            "latest_completed_bar": (payload.get("observation") or {}).get(
                "latest_completed_bar"
            ),
            "advisory": advisory,
            "metric_contract": METRIC_CONTRACT,
        }
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        cutoff = _as_kst(observed_at).date() - timedelta(days=self.retention_days)
        for path in self.directory.glob("samsung_widget_advisory_*.jsonl"):
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
    ) -> None:
        self.snapshot_path = snapshot_path
        self.external_provider = external_provider or YahooExternalMarketProvider()
        self.request_session = request_session
        self.promotion_filter = AdvisoryPromotionFilter()
        self.recorder = ObservationRecorder(observation_dir)
        self._minute_cache: dict[str, Any] = {}
        self._relative_cache: dict[str, Any] = {}
        self._flow_cache: dict[str, Any] = {}
        self._external_cache: dict[str, ExternalPoint] = {}
        self._daily_cache: dict[str, Any] = {}
        self._premarket_cache: dict[str, Any] = {}
        self._regular_flow_cache: dict[str, Any] = {}
        self._last_minute_fetch = ""
        self._last_relative_fetch = 0.0
        self._last_flow_fetch = 0.0
        self._last_external_fetch = 0.0
        self._last_daily_fetch = ""
        self._last_premarket_recovery_attempt = 0.0
        self._last_aftermarket_flow_recovery_attempt = 0.0
        self._optional_gaps: list[dict[str, str]] = []
        self._external_fetch_error: str | None = None
        self._promotion_state_restore_attempted = False

    @staticmethod
    def _peer_request_code(context: SessionContext) -> str:
        return f"{SK_HYNIX_CODE}_NX" if context.market_venue == "NXT" else SK_HYNIX_CODE

    def _read_only_client(self) -> KiwoomReadOnlyClient:
        token = kiwoom_utils.get_cached_kiwoom_token(CONF)
        if not token:
            raise RuntimeError("shared_token_unavailable")
        return KiwoomReadOnlyClient(token, session=self.request_session)

    def _optional_post(
        self,
        client: KiwoomReadOnlyClient,
        path: str,
        api_id: str,
        payload: dict[str, str],
    ) -> dict[str, Any]:
        try:
            return client.post(path, api_id, payload)
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
        if not snapshot_is_fresh(payload, now=observed_at):
            return
        advisory = payload.get("advisory") or {}
        if not isinstance(advisory, dict):
            return
        if (
            payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION
            or payload.get("symbol") != SAMSUNG_CODE
            or payload.get("market_venue") != context.market_venue
            or payload.get("market_cohort") != context.market_cohort
            or payload.get("quote_request_code") != context.request_code
            or payload.get("token_mode") != "shared_cache_only"
            or advisory.get("authority") != ADVISORY_AUTHORITY
            or advisory.get("session") != context.name
            or advisory.get("runtime_effect") is not False
            or advisory.get("actual_order_submitted") is not False
            or advisory.get("broker_order_forbidden") is not True
        ):
            return
        self.promotion_filter.restore(advisory)

    def collect_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        now = _as_kst(observed_at or _now_kst())
        context = session_context(now)
        self._optional_gaps = []
        self._external_fetch_error = None
        if not context.active:
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
                "advisory": evaluate_advisory(
                    observed_at=now,
                    context=context,
                    current_price=0,
                    bars=[],
                    bbo={},
                    previous_day={},
                    relative={},
                    external_points={},
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
        if context.name == "NXT_PREMARKET" and bars:
            self._premarket_cache = _premarket_context(bars, now)

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
                "observed_at": now.isoformat(),
                "market_venue": context.market_venue,
            }
            self._last_relative_fetch = epoch

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
                    if recovered_flow.get("status") == "OBSERVED":
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
            quote_age_sec=quote_age_sec,
            quote_received_at=_as_kst(quote_received_at).isoformat(),
        )
        self._restore_promotion_state(decision_now, context)
        advisory = self.promotion_filter.apply(advisory)
        advisory["source_quality"]["auxiliary_status"] = (
            "DATA_LIMITED"
            if self._optional_gaps or self._external_fetch_error
            else "PASS"
        )
        advisory["source_quality"]["auxiliary_gaps"] = list(self._optional_gaps)
        advisory["provenance"]["external_fetch_error"] = self._external_fetch_error
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
        trends = classify_trends(bars)
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
            "minute_trend_basis": "2_completed_contiguous_1m_closes",
            "minute_trends_basis": (
                "1m_3m_5m_completed_contiguous_1m_close_horizons_5bp_flat_band"
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
            "advisory": advisory,
        }
        _atomic_write_json(self.snapshot_path, payload)
        self.recorder.record(payload, decision_now)
        return payload

    def write_failure(self, reason: str, observed_at: datetime | None = None) -> None:
        now = _as_kst(observed_at or _now_kst())
        payload = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "status": "unavailable",
            "reason": reason,
            "observed_at_kst": now.isoformat(),
            "token_mode": "shared_cache_only",
            "advisory": {
                "state": "DATA_WAIT",
                "raw_state": "DATA_WAIT",
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality": {"status": "BLOCKED", "issues": [reason]},
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
    )
    if args.once:
        collector.collect_once()
        return 0
    collector.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
