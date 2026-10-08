import copy
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








@pytest.mark.parametrize('defect', ['none', 'authority', 'candidate', 'generation', 'index_order'])
def test_samsung_semantic_result_binds_candidate_authority_and_generation(tmp_path, defect):
    from src.engine.scalping import samsung_tick_transition_forward_validation as native
    folder = tmp_path / 'data/report/samsung_tick_transition_forward_validation/2026-10-06'
    identity = dict(source_date='2026-10-06')
    generation = native.S.digest(identity)
    result_path = folder / generation / 'result.json'
    result_path.parent.mkdir(parents=True)
    result = dict(schema='samsung_tick_transition_forward_result_v1', **native.AUTHORITY,
        day='2026-10-06', candidate_id=native.CANDIDATE, status='waiting_new_source_date')
    if defect == 'authority': result['allowed_runtime_apply'] = True
    if defect == 'candidate': result['candidate_id'] = 'another_candidate'
    result_path.write_text(json.dumps(native.A.seal(result)))
    index = dict(schema='samsung_frozen_postclose_index_v1', owner='SamsungFrozenCandidateValidation1006',
        source_date='2026-10-06', target_date=None, generation=generation, identity=identity,
        result_path=str(result_path), result_file_sha256=native.H.file_sha(result_path),
        candidate_id=native.CANDIDATE, status='waiting_new_source_date', runtime_effect=False,
        policy_publication=False, actual_order_submitted=False, decision_authority='report_only')
    if defect == 'generation': index['generation'] = 'a'*64
    if defect == 'index_order': index['actual_order_submitted'] = True
    (folder/'latest.json').write_text(json.dumps(native.A.seal(index)))
    value = detector._samsung_forward_semantics(tmp_path, '2026-10-06')
    assert value['status'] == ('waiting_new_source_date' if defect == 'none' else 'source_invalid')
    assert bool(value['findings']) is (defect != 'none')


@pytest.mark.parametrize('shared_data', [False, True])
def test_samsung_sidecar_reuses_waiting_and_evaluated_generations(tmp_path, monkeypatch, shared_data):
    from src.engine.automation import samsung_frozen_postclose_validation as sidecar
    native = sidecar.consumer
    if shared_data:
        actual_data = tmp_path / 'shared-data'
        actual_data.mkdir()
        (tmp_path / 'data').symlink_to(actual_data, target_is_directory=True)
    contract = tmp_path / 'contract.json'
    contract.write_text(json.dumps(dict(artifact_content_sha256='a'*64)))
    source = tmp_path / 'source.json'
    calls = []
    monkeypatch.setattr(native, 'validate_registration', lambda *_: None)
    monkeypatch.setattr(native, 'source_paths', lambda *_: dict(capture=source))
    def prepare(root, day, receipt, output):
        calls.append(str(output)); output.mkdir(parents=True)
        value = native.A.seal(dict(day=day, status='evaluated' if source.exists() else 'waiting_new_source_date',
            consumer_contract_sha256='a'*64, source_seals={str(source):native.H.file_sha(source)} if source.exists() else {}))
        (output/'result.json').write_text(json.dumps(value))
        return value
    monkeypatch.setattr(native, 'prepare', prepare)
    first = sidecar.run(tmp_path, '2026-10-06', contract_path=contract)
    assert first == sidecar.run(tmp_path, '2026-10-06', contract_path=contract)
    source.write_text('{}')
    second = sidecar.run(tmp_path, '2026-10-06', contract_path=contract)
    assert second == sidecar.run(tmp_path, '2026-10-06', contract_path=contract)
    assert len(calls) == 2 and first['generation'] != second['generation']
    result = Path(second['result_path']); result.write_text('{}')
    with pytest.raises(ValueError, match='existing_generation_invalid'):
        sidecar.run(tmp_path, '2026-10-06', contract_path=contract)


def test_samsung_sidecar_shared_data_preserves_original_source_failure(tmp_path, monkeypatch):
    from src.engine.automation import samsung_frozen_postclose_validation as sidecar
    actual = tmp_path / 'shared-data'
    actual.mkdir()
    (tmp_path / 'data').symlink_to(actual, target_is_directory=True)
    contract = tmp_path / 'contract.json'
    contract.write_text('{}')
    def invalid(*_):
        raise ValueError('tick_research_source_changed:sealed-source')
    monkeypatch.setattr(sidecar.consumer, 'validate_registration', invalid)
    with pytest.raises(ValueError, match='tick_research_source_changed:sealed-source'):
        sidecar.run(tmp_path, '2026-10-06', contract_path=contract)
    receipt = json.loads((actual / 'report/samsung_tick_transition_forward_validation/2026-10-06/latest.json').read_text())
    assert receipt['status'] == 'failed'
    assert receipt['error'] == 'tick_research_source_changed:sealed-source'
    assert receipt['runtime_effect'] is receipt['policy_publication'] is False
    assert Path(receipt['result_path']).is_file()


def test_samsung_sidecar_busy_worker_does_not_replace_terminal(tmp_path):
    import fcntl
    from src.engine.automation import samsung_frozen_postclose_validation as sidecar
    folder = tmp_path / sidecar.REPORT_DIR / '2026-10-06'
    folder.mkdir(parents=True)
    terminal = folder / 'latest.json'
    terminal.write_text('{"status":"sealed_previous_generation"}')
    with (folder / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = sidecar.run(tmp_path, '2026-10-06')
    assert result['status'] == 'running'
    assert json.loads(terminal.read_text())['status'] == 'sealed_previous_generation'
