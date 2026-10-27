import gzip
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.automation import postclose_summary_handoff as mod


@pytest.mark.parametrize("fault", [None, "missing_handoff", "source", "date", "ledger"])
def test_delay_stage_preserves_only_exact_prepared_code_handoff(
    tmp_path, monkeypatch, fault
):
    from src.engine.scalping import (
        pre_submit_delay_initial_policy as I,
        pre_submit_delay_tuning as T,
    )

    reports = tmp_path / "data/report"
    reports.mkdir(parents=True)
    report = reports / "report.json"
    policy = reports / "policy.json"
    ledger = reports / "ledger.json"
    report.write_text(
        json.dumps(
            {
                "source_date": "2026-10-15" if fault == "date" else "2026-10-16",
                "source_sha256": "source",
            }
        )
    )
    policy.write_text(
        json.dumps(
            {
                "schema": "pre_submit_delay_policy_v2",
                "source_date": "2026-10-16",
                "code_contract_sha256": "original",
                "effective_from": "2026-10-19",
            }
        )
    )
    if fault == "ledger":
        ledger.write_text(json.dumps({"compact_source_sha256": "different"}))
    monkeypatch.setattr(
        mod,
        "stage_artifacts",
        lambda *a: {
            "pre_submit_delay_tuning": report,
            "pre_submit_delay_policy": policy,
        },
    )
    monkeypatch.setattr(
        mod, "stage_input_paths", lambda *a: {"pre_submit_delay_source_ledger": ledger}
    )
    monkeypatch.setattr(I, "validate", lambda *a: None)
    monkeypatch.setattr(I, "code_contract", lambda: "current")
    calls = []

    def source(*args):
        calls.append("source")
        if fault == "source":
            raise ValueError("source_changed")

    def code(value, day):
        assert value["code_contract_sha256"] == "original" and day == "2026-10-19"
        calls.append("code")
        if fault == "missing_handoff":
            raise ValueError("prepared_receipt_missing")

    monkeypatch.setattr(I, "verify_source", source)
    monkeypatch.setattr(T, "_verify_runtime_code_contract", code)
    issues = mod._safe_stage_output_issues(reports, "2026-10-16", "pre_submit_delay")
    assert bool(issues) == bool(fault)
    if fault is None:
        assert calls == ["source", "code"]
    if fault in {"source", "date"}:
        assert calls == ["source"]


def test_machine_barrier_waits_for_exact_inputs_and_allows_scoped_recovery(
    tmp_path, monkeypatch
):
    day = "2026-09-21"
    monkeypatch.setattr(mod, "producer_receipt_issues", lambda *a: [])
    assert "ai_decision_outcome_labels" in mod.machine_input_issues(tmp_path, day)[0]
    for label in (
        "ai_decision_outcome_labels",
        "low_price_two_leg_expanded_candidate_research",
        "runtime_approval_summary",
    ):
        path = tmp_path / label / f"{label}_{day}.json"
        path.parent.mkdir()
        path.write_text(json.dumps({"target_date": day}))
    main = (
        tmp_path
        / "threshold_cycle_postclose_status"
        / f"threshold_cycle_postclose_{day}.status.json"
    )
    main.parent.mkdir()
    main.write_text('{"status":"running"}')
    assert mod.wait_for_machine_inputs(tmp_path, day, timeout=0) == 75
    main.write_text('{"status":"failed"}')
    assert mod.wait_for_machine_inputs(tmp_path, day, timeout=0) == 0
    path.write_text('{"target_date":"2026-09-17"}')
    assert mod.wait_for_machine_inputs(tmp_path, day, timeout=0) == 75


def _publish(tmp_path, target="2026-09-07"):
    reports = tmp_path / "data" / "report"
    tower_path = (
        reports
        / "tuning_performance_control_tower"
        / f"tuning_performance_control_tower_{target}.json"
    )
    tower_path.parent.mkdir(parents=True)
    tower_path.write_text(
        json.dumps(
            {
                "date": target,
                "source_generation_contract": mod.source_receipt(
                    mod.source_paths(reports, target, "tower"), target
                ),
            }
        )
    )
    checklist = tmp_path / "2026-09-08-stage2-todo-checklist.md"
    checklist.write_text(
        mod.checklist_marker(
            mod.source_receipt(mod.source_paths(reports, target, "checklist"), target)
        )
    )
    return reports, tower_path, checklist


def test_exact_receipts_and_optional_absence_pass(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    result = mod.verify_summary_handoff(
        "2026-09-07", report_dir=reports, checklist_path=checklist
    )
    assert result["status"] == "pass"
    assert result["runtime_effect"] is False


def test_late_source_arrival_invalidates_both_consumers(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    source = mod.source_paths(reports, "2026-09-07", "tower")[
        "code_improvement_workorder"
    ]
    source.parent.mkdir(parents=True)
    source.write_text('{"date":"2026-09-07","orders":[]}')
    result = mod.verify_summary_handoff(
        "2026-09-07", report_dir=reports, checklist_path=checklist
    )
    assert len(result["issues"]) == 2


def test_route_session_venue_provenance_hashes_bind_both_consumers(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    for consumer in ("tower", "checklist"):
        labels = mod.source_paths(reports, "2026-09-07", consumer)
        assert {"key_lineage_ledger", "conversion_lane"} <= labels.keys()

    source = mod.source_paths(reports, "2026-09-07", "checklist")["conversion_lane"]
    source.parent.mkdir(parents=True)
    source.write_text(
        '{"route":"SOR","session_bucket":"KRX_NXT_AFTERMARKET",'
        '"effective_venue":"INTEGRATED"}',
        encoding="utf-8",
    )

    result = mod.verify_summary_handoff(
        "2026-09-07", report_dir=reports, checklist_path=checklist
    )
    assert result["status"] == "fail"
    assert len(result["issues"]) == 2


def test_verifier_refresh_does_not_create_cycle(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    path = reports / "threshold_cycle_postclose_verification"
    path.mkdir()
    (path / "threshold_cycle_postclose_verification_2026-09-07.json").write_text(
        '{"status":"warning"}'
    )
    assert (
        mod.verify_summary_handoff(
            "2026-09-07", report_dir=reports, checklist_path=checklist
        )["status"]
        == "pass"
    )


@pytest.mark.parametrize(
    "mutation", ["date", "authority", "hash", "duplicate_marker", "no_marker"]
)
def test_invalid_contracts_fail(tmp_path, mutation):
    reports, tower, checklist = _publish(tmp_path)
    payload = json.loads(tower.read_text())
    if mutation == "date":
        payload["date"] = "2026-09-04"
    elif mutation == "authority":
        payload["source_generation_contract"]["allowed_runtime_apply"] = True
    elif mutation == "hash":
        payload["source_generation_contract"]["sources"]["code_improvement_workorder"][
            "sha256"
        ] = ("0" * 64)
    elif mutation == "duplicate_marker":
        checklist.write_text(checklist.read_text() * 2)
    else:
        checklist.write_text("# No receipt")
    if mutation in {"date", "authority", "hash"}:
        tower.write_text(json.dumps(payload))
    assert (
        mod.verify_summary_handoff(
            "2026-09-07", report_dir=reports, checklist_path=checklist
        )["status"]
        == "fail"
    )


def test_explicitly_disabled_consumers_are_not_missing(tmp_path):
    result = mod.verify_summary_handoff(
        "2026-09-07",
        report_dir=tmp_path,
        checklist_path=tmp_path / "missing.md",
        require_tower=False,
        require_checklist=False,
    )
    assert result["status"] == "pass"
    assert result["checked_consumers"] == []


def test_initial_quantity_direct_source_respects_effective_lower_bound_and_invalid_current(
    tmp_path,
):
    reports = tmp_path / "data" / "report"
    current = tmp_path / "data" / "runtime" / "initial_quantity" / "current.json"
    assert "initial_quantity_refresh_stage" not in mod.source_paths(
        reports, "2026-09-28", "tower"
    )
    current.parent.mkdir(parents=True)
    current.write_text('{"effective_from":"2026-09-29"}')
    assert "initial_quantity_refresh_stage" not in mod.source_paths(
        reports, "2026-09-28", "tower"
    )
    current.write_text('{"effective_from":"invalid"}')
    with pytest.raises(RuntimeError, match="initial_quantity_current_invalid"):
        mod.source_paths(reports, "2026-09-28", "tower")


def test_concurrent_source_change_prevents_publish(tmp_path):
    path = tmp_path / "source.json"
    paths = {"source": path}
    receipt = mod.source_receipt(paths, "2026-09-07")
    path.write_text("{}")
    with pytest.raises(RuntimeError, match="changed_during_render"):
        mod.assert_sources_unchanged(receipt, paths)


def test_pipeline_diagnostic_arrival_invalidates_both_exact_consumers(tmp_path):
    reports = tmp_path / "report"
    day = "2026-09-17"
    before = {
        consumer: mod.source_receipt(mod.source_paths(reports, day, consumer), day)
        for consumer in ("tower", "checklist")
    }
    path = mod.source_paths(reports, day, "tower")["pipeline_event_verbosity"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"target_date":"2026-09-17","state":"resource_deferred"}')
    for consumer in ("tower", "checklist"):
        after = mod.source_receipt(mod.source_paths(reports, day, consumer), day)
        assert after != before[consumer]


def test_retired_common_layer_handoff_uses_direct_sources_without_cycle(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-19"
    paths = mod.source_paths(reports, day, "tower")

    assert set(paths) == {"runtime_approval_summary"}
    assert "postclose_verifier" not in paths
    assert "threshold_cycle_ev" not in paths
    assert "preopen_apply_plan" not in paths


def test_retired_handoff_records_future_bootstrap_without_hashing_it(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-19"
    summary = (
        reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    )
    summary.parent.mkdir(parents=True)
    payload = {
        "date": day,
        "preopen_consumption_state": "pending",
        "preopen_consumption_receipt": {
            "apply_date": "2026-09-21",
            "manifest_path": "/runtime/runtime_policy_bootstrap_2026-09-21.json",
            "verification_path": "/runtime/runtime_policy_bootstrap_verify_2026-09-21.json",
        },
        "sources": {},
    }
    summary.write_text(json.dumps(payload), encoding="utf-8")

    paths = mod.source_paths(reports, day, "tower")
    before = mod.source_receipt(paths, day)
    bootstrap = (
        reports.parent
        / "runtime"
        / "policy_bootstrap"
        / "runtime_policy_bootstrap_2026-09-21.json"
    )
    bootstrap.parent.mkdir(parents=True)
    bootstrap.write_text('{"status":"ready"}', encoding="utf-8")
    after = mod.source_receipt(paths, day)

    assert set(paths) == {"runtime_approval_summary"}
    assert before == after
    assert mod.direct_future_handoff(payload, day)["manifest_path"].endswith(
        "runtime_policy_bootstrap_2026-09-21.json"
    )


def test_future_handoff_requires_explicit_transition_after_rewrite(tmp_path):
    from src.engine.automation import runtime_policy_bootstrap as bootstrap

    data = tmp_path / "data"
    reports = data / "report"
    source, apply = "2026-09-23", "2026-09-28"
    root = data / "runtime" / "policy_bootstrap"
    manifest_path = root / f"runtime_policy_bootstrap_{apply}.json"
    verify_path = root / f"runtime_policy_bootstrap_verify_{apply}.json"
    env_path = root / f"runtime_policy_bootstrap_{apply}.env"
    selection_path = data / "runtime" / "runtime_release_selection.json"
    selected = "b" * 40
    selection_path.parent.mkdir(parents=True)
    selection_path.write_text(
        json.dumps(
            {
                "schema": "runtime_release_selection_v1",
                "git_commit": selected,
                "release_root": "/releases/selected",
            }
        )
    )
    summary_path = (
        reports / "runtime_approval_summary" / f"runtime_approval_summary_{source}.json"
    )
    summary_path.parent.mkdir(parents=True)
    summary = {
        "date": source,
        "preopen_consumption_state": "pending",
        "preopen_consumption_receipt": {
            "source_date": source,
            "apply_date": apply,
            "manifest_path": str(manifest_path),
            "manifest_sha256": None,
            "verification_path": str(verify_path),
            "verification_sha256": None,
            "release_selection_sha256": None,
            "selected_release_commit": None,
        },
    }
    summary_path.write_text(json.dumps(summary))
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "pending"
    )

    root.mkdir(parents=True)
    env_path.write_text("export TEST=true\n")
    manifest = {
        "target_date": apply,
        "source_incumbent_target_date": "2026-09-19",
        "selected_release_sha": selected,
        "env_file": str(env_path),
        "env_sha256": bootstrap._digest_bytes(env_path.read_bytes()),
        "selected_families": [],
    }
    manifest["manifest_sha256"] = bootstrap._digest_json(manifest)
    manifest_path.write_text(json.dumps(manifest))
    verify_path.write_text(
        json.dumps(
            {
                "target_date": apply,
                "status": "pass",
                "passed": True,
                "manifest_sha256": manifest["manifest_sha256"],
                "pid": None,
                "pid_passed": None,
                "pid_env_available": True,
            }
        )
    )
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "stale"
    )
    direct = mod.verify_summary_handoff(
        source,
        report_dir=reports,
        checklist_path=tmp_path / "unused.md",
        require_tower=False,
        require_checklist=False,
    )
    assert (
        "postclose_summary_handoff:future_preopen_generation_stale" in direct["issues"]
    )
    transition = bootstrap.publish_future_handoff_transition(apply, data_dir=data)
    assert transition["status"] == "linked"
    linked = mod.inspect_future_handoff(summary, source, report_dir=reports)
    assert linked["status"] == "transitioned_no_pid"
    assert linked["actual_pid_consumed"] is False
    assert linked["valid_empty"] is True
    direct = mod.verify_summary_handoff(
        source,
        report_dir=reports,
        checklist_path=tmp_path / "unused.md",
        require_tower=False,
        require_checklist=False,
    )
    assert (
        "postclose_summary_handoff:future_preopen_generation_stale"
        not in direct["issues"]
    )
    assert (
        mod.stage_overview(reports, source)["future_handoff"]["status"]
        == "transitioned_no_pid"
    )

    original_verify = verify_path.read_bytes()
    verify = json.loads(original_verify)
    verify["verified_at"] = "2026-09-28T08:00:00+09:00"
    verify_path.write_text(json.dumps(verify))
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "stale"
    )
    retry = bootstrap.publish_future_handoff_transition(apply, data_dir=data)
    assert retry["status"] == "linked" and retry["path"] != transition["path"]
    assert Path(transition["path"]).is_file() and Path(retry["path"]).is_file()
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "transitioned_no_pid"
    )
    later_source = "2026-09-24"
    later_summary = {
        **summary,
        "date": later_source,
        "preopen_consumption_receipt": {
            **summary["preopen_consumption_receipt"],
            "source_date": later_source,
        },
    }
    later_path = summary_path.with_name(f"runtime_approval_summary_{later_source}.json")
    later_path.write_text(json.dumps(later_summary))
    both = bootstrap.publish_future_handoff_transition(apply, data_dir=data)
    assert both["status"] == "linked" and len(both["transitions"]) == 2
    assert {row["source_date"] for row in both["transitions"]} == {source, later_source}
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "transitioned_no_pid"
    )
    verify_path.write_bytes(original_verify)
    failed_verify = json.loads(original_verify)
    failed_verify.update(status="fail", passed=False)
    verify_path.write_text(json.dumps(failed_verify))
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "rejected"
    )
    pid_verify = json.loads(original_verify)
    pid_verify.update(pid=4321, pid_passed=True)
    verify_path.write_text(json.dumps(pid_verify))
    pid_state = mod.inspect_future_handoff(summary, source, report_dir=reports)
    assert pid_state["status"] == "stale"
    assert pid_state["pid_receipt_present"] is True
    assert pid_state["actual_pid_consumed"] is False
    summary["preopen_consumption_state"] = "off"
    summary_path.write_text(json.dumps(summary))
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "off"
    )
    assert (
        bootstrap.publish_future_handoff_transition(
            apply, data_dir=data, source_date=source
        )["status"]
        == "off"
    )
    summary["preopen_consumption_state"] = "pending"
    summary_path.write_text(json.dumps(summary))
    verify_path.write_bytes(original_verify)
    original_manifest = manifest_path.read_bytes()
    wrong_date = json.loads(original_manifest)
    wrong_date["target_date"] = "2026-09-29"
    manifest_path.write_text(json.dumps(wrong_date))
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "stale"
    )
    manifest_path.write_bytes(original_manifest)
    selection_path.write_text(
        json.dumps(
            {
                "schema": "runtime_release_selection_v1",
                "git_commit": "c" * 40,
                "release_root": "/releases/new",
            }
        )
    )
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "stale"
    )
    selection_path.write_text(
        json.dumps(
            {
                "schema": "runtime_release_selection_v1",
                "git_commit": selected,
                "release_root": "/releases/selected",
            }
        )
    )

    summary["preopen_consumption_state"] = "verified"
    receipt = summary["preopen_consumption_receipt"]
    receipt["manifest_sha256"] = bootstrap._digest_bytes(manifest_path.read_bytes())
    receipt["verification_sha256"] = bootstrap._digest_bytes(verify_path.read_bytes())
    receipt["release_selection_sha256"] = bootstrap._digest_bytes(
        selection_path.read_bytes()
    )
    receipt["selected_release_commit"] = selected
    summary_path.write_text(json.dumps(summary))
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "same_generation_no_pid"
    )
    pid_verify = json.loads(original_verify)
    pid_verify.update(pid=4321, pid_passed=True)
    verify_path.write_text(json.dumps(pid_verify))
    receipt["verification_sha256"] = bootstrap._digest_bytes(verify_path.read_bytes())
    summary_path.write_text(json.dumps(summary))
    pid_state = mod.inspect_future_handoff(summary, source, report_dir=reports)
    assert pid_state["status"] == "same_generation_pid_receipt_unconfirmed"
    assert pid_state["pid_receipt_present"] is True
    assert pid_state["actual_pid_consumed"] is False
    selection_path.write_text(
        json.dumps(
            {
                "schema": "runtime_release_selection_v1",
                "git_commit": selected,
                "release_root": "/releases/moved",
            }
        )
    )
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "stale"
    )
    selection_path.write_text(
        json.dumps(
            {
                "schema": "runtime_release_selection_v1",
                "git_commit": "c" * 40,
                "release_root": "/releases/new",
            }
        )
    )
    assert (
        mod.inspect_future_handoff(summary, source, report_dir=reports)["status"]
        == "stale"
    )


