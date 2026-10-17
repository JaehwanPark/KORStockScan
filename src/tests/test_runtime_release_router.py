import hashlib
import os
import json
import subprocess
import sys
import shutil
from pathlib import Path

import pytest

from src.engine.infrastructure import runtime_release_router as router


@pytest.mark.parametrize('damage', [None, 'root', 'commit', 'invalid_selection'])
def test_detector_rechecks_current_selection_after_wrapper_lock(tmp_path, monkeypatch, damage):
    workspace = tmp_path / 'project'
    (workspace / 'data').mkdir(parents=True)
    root = tmp_path / 'release'
    root.mkdir()
    (root / 'data').symlink_to(workspace / 'data', target_is_directory=True)
    def selected(actual_workspace):
        assert actual_workspace == workspace
        if damage == 'invalid_selection':
            raise ValueError('release_git_commit_mismatch')
        return (tmp_path / 'successor' if damage == 'root' else root, 'a' * 40)
    monkeypatch.setattr(router, 'selected_release', selected)
    if damage == 'invalid_selection':
        with pytest.raises(ValueError, match='release_git_commit_mismatch'):
            router.error_detector_release_is_current(root)
    else:
        commit = 'b' * 40 if damage == 'commit' else 'a' * 40
        assert router.error_detector_release_is_current(root, commit) == (damage is None)
        if damage is None:
            assert router.error_detector_release_is_current(root)


def test_isolated_filename_router_loads_only_exact_guard_files(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    workspace = tmp_path / 'project'
    for name in ('infrastructure/runtime_release_router.py',
                 'infrastructure/research_release_transition.py',
                 'lifecycle/research_admission.py'):
        target = workspace / 'src/engine' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / 'src/engine' / name, target)
    runtime = workspace / 'data/runtime'
    runtime.mkdir(parents=True)
    (runtime / 'runtime_release_selection.json').write_text('{}')
    poison = tmp_path / 'poison'
    (poison / 'src').mkdir(parents=True)
    marker = tmp_path / 'poison-imported'
    (poison / 'src/__init__.py').write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
    result = subprocess.run([sys.executable, '-I',
        str(workspace / 'src/engine/infrastructure/runtime_release_router.py'),
        'start', '2026-10-12', '--print-plan'], cwd=poison,
        env={**os.environ, 'PYTHONPATH': str(poison)},
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'release_selection_schema_invalid' in result.stderr
    assert 'ImportError' not in result.stderr
    assert not marker.exists()
    body = {'schema': 'research_release_transition_v1', 'transition_id': 'blocked',
            'state': 'publishing', 'owner_pid': os.getpid()}
    body['manifest_sha256'] = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    fence = runtime / 'research_release_transition/current.json'
    fence.parent.mkdir()
    fence.write_text(json.dumps(body))
    blocked = subprocess.run([sys.executable, '-I',
        str(workspace / 'src/engine/infrastructure/runtime_release_router.py'),
        'start', '2026-10-12', '--print-plan'], cwd=poison,
        env={**os.environ, 'PYTHONPATH': str(poison)},
        capture_output=True, text=True, timeout=10)
    assert blocked.returncode == 2
    assert 'research_release_transition_incomplete' in blocked.stderr
    assert 'ImportError' not in blocked.stderr
    assert not marker.exists()


@pytest.fixture
def isolated_record_cli(tmp_path):
    """Exercise the deployed filename CLI, its real git gates and a real child."""
    repo = Path(__file__).resolve().parents[2]
    workspace = tmp_path / 'project'
    root = tmp_path / 'project-runtime-releases/reviewed'
    for name in ('data', 'logs', 'tmp', '.venv', 'docs'):
        (workspace / name).mkdir(parents=True)
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).symlink_to(workspace / name, target_is_directory=True)
    (root / 'restart.flag').symlink_to(workspace / 'restart.flag')
    for name in ('infrastructure/runtime_release_router.py',
                 'infrastructure/research_release_transition.py',
                 'lifecycle/research_admission.py'):
        target = root / 'src/engine' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / 'src/engine' / name, target)
    (root / '.gitignore').write_text('__pycache__/\n*.pyc\n')
    for arguments in (('init', '-q'), ('add', 'src', '.gitignore'),
                      ('-c', 'user.email=test@example.invalid', '-c', 'user.name=Test',
                       'commit', '-qm', 'Test selected router source')):
        subprocess.run(['git', '-C', str(root), *arguments], check=True, capture_output=True)
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    selection_path = workspace / 'data/runtime/runtime_release_selection.json'
    selection_path.parent.mkdir()
    selection_path.write_text(json.dumps(dict(schema='runtime_release_selection_v1',
        workspace=str(workspace), release_root=str(root), git_commit=commit)))
    child = subprocess.Popen([sys.executable, '-I', '-c', 'import sys; sys.stdin.read()'],
                             cwd=root / 'src', stdin=subprocess.PIPE)
    command = [sys.executable, '-I', str(root / 'src/engine/infrastructure/runtime_release_router.py'),
               '--workspace', str(workspace), '--record-pid', str(child.pid),
               '--record-release-root', str(root), '--record-git-commit', commit]
    try:
        yield workspace, root, selection_path, child, command
    finally:
        child.communicate(timeout=5)


def test_selected_filename_cli_records_shared_workspace_pid(isolated_record_cli, tmp_path):
    workspace, root, selection_path, child, command = isolated_record_cli
    original = json.loads(selection_path.read_text())
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    selected = json.loads(selection_path.read_text())
    assert receipt['pid'] == child.pid
    assert receipt['start_ticks'] == router._process_start_ticks(child.pid)
    assert receipt['release_root'] == str(root)
    assert receipt['process_cwd'] == str(root / 'src')
    assert selected['actual_pid_consumed'] is True
    assert selected['actual_pid_receipt'] == receipt
    assert {key: selected[key] for key in original} == original
    assert not (root / 'data/runtime/runtime_release_selection.lock').is_symlink()


@pytest.mark.parametrize('damage, reason', [
    ('relative_workspace', 'runtime_pid_workspace_not_canonical'),
    ('aliased_workspace', 'runtime_pid_workspace_not_canonical'),
    ('operation', 'runtime_pid_workspace_record_only'),
    ('cron', 'runtime_pid_workspace_record_only'),
    ('print', 'runtime_pid_workspace_record_only'),
    ('not_record', 'runtime_pid_workspace_record_only'),
    ('source', 'runtime_pid_router_not_selected_source'),
    ('mount', 'release_shared_path_mismatch:data'),
    ('release', 'runtime_pid_release_root_mismatch'),
    ('commit', 'runtime_pid_commit_mismatch'),
])
def test_selected_filename_cli_rejects_unbound_or_nonrecord_workspace(isolated_record_cli, tmp_path, damage, reason):
    workspace, root, selection_path, _, command = isolated_record_cli
    original = selection_path.read_bytes()
    if damage == 'relative_workspace': command[command.index('--workspace') + 1] = 'project'
    elif damage == 'aliased_workspace':
        alias = tmp_path / 'alias'; alias.symlink_to(workspace, target_is_directory=True)
        command[command.index('--workspace') + 1] = str(alias)
    elif damage == 'operation': command.append('start')
    elif damage == 'cron': command.append('--check-cron')
    elif damage == 'print': command.append('--print-plan')
    elif damage == 'not_record':
        index = command.index('--record-pid'); del command[index:index + 2]
    elif damage == 'source':
        # A clean unrelated source tree cannot attest the selected child.
        other = tmp_path / 'unselected'
        shutil.copytree(root / 'src', other / 'src')
        command[2] = str(other / 'src/engine/infrastructure/runtime_release_router.py')
    elif damage == 'mount':
        wrong_data = tmp_path / 'wrong-data'; wrong_data.mkdir()
        (root / 'data').unlink(); (root / 'data').symlink_to(wrong_data, target_is_directory=True)
    elif damage == 'release': command[command.index('--record-release-root') + 1] = str(workspace)
    elif damage == 'commit': command[command.index('--record-git-commit') + 1] = '0' * 40
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2, result.stdout
    assert reason in result.stderr
    assert 'unrecognized arguments' not in result.stderr
    assert selection_path.read_bytes() == original


