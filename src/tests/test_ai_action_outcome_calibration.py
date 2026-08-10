from __future__ import annotations

import json
from pathlib import Path

from src.engine.scalping.ai_action_outcome_calibration import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_pipeline(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_cumulative_calibration_updates_from_one_exact_trace(tmp_path: Path) -> None:
    report_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-29_candidate_v1.json"
    )
    _write_json(
        report_path,
        {
            "target_date": "2026-07-29",
            "runtime_effect": False,
            "schema_rejected_count": 0,
            "provider_failed_count": 0,
            "candidate_provider_none_count": 0,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "BUY",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 1.2,
                    "delta_pct": 1.2,
                    "first_hit": "target",
                    "outcome_return_pct": 1.2,
                    "outcome_mfe_pct": 1.5,
                    "outcome_mae_pct": -0.1,
                    "candidate_error_taxonomy": [],
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 1
    assert candidate["learning_update_floor"]["pass"] is True
    assert candidate["source_quality_adjusted_ev_delta_pct"] == 1.2
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert "exact_trace_floor" in candidate["prompt_review_gate"]["blockers"]
    assert (
        "independent_source_date_floor" in candidate["prompt_review_gate"]["blockers"]
    )
    assert report["runtime_effect"] is False
    assert report["selected_review_candidate"] is None


def test_prompt_review_candidate_requires_multi_day_bounded_exploration(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for source_date, start in (("2026-07-28", 0), ("2026-07-29", 20)):
        rows = []
        for index in range(start, start + 20):
            is_exposure = index < 5
            rows.append(
                {
                    "decision_trace_id": f"trace-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": (
                        0.4 if is_exposure else 0.01
                    ),
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_probe_worst_loss_pct": -0.2,
                    "delta_pct": 0.4 if is_exposure else 0.01,
                    "first_hit": "target",
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_{source_date}_candidate_v2.json",
            {
                "target_date": source_date,
                "runtime_effect": False,
                "schema_rejected_count": 0,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "requests": [{"candidate": {"prompt_version": "candidate_v2"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["source_date_count"] == 2
    assert candidate["candidate_exposure_count"] == 5
    assert candidate["candidate_exposure_ev_pct"] == 0.4
    assert candidate["prompt_review_gate"]["blockers"] == []
    assert candidate["review_ready_for_prompt_candidate"] is True
    assert report["selected_review_candidate"] == "candidate_v2"


def test_bounded_recovery_exposure_is_not_blocked_by_raw_adverse_first_count(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-08-02", "2026-08-03")):
        rows = []
        for offset in range(20):
            index = day_index * 20 + offset
            is_exposure = index < 5
            is_recovery = index == 0
            rows.append(
                {
                    "decision_trace_id": f"bounded-recovery-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": (
                        0.5 if is_exposure else 0.01
                    ),
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "delta_pct": 0.5 if is_exposure else 0.01,
                    "first_hit": "adverse" if is_recovery else "target",
                    "profit_opportunity_sequence": (
                        "drawdown_then_profit_recovery"
                        if is_recovery
                        else "profit_before_drawdown"
                    ),
                    "candidate_probe_worst_loss_pct": (-1.5 if is_recovery else -0.2),
                    "probe_worst_loss_pct": -1.5 if is_recovery else -0.2,
                    "control_probe_severe_tail_exposure": False,
                    "candidate_probe_severe_tail_exposure": False,
                    "control_drawdown_recovery_captured": False,
                    "candidate_drawdown_recovery_captured": is_recovery,
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_{source_date}_candidate_bounded.json",
            {
                "target_date": source_date,
                "runtime_effect": False,
                "schema_rejected_count": 0,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "requests": [{"candidate": {"prompt_version": "candidate_bounded"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-08-03", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["adverse_first_exposure_not_increased"] is False
    assert candidate["adverse_first_role"] == ("diagnostic_not_absolute_quality_veto")
    assert candidate["candidate_probe_loss_budget_breach_count"] == 0
    assert candidate["candidate_drawdown_recovery_capture_count"] == 1
    assert (
        candidate["prompt_review_gate"]["checks"]["probe_loss_budget_within_cap"]
        is True
    )
    assert (
        candidate["prompt_review_gate"]["checks"]["severe_tail_adverse_not_increased"]
        is True
    )
    assert (
        candidate["prompt_review_gate"]["checks"][
            "drawdown_recovery_capture_not_decreased"
        ]
        is True
    )
    assert (
        "adverse_first_not_increased" not in candidate["prompt_review_gate"]["checks"]
    )
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_schema_reject_blocks_review_selection_but_keeps_learning(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-29_candidate_v1.json"
    )
    _write_json(
        report_path,
        {
            "target_date": "2026-07-29",
            "runtime_effect": False,
            "schema_rejected_count": 1,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "control_action": "WAIT",
                    "candidate_action": "BUY",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.5,
                    "delta_pct": 0.5,
                    "first_hit": "target",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["learning_update_floor"]["pass"] is True
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert report["selected_review_candidate"] is None


def test_isolated_schema_reject_does_not_block_bounded_prompt_review(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-07-28", "2026-07-29")):
        rows = []
        for offset in range(60):
            index = day_index * 60 + offset
            is_exposure = index < 6
            rows.append(
                {
                    "decision_trace_id": f"trace-{index}",
                    "stock_code": f"{index % 12:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": (
                        0.4 if is_exposure else 0.01
                    ),
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_probe_worst_loss_pct": -0.2,
                    "delta_pct": 0.4 if is_exposure else 0.01,
                    "first_hit": "target",
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_{source_date}_candidate_v3.json",
            {
                "target_date": source_date,
                "runtime_effect": False,
                "schema_rejected_count": 1 if day_index == 0 else 0,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "requests": [{"candidate": {"prompt_version": "candidate_v3"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["schema_rejected_count"] == 1
    assert candidate["schema_evaluated_count"] == 121
    assert candidate["schema_rejection_rate_pct"] < 1.0
    assert (
        candidate["prompt_review_gate"]["checks"]["schema_rejection_rate_ceiling"]
        is True
    )
    assert candidate["prompt_review_gate"]["blockers"] == []
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_model_comparison_artifact_is_excluded_from_prompt_cumulative_ledger(
    tmp_path: Path,
) -> None:
    report_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / (
            "ai_prompt_detailed_paired_replay_2026-07-29_candidate_v1_"
            "model_gpt-5-nano.json"
        )
    )
    _write_json(
        report_path,
        {
            "target_date": "2026-07-29",
            "runtime_effect": False,
            "model_comparison_contract": {
                "enabled": True,
                "baseline_model": "gpt-5.4-nano",
                "candidate_model": "gpt-5-nano",
                "decision_authority": "offline_model_comparison_only",
            },
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "control_action": "WAIT",
                    "candidate_action": "BUY",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 1.0,
                    "delta_pct": 1.0,
                    "first_hit": "target",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-29", data_root=tmp_path)

    assert report["candidate_count"] == 0
    assert report["source_reports"] == []
    assert report["selected_review_candidate"] is None


def test_ofi_action_adjustment_joins_exact_trace_outcome_from_first_row(
    tmp_path: Path,
) -> None:
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "holding-trace-1",
                    "control_action": "EXIT",
                    "candidate_action": "EXIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.0,
                    "delta_pct": 0.0,
                    "first_hit": "target",
                    "outcome_return_pct": 0.8,
                    "outcome_mfe_pct": 1.0,
                    "outcome_mae_pct": -0.2,
                }
            ],
        },
    )
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    fields = {
        "smoothing_action": "DEBOUNCE_EXIT",
        "raw_flow_action": "EXIT",
        "final_flow_action": "HOLD",
        "ai_decision_trace_id": "holding-trace-1",
        "ai_input_snapshot_id": "snapshot-1",
        "holding_flow_ofi_usable": True,
        "holding_flow_ofi_regime": "stable_bullish",
        "metric_role": "ai_action_postprocessor_outcome_calibration",
        "decision_authority": (
            "bounded_runtime_action_postprocessor_with_exact_trace_attribution"
        ),
    }
    _write_pipeline(
        pipeline_path,
        [
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "emitted_at": "2026-07-30T10:00:00+09:00",
                "fields": fields,
            }
        ],
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["mature_outcome_row_count"] == 1
    assert ledger["mature_effective_transition_outcome_row_count"] == 1
    assert ledger["effective_transition_row_count"] == 1
    assert ledger["no_change_control_row_count"] == 0
    assert ledger["learning_update_floor"]["pass"] is True
    assert ledger["source_quality_adjusted_ev_delta_pct"] == 0.8
    assert ledger["raw_to_final_transition_counts"] == {"EXIT->HOLD": 1}
    assert report["ofi_smoothing_audit"]["status"] == "pass"


def test_ofi_no_change_exact_outcome_is_control_not_learning_evidence(
    tmp_path: Path,
) -> None:
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "holding-control-1",
                    "control_action": "EXIT",
                    "candidate_action": "EXIT",
                    "outcome_return_pct": 0.8,
                    "outcome_mfe_pct": 1.0,
                    "outcome_mae_pct": -0.2,
                    "first_hit": "target",
                }
            ],
        },
    )
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    _write_pipeline(
        pipeline_path,
        [
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "fields": {
                    "smoothing_action": "NO_CHANGE",
                    "raw_flow_action": "EXIT",
                    "final_flow_action": "EXIT",
                    "ai_decision_trace_id": "holding-control-1",
                    "ai_input_snapshot_id": "snapshot-control-1",
                },
            }
        ],
    )

    ledger = build_report(target_date="2026-07-30", data_root=tmp_path)[
        "ofi_action_outcome_calibration"
    ]

    assert ledger["schema"] == "ofi_exact_trace_action_outcome_calibration_v2"
    assert ledger["status"] == "sample_floor_keep_collecting"
    assert ledger["mature_outcome_row_count"] == 1
    assert ledger["mature_effective_transition_outcome_row_count"] == 0
    assert ledger["effective_transition_row_count"] == 0
    assert ledger["no_change_control_row_count"] == 1
    assert ledger["no_change_control_outcome_status_counts"] == {"mature": 1}
    assert ledger["raw_to_final_transition_counts"] == {}
    assert ledger["source_quality_adjusted_ev_delta_pct"] is None
    assert ledger["learning_update_floor"]["pass"] is False


def test_ofi_unlinked_events_are_preserved_as_audit_exclusions(
    tmp_path: Path,
) -> None:
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    _write_pipeline(
        pipeline_path,
        [
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "fields": {
                    "smoothing_action": "NO_CHANGE",
                    "raw_flow_action": "EXIT",
                    "final_flow_action": "EXIT",
                },
            }
        ],
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["exact_trace_row_count"] == 0
    assert ledger["current_date_exclusion_counts"] == {
        "exact_decision_trace_missing": 1
    }
    assert (
        "exact_decision_trace_attribution_incomplete"
        in report["ofi_smoothing_audit"]["defects"]
    )


def test_prior_pending_ofi_row_is_rejoined_when_outcome_matures(
    tmp_path: Path,
) -> None:
    prior_report = (
        tmp_path
        / "report"
        / "ai_decision_action_outcome_calibration"
        / "ai_decision_action_outcome_calibration_2026-07-29.json"
    )
    _write_json(
        prior_report,
        {
            "target_date": "2026-07-29",
            "ofi_action_outcome_calibration": {
                "rows": [
                    {
                        "ledger_key": "holding_flow_ofi_smoothing_applied:trace-1",
                        "decision_trace_id": "trace-1",
                        "ai_input_snapshot_id": "snapshot-1",
                        "stage": "holding_flow_ofi_smoothing_applied",
                        "raw_action": "EXIT",
                        "final_action": "HOLD",
                        "outcome_status": "pending",
                    }
                ]
            },
        },
    )
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "control_action": "EXIT",
                    "candidate_action": "EXIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.0,
                    "delta_pct": 0.0,
                    "outcome_return_pct": 0.4,
                    "first_hit": "target",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["mature_outcome_row_count"] == 1
    assert ledger["source_quality_adjusted_ev_delta_pct"] == 0.4


def test_ofi_partial_action_without_quantity_is_mature_not_comparable(
    tmp_path: Path,
) -> None:
    pipeline_path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-30.jsonl"
    pipeline_path.parent.mkdir(parents=True)
    pipeline_path.write_text(
        json.dumps(
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "005930",
                "fields": {
                    "ai_decision_trace_id": "trace-trim",
                    "ai_input_snapshot_id": "snapshot-trim",
                    "raw_flow_action": "TRIM",
                    "final_flow_action": "EXIT",
                    "smoothing_action": "CONFIRM_EXIT",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-07-30_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-07-30",
            "runtime_effect": False,
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-trim",
                    "control_action": "TRIM",
                    "candidate_action": "EXIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.0,
                    "delta_pct": 0.0,
                    "outcome_return_pct": -0.8,
                    "first_hit": "adverse",
                }
            ],
        },
    )

    report = build_report(target_date="2026-07-30", data_root=tmp_path)

    ledger = report["ofi_action_outcome_calibration"]
    assert ledger["status"] == "mature_outcome_not_comparable_keep_collecting"
    assert ledger["mature_outcome_row_count"] == 0
    assert ledger["pending_outcome_row_count"] == 0
    assert ledger["mature_not_comparable_outcome_row_count"] == 1
    assert ledger["mature_not_comparable_reason_counts"] == {
        "action_value_requires_exact_quantity_or_cashflow_contract": 1
    }
