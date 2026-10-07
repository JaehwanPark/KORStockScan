import copy
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.error_detectors import artifact_freshness as detector
from src.engine.monitoring import family_policy_semantics as family
from src.engine.monitoring import episode_source_research as research
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


@pytest.mark.parametrize('clock,status', [('07:32:00','future_due'), ('07:35:03','future_due'),
                                        ('07:36:00','source_invalid')])
def test_episode_applied_deadline_matches_preopen_producer(tmp_path, clock, status):
    from src.engine.error_detectors.episode_health import check
    result = check(tmp_path, datetime.fromisoformat('2026-10-07T'+clock+'+09:00'),
        target_date='2026-10-07', reader=detector._semantic_object)
    assert result['status'] == status


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


@pytest.mark.parametrize('tamper', ['none', 'report', 'policy', 'projection', 'kernel'])
def test_family_seal_predecessors_and_population(tmp_path, tamper):
    folder = tmp_path / 'data/report/low_price_two_leg_tuning'
    folder.mkdir(parents=True)
    rp, pp, kernel = folder/'report.json', folder/'policy.json', tmp_path/'producer.py'
    report = dict(target_date='2026-10-02', paired_economic_search=dict(stage_counts=dict(profiles=1),
        profiles=dict(p=dict(disposition='valid_empty_no_fill', completed_actual_legs=0))),
        daily=dict(profiles=dict(p=dict(symbol='005930', session='KRX_REGULAR', source_quality='pass'))))
    policy = dict(target_date='2026-10-06')
    rp.write_text(json.dumps(report)); pp.write_text(json.dumps(policy)); kernel.write_text('producer')
    projection_path = family.publish(report, policy, report_path=rp, policy_path=pp, family='episode', producer_path=kernel)
    if tamper in {'report', 'policy', 'kernel'}:
        {'report': rp, 'policy': pp, 'kernel': kernel}[tamper].write_text('{}')
    if tamper == 'projection':
        v = json.loads(projection_path.read_text()); v['summary']['stage_counts']['profiles'] = 2
        projection_path.write_text(json.dumps(family.seal(v)))
    result = detector._family_policy_semantics(tmp_path, '2026-10-02', 'episode')
    # Current producer edits do not corrupt retained original kernel bytes.
    assert result['status'] == ('pass' if tamper in {'none', 'kernel'} else 'source_invalid')
    if tamper == 'kernel':
        assert set(result['kernel_custody'].values()) >= {'retained_original_bytes'}
    if tamper == 'none':
        assert result['summary']['dispositions'] == {'valid_empty_no_fill': 1}
        assert result['summary']['realized_profit'] is None








def test_future_episode_apply_does_not_count_historical_failed_units(tmp_path, monkeypatch):
    from src.engine.error_detectors import episode_health
    from src.trading.low_price_two_leg import profiles
    monkeypatch.setattr(profiles, "profiles_for_target_date", lambda day: {"p1": object(), "p2": object()})
    monkeypatch.setattr(episode_health, "unit_census", lambda *_: pytest.fail("future missing apply must not query historical units"))
    result = episode_health.check(tmp_path, datetime.fromisoformat('2026-10-05T20:00:00+09:00'),
        target_date='2026-10-06', reader=detector._semantic_object)
    assert result['status'] == 'future_due' and not result['findings']
    assert result['rows'] == [dict(profile_id='p1', status='future_due'), dict(profile_id='p2', status='future_due')]


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


@pytest.mark.parametrize('name', ['run_threshold_cycle_postclose.sh', 'run_postclose_done_controller.sh',
                                'run_machine_microstructure_final_refresh.sh',
                                'run_tuning_monitoring_postclose.sh'])