@pytest.fixture
def release(tmp_path, monkeypatch):
    workspace = tmp_path / "project"
    root = tmp_path / "project-runtime-releases" / "reviewed"
    root.mkdir(parents=True)
    for name in ("data", "logs", "tmp", ".venv", "docs"):
        (workspace / name).mkdir(parents=True)
        (root / name).symlink_to(workspace / name, target_is_directory=True)
    (root / "restart.flag").symlink_to(workspace / "restart.flag")
    (workspace / "data/runtime").mkdir()
    selection = {
        "schema": "runtime_release_selection_v1",
        "workspace": str(workspace),
        "release_root": str(root),
        "git_commit": "a" * 40,
    }
    manifest = workspace / "data/runtime/runtime_release_selection.json"
    manifest.write_text(json.dumps(selection))
    monkeypatch.setattr(
        router, "git", lambda _, *args: "a" * 40 if args[0] == "rev-parse" else ""
    )
    monkeypatch.setattr(router, '_process_start_ticks', lambda _pid: '100')
    return workspace, root, manifest, selection


def test_error_detector_route_consumes_selected_release_and_keeps_log_owner(release):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, "error-detection", "2026-10-02")
    assert str(root / "deploy/run_error_detection.sh") in plan["command"]
    assert str(workspace / "logs/run_error_detection_cron.log") in plan["command"]
    assert plan["command"][-1] == "full"
    assert plan["cwd"] == str(root)




def test_error_cron_installer_preserves_unrelated_auth_and_finalizer(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "data/runtime").mkdir(parents=True)
    cron = tmp_path / "crontab.txt"
    original = ("0 5 * * * bash /project/deploy/run_runtime_release.sh finalize # POSTCLOSE_FINALIZATION_0500\n"
                "1 8 * * * bash /project/deploy/run_error_detection.sh auth_only # AUTH_ONLY\n"
                "*/5 7-20 * * 1-5 bash /project/deploy/run_error_detection.sh full # ERROR_DETECTION_FULL\n")
    cron.write_text(original)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    command = bin_dir / "crontab"
    command.write_text('#!/bin/bash\nif [[ "$1" == "-l" ]]; then /bin/cat "$CRON_FIXTURE"; else /bin/cp "$1" "$CRON_FIXTURE"; fi\n')
    command.chmod(0o755)
    env = {**os.environ, "PROJECT_DIR": str(workspace), "CRON_FIXTURE": str(cron),
           "PATH": str(bin_dir) + ":" + os.environ["PATH"]}
    installer = Path(__file__).resolve().parents[2] / "deploy/install_error_detection_cron.sh"
    for _ in range(2):
        subprocess.run(["bash", str(installer)], env=env, check=True, capture_output=True)
    result = cron.read_text()
    assert original.splitlines()[0] in result
    assert original.splitlines()[1] in result
    assert result.count("# ERROR_DETECTION_FULL") == 3
    assert result.count(" error-detection ") == 3


def test_release_shares_operator_flag_and_docs(release):
    workspace, root, _, _ = release
    assert router.selected_release(workspace) == (root, "a" * 40)
    assert not (workspace / "restart.flag").exists()


def test_pid_receipt_requires_selected_release_child_cwd(release, monkeypatch):
    workspace, root, manifest, _ = release
    (root / "src").mkdir()
    real_readlink = router.os.readlink
    monkeypatch.setattr(
        router.os,
        "readlink",
        lambda path: str(root / "src")
        if str(path).startswith("/proc/")
        else real_readlink(path),
    )

    receipt = router.record_runtime_pid_consumption(
        workspace,
        pid=1234,
        release_root=root,
        git_commit="a" * 40,
    )

    selection = json.loads(manifest.read_text())
    assert receipt["pid"] == 1234
    assert receipt['start_ticks'] == '100'
    assert selection["actual_pid_consumed"] is True
    assert selection["actual_pid_consumption_status"] == "pid_receipt_attested"
    assert selection["actual_pid_receipt"]["process_cwd"] == str(root / "src")


