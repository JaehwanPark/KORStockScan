import gzip
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.automation import postclose_summary_handoff as mod




def test_machine_barrier_waits_for_exact_inputs_and_allows_scoped_recovery(tmp_path, monkeypatch):
    day = "2026-09-21"
    monkeypatch.setattr(mod, "producer_receipt_issues", lambda *a: [])
    assert "ai_decision_outcome_labels" in mod.machine_input_issues(tmp_path, day)[0]
    for label in ("ai_decision_outcome_labels", "low_price_two_leg_expanded_candidate_research", "runtime_approval_summary"):
        path = tmp_path / label / f"{label}_{day}.json"
        path.parent.mkdir()
        path.write_text(json.dumps({"target_date": day}))
    main = tmp_path / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{day}.status.json"
    main.parent.mkdir()
    main.write_text('{"status":"running"}')
    assert mod.wait_for_machine_inputs(tmp_path, day, timeout=0) == 75
    main.write_text('{"status":"failed"}')
    assert mod.wait_for_machine_inputs(tmp_path, day, timeout=0) == 0
    path.write_text('{"target_date":"2026-09-17"}')
    assert mod.wait_for_machine_inputs(tmp_path, day, timeout=0) == 75


def test_incomplete_joint_cohort_is_reported_without_granting_allocation(tmp_path, monkeypatch):
    from datetime import date
    from src.engine.monitoring import research_closed_loop as loop
    own = dict(inputs_sha256="own")
    peer = dict(schema=loop.SCHEMA, family="widget", source_date="2026-09-21", **loop.AUTHORITY)
    peer["inputs_sha256"] = loop.digest(peer)
    monkeypatch.setattr(loop, "joint_inputs", lambda *a, **kw: own)
    monkeypatch.setattr(loop, "read_object", lambda *a: peer)
    def invalid(*a, **kw):
        raise ValueError("joint_cohort_member_pruned_without_supersession")
    monkeypatch.setattr(loop, "frozen_joint_bundle", invalid)
    result = loop.combined_joint_gate({}, family="episode", source_date=date(2026,9,21), directory=tmp_path)
    assert result["status"] == "allocation_blocked"
    assert result["reason"] == "joint_cohort_member_pruned_without_supersession"
    assert result["feasible_combined_net_profit_krw"] is None
    assert all(result[k] is v for k, v in loop.AUTHORITY.items())


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

    source = mod.source_paths(reports, "2026-09-07", "checklist")[
        "conversion_lane"
    ]
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


def test_initial_quantity_direct_source_respects_effective_lower_bound_and_invalid_current(tmp_path):
    reports = tmp_path / "data" / "report"
    current = tmp_path / "data" / "runtime" / "initial_quantity" / "current.json"
    assert "initial_quantity_refresh_stage" not in mod.source_paths(
        reports, "2026-09-28", "tower")
    current.parent.mkdir(parents=True)
    current.write_text('{"effective_from":"2026-09-29"}')
    assert "initial_quantity_refresh_stage" not in mod.source_paths(
        reports, "2026-09-28", "tower")
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
    before = {consumer: mod.source_receipt(mod.source_paths(reports, day, consumer), day)
              for consumer in ("tower", "checklist")}
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
    summary = reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
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
    bootstrap = reports.parent / "runtime" / "policy_bootstrap" / "runtime_policy_bootstrap_2026-09-21.json"
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
    selection_path.write_text(json.dumps({"schema": "runtime_release_selection_v1",
                                          "git_commit": selected, "release_root": "/releases/selected"}))
    summary_path = reports / "runtime_approval_summary" / f"runtime_approval_summary_{source}.json"
    summary_path.parent.mkdir(parents=True)
    summary = {"date": source, "preopen_consumption_state": "pending",
        "preopen_consumption_receipt": {"source_date": source, "apply_date": apply,
            "manifest_path": str(manifest_path), "manifest_sha256": None,
            "verification_path": str(verify_path), "verification_sha256": None,
            "release_selection_sha256": None, "selected_release_commit": None}}
    summary_path.write_text(json.dumps(summary))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "pending"

    root.mkdir(parents=True)
    env_path.write_text("export TEST=true\n")
    manifest = {"target_date": apply, "source_incumbent_target_date": "2026-09-19",
        "selected_release_sha": selected, "env_file": str(env_path),
        "env_sha256": bootstrap._digest_bytes(env_path.read_bytes()),
        "selected_families": []}
    manifest["manifest_sha256"] = bootstrap._digest_json(manifest)
    manifest_path.write_text(json.dumps(manifest))
    verify_path.write_text(json.dumps({"target_date": apply, "status": "pass",
        "passed": True, "manifest_sha256": manifest["manifest_sha256"],
        "pid": None, "pid_passed": None, "pid_env_available": True}))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "stale"
    direct = mod.verify_summary_handoff(
        source, report_dir=reports, checklist_path=tmp_path / "unused.md",
        require_tower=False, require_checklist=False,
    )
    assert "postclose_summary_handoff:future_preopen_generation_stale" in direct["issues"]
    transition = bootstrap.publish_future_handoff_transition(
        apply, data_dir=data
    )
    assert transition["status"] == "linked"
    linked = mod.inspect_future_handoff(summary, source, report_dir=reports)
    assert linked["status"] == "transitioned_no_pid"
    assert linked["actual_pid_consumed"] is False
    assert linked["valid_empty"] is True
    direct = mod.verify_summary_handoff(
        source, report_dir=reports, checklist_path=tmp_path / "unused.md",
        require_tower=False, require_checklist=False,
    )
    assert "postclose_summary_handoff:future_preopen_generation_stale" not in direct["issues"]
    assert mod.stage_overview(reports, source)["future_handoff"]["status"] == "transitioned_no_pid"

    original_verify = verify_path.read_bytes()
    verify = json.loads(original_verify)
    verify["verified_at"] = "2026-09-28T08:00:00+09:00"
    verify_path.write_text(json.dumps(verify))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "stale"
    retry = bootstrap.publish_future_handoff_transition(apply, data_dir=data)
    assert retry["status"] == "linked" and retry["path"] != transition["path"]
    assert Path(transition["path"]).is_file() and Path(retry["path"]).is_file()
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "transitioned_no_pid"
    later_source = "2026-09-24"
    later_summary = {**summary, "date": later_source,
        "preopen_consumption_receipt": {**summary["preopen_consumption_receipt"],
                                         "source_date": later_source}}
    later_path = summary_path.with_name(f"runtime_approval_summary_{later_source}.json")
    later_path.write_text(json.dumps(later_summary))
    both = bootstrap.publish_future_handoff_transition(apply, data_dir=data)
    assert both["status"] == "linked" and len(both["transitions"]) == 2
    assert {row["source_date"] for row in both["transitions"]} == {source, later_source}
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "transitioned_no_pid"
    verify_path.write_bytes(original_verify)
    failed_verify = json.loads(original_verify)
    failed_verify.update(status="fail", passed=False)
    verify_path.write_text(json.dumps(failed_verify))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "rejected"
    pid_verify = json.loads(original_verify)
    pid_verify.update(pid=4321, pid_passed=True)
    verify_path.write_text(json.dumps(pid_verify))
    pid_state = mod.inspect_future_handoff(summary, source, report_dir=reports)
    assert pid_state["status"] == "stale"
    assert pid_state["pid_receipt_present"] is True
    assert pid_state["actual_pid_consumed"] is False
    summary["preopen_consumption_state"] = "off"
    summary_path.write_text(json.dumps(summary))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "off"
    assert bootstrap.publish_future_handoff_transition(
        apply, data_dir=data, source_date=source)["status"] == "off"
    summary["preopen_consumption_state"] = "pending"
    summary_path.write_text(json.dumps(summary))
    verify_path.write_bytes(original_verify)
    original_manifest = manifest_path.read_bytes()
    wrong_date = json.loads(original_manifest)
    wrong_date["target_date"] = "2026-09-29"
    manifest_path.write_text(json.dumps(wrong_date))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "stale"
    manifest_path.write_bytes(original_manifest)
    selection_path.write_text(json.dumps({"schema": "runtime_release_selection_v1",
                                          "git_commit": "c" * 40, "release_root": "/releases/new"}))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "stale"
    selection_path.write_text(json.dumps({"schema": "runtime_release_selection_v1",
                                          "git_commit": selected, "release_root": "/releases/selected"}))

    summary["preopen_consumption_state"] = "verified"
    receipt = summary["preopen_consumption_receipt"]
    receipt["manifest_sha256"] = bootstrap._digest_bytes(manifest_path.read_bytes())
    receipt["verification_sha256"] = bootstrap._digest_bytes(verify_path.read_bytes())
    receipt["release_selection_sha256"] = bootstrap._digest_bytes(selection_path.read_bytes())
    receipt["selected_release_commit"] = selected
    summary_path.write_text(json.dumps(summary))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "same_generation_no_pid"
    pid_verify = json.loads(original_verify)
    pid_verify.update(pid=4321, pid_passed=True)
    verify_path.write_text(json.dumps(pid_verify))
    receipt["verification_sha256"] = bootstrap._digest_bytes(verify_path.read_bytes())
    summary_path.write_text(json.dumps(summary))
    pid_state = mod.inspect_future_handoff(summary, source, report_dir=reports)
    assert pid_state["status"] == "same_generation_pid_receipt_unconfirmed"
    assert pid_state["pid_receipt_present"] is True
    assert pid_state["actual_pid_consumed"] is False
    selection_path.write_text(json.dumps({"schema": "runtime_release_selection_v1",
                                          "git_commit": selected, "release_root": "/releases/moved"}))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "stale"
    selection_path.write_text(json.dumps({"schema": "runtime_release_selection_v1",
                                          "git_commit": "c" * 40, "release_root": "/releases/new"}))
    assert mod.inspect_future_handoff(summary, source, report_dir=reports)["status"] == "stale"


