from __future__ import annotations

import json

import pytest

from src.engine.ai_prompt_contracts import (
    decision_quality_v2_14_setup_risk_adjudicator_system_prompt,
    decision_quality_v2_15_bounded_recovery_system_prompt,
    decision_quality_v2_16_sequential_recovery_system_prompt,
)
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer
from src.engine.scalping import ai_action_outcome_calibration as calibration


def test_calibration_ascii_digest_accepts_nonascii_and_rejects_tampering(
    monkeypatch, tmp_path
):
    report = calibration.build_report(target_date="2026-09-07", data_root=tmp_path)
    report["diagnostic_note"] = "진단"
    report = calibration._with_artifact_content_sha256(report)
    monkeypatch.setattr(optimizer, "_read_json", lambda _: report)
    assert optimizer._latest_action_outcome_calibration("2026-09-07")[2] == []
    report["diagnostic_note"] = "변조"
    assert (
        "action_outcome_calibration_content_hash_invalid"
        in optimizer._latest_action_outcome_calibration("2026-09-07")[2]
    )


def test_calibration_changes_offline_candidate_choice_not_runtime_authority():
    version = optimizer.ENTRY_CANDIDATE_ORDER[0]
    evidence = {
        "candidate_prompt_version": version,
        "candidate_prompt_sha256": optimizer.ENTRY_CANDIDATE_PROMPT_SHA256[version],
        "candidate_contract_sha256": "b" * 64,
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "source_integrity_complete": True,
        "probe_cost_contract_complete": True,
        "review_classification": "learning_only_or_rejected",
        "prompt_review_gate": {
            "checks": {
                "exact_trace_floor": True,
                "unique_symbol_floor": True,
                "independent_source_date_floor": True,
                "candidate_exposure_floor": True,
                "paired_economic_values_complete": True,
                "positive_probe_cost_adjusted_ev": False,
            }
        },
    }

    def select():
        return optimizer._select_entry_challenger(
            "legacy",
            [],
            effective_venue="KRX",
            session_bucket="KRX_REGULAR",
            calibration={"candidate_summaries": [evidence]},
        )

    assert select()["prompt_version"] == optimizer.ENTRY_CANDIDATE_ORDER[1]
    evidence["review_classification"] = "thin_positive_review"
    assert select()["prompt_version"] == version
    assert select()["calibration_used_for_offline_selection"] is True
    evidence["review_classification"] = "learning_only_or_rejected"
    evidence["prompt_review_gate"]["checks"].update(
        positive_probe_cost_adjusted_ev=True,
        positive_ev_delta=True,
        bounded_probe_risk_budget=False,
    )
    evidence["candidate_probe_risk_missing_count"] = 1
    assert select()["prompt_version"] == version
    evidence["candidate_probe_risk_missing_count"] = 0
    assert select()["prompt_version"] == optimizer.ENTRY_CANDIDATE_ORDER[1]
    evidence["session_bucket"] = "NXT_AFTERMARKET"
    assert select()["prompt_version"] == version


def test_follower_requires_valid_calibration_and_current_source_generation(
    monkeypatch, tmp_path
):
    from src.tests.test_ai_action_outcome_calibration import _economic_row, _write_json

    day = "2026-09-07"
    detail_dir = tmp_path / "report" / calibration.PAIRED_SUBDIR
    cal_dir = tmp_path / "report" / calibration.REPORT_SUBDIR
    monkeypatch.setattr(optimizer, "DETAILED_DIR", detail_dir)
    monkeypatch.setattr(optimizer, "ACTION_OUTCOME_CALIBRATION_DIR", cal_dir)
    detail_path = detail_dir / f"ai_prompt_detailed_paired_replay_{day}_candidate.json"
    _write_json(
        detail_path, {"target_date": day, "paired_comparisons": [_economic_row(1)]}
    )
    report = calibration.build_report(target_date=day, data_root=tmp_path)
    cal_path = cal_dir / f"ai_decision_action_outcome_calibration_{day}.json"
    _write(cal_path, report)
    assert optimizer._latest_action_outcome_calibration(day)[2] == []
    _write_json(
        detail_path, {"target_date": day, "paired_comparisons": [_economic_row(1, 0.8)]}
    )
    assert (
        "action_outcome_calibration_source_generation_changed"
        in optimizer._latest_action_outcome_calibration(day)[2]
    )
    prepared = tmp_path / "prepared.json"
    _write(prepared, _prepared_payload(day, [_prepared_row("t1", "entry", "005930")]))
    blocked = optimizer.build_report(
        day,
        prepared_path=prepared,
        bridge_path=tmp_path / "absent",
        require_action_outcome_calibration=True,
    )
    assert blocked["status"] == "blocked"
    assert (
        "required_action_outcome_calibration_invalid_or_unavailable"
        in blocked["blockers"]
    )


