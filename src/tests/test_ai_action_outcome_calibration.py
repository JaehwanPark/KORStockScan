from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.engine.scalping import ai_action_outcome_calibration as calibration

build_report = calibration.build_report


def _economic_row(index: int, ev: float = 0.4) -> dict:
    return {
        "decision_trace_id": f"economic-{index}",
        "stock_code": f"{index % 10:06d}",
        "control_action": "WAIT",
        "candidate_action": "BUY",
        "control_decision_value_pct": 0.0,
        "candidate_primary_decision_value_pct": ev,
        "delta_pct": ev,
        "candidate_execution_cost_contract_applied": True,
        "candidate_execution_cost_pct": 0.2,
        "candidate_probe_worst_loss_pct": -0.2,
        "outcome_return_pct": ev,
    }


def test_small_profit_opportunity_is_handed_off_without_changing_live_gate(tmp_path):
    from src.engine.scalping.micro_reversion import (
        main_ai_prompt_optimizer as optimizer,
    )

    row = _economic_row(1)
    row.update(
        {
            "candidate_action": "DROP",
            "candidate_error_taxonomy": ["false_drop_small_profit_execution_proxy"],
            "entry_small_profit_opportunity": {
                "schema": "entry_small_profit_opportunity_v1",
                "positive_target_first_after_execution_proxy": True,
            },
        }
    )
    path = (
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-08_small.json"
    )
    _write_json(path, {"target_date": "2026-09-08", "paired_comparisons": [row]})
    summary = build_report(target_date="2026-09-08", data_root=tmp_path)[
        "candidate_summaries"
    ][0]
    assert summary["small_profit_opportunity_diagnostic"]["candidate_missed_count"] == 1
    assert summary["false_drop_count"] == 0
    taxonomy = optimizer._error_taxonomy(
        [
            {
                "error_taxonomy_counts": summary["candidate_error_taxonomy_counts"],
            }
        ]
    )
    assert (
        taxonomy["candidate_patch_objectives"]["small_profit_opportunity_diagnostic"]
        == 1
    )


def test_partial_batch_retains_exact_learning_without_live_promotion(tmp_path):
    pairs = [_economic_row(i) for i in range(39)]
    payload = _valid_detailed_payload(
        {
            "target_date": "2026-09-07",
            "request_count": 40,
            "provider_failed_count": 1,
            "promotion_report_integrity_pass": False,
            "promotion_quality_gate_pass": False,
            "paired_comparisons": pairs,
        }
    )
    payload["calibration_source_contract"] = {
        "schema": "ai_paired_calibration_source_v1",
        "global_integrity_pass": True,
        "request_count": 40,
        "retained_pair_count": 39,
        "excluded_request_count": 1,
        "retained_pairs_sha256": calibration._canonical_sha256(
            payload["paired_comparisons"]
        ),
        "decision_authority": "calibration_learning_only",
        "runtime_apply_authority": False,
    }
    path = (
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_partial.json"
    )
    _write_json(path, payload)
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 39
    assert (
        candidate["diagnostic_checks_not_review_veto"]["provider_transport_clean"]
        is False
    )
    assert report["runtime_effect"] is False
    payload["calibration_source_contract"]["global_integrity_pass"] = False
    _write_json(path, payload)
    blocked = build_report(target_date="2026-09-07", data_root=tmp_path)
    assert blocked["candidate_count"] == 0
    assert blocked["source_contract_summary"]["rejection_reason_counts"] == {
        "calibration_source_contract_invalid": 1
    }


