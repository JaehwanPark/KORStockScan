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
    assert candidate["review_ready_for_prompt_candidate"] is True
    assert report["runtime_effect"] is False
    assert report["selected_review_candidate"] == "candidate_v1"
    assert report["legacy_watching_score_smoothing"] == {
        "status": "retired_from_runtime_authority",
        "replacement": "exact_decision_trace_cumulative_action_outcome_v1",
        "numeric_score_ema_used_for_live_decision": False,
        "projection_submitter_removed": True,
        "projection_refresh_removed": True,
        "runtime_env_family_removed": True,
        "runtime_config_surface_removed": True,
        "default_postclose_generation_removed": True,
        "legacy_artifact_role": "explicit_archive_audit_only",
    }


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
    assert ledger["learning_update_floor"]["pass"] is True
    assert ledger["source_quality_adjusted_ev_delta_pct"] == 0.8
    assert ledger["raw_to_final_transition_counts"] == {"EXIT->HOLD": 1}
    assert report["ofi_smoothing_audit"]["status"] == "pass"


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
