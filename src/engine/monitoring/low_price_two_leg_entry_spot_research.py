"""Profile-specific entry-spot research for lower-price two-leg machines.

The module uses only completed Kiwoom ``ka10080`` SOR one-minute bars and an
already-valid shared token.  It cannot issue or refresh tokens, access accounts,
submit orders, or mutate runtime policy. Candidate selection uses every supplied
clean-baseline calibration day; the final 16 days remain untouched holdout data.
"""

from __future__ import annotations

import argparse
from array import array
from bisect import bisect_left, bisect_right
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from heapq import heappush, heapreplace
from itertools import islice
import json
import math
import os
import tempfile
import time as time_module
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Iterator

import requests

from src.trading.low_price_two_leg.profiles import PROFILES, MachineProfile
from src.trading.low_price_two_leg.economics import ROUND_TRIP_COST_PCT
from src.trading.order.regular_two_leg_machine import KST
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

REPORT_SCHEMA = "low_price_two_leg_entry_spot_research_v3"
ECONOMIC_REPLAY_CONTRACT = "low_price_two_leg_continuous_custody_economics_v1"
ECONOMIC_METRIC_CONTRACT = {
    "metric_role": "existing_axis_paired_economic_research",
    "decision_authority": "source_only_no_runtime_or_order_authority",
    "window_policy": "same_clean_prefix_custody_same_observation_dates",
    "sample_floor": "calibration_6_episodes_8_legs_holdout_3_episodes_4_legs",
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": "validated_completed_sor_bars_no_invented_custody_resolution",
    "forbidden_uses": [
        "real_fill_evidence",
        "standalone_live_promotion",
        "held_as_realized_pnl",
    ],
}
OUTPUT_DIR = DATA_DIR / "report" / "low_price_two_leg_entry_spot_research"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
DEFAULT_END_DATE = date(2026, 8, 10)
CALIBRATION_DAYS = 30
HOLDOUT_DAYS = 16
COST_PCT = ROUND_TRIP_COST_PCT
LOOKBACK_GRID = (15, 20, 30, 45, 60)
DRAWDOWN_GRID = (0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00)
NEAR_LOW_GRID = (0.05, 0.10, 0.20, 0.35, 0.50, 0.75)
EXECUTION_PLAN_GRID = (
    ((0, -1), 5, 2),
    ((0, -1), 5, 4),
    ((0, -1), 3, 4),
    ((-1, -2), 5, 4),
)
_DAY_REPLAY = ContextVar("low_price_two_leg_day_replay", default=None)


@contextmanager
def day_replay_scope(transition):
    """Bind optional research-only day transitions to one profile invocation."""
    token = _DAY_REPLAY.set(transition)
    try:
        yield
    finally:
        try:
            transition.flush()
        finally:
            _DAY_REPLAY.reset(token)


PROFILE_EXECUTION_PLAN_EXTENSIONS = {
    "kakao_morning": (((0, -1), 5, 3),),
}
MAX_MANAGEABLE_HELD_LEG_RATE = 0.25
MAX_MANAGEABLE_HELD_MARK_TO_MARKET_LOSS_PCT = 3.0
OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "953e5dbff123f437ab4d11a78a95191a685eb51f",
    "retrieved_at_kst": "2026-09-16T14:22:43+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core/errors.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contract": "POST /api/dostk/chart; api-id=ka10080",
}
METRIC_CONTRACT = {
    "metric_role": "profile_specific_entry_spot_offline_research",
    "decision_authority": "source_only_no_runtime_or_order_authority",
    "window_policy": "clean_baseline_expanding_calibration_latest_16_untouched_holdout",
    "sample_floor": {
        "calibration_signal_episodes": 6,
        "calibration_completed_legs": 8,
        "holdout_signal_episodes": 3,
        "holdout_completed_legs": 4,
        "full_window_completed_legs": 10,
    },
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "official_ka10080_success",
        "requested_start_date_fully_bracketed",
        "clean_baseline_minimum_46_trading_dates",
        "valid_unique_completed_sor_regular_ohlc",
        "bounded_carry_rate_and_mark_to_market_drawdown",
    ],
    "forbidden_uses": [
        "current_holdout_outcome_used_for_candidate_selection",
        "cross_profile_outcome_pooling",
        "price_touch_as_real_fill_evidence",
        "same_bar_fill_then_target_assumption",
        "token_issue_refresh_invalidation_or_replacement",
        "account_or_order_api",
        "runtime_policy_threshold_provider_bot_cap_or_broker_guard_mutation",
        "stop_loss_or_forced_exit_creation",
        "active_unrealized_merged_into_completed_ev",
    ],
}


class ResearchError(RuntimeError):
    """Raised when read-only source or research contracts fail closed."""


class ResearchDeferred(ResearchError):
    """Raised when a bounded shared-read wait must resume in a later attempt."""


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open_price: int
    high_price: int
    low_price: int
    close_price: int


@dataclass(frozen=True)
class SignalFeature:
    index: int
    timestamp: datetime
    close_price: int
    drawdown_pct: float
    near_low_pct: float


