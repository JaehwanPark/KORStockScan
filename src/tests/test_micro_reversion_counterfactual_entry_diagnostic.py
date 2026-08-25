from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from src.engine.scalping.micro_reversion import counterfactual_entry_diagnostic as diag
from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle
from src.engine.scalping.micro_reversion.replay_ablation_contract import (
    CURRENT_ARMS,
    CURRENT_DESIGN_VERSION,
)


def _hash(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _hash_json(value: object) -> str:
    return diag._sha256(value)


def _row(
    *,
    target_date: str,
    parent: str,
    stock_code: str,
    actions: tuple[str, str, str],
    outcome_ev: float,
) -> dict:
    baseline_action, control_action, candidate_action = actions
    control_contract_sha256 = _hash("control-contract")
    candidate_contract_sha256 = _hash("candidate-contract")
    control_prompt_sha256 = _hash(f"control-prompt-{parent}")
    candidate_prompt_sha256 = _hash(f"candidate-prompt-{parent}")
    full_parent_census = {
        "paired_replay_parent_id": parent,
        "arms": [
            {
                "arm": CURRENT_ARMS[0],
                "prompt_contract_sha256": _hash("baseline-contract"),
                "prompt_sha256": _hash("baseline-prompt"),
            },
            {
                "arm": CURRENT_ARMS[1],
                "prompt_contract_sha256": control_contract_sha256,
                "prompt_sha256": control_prompt_sha256,
            },
            {
                "arm": CURRENT_ARMS[2],
                "prompt_contract_sha256": candidate_contract_sha256,
                "prompt_sha256": candidate_prompt_sha256,
            },
        ],
    }

    def exposure(action: str) -> float:
        return outcome_ev if action == "BUY" else 0.0

    row = {
        "target_date": target_date,
        "ablation_design_version": CURRENT_DESIGN_VERSION,
        "r3_tuning_axis": "prompt_contract_effect_on_ask_depletion_context",
        "paired_replay_parent_id": parent,
        "decision_trace_id": f"trace-{parent}",
        "decision_stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "regular",
        "stock_code": stock_code,
        "captured_control_action": "WAIT",
        "lifecycle_findings": ["lifecycle_exact_join_missing"],
        "baseline_action": baseline_action,
        "control_action": control_action,
        "candidate_action": candidate_action,
        "baseline_ev_pct": exposure(baseline_action),
        "baseline_ev_basis": "full_exposure_ev_pct",
        "control_ev_pct": exposure(control_action),
        "control_ev_basis": "full_exposure_ev_pct",
        "candidate_ev_pct": exposure(candidate_action),
        "candidate_ev_basis": "full_exposure_ev_pct",
        "action_neutral_outcome_ev_pct": outcome_ev,
        "action_neutral_outcome_ev_basis": "source_quality_adjusted_ev_pct",
        "action_neutral_mfe_pct": max(outcome_ev, 0.8),
        "action_neutral_mae_pct": min(outcome_ev, -0.2),
        "action_neutral_first_hit": (
            "net_target_first" if outcome_ev > 0 else "adverse_first"
        ),
        "action_neutral_target_first_delay_sec": 3.0 if outcome_ev > 0 else None,
        "full_parent_arm_count": 3,
        "full_parent_arms": list(CURRENT_ARMS),
        "full_parent_census_verified": True,
        "full_parent_census": full_parent_census,
        "full_parent_census_sha256": _hash_json(full_parent_census),
        "control_contract_sha256": control_contract_sha256,
        "candidate_contract_sha256": candidate_contract_sha256,
        "control_prompt_sha256": control_prompt_sha256,
        "candidate_prompt_sha256": candidate_prompt_sha256,
        "outcome_label_content_sha256": _hash(f"label-{parent}"),
        "selected_cost_profile_id": "kiwoom-2026-08-18",
        "selected_cost_profile_content_sha256": _hash("selected-cost"),
        "cost_profile_artifact_sha256": _hash("cost-artifact"),
        "cost_catalog_content_sha256": _hash("cost-catalog"),
        "symbol_master_artifact_sha256": _hash("symbol-master"),
        "symbol_metadata_record_sha256": _hash(f"symbol-{stock_code}"),
    }
    execution_source_commitment_content = {
        "schema": "main_ai_quality_counterfactual_entry_execution_source_v1",
        "target_date": target_date,
        "paired_replay_parent_id": parent,
        "decision_trace_id": f"trace-{parent}",
        "execution_report_content_sha256": _hash(f"execution-content-{parent}"),
        "execution_report_artifact_sha256": _hash(f"execution-artifact-{parent}"),
        "three_arm_evaluation_content_sha256": _hash(f"evaluation-{parent}"),
        "evaluation_parent_row_sha256": _hash(f"evaluation-row-{parent}"),
        "execution_parent_request_refs_sha256": _hash(f"request-refs-{parent}"),
        "execution_parent_results_sha256": _hash(f"results-{parent}"),
        "outcome_label_content_sha256": row["outcome_label_content_sha256"],
        "outcome_label_artifact_sha256": _hash(f"outcome-artifact-{parent}"),
        "materialized_report_content_sha256": _hash(f"materialized-{parent}"),
        "materialized_report_artifact_sha256": _hash(f"materialized-artifact-{parent}"),
        "provider_ablation_sample_floor_content_sha256": _hash(
            f"provider-floor-content-{parent}"
        ),
        "provider_ablation_sample_floor_artifact_sha256": _hash(
            f"provider-floor-artifact-{parent}"
        ),
        "full_parent_census_sha256": row["full_parent_census_sha256"],
    }
    execution_source_commitment = {
        **execution_source_commitment_content,
        "commitment_sha256": _hash_json(execution_source_commitment_content),
    }
    row["execution_source_commitment"] = execution_source_commitment
    row["execution_source_commitment_sha256"] = execution_source_commitment[
        "commitment_sha256"
    ]
    return row


def _reseal(artifact: dict) -> None:
    content = {
        key: value
        for key, value in artifact.items()
        if key != "artifact_content_sha256"
    }
    artifact["artifact_content_sha256"] = diag._sha256(content)


def test_counterfactual_entry_keeps_full_no_transition_and_open_transition_census():
    rows = [
        _row(
            target_date="2026-08-25",
            parent="p-no-change",
            stock_code="005930",
            actions=("WAIT", "WAIT", "WAIT"),
            outcome_ev=-0.3,
        ),
        _row(
            target_date="2026-08-25",
            parent="p-feature-open",
            stock_code="000660",
            actions=("WAIT", "BUY", "BUY"),
            outcome_ev=0.4,
        ),
        _row(
            target_date="2026-08-25",
            parent="p-prompt-open",
            stock_code="035420",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=0.6,
        ),
        _row(
            target_date="2026-08-25",
            parent="p-prompt-open-adverse",
            stock_code="051910",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=-0.3,
        ),
    ]

    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=rows
    )

    assert artifact["status"] == "counterfactual_entry_diagnostic_evaluated"
    assert artifact["eligible_parent_count"] == 4
    assert artifact["candidate_count"] == 0
    assert artifact["candidates"] == []
    assert artifact["runtime_candidate_eligible"] is False
    assert artifact["actual_lifecycle_evidence"] is False
    assert artifact["realized_profit_claim_allowed"] is False
    window = artifact["partitions"][0]["windows"]["5"]
    assert window["full_parent_census_count"] == 4
    comparisons = {row["comparison_role"]: row for row in window["comparisons"]}
    assert comparisons["feature_effect"]["exposure_opened_count"] == 1
    assert comparisons["prompt_effect"]["exposure_opened_count"] == 2
    assert comparisons["composite_effect"]["exposure_opened_count"] == 3
    assert comparisons["composite_effect"]["no_action_transition_count"] == 1
    assert comparisons["prompt_effect"]["new_exposure_first_hit_counts"] == {
        "adverse_first": 1,
        "net_target_first": 1,
    }
    assert (
        comparisons["prompt_effect"]["new_exposure_target_first_delay_sample_count"]
        == 1
    )
    assert (
        comparisons["prompt_effect"]["new_exposure_mean_target_first_delay_sec"] == 3.0
    )
    candidate_arm = window["arms"]["C"]
    assert candidate_arm["exposure_open_first_hit_counts"] == {
        "adverse_first": 1,
        "net_target_first": 2,
    }
    assert candidate_arm["exposure_open_target_first_delay_sample_count"] == 2
    assert candidate_arm["exposure_open_median_target_first_delay_sec"] == 3.0
    assert "source_rows" not in artifact
    assert "input_census" not in artifact
    assert artifact["input_disposition_counts"] == {"eligible": 4}
    assert "actual_holding_duration" not in json.dumps(artifact)


