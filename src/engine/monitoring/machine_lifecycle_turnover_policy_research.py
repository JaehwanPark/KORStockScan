"""Build source-only rolling paired turnover-policy research.

The producer compares each owner's current completed lifecycle with a single
target-timeout axis on the same microstructure path.  It can create a policy
intake candidate only after the rolling source-quality and downside gates pass.
The candidate deliberately has no registered runtime family or apply authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.utils.market_day import is_krx_trading_day

REPORT_SCHEMA = "machine_lifecycle_turnover_policy_research_v1"
CANDIDATE_SCHEMA = "machine_microstructure_policy_promotion_candidate_v1"
ATTRIBUTION_SCHEMA = "machine_microstructure_attribution_v1"
OBJECTIVE_FOLLOWUP_ID = "machine_lifecycle_turnover_policy_research_v1"
OBJECTIVE_BINDING_SCHEMA = "machine_fast_lifecycle_objective_candidate_binding_v1"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
TIMEOUT_AXIS_VALUES_SEC = (60, 120, 180)
ROLLING_PAIRED_LIFECYCLE_FLOORS = {"5d": 5, "10d": 10, "20d": 20}
DECISION_ROLES = {
    "counterfactual_calibration_entry",
    "actual_widget_entry_signal",
    "episode_signal_bar",
    "prospective_widget_research_entry",
    "prospective_episode_research_signal",
}
COST_PROVENANCE_ALLOWLIST = {
    "widget_auto_trade_policy_calibration.round_trip_cost_pct",
    "widget_comparison_cost.effective_dated_contract",
    "low_price_two_leg_tuning.cost_pct",
    "low_price_two_leg_expanded_candidate_research.cost_pct",
}

METRIC_CONTRACT = {
    "metric_role": "source_only_rolling_paired_lifecycle_turnover_policy_research",
    "decision_authority": "postclose_source_only_candidate_research",
    "window_policy": "paired_unique_lifecycle_rolling_5_10_20_krx_trading_days",
    "sample_floor": {
        "observed_trading_days_per_owner_scope": 5,
        "policy_eligible_unique_lifecycles_per_owner_scope": 20,
        "rolling_paired_complete_lifecycles": dict(ROLLING_PAIRED_LIFECYCLE_FLOORS),
        "bbo_complete_rate_pct": 95.0,
        "depth_window_coverage_pct": 90.0,
        "invalid_contract_row_count": 0,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": [
        "clean_baseline_exact_date_attribution",
        "same_owner_symbol_session_unique_lifecycle_pair",
        "matched_policy_eligible_decision_and_execution_anchors",
        "past_only_fillable_bid_timeout_snapshot",
        "explicit_owner_round_trip_cost",
        "current_and_candidate_realized_pair_for_ev",
        "held_and_right_censored_are_not_zero_imputed",
    ],
    "forbidden_uses": [
        "same_day_or_intraday_runtime_mutation",
        "unregistered_runtime_family_apply",
        "broker_order_submission_or_cancellation",
        "target_timeout_cooldown_cap_quantity_or_reentry_mutation",
        "gross_no_slippage_as_policy_authority",
        "manual_control_exclusion_as_collection_or_evaluation_filter",
        "provider_bot_cap_hard_safety_or_broker_guard_change",
    ],
}

AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _p10(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * 0.10) - 1)
    return ordered[index]


def _krx_window_start(target_day: date, trading_day_count: int) -> date:
    current = target_day
    remaining = trading_day_count - 1
    while remaining > 0:
        current -= timedelta(days=1)
        if is_krx_trading_day(current):
            remaining -= 1
    return current


def _advance_krx_trading_days(start_day: date, trading_day_count: int) -> date:
    current = start_day
    remaining = trading_day_count
    while remaining > 0:
        current += timedelta(days=1)
        if is_krx_trading_day(current):
            remaining -= 1
    return current


def _direct_anchor_results(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    consumers = report.get("consumers")
    if not isinstance(consumers, Mapping):
        return []
    results: list[dict[str, Any]] = []
    for consumer_name, collection_name in (
        ("widget_postclose_tuning", "symbols"),
        ("episode_machine_postclose_tuning", "profiles"),
    ):
        consumer = consumers.get(consumer_name)
        rows = consumer.get(collection_name) if isinstance(consumer, Mapping) else None
        if not isinstance(rows, Mapping):
            continue
        for row in rows.values():
            anchors = row.get("anchor_results") if isinstance(row, Mapping) else None
            if isinstance(anchors, list):
                results.extend(
                    dict(anchor) for anchor in anchors if isinstance(anchor, Mapping)
                )
    return results


def _valid_attribution_report(
    payload: Mapping[str, Any], *, expected_day: date | None = None
) -> tuple[date | None, list[str]]:
    errors: list[str] = []
    if payload.get("schema") != ATTRIBUTION_SCHEMA:
        errors.append("attribution_schema_invalid")
    try:
        target_day = date.fromisoformat(str(payload.get("target_date") or ""))
    except ValueError:
        target_day = None
        errors.append("attribution_target_date_invalid")
    if expected_day is not None and target_day != expected_day:
        errors.append("attribution_target_date_mismatch")
    if target_day is not None and (
        target_day < CLEAN_BASELINE_DATE or not is_krx_trading_day(target_day)
    ):
        errors.append("attribution_target_date_not_clean_krx_day")
    if payload.get("clean_baseline_allowed") is not True:
        errors.append("attribution_clean_baseline_not_allowed")
    authority = payload.get("authority")
    if not isinstance(authority, Mapping) or any(
        authority.get(field) is not expected for field, expected in AUTHORITY.items()
    ):
        errors.append("attribution_authority_invalid")
    if not isinstance(payload.get("consumers"), Mapping):
        errors.append("attribution_consumers_missing")
    rolling_source_contract = payload.get("rolling_policy_source_contract")
    if (
        not isinstance(rolling_source_contract, Mapping)
        or rolling_source_contract.get("ready") is not True
    ):
        errors.append("rolling_policy_source_contract_not_ready")
    return target_day, errors


def _load_reports(
    *,
    current_report: Mapping[str, Any],
    report_dir: Path,
    target_day: date,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_day: dict[date, dict[str, Any]] = {}
    exclusions: list[dict[str, Any]] = []
    for path in sorted(report_dir.glob("machine_microstructure_attribution_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            exclusions.append({"path": str(path), "reason": "unreadable_json"})
            continue
        if not isinstance(payload, dict):
            exclusions.append({"path": str(path), "reason": "root_not_object"})
            continue
        source_day, errors = _valid_attribution_report(payload)
        if source_day is None or source_day > target_day or errors:
            exclusions.append(
                {
                    "path": str(path),
                    "source_date": source_day.isoformat() if source_day else None,
                    "reason": ",".join(errors) if errors else "future_source_date",
                }
            )
            continue
        if source_day in by_day:
            exclusions.append(
                {
                    "path": str(path),
                    "source_date": source_day.isoformat(),
                    "reason": "duplicate_source_date",
                }
            )
            continue
        by_day[source_day] = payload
    current_day, current_errors = _valid_attribution_report(
        current_report, expected_day=target_day
    )
    if current_day is None or current_errors:
        exclusions.append(
            {
                "path": "in_memory_current_report",
                "source_date": target_day.isoformat(),
                "reason": ",".join(current_errors) or "invalid_current_report",
            }
        )
    else:
        by_day[current_day] = dict(current_report)
    return [by_day[key] for key in sorted(by_day)], exclusions


def _cohort_key(anchor: Mapping[str, Any]) -> tuple[str, str, str, str] | None:
    values = tuple(
        str(anchor.get(field) or "").strip()
        for field in ("owner", "scope_id", "symbol", "session")
    )
    if any(not value for value in values):
        return None
    return values  # type: ignore[return-value]


def _weighted_average(values: Iterable[tuple[float, float]]) -> float | None:
    pairs = [(value, weight) for value, weight in values if weight > 0]
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0:
        return None
    return sum(value * weight for value, weight in pairs) / denominator


def _anchor_policy_eligible(anchor: Mapping[str, Any]) -> bool:
    return anchor.get("micro_tuning_input_allowed") is True


def _anchor_held_diagnostic_eligible(anchor: Mapping[str, Any]) -> bool:
    outcome = anchor.get("owner_outcome")
    return bool(
        anchor.get("owner") == "episode"
        and anchor.get("micro_context_status") == "matched"
        and anchor.get("owner_lifecycle_contract_valid") is not False
        and anchor.get("owner_policy_tuning_eligible") is False
        and anchor.get("owner_source_quality") == "gap"
        and anchor.get("actual_order_submitted") is True
        and (not isinstance(outcome, Mapping) or outcome.get("realized") is not True)
    )


def _counterfactual_leg(
    anchor: Mapping[str, Any], *, timeout_sec: int
) -> dict[str, Any]:
    metrics = anchor.get("metrics")
    outcome = anchor.get("owner_outcome")
    if not isinstance(metrics, Mapping) or not isinstance(outcome, Mapping):
        return {"eligible": False, "reason": "execution_metrics_or_outcome_missing"}
    reference = _finite(metrics.get("reference_price")) or _finite(
        anchor.get("anchor_price")
    )
    cost_pct = _finite(anchor.get("owner_round_trip_cost_pct"))
    cost_provenance = str(anchor.get("owner_round_trip_cost_provenance") or "").strip()
    notional = _finite(outcome.get("entry_notional_krw"))
    if notional is None:
        notional = reference if anchor.get("owner") == "widget" else None
    if (
        reference is None
        or reference <= 0
        or cost_pct is None
        or cost_pct < 0
        or cost_provenance not in COST_PROVENANCE_ALLOWLIST
        or notional is None
        or notional <= 0
    ):
        return {"eligible": False, "reason": "reference_cost_or_notional_missing"}

    target_touch = metrics.get("fillable_owner_target_touch")
    touch_ms = (
        _finite(target_touch.get("time_ms"))
        if isinstance(target_touch, Mapping) and target_touch.get("touched") is True
        else None
    )
    target_return_bps = (
        _finite(target_touch.get("gross_return_bps"))
        if isinstance(target_touch, Mapping)
        else None
    )
    owner_target_price = _finite(anchor.get("owner_target_price"))
    expected_target_return_bps = (
        (owner_target_price / reference - 1.0) * 10000.0
        if owner_target_price is not None and owner_target_price > 0
        else None
    )
    target_required_quantity = (
        _finite(target_touch.get("required_exit_quantity"))
        if isinstance(target_touch, Mapping)
        else None
    )
    target_available_quantity = (
        _finite(target_touch.get("available_best_bid_quantity"))
        if isinstance(target_touch, Mapping)
        else None
    )
    if (
        touch_ms is not None
        and 0 <= touch_ms <= timeout_sec * 1000
        and target_return_bps is not None
        and expected_target_return_bps is not None
        and abs(target_return_bps - expected_target_return_bps) <= 0.01
        and isinstance(target_touch, Mapping)
        and target_touch.get("depth_backed") is True
        and target_required_quantity is not None
        and target_required_quantity > 0
        and target_available_quantity is not None
        and target_available_quantity >= target_required_quantity
    ):
        candidate_gross_bps = target_return_bps
        candidate_holding_sec = touch_ms / 1000.0
        candidate_exit_source = "fillable_owner_target_touch"
    else:
        horizons = metrics.get("fillable_bid_exit_horizons")
        horizon = (
            horizons.get(str(timeout_sec)) if isinstance(horizons, Mapping) else None
        )
        candidate_gross_bps = (
            _finite(horizon.get("gross_return_bps"))
            if isinstance(horizon, Mapping) and horizon.get("observed") is True
            else None
        )
        observed_offset_ms = (
            _finite(horizon.get("observation_offset_ms"))
            if isinstance(horizon, Mapping)
            else None
        )
        quote_age_ms = (
            _finite(horizon.get("quote_age_from_horizon_ms"))
            if isinstance(horizon, Mapping)
            else None
        )
        bid_price = (
            _finite(horizon.get("bid_price")) if isinstance(horizon, Mapping) else None
        )
        expected_bid_return_bps = (
            (bid_price / reference - 1.0) * 10000.0
            if bid_price is not None and bid_price > 0
            else None
        )
        required_quantity = (
            _finite(horizon.get("required_exit_quantity"))
            if isinstance(horizon, Mapping)
            else None
        )
        available_quantity = (
            _finite(horizon.get("available_best_bid_quantity"))
            if isinstance(horizon, Mapping)
            else None
        )
        if (
            candidate_gross_bps is None
            or observed_offset_ms is None
            or not 0 <= observed_offset_ms <= timeout_sec * 1000
            or quote_age_ms is None
            or not 0 <= quote_age_ms <= 5000
            or expected_bid_return_bps is None
            or abs(candidate_gross_bps - expected_bid_return_bps) > 0.01
            or not isinstance(horizon, Mapping)
            or horizon.get("depth_backed") is not True
            or required_quantity is None
            or required_quantity <= 0
            or available_quantity is None
            or available_quantity < required_quantity
        ):
            return {"eligible": False, "reason": "fillable_timeout_bid_missing"}
        # The quote is a past-only price observation for the timeout decision.
        # Capital remains occupied through the configured timeout boundary even
        # when the freshest eligible quote arrived a few seconds earlier.
        candidate_holding_sec = float(timeout_sec)
        candidate_exit_source = "past_only_fillable_bid_at_timeout"
    if candidate_holding_sec <= 0:
        return {"eligible": False, "reason": "candidate_holding_duration_invalid"}

    candidate_gross_pct = candidate_gross_bps / 100.0
    candidate_net_pct = candidate_gross_pct - cost_pct
    current_net_pct = _finite(outcome.get("cost_aware_net_return_pct"))
    current_holding_ms = _finite(outcome.get("holding_duration_ms"))
    current_realized = bool(
        outcome.get("realized") is True
        and current_net_pct is not None
        and current_holding_ms is not None
        and current_holding_ms > 0
    )
    return {
        "eligible": True,
        "candidate_exit_source": candidate_exit_source,
        "round_trip_cost_pct": cost_pct,
        "round_trip_cost_provenance": cost_provenance,
        "entry_notional_krw": round(notional, 6),
        "current_realized": current_realized,
        "current_net_return_pct": current_net_pct if current_realized else None,
        "current_holding_sec": (
            current_holding_ms / 1000.0 if current_realized else None
        ),
        "current_net_profit_krw": (
            round(notional * current_net_pct / 100.0, 6)
            if current_realized and current_net_pct is not None
            else None
        ),
        "candidate_realized": True,
        "candidate_gross_return_pct": round(candidate_gross_pct, 6),
        "candidate_net_return_pct": round(candidate_net_pct, 6),
        "candidate_holding_sec": round(candidate_holding_sec, 6),
        "candidate_net_profit_krw": round(notional * candidate_net_pct / 100.0, 6),
        "candidate_capital_occupied_krw_seconds": round(
            notional * candidate_holding_sec, 6
        ),
    }


def _lifecycle_units(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    try:
        source_date = date.fromisoformat(str(report.get("target_date") or ""))
    except ValueError:
        return []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for anchor in _direct_anchor_results(report):
        lifecycle_id = str(anchor.get("lifecycle_id") or "").strip()
        if lifecycle_id:
            grouped[lifecycle_id].append(anchor)
    units: list[dict[str, Any]] = []
    for lifecycle_id, anchors in grouped.items():
        decision_anchors = [
            anchor
            for anchor in anchors
            if anchor.get("anchor_role") in DECISION_ROLES
            and anchor.get("lifecycle_stage") == "entry"
        ]
        if len(decision_anchors) != 1:
            continue
        decision_anchor = decision_anchors[0]
        cohort = _cohort_key(decision_anchor)
        if (
            cohort is None
            or decision_anchor.get("micro_context_status") != "matched"
            or decision_anchor.get("owner_lifecycle_contract_valid") is False
            or not (
                _anchor_policy_eligible(decision_anchor)
                or _anchor_held_diagnostic_eligible(decision_anchor)
            )
        ):
            continue
        owner = cohort[0]
        if owner == "episode":
            execution_anchors = [
                anchor
                for anchor in anchors
                if anchor.get("anchor_role")
                in {
                    "episode_buy_fill_confirmed",
                    "prospective_episode_research_buy_fill",
                }
            ]
        elif decision_anchor.get("anchor_role") == "actual_widget_entry_signal":
            execution_anchors = [
                anchor
                for anchor in anchors
                if anchor.get("anchor_role") == "actual_widget_entry_fill_reconciled"
                and anchor.get("execution_order_role") == "ENTRY_BUY"
            ]
        else:
            execution_anchors = [decision_anchor]
        if not execution_anchors or any(
            anchor.get("micro_context_status") != "matched"
            or anchor.get("owner_lifecycle_contract_valid") is False
            or not (
                _anchor_policy_eligible(anchor)
                or _anchor_held_diagnostic_eligible(anchor)
            )
            for anchor in execution_anchors
        ):
            continue
        original_execution_anchors = list(execution_anchors)
        realized_exit_outcomes: dict[str, Mapping[str, Any]] = {}
        policy_eligible_exit_leg_ids: set[str] = set()
        for anchor in anchors:
            if anchor.get("lifecycle_stage") != "exit":
                continue
            outcome = anchor.get("owner_outcome")
            if not isinstance(outcome, Mapping) or outcome.get("realized") is not True:
                continue
            leg_id = str(outcome.get("leg_id") or "owner_episode")
            realized_exit_outcomes[leg_id] = outcome
            if _anchor_policy_eligible(anchor):
                policy_eligible_exit_leg_ids.add(leg_id)
        enriched_execution_anchors: list[dict[str, Any]] = []
        for anchor in execution_anchors:
            enriched = dict(anchor)
            outcome = anchor.get("owner_outcome")
            leg_id = (
                str(outcome.get("leg_id") or "owner_episode")
                if isinstance(outcome, Mapping)
                else "owner_episode"
            )
            if (
                isinstance(outcome, Mapping)
                and outcome.get("realized") is not True
                and leg_id in realized_exit_outcomes
            ):
                enriched["owner_outcome"] = dict(realized_exit_outcomes[leg_id])
            enriched_execution_anchors.append(enriched)
        execution_anchors = enriched_execution_anchors
        entry_policy_eligible = bool(
            _anchor_policy_eligible(decision_anchor)
            and all(
                _anchor_policy_eligible(anchor) for anchor in original_execution_anchors
            )
        )
        all_execution_legs_reconciled = all(
            isinstance(anchor.get("owner_outcome"), Mapping)
            and str(
                (anchor.get("owner_outcome") or {}).get("leg_id") or "owner_episode"
            )
            in policy_eligible_exit_leg_ids
            for anchor in original_execution_anchors
        )
        held_reconciled_policy_eligible = bool(
            all_execution_legs_reconciled
            and (
                _anchor_policy_eligible(decision_anchor)
                or _anchor_held_diagnostic_eligible(decision_anchor)
            )
            and all(
                _anchor_policy_eligible(anchor)
                or _anchor_held_diagnostic_eligible(anchor)
                for anchor in original_execution_anchors
            )
        )
        coverage_anchors = {
            str(anchor.get("anchor_id") or index): anchor
            for index, anchor in enumerate([decision_anchor, *execution_anchors])
        }.values()
        coverage_metrics = [
            anchor.get("metrics")
            for anchor in coverage_anchors
            if isinstance(anchor.get("metrics"), Mapping)
        ]
        if len(coverage_metrics) != len(coverage_anchors):
            continue
        eligible_rows = sum(
            _finite(metrics.get("eligible_window_row_count")) or 0.0
            for metrics in coverage_metrics
        )
        bbo_rows = sum(
            _finite(metrics.get("bbo_complete_row_count")) or 0.0
            for metrics in coverage_metrics
        )
        depth_rows = sum(
            _finite(metrics.get("depth_context_covered_row_count")) or 0.0
            for metrics in coverage_metrics
        )
        alternatives: dict[str, Any] = {}
        for timeout_sec in TIMEOUT_AXIS_VALUES_SEC:
            legs = [
                _counterfactual_leg(anchor, timeout_sec=timeout_sec)
                for anchor in execution_anchors
            ]
            eligible_legs = [leg for leg in legs if leg.get("eligible") is True]
            candidate_realized = bool(eligible_legs) and len(eligible_legs) == len(legs)
            current_realized = candidate_realized and all(
                leg.get("current_realized") is True for leg in eligible_legs
            )
            weights = [
                _finite(leg.get("entry_notional_krw")) or 0.0 for leg in eligible_legs
            ]
            candidate_net = _weighted_average(
                (
                    _finite(leg.get("candidate_net_return_pct")) or 0.0,
                    weight,
                )
                for leg, weight in zip(eligible_legs, weights)
            )
            current_net = (
                _weighted_average(
                    (
                        _finite(leg.get("current_net_return_pct")) or 0.0,
                        weight,
                    )
                    for leg, weight in zip(eligible_legs, weights)
                )
                if current_realized
                else None
            )
            current_capital_seconds = (
                sum(
                    weight * (_finite(leg.get("current_holding_sec")) or 0.0)
                    for leg, weight in zip(eligible_legs, weights)
                )
                if current_realized
                else None
            )
            current_holding_sec = (
                max(
                    _finite(leg.get("current_holding_sec")) or 0.0
                    for leg in eligible_legs
                )
                if current_realized
                else None
            )
            candidate_holding_sec = (
                max(
                    _finite(leg.get("candidate_holding_sec")) or 0.0
                    for leg in eligible_legs
                )
                if candidate_realized
                else None
            )
            alternatives[str(timeout_sec)] = {
                "timeout_sec": timeout_sec,
                "candidate_realized": candidate_realized,
                "current_realized": current_realized,
                "paired_ev_eligible": bool(
                    current_realized
                    and candidate_realized
                    and current_net is not None
                    and candidate_net is not None
                ),
                "current_net_return_pct": (
                    round(current_net, 6) if current_net is not None else None
                ),
                "candidate_net_return_pct": (
                    round(candidate_net, 6) if candidate_net is not None else None
                ),
                "candidate_net_profit_krw": round(
                    sum(
                        _finite(leg.get("candidate_net_profit_krw")) or 0.0
                        for leg in eligible_legs
                    ),
                    6,
                ),
                "current_capital_occupied_krw_seconds": (
                    round(current_capital_seconds, 6)
                    if current_capital_seconds is not None
                    else None
                ),
                "current_net_profit_krw": (
                    round(
                        sum(
                            _finite(leg.get("current_net_profit_krw")) or 0.0
                            for leg in eligible_legs
                        ),
                        6,
                    )
                    if current_realized
                    else None
                ),
                "current_holding_sec": (
                    round(current_holding_sec, 6)
                    if current_holding_sec is not None
                    else None
                ),
                "candidate_holding_sec": (
                    round(candidate_holding_sec, 6)
                    if candidate_holding_sec is not None
                    else None
                ),
                "candidate_capital_occupied_krw_seconds": round(
                    sum(
                        _finite(leg.get("candidate_capital_occupied_krw_seconds"))
                        or 0.0
                        for leg in eligible_legs
                    ),
                    6,
                ),
                "candidate_completed_within_180s": bool(
                    candidate_realized
                    and all(
                        (_finite(leg.get("candidate_holding_sec")) or math.inf) <= 180
                        for leg in eligible_legs
                    )
                ),
                "current_completed_within_180s": bool(
                    current_realized
                    and all(
                        (_finite(leg.get("current_holding_sec")) or math.inf) <= 180
                        for leg in eligible_legs
                    )
                ),
                "leg_count": len(legs),
                "eligible_leg_count": len(eligible_legs),
                "leg_diagnostics": legs,
            }
        units.append(
            {
                "source_date": str(
                    decision_anchor.get("_source_report_date")
                    or source_date.isoformat()
                ),
                "owner": cohort[0],
                "scope_id": cohort[1],
                "symbol": cohort[2],
                "session": cohort[3],
                "lifecycle_id": lifecycle_id,
                "policy_eligible": bool(
                    entry_policy_eligible or held_reconciled_policy_eligible
                ),
                "held_diagnostic_only": bool(
                    not held_reconciled_policy_eligible
                    and _anchor_held_diagnostic_eligible(decision_anchor)
                    and all(
                        _anchor_held_diagnostic_eligible(anchor)
                        for anchor in original_execution_anchors
                    )
                ),
                "eligible_window_row_count": int(eligible_rows),
                "bbo_complete_row_count": int(bbo_rows),
                "depth_context_covered_row_count": int(depth_rows),
                "alternatives": alternatives,
            }
        )
    return units


def _cohort_invalid_contract_counts(
    report: Mapping[str, Any],
) -> dict[tuple[str, str, str, str], int]:
    counts: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for anchor in _direct_anchor_results(report):
        cohort = _cohort_key(anchor)
        if cohort is None:
            continue
        if anchor.get("owner_lifecycle_contract_valid") is False or str(
            anchor.get("micro_context_status") or ""
        ) in {
            "owner_anchor_contract_invalid",
            "micro_scope_source_contract_invalid",
            "micro_stream_source_contract_invalid",
            "micro_source_exclusion_manifest_missing_or_invalid",
        }:
            counts[cohort] += 1
    return dict(counts)


def _window_summary(
    units: Sequence[Mapping[str, Any]], *, timeout_sec: int, start_day: date
) -> dict[str, Any]:
    selected = [
        unit
        for unit in units
        if date.fromisoformat(str(unit["source_date"])) >= start_day
    ]
    policy_selected = [unit for unit in selected if unit.get("policy_eligible") is True]
    alternative_rows = [
        unit.get("alternatives", {}).get(str(timeout_sec), {})
        for unit in policy_selected
    ]
    diagnostic_rows = [
        unit.get("alternatives", {}).get(str(timeout_sec), {}) for unit in selected
    ]
    paired = [row for row in alternative_rows if row.get("paired_ev_eligible") is True]
    current_completed = [
        row for row in alternative_rows if row.get("current_realized") is True
    ]
    candidate_completed = [
        row for row in alternative_rows if row.get("candidate_realized") is True
    ]
    current_values = [
        value
        for row in current_completed
        if (value := _finite(row.get("current_net_return_pct"))) is not None
    ]
    candidate_values = [
        value
        for row in candidate_completed
        if (value := _finite(row.get("candidate_net_return_pct"))) is not None
    ]
    paired_current_values = [
        value
        for row in paired
        if (value := _finite(row.get("current_net_return_pct"))) is not None
    ]
    paired_candidate_values = [
        value
        for row in paired
        if (value := _finite(row.get("candidate_net_return_pct"))) is not None
    ]
    current_ev = statistics.fmean(current_values) if current_values else None
    candidate_ev = statistics.fmean(candidate_values) if candidate_values else None
    paired_current_ev = (
        statistics.fmean(paired_current_values) if paired_current_values else None
    )
    paired_candidate_ev = (
        statistics.fmean(paired_candidate_values) if paired_candidate_values else None
    )
    uplift = (
        paired_candidate_ev - paired_current_ev
        if paired_current_ev is not None and paired_candidate_ev is not None
        else None
    )
    candidate_profit = (
        sum(
            _finite(row.get("candidate_net_profit_krw")) or 0.0
            for row in candidate_completed
        )
        if candidate_completed
        else None
    )
    current_profit = (
        sum(
            _finite(row.get("current_net_profit_krw")) or 0.0
            for row in current_completed
        )
        if current_completed
        else None
    )
    current_capital_seconds = (
        sum(
            _finite(row.get("current_capital_occupied_krw_seconds")) or 0.0
            for row in current_completed
        )
        if current_completed
        else None
    )
    candidate_capital_seconds = (
        sum(
            _finite(row.get("candidate_capital_occupied_krw_seconds")) or 0.0
            for row in candidate_completed
        )
        if candidate_completed
        else None
    )
    paired_candidate_profit = (
        sum(_finite(row.get("candidate_net_profit_krw")) or 0.0 for row in paired)
        if paired
        else None
    )
    paired_current_profit = (
        sum(_finite(row.get("current_net_profit_krw")) or 0.0 for row in paired)
        if paired
        else None
    )
    current_unresolved = sum(
        row.get("current_realized") is not True for row in diagnostic_rows
    )
    candidate_unresolved = sum(
        row.get("candidate_realized") is not True for row in diagnostic_rows
    )
    return {
        "window_start": start_day.isoformat(),
        "lifecycle_count": len(policy_selected),
        "diagnostic_lifecycle_count": len(selected),
        "held_diagnostic_only_lifecycle_count": sum(
            unit.get("held_diagnostic_only") is True for unit in selected
        ),
        "paired_complete_lifecycle_count": len(paired),
        "current_complete_lifecycle_count": len(current_completed),
        "candidate_complete_lifecycle_count": len(candidate_completed),
        "current_source_quality_adjusted_ev_pct": (
            round(current_ev, 6) if current_ev is not None else None
        ),
        "candidate_source_quality_adjusted_ev_pct": (
            round(candidate_ev, 6) if candidate_ev is not None else None
        ),
        "paired_current_source_quality_adjusted_ev_pct": (
            round(paired_current_ev, 6) if paired_current_ev is not None else None
        ),
        "paired_candidate_source_quality_adjusted_ev_pct": (
            round(paired_candidate_ev, 6) if paired_candidate_ev is not None else None
        ),
        "paired_ev_uplift_pct_points": (
            round(uplift, 6) if uplift is not None else None
        ),
        "current_p10_net_return_pct": (
            round(value, 6)
            if (value := _p10(paired_current_values)) is not None
            else None
        ),
        "candidate_p10_net_return_pct": (
            round(value, 6)
            if (value := _p10(paired_candidate_values)) is not None
            else None
        ),
        "candidate_net_profit_krw": (
            round(candidate_profit, 6) if candidate_profit is not None else None
        ),
        "current_net_profit_krw": (
            round(current_profit, 6) if current_profit is not None else None
        ),
        "paired_net_profit_uplift_krw": (
            round(paired_candidate_profit - paired_current_profit, 6)
            if paired_candidate_profit is not None and paired_current_profit is not None
            else None
        ),
        "current_capital_occupied_krw_seconds": (
            round(current_capital_seconds, 6)
            if current_capital_seconds is not None
            else None
        ),
        "candidate_capital_occupied_krw_seconds": (
            round(candidate_capital_seconds, 6)
            if candidate_capital_seconds is not None
            else None
        ),
        "candidate_net_profit_krw_per_capital_occupied_krw_hour": (
            round(candidate_profit / (candidate_capital_seconds / 3600.0), 9)
            if candidate_profit is not None
            and candidate_capital_seconds is not None
            and candidate_capital_seconds > 0
            else None
        ),
        "current_net_profit_krw_per_capital_occupied_krw_hour": (
            round(current_profit / (current_capital_seconds / 3600.0), 9)
            if current_profit is not None
            and current_capital_seconds is not None
            and current_capital_seconds > 0
            else None
        ),
        "current_median_reconciliation_confirmed_duration_sec": (
            round(statistics.median(values), 6)
            if (
                values := [
                    value
                    for row in current_completed
                    if (value := _finite(row.get("current_holding_sec"))) is not None
                ]
            )
            else None
        ),
        "candidate_median_timeout_duration_sec": (
            round(statistics.median(values), 6)
            if (
                values := [
                    value
                    for row in candidate_completed
                    if (value := _finite(row.get("candidate_holding_sec"))) is not None
                ]
            )
            else None
        ),
        "current_held_or_unresolved_count": current_unresolved,
        "candidate_held_or_unresolved_count": candidate_unresolved,
        "candidate_completed_within_180s_count": sum(
            row.get("candidate_completed_within_180s") is True
            for row in diagnostic_rows
        ),
        "current_completed_within_180s_count": sum(
            row.get("current_completed_within_180s") is True for row in diagnostic_rows
        ),
    }


def _candidate_from_research(
    *,
    target_day: date,
    cohort: tuple[str, str, str, str],
    timeout_sec: int,
    observed_days: int,
    unique_lifecycles: int,
    bbo_rate: float | None,
    depth_rate: float | None,
    windows: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    owner, scope_id, symbol, session = cohort
    current_20d = _finite(
        windows["20d"].get("paired_current_source_quality_adjusted_ev_pct")
    )
    candidate_20d = _finite(
        windows["20d"].get("paired_candidate_source_quality_adjusted_ev_pct")
    )
    relative_uplift = (
        (candidate_20d - current_20d) / abs(current_20d) * 100.0
        if current_20d is not None
        and candidate_20d is not None
        and abs(current_20d) > 1e-12
        else None
    )
    bounded_contract = {
        "axis": "target_timeout_sec",
        "type": "integer_seconds",
        "allowed_values": list(TIMEOUT_AXIS_VALUES_SEC),
        "current": "owner_current_exit_policy",
        "recommended": timeout_sec,
        "scope": {"owner": owner, "symbol": symbol, "session": session},
        "source_only": True,
    }
    runtime_design = {
        "runtime_family": f"unregistered_{owner}_lifecycle_turnover_timeout_v1",
        "stage": "exit",
        "axis": "target_timeout_sec",
        "mapping_status": "design_required",
        "runtime_registry_verified": False,
        "same_stage_owner_conflict_free": False,
        "preopen_consumer": "design_required_no_runtime_consumer",
        "bounded_values": {
            "current": "owner_current_exit_policy",
            "recommended": timeout_sec,
        },
        "bounded_contract_sha256": _canonical_sha256(bounded_contract),
        "rollback": {
            "trigger": "any_source_quality_ev_p10_held_or_receipt_guard_breach",
            "value": "owner_current_exit_policy",
        },
        "post_apply_attribution": {
            "owner": "design_required_machine_lifecycle_turnover_attribution",
            "window": "paired_5d_10d_20d",
        },
        "forbidden_uses": list(METRIC_CONTRACT["forbidden_uses"]),
    }
    return {
        "schema": CANDIDATE_SCHEMA,
        "candidate_id": (
            f"machine_turnover:{owner}:{scope_id}:target_timeout_{timeout_sec}s"
        ),
        "source_date": target_day.isoformat(),
        "evidence_valid_through": (target_day + timedelta(days=31)).isoformat(),
        "owner": owner,
        "owner_scope_id": scope_id,
        "first_operator_approval_required": True,
        "evidence": {
            "observed_trading_days": observed_days,
            "matched_entry_anchors": unique_lifecycles,
            "bbo_complete_rate_pct": round(bbo_rate or 0.0, 6),
            "depth_window_coverage_pct": round(depth_rate or 0.0, 6),
            "invalid_contract_row_count": 0,
            "rolling_source_quality_adjusted_ev_pct": {
                key: windows[key]["candidate_source_quality_adjusted_ev_pct"]
                for key in ("5d", "10d", "20d")
            },
            "rolling_paired_complete_lifecycle_count": {
                key: windows[key]["paired_complete_lifecycle_count"]
                for key in ("5d", "10d", "20d")
            },
            "rolling_paired_complete_lifecycle_floor": dict(
                ROLLING_PAIRED_LIFECYCLE_FLOORS
            ),
            "paired_ev_uplift_pct_points": {
                key: windows[key]["paired_ev_uplift_pct_points"]
                for key in ("5d", "10d", "20d")
            },
            "relative_primary_ev_uplift_pct": round(relative_uplift or 0.0, 6),
            "primary_20d_net_profit": windows["20d"]["candidate_net_profit_krw"],
            "costs_included": True,
            "source_quality_pass": True,
            "paired_p10_not_worse": True,
            "held_unresolved_not_increased": True,
            "capital_efficiency": windows["20d"][
                "candidate_net_profit_krw_per_capital_occupied_krw_hour"
            ],
            "candidate_completed_within_180s_count": windows["20d"][
                "candidate_completed_within_180s_count"
            ],
        },
        "runtime_design": runtime_design,
        "objective_followup_binding": {
            "schema": OBJECTIVE_BINDING_SCHEMA,
            "followup_id": OBJECTIVE_FOLLOWUP_ID,
            "resolved_gap_codes": [],
        },
        **AUTHORITY,
    }


def _research_row(
    *,
    target_day: date,
    cohort: tuple[str, str, str, str],
    units: list[dict[str, Any]],
    invalid_contract_counts: Sequence[tuple[date, int]],
    source_report_dates: set[date],
    source_report_exclusion_dates: set[date],
) -> dict[str, Any]:
    primary_window_start = _krx_window_start(target_day, 20)
    diagnostic_units = [
        unit
        for unit in units
        if date.fromisoformat(str(unit["source_date"])) >= primary_window_start
    ]
    readiness_units = [
        unit for unit in diagnostic_units if unit.get("policy_eligible") is True
    ]
    total_rows = sum(
        int(unit.get("eligible_window_row_count") or 0) for unit in readiness_units
    )
    bbo_rows = sum(
        int(unit.get("bbo_complete_row_count") or 0) for unit in readiness_units
    )
    depth_rows = sum(
        int(unit.get("depth_context_covered_row_count") or 0)
        for unit in readiness_units
    )
    bbo_rate = bbo_rows / total_rows * 100.0 if total_rows else None
    depth_rate = depth_rows / total_rows * 100.0 if total_rows else None
    observed_days = len({str(unit["source_date"]) for unit in readiness_units})
    unique_lifecycles = len({str(unit["lifecycle_id"]) for unit in readiness_units})
    invalid_contract_row_count = sum(
        count
        for source_day, count in invalid_contract_counts
        if source_day >= primary_window_start
    )
    alternatives: list[dict[str, Any]] = []
    for timeout_sec in TIMEOUT_AXIS_VALUES_SEC:
        windows = {
            f"{days}d": _window_summary(
                units,
                timeout_sec=timeout_sec,
                start_day=_krx_window_start(target_day, days),
            )
            for days in (5, 10, 20)
        }
        gaps: list[str] = []
        if observed_days < 5:
            gaps.append("observed_trading_days_below_5")
        if unique_lifecycles < 20:
            gaps.append("policy_eligible_unique_lifecycles_below_20")
        if bbo_rate is None or bbo_rate < 95.0:
            gaps.append("bbo_complete_rate_below_95pct")
        if depth_rate is None or depth_rate < 90.0:
            gaps.append("depth_window_coverage_below_90pct")
        if invalid_contract_row_count != 0:
            gaps.append("invalid_contract_rows_present")
        window_sample_readiness: dict[str, Any] = {}
        for window_name, window in windows.items():
            candidate_ev = _finite(
                window.get("candidate_source_quality_adjusted_ev_pct")
            )
            uplift = _finite(window.get("paired_ev_uplift_pct_points"))
            required_paired_lifecycles = ROLLING_PAIRED_LIFECYCLE_FLOORS[window_name]
            paired_lifecycles = int(window.get("paired_complete_lifecycle_count") or 0)
            if candidate_ev is None or candidate_ev <= 0:
                gaps.append(f"{window_name}_candidate_ev_not_positive")
            if uplift is None or uplift <= 0:
                gaps.append(f"{window_name}_paired_ev_uplift_not_positive")
            if paired_lifecycles < required_paired_lifecycles:
                gaps.append(
                    f"{window_name}_paired_lifecycle_count_below_"
                    f"{required_paired_lifecycles}"
                )
            diagnostic_lifecycles = int(window.get("diagnostic_lifecycle_count") or 0)
            eligible_lifecycles = int(window.get("lifecycle_count") or 0)
            held_diagnostic_lifecycles = int(
                window.get("held_diagnostic_only_lifecycle_count") or 0
            )
            terminal_or_unresolved = int(
                window.get("current_held_or_unresolved_count") or 0
            ) + int(window.get("candidate_held_or_unresolved_count") or 0)
            if paired_lifecycles >= required_paired_lifecycles:
                sample_state = "floor_met"
            elif held_diagnostic_lifecycles > 0 and terminal_or_unresolved > 0:
                sample_state = "terminal_or_right_censored_gap"
            elif diagnostic_lifecycles > 0 and eligible_lifecycles == 0:
                sample_state = "source_quality_or_eligibility_gap"
            elif paired_lifecycles == 0 and terminal_or_unresolved > 0:
                sample_state = "terminal_or_right_censored_gap"
            else:
                sample_state = "natural_sample_wait"
            window_start = date.fromisoformat(str(window["window_start"]))
            source_report_day_count = sum(
                window_start <= source_day <= target_day
                for source_day in source_report_dates
            )
            source_report_contract_gap_day_count = sum(
                window_start <= source_day <= target_day
                for source_day in source_report_exclusion_dates
            )
            observed_daily_yield = (
                paired_lifecycles / source_report_day_count
                if source_report_day_count
                else 0.0
            )
            window_days = int(window_name.removesuffix("d"))
            projected_full_window_lifecycles = observed_daily_yield * window_days
            remaining_paired_lifecycles = max(
                required_paired_lifecycles - paired_lifecycles, 0
            )
            remaining_source_report_days = max(
                window_days - source_report_day_count, 0
            )
            classification_window_complete = remaining_source_report_days == 0
            earliest_review_date = (
                target_day
                if classification_window_complete
                else _advance_krx_trading_days(
                    target_day, remaining_source_report_days
                )
            )
            if (
                sample_state == "natural_sample_wait"
                and source_report_contract_gap_day_count > 0
            ):
                sample_state = "source_report_contract_gap"
                gaps.append(f"{window_name}_source_report_contract_gap")
            elif (
                sample_state == "natural_sample_wait"
                and not classification_window_complete
            ):
                sample_state = "pending_declared_window"
                gaps.append(f"{window_name}_classification_window_pending")
            if (
                sample_state == "natural_sample_wait"
                and classification_window_complete
                and projected_full_window_lifecycles + 1e-12
                < required_paired_lifecycles
            ):
                sample_state = "window_floor_unattainable_at_observed_yield"
                gaps.append(
                    f"{window_name}_window_floor_unattainable_at_observed_yield"
                )
            if sample_state == "floor_met":
                shortage_classification_status = "not_applicable_floor_met"
                shortage_class = None
                projected_days = 0
                why_waiting_cannot_resolve = None
            elif sample_state == "source_quality_or_eligibility_gap":
                shortage_classification_status = "classified"
                shortage_class = "structural_population_exhaustion"
                projected_days = None
                why_waiting_cannot_resolve = (
                    "diagnostic_lifecycle_exists_but_policy_eligible_pair_is_absent"
                )
            elif sample_state == "source_report_contract_gap":
                shortage_classification_status = "blocked_missing_evidence"
                shortage_class = None
                projected_days = None
                why_waiting_cannot_resolve = (
                    "rolling_source_report_contract_gap_prevents_population_census"
                )
            elif sample_state == "window_floor_unattainable_at_observed_yield":
                shortage_classification_status = "classified"
                shortage_class = "structural_population_exhaustion"
                projected_days = None
                why_waiting_cannot_resolve = (
                    "observed_yield_cannot_reach_floor_before_rolling_window_expires"
                )
            elif sample_state == "pending_declared_window":
                shortage_classification_status = "pending_declared_window"
                shortage_class = None
                projected_days = None
                why_waiting_cannot_resolve = None
            elif sample_state == "natural_sample_wait" and observed_daily_yield > 0:
                shortage_classification_status = "classified"
                shortage_class = "time_resolvable_shortage"
                projected_days = math.ceil(
                    remaining_paired_lifecycles / observed_daily_yield
                )
                why_waiting_cannot_resolve = None
            else:
                shortage_classification_status = "blocked_missing_evidence"
                shortage_class = None
                projected_days = None
                why_waiting_cannot_resolve = (
                    "terminal_maturity_or_positive_arrival_rate_not_proven"
                )
            window_sample_readiness[window_name] = {
                "shortage_id": (
                    f"machine_turnover:{cohort[0]}:{cohort[1]}:{cohort[2]}:"
                    f"{cohort[3]}:target_timeout_{timeout_sec}s:{window_name}"
                ),
                "required_paired_complete_lifecycle_count": (
                    required_paired_lifecycles
                ),
                "observed_paired_complete_lifecycle_count": paired_lifecycles,
                "remaining_paired_complete_lifecycle_count": (
                    remaining_paired_lifecycles
                ),
                "source_report_day_count": source_report_day_count,
                "source_report_contract_gap_day_count": (
                    source_report_contract_gap_day_count
                ),
                "minimum_completed_due_trading_days": window_days,
                "remaining_completed_due_trading_days_to_classification": (
                    remaining_source_report_days
                ),
                "classification_window_complete": classification_window_complete,
                "earliest_review_date": (
                    earliest_review_date.isoformat()
                    if sample_state == "pending_declared_window"
                    else None
                ),
                "observed_paired_lifecycles_per_source_day": round(
                    observed_daily_yield, 8
                ),
                "projected_paired_lifecycles_in_full_window": (
                    None
                    if sample_state == "source_report_contract_gap"
                    else round(projected_full_window_lifecycles, 8)
                ),
                "projected_additional_trading_days_at_observed_yield": (projected_days),
                "state": sample_state,
                "shortage_classification_status": shortage_classification_status,
                "shortage_class": shortage_class,
                "why_waiting_cannot_resolve": why_waiting_cannot_resolve,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        current_20d = _finite(
            windows["20d"].get("paired_current_source_quality_adjusted_ev_pct")
        )
        candidate_20d = _finite(
            windows["20d"].get("paired_candidate_source_quality_adjusted_ev_pct")
        )
        relative_uplift = (
            (candidate_20d - current_20d) / abs(current_20d) * 100.0
            if current_20d is not None
            and candidate_20d is not None
            and abs(current_20d) > 1e-12
            else None
        )
        if relative_uplift is None or relative_uplift < 1.0:
            gaps.append("relative_primary_ev_uplift_below_1pct")
        if (_finite(windows["20d"].get("candidate_net_profit_krw")) or 0.0) <= 0:
            gaps.append("primary_20d_net_profit_not_positive")
        current_p10 = _finite(windows["20d"].get("current_p10_net_return_pct"))
        candidate_p10 = _finite(windows["20d"].get("candidate_p10_net_return_pct"))
        paired_p10_not_worse = bool(
            current_p10 is not None
            and candidate_p10 is not None
            and candidate_p10 >= current_p10
        )
        if not paired_p10_not_worse:
            gaps.append("paired_p10_worse_or_missing")
        held_not_increased = bool(
            windows["20d"]["candidate_held_or_unresolved_count"]
            <= windows["20d"]["current_held_or_unresolved_count"]
        )
        if not held_not_increased:
            gaps.append("held_unresolved_increased")
        alternatives.append(
            {
                "axis": "target_timeout_sec",
                "recommended_value": timeout_sec,
                "windows": windows,
                "window_sample_readiness": window_sample_readiness,
                "relative_primary_ev_uplift_pct": (
                    round(relative_uplift, 6) if relative_uplift is not None else None
                ),
                "paired_p10_not_worse": paired_p10_not_worse,
                "held_unresolved_not_increased": held_not_increased,
                "candidate_ready": not gaps,
                "readiness_gaps": sorted(set(gaps)),
            }
        )
    ready = [
        alternative for alternative in alternatives if alternative["candidate_ready"]
    ]
    selected = (
        max(
            ready,
            key=lambda row: (
                _finite(
                    row["windows"]["20d"].get(
                        "candidate_net_profit_krw_per_capital_occupied_krw_hour"
                    )
                )
                or float("-inf"),
                _finite(row["windows"]["20d"].get("paired_ev_uplift_pct_points"))
                or float("-inf"),
                -int(row["recommended_value"]),
            ),
        )
        if ready
        else None
    )
    candidate = (
        _candidate_from_research(
            target_day=target_day,
            cohort=cohort,
            timeout_sec=int(selected["recommended_value"]),
            observed_days=observed_days,
            unique_lifecycles=unique_lifecycles,
            bbo_rate=bbo_rate,
            depth_rate=depth_rate,
            windows=selected["windows"],
        )
        if selected is not None
        else None
    )
    return {
        "owner": cohort[0],
        "scope_id": cohort[1],
        "symbol": cohort[2],
        "session": cohort[3],
        "observed_trading_days": observed_days,
        "policy_eligible_unique_lifecycle_count": unique_lifecycles,
        "diagnostic_unique_lifecycle_count": len(
            {str(unit["lifecycle_id"]) for unit in diagnostic_units}
        ),
        "held_diagnostic_only_lifecycle_count": sum(
            unit.get("held_diagnostic_only") is True for unit in diagnostic_units
        ),
        "bbo_complete_rate_pct": round(bbo_rate, 6) if bbo_rate is not None else None,
        "depth_window_coverage_pct": (
            round(depth_rate, 6) if depth_rate is not None else None
        ),
        "invalid_contract_row_count": invalid_contract_row_count,
        "alternatives": alternatives,
        "selected_candidate": candidate,
    }


def _sample_floor_assessment(
    *, rows: Sequence[Mapping[str, Any]], source_contract_ready: bool
) -> dict[str, Any]:
    state_counts: dict[str, int] = defaultdict(int)
    classification_status_counts: dict[str, int] = defaultdict(int)
    shortage_class_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        alternatives = row.get("alternatives")
        if not isinstance(alternatives, list) or not alternatives:
            continue
        # Sample counts are timeout-arm specific. Count each distinct
        # cohort/arm/window assessment once without pooling owner scopes.
        for alternative in alternatives:
            readiness = (
                alternative.get("window_sample_readiness")
                if isinstance(alternative, Mapping)
                else None
            )
            if not isinstance(readiness, Mapping):
                continue
            for window in readiness.values():
                if isinstance(window, Mapping):
                    state = str(window.get("state") or "unknown")
                    state_counts[state] += 1
                    classification_status = str(
                        window.get("shortage_classification_status") or "unknown"
                    )
                    classification_status_counts[classification_status] += 1
                    shortage_class = window.get("shortage_class")
                    if isinstance(shortage_class, str) and shortage_class:
                        shortage_class_counts[shortage_class] += 1
    if not source_contract_ready:
        state = "source_contract_blocked"
        blocker_class = "source_quality"
        next_action = "repair_current_attribution_source_contract_and_rerun"
    elif not rows:
        state = "no_natural_sample"
        blocker_class = "sample_floor"
        next_action = "continue_exact_date_collection_without_imputation"
    elif state_counts.get("source_quality_or_eligibility_gap", 0) > 0:
        state = "source_quality_or_eligibility_gap"
        blocker_class = "source_quality"
        next_action = "repair_exact_scope_source_or_eligibility_contract_and_rerun"
    elif state_counts.get("source_report_contract_gap", 0) > 0:
        state = "source_report_contract_gap"
        blocker_class = "source_quality"
        next_action = "repair_excluded_source_report_contracts_and_rerun"
    elif state_counts.get("window_floor_unattainable_at_observed_yield", 0) > 0:
        state = "window_floor_unattainable_at_observed_yield"
        blocker_class = "sample_floor_contract"
        next_action = "repair_exact_scope_collection_yield_or_review_window_contract"
    elif state_counts.get("terminal_or_right_censored_gap", 0) > 0:
        state = "terminal_or_right_censored_gap"
        blocker_class = "terminal_outcome"
        next_action = "reconcile_exact_owner_terminal_outcomes_before_waiting"
    elif state_counts.get("pending_declared_window", 0) > 0:
        state = "pending_declared_window"
        blocker_class = "sample_floor"
        next_action = "recheck_at_earliest_declared_window"
    elif state_counts.get("natural_sample_wait", 0) > 0:
        state = "natural_sample_wait"
        blocker_class = "sample_floor"
        next_action = "continue_exact_scope_collection_and_recheck_window_floors"
    else:
        state = "sample_floor_met_or_non_sample_gate_pending"
        blocker_class = None
        next_action = "review_non_sample_ev_tail_and_runtime_design_gates"
    if state in {
        "source_quality_or_eligibility_gap",
        "window_floor_unattainable_at_observed_yield",
    }:
        shortage_classification_status = "classified"
        shortage_class = "structural_population_exhaustion"
        why_waiting_cannot_resolve = (
            "source_or_window_capacity_defect_prevents_floor_closure"
        )
    elif state == "source_report_contract_gap":
        shortage_classification_status = "blocked_missing_evidence"
        shortage_class = None
        why_waiting_cannot_resolve = (
            "rolling_source_report_contract_gap_prevents_population_census"
        )
    elif state == "natural_sample_wait" and not classification_status_counts.get(
        "blocked_missing_evidence", 0
    ):
        shortage_classification_status = "classified"
        shortage_class = "time_resolvable_shortage"
        why_waiting_cannot_resolve = None
    elif state == "pending_declared_window":
        shortage_classification_status = "pending_declared_window"
        shortage_class = None
        why_waiting_cannot_resolve = None
    elif state == "sample_floor_met_or_non_sample_gate_pending":
        shortage_classification_status = "not_applicable_sample_floor_met"
        shortage_class = None
        why_waiting_cannot_resolve = None
    else:
        shortage_classification_status = "blocked_missing_evidence"
        shortage_class = None
        why_waiting_cannot_resolve = (
            "positive_arrival_rate_or_terminal_maturity_horizon_not_proven"
        )
    return {
        "shortage_id": "machine_turnover:all_exact_scopes:target_timeout",
        "state": state,
        "shortage_classification_status": shortage_classification_status,
        "shortage_class": shortage_class,
        "why_waiting_cannot_resolve": why_waiting_cannot_resolve,
        "blocker_class": blocker_class,
        "window_state_counts": dict(sorted(state_counts.items())),
        "window_classification_status_counts": dict(
            sorted(classification_status_counts.items())
        ),
        "window_shortage_class_counts": dict(sorted(shortage_class_counts.items())),
        "next_action": next_action,
        **AUTHORITY,
    }


def build_rolling_paired_policy_research(
    *,
    target_date: str,
    current_report: Mapping[str, Any],
    report_dir: Path,
) -> dict[str, Any]:
    target_day = date.fromisoformat(target_date)
    _, current_source_contract_errors = _valid_attribution_report(
        current_report, expected_day=target_day
    )
    current_source_contract_ready = not current_source_contract_errors
    rolling_source_contract = current_report.get("rolling_policy_source_contract")
    source_contract_recovery = (
        dict(rolling_source_contract.get("recovery") or {})
        if isinstance(rolling_source_contract, Mapping)
        else {}
    )
    reports, exclusions = _load_reports(
        current_report=current_report,
        report_dir=report_dir,
        target_day=target_day,
    )
    source_report_dates = {
        date.fromisoformat(str(report["target_date"])) for report in reports
    }
    source_report_exclusion_dates = {
        date.fromisoformat(str(exclusion["source_date"]))
        for exclusion in exclusions
        if exclusion.get("source_date")
        and str(exclusion.get("reason") or "") != "duplicate_source_date"
    }
    cohort_units: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    cohort_invalid_contract_counts: dict[
        tuple[str, str, str, str], list[tuple[date, int]]
    ] = defaultdict(list)
    combined_anchors: list[dict[str, Any]] = []
    for report in reports:
        source_day = date.fromisoformat(str(report["target_date"]))
        for anchor in _direct_anchor_results(report):
            tagged_anchor = dict(anchor)
            tagged_anchor["_source_report_date"] = source_day.isoformat()
            combined_anchors.append(tagged_anchor)
        for cohort, count in _cohort_invalid_contract_counts(report).items():
            cohort_invalid_contract_counts[cohort].append((source_day, count))
    combined_report = {
        "target_date": target_day.isoformat(),
        "consumers": {
            "widget_postclose_tuning": {
                "symbols": {"rolling_history": {"anchor_results": combined_anchors}}
            },
            "episode_machine_postclose_tuning": {"profiles": {}},
        },
    }
    for unit in _lifecycle_units(combined_report):
        cohort = (
            unit["owner"],
            unit["scope_id"],
            unit["symbol"],
            unit["session"],
        )
        cohort_units[cohort].append(unit)
    rows = [
        _research_row(
            target_day=target_day,
            cohort=cohort,
            units=units,
            invalid_contract_counts=cohort_invalid_contract_counts.get(cohort, []),
            source_report_dates=source_report_dates,
            source_report_exclusion_dates=source_report_exclusion_dates,
        )
        for cohort, units in sorted(cohort_units.items())
    ]
    ready_candidates = (
        [
            row["selected_candidate"]
            for row in rows
            if isinstance(row.get("selected_candidate"), dict)
        ]
        if current_source_contract_ready
        else []
    )
    selected_candidate = (
        max(
            ready_candidates,
            key=lambda candidate: (
                _finite((candidate.get("evidence") or {}).get("capital_efficiency"))
                or float("-inf"),
                _finite(
                    (
                        (candidate.get("evidence") or {}).get(
                            "paired_ev_uplift_pct_points"
                        )
                        or {}
                    ).get("20d")
                )
                or float("-inf"),
                str(candidate.get("candidate_id") or ""),
            ),
        )
        if ready_candidates
        else None
    )
    candidates = [selected_candidate] if selected_candidate is not None else []
    selected_candidate_id = (
        str(selected_candidate.get("candidate_id")) if selected_candidate else None
    )
    for row in rows:
        row_candidate = row.get("selected_candidate")
        row["selected_for_intake"] = bool(
            isinstance(row_candidate, Mapping)
            and row_candidate.get("candidate_id") == selected_candidate_id
        )
    unresolved_gap_codes: list[str] = []
    if not candidates:
        if not current_source_contract_ready:
            unresolved_gap_codes.append("current_attribution_source_contract_invalid")
        elif not rows or not any(
            int(row.get("policy_eligible_unique_lifecycle_count") or 0) > 0
            for row in rows
        ):
            unresolved_gap_codes.append("no_policy_eligible_paired_lifecycle_observed")
        else:
            all_gaps = {
                gap
                for row in rows
                for alternative in row["alternatives"]
                for gap in alternative["readiness_gaps"]
            }
            unresolved_gap_codes.extend(sorted(all_gaps))
    sample_floor_assessment = _sample_floor_assessment(
        rows=rows,
        source_contract_ready=current_source_contract_ready,
    )
    report_status = (
        "candidate_ready"
        if candidates
        else (
            "source_quality_blocked"
            if sample_floor_assessment["blocker_class"] == "source_quality"
            else "evidence_accumulating"
        )
    )
    return {
        "schema": REPORT_SCHEMA,
        "target_date": target_date,
        "status": report_status,
        "decision": (
            "source_only_candidate_ready_design_required"
            if candidates
            else (
                "block_candidate_current_attribution_source_contract_invalid"
                if not current_source_contract_ready
                else "continue_source_only_rolling_paired_evidence"
            )
        ),
        "metric_contract": METRIC_CONTRACT,
        "authority": AUTHORITY,
        "current_source_contract": {
            "ready": current_source_contract_ready,
            "errors": current_source_contract_errors,
            "recovery": source_contract_recovery,
        },
        "sample_floor_assessment": sample_floor_assessment,
        "candidate_axes": {
            "single_axis": "target_timeout_sec",
            "values_sec": list(TIMEOUT_AXIS_VALUES_SEC),
            "baseline": "owner_current_exit_policy",
            "episode_same_day_reentry": "not_implemented_separate_future_axis",
            "selection_order": (
                "positive_cost_aware_ev_and_net_profit_and_p10_held_guards_then_"
                "net_profit_per_capital_occupied_hour"
            ),
        },
        "implementation_boundary": {
            "rolling_paired_policy_candidate_producer_present": True,
            "episode_same_day_reentry_or_timeout_tuning_axis_present": True,
            "speed_or_turnover_metric_changes_policy_selection": True,
        },
        "source_report_dates": [str(report.get("target_date")) for report in reports],
        "source_exclusions": exclusions,
        "cohorts": rows,
        "summary": {
            "valid_source_report_count": len(reports),
            "cohort_count": len(rows),
            "candidate_ready_cohort_count": len(ready_candidates),
            "policy_promotion_candidate_count": len(candidates),
        },
        "remaining_gap_codes": unresolved_gap_codes,
        "policy_promotion_candidates": candidates,
    }
