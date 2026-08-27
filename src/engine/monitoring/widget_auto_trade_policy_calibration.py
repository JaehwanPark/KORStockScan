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
import math
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
from src.engine.monitoring.machine_microstructure_attribution import (
    OUTPUT_DIR as MACHINE_MICROSTRUCTURE_REPORT_DIR,
    load_prior_owner_diagnostic,
)
from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    cost_aware_return_pct,
)
from src.engine.monitoring.samsung_widget_contract import (
    DEFAULT_OBSERVATION_DIR as SAMSUNG_OBSERVATION_DIR,
    KST,
    SAMSUNG_CODE,
    SAMSUNG_NAME,
    previous_krx_trading_date,
)
from src.trading.widget_auto_trade.policy import (
    CUMULATIVE_RESEARCH_GATE_SYMBOLS,
    CUMULATIVE_RESEARCH_MIN_QUALIFIED_DATES,
    CUMULATIVE_RESEARCH_QUALIFICATION_CONTRACT,
    CUMULATIVE_RESEARCH_START_DATE,
    DEFAULT_POLICY_DIR,
    POLICY_AUTHORITY,
    POLICY_FILE_PREFIX,
    POLICY_SCHEMA,
    SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL,
    WIDGET_AUTO_TRADE_LEG_QUANTITY,
    WidgetAutoTradePolicyLoader,
)
from src.utils.market_day import is_krx_trading_day

CLEAN_BASELINE_DATE = date(2026, 6, 5)
DEFAULT_OUTPUT_DIR = Path("data/report/widget_auto_trade_policy_calibration")
DEFAULT_EXECUTION_EVENT_DIR = Path("data/report/widget_signal_auto_trade_events")
ACTIONABLE_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
POSTCLOSE_COMPLETE_TIME = time(20, 1)
ENTRY_CAP_VALUES = tuple(range(1, 6))
HIGH_ENTRY_CAP_START = 4
INCONCLUSIVE_HOLDOUT_DECISIONS = frozenset(
    {
        "independent_holdout_signal_missing",
        "independent_holdout_target_missing",
        "independent_holdout_incremental_entry_cap_missing",
    }
)
RUNTIME_READY_DECISIONS = frozenset(
    {
        "widget_auto_trade_policy_candidate_ready",
        "carry_forward_previous_verified_policy",
    }
)

