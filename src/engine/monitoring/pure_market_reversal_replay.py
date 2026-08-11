"""Walk-forward reversal backtest using market data only.

Objective
---------
Find a causal long entry as close as practicable to the end of a decline, then
exit while preserving as much of the subsequent rebound as possible.  Historic
widget signals, AI decisions, strategy states, thresholds, and orders are
forbidden inputs.  Future bars are used only for ex-post opportunity and
capture-error labels, never for policy selection or a simulated decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo

DEFAULT_MARKET_DIR = Path("data/market_data/pure_market_reversal")
DEFAULT_WIDGET_OBSERVATION_DIR = Path("data/report/samsung_widget_advisory_observation")
DEFAULT_OUTPUT_DIR = Path("data/report/pure_market_reversal_replay")
SAMSUNG_CODE = "005930"
KST = ZoneInfo("Asia/Seoul")
OFFICIAL_MARKET_DATA_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-11T10:10:15+09:00",
    "inspected_paths": [
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core/client.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contract": "POST /api/dostk/chart; api-id=ka10080",
}
COHORTS = ("KRX", "NXT")
CLEAN_TUNING_BASELINE_DATE = date(2026, 6, 5)
MIN_QUALIFIED_TRADING_DAYS = 46
DEFAULT_COST_SCENARIOS_PCT = (0.10, 0.20, 0.30, 0.40)
COVERAGE_MIN_BARS = {
    "KRX": {"KRX_REGULAR": 300},
    "NXT": {
        "NXT_PREMARKET": 30,
        "NXT_REGULAR": 300,
        "NXT_AFTERMARKET": 180,
    },
}
OPPORTUNITY_LABEL_CONTRACT = {
    "role": "ex_post_diagnostic_only",
    "local_low_radius_bars": 2,
    "prior_peak_lookback_bars": 20,
    "forward_rebound_horizon_bars": 20,
    "minimum_prior_drawdown_pct": 0.75,
    "minimum_forward_rebound_pct": 0.40,
    "entry_match_window_minutes": [-2, 10],
    "forbidden_use": "same_date_policy_selection_or_simulated_decision",
}
METRIC_CONTRACT = {
    "metric_role": "counterfactual_strategy_research",
    "decision_authority": "offline_pure_market_reversal_replay_only",
    "window_policy": "prior_dates_train_then_next_date_walk_forward_by_venue",
    "sample_floor": (
        f"{MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_"
        "before_strategy_or_runtime_judgment"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "unique_valid_completed_1m_ohlcv_with_explicit_timestamp_venue_session;"
        "no_signal_ai_policy_or_order_input"
    ),
    "forbidden_uses": [
        "historic_entry_or_exit_signal_input",
        "historic_ai_decision_or_widget_policy_input",
        "real_order_submission",
        "automatic_runtime_threshold_or_policy_apply",
        "provider_or_bot_change",
        "broker_account_order_quantity_or_cooldown_bypass",
        "historical_bbo_or_trade_sequence_imputation",
        "in_sample_result_as_live_authority",
    ],
}


def has_research_sample_floor(trading_dates: Sequence[date]) -> bool:
    """Return whether the operator-selected research evidence floor is met."""
    return len(set(trading_dates)) >= MIN_QUALIFIED_TRADING_DAYS


@dataclass(frozen=True)
class Bar:
    symbol: str
    venue: str
    session: str
    timestamp: datetime
    open: int
    high: int
    low: int
    close: int
    volume: int
    source: str

    @property
    def trade_date(self) -> date:
        return self.timestamp.date()


@dataclass(frozen=True)
class Policy:
    lookback_bars: int
    drawdown_pct: float
    stabilization_bars: int
    reclaim_pct: float
    max_chase_pct: float
    rebound_volume_ratio: float
    target_pct: float
    stop_pct: float
    trailing_arm_pct: float
    trailing_drawdown_pct: float
    max_hold_bars: int

    @property
    def policy_id(self) -> str:
        values = (
            self.lookback_bars,
            self.drawdown_pct,
            self.stabilization_bars,
            self.reclaim_pct,
            self.max_chase_pct,
            self.rebound_volume_ratio,
            self.target_pct,
            self.stop_pct,
            self.trailing_arm_pct,
            self.trailing_drawdown_pct,
            self.max_hold_bars,
        )
        return "pmr_" + "_".join(str(value).replace(".", "p") for value in values)


@dataclass
class _Candidate:
    armed_index: int
    armed_timestamp: datetime
    rolling_peak: int
    trough_index: int
    trough_timestamp: datetime
    trough_price: int
    trough_volume: int


def default_policy_grid() -> list[Policy]:
    """Small auditable grid; callers may supply an explicit JSON grid later."""
    policies: list[Policy] = []
    for lookback in (15, 30):
        for drawdown in (0.75, 1.00, 1.50):
            for stabilization in (1, 2):
                for reclaim in (0.10, 0.20):
                    for target in (0.40, 0.60, 0.80):
                        for max_hold in (10, 20):
                            policies.append(
                                Policy(
                                    lookback_bars=lookback,
                                    drawdown_pct=drawdown,
                                    stabilization_bars=stabilization,
                                    reclaim_pct=reclaim,
                                    max_chase_pct=0.80,
                                    rebound_volume_ratio=0.80,
                                    target_pct=target,
                                    stop_pct=0.80,
                                    trailing_arm_pct=0.40,
                                    trailing_drawdown_pct=0.20,
                                    max_hold_bars=max_hold,
                                )
                            )
    return policies


def _positive_int(value: object) -> int:
    try:
        return abs(int(float(str(value or "").replace(",", "").strip())))
    except (TypeError, ValueError):
        return 0


def _nonnegative_int(value: object) -> int:
    try:
        parsed = int(float(str(value or "0").replace(",", "").strip()))
    except (TypeError, ValueError):
        return -1
    return abs(parsed)


def _valid_ohlcv(*, open_: int, high: int, low: int, close: int, volume: int) -> bool:
    return (
        min(open_, high, low, close) > 0
        and high >= max(open_, close, low)
        and low <= min(open_, close, high)
        and volume >= 0
    )


def _parse_source_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()[:14]
    if len(text) != 14 or not text.isdigit():
        return None
    try:
        return datetime.strptime(text, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _load_backfill_file(path: Path) -> tuple[list[Bar], list[str]]:
    bars: list[Bar] = []
    issues: list[str] = []
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError:
        return bars, [f"market_file_unreadable:{path}"]
    with handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError:
                issues.append(f"market_json_invalid:{path}:{line_number}")
                continue
            if (
                not isinstance(row, dict)
                or row.get("schema") != "pure_market_minute_bar_v1"
            ):
                issues.append(f"market_schema_invalid:{path}:{line_number}")
                continue
            timestamp = _parse_source_timestamp(row.get("source_timestamp"))
            open_, high, low, close = (
                _positive_int(row.get(key)) for key in ("open", "high", "low", "close")
            )
            volume = _nonnegative_int(row.get("volume"))
            if timestamp is None or not _valid_ohlcv(
                open_=open_, high=high, low=low, close=close, volume=volume
            ):
                issues.append(f"market_row_invalid:{path}:{line_number}")
                continue
            bars.append(
                Bar(
                    symbol=str(row.get("symbol") or SAMSUNG_CODE),
                    venue=str(row.get("venue") or "").upper(),
                    session=str(row.get("session") or ""),
                    timestamp=timestamp,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    source="ka10080_backfill",
                )
            )
    return bars, issues


def _load_widget_observation_file(path: Path) -> tuple[list[Bar], list[str]]:
    """Extract only market OHLCV; advisory/signal fields are never read."""
    bars: list[Bar] = []
    issues: list[str] = []
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError:
        return bars, [f"widget_market_file_unreadable:{path}"]
    with handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError:
                issues.append(f"widget_market_json_invalid:{path}:{line_number}")
                continue
            if not isinstance(row, dict):
                continue
            latest = row.get("latest_completed_bar")
            if not isinstance(latest, dict):
                continue
            timestamp = _parse_source_timestamp(latest.get("source_time"))
            open_, high, low, close = (
                _positive_int(latest.get(key))
                for key in ("open", "high", "low", "close")
            )
            volume = _nonnegative_int(latest.get("volume"))
            venue = str(row.get("market_venue") or "").upper()
            session = str(row.get("market_session") or "")
            if venue not in {"KRX", "NXT"}:
                venue = "KRX" if session == "KRX_REGULAR" else "NXT"
            if timestamp is None or not _valid_ohlcv(
                open_=open_, high=high, low=low, close=close, volume=volume
            ):
                continue
            bars.append(
                Bar(
                    symbol=SAMSUNG_CODE,
                    venue=venue,
                    session=session,
                    timestamp=timestamp,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    source="widget_completed_ka10080",
                )
            )
    return bars, issues


def load_market_bars(
    *,
    market_paths: Sequence[Path] = (),
    widget_observation_dir: Path | None = DEFAULT_WIDGET_OBSERVATION_DIR,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[Bar], dict[str, Any]]:
    effective_start_date = max(
        start_date or CLEAN_TUNING_BASELINE_DATE,
        CLEAN_TUNING_BASELINE_DATE,
    )
    candidates: list[Bar] = []
    issues: list[str] = []
    input_files: list[dict[str, Any]] = []
    for path in market_paths:
        input_files.append(
            {
                "path": str(path),
                "kind": "pure_market_backfill",
                "sha256": _sha256_file(path),
            }
        )
        loaded, found_issues = _load_backfill_file(path)
        candidates.extend(loaded)
        issues.extend(found_issues)
    if widget_observation_dir is not None and widget_observation_dir.exists():
        for path in sorted(
            widget_observation_dir.glob("samsung_widget_advisory_*.jsonl")
        ):
            input_files.append(
                {
                    "path": str(path),
                    "kind": "completed_market_bar_extraction_only",
                    "sha256": _sha256_file(path),
                }
            )
            loaded, found_issues = _load_widget_observation_file(path)
            candidates.extend(loaded)
            issues.extend(found_issues)

    selected: dict[tuple[str, str, datetime], Bar] = {}
    conflicts: set[tuple[str, str, datetime]] = set()
    source_priority = {"widget_completed_ka10080": 1, "ka10080_backfill": 2}
    for bar in candidates:
        if bar.trade_date < effective_start_date:
            continue
        if end_date is not None and bar.trade_date > end_date:
            continue
        if bar.venue not in {"KRX", "NXT"}:
            continue
        key = (bar.venue, bar.session, bar.timestamp)
        existing = selected.get(key)
        if existing is None:
            selected[key] = bar
            continue
        existing_values = (
            existing.open,
            existing.high,
            existing.low,
            existing.close,
            existing.volume,
        )
        incoming_values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        if existing_values != incoming_values:
            conflicts.add(key)
            continue
        if source_priority.get(bar.source, 0) > source_priority.get(existing.source, 0):
            selected[key] = bar
    for key in conflicts:
        selected.pop(key, None)
    bars = sorted(
        selected.values(), key=lambda bar: (bar.timestamp, bar.venue, bar.session)
    )
    source_counts = Counter(bar.source for bar in bars)
    venue_counts = Counter(bar.venue for bar in bars)
    conflict_counts_by_venue = Counter(key[0] for key in conflicts)
    date_counts = Counter(bar.trade_date.isoformat() for bar in bars)
    quality = {
        "status": (
            "PASS"
            if bars and not conflicts and not issues
            else ("PARTIAL" if bars else "FAIL")
        ),
        "bar_count": len(bars),
        "trading_date_count": len(date_counts),
        "source_counts": dict(sorted(source_counts.items())),
        "venue_counts": dict(sorted(venue_counts.items())),
        "date_counts": dict(sorted(date_counts.items())),
        "conflict_count": len(conflicts),
        "conflict_counts_by_venue": {
            venue: conflict_counts_by_venue[venue] for venue in COHORTS
        },
        "issue_count": len(issues),
        "issues_sample": issues[:20],
        "signal_fields_consumed": False,
        "ai_fields_consumed": False,
        "policy_fields_consumed": False,
        "future_fields_consumed_for_decision": False,
        "clean_tuning_baseline_date": CLEAN_TUNING_BASELINE_DATE.isoformat(),
        "requested_start_date": start_date.isoformat() if start_date else None,
        "effective_start_date": effective_start_date.isoformat(),
        "pre_baseline_rows_excluded": sum(
            bar.trade_date < effective_start_date for bar in candidates
        ),
        "input_files": input_files,
        "venue_status": {
            venue: (
                "PASS"
                if venue_counts[venue] > 0
                and conflict_counts_by_venue[venue] == 0
                and not issues
                else ("PARTIAL" if venue_counts[venue] > 0 else "FAIL")
            )
            for venue in COHORTS
        },
    }
    return bars, quality


def _group_series(bars: Iterable[Bar]) -> dict[tuple[date, str, str], list[Bar]]:
    grouped: dict[tuple[date, str, str], list[Bar]] = defaultdict(list)
    for bar in bars:
        grouped[(bar.trade_date, bar.venue, bar.session)].append(bar)
    return {
        key: sorted(values, key=lambda bar: bar.timestamp)
        for key, values in grouped.items()
    }


def assess_date_coverage(bars: Sequence[Bar]) -> dict[str, Any]:
    """Classify complete venue-days without manufacturing missing bars.

    Samsung is sufficiently liquid that a materially short session is a source
    coverage failure, not a zero-volume market period.  A venue-day is usable
    only when every expected venue session reaches its conservative bar floor.
    """
    counts: Counter[tuple[str, date, str]] = Counter(
        (bar.venue, bar.trade_date, bar.session) for bar in bars
    )
    observed_dates = {
        venue: sorted({bar.trade_date for bar in bars if bar.venue == venue})
        for venue in COHORTS
    }
    qualified: dict[str, list[str]] = {venue: [] for venue in COHORTS}
    excluded: dict[str, list[dict[str, Any]]] = {venue: [] for venue in COHORTS}
    for venue in COHORTS:
        expected = COVERAGE_MIN_BARS[venue]
        for trade_date in observed_dates[venue]:
            missing = {
                session: {
                    "observed": counts[(venue, trade_date, session)],
                    "minimum": minimum,
                }
                for session, minimum in expected.items()
                if counts[(venue, trade_date, session)] < minimum
            }
            if missing:
                excluded[venue].append(
                    {
                        "trade_date": trade_date.isoformat(),
                        "reason": "incomplete_venue_session_coverage",
                        "sessions": missing,
                    }
                )
            else:
                qualified[venue].append(trade_date.isoformat())
    return {
        "policy": {
            "minimum_completed_bars_by_venue_session": COVERAGE_MIN_BARS,
            "missing_bars_are_never_imputed": True,
        },
        "qualified_dates_by_venue": qualified,
        "excluded_dates_by_venue": excluded,
    }


def filter_coverage_qualified_bars(
    bars: Sequence[Bar], coverage: dict[str, Any]
) -> list[Bar]:
    allowed = {
        (venue, date.fromisoformat(day))
        for venue, days in coverage["qualified_dates_by_venue"].items()
        for day in days
    }
    return [bar for bar in bars if (bar.venue, bar.trade_date) in allowed]


def _median_positive(values: Iterable[int]) -> float:
    positive = [value for value in values if value > 0]
    return float(statistics.median(positive)) if positive else 0.0


def _close_trade(
    trade: dict[str, Any],
    *,
    exit_bar: Bar,
    exit_price: float,
    exit_reason: str,
    cost_pct: float,
) -> dict[str, Any]:
    entry_price = float(trade["entry_price"])
    gross = (float(exit_price) / entry_price - 1.0) * 100.0
    setup_trough_price = float(trade["setup_trough_price"])
    setup_trough_at = trade["setup_trough_at"]
    peak_price = float(trade["peak_price"])
    lowest_price = float(trade["lowest_price"])
    return {
        "policy_id": trade["policy_id"],
        "strategy_mode": trade.get("strategy_mode", "confirmed_recovery"),
        "entry_regime": trade.get("entry_regime"),
        "trade_date": trade["trade_date"].isoformat(),
        "venue": trade["venue"],
        "session": trade["session"],
        "candidate_armed_at": trade["candidate_armed_at"].isoformat(),
        "entry_signal_at": trade["entry_signal_at"].isoformat(),
        "entry_at": trade["entry_at"].isoformat(),
        "entry_price": round(entry_price, 4),
        "exit_at": exit_bar.timestamp.isoformat(),
        "exit_price": round(float(exit_price), 4),
        "exit_reason": exit_reason,
        "holding_bar_count": len(trade["holding_bars"]),
        "gross_profit_pct": round(gross, 6),
        "net_profit_pct": round(gross - cost_pct, 6),
        "setup_trough_price": setup_trough_price,
        "setup_trough_at": setup_trough_at.isoformat(),
        "entry_vs_setup_trough_pct": round(
            (entry_price / setup_trough_price - 1.0) * 100.0, 6
        ),
        "entry_timing_vs_setup_trough_min": round(
            (trade["entry_at"] - setup_trough_at).total_seconds() / 60.0,
            3,
        ),
        "mfe_pct": round((peak_price / entry_price - 1.0) * 100.0, 6),
        "mae_pct": round((lowest_price / entry_price - 1.0) * 100.0, 6),
        "holding_peak": peak_price,
        "holding_peak_at": trade["peak_at"].isoformat(),
        "exit_vs_holding_peak_pct": round(
            (float(exit_price) / peak_price - 1.0) * 100.0, 6
        ),
    }


def simulate_policy(
    bars: Sequence[Bar],
    policy: Policy,
    *,
    cost_pct: float,
    regime_by_timestamp: dict[datetime, str] | None = None,
    allowed_entry_regimes: set[str] | None = None,
    exit_regimes: set[str] | None = None,
    exit_regime_confirmations: int = 1,
    strategy_mode: str = "confirmed_recovery",
) -> list[dict[str, Any]]:
    """Causal next-bar-entry simulation with pessimistic same-bar ambiguity."""
    trades: list[dict[str, Any]] = []
    for (_, _, _), series in _group_series(bars).items():
        if len(series) <= policy.lookback_bars + 1:
            continue
        candidate: _Candidate | None = None
        position: dict[str, Any] | None = None
        pending_entry: tuple[_Candidate, int] | None = None
        pending_timeout = False
        pending_regime_exit = False
        exit_regime_streak = 0
        cooldown_until = -1
        for index, bar in enumerate(series):
            if (
                index > 0
                and (bar.timestamp - series[index - 1].timestamp).total_seconds() > 120
            ):
                candidate = None
                pending_entry = None
                if position is not None:
                    if float(bar.open) > float(position["peak_price"]):
                        position["peak_price"] = float(bar.open)
                        position["peak_at"] = bar.timestamp
                    position["lowest_price"] = min(
                        float(position["lowest_price"]), float(bar.open)
                    )
                    result = _close_trade(
                        position,
                        exit_bar=bar,
                        exit_price=bar.open,
                        exit_reason="data_gap_next_open",
                        cost_pct=cost_pct,
                    )
                    trades.append(result)
                    position = None
                pending_timeout = False
                pending_regime_exit = False
                exit_regime_streak = 0
                cooldown_until = index + 2

            if pending_regime_exit and position is not None:
                if float(bar.open) > float(position["peak_price"]):
                    position["peak_price"] = float(bar.open)
                    position["peak_at"] = bar.timestamp
                position["lowest_price"] = min(
                    float(position["lowest_price"]), float(bar.open)
                )
                result = _close_trade(
                    position,
                    exit_bar=bar,
                    exit_price=bar.open,
                    exit_reason="regime_transition_next_open",
                    cost_pct=cost_pct,
                )
                trades.append(result)
                position = None
                pending_regime_exit = False
                pending_timeout = False
                cooldown_until = index + 2
                exit_regime_streak = 0

            if pending_timeout and position is not None:
                if float(bar.open) > float(position["peak_price"]):
                    position["peak_price"] = float(bar.open)
                    position["peak_at"] = bar.timestamp
                position["lowest_price"] = min(
                    float(position["lowest_price"]), float(bar.open)
                )
                result = _close_trade(
                    position,
                    exit_bar=bar,
                    exit_price=bar.open,
                    exit_reason="max_hold_next_open",
                    cost_pct=cost_pct,
                )
                trades.append(result)
                position = None
                pending_timeout = False
                pending_regime_exit = False
                cooldown_until = index + 2
                exit_regime_streak = 0

            if pending_entry is not None and position is None:
                entry_candidate, signal_index = pending_entry
                position = {
                    "policy_id": policy.policy_id,
                    "strategy_mode": strategy_mode,
                    "entry_regime": (
                        regime_by_timestamp.get(series[signal_index].timestamp)
                        if regime_by_timestamp is not None
                        else None
                    ),
                    "trade_date": bar.trade_date,
                    "venue": bar.venue,
                    "session": bar.session,
                    "candidate_armed_at": entry_candidate.armed_timestamp,
                    "entry_signal_at": series[signal_index].timestamp,
                    "entry_at": bar.timestamp,
                    "entry_price": float(bar.open),
                    "entry_index": index,
                    "holding_bars": [bar],
                    "setup_trough_price": float(entry_candidate.trough_price),
                    "setup_trough_at": entry_candidate.trough_timestamp,
                    "peak_price": float(bar.open),
                    "peak_at": bar.timestamp,
                    "lowest_price": float(bar.open),
                }
                candidate = None
                pending_entry = None
                exit_regime_streak = 0

            if position is not None:
                if position["holding_bars"][-1] is not bar:
                    position["holding_bars"].append(bar)
                entry_price = float(position["entry_price"])
                if float(bar.open) > float(position["peak_price"]):
                    position["peak_price"] = float(bar.open)
                    position["peak_at"] = bar.timestamp
                position["lowest_price"] = min(
                    float(position["lowest_price"]), float(bar.open)
                )
                prior_peak = float(position["peak_price"])
                stop_price = entry_price * (1.0 - policy.stop_pct / 100.0)
                target_price = entry_price * (1.0 + policy.target_pct / 100.0)
                trailing_price = prior_peak * (
                    1.0 - policy.trailing_drawdown_pct / 100.0
                )
                trail_armed = (
                    prior_peak / entry_price - 1.0
                ) * 100.0 >= policy.trailing_arm_pct
                stop_hit = bar.low <= stop_price
                target_hit = bar.high >= target_price
                trail_hit = trail_armed and bar.low <= trailing_price
                if stop_hit:
                    fill = min(float(bar.open), stop_price)
                    position["lowest_price"] = min(
                        float(position["lowest_price"]), fill
                    )
                    result = _close_trade(
                        position,
                        exit_bar=bar,
                        exit_price=fill,
                        exit_reason=(
                            "stop_ambiguous_first" if target_hit else "hard_stop"
                        ),
                        cost_pct=cost_pct,
                    )
                    trades.append(result)
                    position = None
                    cooldown_until = index + 2
                    continue
                if trail_hit:
                    fill = min(float(bar.open), trailing_price)
                    position["lowest_price"] = min(
                        float(position["lowest_price"]), fill
                    )
                    result = _close_trade(
                        position,
                        exit_bar=bar,
                        exit_price=fill,
                        exit_reason="trailing_stop",
                        cost_pct=cost_pct,
                    )
                    trades.append(result)
                    position = None
                    cooldown_until = index + 2
                    continue
                if target_hit:
                    if target_price > float(position["peak_price"]):
                        position["peak_price"] = target_price
                        position["peak_at"] = bar.timestamp
                    position["lowest_price"] = min(
                        float(position["lowest_price"]), float(bar.low)
                    )
                    result = _close_trade(
                        position,
                        exit_bar=bar,
                        exit_price=target_price,
                        exit_reason="target_limit",
                        cost_pct=cost_pct,
                    )
                    trades.append(result)
                    position = None
                    cooldown_until = index + 2
                    continue
                if float(bar.high) > prior_peak:
                    position["peak_price"] = float(bar.high)
                    position["peak_at"] = bar.timestamp
                position["lowest_price"] = min(
                    float(position["lowest_price"]), float(bar.low)
                )
                if index - int(position["entry_index"]) + 1 >= policy.max_hold_bars:
                    if index + 1 < len(series):
                        pending_timeout = True
                    else:
                        result = _close_trade(
                            position,
                            exit_bar=bar,
                            exit_price=bar.close,
                            exit_reason="session_end_mark_to_market",
                            cost_pct=cost_pct,
                        )
                        trades.append(result)
                        position = None
                elif (
                    exit_regimes is not None
                    and regime_by_timestamp is not None
                    and regime_by_timestamp.get(bar.timestamp) in exit_regimes
                ):
                    exit_regime_streak += 1
                    if exit_regime_streak >= max(1, exit_regime_confirmations):
                        if index + 1 < len(series):
                            pending_regime_exit = True
                        else:
                            result = _close_trade(
                                position,
                                exit_bar=bar,
                                exit_price=bar.close,
                                exit_reason="session_end_mark_to_market",
                                cost_pct=cost_pct,
                            )
                            trades.append(result)
                            position = None
                else:
                    exit_regime_streak = 0
                continue

            if (
                index <= cooldown_until
                or index < policy.lookback_bars
                or index + 1 >= len(series)
            ):
                continue
            rolling = series[index - policy.lookback_bars : index + 1]
            rolling_peak = max(item.high for item in rolling)
            drawdown_pct = (rolling_peak / bar.low - 1.0) * 100.0
            if candidate is None:
                if drawdown_pct >= policy.drawdown_pct:
                    candidate = _Candidate(
                        armed_index=index,
                        armed_timestamp=bar.timestamp,
                        rolling_peak=rolling_peak,
                        trough_index=index,
                        trough_timestamp=bar.timestamp,
                        trough_price=bar.low,
                        trough_volume=bar.volume,
                    )
                continue
            if bar.low < candidate.trough_price:
                candidate = _Candidate(
                    armed_index=candidate.armed_index,
                    armed_timestamp=candidate.armed_timestamp,
                    rolling_peak=max(candidate.rolling_peak, rolling_peak),
                    trough_index=index,
                    trough_timestamp=bar.timestamp,
                    trough_price=bar.low,
                    trough_volume=bar.volume,
                )
                continue
            bars_since_trough = index - candidate.trough_index
            if bars_since_trough > 12:
                candidate = None
                continue
            post_trough = series[candidate.trough_index + 1 : index + 1]
            higher_low = (
                bool(post_trough)
                and min(item.low for item in post_trough) > candidate.trough_price
            )
            rebound_pct = (bar.close / candidate.trough_price - 1.0) * 100.0
            decline_volume = _median_positive(
                item.volume
                for item in series[
                    max(candidate.trough_index - 3, 0) : candidate.trough_index + 1
                ]
            )
            volume_ratio = bar.volume / decline_volume if decline_volume > 0 else 0.0
            recent_rising = bar.close > series[index - 1].close
            entry_regime = (
                regime_by_timestamp.get(bar.timestamp)
                if regime_by_timestamp is not None
                else None
            )
            regime_allowed = (
                allowed_entry_regimes is None or entry_regime in allowed_entry_regimes
            )
            if strategy_mode == "capitulation_probe":
                entry_setup_confirmed = (
                    bars_since_trough >= policy.stabilization_bars
                    and higher_low
                    and recent_rising
                    and 0.0 <= rebound_pct <= min(policy.max_chase_pct, 0.50)
                    and (
                        candidate.trough_volume <= 0
                        or bar.volume <= candidate.trough_volume * 1.20
                    )
                )
            else:
                entry_setup_confirmed = (
                    bars_since_trough >= policy.stabilization_bars
                    and higher_low
                    and recent_rising
                    and policy.reclaim_pct <= rebound_pct <= policy.max_chase_pct
                    and volume_ratio >= policy.rebound_volume_ratio
                )
            if regime_allowed and entry_setup_confirmed:
                pending_entry = (candidate, index)

        if position is not None:
            last_bar = series[-1]
            result = _close_trade(
                position,
                exit_bar=last_bar,
                exit_price=last_bar.close,
                exit_reason="session_end_mark_to_market",
                cost_pct=cost_pct,
            )
            trades.append(result)
    return trades


def label_reversal_opportunities(bars: Sequence[Bar]) -> list[dict[str, Any]]:
    """Create future-looking labels used only after OOS simulation finishes."""
    contract = OPPORTUNITY_LABEL_CONTRACT
    radius = int(contract["local_low_radius_bars"])
    lookback = int(contract["prior_peak_lookback_bars"])
    horizon = int(contract["forward_rebound_horizon_bars"])
    raw_labels: list[dict[str, Any]] = []
    for (_, venue, session), series in _group_series(bars).items():
        if len(series) < lookback + horizon + radius + 1:
            continue
        for index in range(lookback, len(series) - horizon):
            bar = series[index]
            local_window = series[index - radius : index + radius + 1]
            if bar.low != min(item.low for item in local_window):
                continue
            # Resolve a flat-bottom run to its first timestamp.
            if any(item.low == bar.low for item in local_window[:radius]):
                continue
            prior_peak = max(item.high for item in series[index - lookback : index])
            drawdown_pct = (prior_peak / bar.low - 1.0) * 100.0
            forward = series[index + 1 : index + horizon + 1]
            rebound_peak = max(item.high for item in forward)
            rebound_pct = (rebound_peak / bar.low - 1.0) * 100.0
            if drawdown_pct < float(
                contract["minimum_prior_drawdown_pct"]
            ) or rebound_pct < float(contract["minimum_forward_rebound_pct"]):
                continue
            peak_bar = next(item for item in forward if item.high == rebound_peak)
            raw_labels.append(
                {
                    "trade_date": bar.trade_date.isoformat(),
                    "venue": venue,
                    "session": session,
                    "trough_at": bar.timestamp.isoformat(),
                    "trough_price": bar.low,
                    "prior_peak": prior_peak,
                    "prior_drawdown_pct": round(drawdown_pct, 6),
                    "forward_rebound_peak": rebound_peak,
                    "forward_rebound_peak_at": peak_bar.timestamp.isoformat(),
                    "forward_rebound_pct": round(rebound_pct, 6),
                }
            )

    # Nearby local minima describe one economic opportunity. Keep its lowest
    # trough (earliest on ties) so coverage is not inflated by label density.
    collapsed: list[dict[str, Any]] = []
    for label in sorted(
        raw_labels,
        key=lambda row: (row["venue"], row["session"], row["trough_at"]),
    ):
        if not collapsed:
            collapsed.append(label)
            continue
        previous = collapsed[-1]
        same_series = (
            previous["venue"] == label["venue"]
            and previous["session"] == label["session"]
            and previous["trade_date"] == label["trade_date"]
        )
        separation = (
            datetime.fromisoformat(label["trough_at"])
            - datetime.fromisoformat(previous["trough_at"])
        ).total_seconds() / 60.0
        if same_series and separation <= 5:
            if label["trough_price"] < previous["trough_price"]:
                collapsed[-1] = label
            continue
        collapsed.append(label)
    return collapsed


def summarize_opportunity_capture(
    opportunities: Sequence[dict[str, Any]],
    trades: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Match OOS trades to ex-post troughs without feeding labels upstream."""
    minimum_minutes, maximum_minutes = OPPORTUNITY_LABEL_CONTRACT[
        "entry_match_window_minutes"
    ]
    unmatched_trade_indexes = set(range(len(trades)))
    rows: list[dict[str, Any]] = []
    for opportunity in opportunities:
        trough_at = datetime.fromisoformat(opportunity["trough_at"])
        candidates: list[tuple[float, float, int]] = []
        for trade_index in unmatched_trade_indexes:
            trade = trades[trade_index]
            if (
                trade["trade_date"] != opportunity["trade_date"]
                or trade["venue"] != opportunity["venue"]
                or trade["session"] != opportunity["session"]
            ):
                continue
            entry_at = datetime.fromisoformat(trade["entry_at"])
            offset = (entry_at - trough_at).total_seconds() / 60.0
            if minimum_minutes <= offset <= maximum_minutes:
                price_gap = (
                    float(trade["entry_price"]) / float(opportunity["trough_price"])
                    - 1.0
                ) * 100.0
                candidates.append((abs(offset), price_gap, trade_index))
        matched_trade: dict[str, Any] | None = None
        if candidates:
            _, _, matched_index = min(candidates)
            unmatched_trade_indexes.remove(matched_index)
            matched_trade = trades[matched_index]
        row = dict(opportunity)
        row["captured"] = matched_trade is not None
        if matched_trade is not None:
            entry_at = datetime.fromisoformat(matched_trade["entry_at"])
            row.update(
                {
                    "matched_entry_at": matched_trade["entry_at"],
                    "matched_entry_price": matched_trade["entry_price"],
                    "entry_timing_vs_trough_min": round(
                        (entry_at - trough_at).total_seconds() / 60.0, 3
                    ),
                    "entry_price_vs_trough_pct": round(
                        (
                            float(matched_trade["entry_price"])
                            / float(opportunity["trough_price"])
                            - 1.0
                        )
                        * 100.0,
                        6,
                    ),
                    "matched_exit_at": matched_trade["exit_at"],
                    "matched_exit_price": matched_trade["exit_price"],
                    "matched_exit_reason": matched_trade["exit_reason"],
                    "matched_net_profit_pct": matched_trade["net_profit_pct"],
                    "exit_price_vs_forward_rebound_peak_pct": round(
                        (
                            float(matched_trade["exit_price"])
                            / float(opportunity["forward_rebound_peak"])
                            - 1.0
                        )
                        * 100.0,
                        6,
                    ),
                }
            )
        rows.append(row)
    captured = [row for row in rows if row["captured"]]
    return {
        "label_contract": OPPORTUNITY_LABEL_CONTRACT,
        "opportunity_count": len(rows),
        "captured_count": len(captured),
        "missed_count": len(rows) - len(captured),
        "diagnostic_opportunity_capture_rate_pct": (
            round(len(captured) / len(rows) * 100.0, 3) if rows else None
        ),
        "avg_entry_price_vs_trough_pct": (
            round(
                statistics.fmean(
                    float(row["entry_price_vs_trough_pct"]) for row in captured
                ),
                6,
            )
            if captured
            else None
        ),
        "avg_entry_timing_vs_trough_min": (
            round(
                statistics.fmean(
                    float(row["entry_timing_vs_trough_min"]) for row in captured
                ),
                6,
            )
            if captured
            else None
        ),
        "avg_exit_price_vs_forward_rebound_peak_pct": (
            round(
                statistics.fmean(
                    float(row["exit_price_vs_forward_rebound_peak_pct"])
                    for row in captured
                ),
                6,
            )
            if captured
            else None
        ),
        "opportunities": rows,
    }


