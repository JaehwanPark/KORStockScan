import hashlib
import json
from types import SimpleNamespace

import pytest

from src.engine.automation import postclose_recommendation_intake as mod
from src.engine.automation import postclose_summary_handoff as handoff
from src.engine.automation import postclose_workorder_contract as contract
from src.engine.automation.tuning_performance_control_tower import _selected_runtime
from src.engine.build_code_improvement_workorder import _previous_workorder_lineage
from src.engine.monitoring.machine_recommendation_identity import bind_recommendation

DATE = "2026-09-09"




def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def order(native="order_a", decision="implement_now"):
    return {
        "order_id": native,
        "decision": decision,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "required_downstream": ["direct_consumer"],
        "files_likely_touched": ["src/engine/automation/example.py"],
        "acceptance_tests": ["exact_source_and_consumer_contract"],
    }


def workorder(selected=(), nonselected=()):
    from collections import Counter

    source = [
        {
            "label": "fixture",
            "path": "fixture.json",
            "exists": False,
            "sha256": None,
            "size_bytes": 0,
            "mtime_ns": None,
        }
    ]
    inputs = {
        "source_hash": contract.digest(source),
        "schema_version": 2,
        "producer_contract_version": "code_improvement_workorder_producer_v8",
        "max_orders": 12,
        "include_swing": False,
    }
    rows = [*selected, *nonselected]
    report = {
        "date": DATE,
        "schema_version": 2,
        "producer_contract_version": inputs["producer_contract_version"],
        "orders": list(selected),
        "non_selected_orders": list(nonselected),
        "source_fingerprint": source,
        "source_hash": inputs["source_hash"],
        "generation_inputs": inputs,
        "generation_hash": contract.digest(inputs),
        "generation_id": f"{DATE}-{contract.digest(inputs)[:12]}",
        "summary": {
            "source_order_count": len(rows),
            "selected_order_count": len(selected),
            "non_selected_order_count": len(nonselected),
            "decision_counts": dict(Counter(r["decision"] for r in rows)),
            "selected_decision_counts": dict(Counter(r["decision"] for r in selected)),
            "non_selected_decision_counts": dict(
                Counter(r["decision"] for r in nonselected)
            ),
        },
    }
    report["inventory_contract"] = contract.inventory(report)
    return report


def sources(tmp_path, selected=(), nonselected=()):
    reports = tmp_path / "data/report"
    paths = mod.source_paths(reports, DATE)
    for label in mod.SOURCE_LABELS:
        write(
            paths[label],
            {
                "target_date": DATE,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "recommendations": [],
            },
        )
    write(paths["code_improvement_workorder"], workorder(selected, nonselected))
    return reports, paths


def recommendation(owner="episode", axis="signal", decision="observe"):
    row = {
        "decision": decision,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    bind_recommendation(
        row,
        producer=owner,
        scope="exact_scope",
        axis=axis,
        proposal={"axis": axis},
        consumer="existing_consumer",
        acceptance="exact_source_and_consumer",
    )
    return row


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (
            lambda r: r.pop("source_fingerprint"),
            "source_fingerprint_missing_or_invalid",
        ),
        (lambda r: r["orders"][0].update(order_id=""), "native_id_missing_or_invalid"),
        (
            lambda r: r["non_selected_orders"][0].update(order_id="order_a"),
            "native_id_duplicate",
        ),
        (lambda r: r.update(non_selected_orders=[]), "source_order_count_mismatch"),
        (lambda r: r.pop("generation_hash"), "generation_identity_mismatch"),
        (lambda r: r.update(source_hash="0" * 64), "source_hash_mismatch"),
        (
            lambda r: r["summary"].update(selected_order_count=True),
            "selected_order_count_mismatch",
        ),
        (
            lambda r: r["orders"][0].update(runtime_effect=True),
            "inventory_contract_mismatch",
        ),
        (lambda r: r["orders"][0].update(decision=[]), "decision_missing_or_invalid"),
    ],
)
def test_full_workorder_contract_rejects_previously_missed_mutations(
    mutation, expected
):
    report = workorder([order()], [order("order_b", "observe")])
    assert not contract.contract_issues(report, DATE)
    mutation(report)
    assert expected in contract.contract_issues(report, DATE)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "invalid_or_missing_authority"),
        ("false", "invalid_or_missing_authority"),
        (0, "invalid_or_missing_authority"),
        (True, "user_authority"),
        (False, "eligible_runtime_effect_false"),
    ],
)
def test_authority_is_not_truthiness_or_a_blanket_strategy_veto(
    tmp_path, value, expected
):
    row = order()
    row["runtime_effect"] = value
    reports, _ = sources(tmp_path, [row])
    result = mod.build_intake(reports, DATE)
    assert not result["issues"]
    assert result["rows"][0]["authority_class"] == expected
    assert result["conservation_pass"]
    assert result["all_implementations_completed"] is False