def test_holiday_wrappers_skip_before_native_stage_publication(name):
    import os
    import subprocess
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(['bash', str(root / 'deploy' / name), '2026-10-05'],
        text=True, capture_output=True, timeout=10,
        env={**os.environ, 'POSTCLOSE_STAGE_WORKER': '0', 'KORSTOCKSCAN_PROJECT_DIR': str(root),
             'KORSTOCKSCAN_PYTHON_BIN': str(root / '.venv/bin/python'),
             'PROJECT_DIR': str(root), 'VENV_PY': str(root / '.venv/bin/python')})
    assert result.returncode == 0, result.stderr
    assert '[SKIP]' in result.stdout and 'non_trading_source_date' in result.stdout






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


@pytest.mark.parametrize('native_rc, sidecar_rc', [(7, 0), (0, 9), (0, 0)])
def test_postclose_wrapper_preserves_native_failure_and_optional_research(tmp_path, native_rc, sidecar_rc):
    import os
    import subprocess
    folder = tmp_path / 'deploy'
    folder.mkdir()
    wrapper = folder / 'run_machine_microstructure_final_refresh.sh'
    original = Path(__file__).resolve().parents[2] / 'deploy' / wrapper.name
    wrapper.write_bytes(original.read_bytes())
    (folder / 'eod_terminal_gate.sh').write_text('wait_for_eod_terminal() { return 0; }\npostclose_source_calendar_state() { printf "trading\\n"; }\n')
    python = tmp_path / 'fake-python'
    python.write_text('''#!/usr/bin/env bash
if [[ "$1" == "-c" ]]; then
  if [[ "$2" == *resolve_completed_machine_target_date* ]]; then
    printf '2026-10-06\\n'
  else
    printf '2026-10-07\\n'
  fi
  exit 0
fi
printf '%s\\n' "$2" >> "$SEMANTIC_TEST_CALLS"
if [[ "$2" == "src.engine.automation.postclose_summary_handoff" ]]; then
  exit "$SEMANTIC_TEST_NATIVE_RC"
fi
exit "$SEMANTIC_TEST_SIDECAR_RC"
''')
    python.chmod(0o755)
    calls = tmp_path / 'calls'
    result = subprocess.run(['bash', str(wrapper)], capture_output=True, text=True,
        env={**os.environ, 'KORSTOCKSCAN_PROJECT_DIR': str(tmp_path), 'KORSTOCKSCAN_PYTHON_BIN': str(python),
            'SEMANTIC_TEST_CALLS': str(calls), 'SEMANTIC_TEST_NATIVE_RC': str(native_rc),
            'SEMANTIC_TEST_SIDECAR_RC': str(sidecar_rc)})
    assert result.returncode == native_rc
    modules = calls.read_text().splitlines()
    assert modules == ['src.engine.automation.postclose_summary_handoff'] + (
        ['src.engine.automation.samsung_frozen_postclose_validation'] if native_rc == 0 else [])


def test_episode_diagnostic_without_fills_uses_native_price_replay():
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    target = '2026-10-02'; profiles = profiles_for_target_date(__import__('datetime').date.fromisoformat(target))
    pid, live = next(iter(profiles.items()))
    start = datetime.fromisoformat('2026-10-02T09:00:00+09:00')
    values = [dict(timestamp=(start+__import__('datetime').timedelta(minutes=n)).isoformat(),
        open_price=10000, high_price=10100, low_price=9900, close_price=10000) for n in range(350)]
    import hashlib
    source = dict(source_ok=True, completed_bars=values,
        content_sha256=hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest())
    body = dict(profile_id=pid, action='bar_evaluated', execution_mode='real',
        observed_at_kst='2026-10-02T15:00:00+09:00', bar_source=source, signal_features={})
    policy = {k:getattr(live.policy,k) for k in ('rolling_high_drawdown_pct','rolling_low_proximity_pct',
        'lookback_bars','entry_valid_completed_bars','target_ticks')}; policy['quantity']=20
    report = dict(target_date=target, source_runtime_policy_binding=dict(status='ready', policies={pid:policy}))
    result = research.episode_research(report, {target:[body]})
    row = next(r for r in result['rows'] if r['profile_id']==pid)
    assert row['status']=='report_only_evaluated' and len(row['hypotheses'])==3
    assert result['actual_fill_floor_used_for_research'] is False
    assert all(r['runtime_apply_allowed'] is False for r in row['hypotheses'].values())


