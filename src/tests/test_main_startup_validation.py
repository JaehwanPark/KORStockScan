"""Parent transaction tests using a real isolated early-entrypoint child.

Prepared-policy intake and env construction are unit fixtures here. The child
entrypoint, isolation, PID identity, timeouts and terminal publication are real.
Native active-policy interpretation is covered by the loader contract suite.
"""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import ast

import pytest

from src.engine.automation import main_startup_validation as validation
from src.engine.infrastructure.main_policy_loading import CONSUMER_IDS


ROOT = Path(__file__).resolve().parents[2]
DAY = "2026-10-19"
CODE_FILES = (
    "src/bot_main.py", "src/run_bot.sh",
    "src/engine/automation/main_startup_validation.py",
    "src/engine/infrastructure/startup_validation_isolation.py",
    "src/engine/infrastructure/startup_validation_code_context.py",
    "src/engine/infrastructure/main_policy_environment.sh",
)


def test_source_closure_merge_never_overwrites_original_intake_generation():
    sources = {'/original/policy.json': 'a'*64, '/original/absent': None}
    validation._merge_source_hashes(sources, {'/original/policy.json': 'a'*64, '/new/shard': 'b'*64})
    before = dict(sources)
    for extra in ({'/new/other': 'c'*64, '/original/policy.json': 'd'*64}, {'/original/absent': 'e'*64}):
        with pytest.raises(ValueError, match='startup_source_binding_conflict'):
            validation._merge_source_hashes(sources, extra)
        assert sources == before


@pytest.fixture
def native_preparation_cli(tmp_path):
    """Run the unchanged native CLI dispatcher over tiny private source checks.

    Family semantic verification is isolated here, not replaced in production.
    The selected digest owner, process boundary and runpy/CLI dispatch are real.
    """
    code = tmp_path / 'selected'
    data = code / 'data'
    data.mkdir(parents=True)
    for package in ('src', 'src/utils', 'src/engine', 'src/engine/automation',
                    'src/engine/infrastructure'):
        directory = code / package
        directory.mkdir(parents=True, exist_ok=True)
        (directory / '__init__.py').touch()
    (code / '.venv').symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    shutil.copyfile(ROOT / 'src/engine/infrastructure/validation_digest_session.py',
                    code / 'src/engine/infrastructure/validation_digest_session.py')
    (code / 'src/utils/constants.py').write_text(f'from pathlib import Path\nDATA_DIR=Path({str(data)!r})\n')
    source = data / 'source.bin'
    source.write_bytes(b'a' * (2 * 1024 * 1024))
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    (data / 'mode.txt').write_text('pass')
    owner = (ROOT / 'src/engine/automation/next_preopen_readiness.py').read_text()
    dispatcher = next(node for node in ast.parse(owner).body
                      if isinstance(node, ast.FunctionDef) and node.name == 'main')
    main_source = ast.get_source_segment(owner, dispatcher)
    prelude = f'''"""Private semantic fixture; original native CLI dispatcher below."""
import argparse,json,os,subprocess,sys
from src.utils.constants import DATA_DIR
from src.engine.infrastructure import validation_digest_session as digest_owner
def verify_prepared(target_date, *, require_today=False):
    assert sys.argv[1:]==['--verify','--target-date',{DAY!r}]
    assert target_date=={DAY!r} and require_today is False
    active=digest_owner.ACTIVE.get()
    assert active is not None and active.binding['day']=='2026-10-16'
    path=DATA_DIR/'source.bin'
    mode=(DATA_DIR/'mode.txt').read_text()
    assert digest_owner.reused_digest(path)=={expected!r}
    if mode=='changed':
        path.write_bytes(b'b'*path.stat().st_size)
    if digest_owner.reused_digest(path)!={expected!r}:
        raise ValueError('native_source_changed')
    if mode=='fail':
        return dict(status='fail', findings=['native_semantic_failure'])
    return dict(status='pass', findings=[], target_date=target_date,
                validation_scope='current_full_contract', actual_pid_consumed=False)
'''
    (code / 'src/engine/automation/next_preopen_readiness.py').write_text(
        prelude + '\n' + main_source + '\nif __name__=="__main__":\n    raise SystemExit(main())\n')
    return code, data


def test_native_preparation_context_keeps_cli_full_scope_and_cold_invocation_boundary(native_preparation_cli):
    code, data = native_preparation_cli
    results = [validation._native_preparation_check(code, DAY, '2026-10-16') for _ in range(2)]
    for result in results:
        assert result['validation_scope'] == 'current_full_contract'
        assert result['actual_pid_consumed'] is False
        io = result['native_validation_io']
        assert io['source_date'] == '2026-10-16'
        assert io['remaining_entries'] == 0
        assert io['stats']['cache_status'] == 'invocation_memory_only'
        assert io['stats']['full_reads'] == io['stats']['reused_reads'] == 1
        assert io['stats']['semantic_reused_reads'] == 0
        assert io['stats']['full_bytes'] == io['stats']['reused_bytes'] == 2 * 1024 * 1024
        assert result['native_process_lifecycle']['child_terminated'] is True
        assert result['native_process_lifecycle']['descendants_drained'] is True
        assert result['native_process_lifecycle']['cleanup_required'] is False
    assert results[0]['native_validation_io']['stats']['pid'] != results[1]['native_validation_io']['stats']['pid']
    assert not (data / 'runtime/validation_digests').exists()


def test_native_timeout_terminates_owned_frozen_child_without_touching_unrelated_child(tmp_path):
    pid_path = tmp_path/'frozen.pid'
    script = "import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)"
    unrelated = subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
    try:
        with pytest.raises(subprocess.TimeoutExpired) as caught:
            validation._run_native_validation([sys.executable,'-c',script,str(pid_path)],
                cwd=tmp_path,env=validation._safe_process_environment(),timeout=.3)
        life=caught.value.native_process_lifecycle
        assert life['cleanup_required'] and life['child_terminated'] and life['descendants_drained']
        assert unrelated.poll() is None
        path=Path('/proc')/pid_path.read_text()/'stat'
        assert not path.exists() or path.read_text().rsplit(')',1)[1].split()[0]=='Z'
    finally:
        unrelated.kill(); unrelated.wait(timeout=5)


