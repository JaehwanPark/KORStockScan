"""JSON/Markdown report producer for the micro-reversion V0 replay."""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .contracts import (
    DECISION_AUTHORITY,
    DEFAULT_HORIZONS_SEC,
    METRIC_CONTRACT,
    REPORT_SCHEMA,
)
from .replay import ReplayResult
from .reproducibility import write_reproducibility_manifest
from .tax import (
    TAX_POLICY_SOURCE_URL,
    TAX_POLICY_VERSION,
    ordinary_taxable_equity_floor_bps,
    tax_profile_for,
)

COST_SENSITIVITY_BPS = (0.0, 5.0, 10.0, 15.0, 20.0, 23.0)
FAST_EXIT_HORIZONS_SEC = (15, 30, 60, 120, 180)


def build_report(result: ReplayResult) -> dict[str, Any]:
    trade_dates = sorted(
        {observation.trade_date for observation in result.observations}
        | {event.trade_date for event in result.events}
    )
    window_start = trade_dates[0] if trade_dates else None
    window_end = trade_dates[-1] if trade_dates else None
    horizon_metrics = {
        str(horizon): _horizon_metrics(result, horizon)
        for horizon in DEFAULT_HORIZONS_SEC
    }
    fully_mature_labels = [
        label
        for label in result.labels
        if label.mature_horizon_count == len(DEFAULT_HORIZONS_SEC)
    ]
    event_symbols = {event.symbol for event in result.events}
    mature_coverage_rate = (
        len(fully_mature_labels) / len(result.events) if result.events else None
    )
    daily_metrics = _daily_metrics(result, trade_dates)
    parent_metrics = _parent_metrics(result)
    cost_sensitivity = _cost_sensitivity(result, trade_dates)
    common_maturity_cohorts = _common_maturity_cohorts(result)
    positive_day_count = sum(
        row["source_quality_adjusted_ev_pct_300s"] is not None
        and row["source_quality_adjusted_ev_pct_300s"] > 0
        for row in daily_metrics
    )
    max_date_ev_contribution_rate = _max_date_ev_contribution_rate(daily_metrics)
    eligible_positive_parent_count = sum(
        row["mature_300s_count"] >= 100
        and row["source_quality_adjusted_ev_pct_300s"] is not None
        and row["source_quality_adjusted_ev_pct_300s"] > 0
        for row in parent_metrics
    )
    primary = horizon_metrics["300"]
    fast_exit_rows = [
        cost_sensitivity[str(horizon)] for horizon in FAST_EXIT_HORIZONS_SEC
    ]
    observed_fast_exit_rows = [
        row for row in fast_exit_rows if row["break_even_all_in_cost_bps"] is not None
    ]
    best_observed_row = (
        max(
            observed_fast_exit_rows,
            key=lambda row: row["break_even_all_in_cost_bps"],
        )
        if observed_fast_exit_rows
        else None
    )
    gross_reversion_supported = any(
        row["break_even_all_in_cost_bps"] is not None
        and row["break_even_all_in_cost_bps"] > 0
        for row in fast_exit_rows
    )
    best_observed_fixed_horizon = (
        {
            "horizon_sec": best_observed_row["horizon_sec"],
            "sample_count": best_observed_row["sample_count"],
            "equal_weight_avg_profit_pct": best_observed_row[
                "equal_weight_avg_profit_pct"
            ],
            "break_even_all_in_cost_bps": best_observed_row[
                "break_even_all_in_cost_bps"
            ],
            "selection_authority": False,
            "interpretation": "descriptive_in_sample_not_exit_policy",
        }
        if best_observed_row is not None
        else None
    )
    tax_evidence = _tax_evidence(
        result,
        window_end=window_end,
        best_observed_row=best_observed_row,
    )
    aggregate_taxable_gate = tax_evidence[
        "aggregate_taxable_equity_economic_gate_passed"
    ]
    aggregate_interpretation = (
        "aggregate_ordinary_taxable_equity_fixed_horizon_below_"
        "statutory_floor_but_subcohort_and_path_execution_unresolved"
        if aggregate_taxable_gate is False
        else (
            "aggregate_ordinary_taxable_equity_fixed_horizon_above_"
            "statutory_floor_but_non_tax_execution_costs_unresolved"
            if aggregate_taxable_gate is True
            else "aggregate_ordinary_taxable_equity_gate_unavailable_missing_"
            "mature_fixed_horizon_evidence"
        )
    )
    gate_results = _gate_results(
        event_count=len(result.events),
        fully_mature_event_count=len(fully_mature_labels),
        primary_ev_pct=primary["source_quality_adjusted_ev_pct"],
        mature_coverage_rate=mature_coverage_rate,
        trade_date_count=len(trade_dates),
        positive_day_count=positive_day_count,
        max_date_ev_contribution_rate=max_date_ev_contribution_rate,
        eligible_positive_parent_count=eligible_positive_parent_count,
        tax_classification_complete=tax_evidence["tax_classification_complete"],
        aggregate_taxable_equity_economic_gate_passed=tax_evidence[
            "aggregate_taxable_equity_economic_gate_passed"
        ],
    )
    status = _decision_status(
        event_count=len(result.events),
        fully_mature_event_count=len(fully_mature_labels),
        gross_reversion_supported=gross_reversion_supported,
        primary_ev_pct=primary["source_quality_adjusted_ev_pct"],
        mature_coverage_rate=mature_coverage_rate,
        trade_date_count=len(trade_dates),
        positive_day_count=positive_day_count,
        max_date_ev_contribution_rate=max_date_ev_contribution_rate,
        eligible_positive_parent_count=eligible_positive_parent_count,
        aggregate_taxable_equity_economic_gate_passed=tax_evidence[
            "aggregate_taxable_equity_economic_gate_passed"
        ],
    )
    hypothesis_identified = len(result.events) > 0 and primary["sample_count"] > 0
    report_id = _report_id(window_start, window_end)
    report = {
        "schema": REPORT_SCHEMA,
        "report_id": report_id,
        "window": {
            "start_date": window_start,
            "end_date": window_end,
            "clean_baseline_enforced": True,
        },
        "decision": {
            "status": status,
            "hypothesis_identified": hypothesis_identified,
            "shock_pattern_identified": hypothesis_identified,
            "gross_reversion_hypothesis_supported": gross_reversion_supported,
            "positive_ev_hypothesis_supported": False,
            "complete_case_selected_cost_positive": bool(
                primary["source_quality_adjusted_ev_pct"] is not None
                and primary["source_quality_adjusted_ev_pct"] > 0
                and positive_day_count >= 3
            ),
            "selected_cost_positive_ev_supported": False,
            "positive_ev_hypothesis_interpretation": aggregate_interpretation,
            "strategy_rejected": bool(
                hypothesis_identified and not gross_reversion_supported
            ),
            "aggregate_fixed_horizon_strategy_rejected": (
                aggregate_taxable_gate is False
            ),
            "execution_economics_resolved": False,
            "execution_data_gate": False,
            "execution_data_gate_status": (
                "blocked_no_forward_market_path_or_paired_execution_rows"
            ),
            "aggregate_taxable_equity_economic_gate": tax_evidence[
                "aggregate_taxable_equity_economic_gate_passed"
            ],
            "aggregate_taxable_equity_gate_scope": tax_evidence["aggregate_gate_scope"],
            "tax_classification_complete": tax_evidence["tax_classification_complete"],
            "tax_class_source_quality_blocked": not tax_evidence[
                "tax_classification_complete"
            ],
            "subcohort_opportunity_discovery": "open",
            "observation_eligibility_scope": "broad_tradeable_core_and_discovery",
            "economic_candidate_scope": "narrow_verified_oos_clustered_lcb_only",
            "best_observed_fixed_horizon": best_observed_fixed_horizon,
            "legacy_v0_gate_results_passed": all(
                gate["passed"] for gate in gate_results
            ),
            "candidate_gate_passed": False,
            "candidate_gate_status": (
                "blocked_requires_forward_clustered_lcb_and_multiple_test_control"
            ),
            "gate_results": gate_results,
            "applied_to_sim": False,
            "real_runtime_reflected": False,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": DECISION_AUTHORITY,
            "remaining_for_real_runtime": [
                "all_in_cost_component_decomposition",
                "instrument_tax_classification_coverage",
                "forward_continuous_market_path_coverage",
                "paired_order_origin_and_terminal_receipt_coverage",
                "non_lookahead_exit_policy_simulation",
                "fill_and_slippage_observation",
                "explicit_real_runtime_approval_and_rollback_contract",
            ],
        },
        "summary": {
            "input_row_count": result.input_stats.raw_row_count,
            "accepted_row_count": result.input_stats.accepted_row_count,
            "deduplicated_observation_count": (
                result.input_stats.deduplicated_observation_count
            ),
            "event_count": len(result.events),
            "event_symbol_count": len(event_symbols),
            "fully_mature_event_count": len(fully_mature_labels),
            "fully_mature_event_coverage_rate": (
                None if mature_coverage_rate is None else round(mature_coverage_rate, 6)
            ),
            "trade_date_count": len(trade_dates),
            "positive_300s_ev_day_count": positive_day_count,
            "max_date_ev_contribution_rate": max_date_ev_contribution_rate,
            "eligible_positive_parent_count": eligible_positive_parent_count,
            "deduplicated_observation_coverage_tier_counts": (
                result.input_stats.coverage_tier_counts
            ),
            "raw_bbo_candidate_rows": result.input_stats.raw_bbo_candidate_rows,
            "event_joined_bbo_context_count": sum(
                event.coverage_tier.value in {"bbo_context", "micro_context"}
                for event in result.events
            ),
            "raw_micro_capture_rows": result.input_stats.raw_micro_capture_rows,
            "raw_micro_context_candidate_rows": (
                result.input_stats.raw_micro_context_candidate_rows
            ),
            "event_joined_micro_context_count": sum(
                event.coverage_tier.value == "micro_context" for event in result.events
            ),
            "outcome_source_quality_counts": dict(
                sorted(
                    Counter(
                        label.outcome_source_quality_status for label in result.labels
                    ).items()
                )
            ),
            "tax_classified_event_count": tax_evidence["classified_event_count"],
            "tax_unknown_or_unsupported_event_count": tax_evidence[
                "unknown_or_unsupported_event_count"
            ],
        },
        "horizon_metrics": horizon_metrics,
        "cost_model": {
            "selected_all_in_cost_bps": (
                result.input_stats.conservative_total_cost_bps
            ),
            "sensitivity_scenarios_bps": list(
                _cost_scenarios(result.input_stats.conservative_total_cost_bps)
            ),
            "components_decomposed": False,
            "zero_bps_semantics": "friction_free_not_slippage_only",
            "forbidden_interpretation": (
                "do_not_label_any_scenario_as_slippage_only_without_"
                "fee_tax_spread_and_slippage_components"
            ),
            "statutory_tax_policy": tax_evidence,
        },
        "cost_sensitivity": cost_sensitivity,
        "common_maturity_cohorts": common_maturity_cohorts,
        "daily_metrics": daily_metrics,
        "parent_metrics": parent_metrics,
        "profile_metrics": _profile_metrics(result),
        "source_quality": {
            "status": _source_quality_status(
                result,
            ),
            "input_stats": result.input_stats.as_dict(),
            "known_limitations": [
                "selected_pipeline_observations_not_continuous_tick_feed",
                "missing_l2_queue_and_fill_latency",
                "price_path_mae_may_be_under_observed",
                "fixed_horizon_terminal_return_is_counterfactual_not_realized_pnl",
                "complete_case_cost_adjusted_ev_excludes_unresolved_signals",
            ],
            "ev_denominator_contract": {
                "source_quality_adjusted_ev_pct": (
                    "complete_mature_outcomes_only_not_coverage_adjusted_headline"
                ),
                "economic_headline_allowed": False,
                "required_forward_headline": (
                    "net_ev_per_all_signal_clustered_lower_confidence_bound"
                ),
            },
        },
        "metric_contract": METRIC_CONTRACT,
        "events": [event.as_dict() for event in result.events],
        "labels": [label.as_dict() for label in result.labels],
    }
    return report


