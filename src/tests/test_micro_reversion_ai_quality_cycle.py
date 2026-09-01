from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
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
from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge


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


def _current_prepared_artifact(trace_id: str = "trace-current") -> dict:
    request = {
        **_paired_request(trace_id),
        "decision_ts": "2026-08-25T09:00:00+09:00",
    }
    paired = {
        "schema": quality.PAIRED_SCHEMA,
        "target_date": "2026-08-25",
        "requests": [request],
        "request_count": 1,
        "result_count": 0,
        "status": "paired_replay_requests_ready_candidate_not_executed",
        "candidate_execution_performed": False,
        "prepared_request_exclusions": [],
        "prepared_request_exclusion_count": 0,
        "sample_floor_excluded_request_count": 0,
        "prepared_request_count": 1,
        **cycle.OFFLINE_AUTHORITY,
    }
    return cycle.build_prepared_request_artifact(
        target_date="2026-08-25",
        paired_report=paired,
        source={
            "logical_content_sha256": cycle._sha256(paired),
            "resolved_path": "/tmp/paired.json",
            "stored_sha256": "d" * 64,
        },
    )


def test_scheduled_bridge_prepared_trace_filter_is_exact_and_cycle_passes_binding(
    tmp_path: Path,
) -> None:
    artifact = _current_prepared_artifact()
    trace = {
        "decision_trace_id": "trace-current",
        "decision_ts": "2026-08-25T09:00:01+09:00",
    }
    broad_only = {
        "decision_trace_id": "trace-broad-only",
        "decision_ts": "2026-08-25T09:00:02+09:00",
    }

    selected, census = bridge._validated_scheduled_prepared_trace_census(
        target_date="2026-08-25",
        prepared_artifact=artifact,
        expected_artifact_sha256=cycle._sha256(artifact),
        expected_request_count=1,
        traces=[broad_only, trace],
    )

    assert selected == [trace]
    assert census["prepared_request_count"] == 1
    assert census["exact_trace_census"] is True
    paths = {
        "cost_profile": tmp_path / "cost.json",
        "symbol_master": tmp_path / "symbols.json",
        "capacity_status": tmp_path / "capacity.json",
        "prepared": tmp_path / "prepared.json",
    }
    command = cycle._scheduled_bridge_command(
        target_date="2026-08-25",
        selected_paths=paths,
        prepared_artifact=artifact,
        write=True,
    )
    assert command[command.index("--prepared-requests") + 1] == str(paths["prepared"])
    assert command[command.index("--prepared-artifact-sha256") + 1] == cycle._sha256(
        artifact
    )
    assert command[command.index("--prepared-request-count") + 1] == "1"
    assert command[-1] == "--write"
    bridge_report = {
        "report_row_count": 1,
        "rows": [{"decision_trace_id": "trace-current"}],
        "scheduled_prepared_trace_census": {
            **census,
            "bridge_joined_trace_count": 1,
            "bridge_joined_trace_ids_sha256": quality._sha256(["trace-current"]),
            "bridge_unjoined_trace_count": 0,
        },
    }
    quality._validate_scheduled_bridge_prepared_trace_census(
        bridge_report,
        target_date="2026-08-25",
        prepared_requests=artifact["prepared_requests"],
        expected_prepared_artifact_sha256=cycle._sha256(artifact),
    )
    bridge_report["scheduled_prepared_trace_census"][
        "broad_manual_trace_corpus_used"
    ] = True
    with pytest.raises(
        ValueError, match="micro_reversion_scheduled_bridge_census_invalid"
    ):
        quality._validate_scheduled_bridge_prepared_trace_census(
            bridge_report,
            target_date="2026-08-25",
            prepared_requests=artifact["prepared_requests"],
            expected_prepared_artifact_sha256=cycle._sha256(artifact),
        )


@pytest.mark.parametrize(
    ("failure", "match"),
    [
        ("tamper", "prepared_artifact_outer_sha256_mismatch"),
        ("date", "prepared_trace_target_date_mismatch"),
        ("missing", "prepared_trace_census_missing_or_duplicated"),
        ("duplicate", "prepared_trace_census_missing_or_duplicated"),
        ("count", "prepared_request_census_mismatch"),
    ],
)
def test_scheduled_bridge_prepared_trace_binding_fails_closed(
    failure: str, match: str
) -> None:
    artifact = _current_prepared_artifact()
    trace = {
        "decision_trace_id": "trace-current",
        "decision_ts": "2026-08-25T09:00:01+09:00",
    }
    expected_hash = cycle._sha256(artifact)
    expected_count = 1
    traces = [trace]
    if failure == "tamper":
        expected_hash = "0" * 64
    elif failure == "date":
        traces = [{**trace, "decision_ts": "2026-08-24T09:00:01+09:00"}]
    elif failure == "missing":
        traces = []
    elif failure == "duplicate":
        traces = [trace, deepcopy(trace)]
    else:
        expected_count = 2

    with pytest.raises(ValueError, match=match):
        bridge._validated_scheduled_prepared_trace_census(
            target_date="2026-08-25",
            prepared_artifact=artifact,
            expected_artifact_sha256=expected_hash,
            expected_request_count=expected_count,
            traces=traces,
        )


def test_daily_usd_cap_preserves_exact_decimal_for_command_and_validator():
    canonical, command_text = cycle._canonical_daily_usd_cap("1.000000006")

    assert canonical == Decimal("1.000000006")
    assert command_text == "1.000000006"


def test_raw_artifact_binds_one_generation_and_prefers_equal_plain_copy(tmp_path):
    path = tmp_path / "artifact.json"
    payload = {"schema": "test", "generation": 1}
    encoded = json.dumps(payload).encode("utf-8")
    path.write_bytes(encoded)
    path.with_name(path.name + ".gz").write_bytes(gzip.compress(encoded))

    provenance = cycle._raw_artifact(path)

    assert provenance["resolved_path"] == str(path)
    assert provenance["compression"] == "plain"
    assert provenance["stored_sha256"] == hashlib.sha256(encoded).hexdigest()
    assert provenance["stored_size_bytes"] == len(encoded)
    assert provenance["logical_content_sha256"] == cycle._sha256(payload)


def test_raw_artifact_rejects_generation_swap_between_validation_and_provenance(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps({"generation": 1}), encoding="utf-8")
    original_reader = cycle.read_json_object_strict
    call_count = 0

    def swapping_reader(candidate):
        nonlocal call_count
        value = original_reader(candidate)
        call_count += 1
        if call_count == 1:
            path.write_text(json.dumps({"generation": 2}), encoding="utf-8")
        return value

    monkeypatch.setattr(cycle, "read_json_object_strict", swapping_reader)

    with pytest.raises(ValueError, match="json_artifact_generation_mismatch"):
        cycle._raw_artifact(path)


def test_raw_artifact_rejects_generation_switch_after_earlier_payload_load(tmp_path):
    path = tmp_path / "artifact.json"
    first = {"generation": 1}
    second = {"generation": 2}
    path.write_text(json.dumps(first), encoding="utf-8")
    earlier_payload = cycle._load_json_auto(path)
    path.write_text(json.dumps(second), encoding="utf-8")

    with pytest.raises(ValueError, match="json_artifact_generation_mismatch"):
        cycle._raw_artifact(path, expected_payload=earlier_payload)

    loaded, provenance = cycle._load_json_with_raw_artifact(path)
    assert loaded == second
    assert provenance["logical_content_sha256"] == cycle._sha256(second)


def test_cycle_atomic_writer_delegates_preserving_canonical_format(monkeypatch):
    observed = {}

    def capture(path, value, **options):
        observed.update({"path": path, "value": value, **options})

    monkeypatch.setattr(cycle, "write_json_object_generation_safe", capture)
    cycle._atomic_write_json(Path("report.json"), {"b": 2, "a": 1})

    assert observed == {
        "path": Path("report.json"),
        "value": {"b": 2, "a": 1},
        "ensure_ascii": False,
        "indent": 2,
        "sort_keys": True,
        "trailing_newline": True,
    }


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


def _replace_evaluation_with_parent_local_exclusion(
    report: dict,
    *,
    parent_id: str,
    arm: str,
    action: str,
) -> None:
    exclusion = {
        "paired_replay_parent_id": parent_id,
        "reason": "unsupported_economic_exposure",
        "unsupported_arm_actions": [
            {
                "arm": arm,
                "action": action,
                "exposure_role": "economic_exposure_not_applicable",
            }
        ],
    }
    evaluation_without_hash = {
        "schema": "ai_micro_reversion_three_arm_evaluation_v1",
        "status": "no_comparable_economic_parents",
        "complete_parent_count": 0,
        "excluded_parent_count": 1,
        "exclusions": [exclusion],
        "sample_floor": {"observed_rows": 0},
        "arm_metrics": {arm_name: {"row_count": 0} for arm_name in cycle.EXPECTED_ARMS},
        "stage_venue_partitions": [],
        "rows": [],
        **cycle.OFFLINE_AUTHORITY,
    }
    report["three_arm_evaluation"] = {
        **evaluation_without_hash,
        "evaluation_content_sha256": cycle._sha256(evaluation_without_hash),
    }
    _reseal_execution_report(report)


def test_trim_parent_is_locally_excluded_without_rolling_artifact_poisoning():
    target_date = "2026-08-24"
    parent_id = "holding-trim-parent"
    report = _execution_report(
        target_date,
        parent_id=parent_id,
        trace_id="holding-trim-trace",
        stock_code="000001",
    )
    trim_arm = cycle.EXPECTED_ARMS[0]
    for result in report["results"]:
        action = "TRIM" if result["micro_reversion_replay_arm"] == trim_arm else "HOLD"
        result["stage"] = "holding"
        result["replay_result"]["stage"] = "holding"
        result["replay_result"]["candidate_response"]["action"] = action
        result["candidate_response_content_sha256"] = cycle._sha256(
            result["replay_result"]["candidate_response"]
        )
    _reseal_execution_result_ids(report)
    _replace_evaluation_with_parent_local_exclusion(
        report,
        parent_id=parent_id,
        arm=trim_arm,
        action="TRIM",
    )

    assert cycle._validated_execution_rows(report) == []
    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date=target_date,
        execution_reports=[report],
        lifecycle_reports=[],
        source_quality_pass_by_date={target_date: True},
        economic_reference_pass_by_date={target_date: True},
    )

    assert rolling["global_candidate_blockers"] == []
    assert not any(
        "historical_execution_artifact_contract_invalid" in blocker
        for blocker in manifest["global_candidate_blockers"]
    )


def test_valid_economic_parent_cannot_be_reclassified_as_trim_exclusion():
    target_date = "2026-08-24"
    parent_id = "valid-economic-parent"
    report = _execution_report(
        target_date,
        parent_id=parent_id,
        trace_id="valid-economic-trace",
        stock_code="000001",
    )
    _replace_evaluation_with_parent_local_exclusion(
        report,
        parent_id=parent_id,
        arm=cycle.EXPECTED_ARMS[0],
        action="TRIM",
    )

    with pytest.raises(ValueError, match="evaluation_top_level_census_mismatch"):
        cycle._validated_execution_rows(report)


def _current_execution_report(
    target_date: str,
    *,
    parent_id: str,
    trace_id: str,
    stock_code: str,
) -> dict:
    current_authority = {
        **cycle.SOURCE_ONLY_AUTHORITY_CONTRACT,
        "selection_authority": False,
        "decision_authority": "offline_replay_and_attribution_only",
    }
    report = _execution_report(
        target_date,
        parent_id=parent_id,
        trace_id=trace_id,
        stock_code=stock_code,
    )
    legacy_arms = cycle.EXPECTED_ARMS
    current_arms = cycle.arm_set_for_design(cycle.CURRENT_DESIGN_VERSION)
    arm_mapping = dict(zip(legacy_arms, current_arms))
    baseline_input_sha256 = cycle._sha256(
        {"parent_id": parent_id, "kind": "current_micro_input"}
    )
    enriched_input_sha256 = cycle._sha256(
        {"parent_id": parent_id, "kind": "ask_depletion_input"}
    )
    control_prompt_sha256 = cycle._sha256(
        {"design": cycle.CURRENT_DESIGN_VERSION, "kind": "control_prompt"}
    )
    candidate_prompt_sha256 = cycle._sha256(
        {"design": cycle.CURRENT_DESIGN_VERSION, "kind": "candidate_prompt"}
    )
    ask_contract_sha256 = cycle._sha256({"kind": "ask_depletion_contract_v1"})
    ask_context_sha256 = cycle._sha256(
        {"parent_id": parent_id, "kind": "ask_depletion_context"}
    )
    source_exact_sha256 = report["results"][0]["source_exact_payload_sha256"]
    tactical_evidence_sha256 = cycle._sha256(
        {"parent_id": parent_id, "kind": "tactical_micro_reversion_evidence"}
    )

    request_refs = []
    results = []
    for legacy_arm, current_arm, legacy_ref, legacy_result in zip(
        legacy_arms,
        current_arms,
        report["request_refs"],
        report["results"],
    ):
        request_id = f"{parent_id}-{current_arm}"
        is_baseline = current_arm == current_arms[0]
        is_candidate = current_arm == current_arms[2]
        candidate_input_sha256 = (
            baseline_input_sha256 if is_baseline else enriched_input_sha256
        )
        prompt_sha256 = (
            candidate_prompt_sha256 if is_candidate else control_prompt_sha256
        )
        prompt_contract_sha256 = "2" * 64 if is_candidate else "1" * 64
        ref = {
            **legacy_ref,
            "paired_replay_id": request_id,
            "micro_reversion_replay_arm": current_arm,
            "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
            "decision_stage": "entry",
            "stock_code": stock_code,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "outcome_join_key": f"label-{trace_id}",
            "source_exact_payload_sha256": source_exact_sha256,
            "tactical_micro_reversion_evidence_sha256": (tactical_evidence_sha256),
            "candidate_input_sha256": candidate_input_sha256,
            "prompt_sha256": prompt_sha256,
            "prompt_contract_sha256": prompt_contract_sha256,
        }
        result = {
            **legacy_result,
            "paired_replay_id": request_id,
            "micro_reversion_replay_arm": current_arm,
            "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
            "candidate_input_sha256": candidate_input_sha256,
            "tactical_micro_reversion_evidence_sha256": (tactical_evidence_sha256),
            "prompt_sha256": prompt_sha256,
            "prompt_contract_sha256": prompt_contract_sha256,
            **current_authority,
        }
        if is_baseline:
            ref.pop("ask_depletion_contract_sha256", None)
            ref.pop("ask_depletion_context_sha256", None)
            result.pop("ask_depletion_contract_sha256", None)
            result.pop("ask_depletion_context_sha256", None)
        else:
            ref["ask_depletion_contract_sha256"] = ask_contract_sha256
            ref["ask_depletion_context_sha256"] = ask_context_sha256
            result["ask_depletion_contract_sha256"] = ask_contract_sha256
            result["ask_depletion_context_sha256"] = ask_context_sha256
        request_refs.append(ref)
        results.append(result)
        assert legacy_ref["micro_reversion_replay_arm"] == legacy_arm

    evaluation = report["three_arm_evaluation"]
    evaluation.update(current_authority)
    evaluation["ablation_design_version"] = cycle.CURRENT_DESIGN_VERSION
    evaluation["ablation_arms"] = list(current_arms)
    evaluation["arm_metrics"] = {
        arm_mapping[arm]: metrics for arm, metrics in evaluation["arm_metrics"].items()
    }
    for partition in evaluation["stage_venue_partitions"]:
        partition["arm_metrics"] = {
            arm_mapping[arm]: metrics
            for arm, metrics in partition["arm_metrics"].items()
        }
    for row in evaluation["rows"]:
        row["arms"] = {arm_mapping[arm]: values for arm, values in row["arms"].items()}
        row.update(
            {
                "cost_adjusted_outcome_basis": "source_quality_adjusted_ev_pct",
                "mfe_pct": 0.8,
                "first_hit": "net_target_first",
                "target_first_delay_sec": 3.0,
                "action_neutral_outcome_ev_pct": row["cost_adjusted_outcome_pct"],
                "action_neutral_outcome_ev_basis": ("source_quality_adjusted_ev_pct"),
                "action_neutral_mfe_pct": 0.8,
                "action_neutral_mae_pct": row["mae_pct"],
                "action_neutral_first_hit": "net_target_first",
                "action_neutral_target_first_delay_sec": 3.0,
            }
        )
        for arm_value in row["arms"].values():
            arm_value["runtime_normalized_action"] = arm_value["action"]
            probe_ev = arm_value["standardized_probe_observation_ev_pct"]
            arm_value["comparable_ev_pct"] = (
                probe_ev
                if probe_ev is not None
                else arm_value["source_quality_adjusted_ev_pct"]
            )
            arm_value["comparable_ev_basis"] = (
                "standardized_probe_observation_ev_pct"
                if probe_ev is not None
                else "source_quality_adjusted_ev_pct"
            )

    report["ablation_design_version"] = cycle.CURRENT_DESIGN_VERSION
    report["ablation_arms"] = list(current_arms)
    report["request_refs"] = request_refs
    report["results"] = results
    for outcome_join in report["outcome_joins"]:
        outcome_join.update(
            {
                "target_date": target_date,
                "materialized_report_content_sha256": report[
                    "materialized_report_content_sha256"
                ],
                "evidence_sha256": tactical_evidence_sha256,
            }
        )
    report.update(current_authority)
    report["selected_request_ids"] = [row["paired_replay_id"] for row in results]
    _reseal_execution_result_ids(report)
    return report