def test_counterfactual_entry_requires_provider_floor_commitment() -> None:
    row = _row(
        target_date="2026-08-25",
        parent="p-floor-binding",
        stock_code="005930",
        actions=("WAIT", "BUY", "BUY"),
        outcome_ev=0.4,
    )
    row["execution_source_commitment"].pop(
        "provider_ablation_sample_floor_content_sha256"
    )
    content = {
        key: value
        for key, value in row["execution_source_commitment"].items()
        if key != "commitment_sha256"
    }
    row["execution_source_commitment"]["commitment_sha256"] = _hash_json(content)
    row["execution_source_commitment_sha256"] = row["execution_source_commitment"][
        "commitment_sha256"
    ]

    with pytest.raises(
        ValueError,
        match="counterfactual_entry_execution_source_commitment_invalid",
    ):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25",
            rows=[row],
        )


def test_counterfactual_entry_global_blocker_disables_all_metrics():
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25",
        rows=[
            _row(
                target_date="2026-08-25",
                parent="p1",
                stock_code="005930",
                actions=("WAIT", "BUY", "BUY"),
                outcome_ev=0.4,
            )
        ],
        global_blockers=["current_lifecycle_exact_census_invalid:2026-08-25"],
    )

    assert artifact["status"] == "counterfactual_entry_diagnostic_blocked"
    assert artifact["partitions"] == []
    assert artifact["candidate_count"] == 0


