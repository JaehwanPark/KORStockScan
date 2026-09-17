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
import hashlib
import inspect
from copy import deepcopy
import fcntl
import zlib
from collections import deque
from array import array
from bisect import bisect_left
import json
import os
import signal
import tempfile
import time as time_module
from functools import lru_cache
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Callable, Collection, Iterable
from zoneinfo import ZoneInfo

import requests

from src.trading.order.tick_utils import (
    clamp_price_to_tick,
    get_tick_size,
    move_price_by_ticks,
    move_price_up_by_bps,
)
from src.engine.monitoring.machine_recommendation_identity import bind_recommendation
from src.engine.monitoring.machine_candidate_lifecycle import (
    completed_daily_recommendation_symbols,
    widget_long_term_pruned_symbols,
)
from src.engine.monitoring.widget_execution_quality import load_execution_incidents
from src.engine.monitoring.policy_research_economics import (
    modeled_summary,
    modeled_cap_summaries,
    joint_capital_demand,
    research_universe_handoff,
    load_research_census,
)
from src.engine.monitoring.widget_signal_quality import (
    component_arms,
    objective_comparison,
    select_policy_component,
)
from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    cost_aware_return_pct,
)
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

REPORT_SCHEMA = "widget_symbol_signal_policy_research_v4"
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
DEFAULT_RESEARCH_WATCH_CONFIG_PATH = (
    DATA_DIR / "config" / "widget_research_watch_symbols.json"
)
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
    "commit_sha": "953e5dbff123f437ab4d11a78a95191a685eb51f",
    "retrieved_at_kst": "2026-09-16T12:10:00+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core/errors.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contract": "POST /api/dostk/chart; api-id=ka10080",
}


