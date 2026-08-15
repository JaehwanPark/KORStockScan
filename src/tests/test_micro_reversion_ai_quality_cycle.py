from __future__ import annotations

from copy import deepcopy
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import main_lifecycle_journal as lifecycle_journal
from src.engine.scalping import main_lifecycle_paired as lifecycle_paired
from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle


def _paired_request(trace_id: str = "trace-1", *, stage: str = "entry") -> dict:
    return {
        "paired_replay_id": f"pair-{trace_id}",
        "decision_trace_id": trace_id,
        "decision_ts": "2026-08-14T09:00:00+09:00",
        "stage": stage,
        "endpoint": "analyze_target",
        "stock_code": "000001",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "a" * 64,
        "request_envelope_sha256": "b" * 64,
        "outcome_join_key": f"label-{trace_id}",
        "sample_floor": {"pass": True},
        "candidate": {"contract_sha256": "c" * 64},
        "control": {},
        **cycle.OFFLINE_AUTHORITY,
    }


def test_build_prepared_request_artifact_filters_unsupported_and_duplicate():
    first = _paired_request()
    duplicate = {**first, "paired_replay_id": "pair-duplicate"}
    unsupported = _paired_request("trace-2", stage="entry_price")
    paired = {
        "schema": quality.PAIRED_SCHEMA,
        "target_date": "2026-08-14",
        "requests": [first, duplicate, unsupported],
        **cycle.OFFLINE_AUTHORITY,
    }

    artifact = cycle.build_prepared_request_artifact(
        target_date="2026-08-14",
        paired_report=paired,
        source={"resolved_path": "/tmp/paired.json", "stored_sha256": "d" * 64},
    )

    assert artifact["prepared_request_count"] == 1
    assert artifact["excluded_request_count"] == 2
    assert {row["reason"] for row in artifact["exclusions"]} == {
        "prepared_request_trace_id_duplicate",
        "stage_economic_owner_unsupported",
    }
    cycle._validate_prepared_artifact(artifact)
    assert artifact["runtime_effect"] is False
    assert artifact["broker_order_forbidden"] is True


def test_daily_usd_cap_preserves_exact_decimal_for_command_and_validator():
    canonical, command_text = cycle._canonical_daily_usd_cap("1.000000006")

    assert canonical == Decimal("1.000000006")
    assert command_text == "1.000000006"


def _execution_report(
    target_date: str,
    *,
    parent_id: str,
    trace_id: str,
    stock_code: str,
    control_ev: float = 0.0,
    candidate_ev: float = 0.20,
) -> dict:
    cost_artifact_sha256 = cycle._sha256(
        {"kind": "reviewed_cost_catalog", "target_date": target_date}
    )
    cost_catalog_content_sha256 = cycle._sha256(
        {"kind": "reviewed_cost_catalog_body", "target_date": target_date}
    )
    symbol_master_artifact_sha256 = cycle._sha256(
        {"kind": "symbol_master", "target_date": target_date}
    )
    symbol_metadata_record_sha256 = cycle._sha256(
        {"kind": "symbol_record", "stock_code": stock_code}
    )
    arms = {
        "replay_control_exact_no_micro": {
            "action": "WAIT",
            "exposure_role": "no_entry_exposure",
            "exposure_fraction": 0.0,
            "economic_signal_selected": False,
            "source_quality_adjusted_ev_pct": 0.0,
            "standardized_probe_observation_ev_pct": None,
            "notional_net_profit_eligible": False,
            "notional_incremental_value_krw": None,
            "adverse_exposure": False,
            "severe_tail_exposure": False,
            "after_cost_target_first": False,
        },
        "replay_control_exact_plus_micro": {
            "action": "WAIT",
            "exposure_role": "no_entry_exposure",
            "exposure_fraction": 0.0,
            "economic_signal_selected": False,
            "source_quality_adjusted_ev_pct": control_ev,
            "standardized_probe_observation_ev_pct": None,
            "notional_net_profit_eligible": False,
            "notional_incremental_value_krw": None,
            "adverse_exposure": False,
            "severe_tail_exposure": False,
            "after_cost_target_first": False,
        },
        "replay_candidate_exact_plus_micro": {
            "action": "BUY",
            "exposure_role": "full_entry_exposure",
            "exposure_fraction": 1.0,
            "economic_signal_selected": True,
            "source_quality_adjusted_ev_pct": candidate_ev,
            "standardized_probe_observation_ev_pct": None,
            "notional_net_profit_eligible": True,
            "notional_incremental_value_krw": 200.0,
            "adverse_exposure": True,
            "severe_tail_exposure": False,
            "after_cost_target_first": True,
        },
    }
    evaluation_without_hash = {
        "schema": "ai_micro_reversion_three_arm_evaluation_v1",
        "status": "evaluated",
        "complete_parent_count": 1,
        "excluded_parent_count": 0,
        "exclusions": [],
        "sample_floor": {"observed_rows": 1},
        "arm_metrics": {arm: {"row_count": 1} for arm in cycle.EXPECTED_ARMS},
        "stage_venue_partitions": [
            {
                "decision_stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "complete_parent_count": 1,
                "arm_metrics": {arm: {"row_count": 1} for arm in cycle.EXPECTED_ARMS},
            }
        ],
        "rows": [
            {
                "paired_replay_parent_id": parent_id,
                "decision_trace_id": trace_id,
                "outcome_join_key": f"label-{trace_id}",
                "decision_stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "stock_code": stock_code,
                "cost_profile_artifact_sha256": cost_artifact_sha256,
                "cost_catalog_content_sha256": cost_catalog_content_sha256,
                "selected_cost_profile_id": "reviewed-krx-equity-v1",
                "selected_cost_profile_content_sha256": "5" * 64,
                "symbol_master_artifact_sha256": symbol_master_artifact_sha256,
                "symbol_metadata_record_sha256": symbol_metadata_record_sha256,
                "outcome_label_content_sha256": cycle._sha256(
                    {"target_date": target_date, "trace_id": trace_id}
                ),
                "cost_adjusted_outcome_pct": candidate_ev,
                "mae_pct": -0.5,
                "first_hit": "target_first",
                "arms": arms,
            }
        ],
        **cycle.OFFLINE_AUTHORITY,
    }
    evaluation = {
        **evaluation_without_hash,
        "evaluation_content_sha256": cycle._sha256(evaluation_without_hash),
    }
    results = []
    request_refs = []
    outcome_label_content_sha256 = cycle._sha256(
        {"target_date": target_date, "trace_id": trace_id}
    )
    for arm in cycle.EXPECTED_ARMS:
        reservation_id = f"reservation-{parent_id}-{arm}"
        request_id = f"{parent_id}-{arm}"
        candidate_input_sha256 = cycle._sha256(
            {"parent_id": parent_id, "arm": arm, "kind": "candidate_input"}
        )
        prompt_sha256 = cycle._sha256(
            {"arm": arm, "kind": "stable_prompt_contract_text"}
        )
        prompt_contract_sha256 = (
            "1" * 64 if arm != "replay_candidate_exact_plus_micro" else "2" * 64
        )
        request_refs.append(
            {
                "paired_replay_parent_id": parent_id,
                "paired_replay_id": request_id,
                "micro_reversion_replay_arm": arm,
                "decision_trace_id": trace_id,
                "candidate_input_sha256": candidate_input_sha256,
                "prompt_sha256": prompt_sha256,
                "prompt_contract_sha256": prompt_contract_sha256,
            }
        )
        candidate_response = {
            "action": arms[arm]["action"],
            "confidence": 0.75,
        }
        result_content = {
            "paired_replay_parent_id": parent_id,
            "paired_replay_id": request_id,
            "micro_reversion_replay_arm": arm,
            "decision_trace_id": trace_id,
            "decision_ts": f"{target_date}T09:00:00+09:00",
            "stage": "entry",
            "source_exact_payload_sha256": cycle._sha256(
                {"parent_id": parent_id, "kind": "exact"}
            ),
            "candidate_input_sha256": candidate_input_sha256,
            "prompt_sha256": prompt_sha256,
            "prompt_contract_sha256": prompt_contract_sha256,
            "outcome_join_key": f"label-{trace_id}",
            "outcome_label_content_sha256": outcome_label_content_sha256,
            "replay_result": {
                "status": "pass",
                "stage": "entry",
                "candidate_response": candidate_response,
                "candidate_attempts": [
                    {
                        "status": "pass",
                        "provider_provenance": {
                            "provider": "openai",
                            "model": "gpt-test",
                            "transport": "openai_responses_http_offline",
                            "source_transport_contract": "openai_responses_http_offline",
                            "response_id": f"response-{request_id}",
                            "response_sha256": cycle._sha256(
                                {"request_id": request_id, "kind": "response"}
                            ),
                            "provider_none": False,
                            "provider_call_attempted": True,
                            "provider_call_succeeded": True,
                            "provider_budget_reservation_id": reservation_id,
                            "provider_budget_attempt_identity_sha256": (
                                cycle._sha256({"reservation_id": reservation_id})
                            ),
                            "provider_budget_settled": True,
                            "provider_budget_unknown_usage_reservation_retained": (
                                False
                            ),
                            "provider_budget_reserved_cost_usd": "0.1",
                            "provider_budget_actual_cost_usd": "0.1",
                            "provider_budget_circuit_breaker_open": False,
                        },
                    }
                ],
            },
            "candidate_response_content_sha256": cycle._sha256(candidate_response),
            **cycle.OFFLINE_AUTHORITY,
        }
        results.append(
            {
                "result_id": "micro-result-" + cycle._sha256(result_content)[:24],
                **result_content,
            }
        )
    budget_without_hash = {
        "schema": cycle.BUDGET_SUMMARY_SCHEMA,
        "daily_attempt_cap": 12,
        "daily_usd_cap": "1.0",
        "committed_cost_usd": "0.5",
        "circuit_breaker_open": False,
        "reservation_count": len(results),
        "pricing_artifact_content_sha256": "e" * 64,
        **cycle.PROVIDER_BUDGET_AUTHORITY_CONTRACT,
    }
    body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": target_date,
        "materialized_report_content_sha256": cycle._sha256(
            {"target_date": target_date, "kind": "materialized_content"}
        ),
        "materialized_request_census_sha256": cycle._sha256(
            {"target_date": target_date, "kind": "materialized_census"}
        ),
        "materialized_report_artifact_sha256": cycle._sha256(
            {"target_date": target_date, "kind": "materialized_artifact"}
        ),
        "outcome_label_artifact_sha256": cycle._sha256(
            {"target_date": target_date, "kind": "outcome_artifact"}
        ),
        "three_arm_evaluation": evaluation,
        "results": results,
        "status": "offline_three_arm_execution_complete",
        "execution_requested": True,
        "provider_call_attempted": True,
        "provider_call_performed": True,
        "provider_call_succeeded": True,
        "provider_response_hash_observed": True,
        "outcomes_embedded_in_provider_input": False,
        "request_count": len(results),
        "parent_count": 1,
        "request_refs": request_refs,
        "result_count": len(results),
        "result_ids": [row["result_id"] for row in results],
        "execution_failed_count": 0,
        "execution_exclusion_count": 0,
        "execution_exclusions": [],
        "blocking_execution_exclusion_count": 0,
        "blocking_execution_exclusions": [],
        "deferred_request_count": 0,
        "uncommitted_result_count": 0,
        "committed_parent_count": 1,
        "newly_committed_parent_count": 1,
        "new_result_count": len(results),
        "new_result_ids": [row["result_id"] for row in results],
        "reused_result_count": 0,
        "checkpoint_resume_result_count": 0,
        "provisional_checkpoint_result_count": 0,
        "candidate_model_call_attempted": True,
        "selected_parent_ids": [parent_id],
        "selected_request_ids": [row["paired_replay_id"] for row in results],
        "deferred_request_ids": [],
        "max_new_requests": len(results),
        "outcome_joins": [
            {
                "outcome_join_key": f"label-{trace_id}",
                "outcome_label_content_sha256": outcome_label_content_sha256,
                "decision_trace_id": trace_id,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "label_status": "mature",
                "outcome_embedded_in_provider_input": False,
            }
        ],
        "provider_provenance_pass_count": len(results),
        "provider_budget_contract_findings": [],
        "provider_budget": {
            **budget_without_hash,
            "summary_content_sha256": cycle._sha256(budget_without_hash),
        },
        **cycle.OFFLINE_AUTHORITY,
    }
    return {**body, "report_content_sha256": cycle._sha256(body)}


