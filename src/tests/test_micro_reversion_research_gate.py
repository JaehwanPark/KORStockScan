from datetime import date

import pytest

from src.engine.scalping.micro_reversion.research_gate import (
    PolicyCandidateDefinition,
    PolicySignalOutcome,
    ResearchGateConfig,
    apply_multiple_test_control,
    evaluate_policy_candidate,
)


def _definition(policy_id: str = "policy-1") -> PolicyCandidateDefinition:
    return PolicyCandidateDefinition(
        policy_id=policy_id,
        discovery_start=date(2026, 7, 1),
        discovery_end=date(2026, 7, 31),
        confirmation_start=date(2026, 8, 1),
        confirmation_end=date(2026, 8, 10),
        predeclared_parent_cohort="shock_severe_liquid",
        child_cohort_sample_floor=10,
        policy_frozen_at="2026-07-31T18:00:00+09:00",
        multiple_test_family_id="family-1",
        selection_reason="predeclared discovery winner",
    )


def _outcomes(value: float = 20.0):
    return [
        PolicySignalOutcome(
            signal_id=f"signal-{index}",
            trade_date=date(2026, 8, 1 + index % 5),
            symbol=f"{index % 5:06d}",
            parent_wave_id=f"wave-{index}",
            parent_cohort="shock_severe_liquid",
            net_policy_return_bps=value + (index % 3),
            fill_fraction=1.0,
            resolved=True,
        )
        for index in range(100)
    ]


def test_clustered_lcb_and_multiple_test_gate() -> None:
    result = evaluate_policy_candidate(
        _definition(),
        _outcomes(),
        config=ResearchGateConfig(max_date_contribution_rate=0.5),
    )
    controlled = apply_multiple_test_control([result])

    assert result.coverage_adjusted_lower_bound_bps > 0
    assert controlled[0].candidate_gate_passed is True
    assert controlled[0].multiple_test_q_value == 0.0


def test_unresolved_signals_are_visible_in_bounds() -> None:
    rows = _outcomes()[:10]
    rows.append(
        PolicySignalOutcome(
            signal_id="unresolved",
            trade_date=date(2026, 8, 5),
            symbol="000004",
            parent_wave_id="wave-unresolved",
            parent_cohort="shock_severe_liquid",
            net_policy_return_bps=None,
            fill_fraction=None,
            resolved=False,
        )
    )
    result = evaluate_policy_candidate(
        _definition(),
        rows,
        config=ResearchGateConfig(
            min_parent_waves=10,
            max_date_contribution_rate=1,
            max_symbol_contribution_rate=1,
        ),
    )

    assert result.unresolved_execution_count == 1
    assert result.conservative_fill_bound_ev_bps < result.ev_per_all_signal_bps


def test_policy_must_be_frozen_before_confirmation() -> None:
    with pytest.raises(ValueError, match="frozen before confirmation"):
        PolicyCandidateDefinition(
            policy_id="lookahead",
            discovery_start=date(2026, 7, 1),
            discovery_end=date(2026, 7, 31),
            confirmation_start=date(2026, 8, 1),
            confirmation_end=date(2026, 8, 10),
            predeclared_parent_cohort="cohort",
            child_cohort_sample_floor=10,
            policy_frozen_at="2026-08-01T00:00:00+09:00",
            multiple_test_family_id="family-1",
            selection_reason="invalid hindsight",
        )


def test_confirmation_rows_must_match_frozen_parent_cohort() -> None:
    rows = _outcomes()[:10]
    rows[0] = PolicySignalOutcome(
        signal_id="mismatch",
        trade_date=date(2026, 8, 1),
        symbol="000001",
        parent_wave_id="wave-mismatch",
        parent_cohort="unfrozen_child",
        net_policy_return_bps=10.0,
        fill_fraction=1.0,
        resolved=True,
    )

    with pytest.raises(ValueError, match="predeclared_parent_cohort"):
        evaluate_policy_candidate(_definition(), rows)