def _set_baseline_to_candidate_economics(report: dict) -> None:
    arms = tuple(report.get("ablation_arms") or cycle.EXPECTED_ARMS)
    baseline_arm, _feature_arm, candidate_arm = arms
    evaluation_row = report["three_arm_evaluation"]["rows"][0]
    evaluation_row["arms"][baseline_arm] = deepcopy(
        evaluation_row["arms"][candidate_arm]
    )
    result_by_arm = {
        row["micro_reversion_replay_arm"]: row for row in report["results"]
    }
    baseline_result = result_by_arm[baseline_arm]
    candidate_result = result_by_arm[candidate_arm]
    candidate_response = deepcopy(
        candidate_result["replay_result"]["candidate_response"]
    )
    baseline_result["replay_result"]["candidate_response"] = candidate_response
    baseline_result["candidate_response_content_sha256"] = cycle._sha256(
        candidate_response
    )
    _reseal_execution_result_ids(report)


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


def _disabled_historical_diagnostic_contract(schema: str) -> dict:
    return {
        "schema": schema,
        "enabled": False,
        "raw_source_mutated": False,
        "promotion_evidence_eligible": False,
        "r2_r3_evidence_eligible": False,
        "runtime_effect": False,
        "order_authority": False,
    }


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
        "lifecycle_origin": "same_trade_date_lifecycle",
        "carry_in_custody_schema": None,
        "carry_in_entry_observed_at": None,
        "carry_in_entry_source": None,
        "decision_trace_ids": [trace_id],
        "decision_trace_context_path": [
            {
                "decision_trace_id": trace_id,
                "stage": "entry_decision",
                "venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "venue_source": "test_exact_context",
                "session_bucket_source": "test_exact_context",
                "transition_count": 1,
            }
        ],
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
        "first_fill_execution_at": f"{target_date}T09:00:00+09:00",
        "final_exit_execution_at": f"{target_date}T09:02:00+09:00",
        "duration_source": ("official_fid_908_first_fill_to_reconciled_final_exit"),
        "label_horizon_used": False,
        "session_exposure_sec": session_exposure_sec,
        "capital_time_krw_hours": 50_000.0,
        "bbo_coverage_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "invalid_transition_count": 0,
        "observed_actual_broker_order_submitted": True,
        "observed_real_order_evidence": True,
        "lifecycle_population_scope": cycle.LIFECYCLE_POPULATION_REAL_SUBMITTED,
        "source_population_scopes": [],
        "sim_scope_real_order_contract_violation_count": 0,
        "legacy_unattested_receive_clock_recovery_count": 0,
        "historical_fill_before_submit_diagnostic_recovery_count": 0,
        "historical_fill_before_submit_diagnostic_recovery_provenance": [],
        "historical_legacy_exit_submission_diagnostic_recovery_count": 0,
        "historical_legacy_exit_submission_diagnostic_recovery_provenance": [],
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
        "broker_execution_timing_schema": cycle.BROKER_EXECUTION_TIMING_SCHEMA,
        "broker_execution_ordering_time_source": (
            cycle.BROKER_EXECUTION_ORDERING_TIME_SOURCE
        ),
        "broker_execution_occurrence_time_source": (
            cycle.BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        ),
        "broker_execution_receive_time_source": (
            cycle.BROKER_EXECUTION_RECEIVE_TIME_SOURCE
        ),
        "broker_execution_unique_count": 2,
        "broker_execution_replay_duplicate_count": 0,
        "broker_execution_conflict_count": 0,
        "broker_execution_receipt_companion_conflict_count": 0,
        "broker_execution_receipt_companion_replay_duplicate_count": 0,
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
        "broker_submission_custody_order_count": 0,
        "broker_submission_custody_by_order_no": {},
        "broker_submission_custody_pending_order_count": 0,
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
    pipeline_owner_exclusion_manifest = {
        "schema": cycle.PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA,
        **cycle.PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT,
        "target_date": target_date,
        "excluded_owner_count": 0,
        "excluded_lifecycle_count": 0,
        "gap_count": 0,
        "reason_code_counts": {},
        "entries": [],
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
        "broker_execution_timing_schema": cycle.BROKER_EXECUTION_TIMING_SCHEMA,
        "broker_execution_ordering_time_source": (
            cycle.BROKER_EXECUTION_ORDERING_TIME_SOURCE
        ),
        "broker_execution_occurrence_time_source": (
            cycle.BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
        ),
        "broker_execution_receive_time_source": (
            cycle.BROKER_EXECUTION_RECEIVE_TIME_SOURCE
        ),
        "legacy_unattested_receive_clock_diagnostic": False,
        "legacy_unattested_receive_clock_diagnostic_last_date": (
            cycle.LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE
        ),
        "legacy_unattested_receive_clock_recovery_count": 0,
        "historical_fill_before_submit_diagnostic_recovery_count": 0,
        "historical_fill_before_submit_diagnostic_recovery_contract": (
            _disabled_historical_diagnostic_contract(
                lifecycle_paired.HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA
            )
        ),
        "historical_legacy_exit_submission_diagnostic_recovery_count": 0,
        "historical_legacy_exit_submission_diagnostic_recovery_contract": (
            _disabled_historical_diagnostic_contract(
                lifecycle_paired.HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA
            )
        ),
        "broker_late_arrival_outside_window_count": 0,
        "broker_submission_custody_order_count": 0,
        "broker_submission_custody_pending_order_count": 0,
        "sim_scope_real_order_contract_violation_count": 0,
        "custody_carry_schema": cycle.CARRY_IN_CUSTODY_SCHEMA,
        "custody_carry_lifecycle_count": 0,
        "custody_carry_final_exit_reconciled_count": 0,
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
        "pipeline_lifecycle_missing_identity_count": 0,
        "pipeline_lifecycle_accepted_row_count": 7,
        "pipeline_lifecycle_owner_scoped_gap_count": 0,
        "pipeline_lifecycle_exact_scoped_gap_count": 0,
        "pipeline_lifecycle_unscoped_gap_count": 0,
        "pipeline_owner_scoped_gap_high_volume_min_rows": (
            cycle.PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
        ),
        "pipeline_owner_scoped_gap_high_volume_blocked": False,
        "lifecycle_invalid_transition_count": 0,
        "broker_execution_provenance_gap_count": 0,
        "broker_execution_conflict_count": 0,
        "broker_execution_receipt_companion_conflict_count": 0,
        "broker_execution_receipt_companion_replay_duplicate_count": 0,
        "broker_execution_order_progress_conflict_count": 0,
        "broker_execution_submission_link_conflict_count": 0,
        "broker_order_no_cross_lifecycle_conflict_count": 0,
        "broker_execution_cross_lifecycle_identity_conflict_count": 0,
        "broker_execution_replay_duplicate_count": 0,
        "broker_execution_unique_count": 2,
        "candidate_row_gate_failure_count": 0 if eligible else 1,
        "instrumentation_gap_count": 0 if eligible else 1,
        "lifecycle_window_exclusion_manifest": exclusion_manifest,
        "pipeline_owner_exclusion_manifest": pipeline_owner_exclusion_manifest,
        "lifecycle_count": 1,
        "lifecycle_population_scope_counts": {
            cycle.LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION: 0,
            cycle.LIFECYCLE_POPULATION_REAL_SUBMITTED: 1,
        },
        "real_submitted_lifecycle_count": 1,
        "candidate_observation_lifecycle_count": 0,
        "lifecycle_population_partition_complete": True,
        "promotion_ready_population_scope": (
            f"{cycle.LIFECYCLE_POPULATION_REAL_SUBMITTED}_only"
        ),
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
    clean_report["lifecycle_population_scope_counts"] = {
        cycle.LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION: 0,
        cycle.LIFECYCLE_POPULATION_REAL_SUBMITTED: 2,
    }
    clean_report["real_submitted_lifecycle_count"] = 2
    clean_report["candidate_observation_lifecycle_count"] = 0
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
    occurred_at = base + timedelta(seconds=second)
    proof.update(
        {
            "broker_execution_timing_schema": (
                lifecycle_journal.BROKER_EXECUTION_TIMING_SCHEMA
            ),
            "broker_execution_received_at": occurred_at.isoformat(),
            "broker_execution_occurred_at": occurred_at.isoformat(),
            "broker_execution_receive_time_source": (
                lifecycle_journal.BROKER_EXECUTION_RECEIVE_TIME_SOURCE
            ),
            "broker_execution_ordering_time_source": (
                lifecycle_journal.BROKER_EXECUTION_ORDERING_TIME_SOURCE
            ),
            "broker_execution_occurrence_time_source": (
                lifecycle_journal.BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
            ),
            "broker_execution_receive_lag_ms": 0.0,
            "broker_execution_lifecycle_observed_at_rebound": False,
        }
    )
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
                "submission_leg_contract": "exact_broker_order_leg_v1",
            },
        ),
        transition(
            "submit",
            2,
            {
                "requested_qty": 1,
                "actual_broker_order_submitted": True,
                "broker_order_no": entry_order_no,
                "broker_order_no_list": entry_order_no,
                "submission_summary_only": True,
                "submission_summary_expected_leg_count": 1,
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
                    "submission_leg_contract": ("exact_broker_single_order_leg_v1"),
                    "submission_leg_self_summarizing": True,
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


def _krx_trading_dates(start: date, count: int) -> list[date]:
    dates: list[date] = []
    cursor = start
    while len(dates) < count:
        if cycle.is_krx_trading_day(cursor):
            dates.append(cursor)
        cursor += timedelta(days=1)
    return dates


def test_rolling_r2_r3_emits_source_only_candidate_after_strict_20_day_gate():
    start = date(2026, 7, 20)
    trading_dates = _krx_trading_dates(start, 20)
    execution_reports = []
    lifecycle_reports = []
    source_pass: dict[str, bool] = {}
    economic_pass: dict[str, bool] = {}
    for index, trading_date in enumerate(trading_dates):
        target_date = trading_date.isoformat()
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
        target_date=trading_dates[-1].isoformat(),
        execution_reports=execution_reports,
        lifecycle_reports=lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
    )

    assert rolling["joined_parent_count"] == 20
    assert rolling["partitions"][0]["r3_source_candidate_eligible"] is True
    confirmation_axis = rolling["partitions"][0]["confirmation_window_tuning_axis"]
    assert confirmation_axis["missing_legacy_axis_count"] == 20
    assert confirmation_axis["policy_ev_evaluation_status"] == (
        "awaiting_eligible_post_confirmation_outcomes"
    )
    assert confirmation_axis["runtime_effect"] is False
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
    assert (
        "requires_ask_depletion_feature_ev_noninferiority_against_current_micro"
        not in candidate["evidence_contract"]
    )
    assert manifest["first_runtime_candidate_auto_apply_performed"] is False


@pytest.mark.parametrize("baseline_matches_candidate", (False, True))
def test_current_r3_applies_feature_and_composite_baseline_gates(
    baseline_matches_candidate,
):
    start = date(2026, 7, 20)
    trading_dates = _krx_trading_dates(start, 20)
    execution_reports = []
    lifecycle_reports = []
    source_pass: dict[str, bool] = {}
    economic_pass: dict[str, bool] = {}
    for index, trading_date in enumerate(trading_dates):
        target_date = trading_date.isoformat()
        trace_id = f"current-trace-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        report = _current_execution_report(
            target_date,
            parent_id=f"current-parent-{index}",
            trace_id=trace_id,
            stock_code=stock_code,
        )
        if baseline_matches_candidate:
            _set_baseline_to_candidate_economics(report)
        execution_reports.append(report)
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
        target_date=trading_dates[-1].isoformat(),
        execution_reports=execution_reports,
        lifecycle_reports=lifecycle_reports,
        source_quality_pass_by_date=source_pass,
        economic_reference_pass_by_date=economic_pass,
    )

    assert rolling["joined_parent_count"] == 20
    assert len(rolling["partitions"]) == 1
    partition = rolling["partitions"][0]
    assert partition["ablation_design_version"] == cycle.CURRENT_DESIGN_VERSION
    metrics = partition["windows"]["20"]
    assert metrics["baseline_metric_parent_count"] == 20
    if baseline_matches_candidate:
        assert partition["r3_source_candidate_eligible"] is False
        assert "feature_ev_noninferiority_failed" in partition["gate_findings"]["20"]
        assert "composite_ev_delta_not_positive" in partition["gate_findings"]["20"]
        assert manifest["candidate_count"] == 0
    else:
        assert metrics["baseline_source_quality_adjusted_ev_pct"] == 0.0
        assert metrics["feature_ev_delta_pct"] == 0.0
        assert metrics["composite_ev_delta_pct"] == pytest.approx(0.2)
        assert partition["r3_source_candidate_eligible"] is True
        assert manifest["candidate_count"] == 1
        candidate = manifest["candidates"][0]
        assert (
            candidate["evidence_contract"][
                "requires_ask_depletion_feature_ev_noninferiority_against_current_micro"
            ]
            is True
        )
        assert (
            candidate["evidence_contract"][
                "requires_composite_ev_improvement_against_current_micro"
            ]
            is True
        )
        assert candidate["runtime_effect"] is False
        assert candidate["broker_order_forbidden"] is True


