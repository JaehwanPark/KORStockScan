from __future__ import annotations

import json
from pathlib import Path

from src.engine.scalping import main_ai_holding_base_replay_batch as holding
from src.engine.scalping import main_ai_prompt_consumer as consumer
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer
from src.engine.scalping.micro_reversion import replay_ablation_contract as ablation


def _source_only() -> dict[str, bool]:
    return {
        "runtime_effect": False,
        "runtime_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _optimizer_report(
    target_date: str, *, source_bindings: dict | None = None
) -> dict:
    body = {
        "schema": optimizer.SCHEMA,
        "target_date": target_date,
        "status": "ready_source_only_continuous_search",
        "stage_optimizers": {
            "holding": {
                "cohort_optimizers": [
                    {
                        "effective_venue": "KRX",
                        "session_bucket": "KRX_REGULAR",
                        "champion": {
                            "prompt_version": "holding_score_v2",
                            "prompt_sha256": "a" * 64,
                        },
                        "legacy_r0_challenger": {
                            "prompt_version": "decision_quality_holding_v2_3",
                            "prompt_sha256": "b" * 64,
                        },
                        "selected_challenger": {
                            "prompt_version": "decision_quality_holding_v2_3"
                        },
                    }
                ]
            }
        },
        "result_feasibility": {
            "profit_improving_candidate_currently_demonstrated": False
        },
        "source_bindings": source_bindings or {},
        **_source_only(),
    }
    return {**body, "artifact_content_sha256": optimizer._canonical_sha256(body)}


def _prepared_report(target_date: str) -> dict:
    body = {
        "schema": "main_ai_quality_micro_prepared_requests_v1",
        "target_date": target_date,
        "status": "prepared_requests_ready",
        "prepared_requests": [
            {
                "stage": "holding",
                "decision_trace_id": "trace-1",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
            }
        ],
        **_source_only(),
    }
    return {**body, "artifact_content_sha256": optimizer._canonical_sha256(body)}


def test_holding_base_manifest_consumes_optimizer_with_exact_hashes(
    monkeypatch, tmp_path: Path
):
    target_date = "2026-09-03"
    optimizer_path = tmp_path / "optimizer.json"
    prepared_path = tmp_path / "prepared.json"
    prepared = _prepared_report(target_date)
    optimizer_path.write_text(
        json.dumps(
            _optimizer_report(
                target_date,
                source_bindings={
                    "prepared_request_sha256": optimizer._canonical_sha256(prepared)
                },
            )
        )
    )
    prepared_path.write_text(json.dumps(prepared))
    monkeypatch.setattr(
        optimizer, "report_paths", lambda _date: (optimizer_path, tmp_path / "x.md")
    )
    monkeypatch.setattr(
        holding.quality,
        "micro_reversion_prepared_request_path",
        lambda _date: prepared_path,
    )
    monkeypatch.setattr(
        holding.quality, "control_path", lambda _date: tmp_path / "control.json"
    )
    monkeypatch.setattr(
        holding.quality,
        "load_promotion_for_target_date",
        lambda _date: ({}, None, None),
    )
    monkeypatch.setattr(holding.quality, "_load_json", lambda _path: {})
    monkeypatch.setattr(holding.coverage, "_load_rows", lambda *_args: [])

    request = {
        "paired_replay_id": "pair-1",
        "decision_trace_id": "trace-1",
        "source_date": target_date,
        "stage": "holding",
        "endpoint": "holding_score",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": "c" * 64,
        "source_exact_payload_sha256": "d" * 64,
        "candidate_input_sha256": "e" * 64,
        "control": {
            "prompt_version": "holding_score_v2",
            "prompt_sha256": "a" * 64,
        },
        "candidate": {
            "prompt_version": "decision_quality_holding_v2_3",
            "system_prompt_sha256": "b" * 64,
            "contract_sha256": "f" * 64,
        },
        "source_exactness": "byte_exact",
    }
    monkeypatch.setattr(
        holding.coverage,
        "prepare_stage_requests",
        lambda **_kwargs: ([request], {"selected_frozen_cohort_count": 1}),
    )

    report = holding.build_report(target_date)

    assert report["status"] == "ready_source_only_holding_base_manifest"
    assert report["provider_call_performed"] is False
    assert report["request_count"] == 1
    assert report["cohorts"][0]["path_status"] == consumer.CONNECTED
    assert report["cohorts"][0]["selected_prompt_sha256"] == "b" * 64
    assert report["artifact_content_sha256"] == optimizer._canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "artifact_content_sha256"
        }
    )


def test_holding_base_manifest_fails_closed_on_optimizer_hash_mismatch(
    monkeypatch, tmp_path: Path
):
    target_date = "2026-09-03"
    optimizer_path = tmp_path / "optimizer.json"
    prepared_path = tmp_path / "prepared.json"
    prepared = _prepared_report(target_date)
    bad = _optimizer_report(
        target_date,
        source_bindings={
            "prepared_request_sha256": optimizer._canonical_sha256(prepared)
        },
    )
    bad["decision"] = "tampered"
    optimizer_path.write_text(json.dumps(bad))
    prepared_path.write_text(json.dumps(prepared))
    monkeypatch.setattr(
        optimizer, "report_paths", lambda _date: (optimizer_path, tmp_path / "x.md")
    )
    monkeypatch.setattr(
        holding.quality,
        "micro_reversion_prepared_request_path",
        lambda _date: prepared_path,
    )

    report = holding.build_report(target_date)

    assert report["status"] == "blocked_source_contract"
    assert report["blockers"] == ["optimizer_artifact_missing_or_invalid"]
    assert report["provider_call_performed"] is False