def _startup_receipts(release, monkeypatch, *, intraday=False):
    workspace, root, selection_path, _ = release
    (root / 'src').mkdir()
    original_readlink = router.os.readlink
    monkeypatch.setattr(router.os, 'readlink', lambda path: str(root / 'src')
                        if str(path).startswith('/proc/') else original_readlink(path))
    router.record_runtime_pid_consumption(workspace, pid=1234, release_root=root, git_commit='a' * 40)
    directory = workspace / 'data/runtime/policy_bootstrap'
    directory.mkdir()
    day = '2026-10-14'
    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
    manifest = dict(target_date=day, selected_release_sha='b' * 40 if intraday else 'a' * 40)
    manifest['manifest_sha256'] = hashlib.sha256(json.dumps(manifest, ensure_ascii=True,
        allow_nan=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    manifest_path = directory / f'runtime_policy_bootstrap_{day}.json'
    verify_path = directory / f'runtime_policy_bootstrap_verify_{day}.json'
    put(manifest_path, manifest)
    verification = dict(target_date=day, status='pass', passed=True, pid=1234,
                        pid_passed=True, pid_env_available=True, manifest_sha256=manifest['manifest_sha256'])
    put(verify_path, verification)
    handoff_path = directory / 'intraday_handoff' / day / ('a' * 40 + '.json')
    consumed_path = handoff_path.with_suffix('.consumed.json')
    if intraday:
        handoff = dict(schema='intraday_policy_preserving_release_handoff_v1', status='prepared_verified',
                       authority='APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF',
                       target_date=day, selected_release_commit='a' * 40, release_root=str(root))
        put(handoff_path, handoff)
        consumed = dict(schema='intraday_policy_preserving_consumption_v1', status='pass',
            actual_pid_consumed=True, target_date=day, selected_release_commit='a' * 40,
            release_root=str(root), pid_identity=dict(pid=1234, start_ticks='100', cwd=str(root / 'src')),
            manifest_sha256=manifest['manifest_sha256'],
            handoff_sha256=hashlib.sha256(handoff_path.read_bytes()).hexdigest())
        put(consumed_path, consumed)
    expected = dict(workspace=workspace, pid=1234, start_ticks='100', release_root=root,
                    git_commit='a' * 40, target_date=day)
    return expected, dict(selection=selection_path, manifest=manifest_path, verification=verify_path,
                          handoff=handoff_path, consumed=consumed_path), put


@pytest.mark.parametrize('intraday', [False, True])
def test_startup_first_health_barrier_uses_bounded_exact_receipts(release, monkeypatch, intraday):
    expected, paths, _ = _startup_receipts(release, monkeypatch, intraday=intraday)
    monkeypatch.setattr(router, 'selected_release', lambda *a: pytest.fail('no native release/source revalidation'))
    monkeypatch.setattr(router, 'git', lambda *a: pytest.fail('no startup git/provider subprocess'))
    result = router.startup_consumption_state(**expected)
    assert result['status'] == 'ready'
    assert result['basis'] == ('intraday_policy_preserving_handoff' if intraday else 'native_preopen')
    assert result['runtime_effect'] is False and result['new_finalization_claimed'] is False


@pytest.mark.parametrize('damage, status, reason', [
    ('old_pid', 'pending', 'waiting_current_pid_attestation'),
    ('not_attested', 'pending', 'waiting_current_pid_attestation'),
    ('reused_pid', 'failed', 'startup_attested_identity_invalid'),
    ('generation', 'failed', 'startup_selected_generation_changed'),
    ('bad_receipt', 'failed', 'startup_attested_identity_invalid'),
    ('verify', 'failed', 'startup_bootstrap_pid_receipt_invalid'),
    ('manifest', 'failed', 'startup_bootstrap_pid_receipt_invalid'),
    ('missing_handoff', 'failed', 'startup_native_preopen_release_mismatch'),
    ('consumed', 'failed', 'startup_intraday_consumption_invalid'),
    ('oversized', 'failed', 'startup_receipt_size_limit'),
    ('duplicate_key', 'failed', 'startup_receipt_duplicate_key'),
    ('fifo', 'failed', 'startup_receipt_regular_file_required'),
    ('symlink', 'failed', 'startup_receipt_symlink'),
])
def test_startup_first_health_barrier_never_relabels_incomplete_or_invalid_as_pass(
    release, monkeypatch, damage, status, reason
):
    expected, paths, put = _startup_receipts(release, monkeypatch, intraday=True)
    selection = json.loads(paths['selection'].read_text())
    if damage == 'old_pid': selection['actual_pid_receipt']['pid'] = 9999
    elif damage == 'not_attested': selection['actual_pid_consumed'] = False
    elif damage == 'reused_pid': selection['actual_pid_receipt']['start_ticks'] = 'old'
    elif damage == 'generation': selection['git_commit'] = 'c' * 40
    elif damage == 'bad_receipt': selection['actual_pid_receipt'] = ['malformed']
    put(paths['selection'], selection)
    if damage in {'verify', 'manifest', 'consumed'}:
        selected = 'verification' if damage == 'verify' else damage
        payload = json.loads(paths[selected].read_text())
        payload['status' if damage == 'verify' else 'manifest_sha256'] = 'wrong'
        put(paths[selected], payload)
    elif damage == 'missing_handoff': paths['handoff'].unlink()
    elif damage == 'oversized': paths['selection'].write_bytes(b' ' * (router.MAX_STARTUP_RECEIPT_BYTES + 1))
    elif damage == 'duplicate_key': paths['selection'].write_text('{"schema":1,"schema":2}')
    elif damage == 'fifo':
        paths['selection'].unlink()
        os.mkfifo(paths['selection'])
    elif damage == 'symlink':
        target=paths['selection'].with_suffix('.original.json')
        paths['selection'].replace(target)
        paths['selection'].symlink_to(target)
    result = router.startup_consumption_state(**expected)
    assert result['status'] == status and result['reason'] == reason


def test_startup_receipts_and_pid_rechecked_before_ready(release, monkeypatch):
    expected, paths, put = _startup_receipts(release, monkeypatch, intraday=True)
    original = router._startup_receipt
    calls = []
    def read(path):
        value = original(path)
        calls.append(path)
        if path == paths['verification'] and calls.count(path) == 2:
            paths['consumed'].write_text('{}')
        return value
    monkeypatch.setattr(router, '_startup_receipt', read)
    assert router.startup_consumption_state(**expected)['reason'] == 'startup_receipt_generation_changed'


@pytest.mark.parametrize('race_mode', ['once', 'persistent', 'wrong_identity'])
@pytest.mark.parametrize('race_location', ['during_read', 'between_reads'])
def test_actual_startup_receipt_read_race_uses_original_bot_deadline(release,monkeypatch,race_mode,race_location):
    import src.bot_main as bot_main
    import src.utils.logger as logger
    expected, paths, _ = _startup_receipts(release,monkeypatch,intraday=True)
    original_open=router.os.open
    original_receipt=router._startup_receipt
    original_selection=paths['selection'].read_bytes()
    replacements=[]
    def replace_receipt(path):
        if Path(path)==paths['selection'] and (not replacements or race_mode=='persistent'):
            replacement=paths['selection'].with_suffix('.race.json')
            value=json.loads(original_selection)
            if race_mode=='wrong_identity':value['git_commit']='c'*40
            value['receipt_publication_sequence']=len(replacements)
            replacement.write_text(json.dumps(value))
            replacement.replace(paths['selection'])
            replacements.append(True)
    def open_receipt(path,*args,**kwargs):
        if race_location=='during_read':replace_receipt(path)
        return original_open(path,*args,**kwargs)
    def read_receipt(path):
        value=original_receipt(path)
        if race_location=='between_reads':replace_receipt(path)
        return value
    monkeypatch.setattr(router.os,'open',open_receipt)
    monkeypatch.setattr(router,'_startup_receipt',read_receipt)
    monkeypatch.setattr(logger,'log_info',lambda message:None)
    clock=[149.5 if race_mode=='persistent' else 26.6]
    visits=[];waits=[];heartbeats=[]
    def check(identity):
        result=router.startup_consumption_state(**expected)
        visits.append(result)
        return result
    def wait(seconds):
        waits.append(seconds);clock[0]+=seconds
    result=bot_main._await_startup_consumption(dict(process_started_monotonic=0.),check=check,
        monotonic=lambda:clock[0],wait=wait,heartbeat=lambda:heartbeats.append(clock[0]))
    assert visits[0]['status']=='pending'
    assert visits[0]['reason']==('startup_receipt_changed_during_read' if race_location=='during_read'
                                 else 'startup_receipt_generation_changed')
    assert heartbeats
    if race_mode=='once':
        assert result['status']=='ready' and len(replacements)==1
        assert len(visits)==2 and waits==[.25] and clock[0]==26.85
    elif race_mode=='persistent':
        assert result['status']=='failed' and result['reason']=='startup_consumption_deadline_expired'
        assert sum(waits)==.5 and clock[0]==150. and result['waited_seconds']==.5
    else:
        assert result['status']=='failed' and result['reason']=='startup_selected_generation_changed'
        assert len(visits)==2 and waits==[.25]


def test_startup_process_reuse_during_receipt_read_is_permanent_failure(release,monkeypatch):
    expected,_,_=_startup_receipts(release,monkeypatch,intraday=True)
    calls=[]
    def ticks(pid):
        calls.append(pid)
        return '100' if len(calls)==1 else '999'
    monkeypatch.setattr(router,'_process_start_ticks',ticks)
    result=router.startup_consumption_state(**expected)
    assert result['status']=='failed' and result['reason']=='startup_process_identity_changed'


def test_failed_current_bootstrap_surfaces_before_final_pid_attestation(release, monkeypatch):
    expected, paths, put = _startup_receipts(release, monkeypatch)
    selection = json.loads(paths['selection'].read_text())
    selection['actual_pid_consumed'] = False
    put(paths['selection'], selection)
    verification = json.loads(paths['verification'].read_text())
    put(paths['verification'], dict(verification, status='fail', passed=False, pid_passed=False))
    assert router.startup_consumption_state(**expected)['reason'] == 'startup_bootstrap_pid_receipt_invalid'
    # A previous child's failure does not become this fresh launch's failure.
    put(paths['verification'], dict(verification, pid=9999, status='fail', passed=False))
    assert router.startup_consumption_state(**expected)['status'] == 'pending'


def _ordered_startup_receipts(release, monkeypatch, *, phase='starting', required=True):
    original_datetime = router.datetime
    class StartupClock(original_datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 10, 14, 15, tzinfo=router.ZoneInfo('Asia/Seoul'))
            return value.astimezone(tz) if tz is not None else value.replace(tzinfo=None)
    monkeypatch.setattr(router, 'datetime', StartupClock)
    expected, paths, put = _startup_receipts(release, monkeypatch, intraday=True)
    workspace, root = expected['workspace'], expected['release_root']
    path = workspace / 'data/runtime/release_transitions' / expected['target_date'] / expected['git_commit'] / 'status.json'
    selection = json.loads(paths['selection'].read_text())
    selection.update(approval_scope='ordered_intraday_deploy_and_restart', approved_by='user',
                     selected_at_kst='2026-10-14T14:00:00+09:00', deployment_transition=str(path))
    selection['actual_pid_receipt'].update(ordered_transition_required=required,
        recorded_at_kst='2026-10-14T14:01:00+09:00' if required else '2026-10-14T14:06:00+09:00')
    put(paths['selection'], selection)
    transition = dict(schema='ordered_intraday_deployment_v1', authority='APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART',
        target_date=expected['target_date'], candidate_root=str(root), candidate_commit=expected['git_commit'],
        phase=phase, policy_effect='unchanged', updated_at='2026-10-14T14:05:00+09:00')
    if phase == 'complete':
        transition.update(status='pass', successor_identity=dict(pid=1234, start_ticks='100', cwd=str(root / 'src')))
    put(path, transition)
    paths['transition'] = path
    return expected, paths, put


@pytest.mark.parametrize('phase', ['selected', 'prepared', 'starting', 'complete'])
def test_ordered_startup_waits_for_post_attestation_completion(release, monkeypatch, phase):
    expected, paths, put = _ordered_startup_receipts(release, monkeypatch, phase=phase)
    result = router.startup_consumption_state(**expected)
    assert result['status'] == ('ready' if phase == 'complete' else 'pending')
    if phase != 'complete': assert result['reason'] == 'waiting_ordered_transition_completion'


@pytest.mark.parametrize('damage, reason', [
    ('failed', 'startup_ordered_transition_failed'),
    ('root', 'startup_ordered_transition_identity_invalid'),
    ('commit', 'startup_ordered_transition_identity_invalid'),
    ('policy_effect', 'startup_ordered_transition_identity_invalid'),
    ('policy_effect_missing', 'startup_ordered_transition_identity_invalid'),
    ('approval', 'startup_ordered_transition_approval_invalid'),
    ('path', 'startup_ordered_transition_path_invalid'),
    ('false_while_active', 'startup_ordered_transition_receipt_invalid'),
    ('unknown_phase', 'startup_ordered_transition_state_invalid'),
    ('successor', 'startup_ordered_transition_successor_invalid'),
])
def test_ordered_startup_never_bypasses_a_failed_or_unbound_transition(release, monkeypatch, damage, reason):
    expected, paths, put = _ordered_startup_receipts(release, monkeypatch,
        phase='complete' if damage == 'successor' else 'starting')
    transition = json.loads(paths['transition'].read_text())
    selection = json.loads(paths['selection'].read_text())
    if damage == 'failed': transition.update(phase='failed', status='fail')
    elif damage in {'root', 'commit'}: transition['candidate_' + damage] = 'wrong'
    elif damage == 'policy_effect': transition['policy_effect'] = 'changed'
    elif damage == 'policy_effect_missing': transition.pop('policy_effect')
    elif damage == 'approval': selection['approval_scope'] = 'unapproved'
    elif damage == 'path':
        wrong = paths['transition'].parent / 'wrong.json'
        put(wrong, transition)
        selection['deployment_transition'] = str(wrong)
    elif damage == 'false_while_active': selection['actual_pid_receipt']['ordered_transition_required'] = False
    elif damage == 'unknown_phase': transition['phase'] = 'unknown'
    elif damage == 'successor': transition['successor_identity']['start_ticks'] = '999'
    put(paths['selection'], selection); put(paths['transition'], transition)
    assert router.startup_consumption_state(**expected)['reason'] == reason


def test_record_pid_derives_active_ordered_barrier_and_preserves_it_after_completion(release, monkeypatch):
    expected, paths, put = _ordered_startup_receipts(release, monkeypatch, required=False)
    recorded = router.record_runtime_pid_consumption(expected['workspace'], pid=expected['pid'],
        release_root=expected['release_root'], git_commit=expected['git_commit'])
    assert recorded['ordered_transition_required'] is True
    transition = json.loads(paths['transition'].read_text())
    transition.update(phase='complete', status='pass', successor_identity=dict(pid=1234,
        start_ticks='100', cwd=str(expected['release_root'] / 'src')))
    put(paths['transition'], transition)
    again = router.record_runtime_pid_consumption(expected['workspace'], pid=expected['pid'],
        release_root=expected['release_root'], git_commit=expected['git_commit'])
    assert again['ordered_transition_required'] is True


def test_same_release_later_restart_uses_fresh_consumption_not_historical_successor_pid(release, monkeypatch):
    expected, paths, put = _ordered_startup_receipts(release, monkeypatch, phase='complete', required=False)
    transition = json.loads(paths['transition'].read_text())
    transition['successor_identity']['pid'] = 9999
    put(paths['transition'], transition)
    selection = json.loads(paths['selection'].read_text())
    selection['actual_pid_receipt']['pid'] = 9999
    put(paths['selection'], selection)
    current = router.record_runtime_pid_consumption(expected['workspace'], pid=expected['pid'],
        release_root=expected['release_root'], git_commit=expected['git_commit'])
    assert current['ordered_transition_required'] is False
    assert router.startup_consumption_state(**expected)['status'] == 'ready'


def test_next_date_native_preopen_is_not_blocked_by_completed_previous_day_transition(release, monkeypatch):
    expected, paths, put = _ordered_startup_receipts(release, monkeypatch, phase='complete', required=False)
    expected['target_date'] = '2026-10-15'
    selection = json.loads(paths['selection'].read_text())
    selection['actual_pid_receipt']['recorded_at_kst'] = '2026-10-15T07:55:00+09:00'
    put(paths['selection'], selection)
    manifest = dict(target_date=expected['target_date'], selected_release_sha=expected['git_commit'])
    manifest['manifest_sha256'] = hashlib.sha256(json.dumps(manifest, ensure_ascii=True,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    directory = expected['workspace'] / 'data/runtime/policy_bootstrap'
    put(directory / 'runtime_policy_bootstrap_2026-10-15.json', manifest)
    put(directory / 'runtime_policy_bootstrap_verify_2026-10-15.json', dict(target_date=expected['target_date'],
        status='pass', passed=True, pid=expected['pid'], pid_passed=True, pid_env_available=True,
        manifest_sha256=manifest['manifest_sha256']))
    assert router.startup_consumption_state(**expected)['status'] == 'ready'


def test_ordered_completion_is_rechecked_before_ready(release, monkeypatch):
    expected, paths, put = _ordered_startup_receipts(release, monkeypatch, phase='complete')
    original = router._startup_receipt
    count = [0]
    def read(path):
        count[0] += 1
        if path == paths['transition'] and count[0] > 2:
            payload = json.loads(path.read_text())
            put(path, dict(payload, phase='failed', status='fail'))
        return original(path)
    monkeypatch.setattr(router, '_startup_receipt', read)
    assert router.startup_consumption_state(**expected)['reason'] == 'startup_ordered_transition_generation_changed'


def test_launcher_uses_reviewed_selected_router_after_policy_consumption():
    text = (Path(__file__).resolve().parents[1] / 'run_bot.sh').read_text()
    final = text.index('if record_threshold_runtime_env_pid_handoff "$RUNTIME_TARGET_DATE" "$BOT_PID"; then')
    selected = text.index('../.venv/bin/python -I "$PROJECT_DIR/src/engine/infrastructure/runtime_release_router.py"', final)
    assert selected > final
    assert '--workspace "$RUNTIME_WORKSPACE"' in text[selected:selected+350]
    assert '--record-pid "$BOT_PID"' in text[selected:selected+350]


def test_pid_receipt_rejects_non_release_child_cwd(release, monkeypatch):
    workspace, root, _, _ = release
    (root / "src").mkdir()
    real_readlink = router.os.readlink
    monkeypatch.setattr(
        router.os,
        "readlink",
        lambda path: str(workspace)
        if str(path).startswith("/proc/")
        else real_readlink(path),
    )

    with pytest.raises(ValueError, match="cwd_mismatch"):
        router.record_runtime_pid_consumption(
            workspace,
            pid=1234,
            release_root=root,
            git_commit="a" * 40,
        )


@pytest.mark.parametrize("custody_failure", [False, True])
def test_privileged_pid_writer_preserves_selector_custody(
    release, monkeypatch, custody_failure
):
    workspace, root, manifest, _ = release
    (root / "src").mkdir()
    manifest.chmod(0o600)
    original_bytes = manifest.read_bytes()
    original_stat = Path.stat
    original_readlink = os.readlink
    original_replace = os.replace
    calls = []

    def stat_as_cron_owner(path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if path == manifest:
            fields = list(result)
            fields[4:6] = [40001, 40002]
            return os.stat_result(fields)
        return result

    def preserve_owner(path, uid, gid):
        calls.append(("chown", uid, gid))
        assert Path(path).stat().st_mode & 0o777 == 0o600
        assert manifest.read_bytes() == original_bytes
        if custody_failure:
            raise PermissionError("custody_denied")

    def publish(path, target):
        assert calls == [("chown", 40001, 40002)]
        calls.append(("replace",))
        return original_replace(path, target)

    monkeypatch.setattr(Path, "stat", stat_as_cron_owner)
    monkeypatch.setattr(os, "chown", preserve_owner)
    monkeypatch.setattr(os, "replace", publish)
    monkeypatch.setattr(
        os, "readlink", lambda path: str(root / "src")
        if str(path).startswith("/proc/") else original_readlink(path)
    )
    if custody_failure:
        with pytest.raises(PermissionError, match="custody_denied"):
            router.record_runtime_pid_consumption(
                workspace, pid=1234, release_root=root, git_commit="a" * 40
            )
        assert manifest.read_bytes() == original_bytes
        assert calls == [("chown", 40001, 40002)]
    else:
        router.record_runtime_pid_consumption(
            workspace, pid=1234, release_root=root, git_commit="a" * 40
        )
        assert json.loads(manifest.read_text())["actual_pid_receipt"]["pid"] == 1234
        assert calls == [("chown", 40001, 40002), ("replace",)]
    assert manifest.stat().st_mode & 0o777 == 0o600
    assert sorted(p.name for p in manifest.parent.iterdir()) == [
        "runtime_release_selection.json", "runtime_release_selection.lock"
    ]


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema", "unknown"),
        ("workspace", "/wrong"),
        ("release_root", "relative"),
        ("git_commit", "abc"),
        ("git_commit", "b" * 40),
    ],
)
def test_bad_selection_rejected(release, key, value):
    workspace, _, manifest, selection = release
    selection[key] = value
    manifest.write_text(json.dumps(selection))
    with pytest.raises(ValueError):
        router.selected_release(workspace)


def test_candidate_validation_does_not_publish_or_require_candidate_selection(release):
    workspace, root, manifest, selection = release
    original = manifest.read_bytes()
    # Candidate validation uses the same full immutable-release contract and
    # does not depend on publishing this identity for live readers first.
    manifest.write_text('{"unpublished": true}')
    before = manifest.read_bytes()
    assert router.validate_release(workspace, selection) == (root, selection['git_commit'])
    assert manifest.read_bytes() == before
    manifest.write_bytes(original)


@pytest.mark.parametrize("payload", ["[]", "null", "{invalid"])
def test_bad_json_rejected(release, payload):
    workspace, _, manifest, _ = release
    manifest.write_text(payload)
    with pytest.raises(ValueError):
        router.selected_release(workspace)


def test_runtime_release_set_lock_is_nonblocking(release):
    workspace, _, _, _ = release
    with router.runtime_release_set_lock(workspace):
        with pytest.raises(ValueError, match="transition_in_progress"):
            with router.runtime_release_set_lock(workspace):
                pass


def test_release_set_check_keeps_separate_owner_pins(release, monkeypatch):
    workspace, root, _, _ = release
    other = workspace.parent / f"{workspace.name}-runtime-releases" / "episode"
    other.mkdir()
    policy = workspace / "data" / "machine-policy.json"
    policy.write_text('{"policy":"current"}')
    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    profile = "korstockscan-low-price-two-leg@tym_late_morning.service"
    monkeypatch.setattr(
        router.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, f"{profile} loaded inactive dead description\n", ""
        ),
    )

    def show(unit, **kwargs):
        route = other if unit == profile else root
        environment = (
            f"SAMPLE_POLICY_PATH={policy} SAMPLE_POLICY_SHA256={digest}"
            if unit == profile
            else ""
        )
        return {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "MainPID": "0",
            "WorkingDirectory": str(route),
            "ExecStart": f"{{ path={route}/deploy/run_owner.sh ; argv[]=... }}",
            "Environment": environment,
        }

    monkeypatch.setattr(router, "_systemd_properties", show)
    report = router.check_release_set(workspace, root, "a" * 40)

    assert report["status"] == "passed"
    assert report["owner_count"] == 2
    assert {item["release_root"] for item in report["systemd_owners"]} == {str(root)}
    assert report["episode_profile_inventory"]["loaded_units_checked"] == 1


def test_release_set_rejects_policy_hash_mismatch(release, monkeypatch, tmp_path):
    workspace, root, _, _ = release
    policy = tmp_path / "policy.json"
    policy.write_text("expected")
    with pytest.raises(ValueError, match="hash_mismatch"):
        router._policy_environment_status(
            f"SAMPLE_POLICY_PATH={policy} SAMPLE_POLICY_SHA256={'0' * 64}",
            "sample.service",
        )


def test_outside_root_rejected(release):
    workspace, _, manifest, selection = release
    selection["release_root"] = str(workspace)
    manifest.write_text(json.dumps(selection))
    with pytest.raises(ValueError, match="outside_managed"):
        router.selected_release(workspace)


def test_dirty_source_rejected(release, monkeypatch):
    workspace, _, _, _ = release
    monkeypatch.setattr(
        router,
        "git",
        lambda _, *args: "a" * 40 if args[0] == "rev-parse" else " M src/file.py",
    )
    with pytest.raises(ValueError, match="source_dirty"):
        router.selected_release(workspace)


@pytest.mark.parametrize(
    "name", ["docs", "data", "logs", "tmp", ".venv", "restart.flag"]
)
def test_split_shared_state_rejected(release, name):
    workspace, root, _, _ = release
    (root / name).unlink()
    (root / name).mkdir()
    with pytest.raises(ValueError, match="shared_path_mismatch"):
        router.selected_release(workspace)


@pytest.mark.parametrize("op", router.OPERATIONS)
def test_all_operations_pin_release_and_target_date(release, op):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, op, "2026-09-11")
    assert plan["release_root"] == str(root)
    assert plan["target_date"] == "2026-09-11"
    assert str(root) in " ".join(plan["command"])
    assert "existing_exact_date_gates_unchanged" == plan["policy_authority"]
    if op in router.OWNED or op == "paired-replay":
        expected = "--resolve-effective-today" if op == "finalize" else "2026-09-11"
        assert plan["command"][-1] == expected
    if op == "start":
        assert f"PYTHONPATH={root}" in plan["command"][-1]
        assert plan["cwd"] == str(root / "src")


@pytest.mark.parametrize(
    "value", ["2026-9-11", "2026-09-31", "20260911", "2026-09-11; touch /tmp/no"]
)
def test_invalid_date_rejected(release, value):
    workspace, root, _, _ = release
    with pytest.raises(ValueError):
        router.make_plan(workspace, root, "a" * 40, "postclose", value)


def original_cron(workspace):
    lines = [
        "# unchanged",
        "* * * * * /unrelated/widget",
        "30 7 * * 1-5 /usr/bin/tmux kill-session -t bot",
        f"55 7 * * 1-5 /usr/bin/tmux new-session -d -s bot 'cd {workspace}/src && ./run_bot.sh'",
    ]
    for tag, op in router.TAGS.items():
        if op in router.OWNED:
            script, owner = router.OWNED[op]
            cmd = (
                f"bash {workspace}/deploy/run_with_owned_log.sh --owner {owner} "
                f"--log {workspace}/logs/{owner}.log {workspace}/deploy/run_{script}.sh"
            )
        elif op == "paired-replay":
            cmd = f"{workspace}/deploy/run_ai_entry_setup_paired_replay_postclose.sh"
        elif op == "eod":
            cmd = f"cd {workspace} && {workspace}/.venv/bin/python src/utils/update_kospi.py"
        else:
            cmd = f"{workspace}/deploy/run_dashboard_db_archive_cron.sh 0"
        tail = (
            " $(TZ=Asia/Seoul date +\\%F)"
            if op in router.OWNED or op == "paired-replay"
            else ""
        )
        lines.append(
            f"10 20 * * 1-5 KEEP_POLICY_ENV=true {cmd}{tail} >> /preserved.log 2>&1 # {tag}"
        )
    return "\n".join(lines) + "\n"


def test_cron_preserves_unrelated_env_schedule_date_and_logs(tmp_path):
    before = original_cron(tmp_path)
    after = router.render_crontab(before, tmp_path)
    assert after.splitlines()[:3] == before.splitlines()[:3]
    assert after.count("run_runtime_release.sh") == len(router.CRON_TARGETS)
    assert "AI_ENTRY_SETUP_PAIRED_REPLAY_POSTCLOSE" not in after
    assert after.count("KEEP_POLICY_ENV=true") == len(router.TAGS)
    assert after.count("$(TZ=Asia/Seoul date +\\%F)") == len(router.OWNED) - 1
    assert "0 6 * * * KEEP_POLICY_ENV=true bash " not in after
    assert "run_runtime_release.sh finalize --resolve-effective-today" in after
    assert "POSTCLOSE_FINALIZATION_0535" in after
    assert "35 5 * * * KEEP_POLICY_ENV=true bash " in after
    assert "POSTCLOSE_FINALIZATION_0500" not in after
    assert "POSTCLOSE_FINALIZATION_2155" not in after
    assert "POSTCLOSE_FINALIZATION_0600" not in after
    assert after.count(">> /preserved.log 2>&1") == len(router.TAGS)
    assert router.render_crontab(after, tmp_path) == after


def snapshot_cron(workspace):
    logger = (
        f"bash {workspace}/deploy/run_with_owned_log.sh --owner run_monitor_snapshot_cron "
        f"--log {workspace}/logs/run_monitor_snapshot_cron.log "
    )
    producer = f"{workspace}/deploy/run_monitor_snapshot_incremental_cron.sh"
    return "\n".join([
        f"35-55/20 9 * * 1-5 {logger}{producer} # RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09",
        f"*/20 10-11 * * 1-5 {logger}{producer} # RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11",
        f"0 12 * * 1-5 MONITOR_SNAPSHOT_START_JITTER_SEC=0 {logger}{producer} # RUN_MONITOR_SNAPSHOT_1200",
    ]) + "\n"


def test_snapshot_cron_changes_only_three_inner_commands_and_is_idempotent(tmp_path):
    incumbent = router.render_crontab(original_cron(tmp_path), tmp_path)
    before = incumbent + snapshot_cron(tmp_path)
    after = router.render_crontab(before, tmp_path)
    date_arg = r" $(TZ=Asia/Seoul date +\%F)"
    expected = before.replace(
        f"{tmp_path}/deploy/run_monitor_snapshot_incremental_cron.sh",
        f"bash {tmp_path}/deploy/run_runtime_release.sh monitor-snapshot{date_arg}",
    )
    assert after == expected
    assert sum(a != b for a, b in zip(before.splitlines(), after.splitlines())) == 3
    assert len(before.splitlines()) == len(after.splitlines())
    assert after.startswith(incumbent)
    assert after.count("--owner run_monitor_snapshot_cron ") == 3
    assert after.count(f"--log {tmp_path}/logs/run_monitor_snapshot_cron.log ") == 3
    assert "0 12 * * 1-5 MONITOR_SNAPSHOT_START_JITTER_SEC=0 " in after
    assert router.render_crontab(after, tmp_path) == after


@pytest.mark.parametrize("kept", [1, 2])
def test_partial_snapshot_group_fails_closed(tmp_path, kept):
    before = original_cron(tmp_path) + "\n".join(snapshot_cron(tmp_path).splitlines()[:kept]) + "\n"
    with pytest.raises(ValueError, match="cron_snapshot_target_missing_or_duplicate"):
        router.render_crontab(before, tmp_path)


def test_strict_cron_transform_requires_snapshot_presence_without_breaking_legacy_api(tmp_path):
    before = original_cron(tmp_path)
    assert router.render_crontab(before, tmp_path)
    with pytest.raises(ValueError, match="cron_snapshot_target_missing_or_duplicate"):
        router.render_crontab(before, tmp_path, require_snapshot_group=True)


@pytest.mark.parametrize("mode", ["--check-cron", "--install-cron"])
@pytest.mark.parametrize("with_snapshots", [False, True])
def test_operational_cron_cli_requires_all_snapshot_tags_before_any_install(
    release, monkeypatch, capsys, mode, with_snapshots
):
    workspace, _, _, _ = release
    before = original_cron(workspace) + (snapshot_cron(workspace) if with_snapshots else "")
    current = router.render_crontab(before, workspace)
    monkeypatch.setattr(router, "__file__", str(workspace / "src/engine/infrastructure/runtime_release_router.py"))
    monkeypatch.setattr(router.sys, "argv", ["router", mode])
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: current)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("must not write the crontab"))
    monkeypatch.setattr(router.os, "execvpe", lambda *a: pytest.fail("cron mode cannot execute a worker"))
    assert router.main() == (0 if with_snapshots else 2)
    captured = capsys.readouterr()
    if with_snapshots:
        assert json.loads(captured.out)["snapshot_targets"] == 3
    else:
        assert "cron_snapshot_target_missing_or_duplicate" in captured.err
        assert not captured.out
        assert not list((workspace / "tmp").glob("runtime-release-cron-*"))