def test_wait_probe_percentage_ev_is_comparable_but_notional_stays_separate():
    report = _current_execution_report(
        "2026-08-24",
        parent_id="probe-vs-full-parent",
        trace_id="probe-vs-full-trace",
        stock_code="000001",
    )
    feature_arm = report["ablation_arms"][1]
    feature_result = next(
        row
        for row in report["results"]
        if row["micro_reversion_replay_arm"] == feature_arm
    )
    feature_response = feature_result["replay_result"]["candidate_response"]
    feature_response.update(
        {
            "action": "WAIT",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
        }
    )
    feature_result["candidate_response_content_sha256"] = cycle._sha256(
        feature_response
    )
    feature_metrics = report["three_arm_evaluation"]["rows"][0]["arms"][feature_arm]
    feature_metrics.update(
        {
            "action": "WAIT",
            "exposure_role": "standardized_probe_observation_only",
            "exposure_fraction": None,
            "economic_signal_selected": True,
            "source_quality_adjusted_ev_pct": None,
            "standardized_probe_observation_ev_pct": 0.2,
            "notional_net_profit_eligible": False,
            "notional_incremental_value_krw": None,
            "adverse_exposure": True,
            "severe_tail_exposure": False,
            "after_cost_target_first": True,
        }
    )
    _reseal_execution_result_ids(report)

    normalized = cycle._validated_execution_rows(report)

    assert len(normalized) == 1
    row = normalized[0]
    assert row["control_ev_basis"] == "standardized_one_share_probe_ev_pct"
    assert row["candidate_ev_basis"] == "full_exposure_ev_pct"
    assert row["paired_ev_delta_pct"] == pytest.approx(0.0)
    assert row["control_notional_value_krw"] is None
    assert row["candidate_notional_value_krw"] == pytest.approx(200.0)

    lifecycle_id = f"mlc-{'a' * 32}"
    row["main_lifecycle_id"] = lifecycle_id
    row["lifecycle_stage"] = "entry_decision"
    row["lifecycle"] = {
        "main_lifecycle_id": lifecycle_id,
        "trade_date": "2026-08-24",
        "stock_code": row["stock_code"],
        "session_exposure_sec": 3_600.0,
        "capital_time_krw_hours": 50_000.0,
        "actual_holding_duration_sec": 120.0,
        "bbo_coverage_pct": 100.0,
        "depth_coverage_pct": 100.0,
        "invalid_transition_count": 0,
    }
    row["lifecycle_source_row_sha256"] = cycle._sha256(row["lifecycle"])
    metrics = cycle._window_metrics(
        normalized,
        target_date="2026-08-24",
        trading_days=20,
    )
    assert metrics["control_source_quality_adjusted_ev_pct"] == pytest.approx(0.2)
    assert metrics["candidate_source_quality_adjusted_ev_pct"] == pytest.approx(0.2)
    assert metrics["candidate_notional_eligible_count"] == 1
    assert metrics["candidate_total_notional_net_profit_krw"] == pytest.approx(200.0)
    assert metrics["unique_lifecycle_count"] == 1
    assert metrics["unique_lifecycle_stage_cluster_count"] == 1
    assert metrics["lifecycle_promotion_censored_parent_count"] == 0


def _confirmation_axis(*, net_return_bps: float) -> dict:
    observation = {
        "horizon_sec": 120,
        "confirmation_fraction": 0.5,
        "mature": True,
        "classification_eligible": True,
        "post_trade_count": 12,
        "additional_mae_bps": -30.0,
        "post_low_delay_ms": 20_000,
        "terminal_trade_return_bps": 40.0,
        "max_reclaim_from_post_low_bps": 70.0,
        "half_reclaim_confirmed": True,
        "confirmation_count": 1,
        "recovery_invalidation_count": 0,
        "active_confirmation_delay_ms": 60_000,
        "active_confirmation_trade_price": 10_000.0,
        "active_confirmation_best_ask": 10_010.0,
        "active_confirmation_quote_age_ms": 0.0,
        "confirmation_followthrough_ms": 60_000,
        "confirmation_followthrough_trade_count": 6,
        "confirmation_fresh_bbo_count": 6,
        "confirmation_to_terminal_trade_return_bps": 40.0,
        "confirmation_to_terminal_trade_mfe_bps": 60.0,
        "confirmation_to_terminal_trade_mae_bps": -10.0,
        "confirmation_to_terminal_bbo_proxy_gross_return_bps": (net_return_bps + 23.0),
        "confirmation_to_terminal_bbo_proxy_mfe_bps": 63.0,
        "confirmation_to_terminal_bbo_proxy_mae_bps": 3.0,
        "fixed_followthrough_outcomes": [
            {
                "followthrough_sec": 30,
                "mature": True,
                "entry_observed_at_ms": 1_000_000,
                "entry_delay_from_confirmation_ms": 0,
                "entry_best_ask": 10_010.0,
                "endpoint_observed_at_ms": 1_030_000,
                "endpoint_lag_ms": 0,
                "endpoint_best_bid": 10_010.0
                * (1.0 + (net_return_bps + 23.0) / 10_000.0),
                "fresh_bbo_observation_count": 6,
                "max_fresh_bbo_gap_ms": 1_000,
                "standardized_one_share_gross_return_bps": (net_return_bps + 23.0),
                "verified_roundtrip_cost_bps": 23.0,
                "standardized_one_share_net_return_bps": net_return_bps,
                "standardized_one_share_net_mfe_bps": 40.0,
                "standardized_one_share_net_mae_bps": -20.0,
                "tuning_outcome_eligible": True,
                "source_quality_blockers": [],
                "tuning_outcome_blockers": [],
            }
        ],
        "terminal_trade_lag_ms": 0,
        "direction_state": "REVERSION_CONFIRMED",
        "source_quality_blockers": [],
    }
    return {
        "schema": bridge.CONFIRMATION_WINDOW_SCHEMA,
        "axis_role": "micro_reversion_tuning_only",
        "horizons_sec": [120],
        "followthrough_horizons_sec": [30],
        "confirmation_fraction": 0.5,
        "max_endpoint_lag_ms": 2_500,
        "max_internal_gap_ms": 2_500,
        "max_quote_age_ms": 1_000,
        "outcome_basis": (
            "standardized_one_share_confirmation_deadline_fresh_ask_to_fixed_"
            "followthrough_fresh_bid_top_of_book_proxy_"
            "after_verified_roundtrip_cost"
        ),
        "observations": [observation],
        "included_in_prompt_context": False,
        **bridge.CONFIRMATION_WINDOW_METRIC_CONTRACT,
        **bridge.AUTHORITY_CONTRACT,
    }


def test_confirmation_window_census_reports_post_signal_net_outcome() -> None:
    census = cycle._confirmation_window_tuning_census(
        [
            {"confirmation_window_axis": _confirmation_axis(net_return_bps=10.0)},
            {"confirmation_window_axis": _confirmation_axis(net_return_bps=-5.0)},
        ]
    )

    assert census["policy_ev_evaluation_status"] == (
        "standardized_one_share_source_only_outcome_observed"
    )
    assert census["tuning_outcome_eligible_counts"] == {"confirm_120s_follow_30s": 2}
    metrics = census["outcome_metrics"]["confirm_120s_follow_30s"]
    assert metrics["sample_count"] == 2
    assert metrics["equal_weight_avg_profit_pct"] == pytest.approx(0.025)
    assert metrics["diagnostic_win_rate_pct"] == 50.0
    assert metrics["mean_standardized_one_share_net_mfe_pct"] == 0.4
    assert metrics["mean_standardized_one_share_net_mae_pct"] == -0.2
    assert metrics["median_active_confirmation_delay_ms"] == 60_000.0
    assert metrics["median_entry_deadline_lag_ms"] == 0.0
    assert census["runtime_effect"] is False
    assert census["allowed_runtime_apply"] is False


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


def test_lifecycle_index_rejects_off_trade_date_execution_duration():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["rows"][0]["first_fill_execution_at"] = "2026-08-15T09:00:00+09:00"
    report["rows"][0]["final_exit_execution_at"] = "2026-08-15T09:02:00+09:00"
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(
        "row_official_execution_duration_contract_invalid" in finding
        for finding in findings
    )


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


def test_lifecycle_index_candidate_observation_never_poison_real_trace_join():
    target_date = "2026-08-14"
    report = _mixed_lifecycle_report(target_date)
    candidate = report["rows"][1]
    candidate["decision_trace_ids"] = ["trace-clean"]
    candidate["lifecycle_population_scope"] = (
        cycle.LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION
    )
    candidate["observed_real_order_evidence"] = False
    candidate["observed_actual_broker_order_submitted"] = False
    candidate["broker_submitted_order_count"] = 0
    candidate["broker_submission_custody_order_count"] = 0
    candidate["broker_execution_entry_covered_qty"] = 0.0
    candidate["broker_execution_exit_covered_qty"] = 0.0
    candidate["broker_execution_provenance_state_counts"] = {}
    candidate["broker_submitted_requested_qty_by_order_no"] = {}
    candidate["broker_executed_order_qty_by_phase"] = {}
    candidate["terminal_state"] = "INCOMPLETE"
    for field in (
        "broker_execution_provenance_gap_count",
        "broker_execution_conflict_count",
        "broker_execution_receipt_companion_conflict_count",
        "broker_execution_receipt_companion_replay_duplicate_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "broker_execution_replay_duplicate_count",
        "broker_execution_unique_count",
    ):
        candidate[field] = 0
    report["broker_execution_unique_count"] = 2
    report["candidate_row_gate_failure_count"] = 0
    report["instrumentation_gap_count"] = 0
    report["lifecycle_population_scope_counts"] = {
        cycle.LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION: 1,
        cycle.LIFECYCLE_POPULATION_REAL_SUBMITTED: 1,
    }
    report["real_submitted_lifecycle_count"] = 1
    report["candidate_observation_lifecycle_count"] = 1
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert set(index) == {(target_date, "trace-clean")}
    assert findings == []


def test_lifecycle_validator_rejects_broker_row_laundered_as_candidate():
    target_date = "2026-08-14"
    report = _lifecycle_report(
        target_date,
        trace_id="trace-broker-launder",
        eligible=False,
    )
    row = report["rows"][0]
    row["observed_actual_broker_order_submitted"] = False
    row["observed_real_order_evidence"] = False
    row["lifecycle_population_scope"] = cycle.LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION
    report["lifecycle_population_scope_counts"] = {
        cycle.LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION: 1,
        cycle.LIFECYCLE_POPULATION_REAL_SUBMITTED: 0,
    }
    report["real_submitted_lifecycle_count"] = 0
    report["candidate_observation_lifecycle_count"] = 1
    _seal_lifecycle_report(report)

    findings = cycle._lifecycle_report_contract_findings(
        report,
        rows=report["rows"],
    )

    assert any(
        finding.startswith("lifecycle_population_concrete_broker_evidence_mismatch:")
        for finding in findings
    )


def test_lifecycle_validator_rejects_forged_carry_final_without_exit_receipt_coverage():
    target_date = "2026-08-26"
    report = _lifecycle_report(
        target_date,
        trace_id="trace-carry-final",
        eligible=False,
    )
    row = report["rows"][0]
    row.update(
        {
            "lifecycle_origin": "preexisting_position_custody",
            "carry_in_custody_schema": cycle.CARRY_IN_CUSTODY_SCHEMA,
            "carry_in_entry_observed_at": "2026-08-25T15:10:00+09:00",
            "carry_in_entry_source": "stock.buy_time",
            "terminal_state": "CUSTODY_CARRY_FINAL_EXIT_RECONCILED",
            "right_censored": False,
            "entry_fill_qty": 0.0,
            "promotion_evidence_eligible": False,
            "row_source_quality_gate_pass": False,
            "promotion_blockers": ["custody_carry_in_entry_lifecycle_non_promotable"],
        }
    )
    report["custody_carry_lifecycle_count"] = 1
    report["custody_carry_final_exit_reconciled_count"] = 1

    valid_findings = cycle._lifecycle_report_contract_findings(
        report,
        rows=report["rows"],
    )
    assert not any(
        finding.startswith("lifecycle_custody_carry_contract_invalid:")
        for finding in valid_findings
    )

    row["broker_execution_exit_covered_qty"] = 0.0
    forged_findings = cycle._lifecycle_report_contract_findings(
        report,
        rows=report["rows"],
    )
    assert any(
        finding.startswith("lifecycle_custody_carry_contract_invalid:")
        for finding in forged_findings
    )


