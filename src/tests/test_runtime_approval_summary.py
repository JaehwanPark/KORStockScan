import hashlib
import json
from pathlib import Path

import pytest

from src.engine import runtime_approval_summary as mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _with_artifact_sha(payload: dict) -> dict:
    value = dict(payload)
    value["artifact_sha256"] = hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return value


def _patch(monkeypatch, tmp_path: Path) -> Path:
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "runtime_approval_summary")
    return data


def _seed_required(target_date: str) -> None:
    for owner, path in mod._paths(target_date).items():
        if owner not in mod.REQUIRED_DIRECT_OWNERS:
            continue
        _write(
            path,
            {
                "report_type": owner,
                "target_date": target_date,
                "status": "valid_empty" if owner == "entry_cancel_wait" else "pass",
                "runtime_effect": False,
            },
        )


def test_summary_completes_direct_evidence_without_fabricating_economics(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)

    report = mod.build_runtime_approval_summary(target)

    assert report["status"] == mod.DIRECT_EVIDENCE_COMPLETE
    assert report["direct_evidence_state"] == "complete"
    assert report["economic_state"] == "not_applicable"
    assert report["daily_threshold_cycle_retired"] is True
    assert report["threshold_cycle_ev_retired"] is True
    assert report["common_tuning_candidate_created"] is False
    assert report["available_required_source_count"] == report["required_source_count"]
    assert report["sources"]["entry_split_policy"]["required"] is False
    assert report["actual_order_submitted"] is False


def test_main_mechanistic_report_flags_do_not_prove_future_owner_support():
    evidence = mod._economic_projection(
        "main_mechanistic_entry",
        {
            "report_scope": "main_mechanistic_entry",
            "noncompact_sections_refreshed": True,
            "machine_full_evaluation": {
                "state": "insufficient_mature_sample",
                "full_population_count": 1715,
                "independent_candidate_count": 0,
                "holdout_cost_adjusted_ev_pct": 0.0,
                "holdout_paired_delta_ev_pct": 0.005,
                "daily_net_profit_delta_krw": None,
                "daily_net_profit_status": (
                    "not_available_without_exact_changed_decision_owner_replay"
                ),
                "promotion_pass": False,
            },
        },
    )

    assert evidence["comparison_status"] == "source_gap"
    assert evidence["resolution_mode"] == "producer_repair"
    assert evidence["historical_evidence_state"] is None
    assert evidence["prospective_resolution_mode"] is None
    assert evidence["policy_handoff_state"] == "blocked"
    assert evidence["actual_net_profit_improvement"] is None


def test_compact_historical_gap_keeps_verified_future_natural_owner():
    payload = {
        "status": "source_contract_blocked",
        "evaluation_state": "blocked_source",
        "promotion_pass": False,
        "candidate_selection": {"status": "insufficient_sample"},
        "candidate_zero_disposition": {
            "status": "source_gap",
            "blockers": [
                {"blocker": "exact_stop_distance_missing_or_invalid"}
            ],
        },
        "metrics": {
            "paired_comparable_count": 0,
            "operating_economic_comparison": {"status": "source_gap"},
        },
        "prospective_source_contract": {"implementation_verified": True},
        "historical_evidence_state": (
            "exact_source_unrecoverable_preserved_excluded"
        ),
    }

    evidence = mod._economic_projection("compact_auxiliary", payload)

    assert evidence["comparison_status"] == "source_gap"
    assert evidence["resolution_mode"] == "historical_unrecoverable"
    assert evidence["historical_evidence_state"] == (
        "exact_source_unrecoverable_preserved_excluded"
    )
    assert evidence["prospective_resolution_mode"] == "natural_maturity"
    assert evidence["policy_handoff_state"] == "incumbent_preserved"
    assert evidence["candidate_count"] == 0
    assert evidence["actual_net_profit_improvement"] is None

    payload["prospective_source_contract"] = {"implementation_verified": False}
    unverified = mod._economic_projection("compact_auxiliary", payload)
    assert unverified["prospective_resolution_mode"] == "producer_repair"
    assert unverified["policy_handoff_state"] == "blocked"


