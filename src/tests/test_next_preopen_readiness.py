import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import next_preopen_readiness as readiness

KST = ZoneInfo("Asia/Seoul")


@pytest.mark.parametrize('damage', [None, 'running', 'activated', 'env', 'main', 'lock', 'expired'])
def test_failed_preopen_recovery_requires_unactivated_terminal_failure_and_exclusive_lease(tmp_path, monkeypatch, damage):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    data = tmp_path / 'data'; (tmp_path / 'logs').mkdir()
    monkeypatch.setattr(readiness, 'DATA_DIR', data)
    day = '2026-10-12'; now = datetime.fromisoformat('2026-10-12T07:40:00+09:00')
    path = data / 'report/threshold_cycle_preopen_status' / f'threshold_cycle_preopen_{day}.status.json'
    _json(path, dict(status='running' if damage == 'running' else 'failed', target_date=day,
                    exit_code=1, runtime_env_exists=False, updated_at='2026-10-12T07:35:33+09:00'))
    _json(native.root(data) / 'current.json', dict(effective_date=day if damage == 'activated' else '2026-10-08'))
    if damage == 'env':
        p=data/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{day}.env';p.parent.mkdir(parents=True);p.write_text('existing')
    proc=tmp_path/'proc';proc.mkdir();process=proc/'123';process.mkdir()
    (process/'cmdline').write_bytes(b'python\0bot_main.py\0' if damage == 'main' else b'python\0other.py\0')
    path_class = readiness.Path
    monkeypatch.setattr(readiness, 'Path', lambda p: proc if p == '/proc' else path_class(p))
    import fcntl
    lock=(tmp_path/'logs/runtime_policy_preopen.lock').open('a')
    if damage == 'lock':fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if damage == 'expired':now=datetime.fromisoformat('2026-10-12T08:40:00+09:00')
    try:
        if damage:
            with pytest.raises((ValueError, BlockingIOError)):
                with readiness.failed_preopen_recovery(day,confirm=readiness.RECOVERY_AUTHORITY,now=now):
                    pytest.fail('unsafe recovery admitted')
        else:
            with readiness.failed_preopen_recovery(day,confirm=readiness.RECOVERY_AUTHORITY,now=now) as receipt:
                assert readiness.require_failed_preopen_recovery(data,day,now=now)==receipt
                path.write_text('{}')
                with pytest.raises(ValueError,match='lease_invalid'):
                    readiness.require_failed_preopen_recovery(data,day,now=now)
            with pytest.raises(ValueError,match='lease_invalid'):
                readiness.require_failed_preopen_recovery(data,day,now=now)
    finally:lock.close()


def test_prepared_activation_gate_detects_release_mismatch_before_bootstrap(tmp_path, monkeypatch):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    monkeypatch.setattr(readiness,'DATA_DIR',tmp_path)
    path = native.root(tmp_path)/'candidates/policy_2026-10-12.json'
    _json(path,dict(continuous_reversal=dict(schema='continuous_reversal_policy_v6',
           effective_mode='next_session',release_commit='a'*40),bundle_sha256='b'*64))
    monkeypatch.setattr(native,'validate',lambda *a,**k:None)
    monkeypatch.setattr(native,'_validate_bundle_sources',lambda *a,**k:None)
    with pytest.raises(ValueError,match='prepared_activation_release_mismatch'):
        readiness._activation_candidate_receipt('2026-10-12','c'*40)
    assert readiness._activation_candidate_receipt('2026-10-12','a'*40)['sha256']==readiness._sha(path)


@pytest.mark.parametrize('clock,recovery,expected', [
    ('2026-10-06T07:34:59+09:00', True, 'prepare_exact_effective_date'),
    ('2026-10-06T07:35:00+09:00', True, 'historical_recovery_no_prepare'),
    ('2026-10-06T15:30:00+09:00', True, 'historical_recovery_no_prepare'),
    ('2026-10-07T01:00:00+09:00', True, 'historical_recovery_no_prepare'),
    ('2026-10-06T15:30:00+09:00', False, None),
])
def test_finalization_recovery_never_prepares_another_session(clock, recovery, expected):
    # Oct 5 is a KRX holiday; the original Oct 2 source belongs to Oct 6.
    kwargs = dict(recovery=recovery, now=datetime.fromisoformat(clock))
    if expected is None:
        with pytest.raises(ValueError, match='already_opened'):
            readiness.finalization_preparation_disposition('2026-10-02', '2026-10-06', **kwargs)
    else:
        assert readiness.finalization_preparation_disposition('2026-10-02', '2026-10-06', **kwargs) == expected
    with pytest.raises(ValueError, match='source_session_mismatch'):
        readiness.finalization_preparation_disposition('2026-10-02', '2026-10-07', **kwargs)