def _reseal_execution_report(report: dict) -> None:
    evaluation = report.get("three_arm_evaluation")
    if isinstance(evaluation, dict):
        evaluation["evaluation_content_sha256"] = cycle._content_hash(
            evaluation,
            "evaluation_content_sha256",
        )
    report["report_content_sha256"] = cycle._content_hash(
        report,
        "report_content_sha256",
    )


def _reseal_execution_result_ids(report: dict) -> None:
    id_mapping: dict[str, str] = {}
    resealed_results = []
    for result in report["results"]:
        old_id = result["result_id"]
        new_id = (
            "micro-result-"
            + cycle._sha256(
                {key: value for key, value in result.items() if key != "result_id"}
            )[:24]
        )
        id_mapping[old_id] = new_id
        resealed_results.append({**result, "result_id": new_id})
    report["results"] = resealed_results
    report["result_ids"] = [result["result_id"] for result in report["results"]]
    report["new_result_ids"] = [
        id_mapping[result_id] for result_id in report.get("new_result_ids") or []
    ]
    _reseal_execution_report(report)


def _seal_lifecycle_report(report: dict) -> dict:
    for field in (
        "content_sha256",
        "report_content_sha256",
        "artifact_content_sha256",
    ):
        report.pop(field, None)
    producer_hash = cycle._sha256(report)
    report["content_sha256"] = producer_hash
    report["report_content_sha256"] = producer_hash
    report["artifact_content_sha256"] = cycle._sha256(report)
    return report


def _lifecycle_report(
    target_date: str,
    *,
    trace_id: str,
    stock_code: str = "000001",
    session_exposure_sec: float = 3600.0,
    eligible: bool = True,
) -> dict:
    cost_artifact_sha256 = cycle._sha256(
        {"kind": "reviewed_cost_catalog", "target_date": target_date}
    )
    symbol_master_artifact_sha256 = cycle._sha256(
        {"kind": "symbol_master", "target_date": target_date}
    )
    lineage = {
        "record_id": f"record-{trace_id}",
        "stock_code": stock_code,
        "attempt_id": f"attempt-{trace_id}",
    }
    lifecycle_id = f"mlc-{cycle._sha256(lineage)[:32]}"
    row = {
        "main_lifecycle_id": lifecycle_id,
        **lineage,
        "trade_date": target_date,
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "decision_trace_ids": [trace_id],
        "promotion_evidence_eligible": eligible,
        "row_source_quality_gate_pass": eligible,
        "promotion_blockers": [] if eligible else ["test_ineligible"],
        "lifecycle_window_source_quality_disposition": (
            "eligible_before_global_source_contract_gate"
            if eligible
            else "excluded_exact_lifecycle_window"
        ),
        "lifecycle_window_exclusion_taxonomies": (
            [] if eligible else ["lifecycle_completeness_or_consistency_gap"]
        ),
        "promotion_disposition": (
            "eligible_source_only" if eligible else "excluded_exact_lifecycle_window"
        ),
        "terminal_state": "FINAL_EXIT_RECONCILED",
        "actual_holding_duration_sec": 120.0,
        "session_exposure_sec": session_exposure_sec,
        "capital_time_krw_hours": 50_000.0,
        "bbo_coverage_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "invalid_transition_count": 0,
        "observed_actual_broker_order_submitted": True,
        "entry_fill_qty": 1.0,
        "scale_in_fill_qty": 0.0,
        "exit_qty": 1.0,
        "open_qty_at_censor": 0.0,
        "broker_execution_official_reference_sha": (
            cycle.KIWOOM_OFFICIAL_REFERENCE_SHA
        ),
        "broker_execution_provenance_schema": (
            cycle.BROKER_EXECUTION_PROVENANCE_SCHEMA
        ),
        "broker_execution_raw_envelope_schema": (
            cycle.BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
        ),
        "broker_execution_unique_count": 2,
        "broker_execution_replay_duplicate_count": 0,
        "broker_execution_conflict_count": 0,
        "broker_execution_order_progress_conflict_count": 0,
        "broker_execution_submission_link_conflict_count": 0,
        "broker_order_no_cross_lifecycle_conflict_count": 0,
        "broker_execution_cross_lifecycle_identity_conflict_count": 0,
        "broker_execution_provenance_state_counts": {"complete": 2},
        "broker_execution_provenance_gap_count": 0,
        "broker_execution_provenance_gap_reasons": [],
        "broker_execution_entry_covered_qty": 1.0,
        "broker_execution_exit_covered_qty": 1.0,
        "broker_execution_partial_count": 0,
        "broker_execution_full_count": 2,
        "broker_execution_unreconciled_order_count": 0,
        "broker_submitted_order_count": 2,
        "broker_submitted_requested_qty_by_phase": {"entry": 1, "exit": 1},
        "broker_submitted_requested_qty_by_order_no": {
            "1000001": 1,
            "1000002": 1,
        },
        "broker_executed_order_qty_by_phase": {
            "entry": {"1000001": 1},
            "exit": {"1000002": 1},
        },
        "broker_submitted_order_coverage_gap_phases": [],
        "broker_submitted_order_qty_mismatch_phases": [],
        "reviewed_cost_profile_sha256": cost_artifact_sha256,
        "reviewed_cost_profile_verified": True,
        "symbol_master_artifact_sha256": symbol_master_artifact_sha256,
        "symbol_master_artifact_verified": True,
        **cycle.LIFECYCLE_REPORT_AUTHORITY_CONTRACT,
    }
    source_census = {
        "source_path": f"/tmp/pipeline_events_{target_date}.jsonl",
        "source_exists": True,
        "source_is_gzip": False,
        "source_raw_sha256": "a" * 64,
        "source_raw_bytes": 100,
        "source_decoded_sha256": "b" * 64,
        "source_decoded_bytes": 100,
        "physical_line_count": 10,
        "blank_line_count": 0,
        "json_object_count": 10,
        "malformed_json_count": 0,
        "non_object_count": 0,
        "source_read_error": None,
    }
    exclusion_reasons = [] if eligible else ["test_ineligible"]
    exclusion_taxonomies = (
        [] if eligible else ["lifecycle_completeness_or_consistency_gap"]
    )
    exclusion_manifest = {
        "schema": cycle.LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA,
        **cycle.LIFECYCLE_EXCLUSION_AUTHORITY_CONTRACT,
        "excluded_lifecycle_count": int(not eligible),
        "eligible_lifecycle_count": int(eligible),
        "taxonomy_counts": (
            {} if eligible else {"lifecycle_completeness_or_consistency_gap": 1}
        ),
        "reason_code_counts": {} if eligible else {"test_ineligible": 1},
        "entries": (
            []
            if eligible
            else [
                {
                    "main_lifecycle_id": lifecycle_id,
                    "exclusion_scope": "exact_main_lifecycle_window",
                    "taxonomies": exclusion_taxonomies,
                    "reason_codes_sha256": cycle._sha256(exclusion_reasons),
                }
            ]
        ),
    }
    report = {
        "schema": cycle.LIFECYCLE_REPORT_SCHEMA,
        "target_date": target_date,
        "source_transition_schema": cycle.JOURNAL_SCHEMA,
        "source_pipeline_identity_schema": cycle.PIPELINE_IDENTITY_SCHEMA,
        "source_kind": "pipeline_events_explicit_id_only",
        "source_raw_sha256": source_census["source_raw_sha256"],
        "source_content_sha256": source_census["source_decoded_sha256"],
        "source_raw_census": source_census,
        "source_census_content_sha256": cycle._sha256(source_census),
        "broker_execution_official_reference_sha": (
            cycle.KIWOOM_OFFICIAL_REFERENCE_SHA
        ),
        "broker_execution_provenance_schema": (
            cycle.BROKER_EXECUTION_PROVENANCE_SCHEMA
        ),
        "broker_execution_raw_envelope_schema": (
            cycle.BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
        ),
        "reviewed_cost_profile_sha256": cost_artifact_sha256,
        "reviewed_cost_profile_verified": True,
        "symbol_master_artifact_sha256": symbol_master_artifact_sha256,
        "symbol_master_artifact_verified": True,
        "reference_contract_blockers": [],
        "source_invalid_transition_count": 0,
        "mixed_source_row_count": 0,
        "lifecycle_accumulator_overflow_row_count": 0,
        "transition_event_identity_overflow_row_count": 0,
        "pipeline_lifecycle_instrumentation_gap_count": 0,
        "lifecycle_invalid_transition_count": 0,
        "broker_execution_provenance_gap_count": 0,
        "broker_execution_conflict_count": 0,
        "broker_execution_order_progress_conflict_count": 0,
        "broker_execution_submission_link_conflict_count": 0,
        "broker_order_no_cross_lifecycle_conflict_count": 0,
        "broker_execution_cross_lifecycle_identity_conflict_count": 0,
        "broker_execution_replay_duplicate_count": 0,
        "broker_execution_unique_count": 2,
        "candidate_row_gate_failure_count": 0 if eligible else 1,
        "instrumentation_gap_count": 0 if eligible else 1,
        "lifecycle_window_exclusion_manifest": exclusion_manifest,
        "lifecycle_count": 1,
        "promotion_evidence_eligible_count": int(eligible),
        "promotion_ready": eligible,
        "promotion_ready_lifecycle_ids": [lifecycle_id] if eligible else [],
        "global_source_quality_gate_pass": True,
        "global_source_quality_gate_blockers": [],
        "rows": [row],
        **cycle.LIFECYCLE_REPORT_AUTHORITY_CONTRACT,
    }
    return _seal_lifecycle_report(report)


