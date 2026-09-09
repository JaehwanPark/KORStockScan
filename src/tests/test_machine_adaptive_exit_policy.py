from dataclasses import replace

import pytest

from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    EVIDENCE_SCHEMA,
    EvaluationContract,
    assess_research_evidence,
    canonical_sha256,
    assess_sample_attainability,
)


def contract():
    # Synthetic test contract, NOT proposed production risk/floor settings.
    return EvaluationContract(
        "contract",
        "scope",
        "policy",
        "2026-09-01",
        "2026-09-02",
        "2026-09-09",
        8,
        3,
        3,
        85,
        20,
        0.005,
        0.01,
    )


def evidence():
    data = {
        "schema": EVIDENCE_SCHEMA,
        "authority": dict(AUTHORITY),
        "evaluation_contract_hash": "contract",
        "scope_key": "scope",
        "policy_hash": "policy",
        "holdout_start": "2026-09-02",
        "holdout_end": "2026-09-09",
        "source_quality_valid": True,
        "cost_contract_valid": True,
        "purged_split_valid": True,
        "unique_episodes": 8,
        "holdout_unique_episodes": 3,
        "observed_days": 3,
        "resolved_coverage_pct": 90,
        "right_censored_pct": 10,
        "p10_deterioration_pct_points": 0,
        "primary_paired_net_ev_uplift_pct_points": 0.01,
        "holdout_paired_net_ev_uplift_pct_points": 0.01,
        "primary_paired_net_pnl_uplift_krw": 100,
        "holdout_paired_net_pnl_uplift_krw": 30,
        "primary_candidate_net_ev_pct": 0.01,
        "holdout_candidate_net_ev_pct": 0.01,
    }
    data["canonical_sha256"] = canonical_sha256(data)
    return data


def test_zero_baseline_absolute_uplift_can_pass_research_not_live():
    result = assess_research_evidence(evidence(), contract())
    assert result["decision"] == "research_ready"
    assert result["eligible_for_next_preopen"] is False
    assert result["authority"] == AUTHORITY
    assert "owner_adapter" in result["runtime_blocker"]


def test_holdout_noninferiority_does_not_require_repeating_primary_uplift_floor():
    data = evidence()
    data["holdout_paired_net_ev_uplift_pct_points"] = 0
    data["holdout_paired_net_pnl_uplift_krw"] = 0
    data["canonical_sha256"] = canonical_sha256(data)
    assert assess_research_evidence(data, contract())["decision"] == "research_ready"


@pytest.mark.parametrize(
    "field,value",
    [
        ("authority", []),
        ("authority", {**AUTHORITY, "runtime_effect": 0}),
        ("schema", "legacy"),
        ("unique_episodes", True),
        ("unique_episodes", 7),
        ("holdout_unique_episodes", 0),
        ("observed_days", 0),
        ("resolved_coverage_pct", 101),
        ("right_censored_pct", -1),
        ("primary_paired_net_ev_uplift_pct_points", 0),
        ("holdout_candidate_net_ev_pct", None),
        ("primary_candidate_net_ev_pct", -0.1),
        ("primary_paired_net_pnl_uplift_krw", 0),
        ("p10_deterioration_pct_points", 0.02),
        ("cost_contract_valid", "true"),
        ("purged_split_valid", False),
        ("evaluation_contract_hash", "candidate_chooses_weaker_contract"),
        ("scope_key", "other_owner"),
        ("holdout_end", "2026-10-09"),
    ],
)
def test_invalid_or_under_floor_evidence_does_not_apply(field, value):
    data = evidence()
    data[field] = value
    data["canonical_sha256"] = canonical_sha256(data)
    result = assess_research_evidence(data, contract())
    assert result["decision"] == "research_blocked"
    assert result["errors"] and not result["eligible_for_next_preopen"]


def test_tamper_and_nan_cannot_match_digest():
    data = evidence()
    data["unique_episodes"] = 100
    assert (
        "evidence_digest_invalid"
        in assess_research_evidence(data, contract())["errors"]
    )
    data["unique_episodes"] = float("nan")
    assert assess_research_evidence(data, contract())["decision"] == "research_blocked"


@pytest.mark.parametrize(
    "patch",
    [
        {"minimum_unique_episodes": 0},
        {"minimum_unique_episodes": True},
        {"minimum_holdout_episodes": 9},
        {"minimum_resolved_coverage_pct": 0},
        {"maximum_censored_pct": 100},
        {"minimum_absolute_uplift_pct_points": 0},
        {"train_end": "2026-09-02"},
        {"train_end": "2026-06-04"},
    ],
)
def test_evaluation_contract_must_be_explicit_clean_and_non_circular(patch):
    with pytest.raises(ValueError):
        replace(contract(), **patch)


def test_eta_counts_zero_days_and_rolling_expiry_not_just_positive_days():
    result = assess_sample_attainability(
        daily_mature_unique_counts=(0, 0, 4),
        minimum=10,
        rolling_trading_days=5,
        daily_hard_capacity=None,
    )
    assert result["reason"] == "rolling_floor_unreachable_at_observed_rate"
    assert result["projected_trading_days_to_floor"] is None
    result = assess_sample_attainability(
        daily_mature_unique_counts=(2, 2),
        minimum=6,
        rolling_trading_days=5,
        daily_hard_capacity=3,
    )
    assert result["projected_trading_days_to_floor"] == 1


def test_only_declared_impossible_capacity_is_structural_not_an_empty_day():
    result = assess_sample_attainability(
        daily_mature_unique_counts=(0, 0),
        minimum=6,
        rolling_trading_days=5,
        daily_hard_capacity=1,
    )
    assert result["status"] == "structural_population_exhaustion"
    result = assess_sample_attainability(
        daily_mature_unique_counts=(0, 0),
        minimum=6,
        rolling_trading_days=5,
        daily_hard_capacity=None,
    )
    assert result["status"] == "blocked_missing_evidence"


def test_impossible_population_summary_rejected():
    data = evidence()
    data["holdout_unique_episodes"] = 99
    data["canonical_sha256"] = canonical_sha256(data)
    assert (
        "holdout_count_exceeds_unique_population"
        in assess_research_evidence(data, contract())["errors"]
    )
