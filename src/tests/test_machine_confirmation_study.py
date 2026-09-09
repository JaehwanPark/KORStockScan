from copy import deepcopy
from datetime import date
import json

from src.tests.test_machine_entry_timing_tuning import _entry_row
from src.engine.monitoring.machine_entry_confirmation_study import (
    build_study,
    _decisions,
)
from src.engine.automation.machine_entry_timing_tuning import (
    _dynamic_baseline_observation,
    _study_economic_observer,
    build_applied_policy,
    write_outputs,
)
from src.trading.config.machine_entry_timing_policy import load_applied_policy
from src.trading.market.micro_confirmation import evaluate_dynamic_micro_confirmation


def _immediate(day, index=1):
    row = _entry_row(day, index)
    feature = row["entry_confirmation_checkpoint_ask_depletion"]["checkpoint_reports"][
        "0"
    ]["horizons"][0]
    feature["aggressive_buy_trade_backed_ratio"] = 0.8
    prior = row["dynamic_confirmation_source_only_replay"]
    point = {
        **prior["checkpoint_decisions"][0],
        "aggressive_buy_trade_backed_ratio": 0.8,
    }
    replay = evaluate_dynamic_micro_confirmation({0: point})
    replay["signal_binding"] = prior["signal_binding"]
    row["dynamic_confirmation_source_only_replay"] = replay
    return row


def test_actual_immediate_control_does_not_require_hypothetical_first_hit():
    day = date(2026, 8, 27)
    row = _immediate(day)
    row.pop("dynamic_confirmation_first_hit_outcomes")
    result = _dynamic_baseline_observation(source_date=day, row=row)
    assert result is not None
    assert result["first_hit_label_quality"] == "unavailable_or_invalid"
    assert result["counterfactual_first_hit_state"] is None
    assert result["candidate_net_pct"] == result["baseline_net_pct"]
    row["owner_outcome"]["cost_aware_net_return_pct"] = None
    assert _dynamic_baseline_observation(source_date=day, row=row) is None


def test_delayed_counterfactual_still_requires_executable_label():
    day = date(2026, 8, 27)
    row = _entry_row(day, 1)
    assert _dynamic_baseline_observation(source_date=day, row=row) is not None
    row.pop("dynamic_confirmation_first_hit_outcomes")
    assert _dynamic_baseline_observation(source_date=day, row=row) is None


def test_four_arm_research_pairs_same_population_and_keeps_holdout_separate():
    rows = [
        (day, _immediate(day, i))
        for i, day in enumerate((date(2026, 8, 26), date(2026, 8, 27)))
    ]
    result = build_study(cohort_rows=rows, economic_observer=_study_economic_observer)
    assert result["common_paired_count"] == 2
    assert result["holdout_date"] == "2026-08-27"
    assert result["runtime_effect"] is False
    assert result["allowed_runtime_apply"] is False
    for arm in result["arms"].values():
        assert arm["all"]["paired_count"] == 2
        assert arm["training"]["paired_count"] == arm["holdout"]["paired_count"] == 1
        assert arm["all"]["modeled_profit_uplift_krw"] == 0
        assert arm["all"]["net_ev_pct"] > 0


def test_missing_or_partial_outcomes_are_census_not_zero_profit():
    day = date(2026, 8, 27)
    row = _immediate(day)
    row["owner_outcome"]["quantity"] = 5
    unfilled = _immediate(day, 2)
    unfilled["owner_outcome"] = {}
    unsubmitted = _immediate(day, 3)
    unsubmitted["actual_order_submitted"] = False
    result = build_study(
        cohort_rows=[(day, row), (day, unfilled), (day, unsubmitted)],
        economic_observer=_study_economic_observer,
    )
    assert result["common_paired_count"] == 0
    assert sum(result["outcome_census"].values()) == 3
    for arm in result["arms"].values():
        assert arm["all"]["net_ev_pct"] is None
        assert arm["all"]["modeled_net_profit_krw"] is None


def test_causal_decision_is_independent_of_future_outcome_label():
    day = date(2026, 8, 27)
    row = _immediate(day)
    before = _decisions(row)
    row["dynamic_confirmation_first_hit_outcomes"] = {"fake_future": "adverse"}
    row["owner_outcome"]["cost_aware_net_return_pct"] = -999
    assert _decisions(row) == before