def test_calibration_selected_version_reaches_existing_batch_consumer(
    monkeypatch, tmp_path
):
    from src.tests.test_ai_action_outcome_calibration import _economic_row, _write_json
    from src.engine.scalping import entry_setup_paired_replay_batch as batch

    day = "2026-09-07"
    detail_dir = tmp_path / "report" / calibration.PAIRED_SUBDIR
    cal_dir = tmp_path / "report" / calibration.REPORT_SUBDIR
    monkeypatch.setattr(optimizer, "DETAILED_DIR", detail_dir)
    monkeypatch.setattr(optimizer, "ACTION_OUTCOME_CALIBRATION_DIR", cal_dir)
    monkeypatch.setattr(optimizer, "REPORT_DIR", tmp_path / "optimizer")
    version = optimizer.ENTRY_CANDIDATE_ORDER[0]
    for source_day, offset in (("2026-09-04", 0), (day, 20)):
        _write_json(
            detail_dir
            / f"ai_prompt_detailed_paired_replay_{source_day}_candidate.json",
            {
                "target_date": source_day,
                "requests": [
                    {
                        "candidate": {
                            "prompt_version": version,
                            "system_prompt_sha256": optimizer.ENTRY_CANDIDATE_PROMPT_SHA256[
                                version
                            ],
                        }
                    }
                ],
                "paired_comparisons": [
                    _economic_row(i, -0.1) for i in range(offset, offset + 20)
                ],
            },
        )
    _write(
        cal_dir / f"ai_decision_action_outcome_calibration_{day}.json",
        calibration.build_report(target_date=day, data_root=tmp_path),
    )
    prepared = tmp_path / "prepared.json"
    _write(prepared, _prepared_payload(day, [_prepared_row("t1", "entry", "005930")]))
    report = optimizer.build_report(
        day,
        prepared_path=prepared,
        bridge_path=tmp_path / "absent",
        require_action_outcome_calibration=True,
        write=True,
    )
    plan, source = batch._optimizer_candidate_plan(day)
    assert plan[("KRX", "KRX_REGULAR")] == optimizer.ENTRY_CANDIDATE_ORDER[1]
    assert source["artifact_content_sha256"] == report["artifact_content_sha256"]
    assert report["runtime_effect"] is False