def test_counterfactual_entry_rejects_non_natural_or_duplicate_parent():
    row = _row(
        target_date="2026-08-25",
        parent="p1",
        stock_code="005930",
        actions=("WAIT", "WAIT", "BUY"),
        outcome_ev=0.4,
    )
    invalid = deepcopy(row)
    invalid["captured_control_action"] = "BUY"
    with pytest.raises(ValueError, match="natural_control_absence_required"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25", rows=[invalid]
        )
    with pytest.raises(ValueError, match="parent_census_duplicate"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25", rows=[row, deepcopy(row)]
        )

    extra_finding = deepcopy(row)
    extra_finding["lifecycle_findings"].append("lifecycle_invalid_transition")
    with pytest.raises(ValueError, match="sole_lifecycle_finding_required"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25", rows=[extra_finding]
        )


def test_counterfactual_entry_rejects_resealed_full_parent_census_mutation():
    row = _row(
        target_date="2026-08-25",
        parent="p1",
        stock_code="005930",
        actions=("WAIT", "WAIT", "BUY"),
        outcome_ev=0.4,
    )
    row["full_parent_census"]["arms"][0]["prompt_sha256"] = _hash(
        "resealed-foreign-baseline-prompt"
    )

    with pytest.raises(ValueError, match="full_parent_census_invalid"):
        diag.build_counterfactual_entry_diagnostic(target_date="2026-08-25", rows=[row])


def test_counterfactual_entry_validator_rebuilds_partitions_and_rejects_actual_fields():
    rows = [
        _row(
            target_date="2026-08-25",
            parent="p1",
            stock_code="005930",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=0.4,
        )
    ]
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25",
        rows=rows,
    )
    artifact["partitions"][0]["windows"]["5"]["arms"]["C"][
        "exposure_open_mean_target_first_delay_sec"
    ] = 999.0
    _reseal(artifact)
    with pytest.raises(ValueError, match="partition_rebuild_mismatch"):
        diag.validate_counterfactual_entry_diagnostic(
            artifact,
            expected_source_rows=rows,
            expected_exclusions=[],
            expected_global_blockers=[],
        )

    rows = [
        _row(
            target_date="2026-08-25",
            parent="p1",
            stock_code="005930",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=0.4,
        )
    ]
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25",
        rows=rows,
    )
    artifact["actual_holding_duration_sec"] = 1.0
    _reseal(artifact)
    with pytest.raises((ValueError, AssertionError)):
        diag.validate_counterfactual_entry_diagnostic(
            artifact,
            expected_source_rows=rows,
            expected_exclusions=[],
            expected_global_blockers=[],
        )


def test_counterfactual_entry_rejects_fabricated_duplicate_and_overlap_exclusions():
    row = _row(
        target_date="2026-08-25",
        parent="p1",
        stock_code="005930",
        actions=("WAIT", "WAIT", "BUY"),
        outcome_ev=0.4,
    )
    with pytest.raises(ValueError, match="counterfactual_entry_exclusion_invalid"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25",
            rows=[],
            exclusions=[{"reason": "fabricated"}, {"reason": "fabricated"}],
        )
    with pytest.raises(ValueError, match="exclusion_findings_invalid"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25",
            rows=[],
            exclusions=[
                {
                    "source_row": row,
                    "reason": "counterfactual_entry_contract_not_eligible",
                    "findings": ["fabricated"],
                }
            ],
        )
    exclusion = {
        "source_row": row,
        "reason": "source_quality_audit_not_pass",
        "findings": ["source_quality_audit_not_pass"],
    }
    with pytest.raises(ValueError, match="full_parent_census_duplicate"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25",
            rows=[row],
            exclusions=[exclusion],
        )
    with pytest.raises(ValueError, match="full_parent_census_duplicate"):
        diag.build_counterfactual_entry_diagnostic(
            target_date="2026-08-25",
            rows=[],
            exclusions=[exclusion, deepcopy(exclusion)],
        )