def test_lifecycle_validator_preserves_pre_activation_immutable_report_compatibility():
    legacy = _lifecycle_report(
        "2026-08-26",
        trace_id="trace-pre-carry-contract",
    )
    for field in (
        "custody_carry_schema",
        "custody_carry_lifecycle_count",
        "custody_carry_final_exit_reconciled_count",
    ):
        legacy.pop(field)
    for field in (
        "carry_in_custody_schema",
        "lifecycle_origin",
        "carry_in_entry_observed_at",
        "carry_in_entry_source",
    ):
        legacy["rows"][0].pop(field)

    legacy_findings = cycle._lifecycle_report_contract_findings(
        legacy,
        rows=legacy["rows"],
    )
    assert not any("custody_carry" in finding for finding in legacy_findings)
    assert not any(
        "lifecycle_noncarry_contract_invalid" in finding for finding in legacy_findings
    )

    partial_legacy = deepcopy(legacy)
    partial_legacy["rows"][0]["lifecycle_origin"] = "same_trade_date_lifecycle"
    partial_findings = cycle._lifecycle_report_contract_findings(
        partial_legacy,
        rows=partial_legacy["rows"],
    )
    assert any(
        finding.startswith("lifecycle_custody_carry_contract_incomplete:")
        for finding in partial_findings
    )

    required = _lifecycle_report(
        cycle.CARRY_IN_CUSTODY_REQUIRED_DATE,
        trace_id="trace-required-carry-contract",
    )
    for field in (
        "custody_carry_schema",
        "custody_carry_lifecycle_count",
        "custody_carry_final_exit_reconciled_count",
    ):
        required.pop(field)
    for field in (
        "carry_in_custody_schema",
        "lifecycle_origin",
        "carry_in_entry_observed_at",
        "carry_in_entry_source",
    ):
        required["rows"][0].pop(field)
    required_findings = cycle._lifecycle_report_contract_findings(
        required,
        rows=required["rows"],
    )
    assert "custody_carry_top_level_census_mismatch" in required_findings
    assert any(
        finding.startswith("lifecycle_noncarry_contract_invalid:")
        for finding in required_findings
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


def test_lifecycle_validator_recomputes_sim_scope_real_order_incident(
    tmp_path: Path,
) -> None:
    target_date = "2026-08-14"
    cost_hash = cycle._sha256({"kind": "cost", "target_date": target_date})
    symbol_hash = cycle._sha256({"kind": "symbol", "target_date": target_date})
    transitions = []
    for original in _producer_lifecycle_transitions(
        target_date=target_date,
        attempt="sim-real-incident",
        namespace=7,
        include_scale_in=True,
        cost_hash=cost_hash,
        symbol_hash=symbol_hash,
    ):
        transitions.append(
            lifecycle_journal.build_transition(
                main_lifecycle_id=original["main_lifecycle_id"],
                record_id=original["record_id"],
                stock_code=original["stock_code"],
                attempt_id=original["attempt_id"],
                trade_date=original["trade_date"],
                stage=original["stage"],
                observed_at=original["observed_at"],
                venue=original["venue"],
                session_bucket=original["session_bucket"],
                data={
                    **original["data"],
                    "source_population_scope": "sim_observation_only",
                },
            )
        )
    source = tmp_path / "sim_real_incident.jsonl"
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
    row = report["rows"][0]

    findings = cycle._lifecycle_report_contract_findings(
        report,
        rows=report["rows"],
    )
    assert row["sim_scope_real_order_contract_violation_count"] == 1
    assert report["sim_scope_real_order_contract_violation_count"] == 1
    assert not any("sim_scope_real_order" in finding for finding in findings)

    tampered_row = deepcopy(report)
    tampered_row["rows"][0]["promotion_blockers"].remove(
        "sim_scope_real_order_contract_violation"
    )
    row_findings = cycle._lifecycle_report_contract_findings(
        tampered_row,
        rows=tampered_row["rows"],
    )
    assert any(
        finding.startswith("lifecycle_sim_scope_real_order_incident_contract_invalid:")
        for finding in row_findings
    )

    tampered_count = deepcopy(report)
    tampered_count["sim_scope_real_order_contract_violation_count"] = 0
    count_findings = cycle._lifecycle_report_contract_findings(
        tampered_count,
        rows=tampered_count["rows"],
    )
    assert "sim_scope_real_order_contract_violation_census_mismatch" in (count_findings)
    assert "instrumentation_gap_census_mismatch" in count_findings

    tampered_global = deepcopy(report)
    tampered_global["global_source_quality_gate_blockers"] = []
    global_findings = cycle._lifecycle_report_contract_findings(
        tampered_global,
        rows=tampered_global["rows"],
    )
    assert "sim_scope_real_order_global_blocker_mismatch" in global_findings


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


def test_lifecycle_index_rejects_self_rehashed_pipeline_owner_manifest_tamper():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["pipeline_owner_exclusion_manifest"]["excluded_owner_count"] = 1
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(
        "pipeline_owner_exclusion_owner_census_mismatch" in row for row in findings
    )


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


@pytest.mark.parametrize(
    ("family", "count_field", "contract_field", "provenance_field"),
    (
        (
            "fill_before_submit",
            "historical_fill_before_submit_diagnostic_recovery_count",
            "historical_fill_before_submit_diagnostic_recovery_contract",
            "historical_fill_before_submit_diagnostic_recovery_provenance",
        ),
        (
            "legacy_exit_submission",
            "historical_legacy_exit_submission_diagnostic_recovery_count",
            "historical_legacy_exit_submission_diagnostic_recovery_contract",
            "historical_legacy_exit_submission_diagnostic_recovery_provenance",
        ),
    ),
)
@pytest.mark.parametrize(
    "tamper",
    ("count", "enabled", "promotion_eligible", "r2_r3_eligible"),
)
def test_lifecycle_index_rejects_self_resealed_historical_diagnostic_recovery(
    family: str,
    count_field: str,
    contract_field: str,
    provenance_field: str,
    tamper: str,
) -> None:
    report = _lifecycle_report("2026-08-14", trace_id=f"trace-{family}-{tamper}")
    if tamper == "count":
        report[count_field] = 1
        report["rows"][0][count_field] = 1
        report["rows"][0][provenance_field] = [
            {
                "schema": "forged_self_resealed_diagnostic_recovery",
                "r2_r3_evidence_eligible": False,
            }
        ]
    elif tamper == "enabled":
        report[contract_field]["enabled"] = True
    elif tamper == "promotion_eligible":
        report[contract_field]["promotion_evidence_eligible"] = True
    else:
        report[contract_field]["r2_r3_evidence_eligible"] = True
    _seal_lifecycle_report(report)

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert any(
        "historical_lifecycle_diagnostic_recovery_" in finding
        or "row_historical_diagnostic_provenance_present" in finding
        for finding in findings
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


def test_rolling_binds_mutable_context_by_exact_decision_trace_path():
    target_date = "2026-08-14"
    lifecycle = _lifecycle_report(target_date, trace_id="trace-1")
    lifecycle_row = lifecycle["rows"][0]
    lifecycle_row["venue"] = "NXT"
    lifecycle_row["session_bucket"] = "NXT_AFTERMARKET"
    _seal_lifecycle_report(lifecycle)

    rolling, _ = cycle.build_rolling_source_only_candidates(
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
    assert rolling["joined_parent_count"] == 1
    assert rolling["exclusions"] == []


def test_rolling_rejects_ambiguous_context_for_same_trace_and_stage():
    target_date = "2026-08-14"
    lifecycle = _lifecycle_report(target_date, trace_id="trace-1")
    lifecycle["rows"][0]["decision_trace_context_path"].append(
        {
            "decision_trace_id": "trace-1",
            "stage": "entry_decision",
            "venue": "NXT",
            "session_bucket": "NXT_AFTERMARKET",
            "venue_source": "test_second_context",
            "session_bucket_source": "test_second_context",
            "transition_count": 1,
        }
    )
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
        "daily_lifecycle_trace_context_ambiguous"
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


def test_execution_parent_rejects_arm_local_decision_timestamp_divergence():
    report = _execution_report(
        "2026-08-24",
        parent_id="parent-timestamp",
        trace_id="trace-timestamp",
        stock_code="000001",
    )
    report["results"][1]["decision_ts"] = "2026-08-24T09:00:01+09:00"
    _reseal_execution_result_ids(report)

    with pytest.raises(
        ValueError,
        match="result_parent_decision_timestamp_mismatch",
    ):
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


def test_historical_implicit_legacy_keeps_missing_request_exact_hash_compatibility():
    report = _execution_report(
        "2026-08-14",
        parent_id="legacy-parent",
        trace_id="legacy-trace",
        stock_code="000001",
    )

    rows = cycle._validated_execution_rows(report)

    assert report.get("ablation_design_version") is None
    assert all(
        "source_exact_payload_sha256" not in ref for ref in report["request_refs"]
    )
    assert rows[0]["ablation_design_version"] == cycle.LEGACY_DESIGN_VERSION
    assert "baseline_ev_pct" not in rows[0]


@pytest.mark.parametrize("mutation", ("missing_exact_hash", "missing_design_version"))
def test_explicit_legacy_requires_request_exact_hash_and_version_binding(mutation):
    report = _execution_report(
        "2026-08-14",
        parent_id="explicit-legacy-parent",
        trace_id="explicit-legacy-trace",
        stock_code="000001",
    )
    report["ablation_design_version"] = cycle.LEGACY_DESIGN_VERSION
    report["ablation_arms"] = list(cycle.EXPECTED_ARMS)
    report["three_arm_evaluation"][
        "ablation_design_version"
    ] = cycle.LEGACY_DESIGN_VERSION
    report["three_arm_evaluation"]["ablation_arms"] = list(cycle.EXPECTED_ARMS)
    for ref, result in zip(report["request_refs"], report["results"]):
        ref["ablation_design_version"] = cycle.LEGACY_DESIGN_VERSION
        ref["source_exact_payload_sha256"] = result["source_exact_payload_sha256"]
        result["ablation_design_version"] = cycle.LEGACY_DESIGN_VERSION
    _reseal_execution_result_ids(report)
    assert len(cycle._validated_execution_rows(report)) == 1

    if mutation == "missing_exact_hash":
        report["request_refs"][0].pop("source_exact_payload_sha256")
    else:
        report["request_refs"][0].pop("ablation_design_version")
    _reseal_execution_report(report)

    with pytest.raises(
        ValueError,
        match="execution_report_exact_census_invalid:"
        "request_ref_identity_or_hash_invalid",
    ):
        cycle._validated_execution_rows(report)


def test_current_execution_normalizes_frozen_a_b_c_baseline_values():
    report = _current_execution_report(
        "2026-08-14",
        parent_id="current-parent",
        trace_id="current-trace",
        stock_code="000001",
    )

    rows = cycle._validated_execution_rows(report)

    assert {ref["source_exact_payload_sha256"] for ref in report["request_refs"]} == {
        report["results"][0]["source_exact_payload_sha256"]
    }
    assert len(rows) == 1
    assert rows[0]["ablation_design_version"] == cycle.CURRENT_DESIGN_VERSION
    assert rows[0]["baseline_ev_pct"] == 0.0
    assert rows[0]["feature_ev_delta_pct"] == 0.0
    assert rows[0]["composite_ev_delta_pct"] == pytest.approx(0.2)
    assert rows[0]["baseline_severe_tail"] is False


def test_post_activation_current_execution_requires_persisted_materialized_companion():
    report = _current_execution_report(
        cycle.CURRENT_DESIGN_ACTIVATION_DATE,
        parent_id="current-parent",
        trace_id="current-trace",
        stock_code="000001",
    )

    with pytest.raises(
        ValueError, match="execution_report_materialized_companion_missing"
    ):
        cycle._validated_execution_rows(report)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ("request_missing", "request_ref_identity_or_hash_invalid"),
        ("result_mismatch", "result_source_exact_hash_binding_mismatch"),
        ("one_arm_rebound", "request_parent_source_exact_hash_mismatch"),
    ),
)
def test_current_execution_rejects_unbound_or_nonuniform_source_exact_hashes(
    mutation,
    reason,
):
    report = _current_execution_report(
        "2026-08-14",
        parent_id="current-parent",
        trace_id="current-trace",
        stock_code="000001",
    )
    if mutation == "request_missing":
        report["request_refs"][0].pop("source_exact_payload_sha256")
        _reseal_execution_report(report)
    elif mutation == "result_mismatch":
        report["results"][0]["source_exact_payload_sha256"] = "f" * 64
        _reseal_execution_result_ids(report)
    else:
        report["request_refs"][0]["source_exact_payload_sha256"] = "f" * 64
        report["results"][0]["source_exact_payload_sha256"] = "f" * 64
        _reseal_execution_result_ids(report)

    with pytest.raises(
        ValueError,
        match=f"execution_report_exact_census_invalid:{reason}",
    ):
        cycle._validated_execution_rows(report)


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

    execution, lifecycle, source_pass, economic_pass, labels, diagnostics = (
        cycle._collect_rolling_inputs(
            target_date=target_date,
            lookback_calendar_days=1,
        )
    )

    assert execution == []
    assert lifecycle == []
    assert source_pass == {}
    assert economic_pass == {}
    assert labels == {}
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


def _bind_legacy_execution_companions(report: dict) -> tuple[dict, dict]:
    requests = [
        {
            "paired_replay_parent_id": row["paired_replay_parent_id"],
            "paired_replay_id": row["paired_replay_id"],
            "micro_reversion_replay_arm": row["micro_reversion_replay_arm"],
            "decision_trace_id": row["decision_trace_id"],
        }
        for row in report["request_refs"]
    ]
    materialized_body = {
        "schema": quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA,
        "target_date": report["target_date"],
        "generation": 1,
        "request_count": len(requests),
        "request_ids": [row["paired_replay_id"] for row in requests],
        "requests": requests,
    }
    materialized = {
        **materialized_body,
        "report_content_sha256": cycle._sha256(materialized_body),
    }
    outcome_artifact = {
        "schema": "legacy_action_neutral_outcome_fixture_v1",
        "target_date": report["target_date"],
        "generation": 1,
    }
    report.update(
        {
            "materialized_report_content_sha256": materialized["report_content_sha256"],
            "materialized_report_artifact_sha256": cycle._sha256(materialized),
            "materialized_request_census_sha256": (
                quality._micro_reversion_materialized_request_census_sha256(
                    materialized
                )
            ),
            "outcome_label_artifact_sha256": cycle._sha256(outcome_artifact),
        }
    )
    _reseal_execution_report(report)
    return materialized, outcome_artifact


@pytest.mark.parametrize(
    ("replaced_companion", "expected_reason"),
    (
        (
            "materialized",
            "execution_report_materialized_companion_binding_mismatch",
        ),
        ("outcome", "execution_report_outcome_companion_hash_mismatch"),
    ),
)
def test_preactivation_replaced_execution_companion_is_excluded_without_global_poison(
    replaced_companion,
    expected_reason,
):
    source_date = "2026-08-24"
    report = _execution_report(
        source_date,
        parent_id="legacy-provider-parent",
        trace_id="legacy-provider-trace",
        stock_code="000001",
    )
    materialized, outcome_artifact = _bind_legacy_execution_companions(report)

    assert (
        len(
            cycle._validated_execution_rows(
                report,
                materialized_report=materialized,
                outcome_label_artifact=outcome_artifact,
            )
        )
        == 1
    )

    supplied_materialized = materialized
    supplied_outcome = outcome_artifact
    if replaced_companion == "materialized":
        supplied_materialized = {**materialized, "generation": 2}
        supplied_materialized["report_content_sha256"] = cycle._content_hash(
            supplied_materialized,
            "report_content_sha256",
        )
    else:
        supplied_outcome = {**outcome_artifact, "generation": 2}

    rolling, manifest = cycle.build_rolling_source_only_candidates(
        target_date="2026-08-25",
        execution_reports=[report],
        lifecycle_reports=[],
        source_quality_pass_by_date={source_date: True},
        economic_reference_pass_by_date={source_date: True},
        outcome_label_artifacts_by_date={
            source_date: {
                "outcome_label_artifact": supplied_outcome,
                "materialized_report": supplied_materialized,
            }
        },
    )

    assert rolling["joined_parent_count"] == 0
    assert rolling["source_execution_dates"] == []
    assert rolling["exclusions"] == [
        {"reason": expected_reason, "target_date": source_date}
    ]
    assert rolling["global_candidate_blockers"] == []
    assert manifest["candidate_count"] == 0
    assert manifest["global_candidate_blockers"] == []


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
    if "labels" not in outcome_artifact:
        labels = []
        for index, request in enumerate(requests):
            label_id = f"test-label-{index}"
            request.setdefault("outcome_join_key", label_id)
            labels.append({"label_id": label_id})
        outcome_artifact["labels"] = labels
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
            "materialized_report_artifact_sha256": cycle._sha256(materialized),
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
        lambda _artifact, **_kwargs: None,
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
        lambda _artifact, **_kwargs: None,
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
        lambda _artifact, **_kwargs: None,
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
        lambda **_kwargs: ([stale_execution], [], {}, {}, {}, []),
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
    assert report["storage_capacity_gate"]["large_artifact_growth_allowed"] is True
    assert report["rolling_status"] == "source_quality_or_composed_chain_blocked"
    assert report["status"] == "source_only_blocked_or_deferred"


def test_provider_bound_r0_generation_reuses_exact_companion_set(
    tmp_path,
    monkeypatch,
):
    target_date = "2026-08-14"
    paths = {
        "execution": tmp_path / "execution.json",
        "materialized": tmp_path / "materialized.json",
        "labels": tmp_path / "labels.json",
        "source_bundle": tmp_path / "source-bundle.json",
        "prepared": tmp_path / "prepared.json",
        "bridge_report": tmp_path / "bridge.json",
        "paired_report": tmp_path / "paired.json",
    }
    paired = {"schema": "paired-test", "target_date": target_date}
    bridge_body = {"schema": "bridge-test", "target_date": target_date}
    bridge = {
        **bridge_body,
        "artifact_content_sha256": cycle._sha256(bridge_body),
    }
    prepared = {
        "schema": "prepared-test",
        "target_date": target_date,
        "source_paired_report_content_sha256": cycle._sha256(paired),
    }
    source_bundle = {
        "schema": "source-bundle-test",
        "target_date": target_date,
        "outcome_source_commitment": {
            "bridge_report_content_sha256": bridge["artifact_content_sha256"],
            "bridge_report_artifact_sha256": cycle._sha256(bridge),
        },
    }
    materialized = {
        "schema": quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA,
        "target_date": target_date,
        "source_bundle_path": str(paths["source_bundle"]),
        "prepared_request_artifact_path": str(paths["prepared"]),
        "report_content_sha256": "a" * 64,
    }
    labels = {"schema": "labels-test", "target_date": target_date}
    floor_body = {"schema": "floor-test", "target_date": target_date}
    provider_floor = {
        **floor_body,
        "floor_content_sha256": cycle._sha256(floor_body),
    }
    floor_path = (
        tmp_path
        / f"micro_reversion_provider_ablation_sample_floor_{target_date}.json"
    )
    for path, payload in (
        (paths["materialized"], materialized),
        (paths["labels"], labels),
        (paths["source_bundle"], source_bundle),
        (paths["prepared"], prepared),
        (paths["bridge_report"], bridge),
        (paths["paired_report"], paired),
        (floor_path, provider_floor),
    ):
        path.write_text(json.dumps(payload), encoding="utf-8")
    execution_body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": target_date,
        "provider_call_performed": True,
        "result_count": 1,
        "materialized_artifact_path": str(paths["materialized"]),
        "outcome_label_artifact_path": str(paths["labels"]),
        "provider_ablation_sample_floor_path": str(floor_path),
        "provider_ablation_sample_floor_content_sha256": provider_floor[
            "floor_content_sha256"
        ],
        "provider_ablation_sample_floor_artifact_sha256": cycle._sha256(
            provider_floor
        ),
    }
    paths["execution"].write_text(
        json.dumps(
            {
                **execution_body,
                "report_content_sha256": cycle._sha256(execution_body),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        cycle,
        "_validate_execution_external_companion_bindings",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "validate_current_materialized_source_lineage",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        cycle,
        "provider_ablation_floor_path",
        lambda _target_date: floor_path,
    )

    frozen = cycle._load_provider_bound_r0_generation(
        target_date=target_date,
        selected_paths=paths,
    )

    assert frozen is not None
    assert frozen["prepared"] == prepared
    assert frozen["source_bundle"] == source_bundle
    assert frozen["provider_floor"] == provider_floor

    mutated_bridge = {**bridge, "mutated": True}
    paths["bridge_report"].write_text(
        json.dumps(mutated_bridge),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="provider_bound_bridge_companion_mismatch"):
        cycle._load_provider_bound_r0_generation(
            target_date=target_date,
            selected_paths=paths,
        )

    paths["bridge_report"].write_text(json.dumps(bridge), encoding="utf-8")
    outcome_proof = {"label_id": "label-1", "status": "mature"}
    labels = {
        "schema": "labels-test",
        "target_date": target_date,
        "labels": [outcome_proof],
    }
    paths["labels"].write_text(json.dumps(labels), encoding="utf-8")
    checkpoint_path = tmp_path / "execution.checkpoint.json"
    checkpoint_path.write_text("{}", encoding="utf-8")
    paths["execution_checkpoint"] = checkpoint_path
    paths["provider_ablation_floor"] = floor_path
    checkpoint = {
        "provider_call_performed": True,
        "materialized_report_content_sha256": (
            quality._micro_reversion_materialized_request_census_sha256(
                materialized
            )
        ),
        "results": [
            {
                "outcome_join_key": "label-1",
                "outcome_label_content_sha256": cycle._sha256(outcome_proof),
            }
        ],
    }
    uncommitted_execution_body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": target_date,
        "provider_call_performed": False,
        "result_count": 0,
        "committed_parent_count": 0,
    }
    paths["execution"].write_text(
        json.dumps(
            {
                **uncommitted_execution_body,
                "report_content_sha256": cycle._sha256(
                    uncommitted_execution_body
                ),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        quality,
        "_load_micro_reversion_checkpoint",
        lambda *_args, **_kwargs: checkpoint,
    )
    checkpoint_binding_calls = []
    monkeypatch.setattr(
        quality,
        "_micro_reversion_provider_checkpoint_bindings",
        lambda **kwargs: checkpoint_binding_calls.append(kwargs) or {},
    )

    checkpoint_frozen = cycle._load_provider_bound_r0_generation(
        target_date=target_date,
        selected_paths=paths,
    )
    assert checkpoint_frozen is not None
    assert checkpoint_frozen["execution"] == {
        **uncommitted_execution_body,
        "report_content_sha256": cycle._sha256(uncommitted_execution_body),
    }
    assert checkpoint_frozen["checkpoint"] == checkpoint
    assert checkpoint_binding_calls[0][
        "provider_ablation_sample_floor_content_sha256"
    ] == provider_floor["floor_content_sha256"]

    checkpoint["results"][0]["outcome_label_content_sha256"] = ""
    with pytest.raises(
        ValueError, match="provider_bound_checkpoint_outcome_binding_invalid"
    ):
        cycle._load_provider_bound_r0_generation(
            target_date=target_date,
            selected_paths=paths,
        )


def test_cycle_capacity_gate_blocks_large_chain_but_keeps_lifecycle_source_work(
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
    monkeypatch.setattr(
        cycle,
        "evaluate_large_artifact_capacity_gate",
        lambda **_kwargs: {
            "schema": "scalp_micro_reversion_storage_capacity_growth_gate_v1",
            "target_date": target_date,
            "status": "blocked_critical_or_unknown_capacity",
            "large_artifact_growth_allowed": False,
            "effective_capacity_state": "critical",
            "reason_codes": ["direct_disk_free_below_critical_watermark"],
        },
    )
    monkeypatch.setattr(
        cycle,
        "_collect_rolling_inputs",
        lambda **_kwargs: ([], [], {}, {}, {}, []),
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
    commands = []

    def runner(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    report = cycle.run_cycle(
        target_date=target_date,
        write=True,
        execute_provider_replay=True,
        daily_attempt_cap=12,
        daily_usd_cap=1.0,
        parent_cap=1,
        paths={
            "source_audit": audit_path,
            "capacity_status": tmp_path / "capacity.json",
            "prepared": tmp_path / "prepared.json",
            "bridge_report": tmp_path / "missing-bridge.json",
            "lifecycle": tmp_path / "missing-lifecycle.json",
        },
        command_runner=runner,
    )

    assert report["storage_capacity_gate"]["effective_capacity_state"] == "critical"
    assert (
        "large_artifact_growth_blocked:blocked_critical_or_unknown_capacity"
        in report["blockers"]
    )
    assert report["provider_call_performed"] is False
    assert len(commands) == 1
    assert "src.engine.scalping.main_lifecycle_paired" in commands[0]


def _sample_floor_materialized_report(
    target_date: str, *, parent_start: int, parent_count: int, valid: bool = True
) -> dict:
    requests = []
    arms = cycle.arm_set_for_design(cycle.CURRENT_DESIGN_VERSION)
    for index in range(parent_start, parent_start + parent_count):
        parent_id = f"parent-{target_date}-{index}"
        symbol = f"{index % 10 + 1:06d}"
        requests.extend(
            {
                "paired_replay_parent_id": parent_id,
                "paired_replay_id": f"{parent_id}:{arm}",
                "micro_reversion_replay_arm": arm,
                "stock_code": symbol,
            }
            for arm in arms
        )
    report = {
        "schema": quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA,
        "target_date": target_date,
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
        "status": (
            "materialized_source_only_requests"
            if requests
            else "no_micro_reversion_eligible_requests"
        ),
        "materialization_count": parent_count,
        "request_count": len(requests),
        "request_ids": [row["paired_replay_id"] for row in requests],
        "materializations": [{} for _ in range(parent_count)],
        "requests": requests,
        "provider_call_performed": False,
        "decision_authority": "offline_replay_and_attribution_only",
        "selection_authority": False,
        **cycle.SOURCE_ONLY_AUTHORITY_CONTRACT,
        "_requests": requests,
        "_valid": valid,
    }
    report["report_content_sha256"] = cycle._content_hash(
        report, "report_content_sha256"
    )
    return report


def _sample_floor_companions(target_date: str) -> dict:
    return {
        "source_bundle": {"target_date": target_date},
        "prepared": {"target_date": target_date},
        "bridge": {"target_date": target_date},
        "paired": {"target_date": target_date},
        "paths": {
            "source_bundle": f"source-{target_date}.json",
            "prepared": f"prepared-{target_date}.json",
            "bridge": f"bridge-{target_date}.json",
            "paired": f"paired-{target_date}.json",
        },
    }


def test_provider_ablation_floor_blocks_one_day_and_passes_exact_5_20_10(
    monkeypatch,
):
    def validate(report):
        if report.get("_valid") is not True:
            raise ValueError("tampered")
        return report["_requests"]

    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        validate,
    )
    monkeypatch.setattr(
        cycle,
        "_validate_current_materialized_source_lineage",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_materialized_request_census_sha256",
        lambda report: cycle._sha256(report["request_ids"]),
    )
    one_day = _sample_floor_materialized_report(
        "2026-08-26", parent_start=0, parent_count=1
    )
    blocked = cycle._provider_ablation_sample_floor_from_reports(
        target_date="2026-08-26",
        materialized_reports=[
            (
                "2026-08-26",
                Path("one.json"),
                one_day,
                _sample_floor_companions("2026-08-26"),
            )
        ],
    )
    assert blocked["pass"] is False
    assert blocked["observed_trading_days"] == 1
    assert blocked["observed_common_parent_count"] == 1
    assert blocked["observed_unique_symbol_count"] == 1

    reports = [
        _sample_floor_materialized_report(day, parent_start=index * 4, parent_count=4)
        for index, day in enumerate(
            (
                "2026-08-25",
                "2026-08-26",
                "2026-08-27",
                "2026-08-28",
                "2026-08-31",
                "2026-09-01",
            )
        )
    ]
    passed = cycle._provider_ablation_sample_floor_from_reports(
        target_date="2026-09-01",
        materialized_reports=[
            (
                report["target_date"],
                Path(f"{report['target_date']}.json"),
                report,
                _sample_floor_companions(report["target_date"]),
            )
            for report in reports
        ],
    )
    assert passed["pass"] is True
    assert passed["observed_trading_days"] == 5
    assert passed["observed_common_parent_count"] == 20
    assert passed["observed_unique_symbol_count"] == 10
    assert passed["excluded_pre_source_contract_artifact_dates"] == ["2026-08-25"]
    assert passed["floor_content_sha256"] == cycle._sha256(
        {key: value for key, value in passed.items() if key != "floor_content_sha256"}
    )


def test_historical_backfill_dates_are_oldest_first_and_reserve_current_parent(
    tmp_path,
    monkeypatch,
) -> None:
    floor_body = {
        "target_date": "2026-08-31",
        "pass": True,
        "status": "pass_provider_ablation_floor_met",
        "included_artifacts": [
            {"target_date": day, "parent_count": 4}
            for day in (
                "2026-08-25",
                "2026-08-26",
                "2026-08-27",
                "2026-08-28",
                "2026-08-31",
            )
        ],
    }
    floor = {
        **floor_body,
        "floor_content_sha256": cycle._sha256(floor_body),
    }
    monkeypatch.setattr(
        cycle,
        "provider_ablation_floor_path",
        lambda day: tmp_path / f"floor-{day}.json",
    )

    assert cycle._historical_backfill_dates(
        provider_floor=floor,
        current_target_date="2026-08-31",
        daily_attempt_cap=390,
        parent_cap=130,
    ) == ["2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28"]
    assert cycle._historical_backfill_dates(
        provider_floor=floor,
        current_target_date="2026-08-31",
        daily_attempt_cap=36,
        parent_cap=130,
    ) == ["2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28"]
    assert cycle._historical_backfill_dates(
        provider_floor=floor,
        current_target_date="2026-08-31",
        daily_attempt_cap=390,
        parent_cap=1,
    ) == ["2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28"]
    assert (
        cycle._historical_backfill_parent_slot_limit(
            daily_attempt_cap=36,
            parent_cap=130,
        )
        == 2
    )
    assert (
        cycle._historical_backfill_parent_slot_limit(
            daily_attempt_cap=390,
            parent_cap=1,
        )
        == 0
    )


def test_execution_consumer_rejects_floor_after_physical_budget_day(
    monkeypatch,
) -> None:
    floor = {
        "target_date": "2026-09-01",
        "floor_content_sha256": "a" * 64,
    }
    monkeypatch.setattr(
        quality,
        "validate_micro_reversion_provider_ablation_floor_artifact",
        lambda *_args, **_kwargs: floor,
    )

    with pytest.raises(
        ValueError,
        match="current_execution_provider_floor_time_binding_invalid",
    ):
        cycle._validate_current_provider_preflight_commitments(
            report={"provider_budget": {"execution_date": "2026-08-31"}},
            target_date="2026-08-25",
            materialized_report={},
            provider_ablation_floor_artifact=floor,
            checkpoint_artifact=None,
        )


def test_execution_floor_locator_accepts_exact_later_as_of_generation(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        cycle,
        "provider_ablation_floor_path",
        lambda day: (
            tmp_path / f"micro_reversion_provider_ablation_sample_floor_{day}.json"
        ),
    )
    later_path = cycle.provider_ablation_floor_path("2026-08-31").absolute()

    assert (
        cycle._execution_provider_floor_logical_path(
            {"provider_ablation_sample_floor_path": str(later_path)},
            execution_target_date="2026-08-25",
        )
        == later_path
    )
    assert (
        cycle._execution_provider_floor_logical_path(
            {
                "provider_ablation_sample_floor_path": str(
                    cycle.provider_ablation_floor_path("2026-08-25").absolute()
                )
            },
            execution_target_date="2026-08-31",
        )
        is None
    )


def test_historical_backfill_dates_retains_oldest_date_from_prior_floor(
    tmp_path,
    monkeypatch,
) -> None:
    prior_body = {
        "target_date": "2026-08-31",
        "pass": True,
        "status": "pass_provider_ablation_floor_met",
        "included_artifacts": [
            {"target_date": "2026-08-25", "parent_count": 20},
        ],
    }
    prior = {
        **prior_body,
        "floor_content_sha256": cycle._sha256(prior_body),
    }
    current_body = {
        "target_date": "2026-09-01",
        "pass": True,
        "status": "pass_provider_ablation_floor_met",
        "included_artifacts": [
            {"target_date": "2026-08-26", "parent_count": 20},
        ],
    }
    current = {
        **current_body,
        "floor_content_sha256": cycle._sha256(current_body),
    }
    prior_path = tmp_path / "floor-2026-08-31.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")
    monkeypatch.setattr(
        cycle,
        "provider_ablation_floor_path",
        lambda day: (
            prior_path if day == "2026-08-31" else tmp_path / f"floor-{day}.json"
        ),
    )

    assert cycle._historical_backfill_dates(
        provider_floor=current,
        current_target_date="2026-09-01",
        daily_attempt_cap=390,
        parent_cap=130,
    ) == ["2026-08-25", "2026-08-26"]


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        ("offline_three_arm_execution_complete", True),
        ("offline_three_arm_execution_batch_complete", False),
    ),
)
def test_historical_backfill_skips_only_exact_complete_execution(
    tmp_path,
    monkeypatch,
    status,
    expected,
) -> None:
    execution_path = tmp_path / "execution.json"
    execution_path.write_text(json.dumps({"status": status}), encoding="utf-8")
    context = {
        "paths": {"execution": execution_path},
        "labels": {},
        "bridge": {},
        "materialized": {},
        "source_bundle": {},
        "prepared": {},
        "paired": {},
        "checkpoint": {},
    }
    monkeypatch.setattr(
        cycle, "_validated_execution_rows", lambda *_args, **_kwargs: []
    )
    monkeypatch.setattr(
        cycle,
        "_load_json_auto",
        lambda _path: {"target_date": "2026-08-25", "status": status},
    )

    assert (
        cycle._historical_backfill_already_covered(
            target_date="2026-08-25",
            context=context,
            provider_floor={},
        )
        is expected
    )


def test_historical_backfill_resumes_failure_only_after_checkpoint_binding(
    tmp_path,
    monkeypatch,
) -> None:
    status = "offline_three_arm_execution_complete_with_failures_or_exclusions"
    execution_path = tmp_path / "execution.json"
    execution_path.write_text(json.dumps({"status": status}), encoding="utf-8")
    context = {
        "paths": {"execution": execution_path},
        "labels": {"labels": [{"label_id": "label-1"}]},
        "bridge": {},
        "materialized": {},
        "source_bundle": {},
        "prepared": {},
        "paired": {},
        "checkpoint": {"schema": "checkpoint"},
    }
    report = {"target_date": "2026-08-25", "status": status}
    monkeypatch.setattr(cycle, "_load_json_auto", lambda _path: report)
    monkeypatch.setattr(
        cycle,
        "_validated_execution_rows",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("execution_report_not_complete_provider_verified")
        ),
    )
    checkpoint_validations: list[dict] = []
    monkeypatch.setattr(
        quality,
        "validate_current_micro_reversion_checkpoint_companion",
        lambda **kwargs: checkpoint_validations.append(kwargs),
    )

    assert (
        cycle._historical_backfill_already_covered(
            target_date="2026-08-25",
            context=context,
            provider_floor={},
        )
        is False
    )
    assert checkpoint_validations == [
        {
            "report": report,
            "checkpoint_artifact": context["checkpoint"],
            "materialized_report": context["materialized"],
            "outcome_labels": context["labels"]["labels"],
        }
    ]


def test_bounded_historical_backfill_skips_covered_and_uses_fake_runner(
    monkeypatch,
) -> None:
    target_dates = ["2026-08-25", "2026-08-26", "2026-08-27"]
    floor = {
        "target_date": "2026-08-31",
        "floor_content_sha256": "a" * 64,
    }
    calls: list[str] = []

    monkeypatch.setattr(
        cycle,
        "_historical_backfill_dates",
        lambda **_kwargs: target_dates,
    )
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_floor",
        lambda **_kwargs: (Path("/canonical/floor-2026-08-31.json"), floor),
    )

    def context(target_date, **_kwargs):
        return {
            "paths": {"execution": Path(f"/{target_date}.json")},
            "materialized": {"report_content_sha256": "b" * 64},
            "source_bundle": {},
            "prepared": {},
            "bridge": {},
            "paired": {},
            "labels": {},
            "checkpoint": {},
            "provider_authority_binding": {
                "provider_pricing_artifact_content_sha256": "c" * 64
            },
        }

    monkeypatch.setattr(cycle, "_load_historical_backfill_context", context)
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_already_covered",
        lambda target_date, **_kwargs: target_date == "2026-08-25",
    )
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_orphan_reservation_findings",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        cycle,
        "_pre_provider_capacity_recheck",
        lambda **_kwargs: ({"large_artifact_growth_allowed": True}, None),
    )
    monkeypatch.setattr(
        cycle,
        "_provider_execute_command",
        lambda *, target_date, **_kwargs: ["fake-provider", target_date],
    )
    monkeypatch.setattr(
        cycle,
        "_load_json_auto",
        lambda path: {
            "target_date": path.stem,
            "new_result_count": 3,
            "provider_call_performed": True,
        },
    )
    monkeypatch.setattr(
        cycle,
        "_validate_current_execution_artifact",
        lambda **_kwargs: [],
    )

    def runner(command):
        calls.append(command[-1])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    steps, admissions, selected, performed, blockers = (
        cycle._run_bounded_historical_provider_backfill(
            current_target_date="2026-08-31",
            current_floor=floor,
            write=True,
            daily_attempt_cap=36,
            daily_usd_cap=Decimal("1"),
            daily_usd_cap_text="1",
            parent_cap=130,
            command_runner=runner,
        )
    )

    assert calls == ["2026-08-26", "2026-08-27"]
    assert [step["name"] for step in steps] == [
        "bounded_provider_backfill:2026-08-26",
        "bounded_provider_backfill:2026-08-27",
    ]
    assert selected == 2
    assert performed is True
    assert blockers == []
    assert [row["status"] for row in admissions] == [
        "already_covered_exact_no_call",
        "backfill_parent_committed",
        "backfill_parent_committed",
    ]
    assert all(row["runtime_effect"] is False for row in admissions)
    assert all(row["actual_order_submitted"] is False for row in admissions)
    assert all(row["broker_order_forbidden"] is True for row in admissions)