def _mixed_lifecycle_report(target_date: str) -> dict:
    clean_report = _lifecycle_report(target_date, trace_id="trace-clean")
    excluded_report = _lifecycle_report(
        target_date,
        trace_id="trace-excluded",
        stock_code="000002",
        eligible=False,
    )
    clean_row = clean_report["rows"][0]
    excluded_row = excluded_report["rows"][0]
    clean_report["rows"] = [clean_row, excluded_row]
    clean_report["broker_execution_unique_count"] = 4
    clean_report["candidate_row_gate_failure_count"] = 1
    clean_report["instrumentation_gap_count"] = 1
    clean_report["lifecycle_count"] = 2
    clean_report["promotion_evidence_eligible_count"] = 1
    clean_report["promotion_ready"] = True
    clean_report["promotion_ready_lifecycle_ids"] = [clean_row["main_lifecycle_id"]]
    clean_report["lifecycle_window_exclusion_manifest"] = {
        **excluded_report["lifecycle_window_exclusion_manifest"],
        "eligible_lifecycle_count": 1,
    }
    return _seal_lifecycle_report(clean_report)


def _producer_broker_execution_proof(
    *,
    base: datetime,
    order_no: str,
    execution_no: str,
    second: int,
    side: str,
) -> dict:
    price = 10_000 if side == "BUY" else 10_010
    raw = {
        "broker_raw_envelope_schema": (
            lifecycle_journal.BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
        ),
        "broker_raw_source_type": "00",
        "9203": order_no,
        "9001": "005930",
        "913": "체결",
        "900": "1",
        "902": "0",
        "903": str(price),
        "905": "+매수" if side == "BUY" else "-매도",
        "907": "2" if side == "BUY" else "1",
        "908": (base + timedelta(seconds=second)).strftime("%H%M%S"),
        "909": execution_no,
        "910": str(price),
        "911": "1",
        "914": str(price),
        "915": "1",
        "2134": "1",
        "2135": "KRX",
        "2136": "N",
    }
    proof = lifecycle_journal.build_broker_execution_provenance(
        raw,
        expected_qty=1,
        expected_price=price,
        expected_stock_code="005930",
        expected_side=side,
        lifecycle_venue="KRX",
        expected_fill_state="full",
    )
    assert proof["broker_execution_provenance_state"] == "complete"
    return proof


def _producer_lifecycle_transitions(
    *,
    target_date: str,
    attempt: str,
    namespace: int,
    include_scale_in: bool,
    cost_hash: str,
    symbol_hash: str,
) -> list[dict]:
    base = datetime(2026, 8, 14, 9, 0, tzinfo=timezone(timedelta(hours=9)))
    identity = {
        "record_id": f"record-{attempt}",
        "stock_code": "005930",
        "attempt_id": f"attempt-{attempt}",
    }
    identity["main_lifecycle_id"] = lifecycle_journal.mint_main_lifecycle_id(**identity)

    def transition(stage: str, second: int, data: dict) -> dict:
        return lifecycle_journal.build_transition(
            **identity,
            trade_date=target_date,
            stage=stage,
            observed_at=base + timedelta(seconds=second),
            venue="KRX",
            session_bucket="KRX_REGULAR",
            data={
                "decision_trace_id": f"trace-{attempt}-{stage}-{second}",
                "bbo_observed": True,
                "depth_observed": True,
                "cost_artifact_sha256": cost_hash,
                "cost_artifact_verified": True,
                "symbol_master_sha256": symbol_hash,
                "symbol_master_verified": True,
                **data,
            },
        )

    entry_order_no = f"1{namespace:06d}"
    exit_order_no = f"3{namespace:06d}"
    rows = [
        transition(
            "scanner",
            0,
            {
                "session_exposure_start_at": base.isoformat(),
                "session_exposure_end_at": (base + timedelta(minutes=10)).isoformat(),
            },
        ),
        transition("entry_decision", 1, {"action": "BUY"}),
        transition(
            "submit",
            2,
            {
                "requested_qty": 1,
                "actual_broker_order_submitted": True,
                "broker_order_no": entry_order_no,
                "broker_order_no_list": entry_order_no,
            },
        ),
        transition(
            "fill",
            3,
            {
                "fill_state": "full",
                "fill_qty": 1,
                "fill_price": 10_000,
                **_producer_broker_execution_proof(
                    base=base,
                    order_no=entry_order_no,
                    execution_no=f"2{namespace:06d}",
                    second=3,
                    side="BUY",
                ),
            },
        ),
        transition("holding", 4, {"action": "HOLD"}),
    ]
    if include_scale_in:
        rows.append(transition("scale_in", 5, {"scale_in_decision": "NO_ADD"}))
    rows.extend(
        (
            transition(
                "exit",
                62,
                {
                    "requested_qty": 1,
                    "actual_broker_order_submitted": True,
                    "broker_order_no": exit_order_no,
                    "broker_order_no_list": exit_order_no,
                },
            ),
            transition(
                "exit",
                63,
                {
                    "exit_qty": 1,
                    "exit_price": 10_010,
                    "broker_reconciled": True,
                    "reconciled_final_exit": True,
                    "fees_taxes_krw": 1,
                    "slippage_krw": 1,
                    "slippage_basis_price": 10_011,
                    "slippage_basis_source": "test_exit_decision_price",
                    "realized_net_pnl_krw": 8,
                    **_producer_broker_execution_proof(
                        base=base,
                        order_no=exit_order_no,
                        execution_no=f"4{namespace:06d}",
                        second=63,
                        side="SELL",
                    ),
                },
            ),
        )
    )
    return rows