def test_schema_v3_pre_retirement_source_uses_direct_handoff(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-17"
    summary = reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
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
    summary_path = reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    receipt = mod.source_receipt(mod.source_paths(reports, day, "tower"), day)
    tower = reports / "tuning_performance_control_tower" / f"tuning_performance_control_tower_{day}.json"
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


def test_independent_producer_roundtrip_and_post_terminal_source_drift(monkeypatch, tmp_path):
    from src.engine.automation import postclose_summary_handoff as handoff
    from src.engine.automation.postclose_recommendation_intake import source_paths
    from src.utils import constants
    from pathlib import Path
    import json
    data = tmp_path / "data"
    monkeypatch.setattr(constants, "DATA_DIR", data)
    monkeypatch.setattr(constants, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(handoff.subprocess, "check_output", lambda *a, **k: "a" * 40)
    day = "2026-09-17"
    paths = source_paths(data / "report", day)
    for label in handoff.INDEPENDENT_SOURCES["machine"]:
        path = paths.get(label, data / "report" / label / f"{label}_{day}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"target_date": day}))
    assert handoff._producer_main(["--owner", "machine", "--date", day, "--phase", "started"]) == 0
    assert handoff.producer_receipt_issues(data / "report", day, "machine")
    assert handoff._producer_main(["--owner", "machine", "--date", day, "--phase", "finished"]) == 0
    assert handoff.producer_receipt_issues(data / "report", day, "machine") == []
    paths[handoff.INDEPENDENT_SOURCES["machine"][0]].write_text("{}")
    assert handoff.producer_receipt_issues(data / "report", day, "machine")
    old = handoff.producer_receipt_path(data / "report", day, "machine").read_bytes()
    assert handoff._producer_main(["--owner", "machine", "--date", day, "--phase", "started"]) == 0
    assert any(p.read_bytes() == old for p in (data / "report/postclose_producer_terminal/attempts").glob("*.json"))
    assert handoff._producer_main(["--owner", "machine", "--date", day, "--phase", "finished", "--exit-code", "17"]) == 1






@pytest.mark.parametrize('clock,publication,prepared,allowed', [
    ('2026-09-22T00:30:00+09:00', '2026-09-21', False, True),
    ('2026-09-22T07:29:59+09:00', '2026-09-21', False, True),
    ('2026-09-22T07:30:00+09:00', '2026-09-21', False, False),
    ('2026-09-22T00:30:00+09:00', '2026-09-21', True, False),
    ('2026-09-22T00:30:00+09:00', '', False, False),
    ('2026-09-22T00:30:00+09:00', '2026-09-18', False, False),
])
def test_overnight_publication_recovery_stops_before_preopen(tmp_path, monkeypatch, clock, publication, prepared, allowed):
    from datetime import date, datetime
    from src.engine.monitoring import research_closed_loop as loop
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(clock)
    monkeypatch.setattr(loop, 'datetime', Clock)
    monkeypatch.setattr(loop, 'DATA_DIR', tmp_path)
    monkeypatch.setenv('POSTCLOSE_POLICY_PUBLICATION_DATE', publication)
    effective = date(2026, 9, 22)
    folder = tmp_path / 'policies'
    initial = loop.publication_transaction(folder, effective_date=effective, files={'policy.json': {'revision': 1}})
    if prepared:
        root = tmp_path / 'runtime' / 'policy_bootstrap'
        root.mkdir(parents=True)
        (root / f'runtime_policy_bootstrap_{effective}.json').write_text('{}')
    parent = loop.future_publication_parent(folder, effective)
    if allowed:
        assert parent == initial['generation_sha256']
        updated = loop.publication_transaction(folder, effective_date=effective, files={'policy.json': {'revision': 2}}, expected_generation=parent)
        assert updated['parent_generation_sha256'] == parent
        loop.verify_publication(folder, effective_date=effective, name='policy.json', value={'revision': 2})
    else:
        assert parent is None
        with pytest.raises(ValueError, match='publication_conflict'):
            loop.publication_transaction(folder, effective_date=effective, files={'policy.json': {'revision': 2}}, expected_generation=initial['generation_sha256'])






@pytest.fixture
def stage_environment(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as h
    monkeypatch.setattr(h, '_stage_code', lambda *a: 'code-v2')
    monkeypatch.setattr(h, 'stage_commands', lambda stage, *a, **kw: [['fixture', stage]])
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_EVALUATION_WAIT_FOR_EOD', 'false')
    day = '2026-09-21'; report = tmp_path / 'data' / 'report'
    raw = report.parent / 'pipeline_events' / f'pipeline_events_{day}.jsonl'
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text('{"stage":"fixture"}\n')
    raw_stat = raw.stat()
    preflight = report / 'observation_source_quality_audit' / f'observation_source_quality_audit_{day}.json'
    preflight.parent.mkdir(parents=True, exist_ok=True)
    source = {'target_date':day, 'audit_phase':'preflight', 'status':'pass',
        'consumer_implementation_sha256':'audit-code',
        'summary':{'tuning_input_allowed':True},
        'source':{'generation_stable':True, 'pipeline_events':str(raw),
                  'generation':{'device':raw_stat.st_dev, 'inode':raw_stat.st_ino,
                                'size_bytes':raw_stat.st_size, 'mtime_ns':raw_stat.st_mtime_ns,
                                'ctime_ns':raw_stat.st_ctime_ns}}}
    preflight.write_text(json.dumps(source))
    binding = {'schema':'observation_source_quality_final_binding_v1', 'target_date':day,
        'audit_phase':'preflight', 'implementation_sha256':'audit-code',
        'artifact_sha256':hashlib.sha256(preflight.read_bytes()).hexdigest()}
    Path(str(preflight) + '.final-contract.json').write_text(json.dumps(binding))
    def produce(command, **kwargs):
        from src.engine.scalping.ai_action_outcome_calibration import _with_artifact_content_sha256
        stage = command[1]
        for name, path in h.stage_artifacts(report, day, stage).items():
            value = dict(target_date=day, status='complete')
            if name.startswith('machine_policy'):
                value['status'] = 'completed' if name.endswith('terminal') else 'machine_policy_generated'
                if name == 'machine_policy_terminal':
                    parent=json.loads(h.stage_artifacts(report, day, stage)['machine_policy'].read_text())
                    value['report_sha256']=parent['artifact_content_sha256']
                value = _with_artifact_content_sha256(value)
            if name == 'ai_decision_outcome_labels':
                value.update(schema='ai_decision_outcome_labels_v1', generated_at=day+'T21:00:00+09:00',
                    status='mature_label_rows_available', labels=[])
            if name == 'widget_collector_expansion_recommendation':
                from src.engine.monitoring.widget_collector_expansion_recommendation import history_input_manifest
                from datetime import date
                history = history_input_manifest(
                    report.parent / 'ai_decision_payloads', report / 'widget_mechanical_entry_replay',
                    through_date=date.fromisoformat(day),
                    sentinel_dir=report.parent / 'runtime' / 'sentinel_event_cache',
                    watch_config_path=report.parent / 'config' / 'widget_research_watch_symbols.json')
                value['source'] = {'history_input_manifest': history,
                    'feature_paths': [row['path'] for row in history['entries'] if row['kind'] == 'payload'],
                    'replay_paths': [row['path'] for row in history['entries'] if row['kind'] == 'replay']}
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
        return 0
    def run(stage, **kwargs):
        return h.run_stage(stage, day, report_dir=report, project=tmp_path,
            runner=kwargs.pop('runner', produce), **kwargs)
    return h, day, report, run, produce


def test_machine_stage_requires_exact_bound_preflight(stage_environment):
    h, day, report, run, _produce = stage_environment
    preflight = report / 'observation_source_quality_audit' / f'observation_source_quality_audit_{day}.json'
    binding = Path(str(preflight) + '.final-contract.json')
    assert h._machine_source_preflight_issue(report, day) is None
    source = json.loads(preflight.read_text())
    source['summary']['tuning_input_allowed'] = False
    preflight.write_text(json.dumps(source))
    assert h._machine_source_preflight_issue(report, day) == 'source_quality_preflight_identity_or_hash_invalid'
    binding_body = json.loads(binding.read_text())
    binding_body['artifact_sha256'] = hashlib.sha256(preflight.read_bytes()).hexdigest()
    binding.write_text(json.dumps(binding_body))
    blocked = run('main_machine_policy', runner=lambda *a, **kw: pytest.fail('preflight blocked'))
    assert blocked['status'] == 'deferred'
    assert blocked['policy_disposition'] == 'source_quality_blocked'
    assert blocked['issues'] == ['source_quality_preflight_blocked']


def test_machine_terminal_survives_later_final_audit_generation(stage_environment):
    h, day, report, run, _produce = stage_environment
    machine = run('main_machine_policy')
    assert machine['status'] == 'succeeded'
    assert machine['source_quality_preflight_sha256']
    preflight = report / 'observation_source_quality_audit' / f'observation_source_quality_audit_{day}.json'
    preflight.write_text(json.dumps({'target_date':day, 'audit_phase':'final'}))
    assert h.stage_receipt_issues(report, day, 'main_machine_policy') == []


@pytest.mark.parametrize('staging_status', ['operator_designation_preserved', 'designated_policy_staged'])
def test_machine_stage_distinguishes_designation_from_automatic_carry(stage_environment, monkeypatch, staging_status):
    h, day, report, run, produce = stage_environment
    # Publisher/source validation is covered by designated-policy integration
    # tests. Exercise the stage receipt's downstream semantic projection here.
    monkeypatch.setattr(h, '_safe_stage_output_issues', lambda *args: [])
    def designated(command, **kwargs):
        produce(command, **kwargs)
        path = h.stage_artifacts(report, day, 'main_machine_policy')['machine_policy_terminal']
        terminal = json.loads(path.read_text())
        terminal.update(selection_basis='win_rate_only', disposition='incumbent_carried',
                        staged=dict(status=staging_status, bundle_sha256='designated-bundle'))
        path.write_text(json.dumps(terminal))
        return 0
    receipt = run('main_machine_policy', runner=designated)
    assert receipt['status'] == 'succeeded'
    assert receipt['policy_disposition'] == 'operator_designated'
    assert receipt['automatic_policy_disposition'] == 'incumbent_carried'
    assert receipt['designated_bundle_sha256'] == 'designated-bundle'


def test_machine_closed_date_recovery_accepts_exact_bound_final_audit(stage_environment, monkeypatch):
    h, day, report, run, _produce = stage_environment
    from src.engine import observation_source_quality_audit as audit_owner
    first = run('main_machine_policy')
    assert first['status'] == 'succeeded'
    audit = report / 'observation_source_quality_audit' / f'observation_source_quality_audit_{day}.json'
    binding = Path(str(audit) + '.final-contract.json')
    source = json.loads(audit.read_text())
    source['audit_phase'] = 'final'
    audit.write_text(json.dumps(source))
    final_binding = json.loads(binding.read_text())
    final_binding['audit_phase'] = 'final'
    final_binding['artifact_sha256'] = hashlib.sha256(audit.read_bytes()).hexdigest()
    binding.write_text(json.dumps(final_binding))
    assert h._machine_source_preflight_issue(report, day) == 'source_quality_preflight_identity_or_hash_invalid'
    monkeypatch.setattr(audit_owner, 'check_audit_reusable', lambda *args, **kwargs: {'reusable': False})
    assert h._machine_source_preflight_issue(report, day, recovery=True) == 'source_quality_final_audit_not_reusable'
    monkeypatch.setattr(audit_owner, 'check_audit_reusable', lambda *args, **kwargs: {'reusable': True})
    assert h._machine_source_preflight_issue(report, day, recovery=True) is None
    second = run('main_machine_policy', recovery=True)
    assert second['status'] == 'succeeded'
    assert second['source_quality_audit_phase'] == 'final'
    assert second['source_quality_preflight_sha256'] == final_binding['artifact_sha256']


def test_machine_stage_rejects_raw_generation_changed_after_preflight(stage_environment):
    h, day, report, run, _produce = stage_environment
    raw = report.parent / 'pipeline_events' / f'pipeline_events_{day}.jsonl'
    raw.write_text(raw.read_text() + '{"stage":"late_writer"}\n')
    assert h._machine_source_preflight_issue(report, day) == (
        'source_quality_preflight_raw_generation_changed'
    )
    blocked = run('main_machine_policy', runner=lambda *a, **kw: pytest.fail('stale raw'))
    assert blocked['status'] == 'deferred'
    assert blocked['issues'] == ['source_quality_preflight_raw_generation_changed']


def test_machine_resource_timeout_writes_deferred_terminal(stage_environment):
    _h, _day, _report, run, _produce = stage_environment
    blocked = run('main_machine_policy',
        resource_blocked={'ok':False, 'mem_available_mb':3020.0,
                          'required_mem_mb':4096.0, 'issues':['mem_available_mb=3020.0<4096.0']},
        runner=lambda *a, **kw: pytest.fail('resource guard blocked'))
    assert blocked['status'] == 'deferred'
    assert blocked['issues'] == ['resource_guard_timeout']
    assert blocked['resource_guard']['mem_available_mb'] == 3020.0




@pytest.mark.parametrize("failed_stage", ["market_weakness", "main_auxiliary_policy", "episode_policy", "summary_handoff"])
def test_stage_failure_does_not_cancel_independent_machine(stage_environment, failed_stage):
    h, day, report, run, produce = stage_environment
    if failed_stage == 'main_auxiliary_policy':
        run('outcome_labels')
        run('legacy_machine_report')
    if failed_stage == 'market_weakness': run('machine_attribution')
    failed = run(failed_stage, runner=lambda *a, **kw: 9)
    machine = run('main_machine_policy')
    assert failed['status'] == 'failed'
    assert machine['status'] == 'succeeded'
    assert not h.stage_receipt_issues(report, day, 'main_machine_policy')
    assert h.stage_receipt_issues(report, day, 'main_machine_policy', code_hash='new-code') == ['main_machine_policy:code_changed']


def test_machine_stage_validates_bound_completed_price_generation(stage_environment):
    from src.engine.scalping.ai_action_outcome_calibration import (
        MACHINE_COMPLETED_PRICE_CACHE_SCHEMA, _with_artifact_content_sha256,
    )

    h, day, report_dir, run, _produce = stage_environment
    assert run('main_machine_policy')['status'] == 'succeeded'
    cache_path = (report_dir / 'machine_completed_price_source'
                  / f'machine_completed_price_source_{day}.json')
    cache_path.parent.mkdir(parents=True)
    cache = _with_artifact_content_sha256({
        'schema': MACHINE_COMPLETED_PRICE_CACHE_SCHEMA, 'source_date': day,
        'prices': [], 'provenance': [],
    })
    cache_path.write_text(json.dumps(cache))
    paths = h.stage_artifacts(report_dir, day, 'main_machine_policy')
    machine = json.loads(paths['machine_policy'].read_text())
    machine['observation_source_counts'] = {'completed_price_cache_receipts': [{
        'source_date': day, 'path': str(cache_path),
        'artifact_content_sha256': cache['artifact_content_sha256'],
    }]}
    machine = _with_artifact_content_sha256(machine)
    paths['machine_policy'].write_text(json.dumps(machine))
    terminal = json.loads(paths['machine_policy_terminal'].read_text())
    terminal['report_sha256'] = machine['artifact_content_sha256']
    paths['machine_policy_terminal'].write_text(json.dumps(_with_artifact_content_sha256(terminal)))
    assert h._stage_output_issues(report_dir, day, 'main_machine_policy') == []
    cache['prices'].append({'stock_code': '005930'})
    cache_path.write_text(json.dumps(_with_artifact_content_sha256(cache)))
    assert 'main_machine_policy:completed_price_source_generation_changed' in h._stage_output_issues(
        report_dir, day, 'main_machine_policy')
    machine['observation_source_counts']['completed_price_cache_receipts'] = [{
        'source_date': day, 'path': str(cache_path), 'status': 'collected',
    }]
    paths['machine_policy'].write_text(json.dumps(_with_artifact_content_sha256(machine)))
    assert 'main_machine_policy:completed_price_source_receipts_invalid' in h._stage_output_issues(
        report_dir, day, 'main_machine_policy')


def test_stage_prerequisites_and_changed_generation(stage_environment):
    h, day, report, run, produce = stage_environment
    deferred = run('machine_timing')
    assert deferred['status'] == 'deferred'
    assert run('machine_attribution')['status'] == 'succeeded'
    assert run('machine_timing')['status'] == 'succeeded'
    path = h.stage_artifacts(report, day, 'machine_attribution')['machine_microstructure_attribution']
    path.write_text(json.dumps(dict(target_date=day, status='complete', revised=True)))
    assert h.stage_receipt_issues(report, day, 'machine_attribution') == ['machine_attribution:output_generation_changed']
    assert run('machine_timing')['status'] == 'deferred'


def test_pre_submit_stage_rejects_unsealed_raw_generation(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as handoff

    day = "2026-09-23"
    reports = tmp_path / "data" / "report"
    monkeypatch.setattr(handoff, "_stage_code", lambda *args, **kwargs: "fixture-code")
    monkeypatch.setattr(handoff, "stage_commands", lambda *args, **kwargs: [["fixture"]])
    called = []
    result = handoff.run_stage(
        "pre_submit_delay", day, report_dir=reports, project=tmp_path,
        runner=lambda *args, **kwargs: called.append(args) or 0,
    )
    assert result["status"] == "deferred"
    assert result["exit_code"] == 75
    assert "raw_source_missing" in " ".join(result["issues"])
    assert called == []
    off = handoff.run_stage(
        "pre_submit_delay", day, report_dir=reports, project=tmp_path,
        runner=lambda *args, **kwargs: called.append(args) or 0, off=True,
    )
    assert off["status"] == "off"
    assert handoff.stage_receipt_issues(reports, day, "pre_submit_delay") == []
    assert called == []


def test_pre_submit_receipt_binds_sealed_source_generation(tmp_path, monkeypatch):
    from src.engine.pipeline_event_summary import (
        ProducerSummaryCompactor, seal_producer_summary_source,
    )
    from src.engine.scalping.pre_submit_delay_tuning import seal_family_source_ledger

    day = "2026-09-23"
    data = tmp_path / "data"
    reports = data / "report"
    raw = data / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir(parents=True)
    event = {"event_type": "pipeline_event", "pipeline": "ENTRY_PIPELINE",
             "stage": "scalping_scanner_fast_precheck", "stock_code": "005930",
             "emitted_at": f"{day}T10:00:00", "emitted_date": day,
             "record_id": 1, "fields": {}}
    raw.write_text(json.dumps(event) + "\n")
    compactor = ProducerSummaryCompactor(
        summary_dir=data / "pipeline_event_summaries", mode="shadow",
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
    receipt = {"schema": mod.STAGE_SCHEMA, "stage_id": "pre_submit_delay",
               "source_date": day, "status": "succeeded", "exit_code": 0,
               "run_id": "fixture-run", "stage_code_sha256": "fixture-code",
               "pipeline_source_generation_sha256": ledger["ledger_sha256"],
               "sources": mod._stage_sources(paths), "prerequisite_receipts": {},
               "input_sources": mod._stage_sources(mod.stage_input_paths(reports, day, "pre_submit_delay"))}
    mod._stage_write(mod.stage_path(reports, day, "pre_submit_delay"), receipt)
    assert mod.stage_receipt_issues(reports, day, "pre_submit_delay", code_hash="fixture-code") == []

    raw.write_text(raw.read_text() + json.dumps({**event, "record_id": 2}) + "\n")
    assert "pre_submit_delay:raw_generation_changed" in mod.stage_receipt_issues(
        reports, day, "pre_submit_delay", code_hash="fixture-code",
    )

    raw.write_text(json.dumps(event) + "\n")
    monkeypatch.setattr(mod, "_stage_code", lambda *args, **kwargs: "fixture-code")
    monkeypatch.setattr(mod, "stage_commands", lambda *args, **kwargs: [["fixture"]])

    def drift_during_consumer(*args, **kwargs):
        raw.write_text(raw.read_text() + json.dumps({**event, "record_id": 3}) + "\n")
        return 0

    result = mod.run_stage(
        "pre_submit_delay", day, report_dir=reports, project=tmp_path,
        runner=drift_during_consumer,
    )
    assert result["status"] == "failed"
    assert "pipeline_source_quality:raw_generation_changed" in result["issues"]


def test_summary_handoff_tracks_later_active_stage_generation(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert run('summary_handoff')['status'] == 'succeeded'
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == []
    assert run('legacy_machine_report')['status'] == 'succeeded'
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == [
        'summary_handoff:input_generation_changed'
    ]


@pytest.mark.parametrize("damage", [
    None, "digest", "retired_input_changed", "retired_input_missing",
    "input_set", "output", "code", "failed", "new_publication", "invalid_publication",
])
def test_historical_summary_consumer_preserves_exact_generation_only(stage_environment, damage):
    h, day, report, run, _produce = stage_environment
    assert run('summary_handoff')['status'] == 'succeeded'
    path = h.stage_path(report, day, 'summary_handoff')
    value = h._load_json(path)
    value['schema'] = 'postclose_stage_terminal_v2'
    legacy_paths = {}
    for stage in ('widget_policy', 'collector_recommendation'):
        terminal = report / 'postclose_stage_terminal' / day / f'{stage}.json'
        terminal.write_text(json.dumps({'stage_id': stage, 'historical_only': True}))
        legacy_paths[stage] = terminal
    value['input_sources'].update(h._stage_sources(legacy_paths))
    h._stage_write(path, value)
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == [
        'summary_handoff:terminal_missing_or_invalid'
    ]  # A producer cannot reuse a v2 PASS.
    if damage == 'digest':
        value['run_id'] = 'changed-without-rehash'
        path.write_text(json.dumps(value))
    elif damage == 'retired_input_changed':
        legacy_paths['widget_policy'].write_text('{}')
    elif damage == 'retired_input_missing':
        legacy_paths['collector_recommendation'].unlink()
    elif damage == 'output':
        h.stage_artifacts(report, day, 'summary_handoff')['postclose_done_controller'].write_text('{}')
    elif damage:
        if damage == 'input_set': value['input_sources'].pop('widget_policy')
        elif damage == 'code': value['stage_code_sha256'] = 'unknown-code'
        elif damage == 'failed': value.update(status='failed', exit_code=1)
        elif damage == 'new_publication': value['publication_date'] = '2026-10-06'
        elif damage == 'invalid_publication': value['publication_date'] = '2026-10-00'
        h._stage_write(path, value)
    before = path.read_bytes()
    issues = h.stage_receipt_issues(
        report, day, 'summary_handoff', allow_historical_summary=True,
    )
    assert bool(issues) is (damage is not None), issues
    assert path.read_bytes() == before


def test_summary_handoff_reseals_verified_final_controller(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert run('summary_handoff')['status'] == 'succeeded'
    controller = h.stage_artifacts(report, day, 'summary_handoff')[
        'postclose_done_controller']
    controller.write_text(json.dumps({
        'date': day, 'status': 'done',
        'whole_native_chain_done_claimed': True,
        'final_verifier_status': 'pass',
    }))
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == [
        'summary_handoff:output_generation_changed'
    ]
    assert h.reseal_summary_handoff_for_final_controller(report, day, controller) is True
    receipt = h._load_json(h.stage_path(report, day, 'summary_handoff'))
    assert receipt['final_controller_reseal']['status'] == 'done'
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == []
    controller.write_text(json.dumps({'date': day, 'status': 'failed'}))
    with pytest.raises(ValueError, match='final_controller_not_verified'):
        h.reseal_summary_handoff_for_final_controller(report, day, controller)


def test_final_controller_reseal_preserves_receipt_when_summary_inputs_changed(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert run('summary_handoff')['status'] == 'succeeded'
    receipt_path = h.stage_path(report, day, 'summary_handoff')
    original = receipt_path.read_bytes()
    assert run('legacy_machine_report')['status'] == 'succeeded'
    controller = h.stage_artifacts(report, day, 'summary_handoff')[
        'postclose_done_controller']
    controller.write_text(json.dumps({
        'date': day, 'status': 'done',
        'whole_native_chain_done_claimed': True,
        'final_verifier_status': 'pass',
    }))
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == [
        'summary_handoff:output_generation_changed'
    ]
    with pytest.raises(ValueError, match='input_generation_changed'):
        h.reseal_summary_handoff_for_final_controller(report, day, controller)
    assert receipt_path.read_bytes() == original










def test_exact_ai_stage_keeps_off_and_failed_terminal_semantics(stage_environment):
    h, day, report, run, _produce = stage_environment
    payload = report.parent / 'ai_decision_payloads' / f'ai_decision_payloads_{day}.jsonl.gz'
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b'broken gzip')
    assert run('outcome_labels', off=True)['status'] == 'off'
    assert h.stage_receipt_issues(report, day, 'outcome_labels') == []
    assert run('outcome_labels', runner=lambda *args, **kwargs: 9)['status'] == 'failed'
    assert h.stage_receipt_issues(report, day, 'outcome_labels') == ['outcome_labels:failed']












def test_stage_lock_and_live_orphan_identity_prevent_duplicate(stage_environment):
    import fcntl, os
    h, day, report, run, produce = stage_environment
    path = h.stage_path(report, day, 'machine_attribution'); path.parent.mkdir(parents=True)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert run('machine_attribution')['reason'] == 'existing_stage_writer'
    h._stage_write(path, dict(status='running', child_pid=os.getpid(), child_start_ticks=Path('/proc/self/stat').read_text().split()[21]))
    assert run('machine_attribution')['reason'] == 'existing_child_running'


def test_stage_runner_exception_is_terminal_failure(stage_environment):
    h, day, report, run, produce = stage_environment
    def fail(*a, **kw): raise ValueError('bad_input')
    r = run('machine_attribution', runner=fail)
    assert r['status'] == 'failed' and r['issues'] == ['bad_input']
    assert run('machine_attribution')['status'] == 'succeeded'


def test_stage_publication_date_is_pinned_and_invalid_future_rejected(stage_environment):
    h, day, report, run, produce = stage_environment
    r = run('machine_attribution', publication='2026-09-21')
    assert r['source_date'] == day and r['effective_date'] == '2026-09-22'
    with pytest.raises(ValueError, match='stage_date_contract_invalid'):
        run('machine_attribution', publication='2099-01-01')


def test_late_summary_recovery_uses_source_day_prepared_session(stage_environment):
    h, day, report, run, _produce = stage_environment
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    seen = []

    def capture(_command, *, env, cwd):
        seen.append((env['POSTCLOSE_POLICY_PUBLICATION_DATE'],
                     env['POSTCLOSE_PREPARED_EFFECTIVE_DATE']))
        return _produce(_command, env=env, cwd=cwd)

    result = run('summary_handoff', publication='2026-09-23',
                 recovery=True, runner=capture)
    assert result['status'] == 'succeeded'
    assert result['publication_date'] == '2026-09-23'
    assert result['effective_date'] == _next_krx_trading_day('2026-09-23')
    assert result['prepared_effective_date'] == _next_krx_trading_day(day)
    assert seen == [('2026-09-23', _next_krx_trading_day(day))]
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == []
    h._stage_write(h.stage_path(report, day, 'summary_handoff'), {
        **result, 'prepared_effective_date': result['effective_date'],
    })
    assert h.stage_receipt_issues(report, day, 'summary_handoff') == [
        'summary_handoff:prepared_source_session_mismatch'
    ]
    with pytest.raises(ValueError, match='stage_date_contract_invalid'):
        run('summary_handoff', publication='2026-09-23', effective=_next_krx_trading_day(day))




def test_closed_capacity_failure_blocks_allocation_and_controller_then_binds_native_generation(stage_environment, monkeypatch):
    from datetime import date, datetime
    from types import SimpleNamespace
    from src.engine.monitoring import research_native_capacity_source as native
    from src.engine.automation import postclose_done_controller as controller
    from src.engine.automation import machine_research_closed_loop_refresh as refresh
    from src.engine.monitoring import research_closed_loop as loop

    h, day, report, run, produce = stage_environment
    capacity_root = report.parent / 'runtime' / 'machine_research_closed_loop'
    # A report marked complete, without its frozen native generation, is not a
    # successful capacity terminal and must not admit allocation.
    failed = run('research_capacity')
    assert failed['status'] == 'failed'
    assert 'research_capacity:native_source_invalid:' in failed['issues'][0]
    assert run('research_allocation')['status'] == 'deferred'

    monkeypatch.setattr(controller, 'DATA_DIR', report.parent)
    monkeypatch.setattr(controller, 'REPORT_DIR', report / 'postclose_done_controller')
    monkeypatch.setattr(h, 'stage_overview', lambda *args: {})
    monkeypatch.setattr(controller, 'build_runtime_approval_summary',
                        lambda *args: pytest.fail('blocked controller rebuilt summary'))
    def blocked_controller(*args, **kwargs):
        receipt = controller.build_postclose_done_controller(
            day, summary_handoff_only=True, require_independent_producers=True)
        assert receipt['status'] == 'blocked_independent_producer'
        assert 'research_capacity:failed' in receipt['blocked_reasons']
        assert receipt['final_verifier_status'] == 'not_run'
        return 1
    assert run('summary_handoff', runner=blocked_controller)['status'] == 'failed'

    captured = datetime.fromisoformat(day + 'T20:06:00+09:00')
    monkeypatch.setattr(native, 'datetime', SimpleNamespace(
        now=lambda tz: captured, fromisoformat=datetime.fromisoformat,
    ))
    adapters = dict(
        inventory=lambda token: ([], {'KRX','NXT'}, {'normalization_contract_complete': True}),
        unfilled=lambda token: ([], {'normalization_contract_complete': True,
                                     'request_succeeded': True}),
        deposit=lambda token: None,
        deposit_meta=lambda: dict(source='api_fresh', raw_amount=100000),
        capacity=lambda *args, **kwargs: dict(
            cash_only_orderable_amount=200000, cash_only_orderable_qty=10,
            cash_orderable_contract_status='valid', capacity_source_sha256='a'*64,
            capacity_contract_version=1, requested_stock_code='005930',
            error='', capacity_observed_at=captured.isoformat()),
    )
    assert native.acquire(date.fromisoformat(day), directory=capacity_root,
                          token='fixture', adapters=adapters)['status'] == 'complete'
    repaired = run('research_capacity', runner=lambda *args, **kwargs: 0)
    assert repaired['status'] == 'succeeded'
    assert repaired['run_id'] != failed['run_id']
    assert (h.stage_path(report, day, 'research_capacity').parent / 'attempts' /
            f"research_capacity_{failed['run_id']}.json").exists()
    assert set(repaired['input_sources']) == {'native_cash','native_inventory'}
    assert h.stage_receipt_issues(report, day, 'research_capacity') == []

    # Limit this fixture to capacity→allocation: widget/episode receipts are
    # separate owners, represented by stable exact-date terminal files.
    for stage in ('episode_policy',):
        path = h.stage_path(report, day, stage)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'source_date': day, 'stage_id': stage}))
    original_issues = h.stage_receipt_issues
    monkeypatch.setattr(h, 'stage_receipt_issues',
                        lambda root, source_date, stage, **kw: [] if stage in {'widget_policy','episode_policy'}
                        else original_issues(root, source_date, stage, **kw))
    monkeypatch.setattr(refresh, 'validate_current_receipt', lambda *args, **kwargs: True)
    allocation = run('research_allocation')
    assert allocation['status'] == 'succeeded'
    assert set(allocation['prerequisite_receipts']) == {
        'episode_policy', 'research_capacity'
    }
    assert allocation['prerequisite_receipts']['research_capacity']['sha256'] == (
        h._stage_sources({'capacity': h.stage_path(report, day, 'research_capacity')})['capacity']['sha256']
    )
    assert h.stage_receipt_issues(report, day, 'research_allocation') == []
    downstream = controller.build_postclose_done_controller(
        day, summary_handoff_only=True, require_independent_producers=True)
    assert downstream['status'] == 'blocked_independent_producer'
    assert not any('research_capacity:' in issue or 'research_allocation:' in issue
                   for issue in downstream['blocked_reasons'])
    assert downstream['final_verifier_status'] == 'not_run'
    cash = capacity_root / 'native_capacity' / day / 'native_cash.json'
    cash.write_text(cash.read_text() + '\n')
    assert h.stage_receipt_issues(report, day, 'research_capacity') == [
        'research_capacity:input_generation_changed'
    ]
    blocked_again = run('research_allocation')
    assert blocked_again['status'] == 'deferred'
    assert 'research_capacity:input_generation_changed' in blocked_again['issues']
    assert (h.stage_path(report, day, 'research_allocation').parent / 'attempts' /
            f"research_allocation_{allocation['run_id']}.json").exists()
    downstream = controller.build_postclose_done_controller(
        day, summary_handoff_only=True, require_independent_producers=True)
    assert 'research_capacity:input_generation_changed' in downstream['blocked_reasons']
    assert 'research_allocation:deferred' in downstream['blocked_reasons']


def test_research_capacity_explicit_off_does_not_require_native_source(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert run('research_capacity', off=True)['status'] == 'off'
    assert h.stage_receipt_issues(report, day, 'research_capacity') == []


def test_retired_episode_disables_joint_research_only_with_valid_receipt(stage_environment):
    h, day, report, run, _produce = stage_environment
    assert h._joint_research_peer_off(report, day) is False
    receipt = run('episode_policy', off=True)
    assert receipt['status'] == 'off'
    assert h._joint_research_peer_off(report, day) is True
    path = h.stage_path(report, day, 'episode_policy')
    path.write_text(path.read_text().replace(receipt['receipt_sha256'], '0' * 64))
    assert h._joint_research_peer_off(report, day) is False


def test_staged_winrate_descendant_requires_same_proof_and_machine(tmp_path):
    import json
    from types import SimpleNamespace
    from src.engine.automation import postclose_summary_handoff as h
    parent_hash = 'a' * 64
    child_hash = 'b' * 64
    proof = {'disposition': 'incumbent_carried'}
    parent = {'bundle_sha256': parent_hash, 'target_date': '2026-10-01',
              'winrate_selection': proof, 'machine_policy': {'version': 1}}
    child = {'bundle_sha256': child_hash, 'target_date': '2026-10-01',
             'previous_bundle_sha256': parent_hash,
             'winrate_selection': proof, 'machine_policy': {'version': 1}}
    generations = tmp_path / 'generations'
    generations.mkdir()
    (generations / f'{parent_hash}.json').write_text(json.dumps(parent))
    runtime = SimpleNamespace(
        root=lambda data_root: data_root,
        _read=lambda path: json.loads(path.read_text()),
        validate=lambda value, target_date: value['target_date'] == target_date or
                 (_ for _ in ()).throw(ValueError('wrong date')),
        _validate_bundle_sources=lambda value, data_root: None,
        for_cohort=lambda value, cohort: value,
    )
    staged = {'bundle_sha256': parent_hash, 'target_date': '2026-10-01'}
    assert h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path)
    child['winrate_selection'] = {'disposition': 'successor_selected'}
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path)
    child['winrate_selection'] = proof
    parent['machine_policy'] = {'version': 2}
    (generations / f'{parent_hash}.json').write_text(json.dumps(parent))
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path)


def test_winrate_generation_only_retains_seal_source_and_same_policy_checks(tmp_path):
    import hashlib
    import json
    from types import SimpleNamespace
    from src.engine.automation import postclose_summary_handoff as h
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    parent = {'target_date': '2026-10-02', 'schema': 'sealed-test',
              'machine_policy': {'version': 1}, 'winrate_selection': {'disposition': 'incumbent_carried'}}
    parent['bundle_sha256'] = digest(parent)
    child = {**parent, 'previous_bundle_sha256': parent['bundle_sha256'], 'bundle_sha256': 'b' * 64}
    path = tmp_path / 'generations' / (parent['bundle_sha256'] + '.json')
    path.parent.mkdir()
    path.write_text(json.dumps(parent))
    checked = []
    runtime = SimpleNamespace(root=lambda root: root, digest=digest,
        _read=lambda p: json.loads(p.read_text()), for_cohort=lambda value, cohort: value,
        validate=lambda *a, **kw: (_ for _ in ()).throw(AssertionError('current policy already validated')),
        _validate_bundle_sources=lambda value, root: checked.append(value['bundle_sha256']))
    staged = {'bundle_sha256': parent['bundle_sha256'], 'target_date': '2026-10-02'}
    assert h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path, generation_only=True)
    assert checked == [parent['bundle_sha256']]
    child['machine_policy'] = {'version': 2}
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path, generation_only=True)
    child['machine_policy'] = parent['machine_policy']
    runtime._validate_bundle_sources = lambda *a: (_ for _ in ()).throw(ValueError('source changed'))
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path, generation_only=True)
    parent['machine_policy'] = {'version': 3}
    path.write_text(json.dumps(parent))
    assert not h._staged_winrate_generation_preserved(staged, child, runtime, tmp_path, generation_only=True)