def test_bounded_historical_backfill_hash_mismatch_is_zero_call_fail_closed(
    monkeypatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_dates",
        lambda **_kwargs: ["2026-08-25"],
    )
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_floor",
        lambda **_kwargs: (_ for _ in ()).throw(
            ValueError("historical_backfill_execution_hash_mismatch")
        ),
    )

    result = cycle._run_bounded_historical_provider_backfill(
        current_target_date="2026-08-31",
        current_floor={"target_date": "2026-08-31"},
        write=True,
        daily_attempt_cap=390,
        daily_usd_cap=Decimal("1"),
        daily_usd_cap_text="1",
        parent_cap=130,
        command_runner=lambda command: calls.append(command),
    )

    assert calls == []
    assert result[0] == []
    assert result[2] == 0
    assert result[3] is False
    assert result[4] == [
        "historical_provider_backfill_blocked:2026-08-25:ValueError:"
        "historical_backfill_execution_hash_mismatch"
    ]


def test_bounded_historical_backfill_floor_discovery_hash_mismatch_is_zero_call(
    tmp_path,
    monkeypatch,
) -> None:
    corrupt_path = tmp_path / "floor-2026-08-31.json"
    corrupt_path.write_text(
        json.dumps(
            {
                "target_date": "2026-08-31",
                "pass": True,
                "status": "pass_provider_ablation_floor_met",
                "included_artifacts": [],
                "floor_content_sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    current_body = {
        "target_date": "2026-09-01",
        "pass": True,
        "status": "pass_provider_ablation_floor_met",
        "included_artifacts": [],
    }
    current = {
        **current_body,
        "floor_content_sha256": cycle._sha256(current_body),
    }
    monkeypatch.setattr(
        cycle,
        "provider_ablation_floor_path",
        lambda day: (
            corrupt_path if day == "2026-08-31" else tmp_path / f"floor-{day}.json"
        ),
    )
    calls: list[list[str]] = []

    result = cycle._run_bounded_historical_provider_backfill(
        current_target_date="2026-09-01",
        current_floor=current,
        write=True,
        daily_attempt_cap=390,
        daily_usd_cap=Decimal("1"),
        daily_usd_cap_text="1",
        parent_cap=130,
        command_runner=lambda command: calls.append(command),
    )

    assert calls == []
    assert result[0] == []
    assert result[2] == 0
    assert result[3] is False
    assert result[4] == [
        "historical_provider_backfill_discovery_blocked:ValueError:"
        "historical_backfill_floor_hash_or_date_mismatch"
    ]


def test_historical_backfill_checkpoint_keeps_first_bound_floor_across_days(
    tmp_path,
    monkeypatch,
) -> None:
    target_date = "2026-08-25"
    current_target_date = "2026-08-31"
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text("{}", encoding="utf-8")
    floor_paths = {
        day: tmp_path / f"floor-{day}.json"
        for day in (target_date, current_target_date)
    }
    blocked_body = {
        "target_date": target_date,
        "pass": False,
        "included_artifacts": [],
    }
    blocked = {
        **blocked_body,
        "floor_content_sha256": cycle._sha256(blocked_body),
    }
    floor_paths[target_date].write_text(json.dumps(blocked), encoding="utf-8")
    passing_body = {
        "target_date": current_target_date,
        "pass": True,
        "included_artifacts": [
            {"target_date": target_date, "parent_count": 4},
        ],
    }
    passing = {
        **passing_body,
        "floor_content_sha256": cycle._sha256(passing_body),
    }
    monkeypatch.setattr(
        cycle,
        "_default_paths",
        lambda _day: {
            "execution": tmp_path / "missing-execution.json",
            "execution_checkpoint": checkpoint_path,
        },
    )
    monkeypatch.setattr(
        cycle,
        "provider_ablation_floor_path",
        lambda day: floor_paths.get(day, tmp_path / f"missing-floor-{day}.json"),
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_checkpoint_record_dir",
        lambda _path: tmp_path / "missing-record-dir",
    )
    monkeypatch.setattr(
        quality,
        "_load_micro_reversion_checkpoint",
        lambda *_args, **_kwargs: {
            "results": [
                {
                    "provider_ablation_sample_floor_content_sha256": passing[
                        "floor_content_sha256"
                    ]
                }
            ]
        },
    )

    selected_path, selected_floor = cycle._historical_backfill_floor(
        target_date=target_date,
        current_target_date=current_target_date,
        current_floor=passing,
    )

    assert selected_path == floor_paths[current_target_date].absolute()
    assert selected_floor == passing


def test_historical_backfill_checkpoint_accepts_valid_partial_superseded_by_pass(
    monkeypatch,
) -> None:
    target_date = "2026-08-25"
    floor_hash = "f" * 64
    request = {
        "paired_replay_parent_id": "parent-1",
        "paired_replay_id": "request-1",
        "micro_reversion_replay_arm": "replay_control_exact_no_micro",
        "candidate": {"provider": "openai", "model": "gpt-test"},
    }
    first_attempt = {
        "attempt_number": 1,
        "provider_provenance": {
            "provider_budget_reservation_id": "provider-reservation-" + "a" * 32,
            "provider_budget_attempt_identity_sha256": "b" * 64,
        },
    }
    second_attempt = {
        "attempt_number": 2,
        "provider_provenance": {
            "provider_budget_reservation_id": "provider-reservation-" + "c" * 32,
            "provider_budget_attempt_identity_sha256": "d" * 64,
        },
    }

    def result(status: str, attempts: list[dict]) -> dict:
        content = {
            "paired_replay_parent_id": "parent-1",
            "paired_replay_id": "request-1",
            "micro_reversion_replay_arm": "replay_control_exact_no_micro",
            "provider_ablation_sample_floor_content_sha256": floor_hash,
            "replay_result": {"status": status, "candidate_attempts": attempts},
        }
        return {
            "result_id": "micro-result-" + quality._sha256(content)[:24],
            **content,
        }

    partial = result("provider_capacity_blocked_before_retry", [first_attempt])
    completed = result("pass", [first_attempt, second_attempt])
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda _report: [request],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_reusable_results",
        lambda **_kwargs: [completed],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_partial_retry_states",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        quality,
        "_validate_current_ablation_semantic_authority",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "validate_current_micro_reversion_candidate_response_chain",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "_validated_micro_reversion_result_capacity_receipts",
        lambda **_kwargs: [],
    )

    assert cycle._checkpoint_provider_reservation_bindings(
        target_date=target_date,
        context={
            "materialized": {},
            "labels": {"labels": []},
            "checkpoint": {
                "schema": quality.MICRO_REVERSION_CHECKPOINT_RECONSTRUCTED_SCHEMA,
                "checkpoint_record_count": 2,
                "results": [partial, completed],
            },
        },
        provider_floor={"floor_content_sha256": floor_hash},
    ) == {
        ("provider-reservation-" + "a" * 32, "b" * 64): {
            "request_id": "request-1",
            "parent_id": "parent-1",
            "arm": "replay_control_exact_no_micro",
            "provider": "openai",
            "model": "gpt-test",
            "attempt_number": 1,
        },
        ("provider-reservation-" + "c" * 32, "d" * 64): {
            "request_id": "request-1",
            "parent_id": "parent-1",
            "arm": "replay_control_exact_no_micro",
            "provider": "openai",
            "model": "gpt-test",
            "attempt_number": 2,
        },
    }


def test_historical_backfill_checkpoint_terminal_schema_failure_is_not_resumable(
    monkeypatch,
) -> None:
    floor_hash = "f" * 64
    request = {
        "paired_replay_parent_id": "parent-1",
        "paired_replay_id": "request-1",
        "micro_reversion_replay_arm": "replay_control_exact_no_micro",
        "candidate": {"provider": "openai", "model": "gpt-test"},
    }
    content = {
        "paired_replay_parent_id": "parent-1",
        "paired_replay_id": "request-1",
        "micro_reversion_replay_arm": "replay_control_exact_no_micro",
        "provider_ablation_sample_floor_content_sha256": floor_hash,
        "replay_result": {
            "status": "schema_rejected",
            "candidate_attempts": [
                {
                    "attempt_number": 1,
                    "provider_provenance": {
                        "provider_budget_reservation_id": (
                            "provider-reservation-" + "a" * 32
                        ),
                        "provider_budget_attempt_identity_sha256": "b" * 64,
                    },
                }
            ],
        },
    }
    failed = {
        "result_id": "micro-result-" + quality._sha256(content)[:24],
        **content,
    }
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda _report: [request],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_reusable_results",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_partial_retry_states",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        quality,
        "_validate_current_ablation_semantic_authority",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "_validate_current_micro_reversion_candidate_attempt_prefix",
        lambda **_kwargs: None,
    )

    with pytest.raises(
        ValueError,
        match="historical_backfill_checkpoint_terminal_attempt_not_resumable",
    ):
        cycle._checkpoint_provider_reservation_bindings(
            target_date="2026-08-25",
            context={
                "materialized": {},
                "labels": {"labels": []},
                "checkpoint": {
                    "schema": quality.MICRO_REVERSION_CHECKPOINT_RECONSTRUCTED_SCHEMA,
                    "checkpoint_record_count": 1,
                    "results": [failed],
                },
            },
            provider_floor={"floor_content_sha256": floor_hash},
        )