def test_schema_v3_pre_retirement_source_uses_direct_handoff(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-17"
    summary = (
        reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    )
    summary.parent.mkdir(parents=True)
    summary.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "date": day,
                "preopen_consumption_receipt": {"apply_date": "2026-09-21"},
            }
        ),
        encoding="utf-8",
    )

    paths = mod.source_paths(reports, day, "checklist")

    assert set(paths) == {"runtime_approval_summary"}


def test_retired_common_layer_handoff_skips_legacy_intake(monkeypatch, tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-19"
    summary = {
        "date": day,
        "preopen_consumption_state": "not_due",
        "preopen_consumption_receipt": {},
        "sources": {},
    }
    summary_path = (
        reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    )
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    receipt = mod.source_receipt(mod.source_paths(reports, day, "tower"), day)
    tower = (
        reports
        / "tuning_performance_control_tower"
        / f"tuning_performance_control_tower_{day}.json"
    )
    tower.parent.mkdir(parents=True)
    tower.write_text(json.dumps({"date": day, "source_generation_contract": receipt}))
    checklist = tmp_path / "checklist.md"
    checklist.write_text(
        mod.checklist_marker(receipt)
        + "\n"
        + mod.direct_future_handoff_marker(mod.direct_future_handoff(summary, day))
    )
    monkeypatch.setattr(
        "src.engine.automation.postclose_recommendation_intake.build_intake",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("retired intake must not run")
        ),
    )

    result = mod.verify_summary_handoff(
        day, report_dir=reports, checklist_path=checklist
    )

    assert result["status"] == "pass"


