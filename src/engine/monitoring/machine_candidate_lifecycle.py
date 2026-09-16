"""Shared discovery and long-horizon pruning for widget/episode candidates.

The catalog has no cardinality cap.  It still requires one completed daily
recommendation generation and only prunes research candidates after a mature,
cost-adjusted history.  Established live symbols are never removed here.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

DAILY_RECOMMENDATIONS = DATA_DIR / "daily_recommendations_v2.csv"
DAILY_RECOMMENDATION_DIAGNOSTICS = (
    DATA_DIR / "daily_recommendations_v2_diagnostics.json"
)
WIDGET_REPORT_DIR = DATA_DIR / "report" / "widget_symbol_signal_policy_research"
EPISODE_REPORT_DIR = (
    DATA_DIR / "report" / "low_price_two_leg_expanded_candidate_research"
)
MIN_LONG_HORIZON_TRADING_DAYS = 40


def completed_daily_recommendation_symbols(
    observed_date: date,
    *,
    csv_path: Path = DAILY_RECOMMENDATIONS,
    diagnostics_path: Path = DAILY_RECOMMENDATION_DIAGNOSTICS,
    maximum_close: int | None = None,
    excluded_symbols: set[str] | frozenset[str] = frozenset(),
) -> tuple[date | None, dict[str, str]]:
    """Return every symbol in one integrity-checked completed generation."""

    try:
        diagnostic = json.loads(diagnostics_path.read_text(encoding="utf-8"))
        source_date = date.fromisoformat(str(diagnostic.get("latest_date") or ""))
        selected_count = int(diagnostic.get("selected_count", -1))
    except (OSError, ValueError, TypeError, AttributeError):
        return None, {}
    if source_date > observed_date or selected_count < 0:
        return None, {}
    try:
        handle = csv_path.open(encoding="utf-8-sig", newline="")
    except OSError:
        return None, {}
    with handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != selected_count:
        return None, {}
    symbols: dict[str, tuple[int, str]] = {}
    for row in rows:
        try:
            row_date = date.fromisoformat(str(row.get("date") or ""))
            rank = int(float(row.get("score_rank") or 999_999))
            close = int(float(row.get("close") or 0))
        except (TypeError, ValueError):
            return None, {}
        raw_symbol = str(row.get("code") or "").strip()
        symbol = raw_symbol.zfill(6)
        name = str(row.get("name") or "").strip()
        if (
            row_date != source_date
            or not raw_symbol
            or len(symbol) != 6
            or not symbol.isdigit()
            or not name
            or close <= 0
        ):
            return None, {}
        if symbol in excluded_symbols or (
            maximum_close is not None and close > maximum_close
        ):
            continue
        current = symbols.get(symbol)
        if current is None or rank < current[0]:
            symbols[symbol] = (rank, name)
    return source_date, {
        symbol: name
        for symbol, (_, name) in sorted(
            symbols.items(), key=lambda item: (item[1][0], item[0])
        )
    }


def _latest_prior_report(directory: Path, observed_date: date) -> dict[str, Any] | None:
    candidates: list[tuple[date, Path]] = []
    for path in directory.glob("*.json"):
        try:
            report_date = date.fromisoformat(path.stem[-10:])
        except ValueError:
            continue
        if report_date < observed_date:
            candidates.append((report_date, path))
    if not candidates:
        return None
    try:
        payload = json.loads(max(candidates)[1].read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def widget_long_term_pruned_symbols(
    observed_date: date, *, report_dir: Path = WIDGET_REPORT_DIR
) -> dict[str, str]:
    """Prune only mature non-established candidates with non-positive edge."""

    report = _latest_prior_report(report_dir, observed_date)
    if (
        not report
        or report.get("status") != "complete"
        or int(report.get("trading_date_count") or 0) < MIN_LONG_HORIZON_TRADING_DAYS
    ):
        return {}
    origins = report.get("symbol_origins") or {}
    results = report.get("symbols") or {}
    pruned: dict[str, str] = {}
    for symbol, result in results.items():
        if origins.get(symbol) == "established_widget_symbol" or not isinstance(
            result, dict
        ):
            continue
        calibration = result.get("calibration") or {}
        holdout = result.get("holdout") or {}
        try:
            calibration_count = int(calibration.get("episode_count") or 0)
            holdout_count = int(holdout.get("episode_count") or 0)
            calibration_ev = float(calibration.get("notional_weighted_ev_pct"))
            holdout_ev = float(holdout.get("notional_weighted_ev_pct"))
        except (TypeError, ValueError):
            continue
        if (
            calibration_count >= 10
            and holdout_count >= 4
            and calibration_ev <= 0.0
            and holdout_ev <= 0.0
        ):
            pruned[str(symbol)] = "mature_calibration_and_holdout_ev_nonpositive"
    return pruned


def episode_long_term_pruned_symbols(
    observed_date: date, *, report_dir: Path = EPISODE_REPORT_DIR
) -> dict[str, str]:
    """Remove a dynamic symbol only when every mature session is non-positive."""

    report = _latest_prior_report(report_dir, observed_date)
    if (
        not report
        or int(report.get("trading_date_count") or 0) < MIN_LONG_HORIZON_TRADING_DAYS
    ):
        return {}
    recommended = {
        str(row.get("symbol") or "")
        for row in report.get("recommendations") or []
        if isinstance(row, dict)
    }
    by_symbol: dict[str, list[float]] = {}
    for result in (report.get("profiles") or {}).values():
        if not isinstance(result, dict) or result.get("discovery_lane") != "new_symbol":
            continue
        symbol = str(result.get("symbol") or "")
        metric = (result.get("best_diagnostic_candidate") or {}).get(
            "calibration_full"
        ) or {}
        try:
            days = int(metric.get("source_valid_observation_days") or 0)
            episodes = int(metric.get("signal_episodes") or 0)
            completed = int(metric.get("completed_legs") or 0)
            ev = float(metric.get("notional_weighted_ev_pct"))
        except (TypeError, ValueError):
            continue
        if days >= MIN_LONG_HORIZON_TRADING_DAYS and episodes >= 6 and completed >= 8:
            by_symbol.setdefault(symbol, []).append(ev)
    return {
        symbol: "all_mature_session_calibration_ev_nonpositive"
        for symbol, values in by_symbol.items()
        if symbol not in recommended and values and max(values) <= 0.0
    }
