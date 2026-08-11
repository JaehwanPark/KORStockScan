"""Evaluate widget-only Samsung advisories from compact minute observations."""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitoring.samsung_widget_contract import (
    ACTIONABLE_ADVISORY_STATES,
    ADVISORY_AUTHORITY,
    DEFAULT_OBSERVATION_DIR,
    KST,
    NXT_AFTERMARKET_END,
    SAMSUNG_CODE,
    previous_krx_trading_date,
)
from src.utils.market_day import is_krx_trading_day
from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size

DEFAULT_OUTPUT_DIR = Path("data/report/samsung_widget_advisory_evaluation")
CLEAN_BASELINE_DATE = date(2026, 6, 5)
HORIZONS_MINUTES = (1, 3, 5, 10, 20, 30, 60)
TARGET_RETURN_PCT = 0.5
FALLBACK_ADVERSE_PCT = -0.3
MIN_COVERAGE_RATIO = 0.80
MAX_COVERAGE_GAP_SEC = 120
SIGNAL_EPISODE_DEDUP_SEC = 120
EXIT_POLICY_TARGETS_PCT = (0.5, 1.0)
CAPACITY_REPLAY_ROUND_TRIP_COST_PCT = 0.20
CAPACITY_POLICY_IDS = (
    "fixed_0.5pct",
    "fixed_1pct",
    "observed_exact_episode_structural_exit_ready",
)
SESSION_EXPECTED_MINUTES = {
    "NXT_PREMARKET": 50,
    "KRX_REGULAR": 390,
    "NXT_AFTERMARKET": 260,
}

EVALUATION_CONTRACT = {
    "schema_version": 2,
    "metric_role": "counterfactual_observation",
    "decision_authority": "widget_advisory_evaluation_only",
    "window_policy": "daily_and_rolling_60_trading_days",
    "sample_floor": "60_coverage_qualified_trading_days_before_threshold_judgment",
    "primary_decision_metric": "none_counterfactual_mfe_mae",
    "source_quality_gate": (
        "exact_entry_touch_and_mature_same_session_window_with_80pct_coverage"
    ),
    "legacy_real_replay_policy": (
        "exclude_sources_without_same-session_completed_ohlcv_bbo_venue_and_advisory"
    ),
    "allowed_consumers": [
        "diagnostic_daily_and_rolling_report",
        "bounded_widget_advisory_calibration_v1",
    ],
    "widget_calibration_sample_floor": (
        "one_source_qualified_decisive_10m_outcome_starts_cumulative_widget_only_learning"
    ),
    "target_policy": "entry_reference_plus_0.5pct_tick_ceil",
    "episode_exit_policy_comparison": (
        "same_episode_fixed_0.5pct_fixed_1.0pct_and_observed_exit_ready"
    ),
    "episode_exit_policy_source_quality_gate": (
        "exact_entry_touch_and_80pct_source_quality_pass_coverage_with_exact_episode_id_for_exit"
    ),
    "episode_exit_policy_assumptions": (
        "fixed_targets_hold_without_stop_scale_in_or_position_capacity;gross_market_counterfactual_only"
    ),
    "capacity_constrained_replay": (
        "one_position_per_session_and_policy;signal_validity_enforced;completed_trades_only_cost_adjusted_diagnostic"
    ),
    "adverse_policy": "dynamic_invalidation_else_entry_minus_0.3pct_tick_floor",
    "forbidden_uses": [
        "real_order_submission",
        "real_execution_quality_approval",
        "automatic_real_trading_threshold_or_runtime_apply",
        "provider_or_bot_change",
        "realized_pnl_aggregation",
    ],
}

ENTRY_SCENARIO_UNCLASSIFIED = "unclassified_actionable_setup"

CAPACITY_REPLAY_CONTRACT = {
    "schema_version": 1,
    "metric_role": "counterfactual_observation",
    "decision_authority": "widget_advisory_evaluation_only",
    "window_policy": "daily_session_separated_one_position_per_exit_policy",
    "sample_floor": "none_daily_diagnostic_only",
    "primary_decision_metric": "none_completed_trade_diagnostic_only",
    "source_quality_gate": (
        "exact_entry_touch_within_signal_validity_and_80pct_source_quality_pass_coverage"
    ),
    "fill_assumption": (
        "fixed_target_market_high_touch_at_target_price_without_broker_latency_or_fill_proof"
    ),
    "cost_policy": "fixed_0.20pct_round_trip_research_assumption_not_broker_reconciliation",
    "forbidden_uses": [
        "real_order_submission",
        "automatic_widget_signal_or_calibration_change",
        "automatic_exit_policy_selection",
        "profit_metrics_with_unresolved_positions",
        "cross_policy_profit_summing",
        "provider_or_bot_change",
    ],
}