def test_family_source_read_does_not_require_peer(tmp_path, monkeypatch):
    from datetime import date
    from src.engine.automation import machine_research_closed_loop_refresh as phase
    from src.engine.monitoring import research_closed_loop as loop
    seen=[]
    def read(path):
        seen.append(path)
        return dict(target_date='2026-09-21', closed_loop_contract=loop.SCHEMA, **loop.AUTHORITY)
    monkeypatch.setattr(phase, '_read_report_dependency', read)
    studies, paths, missing = phase.read_studies(date(2026,9,21), report_root=tmp_path, families=('episode',))
    assert not missing and set(studies) == {'episode'} and len(seen) == 1




def test_policy_readiness_is_separate_from_failed_diagnostic(stage_environment, monkeypatch):
    h, day, report, run, produce = stage_environment
    from src.engine.scalping import mechanistic_entry_runtime_policy as main
    from src.engine.automation import low_price_two_leg_auto_expansion_policy as episode
    bootstrap=report.parent/'runtime'/'policy_bootstrap'/'runtime_policy_bootstrap_verify_2026-09-22.json'
    bootstrap.parent.mkdir(parents=True); bootstrap.write_text(json.dumps(dict(passed=True, target_date='2026-09-22', status='pass')))
    from src.engine.automation import runtime_policy_bootstrap as bootstrap_owner
    monkeypatch.setattr(bootstrap_owner, 'manifest_path', lambda *a: bootstrap.parent/'manifest.json')
    monkeypatch.setattr(bootstrap_owner, 'verify_bootstrap', lambda *a, **kw: {'passed':True})
    monkeypatch.setattr(main, 'load_effective', lambda **kw: {'valid':True})
    monkeypatch.setattr(episode, 'load_policy', lambda *a, **kw: {'valid':True})
    run('market_weakness', runner=lambda *a, **kw: 1)
    view=h.stage_overview(report, day)
    assert not view['postclose_all_active_stages_complete']
    assert view['next_session_policy_ready']
    view=h.stage_overview(report, day)
    assert view['next_session_policy_ready']
    monkeypatch.setattr(bootstrap_owner, 'verify_bootstrap', lambda *a, **kw: {'passed':False})
    assert not h.stage_overview(report, day)['next_session_policy_ready']
    monkeypatch.setattr(bootstrap_owner, 'verify_bootstrap', lambda *a, **kw: {'passed':True})
    monkeypatch.setattr(main, 'load_effective', lambda **kw: None)
    assert not h.stage_overview(report, day)['next_session_policy_ready']