@pytest.mark.parametrize("duplicate_index", [0, 1, 2])
def test_duplicate_snapshot_tag_fails_closed(tmp_path, duplicate_index):
    snapshots = snapshot_cron(tmp_path)
    before = original_cron(tmp_path) + snapshots + snapshots.splitlines()[duplicate_index] + "\n"
    with pytest.raises(ValueError, match="cron_snapshot_target_missing_or_duplicate"):
        router.render_crontab(before, tmp_path)


@pytest.mark.parametrize("routed", [False, True])
@pytest.mark.parametrize("damage", [
    "echo", "conditional", "printf", "wrong_owner", "wrong_log", "inner_echo",
    "selected_path", "without_logger", "wrong_operation",
])
def test_snapshot_cron_rejects_deceptive_or_changed_execution_owner(tmp_path, routed, damage):
    before = router.render_crontab(original_cron(tmp_path), tmp_path) + snapshot_cron(tmp_path)
    if routed:
        before = router.render_crontab(before, tmp_path)
    lines = before.splitlines()
    target = lines[-1]
    logger = f"bash {tmp_path}/deploy/run_with_owned_log.sh"
    producer = (f"bash {tmp_path}/deploy/run_runtime_release.sh monitor-snapshot"
                if routed else f"{tmp_path}/deploy/run_monitor_snapshot_incremental_cron.sh")
    if damage in {"echo", "conditional", "printf"}:
        prefix = {"echo": "echo ", "conditional": "false && ", "printf": "printf '%s' "}[damage]
        target = target.replace(logger, prefix + logger)
    elif damage == "wrong_owner":
        target = target.replace("--owner run_monitor_snapshot_cron", "--owner another_worker")
    elif damage == "wrong_log":
        target = target.replace("logs/run_monitor_snapshot_cron.log", "logs/another_worker.log")
    elif damage == "inner_echo":
        target = target.replace(producer, "echo " + producer)
    elif damage == "selected_path":
        target = target.replace(producer, "/immutable-release/deploy/run_monitor_snapshot_incremental_cron.sh")
    elif damage == "without_logger":
        start = target.index(logger)
        target = target[:start] + target[target.index(producer, start):]
    else:
        target = target.replace(producer, producer + "-unexpected")
    lines[-1] = target
    with pytest.raises(ValueError, match="cron_command_unrecognized:monitor-snapshot"):
        router.render_crontab("\n".join(lines) + "\n", tmp_path)


