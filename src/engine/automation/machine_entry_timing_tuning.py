"""Select one bounded next-session machine entry-confirmation delay.

The producer consumes only clean-baseline machine microstructure attribution
rows.  It may select at most one exact owner scope across widget and episode
machines, and it writes an exact-date policy consumed by the existing owners.
It never submits, cancels, or exits an order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.trading.config.machine_entry_timing_policy import (
    ALLOWED_DELAYS_SEC,
    AUTHORITY,
    CLEAN_BASELINE_DATE,
    DEFAULT_POLICY_DIR,
    MAX_P10_DETERIORATION_PCT,
    MAX_RIGHT_CENSORED_RATE_PCT,
    MIN_ABSOLUTE_EV_UPLIFT_PCT,
    MIN_BBO_COMPLETE_RATE_PCT,
    MIN_COMPLETED_OUTCOMES,
    MIN_DELAYED_ENTRY_FEASIBILITY_RATE_PCT,
    MIN_DEPTH_COVERAGE_PCT,
    MIN_OBSERVED_DAYS,
    MIN_PAIRED_COMPLETED_COVERAGE_PCT,
    MIN_UNIQUE_LIFECYCLES,
    REQUIRED_ROLLING_WINDOWS_DAYS,
    SCHEMA as APPLIED_SCHEMA,
    canonical_sha256,
    policy_hash,
    policy_path,
    scope_key,
    validate_applied_policy,
)
from src.trading.order.tick_utils import get_tick_size, move_price_by_ticks
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
REPORT_SCHEMA = "machine_entry_timing_tuning_report_v1"
SOURCE_REPORT_SCHEMA = "machine_microstructure_attribution_v1"
SOURCE_DIR = DATA_DIR / "report" / "machine_microstructure_attribution"
OUTPUT_DIR = DATA_DIR / "report" / "machine_entry_timing_tuning"
SOURCE_PREFIX = "machine_microstructure_attribution"
LOW_PRICE_CANDIDATE_DIR = (
    DATA_DIR / "threshold_cycle" / "low_price_two_leg" / "candidates"
)
SAMSUNG_CANDIDATE_DIR = (
    DATA_DIR / "threshold_cycle" / "samsung_machine_entry_policy" / "candidates"
)
WIDGET_POLICY_DIR = DATA_DIR / "runtime" / "widget_auto_trade_policy"
ENTRY_ROLES = frozenset({"actual_widget_entry_signal", "episode_signal_decision_leg"})
ACTUAL_ENTRY_SOURCE_ROLES = frozenset({*ENTRY_ROLES, "episode_signal_bar"})
DELAYS_SEC = tuple(sorted(ALLOWED_DELAYS_SEC - {0}))
ROLLING_WINDOWS_DAYS = REQUIRED_ROLLING_WINDOWS_DAYS

METRIC_CONTRACT = {
    "metric_role": "bounded_widget_episode_entry_timing_policy_selection",
    "decision_authority": AUTHORITY,
    "window_policy": (
        "clean_baseline_exact_owner_scope_symbol_session_state_cumulative_and_"
        "complete_5d_10d_20d_observed_trading_date_windows"
    ),
    "sample_floor": {
        "observed_trading_days": MIN_OBSERVED_DAYS,
        "unique_decision_lifecycles": MIN_UNIQUE_LIFECYCLES,
        "completed_outcomes": MIN_COMPLETED_OUTCOMES,
        "bbo_complete_rate_pct": MIN_BBO_COMPLETE_RATE_PCT,
        "depth_coverage_pct": MIN_DEPTH_COVERAGE_PCT,
        "paired_completed_coverage_pct": MIN_PAIRED_COMPLETED_COVERAGE_PCT,
        "delayed_entry_feasibility_rate_pct": (MIN_DELAYED_ENTRY_FEASIBILITY_RATE_PCT),
        "maximum_right_censored_rate_pct": MAX_RIGHT_CENSORED_RATE_PCT,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "actual_decision_timestamp_exact_scope_realized_owner_outcome_"
        "executable_bbo_depth_and_eligible_0b_0d_ask_depletion"
    ),
    "forbidden_uses": [
        "same_day_entry_change",
        "more_than_one_same_stage_scope_mutation",
        "quantity_price_target_exit_or_stop_mutation",
        "missing_micro_data_as_zero_or_neutral",
        "cross_owner_scope_session_or_entry_state_pooling",
        "broker_guard_hard_safety_provider_bot_or_cap_change",
        "manual_operator_exit_as_machine_target_fill_success",
    ],
}


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _aware(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _next_trading_date(source_date: date) -> date:
    candidate = source_date + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _source_reports(
    *, target_date: date, source_dir: Path
) -> tuple[list[tuple[date, Path, dict[str, Any]]], list[dict[str, Any]]]:
    reports: list[tuple[date, Path, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob(f"{SOURCE_PREFIX}_*.json")):
        raw_date = path.stem.removeprefix(f"{SOURCE_PREFIX}_")
        try:
            source_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= source_date <= target_date:
            continue
        payload = _read_json(path)
        authority = (payload or {}).get("authority") or {}
        valid = bool(
            payload is not None
            and payload.get("schema") == SOURCE_REPORT_SCHEMA
            and payload.get("target_date") == source_date.isoformat()
            and payload.get("clean_tuning_baseline_date")
            == CLEAN_BASELINE_DATE.isoformat()
            and payload.get("clean_baseline_allowed") is True
            and isinstance(authority, dict)
            and authority.get("runtime_effect") is False
            and authority.get("actual_order_submitted") is False
            and authority.get("allowed_runtime_apply") is False
            and authority.get("broker_order_forbidden") is True
        )
        if not valid:
            rejected.append({"source_date": source_date.isoformat(), "path": str(path)})
            continue
        reports.append((source_date, path, payload))
    return reports, rejected


def _same_stage_owner_guard(
    *,
    target_date: date,
    low_price_candidate_dir: Path,
    samsung_candidate_dir: Path,
    widget_policy_dir: Path = WIDGET_POLICY_DIR,
) -> dict[str, Any]:
    paths = (
        low_price_candidate_dir
        / f"low_price_two_leg_policy_candidate_{target_date.isoformat()}.json",
        samsung_candidate_dir
        / f"samsung_machine_entry_policy_candidate_{target_date.isoformat()}.json",
    )
    owners: list[dict[str, Any]] = []
    for path in paths:
        payload = _read_json(path)
        mutations = (
            payload.get("policy_mutations") if isinstance(payload, dict) else None
        )
        if (
            isinstance(payload, dict)
            and payload.get("source_date") == target_date.isoformat()
            and isinstance(mutations, list)
            and mutations
        ):
            owners.append(
                {
                    "path": str(path),
                    "schema": payload.get("schema"),
                    "policy_mutation_count": len(mutations),
                }
            )
    current_widget_path = (
        widget_policy_dir / f"widget_auto_trade_policy_{target_date.isoformat()}.json"
    )
    effective_date = _next_trading_date(target_date)
    next_widget_path = (
        widget_policy_dir
        / f"widget_auto_trade_policy_{effective_date.isoformat()}.json"
    )
    current_widget = _read_json(current_widget_path)
    next_widget = _read_json(next_widget_path)
    entry_fields = (
        "enabled",
        "new_entry_runtime_eligible",
        "new_entry_runtime_block_reason",
        "allowed_entry_states",
        "allowed_entry_sessions",
        "allowed_entry_venues",
        "max_completed_entries_per_day",
        "reentry_cooldown_minutes",
        "new_entry_cutoff_time",
        "leg_quantity_each",
    )

    def widget_entry_contract(
        payload: Any, *, expected_date: date
    ) -> tuple[dict[str, Any], bool]:
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != "widget_auto_trade_policy_v1"
            or payload.get("effective_date") != expected_date.isoformat()
            or payload.get("runtime_effect") is not True
        ):
            return {}, False
        result: dict[str, Any] = {}
        for symbol, symbol_row in (payload.get("symbols") or {}).items():
            if not isinstance(symbol_row, dict):
                continue
            for session, session_row in (symbol_row.get("sessions") or {}).items():
                if not isinstance(session_row, dict):
                    continue
                key = f"{symbol}|{session}"
                result[key] = {field: session_row.get(field) for field in entry_fields}
        return result, True

    current_widget_entry, current_widget_valid = widget_entry_contract(
        current_widget, expected_date=target_date
    )
    next_widget_entry, next_widget_valid = widget_entry_contract(
        next_widget, expected_date=effective_date
    )
    if next_widget_path.exists() and not next_widget_valid:
        owners.append(
            {
                "path": str(next_widget_path),
                "schema": next_widget.get("schema") if next_widget else None,
                "policy_mutation_count": 0,
                "reason": "next_exact_date_widget_entry_contract_invalid",
            }
        )
    elif next_widget_valid and not current_widget_valid:
        owners.append(
            {
                "path": str(next_widget_path),
                "schema": next_widget.get("schema") if next_widget else None,
                "policy_mutation_count": len(next_widget_entry),
                "reason": "current_exact_date_widget_entry_baseline_unavailable",
            }
        )
    elif next_widget_valid and next_widget_entry != current_widget_entry:
        changed_scopes = sorted(
            key
            for key in set(current_widget_entry) | set(next_widget_entry)
            if current_widget_entry.get(key) != next_widget_entry.get(key)
        )
        owners.append(
            {
                "path": str(next_widget_path),
                "schema": next_widget.get("schema") if next_widget else None,
                "policy_mutation_count": len(changed_scopes),
                "changed_scopes": changed_scopes,
            }
        )
    return {
        "status": "blocked" if owners else "clear",
        "mutation_present": bool(owners),
        "owners": owners,
        "rule": "one_mutation_across_shared_regular_entry_stage",
    }


def _percentile_10(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * 0.10) - 1)
    return ordered[index]


def _ask_horizon_ready(row: dict[str, Any], delay_sec: int) -> bool:
    report = row.get("entry_ask_depletion")
    horizons = report.get("horizons") if isinstance(report, dict) else None
    if not isinstance(horizons, list):
        return False
    for item in horizons:
        if not isinstance(item, dict):
            continue
        try:
            horizon_ms = int(item.get("horizon_ms") or 0)
        except (TypeError, ValueError):
            continue
        if (
            horizon_ms == delay_sec * 1000
            and item.get("eligible_for_feature_ablation") is True
        ):
            return True
    return False


def _positive_target_tick_count(entry_price: float, target_price: float) -> int | None:
    """Return the exact positive KRX tick distance, or reject invalid prices."""

    if (
        not entry_price.is_integer()
        or not target_price.is_integer()
        or target_price <= entry_price
    ):
        return None
    entry = int(entry_price)
    target = int(target_price)
    moved = entry
    # Machine profiles use small target-tick counts. The bound makes malformed
    # source rows fail closed instead of turning report generation into a long loop.
    for ticks in range(1, 101):
        moved = move_price_by_ticks(moved, 1)
        if moved == target:
            return ticks
        if moved > target:
            return None
    return None


def _ceil_krx_price(raw_price: float) -> float | None:
    if not math.isfinite(raw_price) or raw_price <= 0:
        return None
    integer_price = math.ceil(raw_price)
    tick = get_tick_size(integer_price)
    return float(((integer_price + tick - 1) // tick) * tick)


def _candidate_observation(
    *, source_date: date, row: dict[str, Any], delay_sec: int
) -> dict[str, Any] | None:
    horizon = (row.get("entry_confirmation_bbo_horizons") or {}).get(str(delay_sec))
    outcome = row.get("owner_outcome")
    if not isinstance(horizon, dict) or not isinstance(outcome, dict):
        return None
    anchor_at = _aware(row.get("anchor_at"))
    exit_at = _aware(outcome.get("exit_at"))
    exit_price = _finite(outcome.get("exit_price"))
    delayed_ask = _finite(horizon.get("best_ask"))
    baseline_fill_price = _finite(row.get("anchor_price"))
    owner_entry_limit_price = _finite(row.get("owner_entry_limit_price"))
    owner_target_price = _finite(row.get("owner_target_price"))
    baseline_gross = _finite(outcome.get("gross_no_slippage_return_pct"))
    reported_net = _finite(outcome.get("cost_aware_net_return_pct"))
    exit_execution_class = str(outcome.get("exit_execution_class") or "")
    manual_operator_exit = bool(
        row.get("owner") == "episode"
        and exit_execution_class == "manual_operator_exit"
    )
    try:
        cost_contract = comparison_cost_contract(source_date)
    except ValueError:
        cost_contract = None
    cost_pct = _finite(
        cost_contract.get("round_trip_cost_pct")
        if isinstance(cost_contract, dict)
        else None
    )
    episode_target_ticks = (
        _positive_target_tick_count(baseline_fill_price, owner_target_price)
        if row.get("owner") == "episode"
        and baseline_fill_price is not None
        and owner_target_price is not None
        else None
    )
    if (
        row.get("classification") == "source_quality_blocked"
        or row.get("owner_policy_tuning_eligible") is not True
        or row.get("actual_order_submitted") is not True
        or not str(row.get("lifecycle_id") or "")
        or outcome.get("realized") is not True
        or horizon.get("observed") is not True
        or horizon.get("depth_backed") is not True
        or not _ask_horizon_ready(row, delay_sec)
        or anchor_at is None
        or exit_at is None
        or exit_at <= anchor_at + timedelta(seconds=delay_sec)
        or exit_price is None
        or exit_price <= 0
        or delayed_ask is None
        or delayed_ask <= 0
        or baseline_fill_price is None
        or baseline_fill_price <= 0
        or owner_target_price is None
        or owner_target_price <= baseline_fill_price
        or (
            row.get("owner") == "episode"
            and (
                owner_entry_limit_price is None
                or owner_entry_limit_price <= 0
                or delayed_ask > owner_entry_limit_price
                # A worse delayed fill requires a higher tick-derived target.
                # The realized original target receipt cannot prove that
                # counterfactual target would have filled.
                or delayed_ask > baseline_fill_price
                or not delayed_ask.is_integer()
                or episode_target_ticks is None
            )
        )
        or (
            delayed_ask > baseline_fill_price
            and row.get("owner") == "widget"
            and outcome.get("exit_reason") == "take_profit_fill"
        )
        or (row.get("owner") == "widget" and not delayed_ask.is_integer())
        or cost_pct is None
        or baseline_gross is None
        or (
            row.get("owner") == "episode"
            and exit_execution_class
            not in {"", "machine_target_fill", "manual_operator_exit"}
        )
        or (
            row.get("owner") == "widget"
            and int(outcome.get("scale_in_buy_leg_count") or 0) > 0
        )
    ):
        return None
    if (
        row.get("owner") == "widget"
        and outcome.get("exit_reason") == "take_profit_fill"
    ):
        candidate_exit_price = _ceil_krx_price(
            delayed_ask * (owner_target_price / baseline_fill_price)
        )
    elif manual_operator_exit:
        candidate_exit_price = exit_price
    elif row.get("owner") == "episode":
        candidate_exit_price = float(
            move_price_by_ticks(int(delayed_ask), episode_target_ticks)
        )
    else:
        candidate_exit_price = exit_price
    if candidate_exit_price is None:
        return None
    baseline_net = baseline_gross - cost_pct
    candidate_net = (candidate_exit_price / delayed_ask - 1.0) * 100.0 - cost_pct
    return {
        "source_date": source_date,
        "lifecycle_id": str(row.get("lifecycle_id") or ""),
        "baseline_net_pct": baseline_net,
        "candidate_net_pct": candidate_net,
        "reported_cost_aware_net_pct": reported_net,
        "baseline_realized_loss": bool(
            (reported_net if reported_net is not None else baseline_net) < 0.0
        ),
        "exit_execution_class": (
            exit_execution_class
            or ("machine_target_fill" if row.get("owner") == "episode" else "")
        ),
        "outcome_basis": (
            "manual_operator_exit_same_realized_exit_price"
            if manual_operator_exit
            else "machine_target_tick_preserving_exit"
            if row.get("owner") == "episode"
            else "widget_realized_exit_contract"
        ),
        "comparison_cost_contract_sha256": cost_contract.get("contract_sha256"),
    }


def _evaluate_cohort(
    *,
    cohort_rows: list[tuple[date, dict[str, Any]]],
    delay_sec: int,
    target_date: date,
) -> dict[str, Any]:
    observations = [
        observation
        for source_date, row in cohort_rows
        if (
            observation := _candidate_observation(
                source_date=source_date, row=row, delay_sec=delay_sec
            )
        )
        is not None
    ]
    observed_dates = sorted({item["source_date"] for item in observations})
    target_date_in_completed_observations = target_date in observed_dates
    lifecycles = {item["lifecycle_id"] for item in observations if item["lifecycle_id"]}
    eligible_owner_rows = [
        row
        for _, row in cohort_rows
        if (
            row.get("owner_policy_tuning_eligible") is True
            or row.get("owner_timing_custody_observation_eligible") is True
        )
        and row.get("classification") != "source_quality_blocked"
        and row.get("actual_order_submitted") is True
    ]
    bbo_observed = sum(
        (
            (row.get("entry_confirmation_bbo_horizons") or {}).get(str(delay_sec)) or {}
        ).get("observed")
        is True
        for row in eligible_owner_rows
    )
    depth_observed = sum(
        (
            (row.get("entry_confirmation_bbo_horizons") or {}).get(str(delay_sec)) or {}
        ).get("depth_backed")
        is True
        and _ask_horizon_ready(row, delay_sec)
        for row in eligible_owner_rows
    )
    denominator = len(eligible_owner_rows)
    realized_eligible_count = sum(
        isinstance((outcome := row.get("owner_outcome")), dict)
        and outcome.get("realized") is True
        for row in eligible_owner_rows
    )
    right_censored_count = denominator - realized_eligible_count
    paired_completed_coverage_rate = (
        len(observations) / realized_eligible_count * 100.0
        if realized_eligible_count
        else 0.0
    )
    right_censored_rate = (
        right_censored_count / denominator * 100.0 if denominator else 100.0
    )
    bbo_rate = bbo_observed / denominator * 100.0 if denominator else 0.0
    depth_rate = depth_observed / denominator * 100.0 if denominator else 0.0
    feasibility_rate = (
        len(observations) / realized_eligible_count * 100.0
        if realized_eligible_count
        else 0.0
    )
    baseline_values = [item["baseline_net_pct"] for item in observations]
    candidate_values = [item["candidate_net_pct"] for item in observations]
    manual_exit_observations = [
        item
        for item in observations
        if item.get("exit_execution_class") == "manual_operator_exit"
    ]
    baseline_ev = statistics.fmean(baseline_values) if baseline_values else None
    candidate_ev = statistics.fmean(candidate_values) if candidate_values else None
    rolling: dict[str, Any] = {}
    rolling_ready = True
    for window_days in ROLLING_WINDOWS_DAYS:
        window_dates = observed_dates[-window_days:]
        window_rows = [
            item for item in observations if item["source_date"] in set(window_dates)
        ]
        baseline_window = [item["baseline_net_pct"] for item in window_rows]
        candidate_window = [item["candidate_net_pct"] for item in window_rows]
        complete = len(window_dates) >= window_days
        base_ev = statistics.fmean(baseline_window) if baseline_window else None
        cand_ev = statistics.fmean(candidate_window) if candidate_window else None
        improved = bool(
            complete
            and cand_ev is not None
            and base_ev is not None
            and cand_ev > 0
            and cand_ev > base_ev
        )
        rolling[str(window_days)] = {
            "complete": complete,
            "observed_trading_days": len(window_dates),
            "sample_count": len(window_rows),
            "baseline_source_quality_adjusted_ev_pct": base_ev,
            "candidate_source_quality_adjusted_ev_pct": cand_ev,
            "positive_and_improved": improved,
        }
        rolling_ready = rolling_ready and improved
    absolute_uplift = (
        candidate_ev - baseline_ev
        if candidate_ev is not None and baseline_ev is not None
        else None
    )
    baseline_p10 = _percentile_10(baseline_values)
    candidate_p10 = _percentile_10(candidate_values)
    ready = bool(
        len(observed_dates) >= MIN_OBSERVED_DAYS
        and len(lifecycles) >= MIN_UNIQUE_LIFECYCLES
        and len(observations) >= MIN_COMPLETED_OUTCOMES
        and bbo_rate >= MIN_BBO_COMPLETE_RATE_PCT
        and depth_rate >= MIN_DEPTH_COVERAGE_PCT
        and paired_completed_coverage_rate >= MIN_PAIRED_COMPLETED_COVERAGE_PCT
        and feasibility_rate >= MIN_DELAYED_ENTRY_FEASIBILITY_RATE_PCT
        and right_censored_rate <= MAX_RIGHT_CENSORED_RATE_PCT
        and target_date_in_completed_observations
        and candidate_ev is not None
        and candidate_ev > 0
        and absolute_uplift is not None
        and absolute_uplift >= MIN_ABSOLUTE_EV_UPLIFT_PCT
        and baseline_p10 is not None
        and candidate_p10 is not None
        and candidate_p10 >= baseline_p10 - MAX_P10_DETERIORATION_PCT
        and rolling_ready
    )
    return {
        "entry_confirmation_delay_sec": delay_sec,
        "observed_trading_days": len(observed_dates),
        "latest_completed_observation_date": (
            observed_dates[-1].isoformat() if observed_dates else None
        ),
        "target_date_in_completed_observations": (
            target_date_in_completed_observations
        ),
        "unique_decision_lifecycles": len(lifecycles),
        "completed_outcome_count": len(observations),
        "machine_target_fill_outcome_count": sum(
            item.get("exit_execution_class") == "machine_target_fill"
            for item in observations
        ),
        "manual_operator_exit_outcome_count": len(manual_exit_observations),
        "manual_operator_exit_loss_outcome_count": sum(
            item.get("baseline_realized_loss") is True
            for item in manual_exit_observations
        ),
        "source_quality_eligible_anchor_count": denominator,
        "right_censored_or_unresolved_count": right_censored_count,
        "right_censored_rate_pct": round(right_censored_rate, 8),
        "bbo_complete_rate_pct": round(bbo_rate, 8),
        "depth_coverage_pct": round(depth_rate, 8),
        "paired_completed_coverage_rate_pct": round(paired_completed_coverage_rate, 8),
        "delayed_entry_feasibility_rate_pct": round(feasibility_rate, 8),
        "baseline_source_quality_adjusted_ev_pct": (
            round(baseline_ev, 8) if baseline_ev is not None else None
        ),
        "source_quality_adjusted_ev_pct": (
            round(candidate_ev, 8) if candidate_ev is not None else None
        ),
        "absolute_ev_uplift_pct": (
            round(absolute_uplift, 8) if absolute_uplift is not None else None
        ),
        "baseline_p10_pct": baseline_p10,
        "candidate_p10_pct": candidate_p10,
        "rolling_windows": rolling,
        "ready": ready,
    }


def _cohort_sample_floor_assessment(
    *,
    cohort_key: tuple[str, str, str, str, str],
    cohort_rows: list[tuple[date, dict[str, Any]]],
    alternatives: list[dict[str, Any]],
    source_report_dates: set[date],
) -> dict[str, Any]:
    """Separate source/terminal defects from normal exact-scope accumulation."""

    first_seen_date = min(source_date for source_date, _ in cohort_rows)
    eligible_source_dates = {
        source_date
        for source_date in source_report_dates
        if source_date >= first_seen_date
    }
    blocked_count = sum(
        row.get("classification") == "source_quality_blocked" for _, row in cohort_rows
    )
    policy_eligible_count = sum(
        (
            row.get("owner_policy_tuning_eligible") is True
            or row.get("owner_timing_custody_observation_eligible") is True
        )
        and row.get("classification") != "source_quality_blocked"
        and row.get("actual_order_submitted") is True
        for _, row in cohort_rows
    )
    completed_count = max(
        (int(row.get("completed_outcome_count") or 0) for row in alternatives),
        default=0,
    )
    observed_days = max(
        (int(row.get("observed_trading_days") or 0) for row in alternatives),
        default=0,
    )
    remaining = max(MIN_COMPLETED_OUTCOMES - completed_count, 0)
    completed_per_source_day = (
        completed_count / len(eligible_source_dates) if eligible_source_dates else 0.0
    )
    if completed_count >= MIN_COMPLETED_OUTCOMES:
        state = "sample_floor_met"
        projected_days = 0
    elif policy_eligible_count == 0 and blocked_count > 0:
        state = "source_quality_blocked"
        projected_days = None
    elif policy_eligible_count == 0:
        state = "eligibility_contract_gap"
        projected_days = None
    elif completed_count == 0:
        state = "outcome_or_executable_gap"
        projected_days = None
    else:
        state = "natural_sample_wait"
        projected_days = math.ceil(remaining / completed_per_source_day)
    if state == "sample_floor_met":
        shortage_classification_status = "not_applicable_floor_met"
        shortage_class = None
        why_waiting_cannot_resolve = None
    elif state == "natural_sample_wait":
        shortage_classification_status = "classified"
        shortage_class = "time_resolvable_shortage"
        why_waiting_cannot_resolve = None
    elif state in {"source_quality_blocked", "eligibility_contract_gap"}:
        shortage_classification_status = "classified"
        shortage_class = "structural_population_exhaustion"
        why_waiting_cannot_resolve = (
            "source_or_eligibility_defect_prevents_new_valid_unique_rows"
        )
    else:
        shortage_classification_status = "blocked_missing_evidence"
        shortage_class = None
        why_waiting_cannot_resolve = (
            "terminal_maturity_or_executable_pair_arrival_rate_not_proven"
        )
    return {
        "shortage_id": "machine_entry_timing:" + ":".join(cohort_key),
        "state": state,
        "shortage_classification_status": shortage_classification_status,
        "shortage_class": shortage_class,
        "why_waiting_cannot_resolve": why_waiting_cannot_resolve,
        "candidate_input_anchor_count": len(cohort_rows),
        "source_report_day_count_since_scope_first_seen": len(eligible_source_dates),
        "source_quality_blocked_anchor_count": blocked_count,
        "source_quality_eligible_anchor_count": policy_eligible_count,
        "completed_outcome_count": completed_count,
        "observed_trading_days": observed_days,
        "completed_outcome_floor": MIN_COMPLETED_OUTCOMES,
        "remaining_completed_outcome_count": remaining,
        "completed_outcomes_per_source_day": round(completed_per_source_day, 8),
        "projected_additional_trading_days_at_observed_yield": projected_days,
        "projection_authority": "diagnostic_only_no_runtime_or_floor_change",
    }


def _report_sample_floor_assessment(
    *,
    target_date: date,
    reports: list[tuple[date, Path, dict[str, Any]]],
    target_source_ready: bool,
    cohorts: list[dict[str, Any]],
    winner: dict[str, Any] | None,
) -> dict[str, Any]:
    """Classify why a missing winner cannot be resolved by blind waiting."""

    target_actual_rows: list[dict[str, Any]] = []
    for source_date, _, payload in reports:
        if source_date != target_date:
            continue
        confirmation = payload.get("micro_entry_confirmation") or {}
        for row in confirmation.get("entry_anchors") or []:
            if (
                isinstance(row, dict)
                and row.get("owner") in {"widget", "episode"}
                and row.get("anchor_role") in ACTUAL_ENTRY_SOURCE_ROLES
            ):
                target_actual_rows.append(row)
    target_blocked_rows = [
        row
        for row in target_actual_rows
        if row.get("classification") == "source_quality_blocked"
    ]
    gap_reasons: set[str] = set()
    for row in target_blocked_rows:
        raw_reasons = row.get("source_gap_reasons")
        reasons = raw_reasons if isinstance(raw_reasons, list) else [raw_reasons]
        gap_reasons.update(
            str(reason)
            for reason in reasons
            if reason is not None and str(reason).strip()
        )
    cohort_states = [
        str((cohort.get("sample_floor_assessment") or {}).get("state") or "")
        for cohort in cohorts
    ]
    if winner is not None:
        state = "candidate_ready"
        blocker_class = None
        next_action = "preserve_exact_scope_review_and_apply_contract"
    elif not target_source_ready:
        state = "source_contract_blocked"
        blocker_class = "source_quality"
        next_action = "repair_or_generate_exact_target_source_artifact"
    elif target_actual_rows and len(target_blocked_rows) == len(target_actual_rows):
        state = (
            "instrumentation_or_join_gap"
            if "actual_signal_decision_timestamp_missing" in gap_reasons
            else "source_quality_blocked"
        )
        blocker_class = "source_quality"
        next_action = "repair_exact_entry_anchor_market_join_and_rerun"
    elif "source_quality_blocked" in cohort_states:
        state = "source_quality_blocked"
        blocker_class = "source_quality"
        next_action = "repair_blocked_exact_scope_source_and_rerun"
    elif "eligibility_contract_gap" in cohort_states:
        state = "eligibility_contract_gap"
        blocker_class = "source_quality"
        next_action = "repair_exact_scope_eligibility_lineage_before_waiting"
    elif "outcome_or_executable_gap" in cohort_states:
        state = "terminal_or_right_censored_gap"
        blocker_class = "terminal_outcome"
        next_action = "reconcile_terminal_or_executable_pair_before_waiting"
    elif not target_actual_rows:
        state = "no_natural_sample"
        blocker_class = "sample_floor"
        next_action = "continue_exact_date_collection_without_imputation"
    else:
        state = "natural_sample_wait"
        blocker_class = "sample_floor"
        next_action = "continue_exact_scope_collection_and_recheck_projection"
    if state == "candidate_ready":
        shortage_classification_status = "not_applicable_candidate_ready"
        shortage_class = None
        why_waiting_cannot_resolve = None
    elif state == "natural_sample_wait":
        shortage_classification_status = "classified"
        shortage_class = "time_resolvable_shortage"
        why_waiting_cannot_resolve = None
    elif state in {
        "instrumentation_or_join_gap",
        "source_quality_blocked",
        "eligibility_contract_gap",
    }:
        shortage_classification_status = "classified"
        shortage_class = "structural_population_exhaustion"
        why_waiting_cannot_resolve = (
            "waiting_does_not_repair_the_first_depleted_source_or_join_stage"
        )
    else:
        shortage_classification_status = "blocked_missing_evidence"
        shortage_class = None
        why_waiting_cannot_resolve = (
            "positive_arrival_rate_and_finite_resolution_horizon_not_proven"
        )
    return {
        "shortage_id": "machine_entry_timing:all_exact_scopes:entry_confirmation_delay",
        "state": state,
        "shortage_classification_status": shortage_classification_status,
        "shortage_class": shortage_class,
        "why_waiting_cannot_resolve": why_waiting_cannot_resolve,
        "blocker_class": blocker_class,
        "target_actual_entry_anchor_count": len(target_actual_rows),
        "target_source_quality_blocked_anchor_count": len(target_blocked_rows),
        "target_source_gap_reasons": sorted(gap_reasons),
        "cohort_state_counts": {
            value: cohort_states.count(value) for value in sorted(set(cohort_states))
        },
        "next_action": next_action,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def build_report(
    *,
    target_date: date,
    source_dir: Path = SOURCE_DIR,
    low_price_candidate_dir: Path = LOW_PRICE_CANDIDATE_DIR,
    samsung_candidate_dir: Path = SAMSUNG_CANDIDATE_DIR,
    widget_policy_dir: Path = WIDGET_POLICY_DIR,
) -> dict[str, Any]:
    reports, rejected = _source_reports(target_date=target_date, source_dir=source_dir)
    source_report_dates = {source_date for source_date, _, _ in reports}
    target_source_ready = any(
        source_date == target_date for source_date, _, _ in reports
    )
    grouped: dict[tuple[str, str, str, str, str], list[tuple[date, dict[str, Any]]]] = (
        defaultdict(list)
    )
    source_artifacts: list[dict[str, Any]] = []
    for source_date, path, payload in reports:
        raw = path.read_bytes()
        source_artifacts.append(
            {
                "source_date": source_date.isoformat(),
                "path": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        confirmation = payload.get("micro_entry_confirmation") or {}
        for row in confirmation.get("entry_anchors") or []:
            if (
                not isinstance(row, dict)
                or row.get("anchor_role") not in ENTRY_ROLES
                or row.get("owner") not in {"widget", "episode"}
                or not row.get("entry_timing_scope_id")
            ):
                continue
            key = (
                str(row["owner"]),
                str(row["entry_timing_scope_id"]),
                str(row.get("symbol") or ""),
                str(row.get("session") or ""),
                str(row.get("entry_state") or "*"),
            )
            grouped[key].append((source_date, row))
    cohorts: list[dict[str, Any]] = []
    ready: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        owner, scope_id, symbol, session, entry_state = key
        alternatives = [
            _evaluate_cohort(
                cohort_rows=rows,
                delay_sec=delay,
                target_date=target_date,
            )
            for delay in DELAYS_SEC
        ]
        ready_alternatives = [item for item in alternatives if item["ready"]]
        selected = max(
            ready_alternatives,
            key=lambda item: (
                float(item["source_quality_adjusted_ev_pct"]),
                -int(item["entry_confirmation_delay_sec"]),
            ),
            default=None,
        )
        cohort = {
            "owner": owner,
            "scope_id": scope_id,
            "symbol": symbol,
            "session": session,
            "entry_state": entry_state,
            "alternatives": alternatives,
            "selected": selected,
            "sample_floor_assessment": _cohort_sample_floor_assessment(
                cohort_key=key,
                cohort_rows=rows,
                alternatives=alternatives,
                source_report_dates=source_report_dates,
            ),
        }
        cohorts.append(cohort)
        if selected is not None:
            ready.append(cohort)
    same_stage_owner_guard = _same_stage_owner_guard(
        target_date=target_date,
        low_price_candidate_dir=low_price_candidate_dir,
        samsung_candidate_dir=samsung_candidate_dir,
        widget_policy_dir=widget_policy_dir,
    )
    winner = (
        None
        if same_stage_owner_guard["mutation_present"] or not target_source_ready
        else max(
            ready,
            key=lambda item: (
                float(item["selected"]["absolute_ev_uplift_pct"]),
                item["owner"],
                item["scope_id"],
            ),
            default=None,
        )
    )
    sample_floor_assessment = _report_sample_floor_assessment(
        target_date=target_date,
        reports=reports,
        target_source_ready=target_source_ready,
        cohorts=cohorts,
        winner=winner,
    )
    status = (
        "candidate_ready"
        if winner
        else (
            "source_quality_blocked"
            if sample_floor_assessment["blocker_class"] == "source_quality"
            else "evidence_accumulating"
        )
    )
    return {
        "schema": REPORT_SCHEMA,
        "status": status,
        "decision": (
            "select_one_next_session_entry_confirmation_delay"
            if winner
            else "baseline_immediate_entry_carry_forward"
        ),
        "target_date": target_date.isoformat(),
        "effective_date": _next_trading_date(target_date).isoformat(),
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "source_artifacts": source_artifacts,
        "rejected_source_artifacts": rejected,
        "target_source_ready": target_source_ready,
        "cohorts": cohorts,
        "winner": winner,
        "same_stage_owner_guard": same_stage_owner_guard,
        "sample_floor_assessment": sample_floor_assessment,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_applied_policy(
    report: dict[str, Any], *, source_report_path: Path | str | None = None
) -> dict[str, Any]:
    scopes: dict[str, Any] = {}
    winner = report.get("winner")
    if isinstance(winner, dict) and isinstance(winner.get("selected"), dict):
        selected = winner["selected"]
        key = scope_key(
            owner=winner["owner"],
            scope_id=winner["scope_id"],
            symbol=winner["symbol"],
            session=winner["session"],
            entry_state=winner["entry_state"],
        )
        scopes[key] = {
            "owner": winner["owner"],
            "scope_id": winner["scope_id"],
            "symbol": winner["symbol"],
            "session": winner["session"],
            "entry_state": winner["entry_state"],
            "axis": "entry_confirmation_delay_sec",
            "entry_confirmation_delay_sec": selected["entry_confirmation_delay_sec"],
            "evidence": selected,
            "quantity_effect": False,
            "price_effect": False,
            "target_effect": False,
            "exit_effect": False,
            "rollback": "next_exact_date_baseline_immediate_on_any_floor_failure",
        }
    resolved_source_report = source_report_path or (
        f"data/report/machine_entry_timing_tuning/"
        f"machine_entry_timing_tuning_{report['target_date']}.json"
    )
    payload = {
        "schema": APPLIED_SCHEMA,
        "target_date": report["effective_date"],
        "source_date": report["target_date"],
        "applied_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "decision_authority": AUTHORITY,
        "selection_status": report["decision"],
        "source_report": str(resolved_source_report),
        "source_report_canonical_sha256": canonical_sha256(report),
        "scopes": scopes,
        "policy_hash": policy_hash(scopes),
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "forbidden_changes": METRIC_CONTRACT["forbidden_uses"],
    }
    valid, reason = validate_applied_policy(
        payload, target_date=date.fromisoformat(payload["target_date"])
    )
    if not valid:
        raise ValueError(reason)
    return payload


def render_markdown(report: dict[str, Any], applied: dict[str, Any]) -> str:
    winner = report.get("winner")
    lines = [
        "# Machine Entry Timing Tuning",
        "",
        f"- Source date: `{report['target_date']}`",
        f"- Effective date: `{report['effective_date']}`",
        f"- Decision: `{report['decision']}`",
        "- Axis: entry confirmation delay only (`0/1/3/5s`).",
        "- Quantity, order price, target, stop, holding, and exit are unchanged.",
        "",
    ]
    if isinstance(winner, dict):
        selected = winner["selected"]
        lines.append(
            "- Selected: "
            f"`{winner['owner']}:{winner['scope_id']}:{winner['entry_state']}` "
            f"delay `{selected['entry_confirmation_delay_sec']}s`, EV "
            f"`{selected['source_quality_adjusted_ev_pct']}`."
        )
    else:
        lines.append(
            "- No scope passed all cumulative and 5/10/20-day floors; delay remains `0s`."
        )
    sample_assessment = report.get("sample_floor_assessment") or {}
    lines.append(
        "- Sample-floor state: "
        f"`{sample_assessment.get('state')}`; next action "
        f"`{sample_assessment.get('next_action')}`."
    )
    lines.extend(
        [
            f"- Applied scope count: `{len(applied['scopes'])}`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    report: dict[str, Any],
    applied: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    policy_dir: Path = DEFAULT_POLICY_DIR,
) -> tuple[Path, Path, Path]:
    report_path = (
        output_dir / f"machine_entry_timing_tuning_{report['target_date']}.json"
    )
    markdown_path = report_path.with_suffix(".md")
    applied_path = policy_path(
        date.fromisoformat(applied["target_date"]), policy_dir=policy_dir
    )
    _atomic_write_json(report_path, report)
    _atomic_write_text(markdown_path, render_markdown(report, applied))
    _atomic_write_json(applied_path, applied)
    return report_path, markdown_path, applied_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    target_date = date.fromisoformat(args.target_date)
    report = build_report(target_date=target_date)
    applied = build_applied_policy(report)
    paths: tuple[Path, Path, Path] | None = None
    if args.write:
        paths = write_outputs(report, applied)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "decision": report["decision"],
                    "winner": report.get("winner"),
                    "paths": [str(path) for path in paths] if paths else [],
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