def test_verified_off_episode_and_isolated_preparation_are_startup_ready(stage_environment, monkeypatch):
    h, day, report, run, _ = stage_environment
    from src.engine.automation import next_preopen_readiness as readiness
    from src.engine.automation import low_price_two_leg_auto_expansion_policy as episode
    from src.engine.scalping import mechanistic_entry_runtime_policy as main
    run('episode_policy', off=True)
    monkeypatch.setattr(episode, 'load_policy', lambda *a, **kw: None)
    monkeypatch.setattr(main, 'load_effective', lambda **kw: {'valid': True})
    root = report.parent/'runtime'/'policy_bootstrap'/'prepared'/'2026-09-22'
    root.mkdir(parents=True)
    receipt = root/'generation'/'readiness.json';receipt.parent.mkdir()
    receipt.write_text(json.dumps({'source_date': day}))
    (root/'latest.json').write_text(json.dumps({'receipt_path': str(receipt)}))
    monkeypatch.setattr(readiness, 'verify_prepared', lambda *a, **kw: {'status': 'pass'})
    view = h.stage_overview(report, day)
    assert view['next_session_policy_ready']
    assert view['episode_policy_authority'] == 'explicit_schedule_disabled'
    assert view['startup_basis'] == 'isolated_prepared_next_preopen'
    assert view['day_of_activation_required'] and not view['actual_pid_consumed']
    receipt.write_text(json.dumps({'source_date': '2026-09-20'}))
    assert not h.stage_overview(report, day)['next_session_policy_ready']
    receipt.write_text(json.dumps({'source_date': day}))
    monkeypatch.setattr(readiness, 'verify_prepared', lambda *a, **kw: {'status': 'fail'})
    assert not h.stage_overview(report, day)['next_session_policy_ready']
    monkeypatch.setattr(readiness, 'verify_prepared', lambda *a, **kw: {'status': 'pass'})
    monkeypatch.setattr(main, 'load_effective', lambda **kw: None)
    assert not h.stage_overview(report, day)['next_session_policy_ready']


