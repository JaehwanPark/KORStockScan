import json

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
    for label in handoff.INDEPENDENT_SOURCES["widget"]:
        path = paths[label]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"target_date": day}))
    assert handoff._producer_main(["--owner", "widget", "--date", day, "--phase", "started"]) == 0
    assert handoff.producer_receipt_issues(data / "report", day, "widget")
    assert handoff._producer_main(["--owner", "widget", "--date", day, "--phase", "finished"]) == 0
    assert handoff.producer_receipt_issues(data / "report", day, "widget") == []
    paths[handoff.INDEPENDENT_SOURCES["widget"][0]].write_text("{}")
    assert handoff.producer_receipt_issues(data / "report", day, "widget")
    old = handoff.producer_receipt_path(data / "report", day, "widget").read_bytes()
    assert handoff._producer_main(["--owner", "widget", "--date", day, "--phase", "started"]) == 0
    assert any(p.read_bytes() == old for p in (data / "report/postclose_producer_terminal/attempts").glob("*.json"))
    assert handoff._producer_main(["--owner", "widget", "--date", day, "--phase", "finished", "--exit-code", "17"]) == 1


def test_widget_prefix_reuse_rejects_drift_and_preserves_origin(monkeypatch, tmp_path):
    from src.engine.automation.postclose_recommendation_intake import source_paths
    from src.utils import constants
    monkeypatch.setattr(constants, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(constants, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(mod.subprocess, "check_output", lambda args, **kw: "src/engine/monitoring/machine_candidate_lifecycle.py\nsrc/engine/automation/machine_research_closed_loop_refresh.py" if "diff" in args else "a" * 40)
    day="2026-09-17"
    paths=source_paths(tmp_path / "data/report", day)
    for label in mod.INDEPENDENT_SOURCES["widget"][:2]:
        path=paths[label]; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"target_date":day}))
    cli=["--owner","widget","--date",day]
    mod._producer_main(cli+["--phase","started"])
    assert mod._producer_main(cli+["--phase","finished","--exit-code","1"]) == 1
    old=mod._load_json(mod.producer_receipt_path(tmp_path / "data/report",day,"widget"))
    mod._producer_main(cli+["--phase","started","--reuse-widget-prefix"])
    new=mod._load_json(mod.producer_receipt_path(tmp_path / "data/report",day,"widget"))
    assert new["reused_prefix"]["run_id"]==old["run_id"] and new["run_id"]!=old["run_id"]
    mod._producer_main(cli+["--phase","finished","--exit-code","1"])
    paths[mod.INDEPENDENT_SOURCES["widget"][0]].write_text("{}")
    with pytest.raises(RuntimeError, match="source_generation_mismatch"):
        mod._producer_main(cli+["--phase","started","--reuse-widget-prefix"])


@pytest.mark.parametrize("interrupted", [False, True])
def test_machine_refresh_binds_widget_generation_without_rewriting_original_run(monkeypatch, tmp_path, interrupted):
    def _write(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
    from src.utils import constants
    from src.engine.automation import machine_research_closed_loop_refresh as phase
    from src.engine.automation.postclose_recommendation_intake import source_paths
    data = tmp_path / 'data'
    monkeypatch.setattr(constants, 'DATA_DIR', data)
    monkeypatch.setattr(constants, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(mod.subprocess, 'check_output', lambda *a, **k: 'a' * 40)
    # Native economic/publication reconstruction has its separate closed-loop E2E.
    monkeypatch.setattr(phase, 'validate_current_receipt', lambda v, day: v.get('native_current') is True)
    day = '2026-09-17'
    reports = data / 'report'
    paths = source_paths(reports, day)
    for label in set(mod.INDEPENDENT_SOURCES['widget'] + mod.INDEPENDENT_SOURCES['machine']):
        path = paths.get(label, reports / label / f'{label}_{day}.json')
        _write(path, dict(target_date=day, native_current=True))
    def run(owner, stage):
        return mod._producer_main(['--owner', owner, '--date', day, '--phase', stage])
    assert run('widget', 'started') == 0 and run('widget', 'finished') == 0
    original = mod.producer_receipt_path(reports, day, 'widget').read_bytes()
    assert run('machine', 'started') == 0
    path = paths['widget_symbol_signal_policy_research']
    _write(path, dict(target_date=day, enriched=True))
    _write(paths['widget_symbol_runtime_policy_apply'], dict(target_date=day, enriched=True))
    assert mod.producer_receipt_issues(reports, day, 'widget')
    if interrupted:
        assert mod._producer_main(['--owner', 'machine', '--date', day, '--phase', 'finished', '--exit-code', '1']) == 1
        assert mod.producer_receipt_issues(reports, day, 'machine')
        closure = reports / 'machine_research_closed_loop' / f'machine_research_closed_loop_{day}.json'
        _write(closure, dict(target_date=day, native_current=False))
        with pytest.raises(RuntimeError, match='upstream_widget_terminal_invalid'):
            run('machine', 'started')
        _write(closure, dict(target_date=day, native_current=True))
        advisory = paths['widget_advisory_calibration']
        original_advisory = advisory.read_bytes()
        _write(advisory, dict(target_date=day, illegal_change=True))
        with pytest.raises(RuntimeError, match='upstream_widget_terminal_invalid'):
            run('machine', 'started')
        advisory.write_bytes(original_advisory)
        assert run('machine', 'started') == 0
        assert mod.producer_receipt_issues(reports, day, 'widget')
    assert run('machine', 'finished') == 0
    assert mod.producer_receipt_issues(reports, day, 'widget') == []
    assert mod.producer_receipt_path(reports, day, 'widget').read_bytes() == original
    _write(path, dict(target_date=day, unexpected_later_generation=True))
    assert mod.producer_receipt_issues(reports, day, 'widget')
