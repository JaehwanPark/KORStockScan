"""Postclose entry-quality ledger for independent Samsung machine episodes.

This producer deliberately reads only the target-date durable machine states and
previous reports written by this module.  It never queries market history and it
has no runtime, order, or threshold mutation authority.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.order.episode_quantity import SUPPORTED_OWNED_LEG_QUANTITIES
from src.trading.order.samsung_entry_policy import (
    APPLIED_DIR,
    BASELINE_POLICIES,
    CANDIDATE_DIR,
    CANDIDATE_SCHEMA,
    OPERATOR_OVERRIDE_RUNTIME_SOURCE,
    atomic_write_json,
    candidate_artifact_hash,
    canonical_hash,
    file_sha256,
    load_applied_machine_policy,
    policy_hash,
    policy_mutations_between,
    validate_candidate,
    report_artifact_hash,
)
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
REPORT_TYPE = "samsung_machine_entry_tuning"
REPORT_SCHEMA = "samsung_machine_entry_tuning_report_v9"
HASHED_REPORT_SCHEMAS = frozenset(
    {"samsung_machine_entry_tuning_report_v8", REPORT_SCHEMA}
)
SUPPORTED_REPORT_SCHEMAS = frozenset(
    {
        "samsung_machine_entry_tuning_report_v2",
        "samsung_machine_entry_tuning_report_v3",
        "samsung_machine_entry_tuning_report_v4",
        "samsung_machine_entry_tuning_report_v5",
        "samsung_machine_entry_tuning_report_v6",
        "samsung_machine_entry_tuning_report_v7",
        "samsung_machine_entry_tuning_report_v8",
        REPORT_SCHEMA,
    }
)
CLEAN_BASELINE_DATE = date.fromisoformat("2026-06-05")
CLEAN_WINDOW_NAME = "clean_baseline_cumulative"
ROLLING_WINDOWS = {"rolling_10d": 10, "rolling_20d": 20}
POST_APPLY_WINDOW_NAME = "post_apply_version"
BOUNDED_MIN_OBSERVED_DAYS = 5
SAMPLE_FLOOR = 8
AUTO_MIN_COMPLETED_LEGS = 8
ROLLING_10D_MIN_COMPLETED_EPISODES = 4
MIN_NOTIONAL_EV_UPLIFT_PCT = 0.005
LOW_SIGNAL_RATE_THRESHOLD = 0.20
RATE_ASSESSMENT_MIN_OBSERVATION_DAYS = 5
MANUAL_EXIT_FILL_SOURCE = "broker_verified_manual_sell_receipt"
MANUAL_EXIT_PRICE_SOURCE = "broker_manual_sell_receipt"
APPLIED_POLICY_PROVENANCE_REQUIRED_DATE = date(2026, 8, 14)
SOURCE_QUALITY_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
MANUAL_EXIT_RECEIPT_REGISTRY_PATH = (
    DATA_DIR / "runtime" / "episode_manual_exit_receipts.json"
)
MANUAL_CLOSE_RECONCILIATION_DIR = DATA_DIR / "runtime" / "manual_close_reconciliation"
OUTCOME_AMENDMENT_SCHEMA = "samsung_machine_outcome_amendment_v1"
MACHINE_FILES = {
    "morning": "samsung_morning_one_share_state.json",
    "morning_reentry": "samsung_morning_sor_reentry_state.json",
    "midday": "samsung_midday_one_share_state.json",
    "afternoon": "samsung_afternoon_one_share_state.json",
}
EXPECTED_SCHEMAS = {
    "morning": "samsung_morning_two_leg_state_v2",
    "morning_reentry": "samsung_morning_sor_reentry_two_leg_state_v1",
    "midday": "samsung_midday_two_leg_state_v2",
    "afternoon": "samsung_afternoon_two_leg_state_v2",
}
LEGACY_SCHEMAS = {
    "morning": "samsung_morning_one_share_state_v1",
    "midday": "samsung_midday_one_share_state_v1",
    "afternoon": "samsung_afternoon_one_share_state_v1",
}
MACHINE_EFFECTIVE_DATES = {
    "morning_reentry": date(2026, 8, 13),
}
TERMINAL_LEG_STATUSES = {"COMPLETE", "NO_FILL"}
KNOWN_LEG_STATUSES = {
    "PLANNED",
    "BUY_SUBMITTING",
    "BUY_OPEN",
    "BUY_CANCEL_SUBMITTING",
    "BUY_CANCEL_PENDING",
    "POSITION_OPEN",
    "TARGET_SUBMITTING",
    "TARGET_OPEN",
    "NO_FILL",
    "COMPLETE",
    "HELD",
}

METRIC_CONTRACT = {
    "metric_role": "samsung_machine_entry_tuning_observation",
    "decision_authority": "report_only_independent_machine_entry_tuning",
    "window_policy": (
        "daily_clean_baseline_cumulative_and_rolling_10d_20d_actual_observations"
    ),
    "sample_floor": {
        "candidate_observed_trading_days": BOUNDED_MIN_OBSERVED_DAYS,
        "clean_baseline_cumulative_completed_signal_episodes": SAMPLE_FLOOR,
        "clean_baseline_cumulative_completed_legs": AUTO_MIN_COMPLETED_LEGS,
        "broker_priced_completed_legs": AUTO_MIN_COMPLETED_LEGS,
        "post_apply_rollback_completed_signal_episodes": ROLLING_10D_MIN_COMPLETED_EPISODES,
        "minimum_notional_ev_uplift_pct": MIN_NOTIONAL_EV_UPLIFT_PCT,
    },
    "primary_decision_metric": [
        "notional_weighted_ev_pct",
        "broker_realized_net_profit_krw",
        "expected_net_profit_krw_per_observation_day",
        "retained_signal_rate",
        "avg_realized_holding_minutes",
    ],
    "profit_cost_model": (
        "broker_exit_fill_price_minus_fixed_round_trip_cost_pct_including_"
        "verified_manual_operator_losses"
    ),
    "source_quality_gate": [
        "target_date_matches_state",
        "two_leg_v2_schema",
        "attempted_episode_has_signal_features_v1",
        "two_owned_quantity_legs_have_exact_terminal_or_open_status",
        "held_or_unresolved_inventory_blocks_candidate_readiness",
        "observation_source_quality_audit_tuning_input_allowed",
        "target_date_krx_trading_day_for_candidate",
        "prebaseline_and_nontrading_reports_excluded",
        "historical_replay_not_mixed_with_actual_outcomes",
        "subset_is_diagnostic_only_causal_confirmation_owned_by_entry_timing",
        "candidate_does_not_reduce_same_opportunity_broker_realized_net_profit",
        "machine_local_effective_policy_target_quantity_and_timing_cohort",
        "append_only_outcome_amendment_ledger",
        "exact_date_applied_policy_hash_and_fields",
        "verified_manual_operator_exit_is_realized_pnl_not_machine_target_success",
    ],
    "forbidden_uses": [
        "direct_or_same_day_runtime_or_threshold_mutation",
        "cross_machine_position_or_order_ownership",
        "historical_market_data_requery",
        "price_touch_as_fill",
        "legacy_one_leg_and_two_leg_sample_mixing",
        "forced_exit_or_stop_loss_creation",
        "manual_operator_exit_as_machine_target_fill_success",
        "provider_route_cap_bot_or_broker_guard_change",
        "real_runtime_approval",
        "cross_runtime_policy_hash_target_or_quantity_cohort_mixing",
    ],
}


def _clean_trading_dates_through(target_date: date) -> tuple[date, ...]:
    if target_date < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_precedes_clean_tuning_baseline")
    selected: list[date] = []
    current = CLEAN_BASELINE_DATE
    while current <= target_date:
        if is_krx_trading_day(current):
            selected.append(current)
        current += timedelta(days=1)
    return tuple(selected)


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _exit_execution_class(
    *, completed: bool, exit_fill_source: str, profit_price_source: str
) -> str:
    if not completed:
        return "not_realized"
    if (
        exit_fill_source == MANUAL_EXIT_FILL_SOURCE
        or profit_price_source == MANUAL_EXIT_PRICE_SOURCE
    ):
        return "manual_operator_exit"
    if profit_price_source == "broker_target_fill_price":
        return "machine_target_fill"
    if profit_price_source == "configured_target_price_proxy":
        return "configured_target_price_proxy"
    return "realized_exit_source_unknown"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _known_by_report_date(value: Any, target_date: str) -> bool:
    """Compare KST observation time to an exclusive end-of-report-day cutoff."""
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            if len(value) != 10:
                return False
            parsed = parsed.replace(tzinfo=KST)
        cutoff = datetime.fromisoformat(target_date).replace(tzinfo=KST) + timedelta(
            days=1
        )
        return parsed < cutoff
    except (TypeError, ValueError):
        return False


def _row_known_by_report_date(
    row: dict[str, Any], target_date: str, *, require_exit_timestamp: bool = False
) -> bool:
    if require_exit_timestamp and any(
        leg.get("completed") is True and not leg.get("target_filled_at")
        for leg in row.get("legs", [])
        if isinstance(leg, dict)
    ):
        # Unlike a frozen historical daily report, a mutable durable state has
        # no report-date knowledge boundary when its exit time is absent.
        return False
    timestamps = [
        leg.get(key)
        for leg in row.get("legs", [])
        if isinstance(leg, dict)
        for key in ("buy_filled_at", "target_filled_at")
        if leg.get(key)
    ]
    return all(_known_by_report_date(value, target_date) for value in timestamps)


def _receipt_known_by_report_date(receipt: dict[str, Any], target_date: str) -> bool:
    # Economic time AND first knowledge must be causal. An old entry date does
    # not backdate an operator correction.
    economic_time = receipt.get("filled_at_kst") or receipt.get("order_date")
    knowledge_time = receipt.get("applied_at_kst") or receipt.get("recorded_at_kst")
    return bool(
        _known_by_report_date(economic_time, target_date)
        and _known_by_report_date(knowledge_time, target_date)
    )


def _source_quality_preflight(
    target_date: str, source_quality_dir: Path
) -> dict[str, Any]:
    path = source_quality_dir / f"observation_source_quality_audit_{target_date}.json"
    payload = _read_json(path)
    if payload is None:
        preflight = {
            "status": "blocked",
            "tuning_input_allowed": False,
            "reason": "observation_source_quality_audit_missing_or_invalid",
            "source_path": str(path),
            "source_artifact_present": False,
            "audit_status": "missing",
        }
        preflight["source_sha256"] = canonical_hash(preflight)
        return preflight
    status = str(payload.get("status") or "").strip().lower()
    summary = payload.get("summary")
    allowed = isinstance(summary, dict) and summary.get("tuning_input_allowed") is True
    passed = (
        allowed
        and status in {"pass", "warning"}
        and payload.get("target_date") == target_date
        and payload.get("report_type") == "observation_source_quality_audit"
    )
    try:
        source_sha256 = file_sha256(path)
    except OSError:
        source_sha256 = ""
    return {
        "status": "pass" if passed else "blocked",
        "tuning_input_allowed": passed,
        "reason": "ready" if passed else "observation_source_quality_audit_blocked",
        "source_path": str(path),
        "source_sha256": source_sha256,
        "source_artifact_present": True,
        "audit_status": status,
    }


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


def _empty_machine_row(machine: str, target_date: str, reason: str) -> dict[str, Any]:
    return {
        "machine": machine,
        "target_date": target_date,
        "cohort": "source_unavailable",
        "eligible_for_cumulative_tuning": False,
        "source_quality": "gap",
        "source_quality_reasons": [reason],
        "state_status": "UNKNOWN",
        "attempted": False,
        "no_signal": False,
        "signal_features": {},
        "legs": [],
        "summary": _summarize_legs(False, []),
    }


def _pre_effective_machine_row(machine: str, target_date: str) -> dict[str, Any]:
    row = _empty_machine_row(machine, target_date, "machine_not_yet_effective")
    row.update(
        {
            "cohort": "pre_effective_not_applicable",
            "source_quality": "not_applicable",
            "state_status": "NOT_EFFECTIVE",
        }
    )
    return row


def _machine_effective(machine: str, target_date: date) -> bool:
    return target_date >= MACHINE_EFFECTIVE_DATES.get(machine, CLEAN_BASELINE_DATE)


def _sanitize_leg(leg: dict[str, Any], cost_pct: float) -> dict[str, Any]:
    status = str(leg.get("status") or "UNKNOWN")
    fill_price = _as_int(leg.get("fill_price"))
    target_price = _as_int(leg.get("target_price"))
    submitted = bool(str(leg.get("buy_order_no") or "").strip())
    filled = fill_price > 0
    target_submitted = bool(str(leg.get("target_order_no") or "").strip())
    position_qty = _as_int(leg.get("position_qty"))
    target_filled_qty = _as_int(leg.get("target_filled_qty"))
    target_fill_price = _as_int(leg.get("target_fill_price"))
    exit_fill_source = str(leg.get("exit_fill_source") or "")
    manual_exit_verified = exit_fill_source == MANUAL_EXIT_FILL_SOURCE
    buy_filled_qty = _as_int(
        leg.get("buy_filled_qty", position_qty + target_filled_qty)
    )
    completed = bool(
        status == "COMPLETE"
        and target_filled_qty > 0
        and target_filled_qty == buy_filled_qty
        and position_qty == 0
    )
    held = status == "HELD" or position_qty > 0
    terminal = status in TERMINAL_LEG_STATUSES
    profit_pct = None
    profit_exit_price = target_fill_price or target_price
    profit_price_source = (
        "broker_manual_sell_receipt"
        if completed and target_fill_price > 0 and manual_exit_verified
        else (
            "broker_target_fill_price"
            if completed and target_fill_price > 0
            else "configured_target_price_proxy" if completed else "not_completed"
        )
    )
    if completed and fill_price > 0 and profit_exit_price > 0:
        profit_pct = round((profit_exit_price / fill_price - 1.0) * 100.0 - cost_pct, 6)
    exit_execution_class = _exit_execution_class(
        completed=completed,
        exit_fill_source=exit_fill_source,
        profit_price_source=profit_price_source,
    )
    holding_duration_sec = _holding_duration_sec(
        str(leg.get("buy_filled_at") or ""),
        str(leg.get("target_filled_at") or ""),
    )
    return {
        "leg_id": str(leg.get("leg_id") or ""),
        "price_role": str(leg.get("price_role") or ""),
        "route": str(leg.get("route") or "SOR"),
        "quantity": _as_int(leg.get("quantity")),
        "entry_price": _as_int(leg.get("entry_price")),
        "status": status,
        "submitted": submitted,
        "filled": filled,
        "fill_price": fill_price,
        "buy_filled_at": str(leg.get("buy_filled_at") or "") or None,
        "target_submitted": target_submitted,
        "target_price": target_price,
        "position_qty": position_qty,
        "buy_filled_qty": buy_filled_qty,
        "target_filled_qty": target_filled_qty,
        "target_fill_price": target_fill_price,
        "target_filled_at": str(leg.get("target_filled_at") or "") or None,
        "exit_fill_source": exit_fill_source or None,
        "profit_exit_price": profit_exit_price if completed else 0,
        "profit_price_source": profit_price_source,
        "exit_execution_class": exit_execution_class,
        "manual_exit_realized": exit_execution_class == "manual_operator_exit",
        "autonomous_target_filled": exit_execution_class == "machine_target_fill",
        "realized_loss": bool(profit_pct is not None and profit_pct < 0.0),
        "completed": completed,
        "held": held,
        "unresolved": not terminal,
        "equal_weight_profit_pct": profit_pct,
        "holding_duration_sec": holding_duration_sec,
    }


def _holding_duration_sec(started_at: str, completed_at: str) -> int | None:
    if not started_at or not completed_at:
        return None
    try:
        started = datetime.fromisoformat(started_at)
        completed = datetime.fromisoformat(completed_at)
    except ValueError:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=KST)
    if completed.tzinfo is None:
        completed = completed.replace(tzinfo=KST)
    duration = int(
        (completed.astimezone(KST) - started.astimezone(KST)).total_seconds()
    )
    return duration if duration >= 0 else None


def _summarize_legs(attempted: bool, legs: list[dict[str, Any]]) -> dict[str, Any]:
    completed_returns = [
        float(leg["equal_weight_profit_pct"])
        for leg in legs
        if leg.get("equal_weight_profit_pct") is not None
    ]
    complete_episode = bool(
        attempted
        and len(legs) == 2
        and any(leg.get("submitted") for leg in legs)
        and all(str(leg.get("status")) in TERMINAL_LEG_STATUSES for leg in legs)
    )
    return {
        "attempted_legs": len(legs) if attempted else 0,
        "submitted_legs": sum(bool(leg.get("submitted")) for leg in legs),
        "filled_legs": sum(bool(leg.get("filled")) for leg in legs),
        "completed_legs": sum(bool(leg.get("completed")) for leg in legs),
        "machine_target_completed_legs": sum(
            leg.get("exit_execution_class") == "machine_target_fill" for leg in legs
        ),
        "manual_exit_completed_legs": sum(
            leg.get("exit_execution_class") == "manual_operator_exit" for leg in legs
        ),
        "manual_exit_loss_legs": sum(
            leg.get("exit_execution_class") == "manual_operator_exit"
            and leg.get("realized_loss") is True
            for leg in legs
        ),
        "held_legs": sum(bool(leg.get("held")) for leg in legs),
        "unresolved_legs": sum(bool(leg.get("unresolved")) for leg in legs),
        "completed_signal_episode": complete_episode,
        "equal_weight_avg_profit_pct": (
            round(sum(completed_returns) / len(completed_returns), 6)
            if completed_returns
            else None
        ),
    }


def _leg_outcome_contract_valid(leg: dict[str, Any]) -> bool:
    status = str(leg.get("status") or "")
    quantity = _as_int(leg.get("quantity"))
    position_qty = _as_int(leg.get("position_qty"))
    buy_filled_qty = _as_int(leg.get("buy_filled_qty"))
    target_filled_qty = _as_int(leg.get("target_filled_qty"))
    target_fill_price = _as_int(leg.get("target_fill_price"))
    if (
        status not in KNOWN_LEG_STATUSES
        or quantity not in SUPPORTED_OWNED_LEG_QUANTITIES
    ):
        return False
    if (
        _as_int(leg.get("entry_price")) < 0
        or not 0 <= target_filled_qty <= buy_filled_qty <= quantity
        or not 0 <= position_qty <= quantity
        or position_qty != buy_filled_qty - target_filled_qty
        or (target_fill_price > 0 and target_filled_qty <= 0)
        or (
            target_fill_price > 0
            and target_fill_price < _as_int(leg.get("target_price"))
            and leg.get("exit_fill_source") != MANUAL_EXIT_FILL_SOURCE
        )
    ):
        return False
    if status == "COMPLETE":
        return bool(leg.get("completed") and leg.get("filled") and not leg.get("held"))
    if status == "NO_FILL":
        return bool(
            not leg.get("filled") and not leg.get("completed") and not leg.get("held")
        )
    if leg.get("held"):
        return bool(
            leg.get("filled")
            and status in {"POSITION_OPEN", "TARGET_SUBMITTING", "TARGET_OPEN", "HELD"}
        )
    return not leg.get("completed")


def _normalize_historical_machine_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized_legs = []
    for leg in row.get("legs", []):
        if not isinstance(leg, dict):
            continue
        profit_price_source = (
            str(leg.get("profit_price_source"))
            if leg.get("profit_price_source")
            else (
                "broker_target_fill_price"
                if leg.get("completed") and _as_int(leg.get("target_fill_price"))
                else (
                    "configured_target_price_proxy"
                    if leg.get("completed")
                    and leg.get("equal_weight_profit_pct") is not None
                    else "not_completed"
                )
            )
        )
        exit_execution_class = _exit_execution_class(
            completed=bool(leg.get("completed")),
            exit_fill_source=str(leg.get("exit_fill_source") or ""),
            profit_price_source=profit_price_source,
        )
        net_profit = _as_float(leg.get("equal_weight_profit_pct"))
        normalized_legs.append(
            {
                **leg,
                "profit_price_source": profit_price_source,
                "exit_execution_class": exit_execution_class,
                "manual_exit_realized": (
                    exit_execution_class == "manual_operator_exit"
                ),
                "autonomous_target_filled": (
                    exit_execution_class == "machine_target_fill"
                ),
                "realized_loss": bool(
                    leg.get("completed") and net_profit is not None and net_profit < 0.0
                ),
                "holding_duration_sec": (
                    _as_int(leg.get("holding_duration_sec"))
                    if leg.get("holding_duration_sec") is not None
                    else _holding_duration_sec(
                        str(leg.get("buy_filled_at") or ""),
                        str(leg.get("target_filled_at") or ""),
                    )
                ),
            }
        )
    normalized["legs"] = normalized_legs
    attempted = bool(normalized.get("attempted"))
    outcome_complete_for_ev = bool(
        not attempted
        or (
            len(normalized["legs"]) == 2
            and all(
                str(leg.get("status") or "") in TERMINAL_LEG_STATUSES
                for leg in normalized["legs"]
            )
        )
    )
    normalized["outcome_complete_for_ev"] = outcome_complete_for_ev
    normalized["outcome_exclusion_reasons"] = (
        [] if outcome_complete_for_ev else ["held_or_unresolved_inventory"]
    )
    normalized["eligible_for_cumulative_tuning"] = (
        bool(normalized.get("eligible_for_cumulative_tuning"))
        and outcome_complete_for_ev
    )
    normalized["summary"] = _summarize_legs(attempted, normalized_legs)
    return normalized


def _build_outcome_amendment(
    *,
    machine: str,
    source_date: str,
    recorded_report_date: str,
    row: dict[str, Any],
    source_kind: str,
    source_ref: str,
    source_sha256: str,
) -> dict[str, Any]:
    normalized = _normalize_historical_machine_row(row)
    normalized["outcome_amendment_source_kind"] = source_kind
    core = {
        "schema": OUTCOME_AMENDMENT_SCHEMA,
        "machine": machine,
        "source_date": source_date,
        "recorded_report_date": recorded_report_date,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "source_sha256": source_sha256,
        "row_sha256": canonical_hash(normalized),
        "row": normalized,
    }
    return {**core, "amendment_id": canonical_hash(core)}


def _validate_outcome_amendment(value: Any) -> tuple[bool, str]:
    if not isinstance(value, dict) or value.get("schema") != OUTCOME_AMENDMENT_SCHEMA:
        return False, "amendment_schema_invalid"
    machine = str(value.get("machine") or "")
    if machine not in MACHINE_FILES:
        return False, "amendment_machine_invalid"
    try:
        source_date = date.fromisoformat(str(value.get("source_date") or ""))
        recorded_date = date.fromisoformat(str(value.get("recorded_report_date") or ""))
    except ValueError:
        return False, "amendment_date_invalid"
    if (
        source_date < CLEAN_BASELINE_DATE
        or recorded_date < source_date
        or not is_krx_trading_day(source_date)
    ):
        return False, "amendment_date_contract_invalid"
    if str(value.get("source_kind") or "") not in {
        "durable_state_reconciliation",
        "legacy_prior_state_reconciliation",
        "broker_verified_manual_exit_receipt_registry",
        "operator_custody_close_source_only",
    }:
        return False, "amendment_source_kind_invalid"
    if not str(value.get("source_ref") or ""):
        return False, "amendment_source_ref_missing"
    source_sha256 = str(value.get("source_sha256") or "")
    if not _is_sha256(source_sha256):
        return False, "amendment_source_hash_invalid"
    row = value.get("row")
    if (
        not isinstance(row, dict)
        or row.get("machine") != machine
        or row.get("target_date") != source_date.isoformat()
        or row.get("outcome_amendment_source_kind") != value.get("source_kind")
    ):
        return False, "amendment_row_identity_invalid"
    if value.get("row_sha256") != canonical_hash(row):
        return False, "amendment_row_hash_mismatch"
    if not _row_known_by_report_date(row, recorded_date.isoformat()):
        return False, "amendment_outcome_after_report_cutoff"
    legs = row.get("legs")
    if not isinstance(legs, list) or any(not isinstance(leg, dict) for leg in legs):
        return False, "amendment_row_legs_invalid"
    if row.get("summary") != _summarize_legs(bool(row.get("attempted")), legs):
        return False, "amendment_row_summary_mismatch"
    expected_complete = bool(
        not row.get("attempted")
        or (
            len(legs) == 2
            and all(
                str(leg.get("status") or "") in TERMINAL_LEG_STATUSES for leg in legs
            )
        )
    )
    if row.get("outcome_complete_for_ev") is not expected_complete:
        return False, "amendment_row_completion_mismatch"
    if row.get("eligible_for_cumulative_tuning") is True and (
        row.get("source_quality") != "pass" or not expected_complete
    ):
        return False, "amendment_row_eligibility_invalid"
    core = {key: item for key, item in value.items() if key != "amendment_id"}
    if value.get("amendment_id") != canonical_hash(core):
        return False, "amendment_id_mismatch"
    return True, "valid"


def _outcome_resolution_rank(row: dict[str, Any]) -> tuple[int, int, int, int, int]:
    summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
    resolution = (
        row.get("custody_resolution")
        if isinstance(row.get("custody_resolution"), dict)
        else {}
    )
    source_priority = {
        "broker_verified_manual_exit_receipt_registry": 3,
        "durable_state_reconciliation": 2,
        "legacy_prior_state_reconciliation": 1,
        "operator_custody_close_source_only": 0,
    }.get(str(row.get("outcome_amendment_source_kind") or ""), 0)
    return (
        int(bool(row.get("outcome_complete_for_ev"))),
        int(resolution.get("inventory_resolved") is True),
        source_priority,
        _as_int(summary.get("completed_legs")),
        -_as_int(summary.get("unresolved_legs")),
    )


def _effective_inventory_counts(row: dict[str, Any]) -> tuple[int, int]:
    summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
    resolution = (
        row.get("custody_resolution")
        if isinstance(row.get("custody_resolution"), dict)
        else {}
    )
    if resolution.get("inventory_resolved") is True:
        return 0, 0
    return _as_int(summary.get("held_legs")), _as_int(summary.get("unresolved_legs"))


def _resolve_row_with_broker_receipts(
    row: dict[str, Any], receipts: list[dict[str, Any]], *, cost_pct: float
) -> dict[str, Any] | None:
    normalized = _normalize_historical_machine_row(row)
    held_legs = [
        leg
        for leg in normalized.get("legs", [])
        if _as_int(leg.get("position_qty")) > 0
    ]
    held_quantity = sum(_as_int(leg.get("position_qty")) for leg in held_legs)
    receipt_lots = [
        {
            "quantity": _as_int(item.get("filled_qty")),
            "price": _as_int(item.get("fill_price")),
            "filled_at": str(item.get("filled_at_kst") or item.get("order_date") or ""),
        }
        for item in receipts
        if str(item.get("status") or "") == "applied"
        and _as_int(item.get("filled_qty")) > 0
        and _as_int(item.get("fill_price")) > 0
    ]
    if not held_legs or sum(item["quantity"] for item in receipt_lots) != held_quantity:
        return None
    remaining_lots = [dict(item) for item in receipt_lots]
    for leg in held_legs:
        required = _as_int(leg.get("position_qty"))
        allocated = 0
        proceeds = 0
        allocated_at: list[str] = []
        while required > 0 and remaining_lots:
            lot = remaining_lots[0]
            take = min(required, lot["quantity"])
            proceeds += take * lot["price"]
            allocated += take
            if lot["filled_at"]:
                allocated_at.append(lot["filled_at"])
            required -= take
            lot["quantity"] -= take
            if lot["quantity"] == 0:
                remaining_lots.pop(0)
        if required or allocated <= 0:
            return None
        exit_price = proceeds / allocated
        entry_price = _as_int(leg.get("fill_price"))
        if entry_price <= 0:
            return None
        leg.update(
            {
                "status": "COMPLETE",
                "position_qty": 0,
                "target_filled_qty": _as_int(leg.get("buy_filled_qty")),
                "target_fill_price": exit_price,
                "target_filled_at": max(allocated_at, default=""),
                "exit_fill_source": MANUAL_EXIT_FILL_SOURCE,
                "profit_exit_price": exit_price,
                "profit_price_source": MANUAL_EXIT_PRICE_SOURCE,
                "exit_execution_class": "manual_operator_exit",
                "manual_exit_realized": True,
                "autonomous_target_filled": False,
                "completed": True,
                "held": False,
                "unresolved": False,
                "equal_weight_profit_pct": round(
                    (exit_price / entry_price - 1.0) * 100.0 - cost_pct, 6
                ),
                "holding_duration_sec": _holding_duration_sec(
                    str(leg.get("buy_filled_at") or ""),
                    max(allocated_at, default=""),
                ),
            }
        )
        leg["realized_loss"] = leg["equal_weight_profit_pct"] < 0.0
    if remaining_lots:
        return None
    normalized["state_status"] = "COMPLETE"
    normalized["outcome_complete_for_ev"] = bool(
        all(
            str(leg.get("status") or "") in TERMINAL_LEG_STATUSES
            for leg in normalized.get("legs", [])
        )
    )
    normalized["outcome_exclusion_reasons"] = (
        []
        if normalized["outcome_complete_for_ev"]
        else ["held_or_unresolved_inventory"]
    )
    source_reasons = [
        str(item)
        for item in normalized.get("source_quality_reasons") or []
        if str(item) != "held_or_unresolved_inventory"
    ]
    normalized["source_quality_reasons"] = source_reasons
    normalized["source_quality"] = "pass" if not source_reasons else "gap"
    normalized["eligible_for_cumulative_tuning"] = bool(
        normalized["source_quality"] == "pass" and normalized["outcome_complete_for_ev"]
    )
    normalized["summary"] = _summarize_legs(
        bool(normalized.get("attempted")), normalized.get("legs", [])
    )
    return normalized


def _completed_manual_row_matches_receipts(
    row: dict[str, Any], receipts: list[dict[str, Any]]
) -> bool:
    if row.get("outcome_amendment_source_kind") == (
        "broker_verified_manual_exit_receipt_registry"
    ):
        return False
    manual_legs = [
        leg
        for leg in row.get("legs", [])
        if isinstance(leg, dict)
        and leg.get("exit_execution_class") == "manual_operator_exit"
        and leg.get("completed") is True
    ]
    if not manual_legs:
        return False
    row_quantity = sum(_as_int(leg.get("buy_filled_qty")) for leg in manual_legs)
    row_proceeds = sum(
        (_as_float(leg.get("target_fill_price")) or 0.0)
        * _as_int(leg.get("buy_filled_qty"))
        for leg in manual_legs
    )
    receipt_quantity = sum(_as_int(item.get("filled_qty")) for item in receipts)
    receipt_proceeds = sum(
        _as_int(item.get("fill_price")) * _as_int(item.get("filled_qty"))
        for item in receipts
    )
    return bool(
        row_quantity > 0
        and row_quantity == receipt_quantity
        and math.isclose(row_proceeds, receipt_proceeds, abs_tol=1e-6)
    )


def _policy_cohort_contract(
    row: dict[str, Any], machine: str, applied_dir: Path
) -> tuple[dict[str, Any] | None, str]:
    try:
        target_date = date.fromisoformat(str(row.get("target_date") or ""))
    except ValueError:
        return None, "policy_cohort_target_date_invalid"
    features = (
        row.get("signal_features")
        if isinstance(row.get("signal_features"), dict)
        else {}
    )
    as_of = (
        _signal_policy_as_of(features, target_date) if row.get("attempted") else None
    )
    if row.get("attempted") and as_of is None:
        return None, "policy_cohort_signal_timestamp_invalid"
    policy_machine = "morning" if machine == "morning_reentry" else machine
    policy, effective_hash, reason = load_applied_machine_policy(
        policy_machine,
        target_date=target_date,
        applied_dir=applied_dir,
        as_of=as_of,
    )
    if policy is None:
        if target_date >= APPLIED_POLICY_PROVENANCE_REQUIRED_DATE or not row.get(
            "attempted"
        ):
            return None, f"policy_cohort_applied_unavailable:{reason}"
        leg_quantities = {
            _as_int(item.get("quantity"))
            for item in row.get("legs", [])
            if isinstance(item, dict) and _as_int(item.get("quantity")) > 0
        }
        if len(leg_quantities) != 1 or not _signal_feature_contract_valid(
            machine, features
        ):
            return None, "legacy_policy_cohort_features_invalid"
        leg_quantity = leg_quantities.pop()
        cohort = {
            "machine": machine,
            "target_ticks": _as_int(features.get("target_ticks")),
            "episode_quantity": leg_quantity * 2,
            "leg_quantity_each": leg_quantity,
        }
        if machine == "morning":
            drawdowns = features.get("required_drawdown_pct_by_route") or {}
            cohort.update(
                {
                    "nxt_drawdown_pct": _as_float(drawdowns.get("NXT")),
                    "sor_drawdown_pct": _as_float(drawdowns.get("SOR")),
                }
            )
        elif machine == "morning_reentry":
            cohort["entry_policy"] = "fixed_user_approved_reentry_policy"
        else:
            cohort.update(
                {
                    "rolling_high_drawdown_pct": _as_float(
                        features.get("required_drawdown_pct")
                    ),
                    "rolling_low_proximity_pct": _as_float(
                        features.get("max_near_low_pct")
                    ),
                    "lookback_bars": _as_int(features.get("lookback_bars")),
                    "entry_valid_completed_bars": _as_int(
                        features.get("entry_valid_completed_bars")
                    ),
                }
            )
        cohort["effective_runtime_policy_hash"] = canonical_hash(cohort)
        return cohort, "ready_legacy_signal_feature_cohort"
    cohort = {
        "machine": machine,
        # Artifact-wide identity remains on signal_features for integrity. It
        # must not reset this machine's economic cohort when a sibling changes.
        "effective_runtime_policy_hash": canonical_hash(policy),
        "target_ticks": int(policy["target_ticks"]),
        "episode_quantity": int(policy["quantity"]),
        "leg_quantity_each": int(policy["quantity"]) // 2,
    }
    if machine == "morning":
        cohort.update(
            {
                "nxt_drawdown_pct": float(policy["nxt_drawdown_pct"]),
                "sor_drawdown_pct": float(policy["sor_drawdown_pct"]),
            }
        )
    elif machine == "morning_reentry":
        cohort["entry_policy"] = "fixed_user_approved_reentry_policy"
    else:
        cohort.update(
            {
                "rolling_high_drawdown_pct": float(policy["rolling_high_drawdown_pct"]),
                "rolling_low_proximity_pct": float(policy["rolling_low_proximity_pct"]),
                "lookback_bars": int(policy["lookback_bars"]),
                "entry_valid_completed_bars": int(policy["entry_valid_completed_bars"]),
            }
        )
    return cohort, "ready"


def _attach_policy_cohort(
    row: dict[str, Any], machine: str, applied_dir: Path
) -> dict[str, Any]:
    normalized = dict(row)
    cohort, reason = _policy_cohort_contract(normalized, machine, applied_dir)
    if cohort:
        features = normalized.get("signal_features") or {}
        if normalized.get("attempted"):
            timing = features.get("entry_timing_policy_provenance") or {}
            delay = _as_int(features.get("entry_confirmation_delay_sec"))
            mode = str(
                timing.get("entry_confirmation_mode")
                or ("fixed_delay" if delay else "baseline_immediate")
            )
            recipe = str(
                (timing.get("dynamic_runtime_decision") or {}).get("policy_id") or ""
            )
            if mode == "per_signal_dynamic_0_1_3_5":
                # Realized 1/3/5-second decisions are outcomes of one recipe,
                # not different applied policies or independent EV cohorts.
                delay = 0
        else:
            from src.trading.config.machine_entry_timing_policy import (
                resolve_entry_confirmation_policy,
            )
            from src.trading.market.micro_confirmation import dynamic_policy_for_scope

            scope = "morning_sor_reentry" if machine == "morning_reentry" else machine
            timing = resolve_entry_confirmation_policy(
                target_date=date.fromisoformat(str(row["target_date"])),
                owner="episode",
                scope_id=scope,
                symbol="005930",
                session="KRX_REGULAR",
                entry_state="UNSPECIFIED",
            )
            mode, delay = timing["mode"], timing["delay_sec"]
            recipe = (
                dynamic_policy_for_scope(
                    owner="episode", scope_id=scope, symbol="005930"
                ).policy_id
                if mode == "per_signal_dynamic_0_1_3_5"
                else ""
            )
        cohort["entry_confirmation"] = {
            "mode": mode,
            "delay_sec": delay,
            "recipe_id": recipe,
        }
    normalized["policy_cohort"] = cohort or {}
    normalized["policy_cohort_id"] = canonical_hash(cohort) if cohort else ""
    normalized["policy_cohort_status"] = reason
    if normalized.get("attempted") and cohort is None:
        normalized["eligible_for_cumulative_tuning"] = False
        normalized["source_quality"] = "gap"
        reasons = list(normalized.get("source_quality_reasons") or [])
        if reason not in reasons:
            reasons.append(reason)
        normalized["source_quality_reasons"] = reasons
    return normalized


def _runtime_policy_binding(target_date: str, applied_dir: Path) -> dict[str, Any]:
    """Freeze the ACTUALLY applied source-date policy, not an unconsumed candidate."""
    path = applied_dir / f"samsung_machine_entry_policy_{target_date}.json"
    policies = {}
    for machine, baseline in BASELINE_POLICIES.items():
        effective, _, reason = load_applied_machine_policy(
            machine,
            target_date=date.fromisoformat(target_date),
            applied_dir=applied_dir,
        )
        if effective is None:
            return {
                "status": "invalid" if path.exists() else "missing_baseline_only",
                "source_date": target_date,
                "source_artifact_present": path.exists(),
                "reason": reason,
                "policies": deepcopy(BASELINE_POLICIES),
            }
        # The separate approved +3 target overlay is not this tuner's axis.
        policies[machine] = {**effective, "target_ticks": baseline["target_ticks"]}
    return {
        "status": "ready",
        "source_date": target_date,
        "source_artifact_present": True,
        "source_sha256": file_sha256(path),
        "policies": policies,
    }


def _same_machine_entry_policy(cohort: Any, policy: dict[str, Any]) -> bool:
    return (
        isinstance(cohort, dict)
        and all(
            _as_float(cohort.get(key)) == _as_float(policy.get(key))
            for key in (
                "rolling_high_drawdown_pct",
                "rolling_low_proximity_pct",
                "lookback_bars",
                "entry_valid_completed_bars",
            )
        )
        and _as_int(cohort.get("episode_quantity")) == _as_int(policy.get("quantity"))
    )


def _sanitize_signal_features(machine: str, raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    raw_entry_legs = raw.get("entry_legs")
    common = {
        "schema": str(raw.get("schema") or ""),
        "strategy": str(raw.get("strategy") or ""),
        "source": str(raw.get("source") or ""),
        "signal_bar": str(raw.get("signal_bar") or ""),
        "signal_close": _as_int(raw.get("signal_close")),
        "signal_decision_at": str(raw.get("signal_decision_at") or ""),
        "source_entry_event_id": str(raw.get("source_entry_event_id") or ""),
        "entry_confirmation_delay_sec": _as_int(
            raw.get("entry_confirmation_delay_sec")
        ),
        "entry_timing_policy_provenance": (
            dict(raw.get("entry_timing_policy_provenance"))
            if isinstance(raw.get("entry_timing_policy_provenance"), dict)
            else {}
        ),
        "required_drawdown_pct": _as_float(raw.get("required_drawdown_pct")),
        "target_ticks": _as_int(raw.get("target_ticks")),
        "runtime_policy_source": str(raw.get("runtime_policy_source") or ""),
        "runtime_policy_hash": str(raw.get("runtime_policy_hash") or ""),
        "entry_legs": [
            {
                "leg_id": str(item.get("leg_id") or ""),
                "price_role": str(item.get("price_role") or ""),
                "entry_price": _as_int(item.get("entry_price")),
                "route": str(item.get("route") or ""),
            }
            for item in (raw_entry_legs if isinstance(raw_entry_legs, list) else [])
            if isinstance(item, dict)
        ],
    }
    if machine == "morning":
        raw_opening_prices = raw.get("opening_prices")
        raw_drawdowns = raw.get("required_drawdown_pct_by_route")
        raw_routes = raw.get("routes")
        raw_entry_windows = raw.get("entry_windows")
        common.update(
            {
                "route": str(raw.get("route") or ""),
                "routes": sorted(
                    {
                        str(item)
                        for item in (raw_routes if isinstance(raw_routes, list) else [])
                        if str(item) in {"NXT", "SOR"}
                    }
                ),
                "opening_price": _as_int(raw.get("opening_price")),
                "opening_prices": {
                    str(key): _as_int(value)
                    for key, value in (
                        raw_opening_prices.items()
                        if isinstance(raw_opening_prices, dict)
                        else []
                    )
                    if str(key) in {"NXT", "SOR"}
                },
                "required_drawdown_pct_by_route": {
                    str(key): _as_float(value)
                    for key, value in (
                        raw_drawdowns.items() if isinstance(raw_drawdowns, dict) else []
                    )
                    if str(key) in {"NXT", "SOR"}
                },
                "entry_window_start": str(raw.get("entry_window_start") or ""),
                "entry_window_deadline": str(raw.get("entry_window_deadline") or ""),
                "entry_windows": {
                    str(key): {
                        "start": str(value.get("start") or ""),
                        "deadline": str(value.get("deadline") or ""),
                    }
                    for key, value in (
                        raw_entry_windows.items()
                        if isinstance(raw_entry_windows, dict)
                        else []
                    )
                    if str(key) in {"NXT", "SOR"} and isinstance(value, dict)
                },
            }
        )
        return common
    common.update(
        {
            "signal_close": _as_int(raw.get("signal_close")),
            "rolling_high": _as_int(raw.get("rolling_high")),
            "rolling_low": _as_int(raw.get("rolling_low")),
            "observed_drawdown_pct": _as_float(raw.get("observed_drawdown_pct")),
            "observed_near_low_pct": _as_float(raw.get("observed_near_low_pct")),
            "lookback_bars": _as_int(raw.get("lookback_bars")),
            "max_near_low_pct": _as_float(raw.get("max_near_low_pct")),
            "entry_valid_completed_bars": _as_int(
                raw.get("entry_valid_completed_bars")
            ),
            "scan_start": str(raw.get("scan_start") or ""),
            "scan_last_bar": str(raw.get("scan_last_bar") or ""),
        }
    )
    if machine == "morning_reentry":
        common.update(
            {
                "family": str(raw.get("family") or ""),
                "confirmation_bars": _as_int(raw.get("confirmation_bars")),
                "reclaim_ticks": _as_int(raw.get("reclaim_ticks")),
                "entry_offset_ticks": _as_int(raw.get("entry_offset_ticks")),
                "prerequisite": (
                    dict(raw.get("prerequisite"))
                    if isinstance(raw.get("prerequisite"), dict)
                    else {}
                ),
            }
        )
    return common


def _signal_feature_contract_valid(machine: str, features: dict[str, Any]) -> bool:
    entry_legs = features.get("entry_legs")
    if (
        not isinstance(entry_legs, list)
        or len(entry_legs) != 2
        or len({item.get("leg_id") for item in entry_legs}) != 2
        or any(_as_int(item.get("entry_price")) <= 0 for item in entry_legs)
        or _as_int(features.get("target_ticks")) <= 0
        or not _is_sha256(features.get("runtime_policy_hash"))
    ):
        return False
    if machine == "morning_reentry":
        prerequisite = features.get("prerequisite")
        legacy_target_provenance = bool(
            features.get("runtime_policy_source")
            == "user_approved_sor_reentry_2026-08-12"
            and features.get("runtime_policy_hash")
            == "6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a"
            and _as_int(features.get("target_ticks")) == 2
        )
        override_target_provenance = bool(
            features.get("runtime_policy_source") == OPERATOR_OVERRIDE_RUNTIME_SOURCE
            and _is_sha256(features.get("runtime_policy_hash"))
            and _as_int(features.get("target_ticks")) == 3
        )
        return bool(
            features.get("schema") == "samsung_morning_sor_reentry_signal_features_v1"
            and features.get("strategy") == "morning_sor_reentry"
            and features.get("source") == "kiwoom_ka10080_005930_AL_completed_1m"
            and (legacy_target_provenance or override_target_provenance)
            and features.get("family") == "low_hold_reclaim_passive_split"
            and _as_int(features.get("lookback_bars")) == 15
            and _as_int(features.get("confirmation_bars")) == 2
            and _as_int(features.get("reclaim_ticks")) == 1
            and _as_int(features.get("entry_offset_ticks")) == 1
            and _as_int(features.get("entry_valid_completed_bars")) == 3
            and isinstance(prerequisite, dict)
            and prerequisite.get("first_episode_status") == "COMPLETE"
            and _as_int(prerequisite.get("required_completed_leg_count")) == 2
            and prerequisite.get("first_episode_completed_at")
        )
    if features.get("runtime_policy_source") not in {
        "preopen_applied_policy",
        OPERATOR_OVERRIDE_RUNTIME_SOURCE,
    }:
        return False
    if machine == "morning":
        routes = features.get("routes")
        opening_prices = features.get("opening_prices")
        drawdowns = features.get("required_drawdown_pct_by_route")
        entry_windows = features.get("entry_windows")
        return bool(
            features.get("schema") == "samsung_morning_entry_signal_features_v1"
            and features.get("strategy") == "morning"
            and features.get("route") in {"NXT", "SOR", "MIXED"}
            and isinstance(routes, list)
            and routes
            and set(routes) <= {"NXT", "SOR"}
            and isinstance(opening_prices, dict)
            and set(opening_prices) == set(routes)
            and all(_as_int(value) > 0 for value in opening_prices.values())
            and isinstance(drawdowns, dict)
            and set(drawdowns) == set(routes)
            and all((_as_float(value) or 0) > 0 for value in drawdowns.values())
            and isinstance(entry_windows, dict)
            and set(entry_windows) == set(routes)
            and all(
                value.get("start") and value.get("deadline")
                for value in entry_windows.values()
            )
            and features.get("signal_bar")
        )
    return bool(
        features.get("schema") == "samsung_regular_entry_signal_features_v1"
        and features.get("strategy") == machine
        and _as_int(features.get("signal_close")) > 0
        and _as_int(features.get("rolling_high")) > 0
        and _as_int(features.get("rolling_low")) > 0
        and _as_int(features.get("lookback_bars")) > 0
        and _as_int(features.get("entry_valid_completed_bars")) > 0
        and (_as_float(features.get("observed_drawdown_pct")) is not None)
        and (_as_float(features.get("observed_near_low_pct")) is not None)
        and features.get("signal_bar")
    )


def _signal_policy_as_of(
    features: dict[str, Any], target_date: date
) -> datetime | None:
    raw = str(features.get("signal_bar") or "")
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        for pattern in ("%Y%m%d%H%M%S", "%Y%m%d%H%M"):
            try:
                parsed = datetime.strptime(raw, pattern)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    observed_at = parsed.astimezone(KST)
    if observed_at.date() != target_date:
        return None
    return observed_at


def extract_machine_row(
    *,
    machine: str,
    state_path: Path,
    target_date: str,
    cost_pct: float,
    applied_dir: Path = APPLIED_DIR,
) -> dict[str, Any]:
    state = _read_json(state_path)
    if state is None:
        return _empty_machine_row(machine, target_date, "state_missing_or_invalid_json")
    schema = str(state.get("schema") or "")
    state_date = str(state.get("trade_date") or "")
    if state_date != target_date:
        row = _empty_machine_row(machine, target_date, "state_trade_date_mismatch")
        row.update({"observed_state_date": state_date, "observed_schema": schema})
        return row
    if schema == LEGACY_SCHEMAS.get(machine):
        row = _empty_machine_row(machine, target_date, "legacy_one_leg_archive_only")
        row.update(
            {
                "cohort": "legacy_one_leg_archive_only",
                "observed_schema": schema,
                "state_status": str(state.get("status") or "UNKNOWN"),
                "attempted": bool(state.get("attempt_consumed")),
            }
        )
        return row
    if schema != EXPECTED_SCHEMAS[machine]:
        row = _empty_machine_row(machine, target_date, "unexpected_state_schema")
        row["observed_schema"] = schema
        return row

    attempted = bool(state.get("attempt_consumed"))
    state_status = str(state.get("status") or "UNKNOWN")
    blocked_reason = str(state.get("blocked_reason") or "")
    signal_features = _sanitize_signal_features(machine, state.get("signal_features"))
    if (
        machine == "morning_reentry"
        and not attempted
        and state_status == "BLOCKED"
        and blocked_reason == "first_episode_both_legs_not_complete"
        and state.get("legs") == []
    ):
        row = _empty_machine_row(
            machine, target_date, "first_episode_both_legs_not_complete"
        )
        row.update(
            {
                "cohort": "prerequisite_not_met",
                "eligible_for_cumulative_tuning": True,
                "source_quality": "pass",
                "source_quality_reasons": [],
                "state_status": state_status,
                "no_signal": False,
                "prerequisite_met": False,
                "observed_schema": schema,
                "blocked_reason": blocked_reason,
            }
        )
        return row
    reasons: list[str] = []
    if state_status == "BLOCKED":
        reasons.append("machine_state_blocked")
    if not attempted and state_status != "NO_TRADE":
        reasons.append("non_attempted_machine_not_terminal")
    if attempted and not _signal_feature_contract_valid(machine, signal_features):
        reasons.append("attempted_episode_signal_features_missing_or_invalid")
    parsed_target_date = date.fromisoformat(target_date)
    if attempted and parsed_target_date >= APPLIED_POLICY_PROVENANCE_REQUIRED_DATE:
        policy_machine = "morning" if machine == "morning_reentry" else machine
        policy_as_of = _signal_policy_as_of(signal_features, parsed_target_date)
        if policy_as_of is None:
            reasons.append("signal_feature_policy_timestamp_invalid")
            policy_as_of = datetime.combine(
                parsed_target_date, datetime.max.time(), tzinfo=KST
            )
        applied_policy, applied_hash, applied_reason = load_applied_machine_policy(
            policy_machine,
            target_date=parsed_target_date,
            applied_dir=applied_dir,
            as_of=policy_as_of,
        )
        if applied_policy is None:
            reasons.append(f"exact_date_applied_policy_invalid:{applied_reason}")
        else:
            raw_state_legs = state.get("legs")
            if not isinstance(raw_state_legs, list) or any(
                _as_int(leg.get("quantity")) * 2 != int(applied_policy["quantity"])
                for leg in raw_state_legs
                if isinstance(leg, dict)
            ):
                reasons.append("exact_date_applied_quantity_mismatch")
            expected_fields = {
                "target_ticks": int(applied_policy["target_ticks"]),
            }
            if machine == "morning":
                expected_fields.update(
                    {
                        "nxt_drawdown_pct": float(applied_policy["nxt_drawdown_pct"]),
                        "sor_drawdown_pct": float(applied_policy["sor_drawdown_pct"]),
                    }
                )
                observed_matches = bool(
                    _as_int(signal_features.get("target_ticks"))
                    == expected_fields["target_ticks"]
                    and _as_float(
                        (
                            signal_features.get("required_drawdown_pct_by_route") or {}
                        ).get("NXT")
                    )
                    in {None, expected_fields["nxt_drawdown_pct"]}
                    and _as_float(
                        (
                            signal_features.get("required_drawdown_pct_by_route") or {}
                        ).get("SOR")
                    )
                    in {None, expected_fields["sor_drawdown_pct"]}
                )
            elif machine == "morning_reentry":
                observed_matches = bool(
                    _as_int(signal_features.get("target_ticks"))
                    == expected_fields["target_ticks"]
                )
            else:
                observed_matches = bool(
                    _as_int(signal_features.get("target_ticks"))
                    == expected_fields["target_ticks"]
                    and _as_float(signal_features.get("required_drawdown_pct"))
                    == float(applied_policy["rolling_high_drawdown_pct"])
                    and _as_float(signal_features.get("max_near_low_pct"))
                    == float(applied_policy["rolling_low_proximity_pct"])
                    and _as_int(signal_features.get("lookback_bars"))
                    == int(applied_policy["lookback_bars"])
                    and _as_int(signal_features.get("entry_valid_completed_bars"))
                    == int(applied_policy["entry_valid_completed_bars"])
                )
            legacy_reentry_policy = bool(
                machine == "morning_reentry" and applied_reason == "ready"
            )
            expected_runtime_source = (
                "user_approved_sor_reentry_2026-08-12"
                if legacy_reentry_policy
                else (
                    OPERATOR_OVERRIDE_RUNTIME_SOURCE
                    if applied_reason == "ready_operator_override"
                    else "preopen_applied_policy"
                )
            )
            expected_runtime_hash = (
                "6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a"
                if legacy_reentry_policy
                else applied_hash
            )
            if (
                signal_features.get("runtime_policy_source") != expected_runtime_source
                or signal_features.get("runtime_policy_hash") != expected_runtime_hash
                or not observed_matches
            ):
                reasons.append("signal_feature_exact_date_applied_policy_mismatch")
    raw_legs = state.get("legs")
    if not isinstance(raw_legs, list):
        raw_legs = []
        reasons.append("state_legs_invalid")
    legs = [_sanitize_leg(leg, cost_pct) for leg in raw_legs if isinstance(leg, dict)]
    if attempted and (
        len(legs) != 2
        or any(leg["quantity"] not in SUPPORTED_OWNED_LEG_QUANTITIES for leg in legs)
        or len({leg["quantity"] for leg in legs}) != 1
        or len({leg["leg_id"] for leg in legs}) != 2
    ):
        reasons.append("attempted_episode_two_leg_quantity_contract_invalid")
    if attempted and any(not _leg_outcome_contract_valid(leg) for leg in legs):
        reasons.append("attempted_episode_leg_outcome_contract_invalid")
    feature_leg_identity = {
        (
            str(item.get("leg_id") or ""),
            _as_int(item.get("entry_price")),
            str(item.get("route") or "") if machine == "morning" else "SOR",
        )
        for item in signal_features.get("entry_legs", [])
    }
    runtime_leg_identity = {
        (
            str(item.get("leg_id") or ""),
            _as_int(item.get("entry_price")),
            str(item.get("route") or "") if machine == "morning" else "SOR",
        )
        for item in legs
    }
    if attempted and feature_leg_identity != runtime_leg_identity:
        reasons.append("signal_feature_and_runtime_leg_price_mismatch")
    summary = _summarize_legs(attempted, legs)
    outcome_complete_for_ev = bool(
        not attempted
        or (
            len(legs) == 2
            and all(str(leg.get("status")) in TERMINAL_LEG_STATUSES for leg in legs)
        )
    )
    return {
        "machine": machine,
        "target_date": target_date,
        "cohort": "two_leg_runtime",
        "eligible_for_cumulative_tuning": not reasons and outcome_complete_for_ev,
        "outcome_complete_for_ev": outcome_complete_for_ev,
        "outcome_exclusion_reasons": (
            [] if outcome_complete_for_ev else ["held_or_unresolved_inventory"]
        ),
        "source_quality": "pass" if not reasons else "gap",
        "source_quality_reasons": reasons,
        "observed_schema": schema,
        "state_status": state_status,
        "attempted": attempted,
        "no_signal": not attempted and state_status == "NO_TRADE",
        "signal_features": signal_features,
        "legs": legs,
        "summary": summary,
    }


def _aggregate_rows(
    rows: list[dict[str, Any]],
    *,
    observation_day_count: int | None = None,
    current_policy_signal_count: int | None = None,
) -> dict[str, Any]:
    eligible = [row for row in rows if row.get("eligible_for_cumulative_tuning")]
    attempted = [row for row in eligible if row.get("attempted")]
    all_attempted = [row for row in rows if row.get("attempted")]
    summaries = [row.get("summary", {}) for row in attempted]
    completed_returns = [
        float(leg["equal_weight_profit_pct"])
        for row in attempted
        for leg in row.get("legs", [])
        if leg.get("equal_weight_profit_pct") is not None
    ]
    broker_priced_completed = [
        leg
        for row in attempted
        for leg in row.get("legs", [])
        if leg.get("equal_weight_profit_pct") is not None
        and leg.get("profit_price_source")
        in {"broker_target_fill_price", "broker_manual_sell_receipt"}
    ]
    manual_exit_completed = [
        leg
        for leg in broker_priced_completed
        if leg.get("exit_execution_class") == "manual_operator_exit"
    ]
    manual_exit_losses = [
        leg for leg in manual_exit_completed if leg.get("realized_loss") is True
    ]
    machine_target_completed = [
        leg
        for leg in broker_priced_completed
        if leg.get("exit_execution_class") == "machine_target_fill"
    ]
    target_proxy_completed = [
        leg
        for row in attempted
        for leg in row.get("legs", [])
        if leg.get("equal_weight_profit_pct") is not None
        and leg.get("profit_price_source") == "configured_target_price_proxy"
    ]
    duration_completed = [
        leg
        for row in attempted
        for leg in row.get("legs", [])
        if leg.get("completed") is True
        if _as_float(leg.get("holding_duration_sec")) is not None
    ]
    attempted_notional = sum(
        _as_int(leg.get("entry_price")) * _as_int(leg.get("quantity"))
        for row in attempted
        for leg in row.get("legs", [])
    )
    broker_completed_net_profit = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["equal_weight_profit_pct"])
        / 100.0
        for leg in broker_priced_completed
    )
    target_proxy_net_profit = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["equal_weight_profit_pct"])
        / 100.0
        for leg in target_proxy_completed
    )
    manual_exit_fixed_cost_estimate_profit = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["equal_weight_profit_pct"])
        / 100.0
        for leg in manual_exit_completed
    )
    attempted_legs = sum(_as_int(item.get("attempted_legs")) for item in summaries)
    submitted_legs = sum(_as_int(item.get("submitted_legs")) for item in summaries)
    completed_legs = sum(_as_int(item.get("completed_legs")) for item in summaries)
    inventory_counts = [_effective_inventory_counts(row) for row in all_attempted]
    held_legs = sum(item[0] for item in inventory_counts)
    unresolved_legs = sum(item[1] for item in inventory_counts)
    complete_episodes = sum(
        bool(item.get("completed_signal_episode")) for item in summaries
    )
    equal_weight_avg_profit_pct = (
        round(sum(completed_returns) / len(completed_returns), 6)
        if completed_returns
        else None
    )
    source_gaps = sum(
        row.get("cohort")
        not in {"legacy_one_leg_archive_only", "pre_effective_not_applicable"}
        and row.get("source_quality") != "pass"
        for row in rows
    )
    resolved_observation_days = (
        max(0, int(observation_day_count))
        if observation_day_count is not None
        else len(rows)
    )
    signal_rate = (
        len(attempted) / resolved_observation_days
        if resolved_observation_days > 0
        else None
    )
    if held_legs or unresolved_legs:
        candidate_status = "inventory_or_order_unresolved"
    elif complete_episodes < SAMPLE_FLOOR:
        if (
            resolved_observation_days >= RATE_ASSESSMENT_MIN_OBSERVATION_DAYS
            and not attempted
        ):
            candidate_status = "structural_no_signal_observation"
        elif (
            resolved_observation_days >= RATE_ASSESSMENT_MIN_OBSERVATION_DAYS
            and signal_rate is not None
            and signal_rate < LOW_SIGNAL_RATE_THRESHOLD
        ):
            candidate_status = "evidence_accumulating_low_signal_rate"
        else:
            candidate_status = "collect_sample"
    elif len(broker_priced_completed) < AUTO_MIN_COMPLETED_LEGS:
        candidate_status = "collect_broker_sell_fill_price"
    else:
        # Source/sample readiness is independent of the control strategy's PnL.
        # A losing control must not veto an independently positive challenger.
        candidate_status = "auto_bounded_candidate_ready"
    retained_signal_rate = (
        round(len(attempted) / current_policy_signal_count, 6)
        if current_policy_signal_count
        else None
    )
    broker_completed_notional = sum(
        _as_int(leg.get("fill_price")) * _as_int(leg.get("buy_filled_qty"))
        for leg in broker_priced_completed
    )
    episode_days_remaining = (
        max(
            0,
            math.ceil(
                (SAMPLE_FLOOR - complete_episodes)
                * resolved_observation_days
                / complete_episodes
            ),
        )
        if complete_episodes and resolved_observation_days
        else None
    )
    broker_days_remaining = (
        max(
            0,
            math.ceil(
                (AUTO_MIN_COMPLETED_LEGS - len(broker_priced_completed))
                * resolved_observation_days
                / len(broker_priced_completed)
            ),
        )
        if broker_priced_completed and resolved_observation_days
        else None
    )
    return {
        "report_days": len(rows),
        "eligible_report_days": len(eligible),
        "source_gap_days": source_gaps,
        "legacy_excluded_days": sum(
            row.get("cohort") == "legacy_one_leg_archive_only" for row in rows
        ),
        "signal_attempts": len(attempted),
        "observed_signal_attempts": len(all_attempted),
        "no_signal_days": sum(bool(row.get("no_signal")) for row in eligible),
        "completed_signal_episodes": complete_episodes,
        "attempted_legs": attempted_legs,
        "submitted_legs": submitted_legs,
        "filled_legs": sum(_as_int(item.get("filled_legs")) for item in summaries),
        "completed_legs": completed_legs,
        "broker_priced_completed_legs": len(broker_priced_completed),
        "machine_target_completed_legs": len(machine_target_completed),
        "manual_exit_completed_legs": len(manual_exit_completed),
        "manual_exit_loss_legs": len(manual_exit_losses),
        "target_price_proxy_completed_legs": len(target_proxy_completed),
        "broker_sell_fill_price_coverage": (
            round(len(broker_priced_completed) / completed_legs, 6)
            if completed_legs
            else None
        ),
        "held_legs": held_legs,
        "unresolved_legs": unresolved_legs,
        "actual_fill_rate": (
            round(
                sum(_as_int(item.get("filled_legs")) for item in summaries)
                / submitted_legs,
                6,
            )
            if submitted_legs
            else None
        ),
        "completed_legs_per_attempted_leg": (
            round(completed_legs / attempted_legs, 6) if attempted_legs else None
        ),
        "equal_weight_avg_profit_pct": equal_weight_avg_profit_pct,
        "notional_weighted_ev_pct": (
            round(broker_completed_net_profit / broker_completed_notional * 100.0, 6)
            if broker_completed_notional > 0
            else None
        ),
        "attempted_notional_return_pct_diagnostic": (
            round(broker_completed_net_profit / attempted_notional * 100.0, 6)
            if attempted_notional > 0
            else None
        ),
        "broker_completed_notional_krw": broker_completed_notional,
        "observation_coverage_pct": (
            round(len(eligible) / len(rows) * 100, 6) if rows else None
        ),
        "open_inventory_notional_krw_diagnostic": sum(
            _as_int(leg.get("position_qty")) * _as_int(leg.get("fill_price"))
            for row in rows
            if not (row.get("custody_resolution") or {}).get("inventory_resolved")
            for leg in row.get("legs", [])
        ),
        "broker_realized_net_profit_krw": round(broker_completed_net_profit, 3),
        "expected_net_profit_krw_per_observation_day": (
            round(broker_completed_net_profit / resolved_observation_days, 3)
            if resolved_observation_days > 0
            else None
        ),
        "observation_day_count": resolved_observation_days,
        "signal_rate_per_observation_day": (
            round(signal_rate, 6) if signal_rate is not None else None
        ),
        "retained_signal_rate": retained_signal_rate,
        "estimated_observation_days_to_sample_floor": (
            max(episode_days_remaining, broker_days_remaining)
            if episode_days_remaining is not None and broker_days_remaining is not None
            else None
        ),
        "sample_floor_estimate_contract": {
            "status": (
                "rate_projection_not_runtime_approval_eta"
                if broker_days_remaining is not None
                else "no_broker_completion_rate_available"
            ),
            "completed_episode_days_remaining": episode_days_remaining,
            "broker_priced_leg_days_remaining": broker_days_remaining,
            "assumes_stationary_completion_rate": True,
            "does_not_predict_positive_ev_or_source_recovery": True,
        },
        "realized_holding_duration_coverage": (
            round(len(duration_completed) / completed_legs, 6)
            if completed_legs
            else None
        ),
        "avg_realized_holding_minutes": (
            round(
                sum(float(leg["holding_duration_sec"]) for leg in duration_completed)
                / len(duration_completed)
                / 60.0,
                3,
            )
            if duration_completed
            else None
        ),
        "manual_exit_fixed_cost_estimate_net_profit_krw": round(
            manual_exit_fixed_cost_estimate_profit, 3
        ),
        "target_price_proxy_notional_weighted_ev_pct": (
            round(target_proxy_net_profit / attempted_notional * 100.0, 6)
            if attempted_notional > 0
            else None
        ),
        "candidate_status": candidate_status,
        "allowed_runtime_apply": False,
    }


def _axis_observations(
    rows: list[dict[str, Any]], machine: str
) -> list[dict[str, Any]]:
    attempted = [
        row
        for row in rows
        if row.get("eligible_for_cumulative_tuning") and row.get("attempted")
    ]
    if machine == "morning":
        segments: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in attempted:
            features = row.get("signal_features", {})
            key = (
                str(row.get("policy_cohort_id") or ""),
                str(features.get("route") or "UNKNOWN"),
                json.dumps(
                    features.get("required_drawdown_pct_by_route", {}),
                    sort_keys=True,
                ),
            )
            segments[key].append(row)
        return [
            {
                "axis": "current_route_drawdown_policy",
                "policy_cohort_id": policy_cohort_id,
                "route": route,
                "required_drawdown_pct_by_route": json.loads(drawdown_policy),
                "outcome": _aggregate_rows(group),
                "interpretation": "current_policy_outcome_only_no_relaxation_counterfactual",
            }
            for (policy_cohort_id, route, drawdown_policy), group in sorted(
                segments.items()
            )
        ]

    if machine == "morning_reentry":
        latest_cohort_id = (
            str(attempted[-1].get("policy_cohort_id") or "") if attempted else ""
        )
        cohort_attempted = [
            row
            for row in attempted
            if str(row.get("policy_cohort_id") or "") == latest_cohort_id
        ]
        return (
            [
                {
                    "axis": "fixed_user_approved_reentry_policy",
                    "policy_cohort_id": latest_cohort_id,
                    "outcome": _aggregate_rows(cohort_attempted),
                    "interpretation": (
                        "actual_outcome_observation_only_no_automatic_policy_mutation"
                    ),
                }
            ]
            if cohort_attempted
            else []
        )

    if not attempted:
        return []
    latest_cohort_id = str(attempted[-1].get("policy_cohort_id") or "")
    if not latest_cohort_id:
        return []
    current_cohort_rows = [
        row
        for row in rows
        if row.get("eligible_for_cumulative_tuning")
        and str(row.get("policy_cohort_id") or "") == latest_cohort_id
    ]
    current_cohort = attempted[-1].get("policy_cohort") or {}
    current_drawdown = _as_float(current_cohort.get("rolling_high_drawdown_pct"))
    current_near_low = _as_float(current_cohort.get("rolling_low_proximity_pct"))
    if current_drawdown is None or current_near_low is None:
        return []
    current_cohort = [
        row
        for row in attempted
        if str(row.get("policy_cohort_id") or "") == latest_cohort_id
    ]
    policy_grid = {
        (current_drawdown, current_near_low),
        (max(current_drawdown, 1.50), current_near_low),
        (current_drawdown, min(current_near_low, 0.10)),
        (max(current_drawdown, 1.50), min(current_near_low, 0.10)),
    }
    observations = []
    for min_drawdown, max_near_low in sorted(policy_grid):
        matching = []
        for row in current_cohort:
            features = row.get("signal_features", {})
            drawdown = _as_float(features.get("observed_drawdown_pct"))
            near_low = _as_float(features.get("observed_near_low_pct"))
            if drawdown is None or near_low is None:
                continue
            if min_drawdown is not None and drawdown < min_drawdown:
                continue
            if max_near_low is not None and near_low > max_near_low:
                continue
            matching.append(row)
        observations.append(
            {
                "axis": (f"drawdown_{min_drawdown:.4f}_near_low_{max_near_low:.4f}"),
                "min_observed_drawdown_pct": min_drawdown,
                "max_observed_near_low_pct": max_near_low,
                "resulting_policy": {
                    "rolling_high_drawdown_pct": min_drawdown,
                    "rolling_low_proximity_pct": max_near_low,
                },
                "current_policy_cohort": {
                    "rolling_high_drawdown_pct": current_drawdown,
                    "rolling_low_proximity_pct": current_near_low,
                },
                "policy_cohort_id": latest_cohort_id,
                "policy_cohort": attempted[-1].get("policy_cohort") or {},
                "outcome": _aggregate_rows(
                    matching,
                    observation_day_count=len(current_cohort_rows),
                    current_policy_signal_count=len(current_cohort),
                ),
                "interpretation": "tightening_subset_only_not_a_relaxation_backtest",
            }
        )
    return observations


def build_policy_candidate(
    report: dict[str, Any],
    *,
    prior_policies: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Maintain actual policy custody; causal optimization belongs to entry timing.

    Historical signal subsets cannot model a later first signal or fill, so
    they have no new tightening authority. The only remaining mutation here is
    an evidence-bound unwind of a previously APPLIED legacy tightening.
    """
    binding = report.get("source_runtime_policy_binding") or {}
    starting = deepcopy(
        binding.get("policies")
        if binding.get("status") == "ready"
        else BASELINE_POLICIES
    )
    machines: dict[str, Any] = {}
    rollback_choices = []
    for machine, baseline in BASELINE_POLICIES.items():
        current = dict(starting[machine])
        gate = report["operator_review_gate"][machine]
        post_apply = (
            report.get("windows", {}).get(POST_APPLY_WINDOW_NAME, {}).get(machine, {})
        )
        summary = post_apply.get("summary") or {}
        cohort = post_apply.get("policy_cohort") or {}
        active_axes = [
            key
            for key in ("rolling_high_drawdown_pct", "rolling_low_proximity_pct")
            if key in current and current[key] != baseline[key]
        ]
        ev = _as_float(summary.get("notional_weighted_ev_pct"))
        net = _as_float(summary.get("broker_realized_net_profit_krw"))
        ready = bool(
            machine != "morning"
            and len(active_axes) == 1
            and binding.get("status") == "ready"
            and report.get("target_date_is_krx_trading_day") is True
            and report.get("source_quality_preflight", {}).get("tuning_input_allowed")
            is True
            and report.get("outcome_amendment_ledger", {}).get("status") == "pass"
            and gate.get("status")
            not in {
                "inventory_or_order_unresolved",
                "source_quality_blocked",
                "outcome_amendment_contract_blocked",
            }
            and post_apply.get("matches_source_date_applied_policy") is True
            and _same_machine_entry_policy(cohort, current)
            and bool(post_apply.get("applied_epoch_start"))
            and all(
                post_apply["applied_epoch_start"] <= day <= report["target_date"]
                for day in post_apply.get("observed_trading_dates", [])
            )
            and summary.get("completed_signal_episodes", 0)
            >= ROLLING_10D_MIN_COMPLETED_EPISODES
            and summary.get("broker_priced_completed_legs", 0)
            >= ROLLING_10D_MIN_COMPLETED_EPISODES
            and summary.get("broker_sell_fill_price_coverage") == 1.0
            and summary.get("held_legs", 0) == 0
            and summary.get("unresolved_legs", 0) == 0
            and ev is not None
            and net is not None
            and (ev <= 0.0 or net <= 0.0)
        )
        evidence = {
            "operator_review_gate": gate,
            "post_apply_version": post_apply,
            "optimization_owner": "machine_entry_timing_tuning",
            "subset_new_runtime_authority": False,
        }
        status = (
            "baseline_only_entry_timing_owns_confirmation"
            if machine == "morning"
            else "carry_forward_entry_timing_owns_confirmation"
        )
        if gate.get("status") in {
            "source_quality_blocked",
            "outcome_amendment_contract_blocked",
            "inventory_or_order_unresolved",
        }:
            status = f"carry_forward_{gate['status']}"
        if (
            active_axes
            and not ready
            and gate.get("status")
            not in {
                "source_quality_blocked",
                "outcome_amendment_contract_blocked",
                "inventory_or_order_unresolved",
            }
        ):
            status = (
                "carry_forward_legacy_axis_review_required"
                if summary.get("observation_day_count", 0) >= BOUNDED_MIN_OBSERVED_DAYS
                else "carry_forward_legacy_axis_post_apply_observation"
            )
        machines[machine] = {
            "selection_status": status,
            "selected_axis": None,
            "policy": current,
            "evidence": evidence,
            "evidence_digest": canonical_hash(evidence),
            "allowed_runtime_apply": True,
        }
        if ready:
            rollback_choices.append((float(ev), machine, active_axes[0]))
    if rollback_choices:
        _, machine, axis = min(rollback_choices)
        machines[machine]["policy"][axis] = BASELINE_POLICIES[machine][axis]
        machines[machine]["selected_axis"] = axis
        machines[machine][
            "selection_status"
        ] = "bounded_rollback_selected_negative_post_apply_ev"
    policies = {machine: item["policy"] for machine, item in machines.items()}
    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": report["target_date"],
        "generated_at_kst": report["generated_at_kst"],
        "source_report": REPORT_TYPE,
        "source_report_schema": report["schema"],
        "source_report_binding": {
            "schema": report["schema"],
            "target_date": report["target_date"],
            "sha256": report["artifact_hash"],
        },
        "source_runtime_policy_binding": binding,
        "runtime_optimization_owner": "machine_entry_timing_tuning",
        "clean_tuning_baseline_date": report["clean_tuning_baseline_date"],
        "source_quality_preflight": report.get("source_quality_preflight", {}),
        "policy_hash": policy_hash(policies),
        "policy_mutations": policy_mutations_between(
            starting, policies, include_kind=True
        ),
        "machines": machines,
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "rollback": {
            "trigger": "non_positive_actual_applied_epoch_ev_or_net_profit",
            "action": "restore_one_legacy_axis_toward_baseline_next_preopen",
            "floor": {
                "completed_signal_episodes": ROLLING_10D_MIN_COMPLETED_EPISODES,
                "broker_priced_completed_legs": ROLLING_10D_MIN_COMPLETED_EPISODES,
            },
        },
        "forbidden_uses": [
            "subset_only_new_tightening_authority",
            "unconsumed_candidate_as_applied_policy",
            "threshold_relaxation_beyond_baseline",
            "quantity_target_or_entry_validity_change",
            "stop_loss_or_forced_exit_creation",
            "same_day_intraday_runtime_mutation",
            "provider_bot_cap_or_broker_guard_change",
        ],
    }
    candidate["candidate_hash"] = candidate_artifact_hash(candidate)
    return candidate


