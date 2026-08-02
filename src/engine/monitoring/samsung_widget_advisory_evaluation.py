"""Evaluate widget-only Samsung advisories from compact minute observations."""

from __future__ import annotations

import argparse
import json
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
HORIZONS_MINUTES = (1, 3, 5, 10, 20, 30, 60)
TARGET_RETURN_PCT = 0.5
FALLBACK_ADVERSE_PCT = -0.3
MIN_COVERAGE_RATIO = 0.80
MAX_COVERAGE_GAP_SEC = 120
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
    "target_policy": "entry_reference_plus_0.5pct_tick_ceil",
    "adverse_policy": "dynamic_invalidation_else_entry_minus_0.3pct_tick_floor",
    "forbidden_uses": [
        "real_order_submission",
        "real_execution_quality_approval",
        "automatic_threshold_or_runtime_apply",
        "provider_or_bot_change",
        "realized_pnl_aggregation",
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


def _signal_contract_issue(row: dict[str, Any], advisory: object) -> str | None:
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
    expected_request_code = f"{SAMSUNG_CODE}_NX" if venue == "NXT" else SAMSUNG_CODE
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


def _session_coverage(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    total_grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in source_rows:
        session = str(row.get("market_session") or "unknown")
        venue = str(row.get("market_venue") or "unknown")
        if session not in SESSION_EXPECTED_MINUTES:
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
    for session, expected in SESSION_EXPECTED_MINUTES.items():
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
    rows: list[dict[str, Any]], *, target_date: date
) -> dict[str, Any]:
    source_rows = [row for row in rows if row["_observed_at"].date() == target_date]
    outcomes: list[dict[str, Any]] = []
    actionable_signals: set[str] = set()
    signal_touch_statuses: dict[str, str] = {}
    candidate_signal_count = 0
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
        contract_issue = _signal_contract_issue(row, advisory)
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
        actionable_signals.add(row["_observed_at"].isoformat())
        try:
            invalidation = int(advisory.get("invalidation_price") or 0)
        except (TypeError, ValueError):
            invalidation = 0
        target_price = _ceil_to_tick(entry_price * (1 + TARGET_RETURN_PCT / 100))
        adverse_price = (
            invalidation
            if 0 < invalidation < entry_price
            else clamp_price_to_tick(entry_price * (1 + FALLBACK_ADVERSE_PCT / 100))
        )
        signal_time = row["_observed_at"]
        reasons = advisory.get("reasons")
        primary_reason = (
            str(reasons[0])
            if isinstance(reasons, list) and reasons and str(reasons[0]).strip()
            else "unspecified"
        )
        signal_session = str(row.get("market_session") or "unknown")
        signal_venue = str(row.get("market_venue") or "unknown")
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
                    "primary_reason": primary_reason,
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
    session_coverage = _session_coverage(source_rows)
    qualified_trading_day = bool(session_coverage) and all(
        row["qualified"] for row in session_coverage
    )
    eligible_outcomes = [
        outcome for outcome in outcomes if outcome.get("evaluation_eligible") is True
    ]
    return {
        "schema_version": 2,
        "status": "observed" if outcomes else "no_mature_actionable_sample",
        "target_date": target_date.isoformat(),
        "source_row_count": len(source_rows),
        "candidate_signal_count": candidate_signal_count,
        "actionable_signal_count": len(actionable_signals),
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
        "outcomes": outcomes,
        "metric_contract": EVALUATION_CONTRACT,
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


def build_rolling_report(output_dir: Path, *, as_of_date: date) -> dict[str, Any]:
    daily_reports: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob("samsung_widget_advisory_evaluation_*.json")):
        if path.name.endswith("_rolling_60d.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            target_date = date.fromisoformat(str(payload.get("target_date") or ""))
        except (OSError, ValueError, TypeError):
            continue
        if (
            target_date <= as_of_date
            and is_krx_trading_day(target_date)
            and int(payload.get("source_row_count") or 0) > 0
        ):
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
    return {
        "schema_version": 2,
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
        "daily_source_paths": [
            f"samsung_widget_advisory_evaluation_{report['target_date']}.json"
            for report in qualified_reports
        ],
        "metric_contract": EVALUATION_CONTRACT,
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