@pytest.fixture
def stage_environment(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as h

    monkeypatch.setattr(h, "_stage_code", lambda *a: "code-v2")
    monkeypatch.setattr(
        h, "stage_commands", lambda stage, *a, **kw: [["fixture", stage]]
    )
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_EVALUATION_WAIT_FOR_EOD", "false")
    day = "2026-09-21"
    report = tmp_path / "data" / "report"
    raw = report.parent / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text('{"stage":"fixture"}\n')
    raw_stat = raw.stat()
    preflight = (
        report
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    preflight.parent.mkdir(parents=True, exist_ok=True)
    source = {
        "target_date": day,
        "audit_phase": "preflight",
        "status": "pass",
        "consumer_implementation_sha256": "audit-code",
        "summary": {"tuning_input_allowed": True},
        "source": {
            "generation_stable": True,
            "pipeline_events": str(raw),
            "generation": {
                "device": raw_stat.st_dev,
                "inode": raw_stat.st_ino,
                "size_bytes": raw_stat.st_size,
                "mtime_ns": raw_stat.st_mtime_ns,
                "ctime_ns": raw_stat.st_ctime_ns,
            },
        },
    }
    preflight.write_text(json.dumps(source))
    binding = {
        "schema": "observation_source_quality_final_binding_v1",
        "target_date": day,
        "audit_phase": "preflight",
        "implementation_sha256": "audit-code",
        "artifact_sha256": hashlib.sha256(preflight.read_bytes()).hexdigest(),
    }
    Path(str(preflight) + ".final-contract.json").write_text(json.dumps(binding))

    def produce(command, **kwargs):
        from src.engine.scalping.ai_action_outcome_calibration import (
            _with_artifact_content_sha256,
        )

        stage = command[1]
        for name, path in h.stage_artifacts(report, day, stage).items():
            value = dict(target_date=day, status="complete")
            if name.startswith("machine_policy"):
                value["status"] = (
                    "completed"
                    if name.endswith("terminal")
                    else "machine_policy_generated"
                )
                if name == "machine_policy_terminal":
                    parent = json.loads(
                        h.stage_artifacts(report, day, stage)[
                            "machine_policy"
                        ].read_text()
                    )
                    value["report_sha256"] = parent["artifact_content_sha256"]
                value = _with_artifact_content_sha256(value)
            if name == "ai_decision_outcome_labels":
                value.update(
                    schema="ai_decision_outcome_labels_v1",
                    generated_at=day + "T21:00:00+09:00",
                    status="mature_label_rows_available",
                    labels=[],
                )
            if name == "widget_collector_expansion_recommendation":
                from src.engine.monitoring.widget_collector_expansion_recommendation import (
                    history_input_manifest,
                )
                from datetime import date

                history = history_input_manifest(
                    report.parent / "ai_decision_payloads",
                    report / "widget_mechanical_entry_replay",
                    through_date=date.fromisoformat(day),
                    sentinel_dir=report.parent / "runtime" / "sentinel_event_cache",
                    watch_config_path=report.parent
                    / "config"
                    / "widget_research_watch_symbols.json",
                )
                value["source"] = {
                    "history_input_manifest": history,
                    "feature_paths": [
                        row["path"]
                        for row in history["entries"]
                        if row["kind"] == "payload"
                    ],
                    "replay_paths": [
                        row["path"]
                        for row in history["entries"]
                        if row["kind"] == "replay"
                    ],
                }
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        return 0

    def run(stage, **kwargs):
        return h.run_stage(
            stage,
            day,
            report_dir=report,
            project=tmp_path,
            runner=kwargs.pop("runner", produce),
            **kwargs,
        )

    return h, day, report, run, produce


def test_machine_stage_requires_exact_bound_preflight(stage_environment):
    h, day, report, run, _produce = stage_environment
    preflight = (
        report
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    binding = Path(str(preflight) + ".final-contract.json")
    assert h._machine_source_preflight_issue(report, day) is None
    source = json.loads(preflight.read_text())
    source["summary"]["tuning_input_allowed"] = False
    preflight.write_text(json.dumps(source))
    assert (
        h._machine_source_preflight_issue(report, day)
        == "source_quality_preflight_identity_or_hash_invalid"
    )
    binding_body = json.loads(binding.read_text())
    binding_body["artifact_sha256"] = hashlib.sha256(preflight.read_bytes()).hexdigest()
    binding.write_text(json.dumps(binding_body))
    blocked = run(
        "main_machine_policy", runner=lambda *a, **kw: pytest.fail("preflight blocked")
    )
    assert blocked["status"] == "deferred"
    assert blocked["policy_disposition"] == "source_quality_blocked"
    assert blocked["issues"] == ["source_quality_preflight_blocked"]


def test_machine_terminal_survives_later_final_audit_generation(stage_environment):
    h, day, report, run, _produce = stage_environment
    machine = run("main_machine_policy")
    assert machine["status"] == "succeeded"
    assert machine["source_quality_preflight_sha256"]
    preflight = (
        report
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    preflight.write_text(json.dumps({"target_date": day, "audit_phase": "final"}))
    assert h.stage_receipt_issues(report, day, "main_machine_policy") == []


@pytest.mark.parametrize(
    "staging_status", ["operator_designation_preserved", "designated_policy_staged"]
)
def test_machine_stage_distinguishes_designation_from_automatic_carry(
    stage_environment, monkeypatch, staging_status
):
    h, day, report, run, produce = stage_environment
    # Publisher/source validation is covered by designated-policy integration
    # tests. Exercise the stage receipt's downstream semantic projection here.
    monkeypatch.setattr(h, "_safe_stage_output_issues", lambda *args: [])

    def designated(command, **kwargs):
        produce(command, **kwargs)
        path = h.stage_artifacts(report, day, "main_machine_policy")[
            "machine_policy_terminal"
        ]
        terminal = json.loads(path.read_text())
        terminal.update(
            selection_basis="win_rate_only",
            disposition="incumbent_carried",
            staged=dict(status=staging_status, bundle_sha256="designated-bundle"),
        )
        path.write_text(json.dumps(terminal))
        return 0

    receipt = run("main_machine_policy", runner=designated)
    assert receipt["status"] == "succeeded"
    assert receipt["policy_disposition"] == "operator_designated"
    assert receipt["automatic_policy_disposition"] == "incumbent_carried"
    assert receipt["designated_bundle_sha256"] == "designated-bundle"


def test_machine_closed_date_recovery_accepts_exact_bound_final_audit(
    stage_environment, monkeypatch
):
    h, day, report, run, _produce = stage_environment
    from src.engine import observation_source_quality_audit as audit_owner

    first = run("main_machine_policy")
    assert first["status"] == "succeeded"
    audit = (
        report
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    binding = Path(str(audit) + ".final-contract.json")
    source = json.loads(audit.read_text())
    source["audit_phase"] = "final"
    audit.write_text(json.dumps(source))
    final_binding = json.loads(binding.read_text())
    final_binding["audit_phase"] = "final"
    final_binding["artifact_sha256"] = hashlib.sha256(audit.read_bytes()).hexdigest()
    binding.write_text(json.dumps(final_binding))
    assert (
        h._machine_source_preflight_issue(report, day)
        == "source_quality_preflight_identity_or_hash_invalid"
    )
    monkeypatch.setattr(
        audit_owner, "check_audit_reusable", lambda *args, **kwargs: {"reusable": False}
    )
    assert (
        h._machine_source_preflight_issue(report, day, recovery=True)
        == "source_quality_final_audit_not_reusable"
    )
    monkeypatch.setattr(
        audit_owner, "check_audit_reusable", lambda *args, **kwargs: {"reusable": True}
    )
    assert h._machine_source_preflight_issue(report, day, recovery=True) is None
    second = run("main_machine_policy", recovery=True)
    assert second["status"] == "succeeded"
    assert second["source_quality_audit_phase"] == "final"
    assert second["source_quality_preflight_sha256"] == final_binding["artifact_sha256"]


def test_machine_stage_rejects_raw_generation_changed_after_preflight(
    stage_environment,
):
    h, day, report, run, _produce = stage_environment
    raw = report.parent / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.write_text(raw.read_text() + '{"stage":"late_writer"}\n')
    assert h._machine_source_preflight_issue(report, day) == (
        "source_quality_preflight_raw_generation_changed"
    )
    blocked = run(
        "main_machine_policy", runner=lambda *a, **kw: pytest.fail("stale raw")
    )
    assert blocked["status"] == "deferred"
    assert blocked["issues"] == ["source_quality_preflight_raw_generation_changed"]


def test_machine_resource_timeout_writes_deferred_terminal(stage_environment):
    _h, _day, _report, run, _produce = stage_environment
    blocked = run(
        "main_machine_policy",
        resource_blocked={
            "ok": False,
            "mem_available_mb": 3020.0,
            "required_mem_mb": 4096.0,
            "issues": ["mem_available_mb=3020.0<4096.0"],
        },
        runner=lambda *a, **kw: pytest.fail("resource guard blocked"),
    )
    assert blocked["status"] == "deferred"
    assert blocked["issues"] == ["resource_guard_timeout"]
    assert blocked["resource_guard"]["mem_available_mb"] == 3020.0


def test_machine_stage_validates_bound_completed_price_generation(stage_environment):
    from src.engine.scalping.ai_action_outcome_calibration import (
        MACHINE_COMPLETED_PRICE_CACHE_SCHEMA,
        _with_artifact_content_sha256,
    )

    h, day, report_dir, run, _produce = stage_environment
    assert run("main_machine_policy")["status"] == "succeeded"
    cache_path = (
        report_dir
        / "machine_completed_price_source"
        / f"machine_completed_price_source_{day}.json"
    )
    cache_path.parent.mkdir(parents=True)
    cache = _with_artifact_content_sha256(
        {
            "schema": MACHINE_COMPLETED_PRICE_CACHE_SCHEMA,
            "source_date": day,
            "prices": [],
            "provenance": [],
        }
    )
    cache_path.write_text(json.dumps(cache))
    paths = h.stage_artifacts(report_dir, day, "main_machine_policy")
    machine = json.loads(paths["machine_policy"].read_text())
    machine["observation_source_counts"] = {
        "completed_price_cache_receipts": [
            {
                "source_date": day,
                "path": str(cache_path),
                "artifact_content_sha256": cache["artifact_content_sha256"],
            }
        ]
    }
    machine = _with_artifact_content_sha256(machine)
    paths["machine_policy"].write_text(json.dumps(machine))
    terminal = json.loads(paths["machine_policy_terminal"].read_text())
    terminal["report_sha256"] = machine["artifact_content_sha256"]
    paths["machine_policy_terminal"].write_text(
        json.dumps(_with_artifact_content_sha256(terminal))
    )
    assert h._stage_output_issues(report_dir, day, "main_machine_policy") == []
    cache["prices"].append({"stock_code": "005930"})
    cache_path.write_text(json.dumps(_with_artifact_content_sha256(cache)))
    assert (
        "main_machine_policy:completed_price_source_generation_changed"
        in h._stage_output_issues(report_dir, day, "main_machine_policy")
    )
    machine["observation_source_counts"]["completed_price_cache_receipts"] = [
        {
            "source_date": day,
            "path": str(cache_path),
            "status": "collected",
        }
    ]
    paths["machine_policy"].write_text(
        json.dumps(_with_artifact_content_sha256(machine))
    )
    assert (
        "main_machine_policy:completed_price_source_receipts_invalid"
        in h._stage_output_issues(report_dir, day, "main_machine_policy")
    )


def test_pre_submit_stage_rejects_unsealed_raw_generation(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as handoff

    day = "2026-09-23"
    reports = tmp_path / "data" / "report"
    monkeypatch.setattr(handoff, "_stage_code", lambda *args, **kwargs: "fixture-code")
    monkeypatch.setattr(
        handoff, "stage_commands", lambda *args, **kwargs: [["fixture"]]
    )
    called = []
    result = handoff.run_stage(
        "pre_submit_delay",
        day,
        report_dir=reports,
        project=tmp_path,
        runner=lambda *args, **kwargs: called.append(args) or 0,
    )
    assert result["status"] == "deferred"
    assert result["exit_code"] == 75
    assert "raw_source_missing" in " ".join(result["issues"])
    assert called == []
    off = handoff.run_stage(
        "pre_submit_delay",
        day,
        report_dir=reports,
        project=tmp_path,
        runner=lambda *args, **kwargs: called.append(args) or 0,
        off=True,
    )
    assert off["status"] == "off"
    assert handoff.stage_receipt_issues(reports, day, "pre_submit_delay") == []
    assert called == []


def test_pre_submit_receipt_binds_sealed_source_generation(tmp_path, monkeypatch):
    from src.engine.pipeline_event_summary import (
        ProducerSummaryCompactor,
        seal_producer_summary_source,
    )
    from src.engine.scalping.pre_submit_delay_tuning import seal_family_source_ledger

    day = "2026-09-23"
    data = tmp_path / "data"
    reports = data / "report"
    raw = data / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir(parents=True)
    event = {
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": "scalping_scanner_fast_precheck",
        "stock_code": "005930",
        "emitted_at": f"{day}T10:00:00",
        "emitted_date": day,
        "record_id": 1,
        "fields": {},
    }
    raw.write_text(json.dumps(event) + "\n")
    compactor = ProducerSummaryCompactor(
        summary_dir=data / "pipeline_event_summaries",
        mode="shadow",
    )
    compactor.submit(event)
    compactor.flush()
    seal_producer_summary_source(data, day)
    ledger = seal_family_source_ledger(data, day)
    monkeypatch.setattr(mod, "_safe_stage_output_issues", lambda *args: [])
    paths = mod.stage_artifacts(reports, day, "pre_submit_delay")
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"target_date": day}))
    receipt = {
        "schema": mod.STAGE_SCHEMA,
        "stage_id": "pre_submit_delay",
        "source_date": day,
        "status": "succeeded",
        "exit_code": 0,
        "run_id": "fixture-run",
        "stage_code_sha256": "fixture-code",
        "pipeline_source_generation_sha256": ledger["ledger_sha256"],
        "sources": mod._stage_sources(paths),
        "prerequisite_receipts": {},
        "input_sources": mod._stage_sources(
            mod.stage_input_paths(reports, day, "pre_submit_delay")
        ),
    }
    mod._stage_write(mod.stage_path(reports, day, "pre_submit_delay"), receipt)
    assert (
        mod.stage_receipt_issues(
            reports, day, "pre_submit_delay", code_hash="fixture-code"
        )
        == []
    )

    raw.write_text(raw.read_text() + json.dumps({**event, "record_id": 2}) + "\n")
    # The sealed ledger validates the raw generation before a stage-level
    # digest comparison, so drift invalidates that ledger at the first guard.
    assert (
        "pre_submit_delay:family_source_ledger_missing_or_invalid"
        in mod.stage_receipt_issues(
            reports,
            day,
            "pre_submit_delay",
            code_hash="fixture-code",
        )
    )

    raw.write_text(json.dumps(event) + "\n")
    monkeypatch.setattr(mod, "_stage_code", lambda *args, **kwargs: "fixture-code")
    monkeypatch.setattr(mod, "stage_commands", lambda *args, **kwargs: [["fixture"]])

    def drift_during_consumer(*args, **kwargs):
        raw.write_text(raw.read_text() + json.dumps({**event, "record_id": 3}) + "\n")
        return 0

    result = mod.run_stage(
        "pre_submit_delay",
        day,
        report_dir=reports,
        project=tmp_path,
        runner=drift_during_consumer,
    )
    assert result["status"] == "failed"
    assert (
        "pipeline_source_quality:family_source_ledger_missing_or_invalid"
        in result["issues"]
    )


def test_summary_handoff_tracks_later_active_stage_generation(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert run("summary_handoff")["status"] == "succeeded"
    assert h.stage_receipt_issues(report, day, "summary_handoff") == []
    assert run("legacy_machine_report")["status"] == "succeeded"
    assert h.stage_receipt_issues(report, day, "summary_handoff") == [
        "summary_handoff:input_generation_changed"
    ]


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "digest",
        "retired_input_changed",
        "retired_input_missing",
        "input_set",
        "output",
        "code",
        "failed",
        "new_publication",
        "invalid_publication",
    ],
)
def test_historical_summary_consumer_preserves_exact_generation_only(
    stage_environment, damage
):
    h, day, report, run, _produce = stage_environment
    assert run("summary_handoff")["status"] == "succeeded"
    path = h.stage_path(report, day, "summary_handoff")
    value = h._load_json(path)
    value["schema"] = "postclose_stage_terminal_v2"
    legacy_paths = {}
    for stage in ("widget_policy", "collector_recommendation"):
        terminal = report / "postclose_stage_terminal" / day / f"{stage}.json"
        terminal.write_text(json.dumps({"stage_id": stage, "historical_only": True}))
        legacy_paths[stage] = terminal
    value["input_sources"].update(h._stage_sources(legacy_paths))
    h._stage_write(path, value)
    assert h.stage_receipt_issues(report, day, "summary_handoff") == [
        "summary_handoff:terminal_missing_or_invalid"
    ]  # A producer cannot reuse a v2 PASS.
    if damage == "digest":
        value["run_id"] = "changed-without-rehash"
        path.write_text(json.dumps(value))
    elif damage == "retired_input_changed":
        legacy_paths["widget_policy"].write_text("{}")
    elif damage == "retired_input_missing":
        legacy_paths["collector_recommendation"].unlink()
    elif damage == "output":
        h.stage_artifacts(report, day, "summary_handoff")[
            "postclose_done_controller"
        ].write_text("{}")
    elif damage:
        if damage == "input_set":
            value["input_sources"].pop("widget_policy")
        elif damage == "code":
            value["stage_code_sha256"] = "unknown-code"
        elif damage == "failed":
            value.update(status="failed", exit_code=1)
        elif damage == "new_publication":
            value["publication_date"] = "2026-10-06"
        elif damage == "invalid_publication":
            value["publication_date"] = "2026-10-00"
        h._stage_write(path, value)
    before = path.read_bytes()
    issues = h.stage_receipt_issues(
        report,
        day,
        "summary_handoff",
        allow_historical_summary=True,
    )
    assert bool(issues) is (damage is not None), issues
    assert path.read_bytes() == before


def test_legacy_machine_code_hash_still_binds_original_dependencies(tmp_path):
    from src.engine.automation import postclose_summary_handoff as h

    dispatcher = tmp_path / "src/engine/automation/postclose_summary_handoff.py"
    fixed_watch = tmp_path / "src/engine/scalping/main_fixed_watch.py"
    original = tmp_path / "src/engine/scalping/ai_action_outcome_calibration.py"
    for path in (dispatcher, fixed_watch, original):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# first generation\n")
    commands = h.stage_commands("main_machine_policy", "2026-10-02", "2026-10-05")

    def digest(legacy):
        return h._stage_code(
            "main_machine_policy",
            commands,
            tmp_path,
            dispatcher_path=dispatcher,
            legacy_main_machine=legacy,
        )

    old, current = digest(True), digest(False)
    fixed_watch.write_text("# new fixed-watch generation\n")
    assert digest(True) == old
    assert digest(False) != current
    original.write_text("# changed original producer\n")
    assert digest(True) != old


def test_summary_handoff_reseals_verified_final_controller(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert run("summary_handoff")["status"] == "succeeded"
    controller = h.stage_artifacts(report, day, "summary_handoff")[
        "postclose_done_controller"
    ]
    controller.write_text(
        json.dumps(
            {
                "date": day,
                "status": "done",
                "whole_native_chain_done_claimed": True,
                "final_verifier_status": "pass",
            }
        )
    )
    assert h.stage_receipt_issues(report, day, "summary_handoff") == [
        "summary_handoff:output_generation_changed"
    ]
    assert (
        h.reseal_summary_handoff_for_final_controller(report, day, controller) is True
    )
    receipt = h._load_json(h.stage_path(report, day, "summary_handoff"))
    assert receipt["final_controller_reseal"]["status"] == "done"
    assert h.stage_receipt_issues(report, day, "summary_handoff") == []
    controller.write_text(json.dumps({"date": day, "status": "failed"}))
    with pytest.raises(ValueError, match="final_controller_not_verified"):
        h.reseal_summary_handoff_for_final_controller(report, day, controller)


def test_final_controller_reseal_preserves_receipt_when_summary_inputs_changed(
    stage_environment,
):
    h, day, report, run, _produce = stage_environment
    assert run("summary_handoff")["status"] == "succeeded"
    receipt_path = h.stage_path(report, day, "summary_handoff")
    original = receipt_path.read_bytes()
    assert run("legacy_machine_report")["status"] == "succeeded"
    controller = h.stage_artifacts(report, day, "summary_handoff")[
        "postclose_done_controller"
    ]
    controller.write_text(
        json.dumps(
            {
                "date": day,
                "status": "done",
                "whole_native_chain_done_claimed": True,
                "final_verifier_status": "pass",
            }
        )
    )
    assert h.stage_receipt_issues(report, day, "summary_handoff") == [
        "summary_handoff:output_generation_changed"
    ]
    with pytest.raises(ValueError, match="input_generation_changed"):
        h.reseal_summary_handoff_for_final_controller(report, day, controller)
    assert receipt_path.read_bytes() == original


def test_exact_ai_stage_keeps_off_and_failed_terminal_semantics(stage_environment):
    h, day, report, run, _produce = stage_environment
    payload = (
        report.parent / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl.gz"
    )
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"broken gzip")
    assert run("outcome_labels", off=True)["status"] == "off"
    assert h.stage_receipt_issues(report, day, "outcome_labels") == []
    assert run("outcome_labels", runner=lambda *args, **kwargs: 9)["status"] == "failed"
    assert h.stage_receipt_issues(report, day, "outcome_labels") == [
        "outcome_labels:failed"
    ]


def test_stage_lock_and_live_orphan_identity_prevent_duplicate(stage_environment):
    import fcntl, os

    h, day, report, run, produce = stage_environment
    path = h.stage_path(report, day, "legacy_machine_report")
    path.parent.mkdir(parents=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert run("legacy_machine_report")["reason"] == "existing_stage_writer"
    h._stage_write(
        path,
        dict(
            status="running",
            child_pid=os.getpid(),
            child_start_ticks=Path("/proc/self/stat").read_text().split()[21],
        ),
    )
    assert run("legacy_machine_report")["reason"] == "existing_child_running"


def test_stage_runner_exception_is_terminal_failure(stage_environment):
    h, day, report, run, produce = stage_environment

    def fail(*a, **kw):
        raise ValueError("bad_input")

    r = run("legacy_machine_report", runner=fail)
    assert r["status"] == "failed" and r["issues"] == ["bad_input"]
    assert run("legacy_machine_report")["status"] == "succeeded"


def test_stage_publication_date_is_pinned_and_invalid_future_rejected(
    stage_environment,
):
    h, day, report, run, produce = stage_environment
    r = run("pre_submit_delay", publication="2026-09-21")
    assert r["source_date"] == day and r["effective_date"] == "2026-09-22"
    with pytest.raises(ValueError, match="stage_date_contract_invalid"):
        run("pre_submit_delay", publication="2099-01-01")


def test_late_summary_recovery_uses_source_day_prepared_session(stage_environment):
    h, day, report, run, _produce = stage_environment
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day

    seen = []

    def capture(_command, *, env, cwd):
        seen.append(
            (
                env["POSTCLOSE_POLICY_PUBLICATION_DATE"],
                env["POSTCLOSE_PREPARED_EFFECTIVE_DATE"],
            )
        )
        return _produce(_command, env=env, cwd=cwd)

    result = run(
        "summary_handoff", publication="2026-09-23", recovery=True, runner=capture
    )
    assert result["status"] == "succeeded"
    assert result["publication_date"] == "2026-09-23"
    assert result["effective_date"] == _next_krx_trading_day("2026-09-23")
    assert result["prepared_effective_date"] == _next_krx_trading_day(day)
    assert seen == [("2026-09-23", _next_krx_trading_day(day))]
    assert h.stage_receipt_issues(report, day, "summary_handoff") == []
    h._stage_write(
        h.stage_path(report, day, "summary_handoff"),
        {
            **result,
            "prepared_effective_date": result["effective_date"],
        },
    )
    assert h.stage_receipt_issues(report, day, "summary_handoff") == [
        "summary_handoff:prepared_source_session_mismatch"
    ]
    with pytest.raises(ValueError, match="stage_date_contract_invalid"):
        run(
            "summary_handoff",
            publication="2026-09-23",
            effective=_next_krx_trading_day(day),
        )


def test_staged_winrate_descendant_requires_same_proof_and_machine(tmp_path):
    import json
    from types import SimpleNamespace
    from src.engine.automation import postclose_summary_handoff as h

    parent_hash = "a" * 64
    child_hash = "b" * 64
    proof = {"disposition": "incumbent_carried"}
    parent = {
        "bundle_sha256": parent_hash,
        "target_date": "2026-10-01",
        "winrate_selection": proof,
        "machine_policy": {"version": 1},
    }
    child = {
        "bundle_sha256": child_hash,
        "target_date": "2026-10-01",
        "previous_bundle_sha256": parent_hash,
        "winrate_selection": proof,
        "machine_policy": {"version": 1},
    }
    generations = tmp_path / "generations"
    generations.mkdir()
    (generations / f"{parent_hash}.json").write_text(json.dumps(parent))
    runtime = SimpleNamespace(
        root=lambda data_root: data_root,
        _read=lambda path: json.loads(path.read_text()),
        validate=lambda value, target_date: value["target_date"] == target_date
        or (_ for _ in ()).throw(ValueError("wrong date")),
        _validate_bundle_sources=lambda value, data_root: None,
        for_cohort=lambda value, cohort: value,
    )
    staged = {"bundle_sha256": parent_hash, "target_date": "2026-10-01"}
    assert h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path)
    child["winrate_selection"] = {"disposition": "successor_selected"}
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path)
    child["winrate_selection"] = proof
    parent["machine_policy"] = {"version": 2}
    (generations / f"{parent_hash}.json").write_text(json.dumps(parent))
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path)