@pytest.mark.parametrize("checkpoint_bound", (False, True))
def test_historical_backfill_prior_physical_ledger_requires_checkpoint_binding(
    tmp_path,
    monkeypatch,
    checkpoint_bound,
) -> None:
    from src.engine.scalping.micro_reversion import provider_budget

    target_date = "2026-08-25"
    physical_day = date(2026, 8, 26)
    ledger_path = tmp_path / (
        f"ai_micro_reversion_provider_budget_{physical_day.isoformat()}.jsonl"
    )
    ledger_path.write_text("reservation-present\n", encoding="utf-8")
    summary_path = tmp_path / (
        f"ai_micro_reversion_provider_budget_{physical_day.isoformat()}.json"
    )
    request = {
        "paired_replay_parent_id": "parent-1",
        "paired_replay_id": "request-1",
        "micro_reversion_replay_arm": "replay_control_exact_no_micro",
        "candidate": {"provider": "openai", "model": "gpt-test"},
    }
    reservation_id = "provider-reservation-" + "a" * 32
    attempt_hash = "b" * 64
    reservation = {
        "execution_date": physical_day.isoformat(),
        "reservation_id": reservation_id,
        "attempt_identity": {
            "target_date": target_date,
            "parent_id": "parent-1",
            "request_id": "request-1",
            "arm": "replay_control_exact_no_micro",
            "provider": "openai",
            "model": "gpt-test",
            "attempt_number": 1,
        },
        "attempt_identity_sha256": attempt_hash,
        "settled": True,
    }
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_budget_ledger_path",
        lambda day: (
            ledger_path
            if day == physical_day.isoformat()
            else tmp_path / f"{day}.jsonl"
        ),
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_budget_summary_path",
        lambda day: (
            summary_path
            if day == physical_day.isoformat()
            else tmp_path / f"{day}.json"
        ),
    )
    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        lambda _report: [request],
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_provider_checkpoint_bindings",
        lambda **_kwargs: (
            {
                (reservation_id, attempt_hash): {
                    "request_id": "request-1",
                    "parent_id": "parent-1",
                    "arm": "replay_control_exact_no_micro",
                    "provider": "openai",
                    "model": "gpt-test",
                    "attempt_number": 1,
                }
            }
            if checkpoint_bound
            else {}
        ),
    )
    monkeypatch.setattr(
        provider_budget,
        "load_reviewed_pricing_artifact",
        lambda *_args, **_kwargs: object(),
    )

    class FakeBudget:
        def __init__(self, **_kwargs):
            pass

        def validated_reservation_census_read_only(self):
            return (reservation,)

    monkeypatch.setattr(provider_budget, "ProviderBudgetLedger", FakeBudget)

    findings = cycle._historical_backfill_orphan_reservation_findings(
        target_date=target_date,
        context={
            "materialized": {},
            "labels": {"labels": []},
            "paths": {"provider_pricing": tmp_path / "pricing.json"},
            "checkpoint": None,
        },
        provider_floor={"floor_content_sha256": "c" * 64},
        daily_attempt_cap=390,
        daily_usd_cap=Decimal("1"),
        physical_execution_date=physical_day,
    )

    assert findings == (
        []
        if checkpoint_bound
        else ["prior_provider_ledger_orphan_reservation:2026-08-26:request-1:1"]
    )


def test_bounded_historical_backfill_orphan_reservation_is_zero_call(
    monkeypatch,
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_dates",
        lambda **_kwargs: ["2026-08-25"],
    )
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_floor",
        lambda **_kwargs: (Path("floor.json"), {"target_date": "2026-08-26"}),
    )
    context = {
        "paths": {},
        "materialized": {},
        "source_bundle": {},
        "prepared": {},
        "bridge": {},
        "paired": {},
        "labels": {},
        "checkpoint": None,
        "provider_authority_binding": None,
    }
    monkeypatch.setattr(
        cycle,
        "_load_historical_backfill_context",
        lambda **_kwargs: context,
    )
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_already_covered",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(
        cycle,
        "_historical_backfill_orphan_reservation_findings",
        lambda **_kwargs: [
            "prior_provider_ledger_orphan_reservation:2026-08-26:request-1:1"
        ],
    )

    _steps, _admissions, selected, performed, blockers = (
        cycle._run_bounded_historical_provider_backfill(
            current_target_date="2026-08-26",
            current_floor={
                "target_date": "2026-08-26",
                "pass": True,
                "status": "pass_provider_ablation_floor_met",
            },
            write=True,
            daily_attempt_cap=390,
            daily_usd_cap=Decimal("1"),
            daily_usd_cap_text="1",
            parent_cap=130,
            command_runner=lambda command: calls.append(command),
        )
    )

    assert calls == []
    assert selected == 0
    assert performed is False
    assert blockers == [
        "historical_provider_backfill_blocked:2026-08-25:ValueError:"
        "prior_provider_ledger_orphan_reservation:2026-08-26:request-1:1"
    ]