def write_policy_candidate(
    report: dict[str, Any], candidate_dir: Path = CANDIDATE_DIR
) -> Path:
    candidate = build_policy_candidate(report)
    valid, reason = validate_candidate(candidate, source_report=report)
    if not valid:
        raise ValueError(f"generated_candidate_invalid:{reason}")
    path = candidate_dir / (
        f"samsung_machine_entry_policy_candidate_{report['target_date']}.json"
    )
    atomic_write_json(path, candidate)
    return path


def _load_prior_daily_rows(
    output_dir: Path, target_date: date, cost_pct: float
) -> tuple[
    dict[str, dict[str, dict[str, Any]]],
    list[dict[str, Any]],
    list[str],
]:
    by_date: dict[str, dict[str, dict[str, Any]]] = {}
    amendments_by_id: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for path in sorted(output_dir.glob(f"{REPORT_TYPE}_*.json")):
        filename_date = path.stem.removeprefix(f"{REPORT_TYPE}_")
        try:
            report_date = date.fromisoformat(filename_date)
        except ValueError:
            continue
        # A same-day rerun must retain the append-only outcome ledger even if
        # the mutable runtime state or receipt registry has since rotated.
        if not CLEAN_BASELINE_DATE <= report_date <= target_date:
            continue
        report_is_trading = is_krx_trading_day(report_date)
        payload = _read_json(path)
        if not payload:
            if report_is_trading:
                by_date[filename_date] = {
                    machine: _empty_machine_row(
                        machine, filename_date, "prior_report_missing_or_invalid_json"
                    )
                    for machine in MACHINE_FILES
                    if _machine_effective(machine, report_date)
                }
            continue
        try:
            payload_date = date.fromisoformat(str(payload.get("target_date") or ""))
            payload_cost = float(payload.get("cost_pct"))
        except (TypeError, ValueError):
            payload_date = None
            payload_cost = -1.0
        if (
            payload.get("report_type") != REPORT_TYPE
            or payload.get("schema") not in SUPPORTED_REPORT_SCHEMAS
            or payload_date != report_date
            or abs(payload_cost - cost_pct) > 1e-9
        ):
            if report_is_trading:
                by_date[filename_date] = {
                    machine: _empty_machine_row(
                        machine, filename_date, "prior_report_contract_mismatch"
                    )
                    for machine in MACHINE_FILES
                    if _machine_effective(machine, report_date)
                }
            continue
        if payload.get("schema") in HASHED_REPORT_SCHEMAS and payload.get(
            "artifact_hash"
        ) != report_artifact_hash(payload):
            issues.append(f"{filename_date}:prior_report_artifact_hash_invalid")
            if report_is_trading:
                by_date[filename_date] = {
                    machine: _empty_machine_row(
                        machine, filename_date, "prior_report_artifact_hash_invalid"
                    )
                    for machine in MACHINE_FILES
                    if _machine_effective(machine, report_date)
                }
            continue
        machines = payload.get("daily", {}).get("machines", {})
        if report_is_trading and isinstance(machines, dict):
            by_date[filename_date] = {
                machine: (
                    _normalize_historical_machine_row(machines[machine])
                    if isinstance(machines.get(machine), dict)
                    and _row_known_by_report_date(machines[machine], filename_date)
                    else _empty_machine_row(
                        machine, filename_date, "prior_report_machine_row_missing"
                    )
                )
                for machine in MACHINE_FILES
                if _machine_effective(machine, report_date)
            }
        elif report_is_trading:
            by_date[filename_date] = {
                machine: _empty_machine_row(
                    machine, filename_date, "prior_report_machine_map_invalid"
                )
                for machine in MACHINE_FILES
                if _machine_effective(machine, report_date)
            }
        ledger = payload.get("outcome_amendment_ledger")
        records = ledger.get("records") if isinstance(ledger, dict) else []
        if payload.get("schema") in HASHED_REPORT_SCHEMAS and (
            not isinstance(ledger, dict)
            or ledger.get("status") != "pass"
            or ledger.get("issues") != []
            or not isinstance(records, list)
            or ledger.get("record_count") != len(records or [])
            or ledger.get("records_sha256") != canonical_hash(records)
        ):
            issues.append(f"{filename_date}:outcome_amendment_ledger_hash_invalid")
            records = []
        if records is not None and not isinstance(records, list):
            issues.append(f"{filename_date}:outcome_amendment_records_invalid")
            records = []
        for record in records or []:
            valid, reason = _validate_outcome_amendment(record)
            if not valid:
                issues.append(f"{filename_date}:{reason}")
                continue
            if str(record["recorded_report_date"]) > filename_date:
                issues.append(f"{filename_date}:amendment_recorded_after_parent_report")
                continue
            amendments_by_id[str(record["amendment_id"])] = record
        legacy_reconciliations = (
            payload.get("prior_state_reconciliations")
            if payload.get("schema") not in HASHED_REPORT_SCHEMAS
            else None
        )
        if isinstance(legacy_reconciliations, dict):
            for machine, item in legacy_reconciliations.items():
                if machine not in MACHINE_FILES or not isinstance(item, dict):
                    continue
                row = item.get("row")
                source_date = str(item.get("source_date") or "")
                if not isinstance(row, dict) or not source_date:
                    continue
                amendment = _build_outcome_amendment(
                    machine=machine,
                    source_date=source_date,
                    recorded_report_date=filename_date,
                    row=row,
                    source_kind="legacy_prior_state_reconciliation",
                    source_ref=str(path),
                    source_sha256=file_sha256(path),
                )
                valid, reason = _validate_outcome_amendment(amendment)
                if not valid:
                    issues.append(f"{filename_date}:{reason}")
                    continue
                amendments_by_id[amendment["amendment_id"]] = amendment
    ordered_amendments = sorted(
        amendments_by_id.values(),
        key=lambda item: (
            str(item.get("recorded_report_date") or ""),
            str(item.get("source_date") or ""),
            str(item.get("machine") or ""),
            str(item.get("amendment_id") or ""),
        ),
    )
    applied_rank: dict[tuple[str, str], tuple[int, int, int, int, int]] = {}
    for amendment in ordered_amendments:
        source_date = str(amendment["source_date"])
        machine = str(amendment["machine"])
        row = _normalize_historical_machine_row(amendment["row"])
        rank = _outcome_resolution_rank(row)
        key = (source_date, machine)
        if key in applied_rank and rank < applied_rank[key]:
            continue
        by_date.setdefault(
            source_date,
            {
                item: _empty_machine_row(
                    item,
                    source_date,
                    "prior_report_missing_during_outcome_amendment",
                )
                for item in MACHINE_FILES
                if _machine_effective(item, date.fromisoformat(source_date))
            },
        )
        by_date[source_date][machine] = row
        applied_rank[key] = rank
    return by_date, ordered_amendments, sorted(set(issues))


