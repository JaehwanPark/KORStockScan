from __future__ import annotations

import json

from src.engine.ai_prompt_contracts import (
    decision_quality_v2_14_setup_risk_adjudicator_system_prompt,
    decision_quality_v2_15_bounded_recovery_system_prompt,
    decision_quality_v2_16_sequential_recovery_system_prompt,
)
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer


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