def _horizon_metrics(result: ReplayResult, horizon_sec: int) -> dict[str, Any]:
    outcomes = [
        outcome
        for label in result.labels
        for outcome in label.outcomes
        if outcome.horizon_sec == horizon_sec and outcome.complete
    ]
    adjusted_returns = [
        float(outcome.cost_adjusted_terminal_return_bps)
        for outcome in outcomes
        if outcome.cost_adjusted_terminal_return_bps is not None
    ]
    terminal_returns = [
        float(outcome.terminal_return_bps)
        for outcome in outcomes
        if outcome.terminal_return_bps is not None
    ]
    mfe_values = [
        float(outcome.mfe_bps) for outcome in outcomes if outcome.mfe_bps is not None
    ]
    mae_values = [
        float(outcome.mae_bps) for outcome in outcomes if outcome.mae_bps is not None
    ]
    complete_case_adjusted_ev = _avg(adjusted_returns, divisor=100.0)
    all_signal_zero_unresolved_ev = (
        None
        if not result.labels
        else round(sum(adjusted_returns) / len(result.labels) / 100.0, 6)
    )
    return {
        "horizon_sec": horizon_sec,
        "sample_count": len(outcomes),
        "all_detected_signal_count": len(result.labels),
        "resolved_outcome_count": len(outcomes),
        "unresolved_outcome_count": len(result.labels) - len(outcomes),
        "equal_weight_avg_profit_pct": _avg(terminal_returns, divisor=100.0),
        "source_quality_adjusted_ev_pct": complete_case_adjusted_ev,
        "complete_case_cost_adjusted_ev_pct": complete_case_adjusted_ev,
        "ev_per_all_detected_signal_zero_unresolved_pct": (
            all_signal_zero_unresolved_ev
        ),
        "optimistic_fill_bound_ev_pct": None,
        "conservative_fill_bound_ev_pct": None,
        "coverage_adjusted_lower_bound_pct": None,
        "economic_headline_allowed": False,
        "denominator_contract": "complete_mature_outcomes_only",
        "diagnostic_win_rate": _rate(value > 0 for value in adjusted_returns),
        "median_terminal_return_bps": _median(terminal_returns),
        "median_mfe_bps": _median(mfe_values),
        "median_mae_bps": _median(mae_values),
        "mae_p90_bps": _percentile(mae_values, 0.10),
        "mae_p95_bps": _percentile(mae_values, 0.05),
        "full_reclaim_rate": _rate(bool(outcome.full_reclaim) for outcome in outcomes),
        "half_reclaim_rate": _rate(bool(outcome.half_reclaim) for outcome in outcomes),
        "continuation_half_shock_rate": _rate(
            bool(outcome.continuation_half_shock) for outcome in outcomes
        ),
    }