def test_rolling_r2_r3_emits_source_only_candidate_after_strict_20_day_gate():
    start = date(2026, 7, 20)
    execution_reports = []
    lifecycle_reports = []
    source_pass: dict[str, bool] = {}
    economic_pass: dict[str, bool] = {}
    for index in range(20):
        target_date = (start + timedelta(days=index)).isoformat()
        trace_id = f"trace-{index}"
        parent_id = f"parent-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        execution_reports.append(
            _execution_report(
                target_date,
                parent_id=parent_id,
                trace_id=trace_id,
                stock_code=stock_code,
            )
        )
        lifecycle_reports.append(
            _lifecycle_report(
                target_date,
                trace_id=trace_id,
                stock_code=stock_code,
            )
        )
        source_pass[target_date] = True
        economic_pass[target_date] = True

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=(start + timedelta(days=19)).isoformat(),
        execution_reports=execution_reports,
        lifecycle_reports=lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
    )

    assert rolling["joined_parent_count"] == 20
    assert rolling["partitions"][0]["r3_source_candidate_eligible"] is True
    metrics = rolling["partitions"][0]["windows"]["20"]
    assert metrics["eligible_signals_per_session_hour"] == pytest.approx(1.0)
    assert metrics["average_actual_holding_duration_sec"] == 120.0
    assert metrics["candidate_total_notional_net_profit_krw"] == 4000.0
    assert manifest["candidate_count"] == 1
    candidate = manifest["candidates"][0]
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["first_exact_candidate_approval_required"] is True
    assert candidate["continuous_auto_chain_eligible"] is False
    assert manifest["first_runtime_candidate_auto_apply_performed"] is False


@pytest.mark.parametrize("failure_kind", ("contract", "collection"))
def test_rolling_r3_never_promotes_valid_subset_with_invalid_historical_execution(
    failure_kind,
):
    start = date(2026, 7, 20)
    execution_reports = []
    lifecycle_reports = []
    source_pass: dict[str, bool] = {}
    economic_pass: dict[str, bool] = {}
    for index in range(20):
        target_date = (start + timedelta(days=index)).isoformat()
        trace_id = f"trace-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        execution_reports.append(
            _execution_report(
                target_date,
                parent_id=f"parent-{index}",
                trace_id=trace_id,
                stock_code=stock_code,
            )
        )
        lifecycle_reports.append(
            _lifecycle_report(
                target_date,
                trace_id=trace_id,
                stock_code=stock_code,
            )
        )
        source_pass[target_date] = True
        economic_pass[target_date] = True

    input_diagnostics = []
    if failure_kind == "contract":
        malformed = deepcopy(execution_reports[0])
        malformed["results"].pop()
        _reseal_execution_report(malformed)
        execution_reports.append(malformed)
    else:
        input_diagnostics.append(
            {
                "target_date": execution_reports[0]["target_date"],
                "artifact": "execution",
                "status": "invalid",
                "reason": "JSONDecodeError",
            }
        )

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=(start + timedelta(days=19)).isoformat(),
        execution_reports=execution_reports,
        lifecycle_reports=lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
        input_diagnostics=input_diagnostics,
    )

    assert rolling["joined_parent_count"] == 20
    assert rolling["status"] == "historical_execution_contract_blocked"
    assert rolling["global_candidate_blockers"]
    assert rolling["partitions"][0]["r3_source_candidate_eligible"] is False
    assert manifest["candidate_count"] == 0
    assert manifest["status"] == (
        "source_only_candidate_blocked_invalid_historical_execution"
    )
    assert manifest["global_candidate_blockers"] == rolling["global_candidate_blockers"]


def test_rolling_r3_rejects_one_self_rehashed_legacy_fid_day():
    start = date(2026, 7, 20)
    execution_reports = []
    lifecycle_reports = []
    source_pass: dict[str, bool] = {}
    economic_pass: dict[str, bool] = {}
    for index in range(20):
        target_date = (start + timedelta(days=index)).isoformat()
        trace_id = f"trace-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        execution_reports.append(
            _execution_report(
                target_date,
                parent_id=f"parent-{index}",
                trace_id=trace_id,
                stock_code=stock_code,
            )
        )
        lifecycle_reports.append(
            _lifecycle_report(
                target_date,
                trace_id=trace_id,
                stock_code=stock_code,
            )
        )
        source_pass[target_date] = True
        economic_pass[target_date] = True
    legacy_row = lifecycle_reports[0]["rows"][0]
    legacy_row.pop("broker_execution_raw_envelope_schema")
    legacy_row.pop("broker_execution_provenance_state_counts")
    _seal_lifecycle_report(lifecycle_reports[0])

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=(start + timedelta(days=19)).isoformat(),
        execution_reports=execution_reports,
        lifecycle_reports=lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
    )

    assert rolling["joined_parent_count"] == 19
    assert any(
        "row_broker_contract_invalid:broker_execution_raw_envelope_schema" in finding
        for finding in rolling["lifecycle_report_findings"]
    )
    assert manifest["candidate_count"] == 0


def test_rolling_rejects_missing_real_session_denominator_instead_of_3600_per_hour():
    target_date = "2026-08-14"
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[
            _execution_report(
                target_date,
                parent_id="parent-1",
                trace_id="trace-1",
                stock_code="000001",
            )
        ],
        lifecycle_reports=[
            _lifecycle_report(
                target_date,
                trace_id="trace-1",
                session_exposure_sec=0.0,
            )
        ],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert rolling["joined_parent_count"] == 0
    assert rolling["status"] == "no_joined_lifecycle_rows"
    assert rolling["exclusions"][0]["reason"] == (
        "lifecycle_session_exposure_nonpositive"
    )
    assert manifest["candidate_count"] == 0


def test_lifecycle_index_permanently_blocks_conflicting_trace_rows():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    conflicting_report = _lifecycle_report(target_date, trace_id="trace-1")
    conflicting_report["rows"][0]["actual_holding_duration_sec"] = 121.0
    _seal_lifecycle_report(conflicting_report)

    index, findings = cycle._lifecycle_index([report, conflicting_report])

    assert index == {}
    assert findings == [f"lifecycle_trace_identity_ambiguous:{target_date}:trace-1"]


def test_lifecycle_index_blocks_clean_join_when_excluded_row_reuses_same_trace():
    target_date = "2026-08-14"
    report = _mixed_lifecycle_report(target_date)
    report["rows"][1]["decision_trace_ids"] = ["trace-clean"]
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert (target_date, "trace-clean") not in index
    assert any(
        finding == f"lifecycle_trace_identity_ambiguous:{target_date}:trace-clean"
        for finding in findings
    )


def test_lifecycle_index_rejects_missing_producer_content_hash():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report.pop("content_sha256")
    report["artifact_content_sha256"] = cycle._content_hash(
        report, "artifact_content_sha256"
    )

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert findings == [f"lifecycle_report_hash_invalid:{target_date}"]


def test_lifecycle_index_rejects_outer_rehash_with_stale_producer_hash():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["source_raw_sha256"] = "c" * 64
    report["artifact_content_sha256"] = cycle._content_hash(
        report, "artifact_content_sha256"
    )

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert findings == [f"lifecycle_report_hash_invalid:{target_date}"]


def test_lifecycle_index_rejects_nonproducer_schema_even_when_rehashed():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["schema"] = "unrelated_lifecycle_shape_v1"
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert findings == [f"lifecycle_report_schema_invalid:{target_date}"]


def test_lifecycle_index_accepts_only_current_complete_raw_fid_contract():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")

    index, findings = cycle._lifecycle_index([report])

    assert findings == []
    row = index[(target_date, "trace-1")]
    assert row["broker_execution_provenance_state_counts"] == {"complete": 2}
    assert row["broker_execution_provenance_gap_count"] == 0
    assert row["runtime_authority"] is False
    assert row["order_authority"] is False
    assert row["provider_authority"] is False


def test_lifecycle_index_accepts_clean_row_and_excludes_exact_defective_window():
    target_date = "2026-08-14"
    report = _mixed_lifecycle_report(target_date)

    index, findings = cycle._lifecycle_index([report])

    assert set(index) == {(target_date, "trace-clean")}
    assert any(
        "lifecycle_row_contract_invalid:"
        f"{target_date}:{report['rows'][1]['main_lifecycle_id']}:"
        "row_promotion_gate_not_current_complete" in finding
        for finding in findings
    )
    assert not any("lifecycle_report_contract_invalid" in row for row in findings)


def test_current_paired_producer_mixed_report_keeps_only_clean_lifecycle(
    tmp_path: Path,
):
    target_date = "2026-08-14"
    cost_hash = cycle._sha256(
        {"kind": "reviewed_cost_catalog", "target_date": target_date}
    )
    symbol_hash = cycle._sha256({"kind": "symbol_master", "target_date": target_date})
    transitions = [
        *_producer_lifecycle_transitions(
            target_date=target_date,
            attempt="clean",
            namespace=1,
            include_scale_in=True,
            cost_hash=cost_hash,
            symbol_hash=symbol_hash,
        ),
        *_producer_lifecycle_transitions(
            target_date=target_date,
            attempt="excluded",
            namespace=2,
            include_scale_in=False,
            cost_hash=cost_hash,
            symbol_hash=symbol_hash,
        ),
    ]
    source = tmp_path / "main_lifecycle_transitions.jsonl"
    source.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in transitions),
        encoding="utf-8",
    )
    report = lifecycle_paired.build_daily_report(
        target_date,
        source_path=source,
        reviewed_cost_profile_sha256=cost_hash,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=symbol_hash,
        symbol_master_artifact_verified=True,
        write=False,
    )

    index, findings = cycle._lifecycle_index([report])

    assert report["global_source_quality_gate_pass"] is True
    assert report["candidate_row_gate_failure_count"] == 1
    assert report["promotion_evidence_eligible_count"] == 1
    assert {row["attempt_id"] for row in index.values()} == {"attempt-clean"}
    assert any(
        "row_promotion_gate_not_current_complete" in finding for finding in findings
    )
    assert not any("lifecycle_report_contract_invalid" in row for row in findings)

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[
            _execution_report(
                target_date,
                parent_id="parent-clean",
                trace_id="trace-clean-entry_decision-1",
                stock_code="005930",
            )
        ],
        lifecycle_reports=[report],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )
    assert rolling["joined_parent_count"] == 1
    assert rolling["status"] == "rolling_evaluated"
    assert manifest["candidate_count"] == 0