def _parse_time(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").strip())
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _positive_int(value: object) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _signal_contract_issue(
    row: dict[str, Any],
    advisory: object,
    *,
    symbol_code: str = SAMSUNG_CODE,
) -> str | None:
    if row.get("observation_kind") != "state_transition":
        return "observation_kind_missing_or_invalid"
    metric_contract = row.get("metric_contract")
    if (
        not isinstance(metric_contract, dict)
        or metric_contract.get("decision_authority") != ADVISORY_AUTHORITY
    ):
        return "observation_metric_contract_mismatch"
    if not isinstance(advisory, dict):
        return "advisory_not_object"
    if (
        advisory.get("authority") != ADVISORY_AUTHORITY
        or advisory.get("runtime_effect") is not False
        or advisory.get("actual_order_submitted") is not False
        or advisory.get("broker_order_forbidden") is not True
    ):
        return "advisory_authority_contract_mismatch"
    source_quality = advisory.get("source_quality")
    if not isinstance(source_quality, dict) or source_quality.get("status") != "PASS":
        return "advisory_source_quality_not_pass"
    signal_time = row.get("_observed_at")
    advisory_time = _parse_time(advisory.get("observed_at"))
    valid_until = _parse_time(advisory.get("valid_until"))
    if not isinstance(signal_time, datetime) or advisory_time is None:
        return "advisory_observed_at_missing_or_naive"
    if abs((signal_time - advisory_time).total_seconds()) > 1.0:
        return "advisory_observed_at_mismatch"
    if valid_until is None:
        return "advisory_expired_at_signal"
    validity_sec = (valid_until - signal_time).total_seconds()
    if validity_sec < 0 or validity_sec > 60.001:
        return "advisory_validity_window_invalid"
    session = str(row.get("market_session") or "")
    venue = str(row.get("market_venue") or "")
    if advisory.get("session") != session or venue not in {"KRX", "NXT"}:
        return "advisory_session_or_venue_mismatch"
    provenance = advisory.get("provenance")
    expected_request_code = f"{symbol_code}_NX" if venue == "NXT" else symbol_code
    if (
        not isinstance(provenance, dict)
        or provenance.get("market_venue") != venue
        or provenance.get("quote_request_code") != expected_request_code
    ):
        return "advisory_provenance_mismatch"
    try:
        entry_low = int(advisory.get("entry_price_low") or 0)
        entry_high = int(advisory.get("entry_price_high") or 0)
    except (TypeError, ValueError):
        return "advisory_entry_range_invalid"
    if entry_low <= 0 or entry_high < entry_low:
        return "advisory_entry_range_invalid"
    return None


def _parse_bar_start(value: object) -> datetime | None:
    raw = str(value or "").strip()
    try:
        return datetime.strptime(raw[:14], "%Y%m%d%H%M%S").replace(tzinfo=KST)
    except (TypeError, ValueError):
        return None


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError:
        return rows
    with handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            observed_at = _parse_time(row.get("observed_at_kst"))
            try:
                current_price = int(row.get("current_price") or 0)
            except (TypeError, ValueError):
                current_price = 0
            if observed_at is None or current_price <= 0:
                continue
            latest_bar = row.get("latest_completed_bar") or {}
            try:
                high_price = int(latest_bar.get("high") or 0)
                low_price = int(latest_bar.get("low") or 0)
            except (AttributeError, TypeError, ValueError):
                high_price = 0
                low_price = 0
            bar_start = _parse_bar_start(
                latest_bar.get("source_time") if isinstance(latest_bar, dict) else None
            )
            if high_price <= 0 or low_price <= 0 or high_price < low_price:
                bar_start = None
                high_price = 0
                low_price = 0
            rows.append(
                {
                    **row,
                    "_observed_at": observed_at,
                    "_current_price": current_price,
                    "_bar_start": bar_start,
                    "_bar_high": high_price,
                    "_bar_low": low_price,
                    "_line_number": line_number,
                }
            )
    return sorted(rows, key=lambda row: row["_observed_at"])


def _ceil_to_tick(value: float) -> int:
    floored = clamp_price_to_tick(max(1, int(value)))
    if floored >= value:
        return floored
    return floored + get_tick_size(floored)


def _first_hit(
    prices: list[tuple[datetime, int, int]], *, target: int, adverse: int
) -> tuple[str, str | None]:
    for observed_at, high_price, low_price in prices:
        target_hit = high_price >= target
        adverse_hit = low_price <= adverse
        if target_hit and adverse_hit:
            return "same_observation_ambiguous", observed_at.isoformat()
        if target_hit:
            return "target_first", observed_at.isoformat()
        if adverse_hit:
            return "adverse_first", observed_at.isoformat()
    return "neither", None


def _ceil_minute(value: datetime) -> datetime:
    floor = value.replace(second=0, microsecond=0)
    return floor if value == floor else floor + timedelta(minutes=1)


def _future_price_observations(
    rows: list[dict[str, Any]],
    *,
    signal_time: datetime,
    maturity_time: datetime,
) -> list[tuple[datetime, int, int]]:
    """Return future-only points without reusing the signal's completed bar.

    Current-price samples retain their receive time. A completed minute bar is
    included only when the whole bar starts at or after the first full minute
    following the signal and finishes within the requested horizon. Repeated
    state/minute records carrying the same completed bar are deduplicated.
    """
    observations: list[tuple[datetime, int, int]] = []
    first_full_bar_start = _ceil_minute(signal_time)
    completed_bars: dict[datetime, tuple[int, int]] = {}
    for row in rows:
        observed_at = row["_observed_at"]
        if signal_time < observed_at <= maturity_time:
            current_price = row["_current_price"]
            observations.append((observed_at, current_price, current_price))
        bar_start = row.get("_bar_start")
        if not isinstance(bar_start, datetime):
            continue
        bar_end = bar_start + timedelta(minutes=1)
        if first_full_bar_start <= bar_start and bar_end <= maturity_time:
            completed_bars[bar_start] = (row["_bar_high"], row["_bar_low"])
    observations.extend(
        (bar_start + timedelta(minutes=1), high_price, low_price)
        for bar_start, (high_price, low_price) in completed_bars.items()
    )
    merged: dict[datetime, tuple[int, int]] = {}
    for observed_at, high_price, low_price in observations:
        previous = merged.get(observed_at)
        if previous is None:
            merged[observed_at] = (high_price, low_price)
        else:
            merged[observed_at] = (
                max(previous[0], high_price),
                min(previous[1], low_price),
            )
    return [
        (observed_at, high_price, low_price)
        for observed_at, (high_price, low_price) in sorted(merged.items())
    ]


def _entry_touch(
    rows: list[dict[str, Any]],
    *,
    signal_time: datetime,
    entry_low: int,
    entry_high: int,
) -> tuple[str, datetime | None]:
    events: list[tuple[datetime, int, str, int, int]] = []
    for row in rows:
        observed_at = row["_observed_at"]
        if observed_at < signal_time:
            continue
        current_price = row["_current_price"]
        events.append((observed_at, 0, "point", current_price, current_price))
        bar_start = row.get("_bar_start")
        if isinstance(bar_start, datetime):
            bar_end = bar_start + timedelta(minutes=1)
            if bar_end >= signal_time:
                events.append((bar_end, 1, "bar", row["_bar_high"], row["_bar_low"]))
    for observed_at, _, kind, high_price, low_price in sorted(events):
        if high_price < entry_low or low_price > entry_high:
            continue
        if kind == "point":
            return "ENTRY_TOUCHED", observed_at
        return "ENTRY_AMBIGUOUS", observed_at
    return "NOT_TOUCHED", None


def _entry_episode_id(row: dict[str, Any]) -> str | None:
    exit_advisory = row.get("exit_advisory")
    continuity = (
        exit_advisory.get("continuity") if isinstance(exit_advisory, dict) else None
    )
    raw = continuity.get("entry_episode_id") if isinstance(continuity, dict) else None
    value = str(raw or "").strip()
    return value or None


def _classify_entry_scenario(advisory: dict[str, Any]) -> str:
    """Classify an actionable setup without changing the live advisory state.

    Explicit branch triggers take priority.  The legacy/common trigger is then
    split using immutable derived evidence already present in the observation.
    Unknown or incomplete evidence remains unclassified rather than being
    forced into a profitable-looking cohort.
    """
    trigger = str(advisory.get("trigger") or "").strip()
    if trigger == "candidate_support_vwap_recovery_caution":
        return "candidate_support_vwap_recovery"
    if trigger == "confirmed_retest_early_reversal":
        return "support_retest_early_reversal"
    if trigger == "recovery_episode_resistance_reclaim_pullback":
        return "resistance_reclaim_first_pullback"

    derived = advisory.get("derived")
    if not isinstance(derived, dict):
        return ENTRY_SCENARIO_UNCLASSIFIED
    if (
        derived.get("retest_held") is True
        or derived.get("retest_rebound_confirmed") is True
    ):
        return "support_retest_reversal"
    if (
        derived.get("higher_high_and_low") is True
        and derived.get("recent_resistance_reclaimed") is True
    ):
        return "resistance_reclaim_continuation"
    if (
        derived.get("higher_high_and_low") is True
        and derived.get("vwap_only_structure_confirmed") is True
    ):
        return "vwap_higher_low_recovery"
    return ENTRY_SCENARIO_UNCLASSIFIED


def _target_policy_result(
    observations: list[tuple[datetime, int, int]],
    *,
    entry_price: int,
    target_return_pct: float,
    entry_time: datetime,
) -> dict[str, Any]:
    target_price = _ceil_to_tick(entry_price * (1 + target_return_pct / 100))
    observed_through = observations[-1][0].isoformat() if observations else None
    for observed_at, high_price, _ in observations:
        if high_price >= target_price:
            return {
                "policy": f"fixed_{target_return_pct:g}pct",
                "holding_policy": (
                    "hold_until_target_or_observed_session_end_without_stop_or_scale_in"
                ),
                "target_return_pct": target_return_pct,
                "target_price": target_price,
                "status": "TARGET_HIT",
                "hit_at_kst": observed_at.isoformat(),
                "minutes_to_hit": round(
                    (observed_at - entry_time).total_seconds() / 60,
                    3,
                ),
                "observed_through_kst": observed_through,
            }
    return {
        "policy": f"fixed_{target_return_pct:g}pct",
        "holding_policy": (
            "hold_until_target_or_observed_session_end_without_stop_or_scale_in"
        ),
        "target_return_pct": target_return_pct,
        "target_price": target_price,
        "status": "NOT_HIT_WITHIN_OBSERVED_SESSION_WINDOW",
        "hit_at_kst": None,
        "minutes_to_hit": None,
        "observed_through_kst": observed_through,
    }


def _structural_exit_result(
    rows: list[dict[str, Any]],
    *,
    entry_episode_id: str | None,
    entry_time: datetime,
    entry_price: int,
) -> dict[str, Any]:
    base = {
        "policy": "observed_structural_exit_ready",
        "entry_episode_id": entry_episode_id,
        "status": "NO_EXIT_READY_WITHIN_OBSERVED_SESSION_WINDOW",
        "exit_at_kst": None,
        "reference_exit_price": None,
        "gross_return_pct": None,
        "minutes_to_exit": None,
        "contract_issue": None,
    }
    if entry_episode_id is None:
        return {**base, "status": "UNATTRIBUTABLE_MISSING_EPISODE_ID"}
    for row in rows:
        if row["_observed_at"] <= entry_time:
            continue
        exit_advisory = row.get("exit_advisory")
        if (
            not isinstance(exit_advisory, dict)
            or exit_advisory.get("state") != "EXIT_READY"
        ):
            continue
        continuity = exit_advisory.get("continuity")
        candidate_episode_id = (
            str(continuity.get("entry_episode_id") or "").strip()
            if isinstance(continuity, dict)
            else ""
        )
        if candidate_episode_id != entry_episode_id:
            continue
        issue = None
        source_quality = exit_advisory.get("source_quality")
        exit_time = _parse_time(exit_advisory.get("observed_at"))
        valid_until = _parse_time(exit_advisory.get("valid_until"))
        try:
            reference_exit_price = int(exit_advisory.get("reference_exit_price") or 0)
        except (TypeError, ValueError):
            reference_exit_price = 0
        if row.get("observation_kind") not in {
            "state_transition",
            "exit_state_transition",
        }:
            issue = "exit_observation_kind_invalid"
        elif (
            exit_advisory.get("authority") != ADVISORY_AUTHORITY
            or exit_advisory.get("runtime_effect") is not False
            or exit_advisory.get("actual_order_submitted") is not False
            or exit_advisory.get("broker_order_forbidden") is not True
            or exit_advisory.get("holding_independent") is not True
        ):
            issue = "exit_authority_contract_mismatch"
        elif (
            not isinstance(source_quality, dict)
            or source_quality.get("status") != "PASS"
        ):
            issue = "exit_source_quality_not_pass"
        elif (
            exit_time is None
            or abs((row["_observed_at"] - exit_time).total_seconds()) > 1
        ):
            issue = "exit_observed_at_missing_or_mismatch"
        elif valid_until is None or not (
            exit_time <= valid_until <= exit_time + timedelta(seconds=60.001)
        ):
            issue = "exit_validity_window_invalid"
        elif reference_exit_price <= 0:
            issue = "exit_reference_price_invalid"
        if issue is not None:
            return {**base, "status": "INVALID_EXIT_CONTRACT", "contract_issue": issue}
        return {
            **base,
            "status": "EXIT_READY_ATTRIBUTED",
            "exit_at_kst": exit_time.isoformat(),
            "reference_exit_price": reference_exit_price,
            "gross_return_pct": round(
                ((reference_exit_price - entry_price) / entry_price) * 100,
                6,
            ),
            "minutes_to_exit": round(
                (exit_time - entry_time).total_seconds() / 60,
                3,
            ),
        }
    return base


def _build_episode_policy_comparison(
    rows: list[dict[str, Any]],
    *,
    signal_row: dict[str, Any],
    advisory: dict[str, Any],
    touch_status: str,
    touch_time: datetime | None,
    entry_price: int,
    market_session: str,
    market_venue: str,
) -> dict[str, Any]:
    signal_time = signal_row["_observed_at"]
    signal_valid_until = _parse_time(advisory.get("valid_until"))
    episode_id = _entry_episode_id(signal_row)
    scenario = _classify_entry_scenario(advisory)
    base = {
        "signal_observed_at_kst": signal_time.isoformat(),
        "signal_valid_until_kst": (
            signal_valid_until.isoformat() if signal_valid_until else None
        ),
        "source_line_number": signal_row["_line_number"],
        "entry_episode_id": episode_id,
        "entry_scenario": scenario,
        "market_session": market_session,
        "market_venue": market_venue,
        "advisory_state": advisory.get("state"),
        "entry_reference_price": entry_price,
        "entry_touch_status": touch_status,
        "entry_touched_at_kst": touch_time.isoformat() if touch_time else None,
        "entry_touch_within_signal_validity": bool(
            touch_time is not None
            and signal_valid_until is not None
            and touch_time <= signal_valid_until
        ),
        "comparison_status": "ENTRY_NOT_EXACTLY_TOUCHED",
        "comparison_eligible": False,
        "comparison_coverage": None,
        "fixed_target_results": [],
        "structural_exit_result": None,
        "session_end_mfe_pct": None,
        "session_end_mae_pct": None,
        "observed_window_end_at_kst": None,
        "observed_window_end_price": None,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if touch_status != "ENTRY_TOUCHED" or touch_time is None:
        return base
    session_end = rows[-1]["_observed_at"] if rows else touch_time
    source_qualified_rows = []
    for row in rows:
        row_advisory = row.get("advisory")
        source_quality = (
            row_advisory.get("source_quality")
            if isinstance(row_advisory, dict)
            else None
        )
        if isinstance(source_quality, dict) and source_quality.get("status") == "PASS":
            source_qualified_rows.append(row)
    observations = _future_price_observations(
        source_qualified_rows,
        signal_time=touch_time,
        maturity_time=session_end,
    )
    comparison_coverage = _coverage(
        observations,
        start=touch_time,
        end=session_end,
    )
    comparison_coverage["episode_policy_coverage_passed"] = (
        comparison_coverage["coverage_ratio"] >= MIN_COVERAGE_RATIO
    )
    comparison_coverage["episode_policy_coverage_rule"] = (
        "80pct_source_quality_pass_ratio;max_gap_retained_as_diagnostic"
    )
    comparison_eligible = comparison_coverage["episode_policy_coverage_passed"]
    fixed_results = [
        _target_policy_result(
            observations,
            entry_price=entry_price,
            target_return_pct=target_pct,
            entry_time=touch_time,
        )
        for target_pct in EXIT_POLICY_TARGETS_PCT
    ]
    if observations:
        max_price = max(high_price for _, high_price, _ in observations)
        min_price = min(low_price for _, _, low_price in observations)
        session_mfe = round(((max_price - entry_price) / entry_price) * 100, 6)
        session_mae = round(((min_price - entry_price) / entry_price) * 100, 6)
    else:
        session_mfe = None
        session_mae = None
    terminal_rows = [
        row for row in source_qualified_rows if row["_observed_at"] > touch_time
    ]
    terminal_row = terminal_rows[-1] if terminal_rows else None
    return {
        **base,
        "comparison_status": (
            "SOURCE_QUALIFIED"
            if comparison_eligible
            else "INSUFFICIENT_SOURCE_QUALIFIED_COVERAGE"
        ),
        "comparison_eligible": comparison_eligible,
        "comparison_coverage": comparison_coverage,
        "fixed_target_results": fixed_results,
        "structural_exit_result": _structural_exit_result(
            rows,
            entry_episode_id=episode_id,
            entry_time=touch_time,
            entry_price=entry_price,
        ),
        "session_end_mfe_pct": session_mfe,
        "session_end_mae_pct": session_mae,
        "observed_window_end_at_kst": (
            terminal_row["_observed_at"].isoformat() if terminal_row else None
        ),
        "observed_window_end_price": (
            terminal_row["_current_price"] if terminal_row else None
        ),
    }


def _coverage(
    observations: list[tuple[datetime, int, int]],
    *,
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    expected = max(1, int((end - start).total_seconds() // 60))
    minute_points = sorted(
        {
            bucket
            for observed_at, _, _ in observations
            if start < observed_at <= end
            and (bucket := _ceil_minute(observed_at)) <= end
        }
    )
    observed = min(expected, len(minute_points))
    ratio = observed / expected
    gap_points = [start, *minute_points, end]
    max_gap_sec = max(
        (
            (current - previous).total_seconds()
            for previous, current in zip(gap_points, gap_points[1:])
        ),
        default=(end - start).total_seconds(),
    )
    return {
        "expected_minute_count": expected,
        "observed_minute_count": observed,
        "missing_minute_count": max(0, expected - observed),
        "coverage_ratio": round(ratio, 6),
        "max_gap_sec": round(max_gap_sec, 3),
        "coverage_passed": bool(
            ratio >= MIN_COVERAGE_RATIO and max_gap_sec <= MAX_COVERAGE_GAP_SEC
        ),
    }


def _session_coverage(
    source_rows: list[dict[str, Any]],
    *,
    expected_sessions: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    session_expectations = (
        SESSION_EXPECTED_MINUTES if expected_sessions is None else expected_sessions
    )
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    total_grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in source_rows:
        session = str(row.get("market_session") or "unknown")
        venue = str(row.get("market_venue") or "unknown")
        if session not in session_expectations:
            continue
        minute_key = row["_observed_at"].strftime("%Y%m%d%H%M")
        total_grouped[(session, venue)].add(minute_key)
        advisory = row.get("advisory")
        source_quality = (
            advisory.get("source_quality") if isinstance(advisory, dict) else None
        )
        if isinstance(source_quality, dict) and source_quality.get("status") == "PASS":
            grouped[(session, venue)].add(minute_key)
    result: list[dict[str, Any]] = []
    for session, expected in session_expectations.items():
        venue = "KRX" if session == "KRX_REGULAR" else "NXT"
        observed = len(grouped.get((session, venue), set()))
        total_observed = len(total_grouped.get((session, venue), set()))
        ratio = min(1.0, observed / expected)
        result.append(
            {
                "market_session": session,
                "market_venue": venue,
                "expected_minute_count": expected,
                "observed_minute_count": observed,
                "total_observed_minute_count": total_observed,
                "coverage_ratio": round(ratio, 6),
                "qualified": ratio >= MIN_COVERAGE_RATIO,
            }
        )
    return result


def build_daily_evaluation(
    rows: list[dict[str, Any]],
    *,
    target_date: date,
    symbol_code: str = SAMSUNG_CODE,
    expected_sessions: dict[str, int] | None = None,
    target_return_pct: float = TARGET_RETURN_PCT,
    fallback_adverse_pct: float = FALLBACK_ADVERSE_PCT,
) -> dict[str, Any]:
    if target_return_pct <= 0:
        raise ValueError("target_return_pct_must_be_positive")
    if fallback_adverse_pct >= 0:
        raise ValueError("fallback_adverse_pct_must_be_negative")
    source_rows = [row for row in rows if row["_observed_at"].date() == target_date]
    outcomes: list[dict[str, Any]] = []
    episode_policy_comparisons: list[dict[str, Any]] = []
    actionable_signals: set[str] = set()
    signal_touch_statuses: dict[str, str] = {}
    candidate_signal_count = 0
    episode_duplicate_signal_count = 0
    last_signal_by_episode: dict[tuple[str, str, int], datetime] = {}
    excluded_signal_reasons: dict[str, int] = defaultdict(int)
    for index, row in enumerate(source_rows):
        advisory = row.get("advisory") or {}
        if not isinstance(advisory, dict):
            continue
        state = str(advisory.get("state") or "")
        if state not in ACTIONABLE_ADVISORY_STATES:
            continue
        observation_kind = str(row.get("observation_kind") or "").strip()
        if observation_kind == "minute_summary":
            continue
        candidate_signal_count += 1
        contract_issue = _signal_contract_issue(
            row,
            advisory,
            symbol_code=symbol_code,
        )
        if contract_issue is not None:
            excluded_signal_reasons[contract_issue] += 1
            continue
        try:
            entry_low = int(advisory.get("entry_price_low") or 0)
            entry_high = int(advisory.get("entry_price_high") or 0)
            entry_price = entry_high
        except (TypeError, ValueError):
            continue
        if entry_price <= 0:
            continue
        derived = advisory.get("derived")
        try:
            support_key = int(
                (derived.get("structural_support") if isinstance(derived, dict) else 0)
                or advisory.get("invalidation_price")
                or 0
            )
        except (TypeError, ValueError):
            support_key = 0
        signal_session = str(row.get("market_session") or "unknown")
        signal_venue = str(row.get("market_venue") or "unknown")
        episode_key = (signal_session, signal_venue, support_key)
        previous_episode_signal = last_signal_by_episode.get(episode_key)
        last_signal_by_episode[episode_key] = row["_observed_at"]
        if (
            previous_episode_signal is not None
            and (row["_observed_at"] - previous_episode_signal).total_seconds()
            < SIGNAL_EPISODE_DEDUP_SEC
        ):
            episode_duplicate_signal_count += 1
            continue
        actionable_signals.add(row["_observed_at"].isoformat())
        try:
            invalidation = int(advisory.get("invalidation_price") or 0)
        except (TypeError, ValueError):
            invalidation = 0
        target_price = _ceil_to_tick(entry_price * (1 + target_return_pct / 100))
        adverse_price = (
            invalidation
            if 0 < invalidation < entry_price
            else clamp_price_to_tick(entry_price * (1 + fallback_adverse_pct / 100))
        )
        signal_time = row["_observed_at"]
        reasons = advisory.get("reasons")
        calibration_policy = advisory.get("calibration_policy")
        calibration_policy = (
            calibration_policy if isinstance(calibration_policy, dict) else {}
        )
        primary_reason = (
            str(reasons[0])
            if isinstance(reasons, list) and reasons and str(reasons[0]).strip()
            else "unspecified"
        )
        same_scope_future_rows = [
            candidate
            for candidate in source_rows[index + 1 :]
            if str(candidate.get("market_session") or "unknown") == signal_session
            and str(candidate.get("market_venue") or "unknown") == signal_venue
        ]
        touch_status, touch_time = _entry_touch(
            [row, *same_scope_future_rows],
            signal_time=signal_time,
            entry_low=entry_low,
            entry_high=entry_high,
        )
        signal_touch_statuses[signal_time.isoformat()] = touch_status
        entry_scenario = (
            _classify_entry_scenario(advisory) if symbol_code == SAMSUNG_CODE else None
        )
        if symbol_code == SAMSUNG_CODE:
            episode_policy_comparisons.append(
                _build_episode_policy_comparison(
                    same_scope_future_rows,
                    signal_row=row,
                    advisory=advisory,
                    touch_status=touch_status,
                    touch_time=touch_time,
                    entry_price=entry_price,
                    market_session=signal_session,
                    market_venue=signal_venue,
                )
            )
        entry_episode_id = _entry_episode_id(row)
        latest_scope_time = (
            same_scope_future_rows[-1]["_observed_at"]
            if same_scope_future_rows
            else None
        )
        for horizon in HORIZONS_MINUTES:
            evaluation_start = touch_time or signal_time
            maturity_time = evaluation_start + timedelta(minutes=horizon)
            mature = bool(latest_scope_time and latest_scope_time >= maturity_time)
            window = _future_price_observations(
                same_scope_future_rows,
                signal_time=evaluation_start,
                maturity_time=maturity_time,
            )
            if not mature or not window:
                continue
            coverage = _coverage(window, start=evaluation_start, end=maturity_time)
            evaluation_status = touch_status
            if touch_status == "ENTRY_TOUCHED" and not coverage["coverage_passed"]:
                evaluation_status = "INSUFFICIENT_COVERAGE"
            eligible = evaluation_status == "ENTRY_TOUCHED"
            max_price = max(high_price for _, high_price, _ in window)
            min_price = min(low_price for _, _, low_price in window)
            first_hit, first_hit_at = (
                _first_hit(window, target=target_price, adverse=adverse_price)
                if eligible
                else ("not_evaluated", None)
            )
            outcomes.append(
                {
                    "signal_observed_at_kst": signal_time.isoformat(),
                    "source_line_number": row["_line_number"],
                    "market_session": signal_session,
                    "market_venue": signal_venue,
                    "advisory_state": state,
                    **(
                        {
                            "entry_scenario": entry_scenario,
                            "entry_episode_id": entry_episode_id,
                        }
                        if symbol_code == SAMSUNG_CODE
                        else {}
                    ),
                    "primary_reason": primary_reason,
                    "widget_policy_version": calibration_policy.get("policy_version"),
                    "widget_policy_effective_date": calibration_policy.get(
                        "effective_date"
                    ),
                    "required_actionable_confirmations": advisory.get(
                        "required_actionable_confirmations"
                    ),
                    "entry_touch_status": touch_status,
                    "entry_touched_at_kst": (
                        touch_time.isoformat() if touch_time is not None else None
                    ),
                    "evaluation_status": evaluation_status,
                    "evaluation_eligible": eligible,
                    "horizon_minutes": horizon,
                    "entry_reference_price": entry_price,
                    "target_price": target_price,
                    "adverse_price": adverse_price,
                    "max_price": max_price,
                    "min_price": min_price,
                    "mfe_pct": (
                        round(((max_price - entry_price) / entry_price) * 100, 6)
                        if eligible
                        else None
                    ),
                    "mae_pct": (
                        round(((min_price - entry_price) / entry_price) * 100, 6)
                        if eligible
                        else None
                    ),
                    "first_hit": first_hit,
                    "first_hit_at_kst": first_hit_at,
                    "actual_order_submitted": False,
                    "runtime_effect": False,
                    **coverage,
                }
            )

    summary = _summarize_outcomes(outcomes)
    session_coverage = _session_coverage(
        source_rows,
        expected_sessions=expected_sessions,
    )
    qualified_trading_day = bool(session_coverage) and all(
        row["qualified"] for row in session_coverage
    )
    eligible_outcomes = [
        outcome for outcome in outcomes if outcome.get("evaluation_eligible") is True
    ]
    return {
        "schema_version": 2,
        "symbol": symbol_code,
        "status": "observed" if outcomes else "no_mature_actionable_sample",
        "target_date": target_date.isoformat(),
        "source_row_count": len(source_rows),
        "candidate_signal_count": candidate_signal_count,
        "actionable_signal_count": len(actionable_signals),
        "episode_duplicate_signal_count": episode_duplicate_signal_count,
        "signal_episode_dedup_seconds": SIGNAL_EPISODE_DEDUP_SEC,
        "source_quality_excluded_signal_count": sum(excluded_signal_reasons.values()),
        "source_quality_excluded_signal_reasons": dict(
            sorted(excluded_signal_reasons.items())
        ),
        "evaluation_record_count": len(outcomes),
        "mature_outcome_count": len(eligible_outcomes),
        "entry_touch_counts": {
            status: sum(value == status for value in signal_touch_statuses.values())
            for status in ("NOT_TOUCHED", "ENTRY_TOUCHED", "ENTRY_AMBIGUOUS")
        },
        "insufficient_coverage_count": sum(
            outcome.get("evaluation_status") == "INSUFFICIENT_COVERAGE"
            for outcome in outcomes
        ),
        "session_coverage": session_coverage,
        "qualified_trading_day": qualified_trading_day,
        "summary": summary,
        "reason_cohort_summary": _summarize_reason_cohorts(outcomes),
        "scenario_cohort_summary": _summarize_scenario_cohorts(outcomes),
        "episode_exit_policy_summary": _summarize_episode_policy_comparisons(
            episode_policy_comparisons
        ),
        "episode_exit_policy_comparisons": episode_policy_comparisons,
        **(
            {
                "capacity_constrained_exit_policy_replay": (
                    _build_capacity_constrained_replay(episode_policy_comparisons)
                )
            }
            if symbol_code == SAMSUNG_CODE
            else {}
        ),
        "outcomes": outcomes,
        "metric_contract": {
            **EVALUATION_CONTRACT,
            "episode_exit_policy_comparison": (
                EVALUATION_CONTRACT["episode_exit_policy_comparison"]
                if symbol_code == SAMSUNG_CODE
                else "not_applicable_non_samsung_widget"
            ),
            "target_policy": f"entry_reference_plus_{target_return_pct:g}pct_tick_ceil",
            "adverse_policy": (
                "dynamic_invalidation_else_entry_minus_"
                f"{abs(fallback_adverse_pct):g}pct_tick_floor"
            ),
        },
        "target_return_pct": target_return_pct,
        "fallback_adverse_pct": fallback_adverse_pct,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _summarize_outcomes(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
        if outcome.get("evaluation_eligible", True) is not True:
            continue
        grouped[
            (
                str(outcome.get("market_session") or "unknown"),
                str(outcome.get("market_venue") or "unknown"),
                str(outcome.get("advisory_state") or "unknown"),
                int(outcome.get("horizon_minutes") or 0),
            )
        ].append(outcome)
    summary = []
    for (session, venue, state, horizon), items in sorted(grouped.items()):
        summary.append(
            {
                "market_session": session,
                "market_venue": venue,
                "advisory_state": state,
                "horizon_minutes": horizon,
                "sample_count": len(items),
                "equal_weight_avg_mfe_pct": round(
                    sum(item["mfe_pct"] for item in items) / len(items), 6
                ),
                "equal_weight_avg_mae_pct": round(
                    sum(item["mae_pct"] for item in items) / len(items), 6
                ),
                "target_first_count": sum(
                    item["first_hit"] == "target_first" for item in items
                ),
                "adverse_first_count": sum(
                    item["first_hit"] == "adverse_first" for item in items
                ),
                "ambiguous_count": sum(
                    item["first_hit"] == "same_observation_ambiguous" for item in items
                ),
            }
        )
    return summary


def _summarize_reason_cohorts(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
        if outcome.get("evaluation_eligible") is not True:
            continue
        grouped[
            (
                str(outcome.get("market_session") or "unknown"),
                str(outcome.get("primary_reason") or "unspecified"),
                int(outcome.get("horizon_minutes") or 0),
            )
        ].append(outcome)
    return [
        {
            "market_session": session,
            "primary_reason": reason,
            "horizon_minutes": horizon,
            "sample_count": len(items),
            "equal_weight_avg_mfe_pct": round(
                sum(float(item["mfe_pct"]) for item in items) / len(items), 6
            ),
            "equal_weight_avg_mae_pct": round(
                sum(float(item["mae_pct"]) for item in items) / len(items), 6
            ),
        }
        for (session, reason, horizon), items in sorted(grouped.items())
    ]


def _summarize_scenario_cohorts(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
        if outcome.get("evaluation_eligible") is not True:
            continue
        if not str(outcome.get("entry_scenario") or "").strip():
            continue
        grouped[
            (
                str(outcome.get("market_session") or "unknown"),
                str(outcome.get("entry_scenario") or ENTRY_SCENARIO_UNCLASSIFIED),
                int(outcome.get("horizon_minutes") or 0),
            )
        ].append(outcome)
    return [
        {
            "market_session": session,
            "entry_scenario": scenario,
            "horizon_minutes": horizon,
            "sample_count": len(items),
            "equal_weight_avg_mfe_pct": round(
                sum(float(item["mfe_pct"]) for item in items) / len(items),
                6,
            ),
            "equal_weight_avg_mae_pct": round(
                sum(float(item["mae_pct"]) for item in items) / len(items),
                6,
            ),
            "target_first_count": sum(
                item.get("first_hit") == "target_first" for item in items
            ),
            "adverse_first_count": sum(
                item.get("first_hit") == "adverse_first" for item in items
            ),
        }
        for (session, scenario, horizon), items in sorted(grouped.items())
    ]


def _summarize_episode_policy_comparisons(
    comparisons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        grouped[
            (
                str(comparison.get("market_session") or "unknown"),
                str(comparison.get("entry_scenario") or ENTRY_SCENARIO_UNCLASSIFIED),
            )
        ].append(comparison)
    summary: list[dict[str, Any]] = []
    for (session, scenario), items in sorted(grouped.items()):
        eligible = [item for item in items if item.get("comparison_eligible") is True]
        target_hits = {
            f"fixed_{target_pct:g}pct": sum(
                any(
                    result.get("policy") == f"fixed_{target_pct:g}pct"
                    and result.get("status") == "TARGET_HIT"
                    for result in item.get("fixed_target_results", [])
                    if isinstance(result, dict)
                )
                for item in eligible
            )
            for target_pct in EXIT_POLICY_TARGETS_PCT
        }
        target_hit_minutes = {
            f"fixed_{target_pct:g}pct": [
                float(result["minutes_to_hit"])
                for item in eligible
                for result in item.get("fixed_target_results", [])
                if isinstance(result, dict)
                and result.get("policy") == f"fixed_{target_pct:g}pct"
                and result.get("status") == "TARGET_HIT"
                and isinstance(result.get("minutes_to_hit"), (int, float))
            ]
            for target_pct in EXIT_POLICY_TARGETS_PCT
        }
        structural_results = [
            item.get("structural_exit_result")
            for item in eligible
            if isinstance(item.get("structural_exit_result"), dict)
        ]
        attributed = [
            result
            for result in structural_results
            if result.get("status") == "EXIT_READY_ATTRIBUTED"
            and isinstance(result.get("gross_return_pct"), (int, float))
        ]
        summary.append(
            {
                "market_session": session,
                "entry_scenario": scenario,
                "signal_episode_count": len(items),
                "comparison_eligible_count": len(eligible),
                "fixed_target_hit_counts": target_hits,
                "fixed_target_hit_rates": {
                    policy: (round(count / len(eligible), 6) if eligible else None)
                    for policy, count in target_hits.items()
                },
                "fixed_target_avg_minutes_to_hit": {
                    policy: (round(sum(values) / len(values), 3) if values else None)
                    for policy, values in target_hit_minutes.items()
                },
                "structural_exit_attributed_count": len(attributed),
                "structural_exit_unattributable_count": sum(
                    result.get("status") == "UNATTRIBUTABLE_MISSING_EPISODE_ID"
                    for result in structural_results
                ),
                "structural_exit_invalid_contract_count": sum(
                    result.get("status") == "INVALID_EXIT_CONTRACT"
                    for result in structural_results
                ),
                "structural_exit_equal_weight_avg_gross_return_pct": (
                    round(
                        sum(float(result["gross_return_pct"]) for result in attributed)
                        / len(attributed),
                        6,
                    )
                    if attributed
                    else None
                ),
                "structural_exit_avg_minutes_to_exit": (
                    round(
                        sum(float(result["minutes_to_exit"]) for result in attributed)
                        / len(attributed),
                        3,
                    )
                    if attributed
                    else None
                ),
            }
        )
    return summary


def _capacity_policy_exit(
    comparison: dict[str, Any], policy: str
) -> tuple[str, datetime | None, int | None]:
    if policy.startswith("fixed_"):
        for result in comparison.get("fixed_target_results", []):
            if not isinstance(result, dict) or result.get("policy") != policy:
                continue
            hit_at = _parse_time(result.get("hit_at_kst"))
            try:
                target_price = int(result.get("target_price") or 0)
            except (TypeError, ValueError):
                target_price = 0
            if (
                result.get("status") == "TARGET_HIT"
                and hit_at is not None
                and target_price > 0
            ):
                return "TARGET_HIT", hit_at, target_price
            return str(result.get("status") or "TARGET_RESULT_MISSING"), None, None
        return "TARGET_RESULT_MISSING", None, None
    structural = comparison.get("structural_exit_result")
    if not isinstance(structural, dict):
        return "STRUCTURAL_EXIT_RESULT_MISSING", None, None
    exit_at = _parse_time(structural.get("exit_at_kst"))
    try:
        exit_price = int(structural.get("reference_exit_price") or 0)
    except (TypeError, ValueError):
        exit_price = 0
    if (
        structural.get("status") == "EXIT_READY_ATTRIBUTED"
        and exit_at is not None
        and exit_price > 0
    ):
        return "EXIT_READY_ATTRIBUTED", exit_at, exit_price
    return str(structural.get("status") or "STRUCTURAL_EXIT_RESULT_MISSING"), None, None


def _capacity_trade_contract_valid(trade: dict[str, Any]) -> bool:
    entry_at = _parse_time(trade.get("entry_at_kst"))
    entry_price = _positive_int(trade.get("entry_price"))
    if entry_at is None or entry_price is None:
        return False
    completed = trade.get("completed") is True
    gross = trade.get("gross_return_pct")
    net = trade.get("net_return_pct")
    try:
        trade_cost = float(trade.get("round_trip_cost_pct"))
    except (TypeError, ValueError):
        return False
    if (
        not math.isfinite(trade_cost)
        or abs(trade_cost - CAPACITY_REPLAY_ROUND_TRIP_COST_PCT) > 1e-9
    ):
        return False
    if completed:
        exit_at = _parse_time(trade.get("exit_at_kst"))
        exit_price = _positive_int(trade.get("exit_price"))
        if (
            exit_at is None
            or exit_at <= entry_at
            or exit_price is None
            or not isinstance(gross, (int, float))
            or isinstance(gross, bool)
            or not isinstance(net, (int, float))
            or isinstance(net, bool)
            or not math.isfinite(float(gross))
            or not math.isfinite(float(net))
            or trade.get("unresolved_terminal_mark_return_pct") is not None
        ):
            return False
        expected_gross = ((exit_price - entry_price) / entry_price) * 100
        expected_net = expected_gross - CAPACITY_REPLAY_ROUND_TRIP_COST_PCT
        return (
            abs(float(gross) - expected_gross) <= 1e-5
            and abs(float(net) - expected_net) <= 1e-5
        )
    if not (
        trade.get("completed") is False
        and trade.get("exit_at_kst") is None
        and trade.get("exit_price") is None
        and gross is None
        and net is None
    ):
        return False
    terminal_at = _parse_time(trade.get("observed_window_end_at_kst"))
    terminal_price = _positive_int(trade.get("observed_window_end_price"))
    terminal_mark = trade.get("unresolved_terminal_mark_return_pct")
    if (
        terminal_at is None
        or terminal_at <= entry_at
        or terminal_price is None
        or not isinstance(terminal_mark, (int, float))
        or isinstance(terminal_mark, bool)
        or not math.isfinite(float(terminal_mark))
    ):
        return False
    expected_terminal_mark = ((terminal_price - entry_price) / entry_price) * 100
    return abs(float(terminal_mark) - expected_terminal_mark) <= 1e-5


def _summarize_capacity_arm_trades(
    trades: list[dict[str, Any]],
    *,
    selected_entry_count: int,
    overlap_skipped_count: int,
    invalid_candidate_count: int,
) -> dict[str, Any]:
    completed = [
        trade
        for trade in trades
        if trade.get("completed") is True
        and isinstance(trade.get("gross_return_pct"), (int, float))
        and isinstance(trade.get("net_return_pct"), (int, float))
    ]
    unresolved = [trade for trade in trades if trade.get("completed") is not True]
    gross_values = [float(trade["gross_return_pct"]) for trade in completed]
    net_values = [float(trade["net_return_pct"]) for trade in completed]
    return {
        "eligible_candidate_count": selected_entry_count + overlap_skipped_count,
        "selected_entry_count": selected_entry_count,
        "overlap_skipped_count": overlap_skipped_count,
        "invalid_or_insufficient_candidate_count": invalid_candidate_count,
        "completed_trade_count": len(completed),
        "unresolved_position_count": len(unresolved),
        "completed_equal_weight_avg_gross_return_pct": (
            round(sum(gross_values) / len(gross_values), 6) if gross_values else None
        ),
        "completed_equal_weight_avg_profit_pct": (
            round(sum(net_values) / len(net_values), 6) if net_values else None
        ),
        "completed_simple_sum_profit_pct": (
            round(sum(net_values), 6) if net_values else None
        ),
        "diagnostic_win_rate": (
            round(sum(value > 0 for value in net_values) / len(net_values), 6)
            if net_values
            else None
        ),
        "decision_evidence_complete": bool(trades) and not unresolved,
    }


def _build_capacity_constrained_replay(
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Replay each exit arm with one independent position slot per session.

    This removes overlapping-signal inflation.  Arms remain independent and a
    signal must be exactly touched before its original 60-second validity ends.
    An unresolved position occupies the slot through the observed session end.
    """
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        grouped[
            (
                str(comparison.get("market_session") or "unknown"),
                str(comparison.get("market_venue") or "unknown"),
            )
        ].append(comparison)
    arms: list[dict[str, Any]] = []
    for (session, venue), items in sorted(grouped.items()):
        ordered = sorted(
            items,
            key=lambda item: (
                str(item.get("entry_touched_at_kst") or ""),
                int(item.get("source_line_number") or 0),
            ),
        )
        valid_candidates = [
            item
            for item in ordered
            if item.get("comparison_eligible") is True
            and item.get("entry_touch_within_signal_validity") is True
            and _parse_time(item.get("entry_touched_at_kst")) is not None
            and _positive_int(item.get("entry_reference_price")) is not None
        ]
        invalid_candidate_count = len(ordered) - len(valid_candidates)
        for policy in CAPACITY_POLICY_IDS:
            available_after: datetime | None = None
            unresolved_position = False
            selected_entry_count = 0
            overlap_skipped_count = 0
            trades: list[dict[str, Any]] = []
            for candidate in valid_candidates:
                entry_at = _parse_time(candidate.get("entry_touched_at_kst"))
                entry_price = _positive_int(candidate.get("entry_reference_price"))
                if entry_at is None or entry_price is None:
                    continue
                if unresolved_position or (
                    available_after is not None and entry_at <= available_after
                ):
                    overlap_skipped_count += 1
                    continue
                selected_entry_count += 1
                exit_status, exit_at, exit_price = _capacity_policy_exit(
                    candidate,
                    policy,
                )
                completed = bool(
                    exit_at is not None
                    and exit_price is not None
                    and exit_at > entry_at
                )
                gross_return_pct = (
                    round(((exit_price - entry_price) / entry_price) * 100, 6)
                    if completed and exit_price is not None
                    else None
                )
                net_return_pct = (
                    round(
                        gross_return_pct - CAPACITY_REPLAY_ROUND_TRIP_COST_PCT,
                        6,
                    )
                    if gross_return_pct is not None
                    else None
                )
                try:
                    terminal_price = int(
                        candidate.get("observed_window_end_price") or 0
                    )
                except (TypeError, ValueError):
                    terminal_price = 0
                terminal_mark_return_pct = (
                    round(((terminal_price - entry_price) / entry_price) * 100, 6)
                    if not completed and terminal_price > 0
                    else None
                )
                trades.append(
                    {
                        "entry_episode_id": candidate.get("entry_episode_id"),
                        "entry_scenario": candidate.get("entry_scenario"),
                        "entry_at_kst": entry_at.isoformat(),
                        "entry_price": entry_price,
                        "exit_status": exit_status,
                        "exit_at_kst": exit_at.isoformat() if exit_at else None,
                        "exit_price": exit_price,
                        "completed": completed,
                        "gross_return_pct": gross_return_pct,
                        "round_trip_cost_pct": CAPACITY_REPLAY_ROUND_TRIP_COST_PCT,
                        "net_return_pct": net_return_pct,
                        "observed_window_end_at_kst": candidate.get(
                            "observed_window_end_at_kst"
                        ),
                        "observed_window_end_price": (
                            terminal_price if terminal_price > 0 else None
                        ),
                        "unresolved_terminal_mark_return_pct": (
                            terminal_mark_return_pct
                        ),
                    }
                )
                if completed:
                    available_after = exit_at
                else:
                    unresolved_position = True
            arms.append(
                {
                    "market_session": session,
                    "market_venue": venue,
                    "policy": policy,
                    **_summarize_capacity_arm_trades(
                        trades,
                        selected_entry_count=selected_entry_count,
                        overlap_skipped_count=overlap_skipped_count,
                        invalid_candidate_count=invalid_candidate_count,
                    ),
                    "trades": trades,
                }
            )
    return {
        "schema_version": 1,
        "status": "observed" if arms else "no_eligible_episode",
        "position_capacity_per_session_policy": 1,
        "round_trip_cost_pct": CAPACITY_REPLAY_ROUND_TRIP_COST_PCT,
        "fill_assumption": CAPACITY_REPLAY_CONTRACT["fill_assumption"],
        "cost_policy": CAPACITY_REPLAY_CONTRACT["cost_policy"],
        "same_time_entry_after_exit_allowed": False,
        "policy_arms_compared_independently": True,
        "unresolved_positions_excluded_from_completed_profit_metrics": True,
        "arms": arms,
        "metric_contract": CAPACITY_REPLAY_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _build_rolling_capacity_replay(reports: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "trades": [],
            "selected_entry_count": 0,
            "overlap_skipped_count": 0,
            "invalid_candidate_count": 0,
            "source_dates": set(),
        }
    )
    accepted_report_count = 0
    for report in reports:
        replay = report.get("capacity_constrained_exit_policy_replay")
        metric_contract = (
            replay.get("metric_contract") if isinstance(replay, dict) else None
        )
        try:
            round_trip_cost_pct = float(
                replay.get("round_trip_cost_pct") if isinstance(replay, dict) else None
            )
        except (TypeError, ValueError):
            round_trip_cost_pct = -1
        if (
            not isinstance(replay, dict)
            or replay.get("schema_version") != 1
            or replay.get("position_capacity_per_session_policy") != 1
            or abs(round_trip_cost_pct - CAPACITY_REPLAY_ROUND_TRIP_COST_PCT) > 1e-9
            or not isinstance(metric_contract, dict)
            or metric_contract.get("decision_authority")
            != "widget_advisory_evaluation_only"
            or replay.get("runtime_effect") is not False
            or replay.get("actual_order_submitted") is not False
            or replay.get("broker_order_forbidden") is not True
        ):
            continue
        accepted_report_count += 1
        target_date = str(report.get("target_date") or "")
        for arm in replay.get("arms", []):
            if not isinstance(arm, dict):
                continue
            policy = str(arm.get("policy") or "")
            if policy not in CAPACITY_POLICY_IDS:
                continue
            try:
                selected_entry_count = int(arm.get("selected_entry_count") or 0)
                overlap_skipped_count = int(arm.get("overlap_skipped_count") or 0)
                invalid_candidate_count = int(
                    arm.get("invalid_or_insufficient_candidate_count") or 0
                )
            except (TypeError, ValueError):
                continue
            if (
                min(
                    selected_entry_count,
                    overlap_skipped_count,
                    invalid_candidate_count,
                )
                < 0
            ):
                continue
            valid_trades = [
                trade
                for trade in arm.get("trades", [])
                if isinstance(trade, dict) and _capacity_trade_contract_valid(trade)
            ]
            try:
                eligible_candidate_count = int(arm.get("eligible_candidate_count") or 0)
            except (TypeError, ValueError):
                continue
            if (
                len(valid_trades) != selected_entry_count
                or eligible_candidate_count
                != selected_entry_count + overlap_skipped_count
            ):
                continue
            key = (
                str(arm.get("market_session") or "unknown"),
                str(arm.get("market_venue") or "unknown"),
                policy,
            )
            bucket = grouped[key]
            bucket["selected_entry_count"] += selected_entry_count
            bucket["overlap_skipped_count"] += overlap_skipped_count
            bucket["invalid_candidate_count"] += invalid_candidate_count
            if target_date:
                bucket["source_dates"].add(target_date)
            for trade in valid_trades:
                bucket["trades"].append(
                    {**trade, "source_target_date": target_date or None}
                )
    arms: list[dict[str, Any]] = []
    for (session, venue, policy), bucket in sorted(grouped.items()):
        trades = bucket["trades"]
        arms.append(
            {
                "market_session": session,
                "market_venue": venue,
                "policy": policy,
                "source_trading_day_count": len(bucket["source_dates"]),
                **_summarize_capacity_arm_trades(
                    trades,
                    selected_entry_count=bucket["selected_entry_count"],
                    overlap_skipped_count=bucket["overlap_skipped_count"],
                    invalid_candidate_count=bucket["invalid_candidate_count"],
                ),
                "trades": trades,
            }
        )
    return {
        "schema_version": 1,
        "status": "observed" if arms else "no_eligible_episode",
        "source_daily_report_count": accepted_report_count,
        "position_capacity_per_session_policy": 1,
        "round_trip_cost_pct": CAPACITY_REPLAY_ROUND_TRIP_COST_PCT,
        "fill_assumption": CAPACITY_REPLAY_CONTRACT["fill_assumption"],
        "cost_policy": CAPACITY_REPLAY_CONTRACT["cost_policy"],
        "policy_arms_compared_independently": True,
        "unresolved_positions_excluded_from_completed_profit_metrics": True,
        "arms": arms,
        "metric_contract": {
            **CAPACITY_REPLAY_CONTRACT,
            "window_policy": (
                "rolling_qualified_trading_days_session_separated_one_position_per_exit_policy"
            ),
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _day_clustered_summary(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clustered: dict[tuple[str, str, str, int], list[tuple[float, float]]] = defaultdict(
        list
    )
    for report in reports:
        daily: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
        for outcome in report.get("outcomes", []):
            if (
                not isinstance(outcome, dict)
                or outcome.get("evaluation_eligible") is not True
            ):
                continue
            key = (
                str(outcome.get("market_session") or "unknown"),
                str(outcome.get("market_venue") or "unknown"),
                str(outcome.get("advisory_state") or "unknown"),
                int(outcome.get("horizon_minutes") or 0),
            )
            daily[key].append(outcome)
        for key, items in daily.items():
            clustered[key].append(
                (
                    sum(float(item["mfe_pct"]) for item in items) / len(items),
                    sum(float(item["mae_pct"]) for item in items) / len(items),
                )
            )
    return [
        {
            "market_session": session,
            "market_venue": venue,
            "advisory_state": state,
            "horizon_minutes": horizon,
            "qualified_trading_day_count": len(day_values),
            "day_clustered_avg_mfe_pct": round(
                sum(value[0] for value in day_values) / len(day_values), 6
            ),
            "day_clustered_avg_mae_pct": round(
                sum(value[1] for value in day_values) / len(day_values), 6
            ),
        }
        for (session, venue, state, horizon), day_values in sorted(clustered.items())
    ]


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def build_rolling_report(
    output_dir: Path,
    *,
    as_of_date: date,
    report_prefix: str = "samsung_widget_advisory_evaluation",
    symbol_code: str = SAMSUNG_CODE,
    target_return_pct: float = TARGET_RETURN_PCT,
    fallback_adverse_pct: float = FALLBACK_ADVERSE_PCT,
) -> dict[str, Any]:
    if target_return_pct <= 0:
        raise ValueError("target_return_pct_must_be_positive")
    if fallback_adverse_pct >= 0:
        raise ValueError("fallback_adverse_pct_must_be_negative")
    daily_reports: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob(f"{report_prefix}_*.json")):
        if path.name.endswith("_rolling_60d.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            target_date = date.fromisoformat(str(payload.get("target_date") or ""))
        except (OSError, ValueError, TypeError):
            continue
        report_symbol = payload.get("symbol")
        legacy_samsung_symbol = (
            symbol_code == SAMSUNG_CODE
            and report_prefix == "samsung_widget_advisory_evaluation"
            and report_symbol in {None, ""}
        )
        metric_contract = payload.get("metric_contract")
        if not (
            CLEAN_BASELINE_DATE <= target_date <= as_of_date
            and is_krx_trading_day(target_date)
            and payload.get("schema_version") == 2
            and (report_symbol == symbol_code or legacy_samsung_symbol)
            and payload.get("status") in {"observed", "no_mature_actionable_sample"}
            and _positive_int(payload.get("source_row_count")) is not None
            and payload.get("runtime_effect") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
            and isinstance(metric_contract, dict)
            and metric_contract.get("decision_authority")
            == "widget_advisory_evaluation_only"
        ):
            continue
        try:
            report_target_return = float(payload.get("target_return_pct"))
        except (TypeError, ValueError):
            report_target_return = TARGET_RETURN_PCT if legacy_samsung_symbol else None
        try:
            report_fallback_adverse = float(payload.get("fallback_adverse_pct"))
        except (TypeError, ValueError):
            report_fallback_adverse = (
                FALLBACK_ADVERSE_PCT if legacy_samsung_symbol else None
            )
        if (
            report_target_return is None
            or abs(report_target_return - target_return_pct) > 1e-9
            or report_fallback_adverse is None
            or abs(report_fallback_adverse - fallback_adverse_pct) > 1e-9
        ):
            continue
        daily_reports.append(payload)
    calendar_reports = daily_reports[-60:]
    qualified_reports = [
        report
        for report in daily_reports
        if report.get("qualified_trading_day") is True
    ][-60:]
    outcomes = [
        outcome
        for report in qualified_reports
        for outcome in report.get("outcomes", [])
        if isinstance(outcome, dict) and outcome.get("evaluation_eligible") is True
    ]
    episode_policy_comparisons = [
        comparison
        for report in qualified_reports
        for comparison in report.get("episode_exit_policy_comparisons", [])
        if isinstance(comparison, dict)
    ]
    return {
        "schema_version": 2,
        "symbol": symbol_code,
        "status": "observed" if outcomes else "no_mature_actionable_sample",
        "as_of_date": as_of_date.isoformat(),
        "calendar_artifact_count": len(calendar_reports),
        "qualified_trading_day_count": len(qualified_reports),
        "trading_day_count": len(qualified_reports),
        "sample_floor_met": len(qualified_reports) >= 60,
        "mature_outcome_count": len(outcomes),
        "summary": _summarize_outcomes(outcomes),
        "day_clustered_summary": _day_clustered_summary(qualified_reports),
        "reason_cohort_summary": _summarize_reason_cohorts(outcomes),
        "scenario_cohort_summary": _summarize_scenario_cohorts(outcomes),
        "episode_exit_policy_summary": _summarize_episode_policy_comparisons(
            episode_policy_comparisons
        ),
        "episode_exit_policy_comparison_count": len(episode_policy_comparisons),
        **(
            {
                "capacity_constrained_exit_policy_replay": (
                    _build_rolling_capacity_replay(qualified_reports)
                )
            }
            if symbol_code == SAMSUNG_CODE
            else {}
        ),
        "daily_source_paths": [
            f"{report_prefix}_{report['target_date']}.json"
            for report in qualified_reports
        ],
        "metric_contract": {
            **EVALUATION_CONTRACT,
            "episode_exit_policy_comparison": (
                EVALUATION_CONTRACT["episode_exit_policy_comparison"]
                if symbol_code == SAMSUNG_CODE
                else "not_applicable_non_samsung_widget"
            ),
            "target_policy": f"entry_reference_plus_{target_return_pct:g}pct_tick_ceil",
            "adverse_policy": (
                "dynamic_invalidation_else_entry_minus_"
                f"{abs(fallback_adverse_pct):g}pct_tick_floor"
            ),
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _resolve_default_target_date(*, now: datetime | None = None) -> date:
    """Choose the completed trading date for normal and persistent timers."""
    current = (now or datetime.now(KST)).astimezone(KST)
    if current.time().replace(tzinfo=None) >= NXT_AFTERMARKET_END:
        return current.date()
    return previous_krx_trading_date(current.date())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--observation-dir", type=Path, default=DEFAULT_OBSERVATION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def _discover_backfill_dates(
    observation_dir: Path, output_dir: Path, *, through_date: date
) -> list[date]:
    missed_dates: list[date] = []
    for observation_path in sorted(
        observation_dir.glob("samsung_widget_advisory_*.jsonl")
    ):
        try:
            observation_date = datetime.strptime(
                observation_path.stem.rsplit("_", 1)[-1], "%Y%m%d"
            ).date()
        except ValueError:
            continue
        output_path = output_dir / (
            f"samsung_widget_advisory_evaluation_{observation_date.isoformat()}.json"
        )
        if observation_date <= through_date and not output_path.exists():
            missed_dates.append(observation_date)
    return sorted(set(missed_dates))


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else _resolve_default_target_date()
    )
    source_path = args.observation_dir / (
        f"samsung_widget_advisory_{target_date.strftime('%Y%m%d')}.jsonl"
    )
    report = build_daily_evaluation(_load_rows(source_path), target_date=target_date)
    rolling = build_rolling_report(args.output_dir, as_of_date=target_date)
    if args.write:
        work_dates = [target_date]
        if not args.target_date:
            missed_dates = _discover_backfill_dates(
                args.observation_dir, args.output_dir, through_date=target_date
            )
            work_dates = sorted(set([*missed_dates, target_date]))
        for work_date in work_dates:
            work_source = args.observation_dir / (
                f"samsung_widget_advisory_{work_date.strftime('%Y%m%d')}.jsonl"
            )
            work_report = build_daily_evaluation(
                _load_rows(work_source), target_date=work_date
            )
            daily_path = args.output_dir / (
                f"samsung_widget_advisory_evaluation_{work_date.isoformat()}.json"
            )
            _atomic_write(daily_path, work_report)
        # Rebuild rolling after the daily report is visible.
        rolling = build_rolling_report(args.output_dir, as_of_date=target_date)
        _atomic_write(
            args.output_dir / "samsung_widget_advisory_evaluation_rolling_60d.json",
            rolling,
        )
    else:
        print(json.dumps({"daily": report, "rolling": rolling}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