def _trade_summary(
    trades: Sequence[dict[str, Any]],
    *,
    cost_scenarios_pct: Sequence[float],
    source_quality_passed: bool,
) -> dict[str, Any]:
    if not trades:
        return {
            "sample_count": 0,
            "trading_date_count": 0,
            "gross_diagnostic_win_rate_pct": None,
            "gross": {"equal_weight_avg_profit_pct": None},
            "net_by_cost": {},
            "source_quality_adjusted_ev_pct": None,
            "simple_sum_profit_pct": 0.0,
        }
    gross_values = [float(row["gross_profit_pct"]) for row in trades]
    entry_weights = [float(row["entry_price"]) for row in trades]
    gross_avg = statistics.fmean(gross_values)
    notional_gross = sum(
        value * weight for value, weight in zip(gross_values, entry_weights)
    ) / sum(entry_weights)
    net_by_cost: dict[str, Any] = {}
    for cost in cost_scenarios_pct:
        net_values = [value - float(cost) for value in gross_values]
        key = f"cost_{float(cost):.2f}pct".replace(".", "p")
        net_by_cost[key] = {
            "round_trip_cost_pct": float(cost),
            "equal_weight_avg_profit_pct": round(statistics.fmean(net_values), 6),
            "notional_weighted_ev_pct": round(
                sum(value * weight for value, weight in zip(net_values, entry_weights))
                / sum(entry_weights),
                6,
            ),
            "diagnostic_win_rate_pct": round(
                sum(value > 0 for value in net_values) / len(net_values) * 100.0,
                3,
            ),
        }
    return {
        "sample_count": len(trades),
        "trading_date_count": len({row["trade_date"] for row in trades}),
        "gross_diagnostic_win_rate_pct": round(
            sum(value > 0 for value in gross_values) / len(gross_values) * 100.0,
            3,
        ),
        "gross": {
            "equal_weight_avg_profit_pct": round(gross_avg, 6),
            "notional_weighted_ev_pct": round(notional_gross, 6),
        },
        "net_by_cost": net_by_cost,
        "source_quality_adjusted_ev_pct": (
            round(statistics.fmean(float(row["net_profit_pct"]) for row in trades), 6)
            if source_quality_passed
            else None
        ),
        "simple_sum_profit_pct": round(sum(gross_values), 6),
        "avg_entry_vs_setup_trough_pct": round(
            statistics.fmean(float(row["entry_vs_setup_trough_pct"]) for row in trades),
            6,
        ),
        "avg_entry_timing_vs_setup_trough_min": round(
            statistics.fmean(
                float(row["entry_timing_vs_setup_trough_min"]) for row in trades
            ),
            6,
        ),
        "avg_mfe_pct": round(
            statistics.fmean(float(row["mfe_pct"]) for row in trades), 6
        ),
        "avg_mae_pct": round(
            statistics.fmean(float(row["mae_pct"]) for row in trades), 6
        ),
        "avg_exit_vs_holding_peak_pct": round(
            statistics.fmean(float(row["exit_vs_holding_peak_pct"]) for row in trades),
            6,
        ),
        "exit_reason_counts": dict(
            sorted(Counter(row["exit_reason"] for row in trades).items())
        ),
    }


