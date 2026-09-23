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
    # A stopped wrapper may retain only its started receipt and inherited prefix.
    mod._producer_main(cli+["--phase","started","--reuse-widget-prefix"])
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


@pytest.mark.parametrize("terminal,exit_code", [("failed", 1), ("succeeded", 0)])
def test_failed_refresh_can_rebuild_after_unrelated_dependency_changed(tmp_path, monkeypatch, terminal, exit_code):
    from src.engine.monitoring import research_closed_loop as loop
    from src.engine.automation import machine_research_closed_loop_refresh as refresh
    from src.engine.verify_threshold_cycle_postclose_chain import _sha
    from datetime import date
    day = '2026-09-21'
    widget = mod.producer_receipt_path(tmp_path, day, 'widget')
    widget.parent.mkdir(parents=True)
    study = tmp_path / 'study.json'
    study.write_text('{"target_date":"2026-09-21"}')
    sources = {'widget_symbol_signal_policy_research': {'path': str(study)}}
    widget.write_text(json.dumps({'sources': sources}))
    effective = date(2026, 9, 22)
    publication = tmp_path / 'policies'
    manifest = loop.publication_transaction(publication, effective_date=effective, files={'policy.json': {}})
    closure = {'schema': loop.SCHEMA, 'target_date': day, 'status': 'complete',
        'publications': {'widget': {'directory': str(publication), 'effective_date': str(effective), 'generation_sha256': manifest['generation_sha256']}},
        'dependency_sources': {str(study): loop.digest(json.loads(study.read_text()))}}
    closure['receipt_sha256'] = loop.digest(closure)
    path = tmp_path / 'machine_research_closed_loop' / f'machine_research_closed_loop_{day}.json'
    path.parent.mkdir()
    path.write_text(json.dumps(closure))
    previous = {'status': terminal, 'owner': 'machine', 'target_date': day, 'run_id': 'run', 'exit_code': exit_code, 'code_commit': 'a' * 40,
        'upstream_widget': {'sha256': _sha(widget), 'sources': sources}}
    monkeypatch.setattr(refresh, 'validate_current_receipt', lambda *args: False)
    issues = ['widget:source_hash_invalid:widget_symbol_signal_policy_research']
    assert mod._verified_machine_refresh_retry(tmp_path, day, previous, issues)
    (publication / 'policy.json').write_text('{"tampered": true}')
    assert not mod._verified_machine_refresh_retry(tmp_path, day, previous, issues)
    (publication / 'policy.json').write_text('{}')
    bad = dict(closure, receipt_sha256='f' * 64)
    path.write_text(json.dumps(bad))
    assert not mod._verified_machine_refresh_retry(tmp_path, day, previous, issues)
    path.write_text(json.dumps(closure))
    study.write_text('{"target_date":"2026-09-20"}')
    assert not mod._verified_machine_refresh_retry(tmp_path, day, previous, issues)
    assert not mod._verified_machine_refresh_retry(tmp_path, day, previous, ['widget:source_hash_invalid:widget_advisory_calibration'])


def test_widget_state_dependency_ignores_heartbeat_but_binds_order_facts(tmp_path):
    from copy import deepcopy
    from datetime import date
    from src.engine.automation import machine_research_closed_loop_refresh as refresh
    from src.engine.monitoring.research_version_outcomes import native_widget_rows
    day = date(2026, 9, 21)
    path = tmp_path / 'widget_signal_auto_trade_state.json'
    order = dict(order_no='order-1', order_date=str(day), side='BUY', filled_qty=0,
                 requested_qty=1, remaining_qty=1, status='OPEN', signal_id='signal',
                 execution_policy_content_sha256='a' * 64)
    state = dict(active_date=str(day), symbols={'005930': {'orders': [order]}},
                 history=[], last_cycle_at='first', enabled_symbols=['005930'])
    path.write_text(json.dumps(state))
    first = refresh._read_report_dependency(path, source_date=day)
    original_rows = native_widget_rows(state, source_date=day)
    rollover = dict(active_date='2026-09-22', symbols={'000001': {'orders': []}},
                    history=[dict(trade_date=str(day), symbols=state['symbols'])],
                    last_cycle_at='later', enabled_symbols=['000001'])
    path.write_text(json.dumps(rollover))
    assert refresh._read_report_dependency(path, source_date=day) == first
    assert native_widget_rows(rollover, source_date=day) == original_rows
    changed = deepcopy(rollover)
    changed['history'][0]['symbols']['005930']['orders'][0]['filled_qty'] = 1
    path.write_text(json.dumps(changed))
    assert refresh._read_report_dependency(path, source_date=day) != first
    with pytest.raises(ValueError, match='dependency_date_required'):
        refresh._read_report_dependency(path)