def test_stage_machine_rejects_sealed_but_unbound_terminal(stage_environment):
    h, day, report, run, produce = stage_environment
    from src.engine.scalping.ai_action_outcome_calibration import _with_artifact_content_sha256
    assert run('main_machine_policy')['status']=='succeeded'
    path=h.stage_artifacts(report, day, 'main_machine_policy')['machine_policy_terminal']
    value=json.loads(path.read_text()); value['report_sha256']='wrong'
    path.write_text(json.dumps(_with_artifact_content_sha256(value)))
    assert 'main_machine_policy:report_terminal_binding_invalid' in h._stage_output_issues(report, day, 'main_machine_policy')


def test_existing_winrate_carry_binding_requires_same_parent_and_policy(tmp_path):
    from pathlib import Path

    from src.engine.automation.postclose_summary_handoff import (
        _existing_incumbent_winrate_binding_valid,
    )
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy

    machine = {'strategy': 'mechanistic_entry', 'thresholds': {'fixed': 1}}
    previous = {'bundle_sha256': 'a' * 64, 'machine_policy': machine}
    report = {
        'artifact_content_sha256': 'b' * 64,
        'publication_date': '2026-09-24',
        'parent_bundle_sha256': previous['bundle_sha256'],
        'parent_machine_policy_sha256': policy.digest(machine),
        'policy_version': 'winrate_initial_v1',
        'disposition': 'incumbent_carried',
        'candidate_policy': None,
    }
    bundle = {
        'bundle_sha256': 'c' * 64,
        'previous_bundle_sha256': 'f' * 64,
        'machine_policy': machine,
        'winrate_selection': {
            'report_sha256': 'd' * 64,
            'disposition': 'incumbent_carried',
            'policy_version': 'winrate_initial_v1',
            'parent_bundle_sha256': previous['bundle_sha256'],
            'machine_policy_sha256': policy.digest(machine),
        },
    }
    proof = bundle['winrate_selection']
    staged = {
        'bundle_sha256': bundle['bundle_sha256'],
        'current_report_sha256': report['artifact_content_sha256'],
        'bundle_report_sha256': bundle['winrate_selection']['report_sha256'],
        'previous_bundle_sha256': previous['bundle_sha256'],
        'machine_policy_sha256': policy.digest(machine),
    }

    assert _existing_incumbent_winrate_binding_valid(
        report, staged, bundle, previous, policy
    )
    preserving_child = {
        **bundle,
        'bundle_sha256': 'e' * 64,
        'previous_bundle_sha256': bundle['bundle_sha256'],
    }
    assert _existing_incumbent_winrate_binding_valid(
        report, {**staged, 'target_date': '2026-09-25'},
        preserving_child, previous, policy, staged_bundle={
            **bundle, 'target_date': '2026-09-25',
        }
    )
    changed_child = dict(preserving_child, winrate_selection={
        **bundle['winrate_selection'], 'report_sha256': 'f' * 64,
    })
    assert not _existing_incumbent_winrate_binding_valid(
        report, {**staged, 'target_date': '2026-09-25'},
        changed_child, previous, policy, staged_bundle={
            **bundle, 'target_date': '2026-09-25',
        }
    )

    staged_generation = {
        **bundle, 'target_date': '2026-09-25', 'bundle_sha256': 'c' * 64,
    }
    middle_generation = {
        **staged_generation, 'bundle_sha256': 'e' * 64,
        'previous_bundle_sha256': staged_generation['bundle_sha256'],
    }
    current_generation = {
        **middle_generation, 'bundle_sha256': 'f' * 64,
        'previous_bundle_sha256': middle_generation['bundle_sha256'],
    }
    policy_root = tmp_path / 'mechanistic_entry_policy'
    generations = policy_root / 'generations'
    generations.mkdir(parents=True)
    for generation in (staged_generation, middle_generation):
        (generations / f"{generation['bundle_sha256']}.json").write_text(
            json.dumps(generation)
        )
    fake_policy = type('Policy', (), {})()
    fake_policy.root = lambda _root: policy_root
    fake_policy._read = lambda path: json.loads(Path(path).read_text())
    def validate_generation(value, target_date):
        if value.get('target_date') != target_date:
            raise ValueError('target_date_mismatch')
    fake_policy.validate = validate_generation
    fake_policy._validate_bundle_sources = lambda *_args: None
    fake_policy.for_cohort = lambda value, _scope: {'machine_policy': value['machine_policy']}
    fake_policy.digest = policy.digest
    assert _existing_incumbent_winrate_binding_valid(
        report, {**staged, 'bundle_sha256': staged_generation['bundle_sha256'],
                 'target_date': '2026-09-25'},
        current_generation, previous, fake_policy,
        data_root=tmp_path,
    )
    changed_middle = dict(middle_generation, winrate_selection={
        **proof, 'report_sha256': 'f' * 64,
    })
    (generations / f"{middle_generation['bundle_sha256']}.json").write_text(
        json.dumps(changed_middle)
    )
    assert not _existing_incumbent_winrate_binding_valid(
        report, {**staged, 'bundle_sha256': staged_generation['bundle_sha256'],
                 'target_date': '2026-09-25'},
        current_generation, previous, fake_policy,
        data_root=tmp_path,
    )
    changed = dict(report, candidate_policy={'threshold': 'different'})
    assert not _existing_incumbent_winrate_binding_valid(
        changed, staged, bundle, previous, policy
    )
    changed_previous = dict(previous, bundle_sha256='e' * 64)
    assert not _existing_incumbent_winrate_binding_valid(
        report, staged, bundle, changed_previous, policy
    )
    changed_machine = dict(bundle, machine_policy={'strategy': 'other'})
    assert not _existing_incumbent_winrate_binding_valid(
        report, staged, changed_machine, previous, policy
    )