def test_factorial_router_retires_exact_r0_cells_and_connects_only_p1d0():
    trace_id = "holding-trace"
    optimizer_report = _optimizer_report("2026-09-03")
    prepared = {
        "prepared_requests": [
            {
                "stage": "holding",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "decision_trace_id": trace_id,
            }
        ]
    }
    bridge = {
        "rows": [
            {
                "decision_trace_id": trace_id,
                "decision_stage": "holding_score",
                "ask_depletion_sidecar_status": (
                    "eligible_source_only_feature_ablation"
                ),
            }
        ]
    }
    input_sha = "c" * 64
    arm_prompt = {
        ablation.CURRENT_BASE_CONTROL_ARM: ("holding_score_v2", "a" * 64),
        ablation.CURRENT_ASK_CONTROL_ARM: ("holding_score_v2", "a" * 64),
        ablation.CURRENT_ASK_CANDIDATE_ARM: (
            "decision_quality_holding_v2_3",
            "b" * 64,
        ),
    }
    materialized_requests = []
    for arm, (version, prompt_sha) in arm_prompt.items():
        materialized_requests.append(
            {
                "decision_trace_id": trace_id,
                "micro_reversion_replay_arm": arm,
                "paired_replay_id": f"request-{arm}",
                "candidate_input_sha256": input_sha,
                "candidate": {
                    "prompt_version": version,
                    "system_prompt_sha256": prompt_sha,
                },
            }
        )
    holding_base = {
        "decision_trace_id": trace_id,
        "candidate_input_sha256": input_sha,
        "candidate_prompt_version": "decision_quality_holding_v2_3",
        "candidate_prompt_sha256": "b" * 64,
    }

    cells = consumer._factorial_cells(
        optimizer_report=optimizer_report,
        prepared=prepared,
        bridge=bridge,
        materialized={"requests": materialized_requests},
        execution={"results": []},
        entry_request_index={},
        holding_request_index={("KRX", "KRX_REGULAR", trace_id): holding_base},
    )

    assert len(cells) == 4
    assert [row["path_status"] for row in cells].count(consumer.R0_DUPLICATE) == 3
    p1d0 = next(row for row in cells if row["cell"].startswith("P1D0"))
    assert p1d0["path_status"] == consumer.CONNECTED
    assert p1d0["execution_state"] == "provider_execution_budget_checkpoint_pending"


def test_consumer_report_keeps_runtime_blocked_and_detects_unclassified(
    monkeypatch, tmp_path: Path
):
    target_date = "2026-09-03"
    paths = {
        "optimizer": tmp_path / "optimizer.json",
        "prepared": tmp_path / "prepared.json",
        "bridge": tmp_path / "bridge.json",
        "materialized": tmp_path / "materialized.json",
        "execution": tmp_path / "execution.json",
    }
    prepared = _prepared_report(target_date)
    paths["prepared"].write_text(json.dumps(prepared))
    bridge = {
        "schema": "micro_reversion_ai_quality_bridge_v1",
        "target_date": target_date,
        "status": "pass",
        "rows": [],
        **_source_only(),
    }
    paths["bridge"].write_text(json.dumps(bridge))
    paths["optimizer"].write_text(
        json.dumps(
            _optimizer_report(
                target_date,
                source_bindings={
                    "prepared_request_sha256": optimizer._canonical_sha256(prepared),
                    "micro_bridge_sha256": optimizer._canonical_sha256(bridge),
                },
            )
        )
    )
    monkeypatch.setattr(
        optimizer,
        "report_paths",
        lambda _date: (paths["optimizer"], tmp_path / "optimizer.md"),
    )
    monkeypatch.setattr(
        consumer.quality,
        "micro_reversion_prepared_request_path",
        lambda _date: paths["prepared"],
    )
    monkeypatch.setattr(
        consumer.quality,
        "micro_reversion_bridge_report_path",
        lambda _date: paths["bridge"],
    )
    monkeypatch.setattr(
        consumer.quality,
        "micro_reversion_materialized_request_path",
        lambda _date: paths["materialized"],
    )
    monkeypatch.setattr(
        consumer.quality,
        "micro_reversion_execution_result_path",
        lambda _date: paths["execution"],
    )
    connected = {
        "path_status": consumer.CONNECTED,
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "owner": "test-owner",
        "acceptance_test": "test-pass",
    }
    monkeypatch.setattr(
        consumer, "_entry_base_paths", lambda *_args, **_kwargs: ([connected], {})
    )
    monkeypatch.setattr(
        consumer, "_holding_base_paths", lambda *_args, **_kwargs: ([connected], {})
    )
    monkeypatch.setattr(
        consumer,
        "_factorial_cells",
        lambda **_kwargs: [
            {
                "path_status": consumer.BLOCKED,
                "blocking_reason": "missing_cell",
                "owner": "owner",
                "acceptance_test": "test",
            }
        ],
    )

    report = consumer.build_report(target_date)

    assert report["status"] == "ready_source_only_consumer_closure"
    assert report["unclassified_request_path_count"] == 0
    assert report["terminal_request_path_contract_invalid_count"] == 0
    assert report["entry_followup_terminal_ready"] is True
    assert report["provider_call_performed"] is False
    assert report["performance_evidence"]["runtime_prompt_update_allowed"] is False
    assert report["performance_evidence"]["profit_improvement_demonstrated"] is False
    assert (
        report["performance_evidence"]["future_profit_improving_output_likelihood"]
        == "partial_entry_only_plausible_holding_and_factorial_provider_blocked"
    )
    assert (
        report["request_paths"]["optional_micro_enriched_2x2"]["path_status"]
        == consumer.BLOCKED
    )