def _profile_metrics(result: ReplayResult) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Any]] = defaultdict(list)
    for event, label in zip(result.events, result.labels, strict=True):
        grouped[(event.symbol, event.venue, event.session_bucket)].append(label)
    rows = []
    for (symbol, venue, session_bucket), labels in sorted(grouped.items()):
        outcomes = [
            outcome
            for label in labels
            for outcome in label.outcomes
            if outcome.horizon_sec == 300 and outcome.complete
        ]
        adjusted_returns = [
            float(outcome.cost_adjusted_terminal_return_bps)
            for outcome in outcomes
            if outcome.cost_adjusted_terminal_return_bps is not None
        ]
        rows.append(
            {
                "symbol": symbol,
                "venue": venue,
                "session_bucket": session_bucket,
                "event_count": len(labels),
                "mature_300s_count": len(outcomes),
                "source_quality_adjusted_ev_pct_300s": _avg(
                    adjusted_returns, divisor=100.0
                ),
                "diagnostic_win_rate_300s": _rate(
                    value > 0 for value in adjusted_returns
                ),
                "live_authority": False,
            }
        )
    return rows


def _daily_metrics(
    result: ReplayResult, trade_dates: list[str]
) -> list[dict[str, Any]]:
    labels_by_date: dict[str, list[Any]] = defaultdict(list)
    for label in result.labels:
        labels_by_date[label.trade_date].append(label)
    rows = []
    for trade_date in trade_dates:
        outcomes = _complete_outcomes(labels_by_date[trade_date], horizon_sec=300)
        adjusted_returns = _adjusted_returns(outcomes)
        rows.append(
            {
                "trade_date": trade_date,
                "mature_300s_count": len(outcomes),
                "net_cost_adjusted_return_bps": round(sum(adjusted_returns), 6),
                "source_quality_adjusted_ev_pct_300s": _avg(
                    adjusted_returns, divisor=100.0
                ),
                "diagnostic_win_rate_300s": _rate(
                    value > 0 for value in adjusted_returns
                ),
            }
        )
    return rows