def test_provider_ablation_floor_fails_closed_on_tampered_history(monkeypatch):
    def validate(report):
        if report.get("_valid") is not True:
            raise ValueError("tampered")
        return report["_requests"]

    monkeypatch.setattr(
        quality,
        "_validate_micro_reversion_materialized_report",
        validate,
    )
    monkeypatch.setattr(
        cycle,
        "_validate_current_materialized_source_lineage",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_materialized_request_census_sha256",
        lambda report: cycle._sha256(report["request_ids"]),
    )
    valid = _sample_floor_materialized_report(
        "2026-08-25", parent_start=0, parent_count=4
    )
    tampered = _sample_floor_materialized_report(
        "2026-08-26", parent_start=4, parent_count=4, valid=False
    )
    result = cycle._provider_ablation_sample_floor_from_reports(
        target_date="2026-08-26",
        materialized_reports=[
            (
                "2026-08-25",
                Path("valid.json"),
                valid,
                _sample_floor_companions("2026-08-25"),
            ),
            (
                "2026-08-26",
                Path("tampered.json"),
                tampered,
                _sample_floor_companions("2026-08-26"),
            ),
        ],
    )
    assert result["pass"] is False
    assert result["status"] == "blocked_invalid_materialized_history"
    assert any(
        finding.startswith("materialized_contract_invalid:2026-08-26")
        for finding in result["contract_findings"]
    )


def test_provider_ablation_floor_accepts_bound_empty_day_without_counting_it(
    monkeypatch,
) -> None:
    empty = _sample_floor_materialized_report(
        "2026-08-26", parent_start=0, parent_count=0
    )
    lineage_calls = []
    monkeypatch.setattr(
        cycle,
        "_validate_current_materialized_source_lineage",
        lambda **kwargs: lineage_calls.append(kwargs),
    )
    result = cycle._provider_ablation_sample_floor_from_reports(
        target_date="2026-08-26",
        materialized_reports=[
            (
                "2026-08-26",
                Path("empty.json"),
                empty,
                _sample_floor_companions("2026-08-26"),
            )
        ],
    )

    assert result["pass"] is False
    assert result["status"] == "keep_collecting_provider_ablation_floor"
    assert result["contract_findings"] == []
    assert result["observed_trading_days"] == 0
    assert len(lineage_calls) == 1
    assert result["included_artifacts"][0]["lineage_status"] == (
        "full_current_empty_source_lineage_validated_not_counted"
    )


def test_provider_ablation_floor_rejects_detached_empty_day() -> None:
    empty = _sample_floor_materialized_report(
        "2026-08-26", parent_start=0, parent_count=0
    )

    result = cycle._provider_ablation_sample_floor_from_reports(
        target_date="2026-08-26",
        materialized_reports=[("2026-08-26", Path("empty.json"), empty, {})],
    )

    assert result["status"] == "blocked_invalid_materialized_history"
    assert any(
        "provider_floor_lineage_companions_missing" in finding
        for finding in result["contract_findings"]
    )


def test_provider_ablation_floor_excludes_pre_source_contract_artifact() -> None:
    pre_contract = _sample_floor_materialized_report(
        "2026-08-25", parent_start=0, parent_count=1, valid=False
    )

    result = cycle._provider_ablation_sample_floor_from_reports(
        target_date="2026-08-26",
        materialized_reports=[
            ("2026-08-25", Path("pre-contract.json"), pre_contract, {})
        ],
    )

    assert result["status"] == "keep_collecting_provider_ablation_floor"
    assert result["contract_findings"] == []
    assert result["included_artifacts"] == []
    assert result["excluded_pre_source_contract_artifact_dates"] == ["2026-08-25"]


def test_pre_provider_capacity_recheck_catches_state_flip(tmp_path, monkeypatch):
    calls = []

    def capacity(**_kwargs):
        calls.append(len(calls) + 1)
        allowed = len(calls) == 1
        return {
            "schema": cycle.STORAGE_CAPACITY_GROWTH_GATE_SCHEMA,
            "target_date": "2026-08-25",
            "status": (
                "pass_capacity_available"
                if allowed
                else "blocked_critical_or_unknown_capacity"
            ),
            "large_artifact_growth_allowed": allowed,
            "effective_capacity_state": "healthy" if allowed else "critical",
        }

    monkeypatch.setattr(cycle, "evaluate_large_artifact_capacity_gate", capacity)
    selected_paths = {
        "capacity_status": tmp_path / "capacity.json",
        "prepared": tmp_path / "prepared.json",
    }
    initial = cycle._capacity_gate_fail_closed(
        target=date.fromisoformat("2026-08-25"),
        target_date="2026-08-25",
        selected_paths=selected_paths,
    )
    recheck, blocker = cycle._pre_provider_capacity_recheck(
        target=date.fromisoformat("2026-08-25"),
        target_date="2026-08-25",
        selected_paths=selected_paths,
    )

    assert initial["large_artifact_growth_allowed"] is True
    assert recheck["large_artifact_growth_allowed"] is False
    assert blocker == (
        "large_artifact_growth_blocked_pre_provider:"
        "blocked_critical_or_unknown_capacity"
    )
    assert calls == [1, 2]


def test_existing_economic_reference_reuse_binds_exact_source_manifest(
    tmp_path,
    monkeypatch,
):
    target_date = "2026-08-18"
    manifest_path = tmp_path / "economic-reference-sources.json"
    manifest_path.write_text('{"schema":"test_manifest_v1"}\n', encoding="utf-8")
    raw = manifest_path.read_bytes()
    report = {
        "target_date": target_date,
        "status": "pass",
        "tuning_input_allowed": True,
        "source_manifest": {
            "resolved_path": str(manifest_path.resolve()),
            "sha256": cycle._sha256(raw),
            "size_bytes": len(raw),
        },
    }
    monkeypatch.setattr(
        cycle,
        "_economic_outputs",
        lambda _report: ({"verified": True}, {"verified": True}),
    )

    cycle._validate_existing_economic_reference(
        report,
        target_date=target_date,
        manifest_path=manifest_path,
    )

    manifest_path.write_text('{"schema":"tampered_manifest_v1"}\n', encoding="utf-8")
    with pytest.raises(
        ValueError,
        match="existing_economic_reference_source_manifest_mismatch",
    ):
        cycle._validate_existing_economic_reference(
            report,
            target_date=target_date,
            manifest_path=manifest_path,
        )