def _json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_target_after_postclose_handles_late_recovery_and_weekend(monkeypatch):
    monkeypatch.setattr(readiness, "is_krx_trading_day", lambda day: day.weekday() < 5)
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 1, 2, 0, tzinfo=KST),
    ) == "2026-10-01"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 1, 17, 0, tzinfo=KST),
    ) == "2026-10-02"
    assert readiness.target_after_postclose(
        "2026-10-02", now=datetime(2026, 10, 2, 21, 0, tzinfo=KST),
    ) == "2026-10-05"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 2, 0, 36, tzinfo=KST),
    ) == "2026-10-02"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 2, 7, 34, tzinfo=KST),
    ) == "2026-10-02"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 2, 7, 35, tzinfo=KST),
    ) == "2026-10-05"
    assert readiness.target_after_postclose(
        "2026-09-30", now=datetime(2026, 10, 3, 0, 36, tzinfo=KST),
    ) == "2026-10-05"


def test_source_receipt_rejects_unclosed_controller_and_changed_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness, "DATA_DIR", tmp_path)
    source, target = "2026-09-30", "2026-10-02"
    controller = tmp_path / "report/postclose_done_controller" / f"postclose_done_controller_{source}.json"
    _json(controller, {"status": "done"})
    summary = tmp_path / "report/runtime_approval_summary" / f"runtime_approval_summary_{source}.json"
    policy = tmp_path / "runtime/mechanistic_entry_policy" / f"policy_{target}.json"
    _json(policy, {"target_date": target})
    policy_sha = hashlib.sha256(policy.read_bytes()).hexdigest()
    receipt = {"path": str(policy), "sha256": policy_sha, "valid": True,
               "target_date_matches": True}
    _json(summary, {"date": source, "sources": {
        "main_mechanistic_entry": {"policy_receipt": receipt},
        "compact_auxiliary": {"policy_receipt": receipt},
    }})
    monkeypatch.setattr(readiness, "done_terminal_receipt_issues", lambda *a, **k: ["strict_failed"])
    with pytest.raises(ValueError, match="postclose_controller_not_closed"):
        readiness._source_receipts(source, target)
    monkeypatch.setattr(readiness, "done_terminal_receipt_issues", lambda *a, **k: [])
    assert readiness._source_receipts(source, target)["policy_receipts"][0]["sha256"] == policy_sha
    policy.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="target_policy_receipt_invalid"):
        readiness._source_receipts(source, target)


def test_selected_release_requires_router_validated_root_and_commit(monkeypatch, tmp_path):
    release = tmp_path / "managed-release"
    release.mkdir()
    data = tmp_path / "workspace" / "data"
    selection = data / "runtime/runtime_release_selection.json"
    commit = "a" * 40
    _json(selection, {"schema": "runtime_release_selection_v1",
                      "release_root": str(release), "git_commit": commit})
    monkeypatch.setattr(readiness, "DATA_DIR", data)
    monkeypatch.chdir(release)
    calls = []

    def validated(workspace):
        calls.append(workspace)
        return release, commit

    monkeypatch.setattr(readiness, "selected_release", validated)
    assert readiness._selected_release() == (
        json.loads(selection.read_text()), selection, commit)
    assert calls == [data.parent]
    # Main and independent report consumers can verify without changing cwd.
    # The same paths must remain forbidden for preparing a new generation.
    for cwd in (release / 'src', tmp_path / 'report-release'):
        cwd.mkdir()
        monkeypatch.chdir(cwd)
        assert readiness._selected_release(require_selected_cwd=False)[2] == commit
        assert Path.cwd() == cwd
        with pytest.raises(ValueError, match='selected_release_identity_mismatch'):
            readiness._selected_release()
    _json(selection, {"schema": "runtime_release_selection_v1",
                      "release_root": str(release), "git_commit": "b" * 40})
    with pytest.raises(ValueError, match="selected_release_identity_mismatch"):
        readiness._selected_release(require_selected_cwd=False)