def test_summary_distinguishes_missing_required_from_optional(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    mod._paths(target)["entry_split"].unlink()

    report = mod.build_runtime_approval_summary(target)

    assert report["status"] == mod.DIRECT_EVIDENCE_INCOMPLETE
    assert "entry_split:missing" in report["blocking_reasons"]
    assert all("entry_split_policy:missing" != item for item in report["blocking_reasons"])


def test_wrapper_disabled_owner_is_not_required(monkeypatch, tmp_path):
    data = _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    mod._paths(target)["machine_entry"].unlink()
    _write(
        data / "report" / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json",
        {"target_date": target, "producer_flags": {"samsung_machine_entry_tuning": False}},
    )

    report = mod.build_runtime_approval_summary(target)

    assert report["status"] == mod.DIRECT_EVIDENCE_COMPLETE
    assert report["sources"]["machine_entry"]["required"] is False
    assert report["sources"]["machine_entry"]["applicability"] == "not_applicable_disabled_by_wrapper"
    assert report["owner_contract"]["fallback_used"] is True


def test_large_report_uses_semantically_bound_candidate_companion(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    path = mod._paths(target)["low_price_two_leg"]
    semantic_sha = "a" * 64
    paired = {"profiles": {}}
    content = (json.dumps(
        {
            "schema": "low_price_two_leg_tuning_report_v10",
            "target_date": target,
            "artifact_hash": semantic_sha,
            "paired_economic_search": paired,
            "padding": "x" * 1024,
        },
        indent=2,
    ) + "\n").encode()
    path.write_bytes(content)
    candidate = mod._paths(target)["low_price_candidate"]
    _write(
        candidate,
        {
            "target_date": target,
            "source_report_path": str(path),
            "source_report_schema": "low_price_two_leg_tuning_report_v10",
            "source_report_artifact_hash": semantic_sha,
            "paired_economic_search": paired,
            "decision": "incumbent_preserved",
            "allowed_runtime_apply": False,
        },
    )
    monkeypatch.setattr(mod, "MAX_DIRECT_JSON_BYTES", 512)

    report = mod.build_runtime_approval_summary(target)
    row = report["sources"]["low_price_two_leg"]

    assert report["status"] == mod.DIRECT_EVIDENCE_COMPLETE
    assert row["read_mode"] == "bounded_terminal_companion"
    assert row["semantic_companion"]["verified"] is True
    assert row["sha256"] == hashlib.sha256(content).hexdigest()


def test_large_report_without_matching_companion_fails_closed(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    path = mod._paths(target)["low_price_two_leg"]
    paired = {"profiles": {}}
    path.write_text(
        json.dumps(
            {
                "schema": "low_price_two_leg_tuning_report_v10",
                "target_date": target,
                "artifact_hash": "a" * 64,
                "paired_economic_search": paired,
                "padding": "x" * 1024,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write(
        mod._paths(target)["low_price_candidate"],
        {
            "target_date": target,
            "source_report_path": str(path),
            "source_report_schema": "low_price_two_leg_tuning_report_v10",
            "source_report_artifact_hash": "b" * 64,
            "paired_economic_search": paired,
        },
    )
    monkeypatch.setattr(mod, "MAX_DIRECT_JSON_BYTES", 512)

    report = mod.build_runtime_approval_summary(target)

    assert report["status"] == mod.DIRECT_EVIDENCE_INCOMPLETE
    assert "low_price_two_leg:semantic_unverified_large_source" in report["blocking_reasons"]


def test_economic_states_keep_source_gap_no_edge_and_validated_edge_distinct(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    _write(
        mod._paths(target)["entry_cancel_wait"],
        {
            "target_date": target,
            "allowed_runtime_apply": True,
            "economic_evaluation": {"status": "source_gap", "blocker": "missing_fill_lineage"},
        },
    )
    _write(
        mod._paths(target)["entry_split"],
        {"target_date": target, "economic_acceptance": {"status": "no_edge", "paired_sample_count": 12, "delta_ev_pct": -0.03}},
    )
    _write(
        mod._paths(target)["scale_in_split"],
        {
            "target_date": target,
            "evaluation_state": {
                "status": "validated_edge",
                "candidates": [{"name": "candidate"}],
                "allowed_runtime_apply": True,
                "delta_ev_pct": 0.07,
                "actual_net_profit_improvement": None,
            },
        },
    )
    _write(mod._paths(target)["scale_in_split_policy"], {"target_date": target, "allowed_runtime_apply": True})

    report = mod.build_runtime_approval_summary(target)

    assert report["sources"]["entry_cancel_wait"]["economic_evidence"]["comparison_status"] == "source_gap"
    assert report["sources"]["entry_cancel_wait"]["economic_evidence"]["policy_apply_allowed"] is False
    assert report["sources"]["entry_split"]["economic_evidence"]["comparison_status"] == "measured_no_edge"
    scale = report["sources"]["scale_in_split"]["economic_evidence"]
    assert scale["comparison_status"] == "validated_edge"
    assert scale["actual_net_profit_improvement"] is None
    assert report["validated_edge_count"] == 1
    assert report["policy_candidate_count"] == 1
    assert report["policy_handoff_state"] == "candidate_published"


def test_validated_edge_without_dated_policy_receipt_is_source_gap(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    _write(
        mod._paths(target)["scale_in_split"],
        {
            "target_date": target,
            "evaluation_state": {
                "status": "validated_edge",
                "candidates": [{"name": "candidate"}],
                "allowed_runtime_apply": True,
            },
        },
    )

    report = mod.build_runtime_approval_summary(target)
    evidence = report["sources"]["scale_in_split"]["economic_evidence"]

    assert evidence["comparison_status"] == "source_gap"
    assert evidence["first_blocker"] == "validated_candidate_policy_receipt_missing"
    assert report["validated_edge_count"] == 0


def test_compact_direct_policy_receipt_is_bound_to_paired_evaluation(monkeypatch, tmp_path):
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    data = _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    paired = compact.sealed(
        {
            "schema": compact.SCHEMA,
            "target_date": target,
            "status": "complete",
            "evaluation_state": "evaluated_hold",
            "evaluation_fingerprint": "f" * 64,
            "promotion_pass": False,
            "candidate_improvement_proven": False,
            "candidate_zero_disposition": {
                "status": "measured_no_edge",
                "blockers": [{"blocker": "non_positive_paired_delta"}],
            },
            "metrics": {
                "paired_comparable_count": 12,
                "delta_net_ev_pct": -0.03,
                "operating_economic_comparison": {
                    "incumbent": {"ev_pct": 0.11, "es10": -0.4, "fill_participation": 0.5},
                    "candidate": {"ev_pct": 0.08, "es10": -0.42, "fill_participation": 0.5},
                    "robust_paired_delta_ev_lower_bound_pct": -0.08,
                    "portfolio_daily_net_delta_krw": -1200,
                    "portfolio_capital_delta_krw_minutes": 0,
                },
            },
            "chronological_validation": {"learning_pairs": [], "holdout_consumed": True},
            "owner_execution_model_status": "validated",
            "closure_test": "forward_holdout_receipt",
            **compact.AUTHORITY,
        }
    )
    _write(mod._paths(target)["compact_auxiliary"], paired)
    bundle = {
        "schema": policy.SCHEMA,
        "source_date": "2026-09-20",
        "target_date": "2026-09-21",
        "compact_evaluation_source_date": target,
        # Top-level source ownership belongs to the main-machine report.  The
        # compact receipt must use its family-specific source field below.
        "source_artifact_sha256": "a" * 64,
        "compact_paired_artifact_sha256": paired["artifact_content_sha256"],
        "compact_evaluation_fingerprint": paired["evaluation_fingerprint"],
    }
    bundle["bundle_sha256"] = policy.digest(bundle)
    _write(
        data / "runtime/mechanistic_entry_policy/policy_2026-09-21.json",
        bundle,
    )

    report = mod.build_runtime_approval_summary(target)
    source = report["sources"]["compact_auxiliary"]

    assert source["policy_receipt"]["valid"] is True
    assert source["economic_evidence"]["comparison_status"] == "measured_no_edge"
    assert source["economic_evidence"]["policy_handoff_state"] == "incumbent_preserved"


def test_next_effective_date_is_pending_until_preopen_verification(monkeypatch, tmp_path):
    data = _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    policy = mod._paths(target)["entry_cancel_wait_policy"]
    _write(
        policy,
        {"source_date": target, "effective_date": "2026-09-21", "status": "incumbent_preserved"},
    )

    pending = mod.build_runtime_approval_summary(target)

    assert pending["preopen_consumption_state"] == "pending"
    assert pending["natural_acceptance_state"] == "not_due"
    assert pending["preopen_consumption_receipt"]["apply_date"] == "2026-09-21"

    _write(
        data / "runtime" / "policy_bootstrap" / "runtime_policy_bootstrap_2026-09-21.json",
        {"target_date": "2026-09-21", "selected_families": []},
    )
    _write(
        data / "runtime" / "policy_bootstrap" / "runtime_policy_bootstrap_verify_2026-09-21.json",
        {
            "target_date": "2026-09-21",
            "status": "pass",
            "passed": True,
            "pid": None,
            "pid_passed": None,
            "pid_env_available": True,
        },
    )
    verified = mod.build_runtime_approval_summary(target)

    assert verified["preopen_consumption_state"] == "verified"
    assert verified["natural_acceptance_state"] == "not_due"
    assert verified["preopen_consumption_receipt"]["actual_pid_consumed"] is False

    _write(
        data / "runtime" / "policy_bootstrap" / "runtime_policy_bootstrap_verify_2026-09-21.json",
        {
            "target_date": "2026-09-21",
            "status": "pass",
            "passed": True,
            "pid": 4321,
            "pid_passed": True,
            "pid_env_available": True,
        },
    )
    consumed = mod.build_runtime_approval_summary(target)

    assert consumed["preopen_consumption_state"] == "verified"
    assert consumed["natural_acceptance_state"] == "pending"
    assert consumed["preopen_consumption_receipt"]["actual_pid_consumed"] is True
    assert consumed["preopen_consumption_receipt"]["runtime_pid"] == 4321


def test_pending_maturity_requires_verified_future_generation_contract(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    path = mod._paths(target)["entry_cancel_wait"]
    _write(
        path,
        {"target_date": target, "economic_evaluation": {"status": "pending_maturity"}},
    )

    blocked = mod.build_runtime_approval_summary(target)
    evidence = blocked["sources"]["entry_cancel_wait"]["economic_evidence"]
    assert evidence["comparison_status"] == "source_gap"
    assert evidence["first_blocker"] == "future_generation_contract_unverified"

    _write(
        path,
        {
            "target_date": target,
            "economic_evaluation": {
                "status": "pending_maturity",
                "future_generation_contract_verified": True,
            },
        },
    )
    pending = mod.build_runtime_approval_summary(target)
    assert pending["sources"]["entry_cancel_wait"]["economic_evidence"]["comparison_status"] == "pending_maturity"


def test_rising_missed_policy_receipt_is_semantically_bound(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    source_payload = _with_artifact_sha(
        {
            "schema_version": 2,
            "report_type": "rising_missed_classifier_prior",
            "target_date": target,
            "status": "measured_no_edge",
            "economic_evaluation": {
                "comparison_status": "measured_no_edge",
                "paired_sample_count": 50,
                "candidates": [{"disposition": "measured_no_edge"}],
                "allowed_runtime_apply": False,
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    )
    _write(mod._paths(target)["rising_missed"], source_payload)
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": target,
        "effective_date": "2026-09-21",
        "status": "incumbent_preserved",
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "source_report_sha256": source_payload["artifact_sha256"],
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "runtime_env_overrides": {},
    }
    policy["policy_sha256"] = mod.direct_policy_digest(policy)
    _write(mod._paths(target)["rising_missed_policy"], policy)

    report = mod.build_runtime_approval_summary(target)

    source = report["sources"]["rising_missed"]
    assert source["economic_evidence"]["comparison_status"] == "measured_no_edge"
    assert source["policy_receipt"]["valid"] is True
    assert source["economic_evidence"]["policy_handoff_state"] == "incumbent_preserved"


def test_rising_validated_edge_uses_economic_authority_and_bound_policy(
    monkeypatch, tmp_path
):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    source_payload = _with_artifact_sha(
        {
            "schema_version": 2,
            "report_type": "rising_missed_classifier_prior",
            "target_date": target,
            "status": "validated_edge",
            "economic_evaluation": {
                "comparison_status": "validated_edge",
                "paired_sample_count": 50,
                "candidates": [{"disposition": "validated_edge"}],
                "allowed_runtime_apply": True,
                "validated_candidate_count": 1,
            },
            # The report itself never has direct runtime authority.
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    )
    _write(mod._paths(target)["rising_missed"], source_payload)
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": target,
        "effective_date": "2026-09-21",
        "status": "validated_edge",
        "selected_axis": "positive_support_min",
        "allowed_runtime_apply": True,
        "runtime_effect": True,
        "source_report_sha256": source_payload["artifact_sha256"],
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "runtime_env_overrides": {
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-09-21",
            "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN": "1",
        },
    }
    policy["policy_sha256"] = mod.direct_policy_digest(policy)
    policy["runtime_env_overrides"][
        "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256"
    ] = policy["policy_sha256"]
    _write(mod._paths(target)["rising_missed_policy"], policy)

    report = mod.build_runtime_approval_summary(target)

    source = report["sources"]["rising_missed"]
    assert source["economic_evidence"]["comparison_status"] == "validated_edge"
    assert source["economic_evidence"]["policy_apply_allowed"] is True
    assert source["policy_receipt"]["valid"] is True


def test_rising_policy_receipt_rejects_multiple_runtime_axes(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    source_payload = _with_artifact_sha(
        {
            "schema_version": 2,
            "report_type": "rising_missed_classifier_prior",
            "target_date": target,
            "status": "validated_edge",
            "economic_evaluation": {
                "comparison_status": "validated_edge",
                "candidates": [{"disposition": "validated_edge"}],
                "allowed_runtime_apply": True,
                "validated_candidate_count": 1,
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    )
    _write(mod._paths(target)["rising_missed"], source_payload)
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": target,
        "effective_date": "2026-09-21",
        "status": "validated_edge",
        "selected_axis": "positive_support_min",
        "allowed_runtime_apply": True,
        "runtime_effect": True,
        "source_report_sha256": source_payload["artifact_sha256"],
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "runtime_env_overrides": {
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-09-21",
            "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN": "1",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO": "0.0015",
        },
    }
    policy["policy_sha256"] = mod.direct_policy_digest(policy)
    policy["runtime_env_overrides"][
        "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256"
    ] = policy["policy_sha256"]
    _write(mod._paths(target)["rising_missed_policy"], policy)

    report = mod.build_runtime_approval_summary(target)

    source = report["sources"]["rising_missed"]
    assert source["policy_receipt"]["valid"] is False
    assert source["economic_evidence"]["comparison_status"] == "source_gap"


def test_large_expansion_uses_current_late_machine_dependency_proof(monkeypatch, tmp_path):
    from src.engine.automation import machine_research_closed_loop_refresh as native
    day = "2026-09-17"
    path = tmp_path / "low_price_two_leg_expanded_candidate_research" / f"study_{day}.json"
    _write(path, {"target_date": day, "enriched": True})
    receipt_path = tmp_path / "machine_research_closed_loop" / f"machine_research_closed_loop_{day}.json"
    receipt = dict(target_date=day, dependency_sources={str(path.resolve()): "semantic_hash"}, native_valid=True)
    _write(receipt_path, receipt)
    monkeypatch.setattr(native, "validate_current_receipt", lambda value, day: value.get("native_valid") is True)
    payload, proof, error = mod._large_companion("low_price_expansion", path, day, mod._sha(path), {})
    assert error is None and proof["verified"]
    assert proof["contract"] == "machine_research_closed_loop_current_dependency"
    receipt["native_valid"] = False
    _write(receipt_path, receipt)
    assert mod._large_companion("low_price_expansion", path, day, mod._sha(path), {})[2] == "semantic_unverified_large_source"
    receipt.update(native_valid=True, dependency_sources={str(tmp_path / "other.json"): "unrelated"})
    _write(receipt_path, receipt)
    assert mod._large_companion("low_price_expansion", path, day, mod._sha(path), {})[2] == "semantic_unverified_large_source"


def test_main_proxy_population_and_ev_are_not_operating_economics():
    payload = {"machine_full_evaluation": dict(state="source_gap", full_population_count=1715,
        paired_comparable_count=1710, holdout_incumbent_ev_pct=-0.005,
        holdout_cost_adjusted_ev_pct=-0.005, holdout_paired_delta_ev_pct=0.0,
        downstream_operating_evidence_complete=False, structural_blocker="machine_operating_population_unbound")}
    row = mod._economic_projection("main_mechanistic_entry", payload)
    assert row["paired_sample_count"] is None
    assert row["incumbent_cost_adjusted_ev_pct"] is None
    assert row["paired_delta_ev_pct"] is None
    assert row["diagnostic_terminal_proxy"]["comparable_count"] == 1710
    assert row["diagnostic_terminal_proxy"]["delta_ev_pct"] == 0
    assert row["future_contract_state"] == "unverified_requires_owner_evidence"


def test_active_expansion_source_gap_is_not_retired_or_not_applicable(tmp_path):
    path = tmp_path / "study.json"
    _write(path, dict(target_date="2026-09-17", status="partial_source_quality",
        source_symbol_count=204, eligible_source_symbol_count=197,
        quarantined_source_symbol_count=7, recommendation_count=0,
        joint_allocation_gate=dict(status="allocation_blocked", reason="allocator_snapshot_contract_invalid")))
    row = mod._economic_projection("low_price_expansion", mod._expansion_economic_projection(path))
    assert row["comparison_status"] == "source_gap"
    assert row["closure_test"] and row["first_blocker"] == "allocator_snapshot_contract_invalid"
    assert row["resolution_mode"] != "retired_or_not_applicable"


def test_main_supported_economics_never_uses_terminal_proxy_as_currency_ev():
    payload = {'machine_full_evaluation': dict(state='evaluated_no_edge',
        downstream_operating_evidence_complete=True, holdout_incumbent_ev_pct=99.,
        holdout_cost_adjusted_ev_pct=999., holdout_paired_delta_ev_pct=900.,
        operating_economics={'incumbent':{'ev_pct':.2},'candidate':{'ev_pct':.3},
            'robust_paired_delta_ev_lower_bound_pct':.05})}
    row = mod._economic_section('main_mechanistic_entry', payload)
    assert row['incumbent_ev_pct'] == .2
    assert row['candidate_ev_pct'] == .3
    assert abs(row['delta_ev_pct'] - .1) < 1e-10
    assert row['diagnostic_terminal_proxy']['delta_ev_pct'] == 900.


def test_pid_consumption_requires_matching_effective_date_bootstrap(monkeypatch, tmp_path):
    data = _patch(monkeypatch, tmp_path)
    day = "2026-09-21"
    directory = data / "runtime/policy_bootstrap"
    manifest = directory / f"runtime_policy_bootstrap_{day}.json"
    verification = directory / f"runtime_policy_bootstrap_verify_{day}.json"
    _write(manifest, {"target_date": day})
    _write(verification, {"target_date": day, "status": "pass", "passed": True,
                          "pid": 4321, "pid_passed": True, "pid_env_available": True})
    state, natural, receipt = mod._runtime_consumption_state(day, {})
    assert (state, natural) == ("not_due", "not_applicable")
    assert receipt["actual_pid_consumed"] is False
    sources = {"policy": {"exists": True, "target_date_matches": True, "effective_date": day}}
    _write(manifest, {"target_date": "2026-09-20"})
    state, natural, receipt = mod._runtime_consumption_state(day, sources)
    assert state == "rejected" and natural == "not_due"
    assert receipt["actual_pid_consumed"] is False


def test_machine_admission_selection_is_not_portfolio_edge(monkeypatch):
    from src.engine.scalping import entry_strategy_policy as strategy
    measured = dict(status="supported_machine_admission", win_rate_pct=None,
                    selected_path_ev_pct=None, selected_opportunity_count=0)
    train = dict(status="supported_machine_admission", win_rate_pct=60., selected_path_ev_pct=-.40886)
    result = dict(status="selected_machine_policy", promotion_pass=True,
        selection_basis="win_rate_then_net_ev_without_profit_floor", evaluated_candidate_count=94,
        candidate={"parent_policy": {}, "evidence": {"train": {"economics": train}, "holdout": {"economics": measured}}})
    monkeypatch.setattr(strategy, "select_report_candidate", lambda _: ("KRX|KRX_REGULAR", result))
    monkeypatch.setattr(strategy, "promotion_errors", lambda *args: [])
    row = mod._economic_projection("main_mechanistic_entry", {})
    assert row["comparison_status"] == "unsupported_scope"
    assert row["candidate_count"] == 1
    assert row["policy_apply_allowed"] is False
    assert row["candidate_cost_adjusted_ev_pct"] is None
    assert row["actual_net_profit_improvement"] is None
    assert row["diagnostic_machine_selection"]["train"]["win_rate_pct"] == 60.
    assert row["diagnostic_machine_selection"]["holdout"]["selected_opportunity_count"] == 0


def test_explicit_prepared_date_does_not_slide_to_later_sibling(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTCLOSE_PREPARED_EFFECTIVE_DATE", "2026-09-22")
    sources = {str(i): dict(exists=True, target_date_matches=True, effective_date=day)
               for i,day in enumerate(("2026-09-22", "2026-09-23"))}
    _, _, receipt = mod._runtime_consumption_state("2026-09-21", sources)
    assert receipt["apply_date"] == "2026-09-22"
    assert receipt["effective_dates"] == ["2026-09-22", "2026-09-23"]
    monkeypatch.setenv("POSTCLOSE_PREPARED_EFFECTIVE_DATE", "2026-09-24")
    with pytest.raises(ValueError, match="prepared_effective_date_missing"):
        mod._runtime_consumption_state("2026-09-21", sources)