def test_partial_saved_bar_prefix_does_not_prove_empty_signal_window():
    from dataclasses import replace
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    from src.engine.monitoring import low_price_two_leg_entry_spot_research as native
    day = __import__('datetime').date.fromisoformat('2026-10-02')
    profile = next(iter(profiles_for_target_date(day).values()))
    candidate = replace(native.baseline_candidate(profile), scan_start_minute=600, scan_end_minute=609)
    start = datetime.fromisoformat('2026-10-02T09:00:00+09:00')
    bars = [native.Bar(start+__import__('datetime').timedelta(minutes=n), 10000, 10100, 9900, 10000)
            for n in range(25)]
    coverage = research.episode_window_coverage(candidate, native.build_day_contexts(bars), [day])
    assert not coverage['complete'] and coverage['dates'][0]['observed_signal_clocks'] == 0
    assert coverage['dates'][0]['missing_signal_clocks'] == list(range(600, 610))


def test_research_preserves_exact_report_bytes_when_native_publisher_moves(tmp_path, monkeypatch):
    day = '2026-10-02'
    reports = {}
    for family_dir, name in [('low_price_two_leg_tuning', 'low_price_two_leg_tuning')]:
        folder = tmp_path / 'data/report' / family_dir
        folder.mkdir(parents=True)
        path = folder / f'{name}_{day}.json'
        raw = json.dumps(dict(target_date=day, clean_baseline_window=dict(available_actual_observation_dates=[])), indent=2).encode()+b'\n'
        path.write_bytes(raw)
        reports[str(path)] = raw
    monkeypatch.setattr(research, 'episode_research', lambda *_: dict(rows=[]))
    result = research.run(tmp_path, day, tmp_path/'output')
    for source, receipt in result['report_snapshots'].items():
        Path(source).write_text('{"new_generation":true}')
        assert Path(receipt['path']).read_bytes() == reports[source]
        assert family.file_sha(receipt['path']) == result['report_seals'][source]