@pytest.mark.parametrize("routed", [False, True])
@pytest.mark.parametrize("argument", [
    "--print-plan", "2026-10-16", "--workspace /recovery", "--record-pid 1234",
    "--resolve-effective-today", "--install-cron", "; echo changed", "&& echo changed",
])
def test_snapshot_cron_rejects_extra_arguments_and_recovery_modes(tmp_path, routed, argument):
    before = original_cron(tmp_path) + snapshot_cron(tmp_path)
    if routed:
        before = router.render_crontab(before, tmp_path)
    before = before.replace(" # RUN_MONITOR_SNAPSHOT_1200", f" {argument} # RUN_MONITOR_SNAPSHOT_1200")
    with pytest.raises(ValueError, match="cron_arguments_unrecognized:monitor-snapshot"):
        router.render_crontab(before, tmp_path)


def test_routed_snapshot_requires_explicit_canonical_kst_date(tmp_path):
    before = router.render_crontab(original_cron(tmp_path) + snapshot_cron(tmp_path), tmp_path)
    before = before.replace(r"monitor-snapshot $(TZ=Asia/Seoul date +\%F)", "monitor-snapshot", 1)
    with pytest.raises(ValueError, match="cron_target_date_unrecognized:monitor-snapshot"):
        router.render_crontab(before, tmp_path)