def _parent_metrics(result: ReplayResult) -> list[dict[str, Any]]:
    labels_by_parent: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for label in result.labels:
        labels_by_parent[(label.venue, label.session_bucket)].append(label)
    rows = []
    for (venue, session_bucket), labels in sorted(labels_by_parent.items()):
        outcomes = _complete_outcomes(labels, horizon_sec=300)
        adjusted_returns = _adjusted_returns(outcomes)
        rows.append(
            {
                "venue": venue,
                "session_bucket": session_bucket,
                "mature_300s_count": len(outcomes),
                "source_quality_adjusted_ev_pct_300s": _avg(
                    adjusted_returns, divisor=100.0
                ),
                "diagnostic_win_rate_300s": _rate(
                    value > 0 for value in adjusted_returns
                ),
                "live_authority": False,
            }
        )
    return rows


def _complete_outcomes(labels: Iterable[Any], *, horizon_sec: int) -> list[Any]:
    return [
        outcome
        for label in labels
        for outcome in label.outcomes
        if outcome.horizon_sec == horizon_sec and outcome.complete
    ]


def _adjusted_returns(outcomes: Iterable[Any]) -> list[float]:
    return [
        float(outcome.cost_adjusted_terminal_return_bps)
        for outcome in outcomes
        if outcome.cost_adjusted_terminal_return_bps is not None
    ]


def _max_date_ev_contribution_rate(
    daily_metrics: Iterable[dict[str, Any]],
) -> float | None:
    contributions = [
        abs(float(row["net_cost_adjusted_return_bps"])) for row in daily_metrics
    ]
    total = sum(contributions)
    if total <= 0:
        return None
    return round(max(contributions) / total, 6)


def _decision_status(
    *,
    event_count: int,
    fully_mature_event_count: int,
    gross_reversion_supported: bool,
    primary_ev_pct: float | None,
    mature_coverage_rate: float | None,
    trade_date_count: int,
    positive_day_count: int,
    max_date_ev_contribution_rate: float | None,
    eligible_positive_parent_count: int,
    aggregate_taxable_equity_economic_gate_passed: bool | None = None,
) -> str:
    if event_count == 0:
        return "no_shock_events_identified"
    if (
        aggregate_taxable_equity_economic_gate_passed is False
        and gross_reversion_supported
    ):
        return (
            "v0_aggregate_taxable_equity_gate_failed_" "subcohort_execution_unresolved"
        )
    if primary_ev_pct is not None and primary_ev_pct <= 0:
        if gross_reversion_supported:
            return "v0_gross_edge_cost_sensitive_execution_unresolved"
        return "v0_reject_non_positive_gross_300s_ev"
    if fully_mature_event_count < 1_000:
        return "v0_insufficient_mature_sample"
    if mature_coverage_rate is None or mature_coverage_rate < 0.90:
        return "v0_insufficient_10minute_path_coverage"
    if primary_ev_pct is None:
        return "v0_insufficient_300s_ev_coverage"
    if trade_date_count < 5 or positive_day_count < 3:
        return "v0_insufficient_walk_forward_day_breadth"
    if max_date_ev_contribution_rate is None or max_date_ev_contribution_rate > 0.25:
        return "v0_blocked_date_ev_concentration"
    if eligible_positive_parent_count < 1:
        return "v0_insufficient_positive_parent_bucket_sample"
    return "v0_preliminary_candidate_risk_budget_and_forward_observation_required"


def _cost_scenarios(selected_cost_bps: float) -> tuple[float, ...]:
    return tuple(sorted({*COST_SENSITIVITY_BPS, float(selected_cost_bps)}))