def test_winrate_generation_only_retains_seal_source_and_same_policy_checks(tmp_path):
    import hashlib
    import json
    from types import SimpleNamespace
    from src.engine.automation import postclose_summary_handoff as h

    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    parent = {
        "target_date": "2026-10-02",
        "schema": "sealed-test",
        "machine_policy": {"version": 1},
        "winrate_selection": {"disposition": "incumbent_carried"},
    }
    parent["bundle_sha256"] = digest(parent)
    child = {
        **parent,
        "previous_bundle_sha256": parent["bundle_sha256"],
        "bundle_sha256": "b" * 64,
    }
    path = tmp_path / "generations" / (parent["bundle_sha256"] + ".json")
    path.parent.mkdir()
    path.write_text(json.dumps(parent))
    checked = []
    runtime = SimpleNamespace(
        root=lambda root: root,
        digest=digest,
        _read=lambda p: json.loads(p.read_text()),
        for_cohort=lambda value, cohort: value,
        validate=lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("current policy already validated")
        ),
        _validate_bundle_sources=lambda value, root: checked.append(
            value["bundle_sha256"]
        ),
    )
    staged = {"bundle_sha256": parent["bundle_sha256"], "target_date": "2026-10-02"}
    assert h._staged_winrate_generation_preserved(
        staged, child, runtime, tmp_path, generation_only=True
    )
    assert checked == [parent["bundle_sha256"]]
    child["machine_policy"] = {"version": 2}
    assert not h._staged_winrate_generation_preserved(
        staged, child, runtime, tmp_path, generation_only=True
    )
    child["machine_policy"] = parent["machine_policy"]
    runtime._validate_bundle_sources = lambda *a: (_ for _ in ()).throw(
        ValueError("source changed")
    )
    assert not h._staged_winrate_generation_preserved(
        staged, child, runtime, tmp_path, generation_only=True
    )
    parent["machine_policy"] = {"version": 3}
    path.write_text(json.dumps(parent))
    assert not h._staged_winrate_generation_preserved(
        staged, child, runtime, tmp_path, generation_only=True
    )