def test_native_interrupt_also_closes_the_owned_session(tmp_path,monkeypatch):
    original=subprocess.Popen.communicate
    first=True
    def interrupt(process,*args,**kwargs):
        nonlocal first
        if first:
            first=False
            raise KeyboardInterrupt()
        return original(process,*args,**kwargs)
    monkeypatch.setattr(subprocess.Popen,'communicate',interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        validation._run_native_validation([sys.executable,'-c','import time;time.sleep(60)'],
            cwd=tmp_path,env=validation._safe_process_environment())
    assert caught.value.native_process_lifecycle['child_terminated']
    assert caught.value.native_process_lifecycle['descendants_drained']


@pytest.mark.parametrize('mode', ['fail', 'changed'])
def test_native_preparation_context_never_reuses_pass_or_changed_source(
        native_preparation_cli, monkeypatch, mode):
    code, data = native_preparation_cli
    (data / 'mode.txt').write_text(mode)
    original_run = validation._run_native_validation
    observed = []
    def record(*args, **kwargs):
        result = original_run(*args, **kwargs)
        observed.append(result)
        return result
    monkeypatch.setattr(validation, '_run_native_validation', record)
    with pytest.raises(ValueError, match='startup_native_preparation_failed'):
        validation._native_preparation_check(code, DAY, '2026-10-16')
    result, = observed
    assert result.returncode == 1
    native = json.loads(result.stdout.splitlines()[-1])
    if mode == 'changed':
        assert native['reason'] == 'native_source_changed'
    else:
        assert native['findings'] == ['native_semantic_failure']
    line, = [line for line in result.stderr.splitlines() if line.startswith('P5_NATIVE_VALIDATION_IO=')]
    io = json.loads(line.removeprefix('P5_NATIVE_VALIDATION_IO='))
    assert io['remaining_entries'] == 0
    assert io['stats']['full_reads'] == (2 if mode == 'changed' else 1)
    assert io['stats']['reused_reads'] == (0 if mode == 'changed' else 1)
    assert not (data / 'runtime/validation_digests').exists()


def test_native_preparation_rejects_missing_context_diagnostics(tmp_path, monkeypatch):
    def missing(*args, **kwargs):
        result = subprocess.CompletedProcess(args[0], 0, stdout=json.dumps(dict(status='pass', findings=[])), stderr='')
        result.native_process_lifecycle = {'child_terminated': True, 'descendants_drained': True}
        return result
    monkeypatch.setattr(validation, '_run_native_validation', missing)
    with pytest.raises(ValueError, match='startup_native_preparation_diagnostics_invalid'):
        validation._native_preparation_check(tmp_path, DAY, '2026-10-16')


@pytest.mark.parametrize('key', ['semantic_reused_reads', 'admitted_native_proofs', 'admitted_native_bytes'])
@pytest.mark.parametrize('counter', [0, 7, -1, True, '0', None])
def test_native_preparation_validates_native_reuse_counters(native_preparation_cli, monkeypatch, key, counter):
    code, _ = native_preparation_cli
    original = validation._run_native_validation
    def invalid(*args, **kwargs):
        result = original(*args, **kwargs)
        prefix = 'P5_NATIVE_VALIDATION_IO='
        lines = result.stderr.splitlines()
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                value = json.loads(line.removeprefix(prefix))
                value['stats'][key] = counter
                lines[index] = prefix + json.dumps(value)
        result.stderr = '\n'.join(lines)
        return result
    monkeypatch.setattr(validation, '_run_native_validation', invalid)
    if type(counter) is int and counter >= 0:
        result = validation._native_preparation_check(code, DAY, '2026-10-16')
        assert result['native_validation_io']['stats'][key] == counter
    else:
        with pytest.raises(ValueError, match='startup_native_preparation_diagnostics_invalid'):
            validation._native_preparation_check(code, DAY, '2026-10-16')


@pytest.mark.parametrize('failure', ['exit', 'findings'])
def test_native_preparation_diagnostic_status_requires_full_result_contract(
        native_preparation_cli, monkeypatch, failure):
    code, _ = native_preparation_cli
    original_run = validation._run_native_validation
    def contradictory(*args, **kwargs):
        result = original_run(*args, **kwargs)
        if failure == 'exit':
            result.returncode = 1
        else:
            native = json.loads(result.stdout.splitlines()[-1])
            native['findings'] = ['native_failure_despite_status']
            result.stdout = json.dumps(native) + '\n'
        return result
    monkeypatch.setattr(validation, '_run_native_validation', contradictory)
    with pytest.raises(ValueError, match='startup_native_preparation_failed') as captured:
        validation._native_preparation_check(code, DAY, '2026-10-16')
    receipt = captured.value.native_preparation_check
    assert receipt['status'] == 'fail'
    assert receipt['diagnostics_status'] == 'observed'
    assert receipt['native_validation_io']['stats']['full_reads'] == 1


@pytest.fixture
def transaction(tmp_path, monkeypatch):
    class FixtureClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat(DAY+'T10:00:00+09:00').astimezone(tz)
    monkeypatch.setattr(validation, 'datetime', FixtureClock)
    workspace, code = tmp_path / "workspace", tmp_path / "code"
    workspace.mkdir()
    for item in CODE_FILES:
        destination = code / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / item, destination)
    for package in ("src", "src/engine", "src/engine/automation", "src/engine/infrastructure"):
        (code / package / "__init__.py").touch()
    isolation = code / "src/engine/infrastructure/startup_validation_isolation.py"
    with isolation.open("a") as stream:
        stream.write("""
_real_install_validation_isolation = install_validation_isolation
def install_validation_isolation(*args, **kwargs):
    if os.environ.get('FIXTURE_MODE') == 'isolation_unavailable':
        raise IsolationUnavailable('fixture_isolation_unavailable')
    return _real_install_validation_isolation(*args, **kwargs)
""")
    (code / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    loader = code / "src/engine/infrastructure/main_policy_loading.py"
    loader.write_text(f"""
import hashlib, os, pathlib, socket, time
CONSUMER_IDS = frozenset({sorted(CONSUMER_IDS)!r})
def load_main_policies(**kwargs):
    mode = os.environ.get('FIXTURE_MODE', 'passed')
    if mode == 'timeout':
        time.sleep(360)
    if mode == 'crash':
        os._exit(17)
    if mode == 'caught_write':
        try:
            pathlib.Path(os.environ['FIXTURE_PROTECTED']).write_text('CORRUPT')
        except PermissionError:
            pass
    if mode == 'caught_network':
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except PermissionError:
            pass
    rows = {{key: dict(status='loaded', native_status='loaded',
        loaded_object_sha256=hashlib.sha256(key.encode()).hexdigest(),
        policy_sha256=None, source_hashes={{}}) for key in CONSUMER_IDS}}
    if mode == 'missing_consumer':
        rows.pop(sorted(rows)[0])
    if mode == 'failed_consumer':
        rows[sorted(rows)[0]]['status'] = 'failed'
    return dict(schema='main_policy_loading_v1', target_date=kwargs['target_date'],
        observed_at_kst=kwargs['observed_at'].isoformat(),
        status='failed' if mode == 'failed_consumer' else 'passed',
        consumer_results=rows, runtime_effect=(mode == 'authority_leak'),
        actual_pid_consumed=False)
""")
    subprocess.run(["git", "init", "-q", str(code)], check=True)
    subprocess.run(["git", "-C", str(code), "add", "src"], check=True)
    subprocess.run(
        ["git", "-C", str(code), "-c", "user.name=Validation Fixture",
         "-c", "user.email=fixture@example.invalid", "commit", "-qm", "isolated fixture"], check=True,
    )
    commit = subprocess.check_output(["git", "-C", str(code), "rev-parse", "HEAD"], text=True).strip()
    protected = workspace / "protected-policy.json"
    protected.write_text('{"original": true}\n')
    receipt = workspace / "prepared.json"
    receipt.write_text('{"fixture": true}\n')
    bootstrap = workspace / "bootstrap.env"
    bootstrap.write_text("KORSTOCKSCAN_FIXTURE_POLICY=bound\n")
    intake = dict(
        selected_root=code, selected_commit=commit, receipt_path=receipt,
        receipt={"env_path": str(bootstrap), "activation_candidate": {}, "source_date": "2026-10-16"},
        manifest={"target_date": DAY, "env_overrides": {}},
        source_hashes={str(protected): validation._sha(protected), str(receipt): validation._sha(receipt),
                       str(bootstrap): validation._sha(bootstrap)},
    )
    binding = dict(basis="reviewed_candidate_handoff", root=str(code), commit=commit, contracts={})
    monkeypatch.setattr(validation, "_intake", lambda *args: intake)
    monkeypatch.setattr(validation, "_bind_execution", lambda *args: binding)
    native_check = validation._native_preparation_check
    monkeypatch.setattr(validation, "_native_preparation_check", lambda *args: {"status": "pass"})
    state = {"mode": "passed", "workspace": workspace, "code": code, "protected": protected,
             "intake": intake, "binding": binding, "loader": loader, "native_check": native_check}

    def compose(*args, **kwargs):
        return {"PATH": os.defpath, "PYTHONPATH": str(code), "PYTHONDONTWRITEBYTECODE": "1",
                "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                "KORSTOCKSCAN_FIXTURE_POLICY": "bound", "FIXTURE_MODE": state["mode"],
                "FIXTURE_PROTECTED": str(protected)}

    state["compose"] = compose
    monkeypatch.setattr(validation, "_compose_environment", compose)
    return state


def _run(transaction, **kwargs):
    return validation.run_validation(
        workspace=transaction["workspace"], target_date=DAY,
        execution_root=transaction["code"], candidate=True, **kwargs,
    )


def _assert_failed_terminal(final, receipt):
    assert final["status"] == "failed"
    assert final["load_check_passed"] is False
    assert final["actual_pid_consumed"] is False
    assert final["runtime_effect"] is False
    assert final["allowed_runtime_apply"] is False
    assert final["findings"]
    assert json.loads(receipt.read_text()) == final
    assert not list(receipt.parent.glob(".final.json.*"))


def test_real_early_child_terminates_with_exact_identity_and_nonempty_consumer_receipt(transaction):
    before = transaction["protected"].read_bytes()
    final, receipt = _run(transaction)
    assert final["status"] == "passed", (final, (receipt.parent / "child-output.log").read_text())
    assert final["child_exit_code"] == 0
    assert final["child_terminated"] is True
    assert final["load_check_passed"] is True
    assert final["protected_sources_unchanged"] is True
    assert set(final["consumer_results"]) == CONSUMER_IDS
    assert len(final["consumer_results"]) > 1
    child = json.loads((receipt.parent / "child.json").read_text())
    assert child["validation_pid"] == final["validation_pid"] != os.getpid()
    assert child["validation_start_ticks"] == final["validation_start_ticks"]
    assert not Path(f'/proc/{child["validation_pid"]}').exists()
    assert child["request_sha256"] == final["input_manifest_sha256"]
    assert (receipt.parent / "isolation.jsonl").read_bytes() == b""
    assert transaction["protected"].read_bytes() == before
    assert not (transaction["code"] / "logs").exists()


def test_target_expiry_after_successful_child_never_becomes_parent_pass(transaction, monkeypatch):
    class ExpiredClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat('2026-10-20T00:00:01+09:00').astimezone(tz)
    monkeypatch.setattr(validation, 'datetime', ExpiredClock)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final['child_terminated'] is True
    assert final['child_exit_code'] == 0
    assert 'startup_target_expired_during_validation' in ' '.join(final['findings'])


@pytest.mark.parametrize("mode", [
    "failed_consumer", "missing_consumer", "caught_write", "caught_network", "crash",
])
def test_real_child_failure_never_becomes_parent_pass(transaction, mode):
    transaction["mode"] = mode
    before = transaction["protected"].read_bytes()
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True
    assert transaction["protected"].read_bytes() == before
    if mode in {"caught_write", "caught_network"}:
        assert (receipt.parent / "isolation.jsonl").read_bytes()


def test_loader_cannot_report_runtime_authority_and_receive_validation_pass(transaction):
    transaction["mode"] = "authority_leak"
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True


def test_missing_os_isolation_never_enters_loader_or_publishes_pass(transaction):
    transaction["mode"] = "isolation_unavailable"
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True
    assert "fixture_isolation_unavailable" in " ".join(final["findings"])
    assert not final.get("consumer_results")


def test_timeout_kills_only_the_owned_validation_child_and_publishes_failure(transaction):
    transaction["mode"] = "timeout"
    final, receipt = _run(transaction, timeout=1)
    _assert_failed_terminal(final, receipt)
    assert "startup_child_timeout" in " ".join(final["findings"])
    assert final["child_terminated"] is True
    assert not Path(f'/proc/{final["validation_pid"]}').exists()
    assert os.getpid() != final["validation_pid"]


def test_intake_failure_has_atomic_failed_receipt_and_never_creates_child(transaction, monkeypatch):
    def failed(*args):
        raise ValueError("fixture_required_prepared_source_missing")
    monkeypatch.setattr(validation, "_intake", failed)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["failure_phase"] == "intake"
    assert "validation_pid" not in final
    assert not (receipt.parent / "child.json").exists()


def test_source_change_during_environment_composition_is_rejected_before_child(transaction, monkeypatch):
    def racing_compose(*args, **kwargs):
        values = transaction["compose"](*args, **kwargs)
        transaction["protected"].write_text("new-generation\n")
        return values
    monkeypatch.setattr(validation, "_compose_environment", racing_compose)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert "startup_source_changed" in " ".join(final["findings"])
    assert "validation_pid" not in final


def test_last_native_recheck_cannot_change_a_protected_source_then_publish_pass(transaction, monkeypatch):
    def changed_at_final_check(*args):
        transaction["protected"].write_text("changed-by-final-verifier\n")
        return {"status": "pass"}
    monkeypatch.setattr(validation, "_native_preparation_check", changed_at_final_check)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final["child_terminated"] is True
    assert "startup_source_changed" in " ".join(final["findings"])


@pytest.mark.parametrize('phase', ['native_recheck', 'final_binding'])
def test_consumer_only_membership_change_at_final_recheck_never_publishes_pass(
        transaction, monkeypatch, phase):
    # A nested membership leaf is learned by the isolated consumer, so it is
    # absent from the initial request's headers/code/source closure.
    shard = transaction['workspace'] / 'nested-membership.json'
    shard.write_text('{"original_membership": true}\n')
    original_sha = validation._sha(shard)
    loader = transaction['loader']
    marker = "    if mode == 'missing_consumer':"
    text = loader.read_text()
    assert text.count(marker) == 1
    loader.write_text(text.replace(marker,
        f"    rows['pre_submit_delay']['source_hashes'][{str(shard)!r}] = "
        f"hashlib.sha256(pathlib.Path({str(shard)!r}).read_bytes()).hexdigest()\n" + marker))
    changed = []
    def mutate():
        shard.write_text('{"original_membership": false}\n')
        changed.append(True)
    if phase == 'native_recheck':
        def native(*args):
            mutate()
            return {'status': 'pass'}
        monkeypatch.setattr(validation, '_native_preparation_check', native)
    else:
        calls = []
        def bind(*args):
            calls.append(True)
            if len(calls) == 2:
                mutate()
            return transaction['binding']
        monkeypatch.setattr(validation, '_bind_execution', bind)
    final, receipt = _run(transaction)
    request = json.loads((receipt.parent / 'request.json').read_text())
    child = json.loads((receipt.parent / 'child.json').read_text())
    assert str(shard) not in request['source_hashes']
    assert child['consumer_results']['pre_submit_delay']['source_hashes'][str(shard)] == original_sha
    assert changed == [True] and child['status'] == 'passed'
    assert (receipt.parent / 'isolation.jsonl').read_bytes() == b''
    _assert_failed_terminal(final, receipt)
    assert final['failure_phase'] == 'recheck' and final['child_terminated'] is True
    assert final.get('protected_sources_unchanged') is not True
    assert 'startup_source_changed:' + str(shard) in ' '.join(final['findings'])


@pytest.mark.parametrize('phase', ['intake', 'recheck'])
def test_failed_native_preparation_preserves_bounded_stats_in_failed_terminal(
        transaction, native_preparation_cli, monkeypatch, phase):
    code, data = native_preparation_cli
    (data / 'mode.txt').write_text('fail')
    def failing_native(*args):
        return transaction['native_check'](code, DAY, '2026-10-16')
    monkeypatch.setattr(validation, '_intake' if phase == 'intake' else '_native_preparation_check',
                        failing_native)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert final['failure_phase'] == phase
    check = final['native_preparation_checks'][phase]
    assert check['status'] == 'fail' and check['exit_code'] == 1
    assert check['diagnostics_status'] == 'observed'
    assert check['native_validation_io']['remaining_entries'] == 0
    assert check['native_validation_io']['stats']['full_reads'] == 1
    assert check['native_validation_io']['stats']['reused_reads'] == 1
    assert not (data / 'runtime/validation_digests').exists()


def test_native_preparation_timeout_keeps_unknown_counters_without_raw_output(transaction, monkeypatch):
    def timed_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 180, output='PRIVATE_STDOUT', stderr='PRIVATE_STDERR')
    def failing_intake(*args):
        with pytest.MonkeyPatch.context() as isolated:
            isolated.setattr(validation, '_run_native_validation', timed_out)
            return transaction['native_check'](transaction['code'], DAY, '2026-10-16')
    monkeypatch.setattr(validation, '_intake', failing_intake)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    check = final['native_preparation_checks']['intake']
    assert check['status'] == 'timeout' and check['exit_code'] is None
    assert check['native_validation_io'] is None
    assert check['diagnostics_status'] == 'unavailable_child_timeout'
    assert 'PRIVATE_' not in receipt.read_text()
    assert 'remaining_entries' not in check