def _upsert_outcome_amendment(
    history: dict[str, dict[str, dict[str, Any]]],
    amendments_by_id: dict[str, dict[str, Any]],
    amendment: dict[str, Any],
    issues: list[str],
) -> None:
    valid, reason = _validate_outcome_amendment(amendment)
    if not valid:
        issues.append(reason)
        return
    source_date = str(amendment["source_date"])
    machine = str(amendment["machine"])
    current = history.get(source_date, {}).get(machine)
    amended = _normalize_historical_machine_row(amendment["row"])
    if isinstance(current, dict) and _outcome_resolution_rank(amended) < (
        _outcome_resolution_rank(current)
    ):
        return
    amendments_by_id[str(amendment["amendment_id"])] = amendment
    history.setdefault(
        source_date,
        {
            item: _empty_machine_row(
                item, source_date, "outcome_amendment_without_base_daily_row"
            )
            for item in MACHINE_FILES
            if _machine_effective(item, date.fromisoformat(source_date))
        },
    )
    history[source_date][machine] = amended


def _apply_broker_receipt_amendments(
    history: dict[str, dict[str, dict[str, Any]]],
    *,
    target_date: str,
    cost_pct: float,
    receipt_registry_path: Path,
    amendments_by_id: dict[str, dict[str, Any]],
    issues: list[str],
) -> None:
    registry = _read_json(receipt_registry_path)
    if registry is None:
        return
    if registry.get("schema") != "episode_manual_exit_receipt_registry_v1":
        issues.append("manual_exit_receipt_registry_schema_invalid")
        return
    raw_receipts = registry.get("receipts")
    if not isinstance(raw_receipts, list):
        issues.append("manual_exit_receipt_registry_rows_invalid")
        return
    try:
        registry_sha256 = file_sha256(receipt_registry_path)
    except OSError:
        issues.append("manual_exit_receipt_registry_hash_unavailable")
        return
    for source_date, machines in history.items():
        for machine, row in machines.items():
            if machine not in MACHINE_FILES:
                continue
            owner_id = f"samsung_{machine}"
            matches = [
                item
                for item in raw_receipts
                if isinstance(item, dict)
                and item.get("owner_id") == owner_id
                and item.get("entry_trade_date") == source_date
                and item.get("symbol") == "005930"
                and item.get("status") == "applied"
                and _receipt_known_by_report_date(item, target_date)
            ]
            if not matches:
                continue
            held, unresolved = _effective_inventory_counts(row)
            if held or unresolved:
                resolved = _resolve_row_with_broker_receipts(
                    row, matches, cost_pct=cost_pct
                )
            elif _completed_manual_row_matches_receipts(row, matches):
                resolved = _normalize_historical_machine_row(row)
            else:
                continue
            if resolved is None:
                issues.append(
                    f"{source_date}:{machine}:manual_exit_receipt_allocation_invalid"
                )
                continue
            amendment = _build_outcome_amendment(
                machine=machine,
                source_date=source_date,
                recorded_report_date=target_date,
                row=resolved,
                source_kind="broker_verified_manual_exit_receipt_registry",
                source_ref=str(receipt_registry_path),
                source_sha256=registry_sha256,
            )
            _upsert_outcome_amendment(history, amendments_by_id, amendment, issues)


