from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.automation import machine_microstructure_policy_approval as approval
from src.engine.monitoring.machine_lifecycle_turnover_policy_research import (
    AUTHORITY,
    _counterfactual_leg,
    build_rolling_paired_policy_research,
)
from src.engine.monitoring.machine_microstructure_attribution import (
    _anchor_result,
    _fast_lifecycle_objective_followup,
)
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")


def _trading_dates(through: date, count: int) -> list[date]:
    result: list[date] = []
    candidate = through
    while len(result) < count:
        if is_krx_trading_day(candidate):
            result.append(candidate)
        candidate -= timedelta(days=1)
    return sorted(result)


def _anchor(
    *,
    source_date: str,
    lifecycle_number: int,
    current_realized: bool = True,
    scope_id: str = "005930:KRX_REGULAR",
) -> dict:
    lifecycle_id = f"widget:{scope_id}:{source_date}:{lifecycle_number}"
    return {
        "anchor_id": f"{lifecycle_id}:entry",
        "lifecycle_id": lifecycle_id,
        "owner": "widget",
        "scope_id": scope_id,
        "symbol": "005930",
        "session": "KRX_REGULAR",
        "lifecycle_stage": "entry",
        "anchor_role": "counterfactual_calibration_entry",
        "anchor_price": 10_000.0,
        "owner_round_trip_cost_pct": 0.2,
        "owner_round_trip_cost_provenance": (
            "widget_auto_trade_policy_calibration.round_trip_cost_pct"
        ),
        "owner_lifecycle_contract_valid": True,
        "micro_context_status": "matched",
        "micro_tuning_input_allowed": True,
        "metrics": {
            "reference_price": 10_000.0,
            "eligible_window_row_count": 100,
            "bbo_complete_row_count": 100,
            "depth_context_covered_row_count": 95,
            "fillable_owner_target_touch": {
                "touched": False,
                "time_ms": None,
                "gross_return_bps": None,
            },
            "fillable_bid_exit_horizons": {
                "60": {
                    "observed": True,
                    "bid_price": 10_040.0,
                    "gross_return_bps": 40.0,
                    "observation_offset_ms": 60_000,
                    "quote_age_from_horizon_ms": 0,
                    "required_exit_quantity": 1,
                    "available_best_bid_quantity": 100,
                    "depth_backed": True,
                },
                "120": {
                    "observed": True,
                    "bid_price": 10_030.0,
                    "gross_return_bps": 30.0,
                    "observation_offset_ms": 120_000,
                    "quote_age_from_horizon_ms": 0,
                    "required_exit_quantity": 1,
                    "available_best_bid_quantity": 100,
                    "depth_backed": True,
                },
                "180": {
                    "observed": True,
                    "bid_price": 10_025.0,
                    "gross_return_bps": 25.0,
                    "observation_offset_ms": 180_000,
                    "quote_age_from_horizon_ms": 0,
                    "required_exit_quantity": 1,
                    "available_best_bid_quantity": 100,
                    "depth_backed": True,
                },
            },
        },
        "owner_outcome": {
            "realized": current_realized,
            "cost_aware_net_return_pct": 0.05 if current_realized else None,
            "holding_duration_ms": 300_000 if current_realized else None,
            "entry_notional_krw": 10_000.0,
        },
    }


def _report(source_date: str, anchors: list[dict]) -> dict:
    return {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": source_date,
        "clean_baseline_allowed": True,
        "authority": dict(AUTHORITY),
        "rolling_policy_source_contract": {"ready": True, "gap": None},
        "consumers": {
            "widget_postclose_tuning": {
                "symbols": {
                    "005930": {
                        "anchor_results": anchors,
                    }
                }
            },
            "episode_machine_postclose_tuning": {"profiles": {}},
        },
    }


def test_counterfactual_accepts_effective_dated_widget_cost_contract() -> None:
    anchor = _anchor(source_date="2026-08-27", lifecycle_number=1)
    anchor["owner_round_trip_cost_pct"] = 0.23
    anchor["owner_round_trip_cost_provenance"] = (
        "widget_comparison_cost.effective_dated_contract"
    )

    leg = _counterfactual_leg(anchor, timeout_sec=60)

    assert leg["eligible"] is True
    assert leg["candidate_net_return_pct"] == 0.17
    assert leg["round_trip_cost_provenance"] == (
        "widget_comparison_cost.effective_dated_contract"
    )