def test_any_native_code_dependency_change_is_bound_before_child(transaction, monkeypatch):
    def changed_loader(*args, **kwargs):
        values = transaction["compose"](*args, **kwargs)
        dependency = transaction["code"] / "src/engine/__init__.py"
        dependency.write_text("NATIVE_GENERATION = 'changed'\n")
        return values
    monkeypatch.setattr(validation, "_compose_environment", changed_loader)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert "startup_source_changed" in " ".join(final["findings"])
    assert "validation_pid" not in final


def test_execution_binding_change_after_successful_child_invalidates_parent_pass(transaction, monkeypatch):
    calls = []
    def changed_binding(*args, **kwargs):
        calls.append(True)
        result = dict(transaction["binding"])
        if len(calls) > 1:
            result["commit"] = "b" * 40
        return result
    monkeypatch.setattr(validation, "_bind_execution", changed_binding)
    final, receipt = _run(transaction)
    _assert_failed_terminal(final, receipt)
    assert "startup_execution_binding_changed" in " ".join(final["findings"])
    assert final["child_terminated"] is True


def test_atomic_receipt_failure_keeps_original_bytes_and_removes_temporary(tmp_path, monkeypatch):
    receipt = tmp_path / "final.json"
    original = b'{"status":"older-original"}\r\n'
    receipt.write_bytes(original)
    def failed_replace(*args):
        raise OSError("fixture_replace_failed")
    monkeypatch.setattr(validation.os, "replace", failed_replace)
    with pytest.raises(OSError, match="fixture_replace_failed"):
        validation._atomic(receipt, {"status": "new"})
    assert receipt.read_bytes() == original
    assert list(tmp_path.iterdir()) == [receipt]