def test_prepare_isolated_then_detects_source_and_release_drift(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness, 'DATA_DIR', tmp_path)
    native_selection = readiness._selected_release
    source, target = "2026-09-30", "2026-10-02"
    monkeypatch.setattr(readiness, "PREPARED_DIR", tmp_path / "prepared")
    monkeypatch.setattr(readiness, "is_krx_trading_day", lambda day: day.weekday() < 5)
    selection = tmp_path / "selection.json"
    _json(selection, {"git_commit": "a" * 40})
    selected = ["a" * 40]
    monkeypatch.setattr(readiness, "_selected_release", lambda **kwargs: ({}, selection, selected[0]))
    controller = tmp_path / "controller.json"
    summary = tmp_path / "summary.json"
    policy = tmp_path / "policy.json"
    for path in (controller, summary, policy):
        _json(path, {"source_date": source})

    def receipts(_source, _target, **kwargs):
        assert (_source, _target) == (source, target)
        return {"controller_path": str(controller), "controller_sha256": readiness._sha(controller),
                "summary_path": str(summary), "summary_sha256": readiness._sha(summary),
                "policy_receipts": [{"family": "main_mechanistic_entry", "path": str(policy),
                                     "sha256": readiness._sha(policy)}]}

    monkeypatch.setattr(readiness, "_source_receipts", receipts)

    def write(day, *, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        _json(readiness.bootstrap.manifest_path(day, output_dir=output_dir),
              {"manifest_sha256": "m" * 64, "target_date": day,
               "source_incumbent": readiness.bootstrap._file_receipt(controller)})
        readiness.bootstrap.env_path(day, output_dir=output_dir).write_text("export TEST=1\n")
        return {"selected_release_sha": selected[0], "source_incumbent_target_date": "2026-10-01",
                "manifest_sha256": "m" * 64}

    def verify(day, *, output_dir, write=True):
        result = {"status": "pass", "findings": [], "manifest_sha256": "m" * 64, "target_date": day}
        if write:
            _json(readiness.bootstrap.verify_path(day, output_dir=output_dir), result)
        return result

    monkeypatch.setattr(readiness.bootstrap, "write_bootstrap", write)
    monkeypatch.setattr(readiness.bootstrap, "verify_bootstrap", verify)
    now = datetime(2026, 10, 1, 17, 0, tzinfo=KST)
    assert readiness.prepare(source, target_date=target, now=now)["status"] == "prepared_verified"
    assert readiness.verify_prepared(target, now=now)["status"] == "pass"
    # Exercise the real selection gate through verify_prepared, rather than
    # accepting a mocked selector from an unsafe daemon cwd.
    with monkeypatch.context() as consumer:
        release = tmp_path / 'release'
        release.mkdir()
        native_selector = tmp_path / 'runtime/runtime_release_selection.json'
        _json(native_selector, {'git_commit': selected[0]})
        consumer.setattr(readiness, 'DATA_DIR', tmp_path)
        consumer.setattr(readiness, '_selected_release', native_selection)
        consumer.setattr(readiness, 'selected_release', lambda workspace: (release, selected[0]))
        frozen = {str(p): p.read_bytes() for p in (tmp_path / 'prepared').rglob('*') if p.is_file()}
        for cwd in (release / 'src', tmp_path / 'independent-report'):
            cwd.mkdir()
            consumer.chdir(cwd)
            assert readiness.verify_prepared(target, now=now)['status'] == 'pass'
            with pytest.raises(ValueError, match='selected_release_identity_mismatch'):
                readiness.prepare(source, target_date=target, now=now)
            assert Path.cwd() == cwd
        assert all(Path(p).read_bytes() == content for p, content in frozen.items())
    midnight = datetime(2026, 10, 2, 0, 36, tzinfo=KST)
    assert readiness.prepare(source, target_date=target, now=midnight)["status"] == "prepared_verified"
    assert readiness.verify_prepared(target, require_today=True, now=midnight)["status"] == "pass"
    with monkeypatch.context() as bounded:
        bounded.setattr(readiness.bootstrap, "INITIAL_QUANTITY_CURRENT", tmp_path / "quantity-absent.json")
        bounded.setattr(readiness.bootstrap, "verify_bootstrap", lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("report-only generation check must not rerun policy economics")))
        assert readiness.verify_prepared(target, now=now, generation_only=True)["status"] == "pass"
        original = controller.read_bytes()
        controller.write_text("{}")
        assert readiness.verify_prepared(target, now=now, generation_only=True)["status"] == "fail"
        controller.write_bytes(original)
    assert readiness.verify_prepared(target, require_today=True, now=now)["status"] == "fail"
    selected[0] = "b" * 40
    assert readiness.verify_prepared(target, now=now)["status"] == "fail"
    selected[0] = "a" * 40
    policy.write_text("changed\n", encoding="utf-8")
    assert readiness.verify_prepared(target, now=now)["status"] == "fail"
    with pytest.raises(ValueError, match="preopen_target_not_next_operating_day"):
        readiness.prepare(source, target_date="2026-10-05", now=now)