def test_snapshot_cron_preserves_leading_environment_and_redirections(tmp_path):
    before = original_cron(tmp_path) + snapshot_cron(tmp_path).replace(
        "MONITOR_SNAPSHOT_START_JITTER_SEC=0 ", "MONITOR_SNAPSHOT_START_JITTER_SEC=0 KEEP='a value' "
    ).replace(" # RUN_MONITOR_", " >> /existing-snapshot.log 2>&1 # RUN_MONITOR_")
    after = router.render_crontab(before, tmp_path)
    assert "MONITOR_SNAPSHOT_START_JITTER_SEC=0 KEEP='a value' " in after
    assert after.count(" >> /existing-snapshot.log 2>&1 # RUN_MONITOR_") == 3
    assert router.render_crontab(after, tmp_path) == after


@pytest.mark.parametrize("with_snapshots", [False, True])
def test_cron_check_reports_pipeline_and_snapshot_counts_separately(release, monkeypatch, capsys, with_snapshots):
    workspace, _, _, _ = release
    before = original_cron(workspace) + (snapshot_cron(workspace) if with_snapshots else "")
    current = router.render_crontab(before, workspace)
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: current)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("read-only check cannot install"))
    router.manage_cron(workspace, False)
    assert json.loads(capsys.readouterr().out) == {
        "cron_routing_verified": True, "required_targets": 8,
        "snapshot_targets": 3 if with_snapshots else 0,
    }
    assert not (workspace / "data/runtime/runtime_release_cron.lock").exists()


def test_snapshot_install_uses_existing_backup_compare_write_and_readback(release, monkeypatch, capsys):
    workspace, _, _, _ = release
    before = router.render_crontab(original_cron(workspace), workspace) + snapshot_cron(workspace)
    after = router.render_crontab(before, workspace)
    readings = iter([before, before, after])
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: next(readings))
    writes = []
    monkeypatch.setattr(subprocess, "run", lambda command, **kwargs: writes.append((command, kwargs["input"])))
    router.manage_cron(workspace, True)
    assert writes == [(["crontab", "-"], after)]
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    backup = Path(reports[0]["cron_backup"])
    assert (backup / "before.crontab").read_text() == before
    assert (backup / "after.crontab").read_text() == after
    assert reports[-1]["required_targets"] == 8 and reports[-1]["snapshot_targets"] == 3


def test_old_five_am_finalization_migrates_without_changing_other_jobs(tmp_path):
    current = router.render_crontab(original_cron(tmp_path), tmp_path)
    old = current.replace("35 5 * * *", "0 5 * * *").replace(
        "POSTCLOSE_FINALIZATION_0535", "POSTCLOSE_FINALIZATION_0500"
    )
    assert router.render_crontab(old, tmp_path) == current



@pytest.mark.parametrize("mode", ["missing", "duplicate", "unexpected_command"])
def test_cron_drift_blocks_install(tmp_path, mode):
    before = original_cron(tmp_path)
    if mode == "missing":
        before = "\n".join(
            line
            for line in before.splitlines()
            if "# THRESHOLD_CYCLE_POSTCLOSE" not in line
        )
    elif mode == "duplicate":
        before += before.splitlines()[-1] + "\n"
    else:
        before = before.replace("run_threshold_cycle_postclose.sh", "unexpected.sh")
    with pytest.raises(ValueError):
        router.render_crontab(before, tmp_path)


