import gzip
import json
import sys
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from src.engine.scalping import ai_decision_quality as quality

KST = ZoneInfo("Asia/Seoul")


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
        "input_preflight_mode": "exact_v2",
        "input_preflight_allowed": True,
        "venue_consistent": True,
        "input_blockers": [],
        "action": action,
    }


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
            }
        },
    }
    label_report = {
        "schema": quality.LABEL_REPORT_SCHEMA,
        "target_date": "2026-07-27",
        "status": "mature_label_rows_available",
        "summary": {"mature": 1},
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
    context = quality._payload_contract(payload)["canonical_contexts"][0]
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
    assert (
        report["control_primary_decision_ev_pct"]
        == report["candidate_primary_decision_ev_pct"]
    )
    assert report["candidate_primary_decision_ev_delta_pct"] == 0.0


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
    assert report["status"] == "paired_replay_complete_candidate_quality_rejected"
    assert report["candidate_quality_gate_pass"] is False
    assert report["buckets"] == [
        {
            "stage": "entry",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sample_count": 1,
            "control_source_quality_adjusted_ev_pct": 0,
            "control_primary_decision_ev_pct": 0,
            "candidate_source_quality_adjusted_ev_pct": 0,
            "candidate_execution_cost_adjusted_ev_pct": None,
            "candidate_primary_decision_ev_pct": 0,
            "source_quality_adjusted_ev_delta_pct": 0,
            "candidate_primary_decision_ev_delta_pct": 0,
            "missed_upside_reduction_count": 0,
            "new_missed_upside_count": 0,
            "control_adverse_first_exposure_count": 0,
            "adverse_first_candidate_exposure_count": 0,
            "control_tight_stop_adverse_first_exposure_count": 0,
            "candidate_tight_stop_adverse_first_exposure_count": 0,
            "candidate_exposure_decision_count": 0,
            "candidate_exposure_unique_symbol_count": 0,
            "candidate_exposure_sample_floor_pass": False,
            "candidate_dominant_action_ratio": 1.0,
            "candidate_quality_checks": {
                "source_quality_adjusted_ev_improved": False,
                "primary_decision_ev_improved": False,
                "candidate_ev_positive": False,
                "missed_upside_reduced": False,
                "new_missed_upside_not_increased": True,
                "adverse_first_exposure_not_increased": True,
                "tight_stop_adverse_first_exposure_not_increased": True,
                "candidate_action_not_collapsed": False,
                "candidate_exposure_sample_floor_pass": False,
            },
            "candidate_quality_gate_pass": False,
            "candidate_error_taxonomy_counts": {
                "false_drop": 1,
                "false_drop_drawdown_recovery": 1,
            },
        }
    ]


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
        report["candidate_quality_checks"][
            "tight_stop_adverse_first_exposure_not_increased"
        ]
        is False
    )
    assert report["entry_path_label_contract"]["decision_authority"] == (
        "offline_replay_and_attribution_only"
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
    assert captured["reasoning"] == {"effort": "minimal"}
    assert envelope["provider_provenance"]["reasoning_effort"] == "minimal"
    output_schema = captured["text"]["format"]["schema"]
    assert output_schema["properties"]["expected_upside_pct"]["minimum"] == 0
    assert output_schema["properties"]["expected_downside_pct"]["maximum"] == 0
    assert captured["metadata"]["candidate_contract_sha256"]