def test_nonselected_change_and_rank_change_are_different():
    a, b = order(), order("order_b", "observe")
    previous = {"orders": [a], "non_selected_orders": [b]}
    updated = {**b, "decision": "implement_now"}
    result = _previous_workorder_lineage(previous, [a], [updated])
    assert result["decision_changed_order_ids"] == ["order_b"]
    assert result["contract_changed_order_ids"] == ["order_b"]
    result = _previous_workorder_lineage(previous, [b], [a])
    assert result["new_order_ids"] == result["removed_order_ids"] == []
    assert result["contract_changed_order_ids"] == []
    assert result["new_selected_order_ids"] == ["order_b"]







def receipt(reports, paths):
    row = mod.build_intake(reports, DATE)["rows"][0]
    evidence_path = reports.parent.parent / "docs/review.json"
    write(evidence_path, {"review": "passed", "tests": "passed", "consumer": "passed"})
    item = {
        "owner": row["owner"],
        "native_id": row["native_id"],
        "row_sha256": row["row_sha256"],
        "source_sha256": row["sources"][0]["sha256"],
        "final_disposition": "implemented_pass1",
        "reason": "Reviewed exact source-only repair",
        "acceptance_owner": "existing_review_owner",
        "evidence": [
            {
                "kind": kind,
                "path": str(evidence_path),
                "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            }
            for kind in ("code_review", "targeted_validation", "consumer_handoff")
        ],
    }
    payload = {
        "schema": mod.DISPOSITION_SCHEMA,
        "source_date": DATE,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "rows": [item],
    }
    write(paths["postclose_recommendation_dispositions"], payload)
    return payload, evidence_path


def test_completed_claim_needs_exact_generation_and_acyclic_evidence(tmp_path):
    reports, paths = sources(tmp_path, [order(decision="already_implemented")])
    assert mod.build_intake(reports, DATE)["counts"]["eligible_actionable_open"] == 1
    _, evidence_path = receipt(reports, paths)
    result = mod.build_intake(reports, DATE)
    assert result["all_implementations_completed"]
    assert result["counts"]["implemented_pass1"] == 1
    assert result["rows"][0]["deployment"] == "unverified"
    assert result["rows"][0]["economic_acceptance"] == "not_evaluated_by_handoff"
    source_map = handoff.source_paths(reports, DATE, "tower")
    before = handoff.source_receipt(source_map, DATE)
    write(evidence_path, {"review": "changed"})
    with pytest.raises(RuntimeError, match="changed_during_render"):
        handoff.assert_sources_unchanged(before, source_map)
    result = mod.build_intake(reports, DATE)
    assert result["status"] == "fail"
    assert result["counts"]["eligible_actionable_open"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_test",
        "stale_row",
        "stale_source",
        "observed_request",
        "cyclic",
        "external",
    ],
)
def test_invalid_dispositions_never_close_work(tmp_path, mutation):
    reports, paths = sources(tmp_path, [order()])
    payload, _ = receipt(reports, paths)
    item = payload["rows"][0]
    if mutation == "missing_test":
        item["evidence"].pop(1)
    elif mutation == "stale_row":
        item["row_sha256"] = "0" * 64
    elif mutation == "stale_source":
        item["source_sha256"] = "0" * 64
    elif mutation == "observed_request":
        item["final_disposition"] = "observed_no_patch"
    else:
        item["evidence"][0]["path"] = (
            "data/report/postclose_done_controller/done.json"
            if mutation == "cyclic"
            else "/etc/passwd"
        )
    write(paths["postclose_recommendation_dispositions"], payload)
    result = mod.build_intake(reports, DATE)
    assert result["status"] == "fail"
    assert result["counts"]["eligible_actionable_open"] == 1
    assert not result["implementation_fixed_point"]


def publish_summaries(reports, checklist):
    intake = mod.build_intake(reports, DATE)
    tower = (
        reports
        / "tuning_performance_control_tower"
        / f"tuning_performance_control_tower_{DATE}.json"
    )
    write(
        tower,
        {
            "date": DATE,
            "recommendation_intake": intake,
            "selected_runtime": _selected_runtime({}, {}, {}, target_date=DATE),
            "source_generation_contract": handoff.source_receipt(
                handoff.source_paths(reports, DATE, "tower"), DATE
            ),
        },
    )
    checklist.write_text(
        mod.markdown_section(intake)
        + handoff.checklist_marker(
            handoff.source_receipt(
                handoff.source_paths(reports, DATE, "checklist"), DATE
            )
        )
    )
    return tower






def test_equal_plan_manifest_counts_are_not_equal_selection():
    plan = {
        "target_date": DATE,
        "source_date": "2026-09-08",
        "auto_apply_selected": [{"family": "recheck"}],
        "runtime_env_handoff_verification": {
            "status": "pass",
            "target_date": DATE,
            "selected_families": ["cancel_wait"],
        },
    }
    manifest = {
        "target_date": DATE,
        "source_date": "2026-09-08",
        "selected_families": ["cancel_wait"],
    }
    result = _selected_runtime(plan, {}, manifest, target_date=DATE)
    assert result["owner"] == "runtime_policy_bootstrap"
    assert result["selected_families"] == ["cancel_wait"]
    assert result["common_candidate_selection_retired"] is True
    assert _selected_runtime(plan, {}, target_date=DATE)["selected_families"] == []
    manifest["target_date"] = "2026-09-08"
    assert (
        _selected_runtime(plan, {}, manifest, target_date=DATE)["target_date"]
        == "2026-09-08"
    )








