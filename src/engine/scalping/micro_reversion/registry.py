"""CORE/DISCOVERY opportunity registry for broad source-only observation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from .contracts import normalize_symbol

REGISTRY_SCHEMA = "scalp_micro_reversion_opportunity_registry_v2"
REGISTRY_METRIC_CONTRACT = {
    "metric_role": "observation_budget_priority",
    "window_policy": "daily_registry_with_deterministic_discovery_rotation",
    "sample_floor": "not_an_economic_promotion_metric",
    "primary_decision_metric": "registry_tier",
    "source_quality_gate": "tradeability_and_minimum_source_contract",
    "forbidden_uses": (
        "registry_priority_as_expected_value",
        "tax_unknown_as_economic_candidate",
        "sim_or_runtime_promotion",
        "broker_order_submission",
    ),
}


class RegistryTier(StrEnum):
    CORE = "CORE"
    DISCOVERY = "DISCOVERY"
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class RegistryCandidate:
    symbol: str
    tradeable: bool
    minimum_source_contract_passed: bool
    prior_path_evidence_passed: bool
    exact_tax_class_verified: bool
    priority_score: float = 0.0

    def __post_init__(self) -> None:
        symbol = normalize_symbol(self.symbol)
        if not symbol:
            raise ValueError("symbol is required")
        if not math.isfinite(self.priority_score):
            raise ValueError("priority_score must be finite")
        object.__setattr__(self, "symbol", symbol)


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    symbol: str
    tier: RegistryTier
    reasons: tuple[str, ...]
    priority_score: float
    observation_allowed: bool
    economic_headline_allowed: bool
    sim_promotion_allowed: bool = False
    runtime_effect: bool = False
    broker_order_forbidden: bool = True
    decision_authority: str = "observation_budget_priority_only"
    metric_role: str = REGISTRY_METRIC_CONTRACT["metric_role"]
    window_policy: str = REGISTRY_METRIC_CONTRACT["window_policy"]
    sample_floor: str = REGISTRY_METRIC_CONTRACT["sample_floor"]
    primary_decision_metric: str = REGISTRY_METRIC_CONTRACT["primary_decision_metric"]
    source_quality_gate: str = REGISTRY_METRIC_CONTRACT["source_quality_gate"]
    forbidden_uses: tuple[str, ...] = REGISTRY_METRIC_CONTRACT["forbidden_uses"]
    schema: str = REGISTRY_SCHEMA


def classify_candidate(candidate: RegistryCandidate) -> RegistryEntry:
    hard_reasons: list[str] = []
    if not candidate.tradeable:
        hard_reasons.append("not_tradeable")
    if not candidate.minimum_source_contract_passed:
        hard_reasons.append("minimum_source_contract_failed")
    if hard_reasons:
        return RegistryEntry(
            symbol=candidate.symbol,
            tier=RegistryTier.REJECT,
            reasons=tuple(hard_reasons),
            priority_score=candidate.priority_score,
            observation_allowed=False,
            economic_headline_allowed=False,
        )
    if candidate.prior_path_evidence_passed:
        reasons = (
            "prior_path_evidence",
            (
                "exact_tax_class_verified"
                if candidate.exact_tax_class_verified
                else "tax_class_unknown_observe_only"
            ),
        )
        return RegistryEntry(
            symbol=candidate.symbol,
            tier=RegistryTier.CORE,
            reasons=reasons,
            priority_score=candidate.priority_score,
            observation_allowed=True,
            economic_headline_allowed=False,
        )
    return RegistryEntry(
        symbol=candidate.symbol,
        tier=RegistryTier.DISCOVERY,
        reasons=(
            "insufficient_or_missing_prior_path_evidence",
            (
                "exact_tax_class_verified"
                if candidate.exact_tax_class_verified
                else "tax_class_unknown_observe_only"
            ),
        ),
        priority_score=candidate.priority_score,
        observation_allowed=True,
        economic_headline_allowed=False,
    )


def allocate_observation_budget(
    entries: Iterable[RegistryEntry],
    *,
    max_symbols: int,
    discovery_fraction: float = 0.20,
    rotation_key: str,
) -> tuple[RegistryEntry, ...]:
    """Allocate a fixed discovery reserve and deterministic rotation."""

    if max_symbols <= 0:
        raise ValueError("max_symbols must be positive")
    if not 0 <= discovery_fraction <= 1:
        raise ValueError("discovery_fraction must be between 0 and 1")
    materialized = tuple(entries)
    core = sorted(
        (entry for entry in materialized if entry.tier is RegistryTier.CORE),
        key=lambda entry: (-entry.priority_score, entry.symbol),
    )
    discovery = sorted(
        (entry for entry in materialized if entry.tier is RegistryTier.DISCOVERY),
        key=lambda entry: _rotation_rank(entry.symbol, rotation_key),
    )
    discovery_budget = min(
        len(discovery),
        max_symbols,
        max(1 if discovery else 0, math.ceil(max_symbols * discovery_fraction)),
    )
    core_budget = max_symbols - discovery_budget
    selected = core[:core_budget] + discovery[:discovery_budget]
    remaining = max_symbols - len(selected)
    if remaining > 0:
        selected.extend(core[core_budget : core_budget + remaining])
        remaining = max_symbols - len(selected)
    if remaining > 0:
        selected.extend(discovery[discovery_budget : discovery_budget + remaining])
    return tuple(selected)


def _rotation_rank(symbol: str, rotation_key: str) -> str:
    return hashlib.sha256(f"{rotation_key}|{symbol}".encode("ascii")).hexdigest()
