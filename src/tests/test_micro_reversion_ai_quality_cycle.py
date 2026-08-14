from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.engine.scalping import ai_decision_quality as quality
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
    control_ev: float = 0.10,
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
            "source_quality_adjusted_ev_pct": 0.05,
            "notional_incremental_value_krw": 50.0,
            "severe_tail_exposure": False,
            "economic_signal_selected": False,
        },
        "replay_control_exact_plus_micro": {
            "action": "WAIT",
            "source_quality_adjusted_ev_pct": control_ev,
            "notional_incremental_value_krw": 100.0,
            "severe_tail_exposure": False,
            "economic_signal_selected": False,
        },
        "replay_candidate_exact_plus_micro": {
            "action": "BUY",
            "source_quality_adjusted_ev_pct": candidate_ev,
            "notional_incremental_value_krw": 200.0,
            "severe_tail_exposure": False,
            "economic_signal_selected": True,
        },
    }
    evaluation_without_hash = {
        "schema": "ai_micro_reversion_three_arm_evaluation_v1",
        "rows": [
            {
                "paired_replay_parent_id": parent_id,
                "decision_trace_id": trace_id,
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
    for arm in cycle.EXPECTED_ARMS:
        reservation_id = f"reservation-{parent_id}-{arm}"
        results.append(
            {
                "paired_replay_parent_id": parent_id,
                "paired_replay_id": f"{parent_id}-{arm}",
                "micro_reversion_replay_arm": arm,
                "prompt_contract_sha256": (
                    "1" * 64
                    if arm != "replay_candidate_exact_plus_micro"
                    else "2" * 64
                ),
                "replay_result": {
                    "status": "pass",
                    "candidate_attempts": [
                        {
                            "status": "pass",
                            "provider_provenance": {
                                "provider": "openai",
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
                                "provider_budget_circuit_breaker_open": False,
                            },
                        }
                    ],
                },
            }
        )
    budget_without_hash = {
        "daily_attempt_cap": 12,
        "daily_usd_cap": "1.0",
        "committed_cost_usd": "0.5",
        "circuit_breaker_open": False,
        "reservation_count": len(results),
        "pricing_artifact_content_sha256": "e" * 64,
    }
    body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": target_date,
        "three_arm_evaluation": evaluation,
        "results": results,
        "status": "offline_three_arm_execution_complete",
        "execution_requested": True,
        "provider_call_attempted": True,
        "provider_call_performed": True,
        "provider_call_succeeded": True,
        "request_count": len(results),
        "result_count": len(results),
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
        "candidate_model_call_attempted": True,
        "selected_parent_ids": [parent_id],
        "selected_request_ids": [row["paired_replay_id"] for row in results],
        "deferred_request_ids": [],
        "provider_provenance_pass_count": len(results),
        "provider_budget_contract_findings": [],
        "provider_budget": {
            **budget_without_hash,
            "summary_content_sha256": cycle._sha256(budget_without_hash),
        },
        **cycle.OFFLINE_AUTHORITY,
    }
    return {**body, "report_content_sha256": cycle._sha256(body)}


def _lifecycle_report(
    target_date: str,
    *,
    trace_id: str,
    session_exposure_sec: float = 3600.0,
    eligible: bool = True,
) -> dict:
    cost_artifact_sha256 = cycle._sha256(
        {"kind": "reviewed_cost_catalog", "target_date": target_date}
    )
    symbol_master_artifact_sha256 = cycle._sha256(
        {"kind": "symbol_master", "target_date": target_date}
    )
    body = {
        "schema": "main_scalping_lifecycle_paired_daily_v1",
        "target_date": target_date,
        "rows": [
            {
                "main_lifecycle_id": f"lifecycle-{trace_id}",
                "decision_trace_ids": [trace_id],
                "promotion_evidence_eligible": eligible,
                "terminal_state": "RECONCILED_FINAL_EXIT",
                "actual_holding_duration_sec": 120.0,
                "session_exposure_sec": session_exposure_sec,
                "capital_time_krw_hours": 50_000.0,
                "bbo_coverage_pct": 100.0,
                "depth_coverage_pct": 100.0,
                "invalid_transition_count": 0,
                "reviewed_cost_profile_sha256": cost_artifact_sha256,
                "reviewed_cost_profile_verified": True,
                "symbol_master_artifact_sha256": symbol_master_artifact_sha256,
                "symbol_master_artifact_verified": True,
            }
        ],
        **cycle.OFFLINE_AUTHORITY,
    }
    return {**body, "artifact_content_sha256": cycle._sha256(body)}


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
            _lifecycle_report(target_date, trace_id=trace_id)
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


def test_lifecycle_index_permanently_blocks_three_conflicting_trace_rows():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    first = report["rows"][0]
    report["rows"] = [
        first,
        {**first, "actual_holding_duration_sec": 121.0},
        {**first, "actual_holding_duration_sec": 122.0},
    ]
    report["artifact_content_sha256"] = cycle._content_hash(
        report, "artifact_content_sha256"
    )

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert findings == [
        f"lifecycle_trace_identity_ambiguous:{target_date}:trace-1"
    ]


def test_lifecycle_index_rejects_missing_producer_content_hash():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report.pop("artifact_content_sha256")

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert findings == [f"lifecycle_report_hash_invalid:{target_date}"]


def test_lifecycle_index_rejects_nonproducer_schema_even_when_rehashed():
    target_date = "2026-08-14"
    report = _lifecycle_report(target_date, trace_id="trace-1")
    report["schema"] = "unrelated_lifecycle_shape_v1"
    report["artifact_content_sha256"] = cycle._content_hash(
        report, "artifact_content_sha256"
    )

    index, findings = cycle._lifecycle_index([report])

    assert index == {}
    assert findings == [f"lifecycle_report_schema_invalid:{target_date}"]


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

    findings = cycle.validate_source_quality_audit(
        audit, target_date="2026-08-14"
    )

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

    assert cycle.validate_source_quality_audit(
        audit, target_date="2026-08-14"
    ) == []


def test_rolling_rejects_daily_cost_or_symbol_binding_mismatch():
    target_date = "2026-08-14"
    lifecycle = _lifecycle_report(target_date, trace_id="trace-1")
    lifecycle["rows"][0]["reviewed_cost_profile_sha256"] = "f" * 64
    lifecycle_body = {
        key: value
        for key, value in lifecycle.items()
        if key != "artifact_content_sha256"
    }
    lifecycle["artifact_content_sha256"] = cycle._sha256(lifecycle_body)

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
    assert rolling["exclusions"][0]["reason"] == (
        "daily_economic_reference_binding_mismatch"
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
    report.update(
        {
            "status": "offline_three_arm_execution_batch_complete",
            "request_count": 6,
            "deferred_request_count": 3,
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
        "materialized_report_content_sha256": materialized[
            "report_content_sha256"
        ],
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
    stale_execution["outcome_label_artifact_sha256"] = cycle._sha256(
        outcome_artifact
    )
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
        "daily_attempt_cap": 12,
        "daily_usd_cap": "1.000000006",
        "committed_cost_usd": "0.5",
        "circuit_breaker_open": False,
        "reservation_count": len(report["results"]),
        "pricing_artifact_content_sha256": pricing_hash,
    }
    report.update(
        {
            "materialized_report_content_sha256": materialized[
                "report_content_sha256"
            ],
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
            "micro_reversion_replay_arm": result[
                "micro_reversion_replay_arm"
            ],
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
    report.update(
        {
            "status": "offline_three_arm_execution_batch_complete",
            "request_count": 6,
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
            "micro_reversion_replay_arm": result[
                "micro_reversion_replay_arm"
            ],
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
            "micro_reversion_replay_arm": result[
                "micro_reversion_replay_arm"
            ],
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


def test_cycle_cli_returns_nonzero_for_terminal_blocked_artifact(
    monkeypatch, capsys
):
    blocked = {
        "schema": cycle.CYCLE_SCHEMA,
        "target_date": "2026-08-14",
        "status": "source_only_blocked_or_deferred",
        "blockers": ["economic_reference_not_verified"],
        **cycle.OFFLINE_AUTHORITY,
    }
    monkeypatch.setattr(cycle, "run_cycle", lambda **_kwargs: blocked)

    assert cycle.main(["--date", "2026-08-14", "--write"]) == 2
    assert "economic_reference_not_verified" in capsys.readouterr().out