def test_refresh_freezes_executed_day_and_preserves_next_session_recommendation(
    monkeypatch, tmp_path
):
    day = "2026-09-07"
    monkeypatch.setattr(optimizer, "ENTRY_BATCH_DIR", tmp_path / "batch")
    monkeypatch.setattr(optimizer, "DETAILED_DIR", tmp_path / "detailed")
    monkeypatch.setattr(
        optimizer, "ACTION_OUTCOME_CALIBRATION_DIR", tmp_path / "calibration"
    )
    version = optimizer.ENTRY_CANDIDATE_ORDER[1]
    batch_body = {
        "schema": "ai_entry_setup_paired_replay_batch_v1",
        "target_date": day,
        "status": "completed_offline_only",
        **optimizer.SOURCE_ONLY_AUTHORITY,
        "cohorts": [
            {
                "effective_venue": v,
                "session_bucket": s,
                "candidate_prompt_version": version,
                "status": "completed_offline_only",
            }
            for v, s in (("KRX", "KRX_REGULAR"), ("NXT", "NXT_AFTERMARKET"))
        ],
    }
    _write(
        optimizer.ENTRY_BATCH_DIR / f"ai_entry_setup_paired_replay_batch_{day}.json",
        batch_body,
    )
    prepared = tmp_path / "prepared.json"
    _write(prepared, _prepared_payload(day, [_prepared_row("t1", "entry", "005930")]))
    report = optimizer.build_report(
        day,
        prepared_path=prepared,
        bridge_path=tmp_path / "absent",
        preserve_entry_batch_selection=True,
    )
    cohort = report["stage_optimizers"]["entry"]["cohort_optimizers"][0]
    assert cohort["selected_challenger"]["prompt_version"] == version
    assert (
        cohort["next_session_evaluation_recommendation"]["prompt_version"]
        == optimizer.ENTRY_CANDIDATE_ORDER[0]
    )
    assert report["runtime_effect"] is False
    batch_body["status"] = "running"
    _write(
        optimizer.ENTRY_BATCH_DIR / f"ai_entry_setup_paired_replay_batch_{day}.json",
        batch_body,
    )
    with pytest.raises(ValueError, match="terminal_entry_batch"):
        optimizer._frozen_entry_batch_selection(day)


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_optimizer_candidate_prompt_hash_registry_matches_current_contracts():
    builders = (
        decision_quality_v2_14_setup_risk_adjudicator_system_prompt,
        decision_quality_v2_15_bounded_recovery_system_prompt,
        decision_quality_v2_16_sequential_recovery_system_prompt,
    )

    assert optimizer.ENTRY_CANDIDATE_PROMPT_SHA256 == {
        version: optimizer._canonical_sha256(builder("entry"))
        for version, builder in zip(
            optimizer.ENTRY_CANDIDATE_ORDER, builders, strict=True
        )
    }


def _prepared_payload(target_date: str, rows: list[dict]) -> dict:
    payload = {
        "schema": "main_ai_quality_micro_prepared_requests_v1",
        "target_date": target_date,
        "prepared_requests": rows,
        "runtime_effect": False,
        "runtime_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {
        **payload,
        "artifact_content_sha256": optimizer._canonical_sha256(payload),
    }


def _bridge_payload(target_date: str, rows: list[dict]) -> dict:
    body = {
        "schema": "micro_reversion_ai_quality_bridge_v1",
        "target_date": target_date,
        "rows": rows,
        "runtime_effect": False,
        "runtime_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "report_content_sha256": optimizer._ascii_canonical_sha256(body)}


def _prepared_row(trace_id: str, stage: str, symbol: str) -> dict:
    champion = "entry_current" if stage == "entry" else "holding_current"
    challenger = "entry_legacy" if stage == "entry" else "holding_candidate"
    return {
        "decision_trace_id": trace_id,
        "stage": stage,
        "stock_code": symbol,
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "control": {
            "prompt_version": champion,
            "prompt_sha256": "a" * 64,
        },
        "candidate": {
            "prompt_version": challenger,
            "system_prompt_sha256": "b" * 64,
            "contract_sha256": "c" * 64,
        },
    }


def _entry_candidate_requests(
    candidate_prompt_version: str, candidate_contract_sha256: str = "d" * 64
) -> list[dict]:
    return [
        {
            "candidate": {
                "prompt_version": f"{candidate_prompt_version}_entry",
                "system_prompt_sha256": optimizer._expected_entry_prompt_sha256(
                    candidate_prompt_version
                ),
                "contract_sha256": candidate_contract_sha256,
            }
        }
    ]


def test_optimizer_keeps_no_shock_parents_in_base_prompt_comparison(
    monkeypatch, tmp_path
):
    target_date = "2026-09-04"
    prepared_path = tmp_path / "prepared.json"
    bridge_path = tmp_path / "bridge.json"
    detailed_dir = tmp_path / "detailed"
    monkeypatch.setattr(optimizer, "DETAILED_DIR", detailed_dir)
    _write(
        prepared_path,
        _prepared_payload(
            target_date,
            [
                _prepared_row("entry-no-shock", "entry", "000001"),
                _prepared_row("entry-enriched", "entry", "000002"),
                _prepared_row("holding-no-shock", "holding", "000003"),
            ],
        ),
    )
    _write(
        bridge_path,
        _bridge_payload(
            target_date,
            [
                {
                    "decision_trace_id": "entry-no-shock",
                    "decision_stage": "entry_screen",
                    "ask_depletion_sidecar_status": "not_applicable_no_shock_event",
                },
                {
                    "decision_trace_id": "entry-enriched",
                    "decision_stage": "entry_screen",
                    "ask_depletion_sidecar_status": (
                        "eligible_source_only_feature_ablation"
                    ),
                },
            ],
        ),
    )

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=bridge_path,
    )

    entry = report["stage_optimizers"]["entry"]
    design = entry["factorial_input_design"]
    assert design["base_prompt_comparison_parent_count"] == 2
    assert design["full_factorial_common_parent_count"] == 1
    assert design["no_shock_or_micro_not_applicable_kept_in_base"] is True
    assert design["micro_or_ask_depletion_is_global_eligibility_gate"] is False
    assert report["result_feasibility"]["candidate_generation_feasible"] is True
    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True


