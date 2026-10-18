"""Run Main's native policy loaders once without activating a trading process.

The parent binds the selected preparation and reviewed execution code. The
fresh Main child installs mandatory OS isolation before importing any loader.
Only a completed, source-stable, terminated child can publish a validation PASS.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from zoneinfo import ZoneInfo

KST = ZoneInfo('Asia/Seoul')
SCHEMA = 'main_policy_load_exit_validation_v1'
ROOT = Path(__file__).resolve().parents[3]
MAX_JSON = 8 * 1024 * 1024
MAX_SOURCE = 64 * 1024 * 1024
# Historical observation flags remain literal data in the native bootstrap.
# This exact exception belongs to that producer, not custody or arbitrary shell
# settings. Keep the existing values and the launcher's overlay order intact.
BOOTSTRAP_OBSERVATION_ENV_KEYS = frozenset({
    'SCALP_MICRO_REVERSION_DEPTH_CAPTURE_ENABLED',
    'SCALP_MICRO_REVERSION_DISCOVERY_ENABLED',
    'SCALP_MICRO_REVERSION_OBSERVER_ENABLED',
    'SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED',
})


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _sha(path):
    path = Path(path)
    digest = hashlib.sha256()
    with _open_source(path, MAX_SOURCE) as source:
        before = _identity(os.fstat(source.fileno()))
        read_bytes = 0
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            read_bytes += len(chunk)
            if read_bytes > MAX_SOURCE:
                raise ValueError('startup_input_grew_unbounded')
            digest.update(chunk)
        if _identity(os.fstat(source.fileno())) != before:
            raise ValueError('startup_input_changed_during_read')
    return digest.hexdigest()


def _open_source(path, maximum):
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError('startup_input_not_regular_bounded')
        return os.fdopen(fd, 'rb')
    except BaseException:
        os.close(fd)
        raise


def _read(path):
    with _open_source(path, MAX_JSON) as source:
        before = _identity(os.fstat(source.fileno()))
        raw = source.read(MAX_JSON + 1)
        if len(raw) > MAX_JSON or _identity(os.fstat(source.fileno())) != before:
            raise ValueError('startup_json_changed_or_unbounded')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('startup_object_required')
    return value


def _atomic(path, value):
    path = Path(path)
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2,
                      allow_nan=False) + '\n').encode()
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args],
                                   text=True, stderr=subprocess.PIPE, timeout=30).strip()


def _native_preparation_check(selected_root, target_date, source_date):
    if date.fromisoformat(source_date).isoformat() != source_date:
        raise ValueError('startup_native_preparation_source_date_invalid')
    # The selected CLI still performs its full current-contract verification.
    # Reuse only digests already read in this one child; the existing postclose
    # context neither loads nor writes a persistent cache and clears on exit.
    # Keep diagnostics on stderr so the native stdout/exit contract is intact.
    script = r'''import json,runpy,sys
sys.path.insert(0,sys.argv.pop(1))
source_date=sys.argv.pop(1)
from src.engine.infrastructure.validation_digest_session import postclose_session
from src.utils.constants import DATA_DIR
session=None
try:
    with postclose_session(DATA_DIR,source_date) as session:
        runpy.run_module('src.engine.automation.next_preopen_readiness',run_name='__main__')
finally:
    if session is not None:
        print('P5_NATIVE_VALIDATION_IO='+json.dumps(dict(source_date=source_date,
            stats=session.stats,remaining_entries=len(session.entries)),sort_keys=True),file=sys.stderr)
'''
    command = [str(selected_root / '.venv/bin/python'), '-I', '-B', '-c',
               script, str(selected_root), source_date, '--verify',
               '--target-date', target_date]
    env = _safe_process_environment()
    diagnostic_receipt = dict(source_date=source_date, target_date=target_date,
                              exit_code=None, status='not_observed', native_validation_io=None)
    try:
        result = subprocess.run(command, cwd=selected_root, env=env, capture_output=True,
                                text=True, timeout=180, check=False)
    except subprocess.TimeoutExpired as exc:
        # A killed child cannot attest its context cleanup or complete counters.
        diagnostic_receipt.update(status='timeout', diagnostics_status='unavailable_child_timeout')
        error = ValueError('startup_native_preparation_timeout')
        error.native_preparation_check = diagnostic_receipt
        raise error from exc
    diagnostic_receipt['exit_code'] = result.returncode

    def fail(message):
        error = ValueError(message)
        error.native_preparation_check = diagnostic_receipt
        raise error

    records = [line.removeprefix('P5_NATIVE_VALIDATION_IO=')
               for line in result.stderr.splitlines() if line.startswith('P5_NATIVE_VALIDATION_IO=')]
    try:
        if len(records) != 1 or len(records[0]) > 8192:
            raise ValueError('diagnostic_count_or_size')
        diagnostics = json.loads(records[0])
        stats = diagnostics['stats']
        if (set(diagnostics) != {'source_date', 'stats', 'remaining_entries'}
                or diagnostics['source_date'] != source_date
                or type(diagnostics['remaining_entries']) is not int or diagnostics['remaining_entries'] != 0
                or set(stats) - {'full_reads', 'full_bytes', 'reused_reads', 'reused_bytes',
                    'cache_status', 'role', 'generation_sha256', 'pid', 'wall_seconds',
                    'thread_io_delta', 'peak_process_rss_kib'}
                or stats['role'] != 'postclose'
                or stats['cache_status'] not in {'invocation_memory_only', 'storage_unavailable_full_fallback'}
                or type(stats['pid']) is not int or stats['pid'] <= 0
                or not isinstance(stats['generation_sha256'], str)
                or not re.fullmatch('[0-9a-f]{64}', stats['generation_sha256'])
                or type(stats['wall_seconds']) not in (int, float)
                or not 0 <= stats['wall_seconds'] < float('inf')
                or any(type(stats[key]) is not int or stats[key] < 0
                       for key in ('full_reads', 'full_bytes', 'reused_reads', 'reused_bytes'))):
            raise ValueError('diagnostic_contract')
        if ('peak_process_rss_kib' in stats
                and (type(stats['peak_process_rss_kib']) is not int or stats['peak_process_rss_kib'] < 0)):
            raise ValueError('diagnostic_rss')
        io_delta = stats['thread_io_delta']
        if io_delta is not None and (not isinstance(io_delta, dict)
                or set(io_delta) != {'rchar', 'read_bytes', 'write_bytes'}
                or any(type(v) is not int or v < 0 for v in io_delta.values())):
            raise ValueError('diagnostic_io')
        diagnostic_receipt.update(native_validation_io=diagnostics, diagnostics_status='observed')
    except (ValueError, KeyError, TypeError):
        diagnostic_receipt['diagnostics_status'] = 'invalid_or_missing'
    try:
        value = json.loads(result.stdout.splitlines()[-1])
        if not isinstance(value, dict):
            raise ValueError('native_object_required')
    except (ValueError, IndexError):
        diagnostic_receipt['status'] = 'invalid_result'
        fail('startup_native_preparation_result_invalid')
    diagnostic_receipt['status'] = ('pass' if result.returncode == 0
        and value.get('status') == 'pass' and not value.get('findings') else 'fail')
    if result.returncode or value.get('status') != 'pass' or value.get('findings'):
        fail('startup_native_preparation_failed:' +
             ','.join(map(str, value.get('findings') or [])))
    if diagnostic_receipt['diagnostics_status'] != 'observed':
        fail('startup_native_preparation_diagnostics_invalid')
    return {**value, 'native_validation_io': diagnostics}


def _intake(workspace, target_date):
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.utils.market_day import is_krx_trading_day
    day = date.fromisoformat(target_date)
    if day.isoformat() != target_date or day < datetime.now(KST).date() or not is_krx_trading_day(day):
        raise ValueError('startup_policy_target_not_current_or_future_trading_day')
    data = workspace / 'data'
    selection = data / 'runtime/runtime_release_selection.json'
    selection_sha = _sha(selection)
    selected_root, selected_commit = selected_release(workspace)
    if _sha(selection) != selection_sha:
        raise ValueError('startup_selection_changed_during_resolution')
    index = data / 'runtime/policy_bootstrap/prepared' / target_date / 'latest.json'
    view = _read(index)
    receipt_path = Path(view['receipt_path'])
    if (view.get('target_date') != target_date
            or receipt_path.resolve().parent.parent != index.parent.resolve()
            or _sha(receipt_path) != view.get('receipt_sha256')):
        raise ValueError('startup_prepared_index_invalid')
    receipt = _read(receipt_path)
    if (receipt.get('schema') != 'next_preopen_readiness_v1'
            or receipt.get('status') != 'prepared_verified'
            or receipt.get('target_date') != target_date
            or receipt.get('runtime_effect') is not False
            or receipt.get('actual_pid_consumed') is not False):
        raise ValueError('startup_prepared_receipt_invalid')
    sources = {str(selection): selection_sha, str(index): _sha(index),
               str(receipt_path): _sha(receipt_path)}
    for name, digest in [('manifest_path', 'manifest_file_sha256'), ('env_path', 'env_sha256'),
                         ('verification_path', 'verification_sha256'),
                         ('controller_path', 'controller_sha256'), ('summary_path', 'summary_sha256')]:
        path = Path(receipt[name])
        actual = _sha(path)
        if actual != receipt.get(digest):
            raise ValueError('startup_prepared_source_changed:' + name)
        sources[str(path)] = actual
    for row in receipt.get('policy_receipts', []):
        actual = _sha(Path(row['path']))
        if actual != row['sha256']:
            raise ValueError('startup_prepared_policy_changed')
        sources[row['path']] = actual
    manifest = _read(receipt['manifest_path'])
    if (manifest.get('target_date') != target_date
            or manifest.get('manifest_sha256') != receipt.get('manifest_content_sha256')
            or manifest['manifest_sha256'] != _digest({k: v for k, v in manifest.items() if k != 'manifest_sha256'})):
        raise ValueError('startup_prepared_manifest_invalid')
    native = _native_preparation_check(selected_root, target_date, receipt['source_date'])
    if native.get('selected_release_commit') != selected_commit:
        raise ValueError('startup_native_selection_mismatch')
    _recheck(sources)
    return dict(selected_root=selected_root, selected_commit=selected_commit,
                receipt_path=receipt_path, receipt=receipt, manifest=manifest,
                source_hashes=sources, native_verification=native)


def _bind_execution(workspace, execution_root, intake, candidate):
    from src.engine.infrastructure.runtime_release_router import validate_release, selected_release
    if selected_release(workspace) != (intake['selected_root'], intake['selected_commit']):
        raise ValueError('startup_selected_release_changed')
    root = execution_root.resolve(strict=True)
    if root != ROOT:
        raise ValueError('startup_orchestrator_execution_root_mismatch')
    commit = _git(root, 'rev-parse', 'HEAD')
    if _git(root, 'status', '--porcelain', '--untracked-files=normal', '--', 'src', 'deploy', 'requirements.txt'):
        raise ValueError('startup_execution_source_dirty')
    if not candidate:
        if root != intake['selected_root'] or commit != intake['selected_commit']:
            raise ValueError('startup_execution_not_selected')
    else:
        validate_release(workspace, dict(schema='runtime_release_selection_v1', workspace=str(workspace),
                                        release_root=str(root), git_commit=commit))
    from src.engine.automation.intraday_release_handoff import _verify_entry_code_delta
    from src.engine.automation.prepared_policy_code_handoff import resolve_prepared_code_origin
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS
    from src.engine.scalping import main_stop_policy as stop, holding_vote_experiment as vote
    manifest = intake['manifest']
    contracts, contract_sources = {}, {}

    def bind_contract(family, policy_sha, expected, paths):
        origin = resolve_prepared_code_origin(workspace / 'data', manifest['target_date'],
            family=family, policy_sha=policy_sha, expected=expected, paths=paths,
            selected_root=intake['selected_root'], selected_commit=intake['selected_commit'])
        changed = _verify_entry_code_delta(root, commit, origin['origin_commit'], paths, expected)
        sources = dict(origin['sources'])
        sources.update({str((root / name).resolve()): _sha(root / name) for name in paths.values()})
        actual = _digest({key: _sha(root / name) for key, name in paths.items()})
        contracts[family] = dict(schema='main_startup_validation_consumer_code_handoff_v1',
            target_date=manifest['target_date'], family=family, policy_sha256=policy_sha,
            original_code_sha256=expected, runtime_code_contract_sha256=actual, paths=paths,
            execution_release_root=str(root), execution_release_commit=commit,
            source_hashes=sources, origin=origin, changed_consumer_paths=changed,
            status='verified', policy_effect='unchanged')
        contract_sources.update(sources)

    delay = manifest.get('pre_submit_delay_handoff') or {}
    if delay.get('code_contract_sha256'):
        bind_contract('pre_submit_delay', delay['policy_sha256'], delay['code_contract_sha256'],
            {name: name for name in CONTRACT_PATHS})
    stop_receipt = manifest.get('main_stop_confirmation_receipt') or {}
    env = manifest.get('env_overrides') or {}
    if env.get(stop.ENV_FILE):
        bundle = stop.load_bundle(env[stop.ENV_FILE], env[stop.ENV_SHA], manifest['target_date'], require_current_code=False)
        if bundle['policy_sha256'] != stop_receipt.get('policy_sha256'):
            raise ValueError('startup_stop_binding_invalid')
        bind_contract('main_stop', bundle['policy_sha256'], bundle['code_sha256'],
            {name: 'src/engine/' + name for name in stop.implementation_paths()})
    holding = manifest.get('holding_path_vote_policy_receipt') or {}
    if holding.get('bundle_sha256'):
        from src.engine.scalping import holding_path_vote_policy as holding_native
        bundle = holding_native.load_bundle(workspace / 'data', manifest['target_date'], require_current_code=False)
        bind_contract('holding_vote', bundle['bundle_sha256'], bundle['code_sha256'],
            {name: 'src/engine/' + name for name in vote._code_paths()})
    return dict(basis='reviewed_candidate_handoff' if candidate else 'selected',
                root=str(root), commit=commit, contracts=contracts, source_hashes=contract_sources)


def _assignment_values(path, *, source_role='policy'):
    """Accept only data assignments, never expansions or executable shell."""
    if source_role not in ('policy', 'bootstrap', 'custody'):
        raise ValueError('startup_environment_source_role_invalid')
    with _open_source(path, MAX_JSON) as source:
        raw = source.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise ValueError('startup_environment_unbounded')
    values = {}
    for line in raw.decode().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'(?:export )?([A-Z_][A-Z0-9_]*)=(.*)', line)
        if match is None:
            raise ValueError('startup_environment_assignment_required')
        key, rhs = match.groups()
        if (not key.startswith('KORSTOCKSCAN_')
                and not (source_role == 'bootstrap'
                         and key in BOOTSTRAP_OBSERVATION_ENV_KEYS)):
            raise ValueError('startup_environment_policy_namespace_required')
        words = shlex.split(rhs, comments=False, posix=True)
        if len(words) > 1:
            raise ValueError('startup_environment_literal_required')
        value = words[0] if words else ''
        permitted = {shlex.quote(value), '' if value == '' else shlex.quote(value)}
        if not any(c in value for c in '$`\\"\n\r'):
            permitted.add('"' + value + '"')
        if rhs not in permitted or key in values:
            raise ValueError('startup_environment_noncanonical_or_duplicate')
        values[key] = value
    return values


def _safe_process_environment():
    forbidden = {'BASH_ENV', 'ENV', 'SHELLOPTS', 'BASHOPTS', 'CDPATH',
                 'PYTHONHOME', 'PYTHONPATH', 'PYTHONSTARTUP', 'PYTHONINSPECT',
                 'LD_PRELOAD', 'LD_LIBRARY_PATH'}
    env = {key: value for key, value in os.environ.items()
           if key not in forbidden and not key.startswith('BASH_FUNC_')}
    env.update(PATH='/usr/bin:/bin', PYTHONDONTWRITEBYTECODE='1')
    return env


def _environment_sources(workspace, target_date, bootstrap_env):
    data = workspace / 'data'
    paths = {Path(bootstrap_env), data / 'config/native_owner_custody.env',
             data / 'threshold_cycle/runtime_env/operator_runtime_overrides.env',
             data / f'threshold_cycle/runtime_env/operator_runtime_overrides_{target_date}.env'}
    for path in (data / 'runtime').glob('ai_multi_timeframe_context_promotion_*.json'):
        day = path.stem.removeprefix('ai_multi_timeframe_context_promotion_')
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', day) and day <= target_date:
            paths.add(path)
            if day >= '2026-09-19':
                parent, prefix = data / 'runtime/policy_bootstrap', 'runtime_policy_bootstrap_'
            else:
                parent, prefix = data / 'threshold_cycle/runtime_env', 'threshold_runtime_env_'
            paths.update({parent / (prefix + day + suffix) for suffix in ('.env', '.json')})
    return {str(p): _sha(p) if p.exists() or p.is_symlink() else None for p in sorted(paths)}


def _compose_environment(root, target_date, bootstrap_env, directory):
    """Use the exact shell functions used by the real launcher, in its order."""
    script = r'''set -euo pipefail
cd "$1/src"
PROJECT_DIR="$1"
. "$PROJECT_DIR/src/engine/infrastructure/main_policy_environment.sh"
apply_main_policy_defaults
apply_main_policy_handoff "$2" "$3" "$4"
apply_main_policy_final_environment
printf '\0MAIN_POLICY_ENV\0'
env -0
'''
    safe_bootstrap = directory / 'bootstrap-assignments.env'
    safe_custody = directory / 'custody-assignments.env'
    for original, destination, role in [
            (Path(bootstrap_env), safe_bootstrap, 'bootstrap'),
            (root / 'data/config/native_owner_custody.env', safe_custody, 'custody')]:
        values = _assignment_values(original, source_role=role) if original.exists() else {}
        destination.write_text(''.join(f'export {key}={shlex.quote(value)}\n' for key, value in sorted(values.items())))
    process = subprocess.run(['/bin/bash', '-c', script, 'main-policy-env', str(root),
                              target_date, str(safe_bootstrap), str(safe_custody)], capture_output=True,
                             env=_safe_process_environment(), timeout=60, check=True)
    marker = b'\0MAIN_POLICY_ENV\0'
    if process.stdout.count(marker) != 1:
        raise ValueError('startup_environment_result_invalid')
    values = {}
    for assignment in process.stdout.split(marker, 1)[1].split(b'\0'):
        if not assignment:
            continue
        key, value = assignment.split(b'=', 1)
        values[os.fsdecode(key)] = os.fsdecode(value)
    values.pop('PYTHONHOME', None)
    values.update(PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE='1',
                  OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return values


def _recheck(sources):
    for name, expected in sources.items():
        actual = _sha(name) if Path(name).exists() or Path(name).is_symlink() else None
        if actual != expected:
            raise ValueError('startup_source_changed:' + str(name))


def _ticks(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]


def _code_sources(root):
    sources = {}
    names = _git(root, 'ls-files', '-z', '--', 'src', 'deploy', 'requirements.txt').split('\0')
    for name in names:
        if name and (root / name).is_file():
            sources[str(root / name)] = _sha(root / name)
    return sources


def _expected_policy_hashes(intake):
    receipt, manifest = intake['receipt'], intake['manifest']
    expected = {}
    candidate = receipt.get('activation_candidate') or {}
    if candidate.get('bundle_sha256'):
        expected['main_machine'] = candidate['bundle_sha256']
        expected['main_auxiliary'] = candidate['bundle_sha256']
    for consumer, field, key in [('main_stop', 'main_stop_confirmation_receipt', 'policy_sha256'),
                                  ('holding_path_vote', 'holding_path_vote_policy_receipt', 'bundle_sha256'),
                                  ('pre_submit_delay', 'pre_submit_delay_handoff', 'policy_sha256')]:
        bound = manifest.get(field) or {}
        if bound.get(key):
            expected[consumer] = bound[key]
    return expected


def _validate_child_result(child, expected_ids, expected_policy_hashes):
    results = child.get('consumer_results')
    isolation = child.get('isolation') or {}
    if not isinstance(results, dict) or not isinstance(isolation, dict):
        raise ValueError('startup_child_object_contract_invalid')
    if (child.get('status') != 'passed'
            or any(child.get(key) is not False for key in ('runtime_effect', 'actual_pid_consumed', 'allowed_runtime_apply'))
            or child.get('findings') != [] or not isinstance(results, dict)
            or set(results) != set(expected_ids)
            or isolation.get('no_new_privileges') is not True
            or not isolation.get('filesystem_write_root')
            or isolation.get('landlock_abi', 0) < 3
            or isolation.get('network_access') is not False or isolation.get('process_creation') is not False
            or isolation.get('metadata_changes') is not False
            or isolation.get('caught_permission_denials_fail') is not True
            or child.get('forbidden_attempt_count') != 0):
        raise ValueError('startup_child_semantic_contract_invalid')
    for name, row in results.items():
        if (not isinstance(row, dict) or not isinstance(row.get('source_hashes'), dict)
                or row.get('status') not in {'loaded', 'disabled', 'parent_only'}
                or not re.fullmatch('[0-9a-f]{64}', str(row.get('loaded_object_sha256', '')))):
            raise ValueError('startup_child_consumer_invalid:' + name)
        for path, sha in row['source_hashes'].items():
            if not isinstance(path, str) or not Path(path).is_absolute() or not re.fullmatch('[0-9a-f]{64}', str(sha)):
                raise ValueError('startup_child_consumer_source_invalid:' + name)
        if name in expected_policy_hashes and row.get('policy_sha256') != expected_policy_hashes[name]:
            raise ValueError('startup_child_wrong_policy:' + name)


def run_validation(*, workspace, target_date, execution_root=ROOT, candidate=False, timeout=120):
    workspace = Path(workspace).resolve(strict=True)
    if not 1 <= timeout <= 300:
        raise ValueError('startup_timeout_invalid')
    date.fromisoformat(target_date)
    run_id = uuid.uuid4().hex
    directory = workspace / 'data/report/main_startup_validation' / target_date / run_id
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(directory, 0o700)
    final = dict(schema=SCHEMA, run_id=run_id, target_date=target_date,
                 observed_at_kst=datetime.now(KST).isoformat(), status='failed', findings=[],
                 runtime_effect=False, allowed_runtime_apply=False, actual_pid_consumed=False,
                 child_terminated=False, load_check_passed=False, failure_phase='intake')
    process = None
    try:
        intake = _intake(workspace, target_date)
        final['native_preparation_checks'] = {'intake': intake.get('native_verification')}
        binding = _bind_execution(workspace, Path(execution_root), intake, candidate)
        root = Path(binding['root'])
        sources = dict(intake['source_hashes'])
        sources.update(binding.get('source_hashes') or {})
        sources.update(_code_sources(root))
        for name in ['src/bot_main.py', 'src/run_bot.sh',
                     'src/engine/automation/main_startup_validation.py',
                     'src/engine/infrastructure/main_policy_loading.py',
                     'src/engine/infrastructure/main_policy_environment.sh',
                     'src/engine/infrastructure/startup_validation_code_context.py',
                     'src/engine/infrastructure/startup_validation_isolation.py']:
            sources[str(root / name)] = _sha(root / name)
        for name in ['data/config/native_owner_custody.env',
                     'data/config/manual_control_excluded_codes.txt',
                     'data/runtime/mechanistic_entry_policy/current.json',
                     'data/runtime/order_owner_registry.jsonl']:
            path = workspace / name
            if path.exists():
                sources[str(path)] = _sha(path)
        final.update(selected_release_root=str(intake['selected_root']),
                     selected_release_commit=intake['selected_commit'],
                     execution_release_root=str(root), execution_release_commit=binding['commit'],
                     release_binding_basis=binding['basis'], candidate_handoff_sha256=_digest(binding),
                     prepared_receipt_sha256=_sha(intake['receipt_path']))
        final['failure_phase'] = 'environment'
        env_sources = _environment_sources(workspace, target_date, intake['receipt']['env_path'])
        child_env = _compose_environment(root, target_date, intake['receipt']['env_path'], directory)
        child_env.update(PYTHONNOUSERSITE='1', PYTHONPYCACHEPREFIX=str(directory / 'pycache'))
        if _environment_sources(workspace, target_date, intake['receipt']['env_path']) != env_sources:
            raise ValueError('startup_environment_inputs_changed')
        sources.update(env_sources)
        for name in ['data/threshold_cycle/runtime_env/operator_runtime_overrides.env',
                     f'data/threshold_cycle/runtime_env/operator_runtime_overrides_{target_date}.env']:
            path = workspace / name
            if path.exists():
                sources[str(path)] = _sha(path)
        policies = {k: v for k, v in child_env.items() if k.startswith('KORSTOCKSCAN_')}
        final['expected_env_sha256'] = _digest(policies)
        from src.engine.infrastructure.main_policy_loading import CONSUMER_IDS
        request = dict(schema=SCHEMA, run_id=run_id, target_date=target_date,
                       run_directory=str(directory),
                       observed_at_kst=final['observed_at_kst'], execution_release_root=str(root),
                       execution_release_commit=binding['commit'], data_root=str(workspace / 'data'),
                       expected_env_sha256=final['expected_env_sha256'], source_hashes=sources,
                       manifest=intake['manifest'], consumer_ids=sorted(CONSUMER_IDS),
                       expected_policy_hashes=_expected_policy_hashes(intake),
                       candidate_code_handoffs=binding.get('contracts') or {})
        request['request_sha256'] = _digest(request)
        _atomic(directory / 'request.json', request)
        final['input_manifest_sha256'] = request['request_sha256']
        _recheck(sources)
        final['failure_phase'] = 'child'
        command = [str(root / '.venv/bin/python'), '-I', '-B', '-X',
                   'pycache_prefix=' + str(directory / 'pycache'), str(root / 'src/bot_main.py'),
                   '--validate-startup', str(directory / 'request.json')]
        with (directory / 'child-output.log').open('wb') as log:
            process = subprocess.Popen(command, cwd=root / 'src', env=child_env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, close_fds=True,
                                       start_new_session=True)
            ticks = _ticks(process.pid)
            final.update(validation_pid=process.pid, validation_start_ticks=ticks)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
                raise ValueError('startup_child_timeout') from exc
        final.update(child_exit_code=code, child_terminated=process.poll() is not None)
        child = _read(directory / 'child.json')
        if (child.get('run_id') != run_id or child.get('request_sha256') != request['request_sha256']
                or child.get('validation_pid') != process.pid
                or child.get('validation_start_ticks') != ticks
                or child.get('execution_release_commit') != binding['commit']):
            raise ValueError('startup_child_identity_mismatch')
        final['consumer_results'] = child.get('consumer_results', {})
        final['isolation'] = child.get('isolation')
        if code != 0 or child.get('status') != 'passed' or child.get('runtime_effect') is not False:
            final['findings'].extend(child.get('findings') or ['startup_child_failed'])
            raise ValueError('startup_policy_loading_failed')
        _validate_child_result(child, request['consumer_ids'], request['expected_policy_hashes'])
        if (child['isolation'].get('filesystem_write_root') != str(directory)
                or child['isolation'].get('process_group') != process.pid
                or child['isolation'].get('session_id') != process.pid):
            raise ValueError('startup_child_isolation_identity_invalid')
        final['failure_phase'] = 'recheck'
        _recheck(sources)
        for row in final['consumer_results'].values():
            _recheck(row.get('source_hashes') or {})
        final['native_preparation_checks']['recheck'] = _native_preparation_check(
            intake['selected_root'], target_date, intake['receipt']['source_date'])
        if date.fromisoformat(target_date) < datetime.now(KST).date():
            raise ValueError('startup_target_expired_during_validation')
        if _bind_execution(workspace, root, intake, candidate) != binding:
            raise ValueError('startup_execution_binding_changed')
        if _environment_sources(workspace, target_date, intake['receipt']['env_path']) != env_sources:
            raise ValueError('startup_environment_inputs_changed')
        _recheck(sources)
        final.update(status='passed', load_check_passed=True, protected_sources_unchanged=True,
                     failure_phase=None)
    except (OSError, ValueError, TypeError, KeyError, ImportError, subprocess.SubprocessError) as exc:
        # Keep reasons bounded. No raw environment or captured stderr is published.
        native_check = getattr(exc, 'native_preparation_check', None)
        if native_check is not None:
            phase = 'intake' if final['failure_phase'] == 'intake' else 'recheck'
            final.setdefault('native_preparation_checks', {})[phase] = native_check
        final['findings'].append(type(exc).__name__ + ':' + str(exc)[:1000])
    finally:
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
            final['child_terminated'] = process.poll() is not None
        final['completed_at_kst'] = datetime.now(KST).isoformat()
        _atomic(directory / 'final.json', final)
    return final, directory / 'final.json'


def child_main(request_path):
    """Called by bot_main before its first side-effectful import."""
    request_path = Path(request_path).absolute()
    directory = request_path.parent
    request = _read(request_path)
    if request.get('request_sha256') != _digest({k: v for k, v in request.items() if k != 'request_sha256'}):
        raise ValueError('startup_request_digest_invalid')
    if (request.get('schema') != SCHEMA or request.get('execution_release_root') != str(ROOT)
            or request_path.name != 'request.json' or directory.name != request.get('run_id')
            or re.fullmatch('[0-9a-f]{32}', request.get('run_id', '')) is None):
        raise ValueError('startup_child_request_identity_invalid')
    result = dict(schema=SCHEMA, run_id=request['run_id'], request_sha256=request['request_sha256'],
                  validation_pid=os.getpid(), validation_start_ticks=_ticks(os.getpid()),
                  execution_release_commit=request['execution_release_commit'],
                  runtime_effect=False, actual_pid_consumed=False, allowed_runtime_apply=False,
                  status='failed', findings=[])
    from src.engine.infrastructure.startup_validation_isolation import (
        install_validation_isolation, assert_no_forbidden_attempts)
    try:
        result['isolation'] = install_validation_isolation(directory, directory / 'isolation.jsonl')
        _recheck(request['source_hashes'])
        if request.get('candidate_code_handoffs'):
            from src.engine.infrastructure.startup_validation_code_context import install_validation_code_context
            install_validation_code_context(request)
        policy_env = {k: v for k, v in os.environ.items() if k.startswith('KORSTOCKSCAN_')}
        if _digest(policy_env) != request['expected_env_sha256']:
            raise ValueError('startup_child_environment_changed')
        from src.engine.infrastructure.main_policy_loading import load_main_policies, CONSUMER_IDS
        load_clock = datetime.now(KST)
        result['observed_at_kst'] = load_clock.isoformat()
        report = load_main_policies(target_date=request['target_date'],
            observed_at=load_clock,
            data_root=Path(request['data_root']), env=os.environ, validation=True)
        result['consumer_results'] = report['consumer_results']
        if (report.get('schema') != 'main_policy_loading_v1'
                or report.get('target_date') != request['target_date']
                or report.get('runtime_effect') is not False
                or report.get('actual_pid_consumed') is not False
                or report.get('allowed_runtime_apply', False) is not False):
            raise ValueError('startup_loader_authority_or_identity_invalid')
        if set(report['consumer_results']) != CONSUMER_IDS:
            raise ValueError('startup_consumer_coverage_incomplete')
        if report.get('status') != 'passed':
            raise ValueError('startup_required_consumer_failed')
        isolation_result = assert_no_forbidden_attempts()
        result['forbidden_attempt_count'] = isolation_result['forbidden_attempt_count']
        _recheck(request['source_hashes'])
        result['status'] = 'passed'
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        result['findings'].append(type(exc).__name__ + ':' + str(exc)[:1000])
    _atomic(directory / 'child.json', result)
    return 0 if result['status'] == 'passed' else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--target-date', required=True)
    parser.add_argument('--candidate-root', type=Path)
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args(argv)
    result, path = run_validation(workspace=args.workspace, target_date=args.target_date,
        execution_root=args.candidate_root or ROOT, candidate=args.candidate_root is not None,
        timeout=args.timeout)
    print(json.dumps(dict(status=result['status'], receipt_path=str(path),
                         actual_pid_consumed=False, runtime_effect=False), sort_keys=True))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