def test_startup_requires_today_success_from_same_release(monkeypatch, tmp_path):
    monkeypatch.setattr(readiness, "DATA_DIR", tmp_path)
    target = "2026-10-02"
    status = tmp_path / "report/threshold_cycle_preopen_status" / f"threshold_cycle_preopen_{target}.status.json"
    receipt = {"target_date": target, "status": "succeeded", "exit_code": 0,
               "runtime_env_exists": True, "selected_release_commit": "a" * 40,
               "updated_at": "2026-10-02T07:36:00+09:00"}
    _json(status, receipt)
    now = datetime(2026, 10, 2, 7, 55, tzinfo=KST)
    assert readiness.verify_preopen_completion(target, "a" * 40, now=now)["status"] == "pass"
    assert readiness.verify_preopen_completion(target, "b" * 40, now=now)["status"] == "fail"
    receipt["status"] = "failed"
    _json(status, receipt)
    assert readiness.verify_preopen_completion(target, "a" * 40, now=now)["status"] == "fail"


@pytest.fixture
def stopped_rebind(tmp_path, monkeypatch):
    """Exercise real file/lock/CAS guards with only native producer boundaries mocked."""
    import copy
    from types import SimpleNamespace
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.automation import ordered_intraday_deploy as ordered
    from src.engine.automation import postclose_summary_handoff as stages
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import continuous_reversal_policy_v6 as policy
    source, target = '2026-10-14', '2026-10-15'
    workspace = tmp_path / 'workspace'
    data = workspace / 'data'
    release = tmp_path / 'release'
    release.mkdir(); (workspace / 'logs').mkdir(parents=True)
    monkeypatch.chdir(release)
    monkeypatch.setattr(readiness, '__file__', str(release / 'src/engine/automation/next_preopen_readiness.py'))
    monkeypatch.setattr(readiness, 'DATA_DIR', data)
    state = SimpleNamespace(now=datetime.fromisoformat(target + 'T00:01:00+09:00'),
                            main=False, supervisor=False, closure=[], producer=[], writes=0,
                            damage=None, origins=[], parent_calls=[])
    class Clock:
        @classmethod
        def now(cls, tz): return state.now
    monkeypatch.setattr(readiness, 'datetime', Clock)
    monkeypatch.setattr(readiness, 'is_krx_trading_day', lambda d: d.weekday() < 5)
    monkeypatch.setattr(router, 'selected_release', lambda w: (release, 'b' * 40))
    def validate_release(workspace, value):
        if state.damage == 'origin_identity': raise ValueError('original_release_commit_mismatch')
        return Path(value['release_root']), value['git_commit']
    monkeypatch.setattr(router, 'validate_release', validate_release)
    monkeypatch.setattr(ordered, '_main_pids', lambda: [123] if state.main else [])
    monkeypatch.setattr(ordered, '_session_absent', lambda: not state.supervisor)
    monkeypatch.setattr(readiness, 'done_terminal_receipt_issues', lambda *a, **k: state.closure)
    monkeypatch.setattr(stages, 'stage_receipt_issues', lambda *a, **k: state.producer)
    root = native.root(data)
    candidate = root / 'candidates' / ('policy_' + target + '.json')
    pointer = root / 'current.json'
    selection = data / 'runtime/runtime_release_selection.json'
    controller = data / 'report/postclose_done_controller' / ('postclose_done_controller_' + source + '.json')
    strict = data / 'report/threshold_cycle_postclose_verification/attempts' / source / 'strict.json'
    isolation = workspace / 'tmp/postclose_bot_isolation.json'
    hold = data / 'runtime/operator_startup_hold.json'
    family = dict(schema=policy.SCHEMA, source_date=source, publication_date=source,
                  effective_date=target, effective_mode='next_session', release_commit='a' * 40,
                  parent_bundle_sha256='d' * 64, machine_cells={'cell': {'routes': {'KRX': {'payload': {'branch': 'preserved'}}}}},
                  auxiliary_cells={'cell': {'routes': {'KRX': {'payload': {'arm': 'preserved'}}}}},
                  code_refresh={'source_bundle_sha256': 'e' * 64, 'older_proof': 'preserve_in_original'})
    original = dict(bundle_sha256='a' * 64, source_date=source, publication_date=source,
                    target_date=target, continuous_reversal=family, previous_bundle_sha256='d' * 64)
    _json(candidate, original)
    generation = root / 'generations' / ('a' * 64 + '.json')
    _json(generation, original)
    _json(pointer, dict(bundle_sha256='d' * 64, effective_date=source))
    _json(selection, dict(approved_by='user', approval_scope='after_postclose_deploy_for_next_regular_start', actual_pid_consumed=False))
    (data / 'runtime/runtime_release_set.lock').touch()
    _json(strict, {'status': 'pass', 'source': source})
    _json(controller, {'verification_attempt_path': str(strict), 'verification_attempt_sha256': readiness._sha(strict)})
    _json(isolation, dict(target_date=source, active=True, action='stop', session='bot'))
    _json(hold, {'owner': 'operator', 'reason': 'keep unchanged'})
    stage_files = [stages.stage_path(data / 'report', source, name) for name in stages.active_stage_names(source)]
    for path in stage_files: _json(path, {'status': 'succeeded'})
    monkeypatch.setattr(native, 'validate', lambda *a, **k: None)
    def validate_sources(bundle, data_root, *, historical_code_root=None):
        assert bundle == original
        state.origins.append(historical_code_root)
        if state.damage == 'origin': raise ValueError('unattested_original_source')
    monkeypatch.setattr(native, '_validate_bundle_sources', validate_sources)
    def parent(data_root, day, **kwargs):
        state.parent_calls.append(kwargs)
        return {'bundle_sha256': 'e' * 64 if state.damage == 'parent' else 'd' * 64}
    monkeypatch.setattr(policy, '_attested_activation_parent', parent)
    def refresh(bundle, data_root, *, release_commit, proof):
        state.writes += 1
        result = copy.deepcopy(bundle)
        result['bundle_sha256'] = 'c' * 64
        result['continuous_reversal'].update(release_commit=release_commit, code_refresh=proof)
        if state.damage == 'behavior':
            result['continuous_reversal']['auxiliary_cells']['cell']['routes']['KRX']['payload']['arm'] = 'changed'
        if state.damage == 'selection': _json(selection, {'changed': True})
        if state.damage == 'controller': _json(controller, {'changed': True})
        if state.damage == 'generation': _json(generation, {'changed': True})
        if state.damage == 'candidate': _json(candidate, {'changed': True})
        if state.damage == 'current': _json(pointer, {'changed': True})
        if state.damage == 'hold': _json(hold, {'changed': True})
        if state.damage in {'lock_inode', 'release_lock_inode', 'producer_lock_inode', 'publisher_lock_inode'}:
            lock = {'lock_inode': workspace / 'logs/runtime_policy_preopen.lock',
                    'release_lock_inode': data / 'runtime/runtime_release_set.lock',
                    'producer_lock_inode': stage_files[0].with_suffix('.lock'),
                    'publisher_lock_inode': root / 'publisher.lock'}[state.damage]
            lock.unlink(); lock.touch()
        if state.damage == 'cutoff': state.now = datetime.fromisoformat(target + 'T07:35:00+09:00')
        return result
    monkeypatch.setattr(policy, '_write_refreshed_bundle', refresh)
    args = dict(publication_date=source, expected_bundle_sha256='a' * 64,
                expected_candidate_sha256=readiness._sha(candidate),
                expected_current_pointer_sha256=readiness._sha(pointer), expected_selection_sha256=readiness._sha(selection),
                origin_root=tmp_path / 'origin', activation_parent_origin_root=tmp_path / 'parent-origin',
                activation_parent_origin_commit='f' * 40, release_commit='b' * 40,
                reason='reviewed same-policy stopped preparation', confirm=policy.CODE_REFRESH_AUTHORITY)
    state.call = lambda **overrides: readiness.stopped_postclose_candidate_rebind(source, target, **(args | overrides))
    state.paths = dict(candidate=candidate, current=pointer, generation=generation, selection=selection,
                       controller=controller, strict=strict, isolation=isolation, hold=hold)
    state.data, state.workspace, state.original, state.args = data, workspace, original, args
    return state


