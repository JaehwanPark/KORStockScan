from src.engine.scalping.micro_reversion.registry import (
    RegistryCandidate,
    RegistryTier,
    allocate_observation_budget,
    classify_candidate,
)


def _candidate(symbol: str, **overrides) -> RegistryCandidate:
    values = {
        "symbol": symbol,
        "tradeable": True,
        "minimum_source_contract_passed": True,
        "prior_path_evidence_passed": False,
        "exact_tax_class_verified": False,
        "priority_score": 1.0,
    }
    values.update(overrides)
    return RegistryCandidate(**values)


def test_registry_preserves_unknown_tax_discovery_observation() -> None:
    entry = classify_candidate(_candidate("000001"))
    assert entry.tier is RegistryTier.DISCOVERY
    assert entry.observation_allowed is True
    assert entry.economic_headline_allowed is False
    assert "registry_priority_as_expected_value" in entry.forbidden_uses


def test_registry_has_no_manual_control_gate() -> None:
    entry = classify_candidate(_candidate("000001"))
    assert "manual_control" not in entry.source_quality_gate


def test_core_priority_never_grants_economic_headline() -> None:
    entry = classify_candidate(
        _candidate(
            "000001",
            prior_path_evidence_passed=True,
            exact_tax_class_verified=True,
        )
    )
    assert entry.tier is RegistryTier.CORE
    assert entry.economic_headline_allowed is False


def test_budget_reserves_discovery_capacity() -> None:
    entries = [
        classify_candidate(
            _candidate(
                f"{index:06d}",
                prior_path_evidence_passed=index < 8,
                priority_score=float(20 - index),
            )
        )
        for index in range(10)
    ]
    selected = allocate_observation_budget(
        entries,
        max_symbols=5,
        discovery_fraction=0.2,
        rotation_key="2026-08-08",
    )
    assert len(selected) == 5
    assert sum(entry.tier is RegistryTier.DISCOVERY for entry in selected) == 1