def test_optimizer_continues_candidate_until_isolated_promotion_floor_closes(
    monkeypatch, tmp_path
):
    target_date = "2026-09-04"
    prior_result_date = "2026-09-03"
    prepared_path = tmp_path / "prepared.json"
    bridge_path = tmp_path / "bridge.json"
    detailed_dir = tmp_path / "detailed"
    monkeypatch.setattr(optimizer, "DETAILED_DIR", detailed_dir)
    _write(
        prepared_path,
        _prepared_payload(target_date, [_prepared_row("entry-1", "entry", "000001")]),
    )
    _write(
        bridge_path,
        _bridge_payload(target_date, []),
    )
    _write(
        detailed_dir / f"detail_{prior_result_date}.json",
        {
            "schema": "ai_prompt_detailed_paired_replay_v1",
            "target_date": prior_result_date,
            "promotion_cohort_scope": {
                "isolated": True,
                "stages": ["entry"],
                "effective_venues": ["KRX"],
                "session_buckets": ["KRX_REGULAR"],
                "candidate_contract_isolated": True,
                "cross_cohort_promotion_forbidden": True,
                "candidate_contract_sha256": "d" * 64,
            },
            "candidate_contract_sha256": "d" * 64,
            "cumulative_learning": {
                "candidate_prompt_version": optimizer.ENTRY_CANDIDATE_ORDER[0],
                "candidate_contract_sha256": "d" * 64,
                "as_of_date": prior_result_date,
                "clean_tuning_baseline_date": "2026-06-05",
                "decision_count": 20,
                "unique_symbol_count": 10,
                "candidate_exposure_decision_count": 8,
                "candidate_exposure_unique_symbol_count": 8,
                "candidate_primary_decision_ev_pct": -0.01,
                "source_quality_adjusted_ev_delta_pct": -0.01,
                "candidate_exposure_probe_cost_adjusted_ev_pct": -0.2,
                "promotion_evidence_floor": {"pass": False},
                "promotion_quality_gate_pass": False,
                "candidate_error_taxonomy_counts": {"false_wait": 3},
            },
            "candidate_provider_attempt_count": 20,
            "provider_failed_count": 0,
            "candidate_provider_none_count": 0,
            "promotion_report_integrity_pass": True,
            "candidate_execution_selection": {"evaluation_coverage_pct": 50.0},
            "net_profit_status": "not_available_without_notional_and_fill_join",
            "requests": _entry_candidate_requests(optimizer.ENTRY_CANDIDATE_ORDER[0]),
        },
    )

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=bridge_path,
    )

    selected = report["stage_optimizers"]["entry"]["selected_challenger"]
    assert selected == {
        "prompt_version": optimizer.ENTRY_CANDIDATE_ORDER[0],
        "action": "continue_current_challenger_new_mature_parents_only",
        "reason": "promotion_sample_floor_not_complete",
        "calibration_screened_out_versions": [],
    }
    assert (
        report["result_feasibility"][
            "profit_improving_candidate_currently_demonstrated"
        ]
        is False
    )


