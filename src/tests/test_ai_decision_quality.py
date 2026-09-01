import base64
import gzip
import hashlib
import json
import multiprocessing
import sys
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.micro_reversion import provider_budget
from src.engine.scalping.micro_reversion.provider_budget import (
    PRICING_ARTIFACT_SCHEMA,
    PRICING_AUTHORITY,
    pricing_artifact_content_sha256,
)
from src.engine.scalping.micro_reversion.storage_maintenance import (
    STORAGE_CAPACITY_GROWTH_GATE_SCHEMA,
    STORAGE_CRITICAL_DISK_WATERMARK_BYTES,
    STORAGE_LOW_DISK_WATERMARK_BYTES,
)

KST = ZoneInfo("Asia/Seoul")


def _checkpoint_concurrent_append_worker(
    checkpoint_path_text: str,
    materialized_hash: str,
    result_id: str,
    ready_queue,
    start_event,
    result_queue,
) -> None:
    """Exercise the same custody transaction used by direct execution."""

    checkpoint_path = Path(checkpoint_path_text)
    try:
        ready_queue.put(result_id)
        if not start_event.wait(timeout=10):
            raise RuntimeError("checkpoint_concurrency_start_timeout")
        with quality._micro_reversion_checkpoint_custody_lock(
            checkpoint_path,
            exclusive=True,
        ):
            existing = quality._load_micro_reversion_checkpoint_unlocked(
                checkpoint_path,
                repair_manifest=True,
            )
            # Widen the stale-read race. Without the custody lock both workers
            # would construct sequence 1 from the same empty journal.
            time.sleep(0.1)
            sequence = int(existing.get("checkpoint_record_count") or 0) + 1
            previous_hash = str(existing.get("checkpoint_head_sha256") or "") or None
            record = quality._micro_reversion_checkpoint_record(
                materialized_report_content_sha256=materialized_hash,
                sequence=sequence,
                previous_record_sha256=previous_hash,
                result={"result_id": result_id},
            )
            quality._write_micro_reversion_checkpoint_record_unlocked(
                checkpoint_path,
                record,
            )
        result_queue.put(("ok", result_id, sequence))
    except BaseException as exc:  # pragma: no cover - surfaced in parent
        result_queue.put(("error", result_id, repr(exc)))


def _micro_reversion_direct_execute_worker(
    cli_args,
    ready_queue,
    start_event,
    result_queue,
) -> None:
    """Run one exact direct executor in a forked process."""

    try:
        ready_queue.put("ready")
        if not start_event.wait(timeout=10):
            raise RuntimeError("micro_reversion_direct_concurrency_start_timeout")
        result_queue.put(("ok", quality.main(cli_args)))
    except BaseException as exc:  # pragma: no cover - surfaced in parent
        result_queue.put(("error", repr(exc)))


def _healthy_capacity_gate(*, target_date: str, capacity_path) -> dict:
    total_bytes = STORAGE_LOW_DISK_WATERMARK_BYTES * 3
    free_bytes = STORAGE_LOW_DISK_WATERMARK_BYTES * 2
    return {
        "schema": STORAGE_CAPACITY_GROWTH_GATE_SCHEMA,
        "target_date": target_date,
        "status": "allowed",
        "large_artifact_growth_allowed": True,
        "effective_capacity_state": "healthy",
        "artifact_status": "missing",
        "artifact_capacity_state": None,
        "capacity_status_artifact_path": str(capacity_path.absolute()),
        "capacity_status_artifact_raw_sha256": None,
        "capacity_status_artifact_validation_error": None,
        "direct_snapshot_provenance": "shutil.disk_usage_at_consumer_gate",
        "direct_capacity_state": "healthy",
        "direct_disk_snapshot": {
            "disk_total_bytes": total_bytes,
            "disk_used_bytes": total_bytes - free_bytes,
            "disk_free_bytes": free_bytes,
        },
        "direct_disk_snapshot_error": None,
        "low_disk_watermark_bytes": STORAGE_LOW_DISK_WATERMARK_BYTES,
        "critical_disk_watermark_bytes": STORAGE_CRITICAL_DISK_WATERMARK_BYTES,
        "reason_codes": ["capacity_status_artifact_missing_direct_snapshot_used"],
        "decision_authority": "storage_capacity_growth_gate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "provider_route_change_allowed": False,
        "network_call_performed_by_module": False,
        "forbidden_uses": [
            "broker_order_submission_or_cancel",
            "provider_route_or_model_change",
            "strategy_threshold_quantity_cap_or_bot_change",
            "automatic_purge_or_deletion_authority",
        ],
    }


def _freeze_quality_clock(monkeypatch, *, target_date: str) -> None:
    fixed_now = datetime.fromisoformat(f"{target_date}T20:00:00+09:00")

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            fixed = cls(
                fixed_now.year,
                fixed_now.month,
                fixed_now.day,
                fixed_now.hour,
                fixed_now.minute,
                fixed_now.second,
                tzinfo=fixed_now.tzinfo,
            )
            if tz is None:
                return fixed.replace(tzinfo=None)
            return fixed.astimezone(tz)

    monkeypatch.setattr(quality, "datetime", _FixedDateTime)
    monkeypatch.setattr(provider_budget, "datetime", _FixedDateTime)


def _provider_authority_cli_args(
    *,
    monkeypatch,
    target_date: str,
    pricing_path,
    pricing_payload: dict,
    ledger_path,
    summary_path,
) -> list[str]:
    pricing_file_sha256 = hashlib.sha256(pricing_path.read_bytes()).hexdigest()
    source_artifacts = [
        {
            "target_date": f"2026-08-{day:02d}",
            "content_sha256": hashlib.sha256(
                f"provider-budget-source-{day}".encode()
            ).hexdigest(),
        }
        for day in range(10, 15)
    ]
    budget_basis = {
        "evaluated_call_median": 781,
        "target_share_of_evaluated_median_pct": 50.0,
        "daily_parent_cap": 130,
        "logical_requests_per_parent": 3,
        "maximum_logical_request_count": 390,
        "daily_attempt_cap": 390,
        "source_artifacts": source_artifacts,
    }
    policy_path = pricing_path.with_name("economic-policy.json")
    policy_path.write_text(
        json.dumps({"provider_budget_basis": budget_basis}), encoding="utf-8"
    )
    policy_bytes = policy_path.read_bytes()
    manifest_path = pricing_path.with_name("economic-manifest.json")
    manifest_path.write_text(
        json.dumps({"schema": "test-economic-manifest-v1"}), encoding="utf-8"
    )
    manifest_bytes = manifest_path.read_bytes()
    owner_body = {
        "schema": "micro_reversion_economic_reference_owner_report_v1",
        "target_date": target_date,
        "generated_at": f"{target_date}T18:00:00+09:00",
        "status": "pass",
        "policy_path": str(policy_path.absolute()),
        "policy_sha256": hashlib.sha256(policy_bytes).hexdigest(),
        "economic_manifest_path": str(manifest_path.absolute()),
        "economic_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "economic_manifest_size_bytes": len(manifest_bytes),
        "provider_pricing_path": str(pricing_path.absolute()),
        "provider_pricing_sha256": pricing_file_sha256,
        "provider_pricing_size_bytes": pricing_path.stat().st_size,
        "provider_pricing_content_sha256": pricing_payload["artifact_content_sha256"],
        "eligible_common_stock_count": 2,
        "eligible_kospi_count": 1,
        "eligible_kosdaq_count": 1,
        "provider_budget_basis": budget_basis,
        "provider_call_performed": False,
        "decision_authority": "offline_economic_reference_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "trading_runtime_effect": False,
        "trading_decision_effect": False,
        "selection_authority": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": ["direct_runtime_or_order_apply"],
    }
    owner = {
        **owner_body,
        "artifact_content_sha256": quality._sha256(owner_body),
    }
    owner_path = pricing_path.with_name("owner-report.json")
    owner_path.write_text(json.dumps(owner), encoding="utf-8")
    monkeypatch.setattr(
        quality,
        "micro_reversion_economic_owner_report_path",
        lambda _target_date: owner_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_economic_policy_path",
        lambda: policy_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_economic_manifest_path",
        lambda: manifest_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_pricing_path",
        lambda: pricing_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_budget_ledger_path",
        lambda _execution_date: ledger_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_budget_summary_path",
        lambda _execution_date: summary_path,
    )
    return [
        "--micro-reversion-economic-owner-report",
        str(owner_path),
        "--micro-reversion-economic-owner-report-content-sha256",
        owner["artifact_content_sha256"],
        "--micro-reversion-provider-pricing-file-sha256",
        pricing_file_sha256,
        "--micro-reversion-provider-pricing-content-sha256",
        pricing_payload["artifact_content_sha256"],
    ]


def test_micro_reversion_provider_authority_rejects_self_hashed_noncanonical_owner(
    tmp_path, monkeypatch
):
    target_date = "2026-08-18"
    canonical_owner = tmp_path / "canonical" / "owner_report.json"
    canonical_pricing = tmp_path / "canonical" / "provider_pricing.json"
    arbitrary_owner = tmp_path / "attacker" / "owner_report.json"
    arbitrary_pricing = tmp_path / "attacker" / "provider_pricing.json"
    arbitrary_owner.parent.mkdir(parents=True)
    arbitrary_owner.write_text("{}", encoding="utf-8")
    arbitrary_pricing.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        quality,
        "micro_reversion_economic_owner_report_path",
        lambda _target_date: canonical_owner,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_pricing_path",
        lambda: canonical_pricing,
    )

    fake_hash = "a" * 64
    with pytest.raises(
        RuntimeError,
        match="micro_reversion_provider_owner_report_path_not_canonical",
    ):
        quality._validate_micro_reversion_provider_authority_binding(
            target_date=target_date,
            owner_report_path=arbitrary_owner,
            expected_owner_report_content_sha256=fake_hash,
            pricing_path=arbitrary_pricing,
            expected_pricing_file_sha256=fake_hash,
            expected_pricing_content_sha256=fake_hash,
            reviewed_pricing=SimpleNamespace(
                artifact_file_sha256=fake_hash,
                artifact_content_sha256=fake_hash,
            ),
        )


def test_micro_reversion_provider_authority_rejects_canonical_owner_parent_symlink(
    tmp_path, monkeypatch
):
    target_date = "2026-08-18"
    real_parent = tmp_path / "real-owner"
    real_parent.mkdir()
    (real_parent / "owner_report.json").write_text("{}", encoding="utf-8")
    linked_parent = tmp_path / "canonical-owner"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    owner_path = linked_parent / "owner_report.json"
    pricing_path = tmp_path / "provider_pricing.json"
    pricing_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        quality,
        "micro_reversion_economic_owner_report_path",
        lambda _target_date: owner_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_provider_pricing_path",
        lambda: pricing_path,
    )

    fake_hash = "b" * 64
    with pytest.raises(
        RuntimeError,
        match="micro_reversion_provider_owner_report_unreadable",
    ):
        quality._validate_micro_reversion_provider_authority_binding(
            target_date=target_date,
            owner_report_path=owner_path,
            expected_owner_report_content_sha256=fake_hash,
            pricing_path=pricing_path,
            expected_pricing_file_sha256=fake_hash,
            expected_pricing_content_sha256=fake_hash,
            reviewed_pricing=SimpleNamespace(
                artifact_file_sha256=fake_hash,
                artifact_content_sha256=fake_hash,
            ),
        )


def test_legacy_holding_prompt_endpoint_is_consumed_as_holding_score():
    assert (
        quality._trace_endpoint(
            {
                "endpoint": "scalping_holding_score",
                "decision_stage": "holding_score",
            }
        )
        == "holding_score"
    )


def test_load_jsonl_reads_verified_gzip_archive(tmp_path):
    plain_path = tmp_path / "pipeline_events_2026-07-29.jsonl"
    with gzip.open(f"{plain_path}.gz", "wt", encoding="utf-8") as handle:
        handle.write('{"stage":"ai_confirmed"}\n')

    assert quality._load_jsonl(plain_path) == [{"stage": "ai_confirmed"}]


def test_quality_atomic_writer_delegates_preserving_existing_format(
    tmp_path, monkeypatch
):
    observed = {}

    def capture(path, value, **options):
        observed.update({"path": path, "value": value, **options})

    monkeypatch.setattr(quality, "write_json_object_generation_safe", capture)
    output = tmp_path / "report.json"
    quality._atomic_write_json(output, {"b": 2, "a": 1})

    assert observed == {
        "path": output,
        "value": {"b": 2, "a": 1},
        "ensure_ascii": False,
        "indent": 2,
        "sort_keys": False,
        "trailing_newline": False,
    }


def _payload():
    return {
        "payload_sha256": "payload-1",
        "replay_exact": True,
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sanitized_user_input": {
            "entry_candle_context": {
                "schema": quality.ENTRY_CONTEXT_SCHEMA,
                "venue": "KRX",
                "session": "krx_regular",
                "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
                "bars": [
                    {
                        "t": "09:00",
                        "o": 100,
                        "h": 101,
                        "l": 99,
                        "c": 100,
                        "v": 10,
                        "forming": False,
                    }
                ],
            }
        },
    }


def _trace(action="DROP"):
    return {
        "decision_trace_id": "trace-1",
        "decision_ts": "2026-07-27T09:00:00+09:00",
        "decision_stage": "entry",
        "endpoint": "analyze_target",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_replay_exact": True,
        "request_capture_status": "captured",
        "payload_sha256": "payload-1",
        "prompt_version": "entry_v1",
        "prompt_sha256": "prompt-1",
        "provider_actual": "openai",
        "model": "gpt-test",
        "request_temperature": 0,
        "request_reasoning_effort": "medium",
        "openai_response_schema_mode": "json_object",
        "openai_response_schema_registry_used": False,
        "response_schema_application": "provider_json_object_openai",
        "semantic_validator_version": (
            quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
        ),
        "expected_semantic_validator_version": (
            quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
        ),
        "semantic_validator_applied": True,
        "semantic_validation_status": "pass",
        "result_source": "live",
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "action": action,
    }


def test_payload_contract_prefers_exact_replay_context_over_compact_provider_input():
    payload = _payload()
    exact_context = payload["sanitized_user_input"]
    payload.update(
        {
            "sanitized_user_input": {
                "input_schema": "entry_setup_v2_14_live_input",
                "entry_setup_evidence_v1": {"setup_state": "READY"},
            },
            "replay_context_exact": True,
            "sanitized_replay_context": {
                "exact_payload": exact_context,
                "exact_payload_analysis_v1": {"schema": "exact_payload_analysis_v1"},
            },
        }
    )

    assert quality._replay_exact_payload(quality.replay_source_input(payload)) == (
        exact_context
    )
    assert len(quality._payload_contract(payload)["canonical_contexts"]) == 1


def test_payload_lookup_prefers_request_envelope_when_provider_hash_repeats():
    first = {
        **_payload(),
        "endpoint": "analyze_target",
        "request_envelope_sha256": "request-1",
        "sanitized_replay_context": {"exact_payload": {"marker": "first"}},
        "replay_context_present": True,
        "replay_context_exact": True,
    }
    second = {
        **_payload(),
        "endpoint": "analyze_target",
        "request_envelope_sha256": "request-2",
        "sanitized_replay_context": {"exact_payload": {"marker": "second"}},
        "replay_context_present": True,
        "replay_context_exact": True,
    }
    payload_by_key, payload_by_unique_hash = quality._payload_indexes([first, second])

    selected = quality._payload_for_trace(
        {
            **_trace(),
            "request_envelope_sha256": "request-1",
        },
        payload_by_key=payload_by_key,
        payload_by_unique_hash=payload_by_unique_hash,
    )

    assert selected["request_envelope_sha256"] == "request-1"
    assert quality.replay_source_input(selected) == {
        "exact_payload": {"marker": "first"}
    }
    assert (
        quality._payload_for_trace(
            {
                **_trace(),
                "payload_sha256": "corrupted-hash",
                "request_envelope_sha256": "request-1",
            },
            payload_by_key=payload_by_key,
            payload_by_unique_hash=payload_by_unique_hash,
        )
        == {}
    )


def _pending(action="DROP"):
    return {
        "schema": "ai_decision_outcome_label_v1",
        "label_id": "trace-1:v1",
        "decision_trace_id": "trace-1",
        "decision_stage": "entry",
        "stock_code": "005930",
        "decision_ts": "2026-07-27T09:00:00+09:00",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "reference_price": 100,
        "target_price": 101,
        "adverse_price": 99,
        "action": action,
        "confidence": 90,
        "record_id": "record-1",
    }


def test_control_manifest_freezes_exact_post_promotion_signature():
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[_payload()],
    )
    assert report["status"] == "control_manifest_frozen_collect_exact_samples"
    assert report["controls"][0]["prompt_sha256"] == "prompt-1"
    assert report["prompt_model_provider_change_count"] == 0
    assert report["runtime_effect"] is False


def test_control_manifest_surfaces_same_version_prompt_sha_drift_by_cohort():
    second_trace = {
        **_trace(),
        "decision_trace_id": "trace-2",
        "decision_ts": "2026-07-27T09:01:00+09:00",
        "effective_venue": "NXT",
        "session_bucket": "NXT_REGULAR_OVERLAP",
        "payload_sha256": "payload-2",
        "prompt_sha256": "prompt-2",
    }
    second_payload = {
        **_payload(),
        "payload_sha256": "payload-2",
        "effective_venue": "NXT",
        "session_bucket": "NXT_REGULAR_OVERLAP",
        "sanitized_user_input": {
            "entry_candle_context": {
                "schema": quality.ENTRY_CONTEXT_SCHEMA,
                "venue": "NXT",
                "session": "nxt_regular_overlap",
                "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
                "bars": [
                    {
                        "t": "09:01",
                        "o": 100,
                        "h": 101,
                        "l": 99,
                        "c": 100,
                        "v": 10,
                        "forming": False,
                    }
                ],
            }
        },
    }

    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace(), second_trace],
        payloads=[_payload(), second_payload],
    )

    assert report["prompt_version_sha_drift_count"] == 1
    assert report["prompt_version_sha_drift"][0]["prompt_sha256_values"] == [
        "prompt-1",
        "prompt-2",
    ]
    assert len(report["prompt_signature_cohorts"]) == 2


def test_cohort_filter_and_artifact_paths_do_not_mix_krx_and_nxt():
    rows = [
        {"effective_venue": "KRX", "session_bucket": "krx_regular"},
        {
            "effective_venue": "NXT",
            "session_bucket": "nxt_regular_overlap",
        },
    ]

    filtered = quality._filter_rows_for_cohort(
        rows,
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
    )

    assert filtered == [rows[0]]
    assert quality.control_path(
        "2026-08-06",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
    ).name.endswith("_venue_krx_session_krx_regular.json")


def test_daily_materialization_builds_ordered_chain_without_candidate_execution():
    label = {
        **_pending(),
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 1.0,
                "mfe_pct": 1.2,
                "mae_pct": -0.2,
                "first_hit": "target",
                "entry_path_first_hit": "target_first",
                "entry_path_target_pct": 0.3,
                "entry_path_adverse_pct": -0.7,
            }
        },
    }
    label_report = {
        "schema": quality.LABEL_REPORT_SCHEMA,
        "target_date": "2026-07-27",
        "status": "mature_label_rows_available",
        "summary": {"mature": 1},
        "outcome_as_of": "2026-07-27T16:30:00+09:00",
        "labels": [label],
        **quality.OFFLINE_CONTRACT,
    }

    materialization = quality.build_daily_materialization_reports(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[_payload()],
        labels=[label],
        label_report=label_report,
        outcome_price_source="pipeline",
        outcome_price_source_requested="pipeline",
        price_source_provenance=[],
    )

    assert materialization["write_order"] == [
        "control",
        "mature",
        "baseline",
        "paired",
        "candidate_lifecycle_state",
    ]
    assert materialization["candidate_execution_performed"] is False
    assert materialization["contract_validation"] == "pass"
    assert materialization["decision_quality_objective"]["not_objective"] == (
        "maximize_drop_wait_or_eliminate_all_risk"
    )
    assert (
        materialization["decision_quality_objective"][
            "artifact_generation_is_performance"
        ]
        is False
    )
    assert materialization["runtime_effect"] is False
    assert materialization["reports"]["control"]["controls"]
    assert materialization["reports"]["baseline"]["eligible_sample_count"] == 1
    paired = materialization["reports"]["paired"]
    assert paired["prepared_request_count"] == 1
    assert paired["outcome_as_of"] == "2026-07-27T16:30:00+09:00"
    assert (
        materialization["reports"]["candidate_lifecycle_state"]["schema"]
        == "entry_candidate_lifecycle_state_report_v1"
    )
    assert paired["request_count"] == 1
    assert paired["status"] == ("paired_replay_requests_ready_candidate_not_executed")
    assert paired["sample_floor_buckets"][0]["pass"] is True
    assert (
        paired["sample_floor_buckets"][0]["promotion_evidence_floor"]["pass"] is False
    )
    assert paired["candidate_execution_performed"] is False
    assert paired["candidate_execution_authority"] == (
        "explicit_offline_execute_candidate_only"
    )
    funnel = paired["entry_opportunity_funnel"]
    assert funnel["candidate_execution_requested"] is False
    assert funnel["cohorts"][0]["first_blocker_counts"] == {
        "candidate_execution_not_requested": 1
    }

    invalid_reports = dict(materialization["reports"])
    invalid_reports["paired"] = {
        **paired,
        "candidate_execution_performed": True,
        "results": [{"status": "pass"}],
    }
    assert quality.validate_daily_materialization_reports(
        target_date="2026-07-27",
        reports=invalid_reports,
    ) == [
        "paired_candidate_execution_performed",
        "paired_candidate_results_not_empty",
    ]


def _paired_outcome_recovery_report(*, outcome_return_pct=1.0):
    exact_sha256 = quality._sha256(
        quality._replay_exact_payload(_payload()["sanitized_user_input"])
    )
    return {
        "schema": quality.DETAILED_PAIRED_SCHEMA,
        "target_date": "2026-07-27",
        "outcome_price_source": "kiwoom_completed_1m",
        "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "requests": [
            {
                "decision_trace_id": "trace-1",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "payload_sha256": "payload-1",
                "source_exact_payload_sha256": exact_sha256,
                "candidate_exact_payload_sha256": exact_sha256,
                "outcome_join_key": "trace-1:v1",
            }
        ],
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-1",
                "stock_code": "005930",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "control_action": "WAIT",
                "outcome_return_pct": outcome_return_pct,
                "outcome_mfe_pct": 1.2,
                "outcome_mae_pct": -0.2,
                "first_hit": "target",
                "profit_opportunity_observed": True,
                "profit_opportunity_sequence": "profit_without_prior_drawdown",
            }
        ],
        "paired_comparable_count": 1,
        "price_source_provenance": [
            {
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality_status": "pass_target_window_available",
                "fetch_error": None,
            }
        ],
        **quality.OFFLINE_CONTRACT,
    }


def test_same_trace_outcome_recovery_reuses_only_prior_outcome(tmp_path):
    source_path = tmp_path / "prior_paired.json"
    source_path.write_text(
        json.dumps(_paired_outcome_recovery_report()), encoding="utf-8"
    )

    labels, metadata = quality.recover_same_trace_outcome_labels_from_paired_reports(
        target_date="2026-07-27",
        labels=[],
        traces=[_trace()],
        payloads=[_payload()],
        report_paths=[source_path],
    )

    assert metadata["status"] == "recovered_same_trace_primary_outcomes"
    assert metadata["recovered_label_count"] == 1
    assert metadata["exact_payload_reconstructed"] is False
    assert metadata["runtime_effect"] is False
    assert labels[0]["horizon_metrics"]["10m"]["end_return_pct"] == 1.0
    assert labels[0]["outcome_recovery"]["outcome_only_reuse"] is True
    assert labels[0]["outcome_recovery"]["source_report_sha256"]
    assert "exact_payload" not in labels[0]


def test_same_trace_outcome_recovery_replaces_conflicting_regenerated_label(
    tmp_path,
):
    source_path = tmp_path / "prior_paired.json"
    source_path.write_text(
        json.dumps(_paired_outcome_recovery_report(outcome_return_pct=1.0)),
        encoding="utf-8",
    )
    current_label = {
        **_pending(),
        "label_status": "partial",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": -1.0,
                "mfe_pct": 0.1,
                "mae_pct": -1.2,
                "first_hit": "adverse",
            }
        },
    }

    labels, metadata = quality.recover_same_trace_outcome_labels_from_paired_reports(
        target_date="2026-07-27",
        labels=[current_label],
        traces=[_trace()],
        payloads=[_payload()],
        report_paths=[source_path],
    )

    assert labels[0]["horizon_metrics"]["10m"]["end_return_pct"] == 1.0
    assert metadata["replaced_current_label_count"] == 1
    assert metadata["current_primary_metric_conflict_count"] == 1


def test_same_trace_outcome_recovery_ignores_non_recoverable_metric_fields(tmp_path):
    source_path = tmp_path / "prior_paired.json"
    source_path.write_text(
        json.dumps(_paired_outcome_recovery_report(outcome_return_pct=1.0)),
        encoding="utf-8",
    )
    current_label = {
        **_pending(),
        "label_status": "partial",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 1.0,
                "mfe_pct": 1.2,
                "mae_pct": -0.2,
                "first_hit": "target",
                "profit_opportunity_observed": True,
                "profit_opportunity_sequence": "profit_without_prior_drawdown",
                "sample_count": 10,
                "window_basis": "post_decision_same_route",
            }
        },
    }

    _, metadata = quality.recover_same_trace_outcome_labels_from_paired_reports(
        target_date="2026-07-27",
        labels=[current_label],
        traces=[_trace()],
        payloads=[_payload()],
        report_paths=[source_path],
    )

    assert metadata["replaced_current_label_count"] == 1
    assert metadata["current_primary_metric_conflict_count"] == 0


def test_same_trace_outcome_recovery_excludes_conflicting_sources(tmp_path):
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_path.write_text(
        json.dumps(_paired_outcome_recovery_report(outcome_return_pct=1.0)),
        encoding="utf-8",
    )
    second_path.write_text(
        json.dumps(_paired_outcome_recovery_report(outcome_return_pct=-1.0)),
        encoding="utf-8",
    )

    labels, metadata = quality.recover_same_trace_outcome_labels_from_paired_reports(
        target_date="2026-07-27",
        labels=[],
        traces=[_trace()],
        payloads=[_payload()],
        report_paths=[first_path, second_path],
    )

    assert labels == []
    assert metadata["recovered_label_count"] == 0
    assert metadata["excluded_counts"] == {"conflicting_recovered_outcome": 1}


def test_cached_semantic_repair_requires_current_version_and_exact_repair_list():
    request = {
        "candidate": {
            "semantic_repair_version": (
                quality.BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION
            )
        }
    }
    result = {
        "candidate_semantic_repairs": ["invalid_probe_buy_waited"],
        "candidate_attempts": [
            {
                "provider_provenance": {
                    "provider": "deterministic_offline_adapter",
                    "semantic_repair_version": (
                        quality.BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION
                    ),
                    "repairs": ["invalid_probe_buy_waited"],
                }
            }
        ],
    }

    assert quality._semantic_repair_provenance_matches(result, request) is True
    stale = json.loads(json.dumps(result))
    stale["candidate_attempts"][0]["provider_provenance"][
        "semantic_repair_version"
    ] = "bounded_opportunity_fail_safe_repair_v1"
    assert quality._semantic_repair_provenance_matches(stale, request) is False
    stale_list = json.loads(json.dumps(result))
    stale_list["candidate_attempts"][0]["provider_provenance"]["repairs"] = []
    assert quality._semantic_repair_provenance_matches(stale_list, request) is False


def test_paired_request_preparation_is_not_mislabeled_as_candidate_rejection():
    request = {
        "paired_replay_id": "pair-1",
        "decision_trace_id": "trace-1",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
    }

    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=[request],
        results=[],
        labels=[],
    )

    assert report["status"] == ("paired_replay_requests_ready_candidate_not_executed")
    assert report["candidate_execution_performed"] is False
    assert report["missing_result_count"] == 1


def test_stage_paired_path_isolated_from_combined_artifact():
    assert quality.stage_paired_path("2026-08-03", "holding").name == (
        "ai_prompt_paired_replay_2026-08-03_holding.json"
    )
    with pytest.raises(ValueError, match="unsupported_paired_stage"):
        quality.stage_paired_path("2026-08-03", "entry_price")


def test_control_manifest_selects_named_prompt_version_and_records_rollover(tmp_path):
    old_trace = {
        **_trace(),
        "prompt_version": "hot_v1",
        "prompt_sha256": "prompt-old",
    }
    current_trace = {
        **_trace(),
        "decision_trace_id": "trace-current",
        "prompt_version": "decision_quality_v2_7",
        "prompt_sha256": "prompt-current",
    }
    report = quality.build_control_manifest(
        target_date="2026-07-30",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[old_trace, current_trace],
        payloads=[_payload()],
        control_prompt_versions={"analyze_target": "decision_quality_v2_7"},
        promotion_artifact_path=tmp_path / "promotion_2026-07-29.json",
        promotion_source_date="2026-07-29",
    )

    assert report["status"] == "control_manifest_frozen_collect_exact_samples"
    assert report["controls"][0]["prompt_version"] == "decision_quality_v2_7"
    assert report["controls"][0]["sample_count"] == 1
    assert report["excluded_counts"]["control_prompt_version_not_selected"] == 1
    assert report["promotion_rollover"] is True
    assert report["promotion_source_date"] == "2026-07-29"


def test_daily_control_selects_latest_exact_prompt_version_per_endpoint():
    older = {
        **_trace(),
        "prompt_version": "hot_v1",
        "prompt_sha256": "prompt-old",
        "decision_ts": "2026-07-27T09:00:00+09:00",
    }
    latest = {
        **_trace(),
        "decision_trace_id": "trace-latest",
        "prompt_version": "decision_quality_v2_7_probe_v1",
        "prompt_sha256": "prompt-latest",
        "decision_ts": "2026-07-27T10:00:00+09:00",
    }

    selected = quality._latest_exact_control_prompt_versions(
        promotion={"promoted_at": "2026-07-27T08:30:00+09:00"},
        traces=[older, latest],
        payloads=[_payload()],
    )

    assert selected == {"analyze_target": "decision_quality_v2_7_probe_v1"}
    signatures = quality._latest_exact_control_signatures(
        promotion={"promoted_at": "2026-07-27T08:30:00+09:00"},
        traces=[older, latest],
        payloads=[_payload()],
    )
    assert signatures["analyze_target"]["prompt_sha256"] == "prompt-latest"
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[
            {**older, "prompt_version": "decision_quality_v2_7_probe_v1"},
            latest,
        ],
        payloads=[_payload()],
        control_prompt_versions=selected,
        control_signatures=signatures,
    )
    assert report["status"] == "control_manifest_frozen_collect_exact_samples"
    assert report["controls"][0]["prompt_sha256"] == "prompt-latest"
    assert report["controls"][0]["sample_count"] == 1
    assert report["excluded_counts"]["control_signature_not_selected"] == 1


def test_postclose_cli_writes_and_revalidates_all_daily_artifacts(
    monkeypatch, tmp_path, capsys
):
    label = {
        **_pending(),
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 0.5,
                "mfe_pct": 0.8,
                "mae_pct": -0.1,
                "first_hit": "target",
            }
        },
    }
    paths = {
        "control": tmp_path / "control.json",
        "mature": tmp_path / "mature.json",
        "baseline": tmp_path / "baseline.json",
        "paired": tmp_path / "paired.json",
        "candidate_lifecycle_state": tmp_path / "candidate_lifecycle_state.json",
    }
    monkeypatch.setattr(
        quality,
        "_default_sources",
        lambda *_args, **_kwargs: {
            "traces": [_trace()],
            "payloads": [_payload()],
            "pending": [_pending()],
            "pipeline": [],
            "pipeline_paths": [],
        },
    )
    monkeypatch.setattr(
        quality,
        "load_promotion_for_target_date",
        lambda _date: (
            {
                "decision": "promoted_all_market_sessions_full",
                "runtime_activation": True,
                "transaction_status": "committed",
                "promoted_at": "2026-07-27T08:30:00+09:00",
            },
            tmp_path / "promotion.json",
            "2026-07-27",
        ),
    )
    monkeypatch.setattr(
        quality,
        "load_pipeline_price_and_lifecycle_rows",
        lambda *_args, **_kwargs: ([], []),
    )
    monkeypatch.setattr(
        quality,
        "mature_outcome_labels",
        lambda **_kwargs: [label],
    )
    monkeypatch.setattr(
        quality,
        "annotate_primary_cohort_eligibility",
        lambda **kwargs: kwargs["labels"],
    )
    monkeypatch.setattr(quality, "control_path", lambda _date: paths["control"])
    monkeypatch.setattr(quality, "label_report_path", lambda _date: paths["mature"])
    monkeypatch.setattr(quality, "baseline_path", lambda _date: paths["baseline"])
    monkeypatch.setattr(quality, "paired_path", lambda _date: paths["paired"])
    monkeypatch.setattr(
        quality,
        "candidate_lifecycle_report_path",
        lambda _date: paths["candidate_lifecycle_state"],
    )

    assert (
        quality.main(
            [
                "--date",
                "2026-07-27",
                "--mode",
                "postclose",
                "--outcome-price-source",
                "pipeline",
                "--write",
            ]
        )
        == 0
    )

    assert all(path.exists() for path in paths.values())
    paired = quality._load_json(paths["paired"])
    assert paired["candidate_execution_performed"] is False
    assert paired["results"] == []
    assert "daily_exact_quality_chain_prepared" in capsys.readouterr().out


def test_control_manifest_separates_approved_cache_redaction_supplemental():
    trace = {
        **_trace(),
        "payload_replay_exact": False,
        "prompt_version": "decision_quality_v2_7",
        "prompt_sha256": "prompt-current",
    }
    payload = _payload()
    raw_exact = payload["sanitized_user_input"]
    raw_exact["runtime_context"] = {"lifecycle_ai": {"cache_token": "[REDACTED]"}}
    payload.update(
        {
            "redacted": True,
            "replay_exact": False,
            "sanitized_user_input": {
                "exact_payload": raw_exact,
                "exact_payload_analysis_v1": {"schema": "exact_payload_analysis_v1"},
            },
        }
    )
    report = quality.build_control_manifest(
        target_date="2026-07-30",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[payload],
        control_prompt_versions={"analyze_target": "decision_quality_v2_7"},
    )

    assert report["controls"] == []
    assert report["supplemental_semantic_controls"][0]["sample_count"] == 1
    assert report["supplemental_semantic_controls"][0]["prompt_version"] == (
        "decision_quality_v2_7"
    )
    assert report["excluded_counts"]["not_exact"] == 1
    assert report["excluded_counts"]["payload_store_not_exact"] == 1

    payload["sanitized_user_input"]["exact_payload"]["api_key"] = "[REDACTED]"
    assert quality._approved_cache_redaction_supplemental(payload) is False


def test_supplemental_signature_conflict_does_not_block_primary_control():
    supplemental_payloads = []
    supplemental_traces = []
    for index, prompt_hash in enumerate(("supplemental-a", "supplemental-b"), start=2):
        payload = _payload()
        payload["payload_sha256"] = f"payload-{index}"
        raw_exact = payload["sanitized_user_input"]
        raw_exact["runtime_context"] = {"lifecycle_ai": {"cache_token": "[REDACTED]"}}
        payload.update(
            {
                "redacted": True,
                "replay_exact": False,
                "sanitized_user_input": {
                    "exact_payload": raw_exact,
                    "exact_payload_analysis_v1": {
                        "schema": "exact_payload_analysis_v1"
                    },
                },
            }
        )
        supplemental_payloads.append(payload)
        supplemental_traces.append(
            {
                **_trace(),
                "decision_trace_id": f"trace-{index}",
                "payload_sha256": f"payload-{index}",
                "payload_replay_exact": False,
                "prompt_version": "decision_quality_v2_7",
                "prompt_sha256": prompt_hash,
            }
        )

    report = quality.build_control_manifest(
        target_date="2026-07-30",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace(), *supplemental_traces],
        payloads=[_payload(), *supplemental_payloads],
    )

    assert report["status"] == "control_manifest_frozen_collect_exact_samples"
    assert report["conflicts"] == []
    assert report["supplemental_semantic_controls"] == []
    assert report["supplemental_conflicts"] == [
        "supplemental_control_signature_conflict:analyze_target"
    ]


def test_load_promotion_for_target_date_uses_latest_prior_artifact(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(quality, "RUNTIME_DIR", tmp_path)
    (tmp_path / "ai_multi_timeframe_context_promotion_2026-07-28.json").write_text(
        '{"marker":"old"}', encoding="utf-8"
    )
    latest = tmp_path / "ai_multi_timeframe_context_promotion_2026-07-29.json"
    latest.write_text('{"marker":"latest"}', encoding="utf-8")
    (tmp_path / "ai_multi_timeframe_context_promotion_2026-07-31.json").write_text(
        '{"marker":"future"}', encoding="utf-8"
    )

    promotion, path, source_date = quality.load_promotion_for_target_date("2026-07-30")

    assert promotion["marker"] == "latest"
    assert path == latest
    assert source_date == "2026-07-29"


def test_control_manifest_rejects_non_exact_preflight_mode():
    trace = {**_trace(), "input_preflight_mode": "baseline_v1"}
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[_payload()],
    )
    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"]["input_preflight_not_exact_v2"] == 1


def test_control_manifest_excludes_simulation_observation_from_natural_cohort():
    trace = {
        **_trace(),
        "sim_record_id": "sim-005930-1",
        "source_event_stage": "scalp_sim_holding_review",
        "position_reconciliation_mode": "simulation_book",
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[_payload()],
    )

    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"]["simulation_observation_not_natural_cohort"] == 1


def test_control_manifest_does_not_exclude_real_holding_for_legacy_sim_stage_label():
    trace = {
        **_trace(),
        "source_event_stage": "scalp_sim_holding_review",
        "position_reconciliation_mode": "broker_account",
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[_payload()],
    )

    assert (
        report["excluded_counts"].get("simulation_observation_not_natural_cohort", 0)
        == 0
    )


def test_control_manifest_does_not_exclude_legacy_real_record_in_sim_parent_field():
    trace = {
        **_trace(),
        "sim_parent_record_id": "real-db-record-123",
        "position_reconciliation_mode": "not_required",
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[_payload()],
    )

    assert (
        report["excluded_counts"].get("simulation_observation_not_natural_cohort", 0)
        == 0
    )


def test_control_manifest_rejects_canonical_context_without_completed_bars():
    payload = _payload()
    payload["sanitized_user_input"]["entry_candle_context"]["bars"] = [
        {"t": "09:00", "c": 100, "forming": True}
    ]
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[payload],
    )
    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"]["canonical_completed_bars_missing"] == 1


def test_control_manifest_rejects_explicit_sparse_canonical_decision_window():
    payload = _payload()
    payload["sanitized_user_input"]["entry_candle_context"]["source_quality"] = {
        "decision_window": {
            "status": "sparse_observed_minutes",
            "provider_call_allowed": True,
            "missing_bar_count": 2,
        }
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[payload],
    )

    assert report["status"] == "control_manifest_gap_fix_required"
    assert (
        report["excluded_counts"]["canonical_decision_window_source_quality_blocked"]
        == 1
    )


def test_control_manifest_accepts_exact_sparse_no_trade_minute_contract():
    payload = _payload()
    payload.update({"effective_venue": "NXT", "session_bucket": "NXT_AFTERMARKET"})
    payload["sanitized_user_input"]["entry_candle_context"].update(
        {"venue": "NXT", "session": "nxt_aftermarket"}
    )
    payload["sanitized_user_input"]["entry_candle_context"]["source_quality"] = {
        "status": "fresh_consistent",
        "decision_window": {
            "status": "sparse_observed_minutes",
            "provider_call_allowed": True,
            "missing_bar_count": 2,
            "max_consecutive_missing_bar_count": 1,
            "sparse_observed_minutes": True,
            "minute_bar_policy": "ka10080_observed_rows_no_synthetic_fill",
        },
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[
            {
                **_trace(),
                "effective_venue": "NXT",
                "session_bucket": "NXT_AFTERMARKET",
            }
        ],
        payloads=[payload],
    )

    assert report["status"] == "control_manifest_frozen_collect_exact_samples"
    assert (
        report["excluded_counts"].get(
            "canonical_decision_window_source_quality_blocked", 0
        )
        == 0
    )
    payload_contract = quality._payload_contract(payload)
    assert len(payload_contract["canonical_contexts"]) == 1
    context = payload_contract["canonical_contexts"][0]
    assert context["decision_window_status"] == "sparse_observed_minutes"
    assert context["decision_window_sparse_observed_minutes"] is True
    assert (
        context["decision_window_minute_bar_policy"]
        == "ka10080_observed_rows_no_synthetic_fill"
    )


def test_control_manifest_rejects_sparse_context_spoofed_across_trace_venue():
    payload = _payload()
    payload.update({"effective_venue": "NXT", "session_bucket": "NXT_AFTERMARKET"})
    payload["sanitized_user_input"]["entry_candle_context"].update(
        {"venue": "NXT", "session": "nxt_aftermarket"}
    )
    payload["sanitized_user_input"]["entry_candle_context"]["source_quality"] = {
        "status": "fresh_consistent",
        "decision_window": {
            "status": "sparse_observed_minutes",
            "provider_call_allowed": True,
            "missing_bar_count": 2,
            "sparse_observed_minutes": True,
            "minute_bar_policy": "ka10080_observed_rows_no_synthetic_fill",
        },
    }

    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[payload],
    )

    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"]["payload_trace_venue_mismatch"] == 1
    assert report["excluded_counts"]["payload_trace_session_mismatch"] == 1
    assert report["excluded_counts"]["canonical_context_venue_session_mismatch"] == 1


def test_control_manifest_keeps_krx_sparse_window_out_of_primary_cohort():
    payload = _payload()
    payload["sanitized_user_input"]["entry_candle_context"].update(
        {"venue": "KRX", "session": "krx_regular"}
    )
    payload["sanitized_user_input"]["entry_candle_context"]["source_quality"] = {
        "status": "fresh_consistent",
        "decision_window": {
            "status": "sparse_observed_minutes",
            "provider_call_allowed": True,
            "missing_bar_count": 1,
            "max_consecutive_missing_bar_count": 1,
            "sparse_observed_minutes": True,
            "minute_bar_policy": "ka10080_observed_rows_no_synthetic_fill",
        },
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[payload],
    )

    assert report["status"] == "control_manifest_gap_fix_required"
    assert (
        report["excluded_counts"]["canonical_decision_window_source_quality_blocked"]
        == 1
    )


def test_holding_context_contract_reads_nested_candle_bundle_and_bars():
    trace = {
        **_trace(),
        "decision_stage": "holding",
        "endpoint": "holding_score",
    }
    payload = {
        "payload_sha256": "payload-1",
        "replay_exact": True,
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sanitized_user_input": {
            "holding_decision_context": {
                "schema": quality.HOLDING_CONTEXT_SCHEMA,
                "venue": "KRX",
                "session": "krx_regular",
                "candle": {
                    "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
                    "bars": [{"minute": "09:00", "close": 100, "is_forming": False}],
                },
            }
        },
    }
    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[payload],
    )
    assert report["status"] == "control_manifest_frozen_collect_exact_samples"


def test_holding_flow_forensic_sidecar_is_not_a_natural_control_sample():
    trace = {
        **_trace(),
        "decision_stage": "holding",
        "endpoint": "holding_flow",
        "holding_exact_replay_context_capture_status": "forensic_sidecar_captured",
    }
    payload = {
        "payload_sha256": "payload-1",
        "replay_exact": True,
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sanitized_user_input": {
            "holding_decision_context": {
                "schema": quality.HOLDING_CONTEXT_SCHEMA,
                "venue": "KRX",
                "session": "krx_regular",
                "candle": {
                    "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
                    "bars": [
                        {
                            "minute": "09:00",
                            "close": 100,
                            "is_forming": False,
                        }
                    ],
                },
            }
        },
    }

    report = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[payload],
    )

    assert report["status"] == "control_manifest_gap_fix_required"
    assert report["excluded_counts"] == {
        "holding_flow_forensic_sidecar_not_natural_control": 1
    }
    assert payload["replay_exact"] is True
    assert quality.replay_source_input(payload) is payload["sanitized_user_input"]
    replay_requests = quality.prepare_paired_replay_requests(
        control_manifest={
            "status": "control_manifest_frozen_collect_exact_samples",
            "controls": [
                {
                    "endpoint": "holding_flow",
                    "prompt_version": trace["prompt_version"],
                    "prompt_sha256": trace["prompt_sha256"],
                    "provider_actual": trace["provider_actual"],
                    "model": trace["model"],
                    "request_temperature": trace["request_temperature"],
                    "request_reasoning_effort": trace["request_reasoning_effort"],
                }
            ],
        },
        traces=[trace],
        payloads=[payload],
        labels=[
            {
                **_pending(action="HOLD"),
                "decision_stage": "holding",
                "label_status": "mature",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "30m": {"end_return_pct": 0.5, "first_hit": "target"}
                },
            }
        ],
    )
    assert replay_requests == []


def test_mature_outcome_labels_calculates_mfe_mae_first_hit_and_correlation():
    prices = [
        {
            "timestamp": "2026-07-27T09:01:00+09:00",
            "stock_code": "A005930",
            "price": 98,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass",
        },
        {
            "timestamp": "2026-07-27T09:02:00+09:00",
            "stock_code": "005930",
            "price": 102,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass",
        },
    ]
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=prices,
        lifecycle_rows=[
            {
                "timestamp": "2026-07-27T09:02:30+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "actual_order_submitted": True,
                "filled": True,
                "realized_profit_pct": 0.5,
            }
        ],
        as_of=datetime(2026, 7, 27, 9, 3, tzinfo=KST),
    )
    row = labels[0]
    assert row["label_status"] == "partial"
    assert row["horizon_metrics"]["1m"]["mae_pct"] == -2
    assert row["horizon_metrics"]["1m"]["first_hit"] == "adverse"
    assert row["horizon_metrics"]["1m"]["entry_path_first_hit"] == "adverse_first"
    assert row["horizon_metrics"]["1m"]["entry_path_target_pct"] == 0.3
    assert row["horizon_metrics"]["1m"]["entry_path_adverse_pct"] == -0.7
    assert row["horizon_metrics"]["3m"]["mfe_pct"] == 2
    assert row["stage_outcome"]["entry_path_label_status"] == (
        "pending_primary_horizon"
    )
    assert row["correlation"]["actual_order_submitted"] is True
    assert row["correlation"]["status"] == "exact_matched"
    assert row["correlation"]["realized_separate_from_counterfactual"] is True


def test_outcome_correlation_does_not_treat_missing_or_cross_symbol_as_zero_fill():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 101,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            }
        ],
        lifecycle_rows=[
            {
                "timestamp": "2026-07-27T09:01:30+09:00",
                "stock_code": "000660",
                "record_id": "record-1",
                "actual_order_submitted": True,
                "filled": True,
            }
        ],
        as_of=datetime(2026, 7, 27, 9, 2, tzinfo=KST),
    )

    correlation = labels[0]["correlation"]
    assert correlation["status"] == "open_unresolved"
    assert correlation["matched_event_count"] == 0
    assert correlation["actual_order_submitted"] is None
    assert correlation["fill_observed"] is None


def test_quality_baseline_classifies_false_drop():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending("DROP")],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:05:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            },
            {
                "timestamp": "2026-07-27T09:10:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            },
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )
    labels = quality.annotate_primary_cohort_eligibility(
        labels=labels,
        traces=[_trace("DROP")],
        payloads=[_payload()],
        promotion={"promoted_at": "2026-07-27T08:30:00+09:00"},
    )
    baseline = quality.build_quality_baseline(target_date="2026-07-27", labels=labels)
    assert baseline["status"] == "control_error_baseline_ready"
    assert baseline["taxonomy_counts"]["false_drop"] == 1
    assert baseline["rows"][0]["outcome_return_pct"] == 2
    assert baseline["source_quality_adjusted_ev_pct"] == 0


def test_quality_baseline_waits_for_stage_primary_horizon():
    label = {
        **_pending(),
        "label_status": "partial",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {"3m": {"end_return_pct": 1.0}},
    }
    baseline = quality.build_quality_baseline(target_date="2026-07-27", labels=[label])
    assert baseline["status"] == "partial_horizons_keep_maturing"
    assert baseline["eligible_sample_count"] == 0
    assert baseline["primary_horizon_pending_count"] == 1


def test_quality_baseline_excludes_non_exact_primary_cohort():
    label = {
        **_pending(),
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": False,
        "primary_cohort_exclusion_reasons": ["input_preflight_not_exact_v2"],
        "horizon_metrics": {"10m": {"end_return_pct": 2.0}},
    }

    baseline = quality.build_quality_baseline(
        target_date="2026-07-27",
        labels=[label],
    )

    assert baseline["status"] == "partial_horizons_keep_maturing"
    assert baseline["eligible_sample_count"] == 0
    assert baseline["primary_cohort_ineligible_count"] == 1


def test_mature_outcome_requires_fresh_observation_near_horizon_end():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )

    assert "1m" in labels[0]["horizon_metrics"]
    assert "10m" not in labels[0]["horizon_metrics"]
    assert 10 in labels[0]["pending_horizons_min"]


def test_mature_outcome_rejects_uncontracted_price_source():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:10:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "not_recorded",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )

    assert labels[0]["label_status"] == "pending"
    assert labels[0]["source_quality_status"] == "source_quality_blocked"


def test_kiwoom_completed_minute_loader_excludes_forming_and_wrong_session_bars():
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return (
            [
                {
                    "source_timestamp": "20260727085900",
                    "현재가": 99,
                },
                {
                    "source_timestamp": "20260727090100",
                    "시가": 100,
                    "현재가": 101,
                    "고가": 103,
                    "저가": 98,
                },
                {
                    "source_timestamp": "20260727090300",
                    "현재가": 103,
                },
            ],
            {
                "api_id": "ka10080",
                "received_count": 3,
                "cont_yn_seen": True,
            },
        )

    prices, provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[_pending()],
        as_of=datetime(2026, 7, 27, 9, 3, 20, tzinfo=KST),
        fetcher=fetcher,
    )

    assert calls == [("005930", "005930")]
    assert [row["timestamp"] for row in prices] == ["2026-07-27T09:01:00+09:00"]
    assert prices[0]["source_quality"] == "pass_completed_ka10080_bar"
    assert prices[0]["open"] == 100
    assert prices[0]["high"] == 103
    assert prices[0]["low"] == 98
    assert provenance[0]["source_quality_status"] == "pass_target_window_available"
    assert provenance[0]["target_completed_bar_count"] == 1


def test_outcome_price_merge_prefers_kiwoom_for_same_route_minute():
    primary = [
        {
            "timestamp": "2026-07-27T09:01:00+09:00",
            "stock_code": "005930",
            "price": 101,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "pass_completed_ka10080_bar",
        }
    ]
    fallback = [
        {
            "timestamp": "2026-07-27T09:01:30+09:00",
            "stock_code": "005930",
            "price": 999,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "event_observed",
        },
        {
            "timestamp": "2026-07-27T09:02:30+09:00",
            "stock_code": "005930",
            "price": 102,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "event_observed",
        },
        {
            "timestamp": "2026-07-27T09:01:30+09:00",
            "stock_code": "005930",
            "price": 201,
            "effective_venue": "NXT",
            "session_bucket": "NXT_REGULAR_OVERLAP",
            "source_quality": "event_observed",
        },
    ]

    merged, suppressed = quality.merge_preferred_outcome_price_rows(
        primary,
        fallback,
    )

    assert suppressed == 1
    assert [row["price"] for row in merged] == [101, 102, 201]


def test_outcome_price_merge_retains_exact_post_block_attribution_only():
    primary = [
        {
            "timestamp": "2026-08-03T16:05:00+09:00",
            "stock_code": "459510",
            "price": 101,
            "effective_venue": "NXT",
            "session_bucket": "NXT_AFTERMARKET",
            "source_quality": "pass_completed_ka10080_bar",
        }
    ]
    fallback = [
        {
            "timestamp": "2026-08-03T16:05:16+09:00",
            "stock_code": "459510",
            "price": 101.5,
            "effective_venue": "NXT",
            "session_bucket": "NXT_OPEN_OBSERVE",
            "source_quality": "event_observed",
            "post_block_outcome_provenances": [
                {
                    "evaluation_id": "evaluation-first",
                    "decision_trace_id": "post-block-trace",
                }
            ],
        }
    ]

    merged, suppressed = quality.merge_preferred_outcome_price_rows(
        primary,
        fallback,
    )

    assert suppressed == 1
    assert len(merged) == 2
    assert merged[1]["post_block_attribution_only"] is True
    assert merged[1]["post_block_outcome_provenances"][0]["evaluation_id"] == (
        "evaluation-first"
    )


def test_mature_outcome_uses_bar_high_low_and_marks_same_bar_first_hit_ambiguous():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending()],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 100,
                "high": 102,
                "low": 98,
                "close": 100,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass_completed_ka10080_bar",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 2, tzinfo=KST),
    )

    metric = labels[0]["horizon_metrics"]["1m"]
    assert metric["mfe_pct"] == 2
    assert metric["mae_pct"] == -2
    assert metric["end_return_pct"] == 0
    assert metric["first_hit"] == "ambiguous_same_bar"
    assert metric["entry_path_first_hit"] == "same_bar_ambiguous"


def test_mature_entry_outcome_exposes_ten_minute_tight_stop_path_label():
    price_rows = []
    for minute in (1, 3, 5, 10):
        price_rows.append(
            {
                "timestamp": f"2026-07-27T09:{minute:02d}:00+09:00",
                "stock_code": "005930",
                "price": 100.1,
                "high": 100.4 if minute == 1 else 100.2,
                "low": 99.9 if minute == 1 else (99.2 if minute == 3 else 99.8),
                "close": 100.1,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            }
        )

    row = quality.mature_outcome_labels(
        pending_labels=[_pending("BUY")],
        price_rows=price_rows,
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 11, tzinfo=KST),
    )[0]

    assert row["horizon_metrics"]["10m"]["entry_path_first_hit"] == "target_first"
    assert row["stage_outcome"] == {
        "entry_path_primary_horizon": "10m",
        "entry_path_label_version": "tight_stop_entry_path_v1",
        "entry_path_first_hit": "target_first",
        "entry_path_target_pct": 0.3,
        "entry_path_adverse_pct": -0.7,
        "entry_path_target_hit_at": "2026-07-27T09:01:00+09:00",
        "entry_path_adverse_hit_at": "2026-07-27T09:03:00+09:00",
        "entry_path_label_status": "mature",
        "counterfactual_only": True,
    }


def test_mature_non_entry_outcome_does_not_emit_entry_path_label():
    pending = {**_pending("HOLD"), "decision_stage": "holding"}
    row = quality.mature_outcome_labels(
        pending_labels=[pending],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 99.2,
                "high": 100.4,
                "low": 99.2,
                "close": 99.5,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass",
            }
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 2, tzinfo=KST),
    )[0]

    assert "entry_path_first_hit" not in row["horizon_metrics"]["1m"]
    assert "entry_path_label_version" not in row["horizon_metrics"]["1m"]


def test_mature_outcome_classifies_drawdown_then_profit_recovery():
    labels = quality.mature_outcome_labels(
        pending_labels=[_pending("DROP")],
        price_rows=[
            {
                "timestamp": "2026-07-27T09:01:00+09:00",
                "stock_code": "005930",
                "price": 99.5,
                "high": 100.2,
                "low": 99.0,
                "close": 99.5,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass_completed_ka10080_bar",
            },
            {
                "timestamp": "2026-07-27T09:02:00+09:00",
                "stock_code": "005930",
                "price": 101.2,
                "high": 101.2,
                "low": 99.4,
                "close": 101.0,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass_completed_ka10080_bar",
            },
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 27, 9, 3, tzinfo=KST),
    )

    metric = labels[0]["horizon_metrics"]["3m"]
    assert metric["profit_opportunity_observed"] is True
    assert metric["profit_opportunity_threshold_pct"] == 1.0
    assert metric["profit_opportunity_sequence"] == ("drawdown_then_profit_recovery")
    assert metric["pre_profit_mae_pct"] == -1.0


def test_kiwoom_completed_minute_loader_preserves_nxt_request_suffix():
    pending = {
        **_pending(),
        "effective_venue": "NXT",
        "session_bucket": "NXT_AFTERMARKET",
    }
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return (
            [{"source_timestamp": "20260727160100", "현재가": 101}],
            {"api_id": "ka10080", "received_count": 1},
        )

    prices, _provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[pending],
        as_of=datetime(2026, 7, 27, 16, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert calls == [("005930", "005930_NX")]
    assert prices[0]["effective_venue"] == "NXT"
    assert prices[0]["session_bucket"] == "NXT_AFTERMARKET"


def test_kiwoom_completed_minute_loader_preserves_sor_request_suffix():
    pending = {
        **_pending(),
        "effective_venue": "SOR",
        "session_bucket": "KRX_REGULAR",
    }
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return (
            [{"source_timestamp": "20260727090100", "현재가": 101}],
            {"api_id": "ka10080", "received_count": 1},
        )

    prices, _provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[pending],
        as_of=datetime(2026, 7, 27, 9, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert calls == [("005930", "005930_AL")]
    assert prices[0]["effective_venue"] == "SOR"


def test_kiwoom_completed_minute_loader_accepts_nxt_overlap_session():
    pending = {
        **_pending(),
        "effective_venue": "NXT",
        "session_bucket": "NXT_REGULAR_OVERLAP",
    }

    def fetcher(_stock_code, _request_code):
        return (
            [{"source_timestamp": "20260727120100", "현재가": 101}],
            {"api_id": "ka10080", "received_count": 1},
        )

    prices, _provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[pending],
        as_of=datetime(2026, 7, 27, 12, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert prices[0]["session_bucket"] == "NXT_REGULAR_OVERLAP"


def test_pipeline_lifecycle_preserves_entry_price_trace_for_order_correlation():
    _prices, lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
        [
            {
                "emitted_at": "2026-07-27T09:00:03+09:00",
                "stock_code": "005930",
                "record_id": "record-other",
                "stage": "order_bundle_submitted",
                "fields": {
                    "entry_price_ai_decision_trace_id": "entry-price-trace-1",
                    "broker_order_no": "1234567",
                    "actual_order_submitted": True,
                },
            }
        ]
    )

    assert lifecycle[0]["decision_trace_id"] is None
    assert lifecycle[0]["entry_price_decision_trace_id"] == "entry-price-trace-1"
    correlation = quality._correlation(
        {
            **_pending(),
            "decision_trace_id": "entry-price-trace-1",
            "decision_stage": "entry_price",
            "record_id": "record-1",
        },
        lifecycle,
    )
    assert correlation["status"] == "exact_matched"
    assert correlation["actual_order_submitted"] is True
    mismatch = quality._correlation(
        {
            **_pending(),
            "decision_trace_id": "entry-price-trace-other",
            "decision_stage": "entry_price",
            "record_id": "record-other",
        },
        lifecycle,
    )
    assert mismatch["status"] == "open_unresolved"
    assert mismatch["actual_order_submitted"] is None
    entry_parent = quality._correlation(
        {
            **_pending(),
            "decision_trace_id": "entry-trace-parent",
            "decision_stage": "entry",
            "record_id": "record-other",
        },
        lifecycle,
    )
    assert entry_parent["status"] == "exact_matched"
    assert entry_parent["actual_order_submitted"] is True


def test_pipeline_loader_compacts_usable_prices_and_drops_unusable_event_noise():
    prices, lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
        [
            {
                "emitted_at": "2026-07-27T09:00:03.100000+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "stage": "holding_observation",
                "fields": {
                    "current_price": 100,
                    "effective_venue": "KRX",
                    "session_bucket": "KRX_REGULAR",
                    "source_quality_status": "event_observed",
                    "profit_rate": 1.5,
                },
            },
            {
                "emitted_at": "2026-07-27T09:00:03.900000+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "stage": "holding_observation",
                "fields": {
                    "current_price": 102,
                    "effective_venue": "KRX",
                    "session_bucket": "KRX_REGULAR",
                    "source_quality_status": "event_observed",
                    "profit_rate": 2.0,
                },
            },
            {
                "emitted_at": "2026-07-27T09:00:04+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "stage": "holding_observation",
                "fields": {
                    "current_price": 999,
                    "effective_venue": "KRX",
                    "session_bucket": "KRX_REGULAR",
                },
            },
        ]
    )

    assert prices == [
        {
            "timestamp": "2026-07-27T09:00:03+09:00",
            "stock_code": "005930",
            "price": 102.0,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "event_observed",
            "high": 102.0,
            "low": 100.0,
            "close": 102.0,
        }
    ]
    assert lifecycle == []


def test_pipeline_loader_qualifies_fresh_contract_price_and_normalizes_session():
    prices, _lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
        [
            {
                "emitted_at": "2026-07-31T09:00:01+09:00",
                "stock_code": "005930",
                "stage": "scalping_scanner_fast_precheck",
                "fields": {
                    "current_price_observed": 110,
                    "scanner_promotion_price_effective_curr": 100,
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                    "source_quality_gate": "scalping_scanner_fast_precheck_contract",
                    "scanner_promotion_price_ws_fresh": True,
                    "scanner_promotion_price_conflict": False,
                },
            },
            {
                "emitted_at": "2026-07-31T16:00:25.100000+09:00",
                "stock_code": "005930",
                "stage": "rising_missed_nxt_post_block_price_sample",
                "fields": {
                    "current_price_observed": 101,
                    "effective_venue": "NXT",
                    "rising_missed_market_session_bucket": "nxt_open_observe",
                    "source_quality_gate": (
                        "fresh_absolute_nxt_ws_route_or_bounded_receive_observation"
                    ),
                    "rising_missed_nxt_post_block_fresh_sample": True,
                },
            },
            {
                "emitted_at": "2026-07-31T16:00:26+09:00",
                "stock_code": "005930",
                "stage": "rising_missed_nxt_post_block_price_sample",
                "fields": {
                    "current_price_observed": 999,
                    "effective_venue": "NXT",
                    "rising_missed_market_session_bucket": "nxt_open_observe",
                    "source_quality_gate": (
                        "fresh_absolute_nxt_ws_route_or_bounded_receive_observation"
                    ),
                    "rising_missed_nxt_post_block_fresh_sample": True,
                    "quote_stale": True,
                },
            },
        ]
    )

    assert len(prices) == 2
    assert prices[0]["price"] == 100.0
    assert prices[0]["session_bucket"] == "KRX_REGULAR"
    assert prices[0]["source_quality"] == "event_observed"
    assert prices[1]["price"] == 101.0
    assert prices[1]["session_bucket"] == "NXT_OPEN_OBSERVE"
    assert prices[1]["source_quality"] == "event_observed"
    assert quality._same_route(
        {
            "effective_venue": "NXT",
            "session_bucket": "nxt_aftermarket",
        },
        prices[1],
    )


def test_rising_missed_post_block_outcome_joins_only_its_exact_trace():
    first_trace_id = "analyze_target:459510:first"
    second_trace_id = "analyze_target:459510:second"
    evaluation_id = "evaluation-first"
    pipeline_rows = [
        {
            "emitted_at": "2026-08-03T16:01:25.467742+09:00",
            "stock_code": "459510",
            "stage": "rising_missed_nxt_post_block_sampler_registered",
            "fields": {
                "rising_missed_tp1_evaluation_id": evaluation_id,
                "rising_missed_effective_venue": "NXT",
                "rising_missed_market_session_bucket": "nxt_open_observe",
                "rising_missed_nxt_post_block_sampler_entry_price": 100,
                "rising_missed_nxt_post_block_source_block_stage": "tp1_selector",
                "rising_missed_nxt_post_block_source_block_reason": (
                    "rising_missed_tp1_ai_state_blocked"
                ),
            },
        },
        {
            "emitted_at": "2026-08-03T16:01:25.468085+09:00",
            "stock_code": "459510",
            "stage": "rising_missed_tp1_candidate_blocked",
            "fields": {
                "rising_missed_tp1_evaluation_id": evaluation_id,
                "rising_missed_tp1_ai_decision_trace_id": first_trace_id,
                "rising_missed_tp1_gross_target_pct": 1.3,
                "rising_missed_tp1_adverse_stop_pct": -0.7,
                "rising_missed_tp1_horizon_sec": 1200,
            },
        },
        *[
            {
                "emitted_at": timestamp,
                "stock_code": "459510",
                "stage": "rising_missed_nxt_post_block_price_sample",
                "fields": {
                    "rising_missed_tp1_evaluation_id": evaluation_id,
                    "rising_missed_effective_venue": "NXT",
                    "rising_missed_market_session_bucket": "nxt_open_observe",
                    "source_quality_gate": (
                        "fresh_absolute_nxt_ws_route_or_bounded_ka10004_receive_observation"
                    ),
                    "rising_missed_nxt_post_block_fresh_sample": True,
                    "current_price_observed": price,
                },
            }
            for timestamp, price in (
                ("2026-08-03T16:01:30+09:00", 100.0),
                ("2026-08-03T16:05:16+09:00", 101.5),
                ("2026-08-03T16:06:10+09:00", 101.4),
            )
        ],
    ]

    prices, _lifecycle = quality.load_pipeline_price_and_lifecycle_rows(pipeline_rows)

    assert len(prices) == 3
    assert prices[1]["effective_venue"] == "NXT"
    assert prices[1]["session_bucket"] == "NXT_OPEN_OBSERVE"
    assert prices[1]["post_block_outcome_provenances"] == [
        {
            "label_version": quality.RISING_MISSED_POST_BLOCK_LABEL_VERSION,
            "evaluation_id": evaluation_id,
            "stock_code": "459510",
            "decision_trace_id": first_trace_id,
            "registered_at": "2026-08-03T16:01:25.467742+09:00",
            "reference_price": 100.0,
            "effective_venue": "NXT",
            "session_bucket": "NXT_OPEN_OBSERVE",
            "gross_target_pct": 1.3,
            "adverse_pct": -0.7,
            "horizon_sec": 1200.0,
            "source_block_stage": "tp1_selector",
            "source_block_reason": "rising_missed_tp1_ai_state_blocked",
            "source_quality_status": "pass_exact_trace_evaluation_join",
            "counterfactual_only": True,
        }
    ]
    pending = {
        **_pending(),
        "decision_trace_id": first_trace_id,
        "decision_ts": "2026-08-03T16:01:23.495804+09:00",
        "stock_code": "459510",
        "effective_venue": "NXT",
        "session_bucket": "nxt_aftermarket",
        "reference_price": 100.1,
    }
    second_pending = {
        **pending,
        "decision_trace_id": second_trace_id,
        "decision_ts": "2026-08-03T16:03:56.604917+09:00",
        "reference_price": 101.4,
    }
    labels = quality.mature_outcome_labels(
        pending_labels=[pending, second_pending],
        price_rows=prices,
        lifecycle_rows=[],
        as_of=datetime.fromisoformat("2026-08-03T16:06:30+09:00"),
    )

    first_outcome = labels[0]["stage_outcome"]["rising_missed_post_block_outcome"]
    assert first_outcome["evaluation_id"] == evaluation_id
    assert first_outcome["decision_trace_id"] == first_trace_id
    assert first_outcome["gross_first_hit_label"] == "gross_target_first"
    assert first_outcome["target_hit_at"] == "2026-08-03T16:05:16+09:00"
    assert first_outcome["adverse_hit_at"] is None
    assert first_outcome["max_move_pct"] == 1.5
    assert first_outcome["source_quality_status"] == "pass"
    assert "false_drop_post_block_gross_target_first" in quality._taxonomy(labels[0])
    assert labels[1]["stage_outcome"].get("rising_missed_post_block_outcome") is None


def test_pipeline_loader_preserves_same_second_post_block_evaluations():
    rows = []
    for offset, evaluation_id in enumerate(("evaluation-a", "evaluation-b")):
        rows.extend(
            [
                {
                    "emitted_at": f"2026-08-03T16:01:25.46774{offset}+09:00",
                    "stock_code": "459510",
                    "stage": "rising_missed_nxt_post_block_sampler_registered",
                    "fields": {
                        "rising_missed_tp1_evaluation_id": evaluation_id,
                        "rising_missed_effective_venue": "NXT",
                        "rising_missed_market_session_bucket": "nxt_open_observe",
                        "rising_missed_nxt_post_block_sampler_entry_price": 100,
                    },
                },
                {
                    "emitted_at": f"2026-08-03T16:01:25.46808{offset}+09:00",
                    "stock_code": "459510",
                    "stage": "rising_missed_tp1_candidate_blocked",
                    "fields": {
                        "rising_missed_tp1_evaluation_id": evaluation_id,
                        "rising_missed_tp1_ai_decision_trace_id": f"trace-{offset}",
                        "rising_missed_tp1_gross_target_pct": 1.3,
                        "rising_missed_tp1_adverse_stop_pct": -0.7,
                        "rising_missed_tp1_horizon_sec": 1200,
                    },
                },
                {
                    "emitted_at": f"2026-08-03T16:01:30.10000{offset}+09:00",
                    "stock_code": "459510",
                    "stage": "rising_missed_nxt_post_block_price_sample",
                    "fields": {
                        "rising_missed_tp1_evaluation_id": evaluation_id,
                        "rising_missed_effective_venue": "NXT",
                        "rising_missed_market_session_bucket": "nxt_open_observe",
                        "source_quality_gate": (
                            "fresh_absolute_nxt_ws_route_or_bounded_ka10004_"
                            "receive_observation"
                        ),
                        "rising_missed_nxt_post_block_fresh_sample": True,
                        "current_price_observed": 100 + offset,
                    },
                },
            ]
        )

    prices, _lifecycle = quality.load_pipeline_price_and_lifecycle_rows(rows)

    assert len(prices) == 1
    assert {
        provenance["evaluation_id"]
        for provenance in prices[0]["post_block_outcome_provenances"]
    } == {"evaluation-a", "evaluation-b"}


def test_pipeline_loader_qualifies_fresh_evaluated_holding_exact_bid():
    prices, lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
        [
            {
                "emitted_at": "2026-08-03T14:26:32.790850",
                "stock_code": "001740",
                "stage": "ai_holding_review",
                "fields": {
                    "ai_prompt_type": "scalping_holding_score",
                    "holding_context_schema": quality.HOLDING_CONTEXT_SCHEMA,
                    "ai_result_source": "live",
                    "ai_decision_evaluation_status": "evaluated",
                    "holding_score_preflight_blocked": False,
                    "holding_score_preflight_source_quality": "fresh",
                    "holding_context_venue": "KRX",
                    "holding_context_session": "krx_regular",
                    "holding_context_quote_age_ms": 823.769,
                    "holding_context_bbo_fresh": True,
                    "holding_context_source_quality_status": "partial",
                    "holding_context_blockers": "[]",
                    "holding_context_candle_route_conflict_count": 0,
                    "holding_context_position_valid": True,
                    "holding_context_order_consistent": True,
                    "holding_context_best_bid": 7040,
                    "holding_context_best_ask": 7090,
                    "quote_stale": False,
                    "tick_context_stale": False,
                },
            }
        ]
    )

    assert prices == [
        {
            "timestamp": "2026-08-03T14:26:32+09:00",
            "stock_code": "001740",
            "price": 7040.0,
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality": "event_observed_holding_exact",
            "high": 7040.0,
            "low": 7040.0,
            "close": 7040.0,
        }
    ]
    assert lifecycle == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"holding_context_schema": "legacy_holding_context"},
        {"holding_score_preflight_blocked": True},
        {"holding_context_blockers": '["route_conflict"]'},
        {"holding_context_candle_route_conflict_count": 1},
        {"holding_context_position_valid": False},
        {"holding_context_order_consistent": False},
        {"holding_context_quote_age_ms": 3000.001},
        {"quote_stale": True},
        {"tick_context_stale": True},
    ],
)
def test_pipeline_loader_rejects_blocked_or_stale_holding_price(overrides):
    fields = {
        "ai_prompt_type": "scalping_holding_score",
        "holding_context_schema": quality.HOLDING_CONTEXT_SCHEMA,
        "ai_result_source": "live",
        "ai_decision_evaluation_status": "evaluated",
        "holding_score_preflight_blocked": False,
        "holding_score_preflight_source_quality": "fresh",
        "holding_context_venue": "KRX",
        "holding_context_session": "krx_regular",
        "holding_context_quote_age_ms": 800,
        "holding_context_bbo_fresh": True,
        "holding_context_source_quality_status": "partial",
        "holding_context_blockers": "[]",
        "holding_context_candle_route_conflict_count": 0,
        "holding_context_position_valid": True,
        "holding_context_order_consistent": True,
        "holding_context_best_bid": 7040,
        "quote_stale": False,
        "tick_context_stale": False,
    }
    fields.update(overrides)

    prices, _lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
        [
            {
                "emitted_at": "2026-08-03T14:26:32+09:00",
                "stock_code": "001740",
                "stage": "ai_holding_review",
                "fields": fields,
            }
        ]
    )

    assert prices == []


def test_pipeline_loader_never_treats_unrealized_holding_pnl_as_realized():
    _prices, lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
        [
            {
                "emitted_at": "2026-07-27T09:00:03+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "stage": "holding_observation",
                "fields": {"profit_rate": 1.5},
            },
            {
                "emitted_at": "2026-07-27T09:02:03+09:00",
                "stock_code": "005930",
                "record_id": "record-1",
                "stage": "sell_filled",
                "fields": {
                    "broker_order_no": "1234567",
                    "profit_rate": 1.2,
                    "filled": True,
                },
            },
        ]
    )

    assert len(lifecycle) == 1
    assert lifecycle[0]["stage"] == "sell_filled"
    assert lifecycle[0]["realized_profit_pct"] == 1.2


def test_kiwoom_completed_minute_loader_blocks_ambiguous_or_conflicting_route():
    calls = []

    def fetcher(stock_code, request_code):
        calls.append((stock_code, request_code))
        return [], {}

    prices, provenance = quality.load_kiwoom_completed_minute_price_rows(
        target_date="2026-07-27",
        labels=[
            {
                **_pending(),
                "effective_venue": "PREMARKET_KRX_LIKE",
                "session_bucket": "PREMARKET_KRX_LIKE",
            },
            {
                **_pending(),
                "effective_venue": "KRX",
                "session_bucket": "NXT_AFTERMARKET",
            },
        ],
        as_of=datetime(2026, 7, 27, 16, 3, tzinfo=KST),
        fetcher=fetcher,
    )

    assert prices == []
    assert calls == []
    assert {row["fetch_error"] for row in provenance} == {
        "unsupported_effective_venue",
        "venue_session_conflict",
    }
    assert all(
        row["source_quality_status"] == "source_quality_blocked" for row in provenance
    )


def test_score_outcome_correlation_report_uses_spearman_primary_and_sample_floor():
    labels = []
    for index in range(30):
        score = float(index)
        labels.append(
            {
                **_pending(),
                "decision_trace_id": f"trace-{index}",
                "stock_code": f"{index % 10:06d}",
                "score": score,
                "label_status": "partial",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "10m": {
                        "mfe_pct": score,
                        "mae_pct": score - 29.0,
                    }
                },
            }
        )

    report = quality.build_score_outcome_correlation_report(
        target_date="2026-07-27",
        labels=labels,
    )

    assert report["status"] == "exploratory_score_outcome_correlation_available"
    bucket = report["buckets"][0]
    assert bucket["sample_floor_pass"] is True
    assert bucket["score_vs_mfe_pct"]["spearman"] == 1.0
    assert bucket["score_vs_mae_pct"]["spearman"] == 1.0
    assert bucket["score_vs_adverse_magnitude_pct"]["spearman"] == -1.0
    assert bucket["interpretation_contract"]["pearson_role"] == "diagnostic_only"


def test_default_sources_skips_large_pipeline_load_when_not_requested(monkeypatch):
    loaded_paths = []

    def fake_load(path):
        loaded_paths.append(path)
        return []

    monkeypatch.setattr(quality, "_load_jsonl", fake_load)
    sources = quality._default_sources("2026-07-27", include_pipeline=False)

    assert sources["pipeline"] == []
    assert all(path.parent != quality.PIPELINE_DIR for path in loaded_paths)


def test_default_sources_keeps_pipeline_lazy_and_limits_entry_to_target_date(
    monkeypatch,
):
    loaded_paths = []

    def fake_load(path):
        loaded_paths.append(path)
        if path.parent == quality.OUTCOME_DIR:
            return [
                {
                    "decision_stage": "entry",
                    "decision_ts": "2026-07-27T09:00:00+09:00",
                }
            ]
        return []

    monkeypatch.setattr(quality, "_load_jsonl", fake_load)
    sources = quality._default_sources("2026-07-27", include_pipeline=True)

    assert sources["pipeline"] == []
    assert len(sources["pipeline_paths"]) == 1
    assert sources["pipeline_paths"][0].name in {
        "pipeline_events_2026-07-27.jsonl",
        "pipeline_events_2026-07-27.jsonl.gz",
    }
    assert all(path.parent != quality.PIPELINE_DIR for path in loaded_paths)


def test_overnight_outcome_uses_next_day_first_session_window():
    pending = {
        **_pending("HOLD_OVERNIGHT"),
        "decision_stage": "overnight",
        "decision_ts": "2026-07-27T19:50:00+09:00",
        "effective_venue": "NXT",
        "session_bucket": "NXT_AFTERMARKET",
    }
    labels = quality.mature_outcome_labels(
        pending_labels=[pending],
        price_rows=[
            {
                "timestamp": "2026-07-27T19:51:00+09:00",
                "stock_code": "005930",
                "price": 120,
                "effective_venue": "NXT",
                "session_bucket": "NXT_AFTERMARKET",
                "source_quality": "pass",
            },
            {
                "timestamp": "2026-07-28T08:00:00+09:00",
                "stock_code": "005930",
                "price": 102,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "session_bucket": "PREMARKET_KRX_LIKE",
                "source_quality": "pass",
            },
            {
                "timestamp": "2026-07-28T08:10:00+09:00",
                "stock_code": "005930",
                "price": 103,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "session_bucket": "PREMARKET_KRX_LIKE",
                "source_quality": "pass",
            },
        ],
        lifecycle_rows=[],
        as_of=datetime(2026, 7, 28, 8, 11, tzinfo=KST),
    )

    metric = labels[0]["horizon_metrics"]["10m"]
    assert metric["window_basis"] == "next_session_from_first_observation"
    assert metric["mfe_pct"] == 3
    assert metric["gap_from_reference_pct"] == 2
    assert labels[0]["stage_outcome"]["next_session_date"] == "2026-07-28"
    assert labels[0]["stage_outcome"]["next_session_bucket"] == "PREMARKET_KRX_LIKE"


def test_candidate_contract_requires_structured_reasons():
    response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.2,
        "expected_downside_pct": -0.5,
        "confidence": 70,
        "reason_codes": ["trend_tape_aligned"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "supportive",
            "risk": "low",
            "uncertainty": "low",
            "setup": "continuation",
            "positive_edge": "strong",
            "adverse_risk": "low",
            "trigger": "confirmed",
        },
    }
    assert quality.validate_candidate_response(response, stage="entry") == []
    assert quality.decision_quality_v2_system_prompt("entry").isascii()

    invalid = {**response, "reason_codes": ["Not canonical"]}
    invalid.pop("expected_downside_pct")
    assert quality.validate_candidate_response(invalid, stage="entry") == [
        "expected_downside_pct_missing",
        "expected_edge_values_required",
        "reason_codes_invalid",
    ]
    unsupported = {**response, "reason_codes": ["invented_ascii_reason"]}
    assert quality.validate_candidate_response(unsupported, stage="entry") == [
        "reason_codes_invalid"
    ]
    duplicate = {
        **response,
        "reason_codes": ["trend_tape_aligned", "trend_tape_aligned"],
    }
    assert quality.validate_candidate_response(duplicate, stage="entry") == [
        "reason_codes_invalid"
    ]
    no_edge_wait = {
        **response,
        "edge_state": "NO_EDGE",
        "action": "WAIT",
        "expected_upside_pct": 0.3,
        "expected_downside_pct": -0.4,
        "evidence": {
            **response["evidence"],
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "moderate",
            "trigger": "not_applicable",
        },
    }
    assert quality.validate_candidate_response(no_edge_wait, stage="entry") == [
        "entry_no_edge_requires_drop"
    ]
    unsafe_buy = {
        **response,
        "expected_upside_pct": 0.4,
        "expected_downside_pct": -0.5,
        "evidence": {
            **response["evidence"],
            "adverse_risk": "blocking",
            "trigger": "recovery_required",
        },
    }
    assert quality.validate_candidate_response(unsafe_buy, stage="entry") == [
        "entry_buy_requires_confirmed_trigger",
        "entry_buy_adverse_risk_too_high",
        "entry_buy_reward_risk_below_floor",
    ]
    unfavorable_edge_drop = {
        **response,
        "action": "DROP",
        "expected_upside_pct": 0.4,
        "expected_downside_pct": -0.5,
        "evidence": {
            **response["evidence"],
            "adverse_risk": "high",
        },
    }
    assert (
        quality.validate_candidate_response(unfavorable_edge_drop, stage="entry") == []
    )
    prompt = quality.decision_quality_v2_system_prompt("entry")
    assert "Do not erase either ledger by averaging them together." in prompt
    assert "trusted supportive tape" in prompt
    assert "Ask-heavy depth" in prompt
    assert "NO_EDGE" in prompt
    assert "WAIT is invalid." in prompt


def test_holding_candidate_rejects_false_missing_core_and_one_share_trim():
    payload = {
        "position_context": {"buy_qty": 1, "buy_price": 100},
        "holding_decision_context": {
            "execution_pnl": {
                "remaining_qty": 1,
                "average_entry_price": 100,
                "executable_sell_price": 99,
            },
            "position_lifecycle": {"memory_qty": 1},
            "source_quality": {
                "status": "fresh_consistent",
                "candle_status": "fresh_consistent",
                "bbo_fresh": True,
                "position_valid": True,
                "order_consistent": True,
                "position_reconciled": False,
            },
            "candle": {
                "completed_bar_count": 2,
                "bars": [{"minute": "09:00", "close": 100, "is_forming": False}],
            },
        },
    }
    response = {
        "edge_state": "INSUFFICIENT_DATA",
        "action": "HOLD",
        "expected_upside_pct": None,
        "expected_downside_pct": None,
        "confidence": 40,
        "reason_codes": [
            "broker_state_missing",
            "completed_bars_missing",
            "source_stale",
            "insufficient_core_data",
        ],
        "evidence": {
            "trend": "insufficient",
            "liquidity": "insufficient",
            "tape": "insufficient",
            "risk": "insufficient",
            "uncertainty": "high",
            "setup": "insufficient",
            "positive_edge": "insufficient",
            "adverse_risk": "insufficient",
            "trigger": "insufficient",
        },
    }

    assert quality.validate_candidate_response(
        response, stage="holding", exact_payload=payload
    ) == [
        "holding_broker_state_missing_misclassified",
        "holding_completed_bars_missing_misclassified",
        "holding_sufficient_core_misclassified",
        "holding_source_quality_misclassified",
    ]

    trim = {
        **response,
        "edge_state": "NO_EDGE",
        "action": "TRIM",
        "expected_upside_pct": 0.2,
        "expected_downside_pct": -0.5,
        "reason_codes": ["edge_absent"],
        "evidence": {
            **response["evidence"],
            "trend": "adverse",
            "liquidity": "mixed",
            "tape": "adverse",
            "risk": "high",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "high",
            "trigger": "failed",
        },
    }
    assert quality.validate_candidate_response(
        trim, stage="holding", exact_payload=payload
    ) == ["holding_trim_requires_multiple_shares"]


def test_entry_candidate_rejects_trigger_reason_evidence_conflict():
    response = {
        "edge_state": "EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.9,
        "expected_downside_pct": -1.0,
        "confidence": 78,
        "reason_codes": [
            "recovery_trigger_confirmed",
            "risk_reward_unfavorable",
            "structural_edge_without_trigger",
        ],
        "evidence": {
            "trend": "supportive",
            "liquidity": "adverse",
            "tape": "supportive",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "blocking",
            "trigger": "confirmed",
        },
    }

    assert quality.validate_candidate_response(response, stage="entry") == [
        "entry_trigger_reason_evidence_conflict"
    ]
    for reason_code, contradictory_trigger in (
        ("recovery_trigger_confirmed", "failed"),
        ("recovery_trigger_required", "confirmed"),
        ("recovery_trigger_failed", "confirmed"),
    ):
        contradictory = {
            **response,
            "reason_codes": [reason_code, "risk_reward_unfavorable"],
            "evidence": {
                **response["evidence"],
                "trigger": contradictory_trigger,
            },
        }
        assert quality.validate_candidate_response(contradictory, stage="entry") == [
            "entry_trigger_reason_evidence_conflict"
        ]


def test_entry_candidate_rejects_directional_reason_code_conflicts():
    base = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.2,
        "expected_downside_pct": -0.8,
        "confidence": 78,
        "reason_codes": ["edge_absent"],
        "evidence": {
            "trend": "adverse",
            "liquidity": "adverse",
            "tape": "mixed",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "weak",
            "adverse_risk": "high",
            "trigger": "not_applicable",
        },
    }

    for supportive, adverse in (
        ("trend_supportive", "trend_adverse"),
        ("liquidity_supportive", "liquidity_adverse"),
        ("tape_supportive", "tape_adverse"),
    ):
        response = {
            **base,
            "reason_codes": ["edge_absent", supportive, adverse],
        }
        assert quality.validate_candidate_response(response, stage="entry") == [
            "reason_codes_conflict"
        ]


def test_entry_candidate_contract_separates_structural_edge_and_adverse_risk():
    exact_payload = {
        "current": {"fluctuation_pct": 8.0},
        "features": {
            "curr_vs_micro_vwap_bp": -20,
            "curr_vs_ma5_bp": -10,
            "entry_order_flow_status": "adverse",
        },
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "1": 0.2,
                    "3": 0.5,
                    "5": 0.8,
                    "10": 1.2,
                    "20": 2.0,
                    "60": 3.0,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.2,
                    "20": 0.2,
                    "60": 0.1,
                },
                "regime": "range",
                "alignment": "neutral",
            }
        },
    }
    recovery_response = {
        "edge_state": "EDGE",
        "action": "WAIT",
        "expected_upside_pct": 1.4,
        "expected_downside_pct": -0.8,
        "confidence": 68,
        "reason_codes": [
            "edge_positive",
            "pullback_recovery_candidate",
            "recovery_trigger_required",
        ],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "adverse",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "pullback_recovery",
            "positive_edge": "moderate",
            "adverse_risk": "high",
            "trigger": "recovery_required",
        },
    }
    assert (
        quality.validate_candidate_response(
            recovery_response,
            stage="entry",
            exact_payload=exact_payload,
        )
        == []
    )

    misclassified = {
        **recovery_response,
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "reason_codes": ["edge_absent"],
        "evidence": {
            **recovery_response["evidence"],
            "setup": "no_setup",
            "positive_edge": "none",
            "trigger": "not_applicable",
        },
    }
    errors = quality.validate_candidate_response(
        misclassified,
        stage="entry",
        exact_payload=exact_payload,
    )
    assert "entry_structural_edge_floor_misclassified" in errors
    assert "entry_orderly_pullback_recovery_misclassified" in errors

    overextended_payload = {
        **exact_payload,
        "current": {"fluctuation_pct": 20.0},
        "features": {
            **exact_payload["features"],
            "curr_vs_micro_vwap_bp": 120,
            "curr_vs_ma5_bp": 100,
        },
    }
    blocked_response = {
        **recovery_response,
        "action": "DROP",
        "expected_upside_pct": 0.6,
        "expected_downside_pct": -1.0,
        "reason_codes": [
            "edge_positive",
            "overextension_chase_risk",
            "risk_reward_unfavorable",
            "recovery_trigger_failed",
        ],
        "evidence": {
            **recovery_response["evidence"],
            "setup": "continuation",
            "adverse_risk": "blocking",
            "trigger": "failed",
        },
    }
    assert (
        quality.validate_candidate_response(
            blocked_response,
            stage="entry",
            exact_payload=overextended_payload,
        )
        == []
    )

    trusted_supportive_payload = {
        **exact_payload,
        "features": {
            **exact_payload["features"],
            "curr_vs_micro_vwap_bp": 15,
            "curr_vs_ma5_bp": 10,
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "buy_pressure_10t": 90,
            "net_aggressive_delta_10t": 25,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
        },
    }
    confirmed_response = {
        **recovery_response,
        "action": "BUY",
        "expected_upside_pct": 1.5,
        "expected_downside_pct": -0.8,
        "reason_codes": [
            "edge_positive",
            "tape_supportive",
            "recovery_trigger_confirmed",
            "risk_reward_favorable",
        ],
        "evidence": {
            **recovery_response["evidence"],
            "tape": "supportive",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    assert (
        quality.validate_candidate_response(
            confirmed_response,
            stage="entry",
            exact_payload=trusted_supportive_payload,
        )
        == []
    )
    trusted_tape_misclassified = {
        **confirmed_response,
        "action": "WAIT",
        "reason_codes": [
            "edge_positive",
            "tape_adverse",
            "recovery_trigger_required",
        ],
        "evidence": {
            **confirmed_response["evidence"],
            "tape": "adverse",
            "trigger": "recovery_required",
        },
    }
    assert "entry_trusted_supportive_trigger_misclassified" in (
        quality.validate_candidate_response(
            trusted_tape_misclassified,
            stage="entry",
            exact_payload=trusted_supportive_payload,
        )
    )


def test_entry_candidate_rejects_thin_tape_over_adverse_completed_distribution():
    exact_payload = {
        "current": {"price": 30150, "fluctuation_pct": 5.42},
        "features": {
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "buy_pressure_10t": 100.0,
            "net_aggressive_delta_10t": 8,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 6,
            "tick_context_quality": "accel_insufficient_ticks",
            "tick_accel_source": "insufficient_ticks",
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "spread_bp": 82.92,
            "top1_bid_notional": 331650,
            "top1_ask_notional": 5065200,
        },
        "entry_candle_context": {
            "structure": {
                "returns_pct": {"1": -0.1656, "3": 0.5, "5": -0.8224, "10": -2.4272},
                "slopes_pct_per_bar": {
                    "1": -0.1656,
                    "3": -0.1653,
                    "5": 0.0663,
                    "10": -0.1202,
                    "20": -0.0277,
                },
                "peak_drawdown_pct": -3.9809,
                "high_direction": "down",
                "volume_ratio": 0.253,
                "volume_direction_alignment": "price_volume_divergence",
                "regime": "range",
                "alignment": "neutral",
            }
        },
    }
    correct = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.4,
        "expected_downside_pct": -1.0,
        "confidence": 82,
        "reason_codes": [
            "edge_absent",
            "distribution_adverse",
            "volume_confirmation_missing",
            "tape_sample_insufficient",
            "ask_wall_adverse",
        ],
        "evidence": {
            "trend": "adverse",
            "liquidity": "adverse",
            "tape": "mixed",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "blocking",
            "trigger": "failed",
        },
    }
    assert (
        quality.validate_candidate_response(
            correct,
            stage="entry",
            exact_payload=exact_payload,
        )
        == []
    )
    generic_liquidity_code = {
        **correct,
        "reason_codes": [
            code if code != "ask_wall_adverse" else "liquidity_adverse"
            for code in correct["reason_codes"]
        ],
    }
    assert (
        quality.validate_candidate_response(
            generic_liquidity_code,
            stage="entry",
            exact_payload=exact_payload,
        )
        == []
    )
    overstated = {
        **correct,
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.4,
        "expected_downside_pct": -0.8,
        "reason_codes": [
            "edge_positive",
            "tape_supportive",
            "recovery_trigger_confirmed",
        ],
        "evidence": {
            **correct["evidence"],
            "trend": "mixed",
            "liquidity": "supportive",
            "tape": "supportive",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    errors = quality.validate_candidate_response(
        overstated,
        stage="entry",
        exact_payload=exact_payload,
    )
    assert "entry_thin_tape_sample_overstated" in errors
    assert "entry_adverse_distribution_misclassified" in errors
    assert "entry_ask_wall_wide_spread_misclassified" in errors

    missing_tick_count_payload = {
        **exact_payload,
        "features": {
            **exact_payload["features"],
        },
    }
    missing_tick_count_payload["features"].pop("tick_aggressor_trusted_count", None)
    missing_tick_count_errors = quality.validate_candidate_response(
        overstated,
        stage="entry",
        exact_payload=missing_tick_count_payload,
    )
    assert "entry_thin_tape_sample_overstated" in missing_tick_count_errors

    insufficient = {
        **correct,
        "edge_state": "INSUFFICIENT_DATA",
        "action": "WAIT",
        "expected_upside_pct": None,
        "expected_downside_pct": None,
        "reason_codes": ["insufficient_core_data"],
        "evidence": {
            **correct["evidence"],
            "trend": "insufficient",
            "liquidity": "insufficient",
            "tape": "insufficient",
            "risk": "insufficient",
            "setup": "insufficient",
            "positive_edge": "insufficient",
            "adverse_risk": "insufficient",
            "trigger": "insufficient",
        },
    }
    assert (
        quality.validate_candidate_response(
            insufficient,
            stage="entry",
            exact_payload=exact_payload,
        )
        == []
    )

    analysis = quality.build_exact_payload_analysis_v1(
        exact_payload,
        stage="entry",
    )
    assert analysis["schema"] == "exact_payload_analysis_v1"
    assert analysis["completed_structure"]["phase"] == "distribution"
    assert analysis["completed_structure"]["structural_edge"] == "absent"
    assert analysis["volume_confirmation"]["state"] == "confirmation_absent"
    assert analysis["tape_sample"]["state"] == "too_thin"
    assert analysis["executable_liquidity"]["state"] == "blocking"
    assert analysis["trigger_state"] == "failed"
    assert analysis["analysis_sha256"]
    assert analysis["observation_contract"]["runtime_effect"] is False


def test_early_session_available_horizons_preserve_continuation_edge_and_depth():
    exact_payload = {
        "current": {"price": 14900, "fluctuation_pct": 13.91},
        "features": {
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "flat",
            "buy_pressure_10t": 93.33,
            "net_aggressive_delta_10t": 156,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "same_second_burst_10ticks",
            "spread_bp": 40.27,
            "top1_bid_notional": 536_400,
            "top1_ask_notional": 4_246_500,
            "top3_bid_notional": 14_870_200,
            "top3_ask_notional": 11_145_200,
            "fillability_score": 38,
            "would_fill_now": False,
        },
        "entry_candle_context": {
            "completed_bar_count": 13,
            "structure": {
                "returns_pct": {"1": 1.717, "3": 7.5527, "5": 7.6308, "10": 6.8543},
                "slopes_pct_per_bar": {
                    "1": 1.717,
                    "3": 2.2952,
                    "5": 2.1971,
                    "10": 0.5737,
                },
                "peak_drawdown_pct": -0.2694,
                "high_direction": "up_or_flat",
                "low_direction": "up_or_flat",
                "volume_ratio": 3.937,
                "volume_direction_alignment": "bullish_confirmed",
                "regime": "breakout",
                "alignment": "positive",
            },
        },
    }

    facts = quality._entry_contract_facts(exact_payload)
    analysis = quality.build_exact_payload_analysis_v1(exact_payload, stage="entry")

    assert facts["long_horizon_structural_edge_floor"] is False
    assert facts["early_session_structural_edge_floor"] is True
    assert facts["structural_edge_floor"] is True
    assert facts["early_session_probe_candidate"] is True
    assert analysis["completed_structure"]["phase"] == "continuation"
    assert analysis["completed_structure"]["structural_edge"] == "moderate"
    assert analysis["completed_structure"]["structural_edge_policy_version"] == (
        "session_available_horizons_v2"
    )
    assert analysis["trigger_state"] == "recovery_required"
    assert analysis["executable_liquidity"]["state"] == "mixed"
    assert analysis["executable_liquidity"]["directional_depth_state"] == "mixed"
    assert analysis["executable_liquidity"]["execution_cost_state"] == "observable"

    rejected_drop = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.0,
        "expected_downside_pct": -1.2,
        "confidence": 78,
        "reason_codes": ["edge_absent", "liquidity_adverse"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "adverse",
            "tape": "supportive",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "blocking",
            "trigger": "not_applicable",
        },
    }
    errors = quality.validate_candidate_response(
        rejected_drop,
        stage="entry",
        exact_payload=exact_payload,
        enforce_live_probe_contract=True,
    )
    assert "entry_structural_edge_floor_misclassified" in errors
    assert "entry_early_session_probe_misclassified" in errors


def test_three_bar_early_probe_requires_bounded_cost_and_independent_support():
    exact_payload = {
        "current": {"price": 145900, "fluctuation_pct": 7.6},
        "features": {
            "entry_order_flow_status": "neutral",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "buy_pressure_10t": 58.33,
            "net_aggressive_delta_10t": 14,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "same_second_burst_10ticks",
            "spread_bp": 47.98,
            "top1_bid_notional": 21_447_300,
            "top1_ask_notional": 291_800,
            "top3_bid_notional": 37_204_500,
            "top3_ask_notional": 1_459_000,
            "would_fill_now": True,
        },
        "entry_candle_context": {
            "completed_bar_count": 3,
            "structure": {
                "returns_pct": {"1": 1.8336},
                "slopes_pct_per_bar": {"1": 1.8336, "3": 1.2784},
                "peak_drawdown_pct": -0.1383,
                "high_direction": "up_or_flat",
                "low_direction": "up_or_flat",
                "volume_ratio": 1.567,
                "volume_direction_alignment": "not_available",
                "regime": "range",
                "alignment": "neutral",
            },
        },
    }

    facts = quality._entry_contract_facts(exact_payload)
    analysis = quality.build_exact_payload_analysis_v1(exact_payload, stage="entry")

    assert facts["structural_edge_floor"] is False
    assert facts["early_session_probe_candidate"] is True
    assert analysis["completed_structure"]["phase"] == "early_continuation_probe"
    assert analysis["trigger_state"] == "recovery_required"
    assert analysis["executable_liquidity"]["state"] == "supportive"
    assert analysis["executable_liquidity"]["directional_depth_state"] == "supportive"
    assert analysis["executable_liquidity"]["execution_cost_state"] == "observable"

    offline_buy = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 2.0,
        "expected_downside_pct": -1.0,
        "confidence": 70,
        "reason_codes": [
            "edge_positive",
            "continuation_supported",
            "recovery_trigger_confirmed",
        ],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    assert (
        "entry_early_session_probe_misclassified"
        not in quality.validate_candidate_response(
            offline_buy,
            stage="entry",
            exact_payload=exact_payload,
        )
    )
    assert (
        "entry_early_session_probe_misclassified"
        in quality.validate_candidate_response(
            offline_buy,
            stage="entry",
            exact_payload=exact_payload,
            enforce_live_probe_contract=True,
        )
    )

    too_wide = {
        **exact_payload,
        "features": {**exact_payload["features"], "spread_bp": 50.01},
    }
    assert (
        quality._entry_contract_facts(too_wide)["early_session_probe_candidate"]
        is False
    )

    negative_prior_close = {
        **exact_payload,
        "current": {**exact_payload["current"], "fluctuation_pct": -0.01},
    }
    assert (
        quality._entry_contract_facts(negative_prior_close)[
            "early_session_probe_candidate"
        ]
        is False
    )

    adverse_tape = {
        **exact_payload,
        "features": {
            **exact_payload["features"],
            "entry_order_flow_status": "adverse",
        },
    }
    assert (
        quality._entry_contract_facts(adverse_tape)["early_session_probe_candidate"]
        is False
    )


def test_completed_structure_phase_relabels_deep_rebound_and_ignores_intrabar_tape():
    base = {
        "current": {"price": 3080, "fluctuation_pct": 5.84},
        "features": {
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "buy_pressure_10t": 91.68,
            "net_aggressive_delta_10t": 2345,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "spread_bp": 81.17,
        },
        "entry_candle_context": {
            "completed_bar_count": 285,
            "structure": {
                "returns_pct": {
                    "1": 0.3257,
                    "3": 0.3257,
                    "5": -0.1621,
                    "10": 1.8182,
                    "20": 2.1559,
                    "60": 4.7619,
                },
                "slopes_pct_per_bar": {
                    "1": 0.3257,
                    "3": 0.1629,
                    "5": -0.129,
                    "10": 0.2153,
                    "20": 0.051,
                    "60": 0.0754,
                },
                "peak_drawdown_pct": -10.4651,
                "high_direction": "up_or_flat",
                "low_direction": "up_or_flat",
                "volume_ratio": 1.592,
                "volume_direction_alignment": "bullish_confirmed",
                "regime": "range",
                "alignment": "neutral",
            },
        },
    }
    adverse_tape = {
        **base,
        "features": {
            **base["features"],
            "entry_order_flow_status": "adverse",
            "buy_pressure_10t": 15.0,
            "net_aggressive_delta_10t": -500,
        },
    }

    supportive = quality.build_exact_payload_analysis_v1(base, stage="entry")
    adverse = quality.build_exact_payload_analysis_v1(adverse_tape, stage="entry")

    assert supportive["completed_structure"]["phase"] == "recovery_continuation"
    assert adverse["completed_structure"]["phase"] == "recovery_continuation"
    assert supportive["completed_structure"]["phase_policy_version"] == (
        "entry_completed_bar_structure_phase_v2"
    )
    assert supportive["completed_structure"]["phase_stable_on_completed_bar"] is True


def test_downtrend_bounce_cannot_be_named_clean_continuation_phase():
    payload = {
        "current": {"price": 10000, "fluctuation_pct": 3.0},
        "features": {},
        "entry_candle_context": {
            "completed_bar_count": 60,
            "structure": {
                "returns_pct": {
                    "1": 0.2,
                    "3": 0.6,
                    "5": 1.0,
                    "10": 1.2,
                    "20": 0.5,
                    "60": 2.0,
                },
                "slopes_pct_per_bar": {
                    "1": 0.2,
                    "3": 0.2,
                    "5": 0.1,
                    "10": 0.05,
                    "20": -0.04,
                    "60": 0.01,
                },
                "peak_drawdown_pct": -0.5,
                "high_direction": "up_or_flat",
                "low_direction": "up_or_flat",
                "volume_ratio": 1.2,
                "volume_direction_alignment": "bullish_confirmed",
                "regime": "downtrend_bounce",
                "alignment": "adverse",
            },
        },
    }

    analysis = quality.build_exact_payload_analysis_v1(payload, stage="entry")

    assert analysis["completed_structure"]["phase"] == "rebound_attempt"


def test_detailed_replay_preserves_exact_payload_and_adds_analysis_ledger():
    exact_payload = {
        "current": {"price": 10000},
        "features": {
            "tick_aggressor_trusted_count": 10,
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "tick_aggressor_pressure_usable": True,
            "net_aggressive_delta_10t": 20,
            "buy_pressure_10t": 80,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "entry_momentum_status": "accelerating",
            "spread_bp": 10,
            "top1_bid_notional": 1000000,
            "top1_ask_notional": 900000,
        },
        "entry_candle_context": {
            "completed_bar_count": 61,
            "structure": {
                "returns_pct": {
                    "1": 0.2,
                    "3": 0.4,
                    "5": 0.8,
                    "10": 1.1,
                    "20": 1.5,
                    "60": 2.0,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.1,
                    "20": 0.1,
                    "60": 0.1,
                },
                "volume_ratio": 1.2,
                "volume_direction_alignment": "price_volume_aligned",
                "regime": "breakout",
                "alignment": "positive",
            },
        },
    }
    payload_hash = quality._sha256(exact_payload)
    base_request = {
        "paired_replay_id": "pair-base",
        "decision_trace_id": "trace-base",
        "stage": "entry",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "payload_sha256": payload_hash,
        "exact_payload": exact_payload,
        "control": {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "captured_action": "WAIT",
        },
        "candidate": {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "response_schema_sha256": "schema-hash",
        },
        "sample_floor": {"pass": True},
        **quality.OFFLINE_CONTRACT,
    }
    requests = quality.prepare_detailed_paired_replay_requests([base_request])
    assert len(requests) == 1
    request = requests[0]
    assert request["paired_replay_id"] == "detailed-pair-base"
    assert request["candidate_input"]["exact_payload"] == exact_payload
    assert request["candidate_exact_payload_sha256"] == payload_hash
    assert request["source_exact_payload_sha256"] == payload_hash
    assert request["exact_payload_analysis"]["schema"] == ("exact_payload_analysis_v1")
    assert request["candidate"]["prompt_version"] == (
        f"{quality.DECISION_QUALITY_DETAILED_PROMPT_VERSION}_entry"
    )
    assert request["runtime_effect"] is False
    wrapped_request = {
        **base_request,
        "exact_payload": {
            "exact_payload": exact_payload,
            "exact_payload_analysis_v1": {"schema": "stale-analysis-must-recompute"},
        },
    }
    v2_8_request = quality.prepare_detailed_paired_replay_requests(
        [wrapped_request],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION
        ),
    )[0]
    assert v2_8_request["candidate_input"]["exact_payload"] == exact_payload
    assert v2_8_request["candidate"]["prompt_version"] == (
        f"{quality.DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION}_entry"
    )
    assert "tape_mixed" in v2_8_request["candidate"]["system_prompt"]
    assert quality.DECISION_QUALITY_DETAILED_PROMPT_VERSION == ("decision_quality_v2_7")
    assert quality.detailed_paired_path(
        "2026-07-30",
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION
        ),
    ).name.endswith("_decision_quality_v2_8.json")
    model_request = quality.prepare_detailed_paired_replay_requests(
        [base_request],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION
        ),
        candidate_model_override="gpt-5-nano",
    )[0]
    assert model_request["candidate"]["model"] == "gpt-5-nano"
    assert model_request["candidate"]["model_comparison"] == {
        "enabled": True,
        "baseline_model": "gpt-5.4-nano",
        "candidate_model": "gpt-5-nano",
        "baseline_reasoning_effort": None,
        "candidate_reasoning_effort": "minimal",
        "reasoning_compatibility_mapping": "none_to_minimal",
        "decision_authority": "offline_model_comparison_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    assert model_request["paired_replay_id"].startswith("detailed-pair-base-model-")
    assert quality.detailed_paired_path(
        "2026-07-30",
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION
        ),
        candidate_model="gpt-5-nano",
    ).name.endswith("_decision_quality_v2_9_1_anticipatory_model_gpt-5-nano.json")
    baseline_result = {
        "status": "pass",
        "decision_trace_id": model_request["decision_trace_id"],
        "payload_sha256": model_request["payload_sha256"],
        "candidate_prompt_sha256": model_request["candidate"]["system_prompt_sha256"],
        "candidate_input_sha256": model_request["candidate_input_sha256"],
        "exact_payload_analysis_sha256": model_request["exact_payload_analysis_sha256"],
        "anticipatory_reversal_analysis_sha256": model_request[
            "anticipatory_reversal_analysis_sha256"
        ],
        "candidate_attempts": [
            {
                "status": "pass",
                "provider_provenance": {"model": "gpt-5.4-nano"},
            }
        ],
    }
    assert (
        quality.validate_model_comparison_baseline(
            [model_request],
            {
                "requests": [
                    {
                        "candidate": {
                            "model": "gpt-5.4-nano",
                            "reasoning_effort": None,
                        }
                    }
                ],
                "results": [baseline_result],
            },
        )
        == []
    )
    assert quality.validate_model_comparison_baseline(
        [model_request],
        {
            "requests": [
                {
                    "candidate": {
                        "model": "gpt-5.4-nano",
                        "reasoning_effort": None,
                    }
                }
            ],
            "results": [{**baseline_result, "payload_sha256": "other"}],
        },
    ) == [f"baseline_payload_sha256_mismatch:{model_request['decision_trace_id']}"]
    response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.5,
        "expected_downside_pct": -0.8,
        "confidence": 75,
        "reason_codes": [
            "edge_positive",
            "tape_supportive",
            "recovery_trigger_confirmed",
            "risk_reward_favorable",
        ],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "low",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    results = quality.run_paired_replay(
        requests,
        control_runner=lambda _: {"action": "WAIT"},
        candidate_runner=lambda _: response,
    )
    assert results[0]["status"] == "pass"
    assert results[0]["same_payload_confirmed"] is True
    assert results[0]["deterministic_analysis_confirmed"] is True
    assert results[0]["exact_payload_analysis_schema"] == ("exact_payload_analysis_v1")
    report = quality.build_paired_replay_report(
        target_date="2026-07-29",
        requests=requests,
        results=results,
        labels=[
            {
                "decision_trace_id": "trace-base",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 1.0,
                        "mfe_pct": 1.2,
                        "mae_pct": -0.2,
                        "first_hit": "target",
                    }
                },
            }
        ],
    )
    assert "exact_payload" not in report["requests"][0]
    assert "candidate_input" not in report["requests"][0]
    assert report["requests"][0]["exact_payload_analysis"]["schema"] == (
        "exact_payload_analysis_v1"
    )

    unsupported = quality.prepare_detailed_paired_replay_requests(
        [{**base_request, "stage": "holding"}]
    )[0]
    assert unsupported["sample_floor"]["pass"] is False
    assert unsupported["sample_floor"]["detailed_analysis_stage_supported"] is False
    assert unsupported["detailed_analysis_exclusion_reason"] == (
        "detailed_analysis_stage_not_implemented"
    )
    assert "candidate_input" not in unsupported


def test_anticipatory_reversal_allows_fresh_wide_spread_offline_probe(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(quality, "DETAILED_PAIRED_REPORT_DIR", tmp_path)
    exact_payload = {
        "current": {"price": 10000, "fluctuation_pct": 3.0},
        "features": {
            "quote_fresh_for_entry": True,
            "quote_stale": False,
            "quote_age_ms": 1000,
            "quote_depth_present": True,
            "tick_context_stale": True,
            "tick_latest_age_ms": 9000,
            "spread_bp": 100,
            "top1_bid_notional": 1000000,
            "top1_ask_notional": 5000000,
            "same_price_buy_absorption": 1,
            "buy_pressure_10t": 58,
            "net_aggressive_delta_10t": 10,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -20,
            "curr_vs_ma5_bp": -10,
            "price_change_10t_pct": 0.2,
            "entry_order_flow_status": "mixed",
        },
        "entry_candle_context": {
            "completed_bar_count": 20,
            "source_quality": {
                "status": "fresh_consistent",
                "decision_window": {
                    "status": "fresh_consistent",
                    "provider_call_allowed": True,
                    "completed_bar_count": 20,
                },
            },
            "structure": {
                "returns_pct": {"1": 0.2, "3": -0.6, "5": -1.0, "10": -2.0},
                "slopes_pct_per_bar": {"5": -0.2, "10": -0.2},
                "peak_drawdown_pct": -2.5,
                "latest_lower_wick_ratio": 0.5,
                "low_rebound_pct": 0.8,
                "high_direction": "down",
                "low_direction": "up_or_flat",
                "volume_ratio": 0.4,
                "volume_direction_alignment": "price_volume_divergence",
                "regime": "range",
                "alignment": "neutral",
            },
        },
    }
    analysis = quality.build_anticipatory_reversal_analysis_v1(
        exact_payload,
        stage="entry",
    )
    assert analysis["source_mode"] == "degraded_but_bounded"
    assert analysis["spread"]["regime"] == "wide_but_observable"
    assert analysis["spread"]["wide_spread_erases_alpha_edge"] is False
    assert analysis["execution_policy"] == "passive_probe_required"
    assert analysis["eligible_for_counterfactual_probe"] is True
    assert analysis["execution_cost"]["conservative_execution_cost_pct"] == 0.57
    assert analysis["learning_contract"]["update_floor_rows"] == 1

    request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                "paired_replay_id": "pair-reversal",
                "decision_trace_id": "trace-reversal",
                "stage": "entry",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "payload_sha256": quality._sha256(exact_payload),
                "exact_payload": exact_payload,
                "control": {"captured_action": "DROP"},
                "candidate": {
                    "provider": "openai",
                    "model": "gpt-5.4-nano",
                    "response_schema_sha256": "schema-hash",
                },
                **quality.OFFLINE_CONTRACT,
                "sample_floor": {
                    "pass": False,
                    "required_decision_rows": 30,
                    "required_unique_symbols": 10,
                },
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION
        ),
    )[0]
    assert request["sample_floor"]["pass"] is True
    assert request["sample_floor"]["promotion_evidence_floor"]["pass"] is False
    assert request["candidate"]["semantic_validator_version"] == (
        quality.ANTICIPATORY_SEMANTIC_VALIDATOR_VERSION
    )
    assert request["candidate"]["exposure_semantics"] == (
        "offline_counterfactual_passive_probe_only"
    )
    assert request["candidate"]["system_prompt"].isascii()

    response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 2.5,
        "expected_downside_pct": -0.8,
        "confidence": 60,
        "reason_codes": [
            "reversal_candidate",
            "recovery_trigger_confirmed",
            "liquidity_adverse",
            "risk_reward_favorable",
        ],
        "evidence": {
            "trend": "mixed",
            "liquidity": "adverse",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    assert quality.validate_replay_candidate_response(request, response) == []
    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _: {"action": "DROP"},
        candidate_runner=lambda _: response,
    )
    assert results[0]["status"] == "pass"
    assert results[0]["supplemental_analysis_confirmed"] is True
    report = quality.build_paired_replay_report(
        target_date="2026-07-30",
        requests=[request],
        results=results,
        labels=[
            {
                "decision_trace_id": "trace-reversal",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 1.0,
                        "mfe_pct": 1.2,
                        "mae_pct": -0.2,
                        "first_hit": "target",
                    }
                },
            }
        ],
    )
    assert report["candidate_source_quality_adjusted_ev_pct"] == 1.0
    assert abs(report["candidate_execution_cost_adjusted_ev_pct"] - 0.43) < 1e-9
    assert report["candidate_primary_decision_metric"] == (
        "probe_intent_and_execution_cost_adjusted_ev_pct"
    )
    assert report["cumulative_learning"]["decision_count"] == 1
    assert report["cumulative_learning"]["learning_update_floor"]["pass"] is True
    assert report["cumulative_learning"]["promotion_evidence_floor"]["pass"] is False

    ineligible_request = {
        **request,
        "anticipatory_reversal_analysis": {
            **request["anticipatory_reversal_analysis"],
            "eligible_for_counterfactual_probe": False,
        },
    }
    assert "anticipatory_buy_without_eligible_precursors" in (
        quality.validate_replay_candidate_response(ineligible_request, response)
    )


def test_v2_10_bounded_opportunity_accepts_high_risk_one_share_probe_and_fair_control():
    exact_payload = {
        "current": {"price": 10000, "fluctuation_pct": 3.0},
        "features": {
            "quote_fresh_for_entry": True,
            "quote_stale": False,
            "quote_age_ms": 1000,
            "quote_depth_present": True,
            "tick_context_stale": True,
            "tick_latest_age_ms": 9000,
            "spread_bp": 100,
            "top1_bid_notional": 1000000,
            "top1_ask_notional": 5000000,
            "same_price_buy_absorption": 1,
            "buy_pressure_10t": 58,
            "net_aggressive_delta_10t": 10,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -20,
            "curr_vs_ma5_bp": -10,
            "price_change_10t_pct": 0.2,
            "entry_order_flow_status": "mixed",
        },
        "entry_candle_context": {
            "completed_bar_count": 20,
            "source_quality": {
                "status": "fresh_consistent",
                "decision_window": {
                    "status": "fresh_consistent",
                    "provider_call_allowed": True,
                    "completed_bar_count": 20,
                },
            },
            "structure": {
                "returns_pct": {"1": 0.2, "3": -0.6, "5": -1.0, "10": -2.0},
                "slopes_pct_per_bar": {"5": -0.2, "10": -0.2},
                "peak_drawdown_pct": -2.5,
                "latest_lower_wick_ratio": 0.5,
                "low_rebound_pct": 0.8,
                "high_direction": "down",
                "low_direction": "up_or_flat",
                "volume_ratio": 0.4,
                "volume_direction_alignment": "price_volume_divergence",
                "regime": "range",
                "alignment": "neutral",
            },
        },
    }
    request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                "paired_replay_id": "pair-v2-10",
                "decision_trace_id": "trace-v2-10",
                "stage": "entry",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "payload_sha256": quality._sha256(exact_payload),
                "exact_payload": exact_payload,
                "control": {
                    "captured_action": "WAIT",
                    "captured_entry_probe_intent": True,
                    "captured_entry_probe_intent_status": "eligible_wait_probe",
                },
                "candidate": {
                    "provider": "openai",
                    "model": "gpt-5.4-nano",
                    "response_schema_sha256": "schema-hash",
                },
                "sample_floor": {"pass": True},
                **quality.OFFLINE_CONTRACT,
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION
        ),
    )[0]
    assert request["candidate"]["semantic_validator_version"] == (
        quality.BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
    )
    assert request["candidate"]["system_prompt"].isascii()
    assert (
        request["anticipatory_reversal_analysis"]["bounded_opportunity"][
            "eligible_for_one_share_probe"
        ]
        is True
    )
    response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.8,
        "expected_downside_pct": -0.6,
        "confidence": 60,
        "reason_codes": [
            "reversal_candidate",
            "recovery_trigger_confirmed",
            "liquidity_adverse",
            "risk_reward_favorable",
        ],
        "evidence": {
            "trend": "mixed",
            "liquidity": "adverse",
            "tape": "mixed",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "high",
            "trigger": "confirmed",
        },
    }
    assert quality.validate_replay_candidate_response(request, response) == []
    high_risk_no_exposure = {
        **response,
        "action": "DROP",
    }
    assert (
        quality.validate_replay_candidate_response(
            request,
            high_risk_no_exposure,
        )
        == []
    )
    below_floor = {**response, "expected_upside_pct": 1.6}
    assert "bounded_opportunity_after_cost_reward_risk_below_floor" in (
        quality.validate_replay_candidate_response(request, below_floor)
    )
    repaired_below_floor, below_floor_repairs = (
        quality.repair_bounded_opportunity_candidate_response(request, below_floor)
    )
    assert repaired_below_floor["action"] == "WAIT"
    assert repaired_below_floor["evidence"]["trigger"] == "recovery_required"
    assert "invalid_probe_buy_waited" in below_floor_repairs
    assert (
        quality.validate_replay_candidate_response(request, repaired_below_floor) == []
    )
    trusted_request = json.loads(json.dumps(request))
    trusted_features = trusted_request["exact_payload"]["features"]
    trusted_features.update(
        {
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
            "buy_pressure_10t": 65,
            "net_aggressive_delta_10t": 20,
            "entry_momentum_status": "accelerating",
            "tick_context_quality": "pass",
            "tick_accel_source": "trusted_aggressor",
            "tick_context_stale": False,
            "tick_latest_age_ms": 1000,
        }
    )
    trusted_structure = trusted_request["exact_payload"]["entry_candle_context"][
        "structure"
    ]
    trusted_structure["returns_pct"] = {
        "1": 0.2,
        "3": 0.3,
        "5": 0.4,
        "10": 0.6,
        "20": 0.8,
        "60": 1.0,
    }
    trusted_structure["slopes_pct_per_bar"] = {
        "5": 0.1,
        "10": 0.1,
        "20": 0.1,
        "60": 0.1,
    }
    trusted_request["anticipatory_reversal_analysis"] = (
        quality.build_anticipatory_reversal_analysis_v1(
            trusted_request["exact_payload"], stage="entry"
        )
    )
    trusted_below_floor = {
        **below_floor,
        "expected_upside_pct": 1.5,
        "evidence": {
            **below_floor["evidence"],
            "setup": "continuation",
            "tape": "supportive",
        },
    }
    repaired_trusted, trusted_repairs = (
        quality.repair_bounded_opportunity_candidate_response(
            trusted_request, trusted_below_floor
        )
    )
    assert repaired_trusted["action"] == "WAIT"
    assert repaired_trusted["evidence"]["trigger"] == "confirmed"
    assert "invalid_probe_buy_waited" in trusted_repairs
    assert (
        quality.validate_replay_candidate_response(trusted_request, repaired_trusted)
        == []
    )
    blocked_request = {
        **request,
        "anticipatory_reversal_analysis": {
            **request["anticipatory_reversal_analysis"],
            "bounded_opportunity": {
                **request["anticipatory_reversal_analysis"]["bounded_opportunity"],
                "eligible_for_one_share_probe": False,
            },
        },
    }
    assert "bounded_opportunity_buy_not_eligible" in (
        quality.validate_replay_candidate_response(blocked_request, response)
    )
    repaired, repairs = quality.repair_bounded_opportunity_candidate_response(
        request,
        {**response, "confidence": 80},
    )
    assert repaired["confidence"] == 60
    assert "degraded_source_confidence_clamped" in repairs
    assert "reason_code_evidence_alignment" in repairs
    assert quality.validate_replay_candidate_response(request, repaired) == []
    unusable_request = {
        **request,
        "anticipatory_reversal_analysis": {
            **request["anticipatory_reversal_analysis"],
            "source_mode": "unusable",
        },
    }
    repaired, repairs = quality.repair_bounded_opportunity_candidate_response(
        unusable_request,
        response,
    )
    assert repaired["edge_state"] == "INSUFFICIENT_DATA"
    assert repaired["action"] == "WAIT"
    assert repairs == ["unusable_source_fail_closed_wait"]
    assert quality.validate_replay_candidate_response(unusable_request, repaired) == []

    structurally_visible_unusable_request = json.loads(json.dumps(trusted_request))
    structurally_visible_unusable_request["anticipatory_reversal_analysis"] = {
        **structurally_visible_unusable_request["anticipatory_reversal_analysis"],
        "source_mode": "unusable",
        "hard_blockers": ["source_unusable"],
    }
    fail_closed, fail_closed_repairs = (
        quality.repair_bounded_opportunity_candidate_response(
            structurally_visible_unusable_request,
            response,
        )
    )
    assert fail_closed_repairs == ["unusable_source_fail_closed_wait"]
    assert (
        quality.validate_replay_candidate_response(
            structurally_visible_unusable_request,
            fail_closed,
        )
        == []
    )

    hard_blocked_request = json.loads(json.dumps(request))
    hard_blocked_request["anticipatory_reversal_analysis"]["hard_blockers"] = [
        "completed_bars_missing"
    ]
    hard_blocked, hard_blocked_repairs = (
        quality.repair_bounded_opportunity_candidate_response(
            hard_blocked_request,
            response,
        )
    )
    assert hard_blocked["action"] == "DROP"
    assert hard_blocked["evidence"]["adverse_risk"] == "blocking"
    assert hard_blocked["evidence"]["trigger"] == "failed"
    assert "deterministic_hard_blocker_drop" in hard_blocked_repairs
    assert (
        quality.validate_replay_candidate_response(
            hard_blocked_request,
            hard_blocked,
        )
        == []
    )

    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _: {
            "action": "WAIT",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
        },
        candidate_runner=lambda _: response,
    )
    report = quality.build_paired_replay_report(
        target_date="2026-07-31",
        requests=[request],
        results=results,
        labels=[
            {
                "decision_trace_id": "trace-v2-10",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 1.0,
                        "mfe_pct": 1.2,
                        "mae_pct": -0.2,
                        "first_hit": "target",
                    }
                },
            }
        ],
    )
    assert report["control_entry_probe_intent_count"] == 1
    assert report["control_primary_decision_ev_pct"] == 0.0
    assert report["candidate_primary_decision_ev_pct"] > 0.0
    assert report["paired_comparisons"][0]["control_probe_armed"] is True
    assert report["paired_comparisons"][0]["control_exposure_selected"] is False
    assert report["candidate_primary_decision_ev_delta_pct"] > 0.0


def test_v2_11_clean_continuation_requires_truthful_guard_delegated_probe():
    exact_payload = {
        "current": {"price": 10000, "fluctuation_pct": 4.0},
        "features": {
            "quote_fresh_for_entry": True,
            "quote_stale": False,
            "quote_age_ms": 900,
            "quote_depth_present": True,
            "tick_context_stale": False,
            "tick_latest_age_ms": 900,
            "spread_bp": 30,
            "top1_bid_notional": 2_000_000,
            "top1_ask_notional": 2_000_000,
            "same_price_buy_absorption": 1,
            "buy_pressure_10t": 56,
            "net_aggressive_delta_10t": 5,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -10,
            "curr_vs_ma5_bp": 5,
            "price_change_10t_pct": 0.1,
            "entry_order_flow_status": "mixed",
            "tick_aggressor_trusted_count": 12,
            "tick_aggressor_pressure_usable": True,
            "tick_context_quality": "pass",
            "tick_accel_source": "trusted_aggressor",
            "tick_acceleration_ratio": 1.1,
        },
        "entry_candle_context": {
            "completed_bar_count": 20,
            "source_quality": {
                "status": "fresh_consistent",
                "decision_window": {
                    "status": "fresh_consistent",
                    "provider_call_allowed": True,
                    "completed_bar_count": 20,
                },
            },
            "structure": {
                "returns_pct": {
                    "1": 0.1,
                    "3": 0.3,
                    "5": 0.6,
                    "10": 0.8,
                    "20": 1.0,
                    "60": 1.2,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.1,
                    "20": 0.1,
                    "60": 0.1,
                },
                "peak_drawdown_pct": -0.1,
                "latest_lower_wick_ratio": 0.5,
                "low_rebound_pct": 0.8,
                "high_direction": "up",
                "low_direction": "up_or_flat",
                "volume_ratio": 1.0,
                "volume_direction_alignment": "aligned",
                "regime": "trend",
                "alignment": "supportive",
            },
        },
    }
    request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                "paired_replay_id": "pair-v2-11",
                "decision_trace_id": "trace-v2-11",
                "stage": "entry",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "payload_sha256": quality._sha256(exact_payload),
                "exact_payload": exact_payload,
                "control": {"captured_action": "WAIT"},
                "candidate": {
                    "provider": "openai",
                    "model": "gpt-5.4-nano",
                    "response_schema_sha256": "schema-hash",
                },
                "sample_floor": {"pass": True},
                **quality.OFFLINE_CONTRACT,
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION
        ),
    )[0]
    clean_contract = request["anticipatory_reversal_analysis"][
        "clean_continuation_probe"
    ]
    assert clean_contract["eligible"] is True
    assert clean_contract["after_cost_reward_risk_floor"] == 0.75
    assert request["candidate"]["system_prompt"].isascii()

    wait_response = {
        "edge_state": "EDGE",
        "action": "WAIT",
        "expected_upside_pct": 0.9,
        "expected_downside_pct": -0.8,
        "confidence": 55,
        "reason_codes": ["edge_positive", "recovery_trigger_required"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "recovery_required",
        },
    }
    assert quality.validate_replay_candidate_response(request, wait_response) == []

    buy_response = {
        **wait_response,
        "action": "BUY",
        "reason_codes": [
            "edge_positive",
            "recovery_trigger_confirmed",
            "risk_reward_favorable",
        ],
        "evidence": {
            **wait_response["evidence"],
            "trigger": "confirmed",
        },
    }
    assert quality.validate_replay_candidate_response(request, buy_response) == []

    blocked_payload = json.loads(json.dumps(exact_payload))
    blocked_payload["features"]["large_sell_print_detected"] = True
    blocked_analysis = quality.build_anticipatory_reversal_analysis_v1(
        blocked_payload,
        stage="entry",
    )
    assert blocked_analysis["clean_continuation_probe"]["eligible"] is False
    assert "large_sell_print_present" in blocked_analysis["hard_blockers"]

    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _: {"action": "WAIT"},
        candidate_runner=lambda _: buy_response,
    )
    report = quality.build_paired_replay_report(
        target_date="2026-07-31",
        requests=[request],
        results=results,
        labels=[
            {
                "decision_trace_id": "trace-v2-11",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 0.8,
                        "mfe_pct": 1.1,
                        "mae_pct": -0.2,
                        "first_hit": "target",
                    }
                },
            }
        ],
    )
    summary = report["clean_continuation_probe_summary"]
    assert summary["eligible_decision_count"] == 1
    assert summary["candidate_exposure_decision_count"] == 1
    assert summary["candidate_not_exposed_decision_count"] == 0
    assert summary["candidate_exposure_coverage_pct"] == 100.0
    assert abs(summary["eligible_cohort_after_cost_ev_pct"] - 0.65) < 1e-9
    assert summary["runtime_effect"] is False


def test_v2_12_selective_recovery_restricts_generic_bounded_probe_buy():
    exact_payload = {
        "current": {"price": 10000, "fluctuation_pct": 4.0},
        "features": {
            "quote_fresh_for_entry": True,
            "quote_stale": False,
            "quote_age_ms": 500,
            "quote_depth_present": True,
            "tick_context_stale": False,
            "tick_latest_age_ms": 500,
            "spread_bp": 40,
            "top1_bid_notional": 2_000_000,
            "top1_ask_notional": 2_000_000,
            "same_price_buy_absorption": 1,
            "buy_pressure_10t": 70,
            "net_aggressive_delta_10t": 50,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -10,
            "curr_vs_ma5_bp": 5,
            "price_change_10t_pct": 0.2,
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "tick_aggressor_trusted_count": 12,
            "tick_aggressor_pressure_usable": True,
            "tick_context_quality": "pass",
            "tick_accel_source": "trusted_aggressor",
            "tick_acceleration_ratio": 1.6,
        },
        "entry_candle_context": {
            "completed_bar_count": 20,
            "source_quality": {
                "status": "fresh_consistent",
                "decision_window": {
                    "status": "fresh_consistent",
                    "provider_call_allowed": True,
                    "completed_bar_count": 20,
                },
            },
            "structure": {
                "returns_pct": {
                    "1": 0.6,
                    "3": 0.3,
                    "5": -0.1,
                    "10": 1.2,
                    "20": 1.4,
                    "60": 1.6,
                },
                "slopes_pct_per_bar": {
                    "5": 0.05,
                    "10": 0.1,
                    "20": 0.1,
                    "60": 0.05,
                },
                "peak_drawdown_pct": -1.2,
                "latest_lower_wick_ratio": 0.5,
                "low_rebound_pct": 0.8,
                "high_direction": "up",
                "low_direction": "up_or_flat",
                "volume_ratio": 1.0,
                "volume_direction_alignment": "aligned",
                "regime": "trend",
                "alignment": "supportive",
            },
        },
    }
    base_request = {
        "paired_replay_id": "pair-v2-12",
        "decision_trace_id": "trace-v2-12",
        "stage": "entry",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": quality._sha256(exact_payload),
        "exact_payload": exact_payload,
        "control": {"captured_action": "WAIT"},
        "candidate": {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "response_schema_sha256": "schema-hash",
        },
        "sample_floor": {"pass": True},
        **quality.OFFLINE_CONTRACT,
    }
    v2_11_request = quality.prepare_detailed_paired_replay_requests(
        [base_request],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION
        ),
    )[0]
    assert (
        "selective_recovery_probe"
        not in v2_11_request["anticipatory_reversal_analysis"]
    )
    request = quality.prepare_detailed_paired_replay_requests(
        [base_request],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION
        ),
    )[0]
    analysis = request["anticipatory_reversal_analysis"]
    assert analysis["clean_continuation_probe"]["eligible"] is False
    assert analysis["selective_recovery_probe"]["eligible"] is True
    assert request["candidate"]["system_prompt"].isascii()

    buy_response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.2,
        "expected_downside_pct": -0.7,
        "confidence": 60,
        "reason_codes": [
            "edge_positive",
            "recovery_trigger_confirmed",
            "risk_reward_favorable",
        ],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    assert quality.validate_replay_candidate_response(request, buy_response) == []

    no_reclaim_payload = json.loads(json.dumps(exact_payload))
    no_reclaim_payload["features"].update(
        {
            "curr_vs_micro_vwap_bp": -100,
            "curr_vs_ma5_bp": -100,
            "price_change_10t_pct": -0.1,
        }
    )
    blocked_request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                **base_request,
                "paired_replay_id": "pair-v2-12-no-reclaim",
                "decision_trace_id": "trace-v2-12-no-reclaim",
                "payload_sha256": quality._sha256(no_reclaim_payload),
                "exact_payload": no_reclaim_payload,
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION
        ),
    )[0]
    assert (
        blocked_request["anticipatory_reversal_analysis"]["selective_recovery_probe"][
            "eligible"
        ]
        is False
    )
    assert "selective_recovery_buy_not_eligible" in (
        quality.validate_replay_candidate_response(blocked_request, buy_response)
    )

    v2_13_request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                **base_request,
                "paired_replay_id": "pair-v2-13",
                "decision_trace_id": "trace-v2-13",
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
    )[0]
    v2_13_analysis = v2_13_request["anticipatory_reversal_analysis"]
    assert v2_13_analysis["selective_recovery_probe"]["eligible"] is True
    assert v2_13_analysis["recovery_confirmation_probe"]["eligible"] is True
    assert v2_13_request["candidate"]["system_prompt"].isascii()
    assert (
        "V2.12 selective-recovery one-share probe experiment:"
        not in v2_13_request["candidate"]["system_prompt"]
    )
    assert (
        quality.validate_replay_candidate_response(
            v2_13_request,
            buy_response,
        )
        == []
    )

    unconfirmed_payload = json.loads(json.dumps(exact_payload))
    unconfirmed_payload["features"].update(
        {
            "entry_order_flow_status": "mixed",
            "tick_acceleration_ratio": 0.5,
            "net_aggressive_delta_10t": -10,
        }
    )
    unconfirmed_request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                **base_request,
                "paired_replay_id": "pair-v2-13-unconfirmed",
                "decision_trace_id": "trace-v2-13-unconfirmed",
                "payload_sha256": quality._sha256(unconfirmed_payload),
                "exact_payload": unconfirmed_payload,
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
    )[0]
    assert (
        unconfirmed_request["anticipatory_reversal_analysis"][
            "selective_recovery_probe"
        ]["eligible"]
        is True
    )
    assert (
        unconfirmed_request["anticipatory_reversal_analysis"][
            "recovery_confirmation_probe"
        ]["eligible"]
        is False
    )
    assert "recovery_confirmation_buy_not_eligible" in (
        quality.validate_replay_candidate_response(
            unconfirmed_request,
            buy_response,
        )
    )


def test_v2_9_1_semantic_repair_aligns_trigger_reason_without_promoting_buy():
    request = {
        "stage": "entry",
        "exact_payload": {},
        "candidate": {
            "semantic_repair_version": quality.ANTICIPATORY_SEMANTIC_REPAIR_VERSION,
        },
    }
    response = {
        "edge_state": "EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.8,
        "expected_downside_pct": -1.0,
        "confidence": 60,
        "reason_codes": [
            "edge_positive",
            "recovery_trigger_required",
            "risk_reward_unfavorable",
        ],
        "evidence": {
            "trend": "mixed",
            "liquidity": "adverse",
            "tape": "adverse",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "pullback_recovery",
            "positive_edge": "moderate",
            "adverse_risk": "blocking",
            "trigger": "failed",
        },
    }

    repaired, repairs = quality.repair_anticipatory_candidate_response(
        request, response
    )

    assert repaired["action"] == "DROP"
    assert repaired["evidence"]["trigger"] == "failed"
    assert "recovery_trigger_failed" in repaired["reason_codes"]
    assert "recovery_trigger_required" not in repaired["reason_codes"]
    assert "reason_code_evidence_alignment" in repairs
    assert (
        quality.validate_candidate_response(repaired, stage="entry", exact_payload={})
        == []
    )


def test_v2_9_1_semantic_repair_completes_adverse_distribution_reasons():
    exact_payload = {
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "5": -0.6,
                    "10": -1.2,
                    "20": -1.8,
                    "60": -2.4,
                },
                "slopes_pct_per_bar": {
                    "5": -0.1,
                    "10": -0.1,
                    "20": -0.1,
                    "60": -0.1,
                },
                "peak_drawdown_pct": -2.5,
                "high_direction": "down",
                "volume_ratio": 0.4,
            }
        }
    }
    request = {
        "stage": "entry",
        "exact_payload": exact_payload,
        "candidate": {
            "semantic_repair_version": quality.ANTICIPATORY_SEMANTIC_REPAIR_VERSION,
        },
    }
    response = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.0,
        "expected_downside_pct": -1.2,
        "confidence": 84,
        "reason_codes": [
            "edge_absent",
            "distribution_adverse",
            "liquidity_adverse",
        ],
        "evidence": {
            "trend": "adverse",
            "liquidity": "adverse",
            "tape": "mixed",
            "risk": "high",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "blocking",
            "trigger": "failed",
        },
    }

    repaired, repairs = quality.repair_anticipatory_candidate_response(
        request, response
    )

    assert repaired["action"] == "DROP"
    assert "distribution_adverse" in repaired["reason_codes"]
    assert "volume_confirmation_missing" in repaired["reason_codes"]
    assert "reason_code_evidence_alignment" in repairs
    assert (
        quality.validate_candidate_response(
            repaired,
            stage="entry",
            exact_payload=exact_payload,
        )
        == []
    )


def test_v2_13_repair_closes_non_buy_enum_sign_and_evidence_aliases():
    analysis = {
        "schema": quality.ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA,
        "stage": "entry",
        "source_mode": "fresh_dual",
        "spread": {"regime": "wide_but_observable"},
        "execution_cost": {"conservative_execution_cost_pct": 0.2},
        "precursors": {},
        "hard_blockers": [],
        "bounded_opportunity": {
            "eligible_for_one_share_probe": False,
            "execution_policy": "no_counterfactual_exposure",
            "qualifying_edge_facts": {},
        },
        "clean_continuation_probe": {"eligible": False},
        "selective_recovery_probe": {"eligible": False},
        "recovery_confirmation_probe": {"eligible": False},
    }
    response = {
        "edge_state": "EDGE",
        "action": "WAIT (RECOVERY_REQUIRED)",
        "expected_upside_pct": 1.0,
        "expected_downside_pct": 0.8,
        "confidence": 58,
        "reason_codes": ["edge_positive", "recovery_trigger_required"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "neutral",
            "risk": "blocking",
            "uncertainty": "medium",
            "setup": "pullback_recovery",
            "positive_edge": "moderate",
            "adverse_risk": "medium",
            "trigger": "recovery_required",
        },
    }

    repaired, repair_codes, errors = (
        quality.repair_v2_13_recovery_confirmation_response(
            exact_payload={},
            analysis=analysis,
            response=response,
        )
    )

    assert errors == []
    assert repaired["action"] == "WAIT"
    assert repaired["expected_downside_pct"] == -0.8
    assert repaired["evidence"]["risk"] == "high"
    assert repaired["evidence"]["tape"] == "mixed"
    assert repaired["evidence"]["adverse_risk"] == "moderate"
    assert repaired["evidence"]["liquidity"] == "adverse"
    assert "non_buy_action_enum_normalized" in repair_codes
    assert "non_buy_downside_sign_normalized" in repair_codes
    assert "wide_spread_liquidity_aligned" in repair_codes


def test_three_way_comparison_uses_only_common_comparable_rows():
    one_pass = {
        "requests": [{"candidate": {"prompt_version": "decision_quality_v2_6_entry"}}],
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-1",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "krx_regular",
                "control_action": "WAIT",
                "candidate_action": "DROP",
                "outcome_return_pct": 1.0,
                "control_decision_value_pct": 0.0,
                "candidate_decision_value_pct": 0.0,
                "candidate_error_taxonomy": ["false_drop"],
            }
        ],
    }
    detailed = {
        "requests": [{"candidate": {"prompt_version": "decision_quality_v2_7_entry"}}],
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-1",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "krx_regular",
                "control_action": "WAIT",
                "candidate_action": "BUY",
                "outcome_return_pct": 1.0,
                "control_decision_value_pct": 0.0,
                "candidate_decision_value_pct": 1.0,
                "candidate_error_taxonomy": [],
            },
            {
                "decision_trace_id": "trace-detailed-only",
                "candidate_decision_value_pct": 1.0,
            },
            {
                "decision_trace_id": "trace-missing-value",
                "candidate_decision_value_pct": None,
            },
        ],
    }
    one_pass["paired_comparisons"].append(
        {
            "decision_trace_id": "trace-missing-value",
            "candidate_decision_value_pct": 1.0,
        }
    )
    comparison = quality.build_detailed_three_way_comparison(
        one_pass_report=one_pass,
        detailed_report=detailed,
    )
    assert comparison["common_comparable_count"] == 1
    assert comparison["common_cohort_sha256"] == quality._sha256(["trace-1"])
    assert comparison["detailed_vs_one_pass_ev_delta_pct"] == 1.0
    assert comparison["action_transition_counts"] == {"DROP->BUY": 1}
    assert comparison["one_pass_error_taxonomy_counts"] == {"false_drop": 1}
    assert comparison["detailed_error_taxonomy_counts"] == {}
    assert comparison["runtime_effect"] is False


def test_model_replay_comparison_keeps_exact_cohort_and_reports_model_delta():
    baseline = {
        "status": "paired_replay_complete_candidate_quality_rejected",
        "result_count": 2,
        "candidate_source_quality_adjusted_ev_pct": 0.1,
        "candidate_primary_decision_ev_pct": 0.08,
        "candidate_action_counts": {"DROP": 1, "WAIT": 1},
        "candidate_error_taxonomy_counts": {"false_drop": 1},
        "candidate_quality_gate_pass": False,
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-1",
                "candidate_decision_value_pct": 0.1,
                "candidate_primary_decision_value_pct": 0.08,
                "candidate_error_taxonomy": ["false_drop"],
            },
            {
                "decision_trace_id": "trace-2",
                "candidate_decision_value_pct": 0.1,
                "candidate_primary_decision_value_pct": 0.08,
                "candidate_error_taxonomy": [],
            },
        ],
        "results": [
            {
                "status": "pass",
                "decision_trace_id": "trace-1",
                "payload_sha256": "payload-1",
                "candidate_prompt_sha256": "prompt",
                "candidate_input_sha256": "input-1",
                "candidate_response": {"action": "DROP"},
                "candidate_attempts": [
                    {
                        "status": "pass",
                        "provider_provenance": {
                            "provider": "openai",
                            "model": "gpt-5.4-nano",
                            "latency_ms": 100,
                            "input_tokens": 10,
                            "output_tokens": 2,
                            "total_tokens": 12,
                            "provider_none": False,
                        },
                    }
                ],
            },
            {
                "status": "pass",
                "decision_trace_id": "trace-2",
                "payload_sha256": "payload-2",
                "candidate_prompt_sha256": "prompt",
                "candidate_input_sha256": "input-2",
                "candidate_response": {"action": "WAIT"},
                "candidate_attempts": [],
            },
        ],
    }
    candidate = {
        **baseline,
        "candidate_source_quality_adjusted_ev_pct": 0.3,
        "candidate_primary_decision_ev_pct": 0.25,
        "candidate_action_counts": {"WAIT": 2},
        "candidate_error_taxonomy_counts": {},
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-1",
                "candidate_decision_value_pct": 0.3,
                "candidate_primary_decision_value_pct": 0.25,
                "candidate_error_taxonomy": [],
            },
            {
                "decision_trace_id": "trace-2",
                "candidate_decision_value_pct": 0.3,
                "candidate_primary_decision_value_pct": 0.25,
                "candidate_error_taxonomy": [],
            },
        ],
        "results": [
            {
                **baseline["results"][0],
                "candidate_response": {"action": "WAIT"},
                "candidate_attempts": [
                    {
                        "status": "pass",
                        "provider_provenance": {
                            "provider": "openai",
                            "model": "gpt-5-nano",
                            "latency_ms": 80,
                            "input_tokens": 10,
                            "output_tokens": 2,
                            "total_tokens": 12,
                            "provider_none": False,
                        },
                    }
                ],
            },
            {
                **baseline["results"][1],
                "candidate_response": {"action": "WAIT"},
            },
        ],
    }

    comparison = quality.build_model_replay_comparison(
        baseline_report=baseline,
        candidate_report=candidate,
        baseline_model="gpt-5.4-nano",
        candidate_model="gpt-5-nano",
    )

    assert comparison["common_pass_count"] == 2
    assert comparison["payload_hash_mismatch_count"] == 0
    assert comparison["prompt_hash_mismatch_count"] == 0
    assert comparison["candidate_input_hash_mismatch_count"] == 0
    assert comparison["action_agreement_count"] == 1
    assert comparison["action_transition_counts"] == {
        "DROP->WAIT": 1,
        "WAIT->WAIT": 1,
    }
    assert (
        comparison["candidate_vs_baseline_common_source_quality_adjusted_ev_delta_pct"]
        == 0.19999999999999998
    )
    assert comparison["common_comparable_count"] == 2
    assert comparison["baseline_common_error_taxonomy_counts"] == {"false_drop": 1}
    assert comparison["full_eligible_cohort_count"] == 2
    assert comparison["candidate_fail_closed_nonpass_value_policy"] == (
        "zero_no_exposure"
    )
    assert (
        comparison[
            "candidate_vs_baseline_fail_closed_full_eligible_primary_decision_ev_delta_pct"
        ]
        == 0.16999999999999998
    )
    assert comparison["baseline_pass_rate_pct"] == 100.0
    assert comparison["candidate_pass_rate_pct"] == 100.0
    assert comparison["candidate_attempt_stats"]["provider_models"] == ["gpt-5-nano"]
    assert comparison["candidate_attempt_stats"]["openai_api_attempt_count"] == 1
    assert comparison["runtime_effect"] is False


def test_model_replay_comparison_keeps_nonpass_rows_as_zero_exposure():
    baseline = {
        "status": "baseline",
        "result_count": 2,
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-pass",
                "candidate_decision_value_pct": 0.2,
                "candidate_primary_decision_value_pct": 0.1,
            },
            {
                "decision_trace_id": "trace-rejected",
                "candidate_decision_value_pct": 0.4,
                "candidate_primary_decision_value_pct": 0.3,
            },
        ],
        "results": [
            {
                "status": "pass",
                "decision_trace_id": "trace-pass",
                "candidate_response": {"action": "WAIT"},
            },
            {
                "status": "pass",
                "decision_trace_id": "trace-rejected",
                "candidate_response": {"action": "BUY"},
            },
        ],
    }
    candidate = {
        "status": "candidate",
        "result_count": 2,
        "paired_comparisons": [
            {
                "decision_trace_id": "trace-pass",
                "candidate_decision_value_pct": 0.2,
                "candidate_primary_decision_value_pct": 0.1,
            }
        ],
        "results": [
            {
                "status": "pass",
                "decision_trace_id": "trace-pass",
                "candidate_response": {"action": "WAIT"},
            },
            {
                "status": "schema_rejected",
                "decision_trace_id": "trace-rejected",
            },
        ],
    }

    comparison = quality.build_model_replay_comparison(
        baseline_report=baseline,
        candidate_report=candidate,
        baseline_model="gpt-5.4-nano",
        candidate_model="gpt-5-nano",
    )

    assert comparison["common_pass_count"] == 1
    assert comparison["candidate_nonpass_count"] == 1
    assert comparison["candidate_pass_rate_pct"] == 50.0
    assert comparison["full_eligible_cohort_count"] == 2
    assert comparison["full_eligible_primary_metric_missing_count"] == 0
    assert comparison["baseline_full_eligible_primary_decision_ev_pct"] == 0.2
    assert (
        comparison["candidate_fail_closed_full_eligible_primary_decision_ev_pct"]
        == 0.05
    )
    assert (
        comparison[
            "candidate_vs_baseline_fail_closed_full_eligible_primary_decision_ev_delta_pct"
        ]
        == -0.15000000000000002
    )


def test_paired_replay_uses_same_exact_payload_and_has_no_runtime_authority():
    control_manifest = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace()],
        payloads=[_payload()],
    )
    labels = [
        {
            **_pending(),
            "label_status": "mature",
            "source_quality_status": "pass",
            "primary_cohort_eligible": True,
            "horizon_metrics": {
                "10m": {
                    "end_return_pct": 2.0,
                    "mfe_pct": 2.2,
                    "mae_pct": -0.7,
                    "first_hit": "target",
                    "profit_opportunity_threshold_pct": 1.0,
                    "profit_opportunity_observed": True,
                    "profit_opportunity_sequence": "drawdown_then_profit_recovery",
                    "pre_profit_mae_pct": -0.7,
                }
            },
        }
    ]
    requests = quality.prepare_paired_replay_requests(
        control_manifest=control_manifest,
        traces=[_trace()],
        payloads=[_payload()],
        labels=labels,
    )
    assert len(requests) == 1
    assert requests[0]["payload_sha256"] == "payload-1"
    assert requests[0]["runtime_effect"] is False
    assert requests[0]["candidate"]["prompt_version"] == (
        f"{quality.DECISION_QUALITY_V2_PROMPT_VERSION}_entry"
    )
    assert requests[0]["candidate"]["contract_sha256"]
    response = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.3,
        "expected_downside_pct": -0.4,
        "confidence": 60,
        "reason_codes": ["no_positive_edge"],
        "evidence": {
            "trend": "mixed",
            "liquidity": "supportive",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "moderate",
            "trigger": "not_applicable",
        },
    }
    results = quality.run_paired_replay(
        requests,
        control_runner=lambda request: {"action": "DROP"},
        candidate_runner=lambda request: response,
    )
    assert results[0]["same_payload_confirmed"] is True
    assert results[0]["status"] == "pass"
    assert results[0]["candidate_contract_sha256"] == (
        requests[0]["candidate"]["contract_sha256"]
    )
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=requests,
        results=results,
        labels=labels,
    )
    assert report["control_source_quality_adjusted_ev_pct"] == 0
    assert report["candidate_source_quality_adjusted_ev_pct"] == 0
    assert report["paired_comparable_count"] == 1
    assert report["candidate_drop_outcome_trajectory"] == {
        "result_drop_count": 1,
        "comparable_drop_count": 1,
        "outcome_unavailable_drop_count": 0,
        "profit_opportunity_threshold_pct": 1.0,
        "profit_opportunity_count": 1,
        "drawdown_then_profit_recovery_count": 1,
        "direct_profit_count": 0,
        "same_bar_sequence_ambiguous_count": 0,
        "positive_excursion_below_profit_count": 0,
        "no_positive_excursion_count": 0,
        "profit_sequence_counts": {"drawdown_then_profit_recovery": 1},
        "pre_profit_mae_buckets": {
            "nonnegative": 0,
            "minus_0_to_0_5": 0,
            "minus_0_5_to_1": 1,
            "minus_1_to_2": 0,
            "below_minus_2": 0,
            "not_recorded": 0,
        },
        "interpretation": (
            "DROP is not equivalent to a monotonic decline. Profit opportunity "
            "and drawdown-before-profit are evaluated separately."
        ),
    }
    assert report["candidate_error_taxonomy_counts"] == {
        "false_drop": 1,
        "false_drop_drawdown_recovery": 1,
    }
    assert report["candidate_exposure_decision_count"] == 0
    assert report["candidate_exposure_sample_floor"]["pass"] is False
    assert report["status"] == "paired_replay_complete_hold_sample_offline_only"
    assert report["candidate_quality_gate_pass"] is False
    bucket = report["buckets"][0]
    assert bucket["stage"] == "entry"
    assert bucket["effective_venue"] == "KRX"
    assert bucket["candidate_probe_cost_adjusted_ev_pct"] is None
    assert bucket["candidate_probe_loss_budget_breach_count"] == 0
    assert bucket["control_drawdown_recovery_capture_count"] == 0
    assert bucket["candidate_drawdown_recovery_capture_count"] == 0
    assert (
        bucket["candidate_quality_checks"]["candidate_probe_bounded_risk_budget_pass"]
        is False
    )
    assert bucket["diagnostic_checks_not_quality_veto"] == {
        "adverse_first_exposure_not_increased": True,
        "tight_stop_adverse_first_exposure_not_increased": True,
        "severe_tail_adverse_not_increased": True,
        "candidate_action_not_collapsed": False,
    }
    assert bucket["candidate_quality_gate_pass"] is False


def _micro_reversion_materialization_fixture():
    control_prompt = "Current exact control prompt. Return the contracted JSON."
    control_prompt_sha256 = quality._stored_prompt_sha256(control_prompt)
    live_response_schema = quality.build_openai_response_text_format(
        "decision_quality_v2_7_entry"
    )["schema"]
    captured_at = "2026-08-14T09:00:16.000+09:00"
    exact_payload = {
        "schema": "entry_payload_v1",
        "requested_qty": 5,
        "position_sizing_allocator": {"effective_qty": 5},
        "entry_candle_context": {
            "schema": quality.ENTRY_CONTEXT_SCHEMA,
            "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "bars": [{"minute": "09:00", "forming": False}],
        },
        "ai_market_snapshot": {
            "schema": "ai_market_snapshot_v1",
            "snapshot_id": "snapshot-materialize-1",
            "captured_at": captured_at,
            "stock_code": "000001",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "market_data_route": "krx_only",
            "broker_route": "KRX",
        },
    }
    replay_context = {
        "input_schema": "decision_quality_v2_entry",
        "exact_payload": exact_payload,
        "exact_payload_analysis_v1": {"schema": "exact_payload_analysis_v1"},
    }
    replay_context_sha256 = quality._sha256(replay_context)
    payload_sha256 = "provider-payload-materialize-1"
    request_envelope_sha256 = quality._sha256(
        {
            "endpoint": "analyze_target",
            "model": "gpt-test",
            "schema_name": "decision_quality_v2_7_entry",
            "require_json": True,
            "temperature": None,
            "max_output_tokens": 900,
            "reasoning_effort": "medium",
            "prompt_sha256": control_prompt_sha256,
            "user_input_sha256": payload_sha256,
            "replay_context_sha256": replay_context_sha256,
        }
    )
    trace = {
        "schema": "ai_decision_trace_v1",
        "decision_trace_id": "trace-materialize-1",
        "request_id": "request-materialize-1",
        "decision_ts": "2026-08-14T09:00:17.000+09:00",
        "decision_stage": "entry",
        "endpoint": "analyze_target",
        "stock_code": "000001",
        "instrument_type": "COMMON_STOCK",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "market_data_route": "krx_only",
        "broker_route": "KRX",
        "payload_replay_exact": True,
        "request_capture_status": "captured",
        "payload_sha256": payload_sha256,
        "request_envelope_sha256": request_envelope_sha256,
        "prompt_version": "current_control_v1",
        "prompt_sha256": control_prompt_sha256,
        "provider_actual": "openai",
        "provider_called": True,
        "model": "gpt-test",
        "model_requested": "gpt-test",
        "request_temperature": None,
        "request_reasoning_effort": "medium",
        "transport": "responses_http",
        "openai_response_schema_mode": "strict_dynamic_entry",
        "openai_response_schema_registry_used": True,
        "response_schema_sha256": quality._sha256(live_response_schema),
        "response_schema_application": "provider_enforced_openai",
        "semantic_validator_version": (
            quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
        ),
        "expected_semantic_validator_version": (
            quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
        ),
        "semantic_validator_applied": True,
        "semantic_validation_status": "pass",
        "result_source": "live",
        "replay_context_present": True,
        "replay_context_exact": True,
        "replay_context_sha256": replay_context_sha256,
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "canonical_context_capture_status": "exact_completed_bars_captured",
        "snapshot_id": "snapshot-materialize-1",
        "action": "WAIT",
    }
    payload = {
        "schema": "ai_decision_payload_v1",
        "request_id": "request-materialize-1",
        "payload_sha256": payload_sha256,
        "request_envelope_sha256": request_envelope_sha256,
        "endpoint": "analyze_target",
        "model": "gpt-test",
        "schema_name": "decision_quality_v2_7_entry",
        "require_json": True,
        "temperature": None,
        "max_output_tokens": 900,
        "reasoning_effort": "medium",
        "prompt_sha256": control_prompt_sha256,
        "replay_exact": True,
        "replay_context_present": True,
        "replay_context_exact": True,
        "replay_context_sha256": replay_context_sha256,
        "replay_context_input_format": "structured",
        "symbol": "000001",
        "instrument_type": "COMMON_STOCK",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "market_data_route": "krx_only",
        "broker_route": "KRX",
        "snapshot_id": "snapshot-materialize-1",
        "canonical_context_capture": {
            "status": "exact_completed_bars_captured",
            "schema": quality.ENTRY_CONTEXT_SCHEMA,
            "input_bundle_version": quality.INPUT_BUNDLE_VERSION,
            "raw_bar_count": 1,
            "completed_bar_count": 1,
        },
        "sanitized_replay_context": replay_context,
    }
    label = {
        **_pending(action="WAIT"),
        "decision_trace_id": "trace-materialize-1",
        "label_id": "trace-materialize-1:v1",
        "stock_code": "000001",
        "decision_ts": trace["decision_ts"],
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 1.0,
                "probe_cost_adjusted_ev_pct": 0.7,
                "mfe_pct": 1.2,
                "mae_pct": -0.3,
                "first_hit": "target",
                "target_first_delay_sec": 120,
                "position_horizon_sec": 300,
            }
        },
    }
    control_manifest = {
        "status": "control_manifest_frozen_collect_exact_samples",
        "controls": [
            {
                "endpoint": "analyze_target",
                "prompt_version": trace["prompt_version"],
                "prompt_sha256": trace["prompt_sha256"],
                "provider_actual": trace["provider_actual"],
                "model": trace["model"],
                "request_temperature": trace["request_temperature"],
                "request_reasoning_effort": trace["request_reasoning_effort"],
            }
        ],
    }
    prepared = quality.prepare_paired_replay_requests(
        control_manifest=control_manifest,
        traces=[trace],
        payloads=[payload],
        labels=[label],
    )
    assert len(prepared) == 1
    prompt_rows = [
        {
            "schema": "ai_decision_prompt_v1",
            "prompt_sha256": control_prompt_sha256,
            "endpoint": "analyze_target",
            "model": "gpt-test",
            "schema_name": "decision_quality_v2_7_entry",
            "redacted": False,
            "replay_exact": True,
            "sanitized_prompt": control_prompt,
        }
    ]
    control_contract_artifact = quality.build_micro_reversion_control_contract_artifact(
        target_date="2026-08-14",
        prepared_requests=prepared,
        traces=[trace],
        payloads=[payload],
        prompt_rows=prompt_rows,
    )
    assert control_contract_artifact["control_contract_count"] == 1

    def market(timestamp, *, price, side, qty, sequence, bid=None, ask=None):
        return {
            "schema": "scalp_micro_reversion_market_stream_point_v3",
            "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v3",
            "realtime_type": "0B",
            "item": "000001",
            "symbol": "000001",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sequence_epoch": 123,
            "source_sequence": sequence,
            "series_sequence": sequence,
            "exchange_timestamp": timestamp,
            "local_receive_timestamp": timestamp,
            "trade_price": price,
            "trade_qty": qty,
            "best_bid": bid if bid is not None else price - 10,
            "best_ask": ask if ask is not None else price,
            "quote_age_ms": 0.0,
            "aggressor_side": side,
            "path_order_status": "accept",
            "path_consumer_eligible": True,
            "exchange_timestamp_regression_ms": 0,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "trading_runtime_effect": False,
        }

    market_rows = [
        market(
            "2026-08-14T09:00:05.000+09:00",
            price=10_000,
            side="BUY",
            qty=20,
            sequence=1,
        ),
        market(
            "2026-08-14T09:00:06.000+09:00",
            price=9_900,
            side="SELL",
            qty=100,
            sequence=2,
        ),
        market(
            "2026-08-14T09:00:07.000+09:00",
            price=9_880,
            side="SELL",
            qty=100,
            sequence=3,
        ),
        market(
            "2026-08-14T09:00:09.800+09:00",
            price=9_960,
            side="BUY",
            qty=400,
            sequence=4,
            bid=9_950,
            ask=9_960,
        ),
        market(
            "2026-08-14T09:00:11.000+09:00",
            price=9_970,
            side="BUY",
            qty=100,
            sequence=5,
            bid=9_960,
            ask=9_970,
        ),
        market(
            "2026-08-14T09:00:16.000+09:00",
            price=9_980,
            side="BUY",
            qty=100,
            sequence=6,
            bid=9_970,
            ask=9_980,
        ),
    ]

    def depth(
        timestamp,
        *,
        sequence,
        quantities,
        best_bid=9_950,
        best_ask=9_960,
    ):
        ask_depth = sum(quantities)
        return {
            "schema": "scalp_micro_reversion_market_depth_point_v1",
            "metric_contract_id": "scalp_micro_reversion_market_depth_contract_v1",
            "realtime_type": "0D",
            "item": "000001",
            "symbol": "000001",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sequence_epoch": 123,
            "source_sequence": sequence,
            "series_sequence": sequence,
            "exchange_timestamp": timestamp,
            "local_receive_timestamp": timestamp,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "best_bid_qty": 100,
            "best_ask_qty": quantities[0],
            "bid_depth": 1_000,
            "ask_depth": ask_depth,
            "route_depth_totals": {
                "KRX": {"bid": 1_000, "ask": ask_depth},
                "NXT": {"bid": 0, "ask": 0},
                "combined": {"bid": 1_000, "ask": ask_depth},
            },
            "bid_levels": [[1, best_bid, 100], [2, best_bid - 10, 900]],
            "ask_levels": [
                [level, best_ask + (level - 1) * 10, quantity]
                for level, quantity in enumerate(quantities, start=1)
            ],
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "trading_runtime_effect": False,
        }

    depth_rows = [
        depth(
            "2026-08-14T09:00:05.900+09:00",
            sequence=1,
            quantities=(100, 200, 300, 400, 500),
        ),
        depth(
            "2026-08-14T09:00:06.250+09:00",
            sequence=2,
            quantities=(80, 180, 280, 380, 480),
        ),
        depth(
            "2026-08-14T09:00:06.500+09:00",
            sequence=3,
            quantities=(60, 160, 260, 360, 460),
        ),
        depth(
            "2026-08-14T09:00:06.700+09:00",
            sequence=4,
            quantities=(70, 170, 270, 370, 470),
        ),
        depth(
            "2026-08-14T09:00:07.000+09:00",
            sequence=5,
            quantities=(80, 180, 280, 380, 480),
        ),
        depth(
            "2026-08-14T09:00:07.500+09:00",
            sequence=6,
            quantities=(90, 190, 290, 390, 490),
        ),
        depth(
            "2026-08-14T09:00:08.999+09:00",
            sequence=7,
            quantities=(90, 190, 290, 390, 490),
        ),
        depth(
            "2026-08-14T09:00:09.700+09:00",
            sequence=8,
            quantities=(90, 190, 290, 390, 490),
        ),
        depth(
            "2026-08-14T09:00:10.999+09:00",
            sequence=9,
            quantities=(90, 190, 290, 390, 490),
            best_bid=9_960,
            best_ask=9_970,
        ),
        depth(
            "2026-08-14T09:00:15.999+09:00",
            sequence=10,
            quantities=(90, 190, 290, 390, 490),
            best_bid=9_970,
            best_ask=9_980,
        ),
    ]
    event_references = [
        {
            "schema": "scalp_micro_reversion_path_event_reference_v2",
            "symbol": "000001",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sequence_epoch": 123,
            "parent_wave_id": "wave-materialize-1",
            "path_segment_id": "segment-materialize-1",
            "shock_event_id": "shock-materialize-1",
            "shock_horizon_ms": 1_000,
            "event_sequence_in_wave": 1,
            "event_detected_at_ms": int(
                datetime.fromisoformat("2026-08-14T09:00:06.000+09:00").timestamp()
                * 1_000
            ),
            "segment_event_detected_at_ms": int(
                datetime.fromisoformat("2026-08-14T09:00:06.000+09:00").timestamp()
                * 1_000
            ),
            "capture_started_at": "2026-08-14T09:00:05.000+09:00",
            "capture_ended_at": "2026-08-14T09:03:06.000+09:00",
            "decision_authority": ("forward_path_observation_only_no_policy_selection"),
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "trading_runtime_effect": False,
        }
    ]
    cost_profile_artifact = {
        "schema": "micro_reversion_reviewed_cost_profile_v1",
        "artifact_id": "verified-test-cost-profile-v1",
        "effective_date": "2026-08-14",
        "venues": ["KRX"],
        "instrument_scope": "domestic_common_or_preferred_stock",
        "source": "verified_test_profile",
        "buy_fee_bps": 0.0,
        "sell_fee_bps": 0.0,
        "statutory_sell_tax_bps": 20.0,
        "uncertainty_buffer_bps": 3.0,
    }
    bridge_config = {
        "statutory_sell_tax_bps": 20.0,
        "uncertainty_buffer_bps": 3.0,
        "cost_profile_source": "verified_test_profile",
        "cost_profile_verified": True,
        "cost_profile_artifact_id": "verified-test-cost-profile-v1",
        "cost_profile_artifact_sha256": quality._sha256(cost_profile_artifact),
        "cost_profile_artifact_payload_json": json.dumps(
            cost_profile_artifact,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        "cost_profile_effective_date": "2026-08-14",
        "cost_profile_venues": ("KRX",),
    }
    source_bundle = quality.build_micro_reversion_source_bundle(
        target_date="2026-08-14",
        prepared_requests=prepared,
        traces=[trace],
        payloads=[payload],
        prompt_rows=prompt_rows,
        control_prompt_contracts=control_contract_artifact["control_prompt_contracts"],
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=event_references,
        bridge_config=bridge_config,
        verified_symbol_metadata_by_trace={
            "trace-materialize-1": {
                "lookup_status": "verified",
                "record": {
                    "symbol": "000001",
                    "listing_market": "KOSPI",
                    "instrument_type": "EQUITY",
                    "instrument_tax_class": "ordinary_taxable_equity_20bps",
                    "effective_from": "2026-01-01",
                    "effective_to": None,
                    "metadata_source": "verified_test_symbol_master",
                    "source_reference": "test://symbol-master/000001",
                    "verified_at": "2026-08-14T00:00:00+09:00",
                    "conflict_status": "clean",
                },
                "symbol_master_artifact_sha256": "a" * 64,
            }
        },
    )
    return prepared, source_bundle


def _reseal_current_materialized_report(report: dict) -> None:
    template = deepcopy(report["materializations"][0])
    reconstruction_template = deepcopy(
        report["current_control_contract_reconstructions"][0]
    )
    grouped: dict[str, list[dict]] = {}
    for request in report["requests"]:
        grouped.setdefault(request["paired_replay_parent_id"], []).append(request)
    decision_fields = (
        "prompt_version",
        "system_prompt_sha256",
        "schema_name",
        "response_schema_sha256",
        "semantic_validator_version",
    )
    execution_fields = (
        "provider",
        "model",
        "temperature",
        "reasoning_effort",
        "transport",
        "max_output_tokens",
        "response_schema_mode",
        "require_json",
        "response_schema_registry_used",
    )
    materializations = []
    for rows in grouped.values():
        by_arm = {row["micro_reversion_replay_arm"]: row for row in rows}
        base = by_arm["replay_control_exact_plus_micro"]
        ask_control = by_arm["replay_control_exact_plus_micro_ask_depletion"]
        candidate = by_arm["replay_candidate_exact_plus_micro_ask_depletion"]
        control_contract = base["candidate"]
        candidate_contract = candidate["candidate"]
        content = {
            **{
                key: value
                for key, value in template.items()
                if key != "materialization_sha256"
            },
            "decision_trace_id": base["decision_trace_id"],
            "source_exact_payload_sha256": base["source_exact_payload_sha256"],
            "tactical_micro_reversion_evidence_sha256": base[
                "tactical_micro_reversion_evidence_sha256"
            ],
            "ask_depletion_contract_sha256": ask_control[
                "ask_depletion_contract_sha256"
            ],
            "ask_depletion_context_sha256": ask_control["ask_depletion_context_sha256"],
            "control_decision_contract_sha256": quality._sha256(
                {field: control_contract.get(field) for field in decision_fields}
            ),
            "candidate_decision_contract_sha256": quality._sha256(
                {field: candidate_contract.get(field) for field in decision_fields}
            ),
            "locked_execution_contract_sha256": quality._sha256(
                {field: control_contract.get(field) for field in execution_fields}
            ),
        }
        materializations.append(
            {
                **content,
                "materialization_sha256": quality._sha256(
                    {**content, "requests": rows}
                ),
            }
        )
    report["materializations"] = materializations
    report["materialization_count"] = len(materializations)
    report["current_control_contract_reconstructions"] = [
        deepcopy(reconstruction_template) for _ in materializations
    ]
    report["source_exclusion_count"] = len(report["source_exclusions"])
    report["prepared_request_count"] = len(materializations) + len(
        report["source_exclusions"]
    )
    report["request_ids"] = [
        request["paired_replay_id"] for request in report["requests"]
    ]
    report["request_count"] = len(report["requests"])
    report["report_content_sha256"] = quality._sha256(
        {key: value for key, value in report.items() if key != "report_content_sha256"}
    )


def test_provider_execution_freezes_exact_materialized_and_outcome_companions(
    tmp_path, monkeypatch
):
    target_date = "2026-08-14"
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    materialized_path = tmp_path / "materialized.json"
    materialized_gzip_path = materialized_path.with_name(
        f"{materialized_path.name}.gz"
    )
    with gzip.open(materialized_gzip_path, "wt", encoding="utf-8") as handle:
        json.dump(materialized, handle)
    outcome_path = tmp_path / "outcome.json"
    outcome = {"schema": "test_outcome_v1", "target_date": target_date}
    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    execution_path = tmp_path / "execution.json"
    execution_body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": target_date,
        "provider_call_performed": True,
        "result_count": 1,
        "committed_parent_count": 1,
        "materialized_artifact_path": str(materialized_gzip_path),
        "materialized_report_content_sha256": materialized[
            "report_content_sha256"
        ],
        "materialized_report_artifact_sha256": quality._sha256(materialized),
        "materialized_request_census_sha256": (
            quality._micro_reversion_materialized_request_census_sha256(
                materialized
            )
        ),
        "outcome_label_artifact_path": str(outcome_path),
        "outcome_label_artifact_sha256": quality._sha256(outcome),
    }
    execution = {
        **execution_body,
        "report_content_sha256": quality._sha256(execution_body),
    }
    execution_path.write_text(json.dumps(execution), encoding="utf-8")
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _target_date: execution_path,
    )

    frozen_materialized = quality._frozen_provider_materialized_companion(
        target_date,
        logical_path=materialized_path,
    )
    assert frozen_materialized is not None
    assert quality._sha256(frozen_materialized) == quality._sha256(materialized)
    assert quality._frozen_provider_outcome_companion(target_date) == (
        outcome_path,
        outcome,
    )

    mutated_outcome = {**outcome, "mutated": True}
    outcome_path.write_text(json.dumps(mutated_outcome), encoding="utf-8")
    with pytest.raises(
        ValueError, match="frozen_outcome_companion_binding_mismatch"
    ):
        quality._frozen_provider_outcome_companion(target_date)

    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    mutated_materialized = deepcopy(materialized)
    mutated_materialized["generated_at"] = "2026-08-14T23:59:59+09:00"
    mutated_materialized["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in mutated_materialized.items()
            if key != "report_content_sha256"
        }
    )
    with gzip.open(materialized_gzip_path, "wt", encoding="utf-8") as handle:
        json.dump(mutated_materialized, handle)
    with pytest.raises(
        ValueError, match="frozen_materialized_companion_binding_mismatch"
    ):
        quality._frozen_provider_materialized_companion(
            target_date,
            logical_path=materialized_path,
        )


def test_uncommitted_execution_does_not_freeze_companions(tmp_path, monkeypatch):
    target_date = "2026-08-14"
    execution_path = tmp_path / "execution.json"
    execution_body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": target_date,
        "provider_call_performed": False,
        "result_count": 0,
        "committed_parent_count": 0,
    }
    execution_path.write_text(
        json.dumps(
            {
                **execution_body,
                "report_content_sha256": quality._sha256(execution_body),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _target_date: execution_path,
    )

    assert quality._provider_execution_companion_freeze_report(target_date) is None


def test_provider_checkpoint_results_freeze_materialized_companion(
    tmp_path, monkeypatch
):
    target_date = "2026-08-14"
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    materialized_path = tmp_path / "materialized.json"
    materialized_path.write_text(json.dumps(materialized), encoding="utf-8")
    execution_path = tmp_path / "execution.json"
    checkpoint_path = tmp_path / "execution.checkpoint.json"
    checkpoint_path.write_text("{}", encoding="utf-8")
    outcome_path = tmp_path / "outcome.json"
    outcome_proof = {"label_id": "label-1", "status": "mature"}
    outcome = {"labels": [outcome_proof]}
    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    checkpoint = {
        "schema": "micro_reversion_execution_checkpoint_v1",
        "provider_call_performed": True,
        "materialized_report_content_sha256": (
            quality._micro_reversion_materialized_request_census_sha256(
                materialized
            )
        ),
        "results": [
            {
                "paired_replay_id": "committed-request",
                "outcome_join_key": "label-1",
                "outcome_label_content_sha256": quality._sha256(outcome_proof),
            }
        ],
    }
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _target_date: execution_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_checkpoint_path",
        lambda _target_date: checkpoint_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_action_neutral_label_path",
        lambda _target_date: outcome_path,
    )
    monkeypatch.setattr(
        quality,
        "_load_micro_reversion_checkpoint",
        lambda *_args, **_kwargs: checkpoint,
    )

    frozen = quality._frozen_provider_materialized_companion(
        target_date,
        logical_path=materialized_path,
    )
    assert frozen is not None
    assert quality._sha256(frozen) == quality._sha256(materialized)
    assert quality._frozen_provider_outcome_companion(target_date) == (
        outcome_path,
        outcome,
    )

    checkpoint["materialized_report_content_sha256"] = "f" * 64
    with pytest.raises(
        ValueError, match="frozen_checkpoint_materialized_binding_mismatch"
    ):
        quality._frozen_provider_materialized_companion(
            target_date,
            logical_path=materialized_path,
        )

    checkpoint["materialized_report_content_sha256"] = (
        quality._micro_reversion_materialized_request_census_sha256(materialized)
    )
    checkpoint["results"][0]["outcome_label_content_sha256"] = ""
    assert quality._sha256(
        quality._frozen_provider_materialized_companion(
            target_date,
            logical_path=materialized_path,
        )
    ) == quality._sha256(materialized)
    assert quality._frozen_provider_outcome_companion(target_date) is None


def test_materializes_micro_reversion_requests_from_actual_prepared_output():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    persisted_prepared = json.loads(json.dumps(prepared))
    persisted_prepared[0].pop("exact_payload")

    report = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=persisted_prepared,
        bridge_source_bundle=source_bundle,
    )

    assert report["status"] == "materialized_source_only_no_provider_calls"
    assert report["prepared_request_count"] == 1
    assert report["materialization_count"] == 1
    assert report["request_count"] == 3
    assert len(set(report["request_ids"])) == 3
    assert report["ablation_design_version"] == (
        "current_micro_vs_ask_depletion_prompt_v1"
    )
    assert [row["micro_reversion_replay_arm"] for row in report["requests"]] == [
        "replay_control_exact_plus_micro",
        "replay_control_exact_plus_micro_ask_depletion",
        "replay_candidate_exact_plus_micro_ask_depletion",
    ]
    assert report["requests"][0]["candidate"]["prompt_version"] == (
        "current_control_v1"
    )
    assert report["requests"][2]["candidate"]["prompt_version"] == (
        f"{quality.DECISION_QUALITY_V2_PROMPT_VERSION}_entry"
    )
    assert report["provider_call_performed"] is False
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert report["current_control_contract_reconstructions"] == [
        {
            "decision_trace_id": "trace-materialize-1",
            "status": "natural_control_contract_verified",
            "natural_control_contract_status": "verified_exact_trace_contract",
            "source_trace_reconstructed_fields": [],
            "response_contract_anchor": "trace_response_schema_sha256",
            "control_contract_sha256": source_bundle["rows"][0][
                "current_control_prompt_contract"
            ]["contract_sha256"],
        }
    ]


def test_current_source_bundle_rejects_rehashed_sidecar_semantic_tampering() -> None:
    prepared, source_bundle = _micro_reversion_materialization_fixture()

    def reseal_sidecar(bundle: dict) -> None:
        row = bundle["rows"][0]
        sidecar = row["ask_depletion_sidecar"]
        sidecar["ask_depletion_context_sha256"] = quality._sha256(
            {
                key: value
                for key, value in sidecar.items()
                if key != "ask_depletion_context_sha256"
            }
        )
        row["ask_depletion_context_sha256"] = sidecar["ask_depletion_context_sha256"]
        bundle["source_bundle_content_sha256"] = quality._sha256(
            {
                key: value
                for key, value in bundle.items()
                if key != "source_bundle_content_sha256"
            }
        )

    cross_symbol = deepcopy(source_bundle)
    cross_symbol["rows"][0]["ask_depletion_sidecar"]["context"]["symbol"] = "999999"
    reseal_sidecar(cross_symbol)
    with pytest.raises(
        ValueError, match="ask_depletion_sidecar_context_identity_mismatch"
    ):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=prepared,
            bridge_source_bundle=cross_symbol,
        )

    immature = deepcopy(source_bundle)
    eligible_horizon = next(
        row
        for row in immature["rows"][0]["ask_depletion_sidecar"]["horizons"]
        if row["eligible_for_feature_ablation"] is True
    )
    eligible_horizon["mature"] = False
    eligible_horizon["source_gap_reasons"] = ["forced_gap"]
    reseal_sidecar(immature)
    with pytest.raises(
        ValueError, match="ask_depletion_complete_horizon_contract_invalid"
    ):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=prepared,
            bridge_source_bundle=immature,
        )

    mixed_legacy_current = deepcopy(source_bundle)
    mixed_legacy_current.pop("ablation_design_version")
    mixed_legacy_current["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in mixed_legacy_current.items()
            if key != "source_bundle_content_sha256"
        }
    )
    with pytest.raises(
        ValueError,
        match="micro_reversion_source_bundle_legacy_current_contract_mixed",
    ):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=prepared,
            bridge_source_bundle=mixed_legacy_current,
        )


def test_micro_reversion_source_contract_reconstructs_omitted_exact_payload():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    persisted_request = json.loads(json.dumps(prepared[0]))
    persisted_request.pop("exact_payload")
    source_row = source_bundle["rows"][0]

    quality._assert_micro_reversion_source_contract(
        request=persisted_request,
        source_trace=source_row["source_trace"],
        source_payload=source_row["source_payload"],
    )

    tampered_payload = json.loads(json.dumps(source_row["source_payload"]))
    tampered_payload["sanitized_replay_context"]["exact_payload"][
        "requested_qty"
    ] = 99_999
    with pytest.raises(
        ValueError, match="micro_reversion_source_exact_payload_sha256_mismatch"
    ):
        quality._assert_micro_reversion_source_contract(
            request=persisted_request,
            source_trace=source_row["source_trace"],
            source_payload=tampered_payload,
        )


def test_micro_reversion_rehydrates_omitted_holding_candidate_input():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    persisted_request = json.loads(json.dumps(prepared[0]))
    persisted_request.pop("exact_payload")
    persisted_request["stage"] = "holding"
    source_payload = source_bundle["rows"][0]["source_payload"]
    exact_payload = quality._replay_exact_payload(
        quality.replay_source_input(source_payload)
    )
    candidate_input = {
        "exact_payload": exact_payload,
        "holding_exact_contract_facts_v1": quality._holding_contract_facts(
            exact_payload
        ),
    }
    persisted_request["candidate_input_sha256"] = quality._sha256(candidate_input)

    hydrated = quality._rehydrate_micro_reversion_prepared_request(
        request=persisted_request,
        source_payload=source_payload,
    )

    assert hydrated["exact_payload"] == exact_payload
    assert hydrated["candidate_input"] == candidate_input
    persisted_request["candidate_input_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="candidate_input_sha256_mismatch"):
        quality._rehydrate_micro_reversion_prepared_request(
            request=persisted_request,
            source_payload=source_payload,
        )


def test_micro_reversion_control_semantic_analysis_is_derived_outside_provider_input():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    request = json.loads(json.dumps(prepared[0]))
    request.pop("exact_payload")
    request["candidate"][
        "prompt_version"
    ] = f"{quality.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry"
    request["candidate"][
        "semantic_validator_version"
    ] = quality.BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION

    hydrated = quality._rehydrate_micro_reversion_prepared_request(
        request=request,
        source_payload=source_bundle["rows"][0]["source_payload"],
    )
    hydrated["micro_reversion_replay_arm"] = "replay_control_exact_no_micro"
    errors = quality.validate_replay_candidate_response(
        hydrated, _valid_micro_reversion_entry_response()
    )

    assert "anticipatory_analysis_missing" not in errors
    assert hydrated["anticipatory_reversal_analysis"]["schema"] == (
        quality.ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA
    )
    assert "recovery_confirmation_probe" in hydrated["anticipatory_reversal_analysis"]
    assert "anticipatory_reversal_analysis_v1" not in hydrated.get(
        "candidate_input", {}
    )


def test_micro_reversion_recovers_known_nonsecret_prompt_redaction_by_hash():
    exact = "The action value must be exactly one JSON enum token: BUY, WAIT, or DROP."
    stored = exact.replace("token: BUY", "token: [REDACTED]")
    row = {
        "sanitized_prompt": stored,
        "replay_exact": False,
        "redacted": True,
    }

    assert quality._verified_stored_prompt_body(
        row,
        expected_prompt_sha256=quality._stored_prompt_sha256(exact),
    ) == (exact, "hash_exact_known_non_secret_enum_token_reconstruction")
    assert (
        quality._verified_stored_prompt_body(
            row,
            expected_prompt_sha256="f" * 64,
        )
        is None
    )


def test_micro_reversion_accepts_hash_exact_false_positive_redaction_flag():
    exact = "The action value must be exactly one JSON enum token: BUY, WAIT, or DROP."
    row = {
        "sanitized_prompt": exact,
        "replay_exact": False,
        "redacted": True,
    }

    assert quality._verified_stored_prompt_body(
        row,
        expected_prompt_sha256=quality._stored_prompt_sha256(exact),
    ) == (exact, "hash_exact_false_positive_redaction_flag")
    assert (
        quality._verified_stored_prompt_body(
            row,
            expected_prompt_sha256="f" * 64,
        )
        is None
    )


def test_micro_reversion_materialization_fails_closed_without_full_control_prompt():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    source_bundle["rows"][0]["current_control_prompt_contract"].pop("system_prompt")
    source_bundle["source_bundle_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bundle.items()
            if key != "source_bundle_content_sha256"
        }
    )

    with pytest.raises(ValueError, match="control_system_prompt_missing"):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=prepared,
            bridge_source_bundle=source_bundle,
        )


def test_micro_reversion_materialize_cli_does_not_enter_provider_source_flow(
    tmp_path, monkeypatch, capsys
):
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle

    prepared, source_bundle = _micro_reversion_materialization_fixture()
    prepared_path = tmp_path / "prepared.json"
    source_path = tmp_path / "source.json"
    output_path = tmp_path / "materialized.json"
    execution_path = tmp_path / "execution.json"
    capacity_path = tmp_path / "capacity.json"
    prepared_artifact = cycle.build_prepared_request_artifact(
        target_date="2026-08-14",
        paired_report={
            "schema": quality.PAIRED_SCHEMA,
            "target_date": "2026-08-14",
            "requests": prepared,
            **cycle.OFFLINE_AUTHORITY,
        },
        source={"resolved_path": str(prepared_path), "stored_sha256": "a" * 64},
    )
    prepared_path.write_text(json.dumps(prepared_artifact), encoding="utf-8")
    source_path.write_text(json.dumps(source_bundle), encoding="utf-8")
    monkeypatch.setattr(
        quality,
        "_default_sources",
        lambda *args, **kwargs: pytest.fail("provider/source flow must not run"),
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_materialized_request_path",
        lambda target_date: output_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda target_date: execution_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date="2026-08-14",
            capacity_path=capacity_path,
        ),
    )

    assert (
        quality.main(
            [
                "--date",
                "2026-08-14",
                "--mode",
                "micro_reversion_materialize",
                "--micro-reversion-prepared-requests",
                str(prepared_path),
                "--micro-reversion-source-bundle",
                str(source_path),
                "--micro-reversion-storage-capacity-status",
                str(capacity_path),
                "--write",
            ]
        )
        == 0
    )

    printed = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert printed["provider_call_performed"] is False
    assert written["request_count"] == 3
    assert written["provider_call_performed"] is False
    assert written["runtime_effect"] is False
    assert written["actual_order_submitted"] is False

    execution_body = {
        "schema": quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA,
        "target_date": "2026-08-14",
        "provider_call_performed": True,
        "result_count": 1,
        "materialized_artifact_path": str(output_path),
        "materialized_report_content_sha256": written["report_content_sha256"],
        "materialized_report_artifact_sha256": quality._sha256(written),
        "materialized_request_census_sha256": (
            quality._micro_reversion_materialized_request_census_sha256(written)
        ),
    }
    execution_path.write_text(
        json.dumps(
            {
                **execution_body,
                "report_content_sha256": quality._sha256(execution_body),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        quality,
        "_atomic_write_json",
        lambda *_args, **_kwargs: pytest.fail(
            "Provider-bound materialized companion must not be overwritten"
        ),
    )
    assert (
        quality.main(
            [
                "--date",
                "2026-08-14",
                "--mode",
                "micro_reversion_materialize",
                "--micro-reversion-prepared-requests",
                str(prepared_path),
                "--micro-reversion-source-bundle",
                str(source_path),
                "--micro-reversion-storage-capacity-status",
                str(capacity_path),
                "--write",
            ]
        )
        == 0
    )
    frozen_printed = json.loads(capsys.readouterr().out)
    assert frozen_printed["provider_execution_companion_frozen"] is True

    execution_path.unlink()
    checkpoint_path = quality.micro_reversion_execution_checkpoint_path(
        "2026-08-14"
    )
    checkpoint_path.write_text("{}", encoding="utf-8")
    checkpoint = {
        "provider_call_performed": True,
        "materialized_report_content_sha256": (
            quality._micro_reversion_materialized_request_census_sha256(written)
        ),
        "results": [
            {
                "paired_replay_id": "committed-request",
                "outcome_join_key": "label-1",
                "outcome_label_content_sha256": "f" * 64,
            }
        ],
    }
    monkeypatch.setattr(
        quality,
        "_load_micro_reversion_checkpoint_unlocked",
        lambda *_args, **_kwargs: checkpoint,
    )
    assert (
        quality.main(
            [
                "--date",
                "2026-08-14",
                "--mode",
                "micro_reversion_materialize",
                "--micro-reversion-prepared-requests",
                str(prepared_path),
                "--micro-reversion-source-bundle",
                str(source_path),
                "--micro-reversion-storage-capacity-status",
                str(capacity_path),
                "--write",
            ]
        )
        == 0
    )
    checkpoint_frozen_printed = json.loads(capsys.readouterr().out)
    assert checkpoint_frozen_printed["provider_execution_companion_frozen"] is True


def test_micro_reversion_json_loader_resolves_archived_gzip(tmp_path):
    logical_path = tmp_path / "ai_micro_reversion_replay_source_bundle_2026-08-24.json"
    expected = {"schema": "test", "target_date": "2026-08-24"}
    with gzip.open(
        logical_path.with_suffix(".json.gz"), "wt", encoding="utf-8"
    ) as handle:
        json.dump(expected, handle)

    assert quality._load_json(logical_path) == expected


def test_micro_reversion_source_bundle_cli_reads_gzip_exact_journals(
    tmp_path, monkeypatch, capsys
):
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle
    from src.engine.scalping.micro_reversion.symbol_master import (
        VerifiedSymbolMaster,
    )

    prepared, source_bundle = _micro_reversion_materialization_fixture()
    source_row = source_bundle["rows"][0]
    trace = source_row["source_trace"]
    payload = source_row["source_payload"]
    control_contract = source_row["current_control_prompt_contract"]
    prompt_row = {
        "schema": "ai_decision_prompt_v1",
        "prompt_sha256": trace["prompt_sha256"],
        "endpoint": trace["endpoint"],
        "model": trace["model"],
        "schema_name": payload["schema_name"],
        "redacted": False,
        "replay_exact": True,
        "sanitized_prompt": control_contract["system_prompt"],
    }
    prepared_path = tmp_path / "prepared.json"
    contract_path = tmp_path / "control_contracts.json"
    symbol_master_path = tmp_path / "symbol_master.json"
    prepared_artifact = cycle.build_prepared_request_artifact(
        target_date="2026-08-14",
        paired_report={
            "schema": quality.PAIRED_SCHEMA,
            "target_date": "2026-08-14",
            "requests": prepared,
            **cycle.OFFLINE_AUTHORITY,
        },
        source={"resolved_path": str(prepared_path), "stored_sha256": "a" * 64},
    )
    prepared_path.write_text(json.dumps(prepared_artifact), encoding="utf-8")
    contract_path.write_text(
        json.dumps(
            {
                "target_date": "2026-08-14",
                "bridge_config": source_row["bridge_config"],
                "excluded_scopes": [],
            }
        ),
        encoding="utf-8",
    )
    symbol_master_path.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_symbol_master_v1",
                "decision_authority": "instrument_metadata_source_only",
                "runtime_effect": False,
                "records": [source_row["verified_symbol_metadata"]["record"]],
            }
        ),
        encoding="utf-8",
    )

    trace_dir = tmp_path / "trace"
    payload_dir = tmp_path / "payload"
    prompt_dir = tmp_path / "prompt"
    for directory, file_name, row in (
        (trace_dir, "ai_decision_trace_2026-08-14.jsonl.gz", trace),
        (payload_dir, "ai_decision_payloads_2026-08-14.jsonl.gz", payload),
        (prompt_dir, "ai_decision_prompts_2026-08-14.jsonl.gz", prompt_row),
    ):
        directory.mkdir(parents=True)
        with gzip.open(directory / file_name, "wt", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")

    observation_root = tmp_path / "observations"
    partition = (
        observation_root / "trade_date=2026-08-14" / "venue=KRX" / "session=KRX_REGULAR"
    )
    partition.mkdir(parents=True)
    for pool_name, file_name in (
        ("market", "market_stream.jsonl"),
        ("depth", "market_depth_stream.jsonl"),
        ("event_reference", "market_stream_event_references.jsonl"),
    ):
        rows = source_bundle["source_row_pool"][pool_name].values()
        (partition / file_name).write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )

    monkeypatch.setattr(quality, "TRACE_DIR", trace_dir)
    monkeypatch.setattr(quality, "PAYLOAD_DIR", payload_dir)
    monkeypatch.setattr(quality, "PROMPT_DIR", prompt_dir)
    monkeypatch.setattr(
        VerifiedSymbolMaster,
        "from_json_path",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("symbol master must not be reread after strict payload load")
        ),
    )

    assert (
        quality.main(
            [
                "--date",
                "2026-08-14",
                "--mode",
                "micro_reversion_source_bundle",
                "--micro-reversion-prepared-requests",
                str(prepared_path),
                "--micro-reversion-control-contracts",
                str(contract_path),
                "--micro-reversion-observation-root",
                str(observation_root),
                "--micro-reversion-symbol-master",
                str(symbol_master_path),
            ]
        )
        == 0
    )

    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "bounded_source_bundle_ready_no_provider_calls"
    assert report["eligible_row_count"] == 1
    assert report["excluded_row_count"] == 0
    assert report["provider_call_performed"] is False
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False

    data_dir = tmp_path / "isolated-data"
    pipeline_path = data_dir / "pipeline_events" / "pipeline_events_2026-08-14.jsonl"
    pipeline_path.parent.mkdir(parents=True)
    pipeline_path.with_name(f"{pipeline_path.name}.gz").symlink_to(
        tmp_path / "missing-pipeline-target.jsonl.gz"
    )
    bridge_path = tmp_path / "bridge.json"
    bridge_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(quality, "DATA_DIR", data_dir)

    def consume_entry_pipeline_rows(**kwargs):
        list(kwargs["entry_pipeline_rows"])
        raise AssertionError("broken pipeline generation must fail closed")

    monkeypatch.setattr(
        quality,
        "build_micro_reversion_source_bundle",
        consume_entry_pipeline_rows,
    )
    with pytest.raises(ValueError, match="jsonl_artifact_path_type_invalid"):
        quality.main(
            [
                "--date",
                "2026-08-14",
                "--mode",
                "micro_reversion_source_bundle",
                "--micro-reversion-prepared-requests",
                str(prepared_path),
                "--micro-reversion-control-contracts",
                str(contract_path),
                "--micro-reversion-observation-root",
                str(observation_root),
                "--micro-reversion-bridge-report",
                str(bridge_path),
            ]
        )


def _micro_reversion_execution_label(prepared):
    request = prepared[0]
    return {
        "schema": "ai_decision_outcome_label_v1",
        "label_id": request["outcome_join_key"],
        "decision_trace_id": request["decision_trace_id"],
        "decision_stage": request["stage"],
        "stock_code": request["stock_code"],
        "effective_venue": request["effective_venue"],
        "session_bucket": request["session_bucket"],
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 1.0,
                "mfe_pct": 1.2,
                "mae_pct": -0.3,
                "first_hit": "target",
            }
        },
    }


def _micro_reversion_action_neutral_bridge_fixture():
    from src.engine.scalping.micro_reversion.ai_quality_bridge import (
        BridgeConfig,
        build_bridge_report,
    )

    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    source_row = source_bundle["rows"][0]
    evidence = source_row["evidence"]
    market_rows = quality._micro_reversion_source_rows_from_pool(
        source_bundle=source_bundle,
        bundle_row=source_row,
        pool_name="market",
        reference_field="source_market_row_sha256s",
    )
    depth_rows = quality._micro_reversion_source_rows_from_pool(
        source_bundle=source_bundle,
        bundle_row=source_row,
        pool_name="depth",
        reference_field="source_depth_row_sha256s",
    )
    event_references = quality._micro_reversion_source_rows_from_pool(
        source_bundle=source_bundle,
        bundle_row=source_row,
        pool_name="event_reference",
        reference_field="source_event_reference_sha256s",
    )
    last_market = market_rows[-1]
    last_depth = depth_rows[-1]
    path_extension_start = datetime.fromisoformat(
        str(last_market["local_receive_timestamp"])
    ).replace(microsecond=0)
    for offset_sec in range(1, 13):
        timestamp = path_extension_start.timestamp() + offset_sec
        observed_at = datetime.fromtimestamp(timestamp, tz=KST).isoformat()
        market_rows.append(
            {
                **last_market,
                "source_sequence": last_market["source_sequence"] + offset_sec,
                "series_sequence": last_market["series_sequence"] + offset_sec,
                "exchange_timestamp": observed_at,
                "local_receive_timestamp": observed_at,
                "trade_price": 10_060,
                "best_bid": 10_050,
                "best_ask": 10_060,
                "aggressor_side": "BUY",
            }
        )
        depth_rows.append(
            {
                **last_depth,
                "source_sequence": last_depth["source_sequence"] + offset_sec,
                "series_sequence": last_depth["series_sequence"] + offset_sec,
                "exchange_timestamp": observed_at,
                "local_receive_timestamp": observed_at,
                "best_bid": 10_050,
                "best_ask": 10_060,
                "bid_levels": [[1, 10_050, 100], [2, 10_040, 900]],
                "ask_levels": [
                    [1, 10_060, 90],
                    [2, 10_070, 190],
                    [3, 10_080, 290],
                    [4, 10_090, 390],
                    [5, 10_100, 490],
                ],
            }
        )
    config = BridgeConfig(**source_row["bridge_config"])
    bridge_report = build_bridge_report(
        target_date="2026-08-14",
        traces=[source_row["source_trace"]],
        payloads=[source_row["source_payload"]],
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=event_references,
        config=config,
        verified_symbol_metadata_by_trace={
            prepared[0]["decision_trace_id"]: source_row["verified_symbol_metadata"]
        },
    )
    assert bridge_report["rows"][0]["tactical_micro_reversion_evidence_v1"] == (
        evidence
    )
    return prepared, materialized, bridge_report


def _current_outcome_artifact_for_materialized(materialized: dict) -> dict:
    """Clone one exact bridge proof onto the materialized parent census."""

    _, base_materialized, bridge_report = (
        _micro_reversion_action_neutral_bridge_fixture()
    )
    base_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=base_materialized,
    )
    template = base_artifact["labels"][0]
    join_keys = list(
        dict.fromkeys(
            str(request["outcome_join_key"]) for request in materialized["requests"]
        )
    )
    labels = []
    for join_key in join_keys:
        label = deepcopy(template)
        label["label_id"] = join_key
        label["target_date"] = materialized["target_date"]
        label["materialized_report_content_sha256"] = materialized[
            "report_content_sha256"
        ]
        label["label_content_sha256"] = quality._sha256(
            {
                key: value
                for key, value in label.items()
                if key != "label_content_sha256"
            }
        )
        labels.append(label)
    parent_bindings = quality._micro_reversion_materialized_parent_bindings(
        materialized["requests"]
    )
    artifact = deepcopy(base_artifact)
    artifact.update(
        {
            "target_date": materialized["target_date"],
            "status": "action_neutral_labels_ready",
            "prepared_parent_count": len(labels),
            "eligible_label_count": len(labels),
            "excluded_parent_count": 0,
            "labels": labels,
            "exclusions": [],
            "materialized_parent_binding_count": len(parent_bindings),
            "materialized_parent_bindings": parent_bindings,
            "materialized_parent_bindings_sha256": quality._sha256(parent_bindings),
            "materialized_report_content_sha256": materialized["report_content_sha256"],
        }
    )
    artifact["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in artifact.items()
            if key != "artifact_content_sha256"
        }
    )
    quality._validate_micro_reversion_outcome_label_artifact(
        artifact,
        expected_design_version=materialized["ablation_design_version"],
        expected_target_date=materialized["target_date"],
        expected_materialized_report_content_sha256=materialized[
            "report_content_sha256"
        ],
    )
    return artifact


def test_micro_reversion_bridge_outcome_adapts_action_neutral_seconds_label():
    prepared, materialized, bridge_report = (
        _micro_reversion_action_neutral_bridge_fixture()
    )

    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )

    assert artifact["status"] == "action_neutral_labels_ready"
    assert artifact["eligible_label_count"] == 1
    label = artifact["labels"][0]
    assert label["label_id"] == prepared[0]["outcome_join_key"]
    assert label["primary_horizon_key"] == "10s"
    assert "10m" not in label["horizon_metrics"]
    primary = quality._micro_reversion_primary_metric(label)
    assert primary["first_hit"] == "net_target_first"
    assert primary["source_quality_adjusted_ev_pct"] > 0
    assert primary["action_neutral_path_sha256"]
    assert label["quantity_authority"] == ("standardized_one_share_observation_only")
    assert label["notional_net_profit_eligible"] is False
    assert label["outcome_embedded_in_provider_input"] is False
    assert "source_bridge_report" not in artifact
    assert artifact["bridge_report_artifact_sha256"] == quality._sha256(bridge_report)
    assert "source_bridge_report" not in label


def test_current_materialized_report_rejects_resealed_cross_date_evidence():
    _, materialized, _ = _micro_reversion_action_neutral_bridge_fixture()
    materialized["target_date"] = "2026-08-24"
    _reseal_current_materialized_report(materialized)

    with pytest.raises(ValueError, match="current_target_date_mismatch"):
        quality._validate_micro_reversion_materialized_report(materialized)


def test_current_target_date_rejects_cross_date_fixed_followthrough_endpoint():
    _, _, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    bridge_row = bridge_report["rows"][0]
    evidence = deepcopy(bridge_row["tactical_micro_reversion_evidence_v1"])
    outcome = deepcopy(bridge_row["future_outcome"])
    fixed_outcome = outcome["confirmation_window_axis"]["observations"][0][
        "fixed_followthrough_outcomes"
    ][0]
    fixed_outcome["endpoint_observed_at_ms"] = (
        evidence["snapshot_captured_at_ms"] + 86_400_000
    )

    with pytest.raises(
        ValueError,
        match=(
            "micro_reversion_current_target_date_mismatch:"
            "outcome.confirmation_window_axis.observations"
        ),
    ):
        quality._validate_current_micro_reversion_target_date_binding(
            target_date="2026-08-14",
            evidence=evidence,
            outcome=outcome,
        )


def test_action_neutral_artifact_rejects_resealed_shifted_bridge_row():
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )
    from src.engine.scalping.micro_reversion.ai_quality_bridge import (
        rebuild_future_outcome_from_source,
    )

    source_bridge = deepcopy(bridge_report)
    source_row = source_bridge["rows"][0]
    rebuild_source = source_row["future_outcome_rebuild_source"]
    rebuild_source["control_action"] = "DROP"
    rebuild_source["rebuild_source_sha256"] = quality._sha256(
        {
            key: value
            for key, value in rebuild_source.items()
            if key != "rebuild_source_sha256"
        }
    )
    source_row["future_outcome"] = rebuild_future_outcome_from_source(
        evidence=source_row["tactical_micro_reversion_evidence_v1"],
        rebuild_source=rebuild_source,
        source_pool=source_bridge["future_outcome_source_pool"],
    )
    source_bridge["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_bridge.items()
            if key != "report_content_sha256"
        }
    )
    artifact["bridge_report_content_sha256"] = source_bridge["report_content_sha256"]
    artifact["bridge_report_artifact_sha256"] = quality._sha256(source_bridge)
    for label in artifact["labels"]:
        label["bridge_report_content_sha256"] = artifact["bridge_report_content_sha256"]
        label["bridge_report_artifact_sha256"] = artifact[
            "bridge_report_artifact_sha256"
        ]
        label["label_content_sha256"] = quality._sha256(
            {
                key: value
                for key, value in label.items()
                if key != "label_content_sha256"
            }
        )
    artifact["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in artifact.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(ValueError, match="label_artifact_binding_invalid"):
        quality._validate_micro_reversion_outcome_label_artifact(
            artifact,
            source_bridge_report=source_bridge,
        )


def test_action_neutral_artifact_validates_bridge_source_pool_once(monkeypatch):
    from src.engine.scalping.micro_reversion import ai_quality_bridge

    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )
    validation_calls = 0
    original_validation = ai_quality_bridge.validate_future_outcome_source_pool

    def counted_validation(*args, **kwargs):
        nonlocal validation_calls
        validation_calls += 1
        return original_validation(*args, **kwargs)

    monkeypatch.setattr(
        ai_quality_bridge,
        "validate_future_outcome_source_pool",
        counted_validation,
    )

    quality._validate_micro_reversion_outcome_label_artifact(
        artifact,
        source_bridge_report=bridge_report,
    )

    assert validation_calls == 1


def test_micro_reversion_bridge_outcome_rejects_unproven_integrated_micro_scope():
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    evidence_key = "tactical_micro_reversion_evidence_v1"
    bridge_row = bridge_report["rows"][0]
    evidence = bridge_row[evidence_key]
    evidence.update(
        {
            "micro_venue": "SOR",
            "micro_session_bucket": "SOR_REGULAR",
            "trace_market_data_route": "krx_nxt_integrated",
            "integrated_sor_route_proven": True,
        }
    )
    evidence["evidence_sha256"] = quality._sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )
    from src.engine.scalping.micro_reversion.ai_quality_bridge import (
        rebuild_future_outcome_from_source,
    )

    rebuild_source = bridge_row["future_outcome_rebuild_source"]
    source_pool = bridge_report["future_outcome_source_pool"]
    for pool_name in ("market", "depth"):
        replacements = {}
        rewritten_pool = {}
        for old_hash, raw_row in source_pool["row_pools"][pool_name].items():
            rewritten_row = {
                **raw_row,
                "venue": "SOR",
                "session_bucket": "SOR_REGULAR",
            }
            new_hash = quality._sha256(rewritten_row)
            replacements[old_hash] = new_hash
            rewritten_pool[new_hash] = rewritten_row
        source_pool["row_pools"][pool_name] = rewritten_pool
        reference_field = f"{pool_name}_row_sha256s"
        rebuild_source[reference_field] = [
            replacements[row_hash] for row_hash in rebuild_source[reference_field]
        ]
        rebuild_source[f"{reference_field}_sha256"] = quality._sha256(
            rebuild_source[reference_field]
        )
    source_pool["source_pool_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in source_pool.items()
            if key != "source_pool_content_sha256"
        }
    )
    bridge_report["future_outcome_source_pool_content_sha256"] = source_pool[
        "source_pool_content_sha256"
    ]
    bridge_report["future_outcome_source_pool_artifact_sha256"] = quality._sha256(
        source_pool
    )
    rebuild_source["evidence_sha256"] = evidence["evidence_sha256"]
    rebuild_source["source_pool_content_sha256"] = source_pool[
        "source_pool_content_sha256"
    ]
    rebuild_source["rebuild_source_sha256"] = quality._sha256(
        {
            key: value
            for key, value in rebuild_source.items()
            if key != "rebuild_source_sha256"
        }
    )
    bridge_row["future_outcome"] = rebuild_future_outcome_from_source(
        evidence=evidence,
        rebuild_source=rebuild_source,
        source_pool=bridge_report["future_outcome_source_pool"],
    )
    sidecar = bridge_row["ask_depletion_sidecar"]
    sidecar["context"].update(
        {
            "venue": "SOR",
            "session_bucket": "SOR_REGULAR",
        }
    )
    sidecar["tactical_micro_reversion_evidence_sha256"] = evidence["evidence_sha256"]
    sidecar["ask_depletion_context_sha256"] = quality._sha256(
        {
            key: value
            for key, value in sidecar.items()
            if key != "ask_depletion_context_sha256"
        }
    )
    bridge_report["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in bridge_report.items()
            if key != "report_content_sha256"
        }
    )
    for request in materialized["requests"]:
        candidate_input = request["candidate_input"]
        if evidence_key not in candidate_input:
            continue
        candidate_input[evidence_key] = deepcopy(evidence)
        feature_view = candidate_input.get(
            "micro_reversion_ask_depletion_feature_view_v2"
        )
        if isinstance(feature_view, dict):
            feature_view["context"] = deepcopy(sidecar["context"])
            feature_view["tactical_micro_reversion_evidence_sha256"] = evidence[
                "evidence_sha256"
            ]
            feature_view["ask_depletion_context_sha256"] = sidecar[
                "ask_depletion_context_sha256"
            ]
            feature_view["feature_view_sha256"] = quality._sha256(
                {
                    key: value
                    for key, value in feature_view.items()
                    if key != "feature_view_sha256"
                }
            )
            request["ask_depletion_context_sha256"] = sidecar[
                "ask_depletion_context_sha256"
            ]
        request["candidate_input_sha256"] = quality._sha256(candidate_input)
        request["tactical_micro_reversion_evidence_sha256"] = evidence[
            "evidence_sha256"
        ]
    _reseal_current_materialized_report(materialized)

    with pytest.raises(
        ValueError,
        match="current_action_neutral_selective_exclusion_forbidden",
    ):
        quality.build_micro_reversion_action_neutral_outcome_labels(
            bridge_report=bridge_report,
            materialized_report=materialized,
        )


def test_micro_reversion_bridge_outcome_rejects_unsupported_stage_per_row():
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    for request in materialized["requests"]:
        request["stage"] = "entry_price"
        request["endpoint"] = "entry_price"
    _reseal_current_materialized_report(materialized)

    with pytest.raises(
        ValueError,
        match="current_action_neutral_selective_exclusion_forbidden",
    ):
        quality.build_micro_reversion_action_neutral_outcome_labels(
            bridge_report=bridge_report,
            materialized_report=materialized,
        )


def test_micro_reversion_action_neutral_label_tamper_fails_declared_hash():
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )
    artifact["labels"][0]["horizon_metrics"]["10s"][
        "source_quality_adjusted_ev_pct"
    ] = 999.0
    artifact["artifact_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in artifact.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(ValueError, match="label_content_hash_mismatch"):
        quality._validate_micro_reversion_outcome_label_artifact(artifact)


def test_micro_reversion_bridge_report_tamper_fails_declared_hash():
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    bridge_report["summary"]["trace_payload_join_count"] = 999

    with pytest.raises(ValueError, match="bridge_report_content_hash_mismatch"):
        quality.build_micro_reversion_action_neutral_outcome_labels(
            bridge_report=bridge_report,
            materialized_report=materialized,
        )


def test_micro_reversion_action_neutral_label_flows_into_three_arm_evaluator():
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )

    def runner(request):
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": "test-response-id",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
                "input_tokens": 120,
                "output_tokens": 30,
            },
        }

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=artifact,
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=3,
    )

    evaluation = report["three_arm_evaluation"]
    assert evaluation["complete_parent_count"] == 1
    assert evaluation["rows"][0]["cost_adjusted_outcome_pct"] > 0
    assert evaluation["comparisons"][1]["paired_metric_eligible_parent_count"] == 1
    assert [
        (
            row["decision_stage"],
            row["effective_venue"],
            row["session_bucket"],
        )
        for row in evaluation["stage_venue_partitions"]
    ] == [("entry", "KRX", "KRX_REGULAR")]
    assert evaluation["cross_stage_venue_aggregate_promotion_forbidden"] is False
    assert report["outcomes_embedded_in_provider_input"] is False


def test_micro_reversion_execute_cli_uses_safe_single_worker_default(
    tmp_path, monkeypatch, capsys
):
    _freeze_quality_clock(monkeypatch, target_date="2026-08-14")
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    materialized_path = tmp_path / "materialized.json"
    bridge_path = tmp_path / "bridge.json"
    output_path = tmp_path / "execution.json"
    capacity_path = tmp_path / "capacity.json"
    raw_pricing_path = tmp_path / "provider-pricing-source.txt"
    raw_pricing_bytes = b"reviewed test pricing source\n"
    raw_pricing_path.write_bytes(raw_pricing_bytes)
    pricing_path = tmp_path / "provider-pricing.json"
    pricing_payload = {
        "schema": PRICING_ARTIFACT_SCHEMA,
        "artifact_id": "provider-pricing-test-v1",
        "review_status": "reviewed",
        "reviewed_at": "2026-08-14T18:00:00+09:00",
        "effective_from": "2026-08-14",
        "effective_to": "2026-08-14",
        "pricing_basis": "provider_public_rate",
        "raw_pricing_source_path": raw_pricing_path.name,
        "raw_pricing_source_bytes_sha256": hashlib.sha256(
            raw_pricing_bytes
        ).hexdigest(),
        "raw_pricing_source_size_bytes": len(raw_pricing_bytes),
        "prices": [
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "10",
            }
        ],
        "decision_authority": PRICING_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    pricing_payload["artifact_content_sha256"] = pricing_artifact_content_sha256(
        pricing_payload
    )
    pricing_path.write_text(json.dumps(pricing_payload), encoding="utf-8")
    budget_ledger_path = tmp_path / "provider-budget.jsonl"
    budget_summary_path = tmp_path / "provider-budget-summary.json"
    outcome_companion_path = tmp_path / "action-neutral-outcome-labels.json"
    materialized_path.write_text(json.dumps(materialized), encoding="utf-8")
    bridge_path.write_text(json.dumps(bridge_report), encoding="utf-8")
    monkeypatch.setattr(quality, "_offline_openai_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda target_date: output_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_action_neutral_label_path",
        lambda _target_date: outcome_companion_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date="2026-08-14",
            capacity_path=capacity_path,
        ),
    )
    provider_request_ids = []

    def fake_openai_runner(request, *, api_keys, timeout_sec):
        assert api_keys == ["test-key"]
        assert timeout_sec == 45.0
        provider_request_ids.append(request["paired_replay_id"])
        candidate = request["candidate"]
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": candidate["model"],
                "transport": "openai_responses_http_offline",
                "source_transport_contract": candidate["transport"],
                "response_id": f"response-{request['paired_replay_id']}",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
                "input_tokens": 120,
                "output_tokens": 30,
            },
        }

    monkeypatch.setattr(
        quality, "execute_openai_prompt_v2_candidate", fake_openai_runner
    )
    cli_args = [
        "--date",
        "2026-08-14",
        "--mode",
        "micro_reversion_execute",
        "--micro-reversion-materialized-requests",
        str(materialized_path),
        "--micro-reversion-bridge-report",
        str(bridge_path),
        "--execute-candidate",
        "--write",
        "--candidate-max-new-requests",
        "3",
        "--micro-reversion-provider-pricing",
        str(pricing_path),
        "--micro-reversion-provider-daily-attempt-cap",
        "12",
        "--micro-reversion-provider-daily-usd-cap",
        "1",
        "--micro-reversion-storage-capacity-status",
        str(capacity_path),
        "--micro-reversion-provider-budget-ledger",
        str(budget_ledger_path),
        "--micro-reversion-provider-budget-summary",
        str(budget_summary_path),
        *_provider_authority_cli_args(
            monkeypatch=monkeypatch,
            target_date="2026-08-14",
            pricing_path=pricing_path,
            pricing_payload=pricing_payload,
            ledger_path=budget_ledger_path,
            summary_path=budget_summary_path,
        ),
    ]

    assert quality.main(cli_args) == 0

    printed = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert printed["status"] == "offline_three_arm_execution_complete"
    assert written["result_count"] == 3
    assert written["provider_call_performed"] is True
    assert budget_ledger_path.exists()
    assert budget_summary_path.exists()
    assert json.loads(outcome_companion_path.read_text(encoding="utf-8"))[
        "artifact_content_sha256"
    ]
    assert written["runtime_effect"] is False
    assert written["actual_order_submitted"] is False
    checkpoint_path = output_path.with_name(f"{output_path.stem}.checkpoint.json")
    assert not checkpoint_path.exists()
    assert not quality._micro_reversion_checkpoint_record_dir(checkpoint_path).exists()
    assert len(provider_request_ids) == 3

    compressed_output_path = output_path.with_name(f"{output_path.name}.gz")
    with (
        output_path.open("rb") as source,
        gzip.open(compressed_output_path, "wb") as target,
    ):
        target.write(source.read())
    output_path.unlink()

    assert quality.main(cli_args) == 0

    resumed_printed = json.loads(capsys.readouterr().out)
    assert resumed_printed["status"] == "offline_three_arm_execution_complete"
    assert resumed_printed["artifact_path"] == str(compressed_output_path)
    assert len(provider_request_ids) == 3
    assert compressed_output_path.exists()
    assert not output_path.exists()

    checkpoint_record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256=(
            quality._micro_reversion_materialized_request_census_sha256(materialized)
        ),
        sequence=1,
        previous_record_sha256=None,
        result=written["results"][0],
    )
    quality._write_micro_reversion_checkpoint_record(
        checkpoint_path,
        checkpoint_record,
    )
    output_path.write_text('{"conflicting_plain_result":true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="json_artifact_plain_gzip_conflict"):
        quality.main(cli_args)

    assert output_path.exists()
    assert compressed_output_path.exists()
    assert len(provider_request_ids) == 3


def test_micro_reversion_direct_execute_serializes_and_reuses_terminal_report(
    tmp_path,
    monkeypatch,
):
    """Two exact executors publish one call census and one terminal winner."""

    target_date = "2026-08-14"
    _freeze_quality_clock(monkeypatch, target_date=target_date)
    monkeypatch.setattr(
        quality,
        "MICRO_REVERSION_PROVIDER_RESPONSE_CHAIN_ACTIVATION_DATE",
        target_date,
    )
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    materialized_path = tmp_path / "materialized.json"
    bridge_path = tmp_path / "bridge.json"
    output_path = tmp_path / "execution.json"
    capacity_path = tmp_path / "capacity.json"
    outcome_path = tmp_path / "outcomes.json"
    raw_pricing_path = tmp_path / "provider-pricing-source.txt"
    raw_pricing_bytes = b"reviewed concurrent direct pricing source\n"
    raw_pricing_path.write_bytes(raw_pricing_bytes)
    pricing_path = tmp_path / "provider-pricing.json"
    pricing_payload = {
        "schema": PRICING_ARTIFACT_SCHEMA,
        "artifact_id": "provider-pricing-concurrent-direct-v1",
        "review_status": "reviewed",
        "reviewed_at": f"{target_date}T18:00:00+09:00",
        "effective_from": target_date,
        "effective_to": target_date,
        "pricing_basis": "provider_public_rate",
        "raw_pricing_source_path": raw_pricing_path.name,
        "raw_pricing_source_bytes_sha256": hashlib.sha256(
            raw_pricing_bytes
        ).hexdigest(),
        "raw_pricing_source_size_bytes": len(raw_pricing_bytes),
        "prices": [
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "10",
            }
        ],
        "decision_authority": PRICING_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    pricing_payload["artifact_content_sha256"] = pricing_artifact_content_sha256(
        pricing_payload
    )
    pricing_path.write_text(json.dumps(pricing_payload), encoding="utf-8")
    materialized_path.write_text(json.dumps(materialized), encoding="utf-8")
    bridge_path.write_text(json.dumps(bridge_report), encoding="utf-8")
    budget_ledger_path = tmp_path / "provider-budget.jsonl"
    budget_summary_path = tmp_path / "provider-budget-summary.json"
    monkeypatch.setattr(quality, "_offline_openai_api_keys", lambda: ["test-key"])
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _target_date: output_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_action_neutral_label_path",
        lambda _target_date: outcome_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date=target_date,
            capacity_path=capacity_path,
        ),
    )
    process_context = multiprocessing.get_context("fork")
    provider_call_count = process_context.Value("i", 0)
    provider_call_lock = process_context.Lock()
    original_openai_runner = quality.execute_openai_prompt_v2_candidate

    def concurrent_openai_runner(
        request,
        *,
        api_keys=None,
        timeout_sec=45.0,
        _request_projection_only=False,
    ):
        if _request_projection_only:
            return original_openai_runner(
                request,
                _request_projection_only=True,
            )
        assert api_keys == ["test-key"]
        assert timeout_sec == 45.0
        with provider_call_lock:
            provider_call_count.value += 1
        time.sleep(0.05)
        response = _tamper_evident_openai_runner(request)
        response["provider_provenance"].update(
            {"input_tokens": 120, "output_tokens": 30}
        )
        return response

    monkeypatch.setattr(
        quality,
        "execute_openai_prompt_v2_candidate",
        concurrent_openai_runner,
    )
    cli_args = [
        "--date",
        target_date,
        "--mode",
        "micro_reversion_execute",
        "--micro-reversion-materialized-requests",
        str(materialized_path),
        "--micro-reversion-bridge-report",
        str(bridge_path),
        "--execute-candidate",
        "--write",
        "--candidate-max-new-requests",
        "3",
        "--micro-reversion-provider-pricing",
        str(pricing_path),
        "--micro-reversion-provider-daily-attempt-cap",
        "12",
        "--micro-reversion-provider-daily-usd-cap",
        "1",
        "--micro-reversion-storage-capacity-status",
        str(capacity_path),
        "--micro-reversion-provider-budget-ledger",
        str(budget_ledger_path),
        "--micro-reversion-provider-budget-summary",
        str(budget_summary_path),
        *_provider_authority_cli_args(
            monkeypatch=monkeypatch,
            target_date=target_date,
            pricing_path=pricing_path,
            pricing_payload=pricing_payload,
            ledger_path=budget_ledger_path,
            summary_path=budget_summary_path,
        ),
    ]
    ready_queue = process_context.Queue()
    result_queue = process_context.Queue()
    start_event = process_context.Event()
    processes = [
        process_context.Process(
            target=_micro_reversion_direct_execute_worker,
            args=(cli_args, ready_queue, start_event, result_queue),
        )
        for _ in range(2)
    ]
    for process in processes:
        process.start()
    outcomes = []
    try:
        assert [ready_queue.get(timeout=10) for _ in processes] == ["ready", "ready"]
        start_event.set()
        outcomes = [result_queue.get(timeout=30) for _ in processes]
    finally:
        start_event.set()
        for process in processes:
            process.join(timeout=30)
            if process.is_alive():  # pragma: no cover - failure cleanup
                process.terminate()
                process.join(timeout=10)

    assert sorted(outcomes) == [("ok", 0), ("ok", 0)]
    assert all(process.exitcode == 0 for process in processes)
    assert provider_call_count.value == 3
    terminal = json.loads(output_path.read_text(encoding="utf-8"))
    assert terminal["status"] == "offline_three_arm_execution_complete"
    assert terminal["candidate_model_call_attempted"] is True
    assert terminal["provider_call_performed"] is True
    assert terminal["new_result_count"] == 3
    assert len(terminal["new_result_ids"]) == 3
    assert terminal["report_content_sha256"] == quality._sha256(
        {
            key: value
            for key, value in terminal.items()
            if key != "report_content_sha256"
        }
    )
    checkpoint = quality._load_micro_reversion_checkpoint(
        quality.micro_reversion_execution_checkpoint_path(target_date)
    )
    assert checkpoint["checkpoint_record_count"] == 3
    assert [row["result_id"] for row in checkpoint["results"]] == terminal["result_ids"]


def test_micro_reversion_cli_ignores_unselected_openai_credentials_for_bedrock_batch(
    tmp_path, monkeypatch, capsys
):
    _freeze_quality_clock(monkeypatch, target_date="2026-08-14")
    from src.engine.scalping import ai_stage_coverage_replay

    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    future_openai_requests = deepcopy(materialized["requests"])
    future_parent_id = "future-openai-parent"
    future_label_id = "future-openai-trace:v1"
    for request in future_openai_requests:
        request["paired_replay_parent_id"] = future_parent_id
        request["paired_replay_id"] = (
            f"{future_parent_id}:{request['micro_reversion_replay_arm']}"
        )
        request["decision_trace_id"] = prepared[0]["decision_trace_id"]
        request["outcome_join_key"] = future_label_id
    for request in materialized["requests"]:
        candidate = request["candidate"]
        candidate["provider"] = "bedrock_test"
        candidate["response_schema_application"] = (
            "local_expected_only_not_sent_to_bedrock"
        )
        candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    materialized["requests"].extend(future_openai_requests)
    _reseal_current_materialized_report(materialized)
    outcome_artifact = _current_outcome_artifact_for_materialized(materialized)
    materialized_path = tmp_path / "materialized.json"
    outcome_path = tmp_path / "outcomes.json"
    output_path = tmp_path / "execution.json"
    capacity_path = tmp_path / "capacity.json"
    materialized_path.write_text(json.dumps(materialized), encoding="utf-8")
    outcome_path.write_text(json.dumps(outcome_artifact), encoding="utf-8")
    raw_pricing_path = tmp_path / "provider-pricing-source.txt"
    raw_pricing_bytes = b"reviewed mixed provider test pricing source\n"
    raw_pricing_path.write_bytes(raw_pricing_bytes)
    pricing_path = tmp_path / "provider-pricing.json"
    pricing_payload = {
        "schema": PRICING_ARTIFACT_SCHEMA,
        "artifact_id": "provider-pricing-mixed-test-v1",
        "review_status": "reviewed",
        "reviewed_at": "2026-08-14T18:00:00+09:00",
        "effective_from": "2026-08-14",
        "effective_to": "2026-08-14",
        "pricing_basis": "provider_public_rate",
        "raw_pricing_source_path": raw_pricing_path.name,
        "raw_pricing_source_bytes_sha256": hashlib.sha256(
            raw_pricing_bytes
        ).hexdigest(),
        "raw_pricing_source_size_bytes": len(raw_pricing_bytes),
        "prices": [
            {
                "provider": provider,
                "model": "gpt-test",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "10",
            }
            for provider in ("bedrock_test", "openai")
        ],
        "decision_authority": PRICING_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    pricing_payload["artifact_content_sha256"] = pricing_artifact_content_sha256(
        pricing_payload
    )
    pricing_path.write_text(json.dumps(pricing_payload), encoding="utf-8")
    key_checks: list[bool] = []
    bedrock_calls: list[str] = []
    monkeypatch.setattr(
        quality,
        "_offline_openai_api_keys",
        lambda: key_checks.append(True) or [],
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_execution_result_path",
        lambda _target_date: output_path,
    )
    monkeypatch.setattr(
        quality,
        "micro_reversion_storage_capacity_status_path",
        lambda _target_date: capacity_path,
    )
    monkeypatch.setattr(
        quality,
        "_micro_reversion_large_artifact_capacity_gate",
        lambda **_kwargs: _healthy_capacity_gate(
            target_date="2026-08-14",
            capacity_path=capacity_path,
        ),
    )
    original_exclusion = quality._micro_reversion_executor_exclusion
    monkeypatch.setattr(
        quality,
        "_micro_reversion_executor_exclusion",
        lambda request, **_kwargs: (
            None
            if str((request.get("candidate") or {}).get("provider") or "")
            == "bedrock_test"
            else original_exclusion(request)
        ),
    )

    def fake_bedrock_runner(request):
        bedrock_calls.append(str(request["paired_replay_id"]))
        candidate = request["candidate"]
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "bedrock_test",
                "model": candidate["model"],
                "transport": "bedrock_runtime_offline",
                "source_transport_contract": candidate["transport"],
                "response_id": f"response-{request['paired_replay_id']}",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
                "input_tokens": 120,
                "output_tokens": 30,
            },
        }

    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "execute_bedrock_candidate_single_network_attempt",
        fake_bedrock_runner,
    )

    rc = quality.main(
        [
            "--date",
            "2026-08-14",
            "--mode",
            "micro_reversion_execute",
            "--micro-reversion-materialized-requests",
            str(materialized_path),
            "--micro-reversion-outcome-labels",
            str(outcome_path),
            "--execute-candidate",
            "--write",
            "--candidate-max-new-requests",
            "3",
            "--micro-reversion-provider-pricing",
            str(pricing_path),
            "--micro-reversion-provider-daily-attempt-cap",
            "12",
            "--micro-reversion-provider-daily-usd-cap",
            "1",
            "--micro-reversion-storage-capacity-status",
            str(capacity_path),
            "--micro-reversion-provider-budget-ledger",
            str(tmp_path / "provider-budget.jsonl"),
            "--micro-reversion-provider-budget-summary",
            str(tmp_path / "provider-budget-summary.json"),
            *_provider_authority_cli_args(
                monkeypatch=monkeypatch,
                target_date="2026-08-14",
                pricing_path=pricing_path,
                pricing_payload=pricing_payload,
                ledger_path=tmp_path / "provider-budget.jsonl",
                summary_path=tmp_path / "provider-budget-summary.json",
            ),
        ]
    )

    assert rc == 0
    assert len(bedrock_calls) == 3
    assert key_checks == []
    assert json.loads(capsys.readouterr().out)["status"] == (
        "offline_three_arm_execution_batch_complete"
    )
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["result_count"] == 3
    assert written["deferred_request_count"] == 3


def test_micro_reversion_execute_cli_rejects_explicit_parallel_workers(
    tmp_path,
):
    materialized_path = tmp_path / "materialized.json"
    materialized_path.write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit, match="2"):
        quality.main(
            [
                "--date",
                "2026-08-14",
                "--mode",
                "micro_reversion_execute",
                "--micro-reversion-materialized-requests",
                str(materialized_path),
                "--execute-candidate",
                "--write",
                "--candidate-max-new-requests",
                "1",
                "--candidate-workers",
                "2",
            ]
        )


def test_micro_reversion_execute_cli_rejects_no_write_before_provider_call(
    tmp_path, monkeypatch
):
    materialized_path = tmp_path / "materialized.json"
    materialized_path.write_text("{}", encoding="utf-8")
    provider_called = False

    def forbidden_provider(*_args, **_kwargs):
        nonlocal provider_called
        provider_called = True
        raise AssertionError("provider call must be blocked before durable write")

    monkeypatch.setattr(
        quality,
        "execute_openai_prompt_v2_candidate",
        forbidden_provider,
    )

    with pytest.raises(SystemExit, match="2"):
        quality.main(
            [
                "--date",
                "2026-08-25",
                "--mode",
                "micro_reversion_execute",
                "--micro-reversion-materialized-requests",
                str(materialized_path),
                "--execute-candidate",
                "--candidate-max-new-requests",
                "3",
            ]
        )

    assert provider_called is False


def _valid_micro_reversion_entry_response():
    return {
        "edge_state": "EDGE",
        "action": "WAIT",
        "expected_upside_pct": 1.2,
        "expected_downside_pct": -0.5,
        "confidence": 70,
        "reason_codes": ["recovery_trigger_required"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "supportive",
            "tape": "mixed",
            "risk": "low",
            "uncertainty": "low",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "low",
            "trigger": "recovery_required",
        },
    }


def _tamper_evident_openai_runner(request, response=None, *, raw_text=None):
    response = _valid_micro_reversion_entry_response() if response is None else response
    raw_bytes = (
        raw_text.encode("utf-8")
        if raw_text is not None
        else json.dumps(
            response,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    if raw_text is None:
        parsed_response = response
        parse_status = "pass"
    else:
        try:
            parsed_response = json.loads(raw_text)
        except ValueError:
            parsed_response = None
            parse_status = "candidate_response_json_invalid"
        else:
            parse_status = "pass"
        if parse_status == "pass" and not isinstance(parsed_response, dict):
            parsed_response = None
            parse_status = "candidate_response_not_object"
    candidate = request["candidate"]
    declared_schema = candidate.get("response_schema")
    if isinstance(declared_schema, dict) and (
        candidate.get("semantic_validator_version")
        != quality.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
    ):
        response_schema = declared_schema
    else:
        response_schema = quality._candidate_openai_schema(
            stage=request["stage"],
            candidate=candidate,
            setup_evidence=request.get("entry_setup_evidence"),
        )
    schema_instance_sha256 = candidate.get(
        "response_schema_instance_sha256"
    ) or quality._sha256(response_schema)
    response_id = f"response-{request['paired_replay_id']}"
    projection = quality.execute_openai_prompt_v2_candidate(
        request,
        _request_projection_only=True,
    )["provider_request_projection"]
    receipt_content = {
        "schema": quality.MICRO_REVERSION_OPENAI_ATTEMPT_RECEIPT_SCHEMA,
        "paired_replay_parent_id": request.get("paired_replay_parent_id"),
        "paired_replay_id": request["paired_replay_id"],
        "micro_reversion_replay_arm": request.get("micro_reversion_replay_arm"),
        "candidate_input_sha256": request.get("candidate_input_sha256"),
        "candidate_contract_sha256": candidate["contract_sha256"],
        "offline_provider_attempt_number": request["offline_provider_attempt_number"],
        "provider": "openai",
        "model": candidate["model"],
        "response_id": response_id,
        "provider_output_projection": "openai_output_text",
        "provider_output_encoding": "utf-8+base64",
        "provider_output_bytes_b64": base64.b64encode(raw_bytes).decode("ascii"),
        "provider_output_size_bytes": len(raw_bytes),
        "provider_output_bytes_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "parse_transform_version": (
            quality.MICRO_REVERSION_OPENAI_PARSE_TRANSFORM_VERSION
        ),
        "parse_status": parse_status,
        "parsed_candidate_payload": parsed_response,
        "parsed_candidate_payload_sha256": (
            quality._sha256(parsed_response)
            if isinstance(parsed_response, dict)
            else None
        ),
        "response_schema_instance_sha256": schema_instance_sha256,
        "provider_request_projection": projection,
        "provider_request_projection_sha256": quality._sha256(projection),
    }
    return {
        "candidate_response": parsed_response or {},
        "provider_attempt_receipt": {
            **receipt_content,
            "attempt_receipt_content_sha256": quality._sha256(receipt_content),
        },
        "provider_provenance": {
            "provider": "openai",
            "model": candidate["model"],
            "transport": "openai_responses_http_offline",
            "source_transport_contract": candidate["transport"],
            "response_id": response_id,
            "response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "provider_request_projection_sha256": quality._sha256(projection),
            "provider_none": False,
            "provider_call_attempted": True,
            "provider_call_succeeded": True,
        },
    }


def _reseal_current_candidate_attempt_chain(request, replay_result):
    previous_hash = None
    selected_attempt = None
    for attempt in replay_result["candidate_attempts"]:
        attempt["previous_attempt_content_sha256"] = previous_hash
        attempt["attempt_content_sha256"] = quality._sha256(
            {
                key: value
                for key, value in attempt.items()
                if key != "attempt_content_sha256"
            }
        )
        previous_hash = attempt["attempt_content_sha256"]
        if attempt["status"] == "pass":
            selected_attempt = attempt
    assert selected_attempt is not None
    selected_hash = selected_attempt["attempt_content_sha256"]
    replay_result["candidate_attempt_chain_head_sha256"] = previous_hash
    replay_result["candidate_selected_attempt_number"] = selected_attempt[
        "attempt_number"
    ]
    replay_result["candidate_selected_attempt_content_sha256"] = selected_hash
    replay_result["candidate_selected_payload_content_sha256"] = quality._sha256(
        selected_attempt["parsed_candidate_response"]
    )
    assert replay_result["candidate_transform_chain"] == []
    replay_result["candidate_transform_chain_head_sha256"] = selected_hash
    response_chain_content = {
        "chain_version": quality.MICRO_REVERSION_CANDIDATE_RESPONSE_CHAIN_VERSION,
        "paired_replay_id": request["paired_replay_id"],
        "candidate_input_sha256": request["candidate_input_sha256"],
        "candidate_contract_sha256": request["candidate"]["contract_sha256"],
        "selected_attempt_content_sha256": selected_hash,
        "transform_chain_head_sha256": selected_hash,
        "final_candidate_response_content_sha256": replay_result[
            "candidate_response_content_sha256"
        ],
    }
    replay_result["candidate_response_chain_content_sha256"] = quality._sha256(
        response_chain_content
    )


def test_current_openai_retry_request_projection_rejects_fully_resealed_prompt_drift():
    _, materialized, _ = _micro_reversion_action_neutral_bridge_fixture()
    request = materialized["requests"][0]

    def retry_runner(attempt_request):
        return _tamper_evident_openai_runner(
            attempt_request,
            response=(
                {}
                if attempt_request["offline_provider_attempt_number"] == 1
                else _valid_micro_reversion_entry_response()
            ),
        )

    replay_result = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "DROP"},
        candidate_runner=retry_runner,
        require_tamper_evident_candidate_chain=True,
    )[0]
    assert replay_result["status"] == "pass"
    assert len(replay_result["candidate_attempts"]) == 2
    assert (
        replay_result["candidate_attempts"][1]["provider_attempt_receipt"][
            "provider_request_projection"
        ]["schema_correction_errors"]
        == replay_result["candidate_attempts"][0]["schema_errors"]
    )

    tampered = deepcopy(replay_result)
    attempt = tampered["candidate_attempts"][1]
    receipt = attempt["provider_attempt_receipt"]
    projection = receipt["provider_request_projection"]
    attacker_prompt = "Attacker-selected retry prompt. Return the valid object."
    projection["system_instructions"] = quality._provider_request_text_commitment(
        attacker_prompt
    )
    projection_hash = quality._sha256(projection)
    receipt["provider_request_projection_sha256"] = projection_hash
    receipt["attempt_receipt_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in receipt.items()
            if key != "attempt_receipt_content_sha256"
        }
    )
    attempt["provider_provenance"][
        "provider_request_projection_sha256"
    ] = projection_hash
    _reseal_current_candidate_attempt_chain(request, tampered)

    with pytest.raises(
        ValueError,
        match="micro_reversion_openai_attempt_receipt_request_projection_mismatch",
    ):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=request,
            replay_result=tampered,
        )


def test_current_openai_response_chain_replays_raw_bytes_and_rejects_resealed_final(
    tmp_path, monkeypatch
):
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )
    monkeypatch.setattr(
        quality,
        "MICRO_REVERSION_PROVIDER_RESPONSE_CHAIN_ACTIVATION_DATE",
        "2026-08-14",
    )
    checkpoint_path = tmp_path / "current-response-chain.checkpoint.json"

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        source_bridge_report=bridge_report,
        execute_candidate=True,
        candidate_runner=_tamper_evident_openai_runner,
        max_new_requests=3,
        checkpoint_callback=lambda record: (
            quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
        ),
    )

    assert report["status"] == "offline_three_arm_execution_complete"
    for result, request in zip(report["results"], materialized["requests"]):
        replay_result = result["replay_result"]
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=request,
            replay_result=replay_result,
        )
        assert replay_result["candidate_semantic_repairs"] == []
        assert replay_result["candidate_transform_chain"] == []

    request = materialized["requests"][0]
    tampered = deepcopy(report["results"][0]["replay_result"])
    tampered["candidate_response"]["action"] = "DROP"
    final_hash = quality._sha256(tampered["candidate_response"])
    tampered["candidate_response_content_sha256"] = final_hash
    chain_content = {
        "chain_version": quality.MICRO_REVERSION_CANDIDATE_RESPONSE_CHAIN_VERSION,
        "paired_replay_id": request["paired_replay_id"],
        "candidate_input_sha256": request["candidate_input_sha256"],
        "candidate_contract_sha256": request["candidate"]["contract_sha256"],
        "selected_attempt_content_sha256": tampered[
            "candidate_selected_attempt_content_sha256"
        ],
        "transform_chain_head_sha256": tampered[
            "candidate_transform_chain_head_sha256"
        ],
        "final_candidate_response_content_sha256": final_hash,
    }
    tampered["candidate_response_chain_content_sha256"] = quality._sha256(chain_content)

    with pytest.raises(
        ValueError,
        match="micro_reversion_current_direct_response_binding_mismatch",
    ):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=request,
            replay_result=tampered,
        )


def test_current_openai_invalid_json_attempts_retain_raw_receipt_chain():
    _, materialized, _ = _micro_reversion_action_neutral_bridge_fixture()
    request = materialized["requests"][0]

    result = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "DROP"},
        candidate_runner=lambda attempt_request: _tamper_evident_openai_runner(
            attempt_request,
            raw_text="not-json",
        ),
        require_tamper_evident_candidate_chain=True,
    )[0]

    assert result["status"] == "schema_rejected"
    assert len(result["candidate_attempts"]) == quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS
    assert all(
        attempt["provider_attempt_receipt"]["parse_status"]
        == "candidate_response_json_invalid"
        and attempt["parsed_candidate_response"] is None
        and attempt["status"] == "schema_rejected"
        for attempt in result["candidate_attempts"]
    )
    assert (
        result["candidate_attempt_chain_head_sha256"]
        == result["candidate_attempts"][-1]["attempt_content_sha256"]
    )


@pytest.mark.parametrize(
    ("stage", "endpoint"),
    (("holding", "holding_flow"), ("exit", "exit")),
)
def test_current_bedrock_lifecycle_parent_chain_uses_single_calls_and_rejects_reseal(
    monkeypatch, stage, endpoint
):
    from src.engine.bedrock_nova_provider import (
        BedrockNovaModelProfile,
        BedrockNovaResult,
    )
    from src.engine.scalping import ai_stage_coverage_replay

    response = {
        **_valid_micro_reversion_entry_response(),
        "action": "HOLD",
    }
    response_schema = quality._prompt_v2_openai_schema("holding")
    prompt = "Review the frozen holding lifecycle input. Return JSON only."
    candidate = {
        "provider": "bedrock",
        "model": "nova_lite_v2",
        "transport": "bedrock_converse_offline",
        "prompt_version": "current_holding_candidate_v1",
        "system_prompt": prompt,
        "system_prompt_sha256": quality._sha256(prompt),
        "response_schema": response_schema,
        "response_schema_sha256": quality._sha256(response_schema),
        "schema_name": "current_holding_candidate_v1",
        "require_json": True,
        "max_output_tokens": 768,
        "semantic_validator_version": (
            quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
        ),
    }
    bedrock_request_profile = {
        "schema": quality.MICRO_REVERSION_BEDROCK_REQUEST_PROFILE_SCHEMA,
        "family": "lite_v2",
        "model_id": "test.nova-lite-v2",
        "region_name": "ap-northeast-2",
        "max_output_tokens": 768,
        "temperature": 0,
        "timeout_ms": 5_000,
        "prompt_cache_enabled": False,
    }
    candidate["bedrock_request_profile"] = bedrock_request_profile
    candidate["bedrock_request_profile_sha256"] = quality._sha256(
        bedrock_request_profile
    )
    candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    exact_payload = {"holding": {"position_qty": 10}}
    candidate_input = {"exact_payload": exact_payload}
    parent_id = f"current-bedrock-{stage}-parent"
    requests = [
        {
            "paired_replay_parent_id": parent_id,
            "paired_replay_id": f"{parent_id}:{arm}",
            "micro_reversion_replay_arm": arm,
            "ablation_design_version": quality.CURRENT_DESIGN_VERSION,
            "decision_trace_id": f"current-bedrock-{stage}-trace",
            "stage": stage,
            "endpoint": endpoint,
            "payload_sha256": quality._sha256(exact_payload),
            "source_exact_payload_sha256": quality._sha256(exact_payload),
            "exact_payload": exact_payload,
            "candidate_input": candidate_input,
            "candidate_input_sha256": quality._sha256(candidate_input),
            "candidate": deepcopy(candidate),
            **quality.OFFLINE_CONTRACT,
        }
        for arm in quality.arm_set_for_design(quality.CURRENT_DESIGN_VERSION)
    ]
    profile = BedrockNovaModelProfile(
        family="lite_v2",
        model_id="test.nova-lite-v2",
        region_name="ap-northeast-2",
        max_output_tokens=768,
        timeout_ms=5_000,
        prompt_cache_enabled=False,
        input_usd_per_1m=0.0,
        output_usd_per_1m=0.0,
        cache_read_input_usd_per_1m=0.0,
        cache_write_input_usd_per_1m=0.0,
    )
    raw_text = json.dumps(response, sort_keys=True, separators=(",", ":"))
    calls = []
    rotation_flags = []

    class FakeProvider:
        def __init__(self, *, key_rotation_enabled=True):
            rotation_flags.append(key_rotation_enabled)

        def converse(self, *, prompt, user_input, profile):
            calls.append((prompt, user_input, profile.family))
            return BedrockNovaResult(
                payload=deepcopy(response),
                raw_text=raw_text,
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=10,
                input_tokens=100,
                output_tokens=30,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=100,
                estimated_cost_usd=0.0,
                attempted_key_count=1,
                response_id=f"bedrock-response-{len(calls)}",
            )

    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "lite_v2_profile_from_env",
        lambda: profile,
    )
    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "BedrockNovaProvider",
        FakeProvider,
    )

    model_drift_profile = BedrockNovaModelProfile(
        **{
            **profile.__dict__,
            "model_id": "attacker.overridden-model",
        }
    )
    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "lite_v2_profile_from_env",
        lambda: model_drift_profile,
    )
    with pytest.raises(
        ValueError,
        match="micro_reversion_bedrock_selected_profile_drift",
    ):
        ai_stage_coverage_replay.execute_bedrock_candidate_single_network_attempt(
            {**requests[0], "offline_provider_attempt_number": 1}
        )
    lower_token_profile = BedrockNovaModelProfile(
        **{
            **profile.__dict__,
            "max_output_tokens": 767,
        }
    )
    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "lite_v2_profile_from_env",
        lambda: lower_token_profile,
    )
    with pytest.raises(
        ValueError,
        match="bedrock_budgeted_profile_output_tokens_drift",
    ):
        ai_stage_coverage_replay.execute_bedrock_candidate_single_network_attempt(
            {**requests[0], "offline_provider_attempt_number": 1}
        )
    assert calls == []
    rotation_flags.clear()
    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "lite_v2_profile_from_env",
        lambda: profile,
    )

    results = quality.run_paired_replay(
        requests,
        control_runner=lambda _request: {"action": "HOLD"},
        candidate_runner=(
            ai_stage_coverage_replay.execute_bedrock_candidate_single_network_attempt
        ),
        require_tamper_evident_candidate_chain=True,
    )

    assert len(calls) == 3
    assert rotation_flags == [False, False, False]
    assert {result["status"] for result in results} == {"pass"}
    for request, result in zip(requests, results):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=request,
            replay_result=result,
        )
        receipt = result["candidate_attempts"][0]["provider_attempt_receipt"]
        assert (
            receipt["provider_output_bytes_sha256"]
            == hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        )

    resealed_profile_drift = deepcopy(results[0])
    drift_attempt = resealed_profile_drift["candidate_attempts"][0]
    drift_receipt = drift_attempt["provider_attempt_receipt"]
    drift_receipt["model_id"] = "attacker.resealed-model"
    drift_receipt["region_name"] = "us-east-1"
    drift_receipt["attempt_receipt_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in drift_receipt.items()
            if key != "attempt_receipt_content_sha256"
        }
    )
    drift_provenance = drift_attempt["provider_provenance"]
    drift_provenance["model_id"] = drift_receipt["model_id"]
    drift_provenance["bedrock_model_id"] = drift_receipt["model_id"]
    drift_provenance["bedrock_region_name"] = drift_receipt["region_name"]
    _reseal_current_candidate_attempt_chain(requests[0], resealed_profile_drift)
    with pytest.raises(
        ValueError,
        match="micro_reversion_bedrock_attempt_receipt_binding_mismatch",
    ):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=requests[0],
            replay_result=resealed_profile_drift,
        )

    class RetryProvider:
        attempt_count = 0

        def __init__(self, *, key_rotation_enabled=True):
            assert key_rotation_enabled is False

        def converse(self, *, prompt, user_input, profile):
            type(self).attempt_count += 1
            valid = type(self).attempt_count == 2
            retry_raw_text = raw_text if valid else "not-json"
            return BedrockNovaResult(
                payload=deepcopy(response) if valid else {},
                raw_text=retry_raw_text,
                parse_ok=valid,
                parse_error="" if valid else "JSONDecodeError",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=10,
                input_tokens=10,
                output_tokens=2,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=10,
                estimated_cost_usd=0.0,
                attempted_key_count=1,
                response_id=f"bedrock-retry-{type(self).attempt_count}",
            )

    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "BedrockNovaProvider",
        RetryProvider,
    )
    retry_result = quality.run_paired_replay(
        [requests[0]],
        control_runner=lambda _request: {"action": "HOLD"},
        candidate_runner=(
            ai_stage_coverage_replay.execute_bedrock_candidate_single_network_attempt
        ),
        require_tamper_evident_candidate_chain=True,
    )[0]
    assert retry_result["status"] == "pass"
    assert len(retry_result["candidate_attempts"]) == 2
    tampered_retry = deepcopy(retry_result)
    retry_attempt = tampered_retry["candidate_attempts"][1]
    retry_receipt = retry_attempt["provider_attempt_receipt"]
    retry_projection = retry_receipt["provider_request_projection"]
    retry_projection["system_text"] = quality._provider_request_text_commitment(
        "Attacker-selected Bedrock retry system text."
    )
    retry_projection_hash = quality._sha256(retry_projection)
    retry_receipt["provider_request_projection_sha256"] = retry_projection_hash
    retry_receipt["attempt_receipt_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in retry_receipt.items()
            if key != "attempt_receipt_content_sha256"
        }
    )
    retry_attempt["provider_provenance"][
        "provider_request_projection_sha256"
    ] = retry_projection_hash
    _reseal_current_candidate_attempt_chain(requests[0], tampered_retry)
    with pytest.raises(
        ValueError,
        match="micro_reversion_bedrock_attempt_receipt_request_projection_mismatch",
    ):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=requests[0],
            replay_result=tampered_retry,
        )

    class InvalidJsonProvider:
        def __init__(self, *, key_rotation_enabled=True):
            assert key_rotation_enabled is False

        def converse(self, *, prompt, user_input, profile):
            return BedrockNovaResult(
                payload={},
                raw_text="not-json",
                parse_ok=False,
                parse_error="JSONDecodeError",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=10,
                input_tokens=10,
                output_tokens=2,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=10,
                estimated_cost_usd=0.0,
                attempted_key_count=1,
                response_id="bedrock-invalid-json",
            )

    monkeypatch.setattr(
        ai_stage_coverage_replay,
        "BedrockNovaProvider",
        InvalidJsonProvider,
    )
    invalid_result = quality.run_paired_replay(
        [requests[0]],
        control_runner=lambda _request: {"action": "HOLD"},
        candidate_runner=(
            ai_stage_coverage_replay.execute_bedrock_candidate_single_network_attempt
        ),
        require_tamper_evident_candidate_chain=True,
    )[0]
    assert invalid_result["status"] == "schema_rejected"
    assert len(invalid_result["candidate_attempts"]) == (
        quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS
    )
    assert all(
        attempt["provider_attempt_receipt"]["parse_status"] == "JSONDecodeError"
        and attempt["parsed_candidate_response"] is None
        for attempt in invalid_result["candidate_attempts"]
    )

    tampered = deepcopy(results[0])
    tampered["candidate_response"]["action"] = "TRIM"
    final_hash = quality._sha256(tampered["candidate_response"])
    tampered["candidate_response_content_sha256"] = final_hash
    chain_content = {
        "chain_version": quality.MICRO_REVERSION_CANDIDATE_RESPONSE_CHAIN_VERSION,
        "paired_replay_id": requests[0]["paired_replay_id"],
        "candidate_input_sha256": requests[0]["candidate_input_sha256"],
        "candidate_contract_sha256": candidate["contract_sha256"],
        "selected_attempt_content_sha256": tampered[
            "candidate_selected_attempt_content_sha256"
        ],
        "transform_chain_head_sha256": tampered[
            "candidate_transform_chain_head_sha256"
        ],
        "final_candidate_response_content_sha256": final_hash,
    }
    tampered["candidate_response_chain_content_sha256"] = quality._sha256(chain_content)
    with pytest.raises(
        ValueError,
        match="micro_reversion_current_direct_response_binding_mismatch",
    ):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=requests[0],
            replay_result=tampered,
        )


def test_current_checkpoint_companion_rejects_resealed_parent_to_deferred_attack(
    tmp_path, monkeypatch
):
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )
    monkeypatch.setattr(
        quality,
        "MICRO_REVERSION_PROVIDER_RESPONSE_CHAIN_ACTIVATION_DATE",
        "2026-08-14",
    )
    checkpoint_path = tmp_path / "current-parent-census.checkpoint.json"
    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        source_bridge_report=bridge_report,
        execute_candidate=True,
        candidate_runner=_tamper_evident_openai_runner,
        max_new_requests=3,
        checkpoint_callback=lambda record: (
            quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
        ),
    )
    checkpoint = quality._load_micro_reversion_checkpoint(checkpoint_path)
    labels = outcome_artifact["labels"]

    tampered = deepcopy(report)
    tampered["status"] = "offline_three_arm_execution_batch_complete"
    tampered["result_count"] = 0
    tampered["result_ids"] = []
    tampered["results"] = []
    tampered["new_result_count"] = 0
    tampered["new_result_ids"] = []
    tampered["committed_parent_count"] = 0
    tampered["newly_committed_parent_count"] = 0
    tampered["selected_parent_ids"] = []
    tampered["selected_request_ids"] = []
    tampered["deferred_request_count"] = len(materialized["requests"])
    tampered["deferred_request_ids"] = [
        request["paired_replay_id"] for request in materialized["requests"]
    ]
    evaluation = quality.build_micro_reversion_three_arm_evaluation(
        results=[],
        outcome_labels=labels,
        ablation_design_version=quality.CURRENT_DESIGN_VERSION,
    )
    tampered["three_arm_evaluation"] = {
        **evaluation,
        "evaluation_content_sha256": quality._sha256(evaluation),
    }
    tampered_without_hash = {
        key: value for key, value in tampered.items() if key != "report_content_sha256"
    }
    tampered["report_content_sha256"] = quality._sha256(tampered_without_hash)

    with pytest.raises(
        ValueError,
        match="micro_reversion_current_checkpoint_committed_census_mismatch",
    ):
        quality.validate_current_micro_reversion_checkpoint_companion(
            report=tampered,
            checkpoint_artifact=checkpoint,
            materialized_report=materialized,
            outcome_labels=labels,
        )


def test_current_entry_risk_composition_is_recomputed_from_selected_attempt():
    setup_evidence = quality.build_entry_setup_evidence(
        exact_payload={"current": {"price": 10_000}},
        exact_analysis={
            "schema": "exact_payload_analysis_v1",
            "source_quality": {
                "status": "fresh_consistent",
                "completed_bar_count": 20,
            },
            "executable_liquidity": {"execution_cost_state": "low"},
            "contradictions": ["multi_horizon_direction_conflict"],
            "deterministic_contract_facts": {
                "structural_edge_floor": True,
                "early_session_structural_edge_floor": False,
                "early_session_probe_candidate": False,
                "orderly_pullback_recovery": False,
                "trusted_supportive_trigger": True,
                "adverse_distribution_no_edge": False,
                "blocking_overextension": True,
                "ask_wall_wide_spread": False,
            },
        },
        recovery_analysis={
            "schema": "anticipatory_reversal_analysis_v1",
            "source_mode": "fresh_dual",
            "hard_blockers": [],
            "clean_continuation_probe": {"eligible": True},
            "recovery_confirmation_probe": {"eligible": False},
        },
    )
    risk_response = {
        "schema": "entry_setup_risk_adjudication_v1",
        "risk_verdict": "VETO",
        "risk_codes": ["OVEREXTENSION_CHASE"],
        "supporting_fact_ids": ["structural_edge_floor"],
        "contradicting_fact_ids": ["blocking_overextension"],
        "confidence": 80,
    }
    candidate = {
        "provider": "openai",
        "model": "gpt-test",
        "transport": "openai_responses_http_offline",
        "prompt_version": (
            f"{quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION}"
            "_entry"
        ),
        "semantic_validator_version": (
            quality.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
        ),
        "entry_decision_composer_version": quality.ENTRY_DECISION_COMPOSER_VERSION,
        "system_prompt": "Adjudicate the exact setup risk. Return JSON only.",
        "temperature": None,
        "reasoning_effort": None,
        "max_output_tokens": 512,
        "schema_name": "entry_setup_risk_adjudication_v1",
    }
    candidate["system_prompt_sha256"] = quality._sha256(candidate["system_prompt"])
    candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    request = {
        "paired_replay_parent_id": "risk-parent",
        "paired_replay_id": "risk-parent:arm",
        "micro_reversion_replay_arm": quality.arm_set_for_design(
            quality.CURRENT_DESIGN_VERSION
        )[2],
        "ablation_design_version": quality.CURRENT_DESIGN_VERSION,
        "decision_trace_id": "risk-trace",
        "stage": "entry",
        "payload_sha256": "risk-payload",
        "candidate_input_sha256": quality._sha256({"risk": "input"}),
        "entry_setup_evidence": setup_evidence,
        "control": {
            "provider": "openai",
            "model": "gpt-test",
            "reasoning_effort": None,
        },
        "candidate": candidate,
        **quality.OFFLINE_CONTRACT,
    }

    replay_result = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "WAIT"},
        candidate_runner=lambda attempt_request: _tamper_evident_openai_runner(
            attempt_request, risk_response
        ),
        require_tamper_evident_candidate_chain=True,
    )[0]

    assert replay_result["status"] == "pass"
    assert replay_result["candidate_risk_adjudication_response"] == risk_response
    assert replay_result["candidate_response"]["action"] == "DROP"
    assert len(replay_result["candidate_transform_chain"]) == 1
    quality.validate_current_micro_reversion_candidate_response_chain(
        request=request,
        replay_result=replay_result,
    )

    tampered = deepcopy(replay_result)
    tampered["candidate_response"]["action"] = "WAIT"
    with pytest.raises(
        ValueError,
        match="micro_reversion_current_composition_rebuild_mismatch",
    ):
        quality.validate_current_micro_reversion_candidate_response_chain(
            request=request,
            replay_result=tampered,
        )


def test_current_post_network_semantic_repair_is_fail_closed(tmp_path, monkeypatch):
    _, materialized, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    outcome_artifact = quality.build_micro_reversion_action_neutral_outcome_labels(
        bridge_report=bridge_report,
        materialized_report=materialized,
    )
    monkeypatch.setattr(
        quality,
        "MICRO_REVERSION_PROVIDER_RESPONSE_CHAIN_ACTIVATION_DATE",
        "2026-08-14",
    )
    checkpoint_path = tmp_path / "current-fail-closed.checkpoint.json"

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        execute_candidate=True,
        candidate_runner=lambda request: _tamper_evident_openai_runner(
            request, {"action": "INVALID"}
        ),
        max_new_requests=3,
        checkpoint_callback=lambda record: (
            quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
        ),
    )
    checkpoint = quality._load_micro_reversion_checkpoint(checkpoint_path)

    assert report["status"] == (
        "offline_three_arm_execution_complete_with_failures_or_exclusions"
    )
    assert report["result_count"] == 0
    assert checkpoint["checkpoint_record_count"] == 3
    for result in checkpoint["results"]:
        replay_result = result["replay_result"]
        assert replay_result["status"] == "schema_rejected"
        assert replay_result["candidate_semantic_repairs"] == []
        assert len(replay_result["candidate_attempts"]) == (
            quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS
        )
        assert {
            attempt["provider_provenance"]["provider"]
            for attempt in replay_result["candidate_attempts"]
        } == {"openai"}


def test_micro_reversion_execution_defaults_to_no_provider_calls():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    calls = []

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        candidate_runner=lambda request: calls.append(request),
    )

    assert report["status"] == "provider_execution_not_authorized"
    assert report["provider_call_performed"] is False
    assert report["candidate_model_call_attempted"] is False
    assert report["results"] == []
    assert calls == []
    assert all("exact_payload" not in row for row in report["request_refs"])
    assert all("requests" not in row for row in materialized["materializations"])


def test_current_micro_reversion_execution_revalidates_both_single_axes() -> None:
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )

    unrelated_feature = deepcopy(materialized)
    for request in unrelated_feature["requests"][1:]:
        request["candidate_input"]["unrelated_extra_feature"] = {"value": 1}
        request["candidate_input_sha256"] = quality._sha256(request["candidate_input"])
    _reseal_current_materialized_report(unrelated_feature)
    with pytest.raises(
        ValueError,
        match=(
            "micro_reversion_materialized_feature_only_delta_invalid|"
            "micro_reversion_execution_ask_binding_mismatch"
        ),
    ):
        quality.run_micro_reversion_materialized_requests(
            materialized_report=unrelated_feature
        )

    changed_execution_axis = deepcopy(materialized)
    candidate = changed_execution_axis["requests"][2]["candidate"]
    candidate["temperature"] = 0.25
    candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    _reseal_current_materialized_report(changed_execution_axis)
    with pytest.raises(
        ValueError,
        match=(
            "micro_reversion_materialized_prompt_only_delta_invalid|"
            "micro_reversion_execution_locked_contract_axis_mismatch"
        ),
    ):
        quality.run_micro_reversion_materialized_requests(
            materialized_report=changed_execution_axis
        )


def test_micro_reversion_execution_does_not_call_parent_without_outcome_label():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    calls = []
    unrelated_label = deepcopy(
        _current_outcome_artifact_for_materialized(materialized)["labels"][0]
    )
    unrelated_label["label_id"] = "unrelated-label"
    unrelated_label["label_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in unrelated_label.items()
            if key != "label_content_sha256"
        }
    )

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_labels=[unrelated_label],
        execute_candidate=True,
        candidate_runner=lambda request: calls.append(request),
        max_new_requests=3,
    )

    assert calls == []
    assert report["result_count"] == 0
    assert report["deferred_request_count"] == 3
    assert report["blocking_execution_exclusion_count"] == 0
    assert {row["reason"] for row in report["execution_exclusions"]} == {
        "action_neutral_outcome_label_missing_or_ambiguous"
    }


def test_micro_reversion_bedrock_holding_flow_is_explicitly_unsupported():
    request = {
        "stage": "holding",
        "endpoint": "holding_flow",
        "candidate": {
            "provider": "bedrock",
            "model": "nova_lite_v2",
        },
    }

    assert quality._micro_reversion_executor_exclusion(request) == (
        "bedrock_holding_flow_offline_executor_not_implemented"
    )
    assert quality._micro_reversion_executor_exclusion(
        request,
        strict_current_response_chain=True,
    ) == ("current_design_bedrock_request_profile_invalid")
    request_profile = {
        "schema": quality.MICRO_REVERSION_BEDROCK_REQUEST_PROFILE_SCHEMA,
        "family": "lite_v2",
        "model_id": "global.amazon.nova-2-lite-v1:0",
        "region_name": "ap-northeast-2",
        "max_output_tokens": 768,
        "temperature": 0,
        "timeout_ms": 7_000,
        "prompt_cache_enabled": False,
    }
    request["candidate"].update(
        {
            "max_output_tokens": 768,
            "bedrock_request_profile": request_profile,
            "bedrock_request_profile_sha256": quality._sha256(request_profile),
        }
    )
    assert (
        quality._micro_reversion_executor_exclusion(
            request,
            strict_current_response_chain=True,
        )
        is None
    )

    entry_price = deepcopy(request)
    entry_price.update({"stage": "entry_price", "endpoint": "entry_price"})
    entry_price["candidate"]["model"] = "qwen3_32b"
    assert quality._micro_reversion_executor_exclusion(
        entry_price,
        strict_current_response_chain=True,
    ) == ("current_design_bedrock_entry_price_replayable_transform_not_implemented")


def test_micro_reversion_execution_joins_one_outcome_after_three_arm_calls():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    calls = []

    def runner(request):
        calls.append(request["paired_replay_id"])
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": (request["candidate"]["transport"]),
                "response_id": "test-response-id",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
            },
        }

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_labels=_current_outcome_artifact_for_materialized(materialized)[
            "labels"
        ],
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=3,
    )

    assert report["status"] == "offline_three_arm_execution_complete"
    assert len(calls) == 3
    assert report["result_count"] == 3
    assert len(set(report["result_ids"])) == 3
    assert report["provider_call_performed"] is True
    assert report["provider_call_succeeded"] is True
    assert len(report["outcome_joins"]) == 1
    assert report["outcomes_embedded_in_provider_input"] is False
    assert all(row["replay_result"]["status"] == "pass" for row in report["results"])
    evaluation = report["three_arm_evaluation"]
    assert evaluation["complete_parent_count"] == 1
    assert evaluation["ablation_design_version"] == (
        "current_micro_vs_ask_depletion_prompt_v1"
    )
    assert evaluation["ablation_arms"] == [
        "replay_control_exact_plus_micro",
        "replay_control_exact_plus_micro_ask_depletion",
        "replay_candidate_exact_plus_micro_ask_depletion",
    ]
    assert [row["comparison_role"] for row in evaluation["comparisons"]] == [
        "ask_depletion_feature_effect",
        "prompt_contract_effect_conditional_on_ask_depletion",
    ]
    assert [row["changed_axis"] for row in evaluation["comparisons"]] == [
        "ask_liquidity_depletion_context_only",
        "prompt_and_response_contract_only",
    ]
    assert report["three_arm_evaluation"]["notional_net_profit_eligible"] is False


def test_current_holding_trim_keeps_parent_and_existing_position_exposure():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    label = _current_outcome_artifact_for_materialized(materialized)["labels"][0]
    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_labels=[label],
        execute_candidate=True,
        candidate_runner=_tamper_evident_openai_runner,
        max_new_requests=3,
    )
    results = deepcopy(report["results"])
    actions = ("TRIM", "HOLD", "EXIT")
    for result, action in zip(results, actions):
        result["stage"] = "holding"
        result["replay_result"]["stage"] = "holding"
        result["replay_result"]["candidate_response"]["action"] = action

    evaluation = quality.build_micro_reversion_three_arm_evaluation(
        results=results,
        outcome_labels=[label],
        ablation_design_version=quality.CURRENT_DESIGN_VERSION,
    )

    trim_arm = quality.arm_set_for_design(quality.CURRENT_DESIGN_VERSION)[0]
    assert evaluation["complete_parent_count"] == 1
    assert evaluation["excluded_parent_count"] == 0
    assert evaluation["exclusions"] == []
    trim_value = evaluation["rows"][0]["arms"][trim_arm]
    assert trim_value["action"] == "TRIM"
    assert trim_value["runtime_normalized_action"] == "HOLD"
    assert trim_value["exposure_role"] == "existing_position_exposure"
    assert trim_value["exposure_fraction"] == 1.0
    assert evaluation["arm_metrics"][trim_arm]["action_counts"] == {"TRIM": 1}


def test_micro_reversion_evaluation_excludes_mixed_design_parent_once() -> None:
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    label = _current_outcome_artifact_for_materialized(materialized)["labels"][0]

    def runner(request):
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": f"response-{request['paired_replay_id']}",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
            },
        }

    execution = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_labels=[label],
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=3,
    )
    mixed_parent_id = "mixed-design-parent"
    mixed_results = deepcopy(execution["results"])
    for result in mixed_results:
        result["paired_replay_parent_id"] = mixed_parent_id
    mixed_results[0]["ablation_design_version"] = "exact_no_micro_vs_micro_prompt_v1"

    evaluation = quality.build_micro_reversion_three_arm_evaluation(
        results=[*execution["results"], *mixed_results],
        outcome_labels=[label],
    )

    assert evaluation["complete_parent_count"] == 1
    assert {row["paired_replay_parent_id"] for row in evaluation["rows"]} == {
        execution["results"][0]["paired_replay_parent_id"]
    }
    assert evaluation["exclusions"] == [
        {
            "paired_replay_parent_id": mixed_parent_id,
            "reason": "ablation_design_invalid",
        }
    ]


def test_micro_reversion_execution_rejects_schema_valid_missing_provider_provenance():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_labels=_current_outcome_artifact_for_materialized(materialized)[
            "labels"
        ],
        execute_candidate=True,
        candidate_runner=lambda _request: {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {},
        },
        max_new_requests=3,
    )

    assert report["status"] == (
        "offline_three_arm_execution_complete_with_failures_or_exclusions"
    )
    assert report["provider_provenance_pass_count"] == 0
    assert report["provider_call_succeeded"] is False
    assert all(
        row["replay_result"]["status"] == "provider_provenance_rejected"
        for row in report["results"]
    )
    assert report["three_arm_evaluation"]["complete_parent_count"] == 0


def test_micro_reversion_execution_budget_never_slices_one_parent_arms():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    calls: list[str] = []

    def runner(request):
        calls.append(str(request["paired_replay_id"]))
        raise AssertionError("an incomplete A/B/C parent must not call a provider")

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_labels=_current_outcome_artifact_for_materialized(materialized)[
            "labels"
        ],
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=2,
    )

    assert calls == []
    assert report["result_count"] == 0
    assert report["deferred_request_count"] == 3
    assert report["status"] == (
        "offline_three_arm_execution_complete_with_failures_or_exclusions"
    )
    assert (
        quality._micro_reversion_execution_exit_code(
            report=report,
            execute_candidate=True,
        )
        == 2
    )


def test_micro_reversion_execution_commits_one_bounded_parent_per_batch():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    second_requests = deepcopy(materialized["requests"])
    second_parent_id = "micro-parent-second"
    second_label_id = "trace-materialize-2:v1"
    for request in second_requests:
        request["paired_replay_parent_id"] = second_parent_id
        request["paired_replay_id"] = (
            f"{second_parent_id}:{request['micro_reversion_replay_arm']}"
        )
        request["decision_trace_id"] = prepared[0]["decision_trace_id"]
        request["outcome_join_key"] = second_label_id
    materialized["requests"].extend(second_requests)
    _reseal_current_materialized_report(materialized)
    outcome_artifact = _current_outcome_artifact_for_materialized(materialized)
    calls: list[str] = []

    def runner(request):
        calls.append(str(request["paired_replay_id"]))
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": f"response-{request['paired_replay_id']}",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
            },
        }

    first_batch = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=3,
    )

    assert len(calls) == 3
    assert first_batch["status"] == "offline_three_arm_execution_batch_complete"
    assert first_batch["committed_parent_count"] == 1
    assert first_batch["newly_committed_parent_count"] == 1
    assert first_batch["result_count"] == 3
    assert first_batch["deferred_request_count"] == 3
    assert first_batch["three_arm_evaluation"]["complete_parent_count"] == 1
    assert (
        quality._micro_reversion_execution_exit_code(
            report=first_batch,
            execute_candidate=True,
        )
        == 0
    )

    calls.clear()
    second_batch = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        execute_candidate=True,
        candidate_runner=runner,
        existing_result_artifact=first_batch,
        max_new_requests=3,
    )

    assert len(calls) == 3
    assert second_batch["status"] == "offline_three_arm_execution_complete"
    assert second_batch["committed_parent_count"] == 2
    assert second_batch["result_count"] == 6
    assert second_batch["deferred_request_count"] == 0
    assert second_batch["three_arm_evaluation"]["complete_parent_count"] == 2


def test_micro_reversion_execution_isolates_failed_parent_from_clean_batch():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    failed_parent_id = materialized["requests"][0]["paired_replay_parent_id"]
    clean_requests = deepcopy(materialized["requests"])
    clean_parent_id = "micro-parent-clean-after-failure"
    clean_label_id = "trace-clean-after-failure:v1"
    for request in clean_requests:
        request["paired_replay_parent_id"] = clean_parent_id
        request["paired_replay_id"] = (
            f"{clean_parent_id}:{request['micro_reversion_replay_arm']}"
        )
        request["decision_trace_id"] = prepared[0]["decision_trace_id"]
        request["outcome_join_key"] = clean_label_id
    materialized["requests"].extend(clean_requests)
    _reseal_current_materialized_report(materialized)
    outcome_artifact = _current_outcome_artifact_for_materialized(materialized)

    def runner(request):
        failed_parent = request["paired_replay_parent_id"] == failed_parent_id
        return {
            "candidate_response": (
                {"action": "INVALID"}
                if failed_parent
                else _valid_micro_reversion_entry_response()
            ),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": f"response-{request['paired_replay_id']}",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
            },
        }

    batch = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=6,
    )

    assert batch["status"] == "offline_three_arm_execution_batch_complete"
    assert batch["result_count"] == 3
    assert batch["committed_parent_count"] == 1
    assert batch["deferred_request_count"] == 3
    assert batch["uncommitted_result_count"] == 0
    assert batch["provisional_failed_result_count"] == 3
    assert batch["three_arm_evaluation"]["complete_parent_count"] == 1
    assert {row["paired_replay_parent_id"] for row in batch["results"]} == {
        clean_parent_id
    }
    assert {exclusion["reason"] for exclusion in batch["execution_exclusions"]} == {
        "candidate_execution_schema_rejected"
    }
    assert batch["blocking_execution_exclusion_count"] == 0
    assert (
        quality._micro_reversion_execution_exit_code(
            report=batch,
            execute_candidate=True,
        )
        == 0
    )

    prior_label_hashes = {
        result["outcome_label_content_sha256"] for result in batch["results"]
    }
    rematerialized = deepcopy(materialized)
    rematerialized["generated_at"] = "2026-08-14T23:59:59+09:00"
    rematerialized["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in rematerialized.items()
            if key != "report_content_sha256"
        }
    )
    rebound_artifact = _current_outcome_artifact_for_materialized(rematerialized)
    resumed = quality.run_micro_reversion_materialized_requests(
        materialized_report=rematerialized,
        outcome_label_artifact=rebound_artifact,
        execute_candidate=True,
        candidate_runner=runner,
        existing_result_artifact=batch,
        max_new_requests=3,
    )

    assert resumed["status"] == "offline_three_arm_execution_batch_complete"
    assert resumed["result_count"] == 3
    assert resumed["checkpoint_resume_result_count"] == 3
    assert resumed["reused_result_count"] == 3
    assert resumed["new_result_count"] == 0
    assert resumed["provisional_failed_result_count"] == 3
    assert resumed["candidate_model_call_attempted"] is True
    assert {
        result["outcome_label_rebound_from_sha256"] for result in resumed["results"]
    } == prior_label_hashes


def test_micro_reversion_batch_allows_unselected_intentional_exclusion():
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle

    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    supported_requests = deepcopy(materialized["requests"])
    supported_parent_id = "micro-parent-supported-second"
    supported_label_id = "trace-supported-second:v1"
    for request in supported_requests:
        request["paired_replay_parent_id"] = supported_parent_id
        request["paired_replay_id"] = (
            f"{supported_parent_id}:{request['micro_reversion_replay_arm']}"
        )
        request["decision_trace_id"] = prepared[0]["decision_trace_id"]
        request["outcome_join_key"] = supported_label_id
    for request in materialized["requests"]:
        candidate = request["candidate"]
        candidate["provider"] = "unsupported_offline_provider"
        candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    materialized["requests"].extend(supported_requests)
    _reseal_current_materialized_report(materialized)
    outcome_artifact = _current_outcome_artifact_for_materialized(materialized)
    calls: list[str] = []

    def runner(request):
        calls.append(str(request["paired_replay_id"]))
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": f"response-{request['paired_replay_id']}",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
            },
        }

    batch = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=3,
    )

    assert len(calls) == 3
    assert all(supported_parent_id in request_id for request_id in calls)
    assert batch["status"] == "offline_three_arm_execution_batch_complete"
    assert batch["result_count"] == 3
    assert batch["deferred_request_count"] == 3
    assert batch["execution_exclusion_count"] == 3
    assert batch["blocking_execution_exclusion_count"] == 0
    assert batch["three_arm_evaluation"]["complete_parent_count"] == 1
    assert (
        quality._micro_reversion_execution_exit_code(
            report=batch,
            execute_candidate=True,
        )
        == 0
    )

    def consumer_budget_receipt(report):
        report_without_hash = deepcopy(
            {
                key: value
                for key, value in report.items()
                if key != "report_content_sha256"
            }
        )
        for result in report_without_hash["results"]:
            old_result_id = result["result_id"]
            for attempt in result["replay_result"]["candidate_attempts"]:
                provenance = attempt["provider_provenance"]
                reservation_id = f"reservation-{result['paired_replay_id']}"
                provenance.update(
                    {
                        "provider_budget_reservation_id": reservation_id,
                        "provider_budget_attempt_identity_sha256": (
                            quality._sha256({"reservation_id": reservation_id})
                        ),
                        "provider_budget_settled": True,
                        "provider_budget_unknown_usage_reservation_retained": False,
                        "provider_budget_reserved_cost_usd": "0.1",
                        "provider_budget_actual_cost_usd": "0.1",
                        "provider_budget_circuit_breaker_open": False,
                    }
                )
            result["result_id"] = (
                "micro-result-"
                + quality._sha256(quality._micro_reversion_result_content(result))[:24]
            )
            report_without_hash["result_ids"] = [
                result["result_id"] if value == old_result_id else value
                for value in report_without_hash["result_ids"]
            ]
            report_without_hash["new_result_ids"] = [
                result["result_id"] if value == old_result_id else value
                for value in report_without_hash["new_result_ids"]
            ]
        budget_body = {
            "schema": cycle.BUDGET_SUMMARY_SCHEMA,
            "circuit_breaker_open": False,
            "committed_cost_usd": "0.5",
            "daily_usd_cap": "1.0",
            "reservation_count": len(report_without_hash["results"]),
            "daily_attempt_cap": 12,
            "pricing_artifact_content_sha256": "e" * 64,
            **cycle.PROVIDER_BUDGET_AUTHORITY_CONTRACT,
        }
        report_without_hash["provider_budget"] = {
            **budget_body,
            "summary_content_sha256": quality._sha256(budget_body),
        }
        report_without_hash["provider_budget_contract_findings"] = []
        report_without_hash["target_date"] = "2026-08-14"
        report_without_hash["outcome_label_artifact_sha256"] = quality._sha256(
            {"kind": "test_outcome_artifact", "target_date": "2026-08-14"}
        )
        return {
            **report_without_hash,
            "report_content_sha256": cycle._sha256(report_without_hash),
        }

    cycle_report = consumer_budget_receipt(batch)
    # This narrow fixture intentionally has no reviewed economic reference, so
    # fail closed instead of silently turning a present evaluation into an empty
    # subset that could be mistaken for a complete historical consumer pass.
    with pytest.raises(
        ValueError,
        match=(
            "execution_report_exact_census_invalid:"
            "evaluation_economic_reference_hash_invalid"
        ),
    ):
        cycle._validated_execution_rows(cycle_report)

    def forbidden_rerun(_request):
        raise AssertionError("a completed bounded batch must be idempotently reusable")

    rerun = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=outcome_artifact,
        execute_candidate=True,
        candidate_runner=forbidden_rerun,
        existing_result_artifact=batch,
        max_new_requests=3,
    )

    assert rerun["status"] == "offline_three_arm_execution_batch_complete"
    assert rerun["new_result_count"] == 0
    assert rerun["result_count"] == 3
    assert rerun["deferred_request_count"] == 3
    assert (
        quality._micro_reversion_execution_exit_code(
            report=rerun,
            execute_candidate=True,
        )
        == 0
    )
    rerun_for_consumer = consumer_budget_receipt(rerun)
    with pytest.raises(
        ValueError,
        match=(
            "execution_report_exact_census_invalid:"
            "evaluation_economic_reference_hash_invalid"
        ),
    ):
        cycle._validated_execution_rows(rerun_for_consumer)


def test_micro_reversion_execution_does_not_infer_provider_success_from_hash():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )

    def runner(request):
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": "failed-response-id",
                "response_sha256": quality._sha256(request["paired_replay_id"]),
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": False,
            },
        }

    report = quality.run_micro_reversion_materialized_requests(
        materialized_report=materialized,
        outcome_label_artifact=_current_outcome_artifact_for_materialized(materialized),
        execute_candidate=True,
        candidate_runner=runner,
        max_new_requests=3,
    )

    assert report["provider_call_performed"] is True
    assert report["provider_response_hash_observed"] is True
    assert report["provider_call_succeeded"] is False
    assert report["provider_provenance_pass_count"] == 0
    assert report["status"] == (
        "offline_three_arm_execution_complete_with_failures_or_exclusions"
    )


def test_micro_reversion_execution_budget_findings_block_breaker_and_over_cap():
    report = {
        "new_result_ids": ["result-current"],
        "results": [
            {
                "result_id": "result-current",
                "replay_result": {
                    "candidate_attempts": [
                        {
                            "provider_provenance": {
                                "provider": "openai",
                                "provider_budget_reservation_id": "reservation-1",
                                "provider_budget_attempt_identity_sha256": "a" * 64,
                                "provider_budget_settled": True,
                                "provider_budget_unknown_usage_reservation_retained": False,
                                "provider_budget_circuit_breaker_open": False,
                            }
                        }
                    ]
                },
            }
        ],
    }
    summary_body = {
        "circuit_breaker_open": True,
        "committed_cost_usd": "1.00000001",
        "daily_usd_cap": "1.0",
        "reservation_count": 0,
        "daily_attempt_cap": 12,
    }
    summary = {
        **summary_body,
        "summary_content_sha256": quality._sha256(summary_body),
    }

    findings = quality._micro_reversion_execution_budget_findings(
        report=report,
        budget_summary=summary,
    )

    assert "provider_budget_circuit_breaker_open" in findings
    assert "provider_budget_committed_cost_exceeds_cap" in findings
    assert "provider_budget_reservation_count_below_result_provenance" in findings


def test_micro_reversion_budget_census_allows_cross_day_checkpoint_resume():
    def result(result_id: str, reservation_id: str) -> dict:
        return {
            "result_id": result_id,
            "replay_result": {
                "candidate_attempts": [
                    {
                        "provider_provenance": {
                            "provider": "openai",
                            "provider_budget_reservation_id": reservation_id,
                            "provider_budget_attempt_identity_sha256": "a" * 64,
                            "provider_budget_settled": True,
                            "provider_budget_unknown_usage_reservation_retained": (
                                False
                            ),
                            "provider_budget_circuit_breaker_open": False,
                        }
                    }
                ]
            },
        }

    report = {
        # Arm A was reserved on the prior KST execution date; only B/C belong
        # to the current daily ledger summary during checkpoint completion.
        "new_result_ids": ["result-b", "result-c"],
        "results": [
            result("result-a", "prior-day-reservation-a"),
            result("result-b", "current-day-reservation-b"),
            result("result-c", "current-day-reservation-c"),
        ],
    }
    summary_body = {
        "circuit_breaker_open": False,
        "committed_cost_usd": "0.5",
        "daily_usd_cap": "1.0",
        "reservation_count": 2,
        "daily_attempt_cap": 12,
    }
    summary = {
        **summary_body,
        "summary_content_sha256": quality._sha256(summary_body),
    }

    findings = quality._micro_reversion_execution_budget_findings(
        report=report,
        budget_summary=summary,
    )

    assert "provider_budget_reservation_count_below_result_provenance" not in findings


def test_micro_reversion_execution_resumes_hash_bound_checkpoint(tmp_path):
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )
    outcome_artifact = _current_outcome_artifact_for_materialized(materialized)
    first_calls = []
    checkpoint_path = tmp_path / "micro-execution.checkpoint.json"

    def first_runner(request):
        first_calls.append(request["paired_replay_id"])
        return {
            "candidate_response": _valid_micro_reversion_entry_response(),
            "provider_provenance": {
                "provider": "openai",
                "model": "gpt-test",
                "transport": "openai_responses_http_offline",
                "source_transport_contract": request["candidate"]["transport"],
                "response_id": "test-response-id",
                "provider_none": False,
                "provider_call_attempted": True,
                "provider_call_succeeded": True,
                "response_sha256": quality._sha256(request["paired_replay_id"]),
            },
        }

    checkpoint_writes = 0

    def interrupt_after_first_checkpoint(record):
        nonlocal checkpoint_writes
        quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
        checkpoint_writes += 1
        if checkpoint_writes == 1:
            raise RuntimeError("simulated_process_interruption")

    # A/B/C is selected as one atomic parent.  Simulate a process interruption
    # after the first durable checkpoint.  The partial row may prevent a
    # duplicate call while the remaining arms resume, but must remain hidden
    # from the public result/evaluator until the whole parent commits.
    with pytest.raises(RuntimeError, match="simulated_process_interruption"):
        quality.run_micro_reversion_materialized_requests(
            materialized_report=materialized,
            outcome_label_artifact=outcome_artifact,
            execute_candidate=True,
            candidate_runner=first_runner,
            max_new_requests=3,
            checkpoint_callback=interrupt_after_first_checkpoint,
        )

    checkpoint = quality._load_micro_reversion_checkpoint(checkpoint_path)
    assert checkpoint["checkpoint_record_count"] == 1
    assert len(checkpoint["results"]) == 1
    rematerialized = deepcopy(materialized)
    rematerialized["generated_at"] = "2026-08-14T23:59:59+09:00"
    rematerialized["report_content_sha256"] = quality._sha256(
        {
            key: value
            for key, value in rematerialized.items()
            if key != "report_content_sha256"
        }
    )
    rematerialized_outcome_artifact = _current_outcome_artifact_for_materialized(
        rematerialized
    )
    assert rematerialized["report_content_sha256"] != (
        materialized["report_content_sha256"]
    )
    assert quality._micro_reversion_materialized_request_census_sha256(
        rematerialized
    ) == quality._micro_reversion_materialized_request_census_sha256(materialized)

    def forbidden_runner(_request):
        raise AssertionError("insufficient remaining parent budget must not call")

    still_partial = quality.run_micro_reversion_materialized_requests(
        materialized_report=rematerialized,
        outcome_label_artifact=rematerialized_outcome_artifact,
        execute_candidate=True,
        candidate_runner=forbidden_runner,
        existing_result_artifact=checkpoint,
        max_new_requests=1,
    )

    assert still_partial["result_count"] == 0
    assert still_partial["results"] == []
    assert still_partial["three_arm_evaluation"]["complete_parent_count"] == 0
    assert still_partial["reused_result_count"] == 0
    assert still_partial["provisional_checkpoint_result_count"] == 1
    assert still_partial["uncommitted_result_count"] == 1
    assert still_partial["deferred_request_count"] == 3
    assert still_partial["status"] == (
        "offline_three_arm_execution_complete_with_failures_or_exclusions"
    )

    second_calls = []

    def second_runner(request):
        second_calls.append(request["paired_replay_id"])
        return first_runner(request)

    resumed = quality.run_micro_reversion_materialized_requests(
        materialized_report=rematerialized,
        outcome_label_artifact=rematerialized_outcome_artifact,
        execute_candidate=True,
        candidate_runner=second_runner,
        existing_result_artifact=checkpoint,
        max_new_requests=2,
    )

    assert resumed["status"] == "offline_three_arm_execution_complete"
    assert resumed["reused_result_count"] == 0
    assert resumed["checkpoint_resume_result_count"] == 1
    assert resumed["provisional_checkpoint_result_count"] == 1
    assert resumed["uncommitted_result_count"] == 0
    assert resumed["new_result_count"] == 2
    assert resumed["deferred_request_count"] == 0
    assert len(second_calls) == 2
    assert len(resumed["results"]) == 3


def test_micro_reversion_checkpoint_record_writes_scale_linearly(tmp_path, monkeypatch):
    original_atomic_write = quality._atomic_write_json
    serialized_bytes = []

    def measured_atomic_write(path, value):
        serialized_bytes.append(
            len(json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"))
        )
        original_atomic_write(path, value)

    monkeypatch.setattr(quality, "_atomic_write_json", measured_atomic_write)

    def write_records(checkpoint_path, count):
        before = len(serialized_bytes)
        previous_hash = None
        for sequence in range(1, count + 1):
            result = {
                "result_id": f"linear-result-{sequence:04d}",
                "paired_replay_id": f"linear-request-{sequence:04d}",
                "payload": "x" * 512,
            }
            record = quality._micro_reversion_checkpoint_record(
                materialized_report_content_sha256="a" * 64,
                sequence=sequence,
                previous_record_sha256=previous_hash,
                result=result,
            )
            quality._write_micro_reversion_checkpoint_record(
                checkpoint_path,
                record,
            )
            previous_hash = record["checkpoint_record_content_sha256"]
        written = sum(serialized_bytes[before:])
        reconstructed = quality._load_micro_reversion_checkpoint(checkpoint_path)
        assert reconstructed["checkpoint_record_count"] == count
        assert len(reconstructed["results"]) == count
        return written

    bytes_60 = write_records(tmp_path / "sixty.checkpoint.json", 60)
    bytes_120 = write_records(tmp_path / "one-twenty.checkpoint.json", 120)

    assert bytes_120 < bytes_60 * 2.2


def test_micro_reversion_checkpoint_record_tamper_fails_closed(tmp_path):
    checkpoint_path = tmp_path / "tampered.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="b" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "tampered-result", "payload": "original"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    record_path = next(
        quality._micro_reversion_checkpoint_record_dir(checkpoint_path).glob("*.json")
    )
    stored = json.loads(record_path.read_text(encoding="utf-8"))
    stored["result"]["payload"] = "tampered"
    record_path.write_text(json.dumps(stored), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="micro_reversion_checkpoint_record_hash_mismatch",
    ):
        quality._load_micro_reversion_checkpoint(checkpoint_path)


def test_micro_reversion_checkpoint_malformed_record_fails_closed(tmp_path):
    checkpoint_path = tmp_path / "malformed-record.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="b" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "malformed-record-result"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    record_path = next(
        quality._micro_reversion_checkpoint_record_dir(checkpoint_path).glob("*.json")
    )
    record_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="json_generation_payload_invalid"):
        quality._load_micro_reversion_checkpoint(checkpoint_path)


def test_micro_reversion_checkpoint_record_symlink_fails_closed(tmp_path):
    checkpoint_path = tmp_path / "symlink-record.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="b" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "symlink-record-result"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    record_path = next(
        quality._micro_reversion_checkpoint_record_dir(checkpoint_path).glob("*.json")
    )
    external_path = tmp_path / "external-record.json"
    record_path.replace(external_path)
    record_path.symlink_to(external_path)

    with pytest.raises(ValueError, match="json_artifact_path_type_invalid"):
        quality._load_micro_reversion_checkpoint(checkpoint_path)


def test_micro_reversion_checkpoint_record_directory_symlink_rejects_before_write(
    tmp_path,
):
    checkpoint_path = tmp_path / "symlink-record-directory.checkpoint.json"
    external_directory = tmp_path / "external-record-directory"
    external_directory.mkdir()
    record_dir = quality._micro_reversion_checkpoint_record_dir(checkpoint_path)
    record_dir.symlink_to(external_directory, target_is_directory=True)
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="b" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "must-not-escape-record-directory"},
    )

    with pytest.raises(
        ValueError,
        match="micro_reversion_checkpoint_record_directory_invalid",
    ):
        quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)

    assert list(external_directory.iterdir()) == []
    assert not checkpoint_path.exists()


def test_micro_reversion_checkpoint_custody_serializes_concurrent_append(tmp_path):
    checkpoint_path = tmp_path / "concurrent-append.checkpoint.json"
    materialized_hash = "7" * 64
    process_context = multiprocessing.get_context("spawn")
    ready_queue = process_context.Queue()
    result_queue = process_context.Queue()
    start_event = process_context.Event()
    workers = [
        process_context.Process(
            target=_checkpoint_concurrent_append_worker,
            args=(
                str(checkpoint_path),
                materialized_hash,
                f"concurrent-result-{index}",
                ready_queue,
                start_event,
                result_queue,
            ),
        )
        for index in (1, 2)
    ]
    for worker in workers:
        worker.start()
    assert {ready_queue.get(timeout=10) for _ in workers} == {
        "concurrent-result-1",
        "concurrent-result-2",
    }
    start_event.set()
    for worker in workers:
        worker.join(timeout=15)
        assert worker.exitcode == 0

    worker_results = [result_queue.get(timeout=5) for _ in workers]
    assert {row[0] for row in worker_results} == {"ok"}
    assert {row[2] for row in worker_results} == {1, 2}
    checkpoint = quality._load_micro_reversion_checkpoint(checkpoint_path)
    assert checkpoint["checkpoint_record_count"] == 2
    assert {row["result_id"] for row in checkpoint["results"]} == {
        "concurrent-result-1",
        "concurrent-result-2",
    }
    record_names = sorted(
        path.name
        for path in quality._micro_reversion_checkpoint_record_dir(
            checkpoint_path
        ).glob("*.json")
    )
    assert [name[:8] for name in record_names] == ["00000001", "00000002"]


def test_micro_reversion_checkpoint_custody_lock_symlink_fails_closed(tmp_path):
    checkpoint_path = tmp_path / "symlink-lock.checkpoint.json"
    external_lock = tmp_path / "external-lock"
    external_lock.write_text("unchanged", encoding="utf-8")
    lock_path = quality._micro_reversion_checkpoint_custody_lock_path(checkpoint_path)
    lock_path.symlink_to(external_lock)

    with pytest.raises(OSError):
        quality._load_micro_reversion_checkpoint(checkpoint_path)

    assert external_lock.read_text(encoding="utf-8") == "unchanged"
    assert not checkpoint_path.exists()


def test_micro_reversion_checkpoint_collision_symlink_fails_before_manifest_write(
    tmp_path,
):
    checkpoint_path = tmp_path / "symlink-collision.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="b" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "symlink-collision-result"},
    )
    record_dir = quality._micro_reversion_checkpoint_record_dir(checkpoint_path)
    record_dir.mkdir(parents=True)
    external_path = tmp_path / "external-collision-record.json"
    quality._atomic_write_json(external_path, record)
    collision_path = record_dir / (
        "00000001-" + record["checkpoint_record_content_sha256"] + ".json"
    )
    collision_path.symlink_to(external_path)

    with pytest.raises(ValueError, match="json_artifact_path_type_invalid"):
        quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    assert not checkpoint_path.exists()


def test_micro_reversion_checkpoint_malformed_manifest_is_not_repaired_silently(
    tmp_path,
):
    checkpoint_path = tmp_path / "malformed-manifest.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="c" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "malformed-manifest-result"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    checkpoint_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="json_generation_payload_invalid"):
        quality._load_micro_reversion_checkpoint(
            checkpoint_path,
            repair_manifest=True,
        )


def test_micro_reversion_checkpoint_rejects_divergent_plain_gzip_manifests(
    tmp_path,
):
    checkpoint_path = tmp_path / "manifest-conflict.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="d" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "manifest-conflict-result"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    conflicting_manifest = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    conflicting_manifest["checkpoint_record_count"] = 0
    with gzip.open(
        checkpoint_path.with_name(checkpoint_path.name + ".gz"),
        "wt",
        encoding="utf-8",
    ) as handle:
        json.dump(conflicting_manifest, handle)

    with pytest.raises(ValueError, match="json_artifact_plain_gzip_conflict"):
        quality._load_micro_reversion_checkpoint(
            checkpoint_path,
            repair_manifest=True,
        )


def test_micro_reversion_checkpoint_recovers_record_written_before_manifest(
    tmp_path,
):
    checkpoint_path = tmp_path / "orphan-record.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="c" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "orphan-result", "payload": "durable"},
    )
    record_dir = quality._micro_reversion_checkpoint_record_dir(checkpoint_path)
    record_dir.mkdir(parents=True)
    record_path = record_dir / (
        "00000001-" + record["checkpoint_record_content_sha256"] + ".json"
    )
    quality._atomic_write_json(record_path, record)

    with pytest.raises(
        ValueError,
        match="micro_reversion_checkpoint_manifest_missing",
    ):
        quality._load_micro_reversion_checkpoint(checkpoint_path)

    reconstructed = quality._load_micro_reversion_checkpoint(
        checkpoint_path,
        repair_manifest=True,
    )

    assert reconstructed["checkpoint_record_count"] == 1
    assert reconstructed["results"][0]["result_id"] == "orphan-result"
    manifest = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert manifest["checkpoint_record_count"] == 1
    assert manifest["checkpoint_head_sha256"] == (
        record["checkpoint_record_content_sha256"]
    )


def test_micro_reversion_checkpoint_stale_manifest_requires_explicit_repair(tmp_path):
    checkpoint_path = tmp_path / "stale-prefix.checkpoint.json"
    materialized_hash = "e" * 64
    first = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256=materialized_hash,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "stale-prefix-result-1"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, first)
    second = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256=materialized_hash,
        sequence=2,
        previous_record_sha256=first["checkpoint_record_content_sha256"],
        result={"result_id": "stale-prefix-result-2"},
    )
    record_path = quality._micro_reversion_checkpoint_record_dir(checkpoint_path) / (
        "00000002-" + second["checkpoint_record_content_sha256"] + ".json"
    )
    quality._atomic_write_json(record_path, second)

    with pytest.raises(
        ValueError,
        match="micro_reversion_checkpoint_manifest_stale_prefix",
    ):
        quality._load_micro_reversion_checkpoint(checkpoint_path)

    reconstructed = quality._load_micro_reversion_checkpoint(
        checkpoint_path,
        repair_manifest=True,
    )
    assert reconstructed["checkpoint_record_count"] == 2
    assert (
        reconstructed["checkpoint_head_sha256"]
        == second["checkpoint_record_content_sha256"]
    )


def test_micro_reversion_checkpoint_resume_reads_verified_gzip_records(tmp_path):
    checkpoint_path = tmp_path / "compressed.checkpoint.json"
    materialized_hash = "a" * 64
    previous_hash = None
    for sequence in (1, 2):
        result = {
            "result_id": f"result-{sequence}",
            "paired_replay_id": f"request-{sequence}",
        }
        record = quality._micro_reversion_checkpoint_record(
            materialized_report_content_sha256=materialized_hash,
            sequence=sequence,
            previous_record_sha256=previous_hash,
            result=result,
        )
        quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
        previous_hash = record["checkpoint_record_content_sha256"]

    record_dir = quality._micro_reversion_checkpoint_record_dir(checkpoint_path)
    for source in sorted(record_dir.glob("*.json")):
        compressed = source.with_suffix(".json.gz")
        with (
            source.open("rb") as input_handle,
            gzip.open(compressed, "wb") as output_handle,
        ):
            output_handle.write(input_handle.read())
        source.unlink()

    reconstructed = quality._load_micro_reversion_checkpoint(checkpoint_path)

    assert reconstructed["checkpoint_record_count"] == 2
    assert [row["result_id"] for row in reconstructed["results"]] == [
        "result-1",
        "result-2",
    ]
    resumed_record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256=materialized_hash,
        sequence=3,
        previous_record_sha256=previous_hash,
        result={
            "result_id": "result-3",
            "paired_replay_id": "request-3",
        },
    )
    quality._write_micro_reversion_checkpoint_record(
        checkpoint_path,
        resumed_record,
    )
    resumed = quality._load_micro_reversion_checkpoint(checkpoint_path)
    assert resumed["checkpoint_record_count"] == 3
    assert resumed["results"][-1]["result_id"] == "result-3"


def test_micro_reversion_checkpoint_rejects_plain_gzip_logical_collision(tmp_path):
    checkpoint_path = tmp_path / "collision.checkpoint.json"
    record = quality._micro_reversion_checkpoint_record(
        materialized_report_content_sha256="a" * 64,
        sequence=1,
        previous_record_sha256=None,
        result={"result_id": "result-1"},
    )
    quality._write_micro_reversion_checkpoint_record(checkpoint_path, record)
    source = next(
        quality._micro_reversion_checkpoint_record_dir(checkpoint_path).glob("*.json")
    )
    with (
        source.open("rb") as input_handle,
        gzip.open(source.with_suffix(".json.gz"), "wb") as output_handle,
    ):
        output_handle.write(input_handle.read())

    with pytest.raises(
        ValueError, match="micro_reversion_checkpoint_record_storage_conflict"
    ):
        quality._load_micro_reversion_checkpoint(checkpoint_path)


def test_micro_reversion_source_bundle_excludes_bad_row_without_aborting():
    prepared, seed_bundle = _micro_reversion_materialization_fixture()
    bad_request = json.loads(json.dumps(prepared[0]))
    bad_request.update(
        {
            "paired_replay_id": "missing-source-row",
            "decision_trace_id": "missing-source-trace",
        }
    )
    rebuilt = quality.build_micro_reversion_source_bundle(
        target_date="2026-08-14",
        prepared_requests=[prepared[0], bad_request],
        traces=[seed_bundle["rows"][0]["source_trace"]],
        payloads=[seed_bundle["rows"][0]["source_payload"]],
        prompt_rows=[
            {
                "schema": "ai_decision_prompt_v1",
                "endpoint": "analyze_target",
                "model": "gpt-test",
                "schema_name": "decision_quality_v2_7_entry",
                "prompt_sha256": seed_bundle["rows"][0]["source_trace"][
                    "prompt_sha256"
                ],
                "sanitized_prompt": seed_bundle["rows"][0][
                    "current_control_prompt_contract"
                ]["system_prompt"],
                "replay_exact": True,
                "redacted": False,
            }
        ],
        control_prompt_contracts=[
            {
                "decision_trace_id": prepared[0]["decision_trace_id"],
                "prompt_sha256": seed_bundle["rows"][0]["source_trace"][
                    "prompt_sha256"
                ],
                "prompt_contract": seed_bundle["rows"][0][
                    "current_control_prompt_contract"
                ],
            }
        ],
        market_rows=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed_bundle["rows"][0],
            pool_name="market",
            reference_field="source_market_row_sha256s",
        ),
        depth_rows=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed_bundle["rows"][0],
            pool_name="depth",
            reference_field="source_depth_row_sha256s",
        ),
        event_references=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed_bundle["rows"][0],
            pool_name="event_reference",
            reference_field="source_event_reference_sha256s",
        ),
        bridge_config=seed_bundle["rows"][0]["bridge_config"],
        verified_symbol_metadata_by_trace={
            prepared[0]["decision_trace_id"]: seed_bundle["rows"][0][
                "verified_symbol_metadata"
            ]
        },
    )

    assert rebuilt["eligible_row_count"] == 1
    assert rebuilt["excluded_row_count"] == 1
    assert rebuilt["prepared_request_count"] == 2
    assert rebuilt["exclusions"][0]["decision_trace_id"] == "missing-source-trace"


def test_micro_reversion_source_bundle_validates_bridge_commitment_once(
    monkeypatch,
):
    from src.engine.scalping.micro_reversion import ai_quality_bridge

    prepared, seed_bundle = _micro_reversion_materialization_fixture()
    _, _, bridge_report = _micro_reversion_action_neutral_bridge_fixture()
    seed = seed_bundle["rows"][0]
    trace = seed["source_trace"]
    payload = seed["source_payload"]
    commitment_calls = 0
    source_pool_validation_calls = 0
    original_commitment = quality._micro_reversion_outcome_source_commitment
    original_source_pool_validation = (
        ai_quality_bridge.validate_future_outcome_source_pool
    )

    def counted_commitment(*args, **kwargs):
        nonlocal commitment_calls
        commitment_calls += 1
        return original_commitment(*args, **kwargs)

    def counted_source_pool_validation(*args, **kwargs):
        nonlocal source_pool_validation_calls
        source_pool_validation_calls += 1
        return original_source_pool_validation(*args, **kwargs)

    monkeypatch.setattr(
        quality,
        "_micro_reversion_outcome_source_commitment",
        counted_commitment,
    )
    monkeypatch.setattr(
        ai_quality_bridge,
        "validate_future_outcome_source_pool",
        counted_source_pool_validation,
    )
    report = quality.build_micro_reversion_source_bundle(
        target_date="2026-08-14",
        prepared_requests=prepared,
        traces=[trace],
        payloads=[payload],
        prompt_rows=[
            {
                "schema": "ai_decision_prompt_v1",
                "endpoint": trace["endpoint"],
                "model": trace["model"],
                "schema_name": payload["schema_name"],
                "prompt_sha256": trace["prompt_sha256"],
                "sanitized_prompt": seed["current_control_prompt_contract"][
                    "system_prompt"
                ],
                "replay_exact": True,
                "redacted": False,
            }
        ],
        control_prompt_contracts=[
            {
                "decision_trace_id": trace["decision_trace_id"],
                "prompt_sha256": trace["prompt_sha256"],
                "prompt_contract": seed["current_control_prompt_contract"],
            }
        ],
        market_rows=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed,
            pool_name="market",
            reference_field="source_market_row_sha256s",
        ),
        depth_rows=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed,
            pool_name="depth",
            reference_field="source_depth_row_sha256s",
        ),
        event_references=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed,
            pool_name="event_reference",
            reference_field="source_event_reference_sha256s",
        ),
        bridge_config=seed["bridge_config"],
        verified_symbol_metadata_by_trace={
            trace["decision_trace_id"]: seed["verified_symbol_metadata"]
        },
        outcome_source_bridge_report=bridge_report,
    )

    assert commitment_calls == 1
    assert source_pool_validation_calls == 1
    assert report["outcome_source_commitment"]["bridge_report_content_sha256"] == (
        bridge_report["report_content_sha256"]
    )


def test_micro_reversion_source_bundle_uses_bounded_sqlite_store():
    from src.engine.scalping.micro_reversion.ai_quality_bridge import (
        BridgeConfig,
        _relevant_windows,
        _SQLiteRelevantSourceStore,
    )

    prepared, seed_bundle = _micro_reversion_materialization_fixture()
    seed = seed_bundle["rows"][0]
    trace = seed["source_trace"]
    payload = seed["source_payload"]
    market_rows = quality._micro_reversion_source_rows_from_pool(
        source_bundle=seed_bundle,
        bundle_row=seed,
        pool_name="market",
        reference_field="source_market_row_sha256s",
    )
    depth_rows = quality._micro_reversion_source_rows_from_pool(
        source_bundle=seed_bundle,
        bundle_row=seed,
        pool_name="depth",
        reference_field="source_depth_row_sha256s",
    )
    references = quality._micro_reversion_source_rows_from_pool(
        source_bundle=seed_bundle,
        bundle_row=seed,
        pool_name="event_reference",
        reference_field="source_event_reference_sha256s",
    )
    config = BridgeConfig(**seed["bridge_config"])
    windows = _relevant_windows([trace], [payload], config=config)

    def synthetic_market_corpus():
        yield from market_rows
        for index in range(2_000):
            yield {
                **market_rows[0],
                "item": "999999",
                "symbol": "999999",
                "source_sequence": index + 1,
                "series_sequence": index + 1,
            }

    with _SQLiteRelevantSourceStore("", windows=windows) as source_store:
        source_store.ingest("market", synthetic_market_corpus())
        source_store.ingest("depth", depth_rows)
        source_store.ingest("reference", references, reference_rows=True)
        source_store.finalize()
        rebuilt = quality.build_micro_reversion_source_bundle(
            target_date="2026-08-14",
            prepared_requests=prepared,
            traces=[trace],
            payloads=[payload],
            prompt_rows=[
                {
                    "schema": "ai_decision_prompt_v1",
                    "endpoint": trace["endpoint"],
                    "model": trace["model"],
                    "schema_name": payload["schema_name"],
                    "prompt_sha256": trace["prompt_sha256"],
                    "sanitized_prompt": seed["current_control_prompt_contract"][
                        "system_prompt"
                    ],
                    "replay_exact": True,
                    "redacted": False,
                }
            ],
            control_prompt_contracts=[
                {
                    "decision_trace_id": trace["decision_trace_id"],
                    "prompt_sha256": trace["prompt_sha256"],
                    "prompt_contract": seed["current_control_prompt_contract"],
                }
            ],
            market_rows=(),
            depth_rows=(),
            event_references=(),
            bridge_config=config,
            verified_symbol_metadata_by_trace={
                trace["decision_trace_id"]: seed["verified_symbol_metadata"]
            },
            source_store=source_store,
        )

    assert rebuilt["source_materialization_mode"] == "sqlite_bounded_per_trace"
    assert (
        rebuilt["source_materialization_diagnostics"][
            "invalid_timestamp_rows_used_for_evidence"
        ]
        is False
    )
    assert rebuilt["source_materialization_diagnostics"]["retained_row_counts"] == {
        "market": 6,
        "depth": 10,
        "reference": 1,
    }
    assert rebuilt["eligible_row_count"] == 1
    assert rebuilt["rows"][0]["evidence"] == seed["evidence"]


def test_micro_reversion_source_bundle_header_tamper_fails_closed():
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    source_bundle["row_count"] = 2

    with pytest.raises(ValueError, match="source_bundle_content_sha256_mismatch"):
        quality.materialize_micro_reversion_offline_requests(
            prepared_requests=prepared,
            bridge_source_bundle=source_bundle,
        )


def test_micro_reversion_excluded_scope_uses_trade_date_not_symbol():
    assert quality._micro_reversion_excluded_scopes(
        [
            {
                "trade_date": "2026-08-14",
                "venue": "krx",
                "session_bucket": "KRX_REGULAR",
                "sequence_epoch": 123,
            }
        ]
    ) == {("2026-08-14", "KRX", "KRX_REGULAR", 123)}
    with pytest.raises(ValueError, match="excluded_scope_row_invalid"):
        quality._micro_reversion_excluded_scopes(
            [
                {
                    "symbol": "000001",
                    "venue": "KRX",
                    "session_bucket": "KRX_REGULAR",
                    "sequence_epoch": 123,
                }
            ]
        )


def test_actual_stage_coverage_prepare_output_adapts_into_three_arm_requests():
    from src.engine.scalping.ai_stage_coverage_replay import (
        prepare_stage_requests,
    )

    _, seed_bundle = _micro_reversion_materialization_fixture()
    seed = seed_bundle["rows"][0]
    trace = seed["source_trace"]
    payload = seed["source_payload"]
    control_contract = seed["current_control_prompt_contract"]
    stage_requests, summary = prepare_stage_requests(
        stage="entry",
        dates=["2026-08-14"],
        max_rows=1,
        control_manifest={
            "controls": [
                {
                    "endpoint": "analyze_target",
                    "prompt_version": trace["prompt_version"],
                    "prompt_sha256": trace["prompt_sha256"],
                    "provider_actual": trace["provider_actual"],
                    "model": trace["model"],
                    "request_temperature": trace["request_temperature"],
                    "request_reasoning_effort": trace["request_reasoning_effort"],
                }
            ]
        },
        promotion={"promoted_at": "2026-08-14T08:30:00+09:00"},
        traces=[trace],
        payloads=[payload],
        eligible_trace_ids={trace["decision_trace_id"]},
    )
    assert summary["selected_frozen_cohort_count"] == 1
    assert stage_requests[0]["candidate"]["schema_name"] == (
        "decision_quality_v2_entry_candidate"
    )
    assert stage_requests[0]["candidate"]["require_json"] is True
    assert stage_requests[0]["candidate"]["response_schema_application"] == (
        "provider_enforced_openai"
    )
    rebuilt_bundle = quality.build_micro_reversion_source_bundle(
        target_date="2026-08-14",
        prepared_requests=stage_requests,
        traces=[trace],
        payloads=[payload],
        prompt_rows=[
            {
                "schema": "ai_decision_prompt_v1",
                "prompt_sha256": trace["prompt_sha256"],
                "endpoint": trace["endpoint"],
                "model": trace["model"],
                "schema_name": payload["schema_name"],
                "redacted": False,
                "replay_exact": True,
                "sanitized_prompt": control_contract["system_prompt"],
            }
        ],
        control_prompt_contracts=[
            {
                "decision_trace_id": trace["decision_trace_id"],
                "prompt_sha256": trace["prompt_sha256"],
                "prompt_contract": control_contract,
            }
        ],
        market_rows=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed,
            pool_name="market",
            reference_field="source_market_row_sha256s",
        ),
        depth_rows=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed,
            pool_name="depth",
            reference_field="source_depth_row_sha256s",
        ),
        event_references=quality._micro_reversion_source_rows_from_pool(
            source_bundle=seed_bundle,
            bundle_row=seed,
            pool_name="event_reference",
            reference_field="source_event_reference_sha256s",
        ),
        bridge_config=seed["bridge_config"],
        verified_symbol_metadata_by_trace={
            trace["decision_trace_id"]: seed["verified_symbol_metadata"]
        },
    )
    adapter = rebuilt_bundle["rows"][0]["candidate_contract_adapter"]
    assert adapter["status"] == "prepared_contract_complete"
    assert adapter["adapted_fields"] == []

    materialized = quality.materialize_micro_reversion_offline_requests(
        prepared_requests=stage_requests,
        bridge_source_bundle=rebuilt_bundle,
    )
    assert materialized["request_count"] == 3
    assert all(row["candidate"]["schema_name"] for row in materialized["requests"])


def test_holding_paired_replay_uses_noncollapsed_prompt_and_pointer_ledger():
    trace = {
        **_trace(action="EXIT"),
        "decision_stage": "holding",
        "endpoint": "holding_score",
        "source_event_stage": "scale_in_submit_authority_retry",
        "prompt_version": "holding_score_v2",
        "prompt_sha256": "holding-prompt-1",
    }
    exact_payload = {
        "position_context": {"buy_qty": 2, "buy_price": 100},
        "holding_decision_context": {
            "schema": quality.HOLDING_CONTEXT_SCHEMA,
            "execution_pnl": {
                "estimated_net_executable_pnl_pct": -0.2,
                "executable_sell_price": 99,
            },
            "position_lifecycle": {"remaining_qty": 2},
            "order_reconciliation": {
                "position_valid": True,
                "order_consistent": True,
            },
            "source_quality": {
                "status": "fresh_consistent",
                "candle_status": "fresh_consistent",
                "bbo_fresh": True,
                "position_valid": True,
                "order_consistent": True,
            },
            "candle": {
                "completed_bar_count": 1,
                "bars": [{"is_forming": False, "close": 101}],
            },
        },
    }
    payload = {**_payload(), "sanitized_user_input": exact_payload}
    label = {
        **_pending(action="EXIT"),
        "decision_stage": "holding",
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "30m": {
                "end_return_pct": 0.5,
                "mfe_pct": 1.0,
                "mae_pct": -0.3,
                "first_hit": "target",
            }
        },
    }
    control_manifest = {
        "status": "control_manifest_frozen_collect_exact_samples",
        "controls": [
            {
                "endpoint": "holding_score",
                "prompt_version": "holding_score_v2",
                "prompt_sha256": "holding-prompt-1",
                "provider_actual": "openai",
                "model": "gpt-test",
                "request_temperature": 0,
                "request_reasoning_effort": "medium",
            }
        ],
    }

    requests = quality.prepare_paired_replay_requests(
        control_manifest=control_manifest,
        traces=[trace],
        payloads=[payload],
        labels=[label],
    )

    assert len(requests) == 1
    request = requests[0]
    assert request["source_event_stage"] == "scale_in_submit_authority_retry"
    exact_envelope_sha256 = quality._sha256({"request": "holding-scale-in"})
    bound_request = {
        **request,
        "request_envelope_sha256": exact_envelope_sha256,
    }
    bound_trace = {**trace, "request_envelope_sha256": exact_envelope_sha256}
    bound_payload = {
        **payload,
        "endpoint": "holding_score",
        "request_envelope_sha256": exact_envelope_sha256,
    }
    quality._assert_micro_reversion_source_contract(
        request=bound_request,
        source_trace=bound_trace,
        source_payload=bound_payload,
    )
    drifted_source_stage_request = {
        **bound_request,
        "source_event_stage": "holding_score_upstream_preflight",
    }
    with pytest.raises(
        ValueError,
        match="micro_reversion_source_contract_source_event_stage_mismatch",
    ):
        quality._assert_micro_reversion_source_contract(
            request=drifted_source_stage_request,
            source_trace=bound_trace,
            source_payload=bound_payload,
        )
    assert request["candidate"]["prompt_version"] == (
        quality.DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION
    )
    assert request["candidate"]["semantic_validator_version"] == (
        quality.HOLDING_SEMANTIC_VALIDATOR_VERSION
    )
    assert "Holding decision rules:" in request["candidate"]["system_prompt"]
    assert request["candidate_input"]["exact_payload"] == exact_payload
    assert (
        request["candidate_input"]["holding_exact_contract_facts_v1"][
            "position_observed"
        ]
        is True
    )
    assert request["candidate_input_sha256"] == quality._sha256(
        request["candidate_input"]
    )
    assert request["runtime_effect"] is False
    assert request["actual_order_submitted"] is False

    response = {
        "edge_state": "EDGE",
        "action": "HOLD",
        "expected_upside_pct": 1.0,
        "expected_downside_pct": -0.5,
        "confidence": 70,
        "reason_codes": ["continuation_supported", "risk_reward_favorable"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "continuation",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "not_applicable",
        },
    }
    results = quality.run_paired_replay(
        requests,
        control_runner=lambda request: {"action": "EXIT"},
        candidate_runner=lambda request: response,
    )
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=requests,
        results=results,
        labels=[label],
    )

    assert (
        "candidate_probe_cost_adjusted_ev_positive"
        not in report["candidate_quality_checks"]
    )
    assert (
        "candidate_probe_bounded_risk_budget_pass"
        not in report["candidate_quality_checks"]
    )
    assert (
        "candidate_probe_cost_adjusted_ev_positive"
        not in report["buckets"][0]["candidate_quality_checks"]
    )


def test_paired_replay_consumes_tight_stop_entry_path_label():
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=[
            {
                "decision_trace_id": "tight-stop-trace",
                "paired_replay_id": "tight-stop-pair",
                "stock_code": "005930",
            }
        ],
        results=[
            {
                "decision_trace_id": "tight-stop-trace",
                "paired_replay_id": "tight-stop-pair",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "WAIT"},
                "candidate_response": {"action": "BUY", "edge_state": "EDGE"},
            }
        ],
        labels=[
            {
                "decision_trace_id": "tight-stop-trace",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": -0.2,
                        "mfe_pct": 0.1,
                        "mae_pct": -0.8,
                        "first_hit": "neither",
                        "entry_path_first_hit": "adverse_first",
                        "entry_path_target_pct": 0.3,
                        "entry_path_adverse_pct": -0.7,
                    }
                },
            }
        ],
    )

    row = report["paired_comparisons"][0]
    assert row["entry_path_first_hit"] == "adverse_first"
    assert "false_buy_tight_stop_adverse_first" in row["candidate_error_taxonomy"]
    assert report["control_tight_stop_adverse_first_exposure_count"] == 0
    assert report["candidate_tight_stop_adverse_first_exposure_count"] == 1
    assert (
        report["diagnostic_checks_not_quality_veto"][
            "tight_stop_adverse_first_exposure_not_increased"
        ]
        is False
    )
    assert report["entry_path_label_contract"]["decision_authority"] == (
        "offline_replay_and_attribution_only"
    )


def test_wide_spread_drawdown_recovery_uses_bounded_probe_risk_not_adverse_veto():
    report = quality.build_paired_replay_report(
        target_date="2026-08-03",
        requests=[
            {
                "decision_trace_id": "korean-pim-trace",
                "paired_replay_id": "korean-pim-pair",
                "stock_code": "448900",
                "reference_price_type": "executable_ask",
                "reference_price": 60900,
                "best_bid": 60300,
                "best_ask": 60900,
                "candidate": {
                    "exposure_semantics": ("offline_counterfactual_passive_probe_only")
                },
                "anticipatory_reversal_analysis": {
                    "execution_cost": {"conservative_execution_cost_pct": 0.5}
                },
            }
        ],
        results=[
            {
                "decision_trace_id": "korean-pim-trace",
                "paired_replay_id": "korean-pim-pair",
                "stage": "entry",
                "effective_venue": "NXT",
                "session_bucket": "nxt_aftermarket",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {"action": "BUY", "edge_state": "EDGE"},
            }
        ],
        labels=[
            {
                "decision_trace_id": "korean-pim-trace",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 1.4,
                        "mfe_pct": 2.4631,
                        "mae_pct": -0.9852,
                        "first_hit": "adverse",
                        "entry_path_first_hit": "adverse_first",
                        "profit_opportunity_observed": True,
                        "profit_opportunity_sequence": (
                            "drawdown_then_profit_recovery"
                        ),
                        "pre_profit_mae_pct": -0.9852,
                    }
                },
            }
        ],
    )

    row = report["paired_comparisons"][0]
    assert row["initial_spread_cost_pct"] == pytest.approx(0.9852216749)
    assert row["entry_path_adverse_first_spread_confounded"] is True
    assert row["directional_mae_estimate_ex_initial_spread_pct"] == pytest.approx(0.0)
    assert row["probe_worst_loss_pct"] == pytest.approx(-1.4852)
    assert row["probe_worst_loss_krw_per_share"] == pytest.approx(904.4868)
    assert row["probe_loss_within_bounded_cap"] is True
    assert row["probe_severe_tail_adverse"] is False
    assert row["candidate_drawdown_recovery_captured"] is True
    assert report["candidate_probe_cost_adjusted_ev_pct"] == pytest.approx(0.9)
    assert report["candidate_probe_loss_budget_breach_count"] == 0
    assert report["candidate_drawdown_recovery_capture_count"] == 1
    assert (
        report["candidate_quality_checks"]["candidate_probe_bounded_risk_budget_pass"]
        is True
    )
    assert (
        report["diagnostic_checks_not_quality_veto"][
            "adverse_first_exposure_not_increased"
        ]
        is False
    )
    assert report["probe_risk_contract"]["adverse_first_role"] == (
        "diagnostic_not_absolute_quality_veto"
    )


def test_paired_report_can_pass_promotion_from_same_cohort_cumulative_gate(
    monkeypatch,
):
    monkeypatch.setattr(
        quality,
        "_anticipatory_cumulative_learning_summary",
        lambda **_kwargs: {
            "schema": "anticipatory_reversal_cumulative_learning_v2",
            "promotion_quality_gate_pass": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
    )
    candidate_contract = {
        "prompt_version": "v214_entry",
        "system_prompt_sha256": "v214-prompt",
        "response_schema_sha256": "v214-schema",
        "exposure_semantics": "offline_counterfactual_passive_probe_only",
    }
    candidate_contract["contract_sha256"] = quality._candidate_contract_sha256(
        candidate_contract
    )
    report = quality.build_paired_replay_report(
        target_date="2026-08-06",
        requests=[
            {
                "decision_trace_id": "cumulative-trace",
                "paired_replay_id": "cumulative-pair",
                "decision_ts": "2026-08-06T09:00:00+09:00",
                "stock_code": "005930",
                "candidate": candidate_contract,
                "anticipatory_reversal_analysis": {
                    "execution_cost": {"conservative_execution_cost_pct": 0.1}
                },
            }
        ],
        results=[
            {
                "decision_trace_id": "cumulative-trace",
                "paired_replay_id": "cumulative-pair",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "candidate_contract_sha256": candidate_contract["contract_sha256"],
                "control_response": {"action": "DROP"},
                "candidate_response": {"action": "BUY", "edge_state": "EDGE"},
            }
        ],
        labels=[
            {
                "decision_trace_id": "cumulative-trace",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 0.8,
                        "mfe_pct": 1.0,
                        "mae_pct": -0.3,
                        "first_hit": "target",
                    }
                },
            }
        ],
    )

    assert report["candidate_exposure_sample_floor"]["pass"] is False
    assert report["candidate_quality_gate_pass"] is False
    assert report["promotion_quality_gate_pass"] is True
    assert report["promotion_quality_gate_basis"] == (
        "cumulative_same_contract_venue_session"
    )
    assert report["status"] == (
        "paired_replay_complete_cumulative_quality_pass_offline_only"
    )


def test_missing_mae_fails_closed_for_bounded_probe_risk():
    risk = quality._probe_path_risk(
        request={
            "reference_price_type": "executable_ask",
            "reference_price": 10000,
            "best_bid": 9990,
            "best_ask": 10000,
        },
        outcome_mfe_pct=1.0,
        outcome_mae_pct=None,
        pre_profit_mae_pct=None,
        entry_path_first_hit="neither_hit",
        profit_opportunity_sequence="not_recorded_legacy",
        conservative_execution_cost_pct=0.1,
    )

    assert risk["probe_path_risk_evaluable"] is False
    assert risk["probe_worst_loss_pct"] is None
    assert risk["probe_loss_within_bounded_cap"] is False
    assert risk["probe_severe_tail_adverse"] is False


def test_baseline_and_paired_report_preserve_exact_post_block_false_drop():
    post_block_outcome = {
        "label_version": quality.RISING_MISSED_POST_BLOCK_LABEL_VERSION,
        "link_status": "exact_trace_evaluation_joined",
        "evaluation_id": "evaluation-first",
        "decision_trace_id": "post-block-trace",
        "gross_first_hit_label": "gross_target_first",
        "source_quality_status": "pass",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    label = {
        "decision_trace_id": "post-block-trace",
        "decision_stage": "entry",
        "effective_venue": "NXT",
        "session_bucket": "NXT_AFTERMARKET",
        "action": "DROP",
        "label_status": "partial",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 0.8,
                "mfe_pct": 1.5,
                "mae_pct": -0.2,
                "first_hit": "neither",
                "entry_path_first_hit": "target_first",
            }
        },
        "stage_outcome": {
            "rising_missed_post_block_outcome": post_block_outcome,
        },
    }

    baseline = quality.build_quality_baseline(
        target_date="2026-08-03",
        labels=[label],
    )
    report = quality.build_paired_replay_report(
        target_date="2026-08-03",
        requests=[
            {
                "decision_trace_id": "post-block-trace",
                "paired_replay_id": "post-block-pair",
                "stock_code": "459510",
            }
        ],
        results=[
            {
                "decision_trace_id": "post-block-trace",
                "paired_replay_id": "post-block-pair",
                "stage": "entry",
                "effective_venue": "NXT",
                "session_bucket": "NXT_AFTERMARKET",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {"action": "DROP", "edge_state": "NO_EDGE"},
            }
        ],
        labels=[label],
    )

    assert baseline["taxonomy_counts"] == {
        "false_drop": 1,
        "false_drop_post_block_gross_target_first": 1,
        "missed_entry_tight_stop_target_first": 1,
    }
    assert baseline["rows"][0]["rising_missed_post_block_outcome"] == (
        post_block_outcome
    )
    comparison = report["paired_comparisons"][0]
    assert comparison["rising_missed_post_block_outcome"] == post_block_outcome
    assert (
        "false_drop_post_block_gross_target_first"
        in comparison["candidate_error_taxonomy"]
    )


def test_paired_report_requires_diverse_candidate_exposure_sample():
    requests = []
    results = []
    labels = []
    for index in range(10):
        trace_id = f"candidate-exposure-{index}"
        stock_code = f"{index % 3 + 1:06d}"
        requests.append(
            {
                "decision_trace_id": trace_id,
                "paired_replay_id": f"pair-{index}",
                "stock_code": stock_code,
            }
        )
        results.append(
            {
                "decision_trace_id": trace_id,
                "paired_replay_id": f"pair-{index}",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {"action": "BUY", "edge_state": "EDGE"},
            }
        )
        labels.append(
            {
                "decision_trace_id": trace_id,
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 0.5,
                        "mfe_pct": 0.8,
                        "mae_pct": -0.2,
                        "first_hit": "neither",
                    }
                },
            }
        )

    report = quality.build_paired_replay_report(
        target_date="2026-07-29",
        requests=requests,
        results=results,
        labels=labels,
    )

    assert report["candidate_exposure_decision_count"] == 10
    assert report["candidate_exposure_unique_symbol_count"] == 3
    assert report["candidate_exposure_sample_floor"]["pass"] is True
    assert (
        report["candidate_quality_checks"]["candidate_exposure_sample_floor_pass"]
        is True
    )

    split_venue_report = quality.build_paired_replay_report(
        target_date="2026-07-29",
        requests=requests
        + [
            {
                "decision_trace_id": "nxt-no-exposure",
                "paired_replay_id": "nxt-pair",
                "stock_code": "005930",
            }
        ],
        results=results
        + [
            {
                "decision_trace_id": "nxt-no-exposure",
                "paired_replay_id": "nxt-pair",
                "stage": "entry",
                "effective_venue": "NXT",
                "session_bucket": "NXT_AFTERMARKET",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "WAIT"},
                "candidate_response": {"action": "WAIT", "edge_state": "EDGE"},
            }
        ],
        labels=labels
        + [
            {
                "decision_trace_id": "nxt-no-exposure",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 0.2,
                        "mfe_pct": 0.4,
                        "mae_pct": -0.1,
                        "first_hit": "neither",
                    }
                },
            }
        ],
    )
    assert (
        split_venue_report["candidate_quality_checks"][
            "candidate_exposure_sample_floor_pass"
        ]
        is False
    )

    contract_split_requests = []
    for index, request in enumerate(requests):
        candidate = {
            "prompt_version": "candidate-a" if index < 5 else "candidate-b",
            "system_prompt_sha256": "prompt-a" if index < 5 else "prompt-b",
            "response_schema_sha256": "schema",
        }
        candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
        contract_split_requests.append({**request, "candidate": candidate})
    contract_split_results = [
        {
            **result,
            "candidate_contract_sha256": contract_split_requests[index]["candidate"][
                "contract_sha256"
            ],
        }
        for index, result in enumerate(results)
    ]
    contract_split_report = quality.build_paired_replay_report(
        target_date="2026-07-29",
        requests=contract_split_requests,
        results=contract_split_results,
        labels=labels,
    )
    assert contract_split_report["promotion_quality_gate_pass"] is False
    assert contract_split_report["status"] == (
        "paired_replay_complete_candidate_contract_split_required"
    )

    tampered_report = quality.build_paired_replay_report(
        target_date="2026-07-29",
        requests=[
            {
                **requests[0],
                "candidate": {
                    "prompt_version": (
                        quality.DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION
                        + "_entry"
                    ),
                    "system_prompt_sha256": "prompt-a",
                    "response_schema_sha256": "schema",
                    "contract_sha256": "tampered",
                },
            }
        ],
        results=results[:1],
        labels=labels[:1],
    )
    assert tampered_report["paired_comparable_count"] == 0
    assert tampered_report["candidate_contract_integrity_rejected_count"] == 1
    assert tampered_report["status"] == (
        "candidate_contract_integrity_rejected_no_runtime_apply"
    )

    false_wait_results = [dict(row) for row in results]
    false_wait_results[0] = {
        **false_wait_results[0],
        "candidate_response": {"action": "WAIT", "edge_state": "EDGE"},
    }
    false_wait_labels = [dict(row) for row in labels]
    false_wait_labels[0] = {
        **false_wait_labels[0],
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 0.4,
                "mfe_pct": 1.2,
                "mae_pct": -0.2,
                "first_hit": "neither",
            }
        },
    }
    false_wait_report = quality.build_paired_replay_report(
        target_date="2026-07-29",
        requests=requests,
        results=false_wait_results,
        labels=false_wait_labels,
    )

    assert false_wait_report["candidate_error_taxonomy_counts"] == {"false_wait": 1}
    assert false_wait_report["paired_comparisons"][0]["candidate_error_taxonomy"] == [
        "false_wait"
    ]


def test_paired_report_excludes_schema_rejected_candidate_from_ev():
    labels = [
        {
            **_pending(),
            "label_status": "mature",
            "source_quality_status": "pass",
            "primary_cohort_eligible": True,
            "horizon_metrics": {
                "10m": {
                    "end_return_pct": 2.0,
                    "first_hit": "target",
                }
            },
        }
    ]
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=[],
        results=[
            {
                "decision_trace_id": "trace-1",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "schema_rejected",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {"action": "BUY"},
            }
        ],
        labels=labels,
    )

    assert report["status"] == "candidate_rejected_no_runtime_apply"
    assert report["paired_comparable_count"] == 0
    assert report["candidate_source_quality_adjusted_ev_pct"] is None


def test_recovery_trigger_report_values_edge_wait_as_retained_observation():
    decision_ts = datetime(2026, 7, 29, 9, 0, 30, tzinfo=KST)
    price_rows = []
    for minute in range(1, 13):
        close = 100.5 if minute == 1 else (101.2 if minute == 2 else 103.0)
        price_rows.append(
            {
                "timestamp": datetime(
                    2026,
                    7,
                    29,
                    9,
                    minute,
                    tzinfo=KST,
                ).isoformat(),
                "stock_code": "005930",
                "price": close,
                "open": 101.5 if minute == 3 else close,
                "close": close,
                "high": close + 0.2,
                "low": close - 0.2,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "source_quality": "pass_completed_ka10080_bar",
            }
        )
    paired_report = {
        "requests": [
            {
                "decision_trace_id": "trace-recovery",
                "stock_code": "005930",
                "payload_sha256": "payload-recovery",
            }
        ],
        "results": [
            {
                "status": "pass",
                "decision_trace_id": "trace-recovery",
                "paired_replay_id": "pair-recovery",
                "payload_sha256": "payload-recovery",
                "control_response": {"action": "DROP"},
                "candidate_response": {
                    "edge_state": "EDGE",
                    "action": "WAIT",
                    "evidence": {
                        "setup": "pullback_recovery",
                        "adverse_risk": "moderate",
                        "trigger": "recovery_required",
                    },
                },
            }
        ],
    }
    labels = [
        {
            "decision_trace_id": "trace-recovery",
            "decision_ts": decision_ts.isoformat(),
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "source_quality_status": "pass",
            "primary_cohort_eligible": True,
            "decision_stage": "entry",
            "horizon_metrics": {
                "10m": {
                    "end_return_pct": 2.0,
                    "mfe_pct": 3.0,
                    "mae_pct": -0.5,
                }
            },
        }
    ]
    payloads = [
        {
            "payload_sha256": "payload-recovery",
            "endpoint": "analyze_target",
            "sanitized_user_input": {
                "current": {"price": 100},
                "features": {
                    "curr_vs_micro_vwap_bp": -100,
                    "curr_vs_ma5_bp": -50,
                },
                "entry_candle_context": {
                    "bars": [
                        {"c": 99, "l": 98, "forming": False},
                        {"c": 99.5, "l": 98.5, "forming": False},
                        {"c": 100, "l": 99, "forming": False},
                    ]
                },
            },
        }
    ]
    report = quality.build_recovery_trigger_report(
        target_date="2026-07-29",
        paired_report=paired_report,
        labels=labels,
        payloads=payloads,
        price_rows=price_rows,
    )

    assert report["status"] == "sample_floor_keep_collecting"
    assert report["eligible_row_count"] == 1
    assert report["recovery_trigger_count"] == 1
    assert report["control_drop_recovery_count"] == 1
    assert report["missed_upside_reduction_count"] == 1
    row = report["rows"][0]
    assert row["first_event"] == "recovery"
    assert row["recovery_trigger_at"] == "2026-07-29T09:02:00+09:00"
    assert row["recovery_entry_at"] == "2026-07-29T09:03:00+09:00"
    assert row["recovery_entry_price"] == 101.5
    assert row["candidate_conditional_decision_value_pct"] > 0
    assert row["counterfactual_only"] is True
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False

    missing_next_open_rows = [dict(price_row) for price_row in price_rows]
    missing_next_open_rows[2]["open"] = None
    missing_next_open_report = quality.build_recovery_trigger_report(
        target_date="2026-07-29",
        paired_report=paired_report,
        labels=labels,
        payloads=payloads,
        price_rows=missing_next_open_rows,
    )

    assert missing_next_open_report["rows"][0]["recovery_entry_at"] is None
    assert (
        missing_next_open_report["rows"][0]["candidate_conditional_decision_value_pct"]
        is None
    )
    assert missing_next_open_report["comparable_row_count"] == 0


def test_reversal_sequence_uses_only_predecision_state_and_dedupes_episode():
    def request(trace_id, payload_hash):
        return {
            "decision_trace_id": trace_id,
            "stock_code": "005930",
            "stage": "entry",
            "effective_venue": "KRX",
            "session_bucket": "krx_regular",
            "payload_sha256": payload_hash,
            "candidate_input_sha256": f"input-{payload_hash}",
            "candidate_exact_payload_sha256": payload_hash,
            "source_exact_payload_sha256": payload_hash,
            "candidate": {"prompt_version": "decision_quality_v2_9_1_entry"},
            "exact_payload_analysis": {
                "source_quality": {
                    "status": "fresh_consistent",
                    "completed_bar_count": 20,
                },
                "completed_structure": {
                    "phase": "failed_breakout",
                    "structural_edge": "moderate",
                    "returns_pct": {
                        "1m": -0.2,
                        "3m": -0.1,
                        "5m": 0.5,
                        "10m": 0.8,
                        "20m": 1.2,
                    },
                },
            },
            "anticipatory_reversal_analysis": {
                "execution_cost": {"conservative_execution_cost_pct": 0.2}
            },
        }

    def payload(
        trace_id,
        payload_hash,
        captured_at,
        *,
        price,
        net_delta,
        buy_pressure,
        absorption,
        price_change,
        ma5_distance,
        large_sell=False,
    ):
        return {
            "request_id": trace_id,
            "symbol": "005930",
            "effective_venue": "KRX",
            "session_bucket": "krx_regular",
            "captured_at": captured_at,
            "payload_sha256": payload_hash,
            "replay_exact": True,
            "sanitized_user_input": {
                "current": {
                    "price": price,
                    "fluctuation_pct": -1.0,
                    "execution_strength": 100.0,
                },
                "features": {
                    "net_aggressive_delta_10t": net_delta,
                    "buy_pressure_10t": buy_pressure,
                    "same_price_buy_absorption": absorption,
                    "price_change_10t_pct": price_change,
                    "curr_vs_ma5_bp": ma5_distance,
                    "curr_vs_micro_vwap_bp": ma5_distance,
                    "distance_from_day_high_pct": -2.0,
                    "large_sell_print_detected": large_sell,
                    "spread_bp": 70.0,
                    "orderbook_total_ratio": 1.0,
                    "fillability_score": 50.0,
                    "quote_fresh_for_entry": True,
                    "tick_context_stale": False,
                    "minute_candle_window_fresh": True,
                },
                "entry_candle_context": {
                    "schema": "entry_candle_context_v1",
                    "venue": "KRX",
                    "session": "krx_regular",
                    "completed_bar_count": 1,
                    "bars": [
                        {
                            "t": "2026-07-29T08:59:00+09:00",
                            "o": 100,
                            "h": 101,
                            "l": 99,
                            "c": 100,
                            "v": 1000,
                            "forming": False,
                        }
                    ],
                    "input_bundle_version": "scalping_multi_timeframe_context_v1",
                    "multi_timeframe_context": {
                        "previous_day_levels": {
                            "low": 100.0,
                            "close": 101.0,
                            "high": 102.0,
                        },
                        "session_bar_vwap": {"value": 100.0},
                    },
                },
            },
        }

    trace_ids = ("trace-armed", "trace-confirmed", "trace-invalidated")
    payload_hashes = ("payload-armed", "payload-confirmed", "payload-invalidated")
    paired_report = {
        "status": "paired_replay_complete_candidate_quality_rejected",
        "requests": [
            request(trace_id, payload_hash)
            for trace_id, payload_hash in zip(trace_ids, payload_hashes)
        ],
        "results": [
            {"status": "pass", "decision_trace_id": trace_id} for trace_id in trace_ids
        ],
        "paired_comparisons": [
            {
                "decision_trace_id": trace_id,
                "candidate_action": "DROP",
                "control_action": "WAIT",
            }
            for trace_id in trace_ids
        ],
    }
    payloads = [
        payload(
            trace_ids[0],
            payload_hashes[0],
            "2026-07-29T09:00:00+09:00",
            price=100.0,
            net_delta=-100,
            buy_pressure=30,
            absorption=2,
            price_change=0.1,
            ma5_distance=-50,
        ),
        payload(
            trace_ids[1],
            payload_hashes[1],
            "2026-07-29T09:01:00+09:00",
            price=99.8,
            net_delta=-50,
            buy_pressure=40,
            absorption=2,
            price_change=0.1,
            ma5_distance=-20,
        ),
        payload(
            trace_ids[2],
            payload_hashes[2],
            "2026-07-29T09:02:00+09:00",
            price=99.0,
            net_delta=-200,
            buy_pressure=20,
            absorption=0,
            price_change=-1.0,
            ma5_distance=-200,
            large_sell=True,
        ),
    ]

    def labels(end_return):
        return [
            {
                "decision_trace_id": trace_id,
                "label_id": f"label-{trace_id}",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "20m": {
                        "mfe_pct": 1.5,
                        "mae_pct": -0.5,
                        "end_return_pct": end_return,
                        "profit_opportunity_observed": True,
                        "profit_opportunity_sequence": (
                            "drawdown_then_profit_recovery"
                        ),
                    }
                },
            }
            for trace_id in trace_ids
        ]

    report = quality.build_entry_reversal_sequence_report(
        target_date="2026-07-29",
        paired_report=paired_report,
        labels=labels(1.0),
        payloads=payloads,
    )
    changed_outcome_report = quality.build_entry_reversal_sequence_report(
        target_date="2026-07-29",
        paired_report=paired_report,
        labels=labels(-5.0),
        payloads=payloads,
    )

    assert report["reversal_state_counts"] == {
        "ARMED": 1,
        "CONFIRMED": 1,
        "INVALIDATED": 1,
    }
    assert report["status"] == "sequence_hypothesis_keep_collecting"
    assert report["cohorts"]["reversal_armed"]["first_signal_episode_count"] == 1
    assert report["cohorts"]["reversal_confirmed"]["first_signal_episode_count"] == 1
    assert (
        report["cohorts"]["reversal_confirmed"]["first_signal_episode"]["20m"][
            "source_quality_adjusted_ev_pct"
        ]
        == 0.8
    )
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    scale_in = report["scale_in_counterfactual"]
    assert scale_in["status"] == "scale_in_economics_pass_offline_only"
    assert scale_in["pair_count"] == 1
    assert scale_in["primary_20m_pair_count"] == 1
    assert scale_in["economic_quality_pass"] is True
    assert scale_in["probe_learning_value_pass"] is False
    assert scale_in["rows"][0]["sizing_policy"] == (
        "one_share_probe_plus_one_share_confirmation"
    )
    assert scale_in["runtime_effect"] is False
    assert scale_in["allowed_runtime_apply"] is False
    one_share_probe = report["one_share_probe_counterfactual"]
    assert one_share_probe["first_signal_episode_count"] == 1
    assert one_share_probe["runtime_promotion"]["required_cap"] == (
        "one_share_probe_only"
    )
    assert one_share_probe["runtime_promotion"]["scale_in_authority"] is False
    assert one_share_probe["proposed_authority_separation"] == {
        "status": "offline_validated_not_runtime_applied",
        "entry_ai_role": "permissive_one_share_probe_intent",
        "upstream_policy": (
            "do_not_require_retrospective_economic_quality_pass_before_"
            "one_share_probe_intent"
        ),
        "upstream_required": (
            "exact_source_and_semantic_contract_without_known_hard_safety_block"
        ),
        "final_submit_authority": (
            "existing_freshness_price_broker_account_order_cooldown_quantity_"
            "and_hard_safety_guards"
        ),
        "economic_quality_role": "cumulative_post_outcome_learning_not_submit_veto",
        "submit_guard_is_not_directional_alpha_proof": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    assert one_share_probe["rows"][0]["decision_trace_id"] == "trace-armed"
    assert (
        one_share_probe["rows"][0]["horizons"]["20m"][
            "favorable_excursion_after_cost_observed"
        ]
        is True
    )
    assert one_share_probe["runtime_effect"] is False
    assert one_share_probe["allowed_runtime_apply"] is False
    assert all(
        row["source_quality"]["future_outcome_feature_count"] == 0
        for row in report["rows"]
    )
    assert all(
        row["source_quality"]["payload_venue_session_match"] is True
        and row["source_quality"]["canonical_raw_completed_bar_count"] == 1
        for row in report["rows"]
    )
    assert [
        (row["reversal_state"], row["sequence_context_sha256"])
        for row in report["rows"]
    ] == [
        (row["reversal_state"], row["sequence_context_sha256"])
        for row in changed_outcome_report["rows"]
    ]

    route_conflict_payloads = [dict(row) for row in payloads]
    route_conflict_payloads[0] = {
        **route_conflict_payloads[0],
        "effective_venue": "NXT",
    }
    route_conflict_report = quality.build_entry_reversal_sequence_report(
        target_date="2026-07-29",
        paired_report=paired_report,
        labels=labels(1.0),
        payloads=route_conflict_payloads,
    )
    assert route_conflict_report["exclusion_counts"] == {
        "payload_venue_session_contract_mismatch": 1
    }

    missing_source_report = quality.build_entry_reversal_sequence_report(
        target_date="2026-07-29",
        paired_report={},
        labels=labels(1.0),
        payloads=payloads,
    )
    assert missing_source_report["status"] == "sequence_source_artifact_missing"


def test_prepare_paired_replay_marks_stage_floor_without_cherry_picking():
    traces = []
    payloads = []
    labels = []
    for index in range(30):
        trace_id = f"trace-{index}"
        payload_hash = f"payload-{index}"
        stock_code = f"{index % 10 + 1:06d}"
        traces.append(
            {
                **_trace(),
                "decision_trace_id": trace_id,
                "payload_sha256": payload_hash,
            }
        )
        payloads.append(
            {
                **_payload(),
                "payload_sha256": payload_hash,
                "endpoint": "analyze_target",
            }
        )
        labels.append(
            {
                **_pending(),
                "decision_trace_id": trace_id,
                "label_id": f"{trace_id}:v1",
                "stock_code": stock_code,
                "label_status": "mature",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "10m": {"end_return_pct": 1.0, "first_hit": "target"}
                },
            }
        )
    control = quality.build_control_manifest(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=traces,
        payloads=payloads,
    )

    requests = quality.prepare_paired_replay_requests(
        control_manifest=control,
        traces=traces,
        payloads=payloads,
        labels=labels,
    )

    assert len(requests) == 30
    assert all(request["sample_floor"]["pass"] is True for request in requests)
    assert requests[0]["sample_floor"]["unique_symbols"] == 10
    assert requests[0]["sample_floor"]["floor_role"] == (
        "cumulative_learning_update_only"
    )
    assert requests[0]["sample_floor"]["promotion_evidence_floor"]["pass"] is True


def test_paired_replay_retries_schema_once_and_report_omits_exact_payload():
    request = {
        "paired_replay_id": "pair-1",
        "decision_trace_id": "trace-1",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "payload-1",
        "exact_payload": {"secret_free_exact": True},
        "candidate": {"system_prompt_sha256": "candidate-prompt-1"},
        **quality.OFFLINE_CONTRACT,
    }
    responses = [
        {"action": "WAIT"},
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.2,
            "expected_downside_pct": -0.4,
            "confidence": 55,
            "reason_codes": ["no_positive_edge"],
            "evidence": {
                "trend": "mixed",
                "liquidity": "supportive",
                "tape": "mixed",
                "risk": "medium",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "moderate",
                "trigger": "not_applicable",
            },
        },
    ]

    def candidate_runner(attempt_request):
        if len(responses) == 1:
            assert attempt_request["candidate_schema_correction_errors"]
        return responses.pop(0)

    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "DROP"},
        candidate_runner=candidate_runner,
    )
    report = quality.build_paired_replay_report(
        target_date="2026-07-27",
        requests=[request],
        results=results,
        labels=[],
    )

    assert results[0]["status"] == "pass"
    assert len(results[0]["candidate_attempts"]) == 2
    assert "exact_payload" not in report["requests"][0]
    assert report["candidate_provider_none_count"] == 0


def test_paired_replay_allows_bounded_third_semantic_correction():
    request = {
        "paired_replay_id": "pair-three-attempts",
        "decision_trace_id": "trace-three-attempts",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "payload-three-attempts",
        "exact_payload": {"secret_free_exact": True},
        "candidate": {"system_prompt_sha256": "candidate-prompt-three"},
        **quality.OFFLINE_CONTRACT,
    }
    valid_response = {
        "edge_state": "NO_EDGE",
        "action": "DROP",
        "expected_upside_pct": 0.2,
        "expected_downside_pct": -0.4,
        "confidence": 55,
        "reason_codes": ["no_positive_edge"],
        "evidence": {
            "trend": "mixed",
            "liquidity": "supportive",
            "tape": "mixed",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "no_setup",
            "positive_edge": "none",
            "adverse_risk": "moderate",
            "trigger": "not_applicable",
        },
    }
    responses = [
        {**valid_response, "action": "WAIT"},
        {
            **valid_response,
            "edge_state": "EDGE",
            "evidence": {
                **valid_response["evidence"],
                "setup": "continuation",
            },
        },
        valid_response,
    ]

    def candidate_runner(attempt_request):
        if len(responses) < 3:
            assert attempt_request["candidate_schema_correction_errors"]
        return responses.pop(0)

    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "DROP"},
        candidate_runner=candidate_runner,
    )

    assert results[0]["status"] == "pass"
    assert len(results[0]["candidate_attempts"]) == 3


def test_v2_14_invalid_setup_uses_fail_closed_ledger_citation_repair():
    setup_evidence = quality.build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            "schema": "exact_payload_analysis_v1",
            "source_quality": {
                "status": "fresh_consistent",
                "completed_bar_count": 20,
            },
            "executable_liquidity": {"execution_cost_state": "low"},
            "contradictions": ["multi_horizon_direction_conflict"],
            "deterministic_contract_facts": {
                "structural_edge_floor": True,
                "early_session_structural_edge_floor": False,
                "early_session_probe_candidate": False,
                "orderly_pullback_recovery": False,
                "trusted_supportive_trigger": True,
                "adverse_distribution_no_edge": False,
                "blocking_overextension": True,
                "ask_wall_wide_spread": False,
            },
        },
        recovery_analysis={
            "schema": "anticipatory_reversal_analysis_v1",
            "source_mode": "fresh_dual",
            "hard_blockers": [],
            "clean_continuation_probe": {"eligible": True},
            "recovery_confirmation_probe": {"eligible": False},
        },
    )
    invalid_response = {
        "schema": "entry_setup_risk_adjudication_v1",
        "risk_verdict": "VETO",
        "risk_codes": ["OVEREXTENSION_CHASE"],
        "supporting_fact_ids": ["structural_edge_floor"],
        "contradicting_fact_ids": ["multi_horizon_direction_conflict"],
        "confidence": 80,
    }
    request = {
        "paired_replay_id": "pair-v2-14-invalid",
        "decision_trace_id": "trace-v2-14-invalid",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "payload-v2-14-invalid",
        "entry_setup_evidence": setup_evidence,
        "candidate": {
            "semantic_validator_version": (
                quality.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
            ),
            "system_prompt_sha256": "candidate-prompt-v2-14",
        },
        **quality.OFFLINE_CONTRACT,
    }

    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _request: {"action": "WAIT"},
        candidate_runner=lambda _request: invalid_response,
    )

    assert results[0]["status"] == "pass"
    assert results[0]["candidate_response"]["action"] == "DROP"
    assert results[0]["candidate_semantic_repairs"] == [
        "invalid_setup_invalidation_fact_copied_from_ledger"
    ]
    assert len(results[0]["candidate_attempts"]) == (
        quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS + 1
    )
    repair_provenance = results[0]["candidate_attempts"][-1]["provider_provenance"]
    assert repair_provenance["provider"] == "deterministic_offline_adapter"
    assert repair_provenance["runtime_effect"] is False
    assert repair_provenance["semantic_repair_version"] == (
        quality.ENTRY_RISK_ADJUDICATION_REPAIR_VERSION
    )


def test_openai_candidate_parse_gap_is_retryable_and_secret_free(monkeypatch):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="resp-test",
                output_text="not-json",
                usage=SimpleNamespace(
                    input_tokens=12,
                    output_tokens=3,
                    total_tokens=15,
                ),
            )

    class FakeOpenAI:
        def __init__(self, *, api_key, max_retries):
            assert api_key == "test-secret"
            assert max_retries == 0
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    request = {
        "paired_replay_id": "pair-1",
        "stage": "entry",
        "exact_payload": {"value": 1},
        "control": {"provider": "openai", "model": "gpt-test"},
        "candidate": {
            "provider": "openai",
            "model": "gpt-test",
            "reasoning_effort": "minimal",
            "system_prompt": "Return JSON.",
            "max_output_tokens": 900,
        },
        **quality.OFFLINE_CONTRACT,
    }

    envelope = quality.execute_openai_prompt_v2_candidate(
        request,
        api_keys=["test-secret"],
    )

    assert envelope["candidate_response"] == {}
    assert envelope["provider_provenance"]["parse_error"] == (
        "candidate_response_json_invalid"
    )
    assert envelope["provider_provenance"]["response_id"] == "resp-test"
    assert "test-secret" not in str(envelope)
    assert captured["store"] is False
    assert captured["input"] == '{"value":1}'
    assert captured["max_output_tokens"] == 900
    assert captured["reasoning"] == {"effort": "minimal"}
    assert envelope["provider_provenance"]["reasoning_effort"] == "minimal"
    output_schema = captured["text"]["format"]["schema"]
    assert output_schema["properties"]["expected_upside_pct"]["minimum"] == 0
    assert output_schema["properties"]["expected_downside_pct"]["maximum"] == 0
    assert captured["metadata"]["candidate_contract_sha256"]


def test_v2_12_semantic_correction_preserves_nonblocking_wait(monkeypatch):
    captured = {}
    response = {
        "edge_state": "EDGE",
        "action": "WAIT",
        "expected_upside_pct": 0.8,
        "expected_downside_pct": -0.7,
        "confidence": 55,
        "reason_codes": ["recovery_trigger_required"],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "recovery_required",
        },
    }

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="resp-v2-12-correction",
                output_text=json.dumps(response),
                usage=SimpleNamespace(
                    input_tokens=10,
                    output_tokens=10,
                    total_tokens=20,
                ),
            )

    class FakeOpenAI:
        def __init__(self, *, api_key, max_retries):
            assert api_key == "test-secret"
            assert max_retries == 0
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    request = {
        "paired_replay_id": "pair-v2-12-correction",
        "stage": "entry",
        "exact_payload": {"value": 1},
        "candidate_schema_correction_errors": [
            "entry_trusted_supportive_trigger_misclassified",
            "entry_edge_drop_requires_failed_blocking_or_unfavorable",
        ],
        "control": {"provider": "openai", "model": "gpt-test"},
        "candidate": {
            "provider": "openai",
            "model": "gpt-test",
            "system_prompt": "V2.12 base prompt.",
            "max_output_tokens": 900,
            "prompt_version": (
                f"{quality.DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}"
                "_entry"
            ),
            "semantic_validator_version": (
                quality.BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
            ),
        },
        **quality.OFFLINE_CONTRACT,
    }

    quality.execute_openai_prompt_v2_candidate(
        request,
        api_keys=["test-secret"],
    )

    instructions = captured["instructions"]
    assert "For V2.12" in instructions
    assert "WAIT with trigger=recovery_required" in instructions
    assert "WAIT is prohibited for this contract" not in instructions


def test_v2_14_correction_names_mandatory_invalidation_fact_path(monkeypatch):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="resp-v2-14-correction",
                output_text=json.dumps(
                    {
                        "schema": "entry_setup_risk_adjudication_v1",
                        "risk_verdict": "VETO",
                        "risk_codes": ["STRUCTURE_INVALIDATED"],
                        "supporting_fact_ids": [],
                        "contradicting_fact_ids": ["no_supported_setup"],
                        "confidence": 80,
                    }
                ),
                usage=SimpleNamespace(
                    input_tokens=10,
                    output_tokens=10,
                    total_tokens=20,
                ),
            )

    class FakeOpenAI:
        def __init__(self, *, api_key, max_retries):
            assert api_key == "test-secret"
            assert max_retries == 0
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    request = {
        "paired_replay_id": "pair-v2-14-correction",
        "stage": "entry",
        "candidate_input": {"entry_setup_evidence_v1": {"setup_state": "INVALID"}},
        "candidate_schema_correction_errors": [
            "entry_risk_invalid_setup_invalidation_fact_required"
        ],
        "control": {"provider": "openai", "model": "gpt-test"},
        "candidate": {
            "provider": "openai",
            "model": "gpt-test",
            "system_prompt": "V2.14 base prompt.",
            "max_output_tokens": 900,
            "prompt_version": "decision_quality_v2_14_setup_risk_entry",
            "semantic_validator_version": (
                quality.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
            ),
        },
        **quality.OFFLINE_CONTRACT,
    }

    quality.execute_openai_prompt_v2_candidate(
        request,
        api_keys=["test-secret"],
    )

    instructions = captured["instructions"]
    assert "entry_setup_evidence_v1.invalidation_facts" in instructions
    assert "A contradicting_facts-only citation" in instructions


def test_candidate_execution_checkpoint_is_outcome_blind_and_symbol_diverse():
    pending = [
        {
            "paired_replay_id": f"pair-{index}",
            "decision_trace_id": f"trace-{index}",
            "stock_code": "000001" if index < 8 else f"{index:06d}",
            "stage": "entry",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "outcome_return_pct": 99 if index == 0 else -99,
        }
        for index in range(12)
    ]

    selected, metadata = quality.select_pending_candidate_execution_requests(
        pending,
        max_new_requests=5,
    )
    reranked, reranked_metadata = quality.select_pending_candidate_execution_requests(
        [{**row, "outcome_return_pct": -row["outcome_return_pct"]} for row in pending],
        max_new_requests=5,
    )

    assert [row["paired_replay_id"] for row in selected] == [
        row["paired_replay_id"] for row in reranked
    ]
    assert len({row["stock_code"] for row in selected}) == 5
    assert metadata["policy"] == quality.CANDIDATE_EXECUTION_SELECTION_POLICY
    assert metadata["outcome_blind"] is True

    assert metadata["contract_pass"] is True
    assert reranked_metadata["forbidden_selection_fields"] == [
        "outcome_return_pct",
        "outcome_mfe_pct",
        "outcome_mae_pct",
        "first_hit",
        "profit_opportunity_observed",
    ]


def test_candidate_execution_checkpoint_prioritizes_ready_without_using_outcomes():
    pending = []
    for state, count in (("READY", 12), ("WAIT_CONFIRMATION", 12), ("INVALID", 12)):
        for index in range(count):
            pending.append(
                {
                    "paired_replay_id": f"{state}-{index}",
                    "decision_trace_id": f"trace-{state}-{index}",
                    "stock_code": f"{index + (100 if state == 'READY' else 200):06d}",
                    "stage": "entry",
                    "effective_venue": "KRX",
                    "session_bucket": "KRX_REGULAR",
                    "entry_setup_evidence": {"setup_state": state},
                    "outcome_return_pct": 99 if state == "INVALID" else -99,
                }
            )

    selected, metadata = quality.select_pending_candidate_execution_requests(
        pending,
        max_new_requests=10,
    )

    assert len(selected) == 10
    assert metadata["selected_setup_state_counts"] == {
        "READY": 6,
        "WAIT_CONFIRMATION": 3,
        "OTHER": 1,
    }
    assert metadata["outcome_blind"] is True

    one, one_metadata = quality.select_pending_candidate_execution_requests(
        pending,
        max_new_requests=1,
    )
    assert (one[0]["entry_setup_evidence"] or {})["setup_state"] == "READY"
    assert one_metadata["selected_setup_state_counts"] == {"READY": 1}


def test_candidate_execution_checkpoint_retry_does_not_expand_distinct_quota():
    pending = [
        {
            "paired_replay_id": f"pair-{index}",
            "decision_trace_id": f"trace-{index}",
            "stock_code": f"{index:06d}",
            "stage": "entry",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
        }
        for index in range(40)
    ]
    attempted_ids = {f"pair-{index}" for index in range(30)}
    failed_ids = {"pair-4", "pair-17"}
    retry_pending = [
        row
        for row in pending
        if row["paired_replay_id"] in failed_ids
        or row["paired_replay_id"] not in attempted_ids
    ]

    selected, metadata = quality.select_pending_candidate_execution_requests(
        retry_pending,
        max_new_requests=30,
        previously_attempted_pair_ids=attempted_ids,
    )

    assert {row["paired_replay_id"] for row in selected} == failed_ids
    assert metadata["retry_selected_count"] == 2
    assert metadata["selected_new_count"] == 0
    assert metadata["deferred_new_count"] == 10
    assert metadata["distinct_execution_count"] == 30
    assert metadata["distinct_execution_cap_pass"] is True
    assert metadata["contract_pass"] is True


def test_complete_candidate_census_contract_is_bounded_and_tamper_evident():
    pending = [
        {
            "paired_replay_id": f"pair-{index}",
            "stock_code": f"{index:06d}",
        }
        for index in range(3)
    ]
    _selected, metadata = quality.select_pending_candidate_execution_requests(
        pending,
        max_new_requests=5,
    )

    assert metadata["policy"] == "complete_eligible_census"
    assert quality.candidate_execution_selection_contract_pass(
        metadata,
        max_new_requests=5,
    )
    assert not quality.candidate_execution_selection_contract_pass(
        {**metadata, "deferred_new_count": 1},
        max_new_requests=5,
    )
    assert not quality.candidate_execution_selection_contract_pass(
        {**metadata, "distinct_execution_count": 6},
        max_new_requests=5,
    )


def test_round_robin_candidate_selection_contract_rejects_census_or_cap_drift():
    pending = [
        {
            "paired_replay_id": f"pair-{index}",
            "stock_code": f"{index:06d}",
        }
        for index in range(8)
    ]
    _selected, metadata = quality.select_pending_candidate_execution_requests(
        pending,
        max_new_requests=5,
    )

    assert metadata["policy"] == quality.CANDIDATE_EXECUTION_SELECTION_POLICY
    assert quality.candidate_execution_selection_contract_pass(
        metadata,
        max_new_requests=5,
    )
    assert not quality.candidate_execution_selection_contract_pass(
        {**metadata, "deferred_new_count": 2},
        max_new_requests=5,
    )
    assert not quality.candidate_execution_selection_contract_pass(
        {**metadata, "distinct_execution_cap": 6},
        max_new_requests=5,
    )
    assert not quality.candidate_execution_selection_contract_pass(
        {**metadata, "distinct_execution_count": 6},
        max_new_requests=5,
    )


def test_stale_selection_policy_does_not_consume_new_checkpoint_quota():
    existing = {
        "requests": [
            {"paired_replay_id": "old-1"},
            {"paired_replay_id": "old-2"},
            {"paired_replay_id": "not-current"},
        ]
    }

    stale = quality._valid_checkpoint_attempted_pair_ids(
        existing,
        valid_pair_ids={"old-1", "old-2"},
        selection_contract_pass=False,
    )
    current = quality._valid_checkpoint_attempted_pair_ids(
        existing,
        valid_pair_ids={"old-1", "old-2"},
        selection_contract_pass=True,
    )

    assert stale == set()
    assert current == {"old-1", "old-2"}


def test_checkpoint_setup_state_counts_preserve_full_retry_census():
    requests = [
        {"entry_setup_evidence": {"setup_state": "READY"}},
        {"entry_setup_evidence": {"setup_state": "WAIT_CONFIRMATION"}},
        {"entry_setup_evidence": {"setup_state": "INVALID"}},
        {"entry_setup_evidence": {"setup_state": "READY"}},
    ]

    assert quality._checkpoint_setup_state_counts(requests) == {
        "READY": 2,
        "WAIT_CONFIRMATION": 1,
        "OTHER": 1,
    }


def test_opportunity_capture_gate_allows_positive_incremental_probe_with_guarded_risk():
    rows = [
        {
            "stock_code": "000001",
            "control_exposure_selected": False,
            "candidate_exposure_selected": True,
            "control_primary_decision_value_pct": 0.0,
            "candidate_primary_decision_value_pct": 0.4,
            "control_missed_upside": True,
            "candidate_missed_upside": False,
        },
        {
            "stock_code": "000002",
            "control_exposure_selected": True,
            "candidate_exposure_selected": False,
            "control_primary_decision_value_pct": 0.1,
            "candidate_primary_decision_value_pct": 0.0,
            "control_missed_upside": False,
            "candidate_missed_upside": True,
        },
    ]

    tradeoff = quality._opportunity_capture_tradeoff(rows)

    assert tradeoff["incremental_candidate_exposure_count"] == 1
    assert tradeoff["incremental_candidate_exposure_cost_adjusted_ev_pct"] == 0.4
    assert tradeoff["forgone_control_exposure_count"] == 1
    assert tradeoff["net_missed_upside_reduction_count"] == 0
    assert tradeoff["net_missed_upside_value_pct"] == pytest.approx(0.3)
    assert tradeoff["opportunity_capture_expanded"] is True
    assert tradeoff["missed_upside_tradeoff_not_worse"] is True


def test_entry_opportunity_funnel_uses_full_prepared_census_before_ai_budget():
    def label(
        trace_id: str,
        *,
        action: str,
        first_hit: str,
        profit_opportunity: bool,
    ) -> dict:
        return {
            "decision_trace_id": trace_id,
            "decision_stage": "entry",
            "decision_ts": f"2026-08-07T09:0{trace_id[-1]}:00+09:00",
            "stock_code": f"00000{trace_id[-1]}",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "action": action,
            "label_status": "mature",
            "source_quality_status": "pass",
            "primary_cohort_eligible": True,
            "horizon_metrics": {
                "10m": {
                    "end_return_pct": 0.4,
                    "mfe_pct": 1.2 if profit_opportunity else 0.2,
                    "mae_pct": -0.2,
                    "first_hit": "neither",
                    "entry_path_first_hit": first_hit,
                    "entry_path_target_pct": 0.3,
                    "entry_path_adverse_pct": -0.7,
                    "profit_opportunity_observed": profit_opportunity,
                }
            },
        }

    prepared = [
        {
            "decision_trace_id": "trace-1",
            "paired_replay_id": "pair-1",
            "decision_ts": "2026-08-07T09:01:00+09:00",
            "stage": "entry",
            "stock_code": "000001",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_setup_evidence": {"setup_state": "READY"},
        },
        {
            "decision_trace_id": "trace-2",
            "paired_replay_id": "pair-2",
            "decision_ts": "2026-08-07T09:02:00+09:00",
            "stage": "entry",
            "stock_code": "000002",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_setup_evidence": {"setup_state": "READY"},
        },
        {
            "decision_trace_id": "trace-3",
            "paired_replay_id": "pair-3",
            "decision_ts": "2026-08-07T09:03:00+09:00",
            "stage": "entry",
            "stock_code": "000003",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_setup_evidence": {"setup_state": "WAIT_CONFIRMATION"},
        },
    ]
    prepared.append(
        {
            **prepared[1],
            "paired_replay_id": "pair-2-conflict",
            "entry_setup_evidence": {"setup_state": "WAIT_CONFIRMATION"},
        }
    )
    evaluated = [prepared[0], prepared[2]]
    results = [
        {
            "decision_trace_id": request["decision_trace_id"],
            "paired_replay_id": request["paired_replay_id"],
            "stage": "entry",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "status": "pass",
            "same_payload_confirmed": True,
            "control_response": {"action": "DROP"},
            "candidate_response": {
                "action": "WAIT",
                "entry_setup_state": ("READY" if index == 0 else "WAIT_CONFIRMATION"),
                "entry_probe_intent": True,
                "entry_probe_intent_status": "eligible_wait_probe",
            },
        }
        for index, request in enumerate(evaluated)
    ]

    report = quality.build_paired_replay_report(
        target_date="2026-08-07",
        requests=evaluated,
        prepared_requests=prepared,
        results=results,
        labels=[
            label(
                "trace-1",
                action="DROP",
                first_hit="target_first",
                profit_opportunity=True,
            ),
            label(
                "trace-2",
                action="WAIT",
                first_hit="adverse_first",
                profit_opportunity=False,
            ),
            label(
                "trace-3",
                action="DROP",
                first_hit="target_first",
                profit_opportunity=True,
            ),
        ],
    )

    funnel = report["entry_opportunity_funnel"]
    assert funnel["cohort_count"] == 1
    cohort = funnel["cohorts"][0]
    assert cohort["eligible_decision_event_count"] == 3
    assert cohort["prepared_setup_decision_count"] == 3
    assert cohort["prepared_setup_state_counts"] == {
        "READY": 1,
        "WAIT_CONFIRMATION": 1,
        "CONFLICT": 1,
    }
    assert cohort["prepared_setup_state_conflict_count"] == 1
    assert cohort["candidate_evaluated_decision_count"] == 2
    assert cohort["candidate_execution_attempted_decision_count"] == 2
    assert cohort["candidate_execution_status_counts"] == {"pass": 2}
    assert cohort["candidate_evaluation_coverage_pct"] == pytest.approx(2 / 3 * 100)
    assert cohort["control_target_first_capture_rate_pct"] == 0
    assert cohort["candidate_evaluated_target_first_count"] == 2
    assert cohort["candidate_target_first_capture_rate_pct"] == 0
    assert cohort["target_first_first_blocker_counts"] == {
        "bounded_probe_arm_pending_recheck": 1,
        "deterministic_setup_wait_confirmation": 1,
    }


def test_entry_opportunity_funnel_separates_provider_failure_from_budget_defer():
    trace_id = "provider-failed-trace"
    funnel = quality._entry_opportunity_funnel_attribution(
        labels=[
            {
                "decision_trace_id": trace_id,
                "decision_stage": "entry",
                "stock_code": "005930",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "action": "WAIT",
                "source_quality_status": "pass",
                "primary_cohort_eligible": True,
                "horizon_metrics": {
                    "10m": {
                        "entry_path_first_hit": "target_first",
                        "profit_opportunity_observed": True,
                    }
                },
            }
        ],
        prepared_requests=[
            {
                "decision_trace_id": trace_id,
                "stage": "entry",
                "entry_setup_evidence": {"setup_state": "READY"},
            }
        ],
        comparable_rows=[],
        results=[
            {
                "decision_trace_id": trace_id,
                "stage": "entry",
                "status": "provider_failed",
            }
        ],
        candidate_execution_requested=True,
    )

    cohort = funnel["cohorts"][0]
    assert cohort["candidate_execution_attempted_decision_count"] == 1
    assert cohort["candidate_evaluated_decision_count"] == 0
    assert cohort["candidate_execution_status_counts"] == {"provider_failed": 1}
    assert cohort["first_blocker_counts"] == {"candidate_provider_failed": 1}


def test_probe_arm_continuity_finds_ready_followup_deferred_by_ai_budget():
    prepared = [
        {
            "decision_trace_id": "wait-trace",
            "paired_replay_id": "wait-pair",
            "decision_ts": "2026-08-07T09:00:00+09:00",
            "stage": "entry",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_setup_evidence": {"setup_state": "READY"},
        },
        {
            "decision_trace_id": "ready-followup-trace",
            "paired_replay_id": "ready-followup-pair",
            "decision_ts": "2026-08-07T09:02:00+09:00",
            "stage": "entry",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_setup_evidence": {"setup_state": "READY"},
        },
    ]
    label = {
        "decision_trace_id": "wait-trace",
        "decision_stage": "entry",
        "decision_ts": "2026-08-07T09:00:00+09:00",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "action": "DROP",
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 0.8,
                "mfe_pct": 1.2,
                "mae_pct": -0.1,
                "first_hit": "target",
                "entry_path_first_hit": "target_first",
                "entry_path_target_pct": 0.3,
                "entry_path_adverse_pct": -0.7,
            }
        },
    }
    report = quality.build_paired_replay_report(
        target_date="2026-08-07",
        requests=[prepared[0]],
        prepared_requests=prepared,
        results=[
            {
                "decision_trace_id": "wait-trace",
                "paired_replay_id": "wait-pair",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {
                    "action": "WAIT",
                    "entry_setup_state": "READY",
                    "entry_ai_risk_verdict": "CAUTION",
                    "entry_probe_intent": True,
                    "entry_probe_intent_status": "eligible_wait_probe",
                    "entry_recheck_intent": False,
                },
            }
        ],
        labels=[label],
    )

    continuity = report["entry_probe_arm_continuity"]
    assert continuity["waiting_decision_count"] == 1
    assert continuity["followup_observed_count"] == 1
    assert continuity["ready_followup_observed_count"] == 1
    assert continuity["ready_followup_candidate_budget_deferred_count"] == 1
    assert continuity["status_counts"] == {
        "ready_followup_candidate_budget_deferred": 1
    }
    assert continuity["initial_risk_verdict_counts"] == {"CAUTION": 1}
    assert continuity["transition_status_by_initial_risk_verdict"] == {
        "CAUTION": {"ready_followup_candidate_budget_deferred": 1}
    }
    comparison = report["paired_comparisons"][0]
    assert comparison["entry_probe_arm_continuity_followup_trace_id"] == (
        "ready-followup-trace"
    )
    assert report["entry_recheck_attribution"]["candidate_recheck_intent_count"] == 0


def test_sequential_recovery_arms_only_after_all_next_exact_conditions_pass():
    seed = {
        "decision_trace_id": "seed-trace",
        "decision_ts": "2026-08-12T10:00:00+09:00",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "entry_structure_phase_bar_end": "2026-08-12T09:59:00+09:00",
        "reference_price": 100.0,
        "conservative_spread_bp": 20.0,
        "conservative_execution_cost_pct": 0.12,
    }
    comparison = {
        "decision_trace_id": "confirmed-trace",
        "stock_code": "005930",
        "outcome_return_pct": 1.2,
        "conservative_execution_cost_pct": 0.10,
        "entry_path_first_hit": "target_first",
        "probe_severe_tail_adverse": False,
        "probe_worst_loss_pct": -0.2,
    }
    observations = [
        {
            "decision_trace_id": "same-bar-trace",
            "decision_ts": "2026-08-12T10:00:30+09:00",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "structure_phase_bar_end": "2026-08-12T09:59:00+09:00",
            "reference_price": 101.0,
            "spread_bp": 18.0,
            "conservative_execution_cost_pct": 0.10,
            "sell_momentum_decelerating": True,
            "hard_blockers": [],
            "source_quality_status": "fresh_consistent",
            "candidate_evaluated": False,
        },
        {
            "decision_trace_id": "confirmed-trace",
            "decision_ts": "2026-08-12T10:01:10+09:00",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "structure_phase_bar_end": "2026-08-12T10:00:00+09:00",
            "reference_price": 100.5,
            "spread_bp": 19.0,
            "conservative_execution_cost_pct": 0.10,
            "sell_momentum_decelerating": True,
            "hard_blockers": [],
            "source_quality_status": "fresh_consistent",
            "candidate_evaluated": True,
            "comparison_row": comparison,
        },
    ]

    summary = quality._attach_sequential_recovery_transitions(
        seed_rows=[seed], observations=observations
    )

    assert seed["entry_sequential_recovery_probe_armed"] is True
    assert seed["entry_sequential_recovery_followup_trace_id"] == "confirmed-trace"
    assert summary["confirmed_arm_count"] == 1
    assert summary["outcome_joined_arm_count"] == 1
    assert summary["probe_cost_adjusted_ev_pct"] == pytest.approx(1.1)
    assert summary["target_first_count"] == 1
    assert summary["runtime_effect"] is False
    assert summary["broker_order_forbidden"] is True


def test_sequential_recovery_rejects_worse_cost_or_hard_blocker():
    seed = {
        "decision_trace_id": "seed-trace",
        "decision_ts": "2026-08-12T10:00:00+09:00",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "entry_structure_phase_bar_end": "2026-08-12T09:59:00+09:00",
        "reference_price": 100.0,
        "conservative_spread_bp": 20.0,
        "conservative_execution_cost_pct": 0.12,
    }
    observations = [
        {
            "decision_trace_id": "blocked-trace",
            "decision_ts": "2026-08-12T10:01:10+09:00",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "structure_phase_bar_end": "2026-08-12T10:00:00+09:00",
            "reference_price": 101.0,
            "spread_bp": 21.0,
            "conservative_execution_cost_pct": 0.13,
            "sell_momentum_decelerating": True,
            "hard_blockers": ["large_sell_print_present"],
            "source_quality_status": "fresh_consistent",
            "candidate_evaluated": False,
        }
    ]

    summary = quality._attach_sequential_recovery_transitions(
        seed_rows=[seed], observations=observations
    )

    assert seed["entry_sequential_recovery_probe_armed"] is False
    assert summary["confirmed_arm_count"] == 0
    assert summary["status_counts"] == {"followup_observed_not_confirmed": 1}
    assert set(summary["confirmation_failure_counts"]) == {
        "spread_worsened_or_missing",
        "execution_cost_worsened_or_missing",
        "hard_blocker_present",
    }


def test_entry_lifecycle_replay_separates_path_proxy_from_natural_realized_pnl(
    monkeypatch,
):
    monkeypatch.setattr(
        quality,
        "_entry_lifecycle_source_inventory",
        lambda _target_date: [],
    )
    request = {
        "decision_trace_id": "lifecycle-trace",
        "paired_replay_id": "lifecycle-pair",
        "decision_ts": "2026-08-07T09:00:00+09:00",
        "stage": "entry",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "candidate": {
            "exposure_semantics": "offline_counterfactual_passive_probe_only"
        },
        "anticipatory_reversal_analysis": {
            "execution_cost": {"conservative_execution_cost_pct": 0.1}
        },
        "entry_setup_evidence": {"setup_state": "READY"},
    }
    label = {
        "decision_trace_id": "lifecycle-trace",
        "decision_stage": "entry",
        "decision_ts": "2026-08-07T09:00:00+09:00",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "action": "DROP",
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "correlation": {
            "status": "exact_matched",
            "actual_order_submitted": True,
            "fill_observed": True,
            "realized_profit_pct": 0.4,
            "position_cycle_ids": ["cycle-1"],
            "probe_bundle_ids": ["probe-1"],
            "broker_order_nos": ["order-1"],
            "lifecycle_stage_presence": {
                "probe": True,
                "post_probe": True,
                "residual_multi_leg": False,
                "scale_in": False,
                "exit": True,
            },
        },
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 0.1,
                "mfe_pct": 1.0,
                "mae_pct": -0.1,
                "first_hit": "target",
                "entry_path_first_hit": "target_first",
                "entry_path_target_pct": 0.3,
                "entry_path_adverse_pct": -0.7,
            }
        },
    }
    report = quality.build_paired_replay_report(
        target_date="2026-08-07",
        requests=[request],
        prepared_requests=[request],
        results=[
            {
                "decision_trace_id": "lifecycle-trace",
                "paired_replay_id": "lifecycle-pair",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "DROP"},
                "candidate_response": {
                    "action": "BUY",
                    "entry_setup_state": "READY",
                    "entry_probe_intent": True,
                    "entry_probe_intent_status": "eligible_offline_probe",
                },
            }
        ],
        labels=[label],
    )

    lifecycle = report["entry_lifecycle_replay"]
    assert lifecycle["candidate_probe_path_proxy_source_quality_adjusted_ev_pct"] == (
        pytest.approx(0.2)
    )
    assert lifecycle["observed_natural_lifecycle"]["deduped_lifecycle_count"] == 1
    assert lifecycle["observed_natural_lifecycle"][
        "realized_profit_equal_weight_avg_profit_pct"
    ] == pytest.approx(0.4)
    assert (
        lifecycle["observed_natural_lifecycle"][
            "candidate_counterfactual_attribution_allowed"
        ]
        is False
    )
    assert lifecycle["replay_component_status"]["residual_multi_leg"] == (
        "not_counterfactually_replayed"
    )
    assert lifecycle["full_lifecycle_counterfactual_status"] == (
        "source_state_missing_instrumentation_gap"
    )
    assert lifecycle["full_lifecycle_counterfactual_ev_pct"] is None
    source_audit = lifecycle["candidate_full_lifecycle_source_audit"]
    assert source_audit["candidate_probe_or_exposure_count"] == 1
    assert source_audit["candidate_state_row_count"] == 0
    assert source_audit["full_lifecycle_evaluable_candidate_count"] == 0
    assert not any(
        row["candidate_exact_state_authority"]
        for row in source_audit["source_inventory"]
    )


def test_entry_lifecycle_source_inventory_keeps_adjacent_reports_non_authoritative(
    tmp_path, monkeypatch
):
    pyramid_dir = tmp_path / "pyramid"
    scale_in_dir = tmp_path / "scale-in"
    split_dir = tmp_path / "split"
    for path in (pyramid_dir, scale_in_dir, split_dir):
        path.mkdir()
    (pyramid_dir / "scalping_pyramid_intraday_feedback_2026-08-07.json").write_text(
        json.dumps(
            {
                "schema_version": "pyramid_v1",
                "runtime_effect": False,
                "summary": {
                    "one_share_event_count": 1,
                    "probe_residual_real_outcome_closed_count": 1,
                    "whole_day_real_entry_lifecycle": {
                        "filled_cycle_count": 1,
                        "closed_cycle_count": 1,
                    },
                    "real_scale_in_performance": {"execution_count": 1},
                },
            }
        ),
        encoding="utf-8",
    )
    (scale_in_dir / "scale_in_incremental_counterfactual_2026-08-07.json").write_text(
        json.dumps(
            {
                "schema_version": "scale_in_v1",
                "runtime_effect": False,
                "status": "pass",
                "summary": {
                    "candidate_activity_count": 2,
                    "eligible_candidate_count": 1,
                    "counterfactual_event_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    (split_dir / "entry_split_order_plan_2026-08-07.json").write_text(
        json.dumps(
            {
                "schema_version": "split_v1",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "candidate_grid": [{"legs": 2}],
                "recommended_policy": {"legs": 2},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(quality, "PYRAMID_FEEDBACK_REPORT_DIR", pyramid_dir)
    monkeypatch.setattr(quality, "SCALE_IN_COUNTERFACTUAL_REPORT_DIR", scale_in_dir)
    monkeypatch.setattr(quality, "ENTRY_SPLIT_ORDER_PLAN_REPORT_DIR", split_dir)
    monkeypatch.setattr(
        quality,
        "candidate_lifecycle_report_path",
        lambda _target_date: tmp_path / "missing_candidate_state.json",
    )

    inventory = quality._entry_lifecycle_source_inventory("2026-08-07")

    assert len(inventory) == 4
    assert inventory[0]["status"] == "missing_or_unreadable"
    assert all(row["status"] == "available" for row in inventory[1:])
    assert not any(row["candidate_exact_state_authority"] for row in inventory)
    assert inventory[1]["evidence"]["natural_closed_cycle_count"] == 1
    assert inventory[2]["evidence"]["counterfactual_event_count"] == 1
    assert inventory[3]["evidence"]["candidate_policy_count"] == 1


def test_entry_lifecycle_source_audit_requires_exact_candidate_lineage():
    state = {
        "schema": "entry_candidate_lifecycle_state_v1",
        "source_quality_status": "pass",
        "decision_trace_id": "trace-1",
        "paired_replay_id": "wrong-pair",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "probe": {"status": "filled"},
        "post_probe": {"status": "evaluated"},
        "residual_multi_leg": {"status": "terminal_submitted"},
        "scale_in": {"status": "evaluated_not_submitted"},
        "holding_exit": {"status": "terminal_exit_filled"},
        "economics": {"status": "complete"},
    }
    row = {
        "decision_trace_id": "trace-1",
        "paired_replay_id": "pair-1",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "candidate_exposure_selected": True,
        "candidate_counterfactual_lifecycle_state": state,
    }

    mismatched = quality._entry_candidate_lifecycle_source_audit(
        [row], source_inventory=[]
    )
    assert mismatched["status"] == "source_state_missing_instrumentation_gap"
    assert mismatched["full_lifecycle_evaluable_candidate_count"] == 0

    state["paired_replay_id"] = "pair-1"
    exact = quality._entry_candidate_lifecycle_source_audit([row], source_inventory=[])
    assert exact["status"] == (
        "exact_candidate_owned_state_source_available_not_yet_evaluated"
    )
    assert exact["full_lifecycle_evaluable_candidate_count"] == 1


def test_attach_entry_candidate_lifecycle_state_requires_exact_route(monkeypatch):
    state = {
        "schema": "entry_candidate_lifecycle_state_v1",
        "decision_trace_id": "trace-1",
        "paired_replay_id": "pair-1",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "lifecycle_basis": "observed_live_candidate",
    }
    monkeypatch.setattr(
        quality,
        "load_candidate_state_index",
        lambda *_args, **_kwargs: {("trace-1", "pair-1", "KRX", "krx_regular"): state},
    )
    rows = [
        {
            "decision_trace_id": "trace-1",
            "paired_replay_id": "pair-1",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "candidate_probe_armed": True,
        },
        {
            "decision_trace_id": "trace-1",
            "paired_replay_id": "pair-1",
            "effective_venue": "NXT",
            "session_bucket": "NXT_ENTRY_WINDOW",
            "candidate_probe_armed": True,
        },
    ]

    result = quality._attach_entry_candidate_lifecycle_states(
        rows, target_date="2026-08-07"
    )

    assert result["candidate_state_attached_count"] == 1
    assert rows[0]["candidate_counterfactual_lifecycle_state"] == state
    assert "candidate_counterfactual_lifecycle_state" not in rows[1]


def test_lifecycle_correlation_does_not_count_post_probe_as_initial_probe():
    correlation = quality._correlation(
        {
            "decision_trace_id": "trace-post-probe-only",
            "decision_stage": "entry",
            "decision_ts": "2026-08-07T09:00:00+09:00",
            "stock_code": "005930",
        },
        [
            {
                "timestamp": "2026-08-07T09:01:00+09:00",
                "stage": "post_probe_recheck",
                "stock_code": "005930",
                "decision_trace_id": "trace-post-probe-only",
                "actual_order_submitted": False,
                "filled": False,
                "realized_profit_pct": None,
            }
        ],
    )

    assert correlation["status"] == "exact_matched"
    assert correlation["lifecycle_stage_presence"]["probe"] is False
    assert correlation["lifecycle_stage_presence"]["post_probe"] is True


def _reattribution_fixture(tmp_path, monkeypatch):
    request = {
        "decision_trace_id": "reattribute-trace",
        "paired_replay_id": "reattribute-pair",
        "decision_ts": "2026-08-06T09:00:00+09:00",
        "stage": "entry",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "payload-reattribute",
        "candidate_input_sha256": "input-reattribute",
        "exact_payload_analysis_sha256": "exact-analysis-reattribute",
        "anticipatory_reversal_analysis_sha256": "anticipatory-reattribute",
        "entry_setup_evidence_sha256": "setup-reattribute",
        "entry_setup_evidence": {"setup_state": "READY"},
        "candidate": {
            "prompt_version": (
                f"{quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION}_entry"
            ),
            "system_prompt_sha256": "prompt-reattribute",
            "model": "gpt-test",
            "exposure_semantics": "offline_counterfactual_passive_probe_only",
        },
        "anticipatory_reversal_analysis": {
            "execution_cost": {"conservative_execution_cost_pct": 0.1}
        },
        "sample_floor": {"pass": True},
    }
    label = {
        "decision_trace_id": "reattribute-trace",
        "decision_stage": "entry",
        "decision_ts": "2026-08-06T09:00:00+09:00",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "action": "DROP",
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "horizon_metrics": {
            "10m": {
                "end_return_pct": 0.5,
                "mfe_pct": 1.0,
                "mae_pct": -0.2,
                "first_hit": "target",
                "entry_path_first_hit": "target_first",
                "entry_path_target_pct": 0.3,
                "entry_path_adverse_pct": -0.7,
                "profit_opportunity_observed": True,
            }
        },
        "correlation": {"status": "open_unresolved"},
    }
    result = {
        "decision_trace_id": "reattribute-trace",
        "paired_replay_id": "reattribute-pair",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "status": "pass",
        "same_payload_confirmed": True,
        "control_response": {"action": "DROP"},
        "candidate_response": {
            "action": "BUY",
            "entry_setup_state": "READY",
            "entry_ai_risk_verdict": "PASS",
            "entry_probe_intent": True,
        },
    }
    existing = quality.build_paired_replay_report(
        target_date="2026-08-06",
        requests=[request],
        results=[result],
        labels=[label],
        prepared_requests=[request],
    )
    assert existing["promotion_report_integrity_pass"] is True
    existing.update(
        {
            "schema": quality.DETAILED_PAIRED_SCHEMA,
            "cohort_filter": {
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "runtime_effect": False,
            },
            "candidate_execution_performed": True,
            "existing_result_reuse_count": 1,
            "new_candidate_execution_count": 0,
            "deferred_candidate_execution_count": 0,
            "outcome_price_source": "stored_test_source",
            "outcome_price_source_requested": "stored_test_source",
            "price_source_provenance": [],
            "outcome_as_of": "2026-08-06T16:30:00+09:00",
        }
    )
    detailed_path = tmp_path / "detailed.json"
    label_path = tmp_path / "labels.json"
    control_path = tmp_path / "control.json"
    detailed_path.write_text(json.dumps(existing), encoding="utf-8")
    label_path.write_text(
        json.dumps(
            {
                "schema": quality.LABEL_REPORT_SCHEMA,
                "target_date": "2026-08-06",
                "labels": [label],
                "outcome_price_source": "stored_test_source",
                "outcome_price_source_requested": "stored_test_source",
                "price_source_provenance": [],
                "outcome_as_of": "2026-08-06T16:30:00+09:00",
                **quality.OFFLINE_CONTRACT,
            }
        ),
        encoding="utf-8",
    )
    control_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        quality, "detailed_paired_path", lambda *_a, **_k: detailed_path
    )
    monkeypatch.setattr(quality, "label_report_path", lambda *_a, **_k: label_path)
    monkeypatch.setattr(quality, "control_path", lambda *_a, **_k: control_path)
    monkeypatch.setattr(
        quality,
        "_default_sources",
        lambda *_a, **_k: {"traces": [], "payloads": [], "pending": []},
    )
    monkeypatch.setattr(
        quality,
        "prepare_paired_replay_requests",
        lambda **_kwargs: [dict(request)],
    )
    monkeypatch.setattr(
        quality,
        "prepare_detailed_paired_replay_requests",
        lambda rows, **_kwargs: rows,
    )
    return request, detailed_path


def test_rematerialize_detailed_replay_uses_stored_artifacts_without_api_calls(
    tmp_path, monkeypatch
):
    _request, detailed_path = _reattribution_fixture(tmp_path, monkeypatch)

    report, output_path = quality.rematerialize_detailed_replay_attribution(
        target_date="2026-08-06",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
    )

    assert output_path == detailed_path
    assert (
        report["entry_opportunity_funnel"]["cohorts"][0][
            "eligible_decision_event_count"
        ]
        == 1
    )
    assert report["entry_lifecycle_replay"]["bounded_one_share_replay_status"] == (
        "path_proxy_available"
    )
    assert report["reattribution_provenance"]["price_rest_request_performed"] is False
    assert report["reattribution_provenance"]["candidate_model_call_performed"] is False


def test_rematerialize_detailed_replay_rejects_current_request_identity_drift(
    tmp_path, monkeypatch
):
    request, _detailed_path = _reattribution_fixture(tmp_path, monkeypatch)
    drifted = {**request, "candidate_input_sha256": "changed-input"}
    monkeypatch.setattr(
        quality,
        "prepare_paired_replay_requests",
        lambda **_kwargs: [drifted],
    )

    with pytest.raises(RuntimeError, match="offline_reattribution_identity_invalid"):
        quality.rematerialize_detailed_replay_attribution(
            target_date="2026-08-06",
            effective_venue="KRX",
            session_bucket="KRX_REGULAR",
            candidate_prompt_version=(
                quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            ),
        )


def test_rematerialize_detailed_replay_accepts_hash_pinned_historical_snapshot(
    tmp_path, monkeypatch
):
    request, detailed_path = _reattribution_fixture(tmp_path, monkeypatch)
    drifted = {**request, "candidate_input_sha256": "current-source-drift"}
    monkeypatch.setattr(
        quality,
        "prepare_paired_replay_requests",
        lambda **_kwargs: [drifted],
    )
    existing_report = json.loads(detailed_path.read_text(encoding="utf-8"))
    stored_label_report = json.loads(
        (tmp_path / "labels.json").read_text(encoding="utf-8")
    )
    snapshot_path = tmp_path / "prepared_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "schema": quality.DETAILED_PREPARED_REQUEST_SNAPSHOT_SCHEMA,
                "target_date": "2026-08-06",
                "candidate_prompt_version": (
                    quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
                ),
                "cohort_filter": {
                    "effective_venue": "KRX",
                    "session_bucket": "KRX_REGULAR",
                },
                "source_code_commit": "a" * 40,
                "source_report_content_sha256": quality._sha256(existing_report),
                "stored_label_report_content_sha256": quality._sha256(
                    stored_label_report
                ),
                "prepared_request_count": 1,
                "sample_floor_pass_count": 1,
                "prepared_requests": [request],
                **quality.OFFLINE_CONTRACT,
            }
        ),
        encoding="utf-8",
    )

    report, _output_path = quality.rematerialize_detailed_replay_attribution(
        target_date="2026-08-06",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        prepared_request_snapshot_path=snapshot_path,
    )

    provenance = report["reattribution_provenance"]
    assert provenance["prepared_request_source"] == "pinned_historical_snapshot"
    assert provenance["prepared_request_source_code_commit"] == "a" * 40
    assert provenance["candidate_model_call_performed"] is False
    assert provenance["historical_decision_metrics_preserved"] is True

    detailed_path.write_text(json.dumps(report), encoding="utf-8")
    repeated, _output_path = quality.rematerialize_detailed_replay_attribution(
        target_date="2026-08-06",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        prepared_request_snapshot_path=snapshot_path,
    )
    assert (
        repeated["control_source_quality_adjusted_ev_pct"]
        == report["control_source_quality_adjusted_ev_pct"]
    )

    tampered = json.loads(detailed_path.read_text(encoding="utf-8"))
    tampered["control_source_quality_adjusted_ev_pct"] = 999.0
    detailed_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(RuntimeError, match="offline_reattribution_snapshot_invalid"):
        quality.rematerialize_detailed_replay_attribution(
            target_date="2026-08-06",
            effective_venue="KRX",
            session_bucket="KRX_REGULAR",
            candidate_prompt_version=(
                quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            ),
            prepared_request_snapshot_path=snapshot_path,
        )


def test_micro_reversion_budgeted_runner_reserves_each_schema_attempt_and_settles(
    tmp_path,
):
    class FakeLedger:
        def __init__(self):
            self.reservations = []
            self.settlements = []
            self.summary_paths = []

        def reserve_attempt(self, identity, *, token_ceiling):
            self.reservations.append((identity, token_ceiling))
            return SimpleNamespace(
                reservation_id=f"reservation-{identity.attempt_number}",
                attempt_identity_sha256=identity.content_sha256,
                reserved_cost_usd="0.01",
            )

        def settle_attempt(self, identity, **usage):
            self.settlements.append((identity, usage))
            return SimpleNamespace(
                actual_cost_usd="0.001",
                circuit_breaker_open=False,
            )

        def write_summary(self, path):
            self.summary_paths.append(path)

    ledger = FakeLedger()

    def base_runner(_request):
        return {
            "candidate_response": {"action": "WAIT"},
            "provider_provenance": {
                "provider": "openai",
                "input_tokens": 123,
                "output_tokens": 45,
                "response_sha256": "a" * 64,
            },
        }

    runner = quality.build_micro_reversion_budgeted_candidate_runner(
        target_date="2026-08-14",
        base_runner=base_runner,
        budget_ledger=ledger,
        budget_summary_path=tmp_path / "budget.json",
    )
    request = {
        "paired_replay_parent_id": "parent-1",
        "paired_replay_id": "request-arm-b",
        "micro_reversion_replay_arm": "replay_control_exact_plus_micro",
        "offline_provider_attempt_number": 2,
        "candidate_input": {"snapshot": "exact"},
        "candidate": {
            "provider": "openai",
            "model": "gpt-test",
            "max_output_tokens": 900,
        },
    }

    result = runner(request)

    assert len(ledger.reservations) == 1
    identity, ceiling = ledger.reservations[0]
    assert identity.attempt_number == 2
    assert identity.parent_id == "parent-1"
    assert ceiling.max_output_tokens == 900
    assert len(ledger.settlements) == 1
    assert ledger.settlements[0][1]["actual_input_tokens"] == 123
    assert ledger.settlements[0][1]["actual_output_tokens"] == 45
    assert result["provider_provenance"]["provider_budget_settled"] is True
    assert result["provider_provenance"]["provider_budget_reservation_id"] == (
        "reservation-2"
    )
    assert ledger.summary_paths == [tmp_path / "budget.json"]