def test_workorder_source_race_never_binds_new_hash_to_old_input(tmp_path):
    from src.engine import build_code_improvement_workorder as producer

    path = tmp_path / "source.json"
    write(path, {"a": 1})
    token = producer._SOURCE_READS.set({})
    try:
        assert producer._load_json(path) == {"a": 1}
        write(path, {"a": 2})
        with pytest.raises(producer.WorkorderSourceChanged):
            producer._source_fingerprint({"source": path})
        with pytest.raises(producer.WorkorderSourceChanged):
            producer._load_json(path)
    finally:
        producer._SOURCE_READS.reset(token)


def test_new_source_hash_contract_preserves_path_as_nonidentity_provenance():
    report = workorder([order()])
    report["source_hash_contract"] = contract.SOURCE_HASH_CONTRACT
    identity = [
        {key: value for key, value in entry.items() if key != "path"}
        for entry in report["source_fingerprint"]
    ]
    report["source_hash"] = contract.digest(identity)
    report["generation_inputs"]["source_hash"] = report["source_hash"]
    report["generation_inputs"]["source_hash_contract"] = contract.SOURCE_HASH_CONTRACT
    report["generation_hash"] = contract.digest(report["generation_inputs"])
    report["generation_id"] = f"{DATE}-{report['generation_hash'][:12]}"

    assert contract.contract_issues(report, DATE) == []
    report["source_fingerprint"][0]["path"] = "/another/release/source.json"
    assert contract.contract_issues(report, DATE) == []


def test_permission_error_is_not_a_zero_byte_source(monkeypatch, tmp_path):
    from src.engine import build_code_improvement_workorder as producer
    from pathlib import Path

    path = tmp_path / "source.json"
    write(path, {})

    def denied(self):
        raise PermissionError("fixture")

    monkeypatch.setattr(Path, "read_bytes", denied)
    with pytest.raises(PermissionError):
        producer._file_fingerprint(path, "source")




def test_existing_pid_receipt_is_reported_without_current_process_claim():
    manifest = {
        "target_date": DATE,
        "source_date": "2026-09-08",
        "selected_families": ["a"],
    }
    pid = {
        "target_date": DATE,
        "selected_families": ["a"],
        "pid": 12,
        "pid_passed": True,
        "pid_env_available": True,
    }
    result = _selected_runtime({}, {}, manifest, target_date=DATE, pid_receipt=pid)
    assert result["verification_status"] == "not_generated"
    assert result["pid"] == 12
    assert result["pid_passed"] is True
    assert result["common_candidate_selection_retired"] is True
    pid["target_date"] = "2026-09-08"
    assert _selected_runtime(
        {}, {}, manifest, target_date=DATE, pid_receipt=pid
    )["verification_status"] == "not_generated"


def test_direct_tower_reads_summary_and_verifier(tmp_path, monkeypatch):
    from src.engine.automation import tuning_performance_control_tower as tower_builder
    reports = tmp_path / "data/report"
    monkeypatch.setattr(tower_builder, "REPORT_ROOT_DIR", reports)
    monkeypatch.setattr(
        tower_builder, "REPORT_DIR", reports / "tuning_performance_control_tower"
    )
    write(
        reports
        / "runtime_approval_summary"
        / f"runtime_approval_summary_{DATE}.json",
        {"status": "direct_evidence_complete", "direct_evidence_state": "complete"},
    )
    write(
        reports
        / "threshold_cycle_postclose_verification"
        / f"threshold_cycle_postclose_verification_{DATE}.json",
        {"status": "pass", "issues": []},
    )
    result = tower_builder.build_tuning_performance_control_tower(DATE)
    assert result["status"] == "pass"
    assert result["summary"]["common_tuning_search_retired"] is True


def test_current_producer_emits_complete_contract_and_render_failure_preserves_prior(
    tmp_path, monkeypatch
):
    from src.engine import build_code_improvement_workorder as producer
    monkeypatch.setattr(producer, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "inputs/ev")
    monkeypatch.setattr(
        producer, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", tmp_path / "output"
    )
    monkeypatch.setattr(producer, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "docs")
    write(producer.threshold_ev_report_path(DATE), {"date": DATE})
    result = producer.build_code_improvement_workorder(DATE, include_swing=False)
    assert contract.contract_issues(result, DATE) == []
    assert result["generation_phase"] == "manual_final_direct_family"
    assert result["semantic_source_hash"] == result["source_hash"]
    json_path, md_path = producer.code_improvement_workorder_paths(DATE)
    original = (json_path.read_bytes(), md_path.read_bytes())

    def fail_render(report):
        raise ValueError("fixture render failure")

    monkeypatch.setattr(
        producer, "render_code_improvement_workorder_markdown", fail_render
    )
    with pytest.raises(ValueError, match="fixture render"):
        producer.build_code_improvement_workorder(DATE, include_swing=False)
    assert (json_path.read_bytes(), md_path.read_bytes()) == original
