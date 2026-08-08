"""Confirmation-window economic research gates for micro-reversion policies."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from statistics import NormalDist
from typing import Any, Iterable, Mapping

from .contracts import normalize_symbol

RESEARCH_GATE_SCHEMA = "scalp_micro_reversion_research_gate_v1"
RESEARCH_GATE_METRIC_CONTRACT = {
    "metric_role": "primary_ev_confirmation_gate",
    "window_policy": "predeclared_discovery_then_non_overlapping_confirmation",
    "sample_floor": "policy_child_floor_plus_date_symbol_and_parent_wave_breadth",
    "primary_decision_metric": "coverage_adjusted_lower_bound_bps",
    "source_quality_gate": "resolved_and_unresolved_execution_coverage_with_cluster_provenance",
    "forbidden_uses": (
        "complete_case_ev_as_headline_ev",
        "recovery_rate_as_primary_metric",
        "uncontrolled_multiple_testing",
        "sim_or_runtime_promotion",
        "broker_order_submission",
    ),
}


@dataclass(frozen=True, slots=True)
class PolicyCandidateDefinition:
    policy_id: str
    discovery_start: date
    discovery_end: date
    confirmation_start: date
    confirmation_end: date
    predeclared_parent_cohort: str
    child_cohort_sample_floor: int
    policy_frozen_at: str
    multiple_test_family_id: str
    selection_reason: str

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.predeclared_parent_cohort.strip():
            raise ValueError("policy_id and predeclared_parent_cohort are required")
        if self.discovery_end < self.discovery_start:
            raise ValueError("discovery window is invalid")
        if self.confirmation_end < self.confirmation_start:
            raise ValueError("confirmation window is invalid")
        if self.discovery_end >= self.confirmation_start:
            raise ValueError("discovery and confirmation windows must not overlap")
        if self.child_cohort_sample_floor <= 0:
            raise ValueError("child_cohort_sample_floor must be positive")
        frozen_at = _parse_aware_timestamp(self.policy_frozen_at)
        if frozen_at.date() >= self.confirmation_start:
            raise ValueError("policy must be frozen before confirmation begins")
        if (
            not self.multiple_test_family_id.strip()
            or not self.selection_reason.strip()
        ):
            raise ValueError("multiple-test family and selection reason are required")


@dataclass(frozen=True, slots=True)
class PolicySignalOutcome:
    signal_id: str
    trade_date: date
    symbol: str
    parent_wave_id: str
    parent_cohort: str
    net_policy_return_bps: float | None
    fill_fraction: float | None
    resolved: bool

    def __post_init__(self) -> None:
        if (
            not self.signal_id.strip()
            or not self.symbol.strip()
            or not self.parent_wave_id
            or not self.parent_cohort.strip()
        ):
            raise ValueError(
                "signal, symbol, parent_wave_id, and parent_cohort are required"
            )
        if self.fill_fraction is not None and not 0 <= self.fill_fraction <= 1:
            raise ValueError("fill_fraction must be between 0 and 1")
        if self.resolved and (
            self.net_policy_return_bps is None or self.fill_fraction is None
        ):
            raise ValueError("resolved outcomes require return and fill fraction")
        if not self.resolved and (
            self.net_policy_return_bps is not None or self.fill_fraction is not None
        ):
            raise ValueError("unresolved outcomes must not carry final return or fill")
        if self.net_policy_return_bps is not None and not math.isfinite(
            self.net_policy_return_bps
        ):
            raise ValueError("net_policy_return_bps must be finite")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))

    @property
    def ev_contribution_bps(self) -> float | None:
        if not self.resolved:
            return None
        return float(self.fill_fraction) * float(self.net_policy_return_bps)


@dataclass(frozen=True, slots=True)
class ResearchGateConfig:
    confidence_level: float = 0.95
    unresolved_conservative_bps: float = -50.0
    unresolved_optimistic_bps: float = 0.0
    min_trade_dates: int = 5
    min_symbols: int = 5
    min_parent_waves: int = 100
    max_date_contribution_rate: float = 0.35
    max_symbol_contribution_rate: float = 0.35
    max_p95_policy_loss_bps: float = 80.0
    fdr_alpha: float = 0.05

    def __post_init__(self) -> None:
        if not 0.5 < self.confidence_level < 1:
            raise ValueError("confidence_level must be between 0.5 and 1")
        if self.unresolved_conservative_bps > self.unresolved_optimistic_bps:
            raise ValueError("conservative unresolved bound exceeds optimistic bound")
        if min(self.min_trade_dates, self.min_symbols, self.min_parent_waves) <= 0:
            raise ValueError("sample floors must be positive")
        if not 0 < self.max_date_contribution_rate <= 1:
            raise ValueError("max_date_contribution_rate must be in (0, 1]")
        if not 0 < self.max_symbol_contribution_rate <= 1:
            raise ValueError("max_symbol_contribution_rate must be in (0, 1]")
        if self.max_p95_policy_loss_bps <= 0:
            raise ValueError("max_p95_policy_loss_bps must be positive")
        if not 0 < self.fdr_alpha < 1:
            raise ValueError("fdr_alpha must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ResearchGateResult:
    policy_id: str
    multiple_test_family_id: str
    all_detected_signal_count: int
    resolved_execution_count: int
    unresolved_execution_count: int
    complete_case_net_ev_bps: float | None
    ev_per_all_signal_bps: float | None
    optimistic_fill_bound_ev_bps: float | None
    conservative_fill_bound_ev_bps: float | None
    coverage_adjusted_lower_bound_bps: float | None
    net_ev_per_filled_trade_bps: float | None
    expected_fill_fraction: float | None
    p95_policy_loss_bps: float | None
    max_date_contribution_rate: float | None
    max_symbol_contribution_rate: float | None
    trade_date_count: int
    symbol_count: int
    parent_wave_count: int
    one_sided_p_value: float | None
    multiple_test_q_value: float | None
    pre_multiple_test_gate_passed: bool
    candidate_gate_passed: bool
    blocker_reasons: tuple[str, ...]
    recovery_rate_role: str = "diagnostic_only"
    actual_order_submitted: bool = False
    broker_order_forbidden: bool = True
    runtime_effect: bool = False
    decision_authority: str = "confirmation_research_only_no_sim_promotion"
    metric_role: str = RESEARCH_GATE_METRIC_CONTRACT["metric_role"]
    window_policy: str = RESEARCH_GATE_METRIC_CONTRACT["window_policy"]
    sample_floor: str = RESEARCH_GATE_METRIC_CONTRACT["sample_floor"]
    primary_decision_metric: str = RESEARCH_GATE_METRIC_CONTRACT[
        "primary_decision_metric"
    ]
    source_quality_gate: str = RESEARCH_GATE_METRIC_CONTRACT["source_quality_gate"]
    forbidden_uses: tuple[str, ...] = RESEARCH_GATE_METRIC_CONTRACT["forbidden_uses"]
    schema: str = RESEARCH_GATE_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_policy_candidate(
    definition: PolicyCandidateDefinition,
    outcomes: Iterable[PolicySignalOutcome],
    *,
    config: ResearchGateConfig | None = None,
) -> ResearchGateResult:
    gate_config = config or ResearchGateConfig()
    rows = tuple(
        outcome
        for outcome in outcomes
        if definition.confirmation_start
        <= outcome.trade_date
        <= definition.confirmation_end
    )
    mismatched_cohorts = {
        row.parent_cohort
        for row in rows
        if row.parent_cohort != definition.predeclared_parent_cohort
    }
    if mismatched_cohorts:
        raise ValueError("confirmation outcomes must match predeclared_parent_cohort")
    signal_ids = [row.signal_id for row in rows]
    if len(set(signal_ids)) != len(signal_ids):
        raise ValueError("signal_id must be unique within a candidate evaluation")
    resolved = tuple(row for row in rows if row.ev_contribution_bps is not None)
    unresolved_count = len(rows) - len(resolved)
    resolved_values = [float(row.ev_contribution_bps) for row in resolved]
    all_zero_bound_values = resolved_values + [0.0] * unresolved_count
    conservative_values_by_row = {
        row.signal_id: (
            float(row.ev_contribution_bps)
            if row.ev_contribution_bps is not None
            else gate_config.unresolved_conservative_bps
        )
        for row in rows
    }
    optimistic_values = (
        resolved_values + [gate_config.unresolved_optimistic_bps] * unresolved_count
    )
    conservative_values = (
        resolved_values + [gate_config.unresolved_conservative_bps] * unresolved_count
    )
    cluster_means = _cluster_means(rows, conservative_values_by_row)
    lcb, p_value = _normal_lcb_and_pvalue(
        cluster_means,
        confidence_level=gate_config.confidence_level,
    )
    filled_rows = tuple(
        row
        for row in resolved
        if row.fill_fraction is not None and row.fill_fraction > 0
    )
    raw_policy_returns = [
        float(row.net_policy_return_bps)
        for row in filled_rows
        if row.net_policy_return_bps is not None
    ]
    fill_fractions = [
        float(row.fill_fraction) for row in resolved if row.fill_fraction is not None
    ]
    date_contribution = _max_contribution_rate(resolved, key="date")
    symbol_contribution = _max_contribution_rate(resolved, key="symbol")
    p95_loss = _p95_loss(raw_policy_returns)
    blockers: list[str] = []
    if len(rows) < definition.child_cohort_sample_floor:
        blockers.append("child_cohort_sample_floor_not_met")
    trade_date_count = len({row.trade_date for row in rows})
    symbol_count = len({row.symbol for row in rows})
    parent_wave_count = len({row.parent_wave_id for row in rows})
    if trade_date_count < gate_config.min_trade_dates:
        blockers.append("trade_date_breadth_not_met")
    if symbol_count < gate_config.min_symbols:
        blockers.append("symbol_breadth_not_met")
    if parent_wave_count < gate_config.min_parent_waves:
        blockers.append("independent_parent_wave_floor_not_met")
    if lcb is None or lcb <= 0:
        blockers.append("net_ev_per_signal_clustered_lcb_not_positive")
    if p95_loss is None or p95_loss > gate_config.max_p95_policy_loss_bps:
        blockers.append("p95_policy_loss_budget_failed")
    if (
        date_contribution is None
        or date_contribution > gate_config.max_date_contribution_rate
    ):
        blockers.append("date_contribution_concentration_failed")
    if (
        symbol_contribution is None
        or symbol_contribution > gate_config.max_symbol_contribution_rate
    ):
        blockers.append("symbol_contribution_concentration_failed")
    return ResearchGateResult(
        policy_id=definition.policy_id,
        multiple_test_family_id=definition.multiple_test_family_id,
        all_detected_signal_count=len(rows),
        resolved_execution_count=len(resolved),
        unresolved_execution_count=unresolved_count,
        complete_case_net_ev_bps=_mean(resolved_values),
        ev_per_all_signal_bps=_mean(all_zero_bound_values),
        optimistic_fill_bound_ev_bps=_mean(optimistic_values),
        conservative_fill_bound_ev_bps=_mean(conservative_values),
        coverage_adjusted_lower_bound_bps=lcb,
        net_ev_per_filled_trade_bps=_mean(raw_policy_returns),
        expected_fill_fraction=(
            None if not rows else round(sum(fill_fractions) / len(rows), 8)
        ),
        p95_policy_loss_bps=p95_loss,
        max_date_contribution_rate=date_contribution,
        max_symbol_contribution_rate=symbol_contribution,
        trade_date_count=trade_date_count,
        symbol_count=symbol_count,
        parent_wave_count=parent_wave_count,
        one_sided_p_value=p_value,
        multiple_test_q_value=None,
        pre_multiple_test_gate_passed=not blockers,
        candidate_gate_passed=False,
        blocker_reasons=tuple(blockers),
    )


def apply_multiple_test_control(
    results: Iterable[ResearchGateResult],
    *,
    fdr_alpha: float = 0.05,
) -> tuple[ResearchGateResult, ...]:
    """Apply Benjamini-Hochberg within each declared test family."""

    if not 0 < fdr_alpha < 1:
        raise ValueError("fdr_alpha must be between 0 and 1")
    materialized = tuple(results)
    grouped: dict[str, list[ResearchGateResult]] = defaultdict(list)
    for result in materialized:
        grouped[result.multiple_test_family_id].append(result)
    replacements: dict[tuple[str, str], ResearchGateResult] = {}
    for family_id, family_results in grouped.items():
        policy_ids = [result.policy_id for result in family_results]
        if len(set(policy_ids)) != len(policy_ids):
            raise ValueError(f"duplicate policy_id in multiple-test family {family_id}")
        pvalues = {
            result.policy_id: (
                1.0 if result.one_sided_p_value is None else result.one_sided_p_value
            )
            for result in family_results
        }
        qvalues = _benjamini_hochberg_qvalues(pvalues)
        for result in family_results:
            qvalue = qvalues[result.policy_id]
            passed = result.pre_multiple_test_gate_passed and qvalue <= fdr_alpha
            blockers = list(result.blocker_reasons)
            if result.pre_multiple_test_gate_passed and qvalue > fdr_alpha:
                blockers.append("multiple_test_fdr_failed")
            replacements[(family_id, result.policy_id)] = replace(
                result,
                multiple_test_q_value=round(qvalue, 8),
                candidate_gate_passed=passed,
                blocker_reasons=tuple(blockers),
            )
    return tuple(
        replacements[(result.multiple_test_family_id, result.policy_id)]
        for result in materialized
    )


def _cluster_means(
    rows: tuple[PolicySignalOutcome, ...],
    values_by_signal: Mapping[str, float],
) -> list[float]:
    clustered: dict[tuple[date, str, str], list[float]] = defaultdict(list)
    for row in rows:
        clustered[(row.trade_date, row.symbol, row.parent_wave_id)].append(
            values_by_signal[row.signal_id]
        )
    return [statistics.fmean(values) for values in clustered.values()]


def _normal_lcb_and_pvalue(
    cluster_means: list[float],
    *,
    confidence_level: float,
) -> tuple[float | None, float | None]:
    if len(cluster_means) < 2:
        return None, None
    mean = statistics.fmean(cluster_means)
    standard_error = statistics.stdev(cluster_means) / math.sqrt(len(cluster_means))
    if standard_error == 0:
        return (round(mean, 8), 0.0 if mean > 0 else 1.0)
    z_value = NormalDist().inv_cdf(confidence_level)
    lcb = mean - z_value * standard_error
    one_sided_p = 1.0 - NormalDist().cdf(mean / standard_error)
    return round(lcb, 8), round(one_sided_p, 8)


def _max_contribution_rate(
    rows: tuple[PolicySignalOutcome, ...],
    *,
    key: str,
) -> float | None:
    grouped: dict[object, float] = defaultdict(float)
    for row in rows:
        value = row.ev_contribution_bps
        if value is None:
            continue
        group_key = row.trade_date if key == "date" else row.symbol
        grouped[group_key] += abs(float(value))
    total = sum(grouped.values())
    if total <= 0:
        return None
    return round(max(grouped.values()) / total, 8)


def _p95_loss(values: list[float]) -> float | None:
    if not values:
        return None
    ordered_losses = sorted(max(0.0, -value) for value in values)
    index = math.ceil(0.95 * len(ordered_losses)) - 1
    return round(ordered_losses[max(0, index)], 8)


def _mean(values: list[float]) -> float | None:
    return None if not values else round(statistics.fmean(values), 8)


def _benjamini_hochberg_qvalues(pvalues: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    qvalues: dict[str, float] = {}
    running = 1.0
    for rank, (policy_id, pvalue) in reversed(tuple(enumerate(ordered, start=1))):
        running = min(running, float(pvalue) * count / rank)
        qvalues[policy_id] = max(0.0, min(1.0, running))
    return qvalues


def _parse_aware_timestamp(value: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("policy_frozen_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("policy_frozen_at must include a timezone offset")
    return parsed
