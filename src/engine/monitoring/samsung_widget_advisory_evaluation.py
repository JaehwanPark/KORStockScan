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
    DEFAULT_OBSERVATION_DIR,
    KST,
)
from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size

DEFAULT_OUTPUT_DIR = Path("data/report/samsung_widget_advisory_evaluation")
HORIZONS_MINUTES = (1, 3, 5, 10, 20, 30, 60)
TARGET_RETURN_PCT = 0.5
FALLBACK_ADVERSE_PCT = -0.3

EVALUATION_CONTRACT = {
    "metric_role": "counterfactual_observation",
    "decision_authority": "widget_advisory_evaluation_only",
    "window_policy": "daily_and_rolling_60_trading_days",
    "sample_floor": "60_trading_days_before_threshold_judgment",
    "primary_decision_metric": "none_counterfactual_mfe_mae",
    "source_quality_gate": "mature_same_day_minute_observation_window",
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
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


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


def build_daily_evaluation(
    rows: list[dict[str, Any]], *, target_date: date
) -> dict[str, Any]:
    source_rows = [row for row in rows if row["_observed_at"].date() == target_date]
    outcomes: list[dict[str, Any]] = []
    actionable_signals: set[str] = set()
    for index, row in enumerate(source_rows):
        advisory = row.get("advisory") or {}
        if not isinstance(advisory, dict):
            continue
        state = str(advisory.get("state") or "")
        if state not in {"ENTRY_READY", "ENTRY_CAUTION"}:
            continue
        observation_kind = str(row.get("observation_kind") or "").strip()
        if observation_kind and observation_kind != "state_transition":
            continue
        try:
            entry_price = int(
                advisory.get("entry_price_high")
                or advisory.get("entry_price_low")
                or row["_current_price"]
            )
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
        signal_session = str(row.get("market_session") or "unknown")
        signal_venue = str(row.get("market_venue") or "unknown")
        same_scope_future_rows = [
            candidate
            for candidate in source_rows[index + 1 :]
            if str(candidate.get("market_session") or "unknown") == signal_session
            and str(candidate.get("market_venue") or "unknown") == signal_venue
        ]
        latest_scope_time = (
            same_scope_future_rows[-1]["_observed_at"]
            if same_scope_future_rows
            else None
        )
        for horizon in HORIZONS_MINUTES:
            maturity_time = signal_time + timedelta(minutes=horizon)
            mature = bool(latest_scope_time and latest_scope_time >= maturity_time)
            window = _future_price_observations(
                same_scope_future_rows,
                signal_time=signal_time,
                maturity_time=maturity_time,
            )
            if not mature or not window:
                continue
            max_price = max(high_price for _, high_price, _ in window)
            min_price = min(low_price for _, _, low_price in window)
            first_hit, first_hit_at = _first_hit(
                window, target=target_price, adverse=adverse_price
            )
            outcomes.append(
                {
                    "signal_observed_at_kst": signal_time.isoformat(),
                    "source_line_number": row["_line_number"],
                    "market_session": signal_session,
                    "market_venue": signal_venue,
                    "advisory_state": state,
                    "horizon_minutes": horizon,
                    "entry_reference_price": entry_price,
                    "target_price": target_price,
                    "adverse_price": adverse_price,
                    "max_price": max_price,
                    "min_price": min_price,
                    "mfe_pct": round(
                        ((max_price - entry_price) / entry_price) * 100, 6
                    ),
                    "mae_pct": round(
                        ((min_price - entry_price) / entry_price) * 100, 6
                    ),
                    "first_hit": first_hit,
                    "first_hit_at_kst": first_hit_at,
                    "actual_order_submitted": False,
                    "runtime_effect": False,
                }
            )

    summary = _summarize_outcomes(outcomes)
    return {
        "schema_version": 1,
        "status": "observed" if outcomes else "no_mature_actionable_sample",
        "target_date": target_date.isoformat(),
        "source_row_count": len(source_rows),
        "actionable_signal_count": len(actionable_signals),
        "mature_outcome_count": len(outcomes),
        "summary": summary,
        "outcomes": outcomes,
        "metric_contract": EVALUATION_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _summarize_outcomes(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
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
        if target_date <= as_of_date and int(payload.get("source_row_count") or 0) > 0:
            daily_reports.append(payload)
    daily_reports = daily_reports[-60:]
    outcomes = [
        outcome
        for report in daily_reports
        for outcome in report.get("outcomes", [])
        if isinstance(outcome, dict)
    ]
    return {
        "schema_version": 1,
        "status": "observed" if outcomes else "no_mature_actionable_sample",
        "as_of_date": as_of_date.isoformat(),
        "trading_day_count": len(daily_reports),
        "sample_floor_met": len(daily_reports) >= 60,
        "mature_outcome_count": len(outcomes),
        "summary": _summarize_outcomes(outcomes),
        "daily_source_paths": [
            f"samsung_widget_advisory_evaluation_{report['target_date']}.json"
            for report in daily_reports
        ],
        "metric_contract": EVALUATION_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=datetime.now(KST).date().isoformat())
    parser.add_argument("--observation-dir", type=Path, default=DEFAULT_OBSERVATION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_date = date.fromisoformat(args.target_date)
    source_path = (
        args.observation_dir
        / f"samsung_widget_advisory_{target_date.strftime('%Y%m%d')}.jsonl"
    )
    report = build_daily_evaluation(_load_rows(source_path), target_date=target_date)
    rolling = build_rolling_report(args.output_dir, as_of_date=target_date)
    if args.write:
        daily_path = (
            args.output_dir
            / f"samsung_widget_advisory_evaluation_{target_date.isoformat()}.json"
        )
        _atomic_write(daily_path, report)
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