@pytest.mark.parametrize("tag", sorted(router.TAGS))
def test_cron_rejects_missing_scheduled_postclose_owner(tmp_path, tag):
    before = "\n".join(
        line for line in original_cron(tmp_path).splitlines()
        if f"# {tag}" not in line
    ) + "\n"
    with pytest.raises(ValueError, match="cron_target_missing_or_duplicate"):
        router.render_crontab(before, tmp_path)


def test_cron_check_never_installs(release, monkeypatch):
    workspace, _, _, _ = release
    monkeypatch.setattr(
        subprocess, "check_output", lambda *a, **k: original_cron(workspace)
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not install")
    )
    with pytest.raises(ValueError, match="not_installed"):
        router.manage_cron(workspace, False)


def test_cron_wrong_operation_prefix_is_not_a_valid_route(tmp_path):
    valid = router.render_crontab(original_cron(tmp_path), tmp_path)
    invalid = valid.replace(
        "run_runtime_release.sh postclose ", "run_runtime_release.sh postclose-invalid "
    )
    with pytest.raises(ValueError, match="command_unrecognized"):
        router.render_crontab(invalid, tmp_path)


def test_cron_concurrent_edit_prevents_write(release, monkeypatch):
    workspace, _, _, _ = release
    values = iter(
        [original_cron(workspace), original_cron(workspace) + "# concurrent\n"]
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: next(values))
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not overwrite")
    )
    with pytest.raises(ValueError, match="changed_during_install"):
        router.manage_cron(workspace, True)


def test_print_plan_never_starts_or_restarts(release, monkeypatch, capsys):
    workspace, root, _, _ = release
    monkeypatch.setattr(
        router,
        "__file__",
        str(workspace / "src/engine/infrastructure/runtime_release_router.py"),
    )
    monkeypatch.setattr(router.sys, "argv", ["router", "restart", "--print-plan"])
    monkeypatch.setattr(
        router.os, "execvpe", lambda *a: pytest.fail("must not execute")
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not start")
    )
    assert router.main() == 0
    assert json.loads(capsys.readouterr().out)["release_root"] == str(root)


def test_archive_recovery_preserves_explicit_source_date(release,monkeypatch):
    workspace,root,_,_=release
    monkeypatch.setattr(router,'__file__',str(workspace/'src/engine/infrastructure/runtime_release_router.py'))
    monkeypatch.setattr(router.sys,'argv',['router','archive','2026-10-07'])
    monkeypatch.setattr(router.os,'chdir',lambda *a:None)
    captured=[]
    monkeypatch.setattr(router.os,'execvpe',lambda executable,command,env:captured.append((command,env)))
    router.main()
    command,env=captured[0]
    assert command[-1]=='0' and env['TARGET_DATE']=='2026-10-07'
    assert env['PROJECT_DIR']==str(root)


def test_snapshot_plan_targets_selected_incremental_wrapper_with_exact_date(release):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, "monitor-snapshot", "2026-10-19")
    assert "monitor-snapshot" not in router.OWNED
    assert plan["command"] == [
        "/bin/bash", str(root / "deploy/run_monitor_snapshot_incremental_cron.sh"), "2026-10-19",
    ]
    assert plan["cwd"] == str(root)
    assert plan["git_commit"] == "a" * 40
    assert plan["policy_authority"] == "existing_exact_date_gates_unchanged"


def test_snapshot_route_overrides_inherited_workspace_environment_for_child(release, monkeypatch):
    workspace, root, manifest, _ = release
    before = manifest.read_bytes()
    monkeypatch.setattr(router, "__file__", str(workspace / "src/engine/infrastructure/runtime_release_router.py"))
    monkeypatch.setattr(router.sys, "argv", ["router", "monitor-snapshot", "2026-10-19"])
    for key in ("PROJECT_DIR", "PYTHONPATH", "VENV_PY", "KORSTOCKSCAN_PROJECT_DIR",
                "KORSTOCKSCAN_PYTHON_BIN", "KORSTOCKSCAN_RUNTIME_GIT_COMMIT", "PYTHONHOME"):
        monkeypatch.setenv(key, "/mutable-or-previous-release")
    monkeypatch.setenv("MONITOR_SNAPSHOT_START_JITTER_SEC", "0")
    monkeypatch.setenv("MONITOR_SNAPSHOT_ASYNC", "1")
    changed = []
    monkeypatch.setattr(router.os, "chdir", lambda path: changed.append(path))
    executed = []
    monkeypatch.setattr(router.os, "execvpe", lambda executable, command, env: executed.append((executable, command, env)))
    assert router.main() == 0
    assert changed == [str(root)]
    executable, command, env = executed[0]
    assert executable == "/bin/bash"
    assert command == ["/bin/bash", str(root / "deploy/run_monitor_snapshot_incremental_cron.sh"), "2026-10-19"]
    for key in ("PROJECT_DIR", "PYTHONPATH", "KORSTOCKSCAN_PROJECT_DIR"):
        assert env[key] == str(root)
    for key in ("VENV_PY", "KORSTOCKSCAN_PYTHON_BIN"):
        assert env[key] == str(root / ".venv/bin/python")
    assert env["KORSTOCKSCAN_RUNTIME_GIT_COMMIT"] == "a" * 40
    assert "PYTHONHOME" not in env
    assert env["MONITOR_SNAPSHOT_START_JITTER_SEC"] == "0" and env["MONITOR_SNAPSHOT_ASYNC"] == "1"
    assert manifest.read_bytes() == before


def test_snapshot_print_plan_never_dispatches_or_records_pid(release, monkeypatch, capsys):
    workspace, root, manifest, _ = release
    before = manifest.read_bytes()
    monkeypatch.setattr(router, "__file__", str(workspace / "src/engine/infrastructure/runtime_release_router.py"))
    monkeypatch.setattr(router.sys, "argv", ["router", "monitor-snapshot", "2026-10-19", "--print-plan"])
    monkeypatch.setattr(router.os, "execvpe", lambda *a: pytest.fail("plan cannot dispatch"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("plan cannot start a process"))
    assert router.main() == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["command"][-1] == "2026-10-19" and plan["cwd"] == str(root)
    assert manifest.read_bytes() == before


@pytest.mark.parametrize("damage", ["missing", "invalid"])
def test_snapshot_route_fails_closed_without_valid_selection(release, monkeypatch, capsys, damage):
    workspace, _, manifest, _ = release
    if damage == "missing":
        manifest.unlink()
    else:
        manifest.write_text("{}")
    monkeypatch.setattr(router, "__file__", str(workspace / "src/engine/infrastructure/runtime_release_router.py"))
    monkeypatch.setattr(router.sys, "argv", ["router", "monitor-snapshot", "2026-10-19"])
    monkeypatch.setattr(router.os, "execvpe", lambda *a: pytest.fail("invalid selection cannot dispatch"))
    assert router.main() == 2
    assert "runtime_release_route_blocked" in capsys.readouterr().err


def test_snapshot_route_cannot_select_recovery_workspace(release, monkeypatch, capsys):
    workspace, _, _, _ = release
    monkeypatch.setattr(router, "__file__", str(workspace / "src/engine/infrastructure/runtime_release_router.py"))
    monkeypatch.setattr(router.sys, "argv", ["router", "monitor-snapshot", "--workspace", str(workspace)])
    monkeypatch.setattr(router.os, "execvpe", lambda *a: pytest.fail("recovery selector cannot dispatch"))
    assert router.main() == 2
    assert "runtime_pid_workspace_record_only" in capsys.readouterr().err


def test_scheduled_finalizer_argument_resolves_through_runtime_router(
    release, monkeypatch, capsys
):
    workspace, root, _, _ = release
    monkeypatch.setattr(
        router,
        "__file__",
        str(workspace / "src/engine/infrastructure/runtime_release_router.py"),
    )
    monkeypatch.setattr(
        router.sys,
        "argv",
        ["router", "finalize", "--resolve-effective-today", "--print-plan"],
    )
    monkeypatch.setattr(
        router.os, "execvpe", lambda *a: pytest.fail("must not execute")
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not start")
    )

    assert router.main() == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["release_root"] == str(root)
    assert plan["operation"] == "finalize"
    assert plan["command"][-1] == "--resolve-effective-today"


def test_resolve_effective_today_is_rejected_for_other_operations(
    release, monkeypatch, capsys
):
    workspace, _, _, _ = release
    monkeypatch.setattr(
        router,
        "__file__",
        str(workspace / "src/engine/infrastructure/runtime_release_router.py"),
    )
    monkeypatch.setattr(
        router.sys,
        "argv",
        ["router", "postclose", "--resolve-effective-today"],
    )
    assert router.main() == 2
    assert "resolve_effective_today_requires_finalize" in capsys.readouterr().err


def test_missing_manifest_cannot_fall_back_to_workspace(release, monkeypatch, capsys):
    workspace, _, manifest, _ = release
    manifest.unlink()
    monkeypatch.setattr(
        router,
        "__file__",
        str(workspace / "src/engine/infrastructure/runtime_release_router.py"),
    )
    monkeypatch.setattr(router.sys, "argv", ["router", "start"])
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not start")
    )
    assert router.main() == 2
    assert "runtime_release_route_blocked" in capsys.readouterr().err