@pytest.mark.parametrize('defect', ['none', 'prior_date', 'prior_pid', 'prior_policy', 'changed_cwd', 'missing_sequence', 'stale', 'future_clock'])
@pytest.mark.parametrize('inspection', ['readable', 'permission_denied', 'process_exited', 'state_publish_race'])
def test_episode_current_pid_consumption_is_not_inferred_from_unit_configuration(tmp_path, monkeypatch, defect, inspection):
    from src.engine.error_detectors import episode_health
    from src.trading.low_price_two_leg import profiles, policy_runtime, preflight
    pid, profile = next(iter(profiles.PROFILES.items()))
    monkeypatch.setattr(profiles, 'profiles_for_target_date', lambda *_: {pid:profile})
    monkeypatch.setattr(policy_runtime, 'validate_applied', lambda *_, **__: (True,'valid'))
    monkeypatch.setattr(preflight, 'validate_authority', lambda *_, **__: (True,'ready'))
    def inspect(*_):
        if inspection == 'permission_denied':
            raise PermissionError(13, 'Permission denied')
        if inspection == 'process_exited':
            raise FileNotFoundError(2, 'Process exited')
        return '/reviewed-release'
    monkeypatch.setattr(episode_health.os, 'readlink', inspect)
    folder = tmp_path/'data/threshold_cycle/low_price_two_leg/applied'; folder.mkdir(parents=True)
    (folder/'low_price_two_leg_policy_2026-10-06.json').write_text(json.dumps(dict(policy_hash='a'*64)))
    captures = dict(source_date='2026-10-06', profile_id=pid, runtime_pid=123,
        runtime_cwd='/reviewed-release', policy_hash='a'*64, execution_mode='real', status='persisted',
        observed_at_kst='2026-10-06T10:00:00+09:00', observation_sha256='d'*64,
        capture_sequence=dict(schema='low_price_capture_sequence_v1', sequence=1, generation_id='b'*32, previous_observation_sha256=None))
    changes = dict(prior_date=('source_date','2026-10-02'), prior_pid=('runtime_pid',122),
        prior_policy=('policy_hash','c'*64), changed_cwd=('runtime_cwd','/other-release'), missing_sequence=('capture_sequence',None),
        stale=('observed_at_kst','2026-10-06T09:55:00+09:00'), future_clock=('observed_at_kst','2026-10-06T10:01:00+09:00'))
    if defect in changes:
        key,value = changes[defect]; captures[key]=value
    sf = tmp_path/'data/runtime/low_price_two_leg'; sf.mkdir(parents=True)
    (sf/f'{pid}_state.json').write_text(json.dumps(dict(trade_date='2026-10-06', economic_capture=captures)))
    timers = tmp_path/'timers'; timers.mkdir()
    (timers/'korstockscan-low-price-two-leg-test-preflight.timer').write_text(
        f'OnCalendar=Mon..Fri *-*-* 09:00:00 Asia/Seoul\nUnit=korstockscan-low-price-two-leg-preflight@{pid}.service\n')
    def reader(path):
        if inspection == 'state_publish_race' and path.name.endswith('_state.json'):
            raise ValueError('semantic_generation_changed_during_read')
        return detector._semantic_object(path)
    result = episode_health.check(tmp_path, datetime.fromisoformat('2026-10-06T10:00:00+09:00'),
        target_date='2026-10-06', reader=reader, timer_dir=timers,
        states={f'korstockscan-low-price-two-leg@{pid}.service':dict(MainPID='123', ActiveState='active', WorkingDirectory='/reviewed-release')})
    if inspection == 'state_publish_race':
        assert result['status']=='unobservable' and result['findings']==[]
        assert result['actual_pid_consumed'] is False
        return
    assert result['actual_pid_consumed'] is (defect=='none' and inspection=='readable')
    assert result['status']==('warning' if defect!='none' else
                              'pass' if inspection=='readable' else 'unobservable')
    if defect == 'none' and inspection != 'readable':
        assert result['unobservable_profile_count'] == 1
        assert result['findings'] == []
        assert result['rows'][0]['pid_cwd'] is None
        assert result['rows'][0]['capture_contract_valid'] is True
        assert detector._semantic_alerts('episode_startup',result,'2026-10-06') == []
    elif defect != 'none':
        alert = detector._semantic_alerts('episode_startup',result,'2026-10-06')[0]
        assert (alert['affected'],alert['eligible'],alert['total']) == (1,1,1)


@pytest.mark.parametrize('case,expected', [
    ('running', 'waiting_producer'), ('failed', 'warning'),
    ('past_start', 'warning'), ('no_receipt', 'warning'), ('after_grace', 'warning')])