def test_stopped_rebind_preserves_policy_original_proof_sources_and_current(stopped_rebind):
    s = stopped_rebind
    before = {name: path.read_bytes() for name, path in s.paths.items()}
    successor = s.call()
    assert s.writes == 1
    assert s.origins == [s.args['origin_root']]
    assert s.parent_calls == [{'origin_root': s.args['activation_parent_origin_root'], 'origin_commit': 'f' * 40}]
    assert successor['continuous_reversal']['code_refresh']['source_bundle_sha256'] == s.original['bundle_sha256']
    assert json.loads(s.paths['generation'].read_text())['continuous_reversal']['code_refresh'] == s.original['continuous_reversal']['code_refresh']
    assert all(path.read_bytes() == before[name] for name, path in s.paths.items() if name != 'candidate')
    assert json.loads(s.paths['candidate'].read_text()) == successor
    proof = successor['continuous_reversal']['code_refresh']['stopped_postclose_preparation']
    assert proof['source_date'] == '2026-10-14' and proof['target_date'] == '2026-10-15'
    assert proof['source_sha256'][str(s.paths['controller'])] == hashlib.sha256(before['controller']).hexdigest()


@pytest.mark.parametrize('field,value', [
    ('confirm', 'unapproved'), ('reason', ''), ('publication_date', '2026-10-15'),
    ('expected_candidate_sha256', '0' * 64), ('expected_bundle_sha256', '0' * 64),
    ('expected_current_pointer_sha256', '0' * 64), ('expected_selection_sha256', '0' * 64),
    ('release_commit', 'a' * 40), ('activation_parent_origin_commit', 'bad'),
])
def test_stopped_rebind_authority_and_exact_cas_required(stopped_rebind, field, value):
    s = stopped_rebind; before = s.paths['candidate'].read_bytes()
    with pytest.raises(ValueError): s.call(**{field: value})
    assert s.writes == 0 and s.paths['candidate'].read_bytes() == before