def load_symbol_universe(
    *,
    observed_date: date,
    config_path: Path = DEFAULT_RESEARCH_WATCH_CONFIG_PATH,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return fixed, research-watch, and completed auto-discovery symbols."""

    # Import lazily: the collector shares the runtime policy reference and the
    # runtime policy imports this module's research contract.
    from src.engine.monitoring.widget_research_watch_collector import load_config

    config = load_config(observed_date=observed_date, config_path=config_path)
    pruned = widget_long_term_pruned_symbols(observed_date)
    universe = dict(SYMBOLS)
    origins = {symbol: "established_widget_symbol" for symbol in SYMBOLS}
    for row in config["symbols"]:
        symbol = str(row["stock_code"])
        name = str(row["stock_name"])
        if symbol in pruned:
            continue
        if symbol in universe and universe[symbol] != name:
            raise ResearchError("widget_research_watch_symbol_name_conflict")
        universe[symbol] = name
        origins[symbol] = "operator_enrolled_research_watch"
    _, discovered = completed_daily_recommendation_symbols(
        observed_date,
        excluded_symbols=set(pruned),
    )
    for symbol, name in discovered.items():
        if symbol in pruned:
            continue
        if symbol in universe and universe[symbol] != name:
            raise ResearchError("widget_auto_discovery_symbol_name_conflict")
        if symbol not in universe:
            universe[symbol] = name
            origins[symbol] = "completed_daily_recommendation_auto_discovery"
    from src.engine.monitoring.research_closed_loop import admission_symbols

    for symbol, name in admission_symbols(observed_date, owner="widget").items():
        if symbol not in universe and symbol not in pruned:
            universe[symbol] = name
            origins[symbol] = "causal_scanner_research_admission"
    return universe, origins


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
    shared_read_control_enabled: bool | None = None,
    allowed_symbols: Collection[str] | None = None,
    allow_short_listing_history: bool = False,
    incremental_source: bool = False,
) -> tuple[list[Bar], dict[str, Any]]:
    """Fetch widget-owned research OHLCV without auth/account/order mutation."""
    if symbol not in (allowed_symbols if allowed_symbols is not None else SYMBOLS):
        raise ValueError("symbol_not_in_widget_research_allowlist")
    if start_date < CLEAN_BASELINE_DATE or start_date > end_date:
        raise ValueError("invalid_clean_baseline_date_range")
    if int(expected_trading_day_count) <= (0 if incremental_source else HOLDOUT_DAYS):
        raise ValueError("expected_trading_day_count_below_research_minimum")
    clean_token = (
        str(kiwoom_utils.resolve_kiwoom_request_token(token) or "")
        .replace("Bearer ", "")
        .strip()
    )
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
    out_of_target_range_row_count = 0
    page_count = 0
    request_count = 0
    rate_limit_retry_count = 0
    shared_read_control = (
        post is requests.post
        if shared_read_control_enabled is None
        else bool(shared_read_control_enabled)
    )
    start_date_fully_bracketed = False
    continuation_exhausted = False
    for page_index in range(max(1, int(max_pages))):
        response: requests.Response | None = None
        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            if shared_read_control:
                admission = kiwoom_utils.acquire_kiwoom_read_capacity(
                    token=clean_token,
                    endpoint=url,
                    request_owner="widget_symbol_signal_policy_research",
                    request_class="source_only",
                    api_id="ka10080",
                    request_code=request_code,
                    max_wait_sec=1.25,
                )
                if not admission.admitted:
                    raise ResearchError(
                        f"ka10080_shared_read_rate_deferred:{admission.reason}"
                    )
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
            try:
                response_body = response.json()
            except ValueError:
                response_body = {}
            rate_limited = kiwoom_utils.is_kiwoom_read_rate_limit(
                http_status_code=response.status_code,
                response_body=response_body,
            )
            if not rate_limited:
                break
            if shared_read_control:
                kiwoom_utils.record_kiwoom_read_rate_limit(
                    token=clean_token,
                    endpoint=url,
                    request_owner="widget_symbol_signal_policy_research",
                    request_class="source_only",
                    api_id="ka10080",
                    request_code=request_code,
                    http_status_code=response.status_code,
                    response_code=(
                        response_body.get("return_code", response_body.get("rt_cd"))
                        if isinstance(response_body, dict)
                        else None
                    ),
                )
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
            if not start_date <= timestamp.date() <= end_date:
                out_of_target_range_row_count += 1
                continue
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
    listing_history_accepted = False
    if allow_short_listing_history and trading_dates:
        expected_suffix: list[str] = []
        candidate = date.fromisoformat(trading_dates[0])
        while candidate <= end_date:
            if is_krx_trading_day(candidate):
                expected_suffix.append(candidate.isoformat())
            candidate += timedelta(days=1)
        listing_history_accepted = bool(
            continuation_exhausted
            and date.fromisoformat(trading_dates[0]) > start_date
            and len(trading_dates) > HOLDOUT_DAYS + 8
            and trading_dates == expected_suffix
        )
    source_quality_status = (
        "PASS"
        if (start_date_fully_bracketed or listing_history_accepted)
        and invalid_row_count == 0
        and (
            listing_history_accepted
            or (
                len(trading_dates) == int(expected_trading_day_count)
                and trading_dates[0] == start_date.isoformat()
            )
        )
        and trading_dates[-1] == end_date.isoformat()
        else "FAIL"
    )
    meta = {
        "retrieved_at_kst": datetime.now(KST).isoformat(),
        "source_content_sha256": canonical_bar_hash(bars),
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
        "listing_history_accepted": listing_history_accepted,
        "continuation_exhausted": continuation_exhausted,
        "invalid_row_count": invalid_row_count,
        "duplicate_row_count": duplicate_row_count,
        "out_of_session_row_count": out_of_session_row_count,
        "out_of_target_range_row_count": out_of_target_range_row_count,
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


@lru_cache(maxsize=4096)
def _policy_cache_key(policy):
    return json.dumps(asdict(policy), sort_keys=True, separators=(",", ":"))


class ReplayContext:
    """Bounded symbol-local setup/reclaim/exit reuse with legacy arithmetic."""

    def __init__(
        self, grouped: dict[date, tuple[Bar, ...]], cache_dir: Path | None = None
    ) -> None:
        self.features: dict[tuple[date, int, str, int], list[Any]] = {}
        self.entries: dict[tuple[Any, ...], Any] = {}
        self.exits: dict[tuple[Any, ...], Any] = {}
        self.grouped = grouped
        self.cache_dir = cache_dir
        self.setup_indices = {}
        self.segment_indices = {}
        self.reclaim_indices = {}
        self.day_pages = {}
        self.dirty_days = set()
        self.day_keys = {}
        self.cache_write_skips = 0
        self.policy_pages = {
            _policy_cache_key(policy): index // 128
            for index, policy in enumerate(policy_grid())
        }
        self.day_results: dict[date, dict[str, Any]] = {}
        self.cached_day_results: dict[date, dict[str, Any]] = {}
        self.cache_hits = self.cache_misses = 0
        self.contract = research_contract_hash() if cache_dir is not None else ""
        self.symbol = ""

    def _policy_page(self, policy):
        key = _policy_cache_key(policy)
        page = self.policy_pages.get(key)
        return (
            page
            if page is not None
            else "extra_" + hashlib.sha256(key.encode()).hexdigest()[:16]
        )

    def _day_path(self, day: date) -> Path:
        if day not in self.day_keys:
            self.day_keys[day] = hashlib.sha256(
                json.dumps(
                    {
                        "source": canonical_bar_hash(self.grouped[day]),
                        "algorithm": self.contract,
                        "cost": comparison_cost_contract(day),
                    },
                    sort_keys=True,
                ).encode()
            ).hexdigest()
        return (
            self.cache_dir
            / f"{day.isoformat()}_{self.day_keys[day]}_p{self.day_pages.get(day, 0)}.json.z"
        )

    def _load_day(self, day: date, policy: SignalPolicy) -> dict[str, Any]:
        page = self._policy_page(policy)
        if self.day_pages.get(day) != page:
            if day in self.dirty_days:
                self._flush_day(day)
            self.day_results.pop(day, None)
            self.cached_day_results.pop(day, None)
            self.day_pages[day] = page
        if day not in self.day_results:
            result = {}
            if self.cache_dir is not None:
                path = self._day_path(day)
                try:
                    if not path.is_symlink() and path.lstat().st_size <= 1024 * 1024:
                        decoder = zlib.decompressobj()
                        raw = decoder.decompress(path.read_bytes(), 8 * 1024 * 1024)
                        if decoder.eof and not decoder.unused_data:
                            payload = json.loads(raw)
                            if (
                                payload.get("checksum")
                                == hashlib.sha256(
                                    json.dumps(
                                        payload["results"],
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ).encode()
                                ).hexdigest()
                            ):
                                result = payload["results"]
                except (OSError, ValueError, KeyError, TypeError, zlib.error):
                    pass
            self.cached_day_results[day] = dict(result)
            self.day_results[day] = result
        return self.day_results[day]

    def read_day(self, day: date, policy: SignalPolicy) -> list[dict[str, Any]] | None:
        if self.cache_dir is None:
            return None
        key = _policy_cache_key(policy)
        self._load_day(day, policy)
        rows = self.cached_day_results[day].get(key)
        if isinstance(rows, list) and all(
            isinstance(row, dict) and row.get("trade_date") == day.isoformat()
            for row in rows
        ):
            self.cache_hits += 1
            return rows
        self.cache_misses += 1
        return None

    def write_day(
        self, day: date, policy: SignalPolicy, rows: list[dict[str, Any]]
    ) -> None:
        if self.cache_dir is None:
            return
        results = self._load_day(day, policy)
        results[_policy_cache_key(policy)] = rows
        self.dirty_days.add(day)

    def _flush_day(self, day):
        if day not in self.dirty_days:
            return
        results = self.day_results[day]
        content = json.dumps(results, sort_keys=True, separators=(",", ":"))
        encoded = zlib.compress(
            json.dumps(
                {
                    "checksum": hashlib.sha256(content.encode()).hexdigest(),
                    "results": results,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
        from src.engine.monitoring.research_closed_loop import optional_cache_write

        if len(encoded) <= 1024 * 1024 and len(content) <= 8 * 1024 * 1024:
            self.cache_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                written = optional_cache_write(
                    self._day_path(day), encoded, cache_root=self.cache_dir.parent
                )
            except (OSError, ValueError):
                written = False
            if not written:
                self.cache_write_skips += 1
        else:
            self.cache_write_skips += 1
        self.dirty_days.discard(day)

    def flush(self) -> None:
        if self.cache_dir is None:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for day in list(self.dirty_days):
            self._flush_day(day)

    def feature(self, day: date, index: int, policy: SignalPolicy) -> Any:
        minimum = (
            policy.lookback_bars
            if policy.minimum_history_bars is None
            else policy.minimum_history_bars
        )
        key = (day, policy.lookback_bars, policy.anchor_mode, minimum)
        if key not in self.features:
            rows = self.grouped[day]
            highs: deque[int] = deque()
            lows: deque[int] = deque()
            last_gap = -1
            values = []
            for i, row in enumerate(rows):
                if i and row.timestamp - rows[i - 1].timestamp != timedelta(minutes=1):
                    last_gap = i
                start = (
                    0
                    if policy.anchor_mode == "session"
                    else max(0, i - policy.lookback_bars + 1)
                )
                while highs and highs[0] < start:
                    highs.popleft()
                while lows and lows[0] < start:
                    lows.popleft()
                while highs and rows[highs[-1]].high_price <= row.high_price:
                    highs.pop()
                while lows and rows[lows[-1]].low_price >= row.low_price:
                    lows.pop()
                highs.append(i)
                lows.append(i)
                high, low, close = (
                    rows[highs[0]].high_price,
                    rows[lows[0]].low_price,
                    row.close_price,
                )
                valid = (
                    policy.anchor_mode in {"session", "rolling"}
                    and 2 <= minimum <= policy.lookback_bars
                    and i + 1 >= minimum
                    and last_gap <= start
                    and min(high, low, close) > 0
                )
                values.append(
                    ((high - close) / high * 100.0, (close - low) / low * 100.0)
                    if valid
                    else None
                )
            self.features[key] = values
        return self.features[key][index]

    def eligible_setup_indices(self, day: date, policy: SignalPolicy):
        minimum = (
            policy.lookback_bars
            if policy.minimum_history_bars is None
            else policy.minimum_history_bars
        )
        key = (
            day,
            policy.segment,
            policy.lookback_bars,
            policy.anchor_mode,
            minimum,
            policy.drawdown_pct,
            policy.near_low_pct,
            policy.setup_valid_bars,
        )
        if key not in self.setup_indices:
            start, end = SEGMENTS[policy.segment]
            indices = array("I")
            rows = self.grouped[day]
            if day not in self.reclaim_indices:
                self.reclaim_indices[day] = array(
                    "I",
                    (
                        i
                        for i, row in enumerate(rows[:-1])
                        if row.close_price >= row.open_price
                        and _trend_not_down(rows, i, 3)
                        and _trend_not_down(rows, i, 5)
                    ),
                )
            reclaim = self.reclaim_indices[day]
            segment_key = (day, policy.segment, minimum)
            if segment_key not in self.segment_indices:
                self.segment_indices[segment_key] = array(
                    "I",
                    (
                        index
                        for index, bar in enumerate(rows[:-1])
                        if index >= minimum - 1 and start <= bar.timestamp.time() < end
                    ),
                )
            for index in self.segment_indices[segment_key]:
                position = bisect_left(reclaim, index + 1)
                if (
                    position >= len(reclaim)
                    or reclaim[position] > index + policy.setup_valid_bars
                ):
                    continue
                feature = self.feature(day, index, policy)
                if (
                    feature is not None
                    and feature[0] + 1e-12 >= policy.drawdown_pct
                    and feature[1] - 1e-12 <= policy.near_low_pct
                ):
                    indices.append(index)
            self.setup_indices[key] = indices
        return self.setup_indices[key]

    def entry(self, day: date, index: int, policy: SignalPolicy, end: time) -> Any:
        key = (
            day,
            index,
            policy.reclaim_ticks,
            policy.setup_valid_bars,
            policy.max_reclaim_chase_ticks,
            end,
        )
        if key not in self.entries:
            if len(self.entries) >= 8192:
                self.entries.clear()
            self.entries[key] = _find_entry(
                self.grouped[day], index, policy, segment_end=end
            )
        return self.entries[key]

    def exit(self, day: date, index: int, price: int, support: int, target: int) -> Any:
        key = (day, index, price, support, target)
        if key not in self.exits:
            if len(self.exits) >= 8192:
                self.exits.clear()
            self.exits[key] = _exit_episode(
                self.grouped[day],
                entry_index=index,
                entry_price=price,
                support=support,
                target_bps=target,
            )
        return self.exits[key]


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
    replay_context: ReplayContext | None = None,
) -> dict[str, Any]:
    segment_start, segment_end = SEGMENTS[policy.segment]
    episodes: list[dict[str, Any]] = []
    for trade_date in dates:
        cached = replay_context.read_day(trade_date, policy) if replay_context else None
        if cached is not None:
            episodes.extend(cached)
            continue
        day_start = len(episodes)
        rows = grouped[trade_date]
        minimum_history = (
            policy.lookback_bars
            if policy.minimum_history_bars is None
            else policy.minimum_history_bars
        )
        index = minimum_history - 1
        cooldown_until = -1
        daily_entry_count = 0
        setup_indices = (
            replay_context.eligible_setup_indices(trade_date, policy)
            if replay_context
            else None
        )
        while index < len(rows) - 1:
            if setup_indices is not None:
                position = bisect_left(setup_indices, max(index, cooldown_until))
                if position >= len(setup_indices):
                    break
                index = setup_indices[position]
            if daily_entry_count >= max(ENTRY_CAP_VALUES):
                break
            bar = rows[index]
            if bar.timestamp.time() < segment_start or index < cooldown_until:
                index += 1
                continue
            if bar.timestamp.time() >= segment_end:
                break
            feature = (
                replay_context.feature(trade_date, index, policy)
                if replay_context
                else _setup_feature(
                    rows,
                    index,
                    policy.lookback_bars,
                    anchor_mode=policy.anchor_mode,
                    minimum_history_bars=minimum_history,
                )
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
            found = (
                replay_context.entry(trade_date, index, policy, segment_end)
                if replay_context
                else _find_entry(rows, index, policy, segment_end=segment_end)
            )
            if found is None:
                index += 1
                continue
            entry_index, entry_price, state, volume_ratio = found
            support = min(row.low_price for row in rows[index:entry_index])
            outcome = (
                replay_context.exit(
                    trade_date, entry_index, entry_price, support, policy.target_bps
                )
                if replay_context
                else _exit_episode(
                    rows,
                    entry_index=entry_index,
                    entry_price=entry_price,
                    support=support,
                    target_bps=policy.target_bps,
                )
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
        if replay_context:
            replay_context.write_day(trade_date, policy, episodes[day_start:])
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
    notional = pnl = peaks = 0
    worst = None
    target = adverse = flat = ready = caution = 0
    states = {state: [0, 0, 0, 0, None] for state in ("ENTRY_READY", "ENTRY_CAUTION")}
    for row in episodes:
        price, net = row["entry_price"], row["net_return_pct"]
        notional += price
        profit = price * net / 100.0
        pnl += profit
        peaks += row["peak_return_pct"]
        worst = net if worst is None else min(worst, net)
        is_target = row["exit_reason"] == "target"
        target += is_target
        adverse += row["exit_reason"] in {
            "confirmed_support_break",
            "same_bar_conflict_adverse",
        }
        flat += row["exit_reason"] == "force_flat"
        ready += row["entry_state"] == "ENTRY_READY"
        caution += row["entry_state"] == "ENTRY_CAUTION"
        state = states.get(row["entry_state"])
        if state is not None:
            state[0] += 1
            state[1] += is_target
            state[2] += price
            state[3] += profit
            state[4] = net if state[4] is None else min(state[4], net)
    return dict(
        episode_count=len(episodes),
        target_count=target,
        adverse_exit_count=adverse,
        force_flat_count=flat,
        entry_ready_count=ready,
        entry_caution_count=caution,
        notional_weighted_ev_pct=round(pnl / notional * 100.0, 6) if notional else None,
        worst_episode_return_pct=worst,
        average_peak_return_pct=round(peaks / len(episodes), 6) if episodes else None,
        entry_state_breakdown={
            name: dict(
                episode_count=value[0],
                target_count=value[1],
                notional_weighted_ev_pct=round(value[3] / value[2] * 100.0, 6)
                if value[2]
                else None,
                worst_episode_return_pct=value[4],
            )
            for name, value in states.items()
        },
    )


def _entry_cap_comparison(
    episodes: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    comparison: dict[str, dict[str, Any]] = {}
    rows = [(int(row["daily_entry_ordinal"]), row) for row in episodes]
    cumulative_summary = None
    previous_cap = None
    for cap in ENTRY_CAP_VALUES:
        cumulative = [row for ordinal, row in rows if ordinal <= cap]
        incremental = [row for ordinal, row in rows if ordinal == cap]
        if cumulative_summary is None or incremental or cap != previous_cap + 1:
            cumulative_summary = _summarize_episodes(cumulative)
        incremental_summary = _summarize_episode_subset(incremental)
        incremental_ev = incremental_summary.get("notional_weighted_ev_pct")
        comparison[str(cap)] = {
            # No episode added at this adjacent cap: the native sum is exactly
            # unchanged. Keep independent dicts for later modeled annotations.
            "cumulative": deepcopy(cumulative_summary),
            "incremental": incremental_summary,
            "incremental_ev_positive": bool(
                incremental_summary["episode_count"] > 0
                and incremental_ev is not None
                and float(incremental_ev) > 0.0
            ),
        }
        previous_cap = cap
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
    bars: list[Bar],
    *,
    expected_dates: list[date],
    replay_context: ReplayContext | None = None,
) -> dict[str, Any]:
    grouped = _group_bars(bars)
    replay_context = replay_context or ReplayContext(grouped)
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
    calibration_ready_count = 0
    high_caps: dict[SignalPolicy, set[int]] = {}
    for policy_number, policy in enumerate(policy_grid(), 1):
        if replay_context.cache_dir is not None and policy_number % 128 == 0:
            print(
                json.dumps(
                    {
                        "stage": "grid_progress",
                        "symbol": replay_context.symbol,
                        "grid_policies": policy_number,
                        "calibration_dates": len(calibration_dates),
                        "day_cache_hits": replay_context.cache_hits,
                        "day_cache_misses": replay_context.cache_misses,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        full_evaluation = evaluate_policy(
            grouped,
            calibration_dates,
            policy,
            include_episodes=True,
            replay_context=replay_context,
        )
        first_evaluation = _subset_evaluation(full_evaluation, first_dates)
        second_evaluation = _subset_evaluation(full_evaluation, second_dates)
        full_comparison = full_evaluation["entry_cap_comparison"]
        first_comparison = first_evaluation["entry_cap_comparison"]
        second_comparison = second_evaluation["entry_cap_comparison"]
        for evaluation, dates in (
            (full_evaluation, calibration_dates),
            (first_evaluation, first_dates),
            (second_evaluation, second_dates),
        ):
            cap_summaries = modeled_cap_summaries(
                evaluation["episodes"], dates, ENTRY_CAP_VALUES
            )
            for cap in ENTRY_CAP_VALUES:
                evaluation["entry_cap_comparison"][str(cap)]["cumulative"].update(
                    cap_summaries[str(cap)]
                )
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
            if (
                first["modeled_net_pnl_per_qualified_day"] is None
                or second["modeled_net_pnl_per_qualified_day"] is None
            ):
                continue
            score = min(
                first["modeled_net_pnl_per_qualified_day"],
                second["modeled_net_pnl_per_qualified_day"],
            )
            if entry_cap >= HIGH_ENTRY_CAP_START:
                high_caps.setdefault(policy, set()).add(entry_cap)
            calibration_ready_count += 1
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
            # Stable rank preserves the earliest grid item on exact ties.
            for base in (True, False):
                group = [
                    item
                    for item in candidates
                    if (item[2] < HIGH_ENTRY_CAP_START) is base
                ]
                if len(group) > 1:
                    winner = max(
                        group, key=lambda item: (item[0], item[3]["episode_count"])
                    )
                    candidates = [
                        item
                        for item in candidates
                        if (item[2] < HIGH_ENTRY_CAP_START) is not base
                    ]
                    candidates.append(winner)
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
        if high_cap in high_caps.get(selected, set()):
            calibration_selected_cap = high_cap
    holdout_evaluation = evaluate_policy(
        grouped,
        holdout_dates,
        selected,
        include_episodes=True,
        replay_context=replay_context,
    )
    holdout_cap_comparison = holdout_evaluation["entry_cap_comparison"]
    for cap in ENTRY_CAP_VALUES:
        episodes = [
            row
            for row in holdout_evaluation["episodes"]
            if row["daily_entry_ordinal"] <= cap
        ]
        holdout_cap_comparison[str(cap)]["cumulative"].update(
            modeled_summary(episodes, holdout_dates)
        )
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
    full_window.update(
        modeled_summary(
            [
                row
                for row in [
                    *calibration_selected_evaluation["episodes"],
                    *holdout_evaluation["episodes"],
                ]
                if row["daily_entry_ordinal"] <= selected_entry_cap
            ],
            expected_dates,
        )
    )
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
        "selected_episodes": {
            "calibration": [
                row
                for row in calibration_selected_evaluation["episodes"]
                if row["daily_entry_ordinal"] <= selected_entry_cap
            ],
            "holdout": holdout["episodes"],
        },
        "entry_cap_comparison": {
            "calibration": calibration_cap_comparison,
            "calibration_first_half": first_cap_comparison,
            "calibration_second_half": second_cap_comparison,
            "holdout": holdout_cap_comparison,
            "full_window": full_window_cap_comparison,
        },
        "robust_calibration_score": round(score, 6),
        "grid_candidate_count": evaluated,
        "calibration_ready_candidate_count": calibration_ready_count,
        "calibration_gate_counts": gate_counts,
        "date_split": date_split,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _frozen_prospective_result(
    result,
    *,
    symbol,
    grouped,
    qualified_dates,
    end_date,
    replay_context,
    baseline,
    baseline_policy_id=None,
):
    """Keep the historical grid diagnostic; validate a prespecified future seed."""
    from src.engine.monitoring import research_closed_loop as loop

    parameters = result.get("selected_policy")
    frozen = loop.load_candidate(symbol)
    previous = frozen
    reason = None
    if frozen is not None:
        prefix = canonical_bar_hash(
            bar
            for day, rows in grouped.items()
            if str(day) <= frozen["frozen_source_date"]
            for bar in rows
        )
        if (
            prefix != frozen["frozen_source_sha256"]
            or comparison_cost_contract(
                date.fromisoformat(frozen["frozen_source_date"])
            )["contract_sha256"]
            != frozen["cost_sha256"]
        ):
            frozen, reason = None, "source_or_cost_correction"
        elif frozen.get("baseline_parameters") != baseline:
            frozen, reason = None, "incumbent_parent_changed"
    if frozen is None:
        if not isinstance(parameters, dict):
            return result
        frozen = loop.candidate_revision(
            symbol=symbol,
            parameters=parameters,
            source_date=end_date,
            source_sha256=canonical_bar_hash(
                bar for rows in grouped.values() for bar in rows
            ),
            cost_sha256=comparison_cost_contract(end_date)["contract_sha256"],
            baseline_parameters=baseline,
            baseline_policy_id=baseline_policy_id,
            supersedes_revision_sha256=previous["revision_sha256"] if reason else None,
            supersession_reason=reason,
        )
    loop.validate_revision(frozen, symbol=symbol, owner="widget")
    historical = result
    result = {
        **historical,
        "historical_proxy_diagnostic": {
            key: historical.get(key)
            for key in (
                "decision",
                "selected_policy",
                "date_split",
                "grid_candidate_count",
            )
        },
        "candidate_revision": frozen,
        "prospective_window": loop.prospective_window(
            frozen, source_date=end_date, qualified_dates=qualified_dates
        ),
        "selected_policy": frozen["parameters"],
    }
    if result["prospective_window"]["status"] != "ready":
        result["decision"] = (
            "pending_prospective_validation_no_widget_runtime_promotion"
        )
        return result
    dates = [
        date.fromisoformat(day)
        for day in frozen["calibration_dates"] + frozen["holdout_dates"]
    ]
    parameters = frozen["parameters"]
    policy = SignalPolicy(
        **{
            key: value
            for key, value in parameters.items()
            if key in SignalPolicy.__dataclass_fields__
        }
    )
    full = evaluate_policy(
        grouped, dates, policy, include_episodes=True, replay_context=replay_context
    )
    cal = dates[: len(frozen["calibration_dates"])]
    windows = dict(
        calibration=cal,
        calibration_first_half=cal[: len(cal) // 2],
        calibration_second_half=cal[len(cal) // 2 :],
        holdout=dates[len(cal) :],
    )
    cap = parameters["max_completed_entries_per_day"]
    result["selected_episodes"], result["entry_cap_comparison"] = {}, {}
    for name, window in windows.items():
        replay = _subset_evaluation(full, window)
        episodes = [
            row for row in replay["episodes"] if row["daily_entry_ordinal"] <= cap
        ]
        result[name] = {
            **_summarize_episodes(episodes),
            **modeled_summary(episodes, window),
            "episodes": episodes,
        }
        result["entry_cap_comparison"][name] = replay["entry_cap_comparison"]
        if name in ("calibration", "holdout"):
            result["selected_episodes"][name] = episodes
    ready = _calibration_ready(
        result["calibration"],
        result["calibration_first_half"],
        result["calibration_second_half"],
    )
    ready &= result["holdout"]["episode_count"] >= 4 and _positive_ev(result["holdout"])
    ready &= (
        _metric_float(result["holdout"], "worst_episode_return_pct", default=-999) > -3
    )
    ready &= all(
        _incremental_entry_cap_ready(result["entry_cap_comparison"][name], cap)
        for name in windows
    )
    # Component attribution remains an independent required contract for changes
    # to an incumbent. A frozen new-symbol experiment has no incumbent arm.
    result.pop("component_selection", None)
    result.pop("component_comparison", None)
    if baseline:
        arms = {}
        signal_keys = tuple(
            key
            for key in SignalPolicy.__dataclass_fields__
            if key not in {"target_bps", "force_flat_time"}
        )
        for name, arm_parameters in component_arms(
            baseline,
            parameters,
            signal_keys=signal_keys,
            exit_keys=("target_bps", "force_flat_time"),
        ).items():
            arm_policy = SignalPolicy(
                **{
                    key: value
                    for key, value in arm_parameters.items()
                    if key in SignalPolicy.__dataclass_fields__
                }
            )
            arm_replay = evaluate_policy(
                grouped,
                dates,
                arm_policy,
                include_episodes=True,
                replay_context=replay_context,
            )
            arm = {"parameters": arm_parameters}
            for window, window_dates in windows.items():
                subset = _subset_evaluation(arm_replay, window_dates)
                selected_rows = [
                    row
                    for row in subset["episodes"]
                    if row["daily_entry_ordinal"]
                    <= arm_parameters["max_completed_entries_per_day"]
                ]
                arm[window] = {
                    **_summarize_episodes(selected_rows),
                    **modeled_summary(selected_rows, window_dates),
                    "episodes": selected_rows,
                    "entry_cap_comparison": subset["entry_cap_comparison"],
                }
            arms[name] = arm
        result["component_comparison"] = objective_comparison(
            arms, baseline_policy_id=frozen["baseline_policy_id"]
        )
        selection = select_policy_component(result["component_comparison"])
        result["component_selection"] = selection
        chosen = arms.get(selection["selected_arm"])
        # No different holdout winner can replace the prespecified seed.
        expected = {
            key: value
            for key, value in (chosen or {}).get("parameters", {}).items()
            if key in SignalPolicy.__dataclass_fields__
            or key == "max_completed_entries_per_day"
        }
        ready &= expected == parameters
        if chosen and expected == parameters:
            for window in windows:
                result[window] = chosen[window]
    result["decision"] = (
        "holdout_pass_widget_signal_policy_candidate"
        if ready
        else "prospective_holdout_failed_no_widget_runtime_promotion"
    )
    result["date_split"] = dict(
        qualified_trading_date_count=len(dates),
        calibration_trading_date_count=len(cal),
        holdout_trading_date_count=len(dates) - len(cal),
        calibration_start=str(cal[0]),
        calibration_end=str(cal[-1]),
        holdout_start=str(dates[len(cal)]),
        holdout_end=str(dates[-1]),
    )
    return result


def build_report(
    *,
    sources: dict[str, tuple[list[Bar], dict[str, Any]]],
    end_date: date,
    applied_baselines: dict[str, dict] | None = None,
    symbol_universe: dict[str, str] | None = None,
    symbol_origins: dict[str, str] | None = None,
    replay_cache_dir: Path | None = None,
    market_census: dict[str, Any] | None = None,
    capital_limit_krw: float | None = None,
) -> dict[str, Any]:
    global _ACTIVE_REPLAY_CONTEXT
    universe = dict(symbol_universe or SYMBOLS)
    origins = dict(
        symbol_origins or {symbol: "established_widget_symbol" for symbol in universe}
    )
    if (
        set(sources) != set(universe)
        or set(origins) != set(universe)
        or any(
            len(symbol) != 6 or not symbol.isdigit() or not name
            for symbol, name in universe.items()
        )
        or any(
            origin
            not in {
                "established_widget_symbol",
                "operator_enrolled_research_watch",
                "completed_daily_recommendation_auto_discovery",
                "causal_scanner_research_admission",
            }
            for origin in origins.values()
        )
    ):
        raise ResearchError("widget_symbol_source_set_mismatch")
    expected_dates = _clean_trading_dates(end_date)
    if applied_baselines is None:
        from src.engine.monitoring.widget_symbol_runtime_policy import (
            WidgetSymbolRuntimePolicyLoader,
        )

        applied_baselines = WidgetSymbolRuntimePolicyLoader().resolve_all(
            observed_date=end_date
        )
    results: dict[str, Any] = {}
    source_meta: dict[str, Any] = {}
    for symbol, name in universe.items():
        bars, meta = sources[symbol]
        if meta.get("source_quality_status") != "PASS":
            raise ResearchError(f"{symbol}_source_quality_not_pass")
        symbol_expected_dates = expected_dates
        if meta.get("listing_history_accepted") is True and bars:
            first_date = min(bar.timestamp.date() for bar in bars)
            symbol_expected_dates = [
                trade_date for trade_date in expected_dates if trade_date >= first_date
            ]
        coverage = _daily_source_coverage(_group_bars(bars), symbol_expected_dates)
        if coverage["status"] == "FAIL":
            raise ResearchError(f"{symbol}_daily_source_coverage_fail")
        qualified_dates = [
            date.fromisoformat(item) for item in coverage["qualified_dates"]
        ]
        qualified_date_set = set(qualified_dates)
        qualified_bars = [
            bar for bar in bars if bar.timestamp.date() in qualified_date_set
        ]
        grouped_qualified = _group_bars(qualified_bars)
        replay_context = ReplayContext(
            grouped_qualified,
            replay_cache_dir / symbol if replay_cache_dir is not None else None,
        )
        replay_context.symbol = symbol
        _ACTIVE_REPLAY_CONTEXT = replay_context
        discovery_kwargs = {"replay_context": replay_context}
        result = discover_symbol_policy(
            qualified_bars, expected_dates=qualified_dates, **discovery_kwargs
        )
        baseline_receipt = applied_baselines.get(symbol) or {}
        baseline = baseline_receipt.get("signal_policy")
        if baseline:
            baseline = {
                **baseline,
                "max_completed_entries_per_day": baseline_receipt["execution_policy"][
                    "max_completed_entries_per_day"
                ],
            }
        selected_parameters = result.get("selected_policy") or {}
        comparisons = {}
        component_grouped = grouped_qualified
        component_context = replay_context
        if selected_parameters:
            signal_keys = tuple(
                key
                for key in SignalPolicy.__dataclass_fields__
                if key not in {"target_bps", "force_flat_time"}
            )
            for arm_name, parameters in component_arms(
                baseline,
                selected_parameters,
                signal_keys=signal_keys,
                exit_keys=("target_bps", "force_flat_time"),
            ).items():
                replay_policy = SignalPolicy(
                    **{
                        key: value
                        for key, value in parameters.items()
                        if key in SignalPolicy.__dataclass_fields__
                    }
                )
                comparisons[arm_name] = {"parameters": parameters}
                component_full = evaluate_policy(
                    component_grouped,
                    qualified_dates,
                    replay_policy,
                    include_episodes=True,
                    replay_context=component_context,
                )
                for window, dates in (
                    ("calibration", qualified_dates[:-HOLDOUT_DAYS]),
                    (
                        "calibration_first_half",
                        qualified_dates[:-HOLDOUT_DAYS][
                            : max(1, (len(qualified_dates) - HOLDOUT_DAYS) // 2)
                        ],
                    ),
                    (
                        "calibration_second_half",
                        qualified_dates[:-HOLDOUT_DAYS][
                            max(1, (len(qualified_dates) - HOLDOUT_DAYS) // 2) :
                        ],
                    ),
                    ("holdout", qualified_dates[-HOLDOUT_DAYS:]),
                ):
                    replay = _subset_evaluation(component_full, dates)
                    episodes = [
                        row
                        for row in replay["episodes"]
                        if row["daily_entry_ordinal"]
                        <= parameters["max_completed_entries_per_day"]
                    ]
                    summary = _summarize_episodes(episodes)
                    summary["entry_cap_comparison"] = replay["entry_cap_comparison"]
                    summary["episodes"] = episodes
                    summary["modeled_net_pnl_per_qualified_day"] = (
                        sum(
                            row["entry_price"] * row["net_return_pct"] / 100 * 10
                            for row in episodes
                        )
                        / len(dates)
                        if dates
                        else None
                    )
                    summary["completed_episodes_per_qualified_day"] = (
                        len(episodes) / len(dates) if dates else None
                    )
                    durations = [
                        (
                            datetime.fromisoformat(row["exit_at"])
                            - datetime.fromisoformat(row["entry_at"])
                        ).total_seconds()
                        for row in episodes
                    ]
                    summary["observed_occupancy_seconds_sum"] = (
                        sum(durations) if durations else None
                    )
                    summary["small_profit_completed_within_180s_count"] = sum(
                        duration <= 180 and 0 < row["net_return_pct"] <= 0.5
                        for row, duration in zip(episodes, durations)
                    )
                    summary["profitable_completed_within_180s_count"] = sum(
                        0 <= duration <= 180 and row["net_return_pct"] > 0
                        for row, duration in zip(episodes, durations)
                    )
                    comparisons[arm_name][window] = summary
        result["component_comparison"] = objective_comparison(
            comparisons, baseline_policy_id=baseline_receipt.get("policy_id")
        )
        if baseline and selected_parameters and end_date >= date(2026, 9, 9):
            selection = select_policy_component(result["component_comparison"])
            result["component_selection"] = selection
            result["joint_grid_diagnostic"] = {
                "selected_policy": selected_parameters,
                "decision": result.get("decision"),
            }
            chosen = comparisons.get(selection["selected_arm"])
            if chosen:
                result["selected_policy"] = {
                    key: value
                    for key, value in chosen["parameters"].items()
                    if key in SignalPolicy.__dataclass_fields__
                    or key == "max_completed_entries_per_day"
                }
                for window in (
                    "calibration",
                    "calibration_first_half",
                    "calibration_second_half",
                    "holdout",
                ):
                    result[window] = chosen[window]
                result["entry_cap_comparison"] = {
                    window: chosen[window]["entry_cap_comparison"]
                    for window in (
                        "calibration",
                        "calibration_first_half",
                        "calibration_second_half",
                        "holdout",
                    )
                }
                full_window_episodes = [
                    *chosen["calibration"]["episodes"],
                    *chosen["holdout"]["episodes"],
                ]
                result["full_window"] = _summarize_episodes(full_window_episodes)
                result["entry_cap_comparison"]["full_window"] = _entry_cap_comparison(
                    full_window_episodes
                )
                minimum_half_count = min(
                    chosen[window]["episode_count"]
                    for window in ("calibration_first_half", "calibration_second_half")
                )
                result["robust_calibration_score"] = round(
                    min(
                        chosen[window]["notional_weighted_ev_pct"]
                        for window in (
                            "calibration_first_half",
                            "calibration_second_half",
                        )
                    )
                    * minimum_half_count
                    / (minimum_half_count + 6),
                    6,
                )
                result["decision"] = "holdout_pass_widget_signal_policy_candidate"
            else:
                result["decision"] = "component_economics_or_holdout_not_ready"
        selected_parameters = result.get("selected_policy") or {}
        unchanged = baseline is not None and all(
            selected_parameters.get(key) == baseline.get(key)
            for key in selected_parameters
        )
        if end_date >= date(2026, 9, 17) and not unchanged:
            frozen_baseline = {
                key: value
                for key, value in (baseline or {}).items()
                if key in SignalPolicy.__dataclass_fields__
                or key == "max_completed_entries_per_day"
            } or None
            result = _frozen_prospective_result(
                result,
                symbol=symbol,
                grouped=grouped_qualified,
                qualified_dates=qualified_dates,
                end_date=end_date,
                replay_context=replay_context,
                baseline=frozen_baseline,
                baseline_policy_id=baseline_receipt.get("policy_id"),
            )
        replay_context.flush()
        _ACTIVE_REPLAY_CONTEXT = None
        results[symbol] = {"symbol": symbol, "name": name, **result}
        source_meta[symbol] = {**meta, "daily_source_coverage": coverage}
    pass_symbols = [
        symbol
        for symbol, result in results.items()
        if result["decision"] == "holdout_pass_widget_signal_policy_candidate"
    ]
    report = {
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
        "symbol_universe": universe,
        "symbol_origins": origins,
        "passed_symbols": pass_symbols,
        "source_meta": source_meta,
        "execution_quality_by_symbol": {
            symbol: load_execution_incidents(
                symbol, target_date=end_date, session="KRX_REGULAR"
            )
            for symbol in universe
        },
        "metric_contract": METRIC_CONTRACT,
        "owner_contract": OWNER_CONTRACT,
        "official_reference": OFFICIAL_REFERENCE,
        "comparison_cost_contract": comparison_cost_contract(end_date),
        "source_input_fingerprint": research_input_fingerprint(
            sources=sources,
            end_date=end_date,
            applied_baselines=applied_baselines,
            symbol_universe=universe,
            symbol_origins=origins,
        ),
        "execution_mode": "full_recompute",
        "selection_metric_contract": {
            "metric_role": "modeled_net_profit_objective_under_existing_primary_ev_guards",
            "decision_authority": AUTHORITY,
            "window_policy": "qualified_calendar_days_including_valid_zero_signal",
            "sample_floor": METRIC_CONTRACT["sample_floor"],
            "primary_decision_metric": "notional_weighted_ev_pct",
            "candidate_rank_metric": "minimum_half_modeled_net_pnl_per_qualified_day",
            "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
            "forbidden_uses": [
                "broker_profit",
                "quantity_or_cap_change",
                "missing_outcome_as_zero",
            ],
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "collector_created": False,
        "service_started": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if end_date >= date(2026, 9, 17):
        from src.engine.monitoring.widget_symbol_runtime_policy import (
            _normalized_selected_parameters,
        )
        from src.engine.monitoring.widget_symbol_runtime_contract import (
            DEFAULT_OBSERVATION_DIR,
        )
        from src.engine.monitoring.policy_research_economics import (
            signal_execution_feasibility,
        )

        for symbol, result in results.items():
            if result.get("decision") != "holdout_pass_widget_signal_policy_candidate":
                continue
            selected = _normalized_selected_parameters(result.get("selected_policy"))
            incumbent = applied_baselines.get(symbol) or {}
            carry = selected is not None and all(
                incumbent.get(key) == selected.get(key)
                for key in ("signal_policy", "execution_policy")
            )
            if carry:
                result["execution_feasibility"] = {
                    "status": "carry_verified_unchanged_incumbent",
                    "runtime_effect": False,
                }
            elif selected is not None:
                proof = signal_execution_feasibility(
                    result,
                    symbol=symbol,
                    source_date=end_date,
                    signal_policy=selected["signal_policy"],
                    observation_dir=DEFAULT_OBSERVATION_DIR,
                )
                result["execution_feasibility"] = proof
                if proof["status"] != "pass":
                    result["proxy_research_decision"] = result["decision"]
                    result["decision"] = (
                        "execution_feasibility_missing_no_widget_runtime_promotion"
                    )
    return attach_recommendation_contract(
        _attach_population_evidence(
            report, market_census=market_census, capital_limit_krw=capital_limit_krw
        )
    )


def _attach_population_evidence(report, *, market_census=None, capital_limit_krw=None):
    """Reconcile both single-symbol checkpoints and the combined universe."""
    end_date = date.fromisoformat(report["end_date"])
    results, universe = report["symbols"], report["symbol_universe"]
    if market_census is None:
        census_path = (
            DATA_DIR
            / "report"
            / "market_opportunity_census"
            / f"market_opportunity_census_{end_date.isoformat()}.json"
        )
        market_census = load_research_census(census_path)
    report["passed_symbols"] = [
        symbol
        for symbol, result in results.items()
        if result.get("decision") == "holdout_pass_widget_signal_policy_candidate"
    ]
    report["decision"] = (
        "widget_signal_policy_candidates_ready"
        if report["passed_symbols"]
        else "no_widget_signal_policy_candidate"
    )
    report["research_universe_handoff"] = research_universe_handoff(
        market_census, source_date=end_date, universe=universe, results=results
    )
    report["joint_capital_demand"] = joint_capital_demand(
        {
            symbol: [
                row
                for window in ("calibration", "holdout")
                for row in (result.get(window) or {}).get(
                    "episodes", (result.get("selected_episodes") or {}).get(window, [])
                )
            ]
            for symbol, result in results.items()
        },
        capital_limit_krw=capital_limit_krw,
    )
    if end_date >= date(2026, 9, 17):
        from src.engine.monitoring.research_closed_loop import SCHEMA, report_joint_gate

        report["closed_loop_contract"] = SCHEMA
        from src.engine.monitoring.research_version_outcomes import outcome_feedback

        report["policy_version_feedback"] = outcome_feedback(end_date)
        report["joint_allocation_gate"] = report_joint_gate(
            report, source_date=end_date
        )
    return report


class VerifiedBars(tuple):
    def __new__(cls, bars: Iterable[Bar]):
        value = super().__new__(cls, sorted(bars, key=lambda bar: bar.timestamp))
        value.source_content_sha256 = canonical_bar_hash(value)
        return value


def canonical_bar_hash(bars: Iterable[Bar]) -> str:
    digest = hashlib.sha256()
    for bar in sorted(bars, key=lambda item: item.timestamp):
        digest.update(
            json.dumps(
                (
                    bar.timestamp.isoformat(),
                    bar.open_price,
                    bar.high_price,
                    bar.low_price,
                    bar.close_price,
                    bar.volume,
                ),
                separators=(",", ":"),
            ).encode("ascii")
            + b"\n"
        )
    return digest.hexdigest()


def research_contract_hash() -> str:
    # Bind replay, tick/price, calendar and component/cost dependencies together.
    from src.trading.order import tick_utils
    from src.utils import market_day
    from src.engine.monitoring import (
        widget_signal_quality,
        widget_comparison_cost,
        policy_research_economics,
        research_closed_loop,
        research_source_facts,
    )

    digest = hashlib.sha256()
    for module in (
        tick_utils,
        market_day,
        widget_signal_quality,
        widget_comparison_cost,
        policy_research_economics,
        research_closed_loop,
        research_source_facts,
    ):
        digest.update(Path(module.__file__).read_bytes())
    digest.update(Path(__file__).read_bytes())
    return digest.hexdigest()


def _external_evidence_generation(end_date, symbols):
    from src.engine.monitoring.widget_symbol_runtime_contract import (
        DEFAULT_OBSERVATION_DIR,
    )

    census = (
        DATA_DIR
        / "report"
        / "market_opportunity_census"
        / f"market_opportunity_census_{end_date.isoformat()}.json"
    )
    from src.engine.monitoring.research_closed_loop import DIRECTORY

    paths = [
        census,
        DIRECTORY / f"allocator_{end_date.isoformat()}.json",
        DIRECTORY / f"joint_inputs_episode_{end_date.isoformat()}.json",
    ]
    paths.extend(DIRECTORY.glob("widget_outcomes_*.json"))
    for symbol in sorted(symbols):
        paths.extend(
            sorted((DIRECTORY / "facts").glob(f"prospective_facts_{symbol}_*.jsonl*"))
        )
        paths.extend((DIRECTORY / "facts").glob(f"source_gap_{symbol}_*.json"))
    if end_date >= date(2026, 9, 17):
        for symbol in sorted(symbols):
            paths.extend(
                sorted(
                    Path(DEFAULT_OBSERVATION_DIR).glob(
                        f"widget_symbol_advisory_{symbol}_*.jsonl"
                    )
                )
            )
    generations = {}
    for path in paths:
        try:
            stat = path.lstat()
            generations[str(path)] = [
                stat.st_dev,
                stat.st_ino,
                stat.st_size,
                stat.st_mtime_ns,
                stat.st_ctime_ns,
                path.is_symlink(),
            ]
        except OSError:
            generations[str(path)] = None
    return generations


def research_input_fingerprint(
    *,
    sources: dict[str, tuple[list[Bar], dict[str, Any]]],
    end_date: date,
    applied_baselines: dict[str, dict] | None,
    symbol_universe: Collection[str],
    symbol_origins: dict[str, str],
) -> str:
    from src.engine.monitoring.research_closed_loop import load_candidate

    payload = {
        "schema": "widget_symbol_signal_policy_research_input_v3",
        "external_evidence_generation": _external_evidence_generation(
            end_date, symbol_universe
        ),
        "producer_sha256": research_contract_hash(),
        "end_date": end_date.isoformat(),
        "cost_contract": comparison_cost_contract(end_date),
        "frozen_candidates": {
            symbol: load_candidate(symbol) for symbol in sorted(symbol_universe)
        },
        "applied_baselines": applied_baselines or {},
        "symbol_universe": sorted(symbol_universe),
        "symbol_origins": {
            symbol: symbol_origins.get(symbol) for symbol in sorted(symbol_universe)
        },
        "sources": {
            symbol: {
                "source_content_sha256": (
                    bars.source_content_sha256
                    if isinstance(bars, VerifiedBars)
                    else canonical_bar_hash(bars)
                ),
                "source_quality_status": meta.get("source_quality_status"),
                "excluded_dates": meta.get("excluded_dates") or [],
                "listing_history_accepted": meta.get("listing_history_accepted", False),
            }
            for symbol, (bars, meta) in sorted(sources.items())
        },
    }
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def reusable_report(path: Path, *, end_date: date, fingerprint: str) -> dict | None:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if (
        not isinstance(report, dict)
        or report.get("schema") != REPORT_SCHEMA
        or report.get("status") != "complete"
        or report.get("end_date") != end_date.isoformat()
        or report.get("source_input_fingerprint") != fingerprint
        or report.get("runtime_effect") is not False
        or report.get("allowed_runtime_apply") is not False
    ):
        return None
    checksum = report.get("checkpoint_sha256")
    if path.parent.name == "checkpoints" and checksum is None:
        return None
    if checksum is not None:
        material = {
            key: value for key, value in report.items() if key != "checkpoint_sha256"
        }
        if (
            checksum
            != hashlib.sha256(
                json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
        ):
            return None
    return report


def attach_recommendation_contract(report: dict[str, Any]) -> dict[str, Any]:
    for symbol, row in report["symbols"].items():
        bind_recommendation(
            row,
            producer="widget_symbol_signal_policy_research",
            scope=f"{symbol}/KRX_REGULAR",
            axis="symbol_signal_policy",
            proposal=row.get("selected_policy") or {},
            consumer="widget_symbol_runtime_policy",
            acceptance="Existing holdout, source and policy guards must pass; exact next-session policy and loader receipt own application.",
        )
    return report


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
    from src.engine.monitoring.research_closed_loop import freeze_candidate

    for result in report["symbols"].values():
        revision = result.get("candidate_revision")
        if revision is not None and freeze_candidate(revision) != revision:
            raise ValueError("research_concurrent_frozen_candidate_conflict")
    from src.engine.monitoring.research_closed_loop import write_joint_inputs

    write_joint_inputs(report, family="widget")
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


_ACTIVE_REPLAY_CONTEXT: ReplayContext | None = None


def _handle_research_termination(signum: int, _frame: Any) -> None:
    context = _ACTIVE_REPLAY_CONTEXT
    if context is not None:
        context.flush()
        print(
            json.dumps(
                {
                    "stage": "research_terminated",
                    "symbol": context.symbol,
                    "partial_replay_checkpoint": True,
                    "complete": False,
                    "signal": signum,
                }
            ),
            flush=True,
        )
    raise SystemExit(128 + signum)


SNAPSHOT_SCHEMA = "widget_krx_completed_source_v1"
DEFAULT_SNAPSHOT_DIR = DATA_DIR / "cache" / "widget_signal_research_sources"


def _freeze_receipt(end_date: date) -> dict[str, Any] | None:
    path = (
        DATA_DIR
        / "runtime"
        / "update_kospi_status"
        / f"update_kospi_{end_date.isoformat()}.json"
    )
    try:
        receipt_bytes = path.read_bytes()
        receipt = json.loads(receipt_bytes)
        db = receipt.get("db_state") or {}
        if (
            receipt.get("status") not in {"completed", "completed_with_warnings"}
            or receipt.get("target_date") != end_date.isoformat()
            or db.get("latest_quote_date") != end_date.isoformat()
            or int(db.get("rows_on_latest_date") or 0) <= 0
            or end_date > resolve_completed_research_end_date()
        ):
            return None
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    return {
        "target_date": end_date.isoformat(),
        "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
    }


def _snapshot_freeze_valid(freeze: object, day: date) -> bool:
    try:
        target = date.fromisoformat(freeze["target_date"])
        expected = _freeze_receipt(target)
        return (
            target >= day
            and expected is not None
            and freeze.get("sha256") == expected["sha256"]
        )
    except (TypeError, ValueError, KeyError, AttributeError):
        return False


@lru_cache(maxsize=16)
def _source_parser_digest(functions: tuple[Callable[..., Any], ...]) -> str:
    # Dependencies are immutable within a pinned research process.
    from src.utils import market_day

    digest = hashlib.sha256()
    for function in functions:
        digest.update(inspect.getsource(function).encode())
    digest.update(Path(market_day.__file__).read_bytes())
    digest.update(json.dumps(OFFICIAL_REFERENCE, sort_keys=True).encode())
    digest.update(SNAPSHOT_SCHEMA.encode())
    return digest.hexdigest()


def source_parser_contract_hash() -> str:
    # Source acquisition must survive unrelated cost/seed/replay changes.
    return _source_parser_digest(
        (
            fetch_krx_history,
            _parse_response,
            _positive_int,
            canonical_bar_hash,
            _daily_source_coverage,
            _read_snapshot,
            _snapshot_freeze_valid,
            _freeze_receipt,
        )
    )


def _snapshot_key(symbol: str, day: date) -> dict[str, Any]:
    return {
        "schema": SNAPSHOT_SCHEMA,
        "symbol": symbol,
        "date": day.isoformat(),
        "route": symbol,
        "session": "KRX_REGULAR",
        "adjustment": "1",
        "parser_contract": source_parser_contract_hash(),
    }


def _receipt_checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {key: value for key, value in payload.items() if key != "receipt_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _read_snapshot(
    path: Path, symbol: str, day: date
) -> tuple[list[Bar], dict[str, Any]] | None:
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            return None
        payload = json.loads(path.read_text())
        if (
            payload.get("receipt_sha256") != _receipt_checksum(payload)
            or payload.get("key") != _snapshot_key(symbol, day)
            or payload.get("complete") is not True
            or not _snapshot_freeze_valid(payload.get("freeze_receipt"), day)
            or payload.get("source_quality_status") != "PASS"
            or not payload.get("retrieved_at_kst")
        ):
            return None
        retrieved = datetime.fromisoformat(payload["retrieved_at_kst"])
        if (
            retrieved.tzinfo is None
            or retrieved.utcoffset() != timedelta(hours=9)
            or retrieved > datetime.now(KST)
        ):
            return None
        bars = [
            Bar(datetime.fromisoformat(row[0]), *row[1:]) for row in payload["bars"]
        ]
        if (
            not bars
            or retrieved < max(bar.timestamp for bar in bars) + timedelta(minutes=1)
            or canonical_bar_hash(bars) != payload.get("sha256")
            or any(
                bar.timestamp.tzinfo is None
                or bar.timestamp.utcoffset() != timedelta(hours=9)
                or any(
                    isinstance(value, bool) or not isinstance(value, int)
                    for value in (
                        bar.open_price,
                        bar.high_price,
                        bar.low_price,
                        bar.close_price,
                        bar.volume,
                    )
                )
                or bar.timestamp.date() != day
                or not time(9) <= bar.timestamp.time() < time(15, 30)
                or min(bar.open_price, bar.high_price, bar.low_price, bar.close_price)
                <= 0
                or bar.high_price < max(bar.open_price, bar.close_price, bar.low_price)
                or bar.low_price > min(bar.open_price, bar.close_price, bar.high_price)
                or bar.volume < 0
                for bar in bars
            )
            or len({bar.timestamp for bar in bars}) != len(bars)
        ):
            return None
        if _daily_source_coverage(_group_bars(bars), [day])["status"] != "PASS":
            return None
        return bars, payload
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
        return None


def load_completed_symbol_source(
    *,
    symbol: str,
    end_date: date,
    universe: dict[str, str],
    origin: str,
    token_provider: Callable[[], str | None],
    snapshot_dir: Path,
    max_pages: int,
    page_delay_sec: float,
) -> tuple[list[Bar], dict[str, Any]]:
    """Validate dated immutable snapshots before any remote read; serialize publication."""
    if end_date > resolve_completed_research_end_date():
        raise ResearchError("research_target_date_not_completed")
    dates = _clean_trading_dates(end_date)
    root = snapshot_dir / symbol
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".publish.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        records = {
            day: _read_snapshot(root / f"{day.isoformat()}.json", symbol, day)
            for day in dates
        }
        manifest_path = root / "listing.json"
        try:
            manifest = json.loads(manifest_path.read_text())
            listing_start = date.fromisoformat(manifest["first_date"])
            if (
                manifest.get("receipt_sha256") != _receipt_checksum(manifest)
                or not CLEAN_BASELINE_DATE <= listing_start <= end_date
                or manifest.get("contract") != source_parser_contract_hash()
                or manifest.get("complete") is not True
                or manifest.get("symbol") != symbol
                or manifest.get("route") != symbol
                or not _snapshot_freeze_valid(
                    manifest.get("freeze_receipt"), listing_start
                )
                or origin == "established_widget_symbol"
            ):
                listing_start = CLEAN_BASELINE_DATE
        except (OSError, ValueError, KeyError, TypeError):
            listing_start = CLEAN_BASELINE_DATE
        required = [day for day in dates if day >= listing_start]
        missing = [day for day in required if records[day] is None]
        remote_count = 0
        updated_dates: set[date] = set()
        revised_dates: list[str] = []
        meta: dict[str, Any] = {}
        if missing:
            token = token_provider()
            if not token:
                raise ResearchError("cached_token_missing_no_issue_or_refresh_allowed")
            # A cold import keeps the original whole-period validation. Incremental
            # reads bracket only missing dates and still validate every bar/date.
            cold = not any(records.values())
            start = CLEAN_BASELINE_DATE if cold else min(missing)
            finish = end_date if cold else max(missing)
            expected = [day for day in dates if start <= day <= finish]
            fetched, meta = fetch_krx_history(
                symbol=symbol,
                token=token,
                start_date=start,
                end_date=finish,
                expected_trading_day_count=len(expected),
                max_pages=max_pages,
                page_delay_sec=page_delay_sec,
                allowed_symbols=universe,
                allow_short_listing_history=origin != "established_widget_symbol",
                incremental_source=not cold,
            )
            remote_count = int(meta.get("request_count") or 0)
            freeze = _freeze_receipt(end_date)
            grouped = _group_bars(fetched)
            for day, rows in grouped.items():
                old = records.get(day)
                same_source = old and canonical_bar_hash(old[0]) == canonical_bar_hash(
                    rows
                )
                if same_source:
                    continue  # Keep original receipt and retrieval time on overlap.
                if old:
                    revised_dates.append(day.isoformat())
                updated_dates.add(day)
                payload = {
                    "key": _snapshot_key(symbol, day),
                    "complete": True,
                    "freeze_receipt": freeze,
                    "retrieved_at_kst": meta["retrieved_at_kst"],
                    "source_quality_status": "PASS",
                    "sha256": canonical_bar_hash(rows),
                    "bars": [
                        (
                            bar.timestamp.isoformat(),
                            bar.open_price,
                            bar.high_price,
                            bar.low_price,
                            bar.close_price,
                            bar.volume,
                        )
                        for bar in rows
                    ],
                }
                payload["receipt_sha256"] = _receipt_checksum(payload)
                records[day] = (list(rows), payload)
                if (
                    freeze
                    and _daily_source_coverage({day: rows}, [day])["status"] == "PASS"
                ):
                    _atomic_write(
                        root / f"{day.isoformat()}.json",
                        json.dumps(payload, sort_keys=True),
                    )
                elif old:
                    # Preserve original bars/provenance but revoke the optional
                    # cache's completion when a remote revision is incomplete.
                    invalidated = {
                        **old[1],
                        "complete": False,
                        "invalidated_by_source_sha256": payload["sha256"],
                        "previous_receipt_sha256": old[1]["receipt_sha256"],
                    }
                    invalidated["receipt_sha256"] = _receipt_checksum(invalidated)
                    _atomic_write(
                        root / f"{day.isoformat()}.json",
                        json.dumps(invalidated, sort_keys=True),
                    )
            if cold and meta.get("listing_history_accepted"):
                listing_start = min(grouped)
                required = [day for day in dates if day >= listing_start]
                if freeze:
                    manifest = {
                        "symbol": symbol,
                        "route": symbol,
                        "first_date": listing_start.isoformat(),
                        "complete": True,
                        "contract": source_parser_contract_hash(),
                        "freeze_receipt": freeze,
                    }
                    manifest["receipt_sha256"] = _receipt_checksum(manifest)
                    _atomic_write(manifest_path, json.dumps(manifest))
        if any(records[day] is None for day in required):
            raise ResearchError(f"{symbol}_snapshot_coverage_incomplete")
        bars = VerifiedBars(bar for day in required for bar in records[day][0])
        retrieval_times = {
            day.isoformat(): records[day][1]["retrieved_at_kst"] for day in required
        }
        return bars, {
            **meta,
            "symbol": symbol,
            "request_code": symbol,
            "api_id": "ka10080",
            "market": "KRX_regular",
            "source_quality_status": "PASS",
            "source_content_sha256": bars.source_content_sha256,
            "bar_count": len(bars),
            "trading_date_count": len(required),
            "expected_trading_date_count": len(dates),
            "listing_history_accepted": listing_start > CLEAN_BASELINE_DATE,
            "oldest_source_date": required[0].isoformat(),
            "latest_source_date": end_date.isoformat(),
            "retrieved_at_by_date": retrieval_times,
            "snapshot_hit_dates": sum(day not in updated_dates for day in required),
            "source_revision_dates": revised_dates,
            "snapshot_miss_dates": len(missing),
            "request_count": remote_count,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end-date")
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--page-delay-sec", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    signal.signal(signal.SIGTERM, _handle_research_termination)
    end_date = (
        date.fromisoformat(args.end_date)
        if args.end_date
        else resolve_completed_research_end_date()
    )
    symbol_universe, symbol_origins = load_symbol_universe(observed_date=end_date)
    from src.engine.monitoring.widget_symbol_runtime_policy import (
        WidgetSymbolRuntimePolicyLoader,
    )

    applied_baselines = WidgetSymbolRuntimePolicyLoader().resolve_all(
        observed_date=end_date
    )
    # Checkpoint each symbol against source, code, cost and applied incumbent.
    # Raw history is released before acquiring the next symbol.
    reports = []
    symbol_fingerprints = {}
    for index, (symbol, name) in enumerate(symbol_universe.items(), 1):
        started = time_module.monotonic()
        print(
            json.dumps(
                {
                    "stage": "symbol_start",
                    "target_date": end_date.isoformat(),
                    "symbol": symbol,
                    "progress": f"{index}/{len(symbol_universe)}",
                },
                sort_keys=True,
            ),
            flush=True,
        )
        bars, meta = load_completed_symbol_source(
            symbol=symbol,
            end_date=end_date,
            universe=symbol_universe,
            origin=symbol_origins[symbol],
            token_provider=kiwoom_utils.get_cached_kiwoom_token,
            snapshot_dir=args.snapshot_dir,
            max_pages=args.max_pages,
            page_delay_sec=args.page_delay_sec,
        )
        kwargs = dict(
            sources={symbol: (bars, meta)},
            end_date=end_date,
            applied_baselines=(
                {symbol: applied_baselines[symbol]}
                if symbol in applied_baselines
                else {}
            ),
            symbol_universe={symbol: name},
            symbol_origins={symbol: symbol_origins[symbol]},
        )
        fingerprint = research_input_fingerprint(**kwargs)
        checkpoint = (
            args.output_dir / "checkpoints" / f"{end_date.isoformat()}_{symbol}.json"
        )
        reusable = reusable_report(
            checkpoint, end_date=end_date, fingerprint=fingerprint
        )
        if reusable is None:
            report = build_report(
                **kwargs,
                replay_cache_dir=(
                    __import__(
                        "src.engine.monitoring.research_closed_loop",
                        fromlist=["DIRECTORY"],
                    ).DIRECTORY
                    / "cache"
                    / "replay"
                    if end_date >= date(2026, 9, 17)
                    else args.snapshot_dir / "replay"
                ),
                # Population evidence belongs to the final combined report,
                # not N copies of the census in per-symbol checkpoints.
                market_census={},
            )
            if args.write:
                checkpoint_payload = {
                    **report,
                    "checkpoint_sha256": hashlib.sha256(
                        json.dumps(report, ensure_ascii=False, sort_keys=True).encode()
                    ).hexdigest(),
                }
                _atomic_write(
                    checkpoint,
                    json.dumps(checkpoint_payload, ensure_ascii=False, sort_keys=True),
                )
        else:
            report = {
                key: value
                for key, value in reusable.items()
                if key != "checkpoint_sha256"
            }
            report["execution_mode"] = "exact_symbol_checkpoint_reuse"
            # Original retrieval times remain in dated snapshots; refresh only
            # incident evidence, whose closure may change independently of OHLCV.
            report["execution_quality_by_symbol"][symbol] = load_execution_incidents(
                symbol, target_date=end_date, session="KRX_REGULAR"
            )
        symbol_fingerprints[symbol] = fingerprint
        reports.append(report)
        print(
            json.dumps(
                {
                    "stage": "symbol_complete",
                    "target_date": end_date.isoformat(),
                    "symbol": symbol,
                    "progress": f"{index}/{len(symbol_universe)}",
                    "remote_requests": meta["request_count"],
                    "cache_mode": report["execution_mode"],
                    "wall_seconds": round(time_module.monotonic() - started, 3),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        del bars, kwargs
    report = dict(reports[0])
    for key in ("symbols", "source_meta", "execution_quality_by_symbol"):
        report[key] = {
            symbol: value for part in reports for symbol, value in part[key].items()
        }
    report["symbol_universe"] = symbol_universe
    report["symbol_origins"] = symbol_origins
    report["passed_symbols"] = [
        symbol for part in reports for symbol in part["passed_symbols"]
    ]
    report["decision"] = (
        "widget_signal_policy_candidates_ready"
        if report["passed_symbols"]
        else "no_widget_signal_policy_candidate"
    )
    report["source_input_fingerprint"] = hashlib.sha256(
        json.dumps(symbol_fingerprints, sort_keys=True).encode()
    ).hexdigest()
    report["execution_mode"] = "sequential_symbol_checkpoints"
    report["generated_at_kst"] = datetime.now(KST).isoformat(timespec="seconds")
    report = attach_recommendation_contract(_attach_population_evidence(report))
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