def test_episode_preflight_publication_wait_is_exact_date_bounded_and_never_hides_failure(tmp_path, monkeypatch, case, expected):
    from src.engine.error_detectors import episode_health
    from src.trading.low_price_two_leg import profiles, policy_runtime, preflight
    pid = 'samsung_heavy_morning'
    profile = profiles.PROFILES[pid]
    monkeypatch.setattr(profiles, 'profiles_for_target_date', lambda *_: {pid: profile})
    monkeypatch.setattr(policy_runtime, 'validate_applied', lambda *_, **__: (True, 'valid'))
    monkeypatch.setattr(preflight, 'validate_authority', lambda *_, **__: (False, 'not_ready'))
    folder=tmp_path/'data/threshold_cycle/low_price_two_leg/applied';folder.mkdir(parents=True)
    (folder/'low_price_two_leg_policy_2026-10-06.json').write_text(json.dumps(dict(policy_hash='a'*64)))
    timers=tmp_path/'timers';timers.mkdir()
    (timers/'korstockscan-low-price-two-leg-test-preflight.timer').write_text(
        f'OnCalendar=Mon..Fri *-*-* 09:15:00 Asia/Seoul\nUnit=korstockscan-low-price-two-leg-preflight@{pid}.service\n')
    unit=dict(MainPID='123', ActiveState='activating', Result='success',
              ExecMainStartTimestamp='Tue 2026-10-06 09:15:00 KST')
    if case=='failed': unit.update(ActiveState='failed', Result='exit-code')
    if case=='past_start': unit['ExecMainStartTimestamp']='Mon 2026-10-05 09:15:00 KST'
    if case=='no_receipt': unit={}
    clock='09:16:01' if case=='after_grace' else '09:15:03'
    result=episode_health.check(tmp_path, datetime.fromisoformat('2026-10-06T'+clock+'+09:00'),
        target_date='2026-10-06', reader=detector._semantic_object, timer_dir=timers,
        states={f'korstockscan-low-price-two-leg-preflight@{pid}.service':unit})
    assert result['status']==expected and result['actual_pid_consumed'] is False
    if case=='running':
        assert result['findings']==[] and result['rows'][0]['status']=='waiting_preflight_producer'
        assert result['rows'][0]['authority']['valid'] is False
        assert detector._semantic_alerts('episode_startup',result,'2026-10-06') == []
    elif case=='failed':assert result['findings']==['episode_current_preflight_failed']
    else:assert result['findings']==['episode_current_preflight_not_observed']


@pytest.mark.parametrize('inspection', ['readable', 'permission_denied'])
@pytest.mark.parametrize('case', [
    'initializing', 'prior_terminal_initializing', 'repeated_initializing', 'failed_unit',
    'deadline', 'after_deadline', 'evaluated', 'pending', 'non_flat',
    'orders', 'attempted', 'prior_pid', 'wrong_policy', 'missing_prior',
    'invalid_prior', 'wrong_prior_profile', 'stale', 'prior_start', 'prior_publish_race'])