def test_family_publication_validation_uses_bounded_64_mib_read(tmp_path, monkeypatch):
    from src.engine.monitoring import research_closed_loop as loop

    day = '2026-09-21'
    report_dir = tmp_path / 'data' / 'report'
    paths = mod.stage_artifacts(report_dir, day, 'episode_policy')
    source = paths['low_price_two_leg_expanded_candidate_research']
    policy = tmp_path / 'data' / 'runtime' / 'low_price_two_leg_auto_expansion' / 'policy.json'
    source.parent.mkdir(parents=True)
    policy.parent.mkdir(parents=True)
    source_payload = {'end_date': day, 'status': 'complete'}
    policy_payload = {'effective_date': '2026-09-22', 'runtime_effect': False}
    source.write_text(json.dumps(source_payload), encoding='utf-8')
    policy.write_text(json.dumps(policy_payload), encoding='utf-8')
    refresh = paths['episode_policy_refresh']
    refresh.parent.mkdir(parents=True)
    from src.engine.monitoring.research_closed_loop import digest
    value = {
        'source_date': day,
        'source_path': str(source),
        'source_sha256': digest(source_payload),
        'policy_path': str(policy),
        'policy_sha256': digest(policy_payload),
        'status': 'complete',
    }
    value['receipt_sha256'] = digest(value)
    refresh.write_text(json.dumps(value), encoding='utf-8')

    calls = []
    original = loop.read_object
    def bounded(path, *, limit=0):
        calls.append(limit)
        return original(path, limit=limit)
    monkeypatch.setattr(loop, 'read_object', bounded)

    assert mod._stage_output_issues(report_dir, day, 'episode_policy') == []
    assert calls == [64 * 1024 * 1024, 64 * 1024 * 1024]