def test_optimizer_does_not_share_promotion_state_across_cohorts(monkeypatch, tmp_path):
    target_date = "2026-09-04"
    prepared_path = tmp_path / "prepared.json"
    bridge_path = tmp_path / "bridge.json"
    detailed_dir = tmp_path / "detailed"
    monkeypatch.setattr(optimizer, "DETAILED_DIR", detailed_dir)
    krx = _prepared_row("entry-krx", "entry", "000001")
    nxt = _prepared_row("entry-nxt", "entry", "000002")
    nxt["effective_venue"] = "NXT"
    nxt["session_bucket"] = "NXT_AFTERMARKET"
    _write(
        prepared_path,
        _prepared_payload(target_date, [krx, nxt]),
    )
    _write(
        bridge_path,
        _bridge_payload(target_date, []),
    )
    _write(
        detailed_dir / f"detail_{target_date}.json",
        {
            "schema": "ai_prompt_detailed_paired_replay_v1",
            "target_date": target_date,
            "promotion_cohort_scope": {
                "isolated": True,
                "stages": ["entry"],
                "effective_venues": ["KRX"],
                "session_buckets": ["KRX_REGULAR"],
                "candidate_contract_isolated": True,
                "cross_cohort_promotion_forbidden": True,
                "candidate_contract_sha256": "d" * 64,
            },
            "candidate_contract_sha256": "d" * 64,
            "cumulative_learning": {
                "candidate_prompt_version": optimizer.ENTRY_CANDIDATE_ORDER[0],
                "candidate_contract_sha256": "d" * 64,
                "as_of_date": target_date,
                "clean_tuning_baseline_date": "2026-06-05",
                "promotion_evidence_floor": {"pass": True},
                "promotion_quality_gate_pass": True,
            },
            "provider_failed_count": 0,
            "candidate_provider_none_count": 0,
            "promotion_report_integrity_pass": True,
            "requests": _entry_candidate_requests(optimizer.ENTRY_CANDIDATE_ORDER[0]),
        },
    )

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=bridge_path,
    )

    cohorts = {
        (item["effective_venue"], item["session_bucket"]): item
        for item in report["stage_optimizers"]["entry"]["cohort_optimizers"]
    }
    assert cohorts[("KRX", "KRX_REGULAR")]["selected_challenger"]["action"] == (
        "freeze_as_runtime_candidate_pending_r2_r3"
    )
    assert cohorts[("NXT", "NXT_AFTERMARKET")]["selected_challenger"]["action"] == (
        "start_new_challenger_evaluation"
    )
    assert report["stage_optimizers"]["entry"]["selected_challenger"]["action"] == (
        "use_isolated_cohort_selections"
    )


def test_optimizer_ignores_detailed_result_with_stale_prompt_body(
    monkeypatch, tmp_path
):
    target_date = "2026-09-04"
    prepared_path = tmp_path / "prepared.json"
    bridge_path = tmp_path / "bridge.json"
    detailed_dir = tmp_path / "detailed"
    monkeypatch.setattr(optimizer, "DETAILED_DIR", detailed_dir)
    _write(
        prepared_path,
        _prepared_payload(target_date, [_prepared_row("entry-1", "entry", "000001")]),
    )
    _write(bridge_path, _bridge_payload(target_date, []))
    version = optimizer.ENTRY_CANDIDATE_ORDER[0]
    _write(
        detailed_dir / f"detail_{target_date}.json",
        {
            "schema": "ai_prompt_detailed_paired_replay_v1",
            "target_date": target_date,
            "promotion_cohort_scope": {
                "isolated": True,
                "stages": ["entry"],
                "effective_venues": ["KRX"],
                "session_buckets": ["KRX_REGULAR"],
                "candidate_contract_isolated": True,
                "cross_cohort_promotion_forbidden": True,
                "candidate_contract_sha256": "d" * 64,
            },
            "candidate_contract_sha256": "d" * 64,
            "cumulative_learning": {
                "candidate_prompt_version": version,
                "candidate_contract_sha256": "d" * 64,
                "as_of_date": target_date,
                "clean_tuning_baseline_date": "2026-06-05",
                "promotion_evidence_floor": {"pass": True},
                "promotion_quality_gate_pass": True,
            },
            "provider_failed_count": 0,
            "candidate_provider_none_count": 0,
            "promotion_report_integrity_pass": True,
            "requests": [
                {
                    "candidate": {
                        "prompt_version": f"{version}_entry",
                        "system_prompt_sha256": "0" * 64,
                        "contract_sha256": "d" * 64,
                    }
                }
            ],
        },
    )

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=bridge_path,
    )

    selected = report["stage_optimizers"]["entry"]["selected_challenger"]
    assert selected["prompt_version"] == version
    assert selected["action"] == "start_new_challenger_evaluation"
    assert report["evaluated_challengers"] == []


