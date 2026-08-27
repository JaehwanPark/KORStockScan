"""Discover symbol-specific widget ENTRY/EXIT policies from clean market data.

This source-only producer uses completed KRX one-minute OHLCV and a
cached Kiwoom token.  It discovers a causal ``setup -> reclaim entry -> target
or confirmed support-break exit`` state machine per symbol.  Calibration alone
selects parameters; the latest 16 trading dates remain untouched holdout.
Nothing in this module creates collectors, starts services, accesses accounts,
or submits orders.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time as time_module
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

import requests

from src.trading.order.tick_utils import (
    clamp_price_to_tick,
    get_tick_size,
    move_price_by_ticks,
    move_price_up_by_bps,
)
from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    cost_aware_return_pct,
)
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

REPORT_SCHEMA = "widget_symbol_signal_policy_research_v3"
KST = ZoneInfo("Asia/Seoul")
AUTHORITY = "widget_symbol_signal_policy_discovery_only"
OWNER = "widget_symbol_auto_trade"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
HOLDOUT_DAYS = 16
OUTPUT_DIR = DATA_DIR / "report" / "widget_symbol_signal_policy_research"
SYMBOLS = {
    "006800": "미래에셋증권",
    "010140": "삼성중공업",
    "080220": "제주반도체",
    "475150": "SK이터닉스",
}
SEGMENTS = {
    "morning": (time(9, 3), time(10, 30)),
    "midday": (time(10, 30), time(13, 30)),
    "afternoon": (time(13, 30), time(15, 0)),
}
LOOKBACK_GRID = (15, 30, 45)
DRAWDOWN_GRID = (0.50, 1.00, 1.50, 2.00)
NEAR_LOW_GRID = (0.20, 0.50, 0.75)
RECLAIM_TICK_GRID = (1, 2)
BASE_MAX_RECLAIM_CHASE_TICKS = 2
MORNING_MAX_RECLAIM_CHASE_TICK_GRID = (2, 6)
TARGET_BPS_GRID = (30, 50, 75, 100)
SETUP_VALID_BARS = 5
REENTRY_COOLDOWN_BARS = 10
ENTRY_CAP_VALUES = tuple(range(1, 6))
HIGH_ENTRY_CAP_START = 4
# ka10080 labels the completed 15:19~15:20 interval as 15:19.
FORCE_FLAT_TIME = time(15, 19)
MAX_RATE_LIMIT_RETRIES = 5
MAX_RETRY_AFTER_SEC = 10.0

METRIC_CONTRACT = {
    "metric_role": "symbol_specific_widget_signal_policy_discovery",
    "decision_authority": AUTHORITY,
    "window_policy": (
        "clean_baseline_expanding_calibration_latest_16_trading_days_holdout"
    ),
    "sample_floor": {
        "calibration_episodes": 10,
        "each_calibration_half_episodes": 4,
        "holdout_episodes": 4,
        "high_entry_cap_incremental_episodes": 1,
    },
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "official_ka10080_success",
        "requested_start_date_fully_bracketed",
        "all_clean_baseline_trading_dates_match",
        "valid_unique_completed_krx_regular_ohlcv",
        "incomplete_trading_date_excluded_before_split",
        "next_completed_bar_entry_without_same_bar_fill_assumption",
        "chronological_calibration_selection_before_untouched_holdout",
        "daily_entry_caps_1_through_5_compared",
        "entry_caps_4_and_5_positive_incremental_ev_in_calibration_halves_and_holdout",
    ],
    "forbidden_uses": [
        "holdout_outcome_used_for_parameter_selection",
        "historical_bbo_spread_tape_or_flow_imputation",
        "price_touch_as_actual_broker_fill_evidence",
        "collector_creation_or_service_start_by_research_producer",
        "direct_or_same_day_runtime_promotion_without_exact_date_bridge",
        "account_or_order_api",
        "token_issue_refresh_invalidation_or_replacement",
        "provider_bot_cap_or_broker_guard_change",
    ],
}

OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-12T12:09:57+09:00",
    "inspected_paths": [
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contract": "POST /api/dostk/chart; api-id=ka10080",
}

OWNER_CONTRACT = {
    "owner": OWNER,
    "authority": AUTHORITY,
    "state_namespace": "widget_symbol_auto_trade:<symbol>:<trade_date>",
    "order_ledger_namespace": "widget_symbol_auto_trade:<symbol>",
    "position_attribution": "own_filled_buy_quantity_only",
    "forbidden_cross_owner_actions": [
        "read_other_owner_signal_as_widget_entry_or_exit",
        "cancel_other_owner_order",
        "sell_other_owner_quantity",
        "reuse_other_owner_position_or_episode_state",
        "mutate_low_price_two_leg_profile_policy_or_service",
    ],
}


@dataclass(frozen=True)
class SignalPolicy:
    segment: str
    lookback_bars: int
    drawdown_pct: float
    near_low_pct: float
    reclaim_ticks: int
    target_bps: int
    anchor_mode: str = "rolling"
    minimum_history_bars: int | None = None
    max_reclaim_chase_ticks: int = 2
    setup_valid_bars: int = SETUP_VALID_BARS
    reentry_cooldown_bars: int = REENTRY_COOLDOWN_BARS
    force_flat_time: str = FORCE_FLAT_TIME.isoformat()


class ResearchError(RuntimeError):
    """Raised when the independent read-only widget source contract fails."""


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    volume: int


def _positive_int(value: Any) -> int:
    try:
        return abs(int(str(value or "0").replace(",", "").strip()))
    except (TypeError, ValueError):
        return 0


def _parse_response(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ResearchError("ka10080_response_not_json") from exc
    if not isinstance(payload, dict):
        raise ResearchError("ka10080_response_not_object")
    try:
        return_code = int(payload.get("return_code", -1))
    except (TypeError, ValueError):
        return_code = -1
    if response.status_code != 200:
        raise ResearchError(f"ka10080_http_{response.status_code}")
    if return_code != 0:
        raise ResearchError(f"ka10080_return_{return_code}")
    return payload


def fetch_krx_history(
    *,
    symbol: str,
    token: str,
    start_date: date,
    end_date: date,
    expected_trading_day_count: int,
    max_pages: int = 120,
    page_delay_sec: float = 0.2,
    post: Callable[..., requests.Response] = requests.post,
) -> tuple[list[Bar], dict[str, Any]]:
    """Fetch widget-owned research OHLCV without auth/account/order mutation."""
    if symbol not in SYMBOLS:
        raise ValueError("symbol_not_in_widget_research_allowlist")
    if start_date < CLEAN_BASELINE_DATE or start_date > end_date:
        raise ValueError("invalid_clean_baseline_date_range")
    if int(expected_trading_day_count) <= HOLDOUT_DAYS:
        raise ValueError("expected_trading_day_count_below_research_minimum")
    clean_token = str(token or "").replace("Bearer ", "").strip()
    if not clean_token:
        raise ResearchError("cached_token_missing")

    # Runtime signals are intentionally KRX-only. Do not calibrate from the
    # integrated-SOR suffix because that would mix NXT tape into a policy whose
    # live session/provenance contract is KRX_REGULAR.
    request_code = symbol
    url = kiwoom_utils.get_api_url("/api/dostk/chart")
    unique: dict[datetime, Bar] = {}
    cont_yn, next_key = "N", ""
    oldest_seen: date | None = None
    invalid_row_count = duplicate_row_count = out_of_session_row_count = 0
    page_count = 0
    request_count = 0
    rate_limit_retry_count = 0
    start_date_fully_bracketed = False
    continuation_exhausted = False
    for page_index in range(max(1, int(max_pages))):
        response: requests.Response | None = None
        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            response = post(
                url,
                headers={
                    "Content-Type": "application/json;charset=UTF-8",
                    "authorization": f"Bearer {clean_token}",
                    "cont-yn": cont_yn,
                    "next-key": next_key,
                    "api-id": "ka10080",
                },
                json={
                    "stk_cd": request_code,
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
                timeout=(5, 30),
            )
            request_count += 1
            if response.status_code != 429:
                break
            if attempt >= MAX_RATE_LIMIT_RETRIES:
                raise ResearchError("ka10080_rate_limit_retry_exhausted")
            rate_limit_retry_count += 1
            raw_retry_after = str(response.headers.get("Retry-After", "") or "")
            try:
                retry_after = float(raw_retry_after)
            except ValueError:
                retry_after = float(2**attempt)
            time_module.sleep(max(0.2, min(MAX_RETRY_AFTER_SEC, retry_after)))
        if response is None:
            raise ResearchError("ka10080_response_missing")
        page_count += 1
        payload = _parse_response(response)
        rows = payload.get("stk_min_pole_chart_qry")
        if not isinstance(rows, list):
            raise ResearchError("ka10080_rows_contract_invalid")
        for raw in rows:
            if not isinstance(raw, dict):
                invalid_row_count += 1
                continue
            raw_timestamp = str(raw.get("cntr_tm") or "").strip()[:14]
            try:
                timestamp = datetime.strptime(raw_timestamp, "%Y%m%d%H%M%S").replace(
                    tzinfo=KST
                )
            except ValueError:
                invalid_row_count += 1
                continue
            oldest_seen = (
                timestamp.date()
                if oldest_seen is None
                else min(oldest_seen, timestamp.date())
            )
            if not time(9, 0) <= timestamp.time() < time(15, 30):
                out_of_session_row_count += 1
                continue
            prices = (
                _positive_int(raw.get("open_pric")),
                _positive_int(raw.get("high_pric")),
                _positive_int(raw.get("low_pric")),
                _positive_int(raw.get("cur_prc")),
            )
            if (
                min(prices) <= 0
                or prices[1] < max(prices[0], prices[2], prices[3])
                or prices[2] > min(prices[0], prices[1], prices[3])
            ):
                invalid_row_count += 1
                continue
            bar = Bar(
                timestamp=timestamp,
                open_price=prices[0],
                high_price=prices[1],
                low_price=prices[2],
                close_price=prices[3],
                volume=_positive_int(raw.get("trde_qty")),
            )
            if timestamp in unique:
                duplicate_row_count += 1
                if unique[timestamp] != bar:
                    raise ResearchError("ka10080_conflicting_duplicate_bar")
            unique[timestamp] = bar
        if oldest_seen is not None and oldest_seen < start_date:
            start_date_fully_bracketed = True
            break
        cont_yn = str(response.headers.get("cont-yn", "N") or "N").upper()
        next_key = str(response.headers.get("next-key", "") or "").strip()
        if cont_yn != "Y":
            continuation_exhausted = True
            break
        if not next_key:
            raise ResearchError("ka10080_continuation_key_missing")
        if page_index + 1 < max_pages and page_delay_sec > 0:
            time_module.sleep(page_delay_sec)

    bars = [
        bar
        for timestamp, bar in sorted(unique.items())
        if start_date <= timestamp.date() <= end_date
    ]
    trading_dates = sorted({bar.timestamp.date().isoformat() for bar in bars})
    source_quality_status = (
        "PASS"
        if start_date_fully_bracketed
        and invalid_row_count == 0
        and len(trading_dates) == int(expected_trading_day_count)
        and trading_dates[0] == start_date.isoformat()
        and trading_dates[-1] == end_date.isoformat()
        else "FAIL"
    )
    meta = {
        "symbol": symbol,
        "request_code": request_code,
        "api_id": "ka10080",
        "market": "KRX_regular",
        "api_url": url,
        "page_count": page_count,
        "request_count": request_count,
        "rate_limit_retry_count": rate_limit_retry_count,
        "bar_count": len(bars),
        "trading_date_count": len(trading_dates),
        "expected_trading_date_count": int(expected_trading_day_count),
        "oldest_source_date": trading_dates[0] if trading_dates else None,
        "latest_source_date": trading_dates[-1] if trading_dates else None,
        "start_date_fully_bracketed": start_date_fully_bracketed,
        "continuation_exhausted": continuation_exhausted,
        "invalid_row_count": invalid_row_count,
        "duplicate_row_count": duplicate_row_count,
        "out_of_session_row_count": out_of_session_row_count,
        "source_quality_status": source_quality_status,
    }
    if source_quality_status != "PASS":
        raise ResearchError(f"{symbol}_source_quality_{source_quality_status.lower()}")
    return bars, meta


def policy_grid() -> Iterable[SignalPolicy]:
    for segment in SEGMENTS:
        anchor_lookbacks = [
            *(("rolling", lookback) for lookback in LOOKBACK_GRID),
            ("session", min(LOOKBACK_GRID)),
        ]
        max_chase_grid = (
            MORNING_MAX_RECLAIM_CHASE_TICK_GRID
            if segment == "morning"
            else (BASE_MAX_RECLAIM_CHASE_TICKS,)
        )
        for anchor_mode, lookback in anchor_lookbacks:
            for drawdown in DRAWDOWN_GRID:
                for near_low in NEAR_LOW_GRID:
                    for reclaim_ticks in RECLAIM_TICK_GRID:
                        for target_bps in TARGET_BPS_GRID:
                            for max_chase_ticks in max_chase_grid:
                                yield SignalPolicy(
                                    segment,
                                    lookback,
                                    drawdown,
                                    near_low,
                                    reclaim_ticks,
                                    target_bps,
                                    anchor_mode=anchor_mode,
                                    minimum_history_bars=min(15, lookback),
                                    max_reclaim_chase_ticks=max_chase_ticks,
                                )


def _clean_trading_dates(end_date: date) -> list[date]:
    dates: list[date] = []
    current = CLEAN_BASELINE_DATE
    while current <= end_date:
        if is_krx_trading_day(current):
            dates.append(current)
        current += timedelta(days=1)
    if len(dates) <= HOLDOUT_DAYS + 8:
        raise ValueError("clean_baseline_sample_below_discovery_floor")
    return dates


def _group_bars(bars: list[Bar]) -> dict[date, tuple[Bar, ...]]:
    grouped: dict[date, list[Bar]] = {}
    for bar in bars:
        grouped.setdefault(bar.timestamp.date(), []).append(bar)
    return {
        trade_date: tuple(sorted(rows, key=lambda row: row.timestamp))
        for trade_date, rows in sorted(grouped.items())
    }


def _daily_source_coverage(
    grouped: dict[date, tuple[Bar, ...]], expected_dates: list[date]
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for trade_date in expected_dates:
        rows = grouped.get(trade_date, ())
        positive_volume_count = sum(row.volume > 0 for row in rows)
        positive_volume_ratio = positive_volume_count / len(rows) if rows else 0.0
        first_time = rows[0].timestamp.time() if rows else None
        last_time = rows[-1].timestamp.time() if rows else None
        reasons: list[str] = []
        if len(rows) < 300:
            reasons.append("bar_count_below_300")
        if first_time is None or first_time > time(9, 5):
            reasons.append("regular_open_not_covered")
        # ka10080 labels the completed 15:19~15:20 interval as 15:19.
        if last_time is None or last_time < time(15, 19):
            reasons.append("regular_close_not_covered")
        if positive_volume_ratio < 0.90:
            reasons.append("positive_volume_ratio_below_0p90")
        if reasons:
            failures.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "bar_count": len(rows),
                    "first_time": first_time.isoformat() if first_time else None,
                    "last_time": last_time.isoformat() if last_time else None,
                    "positive_volume_ratio": round(positive_volume_ratio, 6),
                    "reasons": reasons,
                }
            )
    failed_dates = {row["trade_date"] for row in failures}
    qualified_dates = [
        item.isoformat()
        for item in expected_dates
        if item.isoformat() not in failed_dates
    ]
    status = (
        "PASS"
        if not failures
        else (
            "PASS_WITH_DATE_EXCLUSIONS"
            if len(qualified_dates) > HOLDOUT_DAYS + 8
            else "FAIL"
        )
    )
    return {
        "status": status,
        "minimum_bar_count": 300,
        "minimum_positive_volume_ratio": 0.90,
        "required_first_time_at_or_before": "09:05:00",
        "required_last_time_at_or_after": "15:19:00",
        "failed_date_count": len(failures),
        "failed_dates": failures,
        "qualified_date_count": len(qualified_dates),
        "qualified_dates": qualified_dates,
    }


def _contiguous(rows: tuple[Bar, ...]) -> bool:
    return all(
        current.timestamp - previous.timestamp == timedelta(minutes=1)
        for previous, current in zip(rows, rows[1:])
    )


def _trend_not_down(rows: tuple[Bar, ...], end_index: int, horizon: int) -> bool:
    if end_index < horizon:
        return False
    window = rows[end_index - horizon : end_index + 1]
    if not _contiguous(window):
        return False
    tick = get_tick_size(window[-1].close_price)
    net = window[-1].close_price - window[0].close_price
    deltas = [
        current.close_price - previous.close_price
        for previous, current in zip(window, window[1:])
    ]
    negative = sum(value < 0 for value in deltas)
    return not (net < -tick and negative >= max(2, horizon - 1))


def _setup_feature(
    rows: tuple[Bar, ...],
    index: int,
    lookback: int,
    *,
    anchor_mode: str = "rolling",
    minimum_history_bars: int | None = None,
) -> tuple[float, float] | None:
    minimum_history = (
        lookback if minimum_history_bars is None else int(minimum_history_bars)
    )
    if minimum_history < 2 or minimum_history > lookback or index + 1 < minimum_history:
        return None
    if anchor_mode == "session":
        window = rows[: index + 1]
    elif anchor_mode == "rolling":
        window = rows[max(0, index - lookback + 1) : index + 1]
    else:
        return None
    if not _contiguous(window):
        return None
    rolling_high = max(row.high_price for row in window)
    rolling_low = min(row.low_price for row in window)
    close = rows[index].close_price
    if min(rolling_high, rolling_low, close) <= 0:
        return None
    return (
        (rolling_high - close) / rolling_high * 100.0,
        (close - rolling_low) / rolling_low * 100.0,
    )


def _volume_state(rows: tuple[Bar, ...], index: int) -> tuple[str, float | None]:
    prior = [row.volume for row in rows[max(0, index - 5) : index] if row.volume > 0]
    current = rows[index].volume
    if not prior or current <= 0:
        return "ENTRY_CAUTION", None
    ratio = current / median(prior)
    return ("ENTRY_READY" if ratio >= 1.0 else "ENTRY_CAUTION"), ratio


def _find_entry(
    rows: tuple[Bar, ...],
    setup_index: int,
    policy: SignalPolicy,
    *,
    segment_end: time,
) -> tuple[int, int, str, float | None] | None:
    setup = rows[setup_index]
    reclaim_price = move_price_by_ticks(setup.close_price, policy.reclaim_ticks)
    last_index = min(len(rows) - 2, setup_index + policy.setup_valid_bars)
    for index in range(setup_index + 1, last_index + 1):
        current = rows[index]
        entry_index = index + 1
        if (
            current.timestamp.time() >= segment_end
            or rows[entry_index].timestamp.time() >= segment_end
        ):
            break
        if current.timestamp - rows[index - 1].timestamp != timedelta(minutes=1):
            break
        if (
            current.close_price >= reclaim_price
            and current.close_price >= current.open_price
            and _trend_not_down(rows, index, 3)
            and _trend_not_down(rows, index, 5)
        ):
            entry_price = clamp_price_to_tick(rows[entry_index].open_price)
            support = min(row.low_price for row in rows[setup_index:entry_index])
            maximum_entry = move_price_by_ticks(
                reclaim_price, policy.max_reclaim_chase_ticks
            )
            conservative_chase_check_price = move_price_by_ticks(entry_price, 1)
            if entry_price < support:
                return None
            if conservative_chase_check_price > maximum_entry:
                continue
            state, volume_ratio = _volume_state(rows, index)
            return entry_index, entry_price, state, volume_ratio
    return None


def _exit_episode(
    rows: tuple[Bar, ...],
    *,
    entry_index: int,
    entry_price: int,
    support: int,
    target_bps: int,
) -> dict[str, Any]:
    target_price = move_price_up_by_bps(entry_price, target_bps)
    peak = entry_price
    consecutive_support_breaks = 0
    exit_index = len(rows) - 1
    exit_price = rows[-1].close_price
    reason = "session_end"
    for index in range(entry_index, len(rows)):
        bar = rows[index]
        if bar.timestamp.time() >= FORCE_FLAT_TIME:
            exit_index, exit_price, reason = index, bar.close_price, "force_flat"
            break
        peak = max(peak, bar.high_price)
        support_broken = bar.close_price < support
        consecutive_support_breaks = (
            consecutive_support_breaks + 1 if support_broken else 0
        )
        adverse_ready = bool(
            consecutive_support_breaks >= 2 and not _trend_not_down(rows, index, 3)
        )
        target_touched = bar.high_price >= target_price
        if adverse_ready and target_touched:
            exit_index, exit_price, reason = (
                index,
                bar.close_price,
                "same_bar_conflict_adverse",
            )
            break
        if adverse_ready:
            exit_index, exit_price, reason = (
                index,
                bar.close_price,
                "confirmed_support_break",
            )
            break
        if target_touched:
            exit_index, exit_price, reason = index, target_price, "target"
            break
    trade_date = rows[entry_index].timestamp.date()
    cost_contract = comparison_cost_contract(trade_date)
    gross_return = (exit_price / entry_price - 1.0) * 100.0
    net_return = cost_aware_return_pct(gross_return, trade_date=trade_date)
    return {
        "exit_index": exit_index,
        "exit_at": rows[exit_index].timestamp.isoformat(),
        "exit_price": exit_price,
        "exit_reason": reason,
        "target_price": target_price,
        "gross_return_pct": round(gross_return, 6),
        "net_return_pct": round(net_return, 6),
        "round_trip_cost_pct": cost_contract["round_trip_cost_pct"],
        "cost_policy_id": cost_contract["policy_id"],
        "cost_contract_sha256": cost_contract["contract_sha256"],
        "peak_price": peak,
        "peak_return_pct": round((peak / entry_price - 1.0) * 100.0, 6),
    }


def evaluate_policy(
    grouped: dict[date, tuple[Bar, ...]],
    dates: list[date],
    policy: SignalPolicy,
    *,
    include_episodes: bool = False,
) -> dict[str, Any]:
    segment_start, segment_end = SEGMENTS[policy.segment]
    episodes: list[dict[str, Any]] = []
    for trade_date in dates:
        rows = grouped[trade_date]
        minimum_history = (
            policy.lookback_bars
            if policy.minimum_history_bars is None
            else policy.minimum_history_bars
        )
        index = minimum_history - 1
        cooldown_until = -1
        daily_entry_count = 0
        while index < len(rows) - 1:
            if daily_entry_count >= max(ENTRY_CAP_VALUES):
                break
            bar = rows[index]
            if bar.timestamp.time() < segment_start or index < cooldown_until:
                index += 1
                continue
            if bar.timestamp.time() >= segment_end:
                break
            feature = _setup_feature(
                rows,
                index,
                policy.lookback_bars,
                anchor_mode=policy.anchor_mode,
                minimum_history_bars=minimum_history,
            )
            if feature is None:
                index += 1
                continue
            drawdown, near_low = feature
            if (
                drawdown + 1e-12 < policy.drawdown_pct
                or near_low - 1e-12 > policy.near_low_pct
            ):
                index += 1
                continue
            found = _find_entry(rows, index, policy, segment_end=segment_end)
            if found is None:
                index += 1
                continue
            entry_index, entry_price, state, volume_ratio = found
            support = min(row.low_price for row in rows[index:entry_index])
            outcome = _exit_episode(
                rows,
                entry_index=entry_index,
                entry_price=entry_price,
                support=support,
                target_bps=policy.target_bps,
            )
            daily_entry_count += 1
            episodes.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "daily_entry_ordinal": daily_entry_count,
                    "setup_at": bar.timestamp.isoformat(),
                    "signal_at": rows[entry_index - 1].timestamp.isoformat(),
                    "entry_at": rows[entry_index].timestamp.isoformat(),
                    "entry_price": entry_price,
                    "entry_state": state,
                    "volume_ratio": (
                        round(volume_ratio, 6) if volume_ratio is not None else None
                    ),
                    "support": support,
                    "drawdown_pct": round(drawdown, 6),
                    "near_low_pct": round(near_low, 6),
                    **outcome,
                }
            )
            index = int(outcome["exit_index"]) + policy.reentry_cooldown_bars
            cooldown_until = index
    result = _summarize_episodes(episodes)
    result["entry_cap_comparison"] = _entry_cap_comparison(episodes)
    if include_episodes:
        result["episodes"] = episodes
    return result


def _subset_evaluation(evaluation: dict[str, Any], dates: list[date]) -> dict[str, Any]:
    """Summarize an already simulated policy over an exact date subset.

    Policy episodes are independent by trading date. Reusing the full
    calibration simulation avoids replaying the same minute bars separately
    for the first half, second half, and full window without changing setup,
    exit, cooldown, or entry-cap semantics.
    """

    allowed_dates = {value.isoformat() for value in dates}
    episodes = [
        row
        for row in evaluation.get("episodes", [])
        if isinstance(row, dict) and row.get("trade_date") in allowed_dates
    ]
    result = _summarize_episodes(episodes)
    result["entry_cap_comparison"] = _entry_cap_comparison(episodes)
    result["episodes"] = episodes
    return result


def _summarize_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    attempted_notional = sum(row["entry_price"] for row in episodes)
    pnl = sum(row["entry_price"] * row["net_return_pct"] / 100.0 for row in episodes)
    return {
        "episode_count": len(episodes),
        "target_count": sum(row["exit_reason"] == "target" for row in episodes),
        "adverse_exit_count": sum(
            row["exit_reason"]
            in {"confirmed_support_break", "same_bar_conflict_adverse"}
            for row in episodes
        ),
        "force_flat_count": sum(row["exit_reason"] == "force_flat" for row in episodes),
        "entry_ready_count": sum(
            row["entry_state"] == "ENTRY_READY" for row in episodes
        ),
        "entry_caution_count": sum(
            row["entry_state"] == "ENTRY_CAUTION" for row in episodes
        ),
        "notional_weighted_ev_pct": (
            round(pnl / attempted_notional * 100.0, 6) if attempted_notional else None
        ),
        "worst_episode_return_pct": (
            min(row["net_return_pct"] for row in episodes) if episodes else None
        ),
        "average_peak_return_pct": (
            round(sum(row["peak_return_pct"] for row in episodes) / len(episodes), 6)
            if episodes
            else None
        ),
        "entry_state_breakdown": {
            state: _summarize_episode_subset(
                [row for row in episodes if row["entry_state"] == state]
            )
            for state in ("ENTRY_READY", "ENTRY_CAUTION")
        },
    }


def _entry_cap_comparison(
    episodes: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    comparison: dict[str, dict[str, Any]] = {}
    for cap in ENTRY_CAP_VALUES:
        cumulative = [row for row in episodes if int(row["daily_entry_ordinal"]) <= cap]
        incremental = [
            row for row in episodes if int(row["daily_entry_ordinal"]) == cap
        ]
        incremental_summary = _summarize_episode_subset(incremental)
        incremental_ev = incremental_summary.get("notional_weighted_ev_pct")
        comparison[str(cap)] = {
            "cumulative": _summarize_episodes(cumulative),
            "incremental": incremental_summary,
            "incremental_ev_positive": bool(
                incremental_summary["episode_count"] > 0
                and incremental_ev is not None
                and float(incremental_ev) > 0.0
            ),
        }
    return comparison


def _summarize_episode_subset(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    attempted_notional = sum(row["entry_price"] for row in episodes)
    pnl = sum(row["entry_price"] * row["net_return_pct"] / 100.0 for row in episodes)
    return {
        "episode_count": len(episodes),
        "target_count": sum(row["exit_reason"] == "target" for row in episodes),
        "notional_weighted_ev_pct": (
            round(pnl / attempted_notional * 100.0, 6) if attempted_notional else None
        ),
        "worst_episode_return_pct": (
            min(row["net_return_pct"] for row in episodes) if episodes else None
        ),
    }


def _positive_ev(summary: dict[str, Any]) -> bool:
    value = summary.get("notional_weighted_ev_pct")
    return value is not None and float(value) > 0.0


def _metric_float(summary: dict[str, Any], key: str, *, default: float) -> float:
    value = summary.get(key)
    return float(value) if value is not None else default


def _incremental_entry_cap_ready(
    comparison: dict[str, dict[str, Any]], cap: int
) -> bool:
    if cap < HIGH_ENTRY_CAP_START:
        return True
    return all(
        comparison.get(str(incremental_cap), {}).get("incremental_ev_positive") is True
        for incremental_cap in range(HIGH_ENTRY_CAP_START, cap + 1)
    )


def _calibration_ready(
    full: dict[str, Any], first: dict[str, Any], second: dict[str, Any]
) -> bool:
    return bool(
        full["episode_count"] >= 10
        and first["episode_count"] >= 4
        and second["episode_count"] >= 4
        and _positive_ev(first)
        and _positive_ev(second)
        and _metric_float(full, "worst_episode_return_pct", default=-999.0) > -3.0
    )


def discover_symbol_policy(
    bars: list[Bar], *, expected_dates: list[date]
) -> dict[str, Any]:
    grouped = _group_bars(bars)
    if set(grouped) != set(expected_dates):
        raise ResearchError("symbol_trading_dates_mismatch")
    calibration_dates = expected_dates[:-HOLDOUT_DAYS]
    holdout_dates = expected_dates[-HOLDOUT_DAYS:]
    date_split = {
        "qualified_trading_date_count": len(expected_dates),
        "calibration_trading_date_count": len(calibration_dates),
        "holdout_trading_date_count": len(holdout_dates),
        "calibration_start": calibration_dates[0].isoformat(),
        "calibration_end": calibration_dates[-1].isoformat(),
        "holdout_start": holdout_dates[0].isoformat(),
        "holdout_end": holdout_dates[-1].isoformat(),
    }
    split = max(1, len(calibration_dates) // 2)
    first_dates = calibration_dates[:split]
    second_dates = calibration_dates[split:]
    candidates: list[
        tuple[
            float,
            SignalPolicy,
            int,
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
            dict[str, dict[str, Any]],
            dict[str, dict[str, Any]],
            dict[str, dict[str, Any]],
            dict[str, Any],
        ]
    ] = []
    best_diagnostic: (
        tuple[
            float,
            SignalPolicy,
            int,
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
        ]
        | None
    ) = None
    gate_counts = {
        "full_sample_positive": 0,
        "both_half_sample": 0,
        "both_half_positive": 0,
        "worst_loss_guard": 0,
        "high_entry_cap_incremental_positive": 0,
    }
    evaluated = 0
    for policy in policy_grid():
        full_evaluation = evaluate_policy(
            grouped,
            calibration_dates,
            policy,
            include_episodes=True,
        )
        first_evaluation = _subset_evaluation(full_evaluation, first_dates)
        second_evaluation = _subset_evaluation(full_evaluation, second_dates)
        full_comparison = full_evaluation["entry_cap_comparison"]
        first_comparison = first_evaluation["entry_cap_comparison"]
        second_comparison = second_evaluation["entry_cap_comparison"]
        for entry_cap in ENTRY_CAP_VALUES:
            evaluated += 1
            full = full_comparison[str(entry_cap)]["cumulative"]
            first = first_comparison[str(entry_cap)]["cumulative"]
            second = second_comparison[str(entry_cap)]["cumulative"]
            if full["episode_count"] < 10 or not _positive_ev(full):
                continue
            gate_counts["full_sample_positive"] += 1
            if first["episode_count"] >= 4 and second["episode_count"] >= 4:
                gate_counts["both_half_sample"] += 1
                first_ev = _metric_float(
                    first, "notional_weighted_ev_pct", default=-999.0
                )
                second_ev = _metric_float(
                    second, "notional_weighted_ev_pct", default=-999.0
                )
                diagnostic_score = (
                    min(first_ev, second_ev)
                    * min(first["episode_count"], second["episode_count"])
                    / (min(first["episode_count"], second["episode_count"]) + 6.0)
                )
                if best_diagnostic is None or diagnostic_score > best_diagnostic[0]:
                    best_diagnostic = (
                        diagnostic_score,
                        policy,
                        entry_cap,
                        full,
                        first,
                        second,
                    )
            if _positive_ev(first) and _positive_ev(second):
                gate_counts["both_half_positive"] += 1
            if _metric_float(full, "worst_episode_return_pct", default=-999.0) > -3.0:
                gate_counts["worst_loss_guard"] += 1
            high_cap_ready = all(
                _incremental_entry_cap_ready(comparison, entry_cap)
                for comparison in (
                    full_comparison,
                    first_comparison,
                    second_comparison,
                )
            )
            if high_cap_ready:
                gate_counts["high_entry_cap_incremental_positive"] += 1
            if not _calibration_ready(full, first, second) or not high_cap_ready:
                continue
            score = (
                min(
                    float(first["notional_weighted_ev_pct"]),
                    float(second["notional_weighted_ev_pct"]),
                )
                * min(first["episode_count"], second["episode_count"])
                / (min(first["episode_count"], second["episode_count"]) + 6.0)
            )
            candidates.append(
                (
                    score,
                    policy,
                    entry_cap,
                    full,
                    first,
                    second,
                    full_comparison,
                    first_comparison,
                    second_comparison,
                    full_evaluation,
                )
            )
    if not candidates:
        diagnostic_payload = None
        if best_diagnostic is not None:
            diagnostic_score, policy, entry_cap, full, first, second = best_diagnostic
            diagnostic_payload = {
                "parameters": {
                    **asdict(policy),
                    "max_completed_entries_per_day": entry_cap,
                },
                "calibration": full,
                "calibration_first_half": first,
                "calibration_second_half": second,
                "robust_calibration_score": round(diagnostic_score, 6),
            }
        return {
            "decision": "no_robust_calibration_policy",
            "grid_candidate_count": evaluated,
            "calibration_gate_counts": gate_counts,
            "best_diagnostic_candidate": diagnostic_payload,
            "date_split": date_split,
            "runtime_effect": False,
        }
    base_candidates = [
        item for item in candidates if int(item[2]) < HIGH_ENTRY_CAP_START
    ]
    (base_candidates or candidates).sort(
        key=lambda item: (item[0], item[3]["episode_count"]), reverse=True
    )
    (
        score,
        selected,
        base_entry_cap,
        calibration,
        first,
        second,
        calibration_cap_comparison,
        first_cap_comparison,
        second_cap_comparison,
        calibration_selected_evaluation,
    ) = (base_candidates or candidates)[0]
    calibration_selected_cap = base_entry_cap
    for high_cap in range(HIGH_ENTRY_CAP_START, max(ENTRY_CAP_VALUES) + 1):
        if any(
            candidate_policy == selected and candidate_cap == high_cap
            for (
                _,
                candidate_policy,
                candidate_cap,
                *_rest,
            ) in candidates
        ):
            calibration_selected_cap = high_cap
    holdout_evaluation = evaluate_policy(
        grouped, holdout_dates, selected, include_episodes=True
    )
    holdout_cap_comparison = holdout_evaluation["entry_cap_comparison"]
    selected_entry_cap = calibration_selected_cap

    def holdout_cap_ready(cap: int) -> bool:
        summary = holdout_cap_comparison[str(cap)]["cumulative"]
        return bool(
            summary["episode_count"] >= 4
            and _positive_ev(summary)
            and _metric_float(summary, "worst_episode_return_pct", default=-999.0)
            > -3.0
            and _incremental_entry_cap_ready(holdout_cap_comparison, cap)
        )

    calibration = calibration_cap_comparison[str(selected_entry_cap)]["cumulative"]
    first = first_cap_comparison[str(selected_entry_cap)]["cumulative"]
    second = second_cap_comparison[str(selected_entry_cap)]["cumulative"]
    score = (
        min(
            float(first["notional_weighted_ev_pct"]),
            float(second["notional_weighted_ev_pct"]),
        )
        * min(first["episode_count"], second["episode_count"])
        / (min(first["episode_count"], second["episode_count"]) + 6.0)
    )
    holdout = dict(holdout_cap_comparison[str(selected_entry_cap)]["cumulative"])
    holdout["episodes"] = [
        row
        for row in holdout_evaluation["episodes"]
        if int(row["daily_entry_ordinal"]) <= selected_entry_cap
    ]
    full_window_cap_comparison = _entry_cap_comparison(
        [
            *calibration_selected_evaluation["episodes"],
            *holdout_evaluation["episodes"],
        ]
    )
    full_window = full_window_cap_comparison[str(selected_entry_cap)]["cumulative"]
    holdout_pass = holdout_cap_ready(selected_entry_cap)
    return {
        "decision": (
            "holdout_pass_widget_signal_policy_candidate"
            if holdout_pass
            else "holdout_failed_no_widget_runtime_promotion"
        ),
        "selected_policy": {
            **asdict(selected),
            "max_completed_entries_per_day": selected_entry_cap,
        },
        "calibration": calibration,
        "calibration_first_half": first,
        "calibration_second_half": second,
        "holdout": holdout,
        "full_window": full_window,
        "entry_cap_comparison": {
            "calibration": calibration_cap_comparison,
            "calibration_first_half": first_cap_comparison,
            "calibration_second_half": second_cap_comparison,
            "holdout": holdout_cap_comparison,
            "full_window": full_window_cap_comparison,
        },
        "robust_calibration_score": round(score, 6),
        "grid_candidate_count": evaluated,
        "calibration_ready_candidate_count": len(candidates),
        "calibration_gate_counts": gate_counts,
        "date_split": date_split,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def build_report(
    *, sources: dict[str, tuple[list[Bar], dict[str, Any]]], end_date: date
) -> dict[str, Any]:
    if set(sources) != set(SYMBOLS):
        raise ResearchError("widget_symbol_source_set_mismatch")
    expected_dates = _clean_trading_dates(end_date)
    results: dict[str, Any] = {}
    source_meta: dict[str, Any] = {}
    for symbol, name in SYMBOLS.items():
        bars, meta = sources[symbol]
        if meta.get("source_quality_status") != "PASS":
            raise ResearchError(f"{symbol}_source_quality_not_pass")
        coverage = _daily_source_coverage(_group_bars(bars), expected_dates)
        if coverage["status"] == "FAIL":
            raise ResearchError(f"{symbol}_daily_source_coverage_fail")
        qualified_dates = [
            date.fromisoformat(item) for item in coverage["qualified_dates"]
        ]
        qualified_date_set = set(qualified_dates)
        qualified_bars = [
            bar for bar in bars if bar.timestamp.date() in qualified_date_set
        ]
        result = discover_symbol_policy(
            qualified_bars,
            expected_dates=qualified_dates,
        )
        results[symbol] = {"symbol": symbol, "name": name, **result}
        source_meta[symbol] = {**meta, "daily_source_coverage": coverage}
    pass_symbols = [
        symbol
        for symbol, result in results.items()
        if result["decision"] == "holdout_pass_widget_signal_policy_candidate"
    ]
    return {
        "schema": REPORT_SCHEMA,
        "status": "complete",
        "decision": (
            "widget_signal_policy_candidates_ready"
            if pass_symbols
            else "no_widget_signal_policy_candidate"
        ),
        "start_date": CLEAN_BASELINE_DATE.isoformat(),
        "first_source_trading_date": expected_dates[0].isoformat(),
        "end_date": end_date.isoformat(),
        "trading_date_count": len(expected_dates),
        "calibration_trading_date_count": len(expected_dates) - HOLDOUT_DAYS,
        "holdout_trading_date_count": HOLDOUT_DAYS,
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "symbols": results,
        "passed_symbols": pass_symbols,
        "source_meta": source_meta,
        "metric_contract": METRIC_CONTRACT,
        "owner_contract": OWNER_CONTRACT,
        "official_reference": OFFICIAL_REFERENCE,
        "comparison_cost_contract": comparison_cost_contract(end_date),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "collector_created": False,
        "service_started": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Widget symbol signal policy research — {report['end_date']}",
        "",
        "Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.",
        "",
        "| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for symbol, result in report["symbols"].items():
        diagnostic = result.get("best_diagnostic_candidate") or {}
        policy = result.get("selected_policy") or diagnostic.get("parameters") or {}
        calibration = result.get("calibration") or diagnostic.get("calibration") or {}
        holdout = result.get("holdout") or {}
        lines.append(
            "| {symbol} | {name} | {decision} | {segment} | {cap} | {cal}/{hold} | {cal_ev}/{hold_ev} | {worst} |".format(
                symbol=symbol,
                name=result["name"],
                decision=result["decision"],
                segment=policy.get("segment", "-"),
                cap=policy.get("max_completed_entries_per_day", "-"),
                cal=calibration.get("episode_count", "-"),
                hold=holdout.get("episode_count", "-"),
                cal_ev=calibration.get("notional_weighted_ev_pct", "-"),
                hold_ev=holdout.get("notional_weighted_ev_pct", "-"),
                worst=holdout.get("worst_episode_return_pct", "-"),
            )
        )
    lines.extend(
        [
            "",
            "A row without holdout values is diagnostic-only and has no promotion authority.",
            "Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.",
            "Live promotion requires a separate reviewed collector/contract/execution implementation.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    report: dict[str, Any], *, output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"widget_symbol_signal_policy_research_{report['end_date']}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def resolve_completed_research_end_date(now: datetime | None = None) -> date:
    """Return the latest KRX session whose regular close is complete."""

    current = (now or datetime.now(KST)).astimezone(KST)
    candidate = current.date()
    if current.time().replace(tzinfo=None) < time(15, 30) or not is_krx_trading_day(
        candidate
    ):
        candidate -= timedelta(days=1)
        while not is_krx_trading_day(candidate):
            candidate -= timedelta(days=1)
    return candidate


def _default_end_date(now: datetime | None = None) -> date:
    """Compatibility wrapper for existing callers and tests."""

    return resolve_completed_research_end_date(now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end-date")
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--page-delay-sec", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    end_date = (
        date.fromisoformat(args.end_date)
        if args.end_date
        else resolve_completed_research_end_date()
    )
    expected_dates = _clean_trading_dates(end_date)
    token = kiwoom_utils.get_cached_kiwoom_token()
    if not token:
        raise ResearchError("cached_token_missing_no_issue_or_refresh_allowed")
    sources = {
        symbol: fetch_krx_history(
            symbol=symbol,
            token=token,
            start_date=CLEAN_BASELINE_DATE,
            end_date=end_date,
            max_pages=args.max_pages,
            page_delay_sec=args.page_delay_sec,
            expected_trading_day_count=len(expected_dates),
        )
        for symbol in SYMBOLS
    }
    report = build_report(sources=sources, end_date=end_date)
    paths = (
        write_report(report, output_dir=args.output_dir) if args.write else (None, None)
    )
    print(
        json.dumps(
            {
                "decision": report["decision"],
                "passed_symbols": report["passed_symbols"],
                "json_path": str(paths[0]) if paths[0] else None,
                "markdown_path": str(paths[1]) if paths[1] else None,
                "runtime_effect": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