def test_label_ready_time_uses_kst_instant(stage_environment):
    h, day, report, run, produce = stage_environment
    produce(['fixture', 'outcome_labels'])
    path=h.stage_artifacts(report, day, 'outcome_labels')['ai_decision_outcome_labels']
    value=json.loads(path.read_text()); value['generated_at']=day+'T12:00:00+00:00'
    path.write_text(json.dumps(value))
    assert run('outcome_labels', execute=False)['status']=='succeeded'
    value['generated_at']=day+'T10:00:00+00:00'; path.write_text(json.dumps(value))
    assert run('outcome_labels', execute=False)['status']=='failed'


def test_launch_rejects_invalid_date_before_fork(monkeypatch):
    from src.engine.automation import postclose_summary_handoff as h
    monkeypatch.setattr(h.subprocess, 'Popen', lambda *a, **kw: pytest.fail('must not launch'))
    with pytest.raises(SystemExit):
        h._stage_main(['--stage','main_machine_policy','--date','2099-01-01','--launch'])


def test_pre_submit_delay_stage_command_resolves_next_session_effective_date():
    from src.engine.automation import postclose_summary_handoff as h

    command = h.stage_commands('pre_submit_delay', '2026-09-23', '2026-09-23')[0]

    assert command[-5:] == ['--date', '2026-09-23', '--effective-date', '2026-09-28',
                            '--require-family-ledger']