def _cost_sensitivity(
    result: ReplayResult,
    trade_dates: list[str],
) -> dict[str, dict[str, Any]]:
    scenarios = _cost_scenarios(result.input_stats.conservative_total_cost_bps)
    rows: dict[str, dict[str, Any]] = {}
    for horizon_sec in DEFAULT_HORIZONS_SEC:
        dated_returns = [
            (label.trade_date, float(outcome.terminal_return_bps))
            for label in result.labels
            for outcome in label.outcomes
            if outcome.horizon_sec == horizon_sec
            and outcome.complete
            and outcome.terminal_return_bps is not None
        ]
        terminal_returns = [value for _, value in dated_returns]
        by_date: dict[str, list[float]] = defaultdict(list)
        for trade_date, value in dated_returns:
            by_date[trade_date].append(value)
        break_even_cost_bps = _avg(terminal_returns)
        scenario_rows = []
        for cost_bps in scenarios:
            adjusted_returns = [value - cost_bps for value in terminal_returns]
            daily_rows = [
                {
                    "trade_date": trade_date,
                    "sample_count": len(by_date[trade_date]),
                    "source_quality_adjusted_ev_pct": _avg(
                        [value - cost_bps for value in by_date[trade_date]],
                        divisor=100.0,
                    ),
                }
                for trade_date in trade_dates
            ]
            observed_daily_ev = [
                float(row["source_quality_adjusted_ev_pct"])
                for row in daily_rows
                if row["source_quality_adjusted_ev_pct"] is not None
            ]
            scenario_rows.append(
                {
                    "all_in_cost_bps": cost_bps,
                    "source_quality_adjusted_ev_pct": _avg(
                        adjusted_returns, divisor=100.0
                    ),
                    "diagnostic_win_rate": _rate(
                        value > 0 for value in adjusted_returns
                    ),
                    "positive_event_count": sum(
                        value > 0 for value in adjusted_returns
                    ),
                    "observed_trade_day_count": len(observed_daily_ev),
                    "positive_ev_day_count": sum(
                        value > 0 for value in observed_daily_ev
                    ),
                    "daily_metrics": daily_rows,
                }
            )
        rows[str(horizon_sec)] = {
            "horizon_sec": horizon_sec,
            "sample_count": len(terminal_returns),
            "gross_positive_event_count": sum(value > 0 for value in terminal_returns),
            "gross_diagnostic_win_rate": _rate(value > 0 for value in terminal_returns),
            "equal_weight_avg_profit_pct": _avg(terminal_returns, divisor=100.0),
            "break_even_all_in_cost_bps": break_even_cost_bps,
            "is_fast_exit_comparison_horizon": (horizon_sec in FAST_EXIT_HORIZONS_SEC),
            "scenarios": scenario_rows,
        }
    return rows


def _common_maturity_cohorts(result: ReplayResult) -> dict[str, dict[str, Any]]:
    groups = tuple(
        FAST_EXIT_HORIZONS_SEC[:index]
        for index in range(2, len(FAST_EXIT_HORIZONS_SEC) + 1)
    )
    rows: dict[str, dict[str, Any]] = {}
    for horizons in groups:
        eligible: list[tuple[Any, dict[int, Any]]] = []
        for label in result.labels:
            outcomes = {outcome.horizon_sec: outcome for outcome in label.outcomes}
            if all(
                horizon in outcomes and outcomes[horizon].complete
                for horizon in horizons
            ):
                eligible.append((label, outcomes))
        metrics: dict[str, dict[str, Any]] = {}
        for horizon in horizons:
            outcomes = [
                outcome_by_horizon[horizon] for _, outcome_by_horizon in eligible
            ]
            terminal_returns = [
                float(outcome.terminal_return_bps)
                for outcome in outcomes
                if outcome.terminal_return_bps is not None
            ]
            adjusted_returns = [
                float(outcome.cost_adjusted_terminal_return_bps)
                for outcome in outcomes
                if outcome.cost_adjusted_terminal_return_bps is not None
            ]
            metrics[str(horizon)] = {
                "horizon_sec": horizon,
                "sample_count": len(outcomes),
                "equal_weight_avg_profit_pct": _avg(terminal_returns, divisor=100.0),
                "source_quality_adjusted_ev_pct": _avg(adjusted_returns, divisor=100.0),
                "break_even_all_in_cost_bps": _avg(terminal_returns),
                "gross_diagnostic_win_rate": _rate(
                    value > 0 for value in terminal_returns
                ),
            }
        max_horizon = horizons[-1]
        rows[f"through_{max_horizon}s"] = {
            "comparison_horizons_sec": list(horizons),
            "common_event_count": len(eligible),
            "selection_authority": False,
            "metrics": metrics,
        }
    return rows