@pytest.fixture
def stage_environment(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as h
    monkeypatch.setattr(h, '_stage_code', lambda *a: 'code-v2')
    monkeypatch.setattr(h, 'stage_commands', lambda stage, *a, **kw: [['fixture', stage]])
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_EVALUATION_WAIT_FOR_EOD', 'false')
    day = '2026-09-21'; report = tmp_path / 'data' / 'report'
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
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
        return 0
    def run(stage, **kwargs):
        return h.run_stage(stage, day, report_dir=report, project=tmp_path,
            runner=kwargs.pop('runner', produce), **kwargs)
    return h, day, report, run, produce


def test_widget_eod_wait_does_not_acquire_compute_slot(stage_environment, monkeypatch):
    h, day, report, run, produce = stage_environment
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_EVALUATION_WAIT_FOR_EOD', 'true')
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_EVALUATION_EOD_WAIT_SEC', '0')
    deferred = run('widget_policy', runner=lambda *a, **kw: pytest.fail('source is not ready'))
    assert deferred['status'] == 'deferred'
    assert deferred['reason'] == 'waiting_for_source'
    assert not (report.parent / 'runtime' / 'postclose_stage_slots').exists()

    status = report.parent / 'runtime' / 'update_kospi_status' / f'update_kospi_{day}.json'
    status.parent.mkdir(parents=True)
    status.write_text(json.dumps({'status':'completed', 'target_date':day,
        'db_state':{'latest_quote_date':day, 'rows_on_latest_date':2}}))
    assert h._widget_eod_state(report, day) == 'ready'
    status.write_text(json.dumps({'status':'completed', 'target_date':day,
        'db_state':{'latest_quote_date':'2026-09-20', 'rows_on_latest_date':2}}))
    assert h._widget_eod_state(report, day) == 'invalid'


@pytest.mark.parametrize("failed_stage", ["market_weakness", "main_auxiliary_policy", "widget_policy", "episode_policy", "summary_handoff"])
def test_stage_failure_does_not_cancel_independent_machine(stage_environment, failed_stage):
    h, day, report, run, produce = stage_environment
    if failed_stage == 'main_auxiliary_policy': run('outcome_labels')
    failed = run(failed_stage, runner=lambda *a, **kw: 9)
    machine = run('main_machine_policy')
    assert failed['status'] == 'failed'
    assert machine['status'] == 'succeeded'
    assert not h.stage_receipt_issues(report, day, 'main_machine_policy')
    assert h.stage_receipt_issues(report, day, 'main_machine_policy', code_hash='new-code') == ['main_machine_policy:code_changed']


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


def test_committed_label_intake_binds_payload_and_rejects_partial_file(stage_environment):
    h, day, report, run, produce = stage_environment
    payload = report.parent / 'ai_decision_payloads' / f'ai_decision_payloads_{day}.jsonl'
    payload.parent.mkdir(parents=True); payload.write_text('{}\n')
    produce(['fixture', 'outcome_labels'])
    first = run('outcome_labels', execute=False)
    assert first['execution_mode'] == 'existing_output_validation'
    assert run('outcome_labels', execute=False)['cache_reused']
    assert run('collector_recommendation')['status'] == 'succeeded'
    payload.write_text('{"changed":true}\n')
    assert h.stage_receipt_issues(report, day, 'outcome_labels') == ['outcome_labels:input_generation_changed']
    label = h.stage_artifacts(report, day, 'outcome_labels')['ai_decision_outcome_labels']
    label.write_text('{')
    assert run('outcome_labels', execute=False)['status'] == 'failed'
    assert run('collector_recommendation')['status'] == 'deferred'


def test_stage_detects_input_change_during_collector(stage_environment):
    h, day, report, run, produce = stage_environment
    assert run('outcome_labels')['status'] == 'succeeded'
    def mutate(command, **kwargs):
        result = produce(command, **kwargs)
        p = h.stage_artifacts(report, day, 'outcome_labels')['ai_decision_outcome_labels']
        p.write_text(p.read_text()+'\n')
        return result
    result = run('collector_recommendation', runner=mutate)
    assert result['status'] == 'failed'
    assert 'input_changed_during_consumption' in result['issues']


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


def test_stage_group_attempts_every_independent_owner_after_failure(monkeypatch):
    from src.engine.automation import postclose_summary_handoff as h
    seen = []
    def run(stage, *a, **kw):
        seen.append(stage)
        return dict(stage_id=stage, status='failed' if stage=='collector_recommendation' else 'succeeded', exit_code=1 if stage=='collector_recommendation' else 0)
    monkeypatch.setattr(h, 'run_stage', run)
    assert h._stage_main(['--stage','machine_group','--date','2026-09-21']) == 1
    assert set(seen) == set(h.STAGE_OWNER_GROUPS['machine'][:6]) | {'summary_handoff','research_capacity'}


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


def test_allocation_stage_does_not_rewrite_family_studies_or_policies(tmp_path, monkeypatch):
    from datetime import date
    from src.engine.automation import machine_research_closed_loop_refresh as phase
    from src.engine.monitoring import research_closed_loop as loop
    from src.engine.monitoring import widget_symbol_signal_policy_research as widget
    from src.engine.monitoring import low_price_two_leg_expanded_candidate_research as episode
    from src.tests.test_widget_symbol_runtime_policy import _research
    day=date(2026,9,17); root=tmp_path/'report'; directory=tmp_path/'runtime'/'machine_research_closed_loop'
    monkeypatch.setattr(phase, 'DATA_DIR', tmp_path/'data')
    monkeypatch.delenv('POSTCLOSE_POLICY_PUBLICATION_DATE', raising=False)
    monkeypatch.delenv('POSTCLOSE_PREPARED_EFFECTIVE_DATE', raising=False)
    report=_research(); report.update(end_date=str(day), closed_loop_contract=loop.SCHEMA)
    for r in report['symbols'].values():
        r.pop('selected_policy', None); r.update(name='fixture', decision='hold_sample_insufficient_signal')
    peer=dict(schema=episode.REPORT_SCHEMA, target_date=str(day), end_date=str(day), start_date='2026-06-05',
        status='no_qualified_candidate', profiles={}, recommendations=[], postclose_logic_recommendations=[],
        recommendation_count=0, trading_date_count=72, calibration_trading_day_count=56, holdout_trading_day_count=16,
        closed_loop_contract=loop.SCHEMA, **loop.AUTHORITY)
    with loop.research_scope(directory):
        widget.write_report(report, output_dir=root/'widget_symbol_signal_policy_research')
        episode.write_report(peer, root/'low_price_two_leg_expanded_candidate_research')
    _, paths, missing=phase.read_studies(day, report_root=root)
    assert not missing
    before={k:p.read_bytes() for k,p in paths.items()}
    result=phase.refresh(day, directory=directory, report_root=root, publish=False, allocation_only=True)
    assert result['status']=='complete' and result['allocation_only']
    assert phase.validate_current_receipt(result, day)
    assert result['publications']=={}
    assert {k:p.read_bytes() for k,p in paths.items()}==before
    assert not (directory.parent/'widget_symbol_runtime_policy').exists()
    assert not (directory.parent/'low_price_two_leg_auto_expansion').exists()


def test_policy_readiness_is_separate_from_failed_diagnostic(stage_environment, monkeypatch):
    h, day, report, run, produce = stage_environment
    from src.engine.scalping import mechanistic_entry_runtime_policy as main
    from src.engine.automation import low_price_two_leg_auto_expansion_policy as episode
    from src.engine.monitoring.widget_symbol_runtime_policy import WidgetSymbolRuntimePolicyLoader
    bootstrap=report.parent/'runtime'/'policy_bootstrap'/'runtime_policy_bootstrap_verify_2026-09-22.json'
    bootstrap.parent.mkdir(parents=True); bootstrap.write_text(json.dumps(dict(passed=True, target_date='2026-09-22', status='pass')))
    from src.engine.automation import runtime_policy_bootstrap as bootstrap_owner
    monkeypatch.setattr(bootstrap_owner, 'manifest_path', lambda *a: bootstrap.parent/'manifest.json')
    monkeypatch.setattr(bootstrap_owner, 'verify_bootstrap', lambda *a, **kw: {'passed':True})
    monkeypatch.setattr(main, 'load_effective', lambda **kw: {'valid':True})
    monkeypatch.setattr(episode, 'load_policy', lambda *a, **kw: {'valid':True})
    monkeypatch.setattr(WidgetSymbolRuntimePolicyLoader, 'resolve_all', lambda *a, **kw: {'operating':{}})
    run('market_weakness', runner=lambda *a, **kw: 1)
    view=h.stage_overview(report, day)
    assert not view['postclose_all_active_stages_complete']
    assert view['next_session_policy_ready']
    monkeypatch.setattr(bootstrap_owner, 'verify_bootstrap', lambda *a, **kw: {'passed':False})
    assert not h.stage_overview(report, day)['next_session_policy_ready']
    monkeypatch.setattr(bootstrap_owner, 'verify_bootstrap', lambda *a, **kw: {'passed':True})
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


@pytest.mark.parametrize('status', ['pending', 'running', 'deferred'])
def test_scheduled_stage_check_reports_pending_as_deferred(stage_environment, monkeypatch, status):
    h, day, report, run, produce=stage_environment
    from src.utils import constants
    monkeypatch.setattr(constants, 'DATA_DIR', report.parent)
    h._stage_write(h.stage_path(report, day, 'main_auxiliary_policy'), {'status':status})
    assert h._stage_main(['--stage','main_auxiliary_policy','--date',day,'--check'])==75