def test_optimizer_keeps_base_prompt_search_when_optional_micro_bridge_is_missing(
    tmp_path,
):
    target_date = "2026-09-04"
    prepared_path = tmp_path / "prepared.json"
    _write(
        prepared_path,
        _prepared_payload(target_date, [_prepared_row("entry-1", "entry", "000001")]),
    )

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=tmp_path / "missing-bridge.json",
    )

    assert report["status"] == "ready_source_only_continuous_search"
    assert report["result_feasibility"]["candidate_generation_feasible"] is True
    assert report["optional_input_warnings"]
    design = report["stage_optimizers"]["entry"]["factorial_input_design"]
    assert design["base_prompt_comparison_parent_count"] == 1
    assert design["full_factorial_common_parent_count"] == 0


def test_optimizer_blocks_tampered_prepared_request_artifact(tmp_path):
    target_date = "2026-09-04"
    prepared_path = tmp_path / "prepared.json"
    payload = _prepared_payload(
        target_date, [_prepared_row("entry-1", "entry", "000001")]
    )
    payload["prepared_requests"][0]["stock_code"] = "999999"
    _write(prepared_path, payload)

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=tmp_path / "missing-bridge.json",
    )

    assert report["status"] == "blocked"
    assert "prepared_request_content_hash_invalid" in report["blockers"]
    assert report["result_feasibility"]["candidate_generation_feasible"] is False


def test_optimizer_ignores_tampered_optional_micro_bridge_but_keeps_base(
    tmp_path,
):
    target_date = "2026-09-04"
    prepared_path = tmp_path / "prepared.json"
    bridge_path = tmp_path / "bridge.json"
    _write(
        prepared_path,
        _prepared_payload(target_date, [_prepared_row("entry-1", "entry", "000001")]),
    )
    bridge = _bridge_payload(
        target_date,
        [
            {
                "decision_trace_id": "entry-1",
                "decision_stage": "entry_screen",
                "ask_depletion_sidecar_status": (
                    "eligible_source_only_feature_ablation"
                ),
            }
        ],
    )
    bridge["rows"][0]["decision_trace_id"] = "tampered"
    _write(bridge_path, bridge)

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=bridge_path,
    )

    assert report["status"] == "ready_source_only_continuous_search"
    assert (
        "optional_micro_bridge_content_hash_invalid"
        in report["optional_input_warnings"]
    )
    design = report["stage_optimizers"]["entry"]["factorial_input_design"]
    assert design["base_prompt_comparison_parent_count"] == 1
    assert design["full_factorial_common_parent_count"] == 0