@dataclass
class DayContext:
    trade_date: date
    bars: tuple[Bar, ...]
    features: dict[int, tuple[SignalFeature, ...]]
    outcome_cache: dict[Any, dict[str, Any]] = field(default_factory=dict)
    _minimum_low_source: tuple[Bar, ...] | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _minimum_low: int | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _feature_minute_index: dict[
        int, tuple[tuple[SignalFeature, ...], array | None]
    ] = field(default_factory=dict, init=False, repr=False, compare=False)
    _signal_partition: dict | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _signal_partition_limit: int = field(
        default=0, init=False, repr=False, compare=False
    )

    def first_signal(self, candidate: SpotCandidate) -> SignalFeature | None:
        """Bounded invocation-local fact, never persistent or custody state."""
        key = (
            candidate.lookback_bars, candidate.scan_start_minute,
            candidate.scan_end_minute, candidate.rolling_high_drawdown_pct,
            candidate.rolling_low_proximity_pct,
        )
        source = self.features[candidate.lookback_bars]
        cached = (self._signal_partition or {}).get(key)
        if isinstance(source, tuple) and cached is not None and cached[0] is source:
            return cached[1]
        signal = next(
            (
                item for item in self.iter_window_features(*key[:3])
                if item.drawdown_pct + 1e-12 >= key[3]
                and item.near_low_pct - 1e-12 <= key[4]
            ),
            None,
        )
        if (self._signal_partition is not None and isinstance(source, tuple)
            and (key in self._signal_partition
                 or len(self._signal_partition) < self._signal_partition_limit)):
            self._signal_partition[key] = (source, signal)
        return signal

    def iter_window_features(
        self, lookback: int, start: int, end: int
    ) -> Iterator[SignalFeature]:
        source = self.features[lookback]
        if not start <= end:
            return iter(())
        if isinstance(source, tuple):
            cached = self._feature_minute_index.get(lookback)
            if cached is None or cached[0] is not source:
                # Minute-of-day is 0..1439. A private read-only-after-build
                # unsigned-short index avoids a Python integer per feature.
                minutes = array(
                    "H",
                    (
                        item.timestamp.hour * 60 + item.timestamp.minute
                        for item in source
                    ),
                )
                # Preserve library callers' original ordering, including
                # duplicate minutes. An unsorted tuple uses the old filter.
                if any(a > b for a, b in zip(minutes, minutes[1:])):
                    minutes = None
                if lookback not in self._feature_minute_index and len(
                    self._feature_minute_index
                ) >= len(LOOKBACK_GRID):
                    self._feature_minute_index.clear()
                cached = (source, minutes)
                self._feature_minute_index[lookback] = cached
            minutes = cached[1]
            if minutes is not None:
                return islice(
                    source, bisect_left(minutes, start), bisect_right(minutes, end)
                )
        # Mutable inputs cannot prove unchanged contents by their identity.
        return (
            item
            for item in source
            if start <= item.timestamp.hour * 60 + item.timestamp.minute <= end
        )

    @property
    def minimum_low_price(self) -> int | None:
        # Bar is frozen and bars is a tuple: share only an immutable day fact,
        # never a candidate's HELD mark/state. A corrected tuple invalidates it.
        if not isinstance(self.bars, tuple):
            # Library callers outside the normalized builder may supply a
            # mutable list. Its identity cannot prove an unchanged day.
            return min((bar.low_price for bar in self.bars), default=None)
        if self._minimum_low_source is not self.bars:
            self._minimum_low = min((bar.low_price for bar in self.bars), default=None)
            self._minimum_low_source = self.bars
        return self._minimum_low


@dataclass(frozen=True)
class SpotCandidate:
    scan_start_minute: int
    scan_end_minute: int
    lookback_bars: int
    rolling_high_drawdown_pct: float
    rolling_low_proximity_pct: float
    entry_offsets_ticks: tuple[int, int] = (0, -1)
    entry_valid_completed_bars: int = 5
    target_ticks: int = 2

    def public(self) -> dict[str, Any]:
        return {
            "scan_start": _minute_text(self.scan_start_minute),
            "scan_end": _minute_text(self.scan_end_minute),
            "lookback_bars": self.lookback_bars,
            "rolling_high_drawdown_pct": self.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": self.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(self.entry_offsets_ticks),
            "entry_valid_completed_bars": self.entry_valid_completed_bars,
            "target_ticks": self.target_ticks,
        }


def _positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return abs(int(float(str(value or "").replace(",", "").strip())))
    except (TypeError, ValueError):
        return 0


def _minute_value(value: time) -> int:
    return value.hour * 60 + value.minute


