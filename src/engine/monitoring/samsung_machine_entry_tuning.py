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
    candidate_policies_with_current_baselines,
    load_applied_machine_policy,
    policy_hash,
    validate_candidate,
)
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
REPORT_TYPE = "samsung_machine_entry_tuning"
REPORT_SCHEMA = "samsung_machine_entry_tuning_report_v7"
SUPPORTED_REPORT_SCHEMAS = frozenset(
    {
        "samsung_machine_entry_tuning_report_v2",
        "samsung_machine_entry_tuning_report_v3",
        "samsung_machine_entry_tuning_report_v4",
        "samsung_machine_entry_tuning_report_v5",
        "samsung_machine_entry_tuning_report_v6",
        REPORT_SCHEMA,
    }
)
CLEAN_BASELINE_DATE = date.fromisoformat("2026-06-05")
CLEAN_WINDOW_NAME = "clean_baseline_cumulative"
ROLLING_WINDOWS = {"rolling_10d": 10, "rolling_20d": 20}
SAMPLE_FLOOR = 20
AUTO_MIN_COMPLETED_LEGS = 20
MANUAL_EXIT_FILL_SOURCE = "broker_verified_manual_sell_receipt"
MANUAL_EXIT_PRICE_SOURCE = "broker_manual_sell_receipt"
APPLIED_POLICY_PROVENANCE_REQUIRED_DATE = date(2026, 8, 14)
SOURCE_QUALITY_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
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
        "clean_baseline_cumulative_completed_signal_episodes": SAMPLE_FLOOR,
        "clean_baseline_cumulative_completed_legs": AUTO_MIN_COMPLETED_LEGS,
        "broker_priced_completed_legs": AUTO_MIN_COMPLETED_LEGS,
    },
    "primary_decision_metric": [
        "completed_signal_episodes",
        "completed_legs_per_attempted_leg",
        "equal_weight_avg_profit_pct",
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
        "positive_rolling_10d_20d_and_cumulative_notional_ev",
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


def _source_quality_preflight(
    target_date: str, source_quality_dir: Path
) -> dict[str, Any]:
    path = source_quality_dir / f"observation_source_quality_audit_{target_date}.json"
    payload = _read_json(path)
    if payload is None:
        return {
            "status": "blocked",
            "tuning_input_allowed": False,
            "reason": "observation_source_quality_audit_missing_or_invalid",
            "source_path": str(path),
        }
    status = str(payload.get("status") or "").strip().lower()
    allowed = (payload.get("summary") or {}).get("tuning_input_allowed") is True
    passed = allowed and status in {"pass", "warning"}
    return {
        "status": "pass" if passed else "blocked",
        "tuning_input_allowed": passed,
        "reason": "ready" if passed else "observation_source_quality_audit_blocked",
        "source_path": str(path),
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
    }


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
                    leg.get("completed")
                    and net_profit is not None
                    and net_profit < 0.0
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
    return normalized


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
        or len(str(features.get("runtime_policy_hash") or "")) != 64
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
            and len(str(features.get("runtime_policy_hash") or "")) == 64
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


def _aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in rows if row.get("eligible_for_cumulative_tuning")]
    attempted = [row for row in eligible if row.get("attempted")]
    all_attempted = [row for row in rows if row.get("attempted")]
    summaries = [row.get("summary", {}) for row in attempted]
    all_summaries = [row.get("summary", {}) for row in all_attempted]
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
    held_legs = sum(_as_int(item.get("held_legs")) for item in all_summaries)
    unresolved_legs = sum(
        _as_int(item.get("unresolved_legs")) for item in all_summaries
    )
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
    if held_legs or unresolved_legs:
        candidate_status = "inventory_or_order_unresolved"
    elif complete_episodes < SAMPLE_FLOOR:
        candidate_status = "collect_sample"
    elif len(broker_priced_completed) < AUTO_MIN_COMPLETED_LEGS:
        candidate_status = "collect_broker_sell_fill_price"
    elif equal_weight_avg_profit_pct is None or equal_weight_avg_profit_pct <= 0:
        candidate_status = "hold_non_positive_ev"
    else:
        candidate_status = "operator_review_candidate"
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
            round(broker_completed_net_profit / attempted_notional * 100.0, 6)
            if attempted_notional > 0
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
        segments: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in attempted:
            features = row.get("signal_features", {})
            key = (
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
                "route": route,
                "required_drawdown_pct_by_route": json.loads(drawdown_policy),
                "outcome": _aggregate_rows(group),
                "interpretation": "current_policy_outcome_only_no_relaxation_counterfactual",
            }
            for (route, drawdown_policy), group in sorted(segments.items())
        ]

    if machine == "morning_reentry":
        return (
            [
                {
                    "axis": "fixed_user_approved_reentry_policy",
                    "outcome": _aggregate_rows(attempted),
                    "interpretation": (
                        "actual_outcome_observation_only_no_automatic_policy_mutation"
                    ),
                }
            ]
            if attempted
            else []
        )

    if not attempted:
        return []
    latest_features = attempted[-1].get("signal_features", {})
    current_drawdown = _as_float(latest_features.get("required_drawdown_pct"))
    current_near_low = _as_float(latest_features.get("max_near_low_pct"))
    if current_drawdown is None or current_near_low is None:
        return []
    current_cohort = [
        row
        for row in attempted
        if _as_float(row.get("signal_features", {}).get("required_drawdown_pct"))
        == current_drawdown
        and _as_float(row.get("signal_features", {}).get("max_near_low_pct"))
        == current_near_low
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
                "outcome": _aggregate_rows(matching),
                "interpretation": "tightening_subset_only_not_a_relaxation_backtest",
            }
        )
    return observations


