"""Postclose actual-outcome tuning for each lower-price two-leg profile.

This producer reads durable profile states, its own prior reports, and exact
realized-cost account rows for uniquely attributable completed episodes. It
never queries market-price history. Observed-signal subsets remain diagnostics.
Actual-qualified profiles reuse cached replay and registered unused windows;
only native execution, daily capital and family authority can select a change.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import statistics
import tempfile
import time
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from src.engine.monitoring.machine_microstructure_attribution import (
    OUTPUT_DIR as MACHINE_MICROSTRUCTURE_REPORT_DIR,
    load_prior_owner_diagnostic,
)
from src.trading.low_price_two_leg.economics import (
    ROUND_TRIP_COST_PCT,
    cost_contract as canonical_cost_contract,
)
from src.trading.low_price_two_leg.machine import DEFAULT_STATE_DIR
from src.trading.low_price_two_leg.policy_runtime import (
    APPLIED_DIR,
    CANDIDATE_DIR,
    CANDIDATE_SCHEMA,
    PAIRED_CANDIDATE_SCHEMA,
    PAIRED_AUTHORITY_CONTRACT,
    next_policy_date,
    paired_promotion_ready,
    paired_capital_confirmation,
    atomic_write_json,
    baseline_policies_for_target_date,
    load_applied_profile_policy,
    policy_hash,
    report_artifact_hash,
    runtime_policy_binding,
    SUBSET_AUTHORITY_CONTRACT,
    policy_bounds_for_target_date,
    policy_mutations_between,
    validate_candidate,
)
from src.trading.low_price_two_leg.profiles import PROFILES, profiles_for_target_date
from src.trading.order.episode_quantity import SUPPORTED_OWNED_LEG_QUANTITIES
from src.trading.order.regular_two_leg_machine import KST
from src.trading.order.tick_utils import move_price_by_ticks
from src.trading.order.samsung_entry_policy import (
    CANDIDATE_DIR as SAMSUNG_CANDIDATE_DIR,
)
from src.trading.order.samsung_entry_policy import (
    validate_candidate as validate_samsung_candidate,
)
from src.utils.constants import DATA_DIR
from src.utils import kiwoom_utils
from src.utils.market_day import is_krx_trading_day

REPORT_TYPE = "low_price_two_leg_tuning"
REPORT_SCHEMA = "low_price_two_leg_tuning_report_v10"
SUPPORTED_REPORT_SCHEMAS = frozenset(
    {
        "low_price_two_leg_tuning_report_v9",
        "low_price_two_leg_tuning_report_v1",
        "low_price_two_leg_tuning_report_v2",
        "low_price_two_leg_tuning_report_v3",
        "low_price_two_leg_tuning_report_v4",
        "low_price_two_leg_tuning_report_v5",
        "low_price_two_leg_tuning_report_v6",
        "low_price_two_leg_tuning_report_v7",
        "low_price_two_leg_tuning_report_v8",
        REPORT_SCHEMA,
    }
)
DEFAULT_ROUND_TRIP_COST_PCT = ROUND_TRIP_COST_PCT
MANUAL_EXIT_FILL_SOURCE = "broker_verified_manual_sell_receipt"
MANUAL_EXIT_PRICE_SOURCE = "broker_manual_sell_receipt"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
CLEAN_WINDOW_NAME = "clean_baseline_cumulative"
CURRENT_WINDOW_NAME = "current_policy_cohort"
POST_APPLY_WINDOW_NAME = "post_apply_version"
BOUNDED_MIN_OBSERVED_DAYS = 5
SAMPLE_FLOOR_COMPLETED_LEGS = 8
MIN_NOTIONAL_EV_UPLIFT_PCT = 0.005
APPLIED_POLICY_PROVENANCE_REQUIRED_DATE = date(2026, 8, 14)
SOURCE_QUALITY_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
OUTPUT_DIR = DATA_DIR / "report" / REPORT_TYPE
PROFILE_FIRST_OPERATIONAL_DATES = {
    "lotte_chemical_midday": date(2026, 9, 11),
    "lx_semicon_morning": date(2026, 9, 11),
    "lotte_chemical_morning": date(2026, 9, 10),
    "lotte_chemical_afternoon": date(2026, 9, 10),
    "tym_late_morning": date(2026, 9, 10),
    "nhn_midday": date(2026, 9, 8),
    "tym_morning": date(2026, 9, 8),
    "sd_biosensor_afternoon": date(2026, 9, 8),
    "samsung_heavy_midday": date(2026, 8, 12),
    "samsung_heavy_afternoon": date(2026, 8, 12),
    "sk_eternix_midday": date(2026, 8, 12),
    "mirae_asset_morning": date(2026, 8, 13),
    "jeju_semiconductor_morning": date(2026, 8, 13),
    "doosan_enerbility_morning": date(2026, 8, 13),
    "hanwha_ocean_late_morning": date(2026, 8, 13),
    "kakao_morning": date(2026, 8, 13),
    "kakao_late_morning": date(2026, 8, 13),
    "sk_eternix_morning": date(2026, 8, 13),
    "sk_eternix_afternoon": date(2026, 8, 13),
    "mirae_asset_midday": date(2026, 8, 13),
    "kepco_afternoon": date(2026, 8, 13),
    "samsung_heavy_morning": date(2026, 8, 19),
    "doosan_enerbility_late_morning": date(2026, 8, 19),
    "kakao_midday": date(2026, 8, 19),
    "sk_telecom_afternoon": date(2026, 8, 19),
    "samsung_ea_morning": date(2026, 8, 19),
    "samsung_ea_late_morning": date(2026, 8, 19),
    "samsung_ea_afternoon": date(2026, 8, 19),
    "sk_telecom_late_morning": date(2026, 8, 21),
    "hanse_morning": date(2026, 8, 21),
    "hanse_afternoon": date(2026, 8, 21),
    "cj_cgv_midday": date(2026, 8, 21),
    "cj_cgv_afternoon": date(2026, 8, 21),
    "tym_midday": date(2026, 8, 21),
    "tym_afternoon": date(2026, 8, 21),
    "cj_cgv_late_morning": date(2026, 8, 24),
    "kepco_late_morning": date(2026, 8, 24),
    "kepco_midday": date(2026, 8, 24),
    "hanse_late_morning": date(2026, 8, 24),
    "hanse_midday": date(2026, 8, 24),
    "nhn_afternoon": date(2026, 8, 24),
    "youngone_morning": date(2026, 8, 24),
    "youngone_afternoon": date(2026, 8, 24),
    "sk_eternix_late_morning": date(2026, 8, 25),
    "mirae_asset_late_morning": date(2026, 8, 25),
    "kepco_morning": date(2026, 8, 25),
    "nhn_morning": date(2026, 8, 25),
    "nhn_late_morning": date(2026, 8, 25),
    "sd_biosensor_morning": date(2026, 8, 27),
    "sd_biosensor_late_morning": date(2026, 8, 27),
    "sd_biosensor_midday": date(2026, 8, 27),
    "doosan_enerbility_afternoon": date(2026, 8, 27),
    "samsung_ea_midday": date(2026, 8, 27),
    "sk_telecom_morning": date(2026, 8, 28),
    "fan_ocean_morning": date(2026, 8, 31),
    "fan_ocean_late_morning": date(2026, 8, 31),
    "samsung_heavy_late_morning": date(2026, 9, 7),
    "cj_cgv_morning": date(2026, 9, 7),
    "fan_ocean_afternoon": date(2026, 9, 7),
    "youngone_midday": date(2026, 9, 7),
    "sk_telecom_midday": date(2026, 9, 7),
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
    "metric_role": "low_price_two_leg_profile_entry_tuning_observation",
    "decision_authority": "postclose_bounded_candidate_only",
    "window_policy": (
        "profile_separated_daily_and_all_available_actual_observations_since_clean_baseline"
    ),
    "sample_floor": {
        "candidate_observed_trading_days": BOUNDED_MIN_OBSERVED_DAYS,
        "clean_baseline_cumulative_completed_legs": SAMPLE_FLOOR_COMPLETED_LEGS,
        "broker_priced_completed_legs": SAMPLE_FLOOR_COMPLETED_LEGS,
        "minimum_notional_ev_uplift_pct": MIN_NOTIONAL_EV_UPLIFT_PCT,
    },
    "primary_decision_metric": (
        "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
    ),
    "secondary_decision_metrics": [
        "notional_weighted_ev_pct",
        "attempted_episodes_per_source_valid_observation_day",
        "broker_completed_net_return_per_capital_hour",
    ],
    "profit_cost_model": (
        "ka10073_exact_cost_when_uniquely_attributable_else_"
        "broker_exit_fill_price_minus_fixed_round_trip_cost_pct_including_"
        "verified_manual_operator_losses"
    ),
    "lifecycle_speed_diagnostics": {
        "metric_role": "diagnostic_execution_velocity_and_capital_occupancy",
        "decision_authority": "postclose_diagnostic_only",
        "window_policy": (
            "per_completed_broker_leg_buy_fill_to_exit_with_machine_target_speed_"
            "reported_separately_from_manual_operator_exit"
        ),
        "sample_floor": "one_completed_leg_with_ordered_aware_fill_timestamps",
        "primary_decision_metric": "broker_completed_net_return_per_capital_hour",
        "primary_decision_metric_unit": (
            "realized_profit_krw_per_capital_occupied_krw_hour"
        ),
        "source_quality_gate": (
            "broker_receipt_terminal_leg_and_ordered_aware_fill_timestamps"
        ),
        "forbidden_uses": [
            "missing_timestamp_as_zero_latency",
            "gross_or_speed_metric_as_policy_selection_authority",
            "target_validity_quantity_stop_or_forced_exit_mutation",
        ],
        "gross_no_slippage_role": "diagnostic_only_not_live_promotion_authority",
        "fields": [
            "buy_filled_at",
            "target_filled_at",
            "holding_duration_sec",
            "gross_no_slippage_return_pct",
            "median_reconciliation_confirmed_holding_duration_sec",
            "target_reconciliation_completion_within_180s_ratio",
            "manual_exit_completed_legs",
            "manual_exit_loss_legs",
            "manual_exit_fixed_cost_estimate_net_profit_krw",
            "broker_completed_capital_occupied_krw_seconds",
            "broker_completed_net_return_per_capital_hour",
        ],
        "missing_timestamp_policy": "unknown_not_zero_or_instant_fill",
        "timestamp_provenance": (
            "broker_execution_reconciliation_observed_at_not_exchange_fill_time"
        ),
    },
    "source_quality_gate": [
        "target_date_profile_state_match",
        "actual_broker_receipt_terminal_leg_contract",
        "profile_specific_no_cross_symbol_pooling",
        "existing_samsung_regular_entry_same_stage_owner_guard",
        "held_or_unresolved_inventory_blocks_tightening",
        "observation_source_quality_audit_tuning_input_allowed",
        "target_date_krx_trading_day_for_candidate",
        "pre_operational_profile_rows_are_not_source_gaps",
        "prebaseline_and_nontrading_reports_excluded",
        "historical_replay_not_mixed_with_actual_outcomes",
        "ka10073_symbol_day_quantity_and_average_price_unique_match",
        "verified_manual_operator_exit_is_realized_pnl_not_machine_target_success",
        "candidate_improves_same_profile_current_policy_cost_adjusted_ev",
        "candidate_improves_same_profile_cost_adjusted_net_profit_per_day",
    ],
    "forbidden_uses": [
        "historical_market_data_requery",
        "price_touch_as_fill",
        "cross_profile_outcome_pooling",
        "same_day_or_intraday_runtime_mutation",
        "more_than_one_profile_or_axis_mutation_per_day",
        "threshold_relaxation",
        "quantity_target_entry_validity_stop_or_forced_exit_change",
        "gross_no_slippage_or_speed_diagnostic_as_standalone_policy_authority",
        "manual_operator_exit_as_machine_target_fill_or_target_speed_success",
        "provider_bot_cap_or_broker_guard_change",
    ],
}

RealizedPnlLoader = Callable[[str, str], list[dict[str, Any]]]


def _clean_trading_dates_through(target_date: date) -> tuple[date, ...]:
    if target_date < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_precedes_clean_baseline")
    selected: list[date] = []
    current = CLEAN_BASELINE_DATE
    while current <= target_date:
        if is_krx_trading_day(current):
            selected.append(current)
        current += timedelta(days=1)
    return tuple(selected)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


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


def _aware_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _source_quality_preflight(target_date: str, source_quality_dir: Path) -> dict:
    from src.engine.automation.source_quality_hard_gate import load_source_quality_preflight
    path = source_quality_dir / f"observation_source_quality_audit_{target_date}.json"
    gate = load_source_quality_preflight(target_date, artifact_path=path,
        require_final=target_date >= "2026-09-17")
    role_valid = (_read_json(path) or {}).get("report_type") == "observation_source_quality_audit"
    passed = role_valid and gate.get("tuning_input_allowed") is True and not gate.get("validation_errors")
    return {"status": "pass" if passed else "blocked", "tuning_input_allowed": passed,
        "reason": "ready" if passed else "observation_source_quality_audit_blocked",
        "source_path": str(path), "source_sha256": gate.get("artifact_sha256") or "",
        "audit_status": gate.get("status"), "audit_phase": gate.get("audit_phase"),
        "validation_errors": gate.get("validation_errors") or []}


def _empty_row(profile_id: str, target_date: str, reason: str) -> dict:
    return {
        "profile_id": profile_id,
        "symbol": PROFILES[profile_id].symbol if profile_id in PROFILES else "",
        "session": PROFILES[profile_id].session if profile_id in PROFILES else "",
        "target_date": target_date,
        "source_quality": "gap",
        "source_quality_reasons": [reason],
        "eligible_for_tuning": False,
        "attempted": False,
        "no_signal": False,
        "state_status": "UNKNOWN",
        "signal_features": {},
        "legs": [],
    }


def _pre_operational_row(profile_id: str, target_date: str) -> dict:
    row = _empty_row(profile_id, target_date, "profile_not_yet_operational")
    row.update(
        {
            "cohort": "pre_operational_not_applicable",
            "source_quality": "not_applicable",
            "source_quality_reasons": [],
            "state_status": "NOT_OPERATIONAL",
        }
    )
    return row


def _profile_was_operational(profile_id: str, target_date: date) -> bool:
    if profile_id.startswith("auto_"):
        return profile_id in _effective_report_profiles(target_date)
    return target_date >= PROFILE_FIRST_OPERATIONAL_DATES[profile_id]


def _signed_number(value: Any) -> float | None:
    text = str(value or "").replace(",", "").replace("+", "").strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def load_realized_pnl_ka10073(
    token: str, trade_date: str, symbol: str
) -> list[dict[str, Any]]:
    """Read normalized symbol-day realized PnL from the official ka10073 API."""

    parsed_date = date.fromisoformat(trade_date)
    normalized_symbol = str(symbol or "").strip().removeprefix("A")
    if len(normalized_symbol) != 6 or not normalized_symbol.isdigit():
        raise ValueError("ka10073_symbol_must_be_six_digits")
    api_date = parsed_date.strftime("%Y%m%d")
    responses = kiwoom_utils.fetch_kiwoom_api_continuous(
        url=kiwoom_utils.get_api_url("/api/dostk/acnt"),
        token=token,
        api_id="ka10073",
        payload={
            "stk_cd": normalized_symbol,
            "strt_dt": api_date,
            "end_dt": api_date,
        },
        use_continuous=True,
        request_owner="low_price_two_leg_tuning.realized_pnl",
        request_class="source_only",
        request_code=normalized_symbol,
    )
    normalized: list[dict[str, Any]] = []
    for response in responses or []:
        if not isinstance(response, dict):
            continue
        response_code = str(response.get("return_code", response.get("rt_cd", "0")))
        if response_code != "0":
            raise RuntimeError(f"ka10073_response_rejected:{response_code}")
        for raw in response.get("dt_stk_rlzt_pl", []) or []:
            if not isinstance(raw, dict):
                continue
            raw_symbol = str(raw.get("stk_cd") or "").strip().removeprefix("A")
            raw_date = str(raw.get("dt") or "").strip().replace("-", "")
            if raw_symbol != normalized_symbol or raw_date != api_date:
                continue
            normalized.append(
                {
                    "trade_date": trade_date,
                    "symbol": normalized_symbol,
                    "filled_qty": _signed_number(raw.get("cntr_qty")),
                    "buy_average_price": _signed_number(raw.get("buy_uv")),
                    "sell_average_price": _signed_number(raw.get("cntr_pric")),
                    "realized_net_profit_krw": _signed_number(raw.get("tdy_sel_pl")),
                    "broker_profit_rate_pct": _signed_number(raw.get("pl_rt")),
                    "commission_krw": _signed_number(raw.get("tdy_trde_cmsn")),
                    "tax_krw": _signed_number(raw.get("tdy_trde_tax")),
                    "source_api": "ka10073",
                }
            )
    return normalized


def _completed_broker_legs(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        leg
        for leg in row.get("legs", [])
        if leg.get("completed")
        and leg.get("profit_price_source")
        in {"broker_target_fill_price", "broker_manual_sell_receipt"}
        and _as_float(leg.get("net_profit_pct")) is not None
        and _as_int(leg.get("fill_price")) > 0
        and 0 < _as_int(leg.get("buy_filled_qty")) <= _as_int(leg.get("quantity"))
    ]


def _broker_realization_date(
    row: dict[str, Any], completed: list[dict[str, Any]]
) -> tuple[str | None, str]:
    """Resolve the account PnL date without guessing across different exits."""

    observed_dates: set[str] = set()
    missing_timestamp = False
    for leg in completed:
        explicit_date = str(leg.get("realization_date") or "")
        if explicit_date:
            try:
                observed_dates.add(date.fromisoformat(explicit_date).isoformat())
            except ValueError:
                missing_timestamp = True
            continue
        observed = _aware_timestamp(leg.get("target_filled_at"))
        if observed is None:
            missing_timestamp = True
            continue
        observed_dates.add(observed.astimezone(KST).date().isoformat())
    if len(observed_dates) > 1:
        return None, "completed_legs_have_multiple_realization_dates"
    if observed_dates and missing_timestamp:
        return None, "completed_leg_realization_date_partially_missing"
    if observed_dates:
        return next(iter(observed_dates)), "target_fill_reconciliation_date"
    target_date = str(row.get("target_date") or "")
    try:
        date.fromisoformat(target_date)
    except ValueError:
        return None, "legacy_target_date_invalid"
    return target_date, "legacy_target_date_without_fill_timestamp"


def _apply_broker_realized_economics(
    rows: list[dict[str, Any]], loader: RealizedPnlLoader | None
) -> dict[str, int]:
    """Attach exact costs only when a symbol-day aggregate has one safe owner."""

    groups: dict[tuple[str, str], list[tuple[dict[str, Any], str]]] = {}
    summary = {"matched": 0, "fallback": 0, "api_requests": 0}
    for row in rows:
        row["broker_realized_economics"] = {
            "status": "not_applicable",
            "selection_effect": False,
        }
        completed = _completed_broker_legs(row)
        if not completed:
            continue
        if not row.get("eligible_for_tuning"):
            row["broker_realized_economics"] = {
                "status": "not_applicable",
                "reason": "profile_row_ineligible_for_tuning",
                "selection_effect": False,
            }
            continue
        realization_date, date_source = _broker_realization_date(row, completed)
        if realization_date is None:
            row["broker_realized_economics"] = {
                "status": "fixed_cost_fallback",
                "reason": date_source,
                "selection_effect": True,
            }
            summary["fallback"] += 1
            continue
        groups.setdefault((realization_date, str(row.get("symbol") or "")), []).append(
            (row, date_source)
        )

    for (realization_date, symbol), candidates in groups.items():
        if len(candidates) != 1:
            for row, date_source in candidates:
                row["broker_realized_economics"] = {
                    "status": "fixed_cost_fallback",
                    "reason": "multiple_episode_profiles_share_symbol_realization_day",
                    "realization_date": realization_date,
                    "realization_date_source": date_source,
                    "selection_effect": True,
                }
                summary["fallback"] += 1
            continue
        row, date_source = candidates[0]
        if loader is None:
            row["broker_realized_economics"] = {
                "status": "fixed_cost_fallback",
                "reason": "ka10073_loader_not_configured",
                "realization_date": realization_date,
                "realization_date_source": date_source,
                "selection_effect": True,
            }
            summary["fallback"] += 1
            continue
        try:
            summary["api_requests"] += 1
            broker_rows = loader(realization_date, symbol)
        except Exception as exc:
            row["broker_realized_economics"] = {
                "status": "fixed_cost_fallback",
                "reason": f"ka10073_query_failed:{type(exc).__name__}",
                "realization_date": realization_date,
                "realization_date_source": date_source,
                "selection_effect": True,
            }
            summary["fallback"] += 1
            continue

        if len(broker_rows) != 1:
            row["broker_realized_economics"] = {
                "status": "fixed_cost_fallback",
                "reason": "ka10073_unique_symbol_day_row_missing",
                "matched_row_count": len(broker_rows),
                "realization_date": realization_date,
                "realization_date_source": date_source,
                "selection_effect": True,
            }
            summary["fallback"] += 1
            continue

        broker = broker_rows[0]
        legs = _completed_broker_legs(row)
        expected_qty = sum(_as_int(leg.get("target_filled_qty")) for leg in legs)
        buy_notional = sum(
            _as_int(leg.get("fill_price")) * _as_int(leg.get("target_filled_qty"))
            for leg in legs
        )
        sell_notional = sum(
            _as_int(leg.get("target_fill_price"))
            * _as_int(leg.get("target_filled_qty"))
            for leg in legs
        )
        expected_buy_average = buy_notional / expected_qty if expected_qty else 0.0
        expected_sell_average = sell_notional / expected_qty if expected_qty else 0.0
        broker_qty = _as_float(broker.get("filled_qty"))
        broker_buy_average = _as_float(broker.get("buy_average_price"))
        broker_sell_average = _as_float(broker.get("sell_average_price"))
        exact_net = _as_float(broker.get("realized_net_profit_krw"))
        commission = _as_float(broker.get("commission_krw"))
        tax = _as_float(broker.get("tax_krw"))
        gross_profit = sell_notional - buy_notional
        values_present = all(
            value is not None
            for value in (
                broker_qty,
                broker_buy_average,
                broker_sell_average,
                exact_net,
                commission,
                tax,
            )
        )
        identity_matches = bool(
            values_present
            and expected_qty > 0
            and abs(float(broker_qty) - expected_qty) < 1e-9
            and abs(float(broker_buy_average) - expected_buy_average) <= 1.0
            and abs(float(broker_sell_average) - expected_sell_average) <= 1.0
            and abs(gross_profit - float(commission) - float(tax) - float(exact_net))
            <= 1.0
        )
        if not identity_matches:
            row["broker_realized_economics"] = {
                "status": "fixed_cost_fallback",
                "reason": "ka10073_episode_identity_mismatch",
                "expected": {
                    "filled_qty": expected_qty,
                    "buy_average_price": round(expected_buy_average, 6),
                    "sell_average_price": round(expected_sell_average, 6),
                    "gross_profit_krw": gross_profit,
                },
                "observed": broker,
                "realization_date": realization_date,
                "realization_date_source": date_source,
                "selection_effect": True,
            }
            summary["fallback"] += 1
            continue

        row["broker_realized_economics"] = {
            "status": "matched_exact",
            "source_api": "ka10073",
            "entry_trade_date": str(row.get("target_date") or ""),
            "realization_date": realization_date,
            "realization_date_source": date_source,
            "symbol": symbol,
            "filled_qty": expected_qty,
            "buy_notional_krw": buy_notional,
            "sell_notional_krw": sell_notional,
            "gross_profit_krw": gross_profit,
            "commission_krw": round(float(commission), 3),
            "tax_krw": round(float(tax), 3),
            "realized_net_profit_krw": round(float(exact_net), 3),
            "realized_net_return_pct": round(float(exact_net) / buy_notional * 100, 6),
            "broker_profit_rate_pct": broker.get("broker_profit_rate_pct"),
            "selection_effect": True,
            "attribution_contract": (
                "unique_episode_profile_and_exact_symbol_realization_day_quantity_"
                "average_price_gross_cost_reconciliation"
            ),
        }
        summary["matched"] += 1
    return summary


def _historical_profile_row(
    profile_id: str,
    report_date: date,
    profiles: dict[str, Any],
    cost_pct: float,
) -> dict:
    row = profiles.get(profile_id)
    if isinstance(row, dict):
        row = dict(row)
        normalized_legs = []
        for leg in row.get("legs", []):
            if not isinstance(leg, dict):
                continue
            normalized = {
                **leg,
                "profit_price_source": (
                    str(leg.get("profit_price_source"))
                    if leg.get("profit_price_source")
                    else (
                        "broker_target_fill_price"
                        if leg.get("completed")
                        and _as_int(leg.get("target_fill_price"))
                        else (
                            "configured_target_price_proxy"
                            if leg.get("completed")
                            and leg.get("net_profit_pct") is not None
                            else "not_completed"
                        )
                    )
                ),
            }
            if normalized.get("completed"):
                fill_price = _as_int(normalized.get("fill_price"))
                exit_price = _as_int(
                    normalized.get("target_fill_price")
                    or normalized.get("profit_exit_price")
                    or normalized.get("target_price")
                )
                if fill_price > 0 and exit_price > 0:
                    normalized["net_profit_pct"] = round(
                        (exit_price / fill_price - 1.0) * 100.0 - cost_pct, 6
                    )
            exit_execution_class = _exit_execution_class(
                completed=bool(normalized.get("completed")),
                exit_fill_source=str(normalized.get("exit_fill_source") or ""),
                profit_price_source=str(normalized.get("profit_price_source") or ""),
            )
            normalized["exit_execution_class"] = exit_execution_class
            normalized["manual_exit_realized"] = (
                exit_execution_class == "manual_operator_exit"
            )
            normalized["autonomous_target_filled"] = (
                exit_execution_class == "machine_target_fill"
            )
            net_profit = _as_float(normalized.get("net_profit_pct"))
            normalized["realized_loss"] = bool(
                normalized.get("completed")
                and net_profit is not None
                and net_profit < 0.0
            )
            normalized_legs.append(normalized)
        row["legs"] = normalized_legs
        reasons = list(row.get("source_quality_reasons") or [])
        if "held_or_unresolved_inventory" in reasons:
            reasons = [
                reason for reason in reasons if reason != "held_or_unresolved_inventory"
            ]
            row["source_quality_reasons"] = reasons
            if not reasons:
                row["source_quality"] = "pass"
        attempted = bool(row.get("attempted"))
        outcome_complete_for_ev = bool(
            not attempted
            or (
                len(normalized_legs) == 2
                and all(
                    str(leg.get("status") or "") in TERMINAL_LEG_STATUSES
                    for leg in normalized_legs
                )
            )
        )
        row["outcome_complete_for_ev"] = outcome_complete_for_ev
        row["outcome_exclusion_reasons"] = (
            [] if outcome_complete_for_ev else ["held_or_unresolved_inventory"]
        )
        row["eligible_for_tuning"] = bool(row.get("eligible_for_tuning")) and (
            outcome_complete_for_ev
        )
        if (
            not _profile_was_operational(profile_id, report_date)
            and row.get("source_quality") == "gap"
            and "state_missing_or_invalid" in reasons
            and not row.get("attempted")
            and not row.get("legs")
        ):
            return _pre_operational_row(profile_id, report_date.isoformat())
        return row
    if not _profile_was_operational(profile_id, report_date):
        return _pre_operational_row(profile_id, report_date.isoformat())
    return _empty_row(profile_id, report_date.isoformat(), "prior_profile_row_missing")


def reconcile_manual_exit_history(history, *, source_date, cost_pct, registry_path):
    """Project applied owner receipts onto historical rows; never mutate custody."""
    body = registry_path.read_bytes() if registry_path.exists() else b""
    summary = {"path": str(registry_path), "sha256": hashlib.sha256(body).hexdigest(),
        "source_date": source_date, "status": "missing" if not body else "ready",
        "resolved_rows": [], "blocked_rows": [], "runtime_effect": False}
    if not body:
        return summary
    try:
        registry = json.loads(body)
        if registry.get("schema") != "episode_manual_exit_receipt_registry_v1" or not isinstance(registry.get("receipts"), list):
            raise ValueError("registry_schema")
        receipts = registry["receipts"]
        identities = [(r["order_date"], r["symbol"], str(r["order_no"]).lstrip("0")) for r in receipts]
    except (ValueError, TypeError, KeyError):
        summary["status"] = "source_gap_invalid_registry"
        return summary
    duplicates = {key for key in identities if identities.count(key) > 1}
    for day, profiles in history.items():
        for pid, original in list(profiles.items()):
            held = [leg for leg in original.get("legs", []) if leg.get("held")]
            matches = [r for r in receipts if r.get("owner_id") == pid and r.get("entry_trade_date") == day and r.get("status") == "applied"]
            if not held or not matches:
                continue
            try:
                live = profiles_for_target_date(date.fromisoformat(day))[pid]
                if original.get("target_date") != day or original.get("profile_id") != pid:
                    raise ValueError("historical_owner_date_binding")
                for r in matches:
                    key = (r["order_date"], r["symbol"], str(r["order_no"]).lstrip("0"))
                    if (key in duplicates or not key[2] or r["symbol"] != live.symbol or r.get("source_api") != "kt00007"
                        or not day <= date.fromisoformat(r["order_date"]).isoformat() <= source_date
                        or not r.get("applied_at_kst") or _as_int(r.get("fill_price")) <= 0 or _as_int(r.get("filled_qty")) <= 0):
                        raise ValueError("receipt_identity_or_asof")
                if (any(not leg.get("contract_valid") or _as_int(leg.get("target_filled_qty")) > 0 for leg in held)
                    or sum(_as_int(r["filled_qty"]) for r in matches) != sum(_as_int(leg["position_qty"]) for leg in held)):
                    raise ValueError("whole_remaining_position_quantity")
                row = copy.deepcopy(original)
                pending = [[r, _as_int(r["filled_qty"])] for r in matches]
                for i, leg in enumerate(row["legs"]):
                    if not leg.get("held"):
                        continue
                    qty = _as_int(leg["position_qty"])
                    available = next((item for item in pending if item[1] >= qty), None)
                    if available is None:
                        raise ValueError("split_price_allocation_unsupported")
                    r = available[0]
                    available[1] -= qty
                    row["legs"][i] = _sanitize_leg({**leg, "status": "COMPLETE", "position_qty": 0,
                        "target_filled_qty": leg["buy_filled_qty"], "target_fill_price": r["fill_price"],
                        "target_filled_at": None, "target_fill_reconciled_at": r["applied_at_kst"],
                        "exit_fill_source": MANUAL_EXIT_FILL_SOURCE,
                        "manual_exit_receipt": {**r, "allocated_qty": qty, "allocation_authority": "explicit_owner_whole_position_exit"}}, cost_pct)
                if not all(leg.get("contract_valid") for leg in row["legs"]):
                    raise ValueError("resolved_leg_contract")
                row["outcome_complete_for_ev"] = len(row["legs"]) == 2 and all(leg.get("terminal") for leg in row["legs"])
                row["outcome_exclusion_reasons"] = [] if row["outcome_complete_for_ev"] else ["held_or_unresolved_inventory"]
                row["eligible_for_tuning"] = row.get("source_quality") == "pass" and row["outcome_complete_for_ev"]
                if row["outcome_complete_for_ev"]:
                    row["state_status"] = "COMPLETE"
                previous_cost = row.get("broker_realized_economics")
                row["broker_realized_economics"] = {"status": "fixed_cost_fallback", "reason": "manual_receipt_projection_requires_new_exact_cost_attribution"}
                row["manual_exit_history_reconciliation"] = {"registry_sha256": summary["sha256"],
                    "original_state_status": original.get("state_status"), "original_held_legs": len(held),
                    "superseded_broker_realized_economics": previous_cost, "receipts": matches}
                profiles[pid] = row
                summary["resolved_rows"].append({"profile_id": pid, "entry_trade_date": day, "resolved_legs": len(held)})
            except (ValueError, TypeError, KeyError) as exc:
                summary["blocked_rows"].append({"profile_id": pid, "entry_trade_date": day, "reason": str(exc)})
    return summary


def _sanitize_leg(raw: dict[str, Any], cost_pct: float) -> dict[str, Any]:
    status = str(raw.get("status") or "UNKNOWN")
    quantity = _as_int(raw.get("quantity"))
    entry_price = _as_int(raw.get("entry_price"))
    fill_price = _as_int(raw.get("fill_price"))
    target_price = _as_int(raw.get("target_price"))
    position_qty = _as_int(raw.get("position_qty"))
    target_filled_qty = _as_int(raw.get("target_filled_qty"))
    target_fill_price = _as_int(raw.get("target_fill_price"))
    buy_filled_qty = _as_int(
        raw.get("buy_filled_qty", position_qty + target_filled_qty)
    )
    buy_filled_at = _aware_timestamp(raw.get("buy_filled_at"))
    target_filled_at = _aware_timestamp(raw.get("target_filled_at"))
    exit_fill_source = str(raw.get("exit_fill_source") or "")
    manual_exit_verified = exit_fill_source == MANUAL_EXIT_FILL_SOURCE
    manual_receipt = (
        raw.get("manual_exit_receipt")
        if isinstance(raw.get("manual_exit_receipt"), dict)
        else {}
    )
    realization_date = str(
        manual_receipt.get("order_date")
        if manual_exit_verified
        else raw.get("target_order_date") or ""
    )
    try:
        realization_date = date.fromisoformat(realization_date).isoformat()
    except ValueError:
        realization_date = ""
    completed = (
        status == "COMPLETE"
        and target_filled_qty > 0
        and target_filled_qty == buy_filled_qty
        and position_qty == 0
        and fill_price > 0
        and target_price > fill_price
    )
    positive_position_statuses = {
        "POSITION_OPEN",
        "TARGET_SUBMITTING",
        "TARGET_OPEN",
        "HELD",
    }
    held = status == "HELD" or position_qty > 0
    contract_valid = bool(
        quantity in SUPPORTED_OWNED_LEG_QUANTITIES
        and entry_price > 0
        and 0 <= position_qty <= quantity
        and 0 <= target_filled_qty <= buy_filled_qty <= quantity
        and position_qty == buy_filled_qty - target_filled_qty
        and (status not in positive_position_statuses or position_qty > 0)
        and (target_filled_qty == 0 or status in {"TARGET_OPEN", "HELD", "COMPLETE"})
        and (target_fill_price == 0 or target_filled_qty > 0)
        and (
            target_fill_price == 0
            or target_fill_price >= target_price
            or manual_exit_verified
        )
        and (status != "COMPLETE" or completed)
        and (
            status != "NO_FILL"
            or (fill_price == 0 and position_qty == 0 and target_filled_qty == 0)
        )
    )
    profit_exit_price = target_fill_price or target_price
    profit_price_source = (
        "broker_manual_sell_receipt"
        if completed and target_fill_price > 0 and manual_exit_verified
        else (
            "broker_target_fill_price"
            if completed and target_fill_price > 0
            else "configured_target_price_proxy"
            if completed
            else "not_completed"
        )
    )
    net_profit_pct = (
        (profit_exit_price / fill_price - 1.0) * 100.0 - cost_pct if completed else None
    )
    gross_no_slippage_return_pct = (
        (profit_exit_price / fill_price - 1.0) * 100.0 if completed else None
    )
    exit_execution_class = _exit_execution_class(
        completed=completed,
        exit_fill_source=exit_fill_source,
        profit_price_source=profit_price_source,
    )
    holding_duration_sec = (
        (target_filled_at - buy_filled_at).total_seconds()
        if completed
        and buy_filled_at is not None
        and target_filled_at is not None
        and target_filled_at >= buy_filled_at
        else None
    )
    return {
        "leg_id": str(raw.get("leg_id") or ""),
        "quantity": quantity,
        "status": status,
        "entry_price": entry_price,
        "fill_price": fill_price,
        "target_price": target_price,
        "position_qty": position_qty,
        "buy_filled_qty": buy_filled_qty,
        "target_filled_qty": target_filled_qty,
        "target_fill_price": target_fill_price,
        "buy_filled_at": buy_filled_at.isoformat() if buy_filled_at else None,
        "target_filled_at": (
            target_filled_at.isoformat() if target_filled_at else None
        ),
        "target_fill_timestamp_status": (
            "unavailable"
            if raw.get("target_filled_at") in (None, "")
            else "observed"
            if target_filled_at is not None
            else "invalid"
        ),
        "exit_fill_source": exit_fill_source or None,
        # Preserve dated reconciliation evidence without inventing a fill time.
        # Downstream timing diagnostics validate this projection independently.
        "target_order_no": raw.get("target_order_no"),
        "target_order_date": raw.get("target_order_date"),
        "target_fill_reconciled_at": raw.get("target_fill_reconciled_at"),
        "target_exit_reconciliation_receipt": (
            dict(raw["target_exit_reconciliation_receipt"])
            if isinstance(raw.get("target_exit_reconciliation_receipt"), dict)
            else None
        ),
        "manual_exit_receipt": (dict(manual_receipt) if manual_receipt else None),
        "realization_date": realization_date or None,
        "holding_duration_sec": (
            round(holding_duration_sec, 3) if holding_duration_sec is not None else None
        ),
        "lifecycle_timestamp_provenance": (
            "broker_execution_reconciliation_observed_at_not_exchange_fill_time"
        ),
        "profit_exit_price": profit_exit_price if completed else 0,
        "profit_price_source": profit_price_source,
        "exit_execution_class": exit_execution_class,
        "manual_exit_realized": exit_execution_class == "manual_operator_exit",
        "autonomous_target_filled": exit_execution_class == "machine_target_fill",
        "realized_loss": bool(net_profit_pct is not None and net_profit_pct < 0.0),
        "completed": completed,
        "held": held,
        "terminal": status in TERMINAL_LEG_STATUSES,
        "contract_valid": contract_valid,
        "net_profit_pct": (
            round(net_profit_pct, 6) if net_profit_pct is not None else None
        ),
        "gross_no_slippage_return_pct": (
            round(gross_no_slippage_return_pct, 6)
            if gross_no_slippage_return_pct is not None
            else None
        ),
    }


def extract_profile_row(
    *,
    profile_id: str,
    state_path: Path,
    target_date: str,
    cost_pct: float,
    applied_dir: Path = APPLIED_DIR,
    profile=None,
) -> dict:
    profile = profile or PROFILES[profile_id]
    state = _read_json(state_path)
    if state is None:
        return _empty_row(profile_id, target_date, "state_missing_or_invalid")
    reasons: list[str] = []
    if state.get("schema") != f"low_price_two_leg_{profile_id}_state_v1":
        reasons.append("state_schema_mismatch")
    if state.get("trade_date") != target_date:
        reasons.append("state_target_date_mismatch")
    attempted = bool(state.get("attempt_consumed"))
    state_status = str(state.get("status") or "UNKNOWN")
    features = state.get("signal_features")
    if not isinstance(features, dict):
        features = {}
        reasons.append("signal_features_invalid")
    if attempted:
        if (
            features.get("schema") != "regular_two_leg_entry_signal_features_v1"
            or features.get("strategy") != profile_id
            or features.get("symbol") != profile.symbol
        ):
            reasons.append("signal_feature_profile_contract_mismatch")
    elif state_status != "NO_TRADE":
        reasons.append("nonterminal_no_attempt_state")
    raw_legs = state.get("legs")
    if not isinstance(raw_legs, list):
        raw_legs = []
        reasons.append("legs_invalid")
    legs = [_sanitize_leg(leg, cost_pct) for leg in raw_legs if isinstance(leg, dict)]
    if attempted:
        parsed_target_date = date.fromisoformat(target_date)
        applied_policy: dict[str, Any] | None = None
        applied_hash = ""
        if profile.policy.runtime_policy_source == "exact_date_auto_expansion_policy":
            if (
                features.get("runtime_policy_source")
                != "exact_date_auto_expansion_policy"
                or features.get("runtime_policy_hash")
                != profile.policy.runtime_policy_hash
            ):
                reasons.append("exact_date_auto_expansion_policy_provenance_mismatch")
        elif parsed_target_date >= APPLIED_POLICY_PROVENANCE_REQUIRED_DATE:
            applied_policy, applied_hash, applied_reason = load_applied_profile_policy(
                profile_id,
                target_date=parsed_target_date,
                applied_dir=applied_dir,
            )
            if applied_policy is None:
                reasons.append(f"exact_date_applied_policy_invalid:{applied_reason}")
            elif (
                features.get("runtime_policy_source") != "preopen_applied_policy"
                or features.get("runtime_policy_hash") != applied_hash
                or _as_float(features.get("required_drawdown_pct"))
                != float(applied_policy["rolling_high_drawdown_pct"])
                or _as_float(features.get("max_near_low_pct"))
                != float(applied_policy["rolling_low_proximity_pct"])
                or _as_int(features.get("lookback_bars"))
                != int(applied_policy["lookback_bars"])
                or _as_int(features.get("entry_valid_completed_bars"))
                != int(applied_policy["entry_valid_completed_bars"])
                or _as_int(features.get("target_ticks"))
                != int(applied_policy["target_ticks"])
            ):
                reasons.append("signal_feature_exact_date_applied_policy_mismatch")
            if applied_policy is not None and any(
                leg["quantity"] * 2 != int(applied_policy["quantity"]) for leg in legs
            ):
                reasons.append("exact_date_applied_quantity_mismatch")
        if len(legs) != 2 or {leg["leg_id"] for leg in legs} != set(
            profile.policy.entry_leg_ids
        ):
            reasons.append("two_leg_identity_contract_invalid")
        if (
            any(
                leg["quantity"] not in SUPPORTED_OWNED_LEG_QUANTITIES
                or leg["status"] not in KNOWN_LEG_STATUSES
                for leg in legs
            )
            or len({leg["quantity"] for leg in legs}) != 1
        ):
            reasons.append("leg_quantity_or_status_invalid")
        signal_close = _as_int(features.get("signal_close"))
        if signal_close <= 0:
            reasons.append("signal_close_missing_or_invalid")
        else:
            expected_entries = {
                str(plan["leg_id"]): int(plan["entry_price"])
                for plan in profile.policy.entry_legs(signal_close)
            }
            if any(
                expected_entries.get(leg["leg_id"]) != leg["entry_price"]
                for leg in legs
            ):
                reasons.append("leg_entry_price_profile_contract_invalid")
        expected_target_ticks = int(
            (applied_policy or {}).get("target_ticks", profile.policy.target_ticks)
        )
        if any(
            leg["fill_price"] > 0
            and leg["target_price"]
            != move_price_by_ticks(leg["fill_price"], expected_target_ticks)
            for leg in legs
        ):
            reasons.append("leg_target_price_profile_contract_invalid")
        if any(not leg["contract_valid"] for leg in legs):
            reasons.append("leg_execution_contract_invalid")
        if any(leg["status"] == "COMPLETE" and not leg["completed"] for leg in legs):
            reasons.append("complete_leg_receipt_contract_invalid")
        if all(leg["terminal"] for leg in legs):
            expected_terminal_status = (
                "NO_TRADE"
                if all(leg["status"] == "NO_FILL" for leg in legs)
                else "COMPLETE"
            )
            if state_status != expected_terminal_status:
                reasons.append("aggregate_terminal_status_mismatch")
        elif state_status in {"COMPLETE", "NO_TRADE"}:
            reasons.append("aggregate_nonterminal_status_mismatch")
    outcome_complete_for_ev = bool(
        not attempted or (len(legs) == 2 and all(leg["terminal"] for leg in legs))
    )
    outcome_exclusion_reasons = (
        [] if outcome_complete_for_ev else ["held_or_unresolved_inventory"]
    )
    return {
        "profile_id": profile_id,
        "symbol": profile.symbol,
        "session": profile.session,
        "target_date": target_date,
        "source_quality": "pass" if not reasons else "gap",
        "source_quality_reasons": reasons,
        "eligible_for_tuning": not reasons and outcome_complete_for_ev,
        "outcome_complete_for_ev": outcome_complete_for_ev,
        "outcome_exclusion_reasons": outcome_exclusion_reasons,
        "attempted": attempted,
        "no_signal": not attempted and state_status == "NO_TRADE",
        "state_status": state_status,
        "signal_features": features,
        "legs": legs,
    }


def _aggregate(rows: list[dict]) -> dict:
    eligible_days = sum(bool(row.get("eligible_for_tuning")) for row in rows)
    source_valid_observation_days = sum(
        row.get("source_quality") == "pass" for row in rows
    )
    all_attempted_rows = [row for row in rows if row.get("attempted")]
    attempted_rows = [
        row for row in rows if row.get("eligible_for_tuning") and row.get("attempted")
    ]
    legs = [leg for row in attempted_rows for leg in row.get("legs", [])]
    all_legs = [leg for row in all_attempted_rows for leg in row.get("legs", [])]
    completed = [leg for leg in legs if leg.get("completed")]
    broker_priced_completed = [
        leg for row in attempted_rows for leg in _completed_broker_legs(row)
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
        for leg in completed
        if leg.get("profit_price_source") == "configured_target_price_proxy"
    ]
    timed_completed = [
        leg
        for leg in completed
        if _as_float(leg.get("holding_duration_sec")) is not None
        and float(leg["holding_duration_sec"]) >= 0.0
    ]
    timed_machine_target_completed = [
        leg
        for leg in machine_target_completed
        if _as_float(leg.get("holding_duration_sec")) is not None
        and float(leg["holding_duration_sec"]) >= 0.0
    ]
    holding_durations = [float(leg["holding_duration_sec"]) for leg in timed_completed]
    machine_target_holding_durations = [
        float(leg["holding_duration_sec"]) for leg in timed_machine_target_completed
    ]
    sorted_holding_durations = sorted(holding_durations)
    p90_holding_duration = (
        sorted_holding_durations[
            max(0, math.ceil(len(sorted_holding_durations) * 0.9) - 1)
        ]
        if sorted_holding_durations
        else None
    )
    gross_no_slippage_returns = [
        float(leg["gross_no_slippage_return_pct"])
        for leg in completed
        if _as_float(leg.get("gross_no_slippage_return_pct")) is not None
    ]
    timed_broker_completed = [
        leg
        for leg in broker_priced_completed
        if _as_float(leg.get("holding_duration_sec")) is not None
        and float(leg["holding_duration_sec"]) >= 0.0
    ]
    attempted_notional = sum(
        _as_int(leg.get("entry_price")) * _as_int(leg.get("quantity")) for leg in legs
    )
    exact_cost_rows = [
        row
        for row in attempted_rows
        if (row.get("broker_realized_economics") or {}).get("status") == "matched_exact"
    ]
    exact_cost_row_ids = {id(row) for row in exact_cost_rows}
    fixed_cost_broker_profit = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["net_profit_pct"])
        / 100.0
        for row in attempted_rows
        if id(row) not in exact_cost_row_ids
        for leg in _completed_broker_legs(row)
    )
    exact_broker_profit = sum(
        float(row["broker_realized_economics"]["realized_net_profit_krw"])
        for row in exact_cost_rows
    )
    broker_realized_profit = fixed_cost_broker_profit + exact_broker_profit
    broker_completed_capital_occupied_krw_seconds = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["holding_duration_sec"])
        for leg in timed_broker_completed
    )
    timed_broker_realized_profit = 0.0
    for row in attempted_rows:
        row_broker_legs = _completed_broker_legs(row)
        row_timed_legs = [
            leg
            for leg in row_broker_legs
            if _as_float(leg.get("holding_duration_sec")) is not None
            and float(leg["holding_duration_sec"]) >= 0.0
        ]
        exact_economics = row.get("broker_realized_economics") or {}
        if (
            exact_economics.get("status") == "matched_exact"
            and row_broker_legs
            and len(row_timed_legs) == len(row_broker_legs)
        ):
            timed_broker_realized_profit += float(
                exact_economics["realized_net_profit_krw"]
            )
        else:
            timed_broker_realized_profit += sum(
                _as_int(leg.get("fill_price"))
                * _as_int(leg.get("buy_filled_qty"))
                * float(leg["net_profit_pct"])
                / 100.0
                for leg in row_timed_legs
            )
    target_proxy_profit = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["net_profit_pct"])
        / 100.0
        for leg in target_proxy_completed
    )
    manual_exit_fixed_cost_estimate_profit = sum(
        _as_int(leg.get("fill_price"))
        * _as_int(leg.get("buy_filled_qty"))
        * float(leg["net_profit_pct"])
        / 100.0
        for leg in manual_exit_completed
    )
    completed_notional = sum(
        _as_int(leg.get("fill_price")) * _as_int(leg.get("buy_filled_qty"))
        for leg in broker_priced_completed
    )
    realized_profit = broker_realized_profit if completed_notional else None
    ev = (
        broker_realized_profit / completed_notional * 100.0
        if completed_notional
        else None
    )
    fill_cohorts = {}
    for name, full in (("full_fill", True), ("partial_fill", False)):
        selected_legs = [
            leg
            for leg in broker_priced_completed
            if (_as_int(leg.get("buy_filled_qty")) == _as_int(leg.get("quantity")))
            == full
        ]
        notional = sum(
            _as_int(leg["fill_price"]) * _as_int(leg["buy_filled_qty"])
            for leg in selected_legs
        )
        profit = sum(
            _as_int(leg["fill_price"])
            * _as_int(leg["buy_filled_qty"])
            * float(leg["net_profit_pct"])
            / 100
            for leg in selected_legs
        )
        fill_cohorts[name] = {
            "completed_legs": len(selected_legs),
            "completed_notional_krw": notional,
            "broker_price_fixed_cost_ev_pct": (
                round(profit / notional * 100, 6) if notional else None
            ),
            "cost_source": "effective_dated_fixed_cost_estimate_not_exact_broker_cost",
            "allowed_runtime_apply": False,
        }
    return {
        "eligible_days": eligible_days,
        "source_valid_observation_days": source_valid_observation_days,
        "source_gap_days": sum(
            row.get("source_quality") not in {"pass", "not_applicable"} for row in rows
        ),
        "pre_operational_days": sum(
            row.get("cohort") == "pre_operational_not_applicable" for row in rows
        ),
        "attempted_episodes": len(attempted_rows),
        "attempted_episodes_per_eligible_day": (
            round(len(attempted_rows) / eligible_days, 6) if eligible_days else None
        ),
        "attempted_episodes_per_source_valid_observation_day": (
            round(len(attempted_rows) / source_valid_observation_days, 6)
            if source_valid_observation_days
            else None
        ),
        "completed_legs": len(completed),
        "broker_priced_completed_legs": len(broker_priced_completed),
        "machine_target_completed_legs": len(machine_target_completed),
        "manual_exit_completed_legs": len(manual_exit_completed),
        "manual_exit_loss_legs": len(manual_exit_losses),
        "target_price_proxy_completed_legs": len(target_proxy_completed),
        "broker_sell_fill_price_coverage": (
            round(len(broker_priced_completed) / len(completed), 6)
            if completed
            else None
        ),
        "exact_broker_cost_profile_rows": len(exact_cost_rows),
        "exact_broker_cost_completed_legs": sum(
            len(_completed_broker_legs(row)) for row in exact_cost_rows
        ),
        "fixed_cost_estimate_completed_legs": len(broker_priced_completed)
        - sum(len(_completed_broker_legs(row)) for row in exact_cost_rows),
        "no_fill_legs": sum(leg.get("status") == "NO_FILL" for leg in legs),
        "held_or_unresolved_legs": sum(
            leg.get("held") or not leg.get("terminal") for leg in all_legs
        ),
        "notional_weighted_ev_pct": round(ev, 6) if ev is not None else None,
        "fill_cohorts": fill_cohorts,
        "pooled_realized_ev_role": "all_fill_accounting_only_not_fill_quality_or_promotion",
        "realized_ev_status": (
            "observed" if completed_notional else "no_broker_priced_completion"
        ),
        "broker_completed_notional_krw": completed_notional,
        "attempted_notional_return_pct_diagnostic": (
            round(broker_realized_profit / attempted_notional * 100.0, 6)
            if attempted_notional and realized_profit is not None
            else None
        ),
        "full_fill_completed_legs": sum(
            _as_int(leg.get("buy_filled_qty")) == _as_int(leg.get("quantity"))
            for leg in broker_priced_completed
        ),
        "partial_fill_completed_legs": sum(
            0 < _as_int(leg.get("buy_filled_qty")) < _as_int(leg.get("quantity"))
            for leg in broker_priced_completed
        ),
        "gross_no_slippage_avg_return_pct": (
            round(statistics.fmean(gross_no_slippage_returns), 6)
            if gross_no_slippage_returns
            else None
        ),
        "completed_legs_with_lifecycle_timing": len(timed_completed),
        "machine_target_completed_legs_with_lifecycle_timing": len(
            timed_machine_target_completed
        ),
        "manual_exit_completed_legs_with_lifecycle_timing": sum(
            leg.get("exit_execution_class") == "manual_operator_exit"
            for leg in timed_completed
        ),
        "lifecycle_timing_missing_completed_legs": len(completed)
        - len(timed_completed),
        "median_reconciliation_confirmed_holding_duration_sec": (
            round(statistics.median(holding_durations), 3)
            if holding_durations
            else None
        ),
        "p90_reconciliation_confirmed_holding_duration_sec": (
            round(p90_holding_duration, 3) if p90_holding_duration is not None else None
        ),
        "target_reconciliation_completion_within_180s_count": sum(
            duration <= 180.0 for duration in machine_target_holding_durations
        ),
        "target_reconciliation_completion_within_180s_ratio": (
            round(
                sum(duration <= 180.0 for duration in machine_target_holding_durations)
                / len(machine_target_holding_durations),
                6,
            )
            if machine_target_holding_durations
            else None
        ),
        "completed_holding_seconds_sum": (
            round(sum(holding_durations), 3) if holding_durations else None
        ),
        "broker_realized_net_profit_krw": (
            round(realized_profit, 3) if realized_profit is not None else None
        ),
        "cost_adjusted_net_profit_krw": (
            round(realized_profit, 3) if realized_profit is not None else None
        ),
        "cost_adjusted_net_profit_krw_per_eligible_day": (
            round(broker_realized_profit / eligible_days, 6)
            if eligible_days and realized_profit is not None
            else None
        ),
        "cost_adjusted_net_profit_krw_per_source_valid_observation_day": (
            round(broker_realized_profit / source_valid_observation_days, 6)
            if source_valid_observation_days and realized_profit is not None
            else None
        ),
        "exact_broker_realized_net_profit_krw": round(exact_broker_profit, 3),
        "fixed_cost_estimate_net_profit_krw": round(fixed_cost_broker_profit, 3),
        "manual_exit_fixed_cost_estimate_net_profit_krw": round(
            manual_exit_fixed_cost_estimate_profit, 3
        ),
        "broker_completed_capital_occupied_krw_seconds": (
            round(broker_completed_capital_occupied_krw_seconds, 3)
            if timed_broker_completed
            else None
        ),
        "broker_completed_net_return_per_capital_hour": (
            round(
                timed_broker_realized_profit
                / (broker_completed_capital_occupied_krw_seconds / 3600.0),
                9,
            )
            if broker_completed_capital_occupied_krw_seconds > 0
            else None
        ),
        "target_price_proxy_notional_weighted_ev_pct": (
            round(target_proxy_profit / attempted_notional * 100.0, 6)
            if attempted_notional
            else None
        ),
    }


def _axis_outcome(
    rows: list[dict], *, min_drawdown: float, max_near_low: float
) -> dict:
    selected: list[dict] = []
    for row in rows:
        if not row.get("attempted"):
            continue
        features = row.get("signal_features") or {}
        drawdown = _as_float(features.get("observed_drawdown_pct"))
        near_low = _as_float(features.get("observed_near_low_pct"))
        if (
            drawdown is not None
            and near_low is not None
            and drawdown + 1e-12 >= min_drawdown
            and near_low - 1e-12 <= max_near_low
        ):
            selected.append(row)
    outcome = _aggregate(selected)
    source_valid_observation_days = sum(
        row.get("source_quality") == "pass" for row in rows
    )
    outcome["source_valid_observation_days"] = source_valid_observation_days
    outcome["attempted_episodes_per_source_valid_observation_day"] = (
        round(outcome["attempted_episodes"] / source_valid_observation_days, 6)
        if source_valid_observation_days
        else None
    )
    outcome["cost_adjusted_net_profit_krw_per_source_valid_observation_day"] = (
        round(
            outcome["cost_adjusted_net_profit_krw"] / source_valid_observation_days,
            6,
        )
        if source_valid_observation_days
        and outcome["cost_adjusted_net_profit_krw"] is not None
        else None
    )
    return outcome


def _policy_windows(
    rows: list[dict],
    *,
    current_policy: dict | None,
    policies_by_date: dict[str, dict | None],
) -> tuple[dict, dict]:
    """Separate semantic policy identity from unrelated global policy hashes.

    Missing applied receipts break the contiguous epoch. Bad observation rows
    remain visible inside their policy window; they do not become valid outcomes.
    """

    def identity(policy: dict | None) -> str | None:
        if not policy:
            return None
        policy = {
            key: (
                int(value)
                if isinstance(value, float)
                and math.isfinite(value)
                and value.is_integer()
                else value
            )
            for key, value in policy.items()
        }
        return hashlib.sha256(
            json.dumps(policy, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()

    current_id = identity(current_policy)
    matching = [
        row
        for row in rows
        if current_id is not None
        and identity(policies_by_date.get(row["target_date"])) == current_id
    ]
    epoch_dates: set[str] = set()
    for day in sorted(policies_by_date, reverse=True):
        if current_id is None or identity(policies_by_date[day]) != current_id:
            break
        epoch_dates.add(day)
    epoch_rows = [row for row in matching if row["target_date"] in epoch_dates]

    def window(selected: list[dict], name: str) -> dict:
        return {
            "window_policy": name,
            "policy_cohort_id": current_id,
            "policy": current_policy,
            "status": "bound" if current_id else "current_applied_policy_missing",
            "summary": _aggregate(selected),
            "rows": selected,
            "excluded_row_count": len(rows) - len(selected),
            "runtime_effect": False,
        }

    cohort = window(matching, CURRENT_WINDOW_NAME)
    epoch = window(epoch_rows, POST_APPLY_WINDOW_NAME)
    epoch["applied_epoch_start"] = min(epoch_dates) if epoch_dates else None
    return cohort, epoch


def _read_daily_history(path: Path, *, wanted=None) -> dict | None:
    wanted = wanted or {"schema", "report_type", "target_date", "clean_tuning_baseline_date", "daily"}
    sections, current = {}, None
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.startswith('  "'):
                    if current in wanted:
                        sections[current] = json.loads("".join(sections[current]).rstrip().rstrip(","))
                    current = line.split('"', 2)[1]
                    if current in wanted:
                        sections[current] = [line.split(":", 1)[1]]
                elif current in wanted:
                    if line.strip() == "}" and line.startswith("}"):
                        sections[current] = json.loads("".join(sections[current]).rstrip().rstrip(","))
                        current = None
                    else:
                        sections[current].append(line)
        if wanted <= sections.keys() and all(not isinstance(sections[k], list) for k in wanted):
            return sections
        # Legacy small compact publications remain readable.
        return _read_json(path) if path.stat().st_size <= 64 * 1024 * 1024 else None
    except (OSError, ValueError, TypeError):
        return None


def _load_history(
    output_dir: Path, target_date: date, cost_pct: float
) -> dict[str, dict[str, dict]]:
    target_profiles = _effective_report_profiles(target_date)
    history: dict[str, dict[str, dict]] = {}
    for path in sorted(output_dir.glob(f"{REPORT_TYPE}_*.json")):
        raw_date = path.stem.removeprefix(f"{REPORT_TYPE}_")
        try:
            report_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= report_date < target_date:
            continue
        if not is_krx_trading_day(report_date):
            continue
        target_profiles = _effective_report_profiles(report_date)
        payload = _read_daily_history(path)
        profiles = (payload or {}).get("daily", {}).get("profiles", {})
        if (
            not payload
            or payload.get("report_type") != REPORT_TYPE
            or payload.get("schema") not in SUPPORTED_REPORT_SCHEMAS
            or payload.get("target_date") != raw_date
            or payload.get("clean_tuning_baseline_date")
            != CLEAN_BASELINE_DATE.isoformat()
            or not isinstance(profiles, dict)
        ):
            history[raw_date] = {
                profile_id: _empty_row(
                    profile_id, raw_date, "prior_report_contract_invalid"
                )
                for profile_id in target_profiles
            }
            continue
        native_ids = set(target_profiles)
        native_ids.update(
            profile_id
            for profile_id, row in profiles.items()
            if isinstance(row, dict)
            and profile_id.startswith("auto_")
            and row.get("profile_id") == profile_id
            and (row.get("signal_features") or {}).get("runtime_policy_source")
            == "exact_date_auto_expansion_policy"
        )
        history[raw_date] = {
            profile_id: _historical_profile_row(
                profile_id, report_date, profiles, cost_pct
            )
            for profile_id in sorted(native_ids)
        }
    return history


def _samsung_same_stage_owner(
    target_date: str, samsung_candidate_dir: Path
) -> dict[str, Any]:
    path = samsung_candidate_dir / (
        f"samsung_machine_entry_policy_candidate_{target_date}.json"
    )
    if not path.exists():
        return {
            "status": "no_samsung_candidate_for_target_date",
            "mutation_present": False,
            "source_path": str(path),
        }
    payload = _read_json(path)
    if payload is None:
        return {
            "status": "samsung_candidate_invalid_fail_closed",
            "mutation_present": True,
            "source_path": str(path),
        }
    valid, reason = validate_samsung_candidate(payload)
    if not valid:
        return {
            "status": f"samsung_candidate_{reason}_fail_closed",
            "mutation_present": True,
            "source_path": str(path),
        }
    mutations = list(payload.get("policy_mutations") or [])
    return {
        "status": (
            "samsung_regular_entry_mutation_owns_stage"
            if mutations
            else "samsung_candidate_has_no_stage_mutation"
        ),
        "mutation_present": bool(mutations),
        "source_path": str(path),
        "policy_mutations": mutations,
    }


def _effective_report_profiles(day):
    profiles = dict(profiles_for_target_date(day))
    try:
        from src.engine.automation.low_price_two_leg_auto_expansion_policy import (
            load_policy,
        )
        from src.trading.low_price_two_leg.auto_expansion_service import _profile

        payload = load_policy(day)
        profiles.update(
            {
                key: _profile(value, authority_hash=payload["policy_hash"])
                for key, value in payload["profiles"].items()
            }
        )
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return profiles


def build_report(
    *,
    target_date: str,
    state_dir: Path = DEFAULT_STATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    source_quality_dir: Path = SOURCE_QUALITY_DIR,
    applied_dir: Path = APPLIED_DIR,
    cost_pct: float = DEFAULT_ROUND_TRIP_COST_PCT,
    machine_microstructure_report_dir: Path = MACHINE_MICROSTRUCTURE_REPORT_DIR,
    realized_pnl_loader: RealizedPnlLoader | None = None,
    paired_context_loader: Callable | None = None,
    paired_selection_dir: Path = CANDIDATE_DIR,
) -> dict:
    parsed_date = date.fromisoformat(target_date)
    target_profiles = dict(profiles_for_target_date(parsed_date)) if parsed_date >= date(2026, 9, 17) else _effective_report_profiles(parsed_date)
    expected_clean_dates = _clean_trading_dates_through(parsed_date)
    target_date_is_trading = is_krx_trading_day(parsed_date)
    if not math.isfinite(cost_pct) or not 0 <= cost_pct < 100:
        raise ValueError("cost_pct_must_be_finite_percentage")
    micro_feedback = load_prior_owner_diagnostic(
        target_date=parsed_date,
        owner="episode",
        report_dir=machine_microstructure_report_dir,
    )
    micro_feedback_cache: dict[str, dict[str, Any]] = {
        str(micro_feedback["source_date"]): micro_feedback
    }

    def feedback_for_source_date(owner_source_date: str) -> dict[str, Any]:
        cached = micro_feedback_cache.get(owner_source_date)
        if cached is not None:
            return cached
        try:
            requested_source_date = date.fromisoformat(owner_source_date)
        except ValueError:
            return {
                "status": "owner_source_date_invalid",
                "source_date": owner_source_date,
                "owner_payload": None,
            }
        loaded = load_prior_owner_diagnostic(
            target_date=parsed_date,
            owner="episode",
            report_dir=machine_microstructure_report_dir,
            source_date=requested_source_date,
        )
        micro_feedback_cache[owner_source_date] = loaded
        return loaded

    def micro_diagnostic(profile_id: str, *, owner_source_date: str) -> dict[str, Any]:
        feedback = feedback_for_source_date(owner_source_date)
        feedback_payload = feedback.get("owner_payload") or {}
        feedback_profiles = (
            feedback_payload.get("profiles")
            if isinstance(feedback_payload, dict)
            else {}
        )
        if not isinstance(feedback_profiles, dict):
            feedback_profiles = {}
        source_date_matches = feedback.get("source_date") == owner_source_date
        return {
            "status": (
                "loaded"
                if source_date_matches and profile_id in feedback_profiles
                else (
                    "owner_profile_not_present"
                    if source_date_matches and feedback["status"] == "loaded"
                    else (
                        "owner_source_date_mismatch"
                        if feedback["status"] == "loaded"
                        else feedback["status"]
                    )
                )
            ),
            "source_date": feedback.get("source_date"),
            "owner_source_date": owner_source_date,
            "source_path": feedback.get("source_path"),
            "source_sha256": feedback.get("source_sha256"),
            "selection_effect": False,
            "base_policy_unchanged": True,
            "payload": (
                feedback_profiles.get(profile_id) if source_date_matches else None
            ),
        }

    daily: dict[str, dict] = {}
    prior_state_reconciliations: dict[str, dict] = {}
    for profile_id in target_profiles:
        state_path = state_dir / f"{profile_id}_state.json"
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
            resolved_row = extract_profile_row(
                profile_id=profile_id,
                state_path=state_path,
                target_date=state_date.isoformat(),
                cost_pct=cost_pct,
                applied_dir=applied_dir,
            )
            original_preflight = _source_quality_preflight(
                state_date.isoformat(), source_quality_dir
            )
            if not original_preflight["tuning_input_allowed"]:
                resolved_row["eligible_for_tuning"] = False
                resolved_row["source_quality"] = "gap"
                if (
                    "original_date_source_quality_audit_blocked"
                    not in resolved_row["source_quality_reasons"]
                ):
                    resolved_row["source_quality_reasons"].append(
                        "original_date_source_quality_audit_blocked"
                    )
            resolved_row["microstructure_prior_trading_day_diagnostic"] = (
                micro_diagnostic(
                    profile_id,
                    owner_source_date=state_date.isoformat(),
                )
            )
            prior_state_reconciliations[profile_id] = {
                "source_date": state_date.isoformat(),
                "state_status": resolved_row["state_status"],
                "row": resolved_row,
                "source_quality_preflight": original_preflight,
            }
            daily[profile_id] = _empty_row(
                profile_id,
                target_date,
                "prior_episode_custody_no_current_date_episode",
            )
            continue
        daily[profile_id] = extract_profile_row(
            profile_id=profile_id,
            state_path=state_path,
            target_date=target_date,
            cost_pct=cost_pct,
            applied_dir=applied_dir,
            profile=target_profiles[profile_id],
        )
    source_preflight = _source_quality_preflight(target_date, source_quality_dir)
    if not source_preflight["tuning_input_allowed"]:
        for row in daily.values():
            row["eligible_for_tuning"] = False
            if (
                "observation_source_quality_audit_blocked"
                not in row["source_quality_reasons"]
            ):
                row["source_quality_reasons"].append(
                    "observation_source_quality_audit_blocked"
                )
            row["source_quality"] = "gap"
    for profile_id, row in daily.items():
        row["microstructure_prior_trading_day_diagnostic"] = micro_diagnostic(
            profile_id,
            owner_source_date=str(micro_feedback["source_date"]),
        )
    economics_rows = list(daily.values()) + [
        item["row"] for item in prior_state_reconciliations.values()
    ]
    broker_realized_reconciliation = _apply_broker_realized_economics(
        economics_rows, realized_pnl_loader
    )
    history = _load_history(output_dir, parsed_date, cost_pct)
    for profile_id, reconciliation in prior_state_reconciliations.items():
        source_date = reconciliation["source_date"]
        history.setdefault(
            source_date,
            {
                item: _empty_row(
                    item,
                    source_date,
                    "prior_report_missing_during_state_reconciliation",
                )
                for item in target_profiles
            },
        )
        history[source_date][profile_id] = reconciliation["row"]
    if target_date_is_trading:
        history[target_date] = daily
    manual_exit_reconciliation = reconcile_manual_exit_history(history,
        source_date=target_date, cost_pct=cost_pct,
        registry_path=state_dir.parent / "episode_manual_exit_receipts.json")
    dates = sorted(history)
    observed_date_set = {date.fromisoformat(item) for item in dates}
    unobserved_dates = [
        item.isoformat()
        for item in expected_clean_dates
        if item not in observed_date_set
    ]
    binding = runtime_policy_binding(target_date=parsed_date, applied_dir=applied_dir)
    applied_history: dict[str, dict] = {}
    applied_history_sources: dict[str, dict] = {}
    for day in expected_clean_dates:
        if dates and day.isoformat() < dates[0]:
            continue
        try:
            prior_binding = runtime_policy_binding(
                target_date=day, applied_dir=applied_dir
            )
        except ValueError:
            prior_binding = {"status": "invalid"}
        applied_history_sources[day.isoformat()] = {
            key: prior_binding.get(key)
            for key in ("status", "source_path", "artifact_hash")
        }
        applied_history[day.isoformat()] = (
            prior_binding.get("policies", {})
            if prior_binding.get("status") == "ready"
            else {}
        )
    windows: dict[str, dict[str, Any]] = {
        CLEAN_WINDOW_NAME: {},
        CURRENT_WINDOW_NAME: {},
        POST_APPLY_WINDOW_NAME: {},
    }
    for profile_id in target_profiles:
        rows = [history[day].get(profile_id) or _empty_row(profile_id, day, "profile_not_observed_in_historical_inventory") for day in dates]
        windows[CLEAN_WINDOW_NAME][profile_id] = {
            "summary": _aggregate(rows),
            "rows": rows,
            "decision_authority": "all_version_actual_audit_only",
        }
        current_policy = (
            (binding.get("policies") or {}).get(profile_id)
            if binding.get("status") == "ready"
            else None
        )
        cohort, epoch = _policy_windows(
            rows,
            current_policy=current_policy,
            policies_by_date={
                day: policies.get(profile_id)
                for day, policies in applied_history.items()
            },
        )
        windows[CURRENT_WINDOW_NAME][profile_id] = cohort
        windows[POST_APPLY_WINDOW_NAME][profile_id] = epoch
    report = {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "artifact_path": str(output_dir / f"{REPORT_TYPE}_{target_date}.json"),
        "source_runtime_policy_binding": binding,
        "applied_policy_history_sources": applied_history_sources,
        "decision_window": POST_APPLY_WINDOW_NAME,
        "evaluation_authority_contract": SUBSET_AUTHORITY_CONTRACT,
        "economic_replay_handoff": {
            "owner": "low_price_two_leg_expanded_candidate_research",
            "profile_field": "existing_axis_economic_replay",
            "decision_authority": "source_only_no_runtime_or_order_authority",
            "runtime_effect": False,
            "reason": "observed_signal_subset_cannot_reconstruct_next_entry_or_custody",
        },
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "target_date_is_krx_trading_day": target_date_is_trading,
        "cost_pct": cost_pct,
        "cost_contract": {
            **canonical_cost_contract(),
            "round_trip_cost_pct": cost_pct,
        },
        "cost_model": {
            "primary_source": "ka10073_exact_when_uniquely_attributable",
            "fallback_source": "fixed_round_trip_cost_pct",
            "fixed_round_trip_cost_pct": cost_pct,
            "broker_realized_reconciliation": broker_realized_reconciliation,
            "exact_match_required_fields": [
                "symbol_day",
                "filled_qty",
                "buy_average_price",
                "sell_average_price",
                "gross_profit_minus_commission_and_tax",
            ],
            "ambiguous_owner_policy": "fixed_cost_fallback_no_exact_pnl_allocation",
        },
        "metric_contract": METRIC_CONTRACT,
        "source_quality_preflight": source_preflight,
        "daily": {"profiles": daily},
        "manual_exit_history_reconciliation": manual_exit_reconciliation,
        "machine_microstructure_prior_trading_day_diagnostic_source": {
            key: value
            for key, value in micro_feedback.items()
            if key != "owner_payload"
        },
        "prior_state_reconciliations": prior_state_reconciliations,
        "clean_baseline_window": {
            "start_date": CLEAN_BASELINE_DATE.isoformat(),
            "end_date": target_date,
            "expected_trading_date_count": len(expected_clean_dates),
            "available_actual_observation_dates": dates,
            "available_actual_observation_date_count": len(dates),
            "unobserved_trading_dates": unobserved_dates,
            "unobserved_trading_date_count": len(unobserved_dates),
            "unobserved_dates_block_candidate": False,
            "candidate_window_uses_only_available_actual_observations": True,
            "missing_dates_imputed_as_outcomes": False,
            "historical_market_replay_included": False,
        },
        "windows": windows,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "decision": "profile_separated_actual_outcome_observation_only",
    }
    from src.engine.monitoring.research_closed_loop import version_economics

    capture = durable_observation_manifest(target_date, source_quality_dir) if report["source_quality_preflight"]["tuning_input_allowed"] and parsed_date >= date(2026, 9, 17) else {"status": "source_gap", "reason": "capture_not_admitted", "profiles": {}}
    report["durable_observation_manifest"] = capture
    for pid, row in daily.items():
        row["durable_observation_capture"] = {**{key: value for key, value in capture.items() if key != "profiles"}, "profile": capture["profiles"].get(pid)}

    native_version_rows = [
        row for day in sorted(history) for row in history[day].values()
    ]
    report["policy_version_economics"] = version_economics(native_version_rows)
    native_dates = sorted(history)
    report["policy_version_rolling_last_30"] = version_economics(
        [row for row in native_version_rows if row["target_date"] in native_dates[-30:]]
    )
    report["policy_version_holdout_last_16"] = version_economics(
        [row for row in native_version_rows if row["target_date"] in native_dates[-16:]]
    )
    report["paired_economic_search"] = _paired_economic_search(report, context_loader=paired_context_loader, selection_dir=paired_selection_dir)
    report["artifact_hash"] = report_artifact_hash(report)
    return report


def paired_search_handoff(target_date: str, *, output_dir=OUTPUT_DIR, candidate_dir=CANDIDATE_DIR) -> dict:
    """Bounded native projection for Daily/EV/runtime; no economic re-execution."""
    report_path = output_dir / f"{REPORT_TYPE}_{target_date}.json"
    candidate_path = candidate_dir / f"low_price_two_leg_policy_candidate_{target_date}.json"
    wanted = {"schema", "target_date", "artifact_hash", "paired_economic_search"}
    report = _read_daily_history(report_path, wanted=wanted) or {}
    candidate = _read_json(candidate_path) or {}
    if (report.get("schema") not in {REPORT_SCHEMA, "low_price_two_leg_tuning_report_v9"} or report.get("target_date") != target_date
        or candidate.get("schema") != PAIRED_CANDIDATE_SCHEMA
        or candidate.get("source_report_schema") != report.get("schema")
        or report.get("artifact_hash") != candidate.get("source_report_artifact_hash")
        or report.get("paired_economic_search") != candidate.get("paired_economic_search")):
        return {"status": "source_gap", "source_date": target_date, "reason": "native_actual_candidate_generation_missing_or_mismatched", "runtime_effect": False}
    search = report["paired_economic_search"]
    return {"status": candidate["selection_status"], "source_date": target_date,
        "publication_date": candidate["publication_date"], "effective_date": candidate["effective_date"],
        "report_path": str(report_path), "report_artifact_hash": report["artifact_hash"],
        "candidate_path": str(candidate_path), "candidate_policy_hash": candidate["policy_hash"],
        "candidate_artifact_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        "selected_profile": search["selected_profile"], "selected_axis": search["selected_axis"],
        "policy_mutations": candidate["policy_mutations"],
        "stage_counts": search.get("stage_counts", {"research_status": "legacy_research_not_reported"}),
        "profiles": {pid: {**{key: value for key, value in proof.items() if key in {"disposition", "completed_actual_legs", "actual_source_valid_days", "actual_eligibility_passed", "research_admission_passed", "research_disposition", "promotion_disposition", "actual_held_legs", "promotion_blocking_reasons", "evidence_grade"}},
            "calibration_diagnostics": [{"axis": item["axis"], "baseline": _economic_brief(item["baseline"]), "challenger": _economic_brief(item["challenger"]), "comparison": item["comparison"], "evidence_role": item["evidence_role"],
                "carry_target_diagnostic": item.get("carry_target_diagnostic")} for item in proof.get("calibration_diagnostics", [])]}
            for pid, proof in search["profiles"].items()},
        "runtime_effect": False, "actual_order_submitted": False,
        "natural_preopen_consumption": "pending_scheduled_preopen"}


def _cached_paired_contexts(profile, source_date):
    from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import DEFAULT_SOURCE_CACHE_DIR, _load_source_cache
    from src.engine.monitoring.low_price_two_leg_entry_spot_research import build_day_contexts
    for directory in sorted(DEFAULT_SOURCE_CACHE_DIR.glob("????-??-??"), reverse=True):
        try:
            end = date.fromisoformat(directory.name)
        except ValueError:
            continue
        if end > source_date:
            continue
        cached = _load_source_cache(cache_dir=DEFAULT_SOURCE_CACHE_DIR, symbol=profile.symbol,
            start_date=CLEAN_BASELINE_DATE, end_date=end,
            expected_trading_day_count=len(_clean_trading_dates_through(end)))
        if cached is not None:
            return build_day_contexts(cached[0]), cached[1]["source_content_sha256"]
    return None


def durable_observation_manifest(target_date: str, source_quality_dir: Path) -> dict:
    """Final census first; stream only a declared native observation population."""
    import gzip
    audit = _read_json(source_quality_dir / f"observation_source_quality_audit_{target_date}.json") or {}
    source = audit.get("source") or {}
    expected = (source.get("audited_stage_counts") or {}).get("low_price_actual_economic_observation", 0)
    manifest = {"schema": "low_price_actual_capture_manifest_v1", "target_date": target_date,
        "source_path": source.get("pipeline_events"), "source_sha256": source.get("logical_content_sha256"),
        "source_generation": source.get("generation"), "expected_event_count": expected,
        "event_count": 0, "invalid_event_count": 0, "profiles": {}, "status": "source_gap"}
    if not expected:
        manifest["reason"] = "native_durable_observation_population_absent"
        return manifest
    raw = Path(source["pipeline_events"])
    if not raw.exists():
        raw = raw.with_name(raw.name + ".gz")
    before = raw.stat()
    observed_bars = {}
    opener = gzip.open if raw.suffix == ".gz" else open
    with opener(raw, "rb") as handle:
        for line in handle:
            if b'low_price_actual_economic_observation' not in line:
                continue
            event = json.loads(line)
            if event.get("stage") != "low_price_actual_economic_observation":
                continue
            manifest["event_count"] += 1
            fields = event.get("fields") or {}
            try:
                encoded = fields["observation_json"]
                body = json.loads(encoded)
                if (hashlib.sha256(encoded.encode()).hexdigest() != fields["observation_sha256"]
                    or body["schema"] != "low_price_actual_economic_observation_v1"
                    or body["logical_date"] != target_date or body["owner"] != "episode"
                    or body["profile_id"] != fields["profile_id"]):
                    raise ValueError("observation_lineage_invalid")
                profile = manifest["profiles"].setdefault(body["profile_id"], {"events": 0, "bar_evaluations": 0, "policy_hashes": [], "signal_policy_bindings": []})
                profile["events"] += 1
                if body.get("bar_source") and body.get("last_evaluated_bar"):
                    observed_bars.setdefault(body["profile_id"], set()).add(body["last_evaluated_bar"])
                    profile["bar_evaluations"] = len(observed_bars[body["profile_id"]])
                if body["policy_hash"] not in profile["policy_hashes"]:
                    profile["policy_hashes"].append(body["policy_hash"])
                signal = (body.get("signal_features") or {}).get("signal_bar")
                signal_policy = (body.get("signal_features") or {}).get("runtime_policy_hash")
                if signal and signal_policy == body["policy_hash"] and len(str(signal_policy)) == 64:
                    identity = f"{signal_policy}|{signal}"
                    if identity not in profile["signal_policy_bindings"]:
                        profile["signal_policy_bindings"].append(identity)
            except (KeyError, TypeError, ValueError):
                manifest["invalid_event_count"] += 1
    after = raw.stat()
    stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    manifest.update(status="pass" if stable and manifest["event_count"] == expected and not manifest["invalid_event_count"] else "source_gap",
        reason="native_capture_reconciled" if stable else "native_capture_generation_changed")
    return manifest


def actual_execution_confirmation(rows, result):
    """Reconcile baseline CF with full native broker terminal legs, never touches."""
    modeled = {episode.get("signal_at"): episode for episode in result["baseline"]["full"]["episodes"]}
    matched = 0
    for row in rows:
        if not row.get("eligible_for_tuning") or not row.get("attempted"):
            continue
        capture = row.get("durable_observation_capture") or {}
        if capture.get("status") != "pass" or capture.get("profile", {}).get("bar_evaluations", 0) == 0:
            return {"status": "source_gap", "reason": "actual_durable_observation_lineage_missing", "matched_legs": matched}
        features = row.get("signal_features") or {}
        signal_policy = features.get("runtime_policy_hash")
        identity = f"{signal_policy}|{features.get('signal_bar')}"
        if len(str(signal_policy)) != 64 or identity not in capture.get("profile", {}).get("signal_policy_bindings", []):
            return {"status": "source_gap", "reason": "actual_capture_signal_policy_binding_missing", "matched_legs": matched}
        episode = modeled.get(row.get("signal_features", {}).get("signal_bar"))
        if not episode:
            return {"status": "source_gap", "reason": "actual_baseline_signal_not_reproduced", "matched_legs": matched}
        if len(row.get("legs", [])) != 2 or len(episode.get("legs", [])) != 2:
            return {"status": "source_gap", "reason": "actual_two_leg_lineage_missing", "matched_legs": matched}
        for actual, model in zip(row.get("legs", []), episode.get("legs", [])):
            if not actual.get("completed") or actual.get("profit_price_source") not in {"broker_target_fill_price", "broker_fill_price"}:
                return {"status": "source_gap", "reason": "actual_full_target_terminal_missing", "matched_legs": matched}
            if (actual.get("quantity") != 10 or actual.get("buy_filled_qty") != 10
                or actual.get("target_filled_qty") != 10 or model.get("status") != "COMPLETE"
                or actual.get("fill_price") != model.get("entry_price")
                or actual.get("profit_exit_price") != model.get("target_price")):
                return {"status": "source_gap", "reason": "actual_baseline_execution_not_reproduced", "matched_legs": matched}
            matched += 1
    return {"status": "pass" if matched >= SAMPLE_FLOOR_COMPLETED_LEGS else "source_gap",
        "reason": "native_baseline_terminal_reconciled" if matched >= SAMPLE_FLOOR_COMPLETED_LEGS else "actual_prospective_execution_sample_missing",
        "matched_legs": matched, "evidence_role": "actual_broker_baseline_reproduction_only"}


def _economic_brief(outcome):
    return {key: value for key, value in outcome.items() if key in {
        "notional_weighted_ev_pct", "cost_adjusted_net_profit_krw_per_source_valid_observation_day", "source_valid_observation_days", "cost_pct", "custody_resolution_required", "realized_net_profit_krw", "completed_legs", "signal_episodes", "held_legs", "carry_in_held_legs", "observation_days", "no_fill_legs", "round_trip_cost_pct", "held_notional_krw", "capital_exposure_completed_bars", "worst_filled_max_adverse_excursion_pct"}}


def _paired_economic_search(report, *, context_loader=None, selection_dir=CANDIDATE_DIR):
    """Two existing axes, actual-conditioned; sealed prospective owner reused."""
    from src.engine.monitoring import research_closed_loop as loop
    from src.engine.monitoring import episode_prospective_research as prospective
    from src.engine.monitoring.low_price_two_leg_entry_spot_research import baseline_candidate, _evaluate_candidate_windows, paired_economics, _calibration_ready, day_replay_scope, _advance_carried_target_day
    from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import ResearchProfile
    source = date.fromisoformat(report["target_date"])
    binding = report["source_runtime_policy_binding"]
    result = {"contract": PAIRED_AUTHORITY_CONTRACT, "profiles": {}, "selected_profile": None,
        "selected_axis": None, "runtime_effect": False, "allowed_runtime_apply": False,
        "actual_order_submitted": False, "source_date": str(source), "frozen_selection": None}
    if source < date(2026, 9, 17):
        result["status"] = "historical_observation_only"
        return result
    fixed = _read_json(selection_dir / "low_price_two_leg_paired_selection.json")
    if fixed:
        revision = loop.validate_revision(fixed["candidate_revision"], owner="episode")
        if not loop.registered_revision(revision) or revision["lane_id"] != fixed["profile_id"] or fixed["selected_axis"] not in {"rolling_high_drawdown_pct", "rolling_low_proximity_pct"}:
            raise ValueError("paired_frozen_selection_invalid")
    previous_selection, reset_reason = None, None
    context_cache = {}
    if fixed and binding.get("status") == "ready":
        pid = fixed["profile_id"]
        live = profiles_for_target_date(source)[pid]
        policy = binding["policies"][pid]
        actual_profile = ResearchProfile(pid, live.symbol, live.name, live.session,
            replace(live.policy, **{key: policy[key] for key in ("rolling_high_drawdown_pct", "rolling_low_proximity_pct", "lookback_bars", "entry_valid_completed_bars", "target_ticks")}), "actual_existing_axis")
        if fixed["candidate_revision"]["baseline_parameters"] != baseline_candidate(actual_profile).public():
            previous_selection, reset_reason, fixed = fixed, "incumbent_parent_changed", None
        elif source.isoformat() > fixed["candidate_revision"]["holdout_dates"][-1]:
            loaded = (context_loader or _cached_paired_contexts)(actual_profile, source)
            context_cache[pid] = loaded
            if loaded:
                sealed = prospective.frozen_research({"profile_id": pid, "symbol": live.symbol}, profile=actual_profile, contexts=loaded[0], source_date=source)
                comparison = sealed.get("paired_economics") or {}
                if sealed["prospective_window"]["status"] == "ready" and comparison.get("economic_comparison_status") == "distinct_resolved_economic_pair" and not (comparison.get("economic_superiority_confirmed") and comparison.get("ev_uplift_pct_point", 0) >= MIN_NOTIONAL_EV_UPLIFT_PCT):
                    previous_selection, reset_reason, fixed = fixed, "mature_nonperforming_revision", None
    ranked = []
    for pid, window in report["windows"][POST_APPLY_WINDOW_NAME].items():
        actual = window["summary"]
        daily = report["daily"]["profiles"][pid]
        proof = {"profile_id": pid, "actual_eligibility_passed": False, "selected_axis": None,
            "completed_actual_legs": actual["broker_priced_completed_legs"], "actual_source_valid_days": actual["source_valid_observation_days"],
            "disposition": "hold_sample", "calibration_diagnostics": [],
            "actual_held_legs": actual["held_or_unresolved_legs"], "research_admission_passed": False,
            "research_disposition": "not_admitted", "promotion_disposition": "hold_sample",
            "promotion_blocking_reasons": [], "evidence_grade": "actual_source_diagnostic_only"}
        result["profiles"][pid] = proof
        if not report["source_quality_preflight"]["tuning_input_allowed"] or daily["source_quality"] != "pass" or binding.get("status") != "ready":
            proof["disposition"] = "source_gap"
            continue
        source_completed = [leg for row in window["rows"] if row.get("source_quality") == "pass"
            for leg in row.get("legs", []) if leg.get("completed") and leg.get("contract_valid")
            and leg.get("profit_price_source") in {"broker_target_fill_price", MANUAL_EXIT_PRICE_SOURCE}
            and _as_float(leg.get("net_profit_pct")) is not None]
        if not source_completed:
            proof["disposition"] = "source_gap" if any(row.get("source_quality") != "pass" or any(_as_int(leg.get("buy_filled_qty")) > 0 or _as_int(leg.get("fill_price")) > 0 for leg in row.get("legs", [])) for row in window["rows"]) else "valid_empty_no_fill"
            continue
        if actual["held_or_unresolved_legs"]:
            proof["promotion_blocking_reasons"].append("actual_inventory_custody")
        if actual["broker_priced_completed_legs"] < SAMPLE_FLOOR_COMPLETED_LEGS or actual["source_valid_observation_days"] < BOUNDED_MIN_OBSERVED_DAYS:
            proof["promotion_blocking_reasons"].append("actual_sample_floor")
        proof["actual_eligibility_passed"] = not proof["promotion_blocking_reasons"]
        if pid not in {"kakao_late_morning", "youngone_morning"} and (not fixed or fixed.get("profile_id") != pid):
            proof["disposition"] = "incumbent_preserved"
            proof["research_disposition"] = "outside_bounded_research_scope"
            continue
        if binding["policies"][pid]["quantity"] != 20:
            proof["disposition"] = "execution_source_gap_quantity_model"
            continue
        live = profiles_for_target_date(source)[pid]
        policy = binding["policies"][pid]
        profile = ResearchProfile(pid, live.symbol, live.name, live.session,
            replace(live.policy, **{k: policy[k] for k in ("rolling_high_drawdown_pct", "rolling_low_proximity_pct", "lookback_bars", "entry_valid_completed_bars", "target_ticks")}),
            "actual_existing_axis")
        if fixed and fixed.get("profile_id") != pid:
            proof["disposition"] = "incumbent_preserved"
            continue
        loaded = context_cache.get(pid) if pid in context_cache else (context_loader or _cached_paired_contexts)(profile, source)
        context_cache[pid] = loaded
        if loaded is None:
            proof["disposition"] = "execution_source_gap"
            continue
        contexts, content_sha = loaded
        proof["research_admission_passed"] = True
        proof["evidence_grade"] = "cached_bar_CF_not_native_execution"
        dates = sorted(day for day in contexts if CLEAN_BASELINE_DATE <= day <= source)
        if len(dates) < 46:
            proof["disposition"] = "hold_sample"
            continue
        baseline = baseline_candidate(profile)
        cal = dates[:-16]
        split = len(cal) // 2
        windows = [cal, cal[:split], cal[split:]]
        current = _evaluate_candidate_windows(baseline, contexts, windows) if not fixed else None
        bounds = policy_bounds_for_target_date(source)[pid]
        for axis, after in (() if fixed else (("rolling_high_drawdown_pct", bounds["drawdown_max"]), ("rolling_low_proximity_pct", bounds["near_low_min"]))):
            if getattr(baseline, axis) == after:
                continue
            challenger = replace(baseline, **{axis: after})
            outcome = _evaluate_candidate_windows(challenger, contexts, windows)
            comparison = paired_economics(current[0], outcome[0])
            diagnostic = {"axis": axis, "parameters": challenger.public(), "baseline": current[0],
                "challenger": outcome[0], "comparison": comparison,
                "evidence_role": "CF_calibration_unit_quantity_one_not_actual_PnL", "native_per_leg_quantity": 10,
                "calibration_sample_passed": _calibration_ready(*outcome),
                "calibration_dates": [str(day) for day in cal], "validation_usage": "calibration_only_no_holdout_read"}
            proof["calibration_diagnostics"].append(diagnostic)
            if comparison.get("economic_comparison_status") != "distinct_resolved_economic_pair":
                # Existing original-target carry model is a separate price-touch
                # diagnostic, never ranking, actual custody or promotion proof.
                with day_replay_scope(_advance_carried_target_day):
                    carry_baseline = _evaluate_candidate_windows(baseline, contexts, [cal])[0]
                    carry_challenger = _evaluate_candidate_windows(challenger, contexts, [cal])[0]
                diagnostic["carry_target_diagnostic"] = {"baseline": _economic_brief(carry_baseline),
                    "challenger": _economic_brief(carry_challenger), "comparison": paired_economics(carry_baseline, carry_challenger),
                    "evidence_role": "original_target_continuation_price_touch_CF_report_only",
                    "ranking_usage": False, "runtime_effect": False}
            if comparison["economic_superiority_confirmed"] and comparison["ev_uplift_pct_point"] >= MIN_NOTIONAL_EV_UPLIFT_PCT and _calibration_ready(*outcome):
                ranked.append((comparison["net_profit_uplift_krw_per_observation_day"], pid, axis, challenger.public(), baseline.public(), content_sha))
        comparisons = [item["comparison"] for item in proof["calibration_diagnostics"]]
        proof["disposition"] = ("self_comparison" if not comparisons else "measured_no_edge" if all(item.get("economic_comparison_status") == "distinct_resolved_economic_pair" for item in comparisons) else "hold_inventory_custody")
        if any(item["comparison"]["economic_superiority_confirmed"] for item in proof["calibration_diagnostics"]):
            proof["disposition"] = "hold_sample" if not any(item["calibration_sample_passed"] for item in proof["calibration_diagnostics"]) else "incumbent_preserved"
        if fixed and fixed.get("profile_id") == pid:
            revision = fixed["candidate_revision"]
            if revision.get("baseline_parameters") != baseline.public():
                proof["disposition"] = "source_gap_incumbent_parent_changed"
                continue
            frozen = prospective.frozen_research({"profile_id": pid, "symbol": live.symbol,
                "calibration_winner": {"parameters": revision["parameters"]}}, profile=profile, contexts=contexts, source_date=source)
            if frozen["candidate_revision"] != revision:
                fixed = {"profile_id": pid, "selected_axis": fixed["selected_axis"], "candidate_revision": frozen["candidate_revision"],
                    "supersedes_selection_sha256": loop.digest(fixed), "selection_reset_reason": frozen["candidate_revision"]["supersession_reason"]}
                revision = frozen["candidate_revision"]
            proof.update(candidate_revision=revision, prospective_result=frozen,
                selected_axis=fixed["selected_axis"], selected_parameters=revision["parameters"],
                baseline_policy_hash=policy_hash(binding["policies"]),
                disposition="hold_unused_holdout" if frozen["prospective_window"]["status"] != "ready" else "hold_execution_confirmation")
            if frozen["prospective_window"]["status"] == "ready":
                proof["execution_confirmation"] = {arm: prospective.execution_feasibility(frozen, source_date=source, arm=arm) for arm in ("baseline", "selected")}
                proof["capital_confirmation"] = paired_capital_confirmation(frozen, source_date=source)
                proof["actual_rows"] = [row for row in window["rows"] if row["target_date"] in revision["calibration_dates"] + revision["holdout_dates"]]
                proof["actual_execution_confirmation"] = actual_execution_confirmation(proof["actual_rows"], frozen)
                from src.trading.low_price_two_leg.preflight import default_authority_path
                authority = default_authority_path(live)
                proof["family_approval"] = {"path": str(authority), "sha256": hashlib.sha256(authority.read_bytes()).hexdigest() if authority.exists() else ""}
                if proof["actual_eligibility_passed"] and paired_promotion_ready(proof, source_date=source):
                    proof["disposition"] = "eligible_paired_policy"
                    result.update(selected_profile=pid, selected_axis=fixed["selected_axis"])
    if fixed:
        result["frozen_selection"] = fixed
    elif ranked:
        _, pid, axis, parameters, baseline, content_sha = max(ranked, key=lambda row: (row[0], row[1], row[2]))
        profile = profiles_for_target_date(source)[pid]
        actual_policy = binding["policies"][pid]
        actual_profile = ResearchProfile(pid, profile.symbol, profile.name, profile.session,
            replace(profile.policy, **{key: actual_policy[key] for key in ("rolling_high_drawdown_pct", "rolling_low_proximity_pct", "lookback_bars", "entry_valid_completed_bars", "target_ticks")}), "actual_existing_axis")
        contexts, _ = context_cache[pid]
        frozen = prospective.frozen_research({"profile_id": pid, "symbol": profile.symbol,
            "calibration_winner": {"parameters": parameters}}, profile=actual_profile, contexts=contexts, source_date=source)
        revision = frozen["candidate_revision"]
        if previous_selection and previous_selection["profile_id"] == pid and revision["revision_sha256"] == previous_selection["candidate_revision"]["revision_sha256"]:
            revision = loop.candidate_revision(symbol=profile.symbol, owner="episode", lane_id=pid,
                parameters=parameters, baseline_parameters=baseline, baseline_policy_id=pid,
                source_date=source, source_sha256=loop.digest([[bar.timestamp.isoformat(), bar.open_price, bar.high_price, bar.low_price, bar.close_price] for day in sorted(contexts) for bar in contexts[day].bars]),
                cost_sha256=loop.digest(canonical_cost_contract()), calibration_days=30, holdout_days=16,
                supersedes_revision_sha256=revision["revision_sha256"], supersession_reason=reset_reason)
        result["frozen_selection"] = {"profile_id": pid, "selected_axis": axis, "candidate_revision": revision}
        if previous_selection:
            result["frozen_selection"].update(supersedes_selection_sha256=loop.digest(previous_selection), selection_reset_reason=reset_reason)
        result["profiles"][pid]["disposition"] = "hold_unused_holdout"
    owner = _samsung_same_stage_owner(str(source), SAMSUNG_CANDIDATE_DIR)
    if result["selected_profile"] and owner["mutation_present"]:
        result["profiles"][result["selected_profile"]]["disposition"] = "hold_same_stage_owner"
        result.update(selected_profile=None, selected_axis=None)
    result["status"] = "paired_policy_selected" if result["selected_profile"] else "incumbent_preserved"
    for proof in result["profiles"].values():
        diagnostics = proof["calibration_diagnostics"]
        if diagnostics:
            proof["research_disposition"] = "research_tested" if all(item["comparison"].get("economic_comparison_status") == "distinct_resolved_economic_pair" for item in diagnostics) else "research_tested_model_custody_censored"
        elif proof["research_admission_passed"]:
            proof["research_disposition"] = "frozen_candidate_pending" if proof.get("candidate_revision") else "self_comparison_or_model_sample_gap"
        if proof["actual_held_legs"]:
            proof["promotion_disposition"] = "hold_actual_inventory_custody"
        elif "actual_sample_floor" in proof["promotion_blocking_reasons"]:
            proof["promotion_disposition"] = "hold_actual_sample"
        else:
            proof["promotion_disposition"] = "hold_model_inventory_custody" if proof["disposition"] == "hold_inventory_custody" else proof["disposition"]
        if proof["disposition"] == "hold_inventory_custody" and not proof["actual_held_legs"]:
            proof["disposition"] = "hold_model_inventory_custody"
        if proof["research_admission_passed"]:
            proof["promotion_blocking_reasons"].extend(["native_paired_execution_capital_and_authority_required"] if proof["promotion_disposition"] != "eligible_paired_policy" else [])
    proofs = list(result["profiles"].values())
    result["stage_counts"] = {"profiles": len(proofs), "research_admitted_profiles": sum(p["research_admission_passed"] for p in proofs),
        "calibration_tested_profiles": sum(bool(p["calibration_diagnostics"]) for p in proofs),
        "distinct_calibration_pairs": sum(len(p["calibration_diagnostics"]) for p in proofs),
        "resolved_calibration_pairs": sum(d["comparison"].get("economic_comparison_status") == "distinct_resolved_economic_pair" for p in proofs for d in p["calibration_diagnostics"]),
        "joint_improved_calibration_pairs": sum(d["comparison"].get("economic_superiority_confirmed", False) and (d["comparison"].get("ev_uplift_pct_point") or 0) >= MIN_NOTIONAL_EV_UPLIFT_PCT for p in proofs for d in p["calibration_diagnostics"]),
        "unused_holdout_waiting_profiles": sum(p["disposition"] == "hold_unused_holdout" for p in proofs),
        "actual_floor_flat_profiles": sum(p["actual_eligibility_passed"] for p in proofs),
        "promotion_selected_profiles": int(result["selected_profile"] is not None), "policy_mutations": int(result["selected_profile"] is not None)}
    return result


def build_candidate(
    report: dict,
    *,
    candidate_dir: Path = CANDIDATE_DIR,
    samsung_candidate_dir: Path = SAMSUNG_CANDIDATE_DIR,
) -> dict:
    source_date = date.fromisoformat(str(report["target_date"]))
    target_profiles = profiles_for_target_date(source_date)
    target_bounds = policy_bounds_for_target_date(source_date)
    binding = report.get("source_runtime_policy_binding") or {
        "status": "missing_baseline_only",
        "source_date": report["target_date"],
        "policies": baseline_policies_for_target_date(source_date),
    }
    prior = binding["policies"]
    selected_policies = {
        profile_id: dict(policy) for profile_id, policy in prior.items()
    }
    evaluations: dict[str, dict[str, Any]] = {}
    for profile_id in target_profiles:
        current = prior[profile_id]
        clean_window = report["windows"].get(
            POST_APPLY_WINDOW_NAME, report["windows"][CLEAN_WINDOW_NAME]
        )[profile_id]
        current_outcome = _axis_outcome(
            clean_window["rows"],
            min_drawdown=float(current["rolling_high_drawdown_pct"]),
            max_near_low=float(current["rolling_low_proximity_pct"]),
        )
        profile_inventory_clear = (
            clean_window["summary"]["held_or_unresolved_legs"] == 0
        )
        alternatives: list[tuple[str, float, float]] = []
        bounds = target_bounds[profile_id]
        if float(current["rolling_high_drawdown_pct"]) < bounds["drawdown_max"]:
            alternatives.append(
                (
                    "rolling_high_drawdown_pct",
                    bounds["drawdown_max"],
                    float(current["rolling_low_proximity_pct"]),
                )
            )
        if float(current["rolling_low_proximity_pct"]) > bounds["near_low_min"]:
            alternatives.append(
                (
                    "rolling_low_proximity_pct",
                    float(current["rolling_high_drawdown_pct"]),
                    bounds["near_low_min"],
                )
            )
        evaluated_alternatives = []
        for axis, drawdown, near_low in alternatives:
            clean_outcome = _axis_outcome(
                clean_window["rows"],
                min_drawdown=drawdown,
                max_near_low=near_low,
            )
            current_ev = current_outcome["notional_weighted_ev_pct"]
            candidate_ev = clean_outcome["notional_weighted_ev_pct"]
            ev_uplift = (
                float(candidate_ev) - float(current_ev)
                if candidate_ev is not None and current_ev is not None
                else None
            )
            current_net_per_day = current_outcome.get(
                "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
            )
            candidate_net_per_day = clean_outcome.get(
                "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
            )
            net_profit_uplift_per_day = (
                float(candidate_net_per_day) - float(current_net_per_day)
                if candidate_net_per_day is not None and current_net_per_day is not None
                else None
            )
            current_frequency = current_outcome.get(
                "attempted_episodes_per_source_valid_observation_day"
            )
            candidate_frequency = clean_outcome.get(
                "attempted_episodes_per_source_valid_observation_day"
            )
            frequency_retention_ratio = (
                float(candidate_frequency) / float(current_frequency)
                if candidate_frequency is not None
                and current_frequency is not None
                and float(current_frequency) > 0.0
                else None
            )
            ready = bool(
                report.get("target_date_is_krx_trading_day") is True
                and report["source_quality_preflight"]["tuning_input_allowed"]
                and report["daily"]["profiles"][profile_id].get("source_quality")
                == "pass"
                and profile_inventory_clear
                and clean_outcome["eligible_days"] >= BOUNDED_MIN_OBSERVED_DAYS
                and clean_outcome["completed_legs"] >= SAMPLE_FLOOR_COMPLETED_LEGS
                and clean_outcome["broker_priced_completed_legs"]
                >= SAMPLE_FLOOR_COMPLETED_LEGS
                and clean_outcome["held_or_unresolved_legs"] == 0
                and candidate_ev is not None
                and current_ev is not None
                and float(candidate_ev) > 0
                and ev_uplift is not None
                and ev_uplift >= MIN_NOTIONAL_EV_UPLIFT_PCT
                and net_profit_uplift_per_day is not None
                and net_profit_uplift_per_day > 1e-9
            )
            evaluated_alternatives.append(
                {
                    "axis": axis,
                    "resulting_drawdown_pct": drawdown,
                    "resulting_near_low_pct": near_low,
                    "clean_baseline_cumulative_outcome": clean_outcome,
                    "current_policy_outcome": current_outcome,
                    "notional_ev_uplift_pct": ev_uplift,
                    "cost_adjusted_net_profit_uplift_krw_per_source_valid_observation_day": (
                        net_profit_uplift_per_day
                    ),
                    "attempted_episode_frequency_retention_ratio": (
                        frequency_retention_ratio
                    ),
                    "ready": False,
                    "diagnostic_economic_conditions_passed": ready,
                    "decision_authority": "observed_signal_subset_diagnostic_only",
                    "allowed_runtime_apply": False,
                    "condition_feasibility": (
                        "hold_source_quality"
                        if not report["source_quality_preflight"][
                            "tuning_input_allowed"
                        ]
                        or report["daily"]["profiles"][profile_id].get("source_quality")
                        != "pass"
                        else (
                            "hold_inventory_custody"
                            if not profile_inventory_clear
                            else (
                                "hold_source_gap_causal_path_required"
                                if ready
                                else (
                                    "hold_sample"
                                    if clean_outcome["broker_priced_completed_legs"]
                                    < SAMPLE_FLOOR_COMPLETED_LEGS
                                    or clean_outcome["eligible_days"]
                                    < BOUNDED_MIN_OBSERVED_DAYS
                                    else "hold_no_edge_in_observed_subset"
                                )
                            )
                        )
                    ),
                }
            )
        evaluations[profile_id] = {
            "current_policy": current,
            "current_clean_baseline_cumulative_outcome": current_outcome,
            "profile_inventory_clear": profile_inventory_clear,
            "alternatives": evaluated_alternatives,
        }
    same_stage_owner = _samsung_same_stage_owner(
        report["target_date"], samsung_candidate_dir
    )
    search = report.get("paired_economic_search") or {}
    selected_pid = search.get("selected_profile")
    if selected_pid and not same_stage_owner["mutation_present"]:
        proof = search["profiles"][selected_pid]
        if paired_promotion_ready(proof, source_date=source_date):
            selected_policies[selected_pid][proof["selected_axis"]] = proof["selected_parameters"][proof["selected_axis"]]
        else:
            raise ValueError("paired_selection_proof_changed_before_publication")
    elif selected_pid:
        raise ValueError("paired_same_stage_owner_changed_before_publication")
    mutations = policy_mutations_between(prior, selected_policies)
    if len(mutations) > 1:
        raise ValueError("same_stage_multiple_axis_candidate_forbidden")
    profiles = {}
    for profile_id in target_profiles:
        profiles[profile_id] = {
            "selection_status": "paired_economic_policy_selected" if profile_id == selected_pid else "carry_forward_profile_policy",
            "selected_axis": search.get("selected_axis") if profile_id == selected_pid else None,
            "policy": selected_policies[profile_id],
            "evaluation": evaluations[profile_id],
            "allowed_runtime_apply": True,
        }
    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "source_date": report["target_date"],
        "generated_at_kst": report["generated_at_kst"],
        "source_report": REPORT_TYPE,
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": report["clean_tuning_baseline_date"],
        "source_quality_preflight": report["source_quality_preflight"],
        "policy_hash": policy_hash(selected_policies),
        "policy_mutations": mutations,
        "source_runtime_policy_binding": binding,
        "evaluation_authority_contract": SUBSET_AUTHORITY_CONTRACT,
        "decision": "carry_actual_policy_subset_promotion_retired",
        "same_stage_owner_guard": same_stage_owner,
        "profiles": profiles,
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "rollback": "next_preopen_exact_date_artifact_or_verified_baseline",
        "forbidden_uses": METRIC_CONTRACT["forbidden_uses"],
    }
    if source_date >= date(2026, 9, 17):
        publication = datetime.fromisoformat(report["generated_at_kst"]).astimezone(KST).date()
        candidate.update(schema=PAIRED_CANDIDATE_SCHEMA, publication_date=str(publication),
            effective_date=str(next_policy_date(source_date, publication)),
            evaluation_authority_contract=PAIRED_AUTHORITY_CONTRACT, paired_economic_search=search,
            selection_status="paired_economic_policy_selected" if mutations else "incumbent_preserved",
            decision="paired_economic_policy_selected" if mutations else "carry_actual_policy_paired_search_incomplete")
    if report.get("artifact_hash"):
        candidate.update(
            {
                "source_report_path": report.get("artifact_path"),
                "source_report_artifact_hash": report.get("artifact_hash"),
                "source_quality_source_sha256": (
                    report.get("source_quality_preflight") or {}
                ).get("source_sha256"),
            }
        )
    return candidate


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


def _render_actual_markdown(report: dict, candidate: dict) -> str:
    cost_model = report["cost_model"]
    reconciliation = cost_model["broker_realized_reconciliation"]
    lines = [
        f"# Low-price two-leg tuning — {report['target_date']}",
        "",
        "- Decision: carry the actually applied policy; observed-signal subsets are diagnostic only and cannot promote new tightening.",
        "- Economic replay owner: low_price_two_leg_expanded_candidate_research / existing_axis_economic_replay (same two filters, source-only, no new live authority).",
        "- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.",
        (
            "- Cost model: exact ka10073 only on unique identity match "
            f"(matched={reconciliation['matched']}, fallback={reconciliation['fallback']}); "
            f"otherwise fixed {cost_model['fixed_round_trip_cost_pct']}%."
        ),
        f"- Clean-baseline actual observations: {report['clean_baseline_window']['available_actual_observation_date_count']}/{report['clean_baseline_window']['expected_trading_date_count']} trading dates; missing dates are coverage only and are not imputed.",
        "",
        "- Main table uses the contiguous current applied-policy epoch; all-version totals remain audit-only in JSON. Missing realized EV is null, never zero.",
        "| Profile | Symbol | Session | Daily status | Post-apply attempts | Complete legs | Manual exits/losses | Held/unresolved | Realized EV |",
        "|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for profile_id, row in report["daily"]["profiles"].items():
        summary = report["windows"].get(
            POST_APPLY_WINDOW_NAME, report["windows"][CLEAN_WINDOW_NAME]
        )[profile_id]["summary"]
        lines.append(
            f"| {profile_id} | {row['symbol']} | {row['session']} | "
            f"{row['source_quality']} | {summary['attempted_episodes']} | "
            f"{summary['completed_legs']} | "
            f"{summary['manual_exit_completed_legs']}/"
            f"{summary['manual_exit_loss_legs']} | "
            f"{summary['held_or_unresolved_legs']} | "
            f"{summary['notional_weighted_ev_pct']} |"
        )
    lines.extend(["", "## Next PREOPEN candidate", ""])
    if candidate["policy_mutations"]:
        item = candidate["policy_mutations"][0]
        lines.append(
            f"- Selected `{item['profile_id']}` `{item['axis']}`: "
            f"{item['before']} -> {item['after']}."
        )
    else:
        lines.append("- No profile/axis mutation; carry forward current policies.")
    lines.append("")
    return "\n".join(lines)


def render_markdown(report: dict, candidate: dict) -> str:
    text = _render_actual_markdown(report, candidate)
    lines = ["", "## Actual-conditioned paired economic search", "",
        f"Selection: {candidate.get('selection_status', candidate.get('decision'))}; source={report['target_date']}; effective={candidate.get('effective_date')}",
        f"Stages: {report.get('paired_economic_search', {}).get('stage_counts', {})}",
        "", "| Profile | Research / Promotion | Actual completed legs / days / held | Calibration distinct comparisons |", "|---|---|---|---|"]
    for pid, proof in (report.get("paired_economic_search") or {}).get("profiles", {}).items():
        diagnostics = proof["calibration_diagnostics"]
        lines.append(f"| {pid} | {proof.get('research_disposition')} / {proof.get('promotion_disposition', proof['disposition'])} | {proof['completed_actual_legs']} / {proof['actual_source_valid_days']} / {proof.get('actual_held_legs')} | {len(diagnostics)} |")
        for item in diagnostics:
            comp = item["comparison"]
            lines.append(f"| {pid}/{item['axis']} | CF calibration only | Delta EV={comp.get('ev_uplift_pct_point')} pp | Delta net/day={comp.get('net_profit_uplift_krw_per_observation_day')} KRW; confirmed={comp.get('economic_superiority_confirmed')} |")
            for role, diagnostic in (("conservative CF unit quantity1", item), ("original-target price-touch CF report-only", item.get("carry_target_diagnostic"))):
                if diagnostic:
                    lines.append(f"- {pid}/{item['axis']} {role}: baseline={_economic_brief(diagnostic['baseline'])}; challenger={_economic_brief(diagnostic['challenger'])}; comparison={diagnostic['comparison']}")
    lines.append(f"\nManual receipt projection (historical recovery, not new profit): {report.get('manual_exit_history_reconciliation', {})}")
    return text + "\n".join(lines) + "\n"


def _write_outputs_locked(
    report: dict, candidate: dict, *, output_dir: Path, candidate_dir: Path
) -> tuple[Path, Path, Path]:
    stem = f"{REPORT_TYPE}_{report['target_date']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    candidate_path = candidate_dir / (
        f"low_price_two_leg_policy_candidate_{report['target_date']}.json"
    )
    if candidate.get("schema") == PAIRED_CANDIDATE_SCHEMA:
        for applied_file in APPLIED_DIR.glob("low_price_two_leg_policy_*.json"):
            applied = _read_json(applied_file) or {}
            if applied.get("source_candidate") == str(candidate_path) and _read_json(candidate_path) != candidate:
                raise ValueError("candidate_already_consumed_by_frozen_applied_policy")
    search = report.get("paired_economic_search") or {}
    fixed = search.get("frozen_selection")
    if fixed:
        from src.engine.monitoring import research_closed_loop as loop
        pointer = candidate_dir / "low_price_two_leg_paired_selection.json"
        existing = _read_json(pointer)
        if existing is not None and existing != fixed:
            if fixed.get("supersedes_selection_sha256") != loop.digest(existing) or fixed.get("selection_reset_reason") not in {"incumbent_parent_changed", "mature_nonperforming_revision", "source_or_cost_correction"}:
                raise ValueError("paired_selection_frozen_conflict")
        stored = loop.freeze_candidate(fixed["candidate_revision"])
        if stored != fixed["candidate_revision"]:
            raise ValueError("paired_candidate_revision_frozen_conflict")
        atomic_write_json(pointer, fixed)
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(md_path, render_markdown(report, candidate))
    atomic_write_json(candidate_path, candidate)
    return json_path, md_path, candidate_path


def write_outputs(report, candidate, *, output_dir, candidate_dir):
    import fcntl
    DEFAULT_STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (DEFAULT_STATE_DIR / "policy_apply.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _write_outputs_locked(report, candidate, output_dir=output_dir, candidate_dir=candidate_dir)


def _live_realized_pnl_loader() -> RealizedPnlLoader:
    token: str | None = None
    last_request_monotonic = 0.0

    def load(trade_date: str, symbol: str) -> list[dict[str, Any]]:
        nonlocal token, last_request_monotonic
        if token is None:
            token = kiwoom_utils.get_kiwoom_token()
        if not token:
            raise RuntimeError("kiwoom_token_unavailable")
        elapsed = time.monotonic() - last_request_monotonic
        if last_request_monotonic and elapsed < 0.25:
            time.sleep(0.25 - elapsed)
        try:
            return load_realized_pnl_ka10073(token, trade_date, symbol)
        finally:
            last_request_monotonic = time.monotonic()

    return load


def refresh_receipt_projection(
    *, target_date: str, state_dir: Path, output_dir: Path
) -> dict:
    """Refresh missing receipt metadata without re-querying or recalculating economics."""
    path = output_dir / f"{REPORT_TYPE}_{target_date}.json"
    original = path.read_bytes()
    report = json.loads(original)
    if (
        report.get("schema") != REPORT_SCHEMA
        or report.get("target_date") != target_date
        or report.get("artifact_hash") != report_artifact_hash(report)
    ):
        raise ValueError("receipt_projection_parent_contract_invalid")
    sources = []
    for profile_id, row in report["daily"]["profiles"].items():
        manual_legs = [
            leg
            for leg in row.get("legs", [])
            if leg.get("exit_fill_source") == MANUAL_EXIT_FILL_SOURCE
        ]
        if not manual_legs:
            continue
        state_path = state_dir / f"{profile_id}_state.json"
        raw_bytes = state_path.read_bytes()
        state = json.loads(raw_bytes)
        if state.get("trade_date") != target_date:
            raise ValueError("receipt_projection_state_date_mismatch")
        raw_legs = state.get("legs") or []
        for leg in manual_legs:
            matches = [item for item in raw_legs if item.get("leg_id") == leg["leg_id"]]
            if len(matches) != 1:
                raise ValueError("receipt_projection_leg_identity_mismatch")
            projected = _sanitize_leg(matches[0], report["cost_pct"])
            if any(
                leg.get(key) != value
                for key, value in projected.items()
                if key != "manual_exit_receipt"
            ):
                raise ValueError("receipt_projection_nonmetadata_state_changed")
            leg["manual_exit_receipt"] = projected["manual_exit_receipt"]
        sources.append(
            {"path": str(state_path), "sha256": hashlib.sha256(raw_bytes).hexdigest()}
        )
    report["receipt_metadata_projection"] = {
        "schema": "low_price_manual_receipt_metadata_projection_v1",
        "parent_sha256": hashlib.sha256(original).hexdigest(),
        "source_date": target_date,
        "state_sources": sources,
        "economics_recomputed": False,
        "broker_calls": 0,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    report["generated_at_kst"] = datetime.now(tz=KST).isoformat(timespec="seconds")
    report["artifact_hash"] = report_artifact_hash(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=CANDIDATE_DIR)
    parser.add_argument("--source-quality-dir", type=Path, default=SOURCE_QUALITY_DIR)
    parser.add_argument("--applied-policy-dir", type=Path, default=APPLIED_DIR)
    parser.add_argument("--cost-pct", type=float, default=DEFAULT_ROUND_TRIP_COST_PCT)
    parser.add_argument("--skip-broker-realized-pnl", action="store_true")
    parser.add_argument("--refresh-receipts-only", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = (
        refresh_receipt_projection(
            target_date=args.target_date,
            state_dir=args.state_dir,
            output_dir=args.output_dir,
        )
        if args.refresh_receipts_only
        else build_report(
            target_date=args.target_date,
            state_dir=args.state_dir,
            output_dir=args.output_dir,
            source_quality_dir=args.source_quality_dir,
            applied_dir=args.applied_policy_dir,
            cost_pct=args.cost_pct,
            paired_selection_dir=args.candidate_dir,
            realized_pnl_loader=(
                None if args.skip_broker_realized_pnl else _live_realized_pnl_loader()
            ),
        )
    )
    candidate = build_candidate(report, candidate_dir=args.candidate_dir)
    valid, reason = validate_candidate(candidate, source_report=report)
    if not valid:
        raise ValueError(reason)
    paths = write_outputs(
        report,
        candidate,
        output_dir=args.output_dir,
        candidate_dir=args.candidate_dir,
    )
    if args.print_summary:
        print(
            json.dumps(
                {
                    "target_date": args.target_date,
                    "report_path": str(paths[0]),
                    "markdown_path": str(paths[1]),
                    "candidate_path": str(paths[2]),
                    "policy_mutations": candidate["policy_mutations"],
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