@pytest.mark.parametrize(
    ("field", "value", "finding"),
    (
        (
            "reason_codes_sha256",
            "0" * 64,
            "lifecycle_window_entry_hash_or_binding_mismatch",
        ),
        (
            "taxonomies",
            ["economic_reference_gap"],
            "lifecycle_window_entry_hash_or_binding_mismatch",
        ),
    ),
)
def test_lifecycle_index_rejects_self_rehashed_exclusion_manifest_entry_tamper(
    field: str,
    value: object,
    finding: str,
):
    target_date = "2026-08-14"
    report = _mixed_lifecycle_report(target_date)
    report["lifecycle_window_exclusion_manifest"]["entries"][0][field] = value
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(finding in row for row in findings)


def test_lifecycle_index_rejects_self_rehashed_exclusion_manifest_census_tamper():
    target_date = "2026-08-14"
    report = _mixed_lifecycle_report(target_date)
    manifest = report["lifecycle_window_exclusion_manifest"]
    manifest["excluded_lifecycle_count"] = 0
    manifest["taxonomy_counts"] = {}
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any("lifecycle_window_excluded_census_mismatch" in row for row in findings)
    assert any("lifecycle_window_taxonomy_census_mismatch" in row for row in findings)


def test_lifecycle_index_rejects_self_rehashed_legacy_row_without_raw_fids():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    row = report["rows"][0]
    for field in (
        "broker_execution_official_reference_sha",
        "broker_execution_provenance_schema",
        "broker_execution_raw_envelope_schema",
        "broker_execution_provenance_state_counts",
        "broker_execution_entry_covered_qty",
        "broker_execution_exit_covered_qty",
    ):
        row.pop(field)
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(
        "row_broker_contract_invalid:broker_execution_raw_envelope_schema" in finding
        for finding in findings
    )
    assert any(
        "row_broker_execution_provenance_census_invalid" in finding
        for finding in findings
    )


def test_lifecycle_index_rejects_self_rehashed_broker_quantity_tamper():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["rows"][0]["broker_submitted_requested_qty_by_order_no"]["1000001"] = 2
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(
        "row_broker_order_quantity_binding_invalid" in finding for finding in findings
    )


def test_lifecycle_index_rejects_self_rehashed_failed_global_gate():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["global_source_quality_gate_pass"] = False
    report["global_source_quality_gate_blockers"] = [
        "broker_execution_raw_provenance_gap"
    ]
    report["promotion_ready"] = False
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any("global_source_quality_gate_not_pass" in finding for finding in findings)
    assert any(
        "global_source_quality_gate_blockers_present" in finding for finding in findings
    )


def test_lifecycle_index_rejects_self_rehashed_authority_expansion():
    target_date = "2026-08-14"
    top_level = _lifecycle_report(target_date, trace_id="trace-top")
    top_level["provider_authority"] = True
    _seal_lifecycle_report(top_level)
    row_level = _lifecycle_report(target_date, trace_id="trace-row")
    row_level["rows"][0]["order_authority"] = True
    _seal_lifecycle_report(row_level)

    index, findings = cycle._lifecycle_index([top_level, row_level])

    assert index == {}
    assert any(
        "top_level_authority_invalid:provider_authority" in finding
        for finding in findings
    )
    assert any(
        "row_authority_invalid:order_authority" in finding for finding in findings
    )


def test_lifecycle_index_rejects_self_rehashed_lineage_mismatch():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["rows"][0]["attempt_id"] = "tampered-attempt"
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(
        "row_exact_lifecycle_identity_invalid" in finding for finding in findings
    )


def test_rolling_rejects_self_rehashed_cross_symbol_trace_binding():
    target_date = "2026-08-14"
    lifecycle = _lifecycle_report(target_date, trace_id="trace-1")
    lifecycle_row = lifecycle["rows"][0]
    lifecycle_row["stock_code"] = "000002"
    tampered_lineage = {
        "record_id": lifecycle_row["record_id"],
        "stock_code": lifecycle_row["stock_code"],
        "attempt_id": lifecycle_row["attempt_id"],
    }
    lifecycle_row["main_lifecycle_id"] = f"mlc-{cycle._sha256(tampered_lineage)[:32]}"
    lifecycle["promotion_ready_lifecycle_ids"] = [lifecycle_row["main_lifecycle_id"]]
    _seal_lifecycle_report(lifecycle)

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[
            _execution_report(
                target_date,
                parent_id="parent-1",
                trace_id="trace-1",
                stock_code="000001",
            )
        ],
        lifecycle_reports=[lifecycle],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert rolling["lifecycle_report_findings"] == []
    assert rolling["joined_parent_count"] == 0
    assert rolling["exclusions"][0]["reason"] == (
        "daily_lifecycle_identity_binding_mismatch"
    )
    assert manifest["candidate_count"] == 0


def test_lifecycle_index_bounds_contract_diagnostics(monkeypatch):
    target_date = "2026-08-14"
    reports = []
    for trace_id in ("trace-a", "trace-b"):
        report = _lifecycle_report(target_date, trace_id=trace_id)
        report["rows"][0].pop("broker_execution_raw_envelope_schema")
        report["rows"][0].pop("broker_execution_provenance_state_counts")
        reports.append(_seal_lifecycle_report(report))
    monkeypatch.setattr(cycle, "MAX_LIFECYCLE_FINDINGS", 3)

    index, findings = cycle._lifecycle_index(reports)

    assert index == {}
    assert len(findings) == 3
    assert findings[-1].startswith("lifecycle_findings_truncated:")


def test_source_quality_audit_is_a_hard_r0_gate():
    audit = {
        "target_date": "2026-08-14",
        "summary": {
            "tuning_input_allowed": False,
            "hard_blocking_contract_gap_count": 1,
            "hard_blocking_excluded_row_count": 0,
            "raw_row_exclusion_applied": False,
            "raw_row_exclusion_manifest": "",
        },
    }

    findings = cycle.validate_source_quality_audit(audit, target_date="2026-08-14")

    assert "source_quality_tuning_input_blocked" in findings
    assert "source_quality_hard_contract_gap" in findings
    assert "source_quality_row_exclusion_not_applied" in findings
    assert "source_quality_exclusion_manifest_missing" in findings


def test_clean_source_quality_audit_does_not_require_empty_exclusion_receipt():
    audit = {
        "target_date": "2026-08-14",
        "summary": {
            "tuning_input_allowed": True,
            "hard_blocking_contract_gap_count": 0,
            "hard_blocking_excluded_row_count": 0,
            "raw_row_exclusion_applied": False,
            "raw_row_exclusion_manifest": "",
        },
    }

    assert cycle.validate_source_quality_audit(audit, target_date="2026-08-14") == []


def test_rolling_rejects_daily_cost_or_symbol_binding_mismatch():
    target_date = "2026-08-14"
    lifecycle = _lifecycle_report(target_date, trace_id="trace-1")
    lifecycle["rows"][0]["reviewed_cost_profile_sha256"] = "f" * 64
    _seal_lifecycle_report(lifecycle)

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[
            _execution_report(
                target_date,
                parent_id="parent-1",
                trace_id="trace-1",
                stock_code="000001",
            )
        ],
        lifecycle_reports=[lifecycle],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert rolling["joined_parent_count"] == 0
    assert rolling["exclusions"][0]["reason"] == "lifecycle_exact_join_missing"
    assert any(
        "row_reference_hash_binding_invalid:reviewed_cost_profile_sha256" in finding
        for finding in rolling["lifecycle_report_findings"]
    )
    assert manifest["candidate_count"] == 0


