"""Calibrate next-day widget auto-trade policies from cumulative market rows.

The producer uses only completed, locally recorded widget observations on or
after the clean baseline.  It evaluates non-overlapping entry episodes,
equal-share scale-in legs, fixed take-profit targets, and (where required) a
pre-close market liquidation.  It writes a verified dated policy for the next
KRX trading day but never submits an order or controls a process.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Sequence

from src.engine.monitoring.doosan_widget_contract import (
    DEFAULT_OBSERVATION_DIR as DOOSAN_OBSERVATION_DIR,
    DOOSAN_CODE,
    DOOSAN_NAME,
)
from src.engine.monitoring.hanwha_ocean_widget_contract import (
    DEFAULT_OBSERVATION_DIR as HANWHA_OBSERVATION_DIR,
    HANWHA_OCEAN_CODE,
    HANWHA_OCEAN_NAME,
)
from src.engine.monitoring.samsung_widget_contract import (
    DEFAULT_OBSERVATION_DIR as SAMSUNG_OBSERVATION_DIR,
    KST,
    SAMSUNG_CODE,
    SAMSUNG_NAME,
    previous_krx_trading_date,
)
from src.trading.widget_auto_trade.policy import (
    DEFAULT_POLICY_DIR,
    POLICY_AUTHORITY,
    POLICY_FILE_PREFIX,
    POLICY_SCHEMA,
    WidgetAutoTradePolicyLoader,
)
from src.utils.market_day import is_krx_trading_day

CLEAN_BASELINE_DATE = date(2026, 6, 5)
DEFAULT_OUTPUT_DIR = Path("data/report/widget_auto_trade_policy_calibration")
ROUND_TRIP_COST_PCT = 0.20
ACTIONABLE_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
POSTCLOSE_COMPLETE_TIME = time(20, 1)

METRIC_CONTRACT = {
    "metric_role": "bounded_widget_auto_trade_policy_calibration",
    "decision_authority": POLICY_AUTHORITY,
    "window_policy": "clean_baseline_cumulative_completed_dates_prior_to_effective_date",
    "sample_floor": (
        "two_source_qualified_signal_dates_and_two_non_overlapping_trades;"
        "small_samples_remain_bounded_initial"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "completed_prior_dates;fresh_actionable_source_rows;valid_completed_bar_ohlc;"
        "venue_and_session_provenance"
    ),
    "forbidden_uses": [
        "same_day_outcome_to_same_day_policy",
        "pre_clean_baseline_tuning",
        "cross_symbol_or_cross_session_evidence",
        "account_or_orderable_cash_decision",
        "token_issue_or_refresh",
        "broker_or_manual_ownership_guard_bypass",
        "automatic_process_restart",
        "same_bar_target_after_scale_in_fill",
        "unresolved_samsung_mark_as_realized_profit",
    ],
}


@dataclass(frozen=True)
class SessionSpec:
    session: str
    venue: str
    new_entry_cutoffs: tuple[str, ...]
    force_flat: bool
    force_exit_times: tuple[str, ...]
    overnight_forbidden: bool


@dataclass(frozen=True)
class SymbolSpec:
    symbol: str
    name: str
    observation_dir: Path
    prefix: str
    sessions: tuple[SessionSpec, ...]
    add_trigger_arms: tuple[tuple[int, ...], ...]
    target_bps_values: tuple[int, ...]
    max_entries_values: tuple[int, ...]
    minimum_signal_dates: int
    minimum_trades: int


SPECS = (
    SymbolSpec(
        symbol=SAMSUNG_CODE,
        name=SAMSUNG_NAME,
        observation_dir=SAMSUNG_OBSERVATION_DIR,
        prefix="samsung_widget_advisory",
        sessions=(
            SessionSpec(
                "NXT_PREMARKET",
                "NXT",
                ("08:35:00", "08:40:00"),
                False,
                (),
                False,
            ),
            SessionSpec(
                "KRX_REGULAR", "KRX", ("14:30:00", "15:00:00"), False, (), False
            ),
            SessionSpec(
                "NXT_AFTERMARKET",
                "NXT",
                ("19:20:00", "19:40:00"),
                False,
                (),
                False,
            ),
        ),
        add_trigger_arms=((), (-40,), (-50, -100), (-80, -160)),
        target_bps_values=(40, 50, 60, 70, 80),
        max_entries_values=(2, 3),
        minimum_signal_dates=2,
        minimum_trades=2,
    ),
    SymbolSpec(
        symbol=DOOSAN_CODE,
        name=DOOSAN_NAME,
        observation_dir=DOOSAN_OBSERVATION_DIR,
        prefix="doosan_widget_advisory",
        sessions=(
            SessionSpec(
                "KRX_REGULAR",
                "KRX",
                ("14:30:00", "15:00:00"),
                True,
                ("15:18:00", "15:23:00", "15:28:00"),
                True,
            ),
        ),
        add_trigger_arms=(
            (),
            (-40,),
            (-60,),
            (-80,),
            (-50, -100),
            (-80, -160),
            (-100, -200),
        ),
        target_bps_values=tuple(range(30, 151, 10)),
        max_entries_values=(2, 3),
        minimum_signal_dates=2,
        minimum_trades=2,
    ),
    SymbolSpec(
        symbol=HANWHA_OCEAN_CODE,
        name=HANWHA_OCEAN_NAME,
        observation_dir=HANWHA_OBSERVATION_DIR,
        prefix="hanwha_ocean_widget_advisory",
        sessions=(
            SessionSpec(
                "KRX_REGULAR",
                "KRX",
                ("14:30:00", "15:00:00"),
                True,
                ("15:18:00", "15:23:00", "15:28:00"),
                True,
            ),
        ),
        add_trigger_arms=(
            (),
            (-40,),
            (-60,),
            (-80,),
            (-50, -100),
            (-80, -160),
            (-100, -200),
        ),
        target_bps_values=tuple(range(30, 151, 10)),
        max_entries_values=(2, 3),
        minimum_signal_dates=2,
        minimum_trades=2,
    ),
)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _next_krx_trading_date(target_date: date) -> date:
    candidate = target_date + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _resolve_default_target_date() -> date:
    now = datetime.now(KST)
    if is_krx_trading_day(now.date()) and now.time() >= POSTCLOSE_COMPLETE_TIME:
        return now.date()
    return previous_krx_trading_date(now.date())


def _clock(value: str) -> time:
    return time.fromisoformat(value)


def _positive_price(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _load_rows(
    spec: SymbolSpec, *, target_date: date
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    source_paths: list[str] = []
    for path in sorted(spec.observation_dir.glob(f"{spec.prefix}_*.jsonl")):
        raw_date = path.stem.rsplit("_", 1)[-1]
        try:
            source_date = datetime.strptime(raw_date, "%Y%m%d").date()
        except ValueError:
            continue
        if source_date < CLEAN_BASELINE_DATE or source_date > target_date:
            continue
        source_paths.append(str(path))
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    payload = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(payload, dict):
                    continue
                advisory = payload.get("advisory")
                latest_bar = payload.get("latest_completed_bar")
                if not isinstance(advisory, dict) or not isinstance(latest_bar, dict):
                    continue
                try:
                    observed_at = datetime.fromisoformat(
                        str(payload.get("observed_at_kst") or "")
                    ).astimezone(KST)
                except ValueError:
                    continue
                if observed_at.date() != source_date:
                    continue
                current_price = _positive_price(payload.get("current_price"))
                bar_low = _positive_price(latest_bar.get("low"))
                bar_high = _positive_price(latest_bar.get("high"))
                if current_price is None or bar_low is None or bar_high is None:
                    continue
                try:
                    bar_at = datetime.strptime(
                        str(latest_bar.get("source_time") or ""), "%Y%m%d%H%M%S"
                    ).replace(tzinfo=KST)
                except ValueError:
                    continue
                session = str(advisory.get("session") or "")
                venue = str(payload.get("market_venue") or "")
                rows.append(
                    {
                        "trade_date": source_date,
                        "observed_at": observed_at,
                        "session": session,
                        "venue": venue,
                        "state": str(advisory.get("state") or ""),
                        "previous_state": str(
                            payload.get("previous_advisory_state") or ""
                        ),
                        "current_price": current_price,
                        "low": min(bar_low, bar_high),
                        "high": max(bar_low, bar_high),
                        "bar_at": bar_at,
                        "source_quality_status": str(
                            (advisory.get("source_quality") or {}).get("status") or ""
                        ),
                        "source_path": str(path),
                        "source_line_number": line_number,
                    }
                )
    rows.sort(key=lambda row: row["observed_at"])
    return rows, source_paths


def _entry_indices(
    rows: Sequence[dict[str, Any]],
    *,
    session: SessionSpec,
    cutoff: str,
) -> list[int]:
    cutoff_time = _clock(cutoff)
    selected: list[int] = []
    prior_state = ""
    for index, row in enumerate(rows):
        if row["session"] != session.session or row["venue"] != session.venue:
            continue
        state = str(row["state"])
        previous = str(row["previous_state"] or prior_state)
        prior_state = state
        if (
            state not in ACTIONABLE_STATES
            or previous in ACTIONABLE_STATES
            or row["source_quality_status"] != "PASS"
            or row["observed_at"].time() > cutoff_time
        ):
            continue
        selected.append(index)
    return selected


def _simulate_day(
    rows: Sequence[dict[str, Any]],
    *,
    session: SessionSpec,
    add_triggers_bps: tuple[int, ...],
    target_bps: int,
    max_entries: int,
    cutoff: str,
    cooldown_minutes: int,
    force_exit_time: str | None = None,
) -> list[dict[str, Any]]:
    entries = _entry_indices(
        rows,
        session=session,
        cutoff=cutoff,
    )
    selected: list[dict[str, Any]] = []
    free_after_index = 0
    last_completed_at: datetime | None = None
    for entry_index in entries:
        if len(selected) >= max_entries or entry_index < free_after_index:
            continue
        entry = rows[entry_index]
        if (
            last_completed_at is not None
            and (entry["observed_at"] - last_completed_at).total_seconds()
            < cooldown_minutes * 60
        ):
            continue
        initial_price = float(entry["current_price"])
        entry_bar_at = entry["bar_at"]
        fills = [initial_price]
        next_leg_index = 0
        exit_index: int | None = None
        exit_price: float | None = None
        exit_reason = "right_censored"
        path_rows = [
            (index, row)
            for index, row in enumerate(rows[entry_index + 1 :], entry_index + 1)
            if row["session"] == session.session and row["venue"] == session.venue
        ]
        for index, row in path_rows:
            added_on_bar = False
            while next_leg_index < len(add_triggers_bps):
                add_price = initial_price * (
                    1.0 + add_triggers_bps[next_leg_index] / 10_000.0
                )
                if float(row["current_price"]) > add_price:
                    break
                fills.append(min(float(row["current_price"]), add_price))
                next_leg_index += 1
                added_on_bar = True
            average_price = statistics.fmean(fills)
            target_price = average_price * (1.0 + target_bps / 10_000.0)
            if added_on_bar:
                continue
            if float(row["current_price"]) >= target_price or (
                row["bar_at"] > entry_bar_at and float(row["high"]) >= target_price
            ):
                exit_index = index
                exit_price = target_price
                exit_reason = "fixed_average_take_profit"
                break
            if (
                session.force_flat
                and force_exit_time is not None
                and row["observed_at"].time() >= _clock(force_exit_time)
            ):
                exit_index = index
                exit_price = float(row["current_price"])
                exit_reason = "preclose_market_exit"
                break
        if exit_index is None and path_rows:
            exit_index, terminal = path_rows[-1]
            if session.force_flat:
                exit_price = float(terminal["current_price"])
                exit_reason = "session_terminal_fallback_exit"
        average_price = statistics.fmean(fills)
        gross_return_pct = (
            (float(exit_price) / average_price - 1.0) * 100.0
            if exit_price is not None
            else None
        )
        net_return_pct = (
            gross_return_pct - ROUND_TRIP_COST_PCT
            if gross_return_pct is not None
            else None
        )
        selected.append(
            {
                "trade_date": entry["trade_date"].isoformat(),
                "entry_at": entry["observed_at"].isoformat(),
                "entry_price": initial_price,
                "entry_state": entry["state"],
                "filled_leg_count": len(fills),
                "filled_prices": [round(value, 6) for value in fills],
                "average_price": round(average_price, 6),
                "exit_at": (
                    rows[exit_index]["observed_at"].isoformat()
                    if exit_index is not None
                    else None
                ),
                "exit_price": round(exit_price, 6) if exit_price is not None else None,
                "exit_reason": exit_reason,
                "gross_return_pct": (
                    round(gross_return_pct, 6) if gross_return_pct is not None else None
                ),
                "net_return_pct": (
                    round(net_return_pct, 6) if net_return_pct is not None else None
                ),
                "source_path": entry["source_path"],
                "source_line_number": entry["source_line_number"],
            }
        )
        if exit_index is not None:
            last_completed_at = rows[exit_index]["observed_at"]
        free_after_index = exit_index + 1 if exit_index is not None else len(rows)
    return selected


def _summary(trades: Sequence[dict[str, Any]]) -> dict[str, Any]:
    resolved = [row for row in trades if row.get("net_return_pct") is not None]
    values = [float(row["net_return_pct"]) for row in resolved]
    dates = sorted({str(row["trade_date"]) for row in trades})
    target_count = sum(
        row.get("exit_reason") == "fixed_average_take_profit" for row in trades
    )
    return {
        "signal_trade_count": len(trades),
        "distinct_signal_date_count": len(dates),
        "signal_dates": dates,
        "resolved_trade_count": len(resolved),
        "target_exit_count": target_count,
        "preclose_exit_count": sum(
            row.get("exit_reason")
            in {"preclose_market_exit", "session_terminal_fallback_exit"}
            for row in trades
        ),
        "right_censored_count": len(trades) - len(resolved),
        "target_completion_ratio": (
            round(target_count / len(trades), 6) if trades else None
        ),
        "equal_weight_avg_net_return_pct": (
            round(statistics.fmean(values), 6) if values else None
        ),
        "source_quality_adjusted_ev_pct": (
            round(sum(values) / len(trades), 6) if trades else None
        ),
        "simple_sum_net_return_pct": round(sum(values), 6) if values else None,
        "diagnostic_win_rate_pct": (
            round(sum(value > 0 for value in values) / len(values) * 100.0, 6)
            if values
            else None
        ),
        "worst_net_return_pct": round(min(values), 6) if values else None,
        "average_filled_leg_count": (
            round(statistics.fmean(row["filled_leg_count"] for row in trades), 6)
            if trades
            else None
        ),
    }


def _candidate_ready(
    spec: SymbolSpec,
    session: SessionSpec,
    summary: dict[str, Any],
) -> tuple[bool, str]:
    avg = summary.get("equal_weight_avg_net_return_pct")
    worst = summary.get("worst_net_return_pct")
    if summary["distinct_signal_date_count"] < spec.minimum_signal_dates:
        return False, "insufficient_distinct_signal_dates"
    if summary["signal_trade_count"] < spec.minimum_trades:
        return False, "insufficient_non_overlapping_trades"
    if session.force_flat:
        if summary["resolved_trade_count"] != summary["signal_trade_count"]:
            return False, "forced_flat_path_not_fully_resolved"
        if avg is None or float(avg) <= 0:
            return False, "cumulative_net_ev_not_positive"
        if summary["target_exit_count"] < 1:
            return False, "no_fixed_target_completion"
        if worst is None or float(worst) < -2.0:
            return False, "worst_trade_exceeds_bounded_initial_floor"
    else:
        if float(summary.get("target_completion_ratio") or 0.0) < 0.5:
            return False, "target_completion_ratio_below_half"
        if summary["target_exit_count"] < 2:
            return False, "insufficient_target_completions"
    return True, "bounded_cumulative_candidate_ready"


def _calibrate_session(
    spec: SymbolSpec,
    session: SessionSpec,
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    rows_by_date: dict[date, list[dict[str, Any]]] = {}
    for row in rows:
        if row["session"] == session.session and row["venue"] == session.venue:
            rows_by_date.setdefault(row["trade_date"], []).append(row)
    candidates: list[dict[str, Any]] = []
    for add_triggers in spec.add_trigger_arms:
        for target_bps in spec.target_bps_values:
            for max_entries in spec.max_entries_values:
                for cutoff in session.new_entry_cutoffs:
                    for cooldown in (5, 10, 20):
                        force_exit_times: tuple[str | None, ...] = (
                            session.force_exit_times if session.force_flat else (None,)
                        )
                        for force_exit_time in force_exit_times:
                            trades = [
                                trade
                                for day_rows in rows_by_date.values()
                                for trade in _simulate_day(
                                    day_rows,
                                    session=session,
                                    add_triggers_bps=add_triggers,
                                    target_bps=target_bps,
                                    max_entries=max_entries,
                                    cutoff=cutoff,
                                    cooldown_minutes=cooldown,
                                    force_exit_time=force_exit_time,
                                )
                            ]
                            summary = _summary(trades)
                            ready, reason = _candidate_ready(spec, session, summary)
                            candidates.append(
                                {
                                    "add_trigger_bps_from_initial_fill": list(
                                        add_triggers
                                    ),
                                    "target_bps": target_bps,
                                    "max_completed_entries_per_day": max_entries,
                                    "new_entry_cutoff_time": cutoff,
                                    "reentry_cooldown_minutes": cooldown,
                                    "force_exit_time": force_exit_time,
                                    "summary": summary,
                                    "ready": ready,
                                    "reason": reason,
                                    "trades": trades,
                                }
                            )

    def rank(candidate: dict[str, Any]) -> tuple[float, ...]:
        summary = candidate["summary"]
        if session.force_flat:
            return (
                float(candidate["ready"]),
                float(summary.get("source_quality_adjusted_ev_pct") or -999.0),
                float(summary.get("simple_sum_net_return_pct") or -999.0),
                float(candidate["target_bps"]),
                -float(summary.get("average_filled_leg_count") or 99.0),
            )
        return (
            float(candidate["ready"]),
            float(summary.get("source_quality_adjusted_ev_pct") or -999.0),
            float(summary.get("simple_sum_net_return_pct") or -999.0),
            float(summary.get("target_completion_ratio") or 0.0),
            float(candidate["target_bps"]),
            -float(summary.get("right_censored_count") or 0),
        )

    selected = max(candidates, key=rank) if candidates else None
    if selected is None:
        return {
            "decision": "no_candidate_rows",
            "selected_policy": None,
            "candidate_count": 0,
        }
    selected_dates = selected["summary"]["signal_dates"]
    holdout_dates = selected_dates[-1:] if len(selected_dates) >= 2 else []
    holdout = _summary(
        [row for row in selected["trades"] if row["trade_date"] in holdout_dates]
    )
    return {
        "decision": (
            "widget_auto_trade_policy_candidate_ready"
            if selected["ready"]
            else selected["reason"]
        ),
        "candidate_count": len(candidates),
        "selected_policy": {
            key: selected[key]
            for key in (
                "add_trigger_bps_from_initial_fill",
                "target_bps",
                "max_completed_entries_per_day",
                "new_entry_cutoff_time",
                "reentry_cooldown_minutes",
                "force_exit_time",
            )
        },
        "selected_summary": selected["summary"],
        "latest_date_holdout_summary": holdout,
        "selected_trades": selected["trades"],
        "policy_tier": "bounded_initial_cumulative_small_sample",
        "rollback_condition": (
            "next cumulative source-quality-adjusted net EV <= 0; "
            "unresolved forced-flat path; "
            "worst trade < -2%; source-quality/policy verification failure; or "
            "prior-day widget-owned inventory remains"
        ),
    }


def build_report(*, target_date: date) -> dict[str, Any]:
    if target_date < CLEAN_BASELINE_DATE:
        raise ValueError("target date precedes clean baseline")
    effective_date = _next_krx_trading_date(target_date)
    symbol_reports: dict[str, Any] = {}
    source_paths: list[str] = []
    for spec in SPECS:
        rows, paths = _load_rows(spec, target_date=target_date)
        source_paths.extend(paths)
        sessions = {
            session.session: _calibrate_session(spec, session, rows)
            for session in spec.sessions
        }
        symbol_reports[spec.symbol] = {
            "name": spec.name,
            "source_row_count": len(rows),
            "source_dates": sorted({row["trade_date"].isoformat() for row in rows}),
            "sessions": sessions,
        }
    ready_count = sum(
        session_report["decision"] == "widget_auto_trade_policy_candidate_ready"
        for symbol_report in symbol_reports.values()
        for session_report in symbol_report["sessions"].values()
    )
    return {
        "schema": "widget_auto_trade_policy_calibration_report_v1",
        "status": "complete",
        "target_date": target_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "round_trip_cost_pct": ROUND_TRIP_COST_PCT,
        "source_paths": sorted(set(source_paths)),
        "source_quality_status": "PASS" if source_paths else "BLOCKED",
        "ready_session_policy_count": ready_count,
        "symbols": symbol_reports,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_policy(report: dict[str, Any]) -> dict[str, Any]:
    target_date = str(report["target_date"])
    effective_date = str(report["effective_date"])
    policy_symbols: dict[str, Any] = {}
    for spec in SPECS:
        source = report["symbols"][spec.symbol]
        session_specs = {value.session: value for value in spec.sessions}
        sessions: dict[str, Any] = {}
        for session_name, calibration in source["sessions"].items():
            if calibration["decision"] != "widget_auto_trade_policy_candidate_ready":
                continue
            selected = calibration["selected_policy"]
            session_spec = session_specs[session_name]
            sessions[session_name] = {
                "enabled": True,
                "market_venue": session_spec.venue,
                "allowed_entry_states": sorted(ACTIONABLE_STATES),
                "leg_quantity_each": 1,
                "add_trigger_bps_from_initial_fill": selected[
                    "add_trigger_bps_from_initial_fill"
                ],
                "take_profit_bps_from_equal_share_average": selected["target_bps"],
                "max_completed_entries_per_day": selected[
                    "max_completed_entries_per_day"
                ],
                "reentry_cooldown_minutes": selected["reentry_cooldown_minutes"],
                "new_entry_cutoff_time": selected["new_entry_cutoff_time"],
                "force_flat_at_session_end": session_spec.force_flat,
                "force_exit_time": selected["force_exit_time"],
                "overnight_forbidden": session_spec.overnight_forbidden,
                "source_final_exit_action": "observe_only_no_forced_sell",
                "research_arm": (
                    f"equal_share_{selected['add_trigger_bps_from_initial_fill']}_"
                    f"tp{selected['target_bps']}_multi"
                ),
                "evidence_window": (f"{CLEAN_BASELINE_DATE.isoformat()}_{target_date}"),
                "evidence_artifact": (
                    "data/report/widget_auto_trade_policy_calibration/"
                    f"widget_auto_trade_policy_calibration_{target_date}.json"
                ),
                "policy_tier": calibration["policy_tier"],
                "rollback_condition": calibration["rollback_condition"],
                "actual_order_submitted": False,
                "broker_guard_bypass": False,
            }
        if sessions:
            policy_symbols[spec.symbol] = {"name": spec.name, "sessions": sessions}
    policy = {
        "schema": POLICY_SCHEMA,
        "status": "verified" if policy_symbols else "no_ready_policy",
        "policy_version": f"widget_auto_trade_policy_{effective_date}_from_{target_date}",
        "source_target_date": target_date,
        "effective_date": effective_date,
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "source_quality_status": report["source_quality_status"],
        "authority": POLICY_AUTHORITY,
        "evidence_report_path": (
            "data/report/widget_auto_trade_policy_calibration/"
            f"widget_auto_trade_policy_calibration_{target_date}.json"
        ),
        "symbols": policy_symbols,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
    }
    return policy


def verify_policy(policy: dict[str, Any], *, policy_dir: Path) -> dict[str, Any]:
    effective_date = date.fromisoformat(str(policy["effective_date"]))
    verification_path = policy_dir / (
        f"{POLICY_FILE_PREFIX}_{effective_date.isoformat()}.json"
    )
    loaded = WidgetAutoTradePolicyLoader(policy_dir).resolve_all(
        observed_date=effective_date
    )
    expected_sessions = {
        (symbol, session)
        for symbol, symbol_payload in policy.get("symbols", {}).items()
        for session in symbol_payload.get("sessions", {})
    }
    loaded_sessions = {
        (symbol, session) for symbol, sessions in loaded.items() for session in sessions
    }
    issues = (
        []
        if loaded_sessions == expected_sessions
        else ["dated_policy_loader_round_trip_mismatch"]
    )
    return {
        "status": "pass" if not issues else "fail",
        "issues": issues,
        "policy_path": str(verification_path),
        "loaded_session_count": len(loaded_sessions),
    }


def write_outputs(
    report: dict[str, Any],
    policy: dict[str, Any],
    *,
    output_dir: Path,
    policy_dir: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    target_date = str(report["target_date"])
    report_path = (
        output_dir / f"widget_auto_trade_policy_calibration_{target_date}.json"
    )
    policy_path = policy_dir / (f"{POLICY_FILE_PREFIX}_{policy['effective_date']}.json")
    policy["evidence_report_path"] = str(report_path)
    for symbol_payload in policy.get("symbols", {}).values():
        for session_payload in symbol_payload.get("sessions", {}).values():
            session_payload["evidence_artifact"] = str(report_path)
    expected_session_count = sum(
        len(symbol_payload.get("sessions", {}))
        for symbol_payload in policy.get("symbols", {}).values()
    )
    report["policy_verification"] = {
        "status": "pass",
        "issues": [],
        "policy_path": str(policy_path),
        "loaded_session_count": expected_session_count,
    }
    report["policy_path"] = str(policy_path)
    _atomic_write(report_path, report)
    _atomic_write(policy_path, policy)
    verification = verify_policy(policy, policy_dir=policy_dir)
    if verification["status"] != "pass":
        report["policy_verification"] = verification
        _atomic_write(report_path, report)
        raise RuntimeError("widget auto-trade policy verification failed")
    return report_path, policy_path, verification


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else _resolve_default_target_date()
    )
    now = datetime.now(KST)
    if target_date > now.date() or (
        target_date == now.date() and now.time() < POSTCLOSE_COMPLETE_TIME
    ):
        raise SystemExit("target-date must be a fully completed prior KST date")
    report = build_report(target_date=target_date)
    policy = build_policy(report)
    result: dict[str, Any] = {
        "status": report["status"],
        "target_date": report["target_date"],
        "effective_date": report["effective_date"],
        "ready_session_policy_count": report["ready_session_policy_count"],
        "policy_status": policy["status"],
        "runtime_effect": False,
    }
    if args.write:
        report_path, policy_path, verification = write_outputs(
            report,
            policy,
            output_dir=args.output_dir,
            policy_dir=args.policy_dir,
        )
        result.update(
            {
                "report_path": str(report_path),
                "policy_path": str(policy_path),
                "policy_verification": verification,
            }
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