def test_conflict_exclusion_does_not_poison_remaining_clean_cohort(tmp_path):
    folder = tmp_path / "report" / calibration.PAIRED_SUBDIR
    for day, offset in (("2026-09-04", 0), ("2026-09-07", 20)):
        _write_json(
            folder / f"ai_prompt_detailed_paired_replay_{day}_clean.json",
            {
                "target_date": day,
                "paired_comparisons": [
                    _economic_row(i) for i in range(offset, offset + 20)
                ],
            },
        )
    for suffix, ev in (("a", 0.4), ("b", -0.4)):
        _write_json(
            folder
            / f"ai_prompt_detailed_paired_replay_2026-09-07_conflict_{suffix}.json",
            {
                "target_date": "2026-09-07",
                "paired_comparisons": [_economic_row(100, ev)],
            },
        )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 40
    assert candidate["conflicting_duplicate_trace_count"] == 1
    assert candidate["prompt_review_gate"]["blockers"] == []
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_two_thin_candidates_pass_central_handoff_verification(tmp_path):
    from src.engine.verify_threshold_cycle_postclose_chain import (
        _ai_decision_action_outcome_calibration_status,
    )

    folder = tmp_path / "report" / calibration.PAIRED_SUBDIR
    for i, ev in enumerate((0.1, 0.5)):
        _write_json(
            folder / f"ai_prompt_detailed_paired_replay_2026-09-07_v{i}.json",
            {
                "target_date": "2026-09-07",
                "requests": [{"candidate": {"prompt_version": f"v{i}"}}],
                "paired_comparisons": [_economic_row(i, ev)],
            },
        )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    assert report["thin_positive_review_candidate_count"] == 2
    assert _ai_decision_action_outcome_calibration_status(report)["status"] == "pass"


def test_runtime_review_route_never_reactivates_legacy_family():
    registered = calibration.runtime_review_route(
        "decision_quality_v2_14_setup_risk_adjudicator", "entry", "KRX", "KRX_REGULAR"
    )
    assert registered["owner"] == "entry_setup_live_policy"
    assert registered["runtime_apply_authority"] is False
    assert registered["legacy_main_ai_quality_family_available"] is False
    assert (
        calibration.runtime_review_route(
            "decision_quality_v2_6", "entry", "KRX", "KRX_REGULAR"
        )["status"]
        == "source_only_no_registered_runtime_route"
    )


@pytest.mark.parametrize("field", ["delta_pct", "candidate_primary_decision_value_pct"])
@pytest.mark.parametrize("invalid", [None, True, "NaN"])
def test_incomplete_economic_values_cannot_be_thin_positive(tmp_path, field, invalid):
    row = _economic_row(1)
    row["candidate_decision_value_pct"] = 0.6
    row[field] = invalid
    _write_json(
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_invalid.json",
        {"target_date": "2026-09-07", "paired_comparisons": [row]},
    )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["review_classification"] == "learning_only_or_rejected"
    assert (
        "paired_economic_values_complete" in candidate["prompt_review_gate"]["blockers"]
    )