def test_rolling_rejects_partial_or_unverified_provider_execution_report():
    target_date = "2026-08-14"
    execution = _execution_report(
        target_date,
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    execution["provider_call_succeeded"] = False
    execution_body = {
        key: value for key, value in execution.items() if key != "report_content_sha256"
    }
    execution["report_content_sha256"] = cycle._sha256(execution_body)

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[execution],
        lifecycle_reports=[_lifecycle_report(target_date, trace_id="trace-1")],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert rolling["joined_parent_count"] == 0
    assert rolling["exclusions"][0]["reason"] == (
        "execution_report_not_complete_provider_verified"
    )
    assert manifest["candidate_count"] == 0


@pytest.mark.parametrize(
    "mutation",
    ("missing", "malformed", "extra"),
)
def test_historical_execution_rejects_self_rehashed_result_row_census(mutation):
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    if mutation == "missing":
        report["results"].pop()
        report["result_ids"] = [row["result_id"] for row in report["results"]]
        report["new_result_ids"] = list(report["result_ids"])
        report["result_count"] = len(report["results"])
        report["new_result_count"] = len(report["results"])
        report["selected_request_ids"] = [
            row["paired_replay_id"] for row in report["results"]
        ]
        report["provider_provenance_pass_count"] = len(report["results"])
    elif mutation == "malformed":
        report["results"][1] = "not-an-object"
    else:
        report["results"].append(deepcopy(report["results"][0]))
        report["result_ids"].append(report["results"][-1]["result_id"])
        report["new_result_ids"].append(report["results"][-1]["result_id"])
        report["result_count"] = len(report["results"])
        report["new_result_count"] = len(report["results"])
        report["selected_request_ids"].append(report["results"][-1]["paired_replay_id"])
        report["provider_provenance_pass_count"] = len(report["results"])
    _reseal_execution_report(report)

    with pytest.raises(ValueError):
        cycle._validated_execution_rows(report)


@pytest.mark.parametrize(
    "mutation",
    ("missing", "malformed", "extra", "arm_incomplete"),
)
def test_historical_execution_rejects_self_rehashed_evaluation_subset(mutation):
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    evaluation = report["three_arm_evaluation"]
    if mutation == "missing":
        evaluation["rows"] = []
        evaluation["complete_parent_count"] = 0
        evaluation["sample_floor"]["observed_rows"] = 0
        for metrics in evaluation["arm_metrics"].values():
            metrics["row_count"] = 0
        evaluation["stage_venue_partitions"] = []
    elif mutation == "malformed":
        evaluation["rows"][0] = "not-an-object"
    elif mutation == "extra":
        extra = deepcopy(evaluation["rows"][0])
        extra["paired_replay_parent_id"] = "invented-parent"
        evaluation["rows"].append(extra)
        evaluation["complete_parent_count"] = 2
        evaluation["sample_floor"]["observed_rows"] = 2
        for metrics in evaluation["arm_metrics"].values():
            metrics["row_count"] = 2
        for metrics in evaluation["stage_venue_partitions"][0]["arm_metrics"].values():
            metrics["row_count"] = 2
        evaluation["stage_venue_partitions"][0]["complete_parent_count"] = 2
    else:
        evaluation["rows"][0]["arms"].pop("replay_control_exact_no_micro")
    _reseal_execution_report(report)

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date="2026-08-14",
        execution_reports=[report],
        lifecycle_reports=[_lifecycle_report("2026-08-14", trace_id="trace-1")],
        source_quality_pass_by_date={"2026-08-14": True},
        economic_reference_pass_by_date={"2026-08-14": True},
    )

    assert rolling["joined_parent_count"] == 0
    assert rolling["excluded_parent_count"] == 1
    assert rolling["exclusions"][0]["reason"].startswith(
        "execution_report_exact_census_invalid:"
    )
    assert manifest["candidate_count"] == 0


@pytest.mark.parametrize("mutation", ("result_action", "evaluation_ev"))
def test_historical_execution_rejects_self_rehashed_result_evaluation_divergence(
    mutation,
):
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    candidate_result = report["results"][-1]
    if mutation == "result_action":
        candidate_result["replay_result"]["candidate_response"]["action"] = "WAIT"
        candidate_result["candidate_response_content_sha256"] = cycle._sha256(
            candidate_result["replay_result"]["candidate_response"]
        )
        old_result_id = candidate_result["result_id"]
        candidate_result["result_id"] = (
            "micro-result-"
            + cycle._sha256(
                {
                    key: value
                    for key, value in candidate_result.items()
                    if key != "result_id"
                }
            )[:24]
        )
        report["result_ids"] = [
            candidate_result["result_id"] if value == old_result_id else value
            for value in report["result_ids"]
        ]
        report["new_result_ids"] = [
            candidate_result["result_id"] if value == old_result_id else value
            for value in report["new_result_ids"]
        ]
    else:
        report["three_arm_evaluation"]["rows"][0]["arms"][
            "replay_candidate_exact_plus_micro"
        ]["source_quality_adjusted_ev_pct"] = 999.0
    _reseal_execution_report(report)

    with pytest.raises(
        ValueError,
        match="execution_report_exact_census_invalid:"
        "evaluation_result_semantic_binding_invalid",
    ):
        cycle._validated_execution_rows(report)


@pytest.mark.parametrize(
    "field,value",
    (
        ("request_refs", []),
        ("checkpoint_resume_result_count", 1),
        ("provisional_checkpoint_result_count", 1),
        ("reused_result_count", 1),
        ("deferred_request_ids", ["invented-request"]),
        ("execution_exclusion_count", 1),
    ),
)
def test_historical_execution_rejects_self_rehashed_receipt_census(field, value):
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    report[field] = value
    _reseal_execution_report(report)

    with pytest.raises(ValueError):
        cycle._validated_execution_rows(report)


@pytest.mark.parametrize(
    "mutation",
    (
        "zero_request_bound",
        "provider_response_census",
        "outcome_embedding_authority",
        "execution_order_authority",
        "provider_attempt_hash",
        "provider_cost_underreported",
        "provider_budget_authority",
        "evaluation_runtime_authority",
        "outcome_identity",
        "outcome_join_authority",
        "partition_count",
    ),
)
def test_historical_execution_rejects_self_rehashed_provider_and_join_receipts(
    mutation,
):
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    if mutation == "zero_request_bound":
        report["max_new_requests"] = 0
    elif mutation == "provider_response_census":
        report["provider_response_hash_observed"] = False
    elif mutation == "outcome_embedding_authority":
        report["outcomes_embedded_in_provider_input"] = True
    elif mutation == "execution_order_authority":
        report["order_authority"] = True
    elif mutation == "provider_attempt_hash":
        report["results"][0]["replay_result"]["candidate_attempts"][0][
            "provider_provenance"
        ]["provider_budget_attempt_identity_sha256"] = ("x" * 64)
        _reseal_execution_result_ids(report)
    elif mutation == "provider_cost_underreported":
        report["provider_budget"]["committed_cost_usd"] = "0.01"
        report["provider_budget"]["summary_content_sha256"] = cycle._content_hash(
            report["provider_budget"], "summary_content_sha256"
        )
    elif mutation == "provider_budget_authority":
        report["provider_budget"]["allowed_runtime_apply"] = True
        report["provider_budget"]["summary_content_sha256"] = cycle._content_hash(
            report["provider_budget"], "summary_content_sha256"
        )
    elif mutation == "evaluation_runtime_authority":
        report["three_arm_evaluation"]["allowed_runtime_apply"] = True
    elif mutation == "outcome_identity":
        report["outcome_joins"][0]["effective_venue"] = "NXT"
    elif mutation == "outcome_join_authority":
        report["outcome_joins"][0]["outcome_embedded_in_provider_input"] = True
    else:
        report["three_arm_evaluation"]["stage_venue_partitions"][0][
            "complete_parent_count"
        ] = 2
        for metrics in report["three_arm_evaluation"]["stage_venue_partitions"][0][
            "arm_metrics"
        ].values():
            metrics["row_count"] = 2
    _reseal_execution_report(report)

    with pytest.raises(ValueError):
        cycle._validated_execution_rows(report)


def test_historical_execution_accepts_partial_checkpoint_parent_after_exact_commit():
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    new_result = report["results"][-1]
    report.update(
        {
            "new_result_count": 1,
            "new_result_ids": [new_result["result_id"]],
            "checkpoint_resume_result_count": 2,
            "provisional_checkpoint_result_count": 2,
            "reused_result_count": 0,
            "newly_committed_parent_count": 1,
            "selected_parent_ids": ["parent-1"],
            "selected_request_ids": [new_result["paired_replay_id"]],
        }
    )
    _reseal_execution_report(report)

    rows = cycle._validated_execution_rows(report)

    assert len(rows) == 1
    assert rows[0]["paired_replay_parent_id"] == "parent-1"