def _apply_source_only_custody_resolutions(
    history: dict[str, dict[str, dict[str, Any]]],
    *,
    target_date: str,
    reconciliation_dir: Path,
    amendments_by_id: dict[str, dict[str, Any]],
    issues: list[str],
) -> None:
    if not reconciliation_dir.exists():
        return
    for path in sorted(reconciliation_dir.glob("*.json")):
        payload = _read_json(path)
        if (
            payload is None
            or payload.get("schema") != "episode_manual_close_reconciliation_receipt_v1"
            or payload.get("authority") != "explicit_operator_manual_sale_confirmation"
            or payload.get("runtime_effect") != "owner_ledger_custody_close_only"
            or payload.get("broker_order_submitted") is not False
        ):
            continue
        recorded_at = payload.get("reconciled_at_kst") or payload.get(
            "generated_at_kst"
        )
        if not _known_by_report_date(recorded_at, target_date):
            continue
        targets = payload.get("targets")
        if not isinstance(targets, list):
            issues.append(f"{path.name}:manual_close_targets_invalid")
            continue
        for item in targets:
            if not isinstance(item, dict):
                continue
            owner = str(item.get("owner") or "")
            if not owner.startswith("samsung_"):
                continue
            machine = owner.removeprefix("samsung_")
            source_date = str(item.get("prior_trade_date") or "")
            row = history.get(source_date, {}).get(machine)
            if machine not in MACHINE_FILES or not isinstance(row, dict):
                continue
            held, unresolved = _effective_inventory_counts(row)
            if not (held or unresolved):
                continue
            held_quantity = sum(
                _as_int(leg.get("position_qty")) for leg in row.get("legs", [])
            )
            if (
                held_quantity <= 0
                or _as_int(item.get("reconciled_quantity")) != held_quantity
            ):
                issues.append(f"{path.name}:{machine}:manual_close_quantity_mismatch")
                continue
            resolved = deepcopy(row)
            resolved["custody_resolution"] = {
                "inventory_resolved": True,
                "economics_eligible": False,
                "reason": "operator_confirmed_close_without_unique_broker_owner_fill",
                "receipt_id": str(payload.get("receipt_id") or ""),
                "reconciled_quantity": _as_int(item.get("reconciled_quantity")),
            }
            resolved["eligible_for_cumulative_tuning"] = False
            resolved["source_quality"] = "gap"
            reasons = list(resolved.get("source_quality_reasons") or [])
            if "manual_close_unpriced_source_only" not in reasons:
                reasons.append("manual_close_unpriced_source_only")
            resolved["source_quality_reasons"] = reasons
            amendment = _build_outcome_amendment(
                machine=machine,
                source_date=source_date,
                recorded_report_date=target_date,
                row=resolved,
                source_kind="operator_custody_close_source_only",
                source_ref=str(path),
                source_sha256=file_sha256(path),
            )
            _upsert_outcome_amendment(history, amendments_by_id, amendment, issues)