@pytest.mark.parametrize('instant,allowed', [
    ('2026-10-14T23:59:59+09:00', False), ('2026-10-15T00:00:00+09:00', True),
    ('2026-10-15T07:34:59+09:00', True), ('2026-10-15T07:35:00+09:00', False),
    ('2026-10-16T00:00:00+09:00', False), ('2026-10-15T00:00:00', False),
])
def test_stopped_rebind_real_clock_window(stopped_rebind, instant, allowed):
    s = stopped_rebind; s.now = datetime.fromisoformat(instant)
    if allowed: assert s.call()['bundle_sha256'] == 'c' * 64
    else:
        with pytest.raises(ValueError, match='window_closed'): s.call()
        assert s.writes == 0


@pytest.mark.parametrize('fault', ['main', 'supervisor', 'closure', 'producer', 'restart', 'env', 'preopen', 'isolation', 'activated', 'source_date', 'mode', 'parent_hash', 'selected_pid', 'selected_transition', 'lock', 'release_lock_absent', 'release_lock_symlink'])
def test_stopped_rebind_refuses_running_unclosed_or_activated_state(stopped_rebind, fault):
    s = stopped_rebind; before = s.paths['candidate'].read_bytes()
    lock = None
    if fault in {'main', 'supervisor'}: setattr(s, fault, True)
    elif fault in {'closure', 'producer'}: setattr(s, fault, ['not_closed'])
    elif fault == 'restart': (s.workspace / 'restart.flag').touch()
    elif fault == 'env': _json(s.data / 'runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-15.env', {})
    elif fault == 'preopen': _json(s.data / 'report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-10-15.status.json', {'status': 'failed'})
    elif fault == 'isolation': _json(s.paths['isolation'], {'active': False})
    elif fault == 'activated':
        _json(s.paths['current'], {'bundle_sha256': 'd' * 64, 'effective_date': '2026-10-15'})
        s.args['expected_current_pointer_sha256'] = readiness._sha(s.paths['current'])
    elif fault in {'source_date', 'mode', 'parent_hash'}:
        value = json.loads(before)
        key, bad = {'source_date': ('source_date', '2026-10-13'), 'mode': ('effective_mode', 'intraday'), 'parent_hash': ('parent_bundle_sha256', 'e' * 64)}[fault]
        value['continuous_reversal'][key] = bad
        _json(s.paths['candidate'], value); before = s.paths['candidate'].read_bytes()
        s.args['expected_candidate_sha256'] = readiness._sha(s.paths['candidate'])
    elif fault in {'selected_pid', 'selected_transition'}:
        value = json.loads(s.paths['selection'].read_text())
        value.update({'actual_pid_consumed': True} if fault == 'selected_pid' else {'deployment_transition': '/old'})
        _json(s.paths['selection'], value); s.args['expected_selection_sha256'] = readiness._sha(s.paths['selection'])
    elif fault == 'lock':
        import fcntl
        lock = (s.workspace / 'logs/runtime_policy_preopen.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    elif fault.startswith('release_lock_'):
        path = s.data / 'runtime/runtime_release_set.lock'
        path.unlink()
        if fault == 'release_lock_symlink': path.symlink_to(s.paths['hold'])
    try:
        with pytest.raises((ValueError, OSError)): s.call()
        assert s.writes == 0 and s.paths['candidate'].read_bytes() == before
    finally:
        if lock: lock.close()


@pytest.mark.parametrize('damage', ['origin', 'origin_identity', 'parent', 'behavior', 'selection', 'controller', 'generation', 'candidate', 'current', 'hold', 'lock_inode', 'release_lock_inode', 'producer_lock_inode', 'publisher_lock_inode', 'cutoff'])
def test_stopped_rebind_rechecks_native_authority_and_preserves_failed_cas(stopped_rebind, damage):
    s = stopped_rebind; before = s.paths['candidate'].read_bytes(); s.damage = damage
    with pytest.raises((ValueError, KeyError)): s.call()
    # An independently changed candidate remains exactly the intervening value.
    assert s.paths['candidate'].read_bytes() == (b'{"changed": true}\n' if damage == 'candidate' else before)
    if damage in {'origin', 'origin_identity', 'parent'}: assert s.writes == 0


def test_stopped_rebind_postpublication_clock_failure_discloses_committed_candidate(stopped_rebind, monkeypatch):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    s = stopped_rebind
    before = s.paths['current'].read_bytes()
    publish = native._atomic_write_json
    def boundary(path, value):
        publish(path, value)
        if path == s.paths['candidate']:
            s.now = datetime.fromisoformat('2026-10-15T07:35:00+09:00')
    monkeypatch.setattr(native, '_atomic_write_json', boundary)
    with pytest.raises(ValueError, match='candidate_published_postcheck_failed:' + 'c' * 64):
        s.call()
    assert json.loads(s.paths['candidate'].read_text())['bundle_sha256'] == 'c' * 64
    assert s.paths['current'].read_bytes() == before
