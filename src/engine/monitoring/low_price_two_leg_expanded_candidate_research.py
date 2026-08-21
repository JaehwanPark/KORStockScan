"""Expanding clean-baseline entry-spot research for lower-price machines.

The source-only report has separate lanes for new symbols and unimplemented
sessions on existing symbols. It reuses completed integrated-SOR minute bars
and cannot issue or refresh tokens, access accounts, submit orders, create a
machine, or mutate runtime policy.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time as time_module
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib import parse, request

import requests

from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    CLEAN_BASELINE_DATE,
    COST_PCT,
    CALIBRATION_DAYS,
    HOLDOUT_DAYS,
    MAX_MANAGEABLE_HELD_LEG_RATE,
    MAX_MANAGEABLE_HELD_MARK_TO_MARKET_LOSS_PCT,
    OFFICIAL_REFERENCE,
    Bar,
    DayContext,
    ResearchError,
    SpotCandidate,
    _atomic_write,
    baseline_candidate,
    build_day_contexts,
    evaluate_candidate,
    fetch_sor_history,
    select_profile_spot,
)
from src.trading.low_price_two_leg.profiles import (
    PROFILES as LIVE_PROFILES,
    profiles_for_target_date,
)
from src.trading.low_price_two_leg.policy_runtime import load_applied_profile_policy
from src.trading.order.regular_two_leg_machine import KST
from src.utils import kiwoom_utils
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH, PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

REPORT_SCHEMA = "low_price_two_leg_expanded_candidate_research_v5"
REPORT_TYPE = "low_price_two_leg_expanded_candidate_research"
AUTHORITY = "lower_price_machine_candidate_recommendation_only"
OUTPUT_DIR = DATA_DIR / "report" / "low_price_two_leg_expanded_candidate_research"
DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "low_price_two_leg_candidate_telegram_state.json"
)
DEFAULT_DYNAMIC_UNIVERSE_PATH = DATA_DIR / "daily_recommendations_v2.csv"
DEFAULT_DYNAMIC_UNIVERSE_DIAGNOSTIC_PATH = (
    DATA_DIR / "daily_recommendations_v2_diagnostics.json"
)
MAX_DYNAMIC_SYMBOLS_PER_DAY = 5
MIN_RESEARCH_DAYS = CALIBRATION_DAYS + HOLDOUT_DAYS
MAX_RECOMMENDATIONS_PER_LANE = 3
MAX_LATEST_CLOSE_PRICE = 100_000
MORNING_WINDOW = (time(9, 10), time(9, 59))
LATE_MORNING_WINDOW = (time(10, 0), time(10, 59))
MIDDAY_WINDOW = (time(13, 15), time(13, 54))
AFTERNOON_WINDOW = (time(14, 0), time(14, 40))
SESSION_WINDOWS = {
    "morning": MORNING_WINDOW,
    "late_morning": LATE_MORNING_WINDOW,
    "midday": MIDDAY_WINDOW,
    "afternoon": AFTERNOON_WINDOW,
}
REVIEWED_SYMBOLS = {
    "006800": "미래에셋증권",
    "007660": "이수페타시스",
    "015760": "한국전력",
    "017670": "SK텔레콤",
    "028050": "삼성E&A",
    "034020": "두산에너빌리티",
    "035720": "카카오",
    "042660": "한화오션",
    "080220": "제주반도체",
    "475560": "더본코리아",
}
IMPLEMENTED_SYMBOLS = {
    profile.symbol: profile.name for profile in LIVE_PROFILES.values()
}
CANDIDATE_SYMBOLS = {
    symbol: name
    for symbol, name in REVIEWED_SYMBOLS.items()
    if symbol not in IMPLEMENTED_SYMBOLS
}
ACTIVE_SYMBOL_SESSIONS = frozenset(
    (profile.symbol, profile.session) for profile in LIVE_PROFILES.values()
)

METRIC_CONTRACT = {
    "metric_role": "lower_price_machine_candidate_recommendation",
    "decision_authority": AUTHORITY,
    "window_policy": (
        "clean_baseline_expanding_calibration_latest_16_trading_days_holdout"
    ),
    "sample_floor": {
        "calibration_signal_episodes": 6,
        "calibration_completed_legs": 8,
        "each_calibration_half_completed_legs": 3,
        "holdout_signal_episodes": 3,
        "holdout_completed_legs": 4,
        "full_window_completed_legs": 10,
    },
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "official_ka10080_success",
        "requested_start_date_fully_bracketed",
        "per_symbol_clean_baseline_trading_dates_complete_or_quarantined",
        "valid_unique_completed_sor_regular_ohlc",
        "bounded_carry_rate_and_mark_to_market_drawdown",
        "latest_close_at_or_below_100000_krw",
        "existing_symbol_lane_excludes_active_symbol_session_pairs",
        "target_date_counterfactual_requires_cumulative_holdout_selected_candidate",
        "target_date_candidate_only_signal_completed_target_and_zero_held_legs",
    ],
    "forbidden_uses": [
        "automatic_machine_implementation_or_service_start",
        "automatic_live_symbol_or_runtime_policy_promotion",
        "account_or_order_api",
        "real_order_submission",
        "token_issue_refresh_invalidation_or_replacement",
        "provider_bot_cap_threshold_or_broker_guard_change",
        "stop_loss_or_forced_exit_creation",
        "active_unrealized_merged_into_completed_ev",
        "risk_budget_diagnostic_as_standalone_live_authority",
        "single_target_date_near_miss_as_standalone_recommendation_authority",
    ],
}

Sender = Callable[[str, str, str], None]
ConfigLoader = Callable[[], tuple[str, str]]


@dataclass(frozen=True)
class ResearchPolicy:
    scan_start: time
    scan_last_bar: time
    lookback_bars: int = 30
    rolling_high_drawdown_pct: float = 1.25
    rolling_low_proximity_pct: float = 0.20
    entry_offsets_ticks: tuple[int, int] = (0, -1)
    entry_valid_completed_bars: int = 5
    target_ticks: int = 2


@dataclass(frozen=True)
class ResearchProfile:
    profile_id: str
    symbol: str
    name: str
    session: str
    policy: ResearchPolicy
    discovery_lane: str
    fixed_observation: bool = False


OPERATOR_OBSERVATION_PROFILE_SPECS = {
    "candidate_475560_morning": {
        "candidate_id": "theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1",
        "policy": ResearchPolicy(
            time(9, 40),
            time(9, 59),
            lookback_bars=20,
            rolling_high_drawdown_pct=0.50,
            rolling_low_proximity_pct=0.35,
            entry_offsets_ticks=(0, -1),
            entry_valid_completed_bars=5,
            target_ticks=4,
        ),
        "status": "source_only_keep_collecting",
    }
}


def _operator_observation_contract(profile: ResearchProfile) -> dict[str, Any] | None:
    spec = OPERATOR_OBSERVATION_PROFILE_SPECS.get(profile.profile_id)
    if not spec or not profile.fixed_observation:
        return None
    holdout_sample_floor = {
        "signal_episodes": METRIC_CONTRACT["sample_floor"]["holdout_signal_episodes"],
        "completed_legs": METRIC_CONTRACT["sample_floor"]["holdout_completed_legs"],
    }
    observation_metric_contract = {
        "metric_role": "fixed_episode_candidate_holdout_observation",
        "decision_authority": "source_only_observation_no_runtime_authority",
        "window_policy": (
            "clean_baseline_expanding_calibration_latest_16_trading_days_holdout"
        ),
        "sample_floor": holdout_sample_floor,
        "primary_decision_metric": "notional_weighted_ev_pct",
        "source_quality_gate": [
            "official_ka10080_success",
            "requested_start_date_fully_bracketed",
            "valid_unique_completed_sor_regular_ohlc",
            "fixed_policy_identity_match",
            "completed_legs_only_for_ev",
            "active_unrealized_separated_from_completed_ev",
        ],
        "missing_execution_evidence": [
            "prospective_fresh_bbo_spread",
            "passive_fill_feasibility",
            "spread_and_fee_adjusted_target_ev",
        ],
        "forbidden_uses": [
            "daily_policy_reoptimization",
            "automatic_machine_implementation_or_service_start",
            "automatic_runtime_or_preopen_policy_promotion",
            "minute_bar_holdout_pass_as_machine_recommendation_without_bbo_economics",
            "account_or_order_api",
            "real_order_submission",
            "provider_bot_cap_threshold_or_broker_guard_change",
            "stop_loss_or_forced_exit_creation",
            "thin_oos_or_diagnostic_win_rate_as_live_authority",
        ],
    }
    return {
        "candidate_id": spec["candidate_id"],
        "profile_id": profile.profile_id,
        "symbol": profile.symbol,
        "name": profile.name,
        "session": profile.session,
        "policy": baseline_candidate(profile).public(),
        "status": spec["status"],
        "holdout_sample_floor": holdout_sample_floor,
        "metric_contract": observation_metric_contract,
        "decision_authority": "source_only_observation_no_runtime_authority",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "machine_created": False,
        "service_started": False,
    }


def _operator_observation_inventory(
    profiles: dict[str, ResearchProfile],
) -> dict[str, dict[str, Any]]:
    return {
        profile_id: contract
        for profile_id, profile in profiles.items()
        if (contract := _operator_observation_contract(profile)) is not None
    }


def _new_symbol_profiles(
    candidate_symbols: dict[str, str] | None = None,
) -> dict[str, ResearchProfile]:
    result: dict[str, ResearchProfile] = {}
    selected_symbols = (
        CANDIDATE_SYMBOLS if candidate_symbols is None else candidate_symbols
    )
    for symbol, name in selected_symbols.items():
        for session, window in SESSION_WINDOWS.items():
            profile_id = f"candidate_{symbol}_{session}"
            observation_spec = OPERATOR_OBSERVATION_PROFILE_SPECS.get(profile_id)
            result[profile_id] = ResearchProfile(
                profile_id=profile_id,
                symbol=symbol,
                name=name,
                session=session,
                policy=(
                    observation_spec["policy"]
                    if observation_spec is not None
                    else ResearchPolicy(window[0], window[1])
                ),
                discovery_lane="new_symbol",
                fixed_observation=observation_spec is not None,
            )
    return result


def _dynamic_candidate_snapshot(
    target_date: date,
    *,
    path: Path = DEFAULT_DYNAMIC_UNIVERSE_PATH,
    diagnostic_path: Path | None = None,
    implemented_symbols: dict[str, str] | None = None,
) -> tuple[date | None, dict[str, str]]:
    selected_implemented_symbols = (
        IMPLEMENTED_SYMBOLS if implemented_symbols is None else implemented_symbols
    )
    completion_marker = diagnostic_path or path.with_name(
        DEFAULT_DYNAMIC_UNIVERSE_DIAGNOSTIC_PATH.name
    )
    try:
        diagnostic = json.loads(completion_marker.read_text(encoding="utf-8"))
        completed_source_date = date.fromisoformat(
            str(diagnostic.get("latest_date") or "")
        )
        completed_selected_count = int(diagnostic.get("selected_count", -1))
    except (OSError, ValueError, TypeError, AttributeError):
        return None, {}
    if (
        not (CLEAN_BASELINE_DATE <= completed_source_date <= target_date)
        or completed_selected_count < 0
    ):
        return None, {}
    try:
        handle = path.open(encoding="utf-8-sig", newline="")
    except OSError:
        return None, {}
    with handle:
        rows_by_date: dict[date, list[dict[str, str]]] = {}
        observed_row_count = 0
        date_contract_mismatch = False
        for raw_row in csv.DictReader(handle):
            observed_row_count += 1
            try:
                row_date = date.fromisoformat(str(raw_row.get("date") or ""))
            except ValueError:
                date_contract_mismatch = True
                continue
            if row_date == completed_source_date:
                rows_by_date.setdefault(row_date, []).append(raw_row)
            else:
                date_contract_mismatch = True
        if date_contract_mismatch or observed_row_count != completed_selected_count:
            return None, {}
        if not rows_by_date:
            return completed_source_date, {}
        source_date = completed_source_date
        ranked_by_symbol: dict[str, tuple[int, str, str]] = {}
        for row in rows_by_date[source_date]:
            raw_symbol = str(row.get("code") or "").strip()
            symbol = raw_symbol.zfill(6)
            name = str(row.get("name") or "").strip()
            try:
                close = int(float(row.get("close") or 0))
                rank = int(float(row.get("score_rank") or 999_999))
            except (TypeError, ValueError):
                continue
            if (
                not raw_symbol
                or len(symbol) != 6
                or not symbol.isdigit()
                or not name
                or not 0 < close <= MAX_LATEST_CLOSE_PRICE
                or symbol in REVIEWED_SYMBOLS
                or symbol in selected_implemented_symbols
            ):
                continue
            candidate = (rank, symbol, name)
            current = ranked_by_symbol.get(symbol)
            if current is None or candidate < current:
                ranked_by_symbol[symbol] = candidate
    return source_date, {
        symbol: name
        for _, symbol, name in sorted(ranked_by_symbol.values())[
            :MAX_DYNAMIC_SYMBOLS_PER_DAY
        ]
    }


def _dynamic_candidate_symbols(
    target_date: date,
    *,
    path: Path = DEFAULT_DYNAMIC_UNIVERSE_PATH,
    implemented_symbols: dict[str, str] | None = None,
) -> dict[str, str]:
    return _dynamic_candidate_snapshot(
        target_date,
        path=path,
        implemented_symbols=implemented_symbols,
    )[1]


def _research_inventory(
    candidate_symbols: dict[str, str],
    applied_policy_snapshots: dict[str, dict[str, Any]] | None = None,
    *,
    live_profiles: dict[str, Any] | None = None,
    implemented_symbols: dict[str, str] | None = None,
    active_symbol_sessions: frozenset[tuple[str, str]] | None = None,
) -> tuple[dict[str, ResearchProfile], dict[str, ResearchProfile]]:
    selected_live_profiles = LIVE_PROFILES if live_profiles is None else live_profiles
    selected_implemented_symbols = (
        IMPLEMENTED_SYMBOLS if implemented_symbols is None else implemented_symbols
    )
    selected_active_symbol_sessions = (
        ACTIVE_SYMBOL_SESSIONS
        if active_symbol_sessions is None
        else active_symbol_sessions
    )
    new_profiles = _new_symbol_profiles(candidate_symbols)
    return (
        new_profiles,
        {
            **new_profiles,
            **_existing_symbol_time_extension_profiles(
                implemented_symbols=selected_implemented_symbols,
                active_symbol_sessions=selected_active_symbol_sessions,
            ),
            **_existing_symbol_logic_improvement_profiles(
                applied_policy_snapshots=applied_policy_snapshots,
                live_profiles=selected_live_profiles,
            ),
        },
    )


def _existing_symbol_time_extension_profiles(
    *,
    implemented_symbols: dict[str, str] | None = None,
    active_symbol_sessions: frozenset[tuple[str, str]] | None = None,
) -> dict[str, ResearchProfile]:
    selected_implemented_symbols = (
        IMPLEMENTED_SYMBOLS if implemented_symbols is None else implemented_symbols
    )
    selected_active_symbol_sessions = (
        ACTIVE_SYMBOL_SESSIONS
        if active_symbol_sessions is None
        else active_symbol_sessions
    )
    result: dict[str, ResearchProfile] = {}
    for symbol, name in selected_implemented_symbols.items():
        for session, window in SESSION_WINDOWS.items():
            if (symbol, session) in selected_active_symbol_sessions:
                continue
            profile_id = f"existing_{symbol}_{session}"
            result[profile_id] = ResearchProfile(
                profile_id=profile_id,
                symbol=symbol,
                name=name,
                session=session,
                policy=ResearchPolicy(window[0], window[1]),
                discovery_lane="existing_symbol_time_extension",
            )
    return result


def _existing_symbol_logic_improvement_profiles(
    *,
    applied_policy_snapshots: dict[str, dict[str, Any]] | None = None,
    live_profiles: dict[str, Any] | None = None,
) -> dict[str, ResearchProfile]:
    selected_live_profiles = LIVE_PROFILES if live_profiles is None else live_profiles
    result: dict[str, ResearchProfile] = {}
    for live_profile_id, live_profile in selected_live_profiles.items():
        policy = live_profile.policy
        snapshot = (applied_policy_snapshots or {}).get(live_profile_id) or {}
        applied = snapshot.get("policy")
        use_applied = snapshot.get("status") == "ready" and isinstance(applied, dict)
        profile_id = f"logic_{live_profile_id}"
        result[profile_id] = ResearchProfile(
            profile_id=profile_id,
            symbol=live_profile.symbol,
            name=live_profile.name,
            session=live_profile.session,
            policy=ResearchPolicy(
                policy.scan_start,
                policy.scan_last_bar,
                lookback_bars=(
                    int(applied["lookback_bars"])
                    if use_applied
                    else policy.lookback_bars
                ),
                rolling_high_drawdown_pct=(
                    float(applied["rolling_high_drawdown_pct"])
                    if use_applied
                    else policy.rolling_high_drawdown_pct
                ),
                rolling_low_proximity_pct=(
                    float(applied["rolling_low_proximity_pct"])
                    if use_applied
                    else policy.rolling_low_proximity_pct
                ),
                entry_offsets_ticks=tuple(policy.entry_offsets_ticks),
                entry_valid_completed_bars=(
                    int(applied["entry_valid_completed_bars"])
                    if use_applied
                    else policy.entry_valid_completed_bars
                ),
                target_ticks=(
                    int(applied["target_ticks"]) if use_applied else policy.target_ticks
                ),
            ),
            discovery_lane="existing_symbol_logic_improvement",
        )
    return result


@dataclass(frozen=True)
class TargetDateResearchInventory:
    live_profiles: dict[str, Any]
    implemented_symbols: dict[str, str]
    candidate_symbols: dict[str, str]
    active_symbol_sessions: frozenset[tuple[str, str]]
    new_symbol_profiles: dict[str, ResearchProfile]
    time_extension_profiles: dict[str, ResearchProfile]
    logic_improvement_profiles: dict[str, ResearchProfile]
    research_profiles: dict[str, ResearchProfile]
    research_symbols: frozenset[str]


def _target_date_research_inventory(
    target_date: date,
    *,
    candidate_symbols: dict[str, str] | None = None,
    applied_policy_snapshots: dict[str, dict[str, Any]] | None = None,
) -> TargetDateResearchInventory:
    """Reconstruct the profile catalog that was effective on ``target_date``."""

    live_profiles = profiles_for_target_date(target_date)
    implemented_symbols = {
        profile.symbol: profile.name for profile in live_profiles.values()
    }
    base_candidate_symbols = {
        symbol: name
        for symbol, name in REVIEWED_SYMBOLS.items()
        if symbol not in implemented_symbols
    }
    selected_candidate_symbols = (
        base_candidate_symbols if candidate_symbols is None else dict(candidate_symbols)
    )
    active_symbol_sessions = frozenset(
        (profile.symbol, profile.session) for profile in live_profiles.values()
    )
    new_symbol_profiles = _new_symbol_profiles(selected_candidate_symbols)
    time_extension_profiles = _existing_symbol_time_extension_profiles(
        implemented_symbols=implemented_symbols,
        active_symbol_sessions=active_symbol_sessions,
    )
    logic_improvement_profiles = _existing_symbol_logic_improvement_profiles(
        applied_policy_snapshots=applied_policy_snapshots,
        live_profiles=live_profiles,
    )
    research_profiles = {
        **new_symbol_profiles,
        **time_extension_profiles,
        **logic_improvement_profiles,
    }
    return TargetDateResearchInventory(
        live_profiles=live_profiles,
        implemented_symbols=implemented_symbols,
        candidate_symbols=selected_candidate_symbols,
        active_symbol_sessions=active_symbol_sessions,
        new_symbol_profiles=new_symbol_profiles,
        time_extension_profiles=time_extension_profiles,
        logic_improvement_profiles=logic_improvement_profiles,
        research_profiles=research_profiles,
        research_symbols=frozenset(selected_candidate_symbols)
        | frozenset(implemented_symbols),
    )


def _research_profile_inventory_public(
    profiles: dict[str, ResearchProfile],
) -> dict[str, dict[str, Any]]:
    return {
        profile_id: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "discovery_lane": profile.discovery_lane,
            "fixed_observation": profile.fixed_observation,
        }
        for profile_id, profile in profiles.items()
    }


NEW_SYMBOL_PROFILES = _new_symbol_profiles()
EXISTING_SYMBOL_TIME_EXTENSION_PROFILES = _existing_symbol_time_extension_profiles()
EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES = (
    _existing_symbol_logic_improvement_profiles()
)
RESEARCH_PROFILES = {
    **NEW_SYMBOL_PROFILES,
    **EXISTING_SYMBOL_TIME_EXTENSION_PROFILES,
    **EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES,
}
RESEARCH_SYMBOLS = frozenset(CANDIDATE_SYMBOLS) | frozenset(IMPLEMENTED_SYMBOLS)


def clean_baseline_trading_dates(end_date: date) -> tuple[date, ...]:
    if not is_krx_trading_day(end_date):
        raise ValueError(f"target_date_not_krx_trading_day:{end_date}")
    selected: list[date] = []
    current = CLEAN_BASELINE_DATE
    while current <= end_date:
        if is_krx_trading_day(current):
            selected.append(current)
        current += timedelta(days=1)
    if len(selected) < MIN_RESEARCH_DAYS:
        raise ValueError("clean_baseline_window_below_research_minimum")
    return tuple(selected)


def _previous_krx_trading_date(value: date) -> date:
    current = value - timedelta(days=1)
    while not is_krx_trading_day(current):
        current -= timedelta(days=1)
    return current


def _default_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if is_krx_trading_day(current.date()) and current.time().replace(
        tzinfo=None
    ) >= time(15, 30):
        return current.date()
    return _previous_krx_trading_date(current.date())


def _price_band(latest_close_price: int) -> str:
    if latest_close_price <= 50_000:
        return "under_50000_krw"
    if latest_close_price <= MAX_LATEST_CLOSE_PRICE:
        return "50000_to_100000_krw"
    return "above_100000_krw_excluded"


def _recommendation_rows(
    profiles: dict[str, dict[str, Any]],
    source_meta: dict[str, dict[str, Any]],
    *,
    research_profiles: dict[str, ResearchProfile] | None = None,
    live_profiles: dict[str, Any] | None = None,
    active_symbol_sessions: frozenset[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    profile_inventory = (
        RESEARCH_PROFILES if research_profiles is None else research_profiles
    )
    selected_live_profiles = LIVE_PROFILES if live_profiles is None else live_profiles
    selected_active_symbol_sessions = (
        ACTIVE_SYMBOL_SESSIONS
        if active_symbol_sessions is None
        else active_symbol_sessions
    )
    rows: list[dict[str, Any]] = []
    for profile_id, item in profiles.items():
        if item.get("decision") != "holdout_pass_source_only_early_candidate":
            continue
        profile = profile_inventory.get(profile_id)
        if profile is None:
            raise ResearchError("recommendation_profile_contract_unknown")
        if profile.fixed_observation:
            # Fixed operator observations accumulate one immutable policy only.
            # Even after their holdout floor matures, they must not enter the
            # generic implementation-recommendation or notifier path.
            continue
        if (
            item.get("symbol") != profile.symbol
            or item.get("name") != profile.name
            or item.get("session") != profile.session
        ):
            raise ResearchError("recommendation_profile_identity_mismatch")
        if (
            profile.discovery_lane == "existing_symbol_time_extension"
            and (profile.symbol, profile.session) in selected_active_symbol_sessions
        ):
            raise ResearchError("existing_symbol_lane_active_session_conflict")
        if profile.discovery_lane == "existing_symbol_logic_improvement" and (
            item.get("baseline_policy_source") != "target_date_applied_policy"
            or not item.get("baseline_policy_hash")
        ):
            continue
        meta = source_meta.get(str(item.get("symbol") or ""), {})
        latest_close = int(meta.get("latest_close_price", 0) or 0)
        if latest_close <= 0 or latest_close > MAX_LATEST_CLOSE_PRICE:
            continue
        holdout = (item.get("selected") or {}).get("holdout") or {}
        baseline_holdout = (item.get("baseline") or {}).get("holdout") or {}
        candidate_ev = float(holdout.get("notional_weighted_ev_pct") or 0.0)
        held_rate = float(holdout.get("held_leg_rate_per_filled_leg", 0.0) or 0.0)
        held_mark = holdout.get("active_unrealized_notional_weighted_pct")
        if not 0.0 <= held_rate <= MAX_MANAGEABLE_HELD_LEG_RATE or (
            held_mark is not None
            and float(held_mark) < -MAX_MANAGEABLE_HELD_MARK_TO_MARKET_LOSS_PCT
        ):
            continue
        baseline_ev_raw = baseline_holdout.get("notional_weighted_ev_pct")
        baseline_ev = float(baseline_ev_raw) if baseline_ev_raw is not None else None
        rows.append(
            {
                "profile_id": profile_id,
                "symbol": item["symbol"],
                "name": item["name"],
                "session": item["session"],
                "discovery_lane": profile.discovery_lane,
                "active_profile_ids_for_symbol": sorted(
                    live_profile_id
                    for live_profile_id, live_profile in selected_live_profiles.items()
                    if live_profile.symbol == profile.symbol
                ),
                "latest_close_price": latest_close,
                "price_band": _price_band(latest_close),
                "recommended_spot": item["recommended_spot"],
                "holdout_signal_episodes": int(holdout.get("signal_episodes", 0) or 0),
                "holdout_completed_legs": int(holdout.get("completed_legs", 0) or 0),
                "holdout_held_legs": int(holdout.get("held_legs", 0) or 0),
                "holdout_held_leg_rate_per_filled_leg": held_rate,
                "holdout_active_unrealized_notional_weighted_pct": holdout.get(
                    "active_unrealized_notional_weighted_pct"
                ),
                "holdout_worst_filled_max_adverse_excursion_pct": holdout.get(
                    "worst_filled_max_adverse_excursion_pct"
                ),
                "holdout_realized_net_profit_krw_per_episode": holdout.get(
                    "realized_net_profit_krw_per_episode"
                ),
                "notional_weighted_ev_pct": candidate_ev,
                "baseline_notional_weighted_ev_pct": baseline_ev,
                "baseline_policy_source": item.get("baseline_policy_source"),
                "baseline_policy_hash": item.get("baseline_policy_hash"),
                "ev_uplift_pct_point": (
                    round(candidate_ev - baseline_ev, 6)
                    if baseline_ev is not None
                    else None
                ),
                "implementation_status": "source_only_requires_review_and_user_approval",
                "runtime_effect": False,
            }
        )
    rows.sort(
        key=lambda row: (
            float(row["notional_weighted_ev_pct"]),
            float(row.get("holdout_realized_net_profit_krw_per_episode") or 0.0),
            -float(row["holdout_held_leg_rate_per_filled_leg"]),
            int(row["holdout_completed_legs"]),
            -int(row["latest_close_price"]),
        ),
        reverse=True,
    )
    return rows


def _spot_candidate_from_public(parameters: dict[str, Any]) -> SpotCandidate:
    try:
        start = datetime.strptime(str(parameters["scan_start"]), "%H:%M").time()
        end = datetime.strptime(str(parameters["scan_end"]), "%H:%M").time()
        offsets = tuple(int(value) for value in parameters["entry_offsets_ticks"])
        if len(offsets) != 2:
            raise ValueError("invalid_offsets")
        return SpotCandidate(
            start.hour * 60 + start.minute,
            end.hour * 60 + end.minute,
            int(parameters["lookback_bars"]),
            float(parameters["rolling_high_drawdown_pct"]),
            float(parameters["rolling_low_proximity_pct"]),
            offsets,
            int(parameters["entry_valid_completed_bars"]),
            int(parameters["target_ticks"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ResearchError("logic_recommendation_parameters_invalid") from exc


def _target_date_logic_attribution(
    *,
    profiles: dict[str, dict[str, Any]],
    contexts_by_symbol: dict[str, dict[date, DayContext]],
    target_date: date,
    applied_policy_snapshots: dict[str, dict[str, Any]],
    logic_improvement_profiles: dict[str, ResearchProfile] | None = None,
    live_profiles: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Attribute cumulative logic candidates on the latest untouched day only."""

    selected_logic_profiles = (
        EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES
        if logic_improvement_profiles is None
        else logic_improvement_profiles
    )
    selected_live_profiles = LIVE_PROFILES if live_profiles is None else live_profiles
    rows: list[dict[str, Any]] = []
    for profile_id, research_profile in sorted(selected_logic_profiles.items()):
        item = profiles.get(profile_id) or {}
        context = (contexts_by_symbol.get(research_profile.symbol) or {}).get(
            target_date
        )
        row: dict[str, Any] = {
            "profile_id": profile_id,
            "active_profile_id": profile_id.removeprefix("logic_"),
            "symbol": research_profile.symbol,
            "name": research_profile.name,
            "session": research_profile.session,
            "cumulative_decision": item.get("decision"),
            "decision": "not_recommended",
            "reason": "cumulative_holdout_candidate_unavailable",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        policy_snapshot = applied_policy_snapshots.get(row["active_profile_id"]) or {}
        row["applied_policy_status"] = policy_snapshot.get("status")
        row["applied_policy_reason"] = policy_snapshot.get("reason")
        row["applied_policy_hash"] = policy_snapshot.get("policy_hash")
        if not isinstance(context, DayContext):
            row["reason"] = "target_date_context_unavailable"
            rows.append(row)
            continue
        if item.get("decision") != "holdout_pass_source_only_early_candidate":
            rows.append(row)
            continue
        applied_policy = policy_snapshot.get("policy")
        if policy_snapshot.get("status") != "ready" or not isinstance(
            applied_policy, dict
        ):
            row["reason"] = "target_date_applied_policy_unavailable"
            rows.append(row)
            continue
        parameters = item.get("recommended_spot")
        if not isinstance(parameters, dict):
            raise ResearchError("logic_recommendation_parameters_missing")
        live_profile = selected_live_profiles[row["active_profile_id"]]
        compiled_baseline = baseline_candidate(live_profile)
        try:
            baseline = SpotCandidate(
                compiled_baseline.scan_start_minute,
                compiled_baseline.scan_end_minute,
                int(applied_policy["lookback_bars"]),
                float(applied_policy["rolling_high_drawdown_pct"]),
                float(applied_policy["rolling_low_proximity_pct"]),
                compiled_baseline.entry_offsets_ticks,
                int(applied_policy["entry_valid_completed_bars"]),
                int(applied_policy["target_ticks"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ResearchError("target_date_applied_policy_invalid") from exc
        candidate = _spot_candidate_from_public(parameters)
        contexts = {target_date: context}
        baseline_result = evaluate_candidate(
            baseline, contexts, [target_date], include_episodes=True
        )
        candidate_result = evaluate_candidate(
            candidate, contexts, [target_date], include_episodes=True
        )
        row.update(
            {
                "baseline_parameters": baseline.public(),
                "candidate_parameters": candidate.public(),
                "baseline_target_date": baseline_result,
                "candidate_target_date": candidate_result,
            }
        )
        candidate_only_signal = bool(
            baseline_result["signal_episodes"] == 0
            and candidate_result["signal_episodes"] == 1
        )
        completed_rebound = bool(
            candidate_result["completed_legs"] >= 1
            and candidate_result["held_legs"] == 0
            and candidate_result["notional_weighted_ev_pct"] is not None
            and float(candidate_result["notional_weighted_ev_pct"]) > 0.0
        )
        if candidate_only_signal and completed_rebound:
            row.update(
                {
                    "decision": "recommend_cumulative_logic_candidate_review",
                    "reason": (
                        "cumulative_holdout_pass_and_target_date_candidate_only_"
                        "completed_rebound"
                    ),
                }
            )
        elif not candidate_only_signal:
            row["reason"] = "target_date_not_candidate_only_signal"
        else:
            row["reason"] = "target_date_rebound_or_carry_gate_failed"
        rows.append(row)
    return rows


def build_report(
    *,
    sources: dict[str, tuple[list[Bar], dict[str, Any]]],
    start_date: date,
    end_date: date,
    candidate_symbols: dict[str, str] | None = None,
    research_profiles: dict[str, ResearchProfile] | None = None,
    dynamic_universe_source_date: date | None = None,
    applied_policy_snapshots: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if start_date != CLEAN_BASELINE_DATE or end_date < start_date:
        raise ValueError("research_window_must_start_at_clean_baseline")
    expected_dates = clean_baseline_trading_dates(end_date)
    calibration_days = len(expected_dates) - HOLDOUT_DAYS
    target_inventory = _target_date_research_inventory(
        end_date,
        candidate_symbols=candidate_symbols,
        applied_policy_snapshots=applied_policy_snapshots,
    )
    selected_candidate_symbols = target_inventory.candidate_symbols
    selected_profiles = (
        target_inventory.research_profiles
        if research_profiles is None
        else research_profiles
    )
    if selected_profiles != target_inventory.research_profiles:
        raise ResearchError("research_profile_target_date_inventory_mismatch")
    selected_symbols = target_inventory.research_symbols
    if set(sources) - set(selected_symbols):
        raise ResearchError("expanded_candidate_source_set_mismatch")
    conflicting_profiles = [
        profile.profile_id
        for profile in selected_profiles.values()
        if profile.discovery_lane != "existing_symbol_logic_improvement"
        and (profile.symbol, profile.session) in target_inventory.active_symbol_sessions
    ]
    if conflicting_profiles:
        raise ResearchError(
            "research_profile_active_symbol_session_conflict:"
            + ",".join(sorted(conflicting_profiles))
        )
    contexts_by_symbol: dict[str, dict[date, DayContext]] = {}
    source_meta: dict[str, dict[str, Any]] = {}
    source_quarantine: dict[str, str] = {}
    for symbol in selected_symbols:
        source = sources.get(symbol)
        if source is None:
            source_quarantine[symbol] = "source_missing"
            continue
        bars, raw_meta = source
        if not bars or raw_meta.get("source_quality_status") != "PASS":
            source_quarantine[symbol] = "source_quality_not_pass"
            continue
        contexts = build_day_contexts(bars)
        if tuple(sorted(contexts)) != expected_dates:
            source_quarantine[symbol] = "clean_baseline_trading_date_window_mismatch"
            continue
        contexts_by_symbol[symbol] = contexts
        meta = dict(raw_meta)
        meta["latest_close_price"] = int(bars[-1].close_price)
        meta["latest_price_band"] = _price_band(int(bars[-1].close_price))
        source_meta[symbol] = meta
    if not contexts_by_symbol:
        raise ResearchError("all_research_symbols_source_quality_blocked")
    profiles: dict[str, dict[str, Any]] = {}
    for profile_id, profile in selected_profiles.items():
        observation_contract = _operator_observation_contract(profile)
        if profile.symbol not in contexts_by_symbol:
            profiles[profile_id] = {
                "profile_id": profile.profile_id,
                "symbol": profile.symbol,
                "name": profile.name,
                "session": profile.session,
                "discovery_lane": profile.discovery_lane,
                "decision": "source_quality_quarantined_no_evaluation",
                "recommended_spot": None,
                "source_quality_reason": source_quarantine.get(
                    profile.symbol, "source_unavailable"
                ),
                "observation_candidate": observation_contract,
                "runtime_effect": False,
            }
            continue
        selected = select_profile_spot(
            profile,
            contexts_by_symbol[profile.symbol],
            calibration_days=calibration_days,
            holdout_days=HOLDOUT_DAYS,
        )
        selected["discovery_lane"] = profile.discovery_lane
        selected["active_profile_ids_for_symbol"] = sorted(
            live_profile_id
            for live_profile_id, live_profile in target_inventory.live_profiles.items()
            if live_profile.symbol == profile.symbol
        )
        selected["active_symbol_session_conflict"] = (
            profile.symbol,
            profile.session,
        ) in target_inventory.active_symbol_sessions
        selected["observation_candidate"] = observation_contract
        if profile.discovery_lane == "existing_symbol_logic_improvement":
            active_profile_id = profile.profile_id.removeprefix("logic_")
            policy_snapshot = (applied_policy_snapshots or {}).get(
                active_profile_id
            ) or {}
            selected["baseline_policy_source"] = (
                "target_date_applied_policy"
                if policy_snapshot.get("status") == "ready"
                else "compiled_profile_baseline_not_recommendable"
            )
            selected["baseline_policy_hash"] = policy_snapshot.get("policy_hash")
            selected["baseline_policy_reason"] = policy_snapshot.get("reason")
        profiles[profile_id] = selected
    recommendations = _recommendation_rows(
        profiles,
        source_meta,
        research_profiles=selected_profiles,
        live_profiles=target_inventory.live_profiles,
        active_symbol_sessions=target_inventory.active_symbol_sessions,
    )
    new_symbol_recommendations = [
        row for row in recommendations if row["discovery_lane"] == "new_symbol"
    ]
    existing_symbol_time_extension_recommendations = [
        row
        for row in recommendations
        if row["discovery_lane"] == "existing_symbol_time_extension"
    ]
    existing_symbol_logic_improvement_recommendations = [
        row
        for row in recommendations
        if row["discovery_lane"] == "existing_symbol_logic_improvement"
    ]
    target_date_logic_attribution = _target_date_logic_attribution(
        profiles=profiles,
        contexts_by_symbol=contexts_by_symbol,
        target_date=end_date,
        applied_policy_snapshots=applied_policy_snapshots or {},
        logic_improvement_profiles=target_inventory.logic_improvement_profiles,
        live_profiles=target_inventory.live_profiles,
    )
    cumulative_logic_ids = {
        row["profile_id"] for row in existing_symbol_logic_improvement_recommendations
    }
    postclose_logic_recommendations = [
        row
        for row in target_date_logic_attribution
        if row["decision"] == "recommend_cumulative_logic_candidate_review"
        and row["profile_id"] in cumulative_logic_ids
    ]
    return {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "target_date": end_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trading_date_count": len(expected_dates),
        "calibration_trading_day_count": calibration_days,
        "holdout_trading_day_count": HOLDOUT_DAYS,
        "cost_pct": COST_PCT,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "candidate_universe_source": (
            "reviewed_new_symbols_plus_latest_completed_daily_recommendations_"
            "and_existing_symbol_missing_sessions_and_logic_v5"
        ),
        "dynamic_universe_source_date": (
            dynamic_universe_source_date.isoformat()
            if dynamic_universe_source_date is not None
            else None
        ),
        "candidate_universe_size": len(selected_candidate_symbols),
        "candidate_symbols": selected_candidate_symbols,
        "existing_symbol_universe_size": len(target_inventory.implemented_symbols),
        "source_symbol_count": len(selected_symbols),
        "new_symbol_profile_count": len(target_inventory.new_symbol_profiles),
        "existing_symbol_time_extension_profile_count": len(
            target_inventory.time_extension_profiles
        ),
        "existing_symbol_logic_improvement_profile_count": len(
            target_inventory.logic_improvement_profiles
        ),
        "eligible_source_symbol_count": len(contexts_by_symbol),
        "quarantined_source_symbol_count": len(source_quarantine),
        "source_quarantine": source_quarantine,
        "research_profile_inventory": _research_profile_inventory_public(
            selected_profiles
        ),
        "operator_observation_candidate_count": len(
            _operator_observation_inventory(selected_profiles)
        ),
        "operator_observation_candidate_inventory": (
            _operator_observation_inventory(selected_profiles)
        ),
        "source_meta": source_meta,
        "profiles": profiles,
        "recommendations": recommendations,
        "recommendation_count": len(recommendations),
        "new_symbol_recommendations": new_symbol_recommendations,
        "new_symbol_recommendation_count": len(new_symbol_recommendations),
        "existing_symbol_time_extension_recommendations": (
            existing_symbol_time_extension_recommendations
        ),
        "existing_symbol_time_extension_recommendation_count": len(
            existing_symbol_time_extension_recommendations
        ),
        "existing_symbol_logic_improvement_recommendations": (
            existing_symbol_logic_improvement_recommendations
        ),
        "existing_symbol_logic_improvement_recommendation_count": len(
            existing_symbol_logic_improvement_recommendations
        ),
        "target_date_logic_attribution": target_date_logic_attribution,
        "target_date_logic_attribution_count": len(target_date_logic_attribution),
        "postclose_logic_recommendations": postclose_logic_recommendations,
        "postclose_logic_recommendation_count": len(postclose_logic_recommendations),
        "status": (
            "recommendations_ready"
            if recommendations
            else (
                "partial_source_quality"
                if source_quarantine
                else "no_qualified_candidate"
            )
        ),
        "decision": "expanded_candidates_source_only_no_runtime_promotion",
        "authority": AUTHORITY,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_source_quality_blocked_report(
    *, start_date: date, end_date: date, reason: str
) -> dict[str, Any]:
    if start_date != CLEAN_BASELINE_DATE or end_date < start_date:
        raise ValueError("research_window_must_start_at_clean_baseline")
    expected_dates = clean_baseline_trading_dates(end_date)
    target_inventory = _target_date_research_inventory(end_date)
    return {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "target_date": end_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trading_date_count": len(expected_dates),
        "calibration_trading_day_count": len(expected_dates) - HOLDOUT_DAYS,
        "holdout_trading_day_count": HOLDOUT_DAYS,
        "cost_pct": COST_PCT,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "candidate_universe_source": (
            "reviewed_new_symbols_plus_latest_completed_daily_recommendations_"
            "and_existing_symbol_missing_sessions_and_logic_v5"
        ),
        "dynamic_universe_source_date": None,
        "candidate_universe_size": len(target_inventory.candidate_symbols),
        "candidate_symbols": target_inventory.candidate_symbols,
        "existing_symbol_universe_size": len(target_inventory.implemented_symbols),
        "source_symbol_count": len(target_inventory.research_symbols),
        "new_symbol_profile_count": len(target_inventory.new_symbol_profiles),
        "existing_symbol_time_extension_profile_count": len(
            target_inventory.time_extension_profiles
        ),
        "existing_symbol_logic_improvement_profile_count": len(
            target_inventory.logic_improvement_profiles
        ),
        "eligible_source_symbol_count": 0,
        "quarantined_source_symbol_count": len(target_inventory.research_symbols),
        "source_quarantine": {
            symbol: str(reason) for symbol in sorted(target_inventory.research_symbols)
        },
        "research_profile_inventory": _research_profile_inventory_public(
            target_inventory.research_profiles
        ),
        "operator_observation_candidate_count": len(
            _operator_observation_inventory(target_inventory.research_profiles)
        ),
        "operator_observation_candidate_inventory": (
            _operator_observation_inventory(target_inventory.research_profiles)
        ),
        "source_meta": {},
        "profiles": {},
        "recommendations": [],
        "recommendation_count": 0,
        "new_symbol_recommendations": [],
        "new_symbol_recommendation_count": 0,
        "existing_symbol_time_extension_recommendations": [],
        "existing_symbol_time_extension_recommendation_count": 0,
        "existing_symbol_logic_improvement_recommendations": [],
        "existing_symbol_logic_improvement_recommendation_count": 0,
        "target_date_logic_attribution": [],
        "target_date_logic_attribution_count": 0,
        "postclose_logic_recommendations": [],
        "postclose_logic_recommendation_count": 0,
        "status": "source_quality_blocked",
        "source_quality_reasons": [str(reason)],
        "decision": "source_quality_blocked_no_recommendation",
        "authority": AUTHORITY,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Expanded lower-price entry-spot research — {report['end_date']}",
        "",
        (
            "Source-only clean-baseline expanding calibration / latest 16-day "
            "holdout. No machine or live session was added."
        ),
        "",
        (
            f"Window: `{report['start_date']}~{report['end_date']}`; "
            f"trading dates `{report['trading_date_count']}`; calibration "
            f"`{report['calibration_trading_day_count']}`; holdout "
            f"`{report['holdout_trading_day_count']}`."
        ),
        "",
        f"Recommendation status: `{report['status']}`; profiles: `{report['recommendation_count']}`.",
        "",
    ]
    if report["status"] == "source_quality_blocked":
        lines.extend(
            [
                "Source quality blocked recommendation generation:",
                *[f"- `{reason}`" for reason in report["source_quality_reasons"]],
                "",
            ]
        )
    elif report.get("source_quarantine"):
        lines.extend(
            [
                "Quarantined source symbols:",
                *[
                    f"- `{symbol}`: `{reason}`"
                    for symbol, reason in sorted(
                        report.get("source_quarantine", {}).items()
                    )
                ],
                "",
            ]
        )
    lines.extend(["## Operator source-only observation candidates", ""])
    observation_inventory = report.get("operator_observation_candidate_inventory") or {}
    if not observation_inventory:
        lines.append("No fixed operator observation candidate.")
    for profile_id, contract in observation_inventory.items():
        profile_result = (report.get("profiles") or {}).get(profile_id) or {}
        if (
            report.get("status") == "source_quality_blocked"
            or profile_result.get("decision")
            == "source_quality_quarantined_no_evaluation"
        ):
            lines.append(
                f"- `{contract['candidate_id']}`: observation input "
                "source-quality blocked; no zero-signal inference."
            )
            continue
        holdout = (profile_result.get("baseline") or {}).get("holdout") or {}
        floor = contract["holdout_sample_floor"]
        lines.append(
            f"- `{contract['candidate_id']}`: `{contract['name']}` "
            f"`{contract['session']}`; OOS episodes "
            f"`{holdout.get('signal_episodes', 0)}/{floor['signal_episodes']}`; "
            f"completed legs `{holdout.get('completed_legs', 0)}/"
            f"{floor['completed_legs']}`; source-only, no runtime/order authority."
        )
    lines.append("")
    lines.extend(
        [
            "| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |",
            "|---|---|---|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["profiles"].values():
        if item.get("decision") == "source_quality_quarantined_no_evaluation":
            lines.append(
                f"| {item['discovery_lane']} | {item['symbol']} | "
                f"{item['name']} | {item['session']} | "
                f"{item['decision']}:{item['source_quality_reason']} | N/A | "
                "0 | 0 | 0 | N/A | N/A |"
            )
            continue
        recommended = item["recommended_spot"]
        if recommended is None:
            spot = "N/A"
            holdout = item["baseline"]["holdout"]
            candidate_ev = None
        else:
            spot = (
                f"{recommended['scan_start']}~{recommended['scan_end']}; "
                f"L{recommended['lookback_bars']}; "
                f"DD{recommended['rolling_high_drawdown_pct']}; "
                f"NL{recommended['rolling_low_proximity_pct']}"
            )
            holdout = item["selected"]["holdout"]
            candidate_ev = holdout["notional_weighted_ev_pct"]
        baseline_ev = item["baseline"]["holdout"]["notional_weighted_ev_pct"]
        lines.append(
            f"| {item['discovery_lane']} | {item['symbol']} | "
            f"{item['name']} | {item['session']} | "
            f"{item['decision']} | {spot} | {holdout['signal_episodes']} | "
            f"{holdout['completed_legs']} | {holdout['held_legs']} | "
            f"{candidate_ev} | {baseline_ev} |"
        )
    lines.extend(["", "## Target-date cumulative logic attribution", ""])
    postclose_rows = report.get("postclose_logic_recommendations") or []
    if not postclose_rows:
        lines.append(
            "No cumulative holdout candidate added a completed target-date rebound."
        )
    for row in postclose_rows:
        outcome = row["candidate_target_date"]
        episode = outcome["episodes"][0]
        lines.append(
            f"- `{row['active_profile_id']}`: candidate-only signal "
            f"`{episode['signal_at']}`; completed `{outcome['completed_legs']}` leg; "
            f"held `{outcome['held_legs']}`; EV "
            f"`{outcome['notional_weighted_ev_pct']}`%."
        )
    lines.extend(
        [
            "",
            "Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.",
            "",
        ]
    )
    return "\n".join(lines)


def build_telegram_message(report: dict[str, Any]) -> str:
    recommendations = list(report.get("recommendations") or [])
    unique_symbols = {str(row.get("symbol") or "") for row in recommendations}
    lines = [
        f"[장후 기계후보 추천] {report['target_date']}",
        (
            f"분석기간: {report['start_date']}~{report['end_date']} "
            f"(clean baseline 전체 {report['trading_date_count']}일 / "
            f"보정 {report['calibration_trading_day_count']}일 + OOS "
            f"{report['holdout_trading_day_count']}일)"
        ),
        (
            "동적 후보 원천일: "
            f"{report.get('dynamic_universe_source_date') or '사용 가능한 완료 스냅샷 없음'}"
        ),
        (
            f"신규후보 {report['candidate_universe_size']}종목 + 기존종목 "
            f"미구현시간대 {report['existing_symbol_time_extension_profile_count']}프로필 + "
            f"로직개선 {report['existing_symbol_logic_improvement_profile_count']}프로필 "
            f"/ 통과 {len(recommendations)}프로필·{len(unique_symbols)}종목"
        ),
    ]
    if report["status"] == "source_quality_blocked":
        reasons = ", ".join(str(item) for item in report["source_quality_reasons"])
        lines.append(f"분석 차단: {reasons}")
        lines.append("오늘은 source-quality 문제로 신규 추천을 산출하지 않았습니다.")
    elif report.get("source_quarantine"):
        lines.append(
            "일부 종목 격리: "
            + ", ".join(
                f"{symbol}({reason})"
                for symbol, reason in sorted(report["source_quarantine"].items())
            )
        )
    elif not recommendations:
        lines.append("오늘 신규 구현 추천 기준을 통과한 종목·시간대가 없습니다.")
    observation_inventory = report.get("operator_observation_candidate_inventory") or {}
    if observation_inventory:
        lines.append("[고정 누적 관찰]")
        for profile_id, contract in observation_inventory.items():
            profile_result = (report.get("profiles") or {}).get(profile_id) or {}
            if (
                report.get("status") == "source_quality_blocked"
                or profile_result.get("decision")
                == "source_quality_quarantined_no_evaluation"
            ):
                lines.append(
                    f"- {contract['name']}({contract['symbol']}) "
                    f"{contract['session']} 관찰 입력 차단(source-quality)"
                )
                continue
            holdout = (profile_result.get("baseline") or {}).get("holdout") or {}
            floor = contract["holdout_sample_floor"]
            lines.append(
                f"- {contract['name']}({contract['symbol']}) {contract['session']} "
                f"OOS {holdout.get('signal_episodes', 0)}/"
                f"{floor['signal_episodes']}회·완료 "
                f"{holdout.get('completed_legs', 0)}/"
                f"{floor['completed_legs']}leg (source-only)"
            )
    lane_sections = (
        ("신규 종목", report["new_symbol_recommendations"]),
        (
            "기존 종목·신규 시간대",
            report["existing_symbol_time_extension_recommendations"],
        ),
        (
            "기존 종목·로직 개선",
            report["existing_symbol_logic_improvement_recommendations"],
        ),
    )
    for lane_label, lane_rows in lane_sections:
        if not lane_rows:
            continue
        lines.append(f"[{lane_label}]")
        for index, row in enumerate(lane_rows[:MAX_RECOMMENDATIONS_PER_LANE], start=1):
            spot = row["recommended_spot"]
            band = (
                "5만원 이하"
                if row["price_band"] == "under_50000_krw"
                else "10만원 이하"
            )
            lines.extend(
                [
                    (
                        f"{index}. {row['name']}({row['symbol']}) {row['session']} "
                        f"{spot['scan_start']}~{spot['scan_end']}"
                    ),
                    (
                        f"   종가 {row['latest_close_price']:,}원({band}) / "
                        f"L{spot['lookback_bars']} "
                        f"DD{spot['rolling_high_drawdown_pct']} "
                        f"NL{spot['rolling_low_proximity_pct']}"
                    ),
                    (
                        f"   OOS {row['holdout_signal_episodes']}회·완료 "
                        f"{row['holdout_completed_legs']}leg / EV "
                        f"{row['notional_weighted_ev_pct']:+.4f}% / "
                        f"보유 {row['holdout_held_legs']}"
                        f"({row['holdout_held_leg_rate_per_filled_leg']:.1%})"
                    ),
                ]
            )
        if len(lane_rows) > MAX_RECOMMENDATIONS_PER_LANE:
            lines.append(
                f"외 {len(lane_rows) - MAX_RECOMMENDATIONS_PER_LANE}개 프로필은 보고서 참조"
            )
    postclose_logic_rows = list(report.get("postclose_logic_recommendations") or [])
    if postclose_logic_rows:
        lines.append("[당일 반등까지 확인된 누적 로직후보]")
        for row in postclose_logic_rows[:MAX_RECOMMENDATIONS_PER_LANE]:
            outcome = row["candidate_target_date"]
            episode = outcome["episodes"][0]
            params = row["candidate_parameters"]
            lines.extend(
                [
                    f"- {row['name']}({row['symbol']}) {row['session']} "
                    f"{str(episode['signal_at'])[11:16]}",
                    (
                        f"  DD{params['rolling_high_drawdown_pct']} "
                        f"NL{params['rolling_low_proximity_pct']} / 완료 "
                        f"{outcome['completed_legs']}leg·보유 {outcome['held_legs']} / "
                        f"EV {outcome['notional_weighted_ev_pct']:+.4f}%"
                    ),
                ]
            )
    lines.extend(
        [
            "판정: source-only 추천이며 자동 기계 구현·기동·실주문 권한 없음",
            "다음: 코드리뷰와 사용자 승인 후에만 별도 실기계 구현",
        ]
    )
    return "\n".join(lines)


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return (
        str(payload.get("TELEGRAM_TOKEN") or "").strip(),
        str(payload.get("ADMIN_ID") or "").strip(),
    )


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST"
    )
    with request.urlopen(req, timeout=10) as response:
        raw_response = response.read()
    try:
        payload = json.loads(raw_response.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("telegram_response_invalid") from exc
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError("telegram_send_not_ok")


class CandidateRecommendationNotifier:
    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        enabled: bool | None = None,
        max_attempts: int = 3,
        retry_delay_sec: float = 2.0,
        sleeper: Callable[[float], None] = time_module.sleep,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.enabled = (
            str(os.getenv("KORSTOCKSCAN_LOW_PRICE_CANDIDATE_TELEGRAM_ENABLED", "true"))
            .strip()
            .lower()
            not in {"0", "false", "no", "off"}
            if enabled is None
            else bool(enabled)
        )
        self.max_attempts = max(1, int(max_attempts))
        self.retry_delay_sec = max(0.0, float(retry_delay_sec))
        self.sleeper = sleeper

    @staticmethod
    def _valid_report(report: dict[str, Any]) -> bool:
        recommendations = report.get("recommendations")
        candidate_symbols = report.get("candidate_symbols")
        profile_inventory = report.get("research_profile_inventory")
        observation_inventory = report.get("operator_observation_candidate_inventory")
        if not isinstance(candidate_symbols, dict):
            return False
        try:
            start_date = date.fromisoformat(str(report.get("start_date") or ""))
            end_date = date.fromisoformat(str(report.get("end_date") or ""))
            target_date = date.fromisoformat(str(report.get("target_date") or ""))
            base_target_inventory = _target_date_research_inventory(target_date)
            target_inventory = _target_date_research_inventory(
                target_date,
                candidate_symbols=candidate_symbols,
            )
        except (TypeError, ValueError):
            return False
        expected_profile_inventory = _research_profile_inventory_public(
            target_inventory.research_profiles
        )
        basic_valid = bool(
            report.get("schema") == REPORT_SCHEMA
            and report.get("report_type") == REPORT_TYPE
            and report.get("status")
            in {
                "recommendations_ready",
                "no_qualified_candidate",
                "partial_source_quality",
                "source_quality_blocked",
            }
            and report.get("metric_contract") == METRIC_CONTRACT
            and report.get("authority") == AUTHORITY
            and report.get("recommendation_only") is True
            and report.get("machine_created") is False
            and report.get("service_started") is False
            and report.get("runtime_effect") is False
            and report.get("allowed_runtime_apply") is False
            and report.get("actual_order_submitted") is False
            and report.get("broker_order_forbidden") is True
            and isinstance(recommendations, list)
            and all(
                isinstance(symbol, str)
                and len(symbol) == 6
                and symbol.isdigit()
                and isinstance(name, str)
                and bool(name.strip())
                for symbol, name in candidate_symbols.items()
            )
            and report.get("candidate_universe_size") == len(candidate_symbols)
            and set(base_target_inventory.candidate_symbols).issubset(candidate_symbols)
            and len(
                set(candidate_symbols) - set(base_target_inventory.candidate_symbols)
            )
            <= MAX_DYNAMIC_SYMBOLS_PER_DAY
            and set(candidate_symbols).isdisjoint(target_inventory.implemented_symbols)
            and report.get("existing_symbol_universe_size")
            == len(target_inventory.implemented_symbols)
            and report.get("source_symbol_count")
            == len(target_inventory.research_symbols)
            and report.get("new_symbol_profile_count")
            == len(target_inventory.new_symbol_profiles)
            and report.get("existing_symbol_time_extension_profile_count")
            == len(target_inventory.time_extension_profiles)
            and report.get("existing_symbol_logic_improvement_profile_count")
            == len(target_inventory.logic_improvement_profiles)
            and report.get("recommendation_count") == len(recommendations or [])
            and isinstance(report.get("new_symbol_recommendations"), list)
            and report.get("new_symbol_recommendation_count")
            == len(report.get("new_symbol_recommendations") or [])
            and isinstance(
                report.get("existing_symbol_time_extension_recommendations"), list
            )
            and report.get("existing_symbol_time_extension_recommendation_count")
            == len(report.get("existing_symbol_time_extension_recommendations") or [])
            and isinstance(
                report.get("existing_symbol_logic_improvement_recommendations"), list
            )
            and report.get("existing_symbol_logic_improvement_recommendation_count")
            == len(
                report.get("existing_symbol_logic_improvement_recommendations") or []
            )
            and isinstance(report.get("target_date_logic_attribution"), list)
            and report.get("target_date_logic_attribution_count")
            == len(report.get("target_date_logic_attribution") or [])
            and isinstance(report.get("postclose_logic_recommendations"), list)
            and report.get("postclose_logic_recommendation_count")
            == len(report.get("postclose_logic_recommendations") or [])
            and int(report.get("eligible_source_symbol_count", -1))
            + int(report.get("quarantined_source_symbol_count", -1))
            == int(report.get("source_symbol_count", -1))
            and isinstance(report.get("source_quarantine"), dict)
            and isinstance(report.get("source_meta"), dict)
            and int(report.get("eligible_source_symbol_count", -1))
            == len(report.get("source_meta") or {})
            and int(report.get("quarantined_source_symbol_count", -1))
            == len(report.get("source_quarantine") or {})
            and set(report.get("source_meta") or {}).isdisjoint(
                report.get("source_quarantine") or {}
            )
            and set(report.get("source_meta") or {})
            | set(report.get("source_quarantine") or {})
            == set(target_inventory.research_symbols)
            and isinstance(profile_inventory, dict)
            and profile_inventory == expected_profile_inventory
            and isinstance(observation_inventory, dict)
            and report.get("operator_observation_candidate_count")
            == len(observation_inventory)
            and isinstance(report.get("profiles"), dict)
            and (
                (
                    report.get("status") == "source_quality_blocked"
                    and not report.get("profiles")
                )
                or set(report.get("profiles") or {}) == set(profile_inventory)
            )
            and len(profile_inventory)
            == int(report.get("new_symbol_profile_count", -1))
            + int(report.get("existing_symbol_time_extension_profile_count", -1))
            + int(report.get("existing_symbol_logic_improvement_profile_count", -1))
            and set(report.get("source_quarantine") or {}).issubset(
                set(target_inventory.research_symbols)
            )
        )
        if not basic_valid:
            return False
        expected_observation_inventory = _operator_observation_inventory(
            _new_symbol_profiles(candidate_symbols)
        )
        if observation_inventory != expected_observation_inventory:
            return False
        if any(
            not isinstance(item, dict)
            or item.get("fixed_observation")
            is not (profile_id in observation_inventory)
            for profile_id, item in profile_inventory.items()
        ):
            return False
        if report.get("status") != "source_quality_blocked" and any(
            not isinstance(item, dict)
            or item.get("observation_candidate")
            != observation_inventory.get(profile_id)
            for profile_id, item in (report.get("profiles") or {}).items()
        ):
            return False
        dynamic_source_date: date | None = None
        if report.get("dynamic_universe_source_date") is not None:
            try:
                dynamic_source_date = date.fromisoformat(
                    str(report["dynamic_universe_source_date"])
                )
            except ValueError:
                return False
        if (
            end_date != target_date
            or start_date != CLEAN_BASELINE_DATE
            or report.get("clean_tuning_baseline_date")
            != CLEAN_BASELINE_DATE.isoformat()
            or not is_krx_trading_day(target_date)
            or (
                dynamic_source_date is not None
                and (
                    not (CLEAN_BASELINE_DATE <= dynamic_source_date <= target_date)
                    or not is_krx_trading_day(dynamic_source_date)
                )
            )
            or (
                bool(
                    set(candidate_symbols)
                    - set(base_target_inventory.candidate_symbols)
                )
                and dynamic_source_date is None
            )
        ):
            return False
        try:
            expected_dates = clean_baseline_trading_dates(end_date)
            if (
                int(report.get("trading_date_count", 0)) != len(expected_dates)
                or int(report.get("calibration_trading_day_count", 0))
                != len(expected_dates) - HOLDOUT_DAYS
                or int(report.get("holdout_trading_day_count", 0)) != HOLDOUT_DAYS
            ):
                return False
        except ValueError:
            return False
        if report.get("status") == "source_quality_blocked":
            return bool(
                not recommendations
                and not report.get("target_date_logic_attribution")
                and not report.get("postclose_logic_recommendations")
                and report.get("source_quality_reasons")
            )
        if bool(recommendations) != (report.get("status") == "recommendations_ready"):
            return False
        profile_ids = [str(row.get("profile_id") or "") for row in recommendations]
        if len(profile_ids) != len(set(profile_ids)):
            return False
        expected_new = [
            row for row in recommendations if row.get("discovery_lane") == "new_symbol"
        ]
        expected_existing = [
            row
            for row in recommendations
            if row.get("discovery_lane") == "existing_symbol_time_extension"
        ]
        expected_logic = [
            row
            for row in recommendations
            if row.get("discovery_lane") == "existing_symbol_logic_improvement"
        ]
        if (
            report.get("new_symbol_recommendations") != expected_new
            or report.get("existing_symbol_time_extension_recommendations")
            != expected_existing
            or report.get("new_symbol_recommendation_count") != len(expected_new)
            or report.get("existing_symbol_time_extension_recommendation_count")
            != len(expected_existing)
            or report.get("existing_symbol_logic_improvement_recommendations")
            != expected_logic
            or report.get("existing_symbol_logic_improvement_recommendation_count")
            != len(expected_logic)
        ):
            return False
        logic_recommendation_ids = {
            str(row.get("profile_id") or "") for row in expected_logic
        }
        logic_policy_hashes = {
            str(row.get("profile_id") or ""): str(row.get("baseline_policy_hash") or "")
            for row in expected_logic
        }
        attribution = report.get("target_date_logic_attribution") or []
        postclose_logic = report.get("postclose_logic_recommendations") or []
        expected_postclose_logic = [
            row
            for row in attribution
            if row.get("decision") == "recommend_cumulative_logic_candidate_review"
            and str(row.get("profile_id") or "") in logic_recommendation_ids
        ]
        if (
            report.get("target_date_logic_attribution_count")
            != len(target_inventory.logic_improvement_profiles)
            or postclose_logic != expected_postclose_logic
        ):
            return False
        if not all(
            isinstance(row, dict)
            and row.get("profile_id") in target_inventory.logic_improvement_profiles
            and row.get("active_profile_id") in target_inventory.live_profiles
            and row.get("runtime_effect") is False
            and row.get("actual_order_submitted") is False
            and row.get("broker_order_forbidden") is True
            for row in attribution
        ):
            return False
        if not all(
            _valid_postclose_logic_recommendation(row)
            and str(row.get("applied_policy_hash") or "")
            == logic_policy_hashes.get(str(row.get("profile_id") or ""))
            for row in postclose_logic
        ):
            return False
        return all(
            isinstance(row, dict)
            and row.get("profile_id") in profile_inventory
            and row.get("symbol")
            == profile_inventory[str(row.get("profile_id"))].get("symbol")
            and row.get("session")
            == profile_inventory[str(row.get("profile_id"))].get("session")
            and row.get("discovery_lane")
            == profile_inventory[str(row.get("profile_id"))].get("discovery_lane")
            and (
                row.get("discovery_lane") != "existing_symbol_time_extension"
                or (
                    (str(row.get("symbol")), str(row.get("session")))
                    not in target_inventory.active_symbol_sessions
                    and row.get("active_profile_ids_for_symbol")
                    == sorted(
                        profile_id
                        for profile_id, live_profile in (
                            target_inventory.live_profiles.items()
                        )
                        if live_profile.symbol == str(row.get("symbol"))
                    )
                )
            )
            and isinstance(row.get("recommended_spot"), dict)
            and 0 < int(row.get("latest_close_price", 0) or 0) <= MAX_LATEST_CLOSE_PRICE
            and row.get("price_band") in {"under_50000_krw", "50000_to_100000_krw"}
            and 0.0
            <= float(row.get("holdout_held_leg_rate_per_filled_leg", -1.0))
            <= MAX_MANAGEABLE_HELD_LEG_RATE
            and (
                row.get("holdout_active_unrealized_notional_weighted_pct") is None
                or float(row["holdout_active_unrealized_notional_weighted_pct"])
                >= -MAX_MANAGEABLE_HELD_MARK_TO_MARKET_LOSS_PCT
            )
            and float(row.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and row.get("implementation_status")
            == "source_only_requires_review_and_user_approval"
            and row.get("runtime_effect") is False
            and (
                row.get("discovery_lane") != "existing_symbol_logic_improvement"
                or (
                    row.get("baseline_policy_source") == "target_date_applied_policy"
                    and bool(str(row.get("baseline_policy_hash") or ""))
                )
            )
            for row in recommendations
        )

    def notify(self, report: dict[str, Any]) -> str:
        if not self.enabled:
            return "disabled"
        if not self._valid_report(report):
            return "invalid_report"
        target_date = str(report.get("target_date") or "")
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if (
            isinstance(state, dict)
            and state.get("last_sent_target_date") == target_date
        ):
            return "duplicate"
        token, admin_id = self.config_loader()
        if not token or not admin_id:
            return "missing_config"
        for attempt in range(1, self.max_attempts + 1):
            try:
                self.sender(token, admin_id, build_telegram_message(report))
                break
            except Exception:
                if attempt >= self.max_attempts:
                    return "send_failed"
                self.sleeper(self.retry_delay_sec)
        try:
            _atomic_write(
                self.state_file,
                json.dumps(
                    {
                        "last_sent_target_date": target_date,
                        "authority": AUTHORITY,
                        "telegram_audience": "ADMIN_ONLY",
                        "runtime_effect": False,
                        "machine_created": False,
                        "service_started": False,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
            )
        except OSError:
            return "sent_state_persist_failed"
        return "sent"


def write_report(
    report: dict[str, Any], output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"low_price_two_leg_expanded_candidate_research_{report['end_date']}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def _valid_postclose_logic_recommendation(row: Any) -> bool:
    if not isinstance(row, dict):
        return False
    baseline = row.get("baseline_target_date")
    candidate = row.get("candidate_target_date")
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        return False
    try:
        return bool(
            row.get("applied_policy_status") == "ready"
            and row.get("applied_policy_reason") == "ready"
            and str(row.get("applied_policy_hash") or "")
            and int(baseline.get("signal_episodes", -1)) == 0
            and int(candidate.get("signal_episodes", -1)) == 1
            and int(candidate.get("completed_legs", -1)) >= 1
            and int(candidate.get("held_legs", -1)) == 0
            and float(candidate.get("notional_weighted_ev_pct")) > 0.0
        )
    except (TypeError, ValueError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--max-pages", type=int, default=400)
    parser.add_argument("--page-delay-sec", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else (
            date.fromisoformat(args.end_date)
            if args.end_date
            else _default_target_date()
        )
    )
    end_date = date.fromisoformat(args.end_date) if args.end_date else target_date
    if end_date != target_date:
        raise ValueError("end_date_must_equal_target_date")
    start_date = (
        date.fromisoformat(args.start_date) if args.start_date else CLEAN_BASELINE_DATE
    )
    if start_date != CLEAN_BASELINE_DATE:
        raise ValueError("start_date_must_equal_clean_baseline")
    expected_trading_day_count = len(clean_baseline_trading_dates(end_date))
    if args.notify and not args.write:
        raise ValueError("telegram_notification_requires_written_report")
    try:
        token = kiwoom_utils.get_cached_kiwoom_token()
        if not token:
            raise ResearchError("cached_token_missing_no_issue_or_refresh_allowed")
        base_target_inventory = _target_date_research_inventory(target_date)
        dynamic_source_date, dynamic_symbols = _dynamic_candidate_snapshot(
            target_date,
            implemented_symbols=base_target_inventory.implemented_symbols,
        )
        candidate_symbols = {
            **base_target_inventory.candidate_symbols,
            **dynamic_symbols,
        }
        applied_policy_snapshots: dict[str, dict[str, Any]] = {}
        for profile_id in sorted(base_target_inventory.live_profiles):
            policy, applied_hash, reason = load_applied_profile_policy(
                profile_id, target_date=target_date
            )
            applied_policy_snapshots[profile_id] = {
                "status": "ready" if policy is not None else "unavailable",
                "reason": reason,
                "policy_hash": applied_hash or None,
                "policy": policy,
            }
        target_inventory = _target_date_research_inventory(
            target_date,
            candidate_symbols=candidate_symbols,
            applied_policy_snapshots=applied_policy_snapshots,
        )
        research_profiles = target_inventory.research_profiles
        allowlist = target_inventory.research_symbols
        sources: dict[str, tuple[list[Bar], dict[str, Any]]] = {}
        fetch_failures: dict[str, str] = {}
        for symbol in sorted(allowlist):
            try:
                sources[symbol] = fetch_sor_history(
                    symbol=symbol,
                    token=token,
                    start_date=start_date,
                    end_date=end_date,
                    max_pages=args.max_pages,
                    page_delay_sec=args.page_delay_sec,
                    allowed_symbols=allowlist,
                    expected_trading_day_count=expected_trading_day_count,
                )
            except (ResearchError, requests.RequestException) as exc:
                fetch_failures[symbol] = str(exc)
        if not sources:
            distinct_reasons = sorted(set(fetch_failures.values()))
            raise ResearchError(
                "all_research_symbols_source_quality_blocked:"
                + "|".join(distinct_reasons)
            )
        report = build_report(
            sources=sources,
            start_date=start_date,
            end_date=end_date,
            candidate_symbols=candidate_symbols,
            research_profiles=research_profiles,
            dynamic_universe_source_date=dynamic_source_date,
            applied_policy_snapshots=applied_policy_snapshots,
        )
        if fetch_failures:
            report["source_quarantine"].update(fetch_failures)
            for item in report["profiles"].values():
                symbol = str(item.get("symbol") or "")
                if symbol in fetch_failures and item.get("decision") == (
                    "source_quality_quarantined_no_evaluation"
                ):
                    item["source_quality_reason"] = fetch_failures[symbol]
            report["quarantined_source_symbol_count"] = len(report["source_quarantine"])
            report["eligible_source_symbol_count"] = len(allowlist) - len(
                report["source_quarantine"]
            )
            if report["status"] == "no_qualified_candidate":
                report["status"] = "partial_source_quality"
    except (ResearchError, requests.RequestException) as exc:
        report = build_source_quality_blocked_report(
            start_date=start_date, end_date=end_date, reason=str(exc)
        )
    report["telegram_status"] = "not_requested"
    paths = write_report(report, args.output_dir) if args.write else (None, None)
    if args.notify:
        report["telegram_status"] = CandidateRecommendationNotifier().notify(report)
        paths = write_report(report, args.output_dir)
        if report["telegram_status"] not in {
            "sent",
            "duplicate",
            "sent_state_persist_failed",
        }:
            raise RuntimeError(
                "candidate_recommendation_telegram_not_delivered:"
                f"{report['telegram_status']}"
            )
    if args.print_summary:
        print(
            json.dumps(
                {
                    "decision": report["decision"],
                    "holdout_pass_profiles": [
                        profile_id
                        for profile_id, item in report["profiles"].items()
                        if item["decision"]
                        == "holdout_pass_source_only_early_candidate"
                    ],
                    "recommendation_count": report["recommendation_count"],
                    "new_symbol_recommendation_count": report[
                        "new_symbol_recommendation_count"
                    ],
                    "existing_symbol_time_extension_recommendation_count": report[
                        "existing_symbol_time_extension_recommendation_count"
                    ],
                    "postclose_logic_recommendation_count": report[
                        "postclose_logic_recommendation_count"
                    ],
                    "telegram_status": report["telegram_status"],
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