METRIC_CONTRACT = {
    "metric_role": "bounded_widget_auto_trade_policy_calibration",
    "decision_authority": POLICY_AUTHORITY,
    "window_policy": "clean_baseline_cumulative_completed_dates_prior_to_effective_date",
    "sample_floor": (
        "two_source_qualified_signal_dates_and_two_non_overlapping_trades;"
        "daily_entry_caps_1_through_5_compared;caps_4_and_5_require_positive_"
        "incremental_source_quality_adjusted_ev_in_calibration_and_holdout;"
        "small_samples_remain_bounded_initial;Doosan_and_Hanwha_require_40_"
        "qualified_KRX_observation_dates_from_2026-08-12"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "lifecycle_speed_diagnostics": {
        "metric_role": "diagnostic_execution_velocity_and_capital_occupancy",
        "decision_authority": "postclose_diagnostic_only",
        "window_policy": "per_resolved_or_right_censored_widget_trade_lifecycle",
        "sample_floor": "one_single_fill_leg_with_aware_entry_and_exit_timestamps",
        "primary_decision_metric": "cost_aware_realized_return_per_capital_hour",
        "primary_decision_metric_unit": (
            "realized_profit_krw_per_capital_occupied_krw_hour"
        ),
        "source_quality_gate": (
            "ordered_aware_timestamps_and_single_leg_exact_occupancy_only"
        ),
        "forbidden_uses": [
            "multi_leg_first_entry_duration_as_exact_capital_occupancy",
            "speed_or_gross_return_as_policy_selection_authority",
            "target_cooldown_cap_quantity_or_force_exit_mutation",
        ],
        "gross_no_slippage_role": "diagnostic_only_not_live_promotion_authority",
        "fields": [
            "gross_no_slippage_avg_return_pct",
            "median_resolved_holding_duration_sec",
            "p90_resolved_holding_duration_sec",
            "target_exit_within_180s_ratio",
            "observed_occupancy_seconds_sum",
            "right_censored_occupancy_seconds_sum",
            "observed_capital_occupied_krw_seconds",
            "cost_aware_realized_return_per_capital_hour",
        ],
        "selection_effect": False,
        "missing_timestamp_policy": "unknown_not_zero_or_instant_exit",
    },
    "source_quality_gate": (
        "completed_prior_dates;fresh_actionable_source_rows;valid_completed_bar_ohlc;"
        "venue_and_session_provenance;chronological_holdout_not_used_for_selection;"
        "real_execution_submit_or_terminal_failure_veto"
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
        "gross_no_slippage_or_speed_diagnostic_as_standalone_policy_authority",
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
    analysis_start_date: date
    minimum_qualified_observation_dates: int


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
        max_entries_values=ENTRY_CAP_VALUES,
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=CLEAN_BASELINE_DATE,
        minimum_qualified_observation_dates=0,
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
        max_entries_values=ENTRY_CAP_VALUES,
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=CUMULATIVE_RESEARCH_START_DATE,
        minimum_qualified_observation_dates=CUMULATIVE_RESEARCH_MIN_QUALIFIED_DATES,
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
        max_entries_values=ENTRY_CAP_VALUES,
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=CUMULATIVE_RESEARCH_START_DATE,
        minimum_qualified_observation_dates=CUMULATIVE_RESEARCH_MIN_QUALIFIED_DATES,
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


def resolve_completed_policy_target_date() -> date:
    """Return the latest KRX date complete for every evaluation-chain stage."""

    now = datetime.now(KST)
    if is_krx_trading_day(now.date()) and now.time() >= POSTCLOSE_COMPLETE_TIME:
        return now.date()
    return previous_krx_trading_date(now.date())


def _resolve_default_target_date() -> date:
    """Compatibility wrapper for existing callers and tests."""

    return resolve_completed_policy_target_date()


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


def _optional_lifecycle_event_valid(
    event: dict[str, Any],
    *,
    expected_type: str,
    symbol: str,
    source_date: date,
    episode_sequence: int | None,
) -> bool:
    event_id = str(event.get("event_id") or "").strip()
    parts = event_id.split(":")
    suffix = parts[4] if len(parts) == 5 else ""
    suffix_valid = bool(
        suffix.isdigit()
        and (
            len(suffix) == 6
            or (len(suffix) == 14 and suffix.startswith(source_date.strftime("%Y%m%d")))
        )
    )
    event_sequence = event.get("episode_sequence")
    try:
        event_at = datetime.fromisoformat(str(event.get("observed_at") or ""))
    except ValueError:
        event_at = None
    if event_at is not None and event_at.tzinfo is not None:
        event_at = event_at.astimezone(KST)
    else:
        event_at = None
    return bool(
        episode_sequence is not None
        and len(parts) == 5
        and parts[0] == symbol
        and parts[1] == source_date.isoformat()
        and parts[2] == expected_type
        and parts[3].isdigit()
        and int(parts[3]) == episode_sequence
        and suffix_valid
        and event.get("event_type") == expected_type
        and event_sequence in {None, episode_sequence}
        and event_at is not None
        and event_at.date() == source_date
        and event.get("source_quality_status") == "PASS"
        and event.get("actual_order_submitted") is False
        and event.get("broker_order_forbidden") is True
        and event.get("runtime_effect") is False
        and (
            expected_type != "ENTRY"
            or (
                event.get("state") in ACTIONABLE_STATES
                and _positive_price(event.get("entry_price_high")) is not None
                and _positive_price(event.get("target_price")) is not None
                and _positive_price(event.get("structural_support")) is not None
            )
        )
        and (
            expected_type != "EXIT"
            or (
                bool(str(event.get("reason") or "").strip())
                and _positive_price(event.get("reference_exit_price")) is not None
            )
        )
    )


def _load_rows(
    spec: SymbolSpec, *, target_date: date
) -> tuple[list[dict[str, Any]], list[str], dict[str, int | bool]]:
    rows: list[dict[str, Any]] = []
    source_paths: list[str] = []
    audit_counts = {
        "raw_line_count": 0,
        "accepted_row_count": 0,
        "invalid_json_or_object_count": 0,
        "required_contract_missing_count": 0,
        "invalid_observed_at_or_date_count": 0,
        "invalid_price_or_bar_time_count": 0,
        "invalid_optional_lifecycle_event_count": 0,
        "expected_source_blocked_without_completed_bar_count": 0,
    }
    for path in sorted(spec.observation_dir.glob(f"{spec.prefix}_*.jsonl")):
        raw_date = path.stem.rsplit("_", 1)[-1]
        try:
            source_date = datetime.strptime(raw_date, "%Y%m%d").date()
        except ValueError:
            continue
        if source_date < spec.analysis_start_date or source_date > target_date:
            continue
        source_paths.append(str(path))
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                audit_counts["raw_line_count"] += 1
                try:
                    payload = json.loads(line)
                except ValueError:
                    audit_counts["invalid_json_or_object_count"] += 1
                    continue
                if not isinstance(payload, dict):
                    audit_counts["invalid_json_or_object_count"] += 1
                    continue
                advisory = payload.get("advisory")
                latest_bar = payload.get("latest_completed_bar")
                if not isinstance(advisory, dict):
                    audit_counts["required_contract_missing_count"] += 1
                    continue
                if not isinstance(latest_bar, dict):
                    source_quality_status = str(
                        (advisory.get("source_quality") or {}).get("status") or ""
                    )
                    if source_quality_status and source_quality_status != "PASS":
                        audit_counts[
                            "expected_source_blocked_without_completed_bar_count"
                        ] += 1
                    else:
                        audit_counts["required_contract_missing_count"] += 1
                    continue
                entry_event = payload.get("entry_event")
                exit_event = payload.get("exit_event")
                episode = payload.get("episode")
                if any(
                    value is not None and not isinstance(value, dict)
                    for value in (entry_event, exit_event, episode)
                ):
                    audit_counts["invalid_optional_lifecycle_event_count"] += 1
                    continue
                episode_sequence = (
                    int(episode.get("sequence"))
                    if isinstance(episode, dict)
                    and not isinstance(episode.get("sequence"), bool)
                    and isinstance(episode.get("sequence"), int)
                    and int(episode["sequence"]) > 0
                    else None
                )
                episode_contract_valid = bool(
                    not isinstance(episode, dict)
                    or (
                        episode_sequence is not None
                        and episode.get("actual_order_submitted") is False
                        and episode.get("broker_order_forbidden") is True
                        and episode.get("runtime_effect") is False
                    )
                )
                if not episode_contract_valid:
                    audit_counts["invalid_optional_lifecycle_event_count"] += 1
                    continue
                if any(
                    isinstance(event, dict)
                    and not _optional_lifecycle_event_valid(
                        event,
                        expected_type=expected_type,
                        symbol=spec.symbol,
                        source_date=source_date,
                        episode_sequence=episode_sequence,
                    )
                    for event, expected_type in (
                        (entry_event, "ENTRY"),
                        (exit_event, "EXIT"),
                    )
                ):
                    audit_counts["invalid_optional_lifecycle_event_count"] += 1
                    continue
                try:
                    observed_at = datetime.fromisoformat(
                        str(payload.get("observed_at_kst") or "")
                    ).astimezone(KST)
                except ValueError:
                    audit_counts["invalid_observed_at_or_date_count"] += 1
                    continue
                if observed_at.date() != source_date:
                    audit_counts["invalid_observed_at_or_date_count"] += 1
                    continue
                current_price = _positive_price(payload.get("current_price"))
                bar_low = _positive_price(latest_bar.get("low"))
                bar_high = _positive_price(latest_bar.get("high"))
                if (
                    current_price is None
                    or bar_low is None
                    or bar_high is None
                    or bar_low > bar_high
                ):
                    audit_counts["invalid_price_or_bar_time_count"] += 1
                    continue
                try:
                    bar_at = datetime.strptime(
                        str(latest_bar.get("source_time") or ""), "%Y%m%d%H%M%S"
                    ).replace(tzinfo=KST)
                except ValueError:
                    audit_counts["invalid_price_or_bar_time_count"] += 1
                    continue
                if bar_at.date() != source_date or bar_at > observed_at:
                    audit_counts["invalid_price_or_bar_time_count"] += 1
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
                        "low": bar_low,
                        "high": bar_high,
                        "bar_at": bar_at,
                        "source_quality_status": str(
                            (advisory.get("source_quality") or {}).get("status") or ""
                        ),
                        "entry_event_id": (
                            str(entry_event.get("event_id") or "")
                            if isinstance(entry_event, dict)
                            else ""
                        ),
                        "entry_event_state": (
                            str(entry_event.get("state") or "")
                            if isinstance(entry_event, dict)
                            else ""
                        ),
                        "exit_event_id": (
                            str(exit_event.get("event_id") or "")
                            if isinstance(exit_event, dict)
                            else ""
                        ),
                        "exit_event_reason": (
                            str(exit_event.get("reason") or "")
                            if isinstance(exit_event, dict)
                            else ""
                        ),
                        "exit_event_reference_price": (
                            _positive_price(exit_event.get("reference_exit_price"))
                            if isinstance(exit_event, dict)
                            else None
                        ),
                        "entry_event_at": (
                            datetime.fromisoformat(str(entry_event["observed_at"]))
                            .astimezone(KST)
                            if isinstance(entry_event, dict)
                            else None
                        ),
                        "exit_event_at": (
                            datetime.fromisoformat(str(exit_event["observed_at"]))
                            .astimezone(KST)
                            if isinstance(exit_event, dict)
                            else None
                        ),
                        "episode_sequence": (episode_sequence),
                        "structural_support": (
                            _positive_price(episode.get("structural_support"))
                            if isinstance(episode, dict)
                            else None
                        ),
                        "source_path": str(path),
                        "source_line_number": line_number,
                    }
                )
                audit_counts["accepted_row_count"] += 1
    rows.sort(key=lambda row: row["observed_at"])
    excluded = audit_counts["raw_line_count"] - audit_counts["accepted_row_count"]
    return (
        rows,
        source_paths,
        {
            **audit_counts,
            "excluded_row_count": excluded,
            "raw_row_exclusion_applied": excluded > 0,
        },
    )


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
    source_final_exit_action: str = "sell_own_filled_quantity",
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
        entry_episode_sequence = entry.get("episode_sequence")
        last_fill_minute = entry["observed_at"].replace(second=0, microsecond=0)
        fills = [initial_price]
        next_leg_index = 0
        exit_index: int | None = None
        exit_price: float | None = None
        exit_price_provenance: str | None = None
        exit_reason = "right_censored"
        path_rows = [
            (index, row)
            for index, row in enumerate(rows[entry_index + 1 :], entry_index + 1)
            if row["session"] == session.session
            and row["venue"] == session.venue
            and row["source_quality_status"] == "PASS"
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
                last_fill_minute = row["observed_at"].replace(second=0, microsecond=0)
            average_price = statistics.fmean(fills)
            target_price = average_price * (1.0 + target_bps / 10_000.0)
            if added_on_bar:
                continue
            source_exit_reason = str(row.get("exit_event_reason") or "")
            source_exit_same_episode = bool(
                source_exit_reason
                and entry_episode_sequence is not None
                and row.get("episode_sequence") == entry_episode_sequence
                and isinstance(row.get("exit_event_at"), datetime)
                and row["exit_event_at"] > entry["observed_at"]
            )
            if (
                source_final_exit_action == "sell_own_filled_quantity"
                and source_exit_same_episode
            ):
                exit_index = index
                exit_price = float(
                    row.get("exit_event_reference_price") or row["current_price"]
                )
                exit_price_provenance = "source_final_exit_reference_price"
                exit_reason = source_exit_reason
                break
            if float(row["current_price"]) >= target_price or (
                row["bar_at"] > last_fill_minute and float(row["high"]) >= target_price
            ):
                exit_index = index
                exit_price = target_price
                exit_price_provenance = "fixed_average_take_profit_target"
                exit_reason = "fixed_average_take_profit"
                break
            if (
                session.force_flat
                and force_exit_time is not None
                and row["observed_at"].time() >= _clock(force_exit_time)
            ):
                exit_index = index
                exit_price = float(row["current_price"])
                exit_price_provenance = "observed_current_price"
                exit_reason = "preclose_market_exit"
                break
        if exit_index is None and path_rows:
            exit_index, terminal = path_rows[-1]
            if session.force_flat:
                exit_price = float(terminal["current_price"])
                exit_price_provenance = "observed_current_price"
                exit_reason = "session_terminal_fallback_exit"
        average_price = statistics.fmean(fills)
        gross_return_pct = (
            (float(exit_price) / average_price - 1.0) * 100.0
            if exit_price is not None
            else None
        )
        cost_contract = comparison_cost_contract(entry["trade_date"])
        net_return_pct = (
            cost_aware_return_pct(
                gross_return_pct,
                trade_date=entry["trade_date"],
            )
            if gross_return_pct is not None
            else None
        )
        selected.append(
            {
                "trade_date": entry["trade_date"].isoformat(),
                "daily_entry_ordinal": len(selected) + 1,
                "entry_at": entry["observed_at"].isoformat(),
                "entry_price": initial_price,
                "entry_state": entry["state"],
                "entry_event_id": entry.get("entry_event_id") or None,
                "structural_support": entry.get("structural_support"),
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
                "exit_price_provenance": exit_price_provenance,
                "gross_return_pct": (
                    round(gross_return_pct, 6) if gross_return_pct is not None else None
                ),
                "net_return_pct": (
                    round(net_return_pct, 6) if net_return_pct is not None else None
                ),
                "round_trip_cost_pct": cost_contract["round_trip_cost_pct"],
                "cost_policy_id": cost_contract["policy_id"],
                "cost_contract_sha256": cost_contract["contract_sha256"],
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
    gross_values = [
        float(row["gross_return_pct"])
        for row in resolved
        if row.get("gross_return_pct") is not None
    ]
    lifecycle_durations: list[tuple[dict[str, Any], float]] = []
    for row in trades:
        try:
            entry_at = datetime.fromisoformat(str(row.get("entry_at") or ""))
            exit_at = datetime.fromisoformat(str(row.get("exit_at") or ""))
        except ValueError:
            continue
        if entry_at.tzinfo is None or exit_at.tzinfo is None or exit_at < entry_at:
            continue
        lifecycle_durations.append((row, (exit_at - entry_at).total_seconds()))
    resolved_holding_durations = [
        duration
        for row, duration in lifecycle_durations
        if row.get("net_return_pct") is not None
    ]
    target_holding_durations = [
        duration
        for row, duration in lifecycle_durations
        if row.get("exit_reason") == "fixed_average_take_profit"
    ]
    right_censored_holding_durations = [
        duration
        for row, duration in lifecycle_durations
        if row.get("exit_reason") == "right_censored"
    ]
    observed_capital_occupied_krw_seconds = 0.0
    observed_cost_aware_realized_profit_krw = 0.0
    capital_timing_trade_count = 0
    capital_occupancy_unavailable_multi_leg_trade_count = 0
    for row, duration in lifecycle_durations:
        average_price = _positive_price(
            row.get("average_price") or row.get("entry_price")
        )
        try:
            filled_leg_count = int(row.get("filled_leg_count") or 0)
        except (TypeError, ValueError):
            filled_leg_count = 0
        if average_price is None or filled_leg_count <= 0:
            continue
        if filled_leg_count != 1:
            capital_occupancy_unavailable_multi_leg_trade_count += 1
            continue
        notional = average_price * filled_leg_count * WIDGET_AUTO_TRADE_LEG_QUANTITY
        observed_capital_occupied_krw_seconds += notional * duration
        capital_timing_trade_count += 1
        if row.get("net_return_pct") is not None:
            observed_cost_aware_realized_profit_krw += (
                notional * float(row["net_return_pct"]) / 100.0
            )
    ordered_resolved_durations = sorted(resolved_holding_durations)
    p90_resolved_duration = (
        ordered_resolved_durations[
            max(0, math.ceil(len(ordered_resolved_durations) * 0.9) - 1)
        ]
        if ordered_resolved_durations
        else None
    )
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
            round(sum(values) / len(resolved), 6) if resolved else None
        ),
        "gross_no_slippage_avg_return_pct": (
            round(statistics.fmean(gross_values), 6) if gross_values else None
        ),
        "lifecycle_timing_trade_count": len(lifecycle_durations),
        "lifecycle_timing_missing_trade_count": len(trades) - len(lifecycle_durations),
        "median_resolved_holding_duration_sec": (
            round(statistics.median(resolved_holding_durations), 3)
            if resolved_holding_durations
            else None
        ),
        "p90_resolved_holding_duration_sec": (
            round(p90_resolved_duration, 3)
            if p90_resolved_duration is not None
            else None
        ),
        "target_exit_within_180s_count": sum(
            duration <= 180.0 for duration in target_holding_durations
        ),
        "target_exit_within_180s_ratio": (
            round(
                sum(duration <= 180.0 for duration in target_holding_durations)
                / len(target_holding_durations),
                6,
            )
            if target_holding_durations
            else None
        ),
        "observed_occupancy_seconds_sum": (
            round(sum(duration for _, duration in lifecycle_durations), 3)
            if lifecycle_durations
            else None
        ),
        "right_censored_occupancy_seconds_sum": (
            round(sum(right_censored_holding_durations), 3)
            if right_censored_holding_durations
            else None
        ),
        "capital_timing_trade_count": capital_timing_trade_count,
        "capital_occupancy_unavailable_multi_leg_trade_count": (
            capital_occupancy_unavailable_multi_leg_trade_count
        ),
        "observed_capital_occupied_krw_seconds": (
            round(observed_capital_occupied_krw_seconds, 3)
            if capital_timing_trade_count
            else None
        ),
        "capital_timing_cohort_cost_aware_realized_net_profit_krw": (
            round(observed_cost_aware_realized_profit_krw, 3)
            if capital_timing_trade_count
            else None
        ),
        "cost_aware_realized_return_per_capital_hour": (
            round(
                observed_cost_aware_realized_profit_krw
                / (observed_capital_occupied_krw_seconds / 3600.0),
                9,
            )
            if observed_capital_occupied_krw_seconds > 0
            else None
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


def _entry_cap_comparison(
    trades: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    comparison: dict[str, dict[str, Any]] = {}
    for cap in ENTRY_CAP_VALUES:
        cumulative = [
            row for row in trades if int(row.get("daily_entry_ordinal") or 0) <= cap
        ]
        incremental = [
            row for row in trades if int(row.get("daily_entry_ordinal") or 0) == cap
        ]
        incremental_summary = _summary(incremental)
        incremental_ev = incremental_summary.get("source_quality_adjusted_ev_pct")
        comparison[str(cap)] = {
            "cumulative": _summary(cumulative),
            "incremental": incremental_summary,
            "incremental_ev_positive": bool(
                incremental_summary["signal_trade_count"] > 0
                and incremental_ev is not None
                and float(incremental_ev) > 0.0
            ),
        }
    return comparison


def _incremental_entry_cap_ready(
    comparison: dict[str, dict[str, Any]], cap: int
) -> tuple[bool, str]:
    if cap < HIGH_ENTRY_CAP_START:
        return True, "incremental_entry_cap_not_required"
    for incremental_cap in range(HIGH_ENTRY_CAP_START, cap + 1):
        evidence = comparison.get(str(incremental_cap), {})
        incremental = evidence.get("incremental")
        if (
            not isinstance(incremental, dict)
            or int(incremental.get("signal_trade_count") or 0) < 1
        ):
            return False, f"incremental_entry_cap_{incremental_cap}_sample_missing"
        if evidence.get("incremental_ev_positive") is not True:
            return False, f"incremental_entry_cap_{incremental_cap}_ev_not_positive"
    return True, "incremental_entry_cap_ev_positive"


def _holdout_date_count(source_date_count: int) -> int:
    if source_date_count < 3:
        return 0
    if source_date_count < 10:
        return 1
    return max(2, min(10, round(source_date_count * 0.20)))


def _load_execution_quality(
    symbol: str,
    *,
    target_date: date,
    event_dir: Path = DEFAULT_EXECUTION_EVENT_DIR,
    session: str | None = None,
) -> dict[str, Any]:
    path = event_dir / f"widget_signal_auto_trade_events_{target_date:%Y%m%d}.jsonl"
    counts: dict[str, int] = {}
    accepted_order_count = 0
    attributed_event_count = 0
    unattributed_execution_failure_count = 0
    terminal_failure_types = {
        "buy_cancel_terminal_failure",
        "sell_terminal_failure",
        "take_profit_cancel_terminal_failure",
        "take_profit_terminal_failure",
    }
    submit_failure_types = {
        "order_submit_failed",
        "order_submit_ambiguous",
    }
    execution_failure_types = terminal_failure_types | submit_failure_types

    def event_session(row: dict[str, Any]) -> str | None:
        for key in (
            "execution_policy_session",
            "market_session",
            "session_bucket",
            "session",
        ):
            value = str(row.get(key) or "").strip().upper()
            if value in {"KRX_REGULAR", "NXT_PREMARKET", "NXT_AFTERMARKET"}:
                return value
        for key in ("signal_id", "parent_entry_signal_id"):
            value = str(row.get(key) or "").upper()
            for candidate in ("KRX_REGULAR", "NXT_PREMARKET", "NXT_AFTERMARKET"):
                if f":{candidate}:" in value:
                    return candidate
        venue = str(row.get("market_venue") or "").strip().upper()
        if venue == "KRX":
            return "KRX_REGULAR"
        if venue == "NXT":
            try:
                observed = datetime.fromisoformat(str(row.get("observed_at") or ""))
            except ValueError:
                return None
            return (
                "NXT_PREMARKET"
                if observed.timetz().replace(tzinfo=None) < time(9, 0)
                else "NXT_AFTERMARKET"
            )
        return None

    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict) or str(row.get("symbol") or "") != symbol:
                    continue
                event_type = str(row.get("event_type") or "")
                if not event_type:
                    continue
                row_session = event_session(row)
                if session is not None and row_session != session:
                    # Any unscoped execution failure remains a global safety
                    # veto. Ordinary unscoped observations are diagnostics,
                    # not evidence for a different session. Submit rejects and
                    # broker-call ambiguity must not disappear merely because
                    # their failing producer omitted session provenance.
                    if (
                        event_type not in execution_failure_types
                        or row_session is not None
                    ):
                        continue
                    unattributed_execution_failure_count += 1
                else:
                    attributed_event_count += 1
                counts[event_type] = counts.get(event_type, 0) + 1
                if (
                    event_type == "order_submitted"
                    and row.get("actual_order_submitted") is True
                ):
                    accepted_order_count += 1
    terminal_failures = sum(
        count
        for event_type, count in counts.items()
        if event_type in terminal_failure_types
    )
    submit_failures = sum(
        counts.get(event_type, 0) for event_type in submit_failure_types
    )
    ambiguous_submit_failures = counts.get("order_submit_ambiguous", 0)
    execution_failures = terminal_failures + submit_failures
    return {
        "status": "SAFETY_VETO" if execution_failures else "PASS",
        "source_path": str(path) if path.exists() else None,
        "accepted_order_count": accepted_order_count,
        "order_submit_failed_count": submit_failures,
        "order_submit_ambiguous_count": ambiguous_submit_failures,
        "execution_failure_count": execution_failures,
        "failure_reason_codes": sorted(
            reason
            for reason, active in (
                (
                    "broker_order_submit_ambiguous",
                    ambiguous_submit_failures > 0,
                ),
                (
                    "broker_order_submit_failed",
                    submit_failures > ambiguous_submit_failures,
                ),
                ("terminal_order_or_cancel_failed", terminal_failures > 0),
            )
            if active
        ),
        "terminal_execution_failure_count": terminal_failures,
        "terminal_sell_failure_count": terminal_failures,
        "event_counts": dict(sorted(counts.items())),
        # A broker-rejected entry means the policy had an eligible live sample
        # but could not execute it.  Treating that path as an empty/healthy
        # sample lets the same policy be selected again without repairing the
        # producer or broker contract.  Keep naturally empty sessions eligible,
        # but fail closed when an actual submit attempt was rejected.
        "runtime_apply_allowed": execution_failures == 0,
        "decision_authority": "execution_quality_real_only_safety_veto",
        "execution_event_scope": session or "symbol_all_sessions",
        "session_attributed_event_count": attributed_event_count,
        "unattributed_execution_failure_count": (unattributed_execution_failure_count),
        # Compatibility field retained for consumers of the previous report
        # schema. It now reflects every unattributed execution failure rather
        # than silently excluding submit failures.
        "unattributed_terminal_failure_count": (unattributed_execution_failure_count),
        "execution_sample_observed": accepted_order_count > 0 or execution_failures > 0,
    }


def _session_execution_quality(
    symbol_report: dict[str, Any], session: str
) -> dict[str, Any]:
    by_session = symbol_report.get("execution_quality_by_session")
    if isinstance(by_session, dict) and isinstance(by_session.get(session), dict):
        return by_session[session]
    quality = symbol_report.get("execution_quality")
    return quality if isinstance(quality, dict) else {}


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
        if summary["target_exit_count"] < 2:
            return False, "insufficient_target_completions"
    return True, "bounded_cumulative_candidate_ready"


def _research_accumulation(
    spec: SymbolSpec,
    session: SessionSpec,
    rows: Sequence[dict[str, Any]],
    *,
    target_date: date | None = None,
) -> dict[str, Any]:
    if spec.symbol not in CUMULATIVE_RESEARCH_GATE_SYMBOLS:
        return {
            "status": "not_required",
            "start_date": spec.analysis_start_date.isoformat(),
            "minimum_qualified_observation_dates": 0,
            "qualified_observation_date_count": 0,
            "qualified_observation_dates": [],
            "excluded_observation_dates": {},
            "runtime_eligible": True,
        }
    rows_by_date: dict[date, list[dict[str, Any]]] = {}
    for row in rows:
        if (
            row["session"] == session.session
            and row["venue"] == session.venue
            and row["trade_date"] >= spec.analysis_start_date
            and is_krx_trading_day(row["trade_date"])
        ):
            rows_by_date.setdefault(row["trade_date"], []).append(row)
    qualified_dates: list[str] = []
    excluded_dates: dict[str, list[str]] = {}
    accumulation_end_date = target_date or max(
        rows_by_date, default=spec.analysis_start_date
    )
    expected_dates: list[date] = []
    candidate_date = spec.analysis_start_date
    while candidate_date <= accumulation_end_date:
        if is_krx_trading_day(candidate_date):
            expected_dates.append(candidate_date)
        candidate_date += timedelta(days=1)
    for source_date in expected_dates:
        day_rows = rows_by_date.get(source_date, [])
        pass_rows = [row for row in day_rows if row["source_quality_status"] == "PASS"]
        reasons: list[str] = []
        if not day_rows:
            reasons.append("no_valid_krx_regular_rows")
        if len(pass_rows) < 300:
            reasons.append("pass_row_count_below_300")
        if not pass_rows or min(row["observed_at"].time() for row in pass_rows) > time(
            9, 30
        ):
            reasons.append("opening_coverage_missing_after_0930")
        if not pass_rows or max(row["observed_at"].time() for row in pass_rows) < time(
            15, 20
        ):
            reasons.append("closing_coverage_missing_before_1520")
        if reasons:
            excluded_dates[source_date.isoformat()] = reasons
        else:
            qualified_dates.append(source_date.isoformat())
    minimum = spec.minimum_qualified_observation_dates
    ready = len(qualified_dates) >= minimum
    return {
        "status": "ready" if ready else "accumulating",
        "start_date": spec.analysis_start_date.isoformat(),
        "minimum_qualified_observation_dates": minimum,
        "qualified_observation_date_count": len(qualified_dates),
        "qualified_observation_dates": qualified_dates,
        "excluded_observation_dates": excluded_dates,
        "qualification_contract": CUMULATIVE_RESEARCH_QUALIFICATION_CONTRACT,
        "runtime_eligible": ready,
    }


def _calibrate_session(
    spec: SymbolSpec,
    session: SessionSpec,
    rows: Sequence[dict[str, Any]],
    *,
    target_date: date | None = None,
    previous_runtime_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    research_accumulation = _research_accumulation(
        spec,
        session,
        rows,
        target_date=target_date,
    )
    rows_by_date: dict[date, list[dict[str, Any]]] = {}
    for row in rows:
        if (
            row["session"] == session.session
            and row["venue"] == session.venue
            and row["source_quality_status"] == "PASS"
        ):
            rows_by_date.setdefault(row["trade_date"], []).append(row)
    ordered_dates = sorted(rows_by_date)
    holdout_count = _holdout_date_count(len(ordered_dates))
    holdout_dates = set(ordered_dates[-holdout_count:]) if holdout_count else set()
    calibration_dates = [value for value in ordered_dates if value not in holdout_dates]

    def simulate_dates(
        dates: Sequence[date],
        *,
        add_triggers: tuple[int, ...],
        target_bps: int,
        max_entries: int,
        cutoff: str,
        cooldown: int,
        force_exit_time: str | None,
    ) -> list[dict[str, Any]]:
        return [
            trade
            for source_date in dates
            for trade in _simulate_day(
                rows_by_date[source_date],
                session=session,
                add_triggers_bps=add_triggers,
                target_bps=target_bps,
                max_entries=max_entries,
                cutoff=cutoff,
                cooldown_minutes=cooldown,
                force_exit_time=force_exit_time,
                source_final_exit_action=SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL.get(
                    spec.symbol, "observe_only_no_forced_sell"
                ),
            )
        ]

    candidates: list[dict[str, Any]] = []
    for add_triggers in spec.add_trigger_arms:
        for target_bps in spec.target_bps_values:
            for cutoff in session.new_entry_cutoffs:
                for cooldown in (5, 10, 20):
                    force_exit_times: tuple[str | None, ...] = (
                        session.force_exit_times if session.force_flat else (None,)
                    )
                    for force_exit_time in force_exit_times:
                        all_cap_trades = simulate_dates(
                            calibration_dates,
                            add_triggers=add_triggers,
                            target_bps=target_bps,
                            max_entries=max(spec.max_entries_values),
                            cutoff=cutoff,
                            cooldown=cooldown,
                            force_exit_time=force_exit_time,
                        )
                        entry_cap_comparison = _entry_cap_comparison(all_cap_trades)
                        for max_entries in spec.max_entries_values:
                            cap_evidence = entry_cap_comparison[str(max_entries)]
                            summary = cap_evidence["cumulative"]
                            ready, reason = _candidate_ready(spec, session, summary)
                            incremental_ready, incremental_reason = (
                                _incremental_entry_cap_ready(
                                    entry_cap_comparison, max_entries
                                )
                            )
                            if ready and not incremental_ready:
                                ready, reason = False, incremental_reason
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
                                    "incremental_entry_cap_decision": (
                                        incremental_reason
                                    ),
                                    "entry_cap_comparison": entry_cap_comparison,
                                    "trades": [
                                        row
                                        for row in all_cap_trades
                                        if int(row["daily_entry_ordinal"])
                                        <= max_entries
                                    ],
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

    base_candidates = [
        candidate
        for candidate in candidates
        if int(candidate["max_completed_entries_per_day"]) < HIGH_ENTRY_CAP_START
    ]
    selected = max(base_candidates or candidates, key=rank) if candidates else None
    if selected is None:
        return {
            "decision": (
                "research_accumulation_incomplete"
                if research_accumulation["runtime_eligible"] is False
                else "no_candidate_rows"
            ),
            "selected_policy": None,
            "candidate_count": 0,
            "research_accumulation": research_accumulation,
        }
    family_keys = (
        "add_trigger_bps_from_initial_fill",
        "target_bps",
        "new_entry_cutoff_time",
        "reentry_cooldown_minutes",
        "force_exit_time",
    )
    for high_cap in range(HIGH_ENTRY_CAP_START, max(ENTRY_CAP_VALUES) + 1):
        high_candidate = next(
            (
                candidate
                for candidate in candidates
                if int(candidate["max_completed_entries_per_day"]) == high_cap
                and all(candidate[key] == selected[key] for key in family_keys)
            ),
            None,
        )
        if high_candidate is not None and high_candidate["ready"]:
            selected = high_candidate
    selected_parameters = {
        key: selected[key]
        for key in (
            "add_trigger_bps_from_initial_fill",
            "target_bps",
            "max_completed_entries_per_day",
            "new_entry_cutoff_time",
            "reentry_cooldown_minutes",
            "force_exit_time",
        )
    }
    all_holdout_trades = simulate_dates(
        sorted(holdout_dates),
        add_triggers=tuple(selected_parameters["add_trigger_bps_from_initial_fill"]),
        target_bps=int(selected_parameters["target_bps"]),
        max_entries=max(spec.max_entries_values),
        cutoff=str(selected_parameters["new_entry_cutoff_time"]),
        cooldown=int(selected_parameters["reentry_cooldown_minutes"]),
        force_exit_time=selected_parameters["force_exit_time"],
    )
    holdout_entry_cap_comparison = _entry_cap_comparison(all_holdout_trades)

    def holdout_status(cap: int) -> tuple[bool, str, dict[str, Any]]:
        summary = holdout_entry_cap_comparison[str(cap)]["cumulative"]
        ready = bool(summary["signal_trade_count"] >= 1)
        reason = "independent_holdout_pass"
        if not ready:
            reason = "independent_holdout_signal_missing"
        elif session.force_flat:
            ready = bool(
                summary["resolved_trade_count"] == summary["signal_trade_count"]
                and float(summary.get("source_quality_adjusted_ev_pct") or 0.0) > 0
                and float(summary.get("worst_net_return_pct") or -999.0) >= -2.0
            )
            if not ready:
                reason = "independent_holdout_ev_or_tail_failed"
        else:
            ready = bool(summary["target_exit_count"] >= 1)
            if not ready:
                reason = "independent_holdout_target_missing"
        incremental_ready, incremental_reason = _incremental_entry_cap_ready(
            holdout_entry_cap_comparison, cap
        )
        if ready and not incremental_ready:
            ready = False
            reason = (
                "independent_holdout_incremental_entry_cap_missing"
                if incremental_reason.endswith("_sample_missing")
                else "independent_holdout_incremental_entry_cap_ev_not_positive"
            )
        return ready, reason, summary

    selected_cap = int(selected_parameters["max_completed_entries_per_day"])
    holdout_ready, holdout_reason, holdout = holdout_status(selected_cap)
    holdout_trades = [
        row
        for row in all_holdout_trades
        if int(row["daily_entry_ordinal"]) <= selected_cap
    ]
    provisional_decision = (
        "widget_auto_trade_policy_candidate_ready"
        if selected["ready"] and holdout_ready
        else selected["reason"] if not selected["ready"] else holdout_reason
    )
    carry_forward_policy = _carry_forward_parameters(previous_runtime_policy)
    carry_forward_calibration_summary = None
    carry_forward_holdout_summary = None
    carry_forward_entry_cap_comparison = None
    carry_forward_holdout_entry_cap_comparison = None
    carry_forward_candidate_ready = False
    carry_forward_candidate_reason = "previous_verified_policy_unavailable"
    carry_forward_holdout_decision = "previous_verified_policy_unavailable"
    if carry_forward_policy is not None and not session.force_flat:
        carry_forward_cap = int(carry_forward_policy["max_completed_entries_per_day"])
        carry_forward_all_calibration_trades = simulate_dates(
            calibration_dates,
            add_triggers=tuple(
                carry_forward_policy["add_trigger_bps_from_initial_fill"]
            ),
            target_bps=int(carry_forward_policy["target_bps"]),
            max_entries=max(spec.max_entries_values),
            cutoff=str(carry_forward_policy["new_entry_cutoff_time"]),
            cooldown=int(carry_forward_policy["reentry_cooldown_minutes"]),
            force_exit_time=carry_forward_policy["force_exit_time"],
        )
        carry_forward_entry_cap_comparison = _entry_cap_comparison(
            carry_forward_all_calibration_trades
        )
        carry_forward_calibration_summary = carry_forward_entry_cap_comparison[
            str(carry_forward_cap)
        ]["cumulative"]
        (
            carry_forward_candidate_ready,
            carry_forward_candidate_reason,
        ) = _candidate_ready(spec, session, carry_forward_calibration_summary)
        carry_forward_incremental_ready, carry_forward_incremental_reason = (
            _incremental_entry_cap_ready(
                carry_forward_entry_cap_comparison, carry_forward_cap
            )
        )
        if carry_forward_candidate_ready and not carry_forward_incremental_ready:
            carry_forward_candidate_ready = False
            carry_forward_candidate_reason = carry_forward_incremental_reason
        carry_forward_all_holdout_trades = simulate_dates(
            sorted(holdout_dates),
            add_triggers=tuple(
                carry_forward_policy["add_trigger_bps_from_initial_fill"]
            ),
            target_bps=int(carry_forward_policy["target_bps"]),
            max_entries=max(spec.max_entries_values),
            cutoff=str(carry_forward_policy["new_entry_cutoff_time"]),
            cooldown=int(carry_forward_policy["reentry_cooldown_minutes"]),
            force_exit_time=carry_forward_policy["force_exit_time"],
        )
        carry_forward_holdout_entry_cap_comparison = _entry_cap_comparison(
            carry_forward_all_holdout_trades
        )
        carry_forward_holdout_summary = carry_forward_holdout_entry_cap_comparison[
            str(carry_forward_cap)
        ]["cumulative"]
        if carry_forward_holdout_summary["signal_trade_count"] < 1:
            carry_forward_holdout_decision = "independent_holdout_signal_missing"
        elif carry_forward_holdout_summary["target_exit_count"] < 1:
            carry_forward_holdout_decision = "independent_holdout_target_missing"
        else:
            carry_forward_holdout_decision = "independent_holdout_pass"
        (
            carry_forward_incremental_holdout_ready,
            carry_forward_incremental_holdout_reason,
        ) = _incremental_entry_cap_ready(
            carry_forward_holdout_entry_cap_comparison, carry_forward_cap
        )
        if not carry_forward_incremental_holdout_ready:
            carry_forward_holdout_decision = (
                "independent_holdout_incremental_entry_cap_missing"
                if carry_forward_incremental_holdout_reason.endswith("_sample_missing")
                else "independent_holdout_incremental_entry_cap_ev_not_positive"
            )
    carry_forward_previous = bool(
        not session.force_flat
        and provisional_decision != "widget_auto_trade_policy_candidate_ready"
        and carry_forward_candidate_ready
        and carry_forward_holdout_decision
        in {*INCONCLUSIVE_HOLDOUT_DECISIONS, "independent_holdout_pass"}
        and carry_forward_policy is not None
    )
    runtime_decision = (
        "carry_forward_previous_verified_policy"
        if carry_forward_previous
        else provisional_decision
    )
    return {
        "decision": (
            "research_accumulation_incomplete"
            if research_accumulation["runtime_eligible"] is False
            else runtime_decision
        ),
        "provisional_candidate_decision": provisional_decision,
        "runtime_selected_policy": (
            carry_forward_policy if carry_forward_previous else selected_parameters
        ),
        "carry_forward_previous_policy": carry_forward_previous,
        "carry_forward_candidate_ready": carry_forward_candidate_ready,
        "carry_forward_candidate_reason": carry_forward_candidate_reason,
        "carry_forward_calibration_summary": carry_forward_calibration_summary,
        "carry_forward_holdout_summary": carry_forward_holdout_summary,
        "carry_forward_entry_cap_comparison": carry_forward_entry_cap_comparison,
        "carry_forward_holdout_entry_cap_comparison": (
            carry_forward_holdout_entry_cap_comparison
        ),
        "carry_forward_holdout_decision": carry_forward_holdout_decision,
        "carry_forward_from_policy_id": (
            str(previous_runtime_policy.get("policy_id") or "")
            if carry_forward_previous and previous_runtime_policy is not None
            else None
        ),
        "candidate_count": len(candidates),
        "selected_policy": selected_parameters,
        "selected_summary": selected["summary"],
        "entry_cap_comparison": selected["entry_cap_comparison"],
        "incremental_entry_cap_decision": selected["incremental_entry_cap_decision"],
        "independent_holdout_summary": holdout,
        "independent_holdout_entry_cap_comparison": holdout_entry_cap_comparison,
        "independent_holdout_decision": holdout_reason,
        "calibration_dates": [value.isoformat() for value in calibration_dates],
        "holdout_dates": [value.isoformat() for value in sorted(holdout_dates)],
        "selected_trades": selected["trades"],
        "holdout_trades": holdout_trades,
        "policy_tier": "bounded_chronological_holdout",
        "rollback_condition": (
            (
                "next cumulative source-quality-adjusted net EV <= 0; "
                "unresolved forced-flat path; worst trade < -2%; "
                "source-quality/policy verification failure; or prior-day "
                "widget-owned inventory remains"
            )
            if session.force_flat
            else (
                "previous-policy cumulative target completions < 2; "
                "daily entry-cap 4/5 incremental EV <= 0; "
                "source-quality/policy verification failure; or terminal "
                "order/cancel failure"
            )
        ),
        "research_accumulation": research_accumulation,
    }


def _carry_forward_parameters(
    previous_runtime_policy: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if (
        not isinstance(previous_runtime_policy, dict)
        or previous_runtime_policy.get("new_entry_runtime_eligible") is not True
    ):
        return None
    try:
        add_triggers = [
            int(value)
            for value in previous_runtime_policy["add_trigger_bps_from_initial_fill"]
        ]
        target_bps = int(
            previous_runtime_policy["take_profit_bps_from_equal_share_average"]
        )
        max_entries = int(previous_runtime_policy["max_completed_entries_per_day"])
        cooldown = int(previous_runtime_policy["reentry_cooldown_minutes"])
        cutoff = str(previous_runtime_policy["new_entry_cutoff_time"])
    except (KeyError, TypeError, ValueError):
        return None
    if (
        not add_triggers
        and previous_runtime_policy.get("add_trigger_bps_from_initial_fill") is None
    ):
        return None
    if max_entries not in ENTRY_CAP_VALUES:
        return None
    return {
        "add_trigger_bps_from_initial_fill": add_triggers,
        "target_bps": target_bps,
        "max_completed_entries_per_day": max_entries,
        "new_entry_cutoff_time": cutoff,
        "reentry_cooldown_minutes": cooldown,
        "force_exit_time": previous_runtime_policy.get("force_exit_time"),
    }


def _load_previous_verified_session_policies(
    *, effective_date: date, policy_dir: Path
) -> dict[str, dict[str, dict[str, Any]]]:
    previous_effective_date = previous_krx_trading_date(effective_date)
    expected_path = policy_dir / (
        f"{POLICY_FILE_PREFIX}_{previous_effective_date.isoformat()}.json"
    )
    if not expected_path.exists():
        return {}
    loaded = WidgetAutoTradePolicyLoader(
        policy_dir, include_symbol_expansion=False
    ).resolve_all(observed_date=previous_effective_date)
    selected: dict[str, dict[str, dict[str, Any]]] = {}
    for symbol, sessions in loaded.items():
        for session, policy in sessions.items():
            if (
                isinstance(policy, dict)
                and policy.get("new_entry_runtime_eligible") is True
                and Path(str(policy.get("policy_path") or "")).resolve()
                == expected_path.resolve()
            ):
                selected.setdefault(symbol, {})[session] = policy
    return selected


def build_report(
    *,
    target_date: date,
    previous_session_policies: dict[str, dict[str, dict[str, Any]]] | None = None,
    machine_microstructure_report_dir: Path = MACHINE_MICROSTRUCTURE_REPORT_DIR,
) -> dict[str, Any]:
    if target_date < CLEAN_BASELINE_DATE:
        raise ValueError("target date precedes clean baseline")
    effective_date = _next_krx_trading_date(target_date)
    previous_session_policies = previous_session_policies or {}
    micro_feedback = load_prior_owner_diagnostic(
        target_date=target_date,
        owner="widget",
        report_dir=machine_microstructure_report_dir,
    )
    feedback_payload = micro_feedback.get("owner_payload") or {}
    feedback_symbols = (
        feedback_payload.get("symbols") if isinstance(feedback_payload, dict) else {}
    )
    if not isinstance(feedback_symbols, dict):
        feedback_symbols = {}
    symbol_reports: dict[str, Any] = {}
    source_paths: list[str] = []
    for spec in SPECS:
        rows, paths, source_load_audit = _load_rows(spec, target_date=target_date)
        source_paths.extend(paths)
        source_dates = sorted({row["trade_date"].isoformat() for row in rows})
        pass_row_count = sum(row["source_quality_status"] == "PASS" for row in rows)
        blocked_row_count = len(rows) - pass_row_count
        source_contract_gap_codes = sorted(
            key
            for key in (
                "invalid_json_or_object_count",
                "required_contract_missing_count",
                "invalid_observed_at_or_date_count",
                "invalid_price_or_bar_time_count",
                "invalid_optional_lifecycle_event_count",
            )
            if int(source_load_audit.get(key) or 0) > 0
        )
        source_contract_valid = not source_contract_gap_codes
        sessions = {
            session.session: _calibrate_session(
                spec,
                session,
                rows,
                target_date=target_date,
                previous_runtime_policy=previous_session_policies.get(
                    spec.symbol, {}
                ).get(session.session),
            )
            for session in spec.sessions
        }
        execution_quality = _load_execution_quality(
            spec.symbol, target_date=target_date
        )
        execution_quality_by_session = {
            session.session: _load_execution_quality(
                spec.symbol,
                target_date=target_date,
                session=session.session,
            )
            for session in spec.sessions
        }
        symbol_reports[spec.symbol] = {
            "name": spec.name,
            "source_row_count": len(rows),
            "source_quality_pass_row_count": pass_row_count,
            "source_quality_blocked_row_count": blocked_row_count,
            "source_quality_status": (
                "PASS" if pass_row_count and source_contract_valid else "BLOCKED"
            ),
            "source_contract_valid": source_contract_valid,
            "source_contract_gap_codes": source_contract_gap_codes,
            "source_load_audit": source_load_audit,
            "source_dates": source_dates,
            "actual_evidence_start_date": source_dates[0] if source_dates else None,
            "analysis_start_date": spec.analysis_start_date.isoformat(),
            "execution_quality": execution_quality,
            "execution_quality_by_session": execution_quality_by_session,
            "sessions": sessions,
            "microstructure_prior_trading_day_diagnostic": {
                "status": (
                    "loaded"
                    if spec.symbol in feedback_symbols
                    else (
                        "owner_symbol_not_present"
                        if micro_feedback["status"] == "loaded"
                        else micro_feedback["status"]
                    )
                ),
                "source_date": micro_feedback["source_date"],
                "selection_effect": False,
                "base_policy_unchanged": True,
                "payload": feedback_symbols.get(spec.symbol),
            },
        }
    statistically_ready_count = sum(
        session_report["decision"] == "widget_auto_trade_policy_candidate_ready"
        for symbol_report in symbol_reports.values()
        for session_report in symbol_report["sessions"].values()
    )
    carried_forward_count = sum(
        symbol_report["source_quality_status"] == "PASS"
        and _session_execution_quality(symbol_report, session_name).get(
            "runtime_apply_allowed"
        )
        is True
        and session_report["decision"] == "carry_forward_previous_verified_policy"
        for symbol_report in symbol_reports.values()
        for session_name, session_report in symbol_report["sessions"].items()
    )
    ready_count = sum(
        symbol_report["source_quality_status"] == "PASS"
        and _session_execution_quality(symbol_report, session_name).get(
            "runtime_apply_allowed"
        )
        is True
        and session_report["decision"] in RUNTIME_READY_DECISIONS
        for symbol_report in symbol_reports.values()
        for session_name, session_report in symbol_report["sessions"].items()
    )
    return {
        "schema": "widget_auto_trade_policy_calibration_report_v1",
        "status": "complete",
        "target_date": target_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "round_trip_cost_pct": comparison_cost_contract(target_date)[
            "round_trip_cost_pct"
        ],
        "comparison_cost_contract": comparison_cost_contract(target_date),
        "source_paths": sorted(set(source_paths)),
        "source_quality_status": (
            "PASS"
            if any(
                value["source_quality_status"] == "PASS"
                for value in symbol_reports.values()
            )
            else "BLOCKED"
        ),
        "statistically_ready_session_policy_count": statistically_ready_count,
        "carried_forward_session_policy_count": carried_forward_count,
        "ready_session_policy_count": ready_count,
        "symbols": symbol_reports,
        "machine_microstructure_prior_trading_day_diagnostic_source": {
            key: value
            for key, value in micro_feedback.items()
            if key != "owner_payload"
        },
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_policy(report: dict[str, Any]) -> dict[str, Any]:
    target_date = str(report["target_date"])
    effective_date = str(report["effective_date"])
    policy_symbols: dict[str, Any] = {}
    blocked_sessions: dict[str, dict[str, str]] = {}
    for spec in SPECS:
        source = report["symbols"][spec.symbol]
        session_specs = {value.session: value for value in spec.sessions}
        sessions: dict[str, Any] = {}
        for session_name, calibration in source["sessions"].items():
            execution_quality = _session_execution_quality(source, session_name)
            block_reason = None
            if source.get("source_quality_status") != "PASS":
                block_reason = "source_quality_blocked"
            elif not execution_quality.get("runtime_apply_allowed", False):
                block_reason = "execution_quality_safety_veto"
            elif calibration["decision"] not in RUNTIME_READY_DECISIONS:
                block_reason = str(calibration["decision"])
            if block_reason is not None:
                blocked_sessions.setdefault(spec.symbol, {})[
                    session_name
                ] = block_reason
                continue
            if calibration["decision"] not in RUNTIME_READY_DECISIONS:
                continue
            selected = (
                calibration.get("runtime_selected_policy")
                or calibration["selected_policy"]
            )
            session_spec = session_specs[session_name]
            research_accumulation = calibration["research_accumulation"]
            sessions[session_name] = {
                "enabled": True,
                "market_venue": session_spec.venue,
                "allowed_entry_states": sorted(ACTIONABLE_STATES),
                "leg_quantity_each": WIDGET_AUTO_TRADE_LEG_QUANTITY,
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
                "source_final_exit_action": SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL[
                    spec.symbol
                ],
                "research_arm": (
                    f"equal_share_{selected['add_trigger_bps_from_initial_fill']}_"
                    f"tp{selected['target_bps']}_multi"
                ),
                "evidence_window": (
                    f"{source['actual_evidence_start_date']}_{target_date}"
                ),
                "evidence_artifact": (
                    "data/report/widget_auto_trade_policy_calibration/"
                    f"widget_auto_trade_policy_calibration_{target_date}.json"
                ),
                "policy_tier": calibration["policy_tier"],
                "runtime_selection_decision": calibration["decision"],
                "carry_forward_from_policy_id": calibration.get(
                    "carry_forward_from_policy_id"
                ),
                "rollback_condition": calibration["rollback_condition"],
                "execution_quality": execution_quality,
                "actual_order_submitted": False,
                "broker_guard_bypass": False,
                "research_accumulation_start_date": research_accumulation["start_date"],
                "research_qualified_observation_date_count": (
                    research_accumulation["qualified_observation_date_count"]
                ),
                "research_minimum_qualified_observation_dates": (
                    research_accumulation["minimum_qualified_observation_dates"]
                ),
                "research_accumulation_gate_status": research_accumulation["status"],
            }
        if sessions:
            policy_symbols[spec.symbol] = {"name": spec.name, "sessions": sessions}
    policy = {
        "schema": POLICY_SCHEMA,
        "status": (
            "verified" if policy_symbols or blocked_sessions else "no_ready_policy"
        ),
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
        "blocked_sessions": blocked_sessions,
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
    loaded = WidgetAutoTradePolicyLoader(
        policy_dir, include_symbol_expansion=False
    ).resolve_all(observed_date=effective_date)
    expected_sessions = {
        (symbol, session)
        for symbol, symbol_payload in policy.get("symbols", {}).items()
        for session in symbol_payload.get("sessions", {})
    }
    expected_sessions.update(
        (symbol, session)
        for symbol, sessions in policy.get("blocked_sessions", {}).items()
        for session in sessions
    )
    loaded_sessions = {
        (symbol, session) for symbol, sessions in loaded.items() for session in sessions
    }
    issues: list[str] = []
    if loaded_sessions != expected_sessions:
        issues.append("dated_policy_loader_round_trip_mismatch")
    for symbol, symbol_payload in policy.get("symbols", {}).items():
        for session in symbol_payload.get("sessions", {}):
            loaded_policy = loaded.get(symbol, {}).get(session)
            if (
                not isinstance(loaded_policy, dict)
                or loaded_policy.get("new_entry_runtime_eligible") is not True
            ):
                issues.append(f"ready_session_not_runtime_eligible:{symbol}:{session}")
    for symbol, sessions in policy.get("blocked_sessions", {}).items():
        for session, reason in sessions.items():
            loaded_policy = loaded.get(symbol, {}).get(session)
            if not isinstance(loaded_policy, dict):
                issues.append(f"blocked_session_not_loaded:{symbol}:{session}")
                continue
            if loaded_policy.get("new_entry_runtime_eligible") is not False:
                issues.append(f"blocked_session_runtime_eligible:{symbol}:{session}")
            if loaded_policy.get("new_entry_runtime_block_reason") != str(reason):
                issues.append(f"blocked_session_reason_mismatch:{symbol}:{session}")
    return {
        "status": "pass" if not issues else "fail",
        "issues": sorted(set(issues)),
        "policy_path": str(verification_path),
        "loaded_session_count": len(loaded_sessions),
        "runtime_eligible_session_count": sum(
            policy_payload.get("new_entry_runtime_eligible") is True
            for sessions in loaded.values()
            for policy_payload in sessions.values()
        ),
        "runtime_blocked_session_count": sum(
            policy_payload.get("new_entry_runtime_eligible") is False
            for sessions in loaded.values()
            for policy_payload in sessions.values()
        ),
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
    expected_session_count += sum(
        len(sessions) for sessions in policy.get("blocked_sessions", {}).values()
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
    effective_date = _next_krx_trading_date(target_date)
    previous_session_policies = _load_previous_verified_session_policies(
        effective_date=effective_date,
        policy_dir=args.policy_dir,
    )
    report = build_report(
        target_date=target_date,
        previous_session_policies=previous_session_policies,
    )
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