def test_cron_install_backups_and_readback(release, monkeypatch):
    workspace, _, _, _ = release
    before = original_cron(workspace)
    after = router.render_crontab(before, workspace)
    readings = iter([before, before, after])
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: next(readings))
    writes = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: writes.append(k["input"]))
    router.manage_cron(workspace, True)
    assert writes == [after]
    backups = list((workspace / "tmp").glob("runtime-release-cron-*"))
    assert len(backups) == 1
    assert (backups[0] / "before.crontab").read_text() == before


def test_start_route_preserves_operator_env_and_log(tmp_path):
    original = router.render_crontab(original_cron(tmp_path), tmp_path)
    with_override = original.replace(
        f"55 7 * * 1-5 bash {tmp_path}/deploy/run_runtime_release.sh start #",
        f"55 7 * * 1-5 MAIN_OPERATOR_VETO=true bash {tmp_path}/deploy/run_runtime_release.sh start >> /start.log 2>&1 #",
    )
    assert router.render_crontab(with_override, tmp_path) == with_override


@pytest.mark.parametrize("prefix", ["echo ", "false && ", "printf '%s' "])
def test_quoted_or_nonexecuted_route_is_not_installed(tmp_path, prefix):
    original = router.render_crontab(original_cron(tmp_path), tmp_path)
    invalid = original.replace(
        f"KEEP_POLICY_ENV=true bash {tmp_path}/deploy/run_runtime_release.sh postclose ",
        f"KEEP_POLICY_ENV=true {prefix}bash {tmp_path}/deploy/run_runtime_release.sh postclose ",
    )
    with pytest.raises(ValueError, match="command_unrecognized"):
        router.render_crontab(invalid, tmp_path)


def test_check_cron_does_not_create_lock(release, monkeypatch):
    workspace, _, _, _ = release
    current = router.render_crontab(original_cron(workspace), workspace)
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: current)
    router.manage_cron(workspace, False)
    assert not (workspace / "data/runtime/runtime_release_cron.lock").exists()


@pytest.mark.parametrize("op", ["postclose", "start"])
def test_scheduled_dry_run_is_not_a_worker(tmp_path, op):
    current = router.render_crontab(original_cron(tmp_path), tmp_path)
    bad = current.replace(
        f"run_runtime_release.sh {op} ", f"run_runtime_release.sh {op} --print-plan "
    )
    with pytest.raises(ValueError, match="unrecognized"):
        router.render_crontab(bad, tmp_path)


def test_legacy_start_preserves_environment_and_redirect(tmp_path):
    current = original_cron(tmp_path)
    old = f"/usr/bin/tmux new-session -d -s bot 'cd {tmp_path}/src && ./run_bot.sh'"
    actual = (
        f"MAIN_OPERATOR_VETO=true /usr/bin/tmux new-session -d -s bot '/bin/bash -c \"cd {tmp_path}/src "
        "&& source ../.venv/bin/activate && ./run_bot.sh\"' >> /start.log 2>&1"
    )
    current = current.replace(old, actual)
    result = router.render_crontab(current, tmp_path)
    assert (
        f"MAIN_OPERATOR_VETO=true bash {tmp_path}/deploy/run_runtime_release.sh start >> /start.log 2>&1 # RUNTIME_RELEASE_START"
        in result
    )
    assert router.render_crontab(result, tmp_path) == result


def test_quoted_leading_assignment_is_preserved(tmp_path):
    current = router.render_crontab(original_cron(tmp_path), tmp_path)
    current = current.replace(
        "KEEP_POLICY_ENV=true", "KEEP_POLICY_ENV='keep value' OTHER=1"
    )
    assert router.render_crontab(current, tmp_path) == current


def test_cron_check_does_not_acquire_installer_lock(release, monkeypatch):
    workspace, _, _, _ = release
    current = router.render_crontab(original_cron(workspace), workspace)
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: current)
    monkeypatch.setattr(
        router.fcntl,
        "flock",
        lambda *a: pytest.fail("read-only check must not wait for installer"),
    )
    router.manage_cron(workspace, False)


def test_submission_monitor_routes_selected_observer_without_start(release):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, "buy-funnel", "2026-09-21")
    assert plan["command"] == ["/bin/bash", str(root / "deploy/run_buy_funnel_sentinel_intraday.sh"), "2026-09-21"]
    assert plan["cwd"] == str(root)


def test_pre_submit_source_monitor_routes_selected_release_independently(release):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, "pre-submit-source", "2026-09-29")
    assert plan["command"][:3] == [str(root / ".venv/bin/python"), "-m",
                                   "src.engine.monitoring.submission_bottleneck_monitor"]
    assert plan["command"][-4:] == ["--delay-source-only", "--date", "2026-09-29", "--notify"]
    assert plan["cwd"] == str(root)


def test_holding_exit_sentinel_routes_selected_release_without_start(release):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, "holding-exit-sentinel", "2026-09-28")
    assert plan["command"] == [
        "/bin/bash", str(root / "deploy/run_holding_exit_sentinel_intraday.sh"),
        "2026-09-28",
    ]
    assert plan["cwd"] == str(root)


def test_stage2_holding_exit_cron_routes_all_session_rows_through_selector():
    installer = (Path(__file__).resolve().parents[2] / "deploy" /
                 "install_stage2_ops_cron.sh").read_text()
    rows = [line for line in installer.splitlines()
            if "# HOLDING_EXIT_SENTINEL_" in line]
    assert len(rows) == 6
    assert all("run_runtime_release.sh holding-exit-sentinel" in row
               for row in rows)


def test_stage2_pre_submit_source_monitor_has_independent_selected_release_trigger():
    installer = (Path(__file__).resolve().parents[2] / "deploy" /
                 "install_stage2_ops_cron.sh").read_text()
    rows = [line for line in installer.splitlines() if "# PRE_SUBMIT_SOURCE_" in line]
    assert len(rows) == 1
    assert rows[0].startswith("2-57/5 8-19 ")
    assert "run_runtime_release.sh pre-submit-source" in rows[0]
    assert "!/PRE_SUBMIT_SOURCE_/" in installer








@pytest.mark.parametrize('kind',['valid','malformed','dangling'])
def test_operator_startup_hold_blocks_only_startup_and_persists(release,kind):
    workspace,root,_,_=release
    hold=workspace/'data/runtime/operator_startup_hold.json'
    if kind=='dangling': hold.symlink_to(workspace/'missing')
    else: hold.write_text('{}' if kind=='valid' else 'broken')
    for op in ('start','restart','preopen'):
        with pytest.raises(ValueError,match='operator_postclose_startup_hold_active'):
            router.make_plan(workspace,root,'a'*40,op,'2026-10-08')
    for op in ('postclose','finalize','error-detection'):
        assert router.make_plan(workspace,root,'a'*40,op,'2026-10-07')
    hold.unlink()
    assert router.make_plan(workspace,root,'a'*40,'start','2026-10-08')


@pytest.mark.parametrize('entry',['run_bot.sh','bot_main.py'])
def test_direct_startup_entry_honors_operator_hold_before_any_bot_import(tmp_path,entry):
    import shutil
    repo=Path(__file__).resolve().parents[2]
    (tmp_path/'src').mkdir();(tmp_path/'deploy').mkdir();(tmp_path/'data/runtime').mkdir(parents=True)
    (tmp_path/'data/runtime/operator_startup_hold.json').write_text('{}')
    shutil.copy2(repo/'src'/entry,tmp_path/'src'/entry)
    shutil.copy2(repo/'deploy/cpu_affinity_profile.sh',tmp_path/'deploy/cpu_affinity_profile.sh')
    command=['bash',str(tmp_path/'src'/entry)] if entry.endswith('.sh') else [sys.executable,str(tmp_path/'src'/entry)]
    result=subprocess.run(command,cwd=tmp_path/'src',capture_output=True,text=True,timeout=10)
    assert result.returncode!=0
    assert 'operator_postclose_startup_hold_active' in result.stdout+result.stderr
    assert 'ModuleNotFoundError' not in result.stderr