def _tax_evidence(
    result: ReplayResult,
    *,
    window_end: str | None,
    best_observed_row: dict[str, Any] | None,
) -> dict[str, Any]:
    tax_profiles = [event.tax_profile for event in result.events]
    tax_class_counts = Counter(
        event.tax_profile.instrument_tax_class.value
        for event in result.events
        if event.instrument_metadata_verified
    )
    unverified_tax_class_counts = Counter(
        event.tax_profile.instrument_tax_class.value
        for event in result.events
        if not event.instrument_metadata_verified
    )
    classified_event_count = sum(
        event.instrument_metadata_verified
        and event.tax_profile.statutory_sell_tax_bps is not None
        for event in result.events
    )
    event_count = len(tax_profiles)
    tax_classification_complete = bool(event_count) and (
        classified_event_count == event_count
    )
    policy_date = date.fromisoformat(window_end) if window_end else None
    ordinary_floor = (
        ordinary_taxable_equity_floor_bps(policy_date)
        if policy_date is not None
        else None
    )
    best_gross_bps = (
        None
        if best_observed_row is None
        else best_observed_row["break_even_all_in_cost_bps"]
    )
    statutory_margin_bps = (
        None
        if ordinary_floor is None or best_gross_bps is None
        else round(float(best_gross_bps) - ordinary_floor, 6)
    )
    aggregate_gate_passed = (
        None if statutory_margin_bps is None else statutory_margin_bps > 0
    )

    exact_rows: dict[str, dict[str, Any]] = {}
    for horizon in FAST_EXIT_HORIZONS_SEC:
        adjusted: list[float] = []
        unknown_count = 0
        for label in result.labels:
            outcome = next(
                (
                    item
                    for item in label.outcomes
                    if item.horizon_sec == horizon and item.complete
                ),
                None,
            )
            if outcome is None or outcome.terminal_return_bps is None:
                continue
            profile = tax_profile_for(
                trade_date=date.fromisoformat(label.trade_date),
                listing_market=label.listing_market,
                instrument_type=label.instrument_type,
            )
            if (
                not label.instrument_metadata_verified
                or profile.statutory_sell_tax_bps is None
            ):
                unknown_count += 1
                continue
            adjusted.append(
                float(outcome.terminal_return_bps)
                - float(profile.statutory_sell_tax_bps)
            )
        exact_rows[str(horizon)] = {
            "horizon_sec": horizon,
            "classified_sample_count": len(adjusted),
            "unknown_or_unsupported_sample_count": unknown_count,
            "statutory_tax_adjusted_ev_pct": _avg(adjusted, divisor=100.0),
        }

    exact_ev_values = [
        float(row["statutory_tax_adjusted_ev_pct"])
        for row in exact_rows.values()
        if row["statutory_tax_adjusted_ev_pct"] is not None
    ]
    return {
        "policy_version": (
            tax_profiles[0].policy_version if tax_profiles else TAX_POLICY_VERSION
        ),
        "official_source_url": (
            tax_profiles[0].source_url if tax_profiles else TAX_POLICY_SOURCE_URL
        ),
        "aggregate_gate_scope": (
            "counterfactual_assuming_ordinary_kospi_or_kosdaq_taxable_equity"
        ),
        "ordinary_taxable_equity_statutory_floor_bps": ordinary_floor,
        "best_observed_fixed_horizon": (
            None if best_observed_row is None else best_observed_row["horizon_sec"]
        ),
        "best_observed_fixed_horizon_gross_bps": best_gross_bps,
        "gross_minus_statutory_floor_bps": statutory_margin_bps,
        "aggregate_taxable_equity_economic_gate_passed": aggregate_gate_passed,
        "tax_classification_complete": tax_classification_complete,
        "classified_event_count": classified_event_count,
        "event_count": event_count,
        "classification_coverage_rate": (
            round(classified_event_count / event_count, 6) if event_count else None
        ),
        "unknown_or_unsupported_event_count": event_count - classified_event_count,
        "verified_metadata_event_count": sum(
            event.instrument_metadata_verified for event in result.events
        ),
        "instrument_tax_class_counts": dict(sorted(tax_class_counts.items())),
        "unverified_instrument_tax_class_counts": dict(
            sorted(unverified_tax_class_counts.items())
        ),
        "exact_sample_tax_adjusted_horizons": exact_rows,
        "exact_sample_tax_adjusted_best_ev_pct": (
            max(exact_ev_values)
            if tax_classification_complete and exact_ev_values
            else None
        ),
        "exact_sample_gate_status": (
            "statutory_tax_only_positive_non_tax_costs_unresolved"
            if tax_classification_complete
            and exact_ev_values
            and max(exact_ev_values) > 0
            else (
                "statutory_tax_only_non_positive"
                if tax_classification_complete and exact_ev_values
                else "blocked_missing_verified_instrument_tax_class"
            )
        ),
        "forbidden_interpretation": (
            "counterfactual_20bps_gate_is_not_event_level_tax_proof_when_"
            "verified_instrument_tax_classification_is_incomplete"
        ),
    }