def test_machine_strategy_refresh_runs_before_auxiliary_ai():
    from src.engine.automation import postclose_summary_handoff as h
    command = h.stage_commands('legacy_machine_report', '2026-09-30', '2026-09-30')[0]
    assert '--machine-only' in command and '--activate-now' in command
    assert 'legacy_machine_report' in h.STAGE_REGISTRY['main_auxiliary_policy'][0]


def test_market_weakness_waits_for_its_attribution_source(stage_environment):
    h, _, _, _, _ = stage_environment

    assert h.STAGE_REGISTRY['market_weakness'][0] == ('machine_attribution',)


def test_unchanged_stage_accepts_exact_selected_release_code_hash(stage_environment, monkeypatch, tmp_path):
    h, day, report, run, _ = stage_environment
    run('machine_attribution')

    managed = tmp_path / 'KORStockScan-runtime-releases'
    release = managed / 'immutable-release'
    previous = managed / 'previous-release'
    for root in (release, previous):
        (root / '.git').mkdir(parents=True)
        dispatcher = root / 'src/engine/automation/postclose_summary_handoff.py'
        dispatcher.parent.mkdir(parents=True)
        dispatcher.write_text('# pinned release dispatcher\n')
    selection = report.parent / 'runtime' / 'runtime_release_selection.json'
    selection.parent.mkdir(parents=True, exist_ok=True)
    selection.write_text(json.dumps({
        'schema': 'runtime_release_selection_v1',
        'release_root': str(release),
        'git_commit': 'a' * 40,
    }))

    def code_hash(stage, commands, project, *, dispatcher_path=None):
        if dispatcher_path is None:
            return 'repaired-code'
        return 'previous-release-code' if project.name == 'previous-release' else 'selected-release-code'

    monkeypatch.setattr(h, '_stage_code', code_hash)
    path = h.stage_path(report, day, 'machine_attribution')
    terminal = h._load_json(path)
    terminal['stage_code_sha256'] = 'previous-release-code'
    h._stage_write(path, terminal)

    assert h.stage_receipt_issues(report, day, 'machine_attribution', code_hash='repaired-code') == []


def test_stage_stop_cleans_child_and_preserves_checkpoint(stage_environment, monkeypatch, tmp_path):
    import sys, threading
    h, day, report, run, produce = stage_environment
    checkpoint=tmp_path/'saved-checkpoint'
    command=[sys.executable, '-c', 'import pathlib,time; pathlib.Path('+repr(str(checkpoint))+').write_text("saved"); time.sleep(30)']
    monkeypatch.setattr(h, 'stage_commands', lambda *a, **kw: [command])
    stop=threading.Event(); timer=threading.Timer(1, stop.set); timer.start()
    try:
        result=h.run_stage('machine_attribution', day, report_dir=report, project=tmp_path, stop_event=stop, timeout=10)
    finally:
        timer.cancel()
    assert result['status']=='failed' and checkpoint.read_text()=='saved'
    assert not Path('/proc/'+str(result['child_pid'])).exists()


def test_summary_receipt_does_not_hash_itself(stage_environment):
    h, day, report, run, produce = stage_environment
    run('machine_attribution')
    paths=h.source_paths(report, day, 'checklist')
    assert h.stage_path(report, day, 'machine_attribution') in paths.values()
    assert h.stage_path(report, day, 'summary_handoff') not in paths.values()
    assert h.stage_artifacts(report, day, 'summary_handoff')['postclose_done_controller'] not in paths.values()
    assert 'stage_pre_submit_delay' not in paths
    assert 'pre_submit_delay' not in h.stage_overview(report, day)['stages']


@pytest.mark.parametrize('status', ['pending', 'running', 'deferred'])
def test_scheduled_stage_check_reports_pending_as_deferred(stage_environment, monkeypatch, status):
    h, day, report, run, produce=stage_environment
    from src.utils import constants
    monkeypatch.setattr(constants, 'DATA_DIR', report.parent)
    h._stage_write(h.stage_path(report, day, 'main_auxiliary_policy'), {'status':status})
    assert h._stage_main(['--stage','main_auxiliary_policy','--date',day,'--check'])==75


@pytest.mark.parametrize('stage,recovery,expected', [
    ('main_auxiliary_policy', True, 123), ('main_auxiliary_policy', False, 123),
    ('machine_timing', True, 0), ('machine_timing', False, 123),
])
def test_compact_recovery_keeps_bounded_prerequisite_wait(monkeypatch, stage, recovery, expected):
    import signal
    from src.engine.automation import postclose_summary_handoff as h
    seen=[]
    monkeypatch.setattr(signal, 'signal', lambda *a: None)
    def run(s, *a, **kw):
        seen.append(kw)
        return dict(stage_id=s, status='succeeded', exit_code=0)
    monkeypatch.setattr(h,'run_stage',run)
    args=['--stage',stage,'--date','2026-09-28','--timeout-sec','123']
    if recovery: args.append('--recover-closed-target')
    assert h._stage_main(args)==0
    assert seen[0]['prerequisite_wait']==expected
    assert seen[0]['recovery'] is recovery


def test_compact_wait_does_not_hide_terminal_failed_peer(stage_environment, monkeypatch):
    import time
    h,day,report,run,_produce=stage_environment
    h._stage_write(h.stage_path(report,day,'outcome_labels'), {'status':'failed'})
    h._stage_write(h.stage_path(report,day,'legacy_machine_report'), {'status':'running'})
    monkeypatch.setattr(h,'stage_receipt_issues',lambda _report,_day,s,**kw:[s+':blocked'])
    monkeypatch.setattr(time,'sleep',lambda _: pytest.fail('terminal failure must not wait'))
    result=run('main_auxiliary_policy',prerequisite_wait=123)
    assert result['status']=='deferred' and result['exit_code']==75
    assert 'outcome_labels:blocked' in result['issues']




@pytest.mark.parametrize("independent", ['research_capacity'])
def test_main_generation_wait_includes_independent_producers(monkeypatch, independent):
    import time
    from src.engine.automation import postclose_summary_handoff as h
    finished = False
    sleeps = []
    def load(path):
        # The summary consumer cannot block its own predecessor generation.
        if path.stem == 'summary_handoff':
            return {'status': 'running'}
        return {'status': 'running' if path.stem == independent and not finished else 'succeeded'}
    def sleep(seconds):
        nonlocal finished
        sleeps.append(seconds)
        finished = True
    monkeypatch.setattr(h, '_load_json', load)
    monkeypatch.setattr(time, 'sleep', sleep)
    monkeypatch.setattr(h, 'run_stage', lambda *a, **kw: pytest.fail('wait cannot launch a producer'))
    assert h._stage_main(['--stage', 'wait', '--date', '2026-09-21']) == 0
    assert sleeps == [1]


def test_main_generation_wait_preserves_existing_timeout(monkeypatch):
    import time
    from src.engine.automation import postclose_summary_handoff as h
    ticks = iter([0.0, 2.0])
    monkeypatch.setattr(time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(time, 'sleep', lambda *a: pytest.fail('deadline already elapsed'))
    monkeypatch.setattr(h, '_load_json', lambda p: {'status': 'running' if p.stem == 'research_capacity' else 'succeeded'})
    assert h._stage_main(['--stage', 'wait', '--date', '2026-09-21', '--timeout-sec', '1']) == 75