def test_episode_prior_custody_initialization_waits_only_for_first_completed_bar(tmp_path, monkeypatch, case, inspection):
    from src.engine.error_detectors import episode_health
    from src.trading.low_price_two_leg import profiles, policy_runtime, preflight
    pid = 'samsung_heavy_morning'
    profile = profiles.PROFILES[pid]
    monkeypatch.setattr(profiles, 'profiles_for_target_date', lambda *_: {pid: profile})
    monkeypatch.setattr(policy_runtime, 'validate_applied',
        lambda _, target_date: (not (case == 'invalid_prior' and target_date.isoformat() == '2026-10-05'), 'valid'))
    monkeypatch.setattr(preflight, 'validate_authority', lambda *_, **__: (True, 'ready'))
    def inspect(*_):
        if inspection == 'permission_denied':
            raise PermissionError(13, 'Permission denied')
        return '/reviewed-release'
    monkeypatch.setattr(episode_health.os, 'readlink', inspect)
    folder = tmp_path/'data/threshold_cycle/low_price_two_leg/applied'; folder.mkdir(parents=True)
    (folder/'low_price_two_leg_policy_2026-10-06.json').write_text(
        json.dumps(dict(policy_hash='a'*64, source_date='2026-10-05')))
    if case != 'missing_prior':
        (folder/'low_price_two_leg_policy_2026-10-05.json').write_text(
            json.dumps(dict(policy_hash='c'*64, profiles={} if case == 'wrong_prior_profile' else {pid: {}})))
    capture = dict(source_date='2026-10-06', profile_id=pid, runtime_pid=123,
        runtime_cwd='/reviewed-release', policy_hash='c'*64, execution_mode='real', status='persisted',
        observed_at_kst='2026-10-06T09:19:20+09:00', observation_sha256='d'*64,
        action='daily_state_initialized', capture_sequence=dict(schema='low_price_capture_sequence_v1',
            sequence=1, generation_id='b'*32, previous_observation_sha256=None))
    state = dict(trade_date='2026-10-06', status='READY', attempt_consumed=False, position_qty=0,
        legs=[], owned_order_nos=[], last_evaluated_bar='', pending_entry_confirmation=None, economic_capture=capture)
    if case in {'prior_terminal_initializing', 'repeated_initializing'}:
        capture['capture_sequence'].update(sequence=2, previous_observation_sha256='f'*64)
    if case == 'prior_terminal_initializing': capture['action'] = 'daily_state_initialized_from_prior_terminal_policy'
    if case == 'evaluated':
        capture['action'] = 'bar_evaluated_no_signal'
        state['last_evaluated_bar'] = '2026-10-06T09:20:00+09:00'
    if case == 'pending': state['pending_entry_confirmation'] = {'due_at': '2026-10-06T09:20:04+09:00'}
    if case == 'non_flat': state.update(position_qty=10, legs=[{'position_qty': 10}])
    if case == 'orders': state['owned_order_nos'] = ['native-order']
    if case == 'attempted': state['attempt_consumed'] = True
    if case == 'prior_pid': capture['runtime_pid'] = 122
    if case == 'wrong_policy': capture['policy_hash'] = 'e'*64
    if case == 'stale': capture['observed_at_kst'] = '2026-10-06T09:15:00+09:00'
    sf = tmp_path/'data/runtime/low_price_two_leg'; sf.mkdir(parents=True)
    (sf/f'{pid}_state.json').write_text(json.dumps(state))
    timers = tmp_path/'timers'; timers.mkdir()
    (timers/'korstockscan-low-price-two-leg-test-preflight.timer').write_text(
        f'OnCalendar=Mon..Fri *-*-* 09:15:00 Asia/Seoul\nUnit=korstockscan-low-price-two-leg-preflight@{pid}.service\n')
    unit = dict(MainPID='123', ActiveState='active', WorkingDirectory='/reviewed-release',
        ExecMainStartTimestamp='Tue 2026-10-06 09:19:14 KST')
    if case == 'prior_start': unit['ExecMainStartTimestamp'] = 'Mon 2026-10-05 09:19:14 KST'
    if case == 'failed_unit': unit['Result'] = 'exit-code'
    clock = '09:21:00' if case == 'deadline' else '09:21:01' if case == 'after_deadline' else '09:20:03'
    def reader(path):
        if case == 'prior_publish_race' and path.name == 'low_price_two_leg_policy_2026-10-05.json':
            raise ValueError('semantic_generation_changed_during_read')
        return detector._semantic_object(path)
    result = episode_health.check(tmp_path, datetime.fromisoformat('2026-10-06T'+clock+'+09:00'),
        target_date='2026-10-06', reader=reader, timer_dir=timers,
        states={f'korstockscan-low-price-two-leg@{pid}.service': unit})
    assert result['actual_pid_consumed'] is False
    if case == 'prior_publish_race':
        assert result['status'] == 'unobservable' and result['findings'] == []
    elif case in {'initializing', 'prior_terminal_initializing'}:
        row = result['rows'][0]
        assert result['status'] == 'waiting_producer' and result['findings'] == []
        assert row['status'] == 'waiting_runtime_policy_binding' and row['capture_contract_valid'] is False
        assert row['initial_policy_binding']['deadline'] == '2026-10-06T09:21:00+09:00'
        assert detector._semantic_alerts('episode_startup', result, '2026-10-06') == []
    else:
        assert result['findings'] == ['episode_current_pid_source_not_observed']
        alert = detector._semantic_alerts('episode_startup', result, '2026-10-06')[0]
        assert (alert['affected'], alert['eligible'], alert['total']) == (1, 1, 1)