def test_stage_machine_rejects_sealed_but_unbound_terminal(stage_environment):
    h, day, report, run, produce = stage_environment
    from src.engine.scalping.ai_action_outcome_calibration import (
        _with_artifact_content_sha256,
    )

    assert run("main_machine_policy")["status"] == "succeeded"
    path = h.stage_artifacts(report, day, "main_machine_policy")[
        "machine_policy_terminal"
    ]
    value = json.loads(path.read_text())
    value["report_sha256"] = "wrong"
    path.write_text(json.dumps(_with_artifact_content_sha256(value)))
    assert (
        "main_machine_policy:report_terminal_binding_invalid"
        in h._stage_output_issues(report, day, "main_machine_policy")
    )


def test_existing_winrate_carry_binding_requires_same_parent_and_policy(tmp_path):
    from pathlib import Path

    from src.engine.automation.postclose_summary_handoff import (
        _existing_incumbent_winrate_binding_valid,
    )
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    machine = {"strategy": "mechanistic_entry", "thresholds": {"fixed": 1}}
    previous = {"bundle_sha256": "a" * 64, "machine_policy": machine}
    report = {
        "artifact_content_sha256": "b" * 64,
        "publication_date": "2026-09-24",
        "parent_bundle_sha256": previous["bundle_sha256"],
        "parent_machine_policy_sha256": policy.digest(machine),
        "policy_version": "winrate_initial_v1",
        "disposition": "incumbent_carried",
        "candidate_policy": None,
    }
    bundle = {
        "bundle_sha256": "c" * 64,
        "previous_bundle_sha256": "f" * 64,
        "machine_policy": machine,
        "winrate_selection": {
            "report_sha256": "d" * 64,
            "disposition": "incumbent_carried",
            "policy_version": "winrate_initial_v1",
            "parent_bundle_sha256": previous["bundle_sha256"],
            "machine_policy_sha256": policy.digest(machine),
        },
    }
    proof = bundle["winrate_selection"]
    staged = {
        "bundle_sha256": bundle["bundle_sha256"],
        "current_report_sha256": report["artifact_content_sha256"],
        "bundle_report_sha256": bundle["winrate_selection"]["report_sha256"],
        "previous_bundle_sha256": previous["bundle_sha256"],
        "machine_policy_sha256": policy.digest(machine),
    }

    assert _existing_incumbent_winrate_binding_valid(
        report, staged, bundle, previous, policy
    )
    preserving_child = {
        **bundle,
        "bundle_sha256": "e" * 64,
        "previous_bundle_sha256": bundle["bundle_sha256"],
    }
    assert _existing_incumbent_winrate_binding_valid(
        report,
        {**staged, "target_date": "2026-09-25"},
        preserving_child,
        previous,
        policy,
        staged_bundle={
            **bundle,
            "target_date": "2026-09-25",
        },
    )
    changed_child = dict(
        preserving_child,
        winrate_selection={
            **bundle["winrate_selection"],
            "report_sha256": "f" * 64,
        },
    )
    assert not _existing_incumbent_winrate_binding_valid(
        report,
        {**staged, "target_date": "2026-09-25"},
        changed_child,
        previous,
        policy,
        staged_bundle={
            **bundle,
            "target_date": "2026-09-25",
        },
    )

    staged_generation = {
        **bundle,
        "target_date": "2026-09-25",
        "bundle_sha256": "c" * 64,
    }
    middle_generation = {
        **staged_generation,
        "bundle_sha256": "e" * 64,
        "previous_bundle_sha256": staged_generation["bundle_sha256"],
    }
    current_generation = {
        **middle_generation,
        "bundle_sha256": "f" * 64,
        "previous_bundle_sha256": middle_generation["bundle_sha256"],
    }
    policy_root = tmp_path / "mechanistic_entry_policy"
    generations = policy_root / "generations"
    generations.mkdir(parents=True)
    for generation in (staged_generation, middle_generation):
        (generations / f"{generation['bundle_sha256']}.json").write_text(
            json.dumps(generation)
        )
    fake_policy = type("Policy", (), {})()
    fake_policy.root = lambda _root: policy_root
    fake_policy._read = lambda path: json.loads(Path(path).read_text())

    def validate_generation(value, target_date):
        if value.get("target_date") != target_date:
            raise ValueError("target_date_mismatch")

    fake_policy.validate = validate_generation
    fake_policy._validate_bundle_sources = lambda *_args: None
    fake_policy.for_cohort = lambda value, _scope: {
        "machine_policy": value["machine_policy"]
    }
    fake_policy.digest = policy.digest
    assert _existing_incumbent_winrate_binding_valid(
        report,
        {
            **staged,
            "bundle_sha256": staged_generation["bundle_sha256"],
            "target_date": "2026-09-25",
        },
        current_generation,
        previous,
        fake_policy,
        data_root=tmp_path,
    )
    changed_middle = dict(
        middle_generation,
        winrate_selection={
            **proof,
            "report_sha256": "f" * 64,
        },
    )
    (generations / f"{middle_generation['bundle_sha256']}.json").write_text(
        json.dumps(changed_middle)
    )
    assert not _existing_incumbent_winrate_binding_valid(
        report,
        {
            **staged,
            "bundle_sha256": staged_generation["bundle_sha256"],
            "target_date": "2026-09-25",
        },
        current_generation,
        previous,
        fake_policy,
        data_root=tmp_path,
    )
    changed = dict(report, candidate_policy={"threshold": "different"})
    assert not _existing_incumbent_winrate_binding_valid(
        changed, staged, bundle, previous, policy
    )
    changed_previous = dict(previous, bundle_sha256="e" * 64)
    assert not _existing_incumbent_winrate_binding_valid(
        report, staged, bundle, changed_previous, policy
    )
    changed_machine = dict(bundle, machine_policy={"strategy": "other"})
    assert not _existing_incumbent_winrate_binding_valid(
        report, staged, changed_machine, previous, policy
    )


def test_label_ready_time_uses_kst_instant(stage_environment):
    h, day, report, run, produce = stage_environment
    produce(["fixture", "outcome_labels"])
    path = h.stage_artifacts(report, day, "outcome_labels")[
        "ai_decision_outcome_labels"
    ]
    value = json.loads(path.read_text())
    value["generated_at"] = day + "T12:00:00+00:00"
    path.write_text(json.dumps(value))
    assert run("outcome_labels", execute=False)["status"] == "succeeded"
    value["generated_at"] = day + "T10:00:00+00:00"
    path.write_text(json.dumps(value))
    assert run("outcome_labels", execute=False)["status"] == "failed"


def test_launch_rejects_invalid_date_before_fork(monkeypatch):
    from src.engine.automation import postclose_summary_handoff as h

    monkeypatch.setattr(
        h.subprocess, "Popen", lambda *a, **kw: pytest.fail("must not launch")
    )
    with pytest.raises(SystemExit):
        h._stage_main(
            ["--stage", "main_machine_policy", "--date", "2099-01-01", "--launch"]
        )


def test_pre_submit_delay_stage_command_resolves_next_session_effective_date():
    from src.engine.automation import postclose_summary_handoff as h

    command = h.stage_commands("pre_submit_delay", "2026-09-23", "2026-09-23")[0]

    assert command[-5:] == [
        "--date",
        "2026-09-23",
        "--effective-date",
        "2026-09-28",
        "--require-family-ledger",
    ]


def test_machine_strategy_refresh_runs_before_auxiliary_ai():
    from src.engine.automation import postclose_summary_handoff as h

    command = h.stage_commands("legacy_machine_report", "2026-09-30", "2026-09-30")[0]
    assert "--machine-only" in command and "--activate-now" in command
    assert "legacy_machine_report" in h.STAGE_REGISTRY["main_auxiliary_policy"][0]


@pytest.mark.parametrize("unrelated", [0, 257])
@pytest.mark.parametrize(
    "origin", ["legacy", "pinned", "changed", "outside", "missing", "null", "symlink"]
)
def test_unchanged_stage_accepts_exact_selected_release_code_hash(
    stage_environment, monkeypatch, tmp_path, unrelated, origin
):
    h, day, report, run, _ = stage_environment
    run("legacy_machine_report")
    assert h._load_json(h.stage_path(report, day, "legacy_machine_report"))[
        "stage_code_root"
    ] == str(tmp_path)

    managed = tmp_path / "KORStockScan-runtime-releases"
    release = managed / "immutable-release"
    previous = managed / (
        "zz-previous-release" if origin == "pinned" else "previous-release"
    )
    for root in (release, previous):
        (root / ".git").mkdir(parents=True)
        dispatcher = root / "src/engine/automation/postclose_summary_handoff.py"
        dispatcher.parent.mkdir(parents=True)
        dispatcher.write_text("# pinned release dispatcher\n")
    for index in range(unrelated):
        (managed / f"z-unrelated-{index:03}" / ".git").mkdir(parents=True)
    selection = report.parent / "runtime" / "runtime_release_selection.json"
    selection.parent.mkdir(parents=True, exist_ok=True)
    selection.write_text(
        json.dumps(
            {
                "schema": "runtime_release_selection_v1",
                "release_root": str(release),
                "git_commit": "a" * 40,
            }
        )
    )

    def code_hash(stage, commands, project, *, dispatcher_path=None):
        if dispatcher_path is None:
            return "repaired-code"
        return (
            "previous-release-code" if project == previous else "selected-release-code"
        )

    monkeypatch.setattr(h, "_stage_code", code_hash)
    path = h.stage_path(report, day, "legacy_machine_report")
    terminal = h._load_json(path)
    terminal.pop(
        "stage_code_root", None
    )  # Original v3 receipts did not record this field.
    terminal["stage_code_sha256"] = "previous-release-code"
    if origin != "legacy":
        terminal["stage_code_root"] = str(previous)
    if origin == "changed":
        terminal["stage_code_root"] = str(release)
    if origin == "outside":
        terminal["stage_code_root"] = str(tmp_path)
    if origin == "missing":
        (previous / "src/engine/automation/postclose_summary_handoff.py").unlink()
    if origin == "null":
        terminal["stage_code_root"] = None
    if origin == "symlink":
        link = managed / "linked-producer"
        link.symlink_to(previous, target_is_directory=True)
        terminal["stage_code_root"] = str(link)
    h._stage_write(path, terminal)

    expected = (
        [] if origin in {"legacy", "pinned"} else ["legacy_machine_report:code_changed"]
    )
    assert (
        h.stage_receipt_issues(
            report, day, "legacy_machine_report", code_hash="repaired-code"
        )
        == expected
    )


def test_auxiliary_stage_hash_binds_tuner_implementation(tmp_path):
    from src.engine.automation import postclose_summary_handoff as h

    commands = h.stage_commands("main_auxiliary_policy", "2026-10-08", "2026-10-08")
    source = tmp_path / "src/engine/scalping/reversal_auxiliary_tuning.py"
    source.parent.mkdir(parents=True)
    source.write_text("# prior tuner\n")
    previous = h._stage_code("main_auxiliary_policy", commands, tmp_path)
    source.write_text("# repaired tuner\n")
    assert h._stage_code("main_auxiliary_policy", commands, tmp_path) != previous


def test_stage_stop_cleans_child_and_preserves_checkpoint(
    stage_environment, monkeypatch, tmp_path
):
    import sys, threading

    h, day, report, run, produce = stage_environment
    checkpoint = tmp_path / "saved-checkpoint"
    command = [
        sys.executable,
        "-c",
        "import pathlib,time; pathlib.Path("
        + repr(str(checkpoint))
        + ').write_text("saved"); time.sleep(30)',
    ]
    monkeypatch.setattr(h, "stage_commands", lambda *a, **kw: [command])
    stop = threading.Event()
    timer = threading.Timer(1, stop.set)
    timer.start()
    try:
        result = h.run_stage(
            "legacy_machine_report",
            day,
            report_dir=report,
            project=tmp_path,
            stop_event=stop,
            timeout=10,
        )
    finally:
        timer.cancel()
    assert result["status"] == "failed" and checkpoint.read_text() == "saved"
    assert not Path("/proc/" + str(result["child_pid"])).exists()