def test_fixed_price_refill_changes_flow_arms_but_not_bid_only():
    row = _immediate(date(2026, 8, 27))
    row["entry_confirmation_checkpoint_ask_depletion"]["checkpoint_reports"]["0"][
        "horizons"
    ][0]["refill_ratio"] = 1.0
    decisions = _decisions(row)
    assert decisions["baseline"]["terminal_action"] == "ENTER"
    assert decisions["bid_rebound"]["terminal_action"] == "ENTER"
    assert decisions["depletion_flow"]["terminal_action"] == "REJECT"
    assert decisions["combined"]["terminal_action"] == "REJECT"


def test_policy_consumes_frozen_source_after_canonical_report_refresh(tmp_path):
    report = {
        "schema": "machine_entry_timing_tuning_report_v3",
        "target_date": "2026-09-08",
        "effective_date": "2026-09-09",
        "clean_tuning_baseline_date": "2026-06-05",
        "target_source_ready": True,
        "decision": "baseline_immediate_entry_carry_forward",
        "runtime_winner": None,
        "winner": None,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "sample_floor_assessment": {},
        "per_signal_dynamic_confirmation_source_only": {},
    }
    report_dir = tmp_path / "report"
    policy_dir = tmp_path / "policy"
    canonical = report_dir / "machine_entry_timing_tuning_2026-09-08.json"
    applied = build_applied_policy(report, source_report_path=canonical)
    _, _, policy_path = write_outputs(
        report, applied, output_dir=report_dir, policy_dir=policy_dir
    )

    def load():
        return load_applied_policy(
            target_date=date(2026, 9, 9),
            policy_dir=policy_dir,
            source_report_dir=report_dir,
        )

    assert load()[1] == "ready"
    changed = {**report, "diagnostic_refresh": True}
    write_outputs(
        changed,
        build_applied_policy(changed, source_report_path=canonical),
        output_dir=report_dir,
        policy_dir=policy_dir,
        publish_policy=False,
    )
    assert load()[1] == "ready"
    frozen = json.loads(policy_path.read_text())["source_evidence_snapshot"]
    canonical.write_text(
        json.dumps({**changed, "same_stage_owner_guard": {"mutation_present": True}})
    )
    assert load()[1] == "entry_timing_current_same_stage_owner_veto"
    canonical.write_text(json.dumps(changed))
    from pathlib import Path

    Path(frozen).write_text(json.dumps(changed))
    assert load()[0] is None


def test_empty_or_duplicate_study_cannot_manufacture_economics():
    day = date(2026, 8, 27)
    row = _immediate(day)
    for rows in ([], [(day, row), (day, deepcopy(row))]):
        result = build_study(
            cohort_rows=rows, economic_observer=_study_economic_observer
        )
        assert result["common_paired_count"] == 0
        assert result["arms"]["combined"]["all"]["net_ev_pct"] is None


def test_census_separates_observed_unfilled_held_and_unknown():
    day = date(2026, 8, 27)
    rows = []
    for index, outcome in enumerate(
        (
            {
                "realized": False,
                "purchased_quantity": 0,
                "entry_fill_status": "unfilled",
            },
            {
                "realized": False,
                "purchased_quantity": 10,
                "right_censored_residual_quantity": 10,
            },
            {
                "realized": False,
                "purchased_quantity": 5,
                "right_censored_residual_quantity": 5,
            },
            {"realized": False, "quantity": 10},
            {},
        )
    ):
        row = _immediate(day, index)
        row["owner_outcome"] = outcome
        rows.append((day, row))
    result = build_study(cohort_rows=rows, economic_observer=_study_economic_observer)
    assert result["common_paired_count"] == 0
    assert result["outcome_census"] == {
        "submitted_unfilled": 1,
        "held_full_entry_fill": 1,
        "held_partial_fill_or_partial_exit": 1,
        "filled_terminal_unknown": 1,
        "submitted_fill_and_terminal_unknown": 1,
    }


def test_completed_count_alone_does_not_claim_all_sample_floors_met():
    from src.engine.automation.machine_entry_timing_tuning import (
        _cohort_sample_floor_assessment,
    )

    day = date(2026, 8, 27)
    rows = [(day, _immediate(day, i)) for i in range(8)]
    result = _cohort_sample_floor_assessment(
        cohort_key=("episode", "test", "005930", "KRX_REGULAR", "ENTRY_READY"),
        cohort_rows=rows,
        alternatives=[],
        source_report_dates={day},
        dynamic_evaluation={
            "completed_outcome_count": 8,
            "unique_decision_lifecycles": 8,
            "observed_trading_days": 1,
        },
    )
    assert result["state"] == "natural_sample_wait"
    assert result["remaining_completed_outcome_count"] == 0
    assert result["projected_additional_trading_days_at_observed_yield"] == 4