def test_collect_rolling_inputs_rejects_path_date_mismatch(tmp_path, monkeypatch):
    target_date = "2026-08-14"
    execution_root = tmp_path / "execution"
    execution_root.mkdir()
    misdated_path = execution_root / f"execution_{target_date}.json"
    misdated_path.write_text(
        json.dumps(
            _execution_report(
                "2026-08-13",
                parent_id="stale-parent",
                trace_id="stale-trace",
                stock_code="000001",
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda date_key: execution_root / f"execution_{date_key}.json",
    )
    monkeypatch.setattr(cycle, "LIFECYCLE_REPORT_ROOT", tmp_path / "lifecycle")
    monkeypatch.setattr(cycle, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(cycle, "ECONOMIC_REPORT_ROOT", tmp_path / "economic")

    execution, lifecycle, source_pass, economic_pass, diagnostics = (
        cycle._collect_rolling_inputs(
            target_date=target_date,
            lookback_calendar_days=1,
        )
    )

    assert execution == []
    assert lifecycle == []
    assert source_pass == {}
    assert economic_pass == {}
    assert diagnostics == [
        {
            "target_date": target_date,
            "artifact": "execution",
            "status": "invalid",
            "reason": "artifact_target_date_path_mismatch",
            "embedded_target_date": "2026-08-13",
        }
    ]


def test_validated_execution_rows_accepts_one_complete_bounded_parent():
    target_date = "2026-08-14"
    report = _execution_report(
        target_date,
        parent_id="supported-parent",
        trace_id="supported-trace",
        stock_code="000001",
    )
    deferred_exclusions = [
        {
            "paired_replay_parent_id": "unsupported-parent",
            "paired_replay_id": f"unsupported-{arm}",
            "micro_reversion_replay_arm": arm,
            "stage": "holding",
            "provider": "bedrock",
            "model": "nova_lite_v2",
            "reason": "bedrock_holding_flow_offline_executor_not_implemented",
        }
        for arm in cycle.EXPECTED_ARMS
    ]
    deferred_refs = [
        {
            "paired_replay_parent_id": "unsupported-parent",
            "paired_replay_id": f"unsupported-{arm}",
            "micro_reversion_replay_arm": arm,
            "decision_trace_id": "unsupported-trace",
            "candidate_input_sha256": cycle._sha256(
                {"arm": arm, "kind": "deferred-input"}
            ),
            "prompt_sha256": cycle._sha256({"arm": arm, "kind": "deferred-prompt"}),
            "prompt_contract_sha256": cycle._sha256(
                {"arm": arm, "kind": "deferred-contract"}
            ),
        }
        for arm in cycle.EXPECTED_ARMS
    ]
    report.update(
        {
            "status": "offline_three_arm_execution_batch_complete",
            "request_count": 6,
            "parent_count": 2,
            "request_refs": [*report["request_refs"], *deferred_refs],
            "deferred_request_count": 3,
            "deferred_request_ids": [row["paired_replay_id"] for row in deferred_refs],
            "execution_exclusion_count": 3,
            "execution_exclusions": deferred_exclusions,
            "blocking_execution_exclusion_count": 0,
            "blocking_execution_exclusions": [],
            "newly_committed_parent_count": 1,
        }
    )
    report["report_content_sha256"] = cycle._content_hash(
        report, "report_content_sha256"
    )

    rows = cycle._validated_execution_rows(report)

    assert len(rows) == 1
    assert rows[0]["paired_replay_parent_id"] == "supported-parent"


def test_current_cycle_rejects_stale_same_date_execution_materialization_binding():
    target_date = "2026-08-14"
    stale_execution = _execution_report(
        target_date,
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )

    with pytest.raises(
        ValueError,
        match="current_execution_materialized_hash_mismatch",
    ):
        cycle._validate_current_execution_artifact(
            report=stale_execution,
            target_date=target_date,
            materialized_report={"report_content_sha256": "f" * 64},
            outcome_label_artifact={},
            expected_max_new_requests=3,
            expected_daily_attempt_cap=12,
            expected_daily_usd_cap=1.0,
            expected_pricing_content_sha256="e" * 64,
        )


def test_current_cycle_rejects_provider_budget_breaker_before_r2():
    target_date = "2026-08-14"
    materialized = {"report_content_sha256": "f" * 64}
    outcome_artifact: dict = {}
    budget_body = {
        "daily_attempt_cap": 12,
        "daily_usd_cap": "1.0",
        "committed_cost_usd": "1.00000001",
        "circuit_breaker_open": True,
        "pricing_artifact_content_sha256": "e" * 64,
    }
    report = {
        "target_date": target_date,
        "materialized_report_content_sha256": materialized["report_content_sha256"],
        "materialized_request_census_sha256": (
            quality._micro_reversion_materialized_request_census_sha256(materialized)
        ),
        "outcome_label_artifact_sha256": cycle._sha256(outcome_artifact),
        "max_new_requests": 3,
        "provider_budget": {
            **budget_body,
            "summary_content_sha256": cycle._sha256(budget_body),
        },
    }

    with pytest.raises(
        ValueError,
        match="current_execution_provider_budget_breached",
    ):
        cycle._validate_current_execution_artifact(
            report=report,
            target_date=target_date,
            materialized_report=materialized,
            outcome_label_artifact=outcome_artifact,
            expected_max_new_requests=3,
            expected_daily_attempt_cap=12,
            expected_daily_usd_cap=Decimal("1.0"),
            expected_pricing_content_sha256="e" * 64,
        )


def test_execution_consumer_recomputes_reservation_settlement_provenance():
    report = _execution_report(
        "2026-08-14",
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    provenance = report["results"][0]["replay_result"]["candidate_attempts"][0][
        "provider_provenance"
    ]
    provenance["provider_budget_settled"] = False
    report["report_content_sha256"] = cycle._content_hash(
        report, "report_content_sha256"
    )

    with pytest.raises(ValueError, match="execution_report_provider_budget_invalid"):
        cycle._validated_execution_rows(report)


def test_current_cycle_rejects_stale_execution_invocation_request_bound():
    target_date = "2026-08-14"
    stale_execution = _execution_report(
        target_date,
        parent_id="parent-1",
        trace_id="trace-1",
        stock_code="000001",
    )
    materialized_hash = "f" * 64
    outcome_artifact: dict = {}
    stale_execution["materialized_report_content_sha256"] = materialized_hash
    stale_execution["materialized_request_census_sha256"] = (
        quality._micro_reversion_materialized_request_census_sha256(
            {"report_content_sha256": materialized_hash}
        )
    )
    stale_execution["outcome_label_artifact_sha256"] = cycle._sha256(outcome_artifact)
    stale_execution["max_new_requests"] = 6

    with pytest.raises(
        ValueError,
        match="current_execution_request_bound_mismatch",
    ):
        cycle._validate_current_execution_artifact(
            report=stale_execution,
            target_date=target_date,
            materialized_report={"report_content_sha256": materialized_hash},
            outcome_label_artifact=outcome_artifact,
            expected_max_new_requests=3,
            expected_daily_attempt_cap=12,
            expected_daily_usd_cap=1.0,
            expected_pricing_content_sha256="e" * 64,
        )


def _bind_current_execution_validation_fixture(
    *, report: dict, requests: list[dict], outcome_artifact: dict
) -> tuple[dict, str]:
    pricing_hash = "e" * 64
    materialized = {
        "schema": quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA,
        "target_date": report["target_date"],
        "request_count": len(requests),
        "request_ids": [row["paired_replay_id"] for row in requests],
        "requests": requests,
    }
    materialized["report_content_sha256"] = cycle._content_hash(
        materialized, "report_content_sha256"
    )
    budget_body = {
        "schema": cycle.BUDGET_SUMMARY_SCHEMA,
        "daily_attempt_cap": 12,
        "daily_usd_cap": "1.000000006",
        "committed_cost_usd": "0.5",
        "circuit_breaker_open": False,
        "reservation_count": len(report["results"]),
        "pricing_artifact_content_sha256": pricing_hash,
        **cycle.PROVIDER_BUDGET_AUTHORITY_CONTRACT,
    }
    report.update(
        {
            "materialized_report_content_sha256": materialized["report_content_sha256"],
            "materialized_request_census_sha256": (
                quality._micro_reversion_materialized_request_census_sha256(
                    materialized
                )
            ),
            "outcome_label_artifact_sha256": cycle._sha256(outcome_artifact),
            "max_new_requests": 3,
            "provider_budget": {
                **budget_body,
                "summary_content_sha256": cycle._sha256(budget_body),
            },
        }
    )
    report["report_content_sha256"] = cycle._content_hash(
        report, "report_content_sha256"
    )
    return materialized, pricing_hash


def test_current_cycle_accepts_exact_one_parent_bounded_batch(monkeypatch):
    target_date = "2026-08-14"
    supported_parent_id = "supported-parent"
    report = _execution_report(
        target_date,
        parent_id=supported_parent_id,
        trace_id="supported-trace",
        stock_code="000001",
    )
    supported_requests = [
        {
            "paired_replay_parent_id": supported_parent_id,
            "paired_replay_id": result["paired_replay_id"],
            "micro_reversion_replay_arm": result["micro_reversion_replay_arm"],
            "stage": "entry",
            "candidate": {"provider": "openai", "model": "gpt-test"},
        }
        for result in report["results"]
    ]
    unsupported_parent_id = "unsupported-parent"
    unsupported_requests = [
        {
            "paired_replay_parent_id": unsupported_parent_id,
            "paired_replay_id": f"unsupported-{arm}",
            "micro_reversion_replay_arm": arm,
            "stage": "holding",
            "endpoint": "holding_flow",
            "candidate": {"provider": "bedrock", "model": "nova_lite_v2"},
        }
        for arm in cycle.EXPECTED_ARMS
    ]
    requests = [*supported_requests, *unsupported_requests]
    execution_exclusions = [
        {
            "paired_replay_parent_id": request["paired_replay_parent_id"],
            "paired_replay_id": request["paired_replay_id"],
            "micro_reversion_replay_arm": request["micro_reversion_replay_arm"],
            "stage": request["stage"],
            "provider": request["candidate"]["provider"],
            "model": request["candidate"]["model"],
            "reason": "bedrock_holding_flow_offline_executor_not_implemented",
        }
        for request in unsupported_requests
    ]
    unsupported_refs = [
        {
            "paired_replay_parent_id": request["paired_replay_parent_id"],
            "paired_replay_id": request["paired_replay_id"],
            "micro_reversion_replay_arm": request["micro_reversion_replay_arm"],
            "decision_trace_id": "unsupported-trace",
            "candidate_input_sha256": cycle._sha256(
                {"request_id": request["paired_replay_id"], "kind": "input"}
            ),
            "prompt_sha256": cycle._sha256(
                {"request_id": request["paired_replay_id"], "kind": "prompt"}
            ),
            "prompt_contract_sha256": cycle._sha256(
                {"request_id": request["paired_replay_id"], "kind": "contract"}
            ),
        }
        for request in unsupported_requests
    ]
    report.update(
        {
            "status": "offline_three_arm_execution_batch_complete",
            "request_count": 6,
            "parent_count": 2,
            "request_refs": [*report["request_refs"], *unsupported_refs],
            "execution_exclusion_count": 3,
            "execution_exclusions": execution_exclusions,
            "blocking_execution_exclusion_count": 0,
            "blocking_execution_exclusions": [],
            "deferred_request_count": 3,
            "deferred_request_ids": [
                request["paired_replay_id"] for request in unsupported_requests
            ],
            "selected_parent_ids": [supported_parent_id],
            "selected_request_ids": [
                request["paired_replay_id"] for request in supported_requests
            ],
        }
    )
    outcome_artifact: dict = {}
    materialized, pricing_hash = _bind_current_execution_validation_fixture(
        report=report,
        requests=requests,
        outcome_artifact=outcome_artifact,
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda _artifact: requests,
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_outcome_label_artifact",
        lambda _artifact: None,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_reusable_results",
        lambda **_kwargs: report["results"],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_complete_parent_ids",
        lambda **_kwargs: {supported_parent_id},
    )

    rows = cycle._validate_current_execution_artifact(
        report=report,
        target_date=target_date,
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        expected_max_new_requests=3,
        expected_daily_attempt_cap=12,
        expected_daily_usd_cap=Decimal("1.000000006"),
        expected_pricing_content_sha256=pricing_hash,
    )

    assert len(rows) == 1
    assert rows[0]["paired_replay_parent_id"] == supported_parent_id

    report.update(
        {
            "newly_committed_parent_count": 0,
            "new_result_count": 0,
            "new_result_ids": [],
            "reused_result_count": 3,
            "checkpoint_resume_result_count": 3,
            "selected_parent_ids": [],
            "selected_request_ids": [],
            "candidate_model_call_attempted": False,
        }
    )
    report["report_content_sha256"] = cycle._content_hash(
        report, "report_content_sha256"
    )

    reused_rows = cycle._validate_current_execution_artifact(
        report=report,
        target_date=target_date,
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        expected_max_new_requests=3,
        expected_daily_attempt_cap=12,
        expected_daily_usd_cap=Decimal("1.000000006"),
        expected_pricing_content_sha256=pricing_hash,
    )

    assert len(reused_rows) == 1


def test_current_cycle_recomputes_blocking_exclusion_census(monkeypatch):
    target_date = "2026-08-14"
    parent_id = "committed-parent"
    report = _execution_report(
        target_date,
        parent_id=parent_id,
        trace_id="trace-1",
        stock_code="000001",
    )
    requests = [
        {
            "paired_replay_parent_id": parent_id,
            "paired_replay_id": result["paired_replay_id"],
            "micro_reversion_replay_arm": result["micro_reversion_replay_arm"],
            "stage": "entry",
            "candidate": {
                "provider": "unsupported_offline_provider",
                "model": "unsupported-model",
            },
        }
        for result in report["results"]
    ]
    expected_exclusions = [
        {
            "paired_replay_parent_id": request["paired_replay_parent_id"],
            "paired_replay_id": request["paired_replay_id"],
            "micro_reversion_replay_arm": request["micro_reversion_replay_arm"],
            "stage": request["stage"],
            "provider": request["candidate"]["provider"],
            "model": request["candidate"]["model"],
            "reason": "offline_provider_stage_executor_not_supported",
        }
        for request in requests
    ]
    report.update(
        {
            "execution_exclusion_count": 3,
            "execution_exclusions": expected_exclusions,
            # Tamper: a self-rehashed producer receipt hides committed-parent
            # exclusions from its blocking subset.
            "blocking_execution_exclusion_count": 0,
            "blocking_execution_exclusions": [],
        }
    )
    outcome_artifact: dict = {}
    materialized, pricing_hash = _bind_current_execution_validation_fixture(
        report=report,
        requests=requests,
        outcome_artifact=outcome_artifact,
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda _artifact: requests,
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_outcome_label_artifact",
        lambda _artifact: None,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_reusable_results",
        lambda **_kwargs: report["results"],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_complete_parent_ids",
        lambda **_kwargs: {parent_id},
    )

    with pytest.raises(
        ValueError,
        match="current_execution_blocking_exclusion_census_mismatch",
    ):
        cycle._validate_current_execution_artifact(
            report=report,
            target_date=target_date,
            materialized_report=materialized,
            outcome_label_artifact=outcome_artifact,
            expected_max_new_requests=3,
            expected_daily_attempt_cap=12,
            expected_daily_usd_cap=Decimal("1.000000006"),
            expected_pricing_content_sha256=pricing_hash,
        )


def test_current_cycle_recomputes_exact_deferred_request_census(monkeypatch):
    target_date = "2026-08-14"
    parent_id = "committed-parent"
    report = _execution_report(
        target_date,
        parent_id=parent_id,
        trace_id="trace-1",
        stock_code="000001",
    )
    requests = [
        {
            "paired_replay_parent_id": parent_id,
            "paired_replay_id": result["paired_replay_id"],
            "micro_reversion_replay_arm": result["micro_reversion_replay_arm"],
            "stage": "entry",
            "candidate": {"provider": "openai", "model": "gpt-test"},
        }
        for result in report["results"]
    ]
    report["deferred_request_count"] = 1
    report["deferred_request_ids"] = [requests[0]["paired_replay_id"]]
    outcome_artifact: dict = {}
    materialized, pricing_hash = _bind_current_execution_validation_fixture(
        report=report,
        requests=requests,
        outcome_artifact=outcome_artifact,
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda _artifact: requests,
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_outcome_label_artifact",
        lambda _artifact: None,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_reusable_results",
        lambda **_kwargs: report["results"],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_complete_parent_ids",
        lambda **_kwargs: {parent_id},
    )

    with pytest.raises(
        ValueError,
        match="current_execution_deferred_request_census_mismatch",
    ):
        cycle._validate_current_execution_artifact(
            report=report,
            target_date=target_date,
            materialized_report=materialized,
            outcome_label_artifact=outcome_artifact,
            expected_max_new_requests=3,
            expected_daily_attempt_cap=12,
            expected_daily_usd_cap=Decimal("1.000000006"),
            expected_pricing_content_sha256=pricing_hash,
        )


def test_cycle_does_not_claim_or_roll_same_date_stale_execution_when_step_skips(
    tmp_path,
    monkeypatch,
):
    target_date = "2026-08-14"
    audit_path = tmp_path / "source-audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "target_date": target_date,
                "summary": {
                    "tuning_input_allowed": True,
                    "hard_blocking_contract_gap_count": 0,
                    "hard_blocking_excluded_row_count": 0,
                    "raw_row_exclusion_applied": False,
                    "raw_row_exclusion_manifest": "",
                },
            }
        ),
        encoding="utf-8",
    )
    stale_execution = _execution_report(
        target_date,
        parent_id="stale-parent",
        trace_id="stale-trace",
        stock_code="000001",
    )
    stale_path = tmp_path / "execution.json"
    stale_path.write_text(json.dumps(stale_execution), encoding="utf-8")

    monkeypatch.setattr(
        cycle,
        "_collect_rolling_inputs",
        lambda **_kwargs: ([stale_execution], [], {}, {}, []),
    )
    monkeypatch.setattr(
        cycle,
        "rolling_report_path",
        lambda _target_date: tmp_path / "rolling.json",
    )
    monkeypatch.setattr(
        cycle,
        "r3_manifest_path",
        lambda _target_date: tmp_path / "r3.json",
    )
    monkeypatch.setattr(
        cycle,
        "cycle_report_path",
        lambda _target_date: tmp_path / "cycle.json",
    )

    report = cycle.run_cycle(
        target_date=target_date,
        write=True,
        execute_provider_replay=True,
        daily_attempt_cap=12,
        daily_usd_cap=1.0,
        parent_cap=1,
        paths={
            "source_audit": audit_path,
            "economic_reference": tmp_path / "missing-economic.json",
            "execution": stale_path,
        },
        command_runner=lambda _command: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="expected test failure",
        ),
    )

    assert report["current_provider_replay_complete"] is False
    assert report["provider_call_performed"] is False
    assert report["rolling_status"] == "no_joined_lifecycle_rows"
    assert report["status"] == "source_only_blocked_or_deferred"