def test_summary_receipt_does_not_hash_itself(stage_environment):
    h, day, report, run, produce = stage_environment
    run("legacy_machine_report")
    paths = h.source_paths(report, day, "checklist")
    assert h.stage_path(report, day, "legacy_machine_report") in paths.values()
    assert h.stage_path(report, day, "summary_handoff") not in paths.values()
    assert (
        h.stage_artifacts(report, day, "summary_handoff")["postclose_done_controller"]
        not in paths.values()
    )
    assert "stage_legacy_machine_report" in paths
    assert "legacy_machine_report" in h.stage_overview(report, day)["stages"]


@pytest.mark.parametrize("status", ["pending", "running", "deferred"])
def test_scheduled_stage_check_reports_pending_as_deferred(
    stage_environment, monkeypatch, status
):
    h, day, report, run, produce = stage_environment
    from src.utils import constants

    monkeypatch.setattr(constants, "DATA_DIR", report.parent)
    h._stage_write(
        h.stage_path(report, day, "main_auxiliary_policy"), {"status": status}
    )
    assert (
        h._stage_main(["--stage", "main_auxiliary_policy", "--date", day, "--check"])
        == 75
    )


@pytest.mark.parametrize(
    "stage,recovery,expected",
    [
        ("main_auxiliary_policy", True, 123),
        ("main_auxiliary_policy", False, 123),
    ],
)
def test_compact_recovery_keeps_bounded_prerequisite_wait(
    monkeypatch, stage, recovery, expected
):
    import signal
    from src.engine.automation import postclose_summary_handoff as h

    seen = []
    monkeypatch.setattr(signal, "signal", lambda *a: None)

    def run(s, *a, **kw):
        seen.append(kw)
        return dict(stage_id=s, status="succeeded", exit_code=0)

    monkeypatch.setattr(h, "run_stage", run)
    args = ["--stage", stage, "--date", "2026-09-28", "--timeout-sec", "123"]
    if recovery:
        args.append("--recover-closed-target")
    assert h._stage_main(args) == 0
    assert seen[0]["prerequisite_wait"] == expected
    assert seen[0]["recovery"] is recovery


def test_compact_wait_does_not_hide_terminal_failed_peer(
    stage_environment, monkeypatch
):
    import time

    h, day, report, run, _produce = stage_environment
    h._stage_write(h.stage_path(report, day, "outcome_labels"), {"status": "failed"})
    h._stage_write(
        h.stage_path(report, day, "legacy_machine_report"), {"status": "running"}
    )
    monkeypatch.setattr(
        h, "stage_receipt_issues", lambda _report, _day, s, **kw: [s + ":blocked"]
    )
    monkeypatch.setattr(
        time, "sleep", lambda _: pytest.fail("terminal failure must not wait")
    )
    result = run("main_auxiliary_policy", prerequisite_wait=123)
    assert result["status"] == "deferred" and result["exit_code"] == 75
    assert "outcome_labels:blocked" in result["issues"]


def test_one_stage_barrier_waits_without_waiting_for_later_consumers(
    monkeypatch, tmp_path
):
    import signal, time
    from src.utils import constants
    from src.engine.automation import postclose_summary_handoff as h

    monkeypatch.setattr(signal, "signal", lambda *a: None)
    monkeypatch.setattr(constants, "DATA_DIR", tmp_path)
    day = "2026-10-07"
    path = h.stage_path(tmp_path / "report", day, "main_machine_policy")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"status": "running"}))
    waited = []

    def advance(seconds):
        waited.append(seconds)
        path.write_text(json.dumps({"status": "succeeded"}))

    monkeypatch.setattr(time, "sleep", advance)
    assert (
        h._stage_main(
            ["--stage", "wait", "--wait-stage", "main_machine_policy", "--date", day]
        )
        == 0
    )
    assert waited == [1]
    # A terminal failure ends waiting but cannot pass the publication check.
    path.write_text(json.dumps({"status": "failed"}))
    assert (
        h._stage_main(
            ["--stage", "wait", "--wait-stage", "main_machine_policy", "--date", day]
        )
        == 0
    )
    assert (
        h._stage_main(["--stage", "main_machine_policy", "--check", "--date", day]) == 1
    )


def test_synchronous_native_completion_after_original_deadline_is_deferred(
    stage_environment, monkeypatch
):
    import time

    h, day, report, run, produce = stage_environment
    clock = [0.0]
    monkeypatch.setattr(time, "monotonic", lambda: clock[0])

    def late(command, **kwargs):
        produce(command, **kwargs)
        clock[0] = 11.0
        return 0

    terminal = h.run_stage(
        "main_machine_policy",
        day,
        report_dir=report,
        project=report.parents[1],
        runner=late,
        timeout=10,
    )
    assert terminal["status"] == "deferred" and terminal["exit_code"] == 75
    assert terminal["synchronous_deadline_expired"] is True


def _joint_stage_fixture(tmp_path, monkeypatch, day="2026-10-13"):
    from src.engine.scalping import continuous_reversal_postclose as p
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import reversal_joint_registration as joint
    from src.engine.scalping.reversal_registered_catalog import cells, ROUTES

    h = mod
    report = tmp_path / "report"
    source = tmp_path / "frozen-source.json"
    source.write_text('{"original":true}')
    request = {
        "schema": joint.SCHEMA,
        "publication_date": day,
        "target_date": native.next_target(day),
    }
    pending = joint.pending_path(tmp_path)
    pending.parent.mkdir(parents=True)
    pending.write_text(json.dumps(request))

    def checked(value):
        if value != request:
            raise ValueError("changed authority fixture")
        return value

    monkeypatch.setattr(joint, "validate_request", checked)
    machine = p.seal(
        dict(
            schema="continuous_reversal_operating_comparison_v1",
            source_date=day,
            target_date=day,
            publication_date=day,
            status="completed",
            adoption_basis="operator_designated",
            registration_state="registered",
            comparison_complete=False,
            registration_change=request,
            source_receipts=[{"path": str(source), "sha256": p.file_hash(source)}],
            cells=[
                {"key": key, "routes": {r: {} for r in ROUTES[key.split("|")[1]]}}
                for key in cells()
            ],
            **p.AUTH,
        )
    )
    owned = report / "continuous_reversal" / day
    owned.mkdir(parents=True)
    (owned / "machine.json").write_text(json.dumps(machine))
    paths = h.stage_artifacts(report, day, "main_machine_policy")
    paths["machine_policy"].parent.mkdir(parents=True)
    paths["machine_policy"].write_text(json.dumps(machine))
    terminal = p.seal(
        dict(
            schema=machine["schema"],
            source_date=day,
            target_date=day,
            status="completed",
            report_sha256=machine["artifact_content_sha256"],
            **p.AUTH,
        )
    )
    paths["machine_policy_terminal"].write_text(json.dumps(terminal))
    return h, day, report, machine, source