def test_counterfactual_entry_binds_each_excluded_parent_to_its_exact_cause():
    first = _row(
        target_date="2026-08-25",
        parent="p1",
        stock_code="005930",
        actions=("WAIT", "WAIT", "BUY"),
        outcome_ev=0.4,
    )
    second = _row(
        target_date="2026-08-25",
        parent="p2",
        stock_code="000660",
        actions=("WAIT", "WAIT", "BUY"),
        outcome_ev=0.4,
    )
    original_exclusions = [
        {
            "source_row": first,
            "reason": "source_quality_audit_not_pass",
            "findings": ["source_quality_audit_not_pass"],
        },
        {
            "source_row": second,
            "reason": "economic_reference_not_verified",
            "findings": ["economic_reference_not_verified"],
        },
    ]
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=[], exclusions=original_exclusions
    )
    swapped_exclusions = deepcopy(original_exclusions)
    swapped_exclusions[0].update(
        {
            "reason": "economic_reference_not_verified",
            "findings": ["economic_reference_not_verified"],
        }
    )
    swapped_exclusions[1].update(
        {
            "reason": "source_quality_audit_not_pass",
            "findings": ["source_quality_audit_not_pass"],
        }
    )

    with pytest.raises(ValueError, match="external_input_census_mismatch"):
        diag.validate_counterfactual_entry_diagnostic(
            artifact,
            expected_source_rows=[],
            expected_exclusions=swapped_exclusions,
            expected_global_blockers=[],
        )


def test_counterfactual_entry_external_census_rejects_coherent_action_reseal():
    original_rows = [
        _row(
            target_date="2026-08-25",
            parent="p1",
            stock_code="005930",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=0.4,
        )
    ]
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25",
        rows=original_rows,
    )
    tampered_rows = deepcopy(original_rows)
    tampered_rows[0]["candidate_action"] = "WAIT"
    tampered_rows[0]["candidate_ev_pct"] = 0.0
    artifact["partitions"] = diag._build_partitions(
        [diag._canonical_source_row(row) for row in tampered_rows],
        target_date="2026-08-25",
    )
    tampered_summary = diag._input_census_summary(
        source_rows=[diag._canonical_source_row(row) for row in tampered_rows],
        exclusions=[],
    )
    artifact.update(tampered_summary)
    _reseal(artifact)

    with pytest.raises(ValueError, match="external_input_census_mismatch"):
        diag.validate_counterfactual_entry_diagnostic(
            artifact,
            expected_source_rows=original_rows,
            expected_exclusions=[],
            expected_global_blockers=[],
        )


def test_counterfactual_entry_validator_requires_external_input_census():
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=[]
    )

    with pytest.raises(ValueError, match="external_input_census_required"):
        diag.validate_counterfactual_entry_diagnostic(artifact)


def test_counterfactual_entry_rejects_resealed_fabricated_global_blocker():
    rows = [
        _row(
            target_date="2026-08-25",
            parent="p1",
            stock_code="005930",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=0.4,
        )
    ]
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=rows
    )
    artifact["global_blockers"] = ["fabricated_global_blocker"]
    artifact["partitions"] = []
    artifact["status"] = "counterfactual_entry_diagnostic_blocked"
    _reseal(artifact)

    with pytest.raises(ValueError, match="external_global_blockers_mismatch"):
        diag.validate_counterfactual_entry_diagnostic(
            artifact,
            expected_source_rows=rows,
            expected_exclusions=[],
            expected_global_blockers=[],
        )


def test_counterfactual_entry_large_rolling_census_stays_bounded():
    rows = [
        _row(
            target_date="2026-08-25",
            parent=f"p-{index:05d}",
            stock_code="005930",
            actions=("WAIT", "WAIT", "BUY"),
            outcome_ev=0.4,
        )
        for index in range(5_500)
    ]

    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=rows
    )

    assert artifact["full_parent_census_count"] == 5_500
    assert len(diag._canonical_bytes(artifact)) < 64 * 1024
    assert "source_rows" not in artifact
    assert "input_census" not in artifact


def test_counterfactual_entry_partition_size_overflow_blocks_only_diagnostic(
    monkeypatch,
):
    monkeypatch.setattr(diag, "MAX_PERSISTED_ARTIFACT_BYTES", 5_000)
    row = _row(
        target_date="2026-08-25",
        parent="p1",
        stock_code="005930",
        actions=("WAIT", "WAIT", "BUY"),
        outcome_ev=0.4,
    )

    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=[row]
    )

    assert artifact["status"] == "counterfactual_entry_diagnostic_blocked"
    assert artifact["global_blockers"] == [
        "counterfactual_entry_partition_artifact_size_bound_exceeded"
    ]
    assert artifact["partitions"] == []
    assert artifact["candidate_count"] == 0


def test_counterfactual_schema_is_rejected_by_actual_r3_consumer():
    artifact = diag.build_counterfactual_entry_diagnostic(
        target_date="2026-08-25", rows=[]
    )

    with pytest.raises(ValueError, match="r3_manifest_schema_invalid"):
        cycle._validate_r3_source_only_manifest(artifact)
