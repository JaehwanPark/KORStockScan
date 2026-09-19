import hashlib
import json
from pathlib import Path

from src.engine import runtime_approval_summary as mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


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
        {"target_date": "2026-09-21", "status": "pass"},
    )
    verified = mod.build_runtime_approval_summary(target)

    assert verified["preopen_consumption_state"] == "verified"
    assert verified["natural_acceptance_state"] == "pending"


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