def _gate_results(
    *,
    event_count: int,
    fully_mature_event_count: int,
    primary_ev_pct: float | None,
    mature_coverage_rate: float | None,
    trade_date_count: int,
    positive_day_count: int,
    max_date_ev_contribution_rate: float | None,
    eligible_positive_parent_count: int,
    tax_classification_complete: bool,
    aggregate_taxable_equity_economic_gate_passed: bool | None,
) -> list[dict[str, Any]]:
    return [
        {
            "gate": "shock_event_count_gt_0",
            "actual": event_count,
            "threshold": 1,
            "passed": event_count > 0,
        },
        {
            "gate": "fully_mature_event_count_ge_1000",
            "actual": fully_mature_event_count,
            "threshold": 1_000,
            "passed": fully_mature_event_count >= 1_000,
        },
        {
            "gate": "fully_mature_event_coverage_rate_ge_0_90",
            "actual": mature_coverage_rate,
            "threshold": 0.90,
            "passed": mature_coverage_rate is not None and mature_coverage_rate >= 0.90,
        },
        {
            "gate": "legacy_complete_case_cost_adjusted_ev_pct_300s_gt_0",
            "actual": primary_ev_pct,
            "threshold": 0.0,
            "passed": primary_ev_pct is not None and primary_ev_pct > 0,
        },
        {
            "gate": "trade_date_count_ge_5",
            "actual": trade_date_count,
            "threshold": 5,
            "passed": trade_date_count >= 5,
        },
        {
            "gate": "positive_300s_ev_day_count_ge_3",
            "actual": positive_day_count,
            "threshold": 3,
            "passed": positive_day_count >= 3,
        },
        {
            "gate": "max_date_ev_contribution_rate_le_0_25",
            "actual": max_date_ev_contribution_rate,
            "threshold": 0.25,
            "passed": max_date_ev_contribution_rate is not None
            and max_date_ev_contribution_rate <= 0.25,
        },
        {
            "gate": "eligible_positive_parent_count_ge_1",
            "actual": eligible_positive_parent_count,
            "threshold": 1,
            "passed": eligible_positive_parent_count >= 1,
        },
        {
            "gate": "instrument_tax_classification_complete",
            "actual": tax_classification_complete,
            "threshold": True,
            "passed": tax_classification_complete,
        },
        {
            "gate": "aggregate_ordinary_taxable_equity_fixed_horizon_ev_gt_0",
            "actual": aggregate_taxable_equity_economic_gate_passed,
            "threshold": True,
            "passed": aggregate_taxable_equity_economic_gate_passed is True,
        },
    ]


def _source_quality_status(result: ReplayResult) -> str:
    if not result.observations:
        return "blocked_no_usable_observations"
    excluded_or_invalid = (
        result.input_stats.invalid_json_count
        + result.input_stats.invalid_timestamp_count
        + result.input_stats.prebaseline_row_count
        + result.input_stats.missing_symbol_count
        + result.input_stats.missing_price_count
        + result.input_stats.invalid_price_count
    )
    if excluded_or_invalid:
        return "pass_with_row_exclusions"
    return "pass"


def _avg(values: list[float], *, divisor: float = 1.0) -> float | None:
    if not values:
        return None
    return round(statistics.fmean(values) / divisor, 6)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.median(values), 6)


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 6)
    position = max(0.0, min(1.0, quantile)) * (len(ordered) - 1)
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 6)


def _rate(values: Iterable[bool]) -> float | None:
    materialized = list(values)
    if not materialized:
        return None
    return round(sum(materialized) / len(materialized), 6)


def _report_id(start_date: str | None, end_date: str | None) -> str:
    if start_date and start_date == end_date:
        return f"scalp_micro_reversion_v0_{start_date}"
    if start_date and end_date:
        return f"scalp_micro_reversion_v0_{start_date}_to_{end_date}"
    return "scalp_micro_reversion_v0_empty"


