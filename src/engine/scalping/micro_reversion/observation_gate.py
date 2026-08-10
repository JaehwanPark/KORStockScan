"""Separate broad observation eligibility from narrow economic promotion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .tax import TaxProfile

OBSERVATION_GATE_SCHEMA = "scalp_micro_reversion_observation_gate_v2"
OBSERVATION_GATE_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_observation_eligibility_gate",
    "window_policy": "point_in_time_pre_observation_gate",
    "sample_floor": "not_applicable_hard_eligibility_contract",
    "primary_decision_metric": "observation_allowed",
    "source_quality_gate": "session_detector_and_minimum_source_contract",
    "forbidden_uses": (
        "economic_headline_from_observation_eligibility",
        "sim_or_runtime_promotion",
        "broker_order_submission",
    ),
}
ECONOMIC_GATE_METRIC_CONTRACT = {
    "metric_role": "economic_candidate_research_gate",
    "window_policy": "predeclared_out_of_sample_confirmation_window",
    "sample_floor": "owned_by_frozen_research_policy",
    "primary_decision_metric": "coverage_adjusted_lower_bound_bps",
    "source_quality_gate": "verified_tax_cost_contract_and_clustered_oos_evidence",
    "forbidden_uses": (
        "in_sample_headline_promotion",
        "sim_or_runtime_promotion_without_separate_approval",
        "broker_order_submission",
    ),
}


class ObservationStatus(StrEnum):
    OBSERVE_ELIGIBLE = "OBSERVE_ELIGIBLE"
    REJECT = "REJECT"


class EconomicCandidateStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    BLOCKED_TAX_CLASS = "BLOCKED_TAX_CLASS"
    BLOCKED_COST_CONTRACT = "BLOCKED_COST_CONTRACT"
    BLOCKED_OOS_EV_LCB = "BLOCKED_OOS_EV_LCB"
    BLOCKED_TAIL_RISK = "BLOCKED_TAIL_RISK"
    BLOCKED_CONCENTRATION = "BLOCKED_CONCENTRATION"


@dataclass(frozen=True, slots=True)
class ObservationGateResult:
    status: ObservationStatus
    reasons: tuple[str, ...]
    observation_allowed: bool
    economic_headline_allowed: bool = False
    sim_promotion_allowed: bool = False
    runtime_effect: bool = False
    broker_order_forbidden: bool = True
    decision_authority: str = "micro_reversion_observation_eligibility_only"
    metric_role: str = OBSERVATION_GATE_METRIC_CONTRACT["metric_role"]
    window_policy: str = OBSERVATION_GATE_METRIC_CONTRACT["window_policy"]
    sample_floor: str = OBSERVATION_GATE_METRIC_CONTRACT["sample_floor"]
    primary_decision_metric: str = OBSERVATION_GATE_METRIC_CONTRACT[
        "primary_decision_metric"
    ]
    source_quality_gate: str = OBSERVATION_GATE_METRIC_CONTRACT["source_quality_gate"]
    forbidden_uses: tuple[str, ...] = OBSERVATION_GATE_METRIC_CONTRACT["forbidden_uses"]
    schema: str = OBSERVATION_GATE_SCHEMA


@dataclass(frozen=True, slots=True)
class EconomicGateResult:
    status: EconomicCandidateStatus
    reasons: tuple[str, ...]
    economic_headline_allowed: bool
    sim_promotion_allowed: bool = False
    runtime_effect: bool = False
    broker_order_forbidden: bool = True
    decision_authority: str = "micro_reversion_economic_research_gate_only"
    metric_role: str = ECONOMIC_GATE_METRIC_CONTRACT["metric_role"]
    window_policy: str = ECONOMIC_GATE_METRIC_CONTRACT["window_policy"]
    sample_floor: str = ECONOMIC_GATE_METRIC_CONTRACT["sample_floor"]
    primary_decision_metric: str = ECONOMIC_GATE_METRIC_CONTRACT[
        "primary_decision_metric"
    ]
    source_quality_gate: str = ECONOMIC_GATE_METRIC_CONTRACT["source_quality_gate"]
    forbidden_uses: tuple[str, ...] = ECONOMIC_GATE_METRIC_CONTRACT["forbidden_uses"]


def evaluate_observation_gate(
    *,
    tradeable_session: bool,
    detector_condition_met: bool,
    source_contract_minimum_passed: bool,
) -> ObservationGateResult:
    reasons: list[str] = []
    if not tradeable_session:
        reasons.append("non_tradeable_session")
    if not source_contract_minimum_passed:
        reasons.append("minimum_source_contract_failed")
    if not detector_condition_met:
        reasons.append("detector_condition_not_met")
    allowed = not reasons
    return ObservationGateResult(
        status=(
            ObservationStatus.OBSERVE_ELIGIBLE if allowed else ObservationStatus.REJECT
        ),
        reasons=tuple(reasons),
        observation_allowed=allowed,
    )


def evaluate_economic_gate(
    *,
    tax_profile: TaxProfile,
    instrument_tax_class_verified: bool,
    all_in_cost_contract_complete: bool,
    oos_net_ev_lcb_bps: float | None,
    tail_risk_passed: bool,
    concentration_passed: bool,
) -> EconomicGateResult:
    checks = (
        (
            (
                not instrument_tax_class_verified
                or tax_profile.statutory_sell_tax_bps is None
            ),
            EconomicCandidateStatus.BLOCKED_TAX_CLASS,
            "exact_instrument_tax_class_missing_or_unsupported",
        ),
        (
            not all_in_cost_contract_complete,
            EconomicCandidateStatus.BLOCKED_COST_CONTRACT,
            "all_in_cost_contract_incomplete",
        ),
        (
            oos_net_ev_lcb_bps is None or oos_net_ev_lcb_bps <= 0,
            EconomicCandidateStatus.BLOCKED_OOS_EV_LCB,
            "oos_net_ev_per_signal_lcb_not_positive",
        ),
        (
            not tail_risk_passed,
            EconomicCandidateStatus.BLOCKED_TAIL_RISK,
            "tail_risk_gate_failed",
        ),
        (
            not concentration_passed,
            EconomicCandidateStatus.BLOCKED_CONCENTRATION,
            "date_or_symbol_concentration_gate_failed",
        ),
    )
    blocked_checks = tuple(
        (status, reason) for blocked, status, reason in checks if blocked
    )
    if blocked_checks:
        return EconomicGateResult(
            status=blocked_checks[0][0],
            reasons=tuple(reason for _, reason in blocked_checks),
            economic_headline_allowed=False,
        )
    return EconomicGateResult(
        status=EconomicCandidateStatus.ELIGIBLE,
        reasons=(),
        economic_headline_allowed=True,
    )