def _minute_text(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


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


def fetch_sor_history(
    *,
    symbol: str,
    token: str,
    start_date: date,
    end_date: date,
    max_pages: int = 80,
    page_delay_sec: float = 0.2,
    post: Callable[..., requests.Response] = requests.post,
    allowed_symbols: frozenset[str] | None = None,
    expected_trading_day_count: int = CALIBRATION_DAYS + HOLDOUT_DAYS,
    shared_read_control_enabled: bool | None = None,
    shared_defer_max_attempts: int = 12,
    shared_defer_delay_sec: float = 2.0,
    sleeper: Callable[[float], None] = time_module.sleep,
    include_integrated_aftermarket: bool = False,
) -> tuple[list[Bar], dict[str, Any]]:
    """Fetch fully bracketed integrated-SOR bars without auth mutation."""
    symbol_allowlist = allowed_symbols or frozenset(
        profile.symbol for profile in PROFILES.values()
    )
    if symbol not in symbol_allowlist:
        raise ValueError("symbol_not_in_selected_profile_allowlist")
    if start_date < CLEAN_BASELINE_DATE or start_date > end_date:
        raise ValueError("invalid_clean_baseline_date_range")
    if int(expected_trading_day_count) < CALIBRATION_DAYS + HOLDOUT_DAYS:
        raise ValueError("expected_trading_day_count_below_research_minimum")
    clean_token = (
        str(kiwoom_utils.resolve_kiwoom_request_token(token) or "")
        .replace("Bearer ", "")
        .strip()
    )
    if not clean_token:
        raise ResearchError("cached_token_missing")
    request_code = f"{symbol}_AL"
    url = kiwoom_utils.get_api_url("/api/dostk/chart")
    unique: dict[datetime, Bar] = {}
    cont_yn, next_key = "N", ""
    oldest_seen: date | None = None
    invalid_row_count = duplicate_row_count = out_of_session_row_count = 0
    page_count = 0
    start_date_fully_bracketed = False
    continuation_exhausted = False
    shared_read_deferred_count = 0
    shared_read_deferred_wait_sec = 0.0
    shared_read_control = (
        post is requests.post
        if shared_read_control_enabled is None
        else bool(shared_read_control_enabled)
    )
    for page_index in range(max(1, int(max_pages))):
        if shared_read_control:
            admission = None
            for deferred_attempt in range(max(0, int(shared_defer_max_attempts)) + 1):
                admission = kiwoom_utils.acquire_kiwoom_read_capacity(
                    token=clean_token,
                    endpoint=url,
                    request_owner="low_price_two_leg_entry_spot_research",
                    request_class="source_only",
                    api_id="ka10080",
                    request_code=request_code,
                    max_wait_sec=1.25,
                )
                if admission.admitted:
                    break
                shared_read_deferred_count += 1
                if deferred_attempt >= max(0, int(shared_defer_max_attempts)):
                    break
                delay = max(0.0, float(shared_defer_delay_sec))
                if delay:
                    sleeper(delay)
                    shared_read_deferred_wait_sec += delay
            assert admission is not None
            if not admission.admitted:
                raise ResearchDeferred(
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
        try:
            response_body = response.json()
        except ValueError:
            response_body = {}
        if shared_read_control and kiwoom_utils.is_kiwoom_read_rate_limit(
            http_status_code=response.status_code,
            response_body=response_body,
        ):
            kiwoom_utils.record_kiwoom_read_rate_limit(
                token=clean_token,
                endpoint=url,
                request_owner="low_price_two_leg_entry_spot_research",
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
            in_regular = time(9, 0) <= timestamp.time() < time(15, 30)
            in_integrated_aftermarket = bool(
                include_integrated_aftermarket
                and time(16, 0) <= timestamp.time() < time(20, 0)
            )
            if not (in_regular or in_integrated_aftermarket):
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
            bar = Bar(timestamp, prices[0], prices[1], prices[2], prices[3])
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
        "market": (
            "KRX_NXT_integrated_SOR_regular_and_aftermarket"
            if include_integrated_aftermarket
            else "KRX_NXT_integrated_SOR_regular"
        ),
        "included_sessions": (
            ["KRX_REGULAR", "KRX_NXT_AFTERMARKET"]
            if include_integrated_aftermarket
            else ["KRX_REGULAR"]
        ),
        "api_url": url,
        "page_count": page_count,
        "bar_count": len(bars),
        "trading_date_count": len(trading_dates),
        "observed_trading_dates": trading_dates,
        "expected_trading_date_count": int(expected_trading_day_count),
        "oldest_source_date": trading_dates[0] if trading_dates else None,
        "latest_source_date": trading_dates[-1] if trading_dates else None,
        "start_date_fully_bracketed": start_date_fully_bracketed,
        "continuation_exhausted": continuation_exhausted,
        "invalid_row_count": invalid_row_count,
        "duplicate_row_count": duplicate_row_count,
        "out_of_session_row_count": out_of_session_row_count,
        "source_quality_status": source_quality_status,
        "shared_read_deferred_count": shared_read_deferred_count,
        "shared_read_deferred_wait_sec": round(shared_read_deferred_wait_sec, 3),
    }
    if source_quality_status != "PASS":
        error = ResearchError(f"{symbol}_source_quality_{source_quality_status.lower()}")
        # Keep the actual collector receipt when the caller quarantines this
        # symbol. A generic failure string cannot identify a missing window.
        error.source_quality_meta = meta
        raise error
    return bars, meta


def build_day_contexts(bars: list[Bar]) -> dict[date, DayContext]:
    grouped: dict[date, list[Bar]] = {}
    for bar in bars:
        grouped.setdefault(bar.timestamp.date(), []).append(bar)
    contexts: dict[date, DayContext] = {}
    for trade_date, raw_day in sorted(grouped.items()):
        day = tuple(sorted(raw_day, key=lambda item: item.timestamp))
        features: dict[int, tuple[SignalFeature, ...]] = {}
        for lookback in LOOKBACK_GRID:
            rows: list[SignalFeature] = []
            highs: deque[int] = deque()
            lows: deque[int] = deque()
            last_discontinuity = 0
            for index, candidate in enumerate(day):
                start = index - lookback + 1
                if index and candidate.timestamp - day[
                    index - 1
                ].timestamp != timedelta(minutes=1):
                    last_discontinuity = index
                while highs and highs[0] < start:
                    highs.popleft()
                while lows and lows[0] < start:
                    lows.popleft()
                while highs and day[highs[-1]].high_price < candidate.high_price:
                    highs.pop()
                while lows and day[lows[-1]].low_price > candidate.low_price:
                    lows.pop()
                highs.append(index)
                lows.append(index)
                # A break immediately before the first window bar is allowed;
                # a gap/duplicate inside the window remains excluded.
                if start < 0 or last_discontinuity > start:
                    continue
                rolling_high = day[highs[0]].high_price
                rolling_low = day[lows[0]].low_price
                if min(rolling_high, rolling_low, candidate.close_price) <= 0:
                    continue
                rows.append(
                    SignalFeature(
                        index=index,
                        timestamp=candidate.timestamp,
                        close_price=candidate.close_price,
                        drawdown_pct=(rolling_high - candidate.close_price)
                        / rolling_high
                        * 100.0,
                        near_low_pct=(candidate.close_price - rolling_low)
                        / rolling_low
                        * 100.0,
                    )
                )
            features[lookback] = tuple(rows)
        contexts[trade_date] = DayContext(trade_date, day, features)
    return contexts


def _window_grid(profile: MachineProfile) -> tuple[tuple[int, int], ...]:
    lower = _minute_value(profile.policy.scan_start)
    upper = _minute_value(profile.policy.scan_last_bar)
    windows: set[tuple[int, int]] = {(lower, upper)}
    for start in range(lower, upper - 8, 5):
        for duration in (10, 20, 30):
            end = start + duration - 1
            if end <= upper:
                windows.add((start, end))
        if upper - start + 1 >= 10:
            windows.add((start, upper))
    return tuple(sorted(windows))


def candidate_grid(profile: MachineProfile) -> tuple[SpotCandidate, ...]:
    if bool(getattr(profile, "fixed_observation", False)):
        # A fixed observation candidate must accumulate evidence for one
        # immutable policy. Re-optimizing it every day would turn the latest
        # 16-day holdout into a moving selection target.
        return (baseline_candidate(profile),)
    baseline_plan = (
        tuple(profile.policy.entry_offsets_ticks),
        int(profile.policy.entry_valid_completed_bars),
        int(profile.policy.target_ticks),
    )
    profile_extensions = PROFILE_EXECUTION_PLAN_EXTENSIONS.get(profile.profile_id, ())
    if profile_extensions:
        execution_plans = tuple(dict.fromkeys((baseline_plan, *profile_extensions)))
    elif getattr(profile, "discovery_lane", "") == "existing_symbol_logic_improvement":
        execution_plans = tuple(dict.fromkeys((baseline_plan, *EXECUTION_PLAN_GRID)))
    else:
        execution_plans = (baseline_plan,)
    return tuple(
        SpotCandidate(
            start,
            end,
            lookback,
            drawdown,
            near_low,
            tuple(offsets),
            valid_bars,
            target_ticks,
        )
        for start, end in _window_grid(profile)
        for lookback in LOOKBACK_GRID
        for drawdown in DRAWDOWN_GRID
        for near_low in NEAR_LOW_GRID
        for offsets, valid_bars, target_ticks in execution_plans
    )


def baseline_candidate(profile: MachineProfile) -> SpotCandidate:
    return SpotCandidate(
        _minute_value(profile.policy.scan_start),
        _minute_value(profile.policy.scan_last_bar),
        profile.policy.lookback_bars,
        profile.policy.rolling_high_drawdown_pct,
        profile.policy.rolling_low_proximity_pct,
        tuple(profile.policy.entry_offsets_ticks),
        int(profile.policy.entry_valid_completed_bars),
        int(profile.policy.target_ticks),
    )


def _leg_outcome(
    *,
    entry_price: int,
    fill_bars: tuple[Bar, ...],
    target_bars: tuple[Bar, ...],
    target_ticks: int = 2,
) -> dict[str, Any]:
    fill = next((bar for bar in fill_bars if bar.low_price <= entry_price), None)
    if fill is None:
        return {"status": "NO_FILL", "entry_price": entry_price}
    target_price = move_price_by_ticks(entry_price, target_ticks)
    post_fill_bars = tuple(bar for bar in target_bars if bar.timestamp > fill.timestamp)
    completed_bar = next(
        (bar for bar in post_fill_bars if bar.high_price >= target_price), None
    )
    observed_bars = tuple(
        bar
        for bar in post_fill_bars
        if completed_bar is None or bar.timestamp <= completed_bar.timestamp
    ) or (fill,)
    minimum_price = min(bar.low_price for bar in observed_bars)
    maximum_price = max(bar.high_price for bar in observed_bars)
    result = {
        "status": "COMPLETE" if completed_bar else "HELD",
        "entry_price": entry_price,
        "target_price": target_price,
        "fill_at": fill.timestamp.isoformat(),
        "holding_completed_bars": len(observed_bars),
        "max_adverse_excursion_pct": round(
            (minimum_price / entry_price - 1.0) * 100.0, 6
        ),
        "max_favorable_excursion_pct": round(
            (maximum_price / entry_price - 1.0) * 100.0, 6
        ),
    }
    if completed_bar:
        result["target_at"] = completed_bar.timestamp.isoformat()
        result["net_profit_pct"] = round(
            (target_price / entry_price - 1.0) * 100.0 - COST_PCT, 6
        )
    else:
        mark_price = int(observed_bars[-1].close_price)
        result["mark_price"] = mark_price
        result["active_unrealized_pct"] = round(
            (mark_price / entry_price - 1.0) * 100.0 - COST_PCT, 6
        )
    return result


def _episode(
    context: DayContext, signal: SignalFeature, candidate: SpotCandidate
) -> dict[str, Any]:
    cache_key = (
        signal.index,
        candidate.entry_offsets_ticks,
        candidate.entry_valid_completed_bars,
        candidate.target_ticks,
    )
    cached = context.outcome_cache.get(cache_key)
    if cached is None and (
        candidate.entry_offsets_ticks,
        candidate.entry_valid_completed_bars,
        candidate.target_ticks,
    ) == ((0, -1), 5, 2):
        cached = context.outcome_cache.get(signal.index)
    if cached is not None:
        # Execution prices may share a cache across lookbacks, but the signal
        # features belong to this candidate's prefix, not the first cache user.
        return {
            **cached,
            "date": context.trade_date.isoformat(),
            "signal_at": signal.timestamp.isoformat(),
            "signal_close": signal.close_price,
            "observed_drawdown_pct": round(signal.drawdown_pct, 6),
            "observed_near_low_pct": round(signal.near_low_pct, 6),
        }
    close = clamp_price_to_tick(signal.close_price)
    # A regular-session signal must never borrow an integrated-aftermarket bar
    # (or the following day) as a synthetic fill/target.  Stop at the first
    # discontinuity so each research episode stays inside its own venue/session
    # cohort even when the source contains both daily sessions.
    contiguous_after_signal: list[Bar] = []
    previous = context.bars[signal.index]
    for bar in context.bars[signal.index + 1 :]:
        if bar.timestamp - previous.timestamp != timedelta(minutes=1):
            break
        contiguous_after_signal.append(bar)
        previous = bar
    target_bars = tuple(contiguous_after_signal)
    fill_bars = target_bars[: candidate.entry_valid_completed_bars]
    legs = [
        _leg_outcome(
            entry_price=entry_price,
            fill_bars=fill_bars,
            target_bars=target_bars,
            target_ticks=candidate.target_ticks,
        )
        for entry_price in (
            move_price_by_ticks(close, offset)
            for offset in candidate.entry_offsets_ticks
        )
    ]
    episode = {
        "date": context.trade_date.isoformat(),
        "signal_at": signal.timestamp.isoformat(),
        "signal_close": signal.close_price,
        "observed_drawdown_pct": round(signal.drawdown_pct, 6),
        "observed_near_low_pct": round(signal.near_low_pct, 6),
        "execution_plan": {
            "entry_offsets_ticks": list(candidate.entry_offsets_ticks),
            "entry_valid_completed_bars": candidate.entry_valid_completed_bars,
            "target_ticks": candidate.target_ticks,
        },
        "legs": legs,
    }
    context.outcome_cache[cache_key] = episode
    return episode


def _summary(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    legs = [leg for episode in episodes for leg in episode["legs"]]
    completed = [leg for leg in legs if leg["status"] == "COMPLETE"]
    filled = [leg for leg in legs if leg["status"] in {"COMPLETE", "HELD"}]
    held = [leg for leg in legs if leg["status"] == "HELD"]
    attempted_notional = sum(int(leg["entry_price"]) for leg in legs)
    realized_profit = sum(
        int(leg["entry_price"]) * float(leg["net_profit_pct"]) / 100.0
        for leg in completed
    )
    ev = realized_profit / attempted_notional * 100.0 if attempted_notional else None
    held_notional = sum(int(leg["entry_price"]) for leg in held)
    held_mark_value = sum(
        int(leg["entry_price"])
        * float(leg.get("active_unrealized_pct", 0.0) or 0.0)
        / 100.0
        for leg in held
    )
    held_mark_to_market_pct = (
        held_mark_value / held_notional * 100.0 if held_notional else None
    )
    held_rate = len(held) / len(filled) if filled else 0.0
    worst_held_mark_to_market_pct = min(
        (float(leg.get("active_unrealized_pct", 0.0) or 0.0) for leg in held),
        default=None,
    )
    return {
        "signal_episodes": len(episodes),
        "attempted_legs": len(legs),
        "completed_legs": len(completed),
        "filled_legs": len(filled),
        "no_fill_legs": sum(leg["status"] == "NO_FILL" for leg in legs),
        "held_legs": len(held),
        "held_leg_rate_per_filled_leg": round(held_rate, 6),
        "held_notional_krw": held_notional,
        "active_unrealized_notional_weighted_pct": (
            round(held_mark_to_market_pct, 6)
            if held_mark_to_market_pct is not None
            else None
        ),
        "worst_held_active_unrealized_pct": worst_held_mark_to_market_pct,
        "worst_filled_max_adverse_excursion_pct": min(
            (float(leg.get("max_adverse_excursion_pct", 0.0) or 0.0) for leg in filled),
            default=None,
        ),
        "capital_exposure_completed_bars": sum(
            int(leg.get("holding_completed_bars", 0) or 0) for leg in filled
        ),
        "realized_net_profit_krw": round(realized_profit, 2),
        "realized_net_profit_krw_per_episode": (
            round(realized_profit / len(episodes), 2) if episodes else None
        ),
        "completed_legs_per_attempted_leg": (
            round(len(completed) / len(legs), 6) if legs else None
        ),
        "notional_weighted_ev_pct": round(ev, 6) if ev is not None else None,
    }


def evaluate_candidate(
    candidate: SpotCandidate,
    contexts: dict[date, DayContext],
    dates: list[date],
    *,
    include_episodes: bool = False,
) -> dict[str, Any]:
    return _evaluate_candidate_windows(
        candidate, contexts, [dates], include_episodes=include_episodes
    )[0]


def _advance_candidate_day(candidate, context, carried):
    """Compute one original custody transition; window membership is irrelevant."""
    if carried is not None:
        day_low = context.minimum_low_price
        for leg in carried["legs"]:
            if leg["status"] != "HELD" or not context.bars:
                continue
            price = int(leg["entry_price"])
            leg["holding_completed_bars"] = int(
                leg.get("holding_completed_bars", 0)
            ) + len(context.bars)
            leg["mark_price"] = context.bars[-1].close_price
            leg["active_unrealized_pct"] = round(
                (leg["mark_price"] / price - 1) * 100 - COST_PCT, 6
            )
            leg["max_adverse_excursion_pct"] = min(
                float(leg.get("max_adverse_excursion_pct", 0)),
                (day_low / price - 1) * 100,
            )
        return carried, None
    if context._signal_partition is None:
        signal = next(
            (
                item
                for item in context.iter_window_features(
                    candidate.lookback_bars,
                    candidate.scan_start_minute,
                    candidate.scan_end_minute,
                )
                if item.drawdown_pct + 1e-12 >= candidate.rolling_high_drawdown_pct
                and item.near_low_pct - 1e-12 <= candidate.rolling_low_proximity_pct
            ),
            None,
        )
    else:
        signal = context.first_signal(candidate)
    episode = _episode(context, signal, candidate) if signal is not None else None
    if episode and any(leg["status"] == "HELD" for leg in episode["legs"]):
        episode = deepcopy(episode)
        return episode, episode
    return None, episode


def _evaluate_candidate_windows(
    candidate: SpotCandidate,
    contexts: dict[date, DayContext],
    windows: list[list[date]],
    *,
    include_episodes: bool = False,
) -> list[dict[str, Any]]:
    """Replay one candidate prefix; seal each window at its own last date.

    Optional scoped transitions restore independent custody copies. A later
    carry update must not change an earlier window's sealed evidence.
    """
    if not windows or any(
        not dates
        or len(dates) != len(set(dates))
        or any(day not in contexts for day in dates)
        for dates in windows
    ):
        raise ResearchError("economic_replay_observation_dates_invalid")
    if any(day < CLEAN_BASELINE_DATE for day in contexts):
        raise ResearchError("economic_replay_prebaseline_context_forbidden")
    boundaries: dict[date, list[int]] = {}
    for index, dates in enumerate(windows):
        boundaries.setdefault(max(dates), []).append(index)
    requested = [set(dates) for dates in windows]
    requested_union = set().union(*requested)
    results: dict[int, dict[str, Any]] = {}
    last_date = max(boundaries)
    events: list[tuple[date, dict[str, Any]]] = []
    blocked: list[date] = []
    carried: dict[str, Any] | None = None
    # Start at the clean prefix even for a half/holdout view. Otherwise slicing
    # the window would erase the inventory that prevented the next entry.
    for trade_date in sorted(day for day in contexts if day <= last_date):
        context = contexts[trade_date]
        previous = carried
        if previous is not None and trade_date in requested_union:
            blocked.append(trade_date)
        transition = _DAY_REPLAY.get()
        if transition is None:
            carried, episode = _advance_candidate_day(candidate, context, carried)
        else:
            carried, episode = transition(candidate, context, carried)
            # Restore the alias between an original HELD event and its evolving
            # custody. Serialized checkpoints cannot preserve object identity.
            if previous is not None:
                if carried is not previous:
                    previous.clear()
                    previous.update(carried)
                carried = previous
            elif carried is not None:
                episode = carried
        if episode is not None and trade_date in requested_union:
            events.append((trade_date, episode))
        for index in boundaries.get(trade_date, ()):
            dates = windows[index]
            episodes = [episode for day, episode in events if day in requested[index]]
            result = _summary(episodes)
            result.update(
                {
                    "economic_replay_contract": ECONOMIC_REPLAY_CONTRACT,
                    "metric_contract": ECONOMIC_METRIC_CONTRACT,
                    "source_valid_observation_days": len(dates),
                    "observation_dates": [day.isoformat() for day in sorted(dates)],
                    "cost_pct": COST_PCT,
                    "cost_adjusted_net_profit_krw_per_source_valid_observation_day": round(
                        result["realized_net_profit_krw"] / len(dates), 8
                    ),
                    "attempted_episodes_per_source_valid_observation_day": round(
                        len(episodes) / len(dates), 8
                    ),
                    "custody_blocked_dates": [
                        day.isoformat() for day in blocked if day in requested[index]
                    ],
                    "custody_resolution_required": carried is not None,
                    "carry_in_held_legs": (
                        sum(
                            leg["status"] == "HELD"
                            for leg in (carried or {}).get("legs", [])
                        )
                        if carried and carried["date"] < min(dates).isoformat()
                        else 0
                    ),
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "source_only_no_runtime_or_order_authority",
                }
            )
            if include_episodes:
                result["episodes"] = deepcopy(episodes)
            results[index] = result
    return [results[index] for index in range(len(windows))]


def _positive_ev(summary: dict[str, Any]) -> bool:
    value = summary.get("notional_weighted_ev_pct")
    return value is not None and float(value) > 0.0


def _calibration_ready(
    full: dict[str, Any], first: dict[str, Any], second: dict[str, Any]
) -> bool:
    return bool(
        _calibration_sample_ready(full, first, second)
        and _manageable_carry(full)
        and _positive_ev(full)
    )


def _manageable_carry(summary: dict[str, Any]) -> bool:
    held_rate = float(summary.get("held_leg_rate_per_filled_leg", 0.0) or 0.0)
    worst_mark = summary.get("worst_held_active_unrealized_pct")
    return bool(
        held_rate <= MAX_MANAGEABLE_HELD_LEG_RATE + 1e-12
        and (
            worst_mark is None
            or float(worst_mark) >= -MAX_MANAGEABLE_HELD_MARK_TO_MARKET_LOSS_PCT - 1e-12
        )
    )


def _calibration_sample_ready(
    full: dict[str, Any], first: dict[str, Any], second: dict[str, Any]
) -> bool:
    return bool(full["signal_episodes"] >= 6 and full["completed_legs"] >= 8)


def _robust_score(first: dict[str, Any], second: dict[str, Any]) -> float:
    values = []
    for summary in (first, second):
        completed = int(summary["completed_legs"])
        ev = float(summary.get("notional_weighted_ev_pct") or 0.0)
        values.append(ev * completed / (completed + 6.0))
    return min(values)


def paired_economics(current: dict, candidate: dict) -> dict:
    """Compare the same observation window, not just profitable trade averages."""
    days = current.get("source_valid_observation_days")
    observed_dates = current.get("observation_dates")
    valid = bool(
        isinstance(days, int)
        and not isinstance(days, bool)
        and days > 0
        and isinstance(observed_dates, list)
        and all(isinstance(day, str) for day in observed_dates)
        and len(observed_dates) == len(set(observed_dates)) == days
        and days == candidate.get("source_valid_observation_days")
        and current.get("observation_dates")
        and current.get("observation_dates") == candidate.get("observation_dates")
        and current.get("cost_pct") == candidate.get("cost_pct") == COST_PCT
        and current.get("economic_replay_contract")
        == candidate.get("economic_replay_contract")
        == ECONOMIC_REPLAY_CONTRACT
    )
    current_net = current.get(
        "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
    )
    candidate_net = candidate.get(
        "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
    )
    try:
        uplift = (
            float(candidate_net) - float(current_net)
            if valid and current_net is not None and candidate_net is not None
            else None
        )
    except (TypeError, ValueError, OverflowError):
        valid, uplift = False, None
    if uplift is None or not math.isfinite(uplift):
        valid, uplift = False, None
    return {
        "economic_replay_contract": ECONOMIC_REPLAY_CONTRACT,
        "comparable_observation_window": valid,
        "net_profit_uplift_krw_per_observation_day": uplift,
        "net_profit_improved": bool(uplift is not None and uplift > 1e-9),
        "current_attempt_frequency": current.get(
            "attempted_episodes_per_source_valid_observation_day"
        ),
        "candidate_attempt_frequency": candidate.get(
            "attempted_episodes_per_source_valid_observation_day"
        ),
        "runtime_effect": False,
        "decision_authority": "source_only_no_runtime_or_order_authority",
    }


def existing_axis_economic_replay(
    profile: MachineProfile, contexts: dict[date, DayContext]
) -> dict:
    """Replay only the two existing filter axes; all execution fields stay fixed."""
    baseline = baseline_candidate(profile)
    dates = sorted(contexts)
    from src.trading.low_price_two_leg.policy_runtime import (
        policy_bounds_for_target_date,
    )

    profile_id = profile.profile_id.removeprefix("logic_")
    bounds = policy_bounds_for_target_date(dates[-1]).get(profile_id)
    if bounds is None:
        raise ResearchError("existing_axis_replay_unknown_live_profile")
    current = evaluate_candidate(baseline, contexts, dates, include_episodes=True)
    alternatives = []
    for axis, after in (
        ("rolling_high_drawdown_pct", bounds["drawdown_max"]),
        ("rolling_low_proximity_pct", bounds["near_low_min"]),
    ):
        if after == getattr(baseline, axis):
            continue
        candidate = replace(baseline, **{axis: after})
        outcome = evaluate_candidate(candidate, contexts, dates, include_episodes=True)
        comparison = paired_economics(current, outcome)
        alternatives.append(
            {
                "axis": axis,
                "before": getattr(baseline, axis),
                "after": after,
                "parameters": candidate.public(),
                "outcome": outcome,
                "comparison": comparison,
                "decision": (
                    "hold_source_gap_external_custody_resolution"
                    if current["custody_resolution_required"]
                    or outcome["custody_resolution_required"]
                    else (
                        "source_only_positive_path_requires_confirmation"
                        if comparison["net_profit_improved"] and _positive_ev(outcome)
                        else "hold_no_edge"
                    )
                ),
            }
        )
    return {
        "economic_replay_contract": ECONOMIC_REPLAY_CONTRACT,
        "metric_contract": ECONOMIC_METRIC_CONTRACT,
        "current_parameters": baseline.public(),
        "current_outcome": current,
        "alternatives": alternatives,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "source_only_no_runtime_or_order_authority",
    }


def valid_existing_axis_economic_replay(replay: Any) -> bool:
    """Check the source-only handoff without granting it execution authority."""
    if not isinstance(replay, dict):
        return False
    if replay.get("status") == "source_runtime_policy_unavailable":
        return (
            replay.get("runtime_effect") is False
            and replay.get("allowed_runtime_apply") is False
        )
    if (
        replay.get("economic_replay_contract") != ECONOMIC_REPLAY_CONTRACT
        or replay.get("metric_contract") != ECONOMIC_METRIC_CONTRACT
        or replay.get("runtime_effect") is not False
        or replay.get("allowed_runtime_apply") is not False
        or replay.get("actual_order_submitted") is not False
        or replay.get("broker_order_forbidden") is not True
        or replay.get("decision_authority")
        != "source_only_no_runtime_or_order_authority"
    ):
        return False
    current = replay.get("current_outcome")
    parameters = replay.get("current_parameters")
    alternatives = replay.get("alternatives")
    if (
        not isinstance(current, dict)
        or not isinstance(current.get("episodes"), list)
        or not isinstance(parameters, dict)
        or not isinstance(alternatives, list)
        or len(alternatives) > 2
    ):
        return False
    seen = set()
    for item in alternatives:
        if not isinstance(item, dict):
            return False
        axis = item.get("axis")
        if (
            axis not in {"rolling_high_drawdown_pct", "rolling_low_proximity_pct"}
            or axis in seen
        ):
            return False
        seen.add(axis)
        outcome = item.get("outcome")
        expected = {**parameters, axis: item.get("after")}
        if (
            item.get("parameters") != expected
            or item.get("before") != parameters.get(axis)
            or not isinstance(outcome, dict)
            or not isinstance(outcome.get("episodes"), list)
            or item.get("comparison") != paired_economics(current, outcome)
            or not item["comparison"]["comparable_observation_window"]
        ):
            return False
    return True


def _retain_calibration_candidate(heap, item, ordinal, limit):
    """Keep only published evidence; evaluate/count every grid member.

    Earlier grid order wins an exact tie, as with the original stable sort.
    The ordinal also keeps heap comparisons away from mutable evidence.
    """
    key = (
        item[4]["full"][
            "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
        ],
        item[0],
        item[1],
        item[2],
        -ordinal,
    )
    if len(heap) < limit:
        heappush(heap, (key, item))
    elif key > heap[0][0]:
        heapreplace(heap, (key, item))


def select_profile_spot(
    profile: MachineProfile,
    contexts: dict[date, DayContext],
    *,
    calibration_days: int = CALIBRATION_DAYS,
    holdout_days: int = HOLDOUT_DAYS,
) -> dict[str, Any]:
    dates = sorted(contexts)
    if calibration_days < CALIBRATION_DAYS or holdout_days < HOLDOUT_DAYS:
        raise ValueError("research_split_below_minimum_sample_window")
    required_days = calibration_days + holdout_days
    if len(dates) != required_days:
        raise ResearchError(f"{profile.profile_id}_requires_{required_days}_dates")
    calibration = dates[:calibration_days]
    holdout = dates[calibration_days:]
    first_half = calibration[: calibration_days // 2]
    second_half = calibration[calibration_days // 2 :]
    ranked_heap = []
    diagnostic_heap = []
    calibration_ready_count = 0
    grid = candidate_grid(profile)
    search_keys = {
        (item.lookback_bars, item.scan_start_minute, item.scan_end_minute,
         item.rolling_high_drawdown_pct, item.rolling_low_proximity_pct)
        for item in grid
    }
    # Execution-plan alternatives often repeat exactly the same signal
    # search. Share only that immutable fact, not episode/leg/carry outcomes.
    # Unique-key grids retain the fast reference path. Reset at each selector
    # invocation; append, split changes and corrections replay normally.
    repeated_searches = len(search_keys) < len(grid)
    for context in contexts.values():
        context._signal_partition = {} if repeated_searches else None
        context._signal_partition_limit = 64_000 // max(1, len(contexts))
    sample_ready_count = manageable_carry_count = both_half_positive_count = 0
    for ordinal, candidate in enumerate(grid):
        first, second, full = _evaluate_candidate_windows(
            candidate, contexts, [first_half, second_half, calibration]
        )
        evidence = {"first_half": first, "second_half": second, "full": full}
        if _calibration_sample_ready(full, first, second):
            sample_ready_count += 1
            manageable_carry = all(
                _manageable_carry(summary) for summary in (full, first, second)
            )
            if manageable_carry:
                manageable_carry_count += 1
                score = _robust_score(first, second)
                _retain_calibration_candidate(
                    diagnostic_heap,
                    (
                        score,
                        float(full["notional_weighted_ev_pct"]),
                        int(full["completed_legs"]),
                        candidate,
                        evidence,
                    ),
                    ordinal,
                    1,
                )
                if _positive_ev(first) and _positive_ev(second):
                    both_half_positive_count += 1
        if not _calibration_ready(full, first, second):
            continue
        score = _robust_score(first, second)
        calibration_ready_count += 1
        _retain_calibration_candidate(
            ranked_heap,
            (
                score,
                float(full["notional_weighted_ev_pct"]),
                int(full["completed_legs"]),
                candidate,
                evidence,
            ),
            ordinal,
            10,
        )

    ranked = [
        item for _, item in sorted(ranked_heap, key=lambda row: row[0], reverse=True)
    ]
    diagnostic_ranked = [item for _, item in diagnostic_heap]
    baseline = baseline_candidate(profile)
    # Keep each observation boundary sealed, but traverse the custody prefix
    # only once. The first two views remain summary-only in the public report.
    baseline_views = _evaluate_candidate_windows(
        baseline, contexts, [calibration, holdout, dates], include_episodes=True
    )
    for view in baseline_views[:2]:
        view.pop("episodes", None)
    baseline_results = dict(zip(("calibration", "holdout", "full"), baseline_views))
    if not ranked:
        return {
            "profile_id": profile.profile_id,
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "date_split": {
                "calibration_start": calibration[0].isoformat(),
                "calibration_end": calibration[-1].isoformat(),
                "holdout_start": holdout[0].isoformat(),
                "holdout_end": holdout[-1].isoformat(),
                "calibration_trading_day_count": len(calibration),
                "holdout_trading_day_count": len(holdout),
            },
            "grid_candidate_count": len(grid),
            "calibration_ready_candidate_count": 0,
            "calibration_gate_counts": {
                "sample_ready": sample_ready_count,
                "manageable_carry": manageable_carry_count,
                "both_halves_positive_ev": both_half_positive_count,
            },
            "best_diagnostic_candidate": (
                _ranked_item_public(diagnostic_ranked[0]) if diagnostic_ranked else None
            ),
            "baseline": {"parameters": baseline.public(), **baseline_results},
            "selected": {"parameters": baseline.public(), **baseline_results},
            "recommended_spot": None,
            "top_calibration_candidates": [],
            "decision": "no_robust_calibration_candidate_do_not_promote",
            "recommended_action": "do_not_activate_profile_from_this_evidence",
            "runtime_effect": False,
        }
    score, _, _, candidate, calibration_evidence = ranked[0]
    candidate_views = _evaluate_candidate_windows(
        candidate, contexts, [holdout, dates], include_episodes=True
    )
    candidate_views[0].pop("episodes", None)
    candidate_results = {
        "calibration": calibration_evidence["full"],
        "calibration_first_half": calibration_evidence["first_half"],
        "calibration_second_half": calibration_evidence["second_half"],
        "holdout": candidate_views[0],
        "full": candidate_views[1],
    }
    candidate_holdout = candidate_results["holdout"]
    holdout_ready = bool(
        candidate_holdout["signal_episodes"] >= 3
        and candidate_holdout["completed_legs"] >= 4
        and _manageable_carry(candidate_holdout)
        and candidate_results["full"]["completed_legs"] >= 10
        and _manageable_carry(candidate_results["full"])
        and _positive_ev(candidate_holdout)
    )
    beats_baseline = bool(
        holdout_ready
        and paired_economics(baseline_results["holdout"], candidate_holdout)[
            "net_profit_improved"
        ]
    )
    if beats_baseline:
        decision = "holdout_pass_source_only_early_candidate"
        recommended_action = "source_only_candidate_requires_separate_runtime_change"
        selected_parameters = candidate.public()
        selected_results = candidate_results
    elif holdout_ready:
        decision = "holdout_positive_not_better_keep_baseline"
        recommended_action = "retain_existing_baseline"
        selected_parameters = baseline.public()
        selected_results = baseline_results
    else:
        decision = "holdout_failed_keep_baseline"
        recommended_action = "retain_existing_baseline"
        selected_parameters = baseline.public()
        selected_results = baseline_results
    top = [_ranked_item_public(item) for item in ranked[:10]]
    return {
        "profile_id": profile.profile_id,
        "symbol": profile.symbol,
        "name": profile.name,
        "session": profile.session,
        "date_split": {
            "calibration_start": calibration[0].isoformat(),
            "calibration_end": calibration[-1].isoformat(),
            "holdout_start": holdout[0].isoformat(),
            "holdout_end": holdout[-1].isoformat(),
            "calibration_trading_day_count": len(calibration),
            "holdout_trading_day_count": len(holdout),
        },
        "grid_candidate_count": len(grid),
        "calibration_ready_candidate_count": calibration_ready_count,
        "calibration_gate_counts": {
            "sample_ready": sample_ready_count,
            "manageable_carry": manageable_carry_count,
            "both_halves_positive_ev": both_half_positive_count,
        },
        "best_diagnostic_candidate": (
            _ranked_item_public(diagnostic_ranked[0]) if diagnostic_ranked else None
        ),
        "baseline": {"parameters": baseline.public(), **baseline_results},
        "paired_economics": paired_economics(
            baseline_results["holdout"], candidate_holdout
        ),
        "calibration_half_diagnostics": {
            "first_half_positive_ev": _positive_ev(calibration_evidence["first_half"]),
            "second_half_positive_ev": _positive_ev(
                calibration_evidence["second_half"]
            ),
            "decision_authority": "robustness_diagnostic_not_standalone_veto",
        },
        "calibration_winner": {
            "parameters": candidate.public(),
            "robust_calibration_score": round(score, 6),
            **candidate_results,
        },
        "selected": {"parameters": selected_parameters, **selected_results},
        "recommended_spot": selected_parameters,
        "top_calibration_candidates": top,
        "decision": decision,
        "recommended_action": recommended_action,
        "runtime_effect": False,
    }


def _ranked_item_public(
    item: tuple[float, float, int, SpotCandidate, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "robust_calibration_score": round(item[0], 6),
        "parameters": item[3].public(),
        "calibration_first_half": item[4]["first_half"],
        "calibration_second_half": item[4]["second_half"],
        "calibration_full": item[4]["full"],
    }


def build_report(
    *,
    sources: dict[str, tuple[list[Bar], dict[str, Any]]],
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    if start_date != CLEAN_BASELINE_DATE or end_date != DEFAULT_END_DATE:
        raise ValueError("research_window_must_match_clean_baseline_46_day_contract")
    contexts_by_symbol = {
        symbol: build_day_contexts(bars) for symbol, (bars, _) in sources.items()
    }
    date_sets = [tuple(sorted(contexts)) for contexts in contexts_by_symbol.values()]
    if not date_sets or any(dates != date_sets[0] for dates in date_sets[1:]):
        raise ResearchError("cross_symbol_trading_dates_mismatch")
    profiles = {
        profile_id: select_profile_spot(profile, contexts_by_symbol[profile.symbol])
        for profile_id, profile in PROFILES.items()
    }
    decisions = [item["decision"] for item in profiles.values()]
    return {
        "schema": REPORT_SCHEMA,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "cost_pct": COST_PCT,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "grid": {
            "lookback_bars": list(LOOKBACK_GRID),
            "drawdown_pct": list(DRAWDOWN_GRID),
            "near_low_pct": list(NEAR_LOW_GRID),
            "time_window_policy": "profile_base_window_subwindows_starting_every_5_minutes",
            "entry_valid_completed_bars": 5,
            "target_ticks": 2,
            "quantity": 2,
            "allocation": "one_share_signal_close_one_share_signal_close_minus_1tick",
            "same_bar_fill_target": "forbidden_target_starts_after_fill_bar",
            "stop_loss": "none",
            "unclosed_position": "held",
        },
        "source_meta": {symbol: meta for symbol, (_, meta) in sources.items()},
        "profiles": profiles,
        "decision": (
            "profile_specific_spots_holdout_pass_source_only"
            if all(
                item == "holdout_pass_source_only_early_candidate" for item in decisions
            )
            else "mixed_profile_validation_source_only_do_not_promote_failed_profiles"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Lower-price profile entry-spot research — {report['end_date']}",
        "",
        "Source-only 30-day calibration / 16-day untouched holdout. No runtime policy was changed.",
        "",
        "| Profile | Symbol | Session | Decision | Selected window | Lookback | Drawdown | Near low | Holdout legs | Held | Holdout EV | Baseline EV |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["profiles"].values():
        selected = item["selected"]
        params = item["recommended_spot"]
        holdout = selected["holdout"]
        baseline_ev = item["baseline"]["holdout"]["notional_weighted_ev_pct"]
        if params is None:
            window = lookback = drawdown = near_low = "N/A"
        else:
            window = f"{params['scan_start']}~{params['scan_end']}"
            lookback = params["lookback_bars"]
            drawdown = params["rolling_high_drawdown_pct"]
            near_low = params["rolling_low_proximity_pct"]
        lines.append(
            f"| {item['profile_id']} | {item['symbol']} | {item['session']} | "
            f"{item['decision']} | {window} | {lookback} | {drawdown} | "
            f"{near_low} | {holdout['completed_legs']} | "
            f"{holdout['held_legs']} | {holdout['notional_weighted_ev_pct']} | "
            f"{baseline_ev} |"
        )
    lines.extend(
        [
            "",
            "Candidate selection never reads holdout outcomes. Price touches are minute-bar proxies, not real fills.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_report(
    report: dict[str, Any], output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"low_price_two_leg_entry_spot_research_{report['end_date']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(md_path, render_markdown(report))
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", default=CLEAN_BASELINE_DATE.isoformat())
    parser.add_argument("--end-date", default=DEFAULT_END_DATE.isoformat())
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--page-delay-sec", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    token = kiwoom_utils.get_cached_kiwoom_token()
    if not token:
        raise ResearchError("cached_token_missing_no_issue_or_refresh_allowed")
    sources = {}
    for symbol in sorted({profile.symbol for profile in PROFILES.values()}):
        sources[symbol] = fetch_sor_history(
            symbol=symbol,
            token=token,
            start_date=start_date,
            end_date=end_date,
            max_pages=args.max_pages,
            page_delay_sec=args.page_delay_sec,
        )
    report = build_report(sources=sources, start_date=start_date, end_date=end_date)
    paths = write_report(report, args.output_dir) if args.write else (None, None)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "decision": report["decision"],
                    "profiles": {
                        key: {
                            "decision": item["decision"],
                            "recommended_spot": item["recommended_spot"],
                            "holdout": item["selected"]["holdout"],
                        }
                        for key, item in report["profiles"].items()
                    },
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