def _policy_rank(
    trades: Sequence[dict[str, Any]],
    *,
    min_train_trades: int,
    min_train_dates: int,
) -> tuple[float, float, float, float] | None:
    if len(trades) < min_train_trades:
        return None
    if len({row["trade_date"] for row in trades}) < min_train_dates:
        return None
    avg_net = statistics.fmean(float(row["net_profit_pct"]) for row in trades)
    simple_net = sum(float(row["net_profit_pct"]) for row in trades)
    avg_bottom_gap = statistics.fmean(
        float(row["entry_vs_setup_trough_pct"]) for row in trades
    )
    avg_exit_gap = -statistics.fmean(
        float(row["exit_vs_holding_peak_pct"]) for row in trades
    )
    return avg_net, simple_net, -avg_bottom_gap, -avg_exit_gap


def _cohort_bars(bars: Sequence[Bar], cohort: str) -> list[Bar]:
    return [bar for bar in bars if bar.venue == cohort]


def build_walk_forward_report(
    bars: Sequence[Bar],
    *,
    source_quality: dict[str, Any],
    policies: Sequence[Policy] | None = None,
    training_days: int = 20,
    min_train_trades: int = 20,
    min_train_dates: int = 10,
    selection_cost_pct: float = 0.20,
    cost_scenarios_pct: Sequence[float] = DEFAULT_COST_SCENARIOS_PCT,
    enforce_coverage: bool = True,
) -> dict[str, Any]:
    policies = list(policies or default_policy_grid())
    cost_scenarios_pct = tuple(
        sorted({float(value) for value in cost_scenarios_pct} | {selection_cost_pct})
    )
    coverage = assess_date_coverage(bars)
    analysis_bars = (
        filter_coverage_qualified_bars(bars, coverage)
        if enforce_coverage
        else list(bars)
    )
    cohorts: dict[str, Any] = {}
    for cohort in COHORTS:
        cohort_source_quality_passed = (
            source_quality.get("venue_status", {}).get(cohort)
            or source_quality.get("status")
        ) == "PASS"
        cohort_bars = _cohort_bars(analysis_bars, cohort)
        available_dates = sorted({bar.trade_date for bar in cohort_bars})
        evaluations: list[dict[str, Any]] = []
        cohort_oos: list[dict[str, Any]] = []
        for date_index, evaluation_date in enumerate(available_dates):
            prior_dates = available_dates[:date_index]
            train_dates = prior_dates[-training_days:]
            if len(train_dates) < training_days:
                evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "insufficient_prior_trading_days",
                        "prior_trading_day_count": len(train_dates),
                        "selected_policy": None,
                        "trades": [],
                    }
                )
                continue
            train_bars = [bar for bar in cohort_bars if bar.trade_date in train_dates]
            selected: (
                tuple[tuple[float, float, float, float], Policy, list[dict[str, Any]]]
                | None
            ) = None
            for policy in policies:
                train_trades = simulate_policy(
                    train_bars,
                    policy,
                    cost_pct=selection_cost_pct,
                )
                rank = _policy_rank(
                    train_trades,
                    min_train_trades=min_train_trades,
                    min_train_dates=min_train_dates,
                )
                if rank is None:
                    continue
                candidate = (rank, policy, train_trades)
                if selected is None or candidate[0] > selected[0]:
                    selected = candidate
            if selected is None:
                evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "no_policy_met_training_floor",
                        "training_dates": [item.isoformat() for item in train_dates],
                        "selected_policy": None,
                        "trades": [],
                    }
                )
                continue
            rank, policy, training_trades = selected
            evaluation_bars = [
                bar for bar in cohort_bars if bar.trade_date == evaluation_date
            ]
            evaluation_trades = simulate_policy(
                evaluation_bars,
                policy,
                cost_pct=selection_cost_pct,
            )
            cohort_oos.extend(evaluation_trades)
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "evaluated_out_of_sample",
                    "training_dates": [item.isoformat() for item in train_dates],
                    "selected_policy": asdict(policy),
                    "selected_policy_id": policy.policy_id,
                    "training_rank": {
                        "source_quality_adjusted_ev_pct": round(rank[0], 6),
                        "simple_sum_profit_pct": round(rank[1], 6),
                    },
                    "training_summary": _trade_summary(
                        training_trades,
                        cost_scenarios_pct=cost_scenarios_pct,
                        source_quality_passed=cohort_source_quality_passed,
                    ),
                    "out_of_sample_summary": _trade_summary(
                        evaluation_trades,
                        cost_scenarios_pct=cost_scenarios_pct,
                        source_quality_passed=cohort_source_quality_passed,
                    ),
                    "trades": evaluation_trades,
                }
            )
        evaluated_dates = {
            date.fromisoformat(row["evaluation_date"])
            for row in evaluations
            if row["status"] == "evaluated_out_of_sample"
        }
        evaluation_bars = [
            bar for bar in cohort_bars if bar.trade_date in evaluated_dates
        ]
        opportunities = label_reversal_opportunities(evaluation_bars)
        sample_floor_passed = has_research_sample_floor(available_dates)
        evaluation_count = sum(
            row["status"] == "evaluated_out_of_sample" for row in evaluations
        )
        if not sample_floor_passed or not cohort_source_quality_passed:
            cohort_decision = "insufficient_for_strategy_or_runtime_judgment"
        elif evaluation_count == 0 or not cohort_oos:
            cohort_decision = "no_out_of_sample_trade_evidence"
        else:
            cohort_decision = "research_sample_floor_passed"
        cohorts[cohort] = {
            "available_trading_dates": [item.isoformat() for item in available_dates],
            "bar_count": len(cohort_bars),
            "evaluation_count": evaluation_count,
            "out_of_sample_summary": _trade_summary(
                cohort_oos,
                cost_scenarios_pct=cost_scenarios_pct,
                source_quality_passed=cohort_source_quality_passed,
            ),
            "opportunity_capture": summarize_opportunity_capture(
                opportunities,
                cohort_oos,
            ),
            "sample_floor_passed": sample_floor_passed,
            "decision": cohort_decision,
            "evaluations": evaluations,
        }
    available_dates = sorted({bar.trade_date for bar in analysis_bars})
    sample_floor_passed_by_venue = {
        cohort: cohorts[cohort]["sample_floor_passed"] for cohort in COHORTS
    }
    sample_floor_passed = all(sample_floor_passed_by_venue.values())
    overall_decision_passed = all(
        cohorts[cohort]["decision"] == "research_sample_floor_passed"
        for cohort in COHORTS
    )
    source_quality_with_coverage = dict(source_quality)
    source_quality_with_coverage["coverage"] = coverage
    source_quality_with_coverage["coverage_enforced"] = enforce_coverage
    source_quality_with_coverage["analysis_bar_count"] = len(analysis_bars)
    return {
        "schema": "pure_market_reversal_replay_v1",
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "objective": (
            "causally enter near the end of a decline and preserve the subsequent "
            "rebound through an exit, maximizing cost-adjusted expected value"
        ),
        "symbol": SAMSUNG_CODE,
        "data_start_date": available_dates[0].isoformat() if available_dates else None,
        "data_end_date": available_dates[-1].isoformat() if available_dates else None,
        "trading_date_count": len(available_dates),
        "policy_count": len(policies),
        "training_days": training_days,
        "min_train_trades": min_train_trades,
        "min_train_dates": min_train_dates,
        "selection_cost_pct": selection_cost_pct,
        "decision_input_contract": {
            "allowed": [
                "completed_1m_open_high_low_close_volume",
                "source_timestamp",
                "venue",
                "session",
            ],
            "forbidden": [
                "ENTRY_*",
                "EXIT_*",
                "AI decision",
                "widget policy or calibration",
                "historic order or position",
                "future bar",
            ],
            "execution_model": (
                "entry_at_next_bar_open; resting_target_and_stop; same_bar_ambiguity_"
                "resolves_adverse_first; timeout_or_data_gap_at_next_open; "
                "session_end_close_mark_to_market"
            ),
        },
        "source_quality": source_quality_with_coverage,
        "official_market_data_reference": OFFICIAL_MARKET_DATA_REFERENCE,
        "sample_floor_passed": sample_floor_passed,
        "sample_floor_passed_by_venue": sample_floor_passed_by_venue,
        "decision": (
            "research_sample_floor_passed"
            if overall_decision_passed
            else "insufficient_for_strategy_or_runtime_judgment"
        ),
        "cohorts": cohorts,
        "opportunity_label_contract": OPPORTUNITY_LABEL_CONTRACT,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "benchmark": {
            "name": "no_trade_cash",
            "equal_weight_avg_profit_pct": 0.0,
            "note": "diagnostic baseline only; opportunity capture remains zero",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    selection_cost = float(report["selection_cost_pct"])
    selection_cost_label = f"{selection_cost:.2f}"
    selection_cost_key = f"cost_{selection_cost:.2f}pct".replace(".", "p")
    lines = [
        f"# Pure-market reversal replay — {report.get('data_start_date')} to {report.get('data_end_date')}",
        "",
        "## Objective",
        "",
        report["objective"],
        "",
        "Historic widget signals, AI decisions, policies, and orders are forbidden inputs. All simulated decisions use completed OHLCV available at that time; future bars are evaluation labels only.",
        "",
        f"- decision: `{report['decision']}`",
        f"- trading dates: `{report['trading_date_count']}` / required `{MIN_QUALIFIED_TRADING_DAYS}`",
        f"- policy grid: `{report['policy_count']}`",
        f"- selection round-trip cost: `{report['selection_cost_pct']}%`",
        "- runtime_effect: `false`",
        "",
        "## Out-of-sample result",
        "",
        f"| Cohort | Bars | Qualified dates | Evaluated dates | Trades | Gross EV | Net EV @{selection_cost_label}% | Net win @{selection_cost_label}% | Opportunities captured | Entry vs trough | Exit vs peak |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cohort in COHORTS:
        row = report["cohorts"][cohort]
        summary = row["out_of_sample_summary"]
        opportunity = row["opportunity_capture"]
        cost_summary = summary.get("net_by_cost", {}).get(selection_cost_key, {})
        lines.append(
            "| "
            + " | ".join(
                [
                    cohort,
                    str(row["bar_count"]),
                    str(len(row["available_trading_dates"])),
                    str(row["evaluation_count"]),
                    str(summary["sample_count"]),
                    str(summary.get("gross", {}).get("equal_weight_avg_profit_pct")),
                    str(summary.get("source_quality_adjusted_ev_pct")),
                    str(cost_summary.get("diagnostic_win_rate_pct")),
                    f"{opportunity.get('captured_count')}/{opportunity.get('opportunity_count')}",
                    str(opportunity.get("avg_entry_price_vs_trough_pct")),
                    str(opportunity.get("avg_exit_price_vs_forward_rebound_peak_pct")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            f"The report is a formal walk-forward backtest artifact. The operator-selected research floor is {MIN_QUALIFIED_TRADING_DAYS} coverage-qualified trading days per venue. Passing it does not create runtime or order authority. Historical BBO and signed tape are not imputed; costs are reported as sensitivity scenarios. Ex-post trough labels measure missed opportunities but never select a same-day policy or decision.",
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
    report: dict[str, Any], *, output_dir: Path = DEFAULT_OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"pure_market_reversal_replay_{report['data_start_date']}_{report['data_end_date']}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--market-data", type=Path, action="append", default=[])
    parser.add_argument("--market-dir", type=Path, default=DEFAULT_MARKET_DIR)
    parser.add_argument(
        "--widget-observation-dir",
        type=Path,
        default=DEFAULT_WIDGET_OBSERVATION_DIR,
    )
    parser.add_argument("--no-widget-observations", action="store_true")
    parser.add_argument("--training-days", type=int, default=20)
    parser.add_argument("--min-train-trades", type=int, default=20)
    parser.add_argument("--min-train-dates", type=int, default=10)
    parser.add_argument("--selection-cost-pct", type=float, default=0.20)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    requested_start = date.fromisoformat(args.start_date) if args.start_date else None
    if requested_start is not None and requested_start < CLEAN_TUNING_BASELINE_DATE:
        raise SystemExit(
            "start-date precedes clean tuning baseline 2026-06-05; "
            "pre-baseline data is audit-only"
        )
    market_paths = list(args.market_data)
    if args.market_dir.exists():
        market_paths.extend(sorted(args.market_dir.glob("samsung_1m_*.jsonl")))
    bars, source_quality = load_market_bars(
        market_paths=market_paths,
        widget_observation_dir=(
            None if args.no_widget_observations else args.widget_observation_dir
        ),
        start_date=requested_start,
        end_date=date.fromisoformat(args.end_date) if args.end_date else None,
    )
    if not bars:
        raise SystemExit("no valid post-baseline market bars available")
    report = build_walk_forward_report(
        bars,
        source_quality=source_quality,
        training_days=max(1, args.training_days),
        min_train_trades=max(1, args.min_train_trades),
        min_train_dates=max(1, args.min_train_dates),
        selection_cost_pct=max(0.0, args.selection_cost_pct),
    )
    if args.write:
        paths = write_report(report, output_dir=args.output_dir)
        print(
            json.dumps(
                {
                    "status": "complete",
                    "json_path": str(paths[0]),
                    "markdown_path": str(paths[1]),
                    "decision": report["decision"],
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