def test_current_run_excludes_stale_same_date_lifecycle_after_producer_failure():
    target_date = "2026-08-14"
    current_execution = _execution_report(
        target_date,
        parent_id="current-parent",
        trace_id="current-trace",
        stock_code="000001",
    )
    stale_lifecycle = _lifecycle_report(
        target_date,
        trace_id="current-trace",
    )

    execution, lifecycle = cycle._bind_current_run_rolling_inputs(
        target_date=target_date,
        execution_reports=[current_execution],
        lifecycle_reports=[stale_lifecycle],
        current_execution_report=current_execution,
        current_provider_replay_complete=True,
        current_lifecycle_producer_complete=False,
    )

    assert execution == [current_execution]
    assert lifecycle == []


def test_cycle_cli_returns_nonzero_for_terminal_blocked_artifact(monkeypatch, capsys):
    blocked = {
        "schema": cycle.CYCLE_SCHEMA,
        "target_date": "2026-08-14",
        "status": "source_only_blocked_or_deferred",
        "blockers": ["economic_reference_not_verified"],
        **cycle.OFFLINE_AUTHORITY,
    }
    observed: dict[str, object] = {}

    def fake_run_cycle(**kwargs):
        observed.update(kwargs)
        return blocked

    monkeypatch.setattr(cycle, "run_cycle", fake_run_cycle)

    assert cycle.main(["--date", "2026-08-14", "--write"]) == 2
    assert observed["daily_attempt_cap"] == cycle.DEFAULT_DAILY_ATTEMPT_CAP == 96
    assert observed["parent_cap"] == cycle.DEFAULT_PARENT_CAP == 8
    assert "economic_reference_not_verified" in capsys.readouterr().out