def test_optimizer_consumes_validated_action_outcome_as_source_only_advisory(
    monkeypatch, tmp_path
):
    target_date = "2026-09-08"
    prepared_path = tmp_path / "prepared.json"
    bridge_path = tmp_path / "bridge.json"
    calibration_dir = tmp_path / "calibration"
    monkeypatch.setattr(optimizer, "ACTION_OUTCOME_CALIBRATION_DIR", calibration_dir)
    monkeypatch.setattr(optimizer, "DETAILED_DIR", tmp_path / "detailed")
    _write(
        prepared_path,
        _prepared_payload(target_date, [_prepared_row("entry-1", "entry", "000001")]),
    )
    _write(bridge_path, _bridge_payload(target_date, []))
    version = optimizer.ENTRY_CANDIDATE_ORDER[0]
    candidate_summary = {
        "candidate_prompt_version": version,
        "candidate_prompt_sha256": "a" * 64,
        "candidate_contract_sha256": "b" * 64,
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "cohort_isolated": True,
        "review_classification": "thin_positive_review",
        "source_integrity_complete": True,
        "candidate_primary_decision_ev_delta_pct": 0.1,
        "candidate_probe_cost_adjusted_ev_pct": 0.2,
        "r3_handoff_evidence": {"pass": False},
        "runtime_apply_authority": False,
    }
    thin_summary = {
        key: candidate_summary[key]
        for key in (
            "candidate_prompt_version",
            "candidate_prompt_sha256",
            "candidate_contract_sha256",
            "stage",
            "effective_venue",
            "session_bucket",
            "review_classification",
            "candidate_primary_decision_ev_delta_pct",
            "candidate_probe_cost_adjusted_ev_pct",
            "runtime_apply_authority",
        )
    }
    handoff_body = {
        "schema": calibration.ACTION_OUTCOME_OPTIMIZER_HANDOFF_SCHEMA,
        "target_date": target_date,
        "selected_review_candidate": None,
        "review_ready_candidates": [],
        "thin_positive_review_candidates": [thin_summary],
        "source_contract_pass": True,
        "decision_authority": "optimizer_source_only_advisory_no_runtime_selection",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report_body = {
        "schema": calibration.SCHEMA,
        "policy_version": calibration.POLICY_VERSION,
        "target_date": target_date,
        "clean_tuning_baseline_date": calibration.CLEAN_BASELINE_DATE,
        "candidate_count": 1,
        "review_candidate_count": 0,
        "review_ready_candidates": [],
        "selected_review_candidate": None,
        "thin_positive_review_candidate_count": 1,
        "thin_positive_review_candidates": [thin_summary],
        "candidate_summaries": [candidate_summary],
        "source_contract_summary": {
            "cross_cohort_aggregation_forbidden": True,
            "invalid_sources_excluded_before_calibration": True,
            "candidate_selection_requires_verified_source_hash": True,
            "conflicting_duplicate_traces_excluded": True,
            "cross_cohort_outcome_conflicts_excluded": True,
        },
        "optimizer_handoff": {
            **handoff_body,
            "handoff_content_sha256": calibration._canonical_sha256(handoff_body),
        },
        **optimizer.SOURCE_ONLY_AUTHORITY,
    }
    _write(
        calibration_dir / f"ai_decision_action_outcome_calibration_{target_date}.json",
        calibration._with_artifact_content_sha256(report_body),
    )

    report = optimizer.build_report(
        target_date,
        prepared_path=prepared_path,
        bridge_path=bridge_path,
    )

    selected = report["stage_optimizers"]["entry"]["selected_challenger"]
    assert report["action_outcome_calibration_input"]["status"] == (
        "connected_validated_source_only"
    )
    assert selected["action_outcome_calibration"]["review_classification"] == (
        "thin_positive_review"
    )
    assert selected["action_outcome_calibration"]["selection_authority"] is False
    assert report["runtime_effect"] is False


def test_optimizer_does_not_fall_back_to_stale_action_outcome_calibration(
    monkeypatch, tmp_path
):
    calibration_dir = tmp_path / "calibration"
    monkeypatch.setattr(optimizer, "ACTION_OUTCOME_CALIBRATION_DIR", calibration_dir)
    _write(
        calibration_dir / "ai_decision_action_outcome_calibration_2026-09-07.json",
        {"target_date": "2026-09-07"},
    )

    payload, path, warnings = optimizer._latest_action_outcome_calibration("2026-09-08")

    assert payload == {}
    assert path is not None and path.name.endswith("2026-09-08.json")
    assert warnings == ["action_outcome_calibration_not_available_for_target_date"]


def test_action_outcome_advisory_rejects_ambiguous_same_version_cohorts() -> None:
    common = {
        "candidate_prompt_version": "candidate_v1",
        "stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
    }
    calibration_payload = {
        "candidate_summaries": [
            {
                **common,
                "candidate_prompt_sha256": "a" * 64,
                "candidate_contract_sha256": "b" * 64,
            },
            {
                **common,
                "candidate_prompt_sha256": "c" * 64,
                "candidate_contract_sha256": "d" * 64,
            },
        ]
    }

    advisory = optimizer._action_outcome_advisory(
        calibration_payload,
        stage="entry",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        candidate_prompt_version="candidate_v1",
    )

    assert advisory is None