@pytest.mark.parametrize("invalid", [None, True, "NaN", -0.1])
def test_missing_or_invalid_cost_not_assumed_zero_for_review(tmp_path, invalid):
    row = _economic_row(1)
    row["candidate_execution_cost_pct"] = invalid
    _write_json(
        tmp_path
        / "report"
        / calibration.PAIRED_SUBDIR
        / "ai_prompt_detailed_paired_replay_2026-09-07_cost.json",
        {"target_date": "2026-09-07", "paired_comparisons": [row, _economic_row(2)]},
    )
    report = build_report(target_date="2026-09-07", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 1
    assert candidate["probe_cost_contract_complete"] is True
    assert report["source_contract_summary"]["row_exclusion_count"] == 1
    assert report["source_reports"][0]["row_exclusion_reason_counts"] == {
        "exposure_execution_cost_missing_or_invalid": 1
    }
    assert candidate["review_classification"] == "thin_positive_review"


def test_calibration_rejects_target_before_clean_baseline(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="target_date_before_clean_baseline"):
        build_report(target_date="2026-06-04", data_root=tmp_path)


def _write_json(path: Path, payload: dict) -> None:
    if path.name.startswith("ai_prompt_detailed_paired_replay_"):
        payload = _valid_detailed_payload(payload)
    elif path.name.startswith("ai_decision_action_outcome_calibration_"):
        payload = _valid_prior_calibration_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _valid_detailed_payload(payload: dict) -> dict:
    value = json.loads(json.dumps(payload))
    source_date = str(value.get("target_date") or "2026-07-29")
    requests = value.setdefault(
        "requests", [{"candidate": {"prompt_version": "candidate_v1"}}]
    )
    candidate = requests[0].setdefault("candidate", {})
    candidate_version = str(candidate.get("prompt_version") or "candidate_v1")
    candidate["prompt_version"] = candidate_version
    candidate.setdefault("system_prompt_sha256", "a" * 64)
    candidate.setdefault("contract_sha256", "b" * 64)
    contract_sha256 = candidate["contract_sha256"]
    rows = value.setdefault("paired_comparisons", [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        row.setdefault("stage", "entry")
        row.setdefault("effective_venue", "KRX")
        row.setdefault("session_bucket", "KRX_REGULAR")
        row.setdefault("decision_ts", f"{source_date}T10:00:00+09:00")
        row.setdefault(
            "outcome_return_pct", row.get("candidate_primary_decision_value_pct", 0.0)
        )
    value.setdefault("schema", calibration.DETAILED_PAIRED_SCHEMA)
    value.setdefault("runtime_effect", False)
    value.setdefault("allowed_runtime_apply", False)
    value.setdefault("actual_order_submitted", False)
    value.setdefault("broker_order_forbidden", True)
    value.setdefault("promotion_report_integrity_pass", True)
    value.setdefault("paired_comparable_count", len(rows))
    value.setdefault("schema_rejected_count", 0)
    value.setdefault("provider_failed_count", 0)
    value.setdefault("candidate_provider_none_count", 0)
    value.setdefault("candidate_contract_sha256", contract_sha256)
    value.setdefault(
        "promotion_cohort_scope",
        {
            "stages": ["entry"],
            "effective_venues": ["KRX"],
            "session_buckets": ["KRX_REGULAR"],
            "isolated": True,
            "candidate_contract_sha256": contract_sha256,
            "candidate_contract_isolated": True,
            "cross_cohort_promotion_forbidden": True,
        },
    )
    value.setdefault(
        "cohort_filter",
        {
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "runtime_effect": False,
        },
    )
    value.setdefault(
        "cumulative_learning",
        {
            "candidate_prompt_version": candidate_version,
            "candidate_contract_sha256": contract_sha256,
            "as_of_date": source_date,
            "clean_tuning_baseline_date": calibration.CLEAN_BASELINE_DATE,
        },
    )
    value.pop("artifact_content_sha256", None)
    return calibration._with_artifact_content_sha256(value)


def _valid_prior_calibration_payload(payload: dict) -> dict:
    value = json.loads(json.dumps(payload))
    value.setdefault("schema", calibration.SCHEMA)
    value.setdefault("policy_version", calibration.POLICY_VERSION)
    value.setdefault("runtime_effect", False)
    value.setdefault("runtime_authority", False)
    value.setdefault("order_authority", False)
    value.setdefault("provider_authority", False)
    value.setdefault("allowed_runtime_apply", False)
    value.setdefault("actual_order_submitted", False)
    value.setdefault("broker_order_forbidden", True)
    ledger = value.setdefault("ofi_action_outcome_calibration", {})
    ledger.setdefault("schema", calibration.OFI_LEDGER_SCHEMA)
    value.pop("artifact_content_sha256", None)
    return calibration._with_artifact_content_sha256(value)


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
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
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
    assert report["selected_review_candidate"]["candidate_prompt_version"] == (
        "candidate_v2"
    )


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
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
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
        candidate["prompt_review_gate"]["checks"]["bounded_probe_risk_budget"] is True
    )
    assert (
        candidate["diagnostic_checks_not_review_veto"]["severe_tail_rate_not_increased"]
        is None
    )
    assert (
        candidate["diagnostic_checks_not_review_veto"][
            "drawdown_recovery_capture_rate_not_decreased"
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
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
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


def test_same_prompt_isolated_krx_and_nxt_are_separate_candidates(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for venue, session, suffix in (
        ("KRX", "KRX_REGULAR", "krx"),
        ("NXT", "NXT_AFTERMARKET", "nxt"),
    ):
        payload = _valid_detailed_payload(
            {
                "target_date": "2026-09-07",
                "requests": [{"candidate": {"prompt_version": "candidate_isolated"}}],
                "paired_comparisons": [
                    {
                        "decision_trace_id": f"trace-{suffix}",
                        "stock_code": "005930",
                        "stage": "entry",
                        "effective_venue": venue,
                        "session_bucket": session,
                        "decision_ts": "2026-09-07T10:00:00+09:00",
                        "control_action": "WAIT",
                        "candidate_action": "WAIT",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": 0.1,
                        "delta_pct": 0.1,
                        "outcome_return_pct": 0.1,
                    }
                ],
            }
        )
        contract = payload["candidate_contract_sha256"]
        payload["promotion_cohort_scope"] = {
            "stages": ["entry"],
            "effective_venues": [venue],
            "session_buckets": [session],
            "isolated": True,
            "candidate_contract_sha256": contract,
            "candidate_contract_isolated": True,
            "cross_cohort_promotion_forbidden": True,
        }
        payload["cohort_filter"] = {
            "effective_venue": venue,
            "session_bucket": session,
            "runtime_effect": False,
        }
        payload = calibration._with_artifact_content_sha256(payload)
        path = paired_dir / f"ai_prompt_detailed_paired_replay_2026-09-07_{suffix}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["candidate_count"] == 2
    assert {
        (row["effective_venue"], row["session_bucket"])
        for row in report["candidate_summaries"]
    } == {("KRX", "KRX_REGULAR"), ("NXT", "NXT_AFTERMARKET")}


def test_multiple_ready_cohorts_are_not_ranked_into_one_global_selection(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    routes = (("KRX", "KRX_REGULAR"), ("NXT", "NXT_AFTERMARKET"))
    for venue, session in routes:
        for day_index, source_date in enumerate(("2026-09-07", "2026-09-08")):
            rows = []
            for offset in range(20):
                is_exposure = day_index == 0 and offset < 5
                rows.append(
                    {
                        "decision_trace_id": f"ready-{venue}-{day_index}-{offset}",
                        "stock_code": f"{offset % 10:06d}",
                        "effective_venue": venue,
                        "session_bucket": session,
                        "control_action": "WAIT",
                        "candidate_action": "BUY" if is_exposure else "WAIT",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": 0.2,
                        "candidate_execution_cost_contract_applied": is_exposure,
                        "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                        "candidate_probe_worst_loss_pct": -0.1,
                        "delta_pct": 0.2,
                    }
                )
            payload = _valid_detailed_payload(
                {
                    "target_date": source_date,
                    "requests": [{"candidate": {"prompt_version": "candidate_ready"}}],
                    "paired_comparisons": rows,
                }
            )
            payload["promotion_cohort_scope"]["effective_venues"] = [venue]
            payload["promotion_cohort_scope"]["session_buckets"] = [session]
            payload["cohort_filter"] = {
                "effective_venue": venue,
                "session_bucket": session,
                "runtime_effect": False,
            }
            payload = calibration._with_artifact_content_sha256(payload)
            path = paired_dir / (
                "ai_prompt_detailed_paired_replay_"
                f"{source_date}_{venue.lower()}_ready.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-08", data_root=tmp_path)

    assert report["review_candidate_count"] == 2
    assert len(report["review_ready_candidates"]) == 2
    assert report["selected_review_candidate"] is None
    assert report["selection_status"] == (
        "multiple_isolated_review_candidates_no_cross_cohort_selection"
    )
    assert report["optimizer_handoff"]["selected_review_candidate"] is None
    assert len(report["optimizer_handoff"]["review_ready_candidates"]) == 2


def test_conflicting_duplicate_trace_is_excluded_and_blocks_only_affected_cohort(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for suffix, outcome in (("a", 0.4), ("b", -0.4)):
        _write_json(
            paired_dir
            / f"ai_prompt_detailed_paired_replay_2026-09-07_conflict_{suffix}.json",
            {
                "target_date": "2026-09-07",
                "requests": [{"candidate": {"prompt_version": "candidate_conflict"}}],
                "paired_comparisons": [
                    {
                        "decision_trace_id": "same-trace",
                        "stock_code": "005930",
                        "control_action": "WAIT",
                        "candidate_action": "BUY",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": outcome,
                        "candidate_execution_cost_contract_applied": True,
                        "candidate_execution_cost_pct": 0.2,
                        "candidate_probe_worst_loss_pct": -0.2,
                        "delta_pct": outcome,
                        "outcome_return_pct": outcome,
                    }
                ],
            },
        )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["source_contract_summary"]["conflicting_duplicate_trace_count"] == 1
    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 0
    assert candidate["source_integrity_complete"] is False
    assert report["selected_review_candidate"] is None
    assert report["optimizer_handoff"]["source_contract_pass"] is True


def test_bounded_probe_budget_allows_one_twopercent_breach_in_five_exposures(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-09-07", "2026-09-08")):
        rows = []
        for offset in range(20):
            index = day_index * 20 + offset
            is_exposure = index < 5
            rows.append(
                {
                    "decision_trace_id": f"risk-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.4,
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "candidate_probe_worst_loss_pct": (-2.5 if index == 0 else -0.2),
                    "delta_pct": 0.4,
                    "first_hit": "target",
                    "candidate_error_taxonomy": [],
                }
            )
        _write_json(
            paired_dir / f"ai_prompt_detailed_paired_replay_{source_date}_risk.json",
            {
                "target_date": source_date,
                "requests": [{"candidate": {"prompt_version": "candidate_risk"}}],
                "paired_comparisons": rows,
            },
        )

    candidate = build_report(target_date="2026-09-08", data_root=tmp_path)[
        "candidate_summaries"
    ][0]

    assert candidate["candidate_probe_loss_budget_breach_count"] == 1
    assert candidate["candidate_probe_loss_budget_breach_rate_pct"] == 20.0
    assert candidate["candidate_probe_severe_tail_exposure_count"] == 1
    assert candidate["candidate_probe_severe_tail_rate_pct"] == 20.0
    assert candidate["candidate_probe_catastrophic_loss_count"] == 0
    assert (
        candidate["prompt_review_gate"]["checks"]["bounded_probe_risk_budget"] is True
    )
    assert candidate["review_ready_for_prompt_candidate"] is True


def test_positive_selective_candidate_is_ranked_as_thin_review_not_discarded(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for day_index, source_date in enumerate(("2026-09-07", "2026-09-08")):
        rows = []
        for offset in range(15):
            index = day_index * 15 + offset
            is_exposure = index == 0
            rows.append(
                {
                    "decision_trace_id": f"thin-{index}",
                    "stock_code": f"{index % 10:06d}",
                    "control_action": "WAIT",
                    "candidate_action": "BUY" if is_exposure else "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.2,
                    "candidate_execution_cost_contract_applied": is_exposure,
                    "candidate_execution_cost_pct": 0.2 if is_exposure else 0.0,
                    "candidate_probe_worst_loss_pct": -0.2,
                    "delta_pct": 0.2,
                }
            )
        _write_json(
            paired_dir / f"ai_prompt_detailed_paired_replay_{source_date}_thin.json",
            {
                "target_date": source_date,
                "requests": [{"candidate": {"prompt_version": "candidate_thin"}}],
                "paired_comparisons": rows,
            },
        )

    report = build_report(target_date="2026-09-08", data_root=tmp_path)
    candidate = report["candidate_summaries"][0]

    assert candidate["candidate_exposure_count"] == 1
    assert candidate["review_classification"] == "thin_positive_review"
    assert candidate["review_ready_for_prompt_candidate"] is False
    assert report["thin_positive_review_candidate_count"] == 1
    assert report["selected_review_candidate"] is None


def test_status_distinguishes_cumulative_unchanged_from_current_update(
    tmp_path: Path,
) -> None:
    paired_path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_candidate_v1.json"
    )
    _write_json(
        paired_path,
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_v1"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "trace-1",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "control_decision_value_pct": 0.0,
                    "candidate_primary_decision_value_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        },
    )

    report = build_report(target_date="2026-09-08", data_root=tmp_path)

    assert report["status"] == "cumulative_unchanged_no_new_exact_results"
    assert report["new_current_result_count"] == 0


def test_post_cutover_hashless_detailed_report_is_explicitly_rejected(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_hashless.json"
    )
    payload = _valid_detailed_payload(
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_hashless"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "hashless-1",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "candidate_primary_decision_value_pct": 0.1,
                    "outcome_return_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        }
    )
    payload.pop("artifact_content_sha256")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["candidate_count"] == 0
    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["source_contract_summary"]["rejection_reason_counts"] == {
        "artifact_content_sha256_missing_after_cutover": 1
    }


def test_pre_cutover_hashless_rows_are_diagnostic_and_do_not_poison_new_candidate(
    tmp_path: Path,
) -> None:
    paired_dir = tmp_path / "report" / "ai_prompt_detailed_paired_replay"
    for source_date, trace_id in (
        ("2026-09-06", "legacy-trace"),
        ("2026-09-07", "verified-trace"),
    ):
        payload = _valid_detailed_payload(
            {
                "target_date": source_date,
                "requests": [{"candidate": {"prompt_version": "candidate_continuity"}}],
                "paired_comparisons": [
                    {
                        "decision_trace_id": trace_id,
                        "stock_code": "005930",
                        "control_action": "WAIT",
                        "candidate_action": "WAIT",
                        "control_decision_value_pct": 0.0,
                        "candidate_primary_decision_value_pct": 0.1,
                        "delta_pct": 0.1,
                    }
                ],
            }
        )
        if source_date < calibration.DETAILED_SELF_HASH_CUTOVER_DATE:
            payload.pop("artifact_content_sha256")
        path = paired_dir / (
            f"ai_prompt_detailed_paired_replay_{source_date}_continuity.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    candidate = report["candidate_summaries"][0]
    assert candidate["exact_trace_count"] == 1
    assert candidate["source_integrity_complete"] is True
    assert candidate["source_report_count"] == 2
    assert candidate["verified_source_report_count"] == 1
    assert candidate["legacy_hashless_source_report_count"] == 1
    assert (
        report["source_contract_summary"]["legacy_hashless_diagnostic_row_count"] == 1
    )


def test_current_date_invalid_row_is_excluded_and_status_is_not_updated(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_row_gap.json",
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_row_gap"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "wrong-stage",
                    "stage": "holding",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "candidate_primary_decision_value_pct": 0.1,
                    "outcome_return_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        },
    )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["new_current_result_count"] == 0
    assert report["source_contract_summary"]["current_date_row_exclusion_count"] == 1


def test_non_native_source_count_is_rejected_before_calibration(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_bad_count.json",
        {
            "target_date": "2026-09-07",
            "schema_rejected_count": 0.5,
            "requests": [{"candidate": {"prompt_version": "candidate_bad_count"}}],
            "paired_comparisons": [],
        },
    )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["candidate_count"] == 0
    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["source_contract_summary"]["rejection_reason_counts"] == {
        "schema_rejected_count_invalid": 1
    }


def test_naive_decision_timestamp_is_excluded_from_exact_date_calibration(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path
        / "report"
        / "ai_prompt_detailed_paired_replay"
        / "ai_prompt_detailed_paired_replay_2026-09-07_naive_time.json",
        {
            "target_date": "2026-09-07",
            "requests": [{"candidate": {"prompt_version": "candidate_naive"}}],
            "paired_comparisons": [
                {
                    "decision_trace_id": "naive-time",
                    "decision_ts": "2026-09-07T10:00:00",
                    "stock_code": "005930",
                    "control_action": "WAIT",
                    "candidate_action": "WAIT",
                    "candidate_primary_decision_value_pct": 0.1,
                    "outcome_return_pct": 0.1,
                    "delta_pct": 0.1,
                }
            ],
        },
    )

    report = build_report(target_date="2026-09-07", data_root=tmp_path)

    assert report["status"] == "current_input_excluded_cumulative_unchanged"
    assert report["source_contract_summary"]["current_date_row_exclusion_count"] == 1
    assert report["source_reports"][0]["row_exclusion_reason_counts"] == {
        "decision_timestamp_invalid_or_naive": 1
    }