def test_joint_initial_stage_succeeds_without_legacy_reports_and_pins_sources(
    tmp_path, monkeypatch
):
    h, day, report, machine, source = _joint_stage_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(h, "_stage_code", lambda *a: "fixture-code")
    monkeypatch.setattr(h, "_machine_source_preflight_issue", lambda *a, **k: None)
    audit = (
        report
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    audit.parent.mkdir()
    audit.write_text('{"audit_phase":"preflight"}')
    Path(str(audit) + ".final-contract.json").write_text(
        json.dumps({"artifact_sha256": hashlib.sha256(audit.read_bytes()).hexdigest()})
    )
    monkeypatch.setattr(h, "stage_commands", lambda *a, **k: [["fixture"]])
    terminal = h.run_stage(
        "main_machine_policy",
        day,
        report_dir=report,
        project=tmp_path,
        runner=lambda *a, **k: 0,
    )
    assert (
        terminal["status"] == "succeeded" and terminal["computation_executed"] is True
    )
    assert "reversal_source_manifest" not in terminal["sources"]
    assert (
        terminal["sources"]["joint_source_0"]["sha256"]
        == hashlib.sha256(source.read_bytes()).hexdigest()
    )
    assert (
        h.stage_receipt_issues(
            report, day, "main_machine_policy", code_hash="fixture-code"
        )
        == []
    )
    source.write_text('{"original":false}')
    assert h.stage_receipt_issues(
        report, day, "main_machine_policy", code_hash="fixture-code"
    )


def _operating_machine_stage_fixture(tmp_path, monkeypatch, day="2026-10-13"):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, machine, source = _joint_stage_fixture(tmp_path, monkeypatch, day=day)
    machine = p.seal(
        dict(
            machine,
            registration_change=None,
            adoption_basis="carried",
            comparison_complete=True,
        )
    )
    owned = report / "continuous_reversal" / day
    (owned / "machine.json").write_text(json.dumps(machine))
    (owned / "machine-comparison.json").write_text(json.dumps(machine))
    (owned / "source.json").write_text(
        json.dumps(p.seal(dict(schema=p.SCHEMA, source_date=day, **p.AUTH)))
    )
    paths = h.stage_artifacts(report, day, "main_machine_policy")
    paths["machine_policy"].write_text(json.dumps(machine))
    terminal = p.seal(
        dict(
            schema="continuous_reversal_operating_comparison_v1",
            source_date=day,
            target_date=day,
            status="completed",
            report_sha256=machine["artifact_content_sha256"],
            selection_basis="cumulative_raw_win_fraction",
            disposition="continuous_reversal_selected",
            staged=dict(status="machine_component_prepared"),
            **p.AUTH,
        )
    )
    paths["machine_policy_terminal"].write_text(json.dumps(terminal))
    monkeypatch.setattr(h, "_stage_code", lambda *a: "fixture-code")
    monkeypatch.setattr(h, "stage_commands", lambda *a, **k: [["fixture"]])
    monkeypatch.setattr(h, "_machine_source_preflight_issue", lambda *a, **k: None)
    audit = (
        report
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    audit.parent.mkdir()
    audit.write_text('{"audit_phase":"preflight"}')
    Path(str(audit) + ".final-contract.json").write_text(
        json.dumps({"artifact_sha256": hashlib.sha256(audit.read_bytes()).hexdigest()})
    )
    return h, day, report, terminal


def test_operating_machine_native_terminal_disposition_is_selected_and_old_receipt_is_preserved_with_projection(
    tmp_path, monkeypatch
):
    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    stage = h.run_stage(
        "main_machine_policy",
        day,
        report_dir=report,
        project=tmp_path,
        runner=lambda *a, **k: 0,
    )
    assert stage["status"] == "succeeded"
    assert stage["policy_disposition"] == "continuous_reversal_selected"
    assert stage["selection_metric"] == "cumulative_raw_win_fraction"
    assert stage["machine_report_sha256"] == native["report_sha256"]
    assert (
        h.stage_receipt_issues(
            report, day, "main_machine_policy", code_hash="fixture-code"
        )
        == []
    )

    old = dict(stage, policy_disposition="no_valid_candidate")
    old.pop("selection_metric")
    old.pop("machine_report_sha256")
    h._stage_write(h.stage_path(report, day, "main_machine_policy"), old)
    original = h.stage_path(report, day, "main_machine_policy").read_bytes()
    assert (
        h.stage_receipt_issues(
            report, day, "main_machine_policy", code_hash="fixture-code"
        )
        == []
    )
    old = json.loads(original)
    view = h._stage_disposition_view(report, day, "main_machine_policy", old, [])
    assert view["recorded_policy_disposition"] == "no_valid_candidate"
    assert view["policy_disposition"] == "continuous_reversal_selected"
    proof = view["native_disposition_projection"]
    assert proof["correction_applied"] is True
    assert proof["original_stage_receipt_sha256"] == old["receipt_sha256"]
    assert proof["original_stage_file_sha256"] == hashlib.sha256(original).hexdigest()
    assert proof["machine_report_content_sha256"] == native["report_sha256"]
    assert (
        proof["current_consumer_sha256"]
        == hashlib.sha256(Path(h.__file__).read_bytes()).hexdigest()
    )
    assert proof["actual_pid_consumed"] is False
    assert h.stage_path(report, day, "main_machine_policy").read_bytes() == original


def test_scoped_stage_binds_real_selector_metadata_and_live_input_generation(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_cumulative_registration as R
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.tests.test_reversal_cumulative_policy import scoring_contract, manifest

    h, day, report, old = _operating_machine_stage_fixture(tmp_path, monkeypatch, day="2026-10-27")
    contract = scoring_contract()
    m = manifest()
    current = {sid:g['baseline'] for sid,g in m['cumulative_variant_groups'].items()}
    m['scopes'] = current
    m['cumulative_scoring_contract'] = contract
    metrics = {}
    for sid,cfg in contract['scopes'].items():
        for name in ['CURRENT_NATIVE',*cfg['alternatives']]:
            metrics[sid+'::'+name]=dict(
                source_universe_sha256=P.digest(['b'*64,sid,R.C.LABEL]),
                source_complete=True,comparison_complete=True,statistic_source_complete=True,
                scoring_contract_sha256=contract['artifact_content_sha256'],
                statistic_contract_sha256=P.digest(R.scoring_spec()),chronological=dict(counts={}),
            )
    original=h._load_json(h.stage_artifacts(report,day,'main_machine_policy')['machine_policy'])
    machine=R.apply_selection(P.seal(dict(
        original, schema=old['schema'],source_date=day,target_date=day,publication_date=day,status='completed',
        parent_bundle_sha256='e'*64,source_manifest_sha256='b'*64,
        source_manifest_receipt=dict(path='private-fixture'),operating_manifest=m,
        scoring_contract=contract,statistic_contract=R.scoring_spec(),label_contract=R.C.LABEL,
        scope_decision_metrics={s:R.SCORE_VERSION for s in contract['scopes']},
        primary_decision_metric=R.SCOPED_METRIC,proposal_metrics=metrics,**P.AUTH,
    )),dict(bundle_sha256='e'*64,continuous_reversal=dict(operating_manifest=dict(scopes=current))))
    terminal=P.seal(dict(old,report_sha256=machine['artifact_content_sha256'],**R.selection_metadata(machine)))
    paths=h.stage_artifacts(report,day,'main_machine_policy')
    P.write(paths['machine_policy'],machine)
    # The stage consumes both the native report and its compatibility projection.
    P.write(report/'continuous_reversal'/day/'machine.json',machine)
    P.write(report/'continuous_reversal'/day/'machine-comparison.json',machine)
    P.write(paths['machine_policy_terminal'],terminal)
    P.write(R.scoring_path(tmp_path),contract)
    stage=h.run_stage('main_machine_policy',day,report_dir=report,project=tmp_path,runner=lambda *a,**k:0)
    assert stage['status']=='succeeded',stage
    assert stage['selection_metric']==R.SCOPED_METRIC
    assert stage['scoring_contract_sha256']==contract['artifact_content_sha256']
    assert stage['statistic_contract_sha256']==P.digest(R.scoring_spec())
    assert h.stage_receipt_issues(report,day,'main_machine_policy',code_hash='fixture-code')==[]
    # The actual enabled tuner issues a different publication hash and sources.
    # The machine stage must retain its original comparison/terminal binding.
    P.write(report/'continuous_reversal'/day/'machine.json',P.seal(dict(machine,source_receipts=[dict(path='auxiliary-evaluation')],adoption_basis='carried')))
    assert h.stage_receipt_issues(report,day,'main_machine_policy',code_hash='fixture-code')==[]
    comparison=report/'continuous_reversal'/day/'machine-comparison.json'
    P.write(comparison,P.seal(dict(machine,source_manifest_sha256='f'*64)))
    assert h.stage_receipt_issues(report,day,'main_machine_policy',code_hash='fixture-code')==['main_machine_policy:operating_comparison_projection_changed']
    P.write(comparison,machine)
    for field,bad in [('selection_basis','cumulative_raw_win_fraction'),('scoring_contract_sha256','f'*64),('statistic_contract_sha256','f'*64)]:
        assert not h._operating_machine_terminal_selected(P.seal(dict(terminal,**{field:bad})),day,machine)
    for field in ('selection_metric','scoring_contract_sha256','statistic_contract_sha256'):
        h._stage_write(h.stage_path(report,day,'main_machine_policy'),dict(stage,**{field:'unbound'}))
        assert h.stage_receipt_issues(report,day,'main_machine_policy',code_hash='fixture-code')==['main_machine_policy:recorded_native_disposition_unproven']
    h._stage_write(h.stage_path(report,day,'main_machine_policy'),stage)
    P.write(R.scoring_path(tmp_path),P.seal(dict(contract,source_manifest_sha256='f'*64)))
    assert h.stage_receipt_issues(report,day,'main_machine_policy',code_hash='fixture-code')==['main_machine_policy:input_generation_changed']


def test_machine_disposition_projection_fails_closed_on_late_native_source_change(
    tmp_path, monkeypatch
):
    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    stage = h.run_stage(
        "main_machine_policy",
        day,
        report_dir=report,
        project=tmp_path,
        runner=lambda *a, **k: 0,
    )
    path = h.stage_artifacts(report, day, "main_machine_policy")[
        "machine_policy_terminal"
    ]
    original = h._stage_sources

    def changed(paths):
        result = original(paths)
        if "consumer" in paths:
            path.write_text(path.read_text() + "\n")
        return result

    monkeypatch.setattr(h, "_stage_sources", changed)
    view = h._stage_disposition_view(report, day, "main_machine_policy", stage, [])
    assert not view.get("native_disposition_projection")
    assert "main_machine_policy:disposition_source_changed" in view["issues"]


def test_machine_disposition_view_cannot_accept_native_source_changed_to_nonselected_before_view(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    stage = h.run_stage(
        "main_machine_policy",
        day,
        report_dir=report,
        project=tmp_path,
        runner=lambda *a, **k: 0,
    )
    path = h.stage_artifacts(report, day, "main_machine_policy")[
        "machine_policy_terminal"
    ]
    path.write_text(
        json.dumps(
            p.seal(
                dict(
                    native,
                    disposition="incumbent_carried",
                    selection_basis="operator_initial",
                    staged=None,
                )
            )
        )
    )
    view = h._stage_disposition_view(report, day, "main_machine_policy", stage, [])
    assert view["policy_disposition"] == "unverified_recorded_disposition"
    assert "main_machine_policy:disposition_source_changed" in view["issues"]
    assert not view.get("native_disposition_projection")


def test_overview_cannot_claim_all_stages_complete_when_current_disposition_view_observes_a_late_gap(
    tmp_path, monkeypatch
):
    day = "2026-09-21"
    report = tmp_path / "report"
    for stage in mod.active_stage_names(day):
        path = mod.stage_path(report, day, stage)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dict(status="succeeded", policy_disposition="incumbent_carry"))
        )
    monkeypatch.setattr(mod, "stage_receipt_issues", lambda *a, **k: [])

    def view(_report, _day, stage, value, issues):
        return dict(
            status="succeeded",
            policy_disposition=value["policy_disposition"],
            issues=(
                ["main_machine_policy:disposition_source_changed"]
                if stage == "main_machine_policy"
                else []
            ),
        )

    monkeypatch.setattr(mod, "_stage_disposition_view", view)
    result = mod.stage_overview(report, day)
    assert result["stages"]["main_machine_policy"]["issues"]
    assert result["postclose_all_active_stages_complete"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "unrelated_completed_report"),
        ("status", "source_gap"),
        ("source_date", "2026-10-12"),
        ("selection_basis", "gross_ev"),
        ("disposition", "incumbent_carried"),
        ("staged", {"status": "activated"}),
        ("runtime_effect", True),
        ("allowed_runtime_apply", True),
        ("actual_order_submitted", True),
        ("broker_order_forbidden", False),
    ],
)
def test_operating_machine_terminal_cannot_grant_selection_for_unknown_or_malformed_contract(
    tmp_path, monkeypatch, field, value
):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    changed = p.seal(dict(native, **{field: value}))
    assert (
        h._operating_machine_terminal_selected(
            changed,
            day,
            json.loads(
                h.stage_artifacts(report, day, "main_machine_policy")[
                    "machine_policy"
                ].read_text()
            ),
        )
        is False
    )
    paths = h.stage_artifacts(report, day, "main_machine_policy")
    paths["machine_policy_terminal"].write_text(json.dumps(changed))
    if field != "status":
        assert h._stage_output_issues(report, day, "main_machine_policy")