def build_report(
    *,
    target_date: str,
    state_dir: Path,
    output_dir: Path,
    cost_pct: float,
    source_quality_dir: Path = SOURCE_QUALITY_DIR,
    applied_dir: Path = APPLIED_DIR,
    manual_exit_receipt_registry_path: Path = MANUAL_EXIT_RECEIPT_REGISTRY_PATH,
    manual_close_reconciliation_dir: Path = MANUAL_CLOSE_RECONCILIATION_DIR,
) -> dict[str, Any]:
    parsed_date = date.fromisoformat(target_date)
    expected_clean_dates = _clean_trading_dates_through(parsed_date)
    target_date_is_trading = is_krx_trading_day(parsed_date)
    if not math.isfinite(cost_pct) or not 0 <= cost_pct < 100:
        raise ValueError("cost_pct_must_be_finite_percentage")
    daily_machines: dict[str, dict[str, Any]] = {}
    prior_state_reconciliations: dict[str, dict[str, Any]] = {}
    for machine, filename in MACHINE_FILES.items():
        if not _machine_effective(machine, parsed_date):
            daily_machines[machine] = _pre_effective_machine_row(machine, target_date)
            continue
        state_path = state_dir / filename
        state = _read_json(state_path)
        raw_state_date = str((state or {}).get("trade_date") or "")
        try:
            state_date = date.fromisoformat(raw_state_date)
        except ValueError:
            state_date = None
        if (
            state_date is not None
            and CLEAN_BASELINE_DATE <= state_date < parsed_date
            and is_krx_trading_day(state_date)
        ):
            resolved_row = extract_machine_row(
                machine=machine,
                state_path=state_path,
                target_date=state_date.isoformat(),
                cost_pct=cost_pct,
                applied_dir=applied_dir,
            )
            original_preflight = _source_quality_preflight(
                state_date.isoformat(), source_quality_dir
            )
            if not original_preflight["tuning_input_allowed"]:
                resolved_row["eligible_for_cumulative_tuning"] = False
                resolved_row["source_quality"] = "gap"
                reasons = list(resolved_row.get("source_quality_reasons") or [])
                if "original_date_source_quality_audit_blocked" not in reasons:
                    reasons.append("original_date_source_quality_audit_blocked")
                resolved_row["source_quality_reasons"] = reasons
            prior_state_reconciliations[machine] = {
                "source_date": state_date.isoformat(),
                "state_status": resolved_row["state_status"],
                "row": resolved_row,
                "source_quality_preflight": original_preflight,
            }
            if not _row_known_by_report_date(
                resolved_row, target_date, require_exit_timestamp=True
            ):
                prior_state_reconciliations.pop(machine)
            daily_machines[machine] = _empty_machine_row(
                machine,
                target_date,
                "prior_episode_custody_no_current_date_episode",
            )
            continue
        daily_machines[machine] = extract_machine_row(
            machine=machine,
            state_path=state_path,
            target_date=target_date,
            cost_pct=cost_pct,
            applied_dir=applied_dir,
        )
        if not _row_known_by_report_date(daily_machines[machine], target_date):
            daily_machines[machine] = _empty_machine_row(
                machine, target_date, "durable_outcome_after_report_cutoff"
            )
    source_quality_preflight = _source_quality_preflight(
        target_date, source_quality_dir
    )
    if not source_quality_preflight["tuning_input_allowed"]:
        for row in daily_machines.values():
            if row.get("cohort") == "pre_effective_not_applicable":
                continue
            row["eligible_for_cumulative_tuning"] = False
            row["source_quality"] = "gap"
            reasons = list(row.get("source_quality_reasons") or [])
            if "observation_source_quality_audit_blocked" not in reasons:
                reasons.append("observation_source_quality_audit_blocked")
            row["source_quality_reasons"] = reasons
    history, prior_amendments, amendment_issues = _load_prior_daily_rows(
        output_dir, parsed_date, cost_pct
    )
    amendments_by_id = {str(item["amendment_id"]): item for item in prior_amendments}
    for machine, reconciliation in prior_state_reconciliations.items():
        source_date = reconciliation["source_date"]
        state_path = state_dir / MACHINE_FILES[machine]
        amendment = _build_outcome_amendment(
            machine=machine,
            source_date=source_date,
            recorded_report_date=target_date,
            row=reconciliation["row"],
            source_kind="durable_state_reconciliation",
            source_ref=str(state_path),
            source_sha256=file_sha256(state_path),
        )
        _upsert_outcome_amendment(
            history, amendments_by_id, amendment, amendment_issues
        )
    if target_date_is_trading:
        history[target_date] = daily_machines
    _apply_broker_receipt_amendments(
        history,
        target_date=target_date,
        cost_pct=cost_pct,
        receipt_registry_path=manual_exit_receipt_registry_path,
        amendments_by_id=amendments_by_id,
        issues=amendment_issues,
    )
    _apply_source_only_custody_resolutions(
        history,
        target_date=target_date,
        reconciliation_dir=manual_close_reconciliation_dir,
        amendments_by_id=amendments_by_id,
        issues=amendment_issues,
    )
    for day, machine_rows in history.items():
        for machine, row in list(machine_rows.items()):
            if not isinstance(row, dict):
                continue
            machine_rows[machine] = _attach_policy_cohort(row, machine, applied_dir)
        if day == target_date:
            daily_machines = machine_rows
    outcome_amendments = sorted(
        amendments_by_id.values(),
        key=lambda item: (
            str(item.get("recorded_report_date") or ""),
            str(item.get("source_date") or ""),
            str(item.get("machine") or ""),
            str(item.get("amendment_id") or ""),
        ),
    )
    ordered_dates = sorted(history)
    observed_date_set = {date.fromisoformat(item) for item in ordered_dates}
    unobserved_dates = [
        item.isoformat()
        for item in expected_clean_dates
        if item not in observed_date_set
    ]
    windows: dict[str, dict[str, Any]] = {
        CLEAN_WINDOW_NAME: {},
        **{name: {} for name in ROLLING_WINDOWS},
        POST_APPLY_WINDOW_NAME: {},
    }
    rolling_date_sets = {
        name: set(item.isoformat() for item in expected_clean_dates[-days:])
        for name, days in ROLLING_WINDOWS.items()
    }
    for machine in MACHINE_FILES:
        dated_rows = [(day, history[day].get(machine)) for day in ordered_dates]
        rows = [row for _, row in dated_rows]
        latest_policy_cohort_id = next(
            (
                str(row.get("policy_cohort_id") or "")
                for _, row in reversed(dated_rows)
                if isinstance(row, dict) and row.get("policy_cohort_id")
            ),
            "",
        )
        all_policy_cohort_rows = [
            row
            for row in rows
            if isinstance(row, dict)
            and row.get("cohort") != "pre_effective_not_applicable"
        ]
        clean_rows = [
            row
            for row in all_policy_cohort_rows
            if str(row.get("policy_cohort_id") or "") == latest_policy_cohort_id
        ]
        windows[CLEAN_WINDOW_NAME][machine] = {
            "policy_cohort_id": latest_policy_cohort_id,
            "summary": _aggregate_rows(clean_rows),
            "all_policy_cohorts_summary_audit_only": _aggregate_rows(
                all_policy_cohort_rows
            ),
            "entry_axis_observations": _axis_observations(clean_rows, machine),
        }
        for window_name, window_dates in rolling_date_sets.items():
            rolling_rows = [
                row
                for day, row in dated_rows
                if day in window_dates
                and isinstance(row, dict)
                and row.get("cohort") != "pre_effective_not_applicable"
                and str(row.get("policy_cohort_id") or "") == latest_policy_cohort_id
            ]
            windows[window_name][machine] = {
                "summary": _aggregate_rows(rolling_rows),
                "entry_axis_observations": _axis_observations(rolling_rows, machine),
                "expected_trading_dates": sorted(window_dates),
            }
        # An A -> B -> A policy sequence has two A apply epochs. Earlier A
        # economics may inform cumulative diagnostics but cannot roll back A2.
        post_apply_rows = []
        for observed_date in reversed(expected_clean_dates):
            row = history.get(observed_date.isoformat(), {}).get(machine)
            if (
                not isinstance(row, dict)
                or str(row.get("policy_cohort_id") or "") != latest_policy_cohort_id
            ):
                break
            post_apply_rows.append(row)
        post_apply_rows.reverse()
        current_row = _attach_policy_cohort(
            {"target_date": target_date, "attempted": False}, machine, applied_dir
        )
        current_cohort = current_row["policy_cohort"]
        current_reason = current_row["policy_cohort_status"]
        windows[POST_APPLY_WINDOW_NAME][machine] = {
            "policy_cohort_id": latest_policy_cohort_id,
            "policy_cohort": (
                post_apply_rows[-1].get("policy_cohort") if post_apply_rows else {}
            ),
            "summary": _aggregate_rows(post_apply_rows),
            "entry_axis_observations": _axis_observations(post_apply_rows, machine),
            "observed_trading_dates": [
                str(row.get("target_date") or "") for row in post_apply_rows
            ],
            "applied_epoch_start": (
                post_apply_rows[0]["target_date"] if post_apply_rows else None
            ),
            "matches_source_date_applied_policy": bool(
                current_reason == "ready"
                and current_cohort
                and latest_policy_cohort_id == canonical_hash(current_cohort)
            ),
        }
    review_gate: dict[str, dict[str, Any]] = {}
    for machine in MACHINE_FILES:
        clean_cumulative = windows[CLEAN_WINDOW_NAME][machine]["summary"]
        post_apply = windows[POST_APPLY_WINDOW_NAME][machine]["summary"]
        status = str(post_apply["candidate_status"])
        if daily_machines[machine].get("cohort") == "pre_effective_not_applicable":
            status = "not_effective"
        elif amendment_issues:
            status = "outcome_amendment_contract_blocked"
        elif post_apply["held_legs"] or post_apply["unresolved_legs"]:
            status = "inventory_or_order_unresolved"
        elif (
            not source_quality_preflight["tuning_input_allowed"]
            or daily_machines[machine].get("source_quality") != "pass"
        ):
            status = "source_quality_blocked"
        review_gate[machine] = {
            "status": status,
            "clean_baseline_completed_signal_episodes": clean_cumulative[
                "completed_signal_episodes"
            ],
            "clean_baseline_equal_weight_avg_profit_pct": clean_cumulative[
                "equal_weight_avg_profit_pct"
            ],
            "clean_baseline_notional_weighted_ev_pct": clean_cumulative[
                "notional_weighted_ev_pct"
            ],
            "post_apply_policy_cohort_id": windows[POST_APPLY_WINDOW_NAME][machine][
                "policy_cohort_id"
            ],
            "post_apply_completed_signal_episodes": post_apply[
                "completed_signal_episodes"
            ],
            "post_apply_broker_priced_completed_legs": post_apply[
                "broker_priced_completed_legs"
            ],
            "post_apply_held_legs": post_apply["held_legs"],
            "post_apply_unresolved_legs": post_apply["unresolved_legs"],
            "post_apply_notional_weighted_ev_pct": post_apply[
                "notional_weighted_ev_pct"
            ],
            "post_apply_broker_realized_net_profit_krw": post_apply[
                "broker_realized_net_profit_krw"
            ],
            "post_apply_expected_net_profit_krw_per_observation_day": post_apply[
                "expected_net_profit_krw_per_observation_day"
            ],
            "post_apply_signal_rate_per_observation_day": post_apply[
                "signal_rate_per_observation_day"
            ],
            "post_apply_avg_realized_holding_minutes": post_apply[
                "avg_realized_holding_minutes"
            ],
            "estimated_observation_days_to_sample_floor": post_apply[
                "estimated_observation_days_to_sample_floor"
            ],
            "rolling_10d_notional_weighted_ev_pct": windows["rolling_10d"][machine][
                "summary"
            ]["notional_weighted_ev_pct"],
            "rolling_20d_notional_weighted_ev_pct": windows["rolling_20d"][machine][
                "summary"
            ]["notional_weighted_ev_pct"],
            "broker_priced_completed_legs": clean_cumulative[
                "broker_priced_completed_legs"
            ],
            "allowed_runtime_apply": False,
            "condition_feasibility": {
                "optimization_owner": "machine_entry_timing_tuning",
                "subset_promotion_retired": True,
                "control_profit_state": (
                    "not_broker_realized"
                    if clean_cumulative["notional_weighted_ev_pct"] is None
                    else (
                        "positive"
                        if clean_cumulative["notional_weighted_ev_pct"] > 0
                        else "non_positive"
                    )
                ),
                "sample_floor_estimate": clean_cumulative[
                    "sample_floor_estimate_contract"
                ],
                "axes": [
                    {
                        "axis": item["axis"],
                        "status": (
                            "no_candidate_signal_observed"
                            if item["outcome"]["signal_attempts"] == 0
                            else (
                                "no_distinct_behavior_observed"
                                if item["outcome"].get("retained_signal_rate") == 1.0
                                else "diagnostic_only_causal_path_required"
                            )
                        ),
                    }
                    for item in windows[CLEAN_WINDOW_NAME][machine][
                        "entry_axis_observations"
                    ]
                ],
            },
        }
    report = {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "symbol": "005930",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "target_date_is_krx_trading_day": target_date_is_trading,
        "cost_pct": cost_pct,
        "metric_contract": METRIC_CONTRACT,
        "source_quality_preflight": source_quality_preflight,
        "source_runtime_policy_binding": _runtime_policy_binding(
            target_date, applied_dir
        ),
        "runtime_optimization_handoff": {
            "owner": "machine_entry_timing_tuning",
            "source_consumer": "machine_microstructure_attribution",
            "objective": "causal_rise_or_rebound_confirmation_ev_and_net_profit",
            "subset_new_runtime_authority": False,
            "required_evidence": "exact_route_causal_confirmation_and_paired_outcomes",
            "status": "existing_entry_timing_chain_owns_candidate_selection",
            "actual_order_submitted": False,
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "observes_actual_order_outcomes": True,
        "daily": {"machines": daily_machines},
        "prior_state_reconciliations": prior_state_reconciliations,
        "outcome_amendment_ledger": {
            "schema": "samsung_machine_outcome_amendment_ledger_v1",
            "status": "blocked" if amendment_issues else "pass",
            "issues": sorted(set(amendment_issues)),
            "record_count": len(outcome_amendments),
            "records_sha256": canonical_hash(outcome_amendments),
            "records": outcome_amendments,
        },
        "clean_baseline_window": {
            "start_date": CLEAN_BASELINE_DATE.isoformat(),
            "end_date": target_date,
            "expected_trading_date_count": len(expected_clean_dates),
            "available_actual_observation_dates": ordered_dates,
            "available_actual_observation_date_count": len(ordered_dates),
            "unobserved_trading_dates": unobserved_dates,
            "unobserved_trading_date_count": len(unobserved_dates),
            "unobserved_dates_block_candidate": False,
            "candidate_window_uses_only_available_actual_observations": True,
            "missing_dates_imputed_as_outcomes": False,
            "historical_market_replay_included": False,
        },
        "windows": windows,
        "operator_review_gate": review_gate,
        "decision": (
            "actual_machine_state_observation_collected_report_only; "
            "no_entry_threshold_or_runtime_change"
        ),
        "next_action": (
            "retain_actual_outcome_and_subset_diagnostics; "
            "causal_confirmation_optimization_owned_by_machine_entry_timing_tuning; "
            "subset_only_tightening_is_not_a_runtime_candidate; "
            "held_or_unresolved_inventory_requires_durable_resolution_before_candidate_readiness; "
            "negative_post_apply_version_ev_triggers_single_axis_bounded_rollback"
        ),
    }
    report["artifact_hash"] = report_artifact_hash(report)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Samsung machine entry tuning — {report['target_date']}",
        "",
        "- Decision: actual-state audit; causal rise/rebound optimization belongs to machine entry timing. No subset-only promotion or same-day runtime change.",
        "- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.",
        f"- Clean baseline: {report['clean_tuning_baseline_date']}",
        f"- Clean-baseline actual observations: {report['clean_baseline_window']['available_actual_observation_date_count']}/{report['clean_baseline_window']['expected_trading_date_count']} trading dates; missing dates are coverage only and are not imputed.",
        "- Decision windows use only the latest exact runtime-policy/target/quantity cohort; cross-version totals are audit-only.",
        f"- Outcome amendment ledger: {report['outcome_amendment_ledger']['status']} / {report['outcome_amendment_ledger']['record_count']} records.",
        "- Held/unresolved inventory in the latest exact cohort blocks candidate readiness; there is no stop-loss or forced exit.",
        "",
        "## Daily",
        "",
        "| Machine | Cohort | Source | Attempt | Status | Completed legs | Manual exits/losses | Held | Unresolved |",
        "|---|---|---|---:|---|---:|---:|---:|---:|",
    ]
    for machine, row in report["daily"]["machines"].items():
        summary = row["summary"]
        lines.append(
            f"| {machine} | {row['cohort']} | {row['source_quality']} | "
            f"{int(bool(row['attempted']))} | {row['state_status']} | "
            f"{summary['completed_legs']} | "
            f"{summary['manual_exit_completed_legs']}/"
            f"{summary['manual_exit_loss_legs']} | {summary['held_legs']} | "
            f"{summary['unresolved_legs']} |"
        )
    lines.extend(["", "## Cumulative decision", ""])
    for machine, gate in report["operator_review_gate"].items():
        lines.append(
            f"- {machine}: `{gate['status']}`; "
            f"complete episodes {gate['clean_baseline_completed_signal_episodes']}/{SAMPLE_FLOOR}, "
            f"clean-baseline cumulative equal-weight/weighted EV "
            f"{gate['clean_baseline_equal_weight_avg_profit_pct']}/"
            f"{gate['clean_baseline_notional_weighted_ev_pct']}; rolling10/20 "
            f"{gate['rolling_10d_notional_weighted_ev_pct']}/"
            f"{gate['rolling_20d_notional_weighted_ev_pct']}; broker-priced legs "
            f"{gate['broker_priced_completed_legs']}/{AUTO_MIN_COMPLETED_LEGS}; "
            f"post-apply net/day KRW {gate['post_apply_broker_realized_net_profit_krw']}/"
            f"{gate['post_apply_expected_net_profit_krw_per_observation_day']}; "
            f"signal rate {gate['post_apply_signal_rate_per_observation_day']}; "
            f"avg realized hold min {gate['post_apply_avg_realized_holding_minutes']}; "
            f"estimated days to floor {gate['estimated_observation_days_to_sample_floor']}."
        )
    lines.extend(
        [
            "",
            "Signal subsets are diagnostic only. New confirmation candidates require the entry-timing causal replay and apply contracts. Only an actually applied legacy tightening can be unwound here using exact-epoch evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    if report.get("artifact_hash") != report_artifact_hash(report):
        raise ValueError("report_artifact_hash_invalid")
    stem = f"{REPORT_TYPE}_{report['target_date']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(md_path, render_markdown(report))
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--state-dir", type=Path, default=DATA_DIR / "runtime")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR / "report" / REPORT_TYPE,
    )
    parser.add_argument("--candidate-dir", type=Path, default=CANDIDATE_DIR)
    parser.add_argument("--source-quality-dir", type=Path, default=SOURCE_QUALITY_DIR)
    parser.add_argument("--applied-policy-dir", type=Path, default=APPLIED_DIR)
    parser.add_argument("--cost-pct", type=float, default=0.20)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.cost_pct) or not 0 <= args.cost_pct < 100:
        parser.error("--cost-pct must be a finite percentage in [0, 100)")
    report = build_report(
        target_date=args.target_date,
        state_dir=args.state_dir,
        output_dir=args.output_dir,
        cost_pct=args.cost_pct,
        source_quality_dir=args.source_quality_dir,
        applied_dir=args.applied_policy_dir,
    )
    json_path, md_path = write_report(report, args.output_dir)
    candidate_path = write_policy_candidate(report, args.candidate_dir)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "report_type": REPORT_TYPE,
                    "target_date": args.target_date,
                    "json_path": str(json_path),
                    "markdown_path": str(md_path),
                    "candidate_path": str(candidate_path),
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