def test_rolling_research_emits_one_source_only_design_required_candidate(
    tmp_path: Path,
):
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13"]
    for source_date in dates:
        payload = _report(
            source_date,
            [
                _anchor(source_date=source_date, lifecycle_number=index)
                for index in range(4)
            ],
        )
        (
            tmp_path / f"machine_microstructure_attribution_{source_date}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current = _report(
        "2026-08-14",
        [
            _anchor(source_date="2026-08-14", lifecycle_number=index)
            for index in range(4)
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14",
        current_report=current,
        report_dir=tmp_path,
    )

    assert research["status"] == "candidate_ready"
    assert research["summary"] == {
        "valid_source_report_count": 5,
        "cohort_count": 1,
        "candidate_ready_cohort_count": 1,
        "policy_promotion_candidate_count": 1,
    }
    candidate = research["policy_promotion_candidates"][0]
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True
    assert candidate["runtime_design"]["mapping_status"] == "design_required"
    assert candidate["runtime_design"]["bounded_values"]["recommended"] == 60
    assert candidate["objective_followup_binding"]["resolved_gap_codes"] == []
    selected = research["cohorts"][0]["alternatives"][0]["windows"]["20d"]
    assert selected["current_complete_lifecycle_count"] == 20
    assert selected["candidate_complete_lifecycle_count"] == 20
    assert selected["current_net_profit_krw"] == 100.0
    assert selected["candidate_net_profit_krw"] == 400.0
    assert selected["paired_net_profit_uplift_krw"] == 300.0
    assert selected["current_capital_occupied_krw_seconds"] == 60_000_000.0
    assert selected["candidate_capital_occupied_krw_seconds"] == 12_000_000.0
    assert selected["current_median_reconciliation_confirmed_duration_sec"] == 300.0
    assert selected["candidate_median_timeout_duration_sec"] == 60.0
    assert selected["current_completed_within_180s_count"] == 0
    assert selected["candidate_completed_within_180s_count"] == 20
    assert approval.evidence_readiness_errors(candidate) == []
    assert "runtime_family_not_in_trusted_registry" in approval.runtime_design_errors(
        candidate
    )
    followup = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment={
            "reflected_in_real_runtime_policy": False,
            "implementation_boundary": research["implementation_boundary"],
            "remaining_gaps": [],
        },
        promotion_candidates=[candidate],
    )
    assert followup["state"] == "CANDIDATE_QUEUE_HANDOFF"
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, candidate_rejections = approval.sync_queue(
        approval._empty_queue(now=now),
        source_candidates=[candidate],
        source_path=tmp_path / "source.json",
        as_of_date=date(2026, 8, 14),
        source_status="loaded",
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    assert candidate_rejections == []
    assert queue["candidates"][0]["state"] == "DESIGN_REQUIRED"
    queue, followup_rejections = approval.sync_objective_followups(
        queue,
        source_followups=[followup],
        source_path=tmp_path / "source.json",
        as_of_date=date(2026, 8, 14),
        source_status="loaded",
        accepted_candidate_queue_keys=queue["last_sync"][
            "accepted_candidate_queue_keys"
        ],
        now=now,
    )
    assert followup_rejections == []
    assert queue["objective_followups"][0]["state"] == "CANDIDATE_QUEUE_HANDOFF"


def test_rolling_research_uses_window_length_paired_sample_floors(
    tmp_path: Path,
) -> None:
    target_day = date(2026, 8, 27)
    source_dates = _trading_dates(target_day, 20)
    for lifecycle_number, source_day in enumerate(source_dates[:-1], start=1):
        payload = _report(
            source_day.isoformat(),
            [
                _anchor(
                    source_date=source_day.isoformat(),
                    lifecycle_number=lifecycle_number,
                )
            ],
        )
        (
            tmp_path
            / f"machine_microstructure_attribution_{source_day.isoformat()}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current = _report(
        target_day.isoformat(),
        [
            _anchor(
                source_date=target_day.isoformat(),
                lifecycle_number=20,
            )
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date=target_day.isoformat(),
        current_report=current,
        report_dir=tmp_path,
    )

    assert research["status"] == "candidate_ready"
    alternative = research["cohorts"][0]["alternatives"][0]
    readiness = alternative["window_sample_readiness"]
    for window_name, floor in (("5d", 5), ("10d", 10), ("20d", 20)):
        window = readiness[window_name]
        assert window["required_paired_complete_lifecycle_count"] == floor
        assert window["observed_paired_complete_lifecycle_count"] == floor
        assert window["remaining_paired_complete_lifecycle_count"] == 0
        assert window["state"] == "floor_met"
        assert window["shortage_classification_status"] == ("not_applicable_floor_met")
        assert window["shortage_class"] is None
    assert not any(
        "5d_paired_lifecycle_count_below_20" in gap
        for gap in research["remaining_gap_codes"]
    )


def test_rolling_research_classifies_unresolved_window_before_waiting(
    tmp_path: Path,
) -> None:
    current = _report(
        "2026-08-27",
        [
            _anchor(
                source_date="2026-08-27",
                lifecycle_number=1,
                current_realized=False,
            )
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-27",
        current_report=current,
        report_dir=tmp_path,
    )

    readiness = research["cohorts"][0]["alternatives"][0]["window_sample_readiness"]
    assert readiness["5d"]["state"] == "terminal_or_right_censored_gap"
    assert readiness["5d"]["shortage_classification_status"] == (
        "blocked_missing_evidence"
    )
    assert readiness["20d"]["remaining_paired_complete_lifecycle_count"] == 20
    assert research["sample_floor_assessment"]["state"] == (
        "terminal_or_right_censored_gap"
    )
    assert research["sample_floor_assessment"]["shortage_classification_status"] == (
        "blocked_missing_evidence"
    )
    assert research["sample_floor_assessment"]["next_action"] == (
        "reconcile_exact_owner_terminal_outcomes_before_waiting"
    )


def test_rolling_research_detects_window_floor_unattainable_at_observed_yield(
    tmp_path: Path,
) -> None:
    target_day = date(2026, 8, 27)
    source_dates = _trading_dates(target_day, 5)
    for source_day in source_dates[:-1]:
        payload = _report(source_day.isoformat(), [])
        (
            tmp_path
            / f"machine_microstructure_attribution_{source_day.isoformat()}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current = _report(
        target_day.isoformat(),
        [
            _anchor(
                source_date=target_day.isoformat(),
                lifecycle_number=1,
            )
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date=target_day.isoformat(),
        current_report=current,
        report_dir=tmp_path,
    )

    window = research["cohorts"][0]["alternatives"][0]["window_sample_readiness"]["5d"]
    assert window["state"] == "window_floor_unattainable_at_observed_yield"
    assert window["source_report_day_count"] == 5
    assert window["projected_paired_lifecycles_in_full_window"] == 1.0
    assert window["shortage_class"] == "structural_population_exhaustion"
    assert research["sample_floor_assessment"]["state"] == (
        "window_floor_unattainable_at_observed_yield"
    )
    assert research["sample_floor_assessment"]["shortage_class"] == (
        "structural_population_exhaustion"
    )
    assert (
        "5d_window_floor_unattainable_at_observed_yield"
        in research["remaining_gap_codes"]
    )


def test_rolling_research_defers_shortage_class_until_declared_window_closes(
    tmp_path: Path,
) -> None:
    target_day = date(2026, 8, 28)
    source_dates = _trading_dates(target_day, 4)
    for source_day in source_dates[:-1]:
        payload = _report(source_day.isoformat(), [])
        (
            tmp_path
            / f"machine_microstructure_attribution_{source_day.isoformat()}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current = _report(
        target_day.isoformat(),
        [
            _anchor(
                source_date=target_day.isoformat(),
                lifecycle_number=1,
            )
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date=target_day.isoformat(),
        current_report=current,
        report_dir=tmp_path,
    )

    readiness = research["cohorts"][0]["alternatives"][0][
        "window_sample_readiness"
    ]
    window = readiness["5d"]
    assert window["state"] == "pending_declared_window"
    assert window["shortage_classification_status"] == "pending_declared_window"
    assert window["shortage_class"] is None
    assert window["classification_window_complete"] is False
    assert window["minimum_completed_due_trading_days"] == 5
    assert window["remaining_completed_due_trading_days_to_classification"] == 1
    assert window["earliest_review_date"] == "2026-08-31"
    assert window["projected_additional_trading_days_at_observed_yield"] is None
    assert research["sample_floor_assessment"]["state"] == (
        "pending_declared_window"
    )
    assert research["sample_floor_assessment"]["shortage_classification_status"] == (
        "pending_declared_window"
    )
    assert research["sample_floor_assessment"]["shortage_class"] is None
    assert research["sample_floor_assessment"]["next_action"] == (
        "recheck_at_earliest_declared_window"
    )
    assert "5d_classification_window_pending" in research["remaining_gap_codes"]


def test_rolling_research_blocks_when_source_report_contract_is_excluded(
    tmp_path: Path,
) -> None:
    excluded_day = date(2026, 8, 27)
    excluded = _report(excluded_day.isoformat(), [])
    excluded["rolling_policy_source_contract"] = {
        "ready": False,
        "gap": "producer_contract_missing",
    }
    (
        tmp_path
        / f"machine_microstructure_attribution_{excluded_day.isoformat()}.json"
    ).write_text(__import__("json").dumps(excluded), encoding="utf-8")
    current = _report(
        "2026-08-28",
        [_anchor(source_date="2026-08-28", lifecycle_number=1)],
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-28",
        current_report=current,
        report_dir=tmp_path,
    )

    window = research["cohorts"][0]["alternatives"][0][
        "window_sample_readiness"
    ]["5d"]
    assert window["state"] == "source_report_contract_gap"
    assert window["source_report_contract_gap_day_count"] == 1
    assert window["shortage_classification_status"] == "blocked_missing_evidence"
    assert window["shortage_class"] is None
    assert window["earliest_review_date"] is None
    assert window["projected_paired_lifecycles_in_full_window"] is None
    assert window["projected_additional_trading_days_at_observed_yield"] is None
    assessment = research["sample_floor_assessment"]
    assert assessment["state"] == "source_report_contract_gap"
    assert assessment["shortage_classification_status"] == (
        "blocked_missing_evidence"
    )
    assert assessment["shortage_class"] is None
    assert assessment["next_action"] == (
        "repair_excluded_source_report_contracts_and_rerun"
    )
    assert "5d_source_report_contract_gap" in research["remaining_gap_codes"]

    followup = _fast_lifecycle_objective_followup(
        target_date="2026-08-28",
        objective_alignment={
            "implementation_boundary": research["implementation_boundary"],
            "reflected_in_real_runtime_policy": False,
            "sample_floor_assessment": assessment,
            "remaining_gaps": research["remaining_gap_codes"],
        },
        promotion_candidates=[],
    )
    assert followup["attention_class"] == "source_quality"
    assert followup["current_capability"] == (
        "rolling_paired_research_report_contract_blocked"
    )
    assert followup["next_action"] == (
        "repair_excluded_source_report_contracts_and_rerun"
    )


def test_rolling_research_keeps_insufficient_and_unresolved_samples_open(
    tmp_path: Path,
):
    current = _report(
        "2026-08-14",
        [
            _anchor(
                source_date="2026-08-14",
                lifecycle_number=1,
                current_realized=False,
            )
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14",
        current_report=current,
        report_dir=tmp_path,
    )

    assert research["status"] == "evidence_accumulating"
    assert research["policy_promotion_candidates"] == []
    assert "observed_trading_days_below_5" in research["remaining_gap_codes"]
    row = research["cohorts"][0]
    window = row["alternatives"][0]["windows"]["20d"]
    assert window["paired_complete_lifecycle_count"] == 0
    assert window["current_source_quality_adjusted_ev_pct"] is None
    assert window["candidate_source_quality_adjusted_ev_pct"] == 0.2
    assert window["current_net_profit_krw"] is None
    assert window["candidate_net_profit_krw"] == 20.0
    assert window["paired_net_profit_uplift_krw"] is None
    assert window["current_capital_occupied_krw_seconds"] is None
    assert window["candidate_capital_occupied_krw_seconds"] == 600_000.0
    assert window["current_held_or_unresolved_count"] == 1
    assert window["candidate_held_or_unresolved_count"] == 0


def test_episode_held_inventory_is_diagnostic_but_never_ev_authority(tmp_path: Path):
    decision = _anchor(source_date="2026-08-14", lifecycle_number=1)
    lifecycle_id = "episode:samsung_midday:2026-08-14T12:00:00+09:00"
    decision.update(
        {
            "anchor_id": f"{lifecycle_id}:signal",
            "lifecycle_id": lifecycle_id,
            "owner": "episode",
            "scope_id": "samsung_midday",
            "anchor_role": "episode_signal_bar",
            "owner_policy_tuning_eligible": False,
            "owner_source_quality": "gap",
            "actual_order_submitted": True,
            "micro_tuning_input_allowed": False,
            "owner_outcome": None,
        }
    )
    fill = dict(decision)
    fill.update(
        {
            "anchor_id": f"{lifecycle_id}:leg_1:buy_fill",
            "anchor_role": "episode_buy_fill_confirmed",
            "anchor_price": 10_000.0,
            "owner_outcome": {
                "leg_id": "leg_1",
                "realized": False,
                "cost_aware_net_return_pct": None,
                "holding_duration_ms": None,
                "entry_notional_krw": 100_000.0,
            },
        }
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14",
        current_report=_report("2026-08-14", [decision, fill]),
        report_dir=tmp_path,
    )

    row = research["cohorts"][0]
    window = row["alternatives"][0]["windows"]["20d"]
    assert row["policy_eligible_unique_lifecycle_count"] == 0
    assert row["diagnostic_unique_lifecycle_count"] == 1
    assert row["held_diagnostic_only_lifecycle_count"] == 1
    assert window["lifecycle_count"] == 0
    assert window["diagnostic_lifecycle_count"] == 1
    assert window["held_diagnostic_only_lifecycle_count"] == 1
    assert window["current_source_quality_adjusted_ev_pct"] is None
    assert window["candidate_source_quality_adjusted_ev_pct"] is None
    assert window["current_held_or_unresolved_count"] == 1
    assert window["candidate_held_or_unresolved_count"] == 0
    assert window["candidate_completed_within_180s_count"] == 1
    assert research["policy_promotion_candidates"] == []


def test_multi_day_held_reconciliation_joins_original_lifecycle(tmp_path: Path):
    source_date = "2026-08-13"
    lifecycle_id = "episode:samsung_midday:2026-08-13T12:00:00+09:00"
    decision = _anchor(source_date=source_date, lifecycle_number=1)
    decision.update(
        {
            "anchor_id": f"{lifecycle_id}:signal",
            "lifecycle_id": lifecycle_id,
            "owner": "episode",
            "scope_id": "samsung_midday",
            "anchor_role": "episode_signal_bar",
            "owner_policy_tuning_eligible": False,
            "owner_source_quality": "gap",
            "actual_order_submitted": True,
            "micro_tuning_input_allowed": False,
            "owner_outcome": None,
        }
    )
    fill = dict(decision)
    fill.update(
        {
            "anchor_id": f"{lifecycle_id}:leg_1:buy_fill",
            "anchor_role": "episode_buy_fill_confirmed",
            "owner_outcome": {
                "leg_id": "leg_1",
                "realized": False,
                "cost_aware_net_return_pct": None,
                "holding_duration_ms": None,
                "entry_notional_krw": 100_000.0,
            },
        }
    )
    prior_report = _report(source_date, [decision, fill])
    (tmp_path / f"machine_microstructure_attribution_{source_date}.json").write_text(
        __import__("json").dumps(prior_report), encoding="utf-8"
    )
    reconciled_exit = dict(fill)
    reconciled_exit.update(
        {
            "anchor_id": f"{lifecycle_id}:leg_1:reconciled_target_fill",
            "lifecycle_stage": "exit",
            "anchor_role": "episode_target_fill_reconciled",
            "owner_policy_tuning_eligible": True,
            "owner_source_quality": "pass",
            "micro_tuning_input_allowed": True,
            "owner_outcome": {
                "leg_id": "leg_1",
                "realized": True,
                "cost_aware_net_return_pct": 0.05,
                "holding_duration_ms": 300_000,
                "entry_notional_krw": 100_000.0,
            },
        }
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14",
        current_report=_report("2026-08-14", [reconciled_exit]),
        report_dir=tmp_path,
    )

    row = research["cohorts"][0]
    window = row["alternatives"][0]["windows"]["20d"]
    assert row["policy_eligible_unique_lifecycle_count"] == 1
    assert row["held_diagnostic_only_lifecycle_count"] == 0
    assert window["paired_complete_lifecycle_count"] == 1
    assert window["current_source_quality_adjusted_ev_pct"] == 0.05
    assert window["candidate_source_quality_adjusted_ev_pct"] == 0.2
    assert window["current_held_or_unresolved_count"] == 0


def test_rolling_research_selects_only_one_ready_cohort_for_intake(tmp_path: Path):
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13"]
    for source_date in dates:
        anchors = [
            _anchor(source_date=source_date, lifecycle_number=index)
            for index in range(4)
        ] + [
            _anchor(
                source_date=source_date,
                lifecycle_number=index,
                scope_id="005930:NXT_REGULAR_OVERLAP",
            )
            for index in range(4)
        ]
        payload = _report(source_date, anchors)
        (
            tmp_path / f"machine_microstructure_attribution_{source_date}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current = _report(
        "2026-08-14",
        [
            _anchor(source_date="2026-08-14", lifecycle_number=index)
            for index in range(4)
        ]
        + [
            _anchor(
                source_date="2026-08-14",
                lifecycle_number=index,
                scope_id="005930:NXT_REGULAR_OVERLAP",
            )
            for index in range(4)
        ],
    )

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14", current_report=current, report_dir=tmp_path
    )

    assert research["summary"]["candidate_ready_cohort_count"] == 2
    assert research["summary"]["policy_promotion_candidate_count"] == 1
    assert sum(row["selected_for_intake"] for row in research["cohorts"]) == 1


def test_invalid_contract_decision_anchor_blocks_otherwise_ready_cohort(
    tmp_path: Path,
):
    dates = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13"]
    for source_date in dates:
        payload = _report(
            source_date,
            [
                _anchor(source_date=source_date, lifecycle_number=index)
                for index in range(4)
            ],
        )
        (
            tmp_path / f"machine_microstructure_attribution_{source_date}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current_anchors = [
        _anchor(source_date="2026-08-14", lifecycle_number=index) for index in range(4)
    ]
    invalid = _anchor(source_date="2026-08-14", lifecycle_number=99)
    invalid["micro_context_status"] = "micro_scope_source_contract_invalid"
    invalid["micro_tuning_input_allowed"] = False
    current_anchors.append(invalid)

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14",
        current_report=_report("2026-08-14", current_anchors),
        report_dir=tmp_path,
    )

    assert research["policy_promotion_candidates"] == []
    assert research["cohorts"][0]["invalid_contract_row_count"] == 1
    assert "invalid_contract_rows_present" in research["remaining_gap_codes"]


def test_unready_current_source_contract_blocks_ready_historical_candidate(
    tmp_path: Path,
):
    for source_date in (
        "2026-08-07",
        "2026-08-10",
        "2026-08-11",
        "2026-08-12",
        "2026-08-13",
    ):
        payload = _report(
            source_date,
            [
                _anchor(source_date=source_date, lifecycle_number=index)
                for index in range(4)
            ],
        )
        (
            tmp_path / f"machine_microstructure_attribution_{source_date}.json"
        ).write_text(__import__("json").dumps(payload), encoding="utf-8")
    current = _report("2026-08-14", [])
    current["rolling_policy_source_contract"] = {
        "ready": False,
        "gap": "micro_canary_target_date_evidence_stale",
        "recovery": {
            "disposition": "repairable_source_contract_gap",
            "rerun_same_source_date_allowed": True,
        },
    }

    research = build_rolling_paired_policy_research(
        target_date="2026-08-14", current_report=current, report_dir=tmp_path
    )

    assert research["status"] == "source_quality_blocked"
    assert research["current_source_contract"]["ready"] is False
    assert research["current_source_contract"]["errors"] == [
        "rolling_policy_source_contract_not_ready"
    ]
    assert research["current_source_contract"]["recovery"] == {
        "disposition": "repairable_source_contract_gap",
        "rerun_same_source_date_allowed": True,
    }
    assert research["policy_promotion_candidates"] == []
    assert research["remaining_gap_codes"] == [
        "current_attribution_source_contract_invalid"
    ]
    followup = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment={
            "reflected_in_real_runtime_policy": False,
            "implementation_boundary": research["implementation_boundary"],
            "remaining_gaps": research["remaining_gap_codes"],
        },
        promotion_candidates=[],
    )
    assert followup["state"] == "EVIDENCE_ACCUMULATING"
    assert followup["attention_class"] == "source_quality"
    assert followup["next_action"] == (
        "repair_current_attribution_source_contract_and_rerun"
    )


def test_anchor_result_records_past_only_fillable_bid_timeout_snapshots():
    anchor_at = datetime(2026, 8, 14, 10, 0, tzinfo=KST)
    anchor = {
        "anchor_id": "widget:005930:entry",
        "lifecycle_id": "widget:005930",
        "owner": "widget",
        "scope_id": "005930:KRX_REGULAR",
        "symbol": "005930",
        "session": "KRX_REGULAR",
        "expected_venues": ["KRX"],
        "expected_session_buckets": ["KRX_REGULAR"],
        "anchor_at": anchor_at.isoformat(),
        "anchor_price": 10_000.0,
        "owner_target_price": 10_050.0,
        "owner_outcome": {
            "quantity_basis": "one_share_normalized",
            "entry_notional_krw": 10_000.0,
        },
        "lifecycle_stage": "entry",
        "anchor_role": "counterfactual_calibration_entry",
        "owner_lifecycle_contract_valid": True,
    }
    rows = [
        {
            "timestamp": anchor_at + timedelta(seconds=59),
            "price": 10_030.0,
            "best_bid": 10_040.0,
            "best_ask": 10_050.0,
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "sequence_epoch": 1,
        },
        {
            "timestamp": anchor_at + timedelta(seconds=61),
            "price": 10_060.0,
            "best_bid": 10_050.0,
            "best_ask": 10_060.0,
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "sequence_epoch": 1,
        },
    ]
    result = _anchor_result(
        anchor,
        {
            "observed_row_count": 2,
            "invalid_contract_scope_counts": {},
        },
        {
            "rows": rows,
            "depth_rows": 2,
            "depth_points": [
                {
                    "sequence_epoch": 1,
                    "timestamp": anchor_at + timedelta(seconds=59),
                    "best_bid": 10_040.0,
                    "best_bid_qty": 10,
                    "bid_depth": 100,
                },
                {
                    "sequence_epoch": 1,
                    "timestamp": anchor_at + timedelta(seconds=61),
                    "best_bid": 10_050.0,
                    "best_bid_qty": 10,
                    "bid_depth": 100,
                },
            ],
            "shock_reference_count": 0,
        },
        partition_loaded=True,
        source_contract_gap=None,
        clean_baseline_allowed=True,
    )

    horizon = result["metrics"]["fillable_bid_exit_horizons"]["60"]
    assert horizon["observed"] is True
    assert horizon["bid_price"] == 10_040.0
    assert horizon["observation_offset_ms"] == 59_000
    assert horizon["depth_backed"] is True
    assert horizon["available_best_bid_quantity"] == 10
    assert result["metrics"]["fillable_owner_target_touch"]["time_ms"] == 61_000


def test_counterfactual_rejects_self_declared_inconsistent_timeout_quote():
    anchor = _anchor(source_date="2026-08-14", lifecycle_number=1)
    anchor["metrics"]["fillable_bid_exit_horizons"]["60"]["bid_price"] = 9_000.0

    result = _counterfactual_leg(anchor, timeout_sec=60)

    assert result == {"eligible": False, "reason": "fillable_timeout_bid_missing"}


def test_counterfactual_rejects_best_bid_quantity_below_required_exit_quantity():
    anchor = _anchor(source_date="2026-08-14", lifecycle_number=1)
    horizon = anchor["metrics"]["fillable_bid_exit_horizons"]["60"]
    horizon["required_exit_quantity"] = 20
    horizon["available_best_bid_quantity"] = 10

    result = _counterfactual_leg(anchor, timeout_sec=60)

    assert result == {"eligible": False, "reason": "fillable_timeout_bid_missing"}
