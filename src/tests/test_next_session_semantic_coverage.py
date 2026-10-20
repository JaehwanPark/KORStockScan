import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.error_detectors import artifact_freshness as detector
from src.engine.monitoring import family_policy_semantics as family
from src.tests.test_entry_designated_policy import staged_request, NOW


def test_current_owner_projection_retains_counts_and_marks_missing_owner():
    semantics = dict(status='source_invalid', findings=['cancel_wait_execution_failed'],
        target_date='2026-10-07', report_sha256='a'*64,
        unclassified_submission_count=4, daily_submitted_parent_count=10)
    alerts = detector._semantic_alerts('entry_cancel_wait_tuning', semantics, '2026-10-06',
        current_owners={'DirectFamilySourceRepairEntryCancelWait'}, as_of_date='2026-10-07')
    assert alerts[0]['owner'] == 'DirectFamilySourceRepairEntryCancelWait'
    assert alerts[0]['producer_owner'] == 'EntryCancelWaitSourceReconciliation1002'
    assert alerts[0]['affected'] == 4 and alerts[0]['eligible'] == 10
    assert alerts[0]['observation_date'] == '2026-10-07'
    alerts = detector._semantic_alerts('entry_cancel_wait_tuning', semantics, '2026-10-06', current_owners=set())
    assert alerts[0]['owner_status'] == 'unresolved'




@pytest.mark.parametrize('tamper', [False, True])
def test_native_designation_semantics_preserves_binding_and_rejects_changed_source(staged_request, tamper):
    from src.engine.scalping import entry_designated_policy as native
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    root, request_path, request, report, *_ = staged_request
    native.stage(request_path, data_root=root, now=NOW)
    bundle = runtime.load(data_root=root, target_date=native.TARGET)
    workspace = root / 'workspace'
    workspace.mkdir()
    (workspace / 'data').symlink_to(root, target_is_directory=True)
    folder = root / 'report/ai_decision_action_outcome_calibration'
    folder.mkdir(parents=True)
    day = report['target_date']
    full = calibration._with_artifact_content_sha256(dict(target_date=day,
        machine_full_evaluation=dict(scope_evaluations={})))
    (folder / f'ai_decision_action_outcome_calibration_{day}.json').write_text(json.dumps(full))
    if tamper:
        report = calibration._with_artifact_content_sha256(dict(report, candidate_selected=True))
    (folder / f'winrate_policy_{day}.json').write_text(json.dumps(report))
    terminal = calibration._with_artifact_content_sha256(dict(report_sha256=report['artifact_content_sha256'],
        staged=native._receipt(bundle)))
    (folder / f'winrate_policy_terminal_{day}.json').write_text(json.dumps(terminal))
    result = detector._machine_result_semantics(workspace, day)
    assert ('winrate_candidate_bundle_or_scope_mismatch' in result['findings']) is tamper


@pytest.mark.parametrize('clock, target', [
    ('2026-10-05T00:00:00+09:00', '2026-10-06'),
    ('2026-10-06T07:34:59+09:00', '2026-10-06'),
    ('2026-10-06T07:35:00+09:00', '2026-10-07'),
])
def test_calendar_handoff_has_receipt_source_on_holiday_and_preopen(tmp_path, clock, target):
    folder = tmp_path / 'data/report/postclose_done_controller'
    folder.mkdir(parents=True)
    (folder / 'postclose_done_controller_2026-10-02.json').write_text(json.dumps(
        dict(status='done', date='2026-10-02', report_type='postclose_done_controller', schema_version=2)))
    selected = detector._completed_semantic_source(tmp_path, datetime.fromisoformat(clock))
    assert selected['source_date'] == '2026-10-02'
    assert selected['target_date'] == target
    assert selected['status'] == 'receipt_selected'


def test_corrupt_latest_receipt_is_not_replaced_with_old_pass(tmp_path):
    folder = tmp_path / 'data/report/postclose_done_controller'
    folder.mkdir(parents=True)
    (folder / 'postclose_done_controller_2026-10-02.json').write_text('{bad')
    result = detector._completed_semantic_source(tmp_path, datetime.fromisoformat('2026-10-05T20:00:00+09:00'))
    assert result['status'] == 'source_invalid'


@pytest.mark.parametrize('status', ['summary_verified', 'blocked_direct_evidence_gap',
    'blocked_independent_producer', 'blocked_predecessor_not_succeeded', 'unknown', None])
def test_latest_recovery_source_never_rolls_back_to_previous_done(tmp_path, monkeypatch, status):
    folder = tmp_path / 'data/report/postclose_done_controller'
    folder.mkdir(parents=True)
    for day, state in [('2026-10-19', 'done'), ('2026-10-20', status)]:
        (folder / f'postclose_done_controller_{day}.json').write_text(json.dumps(dict(
            status=state, date=day, report_type='postclose_done_controller', schema_version=2)))
    now = datetime.fromisoformat('2026-10-21T07:45:07+09:00')
    selected = detector._completed_semantic_source(tmp_path, now)
    assert selected['source_date'] == '2026-10-20'
    monkeypatch.setattr(detector, '_semantic_stage_binding', lambda *args, **kwargs: dict(status='succeeded'))
    from src.engine.automation import postclose_summary_handoff
    monkeypatch.setattr(postclose_summary_handoff, 'stage_artifacts', lambda *args, **kwargs: {})
    result = detector._postclose_handoff_semantics(tmp_path, selected['source_date'], now)
    if status == 'summary_verified':
        assert result['status'] == 'unobservable'
        assert result['reason'] == 'whole_native_chain_pending'
        assert result['findings'] == []
    else:
        assert result['status'] == 'source_invalid'
        assert result['findings']












@pytest.mark.parametrize('day, expected', [('2026-10-05', 'non_trading'), ('2026-10-02', 'trading'), ('20261005', None)])
def test_postclose_calendar_does_not_wait_for_holiday_eod_or_accept_invalid_date(day, expected):
    import subprocess
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(['bash', '-c', 'source "$1/deploy/eod_terminal_gate.sh"; postclose_source_calendar_state "$1" "$1/.venv/bin/python" "$2"',
        'calendar-test', str(root), day], text=True, capture_output=True)
    assert (result.returncode == 0) if expected else (result.returncode != 0)
    if expected: assert result.stdout.strip() == expected


def test_native_controller_skips_holiday_before_predecessor_or_producer(monkeypatch, capsys):
    from src.engine.automation import postclose_done_controller as controller
    def forbidden(*args, **kwargs): raise AssertionError('holiday must not invoke producer or wait')
    monkeypatch.setattr(controller, '_wait_for_predecessor_succeeded', forbidden)
    monkeypatch.setattr(controller, 'build_postclose_done_controller', forbidden)
    assert controller.main(['--date', '2026-10-05']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'skipped_non_trading_day' and result['preparation'] is False