def test_operating_machine_terminal_cannot_select_unrelated_or_rebound_parent_report(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    paths = h.stage_artifacts(report, day, "main_machine_policy")
    machine = json.loads(paths["machine_policy"].read_text())
    changed = p.seal(dict(machine, comparison_complete=False))
    assert not h._operating_machine_terminal_selected(native, day, changed)
    paths["machine_policy_terminal"].write_text(
        json.dumps(p.seal(dict(native, report_sha256="f" * 64)))
    )
    assert (
        "main_machine_policy:operating_terminal_disposition_invalid"
        in h._stage_output_issues(report, day, "main_machine_policy")
    )


def test_known_operator_initial_without_cumulative_selection_claim_remains_nonselected(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    paths = h.stage_artifacts(report, day, "main_machine_policy")
    initial = p.seal(
        dict(
            schema=native["schema"],
            source_date=day,
            target_date=day,
            status="completed",
            report_sha256=native["report_sha256"],
            **p.AUTH,
        )
    )
    paths["machine_policy_terminal"].write_text(json.dumps(initial))
    assert not h._operating_machine_terminal_selected(
        initial, day, json.loads(paths["machine_policy"].read_text())
    )
    assert h._stage_output_issues(report, day, "main_machine_policy") == []


def test_operating_selected_report_authority_cannot_be_added_by_resealing_both_artifacts(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, native = _operating_machine_stage_fixture(tmp_path, monkeypatch)
    paths = h.stage_artifacts(report, day, "main_machine_policy")
    machine = json.loads(paths["machine_policy"].read_text())
    machine = p.seal(dict(machine, allowed_runtime_apply=True))
    (report / "continuous_reversal" / day / "machine.json").write_text(
        json.dumps(machine)
    )
    paths["machine_policy"].write_text(json.dumps(machine))
    (report / "continuous_reversal" / day / "machine-comparison.json").write_text(json.dumps(machine))
    changed = p.seal(dict(native, report_sha256=machine["artifact_content_sha256"]))
    paths["machine_policy_terminal"].write_text(json.dumps(changed))
    assert not h._operating_machine_terminal_selected(changed, day, machine)
    assert (
        "main_machine_policy:operating_terminal_disposition_invalid"
        in h._stage_output_issues(report, day, "main_machine_policy")
    )


@pytest.mark.parametrize(
    "field,value", [("runtime_effect", True), ("source_date", "2026-10-12")]
)
def test_joint_initial_stage_rejects_resealed_authority_or_date_change(
    tmp_path, monkeypatch, field, value
):
    from src.engine.scalping import continuous_reversal_postclose as p

    h, day, report, machine, source = _joint_stage_fixture(tmp_path, monkeypatch)
    changed = p.seal({**machine, field: value})
    (report / "continuous_reversal" / day / "machine.json").write_text(
        json.dumps(changed)
    )
    h.stage_artifacts(report, day, "main_machine_policy")["machine_policy"].write_text(
        json.dumps(changed)
    )
    assert h._stage_output_issues(report, day, "main_machine_policy")


def test_initial_quantity_resume_refuses_running_main(tmp_path):
    path = (
        tmp_path
        / "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-10-13.status.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"target_date": "2026-10-13", "status": "running"}))
    with pytest.raises(ValueError, match="requires_failed_native_main"):
        mod.validate_initial_quantity_resume(tmp_path, "2026-10-13")


def test_initial_quantity_resume_refuses_other_failed_command(tmp_path):
    day = "2026-10-13"
    path = (
        tmp_path
        / f"data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{day}.status.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "target_date": day,
                "status": "failed",
                "exit_code": 1,
                "reason": "command_failed",
                "run_id": "native",
            }
        )
    )
    log = tmp_path / "logs/threshold_cycle_postclose_cron.log"
    log.parent.mkdir()
    log.write_text(
        "[PERF] "
        + json.dumps(
            {
                "run_id": "native",
                "phase": "command",
                "producer_module": "other",
                "exit_code": 1,
            }
        )
    )
    with pytest.raises(ValueError, match="failed_command_not_initial_quantity"):
        mod.validate_initial_quantity_resume(tmp_path, day)


def test_initial_quantity_resume_binds_native_prefix_and_rejects_changed_artifact(
    tmp_path, monkeypatch
):
    day = "2026-10-13"
    report = tmp_path / "data/report"
    paths = {
        "src.engine.monitoring.rising_missed_intraday_feedback": "rising_missed_intraday_feedback",
        "src.engine.observation_source_quality_audit": "observation_source_quality_audit",
        "src.engine.scalping.entry_split_order_plan": "entry_split_order_plan",
        "src.engine.automation.entry_cancel_wait_tuning": "entry_cancel_wait_tuning",
    }
    contracts = {
        name: "code"
        for name in [
            "src/trading/market/session_contract.py",
            "src/trading/market/aftermarket_eligibility.py",
            "src/trading/order/aftermarket_reconciliation.py",
            "src/engine/monitoring/market_opportunity_census.py",
            "src/engine/observation_source_quality_audit.py",
        ]
    }

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    for name in contracts:
        path = write(tmp_path / name, {"code": name})
        contracts[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    metrics = []
    for module, kind in paths.items():
        artifact = write(
            report / kind / f"{kind}_{day}.json", {"target_date": day, "status": "pass"}
        )
        md = artifact.with_suffix(".md")
        md.write_text("native")
        write(
            Path(str(artifact) + ".reuse-contract.json"),
            dict(
                schema="postclose_artifact_reuse_contract_v1",
                target_date=day,
                artifact_path=str(artifact),
                artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                markdown_path=str(md),
                markdown_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),
                aftermarket_contract_sha256s=contracts,
            ),
        )
        metrics.append(
            dict(
                run_id="native",
                phase="command",
                producer_module=module,
                exit_code=0,
                measurement_complete=True,
                target_date=day,
                code_commit="origin",
            )
        )
    for module, kind, name in [
        (
            "src.engine.market_panic_breadth_collector",
            "market_panic_breadth",
            "market_panic_breadth",
        ),
        (
            "src.engine.strategy_position_performance_report",
            "strategy_position_fact_sync",
            "strategy_position_fact_sync",
        ),
        (
            "src.engine.scalping.scale_in_split_order_plan",
            "scale_in_split_order_plan",
            "scale_in_split_order_plan",
        ),
    ]:
        suffix = ".status.json" if kind == "strategy_position_fact_sync" else ".json"
        write(
            report / kind / f"{name}_{day}{suffix}",
            {"target_date": day, "status": "pass"},
        )
        metrics.append(
            dict(
                run_id="native",
                phase="command",
                producer_module=module,
                exit_code=0,
                measurement_complete=True,
                target_date=day,
                code_commit="origin",
            )
        )
    for path in [
        tmp_path
        / f"data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_{day}.json",
        tmp_path
        / f"data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_{day}.json",
        report / f"entry_cancel_wait_tuning/entry_cancel_wait_policy_{day}.json",
    ]:
        write(path, {"target_date": day})
    metrics.append(
        dict(
            run_id="native",
            phase="command",
            producer_module="src.engine.scalping.initial_quantity_policy",
            exit_code=1,
        )
    )
    log = tmp_path / "logs/threshold_cycle_postclose_cron.log"
    log.parent.mkdir()
    log.write_text("\n".join("[PERF] " + json.dumps(v) for v in metrics))
    write(
        report
        / f"threshold_cycle_postclose_status/threshold_cycle_postclose_{day}.status.json",
        dict(
            target_date=day,
            status="failed",
            exit_code=1,
            reason="command_failed",
            run_id="native",
            code_commit="origin",
        ),
    )
    write(
        tmp_path / f"data/runtime/update_kospi_status/update_kospi_{day}.json",
        dict(
            target_date=day,
            status="completed",
            db_state={"latest_quote_date": day, "rows_on_latest_date": 1},
        ),
    )
    monkeypatch.setattr(mod, "stage_receipt_issues", lambda *a: [])
    monkeypatch.setattr(mod, "_machine_source_preflight_issue", lambda *a, **k: None)
    proof = mod.validate_initial_quantity_resume(tmp_path, day)
    assert proof["origin_run_id"] == "native" and proof["runtime_effect"] is False
    alias = tmp_path / "release"
    alias.mkdir()
    for name in ["data", "logs", "src"]:
        (alias / name).symlink_to(tmp_path / name, target_is_directory=True)

    def canonical_stage(report_dir, *args):
        assert report_dir == report.resolve()
        return []

    def canonical_preflight(report_dir, *args, **kwargs):
        assert report_dir == report.resolve()
        return None

    monkeypatch.setattr(mod, "stage_receipt_issues", canonical_stage)
    monkeypatch.setattr(mod, "_machine_source_preflight_issue", canonical_preflight)
    assert mod.validate_initial_quantity_resume(alias, day)["origin_run_id"] == "native"
    artifact = report / f"entry_split_order_plan/entry_split_order_plan_{day}.json"
    artifact.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="resume_artifact_changed"):
        mod.validate_initial_quantity_resume(tmp_path, day)


@pytest.mark.parametrize(
    "locator,damage",
    [
        (locator, damage)
        for locator in ("selected", "strict", "receipt", "preopen")
        for damage in (None, "code", "output", "missing_origin", "alias", "foreign")
    ]
    + [("preopen", "preopen_date"), ("preopen", "preopen_failed")],
)
def test_stage_code_origin_survives_release_inventory_growth(
    stage_environment, monkeypatch, locator, damage
):
    h, day, report, run, _produce = stage_environment
    value = run("legacy_machine_report")
    value.pop("stage_code_root", None)
    managed = report.parent.parent / "KORStockScan-runtime-releases"
    managed.mkdir()
    selected, origin = managed / "selected", managed / "original"
    for root in (selected, origin):
        (root / "src/engine/automation").mkdir(parents=True)
        (root / ".git").write_text("gitdir: immutable")
        (root / "src/engine/automation/postclose_summary_handoff.py").write_text(
            "original"
        )
    for i in range(300):
        root = managed / f"old-{i:03d}"
        root.mkdir()
        (root / ".git").write_text("gitdir: immutable")
    selector = report.parent / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(parents=True, exist_ok=True)
    selector.write_text(
        json.dumps(
            dict(
                schema="runtime_release_selection_v1",
                release_root=str(selected),
                git_commit="a" * 40,
            )
        )
    )
    strict = (
        report
        / "threshold_cycle_postclose_verification"
        / f"threshold_cycle_postclose_verification_{day}.json"
    )
    strict.parent.mkdir(parents=True, exist_ok=True)
    strict.write_text(
        json.dumps(
            dict(date=day, code_commit=("c" if locator == "preopen" else "b") * 40)
        )
    )
    if locator == "preopen":
        from src.engine.build_next_stage2_checklist import _next_krx_trading_day

        target = _next_krx_trading_day(day)
        preopen = (
            report
            / "threshold_cycle_preopen_status"
            / f"threshold_cycle_preopen_{target}.status.json"
        )
        preopen.parent.mkdir(parents=True)
        preopen.write_text(
            json.dumps(
                dict(
                    target_date=day if damage == "preopen_date" else target,
                    status="failed" if damage == "preopen_failed" else "succeeded",
                    selected_release_commit="b" * 40,
                )
            )
        )
    if locator == "selected":
        origin = selected
    if locator == "receipt":
        value["stage_code_root"] = str(origin)
    if damage == "missing_origin":
        (origin / "src/engine/automation/postclose_summary_handoff.py").unlink()
    elif damage == "alias":
        alias = managed / "alias"
        alias.symlink_to(origin, target_is_directory=True)
        if locator == "receipt":
            value["stage_code_root"] = str(alias)
        else:
            origin = alias
    elif damage == "foreign":
        foreign = managed.parent / "foreign"
        foreign.mkdir()
        if locator == "receipt":
            value["stage_code_root"] = str(foreign)
        else:
            origin = foreign
    native_iterdir = Path.iterdir
    ordered_roots = [managed / f"old-{i:03d}" for i in range(300)] + [origin, selected]
    monkeypatch.setattr(
        Path,
        "iterdir",
        lambda path: iter(ordered_roots) if path == managed else native_iterdir(path),
    )
    calls = []

    def code(stage, commands, root, **kwargs):
        calls.append(root)
        return (
            "sealed-producer-code"
            if root == origin and damage != "code"
            else "different-code"
        )

    monkeypatch.setattr(h, "_stage_code", code)
    from src.engine.infrastructure import startup_validation_code_context as context

    monkeypatch.setattr(
        context, "_git_head", lambda root: ("b" if root == origin else "a") * 40
    )
    monkeypatch.setattr(
        h.subprocess,
        "check_output",
        lambda *a, **kw: pytest.fail("sealed-stage lookup attempted process creation"),
    )
    value["stage_code_sha256"] = "sealed-producer-code"
    if damage == "output":
        output = next(
            iter(h.stage_artifacts(report, day, "legacy_machine_report").values())
        )
        output.write_text(output.read_text() + " changed")
    h._stage_write(h.stage_path(report, day, "legacy_machine_report"), value)
    result = h.stage_receipt_issues(
        report, day, "legacy_machine_report", code_hash="current-code"
    )
    if damage is None:
        assert result == []
        assert len(calls) <= 2
    else:
        assert result
    assert len(calls) <= 258


def test_native_stage_writer_binds_root_for_the_later_code_consumer(
    stage_environment, monkeypatch
):
    h, day, report, _run, produce = stage_environment
    root = report.parent.parent / "KORStockScan-runtime-releases" / "producer"
    (root / "src/engine/automation").mkdir(parents=True)
    (root / ".git").write_text("gitdir: immutable")
    (root / "src/engine/automation/postclose_summary_handoff.py").write_text("reviewed")
    result = h.run_stage(
        "legacy_machine_report", day, report_dir=report, project=root, runner=produce
    )
    assert result["status"] == "succeeded" and result["stage_code_root"] == str(root)
    selector = report.parent / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(parents=True, exist_ok=True)
    selector.write_text(
        json.dumps(
            dict(
                schema="runtime_release_selection_v1",
                release_root=str(root),
                git_commit="a" * 40,
            )
        )
    )
    monkeypatch.setattr(
        h,
        "_stage_code",
        lambda stage, commands, project, **kw: result["stage_code_sha256"],
    )
    assert (
        h.stage_receipt_issues(
            report, day, "legacy_machine_report", code_hash="later-consumer"
        )
        == []
    )


@pytest.mark.parametrize("mode", ["verified", "missing", "invalid", "wrong_date"])
def test_quantity_summary_consumes_native_stage_proof_before_cold_replay(
    tmp_path, monkeypatch, mode
):
    from src.engine.scalping import initial_quantity_policy as quantity
    from src.engine.scalping import initial_quantity_monitor_projection as projection

    day = "2026-10-23"
    path = tmp_path / "stage.json"
    path.write_text(
        json.dumps(dict(source_date="2000-01-01" if mode == "wrong_date" else day))
    )
    calls = []

    def proof(*a, **kw):
        if mode == "invalid":
            raise ValueError("quantity_monitor_source_changed")
        return None if mode == "missing" else {"issued": {}, "observation": {}}

    def cold(*a):
        calls.append("cold")
        return True

    monkeypatch.setattr(projection, "read_verified", proof)
    monkeypatch.setattr(quantity, "refresh_quantity_stage_terminal_valid", cold)
    if mode in ("invalid", "wrong_date"):
        with pytest.raises((ValueError, RuntimeError)):
            mod.source_receipt({"initial_quantity_refresh_stage": path}, day)
    else:
        mod.source_receipt({"initial_quantity_refresh_stage": path}, day)
    assert calls == (["cold"] if mode == "missing" else [])