def test_empty_materialized_receipt_is_valid_terminal_no_provider_work() -> None:
    target_date = "2026-08-18"
    report = {
        "schema": quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA,
        "target_date": target_date,
        "status": "no_micro_reversion_eligible_requests",
        "materialization_count": 0,
        "request_count": 0,
        "request_ids": [],
        "materializations": [],
        "requests": [],
        "provider_call_performed": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report["report_content_sha256"] = cycle._content_hash(
        report, "report_content_sha256"
    )

    assert (
        cycle._validate_materialized_step_artifact(report, target_date=target_date) == 0
    )

    tampered = dict(report)
    tampered["request_count"] = 1
    tampered["report_content_sha256"] = cycle._content_hash(
        tampered, "report_content_sha256"
    )
    with pytest.raises(ValueError, match="materialized_step_census_mismatch"):
        cycle._validate_materialized_step_artifact(
            tampered,
            target_date=target_date,
        )


def test_observer_canary_loads_exact_date_early_stop_and_preserves_cause(
    tmp_path,
) -> None:
    latest = tmp_path / "latest.json"
    latest.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_canary_monitor_v1",
                "generated_at": "2026-08-19T09:03:55+09:00",
                "canary_guard": {
                    "status": "stop_required",
                    "stop_required": True,
                    "stop_reasons": [
                        "nonzero_stop_metric:observation_queue_full_count=82"
                    ],
                    "raw_row_exclusion_required": False,
                    "source_quality_row_exclusions": [],
                },
                "collector_snapshot": {
                    "collector_lifecycle": "closed",
                    "selection_authority": False,
                    "trading_runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "observation_queue_full_count": 82,
                    "observation_dropped_envelope_count": 82,
                    "depth_queue_full_count": 0,
                    "depth_dropped_envelope_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    diagnostic = cycle._observer_canary_diagnostic(
        target_date="2026-08-19",
        latest_path=latest,
        daily_path=tmp_path / "missing-daily.json",
    )

    assert diagnostic["status"] == "stop_required"
    assert diagnostic["stop_required"] is True
    assert diagnostic["queue_loss_census"] == {
        "observation_queue_full_count": 82,
        "observation_dropped_envelope_count": 82,
        "depth_queue_full_count": 0,
        "depth_dropped_envelope_count": 0,
    }
    assert diagnostic["runtime_effect"] is False
    assert diagnostic["actual_order_submitted"] is False
    assert cycle._observer_provider_gate_blocker(diagnostic) == (
        "micro_observer_canary_stop_required"
    )


def test_observer_provider_gate_blocks_unscoped_loss_but_not_clean_canary():
    assert (
        cycle._observer_provider_gate_blocker(
            {"source_path": None, "status": "missing_exact_date_canary"}
        )
        == "micro_observer_canary_missing_exact_date_canary"
    )
    assert (
        cycle._observer_provider_gate_blocker(
            {"source_path": "/tmp/canary.json", "status": "row_exclusion_required"}
        )
        == "micro_observer_canary_row_exclusion_required"
    )
    assert (
        cycle._observer_provider_gate_blocker(
            {"source_path": "/tmp/canary.json", "status": "pass"}
        )
        is None
    )
    assert (
        cycle._observer_provider_gate_blocker(
            {"source_path": "/tmp/canary.json", "status": "warming_up"}
        )
        == "micro_observer_canary_warming_up"
    )


def test_observer_stage_gate_keeps_local_labels_but_holds_provider_and_r3():
    blocked = cycle._observer_source_only_stage_gate(
        {"source_path": "/tmp/canary.json", "status": "stop_required"}
    )

    assert blocked["observer_blocks_action_neutral_label_generation"] is False
    assert blocked["observer_blocks_provider_floor_materialization"] is False
    assert blocked["observer_blocks_provider_replay"] is True
    assert blocked["observer_blocks_r3_promotion"] is True
    assert blocked["blocker_code"] == "micro_observer_canary_stop_required"
    assert blocked["runtime_effect"] is False
    assert blocked["actual_order_submitted"] is False
    assert blocked["broker_order_forbidden"] is True

    clean = cycle._observer_source_only_stage_gate(
        {"source_path": "/tmp/canary.json", "status": "pass"}
    )
    assert clean["observer_blocks_action_neutral_label_generation"] is False
    assert clean["observer_blocks_provider_floor_materialization"] is False
    assert clean["observer_blocks_provider_replay"] is False
    assert clean["observer_blocks_r3_promotion"] is False
    assert clean["blocker_code"] is None


def test_observer_canary_requires_running_or_reconciled_closed_lifecycle(
    tmp_path,
) -> None:
    latest = tmp_path / "latest.json"
    payload = {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": "2026-08-19T15:31:00+09:00",
        "canary_guard": {
            "status": "stopped_clean",
            "stop_required": False,
            "stop_reasons": [],
            "raw_row_exclusion_required": False,
            "source_quality_row_exclusions": [],
        },
        "collector_snapshot": {
            "collector_lifecycle": "closed",
            "reference_reconciliation_completed": False,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    latest.write_text(json.dumps(payload), encoding="utf-8")

    invalid = cycle._observer_canary_diagnostic(
        target_date="2026-08-19",
        latest_path=latest,
        daily_path=tmp_path / "missing-daily.json",
    )
    assert invalid["status"] == "invalid_exact_date_canary_contract"
    assert cycle._observer_provider_gate_blocker(invalid) == (
        "micro_observer_canary_invalid_exact_date_canary_contract"
    )

    payload["collector_snapshot"]["reference_reconciliation_completed"] = True
    latest.write_text(json.dumps(payload), encoding="utf-8")
    valid = cycle._observer_canary_diagnostic(
        target_date="2026-08-19",
        latest_path=latest,
        daily_path=tmp_path / "missing-daily.json",
    )
    assert valid["status"] == "pass"


def test_observer_canary_parses_and_hashes_one_raw_snapshot(
    tmp_path,
    monkeypatch,
) -> None:
    latest = tmp_path / "latest.json"
    raw = json.dumps(
        {
            "schema": "scalp_micro_reversion_canary_monitor_v1",
            "generated_at": "2026-08-19T15:31:00+09:00",
            "canary_guard": {
                "status": "healthy_observer_canary",
                "stop_required": False,
                "stop_reasons": [],
                "raw_row_exclusion_required": False,
                "source_quality_row_exclusions": [],
            },
            "collector_snapshot": {
                "collector_lifecycle": "running",
                "selection_authority": False,
                "trading_runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
    ).encode()
    latest.write_bytes(raw)
    original_read_bytes = Path.read_bytes
    read_count = 0

    def counted_read_bytes(path: Path) -> bytes:
        nonlocal read_count
        if path == latest:
            read_count += 1
            if read_count > 1:
                raise AssertionError("canary source was read more than once")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    diagnostic = cycle._observer_canary_diagnostic(
        target_date="2026-08-19",
        latest_path=latest,
        daily_path=tmp_path / "missing-daily.json",
    )

    assert diagnostic["status"] == "pass"
    assert diagnostic["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert read_count == 1


def test_source_gap_diagnostics_names_bridge_and_lifecycle_root_causes() -> None:
    target_date = "2026-08-19"
    bridge_report = {
        "target_date": target_date,
        "summary": {
            "micro_context_eligible_primary_episode_count": 0,
            "exclusion_counts": {
                "past_market_row_missing": 870,
                "integrated_route_proof_missing": 17,
            },
        },
        **cycle.OFFLINE_AUTHORITY,
    }
    bridge_report["report_content_sha256"] = cycle._content_hash(
        bridge_report, "report_content_sha256"
    )
    lifecycle_report = {
        "target_date": target_date,
        "promotion_evidence_eligible_count": 0,
        "broker_execution_provenance_gap_count": 7,
        **cycle.OFFLINE_AUTHORITY,
    }
    lifecycle_report["artifact_content_sha256"] = cycle._content_hash(
        lifecycle_report, "artifact_content_sha256"
    )
    diagnostics = cycle._source_only_gap_diagnostics(
        target_date=target_date,
        observer_canary={
            "status": "stop_required",
            "stop_required": True,
        },
        bridge_report=bridge_report,
        lifecycle_report=lifecycle_report,
    )

    assert diagnostics["blocker_codes"] == [
        "micro_observer_canary_stop_required",
        "micro_integrated_route_proof_missing:17",
        "main_lifecycle_broker_execution_provenance_gap:7",
    ]
    assert [row["owner"] for row in diagnostics["workorders"]] == [
        "MicroReversionForwardCollectorContinuity",
        "MicroReversionIntegratedRouteProof",
        "RuntimeExecutionReceiptCustodyRepair",
    ]
    assert all(row["runtime_effect"] is False for row in diagnostics["workorders"])
    assert all(
        row["actual_order_submitted"] is False for row in diagnostics["workorders"]
    )


def test_source_gap_diagnostics_binds_receipt_gap_to_exact_lifecycle() -> None:
    target_date = "2026-08-26"
    lifecycle_report = {
        "target_date": target_date,
        "promotion_evidence_eligible_count": 0,
        "broker_execution_provenance_gap_count": 0,
        "pipeline_lifecycle_instrumentation_gap_count": 1,
        "real_submitted_lifecycle_count": 1,
        "broker_execution_unique_count": 0,
        "source_path": "/tmp/pipeline_events_2026-08-26.jsonl.gz",
        "source_raw_sha256": "a" * 64,
        "rows": [
            {
                "main_lifecycle_id": f"mlc-{'b' * 32}",
                "attempt_id": "carry-attempt",
                "record_id": "1001",
                "stock_code": "225570",
                "venue": "KRX",
                "session_bucket": "krx_regular",
                "lifecycle_population_scope": "real_submitted",
                "broker_execution_unique_count": 0,
                "observed_actual_broker_order_submitted": False,
                "observed_real_order_evidence": True,
                "invalid_transition_reasons": [
                    "scanner_transition_must_start_lifecycle"
                ],
                "source_population_scopes": ["real_record_bound"],
            }
        ],
        **cycle.OFFLINE_AUTHORITY,
    }
    lifecycle_report["artifact_content_sha256"] = cycle._content_hash(
        lifecycle_report, "artifact_content_sha256"
    )

    diagnostics = cycle._source_only_gap_diagnostics(
        target_date=target_date,
        observer_canary={"status": "pass"},
        bridge_report=None,
        lifecycle_report=lifecycle_report,
    )

    assert diagnostics["lifecycle_receipt_custody_gap_example_count"] == 1
    example = diagnostics["lifecycle_receipt_custody_gap_examples"][0]
    assert example["main_lifecycle_id"] == f"mlc-{'b' * 32}"
    assert example["invalid_transition_reasons"] == [
        "scanner_transition_must_start_lifecycle"
    ]
    assert diagnostics["lifecycle_receipt_custody_gap_examples_sha256"] == (
        cycle._sha256(diagnostics["lifecycle_receipt_custody_gap_examples"])
    )
    assert diagnostics["lifecycle_source_raw_sha256"] == "a" * 64


def test_source_gap_diagnostics_hold_replay_until_queue_loss_has_scoped_receipt():
    bridge_report = {
        "target_date": "2026-08-20",
        "summary": {
            "micro_context_eligible_primary_episode_count": 3,
            "exclusion_counts": {
                "past_market_row_missing": 2,
                "integrated_route_proof_missing": 0,
            },
        },
        **cycle.OFFLINE_AUTHORITY,
    }
    bridge_report["report_content_sha256"] = cycle._content_hash(
        bridge_report, "report_content_sha256"
    )
    lifecycle_report = {
        "target_date": "2026-08-20",
        "promotion_evidence_eligible_count": 1,
        "broker_execution_provenance_gap_count": 2,
        **cycle.OFFLINE_AUTHORITY,
    }
    lifecycle_report["artifact_content_sha256"] = cycle._content_hash(
        lifecycle_report, "artifact_content_sha256"
    )
    diagnostics = cycle._source_only_gap_diagnostics(
        target_date="2026-08-20",
        observer_canary={
            "status": "row_exclusion_required",
            "raw_row_exclusion_required": True,
        },
        bridge_report=bridge_report,
        lifecycle_report=lifecycle_report,
    )

    assert diagnostics["blocker_codes"] == [
        "micro_observer_canary_row_exclusion_required"
    ]
    assert [row["owner"] for row in diagnostics["workorders"]] == [
        "MicroReversionForwardCollectorContinuity"
    ]


def test_source_gap_diagnostics_surfaces_rejected_execution_and_companion_gaps():
    target_date = "2026-08-25"
    bridge_report = {
        "target_date": target_date,
        "summary": {
            "micro_context_eligible_primary_episode_count": 3,
            "exclusion_counts": {},
        },
        **cycle.OFFLINE_AUTHORITY,
    }
    bridge_report["report_content_sha256"] = cycle._content_hash(
        bridge_report, "report_content_sha256"
    )
    lifecycle_report = {
        "target_date": target_date,
        "promotion_evidence_eligible_count": 0,
        "broker_execution_provenance_gap_count": 0,
        "pipeline_lifecycle_instrumentation_gap_count": 36,
        "real_submitted_lifecycle_count": 15,
        "broker_execution_unique_count": 0,
        **cycle.OFFLINE_AUTHORITY,
    }
    lifecycle_report["artifact_content_sha256"] = cycle._content_hash(
        lifecycle_report, "artifact_content_sha256"
    )

    diagnostics = cycle._source_only_gap_diagnostics(
        target_date=target_date,
        observer_canary={"status": "pass"},
        bridge_report=bridge_report,
        lifecycle_report=lifecycle_report,
        rolling_exclusions=[
            {"reason": "execution_report_materialized_companion_binding_mismatch"},
            {"reason": "lifecycle_exact_join_missing"},
        ],
    )

    assert diagnostics["blocker_codes"] == [
        "main_lifecycle_execution_receipt_custody_gap:36"
    ]
    assert (
        diagnostics["execution_report_materialized_companion_binding_mismatch_count"]
        == 1
    )
    assert diagnostics["lifecycle_exact_join_missing_count"] == 1
    assert [row["owner"] for row in diagnostics["workorders"]] == [
        "RuntimeExecutionReceiptCustodyRepair",
        "MainAIQualityMaterializedCompanionBindingRepair",
    ]
    receipt_workorder, companion_workorder = diagnostics["workorders"]
    assert receipt_workorder["reason_codes"] == [
        "pipeline_lifecycle_instrumentation_gap_count=36",
        "real_submitted_lifecycle_count=15",
        "broker_execution_unique_count=0",
        "lifecycle_exact_join_missing_count=1",
    ]
    assert companion_workorder["reason_codes"] == [
        "execution_report_materialized_companion_binding_mismatch_count=1",
    ]


def test_source_gap_diagnostics_does_not_repair_natural_non_order_lifecycle_absence():
    diagnostics = cycle._source_only_gap_diagnostics(
        target_date="2026-08-25",
        observer_canary={"status": "pass"},
        bridge_report=None,
        lifecycle_report=None,
        rolling_exclusions=[
            {
                "target_date": "2026-08-18",
                "reason": "lifecycle_not_applicable_non_order_entry",
                "lifecycle_join_requirement": "not_applicable_non_order_entry",
                "repair_required": False,
            },
            {
                "target_date": "2026-08-19",
                "reason": "lifecycle_exact_join_missing",
                "lifecycle_join_requirement": "not_applicable_non_order_entry",
                "repair_required": False,
            },
        ],
    )

    assert diagnostics["lifecycle_exact_join_missing_count"] == 0
    assert diagnostics["natural_entry_non_order_lifecycle_not_applicable_count"] == 1
    assert diagnostics["workorders"] == []


def test_source_gap_diagnostics_does_not_bind_historical_gap_to_healthy_current_census():
    target_date = "2026-08-31"
    lifecycle_report = {
        "target_date": target_date,
        "promotion_evidence_eligible_count": 0,
        "broker_execution_provenance_gap_count": 0,
        "pipeline_lifecycle_instrumentation_gap_count": 0,
        "real_submitted_lifecycle_count": 3,
        "broker_execution_unique_count": 4,
        **cycle.OFFLINE_AUTHORITY,
    }
    lifecycle_report["artifact_content_sha256"] = cycle._content_hash(
        lifecycle_report, "artifact_content_sha256"
    )
    exclusions = [
        {
            "target_date": "2026-08-24",
            "reason": "execution_report_materialized_companion_binding_mismatch",
        }
    ]
    exclusions.extend(
        {
            "target_date": "2026-08-18",
            "reason": "lifecycle_not_applicable_non_order_entry",
            "repair_required": False,
        }
        for _ in range(7)
    )

    diagnostics = cycle._source_only_gap_diagnostics(
        target_date=target_date,
        observer_canary={"status": "pass"},
        bridge_report=None,
        lifecycle_report=lifecycle_report,
        rolling_exclusions=exclusions,
    )

    assert diagnostics["lifecycle_exact_join_missing_count"] == 0
    assert diagnostics["natural_entry_non_order_lifecycle_not_applicable_count"] == 7
    assert diagnostics[
        "execution_report_materialized_companion_binding_mismatch_dates"
    ] == ["2026-08-24"]
    assert [row["owner"] for row in diagnostics["workorders"]] == [
        "MainAIQualityMaterializedCompanionBindingRepair"
    ]
    assert diagnostics["workorders"][0]["reason_codes"] == [
        "execution_report_materialized_companion_binding_mismatch_count=1",
        "execution_report_materialized_companion_binding_mismatch_dates=2026-08-24",
    ]


def test_source_gap_diagnostics_reject_self_inconsistent_artifact_census():
    bridge_report = {
        "target_date": "2026-08-20",
        "summary": {
            "micro_context_eligible_primary_episode_count": "3",
            "exclusion_counts": {},
        },
        **cycle.OFFLINE_AUTHORITY,
    }
    bridge_report["report_content_sha256"] = cycle._content_hash(
        bridge_report, "report_content_sha256"
    )

    diagnostics = cycle._source_only_gap_diagnostics(
        target_date="2026-08-20",
        observer_canary={"status": "pass"},
        bridge_report=bridge_report,
        lifecycle_report=None,
    )

    assert diagnostics["blocker_codes"] == ["source_gap_diagnostics_contract_invalid"]
    assert diagnostics["contract_findings"] == [
        "diagnostic_census_invalid:micro_context_eligible_primary_episode_count"
    ]


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
    assert observed["daily_attempt_cap"] == cycle.DEFAULT_DAILY_ATTEMPT_CAP == 390
    assert observed["parent_cap"] == cycle.DEFAULT_PARENT_CAP == 130
    assert "economic_reference_not_verified" in capsys.readouterr().out


def test_r3_manifest_binds_one_exact_validated_r2_generation():
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    floor_bindings: list[dict[str, object]] = []
    floor_sha256 = cycle._sha256(floor_bindings)
    rolling_body = {
        "schema": cycle.ROLLING_SCHEMA,
        "target_date": target_date,
        "status": "no_joined_lifecycle_rows",
        "provider_ablation_floor_bindings": floor_bindings,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        "global_candidate_blockers": [],
        "current_run_global_blockers": [],
        "current_run_global_blockers_sha256": cycle._sha256([]),
        "blocked_pre_clear_candidate_count": 0,
        "partitions": [],
        **cycle.OFFLINE_AUTHORITY,
    }
    rolling = {
        **rolling_body,
        "artifact_content_sha256": cycle._sha256(rolling_body),
    }
    manifest_body = {
        "schema": cycle.R3_SCHEMA,
        "target_date": target_date,
        "status": "no_source_only_candidate_passed_all_gates",
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "source_provider_ablation_floor_bindings_sha256": floor_sha256,
        "source_current_run_global_blockers_sha256": cycle._sha256([]),
        "candidate_count": 0,
        "candidates": [],
        "global_candidate_blockers": [],
        "blocked_pre_clear_candidate_count": 0,
        "first_runtime_candidate_auto_apply_performed": False,
        **cycle.OFFLINE_AUTHORITY,
    }
    manifest = {
        **manifest_body,
        "artifact_content_sha256": cycle._sha256(manifest_body),
    }

    cycle._validate_r3_source_only_manifest(
        manifest,
        source_rolling_artifact=rolling,
    )

    forged_body = {
        **manifest_body,
        "source_rolling_artifact_sha256": "f" * 64,
    }
    forged = {
        **forged_body,
        "artifact_content_sha256": cycle._sha256(forged_body),
    }
    with pytest.raises(
        ValueError,
        match="r3_manifest_source_rolling_binding_mismatch",
    ):
        cycle._validate_r3_source_only_manifest(
            forged,
            source_rolling_artifact=rolling,
        )


def test_r3_manifest_rejects_self_hashed_candidate_absent_from_clean_r2():
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    floor_bindings: list[dict[str, object]] = []
    floor_sha256 = cycle._sha256(floor_bindings)
    rolling_body = {
        "schema": cycle.ROLLING_SCHEMA,
        "target_date": target_date,
        "status": "no_joined_lifecycle_rows",
        "provider_ablation_floor_bindings": floor_bindings,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        "global_candidate_blockers": [],
        "current_run_global_blockers": [],
        "current_run_global_blockers_sha256": cycle._sha256([]),
        "blocked_pre_clear_candidate_count": 0,
        "partitions": [],
        **cycle.OFFLINE_AUTHORITY,
    }
    rolling = {
        **rolling_body,
        "artifact_content_sha256": cycle._sha256(rolling_body),
    }
    fabricated_content = {
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        **cycle.OFFLINE_AUTHORITY,
    }
    fabricated_sha256 = cycle._sha256(fabricated_content)
    fabricated = {
        "candidate_id": f"main-ai-quality-{fabricated_sha256[:24]}",
        "candidate_sha256": fabricated_sha256,
        **fabricated_content,
    }
    manifest_body = {
        "schema": cycle.R3_SCHEMA,
        "target_date": target_date,
        "status": "source_only_candidates_ready",
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "source_provider_ablation_floor_bindings_sha256": floor_sha256,
        "source_current_run_global_blockers_sha256": cycle._sha256([]),
        "candidate_count": 1,
        "candidates": [fabricated],
        "global_candidate_blockers": [],
        "blocked_pre_clear_candidate_count": 0,
        "first_runtime_candidate_auto_apply_performed": False,
        **cycle.OFFLINE_AUTHORITY,
    }
    manifest = {
        **manifest_body,
        "artifact_content_sha256": cycle._sha256(manifest_body),
    }

    with pytest.raises(ValueError, match="r3_manifest_candidate_projection_mismatch"):
        cycle.validate_r3_source_only_manifest(
            manifest,
            source_rolling_artifact=rolling,
        )


def test_r3_manifest_rejects_candidate_inserted_into_historical_blocked_r2():
    target_date = cycle.CURRENT_DESIGN_ACTIVATION_DATE
    floor_bindings: list[dict[str, object]] = []
    floor_sha256 = cycle._sha256(floor_bindings)
    blocker = "historical_execution_artifact_collection_invalid:2026-08-25:tamper"
    rolling_body = {
        "schema": cycle.ROLLING_SCHEMA,
        "target_date": target_date,
        "status": "historical_execution_contract_blocked",
        "provider_ablation_floor_bindings": floor_bindings,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        "global_candidate_blockers": [blocker],
        "current_run_global_blockers": [],
        "current_run_global_blockers_sha256": cycle._sha256([]),
        "blocked_pre_clear_candidate_count": 0,
        "partitions": [],
        **cycle.OFFLINE_AUTHORITY,
    }
    rolling = {
        **rolling_body,
        "artifact_content_sha256": cycle._sha256(rolling_body),
    }
    fabricated_content = {
        "ablation_design_version": cycle.CURRENT_DESIGN_VERSION,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        **cycle.OFFLINE_AUTHORITY,
    }
    fabricated_sha256 = cycle._sha256(fabricated_content)
    fabricated = {
        "candidate_id": f"main-ai-quality-{fabricated_sha256[:24]}",
        "candidate_sha256": fabricated_sha256,
        **fabricated_content,
    }
    manifest_body = {
        "schema": cycle.R3_SCHEMA,
        "target_date": target_date,
        "status": "source_only_candidate_blocked_invalid_historical_execution",
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "source_provider_ablation_floor_bindings_sha256": floor_sha256,
        "source_current_run_global_blockers_sha256": cycle._sha256([]),
        "candidate_count": 1,
        "candidates": [fabricated],
        "global_candidate_blockers": [blocker],
        "blocked_pre_clear_candidate_count": 0,
        "first_runtime_candidate_auto_apply_performed": False,
        **cycle.OFFLINE_AUTHORITY,
    }
    manifest = {
        **manifest_body,
        "artifact_content_sha256": cycle._sha256(manifest_body),
    }

    with pytest.raises(ValueError, match="r3_manifest_candidate_projection_mismatch"):
        cycle.validate_r3_source_only_manifest(
            manifest,
            source_rolling_artifact=rolling,
        )