def build_policy_candidate(
    report: dict[str, Any],
    *,
    prior_policies: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    machines: dict[str, dict[str, Any]] = {}
    starting_policies: dict[str, dict[str, Any]] = {}
    for machine, baseline in BASELINE_POLICIES.items():
        if machine == "morning":
            machines[machine] = {
                "selection_status": "baseline_only_no_observed_alternative",
                "selected_axis": "current_route_drawdown_policy",
                "policy": dict(baseline),
                "evidence": report["operator_review_gate"][machine],
                "allowed_runtime_apply": True,
            }
            starting_policies[machine] = dict(baseline)
            continue
        clean_window_axes = {
            item["axis"]: item
            for item in report["windows"][CLEAN_WINDOW_NAME][machine][
                "entry_axis_observations"
            ]
        }
        rolling_window_axes = {
            window_name: {
                item["axis"]: item
                for item in report["windows"][window_name][machine][
                    "entry_axis_observations"
                ]
            }
            for window_name in ROLLING_WINDOWS
        }
        current_policy = dict((prior_policies or {}).get(machine, baseline))
        starting_policies[machine] = dict(current_policy)
        eligible: list[tuple[float, str, dict[str, Any]]] = []
        machine_gate_ready = (
            report.get("target_date_is_krx_trading_day") is True
            and report["operator_review_gate"][machine]["status"]
            == "operator_review_candidate"
            and report.get("source_quality_preflight", {}).get("tuning_input_allowed")
            is True
        )
        axis_items = clean_window_axes.items() if machine_gate_ready else ()
        for axis, item in axis_items:
            outcome = item["outcome"]
            resulting_policy = item["resulting_policy"]
            if float(resulting_policy["rolling_high_drawdown_pct"]) < float(
                current_policy["rolling_high_drawdown_pct"]
            ) or float(resulting_policy["rolling_low_proximity_pct"]) > float(
                current_policy["rolling_low_proximity_pct"]
            ):
                continue
            changed_axes = [
                key
                for key in (
                    "rolling_high_drawdown_pct",
                    "rolling_low_proximity_pct",
                )
                if float(resulting_policy[key]) != float(current_policy[key])
            ]
            if len(changed_axes) > 1:
                continue
            if outcome.get("candidate_status") != "operator_review_candidate":
                continue
            if outcome.get("completed_legs", 0) < AUTO_MIN_COMPLETED_LEGS:
                continue
            if outcome.get("broker_priced_completed_legs", 0) < AUTO_MIN_COMPLETED_LEGS:
                continue
            ev = outcome.get("notional_weighted_ev_pct")
            rolling_outcomes = {
                window_name: (axes.get(axis) or {}).get("outcome")
                for window_name, axes in rolling_window_axes.items()
            }
            rolling_positive = all(
                isinstance(window_outcome, dict)
                and window_outcome.get("notional_weighted_ev_pct") is not None
                and float(window_outcome["notional_weighted_ev_pct"]) > 0
                for window_outcome in rolling_outcomes.values()
            )
            if ev is not None and float(ev) > 0 and rolling_positive:
                item = dict(item)
                item["rolling_outcomes"] = rolling_outcomes
                eligible.append((float(ev), axis, item))
        if eligible:
            selection_ev, selected_axis, selected = max(
                eligible,
                key=lambda item: (
                    item[0],
                    item[2]["resulting_policy"] == item[2]["current_policy_cohort"],
                ),
            )
            current_policy.update(selected["resulting_policy"])
            selection_status = (
                "carry_forward_current_policy_best_ev"
                if selected["resulting_policy"] == selected["current_policy_cohort"]
                else "bounded_tightening_selected"
            )
            evidence = {
                CLEAN_WINDOW_NAME: selected["outcome"],
                **selected["rolling_outcomes"],
            }
        else:
            selection_ev = None
            selected_axis = None
            selection_status = "carry_forward_current_policy_insufficient_evidence"
            evidence = report["operator_review_gate"][machine]
        machines[machine] = {
            "selection_status": selection_status,
            "selected_axis": selected_axis,
            "policy": current_policy,
            "evidence": evidence,
            "allowed_runtime_apply": True,
            "selection_ev": selection_ev,
        }
    requested_mutations: list[dict[str, Any]] = []
    for machine in ("midday", "afternoon"):
        before = starting_policies[machine]
        after = machines[machine]["policy"]
        changed = [key for key in before if after[key] != before[key]]
        if len(changed) > 1:
            raise ValueError("same_stage_multiple_axis_candidate_forbidden")
        if changed:
            key = changed[0]
            requested_mutations.append(
                {
                    "machine": machine,
                    "axis": key,
                    "before": before[key],
                    "after": after[key],
                    "selection_ev": machines[machine]["selection_ev"],
                }
            )
    if len(requested_mutations) > 1:
        winner = max(
            requested_mutations,
            key=lambda item: float(item["selection_ev"] or float("-inf")),
        )
        for mutation in requested_mutations:
            if mutation is winner:
                continue
            machine = mutation["machine"]
            machines[machine]["policy"] = dict(starting_policies[machine])
            machines[machine][
                "selection_status"
            ] = "carry_forward_same_stage_single_axis_guard"
        requested_mutations = [winner]
    for item in machines.values():
        item.pop("selection_ev", None)
    policy_mutations = [
        {key: value for key, value in item.items() if key != "selection_ev"}
        for item in requested_mutations
    ]
    policies = {machine: item["policy"] for machine, item in machines.items()}
    return {
        "schema": CANDIDATE_SCHEMA,
        "source_date": report["target_date"],
        "generated_at_kst": report["generated_at_kst"],
        "source_report": REPORT_TYPE,
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": report["clean_tuning_baseline_date"],
        "source_quality_preflight": report.get("source_quality_preflight", {}),
        "policy_hash": policy_hash(policies),
        "policy_mutations": policy_mutations,
        "machines": machines,
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "rollback": "next_preopen_exact_date_artifact_or_verified_baseline",
        "forbidden_uses": [
            "threshold_relaxation_below_baseline",
            "quantity_target_or_entry_validity_change",
            "stop_loss_or_forced_exit_creation",
            "same_day_intraday_runtime_mutation",
            "provider_bot_cap_or_broker_guard_change",
        ],
    }


def write_policy_candidate(
    report: dict[str, Any], candidate_dir: Path = CANDIDATE_DIR
) -> Path:
    prior_policies: dict[str, dict[str, Any]] | None = None
    prior_paths = sorted(
        candidate_dir.glob("samsung_machine_entry_policy_candidate_*.json"),
        reverse=True,
    )
    for prior_path in prior_paths:
        prior = _read_json(prior_path)
        if prior and str(prior.get("source_date") or "") >= report["target_date"]:
            continue
        if not prior:
            raise ValueError("latest_prior_candidate_unreadable")
        valid, _ = validate_candidate(prior)
        if not valid:
            raise ValueError("latest_prior_candidate_invalid")
        prior_policies = candidate_policies_with_current_baselines(prior)
        break
    candidate = build_policy_candidate(report, prior_policies=prior_policies)
    path = candidate_dir / (
        f"samsung_machine_entry_policy_candidate_{report['target_date']}.json"
    )
    atomic_write_json(path, candidate)
    return path


def _load_prior_daily_rows(
    output_dir: Path, target_date: date, cost_pct: float
) -> dict[str, dict[str, dict[str, Any]]]:
    by_date: dict[str, dict[str, dict[str, Any]]] = {}
    for path in sorted(output_dir.glob(f"{REPORT_TYPE}_*.json")):
        filename_date = path.stem.removeprefix(f"{REPORT_TYPE}_")
        try:
            report_date = date.fromisoformat(filename_date)
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= report_date < target_date:
            continue
        if not is_krx_trading_day(report_date):
            continue
        payload = _read_json(path)
        if not payload:
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
            by_date[filename_date] = {
                machine: _empty_machine_row(
                    machine, filename_date, "prior_report_contract_mismatch"
                )
                for machine in MACHINE_FILES
                if _machine_effective(machine, report_date)
            }
            continue
        machines = payload.get("daily", {}).get("machines", {})
        if isinstance(machines, dict):
            by_date[filename_date] = {
                machine: (
                    _normalize_historical_machine_row(machines[machine])
                    if isinstance(machines.get(machine), dict)
                    else _empty_machine_row(
                        machine, filename_date, "prior_report_machine_row_missing"
                    )
                )
                for machine in MACHINE_FILES
                if _machine_effective(machine, report_date)
            }
        else:
            by_date[filename_date] = {
                machine: _empty_machine_row(
                    machine, filename_date, "prior_report_machine_map_invalid"
                )
                for machine in MACHINE_FILES
                if _machine_effective(machine, report_date)
            }
    return by_date


def build_report(
    *,
    target_date: str,
    state_dir: Path,
    output_dir: Path,
    cost_pct: float,
    source_quality_dir: Path = SOURCE_QUALITY_DIR,
    applied_dir: Path = APPLIED_DIR,
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
    history = _load_prior_daily_rows(output_dir, parsed_date, cost_pct)
    for machine, reconciliation in prior_state_reconciliations.items():
        source_date = reconciliation["source_date"]
        history.setdefault(
            source_date,
            {
                item: _empty_machine_row(
                    item,
                    source_date,
                    "prior_report_missing_during_state_reconciliation",
                )
                for item in MACHINE_FILES
                if _machine_effective(item, date.fromisoformat(source_date))
            },
        )
        history[source_date][machine] = reconciliation["row"]
    if target_date_is_trading:
        history[target_date] = daily_machines
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
    }
    rolling_date_sets = {
        name: set(item.isoformat() for item in expected_clean_dates[-days:])
        for name, days in ROLLING_WINDOWS.items()
    }
    for machine in MACHINE_FILES:
        dated_rows = [(day, history[day].get(machine)) for day in ordered_dates]
        rows = [row for _, row in dated_rows]
        clean_rows = [
            row
            for row in rows
            if isinstance(row, dict)
            and row.get("cohort") != "pre_effective_not_applicable"
        ]
        windows[CLEAN_WINDOW_NAME][machine] = {
            "summary": _aggregate_rows(clean_rows),
            "entry_axis_observations": _axis_observations(clean_rows, machine),
        }
        for window_name, window_dates in rolling_date_sets.items():
            rolling_rows = [
                row
                for day, row in dated_rows
                if day in window_dates
                and isinstance(row, dict)
                and row.get("cohort") != "pre_effective_not_applicable"
            ]
            windows[window_name][machine] = {
                "summary": _aggregate_rows(rolling_rows),
                "entry_axis_observations": _axis_observations(rolling_rows, machine),
                "expected_trading_dates": sorted(window_dates),
            }
    review_gate: dict[str, dict[str, Any]] = {}
    for machine in MACHINE_FILES:
        clean_cumulative = windows[CLEAN_WINDOW_NAME][machine]["summary"]
        status = str(clean_cumulative["candidate_status"])
        if daily_machines[machine].get("cohort") == "pre_effective_not_applicable":
            status = "not_effective"
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
        }
    return {
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
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "observes_actual_order_outcomes": True,
        "daily": {"machines": daily_machines},
        "prior_state_reconciliations": prior_state_reconciliations,
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
            "collect_clean_two_leg_episodes_until_auto_apply_floors; "
            "require_positive_rolling_10d_20d_and_cumulative_broker_priced_ev; "
            "eligible_tightening_is_materialized_only_for_next_preopen; "
            "held_or_unresolved_inventory_must_close_naturally_before_candidate_readiness"
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Samsung machine entry tuning — {report['target_date']}",
        "",
        "- Decision: actual-state observation plus a bounded next-PREOPEN candidate; no same-day runtime change.",
        "- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.",
        f"- Clean baseline: {report['clean_tuning_baseline_date']}",
        f"- Clean-baseline actual observations: {report['clean_baseline_window']['available_actual_observation_date_count']}/{report['clean_baseline_window']['expected_trading_date_count']} trading dates; missing dates are coverage only and are not imputed.",
        "- Held/unresolved inventory blocks candidate readiness; there is no stop-loss or forced exit.",
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
            f"{gate['broker_priced_completed_legs']}/{AUTO_MIN_COMPLETED_LEGS}."
        )
    lines.extend(
        [
            "",
            "Only source-quality-passed tightening subsets may enter the next-PREOPEN candidate. Relaxation, alternate cancel windows, and price-touch fill assumptions are not evaluated.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
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