def test_child_request_tamper_is_rejected_before_loader_import(transaction, tmp_path):
    run = tmp_path / ("a" * 32)
    run.mkdir(mode=0o700)
    request = dict(schema=validation.SCHEMA, run_id=run.name, target_date=DAY,
                   execution_release_root=str(transaction["code"]),
                   execution_release_commit=transaction["binding"]["commit"],
                   request_sha256="0" * 64)
    path = run / "request.json"
    path.write_text(json.dumps(request))
    result = subprocess.run(
        [sys.executable, "-B", str(transaction["code"] / "src/bot_main.py"),
         "--validate-startup", str(path)], cwd=transaction["code"],
        env={"PATH": os.defpath, "PYTHONPATH": str(transaction["code"]),
             "OPENBLAS_NUM_THREADS": "1"}, start_new_session=True,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "startup_request_digest_invalid" in result.stderr
    assert not (run / "isolation.jsonl").exists()
    assert not (run / "child.json").exists()
    assert not (transaction["code"] / "logs").exists()


@pytest.mark.parametrize("contents", [
    "KORSTOCKSCAN_X=$(touch injected)\n",
    "KORSTOCKSCAN_X=value; touch injected\n",
    "KORSTOCKSCAN_X=value\nKORSTOCKSCAN_X=other\n",
    "source other.env\n",
    "PATH=/tmp/untrusted\n",
    "BASH_ENV=/tmp/untrusted\n",
])
def test_environment_data_parser_refuses_shell_or_nonpolicy_authority(tmp_path, contents):
    source = tmp_path / "input.env"
    source.write_text(contents)
    with pytest.raises(ValueError):
        validation._assignment_values(source)
    assert not (tmp_path / "injected").exists()


def test_environment_data_parser_preserves_quoted_shell_characters_as_literal_data(tmp_path):
    source = tmp_path / "input.env"
    source.write_text("export KORSTOCKSCAN_X='$(touch injected)'\n")
    assert validation._assignment_values(source) == {"KORSTOCKSCAN_X": "$(touch injected)"}
    assert not (tmp_path / "injected").exists()


@pytest.mark.parametrize("role", ["policy", "custody"])
@pytest.mark.parametrize("key", sorted(validation.BOOTSTRAP_OBSERVATION_ENV_KEYS))
def test_bootstrap_observation_keys_do_not_expand_other_input_roles(tmp_path, role, key):
    source = tmp_path / "input.env"
    source.write_text(f"export {key}=false\n")
    with pytest.raises(ValueError, match="startup_environment_policy_namespace_required"):
        validation._assignment_values(source, source_role=role)


@pytest.mark.parametrize("key", [
    "SCALP_MICRO_REVERSION_UNKNOWN_ENABLED", "SCALP_MICRO_REVERSION_OBSERVER_ENABLED_EXTRA",
    "SCALP_STOP", "PATH", "BASH_ENV", "PYTHONPATH", "LD_PRELOAD",
])
def test_bootstrap_role_does_not_allow_arbitrary_nonpolicy_names(tmp_path, key):
    source = tmp_path / "input.env"
    source.write_text(f"{key}=untrusted\n")
    with pytest.raises(ValueError, match="startup_environment_policy_namespace_required"):
        validation._assignment_values(source, source_role="bootstrap")


@pytest.mark.parametrize("rhs", ["$(touch injected)", "`touch injected`", "$HOME", "false; touch injected"])
def test_bootstrap_observation_allowlist_never_allows_shell_expressions(tmp_path, rhs):
    source = tmp_path / "input.env"
    source.write_text(f"SCALP_MICRO_REVERSION_OBSERVER_ENABLED={rhs}\n")
    with pytest.raises(ValueError):
        validation._assignment_values(source, source_role="bootstrap")
    assert not (tmp_path / "injected").exists()


def test_environment_unknown_input_role_fails_closed(tmp_path):
    source = tmp_path / "input.env"
    source.write_text("KORSTOCKSCAN_X=bound\n")
    with pytest.raises(ValueError, match="startup_environment_source_role_invalid"):
        validation._assignment_values(source, source_role="operator")


def test_native_bootstrap_observation_values_survive_literal_parser_and_shared_environment(tmp_path, monkeypatch):
    from src.engine.automation import runtime_policy_bootstrap as bootstrap_owner
    from src.engine.scalping.micro_reversion.observation_adapter import ObserverFeatureFlags

    code = tmp_path / "project"
    for directory in (code / "src/engine/infrastructure", code / ".venv/bin", code / "data/config"):
        directory.mkdir(parents=True)
    shutil.copyfile(ROOT / "src/engine/infrastructure/main_policy_environment.sh",
                    code / "src/engine/infrastructure/main_policy_environment.sh")
    python = code / ".venv/bin/python"
    python.write_text("#!/bin/sh\nprintf '%s\\n' 'export KORSTOCKSCAN_STUB_NATIVE=true'\n")
    python.chmod(0o755)
    expected = {
        "SCALP_MICRO_REVERSION_DEPTH_CAPTURE_ENABLED": "false",
        "SCALP_MICRO_REVERSION_DISCOVERY_ENABLED": "true",
        "SCALP_MICRO_REVERSION_OBSERVER_ENABLED": "true",
        "SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED": "false",
        "KORSTOCKSCAN_LITERAL_FIXTURE": "$(touch injected)",
        "KORSTOCKSCAN_OWNER_LAYER": "bootstrap",
    }
    # The native writer owns quoting and the manifest; only its policy inputs
    # are a private fixture. No real preparation or provider is invoked.
    monkeypatch.setattr(bootstrap_owner, "build_manifest", lambda *a, **k: {
        "target_date": DAY, "env_overrides": dict(expected)})
    prepared = code / "prepared"
    prepared.mkdir()
    manifest = bootstrap_owner.write_bootstrap(DAY, output_dir=prepared)
    source = Path(manifest["env_file"])
    before = source.read_bytes()
    parsed = validation._assignment_values(source, source_role="bootstrap")
    assert all(parsed[key] == value for key, value in expected.items())
    (code / "data/config/native_owner_custody.env").write_text(
        "export KORSTOCKSCAN_OWNER_LAYER=custody\n")
    run = tmp_path / "private"
    run.mkdir(mode=0o700)
    environment = validation._compose_environment(code, DAY, source, run)
    for key, value in expected.items():
        assert environment[key] == ("custody" if key == "KORSTOCKSCAN_OWNER_LAYER" else value)
    for key in validation.BOOTSTRAP_OBSERVATION_ENV_KEYS:
        monkeypatch.setenv(key, environment[key])
    flags = ObserverFeatureFlags.from_env()
    assert (flags.depth_capture_enabled, flags.discovery_enabled,
            flags.observer_enabled, flags.path_capture_enabled) == (False, True, True, False)
    assert source.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == manifest["env_sha256"]
    assert not (code / "src/injected").exists()
    assert not (tmp_path / "injected").exists()


def test_noninteractive_shell_does_not_execute_polluted_parent_bash_env(tmp_path, monkeypatch):
    code = tmp_path / "project"
    for directory in (code / "src/engine/infrastructure", code / ".venv/bin", code / "data/config"):
        directory.mkdir(parents=True)
    shutil.copyfile(ROOT / "src/engine/infrastructure/main_policy_environment.sh",
                    code / "src/engine/infrastructure/main_policy_environment.sh")
    python = code / ".venv/bin/python"
    python.write_text("#!/bin/sh\nprintf '%s\\n' 'export KORSTOCKSCAN_STUB_NATIVE=true'\n")
    python.chmod(0o755)
    bootstrap = code / "bootstrap.env"
    bootstrap.write_text("KORSTOCKSCAN_FIXTURE_POLICY=bound\n")
    (code / "data/config/native_owner_custody.env").write_text("KORSTOCKSCAN_NATIVE_CUSTODY_FIXTURE=true\n")
    run = tmp_path / "private"
    run.mkdir(mode=0o700)
    sentinel = tmp_path / "unwanted-shell-execution.txt"
    bash_env = tmp_path / "polluted-bash-env.sh"
    bash_env.write_text(f"printf unsafe > '{sentinel}'\n")
    monkeypatch.setenv("BASH_ENV", str(bash_env))
    environment = validation._compose_environment(code, DAY, bootstrap, run)
    assert environment["KORSTOCKSCAN_FIXTURE_POLICY"] == "bound"
    assert not sentinel.exists()
    assert "BASH_ENV" not in environment


def test_json_reader_rejects_fifo_without_waiting_for_a_writer(tmp_path):
    fifo = tmp_path / "not-a-regular-source.json"
    os.mkfifo(fifo)
    started = time.monotonic()
    with pytest.raises(ValueError, match="startup_input_not_regular_bounded"):
        validation._read(fifo)
    assert time.monotonic() - started < 1


def test_first_read_atime_change_does_not_falsify_source_mutation(tmp_path):
    source = tmp_path / "source.json"
    raw = b'{"policy":"original"}\n'
    source.write_bytes(raw)
    os.utime(source, ns=(1, source.stat().st_mtime_ns))
    assert validation._read(source) == {"policy": "original"}
    os.utime(source, ns=(1, source.stat().st_mtime_ns))
    assert validation._sha(source) == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("defect", ["isolation_type", "row_type", "source_hashes_type",
                                     "missing_consumer", "invalid_digest", "wrong_policy", "runtime_authority"])
def test_parent_independently_rejects_malformed_or_unbound_child_semantics(defect):
    rows = {name: {"status": "loaded", "loaded_object_sha256": "a" * 64,
                   "policy_sha256": "b" * 64, "source_hashes": {}} for name in CONSUMER_IDS}
    child = dict(status="passed", runtime_effect=False, actual_pid_consumed=False,
                 allowed_runtime_apply=False, findings=[], consumer_results=rows,
                 forbidden_attempt_count=0,
                 isolation=dict(no_new_privileges=True, filesystem_write_root="/fixture/private",
                                landlock_abi=8, network_access=False, process_creation=False,
                                metadata_changes=False, caught_permission_denials_fail=True))
    expected = {"main_stop": "b" * 64}
    validation._validate_child_result(child, CONSUMER_IDS, expected)
    if defect == "isolation_type":
        child["isolation"] = ["malformed"]
    elif defect == "row_type":
        rows["main_stop"] = ["malformed"]
    elif defect == "source_hashes_type":
        rows["main_stop"]["source_hashes"] = ["malformed"]
    elif defect == "missing_consumer":
        rows.pop("main_stop")
    elif defect == "invalid_digest":
        rows["main_stop"]["loaded_object_sha256"] = "invalid"
    elif defect == "wrong_policy":
        rows["main_stop"]["policy_sha256"] = "c" * 64
    else:
        child["actual_pid_consumed"] = True
    expected_error = {
        "isolation_type": "startup_child_object_contract_invalid",
        "row_type": "startup_child_consumer_invalid:main_stop",
        "source_hashes_type": "startup_child_consumer_invalid:main_stop",
        "missing_consumer": "startup_child_semantic_contract_invalid",
        "invalid_digest": "startup_child_consumer_invalid:main_stop",
        "wrong_policy": "startup_child_wrong_policy:main_stop",
        "runtime_authority": "startup_child_semantic_contract_invalid",
    }[defect]
    with pytest.raises(ValueError, match=expected_error):
        validation._validate_child_result(child, CONSUMER_IDS, expected)


@pytest.mark.parametrize("boundary", ["load", "validate", "validate_rejected", "preserved"])
def test_native_cli_closure_is_collected_from_executed_native_boundaries(native_preparation_cli, boundary):
    code,data=native_preparation_cli
    package=code/'src/engine/scalping';package.mkdir();(package/'__init__.py').touch()
    (code/'src/engine/automation/pre_submit_delay_partitioned_research.py').write_text('def validate(*a,**k): return None\n')
    (package/'pre_submit_delay_initial_policy.py').write_text('# No delay policy in this native Main-only collection fixture.\n')
    (package/'mechanistic_entry_runtime_policy.py').write_text('''from src.utils.constants import DATA_DIR
import json

def load(*args,**kwargs):
    return json.loads((DATA_DIR/'bundle.json').read_text())
def validate(bundle,**kwargs):
    if bundle.get('reject'):raise ValueError('native_bundle_rejected')
''')
    ident='a'*64;bundle=dict(bundle_sha256='b'*64,target_date=DAY,continuous_reversal={'family_sha256':'c'*64})
    (data/'bundle.json').write_text(json.dumps(bundle))
    path=data/'runtime/mechanistic_entry_policy/auxiliary/transitions'/(ident+'.json')
    path.parent.mkdir(parents=True);path.write_text(json.dumps({'artifact_content_sha256':ident}))
    (package/'reversal_auxiliary_next_session.py').write_text('''from pathlib import Path
from types import SimpleNamespace
import hashlib,json
I=SimpleNamespace(read=lambda path:json.loads(Path(path).read_text()))
_FROZEN_SCRIPT='private_native_collection_fixture'
def _hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _frozen_inventory(root):return {str(Path(root)/'bundle.json'):_hash(Path(root)/'bundle.json')}
def _verify_frozen(root,manifest,bundle):return {'schema':'native_fixture_verified','bundle_sha256':_hash(bundle)}
def _dependencies(manifest):return []
def _database_signature(manifest):return None
def validate_manifest(data_root,manifest,bundle,**kwargs):
    _frozen_inventory(data_root)
    _verify_frozen(data_root,Path(data_root)/'bundle.json',Path(data_root)/'bundle.json')
    return manifest
''')
    cli=code/'src/engine/automation/next_preopen_readiness.py';text=cli.read_text()
    marker="    return dict(status='pass', findings=[], target_date=target_date,"
    calls=f'''    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_next_session as A
    b=N.load(data_root=DATA_DIR,target_date=target_date)
    A.validate_manifest(DATA_DIR,A.I.read({str(path)!r}),b)
'''
    if boundary != 'load':
        calls = calls.replace('b=N.load(data_root=DATA_DIR,target_date=target_date)',
            'b=__import__("json").loads((DATA_DIR/"bundle.json").read_text()); N.validate(b,target_date=target_date)')
    if boundary=='preserved':
        # The incumbent predates invocation-wide reuse: its nested target-day
        # owner must be observed before it clears its actual native entries.
        (code/'src/engine/infrastructure/validation_digest_session.py').write_bytes(
            subprocess.check_output(['git','-C',str(ROOT),'show','a7c0b0dc5:src/engine/infrastructure/validation_digest_session.py']))
        old_cli=subprocess.check_output(['git','-C',str(ROOT),'show',
            'a7c0b0dc5:src/engine/automation/next_preopen_readiness.py'],text=True)
        old_main=next(n for n in ast.parse(old_cli).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        copied_main=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        text=text.replace(ast.get_source_segment(text,copied_main),ast.get_source_segment(old_cli,old_main))
        text=text.replace("active.binding['day']=='2026-10-16'","active.binding['day']==target_date")
        consumed=data/'consumed.json';consumed.write_text('{}')
        (data/'readiness.json').write_text(json.dumps({'manifest_content_sha256':'c'*64}))
        (code/'src/engine/automation/intraday_release_handoff.py').write_text('''
from src.utils.constants import DATA_DIR
import hashlib
def _sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def _paths(day,commit):return DATA_DIR/'bundle.json',DATA_DIR/'consumed.json'
def verify(day,commit):return dict(status='pass',findings=[],handoff=dict(
    frozen_files={str(DATA_DIR/'source.bin'):_sha(DATA_DIR/'source.bin')},manifest_sha256='f'*64,
    prepared_receipt_path=str(DATA_DIR/'readiness.json')))
''')
        (code/'src/engine/automation/runtime_policy_bootstrap.py').write_text('''
from src.utils.constants import DATA_DIR
def manifest_path(day,output_dir=None):return DATA_DIR/'bundle.json'
def verify_bootstrap(day,write=True):return dict(status='pass',findings=[],target_date=day,manifest_sha256='c'*64)
''')
        calls=calls.replace('    A.validate_manifest(DATA_DIR,A.I.read('+repr(str(path))+'),b)', '''    from src.engine.automation import intraday_release_handoff as H,runtime_policy_bootstrap as B
    H.verify(target_date,'d'*40)
    B.verify_bootstrap(target_date,write=False)
    with digest_owner.postclose_session(DATA_DIR,target_date):
        digest_owner.reused_digest(DATA_DIR/'source.bin')
        small=DATA_DIR/'native-small.gz';small.write_bytes(b'native-small')
        stat=small.stat()
        digest_owner.ACTIVE.get().admit_native_generation(small,dict(path=small.name,size=stat.st_size,
            sha256=__import__('hashlib').sha256(small.read_bytes()).hexdigest()),
            [stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns],proof_sha256='e'*64)''')
    if boundary == 'validate_rejected':
        bundle['reject'] = True
        (data/'bundle.json').write_text(json.dumps(bundle))
    assert marker in text;cli.write_text(text.replace(marker,calls+marker,1))
    run_id='1'*32
    if boundary == 'validate_rejected':
        with pytest.raises(ValueError, match='startup_native_preparation_failed'):
            validation._native_preparation_check(code,DAY,'2026-10-16',run_id)
        return
    result=validation._native_preparation_check(code,DAY,'2026-10-16',run_id)
    closure=result['native_machine_closure']
    assert closure['run_id']==run_id
    assert closure['bundles'][bundle['bundle_sha256']]['family_sha256']=='c'*64
    if boundary=='preserved':
        assert closure['manifests']=={}
        assert str(data/'native-small.gz') not in closure['digest_entries']
        record=next(iter(closure['preserved_generations'].values()))
        assert record['full_bootstrap']['full_native_verification'] is True
        assert record['sources'][str(consumed)]==hashlib.sha256(consumed.read_bytes()).hexdigest()
        assert {v['binding']['day'] for v in closure['digest_sessions'].values()}=={'2026-10-16',DAY}
        assert closure['digest_entries'][str(data/'source.bin')]['digest']==hashlib.sha256((data/'source.bin').read_bytes()).hexdigest()
        return
    assert closure['manifests'][ident]['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert closure['frozen_inventories'][str(data)][str(data/'bundle.json')]
    assert closure['frozen_validations'][str(data/'bundle.json')]['result']['schema']=='native_fixture_verified'
    assert closure['digest_binding']['pid']==result['native_validation_io']['stats']['pid']
    assert closure['digest_entries'][str(data/'source.bin')]['digest']==hashlib.sha256((data/'source.bin').read_bytes()).hexdigest()
    assert result['native_validation_io']['remaining_entries']==0


def test_parent_child_source_recheck_keeps_cap_and_independent_digest_authority(tmp_path,monkeypatch):
    from src.engine.infrastructure import startup_validation_code_context as C
    from src.engine.infrastructure.validation_digest_session import identity
    raw=tmp_path/'large.bin';raw.write_bytes(b'a'*2048)
    expected=hashlib.sha256(raw.read_bytes()).hexdigest()
    proof={'closure':{'digest_entries':{str(raw):{'identity':identity(raw),'digest':expected}}}}
    # Full closure schema has its own real-isolation suite. Exercise this
    # consumer's independent expected digest/stat comparison without 65 MiB IO.
    monkeypatch.setattr(C,'_check_native_closure',lambda value:None)
    monkeypatch.setattr(validation,'MAX_SOURCE',1024)
    validation._recheck({str(raw):expected},main_preparation=proof)
    with pytest.raises(ValueError,match='delegated_source_changed'):
        validation._recheck({str(raw):'0'*64},main_preparation=proof)
    with pytest.raises(ValueError,match='not_regular_bounded'):
        validation._recheck({str(raw):expected})
    raw.write_bytes(b'b'*2048)
    with pytest.raises(ValueError,match='delegated_source_changed'):
        validation._recheck({str(raw):expected},main_preparation=proof)


@pytest.mark.parametrize('scope', ['current_full_contract', 'intraday_preserved_historical_generation'])
@pytest.mark.parametrize('fault', [None, 'unknown_scope', 'scope_mismatch', 'basis', 'native_pid', 'manifest', 'authority'])
def test_parent_native_delegation_binds_authenticated_scope(scope, fault):
    from src.engine.infrastructure.startup_validation_code_context import _native_main_basis
    native=dict(status='pass',findings=[],validation_scope=scope,
        handoff_basis='intraday_preserved_preopen_generation',preserved_preopen_commit='a'*40)
    proof=dict(native_verification=native,delegation_basis=_native_main_basis(native),policy_sha256='b'*64,
        closure=dict(digest_binding={'pid':123},manifests={'c'*64:{}}))
    request=dict(run_id='d'*32,target_date='2026-10-19',request_sha256='e'*64)
    delegation=dict(schema='startup_native_validation_delegation_v1',run_id=request['run_id'],
        target_date=request['target_date'],request_sha256=request['request_sha256'],policy_sha256=proof['policy_sha256'],
        source_native_pid=123,basis=proof['delegation_basis'],parent_validation_scope=scope,
        child_semantic_validation='native_validators_executed',auxiliary_manifests=['c'*64],
        digest_reused_reads=1,digest_reused_bytes=32,runtime_effect=False,allowed_runtime_apply=False,actual_pid_consumed=False)
    if fault=='unknown_scope':native['validation_scope']='cached_generation'
    elif fault=='scope_mismatch':delegation['parent_validation_scope']='changed'
    elif fault=='basis':proof['delegation_basis']=delegation['basis']='unverified'
    elif fault=='native_pid':delegation['source_native_pid']=999
    elif fault=='manifest':delegation['auxiliary_manifests']=[]
    elif fault=='authority':delegation['runtime_effect']=True
    if fault:
        with pytest.raises(ValueError,match='startup_child_native_delegation_invalid'):
            validation._validate_native_delegation(delegation,proof,request)
    else:
        validation._validate_native_delegation(delegation,proof,request)