def render_markdown(report: dict[str, Any]) -> str:
    decision = report["decision"]
    summary = report["summary"]
    lines = [
        f"# Scalp Micro-Reversion V0 — {report['report_id']}",
        "",
        "## 판정",
        "",
        f"- status: `{decision['status']}`",
        f"- hypothesis identified: `{decision['hypothesis_identified']}`",
        f"- gross reversion supported: `{decision['gross_reversion_hypothesis_supported']}`",
        f"- positive EV at selected cost supported: `{decision['positive_ev_hypothesis_supported']}`",
        "- aggregate taxable-equity economic gate: "
        f"`{decision['aggregate_taxable_equity_economic_gate']}`",
        f"- tax classification complete: `{decision['tax_classification_complete']}`",
        "- subcohort opportunity discovery: "
        f"`{decision['subcohort_opportunity_discovery']}`",
        f"- execution economics resolved: `{decision['execution_economics_resolved']}`",
        f"- candidate gate passed: `{decision['candidate_gate_passed']}`",
        "- applied to sim: `false`",
        "- real runtime reflected: `false`",
        "- actual_order_submitted: `false`",
        "- broker_order_forbidden: `true`",
        "",
        "## 근거",
        "",
        f"- input rows: `{summary['input_row_count']}`",
        f"- deduplicated observations: `{summary['deduplicated_observation_count']}`",
        f"- shock events: `{summary['event_count']}`",
        f"- fully mature events: `{summary['fully_mature_event_count']}`",
        "",
        "### Candidate gates",
        "",
        "| gate | actual | threshold | passed |",
        "|---|---:|---:|:---:|",
    ]
    for gate in decision["gate_results"]:
        lines.append(
            "| {gate} | {actual} | {threshold} | {passed} |".format(
                gate=gate["gate"],
                actual=_display(gate["actual"]),
                threshold=_display(gate["threshold"]),
                passed=str(gate["passed"]).lower(),
            )
        )
    lines.extend(
        [
            "",
            "| horizon | resolved/all signals | complete-case adjusted EV pct | all-signal zero-unresolved EV pct | win rate | median MFE bps | median MAE bps |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for horizon in DEFAULT_HORIZONS_SEC:
        metrics = report["horizon_metrics"][str(horizon)]
        lines.append(
            "| {horizon} | {sample}/{all_signals} | {ev} | {all_signal_ev} | {win} | {mfe} | {mae} |".format(
                horizon=horizon,
                sample=metrics["sample_count"],
                all_signals=metrics["all_detected_signal_count"],
                ev=_display(metrics["source_quality_adjusted_ev_pct"]),
                all_signal_ev=_display(
                    metrics["ev_per_all_detected_signal_zero_unresolved_pct"]
                ),
                win=_display(metrics["diagnostic_win_rate"]),
                mfe=_display(metrics["median_mfe_bps"]),
                mae=_display(metrics["median_mae_bps"]),
            )
        )
    tax_policy = report["cost_model"]["statutory_tax_policy"]
    lines.extend(
        [
            "",
            "### Statutory sell-tax gate",
            "",
            "The aggregate gate assumes an ordinary taxable KOSPI/KOSDAQ equity. "
            "It is not event-level tax proof while instrument classification is incomplete.",
            "",
            f"- ordinary taxable-equity floor bps: `{_display(tax_policy['ordinary_taxable_equity_statutory_floor_bps'])}`",
            f"- best gross minus statutory floor bps: `{_display(tax_policy['gross_minus_statutory_floor_bps'])}`",
            f"- classified events: `{tax_policy['classified_event_count']} / {tax_policy['event_count']}`",
            f"- exact sample gate: `{tax_policy['exact_sample_gate_status']}`",
            f"- raw BBO candidate rows: `{summary['raw_bbo_candidate_rows']}`",
            f"- event-joined BBO context: `{summary['event_joined_bbo_context_count']}`",
            f"- raw micro capture rows: `{summary['raw_micro_capture_rows']}`",
            f"- raw complete micro-context candidates: `{summary['raw_micro_context_candidate_rows']}`",
            f"- event-joined micro context: `{summary['event_joined_micro_context_count']}`",
            "",
            "### Common-maturity horizon comparison",
            "",
            "| cohort | common events | horizon | gross EV pct | selected-cost EV pct |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for cohort_name, cohort in report["common_maturity_cohorts"].items():
        for horizon, metrics in cohort["metrics"].items():
            lines.append(
                "| {cohort} | {count} | {horizon} | {gross} | {adjusted} |".format(
                    cohort=cohort_name,
                    count=cohort["common_event_count"],
                    horizon=horizon,
                    gross=_display(metrics["equal_weight_avg_profit_pct"]),
                    adjusted=_display(metrics["source_quality_adjusted_ev_pct"]),
                )
            )
    lines.extend(
        [
            "",
            "### All-in cost sensitivity",
            "",
            "`0bps` means friction-free, not slippage-only. Cost components are not decomposed.",
            "",
            "| horizon | break-even cost bps | EV@0bps pct | EV@5bps pct | EV@10bps pct | EV@15bps pct | EV@20bps pct | EV@23bps pct |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for horizon in DEFAULT_HORIZONS_SEC:
        sensitivity = report["cost_sensitivity"][str(horizon)]
        scenario_ev = {
            float(row["all_in_cost_bps"]): row["source_quality_adjusted_ev_pct"]
            for row in sensitivity["scenarios"]
        }
        lines.append(
            "| {horizon} | {break_even} | {ev0} | {ev5} | {ev10} | {ev15} | {ev20} | {ev23} |".format(
                horizon=horizon,
                break_even=_display(sensitivity["break_even_all_in_cost_bps"]),
                ev0=_display(scenario_ev.get(0.0)),
                ev5=_display(scenario_ev.get(5.0)),
                ev10=_display(scenario_ev.get(10.0)),
                ev15=_display(scenario_ev.get(15.0)),
                ev20=_display(scenario_ev.get(20.0)),
                ev23=_display(scenario_ev.get(23.0)),
            )
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "",
            "- Close the V0 walk-forward sample, coverage, and cost-adjusted EV gates.",
            "- Supply verified symbol-level listing-market and instrument-type metadata.",
            "- Accumulate continuous market paths before implementing entry/exit joint replay.",
            "- Keep policy candidates frozen and report resolved, unresolved, and conservative bounds separately.",
            "- Do not connect this report to sim or real order authority.",
            "- Collect forward continuous microstructure before execution-quality review.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    report: dict[str, Any],
    *,
    output_root: Path,
    test_result: str = "not_run_for_this_manifest",
) -> tuple[Path, Path, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    report_id = str(report["report_id"])
    json_path = output_root / f"{report_id}.json"
    markdown_path = output_root / f"{report_id}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    manifest_path = output_root / f"{report_id}.reproducibility.json"
    write_reproducibility_manifest(
        report=report,
        json_report_path=json_path,
        markdown_report_path=markdown_path,
        output_path=manifest_path,
        repository_root=Path(__file__).resolve().parents[4],
        test_result=test_result,
    )
    return json_path, markdown_path, manifest_path


def _display(value: object) -> str:
    return "-" if value is None else str(value)
