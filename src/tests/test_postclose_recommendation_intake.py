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


def recommendation(owner="widget", axis="signal", decision="observe"):
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


def test_all_owners_mirrors_nested_workorders_and_invalid_siblings(tmp_path):
    reports, paths = sources(tmp_path, [order()])
    a = recommendation()
    invalid = {
        "decision": "code_patch_required",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    write(
        paths["widget_advisory_calibration"],
        {
            "target_date": DATE,
            "recommendations": [a, invalid],
            "mirror": a,
            "child": {"code_improvement_orders": [order("child")]},
        },
    )
    result = mod.build_intake(reports, DATE)
    assert result["counts"]["intake_total"] == 4
    assert result["counts"]["implementation_requested_total"] == 3
    assert (
        len(
            next(
                row
                for row in result["rows"]
                if row["native_id"] == a["recommendation_id"]
            )["sources"]
        )
        == 2
    )
    assert result["counts"]["invalid_or_missing_authority_total"] == 1
    assert result["issues"] == []
    assert any(
        "native_identity_invalid" in row.get("validation_issues", [])
        for row in result["rows"]
    )
    assert result["conservation_pass"]
    assert result["all_implementations_completed"] is False


def test_conflicting_mirror_cannot_reuse_identity(tmp_path):
    reports, paths = sources(tmp_path)
    a = recommendation()
    write(
        paths["widget_advisory_calibration"],
        {
            "target_date": DATE,
            "recommendations": [a],
            "mirror": {**a, "allowed_runtime_apply": True},
        },
    )
    result = mod.build_intake(reports, DATE)
    assert any("conflicting_native_id" in issue for issue in result["issues"])


def test_widget_source_date_not_next_effective_date(tmp_path):
    reports, paths = sources(tmp_path)
    write(
        paths["widget_symbol_runtime_policy_apply"],
        {"source_target_date": DATE, "effective_date": "2026-09-10"},
    )
    result = mod.build_intake(reports, DATE)
    assert result["status"] == "accounted"
    assert result["all_implementations_completed"]


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


def test_isolated_native_gap_is_visible_warning_not_global_completion_failure(tmp_path):
    reports, paths = sources(tmp_path)
    write(
        paths["widget_advisory_calibration"],
        {
            "target_date": DATE,
            "recommendations": [
                {
                    "decision": "code_patch_required",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            ],
        },
    )
    checklist = tmp_path / "checklist.md"
    publish_summaries(reports, checklist)
    result = handoff.verify_summary_handoff(
        DATE, report_dir=reports, checklist_path=checklist
    )
    assert result["status"] == "pass"
    intake = result["recommendation_intake"]
    assert intake["status"] == "warning"
    assert intake["counts"]["invalid_or_missing_authority_total"] == 1
    assert intake["all_implementations_completed"] is False


def test_semantics_not_just_hash_markers_and_late_machine_generation(tmp_path):
    reports, paths = sources(tmp_path, [order()])
    checklist = tmp_path / "checklist.md"
    tower = publish_summaries(reports, checklist)
    verify = lambda: handoff.verify_summary_handoff(
        DATE, report_dir=reports, checklist_path=checklist
    )
    assert (
        verify()["status"] == "pass"
    )  # Operational handoff, not implementation completion.
    assert not verify()["recommendation_intake"]["implementation_fixed_point"]
    payload = json.loads(tower.read_text())
    payload.pop("recommendation_intake")
    write(tower, payload)
    assert (
        "postclose_summary_handoff:tower:intake_semantics_mismatch"
        in verify()["issues"]
    )
    publish_summaries(reports, checklist)
    checklist.write_text(
        handoff.checklist_marker(
            handoff.source_receipt(
                handoff.source_paths(reports, DATE, "checklist"), DATE
            )
        )
    )
    assert (
        "postclose_summary_handoff:checklist:intake_semantics_mismatch"
        in verify()["issues"]
    )
    publish_summaries(reports, checklist)
    write(
        paths["machine_entry_timing_tuning"],
        {"target_date": DATE, "recommendations": [recommendation("machine")]},
    )
    assert any("source_generation_mismatch" in issue for issue in verify()["issues"])
    publish_summaries(reports, checklist)
    assert verify()["status"] == "pass"
    assert verify()["recommendation_intake"]["counts"]["intake_total"] == 2


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
    result = _selected_runtime(plan, {}, manifest)
    assert result["planned_family_count"] == result["selected_family_count"] == 1
    assert result["planned_only_families"] == ["recheck"]
    assert result["manifest_only_families"] == ["cancel_wait"]
    assert result["selection_evidence"] == "manifest_selection_receipt_consistent"
    assert result["pid_consumption"] == "not_verified_by_apply_plan"
    assert _selected_runtime(plan, {})["selected_family_count"] is None
    manifest["target_date"] = "2026-09-08"
    assert _selected_runtime(plan, {}, manifest)["selected_family_count"] is None


def test_empty_versus_missing_and_nonfinite_sources(tmp_path):
    reports, paths = sources(tmp_path)
    assert mod.build_intake(reports, DATE)["implementation_fixed_point"]
    paths["machine_entry_timing_tuning"].unlink()
    result = mod.build_intake(reports, DATE)
    assert result["status"] == "waiting_sources"
    assert not result["implementation_fixed_point"]
    paths["machine_entry_timing_tuning"].write_text('{"target_date":NaN}')
    assert mod.build_intake(reports, DATE)["status"] == "fail"


@pytest.mark.parametrize(
    "change,expected",
    [
        ({}, "done"),
        ({"ActiveState": "activating"}, "waiting_running"),
        ({"ActiveState": "failed", "Result": "exit-code"}, "failed_producer_terminal"),
        (
            {"ExecMainStartTimestamp": "2026-09-08 21:15:00 KST"},
            "waiting_exact_date_run",
        ),
        ({"ExecMainStartTimestamp": "2026-09-10 00:15:00 KST"}, "done"),
        ({"LoadState": "not-found"}, "failed_installed_owner_contract"),
        ({"LoadState": "masked", "UnitFileState": "masked"}, "done_off_masked"),
    ],
)
def test_late_independent_producers_must_be_terminal_or_explicitly_off(
    tmp_path, change, expected
):
    reports, _ = sources(tmp_path)
    properties = {
        "LoadState": "loaded",
        "UnitFileState": "static",
        "ActiveState": "inactive",
        "Result": "success",
        "ExecMainStartTimestamp": f"{DATE} 21:15:00 KST",
        **change,
    }

    def runner(cmd, **kwargs):
        assert cmd[:2] == ["systemctl", "show"]
        assert kwargs["timeout"] == 10
        return SimpleNamespace(
            returncode=0, stdout="\n".join(f"{k}={v}" for k, v in properties.items())
        )

    assert set(
        handoff.installed_producer_terminal_states(
            DATE, runner=runner, report_dir=reports
        ).values()
    ) == {expected}


@pytest.mark.parametrize("bad_source", [None, {"target_date": "2026-09-08"}])
def test_successful_unit_cannot_hide_missing_or_previous_date_source(
    tmp_path, bad_source
):
    reports, paths = sources(tmp_path)
    path = paths["widget_advisory_calibration"]
    if bad_source is None:
        path.unlink()
    else:
        write(path, bad_source)
    runner = lambda *a, **kw: SimpleNamespace(
        returncode=0,
        stdout="LoadState=loaded\nUnitFileState=static\nActiveState=inactive\n"
        f"Result=success\nExecMainStartTimestamp={DATE} 21:15:00 KST\n",
    )
    result = handoff.installed_producer_terminal_states(
        DATE, runner=runner, report_dir=reports
    )
    assert result["korstockscan-samsung-widget-evaluation.service"] == (
        "failed_exact_source_artifact:widget_advisory_calibration"
    )
    assert result["korstockscan-machine-microstructure-final-refresh.service"] == "done"


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


def test_json_boolean_is_not_numeric_zero_in_inventory_and_summary(tmp_path):
    report = workorder([order()])
    report["inventory_contract"]["runtime_effect"] = 0
    assert "inventory_contract_mismatch" in contract.contract_issues(report, DATE)
    reports, _ = sources(tmp_path)
    checklist = tmp_path / "checklist.md"
    tower = publish_summaries(reports, checklist)
    payload = json.loads(tower.read_text())
    payload["source_generation_contract"]["runtime_effect"] = 0
    payload["recommendation_intake"]["counts"]["intake_total"] = False
    write(tower, payload)
    result = handoff.verify_summary_handoff(
        DATE, report_dir=reports, checklist_path=checklist
    )
    assert (
        "postclose_summary_handoff:tower:source_generation_mismatch" in result["issues"]
    )
    assert (
        "postclose_summary_handoff:tower:intake_semantics_mismatch" in result["issues"]
    )


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
    assert (
        result["historical_pid_receipt"]["status"]
        == "reported_pass_matching_date_and_families"
    )
    assert result["historical_pid_receipt"]["as_of"] is None
    assert (
        result["historical_pid_receipt"]["current_process_identity_revalidated"]
        is False
    )
    assert result["pid_consumption"] == "not_verified_by_apply_plan"
    pid["target_date"] = "2026-09-08"
    assert (
        _selected_runtime({}, {}, manifest, target_date=DATE, pid_receipt=pid)[
            "historical_pid_receipt"
        ]["status"]
        == "unmatched_or_failed"
    )


def test_real_builders_close_new_date_handoff_and_preserve_manual_tasks(
    tmp_path, monkeypatch
):
    from src.engine import build_next_stage2_checklist as checklist_builder
    from src.engine.automation import tuning_performance_control_tower as tower_builder
    from src.tests.test_build_next_stage2_checklist import _patch_dirs as checklist_dirs
    from src.tests.test_tuning_performance_control_tower import (
        _patch_dirs as tower_dirs,
    )

    checklist_dirs(monkeypatch, tmp_path)
    tower_dirs(monkeypatch, tmp_path)
    reports, paths = sources(tmp_path, [order()], [order("nonselected", "observe")])
    write(
        reports / f"threshold_cycle_ev/threshold_cycle_ev_{DATE}.json", {"date": DATE}
    )
    target = tmp_path / "docs/checklists/2026-09-10-stage2-todo-checklist.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    manual = "- [ ] `[ManualOwner] preserve` (`Due: 2026-09-10`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: RuntimeStability`)"
    target.write_text("# Existing checklist\n\n" + manual + "\n")
    tower_builder.build_tuning_performance_control_tower(DATE)
    for _ in range(2):
        checklist_builder.build_next_stage2_checklist(DATE)
    text = target.read_text()
    assert text.count(mod.SECTION_START) == text.count(mod.SECTION_END) == 1
    assert text.count(manual) == 1
    assert (
        handoff.verify_summary_handoff(DATE, report_dir=reports, checklist_path=target)[
            "status"
        ]
        == "pass"
    )
    write(
        paths["machine_entry_timing_tuning"],
        {"target_date": DATE, "recommendations": [recommendation("machine")]},
    )
    assert (
        handoff.verify_summary_handoff(DATE, report_dir=reports, checklist_path=target)[
            "status"
        ]
        == "fail"
    )
    tower_builder.build_tuning_performance_control_tower(DATE)
    checklist_builder.build_next_stage2_checklist(DATE)
    assert (
        handoff.verify_summary_handoff(DATE, report_dir=reports, checklist_path=target)[
            "status"
        ]
        == "pass"
    )


def test_current_producer_emits_complete_contract_and_render_failure_preserves_prior(
    tmp_path, monkeypatch
):
    from src.engine import build_code_improvement_workorder as producer
    from src.engine import verify_threshold_cycle_postclose_chain as verifier

    monkeypatch.setattr(
        producer, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "inputs/pattern"
    )
    monkeypatch.setattr(producer, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "inputs/ev")
    monkeypatch.setattr(
        producer, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", tmp_path / "output"
    )
    monkeypatch.setattr(producer, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "docs")
    write(
        producer.automation_report_path(DATE),
        {"date": DATE, "code_improvement_orders": []},
    )
    write(producer.threshold_ev_report_path(DATE), {"date": DATE})
    result = producer.build_code_improvement_workorder(DATE, include_swing=False)
    assert contract.contract_issues(result, DATE) == []
    assert (
        verifier._code_improvement_workorder_contract_status(result, target_date=DATE)[
            "status"
        ]
        == "pass"
    )
    assert verifier._workorder_source_fingerprint_issues(result) == []
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
